# OSF Pre-Registration v1 — GSBGEN390 Phase 1

## Feature Attribution for LLM Persona Synthesis: Hierarchical 4-Bin and 34-Battery LOO on GSS 2024 Attitude Outcomes

**Project lead**: Joyce Yu (Stanford GSB master's thesis program, 2026)
**Faculty advisor**: Prof. Mohsen Bayati
**OSF v1 draft date**: 2026-05-09 (Phase 1 design lean-locked + co-primary upgrade + cleanup audits absorbed)
**Companion repo**: https://github.com/Joyceqx/gsbgen390-persona-pipeline (commit `b5a9779`)
**Live design canonical source**: `gss_phase1_design.md` (in repo)

---

## 0. Frozen artifact references (SHA-256 hashes)

These three files are the load-bearing locked artifacts for this preregistration. Their SHA-256 hashes at OSF lock time are listed below. Any modification to these files after OSF lock that changes the hash is a pre-registration deviation and must be filed as an OSF amendment with explicit rationale.

| Artifact | Version | SHA-256 |
|---|---|---|
| `gss_feature_taxonomy.json` | v0.3 (2026-05-05 lock) | `265160aa55df47f690a23fa8898e12f13a374b4037934b1745adf9fd1b573191` |
| `gss_battery_map.json` | v0.2 (2026-05-09 evening lock) | `6e138c9979cec90ee45f786d3777c2ce270de575af821b56643626a7714dcf0c` |
| `outputs/primary_eval_human_variance_2024.json` | locked 2026-05-08 | `b7b64cb2f9e4f5397983c356ffd9ca686fc5f1bc60ee57a76272ec0543e2eb27` |

**Source data**: GSS 2024 cross-section, 3-batch fixed-width extract from GSS Data Explorer (`data/gss/390data1/`). N=3,309 respondents × 973 unique variables (after merging the 3 batches). The pre-registered analysis sample is N=1,500 drawn without replacement using fixed seed=42.

---

## 1. Research question and estimand

### 1.1 Phase 1 research question

> Within attitude prediction (single-wave snapshot setting), which of four survey-collectible feature categories (demographic / behavioral / psychological / attitudinal) most contributes to LLM-persona prediction of held-out attitudinal items, and within each pre-registered bin, which construct-level batteries drive the predictive signal?

### 1.2 Project-level question (broader research direction)

> In LLM persona synthesis, which input feature categories drive prediction quality, and how does that contribution vary across outcome dimensions?

Phase 1 answers this for the **attitude** outcome dimension. Phase 2 (separate preregistration; not in scope here) extends to personality (BFI-44) and behavioral economic games via targeted Cookiy collection with 2-week recontact baseline.

### 1.3 Estimand

> Phase 1 estimates **single-wave GSS 2024 prediction** of held-out attitudinal items (12 `primary_eval` items + 118 `sensitivity_eval` items used for cross-paper benchmarking) **from same-wave GSS feature variables**, decomposed into the contribution of four pre-registered feature categories and (within bin) 34 pre-registered construct-level batteries.

This is **explicitly NOT**:
- Test-retest prediction (no GSS 2024 recontact baseline available).
- Cross-wave or longitudinal prediction (no panel structure used).
- Normalized persona fidelity (no test-retest denominator).
- A claim about general human-simulation ability.
- Population inference about U.S. adult attitudes (see §1.4).

It **is**: feature-category and battery-level contribution analysis within single-wave GSS-attitude prediction, on the GSS-2024 cross-section as a fixed dataset.

### 1.4 Inferential frame (locked 2026-05-09 night)

The bootstrap (paired-respondent-level, B=1000, seed=42) assumes simple random sampling. GSS 2024 is a multi-stage probability sample with PSU + strata + sampling weights. **We explicitly restrict the inferential frame to the GSS-2024 cross-section as a fixed dataset** — i.e., we estimate predictive properties on this specific 3,309-respondent extract, NOT population-level parameters. All "respondent-level" language refers to the sampled 1,500/3,309 from this fixed dataset. We do NOT claim population inference. A weighted/cluster-bootstrap robustness check using `WTSSALL` + PSU is a future-work extension; if pursued, reported as a separate sensitivity column with explicit fixed-dataset-vs-population labeling.

### 1.5 Honest scope statement

This pre-registration covers a feature-attribution study under leakage hygiene. It does NOT cover:
- General human-simulation fidelity (no test-retest).
- Causal feature importance (LOO + Battery LOO estimate predictive dependence under a fixed prompt-construction procedure, NOT causal effects).
- Robust generalization across LLM families beyond the N=100 1a comparison (the 4-cheap-panel members are all China-trained; GPT-4o anchor is the only Western reference).

The contribution claimed at submission is: a **leakage-clean, preregistered, large-N hierarchical feature-attribution framework for LLM persona prediction of public-survey attitudes**.

---

## 2. Park et al. 2024 v2 as benchmarking anchor (NOT research framework)

Park et al. 2024 ("Generative Agent Simulations of 1,000 People", arXiv:2411.10109 v2) is the most-cited prior work in LLM persona simulation. This project uses Park as a **cross-paper benchmarking anchor only**:

- **N=100 GPT-4o anchor subset** of Phase 1b: per-item raw accuracy on the 118 `sensitivity_eval` items, directly comparable to Park v2 SI Table 3 entries.
- **NOT** used: Park v2's normalized accuracy framing, Park's interview-vs-survey comparison structure, Park's specific item exclusions beyond the 118 we keep.

Park serves the same role as Argyle 2023 / Aher 2023 / Bisbee 2024 / Hewitt 2024 / Manning 2024 / Centaur 2025 in the literature review — one important prior work, not the project's defining framework. The research question (feature attribution for LLM persona synthesis) exists independently of Park.

---

## 3. Sampling, sample, eval set

### 3.1 Sampling rule (locked)

- **Source**: GSS 2024 cross-section, N=3,309, all variables in 3-batch extract.
- **Sample size**: N=1,500 respondents drawn without replacement.
- **Seed**: 42 (locked; `gss_pipeline.py:sample_respondents`).
- **Stratification**: NONE. No oversampling on demographics or topics.
- **Weighting**: NONE in the primary analysis (per §1.4 fixed-dataset frame).

### 3.2 Eval set (Path A* design, locked v0.3)

- **Primary eval (the headline)**: 12 curated `primary_eval` items. Each represents a distinct GSS construct family and is the only primary_eval item from its battery (where its battery is also in `sensitivity_eval`). Listed in `gss_feature_taxonomy.json`.
- **Sensitivity eval (Park-comparable)**: 118 `sensitivity_eval` items. Park v2's GSS list minus 15 retired/renamed items in 2024. Used only on the GPT-4o anchor (N=100 subset) for per-item raw accuracy benchmarking against Park v2 SI Table 3.
- **No LOO on sensitivity_eval**. Per-item exclusion only when predicting an item.

### 3.3 Feature taxonomy v0.3 (140 features × 4 bins)

| Bin | n | Examples |
|---|---|---|
| Demographic | 24 | AGE, SEX, RACE, EDUC, INCOME16, REGION, MARITAL, ... |
| Behavioral | 25 | ATTEND, PRAY, NEWS, VOTE16, OWNGUN, WRKSTAT, ... |
| Psychological | 8 | HAPPY, HEALTH, FAIR, HELPFUL, TRUST, HAPMAR, SATJOB, LIFE |
| Attitudinal | 83 | ABANY+AB*, CON*, NAT*, FE*, RAC*, civil-lib*, religious_belief*, ... |

`gss_feature_taxonomy.json` v0.3 enforces: feature_bins ⊥ primary_eval; bins are mutually disjoint; every variable exists in the loaded data. `validate_taxonomy.py` 10 checks confirm.

---

## 4. Battery map v0.2 (34 batteries + 17 singletons)

`gss_battery_map.json` v0.2 (locked 2026-05-09 evening). 34 batteries across all 4 bins:

| Bin | n batteries | Battery names |
|---|---|---|
| Demographic | 7 | own_education, parental_education, marital_status, racial_ethnic_origin, family_of_origin_economic, growing_up_geography, growing_up_family_structure |
| Behavioral | 10 | current_religious_intensity, denominational_identity, voting_turnout, voting_choice, current_employment, work_history, job_security_perception, traditional_media, digital_media, gun_related |
| Psychological | 2 | subjective_wellbeing, interpersonal_trust |
| Attitudinal | 15 | abortion, confidence_in_institutions, national_priorities, racial_inequality_perception, gender_role_attitudes, civil_lib_atheists, civil_lib_racists, civil_lib_communists, sexual_morality, moral_legalization, adolescent_sex_policy, religious_belief, economic_help, end_of_life, police_use_of_force |

Battery design principles (locked):
- Items in the same battery measure the same underlying construct closely enough that LOO must drop them together.
- Split when sub-construct, target group, time point, or response scale differs sufficiently to conflate distinct signals (e.g., civil_lib split by target group; voting_turnout split from voting_choice by scale; INCOME16 NOT in family_of_origin_economic because different time point).

Validator check 7c confirms: every battery's `bin` field matches the actual taxonomy bin; per-bin counts (7/10/2/15) match v0.2 expectations; no item in two batteries; every primary_eval item is in a battery OR singletons list.

---

## 5. Leakage hygiene — 4 layers

**Layer 1 — Disjointness**: declared feature bins are disjoint from `primary_eval` (validator-enforced).

**Layer 2 — GSS-internal synonymy = empty**: Park v2 SI §9 (PDF p.10) reports their cross-instrument synonym audit found zero synonymous pairs within the GSS itself. We adopt this finding and do not re-audit.

**Layer 3 — R1 (battery-level structural exclusion)**: When predicting any primary_eval item that belongs to a battery (per `gss_battery_map.json` v0.2), the entire battery is dropped from the persona prompt for that prediction. This mirrors Park v2's BFI whole-trait-block hold-out (Park v2 SI §5, PDF p.37). Implemented in `gss_pipeline.py::battery_excludes_for_item` and applied in `gss_driver.py::run_primary_one_respondent`.

**Layer 4 — R2 (regression-baseline comparator)**: Alongside the LLM panel, run a non-LLM regression baseline (`regression_baseline.py`: Ridge for Likert, multinomial Logistic for binary; 5-fold respondent-level CV; same R1 battery exclusion applied symmetrically). The regression's per-item MAE is the auto-correlation upper bound any feature-to-item predictor can extract from the same input. The headline comparator approximates:

> LLM_panel_MAE on item X ≈ regression_MAE on X + LLM_gain_over_regression

**Caveat (locked)**: this is a useful rhetorical decomposition, **not a literal causal partition** of LLM behavior. "LLM gain over regression" is evidence of model-specific predictive value beyond a simple supervised baseline, NOT direct proof of human-like reasoning. Discussion-section language must respect this caveat.

---

## 6. LLM panel design

### 6.1 Phase 1a (N=100, multi-model)

- 4 cheap OpenRouter models: Qwen-2.5-72B-Instruct, DeepSeek-V3.1, MiniMax-M1, Kimi K2.
- n_samples = 1 per (respondent, condition, item).
- 5 prompt conditions: Full + 4 LOO (drop demographic / behavioral / psychological / attitudinal).
- + GPT-4o anchor on the same N=100, n_samples = 2, primary conditions only.
- Cost ~$65.

### 6.2 §12.2 model-selection rule (Phase 1a → Phase 1b)

After Phase 1a completes, run `select_phase1b_model.py` to deterministically select the Phase 1b model. The locked rule:

```
primary_score(model) = respondent-macro Likert MAE on 1a primary_eval (full condition only)
choose argmin among DQ-passers
  DQ-1: parse_failure_rate > 30% → disqualify
  DQ-3: per-item relative variance:
        var(model_i) ≥ 0.30 × var(human_2024_i) for ≥50% of items
        (human variance reference: outputs/primary_eval_human_variance_2024.json)
tie-break: within 5% of best MAE, pick lowest cost × (1 + parse_fail)
fallback:  Qwen-2.5-72B-Instruct (named) if all DQ-fail or quality+cost ties
```

`select_phase1b_model.py` implements this with 5-branch synthetic-fixture self-test (argmin_mae / tie_break_cost / fallback_qwen_dq / fallback_qwen_tie / fallback_qwen_no_data — all pass).

### 6.3 Phase 1b (N=1,500, single model)

- Single model selected by §12.2 rule on Phase 1a output.
- n_samples = 1.
- Same 5 prompt conditions as 1a.
- + GPT-4o anchor on the same N=100 subset of Phase 1b respondents.
- Cost ~$95 selected model + ~$50 anchor.

### 6.4 The N=1,500 headline

The N=1,500 headline is the **§12.2-selected single model**, NOT the panel median. The panel median is reported as a Phase 1a (N=100) robustness summary for cross-model coherence, NOT as the headline. Park comparison is via the N=100 GPT-4o anchor subset (per-item raw accuracy table side-by-side with Park v2 SI Table 3), NOT via normalized Park-style fidelity comparison.

### 6.5 Diversity-scope caveat

The 4 cheap-panel models are all China-trained (Alibaba / DeepSeek / MiniMax / Moonshot). The diversity is real across teams and RLHF philosophies but is **NOT** a Western-vs-Eastern training-data robustness check. The GPT-4o anchor provides the only Western-trained reference. Any "robust across LLM families" claim is restricted to **N=100 panel comparison** wording; the N=1,500 headline does not support cross-family generalization.

---

## 7. Aggregation rules (§10)

### 7.1 Per-respondent metric

For each (respondent r, condition c):
- For each Likert primary_eval item i that respondent r answered: compute `|persona_response - true_response|`; average within respondent across answered items.
- For each categorical primary_eval item: 1 if exact match, 0 otherwise; average across answered categorical items.

### 7.2 Headline aggregation

- **Primary**: respondent-macro-averaged Likert MAE. Each respondent contributes equally regardless of how many items they answered, provided they answered ≥1 Likert primary_eval item.
- **Standard errors**: paired-respondent-level bootstrap, B=1000, seed=42.

### 7.3 LOO ΔMAE

`ΔMAE_bin = MAE(LOO-drop-bin) − MAE(Full)`. Bootstrap CIs at respondent level via **paired bootstrap**: in each replicate, draw one respondent set with replacement, then compute MAE(Full) and MAE(LOO-drop-bin) on the same resample, then take the delta.

### 7.4 R1 asymmetric burden across primary_eval items (locked disclosure)

The R1 battery exclusion is asymmetric across the 12 primary_eval items because some have battery-mates inside primary_eval and others do not:

| Group | Items | R1 strips |
|---|---|---|
| In-battery primary_eval (4 of 12) | FECHLD, FEPOL (gender_role_attitudes, 5 items); CONFINAN, CONLEGIS (confidence_in_institutions, 13 items) | 5- or 13-item battery |
| Singleton primary_eval (8 of 12) | POLVIEWS, PARTYID, ABANY, CAPPUN, GUNLAW, RACDIF1, HELPPOOR, SATFIN | only the predicted item itself |

The respondent-macro MAE weights all 12 items equally, so the 4 in-battery items contribute under structurally thinner conditioning. **Pre-registered reporting rule**: alongside the headline 12-item respondent-macro MAE, also report (a) headline split between in-battery (4) vs singleton (8) primary_eval items, and (b) inverse-feature-count-weighted sensitivity column.

---

## 8. Multiplicity correction (§8.8)

**Two corrections in parallel.**

### 8.1 Within-bin nested Holm-Bonferroni primary

| Family | n tests | smallest p must clear |
|---|---|---|
| 4-bin LOO | 4 | α/4 = 0.0125 |
| Demographic battery LOO | 7 | α/7 = 0.00714 |
| Behavioral battery LOO | 10 | α/10 = 0.005 |
| Psychological battery LOO | 2 | α/2 = 0.025 |
| Attitudinal battery LOO | 15 | α/15 = 0.00333 |

### 8.2 Joint-34 Holm sensitivity layer

In addition to within-bin nested Holm, every battery is also tested against a joint Holm-Bonferroni at α=0.05 across all 34 batteries (smallest p < α/34 = 0.00147). This stricter correction is reported as a sensitivity layer used to gate cross-bin claims.

### 8.3 Within-bin vs cross-bin claim discipline

- **Within-bin claims** ("abortion is the strongest battery in the attitudinal bin") use **nested Holm only** — confirmatory within-bin.
- **Cross-bin claims** ("abortion is the strongest battery overall, ahead of subjective_wellbeing") require **joint-34 Holm sensitivity support**. Without joint-34 support, cross-bin language must be descriptive (e.g., "rank-ordered" rather than "significantly stronger").

### 8.4 Bin-level Shapley shares the 4-bin family

Bin-level Shapley decomposition is a robustness re-aggregation of the same 4-bin estimand; no separate Holm correction (it shares the 4-bin primary family).

### 8.5 Theory-bin LOO is NOT a confirmatory family

Theory framing enters Discussion section only. No theory-bin LOO confirmatory tests in this preregistration. Any future theory-bin amendment introduces its own Holm correction at amendment time.

---

## 9. Practical-effect-size thresholds (§8.9)

Because N=1,500 can render very small ΔMAE values statistically significant under Holm correction, every Battery LOO and 4-bin LOO ΔMAE is reported alongside a practical effect-size label:

| Label | Range |
|---|---|
| small / descriptive | ΔMAE < 0.02 |
| modest | 0.02 ≤ ΔMAE < 0.05 |
| substantive | ΔMAE ≥ 0.05 |

These thresholds correspond to "small-but-consequential" (~0.02 on a 1-5 Likert MAE) and "medium" (~0.05) in **Funder & Ozer (2019)** *"Evaluating Effect Sizes in Psychological Research: Sense and Nonsense"* (AMPPS, DOI: 10.1177/2515245919847202), applied to MAE on Likert scales.

A finding is reported as **substantively meaningful** only if **all** of:
1. Holm-significant within its family (nested Holm primary correction).
2. Practical effect-size label ∈ {modest, substantive}.
3. 95% bootstrap CI lower bound > 0.02 (CI excludes the small-effect boundary).

Statistical significance alone is not sufficient for headline-strength substantive interpretation. `n_items_in_battery` is reported alongside ΔMAE; `delta_mae_per_item` is reported as a size-aware sensitivity column (not the primary inferential metric — see §13.2 documented trade-off).

---

## 10. Co-primary analyses (hierarchical structure)

### 10.1 Hierarchical justification (§13.0)

The two co-primary analyses answer different LEVELS of the same attribution-question family — they are NOT two unrelated multiplicity-inflating tests:

```
LEVEL 1 — 4-bin LOO (broad)
    Question: Which broad feature category contributes most?
    Tests:    4 ΔMAE tests, one per bin
    Holm:     within-family α=0.05 (smallest p < 0.0125)

LEVEL 2 — Battery LOO (mechanistic), nested inside Level 1's pre-registered bins
    Question: Within each pre-registered bin, which construct batteries
              drive the predictive signal?
    Tests:    34 ΔMAE tests, partitioned per bin (D=7 / B=10 / P=2 / A=15)
    Holm:     nested-Holm primary correction per bin
              + joint-34 Holm sensitivity gate for cross-bin claims (§8.2)
```

Battery LOO is **not** a fishing expedition across 34 unrelated tests. **Batteries are nested inside pre-registered bins**, with multiplicity controlled within each bin. Co-primary status is justified because the paper has two linked questions — broad category attribution + within-category mechanism — and a single broad answer ("attitudinal dominates") is not an answer to "what mechanistically drives the attitudinal signal."

### 10.2 Co-primary headline #1 — 4-bin LOO

**Question**: Which broad feature category contributes most to LLM persona prediction of attitude outcomes?

**Method**: Drop one bin at a time from the persona prompt; compute respondent-macro Likert ΔMAE on the 12 primary_eval items relative to FULL. Paired-bootstrap CI (B=1000, seed=42).

**Multiplicity**: Holm-Bonferroni at α=0.05 within the 4-bin family.

### 10.3 Co-primary headline #2 — Battery LOO (34 batteries × 4 bins)

**Question**: Within each pre-registered bin, which construct-level batteries drive the predictive signal?

**Method**: For each battery B, drop the entire battery from the persona prompt for ALL 12 primary_eval items (in addition to R1 per-item battery exclusion which already applies — these are independent operations). Compute respondent-macro Likert ΔMAE relative to FULL. Paired-bootstrap CI + nested Holm + joint-34 sensitivity (§8). Effect-size label per §9.

**Estimand caveat**: because R1 already excludes the predicted item's own battery for each primary_eval item, Battery LOO measures **cross-construct predictive contribution after direct same-construct leakage is already blocked** — i.e., how much removing battery B *additionally* harms prediction relative to the FULL condition (which already has the predicted item's own battery R1-excluded). This is **NOT** the raw self-predictive value of a construct, **NOT** causal feature importance, and IS sensitive to battery size, item coverage (GSS ballot rotation), and prompt-design choices.

