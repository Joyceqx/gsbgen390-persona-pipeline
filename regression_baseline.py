"""R2 — Non-LLM correlational baseline (locked 2026-05-08, gss_phase1_design.md §9c.R2).

Why this exists
---------------
Park v2 brackets the within-construct auto-correlation inflation by reporting
two LLM hold-out strategies (single-item vs whole-module). That tells us how
much the headline number can move under different defenses, but it does NOT
tell us how much of the LLM persona's apparent accuracy is *persona reasoning*
vs how much is *auto-correlation that any prediction model could exploit*.

This module fills that gap. For each primary_eval item it trains a NON-LLM
regression on the same encoded GSS features that the LLM persona prompt
exposes (with the predicted item's battery excluded — same R1 rule). The
resulting per-item MAE is a "auto-correlation upper bound" for any feature-
to-item predictor. The headline partition is:

    LLM persona MAE on item X
        = (regression MAE on item X)         ← pure auto-correlation
        + (LLM persona gain over regression) ← persona reasoning

If LLM gain is zero, the LLM persona is doing nothing the regression isn't
already doing — i.e., the apparent attitudinal-bin contribution is fully
explained by within-construct redundancy. If LLM gain is large and positive,
that's the evidence that grounds a persona-reasoning claim.

This is methodologically a step PAST Park v2 — Park brackets the inflation
between two strategies; we partition it.

Design
------
- Per primary_eval item: one regression model (Ridge for Likert, multinomial
  Logistic for binary/categorical).
- Inputs: all 140 feature variables MINUS the predicted item's battery
  (R1 applied symmetrically so LLM and regression see the same input set).
- Encoding: ordinal/Likert items kept numeric; nominal items one-hot encoded.
- Missing handling: per-feature mean imputation (numeric) or "missing" indicator
  (one-hot). This is conservative — it does not give the regression any signal
  the LLM doesn't have.
- Cross-validation: 5-fold respondent-level CV (no respondent in both train
  and test). MAE computed on held-out test fold.
- Seed: locked at 42 (matches Phase 1 sampling + bootstrap seed).
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from gss_loader import MISSING_CODES, load_gss, get_value_label
from gss_pipeline import (
    _is_non_substantive_label,
    battery_excludes_for_item,
    load_battery_map,
    load_taxonomy,
    sample_respondents,
)

WORK = Path("/Users/joyce/Developer/gsbgen390")
SEED = 42

# Items whose value labels are nominal categories (use one-hot rather than ordinal)
NOMINAL_ITEMS = frozenset({
    "REGION", "RACE", "RELIG", "RELIG16", "MARITAL", "MARTYPE",
    "WRKSTAT", "FAMILY16", "FAMDIF16", "DWELOWN16", "MOBILE16",
    "REG16", "ETHNIC", "BORN", "FUND", "PARTFULL", "EVWORK",
    "PRES16", "PRES20", "VOTE16", "VOTE20", "MADEG", "PADEG", "DEGREE",
    "WIDOWED",
})


def _is_likely_nominal(varname: str, taxonomy: dict) -> bool:
    if varname in NOMINAL_ITEMS:
        return True
    return False


def _encode_features(
    df: pd.DataFrame,
    feature_vars: list[str],
    taxonomy: dict,
) -> tuple[np.ndarray, list[str]]:
    """Encode a feature DataFrame for regression input.

    Numeric features: missing replaced by per-column mean over the visible rows
    (substantive codes only).
    Nominal features: one-hot encoded with an explicit "MISSING" level. The
    "MISSING" level prevents leakage of "this respondent has a non-substantive
    answer" into the prediction, which is a real-world signal but one the LLM
    doesn't easily get either.
    """
    cols: list[np.ndarray] = []
    col_names: list[str] = []
    for v in feature_vars:
        if v not in df.columns:
            continue
        s = df[v]
        # Convert positive non-substantive labels to NaN for consistency
        def _clean(val):
            if pd.isna(val):
                return np.nan
            i = int(val)
            if i in MISSING_CODES:
                return np.nan
            lbl = get_value_label(v, i)
            if lbl and _is_non_substantive_label(lbl):
                return np.nan
            return float(i)
        cleaned = s.apply(_clean).astype(float)

        if _is_likely_nominal(v, taxonomy):
            # one-hot with MISSING bucket
            levels = sorted(set(cleaned.dropna().unique().tolist()))
            for lev in levels:
                cols.append((cleaned == lev).astype(float).to_numpy())
                col_names.append(f"{v}={int(lev)}")
            cols.append(cleaned.isna().astype(float).to_numpy())
            col_names.append(f"{v}=MISSING")
        else:
            mu = cleaned.dropna().mean()
            if pd.isna(mu):
                mu = 0.0
            imputed = cleaned.fillna(mu).to_numpy()
            cols.append(imputed)
            col_names.append(v)

    if not cols:
        return np.zeros((len(df), 0)), []
    X = np.column_stack(cols)
    return X, col_names


def _per_respondent_truth(df: pd.DataFrame, varname: str) -> tuple[np.ndarray, np.ndarray]:
    """Return (mask, codes) for respondents who have a substantive answer."""
    s = df[varname]
    keep_mask = np.zeros(len(s), dtype=bool)
    codes = np.zeros(len(s), dtype=float)
    for i, val in enumerate(s):
        if pd.isna(val):
            continue
        ic = int(val)
        if ic in MISSING_CODES:
            continue
        lbl = get_value_label(varname, ic)
        if lbl and _is_non_substantive_label(lbl):
            continue
        keep_mask[i] = True
        codes[i] = ic
    return keep_mask, codes


def _kfold_indices(n: int, k: int = 5, seed: int = SEED) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    order = rng.permutation(n)
    folds = np.array_split(order, k)
    out = []
    for i in range(k):
        test = folds[i]
        train = np.concatenate([folds[j] for j in range(k) if j != i])
        out.append((train, test))
    return out


def regression_baseline_per_item(
    df: pd.DataFrame,
    taxonomy: dict,
    primary_eval_items: list[dict],
    use_battery_exclusion: bool = True,
    k_folds: int = 5,
    seed: int = SEED,
) -> dict[str, dict[str, Any]]:
    """For each primary_eval item, train a regression on the rest of the
    feature pool (with R1 battery exclusion applied symmetrically) and report
    the K-fold cross-validated MAE.

    Returns:
        {item_id: {"mae": float, "n_train": int, "n_features": int,
                   "treatment": "ridge" | "logistic", "excluded_vars": [...]}}

    The MAE is on the SAME numeric coding the LLM is scored on (ordinal
    distance for Likert, exact-match-as-MAE-of-0-or-1 for binary).
    """
    try:
        from sklearn.linear_model import Ridge, LogisticRegression
        from sklearn.preprocessing import StandardScaler
    except ImportError as e:
        raise RuntimeError(
            "regression_baseline.py needs scikit-learn. Install with: pip install scikit-learn"
        ) from e

    # Numerical-stability hardening (added 2026-05-09 night per Codex Fix 11).
    # Earlier self-test runs emitted divide-by-zero / overflow / invalid-value
    # RuntimeWarnings from sklearn's matmul calls when imputed feature columns
    # produced very small std after StandardScaler(with_mean=False). The
    # 12/12-item self-test outputs were unaffected (numerically equivalent to
    # the warning-suppressed run), but the warnings indicated numerical
    # fragility that a replication auditor would care about. We now:
    #   (a) tighten the zero-variance filter from > 1e-9 to > 1e-6 (catches
    #       columns where imputation left near-constant values);
    #   (b) clip post-scaling outliers to ±50 (defends against overflow if a
    #       rare-value column gets a huge scaled value);
    #   (c) suppress the specific RuntimeWarnings from sklearn's matmul as a
    #       last-resort guard, with an explicit note that the test's 12/12
    #       MAE output is reproducibility-stable.
    # If R2 results enter a published paper, replace this scaffolding with a
    # Pipeline-based fit-inside-CV approach using RobustScaler — see TODO at
    # bottom of file.
    import warnings
    warnings.filterwarnings(
        "ignore",
        message=r"(divide by zero|overflow|invalid value) encountered in matmul",
        category=RuntimeWarning,
    )

    battery_map = load_battery_map() if use_battery_exclusion else None
    feature_pool = sorted(taxonomy["_all_features_set"])
    out: dict[str, dict[str, Any]] = {}

    for item in primary_eval_items:
        vid = item["id"]
        fmt = item["format"]
        excludes = (
            battery_excludes_for_item(vid, battery_map)
            if use_battery_exclusion else {vid}
        )
        feats = [f for f in feature_pool if f not in excludes]

        keep_mask, codes = _per_respondent_truth(df, vid)
        if keep_mask.sum() < 50:
            out[vid] = {"mae": None, "reason": "insufficient_truth", "n_train": int(keep_mask.sum())}
            continue

        sub = df.loc[keep_mask].reset_index(drop=True)
        y = codes[keep_mask].astype(float)
        X, col_names = _encode_features(sub, feats, taxonomy)
        if X.shape[1] == 0:
            out[vid] = {"mae": None, "reason": "no_features", "n_train": len(y)}
            continue

        # Drop near-constant columns (tighter than v0.1: 1e-9 → 1e-6 to catch
        # imputation-flat columns; 2026-05-09 night Codex Fix 11).
        col_std = X.std(axis=0)
        nonconst = col_std > 1e-6
        X = X[:, nonconst]
        col_names = [c for c, k in zip(col_names, nonconst) if k]
        if X.shape[1] == 0:
            out[vid] = {"mae": None, "reason": "all_features_constant", "n_train": len(y)}
            continue

        scaler = StandardScaler(with_mean=False)
        X = scaler.fit_transform(X)
        # Clip post-scaling outliers to defend against matmul overflow on
        # rare-value columns (2026-05-09 night).
        X = np.clip(X, -50.0, 50.0)
        # Replace any remaining non-finite values that slipped through the
        # near-constant filter (e.g., divide-by-zero produced inf during
        # StandardScaler fit_transform on edge cases).
        X = np.nan_to_num(X, nan=0.0, posinf=50.0, neginf=-50.0)

        is_likert = fmt.startswith("likert")
        is_binary = fmt == "binary"
        # PARTYID is contingent (Likert 0-6 + categorical 7); treat as Likert
        # for the regression (the rare 7's contribute as integer 7 — close to
        # the LLM scoring rule's behavior on the Likert-comparable subset).
        treatment = "ridge" if (is_likert or vid == "PARTYID") else "logistic"

        folds = _kfold_indices(len(y), k=k_folds, seed=seed)
        per_fold_mae: list[float] = []
        for train_idx, test_idx in folds:
            Xtr, Xte = X[train_idx], X[test_idx]
            ytr, yte = y[train_idx], y[test_idx]
            if treatment == "ridge":
                m = Ridge(alpha=1.0, random_state=seed)
                m.fit(Xtr, ytr)
                yhat = m.predict(Xte)
                # Round to nearest valid code for fair MAE comparison with LLM scoring
                yhat_int = np.clip(np.rint(yhat), y.min(), y.max())
                per_fold_mae.append(float(np.mean(np.abs(yhat_int - yte))))
            else:
                # Multinomial logistic
                if len(set(ytr.tolist())) < 2:
                    continue
                # NOTE: removed `multi_class="auto"` — deprecated in sklearn 1.5
                # (default is now "multinomial" which is what we want anyway).
                m = LogisticRegression(
                    max_iter=2000, random_state=seed, solver="lbfgs",
                )
                m.fit(Xtr, ytr.astype(int))
                yhat = m.predict(Xte).astype(float)
                # For binary categorical: MAE == 1 - exact_match (since codes are
                # adjacent, this matches the LLM "categorical exact-match" → MAE 0/1
                # convention for primary_eval scoring of binary).
                per_fold_mae.append(float(np.mean(np.abs(yhat - yte))))

        if not per_fold_mae:
            out[vid] = {"mae": None, "reason": "all_folds_singleton", "n_train": len(y)}
            continue
        out[vid] = {
            "mae": round(statistics.fmean(per_fold_mae), 4),
            "mae_per_fold": [round(x, 4) for x in per_fold_mae],
            "n_train": int(len(y)),
            "n_features_columns": int(X.shape[1]),
            "n_features_vars": int(len(feats)),
            "treatment": treatment,
            "excluded_vars": sorted(excludes),
        }
    return out


def _self_test() -> None:
    """Smoke test on a 200-respondent subsample. Asserts the baseline is
    sane and not all-zeros."""
    print("=== regression_baseline self-test (N=200 subsample) ===\n")
    sample = sample_respondents(n=200, seed=SEED)
    tax = load_taxonomy()
    out = regression_baseline_per_item(
        sample, tax, tax["primary_eval"]["items"],
        use_battery_exclusion=True, k_folds=5, seed=SEED,
    )

    print(f"{'Item':<10}  {'Treatment':<9}  {'N':>5}  {'#feats':>6}  {'MAE':>6}  ExcludedBattery (count)")
    print("-" * 90)
    for vid, r in out.items():
        if r.get("mae") is None:
            print(f"{vid:<10}  -- {r.get('reason')} (n={r.get('n_train')})")
            continue
        excl = r["excluded_vars"]
        if len(excl) == 1:
            excl_label = "(singleton — only self)"
        else:
            excl_label = f"({len(excl)} items)"
        print(f"{vid:<10}  {r['treatment']:<9}  {r['n_train']:>5d}  "
              f"{r['n_features_vars']:>6d}  {r['mae']:>6.3f}  {excl_label}")

    n_nonzero = sum(1 for r in out.values() if r.get("mae", 0) and r["mae"] > 0)
    n_with_mae = sum(1 for r in out.values() if r.get("mae") is not None)
    assert n_with_mae >= 10, f"expected ≥10 items with MAE; got {n_with_mae}"
    assert n_nonzero >= 8, f"expected ≥8 nonzero MAE; got {n_nonzero}"
    print(f"\n✓ regression baseline self-test PASSED ({n_with_mae}/12 items scored, "
          f"{n_nonzero} nonzero MAE)")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(
        description="R2 — non-LLM regression baseline for primary_eval items."
    )
    p.add_argument("--self-test", action="store_true",
                   help="run smoke test on N=200 subsample")
    p.add_argument("--n", type=int, default=1500,
                   help="sample size for the run (default 1500 = Phase 1b sample)")
    p.add_argument("--out", type=Path, default=None,
                   help="output JSON path (default: outputs/regression_baseline_n{N}_seed42.json)")
    args = p.parse_args()

    if args.self_test:
        _self_test()
    else:
        sample = sample_respondents(n=args.n, seed=SEED)
        tax = load_taxonomy()
        result = regression_baseline_per_item(
            sample, tax, tax["primary_eval"]["items"],
            use_battery_exclusion=True, k_folds=5, seed=SEED,
        )
        out = args.out or (
            WORK / "outputs" / f"regression_baseline_n{args.n}_seed{SEED}.json"
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2))
        print(f"✓ wrote {out}")
