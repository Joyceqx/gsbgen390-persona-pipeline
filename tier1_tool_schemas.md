# Tier 1 Discovery Tool — Output Schemas (lean version, 2026-05-09)

**Version**: v0.2 (slimmed per Codex audit 2026-05-09)
**Locked**: 2026-05-09 — schemas frozen; implementations on Day 3-4
**Purpose**: Lock the OUTPUT SCHEMA of each secondary discovery tool BEFORE theory-interpretation framing is written, so the paper's main contribution rests on stable, pre-specified numeric outputs.

This file is the commitment device for Phase 1's secondary analyses. The primary 4-bin LOO is locked elsewhere (`gss_phase1_design.md` §4 + §10); this file covers only the two secondary tools Codex's lean-design audit (2026-05-09) endorsed:

1. **Bin-level Shapley decomposition** — robustness re-aggregation of the 4-bin LOO
2. **Battery LOO across all 4 bins** — co-primary mechanistic, unconditional, nested Holm + joint-34 sensitivity

Tools considered and **explicitly deferred** (with their schemas removed from this lean version): RSA, permutation importance, theory-derived similarity, "Friedman's H"-style interaction variance from custom definitions. See `gss_phase1_design.md` §13.4 for the explicit deferral list.

---

## Anti-HARKing role of this file

The most subtle HARKing risk is fitting prediction *language* to data: if a tool outputs `{bin: {value, ci_lo, ci_hi, rank}}` and the paper's claims use slightly different aggregation, there is implicit freedom to align language to whichever framing happens to look favorable. Locking schemas first **forces all secondary-analysis claims to commit to specific quantitative form** before any LLM call is made.

Each schema below is fully specified: every field name, every type, every aggregation rule. Any change to a schema after Phase 1a fires must be an OSF amendment.

---

## Tool 1 — `shapley_decomposition.py`

**Purpose**: Decompose the 4-bin contribution to Likert MAE into Shapley values that account for all possible coalitions of bins, plus 2-way / 3-way / 4-way interaction terms. Acts as a robustness check on the primary 4-bin LOO ranking — if Shapley values disagree with LOO ΔMAE rankings, that's evidence of bin-bin interactions worth reporting.

**Algorithm**: Enumerate all 2⁴ = 16 conditions (include/exclude each of the 4 bins). For each condition, compute respondent-macro Likert MAE on the Phase 1a primary_eval items. Shapley value for bin B is the average of `MAE(coalition without B) - MAE(coalition ∪ {B})` over all 8 coalitions that don't already contain B. Interaction terms come from standard ANOVA-style decomposition of the 16 condition MAEs.

