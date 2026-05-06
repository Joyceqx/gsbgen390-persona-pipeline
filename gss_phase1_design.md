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

| Sub-phase | N | LLM calls | API budget | Wall-clock |
|---|---|---|---|---|
| 1a — sanity check | 100 | ~6,000 | $20–30 | 1 week (pipeline build + run + sanity-read) |
| 1b — primary | 1,500 | ~90,000 | $300–500 | 3–4 weeks (full LOO + sensitivity pass + analysis + writeup) |

The N=1,500 sample is drawn from the 3,309 GSS 2024 respondents. Sampling rule (pre-registered): random sample without replacement, fixed seed = 42, no oversampling on demographics. Optional weighted reanalysis using GSS sampling weights as a robustness check (see §10).

## 6. What Phase 1 produces (and what it does not)

**Produces** (publishable on its own, Phase 1-only):
- **Confidence-intervaled feature-category contribution ranking** on GSS-attitudinal-item prediction (the 4-bin LOO ΔMAE per category, with bootstrap CIs at N=1,500)
- **Per-item raw accuracy table** on the ~118 Park-comparable sensitivity_eval items, side-by-side with the corresponding entries in Park v2 Table 3 (raw accuracy only — see §11 on what is NOT a valid comparison)
- **Persona self-consistency** as a stability QA metric
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
- **Persona self-consistency** (temp=0.7, multi-sample) is the only "consistency" measure reported in Phase 1; it is a property of the LLM, not of the human respondent.

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

**LOO-condition delta** — primary inferential quantity per category bin: `ΔMAE_bin = MAE(LOO-drop-bin) − MAE(Full)`. Bootstrap CIs at respondent level.

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

---

## Appendix: 4-bin variable taxonomy

Locked in `gss_feature_taxonomy.json` v0.2 (2026-05-05). Audit-fix removed `PARTYID` from the attitudinal feature bin (it is in `primary_eval`).

**Demographic (23 vars):** AGE, SEX, RACE, HISPANIC, REGION, EDUC, DEGREE, MARITAL, HOMPOP, BORN, INCOME16, PAEDUC, MAEDUC, PADEG, MADEG, REG16, MOBILE16, FAMILY16, FAMDIF16, INCOM16, DWELOWN16, MARTYPE, WIDOWED

**Behavioral (29 vars):** ATTEND, PRAY, WRKSTAT, HRS1, TVHOURS, NEWS, VOTE16, VOTE20, PRES16, PRES20, RELIG, RELIG16, FUND, RELITEN, ETHNIC, EVWORK, PARTFULL, UNEMP, UNION1, JOBLOSE, JOBFIND, OWNGUN, HUNT1, GRASS, COMPUSE, WEBMOB, XMOVIE, XMARSEX, HOMOSEX

**Psychological (8 vars):** HAPPY, HAPMAR, SATJOB, HEALTH, LIFE, FAIR, HELPFUL, TRUST

**Attitudinal (80 vars):** ABDEFECT, ABNOMORE, ABHLTH, ABPOOR, ABRAPE, ABSINGLE, SPANKING, DIVLAW, SEXEDUC, PILLOK, PORNLAW, FEHIRE, FEPRESCH, FEFAM, RACDIF2, RACDIF3, RACDIF4, WLTHWHTS, WLTHBLKS, WLTHHSPS, LETIN1A, CONARMY, CONBUS, CONCLERG, CONEDUC, CONFED, CONJUDGE, CONLABOR, CONMEDIC, CONPRESS, CONSCI, CONTV, POLHITOK, POLABUSE, POLATTAK, COURTS, SPKATH, COLATH, SPKRAC, COLRAC, LIBRAC, SPKCOM, COLCOM, LIBCOM, NATSPAC, NATENVIR, NATHEAL, NATCITY, NATDRUG, NATEDUC, NATRACE, NATARMS, NATAID, NATFARE, NATROAD, NATSOC, NATCHLD, NATSCI, NATENRGY, PRAYER, DISCAFF, DISCAFFW, DISCAFFM, TAX, HELPSICK, HELPNOT, HELPBLK, EQWLTH, GETAHEAD, PARSOL, KIDSSOL, LETDIE1, SUICIDE1, SUICIDE2, SUICIDE4, BIBLE, POSTLIFE, REBORN, SPRTPRSN, RELPERSN

The boundary between psychological and attitudinal in GSS is genuinely fuzzy — `HAPPY` could go either way. Pre-registration commits to this assignment and stick with it.
