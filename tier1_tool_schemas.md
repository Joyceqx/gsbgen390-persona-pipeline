# Tier 1 Discovery Tool — Output Schemas (lean version, 2026-05-09)

**Version**: v0.2 (slimmed per Codex audit 2026-05-09)
**Locked**: 2026-05-09 — schemas frozen; implementations on Day 3-4
**Purpose**: Lock the OUTPUT SCHEMA of each secondary discovery tool BEFORE theory-interpretation framing is written, so the paper's main contribution rests on stable, pre-specified numeric outputs.

This file is the commitment device for Phase 1's secondary analyses. The primary 4-bin LOO is locked elsewhere (`gss_phase1_design.md` §4 + §10); this file covers only the two secondary tools Codex's lean-design audit (2026-05-09) endorsed:

1. **Bin-level Shapley decomposition** — robustness re-aggregation of the 4-bin LOO
2. **Attitudinal-bin battery LOO** — within-bin interpretability, conditional on attitudinal dominance

Tools considered and **explicitly deferred** (with their schemas removed from this lean version): RSA, permutation importance, theory-derived similarity, "Friedman's H"-style interaction variance from custom definitions. See `gss_phase1_design.md` §13.4 for the explicit deferral list.

---

## Anti-HARKing role of this file

The most subtle HARKing risk is fitting prediction *language* to data: if a tool outputs `{bin: {value, ci_lo, ci_hi, rank}}` and the paper's claims use slightly different aggregation, there is implicit freedom to align language to whichever framing happens to look favorable. Locking schemas first **forces all secondary-analysis claims to commit to specific quantitative form** before any LLM call is made.

Each schema below is fully specified: every field name, every type, every aggregation rule. Any change to a schema after Phase 1a fires must be an OSF amendment.

---

## Tool 1 — `shapley_decomposition.py`

**Purpose**: Decompose the 4-bin contribution to Likert MAE into Shapley values that account for all possible coalitions of bins, plus 2-way / 3-way / 4-way interaction terms. Acts as a robustness check on the primary 4-bin LOO ranking — if Shapley values disagree with LOO ΔMAE rankings, that's evidence of bin-bin interactions worth reporting.

**Algorithm**: Enumerate all 2⁴ = 16 conditions (include/exclude each of the 4 bins). For each condition, compute respondent-macro Likert MAE on the Phase 1a primary_eval items. Shapley value for bin B is the average of `MAE(coalition without B) - MAE(coalition ∪ {B})` over all 8 coalitions that don't already contain B. Interaction terms come from standard ANOVA-style decomposition of the 16 condition MAEs.

**When run**: Phase 1a (N=100), once per cheap-panel model (4× total). Optionally re-run after Phase 1b (N=1500) on the §12.2-selected model for stronger CIs.

**Output schema** (one JSON file per `(model, n_respondents, seed)`):

