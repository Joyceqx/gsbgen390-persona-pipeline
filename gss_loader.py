"""GSS loader — reads the GSS.dat fixed-width file using GSS.do specifications.

Outputs:
  - load_gss(year=2024) -> pandas DataFrame with year filter applied
  - get_variable_label(varname) -> long description (e.g., 'think of self as liberal or conservative')
  - get_value_label(varname, value) -> response label (e.g., 7 -> 'Extremely conservative')
  - is_missing(value) -> True if value is one of GSS's missing-value codes (-100..-40)

Internal:
  - parse_do_file(do_path) -> {variables: [(name, start, end)], var_labels: {}, value_label_sets: {}, var_to_label_set: {}}
"""
from __future__ import annotations
import re
from pathlib import Path
from functools import lru_cache
import pandas as pd

WORK = Path("/Users/joyce/Documents/GSBGEN390")
GSS_DIR = WORK / "data" / "gss"
# GSS DE splits the 973-variable extract into 3 batches; each batch has its own
# .dat + .do but the same row order (same respondents, different columns).
GSS_BATCHES_DIR = GSS_DIR / "390data1"
BATCH_DIRS = [GSS_BATCHES_DIR / "batch1", GSS_BATCHES_DIR / "batch2", GSS_BATCHES_DIR / "batch3"]

# GSS missing-value codes (all negative)
MISSING_CODES = {-100, -99, -98, -97, -96, -95, -90, -80, -70, -60, -50, -40}


# ---------------------------------------------------------------------------
# .do file parser
# ---------------------------------------------------------------------------

_INFIX_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s+(\d+)\s*-\s*(\d+)\s*$")
_LABEL_VAR_RE = re.compile(r'^label variable\s+([A-Za-z_][A-Za-z0-9_]*)\s+"(.*)"\s*;?\s*$', re.IGNORECASE)
_LABEL_DEFINE_RE = re.compile(r"^label define\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", re.IGNORECASE)
_LABEL_VALUE_LINE_RE = re.compile(r'^\s*(-?\d+)\s+"(.*)"\s*$')
_LABEL_VALUES_RE = re.compile(r"^label values\s+([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*;?\s*$", re.IGNORECASE)


def parse_do_file(do_path: Path) -> dict:
    """Parse the GSS.do file into structured spec.

    Returns:
        {
            'variables': [(name, start_col, end_col), ...],     # column ranges (1-indexed)
            'var_labels': {VARNAME: 'description', ...},
            'value_label_sets': {SET_NAME: {value: 'label', ...}, ...},
            'var_to_label_set': {VARNAME: SET_NAME, ...},
        }
    """
    text = do_path.read_text()
    lines = text.split("\n")

    variables = []
    var_labels = {}
    value_label_sets = {}
    var_to_label_set = {}

    in_infix = False
    in_label_define: str | None = None

    for line in lines:
        stripped = line.strip().rstrip(";").strip()

        # Infix block (variable column specs)
        if stripped.lower().startswith("infix"):
            in_infix = True
            continue
        if in_infix:
            if stripped.lower().startswith("using"):
                in_infix = False
                continue
            m = _INFIX_RE.match(stripped)
            if m:
                name, start, end = m.group(1), int(m.group(2)), int(m.group(3))
                variables.append((name, start, end))
            continue

        # Label variable
        m = _LABEL_VAR_RE.match(stripped)
        if m:
            var_labels[m.group(1)] = m.group(2)
            continue

        # Label define (multi-line block)
        m = _LABEL_DEFINE_RE.match(stripped)
        if m:
            in_label_define = m.group(1)
            value_label_sets[in_label_define] = {}
            continue
        if in_label_define is not None:
            m = _LABEL_VALUE_LINE_RE.match(stripped)
            if m:
                value_label_sets[in_label_define][int(m.group(1))] = m.group(2)
                continue
            # End of block when we hit a non-value line
            in_label_define = None

        # Label values (var -> labelset link)
        m = _LABEL_VALUES_RE.match(stripped)
        if m:
            var_to_label_set[m.group(1)] = m.group(2)
            continue

    return {
        "variables": variables,
        "var_labels": var_labels,
        "value_label_sets": value_label_sets,
        "var_to_label_set": var_to_label_set,
    }


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _spec() -> dict:
    """Combined spec across all batches. Label-set NAMES (e.g., 'GSP002X') collide
    across batches with different contents — to disambiguate we namespace each
    batch's label sets with a batch prefix (e.g., 'b0_GSP002X')."""
    merged = {"variables": [], "var_labels": {}, "value_label_sets": {}, "var_to_label_set": {}, "_per_batch": []}
    seen_vars = set()
    for batch_idx, d in enumerate(BATCH_DIRS):
        do_path = d / "GSS.do"
        if not do_path.exists():
            continue
        bspec = parse_do_file(do_path)
        merged["_per_batch"].append({"dir": d, "spec": bspec, "idx": batch_idx})
        prefix = f"b{batch_idx}_"
        # Variables (first-seen wins)
        for name, start, end in bspec["variables"]:
            if name.upper() not in seen_vars:
                merged["variables"].append((name, start, end))
                seen_vars.add(name.upper())
                # Carry over the var-label & label-set mapping for this var,
                # using THIS batch's namespaced label-set name
                if name.upper() in bspec["var_labels"]:
                    merged["var_labels"][name.upper()] = bspec["var_labels"][name.upper()]
                if name.upper() in bspec["var_to_label_set"]:
                    merged["var_to_label_set"][name.upper()] = prefix + bspec["var_to_label_set"][name.upper()]
        # Namespace this batch's label-set definitions
        for k, v in bspec["value_label_sets"].items():
            merged["value_label_sets"][prefix + k] = v
    return merged


