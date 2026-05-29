"""§7 joint (model, prompt) cell selector.

Reads `outputs/phase1a_raw.parquet` (the §6.2 long-format DB written by
write_phase1a_parquet.py after --phase1a) and applies the locked §7 rule to
12 candidate cells (4 cheap models × 3 prompts P0/P1/P2). The Random column
is reported as a post-hoc sensitivity aggregate but is NOT a selection input
(§5.4).

Locked rule (RESEARCH_DESIGN.md §7):

    candidate cells = {(m, p) : m in {Qwen, DeepSeek, Llama-3.3, Kimi},
                                p in {P0, P1, P2}}  # 12 cells

    normalized_abs_err(respondent, item) = |pred − true| / (max_code − min_code)
    primary_score(cell) = mean over respondents of (mean over Full-condition
                                                    items in their ballot of
                                                    normalized_abs_err)

    DQ-1: parse_failure_rate <= 0.30 per cell
    DQ-3: per-item model variance / human variance >= 0.30 on a strict
          majority of primary_eval items the cell answered
          (cell fails if > 50% of items fail the floor)

    argmin primary_score among DQ-passers.
    Tie-break (within 5% of best score): lowest cost × (1 + parse_fail_rate).
    Tie on both: Qwen × P0 named fallback.
    All cells fail DQ: PAUSE — Phase 1B does not proceed.

The 5% tiebreak window at best MAE ≈ 0.25 is ≈ 0.013, narrower than the
per-cell SE ≈ 0.071 (N=200); see §7 "Honest framing of the tiebreak" — the
selector behaves quality-primary because argmin almost always lands outside
the tiebreak band, and that winner is noise-driven enough that the
180-row §6.1 summary should be reported alongside the headline.

Usage:
    python3 src/select_phase1b_cell.py outputs/phase1a_raw.parquet
    python3 src/select_phase1b_cell.py outputs/phase1a_raw.parquet --json
    python3 src/select_phase1b_cell.py --self-test
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

import pandas as pd

WORK = Path("/Users/joyce/Developer/gsbgen390")
DEFAULT_PARQUET = WORK / "outputs" / "phase1a_raw.parquet"
HUMAN_VARIANCE_PATH = WORK / "outputs" / "primary_eval_human_variance_2024.json"

QWEN_FALLBACK_MODEL = "qwen/qwen-2.5-72b-instruct"
QWEN_FALLBACK_PROMPT = "P0"
RANDOM_LABEL = "Random"
PANEL_MODELS = (
    "qwen/qwen-2.5-72b-instruct",
    "deepseek/deepseek-chat",
    "meta-llama/llama-3.3-70b-instruct",
    "moonshotai/kimi-k2",
)
PROMPTS = ("P0", "P1", "P2")

DQ1_PARSE_FAIL_MAX: float = 0.30
DQ3_RELATIVE_VARIANCE_FLOOR: float = 0.30
DQ3_PER_ITEM_FAIL_MAX: float = 0.50
TIE_BREAK_QUALITY_PCT: float = 0.05
FALLBACK_COST_PCT: float = 0.01

DEFAULT_COST_PER_CALL_USD: dict[str, float] = {
    "qwen/qwen-2.5-72b-instruct":        6.0e-5,
    "deepseek/deepseek-chat":            4.5e-5,
    "meta-llama/llama-3.3-70b-instruct": 5.5e-5,
    "moonshotai/kimi-k2":                7.5e-5,
}
COST_FLOOR_USD: float = 5.0e-5


# ---------------------------------------------------------------------------
# Item code ranges (for per-item normalization)
# ---------------------------------------------------------------------------

def _item_code_ranges() -> dict[str, tuple[int, int]]:
    """Per-item (min_code, max_code) for the 12 primary_eval items.
    Used to normalize abs_err into [0, 1]."""
    # Late import — keeps the selector importable in environments where the
    # heavy pipeline import (pandas/gss data) would fail.
    sys.path.insert(0, str(WORK / "src"))
    from gss_pipeline import format_eval_question, load_taxonomy
    taxonomy = load_taxonomy()
    out: dict[str, tuple[int, int]] = {}
    for item in taxonomy["primary_eval"]["items"]:
        _, meta = format_eval_question(item)
        codes = meta["valid_codes"]
        out[item["id"]] = (min(codes), max(codes))
    return out


def _load_human_variance_reference() -> dict[str, float]:
    if not HUMAN_VARIANCE_PATH.exists():
        return {}
    raw = json.loads(HUMAN_VARIANCE_PATH.read_text())
    return {vid: x["human_variance"] for vid, x in raw["items"].items()}


# ---------------------------------------------------------------------------
# Per-cell metric computation
# ---------------------------------------------------------------------------

def _cell_parse_failure_rate(cell_df: pd.DataFrame) -> float:
    if cell_df.empty:
        return 1.0
    return 1.0 - (cell_df["parse_ok"].astype(int).mean())


def _cell_per_item_variance(cell_df: pd.DataFrame) -> dict[str, float]:
    by_item: dict[str, float] = {}
    ok = cell_df[cell_df["parse_ok"]]
    for item, sub in ok.groupby("item"):
        codes = sub["pred_code"].dropna().tolist()
        by_item[item] = float(statistics.pvariance(codes)) if len(codes) >= 2 else 0.0
    return by_item


def _cell_dq3(
    cell_df: pd.DataFrame,
    human_variance_by_item: dict[str, float],
    floor: float = DQ3_RELATIVE_VARIANCE_FLOOR,
) -> dict[str, Any]:
    model_var = _cell_per_item_variance(cell_df)
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


def _cell_normalized_mae(
    cell_df: pd.DataFrame,
    item_ranges: dict[str, tuple[int, int]],
) -> float | None:
    """Respondent-macro mean of (per-item normalized abs_err) on the Full
    condition. Per-item normalization makes mixed-scale items (binary,
    Likert-3/4/5/7) contribute on a common [0, 1] scale."""
    full = cell_df[(cell_df["condition"] == "Full") & cell_df["parse_ok"]]
    if full.empty:
        return None
    # Normalize each row's abs_err by its item's (max - min)
    def _normalize(row):
        rng = item_ranges.get(row["item"])
        if rng is None:
            return None
        denom = rng[1] - rng[0]
        if denom <= 0 or row["abs_err"] is None:
            return None
        return row["abs_err"] / denom
    full = full.assign(_nae=full.apply(_normalize, axis=1))
    full = full.dropna(subset=["_nae"])
    if full.empty:
        return None
    per_respondent = full.groupby("respondent_id")["_nae"].mean()
    return float(per_respondent.mean())


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

def select_phase1b_cell(
    df: pd.DataFrame,
    item_ranges: dict[str, tuple[int, int]] | None = None,
    cost_per_call: dict[str, float] | None = None,
    human_variance_by_item: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Apply the §7 joint-cell selection rule.

    Inputs:
      df: long-format parquet DataFrame matching the §6.2 schema.
      item_ranges: per-item (min_code, max_code). Defaults to taxonomy lookup.
      cost_per_call: per-model USD/call. Defaults to DEFAULT_COST_PER_CALL_USD.
      human_variance_by_item: per-item GSS 2024 human variance reference.
        Defaults to outputs/primary_eval_human_variance_2024.json.

    Returns a dict with:
      selected_cell:      {"model": slug, "prompt": pid} | None
      rationale:          "argmin_mae" | "tie_break_cost" | "fallback_qwen_p0_tie"
                          | "all_dq_fail_pause" | "fallback_no_data"
      per_cell:           {"model|prompt": {metrics}} for all 12 real cells
      random_column:      {prompt: normalized_mae}  (post-hoc reporting only)
      decision_log:       human-readable audit lines
    """
    cost = dict(DEFAULT_COST_PER_CALL_USD)
    if cost_per_call:
        cost.update(cost_per_call)
    if item_ranges is None:
        item_ranges = _item_code_ranges()
    if human_variance_by_item is None:
        human_variance_by_item = _load_human_variance_reference()

    log: list[str] = []
    per_cell: dict[str, dict[str, Any]] = {}

    real = df[df["model"].isin(PANEL_MODELS)]
    if real.empty:
        return {
            "selected_cell": None,
            "rationale": "fallback_no_data",
            "per_cell": {},
            "random_column": {},
            "decision_log": ["No real-model rows in input parquet."],
        }

    # Score each (model, prompt) cell
    for (model, prompt), cell_df in real.groupby(["model", "prompt"]):
        key = f"{model}|{prompt}"
        pf = _cell_parse_failure_rate(cell_df)
        dq3 = _cell_dq3(cell_df, human_variance_by_item)
        mae = _cell_normalized_mae(cell_df, item_ranges)
        cost_m = max(cost.get(model, 0.0), COST_FLOOR_USD)
        cost_score = cost_m * (1.0 + pf)
        dq1_pass = pf <= DQ1_PARSE_FAIL_MAX
        per_cell[key] = {
            "model": model,
            "prompt": prompt,
            "n_full_rows": int((cell_df["condition"] == "Full").sum()),
            "parse_failure_rate": round(pf, 4),
            "dq3_per_item_fail_pct": dq3["fail_pct"],
            "dq3_n_items_failing": dq3["n_items_failing"],
            "dq3_per_item": dq3["per_item"],
            "normalized_mae": round(mae, 4) if mae is not None else None,
            "cost_per_call_usd": cost_m,
            "cost_score": round(cost_score, 8),
            "dq1_pass": dq1_pass,
            "dq3_pass": dq3["passes"],
        }
        log.append(
            f"  [{model:<40} × {prompt}] pf={pf:.3f} "
            f"dq3_fail={dq3['fail_pct']:.2f} ({dq3['n_items_failing']}/{dq3['n_items']}) "
            f"mae={f'{mae:.4f}' if mae is not None else 'NA'} "
            f"cost={cost_m:.2e} dq1={'OK' if dq1_pass else 'FAIL'} "
            f"dq3={'OK' if dq3['passes'] else 'FAIL'}"
        )

    # Random column aggregates (post-hoc — NOT a selector input per §5.4)
    random_aggs: dict[str, float | None] = {}
    rand = df[df["model"] == RANDOM_LABEL]
    for prompt in PROMPTS:
        sub = rand[rand["prompt"] == prompt]
        random_aggs[prompt] = _cell_normalized_mae(sub, item_ranges) if not sub.empty else None
    log.append("Random-column normalized MAE (post-hoc, reporting only):")
    for prompt, mae in random_aggs.items():
        log.append(f"  Random × {prompt}: {mae:.4f}" if mae is not None else f"  Random × {prompt}: NA")

    survivors = [
        key for key, x in per_cell.items()
        if x["dq1_pass"] and x["dq3_pass"] and x["normalized_mae"] is not None
    ]
    if not survivors:
        log.append(
            "ALL CELLS FAILED DQ-1 or DQ-3 → PAUSE for human review (§7). "
            "All-DQ-fail is a SIGNAL — prompt templates, parser, or model panel "
            "is broken; advancing to Phase 1B on a failed cell wastes $71 of paid runs."
        )
        return {
            "selected_cell": None,
            "rationale": "all_dq_fail_pause",
            "per_cell": per_cell,
            "random_column": random_aggs,
            "decision_log": log,
        }

    survivors.sort(key=lambda k: per_cell[k]["normalized_mae"])
    best_key = survivors[0]
    best_mae = per_cell[best_key]["normalized_mae"]
    log.append(f"Best normalized MAE: {best_mae:.4f} ({best_key})")

    # 5% relative tiebreak window
    tie_window_max = best_mae * (1.0 + TIE_BREAK_QUALITY_PCT)
    in_window = [k for k in survivors if per_cell[k]["normalized_mae"] <= tie_window_max]

    def _decode(key: str) -> dict[str, str]:
        model, prompt = key.split("|")
        return {"model": model, "prompt": prompt}

    if len(in_window) == 1:
        log.append(f"Argmin unique within 5% MAE window → SELECTED: {best_key}")
        return {
            "selected_cell": _decode(best_key),
            "rationale": "argmin_mae",
            "per_cell": per_cell,
            "random_column": random_aggs,
            "decision_log": log,
        }

    # Cost tiebreak among within-5%
    in_window.sort(key=lambda k: per_cell[k]["cost_score"])
    best_cost = per_cell[in_window[0]]["cost_score"]
    cost_tied = [
        k for k in in_window
        if per_cell[k]["cost_score"] <= best_cost * (1.0 + FALLBACK_COST_PCT)
    ]
    log.append(
        f"Quality tie among {len(in_window)} cells within 5% MAE → cost tiebreak. "
        f"Best cost_score={best_cost:.3e}; cells within 1% of best cost: {cost_tied}"
    )
    if len(cost_tied) == 1:
        chosen = cost_tied[0]
        log.append(f"Cost tiebreak SELECTED: {chosen}")
        return {
            "selected_cell": _decode(chosen),
            "rationale": "tie_break_cost",
            "per_cell": per_cell,
            "random_column": random_aggs,
            "decision_log": log,
        }

    log.append(
        f"≥2 cells tie on quality (≤5%) AND cost (≤1%) → applying Qwen × P0 fallback (§7 rule)."
    )
    return {
        "selected_cell": {"model": QWEN_FALLBACK_MODEL, "prompt": QWEN_FALLBACK_PROMPT},
        "rationale": "fallback_qwen_p0_tie",
        "per_cell": per_cell,
        "random_column": random_aggs,
        "decision_log": log,
    }


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _synthetic_cell_df() -> tuple[pd.DataFrame, dict[str, tuple[int, int]], dict[str, float]]:
    """Build a small synthetic parquet-shape DataFrame covering the rule branches.

    Uses 3 synthetic items P1/P2/P3 (codes 1-7 each → max-min = 6).
    20 respondents × 4 models × 3 prompts × 1 condition (Full) × 3 items = 720 rows.
    Per-item human variance is set to 4.0 to make DQ-3 meaningful."""
    item_ranges = {"P1": (1, 7), "P2": (1, 7), "P3": (1, 7)}
    human_var = {"P1": 4.0, "P2": 4.0, "P3": 4.0}
    rows: list[dict] = []
    for rid in range(20):
        truths = {"P1": (rid % 5) + 1, "P2": (rid % 4) + 1, "P3": (rid % 7) + 1}
        for model in PANEL_MODELS:
            for prompt in PROMPTS:
                # Build a per-cell prediction error pattern so we get a clear winner
                # for the argmin_mae test:
                #   qwen × P0:  hits truth exactly (MAE = 0)
                #   all others: shift truth by +1 (MAE = 1/6 ≈ 0.167 after normalization)
                shift = 0 if (model == "qwen/qwen-2.5-72b-instruct" and prompt == "P0") else 1
                for item, truth in truths.items():
                    pred = min(truth + shift, 7)
                    rows.append({
                        "respondent_id": rid,
                        "model": model,
                        "prompt": prompt,
                        "condition": "Full",
                        "item": item,
                        "true_code": truth,
                        "pred_code": pred,
                        "parse_ok": True,
                        "abs_err": abs(pred - truth),
                        "sample_position": 1,
                    })
    df = pd.DataFrame(rows)
    return df, item_ranges, human_var


