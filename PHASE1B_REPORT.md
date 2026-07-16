# Accuracy and Feature Attribution for LLM Persona Simulation on GSS 2024
## Phase 1 Report

**Joyce Yu · Stanford GSB · GSBGEN390 · Advisor: Prof. Mohsen Bayati**
**Phase 1B run: July 12 to 14, 2026 · Report: July 15, 2026**

*All numbers reproduce from `src/phase1b_analysis.py` on the raw prediction
file (`phase1b_raw.parquet`, 159,804 rows; in the shared Drive folder). Full
tables: [`outputs/phase1b_tables.xlsx`](outputs/phase1b_tables.xlsx).*

---

## Abstract

Can a large language model, given a person's survey profile, predict that
person's other attitudes, and if so, which parts of the profile does it
actually use? We built LLM "personas" from 140 structured features of 3,309
real respondents in the 2024 General Social Survey and asked a panel of four
inexpensive open-weight models to answer 12 held-out attitude questions
(politics, abortion, gun control, gender roles, institutional confidence) as
each respondent. Prediction error was then re-measured under six ablation
conditions that remove categories of profile information. Three results.
First, accuracy is modest (normalized MAE 0.264) and statistically
indistinguishable from what GPT-4o achieves. Second, the personas are
remarkably insensitive to their inputs: deleting an entire feature category
(all demographics, or all behavioral variables) worsens error by at most
0.01, beneath our pre-registered threshold for a "small" effect, and what
signal exists is concentrated in a handful of politically diagnostic
variable groups (vote choice, race, abortion) rather than spread across
categories. Third, a ridge/logistic regression trained on the same features
matches or exceeds the LLM's accuracy on most items. The regression needs
labeled data from the same population and the LLM does not, so the two are
not substitutes; what the comparison shows is that on this task the LLM's
accuracy stays within what feature correlation alone supports. Applications
of "silicon sampling" that count on something beyond that should take note.

---

## 1. Introduction

**The promise.** Park et al. (2024) built generative agents from two-hour
qualitative interviews with 1,052 people and reported that these agents
could reproduce their subjects' General Social Survey answers about as
consistently as the subjects reproduced their own answers two weeks later.
This and similar results have fueled a fast-growing practice of "silicon
sampling": using LLM-simulated respondents to pilot surveys, pre-test
experiments, and even substitute for hard-to-reach populations.

**The gap.** If personas work, a basic engineering and scientific question
follows: *what information about a person does the simulation actually
need?* Two-hour interviews are expensive; structured survey variables are
cheap and already sit in every panel provider's database. Yet the
literature reports headline accuracies without attribution. Nobody has
systematically measured which categories of persona information drive the
predictions, or how the LLM's accuracy relates to the statistical structure
already present in the features. Both questions matter: the first tells
practitioners what data to collect; the second tells researchers what kind
of capability "persona simulation" is.

**This study.** We use the GSS 2024 cross-section as ground truth. Each
respondent's persona is a structured profile of up to 140 variables,
organized two ways. First, into **4 bins**: demographic, behavioral,
psychological, attitudinal. Second, into **34 batteries**: construct-level
variable groups we defined and locked before any paid run
(`gss_battery_map.json`; 7 demographic, 10 behavioral, 2 psychological, 15
attitudinal, plus 17 standalone variables outside any battery). A battery
groups variables that measure the same underlying construct closely enough
that an ablation must drop them together; the grouping is informed by, but
not identical to, the GSS questionnaire's own block structure. The persona
is handed to an LLM which answers 12 held-out attitude items as that
person. Throughout, a leakage rule (R1) excludes the predicted item's own
battery from the persona, mirroring Park et al.'s whole-module hold-out.
Attribution then comes from ablation: re-run the same predictions with a
bin or a battery deleted and measure how much accuracy degrades. A
supervised regression baseline, trained on the identical features under
the identical leakage rule, provides a reference for how much of the task
feature correlation alone can carry.

Phase 1A (June) selected the model and prompt configuration; Phase 1B
(this report) is the full-scale accuracy and attribution run.

## 2. Phase 1A recap: choosing the configuration

*(Details: `report/phase1a_report.md`. This section is a summary.)*

