# Research Design — LLM Persona Feature Attribution on GSS 2024

**Author**: Joyce Yu · Stanford GSB · GSBGEN390 thesis-track · Spring 2026
**Advisor**: Prof. Mohsen Bayati
**Last updated**: 2026-07-12 (Phase 1B cell = Random × P1 per Bayati email; random-battery-ablation 6th condition added; see §7.1, §8)

This is the single source of truth for the Phase 1 study. No OSF preregistration (advisor decision 2026-05-28). Earlier OSF / brief / theory docs are in `archive/`.

---

## 1. Research question

**Phase 1**: Of four pre-specified survey-collectible feature categories — **demographic, behavioral, psychological, attitudinal** — which most contributes to LLM persona prediction of held-out GSS 2024 attitude outcomes? Within each category, which construct-level batteries drive the predictive signal?

**Project-level**: How does the contribution of each category vary across outcome dimensions? Phase 1 answers this for **attitudes**. Phase 2 will extend to **BFI personality** and **behavioral economic games** via targeted Cookiy collection (separate design, not covered here).

**Benchmark**: Park et al. 2024 v2 (arXiv:2411.10109). Park's surveys-only vs. interview comparison shows the outcome-stratified gap: surveys ≈ interview on GSS attitudes (0.82 vs. 0.83), but surveys lag interviews by 0.15 on BFI and 0.28 on behavioral games. Phase 1 attacks the GSS-attitudes row.

**What this estimates**: single-wave GSS 2024 attitude prediction from same-wave GSS features, decomposed by category and battery. Restricted to the GSS 2024 cross-section as a fixed dataset.

**What this does NOT estimate**: test-retest fidelity (no recontact baseline in GSS); longitudinal prediction; population-level US attitude parameters; general human-simulation ability.

---

## 2. Data

GSS 2024 cross-section: **N = 3,309 respondents × 973 variables**, three-batch fixed-width extract from the GSS Data Explorer at `data/gss/390data1/{batch1,batch2,batch3}/`. Loader: `gss_loader.py` (read once, cache in memory).

Sampling is deterministic via `gss_pipeline.sample_respondents(n, seed=42)`. The same seed=42 governs the bootstrap CIs (B=10,000, BCa via `scipy.stats.bootstrap` with percentile fallback).

---

## 3. Evaluation set

Locked in `gss_feature_taxonomy.json` (v0.3) and `gss_battery_map.json` (v0.2).

### 3.1 Primary eval — 12 attitude items (the prediction targets)

| Variable | Construct family | Format | Scale |
|---|---|---|---|
| POLVIEWS | political ideology | Likert-7 | 1 Extremely liberal … 7 Extremely conservative |
| PARTYID | party identification | Likert-7 + Other | 0 Strong Democrat … 6 Strong Republican (7 = Other) |
| ABANY | abortion attitudes | binary | 1 YES, 2 NO |
| CAPPUN | death penalty | binary | 1 FAVOR, 2 OPPOSE |
| GUNLAW | gun control | binary | 1 FAVOR permits, 2 OPPOSE |
| FECHLD | gender role attitudes | Likert-4 | 1 Strongly agree … 4 Strongly disagree |
| FEPOL | women in politics | binary | 1 AGREE, 2 DISAGREE |
| RACDIF1 | racial attitudes | binary | 1 YES (discrimination), 2 NO |
| CONFINAN | confidence in banks | Likert-3 | 1 A great deal … 3 Hardly any |
| CONLEGIS | trust in Congress | Likert-3 | 1 A great deal … 3 Hardly any |
| HELPPOOR | govt help for poor | sparse-anchored Likert-5 | 1 Govt should improve … 5 Each person should |
| SATFIN | financial satisfaction | Likert-3 | 1 Pretty well satisfied … 3 Not at all |

GSS ballot rotation means each respondent typically sees ~8 of 12 items. Coverage varies substantially by item — POLVIEWS / PARTYID / SATFIN are on ~99% of ballots, GUNLAW / FECHLD / CONFINAN / CONLEGIS / HELPPOOR around 65%, ABANY / CAPPUN around 30–65%, and **FEPOL (~27%) and RACDIF1 (~31%) are notably lower**. Per-item statistics (DQ-3 variance ratios, 5 × 3 × 12 summary table cells) on FEPOL and RACDIF1 are estimated from ≤ 65 respondents per cell in the N=200 panel arm; report them with explicit n and treat them as exploratory.

### 3.2 Feature pool — 140 variables × 4 bins

- **Demographic**: 24 variables, 7 batteries (age, sex, race, education, family income, region, etc.)
- **Behavioral**: 25 variables, 10 batteries (religious attendance, TV hours, voting, work hours, etc.)
- **Psychological**: 8 variables, 2 batteries (happiness, health, work satisfaction, exciting life)
- **Attitudinal**: 83 variables, 15 batteries (abortion battery, civil-liberties triad, gender-role attitudes, economic-policy attitudes, etc.)

### 3.3 Sensitivity eval — 118 items (DEFERRED 2026-06-01)

Originally designed to produce a side-by-side per-item raw-accuracy table against Park v2's SI Table 3 reference. **Deferred** after the 2026-06-01 anchor reframing (see §5.5–5.6): we now use the anchor as a within-study frontier baseline on our 12 items rather than as a Park-comparable cross-item table, so the 118 extra sensitivity items are not needed for the headline analysis. Sensitivity_eval code path remains in the driver for future Park-comparable runs if reviewers request them.

---

## 4. Leakage hygiene

Two layers:

**R1 — battery-level structural exclusion**. When predicting any primary_eval item `X`, drop the entire battery containing `X` from the persona prompt. Mirrors Park v2 SI §6's BFI whole-trait-block hold-out. Implemented in `run_primary_one_respondent`; validated by `validate_taxonomy.py` check 7c.

**R2 — regression-baseline comparator**. A non-LLM Ridge (Likert) / multinomial Logistic (binary) baseline with 5-fold respondent-level CV on the same R1-respecting input pool. Estimates what a simple supervised predictor can extract from the same features. The LLM-vs-regression gap is the model-specific predictive value above a non-LLM baseline.

---

## 5. LLM panel (Phase 1A factorial)

**Locked 2026-05-28 per Bayati signoff.** The Phase 1A panel arm is a 4-model × 3-prompt factorial on N=200 panel respondents (`sample_respondents(200, seed=42)`).

### 5.1 Models (4-cell panel + 1 anchor) — Panel F''

