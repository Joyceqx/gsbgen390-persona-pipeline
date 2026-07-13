# GSBGEN390 — LLM Persona Feature Attribution on GSS 2024

Stanford GSB master's thesis, Spring 2026. Lead: Joyce Yu. Advisor: Prof. Mohsen Bayati.

**What this is**: a methodological paper that estimates which categories of survey-collectible features (demographic / behavioral / psychological / attitudinal) drive LLM persona prediction of held-out GSS 2024 attitudes, benchmarked against Park et al. 2024 v2.

## Status (2026-07-12)

| Stage | Status |
|---|---|
| Phase 1A factorial (4 models × 3 prompts × N=200) | ✅ done → `outputs/phase1a_raw.parquet` |
| GPT-4o anchors A (R1-OFF) + B (R1-ON), N=100 | ✅ done → `outputs/anchor_r1{off,on}_n100.json` |
| §7 selector + §7.1 advisor decision | ✅ cell locked: **Random × P1** |
| Phase 1B (N=3,309 × 6 conditions, ~$58) | ⏳ next — see "How to run" |
| Layer-2 paired-difference analyzer | ⏳ pending (before Phase 1B analysis) |
| Phase 1C (Battery LOO $481 / Shapley $38) | Battery LOO contingent on Layer-2 results |

## Layout

- `RESEARCH_DESIGN.md` — **single source of truth** (design, panel, prompts, selector, §7.1 cell decision, §8 two-layer Phase 1B, budget, run commands)
- `CLAUDE.md` — AI-session guidance + changelog
- `gss_feature_taxonomy.json` / `gss_battery_map.json` — locked taxonomy (140 vars × 4 bins) + battery map (34 batteries + 17 singletons)
- `config/persona_prompt_templates.json` — canonical P1/P2 per-variable templates (hash-stamped into records)
- `src/` — pipeline code:
  - `gss_driver.py` — orchestrator (`--phase1a` / `--phase1b` / `--phase1b-anchor` / `--smoke` / `--self-test-dispatch`)
  - `gss_pipeline.py`, `gss_loader.py` — scoring / prompts / data loading
  - `prompt_variants.py` — P0/P1/P2 renderers
  - `llm_router.py` — OpenRouter/OpenAI layer + `PROVIDER_LOCK`
  - `select_phase1b_cell.py` — §7 joint (model, prompt) selector
  - `write_phase1a_parquet.py` — §6.2 parquet writer (Random column; Phase-1B guards)
  - `battery_loo.py`, `shapley_decomposition.py`, `regression_baseline.py` — analyzers
  - `gss_driver_anchor.py` — anchor-run driver
  - `validate_taxonomy.py`, `lint_writeup_language.py` — validators
- `tests/preflight_phase1a.py` — paid-run pre-flight coverage checks
- `scripts/` — run launchers + ops (`launch_phase1a.sh`, `launch_anchor_a.sh`, `check.sh` Phase 1A-era progress monitor, `export_databook_xlsx.py`)
- `data/gss/390data1/` — GSS 2024 3-batch extract (~2 GB)
- `outputs/` — run artifacts + locked references (`primary_eval_human_variance_2024.json`); pre-Phase-1A strays in `outputs/archive_pre_phase1a/`
- `report/` — Phase 1A analysis bundle (stats, figures, databook, advisor correspondence)
- `notes/` — advisor deliverables (Phase 1A report .docx/.pdf) + `park_comparability.md`
- `archive/` — superseded docs + code (OSF prereg, old design docs, `select_phase1b_model.py` legacy selector, Park v2 PDF). Read on demand only.

## How to run (Phase 1B, next step)

```bash
# 0. Pre-flight (free)
python3 src/gss_driver.py --self-test-dispatch     # dispatch pickers
python3 src/write_phase1a_parquet.py --self-test   # writer (9 tests)
python3 src/select_phase1b_cell.py --self-test
python3 tests/preflight_phase1a.py

# 1. Provider re-check (free — PROVIDER_LOCK is from 2026-05-31)
python3 src/llm_router.py --smoke-panel

# 2. Driver smoke (~$0.01)
python3 src/gss_driver.py --smoke

# 3. Phase 1B (~$58, 3-7 days; resumable — rerun the same command to continue)
python3 src/gss_driver.py --phase1b --phase1b-model random --phase1b-prompt P1

# 4. Consolidate Phase 1B parquet (NOTE: flags are REQUIRED — guards refuse otherwise)
python3 src/write_phase1a_parquet.py \
    --inputs outputs/gss_phase1_records_n3309_random_seed42.json \
    --no-random-column --output outputs/phase1b_raw.parquet

# 5. R2 regression baseline (free)
python3 src/regression_baseline.py --input outputs/phase1b_raw.parquet \
    --output outputs/phase1b_r2_baseline.json
```

Full sequence + Phase 1C: `RESEARCH_DESIGN.md` §10.3. Budget: §11 (~$742 max / ~$261 if Battery LOO is dropped).

## Privacy

GSS data is public. Cookiy transcripts and API keys (`Openai_api.txt`, `OpenRouter_api.txt`) are gitignored — never commit or echo them.