### 10.4 Bin-level Shapley decomposition (secondary — robustness on 4-bin LOO)

**Method**: Enumerate all 2⁴ = 16 conditions (include/exclude each of the 4 bins). Compute respondent-macro Likert MAE under each. Compute Shapley value per bin via standard combinatorial weighting. Compute ANOVA-contrast decomposition for 2-way / 3-way / 4-way interaction terms. `interaction_variance_share = Σ_{|T|≥2} α_T² / Σ_{|T|≥1} α_T²` (a clearly-named non-standard metric; **explicitly NOT the Friedman & Popescu 2008 H-statistic**).

**Reporting role**: robustness re-aggregation of the same primary 4-bin estimand. Shares 4-bin family multiplicity. Reported alongside 4-bin LOO ΔMAE; flags interaction effects if Shapley rank disagrees with LOO rank.

---

## 11. Theory interpretation (Discussion section only)

The 4-bin taxonomy is atheoretical — a sorting convention, not derived from cognitive theory. After the primary results are in, the paper's Discussion section situates the empirical pattern in relation to existing cognitive and sociological frameworks (see `theory_interpretation_guide.md` in repo).

**Critical pre-registration commitment** (no theory-driven primary or confirmatory analysis):
- The headline in the abstract is stated in atheoretical engineering terms (e.g., "attitudinal features dominate, with within-bin contribution concentrated in [batteries]").
- Theory framing enters one Discussion subsection labeled clearly as interpretive secondary analysis.
- We do NOT preregister a horse race that would let one theory "win."
- We do NOT make the abstract claim "LLM persona representation aligns with [Theory X]."
- **Null or mixed theoretical alignment will be reported with equal prominence to a positive-alignment finding** — if no framework cleanly explains the empirical pattern, the Discussion says so without distortion.