**Design.** A five-cell model panel: four inexpensive open-weight models
(Qwen3-Max, DeepSeek-V3.1-Terminus, Llama-4-Maverick, Kimi-K2) plus a
fifth policy, **Random**, which assigns each respondent one of the four at
random. Crossed with three prompt formats from the literature: P0
key-value list (Park 2024), P1 first-person narrative (Argyle 2023), P2
interview Q&A (Wang 2025). N = 200 respondents, full persona only, two
samples per call, with GPT-4o as an expensive reference. Scoring used
**normalized error**: absolute distance divided by the item's scale range,
so a one-step miss on a 7-point scale (small error) is not conflated with
missing a yes/no (full error). Parse failures score as the maximum error
of 1.0 (the "conservative" policy), so a model cannot dodge hard questions
by answering garbage.

**Results.**

| Model (over 3 prompts) | Normalized MAE | vs Random |
|---|---|---|
| Llama-4-Maverick | 0.261 | tied (p = 0.12) |
| DeepSeek-V3.1 | 0.272 | tied (p = 0.35) |
| Kimi-K2 | 0.273 | tied (p = 0.32) |
| Qwen3-Max | 0.280 | **worse** (p = 0.02) |
| **Random mix of the four** | **0.268** | reference |

| Prompt | Normalized MAE | vs P0 |
|---|---|---|
| P0 key-value | 0.276 | reference |
| P1 first-person | 0.269 | better, p < 0.01 |
| P2 interview | 0.268 | better, p < 0.01 |

Three facts drove the decision. (1) With respondent-clustered standard
errors, **no model beats the Random policy**; the only distinguishable
model (Qwen) is worse. (2) **GPT-4o is statistically indistinguishable
from the cheap panel** (p = 0.41), the result that licenses doing this
research at a fraction of frontier-model cost. (3) Several models exhibit
**mode collapse** on some items (the same answer for all 200 respondents),
which is invisible to the error metric but fatal for attribution, since a
collapsed answer cannot respond to a deleted feature.

**Decision (advisor email, July 12).** Run Phase 1B on the **Random × P1**
cell, your recommendation, on the grounds that no model earns a
performance claim over the mix and the mix dilutes any single model's
collapse behavior. The same email added a sixth experimental condition
(randomized battery ablation, described in §3) as a low-cost substitute
for the originally budgeted exhaustive battery LOO.

## 3. Phase 1B: design

**Sample and dispatch.** All 3,309 respondents of the GSS 2024
cross-section. Each respondent is assigned one panel model by a seeded
hash (shares: 24.7% to 25.4% per model) and keeps that model across **all
six conditions**, so every within-respondent comparison is model-constant.
Headline statistics use the **N = 3,109 cohort that excludes the 200
respondents Phase 1A used for selection** (removing in-sample optimism);
the full N = 3,309 is reported as a sensitivity check.

**Conditions.** Per respondent × on-ballot item (an average of 8.05 of the
12 items per respondent, following the GSS ballot design), one call per
condition:

| # | Condition | Persona contains |
|---|---|---|
| 1 | Full | all 140 features, minus the held-out item's own battery (R1) |
| 2 to 5 | Bin LOO × 4 | all 140 features, minus the held-out item's own battery (R1), minus one entire bin (demographic / behavioral / psychological / attitudinal) |
| 6 | Random battery drop | all 140 features, minus the held-out item's own battery (R1), minus one additional battery drawn uniformly at random per (respondent, item), draw recorded |

The R1 exclusion applies in every condition: the battery containing the
held-out item is never shown to the model. Every ΔMAE below is therefore
measured on top of that exclusion, on identical footing in both arms of
each comparison.

**Layer 1 (bins).** Each bin's contribution is the paired difference
ΔMAE = MAE(bin dropped) minus MAE(Full), computed within respondent.

**Layer 2 (batteries).** Condition 6 randomizes which battery is absent,
so each of the 34 batteries is missing in roughly 1/33 of ablation calls
(650 to 770 pairs per battery). Battery *b*'s contribution is the mean of
err(ablated) minus err(Full) over the pairs where *b* was drawn, requiring
a parsed answer in both arms. This estimates the same quantity as an
exhaustive 34-condition battery LOO at roughly 1/8 of the cost.

