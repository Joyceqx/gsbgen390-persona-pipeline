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
   - **Phase 1a (N=100)**: 4 cheap OpenRouter models from the locked panel (Qwen-2.5-72B / DeepSeek-V3.1 / MiniMax-M1 / Kimi K2), n_samples=1 each, temperature=0.7 → 4 codes per (respondent, condition, item).
   - **Phase 1b (N=1500)**: ONE model selected via the §12.2 quality-primary rule (lowest 1a Likert MAE among DQ-passers, cost as tie-break), n_samples=1, temperature=0.7.
   - **Anchor (N=100 subset of 1b)**: GPT-4o, primary conditions only, n_samples=2, temperature=0.7. The anchor preserves Park-comparable per-item accuracy AND restores within-model self-consistency on the directly-comparable subset.

5. **Sensitivity pass (Path A, Park-comparable)** — only on the selected 1b model + anchor: for each of the ~118 sensitivity-eval items X, build a persona prompt from the full feature set MINUS X (per-item exclusion to prevent direct leakage), predict X, score.

6. **Score each (respondent, condition, model, item, sample)** via the rules locked in AUDIT-C (`gss_pipeline.py`):
   - Likert items (likert3-7): absolute error vs. truth code
   - Binary / categorical items: exact match
   - PARTYID contingent: Likert on 0-6, categorical when either side outputs 7

7. **Aggregate** per §10 (respondent-macro primary; bootstrap CIs at respondent level B=1000; LOO ΔMAE via paired bootstrap). Multi-model panel synthesis per §12 (median for Likert, mode for categorical, with `_panel_aggregate_code`).

**Primary metrics — raw, NOT normalized**:
- **Likert MAE** (mean absolute error on Likert items)
- **% within ±1** (fraction of Likert items where persona is within 1 scale point of truth)
- **Categorical exact-match accuracy**

**Stability QA metric**:
- Phase 1a / 1b cheap-panel: **cross-model agreement %** (strict — all expected models present + parsed + identical for that tuple). Replaces within-model self-consistency.
- GPT-4o anchor subset: **within-model self-consistency** (n_samples=2, % of items where both samples gave the same code). Restored only here because the anchor is run with n=2.

**Phase 1 does NOT compute test-retest-normalized accuracy.** Park's 0.82/0.83 are normalized against a 2-week recontact baseline that GSS does not provide. We report raw metrics only and avoid direct numerical comparison to Park's normalized headline.

## 5. Sample size, budget, timeline

The N=1,500 sample is drawn from the 3,309 GSS 2024 respondents. Sampling rule (pre-registered): random sample without replacement, **fixed seed = 42**, no oversampling on demographics. The same seed governs the bootstrap CI (B=1000, seed=42) and the paired-bootstrap LOO ΔMAE. Optional weighted reanalysis using GSS sampling weights as a robustness check (see §10).

**Seed reproducibility (Codex I-10)**: every output artifact (ndjson, summary JSON, plots) MUST encode the seed in its filename suffix (e.g., `phase1a_panel_seed42.ndjson`). The driver emits a `WARNING` to stderr when the runtime seed is anything other than 42, and refuses to overwrite a seed-42 artifact with a non-42 run unless `--force-non-canonical-seed` is passed. This guards against silent reproducibility drift if a future contributor changes the seed.

**Two-stage model strategy** (locked 2026-05-06; see §12 for the multi-model-then-single rationale):
- **Phase 1a (N=100)**: run all 4 cheap OpenRouter models in parallel + GPT-4o anchor. Use this as a model-selection step under a pre-registered criterion.
- **Phase 1b (N=1500)**: run the single cheap model selected by the Phase-1a criterion + GPT-4o anchor on N=100 subset. The other 3 cheap models are NOT carried forward to 1b.

| Sub-phase | N | LLM calls per respondent | Cost / respondent | Total budget |
|---|---|---|---|---|
| Smoke | 10 | ~712 (primary + sensitivity, 4 cheap, n=1) | ~$0.24 | **~$2-3** |
| 1a — sanity + model selection | 100 | ~712 × 4 cheap models + 60 × GPT-4o = ~3000 | ~$0.65 | **~$65** |
| 1b — primary | 1,500 | ~712 (1 selected cheap model only, n=1) | ~$0.06 | **~$95** |
| 1b GPT-4o anchor | 100 (subset of 1b) | 60 (primary only, n=2) | ~$0.50 | **~$50** |
| **Total Phase 1** | | | | **~$215** |