def _test_argmin_mae() -> None:
    df, item_ranges, human_var = _synthetic_cell_df()
    out = select_phase1b_cell(df, item_ranges=item_ranges, human_variance_by_item=human_var)
    assert out["selected_cell"] is not None, out
    sel = out["selected_cell"]
    assert sel["model"] == "qwen/qwen-2.5-72b-instruct" and sel["prompt"] == "P0", sel
    assert out["rationale"] == "argmin_mae", out["rationale"]
    print(f"  [argmin_mae] PASSED (selected={sel['model']} × {sel['prompt']})")


def _test_all_dq_fail_pause() -> None:
    # Every cell collapses to a single code → DQ-3 fails everywhere
    rows: list[dict] = []
    for rid in range(20):
        truths = {"P1": (rid % 5) + 1, "P2": (rid % 4) + 1, "P3": (rid % 7) + 1}
        for model in PANEL_MODELS:
            for prompt in PROMPTS:
                for item, truth in truths.items():
                    rows.append({
                        "respondent_id": rid, "model": model, "prompt": prompt,
                        "condition": "Full", "item": item,
                        "true_code": truth, "pred_code": 4,  # collapse to constant
                        "parse_ok": True,
                        "abs_err": abs(4 - truth),
                        "sample_position": 1,
                    })
    df = pd.DataFrame(rows)
    out = select_phase1b_cell(
        df, item_ranges={"P1": (1, 7), "P2": (1, 7), "P3": (1, 7)},
        human_variance_by_item={"P1": 4.0, "P2": 4.0, "P3": 4.0},
    )
    assert out["selected_cell"] is None, out["selected_cell"]
    assert out["rationale"] == "all_dq_fail_pause", out["rationale"]
    print("  [all_dq_fail_pause] PASSED")


