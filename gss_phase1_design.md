# Phase 1 — GSS Public-Data Feature-Importance Analysis

**Author:** Joyce Yu
**Course:** GSBGEN390 / thesis prep · Prof. Mohsen Bayati
**Status:** Locked 2026-05-02; audit-fix revisions 2026-05-05 → 2026-05-06 (this version frozen pending OSF pre-registration sign-off **before Phase 1a launches** — pre-reg locks the model panel, the §12.2 selection rule, and dual-headline aggregation; Phase 1a's results then feed §12.2 to pick the Phase 1b model)
**Sequel to:** the Cookiy pilot in `MEETING_HANDOUT.md` and `progress_report.md`

---

## 1. Research question

**Phase 1 question** (the specific question this design doc covers):
> Within attitude prediction (single-wave snapshot setting), which of four survey-collectible feature categories (demographic / behavioral / psychological / attitudinal) most contributes to LLM-persona prediction of held-out attitudinal items?

**Project-level question** (the larger research direction this design feeds):
> In LLM persona synthesis, which input feature categories drive prediction quality, and how does that contribution vary across outcome dimensions?

Phase 1 is the **first piece** of this project-level program. It targets attitude prediction (the cheapest outcome dimension to attack first — GSS public data is free, N in the thousands). Phase 2 extends to personality (BFI-44) and behavioral economic games via targeted Cookiy collection. Future phases may extend to other outcome dimensions (long-term behavior, open-ended responses, multimodal personas, etc.).

### 1.0 Honest impact / scope framing (locked 2026-05-09 evening)

**What this paper is**:
> Phase 1 is a large-N feature-attribution study for LLM persona prediction of GSS attitude outcomes. It estimates which survey-collectible feature categories and construct batteries improve same-wave attitude prediction, under leakage-clean and pre-registered aggregation.

**The contribution**:
> The contribution is **not** that LLM personas "understand humans." The contribution is a **leakage-clean, preregistered attribution framework showing what kinds of survey information drive LLM persona prediction accuracy in a large public survey setting** — including (a) two-level hierarchical attribution (broad bin + mechanistic battery), (b) battery-level structural exclusion (R1) that mirrors Park v2's BFI rule applied to GSS, (c) regression-baseline comparator (R2) on the same input pool, and (d) a quality-primary multi-model selection rule with named fallback (§12.2).

**Honest impact assessment**:
- Phase 1 alone is a strong empirical/methodological paper if executed cleanly.
- It is **not** a full test of persona fidelity because it lacks test-retest normalization and non-attitude outcomes.
- The higher-impact thesis comes from **Phase 1 + Phase 2 together**: attitude / personality / behavioral-game outcome-stratified feature attribution.

**Anticipated reviewer objection — auto-correlation tautology (locked 2026-05-09 night per Audit-3 M-new-1 review)**:
> *"How is your finding 'attitudinal features dominate within-attitude prediction' meaningfully different from 'related items correlate'?"*

This is the strongest single-paper attack on the Phase 1 framing. Our defenses:
1. **R1 battery exclusion structurally blocks within-construct same-item leakage** — when predicting `ABANY`, the entire abortion battery (`ABDEFECT`, `ABNOMORE`, `ABRAPE`, etc.) is dropped. The bin-level "attitudinal" contribution is therefore **cross-construct attitudinal information**, not auto-correlation within the construct.
2. **R2 regression baseline quantifies the auto-correlation upper bound** any non-LLM predictor can extract from the same R1-excluded feature pool. "LLM gain over regression" measures incremental model-specific predictive value past supervised auto-correlation. (Caveat per §9c.4: this is a *rhetorical* decomposition with an asymmetric-N caveat per N3, not a literal causal partition.)
3. **The cross-outcome contrast in Phase 1 + Phase 2 is the structural answer**: if attitudinal features dominate attitudinal prediction but NOT BFI / behavioral-game prediction (Phase 2), the Phase 1 finding is a real outcome-stratified attribution and the tautology framing fails. **Phase 1 alone cannot fully defang this objection — Phase 2's outcome contrast is the load-bearing rebuttal.** Authors who choose to publish Phase 1 alone must reframe the contribution as a **methods paper** (the leakage hygiene framework + §12.2 selector + dual-headline split) rather than a feature-importance headline. Authors who publish Phase 1+2 together can foreground the attribution claim with the cross-outcome contrast as the defense.

The §1.0 / §11 / §11.1 framing is currently consistent with EITHER publication path. Joyce + Bayati must commit to a path before Phase 2 recruitment locks (see §17 OSF open item #6 for the strategic decision).

**Language we deliberately AVOID** in Phase 1 abstract / headline / dashboard / README:
- ❌ "normalized Park-style fidelity" (we report raw metrics; no test-retest denominator)
- ❌ "causal feature importance" (LOO + Battery LOO estimate predictive dependence under a fixed prompt-construction procedure, not causal effects)
- ❌ "general human simulation ability" (single-wave attitude prediction does not generalize to BFI / games / long-term behavior)
- ❌ "robust generalization across LLM families" beyond the N=200 Phase 1a comparison (after the 2026-05-09 MiniMax→Llama swap the cheap panel is 3 China-trained + 1 Western-trained; the GPT-4o anchor is a second Western reference on N=100 subset; cross-family generalization is bounded by panel composition)
- ❌ "LLM persona reasoning" without the §9c.4 R2-comparator caveat in scope

The exhaustive forbidden/required language template lives in §11.1.

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

For each respondent in the locked sample:

1. **Apply the pre-registered feature taxonomy** (`gss_feature_taxonomy.json` v0.3, 140 variables):
   - Demographic features: 24 GSS variables
   - Behavioral features: 25 variables
   - Psychological features: 8 variables
   - Attitudinal features: 83 variables (the GSS attitude space minus the 12 `primary_eval` items)

2. **For each respondent, drop missing-coded values** (codes in `MISSING_CODES = {-100, -99, …, -40}` AND positive codes whose label is a non-substantive marker like REFUSED / DK / IAP — see `_is_non_substantive_label`). No imputation.

3. **Construct 5 persona-prompt conditions** per respondent:
   - `full` — all 4 feature bins included
   - `loo_drop_demographic` / `loo_drop_behavioral` / `loo_drop_psychological` / `loo_drop_attitudinal` — drop one bin

4. **Run the LLM panel** on each (respondent, condition, item):
   - **Phase 1a (N=200)**: 4 cheap OpenRouter models from the locked panel (Qwen-2.5-72B / DeepSeek-V3.1 / Llama-3.3-70B-Instruct / Kimi K2), n_samples=1 each, temperature=0.7 → 4 codes per (respondent, condition, item). Panel composition revised 2026-05-09 night per Audit-3 cross-family balance review (MiniMax-M1 → Llama-3.3-70B-Instruct, Meta) to introduce one Western-trained model into the headline panel. Phase 1a N also expanded from 100 → 200 to support the §12.2 selector's 100/100 selection/validation split (see §12.2).
   - **Phase 1b (N=3309)**: ONE model selected via the §12.2 quality-primary rule (lowest 1a Likert MAE among DQ-passers, cost as tie-break), n_samples=1, temperature=0.7.
   - **Anchor (N=100 subset = the §12.2 selection split)**: GPT-4o, **primary + sensitivity**, n_samples=2, temperature=0.7. The anchor preserves Park-comparable per-item accuracy AND restores within-model self-consistency on the directly-comparable subset. Single anchor invocation serves both Phase 1a and Phase 1b reporting purposes (locked 2026-05-10 Joyce decision Option A).

5. **Sensitivity pass (Path A, Park-comparable; locked 2026-05-10 Joyce decision Option A)** — **only on the GPT-4o anchor (N=100)**: for each of the ~118 sensitivity-eval items X, build a persona prompt from the full feature set MINUS X (per-item exclusion to prevent direct leakage — mirrors Park v2 SI §6 single-item hold-out yielding 0.82), predict X, score. **Cheap panel models (Qwen / DeepSeek / Llama-3.3 / Kimi) do NOT run the sensitivity pass** — sensitivity_eval is purely the Park-comparable anchor table input, not used by the §12.2 selector or the headline LOO/Battery LOO analyses. (Earlier drafts ran sensitivity on cheap panel + anchor; reverted to OSF §3.2 literal wording 2026-05-10 per Audit-fresh-2 P1 sensitivity-scope review.)

6. **Score each (respondent, condition, model, item, sample)** via the rules locked in AUDIT-C (`gss_pipeline.py`):
   - Likert items (likert3-7): absolute error vs. truth code
   - Binary / categorical items: exact match
   - PARTYID contingent: Likert on 0-6, categorical when either side outputs 7

7. **Aggregate** per §10 (respondent-macro primary; bootstrap CIs at respondent level B=10000 with BCa via scipy + percentile fallback — locked 2026-05-09 night per Codex N5/N6; LOO ΔMAE via paired bootstrap). Multi-model panel synthesis per §12 (median for Likert, mode for categorical, with `_panel_aggregate_code`).

**Primary metrics — raw, NOT normalized**:
- **Likert MAE** (mean absolute error on Likert items)
- **% within ±1** (fraction of Likert items where persona is within 1 scale point of truth)
- **Categorical exact-match accuracy**

**Stability QA metric**:
- Phase 1a / 1b cheap-panel: **cross-model agreement %** (strict — all expected models present + parsed + identical for that tuple). Replaces within-model self-consistency.
- GPT-4o anchor subset: **within-model self-consistency** (n_samples=2, % of items where both samples gave the same code). Restored only here because the anchor is run with n=2.

**Phase 1 does NOT compute test-retest-normalized accuracy.** Park's 0.82/0.83 are normalized against a 2-week recontact baseline that GSS does not provide. We report raw metrics only and avoid direct numerical comparison to Park's normalized headline.

## 5. Sample size, budget, timeline

**The full GSS 2024 cross-section is used (N=3,309 respondents)** — locked 2026-05-09 night per Audit-3 + Joyce decision. The previous N=1,500 random-sample design (seed=42, without replacement) was a budget-driven choice; expanding to the full N=3,309 dataset removes the "sampled to a budget" framing and costs ~$380 more under the co-primary Battery LOO design (see budget table below). Phase 1a uses **N=200** (also expanded from N=100) to support the §12.2 100/100 selection/validation split. The same seed=42 governs the bootstrap CI **(B=10000, seed=42, BCa via scipy with percentile fallback — locked 2026-05-09 night per Codex N5/N6 audit)** and the paired-bootstrap LOO ΔMAE. Optional weighted reanalysis using GSS sampling weights as a robustness check (see §10).

**Seed reproducibility (Codex I-10)**: every output artifact (ndjson, summary JSON, plots) MUST encode the seed in its filename suffix (e.g., `phase1a_panel_seed42.ndjson`). The driver emits a `WARNING` to stderr when the runtime seed is anything other than 42, and refuses to overwrite a seed-42 artifact with a non-42 run unless `--force-non-canonical-seed` is passed. This guards against silent reproducibility drift if a future contributor changes the seed.

**Two-stage model strategy** (locked 2026-05-06; expanded 2026-05-09 night per Audit-3 + Joyce decision; see §12 for the multi-model-then-single rationale):
- **Phase 1a (N=200)**: run all 4 cheap OpenRouter models in parallel + GPT-4o anchor on N=100 subset. The 200 respondents are split 100/100 (selection / held-out validation) per §12.2; selector scores ONLY on the first 100; the held-out 100 yields a validation MAE reported alongside the Phase 1b headline.
- **Phase 1b (N=3,309)**: run the single cheap model selected by the §12.2 quality-primary rule + GPT-4o anchor on N=100 subset. The other 3 cheap models are NOT carried forward to 1b.

| Sub-phase | N | LLM calls per respondent | Cost / respondent | Total budget |
|---|---|---|---|---|
| Smoke | 10 | ~240 (60 primary prompts × 4 cheap, n=1) | ~$0.085 | **~$1** |
| 1a — cheap panel (N=200, 100/100 split) | 200 | ~240 (4 cheap × 60 primary) | ~$0.085 | **~$17** |
| 1b — primary (single §12.2-selected model) | 3,309 | ~60 (1 cheap × 60 primary, n=1) | ~$0.021 | **~$71** |
| 1a + 1b GPT-4o anchor (one run, serves both) | 100 | ~356 (178 prompts × n=2) | ~$1.48 | **~$148** |
| **Total Phase 1 core (pre-Battery LOO)** | | | | **~$237** |

**Per-prompt math (locked 2026-05-10 per Joyce decision Option A; supersedes the Codex N8 numbers under the new sensitivity scope)**:

   - **Cheap panel** (Qwen / DeepSeek / Llama-3.3 / Kimi): **60 prompts/respondent** = 12 primary_eval items × 5 conditions (Full + 4 single-bin LOO). **Cheap panel does NOT run sensitivity** — sensitivity_eval is anchor-only per OSF §3.2 (Park-comparable per-item raw-accuracy table on GPT-4o).
   - **GPT-4o anchor** (N=100 selection-split subset): **178 prompts × n_samples=2 = 356 calls/respondent** = 60 primary + 118 sensitivity (per-item exclusion). One anchor run serves both Phase 1a and Phase 1b reporting.

Cost rates: cheap models ~$0.000356/call (OpenRouter mid-2026 snapshot); GPT-4o ~$0.00417/call (verified against original $50 anchor quote at 12,000 calls, recomputed for 35,600 calls = $148).

**Updated total Phase 1 budget** (locked 2026-05-10 per Joyce decision Option A; supersedes the 2026-05-09 ~$875 estimate which had cheap panel running sensitivity):

- **Core Phase 1 LLM run** (smoke + 1a cheap + 1b cheap + GPT-4o anchor): ~$237
- **Phase 1c Battery LOO** (co-primary): 34 batteries × 12 primary_eval items × **3,309 respondents** × 1 sample = **~1,350,000 LLM calls** at the §12.2-selected cheap model (~$0.000356/call) ≈ **~$481**.
- **Phase 1c Shapley decomposition** (16 conditions on Phase 1a's N=200 panel; primary only — Shapley shares 4-bin LOO conditions): +~$38 incremental (11 multi-bin LOO × 12 items × 200 respondents × 4 cheap models = ~105,600 calls × ~$0.000356).
- **Total Phase 1**: **~$237 + $481 + $38 ≈ $756**.
- All cost estimates assume **no prompt caching** and must be re-verified against OpenRouter prices at smoke-test time.

**Budget evolution log** (so the OSF history reads cleanly):
- Earlier draft (~$280-300): incorrect Battery LOO enumeration, fixed by Codex N9 audit.
- Codex-N9-fixed (~$450): correct math, but assumed N=1,500 + N=100 Phase 1a + all-China panel.
- Audit-3 + Joyce-decisions-2026-05-09 (~$875): full sample (N=3,309), 100/100 Phase 1a split (N=200), Llama swap, **cheap panel running sensitivity**.
- **Current (~$756; locked 2026-05-10 per Joyce decision Option A)**: cheap panel reverts to primary-only per OSF §3.2 literal; sensitivity_eval anchor-only. Drop of ~$120 from the $875 figure (saves cheap-panel sensitivity calls; bumps anchor cost from $50 → $148 since anchor now runs sensitivity). Net ~$120 savings vs Audit-3-locked plan.

If budget is tight, reduction options: (i) Battery LOO at N=1,500 subsample → saves ~$263, (ii) Battery LOO restricted to attitudinal-bin batteries only (15 of 34) → saves ~$209, or (iii) defer Battery LOO to Phase 1d after Phase 1b headline.

Avoid quoting "~$237" without explicitly noting it is the *pre-Battery-LOO core run* total at N=3,309 under Option A. The full-pipeline figure including co-primary Battery LOO is ~$756.

**Cost estimate caveats**: (a) per-token rates above are May-2026 OpenRouter approximations and must be verified at smoke-test time before scaling. (b) These estimates assume **no prompt caching** (the persona prompt repeats across the 12 items × 2 samples within a (respondent, condition); caching would discount input tokens by ~50%). Implementing prompt caching is deferred but could halve costs further if needed.

Wall-clock: smoke in 1-2 hours; 1a in ~1 day at sequential rates (~10 min / respondent × 4 models); 1b in 3-5 days (single-model is much faster). Concurrency (ThreadPoolExecutor for parallel model calls) bumps this 4× faster on 1a; flagged but not implemented yet.

## 6. What Phase 1 produces (and what it does not)

**Produces** (publishable on its own, Phase 1-only):
- **Confidence-intervaled feature-category contribution ranking** on GSS-attitudinal-item prediction (the 4-bin LOO ΔMAE per category, with bootstrap CIs at N=3,309)
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
7. **Pre-registration on OSF before Phase 1a.** The pre-reg (filed *before* 1a fires) locks: taxonomy, primary + sensitivity eval sets, primary metric, exclusion rules (R1 battery exclusion + sensitivity per-item exclusion), R2 regression-baseline partition, the 4-cheap-model panel, the §12.2 quality-primary selection rule, the §10 aggregation + paired-bootstrap rules, **two co-primary analyses** — the **4-bin LOO** (broad feature-category attribution) and the **34-battery LOO across all 4 bins** (mechanistic cluster-level attribution) — the **bin-level Shapley decomposition** as 4-bin LOO robustness, and the §11.1 writeup language template. No post-hoc adjustment of the 4-bin assignments OR the battery map (`gss_battery_map.json` v0.2) after 1a fires.

### 8.8 Multiplicity / multiple-LOO control (nested Holm-Bonferroni primary + joint-34 sensitivity; revised 2026-05-09 evening for co-primary Battery LOO; sub-header normalized 2026-05-09 night per Codex N10)

   - **4-bin primary family** (4 ΔMAE tests): Holm-Bonferroni at α=0.05 within family. Adjusted-significant findings reported as "primary headline #1"; unadjusted bin contributions reported descriptively.
   - **Battery LOO co-primary** uses **nested Holm-Bonferroni primary correction** — one Holm family per bin, applied independently:
     - Demographic battery family (n=7): smallest p < α/7 = 0.0071
     - Behavioral battery family (n=10): smallest p < α/10 = 0.0050
     - Psychological battery family (n=2): smallest p < α/2 = 0.025
     - Attitudinal battery family (n=15): smallest p < α/15 = 0.0033
   - **Joint-34 Holm sensitivity layer (added 2026-05-09 evening)**: in addition to within-bin nested Holm, every battery is also tested against a joint Holm-Bonferroni at α=0.05 across all 34 batteries (smallest p < α/34 = 0.00147). This stricter correction is reported as a sensitivity layer used to gate **cross-bin claims**.
   - **Within-bin claims** (e.g., *"abortion is the strongest battery in the attitudinal bin"*): use **nested Holm only** — confirmatory within-bin.
   - **Cross-bin claims** (e.g., *"abortion is the strongest battery overall, ahead of subjective_wellbeing"*): require **joint-34 Holm sensitivity support**. Without joint-34 support, cross-bin rankings are descriptive only and the paper must use language like "rank-ordered" rather than "significantly stronger than."
   - Why nested-primary + joint-sensitivity: nested respects the pre-registered bin structure and gives each bin's mechanistic question fair statistical power; joint-34 prevents inflated cross-bin headlines. Joint-34 alone would force the psychological 2-battery family to clear α/34 = 0.00147 — practically impossible — and silence a pre-registered analysis arm.
   - **Bin-level Shapley** (16 conditions) is a *robustness re-aggregation* of the same 4-bin estimand; no separate multiplicity correction (it shares the 4-bin primary family).
   - **Theory-bin LOO is NOT a confirmatory family.** Theory framing enters the Discussion section as interpretive secondary analysis only (see §13.3). If a future amendment adds theory-bin LOO as a confirmatory family, that amendment will introduce its own Holm correction at that time.

### 8.9 Practical-effect-size thresholds (locked 2026-05-09 evening; anchored to Funder & Ozer 2019 effect-size taxonomy 2026-05-09 night; sub-header normalized 2026-05-09 night per Codex N10)

Because N=3309 can render very small ΔMAE values statistically significant under Holm correction, every Battery LOO and 4-bin LOO ΔMAE is reported alongside a **practical effect-size label**:

   - **small / descriptive**: ΔMAE < 0.02
   - **modest**: 0.02 ≤ ΔMAE < 0.05
   - **substantive**: ΔMAE ≥ 0.05

   **Anchor to existing literature (revised wording 2026-05-09 night per Audit-2 review)**: these thresholds are *inspired by* — not strictly mapped to — the small-but-consequential (~0.02 on a 1-5 Likert MAE) and medium (~0.05) reasoning in **Funder & Ozer (2019)** *"Evaluating Effect Sizes in Psychological Research: Sense and Nonsense"* (AMPPS, DOI: 10.1177/2515245919847202). Funder & Ozer's taxonomy applies to correlation coefficients and standardized effect sizes; we re-anchor the qualitative framing (small-but-consequential at scale, medium-when-considered-in-context) onto MAE on Likert scales for our persona-prediction context. The 0.02 threshold reflects the Funder & Ozer principle that small effects can be consequential at deployment scale — small per-item ΔMAE in an LLM persona pipeline translates to large aggregate prediction shifts across thousands of users. The mapping is conceptual, not a literal correspondence. See `LIT_REVIEW.md` §2.4 for the Funder & Ozer entry and supporting citation logic.

   - These thresholds are pre-registered. A finding is reported as substantively meaningful only if it is **both** (a) Holm-significant within its family AND (b) practical-effect ≥ "modest" with a 95% bootstrap CI that excludes the "small/descriptive" boundary. Statistical significance alone is not sufficient for headline-strength substantive interpretation.
   - Bootstrap CIs are respondent-level paired CIs **(B=10000, seed=42, BCa via scipy with percentile fallback for degenerate inputs — locked 2026-05-09 night per Codex N5/N6 audit)**. B was bumped from 1000 to keep the bootstrap-p floor (1/B) below the joint-34 Holm critical p (α/34 ≈ 0.00147); BCa is preferred over raw percentile because BCa is more accurate near zero, where many ΔMAEs sit relative to the small/modest practical-effect boundary.
   - Battery size must always be reported alongside ΔMAE; `delta_mae_per_item` (ΔMAE / n_items_in_battery) is reported as a size-aware **descriptive sensitivity column**, not the primary inferential metric.

## 9. Decisions locked (post-Bayati 2026-05-02; audit-fix 2026-05-05)

1. ✅ **Phase split endorsed**: GSS-first → targeted Cookiy in Phase 2.
2. ✅ **4-bin feature taxonomy endorsed** for the GSS-row analysis.
3. ✅ **Pre-registration on OSF before Phase 1a** — eval set, feature taxonomy, primary metric, aggregation rule, exclusion rules, secondary analyses, the 4-cheap-model panel, the §12.2 selection rule, multiplicity correction (Holm-Bonferroni within each LOO family), and the seed/sampling rule.

### 9a. Wave & timing structure — locked

- **Single-wave snapshot** (GSS 2024 cross-section, N=3,309). No panel data. No earlier-wave data. No test-retest computation.
- **Persona prediction window**: same-wave (T=2024) feature → same-wave (T=2024) held-out item.
- **Stability metric**: **cross-model agreement** across the 4-cheap-model panel (locked 2026-05-05; see §12). Within-model self-consistency only computed on the GPT-4o anchor subset (N=100, bumped from 50 per the 2026-05-06 audit).

### 9b. Eval-set composition — Path A* (locked)

- **Primary analysis (the headline)**: 12-item curated `primary_eval`. Supports the 4-bin LOO with full-population feature bins.
- **Sensitivity / Park-comparable analysis**: ~118-item `sensitivity_eval` (Park v2 GSS list minus 15 retired/renamed in 2024). Per-item exclusion when predicted. **Raw accuracy only** — no LOO, no normalization.
- One data download (`data/gss/390data1/`) covers both. Analysis-side split happens in code, audited via `gss_feature_taxonomy.json`.

### 9c. Leakage hygiene — four layers (R1 + R2 added 2026-05-08 per §3.1 audit)

1. **Layer 1 (direct, prevented)**: declared feature bins are disjoint from `primary_eval` (validator enforces); per-item exclusion in the sensitivity pass prevents direct leakage there too.
2. **Layer 2 (synonymous, not present in GSS-only design)**: Park's 27-item AVP-overlap removal does not apply to us (no AVP interview in Phase 1). Within-GSS, Park v2 SI §9 (PDF p.10 / SI p.42) argues no synonymous pairs in the cross-instrument audit.
3. **Layer 3 — R1 (battery-level structural exclusion, NEWLY ENFORCED 2026-05-08; battery map expanded v0.1 → v0.2 on 2026-05-09 evening for co-primary Battery LOO)**: when predicting any primary_eval item that belongs to a battery (per `gss_battery_map.json` v0.2, **34 batteries + 17 singletons** across all 4 bins), the entire battery is dropped from the persona prompt for that prediction. Mirrors Park v2's BFI whole-trait-block hold-out (Park v2 SI §5, PDF p.37: *"For the Big-5 we always hold-out the whole block of questions asking about a particular personality trait when predicting an outcome question within that trait"*). Implemented in `run_primary_one_respondent` and validated by `validate_taxonomy.py` check 7c.
4. **Layer 4 — R2 (regression-baseline comparator, NEWLY ADDED 2026-05-08; rhetorical caveat added 2026-05-09 evening)**: alongside the LLM panel, run a non-LLM regression baseline (`regression_baseline.py`: Ridge for Likert, multinomial Logistic for binary, 5-fold CV at the respondent level, same R1 battery exclusion applied symmetrically). The regression's per-item MAE is the "auto-correlation upper bound" any feature-to-item predictor can extract from the same input. The headline comparator approximates:
   - LLM-panel MAE on item X ≈ (regression MAE on X) + (LLM gain over regression)

   **Caveat (locked 2026-05-09 evening)**: this is a useful rhetorical decomposition, **not a literal causal partition** of LLM behavior. The regression baseline is a non-LLM predictive comparator using the same feature pool and R1 exclusions; it helps distinguish predictable survey auto-correlation from LLM-specific gains, but "LLM gain over regression" is **evidence of model-specific predictive value beyond a simple supervised baseline**, not direct proof of human-like reasoning. We report the gain as an empirical magnitude with its bootstrap CI, and do not claim it isolates any specific LLM mechanism. Avoid abstract / Discussion language like "LLM persona reasoning" without this caveat in scope.

   **Missing-data asymmetry (locked 2026-05-09 night per Codex N3 audit)**: R1 LLM-panel and R2 regression-baseline see *different* effective N for the same item, and this asymmetry must be disclosed alongside any LLM-vs-regression comparison:
   - **LLM panel** receives the persona prompt with whatever feature codes the respondent has (missing values shown as "missing"/"not asked"), and predicts the item regardless of feature completeness — so the LLM produces a prediction for nearly all 3,309 respondents per primary_eval item (excluding only those who have no truth value for that item, or who opt out of the prompted question via R/refused).
   - **Regression baseline** uses sklearn estimators that drop respondents with missing covariates (or imputes them to a median, depending on the configured strategy in `regression_baseline.py`); ballot rotation makes this attrition substantial in some bins (e.g., behavioral and attitudinal items asked on only 1 of 3 ballots → ~33% per-item coverage before R1 exclusions).
   - **Net effect**: R2's effective N per item is typically a fraction of R1's, so the comparison is not strictly apples-to-apples — the regression bound is conditioned on a denser-feature subsample. This asymmetry **biases the comparison in favor of the regression baseline** (denser inputs → lower MAE bound), making "LLM gain over regression" a *conservative* lower bound on model-specific predictive value rather than an unbiased estimate.
   - **Reporting requirement**: every R1-vs-R2 panel/table must list `n_R1_paired` and `n_R2_paired` per item, and the Phase 1 writeup must explicitly note that the gain estimate is conservative under this asymmetry. A sensitivity reanalysis restricting both R1 and R2 to the R2-eligible subsample (intersection-N) is reported as a robustness column.

   - The first term is the auto-correlation upper bound a non-LLM predictor can extract; the second term is empirical model-specific predictive gain (NOT a causal partition).
   - This is methodologically a step *past* Park v2: Park brackets the inflation between two hold-out strategies (single-item gives 0.82, whole-module gives 0.77 — Park v2 SI §6, PDF p.39 *"average normalized accuracy of 0.77 (std = 0.12)"* under whole-module hold-out vs *"0.82 (std = 0.18)"* under single-item); we add a regression comparator on the same input pool. The result is a richer descriptive comparison, not a literal causal decomposition.

**R3 (whole-attitudinal-bin Park-strict reanalysis) was considered and explicitly NOT IMPLEMENTED** (decision 2026-05-08): R3 would globally remove every variable in any primary_eval battery from the attitudinal bin before any LOO ran, leaving an artificially-thin bin. Joyce's call: R1 already provides per-item structural exclusion at the right granularity (the predicted item's own battery, not all batteries), and R3 would conflate two effects (battery-level redundancy + bin-level information capacity), making the LOO ranking uninterpretable. R1 + R2 together provide the structural defense (R1) and the partition test (R2) that R3 was meant to triangulate.

### 9d. Two-week plan

1. (✅ done) Lock design (this section)
2. (✅ done) Build feature-taxonomy JSON
3. (✅ done) Joyce: download GSS data
4. (✅ done) Build GSS loader
5. (✅ done) Build `gss_pipeline.py` (persona-prompt builder, LLM dispatcher, scorer for GSS rows)
6. End-to-end smoke test on N=10
7. Draft OSF pre-registration
8. Run Phase 1a (N=200, 100/100 selection/validation split per §12.2) sanity check
9. Present 1a results to Bayati before launching 1b

### 9e. OSF pre-registration lock checklist (locked 2026-05-09 evening)

The following items must be in the OSF pre-registration document, locked before Phase 1a fires. This list IS the OSF table of contents.

- [ ] **Data**: GSS 2024 cross-section, 3-batch fixed-width extract path documented
- [ ] **Sampling**: random sample without replacement, **seed = 42**, N=3309 from 3,309 (gss_pipeline.py:sample_respondents)
- [ ] **Eval items**: 12 `primary_eval` items locked in `gss_feature_taxonomy.json` v0.3
- [ ] **Sensitivity items**: 118 `sensitivity_eval` items locked in `gss_feature_taxonomy.json` v0.3
- [ ] **Feature taxonomy**: v0.3 (140 features, 24/25/8/83 across 4 bins; locked 2026-05-05)
- [ ] **Battery map**: v0.2 (34 batteries + 17 singletons; locked 2026-05-09 evening)
- [ ] **Leakage hygiene Layer 3 — R1 battery exclusion**: per-item battery drop using `gss_battery_map.json` v0.2
- [ ] **Leakage hygiene Layer 4 — R2 regression baseline comparator** (with rhetorical-decomposition caveat per §9c.4)
- [ ] **Primary metrics**: Likert MAE (respondent-macro), % within ±1, categorical exact-match
- [ ] **Aggregation rules**: §10 (respondent-macro primary, item-macro secondary, paired-bootstrap LOO ΔMAE)
- [ ] **Bootstrap**: B=10000, respondent-level paired, seed=42, BCa via scipy with percentile fallback for degenerate inputs (locked 2026-05-09 night per Codex N5/N6)
- [ ] **4-bin LOO family Holm**: α=0.05 within family (4 tests)
- [ ] **Battery LOO nested Holm primary**: per-bin (D=7 / B=10 / P=2 / A=15 tests)
- [ ] **Battery LOO joint-34 Holm sensitivity gate**: required for cross-bin claims
- [ ] **Practical-effect-size thresholds**: small <0.02, modest 0.02-0.05, substantive ≥0.05; significance + magnitude both required for headline claims
- [ ] **Phase 1a model panel**: Qwen-2.5-72B + DeepSeek-V3.1 + **Llama-3.3-70B-Instruct (Meta)** + Kimi K2 + GPT-4o anchor (locked in `llm_router.py::MODEL_PANEL_PRIMARY`; MiniMax → Llama swap 2026-05-09 night for cross-family balance per Audit-3)
- [ ] **§12.2 model-selection rule**: quality-primary, DQ-1 + DQ-3 + cost tie-break + Qwen fallback (locked, executable in `select_phase1b_model.py`)
- [ ] **DQ-3 reference**: `outputs/primary_eval_human_variance_2024.json` (locked GSS 2024 per-item human variance)
- [ ] **GPT-4o anchor scope**: N=100 selection-split subset, **primary + sensitivity** (n_samples=2; locked 2026-05-10 Joyce decision Option A — anchor is the only run for Park-comparable sensitivity_eval per OSF §3.2), used for the per-item Park v2 SI Table 3 raw-accuracy anchor table; NOT the N=3309 headline
- [ ] **Theory interpretation**: Discussion-section only, no horse race, no theory-bin LOO, no Stage 3 refinement, no hard supports/refutes thresholds (per `theory_interpretation_guide.md`)
- [ ] **Implementation status disclosure** (this is the *lock-first defense* per Codex audit 2026-05-09 night addition A — used CONFIDENTLY, not apologetically; revised 2026-05-09 night per Audit-fresh review to drop the contradictory "not yet implemented" wording — the analyzers ARE implemented; only the orchestration drivers are not): **Shapley decomposition + Battery LOO analyzers ARE implemented and self-tested** (`shapley_decomposition.py` 8-assertion test + `battery_loo.py` 8-assertion test, both green; consume records-JSON in `gss_driver.py` format and produce locked-schema outputs). The **orchestration drivers** that actually emit `condition="shapley_*"` and `condition="battery_loo_drop_*"` records (i.e., `gss_driver.py` extension to enumerate the 16 Shapley conditions and 34-battery LOO conditions) are NOT yet implemented and remain to be built before Phase 1c. 4-bin LOO + R1 + R2 + §12.2 selector + audit primitives + battery map v0.2 + DQ-3 reference are also *implemented and self-tested* (validate_taxonomy 10-check + AUDIT A-E + §12.2 7-branch + R2 12/12 self-test, all green). **Pre-registration commitment**: these analyses were locked at the analysis-plan and analyzer-implementation levels prior to OSF lock; the orchestration runtime will pass self-tests on synthetic fixtures (matching Tools 1-2 schema output exactly) BEFORE any paid Phase 1c run. This is conventional OSF practice for analysis-plan preregistration.
- [ ] **Writeup language template (§11.1)**: forbidden mentalist claims; required scope qualifiers
- [ ] **Decisions log appendix**: PROJECT_SYNTHESIS.md §4 (locked, when, against what evidence)

> ⚠️ **OSF copy-source rule (locked 2026-05-09 night)**: when drafting the OSF preregistration, copy text ONLY from current live-design sections of `gss_phase1_design.md` (§1.0, §4, §8.8, §8.9, §9c, §9e, §10, §11.1, §12.2, §13.0–§13.2) and from `PROJECT_SYNTHESIS.md` §3 + §5 (which are aligned to the live design). Do **NOT** copy from any "What changed YYYY-MM-DD" changelog block in `STATUS.md`, the top-of-file revision-note paragraph in `PROJECT_SYNTHESIS.md`, or the `*.SUPERSEDED-*.md` files — those preserve historical wording (e.g., "attitudinal-bin Battery LOO", "panel median primary headline", "v0.1 15 batteries", "conditional on attitudinal dominance") that contradicts the live spec and would confuse OSF reviewers.

### 9f. Readiness gates before paid runs (locked 2026-05-09 evening)

**Before N=10 paid smoke test**:
- [ ] OpenRouter API key set in `OpenRouter_api.txt` (gitignored)
- [ ] Smoke command **chosen intentionally** — verify no flag accidentally triggers full sensitivity pass across all 4 cheap models (operational risk, see §9g)
- [ ] Expected dollar cost printed and understood (~$2-3 for `--n 10`)
- [ ] All non-paid tests green (validate_taxonomy + audit A-E + selector + R2 baseline)

**Self-imposed smoke discipline (locked 2026-05-09 night per Codex audit addition)**:

> **Smoke = plumbing only, not data look.** N=10 smoke verifies (a) the API succeeded, (b) artifacts have the right shape (NDJSON fields populated, persona_code parsed within valid_codes, parse_failure rate not catastrophic), (c) the seed-42 reproducibility guard fires correctly, and (d) atomic-write resume works on interruption. **Do NOT open the JSON and read the actual codes.** If smoke output informs a design tweak (a prompt change, a parsing rule, a model swap, a battery edit), you have silently pre-violated your own pre-registration. Smoke is for verifying the implemented base pipeline; it is NOT for piloting design choices.

This rule is enforced by the maintainer (Joyce) only — there's no automated check. If a future commit shows changes to prompt wording / parsing rule / model panel / battery map between the smoke run and the Phase 1a launch, that's a pre-registration deviation that must be filed as an OSF amendment with rationale.

**Before Phase 1a (N=200, 100/100 split per §12.2)**:
- [ ] OSF pre-registration draft locked (per §9e)
- [ ] All documentation drift resolved (no stale references to old battery counts, panel-median-as-headline, conditional Battery LOO, theory-bin confirmatory)
- [ ] **Shapley / Battery LOO implementation status disclosed accurately in OSF.** *Locked 2026-05-09 night per Codex N2 audit; phrasing tightened per Audit-2 review 2026-05-09 night to remove "constrains design space" language*: at lock time, **the analyzers (`shapley_decomposition.py`, `battery_loo.py`) ARE implemented and self-tested** (synthetic-fixture self-tests pass; see §13.1 of `osf_preregistration_v1.md`); what is NOT implemented is the **orchestration runtime** in `gss_driver.py` that emits `condition="shapley_*"` / `condition="battery_loo_drop_*"` records the analyzers consume. The OSF lock declares the **analysis contract** (input schema + output schema + math) AND the orchestration design (battery enumeration list, Shapley 16-condition mapping, R1 interaction with battery-level drop); these are frozen at lock time. **Only the runtime implementation timing is deferred** — `tier1_tool_schemas.md` Tools 1-2 contain the precise spec the orchestration code must satisfy. **Schema and design cannot change post-OSF without a logged amendment**; runtime can complete after Phase 1a but only as a faithful implementation of the locked spec. The Phase 1a → 1c gate is "orchestration drivers ready, byte-identical to spec" before any 16-condition or 34-battery paid run fires.
- [ ] Model panel + §12.2 selector locked in OSF
- [ ] Cost estimate verified against current OpenRouter prices

**Before Phase 1b (N=3309)**:
- [ ] Phase 1a complete; results reviewed
- [ ] §12.2 selector run on Phase 1a output → selected model recorded in commit + OSF amendment if any
- [ ] N=10 + N=100 parse-failure rates and DQ-3 mode-collapse checks within acceptable range (per §12.2 DQ-1/DQ-3)
- [ ] Phase 1b CLI command chosen intentionally; no accidental sensitivity-pass-on-all-cheap-models

### 9g. Operational risk — accidental sensitivity-pass on all 4 cheap models

**Mitigations (all locked 2026-05-10 per Joyce decision Option A; previously a §9g manual-discipline risk, now codified)**:
- **Use the named modes for paid runs** (locked 2026-05-09 night per Audit-fresh review; sensitivity scope locked 2026-05-10 per Option A): `--phase1a` (cheap panel × N=200, primary-only — sensitivity is anchor-only per OSF §3.2), `--phase1b --phase1b-model SLUG` (single §12.2-selected cheap model × N=3,309, primary-only), `--phase1b-anchor` (GPT-4o × N=100 selection-split subset, n=2, **primary + sensitivity** — produces the Park-comparable Table 3 anchor table). The named modes hard-code N + panel + sensitivity scope to the locked spec, eliminating the legacy manual-flag-composition risk.
- **F9 cost guard (locked 2026-05-10 per Audit-fresh-2)**: the driver REFUSES to run --n ≥ 1000 with multiple models AND sensitivity unless `--allow-panel-wide-large-n` is explicitly passed (prints projected cost). This catches the operational accident where a manual `--n 3309` with the default 4-cheap panel + sensitivity would burn ~$839 instead of the locked ~$71 single-model 1b run.
- **Stub modes**: `--battery-loo` and `--shapley` print clear NOT-IMPLEMENTED + pointer to OSF §13.2 (analyzer ready, orchestration runtime deferred until before Phase 1c).

## 10. Aggregation & weighting (pre-registered)

**Per-respondent metric** — for each (respondent r, condition c):
- For each Likert primary_eval item i that respondent r answered (i.e., not in MISSING_CODES): compute `|persona_response - true_response|` for both LLM samples; average within respondent across i.
- For each categorical primary_eval item: 1 if exact match, 0 otherwise; average across answered categorical items.

**Headline aggregation** — primary metric is **respondent-macro-averaged**:
- Primary Likert MAE = mean over respondents of (per-respondent average Likert error). Each respondent contributes equally regardless of how many items they answered, provided they answered ≥1 Likert primary_eval item.
- This treats each respondent as one observational unit, controlling for ballot-induced coverage variation.
- Standard errors via bootstrap (B=10000, BCa via scipy with percentile fallback — locked 2026-05-09 night per Codex N5/N6) at the respondent level.

**Single-LLM-draw variance disclosure (locked 2026-05-09 night per Codex N4 audit).** Phase 1 uses `n_samples=1` per (respondent × condition × item) per the locked §12 panel design (rationale: budget; cross-model variance via the 4-model panel substitutes for cross-draw variance in §12.2 selection). One implication that must be disclosed in the writeup:
- **The respondent-level paired bootstrap captures sampling variance over respondents, NOT generation variance over LLM stochastic draws.** A second draw at temperature=0.7 for the same (respondent, condition, item) would in general produce a different code; the bootstrap CI does not reflect this.
- **Why this matters**: the *true* uncertainty around an LLM-MAE point estimate is the convolution of (a) sampling variability over respondents — captured — and (b) generation variability over LLM draws — NOT captured. Reported CIs are therefore **mildly under-stated** relative to a fully-honest CI that integrates both sources.
- **Quantification commitment**: a small N=10-respondent re-draw audit at n_samples=5 (50 redundant calls per condition) is run during Phase 1a smoke testing; the resulting per-(respondent, item) standard deviation across draws is reported in the writeup methods section as an absolute bound on within-respondent generation noise. If the audit finds within-draw SD > 10% of the cross-respondent SD on the headline metric, the abstract must explicitly note "CIs reflect respondent variance only; ~X% relative inflation expected if generation variance were included."
- **Why we do not pre-register full multi-draw**: at the locked panel size (1 selected model × 1 draw × 60 primary prompts × 3,309 respondents) Phase 1b cheap costs ~$71; running n_samples=5 panel-wide would 5× the headline run alone (~$355), and 5× the Battery LOO co-primary (~$2,400). Park et al. 2024 also use n_samples=1 for the analogous panel rows.

**Secondary aggregation** — also reported for transparency:
- **Item-macro-averaged**: mean MAE per item, then average over items. Useful when items differ systematically in difficulty.
- **Respondent-item weighted (pooled)**: pool all (respondent, item) errors and average. Equivalent to weighting respondents by their answered-item count.

**Inferential frame** — locked 2026-05-09 night per Codex M1 audit. Phase 1's bootstrap is paired-respondent-level, which assumes simple random sampling; GSS 2024 is a multi-stage probability sample with PSU + strata + WTSSALL weights. **We explicitly restrict the inferential frame to the GSS-2024 cross-section as a fixed dataset** — i.e., we estimate predictive properties on this specific 3,309-respondent extract, NOT population-level parameters of the U.S. adult attitude landscape. All "respondent-level" language refers to the sampled 1500/3309 from this fixed dataset. We do NOT claim population inference. A weighted/cluster-bootstrap robustness check using `WTSSALL` + PSU is a future-work extension; if pursued, reported as a separate sensitivity column with explicit "fixed-dataset vs population-inferential" framing.

**LOO-condition delta** — primary inferential quantity per category bin: `ΔMAE_bin = MAE(LOO-drop-bin) − MAE(Full)`. Bootstrap CIs at respondent level via **paired bootstrap**: in each of the B=10000 resamples (BCa via scipy with percentile fallback — locked 2026-05-09 night per Codex N5/N6), draw one respondent set with replacement, then compute MAE(Full) and MAE(LOO-drop-bin) on **the same resample**, then take the delta. Do not bootstrap MAE(Full) and MAE(LOO) independently (would over-inflate Δ-CI variance).

### 10a. R1 asymmetric burden across primary_eval items (locked 2026-05-09 night per Codex M6)

The R1 battery exclusion is asymmetric across the 12 primary_eval items because some primary_eval items have battery-mates inside primary_eval and others do not. Specifically:

| Group | Items | R1 strips when predicted |
|---|---|---|
| **In-battery primary_eval** (4 of 12) | FECHLD, FEPOL (gender_role_attitudes battery, 5 items) | 5-item battery from prompt |
| | CONFINAN, CONLEGIS (confidence_in_institutions battery, 13 items) | 13-item battery from prompt |
| **Singleton primary_eval** (8 of 12) | POLVIEWS, PARTYID, ABANY, CAPPUN, GUNLAW, RACDIF1, HELPPOOR, SATFIN | only the predicted item itself |

The respondent-macro Likert MAE weights all 12 items equally, so the 4 in-battery items contribute under structurally thinner conditioning than the 8 singleton items. This is **NOT a bug** — it's the correct behavior of R1 (the battery-mates ARE same-construct redundant siblings that must be removed) — but it produces an implicit per-item weighting that a careful reviewer would flag.

**Pre-registered reporting rule**: alongside the headline respondent-macro Likert MAE over all 12 items, also report:

1. **Headline split**: respondent-macro MAE over the 4 in-battery primary_eval items vs over the 8 singleton primary_eval items, separately. Reported in Table 1 (or Table 2) with explicit labels.
2. **Sensitivity column**: respondent-macro MAE recomputed weighting items inverse to their R1-stripped feature count (in-battery items down-weighted, singletons up-weighted). Reported as descriptive sensitivity.

This is a methodological asymmetry, NOT a confound. We disclose it explicitly because reviewers will (correctly) ask about it.

## 11. What a positive Phase 1 result does and does NOT support (writeup constraints)

**Phase 1 evidence supports**:
- Within-GSS-attitude prediction in 2024, feature-category bin X has the largest contribution (or smallest, etc.).
- A specific, item-level raw-accuracy comparison to Park v2 Table 3 entries.
- Persona self-consistency at temperature 0.7 is high/low under various conditions.

**Phase 1 evidence does NOT support**:
- "The LLM persona simulates humans at X%" — we have no recontact baseline; X% is unnormalized.
- "Our normalized accuracy matches Park's 82%" — we do not compute normalized accuracy.
- "Attitudinal features dominate human-simulation fidelity" — they may dominate due to within-domain auto-correlation; with R1 + R2 in force we can quantify this, but the result remains GSS-attitude-prediction-internal, not a fidelity claim.
- "Demographics don't matter for personas" — we measure demographics' contribution within GSS-attitude prediction, not their general informativeness for BFI personality or behavioral games.
- Generalization to BFI personality or behavioral games — Phase 2 only.
- "Robust across LLM families" — the cheap panel is now **3 China-trained + 1 Western-trained** (Qwen / DeepSeek / Llama-3.3-Meta / Kimi) after the 2026-05-09 night MiniMax→Llama swap; the cross-family claim is restricted to "across four instruction-tuned models spanning Western and Eastern training sources in a 200-respondent comparison" and does NOT apply to the N=3309 Phase 1b headline (which runs on a single §12.2-selected model). Cross-Western/Eastern robustness in the headline lives only on the GPT-4o anchor (N=100 subset).
- **Bin-level claims about the psychological bin** — the psychological bin in `gss_feature_taxonomy.json` v0.3 contains only 8 GSS variables organized into **2 batteries** (`subjective_wellbeing` + `interpersonal_trust`, per the SHA-256-frozen `gss_battery_map.json` v0.2). Two batteries is structurally too thin for a category-level Phase 1 finding (added 2026-05-09 night per Audit-3 M-new-4 review). Bin-level psychological ΔMAEs are reported descriptively only; the inferential headline for psychological-feature contribution lives at the **battery level**, where the 2 batteries each have ≥4 items and the nested Holm correction inside `n=2` is comparatively weak (α/2 = 0.025). Reviewer-facing claims about psychology in the abstract should be Battery-LOO-level, never bin-level.

These constraints carry over into the abstract, headline figures, and reviewer-facing claims of the Phase 1 writeup.

### 11.1 Writeup language template (locked 2026-05-08, per §3.3 + §3.4 audit)

The following sentence-level constraints are **mandatory** in any Phase 1 abstract, headline figure, or reviewer-facing summary:

| Constraint | Required form | Forbidden form |
|---|---|---|
| "Persona fidelity" qualifier | "within-wave attitudinal prediction" / "single-wave GSS attitudes" | bare "persona fidelity" |
| Cross-model robustness scope | "across four China-trained instruction-tuned models in a 100-respondent comparison" | bare "across LLM families" |
| Headline-N model identity | "the {selected_model} reported under the §12.2 quality-primary rule, N=3309" | "the cheap panel" / "the LLM panel" |
| Park comparison anchor | "the GPT-4o anchor on the N=100 subset, with single-item hold-out matching Park v2 SI §6" | "matches Park's 82%" |
| Auto-correlation framing | "after R1 battery-level exclusion and R2 regression-baseline partition" | bare "after leakage hygiene" |
| Test-retest claim | (none — say nothing about test-retest) | "normalized accuracy" / "fidelity" |

The abstract and the dashboard / GitHub Pages footer must each be checked against this table before submission. A reviewer who sees a violation immediately recognizes the over-claim — preventing this is what §11.1 exists for.

## 12. Multi-model panel design (locked 2026-05-05)

### Rationale

GPT-4o-only Phase 1 would cost ~$900 at N=3309, exceeding the $300-500 budget. More importantly, single-model results conflate "feature-category contribution" with "GPT-4o-specific quirks" — a reviewer could plausibly reject "X is the most predictive feature category" with "but maybe only on GPT-4o."

**Solution**: query the same persona prompts on a **panel of 4 cheap, diverse OpenRouter-available models** as the primary analysis. The headline finding becomes "feature-category contribution to GSS-attitude prediction is robust **across LLM families**" — a stronger claim than single-model GPT-4o.

A small GPT-4o anchor on a 100-respondent subset preserves direct Park v2 Table 3 comparability without blowing budget.

### Locked model panel

| Role | Model | Provider | Input $/M (≈) | Output $/M (≈) | Why this model |
|---|---|---|---|---|---|
| Cheap-panel primary | **Qwen-2.5-72B-Instruct** | Alibaba | 0.40 | 0.40 | strong instruction-following; multilingual |
| Cheap-panel primary | **DeepSeek-V3.1** | DeepSeek | 0.20 | 0.80 | very cheap, strong reasoning |
| Cheap-panel primary | **Llama-3.3-70B-Instruct** | Meta (US) | 0.30 | 0.50 | **Western-trained;** swapped in pre-OSF 2026-05-09 night per Audit-3 cross-family balance review (formerly MiniMax-M1) |
| Cheap-panel primary | **Kimi K2** | Moonshot | 0.40 | 1.00 | long-context strong; 4th distinct family |
| Anchor | **GPT-4o** | OpenAI | 2.50 | 10.00 | Park v2 used this; direct Table 3 comparability |

**Panel diversity argument**: 4 different teams, 4 different RLHF philosophies, **3 China-trained + 1 Western-trained**. Convergence across all 4 = result generalizes beyond any single model's bias AND past single-region training-data biases.

**Honest caveat about diversity scope (revised 2026-05-09 night)**: After the MiniMax→Llama-3.3 swap, the cheap panel is **3 China-trained (Alibaba, DeepSeek, Moonshot) + 1 Western-trained (Meta-Llama)**. The Western-trained slot defangs the "all-China cross-family-bias" reviewer attack on the headline panel. The GPT-4o anchor (N=100 subset) remains a separate Western-trained reference for direct Park v2 Table 3 anchoring. For even-stronger Western-vs-Eastern robustness claims (e.g., Mistral-Large-2 swap), reserve as a future sensitivity reanalysis.

### Sampling rules

- **Cheap models**: `n_samples = 1` per (respondent, item, condition). Cross-model agreement (% of items where all 4 models gave the same code) replaces within-model self-consistency as the primary stability metric.
- **GPT-4o anchor**: `n_samples = 2` per (respondent, item) on the **N=100 selection-split subset**, **primary + sensitivity** (locked 2026-05-10 Joyce decision Option A; supersedes earlier "primary-only" wording). Restores Park-style within-model self-consistency for the directly-comparable subset AND **runs the 118 sensitivity_eval items per-item-excluded** to produce the Park-comparable per-item raw-accuracy table side-by-side with Park v2 SI Table 3 — the anchor is the ONLY run that produces this Park-comparable sensitivity table; cheap panel does not run sensitivity (anchor-only per OSF §3.2). N=100 (bumped from N=50 per Codex audit 2026-05-06) gives wider per-item CIs but still tight enough for per-item Park v2 Table 3 anchoring. One anchor invocation serves both Phase 1a and Phase 1b reporting purposes (same N=100 selection-split respondents).

### Headline output extension to multi-model

The aggregation in §10 is computed:
- **Per model**: each cheap-panel model gets its own respondent-macro / item-macro / pooled headline + bootstrap CIs. Reported alongside in the writeup.
- **Panel median (Phase 1a robustness summary, NOT the N=3309 headline)**: for each (respondent, condition, item, sample-position-equivalent), take the median (Likert) or mode (categorical) across the 4 cheap-panel models. Re-run aggregation on this synthetic "panel respondent." **Reported as a Phase 1a (N=100 selection split per §12.2) robustness summary** for cross-model coherence; per-model deltas in supplementary. The N=3309 Phase 1b headline is the §12.2-selected single model, NOT the panel median (Phase 1b runs only one selected model — see §12.2 + line 401 below + §13's writeup constraint).
- **GPT-4o anchor**: per-item raw accuracy on the 12 primary_eval items + the 118 sensitivity_eval items on N=100 subset, n_samples=2, side-by-side with Park v2 SI Table 3 (locked 2026-05-10 Joyce decision Option A; sensitivity_eval is anchor-only per OSF §3.2).
- **Cross-model agreement**: % of (respondent, item, condition) tuples where all 4 cheap models output the same integer code. Reported as the new "consistency QA metric" replacing within-model self-consistency.

### What the writeup must say (extension to §11 constraints)

- "The N=3309 headline is the §12.2-selected single model. Phase 1a (N=200 with 100/100 selection/validation split; selection set N=100 reports per-model and panel-synthesized robustness for cross-model coherence) — the panel median is a Phase 1a robustness summary, NOT the N=3309 headline because Phase 1b runs only one selected model."
- "Direct comparability to Park v2 Table 3 is via the N=100 GPT-4o anchor subset, not via the cheap-model panel. The cheap-model panel addresses generalization across LLM families; the anchor addresses model-comparability with the established benchmark."
- "Cross-model agreement at temperature 0.7 (4 cheap models on the same item) is reported as a stability QA metric in lieu of within-model self-consistency. The two are different concepts."

### Pre-registration must declare

Before Phase 1a launches the OSF pre-reg locks:
- The exact 4-cheap-model list for Phase 1a (prevents post-hoc cherry-picking)
- The model-selection rule from 1a → 1b (locked below in §12.2)
- The GPT-4o anchor scope (N=100 selection-split subset, **primary + sensitivity**, n_samples=2 — locked 2026-05-10 Joyce decision Option A; anchor is the only run for Park-comparable sensitivity_eval per OSF §3.2)
- Aggregation method (per-model + panel median/mode + cross-model agreement)
- Cross-model agreement metric definition (strict: all expected models present + parsed + identical)

### §12.2  Locked model-selection rule (Phase 1a → Phase 1b) — quality-primary

**Phase 1a sample structure (locked 2026-05-09 night per Audit-3 + Joyce decision)**: Phase 1a runs at N=200 with a **pre-registered 100/100 selection/validation split** (seed=42 deterministic). The first 100 respondents are the **selection set** — all selector quality scoring (MAE, DQ-1, DQ-3, tie-break) operates ONLY on these 100. The other 100 respondents are the **validation set** — held out from selection entirely. After the selector picks a model on the selection set, the chosen model's MAE is **also reported on the held-out 100 validation respondents** alongside the N=3309 Phase 1b headline. Rationale: prevents post-selection-inference / overfit-on-eval-set attack — a reviewer asking "of course your selected model has low MAE; it was selected on the same items you headline on" is rebutted by the validation-N MAE which the selector never saw.

After the selection set scores all 4 cheap models, Phase 1b is run at N=3309 on the single cheap model that minimizes **respondent-macro Likert MAE on the Phase 1a SELECTION primary_eval items, full condition only** — i.e., the model whose persona predictions are most accurate on the headline metric of the paper, on the selection-half only.

```
selection_set      = sample[:100]   # respondents 0..99 of seed-42 sample
validation_set     = sample[100:200]  # respondents 100..199 (HELD OUT from selection)

primary_score(model) = respondent_macro_Likert_MAE_on_SELECTION_primary_full
                       (parse-failed items excluded from the per-respondent average;
                        a respondent contributes only if they have ≥1 valid Likert item)
choose argmin

# After selection, ALSO report:
validation_mae(selected_model) = respondent_macro_Likert_MAE_on_VALIDATION_primary_full
# This number must appear in §11.1 abstract template alongside the N=3309 headline.
```

**Why quality-primary, not cost-primary** (locked decision 2026-05-06): the 4-cheap-panel members differ in per-call cost by at most ~2× (~$50-80 swing on the entire N=3309 1b run), but can differ in MAE by considerably more. Optimizing the selection criterion on a $50 axis when the *paper's headline metric is MAE* is internally inconsistent — the rule should pick the model that is best at the thing the paper measures. Cost is preserved as a tie-break, not as the primary score.

**Pre-registered guard rails (all locked in OSF before Phase 1a fires):**

1. **DQ-1 — Parse-failure ceiling.** Any model with `parse_failure_rate_on_1a > 0.30` is removed from the candidate set BEFORE quality scoring. Rationale: a model that parse-fails on >30% of items is operationally unusable at scale regardless of its measured MAE on the parsed remainder.

2. **DQ-3 — Mode-collapse guard (per-item relative threshold; revised 2026-05-08 per audit §3.9).** For each of the 12 primary_eval items, the model's output-code population variance across respondents must satisfy `var(model_i) ≥ 0.30 × var(human_i)`, where `var(human_i)` is the locked GSS 2024 per-item human variance (computed once from `outputs/primary_eval_human_variance_2024.json`, OSF-pre-registered). A model is disqualified if **more than 50% of items fail** this floor — i.e., a majority of items show output collapse relative to the empirical human distribution. Rationale: an absolute threshold (e.g., 0.5) is too lenient on heavily-skewed items where human variance itself is < 0.5 (FEPOL = 0.15, GUNLAW = 0.21, FEPOL is 82/18 split) and too strict on widely-spread items (PARTYID human variance = 4.24). The relative threshold scales with the empirical human distribution per item; 30% is the OSF-pre-registered floor (chosen because (a) a perfectly-calibrated LLM can plausibly run at ~50-100% of human variance, so 30% gives substantial headroom; (b) a mode-collapsed LLM with single-mode output has variance 0% of human; the 30% line cleanly separates the two regimes per the §12.2.1 simulation table).

3. **Tie-break — cost.** Among models within **5% of the best primary_score** (i.e., `MAE_model ≤ 1.05 × MAE_best`), select the one with the **lowest `cost_per_call_USD × (1 + parse_failure_rate)`** score. Rationale: when quality is statistically indistinguishable, the cost-pre-registered framing of the cheap panel still informs the choice.

4. **All-DQ-fail PAUSE for human review (locked 2026-05-09 night per Audit-2 + Joyce decision).** If after DQ-1 + DQ-3 the candidate set is empty (all 4 models failed gates), the selector returns `selected=None, rationale="all_dq_fail_pause_for_review"`. Phase 1b does NOT proceed. Rationale: all-DQ-fail is a SIGNAL that something structural is wrong (the prompt template, the parser, or the entire model panel is broken at the current OpenRouter snapshot); silently bypassing the quality gate to a named-Qwen fallback would waste $209 of paid Phase 1b runs on a model that already failed quality checks. The pause requires diagnosing the failure and either rerunning Phase 1a, swapping the panel, or filing an OSF amendment. **Earlier drafts had a Qwen-fallback-on-all-DQ-fail rule; that was removed pre-OSF after Audit-2 review pointed out it bypasses the gate.**

5. **Deterministic Qwen tie-break fallback — narrow scope.** If ≥2 candidates pass DQ AND tie on both quality (within 5%) AND cost (within 1%), **Qwen-2.5-72B-Instruct** is named. Reason: when models are statistically and economically indistinguishable, a deterministic named choice avoids a coin-flip; Qwen is the most stable instruction-following baseline of the four. The OSF pre-reg names Qwen explicitly so there is no post-hoc judgment. (Note: this is the ONLY remaining Qwen-fallback path. The all-DQ-fail path is now PAUSE.)

**Why each guard rail**:
- DQ-1 prevents picking a parse-broken model that scored a fluke MAE on its small parsed subset.
- DQ-3 is the critical anti-cheat. Without it, a model that always outputs "4" on every item would beat a model that genuinely tries to predict each respondent — because most GSS attitudes cluster centrally and "always 4" has lower MAE than calibrated guesses on outliers. With DQ-3, mode-collapsed models are filtered out before the quality comparison.
- Cost as tie-break (not primary) preserves the budget framing in the noise-equivalent regime without letting it override a real quality difference.
- All-DQ-fail PAUSE keeps the quality gate honest: a failed DQ pass means rerun-or-amend, not silent override.
- Qwen tie-break-only fallback keeps the rule fully deterministic in the indistinguishable-models case — no judgment call required.

**The selection rule in one sentence (for the abstract / writeup; revised 2026-05-09 night):**
> "We selected the Phase 1b model as the lowest-MAE Phase 1a candidate on the pre-registered N=100 selection split, among models passing parse-failure (≤30%) and per-item relative-variance gates (`var(model_i) ≥ 0.30 × var(human_2024_i)` for ≥50% of primary_eval items); cost served as a within-5% tie-break, with Qwen-2.5-72B-Instruct as the named tie-break fallback. All models failing DQ triggers a pre-registered pause for human review rather than a quality-gate override. The selected model's MAE on a held-out N=100 validation split is reported alongside the N=3309 headline."

**Scope** — Phase 1b reports remain valid as "predictive findings on the quality-selected model." Multi-model robustness is established by the 1a comparison itself (published alongside 1b). The thesis claim becomes:
> "On Phase 1a (N=200 with a pre-registered 100/100 selection/validation split, 4 cheap models), feature-category contribution rankings agreed within bootstrap noise across all 4 models. We selected {model_X} for Phase 1b under the §12.2 quality-primary criterion (with parse-failure and mode-collapse gates, cost tie-break, and a named-Qwen tie-break-only fallback; all-DQ-fail returns a pause-for-review verdict rather than a silent override); the N=3,309 results on {model_X} are reported alongside both the 1a multi-model robustness panel AND {model_X}'s held-out validation MAE on the N=100 validation split — a pre-registered post-selection-inference defense."

This is honest, internally consistent with the paper's primary metric, and avoids the cherry-picking objection.

**History note**: an earlier draft (2026-05-06 morning) proposed a cost-primary rule with quality as tie-break. That was reconsidered the same day after recognizing that the 4-cheap-panel cost spread is too narrow to dominate over typical quality differences, and that selecting on a metric different from the paper's headline metric creates an internal inconsistency that reviewers will flag. The cost-primary alternative is preserved in version-control history but is NOT what the OSF pre-reg locks.

---

## 13. Secondary analyses (locked 2026-05-09 lean → 2026-05-09 evening: Battery LOO promoted to co-primary)

**Design philosophy** (locked 2026-05-09 evening): the paper has TWO co-primary contributions:
1. **Broad finding** (4-bin LOO): which feature category contributes most to LLM persona prediction of attitude outcomes?
2. **Mechanistic finding** (34-battery LOO across all 4 bins, nested Holm): which specific construct-level clusters drive the signal within each bin?

Bin-level Shapley is robustness on the broad finding. Theory interpretation enters Discussion only.

### 13.0 Hierarchical justification — why two co-primary analyses are NOT a multiplicity sin

A reviewer will reasonably ask: *"You tested 4 broad bins and then 34 batteries. Is this just many chances to find significance?"*

The honest answer: **No, the design is hierarchical, and multiplicity is controlled within each pre-registered level.**

```
LEVEL 1 — 4-bin LOO (broad)
    Question: Which broad feature category contributes most to LLM
              prediction of held-out GSS attitude items?
    Tests:    4 ΔMAE tests, one per bin
    Holm:     within-family α=0.05 (smallest p < 0.0125)

LEVEL 2 — Battery LOO (mechanistic), nested inside Level 1's pre-registered bins
    Question: Within each pre-registered bin, which construct batteries
              drive the predictive signal?
    Tests:    34 ΔMAE tests, partitioned per bin (D=7 / B=10 / P=2 / A=15)
    Holm:     nested-Holm primary correction per bin
              + joint-34 Holm sensitivity gate for cross-bin claims (§8.8)
```

**The two co-primary analyses answer different levels of the same attribution-question family**:
- The 4-bin LOO identifies which broad feature category matters.
- The Battery LOO identifies which pre-registered construct-level clusters account for signal within each category.

Battery LOO is **not** a fishing expedition across 34 unrelated tests. **Batteries are nested inside pre-registered bins.** Co-primary status is justified because the paper has two linked questions — broad category attribution + within-category mechanism — and a single broad answer ("attitudinal dominates") is not an answer to "what mechanistically drives the attitudinal signal."

**Rebuttal language for the paper / reviewer response**:
> "The 4-bin LOO and Battery LOO answer different levels of the same attribution question. The former identifies which broad feature category matters; the latter identifies which pre-registered construct batteries account for signal within each category. Battery LOO is therefore a mechanistic co-primary analysis nested inside pre-registered bin boundaries, not a post-hoc exploratory scan. Multiplicity is controlled within each bin via nested Holm-Bonferroni; cross-bin claims additionally require joint-34 Holm sensitivity support (§8.8)."

### 13.1 Bin-level Shapley decomposition (secondary — robustness on 4-bin LOO)

**Purpose**: check whether the 4-bin LOO ranking is robust to feature-bin interactions that LOO (a marginal-effects estimator) cannot capture.

**Algorithm**: enumerate all 2⁴ = 16 conditions (include/exclude each of the 4 bins). Compute respondent-macro Likert MAE under each condition. Shapley value for bin B = average of `MAE(coalition without B) − MAE(coalition ∪ {B})` over all 8 coalitions not already containing B. Output schema in `tier1_tool_schemas.md`.

**When run**: Phase 1a (N=200, on the N=100 selection split per §12.2), once per cheap-panel model. Optionally re-run on Phase 1b selected model.

**Reporting role**: **robustness re-aggregation of the same primary 4-bin estimand**, not a separate confirmatory family. The 4-bin Shapley values + their interaction terms are reported alongside the LOO ΔMAE as evidence of robustness. No separate Holm correction (shares the 4-bin family).

**Why Shapley does NOT extend to batteries**: 2³⁴ ≈ 17 billion coalitions on 34 batteries; even sampled Shapley would produce 561 pairwise interaction terms that are uninterpretable. Battery LOO operates as a marginal estimator (R1 already isolates each battery's contribution from same-construct redundancy); interaction-aware battery analysis is deferred to future work.

**Anti-overclaim**: Shapley is a decomposition tool, NOT a "new theory engine." We do not interpret 2-way / 3-way interaction terms as theoretical findings unless they survive bootstrap CI; they are reported as descriptive numbers with their CIs. **We do not call any custom variance-share statistic "Friedman's H"** unless we explicitly implement Friedman & Popescu (2008)'s definition; we use a clearly-named non-standard metric (`interaction_variance_share`) defined in the schema.

### 13.2 Battery LOO (co-primary — mechanistic across all 4 bins, locked 2026-05-09 evening)

**Purpose**: identify which **construct-level clusters** within each feature bin drive LLM persona prediction. This is the mechanistic complement to the 4-bin LOO's broad finding.

**Scope**: all 34 batteries across all 4 bins (per `gss_battery_map.json` v0.2: 7 demographic + 10 behavioral + 2 psychological + 15 attitudinal). **Singletons are NOT tested in Battery LOO** (variable-level LOO has too low statistical power; they are absorbed into the 4-bin LOO via their parent bin). **Unconditional run** (no longer gated on attitudinal-bin dominance).

**Battery design principles** (from `gss_battery_map.json` v0.2):
- A battery groups variables that measure the same underlying construct closely enough that LOO must drop them together — otherwise residual same-construct siblings fill the signal back in and undercount the construct's contribution.
- SPLIT criterion: when sub-construct, target group, time point, or response scale differs sufficiently to conflate distinct signals (mirrors civil_liberties' 3-way split by target group).
- Symmetry across all 4 bins prevents asymmetric leakage hygiene where attitudinal is fine-grained but other bins are coarse.

**Algorithm**: for each of the 34 batteries B, drop the entire battery from the persona prompt for ALL 12 primary_eval items (in addition to R1's per-item battery exclusion which already applies — these are independent operations). Re-run prediction; compute respondent-macro Likert ΔMAE vs FULL. Bootstrap CI at respondent level **(B=10000, seed=42, BCa via scipy with percentile fallback — locked 2026-05-09 night per Codex N5/N6 audit)**. Apply **nested Holm-Bonferroni primary** within each bin's battery family + **joint-34 Holm sensitivity** for cross-bin claims (see §8.8).

**Estimand clarification (locked 2026-05-09 evening)**: because R1 already excludes the predicted item's own battery for each primary_eval item, Battery LOO estimates **cross-construct predictive contribution after direct same-construct leakage is already blocked** — i.e., how much removing battery B *additionally* harms prediction of held-out primary_eval items relative to the FULL condition (which already has the predicted item's own battery R1-excluded). It does **not** estimate the raw self-predictive value of a battery. Concretely:
- Battery LOO does NOT estimate causal importance of a construct.
- Battery LOO estimates **predictive dependence** of the held-out primary_eval items on a battery, **under a fixed prompt-construction procedure** (R1 + the locked persona prompt template).
- Battery LOO is sensitive to battery size, item coverage (GSS ballot rotation), and prompt-design choices — these are reported alongside ΔMAE.

**When run**: Phase 1c (post Phase 1b headline) on the §12.2-selected 1b model only. **Honest budget (locked 2026-05-09 night per Audit-3 + Joyce decision; supersedes earlier ~$218 estimate which assumed N=1,500)**: 34 batteries × 12 items × **3,309 respondents** × 1 model × 1 sample = **~1,350,000 calls × ~$0.000356/call ≈ ~$481 incremental**. See §5 for the full Phase 1 budget (~$756 total under Option A: cheap panel primary-only; sensitivity_eval anchor-only).

**Reporting role**: **co-primary mechanistic finding**, equal prominence to 4-bin LOO in the abstract. The paper reports both:
- Headline #1 (broad): "[Bin] contributes the most to attitude prediction" + Shapley robustness
- Headline #2 (mechanistic): "Within each bin, the following batteries are Holm-significant: ..." + per-bin family-significant ΔMAE table

**Anti-overclaim** (locked 2026-05-09 evening):
- **Within-bin claims** use nested Holm only and are confirmatory.
- **Cross-bin claims** ("battery X is the strongest battery overall") require joint-34 Holm sensitivity support (§8.8). Without joint-34 support, cross-bin language must be descriptive (e.g., "rank-ordered" rather than "significantly stronger").
- **Practical-effect threshold gate** (§8.9): a battery is reported as substantively meaningful only if Holm-significant AND practical-effect ≥ "modest" (ΔMAE ≥ 0.02) with bootstrap CI excluding the small-effect boundary. Statistical significance alone is insufficient.
- Battery size is unbalanced (2-15 items per battery); ΔMAE magnitudes are reported alongside `n_items_in_battery` and `delta_mae_per_item` for size-aware interpretation. `delta_mae_per_item` is a descriptive sensitivity column, NOT the primary inferential metric. **Documented trade-off (locked 2026-05-09 night per Codex M3)**: bare ΔMAE has a size-toward-larger-batteries confound; per-item ΔMAE has a variance-toward-smaller-batteries confound. There is no clean primary metric that escapes both. We report **both metrics with the explicit `n_items_in_battery` size column** so readers can apply whichever framing fits their substantive question. The headline Holm-significance test runs on bare ΔMAE because it has the better statistical-power profile at this N; per-item ΔMAE is reported as a robustness column in every results table.

**Output schema** in `tier1_tool_schemas.md` Tool 2 — includes `p_holm_within_bin`, `p_holm_joint_34`, `holm_significant_within_bin`, `holm_significant_joint_34`, `effect_size_label`, and `n_items_in_battery` / `delta_mae_per_item`.

### 13.3 Theory interpretation (Discussion section only)

The 4-bin taxonomy is atheoretical — a sorting convention, not derived from cognitive theory. After the primary results are in, the paper's Discussion section situates the empirical pattern in relation to existing cognitive and sociological frameworks (see `theory_interpretation_guide.md`).

**Critical preregistration commitment**: theory interpretation is **secondary and explanatory**. The primary findings (4-bin LOO rankings, Shapley decomposition, attitudinal battery LOO) do NOT depend on which theory aligns most closely with the data. Specifically:

- The headline in the abstract is stated in atheoretical engineering terms (e.g., *"attitudinal features dominate, with within-bin contribution concentrated in [batteries]"*).
- Theory framing enters one Discussion subsection labeled clearly as interpretive secondary analysis.
- We do NOT preregister a horse race that would let one theory "win."
- We do NOT make the abstract claim "LLM persona representation aligns with [Theory X]."
- **Null or mixed theoretical alignment will be reported honestly** — if no framework cleanly explains the empirical pattern, the Discussion says so without distortion.

**What we DO commit to** (anti-HARKing on the secondary):
1. Listing candidate frameworks (MFT / Schwartz / Bourdieu / Cultural Theory / Inglehart-Welzel / Big Five) BEFORE seeing Phase 1a results, in `theory_interpretation_guide.md`.
2. Stating each framework's broad expected pattern (which bin / battery should dominate) at a coarse level — to prevent post-hoc cherry-picking among them.
3. Reporting the alignment qualitatively, NOT through preregistered numeric thresholds that would convert this into a confirmatory horse race.

**What we explicitly DO NOT commit to**:
- Hard Spearman ρ thresholds per theory.
- A "Stage 3 refinement" experiment (deferred to future work; see §13.4).
- Theory-bin LOO as a confirmatory family (deferred; see §13.4).
- Any abstract claim that theory wins or aligns.

### 13.4 Deferred to future work

The following analyses were considered for Phase 1 but **explicitly deferred**. They may appear as future-work bullet points in the paper's Discussion or as optional appendix material, but are NOT in the primary OSF pre-registration:

- **Theory-bin LOO as confirmatory family** (re-aggregating LLM outputs under a locked theoretical grouping; would require `gss_theory_taxonomy.json` lock + OSF amendment)
- **Representational Similarity Analysis (RSA)** (theory-derived similarity matrices vs LLM-output similarity)
- **Permutation importance theory adjudication** (per-(item, var) importance from R2 baseline used to rank theories)
- **Stage 3 refinement experiments** (theory-organized prompts; counterfactual perturbation; theory-derived feature subsets)
- **Six-theory horse race with hard numeric thresholds**
- **Friedman & Popescu (2008) H-statistic** (proper implementation; the slimmed design uses a clearly-named non-standard `interaction_variance_share` instead)
- **Sampled Shapley on 34 batteries** (2³⁴ ≈ 17 billion exact coalitions infeasible; sampled Shapley would produce 561 uninterpretable pairwise interaction terms; deferred until a future paper specifically targeting battery-battery interaction structure)
- **Variable-level LOO** (per-variable single-drop within each battery; variable-level statistical power too low at N=3309 with 140 features × multiplicity correction; deferred to a future paper with N≥5000)
- **Singleton-level LOO testing** (the 17 singletons in `gss_battery_map.json` are not tested as Battery LOO units — testing each as a 1-variable "battery" would inflate multiplicity without comparable statistical power; their contribution is absorbed into the 4-bin LOO via parent bin)

These are listed here so future Joyce + Bayati discussions know what was considered and explicitly chosen against.

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