**Candidate frameworks listed in `theory_interpretation_guide.md`** (locked before Phase 1a fires; prevents post-hoc framework cherry-picking):
1. Moral Foundations Theory (Haidt; 5-6 foundations)
2. Schwartz Theory of Basic Values (10 values / 4 quadrants)
3. Bourdieu's Forms of Capital (3 capitals)
4. Cultural Theory of Risk (Douglas-Wildavsky; 4 worldviews)
5. Inglehart-Welzel Cultural Map (2 axes)
6. Big Five (HEXACO; 5-6 traits)

For each framework, the Discussion notes qualitatively which aspects of the empirical pattern do or do not align. No hard numeric thresholds, no Spearman correlation gates, no Stage 3 refinement experiments.

**Deferred to future work** (NOT in this preregistration; see `gss_phase1_design.md` §13.4): theory-bin LOO as confirmatory family, Representational Similarity Analysis (RSA), permutation importance theory adjudication, Stage 3 refinement experiments, six-theory horse race with hard numeric thresholds, sampled Shapley on 34 batteries, variable-level LOO, singleton-level LOO testing, Friedman & Popescu (2008) H-statistic proper implementation.

---

## 12. Writeup language template (§11.1, mandatory)

The following sentence-level constraints govern any Phase 1 abstract / headline figure / dashboard / paper text. **Forbidden language results in pre-registration deviation.**

