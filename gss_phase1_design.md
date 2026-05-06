# Phase 1 — GSS Public-Data Feature-Importance Analysis

**Author:** Joyce Yu
**Course:** GSBGEN390 / thesis prep · Prof. Mohsen Bayati
**Status:** Locked 2026-05-02; audit-fix revisions 2026-05-05 (this version frozen pending OSF pre-registration sign-off before Phase 1b launches)
**Sequel to:** the Cookiy pilot in `MEETING_HANDOUT.md` and `progress_report.md`

---

## 1. Research question

**Within the GSS-attitudes outcome dimension, which of four survey-collectible feature categories (demographic / behavioral / psychological / attitudinal) most contribute to LLM-persona prediction of held-out attitudinal items, in a single-wave snapshot setting?**

This is the **GSS-attitudes cell** of the (feature category × outcome dimension) thesis matrix. It is the cheapest cell to attack first because GSS public data is free and N is in the thousands. BFI-personality and behavioral-game outcome dimensions are deferred to Phase 2 (Cookiy collection).

### What this study estimates (estimand)

> Phase 1 estimates **single-wave GSS 2024 prediction** of held-out attitudinal items (the 12 items in `primary_eval`, plus per-item Park-comparable sensitivity over ~118 items) **from same-wave GSS feature variables**, decomposed into the contribution of four pre-registered feature categories.

Explicitly, this is **NOT**:
- Test-retest prediction (we have no recontact baseline in GSS)
- Longitudinal / cross-wave prediction (no panel structure used)
- Normalized persona fidelity (we do not divide by a test-retest denominator)
- A claim about general "human-simulation ability" (see §11 caveats)

It **is** a feature-category contribution analysis within GSS-attitudinal-item prediction at a single wave.

## 2. Why GSS public data first (the ROI argument)

| Dimension | Cookiy collection (Pilot) | GSS public data (Phase 1) |
|---|---|---|
| N | 3 (pilot) → 30+ (thesis) | **3,309** (GSS 2024 cross-section) |
| Cost per respondent | ~$10 platform + ~$1 LLM | $0 platform + ~$0.10–0.30 LLM |
| Time to data-in-hand | days to weeks | **already collected** (GSS 2024 fully released) |
| In-session priming | yes (open methodological liability) | **none** — survey is a single instrument, no interview |
| Test-retest baseline | not available | **also not available in single-wave snapshot** — deferred to Phase 2 |
| BFI-44 outcome dimension | possible to add | **not available** — GSS has no BFI |
| Behavioral-game outcome | possible to add | **not available** — GSS has no economic games |
| Interview-vs-survey comparison | possible | **not possible** — no interviews in GSS |

**The trade**: by going GSS-first we lose the BFI / games outcome rows, the interview-vs-survey comparator, and a test-retest denominator. We gain (a) Park-comparable item set, (b) N in the thousands at near-zero collection cost, (c) zero priming, (d) immediate publishability of a single-row analysis. **Phase 2 (small targeted Cookiy collection with 2-week recontact) restores BFI, games, AND a test-retest baseline at much smaller N**, where Park's gap is biggest.

## 3. Data source

**Primary**: **GSS 2024 cross-section**, 3,309 respondents, 973 unique variables (extracted via GSS Data Explorer in 3 batches; merged in `gss_loader.py`). Most recent fully-released GSS year as of 2026-05.

**Single-wave snapshot only.** No use of earlier GSS waves for prediction or normalization in Phase 1. Earlier waves are *not* loaded.

Freely available at https://gss.norc.org/ (registration required, no fee).

## 4. Method

For each of the 3,309 respondents:

1. **Apply the pre-registered feature taxonomy** (`gss_feature_taxonomy.json`):
   - Demographic features: 23 GSS variables (age, sex, race, region, education, income, marital, work status, parental background, etc.)
   - Behavioral features: 29 variables (voting, religious attendance, prayer, news, hours worked, gun ownership, media use, etc.)
   - Psychological features: 8 variables (general happiness, marital happiness, job satisfaction, health, life-evaluation, fair/helpful/trust dispositional triad)
   - Attitudinal features: 80 variables (the GSS attitude space minus the 12 primary_eval items — abortion battery, gender attitudes, racial attitudes, confidence battery, free-speech battery, national-priorities battery, etc.)
