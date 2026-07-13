"""Analyze the no-persona baseline vs the base-rate guess vs the selected cell.

Reads report/no_persona_samples.json (Kimi-K2 × P2 prior, M draws per item),
the panel truths for the 200 cohort, and the databook's kk2×P2 per-item
exact-match. Produces, per question and overall:

  base_rate_em    : accuracy of "predict the population's most common answer"
  no_persona_em   : accuracy of "predict the MODEL's most common no-persona answer"
                    (the fair, equal-information floor)
  cell_em         : Kimi-K2 × P2 with the full persona (databook)
  lift_over_noP   : (cell_em - no_persona_em) / (1 - no_persona_em)

Writes report/no_persona_stats.json and prints a table.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
from statistics import mean

import pandas as pd

ROOT = Path("/Users/joyce/Developer/gsbgen390")
sys.path.insert(0, str(ROOT / "src"))
from gss_pipeline import load_taxonomy  # noqa: E402

SAMP = ROOT / "report" / "no_persona_samples.json"
P2_JSON = ROOT / "outputs/gss_phase1_records_n200_qwen3-ma-deepseek-llama-4--kimi-k2-_seed42_P2.json"
OUT = ROOT / "report" / "no_persona_stats.json"

tx = load_taxonomy()
PRIMARY = [it["id"] for it in tx["primary_eval"]["items"]]

samp = json.loads(SAMP.read_text())["items"]

# truths per (item, rid) on the full 200 cohort, from the kk2 P2 records
recs = [r for r in json.loads(P2_JSON.read_text()) if r["model"] == "moonshotai/kimi-k2-0905"]
truths = {it: [] for it in PRIMARY}
for r in recs:
    for it in PRIMARY:
        for s in r["per_item_scores"].get(it, []):
            if s.get("skipped_missing_truth"):
                continue
            t = s.get("truth")
            if t is not None:
                truths[it].append(t)
                break   # one truth per respondent

# kk2 x P2 per-item exact-match from the databook
db1 = pd.read_excel(ROOT / "outputs/raw_tables.xlsx", sheet_name="Databook_1_Phase1A", skiprows=[1])
cell_em = {it: float(db1[(db1.model == "kk2") & (db1.prompt == "P2") & (db1.item == it)]["em"].iloc[0])
           for it in PRIMARY}

rows = {}
for it in PRIMARY:
    tr = truths[it]
    if not tr:
        continue
    n = len(tr)
    tcount = Counter(tr)
    base_mode = tcount.most_common(1)[0][0]
    base_em = tcount[base_mode] / n

    prior = {int(k): v for k, v in samp[it]["prior_dist"].items()}
    M = sum(prior.values())
    prior_mode = samp[it]["prior_mode"]
    # no-persona EM, mode-based: predict the model's prior mode for everyone
    nop_em_mode = (tcount.get(prior_mode, 0) / n) if prior_mode is not None else 0.0
    # no-persona EM, expected: P(a random prior draw == a random respondent's truth)
    nop_em_exp = sum((tcount.get(c, 0) / n) * (cnt / M) for c, cnt in prior.items())

    def lift(em, base):
        return (em - base) / (1 - base) if base < 1 else None

    rows[it] = {
        "n": n,
        "base_rate_em": round(base_em, 4), "base_mode": base_mode,
        "no_persona_em_mode": round(nop_em_mode, 4),
        "no_persona_em_expected": round(nop_em_exp, 4),
        "prior_mode": prior_mode, "prior_dist": prior,
        "prior_distinct": len(prior), "K": len(samp[it]["valid_codes"]),
        "cell_em": round(cell_em[it], 4),
        "lift_over_base": round(lift(cell_em[it], base_em), 4),
        "lift_over_no_persona": round(lift(cell_em[it], nop_em_mode), 4) if prior_mode is not None else None,
    }

# overall, question-macro (each question weighted equally)
def macro(key):
    return round(mean(rows[it][key] for it in rows), 4)

overall = {
    "base_rate_em": macro("base_rate_em"),
    "no_persona_em_mode": macro("no_persona_em_mode"),
    "no_persona_em_expected": macro("no_persona_em_expected"),
    "cell_em": macro("cell_em"),
    "n_questions_cell_beats_no_persona": sum(1 for it in rows if rows[it]["cell_em"] > rows[it]["no_persona_em_mode"]),
    "n_questions_cell_beats_base": sum(1 for it in rows if rows[it]["cell_em"] > rows[it]["base_rate_em"]),
    "n_collapsed_prior": sum(1 for it in rows if rows[it]["K"] >= 3 and max(rows[it]["prior_dist"].values()) / sum(rows[it]["prior_dist"].values()) > 0.95),
}
OUT.write_text(json.dumps({"overall": overall, "per_item": rows,
                           "model": samp and "moonshotai/kimi-k2-0905", "M": sum(next(iter(samp.values()))["prior_dist"].values()) if False else None}, indent=2))

print(f"{'item':9s} {'base':>6s} {'noP(mode)':>9s} {'noP(exp)':>9s} {'cell':>6s} {'lift/base':>9s} {'lift/noP':>9s}  prior_mode")
for it in PRIMARY:
    if it not in rows:
        continue
    r = rows[it]
    print(f"{it:9s} {r['base_rate_em']:.3f} {r['no_persona_em_mode']:>9.3f} {r['no_persona_em_expected']:>9.3f} "
          f"{r['cell_em']:.3f} {str(r['lift_over_base']):>9s} {str(r['lift_over_no_persona']):>9s}  "
          f"mode={r['prior_mode']} dist={r['prior_dist']}")
print()
print("OVERALL (question-macro):", json.dumps(overall, indent=2))
print(f"\nwrote {OUT}")
