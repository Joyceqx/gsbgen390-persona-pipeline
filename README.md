# GSBGEN390 — Feature Attribution for LLM Persona Synthesis

Independent research project, Spring 2026, Stanford GSB. Faculty advisor: **Prof. Mohsen Bayati.** Lead: **Joyce Yu.**

## What this is

A research project investigating **feature attribution for LLM persona synthesis**: when a language model is prompted to respond as a specific human individual (for survey simulation, agent-based modeling, in-silico RCTs, or commercial synthetic-respondent panels), which input feature categories actually drive prediction quality, and how does that contribution vary across outcome dimensions?

The thesis is structured in two phases plus a completed pilot:

- **Pilot** (completed 2026-04-30): N=2 interview + N=1 survey via Cookiy → GPT-4o → eval, with manual leakage audit. Pipeline + dashboard + audit shipped. Scale supports feasibility demonstration only, not statistical inference.
- **Phase 1** (in progress, lean-design + co-primary Battery LOO locked 2026-05-09): N≈1500 from GSS 2024 cross-section. Answers the project-level question for the **attitude** outcome dimension. **Two co-primary analyses**: (i) 4-bin LOO ablation (broad), (ii) 34-battery LOO across all 4 bins with nested Holm primary + joint-34 sensitivity (mechanistic). Bin-level Shapley = 4-bin robustness. R1 (battery exclusion, `gss_battery_map.json` v0.2 = 34 batteries) + R2 (regression-baseline comparator) as leakage hygiene. Multi-model OpenRouter panel + GPT-4o anchor. Budget: ~$215 core run + ~$50-60 Battery LOO + ~$15-25 Shapley = **~$280-300 total**.
- **Phase 2** (planned): N=20-30 Prolific respondents, 30-45 min modular interview (4 modules ↔ 4 feature bins) with **2-week separation** for test-retest baseline, BFI-44 + behavioral-game vignettes + GSS held-out outcomes. Extends feature attribution to **personality** and **behavior** outcome dimensions; ~$1,500-1,750.

