"""Re-base the Phase 1A cell analysis on raw_tables.xlsx (the databook).

Cell-level metrics = item-macro aggregation of the databook's 12 per-item rows
(equal weight per item, matching the earlier EM-forward analysis). Reliability
uses the databook's own collapse proxy (pred_top1_share / pred_distinct_codes),
since DQ-3 variance-ratio is not stored in the table. Cell CIs are a respondent
bootstrap (B=2000, seed=42) over the same JSON the databook was built from.

Writes report/databook_stats.json and prints a verification against the numbers
in the user's pasted prior analysis.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

import numpy as np
import pandas as pd

ROOT = Path("/Users/joyce/Developer/gsbgen390")
sys.path.insert(0, str(ROOT / "src"))
from gss_pipeline import format_eval_question, load_taxonomy  # noqa: E402

tx = load_taxonomy()
PRIMARY = [it["id"] for it in tx["primary_eval"]["items"]]
META = {}
for it in tx["primary_eval"]["items"]:
    _, m = format_eval_question(it)
    c = sorted(m["valid_codes"])
    META[it["id"]] = {"K": len(c), "range": (max(c) - min(c)) or 1}

SHORT = {"qwen/qwen3-max": "q3m", "deepseek/deepseek-v3.1-terminus": "ds31",
         "meta-llama/llama-4-maverick": "l4m", "moonshotai/kimi-k2-0905": "kk2"}
NAME = {"q3m": "Qwen3-Max", "ds31": "DeepSeek-V3.1", "l4m": "Llama-4-Mav", "kk2": "Kimi-K2"}
PROMPTS = ["P0", "P1", "P2"]
COST = {"q3m": 9.8e-4, "ds31": 3.2e-4, "l4m": 1.8e-4, "kk2": 7.2e-4}
CHEAP = {p: ROOT / f"outputs/gss_phase1_records_n200_qwen3-ma-deepseek-llama-4--kimi-k2-_seed42_{p}.json" for p in PROMPTS}

db1 = pd.read_excel(ROOT / "outputs/raw_tables.xlsx", sheet_name="Databook_1_Phase1A", skiprows=[1])
db2 = pd.read_excel(ROOT / "outputs/raw_tables.xlsx", sheet_name="Databook_2_Anchor", skiprows=[1])

# ---- collapse proxy (databook README definition) ---------------------------
def is_collapsed(row):
    if row["K"] >= 3:
        return bool(row["pred_top1_share"] > 0.95)
    return bool(row["pred_distinct_codes"] == 1)   # K==2

# ---- per-respondent records (JSON) for cell bootstrap ----------------------
def cell_records(model_slug, prompt):
    recs = json.loads(CHEAP[prompt].read_text())
    return [r for r in recs if r["model"] == model_slug]

def sample_nae_exact(s, cr):
    if s.get("skipped_missing_truth"):
        return None, None
    if s.get("parse_fail"):
        return 1.0, None
    ae, cm = s.get("abs_err"), s.get("cat_match")
    if ae is not None:
        return ae / cr, 1 if ae == 0 else 0
    if cm is not None:
        return (0.0 if cm == 1 else 1.0), 1 if cm == 1 else 0
    return None, None

def cell_bootstrap_ci(records, B=2000, seed=42):
    """Respondent bootstrap; statistic = item-macro mean (mean over 12 items of
    that item's pooled value). Returns (em_point, em_lo, em_hi, mae_point, mae_lo, mae_hi)."""
    # collect per-respondent per-item sample lists
    by_item_rid = {it: defaultdict(lambda: [[], []]) for it in PRIMARY}  # rid -> [exacts, naes]
    rids = set()
    for r in records:
        rid = r["respondent_id"]; rids.add(rid)
        for it in PRIMARY:
            cr = META[it]["range"]
            for s in r["per_item_scores"].get(it, []):
                nae, ex = sample_nae_exact(s, cr)
                if nae is None:
                    continue
                by_item_rid[it][rid][1].append(nae)
                if ex is not None:
                    by_item_rid[it][rid][0].append(ex)
    rids = np.array(sorted(rids))
    n = len(rids)

    def item_macro(sample_rids):
        em_items, mae_items = [], []
        for it in PRIMARY:
            exs, naes = [], []
            d = by_item_rid[it]
            for rid in sample_rids:
                cell = d.get(rid)
                if cell:
                    exs += cell[0]; naes += cell[1]
            if exs:
                em_items.append(mean(exs))
            if naes:
                mae_items.append(mean(naes))
        return (mean(em_items) if em_items else np.nan,
                mean(mae_items) if mae_items else np.nan)

    em_pt, mae_pt = item_macro(rids)
    rng = np.random.default_rng(seed)
    ems, maes = [], []
    for _ in range(B):
        samp = rng.choice(rids, size=n, replace=True)
        e, m = item_macro(samp)
        ems.append(e); maes.append(m)
    return (em_pt, float(np.percentile(ems, 2.5)), float(np.percentile(ems, 97.5)),
            mae_pt, float(np.percentile(maes, 2.5)), float(np.percentile(maes, 97.5)))

# ---- build cell table from databook (item-macro point) + bootstrap CI ------
cells = {}
for slug, short in SHORT.items():
    for p in PROMPTS:
        g = db1[(db1.model == short) & (db1.prompt == p)].copy()
        em_im = g["em"].mean()
        mae_im = g["mae_normalized"].mean()
        pf_im = g["parse_fail_rate"].mean()
        g["collapsed"] = g.apply(is_collapsed, axis=1)
        n_collapse = int(g["collapsed"].sum())
        collapse_items = g[g["collapsed"]]["item"].tolist()
        n_lift_pos = int((g["lift_maj"] > 0).sum())
        recs = cell_records(slug, p)
        em_pt, em_lo, em_hi, mae_pt, mae_lo, mae_hi = cell_bootstrap_ci(recs)
        cells[f"{short}|{p}"] = {
            "model": short, "name": NAME[short], "prompt": p,
            "em": round(em_im, 4), "em_ci": [round(em_lo, 4), round(em_hi, 4)],
            "mae_n": round(mae_im, 4), "mae_ci": [round(mae_lo, 4), round(mae_hi, 4)],
            "parse_fail": round(pf_im, 4),
            "n_collapse": n_collapse, "collapse_items": collapse_items,
            "n_lift_pos": n_lift_pos, "cost": COST[short],
            "_em_boot_pt": round(em_pt, 4), "_mae_boot_pt": round(mae_pt, 4),
        }

# ---- per-item (item-macro point estimates already in databook) -------------
# pooled over the 12 cheap cells (4 models x 3 prompts), n-weighted by n_eff
per_item = {}
for it in PRIMARY:
    g = db1[(db1.model != "rnd") & (db1.item == it)]
    w = g["n_eff"]
    per_item[it] = {
        "em": float((g["em"] * w).sum() / w.sum()),
        "mae_n": float((g["mae_normalized"] * w).sum() / w.sum()),
        "maj_em": float(g["maj_em"].iloc[0]),
        "lift_maj": float((g["lift_maj"] * w).sum() / w.sum()),
        "K": int(g["K"].iloc[0]), "tx": g["tx"].iloc[0],
        "n_eff": int(g["n_eff"].iloc[0]),
    }

# ---- collapse heatmap matrix (per model, averaged over prompts) ------------
collapse_mat = {}
for short in NAME:
    collapse_mat[short] = {}
    for it in PRIMARY:
        g = db1[(db1.model == short) & (db1.item == it)]
        collapse_mat[short][it] = {
            "top1": float(g["pred_top1_share"].mean()),
            "distinct": float(g["pred_distinct_codes"].mean()),
            "K": int(g["K"].iloc[0]),
        }

# ---- anchor (Databook_2) : item-macro EM/MAE per condition -----------------
anchor = {}
for lab in ["Anchor-B-R1ON", "Anchor-A-R1OFF"]:
    g = db2[db2.model == lab]
    w = g["n_eff"]
    anchor[lab] = {
        "em_macro": float(g["em"].mean()),
        "em_micro": float((g["em"] * w).sum() / w.sum()),
        "mae_macro": float(g["mae_normalized"].mean()),
        "per_item": {r["item"]: {"em": float(r["em"]), "mae": float(r["mae_normalized"])}
                     for _, r in g.iterrows()},
    }
# cheap @ P0 on the 84-row anchor sheet (first-100 cohort) for paired framing
for short in NAME:
    g = db2[db2.model == short]
    w = g["n_eff"]
    anchor[f"cheap_{short}_P0_100"] = {"em_micro": float((g["em"] * w).sum() / w.sum()),
                                       "mae_macro": float(g["mae_normalized"].mean())}

# ---- base-rate baseline MAE, item-macro (to match the item-macro cell MAEs) -
# Computed from the raw parquet truths so it is on the SAME averaging basis as
# the cells (each question weighted equally). The §7 selector's 0.2707 is the
# respondent-weighted version; for the report's item-macro table we use this.
from collections import Counter as _C  # noqa: E402
_pq = pd.read_parquet(ROOT / "outputs/phase1a_raw.parquet")
_pq = _pq[_pq.condition == "Full"].drop_duplicates(["item", "respondent_id"])
_base_item_mae = []
for _it, _g in _pq.groupby("item"):
    _rng = META[_it]["range"]
    _mode = _C(_g.true_code).most_common(1)[0][0]
    _base_item_mae.append(float((_g.true_code - _mode).abs().mean()) / _rng)
base_rate_mae_macro = mean(_base_item_mae)

out = {"cells": cells, "per_item": per_item, "collapse_mat": collapse_mat, "anchor": anchor,
       "majority_note": "databook maj_em per item; item-macro majority EM below",
       "majority_em_macro": float(db1[(db1.model == "q3m") & (db1.prompt == "P0")]["maj_em"].mean()),
       "base_rate_mae_macro": base_rate_mae_macro}
(ROOT / "report" / "databook_stats.json").write_text(json.dumps(out, indent=2))

# ============================ VERIFICATION ==================================
print("=" * 78)
print("CELL TABLE from databook (item-macro), ranked by EM   [verify vs pasted]")
print("=" * 78)
print(f"{'cell':9s} {'EM':>6s} {'EM 95% CI':>16s} {'MAE_n':>6s} {'MAE_n CI':>16s} {'collapse':>8s} {'lift+':>5s} {'$/call':>8s}")
for k in sorted(cells, key=lambda k: -cells[k]["em"]):
    c = cells[k]
    print(f"{c['model']+'·'+c['prompt']:9s} {c['em']:.3f} "
          f"[{c['em_ci'][0]:.3f},{c['em_ci'][1]:.3f}] {c['mae_n']:.3f} "
          f"[{c['mae_ci'][0]:.3f},{c['mae_ci'][1]:.3f}] "
          f"{c['n_collapse']:>5d}/12 {c['n_lift_pos']:>3d}/12 {c['cost']:.5f}"
          + (f"  collapse:{c['collapse_items']}" if c['collapse_items'] else ""))
print()
print("Pasted-claim checks:")
print(f"  ds31·P2 EM = {cells['ds31|P2']['em']:.3f} (claim 0.529)  MAE_n {cells['ds31|P2']['mae_n']:.3f} (claim 0.274)")
print(f"  kk2·P2  EM = {cells['kk2|P2']['em']:.3f} (claim 0.528)  MAE_n {cells['kk2|P2']['mae_n']:.3f} (claim 0.282)")
print(f"  q3m·P0  EM = {cells['q3m|P0']['em']:.3f} (claim 0.499)  MAE_n {cells['q3m|P0']['mae_n']:.3f} (claim 0.286)")
print(f"  kk2 collapse counts P0/P1/P2: "
      f"{cells['kk2|P0']['n_collapse']}/{cells['kk2|P1']['n_collapse']}/{cells['kk2|P2']['n_collapse']} (claim 0/0/0)")
print(f"  ds31·P2 collapse = {cells['ds31|P2']['n_collapse']} (claim 1)   "
      f"kk2·P2 lift+ = {cells['kk2|P2']['n_lift_pos']}/12 (claim 8)   "
      f"ds31·P1 lift+ = {cells['ds31|P1']['n_lift_pos']}/12 (claim 7)")
print(f"  l4m collapse P0/P1/P2: {cells['l4m|P0']['n_collapse']}/{cells['l4m|P1']['n_collapse']}/{cells['l4m|P2']['n_collapse']} (claim ~3)")
print()
print("Anchor (item-macro / micro):")
for lab in ["Anchor-A-R1OFF", "Anchor-B-R1ON"]:
    print(f"  {lab}: EM micro={anchor[lab]['em_micro']:.4f} macro={anchor[lab]['em_macro']:.4f} MAE_macro={anchor[lab]['mae_macro']:.4f}")
print(f"\nwrote report/databook_stats.json")
