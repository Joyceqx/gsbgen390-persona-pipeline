# Project Status — GSBGEN390 Phase 1 (Lean Design Locked)

**Last updated:** 2026-05-09 (lean-design lock + housekeeping)
**Maintained by:** Joyce Yu + collaborating Claude session
**See also:** `INDEX.md` (file map), `HANDOFF.md` (fresh-session quickstart), `PROJECT_SYNTHESIS.md` (paper-ready synthesis)

This document is the changelog-style single-source-of-truth for what's done, what's pending, and how to pick up the project in a fresh terminal. Per-decision rationale is in `PROJECT_SYNTHESIS.md` §4; per-section locked design is in `gss_phase1_design.md`.

---

## TL;DR for a fresh session

**Phase 1 design is LEAN-LOCKED as of 2026-05-09 + Battery LOO co-primary upgrade 2026-05-09 evening + comprehensive cleanup 2026-05-09 night.**

Implementation status (be precise about this):
- **Implemented + tested (analysis tier)**: `gss_loader.py`, `validate_taxonomy.py` (10 checks), `gss_pipeline.py` AUDIT A-E + B-regression, `gss_driver.py`, `select_phase1b_model.py` (5-branch self-test), `regression_baseline.py` (12/12 items self-test), **`shapley_decomposition.py` (8-assertion synthetic-fixture self-test, locked 2026-05-09 night)**, **`battery_loo.py` (8-assertion synthetic-fixture self-test, locked 2026-05-09 night)** — all passing.
- **NOT yet implemented (driver runtime extension)**: 16-condition Shapley enumeration mode in `gss_driver.py` (currently runs 5 conditions: Full + 4 LOO; needs +11 conditions for Shapley) and 34-battery exclusion mode (currently no battery-drop conditions). These are Phase 1a / Phase 1c runtime work; spec'd in `tier1_tool_schemas.md` Tools 1-2 and ready to implement when OpenRouter API key is in place.
- **Pending paid runs**: N=10 smoke / Phase 1a N=100 / Phase 1b N=1500 / GPT-4o anchor N=100 — all blocked on OpenRouter API key.

The base Phase 1 driver + audit pipeline + analysis tools (Shapley + Battery LOO) are implemented and self-tested on synthetic fixtures. The driver runtime extensions to actually GENERATE the 16-condition / 34-battery LLM call data are deferred to Phase 1a / 1c runtime (require API key + paid budget).

**Project-level research question**: *In LLM persona synthesis, which input feature categories drive prediction quality, and how does that contribution vary across outcome dimensions?* No prior published work has done large-N, leakage-clean, multi-model feature attribution at scale; this project fills that area-level methodological gap. Park et al. 2024 is the most-cited prior work in LLM persona simulation and serves here as a **cross-paper benchmarking anchor**, not as the project's defining framework.

**Phase 1 has TWO co-primary contributions** (locked 2026-05-09 evening — Battery LOO promoted from conditional secondary to unconditional co-primary across all 4 bins):
1. **Broad finding (4-bin LOO)**: which feature category contributes most to LLM persona prediction of attitude outcomes? — answered by 4-bin leave-one-out (demographic / behavioral / psychological / attitudinal) on GSS 2024 (N=1500).
2. **Mechanistic finding (34-battery LOO across all 4 bins, nested Holm)**: which specific construct-level clusters drive the signal within each bin? — answered by Battery LOO across the 34 batteries in `gss_battery_map.json` v0.2 (7 demographic + 10 behavioral + 2 psychological + 15 attitudinal), with **nested Holm-Bonferroni** within each bin's battery family.

One **secondary analysis** supports primary #1:
- **Bin-level Shapley decomposition** (16 conditions) — robustness check on the 4-bin LOO ranking against bin-bin interactions. Shares the 4-bin family multiplicity, no separate Holm correction.

**Theory interpretation** (6 candidate frameworks: MFT / Schwartz / Bourdieu / Cultural Theory / Inglehart-Welzel / Big Five) enters the Discussion section as **interpretive secondary analysis only** — NO horse race, no preregistered numeric thresholds, no Stage 3 refinement experiments. See `theory_interpretation_guide.md`.

**Locked numerical and structural decisions**:
- §12.2 quality-primary model-selection rule (DQ-1 parse-fail ≤30% + DQ-3 per-item relative variance ≥30% of human var + cost tie-break + Qwen fallback)
- DQ-3 reference: `outputs/primary_eval_human_variance_2024.json` (frozen GSS 2024 per-item variance)
- 4-layer leakage hygiene: §9c.1 disjointness + §9c.2 GSS-internal synonymy = none + §9c.3 R1 battery exclusion (**34 batteries + 17 singletons in `gss_battery_map.json` v0.2**) + §9c.4 R2 regression-baseline partition
- §11.1 abstract language template (forbidden mentalist claims; required scope qualifiers)
- **Nested Holm-Bonferroni**: 4-bin family (n=4) + Battery LOO families per-bin (demographic n=7, behavioral n=10, psychological n=2, attitudinal n=15) — 5 independent Holm corrections, NOT joint

**Joyce's path forward (lean version)**:
- (a) Get OpenRouter API key + run N=10 smoke (~$2-3)
- (b) Draft OSF pre-reg (4-bin primary scope; `PROJECT_SYNTHESIS.md` §3+§4 is the template; Joyce + Bayati signoff on items in `theory_interpretation_guide.md` §"Open items")
- (c) Run Phase 1a (4 cheap models on N=100 + GPT-4o anchor) → §12.2 selector picks 1b model
- (d) Run Phase 1b (single quality-selected model, N=1500) + GPT-4o anchor on N=100 subset
- (e) Run Shapley decomposition on Phase 1a outputs; run 34-battery Battery LOO on Phase 1b (unconditional, all 4 bins)
- (f) Write paper with theory framing as Discussion-only

The project has **two sequential phases**, both scoped at the Bayati meeting (2026-05-02):

### ✅ Pilot phase (completed 2026-04-30)
End-to-end replication of Park et al. at N=2 + N=1 via Cookiy. Pipeline + dashboard + leakage audit shipped. GitHub repo: https://github.com/Joyceqx/gsbgen390-persona-pipeline. Live dashboard: https://joyceqx.github.io/gsbgen390-persona-pipeline/

### 🟢 Phase 1: GSS public-data feature-importance analysis — design LEAN-LOCKED, pipeline complete

**Goal**: attack the GSS-attitudes row of Park's outcome × feature-category matrix at N≈1,500, using free GSS public panel data + 4-cheap-OpenRouter-model panel + GPT-4o anchor on N=100.

**Locked design (lean version, 2026-05-09)**:
- **Snapshot prediction** on GSS 2024 cross-section (N=3,309 respondents, 973 variables)
- **Primary eval (Path B)**: 12 curated `primary_eval` items → supports 4-bin LOO ablation
- **Sensitivity eval (Path A)**: 118 Park-comparable items → per-item raw accuracy via GPT-4o anchor on N=100 subset
- **Feature pool**: 140 variables across 4 bins (24 demographic / 25 behavioral / 8 psychological / 83 attitudinal — taxonomy v0.3)
- **LLM panel — Phase 1a (N=100)**: 4 OpenRouter models, n_samples=1 each: Qwen-2.5-72B-Instruct / DeepSeek-V3.1 / MiniMax-M1 / Kimi K2 + GPT-4o anchor on full N=100
- **LLM panel — Phase 1b (N=1500)**: single model selected by §12.2 quality-primary rule + GPT-4o anchor on N=100 subset
- **Stability metric**: cross-model agreement % (cheap panel) + within-model self-consistency (GPT-4o anchor only)
- **Aggregation**: respondent-macro PRIMARY; bootstrap CIs at respondent level B=1000, seed=42; LOO ΔMAE via PAIRED bootstrap; Holm-Bonferroni FWER within each LOO family
- **Raw accuracy** primary metric — no test-retest normalization (deferred to Phase 2)
- **Leakage hygiene**: 4 layers (see §9c of design doc): disjointness, GSS-internal synonymy = none, R1 battery exclusion, R2 regression-baseline partition
- **Pre-registration** on OSF before Phase 1a launches

**Phase 1 budget**: ~$215 total at N=1500 (within original $300-500 envelope; halved from earlier ~$440 by the §12.2 single-model rule for 1b).