| Constraint | Required form | Forbidden form |
|---|---|---|
| "Persona fidelity" qualifier | "within-wave attitudinal prediction" | bare "persona fidelity" |
| Cross-model robustness scope | "across four China-trained instruction-tuned models in a 100-respondent comparison" | bare "across LLM families" |
| Headline-N model identity | "the {selected_model} reported under the §12.2 quality-primary rule, N=1500" | "the cheap panel" / "the LLM panel" |
| Park comparison anchor | "the GPT-4o anchor on the N=100 subset, with single-item hold-out matching Park v2 SI §6" | "matches Park's 82%" |
| Auto-correlation framing | "after R1 battery-level exclusion and R2 regression-baseline partition" | bare "after leakage hygiene" |
| Test-retest claim | (none — say nothing about test-retest) | "normalized accuracy" / "fidelity" |
| LLM internal-state claim | "LLM output covaries with X" / "LLM behavior aligns with [direction]" | "LLM understands X" / "LLM internalized X" / "LLM uses the schema" |

---

## 13. Implementation status (§9e disclosure)

The locked analysis code passes synthetic-fixture self-tests prior to OSF lock. This is conventional OSF practice for analysis-plan preregistration.

### 13.1 Implemented + self-tested at OSF lock time

| Module | Self-test |
|---|---|
| `gss_loader.py` | reads 3-batch GSS extract → 3,309 × 973 DataFrame; 22/22 key Park variables verified |
| `validate_taxonomy.py` | 10 checks (incl. 7c battery map well-formedness): all pass |
| `gss_pipeline.py` | AUDIT A through E + B-regression: all pass |
| `gss_driver.py` | base orchestrator (5-condition LOO + sensitivity, atomic-write resume, R1 battery exclusion, item-level sensitivity resume, I-10 reproducibility guard) |
| `select_phase1b_model.py` | 5-branch self-test (argmin_mae / tie_break_cost / fallback_qwen_dq / fallback_qwen_tie / fallback_qwen_no_data): all pass |
| `regression_baseline.py` | 12/12 items scored on N=200 self-test; warning-free |
| `shapley_decomposition.py` | 8-assertion synthetic-fixture self-test: Shapley values exactly recover constructed contributions; IVS = 0 on additive data; LOO rank = Shapley rank |
| `battery_loo.py` | 8-assertion synthetic-fixture self-test: nested Holm + joint-N + effect-size labels + substantively-meaningful gate all behave correctly |

