"""Phase 1B analysis — §8 two-layer LOO tables (T0–T5).

Implements the locked RESEARCH_DESIGN.md §8 spec on outputs/phase1b_raw.parquet:

  Layer 1 (headline): 4-bin LOO ΔMAE vs Full, paired at the respondent level,
  BCa bootstrap CIs (B=10,000, seed 42, respondent clusters), Holm-Bonferroni
  across the 4 bins on the N=3,109 headline cohort (full cross-section minus
  the §7 selector's 200 panel respondents); full N=3,309 as sensitivity.

  Layer 2: randomized battery ablation — paired (rid, item) differences
  `err_ablated − err_full` grouped by `random_dropped_battery`, parse_ok
  required in both arms (§8 missingness note), BCa CIs on respondent clusters.

Metric conventions imported from select_phase1b_cell (identical normalization
to the §7 selector): normalized_abs_err = |pred − true| / (max_code − min_code)
per item; CONSERVATIVE primary (parse_fail → 1.0), OPTIMISTIC (drop parse_fail
rows) reported alongside.

Outputs (all DRAFT until Joyce signs off):
  outputs/phase1b_tables.xlsx   — T0–T5 sheets
  outputs/phase1b_analysis.json — machine-readable numbers
  console summary               — headline paragraph numbers

Tables (locked with Joyce 2026-07-14; raw tables stay raw per-item —
aggregations live in separate sheets, never mixed into T0):
  T0  raw per-item × 6-condition × model-column normalized MAE (+ n)
  T1  Full-condition baseline per item × model column
  T2  bin-LOO ΔMAE per bin × model column (+BCa CI, Holm-adjusted p)
  T3  battery ablation ΔMAE per battery × model column (+CI, n), sorted
  T4  LLM Full vs R2 regression baseline per item
  T5  parse_fail by model × item; conservative-vs-optimistic headline gap
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from select_phase1b_cell import _item_code_ranges  # §7 normalization source
from gss_loader import load_gss
from gss_pipeline import sample_respondents

ROOT = Path(__file__).resolve().parent.parent
PARQUET = ROOT / "outputs" / "phase1b_raw.parquet"
R2_JSON = ROOT / "outputs" / "phase1b_r2_baseline.json"
XLSX_OUT = ROOT / "outputs" / "phase1b_tables.xlsx"
JSON_OUT = ROOT / "outputs" / "phase1b_analysis.json"

B = 10_000
SEED = 42
BINS = ["drop_demographic", "drop_behavioral", "drop_psychological", "drop_attitudinal"]
MODEL_SHORT = {
    "qwen/qwen3-max": "qwen3-max",
    "deepseek/deepseek-v3.1-terminus": "deepseek-v3.1",
    "meta-llama/llama-4-maverick": "llama-4-mav",
    "moonshotai/kimi-k2-0905": "kimi-k2",
}
COMBINED = "random(combined)"


def add_normalized_err(df: pd.DataFrame, conservative: bool) -> pd.Series:
    """Per-row normalized error under the chosen parse_fail policy.

    conservative=True: parse_fail rows get 1.0 (§7 primary convention).
    conservative=False (optimistic): parse_fail rows get NaN (dropped).
    """
    ranges = _item_code_ranges()
    span = df["item"].map({k: hi - lo for k, (lo, hi) in ranges.items()})
    err = df["abs_err"].astype(float) / span
    if conservative:
        return err.where(df["parse_ok"], 1.0)
    return err.where(df["parse_ok"], np.nan)


def respondent_macro(df: pd.DataFrame, err_col: str) -> pd.Series:
    """§7 macro convention: mean over each respondent's items, indexed by rid."""
    return df.groupby("respondent_id")[err_col].mean()


def bca_ci(values: np.ndarray, b: int = B, seed: int = SEED) -> tuple[float, float]:
    """BCa bootstrap CI for the mean of respondent-level values."""
    from scipy.stats import bootstrap
    values = values[~np.isnan(values)]
    if len(values) < 20:
        return (float("nan"), float("nan"))
    res = bootstrap(
        (values,), np.mean, n_resamples=b, method="BCa",
        random_state=np.random.default_rng(seed), vectorized=False,
    )
    return (float(res.confidence_interval.low), float(res.confidence_interval.high))


