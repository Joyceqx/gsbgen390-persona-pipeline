# GSBGEN390 — Independent Reviewer Audit Summary

**Project:** Mini-replication of Park et al. (2024) "Generative Agent Simulations of 1,000 People"
**Lead:** Joyce Yu · **Advisor:** Prof. Mohsen Bayati · **Course:** GSBGEN390, Stanford GSB, Spring 2026
**Audit standard:** Top-tier venue (NeurIPS Datasets & Benchmarks / *Management Science* methods track)
**Reviewer recommendation:** **Major revision before submission.** Trajectory is strong; Phase 1 is publishable conditional on the §3 fixes below.

---

## 1. What the project does (reviewer's understanding)

Decomposes Park v2's aggregate "interview vs. surveys" persona-fidelity gap along a **4 (feature category) × 3 (outcome dimension) matrix** that Park's paper implies but never fills.

| Stage | Status | Description |
|---|---|---|
| **Pilot** | ✅ Done (2026-04-30) | N=2 interview + N=1 survey via Cookiy → GPT-4o → eval. Includes manual leakage audit + LOO ablation. **Feasibility demo only, not inference.** |
| **Phase 1** | 🟢 Pipeline built; awaits API key | GSS 2024 cross-section, N≈1,500, single-wave snapshot prediction. 4-bin LOO primary; ~118 Park-comparable items as sensitivity. Multi-model cheap panel (Qwen / DeepSeek / MiniMax / Kimi) for 1a (N=100) → quality-pre-registered single model for 1b + GPT-4o anchor on N=100. ~$215. OSF pre-reg before 1a fires. |
| **Phase 2** | 📐 Designed, not started | Prolific N=20–30, 30–45 min modular AVP-style interview (4 modules ↔ 4 feature bins), 2-week-separated outcome battery (BFI-44 + behavioral games + GSS). Interview-content-level LOO directly decomposes Park's interview-only condition. ~$1,500–1,750. |

**Composed thesis output:** filled 4×3 matrix in one semester at ~$2,000 — an artifact no published paper currently provides.

---

## 2. Impact assessment

- **Conceptual contribution: real but bounded.** A second-derivative result on Park's framework, not a framework-level advance. Realistic venues: *Management Science* methods, NeurIPS Datasets & Benchmarks, CSCW / FAccT persona auditing.
- **Methodological contribution: stronger than the conceptual one.** Three transferable artifacts:
  1. Leakage audit + strict/broad-clean rescoring procedure.
  2. Multi-model cheap-panel + quality-primary selection rule + named fallback OSF template.
  3. AVP-protocol modular interview + content-level LOO (Phase 2, *if it ships*).
- **Industry relevance: indirect.** Stanford spinout Simile productionizes Park's pipeline; the 4×3 matrix is the closest public artifact to "which inputs matter for which outcomes." Commercial impact bounded by Phase 2's small N; methodological impact larger.

---

## 3. Major concerns (in priority order — these gate publishability)

### 3.1 ⚠️ Constructive auto-correlation in attitudinal feature bin (potentially decision-altering)
The 83-var attitudinal bin contains within-battery correlates of `primary_eval` items (e.g., `ABDEFECT/ABNOMORE/...` predict `ABANY`; same for `CON*`, `NAT*`, `WLTH*`). LOO ΔMAE on the attitudinal bin partly measures auto-correlation, **not persona reasoning**. §11 of the design doc only acknowledges this verbally.

**Park v2 precedent — they faced the same problem and put a number on it.** Park layered three defenses (Park v2, p11 + SI §9, pp. 41–43; pp. 29, 35, 38, 40):
- **Layer 1 — cross-instrument synonym audit (interview ↔ GSS):** GPT-4.1 classifier + manual review + 500-pair human-coded validation across all 54,694 GSS×AVP pairs → **27 GSS items removed** from the eval set.
- **Layer 2 — within-instrument synonym audit (GSS ↔ GSS):** same procedure run internally; *"no two GSS questions are synonymous"* (p42). This is what `gss_phase1_design.md` §9c Layer 2 cites.
- **Layer 3 — whole-block hold-out, asymmetric across instruments:** for **BFI**, Park drops the entire trait block when predicting any item in it; for **GSS main analysis**, Park drops only the predicted item (the more lenient strategy); whole-GSS-module hold-out is reported only as an SI robustness check.