### 13.2 NOT yet implemented at OSF lock time (driver runtime extension)

The 16-condition Shapley enumeration mode and 34-battery exclusion mode in `gss_driver.py` are **not yet implemented** — these are the runtime modes that actually GENERATE the LLM-call data the analyzers consume. Specs are precise (`tier1_tool_schemas.md` Tools 1-2). Implementation will pass synthetic-fixture self-tests on the corresponding driver-output records BEFORE any paid Phase 1c run.

### 13.3 Pre-registration commitment

These analyses were locked at the analysis-plan level prior to implementation; the implementations will pass self-tests on synthetic fixtures (matching Tools 1-2 schema output exactly) BEFORE any paid Phase 1c run.

---

## 14. Reproducibility

- All seeds locked at **42**: sampling, bootstrap (primary + paired LOO + Shapley + Battery LOO), §12.2 selector, regression baseline 5-fold split.
- `gss_driver.py` enforces `--force-non-canonical-seed` flag to overwrite a seed-42 artifact with a non-42 run; default refuses (per Codex audit I-10 fix).
- Output filenames encode model + seed: `outputs/gss_phase1_records_n{N}_{model_tag}_seed{seed}.json`.
- The locked artifacts in §0 (with SHA-256 hashes) are versioned; any change post-lock requires OSF amendment.