def _test_fallback_no_data() -> None:
    df = pd.DataFrame(columns=[
        "respondent_id", "model", "prompt", "condition", "item",
        "true_code", "pred_code", "parse_ok", "abs_err", "sample_position",
    ])
    out = select_phase1b_cell(df, item_ranges={}, human_variance_by_item={})
    assert out["selected_cell"] is None, out
    assert out["rationale"] == "fallback_no_data", out["rationale"]
    print("  [fallback_no_data] PASSED")


def _test_tie_break_cost() -> None:
    # qwen × P0 and deepseek × P0 both hit truth exactly → MAE tied at 0
    # deepseek has lower cost → cost tiebreak picks deepseek × P0
    rows: list[dict] = []
    for rid in range(20):
        truths = {"P1": (rid % 5) + 1, "P2": (rid % 4) + 1, "P3": (rid % 7) + 1}
        for model in ("qwen/qwen-2.5-72b-instruct", "deepseek/deepseek-chat"):
            for item, truth in truths.items():
                rows.append({
                    "respondent_id": rid, "model": model, "prompt": "P0",
                    "condition": "Full", "item": item,
                    "true_code": truth, "pred_code": truth,
                    "parse_ok": True, "abs_err": 0, "sample_position": 1,
                })
    df = pd.DataFrame(rows)
    out = select_phase1b_cell(
        df, item_ranges={"P1": (1, 7), "P2": (1, 7), "P3": (1, 7)},
        human_variance_by_item={"P1": 4.0, "P2": 4.0, "P3": 4.0},
    )
    sel = out["selected_cell"]
    assert sel == {"model": "deepseek/deepseek-chat", "prompt": "P0"}, sel
    assert out["rationale"] == "tie_break_cost", out["rationale"]
    print("  [tie_break_cost] PASSED")


