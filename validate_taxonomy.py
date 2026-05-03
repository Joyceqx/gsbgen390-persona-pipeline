"""Validate gss_feature_taxonomy.json:
  1. Every claimed variable is actually in the loaded data (no typos)
  2. Disjointness: no variable in both feature bin and eval set
  3. Coverage: report N respondents who would have at least k items in each bin
"""
import json
from pathlib import Path
import pandas as pd
from gss_loader import load_gss, _spec

WORK = Path("/Users/joyce/Documents/GSBGEN390")
TAX_PATH = WORK / "gss_feature_taxonomy.json"

tax = json.loads(TAX_PATH.read_text())
spec = _spec()
all_vars = {n.upper() for n, _, _ in spec["variables"]}

primary_eval = {it["id"] for it in tax["primary_eval"]["items"]}
sensitivity_eval = set(tax["sensitivity_eval"]["items"])
bins = tax["feature_bins"]

print("=== 1. Verify each claimed variable exists in the loaded data ===")
issues = []
for label, items in [
    ("primary_eval", primary_eval),
    ("sensitivity_eval", sensitivity_eval),
    ("feature_bin: demographic", set(bins["demographic"])),
    ("feature_bin: behavioral",  set(bins["behavioral"])),
    ("feature_bin: psychological", set(bins["psychological"])),
    ("feature_bin: attitudinal", set(bins["attitudinal"])),
]:
    missing = sorted(items - all_vars)
    if missing:
        issues.append(f"  {label}: NOT IN DATA: {missing}")
        print(f"  {label}: {len(items)} claimed, {len(missing)} missing")
    else:
        print(f"  ✓ {label}: all {len(items)} variables present")

if issues:
    print("\nDETAIL:")
    for i in issues:
        print(i)

print()
print("=== 2. Disjointness check ===")
# PRIMARY analysis effective features = declared bin lists MINUS primary_eval ONLY
# (sensitivity_eval items CAN be in features for the primary LOO; the sensitivity
# pass handles per-item leakage separately)
effective_features = {}
for bin_name, items in bins.items():
    if bin_name.startswith("_"):
        continue
    declared = set(items)
    in_data = declared & all_vars
    effective = in_data - primary_eval  # primary-pass features
    primary_eval_shadow = declared & primary_eval
    not_in_data = declared - all_vars
    effective_features[bin_name] = effective
    print(f"  {bin_name}: declared {len(declared)}, in_data {len(in_data)}, "
          f"primary_eval_shadow {len(primary_eval_shadow)}, not_in_data {len(not_in_data)}, "
          f"effective features {len(effective)}")

# Across-bin disjointness within features
all_seen = set()
overlap = []
for bin_name, items in effective_features.items():
    inter = items & all_seen
    if inter:
        overlap.append(f"  {bin_name} overlaps with prior bins on: {sorted(inter)}")
    all_seen |= items
if overlap:
    print("\n!! BIN OVERLAPS:")
    for o in overlap:
        print(o)
else:
    print(f"\n  ✓ Feature bins are mutually disjoint ({len(all_seen)} total feature variables)")

print()
print("=== 3. Coverage at GSS 2024 (N=3309) ===")
df = load_gss(year=2024)
MISSING_CODES = {-100, -99, -98, -97, -96, -95, -90, -80, -70, -60, -50, -40}
def n_answered(varlist):
    """For each respondent, count how many vars they actually answered (non-missing)."""
    sub = df[[v for v in varlist if v in df.columns]]
    # Treat MISSING_CODES as missing
    is_real = sub.applymap(lambda x: not (pd.isna(x) or int(x) in MISSING_CODES if pd.notna(x) else True))
    return is_real.sum(axis=1)

for label, varlist in [
    ("primary_eval (12 items)", list(primary_eval)),
    ("demographic", list(effective_features["demographic"])),
    ("behavioral", list(effective_features["behavioral"])),
    ("psychological", list(effective_features["psychological"])),
    ("attitudinal", list(effective_features["attitudinal"])),
]:
    n_real = n_answered(varlist)
    print(f"  {label}: ")
    print(f"    median answered: {int(n_real.median())} / {len(varlist)}")
    print(f"    respondents with >=1: {int((n_real >= 1).sum())} / {len(df)}")
    print(f"    respondents with >=50% of items: {int((n_real >= len(varlist)/2).sum())} / {len(df)}")