---

## 15. Self-imposed smoke-test discipline (§9f)

**Smoke = plumbing only, not data look.**

N=10 smoke test verifies (a) the OpenRouter API succeeded, (b) artifacts have the right shape (NDJSON fields populated, persona_code parsed within valid_codes, parse_failure rate not catastrophic), (c) the seed-42 reproducibility guard fires correctly, and (d) atomic-write resume works on interruption. **The maintainer (Joyce) commits to NOT opening the smoke-output JSON and reading the actual codes.** If smoke output informs a design tweak (a prompt change, a parsing rule, a model swap, a battery edit), that is a silent pre-registration violation requiring OSF amendment.

---

## 16. Decisions log (chronological, with evidence)

Per `PROJECT_SYNTHESIS.md` §4 — locked decisions, when, against what evidence:

| Decision | Date | Rationale source |
|---|---|---|
| Phase split (GSS-first → Cookiy in Phase 2) | 2026-05-02 | Bayati meeting; ROI ≈100× over Cookiy at Phase 1 sample size |
| Single-wave snapshot (not cross-wave) | 2026-05-05 | Cross-wave introduces direct item-repetition leakage; avoid mixing "persistence" with "model accuracy" |
| §12.2 cost-primary → quality-primary flip | 2026-05-06 | 4-cheap-panel cost spread is ~2× while MAE spread can be much larger; selecting on a different metric than the headline is internally inconsistent |
| DQ-3 absolute → per-item relative threshold | 2026-05-08 | Human variance spans 28× across primary_eval items (FEPOL=0.15 vs PARTYID=4.24); absolute 0.5 threshold is too lenient/strict at the extremes |
| R1 battery boundaries (15 attitudinal-only) | 2026-05-08 | Park v2 BFI rule analog; SPLIT principle from civil_liberties (3 by target group) |
| R3 NOT implemented | 2026-05-08 | Would conflate "battery info loss" with "bin capacity reduction"; LOO ranking uninterpretable |
| Theory framing → Discussion-only | 2026-05-09 | Codex lean-design audit: 6-theory horse race would push paper toward "tool-stack" territory |
| Battery map v0.1 → v0.2 (15 → 34 batteries) | 2026-05-09 evening | Battery LOO promoted to co-primary; symmetric coverage across all 4 bins required |
| Nested Holm + joint-34 sensitivity | 2026-05-09 night | Codex M3 audit: cross-bin claims need stricter correction; nested-only is too loose for bin-comparison language |
| Practical-effect-size thresholds locked | 2026-05-09 night | N=1,500 makes very small ΔMAE significant; Funder & Ozer 2019 anchor |
| Fixed-dataset inferential frame | 2026-05-09 night | Codex M1 audit: GSS is multi-stage probability sample; cluster-bootstrap + WTSSALL too expensive vs the cheaper "fixed dataset" framing standard for LLM-persona prediction |
| Panel tie-break bug fix (M5) | 2026-05-09 night | Codex M5 audit: prior `min(candidates)` rule biased binary items toward code 1 systematically |
| R1 asymmetric burden disclosed (M6) | 2026-05-09 night | Codex M6 audit: 4 of 12 primary_eval items have battery-mates inside primary_eval (FECHLD/FEPOL, CONFINAN/CONLEGIS) — needs explicit headline split |
| Shapley + Battery LOO analyzers implemented | 2026-05-09 night | Codex audit B1 concession: lock-first defense is fine, but implement-first gives stronger OSF position |