def _test_fallback_qwen_p0_tie() -> None:
    # 3 cells all tied on quality (MAE=0) AND cost (override identical costs) →
    # Qwen × P0 named fallback fires.
    rows: list[dict] = []
    for rid in range(20):
        truths = {"P1": (rid % 5) + 1, "P2": (rid % 4) + 1, "P3": (rid % 7) + 1}
        for model in ("qwen/qwen-2.5-72b-instruct", "deepseek/deepseek-chat",
                      "meta-llama/llama-3.3-70b-instruct"):
            for item, truth in truths.items():
                rows.append({
                    "respondent_id": rid, "model": model, "prompt": "P1",
                    "condition": "Full", "item": item,
                    "true_code": truth, "pred_code": truth,
                    "parse_ok": True, "abs_err": 0, "sample_position": 1,
                })
    df = pd.DataFrame(rows)
    cost_override = {m: 6.0e-5 for m in (
        "qwen/qwen-2.5-72b-instruct",
        "deepseek/deepseek-chat",
        "meta-llama/llama-3.3-70b-instruct",
    )}
    out = select_phase1b_cell(
        df,
        item_ranges={"P1": (1, 7), "P2": (1, 7), "P3": (1, 7)},
        cost_per_call=cost_override,
        human_variance_by_item={"P1": 4.0, "P2": 4.0, "P3": 4.0},
    )
    assert out["selected_cell"] == {"model": QWEN_FALLBACK_MODEL, "prompt": "P0"}, \
        out["selected_cell"]
    assert out["rationale"] == "fallback_qwen_p0_tie", out["rationale"]
    print("  [fallback_qwen_p0_tie] PASSED")


