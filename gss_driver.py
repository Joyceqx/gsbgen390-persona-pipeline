"""GSS Phase 1 driver — top-level orchestrator that runs the LLM panel
across respondents × conditions × items × models, scores each call, and
persists results.

Audit primitives (prompts / scoring / aggregation) live in gss_pipeline.py.
LLM network layer lives in llm_router.py. This module only orchestrates.

Locked design (gss_phase1_design.md §12):
  - Cheap-panel primary: 4 OpenRouter models × n_samples=1
  - GPT-4o anchor: N=50 subset, n_samples=2, primary conditions only
  - Sensitivity pass: per-item exclusion, all 4 cheap models × n_samples=1

Usage:
    # Smoke test — 1 respondent, 1 model, primary conditions only
    python3 gss_driver.py --smoke

    # Full N=10 smoke — 4 cheap models, primary + sensitivity
    python3 gss_driver.py --n 10

    # Full N=10 primary only (skip sensitivity to save cost)
    python3 gss_driver.py --n 10 --primary-only

    # GPT-4o anchor on N=50 subset (only after cheap-panel run is in)
    python3 gss_driver.py --anchor --n 50
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
    # WLTH* battery — true scale 1-7, codebook only anchors at 1 and 7
    "WLTHWHTS": {"format": "likert7", "valid_codes": [1,2,3,4,5,6,7], "is_sparse": True},
    "WLTHBLKS": {"format": "likert7", "valid_codes": [1,2,3,4,5,6,7], "is_sparse": True},
    "WLTHHSPS": {"format": "likert7", "valid_codes": [1,2,3,4,5,6,7], "is_sparse": True},
    # COL* / SPK* / LIB* batteries — codebook may include meta-codes;
    # observed substantive values are 1=ALLOWED / 2=NOT ALLOWED for newer waves.
    # Treat as binary on substantive codes only.
    "COLATH":   {"format": "binary", "valid_codes": [1,2], "is_sparse": False},
    "COLRAC":   {"format": "binary", "valid_codes": [1,2], "is_sparse": False},
    "LIBRAC":   {"format": "binary", "valid_codes": [1,2], "is_sparse": False},
    "SPKRAC":   {"format": "binary", "valid_codes": [1,2], "is_sparse": False},
    "SPKATH":   {"format": "binary", "valid_codes": [1,2], "is_sparse": False},
    "COLCOM":   {"format": "binary", "valid_codes": [1,2], "is_sparse": False},
    "LIBCOM":   {"format": "binary", "valid_codes": [1,2], "is_sparse": False},
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
) -> list[dict]:
    """For one respondent: each sensitivity item gets its own per-item-excluded
    persona prompt. Returns one record per model, with per_item_scores keyed
    by sensitivity_item_id."""
    rid = int(respondent.get("ID_", -1))
    per_model_scores: dict[str, dict[str, list[dict]]] = {m: {} for m in models}

    for vid in sensitivity_eval_ids:
        item = derive_sensitivity_item(vid)
        if item is None:
            continue
        # Build system prompt with this specific item excluded
        system, _ = build_persona_prompt(
            respondent, taxonomy, drop_bin=None, exclude_vars=[vid]
        )
        question, meta = format_eval_question(item)
        truth = truth_code_or_none(respondent.get(vid), vid)

        for m in models:
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

    return [
        {
            "respondent_id": rid,
            "condition": "sensitivity",
            "model": m,
            "n_samples": n_samples,
            "per_item_scores": per_item,
        }
        for m, per_item in per_model_scores.items()
    ]


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
        output_path = OUTPUTS / f"gss_phase1_records_n{n}.json"

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
            need_sens = any((rid, "sensitivity", m) not in done_keys for m in models)
            if need_sens:
                records = run_sensitivity_one_respondent(
                    respondent, taxonomy, sensitivity_eval_ids,
                    models=models, n_samples=n_samples, verbose=verbose,
                )
                new = [r for r in records if (r["respondent_id"], r["condition"], r["model"]) not in done_keys]
                all_records.extend(new)
                done_keys.update((r["respondent_id"], r["condition"], r["model"]) for r in new)
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
    return p.parse_args()


if __name__ == "__main__":
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
        models = (
            args.models.split(",") if args.models else list(MODEL_PANEL_PRIMARY)
        )
        n = args.n
        n_samples = 1
        do_primary = not args.sensitivity_only
        do_sensitivity = not args.primary_only

    print(f"=== GSS Phase 1 driver ===")
    print(f"  N respondents: {n}")
    print(f"  models:        {models}")
    print(f"  n_samples:     {n_samples}")
    print(f"  primary:       {do_primary}")
    print(f"  sensitivity:   {do_sensitivity}")
    print(f"  seed:          {args.seed}")

    out = args.out or (OUTPUTS / f"gss_phase1_records_n{n}_{'-'.join([m.split('/')[-1][:8] for m in models])}.json")
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
