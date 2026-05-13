# CLAUDE.md — Project guidance for AI assistants working on this project

This file is loaded automatically by Claude Code (and any AI coding assistant that respects the CLAUDE.md convention) at the start of every session in this directory.

---

## ⚡ Fresh-session boot-up reading order (READ THIS FIRST)

**Last refreshed**: 2026-05-13 (stale-doc consolidation: STATUS, PROJECT_SYNTHESIS, theory_review, replication_scoping, FUTURE_DESIGN, PRIMER moved to `archive/`). Project pre-OSF-lock commit: `16a1c04` (any later commit supersedes).

If you are a fresh Claude session resuming this project, read these in order **before doing anything else**. Skip the "DO NOT read" set; they have superseded content with stale numbers and will mislead you.

### ✅ Canonical sources to read

1. **`gss_phase1_design.md`** — canonical live design document (single source of truth for sample sizes, panel composition, sensitivity scope, selector rule, statistical infrastructure, theory framing, budget). All current.
2. **`osf_preregistration_v1.md`** — OSF v1 preregistration (mirrors design doc; locks the analysis contract). §17 lists the 7 decision items; 6 are LOCKED, item ⑥ (Bayati signoff) is the only external blocker.
3. **`RUNBOOK.md`** — exact paid-run sequence with named driver modes, expected outputs, cost per step, common pitfalls.
4. **This file (`CLAUDE.md`)** — operating principles you should follow.

### 📚 Use-case-specific extensions

- **Implementing Phase 1c orchestration** (Battery LOO + Shapley `gss_driver.py` modes): also read `tier1_tool_schemas.md` (Tools 1-2 spec) and the existing `--battery-loo` / `--shapley` NOT-IMPLEMENTED stubs in `gss_driver.py`.
- **Writing Phase 1 paper**: also read `theory_review_round2.md` §2 (theory framework comparison with verified citations) and the forbidden-language rules in `lint_writeup_language.py`.
- **Phase 2 design work**: also read `thesis_phase2_design.md` (last touched 2026-04-30; needs revision against current Phase 1 design).
- **Brief Joyce's advisor**: `Project Brief for Professor Bayati.md` (15-min overview with two Mermaid flowchart diagrams).

### 🚫 DO NOT read (moved to `archive/` 2026-05-13; banner'd as partially superseded; stale numbers)

- `archive/STATUS.md` — banner'd partially-superseded; historical changelog only.
- `archive/PROJECT_SYNTHESIS.md` — banner'd; pre-2026-05-10 numbers in body.
- `archive/theory_review.md` — Round-1 4-theory scaffold; banner'd stale under lean lock; superseded by `theory_review_round2.md` + `theory_interpretation_guide.md`.
- `archive/replication_scoping.md` — pre-pivot Park v2 replication-scoping doc (2026-04-29).
- `archive/FUTURE_DESIGN.md` — pre-pivot Bayati meeting agenda (2026-04-30); items resolved.
- `archive/PRIMER.md` — personal self-intro doc with pre-pivot numbers.
- `archive/HANDOFF.md` — moved to archive; old N=100/N=1500/old budget.
- `archive/MEETING_HANDOUT.md` — pilot-era; nothing about Phase 1.
- `archive/WRITEUP.md` — pilot writeup; not the Phase 1 paper.
- Any other file in `archive/` or `pilot_code/` — historical only.

### 📌 Current state snapshot (2026-05-12)

- **Phase 1a** ready to run (N=200, 100/100 selection/validation split). Cheap panel: Qwen-2.5-72B / DeepSeek-V3.1 / Llama-3.3-70B-Instruct / Kimi K2 (3 China + 1 Western post pre-OSF MiniMax→Llama swap). GPT-4o anchor on N=100 selection-split subset, primary + sensitivity, n_samples=2 — the only Park-comparable run per OSF §3.2.
- **Phase 1b** runs single §12.2-selected cheap model on N=3,309 (full GSS 2024 cross-section), primary_eval only.
- **Phase 1c** (Battery LOO + Shapley) co-primary by default; orchestration drivers NOT yet implemented (stubs in place pointing to OSF §13.2).
- **Budget**: ~$756 total Phase 1 (Option A: cheap panel primary-only; sensitivity anchor-only). Joyce has authorized; awaiting Bayati signoff for OSF lock.
- **Bootstrap**: B=10,000 BCa via scipy with percentile fallback (was 1,000 percentile).
- **All-DQ-fail**: PAUSE for human review (NOT silent Qwen fallback).
- **Per-call seed**: SHA-256 over (rid, condition, item_id, model, sample_idx); NOT a single hardcoded value.
- **Cost guards in driver**: F9 panel-wide-large-N guard refuses --n≥1000 multi-model+sensitivity unless explicitly bypassed; partial-resume guard refuses to silently resume from suspiciously small artifacts.

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
- N=3,309 (GSS Phase 1, full cross-section — expanded from earlier N=1,500 drafts) supports proper feature-importance inference with confidence intervals.
- Any AI-generated chart or sentence that implies inferential certainty at low N is a bug.

