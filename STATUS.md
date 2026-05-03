# Project Status — GSBGEN390 Phase 1 Underway

**Last updated:** 2026-05-02 (Phase 1 build phase: GSS data + loader + taxonomy locked; pipeline adapter next)
**Maintained by:** Joyce Yu + collaborating Claude session

This document is the single-source-of-truth for what's done, what's pending, and how to pick up the project in a fresh terminal, Claude Code CLI, or Claude Cowork session.

---

## TL;DR for a fresh session

The project has **two sequential phases**, both scoped at the Bayati meeting (2026-05-02):

### ✅ Pilot phase (completed 2026-04-30)
End-to-end replication of Park et al. at N=2 + N=1 via Cookiy. Pipeline + dashboard + leakage audit shipped. GitHub repo: https://github.com/Joyceqx/gsbgen390-persona-pipeline. Live dashboard: https://joyceqx.github.io/gsbgen390-persona-pipeline/

### 🟡 Phase 1: GSS public-data feature-importance analysis (IN PROGRESS, 2026-05-02→)
**Goal**: attack the GSS-attitudes row of Park's outcome × feature-category matrix at N≈1,500, using free GSS public panel data (no Cookiy collection needed).

**Locked design (Path A\*)**:
- **Snapshot prediction** on a single GSS wave (2024 cross-section, N=3,309)
- **Primary eval (Path B)**: 12 curated high-variance attitudinal items — supports meaningful 4-bin LOO
- **Sensitivity eval (Path A)**: Park's full ~118 GSS items — for per-item Park-comparable accuracy
- **Feature pool**: 140 GSS variables partitioned into 4 bins (23 demographic / 29 behavioral / 8 psychological / 80 attitudinal)
- **Raw accuracy** as primary metric (no test-retest normalization in Phase 1; deferred to Phase 2)
- **Persona self-consistency** (temp=0.7 multi-sample) reported as supplementary stability check
- **Pre-registration** on OSF before Phase 1b launches

**State**:
- ✅ GSS 2024 data downloaded (973 unique variables × 75,699 rows from cumulative; 3,309 in 2024)
- ✅ `gss_loader.py` reads the 3-batch fixed-width extract; verified 22/22 key Park variables present with correct labels
- ✅ `gss_feature_taxonomy.json` locked + validated (all 140 features + 12 primary_eval + 118 sensitivity_eval present in data; bins disjoint)
- 🟡 `gss_pipeline.py` (persona-prompt builder + LLM dispatcher + scorer) — next
- 🔒 N=10 smoke test
- 🔒 OSF pre-registration
- 🔒 Phase 1a (N=100, ~$30) sanity check
- 🔒 Phase 1b (N=1500, ~$300-500) primary

### 🔮 Phase 2: targeted Cookiy collection (planned, not started)
Will cover BFI-44 personality + behavioral game outcomes that GSS doesn't measure. Includes 2-week recontact for proper test-retest baseline. Smaller N (~30-100). Design in `thesis_phase2_design.md`.

---

## What changed 2026-05-02 (Phase 1 build session)

