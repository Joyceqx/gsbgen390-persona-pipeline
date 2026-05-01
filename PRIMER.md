# Primer — Joyce Yu × AI Persona Simulation

A 1–2 page self-introduction document. Tunable for three audiences (each version is one page). Use the version that fits the conversation; don't paste all three at once.

---

## Version A — For researchers / academics (Park, Bernstein, Bayati's circle, conference attendees)

**Joyce Yu** · Stanford GSB, Spring 2026 · independent research with Prof. Mohsen Bayati.

I'm working on a replication-and-extension of Park, Zou, Shaw, Hill, Cai, Morris, Willer, Liang & Bernstein (2024) *Generative Agent Simulations of 1,000 People* (arXiv:2411.10109; v2 retitled *LLM Agents Grounded in Self-Reports...*). The pilot is complete: I built a transcript-to-LLM persona pipeline using Cookiy as the AI moderator, ran it on N=2 interview respondents and N=1 survey respondent, and ran a leave-one-feature-out ablation on the survey arm to test which of four feature categories (demographic, behavioral, psychological, attitudinal) most predict persona fidelity. Headline pilot finding: interview-conditioned personas (Condition C) reach Likert MAE ≤ 0.08 on held-out items, and the advantage holds under a manual leakage audit even on items where the construct was never mentioned in the interview — suggesting the persona is doing real inference, not regex matching.

The thesis-stage extension I'm writing toward is the **outcome-stratified feature-importance analysis Park 2024 did not run.** Park's v2 reports per-outcome breakdowns: surveys-only matches interview-only on GSS attitudes (0.82 vs 0.83) but lags on BFI-44 personality by 0.15 and on behavioral economic games by 0.28. So the productive question isn't *"can surveys substitute for interviews?"* (no — depends on the outcome) but *"which survey-collectible feature categories close which parts of that gap on which outcomes?"* My work subdivides "surveys" into the four-category taxonomy and runs LOO ablations cross-cut by outcome dimension. This is a natural complement to SCOPE's sociopsychological-facet framework (Bao et al. 2026) and to Eval4Sim's three-axis evaluation (adherence / consistency / naturalness).

The research is also informed by **Lens**, an AI persona platform for marketing research I built and operate. Lens has surfaced the practical question — *which input data is actually worth collecting?* — that the thesis answers methodologically. I'm equally comfortable in the academic framing (extending Park / SCOPE / Eval4Sim) and the deployment framing (cost-fidelity tradeoffs across Cookiy, Outset, Listen Labs, etc.).

Open questions I'd love feedback on: (1) the right granularity for the feature taxonomy at thesis-stage N (4 buckets or finer like SCOPE's 8 facets); (2) whether to follow Park's 2-week eval separation or design around platform constraints; (3) sample-size planning per Kang's 2026 information-theoretic bounds for persona benchmarking.

---

## Version B — For industry / commercial outreach (Simile, Aaru, persona-research startups, VCs)

**Joyce Yu** · Stanford GSB MBA + creator of **Lens**, an AI persona platform for marketing research.

Two parallel tracks: I run Lens, which builds AI persona agents from real behavioral data so brands can test messaging and product concepts; and I'm doing independent research with Prof. Mohsen Bayati on a question every persona-research company has had to answer with a guess — *which input features actually drive synthetic-respondent fidelity?*

Park et al. (2024) showed interview-grounded personas can predict held-out GSS-attitude responses at 83% of test-retest reliability, and surveys-only at 82% — but their v2 paper also reports surveys lagging interviews by 0.15 on BFI personality and by 0.28 on behavioral economic games. **The commercially actionable read is outcome-stratified**: for attitudinal market-research use cases, survey-collectible inputs are nearly sufficient (and dramatically cheaper to scale); for personality-typed segmentation or behavioral-prediction use cases, the cheap-input path leaves accuracy on the table. Park did not subdivide "surveys" into feature categories — that's the gap my thesis fills. I run the leave-one-feature-out ablation across demographic / behavioral / psychological / attitudinal categories, cross-cut by outcome dimension, to map *which* feature category closes *which* part of the gap. The pilot already shows that for Study 2's respondent, dropping demographic items hurts most — direction-only at N=1, but the methodology is in place for thesis-stage N≥30.