**Pipeline state (all green)**:
- ✅ GSS 2024 data downloaded (3-batch fixed-width extract)
- ✅ `gss_loader.py` reads → 3,309 × 973 DataFrame; 22/22 key Park variables verified
- ✅ `gss_feature_taxonomy.json` v0.3 locked + `validate_taxonomy.py` 10 checks pass (incl. 7c battery map well-formedness)
- ✅ `gss_battery_map.json` **v0.2** locked (34 batteries: 7 D / 10 B / 2 P / 15 A; 17 singletons) — expanded from v0.1 (15 attitudinal-only batteries) on 2026-05-09 evening for co-primary Battery LOO
- ✅ AUDIT-A through AUDIT-E (5 audit smoke tests) all pass
- ✅ AUDIT-B regression: no non-substantive options exposed (12 primary + 118 sensitivity items)
- ✅ Multi-model extension to AUDIT-E: per-model + panel-median + cross-model agreement
- ✅ `llm_router.py` — OpenRouter / OpenAI client with retry/backoff
- ✅ `gss_driver.py` — top-level orchestrator (atomic-write per-respondent + item-level sensitivity resume + R1 battery exclusion + I-10 reproducibility guard with `--force-non-canonical-seed`)
- ✅ `select_phase1b_model.py` — §12.2 rule executable + 5-branch self-test passes
- ✅ `regression_baseline.py` — R2 partition test + N=200 self-test passes (12/12 items scored)
- 🟡 **N=10 smoke test on real LLM data** ← needs OpenRouter API key
- 🔒 OSF pre-registration draft (after smoke green)
- 🔒 Phase 1a (N=100, ~$65 with anchor)
- 🔒 §12.2 selector run on 1a output → picks 1b model
- 🔒 Phase 1b (N=1500, ~$95 selected model + ~$50 anchor)
- 🔒 Shapley decomposition (Phase 1a; tool to be implemented)
- 🔒 Battery LOO (Phase 1c, **co-primary, all 4 bins, unconditional**; nested Holm per-bin; tool to be implemented; ~$50-60)

### 🔮 Phase 2: targeted Cookiy collection (planned, not started)
Will cover BFI-44 personality + behavioral game outcomes that GSS doesn't measure. Includes 2-week recontact for proper test-retest baseline. Smaller N (~20-30, with Phase-1-empirics-seeded power calc before launch). Design in `thesis_phase2_design.md`.

---

## What changed 2026-05-09 night (comprehensive pre-OSF cleanup audit)

Codex re-audited the full design after the Battery LOO co-primary promotion and identified 16 cleanup items. All implemented as documentation/design changes — no code re-architecture, no locked artifact regenerated.

### Multiplicity strengthening
- **Joint-34 Holm sensitivity layer added** (`gss_phase1_design.md` §8.8): nested Holm primary + joint-34 sensitivity for cross-bin claims. Within-bin claims confirmatory under nested; cross-bin claims need joint-34 support otherwise descriptive only.
- **Practical-effect-size thresholds added** (§8.9): small <0.02 / modest 0.02-0.05 / substantive ≥0.05. Substantive interpretation requires Holm-significance AND modest+ effect size with CI excluding small boundary.
- **Battery LOO schema v0.3 → v0.4** (`tier1_tool_schemas.md`): per-battery now reports `p_holm_within_bin` + `p_holm_joint_34` + `effect_size_label` + `substantively_meaningful` flag.

### Estimand + framing precision
- **Battery LOO estimand caveat** (§13.2): explicit statement that LOO measures "predictive dependence under fixed prompt-construction procedure, after R1 already blocks direct same-battery leakage" — NOT causal importance, NOT raw self-predictive value.
- **R2 regression baseline caveat** (§9c.4): the "LLM MAE = regression MAE + LLM gain" decomposition explicitly relabeled as **rhetorical**, not causal partition. "LLM gain" framed as "model-specific predictive value beyond a simple supervised baseline," not "persona reasoning."
- **Hierarchical justification §13.0 added**: explicit explanation that 4-bin LOO + Battery LOO are different LEVELS of the same attribution-question family, not two unrelated multiplicity-inflating tests. Reviewer rebuttal language drafted.

### Honest impact / scope framing (§1.0)
- Added explicit "what this paper is not" list: NOT general human simulation, NOT causal feature importance, NOT normalized Park-style fidelity, NOT robust cross-LLM-family generalization beyond N=100 panel.
- Honest contribution: "leakage-clean preregistered attribution framework showing what kinds of survey information drive LLM persona prediction accuracy" — not "LLM personas understand humans."
- Phase 1 alone = strong empirical/methodological paper; Phase 1+2 = higher-impact complete thesis.

### OSF + readiness procedural infrastructure
- **§9e OSF lock checklist** added: 22-item checklist with exact pre-reg locked items.
- **§9f readiness gates** added: pre-N=10 / pre-Phase-1a / pre-Phase-1b checklists.
- **§9g operational risk** added: documented that `gss_driver.py --n N` defaults to running sensitivity across all 4 cheap models (could blow budget); mitigation = always pass `--primary-only` for Phase 1a; future low-risk fix = explicit `--phase1a / --phase1b / --anchor / --battery-loo` modes.

### Stale-phrase cleanup (Fix 6)
Removed or replaced across docs:
- "attitudinal-bin Battery LOO" → "Battery LOO across all 4 bins" (HANDOFF, README, PROJECT_SYNTHESIS)
- "conditional on attitudinal dominance" — historical-context preserved in changelog; live-spec wording removed
- "15 batteries + 9 singletons" → "34 batteries + 17 singletons" (5 places: gss_phase1_design.md §9c.3, HANDOFF.md §4, PROJECT_SYNTHESIS Chinese §4.5 + English §3.5 + §4.5, STATUS.md 3 places)
- "panel median is the headline" — fixed in `gss_phase1_design.md` §12.4 (panel median is Phase 1a robustness, NOT N=1500 headline; Phase 1b headline is the §12.2-selected single model)
- "$215" budget — clarified as "core Phase 1 LLM run; total with Battery LOO + Shapley = ~$280-300"
- "Phase 1c theory-driven" — historical-context preserved in changelog; replaced in §5 budget paragraph with "co-primary Battery LOO + Shapley" allocation
- "pipeline is 100% built and tested" → "base pipeline implemented + tested; Battery LOO + Shapley specified, not yet implemented"

### Other documentation consistency
- README.md "What this is" budget line updated; "attitudinal-bin Battery LOO" replaced.
- HANDOFF.md §1 "100% built" qualified; §4 design-summary corrected; old paper-claim paragraph at the bottom rewritten with co-primary narrative.
- PROJECT_SYNTHESIS.md Chinese §4.5 + English §4.5 (R1 battery boundaries decision log entries) updated to reflect v0.2 expansion that came AFTER v0.1's 15-battery decision.
- INDEX.md `gss_battery_map.json` description was already on v0.2 (no change).

### R2 regression baseline numerical-warnings note (Fix 11)
- Documented in `regression_baseline.py` docstring: sklearn emits divide-by-zero / overflow / invalid-value warnings during the self-test even with the existing zero-variance column filter. The 12/12-item MAE output is internally consistent and reproducible, but warnings indicate numerical fragility that should be diagnosed before R2 results enter a published paper.
- Suggested follow-up (NOT done now): replace `StandardScaler(with_mean=False)` with a more robust scaler; pipe scaling inside CV folds; consider `with_warnings_as_errors=True` for regression tests.

### What was NOT changed (intentional)
- Locked taxonomy v0.3 — not touched.
- Locked battery map v0.2 — not touched.
- Locked DQ-3 reference (`outputs/primary_eval_human_variance_2024.json`) — not touched.
- §12.2 quality-primary selection rule + 5-branch self-test — not touched.
- AUDIT A-E + B-regression scoring rules — not touched.
- All locked code modules' core behavior — not touched (only docstrings clarified for R2).

---

## What changed 2026-05-09 evening (Battery LOO promoted to co-primary across all 4 bins)

After lean-lock + drift-fix + framing reset earlier today, Joyce flagged that the conditional-on-attitudinal-dominance Battery LOO was awkward and Battery-level findings should be more compelling than 4-bin alone. Promoted Battery LOO from "conditional secondary on attitudinal only" to "unconditional co-primary across all 4 bins" with nested Holm correction.

### Changes
1. **`gss_battery_map.json` v0.1 → v0.2**: expanded from 15 batteries (attitudinal only) to **34 batteries** across all 4 bins:
   - **Demographic** (7): own_education, parental_education, marital_status, racial_ethnic_origin, family_of_origin_economic, growing_up_geography, growing_up_family_structure
   - **Behavioral** (10): current_religious_intensity, denominational_identity, voting_turnout, voting_choice, current_employment, work_history, job_security_perception, traditional_media, digital_media, gun_related
   - **Psychological** (2): subjective_wellbeing, interpersonal_trust
   - **Attitudinal** (15): unchanged from v0.1
   - Each battery now has explicit `bin` field; validator check 7c verifies `bin` matches actual taxonomy.
2. **§13.2 Battery LOO** rewritten from "conditional secondary, attitudinal only" to "unconditional co-primary, all 4 bins, nested Holm per-bin."
3. **§8.8 multiplicity** rewritten: 5 independent Holm families (1 for 4-bin LOO + 4 for Battery LOO per bin) instead of "4-bin + attitudinal Battery LOO."
4. **§13.4 deferred list** updated: added `sampled Shapley on 34 batteries` + `variable-level LOO` + `singleton-level LOO testing` as explicit deferrals (each with rationale).
5. **`tier1_tool_schemas.md` Tool 2** updated to v0.3 schema: scope is all 4 bins; output is bin-keyed with per-bin Holm; size-aware reporting fields (`n_items_in_battery`, `delta_mae_per_item`).
6. **`validate_taxonomy.py` check 7c** extended: per-bin battery count + `bin` field consistency check. Currently passes with 7/10/2/15 = 34.
7. **Budget**: Battery LOO incremental cost ~$50-60 (up from prior ~$25-30 for attitudinal-only conditional design). Total Phase 1 budget remains within ~$215-275 envelope.
8. **STATUS.md / HANDOFF.md / PROJECT_SYNTHESIS.md / INDEX.md** updated to reflect co-primary structure.

