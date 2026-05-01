# GSBGEN390 — Pilot Replication Status (One-Page Brief for Prof. Bayati)

**Joyce Yu · 2026-04-30**

## What I built in this sprint

A working end-to-end pipeline that mirrors **Park et al. 2024 ("Generative Agent Simulations of 1,000 People")** at small scale, plus the seeds of a feature-importance analysis the original paper did not perform.

**Two-arm design** (forced by Cookiy's 15-min cap and inability to pair respondents across studies):

| | Study 1 — Interview arm | Study 2 — Survey arm |
|---|---|---|
| N | 2 panel respondents | 1 panel respondent |
| Format | 15-min combined session: ~9 min open AVP-style interview + ~6 min held-out eval | 15-min structured: 18 construction items + same 15 held-out eval |
| Conditions tested | A demographics-only, B persona description, C interview-conditioned | A demographics-only, D survey-conditioned, **+4 LOO ablations** dropping each of {demographic, behavioral, psychological, attitudinal} |

**Key pipeline characteristics:**
- Persona-in-context architecture (transcript → LLM system prompt), identical to Park's method.
- Default model: GPT-4o (Park-comparability); Claude Sonnet 4.6 supported via env var for robustness check.
- Each eval item asked twice at temperature 0.7 to compute self-consistency *in addition to* accuracy-vs-truth.
- Smart parser uses the moderator's confirmation utterance as gold signal — robust against participant multi-attempt answers.
- Pipeline now achieves **100% parse rate** (15/15 eval × 3 respondents; 18/18 construction × 1 respondent).

## Important correction to the proposal

Park's headline numbers (% of test-retest reliability on held-out GSS items):
- **Demographics only: 74%**
- **Interview only: 83%**
- **Surveys only: 82%**
- **Interview + surveys: 86%**

The proposal v2 cited "85%" for the interview condition — actual is 83%. **More importantly: surveys-only (82%) is one percentage point off interview-only (83%).** This is direct prior evidence that survey-collectible features can approach interview-quality fidelity, and it transforms the thesis question from *"can surveys substitute for interviews?"* (largely yes) to *"which survey features account for the substitution?"* (the deeper, more publishable question).

## Five design pivots forced by Cookiy's constraints

1. **N=1 (Joyce-only) → multi-respondent panel.** Methodological objection: self-experimentation can't test the central question.
2. **Two split sessions → one comprehensive session.** Cookiy can't pair the same respondent across studies.
3. **75–90 min comprehensive interview → 15-min combined session.** Cookiy's per-interview duration cap.
4. **Added Study 2 (survey-only arm).** Mirrors Park's main framework; aligned with thesis emphasis on survey methodology.
5. **In-session eval rather than 2-week-separated.** Acknowledged limitation: likely inflates absolute accuracy via priming; pilot is honest about this.

## What the meeting needs to discuss

1. **In-session eval priming** — accept as a v1 limitation, or redesign for 2-week separation (requires a panel platform that supports recontact)?
2. **LOO category granularity** — 4 categories (demographic / behavioral / psychological / attitudinal) at pilot scale. For the thesis, do we keep this taxonomy or subdivide further? Park's "surveys" was a single bucket; my four-bin approach is a real extension.
3. **N for the thesis-stage replication.** Pilot is N=2+1. Real study probably needs N≥30 per arm to put error bars on LOO effects.
4. **Test-retest baseline.** Park reports % of test-retest reliability. We don't have that. Should we run a 2-week self-retest with our pilot respondents to recover the denominator?
5. **AI-moderator paraphrase variance.** Cookiy moderators paraphrase questions — affects eval-item wording across respondents. Real concern at scale, or acceptable noise?

## Status of deliverables

| Deliverable | Status |
|---|---|
| Scoping document (`replication_scoping.md`) | ✅ Done — design rationale, Park's actual numbers, pipeline diagram |
| 15-item held-out eval battery (`eval_battery.json`) | ✅ Done with explicit anchors |
| 18-item construction battery (in pipeline) | ✅ Done |
| Cookiy briefs (Study 1 + Study 2) | ✅ Done; both studies completed |
| 3 Cookiy transcripts | ✅ Collected, audited usable |
| Truth-answer extraction CSV (`eval_answers_extracted.csv`) | ✅ 100% parse rate |
| Persona pipeline (`persona_pipeline.py`) | ✅ Smoke-tested |
| **Colab notebook (`persona_pipeline.ipynb`)** | ✅ Ready; also runs locally via `run_notebook_local.py` |
| **Persona-construction run (LLM calls)** | ✅ **Completed locally** — 12 conditions × 15 items × 2 samples; ~$4 in API |
| **Leakage-robustness audit** | ✅ Completed — `metrics_with_leakage_audit.csv`, `chart_robustness.png`, `leakage_audit.json` |
| 3-5 page writeup | 🔴 To do |

## Results

### Headline table — Likert MAE per condition (lower = closer to truth)

| Arm | Resp. | A demo | B desc | C/D | LOO best | LOO worst |
|---|---|---|---|---|---|---|
| Study 1 | P1 | 0.83 | 0.92 | **C: 0.08** | — | — |
| Study 1 | P2 | 1.17 | 0.75 | **C: 0.00** | — | — |
| Study 2 | S2-P1 | 0.50 | — | D: 0.83 | drop attitudinal: 0.58 | drop demographic: 1.17 |

Self-consistency, BFI-trait RMSE, and categorical accuracy are in `metrics_per_respondent.csv`.

### What the numbers say

**Study 1 (interview arm) — interview conditioning effect is large.** C beats A by ~0.75–1.17 MAE on both respondents. This direction matches Park's 83% (interview-only) > 74% (demographics-only).

**Study 2 (survey arm) — A > D unexpectedly.** Adding the 18 construction items on top of demographics did *not* improve accuracy for this respondent. With N=1, this could be noise (≈ 2 items more wrong out of 12) or a real signal that needs rich-context survey items beyond demographics aren't always additive. The LOO ranking shows dropping demographics hurt most (MAE 0.50 → 1.17), then psychological (0.92), then behavioral and attitudinal (smaller deltas).

**Caveat:** N=2 + N=1 cannot statistically separate any of these effects. Pilot demonstrates the architecture works; numbers are illustrative.

### Leakage robustness audit (defense against the "in-session priming" objection)

Because Cookiy can't pair respondents across studies, our eval is administered in the same session as the interview/construction — Park's protocol uses a 2-week gap. This means **some eval items have their answer effectively pre-stated in the interview** (e.g., P1 disclosed political ideology during the open-interview portion, then minutes later was asked to self-place on the 1–7 liberal-conservative eval scale). Question: is C's win driven by leakage or by real prediction?

I manually audited each of the 15 eval items per respondent against their interview transcript and tagged each as **STRONG** (construct directly stated by participant or paraphrased by moderator), **SOFT** (construct semantically related), or **CLEAN** (no detectable mention). Tags + evidence quotes are in `leakage_audit.json`. Then I re-scored each condition under three filters:

| | full_eval (15) | strict-clean (drop STRONG) | broad-clean (drop STRONG + SOFT) |
|---|---|---|---|
| P1/A | 0.83 | 0.70 | 1.00 |
| P1/B | 0.92 | 0.80 | 1.00 |
| **P1/C** | **0.08** | **0.10** | **0.00** |
| P2/A | 1.17 | 1.20 | 1.00 |
| P2/B | 0.75 | 0.80 | 0.75 |
| **P2/C** | **0.00** | **0.00** | **0.00** |

**Finding: C's advantage over A and B does not collapse when leak-suspect items are dropped.** Even on the broad-clean subset (P1: 6 items; P2: 4 items — only items where the construct was *not* mentioned in any form in the interview), C's MAE is essentially zero. The interview transcript apparently encodes enough personality structure that the LLM can predict held-out responses on uncovered items by inference, not just regex.

**The 0.00 numbers are noisy** (broad-clean for P2 has only 4 items). The honest headline is the **strict-clean** column: drop the 3 STRONG-leaked items (bfi_c, polviews, happy/satjob) and C still wins by 0.6–1.2 MAE over A.

**Visualization:** `chart_robustness.png` — three-bar groups showing this comparison side-by-side.

**Open methodological question for the meeting**: is this leakage-filtered analysis sufficient defense, or do we still need 2-week-separated re-collection for the thesis-stage replication? My read: at higher N the strict-clean column is what we'd publish; broad-clean is a supplementary robustness check.

## Bottom-line ask for the meeting

Three concrete decisions to make:

1. **Confirm or reframe the thesis question** in light of Park's surveys-only ≈ interview-only finding.
2. **Choose granularity** for the feature-importance analysis (4 bins vs. finer taxonomy).
3. **Set a target N and timeline** for the actual thesis-stage replication.

---

*Supporting documents in `~/Documents/GSBGEN390/`:*
- `progress_report.md` — full sprint narrative with five pivots elaborated
- `STATUS.md` — current state for handoff to Claude Code CLI
- `replication_scoping.md` — design rationale
- `COLAB_RUN_GUIDE.md` — step-by-step Colab instructions