**The empirical anchor (Park v2 p40):** when Park switches the GSS from single-item hold-out to whole-module hold-out, **survey-agent normalized accuracy falls from ~0.82 to 0.77 — a ≈ 0.05 inflation directly attributable to within-module redundancy.** Park measured exactly the inflation §3.1 is concerned about.

**Implication for Joyce's design.** Park's synonym-level defenses (Layers 1 + 2) are already cited. Park does **not** ship a clean defense against non-synonymous same-construct correlation (ABDEFECT ↔ ABANY); whole-block / whole-module ablation is their best partial answer. Joyce's current design is in Park's **strategy-1 regime** (single-item disjointness with `primary_eval`), so Park's measured ≈ 0.05 inflation plausibly applies — likely amplified, since the 83-var attitudinal bin is internally denser than Park's survey input. Park's whole-module result also shows the *ranking* survives even when the inflation is removed (interview agents still beat survey agents, just by less); the analogous expectation for Joyce is that the 4-bin ranking *may* survive R1 — and whether it does is the actual scientific finding.

**Required fixes (recommend R2 as near-mandatory; R1 is the Park-precedented minimum):**
- **R1:** battery-level exclusion (drop entire AB* family when predicting `ABANY`). **Directly mirrors Park's BFI rule and Park's GSS strategy-2 robustness analysis** (cite Park v2 pp. 38, 40). Lowest-risk option.
- **R2:** add a non-LLM correlational baseline (linear/logistic regression on attitudinal features). LLM gain over this baseline = persona-driven contribution; rest = pure auto-correlation any model would exploit. **$0 marginal cost.** This is *beyond* what Park ships — Park's design *brackets* the inflation; a regression baseline lets Joyce *partition* it. A real methodological step past Park.
- **R3:** define a "Park-strict" attitudinal bin that drops every same-battery item; report as sensitivity headline.

### 3.2 LOO over correlated, unbalanced bins is a known weak attribution method
Bin sizes 24 / 25 / 8 / 83 are dramatically unbalanced; the attitudinal bin is internally redundant. LOO ΔMAE is a noisy bin-level estimator.

**Required additions:**
- **Leave-one-in** ablation (start from minimal demo, add bins one at a time) alongside LOO. Disagreement is itself informative.
- **Bin-size-balanced sensitivity:** randomly subsample attitudinal bin to 25 vars × B=200 reruns to bound the "attitudinal dominates because it has 3× more vars" confound.
- **Shapley-style 4-bin decomposition:** 2⁴ = 16 conditions, feasible at ~$15 extra on N=100. More rigorous attribution.

### 3.3 "Robust across LLM families" claim is overstated under all-China-trained panel
The N=1500 1b headline runs on a *single* quality-selected model from a panel of 4 China-trained models (Qwen / DeepSeek / MiniMax / Kimi). The cross-family claim rests only on N=100 1a comparison, not on the headline.

**Required:** narrow abstract claim to "feature-category rankings replicated across four China-trained instruction-tuned models in a 100-respondent comparison; headline 1500-respondent estimate uses a single quality-selected model." Drop "robust across LLM families" from any sentence touching the headline number. Cross-Western/Eastern robustness lives only on the N=100 GPT-4o anchor.

### 3.4 Single-wave snapshot prediction ≠ persona simulation
Phase 1 estimand: `f(features at T) → held-out items at T`.
Park's estimand: `f(2hr interview at T) → items at T+2 weeks, normalized by within-respondent test-retest`.
**Different estimands.** §11 disclaims this; abstract / framing must match.

**Required:** in any Phase 1 published abstract, do not use "persona fidelity" without "within-wave attitudinal" qualifier. Reserve "persona fidelity" for Phase 2 results that have a 2-week recontact baseline.

### 3.5 Phase 2 N=20–30 is statistically thin for 4×3 matrix headline
12 cells × ΔMAE with CIs × 20–30 paired observations. No power calc visible in design docs. Bootstrap ΔMAE CIs at N=30 will be ~±0.05–0.10; cells with effects below ~0.05 are statistically silent.

