"""GSS Phase 1 driver — top-level orchestrator that runs the LLM panel
across respondents × conditions × items × models, scores each call, and
persists results.

Audit primitives (prompts / scoring / aggregation) live in gss_pipeline.py.
LLM network layer lives in llm_router.py. This module only orchestrates.

Locked design (gss_phase1_design.md §12; sample sizes revised 2026-05-09 night
per Audit-3 + Joyce decision; sensitivity scope revised 2026-05-10 per Joyce
decision Option A):
  - Phase 1a (N=200): 4 cheap OpenRouter models × n_samples=1, **primary_eval
    ONLY** (12 items × 5 conditions = 60 prompts/model/respondent), with a
    locked 100/100 selection/validation split per §12.2 (selector scores ONLY
    on the selection-half; validation-half held out for post-selection-
    inference defense).
  - Phase 1b (N=3,309 — full GSS 2024 cross-section): single §12.2-quality-
    selected model × n_samples=1, **primary_eval ONLY** (60 prompts/respondent;
    argmin selection-MAE among DQ-passers; cost is tie-break only; all-DQ-fail
    PAUSES for human review rather than silently bypassing the gate to Qwen).
  - GPT-4o anchor: N=100 selection-split subset, n_samples=2, **primary +
    sensitivity** (60 + 118 = 178 prompts × n=2 = 356 calls/respondent — the
    ONLY Park-comparable run; produces the per-item raw-accuracy anchor table
    side-by-side with Park v2 SI Table 3 per OSF §3.2). One anchor invocation
    serves both Phase 1a and Phase 1b reporting purposes.
  - Sensitivity pass scope (locked 2026-05-10 Option A): **anchor-only**.
    Cheap panel + selected 1b model do NOT run sensitivity_eval — those
    headline runs are primary_eval only. Earlier docs that listed sensitivity
    on cheap models or 1b model are superseded by Option A.
  - 4-cheap panel: Qwen-2.5-72B / DeepSeek-V3.1 / Llama-3.3-70B-Instruct (Meta) /
    Kimi K2 (3 China-trained + 1 Western-trained for cross-family balance;
    MiniMax-M1 → Llama swap locked pre-OSF per Audit-3).

Usage (LOCKED Phase 1 paid runs — use named modes; locked 2026-05-29 per
post-factorial audit; legacy --smoke / --anchor flags below are debug-only):

    # Phase 1a — N=200 cheap-panel × 3 prompts × FULL CONDITION ONLY × n_samples=2.
    # LOO conditions are deferred to Phase 1b (run on the selected cell × N=3,309
    # disjoint cohort, where they actually power the §8 LOO ΔMAE headline).
    # Ballot-off items (no GSS truth) are skipped before the LLM call. Cost: ~$14.
    python3 gss_driver.py --phase1a

    # §7 joint (model, prompt) cell selector — reads outputs/phase1a_raw.parquet:
    python3 select_phase1b_cell.py outputs/phase1a_raw.parquet

    # Phase 1b — N=3,309 × single §7-selected cell × primary-only × Full + 4 LOO
    # × n_samples=1. Headline cohort excludes the 200 selector respondents
    # (N=3,109 disjoint); full N=3,309 reported as sensitivity. Cost: ~$48.
    python3 gss_driver.py --phase1b \\
        --phase1b-model qwen/qwen-2.5-72b-instruct \\
        --phase1b-prompt P0
    # (replace slug + prompt with the actual selector output)

    # GPT-4o anchor — N=100 selection-split subset × primary + sensitivity
    # (the only Park-comparable run; produces the Park v2 SI Table 3 anchor
    # table). One invocation serves both Phase 1a and Phase 1b reporting.
    # Cost: ~$148.
    python3 gss_driver.py --phase1b-anchor

    # Phase 1c stubs (orchestration runtime not yet implemented; analyzer
    # ready — see osf_preregistration_v1.md §13.2).
    python3 gss_driver.py --battery-loo  # NOT IMPLEMENTED — prints OSF pointer
    python3 gss_driver.py --shapley      # NOT IMPLEMENTED — same status

DEBUG / smoke (NOT for paid runs; sensitivity scope here is legacy):
    python3 gss_driver.py --smoke        # 1 respondent × 1 model × primary

See `RUNBOOK.md` for the full step-by-step paid-run sequence + expected
output paths + cost projection per step.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import pandas as pd

from gss_loader import load_gss
from gss_pipeline import (
    BIN_DISPLAY,
    battery_excludes_for_item,
    build_persona_prompt,  # legacy P0-only; still used by the sensitivity pass
    format_eval_question,
    load_battery_map,
    load_taxonomy,
    sample_respondents,
    score_item,
    truth_code_or_none,
    _scale_options_for,
)
from prompt_variants import (
    build_prompt as build_prompt_variant,  # P0/P1/P2 dispatcher used by --phase1a
    PROMPT_VERSION,
    TEMPLATE_HASH,
)
from llm_router import (
    MODEL_ANCHOR,
    MODEL_PANEL_PRIMARY,
    LLMError,
    call_llm,
)

WORK = Path("/Users/joyce/Developer/gsbgen390")
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
# Per-call seed derivation (locked 2026-05-09 night per Audit-2 critical fix)
# ---------------------------------------------------------------------------
# A single hardcoded seed=42 across all calls would collapse GPT-4o n_samples=2
# self-consistency to deterministic identity (same prompt + same seed → same
# reply, if the provider honors seed). We derive a per-call seed from a stable
# hash of (rid, condition, item_id, model, sample_idx) so:
#   - same (rid, cond, item, model, sample_idx) → same seed → reproducible.
#   - different sample_idx → different seed → genuine within-prompt variation
#     when n_samples > 1 (e.g., GPT-4o anchor with n_samples=2).
# Seed is a hint per llm_router.py docstring; provider honoring is verified at
# smoke-test time.
SEED_BASE = 42

def _derive_seed(
    rid: int,
    condition: str,
    item_id: str,
    model: str,
    sample_idx: int,
    prompt_id: str = "P0",
) -> int:
    """Per-call deterministic seed. `prompt_id` is part of the payload so the
    3-prompt factorial does not share seeds across P0/P1/P2 — if it did, the
    provider could give correlated answers to (rid, item, model) for the three
    prompt variants, biasing the prompt comparison towards zero. The default
    "P0" lets sensitivity-pass and smoke-test callers stay one-liners; it is
    NOT byte-equal to the pre-2026-05-28 OSF-v1 seed format (which had no
    prompt_id in the payload), so any cached pre-factorial records would
    re-roll seeds on resume. No paid factorial run has been launched yet, so
    this seed-format break is internal-only."""
    payload = f"{SEED_BASE}|{rid}|{condition}|{item_id}|{model}|{prompt_id}|{sample_idx}".encode("utf-8")
    h = hashlib.sha256(payload).digest()
    return int.from_bytes(h[:4], "big") & 0x7FFFFFFF


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
    prompt_id: str = "P0",
    n_samples: int = 1,
    temperature: float = 0.7,
    verbose: bool = True,
) -> list[dict]:
    """For one respondent: 5 conditions × 12 items × len(models) × n_samples calls.
    Returns a list of records, one per (condition, model).

    R1 (locked 2026-05-08, gss_phase1_design.md §9c.R1): battery exclusion is
    applied PER ITEM. When predicting any item that belongs to a battery (per
    `gss_battery_map.json`), the entire battery is excluded from the persona
    prompt for that prediction. This mirrors Park v2's BFI whole-trait-block
    hold-out rule (Park v2 SI §5, PDF p.37) and defends against constructive
    auto-correlation in the attitudinal feature bin (e.g., ABDEFECT/ABNOMORE
    leaking into ABANY prediction).

    Singleton items (PARTYID, POLVIEWS, CAPPUN, GUNLAW, SATFIN) get only the
    predicted item itself excluded (a no-op since primary_eval is already
    disjoint from feature bins per the validator).
    """
    rid = int(respondent.get("ID_", -1))
    records: list[dict] = []
    battery_map = load_battery_map()

    for cond_name, drop_bin in CONDITIONS_PRIMARY:
        per_model_scores: dict[str, dict[str, list[dict]]] = {m: {} for m in models}
        # Track per-item prompt stats for transparency (each item now has its
        # own battery-excluded prompt rather than a single shared prompt).
        per_item_prompt_stats: dict[str, dict] = {}

        for item in primary_eval_items:
            # R1: battery exclusion per item
            excludes = battery_excludes_for_item(item["id"], battery_map)
            out = build_prompt_variant(
                respondent, taxonomy,
                prompt_id=prompt_id,
                drop_bin=drop_bin,
                exclude_vars=excludes,
            )
            # The SYSTEM_INSTRUCTION (constant across P0/P1/P2 — audit #4) is
            # prepended to the persona body so call_llm's `system` argument
            # carries the same instruction text for every prompt variant; only
            # the persona section differs across cells.
            system = out["system_instruction"] + "\n\n" + out["persona_prompt"]
            per_item_prompt_stats[item["id"]] = {
                "prompt_id": out["metadata"]["prompt_id"],
                "feature_count": out["metadata"]["feature_count"],
                "char_count": out["metadata"]["char_count"],
                "approx_tokens": out["metadata"]["approx_tokens"],
                "bin_counts": out["metadata"]["bin_counts"],
                "battery_excluded": sorted(excludes),
            }

            question, meta = format_eval_question(item)
            truth = truth_code_or_none(respondent.get(item["id"]), item["id"])
            for m in models:
                samples: list[dict] = []
                for s_idx in range(n_samples):
                    seed = _derive_seed(rid, cond_name, item["id"], m, s_idx, prompt_id=prompt_id)
                    try:
                        raw = call_llm(system, question, model=m,
                                        temperature=temperature, seed=seed)
                    except LLMError as e:
                        raw = f"<<LLM_ERROR: {e}>>"
                    score = score_item(
                        item["id"], item["format"], meta["valid_codes"], raw, truth
                    )
                    score["seed"] = seed  # record for reproducibility audit
                    samples.append(score)
                per_model_scores[m][item["id"]] = samples
            if verbose:
                print(f"    [{rid}/{cond_name}] item {item['id']:<10} done", flush=True)

        for m, per_item in per_model_scores.items():
            records.append({
                "respondent_id": rid,
                "condition": cond_name,
                "model": m,
                "prompt_id": prompt_id,
                "prompt_version": PROMPT_VERSION,
                "template_hash": TEMPLATE_HASH[:16],
                "n_samples": n_samples,
                "per_item_scores": per_item,
                "per_item_prompt_stats": per_item_prompt_stats,
                "r1_battery_exclusion": True,
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
    existing_per_model_scores: dict[str, dict[str, list[dict]]] | None = None,
    persist_after_each_item: "Callable[[list[dict]], None] | None" = None,
) -> list[dict]:
    """For one respondent: each sensitivity item gets its own per-item-excluded
    persona prompt. Returns one record per model, with per_item_scores keyed
    by sensitivity_item_id.

    Item-level resume (P2.1, fix locked 2026-05-09 night per Audit-2 critical):
      - `done_items_by_model[m]` lists item ids ALREADY scored for model m on
        this respondent; those items are skipped per model.
      - `existing_per_model_scores[m]` carries the previously-scored item-list
        dicts so the snapshot/upsert preserves them. If absent, the snapshot
        contains only newly-completed items and the caller's REPLACE-style
        upsert silently nukes the prior items (the bug the audit flagged).
      - If `persist_after_each_item` is supplied, it's called after every
        sensitivity item (across all models) finishes, with the current
        partial-records snapshot. The caller persists. This bounds the worst-
        case rerun on interruption to ONE in-flight item per respondent×model
        rather than the full ~118-item block.
    """
    rid = int(respondent.get("ID_", -1))
    skip = done_items_by_model or {m: set() for m in models}
    # Pre-populate with previously-scored items so the snapshot carries them
    # forward across resume + persist cycles. Deep-copy the per-item lists so
    # the caller's records aren't mutated.
    per_model_scores: dict[str, dict[str, list[dict]]] = {m: {} for m in models}
    if existing_per_model_scores:
        for m, items_done in existing_per_model_scores.items():
            if m in per_model_scores:
                per_model_scores[m] = {k: list(v) for k, v in items_done.items()}

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
                seed = _derive_seed(rid, "sensitivity", vid, m, s_idx)
                try:
                    raw = call_llm(system, question, model=m,
                                    temperature=temperature, seed=seed)
                except LLMError as e:
                    raw = f"<<LLM_ERROR: {e}>>"
                score = score_item(vid, item["format"], meta["valid_codes"], raw, truth)
                score["seed"] = seed  # record for reproducibility audit
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
    """Return set of (respondent_id, condition, model, prompt_id) tuples
    already done. Sensitivity-pass records (legacy, P0-only) are stamped
    with prompt_id="P0" for compatibility."""
    return {
        (r["respondent_id"], r["condition"], r["model"], r.get("prompt_id", "P0"))
        for r in records
    }


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


def _existing_sensitivity_per_model_scores(
    records: list[dict], rid: int
) -> dict[str, dict[str, list[dict]]]:
    """For respondent rid, return {model: {item_id: [score_dicts...]}} of
    previously-completed sensitivity items. Used to pre-populate the runner
    so the upsert preserves prior items across resume cycles (Audit-2 fix).
    """
    out: dict[str, dict[str, list[dict]]] = {}
    for r in records:
        if r.get("condition") != "sensitivity" or r.get("respondent_id") != rid:
            continue
        m = r.get("model")
        if m is None:
            continue
        existing = r.get("per_item_scores") or {}
        out.setdefault(m, {}).update(existing)
    return out


def _upsert_sensitivity_records(all_records: list[dict], new_partial: list[dict]) -> None:
    """In-place upsert: for each (rid, 'sensitivity', model) record in
    new_partial, MERGE the per_item_scores into the matching record in
    all_records (or append). Locked 2026-05-09 night per Audit-2 critical fix:
    previously this REPLACED the old record with `new`, silently dropping
    items that had been completed in earlier resume cycles. Deep-merge the
    per_item_scores dicts (new wins on key conflict, which only matters if
    the same item was scored twice — should not happen in a correctly-resuming
    run, and if it does, the most recent score is kept).
    """
    index: dict[tuple, int] = {}
    for i, r in enumerate(all_records):
        if r.get("condition") == "sensitivity":
            index[(r["respondent_id"], r["model"])] = i
    for new in new_partial:
        key = (new["respondent_id"], new["model"])
        if key in index:
            old = all_records[index[key]]
            old_items = old.get("per_item_scores") or {}
            new_items = new.get("per_item_scores") or {}
            merged = dict(old_items)
            merged.update(new_items)  # new wins on collision (rare; same-item rerun)
            merged_record = dict(new)
            merged_record["per_item_scores"] = merged
            all_records[index[key]] = merged_record
        else:
            all_records.append(new)
            index[key] = len(all_records) - 1


def run_phase1(
    n: int,
    models: list[str] = list(MODEL_PANEL_PRIMARY),
    prompt_id: str = "P0",
    n_samples: int = 1,
    seed: int = 42,
    output_path: Path | None = None,
    do_primary: bool = True,
    do_sensitivity: bool = True,
    resume: bool = True,
    verbose: bool = True,
    force_resume_partial: bool = False,
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

    # Audit-fresh-4 P1 partial-resume guard (locked 2026-05-10 night).
    # If the driver finds an existing artifact at the canonical output path
    # but its record count is suspiciously small for the planned (n × models ×
    # conditions) shape, refuse to silently resume — most likely the file is
    # a stray smoke/test partial. The user must explicitly confirm by either
    # (a) deleting the file (and re-running with --no-resume implicit) OR
    # (b) passing --force-resume-partial to acknowledge the partial state.
    if existing and resume:
        n_models = len(models) if models else 1
        # Conservative lower-bound on expected records for a realistic resume
        # of an interrupted full run: at least 5% of the full record count.
        # Each respondent contributes one record per (condition × model):
        #   - primary pass: 5 conditions (Full + 4 single-bin LOO)
        #   - sensitivity pass: 1 condition ("sensitivity")
        # Bug fix locked 2026-05-10 night per Audit-fresh-5 RevB P2 review:
        # earlier formula was `n * n_models` (no condition factor), which made
        # the 5% threshold equivalent to ~1% of real records — Phase 1a's true
        # 4,000-record full run let stray ~200-record partials through. The
        # corrected formula multiplies by the per-respondent record count.
        records_per_respondent_per_model = (
            (5 if do_primary else 0) + (1 if do_sensitivity else 0)
        )
        if records_per_respondent_per_model == 0:
            # No primary AND no sensitivity → guard is moot; skip
            records_per_respondent_per_model = 1
        expected_full_records = n * n_models * records_per_respondent_per_model
        partial_threshold = max(int(expected_full_records * 0.05), 20)
        if (
            len(existing) < partial_threshold
            and len(existing) < expected_full_records
            and not force_resume_partial
        ):
            cond_factor = records_per_respondent_per_model
            print(
                f"REFUSING [partial-resume guard]: existing artifact at\n"
                f"    {output_path}\n"
                f"  has only {len(existing)} record(s); the planned run "
                f"shape (N={n} × {n_models} models × {cond_factor} "
                f"condition-records/respondent) expects ~{expected_full_records} "
                f"records when complete, so resume is meaningful only above "
                f"{partial_threshold} (5% of expected). "
                f"This suggests the file is a stray smoke/test partial that "
                f"would silently corrupt a paid run.\n\n"
                f"  Options:\n"
                f"    1. Move/delete the partial file:\n"
                f"         mv {output_path} {output_path}.partial-stray\n"
                f"       Then re-run; the driver will start fresh.\n"
                f"    2. Acknowledge and force resume from the partial:\n"
                f"         (re-invoke with --force-resume-partial)\n"
                f"    3. Run with --no-resume to ignore the file entirely\n"
                f"       (NOTE: --no-resume will OVERWRITE the existing file).",
                file=sys.stderr,
            )
            sys.exit(2)

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
            # done_keys now includes prompt_id since records vary by (rid, cond, model, prompt_id).
            need_primary = any(
                (rid, c, m, prompt_id) not in done_keys
                for c, _ in CONDITIONS_PRIMARY for m in models
            )
            if need_primary:
                records = run_primary_one_respondent(
                    respondent, taxonomy, primary_eval_items,
                    models=models, prompt_id=prompt_id,
                    n_samples=n_samples, verbose=verbose,
                )
                # Filter out any record that's already in done_keys (resume safety)
                new = [r for r in records if (r["respondent_id"], r["condition"], r["model"], r["prompt_id"]) not in done_keys]
                all_records.extend(new)
                done_keys.update((r["respondent_id"], r["condition"], r["model"], r["prompt_id"]) for r in new)
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
            existing_pms = _existing_sensitivity_per_model_scores(all_records, rid)
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
                    existing_per_model_scores=existing_pms,
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
        description="GSS Phase 1 driver — orchestrates LLM panel over GSS respondents.",
        epilog=(
            "Locked Phase 1 named modes (recommended; locked 2026-05-09 night per "
            "Audit-fresh review; sensitivity scope locked 2026-05-10 per Joyce "
            "decision Option A): use --phase1a / --phase1b / --phase1b-anchor to "
            "invoke the OSF-locked paid-run configuration in one flag. "
            "(--battery-loo / --shapley are NOT-IMPLEMENTED stubs that print a "
            "clear OSF §13.2 pointer — analyzer is ready, orchestration runtime "
            "deferred until before Phase 1c.) Manual flag composition (--n, "
            "--models, etc.) is preserved for debugging, but for paid runs at "
            "the locked ~$756 budget (Option A: cheap-panel primary-only + "
            "anchor with sensitivity), use the named modes — they pin N + panel "
            "+ sensitivity scope to the locked spec. See RUNBOOK.md for the "
            "step-by-step paid-run sequence with expected outputs + cost per step."
        ),
    )

    # Locked Phase 1 named modes (Audit-fresh fix; mutually exclusive).
    # Sensitivity scope locked 2026-05-10 per Joyce decision Option A:
    # cheap models = primary_eval only; GPT-4o anchor = primary + sensitivity_eval
    # (the only Park-comparable run, per OSF §3.2).
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--phase1a", action="store_true",
                      help="Phase 1a (N=200, 4 cheap panel, n_samples=1, "
                           "PRIMARY ONLY — sensitivity_eval is anchor-only per "
                           "OSF §3.2). The 100/100 selection/validation split is "
                           "enforced downstream by select_phase1b_model.py CLI.")
    mode.add_argument("--phase1b", action="store_true",
                      help="Phase 1b (N=3,309 full GSS 2024 cross-section, single "
                           "§12.2-selected model, n_samples=1, PRIMARY ONLY — "
                           "sensitivity_eval is anchor-only per OSF §3.2). "
                           "REQUIRES --phase1b-model SLUG (the §12.2 selector output).")
    mode.add_argument("--phase1b-anchor", action="store_true",
                      help="GPT-4o anchor (N=100 selection-split subset; one run "
                           "serves both Phase 1a and Phase 1b reporting), "
                           "n_samples=2, PRIMARY + SENSITIVITY (the only Park-"
                           "comparable run per OSF §3.2; produces the per-item "
                           "raw-accuracy table side-by-side with Park v2 SI Table 3).")
    mode.add_argument("--battery-loo", action="store_true",
                      help="Phase 1c Battery LOO orchestration. NOT YET IMPLEMENTED — "
                           "the analyzer (battery_loo.py) is implemented and self-tested; "
                           "the gss_driver.py runtime extension that emits "
                           "condition='battery_loo_drop_<name>' records is the deferred "
                           "implementation work disclosed in osf_preregistration_v1.md "
                           "§13.2.")
    mode.add_argument("--shapley", action="store_true",
                      help="Phase 1c Shapley 16-condition enumeration. NOT YET "
                           "IMPLEMENTED — same status as --battery-loo (analyzer "
                           "implemented, driver runtime deferred per OSF §13.2).")

    p.add_argument("--phase1b-model", default=None,
                   help="Required with --phase1b. The §7-selected model slug.")
    p.add_argument("--phase1b-prompt", default=None, choices=["P0", "P1", "P2"],
                   help="Required with --phase1b after Phase 1A factorial. The §7-selected "
                        "prompt ID (one of P0 / P1 / P2). Defaults to P0 for backward "
                        "compatibility with OSF v1 single-prompt records.")

    # Legacy / debugging flags (preserved).
    p.add_argument("--n", type=int, default=10, help="number of respondents to run")
    p.add_argument("--seed", type=int, default=42, help="sampling seed (locked at 42)")
    p.add_argument("--smoke", action="store_true",
                   help="single-respondent, single-model, primary-only (cheapest possible test)")
    p.add_argument("--anchor", action="store_true",
                   help="LEGACY: GPT-4o anchor (use --phase1b-anchor for the locked Phase 1b anchor).")
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
    p.add_argument("--allow-panel-wide-large-n", action="store_true",
                   help="bypass the panel-wide-large-N cost guard (Audit-fresh-2 F9). "
                        "Default: refuse to run --n >= 1000 with >1 model + sensitivity "
                        "since this would burn ~$836 for the 4-model × N=3309 × full-178-prompt "
                        "panel-wide grid (Phase 1b is locked to a SINGLE §12.2-selected model). "
                        "Pass this flag only for an intentional cross-panel reanalysis with "
                        "explicit budget approval.")
    p.add_argument("--force-resume-partial", action="store_true",
                   help="bypass the partial-resume guard (Audit-fresh-4 P1). Default: "
                        "refuse to resume from an existing artifact whose record count "
                        "is suspiciously small for the planned (n × models) shape "
                        "(<5%% of expected primary-pass records, with a floor of 20). "
                        "Pass this flag ONLY when intentionally continuing a known-"
                        "interrupted real run; for stray smoke artifacts, delete the "
                        "file first instead.")
    return p.parse_args()


if __name__ == "__main__":
    import sys
    args = _cli()

    # Stub modes (analyzer exists; orchestration runtime deferred per OSF §13.2).
    if args.battery_loo or args.shapley:
        which = "Battery LOO" if args.battery_loo else "Shapley 16-condition"
        print(
            f"NOT IMPLEMENTED: --{'battery-loo' if args.battery_loo else 'shapley'} "
            f"orchestration is deferred runtime work.\n\n"
            f"  Status (locked 2026-05-09 night, disclosed in osf_preregistration_v1.md\n"
            f"  §13.2 + gss_phase1_design.md §9f):\n"
            f"    - {which} ANALYZER is implemented and self-tested\n"
            f"      ({'battery_loo.py' if args.battery_loo else 'shapley_decomposition.py'} "
            f"--self-test passes).\n"
            f"    - {which} ORCHESTRATION DRIVER (this file's extension to enumerate\n"
            f"      condition='{('battery_loo_drop_<name>' if args.battery_loo else 'shapley_<subset>')}' \n"
            f"      records) remains to be built before any paid Phase 1c run.\n\n"
            f"  Why deferred: per OSF lock-first defense, the analysis contract\n"
            f"  (analyzer + spec in tier1_tool_schemas.md Tools 1-2) is locked at\n"
            f"  OSF time; the orchestration is implemented faithfully to that spec\n"
            f"  before Phase 1c. Schema + design cannot change post-OSF; only the\n"
            f"  runtime implementation timing.\n",
            file=sys.stderr,
        )
        sys.exit(2)

    # Locked Phase 1 named modes (Audit-fresh fix). Prefer these over manual
    # composition for paid runs.
    if args.phase1a:
        models = list(MODEL_PANEL_PRIMARY)
        n = 200
        n_samples = 1
        do_primary = True
        # Locked Option A 2026-05-10 (Joyce decision per Audit-fresh-2 P1 sensitivity-
        # scope review): cheap panel runs primary ONLY. sensitivity_eval is the 118-item
        # Park-comparable benchmark, used only for the GPT-4o anchor side-by-side table
        # against Park v2 SI Table 3 (per OSF §3.2). Cheap panel sensitivity adds
        # nothing to the headline 4-bin LOO / Battery LOO / §12.2 selector and is
        # excluded to keep budget honest (~$71 saved per Phase 1a + Phase 1b combined).
        do_sensitivity = False
        print(
            "  [mode=--phase1a] N=200, 4-cheap panel locked from MODEL_PANEL_PRIMARY, "
            "primary ONLY (sensitivity_eval is anchor-only per OSF §3.2).\n"
            "  After this completes, run: python3 select_phase1b_model.py "
            f"<output.json> (the CLI auto-derives the locked 100/100 split via "
            "_derive_phase1a_split — do NOT pass --no-split for paid runs.)",
            file=sys.stderr,
        )
    elif args.phase1b:
        if not args.phase1b_model:
            print(
                "ERROR: --phase1b requires --phase1b-model SLUG (the §12.2-selected "
                "model slug, e.g., 'qwen/qwen-2.5-72b-instruct'). Run "
                "select_phase1b_model.py on Phase 1a output first to determine the "
                "locked-rule selection.",
                file=sys.stderr,
            )
            sys.exit(2)
        models = [args.phase1b_model]
        n = 3309
        n_samples = 1
        do_primary = True
        # Locked Option A 2026-05-10: cheap panel sensitivity off (same rationale
        # as --phase1a above; sensitivity_eval is anchor-only per OSF §3.2).
        do_sensitivity = False
        print(
            f"  [mode=--phase1b] N=3,309 (full GSS 2024), single §12.2-selected "
            f"model: {args.phase1b_model}, primary ONLY "
            f"(sensitivity_eval is anchor-only per OSF §3.2).",
            file=sys.stderr,
        )
    elif args.phase1b_anchor:
        models = [MODEL_ANCHOR]
        n = 100
        n_samples = 2
        do_primary = True
        # Locked Option A 2026-05-10: ANCHOR runs sensitivity_eval (this is the
        # only Park-comparable run; produces the side-by-side per-item raw
        # accuracy table against Park v2 SI Table 3 per OSF §3.2). Single anchor
        # invocation on the N=100 selection split serves both Phase 1a and
        # Phase 1b reporting purposes.
        do_sensitivity = True
        print(
            "  [mode=--phase1b-anchor] N=100 selection-split subset, GPT-4o, "
            "n_samples=2, primary + sensitivity (Park-comparable Table 3 anchor "
            "table per OSF §3.2; locked 2026-05-10 Joyce decision Option A).",
            file=sys.stderr,
        )
    elif args.smoke:
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

    # Audit-fresh-2 F9: panel-wide large-N cost guard.
    # Refuse to run >1 model at N>=1000 with sensitivity unless --allow-panel-
    # wide-large-n is explicitly passed. The named --phase1b mode hard-codes a
    # single model (so it bypasses this guard), but a manual command like
    # `--n 3309` with the default 4-cheap panel + sensitivity would burn ~$836
    # vs the planned ~$209 single-model 1b run.
    if (
        n >= 1000
        and len(models) > 1
        and do_sensitivity
        and not args.allow_panel_wide_large_n
    ):
        # Approximate cost: per-respondent prompts × n × models × $/call
        # 178 = 60 primary + 118 sensitivity per the locked design.
        approx_calls = 178 * n * len(models)
        approx_cost = approx_calls * 0.000356
        print(
            f"REFUSING [F9 cost guard]: --n={n} with {len(models)} models AND "
            f"sensitivity pass would dispatch ~{approx_calls:,} LLM calls "
            f"(~${approx_cost:,.0f}). The locked Phase 1b design (per §12.2) "
            f"runs a SINGLE §12.2-selected model at N=3,309 (~$209). To "
            f"replicate that, use:\n"
            f"    python3 gss_driver.py --phase1b --phase1b-model SLUG\n"
            f"\n"
            f"If you intentionally want a cross-panel reanalysis at large N, "
            f"pass --allow-panel-wide-large-n explicitly AND ensure the "
            f"resulting cost is approved.",
            file=sys.stderr,
        )
        sys.exit(2)

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

    # Resolve which prompt variants to run. --phase1a runs the 3-prompt factorial
    # (P0 + P1 + P2). --phase1b runs the single §7-selected (model, prompt) cell;
    # if the factorial parquet exists then --phase1b-prompt is REQUIRED (Phase 1B
    # headlines the §7-selected cell — silently defaulting to P0 would risk
    # running Phase 1B on a prompt the selector did not choose). If no factorial
    # has been run yet (OSF-v1 backward compatibility path), --phase1b-prompt
    # may be omitted and defaults to P0. The anchor mode is locked to P0
    # (per RESEARCH_DESIGN.md §5.5 — Park v2 SI Table 3 anchor comparability).
    if args.phase1a:
        prompt_ids = ["P0", "P1", "P2"]
    elif args.phase1b:
        factorial_parquet = OUTPUTS / "phase1a_raw.parquet"
        if args.phase1b_prompt is None and factorial_parquet.exists():
            print(
                f"REFUSING: --phase1b-prompt is required when {factorial_parquet.name} "
                f"exists (the factorial has run; Phase 1B should use the §7-selected "
                f"prompt). Run `python3 src/select_phase1b_cell.py "
                f"{factorial_parquet}` to choose the cell, then pass "
                f"--phase1b-prompt {{P0,P1,P2}}.",
                file=sys.stderr,
            )
            sys.exit(2)
        prompt_ids = [args.phase1b_prompt or "P0"]
    else:
        prompt_ids = ["P0"]

    per_prompt_outputs: list[Path] = []
    for pid in prompt_ids:
        per_prompt_out = (
            out.with_name(out.stem + f"_{pid}" + out.suffix)
            if len(prompt_ids) > 1
            else out
        )
        per_prompt_outputs.append(per_prompt_out)
        run_phase1(
            n=n,
            models=models,
            prompt_id=pid,
            n_samples=n_samples,
            seed=args.seed,
            output_path=per_prompt_out,
            do_primary=do_primary,
            do_sensitivity=do_sensitivity,
            resume=not args.no_resume,
            force_resume_partial=args.force_resume_partial,
        )

    # After --phase1a completes the 3-prompt factorial, consolidate the per-prompt
    # JSON artifacts into the canonical long-format parquet (RESEARCH_DESIGN.md
    # §6.2). The §7 selector reads the parquet, not the JSONs. Failure here is
    # non-fatal — the JSON artifacts are the source of truth and the writer can
    # be re-run manually via `python3 src/write_phase1a_parquet.py --inputs ...`.
    if args.phase1a and len(per_prompt_outputs) == 3:
        try:
            from write_phase1a_parquet import build_dataframe
            parquet_out = OUTPUTS / "phase1a_raw.parquet"
            print(f"\nConsolidating 3 per-prompt JSONs → {parquet_out.name}")
            df = build_dataframe(per_prompt_outputs)
            df.to_parquet(parquet_out, index=False)
            print(
                f"  wrote {len(df):,} rows  "
                f"({df.groupby(['model', 'prompt']).ngroups} cells, "
                f"{df['item'].nunique()} items)"
            )
        except Exception as e:
            print(
                f"  warning: parquet consolidation failed: {type(e).__name__}: {e}\n"
                f"  re-run manually: python3 src/write_phase1a_parquet.py "
                f"--inputs {' '.join(str(p) for p in per_prompt_outputs)}",
                file=sys.stderr,
            )