**Locked 2026-05-31 23:52** (Joyce decision after V4-Pro thinking cell from panel F' showed concerning behavior on the first 5 paid respondents: 7.3% parse failure rate trending poorly + ~4x runtime overhead from CoT). Panel F' had structured one cell as a thinking sensitivity comparison; F'' drops that contribution in favor of all-non-thinking reliability and faster execution. Cross-family balance preserved (3 China + 1 Western).

| Slot | Model (OpenRouter slug) | Provider (locked) | Type | Cost/call | Role |
|---|---|---|---|---|---|
| 1 (China) | `qwen/qwen3-max` | Alibaba (official) | non-thinking | $0.00098 | Newer-flagship Qwen 3 instruct; description ("instruction following, multilingual, long-tail knowledge") matches GSS task. `supported_parameters` lacks `reasoning` → pure non-thinking architecture. |
| 2 (China) | `deepseek/deepseek-v3.1-terminus` | DeepInfra | non-thinking | $0.00032 | DeepSeek V3 lineage final non-thinking variant; fixed Chinese-English language-mixing bug per release notes (relevant for English-only GSS output). Replaces V4-Pro thinking cell from F'. |
| 3 (Western) | `meta-llama/llama-4-maverick` | DeepInfra | non-thinking | $0.00018 | Sole Western family; Llama 4 instruct succeeds Llama-3.3-70B. |
| 4 (China) | `moonshotai/kimi-k2-0905` | Novita | non-thinking | $0.00072 | 2025-09 non-thinking refresh of K2-0711; same MoE architecture, smaller drift. (K2.5 / K2.6 are hybrid and reserved as future sensitivity cells.) |
| Anchor | `openai/gpt-4o-2024-08-06` | OpenAI direct | non-thinking | $148 total | Park v2 reference (dated snapshot per round-4 #3); N=100 selection subset, P0 only, n_samples=2. |

**F' → F'' swap rationale**. The thinking sensitivity cell was an attractive methodological addition but proved costly in practice: V4-Pro on the first 5 paid respondents produced 6 parse failures (all empty `''` content — CoT consumed the token budget without emitting a final integer), concentrated on Likert-7+ items (POLVIEWS, PARTYID, HELPPOOR). Per-respondent latency was ~4 min vs ~1 min for non-thinking peers, projecting the full Phase 1A run from ~14h to ~42h. The five-respondent V4-Pro data is archived at `outputs/.archive_v4pro_attempt_2026-05-31.json` and the F'/F'' transition itself is a usable methodology footnote in the paper ("we evaluated thinking-cell viability empirically; the cell met our DQ-1 ceiling but failed our runtime budget").

**Citations originally supporting panel choice** (still relevant for non-thinking cells; the thinking-cell hypothesis is now an open question rather than a sensitivity test):
- PB&J (arXiv:2504.17993): plain CoT gives ~0 gain on OpinionQA — supports our choice to drop the thinking cell.
- "Reasoning or Overthinking" (arXiv:2506.04574): classification accuracy underperforms with deliberative reasoning — consistent with V4-Pro's parse-fail rate trend.
- DeepSeek-R1 Nature paper (arXiv:2501.12948): structured output + format compliance flagged as limitation — directly validated by V4-Pro's empty-content failures.
- Sun et al. 2025 (arXiv:2506.21587): DeepSeek-V3 / Qwen2.5 / Llama-3.3 / GPT-4o cross-cultural ANES comparison establishes cheap-LLM-vs-frontier baseline competitiveness.

**Cost summary**: average cheap cell ~$0.00055/call (input-dominated for non-thinking models); Phase 1A estimated **~$15-20** (down from F''s projected $22 because non-thinking output tokens are 1-2 per call vs V4-Pro's 200-1000); Phase 1 total ~$735. Runtime estimate **~12-15h total** (vs F''s 42h projection from the 5-respondent observation), though actual speed will reveal at run time.

### 5.2 Prompts (3 format candidates for §7 selection)

| ID | Format | Citation |
|---|---|---|
| **P0** | 4-bin key-value list, 2nd-person framing | Park et al. 2024 v2 (arXiv:2411.10109), surveys-only condition |
| **P1** | 4-bin 1st-person prose clauses | Argyle, Busby, Fulda, Gubler, Rytting, Wingate (2023) "Out of One, Many", *Political Analysis* 31(3) |
| **P2** | 4-bin interview Q&A turns | Wang, Pyatkin, Bhagavatula, Choi (2025) "The Prompt Makes the Person(a)", *Findings of EMNLP 2025* |

These are three published persona-prompt formats from the LLM-on-survey literature. The set is **not a crossed design** over voice or structure factors and therefore does not support causal attribution of any single design feature; it is treated end-to-end as three format candidates, one of which §7 selects for Phase 1B. The Phase 1B headline reports MAE under the §7-selected (model, prompt) cell with no causal claim about prompt design.

P0 is the OSF-v1-era baseline implemented in `build_persona_prompt()`. P1 and P2 are new for Phase 1A. Full literature scan grounding these choices is at `archive/lit_review_prompt_variants_2026-05-15.md`.

### 5.3 Factorial structure (12 cells)

Each of the 200 panel respondents runs all 12 (model × prompt) cells × **Full condition only** × 12 primary_eval items (filtered to those on the respondent's GSS ballot — ~8/12 on average per §3.1). **n_samples = 2 per call** to match the GPT-4o anchor's `n_samples` and shrink per-cell SE on the selector's primary metric (Reviewer round-2 Q1). Comparison across cells is within-respondent.

**LOO conditions are deferred to Phase 1B** (Joyce 2026-05-29 decision per Reviewer round-2 Q3): the §7 selector only reads Full, and the §8 4-bin LOO ΔMAE headline runs on the disjoint N=3,309 Phase 1B cohort. Generating LOO data on the N=200 panel for all 12 cells, only to discard 11 of those cells' LOO records after selection, was the dominant cost driver in the previous Phase 1A budget.

**Ballot-off pre-filter**: `run_primary_one_respondent` checks `truth_code_or_none` before each LLM call. Items where the respondent's GSS ballot did not include the item (no GSS-2024 truth code) are skipped at call time rather than at scoring time. ~33% additional cost reduction with zero analytical impact.

### 5.4 Random-model column (5th "model", 3 cells, post-hoc)

For each respondent `r` and each prompt `p`, a model is selected uniformly at random from {Qwen3-max, DeepSeek-v3.1, Llama-4-maverick, Kimi-K2} via a seed=42 hash on `(r, p)`. The respondent's "Random × p" value is set equal to the corresponding (model, p) panel result. **Pure uniform random — no 50/50/50/50 balance constraint.** No new LLM calls.

The random column is a deployment-mode sensitivity comparator (each Phase 1B respondent in deployment sees one model; this estimates "if a Phase 1A respondent had only seen one randomly-assigned model"). It is reporting-only, **not a §12.2 selector input**.

### 5.5 GPT-4o anchor — within-study frontier baseline

**Updated 2026-06-01 23:55** after dropping the direct Park v2 raw-accuracy comparison (see §5.6 for rationale). The anchor's primary role is now **within-study frontier baseline** for the cheap-vs-frontier comparison on **our 12 items, our protocol, our cohort**.

Two anchor conditions are run, both N=100 (= first 100 IDs of `sample_respondents(200, seed=42)` — identical IDs to Phase 1A's first 100 panel respondents, enabling paired comparison):

| Condition | Model | R1 battery exclusion | Items | n_samples | Purpose |
|---|---|---|---|---|---|
| **Anchor B** (our protocol) | `openai/gpt-4o-2024-08-06` | **ON** | 12 primary_eval | 2 | Apples-to-apples frontier vs cheap panel — isolates the model-tier effect under identical R1 protocol |
| **Anchor A** (Park-exact) | `openai/gpt-4o-2024-08-06` | **OFF** | 12 primary_eval | 2 | Park v2's leakage protocol on our items + model — isolates the R1-protection cost |

Cost: ~$24 each = $48 total. Sensitivity_eval (118 items) deferred — no longer needed once we abandon the direct Park-comparable per-item Table 3 frame.

**Paired comparison structure**: the 100 anchor respondents are the *same individuals* as Phase 1A's first 100 panel respondents (verified by ID-set equality on `sample_respondents(n, seed=42)`'s deterministic shuffle). For each (respondent, item) the paper reports:
- Cheap × (model, prompt) prediction (Phase 1A panel data)
- GPT-4o R1-ON prediction (Anchor B)
- GPT-4o R1-OFF prediction (Anchor A)

A paired Wilcoxon / paired bootstrap on the per-respondent normalized MAE difference quantifies the cheap-vs-frontier gap with substantially more power than an unpaired N=200 comparison would have given.

### 5.6 Park v2 comparability stance

**Updated 2026-06-01 23:55 after Researcher subagent audit of Park v2 SI Table 3.** Initial worry was that Park's headline 65.67% raw GSS accuracy averaged over 177 mixed items (including easy demographic items like sex, race, citizenship which score 0.93–1.00) wouldn't apples-to-apples with our 12 politically-charged attitudes. **Researcher resolved this** by extracting Park v2 SI Table 3 per-item raw accuracy:

| Our item | Park v2 SI Table 3 raw accuracy | Park v2 normalized accuracy |
|---|---|---|
| polviews | 0.55 | 0.66 |
| partyid | 0.74 | 0.90 |
| abany | 0.79 | 0.88 |
| cappun | 0.67 | 0.77 |
| gunlaw | 0.70 | 0.83 |
| fechld | 0.48 | 0.75 |
| fepol | 0.78 | 0.88 |
| racdif1 | 0.81 | 0.95 |
| confinan | 0.52 | 0.72 |
| conlegis | 0.55 | 0.75 |
| satfin | 0.67 | 0.97 |
| HELPPOOR | not in Park v2 SI Table 3 | — |
| **Mean over 11 items** | **0.66 raw** | **0.82 normalized** |

The 11-item mean (0.66) is essentially identical to Park's overall headline (0.6567). The "politically-charged items are systematically harder" worry is **empirically false** — Park's agents do as well on our slice as on the full set.

This unlocks a **clean per-item Park-comparable benchmark**: side-by-side accuracy for each of our 11 items, cheap-panel × P0/P1/P2 vs Park v2's reported numbers.

**Three remaining genuine differences (acknowledged in writeup, not used to dismiss comparison):**

1. **Persona-richness mismatch.** Park's agents have access to 2-hour interview transcripts (mean 6,491 words/transcript) — semi-structured narrative of life history, values, opinions. Our agents have 140 GSS structured variables. Park's higher accuracy partly reflects richer persona inputs, not just better LLMs. **This is the substantive scientific tradeoff our paper measures**: how much accuracy does the cheap-personas-via-public-survey route lose vs the expensive-personas-via-interview route?

2. **Headline number convention.** Park v2's headline 82-86% is normalized by 79.53% human two-week test-retest consistency, not raw. Their raw is 65.67%. GSS 2024 public release has no test-retest, so we report raw accuracy throughout and footnote Park's normalized headline for reader context.

3. **Sample-frame.** Park v2 recruited their own 1,052-respondent stratified panel and ran 2-hour interviews + custom Qualtrics GSS administration. We use public GSS 2024 cross-section. Different respondents, different administration mode.

**Decision** (locked 2026-06-01): we report **two Park-comparable benchmarks** side by side with cheap-panel headline:

(a) **Internal GPT-4o anchor** (§5.5) — same 12 items, same cohort, same R1 protocol. Primary frontier baseline; pairs cleanly with cheap panel for paired statistical comparison.

(b) **Park v2 SI Table 3 per-item accuracy** (this section) — external reference; per-item table shown side-by-side with our results. Specifically the headline summary table in the writeup will read:

| Item | Cheap × P1 (ours) | GPT-4o anchor R1-OFF (ours) | Park v2 (interview agents, raw) |

Park v2's persona-richness advantage (interview vs survey-only personas) is named in the limitations, not used to dismiss the comparison. **Park's 65.67% headline is NOT a comparison target**; per-item Table 3 entries are.

**Sources**: Park v2 SI Table 3, PDF pp. 39–43 (raw accuracy per GSS item, both interview and surveys-only conditions). Park's strict exact-match scoring (SI §5 p.19) matches ours.

---

## 6. Phase 1A output structure

Bayati's requested format (2026-05-28). The Phase 1A run produces both a summary table and a raw long-format database.

### 6.1 Summary table — 5 × 3 × 12 = **180 rows**

| Model | Prompt | Question | Construct | Format | N | MAE | exact_match | parse_fail_rate | DK_rate | dq3_variance_ratio |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen | P0 | POLVIEWS | political ideology | Likert-7 | ~99 | ... | ... | ... | ... | ... |
| Qwen | P0 | PARTYID | party identification | Likert-7 | ~99 | ... | ... | ... | ... | ... |
| Qwen | P0 | ABANY | abortion attitudes | binary | ~65 | ... | ... | ... | ... | ... |
| ... (12 rows for Qwen × P0) | | | | | | | | | | |
| Qwen | P1 | POLVIEWS | ... | | | | | | | |
| ... (12 rows for Qwen × P1) | | | | | | | | | | |
| Qwen | P2 | ... (12 rows for Qwen × P2) | | | | | | | | |
| DeepSeek | P0 | ... (36 rows) | | | | | | | | |
| Llama-3.3 | P0 | ... (36 rows) | | | | | | | | |
| Kimi | P0 | ... (36 rows) | | | | | | | | |
| **Random** | P0 | ... (12 rows, post-hoc) | | | | | | | | |
| **Random** | P1 | ... (12 rows) | | | | | | | | |
| **Random** | P2 | ... (12 rows) | | | | | | | | |

Stored at `outputs/phase1a_summary_table.{csv,parquet}` after the §12.2 selector runs.

### 6.2 Raw long-format database — ~38,400 rows (Phase 1A) + Random column

Schema (19 columns; `random_dropped_battery` added 2026-07-12, NULL for all Phase 1A rows):

| Group | Column | Meaning |
|---|---|---|
| **Prediction** | `respondent_id` | seed=42 index into the GSS 2024 sample |
| | `model` | full slug (e.g., `qwen/qwen-2.5-72b-instruct`) or `Random` |
| | `prompt` | one of `P0`, `P1`, `P2` |
| | `condition` | `Full` (Phase 1A); Phase 1B also has `drop_demographic` / `drop_behavioral` / `drop_psychological` / `drop_attitudinal` |
| | `item` | primary_eval variable (e.g., `POLVIEWS`, `GUNLAW`, …) |
| | `true_code` | ground-truth integer code from GSS 2024 |
| | `pred_code` | model-output integer code (NULL if parse_ok=false) |
| | `parse_ok` | boolean — did the model output parse to a valid code? |
| | `abs_err` | `|pred_code − true_code|` on Likert items; 0/1 on binary (NULL if parse_ok=false) |
| | `sample_position` | 1 or 2 (Phase 1A cheap panel runs n_samples=2 to match the GPT-4o anchor) |
| **Call metadata** | `timestamp` | parquet-write time, ISO 8601 UTC (per-call timestamps are not yet returned by call_llm_meta) |
| | `cost_usd` | NULL — `call_llm_meta` returns tokens, not USD; cost = tokens × USD-rate join downstream |
| | `tokens_in` | input token count from `call_llm_meta` |
| | `tokens_out` | output token count from `call_llm_meta` |
| **Provenance** | `error_type` | `ok` \| `parse_fail` \| `provider_error`; disentangles model-output rejection from transient API failures |
| | `provider` | OpenRouter backend identifier when available (NULL for OpenAI direct calls) |
| | `system_fingerprint` | OpenAI reproducibility token when available |
| | `model_returned` | provider-reported model name; may differ from the requested slug (mid-run quantization/version drift detector) |
| **Ablation** | `random_dropped_battery` | battery dropped in the `random_battery_drop` condition (§8 Layer 2); NULL in all other conditions and all Phase 1A rows. The per-battery absent-vs-present analysis joins on this column. |

Example rows:

| respondent_id | model | prompt | condition | item | true_code | pred_code | parse_ok | abs_err | sample_position | timestamp | cost_usd | tokens_in | tokens_out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | Qwen | P0 | Full | POLVIEWS | 3 | 3 | true | 0 | 1 | 2026-05-29T14:32:01Z | 0.00041 | 928 | 3 |
| 0 | Qwen | P0 | drop_demographic | POLVIEWS | 3 | 2 | true | 1 | 1 | 2026-05-29T14:32:04Z | 0.00038 | 858 | 3 |
| 0 | Qwen | P0 | Full | PARTYID | 1 | 1 | true | 0 | 1 | 2026-05-29T14:32:07Z | 0.00041 | 928 | 3 |
| 0 | **Random** | P0 | Full | POLVIEWS | 3 | 3 | true | 0 | 1 | (= Qwen row's metadata) | | | |

**`model="Random"` row construction**: for each `(respondent_id, prompt)`, a seed=42 hash uniformly picks one of the four real models (no balance constraint). The `Random × prompt` rows are copies of that picked model's rows with `model` re-labeled to `Random`. No new LLM calls; the timestamp / cost / token columns are copied from the source row for auditability.

**Volume**: 200 respondents × 5 (4 cheap models + Random) × 3 prompts × **1 condition (Full only — LOO deferred to Phase 1B)** × ~8 ballot-on items × **n_samples=2** ≈ **48,000 rows**. Stored at `outputs/phase1a_raw.parquet` (DuckDB-compatible). The Phase 1B parquet (`outputs/phase1b_raw.parquet`) adds the 6 §8 conditions (Full + 4 bin-LOO + random_battery_drop) on the §7.1 cell × N=3,309 — consolidated with `--no-random-column` + explicit `--output` (the §5.4 Random column is Phase 1A-only; under random dispatch it would duplicate every row).

The summary table (§6.1, 180 rows) is derived from the raw DB by aggregating on the `Full` condition. Any future re-analysis (different metric, different aggregation, sensitivity check) queries the raw DB directly without re-running the LLM panel. Bayati's requested 5 × 3 × 12 = 180-row MAE table is one line of pandas / SQL:

```sql
SELECT model, prompt, item, AVG(abs_err) AS mae, COUNT(*) AS n
FROM phase1a_raw
WHERE condition = 'Full' AND parse_ok = true
GROUP BY model, prompt, item
ORDER BY model, prompt, item;
-- → 180 rows (5 models × 3 prompts × 12 items, minus the (cell, item) pairs where every
--   respondent's ballot missed that item — these become NaN MAE with n=0)
```

### 6.3 Phase 1B raw DB (when it runs)

Same 19-column schema. Random-dispatch cell (§7.1) × N=3,309 × **6 conditions**
(Full + 4 bin-LOO + random_battery_drop, §8) × ~8 items × n_samples=1 ≈
**158,000 rows**. Stored at `outputs/phase1b_raw.parquet`. The `model` column
records the actually-dispatched slug per respondent (the random assignment is
recoverable from SHA-256(42|rid|P1)); no post-hoc Random relabeling at the
Phase 1B stage.

---

## 7. Selector: Phase 1A → Phase 1B

Joint (model, prompt) cell selection. See `select_phase1b_cell.py`.

```
candidate cells = {(m, p) : m ∈ {Qwen, DeepSeek, Llama-3.3, Kimi}, p ∈ {P0, P1, P2}}  # 12 cells

# Per-item normalized abs-err so that mixed scales (binary, Likert-3/4/5/7) contribute
# comparably. Each item's normalized abs-err is in [0, 1]; macro-average runs
# over respondents and then over items.
normalized_abs_err(respondent, item) = abs(pred_code − true_code) / (max_code − min_code)

# CONSERVATIVE primary metric (locked 2026-05-29 Reviewer round-2 Q2):
# parse_fail rows are counted as normalized_abs_err = 1.0 (maximum). The
# previous "optimistic" metric dropped parse_fail rows, which structurally
# rewarded cells that strategically refused to answer hard items.
# Both metrics are computed; conservative drives selection, optimistic is
# reported alongside as a sensitivity check.
primary_score(cell) = mean over respondents of (mean over Full-condition items in their ballot of
                                                normalized_abs_err   # parse_fail → 1.0)

# Scoring uses the FULL N=200 panel cohort with n_samples=2 (the OSF-era
# 100/100 split was dropped per 2026-05-28 Bayati signoff; n_samples bumped
# from 1 to 2 to match the GPT-4o anchor per 2026-05-29 Joyce decision).

DQ-1 (parse-fail ceiling):    parse_failure_rate ≤ 10% per cell  (was 30%)
DQ-3 (marginal-distribution-collapse guard): for each primary_eval item i,
                              var(cell_i) / var(human_i) ≥ 0.30
                              cell fails if > 30% of items fail the floor
                              (tightened from > 50% per commit 390780f Reviewer
                              round-4 #1b — the 5/12 = 41.7% binary-only
                              collapse case slipped through the old 50% ceiling)
                              human variance reference: outputs/primary_eval_human_variance_2024.json
                              variance computed at the respondent level
                              (mean across n_samples per (rid, item) first,
                              then population variance across respondents —
                              prevents n_samples>1 LLM jitter from inflating
                              the variance estimate; Reviewer round-3 P2 #3)

# Tiebreak: bootstrap-CI overlap (NOT a fixed 5% MAE window).
# Locked 2026-05-29 per Reviewer round-3 P1 #4. The old fixed 5% window
# was ~5x narrower than the per-cell SE, so the argmin "winner" was
# selected at noise resolution while the rationale label claimed a clean
# win. New rule:
tie_set = {argmin cell} ∪ {survivors whose bootstrap CI overlaps the argmin's CI}

if |tie_set| == 1:  rationale = ci_unique_argmin    (statistically separated; SELECTED = argmin)
else: cost tiebreak inside tie_set:
    if single cost-cheapest: rationale = ci_overlap_cost_break
    if multiple cells tied on cost (≤1%): rationale = fallback_qwen_p0_tie (named fallback)

All cells fail DQ: PAUSE — Phase 1B does not proceed (rationale = all_dq_fail_pause).
```

### 7.1 Selection outcome + advisor override (2026-07-12)

The selector ran on `outputs/phase1a_raw.parquet` (2026-06-01 data) and returned
**Qwen × P0 via `fallback_qwen_p0_tie`** — 8 of 12 cells were statistically
indistinguishable (CI overlap) and 2 tied on cost, so the named fallback fired.
No cell won on quality.

**Phase 1B cell decision (Bayati email 2026-07-12, superseding the fallback): Random × P1.**
Rationale:

1. **No model separates statistically.** With respondent-clustered SEs no cheap
   model beats the Random column on either raw accuracy or normalized MAE;
   only Qwen separates, and it is *worse*.
2. **Mode collapse.** On CONFINAN/CONLEGIS the individual models give one
   answer to nearly all 200 respondents (top-code fraction 0.77–1.00).
   Random dispatch mixes models that collapse to *different* codes, restoring
   spread on CONLEGIS (top-code fraction 0.53, close to the truth marginal).
   It does NOT fix CONFINAN, where all four models collapse to the same code
   (0.92) — reported as a per-item limitation.
3. **Deployment realism.** Random dispatch matches the §5.4 deployment-mode
   framing: each Phase 1B respondent is served by one model.

Prompt = **P1** (best Random-column normalized MAE: 0.2607 vs 0.2617 P2 /
0.2685 P0; also the best prompt across the panel overall).

**Mechanics**: `--phase1b-model random` dispatches per respondent via
SHA-256(42|rid|prompt) into the 4-model panel — hash-identical to the §5.4
Phase 1A Random column, so the Phase 1A random assignments extend verbatim.
The assignment is fixed per respondent across all 6 conditions (LOO ΔMAE
stays within-model). The §7 selector output (Qwen × P0) and this override
are both reported in the paper; the override is an advisor decision on the
"no model beats Random + collapse" evidence, not a re-run of the selector.

**Bootstrap CI per cell** (locked 2026-05-29 Reviewer round-2 Q1, made decision-relevant 2026-05-29 Reviewer round-3 P1 #4). Respondent-level percentile bootstrap (B=10,000, seeded) per cell on the conservative normalized MAE. The selector decision now consumes CI overlap directly: cells whose CIs overlap the headline's CI are statistically indistinguishable from it and enter cost-driven secondary tiebreak; cells whose CIs sit cleanly outside the headline's CI are excluded from the tie-set. This closes the internal contradiction that the previous fixed-5% rule produced — the diagnostic ("X other cells overlap") and the rationale ("argmin_mae, clean win") could appear together on adjacent lines of the same log.

**Why this matters**: per-cell normalized MAE for cheap LLMs on GSS attitude prediction typically sits in the range ≈ 0.20–0.35 (cf. Park v2 SI Table 3 surveys-only baseline and comparable LLM-on-Likert work), with a per-cell SE of ≈ 0.071 (N=200, computed across respondents). The expected gap between rank-1 and rank-2 cells is on the order of ~0.05 by chance alone even when all 12 cells share the same true MAE — a fixed 5% MAE window (≈ 0.013) cannot tell signal from noise at this scale. CI overlap is the principled tie definition: two cells whose 95% CIs overlap are not statistically separated, and the selector should treat them as a tie-set rather than declaring a winner. Cells whose CIs do NOT overlap with the argmin are genuinely worse on this cohort.

Mitigations: report the full 180-row summary (§6.1) alongside the headline so the reader can audit the cluster of near-ties; report the headline MAE with paired-respondent bootstrap CI; bind the §10 LOO ablation to the chosen cell rather than re-selecting per LOO condition.

**Binary sensitivity check** (post-selection, mandatory). After §7 picks the headline cell, report that cell's **exact-match accuracy on each of the 5 binary primary_eval items** (ABANY, CAPPUN, GUNLAW, FEPOL, RACDIF1) alongside the headline normalized MAE. Per-item normalization makes binary errors equal-weighted in `primary_score`, but a cell can still have a low aggregate MAE while collapsing specifically on one or two binary items. If any of the 5 binary items has exact-match accuracy < 0.50 (worse than chance) on the held-out Phase 1B sample, that item is flagged in the limitations section as a model-specific failure on the selected cell. This is reporting only — it does NOT trigger a selection rerun.

---

## 8. Phase 1B

Cell = **Random × P1** (§7.1 advisor decision). Primary_eval only, n_samples=1,
**6 conditions** (locked 2026-07-12, Joyce + Bayati email): the original 5
(Full + 4-bin LOO) plus a randomized-battery-ablation condition. Two layers:

**Layer 1 — bin-level LOO (headline, unchanged).** Full + drop_{demographic,
behavioral, psychological, attitudinal}. Exclusions per prediction: the item's
own battery (R1, all conditions) + the dropped bin. All 34 batteries nest
within single bins (verified), and every primary_eval own-battery is
attitudinal — so under drop_attitudinal the bin drop subsumes R1 (the code's
drop_bin + exclude_vars union handles this automatically), and the
drop_attitudinal ΔMAE estimates the contribution of the attitudinal bin
*beyond* the own battery, which is the intended estimand since R1 holds on
both sides of every Δ.

**Layer 2 — randomized battery ablation (`random_battery_drop`, new).** Per
(respondent, item): drop the own battery (R1) + ONE additional battery drawn
uniformly at random from the remaining 33 (34 for singleton items), via
seeded hash SHA-256(42|battery|rid|item). Deterministic, resume-safe; the
drawn battery name is recorded in the `random_dropped_battery` column.

Because the draw is randomized per (rid, item), each of the 34 batteries is
absent in ~1/33 of ablation calls (**~650–800** (rid, item) pairs per battery
across N=3,309 × ~8 items — the lower end applies to batteries that own
multiple primary items, e.g. `gender_role_attitudes` and
`confidence_in_institutions`, which can never be drawn on their own items).
Each ablation row pairs with the Full row for the same (rid, item), so battery
`b`'s marginal contribution is estimated by the **paired difference**
`mean(err_ablated − err_full)` over the pairs where `b` was drawn — pairing
cancels respondent- and item-level variation (expected SE ≈ 0.005 on
normalized error; detectable effects ≥ ~0.01). This is the randomized-sampling
approximation of the §9.1 enumerated Battery LOO at ~1/8 of its cost; §9.1's
fate (full / reduced / dropped) is decided after these results are in.

**Estimand definition**: battery `b`'s effect is identified only on items
*outside* `b` — its own primary items exclude `b` via R1 in both arms, so
those cells are structural zeros. This matches §9.1 (the enumerated LOO's
drop-`b` is equally a no-op on `b`'s own items under R1): the estimand in
both designs is `b`'s **marginal contribution to predicting out-of-battery
items**. Two analysis-time notes: (a) cross-battery comparisons ride on
slightly different item supports (own-batteries of primary items are
evaluated on 10–11 items; the other 29 batteries on all 12); (b) the paired
estimator requires `parse_ok` in both arms — differential parse failure
between arms is a (small) missingness channel to check before interpreting.

**Analyzer status**: the paired-difference analyzer for this layer is
**pending** — `battery_loo.py` only consumes `condition='battery_loo_drop_*'`
records and ignores `random_battery_drop`. To be implemented before Phase 1B
analysis (data collection is not blocked).

Note for cross-run comparisons: Layer 2 is a *new condition*; the Full
condition is untouched (still all features − own battery), so the headline
MAE remains directly comparable to Phase 1A and the GPT-4o anchor.

**Headline cohort**: N=3,109 — the full 2024 GSS cross-section **minus** the N=200 panel respondents used by the §7 selector. Excluding the selector cohort removes the in-sample optimism on the cell chosen by argmin. The 200 selector respondents are reusing the Phase 1A artifact (already paid), so the exclusion costs no LLM calls — it only changes which rows are aggregated for the headline. Cohort assignment is deterministic via `sample_respondents(200, seed=42)` ∩ `gss_cross_section_2024.index`.

**Sensitivity cohort**: full N=3,309 (including the 200 selector respondents). Reported alongside the headline. Expected gap is small because 200 / 3,309 ≈ 6%, but the gap itself is the empirical optimism estimate and worth reporting; a large gap is a flag that the §7 winner was substantially noise-driven.

**Headline**: 4-bin LOO ΔMAE per bin (drop bin, re-score, take Δ vs. Full). Paired-respondent bootstrap CIs (B=10,000 BCa) on the N=3,109 cohort. When reporting bin rankings, apply Holm-Bonferroni at α=0.05 across the 4 bins.

**Effect size thresholds** (Funder & Ozer 2019): small <0.02 ΔMAE on the Likert scale; modest 0.02–0.05; substantive ≥0.05. Substantively interpret a bin's contribution only when its ΔMAE CI excludes the small threshold.

---

## 9. Phase 1C (co-primary)

Two analyses on the Phase 1B records:

### 9.1 Battery LOO — 34 batteries × 12 items × N=3,309

**Status update 2026-07-12**: the §8 Layer-2 randomized battery ablation
estimates the same per-battery estimand from the Phase 1B run itself (~800
paired observations per battery, SE ≈ 0.005). Whether this enumerated Battery
LOO still runs — in full (~$481), reduced to the batteries the ablation flags
as significant, or not at all — is **decided after Phase 1B data is in**.
Design below retained for the full-enumeration case.

Drop one battery at a time from the persona prompt; recompute MAE; report ΔMAE per battery. Two corrections:

- **Within-bin nested Holm**: independent Holm at α=0.05 per bin (D:7, B:10, P:2, A:15).
- **Joint-34 sensitivity**: stricter Holm at α/34 ≈ 0.00147 across all batteries; required for cross-bin claims.

Analyzer: `battery_loo.py`.

### 9.2 Bin-level Shapley decomposition — 16 conditions on the Phase 1A panel

Enumerate 16 subset-drop conditions on the N=200 panel cohort (4 cheap models × the selected prompt). Shapley shares the 4-bin LOO family — no separate multiplicity correction.

Analyzer: `shapley_decomposition.py`.

---

## 10. Implementation

### 10.1 Code (in `src/`)

| File | Status |
|---|---|
| `src/gss_loader.py`, `src/gss_pipeline.py` | Loader + persona-prompt + scoring; implemented + tested |
| `src/llm_router.py` | Multi-model LLM router with per-call seed derivation; implemented + tested |
| `archive/select_phase1b_model.py` | OSF-v1 single-model selector with DQ gates; superseded by `select_phase1b_cell.py`, archived 2026-07-12. |
| `src/select_phase1b_cell.py` | §7 joint (model, prompt) cell selector. Reads `outputs/phase1a_raw.parquet`. Implemented + 6 self-tests pass. |
| `src/write_phase1a_parquet.py` | §6.2 long-format parquet writer + Random column. Implemented + 9 self-tests pass (incl. 2026-07-12: populated `random_dropped_battery` roundtrip, Phase-1B-shape guard, panel-list lock vs `llm_router`). |
| `src/gss_driver.py` | Orchestrator with `--phase1a` / `--phase1b` / `--phase1b-anchor` modes. 3-prompt factorial extension implemented: `--phase1a` loops over P0/P1/P2 (writes three per-prompt JSONs) and auto-consolidates into `outputs/phase1a_raw.parquet`. `--phase1b-prompt {P0,P1,P2}` required for non-anchor Phase 1B runs once the factorial parquet exists. **2026-07-12 additions**: `--phase1b-model random` (per-respondent SHA-256 dispatch, hash-identical to the §5.4 Random column, fixed across conditions) + `random_battery_drop` 6th condition (CONDITIONS_PHASE1B; seeded per-(rid,item) battery draw avoiding the own battery; battery name stamped into records + parquet `random_dropped_battery` column). Verified: picker determinism, own-battery avoidance (N=3,309), 33/33 + 34/34 coverage, prompt-shrinkage E2E. |
| `src/battery_loo.py`, `src/shapley_decomposition.py` | Phase 1C analyzers; implemented + self-tested. **Orchestration drivers (`--battery-loo`, `--shapley`) pending.** |
| `src/regression_baseline.py` | R2 baseline (Ridge + multinomial Logistic, 5-fold CV); implemented + tested |
| `src/validate_taxonomy.py`, `src/lint_writeup_language.py` | Lint / validation utilities; implemented + tested |

### 10.2 Pipeline extensions for the Bayati-confirmed factorial — STATUS

All 4 extensions plus the post-factorial Reviewer round-2 cleanup are complete; smoke test is the next paid step.

1. **`src/gss_driver.py --phase1a`** (DONE): iterates over 3 prompts × 4 models × **Full condition only** × ballot-on items × **n_samples=2**. Records carry `prompt_id` + `prompt_version` + `template_hash` + `error_type` + provider/fingerprint provenance.
2. **`src/select_phase1b_cell.py`** (DONE, sibling of the OSF-v1 `select_phase1b_model.py`): scores 12 (model, prompt) cells jointly. Per-cell DQ-1 (tightened 30% → 10%) + DQ-3 (tightened 50% → 30% fail-fraction ceiling). Per-item normalized MAE with the **conservative** parse_fail-as-1.0 policy as primary metric (optimistic legacy metric reported alongside). **CI-overlap-driven tiebreak** (NOT a fixed 5% MAE window — see §7): the tie-set is the headline cell plus all surviving cells whose bootstrap CI overlaps the headline's CI; cost-driven secondary tiebreak fires only within that tie-set; Qwen × P0 named fallback when both ties hit. Random column (§5.4) aggregated post-hoc — not a selector input. **Per-cell bootstrap CIs** (B=10,000, respondent-level) plus a majority-class baseline (§7 round-4 addition) reported alongside the headline.
3. **Phase 1A output writer (`src/write_phase1a_parquet.py`)** (DONE): emits `outputs/phase1a_raw.parquet` (19-column long-format DB per §6.2) after the 3-prompt loop in `--phase1a`. Random column rows generated deterministically via SHA-256(seed=42 | rid | prompt). 180-row §6.1 summary derivable from the parquet in one pandas/SQL groupby. **2026-07-12**: Phase-1B-shape guard added (refuses to add the Random column to non-Full-condition records — it would duplicate 100% of dispatch rows) + `--no-random-column` flag + clobber guard requiring explicit `--output` for Phase 1B consolidation.
4. **`src/gss_driver.py --phase1b`** (DONE): accepts `--phase1b-prompt` in addition to `--phase1b-model`. Errors out if `outputs/phase1a_raw.parquet` exists but `--phase1b-prompt` is omitted (refuses to silently default to P0 once the factorial has chosen).

Reviewer round-2 cleanup also complete: ballot-off pre-filter, LOO deferral, parse_fail conservative metric, DQ-1 tightening, bootstrap CIs, fingerprint/provider/error_type logging — see commits `e17ea11`, `3236fe4`, `5ecf345`, `bacfa72`.

Reviewer round-3 cleanup complete (locked 2026-05-29): selector docstring + driver CLI stale text purged (`f5cfcea`); DQ-3 variance aggregated per (respondent, item) before cross-respondent variance to neutralize n_samples=2 LLM jitter (`851826a`); §7 tiebreak rule replaced from fixed 5% MAE window with bootstrap-CI overlap, new rationales `ci_unique_argmin` / `ci_overlap_cost_break` / `fallback_qwen_p0_tie` (`c773501`); OpenRouter provider preferences locked at call time via `allow_fallbacks=False` + `require_parameters=True` defaults plus a `PROVIDER_LOCK` dict the user populates after smoke (`f90f20c`); parquet provenance columns verified end-to-end with a new self-test (`f90f20c`).

Reviewer round-4 cleanup also complete (locked 2026-05-30): GPT-4o anchor pinned to `gpt-4o-2024-08-06` snapshot for Park v2 comparability (`6f764e4`); `.0` strip in `_extract_features` so all P0/P1/P2 renderings share clean numeric val_labels (`a95219d`); DQ-3 fail-fraction ceiling tightened 0.50 → 0.30 to catch binary-only collapse (`390780f`); majority-class baseline reported alongside the headline in the selector decision log with automatic warnings for gap < 0.02 / gap < 0 (`5cce65d`).

Next step:

1. **Panel-wide provider discovery** (free, ~10 s):
   ```
   python3 src/llm_router.py --smoke-panel
   ```
   Calls each of the 4 cheap panel models once and prints a `model → provider` table plus a ready-to-paste `PROVIDER_LOCK[...]` snippet at the bottom of the output. Copy the snippet into `src/llm_router.py:PROVIDER_LOCK`.

2. **Pipeline smoke test** (~$0.006, ~1 min):
   ```
   python3 src/gss_driver.py --smoke
   ```
   Runs 1 respondent × Qwen × P0 × Full × n_samples=2 — the exact shape of Phase 1A on a tiny cohort. Verifies the full pipeline (call_llm_meta → record → parquet consolidation if 3 prompts were run).

3. **Re-smoke with PROVIDER_LOCK populated** to confirm the locked provider serves each model. Then launch paid Phase 1A.

### 10.3 How to run (after the extensions above land)

```bash
# Pre-flight self-tests
python3 src/validate_taxonomy.py
python3 src/llm_router.py --self-test                # 1 mock-client test verifying PROVIDER_LOCK extra_body shape
python3 src/select_phase1b_cell.py --self-test       # 10 joint-cell tests (5 rationales + random column + parse_fail conservative + DQ-3 respondent-level + majority baseline + bootstrap CI)
python3 src/write_phase1a_parquet.py --self-test     # 7 writer tests (relabel, parse_fail, binary, random, count, roundtrip, provenance E2E)
python3 src/battery_loo.py --self-test
python3 src/shapley_decomposition.py --self-test
python3 src/gss_pipeline.py --test-aggregation
python3 src/prompt_variants.py --self-test           # 6 single-respondent prompt tests
python3 tests/preflight_phase1a.py                   # N=200 panel × 12 batteries × 3 prompts coverage

# 1. Provider discovery + smoke (~$0.01, ~1 min)
python3 src/llm_router.py --smoke-panel        # 4 models × 1 call; populates PROVIDER_LOCK table
python3 src/gss_driver.py --smoke              # 1 resp × Qwen × P0 × Full × n=2; exercises full Phase 1A path

# 2. Phase 1A factorial + GPT-4o anchor (~$162, ~24 hr)
python3 src/gss_driver.py --phase1a              # 4 models × 3 prompts × N=200 × Full × n=2 (~$14)
python3 src/gss_driver.py --phase1b-anchor       # GPT-4o × P0 × N=100 (~$148)

# 3. §7 joint (model, prompt) cell selector (free, <1 min)
python3 src/select_phase1b_cell.py outputs/phase1a_raw.parquet

# 4. Phase 1B (~$58, ~3-7 days) — cell locked 2026-07-12: Random × P1 (§7.1)
#    Runs on full N=3,309 × 6 conditions (Full + 4 bin-LOO +
#    random_battery_drop; §8). Headline aggregation excludes the §7 selector
#    cohort (N=3,109 disjoint), full cohort (N=3,309) reported as sensitivity.
python3 src/gss_driver.py --phase1b \
    --phase1b-model random \
    --phase1b-prompt P1

# 4b. R2 regression baseline (free, ~5 min) — report alongside Phase 1B headline
#    Non-LLM Ridge (Likert) / multinomial Logistic (binary) baseline with the same
#    R1 battery-exclusion rules. Tells reviewers what a simple supervised predictor
#    could extract from the same feature pool; the LLM-vs-R2 gap is the LLM-specific
#    predictive contribution (§4).
python3 src/regression_baseline.py \
    --input outputs/phase1b_raw.parquet \
    --output outputs/phase1b_r2_baseline.json

# 5. Phase 1C analyzers (~$519 paid + analyzers)
python3 src/gss_driver.py --battery-loo --phase1b-model <slug> --phase1b-prompt <prompt_id>
python3 src/battery_loo.py --input outputs/phase1c_battery_loo_*.parquet
python3 src/shapley_decomposition.py --input outputs/phase1c_shapley_*.parquet
```

---

## 11. Budget

| Step | Cost | Notes |
|---|---|---|
| Smoke (panel + pipeline) | ~$0.01 | `llm_router --smoke-panel` (4 calls for PROVIDER_LOCK) + `gss_driver --smoke` (1 resp × Qwen × P0 × Full × n=2 ≈ 16 calls) |
| Phase 1A factorial (4 models × 3 prompts × N=200 × Full × n=2 × ballot filter) | **~$14** | Down from ~$51 — LOO deferred to Phase 1B + ballot-off pre-filter (Reviewer round-2 Q3) |
| GPT-4o anchor (P0 only, N=100, primary + sensitivity, n=2) | ~$148 | One run serves Phase 1A + 1B reporting |
| Phase 1B (Random × P1 × N=3,309 × 6 conditions × n=1 × ballot filter) | **~$58** | 5 → 6 conditions 2026-07-12 (+random_battery_drop, ~$10); ballot-off pre-filter applied |
| **Subtotal pre-Battery LOO** | **~$223** | |
| Phase 1C Battery LOO (34 batteries × 12 items × N=3,309) | ~$481 **(contingent)** | May be dropped or reduced — the §8 Layer-2 randomized ablation covers the same estimand; decision after Phase 1B (§9.1) |
| Phase 1C Shapley (11 multi-bin conditions × N=200) | ~$38 | |
| **Total Phase 1** | **~$742 max / ~$261 if Battery LOO dropped** | Assumes no prompt caching; verify OpenRouter prices at smoke time |

Reduction options if budget tightens: Battery LOO at N=1,500 (saves ~$263), attitudinal-bin batteries only (saves ~$209), or defer Battery LOO to Phase 1D.

---

## 12. Privacy

GSS data is public — no constraints. Cookiy pilot transcripts (`cookiy_transcripts/`, `responses/`, `responses_s2/`) and any audit files with direct quotes are gitignored and stay local; do not push to public repos. API keys (`Openai_api.txt`, `OpenRouter_api.txt`) are gitignored.

---

*All earlier design / OSF / brief / theory docs are in `archive/`. The supporting literature scan for the P0 / P1 / P2 prompt choices is at `archive/lit_review_prompt_variants_2026-05-15.md`. The Phase 1C tool spec is at `archive/tier1_tool_schemas.md`. The Park v2 PDF reference is `archive/2411.10109v2.pdf` (gitignored).*
