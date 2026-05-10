# ⚠️ SUPERSEDED 2026-05-09 — see `theory_interpretation_guide.md`

This file is the v0.1 DRAFT of a **six-theory horse-race preregistration** that was slimmed
down per Codex's lean-design audit on 2026-05-09. The slim design replaces the horse race
with a lighter "interpretive secondary analysis" approach. This file is preserved unchanged
below for historical reference; the live design lives in `theory_interpretation_guide.md`
and `gss_phase1_design.md` §13.

**Why slimmed**: a confirmatory horse race with hard numeric thresholds per theory would push
the paper toward "tool-stack" territory and overshadow its clean primary contribution
(*which survey-collectible feature categories actually improve LLM persona prediction*).
The slim design preserves anti-HARKing through theory-list pre-commitment + null-reporting
commitment, without requiring the heavy preregistration machinery.

**Do NOT use this file as a live spec.** Use `theory_interpretation_guide.md` instead.

---

# OSF Pre-Registration — Appendix A (HISTORICAL — SUPERSEDED)
## Candidate Cognitive-Theory Predictions for the Phase 1 ML Findings

**Version**: v0.1 DRAFT — SUPERSEDED 2026-05-09
**Locked**: NEVER (slimmed before lock)
**Authors**: Joyce Yu (lead) + Prof. Mohsen Bayati (advisor) — collaborating Claude session prepared draft
**Companion files** (historical references; some no longer exist or have changed):
- `tier1_tool_schemas.md` — slimmed 2026-05-09 to Shapley + Battery LOO only
- `methodology_review.md` (was forthcoming, now deferred under lean-design lock)
- `gss_phase1_design.md` §14 (was forthcoming, now NOT created — lean design uses §13 instead)

**Status of this draft (2026-05-09)**:
- [draft-by-Claude] All theory predictions below were drafted from `theory_review.md` (Round 1) + `theory_review_round2.md` (Round 2). They are my best reading of the theoretical literature **as it currently exists in the project files**. Joyce / Bayati must validate every prediction against original sources before lock.
- [Joyce/Bayati to verify] markers flag places where I made a judgment call beyond what the theory_review files explicitly state.
- All threshold magnitudes (e.g., "Spearman ρ ≥ 0.4") are **my proposed values**; Joyce / Bayati must accept, modify, or replace them before lock.

---

## A.1 Why this Appendix exists (anti-HARKing role)

The staged confirmatory discovery design (gss_phase1_design.md §14) has three stages:

```
Stage 1 — DISCOVERY      (data-driven; atheoretical ML attribution)
Stage 2 — CONFRONTATION  (preregistered theoretical predictions tested against Stage 1 results)
Stage 3 — REFINEMENT     (targeted follow-up tests of best-aligned theory)
```

Without preregistration of Stage 2's theory predictions, the entire design degenerates into HARKing: "we ran ML, then noticed it looked like Theory X, so we say it's Theory X." Reviewers will reject this immediately.

**This Appendix is the anti-HARKing device.** It commits, *before any Phase 1a LLM call has been made*, to:

1. **Direction**: which bin / battery / cluster / variable each theory predicts will be most important
2. **Magnitude threshold**: the minimum quantitative pattern (in tool-schema fields from `tier1_tool_schemas.md`) that counts as "supports the theory"
3. **Refutation criteria**: what specific ML outputs would falsify the theory
4. **Tie-handling rule**: how multi-theory alignment is adjudicated
5. **Null-result branch**: how we report and publish if NO theory aligns

This file must be filed in OSF as a frozen artifact before `gss_driver.py --n 100` is run for Phase 1a.

---

## A.2 Candidate theories (six)

The six candidate frameworks below are pulled from `theory_review.md` (Round 1; MFT / Schwartz / Bourdieu / Cultural Theory of Risk) and `theory_review_round2.md` (Round 2; Inglehart-Welzel / Big Five). Other Round 2 candidates (Hofstede, Theory of Planned Behavior, Self-Determination, Dual-Process) are excluded from Stage 2 confrontation either because they are country-level (Hofstede), Phase-2-only (TPB, SDT), or framing-only (Dual-Process). [Joyce/Bayati: confirm exclusions or restore.]