**Inference.** Normalized error as in Phase 1A; the conservative
parse-fail policy is primary, with the optimistic variant (drop unparsed
rows) reported alongside. CIs are BCa bootstrap, B = 10,000, resampling
respondents (clusters), seed 42. The four bin tests are Holm-Bonferroni
corrected. Following Funder and Ozer (2019) we pre-registered ΔMAE < 0.02
as below "small"; we substantively interpret a contribution only if its CI
excludes that threshold.

**Execution.** 159,804 calls over July 12 to 14 (about $87 at OpenRouter
prices). Final artifact: 19,854 records, exactly 3,309 respondents × 6
conditions, passing all integrity checks (no duplicates; model constant
within respondent and identical to the dispatch hash; recorded seeds
identical to their deterministic derivation; battery draws identical to
the seeded picker). Transient network interruptions corrupted 0.3% of
calls mid-run; affected records were deleted and regenerated through the
driver's resume path, which is equivalent to a single-pass run because
call seeds are pure functions of the call coordinates.

## 4. Results

### 4.1 Overall accuracy

Full-persona normalized MAE on the headline cohort is **0.264**
(conservative; 0.255 optimistic). The N = 3,309 sensitivity cohort gives
0.2646, a selector-optimism gap of about 0.001, confirming the Phase 1A
choice was not fit to noise. Per model (respondent-macro): Llama 0.242,
DeepSeek 0.261, Qwen 0.266, Kimi 0.287 (Kimi's figure includes its
parse-failure penalty, see §4.5).

Interpretation anchor: 0.264 means that on a 7-point item the average
prediction is about 1.8 scale points off. The model is clearly better
than guessing, but §4.4 puts the number in context.

### 4.2 Which feature categories matter (bin LOO)

| Bin dropped | ΔMAE | 95% BCa CI | Holm-p | n |
|---|---|---|---|---|
| Attitudinal | +0.0095 | [+0.0059, +0.0132] | 0.0004 | 3,109 |
| Behavioral | +0.0066 | [+0.0032, +0.0099] | 0.0004 | 3,109 |
| Demographic | +0.0045 | [+0.0012, +0.0078] | 0.014 | 3,109 |
| Psychological | +0.0008 | [−0.0022, +0.0037] | 0.61 | 3,109 |

Three of four bins have statistically reliable effects with a consistent
ordering (attitudinal > behavioral > demographic > psychological ≈ 0),
and the per-model breakdowns agree in direction. But **every CI lies
entirely below the 0.02 small-effect threshold**: removing a whole
category of information about a person, all their demographics or all
their behavioral traces, costs the persona at most one percentage point
of normalized accuracy. The profile is heavily redundant, and the model
reconstructs what a dropped bin carried from the features that remain.
The psychological bin (happiness, trust, life satisfaction) is not used
at all.

### 4.3 Which specific batteries matter (randomized ablation)

Top of the 34-battery ranking (combined column; full table in the xlsx):

| Battery | ΔMAE | 95% BCa CI | n pairs |
|---|---|---|---|
| voting_choice | +0.0174 | [+0.0032, +0.0323] | 715 |
| racial_ethnic_origin | +0.0161 | [+0.0015, +0.0317] | 766 |
| abortion | +0.0147 | [+0.0037, +0.0288] | 654 |
| denominational_identity | +0.0132 | [−0.0001, +0.0277] | 717 |
| current_religious_intensity | +0.0110 | [−0.0032, +0.0259] | 718 |
| *remaining 29 batteries* | CIs include 0 | | 650 to 770 each |

The picture sharpens: predictive signal is not spread across categories
but **concentrated in the few batteries that are politically diagnostic**:
whom the respondent voted for, their race, their abortion stance, and
(borderline) their religious affiliation. Deleting any of the other
roughly 30 batteries does nothing detectable. Note that the two layers
measure different estimands (a battery's effect is identified only on
items outside it, and battery cells have about 1/30 the data of bin
cells), so point estimates should not be compared across the two tables.
The qualitative conclusion is the same from both: most of the persona is
decoration.

Missingness check: of 25,029 ablation-Full pairs, 97.5% parse in both
arms, and one-sided failures are balanced (305 vs 299), so differential
parse failure does not drive the estimates.

### 4.4 How the LLM compares with a supervised baseline

