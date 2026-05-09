# Phase 1 — GSS Public-Data Feature-Importance Analysis

**Author:** Joyce Yu
**Course:** GSBGEN390 / thesis prep · Prof. Mohsen Bayati
**Status:** Locked 2026-05-02; audit-fix revisions 2026-05-05 → 2026-05-06 (this version frozen pending OSF pre-registration sign-off **before Phase 1a launches** — pre-reg locks the model panel, the §12.2 selection rule, and dual-headline aggregation; Phase 1a's results then feed §12.2 to pick the Phase 1b model)
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
7. **Pre-registration on OSF before Phase 1a — staged.** The initial pre-reg (filed *before* 1a fires) locks: taxonomy, primary + sensitivity eval sets, primary metric, exclusion rules, the 4-cheap-model panel, the §12.2 quality-primary selection rule, the §10 aggregation + paired-bootstrap rules, and the **4-bin LOO** as the lock-ready primary analysis. No post-hoc adjustment of the 4-bin assignments after 1a fires.

   **The theory-bin LOO (§13) is NOT in the initial pre-reg.** It enters via a pre-reg amendment, filed *before any 1c re-aggregation runs*, once Joyce's literature review has locked a theory and the variable→cluster mapping is committed in `gss_theory_taxonomy.json`. Until that amendment is filed, the theory-bin LOO is exploratory.

8. **Multiplicity / multiple-LOO control.**
   - The 4-bin primary family has 4 ΔMAE tests. **Holm-Bonferroni at α=0.05** is applied within this family. Adjusted-significant findings are reported as "primary"; unadjusted bin contributions are reported descriptively.
   - The theory-bin LOO (when activated via the §13 amendment) constitutes a separate, secondary family of ~5-10 ΔMAE tests; Holm-Bonferroni is applied within it independently. The theory-bin family is always reported as a *secondary confirmation*, not as a co-primary headline, even after the amendment.
   - Until the §13 amendment is filed, **only the 4-bin primary multiplicity rule is in force.** No theory-bin tests are reported during the initial Phase 1a/1b primary writeup.

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

2. **DQ-3 — Mode-collapse guard.** Any model whose **per-item output-code variance** averaged across the 12 primary_eval items is `< 0.5` is removed. Rationale: a model that constantly outputs the same modal code (e.g., always "4" on a Likert-7) trivially achieves a low MAE on a centrally-distributed sample — DQ-3 catches this without requiring a comparator. The 0.5 floor is calibrated against the GSS 2024 *human* per-item variance, which is typically >1.0 on contested items; a model below 0.5 is producing degenerate output, not a calibrated prediction.

3. **Tie-break — cost.** Among models within **5% of the best primary_score** (i.e., `MAE_model ≤ 1.05 × MAE_best`), select the one with the **lowest `cost_per_call_USD × (1 + parse_failure_rate)`** score. Rationale: when quality is statistically indistinguishable, the cost-pre-registered framing of the cheap panel still informs the choice.

4. **Deterministic fallback — Qwen-2.5-72B-Instruct.** If after DQ-1 + DQ-3 the candidate set is empty (all 4 models failed gates), OR ≥2 candidates tie on both quality (within 5%) AND cost (within 1%), **Qwen-2.5-72B-Instruct** is used. Reason: it is the most stable instruction-following baseline of the four and is the panel's documented "default" provider. The OSF pre-reg names Qwen explicitly so there is no post-hoc judgment.

**Why each guard rail**:
- DQ-1 prevents picking a parse-broken model that scored a fluke MAE on its small parsed subset.
- DQ-3 is the critical anti-cheat. Without it, a model that always outputs "4" on every item would beat a model that genuinely tries to predict each respondent — because most GSS attitudes cluster centrally and "always 4" has lower MAE than calibrated guesses on outliers. With DQ-3, mode-collapsed models are filtered out before the quality comparison.
- Cost as tie-break (not primary) preserves the budget framing in the noise-equivalent regime without letting it override a real quality difference.
- Qwen fallback ensures the rule is fully deterministic and OSF-eligible — no judgment call required after 1a completes.

**The selection rule in one sentence (for the abstract / writeup):**
> "We selected the Phase 1b model as the lowest-MAE Phase 1a candidate among models passing pre-registered parse-failure (≤30%) and output-variance (≥0.5) gates; cost served as a within-5% tie-break, with Qwen-2.5-72B-Instruct as the named fallback."

**Scope** — Phase 1b reports remain valid as "predictive findings on the quality-selected model." Multi-model robustness is established by the 1a comparison itself (published alongside 1b). The thesis claim becomes:
> "On Phase 1a (N=100, 4 cheap models), feature-category contribution rankings agreed within bootstrap noise across all 4 models. We selected {model_X} for Phase 1b under the §12.2 quality-primary criterion (with parse-failure and mode-collapse gates, cost tie-break, and Qwen fallback); the N=1500 results on {model_X} are reported alongside the 1a multi-model robustness panel."

This is honest, internally consistent with the paper's primary metric, and avoids the cherry-picking objection.

**History note**: an earlier draft (2026-05-06 morning) proposed a cost-primary rule with quality as tie-break. That was reconsidered the same day after recognizing that the 4-cheap-panel cost spread is too narrow to dominate over typical quality differences, and that selecting on a metric different from the paper's headline metric creates an internal inconsistency that reviewers will flag. The cost-primary alternative is preserved in version-control history but is NOT what the OSF pre-reg locks.

---

## 13. Theory-driven feature engineering (Phase 1c — pending literature lock)

The 4-bin taxonomy (demographic / behavioral / psychological / attitudinal) is **atheoretical** — it's a sorting convention, not derived from any cognitive or behavioral-science theory. To strengthen the paper's theoretical contribution, Phase 1 will additionally run a **theory-driven secondary LOO analysis** alongside the atheoretical primary.

### Status — NOT LOCK-READY

⚠️ **§13 is NOT lock-ready as of 2026-05-06.** It cannot be in the OSF pre-registration in its current form because the theory has not yet been chosen. Joyce is conducting the literature review (`theory_review.md`) to pick one of: Moral Foundations Theory, Schwartz's Universal Values, Bourdieu's Capitals, or Cultural Theory of Risk. Once a theory is selected, the variable→cluster mapping is locked in `gss_theory_taxonomy.json`, and §13 becomes lock-eligible.

**Pre-reg sequencing**:
- The atheoretical 4-bin LOO (§§4–12) IS lock-ready and can go to OSF immediately.
- §13 requires either (a) Joyce's theory pick + mapping JSON before pre-reg, OR (b) §13 being explicitly listed in the OSF pre-reg as "exploratory secondary analysis to be specified in a pre-reg amendment before any 1c re-aggregation runs."
- Default: option (b) — file the OSF pre-reg now with the 4-bin primary locked, and amend with the locked theory mapping before Phase 1c re-aggregation.

🔒 **Pending Joyce's literature review** (deliberate). Candidate theories surveyed in `theory_review.md`; the chosen theory's mapping to GSS items will be locked in `gss_theory_taxonomy.json` before Phase 1c re-aggregation runs.

### What this adds

After the 4-bin LOO produces the atheoretical primary headline, **the same persona prompts and the same eval items** will be re-aggregated under a theoretically-grounded grouping (e.g., Moral Foundations Theory's 5-6 foundations, or Schwartz's 10 universal values, or Bourdieu's 3 capitals). The same LOO ablation runs against the new groups.

### Why this matters for the paper

- The 4-bin LOO answers an engineering question: *which arbitrary feature category contributes most?*
- The theory-driven LOO answers a psychological question: *which theoretical construct best organizes the input that drives accurate persona prediction?*
- Comparing the two LOOs tells us whether the LLM's persona-internal feature representation aligns with established human-cognition theory.
- This shifts the paper from "feature-engineering result on GSS data" to "psychological-theoretical claim about LLM persona construction" — much stronger thesis fit.

### Cost addition

Almost zero. The theoretical secondary analysis re-uses the same LLM outputs from Phase 1a/1b — it's a re-aggregation, not a re-run. Only cost is the 2-3 days of Joyce's literature work to lock the mapping.

### Pre-registration — staged via amendment

The initial OSF pre-registration (filed *before Phase 1a fires*) locks the **4-bin primary LOO only**. It does NOT include the theory-bin LOO, because the theory has not yet been chosen.

The theory-bin LOO enters via an **OSF pre-reg amendment**, filed *before any 1c re-aggregation runs*, once the following are committed:
1. A locked candidate theory in `theory_review.md` §8 (`_locked_theory` field set)
2. A locked variable → theory-cluster mapping in `gss_theory_taxonomy.json`
3. A locked Holm-Bonferroni multiplicity rule for the theory-bin family (independent of the 4-bin primary family — see §8.8)

Until the amendment is filed, the theory-bin LOO is **exploratory** and is NOT reported as a confirmatory result in the Phase 1a/1b primary writeup. Re-aggregating the existing LLM outputs under a theory-bin grouping *before* the amendment is research-degrees-of-freedom misuse and must be avoided.

### Joyce's next step

Read `theory_review.md` for the candidate-theory survey. Pick one. Update the `_locked_theory` field at the top of that doc. Once locked, the next steps are:
1. Build `gss_theory_taxonomy.json` mapping each attitudinal GSS variable → theory cluster
2. Extend `compute_phase1_headline_multimodel` to compute LOO on theory-cluster groups
3. **File the OSF pre-reg amendment** introducing the theory-bin family BEFORE running any theory-bin re-aggregation
4. Re-aggregate Phase 1a/1b outputs under the theory grouping; report theory-bin LOO as a secondary confirmation

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