Roughly halves the previous $440 budget (which assumed all-4-cheap-models for the full 1b run). The savings (~$225) are reserved for Phase 1c — the theory-driven secondary analysis (§13) — and any post-hoc concurrency / robustness extensions.

**Cost estimate caveats**: (a) per-token rates above are May-2026 OpenRouter approximations and must be verified at smoke-test time before scaling. (b) These estimates assume **no prompt caching** (the persona prompt repeats across the 12 items × 2 samples within a (respondent, condition); caching would discount input tokens by ~50%). Implementing prompt caching is deferred but could halve costs further if needed.

Wall-clock: smoke in 1-2 hours; 1a in ~1 day at sequential rates (~10 min / respondent × 4 models); 1b in 3-5 days (single-model is much faster). Concurrency (ThreadPoolExecutor for parallel model calls) bumps this 4× faster on 1a; flagged but not implemented yet.

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
7. **Pre-registration on OSF before Phase 1a.** The pre-reg (filed *before* 1a fires) locks: taxonomy, primary + sensitivity eval sets, primary metric, exclusion rules (R1 battery exclusion + sensitivity per-item exclusion), R2 regression-baseline partition, the 4-cheap-model panel, the §12.2 quality-primary selection rule, the §10 aggregation + paired-bootstrap rules, **two co-primary analyses** — the **4-bin LOO** (broad feature-category attribution) and the **34-battery LOO across all 4 bins** (mechanistic cluster-level attribution) — the **bin-level Shapley decomposition** as 4-bin LOO robustness, and the §11.1 writeup language template. No post-hoc adjustment of the 4-bin assignments OR the battery map (`gss_battery_map.json` v0.2) after 1a fires.

8. **Multiplicity / multiple-LOO control (nested Holm-Bonferroni; revised 2026-05-09 for co-primary Battery LOO).**
   - **4-bin primary family** (4 ΔMAE tests): Holm-Bonferroni at α=0.05 within family. Adjusted-significant findings reported as "primary headline #1"; unadjusted bin contributions reported descriptively.
   - **Battery LOO co-primary** uses **nested Holm-Bonferroni** — one Holm family per bin, applied independently:
     - Demographic battery family (n=7): smallest p < α/7 = 0.0071
     - Behavioral battery family (n=10): smallest p < α/10 = 0.0050
     - Psychological battery family (n=2): smallest p < α/2 = 0.025
     - Attitudinal battery family (n=15): smallest p < α/15 = 0.0033
   - Nested (rather than joint Holm across all 34) is principled because (a) bin is a meaningful pre-registered boundary; (b) joint Holm at n=34 would force the psychological 2-battery family to clear α/34 = 0.0015, which is impractical and would silence a pre-registered analysis arm.
   - **Bin-level Shapley** (16 conditions) is a *robustness re-aggregation* of the same 4-bin estimand; no separate multiplicity correction (it shares the 4-bin primary family).
   - **Theory-bin LOO is NOT a confirmatory family.** Theory framing enters the Discussion section as interpretive secondary analysis only (see §13.3). If a future amendment adds theory-bin LOO as a confirmatory family, that amendment will introduce its own Holm correction at that time.

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
3. **Layer 3 — R1 (battery-level structural exclusion, NEWLY ENFORCED 2026-05-08)**: when predicting any primary_eval item that belongs to a battery (per `gss_battery_map.json` v0.1, 15 batteries + 9 singletons), the entire battery is dropped from the persona prompt for that prediction. Mirrors Park v2's BFI whole-trait-block hold-out (Park v2 SI §5, PDF p.37: *"For the Big-5 we always hold-out the whole block of questions asking about a particular personality trait when predicting an outcome question within that trait"*). Implemented in `run_primary_one_respondent` and validated by `validate_taxonomy.py` check 7c.
4. **Layer 4 — R2 (regression-baseline partition, NEWLY ADDED 2026-05-08)**: alongside the LLM panel, run a non-LLM regression baseline (`regression_baseline.py`: Ridge for Likert, multinomial Logistic for binary, 5-fold CV at the respondent level, same R1 battery exclusion applied symmetrically). The regression's per-item MAE is the "auto-correlation upper bound" any feature-to-item predictor can extract from the same input. The headline partition becomes:
   - LLM-panel MAE on item X = (regression MAE on X) + (LLM gain over regression)
   - The first term is pure auto-correlation; the second is the persona-reasoning contribution.
   - This is methodologically a step *past* Park v2: Park brackets the inflation between two hold-out strategies (single-item gives 0.82, whole-module gives 0.77 — Park v2 SI §6, PDF p.39 *"average normalized accuracy of 0.77 (std = 0.12)"* under whole-module hold-out vs *"0.82 (std = 0.18)"* under single-item); we partition it by introducing a regression comparator the same input pool can produce.