def _read_batch(batch_dir: Path, spec: dict) -> pd.DataFrame:
    dat_path = batch_dir / "GSS.dat"
    variables = spec["variables"]
    colspecs = [(start - 1, end) for _, start, end in variables]
    names = [name.upper() for name, _, _ in variables]
    df = pd.read_fwf(dat_path, colspecs=colspecs, names=names, header=None,
                     dtype=str, na_values=[])
    for col in df.columns:
        df[col] = pd.to_numeric(df[col].str.strip(), errors="coerce")
    return df


@lru_cache(maxsize=1)
def _full_data() -> pd.DataFrame:
    """Read all 3 batch .dat files and concatenate horizontally.

    GSS Data Explorer splits a single year-filtered extract into multiple batches
    (each holding a subset of variables but the SAME respondents in the SAME row
    order). We verify alignment explicitly via repeated YEAR + ID_ columns before
    concatenating: row counts AND per-row YEAR + ID_ values must match across
    batches.

    The repeated identifier columns in GSS DE extracts are exactly `YEAR` and
    `ID_` (with trailing underscore). We keep them only from the first batch.
    """
    spec = _spec()
    batches_raw = []
    for entry in spec["_per_batch"]:
        df = _read_batch(entry["dir"], entry["spec"])
        batches_raw.append(df)
    if not batches_raw:
        raise RuntimeError(f"No batch data found under {GSS_BATCHES_DIR}")

    # Verify row counts match across batches.
    row_counts = [len(b) for b in batches_raw]
    if len(set(row_counts)) > 1:
        raise RuntimeError(
            f"Batch row counts differ — cannot horizontally concat. counts={row_counts}"
        )

    # Verify per-row alignment via repeated identifier columns YEAR and ID_.
    # If GSS DE ever changes the row ordering across batches this catches it.
    ref = batches_raw[0]
    for col in ("YEAR", "ID_"):
        if col not in ref.columns:
            continue  # no reference to align against
        for i, b in enumerate(batches_raw[1:], start=1):
            if col not in b.columns:
                continue
            same = (ref[col].fillna(-99999) == b[col].fillna(-99999)).all()
            if not same:
                first_diff = (ref[col].fillna(-99999) != b[col].fillna(-99999)).idxmax()
                raise RuntimeError(
                    f"Batch row alignment failed: batch 0 vs batch {i} disagree on {col!r} "
                    f"at row index {first_diff} "
                    f"(batch0={ref.loc[first_diff, col]}, batch{i}={b.loc[first_diff, col]}). "
                    f"Re-download or re-extract — this should not happen for a single GSS DE extract."
                )

    # Drop repeated identifier columns from all batches except the first.
    REPEATED_COLS = ["YEAR", "ID_"]
    batches = [batches_raw[0]]
    for b in batches_raw[1:]:
        batches.append(b.drop(columns=[c for c in REPEATED_COLS if c in b.columns], errors="ignore"))

    full = pd.concat(batches, axis=1)
    # Sanity: no duplicate column names after the drop.
    dup_cols = full.columns[full.columns.duplicated()].tolist()
    if dup_cols:
        raise RuntimeError(
            f"Loader produced duplicate columns after batch merge: {sorted(set(dup_cols))[:10]}. "
            f"Add the duplicate(s) to REPEATED_COLS in gss_loader.py."
        )
    return full


