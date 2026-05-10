"""Bin-level Shapley decomposition (Tier 1 secondary tool — robustness for 4-bin LOO).

Locked spec: `tier1_tool_schemas.md` Tool 1 (v0.2).
Locked design: `gss_phase1_design.md` §13.1.

Implements POST-HOC analysis only — consumes records JSON in the standard
`gss_driver.py` format and produces Shapley + interaction outputs matching
the locked schema. Does NOT extend `gss_driver.py` to actually run the
16-condition LLM enumeration; that's Phase 1a runtime work.

Math (locked):
- 4 bins → 2⁴ = 16 conditions, indexed by which bins are INCLUDED.
- Shapley value for bin B = sum over coalitions S not containing B of
  weight(|S|, n=4) × [MAE(S) − MAE(S ∪ {B})], where weight is the
  standard Shapley combinatorial weight.
- ANOVA-contrast decomposition: each subset T ⊆ bins has a coefficient
  α_T = (1/16) Σ_x MAE(x) c_T(x), where c_T(x) = ∏_{B∈T}(2·1[B in x] - 1).
  α_∅ = grand mean; α_{B} = main effect for B; α_T for |T|≥2 = interactions.
- interaction_variance_share = Σ_{|T|≥2} α_T² / Σ_{|T|≥1} α_T².
- Bootstrap CIs at respondent level, B=10000, seed=42 (paired across all 16
  conditions per resample to preserve correlation structure).
- Percentile bootstrap (NOT BCa) because each replicate produces a vector of
  ~16 derived statistics (4 Shapley values + 11 interaction contrasts + IVS).
  BCa requires per-statistic jackknife on the original data, which would mean
  16 separate full re-decompositions per leave-one-respondent-out — ~24,000
  jackknife evaluations on top of 10,000 bootstrap replicates. Cost-prohibitive
  and the symmetric-by-construction Shapley contrast distribution makes BCa
  correction mostly cosmetic. Battery LOO uses BCa because each battery is a
  scalar ΔMAE close to the small/modest practical-effect boundary, where
  near-zero asymmetry actually matters.
- Bumped B 1000 → 10000 (Codex N5 audit 2026-05-09 night, doc revised
  per Audit-2 review 2026-05-09 night): rationale is consistency with the
  rest of the bootstrap pipeline (battery_loo + gss_pipeline both at 10000)
  and tighter Shapley + IVS CIs. Note: the joint-34 Holm threshold rationale
  cited elsewhere does NOT apply here — Shapley shares the 4-bin primary
  family per §8.8 and has no joint-34 multiplicity gate. Bootstrap is local-
  compute (no LLM cost) so 10x runtime is acceptable for the headline.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from itertools import combinations
from pathlib import Path
from typing import Any
import random as _rng


BINS = ("demographic", "behavioral", "psychological", "attitudinal")
N_BINS = 4

# Per-bin abbreviation for compact subset naming (e.g., "DBP" = D+B+P).
BIN_ABBREV = {"demographic": "D", "behavioral": "B", "psychological": "P", "attitudinal": "A"}
ABBREV_TO_BIN = {v: k for k, v in BIN_ABBREV.items()}


# ---------------------------------------------------------------------------
# Subset helpers
# ---------------------------------------------------------------------------

def _all_subsets(items: tuple[str, ...]) -> list[frozenset[str]]:
    """All 2^n subsets of items as frozensets."""
    return [
        frozenset(c)
        for r in range(len(items) + 1)
        for c in combinations(items, r)
    ]


def _subset_label(S: frozenset[str]) -> str:
    """Compact label for a subset, e.g., {dem, beh} → 'DB'; {} → '_'."""
    if not S:
        return "_"
    return "".join(BIN_ABBREV[b] for b in BINS if b in S)


def _shapley_weight(s_size: int, n: int) -> float:
    """Standard Shapley combinatorial weight: |S|! · (n−|S|−1)! / n!"""
    return (
        math.factorial(s_size)
        * math.factorial(n - s_size - 1)
        / math.factorial(n)
    )


# ---------------------------------------------------------------------------
# Per-respondent MAE per condition
# ---------------------------------------------------------------------------

def _likert_errs_in_record(record: dict[str, Any]) -> list[float]:
    """Flatten one record's per_item_scores to list of Likert |error| values
    (excludes parse-failed and missing-truth-skipped samples)."""
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
    """For a list of records (one per respondent under a SINGLE condition),
    return {respondent_id: per-respondent Likert MAE}.

    Records with no Likert observations are dropped. If a respondent has
    multiple records (e.g., one per sample), errors are pooled then meaned.
    """
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
# Shapley + ANOVA decomposition (deterministic from 16-condition MAE map)
# ---------------------------------------------------------------------------

def _shapley_per_bin(mae_by_subset: dict[frozenset[str], float]) -> dict[str, float]:
    """Compute Shapley value for each bin given MAE under each of 16 subsets.

    mae_by_subset must map every frozenset(subset of BINS) to a float MAE.
    Returns {bin_name: shapley_value}.
    """
    out: dict[str, float] = {}
    for B in BINS:
        sv = 0.0
        for S in _all_subsets(tuple(b for b in BINS if b != B)):
            S_with_B = S | {B}
            w = _shapley_weight(len(S), N_BINS)
            sv += w * (mae_by_subset[S] - mae_by_subset[S_with_B])
        out[B] = sv
    return out


def _anova_contrasts(mae_by_subset: dict[frozenset[str], float]) -> dict[frozenset[str], float]:
    """ANOVA-contrast decomposition over 2^4 design.

    For each subset T ⊆ BINS, α_T = (1/16) Σ_x MAE(x) · c_T(x), where
    c_T(x) = ∏_{B∈T} (2·1[B∈x] − 1) ∈ {±1}.

    Returns {frozenset: α_T}. α_∅ is the grand mean across 16 conditions;
    α_{B} for singletons are main effects; |T|≥2 are interactions.
    """
    all_T = _all_subsets(BINS)
    out: dict[frozenset[str], float] = {}
    for T in all_T:
        s = 0.0
        for x in _all_subsets(BINS):
            sign = 1
            for B in T:
                sign *= 1 if B in x else -1
            s += sign * mae_by_subset[x]
        out[T] = s / (2 ** N_BINS)
    return out


def _interaction_variance_share(contrasts: dict[frozenset[str], float]) -> float:
    """Share of total non-mean variance attributable to ≥2-way interactions.

    interaction_variance_share = Σ_{|T|≥2} α_T² / Σ_{|T|≥1} α_T².
    Returns 0.0 if no main effects (degenerate flat MAE surface).
    """
    main_plus_inter = sum(v ** 2 for T, v in contrasts.items() if len(T) >= 1)
    inter_only = sum(v ** 2 for T, v in contrasts.items() if len(T) >= 2)
    if main_plus_inter == 0:
        return 0.0
    return inter_only / main_plus_inter


# ---------------------------------------------------------------------------
# Bootstrap CI (paired across 16 conditions per resample)
# ---------------------------------------------------------------------------

BOOTSTRAP_B_DEFAULT = 10000  # locked 2026-05-09 night per Codex N5 audit


def _paired_bootstrap_shapley(
    per_resp_mae_by_subset: dict[frozenset[str], dict[int, float]],
    B: int = BOOTSTRAP_B_DEFAULT,
    seed: int = 42,
    alpha: float = 0.05,
) -> dict[str, dict[str, tuple[float, float]]]:
    """Paired bootstrap: resample respondents ONCE per replicate; compute
    Shapley values + interaction terms on the resample-aggregated MAEs.

    Returns nested dict:
        {
          "shapley": {bin: (ci_lo, ci_hi)},
          "interaction_2way": {label: (ci_lo, ci_hi)},
          "interaction_3way": {label: (ci_lo, ci_hi)},
          "interaction_4way": {label: (ci_lo, ci_hi)},
          "interaction_variance_share": (ci_lo, ci_hi),
        }
    """
    # Common respondents present in ALL 16 condition dicts
    common_rids = sorted(
        set.intersection(*(set(d.keys()) for d in per_resp_mae_by_subset.values()))
    )
    if len(common_rids) < 5:
        # too thin; return NaN CIs
        empty = (float("nan"), float("nan"))
        return {
            "shapley": {b: empty for b in BINS},
            "interaction_2way": {},
            "interaction_3way": {},
            "interaction_4way": {},
            "interaction_variance_share": empty,
        }

    rng = _rng.Random(seed)
    n = len(common_rids)
    boot_shapley: dict[str, list[float]] = {b: [] for b in BINS}
    boot_int2: dict[str, list[float]] = {}
    boot_int3: dict[str, list[float]] = {}
    boot_int4: dict[str, list[float]] = {}
    boot_ivs: list[float] = []

    for _ in range(B):
        sample = [rng.choice(common_rids) for _ in range(n)]
        # Aggregate MAE per subset across the resample
        mae_by_subset: dict[frozenset[str], float] = {}
        for S, per_resp in per_resp_mae_by_subset.items():
            mae_by_subset[S] = statistics.fmean(per_resp[r] for r in sample)
        sv = _shapley_per_bin(mae_by_subset)
        for B_name, val in sv.items():
            boot_shapley[B_name].append(val)
        contrasts = _anova_contrasts(mae_by_subset)
        for T, alpha_T in contrasts.items():
            label = _subset_label(T)
            if len(T) == 2:
                boot_int2.setdefault(label, []).append(alpha_T)
            elif len(T) == 3:
                boot_int3.setdefault(label, []).append(alpha_T)
            elif len(T) == 4:
                boot_int4.setdefault(label, []).append(alpha_T)
        boot_ivs.append(_interaction_variance_share(contrasts))

    def _ci(values: list[float]) -> tuple[float, float]:
        s = sorted(values)
        lo_idx = int((alpha / 2) * len(s))
        hi_idx = int((1 - alpha / 2) * len(s)) - 1
        return (s[lo_idx], s[hi_idx])

    return {
        "shapley": {b: _ci(boot_shapley[b]) for b in BINS},
        "interaction_2way": {k: _ci(v) for k, v in boot_int2.items()},
        "interaction_3way": {k: _ci(v) for k, v in boot_int3.items()},
        "interaction_4way": {k: _ci(v) for k, v in boot_int4.items()},
        "interaction_variance_share": _ci(boot_ivs),
    }


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------

def shapley_decomposition(
    records: list[dict[str, Any]],
    model: str | None = None,
    seed: int = 42,
    bootstrap_B: int = BOOTSTRAP_B_DEFAULT,
) -> dict[str, Any]:
    """Compute the full Shapley + interaction decomposition from a records list.

    Records are filtered to (a) the specified `model` (or the unique model in
    records, if exactly one), (b) the 16 Shapley conditions named
    `shapley_<subset_label>` (e.g., shapley_DBPA, shapley_DB, shapley__).

    Returns a dict matching `tier1_tool_schemas.md` Tool 1 v0.2 schema.
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
    if not model_records:
        return _empty_output(seed, model=model, reason=f"no_records_for_model_{model}")

    # Group by condition; expect 16 conditions named shapley_<label>
    by_condition: dict[str, list[dict[str, Any]]] = {}
    for r in model_records:
        c = r.get("condition", "")
        if c.startswith("shapley_"):
            by_condition.setdefault(c, []).append(r)

    # Map condition → subset frozenset
    cond_to_subset: dict[str, frozenset[str]] = {}
    for cond in by_condition:
        label = cond[len("shapley_"):]  # e.g., "DBPA" or "" for shapley__
        if label == "_" or label == "":
            cond_to_subset[cond] = frozenset()
            continue
        try:
            S = frozenset(ABBREV_TO_BIN[ch] for ch in label)
        except KeyError:
            continue
        cond_to_subset[cond] = S

    expected_subsets = set(_all_subsets(BINS))
    present_subsets = set(cond_to_subset.values())
    missing = expected_subsets - present_subsets
    if missing:
        return _empty_output(
            seed, model=model,
            reason=f"missing_{len(missing)}_of_16_subsets",
            missing_subsets=sorted(_subset_label(s) for s in missing),
        )

    # Per-respondent MAE for each subset
    per_resp_by_subset: dict[frozenset[str], dict[int, float]] = {}
    for cond, S in cond_to_subset.items():
        per_resp_by_subset[S] = _per_respondent_mae(by_condition[cond])

    # Common respondents across all 16 conditions
    common_rids = sorted(
        set.intersection(*(set(d.keys()) for d in per_resp_by_subset.values()))
    )

    # Aggregate point estimates
    mae_by_subset = {
        S: statistics.fmean(per_resp_by_subset[S][r] for r in common_rids)
        for S in expected_subsets
    }
    shapley_vals = _shapley_per_bin(mae_by_subset)
    contrasts = _anova_contrasts(mae_by_subset)
    ivs = _interaction_variance_share(contrasts)

    # Bootstrap CIs
    cis = _paired_bootstrap_shapley(per_resp_by_subset, B=bootstrap_B, seed=seed)

    # Build output matching tier1_tool_schemas.md Tool 1 v0.2 schema
    shapley_per_bin: dict[str, dict[str, float]] = {}
    rank_order = sorted(BINS, key=lambda b: shapley_vals[b], reverse=True)
    for b in BINS:
        ci_lo, ci_hi = cis["shapley"][b]
        shapley_per_bin[b] = {
            "shapley_value": round(shapley_vals[b], 6),
            "ci_lo": round(ci_lo, 6) if not math.isnan(ci_lo) else None,
            "ci_hi": round(ci_hi, 6) if not math.isnan(ci_hi) else None,
            "rank": rank_order.index(b) + 1,
        }

    def _interaction_block(target_size: int, ci_block: dict[str, tuple[float, float]]) -> dict[str, dict[str, float]]:
        out: dict[str, dict[str, float]] = {}
        for T, alpha_T in contrasts.items():
            if len(T) != target_size:
                continue
            label = _subset_label(T)
            ci_lo, ci_hi = ci_block.get(label, (float("nan"), float("nan")))
            # Use full bin names joined by * for readability in JSON
            full_name = "*".join(b for b in BINS if b in T)
            out[full_name] = {
                "value": round(alpha_T, 6),
                "ci_lo": round(ci_lo, 6) if not math.isnan(ci_lo) else None,
                "ci_hi": round(ci_hi, 6) if not math.isnan(ci_hi) else None,
            }
        return out

    output = {
        "_version": "0.2",
        "_run_id": f"shapley_{model.replace('/', '-')}_n{len(common_rids)}_seed{seed}",
        "_locked_spec_path": "tier1_tool_schemas.md",
        "model": model,
        "n_respondents": len(common_rids),
        "n_primary_eval_items": "(see records)",
        "n_conditions_run": len(present_subsets),
        "seed": seed,
        "shapley_per_bin": shapley_per_bin,
        "interaction_2way": _interaction_block(2, cis["interaction_2way"]),
        "interaction_3way": _interaction_block(3, cis["interaction_3way"]),
        "interaction_4way": _interaction_block(4, cis["interaction_4way"]),
        "interaction_variance_share": round(ivs, 6),
        "_interaction_variance_share_definition": (
            "Sum of squared 2-way + 3-way + 4-way interaction terms, divided by total sum of "
            "squared (main + interaction) terms. Range [0, 1]. Higher = more variance attributable "
            "to interactions vs main effects. NOT the Friedman & Popescu (2008) H-statistic."
        ),
        "interaction_variance_share_ci": {
            "ci_lo": round(cis["interaction_variance_share"][0], 6) if not math.isnan(cis["interaction_variance_share"][0]) else None,
            "ci_hi": round(cis["interaction_variance_share"][1], 6) if not math.isnan(cis["interaction_variance_share"][1]) else None,
        },
        "raw_condition_mae": {
            f"{_subset_label(S)}_{'+'.join(sorted(b for b in BINS if b in S)) or 'no_bins'}": {
                "mae": round(mae_by_subset[S], 6),
                "n": len(common_rids),
            }
            for S in expected_subsets
        },
        "loo_consistency_check": _loo_vs_shapley_rank_check(
            shapley_vals, mae_by_subset
        ),
        "ci_method": f"paired_bootstrap_respondent_level_B{bootstrap_B}",
        "alpha": 0.05,
    }
    return output


