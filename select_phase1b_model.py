"""Deterministic implementation of the §12.2 quality-primary model-selection rule.

Locked rule (gss_phase1_design.md §12.2, 2026-05-06):

    primary_score(model) = respondent-macro Likert MAE on Phase-1a primary_eval,
                           full condition only, parse-failed items excluded.
    choose argmin among DQ-passers
        DQ-1: parse_failure_rate_on_1a > 0.30  → disqualify
        DQ-3: mean per-item output-code variance < 0.5  → disqualify (mode-collapse)
    tie-break: among models within 5% of best primary_score, pick lowest
               cost_per_call_USD × (1 + parse_failure_rate)
    fallback:  if candidate set is empty after DQ, OR ≥2 candidates tie on both
               quality (≤5%) AND cost (≤1%) → Qwen-2.5-72B-Instruct.

This script is the canonical executable form of the rule. Running it on the
Phase-1a output JSON produces a single deterministic decision plus an audit
trail, so the §12.2 decision is reproducible and reviewable.

Usage:
    python3 select_phase1b_model.py outputs/gss_phase1_records_n100_<...>.json

    # JSON output for programmatic consumption:
    python3 select_phase1b_model.py outputs/<...>.json --json

The cost table below is the May-2026 OpenRouter snapshot used in the design
doc §12.2 budget table; verify before live runs.
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

# Pre-registered DQ thresholds (locked in OSF §12.2).
DQ1_PARSE_FAIL_MAX: float = 0.30
DQ3_VARIANCE_MIN: float = 0.50
TIE_BREAK_QUALITY_PCT: float = 0.05  # within 5% of best MAE → cost tie-break
FALLBACK_COST_PCT: float = 0.01      # within 1% on cost AND ≤5% quality → fallback

# May-2026 OpenRouter cost snapshot (USD per call). The selection rule is
# robust to the absolute scale; only relative cost matters. Update before
# Phase 1a if provider prices change materially.
DEFAULT_COST_PER_CALL_USD: dict[str, float] = {
    "qwen/qwen-2.5-72b-instruct":  6.0e-5,
    "deepseek/deepseek-chat":      4.5e-5,
    "minimax/minimax-m1":          5.0e-5,
    "moonshotai/kimi-k2":          7.5e-5,
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


def _mean_per_item_variance(model_records: list[dict]) -> float:
    """For each primary_eval item, compute the variance of the model's
    output code across respondents (parse-failed and missing-truth items
    excluded). Average those variances over items.

    A mode-collapsed model that always emits the same code has per-item
    variance of 0, so this average is 0; a calibrated model produces a
    range of codes per item and has variance > 1 on contested items.
    DQ-3 disqualifies models below 0.5.
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
    if not by_item:
        return 0.0
    variances = [
        statistics.pvariance(codes) if len(codes) >= 2 else 0.0
        for codes in by_item.values()
    ]
    return statistics.fmean(variances) if variances else 0.0


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
) -> dict[str, Any]:
    """Apply the §12.2 quality-primary rule to a Phase-1a records list.

    Returns a dict with:
        "selected": chosen model slug
        "rationale": one of "argmin_mae", "tie_break_cost", "fallback_qwen_dq",
                     "fallback_qwen_tie", "fallback_qwen_no_data"
        "per_model": per-model metrics + DQ verdicts
        "candidates_after_dq": ordered list (by MAE) of surviving models
        "decision_log": human-readable list of audit lines
    """
    cost = dict(DEFAULT_COST_PER_CALL_USD)
    if cost_per_call:
        cost.update(cost_per_call)

    by_model = _full_records_by_model(records)
    if not by_model:
        return {
            "selected": QWEN_FALLBACK_SLUG,
            "rationale": "fallback_qwen_no_data",
            "per_model": {},
            "candidates_after_dq": [],
            "decision_log": [
                "No full-condition records found in input — applying Qwen fallback per §12.2."
            ],
        }

    log: list[str] = []
    per_model: dict[str, dict[str, Any]] = {}

    for m, recs in sorted(by_model.items()):
        pf = _parse_failure_rate(recs)
        var_mean = _mean_per_item_variance(recs)
        mae = _respondent_macro_likert_mae(recs)
        cost_m = max(cost.get(m, 0.0), COST_FLOOR_USD)
        cost_score = cost_m * (1.0 + pf)
        dq1_pass = pf <= DQ1_PARSE_FAIL_MAX
        dq3_pass = var_mean >= DQ3_VARIANCE_MIN
        per_model[m] = {
            "n_records_full": len(recs),
            "parse_failure_rate": round(pf, 4),
            "mean_per_item_variance": round(var_mean, 4),
            "respondent_macro_likert_mae": round(mae, 4) if mae is not None else None,
            "cost_per_call_usd": cost_m,
            "cost_score": round(cost_score, 8),
            "dq1_pass": dq1_pass,
            "dq3_pass": dq3_pass,
        }
        log.append(
            f"  [{m}] pf={pf:.3f} var={var_mean:.3f} mae="
            f"{f'{mae:.4f}' if mae is not None else 'NA'} "
            f"cost={cost_m:.2e} dq1={'OK' if dq1_pass else 'FAIL'} "
            f"dq3={'OK' if dq3_pass else 'FAIL'}"
        )

    survivors = [
        m for m, x in per_model.items()
        if x["dq1_pass"] and x["dq3_pass"]
        and x["respondent_macro_likert_mae"] is not None
    ]

    if not survivors:
        log.append("ALL MODELS FAILED DQ-1 or DQ-3 → applying Qwen fallback (§12.2 rule 4).")
        return {
            "selected": QWEN_FALLBACK_SLUG,
            "rationale": "fallback_qwen_dq",
            "per_model": per_model,
            "candidates_after_dq": [],
            "decision_log": log,
        }

    survivors.sort(key=lambda m: per_model[m]["respondent_macro_likert_mae"])
    best_mae = per_model[survivors[0]]["respondent_macro_likert_mae"]
    log.append(f"Best MAE: {best_mae:.4f} ({survivors[0]})")

    # Tie-break window on quality (within 5% of best MAE)
    tie_window_max = best_mae * (1.0 + TIE_BREAK_QUALITY_PCT)
    in_window = [
        m for m in survivors
        if per_model[m]["respondent_macro_likert_mae"] <= tie_window_max
    ]
    if len(in_window) == 1:
        chosen = in_window[0]
        log.append(f"Argmin unique within 5% MAE window → SELECTED: {chosen}")
        return {
            "selected": chosen,
            "rationale": "argmin_mae",
            "per_model": per_model,
            "candidates_after_dq": survivors,
            "decision_log": log,
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
        log.append(f"Cost tie-break selected: {chosen}")
        return {
            "selected": chosen,
            "rationale": "tie_break_cost",
            "per_model": per_model,
            "candidates_after_dq": survivors,
            "decision_log": log,
        }

    log.append(
        f"≥2 models tie on quality (≤5%) AND cost (≤1%) → applying Qwen fallback (§12.2 rule 4)."
    )
    return {
        "selected": QWEN_FALLBACK_SLUG,
        "rationale": "fallback_qwen_tie",
        "per_model": per_model,
        "candidates_after_dq": survivors,
        "decision_log": log,
    }


# ---------------------------------------------------------------------------
# CLI + self-test
# ---------------------------------------------------------------------------

def _cli():
    p = argparse.ArgumentParser(
        description="Apply the §12.2 quality-primary model-selection rule to "
                    "Phase-1a records. Deterministic; OSF-locked."
    )
    p.add_argument("records_path", type=Path, nargs="?",
                   help="Phase-1a records JSON (gss_phase1_records_n100_*.json)")
    p.add_argument("--json", action="store_true",
                   help="emit the decision dict as JSON (default: human-readable)")
    p.add_argument("--self-test", action="store_true",
                   help="run hand-crafted assertions against synthetic 1a records")
    return p.parse_args()


def _self_test() -> None:
    """Hand-crafted records exercising each branch of the rule."""

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
        r1.append(_make_record(rid, "minimax/minimax-m1",
                               {k: [(min(t + 1, 7), t)] for k, t in truths.items()}))
        # Kimi: shift by +3 → MAE ~3
        r1.append(_make_record(rid, "moonshotai/kimi-k2",
                               {k: [(min(t + 3, 7), t)] for k, t in truths.items()}))
    out1 = select_phase1b_model(r1)
    assert out1["selected"] == "qwen/qwen-2.5-72b-instruct", out1["selected"]
    assert out1["rationale"] == "argmin_mae", out1["rationale"]
    print(f"    ✓ SELECTED={out1['selected']} rationale={out1['rationale']}")

    # Test 2: fallback_qwen_dq — every model fails DQ-3 (mode collapse)
    print("\n[2] fallback_qwen_dq — every model collapses to a single code")
    r2 = []
    for rid in range(20):
        for m in ["qwen/qwen-2.5-72b-instruct", "deepseek/deepseek-chat",
                  "minimax/minimax-m1", "moonshotai/kimi-k2"]:
            # Every output is "4" → variance 0, fails DQ-3
            r2.append(_make_record(rid, m, {"P1": [(4, 4)], "P2": [(4, 3)],
                                            "P3": [(4, 5)]}))
    out2 = select_phase1b_model(r2)
    assert out2["selected"] == QWEN_FALLBACK_SLUG, out2["selected"]
    assert out2["rationale"] == "fallback_qwen_dq", out2["rationale"]
    print(f"    ✓ SELECTED={out2['selected']} rationale={out2['rationale']}")

    # Test 3: fallback_qwen_dq — every model parse-fails > 30%
    print("\n[3] fallback_qwen_dq — all models exceed parse-failure ceiling")
    r3 = []
    for rid in range(10):
        for m in ["qwen/qwen-2.5-72b-instruct", "deepseek/deepseek-chat",
                  "minimax/minimax-m1", "moonshotai/kimi-k2"]:
            r3.append(_make_record(rid, m, {
                "P1": [(None, 4)],   # parse fail
                "P2": [(None, 3)],   # parse fail
                "P3": [(5, 5)],      # OK
            }))  # 2/3 = 66.7% parse fail
    out3 = select_phase1b_model(r3)
    assert out3["selected"] == QWEN_FALLBACK_SLUG, out3["selected"]
    assert out3["rationale"] == "fallback_qwen_dq", out3["rationale"]
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
    out4 = select_phase1b_model(r4)
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

    print("\n✓ ALL §12.2 SELECTOR SELF-TESTS PASSED\n")


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
    decision = select_phase1b_model(records)
    if args.json:
        print(json.dumps(decision, indent=2))
    else:
        print(f"=== §12.2 Phase 1b model selection ===")
        print(f"Records: {args.records_path}")
        print(f"\nDecision log:")
        for line in decision["decision_log"]:
            print(line)
        print(f"\nSELECTED: {decision['selected']}")
        print(f"RATIONALE: {decision['rationale']}")
