# Mini-Replication of Park et al. (2024) — Scoping Document

**Author:** Joyce Yu
**Course:** GSBGEN390, Spring 2026 — Prof. Mohsen Bayati
**Date:** 2026-04-29 (updated 2026-04-29 evening)
**Sprint window:** ~1.5 days (2026-04-29 → 2026-05-01)

---

## 1. What Park et al. (2024) Did

In *Generative Agent Simulations of 1,000 People* (arXiv:2411.10109), Park, Bernstein, Liang and collaborators built LLM-based agents that simulate real individuals. Their pipeline:

1. **Recruit** a stratified sample of 1,052 U.S. adults via Bovitz Inc., representative across age, gender, race, region, education, political ideology.
2. **Interview** each participant for ~2 hours using a single semi-structured session based on the **American Voices Project (AVP)** protocol developed at the Stanford Center on Poverty and Inequality. The AVP covers life history, family, neighborhood and community, employment and earnings, household spending and consumption, health and mental health, parenting and family conflict, religion and meaning, political views and voting, and attitudes about race, class, and inequality.
3. **Construct an agent** by feeding the verbatim interview transcript into an LLM (GPT-4o) as part of an extended system prompt. Each question is answered "in character" as the participant.
4. **Evaluate.** Two weeks after the interview, the same participants completed a battery of GSS attitudinal items, the Big Five (BFI-44), five canonical behavioral economic games, and five published social science experiments.

**Headline numbers (per arXiv v2, retitled *"LLM Agents Grounded in Self-Reports..."*):** held-out GSS accuracy as a fraction of participants' own two-week test-retest reliability:

| Construction condition | GSS accuracy (% of test-retest) |
|---|---|
| Demographics only | 74% |
| Interview only | 83% |
| Surveys only | 82% |
| Interview + surveys combined | 86% |

**Important caveat — "surveys ≈ interview" is a GSS-specific finding.** v2 reports per-outcome breakdowns and the picture changes substantially outside attitudinal items:

| Outcome | Interview | Surveys-only | Gap |
|---|---|---|---|
| GSS attitudes (normalized accuracy) | 0.83 | 0.82 | tie |
| BFI-44 personality (normalized correlation) | 0.80 | 0.65 | surveys lag by 0.15 |
| Behavioral economic games (normalized correlation) | 0.66 | 0.38 | surveys lag by 0.28 |

**Implication for the thesis:** the right framing is not *"can surveys substitute for interviews?"* but *"which survey-collectible feature categories close which parts of the gap on which outcome dimensions?"* The interview→surveys delta is small for attitudes, moderate for personality, and large for behavioral games — that pattern itself motivates an outcome-stratified feature-importance analysis. This is exactly the analysis Park did not run.

**Note on v1 vs v2.** The proposal cited v1's "85%" headline number (interview-only normalized accuracy ≈ 0.85 in the original abstract). v2 reorganized the conditions and reports the four numbers above. Both are at the same arXiv ID; we use v2 framing throughout this document because it's the live version of the paper.

---

## 2. What We Are Replicating (and What We Are Not)

### Replicating
- **The architectural insight:** transcript-conditioned LLM persona answers a held-out battery.
- **The held-out evaluation logic:** ground-truth answers are collected before the persona pipeline ever sees them.
- **Three persona-construction conditions** mapping to Park's design: demographics-only, persona-description, interview-conditioned.
- **The headline metric:** agreement between persona answers and self-reported answers on a fixed question battery.
- **Self-consistency dimension:** two samples per item with temperature > 0, measuring how stable the persona is with itself.