def _loo_vs_shapley_rank_check(
    shapley_vals: dict[str, float],
    mae_by_subset: dict[frozenset[str], float],
) -> dict[str, Any]:
    """Compare 4-bin LOO ranking (drop-one) against Shapley ranking.

    LOO ΔMAE for bin B = MAE(all-but-B) − MAE(all). Higher ΔMAE = bigger
    drop in accuracy when removed = more important.
    Shapley rank is by Shapley value (higher = more contribution).
    These should usually agree; disagreement flags interaction effects.
    """
    full_set = frozenset(BINS)
    mae_full = mae_by_subset[full_set]
    loo_delta = {
        B: mae_by_subset[full_set - {B}] - mae_full
        for B in BINS
    }
    loo_rank = sorted(BINS, key=lambda b: loo_delta[b], reverse=True)
    shapley_rank = sorted(BINS, key=lambda b: shapley_vals[b], reverse=True)
    rank_match: dict[str, bool] = {}
    for b in BINS:
        rank_match[b] = (loo_rank.index(b) == shapley_rank.index(b))
    return {
        "loo_rank_matches_shapley_rank": all(rank_match.values()),
        "_definition": (
            "For each bin, does its 4-bin LOO ΔMAE rank equal its Shapley rank? "
            "If false, LOO ranking depends on bin interactions — flag for Discussion."
        ),
        "per_bin_rank_match": rank_match,
        "loo_delta_mae": {b: round(v, 6) for b, v in loo_delta.items()},
        "shapley_rank_order": shapley_rank,
        "loo_rank_order": loo_rank,
    }