This is directly relevant to product roadmap decisions at any company in the segment (Simile, Aaru, Synthetic Users, Evidenza, Artificial Societies, Listen Labs's persona-generation layer). The thesis answers: *if I'm building a persona platform, what's the minimal-cost data I should collect, and how does fidelity degrade as I drop categories?*

Background: B2B/B2C product-design experience, technical chops in CS (Python, ML/data-science fundamentals), and operating experience running a small but real persona-platform business. Comfortable across the academic-industry boundary; I read papers, build code, ship product.

I'd love to talk about: how your team thinks about input-feature curation; whether you'd find an externally-validated feature taxonomy useful as a customer-onboarding scaffolding; collaboration models for the thesis-stage data collection.

---

## Version C — For conferences / casual networking / social media bio

**Joyce Yu** · Stanford GSB · I research how well LLM personas can substitute for real people, and which input features matter most.

The 2-line version: *Park et al. 2024 showed AI personas built from 2-hour interviews can predict the same person's attitude answers at 83% — but they lag interviews by 0.15 on personality and 0.28 on behavioral-game outcomes. My research asks the question they skipped: out of all the input features (demographics, behaviors, psychology, attitudes), which ones close which parts of that gap on which outcomes?*

Pilot done · thesis in motion · also build Lens, an AI persona platform.

---

## Tunable parts (swap depending on context)

**Tagline (one sentence):**
> *"I research which input features close which parts of the interview→surveys fidelity gap on which outcome dimensions — the outcome-stratified feature-importance analysis Park 2024 did not run."*

**Elevator (~30 sec spoken):**
> *"AI personas built from interview transcripts can predict a specific real person's GSS-style attitude answers at 83% of test-retest reliability — that's the Park 2024 headline. The wrinkle is in their v2 paper: surveys-only matches interviews on attitudes (82% vs 83%) but lags by 0.15 on BFI personality and by 0.28 on behavioral economic games. So the question isn't 'do you need an interview?' — it's 'which kind of survey data closes which gap on which outcome?' That's my thesis. I run leave-one-feature-out ablations across four categories — demographics, behaviors, psychology, attitudes — cross-cut by outcome dimension. Pilot is done at N=3 with the methodology in place; thesis study scales to N≥30."*

**Why now (the urgency framing):**
> *"Simile just raised $100M. Aaru hit a $1B valuation. Qualtrics committed $500M to AI. 71% of researchers think the majority of market research will use synthetic responses within 3 years. The whole industry is making bets on which input data to collect — but no published work tells them what's actually predictive at the feature-category level. That's the gap."*

**The skeptical version (for academic audiences who'd push back):**
> *"This is not a claim that synthetic samples replace human studies — Bisbee 2024 and Hullman are right that population inference from synthetic data is methodologically dangerous. The thesis claim is narrower: at the level of individual prediction, which is what persona-platform companies sell, the input-feature decomposition has not been done, and that's what I'm running."*

---

## Resources / portfolio

- [Pilot dashboard](https://github.com/joyceyu/GSBGEN390) (live results, leakage audit, methodology)
- [Lens — AI persona platform for marketing research](https://lens.example) *(replace with real URL)*
- Pilot codebase: `persona_pipeline.py` + `persona_pipeline.ipynb` (Colab-ready), 100% transcript-parse rate, leakage-audit-validated.
- Related work I've engaged with: Park 2024, SCOPE (Bao 2026), Eval4Sim (2026), Kang 2026, Bisbee/Hullman skepticism, the synthetic-research market map.

---

## Notes for using this primer

- **Version A** for academic conversations. Lead with Park/SCOPE/Eval4Sim, signal academic literacy.
- **Version B** for commercial conversations. Lead with Lens + the surveys-only ≈ interview-only finding's commercial implication.
- **Version C** for low-context settings (LinkedIn, casual intros, social).
- The "skeptical version" should always be ready in your back pocket — it's the strongest signal of methodological seriousness when an academic asks "but isn't this just synthetic-sample sloppiness?"

If sending in writing: pick one version, don't combine. The whole point of having three is that the audience expects different framings.