def cluster_ratio_bca_ci(sums: np.ndarray, counts: np.ndarray,
                         b: int = B, seed: int = SEED) -> tuple[float, float]:
    """BCa CI for a pair-level mean with respondent clusters: resample
    respondents, statistic = sum(delta sums) / sum(pair counts)."""
    from scipy.stats import bootstrap
    if len(sums) < 20:
        return (float("nan"), float("nan"))
    res = bootstrap(
        (sums, counts), lambda s, c: np.sum(s) / np.sum(c),
        n_resamples=b, method="BCa", paired=True,
        random_state=np.random.default_rng(seed), vectorized=False,
    )
    return (float(res.confidence_interval.low), float(res.confidence_interval.high))


def boot_p_two_sided(values: np.ndarray, b: int = B, seed: int = SEED) -> float:
    """Percentile-bootstrap two-sided p for H0: mean == 0 (respondent clusters)."""
    values = values[~np.isnan(values)]
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(b, len(values)))
    means = values[idx].mean(axis=1)
    p_low = float((means <= 0).mean())
    return float(min(1.0, 2 * min(p_low, 1 - p_low) + 1 / b))


def holm(pvals: dict[str, float]) -> dict[str, float]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    out, m, running = {}, len(items), 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def model_frames(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Column set: per-model respondent subsets + the combined random column."""
    out = {}
    for slug, short in MODEL_SHORT.items():
        out[short] = df[df["model"] == slug]
    out[COMBINED] = df
    return out


def build_tables(df: pd.DataFrame, cohort_name: str) -> dict:
    tables: dict = {"cohort": cohort_name, "n_respondents": df["respondent_id"].nunique()}
    df = df.copy()
    df["err_cons"] = add_normalized_err(df, conservative=True)
    df["err_opt"] = add_normalized_err(df, conservative=False)
    cols = model_frames(df)

    # ---- T0: raw per-item × condition × model column (conservative) --------
    t0 = []
    for cname, cdf in cols.items():
        g = cdf.groupby(["item", "condition"])["err_cons"].agg(["mean", "count"]).reset_index()
        g["column"] = cname
        t0.append(g)
    t0 = pd.concat(t0).pivot_table(
        index=["item", "condition"], columns="column", values="mean"
    ).round(4).reset_index()
    tables["T0_raw"] = t0

    # ---- T1: Full-condition baseline per item ------------------------------
    full = {c: cdf[cdf["condition"] == "Full"] for c, cdf in cols.items()}
    t1 = pd.DataFrame({
        c: fdf.groupby("item")["err_cons"].mean() for c, fdf in full.items()
    }).round(4)
    t1["n_pairs(combined)"] = full[COMBINED].groupby("item").size()
    tables["T1_full_baseline"] = t1.reset_index()

    # ---- T2: bin-LOO ΔMAE ---------------------------------------------------
    rows = []
    for cname, cdf in cols.items():
        full_macro = respondent_macro(cdf[cdf["condition"] == "Full"], "err_cons")
        pvals = {}
        for b_ in BINS:
            loo_macro = respondent_macro(cdf[cdf["condition"] == b_], "err_cons")
            delta = (loo_macro - full_macro).dropna()
            lo, hi = bca_ci(delta.values)
            p = boot_p_two_sided(delta.values)
            pvals[b_] = p
            rows.append({
                "bin": b_, "column": cname, "delta_mae": delta.mean(),
                "ci_lo": lo, "ci_hi": hi, "p_boot": p,
                "n_respondents": len(delta),
            })
        adj = holm(pvals)
        for r in rows:
            if r["column"] == cname and r["bin"] in adj and "p_holm" not in r:
                r["p_holm"] = adj[r["bin"]]
    t2 = pd.DataFrame(rows)
    tables["T2_bin_loo"] = t2.round(4)

    # ---- T3: battery ablation (paired on (rid, item), parse_ok both arms) --
    rbd = df[df["condition"] == "random_battery_drop"]
    fullc = df[df["condition"] == "Full"]
    pair = rbd.merge(
        fullc[["respondent_id", "item", "err_cons", "err_opt", "parse_ok"]],
        on=["respondent_id", "item"], suffixes=("_abl", "_full"),
    )
    both_ok = pair[pair["parse_ok_abl"] & pair["parse_ok_full"]].copy()
    both_ok["delta"] = both_ok["err_cons_abl"] - both_ok["err_cons_full"]
    # §8 missingness check: differential parse failure between arms
    tables["battery_missingness"] = {
        "pairs_total": len(pair),
        "pairs_both_parse_ok": len(both_ok),
        "abl_only_fail": int((~pair["parse_ok_abl"] & pair["parse_ok_full"]).sum()),
        "full_only_fail": int((pair["parse_ok_abl"] & ~pair["parse_ok_full"]).sum()),
    }
    rows = []
    for cname in cols:
        sub = both_ok if cname == COMBINED else both_ok[both_ok["model"] == {v: k for k, v in MODEL_SHORT.items()}[cname]]
        for bat, g in sub.groupby("random_dropped_battery"):
            # §8 estimand: mean(err_ablated − err_full) over the PAIRS where
            # b was drawn (pair-level mean, not respondent-macro). Inference
            # still clusters by respondent: bootstrap resamples respondents
            # and recomputes the pair-level mean from their (sum, n) pairs.
            per_resp = g.groupby("respondent_id")["delta"].agg(["sum", "count"])
            lo, hi = cluster_ratio_bca_ci(
                per_resp["sum"].values, per_resp["count"].values
            )
            rows.append({
                "battery": bat, "column": cname,
                "delta_mae": g["delta"].mean(), "ci_lo": lo, "ci_hi": hi,
                "n_pairs": len(g), "n_respondents": len(per_resp),
                "n_items_support": g["item"].nunique(),
            })
    t3 = pd.DataFrame(rows)
    order = (
        t3[t3["column"] == COMBINED]
        .sort_values("delta_mae", ascending=False)["battery"].tolist()
    )
    t3["battery"] = pd.Categorical(t3["battery"], categories=order, ordered=True)
    tables["T3_battery_ablation"] = t3.sort_values(["battery", "column"]).round(4)

    # ---- T5: DQ / parse_fail ------------------------------------------------
    t5 = (
        df.assign(model_short=df["model"].map(MODEL_SHORT))
        .pivot_table(index="item", columns="model_short", values="parse_ok",
                     aggfunc=lambda s: 1 - s.mean())
        .round(4)
    )
    headline_cons = respondent_macro(full[COMBINED], "err_cons").mean()
    headline_opt = respondent_macro(full[COMBINED], "err_opt").mean()
    tables["T5_parse_fail"] = t5.reset_index()
    tables["headline"] = {
        "full_mae_conservative": round(float(headline_cons), 4),
        "full_mae_optimistic": round(float(headline_opt), 4),
        "conservative_optimistic_gap": round(float(headline_cons - headline_opt), 4),
    }
    return tables


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 1B §8 analysis (T0–T5)")
    ap.add_argument("--parquet", type=Path, default=PARQUET)
    ap.add_argument("--xlsx", type=Path, default=XLSX_OUT)
    ap.add_argument("--json", type=Path, default=JSON_OUT)
    args = ap.parse_args()

    df = pd.read_parquet(args.parquet)
    assert set(df["condition"].unique()) == {
        "Full", *BINS, "random_battery_drop"
    }, f"unexpected conditions: {df['condition'].unique()}"

    # Headline cohort: full minus the §7 selector's 200 panel respondents.
    panel_rids = set(sample_respondents(n=200, seed=SEED)["ID_"].astype(int))
    headline_df = df[~df["respondent_id"].isin(panel_rids)]
    print(f"cohorts: headline N={headline_df['respondent_id'].nunique()}, "
          f"full N={df['respondent_id'].nunique()} (panel overlap {len(panel_rids)})")

    results = {
        "headline_N3109": build_tables(headline_df, "headline_N3109"),
        "sensitivity_N3309": build_tables(df, "sensitivity_N3309"),
    }

    # T4: LLM Full vs R2 baseline (per item, combined column, headline cohort)
    if R2_JSON.exists():
        r2 = json.loads(R2_JSON.read_text())
        t1 = results["headline_N3109"]["T1_full_baseline"].set_index("item")
        ranges = _item_code_ranges()
        # R2 JSON stores RAW-scale MAE; normalize by the same §7 item span so
        # the two columns are commensurable.
        r2_norm = {
            item: v["mae"] / (ranges[item][1] - ranges[item][0])
            for item, v in r2.items()
            if isinstance(v, dict) and "mae" in v and item in ranges
        }
        t4 = pd.DataFrame({
            "llm_full_mae": t1[COMBINED],
            "r2_baseline_mae": pd.Series(r2_norm, dtype=float),
        })
        t4["llm_gain"] = t4["r2_baseline_mae"] - t4["llm_full_mae"]
        results["headline_N3109"]["T4_llm_vs_r2"] = t4.round(4).reset_index()

    readme_rows = [
        ("WORKBOOK GUIDE", ""),
        ("", ""),
        ("Sheet suffix _H", "Headline cohort, N = 3,109: the full GSS 2024 cross-section minus the 200 respondents Phase 1A used to select the model/prompt cell. Use these numbers."),
        ("Sheet suffix _S", "Sensitivity cohort, N = 3,309: everyone included. Reported to show the selection-optimism gap (it is about 0.001)."),
        ("", ""),
        ("T0_raw", "Raw building block: per-item x per-condition normalized MAE, one column per model plus random(combined). No aggregation mixed in; every other sheet can be recomputed from the raw prediction file."),
        ("T1_full_baseline", "Baseline accuracy: per-item normalized MAE in the Full condition (all features minus the held-out item's own battery). n_pairs = scored (respondent, item) pairs."),
        ("T2_bin_loo", "Layer 1 result: for each of the 4 feature bins, delta_mae = MAE(bin dropped) minus MAE(Full), paired within respondent. Positive = dropping the bin hurts. ci_lo/ci_hi = 95% BCa bootstrap (B=10,000, respondent clusters); p_holm = Holm-corrected across the 4 bins."),
        ("T3_battery_ablation", "Layer 2 result: for each of the 34 batteries, mean of err(ablated) minus err(Full) over the (respondent, item) pairs where that battery was randomly dropped, parse-ok in both arms. Sorted by the combined column. n_items_support: batteries owning primary items are evaluated on fewer items."),
        ("T4_llm_vs_r2", "LLM (Full condition, combined column) vs a ridge/logistic regression trained on the same features under the same leakage rule, 5-fold CV. llm_gain = regression MAE minus LLM MAE; positive means the LLM is better. Headline cohort only."),
        ("T5_parse_fail", "Data quality: share of calls per item x model where the answer did not parse to a valid code. Concentrated in Kimi-K2 (4.9%); all other models at or near zero."),
        ("", ""),
        ("Metric", "Normalized error = |predicted - true| / (item scale max - min), in [0, 1]. All sheets use the CONSERVATIVE policy: an unparsable answer counts as error 1.0. The optimistic variant (drop unparsed rows) shifts the headline by 0.0094 and changes no conclusion."),
        ("Model columns", "Respondents are partitioned by which panel model answered them (seeded random dispatch, about 25% each). random(combined) = all respondents together; this is the headline column."),
        ("Reproduction", "python3 src/phase1b_analysis.py regenerates this workbook from phase1b_raw.parquet (all randomness seeded, seed 42). Repo: github.com/Joyceqx/gsbgen390-persona-pipeline"),
    ]
    readme_df = pd.DataFrame(readme_rows, columns=["Sheet / topic", "What it shows"])

    with pd.ExcelWriter(args.xlsx) as xw:
        readme_df.to_excel(xw, sheet_name="READ_ME", index=False)
        ws = xw.sheets["READ_ME"]
        ws.column_dimensions["A"].width = 24
        ws.column_dimensions["B"].width = 130
        for cohort, tabs in results.items():
            for name, tab in tabs.items():
                if isinstance(tab, pd.DataFrame):
                    sheet = f"{name[:24]}_{'H' if 'headline' in cohort else 'S'}"
                    tab.to_excel(xw, sheet_name=sheet[:31], index=False)
    args.json.write_text(json.dumps(
        {c: {k: (v.to_dict("records") if isinstance(v, pd.DataFrame) else v)
             for k, v in tabs.items()} for c, tabs in results.items()},
        indent=1, default=str))

    h = results["headline_N3109"]
    print(f"\nheadline (N=3,109, conservative): Full MAE = "
          f"{h['headline']['full_mae_conservative']}"
          f" (optimistic {h['headline']['full_mae_optimistic']})")
    print("\nT2 bin-LOO ΔMAE (combined column):")
    t2 = h["T2_bin_loo"]
    print(t2[t2["column"] == COMBINED][
        ["bin", "delta_mae", "ci_lo", "ci_hi", "p_holm"]].to_string(index=False))
    print(f"\nwrote {args.xlsx.name} + {args.json.name} (DRAFT — Joyce review "
          f"before sending)")


if __name__ == "__main__":
    main()
