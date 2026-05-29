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

    DQ-1: parse_failure_rate <= 0.10 per cell (tightened from 0.30 — locked
          2026-05-29 per Reviewer round-2 Q2; cheap LLMs in practice
          parse-fail <5%, so 10% is still a generous safety net while
          closing the evasive-cell loophole).
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

import numpy as np
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

# DQ-1 ceiling tightened 0.30 → 0.10 (locked 2026-05-29 Joyce decision per
# Reviewer round-2 Q2): cheap LLMs in practice have parse_failure_rate < 5%
# on this task. A cell at 30% is broken, not borderline. The previous 30%
# was an overly generous safety net that left room for evasive cells to
# slip through the conservative MAE metric.
DQ1_PARSE_FAIL_MAX: float = 0.10
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


BOOTSTRAP_B: int = 10_000
BOOTSTRAP_SEED: int = 42


def _cell_bootstrap_ci(
    cell_df: pd.DataFrame,
    item_ranges: dict[str, tuple[int, int]],
    B: int = BOOTSTRAP_B,
    seed: int = BOOTSTRAP_SEED,
    parse_fail_as_max: bool = True,
) -> tuple[float | None, float | None, float | None]:
    """Respondent-level percentile bootstrap CI on the cell's normalized MAE.

    Robustness diagnostic per Reviewer round-2 Q1 (Joyce-locked 2026-05-29).
    The selector's N=200 per-cell SE (~0.071) is ~5x wider than the 5%
    tiebreak window (~0.013) at typical MAE ≈ 0.25, so the argmin "winner"
    is largely noise-driven (see §7 "Honest framing of the tiebreak").
    Reporting per-cell bootstrap CIs alongside the point estimate lets
    readers see directly which cells' CIs overlap with the headline cell's
    — that overlap is the visual stand-in for "argmin gap < SE".

    Implementation: resample respondent IDs with replacement; for each
    resample, recompute the respondent-macro normalized MAE; take 2.5 / 97.5
    percentiles. Vectorized over B bootstrap iterations.

    Returns (point_estimate, ci_lo, ci_hi). All three None if the cell has
    no usable Full-condition rows.
    """
    full = cell_df[cell_df["condition"] == "Full"]
    if full.empty:
        return None, None, None
    range_map = {item: rng[1] - rng[0] for item, rng in item_ranges.items()}
    full = full.copy()
    full["_denom"] = full["item"].map(range_map)
    full = full[full["_denom"] > 0]
    if full.empty:
        return None, None, None
    if parse_fail_as_max:
        ok_nae = full["abs_err"].astype("float") / full["_denom"].astype("float")
        full["_nae"] = ok_nae.where(full["parse_ok"], 1.0)
    else:
        full = full[full["parse_ok"]]
        if full.empty:
            return None, None, None
        full["_nae"] = full["abs_err"].astype("float") / full["_denom"].astype("float")
    full = full.dropna(subset=["_nae"])
    if full.empty:
        return None, None, None
    per_rid = full.groupby("respondent_id")["_nae"].mean()
    rids = per_rid.index.to_numpy()
    means = per_rid.to_numpy()
    n = len(rids)
    if n == 0:
        return None, None, None
    point = float(means.mean())
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(B, n))
    boot_means = means[idx].mean(axis=1)
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    return point, float(lo), float(hi)