**R3 (whole-attitudinal-bin Park-strict reanalysis) was considered and explicitly NOT IMPLEMENTED** (decision 2026-05-08): R3 would globally remove every variable in any primary_eval battery from the attitudinal bin before any LOO ran, leaving an artificially-thin bin. Joyce's call: R1 already provides per-item structural exclusion at the right granularity (the predicted item's own battery, not all batteries), and R3 would conflate two effects (battery-level redundancy + bin-level information capacity), making the LOO ranking uninterpretable. R1 + R2 together provide the structural defense (R1) and the partition test (R2) that R3 was meant to triangulate.

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
- "Attitudinal features dominate human-simulation fidelity" — they may dominate due to within-domain auto-correlation; with R1 + R2 in force we can quantify this, but the result remains GSS-attitude-prediction-internal, not a fidelity claim.
- "Demographics don't matter for personas" — we measure demographics' contribution within GSS-attitude prediction, not their general informativeness for BFI personality or behavioral games.
- Generalization to BFI personality or behavioral games — Phase 2 only.
- "Robust across LLM families" — the 4 cheap-panel models are all China-trained (Qwen / DeepSeek / MiniMax / Kimi); the cross-family claim is restricted to "across four China-trained instruction-tuned models in a 100-respondent comparison" and does NOT apply to the N=1500 Phase 1b headline (which runs on a single quality-selected model). Cross-Western/Eastern robustness lives only on the GPT-4o anchor (N=100 subset).

These constraints carry over into the abstract, headline figures, and reviewer-facing claims of the Phase 1 writeup.

### 11.1 Writeup language template (locked 2026-05-08, per §3.3 + §3.4 audit)

The following sentence-level constraints are **mandatory** in any Phase 1 abstract, headline figure, or reviewer-facing summary:

| Constraint | Required form | Forbidden form |
|---|---|---|
| "Persona fidelity" qualifier | "within-wave attitudinal prediction" / "single-wave GSS attitudes" | bare "persona fidelity" |
| Cross-model robustness scope | "across four China-trained instruction-tuned models in a 100-respondent comparison" | bare "across LLM families" |
| Headline-N model identity | "the {selected_model} reported under the §12.2 quality-primary rule, N=1500" | "the cheap panel" / "the LLM panel" |
| Park comparison anchor | "the GPT-4o anchor on the N=100 subset, with single-item hold-out matching Park v2 SI §6" | "matches Park's 82%" |
| Auto-correlation framing | "after R1 battery-level exclusion and R2 regression-baseline partition" | bare "after leakage hygiene" |
| Test-retest claim | (none — say nothing about test-retest) | "normalized accuracy" / "fidelity" |

The abstract and the dashboard / GitHub Pages footer must each be checked against this table before submission. A reviewer who sees a violation immediately recognizes the over-claim — preventing this is what §11.1 exists for.

## 12. Multi-model panel design (locked 2026-05-05)

### Rationale

GPT-4o-only Phase 1 would cost ~$900 at N=1500, exceeding the $300-500 budget. More importantly, single-model results conflate "feature-category contribution" with "GPT-4o-specific quirks" — a reviewer could plausibly reject "X is the most predictive feature category" with "but maybe only on GPT-4o."

**Solution**: query the same persona prompts on a **panel of 4 cheap, diverse OpenRouter-available models** as the primary analysis. The headline finding becomes "feature-category contribution to GSS-attitude prediction is robust **across LLM families**" — a stronger claim than single-model GPT-4o.

A small GPT-4o anchor on a 100-respondent subset preserves direct Park v2 Table 3 comparability without blowing budget.

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
- **GPT-4o anchor**: per-item raw accuracy table on N=100 subset, side-by-side with Park v2 Table 3.
- **Cross-model agreement**: % of (respondent, item, condition) tuples where all 4 cheap models output the same integer code. Reported as the new "consistency QA metric" replacing within-model self-consistency.

### What the writeup must say (extension to §11 constraints)

- "Our headline is the panel median of 4 models (Qwen, DeepSeek, MiniMax, Kimi). Per-model results are in the supplementary."
- "Direct comparability to Park v2 Table 3 is via the N=100 GPT-4o anchor subset, not via the cheap-model panel. The cheap-model panel addresses generalization across LLM families; the anchor addresses model-comparability with the established benchmark."
- "Cross-model agreement at temperature 0.7 (4 cheap models on the same item) is reported as a stability QA metric in lieu of within-model self-consistency. The two are different concepts."

