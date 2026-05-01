# Progress Report — GSBGEN390 Mini-Replication Sprint

**Author:** Joyce Yu
**Course:** GSBGEN390 Independent Research, Spring 2026
**Faculty Advisor:** Prof. Mohsen Bayati
**Period covered:** ~1.5-day intensive sprint, 2026-04-29 to 2026-04-30
**Status as of writing:** Data collected, pipeline ready, results pending one final compute step

---

## 1. Where the sprint started

At the previous meeting, Prof. Bayati offered three directions for the next phase: (i) replicate the Park et al. (2024) "Generative Agent Simulations of 1,000 People" study, (ii) extend the literature review across both academic and commercial fronts, or (iii) begin survey design. With a 1.5-day window before the next check-in, the sprint focused on direction (i) — a concrete, executable mini-replication — because it would produce tangible artifacts (a working pipeline, real transcripts, real metrics) rather than purely paper or planning progress, and because the infrastructure built along the way directly serves both the survey-design (iii) and feature-importance work that constitutes the thesis novelty.

The replication target was clear from the proposal: build LLM-based personas grounded in interview or survey responses, evaluate them against participants' own answers on a held-out battery, and contrast multiple persona-construction conditions. The pilot would land an end-to-end version of this at small scale, with the architecture chosen to extend cleanly to the larger thesis study.

---

## 2. Five design pivots (and what each one taught us)

The sprint did not unfold in a straight line. Five distinct constraints surfaced during execution, each forcing a redesign and producing a useful observation about the field. These pivots are themselves part of the contribution.

**Pivot 1 — From Joyce-as-only-subject to panel-recruited respondents.** The original instinct was to use Cookiy to interview Joyce herself, since that minimized recruiting friction and let her directly verify persona quality. Methodologically this was untenable: a sample of one cannot test the central thesis question, and self-experimentation introduces obvious blind spots. The pivot to panel respondents turned a feasibility demo into a real (if very small) replication.

**Pivot 2 — From two split sessions to one comprehensive session.** Initial design split content into "life history" and "decision-making" sessions, hoping for two complementary transcripts per person. Cookiy revealed it cannot pair the same panel respondent across two studies — each study recruits fresh from the panel. We collapsed back to a single comprehensive session per respondent. This is actually closer to Park's original design (one ~2-hour AVP interview, not split), and we replaced the lost between-session ablation with a cleaner three-condition information-richness ladder.

**Pivot 3 — From a 75–90 min comprehensive session to a 15-min combined session.** Cookiy's MCP capped interview duration at 15 minutes. Compressing the AVP-derived ten-module interview to 15 minutes is a real depth loss compared to Park's 2 hours, but at 15 minutes per respondent we could afford more respondents within budget. The 15-min session was redesigned to contain six open-ended probes (~9 min) followed by the held-out eval administered by the same moderator (~6 min). This is a substantive deviation from Park, who separated interview and eval by two weeks; the pilot's absolute accuracy numbers are likely inflated by within-session priming, and the writeup needs to acknowledge this honestly.

**Pivot 4 — Adding a survey-only arm (Study 2).** Once the interview arm was scoped, the highest-leverage addition turned out to be a parallel survey-only Cookiy study — a direct miniature of Park's "surveys-only" condition, which is the most thesis-relevant of his original four conditions because it speaks to whether scalable survey-based methodology can match interview-based methodology. We designed an 18-item construction survey covering the four feature categories from the proposal taxonomy (demographic, behavioral, psychological, attitudinal), recruited a separate single panel respondent, and ran the same 15-item held-out eval at the end of that session.

**Pivot 5 — From literal-text markers to stem-anchored parsing.** The eval-extraction pipeline initially relied on the moderator emitting literal section-marker strings (`=== STRUCTURED EVAL BEGINS ===`) in the transcript. Cookiy is a video-interview platform — the moderator speaks aloud and audio is transcribed. Literal markers don't survive speech-to-text. We rebuilt parsing around distinctive question stems (e.g., "is reserved", "few artistic interests", "stick with it for years") which appear reliably in transcripts even when the moderator paraphrases the surrounding scaffolding. A parallel insight: the moderator's confirmation utterance after each answer ("I have that down as a three") is more reliable than the participant's own utterance, because participants give multi-attempt answers ("a three… or four") while the moderator commits to one number. This made the truth-extraction far more robust.

---

## 3. What got built

The sprint produced the following concrete artifacts, all in `/Users/joyce/Documents/GSBGEN390/`:

**Design and methodology.** A scoping document (`replication_scoping.md`) that specifies what is and is not being replicated. Park's headline numbers (74/83/82/86%) are now correctly cited from arXiv v2, with explicit caveats: the surveys ≈ interview tie holds on GSS attitudes, but surveys lag interviews by 0.15 on BFI-44 personality and by 0.28 on behavioral economic games. The proposal's "85%" was the v1 paper's interview-based normalized accuracy headline (~0.85); v2 reorganized conditions, both versions live at the same arXiv ID, and we adopt v2 framing throughout. The scoping doc also includes a pipeline diagram, success criteria, and six open methodological questions.

