"""GSS Phase 1 driver — top-level orchestrator that runs the LLM panel
across respondents × conditions × items × models, scores each call, and
persists results.

Audit primitives (prompts / scoring / aggregation) live in gss_pipeline.py.
LLM network layer lives in llm_router.py. This module only orchestrates.

Locked design (gss_phase1_design.md §12):
  - Phase 1a (N=100): 4 cheap OpenRouter models × n_samples=1
  - Phase 1b (N=1500): single quality-selected model × n_samples=1 (per §12.2: argmin 1a MAE among DQ-passers; cost is tie-break only)
  - GPT-4o anchor: N=100 subset, n_samples=2, primary conditions only
  - Sensitivity pass: per-item exclusion (1b model + anchor only)

Usage:
    # Smoke test — 1 respondent, 1 model, primary conditions only
    python3 gss_driver.py --smoke

    # Full N=10 smoke — 4 cheap models, primary + sensitivity
    python3 gss_driver.py --n 10

    # Full N=10 primary only (skip sensitivity to save cost)
    python3 gss_driver.py --n 10 --primary-only

    # GPT-4o anchor on N=100 subset (only after cheap-panel run is in)
    python3 gss_driver.py --anchor --n 100
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from gss_loader import load_gss
from gss_pipeline import (
    BIN_DISPLAY,
    build_persona_prompt,
    format_eval_question,
    load_taxonomy,
    sample_respondents,
    score_item,
    truth_code_or_none,
    _scale_options_for,
)
from llm_router import (
    MODEL_ANCHOR,
    MODEL_PANEL_PRIMARY,
    LLMError,
    call_llm,
)

WORK = Path("/Users/joyce/Documents/GSBGEN390")
OUTPUTS = WORK / "outputs"
OUTPUTS.mkdir(exist_ok=True)

# Conditions for the primary LOO analysis (5 total: full + 4 LOO).
CONDITIONS_PRIMARY = [
    ("full", None),
    ("loo_drop_demographic", "demographic"),
    ("loo_drop_behavioral", "behavioral"),
    ("loo_drop_psychological", "psychological"),
    ("loo_drop_attitudinal", "attitudinal"),
]


# ---------------------------------------------------------------------------
# Sensitivity-pass synthesis: derive eval-item dicts from sensitivity_eval
# ---------------------------------------------------------------------------

# Items where label-set count does NOT correctly reflect the true ordinal scale.
# Either codebook labels are sparse (only endpoints + middle anchored), or labels
# include meta-codes (e.g., 8/9/97 = DK/REFUSED/NAP) that should be excluded
# from the scale shown to the LLM. Per Codex audit 2026-05-06.
SENSITIVITY_FORMAT_OVERRIDES: dict[str, dict] = {
    # WLTH* battery — true scale 1-7 (lots-more-wealth → lots-less-wealth);
    # codebook only labels endpoints, so we explicitly include all 7 codes.
    "WLTHWHTS": {"format": "likert7", "valid_codes": [1,2,3,4,5,6,7], "is_sparse": True},
    "WLTHBLKS": {"format": "likert7", "valid_codes": [1,2,3,4,5,6,7], "is_sparse": True},
    "WLTHHSPS": {"format": "likert7", "valid_codes": [1,2,3,4,5,6,7], "is_sparse": True},
    # COL* battery — 2024 substantive codes are [4, 5] (NOT [1, 2]).
    # COLATH/COLRAC: 4=ALLOWED, 5=NOT ALLOWED.
    # COLCOM: 4='Yes, fired', 5='Not fired' (different question — about firing
    # a communist teacher — but same code domain in 2024 GSS).
    "COLATH":   {"format": "binary", "valid_codes": [4,5], "is_sparse": False},
    "COLRAC":   {"format": "binary", "valid_codes": [4,5], "is_sparse": False},
    "COLCOM":   {"format": "binary", "valid_codes": [4,5], "is_sparse": False},
    # LIB* / SPK* batteries — 2024 substantive codes are [1, 2].
    # LIB*: 1=REMOVE (the offending book from library), 2=NOT REMOVE.
    # SPK*: 1=ALLOWED (to give a public speech), 2=NOT ALLOWED.
    "LIBRAC":   {"format": "binary", "valid_codes": [1,2], "is_sparse": False},
    "LIBCOM":   {"format": "binary", "valid_codes": [1,2], "is_sparse": False},
    "SPKRAC":   {"format": "binary", "valid_codes": [1,2], "is_sparse": False},
    "SPKATH":   {"format": "binary", "valid_codes": [1,2], "is_sparse": False},
    "SPKCOM":   {"format": "binary", "valid_codes": [1,2], "is_sparse": False},
}


def derive_sensitivity_item(varname: str) -> dict | None:
    """Build a synthetic eval-item dict for a sensitivity_eval variable, by
    inspecting its label set to infer format. Returns None if the variable
    has no usable label set (skip it).

    For variables in SENSITIVITY_FORMAT_OVERRIDES, the override wins:
    overrides specify the true ordinal scale and any sparse-anchor flag,
    correcting cases where label-set length misclassifies the format.
    """
    if varname in SENSITIVITY_FORMAT_OVERRIDES:
        ovr = SENSITIVITY_FORMAT_OVERRIDES[varname]
        return {
            "id": varname,
            "format": ovr["format"],
            "construct": "(sensitivity)",
            "_valid_codes_override": ovr["valid_codes"],
            "_is_sparse_override": ovr["is_sparse"],
        }
    options = _scale_options_for(varname)
    n = len(options)
    if n == 0:
        return None
    if n == 2:
        fmt = "binary"
    elif n == 3:
        fmt = "likert3"
    elif n == 4:
        fmt = "likert4"
    elif n == 5:
        fmt = "likert5"
    elif n == 7:
        fmt = "likert7"
    elif n > 7:
        fmt = "categorical"
    else:
        fmt = "categorical"
    return {"id": varname, "format": fmt, "construct": "(sensitivity)"}


# ---------------------------------------------------------------------------
# Per-respondent runners
# ---------------------------------------------------------------------------

def run_primary_one_respondent(
    respondent: pd.Series,
    taxonomy: dict,
    primary_eval_items: list[dict],
    models: list[str],
    n_samples: int = 1,
    temperature: float = 0.7,
    verbose: bool = True,
) -> list[dict]:
    """For one respondent: 5 conditions × 12 items × len(models) × n_samples calls.
    Returns a list of records, one per (condition, model)."""
    rid = int(respondent.get("ID_", -1))
    records: list[dict] = []

    for cond_name, drop_bin in CONDITIONS_PRIMARY:
        # Build the persona prompt ONCE per condition (reused across items + models)
        system, prompt_stats = build_persona_prompt(respondent, taxonomy, drop_bin=drop_bin)
        per_model_scores: dict[str, dict[str, list[dict]]] = {m: {} for m in models}

        for item in primary_eval_items:
            question, meta = format_eval_question(item)
            truth = truth_code_or_none(respondent.get(item["id"]), item["id"])
            for m in models:
                samples: list[dict] = []
                for s_idx in range(n_samples):
                    try:
                        raw = call_llm(system, question, model=m, temperature=temperature)
                    except LLMError as e:
                        raw = f"<<LLM_ERROR: {e}>>"
                    score = score_item(
                        item["id"], item["format"], meta["valid_codes"], raw, truth
                    )
                    samples.append(score)
                per_model_scores[m][item["id"]] = samples
            if verbose:
                print(f"    [{rid}/{cond_name}] item {item['id']:<10} done", flush=True)

        for m, per_item in per_model_scores.items():
            records.append({
                "respondent_id": rid,
                "condition": cond_name,
                "model": m,
                "n_samples": n_samples,
                "per_item_scores": per_item,
                "prompt_stats": {k: v for k, v in prompt_stats.items() if k != "excluded_vars"},
            })
    return records


def run_sensitivity_one_respondent(
    respondent: pd.Series,
    taxonomy: dict,
    sensitivity_eval_ids: list[str],
    models: list[str],
    n_samples: int = 1,
    temperature: float = 0.7,
    verbose: bool = True,
    done_items_by_model: dict[str, set[str]] | None = None,
    persist_after_each_item: "Callable[[list[dict]], None] | None" = None,
) -> list[dict]:
    """For one respondent: each sensitivity item gets its own per-item-excluded
    persona prompt. Returns one record per model, with per_item_scores keyed
    by sensitivity_item_id.

    Item-level resume (P2.1):
      - `done_items_by_model[m]` lists item ids ALREADY scored for model m on
        this respondent; those items are skipped per model.
      - If `persist_after_each_item` is supplied, it's called after every
        sensitivity item (across all models) finishes, with the current
        partial-records snapshot. The caller persists. This bounds the worst-
        case rerun on interruption to ONE in-flight item per respondent×model
        rather than the full ~118-item block.
    """
    rid = int(respondent.get("ID_", -1))
    skip = done_items_by_model or {m: set() for m in models}
    per_model_scores: dict[str, dict[str, list[dict]]] = {m: {} for m in models}

    def _snapshot() -> list[dict]:
        # Build the records snapshot for this respondent right now.
        return [
            {
                "respondent_id": rid,
                "condition": "sensitivity",
                "model": m,
                "n_samples": n_samples,
                "per_item_scores": dict(per_item),
            }
            for m, per_item in per_model_scores.items()
        ]

    for vid in sensitivity_eval_ids:
        item = derive_sensitivity_item(vid)
        if item is None:
            continue
        # If every model has already scored this item, skip the prompt build.
        if all(vid in skip.get(m, set()) for m in models):
            if verbose:
                print(f"    [{rid}/sensitivity] {vid:<10} resume-skip (all models done)",
                      flush=True)
            continue

        system, _ = build_persona_prompt(
            respondent, taxonomy, drop_bin=None, exclude_vars=[vid]
        )
        question, meta = format_eval_question(item)
        truth = truth_code_or_none(respondent.get(vid), vid)

        for m in models:
            if vid in skip.get(m, set()):
                continue
            samples: list[dict] = []
            for s_idx in range(n_samples):
                try:
                    raw = call_llm(system, question, model=m, temperature=temperature)
                except LLMError as e:
                    raw = f"<<LLM_ERROR: {e}>>"
                score = score_item(vid, item["format"], meta["valid_codes"], raw, truth)
                samples.append(score)
            per_model_scores[m][vid] = samples

        if verbose:
            print(f"    [{rid}/sensitivity] {vid:<10} done", flush=True)
        if persist_after_each_item is not None:
            persist_after_each_item(_snapshot())

    return _snapshot()


# ---------------------------------------------------------------------------
# Top-level run + persistence (resumable)
# ---------------------------------------------------------------------------

def _persist(records: list[dict], path: Path) -> None:
    """Atomically write records to `path` (write to .tmp then rename)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(records, indent=2, default=str))
    tmp.replace(path)


