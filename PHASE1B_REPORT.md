# Phase 1B Results: What Survey Features Drive LLM Persona Predictions?

**Joyce Yu · Stanford GSB · GSBGEN390 · Advisor: Prof. Mohsen Bayati**
**Run: 2026-07-12 → 2026-07-14 · Report: 2026-07-14**
*Numbers computed from the raw prediction file (`phase1b_raw.parquet`, 159,804
rows) by `src/phase1b_analysis.py`; all tables in `phase1b_tables.xlsx`.
Design per RESEARCH_DESIGN.md §8 (locked 2026-07-12): Random × P1 cell,
N = 3,309 GSS 2024 respondents × 6 conditions, primary_eval (12 attitude
items). Headline cohort N = 3,109 (excludes the 200 Phase 1A selector
respondents); full N = 3,309 reported as sensitivity.*

---

## 1. The short version

1. **Baseline accuracy is unchanged from Phase 1A.** Full-persona normalized
   MAE is 0.264 (conservative; 0.255 optimistic) on the headline cohort. The
   sensitivity cohort gives 0.2646 — the selector-optimism gap is ~0.001,
   i.e., the Phase 1A cell choice was not noise-chasing.
2. **Removing any whole feature bin barely hurts.** Three of four bins have
   statistically reliable but tiny effects (largest: attitudinal,
   ΔMAE = +0.0095). Every bin's 95% CI lies entirely below our pre-registered
   "small effect" threshold of 0.02. The psychological bin contributes
   nothing (ΔMAE = +0.0008, n.s.). Feature information is highly redundant:
   the model reconstructs what a dropped bin carried from what remains.
3. **What signal exists is concentrated in a few specific batteries, not in
   categories.** In the randomized battery ablation, 3 of 34 batteries have
   CIs excluding zero: voting choice (+0.017), racial/ethnic origin (+0.016),
   abortion attitudes (+0.015); denominational identity is borderline
   (+0.013, CI [−0.0001, +0.028]). The other 30 are indistinguishable from
   zero. The politically diagnostic variables do the work; everything else
   is decoration.
4. **A ridge/logistic regression trained on the same features beats the LLM
   on 9 of 12 items** (e.g., POLVIEWS: regression 0.144 vs LLM 0.197). By
   the R2 module's definition, the LLM persona's apparent accuracy is mostly
   feature auto-correlation that any supervised predictor can exploit — we
   find no persona-reasoning premium in this setting. (The regression is an
   in-distribution upper bound by design: it trains on 4/5 of this year's
   respondents, cross-validated; the LLM is zero-shot.)
5. **Per-model patterns agree in direction, differ in noise.** Llama-4 shows
   all four bins significant; DeepSeek loads on behavioral; Kimi's deltas
   are noisy because its 4.9% parse-failure rate (§4) inflates conservative
   errors on both sides of each Δ.
6. **We are not drawing the Phase 1C conclusion here.** The battery ranking
   and its precision (per-battery n ≈ 650–770, CI half-width ≈ ±0.015) are
   what the §9 decision needs; we leave that discussion to our next meeting.

## 2. Design (one paragraph)

Each of 3,309 respondents was answered by one panel model chosen by a
seeded hash (share per model ≈ 25%; identical model across all six
conditions, so within-respondent differences are model-constant). The six
conditions: Full persona (140 features, own-battery excluded per R1), four
bin-LOO conditions (drop demographic / behavioral / psychological /
attitudinal), and `random_battery_drop` (R1 plus one battery drawn uniformly
per respondent-item; the drawn battery is recorded, so each battery's effect
is estimated from the pairs where it was absent vs the same pairs' Full
rows). Scoring: per-item normalized absolute error in [0,1]; parse failures
count as error 1.0 (conservative) with the optimistic variant alongside.
CIs: BCa bootstrap, B = 10,000, respondent clusters, seed 42;
Holm-Bonferroni across the four bins.

## 3. Results

**Bin-LOO ΔMAE vs Full** (headline cohort, conservative, combined column;
positive = dropping the bin hurts):