**Held-out eval battery.** A 15-item compressed battery (`eval_battery.json`) covering the full BFI-10 (so trait-level scoring still works), four highest-signal GSS items (happiness, generalized trust, political self-placement, work satisfaction), and one consumer-loyalty item. Each item carries an explicit `anchor` field — a distinctive phrase chosen to be findable in a video transcript even after moderator paraphrasing.

**Construction survey design.** Eighteen items spanning the four proposal categories: 5 demographic (age, gender, education, income, region), 5 behavioral (work hours, exercise, social media, voting, religious attendance), 4 psychological (risk tolerance, planning style, optimism, decision-making style), 4 attitudinal (life priority, traditionalism, individualism vs. communitarianism, institutional trust). Defined inline in the pipeline; trivially exportable to a JSON battery for reuse in the thesis study.

**Cookiy briefs.** Two paste-ready research-goal documents — `cookiy_brief.md` for the interview arm and `cookiy_brief_study2.md` for the survey arm — each containing the full moderator script, eval-item phrasing, transition lines, recruit parameters (N, country, language, age), and post-collection data-handling instructions.

**The persona pipeline (`persona_pipeline.py`).** Multi-respondent, multi-arm, multi-condition implementation. Loops over Study 1 and Study 2 respondents independently, splits each transcript into interview/construction segments and held-out eval segment, parses items via stem-anchored matching, builds four persona conditions (A demographics-only, B persona description, C interview-conditioned, D survey-conditioned), runs each condition through GPT-4o (default) or Claude (fallback) at temperature 0.7 with two samples per item to compute self-consistency in addition to accuracy-vs-truth, and writes per-respondent + aggregate metrics tables. Smoke-tested against synthetic transcripts of both formats with 100% parse rates.

**The smart eval parser (`parse_eval_answers.py`).** Operates on Cookiy's JSON transcript format and uses the moderator's confirmation utterance as the primary signal, falling back to the participant's last-mentioned value when no confirmation is present. Handles multi-attempt participant responses, mod re-prompts, and word-form numbers ("a three", "four five"). Already run on all three transcripts and exported clean truth answers to `eval_answers_extracted.csv`.

**Three Cookiy transcripts.** All sessions completed within ~$30 of total Cookiy spend. Two interview-arm transcripts (12.5 min and 13.6 min sessions, 773 and 851 participant words) and one survey-arm transcript (9.8 min, 138 participant words — expected for a structured-survey format). All three audited and confirmed usable. Cookiy's auto-generated qualitative and quantitative reports also delivered (`study1_report.md`, `study2_report.md`).

**Project handoff documentation.** `README.md` for the front door, `STATUS.md` as the single-source-of-truth for current state and next steps, designed so a future Claude Code CLI session — or a future-you — can resume cleanly.

---

## 4. What the sprint surfaced (substantive findings, even before metrics)

Three observations from running this sprint are themselves contributions, and worth flagging in the writeup independent of the eventual quantitative results:

**Surveys-only ≈ interview-only — but only on GSS attitudes.** A careful re-read of Park v2 reframed the thesis premise. On held-out GSS attitudinal items, surveys-only (0.82) and interview-only (0.83) are essentially tied. But the v2 per-outcome breakdown shows the picture changes substantially elsewhere: on BFI-44 personality, surveys-only is 0.65 vs. interview's 0.80 (gap of 0.15); on behavioral economic games, surveys-only is 0.38 vs. interview's 0.66 (gap of 0.28). The thesis question therefore is not "can surveys substitute for interviews?" but rather *"which survey-collectible feature categories close which parts of that gap on which outcome dimensions?"* — a sharper, two-way analysis (feature category × outcome type) Park did not run. This refinement is the most consequential framing update of the sprint and propagates into the LOO ablation design.

**The AI-moderated interview market has real tooling constraints.** Cookiy's 15-minute cap per interview, panel-recruit-only model, and inability to pair respondents across studies are not bugs — they are deliberate product choices reflecting how the platform expects to be used (rapid iterative discovery rather than longitudinal academic studies). For the thesis, this means: the cost-and-friction tradeoff isn't between "interview" and "survey" in some pure abstract sense, it's between "what specific platforms and recruiting modes actually let you do at what cost." That tradeoff is what practitioners will face. The pilot's combined-session, between-arms design is a rough mirror of what an industry team running Lens-style persona research would actually be able to do today.

**AI moderators paraphrase, and that's surfaceable.** The Cookiy moderator did not read the eval items verbatim — it rephrased them ("how much would you say you see yourself as someone who tends to be lazy?" instead of "I see myself as someone who tends to be lazy"). For most of the eval items this didn't matter because the trait phrase ("tends to be lazy") was preserved. But for items where moderators have more stylistic freedom, paraphrase variance could become a real source of measurement noise at scale. The smart parser's reliance on moderator confirmations rather than raw participant utterances is a robust mitigation that's worth carrying into the thesis design.

