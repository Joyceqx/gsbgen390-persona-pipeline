"""Build docs/data/*.json from the pipeline's CSV outputs.

Run this every time you re-run the pipeline. It is idempotent.
"""
import csv
import json
from pathlib import Path

WORK = Path("/Users/joyce/Documents/GSBGEN390")
DATA = WORK / "docs" / "data"
DATA.mkdir(parents=True, exist_ok=True)

# ---------- metrics_per_respondent.json ----------
def csv_to_jsonable_rows(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        rec = {}
        for k, v in r.items():
            if v in ("", None):
                rec[k] = None
                continue
            try:
                rec[k] = int(v)
            except ValueError:
                try:
                    rec[k] = float(v)
                except ValueError:
                    rec[k] = v
        out.append(rec)
    return out

# Normalization: site uses short codes (R1/R2 within an arm) and the longer
# Park-style condition names; pipeline uses long respondent IDs and short
# condition names.
RESPONDENT_REMAP = {
    "study1_interview_p1": "R1",
    "study1_interview_p2": "R2",
    "study2_survey_p1": "R1",  # within study2 context
}
CONDITION_REMAP = {
    "A_demographics": "A_demographic_only",
    "B_description": "B_persona_description",
    "C_interview": "C_interview",
    "D_survey": "D_survey_conditioned",
    "D_loo_drop_demographic": "D_loo_drop_demographic",
    "D_loo_drop_behavioral": "D_loo_drop_behavioral",
    "D_loo_drop_psychological": "D_loo_drop_psychological",
    "D_loo_drop_attitudinal": "D_loo_drop_attitudinal",
}

def normalize_for_site(rows):
    out = []
    for r in rows:
        rec = dict(r)
        if "respondent" in rec and rec["respondent"] in RESPONDENT_REMAP:
            rec["respondent"] = RESPONDENT_REMAP[rec["respondent"]]
        if "condition" in rec and rec["condition"] in CONDITION_REMAP:
            rec["condition"] = CONDITION_REMAP[rec["condition"]]
        out.append(rec)
    return out

per_resp_raw = csv_to_jsonable_rows(WORK / "metrics_per_respondent.csv")
per_resp = normalize_for_site(per_resp_raw)
(DATA / "metrics_per_respondent.json").write_text(json.dumps(per_resp, indent=2))
print(f"wrote {len(per_resp)} rows to docs/data/metrics_per_respondent.json")

# ---------- metrics_with_leakage_audit.json ----------
audit_raw = csv_to_jsonable_rows(WORK / "outputs" / "metrics_with_leakage_audit.csv")
audit = normalize_for_site(audit_raw)
(DATA / "metrics_with_leakage_audit.json").write_text(json.dumps(audit, indent=2))
print(f"wrote {len(audit)} rows to docs/data/metrics_with_leakage_audit.json")

# ---------- aggregate (per arm × condition) ----------
def aggregate(rows, fields=("likert_mae", "likert_within1_pct", "categorical_acc_pct",
                            "bfi_trait_rmse", "self_likert_mae", "self_cat_match_pct")):
    grouped = {}
    for r in rows:
        key = (r.get("arm"), r.get("condition"))
        grouped.setdefault(key, []).append(r)
    agg = []
    for (arm, cond), items in grouped.items():
        rec = {"arm": arm, "condition": cond, "n_respondents": len(items)}
        for f in fields:
            vals = [it[f] for it in items if isinstance(it.get(f), (int, float))]
            rec[f + "_mean"] = round(sum(vals) / len(vals), 3) if vals else None
        agg.append(rec)
    return agg

agg = aggregate(per_resp)  # already normalized
(DATA / "metrics_aggregate.json").write_text(json.dumps(agg, indent=2))
print(f"wrote {len(agg)} rows to docs/data/metrics_aggregate.json")

# ---------- truth answers (aggregate, no PII; participant ids are coded) ----------
truth_path = WORK / "eval_answers_extracted.csv"
if truth_path.exists():
    truth_rows_raw = csv_to_jsonable_rows(truth_path)
    # truth CSV has 'participant_id' column; normalize that too
    pid_remap = RESPONDENT_REMAP
    truth_rows = []
    for r in truth_rows_raw:
        rec = dict(r)
        if rec.get("participant_id") in pid_remap:
            # encode arm in the new id so app.js can group properly
            orig = rec["participant_id"]
            arm = "study2" if "study2" in orig else "study1"
            rec["participant_id"] = f"{pid_remap[orig]}__{arm}"
        truth_rows.append(rec)
    (DATA / "eval_answers_extracted.json").write_text(json.dumps(truth_rows, indent=2))
    print(f"wrote {len(truth_rows)} rows to docs/data/eval_answers_extracted.json")

print("\nAll site data built. Refresh the dashboard to see real numbers.")
