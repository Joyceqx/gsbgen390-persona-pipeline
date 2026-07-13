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
    # Phase 1B 6th condition (locked 2026-07-12): R1 + one random battery
    # per (rid, item). The dropped battery name travels in the
    # random_dropped_battery column.
    "random_battery_drop": "random_battery_drop",
}

# Cheap-panel real models (deterministic order; matters for the seeded random pick).
PANEL_MODELS = [
    "qwen/qwen3-max",
    "deepseek/deepseek-v3.1-terminus",   # F'' swap: was deepseek-v4-pro thinking cell
    "meta-llama/llama-4-maverick",
    "moonshotai/kimi-k2-0905",
]

RANDOM_LABEL = "Random"
RANDOM_PICK_SEED = 42  # seeded picker for §5.4 post-hoc random column

# Column order = §6.2 schema + provenance extensions (locked 2026-05-29 per
# Reviewer round-2 Q5 — cross-model paper requires per-call provider /
# fingerprint logging since post-hoc backend identity recovery is impossible).
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
    "timestamp",           # str (ISO 8601 UTC; parquet-write time)
    "cost_usd",            # nullable float64 (call_llm TODO — not exposed yet)
    "tokens_in",           # nullable int32 (from call_llm_meta usage)
    "tokens_out",          # nullable int32 (from call_llm_meta usage)
    # Provenance + audit trail
    "error_type",          # str: "ok" | "parse_fail" | "provider_error"
    "provider",            # nullable str (OpenRouter backend; null for OpenAI direct)
    "system_fingerprint",  # nullable str (OpenAI reproducibility token)
    "model_returned",      # nullable str (provider-reported model name; may differ from requested slug)
    # Randomized battery ablation (Phase 1B 6th condition, locked 2026-07-12)
    "random_dropped_battery",  # nullable str: battery dropped in the
                               # random_battery_drop condition; NULL elsewhere
                               # (incl. all Phase 1A rows). The absent-vs-present
                               # per-battery analysis joins on this column.
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
        "cost_usd": None,  # call_llm_meta returns tokens, not USD; cost is left
                            # for downstream USD-rate-table joins.
        "tokens_in": sample.get("tokens_in"),
        "tokens_out": sample.get("tokens_out"),
        "error_type": sample.get("error_type", "ok" if parse_ok else "parse_fail"),
        "provider": sample.get("provider"),
        "system_fingerprint": sample.get("system_fingerprint"),
        "model_returned": sample.get("model_returned"),
        "random_dropped_battery": sample.get("random_dropped_battery"),
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

def build_dataframe(json_paths: list[Path], add_random: bool = True) -> pd.DataFrame:
    write_timestamp = datetime.now(timezone.utc).isoformat()
    all_records: list[dict] = []
    for p in json_paths:
        if not p.exists():
            print(f"  warning: {p.name} not found, skipping", file=sys.stderr)
            continue
        with p.open() as f:
            all_records.extend(json.load(f))
    rows = flatten_records(all_records, write_timestamp)
    # Phase 1B guard (Reviewer 2026-07-12 CRITICAL): under random dispatch the
    # picked model IS the §5.4 random pick (hash-identical by design), so
    # add_random_column would duplicate 100% of Phase 1B rows under
    # model="Random" — doubling N and silently shrinking bootstrap/clustered
    # SEs by ~√2. The Random column is a Phase 1A construct; §6.3 locks
    # "no post-hoc Random relabeling at the Phase 1B stage". Detect
    # Phase-1B-shaped input (any non-Full condition) and refuse.
    phase1b_shaped = any(r["condition"] != "Full" for r in rows)
    if add_random and phase1b_shaped:
        raise ValueError(
            "Input records contain non-Full conditions (Phase 1B shape). "
            "The §5.4 Random column applies to Phase 1A only — adding it here "
            "would duplicate every row (random dispatch pick == Random-column "
            "pick by design). Re-run with --no-random-column and an explicit "
            "--output (e.g. outputs/phase1b_raw.parquet)."
        )
    if add_random:
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


