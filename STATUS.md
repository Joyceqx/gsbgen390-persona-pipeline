# Project Status — GSBGEN390 Mini-Replication

**Last updated:** 2026-04-30 evening (post-tidy: outputs/ + archive/ created; GitHub repo + Pages deployed)
**Maintained by:** Joyce Yu + collaborating Claude session

This document is the single-source-of-truth for what's done, what's pending, and how to pick up the project in a fresh terminal, Claude Code CLI, or Claude Cowork session.

---

## TL;DR for a fresh session

Pilot replication of Park et al. (2024) *Generative Agent Simulations of 1,000 People* is **end-to-end complete at small scale**:

- **3 Cookiy transcripts** collected (Study 1 N=2 interview, Study 2 N=1 survey).
- **Smart parser** extracts 15/15 eval truth and 18/18 construction items at 100% rate.
- **Persona pipeline ran successfully on local laptop** via `run_notebook_local.py` (a thin runner that executes `persona_pipeline.ipynb` outside Colab) — 12 conditions, ~9 min, ~$4 in OpenAI API.
- **Headline finding**: Condition C (interview-conditioned) wins by a large margin on Study 1 (Likert MAE 0.00–0.08 vs 0.83–1.17 for A demographics-only). Direction matches Park.
- **Leakage audit**: even after manually dropping the 3 STRONG-leaked items per Study-1 respondent, C still wins. The interview-conditioning advantage is **not** a regex artifact — robustness check passes.
- **Study 2 LOO ablation** is run-unstable at N=1 (different category ranks first across runs at temp 0.7) — directional only, awaits N≥30.
- **Bayati meeting handout** ready: `MEETING_HANDOUT.md` covers headline numbers, leakage audit, open questions.

**What has NOT been done yet**: 3-5 page formal writeup, multi-seed run-variance estimation, 2-week-separated re-collection, BFI-44 upgrade. All are post-meeting decisions.

---

## What changed in this session (2026-04-30 evening)

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

## Current work tree (post-tidy 2026-04-30 evening)

```
GSBGEN390/
├── README.md                          ← front door
├── STATUS.md                          ← this file (single-source-of-truth)
├── PRIMER.md                          ← 1-2 page Joyce self-intro (audience-tunable)
├── MEETING_HANDOUT.md                 ← one-page brief for Bayati meeting
├── WRITEUP.md                         ← 3-5 page formal pilot write-up
├── progress_report.md                 ← full sprint narrative
├── replication_scoping.md             ← design rationale + Park's actual numbers
├── FUTURE_DESIGN.md                   ← open design questions for the thesis-stage study
├── BUSINESS_LANDSCAPE.md              ← market scan: AI persona simulation + AI-moderated research
├── LIT_REVIEW.md                      ← academic literature review
├── EXPLAIN_ZH.md                      ← Chinese-language project explanation
├── CODE_WALKTHROUGH_ZH.md             ← Chinese walkthrough of persona_pipeline.py
├── COLAB_RUN_GUIDE.md                 ← Colab fallback instructions
│
├── cookiy_brief.md                    ← Study 1 brief (interview arm)
├── cookiy_brief_study2.md             ← Study 2 brief (survey arm)
├── cookiy_guide_session1.md           ← Cookiy's auto-generated discussion guide (S1)
├── cookiy_guide_session2.md           ← Cookiy's auto-generated discussion guide (S2)
│
├── eval_battery.json                  ← 15-item held-out eval, with regex anchors
├── eval_answers_extracted.csv         ← parsed truth: 15 items × 3 respondents (GOLD)
├── construction_answers_extracted.csv ← parsed truth: 18 construction items × 1 respondent
├── metrics_per_respondent.csv         ← notebook scoring: 12 conditions × full eval metrics
│
├── persona_pipeline.py                ← script-style pipeline (uses responses/ layout)
├── persona_pipeline.ipynb             ← CANONICAL pipeline (31 cells, includes LOO)
├── run_notebook_local.py              ← runner: executes the notebook outside Colab
├── parse_eval_answers.py              ← smart parser using moderator confirmations as gold
├── parse_construction_answers.py      ← parser for Study 2 construction items
├── rescore_with_leakage_audit.py      ← post-hoc rescoring under STRONG/SOFT/CLEAN filters
├── make_robustness_chart.py           ← chart generator for the leakage audit
├── build_site_data.py                 ← CSV→JSON for docs/data/ with naming normalization
├── build_notebook.py                  ← (Cowork-built — assembles persona_pipeline.ipynb)
│
├── interview_quality_audit.md         ← Study 1 transcript quality audit (GITIGNORED — quotes)
├── survey_quality_audit.md            ← Study 2 transcript quality audit (GITIGNORED — quotes)
├── leakage_audit.json                 ← per-item leakage tags + evidence (GITIGNORED — quotes)
├── Openai_api.txt                     ← API key (GITIGNORED)
│
├── cookiy_transcripts/                ← raw Cookiy outputs (GITIGNORED — verbatim PII)
│   ├── study1_interview_p{1,2}.{txt,json}
│   ├── study2_survey_p1.{txt,json}
│   └── study{1,2}_report.{md,json}    ← Cookiy auto-generated qual/quant reports
│
├── responses/        R{1,2}/{transcript.txt,demographics.json}    ← script-pipeline layout (GITIGNORED)
├── responses_s2/     R1/{transcript.txt,demographics.json}        ← (GITIGNORED)
│
├── outputs/                           ← all pipeline-derivative artifacts
│   ├── metrics_with_leakage_audit.csv ← 36 rows: 12 conditions × 3 filter views
│   ├── chart_robustness.png           ← 2-panel leakage robustness chart
│   ├── persona_answers_full.json      ← per-condition primary+samples (GITIGNORED — embeds prompts)
│   └── logs/                          ← run_*.log timestamped runner logs (GITIGNORED)
│
├── docs/                              ← static GitHub Pages dashboard
│   ├── index.html, style.css, app.js, README.md
│   └── data/                          ← JSON inputs the site fetches (built by build_site_data.py)
│       ├── metrics_per_respondent.json
│       ├── metrics_with_leakage_audit.json
│       ├── metrics_aggregate.json
│       └── eval_answers_extracted.json
│
├── archive/                           ← stale pre-pivot files, kept for history
│   ├── eval_joyce_truth.md
│   ├── eval_joyce_truth_FORM.md
│   ├── persona_demographics.json
│   ├── persona_description.md
│   └── claude_moderator_prompt.md
│
├── test/                              ← synthetic transcript fixtures for smoke testing
│   ├── synthetic_s1_transcript.txt
│   └── synthetic_s2_transcript.txt
│
└── (gitignored at root: GSBGEN390_Application_*.docx, __pycache__/)
```