def _empty_output(seed: int, model: str, reason: str, **extra) -> dict[str, Any]:
    return {
        "_version": "0.2",
        "_run_id": f"shapley_empty_seed{seed}",
        "model": model,
        "seed": seed,
        "status": "no_output",
        "reason": reason,
        **extra,
    }


# ---------------------------------------------------------------------------
# CLI + self-test
# ---------------------------------------------------------------------------

def _make_synthetic_record(
    rid: int,
    condition: str,
    model: str,
    item_codes: dict[str, list[tuple[int | None, int]]],
    n_samples: int = 1,
) -> dict[str, Any]:
    """Build a synthetic record matching gss_driver.py output structure.

    item_codes: {item_id: [(persona_code, truth_code), ...]} per sample.
    """
    per_item: dict[str, list[dict]] = {}
    for vid, samples in item_codes.items():
        sample_dicts = []
        for persona_code, truth in samples:
            if persona_code is None:
                sample_dicts.append({
                    "truth": truth, "persona_code": None,
                    "parse_fail": True, "treatment": None,
                    "abs_err": None, "skipped_missing_truth": False,
                })
            else:
                sample_dicts.append({
                    "truth": truth, "persona_code": persona_code,
                    "parse_fail": False, "treatment": "likert",
                    "abs_err": abs(persona_code - truth),
                    "skipped_missing_truth": False,
                })
        per_item[vid] = sample_dicts
    return {
        "respondent_id": rid, "condition": condition, "model": model,
        "n_samples": n_samples, "per_item_scores": per_item,
    }


