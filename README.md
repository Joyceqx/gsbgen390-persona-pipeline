# GSBGEN390 — LLM Persona Feature Attribution on GSS 2024

Stanford GSB master's thesis, Spring 2026. Lead: Joyce Yu. Advisor: Prof. Mohsen Bayati.

**What this is**: a methodological paper that estimates which categories of survey-collectible features (demographic / behavioral / psychological / attitudinal) drive LLM persona prediction of held-out GSS 2024 attitudes, benchmarked against Park et al. 2024 v2.

## Where to start

- **Design**: `RESEARCH_DESIGN.md` is the single source of truth — research question, data, eval set, panel, prompts, selector, analysis plan, budget.
- **Code**: `src/` — pipeline in `src/gss_driver.py` (orchestrator) → `src/gss_pipeline.py`, `src/select_phase1b_model.py`, `src/battery_loo.py`, `src/shapley_decomposition.py`, `src/regression_baseline.py`, `src/validate_taxonomy.py`, `src/llm_router.py`, `src/lint_writeup_language.py`.
- **Data**: `data/gss/390data1/` — 3-batch GSS extract covering 1972–2024 (~2 GB).
- **Locked artifacts**: `gss_feature_taxonomy.json` (140 variables × 4 bins) and `gss_battery_map.json` (34 batteries + 17 singletons).
- **History + reference materials**: `archive/` (earlier design docs, OSF preregistration, prior advisor briefs, theory reviews, Park v2 PDF `2411.10109v2.pdf`, supporting lit review `lit_review_prompt_variants_2026-05-15.md`, Phase 1c tool spec `tier1_tool_schemas.md`). Read on demand only.

## How to run

See `RESEARCH_DESIGN.md` §10.3 for the full command sequence. Quick version:

```bash
# Pre-flight (free)
python3 src/validate_taxonomy.py
python3 src/select_phase1b_model.py --self-test

# Smoke
python3 src/gss_driver.py --smoke              # ~$3, 5 min

# Phase 1A (4 models × 3 prompts × N=200) + GPT-4o anchor
python3 src/gss_driver.py --phase1a            # ~$51, ~24 hr
python3 src/gss_driver.py --phase1b-anchor     # ~$148, 2-4 hr

# Joint (model, prompt) cell selector
python3 src/select_phase1b_model.py outputs/phase1a_raw.parquet

# Phase 1B (selected cell × N=3,309)
python3 src/gss_driver.py --phase1b --phase1b-model <slug> --phase1b-prompt <p>   # ~$71, 3-7 days

# Phase 1C
python3 src/gss_driver.py --battery-loo --phase1b-model <slug> --phase1b-prompt <p>  # ~$481
python3 src/gss_driver.py --shapley                                                  # ~$38
```

Total Phase 1 budget: ~$792. The factorial extension (3 prompts) and parquet writer in `gss_driver.py` are not yet implemented; see `RESEARCH_DESIGN.md` §10.2 for the extension scope.

## Privacy

GSS data is public — no constraints. Cookiy participant transcripts (`cookiy_transcripts/`, `responses/`, `responses_s2/`) are gitignored and stay local. API keys are gitignored.
