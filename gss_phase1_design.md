# Phase 1 — GSS Public-Data Feature-Importance Analysis

**Author:** Joyce Yu
**Course:** GSBGEN390 / thesis prep · Prof. Mohsen Bayati
**Status:** Proposed (drafted 2026-04-30, awaiting Bayati sign-off)
**Sequel to:** the Cookiy pilot in `MEETING_HANDOUT.md` and `progress_report.md`

---

## 1. Research question

*Within the GSS-attitudes outcome dimension* — the row of Park's outcome matrix where **surveys-only ≈ interview-only** (0.82 vs 0.83) — **which of four survey-collectible feature categories (demographic / behavioral / psychological / attitudinal) most contribute to LLM-persona predictive fidelity?**

This is the **GSS-row cell** of the two-way (feature category × outcome dimension) thesis matrix. It is the cheapest cell to attack first because GSS public data is free, panel-structured, and N is in the thousands.

## 2. Why GSS first (the ROI argument)

| Dimension | Cookiy collection (Pilot) | GSS public data (Phase 1) |
|---|---|---|
| N | 3 (pilot) → 30+ (thesis) | 1,500+ (panel) or 70,000+ (cumulative) |
| Cost per respondent | ~$10 platform + ~$1 LLM | $0 platform + ~$0.10 LLM |
| Time to data-in-hand | days to weeks | minutes (already collected) |
| In-session priming | yes (open methodological liability) | none — survey is single instrument, no interviews |
| Test-retest baseline | not available | **available**: same respondent answers same items 2 / 4 years apart in panel waves |
| BFI-44 outcome dimension | possible to add | not available — GSS has no BFI |
| Behavioral-game outcome | possible to add | not available — GSS has no economic games |
| Interview-vs-survey comparison | possible | not possible — no interviews in GSS |

**The trade**: by going GSS-first we lose the BFI/games outcome rows and the interview comparator, but we gain (a) Park-comparable N, (b) a real test-retest denominator, (c) zero priming, (d) immediate publishability of a single-row analysis. **Phase 2 (small targeted Cookiy collection) restores BFI and games at much smaller N, where Park's gap is biggest and interview vs. survey actually matters.**

## 3. Data source

**Primary**: GSS Three-Wave Panel, 2010-2012-2014 (most recent fully-released panel, N≈2,000 in wave 1, ~1,500 surviving wave 3 after attrition). Same respondents answered ~70 items per wave with substantial item overlap → built-in within-person test-retest.

**Backup**: GSS 1972-2022 Cumulative Cross-Section Data File (N≈72,000) for items not covered by the panel. Used for sensitivity checks, not the primary analysis.

**Both freely available** at https://gss.norc.org/ (registration required, no fee).

## 4. Method (Park's framework, adapted)

For each respondent in the panel:

1. **Split features into four pre-registered categories** (mapping documented in `gss_feature_taxonomy.json`, to be created):
   - **Demographic** (~8 items): age, sex, race, region, education, income, marital status, employment status
   - **Behavioral** (~10 items): voting, religious attendance, frequency of prayer, news consumption, hours worked, household labor, etc.
   - **Psychological** (~6 items, limited in GSS): general happiness, life satisfaction, anomia subscale, locus-of-control proxies
   - **Attitudinal** (~30 items): political views (polviews), abortion (abany/abrape), racial attitudes (racdif), gender role attitudes (fepol/fechld), institutional trust (confinan/conlegis), etc.
2. **Construct persona prompt** from wave-1 items in the *included* feature categories (Condition C-equivalent: all four bins; LOO conditions: drop one bin at a time).
3. **Predict held-out wave-2 (or wave-3) responses** via LLM persona (GPT-4o, temp 0.7, N=2 samples per item, identical to pilot pipeline).
4. **Score**: Likert MAE, % within ±1, categorical exact-match — same metrics as pilot.
5. **Normalize against test-retest baseline**: for each item, the within-person wave-1↔wave-3 agreement rate is the denominator. Final headline = persona accuracy ÷ test-retest reliability — **directly comparable to Park's 0.82–0.83 normalized accuracy on GSS**.

**LOO ablation**: 5 conditions per respondent — full (all 4 bins) + 4 LOO (drop demographic / drop behavioral / drop psychological / drop attitudinal). With N≈1,500, every category-importance estimate gets a real confidence interval.

## 5. Sample size, budget, timeline

| Phase | N | LLM calls | API budget | Wall-clock |
|---|---|---|---|---|
| 1a — sanity check | 100 | ~5,000 | $20-30 | 1 week (code adaptation + run + sanity-read) |
| 1b — full primary | 1,500 | ~75,000 | $300-500 | 3-4 weeks (full LOO + analysis + writeup) |