**Required:** before Phase 2 fires, run a power-calc simulation seeded by Phase 1's empirical bin-level ΔMAE distributions. Pre-disclose which cells of the 4×3 matrix are detectable at N=30 vs. need N≥60.

### 3.6 "Pre-registration" is post-pilot; audit chain has been long
Pilot informed many Phase 1 design choices (eval behavior, leakage shapes, PARTYID scoring). This is fine and standard, but a senior reviewer will note it. Two design upgrades (model-selection rule, theory-driven secondary) locked *after* the audit-driven design was supposedly complete.

**Required:** add a "decisions locked, when, against what evidence" log to the OSF pre-reg. The §12.2 history note ("earlier draft proposed cost-primary … reconsidered the same day") is a good template; extend to all design decisions.

### 3.7 Phase 2 self-hosted Realtime moderator is critical-path risk treated lightly
Building a production-quality voice-to-voice AVP moderator with module-boundary discipline + adaptive depth-probing is non-trivial software (essentially what Park's team built). Phase 2 design treats it as a checkbox. Without depth-probing, Phase 2 produces "longer Cookiy transcripts," not Park-comparable AVP transcripts.

**Required:** before Phase 2 main spend, build and pilot the moderator on N=2–3 internal volunteers. Audit depth-probing against Park's published AVP excerpts. **$50 spike prevents $1500 wasted run.**

### 3.8 Pilot 0.00 / 0.08 MAE numbers risk being decontextualized
`WRITEUP.md` §6.1 and `STATUS.md` headline tables bold `C: 0.00` and `C: 0.08`. Public dashboard at https://joyceqx.github.io/gsbgen390-persona-pipeline/ makes it easy to screenshot out of context.

**Required:** demote bolding; lead with strict-clean column (the honest headline). Add "N=1 / N=2; pipeline feasibility, not statistical claim" prefix to every MAE figure on the public dashboard.

### 3.9 DQ-3 mode-collapse threshold is panel-described but applied in a way too lenient for skewed items
Current spec: "per-item output-code variance averaged across 12 primary_eval items < 0.5 → removed." For items where the *human* GSS distribution is heavily skewed (e.g., `FAIR`, `HELPFUL`), a model that always outputs the modal code achieves low variance + low MAE without being mode-collapsed.

**Required:** redefine DQ-3 as item-level relative threshold: "for each primary_eval item, model output variance must be ≥ X% of the empirical human variance on that item among GSS 2024 respondents." Pre-register X (e.g., 30%).

---

## 4. Minor concerns

- **MDE pre-reg:** With 12 primary_eval items × 4 LOO conditions × ballot-rotation coverage variance, some respondent-condition cells have only 4–8 observations. Pre-register a minimum-detectable Δ.
- **Theory-driven §13 shared-data multiplicity:** §13 reuses the same LLM outputs as the 4-bin primary. Either explicitly frame Phase 1c as exploratory in the published abstract, or pre-register a joint family-wise correction.
- **Public-dashboard sweep:** the "Park used a human interviewer" historical error was patched in 5 docs; do one more end-to-end sweep of dashboard text before Bayati signs off Phase 2.
- **API key hygiene:** `Openai_api.txt` is plaintext at project root. Rotate now if on disk >1 month, regardless of git status — anyone with iCloud folder read access reads it.
- **Stale taxonomy counts:** `STATUS.md` line 38 says "24/25/8/83" but line 173 says "23/29/8/80". Reconcile before OSF lock.
- **Why exactly 12 primary_eval items?** Decision drives LOO statistical power. §9b should add an explicit rationale paragraph (not just "one per construct family").

---

## 5. Recommended action checklist (priority order)

| # | Action | Why | Cost |
|---|---|---|---|
| 1 | Add non-LLM correlational baseline (regression on attitudinal features) alongside every LOO ΔMAE | §3.1 R2 — most decision-altering single addition; cleanly attributes "attitudinal dominates" to persona vs. auto-correlation | $0 |
| 2 | Add Shapley-style 16-condition decomposition at N=100 | §3.2 — reframes LOO as one of multiple convergent attribution methods | ~$15 |
| 3 | Run Phase-1-empirics-seeded power calc for Phase 2's 4×3 matrix | §3.5 — pre-discloses detectable cells; prevents post-hoc "no effect" interpretation | $0 (sim) |
| 4 | Spike-test Phase 2 self-hosted moderator on N=2–3 internal volunteers | §3.7 — $50 prevents $1500 wasted run | ~$50 |
| 5 | Tighten language: drop "persona fidelity" from Phase-1 abstract; restrict "robust across LLM families" to N=100 cheap-panel | §3.3, §3.4 | $0 |
| 6 | Demote pilot 0.00/0.08 MAE bolding; lead with strict-clean; add feasibility banner to public dashboard | §3.8 | $0 |
| 7 | Redefine DQ-3 as item-level relative-to-human-variance threshold; pre-register X% | §3.9 | $0 |
| 8 | Add "decisions locked, when, against what evidence" log to OSF pre-reg | §3.6 | $0 |
| 9 | Reconcile bin-count discrepancies in `STATUS.md` | §4 | $0 |
| 10 | Rotate OpenAI key if on disk >1 month | §4 | $0 |

---

## 6. Strengths to preserve (do not regress)

1. OSF pre-registration before Phase 1a fires, including §12.2 selection rule, Holm-Bonferroni multiplicity, named Qwen fallback.
2. Outcome-stratified framing (corrected from v1's "85%" to v2's 74/82/83/86%, with explicit BFI 0.15 and games 0.28 gaps).
3. Honest disclaiming of pilot N, in-session priming, BFI-10 unsuitability, and LOO instability at N=1 in `WRITEUP.md` §6.2 / §7.4 / §8.
4. Codex-audit-driven design hardening (C-1, C-2, I-1, I-2, I-9, etc.) — adversarial review was *invited and acted upon*.
5. Quality-primary selection rule (`argmin` 1a Likert MAE among DQ-passers, cost as tie-break, Qwen as named fallback). Defends against cherry-picking objection.
6. Disjoint-set rule: features ∩ primary_eval = ∅, with per-item exclusion in sensitivity pass; validator-enforced.

---

## 7. Bottom line

Serious thesis program by a methodologically careful first author. Discipline exceeds GSBGEN390 norm. Phase 1 single-row analysis is on a publishable trajectory **conditional on §3.1 + §3.2 fixes and §3.3 + §3.4 language tightening**. Phase 2 is higher-impact but its largest threat is engineering risk (Realtime moderator) — fixable with a $50 spike before main spend. With the §3 changes, the composed thesis can be a credible single-author submission to *Management Science* methods / NeurIPS Datasets & Benchmarks / CSCW. Without them, it remains a strong class deliverable.

---

## Appendix A — Park v2 precedent for the auto-correlation problem (full citations)

This appendix expands on §3.1 with verbatim citations from Park v2 (`2411.10109v2.pdf`, kept locally in the working folder, gitignored). It is the reference the coding agent should cite when implementing R1, R2, or R3.

### A.1 The three layers of defense Park v2 ships

**Layer 1 — Cross-instrument synonym audit (interview ↔ GSS).** Main paper p11; SI §9, pp. 41–43.

> "We systematically screened all 54,694 possible pairings of GSS items and interview questions — first with a GPT-based classifier, then by human review — for near-duplicate wording (SI section 9). The process flagged 27 GSS items, which we removed to ensure interview-based agents could not boost their accuracy by parroting answers to questions that were effectively asked twice." (p11)

3-step procedure (SI §9, pp. 41–42):
1. GPT-4.1 binary classifier on all 54,694 GSS×AVP pairs.
2. Manual review of all flagged + "unsure" cases → 2 additional demographic items removed.
3. Human coder labels 500 pairs (all model-flagged + stratified-random unflagged); finds 1 missed pair → ≤ 0.4 percentage-point margin.

**Outcome:** 27 GSS items dropped from the evaluation set.

**Layer 2 — Within-instrument synonym audit (GSS ↔ GSS).** SI §9, p. 42.

> "We applied the same procedure to identify questions in the GSS that are synonymous to other GSS questions and **found none**." (p42)

This is what `gss_phase1_design.md` §9c "Layer 2" cites as protection against same-instrument synonymy. **Note:** synonymy ≠ within-construct correlation. Layer 2 does not protect against ABDEFECT ↔ ABANY (ρ ≈ 0.6 from shared construct, not shared wording).

**Layer 3 — Whole-block hold-out, asymmetric across instruments.** SI pp. 29, 35, 38, 40.

| Instrument | Park's hold-out rule |
|---|---|
| **BFI** (main analysis) | Drop **the entire trait block** when predicting any item in it. |
| **GSS** (main analysis) | Drop **only the predicted item** (single-item hold-out — the more lenient strategy). |
| **GSS** (SI robustness) | Drop **the whole GSS module** containing the predicted item — reported only as a robustness check. |

Park's framing of the asymmetry (SI p. 38):
> "First, we remove only the outcome question we predict from the input data for the agent. ... Second, we hold-out the whole GSS module a given outcome question is in. This approach means the survey agents have fewer access to similar questions than the interview agents have, whereas the first strategy ensures the survey agents have access to more similar questions than the interview agents."

### A.2 The empirical anchor — Park measured the inflation directly

SI p. 40, comparing strategy 1 (single-item hold-out) vs. strategy 2 (whole-module hold-out):

> "Survey Agents: When excluding question-answer pairs from the same category as the predicted question, survey agents performed similarly compared to interview-based agents. Specifically, the survey agents reached a normalized accuracy of **0.77 (std = 0.13)**." (p40)

vs. ~0.82 (std = 0.13) under strategy 1 in the main paper.

**Anchor figure: ≈ 0.05 normalized-accuracy points of survey-agent inflation comes from within-GSS-module redundancy.** Park's main reported numbers are from the inflation-friendly regime (strategy 1); the deflated number sits in the SI.

### A.3 What this means for Joyce's design — implementation guidance

- Joyce's current design uses Park's **strategy-1 regime** for the GSS (single-item disjointness with `primary_eval` only, enforced by the `gss_feature_taxonomy.json` validator). The Park-measured ~0.05 inflation plausibly applies, **likely amplified** because the 83-var attitudinal bin is internally denser than Park's heterogeneous survey input (Park's input mixes GSS modules; Joyce's bin concentrates same-construct items).
- Park's whole-module result also shows the *ranking* survives even when the inflation is removed: interview agents still beat survey agents at 0.82 vs. 0.77, just by less. **The analogous expectation for Joyce is that the 4-bin LOO ranking *may* survive R1; whether it does is the actual scientific finding.**
- **R1 (battery-level exclusion) directly mirrors Park's BFI rule and Park's GSS strategy-2 robustness analysis.** Cite Park v2 SI pp. 38, 40 as the precedent in the writeup. Implementation: when predicting any item in a GSS battery (AB*, CON*, NAT*, WLTH*, FE*, RAC*, ...), drop the entire battery from the attitudinal feature bin for that respondent.
- **R2 (non-LLM correlational baseline) is beyond what Park ships.** Park's design *brackets* the inflation between strategies 1 and 2. A linear / logistic regression baseline on the attitudinal feature bin lets Joyce *partition* it: LLM-with-attitudinal vs. pure regression-on-attitudinal = persona-driven gain; the rest = pure auto-correlation any model would exploit. This is a methodological step *past* Park. **Recommend implementing as a $0 sensitivity column alongside the headline.**
- **R3 (Park-strict attitudinal bin)** is the most aggressive option: pre-define an attitudinal feature bin that drops every item whose own GSS battery overlaps with any `primary_eval` item, and run that as a sensitivity headline. Park's 0.05 anchor is the upper bound on what this should change.

### A.4 Quick reference — Park v2 page index for §3.1

| Topic | Park v2 location |
|---|---|
| 27-item cross-instrument removal procedure (Layer 1) | Main p. 11; SI §9, pp. 41–43 |
| GSS-internal synonymy = none (Layer 2) | SI §9, p. 42 |
| BFI whole-trait-block hold-out rule | SI pp. 29, 35 |
| GSS strategy 1 vs. strategy 2 framing | SI p. 38 |
| Strategy 2 numerical result (0.77 vs. 0.82 ≈ 0.05) | SI p. 40 |
| Random-lesion robustness (drop 80% of interview → 0.79) | SI p. 41; main p. 7 |
| Direct retrieval vs. inference decomposition | SI pp. 46–50 |
