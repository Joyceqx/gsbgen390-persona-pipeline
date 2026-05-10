# Project File Index

**Project**: GSBGEN390 thesis-track research, Stanford GSB, Spring 2026
**Research direction**: feature attribution for LLM persona synthesis (Phase 1: attitude prediction; Phase 2 planned: personality + behavioral games)
**Lead**: Joyce Yu · **Advisor**: Prof. Mohsen Bayati
**Last housekeeping**: 2026-05-09

This file maps every file in the project to its purpose, status, and "stop reading here if I just want to get oriented" signal. **Read `HANDOFF.md` first** if this is a fresh session; this file is the lookup table when you know the question.

For "what changed and when", see `STATUS.md` changelog. For "the comprehensive paper-ready synthesis", see `PROJECT_SYNTHESIS.md`. For "what to do right now", see `HANDOFF.md` §6.

---

## Layer 0 — Read these first (in order)

| File | Purpose | Status |
|---|---|---|
| `CLAUDE.md` | Operating principles for any AI assistant in this folder (rigor over velocity, pre-reg discipline, Park comparability) | Stable |
| `HANDOFF.md` | Front-door quickstart for a fresh terminal / Claude session | Updated 2026-05-09 |
| `STATUS.md` | Single source of truth for tree state + decisions log; changelog-style | Updated 2026-05-09 |
| `INDEX.md` | This file — every file's purpose | Updated 2026-05-09 |
| `README.md` | Public-facing repo README (GitHub) | Updated periodically |

## Layer 1 — Phase 1 design specs (CURRENT, lean-design locked 2026-05-09)

| File | Purpose | Status |
|---|---|---|
| `gss_phase1_design.md` | **THE design doc.** Locked decisions: §4 method, §10 aggregation, §12 multi-model panel, §12.2 quality-primary selection rule, §13.1 Shapley, §13.2 Battery LOO, §13.3 theory interpretation | Lean-locked 2026-05-09 |
| `gss_feature_taxonomy.json` | v0.3 — 12 primary_eval, 118 sensitivity_eval, 140 features × 4 bins | Locked 2026-05-05 |
| `gss_battery_map.json` | **v0.2** — 34 batteries (D=7/B=10/P=2/A=15) + 17 singletons; used by R1 leakage exclusion AND co-primary Battery LOO across all 4 bins | Locked 2026-05-08 (v0.1) → 2026-05-09 (v0.2 expansion) |
| `tier1_tool_schemas.md` | Output schemas for the 2 secondary tools (Shapley + Battery LOO) | Lean v0.2 locked 2026-05-09 |
| `theory_interpretation_guide.md` | Discussion-section memo: 6 candidate frameworks for interpretive secondary analysis (NOT a horse race) | Lean v0.1 locked 2026-05-09 |
| `osf_preregistration_v1.md` | **OSF v1 draft** — full preregistration document with locked artifact SHA-256 hashes, walks through §9e 22-item checklist; 6 open items pending Joyce + Bayati signoff before final lock | v1 DRAFT 2026-05-09 night |
| `theory_review.md` | Round 1 lit review: MFT / Schwartz / Bourdieu / Cultural Theory of Risk | Stable; §8 lock empty (theory choice deferred to amendment-only) |
| `theory_review_round2.md` | Round 2 lit review: + Inglehart-Welzel / Big Five + verified 2024-2026 LLM-applied work | Stable |
| `outputs/primary_eval_human_variance_2024.json` | Locked GSS-2024 per-item human variance reference for DQ-3 | Locked 2026-05-08 |

## Layer 2 — Phase 1 implementation (code)

