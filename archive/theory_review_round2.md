# Theory-driven feature engineering — Round 2 (cog-sci / behavioral-science scan)

**Author:** collaborating Claude session (scaffold for Joyce)
**Created:** 2026-05-07
**Status:** Open. Companion to `archive/theory_review.md` (Round 1, moved to archive 2026-05-13 as banner'd stale under lean lock). Does NOT supersede §1–11 of that file as historical scaffolding. Joyce owns the locked decision; the live spec is `theory_interpretation_guide.md`.

This round adds (a) candidate frameworks the Round-1 scaffold missed because it skewed toward moral/values theories, (b) verified 2023–2026 LLM-applied work that establishes methodological precedent for theory-grounded persona construction, and (c) a prioritized reading list. All arXiv IDs and journal references below were retrieved via web search on 2026-05-07; none are recall-only. **Joyce should still pull the abstracts before quoting in OSF pre-reg.**

---

## 0. What this round adds vs `archive/theory_review.md`

| Round-1 gap | Round-2 contribution |
|---|---|
| 4 candidates skewed toward moral/values theories (MFT, Schwartz, Bourdieu, Cultural Theory of Risk) | +5 candidates from personality / behavioral-science / cross-cultural traditions (Big Five-HEXACO, Inglehart-Welzel, Hofstede, Theory of Planned Behavior, Dual-Process) |
| §10 explicitly admitted no 2024–2026 arXiv sweep | Verified 2024–2026 papers: Big5-Chat (ACL 2025), "Do LLMs Have Consistent Values?" (ICLR 2025), Centaur (Nature 2025), AI Psychometrics (PPS 2024), social-desirability warning (PNAS Nexus 2024), Hewitt et al. social-experiment prediction (2024), persona vectors (Anthropic 2025) |
| Citation hallucination flagged; some Round-1 names removed (Hewitt NBER, fake Tjuatja MFT claim) | Re-verified Hewitt at `treatmenteffect.app` + Stanford AI4PB; confirmed Tjuatja 2024 is response-bias work (already corrected in Round-1 §10.1) |
| No discussion of *methodological* precedent for psychology-on-LLM beyond persona work | Adds Binz & Schulz (PNAS 2023), Hagendorff "Machine Psychology", Centaur (Nature 2025), Pellert (Perspectives on Psych Science 2024), Ye et al. systematic review (arXiv 2025) — these are the methodological backbone Joyce should cite |
| No critical/skeptical literature surveyed | Adds Salecha et al. PNAS Nexus 2024 (social desirability bias in BFI-on-LLM); Bisbee et al. Political Analysis 2024 (perils of synthetic respondents); Hullman et al. (validating LLM simulations) |

---

## 1. Recommendation up front (read this before the rest)

If Joyce wants the strongest cog-sci/behavioral-science upgrade with the least added work, **the highest-leverage move is to seriously evaluate the Inglehart-Welzel 4-quadrant model** alongside Round-1's MFT and Schwartz candidates, for the following reasons:

1. **Direct empirical lineage with GSS.** Inglehart-Welzel was extracted from the World Values Survey, which shares item-level overlap with GSS (the WVS borrowed many items from GSS). The mapping from GSS variable → quadrant is therefore *less inferential* than mapping from GSS → MFT or GSS → Schwartz.
2. **Clean 4-cluster LOO structure.** Two orthogonal axes (Traditional ↔ Secular-rational; Survival ↔ Self-expression) produce 4 quadrants — same cluster count as the existing atheoretical 4-bin taxonomy, so the comparison is clean.
3. **Cross-cultural validation in 100+ countries.** Stronger generalization claim than MFT's WEIRD-bound original validation (though Atari 2023 partially fixed that).
4. **Not in §2-5 of `archive/theory_review.md`** — Round-1 missed it; this is a real gap.

**This is a recommendation for evaluation, not a lock.** The fact that Bayati's tradition is closer to behavioral economics / management science also weighs in favor of values frameworks (Inglehart, Schwartz) over moral-psych (MFT) or sociology (Bourdieu).

If Inglehart-Welzel doesn't fit on closer reading, the second-strongest move is **Big Five (CANOE) as the persona-INPUT theory layer** — this is a direct mirror of Park's Phase 2 BFI outcome row, which means Joyce can argue "we organize the *input* features around the same construct that the *output* measures" — methodologically symmetric and reviewer-resistant.

---

## 2. Additional candidate frameworks (beyond Round-1 §2–5)

### 2.1 Big Five / HEXACO personality

**Foundational citations (verify before quoting):**
- Costa & McCrae (1992). *Revised NEO Personality Inventory and NEO Five-Factor Inventory professional manual.* PAR.
- Goldberg (1990). *An alternative description of personality: The Big-Five factor structure.* JPSP, 59(6), 1216-1229.
- Ashton & Lee (2007). *Empirical, theoretical, and practical advantages of the HEXACO model of personality structure.* Personality and Social Psychology Review, 11, 150-166.
- John, Naumann, & Soto (2008). *Paradigm shift to the integrative Big Five trait taxonomy: History, measurement, and conceptual issues.* In *Handbook of personality* (3rd ed.).

**What it claims.** Five (Big Five / OCEAN) or six (HEXACO; adds Honesty-Humility) trait dimensions are sufficient to describe stable individual-difference variance in personality. Validated across 50+ language communities; lexical-hypothesis derivation gives strong theoretical pedigree.

**Fit to GSS persona-construction:**
- GSS does NOT include BFI directly, BUT GSS attitude items have known correlations with Big Five traits in published meta-analyses (e.g., Openness ↔ political liberalism; Conscientiousness ↔ traditionalism; Agreeableness ↔ helpfulness scales).
- Big Five is the construct Park's Phase 2 measures as an *outcome*. Using it as the *input* organization gives a methodologically symmetric design.
- Limitation: Big Five is an OUTPUT structure (variance-based factor analysis), not really a behavioral or attitude-organization scheme. Mapping GSS items → Big Five is INDIRECT (similar to Schwartz indirection).

**Verdict.** Strong choice IF Joyce wants symmetric input/output theory. Modest choice if she wants direct attitude-cluster mapping. Strongest reviewer reception of any candidate (Big Five is the least-contested personality framework).

### 2.2 Inglehart-Welzel cultural map (World Values Survey)

**Foundational citations (✅ VERIFIED 2026-05-10 night per OSF §17 item ④ Claude cite check):**
- Inglehart, R. & Welzel, C. (2005). *Modernization, Cultural Change, and Democracy: The Human Development Sequence.* Cambridge University Press. [ISBN 0-521-60971-2, 333 pages; data from WVS + European Values Surveys, covering 85% of world population]
- Inglehart, R. (1997). *Modernization and Postmodernization: Cultural, Economic, and Political Change in 43 Societies.* Princeton University Press. [ISBN 0-691-01180-X paperback / 0-691-01181-8 hardcover, x+453 pages; data from WVS, 70% of world population]
- Welzel, C. (2013). *Freedom Rising: Human Empowerment and the Quest for Emancipation.* Cambridge University Press. [The canonical source for **individual-level value indices**; introduces the **Emancipative Values Index** (12-item, 4 sub-domains: reproductive choice, gender equality, people's voice, personal autonomy), the **Cognitive Stimulation Index** (3-item), etc. Online appendix at www.cambridge.com/welzel.]
- World Values Survey association: https://www.worldvaluessurvey.org/

**What it claims.** Two orthogonal axes structure cross-cultural value variation (canonical 2005 nomenclature):
- **Traditional ↔ Secular-rational** (vertical / y-axis) — importance of religion, parent-child ties, deference to authority, absolute standards, traditional family values; secular-rational = "replacement of religion and superstition with science and bureaucracy as the basis of behaviour and authority relations"
- **Survival ↔ Self-expression** (horizontal / x-axis) — survival = economic + physical security, ethnocentric outlook, low trust/tolerance; self-expression = subjective well-being, individual freedom, quality of life

The 4 quadrants give a "cultural map" showing nation-level positions. An early version was created in 1997; revised maps released in 2005, 2010-2011, and 2023.

**Fit to GSS attitudinal items:**

| Quadrant | Candidate GSS items |
|---|---|
| Traditional | BIBLE, REBORN, POSTLIFE, ATTEND, RELITEN, ABANY (against), HOMOSEX (against), CAPPUN, GUNLAW (pro), FUND |
| Secular-rational | EVOLUTION, SCIBNFTS, ABANY (for), HOMOSEX (for), GRASS, PORNLAW (for) |
| Survival | NATARMS (pro), USWARY, NAT*-priorities (US-first), RACDIF1 (in-group), WLTHWHTS-BLKS (in-group) |
| Self-expression | LIBRAC, LIBCOM, SPK*-civil-liberties, HELPPOOR, NATENVIR, EQWLTH, DISCAFF*, SEXEDUC |

**Strengths.** Direct empirical lineage with GSS (items literally overlap with WVS); 4 balanced quadrants (similar item counts); cross-cultural pedigree across 100+ countries; less politically loaded than MFT.

**Risks** (revised 2026-05-10 night with verified citations + an additional methodological caveat found during cite check):

1. **Country-level vs. individual-level**: the framework is originally a *country-level* construct (national averages on the cultural map). Individual-level application is supported by Welzel (2013)'s Emancipative Values Index (12-item, individual-level) — that is the citation to use for individual-level claims, NOT the original 2005 Inglehart-Welzel cultural-map work.

2. **Single-factor vs. two-factor structure (Beugelsdijk & Welzel 2010 critique)** — verified during cite check: in 2010, calculations by Beugelsdijk and Welzel themselves suggested that the split into two factors (Traditional/Secular-rational + Survival/Self-expression) is only weakly justified by the data, and that **a single-factor solution might be appropriate** at the individual level. This is a real methodological caveat that **the 6-framework comparison in OSF Discussion section must acknowledge**: if the two-axis structure collapses to a single dimension in the GSS-2024 individual-level data, the Inglehart-Welzel quadrant predictions become less differentiated.

3. **Cultural essentialism critique (Dervin / Moloney / Simpson 2020)** — a polemical critique that the map's classifications can stigmatize developing countries as inferior to predominantly White / European / Christian ones. Not a methodological show-stopper for Phase 1 (which is US-only) but should be acknowledged if any cross-cultural extension is discussed in Phase 2 or future work.

**Verdict.** **High-priority candidate, retained in the locked 6-framework list (OSF §17 item ①, locked 2026-05-10 night).** Joyce evaluates side-by-side with MFT and Schwartz. Discussion section must cite Welzel (2013) for individual-level claims and acknowledge the 2010 single-factor caveat.

### 2.3 Hofstede's cultural dimensions

**Foundational citations:**
- Hofstede, G. (1980/2001). *Culture's Consequences: Comparing Values, Behaviors, Institutions, and Organizations Across Nations.* SAGE.
- Hofstede, G., Hofstede, G. J., & Minkov, M. (2010). *Cultures and Organizations: Software of the Mind* (3rd ed.). McGraw-Hill.

**What it claims.** Six (originally four) dimensions: Power Distance, Individualism-Collectivism, Masculinity-Femininity, Uncertainty Avoidance, Long-Term Orientation, Indulgence-Restraint.

**Fit to GSS.** Mostly *country-level*; GSS is single-country (USA). Hofstede works for cross-national comparison, less for within-country attitude prediction. **Skip for Phase 1** (not a fit). Could be revived if Phase 2 goes cross-national.

**Verdict.** Lower priority than Inglehart-Welzel for Phase 1. But: Hofstede has the strongest LLM-applied literature of any cultural-dimensions framework (see arXiv:2309.12342 — Cultural Alignment in LLMs based on Hofstede, ACL 2025), so it's a useful methodological reference even if not the chosen lens.

### 2.4 Theory of Planned Behavior (Ajzen)

**Foundational citations:**
- Ajzen, I. (1991). *The theory of planned behavior.* Organizational Behavior and Human Decision Processes, 50(2), 179-211.
- Ajzen, I. (2020). *The theory of planned behavior: Frequently asked questions.* Human Behavior and Emerging Technologies, 2(4), 314-324.

**What it claims.** Behavior is determined by *intention*, which is determined by three antecedents: (a) attitude toward the behavior, (b) subjective norms (perceived social pressure), (c) perceived behavioral control. Causal model.

**Fit to GSS persona-construction.** Different from values theories — TPB is a *causal* (not categorical) model. Could organize features causally:
- Attitude features → ABANY, HOMOSEX, CAPPUN
- Subjective norms → ATTEND, RELITEN, MARITAL (social-tie indicators)
- Perceived control → INCOME, EDUC, HEALTH (resource indicators)

**Verdict.** Interesting for *behavioral* outcome rows (Phase 2 economic games); less natural for GSS attitude prediction (Phase 1). **Park for Phase 2.**

### 2.5 Self-Determination Theory (Deci & Ryan)

**Foundational citations:**
- Deci, E. L. & Ryan, R. M. (2000). *The 'what' and 'why' of goal pursuits: Human needs and the self-determination of behavior.* Psychological Inquiry, 11(4), 227-268.
- Ryan, R. M. & Deci, E. L. (2017). *Self-Determination Theory: Basic Psychological Needs in Motivation, Development, and Wellness.* Guilford.

**What it claims.** Three innate psychological needs: autonomy, competence, relatedness. Behavior and well-being depend on whether environments support these.

**Fit to GSS.** Limited direct attitude-mapping. SAT* satisfaction items, JOBLOSE, SATJOB tap into competence/autonomy at work. Better suited for well-being outcome prediction than for attitude prediction. **Skip for Phase 1.**

### 2.6 Dual-Process Theory / Heuristics & Biases

**Foundational citations:**
- Kahneman, D. (2011). *Thinking, Fast and Slow.* Farrar, Straus and Giroux.
- Tversky, A. & Kahneman, D. (1974). *Judgment under uncertainty: Heuristics and biases.* Science, 185(4157), 1124-1131.
- Evans, J. S. B. T. & Stanovich, K. E. (2013). *Dual-process theories of higher cognition.* Perspectives on Psychological Science, 8(3), 223-241.

**Use as theory-of-LLM-cognition, not as feature taxonomy.** Dual-process is a model of *how* cognition works, not *what* features organize attitudes. Useful FRAMING for the discussion section ("Are LLM personas using System-1 pattern-matching on demographic prototypes, or System-2 reasoning over the persona's stated commitments?") but not a candidate for the feature taxonomy.

**Verdict.** Don't use as the locked theory. Cite in discussion if relevant. Hagendorff "Machine Psychology" (2023) is the canonical anchor here.

---

## 3. Verified 2024–2026 LLM-applied work (methodological precedent)

These are the papers that establish "psychology on LLMs" as a legitimate research mode and provide the methodological backbone for theory-driven persona construction. **All citations verified via web search 2026-05-07.**

### 3.1 Methodological backbone (read first)

| Citation | Why it matters | Link |
|---|---|---|
| **Binz & Schulz (2023). Using cognitive psychology to understand GPT-3.** PNAS 120(6):e2218523120 | First systematic application of cog-psych task batteries to an LLM. Establishes the precedent Joyce's project extends. | https://www.pnas.org/doi/abs/10.1073/pnas.2218523120 ; arXiv:2206.14576 |
| **Binz et al. (2025). Centaur: a foundation model of human cognition.** Nature 644:1002-1009 | Fine-tuned Llama-3.1-70B on Psych-101 (60K participants × 160 cognitive experiments) → predicts held-out human behavior across novel cog-sci tasks better than domain-specific cognitive models. **Methodological gold standard for "use cog-sci data + LLM together".** | https://www.nature.com/articles/s41586-025-09215-4 ; arXiv:2410.20268 |
| **Hagendorff, Dasgupta, Binz et al. (2023). Machine Psychology.** arXiv:2303.13988 (multiple authors incl. DeepMind) | Survey/manifesto for using psych methods to study LLMs. Four target areas: heuristics/biases, social interaction, language psychology, learning. Useful as the related-work scaffolding for Joyce's introduction. | https://arxiv.org/abs/2303.13988 |
| **Pellert, Lechner, Wagner, Rammstedt, Strohmaier (2024). AI Psychometrics: Assessing the Psychological Profiles of Large Language Models Through Psychometric Inventories.** Perspectives on Psychological Science 19(5):808-826 | Demonstrates zero-shot personality/values/morality profiling of LLMs (Big Five, Dark Tetrad, Schwartz, Moral Norms). Directly relevant — shows that psychometric instruments work as diagnostic tools on LLMs. | https://journals.sagepub.com/doi/10.1177/17456916231214460 |
| **Ye, Jin, Xie, Zhang, Song (2025). Large Language Model Psychometrics: A Systematic Review.** arXiv:2505.08245 | Comprehensive systematic review covering Big Five / HEXACO / MBTI / Dark Triad / Schwartz / WVS / VSM / GLOBE / MFT / DIT / ETHICS — exactly Joyce's decision space. Companion repo: github.com/ValueByte-AI/Awesome-LLM-Psychometrics. **Use as the reading-graph backbone.** | https://arxiv.org/abs/2505.08245 |

### 3.2 Theory-as-input persona work (closest to Joyce's question)

| Citation | What they did | Theory framework |
|---|---|---|
| **Big5-Chat: Shaping LLM Personalities Through Training on Human-Grounded Data.** ACL 2025 (arXiv:2410.16491) | Trains LLMs on 100K dialogues annotated with Big Five trait expressions. SFT + DPO methods make output BFI scores correlate with input Big Five traits. | Big Five (input → output, training-time) |
| **Do LLMs Have Consistent Values?** ICLR 2025 | Tests whether Schwartz value structure emerges in LLM outputs; finds *organic* alignment (r=0.87–0.95) with Schwartz circumplex even without explicit value-prompting. | Schwartz Theory of Basic Values (probe) |
| **Bridging Values and Behavior: A Hierarchical Framework for Proactive Embodied Agents.** arXiv 2025 | Schwartz values as the cognitive layer organizing LLM agent action selection. | Schwartz (input → action, agentic) |
| **Cultural Alignment in Large Language Models** (Masoud et al.). arXiv:2309.12342, COLING 2025 | Hofstede CAT measures LLM alignment with US/China/Arab cultural dimensions across Llama-2/GPT-3.5/GPT-4. | Hofstede (probe) |
| **Break the Checkbox: Challenging Closed-Style Evaluations of Cultural Alignment in LLMs.** arXiv:2502.08045 | Critiques the "feed an LLM a multiple-choice cultural questionnaire and call that alignment" methodology. Important for any cultural-dim evaluation Joyce builds. | Methodological critique |
| **PersonaLLM** (Jiang et al.). arXiv:2305.02547, NAACL Findings 2024 | Big-Five-prompted LLMs complete BFI-44; report scores correlate with prompt traits with large effect sizes. | Big Five (prompt-time) |
| **LLMs Simulate Big Five Personality Traits: Further Evidence.** arXiv:2402.01765 | Cross-model BFI-44 results (Llama-2, GPT-4, Mixtral). | Big Five (cross-model probe) |

### 3.3 Synthetic-respondent / silicon-sampling literature (Park's neighborhood)

| Citation | What they did |
|---|---|
| **Argyle, Busby, Fulda, Gubler, Rytting, Wingate (2023). Out of One, Many: Using Language Models to Simulate Human Samples.** Political Analysis 31(3):337-351 | Demographic-priming → "silicon sample"; coined "algorithmic fidelity." Atheoretical baseline for any Joyce-comparison. |
| **Aher, Arriaga, Kalai (2023). Using Large Language Models to Simulate Multiple Humans.** ICML 2023 | Replicates Milgram, Ultimatum etc. with demographic-prompted LLMs. |
| **Bisbee, Clinton, Dorff, Kenkel, Larson (2024). Synthetic Replacements for Human Survey Data? The Perils of Large Language Models.** Political Analysis | **Critical warning paper**: GPT-4 demographic personas show distributional inconsistencies vs. real ANES respondents. Joyce must cite when defending method. |
| **Hewitt, Ashokkumar, Ghezae, Willer (2024). Predicting Results of Social Science Experiments Using Large Language Models.** Working paper / Stanford AI4PB. | GPT-4 simulates representative US samples → predicts treatment effects across 70 pre-registered experiments at r=0.85. Most direct precedent for Park-style "LLM-as-population." | https://www.treatmenteffect.app/ |
| **Manning, Zhu, Horton (2024). Automated Social Science: Language Models as Scientist and Subjects.** NBER WP 32381 / arXiv:2404.11794 | LLMs both *generate* and *test* social-science hypotheses via structural causal models. Methodological frontier. | https://www.nber.org/papers/w32381 |
| **Santurkar, Durmus, Ladhak, Lee, Liang, Hashimoto (2023). Whose Opinions Do Language Models Reflect?** arXiv:2303.17548 | Measures GPT-3.5 group-level alignment with Pew/ATP demographic strata. |
| **Horton (2023). Large Language Models as Simulated Economic Agents.** NBER WP | Stylized econ-rational-agent framing of LLMs. |

### 3.4 Critical / skeptic literature (must cite to be defensible)

| Citation | Why it matters |
|---|---|
| **Salecha, Ireland, Subrahmanian, Boyd, Kosinski (2024). Large language models display human-like social desirability biases in Big Five personality surveys.** PNAS Nexus 3(12):pgae533 | LLMs detect when they're being personality-tested and shift answers toward socially desirable poles by ~1 SD. **Critical for any BFI/values measurement Joyce takes from an LLM.** |
| **Ullman (2023). Large Language Models Fail on Trivial Alterations to Theory-of-Mind Tasks.** arXiv:2302.08399 | Companion to Kosinski's ToM-on-LLM paper; small adversarial perturbations break LLM ToM performance. |
| **Kosinski (2024). Evaluating Large Language Models in Theory-of-Mind Tasks.** PNAS 121(45):e2405460121 | The original "GPT-4 has 6yo-level ToM" paper; widely cited and contested. |
| **Hullman et al. — Validating LLM simulations as behavioral evidence.** Working paper (Northwestern MU Collective) | Methodological framework for what counts as valid evidence when LLM is the participant. |
| **Anthropic — Persona Vectors: Monitoring and Controlling Character Traits.** arXiv:2507.21509 | Mechanistic-interp angle: persona traits are encoded as directions in activation space; relevant if Joyce wants to ground "feature category contributes to persona representation" in something stronger than behavior alone. |

---

## 4. Prioritized reading list

Joyce should read in this order. Time estimates assume reading abstract + skimming methods/results, NOT full deep-read; the full read can come during writing.

### Tier 1 — must-read before locking theory (~6 hours)

These five anchor the methodological argument regardless of which theory Joyce locks:

1. **Pellert et al. (2024). AI Psychometrics.** Perspectives on Psychological Science. *(45 min)*
   *Why:* Establishes the legitimacy of doing psychometric profiling on LLMs across multiple frameworks at once. Directly relevant to Joyce's "compare 4-bin atheoretical vs theory-bin" comparison.
2. **Ye et al. (2025). LLM Psychometrics: A Systematic Review.** arXiv:2505.08245. *(60 min — read intro + theory taxonomy section + use Awesome-LLM-Psychometrics repo as reading-graph)*
   *Why:* Single most efficient way to map the field. Joyce can use the bibliography as a reading-graph hub.
3. **Binz et al. (2025). Centaur.** Nature. *(45 min)*
   *Why:* Establishes the methodological frontier for "LLM + cognitive-science data → human behavior prediction." Joyce's project is methodologically a smaller-scale cousin.
4. **Hewitt, Ashokkumar et al. (2024). Predicting social science experiments with LLMs.** *(45 min)*
   *Why:* Closest peer-comparison to Park: same outcome (predicting human responses), same input regime (LLM-as-respondent). The r=0.85 number is the benchmark Joyce should be ready to discuss.
5. **Salecha et al. (2024). Social desirability biases in BFI-on-LLM.** PNAS Nexus. *(30 min)*
   *Why:* The critical caveat for any psychometric LLM measurement. Joyce must address this in her threats-to-validity.

Total: ~3.5 hours. Add a re-read of Park 2024 (~2h) → **~5.5 hours total Tier 1**.

### Tier 2 — read when picking the theory (~3-5 hours, depends on choice)

Read the full set for the theory(ies) Joyce is seriously considering, plus 1-2 from each runner-up:

**If Inglehart-Welzel (Round-2 recommended):**
- Inglehart & Welzel (2005). *Modernization, Cultural Change, and Democracy.* Cambridge UP. *(read intro + ch. 2; ~2h)*
- Welzel (2013). *Freedom Rising: Human Empowerment and the Quest for Emancipation.* Cambridge UP. *(intro + ch. 1 for individual-level value indices; ~1.5h)*
- WVS Wave 7 documentation (~30 min skim).

**If Big Five (Round-2 recommended secondary):**
- Costa & McCrae (1992). NEO-PI-R manual selections. *(skim; ~1h)*
- John, Naumann, Soto (2008). Handbook chapter. *(~1.5h — best single reference)*
- Big5-Chat paper (arXiv:2410.16491). *(~45 min)*
- PersonaLLM (arXiv:2305.02547) + Salecha 2024. *(already in Tier 1)*

**If MFT (Round-1 §2):**
- Graham, Haidt, Nosek (2009). *(60 min)*
- Atari et al. (2023). *Morality beyond the WEIRD.* JPSP. *(60 min — for cross-cultural pedigree, NOT as LLM-applied work)*

**If Schwartz (Round-1 §3):**
- Schwartz (2012). Online Readings overview. *(30 min)*
- Cieciuch & Schwartz (2012). PVQ-40 paper. *(30 min)*
- "Do LLMs Have Consistent Values?" ICLR 2025. *(60 min — LLM-applied)*

### Tier 3 — context / discussion-section material (~2-3 hours)

- Hagendorff "Machine Psychology" arXiv:2303.13988 (skim — useful framing language for related work)
- Binz & Schulz (2023). *Using cognitive psychology to understand GPT-3.* PNAS. (skim — methodological precedent)
- Argyle et al. (2023). *Out of One, Many.* Political Analysis. (skim)
- Anthropic persona-vectors paper (skim — for "what's happening inside the model" framing)
- Ullman (2023). LLM-fails-ToM-on-perturbations. (15 min — caveat literature)

### Tier 4 — only if Phase 2 / cross-cultural extension is on the table

- Hofstede 2010 Cultures and Organizations.
- Cultural Alignment in LLMs (arXiv:2309.12342) + "Break the Checkbox" (arXiv:2502.08045).
- Theory of Planned Behavior (Ajzen 1991, 2020).
- Self-Determination Theory (Deci & Ryan 2000).

---

## 5. Methodological argument Joyce can now make

After reading Tier 1, Joyce can pre-register the following framing:

> *Recent work has established a research mode in which psychometric instruments and cognitive-science task batteries are applied to LLMs as diagnostic and behavioral probes (Binz & Schulz, 2023, PNAS; Hagendorff et al., 2023; Pellert et al., 2024, Perspectives on Psychological Science; Binz et al., 2025, Nature; Ye et al., 2025). Within the synthetic-respondent / silicon-sampling line specifically (Argyle et al., 2023; Hewitt et al., 2024; Park et al., 2024-2025), prior work has used demographic priming or raw interview transcripts as persona-construction inputs, and post-hoc psychometric instruments to characterize the resulting model behavior. To our knowledge, no published work systematically applies a pre-registered theoretical framework — Inglehart-Welzel cultural values / Schwartz Theory of Basic Values / Moral Foundations Theory / Big Five / etc. — to organize the input features of an LLM persona, and empirically compares that theoretical organization to an atheoretical baseline. Phase 1c proposes to fill that gap.*

This positions the contribution as a methodological extension of an established research mode, rather than a one-off engineering choice.

---

## 6. Open questions for Bayati (suggest raising at next meeting)

1. **Theory choice steer.** Bayati's discipline (operations / management science / behavioral econ) tends to value (a) parsimony, (b) symmetric input/output, (c) econ-friendly value frameworks. Does he have a preference between Inglehart-Welzel (cross-cultural values, 4 quadrants), Schwartz (10 values / 4 quadrants), MFT (5-6 foundations), or Big Five (5 traits)?
2. **Symmetric input/output design.** If Phase 2's outcomes are BFI + behavioral games, would using Big Five as the Phase 1 *input* organization create an unfair advantage at the LLM-eval stage, or is it methodologically fine because GSS is the held-out outcome?
3. **Multi-theory pre-registration.** OSF allows pre-registering multiple secondary analyses with multiplicity correction. Is Bayati comfortable pre-registering 4-bin (atheoretical) + Inglehart-Welzel + Big Five LOOs as a *family*, with Holm-Bonferroni applied across the family? This buys insurance against a single bad theory choice and enables a "which framework predicts best" comparison as an extra contribution.
4. **Validity / threat literature.** Salecha 2024 (social desirability bias in BFI-on-LLM) implies LLM persona BFI scores are inflated. Does this matter for Joyce's design, where BFI is an *outcome* in Phase 2 only, not a feature in Phase 1? Probably not — but worth raising.

---

## 7. What Round-2 did NOT cover

- **Cross-cultural extension** of Phase 1 (single-country GSS doesn't need Hofstede).
- **Behavioral economics frameworks** (Prospect Theory, bounded rationality) — these are Phase 2 territory.
- **Predictive processing / Bayesian theory of mind** (Tenenbaum, Friston, Goodman) — too theoretical for a Phase-1-style empirical claim; cite in discussion if relevant.
- **Identity-based theories** (Tajfel social identity, Markus & Kitayama self-construal) — partially overlaps with Inglehart-Welzel's individualism/survival axis; defer.
- **Searches in Chinese-language psychology literature** — the panel of 4 cheap LLMs is China-trained (Qwen / DeepSeek / MiniMax / Kimi), so Chinese-language values frameworks (e.g., Schwartz extensions adapted by Yu et al.) might be relevant for understanding model behavior. Joyce should consider this when interpreting cross-model agreement % from the panel.

---

## 8. ⚠️ Honest disclaimer (read before citing anything above)

All arXiv IDs, DOIs, and paper titles in §3 were retrieved by web search on 2026-05-07. They are not LLM-recall-only (which is the failure mode Round-1 §11 warned about). However:
- Author lists are summarized from search snippets — verify full author orderings before pre-reg.
- Page numbers / volume numbers may have transcription errors — verify from publisher.
- Year of publication is reliable for most; but pre-print → final-publication can shift.
- For Inglehart-Welzel specifically: §2.2 citations were verified 2026-05-10 night via web cross-check against publisher pages (Cambridge UP, Princeton UP) + Wikipedia + World Values Survey site (per OSF §17 item ④). Verification added the 2010 Beugelsdijk & Welzel single-factor caveat to §2.2 Risks. **For Hofstede specifically: §2.3 citations are still textbook-reference recall; verify independently before any Discussion-section use.**

Joyce: before any of these citations enter the OSF pre-registration or paper, retrieve the actual paper or DOI page and confirm.

---

**Companion file:** `archive/theory_review.md` (Round 1, scaffold for the original 4 candidates; do not delete — Round 2 is additive).