def _load_partial(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _completed_keys(records: list[dict]) -> set[tuple]:
    """Return set of (respondent_id, condition, model) tuples already done."""
    return {(r["respondent_id"], r["condition"], r["model"]) for r in records}


def _completed_sensitivity_items(records: list[dict], rid: int) -> dict[str, set[str]]:
    """For respondent rid, return {model: set of sensitivity item-ids already
    scored}. Used by run_phase1 to enable item-level sensitivity resume (P2.1).
    """
    out: dict[str, set[str]] = {}
    for r in records:
        if r.get("condition") != "sensitivity" or r.get("respondent_id") != rid:
            continue
        m = r.get("model")
        scored = set((r.get("per_item_scores") or {}).keys())
        out.setdefault(m, set()).update(scored)
    return out


def _upsert_sensitivity_records(all_records: list[dict], new_partial: list[dict]) -> None:
    """In-place upsert: for each (rid, 'sensitivity', model) record in
    new_partial, replace the matching record in all_records (or append).
    Item-level merging (per_item_scores union) is handled by the caller —
    new_partial already carries the union for the in-flight respondent.
    """
    index: dict[tuple, int] = {}
    for i, r in enumerate(all_records):
        if r.get("condition") == "sensitivity":
            index[(r["respondent_id"], r["model"])] = i
    for new in new_partial:
        key = (new["respondent_id"], new["model"])
        if key in index:
            all_records[index[key]] = new
        else:
            all_records.append(new)
            index[key] = len(all_records) - 1


def run_phase1(
    n: int,
    models: list[str] = list(MODEL_PANEL_PRIMARY),
    n_samples: int = 1,
    seed: int = 42,
    output_path: Path | None = None,
    do_primary: bool = True,
    do_sensitivity: bool = True,
    resume: bool = True,
    verbose: bool = True,
) -> Path:
    """Top-level driver. Sequential calls; resumable.

    Writes records (list of dicts) to output_path as a JSON file. Each record
    is one (respondent, condition, model). Per-condition prompt + per-item
    scores live inside `per_item_scores` in the record.
    """
    taxonomy = load_taxonomy()
    primary_eval_items = taxonomy["primary_eval"]["items"]
    sensitivity_eval_ids = list(taxonomy["sensitivity_eval"]["items"])

    sample = sample_respondents(n=n, seed=seed)
    if output_path is None:
        # Reproducibility-safe default name (matches the CLI block in __main__).
        # Encodes both the model panel and the seed so a notebook/programmatic
        # caller cannot silently overwrite a different-seed or different-models
        # run by passing output_path=None.
        model_tag = "-".join(m.split("/")[-1][:8] for m in models)
        output_path = OUTPUTS / f"gss_phase1_records_n{n}_{model_tag}_seed{seed}.json"

    existing = _load_partial(output_path) if resume else []
    done_keys = _completed_keys(existing)
    if existing:
        print(f"Resuming: {len(existing)} records already in {output_path.name}")

    all_records = list(existing)
    t0 = time.time()
    for ri, respondent in sample.iterrows():
        rid = int(respondent.get("ID_", -1))
        print(f"\n=== respondent {ri+1}/{n} (ID_={rid}, AGE={respondent.get('AGE')}) ===", flush=True)

        if do_primary:
            # Skip if all (resp, condition, model) tuples already done
            need_primary = any(
                (rid, c, m) not in done_keys
                for c, _ in CONDITIONS_PRIMARY for m in models
            )
            if need_primary:
                records = run_primary_one_respondent(
                    respondent, taxonomy, primary_eval_items,
                    models=models, n_samples=n_samples, verbose=verbose,
                )
                # Filter out any record that's already in done_keys (resume safety)
                new = [r for r in records if (r["respondent_id"], r["condition"], r["model"]) not in done_keys]
                all_records.extend(new)
                done_keys.update((r["respondent_id"], r["condition"], r["model"]) for r in new)
                _persist(all_records, output_path)
                print(f"  primary done; persisted {len(all_records)} records total")
            else:
                print(f"  primary already complete in resume file")

        if do_sensitivity:
            # P2.1: item-level resume. Compute, per model, the set of
            # sensitivity items already scored for this respondent. If every
            # model has all 118 items done, skip; otherwise pass the per-model
            # done-set into the runner so only missing items are re-issued.
            done_items_by_model = _completed_sensitivity_items(all_records, rid)
            n_total = len(sensitivity_eval_ids)
            all_models_complete = all(
                len(done_items_by_model.get(m, set())) >= n_total for m in models
            )
            if not all_models_complete:
                def _persist_partial(partial_records: list[dict]) -> None:
                    _upsert_sensitivity_records(all_records, partial_records)
                    _persist(all_records, output_path)

                records = run_sensitivity_one_respondent(
                    respondent, taxonomy, sensitivity_eval_ids,
                    models=models, n_samples=n_samples, verbose=verbose,
                    done_items_by_model=done_items_by_model,
                    persist_after_each_item=_persist_partial,
                )
                # Final upsert + persist for this respondent
                _upsert_sensitivity_records(all_records, records)
                done_keys.update(
                    (r["respondent_id"], r["condition"], r["model"]) for r in records
                )
                _persist(all_records, output_path)
                print(f"  sensitivity done; persisted {len(all_records)} records total")
            else:
                print(f"  sensitivity already complete in resume file")

        elapsed = time.time() - t0
        print(f"  elapsed {elapsed:.0f}s, {(ri+1)/elapsed*60:.1f} respondents/min")

    print(f"\n✓ phase1 run complete: {len(all_records)} records written to {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli():
    p = argparse.ArgumentParser(
        description="GSS Phase 1 driver — orchestrates LLM panel over GSS respondents."
    )
    p.add_argument("--n", type=int, default=10, help="number of respondents to run")
    p.add_argument("--seed", type=int, default=42, help="sampling seed (locked at 42)")
    p.add_argument("--smoke", action="store_true",
                   help="single-respondent, single-model, primary-only (cheapest possible test)")
    p.add_argument("--anchor", action="store_true",
                   help="GPT-4o anchor mode: 1 model (gpt-4o), n_samples=2, primary-only")
    p.add_argument("--primary-only", action="store_true",
                   help="skip sensitivity pass (saves ~60%% of LLM calls)")
    p.add_argument("--sensitivity-only", action="store_true",
                   help="skip primary pass (used to fill in sensitivity after primary completed)")
    p.add_argument("--models", default=None,
                   help="comma-separated model slugs (overrides default panel)")
    p.add_argument("--out", type=Path, default=None,
                   help="output JSON path (default: outputs/gss_phase1_records_n{N}.json)")
    p.add_argument("--no-resume", action="store_true",
                   help="ignore existing output file; restart from scratch")
    p.add_argument("--force-non-canonical-seed", action="store_true",
                   help="permit a non-42 seed run to overwrite an existing seed-42 "
                        "artifact (default: refuse). The locked Phase 1 seed is 42; "
                        "this flag exists ONLY for explicit reproducibility-drift tests.")
    return p.parse_args()


if __name__ == "__main__":
    import sys
    args = _cli()

    if args.smoke:
        models = ["qwen/qwen-2.5-72b-instruct"]
        n = 1
        n_samples = 1
        do_primary = True
        do_sensitivity = False
    elif args.anchor:
        models = [MODEL_ANCHOR]
        n = args.n
        n_samples = 2
        do_primary = True
        do_sensitivity = False
    else:
        if args.models:
            models = args.models.split(",")
            locked = set(MODEL_PANEL_PRIMARY)
            non_locked = [m for m in models if m not in locked]
            if non_locked:
                print(
                    f"WARNING [M-3]: --models override contains non-locked panel members: "
                    f"{non_locked}. The locked panel is {sorted(locked)}. "
                    f"Phase 1a/1b results MUST use the locked panel; non-locked runs are "
                    f"NOT pre-registered and must be reported as exploratory only.",
                    file=sys.stderr,
                )
        else:
            models = list(MODEL_PANEL_PRIMARY)
        n = args.n
        n_samples = 1
        do_primary = not args.sensitivity_only
        do_sensitivity = not args.primary_only

    if args.seed != 42:
        print(
            f"WARNING [I-10]: --seed={args.seed} differs from the locked seed=42. "
            f"Phase 1 pre-registration locks seed=42 for sampling, bootstrap, and "
            f"paired-bootstrap LOO. Non-canonical seeds produce results that are "
            f"NOT comparable to the pre-registered run.",
            file=sys.stderr,
        )

    print(f"=== GSS Phase 1 driver ===")
    print(f"  N respondents: {n}")
    print(f"  models:        {models}")
    print(f"  n_samples:     {n_samples}")
    print(f"  primary:       {do_primary}")
    print(f"  sensitivity:   {do_sensitivity}")
    print(f"  seed:          {args.seed}")

    seed_tag = f"_seed{args.seed}"
    model_tag = "-".join(m.split("/")[-1][:8] for m in models)
    out = args.out or (
        OUTPUTS / f"gss_phase1_records_n{n}_{model_tag}{seed_tag}.json"
    )

    # I-10 reproducibility guard: a non-42 run must not silently overwrite a
    # canonical seed-42 artifact at the same logical path. We check both the
    # explicit --out path AND the auto-generated path's seed-42 sibling so a
    # user who passes --out my_run.json with --seed 99 also gets the guard.
    if args.seed != 42 and not args.force_non_canonical_seed:
        canonical_sibling = (
            args.out.with_name(args.out.name.replace(seed_tag, "_seed42"))
            if args.out is not None and seed_tag in args.out.name
            else (
                OUTPUTS / f"gss_phase1_records_n{n}_{model_tag}_seed42.json"
            )
        )
        clobber_targets = []
        if out.exists():
            clobber_targets.append(out)
        if canonical_sibling.exists() and canonical_sibling != out:
            clobber_targets.append(canonical_sibling)
        if clobber_targets:
            print(
                f"REFUSING [I-10]: --seed={args.seed} (non-canonical) would overwrite "
                f"or shadow existing seed-42 artifact(s):\n"
                + "\n".join(f"    {p}" for p in clobber_targets)
                + "\nPass --force-non-canonical-seed to override explicitly, or rerun "
                "with --seed 42.",
                file=sys.stderr,
            )
            sys.exit(2)

    run_phase1(
        n=n,
        models=models,
        n_samples=n_samples,
        seed=args.seed,
        output_path=out,
        do_primary=do_primary,
        do_sensitivity=do_sensitivity,
        resume=not args.no_resume,
    )
