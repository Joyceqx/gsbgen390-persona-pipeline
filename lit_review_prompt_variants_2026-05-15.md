# Prompt-Variant Literature Review for GSBGEN390 Phase 1A
**2026-05-15 | for Joyce Yu, GSBGEN390 thesis (adv. M. Bayati)**

---

## TL;DR

- **The current baseline ("P0") already implements Park v2's surveys-only format** (2nd person, structured bin headers, variable-label : value-label lines, anti-refusal trailer).
- **Voice is genuinely contested in the literature.** Argyle 2023 uses **1st-person prose** ("I am 33 years old. I am a man."), Aher 2023 uses **3rd-person named** ("Ms. Huang decided to..."), Park/Hu/Bisbee/baseline use **2nd person**. Wang et al. 2025 — the only head-to-head ablation — finds **interview-style Q&A + name-based priming** beats both direct 2nd-person and 3rd-person on stereotyping *and* opinion-alignment.
- **Plain chain-of-thought does NOT help persona simulation; structured psychological-scaffold rationales DO.** Sun et al. 2025 (PB&J, arXiv:2504.17993): Demographics+Judgments+CoT = 49.17% on OpinionQA vs 49.63% baseline (no gain), while Primal-World-Beliefs scaffold = **+4.8 pp, p<0.05**. Park v2's "expert reflection" module is conceptually the same finding — scaffold beats free reasoning. **Do not waste a sweep slot on plain CoT.**
- **Persona variables explain ~1.4-10.6% of variance on most subjective NLP tasks, but 71.9% on ANES** (Hu & Collier 2024). GSS political attitudes sit in the high-explanatory regime, so persona prompting is worth real effort — but reordering/reparagraphing within a bin had "little variation" in their tests, so within-bin alphabetical order is not a meaningful lever for Joyce.
- **Recommended sweep:** P0 (baseline), P2 (Wang interview Q&A), P3 (PB&J Schwartz/Primal scaffold), and optionally P1 (Argyle 1st-person prose) or P4 (Salecha "remove the GSS brand name" ablation).

---

## 1. Per-paper extraction

### 1.1 Park et al. 2024 v2 (arXiv:2411.10109)

- **Persona representation.** Two conditions: (a) "interview" = full ~6,491-word AVP-style transcript dumped into context; (b) **"surveys-only"** = saturated standardized batteries (GSS attitudes + full BFI-44) as label:value lines. Verbatim surveys-only template not retrievable from abstract; Joyce's `gss_pipeline.py` baseline mirrors it.
- **Voice/person.** **2nd person** ("You are a person who completed...").
- **Item presentation.** **One item per LLM call** for the held-out GSS attitude eval. No batching.
- **Refusal/format handling.** Single-integer code requested at item time. Minimal anti-refusal scaffolding needed for GPT-4o-class models once the persona context is coherent.
- **Variant ablations.** Park's ablation is across *conditions* (demographics/description/interview/surveys/combined), not prompt-form within a condition. Headline: surveys-only ≈ interview on **GSS attitudes** (0.82 vs 0.83) but lags by 0.15 on BFI-44, 0.28 on behavioral games. **Park also introduces an "expert reflection" two-stage module**: classify which of four domain experts is relevant, then pull that expert's reflection on top of the persona context (GPT-4o). This is the closest thing in the paper to a literature-validated scaffold.
- **Source.** arXiv:2411.10109v2; HAI press release.

### 1.2 Argyle, Busby, Fulda, Gubler, Rytting, Wingate 2023 — "Out of One, Many" (Political Analysis 31(3))

- **Persona representation.** ~11 ANES 2016 sociodemographic + political attributes rendered as 1st-person prose. Verbatim canonical example: *"Racially, I am black. I like to discuss politics with my family and friends. Ideologically, I am strongly liberal. Politically, I am a democrat. I do not attend church. I am 33 years old. I am a man. I am highly interested in politics."*
- **Voice/person.** **1st person.** No bins; one paragraph.
- **Item presentation.** Conditioning prompt + survey question as continuation. They extract **token logprob over option tokens** (e.g., "Trump" vs "Clinton") — GPT-3-era logprob-access design.
- **Refusal/format handling.** Sidestepped by logprob extraction.
- **Variant ablations.** None of voice/structure variants; focus is on demographic-bias alignment at population scale.
- **LOO note.** Pure prose blends features — **incompatible with Joyce's bin-drop LOO unless bins are kept as separable paragraphs** (see P1 in §3).
- **Source.** arXiv:2209.06899; Pol. Analysis 31(3): 337-351.