For each theory, I draft a predicted ML pattern below. The format is constrained: predictions must be expressible in `tier1_tool_schemas.md` fields.

---

### Theory 1 — Moral Foundations Theory (MFT)

**Source citations** (per `theory_review.md` §2):
- Haidt & Graham 2007 *Soc. Justice Res.*
- Graham, Haidt & Nosek 2009 *JPSP*
- Atari et al. 2023 *JPSP* (cross-cultural validation)

**Theoretical claim relevant to Phase 1**: Political and religious attitudes derive from how strongly each person weights five (or six) innate moral foundations. Liberals weight Care/harm + Fairness more; conservatives weight all six approximately equally. The five-six foundations are: Care/harm, Fairness/cheating, Loyalty/betrayal, Authority/subversion, Sanctity/degradation, and (added 2012) Liberty/oppression.

**Predicted ML pattern**:

| Schema field | Predicted value | Rationale |
|---|---|---|
| `shapley_per_bin.attitudinal.rank` | **= 1** | MFT operates on attitudes, not capitals; attitudinal bin must dominate. |
| `shapley_per_bin.demographic.rank` | **≥ 3** | Demographics matter only insofar as they correlate with foundation weighting; no direct prediction. |
| `by_battery_total_importance` top-5 includes ≥3 of: `abortion`, `sexual_morality`, `religious_belief`, `civil_lib_*` (any of three target groups) | Yes | These map to Care/harm + Sanctity + Liberty/oppression — the foundations MFT claims drive moral attitudes most strongly. |
| `per_item_per_var.ABANY` top-5 features (excluding R1-excluded battery) includes RELPERSN OR ATTEND OR FUND | Yes | Religiosity is the canonical empirical correlate of MFT-Sanctity weighting and ABANY position (Haidt 2012, ch. 11). [Joyce/Bayati: verify if this is explicit prediction or my interpolation.] |
| `theory_aligned_correlations.MFT.spearman_rho_with_llm` | **≥ 0.40** | If LLM persona uses moral-foundation-aligned features, the MFT-derived similarity matrix should align with the LLM matrix. Threshold is my proposed value; standard for "moderate alignment" in RSA literature is 0.3-0.5. [Joyce/Bayati to verify threshold.] |

**Refutation criteria**:
- If `shapley_per_bin.attitudinal.rank ≠ 1` (some other bin dominates) → **refutes** MFT for the LLM persona setting.
- If top-5 batteries are all confidence-or-economic-or-political (not moral-or-sanctity) → **refutes**.
- If `theory_aligned_correlations.MFT.spearman_rho_with_llm < 0.20` → **refutes**.
- If predictions partially hold (1-2 of 4 schema-field criteria met) → "partial support."

**Identifiability vs other theories**:
- MFT vs Schwartz: both predict attitudinal-bin dominance; differ on which sub-cluster. MFT predicts moral / religious / civil-lib batteries; Schwartz (see below) puts more weight on universalism / economic_help.
- MFT vs Inglehart-Welzel: high overlap on sexual_morality and religious_belief batteries. Disambiguator: MFT does not predict AGE (demographic) to be strongly important; Inglehart-Welzel does (cohort effects). [Joyce/Bayati: verify this disambiguator is theoretically clean.]

---

### Theory 2 — Schwartz Theory of Basic Values

**Source citations** (per `theory_review.md` §3):
- Schwartz 1992 *Adv. Exp. Soc. Psychol.* 25:1-65
- Schwartz 2012 *Online Readings in Psychology and Culture* 2(1) [DOI 10.9707/2307-0919.1116]
- Cieciuch & Schwartz 2012 *J. Pers. Assess.* 94(3):321-328

**Theoretical claim relevant to Phase 1**: 10 universal human values organize on a circumplex (compatible vs conflicting), grouped into 4 higher-order quadrants: openness-to-change vs conservation; self-enhancement vs self-transcendence. Each value can be inferred from related attitudes when direct measures (PVQ instrument) are absent.

**Predicted ML pattern**:

| Schema field | Predicted value | Rationale |
|---|---|---|
| `shapley_per_bin.attitudinal.rank` | **= 1** | Schwartz values are measured / inferred via attitudes; attitudinal bin dominates. |
| `by_battery_total_importance` top-5 includes ≥2 of: `economic_help`, `racial_inequality_perception`, `religious_belief`, `sexual_morality` | Yes | Universalism (self-transcendence) maps to economic_help + racial_inequality; Tradition (conservation) maps to religious_belief + sexual_morality. |
| `by_battery_total_importance.economic_help.rank` | **≤ 4** | Universalism is one of Schwartz's most-cited values; HELP* and EQWLTH items are its standard GSS proxies. [Joyce/Bayati: verify top-4 threshold; this is my proposal.] |
| `theory_aligned_correlations.Schwartz.spearman_rho_with_llm` | **≥ 0.40** | Same threshold as MFT for "moderate alignment." |

**Refutation criteria**:
- If `shapley_per_bin.attitudinal.rank ≠ 1` → **refutes**.
- If `by_battery_total_importance.economic_help.rank ≥ 8` (i.e., bottom-half) → **refutes** the Universalism prediction.
- If `theory_aligned_correlations.Schwartz.spearman_rho_with_llm < 0.20` → **refutes**.
- 1 of 4 sub-criteria met → "partial support."

**Identifiability vs MFT**:
- MFT emphasizes religious / sanctity / liberty batteries; Schwartz emphasizes economic / racial-inequality batteries.
- Specifically: if `by_battery_total_importance.economic_help.rank ≤ 3` AND `religious_belief.rank ≤ 3` → both theories partially supported, see tie-handling §A.4.

---

### Theory 3 — Bourdieu's Forms of Capital

**Source citations** (per `theory_review.md` §4):
- Bourdieu 1986 "The Forms of Capital" in Richardson (ed.) *Handbook of Theory and Research for the Sociology of Education*
- Bourdieu 1984 *Distinction: A Social Critique of the Judgement of Taste*

**Theoretical claim relevant to Phase 1**: Three forms of capital structure social position: economic, cultural, social. Habitus (durable dispositions) is shaped by capital configuration; attitudes are downstream of habitus. **Bourdieu's framework predicts FEATURES (capitals) → DISPOSITIONS (habitus) → ATTITUDES.** Phase 1 tests the first link only.

**This is a critical theory to include in the horse race because Bourdieu predicts the *opposite* bin ranking from MFT/Schwartz.** If demographic + behavioral bins dominate, Bourdieu wins.

**Predicted ML pattern**:

| Schema field | Predicted value | Rationale |
|---|---|---|
| `shapley_per_bin.demographic.rank` | **≤ 2** | Economic capital lives in demographic (INCOME, INCOME16, DWELOWN16). |
| `shapley_per_bin.behavioral.rank` | **≤ 2** | Cultural + social capital live in behavioral (NEWS, ATTEND, RELITEN, etc.). |
| `shapley_per_bin.attitudinal.rank` | **≥ 3** | Attitudes are downstream of capital; Bourdieu does NOT predict attitudinal-bin dominance. |
| `per_item_per_var.ABANY` top-5 includes EDUC, DEGREE, MAEDUC, OR PAEDUC | Yes | Cultural-capital proxies should be primary predictors of moral attitude under Bourdieu. |
| `theory_aligned_correlations.Bourdieu.spearman_rho_with_llm` | **≥ 0.30** | Bourdieu predicts a coarser cluster structure than value theories; threshold relaxed to 0.30 (vs 0.40 for MFT/Schwartz). [Joyce/Bayati: verify rationale.] |

**Refutation criteria**:
- If `shapley_per_bin.attitudinal.rank = 1` AND attitudinal Shapley ≥ 2× demographic Shapley → **strongly refutes** Bourdieu (attitudes-not-capitals hypothesis).
- If `theory_aligned_correlations.Bourdieu.spearman_rho_with_llm < 0.15` → **refutes**.
- If 0-1 of 5 sub-criteria met → "refutes." 2 of 5 → "partial support."

**Why Bourdieu is in the horse race even if I expect it to lose**: If Bourdieu wins, that's a major finding — it would mean the LLM persona is using the persona's structural-position information rather than their stated attitudes to predict held-out attitudes. This would significantly change the paper's conclusions about what "persona reasoning" is.

---

### Theory 4 — Cultural Theory of Risk (Douglas-Wildavsky)