| File | Purpose | Test command |
|---|---|---|
| `gss_loader.py` | Reads 3-batch GSS DE extract → 3,309 × 973 DataFrame | `python3 gss_loader.py` |
| `gss_pipeline.py` | Persona-prompt builder + scorer + audit primitives + battery-map loader | `python3 gss_pipeline.py --print-prompt` |
| `gss_driver.py` | Top-level orchestrator (4-bin LOO + sensitivity + atomic-write resume + R1 battery exclusion) | `python3 gss_driver.py --smoke` |
| `llm_router.py` | OpenRouter / OpenAI client + 8-attempt backoff | (needs API key) |
| `validate_taxonomy.py` | 10-check structural validator (data presence, bin disjointness, override coverage, battery map well-formedness) | `python3 validate_taxonomy.py` |
| `select_phase1b_model.py` | §12.2 quality-primary rule executable + 5-branch self-test | `python3 select_phase1b_model.py --self-test` |
| `regression_baseline.py` | R2 regression baseline (Layer 4 leakage hygiene) — partition LLM gain from auto-correlation | `python3 regression_baseline.py --self-test` |
| `shapley_decomposition.py` | Tier 1 secondary tool — 16-condition bin-level Shapley + ANOVA-contrast decomposition + interaction_variance_share + paired bootstrap CI; consumes records JSON, produces JSON matching `tier1_tool_schemas.md` Tool 1 v0.2 | `python3 shapley_decomposition.py --self-test` |
| `battery_loo.py` | Tier 1 co-primary tool — 34-battery LOO ΔMAE + nested Holm primary + joint-34 sensitivity + practical-effect labels + paired bootstrap; consumes records JSON, produces JSON matching `tier1_tool_schemas.md` Tool 2 v0.4 | `python3 battery_loo.py --self-test` |

## Layer 3 — Status / decisions (cross-reference)

| File | Purpose | Notes |
|---|---|---|
| `STATUS.md` | Working state + per-day changelog | Updated 2026-05-09 |
| `HANDOFF.md` | Fresh-session quickstart | Updated 2026-05-09 |
| `PROJECT_SYNTHESIS.md` | Paper-ready comprehensive synthesis (bilingual ZH/EN); decision log; criticisms + responses | Updated 2026-05-09 (lean revision) |

## Layer 4 — Phase 2 design (planned, not started)

| File | Purpose | Status |
|---|---|---|
| `thesis_phase2_design.md` | Phase 2 design: Cookiy + Prolific N=20-30 with 2-week recontact, BFI-44 + behavioral games + GSS | Stable; will be revisited after Phase 1 results |

## Layer 5 — Pilot phase (completed 2026-04-30)

Pilot is **done**. These files are functional but archive-eligible — they document the N=2 + N=1 Cookiy pilot that informed Phase 1's design.

| File | Purpose |
|---|---|
| `persona_pipeline.py` | Pilot LLM pipeline (Cookiy → GPT-4o → eval) |
| `parse_eval_answers.py`, `parse_construction_answers.py` | Pilot data extractors |
| `run_notebook_local.py`, `build_notebook.py` | Notebook scaffolding |
| `rescore_with_leakage_audit.py`, `make_robustness_chart.py`, `build_site_data.py` | Pilot post-processing |
| `eval_battery.json` | Pilot eval items |
| `leakage_audit.json` | Pilot manual leakage audit |
| `cookiy_brief*.md`, `cookiy_guide*.md` | Cookiy moderator briefs |
| `interview_quality_audit.md`, `survey_quality_audit.md` | Pilot quality audits (gitignored if PII present) |
| `archive/MEETING_HANDOUT.md`, `WRITEUP.md`, `progress_report.md` | Pilot writeups |
| `EXPLAIN_ZH.md`, `CODE_WALKTHROUGH_ZH.md`, `COLAB_RUN_GUIDE.md` | Pilot user guides |
| `outputs/persona_answers_full.json` (gitignored), `metrics_with_leakage_audit.csv`, `chart_robustness.png` | Pilot outputs |

## Layer 6 — Cross-phase research scaffolding