### Why this is an upgrade, not a re-litigation of the lean lock
The lean-lock decision was "don't add tools we don't need; keep the paper focused." This change does NOT add a new tool — Battery LOO was already in the lean-lock design (as conditional secondary). It elevates an existing tool's reporting role and expands its scope. The motivation: "conditional on attitudinal dominance" was an awkward design that produced no mechanistic finding when attitudinal didn't dominate — and the paper would have a weaker story in that case. Always-on, all-bin Battery LOO produces a mechanistic finding regardless of which bin wins the broad LOO.

---

## What changed 2026-05-09 (lean-design lock + housekeeping)

### Lean-design lock (Codex's lean-design audit; locked 2026-05-09 afternoon)
1. **Slimmed away** from "staged confirmatory discovery with 6-theory horse race" toward a leaner, more-publishable structure: 4-bin LOO primary + Shapley robustness + attitudinal Battery LOO interpretability + theory-framing as Discussion-only.
2. **Deferred to future work**: theory-bin LOO as confirmatory family, RSA, permutation importance theory adjudication, Stage 3 refinement experiments, 6-theory horse race with hard numeric thresholds, Friedman & Popescu (2008) H-statistic proper implementation. See `gss_phase1_design.md` §13.4.
3. **Renamed**: the morning-of v0.1 DRAFT `osf_preregistration_appendix_a_theory_predictions.md` → `*.SUPERSEDED-2026-05-09.md`. New live spec is `theory_interpretation_guide.md` (Discussion-section memo, not OSF appendix).
4. **Renamed metric**: the Shapley schema's `friedman_h_statistic` → `interaction_variance_share` (with explicit non-standard definition; we no longer call any custom variance-share statistic "Friedman's H" since we don't implement the Friedman & Popescu (2008) partial-dependence H).
5. **Files updated**: `gss_phase1_design.md` (§7, §8, §13), `tier1_tool_schemas.md` (slimmed to Shapley + Battery LOO), `theory_interpretation_guide.md` (NEW), `PROJECT_SYNTHESIS.md` (§3.8, §4.8, §6.4, §6.8, §6.9).

### Housekeeping (2026-05-09 evening)
6. **Created `INDEX.md`** — canonical file map.
7. **Updated STATUS.md TL;DR** — reflects the lean-locked design (was stale from 2026-05-06).
8. **Updated HANDOFF.md** — §3 state snapshot + §4 design summary refreshed for lean lock.
9. **Moved `email_to_bayati.md` → `archive/`** (one-off historical email).
10. **`osf_preregistration_appendix_a_theory_predictions.SUPERSEDED-2026-05-09.md`** kept in root with explicit suffix (cross-referenced from `theory_interpretation_guide.md` + `PROJECT_SYNTHESIS.md`).

---

## What changed 2026-05-08 (R1 + R2 leakage hygiene + selector + lots of audit fixes)

### Codex research-layer audit (§3.1 / §3.9 / §4) — addressed
1. **R1 battery exclusion** (§3.1): when predicting any primary_eval item in a battery, drop the entire battery from the persona prompt. Mirrors Park v2's BFI whole-trait-block hold-out (Park v2 PDF p.37, verified). Implemented in `gss_pipeline.py::battery_excludes_for_item` + `gss_driver.py::run_primary_one_respondent`.
2. **R2 regression baseline** (§3.1): non-LLM regression (Ridge for Likert, multinomial Logistic for binary; 5-fold CV). Per-item MAE = auto-correlation upper bound; partitions LLM gain from auto-correlation. Implemented in `regression_baseline.py`. **Beyond Park v2**: Park brackets inflation (single-item vs whole-module hold-out); we partition it.
3. **R3 NOT implemented** — would conflate "battery info loss" with "bin capacity reduction." R1 + R2 do the work cleaner.
4. **DQ-3 absolute threshold (var<0.5) → per-item relative threshold** (§3.9): `var(model_i) ≥ 0.30 × var(human_2024_i)`; >50% items failing disqualifies. Locked human-variance reference at `outputs/primary_eval_human_variance_2024.json`.
5. **§3.3 + §3.4 abstract language tightening**: `gss_phase1_design.md` §11.1 adds 6-row mandatory measurement-language template (forbids "persona fidelity" / "robust across LLM families" / "matches Park's 82%" / mentalist claims).
6. **§3.6 decision log**: this STATUS + `PROJECT_SYNTHESIS.md` §4 serve as the OSF "decisions locked, when, against what evidence" log.

### Battery map locked
7. **`gss_battery_map.json` v0.1**: 15 batteries + 9 singletons. Civil-liberties split into 3 batteries by target group (atheists / racists / communists). `morality_lifestyle` refined into 3 (`sexual_morality` / `moral_legalization` / `adolescent_sex_policy`).
8. **`validate_taxonomy.py`** check 7c added: every primary_eval item is in a battery OR a singleton; every battery item exists in data; no item in two batteries.

### §12.2 quality-primary selector
9. **`select_phase1b_model.py`** implements the §12.2 rule deterministically: argmin Likert MAE among DQ-passers (DQ-1 parse-fail ≤30%; DQ-3 per-item relative variance ≥30% of human); cost as 5%-tie-break; Qwen-2.5-72B as named fallback. 5-branch self-test passes (`argmin_mae` / `tie_break_cost` / `fallback_qwen_dq` / `fallback_qwen_tie` / `fallback_qwen_no_data`).

### Code-level operational fixes
10. **§12.2 selector wired with relative DQ-3** + locked human-variance reference.
11. **Item-level sensitivity resume** (`gss_driver.py`): `_completed_sensitivity_items` + `_upsert_sensitivity_records` + `persist_after_each_item` callback. Worst-case interruption rerun = 1 in-flight item per (rid, model) instead of 118.
12. **`run_phase1` default path** now encodes `model_tag` + `seed` so notebook/programmatic callers can't bypass the I-10 reproducibility guard.
13. **`gss_pipeline.py` `--test-question-options` CLI flag** wired to `_audit_b_test_no_refusal_options`.
14. **Output schema for AUDIT-B regression** added (no non-substantive labels exposed in `format_eval_question` for any of 12 primary + 118 sensitivity items).
15. **Bilingual comprehensive doc**: `PROJECT_SYNTHESIS.md` (~750 lines, ZH-first then EN) created — pre-smoke-test review artifact + paper scaffolding.

---

## What changed 2026-05-07 (theory review Round 2)

1. **`theory_review_round2.md` created**: 5 additional candidates the Round 1 scaffold missed (Big Five/HEXACO, Inglehart-Welzel, Hofstede, Theory of Planned Behavior, Self-Determination, Dual-Process), verified 2024-2026 LLM-applied work in 4 buckets (methodological backbone / theory-as-input persona / silicon-sampling neighbors / critical-skeptic), tiered reading list (Tier 1 ~5.5h must-read, Tier 2-4 deeper), 4 open questions for Bayati.
2. **Round 2 recommendations**: evaluate Inglehart-Welzel 4-quadrant (top) + Big Five-as-input (secondary) alongside Round-1's MFT/Schwartz.

---

## What changed 2026-05-06 (Codex audit fixes + two design upgrades)

### Codex audit (2nd round) — all critical + most important issues fixed

Codex audited the AUDIT-E + multi-model build and found 2 critical + 10 important issues. Fixed all that affect smoke correctness; deferred concurrency / fine-grained resume to post-smoke.

**Critical fixes**:
- C-1: sensitivity item scale derivation was unsafe (WLTH* trio misclassified as binary; COL* meta-codes contaminating Likert scoring). Added `SENSITIVITY_FORMAT_OVERRIDES` in `gss_driver.py` for 9 affected items + override-aware `format_eval_question`.
- C-2: panel synthesis used median for ALL items (broken for binary + PARTYID-with-7). New `_panel_aggregate_code` routes by item_format: median for likert3+, mode for binary/categorical, mode for PARTYID when any model outputs 7.

**Important fixes**:
- I-1: positive non-substantive codes (e.g., OWNGUN=3 REFUSED, 36 of 3309 respondents) now filtered at both prompt-build and truth-conversion via `_is_non_substantive_label()` heuristic.
- I-2: `cross_model_agreement_pct` now strictly defined (all expected models present + parsed + identical), reports {agreement_pct, n_tuples, n_strict_agreed, n_lost_to_parse_or_missing} per condition.
- I-3: panel synthesis takes `expected_models`, skips incomplete-coverage tuples.
- I-4: `max_tokens` 16 → 64 to handle reasoning-style chain-of-thought.
- I-5: `_is_retryable` now class-aware (RateLimitError / APITimeoutError / APIStatusError 5xx), substring fallback extended for 500 / "internal server" / "service unavailable".
- I-9: GPT-4o anchor bumped N=50 → N=100 (Codex flagged underpowered for per-item Park comparison).
- I-10: Cost-estimate caveats added (rates approximate; no prompt caching assumed).
- I-8: Panel diversity language softened — explicit acknowledgment that all 4 cheap models are China-trained orgs.

**Deferred**: I-6 concurrency in `call_panel`; I-7 finer resume granularity. Both irrelevant to N=10 smoke; flagged for pre-Phase-1b implementation.

### Two locked design upgrades (post-Codex)