def _self_test() -> None:
    """Synthetic-fixture self-test exercising all 16 conditions + Shapley + ANOVA.

    Construction: a 4-bin world where attitudinal contributes most, behavioral
    second, demographic third, psychological least. Per-bin contributions are
    additive in the synthetic data, so interactions ≈ 0. We verify:
    1. Shapley ranking matches the constructed contribution ordering.
    2. interaction_variance_share is small (since data is additive).
    3. Output schema fields all present.
    4. LOO rank matches Shapley rank under additive construction.
    5. Bootstrap CIs are non-degenerate.
    """
    print("=== shapley_decomposition self-test (synthetic 16-condition) ===\n")

    MODEL = "synthetic-test-model"
    # Bin contributions to MAE reduction (per-bin signal):
    #   attitudinal=0.5, behavioral=0.3, demographic=0.15, psychological=0.05
    # MAE under subset S = base_MAE - Σ_{B in S} contrib[B]
    contrib = {"demographic": 0.15, "behavioral": 0.30, "psychological": 0.05, "attitudinal": 0.50}
    base_mae = 1.5  # MAE when no bins included (worst case)

    # Build 50 respondents × 16 conditions, exactly additive (no discretization
    # noise). Each (rid, S) gets ONE item whose abs_err is the EXACT target
    # MAE, so per-respondent-mean-MAE = target_mae per subset. This cleanly
    # decomposes into bin main effects only; interactions ≈ 0.
    rng = _rng.Random(42)
    records: list[dict[str, Any]] = []
    n_resp = 50
    for rid in range(n_resp):
        per_resp_noise = rng.uniform(-0.05, 0.05)
        for S in _all_subsets(BINS):
            label = _subset_label(S)
            condition = f"shapley_{label}"
            target_mae = base_mae - sum(contrib[b] for b in S) + per_resp_noise
            target_mae = max(0.001, target_mae)
            # ONE Likert item with abs_err = target_mae directly (float allowed
            # since aggregator computes mean of abs_err values).
            per_item = {
                "FAKE_ITEM_LIKERT": [{
                    "truth": 4,
                    "persona_code": 4,
                    "parse_fail": False,
                    "treatment": "likert",
                    "abs_err": float(target_mae),
                    "skipped_missing_truth": False,
                }]
            }
            records.append({
                "respondent_id": rid, "condition": condition, "model": MODEL,
                "n_samples": 1, "per_item_scores": per_item,
            })

    out = shapley_decomposition(records, model=MODEL, seed=42, bootstrap_B=200)

    # Test 1: schema fields
    required_fields = (
        "_version", "_run_id", "model", "n_respondents", "n_conditions_run",
        "seed", "shapley_per_bin", "interaction_2way", "interaction_3way",
        "interaction_4way", "interaction_variance_share", "raw_condition_mae",
        "loo_consistency_check",
    )
    for f in required_fields:
        assert f in out, f"missing required field {f!r}"
    print(f"[1] schema fields present: {len(required_fields)}/16 ✓")

    # Test 2: 16 conditions present
    assert out["n_conditions_run"] == 16, f"expected 16 conditions, got {out['n_conditions_run']}"
    assert len(out["raw_condition_mae"]) == 16
    print(f"[2] 16 raw_condition_mae entries ✓")

    # Test 3: Shapley ranking matches construction
    sv = {b: out["shapley_per_bin"][b]["shapley_value"] for b in BINS}
    print(f"[3] Shapley values:")
    for b in sorted(BINS, key=lambda x: sv[x], reverse=True):
        print(f"     {b:<14}: {sv[b]:>+.4f} (rank={out['shapley_per_bin'][b]['rank']})")
    expected_order = ["attitudinal", "behavioral", "demographic", "psychological"]
    actual_order = sorted(BINS, key=lambda b: sv[b], reverse=True)
    assert actual_order == expected_order, (
        f"expected ranking {expected_order}, got {actual_order}"
    )
    print(f"     ✓ ranking matches synthetic contribution ordering")

    # Test 4: interaction_variance_share is small (additive construction)
    ivs = out["interaction_variance_share"]
    assert ivs < 0.20, f"expected low interaction share for additive data; got {ivs:.3f}"
    print(f"[4] interaction_variance_share = {ivs:.3f} (additive → low ✓)")

    # Test 5: LOO rank matches Shapley rank for additive data
    loo_match = out["loo_consistency_check"]["loo_rank_matches_shapley_rank"]
    assert loo_match, "LOO and Shapley rankings should match for additive data"
    print(f"[5] LOO rank matches Shapley rank (additive case): {loo_match} ✓")

    # Test 6: bootstrap CIs are non-degenerate (lo < hi)
    for b, vals in out["shapley_per_bin"].items():
        if vals["ci_lo"] is not None and vals["ci_hi"] is not None:
            assert vals["ci_lo"] <= vals["shapley_value"] <= vals["ci_hi"] + 1e-6, (
                f"CI must contain point estimate; got {b}: {vals}"
            )
    print(f"[6] bootstrap CIs all contain their point estimates ✓")

    # Test 7: empty input handled
    out_empty = shapley_decomposition([], model="empty-model", seed=42, bootstrap_B=10)
    assert out_empty.get("status") == "no_output"
    print(f"[7] empty-records input handled gracefully ✓")

    # Test 8: missing-subset input handled
    incomplete = [r for r in records if r["condition"] != "shapley_DBPA"]
    out_partial = shapley_decomposition(incomplete, model=MODEL, seed=42, bootstrap_B=10)
    assert out_partial.get("status") == "no_output"
    assert "missing" in out_partial.get("reason", "")
    print(f"[8] missing-subset input handled gracefully ✓")

    print(f"\n✓ ALL SHAPLEY DECOMPOSITION SELF-TESTS PASSED")


def _cli():
    p = argparse.ArgumentParser(
        description="Bin-level Shapley decomposition (Tier 1 secondary tool). "
                    "Locked spec: tier1_tool_schemas.md Tool 1 v0.2."
    )
    p.add_argument("--self-test", action="store_true",
                   help="run synthetic-fixture self-test (8 assertions)")
    p.add_argument("--input", type=Path, default=None,
                   help="path to records JSON (gss_driver.py output format)")
    p.add_argument("--output", type=Path, default=None,
                   help="path to write Shapley decomposition JSON output")
    p.add_argument("--model", type=str, default=None,
                   help="filter records to this model slug (default: unique model)")
    p.add_argument("--seed", type=int, default=42, help="bootstrap seed (locked at 42)")
    p.add_argument("--bootstrap-B", type=int, default=BOOTSTRAP_B_DEFAULT,
                   help=f"bootstrap replicates (default {BOOTSTRAP_B_DEFAULT})")
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
    records = json.loads(args.input.read_text())
    out = shapley_decomposition(records, model=args.model, seed=args.seed, bootstrap_B=args.bootstrap_B)
    if args.output is None:
        print(json.dumps(out, indent=2))
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(out, indent=2))
        print(f"✓ wrote {args.output}")
