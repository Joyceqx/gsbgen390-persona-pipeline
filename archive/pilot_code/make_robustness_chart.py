"""Generate chart_robustness.png — Likert MAE per condition, three bars
(full / strict-clean / broad-clean) showing how leakage filtering affects results."""
import csv
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

WORK = Path("/Users/joyce/Developer/gsbgen390")
OUTPUTS = WORK / "outputs"

# Load both metric tables
audit_rows = []
with open(OUTPUTS / "metrics_with_leakage_audit.csv") as f:
    for row in csv.DictReader(f):
        audit_rows.append(row)

# Reshape: condition_label -> {filter: mae}
study1 = {}  # for P1+P2
study2 = {}
for row in audit_rows:
    arm, resp, cond, filt = row["arm"], row["respondent"], row["condition"], row["filter"]
    if row["likert_mae"] in (None, ""):
        continue
    mae = float(row["likert_mae"])
    label = f"{resp.split('_')[-1].upper()}/{cond}"  # e.g. "P1/A_demographics"
    bucket = study1 if arm == "study1" else study2
    bucket.setdefault(label, {})[filt] = mae

def plot_panel(ax, data, title):
    labels = list(data.keys())
    filters = ["full_eval", "strict_clean", "broad_clean"]
    pretty = {"full_eval": "Full (15)", "strict_clean": "Strict-clean", "broad_clean": "Broad-clean"}
    colors = {"full_eval": "#4a7ab5", "strict_clean": "#7fb069", "broad_clean": "#e07a5f"}

    x = np.arange(len(labels))
    w = 0.27

    for i, f in enumerate(filters):
        vals = [data[l].get(f, 0) for l in labels]
        ax.bar(x + (i - 1) * w, vals, w, label=pretty[f], color=colors[f])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Likert MAE (lower = closer to truth)")
    ax.set_title(title)
    ax.axhline(0, color="black", lw=0.5)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.5)

fig, axes = plt.subplots(2, 1, figsize=(13, 9))
plot_panel(axes[0], study1, "Study 1 (interview arm) — Likert MAE under three leakage-filtering views")
plot_panel(axes[1], study2, "Study 2 (survey arm) — Likert MAE under three views (Study 2 has 0 STRONG-leak items)")

fig.suptitle("Leakage-robustness audit: does Condition C's win survive removal of leak-suspect eval items?",
             y=1.00, fontsize=12, fontweight="bold")
plt.tight_layout()
out = OUTPUTS / "chart_robustness.png"
plt.savefig(out, dpi=140, bbox_inches="tight")
print(f"saved {out.name}")
