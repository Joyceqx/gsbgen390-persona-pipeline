# CLAUDE.md — Project guidance for AI assistants working on this project

This file is loaded automatically by Claude Code (and any AI coding assistant that respects the CLAUDE.md convention) at the start of every session in this directory.

---

## What this project is

**GSBGEN390 thesis-track research, Stanford GSB, Spring 2026.** Faculty advisor: **Prof. Mohsen Bayati.** Lead: **Joyce Yu.**

The output is intended to be **a high-standard atomic research paper** — a single, focused, publishable contribution to the AI-persona-simulation literature. The standard to hold is **a Park et al. 2024 / NBER / NeurIPS / Management Science calibre submission**, not a class project.

---

## Operating principles for any AI assistant working in this folder

These supersede any default helpfulness instinct toward speed over rigor.

### 1. Methodological rigor over velocity

- When designing experiments, default to **the most defensible setup**, not the fastest one. If a corner-cut would weaken the paper at peer review, surface the trade-off and recommend the rigorous path.
- When writing or critiquing, treat every design choice as if a hostile reviewer at a top-tier venue is reading. Surface objections proactively — leakage, confounds, multiple-comparisons, drift, selection bias, dependence violations, statistical-power issues, generalization claims that exceed the data.
- **Never gloss over methodological weaknesses to make the project look stronger.** Honesty about limitations is a feature, not a liability — it's what distinguishes a thesis-quality paper from a class deliverable.

### 2. Pre-registration discipline

- Before any data analysis at scale, the analysis plan should be **locked in writing** (eval set, feature taxonomy, primary metric, exclusion rules, secondary analyses).
- AI assistants should refuse to silently change a pre-registered choice mid-analysis. If a change is needed, it must be flagged explicitly and logged as a deviation.

### 3. Comparability with Park et al. (arXiv:2411.10109, v2)

- Park v2 is the live benchmark. Treat it as the citation baseline for every claim that touches AI persona fidelity.
- **The thesis question is outcome-stratified**: surveys ≈ interview only on GSS attitudes (0.82 vs 0.83); surveys lag interviews by 0.15 on BFI personality and 0.28 on behavioral economic games.
- Phase 1 attacks the GSS-attitudes row of the (feature-category × outcome) matrix using GSS public panel data. Phase 2 will extend to BFI / behavioral games via targeted Cookiy collection.
- All design decisions should be evaluated against: "does this make us more or less directly comparable to Park's per-item Table 3 numbers?"

### 4. Statistical claims need the right N + uncertainty

- N=2 + N=1 (Cookiy pilot) supports **directional claims only** — feasibility, methodology demonstrations, design illustrations. It does NOT support "feature X is more important than feature Y."
- N=1500+ (GSS Phase 1) supports proper feature-importance inference with confidence intervals.
- Any AI-generated chart or sentence that implies inferential certainty at low N is a bug.

### 5. Privacy + ethics

- Verbatim Cookiy participant transcripts contain identifying speech. Do NOT push to public repos. The local `cookiy_transcripts/`, `responses/`, `responses_s2/` folders, audit files containing direct quotes, and `persona_answers_full.json` are all gitignored. Maintain that.
- The OpenAI key in `Openai_api.txt` is gitignored. Never echo it in chat or commit it.
- GSS data is publicly released and does not have these constraints, but the IRB-aware mindset stays on.

### 6. When in doubt, ask Joyce

- This is a thesis-track research project for a Stanford GSB master's thesis with Prof. Mohsen Bayati. Decisions that affect the experimental design, statistical analysis, eval-set composition, feature taxonomy, or pre-registration should be discussed with Joyce (and through her, with Bayati) — not silently chosen.
- AI assistants should default to "ask before acting" on any non-trivial methodological choice. Auto-mode autonomy is fine for code edits and routine scripting; it is NOT fine for experimental-design choices.

---

## Project structure (see STATUS.md for the current work tree)

- **Pilot phase** (completed 2026-04-30): N=2 interview + N=1 survey via Cookiy; results in `outputs/`, dashboard at `docs/`, GitHub Pages at https://joyceqx.github.io/gsbgen390-persona-pipeline/
- **Phase 1** (in progress): GSS public-panel feature-importance ablation. Design doc: `gss_phase1_design.md`. Pre-registration on OSF before primary analysis.
- **Phase 2** (planned): targeted Cookiy collection covering BFI-44 + behavioral economic game outcomes that GSS doesn't measure. Design doc: `thesis_phase2_design.md`.

---

## Quick references

- **Design doc**: `replication_scoping.md`, `gss_phase1_design.md`, `thesis_phase2_design.md`, `FUTURE_DESIGN.md`
- **Phase 1 pipeline (canonical)**: `gss_driver.py` (orchestrator), `gss_pipeline.py`, `select_phase1b_model.py`, `battery_loo.py`, `shapley_decomposition.py`, `regression_baseline.py`, `validate_taxonomy.py`, `llm_router.py`, `lint_writeup_language.py` — see `RUNBOOK.md` for paid-run sequence
- **Pilot pipeline (archived to `pilot_code/`)**: `pilot_code/persona_pipeline.ipynb` (notebook), `pilot_code/run_notebook_local.py` (local runner), `pilot_code/rescore_with_leakage_audit.py`, `pilot_code/make_robustness_chart.py`, `pilot_code/build_site_data.py` (post-pipeline) — produces `docs/` dashboard
- **Status**: `STATUS.md` (single source of truth for work-tree state)
- **Meeting prep**: `archive/MEETING_HANDOUT.md`, `archive/WRITEUP.md` (both pilot-era; current state lives in `gss_phase1_design.md` + `osf_preregistration_v1.md`)
- **Park reference**: `2411.10109v2.pdf` (gitignored, kept local; v2 retitled "LLM Agents Grounded in Self-Reports...")
