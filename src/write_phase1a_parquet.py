"""Flatten Phase 1A JSON records into the §6.2 long-format parquet.

The driver writes one JSON file per prompt (`gss_phase1_records_n200_panel_seed42_P0.json`,
_P1.json, _P2.json) with a record per (respondent_id, condition, model, prompt_id).
Each record nests `per_item_scores: {item_id: [{persona_code, truth, parse_fail,
abs_err, cat_match, ...}, ...]}` — the inner list is `n_samples` long.

This module turns that nested structure into one row per
(respondent_id, model, prompt, condition, item, sample_position) tuple,
adds the post-hoc Random column (§5.4 — uniform pick per (respondent_id, prompt),
seed=42 hash), normalizes condition / model labels to the §6.2 vocabulary,
and writes `outputs/phase1a_raw.parquet`.

Schema follows RESEARCH_DESIGN.md §6.2 exactly. Token / cost / per-call timestamp
columns are reserved as nullable — `call_llm` does not yet return usage stats,
so they are written as NULL. A future `call_llm` extension can backfill without
schema migration.

Run:
    python3 src/write_phase1a_parquet.py                      # auto-discover P0/P1/P2 JSONs
    python3 src/write_phase1a_parquet.py --self-test          # synthetic 2-respondent test
    python3 src/write_phase1a_parquet.py --json-glob "..."    # custom input glob
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

WORK = Path("/Users/joyce/Developer/gsbgen390")
OUTPUTS = WORK / "outputs"
DEFAULT_OUTPUT = OUTPUTS / "phase1a_raw.parquet"

# §6.2 condition vocabulary. Driver writes the internal names on the left;
# we normalize to the spec names on the right before parquet emit.
CONDITION_LABEL = {
    "full": "Full",
    "loo_drop_demographic": "drop_demographic",
    "loo_drop_behavioral": "drop_behavioral",
    "loo_drop_psychological": "drop_psychological",
    "loo_drop_attitudinal": "drop_attitudinal",
}

# Cheap-panel real models (deterministic order; matters for the seeded random pick).
PANEL_MODELS = [
    "qwen/qwen-2.5-72b-instruct",
    "deepseek/deepseek-chat",
    "meta-llama/llama-3.3-70b-instruct",
    "moonshotai/kimi-k2",
]

RANDOM_LABEL = "Random"
RANDOM_PICK_SEED = 42  # seeded picker for §5.4 post-hoc random column

# Column order = §6.2 schema exactly. dtypes documented for parquet stability.
PARQUET_COLUMNS = [
    "respondent_id",       # int32
    "model",               # str (slug or "Random")
    "prompt",              # str (P0/P1/P2)
    "condition",           # str (Full / drop_*)
    "item",                # str (POLVIEWS / ...)
    "true_code",           # int32
    "pred_code",           # nullable int32
    "parse_ok",            # bool
    "abs_err",             # nullable int32
    "sample_position",     # int32 (1-indexed)
    "timestamp",           # str (ISO 8601 UTC; run-write time as proxy until call_llm exposes it)
    "cost_usd",            # nullable float64 (call_llm TODO)
    "tokens_in",           # nullable int32 (call_llm TODO)
    "tokens_out",          # nullable int32 (call_llm TODO)
]


# ---------------------------------------------------------------------------
# Flattening
# ---------------------------------------------------------------------------

def _row_from_sample(
    rid: int,
    model: str,
    prompt_id: str,
    condition_internal: str,
    item: str,
    sample_position: int,
    sample: dict[str, Any],
    write_timestamp: str,
) -> dict[str, Any] | None:
    """Convert one score_item() output dict into one parquet row.
    Returns None if the row should be skipped (ballot rotation: no truth)."""
    if sample.get("skipped_missing_truth"):
        return None
    true_code = sample.get("truth")
    if true_code is None:
        return None

    pred_code = sample.get("persona_code")
    parse_ok = not sample.get("parse_fail", True)
    # §6.2: "abs_err |pred − true| on Likert; 0/1 on binary; NULL if parse_ok=false"
    # score_item only fills abs_err for treatment='likert'; for categorical/binary
    # it fills cat_match instead. Derive the binary abs_err from cat_match here
    # so the column is consistent across both treatments.
    if not parse_ok:
        abs_err = None
    elif sample.get("abs_err") is not None:
        abs_err = int(sample["abs_err"])
    elif sample.get("cat_match") is not None:
        abs_err = 1 - int(sample["cat_match"])
    else:
        abs_err = None

    return {
        "respondent_id": int(rid),
        "model": model,
        "prompt": prompt_id,
        "condition": CONDITION_LABEL.get(condition_internal, condition_internal),
        "item": item,
        "true_code": int(true_code),
        "pred_code": int(pred_code) if pred_code is not None else None,
        "parse_ok": bool(parse_ok),
        "abs_err": abs_err,
        "sample_position": int(sample_position),
        "timestamp": write_timestamp,
        "cost_usd": None,
        "tokens_in": None,
        "tokens_out": None,
    }


def flatten_records(records: list[dict], write_timestamp: str) -> list[dict]:
    """JSON records → flat row list. One row per (rid, cond, model, prompt, item, sample)."""
    rows: list[dict] = []
    for rec in records:
        rid = rec["respondent_id"]
        condition_internal = rec["condition"]
        model = rec["model"]
        prompt_id = rec.get("prompt_id", "P0")  # P0 default for OSF-v1 legacy
        per_item = rec.get("per_item_scores", {})
        for item, samples in per_item.items():
            for idx, sample in enumerate(samples, start=1):
                row = _row_from_sample(
                    rid, model, prompt_id, condition_internal, item, idx, sample,
                    write_timestamp,
                )
                if row is not None:
                    rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Random column (§5.4: post-hoc, one real-model pick per (rid, prompt))
# ---------------------------------------------------------------------------

def _picked_model_for(rid: int, prompt_id: str, panel_models: list[str]) -> str:
    """Deterministic random pick. SHA-256(seed|rid|prompt) → uniform index into PANEL_MODELS.
    Same inputs always produce the same pick — auditable post-hoc."""
    key = f"{RANDOM_PICK_SEED}|{rid}|{prompt_id}".encode("utf-8")
    h = hashlib.sha256(key).digest()
    idx = int.from_bytes(h[:8], "big") % len(panel_models)
    return panel_models[idx]


def add_random_column(rows: list[dict], panel_models: list[str] = PANEL_MODELS) -> list[dict]:
    """Append Random-model rows by copying the picked model's rows for each
    (respondent_id, prompt). All non-model columns preserved verbatim per §6.2."""
    by_key: dict[tuple[int, str, str], list[dict]] = {}
    for r in rows:
        if r["model"] in (RANDOM_LABEL,):
            continue  # safety: don't recurse on existing random rows
        by_key.setdefault((r["respondent_id"], r["prompt"], r["model"]), []).append(r)

    extra: list[dict] = []
    rid_prompt_pairs = {(r["respondent_id"], r["prompt"]) for r in rows}
    for rid, prompt in rid_prompt_pairs:
        picked = _picked_model_for(rid, prompt, panel_models)
        src_rows = by_key.get((rid, prompt, picked), [])
        for r in src_rows:
            new = dict(r)
            new["model"] = RANDOM_LABEL
            extra.append(new)
    return rows + extra


# ---------------------------------------------------------------------------
# Top-level write
# ---------------------------------------------------------------------------

def build_dataframe(json_paths: list[Path]) -> pd.DataFrame:
    write_timestamp = datetime.now(timezone.utc).isoformat()
    all_records: list[dict] = []
    for p in json_paths:
        if not p.exists():
            print(f"  warning: {p.name} not found, skipping", file=sys.stderr)
            continue
        with p.open() as f:
            all_records.extend(json.load(f))
    rows = flatten_records(all_records, write_timestamp)
    rows = add_random_column(rows)
    df = pd.DataFrame(rows, columns=PARQUET_COLUMNS)
    # Cast nullable int columns
    for col in ("pred_code", "abs_err", "tokens_in", "tokens_out"):
        df[col] = df[col].astype("Int32")
    df["true_code"] = df["true_code"].astype("int32")
    df["respondent_id"] = df["respondent_id"].astype("int32")
    df["sample_position"] = df["sample_position"].astype("int32")
    df["cost_usd"] = df["cost_usd"].astype("float64")
    return df


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _synthetic_records() -> list[dict]:
    """A tiny synthetic record bundle covering: 2 respondents × 4 models × 3 prompts
    × 2 conditions (Full + 1 LOO) × 2 items × n_samples=1, with one parse_fail and
    one skipped_missing_truth case."""
    out: list[dict] = []
    for rid in (0, 1):
        for cond in ("full", "loo_drop_demographic"):
            for model in PANEL_MODELS:
                for pid in ("P0", "P1", "P2"):
                    per_item = {
                        "POLVIEWS": [{
                            "truth": 3, "persona_code": 3, "parse_fail": False,
                            "treatment": "likert", "abs_err": 0, "within1": 1,
                            "cat_match": None, "skipped_missing_truth": False,
                        }],
                        "ABANY": [{
                            "truth": 1, "persona_code": 2, "parse_fail": False,
                            "treatment": "categorical", "abs_err": None, "within1": None,
                            "cat_match": 0, "skipped_missing_truth": False,
                        }],
                    }
                    if rid == 0 and model == PANEL_MODELS[0] and pid == "P0":
                        # one parse_fail, one ballot-skipped item
                        per_item["POLVIEWS"][0] = {
                            "truth": 3, "persona_code": None, "parse_fail": True,
                            "treatment": None, "abs_err": None, "within1": None,
                            "cat_match": None, "skipped_missing_truth": False,
                        }
                        per_item["GUNLAW"] = [{
                            "truth": None, "persona_code": 1, "parse_fail": False,
                            "treatment": None, "abs_err": None, "within1": None,
                            "cat_match": None, "skipped_missing_truth": True,
                        }]
                    out.append({
                        "respondent_id": rid,
                        "condition": cond,
                        "model": model,
                        "prompt_id": pid,
                        "prompt_version": "v1",
                        "template_hash": "deadbeef" + "00" * 4,
                        "n_samples": 1,
                        "per_item_scores": per_item,
                    })
    return out


def _test_row_count() -> None:
    """Compute expected counts honestly from the synthetic structure.

    2 rids × 4 models × 3 prompts × 2 conditions × 2 items = 96 nominal rows.
    The (rid=0, qwen, P0) cell adds 1 GUNLAW item but it's skipped_missing_truth
    in both conditions → 0 extra rows; the POLVIEWS rows in those 2 cells are
    parse_fail but still emit (with NULL pred_code) → still 96 real rows.
    Random column adds (rids × prompts) × conditions × items = 2 × 3 × 2 × 2
    = 24 random rows if no source row is skipped. The picked-model source for
    (rid=0, P0) determines whether random duplicates the parse_fail or not —
    either way row count is exactly 96 + 24 = 120 because parse_fail rows still
    emit (only ballot-skipped truth rows are dropped, and the GUNLAW skip
    affected the qwen source which random may or may not be drawn from)."""
    records = _synthetic_records()
    rows = flatten_records(records, datetime.now(timezone.utc).isoformat())
    assert len(rows) == 96, f"expected 96 real rows, got {len(rows)}"
    rows_with_random = add_random_column(rows)
    n_random = len(rows_with_random) - 96
    assert n_random == 24, f"expected 24 random rows, got {n_random}"
    print(f"  [row_count] PASSED (real={len(rows)}, random={n_random})")


def _test_random_determinism() -> None:
    records = _synthetic_records()
    write_ts = "2026-01-01T00:00:00+00:00"
    a = add_random_column(flatten_records(records, write_ts))
    b = add_random_column(flatten_records(records, write_ts))
    df_a = pd.DataFrame(a).sort_values(["respondent_id", "model", "prompt", "condition", "item"]).reset_index(drop=True)
    df_b = pd.DataFrame(b).sort_values(["respondent_id", "model", "prompt", "condition", "item"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(df_a, df_b)
    print("  [random_determinism] PASSED")


def _test_condition_relabel() -> None:
    records = _synthetic_records()
    rows = flatten_records(records, "2026-01-01T00:00:00+00:00")
    conds = set(r["condition"] for r in rows)
    assert conds <= {"Full", "drop_demographic"}, f"unexpected conditions: {conds}"
    print("  [condition_relabel] PASSED")


def _test_parse_fail_nulls() -> None:
    # Test BEFORE add_random_column — random column may duplicate the parse_fail
    # row under model="Random" if the seeded pick lands on the same source model.
    # Synthetic records apply the parse_fail patch to (rid=0, qwen, P0) across
    # both conditions (full + loo_drop_demographic), so we expect 2 parse_fail
    # rows pre-random.
    records = _synthetic_records()
    rows = flatten_records(records, "2026-01-01T00:00:00+00:00")
    parse_fail_rows = [r for r in rows if not r["parse_ok"]]
    assert len(parse_fail_rows) == 2, f"expected 2 parse_fail rows (pre-random), got {len(parse_fail_rows)}"
    for r in parse_fail_rows:
        assert r["pred_code"] is None and r["abs_err"] is None, f"parse_fail nulls wrong: {r}"
    print("  [parse_fail_nulls] PASSED")


def _test_binary_abs_err() -> None:
    """ABANY rows: treatment='categorical', cat_match=0 → abs_err should be 1.
    Likert POLVIEWS rows: treatment='likert', abs_err=0 → abs_err should be 0."""
    records = _synthetic_records()
    rows = flatten_records(records, "2026-01-01T00:00:00+00:00")
    abany_rows = [r for r in rows if r["item"] == "ABANY" and r["parse_ok"]]
    assert abany_rows and all(r["abs_err"] == 1 for r in abany_rows), \
        f"binary abs_err derivation wrong: {[r['abs_err'] for r in abany_rows[:3]]}"
    polviews_ok = [r for r in rows if r["item"] == "POLVIEWS" and r["parse_ok"]]
    assert polviews_ok and all(r["abs_err"] == 0 for r in polviews_ok), \
        f"likert abs_err wrong: {[r['abs_err'] for r in polviews_ok[:3]]}"
    print("  [binary_abs_err] PASSED")


def _test_parquet_roundtrip(tmp_path: Path) -> None:
    """End-to-end: synthetic records → DataFrame → parquet write → parquet read."""
    records = _synthetic_records()
    write_ts = datetime.now(timezone.utc).isoformat()
    rows = add_random_column(flatten_records(records, write_ts))
    df = pd.DataFrame(rows, columns=PARQUET_COLUMNS)
    for col in ("pred_code", "abs_err", "tokens_in", "tokens_out"):
        df[col] = df[col].astype("Int32")
    df["true_code"] = df["true_code"].astype("int32")
    df["respondent_id"] = df["respondent_id"].astype("int32")
    df["sample_position"] = df["sample_position"].astype("int32")
    out = tmp_path / "tmp_phase1a.parquet"
    df.to_parquet(out, index=False)
    df2 = pd.read_parquet(out)
    pd.testing.assert_frame_equal(
        df.reset_index(drop=True), df2.reset_index(drop=True),
        check_dtype=False,  # pyarrow may widen Int32 → Int64 on read
    )
    out.unlink()
    print("  [parquet_roundtrip] PASSED")


def run_self_tests() -> int:
    import tempfile
    print("Phase 1A parquet writer self-tests")
    _test_condition_relabel()
    _test_parse_fail_nulls()
    _test_binary_abs_err()
    _test_random_determinism()
    _test_row_count()
    with tempfile.TemporaryDirectory() as d:
        _test_parquet_roundtrip(Path(d))
    print("✓ ALL 6 SELF-TESTS PASSED")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--self-test", action="store_true", help="Run self-tests and exit")
    p.add_argument("--inputs", nargs="*", type=Path,
                   help="JSON input paths. Default: auto-discover P0/P1/P2 for panel n=200 seed=42.")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                   help=f"Output parquet path. Default: {DEFAULT_OUTPUT}")
    p.add_argument("--model-tag", default="panel")
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    if args.self_test:
        return run_self_tests()

    if args.inputs:
        json_paths = list(args.inputs)
    else:
        json_paths = []
        for pid in ("P0", "P1", "P2"):
            for pattern in (
                OUTPUTS / f"gss_phase1_records_n{args.n}_{args.model_tag}_seed{args.seed}_{pid}.json",
                OUTPUTS / f"gss_phase1_records_n{args.n}_{args.model_tag}_{pid}_seed{args.seed}.json",
                OUTPUTS / f"gss_phase1_records_n{args.n}_{args.model_tag}_{pid}.json",
            ):
                if pattern.exists():
                    json_paths.append(pattern)
                    break

    if not json_paths:
        print("error: no input JSON files found. Pass --inputs explicitly.", file=sys.stderr)
        return 2

    print(f"Building parquet from {len(json_paths)} input JSON(s):")
    for p in json_paths:
        print(f"  - {p}")
    df = build_dataframe(json_paths)
    df.to_parquet(args.output, index=False)
    print(f"Wrote {len(df):,} rows → {args.output}")
    print(f"  unique cells (model × prompt): {df.groupby(['model', 'prompt']).ngroups}")
    print(f"  conditions: {sorted(df['condition'].unique())}")
    print(f"  items: {sorted(df['item'].unique())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
