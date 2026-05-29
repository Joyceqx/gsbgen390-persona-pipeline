# Research Design — LLM Persona Feature Attribution on GSS 2024

**Author**: Joyce Yu · Stanford GSB · GSBGEN390 thesis-track · Spring 2026
**Advisor**: Prof. Mohsen Bayati
**Last updated**: 2026-05-28

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

### 3.3 Sensitivity eval — 118 items (Park-comparable, anchor-only)

The Park v2 GSS list minus 15 items retired or renamed in 2024. Used only on the GPT-4o anchor (N=100 subset) to produce the per-item raw-accuracy table side-by-side with Park v2 SI Table 3. NOT used in the headline LOO or selector.

---

## 4. Leakage hygiene

Two layers:

**R1 — battery-level structural exclusion**. When predicting any primary_eval item `X`, drop the entire battery containing `X` from the persona prompt. Mirrors Park v2 SI §6's BFI whole-trait-block hold-out. Implemented in `run_primary_one_respondent`; validated by `validate_taxonomy.py` check 7c.

**R2 — regression-baseline comparator**. A non-LLM Ridge (Likert) / multinomial Logistic (binary) baseline with 5-fold respondent-level CV on the same R1-respecting input pool. Estimates what a simple supervised predictor can extract from the same features. The LLM-vs-regression gap is the model-specific predictive value above a non-LLM baseline.

---

## 5. LLM panel (Phase 1A factorial)

**Locked 2026-05-28 per Bayati signoff.** The Phase 1A panel arm is a 4-model × 3-prompt factorial on N=200 panel respondents (`sample_respondents(200, seed=42)`).

### 5.1 Models (4 cheap + 1 anchor)

| Slot | Model | Provider | Why |
|---|---|---|---|
| Cheap | Qwen-2.5-72B-Instruct | Alibaba | Strong instruction-following |
| Cheap | DeepSeek-V3.1 | DeepSeek | Cheap, strong reasoning |
| Cheap | Llama-3.3-70B-Instruct | Meta | Western-trained (cross-family balance) |
| Cheap | Kimi K2 | Moonshot | Long-context, 4th family |
| Anchor | GPT-4o | OpenAI | Park v2 reference; runs only the N=100 selection subset, P0 only |

3 China-trained + 1 Western-trained on the cheap side. GPT-4o anchor is a second Western reference for Park comparison.

### 5.2 Prompts (3 format candidates for §7 selection)

| ID | Format | Citation |
|---|---|---|
| **P0** | 4-bin key-value list, 2nd-person framing | Park et al. 2024 v2 (arXiv:2411.10109), surveys-only condition |
| **P1** | 4-bin 1st-person prose clauses | Argyle, Busby, Fulda, Gubler, Rytting, Wingate (2023) "Out of One, Many", *Political Analysis* 31(3) |
| **P2** | 4-bin interview Q&A turns | Wang, Pyatkin, Bhagavatula, Choi (2025) "The Prompt Makes the Person(a)", *Findings of EMNLP 2025* |

These are three published persona-prompt formats from the LLM-on-survey literature. The set is **not a crossed design** over voice or structure factors and therefore does not support causal attribution of any single design feature; it is treated end-to-end as three format candidates, one of which §7 selects for Phase 1B. The Phase 1B headline reports MAE under the §7-selected (model, prompt) cell with no causal claim about prompt design.

P0 is the OSF-v1-era baseline implemented in `build_persona_prompt()`. P1 and P2 are new for Phase 1A. Full literature scan grounding these choices is at `archive/lit_review_prompt_variants_2026-05-15.md`.

### 5.3 Factorial structure (12 cells)

Each of the 200 panel respondents runs all 12 (model × prompt) cells × 5 conditions (Full + 4 single-bin LOO) × 12 primary_eval items (subject to ballot rotation). n_samples = 1 per call. The comparison across cells is within-respondent.

### 5.4 Random-model column (5th "model", 3 cells, post-hoc)

For each respondent `r` and each prompt `p`, a model is selected uniformly at random from {Qwen, DeepSeek, Llama-3.3, Kimi} via a seed=42 hash on `(r, p)`. The respondent's "Random × p" value is set equal to the corresponding (model, p) panel result. **Pure uniform random — no 50/50/50/50 balance constraint.** No new LLM calls.

The random column is a deployment-mode sensitivity comparator (each Phase 1B respondent in deployment sees one model; this estimates "if a Phase 1A respondent had only seen one randomly-assigned model"). It is reporting-only, **not a §12.2 selector input**.

### 5.5 GPT-4o anchor (P0 only)

N=100 selection-split subset, n_samples=2, **P0 only** (preserves Park v2 SI Table 3 comparability). Runs primary + 118 sensitivity items. One anchor invocation serves both Phase 1A and Phase 1B reporting.

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

