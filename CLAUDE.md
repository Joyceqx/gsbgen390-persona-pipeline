# CLAUDE.md — guidance for AI assistants working on this project

This file is loaded automatically by Claude Code (and any AI coding assistant that respects the CLAUDE.md convention) at the start of every session in this directory. Read it before making any non-trivial change.

---

## 1. What this project is

GSBGEN390 thesis-track research, Stanford Graduate School of Business, Spring 2026. **Advisor**: Prof. Mohsen Bayati. **Lead**: Joyce Yu.

The output is a methodological paper on LLM persona simulation — specifically, **which categories of survey-collectible features drive LLM prediction of held-out GSS 2024 attitudes** (Phase 1), and how that pattern varies across outcome dimensions (Phase 2, separate preregistration). The reference benchmark is Park et al. 2024 v2 (arXiv:2411.10109). The target standard is a Park v2 / NBER / NeurIPS / *Management Science* submission, not a class deliverable.

---

## 2. State as of 2026-05-28

### Phase 1A — Bayati-confirmed direction (2026-05-28)

Phase 1A design was finalized with Prof. Bayati on 2026-05-28. The 2026-05-15 proposal brief is archived (`archive/Project Brief — Phase 1A Updates 2026-05-15.md`); the locked direction below supersedes it.

- **Panel arm (factorial)**: 4 cheap models × **3 literature-grounded prompts** (P0 = Park v2 surveys-only baseline, P1 = Argyle 2023 1st-person prose, P2 = Wang 2025 interview Q&A) on N=200 in `[0:200]`, within-respondent factorial. Each respondent runs all 12 (model, prompt) cells × 5 conditions × primary_eval items.
- **§12.2 joint selector**: generalized from "best model" to **best (model, prompt) cell**. argmin respondent-macro Likert MAE on the 12 panel cells over the selection split `[0:100]`, gated by DQ-1 (parse-fail ≤ 30%) and DQ-3 (per-item variance ≥ 30% × human, fail-cell aggregation > 50%) per cell, 5% MAE cost tiebreak, Qwen × P0 as the named tie-break fallback, all-DQ-fail → PAUSE.
- **Random-model column** (no separate cohort): computed analytically post-hoc on the panel data. For each respondent and each prompt, randomly pick 1 of the 4 model results (uniform random, **no 50/50/50/50 balance constraint**). The random column is reported alongside the per-cell results as a deployment-mode sensitivity column — it is not a §12.2 input.
- **GPT-4o anchor**: stays on **P0 only**, preserving Park v2 SI Table 3 comparability (anchor cohort unchanged: N=100 selection split, primary + 118 sensitivity items at n_samples=2).
- **Phase 1B headline**: unchanged from OSF v1 — single selected (model, prompt) on the full N=3,309 GSS 2024 cross-section, primary_eval only, paired-respondent bootstrap, 4-bin LOO ΔMAE with Holm-Bonferroni at α=0.05.
- **Total Phase 1 budget**: ~$790 (panel arm scales 3× from $17 to ~$51 because of the 3-prompts dimension; everything else unchanged).

The canonical design source for the locked Phase 1A is `gss_phase1_design.md` §12 (updated 2026-05-28). OSF v1.1 is reflected in `osf_preregistration_v1.md` (Bayati signoff on §17 item ⑥ recorded 2026-05-28).

### Phase 1B + 1c + supporting infrastructure (unchanged from OSF v1)