---

## 17. Open items pending Joyce + Bayati signoff before final OSF lock

The following items are flagged in the live design but require explicit Joyce + Bayati signoff before this v1 draft becomes the final lockable preregistration:

1. **Theory candidate list final**: confirm the 6-framework list in `theory_interpretation_guide.md` (MFT / Schwartz / Bourdieu / Cultural Theory / Inglehart-Welzel / Big Five) is the locked set, NOT subject to addition or removal post-OSF-lock without amendment.
   - **Default if no objection**: 6-framework list as listed in §11 above is locked.

2. **Null-alignment reporting commitment**: explicit affirmation that null or mixed theoretical alignment will be published with equal prominence to a positive-alignment result. This is the **central anti-HARKing commitment** in the slim design.
   - **Suggested locked text** (Bayati to approve): *"If no candidate framework cleanly explains the empirical pattern (defined as: no framework's qualitative predictions are met by ≥3 of the 4-bin or ≥10 of the 34-battery results), the Discussion section reports this as a primary finding with the headline 'Tested cognitive frameworks do not predict the LLM persona's input-feature usage.' This null result is reported with equal prominence as a positive-alignment finding would be."*

3. **Discussion section structure**: data-organized (one subsection per primary finding, with theory frames as scaffolding within) vs theory-organized (one subsection per framework).
   - **Suggested locked structure**: data-organized.

4. **Inglehart-Welzel citation verification**: per `theory_review_round2.md` §2.2 own caveat, some Inglehart-Welzel claims are recall-based; verify primary sources before any framework appears in Discussion.
   - **Suggested**: Joyce to verify before final lock; if not verified, drop Inglehart-Welzel from the candidate list.

5. **Driver runtime extension timing**: when do `shapley_decomposition.py` and `battery_loo.py` driver runtime extensions get implemented?
   - **Default**: Phase 1a-time work for Shapley (Phase 1a output drives Shapley); Phase 1c-time work for Battery LOO (Phase 1b output drives Battery LOO).
   - Joyce-call: deviate from default if needed.

6. **Bayati final signoff**: faculty advisor approval on the OSF v1 draft as a whole.

---

## 18. What this preregistration does NOT cover (out of scope)