**Q1 (locked) — Model-selection rule (Phase 1a → 1b)**:
- Phase 1a runs all 4 cheap models on N=100 + GPT-4o anchor.
- Phase 1b runs only the cheap model that minimizes the locked composite score: `cost_per_call × (1 + parse_failure_rate)`. Tie-break by Likert MAE then cross-model agreement.
- Total Phase 1 budget halved: ~$215 (vs ~$440 previously).
- Methodological strengthening: Phase 1a multi-model comparison itself becomes a publishable mini-result; Phase 1b focuses on the **quality-pre-registered** single model (argmin 1a Likert MAE among DQ-passers; cost is tie-break only — see §12.2) with multi-model robustness panel from 1a.
- Pre-registration must lock the rule BEFORE 1a runs.
- See `gss_phase1_design.md` §12.2.

**Q2 (revised under 2026-05-09 lean lock) — Theory interpretation moved to Discussion-only**:
- Originally proposed: theory-driven secondary LOO as a confirmatory family alongside the 4-bin primary, with Joyce locking one theory (MFT / Schwartz / Bourdieu / Cultural Theory) and building `gss_theory_taxonomy.json`.
- Reverted under Codex's lean-design audit (2026-05-09): theory framing now enters the Discussion section only, as **interpretive secondary analysis** across 6 candidate frameworks. NO confirmatory horse race, NO `gss_theory_taxonomy.json` build, NO theory-bin LOO ΔMAE in the OSF pre-reg.
- Live spec: `theory_interpretation_guide.md` (replaces the planned theory-bin appendix).
- See `gss_phase1_design.md` §13.3 (theory interpretation in Discussion) + §13.4 (deferred to future work).

### Tasks updated (under lean lock)
- #14 (§12.2 selector) — DONE; `select_phase1b_model.py` + 5-branch self-test pass.
- #15 (Joyce's literature review) — Joyce's work; informational only under lean lock (no longer blocks OSF pre-reg).
- #16 (theory-bin LOO build) — DEFERRED to future work; not in lean Phase 1.

---

## What changed 2026-05-05 (audit checkpoints + LLM panel build)

### 5 audit checkpoints all locked
1. ✅ **AUDIT-A** persona prompt template — Park-style "you are this person" preamble + 4 fixed-order bin sections + alphabetical within-bin + missing-coded items omitted. Smoke: `--print-prompt`.
2. ✅ **AUDIT-B** eval question phrasing — unified format (GSS question + numbered option list + "output single integer code"). 4 stem overrides for FECHLD/FEPOL/RACDIF1/HELPPOOR with canonical GSS codebook wording. PARTYID presents all 8 codes 0-7. Smoke: `--print-questions`.
3. ✅ **AUDIT-C** scoring rules — Likert MAE for likert3-7, categorical exact-match for binary, contingent treatment for PARTYID (Likert on 0-6, categorical when either side = 7 'Other party'). Parse failures tracked separately. Self-consistency at temp=0.7. 7 hand-test assertions pass (`--test-scoring`).
4. ✅ **AUDIT-D** sensitivity per-item exclusion — `build_persona_prompt(exclude_vars=...)` drops listed variables from all bins. Hard assertion: when excluding X, X disappears AND other items remain. Smoke: `--test-exclusion` (3 targets).
5. ✅ **AUDIT-E** aggregation — respondent-macro PRIMARY (each respondent equal weight); item-macro and pooled SECONDARY. Bootstrap CIs at respondent level B=1000. LOO ΔMAE via PAIRED bootstrap (locked rule from §10: resample respondents once, compute Full and LOO on same resample, then delta). 5 hand-test assertions pass (`--test-aggregation`).

### Multi-model panel redesign (locked 2026-05-05)
Original GPT-4o-only would cost ~$900 at N=1500 (over budget). Redesigned to a **4-model OpenRouter panel** as primary + **GPT-4o anchor on N=100** for Park-comparability (anchor bumped from N=50 → N=100 per Codex audit 2026-05-06; budget moved from 1b panel into the cost-saving switch to a single quality-selected model for 1b — see `gss_phase1_design.md` §5):

| Role | Model | Budget |
|---|---|---|
| Phase 1a — 4 cheap panel + anchor (N=100) | Qwen-2.5-72B + DeepSeek-V3.1 + MiniMax-M1 + Kimi K2 + GPT-4o anchor | ~$65 |
| Phase 1b — 1 quality-selected model (N=1500, n=1) | (selected by §12.2 quality-primary rule) | ~$95 |
| Phase 1b — GPT-4o anchor (N=100 subset, n=2) | GPT-4o | ~$50 |
| **Total Phase 1** | | **~$215** |

**Methodological strengthening**: "feature-category contribution generalizes across 4 LLM families" is a stronger thesis claim than "tested on GPT-4o." Anchor preserves direct Park v2 Table 3 comparison. Cross-model agreement % replaces within-model self-consistency as primary stability metric. See `gss_phase1_design.md` §12 for full rationale.