### Pre-registration must declare

Before Phase 1a launches the OSF pre-reg locks:
- The exact 4-cheap-model list for Phase 1a (prevents post-hoc cherry-picking)
- The model-selection rule from 1a → 1b (locked below in §12.2)
- The GPT-4o anchor scope (N=100 subset, primary conditions only, n_samples=2)
- Aggregation method (per-model + panel median/mode + cross-model agreement)
- Cross-model agreement metric definition (strict: all expected models present + parsed + identical)

### §12.2  Locked model-selection rule (Phase 1a → Phase 1b) — quality-primary

After Phase 1a (N=100) completes for all 4 cheap models, Phase 1b is run on the single cheap model that minimizes **respondent-macro Likert MAE on the Phase 1a primary_eval items, full condition only** — i.e., the model whose persona predictions are most accurate on the headline metric of the paper.

```
primary_score(model) = respondent_macro_Likert_MAE_on_1a_primary_full
                       (parse-failed items excluded from the per-respondent average;
                        a respondent contributes only if they have ≥1 valid Likert item)
choose argmin
```

**Why quality-primary, not cost-primary** (locked decision 2026-05-06): the 4-cheap-panel members differ in per-call cost by at most ~2× (~$50-80 swing on the entire N=1500 1b run), but can differ in MAE by considerably more. Optimizing the selection criterion on a $50 axis when the *paper's headline metric is MAE* is internally inconsistent — the rule should pick the model that is best at the thing the paper measures. Cost is preserved as a tie-break, not as the primary score.

**Pre-registered guard rails (all locked in OSF before Phase 1a fires):**

1. **DQ-1 — Parse-failure ceiling.** Any model with `parse_failure_rate_on_1a > 0.30` is removed from the candidate set BEFORE quality scoring. Rationale: a model that parse-fails on >30% of items is operationally unusable at scale regardless of its measured MAE on the parsed remainder.

2. **DQ-3 — Mode-collapse guard (per-item relative threshold; revised 2026-05-08 per audit §3.9).** For each of the 12 primary_eval items, the model's output-code population variance across respondents must satisfy `var(model_i) ≥ 0.30 × var(human_i)`, where `var(human_i)` is the locked GSS 2024 per-item human variance (computed once from `outputs/primary_eval_human_variance_2024.json`, OSF-pre-registered). A model is disqualified if **more than 50% of items fail** this floor — i.e., a majority of items show output collapse relative to the empirical human distribution. Rationale: an absolute threshold (e.g., 0.5) is too lenient on heavily-skewed items where human variance itself is < 0.5 (FEPOL = 0.15, GUNLAW = 0.21, FEPOL is 82/18 split) and too strict on widely-spread items (PARTYID human variance = 4.24). The relative threshold scales with the empirical human distribution per item; 30% is the OSF-pre-registered floor (chosen because (a) a perfectly-calibrated LLM can plausibly run at ~50-100% of human variance, so 30% gives substantial headroom; (b) a mode-collapsed LLM with single-mode output has variance 0% of human; the 30% line cleanly separates the two regimes per the §12.2.1 simulation table).

3. **Tie-break — cost.** Among models within **5% of the best primary_score** (i.e., `MAE_model ≤ 1.05 × MAE_best`), select the one with the **lowest `cost_per_call_USD × (1 + parse_failure_rate)`** score. Rationale: when quality is statistically indistinguishable, the cost-pre-registered framing of the cheap panel still informs the choice.

4. **Deterministic fallback — Qwen-2.5-72B-Instruct.** If after DQ-1 + DQ-3 the candidate set is empty (all 4 models failed gates), OR ≥2 candidates tie on both quality (within 5%) AND cost (within 1%), **Qwen-2.5-72B-Instruct** is used. Reason: it is the most stable instruction-following baseline of the four and is the panel's documented "default" provider. The OSF pre-reg names Qwen explicitly so there is no post-hoc judgment.

**Why each guard rail**:
- DQ-1 prevents picking a parse-broken model that scored a fluke MAE on its small parsed subset.
- DQ-3 is the critical anti-cheat. Without it, a model that always outputs "4" on every item would beat a model that genuinely tries to predict each respondent — because most GSS attitudes cluster centrally and "always 4" has lower MAE than calibrated guesses on outliers. With DQ-3, mode-collapsed models are filtered out before the quality comparison.
- Cost as tie-break (not primary) preserves the budget framing in the noise-equivalent regime without letting it override a real quality difference.
- Qwen fallback ensures the rule is fully deterministic and OSF-eligible — no judgment call required after 1a completes.