2. **For each respondent, drop GSS-missing-coded values** from the per-respondent feature set (codes in `MISSING_CODES`: -100..-40). No imputation.
3. **Construct the persona prompt** in 5 conditions:
   - **Full**: all 4 feature bins included
   - **LOO-drop-demographic**: 3 bins, demographic dropped
   - **LOO-drop-behavioral**: 3 bins, behavioral dropped
   - **LOO-drop-psychological**: 3 bins, psychological dropped
   - **LOO-drop-attitudinal**: 3 bins, attitudinal dropped
4. **Predict the 12 `primary_eval` items** under each condition, via GPT-4o at temperature 0.7, 2 samples per item (matches pilot pipeline; supports persona self-consistency reporting).
5. **Sensitivity pass (Path A, Park-comparable)**: separately, for each of the ~118 sensitivity_eval items X, build a persona prompt from the full-bin feature set MINUS X (per-item exclusion to prevent direct leakage), predict X under the full condition only (no LOO), score against the respondent's actual GSS 2024 answer.
6. **Score each (respondent, item) prediction**:
   - Likert items: absolute error vs. the GSS-coded numeric answer (after de-reversing where the GSS scale is reverse-coded)
   - Categorical items: exact match vs. the response label
7. **Aggregate** per the rules in §10 below.

**Primary metrics — raw, NOT normalized**:
- **Likert MAE** (mean absolute error on Likert items)
- **% within ±1** (fraction of Likert items where persona is within 1 scale point of truth)
- **Categorical exact-match accuracy**

**Persona self-consistency** (temp=0.7 multi-sample): reported as a supplementary stability check throughout. Measures whether the persona is internally stable across LLM samples; INDEPENDENT of any human-side test-retest question.

**Phase 1 does NOT compute test-retest-normalized accuracy.** Park's 0.82/0.83 are normalized against a 2-week recontact baseline that GSS does not provide. We report raw metrics only.

## 5. Sample size, budget, timeline

The N=1,500 sample is drawn from the 3,309 GSS 2024 respondents. Sampling rule (pre-registered): random sample without replacement, fixed seed = 42, no oversampling on demographics. Optional weighted reanalysis using GSS sampling weights as a robustness check (see §10).

**Multi-model panel as primary** (locked 2026-05-05; see §12 for full rationale): each respondent is queried under all conditions × items by 4 OpenRouter models in parallel. The headline result reports per-model raw accuracy AND a panel headline (median across 4 models). A small GPT-4o anchor on N=50 subset gives direct Park v2 Table 3 comparability.

| Sub-phase | N | LLM calls per respondent | Cost / respondent | Total budget |
|---|---|---|---|---|
| 1a — sanity check | 100 | ~712 (primary + sensitivity, 4 cheap models, n=1) | ~$0.24 | **~$25** |
| 1b — primary | 1,500 | ~712 | ~$0.24 | **~$360** |
| 1b GPT-4o anchor | 100 (subset of 1b) | 60 (primary only, 5 cond × 12 items × n=2) | ~$0.50 | **~$50** |
| **Total Phase 1** | | | | **~$440** |

Within the original $300-500 budget, with 4-model robustness as a bonus.

**Cost estimate caveats**: (a) per-token rates above are May-2026 OpenRouter approximations and must be verified at smoke-test time before scaling. (b) These estimates assume **no prompt caching** (the persona prompt repeats across the 12 items × 2 samples within a (respondent, condition); caching would discount input tokens by ~50%). Implementing prompt caching is deferred but could halve the 1b budget if needed.

Wall-clock: 1a in 1 week; 1b in 3-4 weeks (LLM run dominated by OpenRouter rate limits, not compute).

## 6. What Phase 1 produces (and what it does not)

**Produces** (publishable on its own, Phase 1-only):
- **Confidence-intervaled feature-category contribution ranking** on GSS-attitudinal-item prediction (the 4-bin LOO ΔMAE per category, with bootstrap CIs at N=1,500)
- **Per-item raw accuracy table** on the ~118 Park-comparable sensitivity_eval items, side-by-side with the corresponding entries in Park v2 Table 3 (raw accuracy only — see §11 on what is NOT a valid comparison)
- **Cross-model agreement %** as the primary stability QA metric for the cheap panel (4 models on the same item) — replaces within-model self-consistency for cost reasons. Within-model self-consistency (n_samples=2) is restored for the GPT-4o anchor subset only. See §12.
- A pre-registered feature taxonomy → standardized vocabulary for Phase 2 and for any later survey-instrument design
- A reusable codebase that runs against any single-wave GSS extract

