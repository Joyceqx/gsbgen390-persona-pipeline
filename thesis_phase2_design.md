# Phase 2 — Interview-Decomposed Feature-Importance Study

**Author:** Joyce Yu
**Course:** GSBGEN390 / thesis prep · Prof. Mohsen Bayati
**Status:** Proposed (drafted 2026-04-30, awaiting Bayati sign-off)
**Sequel to:** [`gss_phase1_design.md`](gss_phase1_design.md) (GSS public-data Phase 1)

---

## 1. Research question

**Within an LLM persona built from a long interview transcript, which content categories of that interview most predict held-out responses on which outcome dimensions?**

This is the *non-attitudinal* half of the thesis matrix — the rows where Park v2 finds **interview > surveys** by 0.15 (BFI-44 personality) and 0.28 (behavioral economic games). Phase 1 covers the GSS-attitudes row using public data; Phase 2 covers the BFI and games rows using **new collection**, because that gap exists *inside the interview content* and cannot be observed from any survey-only public dataset.

**The thesis-relevant operationalization**: Park's 0.15 and 0.28 gaps are reported as *aggregate* differences between "interview" and "surveys" persona conditions. Phase 2 asks which **interview-content category** (demographic / behavioral / psychological / attitudinal disclosures) carries the predictive signal that closes those gaps — i.e., decomposes Park's monolithic "interview" condition into pre-registered content bins.

## 2. Why this design beats the alternatives

| Alternative | Why it doesn't answer the question |
|---|---|
| GSS public data only (Phase 1) | GSS contains no interviews, no BFI, no games. Cannot observe the BFI/games gap or its content-level decomposition. |
| Paired structured survey at higher N | Tests "which *survey-collectible* features close the gap" — but Park's gap is *defined* as interview-vs-surveys. Surveys-only ablation cannot explain why interviews win. |
| Scaling pilot's 9-min Cookiy interview | 9 minutes is too thin to support meaningful within-transcript ablation; depth-domain coverage already audited as inadequate at that length. |

**This design is the unique research move that directly decomposes Park's "interview-only" condition.** The thesis novelty is not "we ran longer interviews" — it is **modular interview design + content-level LOO ablation against multi-outcome held-out battery**.

## 3. Recruitment & platform

**N = 20–30 panel respondents** recruited via **Prolific** (not Cookiy).

Why Prolific:
- Cookiy caps interviews at 15 minutes — incompatible with 30-45 min modular AVP-style interview
- Cookiy panel cannot be re-contacted across studies → no Wave-1 / Wave-2 separation
- Prolific supports custom-script studies with same-respondent re-invitation across separated waves
- Prolific has a stable, vetted, ID-traceable participant pool

**Moderator**: self-hosted AI agent built on OpenAI Realtime API (or equivalent). The pilot's Cookiy moderator script is the seed — port to a stand-alone AI agent that the team controls. This avoids Cookiy's 15-min cap and gives full control over module-level scripting.

**Methodological contribution from this choice**: the design produces a documented, replicable "how to deploy a Park-comparable AI-moderated long interview at academic budget" recipe — itself a practitioner-relevant artifact and a Lens-relevant deployment pattern.

## 4. Interview design — modular by feature category

The 30-45 min interview is structured as four **content modules**, each mapped to a feature category. The modular structure is what enables clean transcript decomposition for the LOO ablation.

| Module | Duration | Feature category | Content |
|---|---|---|---|
| **M1 — Life basics** | 5 min | Demographic | Age, family structure, work/role, education, region, income bracket — all stated facts |
| **M2 — Daily behaviors** | 10 min | Behavioral | Weekly routine, consumption, exercise, social patterns, media diet, religious practice, voting behavior |
| **M3 — Inner self / psychological** | 10 min | Psychological | Childhood, key relationships, stressors, motivations, regrets, recent peak/valley emotional moments |
| **M4 — Values / attitudes** | 10 min | Attitudinal | Political views, social/policy positions, life philosophy, institutional trust, traditionalism |

**Moderator script discipline**: hard module boundaries with verbal markers ("OK, let's move to the next part — I want to ask about your daily routines"). Cross-module excursions are common when respondents free-associate (e.g., M3 stress story spilling into M2 exercise habit) and are handled in post-processing (§5).