### Where each file is read from / written to

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

---

## How to resume in a fresh terminal / new Claude Cowork session

### To re-read everything and pick up the story:
```bash
cd ~/Documents/GSBGEN390
# Read in this order:
#   1. STATUS.md (this file) — current state
#   2. MEETING_HANDOUT.md — what we're presenting
#   3. progress_report.md — full sprint narrative
#   4. replication_scoping.md — design rationale
#   5. interview_quality_audit.md / survey_quality_audit.md — data quality findings
```

### To re-run the pipeline (~9 min, $3-5 in API):
```bash
cd ~/Documents/GSBGEN390
export OPENAI_API_KEY=$(cat Openai_api.txt)
# Note: pandas, openai, matplotlib must be installed (already are on Joyce's laptop)
python3 -u run_notebook_local.py 2>&1 | tee outputs/logs/run_$(date +%Y%m%d_%H%M).log
```

This produces `metrics_per_respondent.csv` (at root) + `outputs/persona_answers_full.json`. Then:

```bash
python3 rescore_with_leakage_audit.py    # → outputs/metrics_with_leakage_audit.csv
python3 make_robustness_chart.py         # → outputs/chart_robustness.png
python3 build_site_data.py               # → docs/data/*.json (refreshes the website)
```

### To re-run only the rescoring (no API calls, ~1 second):
If `outputs/persona_answers_full.json` exists from a previous run:
```bash
python3 rescore_with_leakage_audit.py
python3 make_robustness_chart.py
python3 build_site_data.py
```

### Known runtime gotchas
- **TPM rate limit**: account is at 30K tokens/min for gpt-4o. Condition C prompts hit this; the runner has retry+exponential-backoff that adds ~30-60s total to a run.
- **Cell 8** in the notebook uses `google.colab.files.upload()` which doesn't work locally. The runner replaces this with disk reads from `cookiy_transcripts/`.
- **Cell 16** uses `display()` (Jupyter built-in). The runner stubs this to `print()`.
- **Jupyter magics (`!pip`, `%`)** in cells are silently skipped by the runner.
- **`LLM_CACHE`** is in-memory only — every fresh process re-runs all 240+ API calls. To make iteration cheap, the runner persists `persona_answers_full.json` end-of-run; the rescoring script reads from that without API calls.

---

## Pending work (post-meeting decisions)

1. **3-5 page formal writeup** — methods, pipeline, results, leakage audit, comparison to Park's 83/82/86%, limitations, next steps. Awaits Bayati feedback.
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