Most of the pilot pipeline transfers directly: persona-prompt builder, LLM dispatcher, scorer. The new code is (a) a GSS-loader / wave-merger and (b) a feature-taxonomy mapper from GSS variable names to the four bins. Both straightforward.

## 6. What Phase 1 produces (and what it does not)

**Produces** (publishable on its own):
- Confidence-intervaled feature-importance ranking on the GSS-attitudes outcome
- Direct comparison to Park's 0.82-0.83 normalized accuracy at comparable N
- A pre-registered feature taxonomy → standardized vocabulary for the rest of the thesis
- A reusable codebase that runs against any panel survey dataset

**Does not produce** (Phase 2's job):
- Feature importance for BFI-44 personality outcomes (GSS doesn't measure BFI)
- Feature importance for behavioral-game outcomes (GSS doesn't measure these)
- Interview-vs-survey comparator (no interviews in GSS)

## 7. How Phase 1 informs Phase 2

Phase 1's results **direct Phase 2's design**. Concrete examples:

- If Phase 1 finds **demographic features explain ≤2% of GSS-attitude prediction variance** (consistent with SCOPE's finding), Phase 2 can de-prioritize demographics in its targeted Cookiy collection and budget-shift to richer behavioral/psychological items.
- If Phase 1 finds **attitudinal features dominate within-attitude prediction** (likely — auto-correlation), Phase 2 must measure cross-outcome transfer: do attitudinal features still help on BFI? On games? Or do those need behavioral features the way attitudes need attitudinal features?
- If Phase 1 finds **psychological features are weak** (probable, given GSS's thin psychological coverage), this is itself a methodological note: real psychology requires real psychology batteries, not GSS proxies — strengthens the case for BFI in Phase 2.

This sequence is **hypothesis-driven**, not exploratory: Phase 1 outputs become Phase 2 inputs.

## 8. Limitations & open questions

1. **GSS panel attrition is non-random** (richer/older respondents stay longer). Apply panel weights or report sensitivity bounds.
2. **GSS items repeat across waves but with some module rotation** — not every item is asked every wave. Need to filter to the within-respondent intersection.
3. **2-year retest is longer than Park's 2-week.** True attitudes do shift in 2 years; the test-retest denominator therefore *underestimates* perfect-agent ceiling. Conservative bias — our normalized accuracy will read as a lower bound.
4. **GSS-attitude outcome dimension only.** Be explicit in writeup: this is the surveys ≈ interview row of Park's matrix, not a full replacement for Phase 2.
5. **Pre-register on OSF before running** — feature taxonomy, exclusion rules, primary metric. Locks Joyce in against post-hoc flexibility.

## 9. Decision Joyce wants from Bayati

1. **Endorse the phase-split**: GSS-first then targeted Cookiy, vs. straight-to-Cookiy at higher N.
2. **Endorse the feature taxonomy** at this granularity (4 bins) for the GSS-row analysis, with the option to subdivide for Phase 2.
3. **Endorse pre-registration** before Phase 1b launches.

If yes on all three, Joyce's two-week plan: complete the GSS loader + feature-taxonomy mapper, run Phase 1a (N=100) sanity check, present results in three weeks.

---

## Appendix: Mapping the four-category taxonomy onto GSS variables

This is a **first-cut mapping**, to be refined with Bayati and pre-registered. Variable names follow GSS codebook conventions.

**Demographic (~8 items):** `age`, `sex`, `race`, `region`, `educ`, `degree`, `income16`, `marital`, `wrkstat`

**Behavioral (~10 items):** `vote*` (turnout), `attend` (religious service frequency), `pray`, `news` (newspaper reading), `hrs1` (hours worked), `tvhours`, `socbar` (frequency at bar), `socommun` (talk to neighbors), `partyid` (as behavior signal: registered affiliation)

**Psychological (~6 items, GSS-thin):** `happy`, `satfin`, `health`, `life` (satisfaction), `anomia*` series (powerlessness scale), `fairness/helpful/trust` triad if framed as dispositional rather than attitudinal

**Attitudinal (~30 items):** `polviews`, `abany`/`abrape`/`abdefect`/etc. (abortion battery), `cappun`, `gunlaw`, `racdif*` series, `fepol`/`fechld` (gender attitudes), `confinan`/`conlegis`/`conmedic`/`conpress`/etc. (institutional confidence battery), `eqwlth`, `helppoor`, `tax`, etc.

The boundary between **psychological** and **attitudinal** in GSS is genuinely fuzzy — `happy` could go either way. Pre-registration must commit to a specific assignment and stick with it. The pilot already used a similar 4-bin scheme; consistency with the pilot's mapping is preferred unless a GSS-specific reason argues otherwise.
