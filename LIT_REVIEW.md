# Literature Review — AI Persona Simulation & Survey-Feature Importance

**Maintained by:** Joyce Yu, GSBGEN390 Spring 2026
**Last updated:** 2026-04-30
**Scope:** ~12 papers organized by theme, mapped against the thesis question — *which survey-collectible features most predict persona fidelity?*

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
- **Headline numbers** (% of test-retest reliability): demographics 74% / interview 83% / surveys 82% / combined 86%. **Surveys-only ≈ interview-only is the key result.**
- **Method.** Custom voice-to-voice AI interviewer (not human), AVP-protocol-grounded, adaptive follow-ups, 6,491 words/transcript average.
- **Relevance.** Direct prior work. Our pilot replicates the architecture; the thesis extends with feature-importance analysis they did not run.
- **Borrowable.** Full eval battery; condition design (demo / description / interview / surveys / combined); test-retest baseline framing.
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

## What's missing from the existing literature (= thesis opportunity)

1. **Feature-importance ablation across persona-construction inputs.** No paper systematically removes feature categories from the persona prompt and measures the marginal contribution. Park 2024 compares interview vs. survey vs. combined, but does not subdivide "surveys" by feature type. **This is the thesis novelty.**
2. **Industry-deployment-aware methodology.** SCOPE and Eval4Sim are academic benchmarks; Park used custom-built tooling. The cost/fidelity tradeoff using *commercial* AI-moderator platforms (Cookiy, Outset, Listen Labs) is unmapped. The thesis can fill this with deliberate documentation of platform constraints (15-min cap, no participant pairing, paraphrase variance — all observed in our pilot).
3. **Item-level vs category-level feature importance.** Even SCOPE, with its 8-facet taxonomy, does not run leave-one-item-out within facet. The thesis could go finer-grained at higher N.

---

## Reading priority for the next two weeks

1. **Park 2024 full text** — re-read sections 4 (eval design) and 5 (results table) carefully against the pilot's design.
2. **SCOPE paper** — borrow the 8-facet taxonomy as a refinement of the 4-category one.
3. **Kang 2026** — sample-size planning for the LOO ablation in the thesis.
4. **Bisbee/Cambridge piece** — to defend the thesis framing against "but synthetic samples are bad" objections.
5. **Eval4Sim** — for evaluation-framework vocabulary in the writeup.

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
