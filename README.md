# GSBGEN390 — Feature Attribution for LLM Persona Synthesis

> ⚠️ **PARTIALLY SUPERSEDED** (banner added 2026-05-10 night per Audit-fresh-4 P2.3). Phase 1 numbers below are from 2026-05-09 evening; sample sizes / panel / sensitivity scope / budget were revised on 2026-05-09 night and 2026-05-10. **Always read** `gss_phase1_design.md` (live design) + `osf_preregistration_v1.md` (OSF lock) for canonical state, and `RUNBOOK.md` for the exact paid-run sequence.
>
> **Current Phase 1 numbers** (locked 2026-05-10 Joyce decision Option A):
> - Phase 1a: **N=200** with 100/100 selection/validation split, cheap panel **primary-only**
> - Phase 1b: **N=3,309** (full GSS 2024), single §12.2-selected model, **primary-only**
> - GPT-4o anchor: **N=100 selection-split subset, primary + sensitivity** (the only Park-comparable run; produces the per-item raw-accuracy anchor table)
> - Cheap panel: Qwen-2.5-72B / DeepSeek-V3.1 / **Llama-3.3-70B-Instruct (Meta)** / Kimi K2 (3 China + 1 Western post pre-OSF MiniMax→Llama swap)
> - Budget: **~$756** total Phase 1 (~$237 core + ~$481 Battery LOO + ~$38 Shapley)
> - All-DQ-fail: **PAUSE for human review** (no silent Qwen fallback)
> - Bootstrap: B=10000 BCa with percentile fallback (was 1000 percentile)

Independent research project, Spring 2026, Stanford GSB. Faculty advisor: **Prof. Mohsen Bayati.** Lead: **Joyce Yu.**

## What this is

A research project investigating **feature attribution for LLM persona synthesis**: when a language model is prompted to respond as a specific human individual (for survey simulation, agent-based modeling, in-silico RCTs, or commercial synthetic-respondent panels), which input feature categories actually drive prediction quality, and how does that contribution vary across outcome dimensions?

The thesis is structured in two phases plus a completed pilot:

- **Pilot** (completed 2026-04-30): N=2 interview + N=1 survey via Cookiy → GPT-4o → eval, with manual leakage audit. Pipeline + dashboard + audit shipped. Scale supports feasibility demonstration only, not statistical inference.
- **Phase 1** (in progress; design locked 2026-05-10 evening — see banner above for current numbers): full GSS 2024 cross-section (**N=3,309**) for the **attitude** outcome dimension. **Two co-primary analyses**: (i) 4-bin LOO ablation (broad), (ii) 34-battery LOO across all 4 bins with nested Holm primary + joint-34 sensitivity (mechanistic). Bin-level Shapley = 4-bin robustness. R1 (battery exclusion, `gss_battery_map.json` v0.2 = 34 batteries) + R2 (regression-baseline comparator) as leakage hygiene. Multi-model OpenRouter panel + GPT-4o anchor. Budget: **~$756 total** (Option A: cheap-panel primary-only; sensitivity_eval anchor-only per OSF §3.2).
- **Phase 2** (planned): N=20-30 Prolific respondents, 30-45 min modular interview (4 modules ↔ 4 feature bins) with **2-week separation** for test-retest baseline, BFI-44 + behavioral-game vignettes + GSS held-out outcomes. Extends feature attribution to **personality** and **behavior** outcome dimensions; ~$1,500-1,750.