```json
{
  "_version": "0.2",
  "_run_id": "phase1a_shapley_qwen-2.5_n100_seed42",
  "_locked_spec_path": "tier1_tool_schemas.md",
  "model": "qwen/qwen-2.5-72b-instruct",
  "n_respondents": 100,
  "n_primary_eval_items": 12,
  "n_conditions_run": 16,
  "seed": 42,

  "shapley_per_bin": {
    "demographic":   {"shapley_value": 0.043, "ci_lo": 0.018, "ci_hi": 0.071, "rank": 4},
    "behavioral":    {"shapley_value": 0.062, "ci_lo": 0.029, "ci_hi": 0.099, "rank": 3},
    "psychological": {"shapley_value": 0.084, "ci_lo": 0.041, "ci_hi": 0.131, "rank": 2},
    "attitudinal":   {"shapley_value": 0.211, "ci_lo": 0.158, "ci_hi": 0.267, "rank": 1}
  },

  "interaction_2way": {
    "demographic*behavioral":      {"value": 0.012, "ci_lo": -0.008, "ci_hi": 0.034},
    "demographic*psychological":   {"value": 0.005, "ci_lo": -0.011, "ci_hi": 0.022},
    "demographic*attitudinal":     {"value": 0.018, "ci_lo": -0.004, "ci_hi": 0.041},
    "behavioral*psychological":    {"value": 0.022, "ci_lo": 0.003,  "ci_hi": 0.044},
    "behavioral*attitudinal":      {"value": 0.031, "ci_lo": 0.011,  "ci_hi": 0.054},
    "psychological*attitudinal":   {"value": 0.045, "ci_lo": 0.022,  "ci_hi": 0.071}
  },

  "interaction_3way": {
    "demographic*behavioral*psychological":   {"value": 0.008, "ci_lo": -0.012, "ci_hi": 0.030},
    "demographic*behavioral*attitudinal":     {"value": 0.014, "ci_lo": -0.005, "ci_hi": 0.035},
    "demographic*psychological*attitudinal":  {"value": 0.009, "ci_lo": -0.011, "ci_hi": 0.030},
    "behavioral*psychological*attitudinal":   {"value": 0.019, "ci_lo": 0.001,  "ci_hi": 0.040}
  },

  "interaction_4way": {
    "demographic*behavioral*psychological*attitudinal": {"value": 0.006, "ci_lo": -0.014, "ci_hi": 0.026}
  },

  "interaction_variance_share": 0.27,
  "_interaction_variance_share_definition": "Sum of squared 2-way + 3-way + 4-way interaction terms, divided by total sum of squared (main + interaction) terms. Range [0, 1]. Higher = more variance attributable to interactions vs main effects. NOTE: this is a clearly-named non-standard metric. It is NOT the Friedman & Popescu (2008) H-statistic, which is a different quantity defined on partial-dependence functions of tree-based models and is not implemented here.",

  "raw_condition_mae": {
    "0000_no_bins":       {"mae": 1.420, "n": 100},
    "1000_demo_only":     {"mae": 1.341, "n": 100},
    "...":                "(all 16 conditions)"
  },

  "loo_consistency_check": {
    "loo_rank_matches_shapley_rank": true,
    "_definition": "For each bin, does its 4-bin LOO ΔMAE rank equal its Shapley rank? If false, the LOO ranking depends on bin interactions — flag for explicit Discussion.",
    "per_bin_rank_match": {
      "demographic":   true,
      "behavioral":    true,
      "psychological": true,
      "attitudinal":   true
    }
  },

  "ci_method": "paired_bootstrap_respondent_level_B1000",
  "alpha": 0.05
}
```

**Reporting role**: robustness re-aggregation of the same primary 4-bin estimand. The primary headline remains the 4-bin LOO ΔMAE; Shapley values are reported alongside in the same table to show the LOO ranking is robust to interactions. If `loo_consistency_check.loo_rank_matches_shapley_rank == false`, the paper's Discussion explicitly flags this as a finding (LOO is exploiting bin-redundancy that Shapley penalizes).

**Forbidden uses** (anti-overclaim per §13.1):
- Do NOT call `interaction_variance_share` "Friedman's H."
- Do NOT interpret 2-way/3-way interaction terms as theoretical findings unless their CIs exclude zero AND the interaction has a substantively-named direction.
- Do NOT promote Shapley results to "primary" — they are robustness on the same primary estimand.

---

## Tool 2 — `battery_loo.py` (attitudinal bin only; conditional)

**Purpose**: Conditional on the 4-bin LOO confirming attitudinal-bin dominance, identify which specific attitude batteries within the bin drive the prediction signal. Within-bin interpretability — answers "if attitudinal matters most, which attitudes specifically?"

**Trigger condition** (locked): only run if `shapley_per_bin.attitudinal.rank == 1` AND attitudinal-bin LOO ΔMAE > LOO ΔMAE for each of the other three bins. If attitudinal does NOT dominate, this tool is skipped and the paper reports "battery-level decomposition not run because attitudinal-bin dominance was not observed."

**Algorithm**: For each of the ~10-11 attitudinal-bin batteries (per `gss_battery_map.json`), drop the entire battery from the persona prompt for ALL 12 primary_eval items (in addition to R1 per-item battery exclusion which already applies). Re-run prediction. Compute respondent-macro Likert ΔMAE vs FULL. Bootstrap CI at respondent level (paired bootstrap, B=1000, seed=42). Apply Holm-Bonferroni at α=0.05 across the within-attitudinal battery family.

**When run**: Phase 1c (post Phase 1b headline) on the §12.2-selected 1b model only. ~10 batteries × 1500 respondents × 12 items × 1 model ≈ $25-30 incremental.

**Output schema** (one JSON file per `(model, n_respondents, seed)`):