- **Cohort + sample**: N=200 panel cohort with a pre-registered 100/100 selection/validation split. Cheap panel: Qwen-2.5-72B / DeepSeek-V3.1 / Llama-3.3-70B / Kimi K2 (3 China-trained + 1 Western-trained).
- **GPT-4o anchor**: on the N=100 selection subset, primary + 118 sensitivity items, n_samples=2, **P0 only** — the only Park-comparable run.
- **Phase 1b**: single §12.2-selected (model, prompt) cell on the full N=3,309 GSS 2024 cross-section, primary_eval only.
- **Phase 1c (co-primary)**: Battery LOO + Shapley on the full N=3,309. Analyzers implemented and self-tested; orchestration drivers in `gss_driver.py` are still NOT-IMPLEMENTED stubs.
- **Bootstrap**: B = 10,000 BCa via `scipy.stats.bootstrap` with percentile fallback.
- **Per-call seed**: SHA-256 over `(rid, condition, item_id, model, sample_idx)` — not a single hardcoded value.
- **Cost guards**: F9 panel-wide-large-N guard refuses `--n ≥ 1000` multi-model + sensitivity unless explicitly bypassed; partial-resume guard refuses to silently resume from suspiciously small artifacts.

### Code implementation status

The pipeline is implemented at the OSF v1 single-model selection level. The Bayati-confirmed Phase 1A direction extends §12.2 to joint (model, prompt) selection — that extension is **not yet implemented** in code.

| Component | Status |
|---|---|
| GSS loader, persona-prompt construction, scoring pipeline | Implemented + tested (Audit A-E + multi-model aggregation) |
| Multi-model LLM router with per-call seed derivation | Implemented + tested |
| §12.2 selector — **single-model version** (DQ gates, 100/100 split, PAUSE, Qwen tie-break fallback) | Implemented + tested (7-branch self-test) |
| §12.2 selector — **joint (model, prompt) version** + random column post-hoc | **NOT yet implemented** |
| Driver named modes (`--phase1a`, `--phase1b`, `--phase1b-anchor`) — single-prompt panel | Implemented + tested |
| Driver `--phase1a` extension to support 3-prompt factorial panel | **NOT yet implemented** |
| R2 regression baseline (Ridge for Likert, multinomial Logistic for binary, 5-fold CV) | Implemented + tested |
| Battery LOO analyzer, Shapley analyzer | Implemented + tested (8 assertions each) |
| Forbidden-language linter for writeup drafts | Implemented + tested |
| Phase 1c orchestration drivers (`--battery-loo`, `--shapley`) | **NOT yet implemented**; stubs exit with an OSF §13.2 pointer |

---

## 3. Reading order for a fresh AI session

### Canonical sources

1. `gss_phase1_design.md` — live design document. Single source of truth for sample sizes, panel composition, sensitivity scope, the §12.2 selector rule, statistical infrastructure, theory framing, and budget. Reflects the Bayati-confirmed Phase 1A direction (factorial 4 × 3 panel + post-hoc random column).
2. `osf_preregistration_v1.md` — OSF v1.1 preregistration. Mirrors the design doc and locks the analysis contract. §17 item ⑥ (Bayati signoff) recorded 2026-05-28.
3. `RUNBOOK.md` — paid-run sequence with exact commands, expected outputs, per-step costs, and common pitfalls.
4. This file (`CLAUDE.md`) — operating principles.

### Use-case extensions

- **Implementing Phase 1c orchestration**: also read `tier1_tool_schemas.md` (Tools 1-2 spec) and the `--battery-loo` / `--shapley` stubs in `gss_driver.py`.
- **Writing the Phase 1 paper**: also read `theory_review_round2.md` §2 (theory framework comparison with verified citations) and the forbidden-language rules in `lint_writeup_language.py`.
- **Phase 2 design work**: also read `thesis_phase2_design.md` (last touched 2026-04-30; needs revision against current Phase 1 design).
- **Supporting literature for the prompt-sweep proposal**: `lit_review_prompt_variants_2026-05-15.md` (Park v2 + Argyle 2023 + Wang 2025 + Sun 2025 + Hu & Collier 2024 + Bisbee 2024 + Salecha 2024 + Aher 2023 + Horton 2023).

### Do not read

Everything in `archive/` or `pilot_code/` — historical only. The archive contains the pre-2026-05-13 narrative docs (STATUS, PROJECT_SYNTHESIS, theory_review round 1, etc.); their bodies still contain pre-lock numbers and stale framings, and reading them will mislead.

---

## 4. Operating principles

These supersede any default helpfulness instinct toward speed over rigor.