- Phase 2 (BFI-44 + behavioral games + 2-week recontact via Cookiy/Prolific) — separate preregistration when ready.
- Theory-bin LOO as a confirmatory family — would require a separate amendment after Joyce's literature-review lock and `gss_theory_taxonomy.json` build.
- Cross-cultural extension (Inglehart-Welzel-style cohort analysis on non-US data).
- Multimodal personas (image / voice).
- Long-term persona behavior over many turns.
- Open-ended response prediction (not a Likert / binary / categorical task).

---

## 19. Reviewer-facing summary (for OSF abstract field)

> **Title**: Hierarchical Feature Attribution for LLM Persona Prediction of GSS 2024 Attitude Outcomes: A Pre-Registered Analysis Plan
>
> **Abstract**: This preregistration covers Phase 1 of a multi-phase research program on feature attribution for LLM persona synthesis. Phase 1 estimates which of four pre-registered survey-collectible feature categories (demographic / behavioral / psychological / attitudinal) most contribute to LLM persona prediction of held-out GSS 2024 attitude outcomes (N=1,500 from the GSS 2024 cross-section), and within each pre-registered bin, which construct-level batteries (34 across all 4 bins) drive the predictive signal. The design has two co-primary analyses at hierarchical levels: a 4-bin leave-one-out ablation (broad feature-category attribution) and a 34-battery LOO with nested Holm-Bonferroni primary correction + joint-34 Holm sensitivity gate (mechanistic cluster-level attribution). Bin-level Shapley decomposition serves as 4-bin LOO robustness. Leakage hygiene is provided by R1 battery-level structural exclusion (mirroring Park v2's BFI whole-trait-block hold-out applied to GSS) and R2 regression-baseline comparator (a non-LLM Ridge/Logistic baseline on the same R1-respecting input pool). LLM panel: Phase 1a runs all 4 cheap OpenRouter models on N=100 + GPT-4o anchor for cross-model robustness and §12.2 quality-primary model selection; Phase 1b runs the single §12.2-selected model on N=1,500. Practical-effect-size thresholds (small <0.02 / modest 0.02-0.05 / substantive ≥0.05) gate substantive interpretation alongside Holm significance. Theory interpretation is Discussion-section only; null or mixed theoretical alignment is reported with equal prominence to positive alignment. Full design canonical source: `gss_phase1_design.md` (commit `b5a9779`).

---

## 20. Submission checklist

Per `gss_phase1_design.md` §9e (22-item OSF lock checklist), all items addressed in this v1 draft:

- [x] §1 Data: GSS 2024 cross-section, 3-batch path documented
- [x] §3 Sampling: N=1,500, seed=42, no stratification
- [x] §3 Eval items: 12 primary_eval + 118 sensitivity_eval (taxonomy v0.3 SHA-256 in §0)
- [x] §3 Feature taxonomy v0.3 (140 features × 4 bins)
- [x] §4 Battery map v0.2 (34 batteries + 17 singletons; SHA-256 in §0)
- [x] §5 Layer 3 R1 battery exclusion
- [x] §5 Layer 4 R2 regression baseline (with rhetorical-decomposition caveat)
- [x] §7 Primary metrics: Likert MAE, % within ±1, categorical exact-match
- [x] §7 Aggregation: respondent-macro primary, item-macro secondary, paired-bootstrap LOO Δ
- [x] §7 Bootstrap: B=1000, respondent-level paired, seed=42
- [x] §8 4-bin LOO Holm (n=4)
- [x] §8 Battery LOO nested Holm (per-bin) + joint-34 sensitivity
- [x] §9 Practical-effect-size thresholds (Funder & Ozer 2019 anchored)
- [x] §6 Phase 1a model panel (locked in `llm_router.py::MODEL_PANEL_PRIMARY`)
- [x] §6 §12.2 quality-primary selection rule
- [x] §6 DQ-3 reference (`outputs/primary_eval_human_variance_2024.json`; SHA-256 in §0)
- [x] §6 GPT-4o anchor scope (N=100 subset, NOT N=1,500 headline)
- [x] §11 Theory interpretation Discussion-only commitment
- [x] §13 Implementation status disclosure
- [x] §12 Writeup language template
- [x] §16 Decisions log appendix
- [x] §0 OSF copy-source rule (this doc copied ONLY from live-design sources per `gss_phase1_design.md` §9e final paragraph)

---

**End of OSF preregistration v1 draft.**

Pending: Joyce + Bayati signoff on §17 open items, then this document becomes the final lockable preregistration. After lock, `b5a9779` (or successor commit if any pre-lock fixes are filed) is the commit-hash-frozen reference; SHA-256 hashes in §0 are the artifact-frozen references. Any post-lock change to a hashed artifact requires OSF amendment.

**OSF v1 draft prepared by**: Joyce Yu + collaborating Claude session (2026-05-09 night).