def _test_provenance_columns_e2e(tmp_path: Path) -> None:
    """Reviewer round-3 additional concern: confirm error_type / provider /
    system_fingerprint / model_returned actually flow from the JSON sample
    dict through flatten_records into the parquet on disk.

    Builds a minimal record where every sample carries populated provenance
    fields; writes parquet; reads back; asserts each provenance column is
    present and matches the source values."""
    # Hand-built record with provenance fields (driver populates these via
    # call_llm_meta + score.update(call_meta) + score["error_type"]).
    rec = {
        "respondent_id": 0, "condition": "full",
        "model": "qwen/qwen3-max",
        "prompt_id": "P0", "prompt_version": "v1",
        "template_hash": "abc123" + "00" * 5, "n_samples": 1,
        "per_item_scores": {
            "POLVIEWS": [{
                "truth": 3, "persona_code": 3, "parse_fail": False,
                "treatment": "likert", "abs_err": 0, "within1": 1,
                "cat_match": None, "skipped_missing_truth": False,
                "error_type": "ok",
                "provider": "DeepInfra",
                "system_fingerprint": "fp_44709d6fcb",
                "model_returned": "qwen/qwen3-max",
                "tokens_in": 928, "tokens_out": 3,
            }],
            "ABANY": [{
                "truth": 1, "persona_code": None, "parse_fail": True,
                "treatment": None, "abs_err": None, "within1": None,
                "cat_match": None, "skipped_missing_truth": False,
                "error_type": "provider_error",
                "provider": None,  # provider unknown when call_llm raised
                "system_fingerprint": None,
                "model_returned": None,
                "tokens_in": None, "tokens_out": None,
            }],
        },
    }
    write_ts = datetime.now(timezone.utc).isoformat()
    rows = flatten_records([rec], write_ts)
    # Two rows: POLVIEWS (ok) and ABANY (provider_error)
    assert len(rows) == 2, len(rows)
    polviews = next(r for r in rows if r["item"] == "POLVIEWS")
    abany = next(r for r in rows if r["item"] == "ABANY")
    assert polviews["error_type"] == "ok"
    assert polviews["provider"] == "DeepInfra"
    assert polviews["system_fingerprint"] == "fp_44709d6fcb"
    assert polviews["model_returned"] == "qwen/qwen3-max"
    assert polviews["tokens_in"] == 928 and polviews["tokens_out"] == 3
    assert abany["error_type"] == "provider_error"
    assert abany["provider"] is None
    assert abany["system_fingerprint"] is None

    # Now write parquet, read back, and re-verify the provenance columns
    df = pd.DataFrame(rows, columns=PARQUET_COLUMNS)
    for col in ("pred_code", "abs_err", "tokens_in", "tokens_out"):
        df[col] = df[col].astype("Int32")
    df["true_code"] = df["true_code"].astype("int32")
    df["respondent_id"] = df["respondent_id"].astype("int32")
    df["sample_position"] = df["sample_position"].astype("int32")
    out = tmp_path / "tmp_provenance.parquet"
    df.to_parquet(out, index=False)
    df2 = pd.read_parquet(out)
    expected_provenance_cols = {
        "error_type", "provider", "system_fingerprint", "model_returned",
        "tokens_in", "tokens_out",
    }
    assert expected_provenance_cols <= set(df2.columns), \
        f"missing provenance columns on read-back: {expected_provenance_cols - set(df2.columns)}"
    polviews_back = df2[df2["item"] == "POLVIEWS"].iloc[0]
    assert polviews_back["provider"] == "DeepInfra"
    assert polviews_back["system_fingerprint"] == "fp_44709d6fcb"
    assert polviews_back["model_returned"] == "qwen/qwen3-max"
    assert polviews_back["error_type"] == "ok"
    assert int(polviews_back["tokens_in"]) == 928
    abany_back = df2[df2["item"] == "ABANY"].iloc[0]
    assert abany_back["error_type"] == "provider_error"
    assert pd.isna(abany_back["provider"])
    out.unlink()
    print("  [provenance_columns_e2e] PASSED")