| Bin dropped | ΔMAE | 95% BCa CI | Holm-p |
|---|---|---|---|
| Attitudinal | +0.0095 | [+0.0059, +0.0132] | 0.0004 |
| Behavioral | +0.0066 | [+0.0032, +0.0099] | 0.0004 |
| Demographic | +0.0045 | [+0.0012, +0.0078] | 0.014 |
| Psychological | +0.0008 | [−0.0022, +0.0037] | 0.61 |

All CIs sit below the pre-registered small-effect threshold (0.02): reliable
direction, negligible magnitude.

**Battery ablation** (top of 34; paired ΔMAE on pairs where the battery was
drawn; parse-ok required in both arms):

| Battery | ΔMAE | 95% CI | n pairs |
|---|---|---|---|
| voting_choice | +0.0174 | [+0.0032, +0.0323] | 715 |
| racial_ethnic_origin | +0.0161 | [+0.0015, +0.0317] | 766 |
| abortion | +0.0147 | [+0.0037, +0.0288] | 654 |
| denominational_identity | +0.0132 | [−0.0001, +0.0277] | 717 |
| *remaining 30 batteries* | CIs include 0 | | ≈650–770 each |

Point estimates are pair-level means per the §8 estimand; CIs are BCa with
respondent clusters. (A respondent-macro estimator gives the same ranking
with slightly larger point estimates — the difference is respondents with
more on-ballot items getting proportionally more weight.)

Missingness check for the paired estimator: 25,029 pairs, 97.5% parse-ok in
both arms; arm-specific failures are balanced (305 ablated-only vs 299
full-only), so differential parse failure is not driving the estimates.

**LLM vs regression baseline** (per-item normalized MAE, headline cohort;
full table in `T4`): regression wins 9/12 items; LLM wins FEPOL (+0.022),
GUNLAW (+0.007), RACDIF1 (+0.006) — all within noise of a tie.

## 4. Data quality and caveats

- **Parse failure is one model's problem.** Kimi-K2 fails to emit a scorable
  answer on 4.9% of calls (other models ≤ 0.1%; overall 1.24%). This
  penalizes Kimi's ~25% of respondents under the conservative metric; the
  conservative-vs-optimistic headline gap is 0.0094. Raw model outputs are
  preserved in the JSON records for inspection.
- **Training-data contamination cannot be ruled out** — all four panel
  models postdate GSS 2024 fieldwork. Two observations bound the concern:
  (a) contamination inflates LLM accuracy, so finding 4 (no premium over a
  regression) survives it a fortiori; (b) the absolute level (0.264) should
  be read as an upper bound on clean-room performance. A release-date audit
  and aggregate-recall probes are cheap follow-ups if wanted.
- **Run repairs.** Network interruptions during the 45-hour run caused
  retry-exhaustion on 0.3% of calls; affected records were deleted and
  re-generated through the driver's resume path (call seeds are pure
  functions of (respondent, condition, item, model), verified identical to a
  single-pass run; audit script in repo). Final artifact: 19,854 records,
  zero failures, all integrity checks pass.

## 5. Data and reproduction

- **Raw data**: `phase1b_raw.parquet` — all 159,804 predictions (0.5 MB) —
  is in the shared Drive folder (*Phase 1B*), with
  [`report/phase1b_data_readme.md`](report/phase1b_data_readme.md) as the
  column dictionary and loading guide.
- **Tables**: [`outputs/phase1b_tables.xlsx`](outputs/phase1b_tables.xlsx) —
  T0 raw per-item tables plus every aggregate above. Sheets suffixed `_H`
  use the N=3,109 headline cohort; `_S` the N=3,309 sensitivity cohort.
- **Code**: [`src/phase1b_analysis.py`](src/phase1b_analysis.py) reproduces
  every number here from the parquet (BCa bootstrap B=10,000, seed 42);
  machine-readable results in
  [`outputs/phase1b_analysis.json`](outputs/phase1b_analysis.json).