def load_gss(year: int | None = 2024, columns: list[str] | None = None) -> pd.DataFrame:
    """Load GSS data, optionally filtered to a single year and/or specific columns.

    Args:
        year: filter to a single GSS year. None = all years.
        columns: list of variable names to return. None = all.

    Returns:
        pandas DataFrame.
    """
    df = _full_data()
    if columns:
        keep = [c for c in columns if c in df.columns]
        missing = set(columns) - set(keep)
        if missing:
            print(f"WARN: requested but missing in data: {sorted(missing)}")
        df = df[keep + (["YEAR"] if "YEAR" in df.columns and "YEAR" not in keep else [])]
    if year is not None:
        if "YEAR" not in df.columns:
            raise ValueError("YEAR column not in data; cannot filter")
        df = df[df["YEAR"] == year]
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Label lookups
# ---------------------------------------------------------------------------

def get_variable_label(varname: str) -> str:
    """Long description of variable (e.g., 'think of self as liberal or conservative')."""
    return _spec()["var_labels"].get(varname.upper(), varname)


def get_value_label(varname: str, value) -> str:
    """Map numeric value to its label (e.g., POLVIEWS=7 -> 'Extremely conservative').
    Returns the raw value as string if no mapping exists or value is missing."""
    if value is None or pd.isna(value) or int(value) in MISSING_CODES:
        return None  # explicit missing
    spec = _spec()
    set_name = spec["var_to_label_set"].get(varname.upper())
    if not set_name:
        return str(value)
    label_set = spec["value_label_sets"].get(set_name, {})
    return label_set.get(int(value), str(value))


def is_missing(value) -> bool:
    if value is None or pd.isna(value):
        return True
    try:
        return int(value) in MISSING_CODES
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    print("=== parse .do files (combined across 3 batches) ===")
    spec = _spec()
    print(f"  variables: {len(spec['variables'])}")
    print(f"  variable labels: {len(spec['var_labels'])}")
    print(f"  value label sets: {len(spec['value_label_sets'])}")
    print(f"  variables with label sets: {len(spec['var_to_label_set'])}")

    print()
    print("=== check key variables present in spec ===")
    target = ["YEAR", "ID_", "POLVIEWS", "ABANY", "FECHLD", "FEPOL", "CAPPUN", "GUNLAW",
             "CONFINAN", "CONLEGIS", "ATTEND", "PRAY", "HAPPY", "SATFIN", "TRUST",
             "RACDIF1", "AGE", "SEX", "RACE", "EDUC", "INCOME", "REGION"]
    var_names = {n.upper() for n, _, _ in spec["variables"]}
    for v in target:
        present = "✓" if v in var_names else "✗"
        label = spec["var_labels"].get(v, "—")
        print(f"  {present} {v:<10s}  {label}")

    print()
    print("=== load year=2024 ===")
    df = load_gss(year=2024)
    print(f"  rows: {len(df)}")
    print(f"  cols: {len(df.columns)}")

    if len(df) > 0:
        print()
        print("=== sample row (first respondent, key vars only) ===")
        sample_cols = [c for c in ["YEAR", "ID_", "AGE", "SEX", "EDUC", "POLVIEWS", "ABANY", "HAPPY"]
                       if c in df.columns]
        if sample_cols:
            row = df.iloc[0][sample_cols]
            for col in sample_cols:
                v = row[col]
                lbl = get_value_label(col, v) if not is_missing(v) else "(missing)"
                print(f"  {col:<10s} = {str(v):<8s}  ({lbl})")

    print()
    print("=== check 2024 N ===")
    if "YEAR" in df.columns:
        full = _full_data()
        year_counts = full["YEAR"].value_counts().sort_index()
        recent = year_counts.tail(5)
        print(f"  recent year counts:\n{recent.to_string()}")
