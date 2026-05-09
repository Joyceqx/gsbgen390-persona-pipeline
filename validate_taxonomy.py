"""Validate gss_feature_taxonomy.json + gss_loader.py against the loaded GSS data.

Fails LOUDLY (raises AssertionError) on any check that violates the locked design:
  1. Loader produces unique columns.
  2. GSS 2024 cross-section loads with N=3,309 (the documented count).
  3. primary_eval ∩ declared feature bins == ∅ (no direct leakage in primary LOO).
  4. Every taxonomy variable (primary_eval, sensitivity_eval, all 4 feature bins)
     is present in the loaded data.
  5. Per-respondent coverage ≥1 item for every primary_eval item.
  6. All observed negative values in taxonomy-listed variables are members of
     gss_loader.MISSING_CODES (i.e., we know how to interpret every missing-code
     value the data actually contains).
  7. Sensitivity per-item exclusion rule is auditable: prints a small report
     listing each sensitivity_eval item that is also in a feature bin (those are
     the ones that need per-item exclusion downstream in gss_pipeline.py).

Prints a clean PASS / FAIL summary at the end.
"""
import json
from pathlib import Path
import pandas as pd
from gss_loader import load_gss, _spec, MISSING_CODES, _full_data

WORK = Path("/Users/joyce/Documents/GSBGEN390")
TAX_PATH = WORK / "gss_feature_taxonomy.json"

EXPECTED_N_2024 = 3309
EXPECTED_FULL_COLS = 973  # 973 unique GSS variables after merging 3 batches and dropping duplicate ID_/YEAR

tax = json.loads(TAX_PATH.read_text())
spec = _spec()
all_vars = {n.upper() for n, _, _ in spec["variables"]}

primary_eval = {it["id"] for it in tax["primary_eval"]["items"]}
sensitivity_eval = set(tax["sensitivity_eval"]["items"])
bins = tax["feature_bins"]
declared_features = {
    bin_name: set(items)
    for bin_name, items in bins.items()
    if not bin_name.startswith("_")
}
all_declared_features = set().union(*declared_features.values())

failures = []
def fail(label, msg):
    failures.append(f"  ✗ {label}: {msg}")
    print(f"  ✗ {label}: {msg}")
def ok(label, msg=""):
    print(f"  ✓ {label}{(': ' + msg) if msg else ''}")

# ---------------------------------------------------------------------------
# CHECK 1: loader produces unique columns
# ---------------------------------------------------------------------------
print("=== 1. Loader produces unique column names ===")
full = _full_data()
dup_cols = full.columns[full.columns.duplicated()].tolist()
if dup_cols:
    fail("unique columns", f"duplicates after merge: {sorted(set(dup_cols))[:10]}")
else:
    ok("unique columns", f"all {len(full.columns)} columns unique")

# ---------------------------------------------------------------------------
# CHECK 2: full data has expected unique-column structure (973)
# ---------------------------------------------------------------------------
print("\n=== 2. Full-data shape matches 973 unique variables ===")
if len(full.columns) == EXPECTED_FULL_COLS:
    ok("full shape", f"{len(full)} rows × {len(full.columns)} cols")
else:
    fail("full shape", f"expected 973 cols, got {len(full.columns)} (rows={len(full)})")

# ---------------------------------------------------------------------------
# CHECK 3: GSS 2024 loads with N=3,309
# ---------------------------------------------------------------------------
print("\n=== 3. GSS 2024 loads with N=3,309 ===")
df = load_gss(year=2024)
if len(df) == EXPECTED_N_2024:
    ok("2024 N", f"{len(df)} respondents")
else:
    fail("2024 N", f"expected {EXPECTED_N_2024}, got {len(df)}")

# ---------------------------------------------------------------------------
# CHECK 4: primary_eval ∩ declared feature bins == ∅
# ---------------------------------------------------------------------------
print("\n=== 4. primary_eval is disjoint from declared feature bins ===")
overlap = primary_eval & all_declared_features
if not overlap:
    ok("primary_eval ⊥ features", f"clean (12 primary_eval × {len(all_declared_features)} features)")
else:
    fail("primary_eval ⊥ features", f"OVERLAP: {sorted(overlap)} appear in BOTH primary_eval and a feature bin. "
                                    f"Move them out of feature bin(s) or out of primary_eval.")

# Also verify mutual disjointness of feature bins
print("\n=== 4b. Feature bins are mutually disjoint ===")
seen = set()
overlap_bins = []
for bin_name, items in declared_features.items():
    inter = items & seen
    if inter:
        overlap_bins.append((bin_name, inter))
    seen |= items
if overlap_bins:
    for b, inter in overlap_bins:
        fail("feature-bin mutual disjointness", f"{b} overlaps prior bins on {sorted(inter)}")
else:
    ok("feature-bin mutual disjointness", f"{len(seen)} unique features across 4 bins")

# ---------------------------------------------------------------------------
# CHECK 5: Every taxonomy variable exists in the loaded data
# ---------------------------------------------------------------------------
print("\n=== 5. Every taxonomy variable exists in loaded data ===")
for label, items in [
    ("primary_eval", primary_eval),
    ("sensitivity_eval", sensitivity_eval),
    *[(f"feature_bins.{name}", items) for name, items in declared_features.items()],
]:
    missing = sorted(items - all_vars)
    if missing:
        fail(label, f"missing from data: {missing}")
    else:
        ok(label, f"all {len(items)} present")

# ---------------------------------------------------------------------------
# CHECK 6: Per-item coverage for all 12 primary eval items
# ---------------------------------------------------------------------------
print("\n=== 6. Per-item coverage for primary_eval items in 2024 ===")
def n_real(varname):
    if varname not in df.columns:
        return 0
    s = df[varname]
    is_real = s.notna() & ~s.isin(MISSING_CODES)
    return int(is_real.sum())

