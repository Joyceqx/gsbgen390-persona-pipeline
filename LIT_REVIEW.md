# Literature Review — AI Persona Simulation & Survey-Feature Importance

**Maintained by:** Joyce Yu, GSBGEN390 Spring 2026
**Last updated:** 2026-05-09
**Scope:** ~30 papers organized by theme, mapped against the thesis question — *which survey-collectible features most predict persona fidelity?* Themes 1–5 cover the AI-persona literature directly; Theme 6 imports construct-theory foundations from organizational behavior, personality / cognitive science, and social psychology, organized by eval-battery family.

This is a working bibliography, not a full literature review. Each entry has the same structure: **Citation · Core contribution · Method · Relevance to thesis · Borrowable design choices.**

---

## Theme 1 — Foundational generative-agent work

### 1.1 Park et al. (2023). *Generative Agents: Interactive Simulacra of Human Behavior.* UIST '23.
- **Core contribution.** Introduced the architecture: LLM + memory stream + reflection + planning loop, applied to 25 simulated agents in a town ("Smallville"). Won Best Paper at UIST.
- **Method.** Each agent has a natural-language memory store; behavior is driven by retrieval over that store + LLM-generated plans.
- **Relevance.** This is the architectural ancestor of Park 2024. Read to understand *why* persona-in-context works at all.
- **Borrowable.** The memory + reflection pattern is overkill for our pilot but is the right scaffolding for the thesis-stage version if we want personas to behave consistently across a multi-question survey administered as a conversation.
- arXiv: 2304.03442 · [GitHub](https://github.com/joonspk-research/generative_agents)

### 1.2 Park, Zou, Shaw, Hill, Cai, Morris, Willer, Liang & Bernstein (2024). *Generative Agent Simulations of 1,000 People.* arXiv:2411.10109. (Later retitled *LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals.*)
- **Author affiliations.** Park, Zou, Liang, Bernstein, Willer (Stanford); Shaw (Northwestern); Hill (University of Washington); Cai, Morris (Google DeepMind). Stanford-led with cross-institution collaboration.
- **Core contribution.** The paper our thesis builds on. n=1,052 U.S. adults; 2-hour AVP-style interview → LLM persona → held-out GSS/BFI/economic-game battery.
- **Headline numbers — GSS attitudes** (% of test-retest reliability): demographics 74% / interview 83% / surveys 82% / combined 86%. The "surveys ≈ interview" framing in the proposal came from this row alone.
- **Outcome-stratified breakdown (v2 paper, Tables 2–3).** The "surveys ≈ interview" claim does **not** generalize beyond attitudes:
  - **GSS attitudes (normalized accuracy):** interview 0.83 / surveys 0.82 — tie
  - **BFI-44 personality (normalized correlation):** interview 0.80 / surveys 0.65 — surveys lag by 0.15
  - **Behavioral economic games (normalized correlation):** interview 0.66 / surveys 0.38 — surveys lag by 0.28
- **Method.** Custom voice-to-voice AI interviewer (not human), AVP-protocol-grounded, adaptive follow-ups, 6,491 words/transcript average. Park's "surveys-only" condition uses GSS + full BFI-44 (saturated standardized batteries) as input.
- **v1 vs v2 note.** The original v1 abstract led with an interview-based normalized-accuracy headline of ~0.85; v2 reorganized conditions and added the per-outcome breakdown above. Both versions live at the same arXiv ID. Citing v2 is correct for current literature; the proposal's "85%" was v1.
- **Relevance.** Direct prior work. Our pilot replicates the architecture; the thesis extension is the **outcome-stratified feature-importance analysis** Park did not run — *which* survey-collectible feature category closes *which* part of the BFI/games gap.
- **Borrowable.** Full eval battery; condition design (demo / description / interview / surveys / combined); test-retest baseline framing; per-outcome reporting structure (do not collapse to a single number).
- arXiv: 2411.10109 · [HAI summary](https://hai.stanford.edu/news/ai-agents-simulate-1052-individuals-personalities-with-impressive-accuracy)

---

## Theme 2 — Evaluation frameworks for persona quality

### 2.1 Eval4Sim (2026). arXiv:2603.02876.
- **Core contribution.** Three-dimensional evaluation: **Adherence** (does the persona's background show up in utterances), **Consistency** (does identity hold across conversations), **Naturalness** (does conversation flow like a human's, neither rigid nor over-optimized).
- **Method.** Penalizes deviation from PersonaChat reference corpus in *both directions* — i.e., a persona that's too uniform is as bad as one that's too random. Avoids LLM-as-judge opacity.
- **Relevance.** Directly applicable to the thesis evaluation framework. The three axes give us names for what our metrics actually measure (our Likert MAE = adherence; our self-MAE = consistency; we don't have naturalness).
- **Borrowable.** Use Adherence/Consistency/Naturalness terminology in the thesis writeup. Consider adding a naturalness check on Conditions C/D outputs.

### 2.2 SCOPE: A Socially-Grounded Persona Framework. arXiv:2601.07110.
- **Core contribution.** **"Demographics explain only ~1.5% of variance in human response similarity."** Built from a 141-item, 2-hour sociopsychological protocol with 124 U.S. participants. Integrates 8 sociopsychological facets, separates conditioning vs. evaluation explicitly.
- **Method.** Construct personas from increasingly rich sociopsychological inputs; measure improvement in behavioral prediction.
- **Relevance.** **The single most thesis-relevant paper after Park 2024.** SCOPE's finding that demographics are a structural bottleneck *directly motivates* the thesis question of which non-demographic features matter most.
- **Borrowable.** The 8-facet sociopsychological taxonomy is a candidate refinement of our four-category taxonomy. Consider mapping our demographic/behavioral/psychological/attitudinal bins to SCOPE's facets for thesis-stage subdivision.

### 2.3 PersonaGym (Findings of EMNLP 2025).
- **Core contribution.** Benchmark for evaluating persona agents across many tasks; complements Eval4Sim's three axes.
- **Relevance.** A possible second-axis benchmark to run our thesis personas against, separate from the held-out battery design.

### 2.4 Funder & Ozer (2019). *Evaluating effect sizes in psychological research: Sense and nonsense.* AMPPS.
- **Core contribution.** Calibration table for psychological effect sizes: r=.05 very small, r=.10 small-but-consequential, r=.20 medium, r=.30 large, r=.40+ very large. Argues that "small" effects can have large cumulative consequences across people and time.
- **Relevance.** Sanity-check for LOO ablation effect sizes in the thesis. When a feature category's removal causes a 0.05 drop in normalized accuracy, this is the citation that frames it as "small but real" rather than dismissing it.
- **Borrowable.** Effect-size labels for the thesis results table; explicit recognition that meaningful feature-importance gaps can sit below r=.20.
- DOI: 10.1177/2515245919847202

---

## Theme 3 — Validity skepticism (the necessary counter-evidence)

### 3.1 Bisbee et al. (2024–2025). *Synthetic Replacements for Human Survey Data? The Perils of LLMs.* Cambridge — *Political Analysis*.
- **Core contribution.** Synthetic samples break the logic of traditional survey research: there is no reliable link between model-generated responses and population parameters. Models systematically misrepresent marginalized groups.
- **Relevance.** **Required-reading counterweight.** Any thesis claim that "surveys can substitute for interviews because LLM personas approach interview accuracy" needs to engage with this paper. The thesis position should be: *for individual-level fidelity (Park's framing), persona-conditioning works; for population-level inference (Bisbee's framing), it does not — and these are different tasks.*

### 3.2 Hullman et al. *Validating LLM Simulations as Behavioral Evidence* (Northwestern).
- **Core contribution.** Frames the question as: when, exactly, can LLM-simulated behavior count as evidence about humans? Articulates conditions under which it can and cannot.
- **Relevance.** Provides epistemological scaffolding for the thesis discussion. Joyce should reference this when defending the pilot's framing.

### 3.3 Cui et al. (2025). LLM replication of social science effects.
- **Core contribution.** **LLMs replicate the direction and significance of ~81% of main effects across 156 randomly selected social science studies.** Aggregate-level, not individual-level, fidelity.
- **Relevance.** A useful complement to Park's 83% — both numbers land near the same magnitude but measure different things (population-effect replication vs. individual-response prediction).

### 3.4 Mitigating Social Desirability Bias in Random Silicon Sampling. arXiv:2512.22725.
- **Core contribution.** LLMs tend to give "socially desirable" answers, especially on sensitive items. Proposes mitigations.
- **Relevance.** Direct concern for Conditions B/C/D in the thesis — if the persona LLM smooths participant answers toward acceptability, our agreement metric understates fidelity for items where the participant's true answer was non-normative. Must check this on items like `polviews` and `bfi_a_r` (find fault with others).

---

## Theme 4 — Theoretical / methodological foundations

### 4.1 Kang (2026). *LLM Personas as a Substitute for Field Experiments in Method Benchmarking.* arXiv:2512.21080.
- **Core contribution.** Conditions under which LLM persona simulation can validly substitute for an A/B field experiment. Specifically, when (i) only aggregate outcomes are observed and (ii) evaluation is method-blind, swapping humans for personas is just a panel change. Provides explicit information-theoretic bounds on the *number* of persona evaluations needed for decision-relevance.
- **Relevance.** **The N question for the thesis.** This paper gives us a principled answer to "how many personas do we need to detect a feature-importance effect of size X." Read carefully when designing the thesis-stage replication — it dictates sample-size planning for the LOO ablation.

### 4.2 Whose Personae? *Synthetic Persona Experiments in LLM Research and Pathways to Transparency.* arXiv:2512.00461.
- **Core contribution.** Calls for transparency in how synthetic persona experiments are run and reported.
- **Relevance.** Methodological hygiene for the thesis writeup. Should pre-register on OSF, document prompt versions, model versions, sample composition.

### 4.3 Brunswik (1956). *Perception and the Representative Design of Psychological Experiments.* University of California Press. (**Lens Model**)
- **Core contribution.** The lens model: a distal latent property (e.g., a personality trait) is inferred by a judge through a fan of probabilistically valid proximal cues. Cue *validity* (cue ↔ trait) and cue *utilization* (cue ↔ judgment) decompose accuracy into separable terms.
- **Relevance.** **The natural epistemological frame for persona inference.** A persona pipeline *is* a lens-model setup: latent participant traits → survey/interview cues → LLM persona's predicted answer. This lets us write the thesis question as "which cues maximize utilization-validity overlap?" rather than the looser "which features matter?" Pair with Funder (RAM) below.
- **Borrowable.** Lens-model decomposition language for the writeup; an explicit diagram in the introduction; the "representative design" idea (sample cues as they occur in the wild) as a defense against artificially saturated prompts.
- Hammond's (1996) *Human Judgment and Social Policy*, Chapter 6, is the readable secondary source.

### 4.4 Funder (2012). *Accurate personality judgment.* Curr. Dir. Psych. Sci. (**Realistic Accuracy Model**)
- **Core contribution.** RAM: accurate trait judgment requires four sequential stages — (1) **relevance** (the trait must be expressed in behavior), (2) **availability** (relevant behavior must occur where the judge can see it), (3) **detection** (the judge must notice the cue), (4) **utilization** (the judge must use the cue correctly). A failure at any stage caps overall accuracy.
- **Relevance.** **Diagnostic vocabulary for *why* feature categories fail.** The Park interview→survey gap on BFI personality (0.15) and games (0.28) is, in RAM terms, an *availability* failure — surveys don't surface the relevant cues. The thesis can use RAM to label each LOO drop ("dropping `current_employment` is a relevance failure for SATJOB; dropping `voting_choice` is an availability failure for POLVIEWS").
- **Borrowable.** Four-stage taxonomy as a column in the LOO results table; framing the thesis as a partial empirical test of the RAM availability stage when judge = LLM.
- DOI: 10.1177/0963721412445309

### 4.5 Vazire (2010). *Who knows what about a person? The Self–Other Knowledge Asymmetry (SOKA) model.* JPSP.
- **Core contribution.** Self-reports and observer reports systematically diverge: self is more accurate on *internal, evaluatively neutral* traits (neuroticism); others are more accurate on *external, evaluative* traits (intellect, dominance). Driven by observability + ego-protective motives.
- **Relevance.** Sharpens the question of what an LLM persona *is*. A persona conditioned on self-report mimics a self-judge; one conditioned on interview transcript (which contains observable speech style, hesitations, narrative choices) is closer to an observer-judge. SOKA predicts these will be differentially accurate by trait, which is exactly Park's per-outcome pattern.
- **Borrowable.** Hypothesis-generating frame for Phase 2: BFI traits with high self-knowledge (neuroticism) should narrow the survey-vs-interview gap; traits with low self-knowledge (intellect) should not.
- DOI: 10.1037/a0017908

---

## Theme 5 — Adjacent work worth knowing

### 5.1 Agarwal. *The Silicon Sample: Benchmarking Synthetic Users Against Human Respondents in Market Research.* SSRN (2025–2026).
- **Core contribution.** Compares synthetic and human respondents specifically in *market research* contexts. Directly relevant to Joyce's industry framing (Lens platform).
- **Relevance.** Market-research-specific validation, complementing Park's social-science framing.

### 5.2 PersonaAgent (2025). arXiv:2506.06254.
- **Core contribution.** Adds episodic + semantic memory and personalized action modules on top of persona prompting. Ablation studies validate persona prompt + test-time alignment as critical components.
- **Relevance.** A more architecture-heavy direction the thesis could cite when discussing why we *don't* need that complexity for the survey-prediction task.

### 5.3 Persona-Conditioned LLMs as Synthetic Survey Respondents. arXiv:2602.18462.
- **Core contribution.** Empirical assessment of reliability of persona-conditioned LLMs in survey settings. (Need to read full abstract for specifics.)
- **Relevance.** Closest existing work to Joyce's thesis design. Use as a comparison baseline for methodology.

---

## Theme 6 — Construct theory underlying the eval batteries

The AI-persona literature (Themes 1–5) studies *how to simulate* people; it rarely engages with *what each battery is supposed to measure*. This theme imports the foundational construct theory for each battery family in `archive/eval_battery.json` (pilot) and `gss_battery_map.json` (Phase 1). Use these citations to motivate (a) why batteries are grouped the way they are, (b) why some constructs are deeper than surveys can reach, and (c) what the survey-vs-interview gap *means* substantively.

### 6.1 Personality (BFI-10; Phase 2 BFI-44)

#### 6.1.1 McAdams (1995). *What do we know when we know a person?* J. Personality.
- **Core contribution.** Three-level personality framework: **Level 1 — dispositional traits** (Big Five), **Level 2 — characteristic adaptations** (goals, values, coping strategies, contextualized motives), **Level 3 — integrative life narratives** (the internalized story that gives a life unity and purpose).
- **Method.** Theoretical synthesis spanning trait psychology, motivational psychology, and narrative psychology.
- **Relevance.** **The single most important construct-theory paper for the thesis.** It directly explains the Park interview→survey gap: BFI items index Level 1 only; an open-ended interview surfaces Levels 2 and 3 ("characteristic adaptations" via probed goals/coping; "life narrative" via biographical questions). Cite this whenever you motivate why interviews carry information surveys cannot.
- **Borrowable.** Three-level vocabulary for the introduction; explicit claim that the BFI gap of 0.15 and the games gap of 0.28 are gaps at Levels 2–3, not Level 1.
- DOI: 10.1111/j.1467-6494.1995.tb00500.x

#### 6.1.2 DeYoung (2015). *Cybernetic Big Five Theory.* J. Research in Personality.
- **Core contribution.** Reformulates the Big Five as parameters of a cybernetic goal-pursuit system, grounded in dopaminergic and serotonergic neural systems. Each trait is the stable parameter of a specific psychological function (e.g., extraversion = sensitivity to incentive reward).
- **Relevance.** Lets the thesis assert "BFI items are surface markers of stable neural-system parameters, not arbitrary self-descriptions" with neuroscience-grade citations. Useful in the discussion when defending why BFI traits are stable enough to be predicted from sparse cues at all.
- DOI: 10.1016/j.jrp.2014.07.004

#### 6.1.3 Mischel & Shoda (1995). *A cognitive-affective system theory of personality.* Psych Review.
- **Core contribution.** **CAPS** (Cognitive-Affective Personality System): personality is best characterized as if-then situation-behavior signatures, not global traits. Apparent inconsistency across situations is itself the data, not noise.
- **Relevance.** Necessary counterpoint to FFM. Useful when defending why a persona prompt cannot be reduced to a trait vector — it must encode situational contingencies. Bridges to Phase 2 behavioral games (where situational structure is the entire point).
- **Borrowable.** "If-then signatures" framing for designing Phase 2 game scenarios that go beyond global trait reports.
- DOI: 10.1037/0033-295X.102.2.246

### 6.2 Subjective wellbeing & job satisfaction (`subjective_wellbeing` battery: HAPPY, HAPMAR, SATJOB, LIFE)

#### 6.2.1 Diener (1984). *Subjective well-being.* Psych Bulletin.
- **Core contribution.** Tripartite SWB framework: (1) life satisfaction (cognitive), (2) positive affect, (3) negative affect — three separable components.
- **Relevance.** Foundational citation for grouping HAPPY + HAPMAR + SATJOB + LIFE as a single battery. The thesis's `subjective_wellbeing` lump is justified by Diener's framework; a sharper Phase 2 design could split affect from satisfaction.
- **Borrowable.** Tripartite decomposition as a refinement candidate when N permits.
- DOI: 10.1037/0033-2909.95.3.542

#### 6.2.2 Ryff (1989). *Happiness is everything, or is it?* JPSP.
- **Core contribution.** Eudaimonic counterpoint to Diener's hedonic SWB. Six dimensions of psychological wellbeing: autonomy, environmental mastery, personal growth, positive relations, purpose in life, self-acceptance.
- **Relevance.** Caveat for the thesis: GSS hedonic items don't exhaust the construct. Useful when discussing limits of generalizing wellbeing claims.
- DOI: 10.1037/0022-3514.57.6.1069

#### 6.2.3 Hackman & Oldham (1976). *Motivation through the design of work.* OBHP.
- **Core contribution.** **Job Characteristics Model (JCM).** Five core job dimensions — skill variety, task identity, task significance, autonomy, feedback — combine into Motivating Potential Score, which predicts SATJOB and intrinsic motivation.
- **Method.** OB classic; Hackman & Oldham's foundational empirical demonstration in industrial samples.
- **Relevance.** **Direct OB anchor for SATJOB** — Bayati's home discipline. Lets the thesis frame SATJOB prediction not as "another Likert item" but as a measurable function of job characteristics that GSS doesn't fully capture (a concrete example of an *availability* failure in RAM terms).
- **Borrowable.** JCM dimensions as a candidate Phase 2 module for SATJOB-specific feature collection.
- DOI: 10.1016/0030-5073(76)90016-7

### 6.3 Interpersonal trust (`interpersonal_trust` battery: FAIR, HELPFUL, TRUST)

#### 6.3.1 Rotter (1967). *A new scale for the measurement of interpersonal trust.* J. Personality.
- **Core contribution.** Origin of the modern trust-scale tradition; trust as a generalized expectancy that another's word can be relied upon.
- **Relevance.** Cite when defining what the GSS trust triad is *for* — Rotter's expectancy framing is the ancestor of the GSS items.
- DOI: 10.1111/j.1467-6494.1967.tb01454.x

#### 6.3.2 Yamagishi & Yamagishi (1994). *Trust and commitment in the United States and Japan.* Motivation and Emotion.
- **Core contribution.** Distinguishes **trust** (belief in others' benevolence under social uncertainty) from **assurance** (belief in others' compliance due to incentive structure). Reframes trust as social intelligence.
- **Relevance.** Sharper construct definition than Rotter. Lets the thesis distinguish the GSS items (trust proper) from situations where compliance is institutionally enforced — relevant when interpreting cross-domain transfer.
- DOI: 10.1007/BF02249397

#### 6.3.3 Glaeser, Laibson, Scheinkman & Soutter (2000). *Measuring trust.* QJE.
- **Core contribution.** Behaviorally validates the GSS trust item against laboratory trust games. The standard survey item predicts trustworthy *behavior* (sending money) better than it predicts trusting *attitudes*.
- **Relevance.** **Direct bridge between Phase 1 (`interpersonal_trust` battery) and Phase 2 (behavioral economic games).** This is the citation that lets the thesis claim Phase 2 game outcomes are theoretically continuous with Phase 1 attitude items, not a separate domain.
- **Borrowable.** Trust-game design pattern for Phase 2; the validation logic (does the survey item predict the behavioral analog?) is itself a thesis sub-question.
- DOI: 10.1162/003355300554926

### 6.4 Political and moral attitudes (POLVIEWS singleton; `abortion`, `gender_role_attitudes`, `sexual_morality`, `civil_lib_*`, `religious_belief`, `economic_help`, `national_priorities`, `moral_legalization`, `adolescent_sex_policy`, `end_of_life`, `police_use_of_force` batteries)

#### 6.4.1 Converse (1964). *The nature of belief systems in mass publics.* In Apter (ed.), *Ideology and Discontent.*
- **Core contribution.** Classic finding that mass-public belief systems show low **constraint** — knowing one attitude poorly predicts another, except among elites. Belief systems are organized loosely around "non-attitudes" rather than coherent ideology.
- **Relevance.** **Critical for the Battery LOO design.** Converse's low-constraint finding predicts that dropping `gender_role_attitudes` should *not* much hurt prediction of `abortion` — they are not held together by ideology in mass samples. If the thesis observes high cross-battery transfer, that is itself a non-trivial finding (LLM personas may be artificially imposing constraint that humans don't have).
- **Borrowable.** Constraint as a falsifiable prediction for the LOO results.
- Reprinted in *Critical Review* 18 (2006): 1–74. DOI: 10.1080/08913810608443650

#### 6.4.2 Haidt & Graham (2007). *When morality opposes justice.* Social Justice Research. (**Moral Foundations Theory**)
- **Core contribution.** **MFT.** Five (later six) moral foundations: **care/harm, fairness/cheating, loyalty/betrayal, authority/subversion, sanctity/degradation**, and (added later) **liberty/oppression**. Liberals weight care+fairness; conservatives spread weight more evenly across all foundations.
- **Relevance.** **Cleanest single re-labeling of your attitudinal batteries.** `abortion` + `sexual_morality` + `religious_belief` + `adolescent_sex_policy` load on **sanctity**; `gender_role_attitudes` + `economic_help` + `racial_inequality_perception` on **care/fairness**; `civil_lib_atheists/racists/communists` on **liberty**; `police_use_of_force` on **authority**. This lets the thesis present results not as "15 attitudinal batteries" but as "5 moral foundations × LLM-persona fidelity."
- **Borrowable.** Foundation labels as a secondary axis in the attitudinal LOO results; potential alternative aggregation if the 15-battery Holm correction is too punishing.
- DOI: 10.1007/s11211-007-0034-z

#### 6.4.3 Schwartz (1992). *Universals in the content and structure of values.* Advances in Experimental Social Psychology.
- **Core contribution.** Ten basic human values (later refined to 19) organized along two axes: **openness-to-change vs conservation** and **self-transcendence vs self-enhancement**. Cross-culturally validated.
- **Relevance.** Compatible with Haidt; broader (covers economic + work values, not just moral). Useful for `economic_help`, `national_priorities`, and any Phase 2 work-values module.
- DOI: 10.1016/S0065-2601(08)60281-6

#### 6.4.4 Jost, Glaser, Kruglanski & Sulloway (2003). *Political conservatism as motivated social cognition.* Psych Bulletin.
- **Core contribution.** Meta-analysis of 88 samples: conservatism correlates with intolerance of ambiguity, need for closure, death anxiety, and system justification motives. Frames POLVIEWS as a downstream consequence of underlying epistemic and existential motives.
- **Relevance.** The motivated-cognition account of POLVIEWS. Implies POLVIEWS prediction depends on capturing those upstream motives — most of which the GSS doesn't measure directly. A potential explanation for why a singleton item might be hard to predict from demographic + behavioral cues alone.
- DOI: 10.1037/0033-2909.129.3.339

#### 6.4.5 Stouffer (1955). *Communism, Conformity, and Civil Liberties.* Doubleday.
- **Core contribution.** Foundational study of political tolerance toward unpopular groups (atheists, communists, socialists). Originated the survey-item template still in GSS today.
- **Relevance.** **Origin of your `civil_lib_atheists` / `civil_lib_racists` / `civil_lib_communists` batteries.** The SPK/COL/LIB items are Stouffer items in everything but year. Citation hygiene — these batteries should be attributed.
- (No DOI; book.)

### 6.5 Consumer behavior (`loyal` item; Lens-platform framing)

#### 6.5.1 Oliver (1999). *Whence consumer loyalty?* J. Marketing.
- **Core contribution.** Four-stage loyalty hierarchy: **cognitive** (information-based) → **affective** (preference-based) → **conative** (intention-based) → **action** (behavioral). Each stage has distinct vulnerability to switching.
- **Relevance.** A single Likert item (`loyal`) cannot separate stages — useful caveat. Frames the limit of what one consumer-decision item can carry, motivating any Phase 2 expansion of the consumer module.
- DOI: 10.2307/1252099

#### 6.5.2 Aaker (1997). *Dimensions of brand personality.* J. Marketing Research.
- **Core contribution.** Brand-personality five-factor structure: **sincerity, excitement, competence, sophistication, ruggedness**. Maps brand perception onto a quasi-FFM space.
- **Relevance.** Bridge between BFI personality and consumer batteries. Particularly relevant to the **Lens-platform industry framing** — a persona who can answer brand-personality items is doing the same kind of inference at consumer scale that BFI-10 tests at human-trait scale.
- **Borrowable.** Brand-personality items as a Phase 2 add-on for the industry-deployment narrative.
- DOI: 10.1177/002224379703400304

---



1. **Outcome-stratified feature-importance ablation.** No paper systematically removes feature categories from the persona prompt and measures the marginal contribution *per outcome dimension*. Park 2024 compares interview vs. survey vs. combined and reports per-outcome (GSS / BFI / games) gaps, but does not subdivide "surveys" by feature type. The thesis novelty is the **two-way decomposition**: which feature category × which outcome dimension. The interview→surveys gap is 0.01 on attitudes, 0.15 on personality, 0.28 on games — that pattern is itself a research target.
2. **Industry-deployment-aware methodology.** SCOPE and Eval4Sim are academic benchmarks; Park used custom-built tooling. The cost/fidelity tradeoff using *commercial* AI-moderator platforms (Cookiy, Outset, Listen Labs) is unmapped. The thesis can fill this with deliberate documentation of platform constraints (15-min cap, no participant pairing, paraphrase variance — all observed in our pilot).
3. **Item-level vs category-level feature importance.** Even SCOPE, with its 8-facet taxonomy, does not run leave-one-item-out within facet. The thesis could go finer-grained at higher N.

---

## Reading priority for the next two weeks

**AI-persona track (Themes 1–5):**
1. **Park 2024 full text** — re-read sections 4 (eval design) and 5 (results table) carefully against the pilot's design.
2. **SCOPE paper** — borrow the 8-facet taxonomy as a refinement of the 4-category one.
3. **Kang 2026** — sample-size planning for the LOO ablation in the thesis.
4. **Bisbee/Cambridge piece** — to defend the thesis framing against "but synthetic samples are bad" objections.
5. **Eval4Sim** — for evaluation-framework vocabulary in the writeup.

**Construct-theory track (Theme 6) — read in this order:**
6. **McAdams 1995** (~25 pp.) — three-level personality theory. **Highest leverage.** Will reshape the introduction and explain Park's per-outcome gap. Read first.
7. **Funder 2012 — RAM** (~6 pp., *Current Directions*). Short and immediately useful — the four-stage taxonomy will sharpen how every LOO result is described.
8. **Haidt & Graham 2007** + the MFT codebook (~30 min). After this you can re-label the 15 attitudinal batteries by foundation in an afternoon.
9. **Brunswik / Hammond 1996 Ch. 6** (lens model, secondary source — readable). The epistemological frame for the whole pilot. Pair with Funder 2012.
10. **Diener 1984** — short, foundational, citation-target for `subjective_wellbeing`.
11. **Glaeser et al. 2000** (QJE) — the trust-survey ↔ trust-game bridge; also good Phase 2 prep.
12. **Funder & Ozer 2019** — effect-size calibration, ~10 pp.

**Background — I (Claude / co-authoring assistant) can summarize on demand without you reading the originals:** DeYoung 2015, Mischel & Shoda 1995, Ryff 1989, Hackman & Oldham 1976, Rotter 1967, Yamagishi 1994, Converse 1964, Schwartz 1992, Jost et al. 2003, Stouffer 1955, Oliver 1999, Aaker 1997, Vazire 2010.

---

## Sources

- [Park et al. 2024 — arXiv 2411.10109](https://arxiv.org/abs/2411.10109)
- [Park et al. 2023 — Generative Agents arXiv 2304.03442](https://arxiv.org/abs/2304.03442)
- [Stanford HAI summary of 1052 People paper](https://hai.stanford.edu/news/ai-agents-simulate-1052-individuals-personalities-with-impressive-accuracy)
- [Eval4Sim — arXiv 2603.02876](https://arxiv.org/abs/2603.02876)
- [SCOPE Sociopsychological Persona Framework — arXiv 2601.07110](https://arxiv.org/html/2601.07110)
- [Kang — LLM Personas as Substitute for Field Experiments — arXiv 2512.21080](https://arxiv.org/abs/2512.21080)
- [Whose Personae? — arXiv 2512.00461](https://arxiv.org/html/2512.00461)
- [Persona-Conditioned LLMs as Synthetic Survey Respondents — arXiv 2602.18462](https://arxiv.org/html/2602.18462)
- [Mitigating Social Desirability Bias — arXiv 2512.22725](https://arxiv.org/html/2512.22725)
- [Hullman et al. — Validating LLM Simulations as Behavioral Evidence](https://mucollective.northwestern.edu/files/Hullman-llm-behavioral.pdf)
- [Bisbee et al. — Synthetic Replacements for Human Survey Data? — Cambridge Political Analysis](https://www.cambridge.org/core/journals/political-analysis/article/synthetic-replacements-for-human-survey-data-the-perils-of-large-language-models/B92267DC26195C7F36E63EA04A47D2FE)
- [PersonaGym — ACL 2025](https://aclanthology.org/2025.findings-emnlp.368.pdf)
- [PersonaAgent — arXiv 2506.06254](https://arxiv.org/abs/2506.06254)
- [Agarwal — Silicon Sample Benchmarking Synthetic Users (SSRN 5835122)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5835122)

### Theme 4 additions (lens-model methodology)
- Brunswik (1956). *Perception and the Representative Design of Psychological Experiments.* University of California Press.
- Hammond (1996). *Human Judgment and Social Policy*, Ch. 6 (readable secondary source for the lens model).
- Funder (2012). *Accurate personality judgment.* Curr. Dir. Psych. Sci. 21(3), 177–182. DOI: 10.1177/0963721412445309
- Vazire (2010). *Who knows what about a person? The Self–Other Knowledge Asymmetry (SOKA) model.* JPSP 98(2), 281–300. DOI: 10.1037/a0017908

### Theme 6 — Construct theory (organized by battery)

**Personality (BFI):**
- McAdams (1995). *What do we know when we know a person?* J. Personality 63(3), 365–396. DOI: 10.1111/j.1467-6494.1995.tb00500.x
- DeYoung (2015). *Cybernetic Big Five Theory.* J. Research in Personality 56, 33–58. DOI: 10.1016/j.jrp.2014.07.004
- Mischel & Shoda (1995). *A cognitive-affective system theory of personality.* Psych Review 102(2), 246–268. DOI: 10.1037/0033-295X.102.2.246

**Subjective wellbeing & job satisfaction:**
- Diener (1984). *Subjective well-being.* Psych Bulletin 95(3), 542–575. DOI: 10.1037/0033-2909.95.3.542
- Ryff (1989). *Happiness is everything, or is it?* JPSP 57(6), 1069–1081. DOI: 10.1037/0022-3514.57.6.1069
- Hackman & Oldham (1976). *Motivation through the design of work.* OBHP 16(2), 250–279. DOI: 10.1016/0030-5073(76)90016-7

**Interpersonal trust:**
- Rotter (1967). *A new scale for the measurement of interpersonal trust.* J. Personality 35(4), 651–665. DOI: 10.1111/j.1467-6494.1967.tb01454.x
- Yamagishi & Yamagishi (1994). *Trust and commitment in the United States and Japan.* Motivation and Emotion 18(2), 129–166. DOI: 10.1007/BF02249397
- Glaeser, Laibson, Scheinkman & Soutter (2000). *Measuring trust.* QJE 115(3), 811–846. DOI: 10.1162/003355300554926

**Political and moral attitudes:**
- Converse (1964). *The nature of belief systems in mass publics.* Reprinted in *Critical Review* 18 (2006), 1–74. DOI: 10.1080/08913810608443650
- Haidt & Graham (2007). *When morality opposes justice.* Social Justice Research 20(1), 98–116. DOI: 10.1007/s11211-007-0034-z
- Schwartz (1992). *Universals in the content and structure of values.* Advances in Experimental Social Psychology 25, 1–65. DOI: 10.1016/S0065-2601(08)60281-6
- Jost, Glaser, Kruglanski & Sulloway (2003). *Political conservatism as motivated social cognition.* Psych Bulletin 129(3), 339–375. DOI: 10.1037/0033-2909.129.3.339
- Stouffer (1955). *Communism, Conformity, and Civil Liberties.* Doubleday.

**Consumer behavior:**
- Oliver (1999). *Whence consumer loyalty?* J. Marketing 63 (Special Issue), 33–44. DOI: 10.2307/1252099
- Aaker (1997). *Dimensions of brand personality.* J. Marketing Research 34(3), 347–356. DOI: 10.1177/002224379703400304

**Effect-size calibration:**
- Funder & Ozer (2019). *Evaluating effect sizes in psychological research.* AMPPS 2(2), 156–168. DOI: 10.1177/2515245919847202
