# GSBGEN390 — Mini-Replication of Park et al. (2024)

Independent research project, Spring 2026, Stanford GSB. Faculty advisor: **Prof. Mohsen Bayati.** Lead: **Joyce Yu.**

## What this is

A small-scale replication of [Park, Bernstein, Liang et al. (2024) "Generative Agent Simulations of 1,000 People"](https://arxiv.org/abs/2411.10109), the foundational paper for the Stanford spinout Simile. Park's original study built LLM-based personas from 2-hour voice-to-voice interviews — conducted by a custom AI interviewer they built specifically around the American Voices Project (AVP) protocol with adaptive follow-ups — with 1,052 U.S. adults, and showed those personas could predict the same individuals' GSS, BFI, and behavioral-game responses at ~83% of test-retest reliability. **This pilot reproduces the pipeline architecture at small scale (N=2 interview arm, N=1 survey arm) using AI-moderated Cookiy interviews** in place of Park's custom AVP-protocol agent.

The pilot is the first step of a larger thesis question: **which survey-collectible features (demographic, behavioral, psychological, attitudinal) most predict persona fidelity, and on which outcome dimensions?** Park's v2 paper finds that surveys-only nearly matches interview-only on GSS-style attitudinal items (0.82 vs 0.83 normalized accuracy) but lags meaningfully on BFI personality (0.65 vs 0.80) and behavioral economic games (0.38 vs 0.66). That pattern motivates a feature-importance analysis Park did not run: not just "can surveys substitute for interviews?" but *"which survey-collectible feature categories close which parts of the gap on which outcomes?"* This pilot establishes the evaluation infrastructure for that follow-up.

## Quick orientation

If you (or future-Claude) walked in cold, read these in order:

1. [`README.md`](README.md) — this file
2. [`MEETING_HANDOUT.md`](MEETING_HANDOUT.md) — comprehensive bilingual project brief (English + 中文) — best single read for full context
3. [`STATUS.md`](STATUS.md) — current project state, what's done vs. pending, file inventory
4. [`replication_scoping.md`](replication_scoping.md) — full design rationale, Park's actual numbers, what we are and aren't replicating
5. [`gss_phase1_design.md`](gss_phase1_design.md) — **thesis Phase 1**: GSS public-data feature-importance analysis (proposal)
6. [`thesis_phase2_design.md`](thesis_phase2_design.md) — **thesis Phase 2**: interview-decomposed feature-importance study (proposal)
7. [`cookiy_brief.md`](cookiy_brief.md) — Study 1 (interview arm) brief
8. [`cookiy_brief_study2.md`](cookiy_brief_study2.md) — Study 2 (survey arm) brief

## How to run the pipeline

The canonical pipeline is `persona_pipeline.ipynb` (Jupyter / Colab notebook). To run it locally without Jupyter:

```bash
cd ~/Documents/GSBGEN390
export OPENAI_API_KEY=$(cat Openai_api.txt)
python3 -u run_notebook_local.py 2>&1 | tee run_$(date +%Y%m%d_%H%M).log
```

`run_notebook_local.py` is a thin runner that executes the notebook's code cells outside Colab (patches the file-upload cell to read from `cookiy_transcripts/`, skips Jupyter magics, stubs `display()`, adds retry+exponential-backoff for OpenAI TPM limits).

Runtime: ~9 minutes, ~$3-5 in OpenAI API calls. Outputs:
- `metrics_per_respondent.csv` — 12 conditions × full eval metrics
- `persona_answers_full.json` — per-condition primary + samples for every item

Then optionally re-score under leakage-filter views (no API, ~1 second) and produce the chart:
```bash
python3 rescore_with_leakage_audit.py    # → metrics_with_leakage_audit.csv
python3 make_robustness_chart.py         # → chart_robustness.png
```

`persona_pipeline.py` (the older script-based version) still works but is no longer the canonical path. See STATUS.md for the latest results and file inventory.

## Project goal

The eventual thesis fills a 4 (feature category) × 3 (outcome dimension) feature-importance matrix that Park v2 implies but does not produce. The pilot establishes the architecture; **two phases** carry it to publishable scale:

- **Phase 1 — GSS public-data analysis** ([`gss_phase1_design.md`](gss_phase1_design.md)). N≈1,500 same respondents from the GSS Three-Wave Panel 2010-2014; Park-comparable normalized accuracy via within-person retest baseline. Covers the GSS-attitudes outcome row only. Budget ~$300-500, ~1-4 weeks.
- **Phase 2 — Interview-decomposed study** ([`thesis_phase2_design.md`](thesis_phase2_design.md)). N=20-30 Prolific respondents, 30-45 min modular long interview (4 modules ↔ 4 feature bins) with 2-week separation, BFI-44 + behavioral-game vignettes + GSS held-out outcomes. LOO ablation operates at the **interview-content level** — directly decomposes Park's "interview-only" condition. Budget ~$1,500-1,750, ~7-9 weeks.

**Composed thesis output**: the full feature × outcome feature-importance matrix in one semester, ~$2,000 total.

The pilot delivers the smallest end-to-end version of the architecture (Cookiy interview/survey → transcript → persona → held-out eval → metrics) plus the leakage-audit methodology that makes the architecture defensible at small N.

## Repo conventions

- Markdown working notes for design and status; JSON for machine-readable batteries and metrics; Python for the pipeline.
- All paths in `persona_pipeline.py` resolve under `$GSBGEN390_DIR`, defaulting to `/Users/joyce/Documents/GSBGEN390`.
- Sensitive: `Openai_api.txt` lives in this folder for convenience but should be deleted/rotated when the project ends. Never check it into version control.