### Built this session
- **`llm_router.py`** (254 lines) — OpenRouter / OpenAI client with 8-attempt exponential backoff (caps at 60s), `call_panel()` for multi-model, locked panel constants, smoke-test CLI (`--smoke-one`, `--smoke-panel`, `--smoke-anchor`).
- **`gss_driver.py`** (369 lines) — top-level orchestrator. `run_phase1(n, models, ...)` runs respondents × conditions × items × models with atomic-write resumability (every respondent's records persisted before next; SIGINT-safe via `--resume`). CLI flags: `--smoke`, `--anchor`, `--n`, `--primary-only`, `--sensitivity-only`, `--models`, `--no-resume`.
- **gss_pipeline.py multi-model extension** (305 lines added) — `compute_phase1_headline_multimodel()` returns per-model headlines + panel-median synthesis + cross-model agreement %. Smoke test: `--test-multimodel`.

### Codex audits passed
- First audit (post-pilot tidy): 5 critical + 5 important issues fixed (commit `6947c70`).
- Second audit (AUDIT A-D scaffold): 4 important + 4 minor issues fixed; no critical issues found (commit `d00cb17`).

### Status of locked decisions (no changes since 05-02)
All Bayati-endorsed direction (Phase split / 4-bin taxonomy / pre-registration commitment) and AUDIT A-E decisions still locked. Multi-model panel is an ADDITION to the locked design (in §12), not a change to it.

---

## What changed 2026-05-02 (Phase 1 build session)

### Direction-setting
1. ✅ **Bayati meeting**: Phase split (GSS-first → targeted Cookiy) and 4-bin taxonomy endorsed; pre-registration committed to before Phase 1a (revised 2026-05-06: pre-reg now precedes 1a so the §12.2 selection rule is locked before 1a fires; that rule was further revised 2026-05-06 from cost-primary to **quality-primary** — argmin 1a Likert MAE among DQ-passers — to align the selection metric with the paper's headline metric).
2. ✅ **Path A\* locked**: Path B as primary (12 items, supports LOO), Path A as sensitivity (Park's ~118 items, per-item comparability). Same data, two analytical lenses.
3. ✅ **Snapshot wave structure**: single-wave prediction on GSS 2024 (avoids panel-evolution and cross-wave leakage). Raw accuracy primary; test-retest normalization deferred to Phase 2.
4. ✅ **Disjoint-set rule clarified**: primary-pass features = (declared bin lists) MINUS primary_eval only; sensitivity-pass handles per-item leakage separately. Resolves the otherwise-empty-psychological-bin problem.

### Data + loader
5. ✅ **GSS 2024 data downloaded** via GSS Data Explorer. The 973-variable extract is split into 3 batches by GSS DE; combined locally to a single 973-column DataFrame.
6. ✅ **`gss_loader.py`** — parses each batch's `.do` script for column ranges + variable labels + value labels; reads the corresponding `.dat` fixed-width file; merges 3 batches horizontally into one DataFrame at 75,699 rows × 973 columns. Handles missing-value codes (-100, -99, etc.) explicitly. Namespaced label sets per batch to avoid label-set name collisions across batches.
7. ✅ **Verified**: 22/22 key Park variables present with correct labels (POLVIEWS=4 → "Moderate, middle of the road"; HAPPY=3 → "Not too happy"; SEX=1 → "MALE"; etc.). N=3,309 respondents in 2024.

### Taxonomy
8. ✅ **`gss_feature_taxonomy.json`** locked:
   - 12 primary_eval items (one per construct family, ~auto-correlation-minimized)
   - 118 sensitivity_eval items (Park's list minus 15 retired/renamed in 2024)
   - 140 feature variables in 4 bins (24 demographic / 25 behavioral / 8 psychological / 83 attitudinal — final v0.3 counts after audit-A reclassification; superseded the initial 23/29/8/80 from 2026-05-02)
9. ✅ **`validate_taxonomy.py`** — confirms (a) every claimed variable exists in the data, (b) bins are mutually disjoint, (c) per-respondent coverage. Median respondent answered: 8/12 primary_eval, 20/24 demographic, 17/25 behavioral, 4/8 psychological, 42/83 attitudinal items.

### Doc updates locked
10. ✅ `gss_phase1_design.md` rewritten with locked decisions (snapshot, raw accuracy, Path A\*, disjoint-set rule, 2-week plan).
11. ✅ `gss_variables_to_download.md` documenting the GSS DE workflow + variable list (now used as the data download record).

### Open work (not started yet)
- **#10 `gss_pipeline.py`** — persona-prompt builder + LLM dispatcher + scorer adapted for GSS rows. Reuses pilot's retry/backoff and self-consistency machinery. Needed before any LLM calls.
- **#6 N=10 smoke test** — verify pipeline end-to-end at minimum scale (~$1).
- **#7 OSF pre-registration** — drafted **before Phase 1a**; locks taxonomy, eval list, primary metric, exclusion rules, secondary analyses, the 4-cheap-model panel, the §12.2 **quality-primary** selection rule (argmin 1a MAE among DQ-passers; DQ-1 parse-fail ≤30%; DQ-3 per-item relative variance ≥30% of human var; cost as tie-break; Qwen fallback), and the Holm-Bonferroni multiplicity correction.
- **#8 Phase 1a (N=100)** — sanity check.
- **#9 Phase 1b (N=1,500)** — primary analysis.

---

## What changed in earlier sessions (2026-04-30 evening — pilot phase wrap)

### Major fixes / additions to pipeline
1. ✅ **Path reconciliation** — transcripts copied to `responses/R{1,2}/transcript.txt` and `responses_s2/R1/transcript.txt`.
2. ✅ **Demographics JSON** per respondent (`responses/R1/demographics.json` etc.) — hand-extracted from transcripts because pipeline previously had only `{respondent_id}` for Condition A.
3. ✅ **Self-description anchors** extended to match real Cookiy moderator phrasings ("a little bit about yourself", "in a short paragraph", etc.) — was silently failing on P1.
4. ✅ **Truth-source unification** — pipeline now overrides internal parser output with the audited `eval_answers_extracted.csv` (single gold source).
5. ✅ **TypeError defense** in metrics-table writer.
6. ✅ **Eval-stem-based splitter** for both Study 1 and Study 2 — replaces fragile verbal-transition anchors. Verified no eval Q&A leaks into interview_text/construction_qa segments.

### Pipeline run + LOO ablation
7. ✅ **`run_notebook_local.py`** — runner that executes `persona_pipeline.ipynb` outside Colab. Patches Cell 8 (file upload → local read), skips Jupyter magics (`!pip`), stubs `display()`, **adds exponential-backoff retry around `_call_openai`** (essential — TPM=30K limit triggers ~3-5 times per run on this account), saves `persona_answers_full.json` with per-item primary + samples.
8. ✅ **12 conditions ran**: Study 1 ×3 conditions × 2 respondents + Study 2 ×6 conditions (A, D, +4 LOO) ×1 respondent. ~9 min total wall-clock, ~$4 API cost.

### Leakage audit (defense against in-session priming)
9. ✅ **`leakage_audit.json`** — manually tagged each of 15 eval items per respondent as STRONG / SOFT / CLEAN with evidence quotes from the transcript.
   - P1 STRONG: `bfi_c, polviews, happy` (3 items)
   - P2 STRONG: `bfi_c, polviews, satjob` (3 items)
   - S2 STRONG: 0 (survey arm has structurally less leakage)
10. ✅ **`rescore_with_leakage_audit.py`** — re-scores each condition under three filters: `full_eval / strict_clean / broad_clean`. Output: `metrics_with_leakage_audit.csv`.
11. ✅ **`make_robustness_chart.py`** — produces `chart_robustness.png` (3-bar groups per condition: full / strict / broad MAE), separated into Study 1 and Study 2 panels.

### Fact corrections to docs
12. ✅ **Park used an AI interviewer, not a human one.** The user originally believed Park used human interviewers (an error inherited from `replication_scoping.md` and `interview_quality_audit.md`). Park 2024 directly states they built a custom voice-to-voice AI agent around the AVP protocol with adaptive follow-ups, averaging 6,491 words/transcript. Fixed in:
   - `README.md` (front-door description)
   - `replication_scoping.md` (comparison table + Open Question 2)
   - `interview_quality_audit.md` (§1, §3.1, §3.5, table row)
   - `EXPLAIN_ZH.md` (主持人 row in comparison table)
   - The remaining "human" references in docs are now intentional (AVP protocol historical origin, future-design hypothetical alternative, "vs human moderator" comparisons).

---

## Headline results (from `metrics_per_respondent.csv`)

### Likert MAE per condition (lower = closer to truth)

| Arm | Resp. | A demo | B desc | C/D | LOO best | LOO worst |
|---|---|---|---|---|---|---|
| Study 1 | P1 | 0.83 | 0.92 | **C: 0.08** | — | — |
| Study 1 | P2 | 1.17 | 0.75 | **C: 0.00** | — | — |
| Study 2 | S2-P1 | 0.50 | — | D: 0.83 | drop attitudinal: 0.58 | drop demographic: 1.17 |

### Leakage-filter robustness (`metrics_with_leakage_audit.csv`)

|  | full (15) | strict-clean | broad-clean |
|---|---|---|---|
| P1/A | 0.83 | 0.70 | 1.00 |
| P1/B | 0.92 | 0.80 | 1.00 |
| **P1/C** | **0.08** | **0.10** | **0.00** |
| P2/A | 1.17 | 1.20 | 1.00 |
| P2/B | 0.75 | 0.80 | 0.75 |
| **P2/C** | **0.00** | **0.00** | **0.00** |

**Caveat**: broad-clean for P2 has only 4 items left (very noisy at MAE=0.00). Headline figure should be **strict-clean** (10 items kept). At strict-clean, C still beats A by 0.6–1.2 MAE per respondent.

---

## Current work tree (updated 2026-05-09)

```
GSBGEN390/
│
├── ── DESIGN + NARRATIVE DOCS ──
├── README.md                          ← front door
├── STATUS.md                          ← this file (single-source-of-truth)
├── CLAUDE.md                          ← guidance for AI assistants in this folder
├── AGENTS.md                          ← guidance for Codex (parallel of CLAUDE.md)
├── PRIMER.md                          ← 1-2 page Joyce self-intro
├── MEETING_HANDOUT.md                 ← one-page brief for Bayati meeting (pilot)
├── WRITEUP.md                         ← 3-5 page formal pilot write-up
├── progress_report.md                 ← pilot sprint narrative
├── replication_scoping.md             ← design rationale + Park's actual numbers
├── FUTURE_DESIGN.md                   ← open design questions for the thesis-stage
├── BUSINESS_LANDSCAPE.md              ← market scan
├── LIT_REVIEW.md                      ← academic literature review
├── EXPLAIN_ZH.md                      ← Chinese project explanation
├── CODE_WALKTHROUGH_ZH.md             ← Chinese walkthrough of persona_pipeline.py
├── COLAB_RUN_GUIDE.md                 ← Colab fallback instructions
│
├── ── PHASE 1 (GSS-PUBLIC) DESIGN + ARTIFACTS ──
├── gss_phase1_design.md               ← Phase 1 LEAN-LOCKED design (2026-05-09); §4 method, §9c 4-layer leakage hygiene, §10 aggregation, §11.1 abstract language template, §12 multi-model panel, §12.2 quality-primary selection rule, §13.1 Shapley, §13.2 Battery LOO, §13.3 theory interpretation (Discussion only), §13.4 deferred-to-future-work list
├── theory_review.md                   ← Round 1 lit review (informational under lean lock; §8 lock unused)
├── theory_review_round2.md            ← Round 2 lit review (Inglehart-Welzel + Big Five + verified 2024-2026 LLM-applied work)
├── theory_interpretation_guide.md     ← Discussion-section memo (lean replacement for the deprecated theory-bin appendix)
├── tier1_tool_schemas.md              ← output schemas for Shapley + Battery LOO secondary tools
├── gss_variables_to_download.md       ← record of GSS Data Explorer variable list
├── gss_feature_taxonomy.json          ← LOCKED v0.3: 12 primary_eval, 118 sensitivity_eval, 140 features × 4 bins
├── gss_battery_map.json               ← LOCKED **v0.2** (2026-05-09 evening): 34 batteries (D=7 / B=10 / P=2 / A=15) + 17 singletons (R1 leakage exclusion + co-primary Battery LOO across all 4 bins)
├── outputs/primary_eval_human_variance_2024.json ← LOCKED DQ-3 reference (per-item human variance from GSS 2024)
├── gss_loader.py                      ← reads 3-batch GSS extract → pandas DataFrame; label-set namespacing
├── validate_taxonomy.py               ← 10-check validator (incl. 7c battery map): vars exist, bins disjoint, coverage, missingness, override-vs-truth-codes, battery map well-formedness
├── gss_pipeline.py                    ← AUDIT primitives: persona prompt builder, eval question formatter, scorer, aggregation, multi-model panel synthesis, battery exclusion (R1)
├── llm_router.py                      ← OpenRouter / OpenAI client with retry+backoff; locked model panel
├── gss_driver.py                      ← top-level orchestrator: respondents × conditions × items × models loop with atomic-write resumability + R1 per-item battery exclusion + item-level sensitivity resume + I-10 reproducibility guard
├── select_phase1b_model.py            ← §12.2 quality-primary rule executable; DQ-1 + DQ-3 (per-item relative ≥30% × human var) + cost tie-break + Qwen fallback; 5-branch self-test
├── regression_baseline.py             ← R2 leakage-hygiene partition (Layer 4): non-LLM regression baseline; LLM gain over regression = persona-reasoning contribution
│
├── ── EXPECTED-AT-RUNTIME (after smoke test, gitignored where appropriate) ──
│   outputs/gss_phase1_records_n{N}_*.json          ← raw LLM outputs + scores per (resp, cond, model)
│   outputs/gss_phase1_per_respondent.csv           ← per-respondent metrics (built post-run)
│   outputs/gss_phase1_headline.csv                 ← multi-model headline + LOO ΔMAE + CIs
│   outputs/gss_phase1_persona_answers.json         ← diagnostic per-item record
│   OpenRouter_api.txt                              ← (gitignored) OpenRouter API key
│
├── ── PHASE 2 (COOKIY-TARGETED) DESIGN ──
├── thesis_phase2_design.md            ← Phase 2 design (BFI + econ games, smaller N + 2-week recontact)
│
├── ── PILOT PHASE COOKIY ARTIFACTS ──
├── cookiy_brief.md                    ← Study 1 brief (interview arm)
├── cookiy_brief_study2.md             ← Study 2 brief (survey arm)
├── cookiy_guide_session1.md           ← Cookiy auto-generated discussion guide (S1)
├── cookiy_guide_session2.md           ← Cookiy auto-generated discussion guide (S2)
├── eval_battery.json                  ← 15-item held-out eval, with regex anchors
├── eval_answers_extracted.csv         ← parsed truth: 15 items × 3 respondents (GOLD)
├── construction_answers_extracted.csv ← parsed truth: 18 construction items × 1 respondent
├── metrics_per_respondent.csv         ← notebook scoring: 12 conditions × full eval metrics
│
├── ── PILOT PIPELINE CODE ──
├── persona_pipeline.py                ← script-style pipeline (responses/ layout)
├── persona_pipeline.ipynb             ← CANONICAL pilot pipeline (31 cells, incl. LOO)
├── run_notebook_local.py              ← runner: executes the notebook outside Colab
├── parse_eval_answers.py              ← smart parser using moderator confirmations as gold
├── parse_construction_answers.py      ← parser for Study 2 construction items
├── rescore_with_leakage_audit.py      ← post-hoc rescoring under STRONG/SOFT/CLEAN filters
├── make_robustness_chart.py           ← chart generator for the leakage audit
├── build_site_data.py                 ← CSV→JSON for docs/data/
├── build_notebook.py                  ← (Cowork-built — assembles persona_pipeline.ipynb)
│
├── ── GITIGNORED (PII + secrets) ──
├── interview_quality_audit.md         ← Study 1 transcript quality audit (verbatim quotes)
├── survey_quality_audit.md            ← Study 2 transcript quality audit (verbatim quotes)
├── leakage_audit.json                 ← per-item leakage tags + evidence quotes
├── Openai_api.txt                     ← API key
├── 2411.10109v2.pdf                   ← Park v2 paper (kept local for reference)
│
├── cookiy_transcripts/                ← raw Cookiy outputs (verbatim PII)
│   ├── study1_interview_p{1,2}.{txt,json}
│   ├── study2_survey_p1.{txt,json}
│   └── study{1,2}_report.{md,json}
│
├── responses/        R{1,2}/{transcript.txt,demographics.json}
├── responses_s2/     R1/{transcript.txt,demographics.json}
│
├── data/gss/                          ← GSS Data Explorer extracts (NOT public; large; partly PII)
│   ├── 390data1/{batch1,batch2,batch3}/  ← active extract: 973 vars × 75,699 rows
│   │   ├── GSS.dat   (fixed-width data)
│   │   ├── GSS.do    (Stata import script with col specs + labels)
│   │   └── post_processing_output.json
│   └── archive/                       ← older extract attempts
│
├── ── PIPELINE OUTPUTS ──
├── outputs/                           ← all pilot-pipeline-derivative artifacts
│   ├── metrics_with_leakage_audit.csv
│   ├── chart_robustness.png
│   ├── persona_answers_full.json      (gitignored — embeds prompts)
│   └── logs/                          (gitignored — runner logs)
│
├── ── DASHBOARD ──
├── docs/                              ← static GitHub Pages dashboard for pilot
│   ├── index.html, style.css, app.js, README.md
│   └── data/
│       ├── metrics_per_respondent.json
│       ├── metrics_with_leakage_audit.json
│       ├── metrics_aggregate.json
│       └── eval_answers_extracted.json
│
├── ── HISTORICAL ──
├── archive/                           ← stale pre-pivot files (pilot history)
├── test/                              ← synthetic transcript fixtures
│
└── (also gitignored: GSBGEN390_Application_*.docx, __pycache__/, *.pdf)
```

### Where each file is read from / written to

#### Pilot phase (Cookiy)

| File | Read by | Written by |
|---|---|---|
| `eval_battery.json` | notebook, `persona_pipeline.py` | (manual) |
| `eval_answers_extracted.csv` | `rescore_with_leakage_audit.py`, `build_site_data.py` | `parse_eval_answers.py` |
| `construction_answers_extracted.csv` | (reference) | `parse_construction_answers.py` |
| `metrics_per_respondent.csv` | `build_site_data.py` | notebook cell 30 |
| `outputs/metrics_with_leakage_audit.csv` | `make_robustness_chart.py`, `build_site_data.py` | `rescore_with_leakage_audit.py` |
| `outputs/persona_answers_full.json` | `rescore_with_leakage_audit.py` | `run_notebook_local.py` (end-of-run) |
| `outputs/chart_robustness.png` | (visual) | `make_robustness_chart.py` |
| `outputs/logs/run_*.log` | (manual review) | shell `tee` from `run_notebook_local.py` |
| `leakage_audit.json` | `rescore_with_leakage_audit.py` | (manual tagging — Joyce + Claude) |
| `docs/data/*.json` | `docs/app.js` (browser fetch) | `build_site_data.py` |

#### Phase 1 (GSS public)

| File | Read by | Written by |
|---|---|---|
| `data/gss/390data1/batch{1,2,3}/GSS.{dat,do}` | `gss_loader.py` | (downloaded from GSS Data Explorer 2026-05-02) |
| `gss_loader.py` | `validate_taxonomy.py`, `gss_pipeline.py`, `gss_driver.py` | (manual) |
| `gss_feature_taxonomy.json` (v0.3) | `validate_taxonomy.py`, `gss_pipeline.py`, `gss_driver.py` | (locked, audit-revised 2026-05-05) |
| `validate_taxonomy.py` | (manual integrity check) | — |
| `gss_pipeline.py` | `gss_driver.py` (calls AUDIT primitives), aggregation post-run | (built 2026-05-05) |
| `llm_router.py` | `gss_driver.py` (LLM calls) | (built 2026-05-05) |
| `gss_driver.py` | (top-level CLI) | — |
| `outputs/gss_phase1_records_n{N}_*.json` | (post-run aggregation script, TBD) | `gss_driver.py` (atomic-write per respondent) |

---

## How to resume in a fresh terminal / new Claude Cowork session

### To re-read everything and pick up the story (current Phase 1 build):
```bash
cd ~/Documents/GSBGEN390
# Read in this order for Phase 1 context:
#   1. STATUS.md (this file) — current state
#   2. CLAUDE.md — guidance for AI assistants
#   3. gss_phase1_design.md — Phase 1 locked design (esp. §10 aggregation, §12 multi-model panel)
#   4. gss_feature_taxonomy.json — eval and feature lists (v0.3)
# Then for pilot context:
#   5. MEETING_HANDOUT.md, WRITEUP.md, progress_report.md
```

### Phase 1 — IMMEDIATE NEXT STEP (task #6: N=10 smoke test)

**1. Get an OpenRouter API key:** https://openrouter.ai/keys → load $5 in credits.

**2. Drop the key in the project root** (file is gitignored):
```bash
echo "sk-or-v1-XXXXXX..." > ~/Documents/GSBGEN390/OpenRouter_api.txt
git status   # confirm OpenRouter_api.txt is NOT shown — gitignored via *api* pattern
```

**3. Run smoke tests in escalating order:**
```bash
cd ~/Documents/GSBGEN390

# (a) Verify API key works on one model — ~$0.001, ~5s
python3 llm_router.py --smoke-one

# (b) Verify the 4-model panel responds — ~$0.005, ~30s
python3 llm_router.py --smoke-panel

# (c) Single respondent / single model / primary only — ~$0.02, ~1 min
python3 gss_driver.py --smoke

# (d) Full N=10 panel, primary only — ~$0.70, ~30-60 min sequential
python3 gss_driver.py --n 10 --primary-only

# (e) (optional) Full N=10 with sensitivity pass — ~$2.00, ~2-3 hours sequential
python3 gss_driver.py --n 10
```

**4. After smoke green:** commit the records JSON (it's anonymized — only respondent ID_ codes + LLM outputs, no transcripts), then move to OSF pre-registration draft (task #7).

### Phase 1 — already-validated commands (no API; safe anytime)

```bash
# Loader + taxonomy validation
python3 gss_loader.py
python3 validate_taxonomy.py

# Audit checkpoint smoke tests (all pass; pure synthetic + parsed data)
python3 gss_pipeline.py --print-prompt          # AUDIT-A
python3 gss_pipeline.py --print-questions       # AUDIT-B
python3 gss_pipeline.py --test-scoring          # AUDIT-C
python3 gss_pipeline.py --test-exclusion        # AUDIT-D
python3 gss_pipeline.py --test-aggregation      # AUDIT-E
python3 gss_pipeline.py --test-multimodel       # multi-model extension
```

### Driver CLI reference

```bash
python3 gss_driver.py --smoke                   # 1 resp / 1 model / primary only (cheapest)
python3 gss_driver.py --n 10 --primary-only     # full panel, primary only
python3 gss_driver.py --n 10                    # full panel + sensitivity pass
python3 gss_driver.py --anchor --n 100          # GPT-4o anchor on N=100, primary only, n=2
python3 gss_driver.py --n 1500                  # Phase 1b primary (after pre-reg)
python3 gss_driver.py --n 1500 --sensitivity-only  # fill in sensitivity after primary done
python3 gss_driver.py --models qwen/qwen-2.5-72b-instruct  # custom model list
python3 gss_driver.py --no-resume               # ignore existing output, start fresh
```

Output format: each run writes `outputs/gss_phase1_records_n{N}_*.json` — a JSON list of records, one per (respondent, condition, model). Per-item per-sample scores nested inside `per_item_scores`. Atomic-write per respondent — kill the process and resume with the same command + default `--resume` (on by default).

### Pilot phase commands (still works, for the Cookiy pipeline)

**Re-run pilot pipeline** (~9 min, $3-5 in API):
```bash
export OPENAI_API_KEY=$(cat Openai_api.txt)
python3 -u run_notebook_local.py 2>&1 | tee outputs/logs/run_$(date +%Y%m%d_%H%M).log
python3 rescore_with_leakage_audit.py
python3 make_robustness_chart.py
python3 build_site_data.py
```

**Re-run rescoring only** (no API, ~1s) — if `outputs/persona_answers_full.json` exists:
```bash
python3 rescore_with_leakage_audit.py
python3 make_robustness_chart.py
python3 build_site_data.py
```

### Known runtime gotchas

**Phase 1 / GSS:**
- GSS DE splits the 973-variable extract into **3 batches** — `gss_loader.py` merges them horizontally. If you re-download, expect 3 batch folders.
- Label-set names (e.g., `GSP002X`) **collide across batches** with different contents. The loader namespaces them per-batch (`b0_GSP002X`, `b1_GSP002X`) to avoid wrong labels.
- The repeated identifier columns are `YEAR` AND `ID_` (with trailing underscore). Loader drops `ID_` from batches 2-3 and asserts row alignment via per-row equality on YEAR + ID_. Final shape = 3,309 × 973.
- GSS missing-value codes are negative integers in `{-100, -99, -98, -97, -96, -95, -90, -80, -70, -60, -50, -40}`. Loader exposes `is_missing()` and `truth_code_or_none()` helpers. **Ballot rotation** means many GSS items aren't asked of every respondent; aggregation rule (gss_phase1_design.md §10) handles via respondent-macro averaging.

**Phase 1 / LLM panel:**
- OpenRouter API key required before any actual LLM call. Put in `OpenRouter_api.txt` at project root (gitignored via `*api*` pattern).
- The 4-cheap-panel run is sequential (~30-60 min for N=10 primary). Could parallelize via threadpool/async — not a priority; smoke first.
- Each model has different rate limits on OpenRouter. Dispatcher has 8-attempt exponential backoff (caps at 60s/delay) for 429/timeout/connection/5xx errors.
- `gss_driver.py` writes `outputs/gss_phase1_records_n{N}_*.json` atomically per respondent. Resumable: rerun the same command and it skips already-done (respondent, condition, model) tuples.
- PARTYID code 7 = "Other party" is contingent: scored as Likert MAE on 0-6, categorical exact-match when either side outputs 7 (per AUDIT-C.3).
- HELPPOOR has sparse codebook anchors at 1, 3, 5; codes 2 and 4 are valid intermediate positions (per AUDIT-B.4 instruction).

**Pilot phase:**
- TPM rate limit: account is at 30K tokens/min for gpt-4o. Condition C prompts hit this; the runner has retry+exponential-backoff.
- Cell 8 in the notebook uses `google.colab.files.upload()` which doesn't work locally. The runner replaces this with disk reads from `cookiy_transcripts/`.
- Cell 16 uses `display()` (Jupyter built-in). The runner stubs this to `print()`.
- Jupyter magics (`!pip`, `%`) in cells are silently skipped by the runner.
- `LLM_CACHE` is in-memory only — every fresh process re-runs all 240+ API calls. The runner persists `persona_answers_full.json` end-of-run; the rescoring script reads from that without API calls.

---

## Pending work (post-meeting decisions)

> **Frozen 2026-04-30 (pilot wrap state).** The bullets below were the open list at the end of the pilot, before the 2026-05-02 Phase 1 lock and the 2026-05-09 lean-lock. Phase 1 design questions are now settled in `gss_phase1_design.md`; Phase 2 questions live in `thesis_phase2_design.md`; current next-actions are in HANDOFF §6 + the TL;DR at the top of this file. Kept here as historical context.

1. **3-5 page formal writeup** — methods, pipeline, results, leakage audit, comparison to Park v2's per-outcome 74/83/82/86% (with caveats: ≈ tie on GSS only; surveys lag by 0.15 BFI / 0.28 games), limitations, next steps. Awaits Bayati feedback.
1a. **Phase 1 — GSS public-data feature-importance analysis** (proposed; see [`gss_phase1_design.md`](gss_phase1_design.md)). Uses GSS Three-Wave Panel 2010-2014 (N≈1,500), provides first test-retest-normalized-accuracy comparison to Park's 0.82-0.83. Covers GSS-attitudes outcome row only. Budget ~$300-500, timeline 1-4 weeks. Awaiting Bayati endorsement. *[Endorsed 2026-05-02; design subsequently revised to GSS 2024 single-wave snapshot, raw-only, ~$215 — see TL;DR.]*
1b. **Phase 2 — Interview-decomposed feature-importance study** (proposed; see [`thesis_phase2_design.md`](thesis_phase2_design.md)). Prolific N=20-30, 30-45 min modular long interview (4 modules ↔ 4 feature bins), 2-week wait, BFI-44 + behavioral-game vignettes + GSS as held-out outcomes. LOO ablation operates **at the interview-content level** — decomposes Park's "interview-only" condition into pre-registered content bins. Covers BFI (0.15 gap) and games (0.28 gap) rows that Phase 1 cannot. Requires platform pivot to Prolific + self-hosted OpenAI Realtime API moderator (Cookiy 15-min cap incompatible). Budget ~$1,500-1,750, timeline 7-9 weeks. Awaiting Bayati endorsement of platform pivot + N + module structure.
2. **Multi-seed run-variance estimate** — re-run pipeline 5-10 times with different seeds to bound LOO ranking instability at N=1. Honest answer to "how reliable is this LOO?"
3. **2-week-separated re-collection (likely needed)** — Cookiy can't recontact panel respondents, so this requires a different platform (Prolific custom script, or recruiting in-house). Without this, the C-condition's win is technically defensible only via the leakage-audit argument, not via Park-protocol comparability. *[Absorbed into Phase 2 design.]*
4. **BFI-44 upgrade** — at 2 items/trait, BFI trait RMSE is statistically meaningless. Real study should use BFI-44. *[Absorbed into Phase 2 design.]*
5. **Larger N** — pilot N=2+1 → thesis target probably N≥30 per arm based on what's needed for stable LOO ranking + ablation effect estimation. *[Phase 1: N=1500 GSS; Phase 2: N=20-30 with power calc.]*
6. **Survey-instrument design for thesis** — 8-15 items per category × 4 categories = 60+ construction items. Pilot's 5/5/4/4 split is illustrative only. *[Absorbed into Phase 2 design.]*

---

## Open methodological questions for Bayati meeting

> **Frozen 2026-04-30.** These were the questions queued for the 2026-05-02 Bayati meeting; that meeting locked the Phase 1 direction (GSS-first → Phase 2 Cookiy + 4-bin taxonomy + pre-reg before Phase 1a). Most items below are now answered or absorbed into Phase 2 (`thesis_phase2_design.md`). Current open items for Bayati are in HANDOFF §8.

1. Is the leakage-filtered analysis (manual STRONG-tagging + strict-clean MAE column) sufficient defense of the C-condition result, or does the thesis-stage replication need 2-week-separated collection regardless?
2. **LOO ranking instability at N=1**: across two pipeline runs at temp 0.7, the "most-important-when-dropped" category changed (psychological → demographic). What N + how many seeds buy a stable ranking?
3. Park's denominator is `% of test-retest reliability`. We don't have that. Worth running a 2-week self-retest with the 3 pilot respondents to recover a denominator, or accept the gap and never quote a single number against Park's?
4. BFI-10 → BFI-44 upgrade for the thesis-stage study: yes/no?
5. Does our 4-category taxonomy (demographic / behavioral / psychological / attitudinal) extend cleanly when N grows, or do we need finer subdivisions?
6. Cookiy as the data-collection platform for the thesis — keep, or switch (e.g., Prolific + custom script for verbatim eval items + 2-week recontact)?

---

## Key decisions log

- **2026-04-29**: Started Joyce-as-only-participant. Pivoted to multi-respondent panel after methodology objection.
- **2026-04-29**: Cookiy 15-min cap discovered. Tried 2-session pairing; Cookiy panel can't pair across studies. Collapsed to single combined session per respondent.
- **2026-04-29**: Added Study 2 (survey-only) to mirror Park's main framework. Between-subjects acceptable at pilot scale.
- **2026-04-29**: N constrained to 2 (Study 1) + 1 (Study 2). Pilot reframed as feasibility demonstration, not statistical comparison.
- **2026-04-29**: In-session eval priming acknowledged as known deviation; absolute accuracy may be inflated.
- **2026-04-30 morning**: Cookiy delivered all 3 transcripts. Smart parser → 15/15 × 3.
- **2026-04-30 evening**: 6 pre-flight fixes applied (paths, demographics, anchors, CSV truth, TypeError, splitter). Pipeline ran end-to-end on laptop with retry/backoff. Leakage audit + robustness chart produced. **Park-was-AI-not-human correction propagated through 5 docs.**
- **2026-04-30 late evening**: GitHub repo created at `Joyceqx/gsbgen390-persona-pipeline` and pushed; GitHub Pages enabled on `/docs`. Project folder tidied: derivative outputs moved into `outputs/` (logs to `outputs/logs/`); pre-pivot stale files moved into `archive/`; code paths in `rescore_with_leakage_audit.py`, `make_robustness_chart.py`, `build_site_data.py`, `run_notebook_local.py` updated for new locations and verified by re-running the post-pipeline rescore + chart + site-build pipeline end-to-end.
- **2026-04-30 late night — Thesis-stage two-phase plan committed.** Phase 1 = GSS public-data feature-importance (`gss_phase1_design.md`). Phase 2 = interview-decomposed study (`thesis_phase2_design.md`). Phase 2 replaces an earlier "paired structured survey" idea after Joyce noted that the actual question — *what's IN the interview that surveys can't capture* — requires interview decomposition, not survey-feature ablation. Phase 2 forces a platform pivot: Cookiy 15-min cap is incompatible with 30-45 min modular long interview, so Phase 2 will use Prolific + a self-hosted OpenAI Realtime API moderator. Composed deliverable = the full 4×3 feature-category × outcome-dimension matrix.
- **2026-04-30 night — Park v1 vs v2 reconciliation + outcome-stratified narrative pivot.** Verified directly from both v1 and v2 PDFs that the proposal's "85%" headline came from v1's interview-based normalized accuracy (~0.85), while v2 reorganized conditions and reports the four numbers we now cite (74/82/83/86%). Both versions live at the same arXiv ID; we adopt v2 framing throughout. **Critical refinement**: the "surveys ≈ interview" tie holds only on GSS attitudes — v2 also reports surveys lagging interviews by 0.15 on BFI-44 personality and by 0.28 on behavioral economic games. Thesis question reframed from "can surveys substitute for interviews?" to **outcome-stratified** "which feature categories close which parts of that gap on which outcomes?" Batch update propagated through `MEETING_HANDOUT.md`, `README.md`, `replication_scoping.md`, `EXPLAIN_ZH.md`, `LIT_REVIEW.md`, `PRIMER.md`, `FUTURE_DESIGN.md`, `progress_report.md`, `docs/index.html`, and this STATUS file.
- **2026-05-02 — Bayati meeting; Phase 1 design locked.** Direction confirmed: GSS-first then targeted Cookiy. **Path A\* locked**: Path B (12 curated items) as primary for the LOO; Path A (Park's full ~118 items) as sensitivity. Snapshot prediction on a single GSS wave (no panel for prediction). Raw accuracy as primary metric — no test-retest normalization in Phase 1; deferred to Phase 2's recontact arm. Persona self-consistency reported as supplementary stability check. Resolution rule for disjoint sets: features = (declared bin lists) MINUS primary_eval (only); sensitivity-pass handles per-item leakage separately. This rule preserves a populated psychological feature bin in GSS, which would otherwise be empty.
- **2026-05-02 — Phase 1 data + tooling shipped.** GSS 2024 cross-section (3,309 respondents × 973 unique variables) downloaded via GSS Data Explorer in 3-batch fixed-width format. `gss_loader.py` written: parses each batch's `.do` script for column specs + variable labels + value labels, reads the corresponding `.dat` fixed-width file, namespaces label-set names per batch (avoids cross-batch label collisions), merges 3 batches horizontally. Verified 22/22 key Park variables present with correct labels. `gss_feature_taxonomy.json` initially locked at 23/29/8/80 (140 total); subsequently revised to v0.3 final counts 24/25/8/83 after the AUDIT-A reclassifications of 2026-05-05. `validate_taxonomy.py` confirms variable presence, bin disjointness, per-respondent coverage.
- **2026-05-05 morning — Codex audit fixes (1st round).** 5 critical issues fixed: (a) gss_phase1_design.md rewritten end-to-end to match locked snapshot/raw-accuracy design (was internally inconsistent, mixing old 2010-2014 panel design with new 2024 snapshot); (b) Park comparability claims softened to "raw / per-item" only ("not directly numerically comparable to Park's normalized accuracy"); (c) feature-bin leakage rule rewritten to be self-consistent — declared bins disjoint from primary_eval, sensitivity items may be in features with per-item exclusion; (d) PARTYID removed from attitudinal feature bin (it's in primary_eval); (e) loader batch merge now verifies row alignment via per-row YEAR + ID_ equality, fixed ID_ vs ID column drop bug (final shape now correctly 973). validate_taxonomy.py rewritten with 9 explicit checks; raises SystemExit(1) on failure.
- **2026-05-05 morning — gss_pipeline.py AUDIT-A built + taxonomy v0.3.** Persona prompt template scaffold; AUDIT-A inspection of a sample prompt revealed 4 conceptual mis-categorizations: ETHNIC moved behavioral → demographic; XMARSEX/HOMOSEX/GRASS moved behavioral → attitudinal (these GSS items ask opinions, not behaviors). Net counts now: demographic 24, behavioral 25, psychological 8, attitudinal 83 (still 140 total).
- **2026-05-05 mid-day — AUDIT B/C/D scaffold + Codex audit fixes (2nd round).** AUDIT-B eval question phrasing: unified format (GSS question + numbered options + "output single integer"). 4 stem overrides for FECHLD/FEPOL/RACDIF1/HELPPOOR with canonical GSS codebook wording (overrides terse `.do` `label var` summaries that were ambiguous). PARTYID presents all 8 codes 0-7. AUDIT-C scoring: Likert MAE for likert3-7, categorical for binary, contingent treatment for PARTYID code 7, parse-failure tracking, missing-truth handling (truth_code_or_none helper). 7 hand-test assertions pass. AUDIT-D sensitivity per-item exclusion: build_persona_prompt(exclude_vars=...). Hard-asserted smoke test: when excluding X, X disappears from prompt AND other sensitivity items remain. 2nd Codex audit: 4 important + 4 minor issues — all fixed (assertion strength, missing-truth converter, paired-bootstrap explicit, stale docstrings, etc.).
- **2026-05-05 afternoon — AUDIT-E aggregation built.** Respondent-macro (PRIMARY) + item-macro + pooled (secondary). Bootstrap CIs at respondent level B=1000 percentile. LOO ΔMAE via PAIRED bootstrap (resample respondents once, compute Full and LOO from same resample, then delta — explicitly enforced in code, with caveat that mathematically equivalent to bootstrap of per-respondent paired deltas). 5 hand-test assertions pass.
- **2026-05-05 evening — multi-model panel redesign (locked).** GPT-4o-only would cost ~$900 at N=1500 (over budget). Redesigned to **4 OpenRouter cheap models** (Qwen-2.5-72B / DeepSeek-V3.1 / MiniMax-M1 / Kimi K2) with n_samples=1 each as PRIMARY + **GPT-4o anchor** on N=50 subset, primary conditions only, n_samples=2 for direct Park v2 Table 3 comparability. Headline = panel median across 4 cheap models; cross-model agreement % replaces within-model self-consistency as primary stability metric. Pre-registration must declare the exact 4-cheap-model list. Total Phase 1b budget ~$420 (within $300-500 envelope). Methodological strengthening: "feature-category contribution generalizes across 4 LLM families" is a stronger claim than "tested on GPT-4o." See gss_phase1_design.md §12.
- **2026-05-05 evening — LLM dispatcher + driver + multi-model aggregation built.** llm_router.py (OpenRouter / OpenAI client with 8-attempt exponential backoff, locked panel constants, smoke-test CLI). gss_driver.py (top-level orchestrator with atomic-write resumability per respondent; CLI: --smoke / --anchor / --n / --primary-only / --sensitivity-only / --models / --no-resume). gss_pipeline.py extended with multi-model aggregation: filter_records_by_model, synthesize_panel_median_records (median across models, snap to valid code, re-score), cross_model_agreement_pct, compute_phase1_headline_multimodel orchestrator. All 6 audit smoke tests pass; multi-model orchestrator tested on synthetic 4-model × 2-resp data with hand-checked agreement % and panel-median values. **Pipeline is 100% built.** Joyce just needs OpenRouter API key + run smoke tests in documented order.