**4.1 Methodological rigor over velocity.** When designing or critiquing, surface objections proactively: leakage, confounds, multiple comparisons, drift, selection bias, dependence violations, statistical power, generalization overclaim. Do not gloss over weaknesses to make the project look stronger. Honesty about limitations is what distinguishes a thesis from a class deliverable.

**4.2 Pre-registration discipline.** Before any data analysis at scale, the analysis plan must be locked in writing (eval set, feature taxonomy, primary metric, exclusion rules, secondary analyses). Refuse to silently change a pre-registered choice mid-analysis. If a change is needed, flag it explicitly and log it as a deviation.

**4.3 Comparability with Park v2.** The thesis question is outcome-stratified: surveys ≈ interview only on GSS attitudes (0.82 vs. 0.83); surveys lag interviews by 0.15 on BFI personality and 0.28 on behavioral economic games. Phase 1 attacks the GSS-attitudes row using GSS public panel data. Phase 2 will extend to BFI / behavioral games via targeted Cookiy collection. Every design decision should be evaluated against direct comparability to Park's per-item Table 3 numbers.

**4.4 Statistical claims need the right N + uncertainty.** N=2 + N=1 (Cookiy pilot) supports directional claims only — feasibility, methodology demonstration, design illustration. It does not support "feature X is more important than feature Y". N=3,309 (GSS Phase 1 cross-section) supports proper feature-importance inference with confidence intervals. Inferential certainty at low N is a bug.

**4.5 Privacy + ethics.** Cookiy participant transcripts contain identifying speech and must not be pushed to public repos. The `cookiy_transcripts/`, `responses/`, `responses_s2/` folders, audit files containing direct quotes, and `persona_answers_full.json` are gitignored — maintain that. The OpenAI key in `Openai_api.txt` is gitignored; never echo it in chat or commit it. GSS data is publicly released and does not have these constraints, but the IRB-aware mindset stays on.

**4.6 When in doubt, ask Joyce.** Decisions affecting experimental design, statistical analysis, eval-set composition, feature taxonomy, or pre-registration go through Joyce (and through her, through Bayati). Auto-mode autonomy is fine for code edits and routine scripting; it is not fine for experimental-design choices.

---

## 5. Codebase reference

- **Phase 1 pipeline (canonical)**: `gss_driver.py` (orchestrator) → `gss_pipeline.py`, `select_phase1b_model.py`, `battery_loo.py`, `shapley_decomposition.py`, `regression_baseline.py`, `validate_taxonomy.py`, `llm_router.py`, `lint_writeup_language.py`. Run order: see `RUNBOOK.md`.
- **Pilot pipeline** (archived to `pilot_code/`): `pilot_code/persona_pipeline.ipynb`, `pilot_code/run_notebook_local.py`, `pilot_code/rescore_with_leakage_audit.py`, `pilot_code/make_robustness_chart.py`, `pilot_code/build_site_data.py`. Produced the `docs/` dashboard; historical, do not modify.
- **Data**: `data/gss/390data1/` — 3-batch GSS extract from NORC GSS Data Explorer, covering 1972–2024 (and 2022), ~2 GB.
- **Status (live)**: §16 decisions log inside `osf_preregistration_v1.md`; `RUNBOOK.md` TL;DR for paid-run state. The earlier `STATUS.md` and `PROJECT_SYNTHESIS.md` were moved to `archive/` on 2026-05-13.
- **Faculty briefs**: `Project Brief for Professor Bayati.md` (2026-05-10 OSF v1 overview). The 2026-05-15 Phase 1A redesign proposal is archived at `archive/Project Brief — Phase 1A Updates 2026-05-15.md` (Bayati-confirmed direction is now in `gss_phase1_design.md` §12 and `osf_preregistration_v1.md`).
- **Park v2 reference PDF**: `2411.10109v2.pdf` (gitignored).

---

*Last refreshed 2026-05-28. Main-branch tip: `122dee1`. Redesign-branch tip: `db37731`. Pre-redesign snapshot: tag `pre-mohsen-redesign-2026-05-13`.*