| File | Purpose |
|---|---|
| `LIT_REVIEW.md` | Academic literature review (cross-phase) |
| `BUSINESS_LANDSCAPE.md` | Industry survey (Simile / Aaru / Voicepanel / Synthetic Users / etc.) |
| `replication_scoping.md` | Original Park v2 replication scope analysis |
| `FUTURE_DESIGN.md` | Aspirational design ideas (cross-phase) |
| `gss_variables_to_download.md` | GSS DE variable download workflow |
| `PRIMER.md`, `AGENTS.md` | Cross-AI-tool guidance |

## Layer 7 — External / public

| Path | Purpose |
|---|---|
| `docs/` | GitHub Pages dashboard (`index.html`, `app.js`, `style.css`, `data/`) — pilot results visualization |
| `data/gss/390data1/{batch1,batch2,batch3}/{GSS.dat,GSS.do,post_processing_output.json}` | GSS 2024 raw data (3-batch fixed-width) |
| `2411.10109v2.pdf` | Park v2 paper (gitignored, kept local) |

## Layer 8 — Historical / superseded (kept for reference)

| File | Purpose | Why kept |
|---|---|---|
| `osf_preregistration_appendix_a_theory_predictions.SUPERSEDED-2026-05-09.md` | The 6-theory horse-race draft slimmed away on 2026-05-09 | Referenced from `theory_interpretation_guide.md` + `PROJECT_SYNTHESIS.md` as historical context |
| `GSBGEN390_audit_summary.md` | Original Codex 2026-05-08 research-layer audit text | Source document for the audit fix arc |
| `archive/` | Pre-pivot pilot scaffolds (claude_moderator_prompt, eval_joyce_truth, persona_demographics) | Historical |
| `email_to_bayati.md` (now in `archive/`) | One-off email draft from 2026-04-30 | Historical |

## Layer 9 — Gitignored secrets / PII

| Path | Purpose | Why gitignored |
|---|---|---|
| `Openai_api.txt`, `OpenRouter_api.txt` | API keys | Secrets |
| `cookiy_transcripts/`, `responses/`, `responses_s2/`, `outputs/persona_answers_full.json` | Cookiy participant verbatim transcripts | PII |
| `interview_quality_audit.md`, `survey_quality_audit.md` (if containing direct quotes) | Pilot audits with quotes | PII |
| `2411.10109v2.pdf` | Park v2 PDF | Copyright |
| `*.docx` (e.g., `GSBGEN390_Application_Joyce Yu_v{1,2}.docx`) | Personal application materials | Personal |

---

## Maintenance habits (going forward)

1. **One canonical truth per fact.** If a decision is in `gss_phase1_design.md` §X, the same decision should not be re-stated in `STATUS.md` or `HANDOFF.md` — those should LINK to §X. This file is the cross-reference authority.
2. **Mark superseded files explicitly.** Add `SUPERSEDED-{YYYY-MM-DD}` suffix; do not delete. Linkers to the old name keep working.
3. **Update STATUS.md changelog after every locked decision.** Append a new dated entry; do not rewrite history.
4. **Update HANDOFF.md when the immediate-next-action changes.** §3 state snapshot + §6 next actions are the volatile sections.
5. **Update INDEX.md when a new file is added or moved.** This file should remain accurate within hours of any restructure.
6. **Do NOT move .py files** without checking imports + Path() references (e.g., `gss_pipeline.py:43 TAXONOMY_PATH = WORK / "gss_feature_taxonomy.json"`).
7. **Do NOT move locked artifact JSONs** (`gss_feature_taxonomy.json`, `gss_battery_map.json`, `outputs/primary_eval_human_variance_2024.json`) without an OSF amendment if they are pre-reg-locked.

## How a fresh session should boot up

1. Read `CLAUDE.md` (operating principles)
2. Read `HANDOFF.md` (front door + what to do first)
3. Skim `INDEX.md` (this file — learn what's where)
4. Skim `STATUS.md` TL;DR (what's locked, what's pending)
5. Open `gss_phase1_design.md` only when working on Phase 1 design
6. Open `PROJECT_SYNTHESIS.md` only when paper-writing or stakeholder-presenting

A fresh session should be productive within 60-90 minutes of focused reading.