**Source citations** (per `theory_review.md` §5):
- Douglas & Wildavsky 1982 *Risk and Culture*
- Kahan 2011 *Temple Law Review* 83
- Tetlock 2003 *Trends in Cog. Sci.* 7(7):320-324

**Theoretical claim relevant to Phase 1**: Four cultural worldviews (Hierarchical, Egalitarian, Individualist, Fatalist) structure risk perception and political attitudes. Organized on two axes: group-vs-individualism × grid-of-prescription. **Strong fit specifically for political and risk-related attitudes; weaker for moral / religious attitudes.**

**Predicted ML pattern**:

| Schema field | Predicted value | Rationale |
|---|---|---|
| `shapley_per_bin.attitudinal.rank` | **= 1** | Operates on attitudes. |
| `by_battery_total_importance` top-5 includes ≥3 of: `racial_inequality_perception`, `economic_help`, `civil_lib_*`, `police_use_of_force` | Yes | These map to Egalitarian (racial_inequality, economic_help) + Individualist (civil_lib) + Hierarchical (police_use_of_force). |
| `by_battery_total_importance.abortion.rank` | **≥ 5** | Cultural Theory does NOT centrally predict abortion attitudes (those are MFT-Sanctity, not Cultural-Theory-risk). [Joyce/Bayati: verify; this is my interpolation from Kahan 2011's framing of risk-attitudes vs morality.] |
| `theory_aligned_correlations.Cultural_Theory.spearman_rho_with_llm` | **≥ 0.35** | Slightly relaxed vs MFT/Schwartz because Cultural Theory has 4 clusters (vs 5-6/10) — coarser similarity expected. |

**Refutation criteria**:
- If `by_battery_total_importance.abortion.rank ≤ 2` AND `racial_inequality.rank ≥ 5` → **refutes** (theory predicts the opposite).
- If `theory_aligned_correlations.Cultural_Theory.spearman_rho_with_llm < 0.20` → **refutes**.
- 1 of 4 sub-criteria met → "partial support."

**Identifiability vs MFT**: Direct disambiguator. MFT predicts abortion-battery in top-3; Cultural Theory predicts abortion-battery NOT in top-3.

---

### Theory 5 — Inglehart-Welzel Cultural Map

**Source citations** (per `theory_review_round2.md` §2.2 — Joyce: this section is recall-based per the doc's own caveat; verify before lock):
- Inglehart 1977 *The Silent Revolution* and 2018 *Cultural Evolution*
- Welzel 2013 *Freedom Rising*
- WVS-survey-derived cultural map (https://www.worldvaluessurvey.org)

**Theoretical claim relevant to Phase 1**: Cultural values arrange on two axes: traditional vs secular-rational, and survival vs self-expression. Generational cohorts move predictably along these axes as societies become more affluent. **Strong cohort/AGE prediction is the disambiguator from MFT.**

**Predicted ML pattern**:

| Schema field | Predicted value | Rationale |
|---|---|---|
| `shapley_per_bin.attitudinal.rank` | **= 1** | Cultural values are measured via attitudes. |
| `shapley_per_bin.demographic.rank` | **≤ 3** | AGE is centrally predictive (cohort effects). |
| `per_item_per_var.ABANY` top-5 includes AGE | Yes | Inglehart-Welzel's key empirical contribution is generational shift; AGE as predictor of moral attitudes is its hallmark. |
| `by_battery_total_importance` top-5 includes ≥3 of: `gender_role_attitudes`, `sexual_morality`, `civil_lib_*`, `religious_belief` | Yes | These are the canonical "self-expression vs survival" + "secular-rational vs traditional" battery loadings. |
| `theory_aligned_correlations.Inglehart_Welzel.spearman_rho_with_llm` | **≥ 0.35** | Two-axis cluster structure → moderate alignment expected. |

**Refutation criteria**:
- If `per_item_per_var.ABANY` rank of AGE ≥ 30 → **refutes** the cohort prediction.
- If `theory_aligned_correlations.Inglehart_Welzel.spearman_rho_with_llm < 0.20` → **refutes**.
- 1 of 5 sub-criteria met → "partial support."

**Identifiability vs MFT**:
- Both predict attitudinal-bin dominance and several overlapping batteries (sexual_morality, religious_belief, civil_lib).
- Disambiguator: AGE rank for ABANY. MFT does NOT centrally predict AGE; Inglehart-Welzel does. [Joyce/Bayati: verify this disambiguator is correct.]

---

### Theory 6 — Big Five (HEXACO)

**Source citations** (per `theory_review_round2.md` §2.1):
- Costa & McCrae 1992 *NEO-PI-R Manual*
- John & Srivastava 1999 *Handbook of Personality* — Big Five Inventory
- Ashton & Lee 2007 *Personality and Social Psychology Review* (HEXACO 6-trait extension)

**Theoretical claim relevant to Phase 1**: 5 (or 6, with HEXACO) personality traits — Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism (+ Honesty-Humility) — explain variance in behaviors and attitudes via trait → behavior linkage. **Critical caveat for Phase 1: GSS does not measure Big Five directly; the project uses GSS psychological + behavioral bins as crude proxies.**

**Predicted ML pattern**:

| Schema field | Predicted value | Rationale |
|---|---|---|
| `shapley_per_bin.psychological.rank` | **≤ 2** | Big Five proxies (HAPPY, HEALTH, FAIR, HELPFUL, TRUST) live in psychological bin. |
| `shapley_per_bin.behavioral.rank` | **≤ 2** | Behavior proxies of conscientiousness (ATTEND, PRAY) and openness (NEWS) matter. |
| `shapley_per_bin.attitudinal.rank` | **≥ 3** | Attitudes are downstream of trait → behavior; Big Five is NOT primarily an attitude theory. |
| `theory_aligned_correlations.Big_Five.spearman_rho_with_llm` | **≥ 0.25** | Threshold further relaxed because GSS proxies are weak; even if Big Five operates, the proxy → trait mapping introduces noise. [Joyce/Bayati: verify this is acceptable theoretical concession.] |

**Refutation criteria**:
- If `shapley_per_bin.attitudinal.rank = 1` AND attitudinal ≥ 2× psychological + behavioral → **refutes** (attitudes-not-traits).
- If `theory_aligned_correlations.Big_Five.spearman_rho_with_llm < 0.10` → **refutes**.
- 0-1 of 4 → "refutes." 2 of 4 → "partial support."

**Why Big Five is in the horse race**: It's the dominant theory in personality psychology and a standard reviewer-expectation prompt ("did you test Big Five?"). Including it commits us to a falsifiable position.

**Strong identifiability vs MFT/Schwartz/Cultural Theory**: All three of those predict attitudinal-bin dominance; Big Five (and Bourdieu) predict the opposite. This is the cleanest cleavage in the horse race.

---

## A.3 Agreement scoring (locked criteria)

For each theory, compute its **agreement score** as the fraction of pre-registered sub-criteria met (e.g., 4/4 = "supports", 2/4 = "partial", 0-1/4 = "refutes"). The exact thresholds are encoded per theory above.

**Specific scoring rules** (locked):

| Outcome | Sub-criteria met | Reporting language |
|---|---|---|
| **Supports** | ≥ ⌈¾ × n_subcriteria⌉ | "Phase 1 ML attribution is consistent with [Theory]'s predictions on [N of M] tested fields." |
| **Partial support** | between ⌈½⌉ and ⌈¾⌉ | "Phase 1 ML attribution partially aligns with [Theory] on [N of M] fields; specifically, [agreed] but [disagreed]." |
| **Refutes** | ≤ ⌊½ × n_subcriteria⌋ | "Phase 1 ML attribution does NOT align with [Theory]'s predictions; [N of M] sub-criteria failed." |

**Cross-theory dominance rule**:
- If exactly one theory in {MFT, Schwartz, Bourdieu, Cultural_Theory, Inglehart_Welzel, Big_Five} achieves "Supports" → that theory is the **best-aligned candidate** and proceeds to Stage 3.
- If two or more achieve "Supports" → see tie-handling §A.4.
- If zero achieve "Supports" → see null-result §A.5.

**Multiplicity correction** (Holm-Bonferroni-style, applied to RSA correlations only):
Because we test 6 RSA correlations against the LLM matrix, apply Holm-Bonferroni at α=0.05. A theory's `theory_aligned_correlations.{theory}.spearman_rho_with_llm` is treated as significant only after correction. Pre-registered: **for the threshold criteria above, only Holm-significant Spearman ρ values count.**

[Joyce/Bayati: confirm Holm vs alternative (e.g., FDR-BH) — Holm is more conservative.]

---

## A.4 Tie-handling rule (locked)

**Case 1 — Two theories both achieve "Supports"**:
- Compare on RSA correlation magnitude (Spearman ρ).
- The theory with the higher Holm-corrected ρ is named the **lead theory**; the other is named the **co-aligned theory** in the writeup.
- Stage 3 refinement is run for the lead theory only.
- **Both are reported in the abstract with the explicit "co-aligned" framing — never "the theory that won."**

**Case 2 — Two theories both achieve "Supports" AND have RSA ρ within 0.03**:
- Theories are reported as **"jointly supported."**
- Stage 3 designs an additional test that disambiguates them (e.g., counterfactual prompt manipulation that targets a sub-cluster predicted by ONE theory but not the other).
- This is reported as an open question, not resolved within Phase 1.

**Case 3 — Three or more theories achieve "Supports"**:
- Strong overlap detected. Report all and discuss in `Limitations` that Phase 1 cannot adjudicate among broadly compatible value-theory frameworks.
- Stage 3 still runs on the highest-ρ theory but with explicit caveat.

**Case 4 — Pairwise tie within "Partial support"**:
- Both reported as partial. No Stage 3 promotion.

**Pre-committed tie-break for cross-Stage-3 promotion**: If exactly one theory advances to Stage 3 under any of the rules above, that one runs. If multiple advance, the tie-break order is:
1. Higher Holm-corrected RSA ρ
2. Higher fraction of sub-criteria met (4/4 beats 3/4)
3. Theory predicted MORE specific patterns (rationale: more specific = more falsifiable, so a "supports" verdict is stronger evidence)
4. **Coin flip on the public OSF amendment** (last resort; would never expect to reach this)

[Joyce/Bayati: any one of these tie-handling rules can be substituted; please mark which you wish to alter.]

---

## A.5 Null-result branch (locked)

**Trigger**: If after Stage 1 + Stage 2 scoring, NO theory achieves "Supports" (i.e., all 6 are "Partial" or "Refutes").

**Reporting language** (locked):

> Phase 1 finds that the LLM persona's input-feature usage does NOT cleanly align with any of six pre-registered cognitive-theoretic frameworks (Moral Foundations Theory, Schwartz's Theory of Basic Values, Bourdieu's Forms of Capital, Cultural Theory of Risk, Inglehart-Welzel cultural map, Big Five). Specifically:
> - [theory list with sub-criteria scores]
> - The empirical pattern in Stage 1 may reflect (a) idiosyncratic computational properties of the LLM that do not map onto extant cognitive frameworks, (b) a hybrid pattern that combines features from multiple frameworks below the support threshold, or (c) a framework not represented in our Stage 2 candidate set.
>
> We treat this as a finding of equivalent importance to a positive-alignment result and report it as a primary contribution of the paper.

**Stage 3 under null result**: Stage 3 is replaced by **exploratory analysis only** (clearly labeled as such):
- Cross-theory feature overlap (which subset of features ALL theories disagree on)
- Hybrid hypothesis generation (not pre-registered; flagged as exploratory)
- Discussion of which (if any) framework class is closer to the LLM pattern in a degraded sense

**Critical commitment**: A null result is published with the SAME visibility as a positive result. The OSF lock binds us to this — the abstract cannot bury or downplay a null. [Joyce/Bayati: this is the most important pre-registration commitment in the document.]

---

## A.6 What Stage 3 does (refinement, not "internalization")

[Following Joyce's 2026-05-09 critique: Stage 3 language must be behaviorally constrained, NOT mentalistic.]

For the lead theory T (or co-aligned theories under §A.4 Case 2):

**Refinement test 1 — Theory-organized prompt**:
- Re-run a 100-respondent subset with the persona prompt's attitudinal section reorganized by T's clusters (e.g., MFT: care/harm items first, fairness items next, etc.).
- Measure: ΔMAE between theory-organized and atheoretical prompts.
- **Reporting language (locked)**: "Reorganizing the prompt by T's clusters changed prediction MAE by [Δ]; the direction is [consistent / inconsistent] with T's predicted positive contribution."
- **NOT permitted**: "T-organized prompts work better, suggesting LLM uses T internally."

**Refinement test 2 — Counterfactual prompt manipulation**:
- For each of T's predicted clusters, generate counterfactual personas where the cluster's values are inverted (e.g., a Care/harm-low persona is converted to Care/harm-high).
- Measure: how much the LLM's prediction shifts in the theory-predicted direction.
- **Reporting language (locked)**: "Counterfactual cluster perturbation changes LLM predictions in the direction predicted by T; the magnitude of shift is [Δ]."
- **NOT permitted**: "LLM internalizes T's clusters" / "LLM reasons via T's framework."

**Refinement test 3 — Theory-derived feature subset**:
- Re-run with ONLY T's predicted relevant features in the prompt.
- Measure: MAE drop relative to using a same-size random subset.
- Tests whether T's predicted feature subset is more informative than chance.

**Stage 3 budget**: ~$30-50 incremental on top of Phase 1 budget. Pre-allocated.

**Stage 3 outputs are never headline**: Even if all three refinement tests show theory-positive results, the abstract's primary claim remains the Stage 1 ML attribution + Stage 2 horse-race verdict. Stage 3 is a *follow-up confirmation*, not the main result.

---

## A.7 What this Appendix does NOT do

- Does NOT lock *which* theory will win — that's the data's job.
- Does NOT commit to running Stage 3 if all theories are refuted or are only partially supported.
- Does NOT promise a single "right answer" — null results, partial-support results, and joint-support results are all explicitly anticipated and reported.
- Does NOT govern theory-bin LOO design (now subsumed into the staged-discovery framework; this Appendix replaces the previous §13 "lock a theory + run theory-bin LOO" plan).
- Does NOT bind the actual *cluster-to-feature mapping* used by Stage 2 — that mapping is in `gss_theory_taxonomy.json` (TO BE BUILT after this Appendix locks).

---

## A.8 Open items requiring Joyce / Bayati input before lock

Marked throughout above with `[Joyce/Bayati to verify]` or `[Joyce/Bayati to fill]`. Consolidated list:

1. **Theory exclusions (§A.2)**: confirm Hofstede / TPB / SDT / Dual-Process are out of horse race.
2. **MFT prediction (§A.2 Theory 1)**: verify "RELPERSN OR ATTEND OR FUND in ABANY top-5" is explicit MFT prediction (not my interpolation).
3. **MFT identifiability (§A.2 Theory 1)**: verify AGE-importance claim distinguishes MFT from Inglehart-Welzel cleanly.
4. **Schwartz threshold (§A.2 Theory 2)**: verify `economic_help.rank ≤ 4` is appropriate; consider raising / lowering.
5. **Bourdieu threshold (§A.2 Theory 3)**: verify `Spearman ρ ≥ 0.30` rationale (relaxed vs MFT) is acceptable.
6. **Cultural Theory abortion claim (§A.2 Theory 4)**: verify `abortion.rank ≥ 5` is theoretical prediction.
7. **Inglehart-Welzel disambiguator (§A.2 Theory 5)**: verify AGE is the cleanest disambiguator from MFT.
8. **Big Five threshold (§A.2 Theory 6)**: verify `Spearman ρ ≥ 0.25` — most relaxed in the table — is acceptable theoretical concession.
9. **Multiplicity correction (§A.3)**: confirm Holm-Bonferroni vs FDR-BH for the 6-theory RSA testing.
10. **Tie-handling specifics (§A.4)**: review and customize.
11. **Null-result reporting commitment (§A.5)**: this is the most important commitment; please affirm explicitly that null results get equal-prominence reporting.
12. **Cluster-to-feature mapping** (`gss_theory_taxonomy.json`): forthcoming after this Appendix locks; will need separate lock-and-review cycle.

---

## A.9 Lock procedure

1. Joyce reviews this draft.
2. Bayati reviews (or Joyce represents Bayati's position).
3. Open items in §A.8 are resolved; this file is updated to v1.0.
4. The v1.0 file is uploaded to OSF as Appendix A of the Phase 1 pre-registration.
5. ONLY AFTER OSF lock can `gss_driver.py --n 100` be run for Phase 1a.

**No discovery tool may be run on real Phase 1a data before §A.9 step 4 completes.** This is the binding rule of staged confirmatory discovery.