def _test_random_battery_drop_column(tmp_path: Path) -> None:
    """Reviewer 2026-07-12 findings 1 + 5: (a) a POPULATED
    random_dropped_battery value must survive flatten → parquet → read-back;
    (b) build_dataframe must REFUSE to add the Random column on
    Phase-1B-shaped (non-Full) records."""
    rec = {
        "respondent_id": 7, "condition": "random_battery_drop",
        "model": "moonshotai/kimi-k2-0905",
        "prompt_id": "P1", "prompt_version": "v1",
        "template_hash": "abc123" + "00" * 5, "n_samples": 1,
        "per_item_scores": {
            "POLVIEWS": [{
                "truth": 3, "persona_code": 2, "parse_fail": False,
                "treatment": "likert", "abs_err": 1, "within1": 1,
                "cat_match": None, "skipped_missing_truth": False,
                "random_dropped_battery": "voting_choice",
            }],
        },
    }
    rows = flatten_records([rec], datetime.now(timezone.utc).isoformat())
    assert len(rows) == 1
    assert rows[0]["condition"] == "random_battery_drop", rows[0]["condition"]
    assert rows[0]["random_dropped_battery"] == "voting_choice"

    df = pd.DataFrame(rows, columns=PARQUET_COLUMNS)
    out = tmp_path / "tmp_ablation.parquet"
    df.to_parquet(out, index=False)
    back = pd.read_parquet(out)
    assert back.iloc[0]["random_dropped_battery"] == "voting_choice"
    out.unlink()

    # (b) the Phase 1B guard: build_dataframe(add_random=True) must raise
    import tempfile as _tf
    with _tf.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump([rec], f)
        tmp_json = Path(f.name)
    try:
        try:
            build_dataframe([tmp_json], add_random=True)
            raise AssertionError("build_dataframe did not refuse Phase-1B-shaped input with add_random=True")
        except ValueError:
            pass
        df_ok = build_dataframe([tmp_json], add_random=False)
        assert len(df_ok) == 1 and "Random" not in set(df_ok["model"])
    finally:
        tmp_json.unlink()
    print("  [random_battery_drop_column] PASSED")


def _test_panel_lock_matches_router() -> None:
    """Reviewer 2026-07-12 finding 4: PANEL_MODELS here and
    MODEL_PANEL_PRIMARY in llm_router must stay identical IN ORDER — the
    §5.4 Random column and the Phase 1B random dispatch hash into these
    lists independently, and any silent reorder breaks the '§7.1 Phase 1A
    random assignments extend verbatim' contract."""
    from llm_router import MODEL_PANEL_PRIMARY
    assert PANEL_MODELS == list(MODEL_PANEL_PRIMARY), (
        f"PANEL_MODELS != llm_router.MODEL_PANEL_PRIMARY:\n"
        f"  writer: {PANEL_MODELS}\n  router: {list(MODEL_PANEL_PRIMARY)}"
    )
    print("  [panel_lock_matches_router] PASSED")


def run_self_tests() -> int:
    import tempfile
    print("Phase 1A parquet writer self-tests")
    _test_condition_relabel()
    _test_parse_fail_nulls()
    _test_binary_abs_err()
    _test_random_determinism()
    _test_row_count()
    _test_panel_lock_matches_router()
    with tempfile.TemporaryDirectory() as d:
        _test_parquet_roundtrip(Path(d))
        _test_provenance_columns_e2e(Path(d))
        _test_random_battery_drop_column(Path(d))
    print("✓ ALL 9 SELF-TESTS PASSED")
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
    p.add_argument("--no-random-column", action="store_true",
                   help="Skip the §5.4 post-hoc Random column. REQUIRED for "
                        "Phase 1B consolidation (random dispatch already IS "
                        "the random pick; adding the column would duplicate "
                        "every row — Reviewer 2026-07-12 CRITICAL).")
    p.add_argument("--model-tag", default="panel")
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    if args.self_test:
        return run_self_tests()

    # Clobber guard: Phase 1B consolidation (--no-random-column) must not
    # silently overwrite the paid Phase 1A artifact at the default path.
    if args.no_random_column and args.output == DEFAULT_OUTPUT:
        print(
            "error: --no-random-column (Phase 1B consolidation) requires an "
            "explicit --output (e.g. outputs/phase1b_raw.parquet) — the "
            f"default {DEFAULT_OUTPUT.name} is the paid Phase 1A artifact.",
            file=sys.stderr,
        )
        return 2

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
    try:
        df = build_dataframe(json_paths, add_random=not args.no_random_column)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    df.to_parquet(args.output, index=False)
    print(f"Wrote {len(df):,} rows → {args.output}")
    print(f"  unique cells (model × prompt): {df.groupby(['model', 'prompt']).ngroups}")
    print(f"  conditions: {sorted(df['condition'].unique())}")
    print(f"  items: {sorted(df['item'].unique())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