### 1.3 Aher, Arriaga, Kalai 2023 — "Turing Experiments" (ICML 2023)

- **Persona representation.** **Minimal:** title + surname only (Mr./Ms./Mx. + Census-sourced surname encoding race+gender). Persona is *implicit* in the name.
- **Voice/person.** **3rd-person named narrative.** Verbatim examples:
  - Ultimatum: *"In the following scenario, Ms. Huang had to decide whether to accept or reject the proposal. Scenario: Mr. Wagner is given $10... Mr. Wagner takes $6 for himself and offers Ms. Huang $4. Answer: Ms. Huang decides to"*
  - Wisdom of Crowds: *"Ms. Huang was asked the following question... Ms. Huang's answer (integer):"*
- **Item presentation.** One scenario per call; scenario is self-contained narrative.
- **Refusal/format handling.** Optimize "validity rate" (parseable-answer fraction) before running hypothesis tests; temperature=1, top_p=1.
- **Variant ablations.** Stimulus-variation sensitivity tests, not prompt-form. They explicitly flag LM "high sensitivity to wording."
- **Source.** arXiv:2208.10264; PMLR v202.

### 1.4 Horton, Filippas, Manning 2023 — "Homo Silicus" (NBER w31122)

- **Persona representation.** Single-clause theory-grounded labels: *"You are a libertarian"*, *"You are a fairness agent"*, or behavioral-econ endowments ("Your marginal cost is 15 tokens").
- **Voice/person.** **2nd person.**
- **Item presentation.** Decision scenario stated; single-shot answer.
- **Variant ablations.** None on prompt design.
- **Relevance for Joyce.** Not directly imitable — Horton's personas are too sparse for 50+ GSS variables. Useful only as a citation for "label-based ideological priming" but a summary-label variant would bake in cross-bin features (LOO-incompatible). **Skip for sweep.**
- **Source.** NBER w31122; arXiv:2301.07543.

### 1.5 Bisbee, Clinton, Dorff, Kenkel, Larson 2024 — "Synthetic Replacements?" (Political Analysis 32(4))

- **Persona representation.** Demographics + party + ideology as 2nd-person persona prompt to ChatGPT-3.5; ask for feeling-thermometer ratings (0-100) of 11 sociopolitical groups.
- **Voice/person.** 2nd person.
- **Item presentation.** Mostly batched (all 11 in one response).
- **Refusal/format handling.** ChatGPT-3.5 sometimes refuses; re-prompt until numeric answer is given.
- **Variant ablations.** **Critical finding:** "the distribution of synthetic responses varies with minor changes in prompt wording and yields significantly different results over a 3-month period." Bisbee explicitly tested paraphrases and found high sensitivity. *Motivates Joyce's whole sweep* but also implies any single run under-estimates true uncertainty. **Recommend ≥2 paraphrases per variant if budget allows.**
- **Source.** Cambridge Pol. Analysis 32(4): 401-416, 2024.

### 1.6 Hu & Collier 2024 — "Quantifying the Persona Effect" (ACL 2024)

- **Persona representation.** Demographic variables in 2nd-person natural-language declarations prepended to task.
- **Voice/person.** **2nd person.**
- **Item presentation.** Single item per call; next-token logprob over option tokens.
- **Variant ablations.** **Key results:** persona variables explain **<10% variance** on subjective NLP datasets (marginal R² 1.4-10.6%), but **71.9% on ANES**. They tested **reordering** and **reparagraphing** of variables — found **"little variation."** With 70B + persona prompting, they recover 81% of ground-truth-trained linear regression variance.
- **Relevance.** Confirms persona prompting is worth doing on polarized political items (which GSS attitudes largely are). Also confirms within-bin order is not a productive lever — focus structure and voice instead.
- **Source.** arXiv:2402.10811v2; ACL 2024.

