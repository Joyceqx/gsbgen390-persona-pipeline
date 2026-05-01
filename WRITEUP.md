# Mini-Replication of Park et al. (2024) — Pilot Write-Up

**Author:** Joyce Yu
**Course:** GSBGEN390 Independent Research, Spring 2026
**Faculty Advisor:** Prof. Mohsen Bayati
**Sprint window:** 2026-04-29 → 2026-04-30 (≈ 1.5 days)
**Document date:** 2026-04-30
**Document purpose:** Pre-meeting write-up of the pilot — what I built, how I built it, what I found, and what to decide next.

---

## 1. Motivation and research question

Park, Bernstein, Liang and collaborators (arXiv:2411.10109, *Generative Agent Simulations of 1,000 People*, 2024) showed that an LLM conditioned on a verbatim ~2-hour interview transcript can answer held-out social-science questions with surprising fidelity to the participant's own answers. The headline numbers — re-checked against the paper itself, since the proposal v2 quoted "85%" — are:

| Construction condition | GSS accuracy (% of test-retest reliability) |
|---|---|
| Demographics only | 74% |
| Interview only | **83%** |
| Surveys only | **82%** |
| Interview + surveys combined | 86% |

The result that reframes the thesis is the one-percentage-point gap between **interview-only (83%)** and **surveys-only (82%)**. If structured surveys can already reach interview-quality persona fidelity in aggregate, the more publishable question is no longer "can surveys substitute for interviews?" — Park already answered that — but **"which survey-collectible features account for the substitution?"** That feature-importance question is the thesis novelty; it is also the question Park did *not* answer.

This pilot is the smallest end-to-end version of Park's pipeline I can run before the survey-design phase, plus a first attempt at a feature-importance ablation Park did not perform. Its goals are concrete:

1. Prove the pipeline runs end-to-end on accessible tooling (Cookiy + GPT-4o + a laptop).
2. Surface the methodological and engineering choices the larger thesis study will inherit.
3. Produce honest, illustrative numbers that show the architecture *can* recover signal at small N — without claiming statistical generalization.

---

## 2. What I am replicating, and what I am explicitly not

Replicated faithfully:
- **Persona-in-context architecture** — verbatim transcript injected into the system prompt; persona answers held-out items "in character."
- **Held-out evaluation logic** — ground truth is collected before the persona pipeline ever sees the eval items.
- **Information-richness ladder of conditions** — demographics-only, persona-description, interview/survey-conditioned, mapping cleanly to Park's main framework.
- **Self-consistency dimension** — every item is asked twice at temperature 0.7, so we can separate accuracy (vs. truth) from stability (sample 1 vs. sample 2).
- **Default model** — GPT-4o, with Claude Sonnet 4.6 swappable via env var for a robustness check.

Not replicated, and labelled openly:

| Park et al. | This pilot |
|---|---|
| n = 1,052 stratified U.S. adults | n = 2 (Study 1) + 1 (Study 2) panel respondents |
| 2-hour AI-administered AVP interview (Park's custom voice-to-voice agent with adaptive follow-ups; ~6,491 words/transcript) | ~9-min Cookiy AVP-style interview (general-purpose product, fixed probes, no depth probing) |
| BFI-44 + full GSS + 5 econ games + 5 experiments | BFI-10 + 4 GSS items + 1 consumer item (15 total) |
| Self test-retest baseline at 2 weeks | Single-shot — no retest baseline |
| 2-week gap between interview and eval | **In-session eval** (forced by Cookiy's panel inability to recontact) |
| Surveys-only and interview+surveys conditions | Study 2 (survey arm) included; combined arm not |

The pilot is a **proof-of-concept replication, not a generalization claim.**

---

## 3. Five design pivots (and what each one taught me)

The sprint did not run in a straight line. Five constraints surfaced, each forced a redesign, and each is itself part of the contribution.

**Pivot 1 — From Joyce-as-only-subject to a panel.** The first instinct was to interview myself, since that minimized recruiting friction. Methodologically untenable: a sample of one cannot test the central question, and self-experimentation has obvious blind spots. Pivoting to panel respondents turned a feasibility demo into a real (if small) replication.

**Pivot 2 — From two split sessions to one comprehensive session.** I had originally split content into "life history" and "decision-making" sessions, hoping for two complementary transcripts per respondent. Cookiy revealed it cannot pair the same panel respondent across two studies — each study recruits fresh from the panel. Collapsing back to a single session is actually closer to Park's design (one ~2-hour AVP interview, not split), and the lost between-session ablation was replaced with a cleaner three-condition information-richness ladder.

**Pivot 3 — From 75–90 min comprehensive to a 15-min combined session.** Cookiy's per-interview cap is 15 minutes. Compressing a ten-module AVP-derived guide to that window is a real depth loss compared to Park's 2 hours, but it lets us afford more respondents within budget. The 15-min session was redesigned to contain ~9 min of open-ended probes followed by ~6 min of held-out eval administered by the same moderator. **This deviates substantively from Park, who separated interview and eval by two weeks.** Within-session priming likely inflates absolute accuracy in our pilot — addressed in §7's leakage audit.

**Pivot 4 — Adding a survey-only arm (Study 2).** Once the interview arm was scoped, the highest-leverage addition was a parallel survey-only Cookiy study, mirroring Park's surveys-only condition. I designed an 18-item construction battery covering the four feature categories from the proposal taxonomy (demographic, behavioral, psychological, attitudinal), recruited a separate single respondent, and ran the same 15-item held-out eval at the end. Study 2 also enables a **leave-one-category-out (LOO) ablation** that Park did not perform — a first miniature of the thesis feature-importance analysis.

**Pivot 5 — From literal-text markers to stem-anchored parsing.** The eval-extraction code initially relied on the moderator emitting literal section-marker strings like `=== STRUCTURED EVAL BEGINS ===`. Cookiy is a video-interview platform — the moderator speaks aloud and audio is transcribed. Literal markers don't survive speech-to-text. I rebuilt parsing around distinctive question stems ("is reserved", "few artistic interests", "stick with it for years") which appear reliably in transcripts even after moderator paraphrasing. A complementary insight: the **moderator's confirmation utterance** ("I have that down as a three") is a more reliable gold signal than the participant's own utterance, because participants give multi-attempt answers ("a three… or four") while the moderator commits to one number. This made truth extraction far more robust and is reusable for the thesis-stage pipeline.

---

## 4. How the interviews and surveys were collected

### 4.1 Platform and recruitment

Both studies were run through **Cookiy**, an AI-moderated research platform (panel-recruited respondents, voice or chat moderator, structured + open probes, automatic transcript with timestamps). Recruitment parameters: U.S. adults, English, age 18+. Costs: total Cookiy spend across all three sessions stayed under ~$30. No respondent was paired across studies (Cookiy structurally cannot do this).

### 4.2 Study 1 — Interview arm (N = 2)

**Format.** 15-minute combined session per respondent, structured as:
- ~9 minutes of open-ended AVP-style probes — life story, family, work, daily life, money, attitudes — compressed from a ten-module guide.
- ~6 minutes of structured held-out eval (15 items: BFI-10 + 4 GSS items + 1 consumer-loyalty item), administered by the same Cookiy moderator immediately after the interview probes.

**Output.** Two interview transcripts (12.5 min / 13.6 min sessions; 773 / 851 participant words). Both audited as usable.

**Study 1 design rationale.** This arm tests Park's **interview condition** (Condition C) against demographics-only (A) and a self-description baseline (B). The information-richness ladder A → B → C maps directly to Park's main framework.

### 4.3 Study 2 — Survey arm (N = 1)

**Format.** 15-minute structured session: an **18-item construction battery** covering the four proposal categories, followed by the **same 15-item held-out eval**.

**Construction battery composition (18 items, defined inline in the pipeline):**
- 5 **demographic** — age, gender, education, income range, region.
- 5 **behavioral** — work hours, exercise frequency, social media, voting, religious attendance.
- 4 **psychological** — risk tolerance, planning style, optimism, decision-making style.
- 4 **attitudinal** — life priority, traditionalism, individualism vs. communitarianism, institutional trust.

**Output.** One transcript (9.8 min, 138 participant words — expected for structured-survey format). Audited usable.

**Study 2 design rationale.** This arm tests Park's **surveys-only condition** (Condition D) against demographics-only (A) **and** runs a **leave-one-category-out (LOO) ablation** — four additional conditions that drop each of {demographic, behavioral, psychological, attitudinal} in turn, so we can see which feature category, when removed, hurts accuracy most. This LOO ablation is a first sketch of the feature-importance analysis the thesis is built around. **Park's "surveys" was a single bucket; the four-bin partition is a real extension.**

### 4.4 Eval battery (held out across both studies)

The same 15 items are scored against the persona's answers in every condition:

- **BFI-10** (10 items, 1–5 Likert) — Big Five at trait level (2 items per trait).
- **GSS subset** (4 items) — happiness, generalized trust, political self-placement (1–7), work satisfaction.
- **Consumer-loyalty item** (1 item, 1–5 Likert) — "When I find a brand I like, I tend to stick with it for years."

Each item has an explicit `anchor` phrase chosen to be findable in a video-transcribed interview even after moderator paraphrasing. The full battery, with anchors, lives in `eval_battery.json`.

---

## 5. Pipeline architecture

### 5.1 Flow

```
Cookiy session ──► transcript (.txt + .json) ──► two parsers:
                                                  • parse_eval_answers.py        → eval_answers_extracted.csv  (truth)
                                                  • parse_construction_answers.py → construction_answers_extracted.csv  (Study 2 only)

For each respondent × each condition (A, B, C/D, + LOO for Study 2):
    persona system prompt = role frame + condition-specific materials
    For each of 15 eval items:
        ask the LLM twice at temperature 0.7  →  primary answer + sample
    Score:
        Likert MAE                  vs. truth
        Likert within ±1            vs. truth
        Categorical exact-match     vs. truth
        BFI-trait RMSE              vs. truth
        Self-consistency (sample 1 vs. sample 2): Likert self-MAE, categorical self-match
    Write per-respondent + aggregate CSV
```

### 5.2 The four (six for Study 2) conditions

| ID | Materials given to the persona | Purpose |
|---|---|---|
| **A** demographics-only | A few basic facts (age range, role, region, education) | Baseline — what does the LLM "know" with almost nothing? |
| **B** persona description | A 1–3 paragraph self-description (independently composed, not from the interview) | Tests whether a *summary* matches a *transcript* |
| **C** interview-conditioned | The verbatim Cookiy interview transcript | Park's interview condition |
| **D** survey-conditioned | All 18 construction items + their answers | Park's surveys-only condition |
| **D − {category}** (×4) | All construction items *except* one category | Leave-one-category-out ablation (feature importance) |

### 5.3 Smart parser

`parse_eval_answers.py` (and its sibling `parse_construction_answers.py`) operate on Cookiy's JSON transcript format. Two design choices make them robust:

- **Stem-anchored matching.** Every eval item carries a distinctive anchor phrase ("is reserved", "few artistic interests", "stick with it for years"). The parser locates the moderator turn that contains the anchor, then walks forward to find the participant's answer — robust to paraphrase of the surrounding scaffolding.
- **Moderator confirmation as gold signal.** When the moderator says "I have that down as a three," that becomes the ground-truth value rather than the participant's last-mentioned number. Participants give multi-attempt answers ("a three… or four"); moderators commit. This roughly halved truth-extraction error in piloting.

Result: **100% parse rate** — 15/15 eval × 3 respondents and 18/18 construction × 1 respondent.

### 5.4 Runner

The canonical pipeline lives in `persona_pipeline.ipynb` (31 cells, end-to-end). To execute it from a laptop terminal without Colab, `run_notebook_local.py` patches the file-upload cell to read from disk, stubs Jupyter built-ins (`display`, magics), and **adds exponential-backoff retry around `_call_openai`** — important, because the OpenAI account's TPM limit (30K tokens/min for GPT-4o) trips ~3–5 times per full run and would otherwise fail mid-run. End of run, it persists every primary + sample answer to `persona_answers_full.json`, which lets all downstream re-scoring (e.g., the leakage audit) avoid re-paying for API calls.

A full run: **12 conditions × 15 items × 2 samples ≈ 360 calls; ~9 minutes wall-clock; ~$4 in API.**

---

## 6. Results

### 6.1 Headline table — Likert MAE per condition (lower = closer to truth)

Source: `metrics_with_leakage_audit.csv` (`full_eval` filter; this is the canonical post-fix output — it reads from the same `persona_answers_full.json` as `metrics_per_respondent.csv` but uses the audited `eval_answers_extracted.csv` as the single gold source).

| Arm | Resp. | A demo | B desc | C / D | LOO best | LOO worst |
|---|---|---|---|---|---|---|
| Study 1 | P1 | 0.83 | 0.92 | **C: 0.08** | — | — |
| Study 1 | P2 | 1.17 | 0.75 | **C: 0.00** | — | — |
| Study 2 | S2-P1 | 0.50 | — | D: 0.83 | drop attitudinal: 0.58 | drop demographic: 1.17 |

Self-consistency, BFI-trait RMSE, categorical exact-match accuracy, and within ±1 are reported in `metrics_per_respondent.csv` and `metrics_with_leakage_audit.csv`.

### 6.2 What the numbers say

**Study 1 (interview arm) — interview conditioning is a large effect.** C beats A by 0.75 MAE on P1 and 1.17 MAE on P2. Self-consistency for C is essentially perfect on both respondents (Likert self-MAE 0.00–0.08; sample 1 ≈ sample 2). This direction matches Park's own ladder (74% → 83%) and is qualitatively much larger here — almost certainly because of in-session priming (see §7). **The direction is the load-bearing finding; the absolute magnitude is not.**

**Study 2 (survey arm) — A > D unexpectedly.** Adding the 18 construction items on top of demographics did *not* improve accuracy for this respondent (A: 0.50, D: 0.83). With N=1 this could be noise (≈ 2 items more wrong out of 12), or it could be a real signal that survey-collectible context isn't always additive past demographics. The LOO ablation on D shows:

| LOO condition (drop one category) | MAE |
|---|---|
| drop **demographic** | 1.17 |
| drop **psychological** | 0.92 |
| drop **behavioral** | 0.83 |
| drop **attitudinal** | 0.58 |

Dropping demographics hurts most; dropping attitudinal items actually *helps* this respondent (0.83 → 0.58). At N=1 this LOO ranking is **run-unstable across temperature-0.7 reruns** — different categories rank "most important" across runs — so the order is directional only and awaits N ≥ 30 to stabilize.

**Caveat on all of the above.** N = 2 + N = 1 cannot statistically separate any of these effects. The pilot demonstrates the architecture works; the numbers are illustrative.

### 6.3 What does *not* show up in this table

- **Park's denominator.** Park reports "% of test-retest reliability." We do not have a self test-retest. So our numbers are raw agreement with truth, not normalized agreement — direct numerical comparison to 83 / 82 / 86% is not warranted. (Open question 3 in §9.)
- **BFI-44 trait RMSE.** At BFI-10 (2 items per trait), trait-level RMSE is statistically meaningless. We report it for completeness but do not interpret it.

---

## 7. Leakage audit (defense against in-session priming)

### 7.1 The objection

Because Cookiy can't pair respondents across studies, our held-out eval is administered in the **same session** as the interview / construction items. Park's protocol uses a 2-week gap. This means **some eval items have their answer effectively pre-stated in the interview** (e.g., P1 disclosed their political ideology during the open-interview portion, then minutes later was asked to self-place on the 1–7 liberal–conservative eval scale). Plausible objection: is Condition C's win driven by an actual prediction, or by the LLM regex-matching pre-stated answers?

### 7.2 What I did

Manually audited **each of the 15 eval items × each respondent** against their interview/construction transcript. Each item was tagged:
- **STRONG** — construct directly stated by participant or paraphrased by moderator (e.g., "you are prepared for the long, steady effort it takes to reach your goal" → STRONG for `bfi_c` conscientiousness).
- **SOFT** — construct semantically related to discussed content but not directly stated (e.g., "discussed daily juggling of caregiving + school" → SOFT for `bfi_c_r`).
- **CLEAN** — no detectable mention.

Tags + evidence quotes are in `leakage_audit.json`. By count:

| Respondent | STRONG | SOFT | CLEAN |
|---|---|---|---|
| P1 (interview) | 3 (`bfi_c`, `polviews`, `happy`) | 5 | 7 |
| P2 (interview) | 3 (`bfi_c`, `polviews`, `satjob`) | 8 | 4 |
| S2-P1 (survey) | 0 | 5 | 10 |

The survey arm has structurally less leakage: construction items don't directly answer eval items; they only semantically prime via overlap (e.g., the construction item on individualism vs. communitarianism softly relates to GSS political views).

### 7.3 Re-score under three filters

`rescore_with_leakage_audit.py` re-computes Likert MAE under:
- **`full_eval`** — all 15 items.
- **`strict_clean`** — drop only STRONG-tagged items.
- **`broad_clean`** — drop both STRONG and SOFT.

| | full (15) | strict-clean | broad-clean |
|---|---|---|---|
| P1 / A | 0.83 | 0.70 | 1.00 |
| P1 / B | 0.92 | 0.80 | 1.00 |
| **P1 / C** | **0.08** | **0.10** | **0.00** |
| P2 / A | 1.17 | 1.20 | 1.00 |
| P2 / B | 0.75 | 0.80 | 0.75 |
| **P2 / C** | **0.00** | **0.00** | **0.00** |

(Visualization: `chart_robustness.png`, three-bar groups per condition.)

### 7.4 What this means

**C's advantage over A and B does not collapse when leak-suspect items are dropped.** Even on the broad-clean subset (P1: 6 items; P2: 4 items — only items where the construct was *not* mentioned in any form), C's MAE is essentially zero. The interview transcript apparently encodes enough personality structure that the LLM can predict held-out responses on uncovered items by inference, not just by retrieving pre-stated answers.

**Important caveat.** The 0.00 numbers in broad-clean are noisy — P2 broad-clean has only 4 items left. The honest headline is the **strict-clean column** (10 items kept): drop the 3 STRONG-leaked items per respondent and **C still wins by 0.6–1.2 MAE over A** on both respondents. That is the number to report.

The audit doesn't make in-session eval *good practice* — it just shows the C-condition win is not a regex artifact of the deviation. For the thesis-stage replication, 2-week-separated re-collection is still preferable. (Open question 1 in §9.)

---

## 8. Limitations

In approximate order of severity:

1. **N = 2 + 1.** No statistical inference is supportable from the pilot. Numbers are illustrative.
2. **In-session eval rather than 2-week-separated.** Likely inflates absolute accuracy via priming; mitigated but not fully removed by the §7 audit.
3. **No test-retest baseline.** We do not have Park's denominator, so absolute numbers cannot be quoted as direct comparators to Park's 83 / 82 / 86%.
4. **15-min session vs. Park's 2 hours.** Real depth loss; Cookiy moderators have no adaptive depth-probing behavior, so emotional / relational / autobiographical depth is thin compared to the AVP protocol.
5. **BFI-10 not BFI-44.** At 2 items per trait, BFI-trait RMSE is not interpretable; the headline metric is per-item Likert MAE.
6. **Cookiy moderator paraphrase.** Eval items are not always read verbatim — the moderator reuses the trait phrase but rephrases the surrounding stem. For most items this is fine; for items with more stylistic variance, it would become real measurement noise at scale. The smart parser's reliance on moderator confirmations is a partial mitigation.
7. **LOO at N=1 is run-unstable.** The "most-important-when-dropped" category changes across temperature-0.7 reruns. Direction-only at this N.
8. **No multi-seed run-variance estimate yet.** I have not yet bounded LLM-output variance by re-running the pipeline 5–10 times from different seeds. Pending (§10).
9. **No combined arm.** Park's interview + surveys condition is not in the pilot; would need a Cookiy product feature that does not exist (cross-study respondent pairing).

---

## 9. Open methodological questions for the meeting

Five questions where Prof. Bayati's input meaningfully shifts the thesis-stage design.

1. **Is the leakage-filtered analysis (manual STRONG-tagging + strict-clean MAE) a sufficient defense of the C-condition result?** Or does the thesis-stage replication need 2-week-separated re-collection regardless? My read: at higher N the strict-clean column is what we'd publish; broad-clean is a supplementary robustness check. But for the thesis we likely want a real time-separated protocol — which means picking a different recruitment platform (Prolific custom script, in-house panel) since Cookiy can't recontact.

2. **LOO category granularity.** Four categories (demographic / behavioral / psychological / attitudinal) is the proposal taxonomy. Park's "surveys" was one bucket; a 4-bin partition is already a real extension. Do we keep this taxonomy for the thesis, or subdivide further (e.g., split "behavioral" into health behaviors / consumption behaviors / civic behaviors)?

3. **Test-retest baseline.** Park reports % of test-retest reliability. We don't have that. Worth running a 2-week self-retest with the 3 pilot respondents to recover the denominator and quote a single number against Park's, or accept the gap and never quote that comparison?

4. **BFI-10 → BFI-44** for the thesis-stage study: yes/no? The trait-level analysis only becomes interpretable with the full 44.

5. **Cookiy as the data-collection platform for the thesis.** Keep, or switch (Prolific + custom script for verbatim eval-item delivery and 2-week recontact)? This is the largest single design choice and gates the answer to questions 1 and 3.

---

## 10. What's pending (post-meeting)

1. **Multi-seed run-variance estimate.** Re-run the pipeline 5–10 times with different seeds; bound LOO ranking instability at N=1. Honest answer to "how reliable is this LOO?"
2. **3–5 page formal writeup** for course submission — methods, pipeline, results, leakage audit, comparison to Park's 83/82/86%, limitations, next steps. (This document is the long-form draft input.)
3. **2-week-separated re-collection.** Decision pending Q5 above. If yes, requires switching off Cookiy.
4. **BFI-44 upgrade.** Decision pending Q4 above.
5. **Larger N.** Pilot N=2+1 → thesis target probably **N ≥ 30 per arm** based on what's needed for stable LOO ranking + ablation effect estimation.
6. **Survey-instrument design for the thesis.** The pilot's 5/5/4/4 split is illustrative only. The real instrument probably needs 8–15 items per category × 4 categories ≈ 60+ construction items.

---

## 11. Bottom-line ask for the meeting

Three concrete decisions, each of which gates a downstream step:

1. **Confirm or reframe the thesis question** in light of Park's surveys-only ≈ interview-only finding. (My current framing: "which survey-collectible features account for most of the substitution?")
2. **Choose the granularity** for the feature-importance analysis (4 bins vs. finer).
3. **Pick the data-collection platform and protocol** for the thesis-stage replication (Cookiy in-session vs. Prolific 2-week).

---

## Appendix A — File inventory

**Design and methodology**
- `replication_scoping.md` — full design rationale, pipeline diagram
- `eval_battery.json` — 15-item eval with anchors
- `cookiy_brief.md`, `cookiy_brief_study2.md` — moderator scripts and recruit parameters

**Data (Cookiy outputs)**
- `cookiy_transcripts/study1_interview_p{1,2}.{txt,json}` — Study 1 transcripts
- `cookiy_transcripts/study2_survey_p1.{txt,json}` — Study 2 transcript
- `cookiy_transcripts/study{1,2}_report.{md,json}` — Cookiy auto-generated reports

**Parsers and pipeline**
- `parse_eval_answers.py` → `eval_answers_extracted.csv` (truth)
- `parse_construction_answers.py` → `construction_answers_extracted.csv`
- `persona_pipeline.ipynb` — canonical end-to-end notebook (31 cells)
- `run_notebook_local.py` — local runner with retry/backoff

**Run artifacts**
- `persona_answers_full.json` — every primary + sample answer (raw LLM output)
- `metrics_per_respondent.csv` — per-respondent × per-condition metrics
- `metrics_with_leakage_audit.csv` — same, three filter views (full / strict-clean / broad-clean)
- `leakage_audit.json` — per-respondent item tags + evidence quotes
- `chart_robustness.png` — leakage-robustness visualization
- `run_*.log` — timestamped run logs

**Quality audits**
- `interview_quality_audit.md`
- `survey_quality_audit.md`

**Handoff**
- `STATUS.md` — single-source-of-truth for current state and resumption
- `MEETING_HANDOUT.md` — one-page meeting brief
- `progress_report.md` — full sprint narrative
- `EXPLAIN_ZH.md`, `CODE_WALKTHROUGH_ZH.md` — Chinese-language explanations

---

## Appendix B — Reproduction recipe

```bash
cd ~/Documents/GSBGEN390
export OPENAI_API_KEY=$(cat Openai_api.txt)

# Full pipeline run (~9 min, ~$4):
python3 -u run_notebook_local.py 2>&1 | tee run_$(date +%Y%m%d_%H%M).log

# Re-score only (no API calls, ~1 second; needs persona_answers_full.json):
python3 rescore_with_leakage_audit.py
python3 make_robustness_chart.py
```

Runtime gotchas: TPM rate limit triggers retry/backoff (~30–60s overhead per run); Cell 8's `google.colab.files.upload()` is patched to read from disk; `display()` is stubbed; `LLM_CACHE` is in-memory only — `persona_answers_full.json` is the cross-process persistence layer.

---

*End of write-up. For meeting reference: 1-page brief in `MEETING_HANDOUT.md`; current state and handoff in `STATUS.md`; full sprint narrative in `progress_report.md`.*