def _cell_normalized_mae(
    cell_df: pd.DataFrame,
    item_ranges: dict[str, tuple[int, int]],
    parse_fail_as_max: bool = True,
) -> float | None:
    """Respondent-macro mean of (per-item normalized abs_err) on the Full
    condition. Per-item normalization makes mixed-scale items (binary,
    Likert-3/4/5/7) contribute on a common [0, 1] scale.

    `parse_fail_as_max` (locked 2026-05-29 per Reviewer round-2 Q2):
      - True  (DEFAULT, "conservative"): parse_fail rows count as
        normalized_abs_err = 1.0 (maximum possible error). This is the
        selector's PRIMARY metric. Without it, a cell that strategically
        refuses to answer hard items can look better than a cell that
        answers everything — the optimistic metric structurally rewards
        evasion.
      - False ("optimistic"): parse_fail rows are dropped. This is the
        sensitivity / legacy metric, reported alongside the conservative
        version so writeups can show readers how much of the headline
        depends on the parse_fail policy.
    """
    full = cell_df[cell_df["condition"] == "Full"]
    if full.empty:
        return None
    range_map = {item: rng[1] - rng[0] for item, rng in item_ranges.items()}
    full = full.copy()
    full["_denom"] = full["item"].map(range_map)
    full = full[full["_denom"] > 0]
    if full.empty:
        return None
    if parse_fail_as_max:
        # Conservative: parse_fail → 1.0; parse_ok → abs_err / denom.
        ok_nae = full["abs_err"].astype("float") / full["_denom"].astype("float")
        full["_nae"] = ok_nae.where(full["parse_ok"], 1.0)
    else:
        # Optimistic: drop parse_fail rows entirely.
        full = full[full["parse_ok"]]
        if full.empty:
            return None
        full["_nae"] = full["abs_err"].astype("float") / full["_denom"].astype("float")
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

    # Score each (model, prompt) cell. Both MAE versions are computed:
    # `mae_conservative` (parse_fail → 1.0; PRIMARY) drives selection;
    # `mae_optimistic` (parse_fail dropped) is the sensitivity report.
    for (model, prompt), cell_df in real.groupby(["model", "prompt"]):
        key = f"{model}|{prompt}"
        pf = _cell_parse_failure_rate(cell_df)
        dq3 = _cell_dq3(cell_df, human_variance_by_item)
        mae_conservative, ci_lo, ci_hi = _cell_bootstrap_ci(
            cell_df, item_ranges, parse_fail_as_max=True,
        )
        mae_optimistic = _cell_normalized_mae(
            cell_df, item_ranges, parse_fail_as_max=False,
        )
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
            "normalized_mae": round(mae_conservative, 4) if mae_conservative is not None else None,
            "normalized_mae_optimistic": round(mae_optimistic, 4) if mae_optimistic is not None else None,
            "bootstrap_ci_lo": round(ci_lo, 4) if ci_lo is not None else None,
            "bootstrap_ci_hi": round(ci_hi, 4) if ci_hi is not None else None,
            "cost_per_call_usd": cost_m,
            "cost_score": round(cost_score, 8),
            "dq1_pass": dq1_pass,
            "dq3_pass": dq3["passes"],
        }
        ci_str = (
            f"[{ci_lo:.4f}, {ci_hi:.4f}]" if ci_lo is not None and ci_hi is not None else "[NA, NA]"
        )
        log.append(
            f"  [{model:<40} × {prompt}] pf={pf:.3f} "
            f"dq3_fail={dq3['fail_pct']:.2f} ({dq3['n_items_failing']}/{dq3['n_items']}) "
            f"mae_c={f'{mae_conservative:.4f}' if mae_conservative is not None else 'NA'} "
            f"95% CI {ci_str} (opt {f'{mae_optimistic:.4f}' if mae_optimistic is not None else 'NA'}) "
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

    # CI-overlap robustness diagnostic: which surviving cells have bootstrap
    # CIs overlapping the headline's CI? Per Reviewer round-2 Q1, an
    # overlapping CI means the headline cell's lead is within bootstrap noise.
    best_lo = per_cell[best_key]["bootstrap_ci_lo"]
    best_hi = per_cell[best_key]["bootstrap_ci_hi"]
    overlapping = []
    if best_lo is not None and best_hi is not None:
        for k in survivors[1:]:
            lo = per_cell[k]["bootstrap_ci_lo"]
            hi = per_cell[k]["bootstrap_ci_hi"]
            if lo is None or hi is None:
                continue
            # CIs overlap iff max(lo) <= min(hi)
            if max(best_lo, lo) <= min(best_hi, hi):
                overlapping.append(k)
    if overlapping:
        log.append(
            f"  CI-overlap diagnostic: {len(overlapping)} other surviving cell(s) "
            f"have bootstrap CIs that overlap the headline's "
            f"[{best_lo:.4f}, {best_hi:.4f}] — headline is best on this cohort "
            f"but not statistically separated from: "
            + ", ".join(f"{k} [{per_cell[k]['bootstrap_ci_lo']:.4f}, {per_cell[k]['bootstrap_ci_hi']:.4f}]" for k in overlapping[:3])
            + (f" (+{len(overlapping)-3} more)" if len(overlapping) > 3 else "")
        )
    elif best_lo is not None:
        log.append(
            f"  CI-overlap diagnostic: headline CI [{best_lo:.4f}, {best_hi:.4f}] "
            f"does not overlap any other surviving cell's CI — argmin is "
            f"statistically separated."
        )

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


def _test_parse_fail_conservative_vs_optimistic() -> None:
    """The conservative metric (parse_fail → 1.0) must penalize a cell that
    strategically parse_fails on hard items while the optimistic metric
    (current behavior pre-2026-05-29) lets that cell off the hook.

    Construct:
      - qwen × P0: hits every item (MAE_optimistic = 0, MAE_conservative = 0).
      - deepseek × P0: hits every item it answers (small MAE on answered),
        but parse_fails 40% of the time on item P1 — far above the 10% DQ-1
        ceiling, so the cell is disqualified entirely (so the conservative
        winner is qwen × P0). This also exercises the DQ-1 tightening
        (was 30% → now 10%): under the old 30% ceiling deepseek would
        have survived DQ.
    """
    rows: list[dict] = []
    for rid in range(20):
        truths = {"P1": (rid % 5) + 1, "P2": (rid % 4) + 1, "P3": (rid % 7) + 1}
        # qwen: perfect everywhere
        for item, truth in truths.items():
            rows.append({
                "respondent_id": rid, "model": "qwen/qwen-2.5-72b-instruct",
                "prompt": "P0", "condition": "Full", "item": item,
                "true_code": truth, "pred_code": truth,
                "parse_ok": True, "abs_err": 0, "sample_position": 1,
            })
        # deepseek: parse_fails on P1 for 40% of respondents (8/20).
        # Note: deepseek's RAW parse_fail rate over all 60 deepseek rows is 8/60 = 13.3%,
        # which is above the 10% DQ-1 ceiling. (Pre-2026-05-29 the ceiling was 30% so
        # deepseek would have survived; the tightened ceiling now flags it.)
        for item, truth in truths.items():
            if item == "P1" and rid < 8:
                rows.append({
                    "respondent_id": rid, "model": "deepseek/deepseek-chat",
                    "prompt": "P0", "condition": "Full", "item": item,
                    "true_code": truth, "pred_code": None,
                    "parse_ok": False, "abs_err": None, "sample_position": 1,
                })
            else:
                rows.append({
                    "respondent_id": rid, "model": "deepseek/deepseek-chat",
                    "prompt": "P0", "condition": "Full", "item": item,
                    "true_code": truth, "pred_code": truth,
                    "parse_ok": True, "abs_err": 0, "sample_position": 1,
                })
    df = pd.DataFrame(rows)
    item_ranges = {"P1": (1, 7), "P2": (1, 7), "P3": (1, 7)}
    human_var = {"P1": 4.0, "P2": 4.0, "P3": 4.0}
    out = select_phase1b_cell(df, item_ranges=item_ranges,
                              human_variance_by_item=human_var)
    deepseek = out["per_cell"]["deepseek/deepseek-chat|P0"]
    qwen = out["per_cell"]["qwen/qwen-2.5-72b-instruct|P0"]
    # DQ-1: deepseek's parse_failure_rate ≈ 0.133 > 0.10 → disqualified.
    assert not deepseek["dq1_pass"], deepseek["parse_failure_rate"]
    assert qwen["dq1_pass"], qwen["parse_failure_rate"]
    # Conservative MAE penalizes deepseek (parse_fails count as 1.0):
    # deepseek's MAE_conservative > 0; optimistic = 0.
    assert deepseek["normalized_mae"] is not None and deepseek["normalized_mae"] > 0, deepseek
    assert deepseek["normalized_mae_optimistic"] == 0.0, deepseek
    # Selector picks qwen × P0 (deepseek DQ'd out).
    assert out["selected_cell"] == {
        "model": "qwen/qwen-2.5-72b-instruct", "prompt": "P0",
    }, out["selected_cell"]
    print(
        f"  [parse_fail_conservative_vs_optimistic] PASSED "
        f"(deepseek mae_conservative={deepseek['normalized_mae']:.4f}, "
        f"mae_optimistic={deepseek['normalized_mae_optimistic']}, "
        f"DQ-1 flag={deepseek['parse_failure_rate']:.3f} > 0.10)"
    )


def _test_bootstrap_ci_brackets_point() -> None:
    """Bootstrap CI must bracket the point estimate, both bounds in [0, 1]
    (the normalized MAE range), and CI width should be > 0 for a non-
    degenerate cell."""
    df, item_ranges, _ = _synthetic_cell_df()
    qwen_p0 = df[(df["model"] == "qwen/qwen-2.5-72b-instruct") & (df["prompt"] == "P0")]
    point, lo, hi = _cell_bootstrap_ci(qwen_p0, item_ranges, B=1_000)
    # Qwen × P0 in the synthetic data hits truth exactly → MAE = 0; CI tight
    # around 0 (lo and hi both = 0.0 since every per-rid mean = 0).
    assert point == 0.0, point
    assert lo == 0.0 and hi == 0.0, (lo, hi)

    # Now pick a cell with non-zero MAE: any "other model × P0" with shift = 1.
    deepseek_p0 = df[(df["model"] == "deepseek/deepseek-chat") & (df["prompt"] == "P0")]
    point, lo, hi = _cell_bootstrap_ci(deepseek_p0, item_ranges, B=2_000, seed=1)
    assert point is not None and lo is not None and hi is not None
    assert 0.0 <= lo <= point <= hi <= 1.0, (lo, point, hi)
    assert hi > lo, "CI should have non-zero width on a noisy cell"
    print(f"  [bootstrap_ci_brackets_point] PASSED (deepseek × P0: {point:.4f}, [{lo:.4f}, {hi:.4f}])")


def run_self_tests() -> int:
    print("§7 joint-cell selector self-tests")
    _test_argmin_mae()
    _test_all_dq_fail_pause()
    _test_fallback_no_data()
    _test_tie_break_cost()
    _test_fallback_qwen_p0_tie()
    _test_random_column_reporting()
    _test_parse_fail_conservative_vs_optimistic()
    _test_bootstrap_ci_brackets_point()
    print("✓ ALL 8 SELF-TESTS PASSED")
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