[Park, Bernstein, Liang et al. (2024) "Generative Agent Simulations of 1,000 People"](https://arxiv.org/abs/2411.10109) (the Stanford-spinout-Simile paper) is the most-cited prior work in this area. This project anchors against Park for cross-paper benchmarking — a GPT-4o anchor on N=100 subset gives per-item raw accuracy directly comparable to Park v2 SI Table 3 — but the research question stands independently. Park studied aggregate "interview vs surveys"; this project studies feature attribution within survey-style persona prompts at scale, with leakage-stringency that goes beyond Park's reported defenses.

## Quick orientation

If you (or future-Claude) walked in cold, read these in order:

1. [`HANDOFF.md`](HANDOFF.md) — **start here** — fresh-session quickstart, current state, immediate next actions
2. [`INDEX.md`](INDEX.md) — file map; what every file is and which are current vs historical
3. [`STATUS.md`](STATUS.md) — TL;DR + dated changelog
4. [`PROJECT_SYNTHESIS.md`](PROJECT_SYNTHESIS.md) — paper-ready bilingual (中文 + English) comprehensive synthesis
5. [`gss_phase1_design.md`](gss_phase1_design.md) — locked Phase 1 design (lean lock 2026-05-09)
6. [`theory_interpretation_guide.md`](theory_interpretation_guide.md) — Discussion-section memo on candidate cognitive frameworks
7. [`MEETING_HANDOUT.md`](MEETING_HANDOUT.md) — earlier bilingual project brief (still useful for cross-phase context)
8. [`replication_scoping.md`](replication_scoping.md) — original Park v2 replication scoping
9. [`thesis_phase2_design.md`](thesis_phase2_design.md) — Phase 2 (planned)

## How to run the pipelines

### Phase 1 (GSS public — pipeline built; needs OpenRouter API key for actual runs)

**No-API validation** (~30s):
```bash
cd ~/Documents/GSBGEN390
python3 gss_loader.py             # loader smoke
python3 validate_taxonomy.py      # 10-check validator (incl. 7c battery map)
python3 gss_pipeline.py --print-prompt          # AUDIT-A
python3 gss_pipeline.py --print-questions       # AUDIT-B
python3 gss_pipeline.py --test-scoring          # AUDIT-C
python3 gss_pipeline.py --test-exclusion        # AUDIT-D
python3 gss_pipeline.py --test-aggregation      # AUDIT-E
python3 gss_pipeline.py --test-multimodel       # multi-model panel test
```

**Real LLM runs** (need OpenRouter API key — `echo "sk-or-v1-..." > OpenRouter_api.txt`):
```bash
python3 llm_router.py --smoke-one               # ~$0.001 — verify connectivity
python3 llm_router.py --smoke-panel             # ~$0.005 — verify all 4 models respond
python3 gss_driver.py --smoke                   # ~$0.02 — 1 resp / 1 model / primary
python3 gss_driver.py --n 10 --primary-only     # ~$0.70 — full panel, primary only
python3 gss_driver.py --n 10                    # ~$2.00 — primary + sensitivity
python3 gss_driver.py --anchor --n 100          # GPT-4o anchor on N=100, primary only, n=2
python3 gss_driver.py --n 1500                  # Phase 1b primary (after OSF pre-reg)
```

Output: `outputs/gss_phase1_records_n{N}_*.json` (atomic-write per respondent; `--resume` default-on).

See **STATUS.md** for the full work-tree, locked design references, and known runtime gotchas.

### Pilot phase (Cookiy, completed)

Canonical pipeline is `persona_pipeline.ipynb`. To run it locally without Jupyter:

```bash
export OPENAI_API_KEY=$(cat Openai_api.txt)
python3 -u run_notebook_local.py 2>&1 | tee outputs/logs/run_$(date +%Y%m%d_%H%M).log
```

Runtime: ~9 minutes, ~$3-5 in OpenAI API calls. Outputs `metrics_per_respondent.csv` + `outputs/persona_answers_full.json`.

Then re-score under leakage-filter views and refresh the dashboard data (no API, ~1 second):
```bash
python3 rescore_with_leakage_audit.py    # → outputs/metrics_with_leakage_audit.csv
python3 make_robustness_chart.py         # → outputs/chart_robustness.png
python3 build_site_data.py               # → docs/data/*.json
```

`run_notebook_local.py` is a thin runner that executes the notebook's code cells outside Colab (patches Cell 8 to read from `cookiy_transcripts/`, skips Jupyter magics, stubs `display()`, adds retry+exponential-backoff for OpenAI TPM limits).

`persona_pipeline.py` (the older script-based version) still works but is no longer the canonical path. See STATUS.md for the latest results and full file inventory.

## Project goal

The eventual thesis fills a 4 (feature category) × 3 (outcome dimension) feature-importance matrix that Park v2 implies but does not produce. The pilot establishes the architecture; **two phases** carry it to publishable scale:

- **Phase 1 — GSS public-data analysis** (IN PROGRESS, lean-design locked 2026-05-09; [`gss_phase1_design.md`](gss_phase1_design.md)). N≈1,500 from GSS 2024 cross-section. **Snapshot prediction** (no panel for prediction; raw accuracy as primary metric, no normalization in Phase 1). Path A* design: Path B 12-item curated eval as primary (supports 4-bin LOO); Path A Park's full ~118 items as sensitivity (per-item Park-comparability). Covers GSS-attitudes outcome row only. Budget ~$215 (within original $300-500 envelope), ~1-4 weeks.
- **Phase 2 — Interview-decomposed study** ([`thesis_phase2_design.md`](thesis_phase2_design.md)). N=20-30 Prolific respondents, 30-45 min modular long interview (4 modules ↔ 4 feature bins) with **2-week separation** (recovers test-retest baseline GSS can't provide), BFI-44 + behavioral-game vignettes + GSS held-out outcomes. LOO ablation operates at the **interview-content level** — directly decomposes Park's "interview-only" condition. Budget ~$1,500-1,750, ~7-9 weeks.

**Composed thesis output**: the full feature × outcome feature-importance matrix in one semester, ~$2,000 total.

The pilot delivers the smallest end-to-end version of the architecture (Cookiy interview/survey → transcript → persona → held-out eval → metrics) plus the leakage-audit methodology that makes the architecture defensible at small N.

## Repo conventions

- Markdown working notes for design and status; JSON for machine-readable batteries and metrics; Python for the pipeline.
- All paths in `persona_pipeline.py` resolve under `$GSBGEN390_DIR`, defaulting to `/Users/joyce/Documents/GSBGEN390`.
- Sensitive: `Openai_api.txt` lives in this folder for convenience but should be deleted/rotated when the project ends. Never check it into version control.