### 1.7 Salecha et al. 2024 — "LLMs Display Social-Desirability Biases in BFI" (PNAS Nexus)

- **Persona representation.** No persona — LLM answers BFI for itself.
- **Variant ablations.** GPT-4 shifts ~**1.20 SD** toward socially desirable answers when it can detect that BFI items are being administered. Order randomization and paraphrasing did NOT eliminate it; reverse coding only reduced.
- **Relevance for Joyce.** *Negative result for one specific design choice.* Joyce's baseline names "the 2024 General Social Survey" in the preamble; Salecha predicts this could inflate social-desirability bias on items like POLVIEWS, civil-lib triad, RACMAR, FEPOL. Tested as P4 below.
- **Source.** PNAS Nexus 3(12):pgae533, 2024.

### 1.8 Wang, Pyatkin, Bhagavatula, Choi 2025 — "The Prompt Makes the Person(a)" (Findings EMNLP 2025)

**Most actionable paper for Joyce's sweep.** Direct head-to-head ablation of three role-adoption × three demographic-priming strategies on 15 intersectional demographic groups × 5 open-source LLMs × 100 OpinionQA questions.

- **Voice tested head-to-head:**
  - Direct 2nd: *"You are a Hispanic woman"* / *"Act as a Hispanic woman"*
  - 3rd-person hypothetical: *"Think of a Hispanic woman"*
  - **Interview Q&A:** *"Interviewer: What is your race? Interviewee: My race is Black."*
- **Priming tested head-to-head:** name-based / explicit / structured-categorical.
- **Winners:** **interview-style Q&A + name-based priming.** Lower stereotyping (marked word counts), higher semantic diversity, reduced disparity coefficients across demographic groups (Table 1: −5.9 to −11.4 with name-based vs −5.3 to −5.9 for interview format alone), better opinion alignment on OpinionQA.
- **Surprise:** smaller models (OLMo-2-7B) outperformed Llama-3.3-70B.
- **LOO-compat note.** Wang's prompts have only a few demographic facets. **Bin-grouping interview turns** (proposed P2) extends Wang's design to Joyce's 50+ variable setting while preserving LOO compatibility.
- **Source.** arXiv:2507.16076v2; Findings EMNLP 2025.

### 1.9 Sun, Sap et al. 2025 — PB&J: "Improving LLM Personas via Rationalization with Psychological Scaffolds" (arXiv:2504.17993)

**The CoT-vs-scaffold answer.** Two-stage: (1) generate a rationale conditioned on a **psychological scaffold** (Big Five OCEAN / Schwartz Values / Primal World Beliefs / Experiences); (2) feed [demographics + judgments + rationale] into response prediction.

- **OpinionQA (GPT-4) results:**
  - Demographics + Judgments baseline: **49.63%**
  - + plain **CoT**: **49.17%** (NO GAIN over baseline)
  - + **PB&J Primal Beliefs scaffold**: **54.43%** (+4.8 pp, p<0.05)
- **MovieLens:** +5.1 pp with Schwartz Values scaffold.
- **Rationale length doesn't drive gains** (r=0.03 with accuracy); structure does. Human-written rationales (~40 tokens) beat longer CoT (60-124 tokens).
- **Relevance.** Directly answers "should we try CoT?" — NO. Points to scaffolded rationale (especially Schwartz / Primal Beliefs) as the productive direction. Coheres with Park v2's expert-reflection module.
- **LOO note.** If the rationale is generated *only* from the psychological bin, dropping that bin cleanly removes both items and rationale (LOO-Ψ). See P3.
- **Source.** arXiv:2504.17993v2.

### 1.10 Convergent insight across Park v2 + PB&J

Both papers independently report that a *structured intermediate step* (Park's expert-reflection / PB&J's scaffolded rationale) outperforms either plain persona-listing OR free-form CoT. This is the strongest meta-finding in the field on prompt-form design and anchors P3.

### 1.11 Papers searched but not deeply extracted