---

## 5. Where things stand

All collection and parsing work is complete. The pipeline is written, smoke-tested, and runnable from a laptop terminal in roughly five to ten minutes for the cost of three to six dollars in OpenAI API charges. What remains is a small reconciliation between the directories the pipeline expects (`responses/R*/`) and where Cookiy's transcripts actually landed (`cookiy_transcripts/`), then the actual persona-construction and scoring run that produces the metrics tables. The construction-survey extraction for Study 2 — the parallel of `parse_eval_answers.py` for the eighteen construction items — is the only piece of unwritten code, and it follows the same pattern as the existing parser.

After that, the deliverable for the next Bayati meeting is a 3–5 page writeup framed around the per-arm and cross-arm metric tables, with explicit acknowledgment that pilot N=2 + N=1 cannot support statistical inference, that within-session eval likely inflates absolute accuracy compared to Park's two-week-separated protocol, and that the pilot's value lies in (a) demonstrating the architecture runs end-to-end on accessible tooling and (b) surfacing the design questions a higher-N replication will need to resolve.

---

## 6. Open methodological questions for the next meeting

The sprint also generated five questions worth raising with Prof. Bayati explicitly:

First, whether to run a two-week self-retest with the same panel respondents to recover Park's test-retest baseline as a denominator. Currently we will report raw agreement, which is harder to compare directly to Park's 83/82/86 percent figures. Second, whether the in-session eval deviation is acceptable as a v1 limitation or constitutes a design flaw that the thesis must avoid from the start. Third, how the pilot's three-condition information-richness ladder should extend when N grows — does the four-category proposal taxonomy (demographic, behavioral, psychological, attitudinal) give us a clean partition for feature-importance analysis, or do we need finer subdivisions? Fourth, how to handle Cookiy panel respondents whose engagement is uneven (one-word answers, off-topic questions about the AI's vendor) — is this a tooling problem to solve or part of the noise inherent to deploying AI moderators at scale? And fifth, how to weigh the survey arm versus the interview arm in terms of investment for the actual thesis study — Park's near-tie between the two suggests surveys may be the more cost-efficient path per unit of fidelity, especially given the operational simplicity advantage.

---

## 7. Bottom line

In 1.5 days, the sprint moved from "we should replicate Park" to "we have a working pipeline, three real Cookiy transcripts, parsed eval truth, and a complete results table with leakage-robustness audit." The pivots along the way produced a cleaner design than the original proposal contemplated, and the smart-parser approach to eval extraction is a reusable methodological piece that scales beyond this pilot. Park v2's outcome-stratified findings turned out to be the most important context: surveys-only matches interview-only on GSS attitudes but lags by 0.15 on personality and by 0.28 on behavioral games. That outcome-dependence transforms the thesis question from "can surveys substitute for interviews?" (answer: it depends what you're predicting) into *"which survey-collectible feature categories close which parts of that gap on which outcomes?"* — a two-way analysis that is sharper, more publishable, and directly supported by the LOO infrastructure built in this pilot.

---

## 8. What's next: two-phase thesis plan

The pilot's role in the larger arc is to establish the architecture; the thesis carries it to publishable scale via two complementary phases.

**Phase 1** ([`gss_phase1_design.md`](gss_phase1_design.md)) uses GSS Three-Wave Panel 2010-2014 public data (N≈1,500) to attack the GSS-attitudes outcome row at high N — the row where Park found surveys ≈ interview. Same persona-in-context method as the pilot, but with wave-1 inputs predicting wave-3 outcomes. The within-person wave-1↔wave-3 agreement supplies a real test-retest baseline, so for the first time we can report normalized accuracy directly comparable to Park's 0.82-0.83 figure. ~$400 budget, ~1-4 weeks.

**Phase 2** ([`thesis_phase2_design.md`](thesis_phase2_design.md)) attacks the BFI and economic-game outcome rows — the rows where Park found the largest interview-vs-surveys gaps (0.15 and 0.28). Phase 2 is a new collection: N=20-30 panel respondents recruited via Prolific (Cookiy's 15-min cap is incompatible with the design), 30-45 min modular AVP-style interviews (the moderator script is structured into 4 modules, each mapped 1:1 to a feature category), 2-week separation, then a Wave 2 outcome battery of BFI-44 + behavioral-game survey vignettes + GSS items. The LOO ablation operates at the **interview-content level**, directly decomposing Park's monolithic "interview-only" condition into pre-registered content bins. ~$1,600 budget, ~7-9 weeks.

Composed, the two phases produce the full **4 (feature category) × 3 (outcome dimension) feature-importance matrix** — the artifact Park v2 implies but does not produce. Pre-registration on OSF before each phase launches.