### NOT replicating (and we say so explicitly)
| Park et al. | This pilot |
|---|---|
| n = 1,052 stratified U.S. adults | N=2 (Study 1, interview arm) + N=1 (Study 2, survey arm) |
| 2-hour AI-administered AVP-protocol interview (Park's custom voice-to-voice agent with adaptive follow-ups; avg 6,491 words/transcript) | ~9 min Cookiy AI-moderated AVP-style interview (general-purpose product, no adaptive depth probes) |
| GSS + BFI-44 + 5 econ games + 5 experiments | Subset: BFI-10, ~15 GSS items, 8 consumer/decision-making items, 5 free-response |
| Self test-retest baseline at 2 weeks | Single-shot eval administered in the same session (priming risk audited via leakage filter) |
| GPT-4o (closed-source baseline) | GPT-4o-2024-08-06 by default; pipeline supports model swap to Claude |
| Surveys-only construction = full GSS battery + full BFI-44 (standardized instruments) | Study 2 surveys-only construction = 18 items spanning four pre-registered categories (demographic / behavioral / psychological / attitudinal). **This is a deliberate methodological deviation**: Park's surveys-only is a "kitchen-sink standardized battery"; ours is a leaner theory-driven taxonomy whose viability vs. Park's saturated input is part of the thesis novelty. |
| One coarse "surveys" bucket | Four-category LOO ablation (drop each of {demographic, behavioral, psychological, attitudinal}) — a finer-grained feature-importance analysis Park did not run |

This is a **proof-of-concept replication**, not a generalization. Its goal is (a) to prove the pipeline runs end-to-end on accessible tooling and (b) to surface the engineering and methodological choices that the later survey-based study (the actual thesis novelty) will inherit.

---

## 3. Pipeline Diagram

```
┌──────────────────────┐    ┌────────────────────────────────────────────┐
│  Held-out eval set   │    │  Cookiy AI-moderated AVP-style interview   │
│  (BFI-10 + GSS +     │    │  (one comprehensive session, 75–90 min)    │
│  consumer items +    │    │  10 modules: life story, family, work,     │
│  free-response)      │    │  money, daily life, health, politics,      │
└──────────┬───────────┘    │  religion, identity, future                │
           │                └─────────────────────┬──────────────────────┘
           ▼                                      ▼
   Joyce answers                          Cookiy transcript
   ground-truth                          (verbatim, untrimmed)
   (sealed, hidden                                │
    from persona)                                 ▼
           │                          ┌────────────────────────────┐
           │                          │ LLM persona prompt:        │
           │                          │  system role + materials   │
           │                          │                            │
           │            ┌─────────────┤  Three conditions:         │
           │            │             │   A: demographics only     │
           │            │             │   B: persona description   │
           │            │             │   C: full interview        │
           │            │             └─────────────┬──────────────┘
           │            │                           ▼
           │            │             ┌────────────────────────────┐
           │            │             │ Persona answers eval       │
           │            │             │ battery — 2 samples per    │
           │            │             │ item @ temp 0.7            │
           │            │             └─────────────┬──────────────┘
           │            │                           │
           ▼            ▼                           ▼
   ┌────────────────────────────────────────────────────────────────┐
   │  Metrics:                                                      │
   │   ACCURACY vs. truth                                           │
   │     - Likert MAE + within ±1                                   │
   │     - Categorical exact-match accuracy                         │
   │     - BFI trait-score RMSE                                     │
   │   SELF-CONSISTENCY (sample 1 vs. sample 2)                     │
   │     - Likert self-MAE + within ±1                              │
   │     - Categorical self-match rate                              │
   │  Per-condition breakdown (A vs. B vs. C)                       │
   └────────────────────────────────────────────────────────────────┘
```

---

## 4. Evaluation Methodology

**Battery composition (38 items total):**
- **Big Five — BFI-10** (10 items, 1–5 Likert): trait-level scores → distance vs. Joyce's true scores.
- **GSS subset** (15 items): public confidence, social trust, gender role attitudes, abortion stance, work satisfaction, etc. — categorical or 1–7 ordinal.
- **Consumer/preference items** (8 items, 1–5 Likert): brand affinity, decision-making style, willingness to pay tradeoffs, marketing receptiveness, ad skepticism, value-based avoidance.
- **Behavioral free-response** (5 items): ideal weekend, recent purchase, money tradeoff, 5-year career, recent regret.

**Three conditions to compare:**
1. **A. Demographic-only:** persona prompt with just basic facts (age range, role, region, education).
2. **B. Persona description:** prompt with a 1–3 paragraph self-description (independently written, not from the interview).
3. **C. Interview-conditioned:** prompt with the full Cookiy interview transcript.

**This three-condition design directly maps to Park's main framework** (demographics-only / persona-description / interview), giving us an information-richness ladder that previews the thesis's survey-feature-importance question.

**Metrics:**
- **Accuracy vs. truth.** Categorical exact-match, Likert MAE and % within ±1, BFI-trait Euclidean distance.
- **Self-consistency.** Each item asked twice at temperature 0.7. Compare sample 1 to sample 2 with the same metrics. A high-fidelity persona is both *accurate* and *self-consistent*; high accuracy with low self-consistency suggests the persona got lucky on individual items rather than capturing a stable model of the person.

**No claim of statistical generality.** The pilot is about pipeline correctness, not effect estimation. Sample size = 1.

---

## 5. Success Criteria for the Sprint

Walking into the next Bayati meeting, "success" looks like:

1. ✅ End-to-end pipeline executes: Cookiy interview → transcript → 3 persona conditions → answered battery (38 items × 2 samples × 3 conditions = 228 calls) → metric tables.
2. ✅ A real number for each condition × each metric.
3. ✅ Honest articulation of what the numbers mean and don't mean given n=1.
4. ✅ Concrete list of design questions surfaced by running the pilot.
5. ✅ A clear path from this pilot to the thesis study — what infrastructure is reusable, what changes when we substitute survey data for interviews.

---

## 6. Why This Is the Right First Move (Given the Three Directions)

Prof. Bayati offered three directions: (i) replicate Park et al., (ii) literature/market scan, (iii) start survey design. This pilot directly addresses (i) and *also*:

- **Surfaces the eval design** the survey-based study will need (the eval battery is invariant to how the persona was constructed).
- **Forces decisions** on persona-prompt construction, model choice, scoring, and consistency metrics — all required for the thesis anyway.
- **Demonstrates execution capability** in a way that pure-paper or pure-design progress cannot.
- **Refines the methodological motivation:** Park's surveys-only (0.82) ≈ interview-only (0.83) on GSS, but lags by 0.15 on BFI-44 and by 0.28 on economic games. The thesis's productive question is therefore **outcome-stratified**: *which feature categories close the gap on which dimensions?* The pilot infrastructure supports running that analysis once eval batteries are extended beyond GSS-style attitudes.

The lit/market scan and survey-instrument design follow naturally — and with the pipeline already running, both will be easier to scope tightly.

---

## 7. Open Methodological Questions (For the Meeting)

1. Park et al. used self test-retest as their accuracy denominator. We don't have that here. Should we run a self-retest in the next 2 weeks to recover the baseline, so our absolute numbers become comparable?
2. Both Park and our pilot use AI moderators, but Park built a custom voice-to-voice agent specifically for the AVP protocol with adaptive follow-ups, while Cookiy is a general-purpose product with fixed probes and no depth-probing behavior. Does this difference (custom protocol-specific vs. general platform) systematically thin certain content domains (e.g., emotional/relational depth)? The interview-quality audit ([`interview_quality_audit.md`](interview_quality_audit.md)) provides direct evidence.
3. For the *survey-based* version of the thesis, do we keep the same eval battery, or do we co-evolve eval and instrument?
4. What's the right N for the actual thesis study, given the cost-per-interview vs. cost-per-survey tradeoff? Park's GSS-attitudes result suggests survey-only could be cost-effective for *attitudinal* outcomes, but the BFI 0.15 / games 0.28 gaps imply interviews still earn their keep on personality and behavioral dimensions — so N planning needs to be outcome-conditioned.
5. How do we operationalize the **construction question** beyond a four-bin taxonomy? Park's "surveys-only" condition is a single coarse bucket — your thesis subdivides "surveys" into demographic / behavioral / psychological / attitudinal. Does the pilot's three-condition architecture extend cleanly to that finer grid?
6. **Eval battery extension.** The pilot uses a GSS-heavy 38-item battery (BFI-10, ~15 GSS items, 8 consumer items, 5 free-response). To detect the BFI/games-style gaps Park found, the thesis-stage battery needs full BFI-44 + at least 2–3 behavioral-game-style items. What's the right scope expansion?