[Park, Bernstein, Liang et al. (2024) "Generative Agent Simulations of 1,000 People"](https://arxiv.org/abs/2411.10109) (the Stanford-spinout-Simile paper) is the most-cited prior work in this area. This project anchors against Park for cross-paper benchmarking — a GPT-4o anchor on N=100 subset gives per-item raw accuracy directly comparable to Park v2 SI Table 3 — but the research question stands independently. Park studied aggregate "interview vs surveys"; this project studies feature attribution within survey-style persona prompts at scale, with leakage-stringency that goes beyond Park's reported defenses.

## Quick orientation

If you (or future-Claude) walked in cold, read these in order (reordered
2026-05-10 night per Audit-fresh-5 RevB P2 to put canonical / operational
sources ABOVE historical handoff docs that have superseded banners but
stale bodies):

**Canonical / operational (read first; current as of 2026-05-10):**
1. [`gss_phase1_design.md`](gss_phase1_design.md) — **start here** — the live canonical Phase 1 design (single source of truth; sample sizes / panel / sensitivity scope all current)
2. [`osf_preregistration_v1.md`](osf_preregistration_v1.md) — OSF v1 preregistration (mirrors design doc; locks the analysis contract)
3. [`RUNBOOK.md`](RUNBOOK.md) — step-by-step paid-run sequence with exact commands, costs, and expected outputs
4. [`tier1_tool_schemas.md`](tier1_tool_schemas.md) — Battery LOO + Shapley analyzer/orchestration spec
5. [`INDEX.md`](INDEX.md) — file map; what every file is and which are current vs historical

**Live secondary docs:**
6. [`theory_interpretation_guide.md`](theory_interpretation_guide.md) — Discussion-section memo on candidate cognitive frameworks
7. [`thesis_phase2_design.md`](thesis_phase2_design.md) — Phase 2 (planned; out-of-date, needs revision against current Phase 1 design)
8. [`Project Brief for Professor Bayati.md`](Project%20Brief%20for%20Professor%20Bayati.md) — 15-min faculty-advisor briefing on OSF v1

**Historical handoff (all in `archive/` — read for project history, NOT current numbers; moved 2026-05-13):**
9. [`archive/STATUS.md`](archive/STATUS.md) — dated changelog (banner'd; partially superseded)
10. [`archive/PROJECT_SYNTHESIS.md`](archive/PROJECT_SYNTHESIS.md) — paper-ready bilingual synthesis (banner'd)
11. [`archive/replication_scoping.md`](archive/replication_scoping.md) — original Park v2 replication scoping
12. [`archive/FUTURE_DESIGN.md`](archive/FUTURE_DESIGN.md) — pre-pivot Bayati meeting agenda
13. [`archive/PRIMER.md`](archive/PRIMER.md) — personal self-intro
14. [`archive/theory_review.md`](archive/theory_review.md) — Round-1 theory scaffold (superseded by `theory_review_round2.md`)
15. [`archive/MEETING_HANDOUT.md`](archive/MEETING_HANDOUT.md) — earlier bilingual project brief
16. [`archive/HANDOFF.md`](archive/HANDOFF.md) — earlier fresh-session quickstart

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

> ⚠️ **Use the locked named modes for paid runs** — see `RUNBOOK.md` for the
> canonical step-by-step paid sequence with cost projections per step. Legacy
> manual-flag commands are preserved below for cheap connectivity smoke only;
> they do NOT match the OSF Option A scope and the F9 cost guard will
> refuse panel-wide-large-N invocations like `--n 3309` outright.

```bash
# Connectivity smokes (cheap, NOT paid runs):
python3 llm_router.py --smoke-one               # ~$0.001 — verify connectivity
python3 llm_router.py --smoke-panel             # ~$0.005 — verify all 4 models respond
python3 gss_driver.py --smoke                   # ~$0.02 — 1 resp / 1 model / primary

# Locked paid-run named modes (per RUNBOOK.md + Option A):
python3 gss_driver.py --phase1a                 # Phase 1a cheap × N=200 primary-only, ~$17
python3 select_phase1b_model.py outputs/gss_phase1_records_n200_*.json   # §12.2 selector, free
python3 gss_driver.py --phase1b --phase1b-model SLUG  # Phase 1b cheap × N=3309 primary-only, ~$71
python3 gss_driver.py --phase1b-anchor          # GPT-4o anchor × N=100 primary+sensitivity, ~$148
```

Output: `outputs/gss_phase1_records_n{N}_*.json` (atomic-write per respondent;
resume default-on; partial-resume guard refuses to silently resume from
suspiciously-small files).

See **`RUNBOOK.md`** for the full paid-run sequence, **`gss_phase1_design.md`**
for the canonical live design (the source of truth), and **`osf_preregistration_v1.md`**
for the OSF lock. The earlier `STATUS.md` / `PROJECT_SYNTHESIS.md` narrative
docs moved to `archive/` on 2026-05-13; consult them only for decision-evidence
trails or ZH context, never for current numbers.

### Pilot phase (Cookiy, completed — code archived to `pilot_code/`)

Canonical pipeline is `pilot_code/persona_pipeline.ipynb`. To run it locally without Jupyter:

```bash
export OPENAI_API_KEY=$(cat Openai_api.txt)
python3 -u pilot_code/run_notebook_local.py 2>&1 | tee outputs/logs/run_$(date +%Y%m%d_%H%M).log
```

Runtime: ~9 minutes, ~$3-5 in OpenAI API calls. Outputs `pilot_code/metrics_per_respondent.csv` + `outputs/persona_answers_full.json`.

Then re-score under leakage-filter views and refresh the dashboard data (no API, ~1 second):
```bash
python3 pilot_code/rescore_with_leakage_audit.py    # → outputs/metrics_with_leakage_audit.csv
python3 pilot_code/make_robustness_chart.py         # → outputs/chart_robustness.png
python3 pilot_code/build_site_data.py               # → docs/data/*.json
```

`pilot_code/run_notebook_local.py` is a thin runner that executes the notebook's code cells outside Colab (patches Cell 8 to read from `cookiy_transcripts/`, skips Jupyter magics, stubs `display()`, adds retry+exponential-backoff for OpenAI TPM limits).

`pilot_code/persona_pipeline.py` (the older script-based version) still works but is no longer the canonical path. See `INDEX.md` for the full file inventory and `archive/STATUS.md` for the historical pilot-era changelog.

## Project goal

The eventual thesis fills a 4 (feature category) × 3 (outcome dimension) feature-importance matrix that Park v2 implies but does not produce. The pilot establishes the architecture; **two phases** carry it to publishable scale:

- **Phase 1 — GSS public-data analysis** (IN PROGRESS, lean-design locked 2026-05-09; [`gss_phase1_design.md`](gss_phase1_design.md)). N≈1,500 from GSS 2024 cross-section. **Snapshot prediction** (no panel for prediction; raw accuracy as primary metric, no normalization in Phase 1). Path A* design: Path B 12-item curated eval as primary (supports 4-bin LOO); Path A Park's full ~118 items as sensitivity (per-item Park-comparability). Covers GSS-attitudes outcome row only. Budget ~$215 (within original $300-500 envelope), ~1-4 weeks.
- **Phase 2 — Interview-decomposed study** ([`thesis_phase2_design.md`](thesis_phase2_design.md)). N=20-30 Prolific respondents, 30-45 min modular long interview (4 modules ↔ 4 feature bins) with **2-week separation** (recovers test-retest baseline GSS can't provide), BFI-44 + behavioral-game vignettes + GSS held-out outcomes. LOO ablation operates at the **interview-content level** — directly decomposes Park's "interview-only" condition. Budget ~$1,500-1,750, ~7-9 weeks.

**Composed thesis output**: the full feature × outcome feature-importance matrix in one semester, ~$2,000 total.

The pilot delivers the smallest end-to-end version of the architecture (Cookiy interview/survey → transcript → persona → held-out eval → metrics) plus the leakage-audit methodology that makes the architecture defensible at small N.

## Repo conventions

- Markdown working notes for design and status; JSON for machine-readable batteries and metrics; Python for the pipeline.
- All paths in `pilot_code/persona_pipeline.py` resolve under `$GSBGEN390_DIR`, defaulting to `/Users/joyce/Documents/GSBGEN390`.
- Sensitive: `Openai_api.txt` lives in this folder for convenience but should be deleted/rotated when the project ends. Never check it into version control.