low_coverage = []
for it in tax["primary_eval"]["items"]:
    n = n_real(it["id"])
    pct = 100 * n / len(df) if len(df) else 0
    if n == 0:
        fail(f"primary_eval/{it['id']}", "ZERO respondents answered this item")
    elif pct < 10:
        low_coverage.append((it["id"], n, pct))
        fail(f"primary_eval/{it['id']}", f"low coverage: only {n}/{len(df)} ({pct:.1f}%) answered")
    else:
        print(f"  {it['id']:<12s}  n_answered = {n:5d} / {len(df)}  ({pct:.0f}%)")
if not low_coverage:
    ok("primary_eval coverage", "all 12 items have ≥10% respondent coverage")

# ---------------------------------------------------------------------------
# CHECK 7: All observed negative values in taxonomy variables are in MISSING_CODES
# ---------------------------------------------------------------------------
print("\n=== 7. All negative values in taxonomy variables are accounted for in MISSING_CODES ===")
all_taxonomy_vars = primary_eval | sensitivity_eval | all_declared_features
unknown_codes = {}
for v in sorted(all_taxonomy_vars):
    if v not in df.columns:
        continue
    col = df[v]
    neg_observed = set(col[col < 0].dropna().astype(int).unique())
    unknown = neg_observed - MISSING_CODES
    if unknown:
        unknown_codes[v] = unknown
if unknown_codes:
    fail("missing-codes coverage",
         f"{len(unknown_codes)} variables have negative values NOT in MISSING_CODES: " +
         "; ".join(f"{v}={sorted(c)}" for v, c in list(unknown_codes.items())[:5]) +
         ("; ..." if len(unknown_codes) > 5 else ""))
else:
    ok("missing-codes coverage", f"all observed negative values in taxonomy vars are in MISSING_CODES "
                                  f"(checked {len(all_taxonomy_vars)} vars)")

# ---------------------------------------------------------------------------
# CHECK 7b: Sensitivity overrides match observed truth codes (Codex 2026-05-06)
# Loud failure if any sensitivity item's override valid_codes don't cover the
# observed substantive codes in the loaded data — would otherwise silently
# produce prompts on one scale and score on another.
# ---------------------------------------------------------------------------
print("\n=== 7b. Sensitivity overrides match observed truth codes ===")
try:
    from gss_driver import SENSITIVITY_FORMAT_OVERRIDES
except ImportError:
    fail("sensitivity overrides", "could not import gss_driver.SENSITIVITY_FORMAT_OVERRIDES")
    SENSITIVITY_FORMAT_OVERRIDES = {}

mismatches: list[str] = []
for vname, ovr in SENSITIVITY_FORMAT_OVERRIDES.items():
    if vname not in df.columns:
        continue
    declared = set(ovr["valid_codes"])
    observed = set(df[vname].dropna().astype(int).tolist()) - MISSING_CODES
    # Allow overrides to expand beyond observed (e.g., sparse 1-7 even if data only has 1-5)
    # but require: every observed substantive code must be covered by override valid_codes.
    uncovered = observed - declared
    if uncovered:
        mismatches.append(
            f"  {vname}: override valid_codes={sorted(declared)} but observed "
            f"substantive codes {sorted(observed)} contains uncovered {sorted(uncovered)}"
        )

if mismatches:
    fail("sensitivity overrides", "valid_codes don't cover observed truth codes")
    for m in mismatches:
        print(m)
else:
    ok("sensitivity overrides", f"all {len(SENSITIVITY_FORMAT_OVERRIDES)} overrides cover observed truth codes")

# ---------------------------------------------------------------------------
# CHECK 8 (REPORTING): sensitivity per-item exclusion auditability
# ---------------------------------------------------------------------------
print("\n=== 8. Sensitivity per-item exclusion plan (downstream gss_pipeline.py contract) ===")
sens_in_features = sensitivity_eval & all_declared_features
print(f"  {len(sens_in_features)} of {len(sensitivity_eval)} sensitivity_eval items also live in feature bins.")
print(f"  When predicting any of these, gss_pipeline.py MUST exclude that specific item from the prompt.")
print(f"  Sample: {sorted(sens_in_features)[:8]}{'...' if len(sens_in_features) > 8 else ''}")

# ---------------------------------------------------------------------------
# CHECK 9: Coverage at GSS 2024 — feature bins (informational)
# ---------------------------------------------------------------------------
print("\n=== 9. Per-respondent coverage by feature bin (informational) ===")
def coverage_summary(varlist, label):
    cols = [v for v in varlist if v in df.columns]
    if not cols:
        print(f"  {label}: no variables in data")
        return
    sub = df[cols]
    is_real = sub.notna() & ~sub.isin(MISSING_CODES)
    n_real_per_resp = is_real.sum(axis=1)
    print(f"  {label}: median answered {int(n_real_per_resp.median())}/{len(varlist)}, "
          f">=1: {(n_real_per_resp>=1).sum()}/{len(df)}, "
          f">=50%: {(n_real_per_resp >= len(varlist)/2).sum()}/{len(df)}")

coverage_summary(list(primary_eval), "primary_eval (12)")
for bin_name, items in declared_features.items():
    coverage_summary(list(items), f"feature_bin.{bin_name}")

# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if failures:
    print(f"FAIL — {len(failures)} check(s) violated:")
    for f in failures:
        print(f)
    raise SystemExit(1)
else:
    print("✓ ALL VALIDATION CHECKS PASSED")