**The selection rule in one sentence (for the abstract / writeup):**
> "We selected the Phase 1b model as the lowest-MAE Phase 1a candidate among models passing pre-registered parse-failure (≤30%) and per-item relative-variance gates (`var(model_i) ≥ 0.30 × var(human_2024_i)` for ≥50% of primary_eval items); cost served as a within-5% tie-break, with Qwen-2.5-72B-Instruct as the named fallback."

**Scope** — Phase 1b reports remain valid as "predictive findings on the quality-selected model." Multi-model robustness is established by the 1a comparison itself (published alongside 1b). The thesis claim becomes:
> "On Phase 1a (N=100, 4 cheap models), feature-category contribution rankings agreed within bootstrap noise across all 4 models. We selected {model_X} for Phase 1b under the §12.2 quality-primary criterion (with parse-failure and mode-collapse gates, cost tie-break, and Qwen fallback); the N=1500 results on {model_X} are reported alongside the 1a multi-model robustness panel."

This is honest, internally consistent with the paper's primary metric, and avoids the cherry-picking objection.

**History note**: an earlier draft (2026-05-06 morning) proposed a cost-primary rule with quality as tie-break. That was reconsidered the same day after recognizing that the 4-cheap-panel cost spread is too narrow to dominate over typical quality differences, and that selecting on a metric different from the paper's headline metric creates an internal inconsistency that reviewers will flag. The cost-primary alternative is preserved in version-control history but is NOT what the OSF pre-reg locks.

---

## 13. Secondary analyses (locked 2026-05-09 lean → 2026-05-09 evening: Battery LOO promoted to co-primary)

**Design philosophy** (locked 2026-05-09 evening): the paper has TWO co-primary contributions:
1. **Broad finding** (4-bin LOO): which feature category contributes most to LLM persona prediction of attitude outcomes?
2. **Mechanistic finding** (34-battery LOO across all 4 bins, nested Holm): which specific construct-level clusters drive the signal within each bin?

Bin-level Shapley is robustness on the broad finding. Theory interpretation enters Discussion only.

### 13.1 Bin-level Shapley decomposition (secondary — robustness on 4-bin LOO)

**Purpose**: check whether the 4-bin LOO ranking is robust to feature-bin interactions that LOO (a marginal-effects estimator) cannot capture.

**Algorithm**: enumerate all 2⁴ = 16 conditions (include/exclude each of the 4 bins). Compute respondent-macro Likert MAE under each condition. Shapley value for bin B = average of `MAE(coalition without B) − MAE(coalition ∪ {B})` over all 8 coalitions not already containing B. Output schema in `tier1_tool_schemas.md`.

**When run**: Phase 1a (N=100), once per cheap-panel model. Optionally re-run on Phase 1b selected model.

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

**Algorithm**: for each of the 34 batteries B, drop the entire battery from the persona prompt for ALL 12 primary_eval items (in addition to R1's per-item battery exclusion which already applies — these are independent operations). Re-run prediction; compute respondent-macro Likert ΔMAE vs FULL. Bootstrap CI at respondent level (B=1000, seed=42). Apply **nested Holm-Bonferroni** within each bin's battery family (see §8.8).

**When run**: Phase 1c (post Phase 1b headline) on the §12.2-selected 1b model only. ~34 batteries × N=1500 × 12 items × 1 model ≈ ~$50-60 incremental (up from ~$25-30 of the previous attitudinal-only conditional design).

**Reporting role**: **co-primary mechanistic finding**, equal prominence to 4-bin LOO in the abstract. The paper reports both:
- Headline #1 (broad): "[Bin] contributes the most to attitude prediction" + Shapley robustness
- Headline #2 (mechanistic): "Within each bin, the following batteries are Holm-significant: ..." + per-bin family-significant ΔMAE table

**Anti-overclaim**:
- Battery size is unbalanced (2-15 items per battery); ΔMAE magnitudes are reported alongside battery size to enable size-aware interpretation. Per-variable mean importance (ΔMAE / n_items_in_battery) is reported as a sensitivity column.
- Holm correction is per-bin (nested), so cross-bin comparisons of "which battery overall ranks highest" are descriptive only, not confirmatory.

**Output schema** in `tier1_tool_schemas.md` Tool 2.

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
- **Variable-level LOO** (per-variable single-drop within each battery; variable-level statistical power too low at N=1500 with 140 features × multiplicity correction; deferred to a future paper with N≥5000)
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