### 6.2 Raw long-format database — ~120,000 rows

Schema (14 columns):

| Group | Column | Meaning |
|---|---|---|
| **Prediction** | `respondent_id` | seed=42 index into the GSS 2024 sample |
| | `model` | one of `Qwen`, `DeepSeek`, `Llama-3.3`, `Kimi`, `Random` — see note below |
| | `prompt` | one of `P0`, `P1`, `P2` |
| | `condition` | one of `Full`, `drop_demographic`, `drop_behavioral`, `drop_psychological`, `drop_attitudinal` |
| | `item` | primary_eval variable (e.g., `POLVIEWS`, `GUNLAW`, …) |
| | `true_code` | ground-truth integer code from GSS 2024 |
| | `pred_code` | model-output integer code (NULL if parse_ok=false) |
| | `parse_ok` | boolean — did the model output parse to a valid code? |
| | `abs_err` | `|pred_code − true_code|` on Likert items; 0/1 on binary (NULL if parse_ok=false) |
| | `sample_position` | 1 (cheap-panel n=1) or 1/2 (GPT-4o anchor n=2) |
| **Call metadata** | `timestamp` | UTC datetime of the LLM call |
| | `cost_usd` | per-call cost in USD (computed from token counts × provider rate) |
| | `tokens_in` | input token count |
| | `tokens_out` | output token count |

Example rows:

| respondent_id | model | prompt | condition | item | true_code | pred_code | parse_ok | abs_err | sample_position | timestamp | cost_usd | tokens_in | tokens_out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | Qwen | P0 | Full | POLVIEWS | 3 | 3 | true | 0 | 1 | 2026-05-29T14:32:01Z | 0.00041 | 928 | 3 |
| 0 | Qwen | P0 | drop_demographic | POLVIEWS | 3 | 2 | true | 1 | 1 | 2026-05-29T14:32:04Z | 0.00038 | 858 | 3 |
| 0 | Qwen | P0 | Full | PARTYID | 1 | 1 | true | 0 | 1 | 2026-05-29T14:32:07Z | 0.00041 | 928 | 3 |
| 0 | **Random** | P0 | Full | POLVIEWS | 3 | 3 | true | 0 | 1 | (= Qwen row's metadata) | | | |

**`model="Random"` row construction**: for each `(respondent_id, prompt)`, a seed=42 hash uniformly picks one of the four real models (no balance constraint). The `Random × prompt` rows are copies of that picked model's rows with `model` re-labeled to `Random`. No new LLM calls; the timestamp / cost / token columns are copied from the source row for auditability.

**Volume**: 200 respondents × 5 (4 cheap models + Random) × 3 prompts × 5 conditions (Full + 4 single-bin LOO) × ~8 ballot-on items (GSS ballot rotation; see §3.1) ≈ **120,000 rows**. Stored at `outputs/phase1a_raw.parquet` (DuckDB-compatible).

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

Same 14-column schema. Single (model, prompt) cell × N=3,309 × 5 conditions × ~8 items ≈ **132,000 rows**. Stored at `outputs/phase1b_raw.parquet`. No Random column at the Phase 1B stage (deployment is the single selected cell).

---

## 7. Selector: Phase 1A → Phase 1B

Joint (model, prompt) cell selection. See `select_phase1b_model.py`.

```
candidate cells = {(m, p) : m ∈ {Qwen, DeepSeek, Llama-3.3, Kimi}, p ∈ {P0, P1, P2}}  # 12 cells

# Per-item normalized abs-err so that mixed scales (binary, Likert-3/4/5/7) contribute
# comparably. Each item's normalized abs-err is in [0, 1]; macro-average runs
# over respondents and then over items.
normalized_abs_err(respondent, item) = abs(pred_code − true_code) / (max_code − min_code)
primary_score(cell) = mean over respondents of (mean over Full-condition items in their ballot of
                                                normalized_abs_err)

# Scoring uses the FULL N=200 panel cohort (no 100/100 split — the OSF-era
# post-selection-inference defense is dropped per 2026-05-28 Bayati signoff).

DQ-1 (parse-fail ceiling):    parse_failure_rate ≤ 30% per cell
DQ-3 (mode-collapse guard):   for each primary_eval item i, var(cell_i) / var(human_i) ≥ 0.30
                              cell fails if > 50% of items fail the floor
                              human variance reference: outputs/primary_eval_human_variance_2024.json

argmin primary_score among DQ-passers.
Tie-break (within 5% of best score): lowest cost × (1 + parse_fail_rate).
Tie on both quality + cost: Qwen × P0 named fallback.
All cells fail DQ: PAUSE — Phase 1B does not proceed.
```

**Honest framing of the tiebreak**: per-cell normalized MAE for cheap LLMs on GSS attitude prediction typically sits in the range ≈ 0.20–0.35 (cf. Park v2 SI Table 3 surveys-only baseline and comparable LLM-on-Likert work). The 5%-relative tiebreak window around best MAE ≈ 0.25 is therefore ≈ 0.013 — narrower than the per-cell standard error of ≈ 0.071 (N=200, computed across respondents). When the tiebreak window is narrower than one SE, two things follow:

  (i) The argmin almost always finds a "winner" outside the tiebreak band, so the cost × (1 + parse_fail_rate) tiebreaker is rarely triggered. The selector behaves as quality-primary in practice — the Qwen × P0 fallback only fires if all DQ-passing cells also tie on cost.

  (ii) That winner is largely noise-driven. With 12 cells and SE ≈ 0.07 on a quantity bounded in [0, 1], the expected gap between rank-1 and rank-2 is on the order of ~0.05 by chance alone even when all 12 cells share the same true MAE. Treat the headline cell as "best on this cohort" rather than "best in expectation".

Mitigations: report the full 180-row summary (§6.1) alongside the headline so the reader can audit the cluster of near-ties; report the headline MAE with paired-respondent bootstrap CI; bind the §10 LOO ablation to the chosen cell rather than re-selecting per LOO condition.

**Binary sensitivity check** (post-selection, mandatory). After §7 picks the headline cell, report that cell's **exact-match accuracy on each of the 5 binary primary_eval items** (ABANY, CAPPUN, GUNLAW, FEPOL, RACDIF1) alongside the headline normalized MAE. Per-item normalization makes binary errors equal-weighted in `primary_score`, but a cell can still have a low aggregate MAE while collapsing specifically on one or two binary items. If any of the 5 binary items has exact-match accuracy < 0.50 (worse than chance) on the held-out Phase 1B sample, that item is flagged in the limitations section as a model-specific failure on the selected cell. This is reporting only — it does NOT trigger a selection rerun.

---

## 8. Phase 1B

Single §7-selected (model, prompt) cell. Primary_eval only, n_samples=1, Full + 4-bin LOO conditions.

**Headline cohort**: N=3,109 — the full 2024 GSS cross-section **minus** the N=200 panel respondents used by the §7 selector. Excluding the selector cohort removes the in-sample optimism on the cell chosen by argmin. The 200 selector respondents are reusing the Phase 1A artifact (already paid), so the exclusion costs no LLM calls — it only changes which rows are aggregated for the headline. Cohort assignment is deterministic via `sample_respondents(200, seed=42)` ∩ `gss_cross_section_2024.index`.

**Sensitivity cohort**: full N=3,309 (including the 200 selector respondents). Reported alongside the headline. Expected gap is small because 200 / 3,309 ≈ 6%, but the gap itself is the empirical optimism estimate and worth reporting; a large gap is a flag that the §7 winner was substantially noise-driven.

**Headline**: 4-bin LOO ΔMAE per bin (drop bin, re-score, take Δ vs. Full). Paired-respondent bootstrap CIs (B=10,000 BCa) on the N=3,109 cohort. When reporting bin rankings, apply Holm-Bonferroni at α=0.05 across the 4 bins.

**Effect size thresholds** (Funder & Ozer 2019): small <0.02 ΔMAE on the Likert scale; modest 0.02–0.05; substantive ≥0.05. Substantively interpret a bin's contribution only when its ΔMAE CI excludes the small threshold.

---

## 9. Phase 1C (co-primary)

Two analyses on the Phase 1B records:

### 9.1 Battery LOO — 34 batteries × 12 items × N=3,309

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
| `src/select_phase1b_model.py` | OSF-v1 single-model selector with DQ gates; kept as legacy reference for the pre-factorial design. |
| `src/select_phase1b_cell.py` | §7 joint (model, prompt) cell selector. Reads `outputs/phase1a_raw.parquet`. Implemented + 6 self-tests pass. |
| `src/write_phase1a_parquet.py` | §6.2 long-format parquet writer + Random column. Implemented + 6 self-tests pass. |
| `src/gss_driver.py` | Orchestrator with `--phase1a` / `--phase1b` / `--phase1b-anchor` modes; implemented + tested for single-prompt panel. **3-prompt factorial extension pending.** |
| `src/battery_loo.py`, `src/shapley_decomposition.py` | Phase 1C analyzers; implemented + self-tested. **Orchestration drivers (`--battery-loo`, `--shapley`) pending.** |
| `src/regression_baseline.py` | R2 baseline (Ridge + multinomial Logistic, 5-fold CV); implemented + tested |
| `src/validate_taxonomy.py`, `src/lint_writeup_language.py` | Lint / validation utilities; implemented + tested |

### 10.2 Pipeline extensions needed for the Bayati-confirmed factorial

Before launching paid Phase 1A:

1. **`src/gss_driver.py --phase1a`**: extend to iterate over 3 prompts in addition to 4 models. Each call now varies on `(respondent, condition, item, prompt, model)`. Output records include `prompt_id` in metadata.
2. **`src/select_phase1b_cell.py`** (new file, sibling of the OSF-v1 single-model `select_phase1b_model.py`): scores the 12 (model, prompt) cells jointly. Per-cell DQ-1 + DQ-3, per-item normalized MAE, 5%-relative quality tiebreak, cost-driven secondary tiebreak, Qwen × P0 named fallback. Random column (§5.4) aggregated post-hoc as 3 normalized-MAE reports — not a selector input.
3. **Phase 1A output writer (`src/write_phase1a_parquet.py`)**: emits `outputs/phase1a_raw.parquet` (long-format DB per §6.2) after the 3-prompt loop in `--phase1a`. Random column rows generated deterministically via SHA-256(seed=42 | rid | prompt). 180-row §6.1 summary is derivable from the parquet in one pandas/SQL groupby; not materialized as a separate artifact until needed.
4. **`src/gss_driver.py --phase1b`**: accept `--phase1b-prompt` in addition to `--phase1b-model` so the selected (model, prompt) cell is fully addressable.

Estimated effort: ~2-3 days of careful coding + self-tests on synthetic fixtures before paid runs.

### 10.3 How to run (after the extensions above land)

```bash
# Pre-flight self-tests
python3 src/validate_taxonomy.py
python3 src/select_phase1b_cell.py --self-test       # 6 joint-cell tests (rationales × 5 + random column)
python3 src/write_phase1a_parquet.py --self-test     # 6 writer tests (relabel, parse_fail, binary, random, count, roundtrip)
python3 src/battery_loo.py --self-test
python3 src/shapley_decomposition.py --self-test
python3 src/gss_pipeline.py --test-aggregation
python3 src/prompt_variants.py --self-test           # 6 single-respondent prompt tests
python3 tests/preflight_phase1a.py                   # N=200 panel × 12 batteries × 3 prompts coverage

# 1. Smoke (~$3, ~5 min)
python3 src/gss_driver.py --smoke

# 2. Phase 1A factorial + GPT-4o anchor (~$199, ~24 hr)
python3 src/gss_driver.py --phase1a              # 4 models × 3 prompts × N=200
python3 src/gss_driver.py --phase1b-anchor       # GPT-4o × P0 × N=100

# 3. §7 joint (model, prompt) cell selector (free, <1 min)
python3 src/select_phase1b_cell.py outputs/phase1a_raw.parquet

# 4. Phase 1B (~$71, ~3-7 days)
#    Runs on full N=3,309; headline aggregation excludes the §7 selector cohort
#    (N=3,109 disjoint), full cohort (N=3,309) reported as sensitivity. See §8.
python3 src/gss_driver.py --phase1b \
    --phase1b-model <slug> \
    --phase1b-prompt <prompt_id>

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
| Smoke | ~$3 | 1 respondent × 1 model × 3 prompts × 5 conditions |
| Phase 1A factorial (4 models × 3 prompts × N=200) | ~$51 | Cheap models at ~$0.000356/call |
| GPT-4o anchor (P0 only, N=100, primary + sensitivity, n=2) | ~$148 | One run serves Phase 1A + 1B reporting |
| Phase 1B (selected cell × N=3,309) | ~$71 | |
| **Subtotal pre-Battery LOO** | **~$273** | |
| Phase 1C Battery LOO (34 batteries × 12 items × N=3,309) | ~$481 | |
| Phase 1C Shapley (11 multi-bin conditions × N=200) | ~$38 | |
| **Total Phase 1** | **~$792** | Assumes no prompt caching; verify OpenRouter prices at smoke time |

Reduction options if budget tightens: Battery LOO at N=1,500 (saves ~$263), attitudinal-bin batteries only (saves ~$209), or defer Battery LOO to Phase 1D.

---

## 12. Privacy

GSS data is public — no constraints. Cookiy pilot transcripts (`cookiy_transcripts/`, `responses/`, `responses_s2/`) and any audit files with direct quotes are gitignored and stay local; do not push to public repos. API keys (`Openai_api.txt`, `OpenRouter_api.txt`) are gitignored.

---

*All earlier design / OSF / brief / theory docs are in `archive/`. The supporting literature scan for the P0 / P1 / P2 prompt choices is at `archive/lit_review_prompt_variants_2026-05-15.md`. The Phase 1C tool spec is at `archive/tier1_tool_schemas.md`. The Park v2 PDF reference is `archive/2411.10109v2.pdf` (gitignored).*