**When run**: Phase 1a (N=200), once per cheap-panel model (4× total). Optionally re-run after Phase 1b (N=3,309) on the §12.2-selected model for stronger CIs.

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

  "ci_method": "paired_bootstrap_respondent_level_B10000_BCa",
  "alpha": 0.05
}
```

**Reporting role**: robustness re-aggregation of the same primary 4-bin estimand. The primary headline remains the 4-bin LOO ΔMAE; Shapley values are reported alongside in the same table to show the LOO ranking is robust to interactions. If `loo_consistency_check.loo_rank_matches_shapley_rank == false`, the paper's Discussion explicitly flags this as a finding (LOO is exploiting bin-redundancy that Shapley penalizes).

**Forbidden uses** (anti-overclaim per §13.1):
- Do NOT call `interaction_variance_share` "Friedman's H."
- Do NOT interpret 2-way/3-way interaction terms as theoretical findings unless their CIs exclude zero AND the interaction has a substantively-named direction.
- Do NOT promote Shapley results to "primary" — they are robustness on the same primary estimand.

---

## Tool 2 — `battery_loo.py` (all 4 bins; unconditional co-primary, locked 2026-05-09 evening)

**Purpose**: Identify which **construct-level clusters** within each feature bin drive LLM persona prediction. Co-primary mechanistic finding alongside the 4-bin LOO's broad finding.

**Scope**: 34 batteries across all 4 bins per `gss_battery_map.json` v0.2 (7 demographic + 10 behavioral + 2 psychological + 15 attitudinal). Singletons (17 items) are NOT tested per `gss_phase1_design.md` §13.4 (variable-level statistical power too low + would inflate multiplicity).

**Unconditional**: runs regardless of which bin dominates the 4-bin LOO. The previous "conditional on attitudinal dominance" trigger was removed 2026-05-09 evening when Battery LOO was promoted to co-primary.

**Algorithm**: For each of the 34 batteries B, drop the entire battery from the persona prompt for ALL 12 primary_eval items (in addition to R1 per-item battery exclusion — these are independent operations). Re-run prediction. Compute respondent-macro Likert ΔMAE vs FULL. Bootstrap CI at respondent level (paired bootstrap, **B=10000, seed=42, BCa via scipy with percentile fallback for degenerate inputs** — locked 2026-05-09 night per Codex N5/N6 audit). Apply **two Holm corrections in parallel**:
1. **Nested Holm-Bonferroni primary** within each bin's battery family — 4 separate corrections, NOT joint:
   - Demographic family: 7 tests, smallest p < α/7 = 0.0071
   - Behavioral family: 10 tests, smallest p < α/10 = 0.0050
   - Psychological family: 2 tests, smallest p < α/2 = 0.025
   - Attitudinal family: 15 tests, smallest p < α/15 = 0.0033
2. **Joint-34 Holm sensitivity** across all 34 batteries simultaneously — smallest p < α/34 = 0.00147. Used as a gate for cross-bin claims (per `gss_phase1_design.md` §8.8).

**Within-bin claims** (e.g., *"abortion is the strongest battery in the attitudinal bin"*) use the **nested Holm** primary correction.
**Cross-bin claims** (e.g., *"abortion is the strongest battery overall"*) require **joint-34 Holm sensitivity** support; without it, cross-bin language is descriptive only.

**Practical-effect-size thresholds** (per `gss_phase1_design.md` §8.9; locked 2026-05-09 evening):
- `small / descriptive`: ΔMAE < 0.02
- `modest`: 0.02 ≤ ΔMAE < 0.05
- `substantive`: ΔMAE ≥ 0.05

A finding is "substantively meaningful" only if **both** Holm-significant within its family AND practical-effect ≥ "modest" with bootstrap CI excluding the small-effect boundary.

**When run**: Phase 1c (post Phase 1b headline) on the §12.2-selected 1b model only. 34 batteries × **3,309 respondents** × 12 items × 1 model ≈ **~$481 incremental** (locked 2026-05-09 night per Audit-3 + Joyce decision; supersedes the earlier ~$218 estimate at N=1,500 and the original ~$50-60 back-of-envelope). See `gss_phase1_design.md` §5 for the full Phase 1 budget (~$756 total under Option A: cheap panel primary-only; sensitivity_eval anchor-only).

**Output schema** (one JSON file per `(model, n_respondents, seed)`):

```json
{
  "_version": "0.4",
  "_run_id": "phase1c_battery_loo_qwen-2.5_n3309_seed42",
  "_locked_spec_path": "tier1_tool_schemas.md",
  "model": "qwen/qwen-2.5-72b-instruct",
  "n_respondents": 3309,
  "seed": 42,
  "scope": "all_4_bins_34_batteries",
  "_scope_definition": "All 34 batteries per gss_battery_map.json v0.2: 7 demographic + 10 behavioral + 2 psychological + 15 attitudinal. Singletons NOT tested (deferred per §13.4).",

  "practical_thresholds": {
    "small_lt": 0.02,
    "modest_range": [0.02, 0.05],
    "substantive_gte": 0.05
  },

  "battery_loo_per_bin": {
    "demographic": {
      "n_batteries": 7,
      "alpha_within_bin_holm": 0.05,
      "holm_critical_smallest_p_within_bin": 0.00714,
      "results": {
        "own_education": {
          "delta_mae": 0.022, "ci_lo": 0.008, "ci_hi": 0.038,
          "rank_in_bin": 1,
          "p_holm_within_bin": 0.003, "holm_significant_within_bin": true,
          "p_holm_joint_34": 0.041, "holm_significant_joint_34": true,
          "effect_size_label": "modest",
          "substantively_meaningful": true,
          "n_items_in_battery": 2, "delta_mae_per_item": 0.0110
        },
        "parental_education": {
          "delta_mae": 0.018, "ci_lo": 0.005, "ci_hi": 0.032,
          "rank_in_bin": 2,
          "p_holm_within_bin": 0.012, "holm_significant_within_bin": true,
          "p_holm_joint_34": 0.071, "holm_significant_joint_34": false,
          "effect_size_label": "small",
          "substantively_meaningful": false,
          "n_items_in_battery": 4, "delta_mae_per_item": 0.0045
        },
        "...": "(all 7 demographic batteries)"
      }
    },
    "behavioral":    {"n_batteries": 10, "alpha_within_bin_holm": 0.05, "holm_critical_smallest_p_within_bin": 0.005,   "results": "(see schema pattern above)"},
    "psychological": {"n_batteries":  2, "alpha_within_bin_holm": 0.05, "holm_critical_smallest_p_within_bin": 0.025,   "results": "(see schema pattern above)"},
    "attitudinal":   {"n_batteries": 15, "alpha_within_bin_holm": 0.05, "holm_critical_smallest_p_within_bin": 0.00333, "results": "(see schema pattern above)"}
  },

  "joint_34_holm_correction": {
    "n_tests_total": 34,
    "alpha": 0.05,
    "holm_critical_smallest_p_joint": 0.00147,
    "purpose": "cross-bin claim sensitivity gate per gss_phase1_design.md §8.8"
  },

  "summary": {
    "n_batteries_tested_total": 34,
    "n_batteries_holm_significant_within_bin_per_bin": {"demographic": 2, "behavioral": 5, "psychological": 2, "attitudinal": 6},
    "n_batteries_holm_significant_within_bin_total": 15,
    "n_batteries_holm_significant_joint_34": 7,
    "n_batteries_substantively_meaningful": 5,
    "_substantively_meaningful_definition": "Holm-significant WITHIN BIN AND effect_size_label in {modest, substantive} AND ci_lo ≥ 0.02 (CI excludes small-effect boundary)."
  },

  "ci_method": "paired_bootstrap_respondent_level_B10000_BCa_seed42",
  "multiplicity_correction": "nested_holm_per_bin_primary_plus_joint34_sensitivity",
  "_multiplicity_definition": "Two corrections in parallel. Nested Holm within each bin's battery family is the PRIMARY correction (controls within-bin FWER). Joint Holm across all 34 batteries is the SENSITIVITY correction used to gate cross-bin claims. Within-bin claims need only nested Holm; cross-bin claims need both."
}
```

**Reporting role**: **co-primary mechanistic finding**, equal prominence to 4-bin LOO. The abstract reports both:
- Headline #1 (broad): from 4-bin LOO + Shapley
- Headline #2 (mechanistic): "Within each bin, the following batteries are Holm-significant **within-bin**: ..." with per-bin tables. Cross-bin "strongest battery overall" claims require joint-34 Holm sensitivity support.

**Estimand caveat**: Battery LOO estimates **predictive dependence under a fixed prompt-construction procedure** (R1 + locked persona prompt template), NOT causal feature importance. Because R1 already excludes the predicted item's own battery, Battery LOO measures **cross-construct contribution after direct same-battery leakage is already blocked**. See `gss_phase1_design.md` §13.2 for the full estimand statement.

**Forbidden uses** (anti-overclaim per §13.2):
- Do NOT compare ranks across bins as confirmatory unless joint-34 Holm sensitivity also passes. The nested Holm controls FWER WITHIN each bin only; cross-bin comparisons require either joint-34 support or explicitly descriptive language.
- Do NOT interpret battery-level findings as theoretical claims — that goes through `theory_interpretation_guide.md` as Discussion-level interpretation.
- Do NOT report `delta_mae` without alongside `n_items_in_battery` and `delta_mae_per_item` — battery-size matters for interpretation.
- Do NOT report `holm_significant_within_bin == true` as "substantively meaningful" without checking `effect_size_label` AND `substantively_meaningful` flag (§13.2 anti-overclaim rule).
- Do NOT interpret Battery LOO as causal — it estimates predictive dependence under a fixed prompt-construction procedure.

---

## Cross-tool naming conventions (locked)

- **Bin names**: `demographic`, `behavioral`, `psychological`, `attitudinal` (lowercase, underscored where multi-word; matches `gss_feature_taxonomy.json` keys)
- **Battery names**: lowercase, underscored, matches `gss_battery_map.json` keys
- **Run-id format**: `{phase}_{tool}_{model_short}_{n}_{seed}` — matches the locked I-10 reproducibility filename convention
- **Seed**: always 42 unless `--force-non-canonical-seed` (per `gss_driver.py`)
- **CI method**: `paired_bootstrap_respondent_level_B10000_BCa` for ablation deltas (BCa via scipy with percentile fallback for degenerate inputs; locked 2026-05-09 night per Codex N5/N6 audit)

## Implementation order (Day 3-4 of slim build)

1. Build `shapley_decomposition.py` — needs the `gss_driver.py` 16-condition enumeration and the standard ANOVA-style interaction decomposition.
2. Build `battery_loo.py` — wraps existing `gss_driver.py` with battery-level exclude_vars; runs **unconditionally as a co-primary analysis** post-Phase-1b (locked 2026-05-09 evening — the previous "after attitudinal-dominance trigger" gating was removed when Battery LOO was promoted to co-primary).

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