```json
{
  "_version": "0.2",
  "_run_id": "phase1c_battery_loo_attitudinal_qwen-2.5_n1500_seed42",
  "_locked_spec_path": "tier1_tool_schemas.md",
  "model": "qwen/qwen-2.5-72b-instruct",
  "n_respondents": 1500,
  "seed": 42,
  "scope": "attitudinal_bin_only",
  "trigger_satisfied": true,
  "_trigger_definition": "shapley_per_bin.attitudinal.rank == 1 in Phase 1a Shapley output AND 4-bin LOO ΔMAE for attitudinal > each other bin's LOO ΔMAE",

  "battery_loo_delta": {
    "abortion":                     {"delta_mae": 0.041, "ci_lo": 0.022, "ci_hi": 0.061, "rank": 1, "holm_significant": true,  "p_holm_adjusted": 0.003},
    "confidence_in_institutions":   {"delta_mae": 0.029, "ci_lo": 0.012, "ci_hi": 0.045, "rank": 2, "holm_significant": true,  "p_holm_adjusted": 0.018},
    "national_priorities":          {"delta_mae": 0.024, "ci_lo": 0.008, "ci_hi": 0.041, "rank": 3, "holm_significant": true,  "p_holm_adjusted": 0.029},
    "racial_inequality_perception": {"delta_mae": 0.018, "ci_lo": 0.001, "ci_hi": 0.034, "rank": 4, "holm_significant": false, "p_holm_adjusted": 0.071},
    "economic_help":                {"delta_mae": 0.015, "ci_lo": -0.002,"ci_hi": 0.031, "rank": 5, "holm_significant": false, "p_holm_adjusted": 0.142},
    "...": "(all attitudinal-bin batteries)"
  },

  "n_batteries_holm_significant": 3,
  "n_batteries_tested": 11,
  "alpha_after_holm_correction": "0.05 within attitudinal-bin battery family",

  "ci_method": "paired_bootstrap_respondent_level_B1000_seed42"
}
```

**Reporting role**: descriptive within-bin decomposition. The paper's Table 4 reports the Holm-significant batteries with their ΔMAE + CIs. The Discussion qualitatively notes which batteries dominate. NOT a co-primary headline — the paper's primary claim is the bin-level finding from §10.

**Forbidden uses** (anti-overclaim per §13.2):
- Do NOT run this tool if the trigger condition is not met. Reporting "we considered battery LOO but the precondition was not met" is the correct null behavior.
- Do NOT interpret battery-level findings as theoretical claims — that goes through §13.3 / `theory_interpretation_guide.md` as discussion-level interpretation.

---

## Cross-tool naming conventions (locked)

- **Bin names**: `demographic`, `behavioral`, `psychological`, `attitudinal` (lowercase, underscored where multi-word; matches `gss_feature_taxonomy.json` keys)
- **Battery names**: lowercase, underscored, matches `gss_battery_map.json` keys
- **Run-id format**: `{phase}_{tool}_{model_short}_{n}_{seed}` — matches the locked I-10 reproducibility filename convention
- **Seed**: always 42 unless `--force-non-canonical-seed` (per `gss_driver.py`)
- **CI method**: `paired_bootstrap_respondent_level_B1000` for ablation deltas

## Implementation order (Day 3-4 of slim build)

1. Build `shapley_decomposition.py` — needs the `gss_driver.py` 16-condition enumeration and the standard ANOVA-style interaction decomposition.
2. Build `battery_loo.py` — wraps existing `gss_driver.py` with battery-level exclude_vars; runs only post-1b after trigger condition is checked.

## What this file does NOT do

- Does NOT specify implementations (algorithms above are sketches; full algorithms in the implementation files).
- Does NOT lock RSA, permutation importance, theory-derived similarity, or other deferred tools — those are listed in `gss_phase1_design.md` §13.4 as future-work, NOT in the OSF pre-registration.
- Does NOT lock theory-interpretation framing — that's `theory_interpretation_guide.md` (Discussion-section memo, NOT a confirmatory horse race).
- Does NOT govern OSF success/refutation criteria for theories — there are none in the slim design; theory enters Discussion only.

## Deferred tool schemas (NOT in lean Phase 1)

The following tools were considered and **explicitly deferred** under the 2026-05-09 lean-design lock (`gss_phase1_design.md` §13.4):

| Tool | Status | Reason |
|---|---|---|
| RSA (representational similarity analysis) | DEFERRED | Statistically thin at 12-dim response vectors; primary contribution does not require it; adds tool-stack burden. May appear as future work. |
| Permutation importance (R2 extension) | DEFERRED | The R2 partition test (§9c.4) covers leakage hygiene; per-variable variation is decoration. R2 model itself stays. |
| Theory-derived similarity matrices | DEFERRED | Would convert Discussion into preregistered confrontation; lean design keeps theory in Discussion only. |
| Friedman & Popescu (2008) H-statistic | DEFERRED | Proper implementation requires partial-dependence machinery from tree-based models; we use a clearly-named non-standard `interaction_variance_share` instead. |
| Stage 3 refinement experiments | DEFERRED | Theory-organized prompts / counterfactual perturbation; future-work for a follow-up paper. |

Schemas for these tools, if implemented in the future, will be added to a v0.3 of this file or to a separate `future_work_schemas.md`.
