# CLAUDE.md — AI guidance for this project

Loaded automatically by Claude Code at session start. Read `RESEARCH_DESIGN.md` first — it is the single source of truth for the study.

---

## Project

GSBGEN390 thesis-track research, Stanford GSB, Spring 2026. Advisor: Prof. Mohsen Bayati. Lead: Joyce Yu. The output is a methodological paper on LLM persona simulation of GSS 2024 attitude outcomes, benchmarking against Park et al. 2024 v2 (arXiv:2411.10109).

## Where things live

- `RESEARCH_DESIGN.md` — single source of truth (data, design, panel, prompts, selector, analysis, budget, run commands)
- `gss_feature_taxonomy.json`, `gss_battery_map.json` — locked feature taxonomy + battery map
- `data/gss/390data1/` — GSS 2024 cross-section (3-batch extract, ~2 GB)
- `outputs/` — locked reference files (`primary_eval_human_variance_2024.json`) + run artifacts
- `src/` — all pipeline code (orchestrator: `src/gss_driver.py`; selector: `src/select_phase1b_model.py`; analyzers: `src/battery_loo.py`, `src/shapley_decomposition.py`; etc.)
- `archive/` — historical docs (OSF preregistration, prior briefs, theory reviews, Park v2 PDF, supporting lit review, Phase 1c tool spec, etc.). Read on demand only.

## Operating principles

1. **Rigor over velocity.** Surface objections proactively — leakage, confounds, multiple comparisons, drift, selection bias, dependence violations, power, generalization overclaim. Honesty about limitations is the point.
2. **Park v2 benchmark.** Phase 1 attacks the GSS-attitudes row of Park's outcome-stratified matrix. Every design choice should be evaluated against direct comparability to Park's per-item Table 3 numbers.
3. **Statistics.** N=2 + N=1 Cookiy pilot supports directional claims only. N=3,309 GSS supports inferential feature-importance claims with CIs. Inferential certainty at low N is a bug.
4. **Privacy.** Cookiy participant transcripts are gitignored. API keys (`Openai_api.txt`, `OpenRouter_api.txt`) are gitignored — never echo them in chat or commit them.
5. **Implementation status (2026-05-28).** Pipeline implements OSF v1 single-prompt panel. The Bayati-confirmed 4 × 3 factorial extension (joint (model, prompt) selector + 3-prompt driver + random-column aggregation + parquet output writer) is **not yet implemented**. See `RESEARCH_DESIGN.md` §10 for the extension scope.
6. **Ask Joyce on design decisions.** Code edits and routine scripting are fine to autopilot; experimental design / statistical analysis / eval-set composition / feature taxonomy changes go through Joyce.

## What changed recently

- **2026-07-12**: Phase 1B cell locked = **Random × P1** (Bayati email; overrides the §7 selector's `fallback_qwen_p0_tie` output — rationale: no model beats Random with clustered SEs + mode-collapse mitigation on CONLEGIS). Phase 1B extended to **6 conditions**: Full + 4 bin-LOO + `random_battery_drop` (randomized battery ablation, one seeded random battery per (rid, item) on top of R1 — the cheap approximation of Phase 1C Battery LOO; §8 Layer 2). Driver implements `--phase1b-model random` + `CONDITIONS_PHASE1B`; parquet schema gains `random_dropped_battery` (19 cols). Phase 1C Battery LOO ($481) now contingent on ablation results.
- **2026-05-28**: Prof. Bayati signed off the design and removed the OSF preregistration requirement. Phase 1A panel arm extended to a 4-model × 3-prompt factorial; §12.2 selector now operates on 12 (model, prompt) cells; random-model column added post-hoc.
- **2026-05-28**: Major doc cleanup. The earlier living design doc (`gss_phase1_design.md`), the OSF preregistration (`osf_preregistration_v1.md`), the paid-run sequence (`RUNBOOK.md`), the 5/10 advisor brief, the theory reviews, the early lit review, and assorted scaffolding docs were all archived to `archive/`. `RESEARCH_DESIGN.md` is now the single source of truth.