### Direction-setting
1. ✅ **Bayati meeting**: Phase split (GSS-first → targeted Cookiy) and 4-bin taxonomy endorsed; pre-registration committed to before Phase 1b.
2. ✅ **Path A\* locked**: Path B as primary (12 items, supports LOO), Path A as sensitivity (Park's ~118 items, per-item comparability). Same data, two analytical lenses.
3. ✅ **Snapshot wave structure**: single-wave prediction on GSS 2024 (avoids panel-evolution and cross-wave leakage). Raw accuracy primary; test-retest normalization deferred to Phase 2.
4. ✅ **Disjoint-set rule clarified**: primary-pass features = (declared bin lists) MINUS primary_eval only; sensitivity-pass handles per-item leakage separately. Resolves the otherwise-empty-psychological-bin problem.

### Data + loader
5. ✅ **GSS 2024 data downloaded** via GSS Data Explorer. The 973-variable extract is split into 3 batches by GSS DE; combined locally to a single 973-column DataFrame.
6. ✅ **`gss_loader.py`** — parses each batch's `.do` script for column ranges + variable labels + value labels; reads the corresponding `.dat` fixed-width file; merges 3 batches horizontally into one DataFrame at 75,699 rows × 973 columns. Handles missing-value codes (-100, -99, etc.) explicitly. Namespaced label sets per batch to avoid label-set name collisions across batches.
7. ✅ **Verified**: 22/22 key Park variables present with correct labels (POLVIEWS=4 → "Moderate, middle of the road"; HAPPY=3 → "Not too happy"; SEX=1 → "MALE"; etc.). N=3,309 respondents in 2024.

### Taxonomy
8. ✅ **`gss_feature_taxonomy.json`** locked:
   - 12 primary_eval items (one per construct family, ~auto-correlation-minimized)
   - 118 sensitivity_eval items (Park's list minus 15 retired/renamed in 2024)
   - 140 feature variables in 4 bins (23 demographic / 29 behavioral / 8 psychological / 80 attitudinal)
9. ✅ **`validate_taxonomy.py`** — confirms (a) every claimed variable exists in the data, (b) bins are mutually disjoint, (c) per-respondent coverage. Median respondent answered: 8/12 primary_eval, 20/23 demographic, 20/29 behavioral, 4/8 psychological, 40/80 attitudinal items.

### Doc updates locked
10. ✅ `gss_phase1_design.md` rewritten with locked decisions (snapshot, raw accuracy, Path A\*, disjoint-set rule, 2-week plan).
11. ✅ `gss_variables_to_download.md` documenting the GSS DE workflow + variable list (now used as the data download record).

### Open work (not started yet)
- **#10 `gss_pipeline.py`** — persona-prompt builder + LLM dispatcher + scorer adapted for GSS rows. Reuses pilot's retry/backoff and self-consistency machinery. Needed before any LLM calls.
- **#6 N=10 smoke test** — verify pipeline end-to-end at minimum scale (~$1).
- **#7 OSF pre-registration** — drafted before Phase 1b; locks taxonomy, eval list, primary metric, exclusion rules, secondary analyses.
- **#8 Phase 1a (N=100)** — sanity check.
- **#9 Phase 1b (N=1,500)** — primary analysis.

---

## What changed in earlier sessions (2026-04-30 evening — pilot phase wrap)

### Major fixes / additions to pipeline
1. ✅ **Path reconciliation** — transcripts copied to `responses/R{1,2}/transcript.txt` and `responses_s2/R1/transcript.txt`.
2. ✅ **Demographics JSON** per respondent (`responses/R1/demographics.json` etc.) — hand-extracted from transcripts because pipeline previously had only `{respondent_id}` for Condition A.
3. ✅ **Self-description anchors** extended to match real Cookiy moderator phrasings ("a little bit about yourself", "in a short paragraph", etc.) — was silently failing on P1.
4. ✅ **Truth-source unification** — pipeline now overrides internal parser output with the audited `eval_answers_extracted.csv` (single gold source).
5. ✅ **TypeError defense** in metrics-table writer.
6. ✅ **Eval-stem-based splitter** for both Study 1 and Study 2 — replaces fragile verbal-transition anchors. Verified no eval Q&A leaks into interview_text/construction_qa segments.

### Pipeline run + LOO ablation
7. ✅ **`run_notebook_local.py`** — runner that executes `persona_pipeline.ipynb` outside Colab. Patches Cell 8 (file upload → local read), skips Jupyter magics (`!pip`), stubs `display()`, **adds exponential-backoff retry around `_call_openai`** (essential — TPM=30K limit triggers ~3-5 times per run on this account), saves `persona_answers_full.json` with per-item primary + samples.
8. ✅ **12 conditions ran**: Study 1 ×3 conditions × 2 respondents + Study 2 ×6 conditions (A, D, +4 LOO) ×1 respondent. ~9 min total wall-clock, ~$4 API cost.

### Leakage audit (defense against in-session priming)
9. ✅ **`leakage_audit.json`** — manually tagged each of 15 eval items per respondent as STRONG / SOFT / CLEAN with evidence quotes from the transcript.
   - P1 STRONG: `bfi_c, polviews, happy` (3 items)
   - P2 STRONG: `bfi_c, polviews, satjob` (3 items)
   - S2 STRONG: 0 (survey arm has structurally less leakage)
10. ✅ **`rescore_with_leakage_audit.py`** — re-scores each condition under three filters: `full_eval / strict_clean / broad_clean`. Output: `metrics_with_leakage_audit.csv`.
11. ✅ **`make_robustness_chart.py`** — produces `chart_robustness.png` (3-bar groups per condition: full / strict / broad MAE), separated into Study 1 and Study 2 panels.

### Fact corrections to docs
12. ✅ **Park used an AI interviewer, not a human one.** The user originally believed Park used human interviewers (an error inherited from `replication_scoping.md` and `interview_quality_audit.md`). Park 2024 directly states they built a custom voice-to-voice AI agent around the AVP protocol with adaptive follow-ups, averaging 6,491 words/transcript. Fixed in:
   - `README.md` (front-door description)
   - `replication_scoping.md` (comparison table + Open Question 2)
   - `interview_quality_audit.md` (§1, §3.1, §3.5, table row)
   - `EXPLAIN_ZH.md` (主持人 row in comparison table)
   - The remaining "human" references in docs are now intentional (AVP protocol historical origin, future-design hypothetical alternative, "vs human moderator" comparisons).

---

## Headline results (from `metrics_per_respondent.csv`)

### Likert MAE per condition (lower = closer to truth)

| Arm | Resp. | A demo | B desc | C/D | LOO best | LOO worst |
|---|---|---|---|---|---|---|
| Study 1 | P1 | 0.83 | 0.92 | **C: 0.08** | — | — |
| Study 1 | P2 | 1.17 | 0.75 | **C: 0.00** | — | — |
| Study 2 | S2-P1 | 0.50 | — | D: 0.83 | drop attitudinal: 0.58 | drop demographic: 1.17 |

### Leakage-filter robustness (`metrics_with_leakage_audit.csv`)

|  | full (15) | strict-clean | broad-clean |
|---|---|---|---|
| P1/A | 0.83 | 0.70 | 1.00 |
| P1/B | 0.92 | 0.80 | 1.00 |
| **P1/C** | **0.08** | **0.10** | **0.00** |
| P2/A | 1.17 | 1.20 | 1.00 |
| P2/B | 0.75 | 0.80 | 0.75 |
| **P2/C** | **0.00** | **0.00** | **0.00** |

**Caveat**: broad-clean for P2 has only 4 items left (very noisy at MAE=0.00). Headline figure should be **strict-clean** (10 items kept). At strict-clean, C still beats A by 0.6–1.2 MAE per respondent.

---

## Current work tree (updated 2026-05-02)

```
GSBGEN390/
│
├── ── DESIGN + NARRATIVE DOCS ──
├── README.md                          ← front door
├── STATUS.md                          ← this file (single-source-of-truth)
├── CLAUDE.md                          ← guidance for AI assistants in this folder
├── PRIMER.md                          ← 1-2 page Joyce self-intro
├── MEETING_HANDOUT.md                 ← one-page brief for Bayati meeting (pilot)
├── WRITEUP.md                         ← 3-5 page formal pilot write-up
├── progress_report.md                 ← pilot sprint narrative
├── replication_scoping.md             ← design rationale + Park's actual numbers
├── FUTURE_DESIGN.md                   ← open design questions for the thesis-stage
├── BUSINESS_LANDSCAPE.md              ← market scan
├── LIT_REVIEW.md                      ← academic literature review
├── EXPLAIN_ZH.md                      ← Chinese project explanation
├── CODE_WALKTHROUGH_ZH.md             ← Chinese walkthrough of persona_pipeline.py
├── COLAB_RUN_GUIDE.md                 ← Colab fallback instructions
│
├── ── PHASE 1 (GSS-PUBLIC) DESIGN + ARTIFACTS ──
├── gss_phase1_design.md               ← Phase 1 locked design (Path A*, snapshot, raw acc)
├── gss_variables_to_download.md       ← record of GSS Data Explorer variable list
├── gss_feature_taxonomy.json          ← LOCKED: 12 primary_eval, 118 sensitivity_eval, 140 features × 4 bins
├── gss_loader.py                      ← reads 3-batch GSS extract → pandas DataFrame; label-set namespacing
├── validate_taxonomy.py               ← sanity-check: variables exist, bins disjoint, coverage stats
│   (next: gss_pipeline.py, gss_phase1_results.csv, gss_pipeline_logs/)
│
├── ── PHASE 2 (COOKIY-TARGETED) DESIGN ──
├── thesis_phase2_design.md            ← Phase 2 design (BFI + econ games, smaller N + 2-week recontact)
│
├── ── PILOT PHASE COOKIY ARTIFACTS ──
├── cookiy_brief.md                    ← Study 1 brief (interview arm)
├── cookiy_brief_study2.md             ← Study 2 brief (survey arm)
├── cookiy_guide_session1.md           ← Cookiy auto-generated discussion guide (S1)
├── cookiy_guide_session2.md           ← Cookiy auto-generated discussion guide (S2)
├── eval_battery.json                  ← 15-item held-out eval, with regex anchors
├── eval_answers_extracted.csv         ← parsed truth: 15 items × 3 respondents (GOLD)
├── construction_answers_extracted.csv ← parsed truth: 18 construction items × 1 respondent
├── metrics_per_respondent.csv         ← notebook scoring: 12 conditions × full eval metrics
│
├── ── PILOT PIPELINE CODE ──
├── persona_pipeline.py                ← script-style pipeline (responses/ layout)
├── persona_pipeline.ipynb             ← CANONICAL pilot pipeline (31 cells, incl. LOO)
├── run_notebook_local.py              ← runner: executes the notebook outside Colab
├── parse_eval_answers.py              ← smart parser using moderator confirmations as gold
├── parse_construction_answers.py      ← parser for Study 2 construction items
├── rescore_with_leakage_audit.py      ← post-hoc rescoring under STRONG/SOFT/CLEAN filters
├── make_robustness_chart.py           ← chart generator for the leakage audit
├── build_site_data.py                 ← CSV→JSON for docs/data/
├── build_notebook.py                  ← (Cowork-built — assembles persona_pipeline.ipynb)
│
├── ── GITIGNORED (PII + secrets) ──
├── interview_quality_audit.md         ← Study 1 transcript quality audit (verbatim quotes)
├── survey_quality_audit.md            ← Study 2 transcript quality audit (verbatim quotes)
├── leakage_audit.json                 ← per-item leakage tags + evidence quotes
├── Openai_api.txt                     ← API key
├── 2411.10109v2.pdf                   ← Park v2 paper (kept local for reference)
│
├── cookiy_transcripts/                ← raw Cookiy outputs (verbatim PII)
│   ├── study1_interview_p{1,2}.{txt,json}
│   ├── study2_survey_p1.{txt,json}
│   └── study{1,2}_report.{md,json}
│
├── responses/        R{1,2}/{transcript.txt,demographics.json}
├── responses_s2/     R1/{transcript.txt,demographics.json}
│
├── data/gss/                          ← GSS Data Explorer extracts (NOT public; large; partly PII)
│   ├── 390data1/{batch1,batch2,batch3}/  ← active extract: 973 vars × 75,699 rows
│   │   ├── GSS.dat   (fixed-width data)
│   │   ├── GSS.do    (Stata import script with col specs + labels)
│   │   └── post_processing_output.json
│   └── archive/                       ← older extract attempts
│
├── ── PIPELINE OUTPUTS ──
├── outputs/                           ← all pilot-pipeline-derivative artifacts
│   ├── metrics_with_leakage_audit.csv
│   ├── chart_robustness.png
│   ├── persona_answers_full.json      (gitignored — embeds prompts)
│   └── logs/                          (gitignored — runner logs)
│
├── ── DASHBOARD ──
├── docs/                              ← static GitHub Pages dashboard for pilot
│   ├── index.html, style.css, app.js, README.md
│   └── data/
│       ├── metrics_per_respondent.json
│       ├── metrics_with_leakage_audit.json
│       ├── metrics_aggregate.json
│       └── eval_answers_extracted.json
│
├── ── HISTORICAL ──
├── archive/                           ← stale pre-pivot files (pilot history)
├── test/                              ← synthetic transcript fixtures
│
└── (also gitignored: GSBGEN390_Application_*.docx, __pycache__/, *.pdf)
```

### Where each file is read from / written to

#### Pilot phase (Cookiy)

| File | Read by | Written by |
|---|---|---|
| `eval_battery.json` | notebook, `persona_pipeline.py` | (manual) |
| `eval_answers_extracted.csv` | `rescore_with_leakage_audit.py`, `build_site_data.py` | `parse_eval_answers.py` |
| `construction_answers_extracted.csv` | (reference) | `parse_construction_answers.py` |
| `metrics_per_respondent.csv` | `build_site_data.py` | notebook cell 30 |
| `outputs/metrics_with_leakage_audit.csv` | `make_robustness_chart.py`, `build_site_data.py` | `rescore_with_leakage_audit.py` |
| `outputs/persona_answers_full.json` | `rescore_with_leakage_audit.py` | `run_notebook_local.py` (end-of-run) |
| `outputs/chart_robustness.png` | (visual) | `make_robustness_chart.py` |
| `outputs/logs/run_*.log` | (manual review) | shell `tee` from `run_notebook_local.py` |
| `leakage_audit.json` | `rescore_with_leakage_audit.py` | (manual tagging — Joyce + Claude) |
| `docs/data/*.json` | `docs/app.js` (browser fetch) | `build_site_data.py` |

#### Phase 1 (GSS public)

| File | Read by | Written by |
|---|---|---|
| `data/gss/390data1/batch{1,2,3}/GSS.{dat,do}` | `gss_loader.py` | (downloaded from GSS Data Explorer 2026-05-02) |
| `gss_loader.py` | `validate_taxonomy.py`, `gss_pipeline.py` (next) | (manual) |
| `gss_feature_taxonomy.json` | `validate_taxonomy.py`, `gss_pipeline.py` (next) | (locked manual + Bayati endorsement 2026-05-02) |
| `validate_taxonomy.py` | (manual integrity check) | — |
| `gss_pipeline.py` (NOT YET WRITTEN) | (top-level driver) | — |
| `outputs/gss_phase1_results.csv` (NOT YET WRITTEN) | — | `gss_pipeline.py` |

---

## How to resume in a fresh terminal / new Claude Cowork session

### To re-read everything and pick up the story (current Phase 1 build):
```bash
cd ~/Documents/GSBGEN390
# Read in this order for Phase 1 context:
#   1. STATUS.md (this file) — current state
#   2. CLAUDE.md — guidance for AI assistants
#   3. gss_phase1_design.md — Phase 1 locked design
#   4. gss_feature_taxonomy.json — eval and feature lists
# Then for pilot context:
#   5. MEETING_HANDOUT.md, WRITEUP.md, progress_report.md
```

### Phase 1 commands (current session)

**Validate the loaded GSS extract + taxonomy** (no API):
```bash
python3 gss_loader.py            # smoke test loader, ~30s for 75K-row .dat parse
python3 validate_taxonomy.py     # check variable presence + bin disjointness + coverage
```

**Run Phase 1 pipeline** (NOT YET BUILT — task #10):
```bash
# Will be: python3 gss_pipeline.py --n 10        # smoke test, ~$1
# Will be: python3 gss_pipeline.py --n 100       # Phase 1a sanity, ~$30
# Will be: python3 gss_pipeline.py --n 1500      # Phase 1b primary, ~$300-500
```

### Pilot phase commands (still works, for the Cookiy pipeline)

**Re-run pilot pipeline** (~9 min, $3-5 in API):
```bash
export OPENAI_API_KEY=$(cat Openai_api.txt)
python3 -u run_notebook_local.py 2>&1 | tee outputs/logs/run_$(date +%Y%m%d_%H%M).log
python3 rescore_with_leakage_audit.py
python3 make_robustness_chart.py
python3 build_site_data.py
```

**Re-run rescoring only** (no API, ~1s) — if `outputs/persona_answers_full.json` exists:
```bash
python3 rescore_with_leakage_audit.py
python3 make_robustness_chart.py
python3 build_site_data.py
```

### Known runtime gotchas

**Phase 1 / GSS:**
- GSS DE splits the 973-variable extract into **3 batches** — `gss_loader.py` merges them horizontally. If you re-download, expect 3 batch folders.
- Label-set names (e.g., `GSP002X`) **collide across batches** with different contents. The loader namespaces them per-batch (`b0_GSP002X`, `b1_GSP002X`) to avoid wrong labels.
- GSS missing-value codes are negative integers in `{-100, -99, -98, -97, -96, -95, -90, -80, -70, -60, -50, -40}`. Loader exposes `is_missing()` helper. **Ballot rotation** means many GSS items aren't asked of every respondent; pre-registration must commit to handling.

**Pilot phase:**
- TPM rate limit: account is at 30K tokens/min for gpt-4o. Condition C prompts hit this; the runner has retry+exponential-backoff.
- Cell 8 in the notebook uses `google.colab.files.upload()` which doesn't work locally. The runner replaces this with disk reads from `cookiy_transcripts/`.
- Cell 16 uses `display()` (Jupyter built-in). The runner stubs this to `print()`.
- Jupyter magics (`!pip`, `%`) in cells are silently skipped by the runner.
- `LLM_CACHE` is in-memory only — every fresh process re-runs all 240+ API calls. The runner persists `persona_answers_full.json` end-of-run; the rescoring script reads from that without API calls.

---

## Pending work (post-meeting decisions)


1. **3-5 page formal writeup** — methods, pipeline, results, leakage audit, comparison to Park v2's per-outcome 74/83/82/86% (with caveats: ≈ tie on GSS only; surveys lag by 0.15 BFI / 0.28 games), limitations, next steps. Awaits Bayati feedback.
1a. **Phase 1 — GSS public-data feature-importance analysis** (proposed; see [`gss_phase1_design.md`](gss_phase1_design.md)). Uses GSS Three-Wave Panel 2010-2014 (N≈1,500), provides first test-retest-normalized-accuracy comparison to Park's 0.82-0.83. Covers GSS-attitudes outcome row only. Budget ~$300-500, timeline 1-4 weeks. Awaiting Bayati endorsement.
1b. **Phase 2 — Interview-decomposed feature-importance study** (proposed; see [`thesis_phase2_design.md`](thesis_phase2_design.md)). Prolific N=20-30, 30-45 min modular long interview (4 modules ↔ 4 feature bins), 2-week wait, BFI-44 + behavioral-game vignettes + GSS as held-out outcomes. LOO ablation operates **at the interview-content level** — decomposes Park's "interview-only" condition into pre-registered content bins. Covers BFI (0.15 gap) and games (0.28 gap) rows that Phase 1 cannot. Requires platform pivot to Prolific + self-hosted OpenAI Realtime API moderator (Cookiy 15-min cap incompatible). Budget ~$1,500-1,750, timeline 7-9 weeks. Awaiting Bayati endorsement of platform pivot + N + module structure.
2. **Multi-seed run-variance estimate** — re-run pipeline 5-10 times with different seeds to bound LOO ranking instability at N=1. Honest answer to "how reliable is this LOO?"
3. **2-week-separated re-collection (likely needed)** — Cookiy can't recontact panel respondents, so this requires a different platform (Prolific custom script, or recruiting in-house). Without this, the C-condition's win is technically defensible only via the leakage-audit argument, not via Park-protocol comparability.
4. **BFI-44 upgrade** — at 2 items/trait, BFI trait RMSE is statistically meaningless. Real study should use BFI-44.
5. **Larger N** — pilot N=2+1 → thesis target probably N≥30 per arm based on what's needed for stable LOO ranking + ablation effect estimation.
6. **Survey-instrument design for thesis** — 8-15 items per category × 4 categories = 60+ construction items. Pilot's 5/5/4/4 split is illustrative only.

---

## Open methodological questions for Bayati meeting

1. Is the leakage-filtered analysis (manual STRONG-tagging + strict-clean MAE column) sufficient defense of the C-condition result, or does the thesis-stage replication need 2-week-separated collection regardless?
2. **LOO ranking instability at N=1**: across two pipeline runs at temp 0.7, the "most-important-when-dropped" category changed (psychological → demographic). What N + how many seeds buy a stable ranking?
3. Park's denominator is `% of test-retest reliability`. We don't have that. Worth running a 2-week self-retest with the 3 pilot respondents to recover a denominator, or accept the gap and never quote a single number against Park's?
4. BFI-10 → BFI-44 upgrade for the thesis-stage study: yes/no?
5. Does our 4-category taxonomy (demographic / behavioral / psychological / attitudinal) extend cleanly when N grows, or do we need finer subdivisions?
6. Cookiy as the data-collection platform for the thesis — keep, or switch (e.g., Prolific + custom script for verbatim eval items + 2-week recontact)?

---

## Key decisions log

- **2026-04-29**: Started Joyce-as-only-participant. Pivoted to multi-respondent panel after methodology objection.
- **2026-04-29**: Cookiy 15-min cap discovered. Tried 2-session pairing; Cookiy panel can't pair across studies. Collapsed to single combined session per respondent.
- **2026-04-29**: Added Study 2 (survey-only) to mirror Park's main framework. Between-subjects acceptable at pilot scale.
- **2026-04-29**: N constrained to 2 (Study 1) + 1 (Study 2). Pilot reframed as feasibility demonstration, not statistical comparison.
- **2026-04-29**: In-session eval priming acknowledged as known deviation; absolute accuracy may be inflated.
- **2026-04-30 morning**: Cookiy delivered all 3 transcripts. Smart parser → 15/15 × 3.
- **2026-04-30 evening**: 6 pre-flight fixes applied (paths, demographics, anchors, CSV truth, TypeError, splitter). Pipeline ran end-to-end on laptop with retry/backoff. Leakage audit + robustness chart produced. **Park-was-AI-not-human correction propagated through 5 docs.**
- **2026-04-30 late evening**: GitHub repo created at `Joyceqx/gsbgen390-persona-pipeline` and pushed; GitHub Pages enabled on `/docs`. Project folder tidied: derivative outputs moved into `outputs/` (logs to `outputs/logs/`); pre-pivot stale files moved into `archive/`; code paths in `rescore_with_leakage_audit.py`, `make_robustness_chart.py`, `build_site_data.py`, `run_notebook_local.py` updated for new locations and verified by re-running the post-pipeline rescore + chart + site-build pipeline end-to-end.
- **2026-04-30 late night — Thesis-stage two-phase plan committed.** Phase 1 = GSS public-data feature-importance (`gss_phase1_design.md`). Phase 2 = interview-decomposed study (`thesis_phase2_design.md`). Phase 2 replaces an earlier "paired structured survey" idea after Joyce noted that the actual question — *what's IN the interview that surveys can't capture* — requires interview decomposition, not survey-feature ablation. Phase 2 forces a platform pivot: Cookiy 15-min cap is incompatible with 30-45 min modular long interview, so Phase 2 will use Prolific + a self-hosted OpenAI Realtime API moderator. Composed deliverable = the full 4×3 feature-category × outcome-dimension matrix.
- **2026-04-30 night — Park v1 vs v2 reconciliation + outcome-stratified narrative pivot.** Verified directly from both v1 and v2 PDFs that the proposal's "85%" headline came from v1's interview-based normalized accuracy (~0.85), while v2 reorganized conditions and reports the four numbers we now cite (74/82/83/86%). Both versions live at the same arXiv ID; we adopt v2 framing throughout. **Critical refinement**: the "surveys ≈ interview" tie holds only on GSS attitudes — v2 also reports surveys lagging interviews by 0.15 on BFI-44 personality and by 0.28 on behavioral economic games. Thesis question reframed from "can surveys substitute for interviews?" to **outcome-stratified** "which feature categories close which parts of that gap on which outcomes?" Batch update propagated through `MEETING_HANDOUT.md`, `README.md`, `replication_scoping.md`, `EXPLAIN_ZH.md`, `LIT_REVIEW.md`, `PRIMER.md`, `FUTURE_DESIGN.md`, `progress_report.md`, `docs/index.html`, and this STATUS file.
- **2026-05-02 — Bayati meeting; Phase 1 design locked.** Direction confirmed: GSS-first then targeted Cookiy. **Path A\* locked**: Path B (12 curated items) as primary for the LOO; Path A (Park's full ~118 items) as sensitivity. Snapshot prediction on a single GSS wave (no panel for prediction). Raw accuracy as primary metric — no test-retest normalization in Phase 1; deferred to Phase 2's recontact arm. Persona self-consistency reported as supplementary stability check. Resolution rule for disjoint sets: features = (declared bin lists) MINUS primary_eval (only); sensitivity-pass handles per-item leakage separately. This rule preserves a populated psychological feature bin in GSS, which would otherwise be empty.
- **2026-05-02 — Phase 1 data + tooling shipped.** GSS 2024 cross-section (3,309 respondents × 973 unique variables) downloaded via GSS Data Explorer in 3-batch fixed-width format. `gss_loader.py` written: parses each batch's `.do` script for column specs + variable labels + value labels, reads the corresponding `.dat` fixed-width file, namespaces label-set names per batch (avoids cross-batch label collisions), merges 3 batches horizontally. Verified 22/22 key Park variables present with correct labels. `gss_feature_taxonomy.json` locked: 12 primary_eval items + 118 sensitivity_eval items + 140 features (23 demographic / 29 behavioral / 8 psychological / 80 attitudinal). `validate_taxonomy.py` confirms variable presence, bin disjointness, per-respondent coverage. Next: `gss_pipeline.py` (persona-prompt builder + LLM dispatcher + scorer adapted for GSS rows).