- **Boelaert et al. 2025 "Machine Bias"** (Sociol. Methods & Research): LLMs exhibit "strong bias with low variance per topic, randomly varying across topics" — reinforces Bisbee's sensitivity concern; no new prompt-design recommendation.
- **Anthis et al. 2025 "LLM Social Simulations Are a Promising Research Method"** (arXiv:2504.02234): synthesis position paper; no ablation.
- **GGSS Personas (arXiv:2511.21722)**: German ALLBUS analog; independently arrived at a "core socio-demographic block + TOP-k extensible block" 2-block layout similar to Joyce's 4-bin layout. Worth citing as parallel work.
- **PersonaLLM (Jiang et al., NAACL Findings 2024)**: tests LLM persona expression of traits; off-topic for predict-others.
- **Santurkar et al. 2023 (OpinionQA)**: dataset many later papers (Hu, PB&J, Wang) use. Joyce's analog is the 12-item GSS primary eval.

---

## 2. Cross-paper synthesis

### 2.1 Key findings about what reliably works / fails

1. **Persona-variable *choice* >> persona-variable *order***. Hu & Collier find reordering and reparagraphing produce "little variation." Joyce's alphabetical-within-bin order is *not* worth burning a sweep slot on.
2. **Interview-style Q&A structure beats both flat 2nd-person and 3rd-person on opinion alignment** (Wang 2025, head-to-head, 5 LLMs × 15 groups × 100 questions). The cleanest ablation in the field.
3. **Plain CoT does NOT help persona simulation; structured psychological-scaffold rationales DO** (PB&J: CoT = 0 gain vs +4.8 pp scaffold). Park's expert-reflection module is conceptually the same finding.
4. **Naming a recognizable instrument in the preamble risks inflating social-desirability bias** (Salecha: ~1.2 SD shift on GPT-4 when BFI-administration is detectable). Joyce's baseline names the GSS — ablate downward, not upward.
5. **Surveys-only conditioning is near-ceiling against interview on GSS attitudes** (Park: 0.82 vs 0.83). Realistic effect-size expectations for prompt-form deltas: r in the .02-.10 range per variant (Funder & Ozer 2019 "small but consequential" rubric). Plan power accordingly.

### 2.2 Tensions / disagreements

- **Voice: 1st vs 2nd vs 3rd.** Argyle (1st), Park/Hu/Horton/Bisbee/baseline (2nd), Aher (3rd). Wang resolves direct-2nd vs 3rd-hypothetical in favor of interview-Q&A, but **no paper directly compares 1st-person vs 2nd-person in a controlled sweep on a survey-prediction task**. Joyce's sweep can illuminate this gap.
- **Prose vs structured key-value.** Argyle's prose reads naturally and is per-respondent unique; Park/baseline structured format is machine-friendly and supports LOO. No published head-to-head on a *survey-prediction* outcome. Wang's interview-Q&A is the closest middle ground.
- **Batched vs one-per-call.** Bisbee batches (and shows high sensitivity). Park/Hu/Wang/Argyle/Aher single-item. **Stay one-per-call** — don't waste a sweep slot.
- **CoT helps in general LLM tasks but not for persona-survey prediction.** This is itself a citable finding; **do not include plain CoT** as a sweep variant.

### 2.3 Gaps the literature does NOT answer that Joyce's sweep could illuminate

1. **1st-person vs 2nd-person head-to-head on a structured-bin GSS-attitudes task.** Argyle (1st-prose) vs Park/baseline (2nd-structured) have never been controlled-compared.
2. **Whether Wang's interview-Q&A format ports to a 50+ variable persona** without dilution. Wang's personas had only a few facets.
3. **Whether a Schwartz/Primal-Beliefs scaffold adds value on top of an attitudinal bin that already expresses values** — the scaffold may be redundant or may compress noisy items into a usable axis. LOO drop of the psychological bin gives a clean test.
4. **Whether removing the "GSS" brand name from the preamble reduces social-desirability bias** on the politically sensitive subset of items. Salecha-predicted but never tested in a persona-prediction (not self-administration) setting.

---

## 3. Proposed prompt candidates (literature-grounded)

### P0 — Baseline (current pipeline)

Joyce's existing `build_persona_prompt()` in `/Users/joyce/Developer/gsbgen390/gss_pipeline.py` lines 159-287. Structured 4-bin, 2nd-person, alphabetical-within-bin, "You are a person who completed the 2024 GSS" preamble, anti-refusal trailer. **Already implements Park v2 surveys-only condition.** Reference point.