For each item we trained a ridge (ordinal items) or logistic (binary
items) regression on the *same* encoded features under the *same* R1
battery-exclusion rule, 5-fold cross-validated within GSS 2024. The two
predictors have fundamentally different data requirements: the regression
learns from about 2,650 labeled respondents of this very survey, while
the LLM sees only one profile at a time and no labels. The comparison is
therefore not "which tool should you use"; it is a measurement of how
much of the task is carried by feature correlation that any supervised
learner can extract, versus knowledge the LLM brings on its own.

| Item | LLM (Full) | Regression | LLM gain | n |
|---|---|---|---|---|
| POLVIEWS | 0.197 | 0.144 | −0.054 | 2,970 |
| PARTYID | 0.170 | 0.147 | −0.023 | 3,071 |
| ABANY | 0.342 | 0.263 | −0.079 | 2,006 |
| CAPPUN | 0.375 | 0.344 | −0.032 | 1,944 |
| GUNLAW | 0.300 | 0.307 | +0.007 | 2,058 |
| FECHLD | 0.275 | 0.218 | −0.058 | 2,040 |
| FEPOL | 0.245 | 0.268 | +0.022 | 839 |
| RACDIF1 | 0.330 | 0.336 | +0.006 | 956 |
| CONFINAN | 0.244 | 0.238 | −0.006 | 2,032 |
| CONLEGIS | 0.287 | 0.228 | −0.059 | 2,020 |
| HELPPOOR | 0.264 | 0.217 | −0.047 | 2,001 |
| SATFIN | 0.257 | 0.233 | −0.023 | 3,092 |

The regression matches or exceeds the LLM on 9 of 12 items; the LLM's
three wins (+0.006 to +0.022) are small. Read together with §4.2 and
§4.3, the zero-shot persona appears to operate on the same correlational
signal the regression uses, and to extract somewhat less of it. What the
LLM uniquely offers is availability without training data. Whether that
zero-shot convenience is worth the accuracy gap, and whether the
correlational reading generalizes to settings where no labeled data
exists to check it, are questions this comparison raises rather than
settles.

### 4.5 Data quality

Parse failures are 1.24% of samples overall but concentrated in one
model: Kimi-K2 4.95%, Llama 0.08%, Qwen and DeepSeek 0.00%. Under the
conservative policy this penalizes Kimi's quarter of respondents; the
conservative-vs-optimistic headline gap is 0.0094, and no qualitative
conclusion changes between policies (both reported in every table). All
raw model outputs are preserved for inspection.

## 5. Limitations and caveats

- **Training-data contamination.** All four models postdate GSS 2024
  fieldwork, so memorized aggregates (or, less plausibly, memorized
  microdata) cannot be ruled out. The concern is directional:
  contamination would inflate LLM accuracy, so the finding that the LLM
  stays within the regression's reach (§4.4) survives it a fortiori,
  while the absolute level (0.264) should be read as an upper bound. A
  release-date audit and aggregate-recall probes are cheap follow-ups.
- **The regression baseline is in-distribution by construction.** It
  answers "how much is extractable from these features on this
  population," not "what would a zero-data predictor do." Section 4.4
  states the practical asymmetry; the limitation worth repeating is that
  in a genuinely data-free setting the LLM's accuracy could not be
  verified by this design at all.
- **Attribution granularity.** Battery cells have wide CIs (roughly
  ±0.015); batteries with true effects near 0.01 cannot be separated from
  zero at this budget. Whether that precision suffices, or whether the
  enumerated battery LOO (Phase 1C, about $481) is still worth running,
  is deferred to our next meeting.
- **One survey, one year, 12 items.** Attitude items with strong
  political structure; generalization to behaviors, preferences, or other
  populations is untested.

## 6. Reproducibility

Raw predictions: `phase1b_raw.parquet` (Drive folder *Phase 1B*; column
dictionary in [`report/phase1b_data_readme.md`](report/phase1b_data_readme.md)).
Analysis: [`src/phase1b_analysis.py`](src/phase1b_analysis.py) regenerates
every table ([`outputs/phase1b_tables.xlsx`](outputs/phase1b_tables.xlsx),
[`outputs/phase1b_analysis.json`](outputs/phase1b_analysis.json)); sheets
suffixed `_H` are the headline cohort, `_S` the sensitivity cohort. All
randomness is seeded (seed 42): respondent sampling, model dispatch,
battery draws, bootstrap. Design document: `RESEARCH_DESIGN.md` (§8 for
this phase). Total Phase 1 spend to date: about $250 of the roughly $769
budget.