**Does NOT produce** (Phase 2's job):
- Feature importance for BFI-44 personality outcomes (GSS doesn't measure BFI)
- Feature importance for behavioral-game outcomes (GSS doesn't measure these)
- Interview-vs-survey comparator (no interviews in GSS)
- **Park-style test-retest-normalized accuracy** — there is no within-respondent recontact in GSS 2024
- Any direct numerical claim that "our X% normalized accuracy matches Park's 82%" — Phase 1 reports RAW metrics; Park's headline is normalized; the units are different

## 7. How Phase 1 informs Phase 2

Phase 1 results direct Phase 2 design. Concrete examples:

- If Phase 1 finds **demographic features explain ≤2% of LOO ΔMAE** (consistent with prior literature on demographic-only persona conditions), Phase 2 can de-prioritize demographics in its targeted Cookiy collection and shift budget to richer behavioral/psychological items.
- If Phase 1 finds **attitudinal features dominate within-attitude prediction** (likely, partly because of constructive auto-correlation across the abortion / confidence / national-priorities batteries — see §11), Phase 2 must measure cross-outcome transfer: do attitudinal features still help on BFI? On behavioral games? Or do those outcomes need behavioral / psychological features the way attitudes need attitudinal features?
- If Phase 1 finds **psychological features are weak** (probable, given GSS's thin psychological coverage — only 8 features, mostly the fair/helpful/trust triad and the satisfaction items), this becomes a methodological note: real psychological measurement requires real psychological batteries, not GSS proxies. This strengthens the case for BFI-44 in Phase 2.

This sequence is **hypothesis-driven**, not exploratory. Phase 1 outputs become Phase 2 inputs.

## 8. Limitations & open questions (must be in writeup)

1. **Single-wave only — no test-retest baseline.** Cannot compute Park-style normalized accuracy. Reported metrics are raw.
2. **Constructive auto-correlation** (see §11). The attitudinal feature bin contains items that are domain-correlated with `primary_eval` items (e.g., `ABDEFECT`/`ABNOMORE` predict `ABANY`). Attitudinal-feature contribution is partly inflated by within-domain correlation, NOT by general "persona understanding". This is acknowledged, not corrected.
3. **GSS ballot rotation** creates uneven per-respondent item coverage. Aggregation rules in §10 below are the pre-registered handling.
4. **GSS-attitudinal outcome only.** Does NOT generalize to BFI-personality or behavioral-game prediction. Phase 2 covers those.
5. **Snapshot prediction.** Does NOT measure stability over time, longitudinal change, or causal direction.
6. **GSS sampling design** is a complex multi-stage probability sample with weights (`WTSSALL`, `WTSSPS_NEXT`, etc.). Primary analysis is unweighted; a weighted-reanalysis robustness check is in §10.
7. **Pre-registration on OSF before Phase 1b.** Locks taxonomy, eval set, primary metric, exclusion rules, secondary analyses. No post-hoc adjustment of the 4-bin assignments.

## 9. Decisions locked (post-Bayati 2026-05-02; audit-fix 2026-05-05)

1. ✅ **Phase split endorsed**: GSS-first → targeted Cookiy in Phase 2.
2. ✅ **4-bin feature taxonomy endorsed** for the GSS-row analysis.
3. ✅ **Pre-registration on OSF before Phase 1b** — eval set, feature taxonomy, primary metric, aggregation rule, exclusion rules, secondary analyses.

### 9a. Wave & timing structure — locked

- **Single-wave snapshot** (GSS 2024 cross-section, N=3,309). No panel data. No earlier-wave data. No test-retest computation.
- **Persona prediction window**: same-wave (T=2024) feature → same-wave (T=2024) held-out item.
- **Stability metric**: **cross-model agreement** across the 4-cheap-model panel (locked 2026-05-05; see §12). Within-model self-consistency only computed on the GPT-4o anchor subset (N=50).

### 9b. Eval-set composition — Path A* (locked)

- **Primary analysis (the headline)**: 12-item curated `primary_eval`. Supports the 4-bin LOO with full-population feature bins.
- **Sensitivity / Park-comparable analysis**: ~118-item `sensitivity_eval` (Park v2 GSS list minus 15 retired/renamed in 2024). Per-item exclusion when predicted. **Raw accuracy only** — no LOO, no normalization.
- One data download (`data/gss/390data1/`) covers both. Analysis-side split happens in code, audited via `gss_feature_taxonomy.json`.

### 9c. Leakage hygiene — three layers

1. **Layer 1 (direct, prevented)**: declared feature bins are disjoint from `primary_eval` (validator enforces); per-item exclusion in the sensitivity pass prevents direct leakage there too.
2. **Layer 2 (synonymous, not present in GSS-only design)**: Park's 27-item AVP-overlap removal does not apply to us (no AVP interview in Phase 1). Within-GSS, Park v2 SI argues no synonymous pairs.
3. **Layer 3 (constructive auto-correlation, acknowledged not prevented)**: items within a battery (abortion, confidence, gender) are highly correlated. Attitudinal-bin LOO drop will partly measure within-domain correlation, not just "construct understanding". This is documented in §11 and propagates to the writeup.

### 9d. Two-week plan

1. (✅ done) Lock design (this section)
2. (✅ done) Build feature-taxonomy JSON
3. (✅ done) Joyce: download GSS data
4. (✅ done) Build GSS loader
5. Build `gss_pipeline.py` (persona-prompt builder, LLM dispatcher, scorer for GSS rows)
6. End-to-end smoke test on N=10
7. Draft OSF pre-registration
8. Run Phase 1a (N=100) sanity check
9. Present 1a results to Bayati before launching 1b

## 10. Aggregation & weighting (pre-registered)

**Per-respondent metric** — for each (respondent r, condition c):
- For each Likert primary_eval item i that respondent r answered (i.e., not in MISSING_CODES): compute `|persona_response - true_response|` for both LLM samples; average within respondent across i.
- For each categorical primary_eval item: 1 if exact match, 0 otherwise; average across answered categorical items.

**Headline aggregation** — primary metric is **respondent-macro-averaged**:
- Primary Likert MAE = mean over respondents of (per-respondent average Likert error). Each respondent contributes equally regardless of how many items they answered, provided they answered ≥1 Likert primary_eval item.
- This treats each respondent as one observational unit, controlling for ballot-induced coverage variation.
- Standard errors via bootstrap (B=1000) at the respondent level.

**Secondary aggregation** — also reported for transparency:
- **Item-macro-averaged**: mean MAE per item, then average over items. Useful when items differ systematically in difficulty.
- **Respondent-item weighted (pooled)**: pool all (respondent, item) errors and average. Equivalent to weighting respondents by their answered-item count.

**Weighted reanalysis** — robustness check using GSS sampling weights (`WTSSALL` or equivalent in the 2024 release). Reported alongside unweighted primary if the two diverge by >0.05 MAE.

**LOO-condition delta** — primary inferential quantity per category bin: `ΔMAE_bin = MAE(LOO-drop-bin) − MAE(Full)`. Bootstrap CIs at respondent level via **paired bootstrap**: in each of the B=1000 resamples, draw one respondent set with replacement, then compute MAE(Full) and MAE(LOO-drop-bin) on **the same resample**, then take the delta. Do not bootstrap MAE(Full) and MAE(LOO) independently (would over-inflate Δ-CI variance).

## 11. What a positive Phase 1 result does and does NOT support (writeup constraints)

**Phase 1 evidence supports**:
- Within-GSS-attitude prediction in 2024, feature-category bin X has the largest contribution (or smallest, etc.).
- A specific, item-level raw-accuracy comparison to Park v2 Table 3 entries.
- Persona self-consistency at temperature 0.7 is high/low under various conditions.

**Phase 1 evidence does NOT support**:
- "The LLM persona simulates humans at X%" — we have no recontact baseline; X% is unnormalized.
- "Our normalized accuracy matches Park's 82%" — we do not compute normalized accuracy.
- "Attitudinal features dominate human-simulation fidelity" — they may dominate due to within-domain auto-correlation; the result is GSS-attitude-prediction-internal, not a fidelity claim.
- "Demographics don't matter for personas" — we measure demographics' contribution within GSS-attitude prediction, not their general informativeness for BFI personality or behavioral games.
- Generalization to BFI personality or behavioral games — Phase 2 only.

These constraints carry over into the abstract, headline figures, and reviewer-facing claims of the Phase 1 writeup.

## 12. Multi-model panel design (locked 2026-05-05)

### Rationale

GPT-4o-only Phase 1 would cost ~$900 at N=1500, exceeding the $300-500 budget. More importantly, single-model results conflate "feature-category contribution" with "GPT-4o-specific quirks" — a reviewer could plausibly reject "X is the most predictive feature category" with "but maybe only on GPT-4o."

**Solution**: query the same persona prompts on a **panel of 4 cheap, diverse OpenRouter-available models** as the primary analysis. The headline finding becomes "feature-category contribution to GSS-attitude prediction is robust **across LLM families**" — a stronger claim than single-model GPT-4o.

A small GPT-4o anchor on a 50-respondent subset preserves direct Park v2 Table 3 comparability without blowing budget.

### Locked model panel

| Role | Model | Provider | Input $/M (≈) | Output $/M (≈) | Why this model |
|---|---|---|---|---|---|
| Cheap-panel primary | **Qwen-2.5-72B-Instruct** | Alibaba | 0.40 | 0.40 | strong instruction-following; multilingual |
| Cheap-panel primary | **DeepSeek-V3.1** | DeepSeek | 0.20 | 0.80 | very cheap, strong reasoning |
| Cheap-panel primary | **MiniMax-M1** (Hailuo) | MiniMax | 0.20 | 1.00 | different RLHF philosophy from above |
| Cheap-panel primary | **Kimi K2** | Moonshot | 0.40 | 1.00 | long-context strong; 4th distinct family |
| Anchor | **GPT-4o** | OpenAI | 2.50 | 10.00 | Park v2 used this; direct Table 3 comparability |

**Panel diversity argument**: 4 different teams, 4 different RLHF philosophies. Convergence across all 4 = result generalizes beyond any single model's bias.

**Honest caveat about diversity scope**: All 4 cheap-panel models are trained by China-based organizations (Alibaba, DeepSeek, MiniMax, Moonshot). The diversity is real *across teams and RLHF philosophies* but is NOT a Western-vs-Eastern training-data robustness check. The GPT-4o anchor (N=100 subset) provides a single Western-trained reference; for stronger diversity claims at thesis-stage, swap one slot for Llama-3.3-70B (Meta) or Mistral-Large-2 in a sensitivity reanalysis.

### Sampling rules

- **Cheap models**: `n_samples = 1` per (respondent, item, condition). Cross-model agreement (% of items where all 4 models gave the same code) replaces within-model self-consistency as the primary stability metric.
- **GPT-4o anchor**: `n_samples = 2` per (respondent, item) on **N=100** subset, primary conditions only. Restores Park-style within-model self-consistency for the directly-comparable subset. Sensitivity pass NOT run on GPT-4o (cost reasons). N=100 (bumped from N=50 per Codex audit 2026-05-06) gives wider per-item CIs but still tight enough for per-item Park v2 Table 3 anchoring.

### Headline output extension to multi-model

The aggregation in §10 is computed:
- **Per model**: each cheap-panel model gets its own respondent-macro / item-macro / pooled headline + bootstrap CIs. Reported alongside in the writeup.
- **Panel median**: for each (respondent, condition, item, sample-position-equivalent), take the median (Likert) or mode (categorical) across the 4 models. Re-run aggregation on this synthetic "panel respondent." Reported as the primary headline; per-model deltas in supplementary.
- **GPT-4o anchor**: per-item raw accuracy table on N=50 subset, side-by-side with Park v2 Table 3.
- **Cross-model agreement**: % of (respondent, item, condition) tuples where all 4 cheap models output the same integer code. Reported as the new "consistency QA metric" replacing within-model self-consistency.

### What the writeup must say (extension to §11 constraints)

- "Our headline is the panel median of 4 models (Qwen, DeepSeek, MiniMax, Kimi). Per-model results are in the supplementary."
- "Direct comparability to Park v2 Table 3 is via the N=50 GPT-4o anchor subset, not via the cheap-model panel. The cheap-model panel addresses generalization across LLM families; the anchor addresses model-comparability with the established benchmark."
- "Cross-model agreement at temperature 0.7 (4 cheap models on the same item) is reported as a stability QA metric in lieu of within-model self-consistency. The two are different concepts."

### Pre-registration must declare

Before Phase 1b launches the OSF pre-reg locks:
- The exact 4-cheap-model list (prevents post-hoc cherry-picking)
- The N=50 anchor model (GPT-4o) and that it is run only on primary conditions
- The aggregation method (per-model + panel median + anchor side-by-side)
- The cross-model agreement metric definition

---

## Appendix: 4-bin variable taxonomy

Locked in `gss_feature_taxonomy.json` v0.3 (2026-05-05). Two prior audit-fixes:
- 2026-05-05 morning: removed `PARTYID` from attitudinal (it is in `primary_eval`).
- 2026-05-05 AUDIT-A: re-classified 4 variables to fix conceptual mis-categorizations surfaced when inspecting a sample persona prompt — `ETHNIC` (behavioral → demographic; ancestry/origin is descriptive not behavioral), `XMARSEX` / `HOMOSEX` / `GRASS` (behavioral → attitudinal; these GSS items ask opinions about extramarital sex / same-sex relations / marijuana legalization, NOT self-reported behaviors).

Net effect: 4 reclassifications between feature bins. No item moved into/out of `primary_eval` or `sensitivity_eval`. Total feature count unchanged at 140. Disjointness with `primary_eval` preserved.

**Demographic (24 vars):** AGE, SEX, RACE, HISPANIC, ETHNIC, REGION, EDUC, DEGREE, MARITAL, HOMPOP, BORN, INCOME16, PAEDUC, MAEDUC, PADEG, MADEG, REG16, MOBILE16, FAMILY16, FAMDIF16, INCOM16, DWELOWN16, MARTYPE, WIDOWED

**Behavioral (25 vars):** ATTEND, PRAY, WRKSTAT, HRS1, TVHOURS, NEWS, VOTE16, VOTE20, PRES16, PRES20, RELIG, RELIG16, FUND, RELITEN, EVWORK, PARTFULL, UNEMP, UNION1, JOBLOSE, JOBFIND, OWNGUN, HUNT1, COMPUSE, WEBMOB, XMOVIE

**Psychological (8 vars):** HAPPY, HAPMAR, SATJOB, HEALTH, LIFE, FAIR, HELPFUL, TRUST

**Attitudinal (83 vars):** ABDEFECT, ABNOMORE, ABHLTH, ABPOOR, ABRAPE, ABSINGLE, SPANKING, DIVLAW, SEXEDUC, PILLOK, PORNLAW, XMARSEX, HOMOSEX, GRASS, FEHIRE, FEPRESCH, FEFAM, RACDIF2, RACDIF3, RACDIF4, WLTHWHTS, WLTHBLKS, WLTHHSPS, LETIN1A, CONARMY, CONBUS, CONCLERG, CONEDUC, CONFED, CONJUDGE, CONLABOR, CONMEDIC, CONPRESS, CONSCI, CONTV, POLHITOK, POLABUSE, POLATTAK, COURTS, SPKATH, COLATH, SPKRAC, COLRAC, LIBRAC, SPKCOM, COLCOM, LIBCOM, NATSPAC, NATENVIR, NATHEAL, NATCITY, NATDRUG, NATEDUC, NATRACE, NATARMS, NATAID, NATFARE, NATROAD, NATSOC, NATCHLD, NATSCI, NATENRGY, PRAYER, DISCAFF, DISCAFFW, DISCAFFM, TAX, HELPSICK, HELPNOT, HELPBLK, EQWLTH, GETAHEAD, PARSOL, KIDSSOL, LETDIE1, SUICIDE1, SUICIDE2, SUICIDE4, BIBLE, POSTLIFE, REBORN, SPRTPRSN, RELPERSN

The boundary between psychological and attitudinal in GSS is genuinely fuzzy — `HAPPY` could go either way. Pre-registration commits to this assignment and sticks with it.
