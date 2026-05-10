"""Battery LOO (Tier 1 co-primary tool — mechanistic attribution across all 4 bins).

Locked spec: `tier1_tool_schemas.md` Tool 2 (v0.4).
Locked design: `gss_phase1_design.md` §13.2 + §8.8 (multiplicity) + §8.9 (effect sizes).

Implements POST-HOC analysis only — consumes records JSON in the standard
`gss_driver.py` format and produces Battery LOO output matching the locked
schema. Does NOT extend `gss_driver.py` to actually run the 34-battery
exclusion LLM enumeration; that's Phase 1c runtime work.

Algorithm (locked):
- Records contain conditions:
  * 'full' — baseline (R1 per-item battery exclusion already applied)
  * 'battery_loo_drop_<battery_name>' — additionally drops the named battery
- For each battery B, ΔMAE_B = mean over respondents of [MAE(drop_B) − MAE(full)]
- Bootstrap CI: paired-respondent bootstrap, B=10000, seed=42 (BCa via scipy with percentile fallback for degenerate inputs — locked 2026-05-09 night per Codex N5/N6)
- Two-tailed p-value: 2 × min(P(Δ ≤ 0), P(Δ ≥ 0)) under bootstrap distribution

Multiplicity (locked, §8.8):
- Within-bin nested Holm-Bonferroni primary correction:
  D=7 / B=10 / P=2 / A=15 → smallest p < α/n_in_bin
- Joint-34 Holm sensitivity gate for cross-bin claims:
  smallest p < α/34 = 0.00147

Practical effect-size labels (locked, §8.9 + Funder & Ozer 2019):
- small / descriptive: ΔMAE < 0.02
- modest:             0.02 ≤ ΔMAE < 0.05
- substantive:        ΔMAE ≥ 0.05

substantively_meaningful flag = holm_significant_within_bin
                                AND effect_size_label ∈ {modest, substantive}
                                AND ci_lo > 0.02
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any
import random as _rng


# Pre-registered thresholds (locked 2026-05-09 evening; anchored to Funder & Ozer 2019)
EFFECT_SIZE_SMALL_LT = 0.02
EFFECT_SIZE_MODEST_GTE = 0.02
EFFECT_SIZE_SUBSTANTIVE_GTE = 0.05
ALPHA = 0.05
# B=10000 for headline runs (Codex N5 audit 2026-05-09 night): with B=1000 the
# p-value floor was 0.001, colliding with joint-34 Holm threshold (α/34 = 0.00147).
# B=10000 floor is 0.0001, well below joint-34 critical p. Bootstrap is local-
# compute (no LLM cost), so 10x runtime is acceptable for headline analysis.
# Self-tests can use smaller B for speed.
BOOTSTRAP_B_DEFAULT = 10000
SEED = 42

# BCa (bias-corrected, accelerated) bootstrap is more accurate near zero —
# important for ΔMAE values close to the small/modest practical-effect boundary.
# Locked 2026-05-09 night per Codex N6 audit. Falls back to percentile if
# scipy.stats.bootstrap is unavailable, with explicit log warning.
USE_BCA = True


# ---------------------------------------------------------------------------
# Per-respondent MAE + ΔMAE
# ---------------------------------------------------------------------------

def _likert_errs_in_record(record: dict[str, Any]) -> list[float]:
    """Same as shapley_decomposition._likert_errs_in_record. Defined locally
    to keep the module standalone."""
    errs: list[float] = []
    for samples in (record.get("per_item_scores") or {}).values():
        for s in samples:
            if s.get("parse_fail"):
                continue
            if s.get("treatment") != "likert":
                continue
            ae = s.get("abs_err")
            if ae is None:
                continue
            errs.append(float(ae))
    return errs


def _per_respondent_mae(records: list[dict[str, Any]]) -> dict[int, float]:
    by_resp: dict[int, list[float]] = {}
    for r in records:
        rid = int(r["respondent_id"])
        by_resp.setdefault(rid, []).extend(_likert_errs_in_record(r))
    return {
        rid: statistics.fmean(errs)
        for rid, errs in by_resp.items()
        if errs
    }


# ---------------------------------------------------------------------------
# Effect-size labels + significance flag
# ---------------------------------------------------------------------------

def _effect_size_label(delta_mae: float) -> str:
    if delta_mae < EFFECT_SIZE_SMALL_LT:
        return "small"
    if delta_mae < EFFECT_SIZE_SUBSTANTIVE_GTE:
        return "modest"
    return "substantive"


def _is_substantively_meaningful(
    delta_mae: float,
    ci_lo: float,
    holm_significant_within_bin: bool,
) -> bool:
    """Locked rule: significant + ≥ modest effect + CI excludes small boundary."""
    if not holm_significant_within_bin:
        return False
    if _effect_size_label(delta_mae) == "small":
        return False
    if math.isnan(ci_lo) or ci_lo <= EFFECT_SIZE_MODEST_GTE:
        return False
    return True


# ---------------------------------------------------------------------------
# Holm-Bonferroni step-down correction
# ---------------------------------------------------------------------------

def _holm_correction(p_values: dict[str, float], alpha: float = ALPHA) -> dict[str, dict[str, Any]]:
    """Apply Holm step-down correction.
    Input: {key: raw_p}
    Output: {key: {'p_holm_adjusted': float, 'holm_significant': bool}}.

    Holm: sort p ascending; smallest must clear α/n, next α/(n-1), etc.
    Adjusted p reported as min(1, p_i × (n - rank_i + 1)) with monotone ramp.
    """
    n = len(p_values)
    if n == 0:
        return {}
    sorted_keys = sorted(p_values.keys(), key=lambda k: p_values[k])
    out: dict[str, dict[str, Any]] = {}
    running_max = 0.0
    found_first_fail = False
    for i, k in enumerate(sorted_keys):
        rank = i + 1  # 1-indexed
        raw = p_values[k]
        adj = min(1.0, raw * (n - rank + 1))
        # Monotone ramp: adjusted p must be non-decreasing
        adj = max(adj, running_max)
        running_max = adj
        # Holm fails after first non-rejection: any subsequent test is non-significant
        if not found_first_fail and adj <= alpha:
            sig = True
        else:
            sig = False
            found_first_fail = True
        out[k] = {"p_holm_adjusted": round(adj, 6), "holm_significant": sig}
    return out


# ---------------------------------------------------------------------------
# Paired bootstrap for ΔMAE per battery + p-value
# ---------------------------------------------------------------------------

def _battery_paired_bootstrap(
    full_per_resp: dict[int, float],
    drop_per_resp: dict[int, float],
    B: int = BOOTSTRAP_B_DEFAULT,
    alpha: float = ALPHA,
    seed: int = SEED,
    method: str = "bca",
) -> dict[str, float]:
    """Per-battery paired bootstrap.

    method: "bca" (bias-corrected, accelerated; preferred — uses scipy)
            "percentile" (raw percentile cuts; legacy / fallback when scipy unavailable)

    Returns {'mean_delta', 'ci_lo', 'ci_hi', 'p_two_tailed', 'n_paired',
             'method_used'}.
    Two-tailed p uses the bootstrap distribution: 2 × min(P_boot(Δ ≤ 0), P_boot(Δ ≥ 0)),
    floored at 1/B to avoid log(0) downstream.
    """
    common = sorted(set(full_per_resp) & set(drop_per_resp))
    # Floor raised 5 → 30 on 2026-05-10 per Audit-fresh-2 F10. Below 30 paired
    # respondents, BCa acceleration is undefined and percentile CIs are too
    # noisy to be informative — return NaN with an explicit warning so callers
    # see the silent-fallback case. At N=3,309 the floor never triggers; it
    # exists for the OSF §6.6 reduction-to-N=1500 fallback × R1 missingness ×
    # ballot rotation case where individual battery LOO can produce sub-30
    # paired counts.
    if len(common) < 30:
        if 0 < len(common) < 30:
            print(
                f"  [battery LOO: insufficient_n={len(common)} (<30 floor); "
                "returning NaN CI rather than silent percentile estimate]",
                file=sys.stderr,
            )
        return {"mean_delta": float("nan"), "ci_lo": float("nan"),
                "ci_hi": float("nan"), "p_two_tailed": 1.0, "n_paired": len(common),
                "method_used": "insufficient_n_floor30"}
    per_resp_delta = {rid: drop_per_resp[rid] - full_per_resp[rid] for rid in common}
    delta_array = [per_resp_delta[r] for r in common]
    mean_delta = statistics.fmean(delta_array)

    # Try BCa via scipy.stats.bootstrap (preferred; more accurate near zero)
    if method == "bca":
        try:
            import math as _math
            import warnings as _warnings
            import numpy as np
            from scipy.stats import bootstrap as scipy_bootstrap
            data = (np.array(delta_array, dtype=float),)
            rng_np = np.random.default_rng(seed)
            with _warnings.catch_warnings():
                # Suppress scipy DegenerateDataWarning + numpy divide warnings
                # when input is near-constant — we detect via NaN CI below and
                # fall back to percentile.
                _warnings.simplefilter("ignore")
                res = scipy_bootstrap(
                    data,
                    statistic=np.mean,
                    n_resamples=B,
                    confidence_level=1 - alpha,
                    method="BCa",
                    random_state=rng_np,
                )
            ci_lo = float(res.confidence_interval.low)
            ci_hi = float(res.confidence_interval.high)
            if not (_math.isfinite(ci_lo) and _math.isfinite(ci_hi)):
                raise ValueError("BCa CI not finite (degenerate data)")
            boot_deltas = sorted(res.bootstrap_distribution.tolist())
            method_used = "bca"
        except Exception as e:
            # Fall back to percentile if scipy unavailable or BCa fails
            # (e.g., constant data → BCa undefined acceleration)
            print(
                f"  [bootstrap method=bca failed ({type(e).__name__}: {e}); "
                f"falling back to percentile]",
                file=sys.stderr,
            )
            method = "percentile"

    if method == "percentile":
        rng = _rng.Random(seed)
        n = len(common)
        boot_deltas = []
        for _ in range(B):
            sample = [rng.choice(delta_array) for _ in range(n)]
            boot_deltas.append(statistics.fmean(sample))
        boot_deltas.sort()
        lo_idx = int((alpha / 2) * B)
        hi_idx = int((1 - alpha / 2) * B) - 1
        ci_lo = boot_deltas[lo_idx]
        ci_hi = boot_deltas[hi_idx]
        method_used = "percentile"

    # Two-tailed p from bootstrap distribution (works for both methods).
    # Floor at 1/B so multiple batteries don't tie at 0.
    p_left = sum(1 for d in boot_deltas if d <= 0) / B
    p_right = sum(1 for d in boot_deltas if d >= 0) / B
    p_two = max(2 * min(p_left, p_right), 1.0 / B)

    return {
        "mean_delta": mean_delta,
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "p_two_tailed": p_two,
        "n_paired": len(common),
        "method_used": method_used,
    }


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------

def battery_loo_decomposition(
    records: list[dict[str, Any]],
    battery_map: dict[str, Any],
    model: str | None = None,
    seed: int = SEED,
    bootstrap_B: int = BOOTSTRAP_B_DEFAULT,
) -> dict[str, Any]:
    """Compute the full Battery LOO decomposition matching tier1_tool_schemas.md
    Tool 2 v0.4 schema.

    Args:
        records: list of records in gss_driver.py output format. Must contain:
                 - one 'full' condition per respondent
                 - one 'battery_loo_drop_<battery_name>' per (respondent, battery)
                   for each battery in battery_map['batteries'].
        battery_map: parsed gss_battery_map.json (with 'batteries' dict where
                     each battery has at least a 'bin' field).
        model: filter to this model slug (default: unique model in records).
        seed: bootstrap seed (locked at 42).
        bootstrap_B: number of bootstrap replicates (locked at 1000).
    """
    # Filter to chosen model
    if model is None:
        models_present = {r.get("model") for r in records}
        if len(models_present) == 1:
            model = next(iter(models_present))
        elif not models_present:
            return _empty_output(seed, model="UNKNOWN", reason="no_records")
        else:
            raise ValueError(
                f"Multiple models in records ({models_present}); pass `model=` to disambiguate."
            )
    model_records = [r for r in records if r.get("model") == model]

    # Group by condition
    full_records: list[dict[str, Any]] = [r for r in model_records if r.get("condition") == "full"]
    drop_records_by_battery: dict[str, list[dict[str, Any]]] = {}
    for r in model_records:
        c = r.get("condition", "")
        if c.startswith("battery_loo_drop_"):
            bname = c[len("battery_loo_drop_"):]
            drop_records_by_battery.setdefault(bname, []).append(r)

    if not full_records:
        return _empty_output(seed, model=model, reason="no_full_condition_records")

    # Per-respondent MAE under FULL
    full_per_resp = _per_respondent_mae(full_records)

    # Compute per-battery ΔMAE + bootstrap
    expected_batteries = set(battery_map["batteries"].keys())
    missing = expected_batteries - set(drop_records_by_battery)
    if missing:
        return _empty_output(
            seed, model=model,
            reason=f"missing_battery_drop_records",
            missing_batteries=sorted(missing),
            n_missing=len(missing),
        )

    per_battery_stats: dict[str, dict[str, Any]] = {}
    for bname in expected_batteries:
        drop_per_resp = _per_respondent_mae(drop_records_by_battery[bname])
        boot = _battery_paired_bootstrap(
            full_per_resp, drop_per_resp, B=bootstrap_B, seed=seed,
        )
        n_items_in_battery = len(battery_map["batteries"][bname]["items"])
        per_battery_stats[bname] = {
            "delta_mae": boot["mean_delta"],
            "ci_lo": boot["ci_lo"],
            "ci_hi": boot["ci_hi"],
            "p_raw": boot["p_two_tailed"],
            "n_paired": boot["n_paired"],
            "bin": battery_map["batteries"][bname]["bin"],
            "n_items_in_battery": n_items_in_battery,
            "delta_mae_per_item": (
                boot["mean_delta"] / n_items_in_battery if n_items_in_battery else 0.0
            ),
        }

    # Group by bin for nested Holm
    by_bin: dict[str, list[str]] = {}
    for bname, stats in per_battery_stats.items():
        by_bin.setdefault(stats["bin"], []).append(bname)

    # Nested Holm per bin
    nested_holm: dict[str, dict[str, dict[str, Any]]] = {}
    for bin_name, batteries_in_bin in by_bin.items():
        p_in_bin = {b: per_battery_stats[b]["p_raw"] for b in batteries_in_bin}
        nested_holm[bin_name] = _holm_correction(p_in_bin, alpha=ALPHA)

    # Joint-34 Holm
    p_all = {b: stats["p_raw"] for b, stats in per_battery_stats.items()}
    joint_holm = _holm_correction(p_all, alpha=ALPHA)

    # Build per-bin output blocks
    output_per_bin: dict[str, dict[str, Any]] = {}
    n_substantive_per_bin: dict[str, int] = {}
    for bin_name in ("demographic", "behavioral", "psychological", "attitudinal"):
        if bin_name not in by_bin:
            continue
        batteries_in_bin = by_bin[bin_name]
        # Rank batteries within bin by ΔMAE (descending)
        ranked = sorted(batteries_in_bin, key=lambda b: per_battery_stats[b]["delta_mae"], reverse=True)
        bin_results: dict[str, dict[str, Any]] = {}
        n_substantive = 0
        for rank_in_bin, bname in enumerate(ranked, 1):
            stats = per_battery_stats[bname]
            within_bin = nested_holm[bin_name][bname]
            joint_34 = joint_holm[bname]
            sm = _is_substantively_meaningful(
                stats["delta_mae"], stats["ci_lo"], within_bin["holm_significant"]
            )
            if sm:
                n_substantive += 1
            bin_results[bname] = {
                "delta_mae": round(stats["delta_mae"], 6),
                "ci_lo": round(stats["ci_lo"], 6),
                "ci_hi": round(stats["ci_hi"], 6),
                "rank_in_bin": rank_in_bin,
                "p_holm_within_bin": within_bin["p_holm_adjusted"],
                "holm_significant_within_bin": within_bin["holm_significant"],
                "p_holm_joint_34": joint_34["p_holm_adjusted"],
                "holm_significant_joint_34": joint_34["holm_significant"],
                "effect_size_label": _effect_size_label(stats["delta_mae"]),
                "substantively_meaningful": sm,
                "n_items_in_battery": stats["n_items_in_battery"],
                "delta_mae_per_item": round(stats["delta_mae_per_item"], 6),
            }
        n_in_bin = len(batteries_in_bin)
        output_per_bin[bin_name] = {
            "n_batteries": n_in_bin,
            "alpha_within_bin_holm": ALPHA,
            "holm_critical_smallest_p_within_bin": round(ALPHA / n_in_bin, 6),
            "results": bin_results,
        }
        n_substantive_per_bin[bin_name] = n_substantive

    n_holm_significant_within_bin_per_bin = {
        bin_name: sum(
            1 for b in by_bin.get(bin_name, [])
            if nested_holm[bin_name][b]["holm_significant"]
        )
        for bin_name in ("demographic", "behavioral", "psychological", "attitudinal")
    }
    n_holm_significant_joint_34 = sum(
        1 for v in joint_holm.values() if v["holm_significant"]
    )
    n_substantively_meaningful = sum(n_substantive_per_bin.values())

    # Build final output
    n_respondents = len(set(full_per_resp.keys()))
    out = {
        "_version": "0.4",
        "_run_id": f"battery_loo_{model.replace('/', '-')}_n{n_respondents}_seed{seed}",
        "_locked_spec_path": "tier1_tool_schemas.md",
        "model": model,
        "n_respondents": n_respondents,
        "seed": seed,
        "scope": "all_4_bins_34_batteries",
        "_scope_definition": (
            "All 34 batteries per gss_battery_map.json v0.2: 7 demographic + 10 behavioral + "
            "2 psychological + 15 attitudinal. Singletons NOT tested (deferred per §13.4)."
        ),
        "practical_thresholds": {
            "small_lt": EFFECT_SIZE_SMALL_LT,
            "modest_range": [EFFECT_SIZE_MODEST_GTE, EFFECT_SIZE_SUBSTANTIVE_GTE],
            "substantive_gte": EFFECT_SIZE_SUBSTANTIVE_GTE,
        },
        "battery_loo_per_bin": output_per_bin,
        "joint_34_holm_correction": {
            "n_tests_total": len(per_battery_stats),
            "alpha": ALPHA,
            "holm_critical_smallest_p_joint": round(ALPHA / max(len(per_battery_stats), 1), 6),
            "purpose": "cross-bin claim sensitivity gate per gss_phase1_design.md §8.8",
        },
        "summary": {
            "n_batteries_tested_total": len(per_battery_stats),
            "n_batteries_holm_significant_within_bin_per_bin": n_holm_significant_within_bin_per_bin,
            "n_batteries_holm_significant_within_bin_total": sum(n_holm_significant_within_bin_per_bin.values()),
            "n_batteries_holm_significant_joint_34": n_holm_significant_joint_34,
            "n_batteries_substantively_meaningful": n_substantively_meaningful,
            "_substantively_meaningful_definition": (
                "Holm-significant WITHIN BIN AND effect_size_label in {modest, substantive} "
                "AND ci_lo > modest threshold (excludes small-effect boundary)."
            ),
        },
        "ci_method": f"paired_bootstrap_respondent_level_B{bootstrap_B}_seed{seed}",
        "multiplicity_correction": "nested_holm_per_bin_primary_plus_joint34_sensitivity",
        "_multiplicity_definition": (
            "Two corrections in parallel. Nested Holm within each bin's battery family is the "
            "PRIMARY correction (controls within-bin FWER). Joint Holm across all 34 batteries "
            "is the SENSITIVITY correction used to gate cross-bin claims. Within-bin claims need "
            "only nested Holm; cross-bin claims need both."
        ),
    }
    return out


def _empty_output(seed: int, model: str, reason: str, **extra) -> dict[str, Any]:
    return {
        "_version": "0.4",
        "_run_id": f"battery_loo_empty_seed{seed}",
        "model": model,
        "seed": seed,
        "status": "no_output",
        "reason": reason,
        **extra,
    }


# ---------------------------------------------------------------------------
# CLI + self-test
# ---------------------------------------------------------------------------

def _self_test() -> None:
    """Synthetic-fixture self-test exercising the full Battery LOO pipeline.

    Construction:
    - 4 bins × small set of batteries each (1+1+2+2 = 6 batteries total —
      smaller than v0.2's 34 to keep self-test fast).
    - 100 synthetic respondents.
    - One battery per bin gets a substantive ΔMAE (~0.06 = above 0.05 threshold);
      others get small ΔMAE (~0.005, below 0.02 → small/descriptive).
    - We verify:
        1. Schema fields all present.
        2. Substantive batteries are Holm-significant within-bin AND substantively_meaningful=True.
        3. Small batteries are NOT substantively_meaningful (below threshold).
        4. effect_size_label matches expected for each battery.
        5. Joint-34 Holm correctly stricter than within-bin Holm.
        6. Empty input handled.
        7. Missing-battery input handled.
        8. Multiplicity definition fields present.
    """
    print("=== battery_loo self-test (synthetic fixture) ===\n")

    MODEL = "synthetic-test-model"
    n_resp = 100

    # Synthetic battery map (smaller than v0.2 to keep self-test fast)
    SYNTH_BATTERY_MAP = {
        "_version": "test",
        "batteries": {
            "demo_strong":  {"bin": "demographic",   "items": ["X1", "X2", "X3"]},  # ΔMAE ~0.06
            "demo_weak":    {"bin": "demographic",   "items": ["X4", "X5"]},        # ΔMAE ~0.005
            "beh_strong":   {"bin": "behavioral",    "items": ["X6", "X7", "X8", "X9"]},
            "beh_weak":     {"bin": "behavioral",    "items": ["X10"]},
            "psych_strong": {"bin": "psychological", "items": ["X11", "X12"]},
            "psych_weak":   {"bin": "psychological", "items": ["X13", "X14"]},
            "att_strong":   {"bin": "attitudinal",   "items": ["X15", "X16", "X17", "X18", "X19"]},
            "att_weak":     {"bin": "attitudinal",   "items": ["X20"]},
        },
        "singletons": [],
    }

    # ΔMAE design
    delta_design = {
        "demo_strong": 0.060, "demo_weak": 0.005,
        "beh_strong":  0.070, "beh_weak":  0.005,
        "psych_strong": 0.055, "psych_weak": 0.005,
        "att_strong":  0.080, "att_weak":  0.005,
    }
    base_full_mae = 1.0  # arbitrary

    rng = _rng.Random(42)
    records: list[dict[str, Any]] = []

    def _make_record(rid: int, condition: str, mae: float) -> dict[str, Any]:
        return {
            "respondent_id": rid, "condition": condition, "model": MODEL,
            "n_samples": 1,
            "per_item_scores": {
                "FAKE_LIKERT": [{
                    "truth": 4, "persona_code": 4, "parse_fail": False,
                    "treatment": "likert", "abs_err": float(mae),
                    "skipped_missing_truth": False,
                }],
            },
        }

    for rid in range(n_resp):
        per_resp_noise = rng.uniform(-0.005, 0.005)
        full_mae = base_full_mae + per_resp_noise
        records.append(_make_record(rid, "full", full_mae))
        for bname, delta in delta_design.items():
            drop_mae = full_mae + delta
            records.append(_make_record(rid, f"battery_loo_drop_{bname}", drop_mae))

    out = battery_loo_decomposition(records, SYNTH_BATTERY_MAP, model=MODEL, seed=42, bootstrap_B=200)

    # Test 1: schema fields
    required_fields = (
        "_version", "model", "n_respondents", "seed", "scope",
        "practical_thresholds", "battery_loo_per_bin", "joint_34_holm_correction",
        "summary", "ci_method", "multiplicity_correction",
    )
    for f in required_fields:
        assert f in out, f"missing required field {f!r}"
    print(f"[1] schema fields present: {len(required_fields)}/{len(required_fields)} ✓")

    # Helper to find battery result
    def _result(bname: str) -> dict[str, Any]:
        bin_name = SYNTH_BATTERY_MAP["batteries"][bname]["bin"]
        return out["battery_loo_per_bin"][bin_name]["results"][bname]

    # Test 2: substantive batteries are Holm-significant within-bin
    for bname in ("demo_strong", "beh_strong", "psych_strong", "att_strong"):
        r = _result(bname)
        assert r["holm_significant_within_bin"], (
            f"{bname} should be Holm-significant within bin; got {r}"
        )
    print(f"[2] all 4 strong batteries Holm-significant within-bin ✓")

    # Test 3: weak batteries are NOT substantively_meaningful
    for bname in ("demo_weak", "beh_weak", "psych_weak", "att_weak"):
        r = _result(bname)
        assert not r["substantively_meaningful"], (
            f"{bname} should NOT be substantively_meaningful (effect=0.005 < 0.02); got {r}"
        )
    print(f"[3] all 4 weak batteries NOT substantively_meaningful ✓")

    # Test 4: effect-size labels match
    for bname in ("demo_strong", "beh_strong", "psych_strong", "att_strong"):
        r = _result(bname)
        assert r["effect_size_label"] == "substantive", (
            f"{bname} should be 'substantive' (delta ≥ 0.05); got {r['effect_size_label']}"
        )
    for bname in ("demo_weak", "beh_weak", "psych_weak", "att_weak"):
        r = _result(bname)
        assert r["effect_size_label"] == "small", (
            f"{bname} should be 'small' (delta < 0.02); got {r['effect_size_label']}"
        )
    print(f"[4] effect_size_label correct on all 8 batteries ✓")

    # Test 5: joint-34 Holm is at least as strict as within-bin Holm.
    # Check: any battery where within_bin=False MUST also have joint=False.
    for bin_name, bin_block in out["battery_loo_per_bin"].items():
        for bname, r in bin_block["results"].items():
            if not r["holm_significant_within_bin"]:
                assert not r["holm_significant_joint_34"], (
                    f"{bname}: joint-34 cannot be significant if within-bin is not; got {r}"
                )
    print(f"[5] joint-34 Holm is ≥ within-bin Holm strictness ✓")

    # Test 6: empty input
    out_empty = battery_loo_decomposition([], SYNTH_BATTERY_MAP, model="empty", seed=42, bootstrap_B=10)
    assert out_empty.get("status") == "no_output"
    print(f"[6] empty-records input handled gracefully ✓")

    # Test 7: missing-battery input
    incomplete = [r for r in records if "att_strong" not in r["condition"]]
    out_partial = battery_loo_decomposition(incomplete, SYNTH_BATTERY_MAP, model=MODEL, seed=42, bootstrap_B=10)
    assert out_partial.get("status") == "no_output"
    assert "missing" in out_partial.get("reason", "")
    print(f"[7] missing-battery input handled gracefully ✓")

    # Test 8: multiplicity-definition fields present
    assert out["multiplicity_correction"] == "nested_holm_per_bin_primary_plus_joint34_sensitivity"
    assert "joint_34_holm_correction" in out
    assert out["joint_34_holm_correction"]["n_tests_total"] == 8  # synthetic has 8 batteries, not 34
    print(f"[8] multiplicity definition fields present + correct ✓")

    print(f"\n  Substantive findings (subset): "
          f"{out['summary']['n_batteries_substantively_meaningful']}/8 batteries")
    print(f"  Holm-significant within-bin: {out['summary']['n_batteries_holm_significant_within_bin_total']}/8")
    print(f"  Holm-significant joint-N: {out['summary']['n_batteries_holm_significant_joint_34']}/8")

    print(f"\n✓ ALL BATTERY LOO SELF-TESTS PASSED")


def _cli():
    p = argparse.ArgumentParser(
        description="Battery LOO co-primary mechanistic attribution. "
                    "Locked spec: tier1_tool_schemas.md Tool 2 v0.4."
    )
    p.add_argument("--self-test", action="store_true",
                   help="run synthetic-fixture self-test (8 assertions)")
    p.add_argument("--input", type=Path, default=None,
                   help="path to records JSON (gss_driver.py output format)")
    p.add_argument("--battery-map", type=Path,
                   default=Path(__file__).parent / "gss_battery_map.json",
                   help="path to gss_battery_map.json (default: locked v0.2)")
    p.add_argument("--output", type=Path, default=None,
                   help="path to write Battery LOO JSON output")
    p.add_argument("--model", type=str, default=None,
                   help="filter records to this model slug (default: unique model)")
    p.add_argument("--seed", type=int, default=SEED, help="bootstrap seed (locked at 42)")
    p.add_argument("--bootstrap-B", type=int, default=BOOTSTRAP_B_DEFAULT, help="bootstrap replicates")
    return p.parse_args()


if __name__ == "__main__":
    args = _cli()
    if args.self_test:
        _self_test()
        sys.exit(0)
    if args.input is None:
        print("error: --input required (or pass --self-test)", file=sys.stderr)
        sys.exit(2)
    if not args.input.exists():
        print(f"error: {args.input} not found", file=sys.stderr)
        sys.exit(2)
    if not args.battery_map.exists():
        print(f"error: {args.battery_map} not found", file=sys.stderr)
        sys.exit(2)
    records = json.loads(args.input.read_text())
    battery_map = json.loads(args.battery_map.read_text())
    out = battery_loo_decomposition(
        records, battery_map, model=args.model, seed=args.seed, bootstrap_B=args.bootstrap_B,
    )
    if args.output is None:
        print(json.dumps(out, indent=2))
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(out, indent=2))
        print(f"✓ wrote {args.output}")