## 5. Transcript decomposition method

Two-stage process for each transcript:

**Stage A — Module-boundary segmentation.**
Cut transcript at moderator's verbal module markers. First-pass clean: ~95% of content lands in the correct module bin.

**Stage B — Cross-content reassignment (LLM-assisted).**
Pass each utterance through a classifier prompt that asks GPT-4o: "*This utterance was given during Module {M_n}. Does the content primarily reveal {demographic / behavioral / psychological / attitudinal} information about the speaker, or does it primarily fit a different category?*" Reassign cross-content utterances; flag ambiguous segments for human review.

**Quality control**: 10% sample human-coded; agreement rate between LLM coder and human coder reported. With N=30 and ~30-min transcripts (~4000 words each), full human coding takes ~10 minutes per transcript and is feasible if needed.

**Outputs**: 4 cleaned content tracks per respondent (one per module), each ~700-1200 words, plus a "shared/cross" residual track that goes into all LOO conditions.

## 6. Wave 2 — Outcome battery

Administered ~2 weeks after Wave 1 (Park's separation), 25 minutes total.

| Block | Items | Time | Maps to Park outcome row |
|---|---|---|---|
| **BFI-44** | 44 items, 1-5 Likert | 10 min | BFI-44 personality |
| **Behavioral game survey-vignettes** | 5 items: dictator, ultimatum, trust, public goods, donation | 5 min | Behavioral economic games |
| **GSS attitudinal subset** | 15 items | 7 min | GSS attitudes (cross-validates Phase 1) |
| **Manipulation/attention checks** | 3 items | 3 min | Quality control |

**Total held-out items per respondent: ~64.**

## 7. LOO ablation method (the analysis)

Five persona conditions per respondent:

| Condition | Persona prompt content |
|---|---|
| **Full** | M1 + M2 + M3 + M4 + shared/cross |
| **LOO_M1** | (Full minus M1 content) |
| **LOO_M2** | (Full minus M2 content) |
| **LOO_M3** | (Full minus M3 content) |
| **LOO_M4** | (Full minus M4 content) |

For each condition × respondent × outcome item, LLM persona predicts the response (GPT-4o, temp 0.7, N=2 samples for self-consistency) — same pipeline as the pilot.

**Headline output**: the `feature_category × outcome_dimension` matrix:

|  | BFI MAE Δ | Games MAE Δ | GSS MAE Δ |
|---|---|---|---|
| Drop M1 (demographic) | ?? | ?? | ?? |
| Drop M2 (behavioral) | ?? | ?? | ?? |
| Drop M3 (psychological) | ?? | ?? | ?? |
| Drop M4 (attitudinal) | ?? | ?? | ?? |

Each cell is the average increase in MAE when that content is removed. Bootstrap 95% CIs across respondents. Effect-size (Δ) ranking is the headline finding.

**This 4×3 matrix is the artifact.** No prior published work has it.

## 8. Sample size, budget, timeline

**Sample size justification (N = 20-30):**
- Park's gaps are large effects (0.15 and 0.28 on outcomes scaled 0-1). Detecting LOO effects of similar magnitude does not require Park's N=1052.
- BFI is item-rich: 30 respondents × 44 items = 1320 paired observations per condition.
- Phase 2 is **confirmatory after Phase 1** — Phase 1's results give priors on which categories matter most on attitudes; Phase 2 tests whether the same priors hold cross-outcome. Confirmatory designs need less power than exploratory.

**Budget:**
| Line | Cost |
|---|---|
| Prolific recruitment, 30 × 2 sessions × $15 | ~$900 |
| AI moderator API costs (Realtime API, ~30 min × 30 sessions) | ~$150 |
| LLM persona evaluation (30 × 5 conditions × ~64 items × 2 samples) | ~$200-400 |
| Buffer (re-runs, drop-outs, attention-check failures) | ~$300 |
| **Total** | **~$1,500-1,750** |

**Timeline:** ~7-9 weeks
- Weeks 1-2: AI moderator setup on OpenAI Realtime API; pilot 2 transcripts in-house to verify module separation works
- Weeks 3-4: Run Wave 1 with all N respondents (rolling)
- Weeks 5-6: 2-week separation enforced
- Week 7: Run Wave 2 follow-up
- Weeks 8-9: Decompose transcripts, run LOO pipeline, analyze, draft writeup

## 9. What Phase 2 produces

**Headline**: the first published feature × outcome 2D feature-importance map for LLM personas — covering the rows where Park identified the largest interview-vs-surveys gap (BFI 0.15, games 0.28).

**Methodological contributions:**
- Modular interview design as a tool for content-level ablation
- LLM-assisted transcript decomposition protocol with human-coded validation
- "Park-comparable interview at academic budget" deployment recipe (Prolific + self-hosted AI moderator)

**Theoretical contributions:**
- Mechanism for Park v2's BFI/games gap (which interview content does the work)
- Cross-outcome transferability of feature-category importance (do the same categories matter across BFI / games / GSS, or do different outcomes need different content?)
- Direct response to Bisbee/Hullman "synthetic-sample sloppiness" critique: cross-outcome prediction with held-out paired data is structurally different from within-survey self-correlation

## 10. How Phase 1 and Phase 2 compose into the thesis

| Phase | Outcome row covered | N | Method | Cost | What it answers |
|---|---|---|---|---|---|
| **Phase 1** | GSS attitudes | ~1,500 | GSS Three-Wave Panel public data + LOO across feature categories | ~$300-500 | Which feature category matters on the row where surveys ≈ interview (Park's 0.82 vs 0.83) |
| **Phase 2** | BFI + games + GSS | 20-30 | New paired-wave Prolific collection + interview-content LOO | ~$1,500-1,750 | Which interview-content category drives Park's interview > surveys gap on BFI (0.15) and games (0.28) |

**Composed thesis chapters:**
- Chapter 1 — Park v2 outcome-stratified framing & motivation
- Chapter 2 — Phase 1 method + results (GSS-attitude row, large N)
- Chapter 3 — Phase 2 method + results (BFI/games rows, interview decomposition)
- Chapter 4 — Cross-phase synthesis: do feature categories transfer across outcomes? methodological limits; future work

**Strategic logic of running both:** Phase 1 is cheap and answers one row at high N; Phase 2 is expensive but answers two rows where the gap actually matters. Running both gives the thesis the full 4×3 matrix and a direct answer to the question Park's v2 posed but did not resolve.

## 11. Limitations

1. **N=20-30 is small** — directional findings, not population-level inference. Confidence intervals will be wide for the rarer effect cells.
2. **AI moderator paraphrase variance** — same concern as pilot. Documented as acceptable noise; depth-quality varies across respondents.
3. **Module separation isn't perfect** — even with strict scripting, ~5-10% of content is cross-categorical. The reassignment + shared-track method handles this transparently but introduces some classifier noise.
4. **Behavioral games as survey vignettes ≠ real games** — Park's actual games involved real money. Vignette versions correlate but don't replicate. Documented as a deviation.
5. **No real test-retest baseline** — unlike Phase 1, Phase 2 doesn't have within-person retest. Headline is raw normalized accuracy with Phase 1's GSS-row retest as a reference point only.

## 12. Decisions asked of Bayati at the meeting

1. **Endorse Phase 2** as the interview-decomposed study replacing the earlier "paired structured survey" idea. Confirms thesis direction.
2. **Endorse Prolific + self-hosted AI moderator** as the platform pivot — moves the project off Cookiy for the long-interview phase. Cookiy stays useful for the pilot data but is not the production platform.
3. **Endorse N=20-30** as adequate for Phase 2's confirmatory design, conditional on Phase 1's priors. Or argue for higher N.
4. **Endorse the module structure** — 4 modules mapped 1:1 to the 4 feature categories. Or argue for an alternative structure (e.g., SCOPE's 8 facets).
5. **Endorse pre-registration** of the decomposition protocol + module assignment + primary metric on OSF before Wave 1 launches.

If 1-5 are yes, Phase 1 launches immediately (week of meeting); Phase 2 launches once Phase 1's N=100 sanity-check returns. Both phases land within a single semester.
