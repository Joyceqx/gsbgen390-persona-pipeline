"""Re-score persona answers with three views:
  - full_eval: all 15 items (existing metrics_per_respondent.csv)
  - strict_clean: drop STRONG-leaked items per respondent
  - broad_clean: drop STRONG + SOFT-leaked items per respondent

Inputs:
  persona_answers_full.json  — produced by run_notebook_local.py end-of-run
  eval_answers_extracted.csv — audited truth answers (gold)
  leakage_audit.json         — per-respondent item tags

Output:
  metrics_with_leakage_audit.csv — per (respondent, condition, filter) MAE breakdown
"""
import csv
import json
import re
from pathlib import Path
from statistics import mean

WORK = Path("/Users/joyce/Documents/GSBGEN390")
OUTPUTS = WORK / "outputs"
OUTPUTS.mkdir(exist_ok=True)

# ----- Load inputs -----
# persona_answers_full.json is a pipeline-output artifact (kept gitignored under outputs/).
# leakage_audit.json is a manual-tagging input (gitignored at root because it has quotes).
results = json.loads((OUTPUTS / "persona_answers_full.json").read_text())
audit = json.loads((WORK / "leakage_audit.json").read_text())["per_respondent"]

truth = {}
with open(WORK / "eval_answers_extracted.csv") as f:
    for row in csv.DictReader(f):
        truth[row["participant_id"]] = {k: v for k, v in row.items() if k != "participant_id" and v}

# Item answer formats (mirror notebook's EVAL_ITEMS — only the bits we need to score)
LIKERT5 = ["bfi_e_r","bfi_a","bfi_c_r","bfi_n_r","bfi_o_r","bfi_e","bfi_a_r","bfi_c","bfi_n","bfi_o","loyal"]
LIKERT7 = ["polviews"]
CATEGORICAL = ["happy", "trust", "satjob"]
ALL_ITEMS = LIKERT5 + LIKERT7 + CATEGORICAL

NUM_WORDS = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7}

def parse_likert(s, lo=1, hi=7):
    if s is None: return None
    s = str(s).lower()
    for n in re.findall(r"-?\d+", s):
        v = int(n)
        if lo <= v <= hi:
            return v
    for w, v in NUM_WORDS.items():
        if w in s and lo <= v <= hi:
            return v
    return None

def cat_match(predicted, t):
    if not predicted or not t: return False
    p, t_norm = predicted.lower().strip(), t.lower().strip()
    if t_norm in p or p in t_norm: return True
    # tolerate truncations / paraphrases of the standard option strings
    fragments = [f.strip() for f in re.split(r"[,/]", t_norm) if f.strip()]
    return any(f in p for f in fragments)

def score_subset(persona_answers, truth_row, item_ids):
    likert_errs, cat_correct, cat_total = [], 0, 0
    for iid in item_ids:
        p = persona_answers.get(iid)
        t = truth_row.get(iid)
        if p is None or t is None or t == "":
            continue
        if iid in LIKERT5:
            pv, tv = parse_likert(p, 1, 5), parse_likert(t, 1, 5)
            if pv is not None and tv is not None:
                likert_errs.append(abs(pv - tv))
        elif iid in LIKERT7:
            pv, tv = parse_likert(p, 1, 7), parse_likert(t, 1, 7)
            if pv is not None and tv is not None:
                likert_errs.append(abs(pv - tv))
        elif iid in CATEGORICAL:
            cat_total += 1
            if cat_match(p, t):
                cat_correct += 1
    return {
        "n_likert": len(likert_errs),
        "likert_mae": round(mean(likert_errs), 3) if likert_errs else None,
        "likert_within1_pct": round(100 * sum(1 for e in likert_errs if e <= 1) / len(likert_errs), 1) if likert_errs else None,
        "n_cat": cat_total,
        "cat_acc_pct": round(100 * cat_correct / cat_total, 1) if cat_total else None,
    }

# ----- Score each (respondent, condition) under each filter -----
filters = ["full_eval", "strict_clean", "broad_clean"]
rows = []
for r in results:
    arm, resp, cond = r["arm"], r["respondent"], r["condition"]
    persona = r["primary"]
    truth_row = truth.get(resp, {})
    if not truth_row:
        print(f"WARN: no truth for {resp}")
        continue
    a = audit.get(resp, {})
    strong = set(a.get("STRONG", []))
    soft = set(a.get("SOFT", []))

    item_sets = {
        "full_eval": ALL_ITEMS,
        "strict_clean": [i for i in ALL_ITEMS if i not in strong],
        "broad_clean":  [i for i in ALL_ITEMS if i not in (strong | soft)],
    }
    for f in filters:
        m = score_subset(persona, truth_row, item_sets[f])
        rows.append({
            "arm": arm, "respondent": resp, "condition": cond, "filter": f,
            "n_likert_used": m["n_likert"], "likert_mae": m["likert_mae"],
            "likert_within1_pct": m["likert_within1_pct"],
            "n_cat_used": m["n_cat"], "cat_acc_pct": m["cat_acc_pct"],
            "n_strong_dropped": len(strong) if f != "full_eval" else 0,
            "n_soft_dropped": len(soft) if f == "broad_clean" else 0,
        })

# ----- Write CSV -----
out_path = OUTPUTS / "metrics_with_leakage_audit.csv"
fieldnames = ["arm","respondent","condition","filter","n_likert_used","likert_mae",
              "likert_within1_pct","n_cat_used","cat_acc_pct","n_strong_dropped","n_soft_dropped"]
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)
print(f"Wrote {len(rows)} rows to {out_path.name}")

# ----- Print compact comparison table -----
import pandas as pd
df = pd.DataFrame(rows)
print("\n=== Likert MAE by condition × filter ===")
piv = df.pivot_table(
    index=["arm","respondent","condition"],
    columns="filter",
    values="likert_mae",
    aggfunc="first",
)[["full_eval","strict_clean","broad_clean"]]
print(piv.to_string())

print("\n=== n_likert items used (smaller = more dropped) ===")
piv_n = df.pivot_table(
    index=["arm","respondent","condition"],
    columns="filter",
    values="n_likert_used",
    aggfunc="first",
)[["full_eval","strict_clean","broad_clean"]]
print(piv_n.to_string())
