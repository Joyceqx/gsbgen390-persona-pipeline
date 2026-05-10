# HANDOFF — GSBGEN390 (for a fresh Claude session)

**Created:** 2026-05-08 · **Last refreshed:** 2026-05-09 (lean-design lock + housekeeping)
**Author of project:** Joyce Yu (Stanford GSB master's thesis, advisor Prof. Mohsen Bayati)
**Read this file first.** It points you to the canonical sources and tells you the immediate next action. It is NOT a replacement for `STATUS.md` — it's the front door.

---

## 1. What this project is, in 5 sentences

GSBGEN390 is a Stanford GSB master's thesis on **feature attribution for LLM persona synthesis** — when an LLM is prompted to respond as a specific human individual, which input feature categories (demographic / behavioral / psychological / attitudinal) actually drive prediction quality, and how does this contribution vary across outcome dimensions (attitudes / personality / behavior)? Phase 1 answers this question for the **attitude** outcome dimension at N≈1500 using GSS 2024 public data, a multi-model OpenRouter panel + GPT-4o anchor, R1+R2 leakage hygiene (battery exclusion + regression-baseline partition), and the §12.2 quality-primary model-selection rule. Phase 2 (planned) extends the analysis to **personality** (BFI-44) + **behavioral economic games** outcome dimensions via targeted Cookiy collection with 2-week recontact baseline. Park et al. 2024 (arXiv:2411.10109 v2) is the most-cited prior work in LLM persona simulation; this project anchors against Park for cross-paper benchmarking (GPT-4o anchor on N=100 subset → direct comparison with Park v2 SI Table 3) but the research question stands independently. Pilot phase (N=2+1 via Cookiy) is complete; **Phase 1 pipeline is 100% built and lean-design-locked as of 2026-05-09; the only blocker is dropping in an OpenRouter API key for smoke tests + filing OSF pre-registration.**

---

## 2. Read-in order for a fresh session

```
1. CLAUDE.md                       — operating principles (rigor over velocity, pre-reg discipline, Park comparability)
2. HANDOFF.md                      — this file (front door)
3. INDEX.md                        — file map (NEW 2026-05-09; what every file is)
4. STATUS.md                       — TL;DR + dated changelog (skim the TL;DR + the 2026-05-09 changelog entry)
5. gss_phase1_design.md            — LEAN-LOCKED Phase 1 design (esp §4 method, §10 aggregation, §12.2 quality-primary
                                      selection rule, §13 secondary analyses, §11.1 abstract language template)
6. theory_interpretation_guide.md  — Discussion-section memo (6 candidate frameworks for interpretive secondary analysis)
7. PROJECT_SYNTHESIS.md            — paper-ready bilingual synthesis (ZH then EN; comprehensive design, decisions, criticisms)
8. tier1_tool_schemas.md           — schemas for the 2 secondary tools (Shapley + Battery LOO)
9. gss_feature_taxonomy.json       — v0.3 locked (12 primary_eval, 118 sensitivity_eval, 140 features × 4 bins)
10. gss_battery_map.json            — **v0.2 locked 2026-05-09** (34 batteries: 7 D + 10 B + 2 P + 15 A; 17 singletons; for R1 + co-primary Battery LOO)
11. theory_review.md / theory_review_round2.md — literature scaffolds (informational, not driving primary findings under lean lock)
```

For Phase 2 / pilot context, also: `thesis_phase2_design.md`, `MEETING_HANDOUT.md`, `WRITEUP.md`, `progress_report.md`, `replication_scoping.md`.

---

## 3. State snapshot (2026-05-09)

| Phase | State | Key blocker |
|---|---|---|
| Pilot (Cookiy N=2+1) | ✅ done; GitHub repo + GitHub Pages dashboard live | — |
| Phase 1 pipeline (loader, audit primitives, multi-model orchestrator, atomic-write driver, R1+R2 leakage hygiene, §12.2 selector, R2 regression baseline) | ✅ 100% built, all tests pass | — |
| Phase 1 design lock | ✅ LEAN-LOCKED 2026-05-09 + Battery LOO promoted to co-primary 2026-05-09 evening (4-bin LOO + 34-battery LOO across all 4 bins co-primary; Shapley robustness; theory-as-Discussion) | — |
| Phase 1 N=10 smoke test on real LLMs | 🟡 awaiting OpenRouter API key | needs key in `OpenRouter_api.txt` |
| OSF pre-registration | 🔒 awaiting (a) Joyce + Bayati signoff on `theory_interpretation_guide.md` open items + (b) smoke green | blocks Phase 1a |
| Phase 1a (N=100, ~$65 with anchor) | 🔒 blocked on pre-reg | — |
| §12.2 selector run on 1a output | 🔒 blocked on 1a complete | — |
| Phase 1b (N=1500, ~$95 selected model + ~$50 anchor) | 🔒 blocked on §12.2 selector | — |
| Shapley decomposition (Phase 1a) | 🔒 tool to be implemented (~Day 3-4 of forward plan) | — |
| Battery LOO (Phase 1c, all 4 bins, **co-primary**) | 🔒 tool to be implemented (`battery_loo.py`); ~$50-60; **unconditional**; nested Holm per-bin (D=7/B=10/P=2/A=15) | — |
| Phase 2 (Cookiy + Prolific, BFI + behavioral games) | 📅 planned, not started; design in `thesis_phase2_design.md` | awaits Phase 1 wrap + power calc |

**Phase 1 budget:** ~$215 total at N=1500 (within original $300-500 envelope).

**Tests passing as of 2026-05-09**: `validate_taxonomy.py` 10 checks (incl. 7c battery map), AUDIT A/B/B-regression/C/D/E pipeline tests, §12.2 selector 5-branch self-test, R2 regression baseline self-test (12/12 items scored).

---

## 4. Phase 1 design at a glance (lean lock 2026-05-09)

### Primary contribution
*Which survey-collectible feature categories actually improve LLM persona prediction of GSS attitude outcomes?* — answered by **4-bin LOO ablation** (demographic / behavioral / psychological / attitudinal).

### Co-primary analyses (locked 2026-05-09 evening)
- **Primary headline #1 — 4-bin LOO** (broad finding): which feature category contributes most? `gss_phase1_design.md` §4 + §10
- **Primary headline #2 — 34-battery LOO across all 4 bins** (mechanistic finding): which construct-level clusters drive the signal within each bin? Nested Holm per-bin (D=7 / B=10 / P=2 / A=15). `gss_phase1_design.md` §13.2 + `gss_battery_map.json` v0.2

### Secondary analyses
- **Bin-level Shapley decomposition** (16 conditions) — robustness on 4-bin LOO ranking against bin interactions (shares 4-bin family multiplicity). `gss_phase1_design.md` §13.1
- **Theory interpretation** — 6 candidate frameworks discussed qualitatively in Discussion section only; NOT a horse race, NO preregistered numeric thresholds. `theory_interpretation_guide.md`

### §12.2 quality-primary model-selection rule (locked)
Phase 1a runs all 4 cheap OpenRouter models on N=100 + GPT-4o anchor. The §12.2 selector picks the Phase 1b model:
- **Primary score**: respondent-macro Likert MAE on 1a primary_eval items (full condition only)
- **DQ-1**: parse-failure rate > 30% disqualifies
- **DQ-3** (per-item relative): for each primary_eval item, `var(model_i) ≥ 0.30 × var(human_2024_i)`; >50% items failing disqualifies
- **Tie-break**: within 5% of best MAE, pick lowest `cost × (1 + parse_fail)`
- **Fallback**: Qwen-2.5-72B-Instruct if all DQ-fail or quality+cost ties
- See `gss_phase1_design.md` §12.2 + `select_phase1b_model.py`

### Leakage hygiene (4 layers)
1. Disjointness: feature_bins ⊥ primary_eval (validator-enforced)
2. Synonymy: GSS-internal synonymy = empty (Park v2 SI §9, verified)
3. **R1 — battery exclusion**: when predicting any item in a battery, drop the entire battery from prompt (mirrors Park BFI rule; 15 batteries + 9 singletons in `gss_battery_map.json`)
4. **R2 — regression-baseline partition**: non-LLM regression on same input partitions LLM gain from auto-correlation (Beyond Park v2; `regression_baseline.py`)

### Deferred (NOT in lean lock — see `gss_phase1_design.md` §13.4)
RSA, permutation importance theory adjudication, Stage 3 refinement experiments, six-theory horse race with hard numeric thresholds, theory-bin LOO as confirmatory family, Friedman & Popescu (2008) H-statistic.

---

## 5. Literature review state (informational under lean lock)

### Round 1 — `theory_review.md` (2026-05-06, scaffold by AI)
4 candidates surveyed, all foundational citations + GSS-item mapping sketched:
- §2 **Moral Foundations Theory** (Haidt; 5-6 foundations) — strong fit, contested-theory risk
- §3 **Schwartz Theory of Basic Values** (10 values / 4 quadrants) — moderate-strong fit, indirect mapping
- §4 **Bourdieu's Forms of Capital** (economic / cultural / social) — best as supplementary for demographic+behavioral bins
- §5 **Cultural Theory of Risk** (Douglas-Wildavsky; 4 worldviews) — strong fit for political items, niche

§8 lock decision: **still empty.**
§10 (prior LLM-applied work): explicitly admitted no 2024-2026 sweep; flagged hallucination risk; verified Tjuatja 2024 is response-bias work, not MFT-on-LLM.

### Round 2 — `theory_review_round2.md` (2026-05-07, this session)
**Headline recommendation:** evaluate **Inglehart-Welzel 4-quadrant** (top) + **Big Five-as-input** (secondary) alongside Round-1's MFT/Schwartz.

What was added (verified citations from web search 2026-05-07):
- §2 — 5 additional candidates: Big Five/HEXACO, Inglehart-Welzel cultural map (top recommend; clean GSS-WVS lineage), Hofstede (skip — country-level), Theory of Planned Behavior (Phase-2 only), Self-Determination Theory (skip), Dual-Process (framing only)
- §3 — verified 2024-2026 LLM-applied work in 4 buckets:
  - **Methodological backbone**: Binz & Schulz PNAS 2023, Hagendorff 2023, Pellert PPS 2024, Centaur Nature 2025, Ye et al. systematic review arXiv:2505.08245 + Awesome-LLM-Psychometrics repo
  - **Theory-as-input persona work**: Big5-Chat (ACL 2025, arXiv:2410.16491), "Do LLMs Have Consistent Values?" ICLR 2025, Bridging Values and Behavior, Cultural Alignment in LLMs (arXiv:2309.12342), Break the Checkbox (arXiv:2502.08045), PersonaLLM (NAACL 2024)
  - **Silicon-sampling neighbors**: Argyle 2023, Aher 2023, Bisbee 2024, Hewitt et al. 2024, Manning-Zhu-Horton NBER 32381, Santurkar 2023, Horton 2023
  - **Critical/skeptic**: Salecha PNAS Nexus 2024 (social desirability bias on BFI-on-LLM), Kosinski PNAS 2024, Ullman 2023, persona vectors (arXiv:2507.21509)
- §4 — tiered reading list: Tier 1 must-read ~5.5h (Pellert 2024 / Ye 2025 / Centaur 2025 / Hewitt 2024 / Salecha 2024), Tier 2 theory-specific ~3-5h, Tier 3 context, Tier 4 Phase-2/cross-cultural
- §6 — 4 open questions for Bayati: theory steer, multi-theory family pre-reg with Holm-Bonferroni, Salecha-bias relevance, symmetric input/output design

Round-2 explicit gaps (NOT covered):
- Behavioral-economics frameworks (Prospect Theory, bounded rationality)
- Predictive-processing / Bayesian theory of mind
- Identity theories (Tajfel social identity, Markus & Kitayama self-construal)
- Chinese-language psychology relevant to the China-trained 4-cheap-panel

Also flagged for Joyce: Inglehart-Welzel + Hofstede textbook citations in Round-2 §2.2 / §2.3 are recall-based (NOT from the Round-2 web searches) — verify before pre-reg quoting.

---

## 6. Immediate next actions (in order)

For Joyce (gating Phase 1a):
1. **Get an OpenRouter API key** at https://openrouter.ai/keys (load $5 in credits) → drop in `OpenRouter_api.txt` (gitignored). This is the most important blocker — paid smoke tests cannot start without it.
2. **Sign off on `theory_interpretation_guide.md` open items** (4 items in §"Open items for Joyce / Bayati before Phase 1a"): theory candidate list, null-alignment reporting commitment, Discussion structure (data-organized vs theory-organized), Inglehart-Welzel citation verification.
3. **Optional reading for context** (NOT blocking): `theory_review_round2.md` Tier 1 (~5.5 h: Pellert 2024 + Ye 2025 + Centaur 2025 + Hewitt 2024 + Salecha 2024). Helpful for the Discussion section but not for the OSF pre-reg under the lean lock.

For the next Claude session, after Joyce drops the API key:
4. **Run smoke tests** in this exact order:
   ```
   python3 llm_router.py --smoke-one          # ~$0.001 / 5s
   python3 llm_router.py --smoke-panel        # ~$0.005 / 30s
   python3 gss_driver.py --smoke              # ~$0.02 / 1 min
   python3 gss_driver.py --n 10 --primary-only  # ~$0.70 / 30-60 min
   python3 gss_driver.py --n 10               # ~$2.00 / 2-3 hours (with sensitivity)
   ```
5. **Draft OSF pre-registration** under the lean lock + Battery-LOO-co-primary upgrade. Locked items: **two co-primary analyses** (4-bin LOO + 34-battery LOO across all 4 bins with nested Holm per-bin) + Shapley robustness on 4-bin + §12.2 quality-primary selection rule + R1+R2 leakage hygiene + §11.1 abstract language template + null-alignment reporting commitment from `theory_interpretation_guide.md`. Source template: `PROJECT_SYNTHESIS.md` §3 + §4 (decision log).
6. **Phase 1a** (N=100, ~$65 with anchor) → §12.2 selector picks Phase 1b model.
7. **Phase 1b** (N=1500, ~$95 selected model + ~$50 anchor) → primary analysis.
8. **Implement Tier 1 tools** (`shapley_decomposition.py` for 4-bin robustness, `battery_loo.py` for 34-battery co-primary across all 4 bins) per `tier1_tool_schemas.md` schemas. Shapley runs on Phase 1a (~$25 incremental); Battery LOO runs on Phase 1c **unconditionally** (~$50-60 incremental).

**NOT in the lean Phase 1 plan** (deferred to future work — see `gss_phase1_design.md` §13.4): theory-bin LOO as confirmatory family, building `gss_theory_taxonomy.json`, RSA, permutation importance theory adjudication, Stage 3 refinement experiments, six-theory horse race with hard numeric thresholds.

Also outstanding (lower priority): Codex-deferred I-6 concurrency in `call_panel`. Irrelevant to N=10 smoke; flag for pre-Phase-1b implementation.

---

## 7. Operating principles (must follow; from CLAUDE.md)

1. **Methodological rigor over velocity.** Default to the most defensible setup, surface trade-offs, treat every choice as if a hostile reviewer is reading.
2. **Pre-registration discipline.** Lock the analysis plan in writing before any data analysis at scale. Never silently change a pre-registered choice mid-analysis. If a change is needed, flag it explicitly and log as a deviation.
3. **Comparability with Park v2.** Park 2024 v2 is the live benchmark. Every claim that touches AI persona fidelity should reference Park's per-item Table 3 numbers (74/82/83/86%).
4. **Statistical claims need right N + uncertainty.** N=2+1 supports directional/feasibility claims only. N=1500+ supports proper feature-importance inference. Never imply inferential certainty at low N.
5. **Privacy.** Cookiy transcripts (verbatim PII), `Openai_api.txt`, `OpenRouter_api.txt`, `cookiy_transcripts/`, `responses/`, `responses_s2/`, audit files with quotes, `persona_answers_full.json`, `*.docx` are all gitignored. Maintain that.
6. **Ask before acting** on any non-trivial methodological choice. Auto-mode is fine for code edits and routine scripting, NOT for experimental-design choices.

---

## 8. Open questions for Bayati (queue for next meeting)

From `theory_review_round2.md` §6 (rephrased under lean lock — theory is Discussion-only, not pre-registered):
1. **Discussion-section emphasis** — among the 6 candidate frameworks listed in `theory_interpretation_guide.md` (MFT / Schwartz / Bourdieu / Cultural Theory / Inglehart-Welzel / Big Five), which 1–2 does Bayati want featured most prominently in the Discussion's interpretive subsection? (No pre-registered horse race — qualitative interpretation only.)
2. **Symmetric input/output design** — if Big Five is featured in the Discussion as a Phase-1 *input* organization, Phase-2 will measure BFI as an *outcome*: methodologically clean or creates an unfair advantage at Phase-2 eval?
3. **Salecha 2024 social-desirability bias** — relevant for Phase 1 (BFI is only Phase-2 outcome) or just a Discussion-section caveat?

From `STATUS.md` open methodological questions:
- Leakage-filtered analysis sufficient defense of pilot's C-condition result, or needs 2-week-separated collection?
- LOO ranking instability at N=1: what N + how many seeds buy stable ranking?
- 2-week self-retest with pilot respondents to recover Park-comparable denominator?
- BFI-10 → BFI-44 upgrade for Phase 2: yes/no?
- 4-category taxonomy holds at scale, or finer subdivisions needed?
- Cookiy as Phase-2 platform, or pivot to Prolific?

---

## 9. Work-tree quick reference (see STATUS.md §"Current work tree" for full)

```
GSBGEN390/
├── DESIGN + NARRATIVE
│   ├── README.md, STATUS.md (canonical), HANDOFF.md (this), CLAUDE.md, AGENTS.md, PRIMER.md
│   ├── replication_scoping.md, FUTURE_DESIGN.md, BUSINESS_LANDSCAPE.md
│   ├── LIT_REVIEW.md (academic), MEETING_HANDOUT.md, WRITEUP.md, progress_report.md
│   └── EXPLAIN_ZH.md, CODE_WALKTHROUGH_ZH.md, COLAB_RUN_GUIDE.md
│
├── PHASE 1 (GSS PUBLIC) DESIGN + ARTIFACTS
│   ├── gss_phase1_design.md         ← LEAN-LOCKED design (§4/§9c/§10/§11.1/§12.2/§13 most relevant)
│   ├── theory_review.md             ← Round-1 lit review (informational under lean lock; §8 lock unused)
│   ├── theory_review_round2.md      ← Round-2 lit review (Inglehart-Welzel + Big Five + verified 2024-2026 LLM-applied work)
│   ├── theory_interpretation_guide.md ← Discussion-section memo for 6 candidate frameworks (lean replacement)
│   ├── tier1_tool_schemas.md        ← schemas for Shapley + Battery LOO secondary tools
│   ├── gss_variables_to_download.md
│   ├── gss_feature_taxonomy.json    ← v0.3 LOCKED
│   ├── gss_battery_map.json         ← **v0.2 LOCKED 2026-05-09** (34 batteries: D=7/B=10/P=2/A=15; 17 singletons; for R1 + co-primary Battery LOO)
│   ├── outputs/primary_eval_human_variance_2024.json ← LOCKED DQ-3 reference
│   ├── gss_loader.py, validate_taxonomy.py (10-check incl. 7c battery map)
│   ├── gss_pipeline.py              ← AUDIT primitives + R1 battery exclusion + multi-model panel synthesis
│   ├── llm_router.py                ← OpenRouter / OpenAI client + 8-attempt backoff
│   ├── gss_driver.py                ← top-level orchestrator with atomic-write resumability + item-level sensitivity resume + I-10 reproducibility guard
│   ├── select_phase1b_model.py      ← §12.2 quality-primary rule executable + 5-branch self-test
│   └── regression_baseline.py       ← R2 regression baseline (Layer 4 leakage hygiene partition)
│
├── PHASE 2 DESIGN
│   └── thesis_phase2_design.md
│
├── PILOT (COOKIY)
│   ├── eval_battery.json, eval_answers_extracted.csv, construction_answers_extracted.csv
│   ├── persona_pipeline.py / .ipynb, run_notebook_local.py
│   ├── parse_eval_answers.py, parse_construction_answers.py
│   ├── rescore_with_leakage_audit.py, make_robustness_chart.py, build_site_data.py
│   └── outputs/ (metrics_per_respondent, metrics_with_leakage_audit, chart_robustness)
│
├── DASHBOARD
│   └── docs/ (GitHub Pages — index.html, app.js, style.css, data/)
│
├── DATA
│   └── data/gss/390data1/{batch1,batch2,batch3}/{GSS.dat, GSS.do, post_processing_output.json}
│
├── GITIGNORED (PII + secrets)
│   ├── interview_quality_audit.md, survey_quality_audit.md, leakage_audit.json
│   ├── Openai_api.txt, OpenRouter_api.txt
│   ├── 2411.10109v2.pdf (Park v2)
│   ├── GSBGEN390_Application_Joyce Yu_v{1,2}.docx
│   ├── cookiy_transcripts/, responses/, responses_s2/
│   └── outputs/persona_answers_full.json, outputs/logs/
│
├── archive/                         ← stale pre-pivot files
└── test/                            ← synthetic transcript fixtures
```

Output convention for Phase 1 runs: `outputs/gss_phase1_records_n{N}_*.json` (atomic-write per respondent; resumable via `--resume`, on by default).

---

## 10. Known runtime gotchas (for the smoke-test session)

**Phase 1 / GSS:**
- GSS DE splits the 973-variable extract into 3 batches; `gss_loader.py` merges horizontally with per-batch label-set namespacing (`b0_GSP002X`, `b1_GSP002X`) to avoid cross-batch label collisions. Final shape 3,309 × 973.
- GSS missing codes are negative integers in `{-100,-99,-98,-97,-96,-95,-90,-80,-70,-60,-50,-40}`. Use `gss_loader.is_missing()` and `truth_code_or_none()`.
- Ballot rotation → many GSS items aren't asked of every respondent. Aggregation uses respondent-macro averaging.

**Phase 1 / LLM panel:**
- OpenRouter API key required before any actual LLM call. Put in `OpenRouter_api.txt` at project root (gitignored via `*api*` pattern).
- The 4-cheap-panel run is sequential (~30-60 min for N=10 primary). Could parallelize via threadpool/async — not a priority; smoke first. Codex flagged this as I-6 (deferred until pre-1b).
- Each model has different rate limits. Dispatcher has 8-attempt exponential backoff (caps at 60s) for 429 / timeout / 5xx.
- `gss_driver.py` writes records atomically per respondent. Kill + resume with same command + `--resume` (on by default).
- PARTYID code 7 ("Other party") is contingent: scored as Likert MAE on 0-6, categorical exact-match when either side outputs 7.
- HELPPOOR has sparse codebook anchors at 1, 3, 5; codes 2 and 4 are valid intermediate positions.

**Pilot phase:**
- TPM rate limit on gpt-4o is 30K tokens/min on this account. Condition C prompts hit this; runner has retry+backoff.
- Notebook Cell 8 uses `google.colab.files.upload()` (doesn't work locally); runner replaces with disk reads.
- Cell 16 uses `display()` (Jupyter built-in); runner stubs to `print()`.
- Jupyter magics silently skipped by the runner.

---

## 11. Pre-validated commands (no API key needed; safe to run anytime)

```bash
cd /Users/joyce/Documents/GSBGEN390

python3 gss_loader.py
python3 validate_taxonomy.py

python3 gss_pipeline.py --print-prompt          # AUDIT-A
python3 gss_pipeline.py --print-questions       # AUDIT-B
python3 gss_pipeline.py --test-scoring          # AUDIT-C
python3 gss_pipeline.py --test-exclusion        # AUDIT-D
python3 gss_pipeline.py --test-aggregation      # AUDIT-E
python3 gss_pipeline.py --test-multimodel       # multi-model extension
```

All 6 audit smoke tests must continue to pass.

---

## 12. The one-paragraph paper claim (lean lock 2026-05-09)

*Park et al. 2024 v2 demonstrates that 2-hour AVP-style interview transcripts produce LLM personas whose GSS-attitude predictions reach ~0.83 (vs ~0.82 for demographic-only surveys). Phase 1 of this thesis tests the cheaper survey-style condition at scale (N=1500) using public GSS 2024 data, organizes the persona's input features into 4 pre-registered bins (demographic / behavioral / psychological / attitudinal), and runs a leave-one-out ablation on the §12.2 quality-selected model + GPT-4o anchor (N=100), with cross-model robustness from the Phase 1a 4-cheap-OpenRouter-model panel. Two pre-registered secondary analyses extend the primary: bin-level Shapley decomposition (16-condition robustness on the 4-bin LOO ranking) and attitudinal-bin Battery LOO (within-bin interpretability, conditional on attitudinal-bin dominance). The contribution is: (a) the first systematic feature-importance ablation on Park's GSS-attitudes outcome row at N=1500 with R1 battery-level structural exclusion + R2 regression-baseline partition (a partition test Park v2 itself does not run); (b) a reusable §12.2 quality-primary multi-model selection rule with named Qwen-2.5-72B fallback; and (c) Discussion-section qualitative interpretation across 6 candidate cognitive/sociological frameworks (per `theory_interpretation_guide.md`) — null or mixed alignment reported with equal prominence.*

---

**End of handoff.** A fresh session that reads this file + STATUS.md + theory_review_round2.md + gss_phase1_design.md should be fully briefed within 60-90 minutes of focused reading.