def _test_random_column_reporting() -> None:
    df, item_ranges, human_var = _synthetic_cell_df()
    # Append synthetic Random rows mirroring qwen × P0 for rid=0..9
    qwen_p0 = df[(df["model"] == "qwen/qwen-2.5-72b-instruct") & (df["prompt"] == "P0")
                  & (df["respondent_id"] < 10)]
    random_rows = qwen_p0.copy()
    random_rows["model"] = RANDOM_LABEL
    df_with_random = pd.concat([df, random_rows], ignore_index=True)
    out = select_phase1b_cell(
        df_with_random, item_ranges=item_ranges, human_variance_by_item=human_var,
    )
    # Random × P0 inherits qwen × P0's perfect predictions → MAE = 0
    assert out["random_column"].get("P0") == 0.0, out["random_column"]
    # Random × P1 / P2: no Random rows for those prompts → None
    assert out["random_column"].get("P1") is None, out["random_column"]
    assert out["random_column"].get("P2") is None, out["random_column"]
    # Random is NOT in per_cell (post-hoc only)
    for key in out["per_cell"]:
        assert not key.startswith("Random|"), key
    print("  [random_column_reporting] PASSED")


def run_self_tests() -> int:
    print("§7 joint-cell selector self-tests")
    _test_argmin_mae()
    _test_all_dq_fail_pause()
    _test_fallback_no_data()
    _test_tie_break_cost()
    _test_fallback_qwen_p0_tie()
    _test_random_column_reporting()
    print("✓ ALL 6 SELF-TESTS PASSED")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("parquet_path", type=Path, nargs="?", default=DEFAULT_PARQUET,
                   help=f"Phase 1A long-format parquet (default: {DEFAULT_PARQUET}).")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--json", action="store_true",
                   help="emit decision as JSON (default: human-readable)")
    args = p.parse_args()

    if args.self_test:
        return run_self_tests()

    if not args.parquet_path.exists():
        print(f"error: {args.parquet_path} not found", file=sys.stderr)
        return 2

    df = pd.read_parquet(args.parquet_path)
    decision = select_phase1b_cell(df)

    if args.json:
        print(json.dumps(decision, indent=2, default=str))
        return 0

    print(f"=== §7 joint (model, prompt) cell selection ===")
    print(f"Parquet: {args.parquet_path}")
    print(f"  rows: {len(df):,}  cells: {df.groupby(['model', 'prompt']).ngroups}")
    print(f"\nDecision log:")
    for line in decision["decision_log"]:
        print(line)
    sel = decision["selected_cell"]
    print(f"\nSELECTED CELL: {sel['model'] + ' × ' + sel['prompt'] if sel else 'PAUSE — review required'}")
    print(f"RATIONALE: {decision['rationale']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