### 5. Privacy + ethics

- Verbatim Cookiy participant transcripts contain identifying speech. Do NOT push to public repos. The local `cookiy_transcripts/`, `responses/`, `responses_s2/` folders, audit files containing direct quotes, and `persona_answers_full.json` are all gitignored. Maintain that.
- The OpenAI key in `Openai_api.txt` is gitignored. Never echo it in chat or commit it.
- GSS data is publicly released and does not have these constraints, but the IRB-aware mindset stays on.

### 6. When in doubt, ask Joyce

- This is a thesis-track research project for a Stanford GSB master's thesis with Prof. Mohsen Bayati. Decisions that affect the experimental design, statistical analysis, eval-set composition, feature taxonomy, or pre-registration should be discussed with Joyce (and through her, with Bayati) — not silently chosen.
- AI assistants should default to "ask before acting" on any non-trivial methodological choice. Auto-mode autonomy is fine for code edits and routine scripting; it is NOT fine for experimental-design choices.

---

## Project structure (see `gss_phase1_design.md` for canonical Phase 1 design state)

- **Pilot phase** (completed 2026-04-30): N=2 interview + N=1 survey via Cookiy; results in `outputs/`, dashboard at `docs/`, GitHub Pages at https://joyceqx.github.io/gsbgen390-persona-pipeline/. Pilot code archived to `pilot_code/`.
- **Phase 1** (in progress, OSF lock pending Bayati signoff): GSS 2024 full cross-section (N=3,309) feature-importance ablation; two co-primary analyses (4-bin LOO + 34-battery LOO). Design doc: `gss_phase1_design.md`. OSF v1: `osf_preregistration_v1.md`. Paid-run sequence: `RUNBOOK.md`.
- **Phase 2** (planned, separate preregistration when Phase 1 results land): targeted Prolific/Cookiy collection covering BFI-44 + behavioral economic game outcomes that GSS doesn't measure. Design doc: `thesis_phase2_design.md` (last touched 2026-04-30; needs revision against current Phase 1 design).

---

## Quick references

- **Design doc (live)**: `gss_phase1_design.md` (Phase 1 canonical), `thesis_phase2_design.md` (Phase 2 planned — out-of-date, needs revision)
- **Phase 1 pipeline (canonical)**: `gss_driver.py` (orchestrator), `gss_pipeline.py`, `select_phase1b_model.py`, `battery_loo.py`, `shapley_decomposition.py`, `regression_baseline.py`, `validate_taxonomy.py`, `llm_router.py`, `lint_writeup_language.py` — see `RUNBOOK.md` for paid-run sequence
- **Pilot pipeline (archived to `pilot_code/`)**: `pilot_code/persona_pipeline.ipynb` (notebook), `pilot_code/run_notebook_local.py` (local runner), `pilot_code/rescore_with_leakage_audit.py`, `pilot_code/make_robustness_chart.py`, `pilot_code/build_site_data.py` (post-pipeline) — produces `docs/` dashboard
- **Status (live)**: `osf_preregistration_v1.md` §16 decisions log + `RUNBOOK.md` TL;DR. (Earlier `STATUS.md` and `PROJECT_SYNTHESIS.md` moved to `archive/` 2026-05-13.)
- **Faculty briefing**: `Project Brief for Professor Bayati.md` (15-min OSF v1 overview with two Mermaid flowcharts)
- **Park reference**: `2411.10109v2.pdf` (gitignored, kept local; v2 retitled "LLM Agents Grounded in Self-Reports...")
