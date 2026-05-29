"""Deterministic implementation of the §7 quality-primary cell-selection rule.

Locked rule (RESEARCH_DESIGN.md §7; canonical single-source 2026-05-28
post-Bayati signoff. Earlier framing in gss_phase1_design.md §12.2 is
archived):

    primary_score(model) = respondent-macro Likert MAE on Phase-1a primary_eval,
                           full condition only, parse-failed items excluded.
    choose argmin among DQ-passers
        DQ-1: parse_failure_rate_on_1a > 0.30  → disqualify
        DQ-3: per-item output variance < 30% of human variance on that item
              for any primary_eval item where the model is asked, computed as
              the fraction of items failing the threshold; disqualify if
              ≥ 50% of items fail (i.e., a majority of items show mode collapse
              relative to the human distribution).
    tie-break: among models within 5% of best primary_score, pick lowest
               cost_per_call_USD × (1 + parse_failure_rate)
    fallback:  if candidate set is empty after DQ, OR ≥2 candidates tie on both
               quality (≤5%) AND cost (≤1%) → Qwen-2.5-72B-Instruct.

DQ-3 history:
- 2026-05-06: introduced as ABSOLUTE threshold (mean per-item variance < 0.5).
- 2026-05-08: revised to PER-ITEM RELATIVE threshold (var(model_i) / var(human_i)
  < 0.30 per item) after Codex audit §3.9 noted that an absolute threshold is
  too lenient on heavily-skewed items (e.g., FAIR/HELPFUL/TRUST/FEPOL where
  human variance itself is < 0.5) and too strict on widely-spread items (e.g.,
  PARTYID where human variance is 4.24). The relative threshold scales with
  the empirical human distribution per item.

This script is the canonical executable form of the rule. Running it on the
Phase-1a output produces a single deterministic decision plus an audit trail,
so the §7 decision is reproducible and reviewable.

NOTE (2026-05-28): this module implements the OSF-v1 single-model selector
and is preserved as the legacy reference for the pre-factorial design. The
Bayati-confirmed joint (model, prompt) cell selector — 12 panel cells +
post-hoc random-model column (per RESEARCH_DESIGN.md §5.2 + §7) — lives at
`src/select_phase1b_cell.py`. New runs should use that module; this file
should not be invoked for the factorial pipeline.

Usage:
    python3 src/select_phase1b_model.py outputs/phase1a_raw.parquet

    # JSON output for programmatic consumption:
    python3 src/select_phase1b_model.py outputs/<...> --json

The cost table below is the May-2026 OpenRouter snapshot used in the
RESEARCH_DESIGN.md §11 budget table; verify before live runs.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

# Locked panel + canonical fallback (matches llm_router.MODEL_PANEL_PRIMARY).
QWEN_FALLBACK_SLUG: str = "qwen/qwen-2.5-72b-instruct"

# Pre-registered DQ thresholds (locked in OSF §12.2; revised 2026-05-08).
DQ1_PARSE_FAIL_MAX: float = 0.30
DQ3_RELATIVE_VARIANCE_FLOOR: float = 0.30  # model_var(i) / human_var(i) ≥ 30%
DQ3_PER_ITEM_FAIL_MAX: float = 0.50         # disqualify if >50% of items fail floor
TIE_BREAK_QUALITY_PCT: float = 0.05  # within 5% of best MAE → cost tie-break
FALLBACK_COST_PCT: float = 0.01      # within 1% on cost AND ≤5% quality → fallback

# Path to the precomputed per-item human variance reference. The reference is
# computed once from GSS 2024 substantive responses (excluding MISSING_CODES
# and non-substantive labels) for each primary_eval item. Pre-registered.
HUMAN_VARIANCE_PATH = Path("/Users/joyce/Developer/gsbgen390") / "outputs" / "primary_eval_human_variance_2024.json"

# May-2026 OpenRouter cost snapshot (USD per call). The selection rule is
# robust to the absolute scale; only relative cost matters. Update before
# Phase 1a if provider prices change materially.
DEFAULT_COST_PER_CALL_USD: dict[str, float] = {
    "qwen/qwen-2.5-72b-instruct":      6.0e-5,
    "deepseek/deepseek-chat":          4.5e-5,
    # MiniMax-M1 swapped to Llama-3.3 pre-OSF (Audit-3 cross-family balance review).
    "meta-llama/llama-3.3-70b-instruct": 5.5e-5,
    "moonshotai/kimi-k2":              7.5e-5,
}
COST_FLOOR_USD: float = 5.0e-5


# ---------------------------------------------------------------------------
# Per-model 1a metrics
# ---------------------------------------------------------------------------

def _full_records_by_model(records: list[dict]) -> dict[str, list[dict]]:
    """Group full-condition records by model. Sensitivity + LOO conditions
    are not used by the §12.2 selection rule (the rule scores models on the
    paper's headline metric, which is computed under the full condition
    only)."""
    out: dict[str, list[dict]] = {}
    for r in records:
        if r.get("condition") != "full":
            continue
        out.setdefault(r["model"], []).append(r)
    return out


def _parse_failure_rate(model_records: list[dict]) -> float:
    """Fraction of (respondent, item, sample) tuples where the model's
    output failed to parse to a valid code, over the full condition only."""
    total = 0
    fails = 0
    for r in model_records:
        for samples in (r.get("per_item_scores") or {}).values():
            for s in samples:
                total += 1
                if s.get("parse_fail"):
                    fails += 1
    return fails / total if total else 1.0


def _per_item_variance(model_records: list[dict]) -> dict[str, float]:
    """Per-item population variance of the model's output codes across
    respondents. Parse-failed and missing-truth samples excluded.
    """
    by_item: dict[str, list[int]] = {}
    for r in model_records:
        for item_id, samples in (r.get("per_item_scores") or {}).items():
            for s in samples:
                if s.get("parse_fail"):
                    continue
                code = s.get("persona_code")
                if code is None:
                    continue
                by_item.setdefault(item_id, []).append(int(code))
    return {
        item_id: (statistics.pvariance(codes) if len(codes) >= 2 else 0.0)
        for item_id, codes in by_item.items()
    }


def _load_human_variance_reference() -> dict[str, float]:
    """Load the locked GSS 2024 per-item human variance reference (DQ-3)."""
    if not HUMAN_VARIANCE_PATH.exists():
        return {}
    raw = json.loads(HUMAN_VARIANCE_PATH.read_text())
    return {vid: x["human_variance"] for vid, x in raw["items"].items()}


def _dq3_relative_check(
    model_records: list[dict],
    human_variance_by_item: dict[str, float],
    floor: float = DQ3_RELATIVE_VARIANCE_FLOOR,
) -> dict[str, Any]:
    """Apply per-item relative-variance DQ-3.

    For each primary_eval item, compute model_var/human_var. Item fails the
    floor if the ratio < `floor`. Model fails DQ-3 if more than DQ3_PER_ITEM_FAIL_MAX
    of the items fail the floor.
    """
    model_var = _per_item_variance(model_records)
    if not model_var:
        return {
            "fail_pct": 1.0, "n_items": 0, "n_items_failing": 0,
            "per_item": {}, "passes": False,
        }
    per_item: dict[str, dict[str, Any]] = {}
    n_fail = 0
    n_total = 0
    for item_id, mv in model_var.items():
        hv = human_variance_by_item.get(item_id)
        if hv is None or hv <= 0:
            # Without a human-variance reference for this item, abstain
            # (count it as 'unknown'); do not penalize the model.
            per_item[item_id] = {
                "model_var": round(mv, 4), "human_var": None,
                "ratio": None, "fails_floor": None,
            }
            continue
        ratio = mv / hv
        fails = ratio < floor
        per_item[item_id] = {
            "model_var": round(mv, 4),
            "human_var": round(hv, 4),
            "ratio": round(ratio, 4),
            "fails_floor": fails,
        }
        n_total += 1
        if fails:
            n_fail += 1
    fail_pct = (n_fail / n_total) if n_total else 0.0
    return {
        "fail_pct": round(fail_pct, 4),
        "n_items": n_total,
        "n_items_failing": n_fail,
        "per_item": per_item,
        "passes": fail_pct <= DQ3_PER_ITEM_FAIL_MAX,
    }


def _respondent_macro_likert_mae(model_records: list[dict]) -> float | None:
    """For each respondent, mean Likert |error| across that respondent's
    answered Likert primary_eval items (parse-failed and missing-truth
    excluded). Then mean across respondents. Returns None if no respondent
    contributed any Likert observation (degenerate run).
    """
    per_respondent_means: list[float] = []
    for r in model_records:
        errs: list[float] = []
        for samples in (r.get("per_item_scores") or {}).values():
            for s in samples:
                if s.get("parse_fail"):
                    continue
                if s.get("treatment") != "likert":
                    continue
                ae = s.get("abs_err")
                if ae is None:
                    continue
                errs.append(float(ae))
        if errs:
            per_respondent_means.append(statistics.fmean(errs))
    if not per_respondent_means:
        return None
    return statistics.fmean(per_respondent_means)


# ---------------------------------------------------------------------------
# Selection rule
# ---------------------------------------------------------------------------

def select_phase1b_model(
    records: list[dict],
    cost_per_call: dict[str, float] | None = None,
    human_variance_by_item: dict[str, float] | None = None,
    selection_respondent_ids: set[int] | None = None,
    validation_respondent_ids: set[int] | None = None,
) -> dict[str, Any]:
    """Apply the §12.2 quality-primary rule to a Phase-1a records list.

    100/100 SPLIT (locked 2026-05-09 night per Audit-3 + Joyce decision):
      - `selection_respondent_ids`: respondents the SELECTOR scores on (locked
        first half of the seed-42 N=200 sample). All DQ + MAE + tie-break logic
        operates on records filtered to these respondents.
      - `validation_respondent_ids`: held-out respondents the selector NEVER
        scores on. After selection, the chosen model's MAE on the validation
        split is also computed and reported as `validation_mae`. This rebuts
        post-selection-inference attacks ("of course your selected model wins
        on the same items").
      - If both are None (legacy / single-split tests), the selector scores
        on ALL respondents and `validation_mae` is None.

    Returns a dict with:
        "selected": chosen model slug, OR None when all models fail DQ
                    (locked 2026-05-09 night per Audit-2 + Joyce decision —
                    Qwen-fallback under all-DQ-fail removed; selector now
                    PAUSES for human review instead of silently bypassing
                    the quality gate).
        "rationale": one of "argmin_mae", "tie_break_cost",
                     "all_dq_fail_pause_for_review", "fallback_qwen_tie",
                     "fallback_qwen_no_data"
        "per_model": per-model metrics + DQ verdicts (selection-set only)
        "validation_mae": MAE of the selected model on the held-out validation
                          split (None when no split was supplied or selection
                          paused for review)
        "candidates_after_dq": ordered list (by MAE) of surviving models
        "decision_log": human-readable list of audit lines
        "split_info": dict with selection_n / validation_n / mode
    """
    cost = dict(DEFAULT_COST_PER_CALL_USD)
    if cost_per_call:
        cost.update(cost_per_call)

    # 100/100 split: filter records to the selection split for selector scoring.
    if selection_respondent_ids is not None:
        selection_records = [
            r for r in records
            if r.get("respondent_id") in selection_respondent_ids
        ]
        validation_records = [
            r for r in records
            if validation_respondent_ids is not None
            and r.get("respondent_id") in validation_respondent_ids
        ]
        split_info = {
            "mode": "100_100_split",
            "selection_n": len({r.get("respondent_id") for r in selection_records}),
            "validation_n": len({r.get("respondent_id") for r in validation_records}),
        }
    else:
        selection_records = records
        validation_records = []
        split_info = {
            "mode": "single_split",
            "selection_n": len({r.get("respondent_id") for r in records}),
            "validation_n": 0,
        }
    # Selector scoring uses only the selection split below.
    records = selection_records
    hvar = human_variance_by_item or _load_human_variance_reference()

    by_model = _full_records_by_model(records)
    if not by_model:
        return {
            "selected": QWEN_FALLBACK_SLUG,
            "rationale": "fallback_qwen_no_data",
            "per_model": {},
            "validation_mae": None,
            "candidates_after_dq": [],
            "decision_log": [
                "No full-condition records found in input — applying Qwen fallback per §12.2."
            ],
            "split_info": split_info,
        }

    log: list[str] = []
    per_model: dict[str, dict[str, Any]] = {}

    for m, recs in sorted(by_model.items()):
        pf = _parse_failure_rate(recs)
        dq3 = _dq3_relative_check(recs, hvar)
        mae = _respondent_macro_likert_mae(recs)
        cost_m = max(cost.get(m, 0.0), COST_FLOOR_USD)
        cost_score = cost_m * (1.0 + pf)
        dq1_pass = pf <= DQ1_PARSE_FAIL_MAX
        per_model[m] = {
            "n_records_full": len(recs),
            "parse_failure_rate": round(pf, 4),
            "dq3_per_item_fail_pct": dq3["fail_pct"],
            "dq3_n_items_failing": dq3["n_items_failing"],
            "dq3_per_item": dq3["per_item"],
            "respondent_macro_likert_mae": round(mae, 4) if mae is not None else None,
            "cost_per_call_usd": cost_m,
            "cost_score": round(cost_score, 8),
            "dq1_pass": dq1_pass,
            "dq3_pass": dq3["passes"],
        }
        log.append(
            f"  [{m}] pf={pf:.3f} "
            f"dq3_fail_pct={dq3['fail_pct']:.2f} ({dq3['n_items_failing']}/{dq3['n_items']}) "
            f"mae={f'{mae:.4f}' if mae is not None else 'NA'} "
            f"cost={cost_m:.2e} dq1={'OK' if dq1_pass else 'FAIL'} "
            f"dq3={'OK' if dq3['passes'] else 'FAIL'}"
        )

    survivors = [
        m for m, x in per_model.items()
        if x["dq1_pass"] and x["dq3_pass"]
        and x.get("respondent_macro_likert_mae") is not None
    ]

    if not survivors:
        log.append(
            "ALL MODELS FAILED DQ-1 or DQ-3 → PAUSE for human review. "
            "(Locked 2026-05-09 night per Audit-2: Qwen-fallback under all-DQ-fail "
            "removed because all-DQ-fail is a SIGNAL — prompt template, parser, or "
            "model panel is broken — and continuing to Phase 1b on a failed model "
            "wastes ~$95-209 of paid runs. Resume requires diagnosing the failure "
            "and either rerunning Phase 1a, swapping the panel, or filing an OSF "
            "amendment.)"
        )
        return {
            "selected": None,
            "rationale": "all_dq_fail_pause_for_review",
            "per_model": per_model,
            "validation_mae": None,
            "candidates_after_dq": [],
            "decision_log": log,
            "split_info": split_info,
        }

    survivors.sort(key=lambda m: per_model[m]["respondent_macro_likert_mae"])
    best_mae = per_model[survivors[0]]["respondent_macro_likert_mae"]
    log.append(f"Best MAE: {best_mae:.4f} ({survivors[0]})")

    # Helper: compute validation MAE for the chosen model on the held-out split
    # (Audit-3 anti-overfit defense). Returns None if no validation set.
    def _validation_mae_for(model_slug: str) -> float | None:
        if not validation_records:
            return None
        v_by_model = _full_records_by_model(validation_records)
        v_recs = v_by_model.get(model_slug, [])
        if not v_recs:
            return None
        v_mae = _respondent_macro_likert_mae(v_recs)
        return round(v_mae, 4) if v_mae is not None else None

    # Tie-break window on quality (within 5% of best MAE)
    tie_window_max = best_mae * (1.0 + TIE_BREAK_QUALITY_PCT)
    in_window = [
        m for m in survivors
        if per_model[m]["respondent_macro_likert_mae"] <= tie_window_max
    ]
    if len(in_window) == 1:
        chosen = in_window[0]
        v_mae = _validation_mae_for(chosen)
        log.append(f"Argmin unique within 5% MAE window → SELECTED: {chosen}")
        if v_mae is not None:
            log.append(f"  validation_mae (held-out N={split_info['validation_n']}): {v_mae:.4f}")
        return {
            "selected": chosen,
            "rationale": "argmin_mae",
            "per_model": per_model,
            "validation_mae": v_mae,
            "candidates_after_dq": survivors,
            "decision_log": log,
            "split_info": split_info,
        }

    # Cost tie-break among the within-5% survivors
    in_window.sort(key=lambda m: per_model[m]["cost_score"])
    best_cost = per_model[in_window[0]]["cost_score"]
    cost_tied = [
        m for m in in_window
        if per_model[m]["cost_score"] <= best_cost * (1.0 + FALLBACK_COST_PCT)
    ]
    log.append(
        f"Quality tie among {len(in_window)} models within 5% MAE → "
        f"cost tie-break: best cost_score={best_cost:.3e}, "
        f"models within 1% of best cost: {cost_tied}"
    )
    if len(cost_tied) == 1:
        chosen = cost_tied[0]
        v_mae = _validation_mae_for(chosen)
        log.append(f"Cost tie-break selected: {chosen}")
        if v_mae is not None:
            log.append(f"  validation_mae (held-out N={split_info['validation_n']}): {v_mae:.4f}")
        return {
            "selected": chosen,
            "rationale": "tie_break_cost",
            "per_model": per_model,
            "validation_mae": v_mae,
            "candidates_after_dq": survivors,
            "decision_log": log,
            "split_info": split_info,
        }

    log.append(
        f"≥2 models tie on quality (≤5%) AND cost (≤1%) → applying Qwen fallback (§12.2 rule 4)."
    )
    v_mae = _validation_mae_for(QWEN_FALLBACK_SLUG)
    if v_mae is not None:
        log.append(f"  validation_mae (held-out N={split_info['validation_n']}): {v_mae:.4f}")
    return {
        "selected": QWEN_FALLBACK_SLUG,
        "rationale": "fallback_qwen_tie",
        "per_model": per_model,
        "validation_mae": v_mae,
        "candidates_after_dq": survivors,
        "decision_log": log,
        "split_info": split_info,
    }


# ---------------------------------------------------------------------------
# CLI + self-test
# ---------------------------------------------------------------------------

def _cli():
    p = argparse.ArgumentParser(
        description="Apply the §12.2 quality-primary model-selection rule to "
                    "Phase-1a records. Deterministic; OSF-locked. The CLI "
                    "ENFORCES the locked 100/100 selection/validation split "
                    "by default (per Audit-3 + Audit-fresh review). Pass "
                    "--no-split only for legacy / single-set debugging."
    )
    p.add_argument("records_path", type=Path, nargs="?",
                   help="Phase-1a records JSON (gss_phase1_records_n200_*.json)")
    p.add_argument("--json", action="store_true",
                   help="emit the decision dict as JSON (default: human-readable)")
    p.add_argument("--self-test", action="store_true",
                   help="run hand-crafted assertions against synthetic 1a records")
    p.add_argument("--phase1a-n", type=int, default=200,
                   help="locked Phase 1a sample size (default 200)")
    p.add_argument("--selection-n", type=int, default=100,
                   help="size of the selection split (default 100; remainder is validation)")
    p.add_argument("--seed", type=int, default=42,
                   help="locked GSS sampling seed (default 42)")
    p.add_argument("--no-split", action="store_true",
                   help="DISABLE the 100/100 split (legacy / debug mode); "
                        "the selector then scores on all respondents in the "
                        "input. WARNING: this is NOT the OSF-locked design "
                        "and prints an explicit stderr warning.")
    return p.parse_args()


def _derive_phase1a_split(
    phase1a_n: int,
    selection_n: int,
    seed: int,
) -> tuple[set[int], set[int]]:
    """Re-derive the locked Phase 1a 100/100 split from the canonical seed-42
    sample order. Returns (selection_ids, validation_ids) as sets of int rids.

    Locked 2026-05-09 night per Audit-fresh review (P1.1): the CLI must
    enforce the 100/100 split — without this helper, the selector silently
    scored on the full N=200 sample, defeating the anti-overfit defense.
    """
    # Late import to avoid coupling the selector module to pandas at import time.
    from gss_pipeline import sample_respondents
    df = sample_respondents(phase1a_n, seed=seed)
    rids = [int(r) for r in df["ID_"].tolist()]
    if len(rids) < phase1a_n:
        raise RuntimeError(
            f"Expected N={phase1a_n} respondents from sample_respondents, got {len(rids)}"
        )
    sel = set(rids[:selection_n])
    val = set(rids[selection_n:phase1a_n])
    if len(sel) != selection_n or len(val) != phase1a_n - selection_n:
        raise RuntimeError(
            f"Split derivation failed: selection={len(sel)}, validation={len(val)}"
        )
    return sel, val


def _self_test() -> None:
    """Hand-crafted records exercising each branch of the rule.

    Synthetic human-variance reference for the self-test items P1/P2/P3:
    we use {P1: 4.0, P2: 3.0, P3: 2.0} so the relative-variance DQ-3
    has meaningful behavior. Real GSS items use the locked reference at
    outputs/primary_eval_human_variance_2024.json.
    """
    SYNTHETIC_HUMAN_VAR = {"P1": 4.0, "P2": 3.0, "P3": 2.0}

    def _make_record(
        rid: int, model: str, item_codes: dict[str, list[tuple[int | None, int]]],
        condition: str = "full",
    ) -> dict:
        # item_codes: {item_id: [(persona_code, truth_code), ...]} per sample
        per_item: dict[str, list[dict]] = {}
        for vid, samples in item_codes.items():
            sample_dicts = []
            for persona_code, truth in samples:
                if persona_code is None:
                    sample_dicts.append({
                        "truth": truth, "persona_code": None,
                        "parse_fail": True, "treatment": None,
                        "abs_err": None, "skipped_missing_truth": False,
                    })
                else:
                    sample_dicts.append({
                        "truth": truth, "persona_code": persona_code,
                        "parse_fail": False, "treatment": "likert",
                        "abs_err": abs(persona_code - truth),
                        "skipped_missing_truth": False,
                    })
            per_item[vid] = sample_dicts
        return {
            "respondent_id": rid, "condition": condition, "model": model,
            "n_samples": 1, "per_item_scores": per_item,
        }

    print("=== §12.2 selector self-test ===\n")

    # Test 1: argmin_mae — Qwen has clearly best MAE among DQ-passers.
    # Each respondent's truth varies across the rid range so per-item variance
    # is non-zero (passes DQ-3). Qwen always nails truth (MAE=0); the others
    # have a uniform offset (MAE>0).
    print("[1] argmin_mae — clean win on quality")
    r1 = []
    for rid in range(20):
        truths = {"P1": (rid % 5) + 1, "P2": (rid % 4) + 1, "P3": (rid % 7) + 1}
        r1.append(_make_record(rid, "qwen/qwen-2.5-72b-instruct",
                               {k: [(t, t)] for k, t in truths.items()}))
        # DeepSeek: shift by +2 (clipped to 1-7) → MAE ~2
        r1.append(_make_record(rid, "deepseek/deepseek-chat",
                               {k: [(min(t + 2, 7), t)] for k, t in truths.items()}))
        # MiniMax: shift by +1 → MAE ~1
        r1.append(_make_record(rid, "meta-llama/llama-3.3-70b-instruct",
                               {k: [(min(t + 1, 7), t)] for k, t in truths.items()}))
        # Kimi: shift by +3 → MAE ~3
        r1.append(_make_record(rid, "moonshotai/kimi-k2",
                               {k: [(min(t + 3, 7), t)] for k, t in truths.items()}))
    out1 = select_phase1b_model(r1, human_variance_by_item=SYNTHETIC_HUMAN_VAR)
    assert out1["selected"] == "qwen/qwen-2.5-72b-instruct", out1["selected"]
    assert out1["rationale"] == "argmin_mae", out1["rationale"]
    print(f"    ✓ SELECTED={out1['selected']} rationale={out1['rationale']}")

    # Test 2: all_dq_fail_pause — every model fails DQ-3 (mode collapse).
    # Locked 2026-05-09 night per Audit-2 + Joyce decision: PAUSE instead of
    # silently falling back to Qwen.
    print("\n[2] all_dq_fail_pause_for_review — every model collapses to a single code")
    r2 = []
    for rid in range(20):
        for m in ["qwen/qwen-2.5-72b-instruct", "deepseek/deepseek-chat",
                  "meta-llama/llama-3.3-70b-instruct", "moonshotai/kimi-k2"]:
            # Every output is "4" → variance 0, fails DQ-3
            r2.append(_make_record(rid, m, {"P1": [(4, 4)], "P2": [(4, 3)],
                                            "P3": [(4, 5)]}))
    out2 = select_phase1b_model(r2, human_variance_by_item=SYNTHETIC_HUMAN_VAR)
    assert out2["selected"] is None, out2["selected"]
    assert out2["rationale"] == "all_dq_fail_pause_for_review", out2["rationale"]
    print(f"    ✓ SELECTED={out2['selected']} rationale={out2['rationale']}")

    # Test 3: all_dq_fail_pause — every model parse-fails > 30%
    print("\n[3] all_dq_fail_pause_for_review — all models exceed parse-failure ceiling")
    r3 = []
    for rid in range(10):
        for m in ["qwen/qwen-2.5-72b-instruct", "deepseek/deepseek-chat",
                  "meta-llama/llama-3.3-70b-instruct", "moonshotai/kimi-k2"]:
            r3.append(_make_record(rid, m, {
                "P1": [(None, 4)],   # parse fail
                "P2": [(None, 3)],   # parse fail
                "P3": [(5, 5)],      # OK
            }))  # 2/3 = 66.7% parse fail
    out3 = select_phase1b_model(r3, human_variance_by_item=SYNTHETIC_HUMAN_VAR)
    assert out3["selected"] is None, out3["selected"]
    assert out3["rationale"] == "all_dq_fail_pause_for_review", out3["rationale"]
    print(f"    ✓ SELECTED={out3['selected']} rationale={out3['rationale']}")

    # Test 4: tie_break_cost — Qwen and DeepSeek tie on quality; DeepSeek cheaper.
    # Per-respondent truth varies so per-item variance > 0 (DQ-3 passes); both
    # models nail truth identically → MAE 0 for both → cost tie-break decides.
    print("\n[4] tie_break_cost — quality tied within 5%, cheaper model wins")
    r4 = []
    for rid in range(20):
        truths = {"P1": (rid % 7) + 1, "P2": (rid % 5) + 1, "P3": (rid % 4) + 1}
        for m in ["qwen/qwen-2.5-72b-instruct", "deepseek/deepseek-chat"]:
            r4.append(_make_record(rid, m, {k: [(t, t)] for k, t in truths.items()}))
    out4 = select_phase1b_model(r4, human_variance_by_item=SYNTHETIC_HUMAN_VAR)
    # Note: DeepSeek has lower default cost (4.5e-5 < 6.0e-5 Qwen)
    assert out4["selected"] == "deepseek/deepseek-chat", out4["selected"]
    assert out4["rationale"] == "tie_break_cost", out4["rationale"]
    print(f"    ✓ SELECTED={out4['selected']} rationale={out4['rationale']}")

    # Test 5: fallback_qwen_no_data — empty records
    print("\n[5] fallback_qwen_no_data — no full-condition records")
    out5 = select_phase1b_model([])
    assert out5["selected"] == QWEN_FALLBACK_SLUG, out5["selected"]
    assert out5["rationale"] == "fallback_qwen_no_data", out5["rationale"]
    print(f"    ✓ SELECTED={out5['selected']} rationale={out5['rationale']}")

    # Test 6 (NEW 2026-05-09 night per Codex N7): fallback_qwen_tie — multiple
    # candidates tie on quality (within 5% MAE) AND cost (within 1%); rule must
    # fall through to Qwen named fallback rather than tie-break alphabetically.
    # Construct: 3 models all with identical near-zero MAE and identical cost.
    # The DEFAULT_COST_PER_CALL_USD has Qwen + DeepSeek + MiniMax distinct
    # base costs; we override the cost map to make 3 models identically priced.
    print("\n[6] fallback_qwen_tie — quality tied AND cost tied; named Qwen fallback fires")
    r6 = []
    for rid in range(20):
        truths = {"P1": (rid % 7) + 1, "P2": (rid % 5) + 1, "P3": (rid % 4) + 1}
        # 3 models nail truth identically (MAE = 0 for all) → quality tie
        for m in ("qwen/qwen-2.5-72b-instruct",
                  "deepseek/deepseek-chat",
                  "meta-llama/llama-3.3-70b-instruct"):
            r6.append(_make_record(rid, m, {k: [(t, t)] for k, t in truths.items()}))
    # Cost override: identical cost for the 3 candidates → cost tie within 1%
    cost_override = {
        "qwen/qwen-2.5-72b-instruct": 6.0e-5,
        "deepseek/deepseek-chat":     6.0e-5,
        "meta-llama/llama-3.3-70b-instruct":         6.0e-5,
    }
    out6 = select_phase1b_model(
        r6,
        cost_per_call=cost_override,
        human_variance_by_item=SYNTHETIC_HUMAN_VAR,
    )
    assert out6["selected"] == QWEN_FALLBACK_SLUG, out6["selected"]
    assert out6["rationale"] == "fallback_qwen_tie", out6["rationale"]
    print(f"    ✓ SELECTED={out6['selected']} rationale={out6['rationale']}")

    # Test 7 (NEW 2026-05-09 night per Audit-3 + Joyce decision): 100/100
    # split — selector scores ONLY on selection rids (0..99); validation rids
    # (100..199) yield a separate validation_mae for the chosen model.
    print("\n[7] 100/100 split — validation MAE on held-out split is computed")
    r7 = []
    for rid in range(200):  # N=200: 0..99 selection, 100..199 validation
        truths = {"P1": (rid % 7) + 1, "P2": (rid % 5) + 1, "P3": (rid % 4) + 1}
        # Qwen: hits truth exactly on selection (low MAE) but offset by 1 on validation
        for k, t in truths.items():
            in_selection = rid < 100
            qwen_persona = t if in_selection else min(t + 1, 7)
            r7.append(_make_record(rid, "qwen/qwen-2.5-72b-instruct",
                                    {k: [(qwen_persona, t)]}))
        # Other models: shifted by +2 throughout → higher MAE everywhere
        for m in ("deepseek/deepseek-chat",
                  "meta-llama/llama-3.3-70b-instruct",
                  "moonshotai/kimi-k2"):
            for k, t in truths.items():
                r7.append(_make_record(rid, m, {k: [(min(t + 2, 7), t)]}))
    sel_ids = set(range(0, 100))
    val_ids = set(range(100, 200))
    out7 = select_phase1b_model(
        r7,
        human_variance_by_item=SYNTHETIC_HUMAN_VAR,
        selection_respondent_ids=sel_ids,
        validation_respondent_ids=val_ids,
    )
    assert out7["selected"] == "qwen/qwen-2.5-72b-instruct", out7["selected"]
    assert out7["rationale"] == "argmin_mae", out7["rationale"]
    assert out7["split_info"]["mode"] == "100_100_split", out7["split_info"]
    assert out7["split_info"]["selection_n"] == 100, out7["split_info"]
    assert out7["split_info"]["validation_n"] == 100, out7["split_info"]
    assert out7["validation_mae"] is not None, out7["validation_mae"]
    # Selection-set MAE ≈ 0 (Qwen hits truth); validation-set MAE ≈ 1 (offset by 1)
    sel_mae = out7["per_model"]["qwen/qwen-2.5-72b-instruct"]["respondent_macro_likert_mae"]
    val_mae = out7["validation_mae"]
    assert sel_mae < 0.1, f"selection MAE expected near 0, got {sel_mae}"
    assert 0.5 < val_mae < 1.5, f"validation MAE expected ≈1, got {val_mae}"
    print(f"    ✓ SELECTED={out7['selected']} rationale={out7['rationale']}")
    print(f"      selection_mae (N=100): {sel_mae:.4f}")
    print(f"      validation_mae (N=100, held out): {val_mae:.4f}")
    print(f"      gap = {val_mae - sel_mae:.4f}  (post-selection-inference signature)")

    print("\n✓ ALL §12.2 SELECTOR SELF-TESTS PASSED (7 tests across 5 rationales:")
    print("    argmin_mae (×2: vanilla + 100/100 split), tie_break_cost,")
    print("    all_dq_fail_pause_for_review (×2: DQ-1 + DQ-3),")
    print("    fallback_qwen_no_data, fallback_qwen_tie)\n")


if __name__ == "__main__":
    args = _cli()
    if args.self_test:
        _self_test()
        sys.exit(0)
    if args.records_path is None:
        print("error: records_path is required (or pass --self-test)", file=sys.stderr)
        sys.exit(2)
    if not args.records_path.exists():
        print(f"error: {args.records_path} not found", file=sys.stderr)
        sys.exit(2)
    records = json.loads(args.records_path.read_text())

    if args.no_split:
        print(
            "WARNING: --no-split disables the OSF-locked 100/100 selection/"
            "validation split. The selector will score on ALL respondents in "
            "the input, which is NOT the pre-registered design and exposes "
            "the headline to post-selection-inference attack. Use only for "
            "legacy debugging.",
            file=sys.stderr,
        )
        sel_ids, val_ids = None, None
    else:
        sel_ids, val_ids = _derive_phase1a_split(
            phase1a_n=args.phase1a_n,
            selection_n=args.selection_n,
            seed=args.seed,
        )
        print(
            f"  Enforcing locked split: selection_n={len(sel_ids)} / "
            f"validation_n={len(val_ids)} (phase1a_n={args.phase1a_n}, seed={args.seed})",
            file=sys.stderr,
        )

    decision = select_phase1b_model(
        records,
        selection_respondent_ids=sel_ids,
        validation_respondent_ids=val_ids,
    )

    if args.json:
        print(json.dumps(decision, indent=2))
    else:
        print(f"=== §12.2 Phase 1b model selection ===")
        print(f"Records: {args.records_path}")
        si = decision.get("split_info", {})
        if si:
            print(f"Split mode: {si.get('mode')} "
                  f"(selection_n={si.get('selection_n')}, "
                  f"validation_n={si.get('validation_n')})")
        print(f"\nDecision log:")
        for line in decision["decision_log"]:
            print(line)
        print(f"\nSELECTED: {decision['selected']}")
        print(f"RATIONALE: {decision['rationale']}")
        if decision.get("validation_mae") is not None:
            print(f"VALIDATION_MAE (held-out N={si.get('validation_n', '?')}): "
                  f"{decision['validation_mae']:.4f}")