### P1 — Argyle-style 1st-person bin-prose

**Skeleton.**
```
PREAMBLE (1st person):
I am a respondent of the 2024 General Social Survey. Below is who I am,
organized into four parts: who I am demographically, what I do, how I think,
and what I believe. I will answer further survey questions in character, in
the exact format requested. I will commit to a single answer. I will not
hedge, refuse, or break character.

## ABOUT ME — DEMOGRAPHICS
I am 45 years old. I am female. I am married. I have a bachelor's degree.
I live in the Pacific region. (... one short clause per variable,
alphabetical within bin, comma-joined into 2-3 sentences ...)

## ABOUT ME — BEHAVIORS
I attend religious services about once a month. I watch about 2 hours of TV
per day. (...)

## ABOUT ME — PSYCHOLOGICAL DISPOSITIONS
(... 1st-person clauses ...)

## ABOUT ME — ATTITUDES
(... 1st-person clauses ...)

TRAILER:
I will now be asked one or more further GSS questions. I will answer in
character, in the exact format requested.
```

- **Grounding.** Argyle, Busby, Fulda et al. 2023; first-person framing shown to capture demographically-correlated bias on ANES voting prediction. Extended to a bin structure for LOO-compat.
- **Prior hypothesis.** First-person may activate stronger self-modeling in the LLM. On polarized political GSS items (POLVIEWS, abortion, racial-inequality items) — the high-explanatory-power regime per Hu & Collier — 1st-person may help the model commit decisively rather than averaging.
- **LOO compatibility.** ✅ Each bin remains an isolable block; dropping a bin removes a section.
- **Sensitivity-eval (AUDIT-D) compatibility.** ✅ Per-item exclusion can drop individual clauses; needs templating care.
- **Risks.** Prose generation requires variable-value-label → natural-clause templating that's error-prone for some GSS value labels ("I am Never married" needs rewrite to "I have never been married"). Pre-test on a handful of respondents before sweep.

### P2 — Wang-style interview Q&A (bin-grouped turns) [RECOMMENDED]

**Skeleton.**
```
PREAMBLE:
The following is an interview transcript with a respondent of the 2024
General Social Survey. The respondent answered questions about themselves,
their behaviors, their psychological dispositions, and their attitudes.
You will later be asked to continue answering in the voice of this same
respondent, in the exact format requested. You will commit to a single
answer per question and will not hedge or refuse.

## DEMOGRAPHIC BACKGROUND
Interviewer: How old are you?
Respondent: I am 45.
Interviewer: What is your sex?
Respondent: Female.
Interviewer: What is your marital status?
Respondent: Married.
(... one Q-A pair per variable, alphabetical within bin ...)

## BEHAVIORS
Interviewer: How often do you attend religious services?
Respondent: About once a month.
(...)

## PSYCHOLOGICAL DISPOSITIONS
(...)

## ATTITUDES
(...)

TRAILER:
Interviewer: I will now ask you a few more questions. Please answer in
the same format I request for each.
```

- **Grounding.** Wang, Pyatkin, Bhagavatula, Choi 2025 (Findings EMNLP 2025). Their head-to-head ablation found interview Q&A beat direct 2nd-person and 3rd-person on both stereotyping and opinion-alignment metrics across 5 LLMs and 15 demographic groups on OpinionQA. Also coheres with Park v2's interview condition being the strongest overall — suggesting part of the lift may be format-driven, not content-driven.
- **Prior hypothesis.** Q&A scaffolding mimics the dialogue format LLMs saw during instruction-tuning, forcing the model to predict an "answer" rather than re-state a "fact." If even part of Park's interview→surveys gap is format-driven, P2 should narrow it on GSS attitudes.
- **LOO compatibility.** ✅ Bin-grouped turns; dropping a bin drops the block.
- **Sensitivity-eval compatibility.** ✅ Per-item exclusion drops one Q-A pair.
- **Risks.** Longer prompt (~1.8× token count vs P0). Wang's panel was 7B-70B open models; Joyce's 4-LLM panel includes proprietary models that may respond differently. Joyce's question-asking module already uses turn-style at item time — make sure persona-prompt Interviewer ≠ item-prompt Interviewer to avoid confusion (or deliberately unify them, which would be even more on-format).

### P3 — PB&J psychological-scaffold rationale (Ψ-bin-only, LOO-safe) [RECOMMENDED]

**Skeleton.**
```
[Same PREAMBLE as P0 — 2nd person, structured.]

## YOUR DEMOGRAPHICS
- age: 45
- sex: female
(...)

## YOUR BEHAVIORS
(...)

## YOUR PSYCHOLOGICAL DISPOSITIONS
- (... the psychological-bin variables ...)

### YOUR DISPOSITIONAL SUMMARY (Schwartz value-axes)
Based on your psychological dispositions above, the following short summary
characterizes your underlying value orientation:
[1-2 sentence model-generated rationale conditioned ONLY on the psychological
bin, using Schwartz human values OR primal world beliefs as scaffold].

## YOUR ATTITUDES
(...)

[TRAILER as in P0]
```

- **Grounding.** Sun, Sap et al. 2025 (PB&J, arXiv:2504.17993). +4.8 pp on OpinionQA with Primal Beliefs scaffold; +5.1 pp on MovieLens with Schwartz Values scaffold. Resonates with Park v2's expert-reflection module — both are intermediate-structure scaffolds, not free CoT.
- **Prior hypothesis.** The psychological bin's raw items are noisy individual indicators; a value-axis scaffold compresses them into a one-axis summary the LLM uses more directly when predicting downstream attitudinal items (POLVIEWS, abortion, gender-role-attitudes). May particularly help on items linked to moral foundations (Haidt-Graham 2007).
- **LOO compatibility.** ✅ **Provided the rationale is generated conditioned ONLY on the psychological bin.** Then dropping Ψ cleanly removes both variables and rationale; dropping any other bin leaves the rationale intact.
- **AUDIT-D compatibility.** ⚠️ **Caveat.** Per-item exclusion within the psychological bin would change the rationale. Cleanest fix: generate the rationale once (full bin) and freeze it; document the mild AUDIT-D contamination. Or skip AUDIT-D for P3 only. **Flag for Bayati conversation.**
- **Risks.** Extra pre-pass adds latency + cost (~1 extra LLM call per respondent per pre-pass). Cap rationale at ~30 tokens (PB&J shows length doesn't drive accuracy). If the rationale model is the same as the eval model, the gain may evaporate — PB&J protocol uses cross-model rationale + prediction. **Recommend rationale generator = a fixed model (e.g., GPT-4o)** regardless of eval-panel model.

### P4 (optional) — Surveys-only with GSS brand name removed (Salecha ablation)

**Skeleton.** Identical to P0 *except* the preamble loses "the 2024 General Social Survey":

```
You are a person whose background, behaviors, dispositions, and views are
described below. Stay in character as this respondent throughout. Below is
what you have shared, organized by topic. Always commit to a single answer
in the requested format. No "it depends" hedges, no refusals, no
qualifications about being an AI.

[bins as before]
[trailer: "additional questions" rather than "additional GSS questions"]
```

- **Grounding.** Salecha et al. 2024 (PNAS Nexus): naming a recognizable instrument inflates social-desirability bias by ~1.2 SD on GPT-4. Joyce's baseline names the GSS twice.
- **Prior hypothesis.** Salecha-predicted improvement on socially-sensitive items (POLVIEWS extremes, civil-lib items, RACMAR, FEPOL). Item-level decomposition could surface this even if average MAE is unchanged.
- **LOO / AUDIT-D compatibility.** ✅ trivially.
- **Risks.** Park-comparability suffers slightly (Park does name the GSS). Acceptable trade since P0 retains Park's framing. **Single-knob ablation** — if Joyce wants only 3 variants, this is the one to drop.

### Summary table

| Variant | Voice | Structure | Extra scaffold | Cite | LOO-safe | AUDIT-D-safe | New cost |
|---|---|---|---|---|---|---|---|
| P0 baseline | 2nd | 4-bin key:value | none | Park v2 | ✅ | ✅ | — |
| P1 1st-person prose | 1st | 4-bin prose clauses | none | Argyle 2023 | ✅ | ✅ (regex) | template effort |
| P2 interview Q&A | 2nd (dialogue) | 4-bin Q-A turns | none | Wang 2025 | ✅ | ✅ | ~1.8× tokens |
| P3 PB&J scaffold | 2nd | P0 + Ψ-rationale | Schwartz or Primal Beliefs | Sun 2025 | ✅ (Ψ-only) | ⚠️ caveat | +1 LLM pre-pass |
| P4 (opt) no-instrument-name | 2nd | as P0 minus "GSS" | none | Salecha 2024 | ✅ | ✅ | — |

**Recommended sweep (3 slots):** P0, P2, P3. Add P1 as a fourth if budget allows (it's the only variant that probes the 1st-vs-2nd voice gap, which is a genuine literature hole). Add P4 only if Joyce also wants item-level social-desirability decomposition.

---

## 4. Citations (full)

- Aher, G., Arriaga, R. I., & Kalai, A. T. (2023). *Using Large Language Models to Simulate Multiple Humans and Replicate Human Subject Studies.* ICML 2023. arXiv:2208.10264. https://proceedings.mlr.press/v202/aher23a.html
- Anthis, J. R., Liu, R., Richardson, S. M., Kozlowski, A. C., Koch, B., Evans, J., Brynjolfsson, E., & Bernstein, M. (2025). *LLM Social Simulations Are a Promising Research Method.* arXiv:2504.02234.
- Argyle, L. P., Busby, E. C., Fulda, N., Gubler, J. R., Rytting, C., & Wingate, D. (2023). *Out of One, Many: Using Language Models to Simulate Human Samples.* Political Analysis 31(3): 337-351. DOI: 10.1017/pan.2023.2. arXiv:2209.06899.
- Bisbee, J., Clinton, J. D., Dorff, C., Kenkel, B., & Larson, J. M. (2024). *Synthetic Replacements for Human Survey Data? The Perils of Large Language Models.* Political Analysis 32(4): 401-416.
- Boelaert, J., Coavoux, S., Ollion, É., Petev, I., & Präg, P. (2025). *Machine Bias: How Do Generative Language Models Answer Opinion Polls?* Sociological Methods & Research, online first. DOI: 10.1177/00491241251330582.
- Funder, D. C., & Ozer, D. J. (2019). *Evaluating effect sizes in psychological research: Sense and nonsense.* AMPPS 2(2): 156-168.
- Haidt, J., & Graham, J. (2007). *When morality opposes justice.* Social Justice Research 20(1): 98-116.
- Horton, J. J., Filippas, A., & Manning, B. S. (2023). *Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?* NBER WP w31122. arXiv:2301.07543.
- Hu, T., & Collier, N. (2024). *Quantifying the Persona Effect in LLM Simulations.* Proceedings of ACL 2024 (Long). arXiv:2402.10811. https://aclanthology.org/2024.acl-long.554/
- Park, J. S., Zou, C. Q., Shaw, A., Hill, B. M., Cai, C., Morris, M. R., Willer, R., Liang, P., & Bernstein, M. S. (2024). *Generative Agent Simulations of 1,000 People* (v2 retitled *LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals*). arXiv:2411.10109v2.
- Salecha, A., Ireland, M. E., Subrahmanya, S., Sedoc, J., Ungar, L. H., & Eichstaedt, J. C. (2024). *Large language models display human-like social desirability biases in Big Five personality surveys.* PNAS Nexus 3(12): pgae533.
- Santurkar, S., Durmus, E., Ladhak, F., Lee, C., Liang, P., & Hashimoto, T. (2023). *Whose Opinions Do Language Models Reflect?* ICML 2023; arXiv:2303.17548. (OpinionQA dataset.)
- Schwartz, S. H. (1992). *Universals in the content and structure of values.* Adv. Exp. Soc. Psych. 25: 1-65.
- Sun, J., Bhattacharjee, A., Hwang, M., Sap, M., et al. (2025). *Improving LLM Personas via Rationalization with Psychological Scaffolds.* arXiv:2504.17993v2.
- Wang, X., Pyatkin, V., Bhagavatula, C., & Choi, Y. (2025). *The Prompt Makes the Person(a): A Systematic Evaluation of Sociodemographic Persona Prompting for Large Language Models.* Findings of EMNLP 2025. arXiv:2507.16076v2. https://aclanthology.org/2025.findings-emnlp.1261/
