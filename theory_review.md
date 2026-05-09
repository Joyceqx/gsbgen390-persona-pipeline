# Theory-driven feature-engineering: literature review starter

> ⚠️ **Status update 2026-05-09 (lean-design lock)**: this file was originally written under the assumption that one theory would be **locked** and that locked theory would drive a confirmatory theory-bin LOO secondary family. **Under the 2026-05-09 lean lock, that plan was removed.** Theory framing now enters the Discussion section only as interpretive secondary analysis across 6 candidate frameworks — see `theory_interpretation_guide.md` for the live spec. **§6 / §8 / §9 of this file (which still talk about "lock §8 before Phase 1a runs", building `gss_theory_taxonomy.json`, and OSF amendment) are stale relative to the lean lock.** They are preserved for historical context but do NOT describe the current plan. Joyce's literature review continues as Discussion-writing input.

**Author:** Joyce Yu (literature review owner)
**Created:** 2026-05-06 by collaborating Claude session (scaffold only — Joyce owns the actual review)
**Status under lean lock**: informational; not gating Phase 1a or OSF.
**Locked theory:** N/A under lean lock — no single theory is selected; 6 candidates are discussed in `theory_interpretation_guide.md`.
**See also:** `theory_review_round2.md` (2026-05-07) — adds 5 cog-sci/behavioral-science candidates Round-1 missed (Big Five/HEXACO, Inglehart-Welzel, Hofstede, Theory of Planned Behavior, Self-Determination, Dual-Process), verified 2024-2026 LLM-applied work, and a tiered reading list. Read Round 2 alongside this file for full context; for the live design see `theory_interpretation_guide.md`.

This document is a structured starter for the literature review committed to in `gss_phase1_design.md` §13. The goal: pick ONE theoretical framework that maps cleanly onto GSS-attitudinal items, and lock the GSS-variable → theory-cluster mapping in `gss_theory_taxonomy.json` before Phase 1a runs.

The four candidate theories below are the strongest fits I can identify for GSS-attitude prediction. Each section gives the foundational citation, scope, fit-to-GSS, and a partial mapping. Joyce will read the original sources, decide, and lock the choice.

---

## 1. Why a theory-driven layer at all

The current 4-bin taxonomy (demographic / behavioral / psychological / attitudinal) is atheoretical — a sorting convention, not derived from any cognitive or behavioral-science theory. Adding a theoretically-grounded grouping turns the LOO ablation from an engineering result ("category X contributes most variance") into a falsifiable psychological claim ("the persona-internal representation aligns with theoretical construct Y").

**For an atomic-paper-quality thesis, this is the strongest single move available.** The paper goes from:
> *"GSS features predict GSS attitudes via LLM personas; demographic features contribute least, attitudinal features contribute most"*

to:
> *"LLM persona-internal feature representation aligns with {Moral Foundations Theory / Schwartz Values / Bourdieu's capitals}, with the {care-harm / universalism / cultural-capital} cluster providing the largest predictive contribution. This {confirms / partially refutes} {theory}'s explanatory scope when extended to the LLM persona-construction setting."*

The theory choice is therefore high-stakes. Don't pick the first one that sounds good.

---

## 2. Candidate theory: Moral Foundations Theory (MFT) — Haidt & Graham

### Foundational citation

- Haidt, J. & Graham, J. (2007). *When morality opposes justice: Conservatives have moral intuitions that liberals may not recognize.* Social Justice Research, 20(1), 98-116.
- Graham, J., Haidt, J., & Nosek, B. A. (2009). *Liberals and conservatives rely on different sets of moral foundations.* Journal of Personality and Social Psychology, 96(5), 1029-1046.
- Haidt, J. (2012). *The Righteous Mind: Why Good People Are Divided by Politics and Religion.* Pantheon.
- Atari, M. et al. (2023). *Morality beyond the WEIRD: How the nomological network of morality varies across cultures.* Journal of Personality and Social Psychology — for cross-cultural validation.

### What it claims

Five (later six) innate moral foundations evolved to solve adaptive social problems. Political and religious attitudes derive from how strongly each foundation is weighted:

1. **Care / harm** — concern for suffering, protection of vulnerable
2. **Fairness / cheating** — equality, reciprocity, proportionality
3. **Loyalty / betrayal** — in-group cohesion, patriotism
4. **Authority / subversion** — respect for legitimate hierarchy, tradition
5. **Sanctity / degradation** — purity, contamination avoidance, sacredness
6. **(Liberty / oppression — added in 2012)** — autonomy, resistance to domination

Liberals weight care/harm and fairness more; conservatives weight all six more equally.

### Fit to GSS attitudinal items

**Strong fit** for political-attitude items:

| Foundation | Candidate GSS items |
|---|---|
| Care / harm | ABANY, ABRAPE, ABDEFECT (abortion attitudes), HELPPOOR, HELPSICK, LETDIE1, SUICIDE* |
| Fairness / cheating | RACDIF1-4, WLTH{WHTS,BLKS,HSPS}, DISCAFF*, EQWLTH, GETAHEAD, PARSOL/KIDSSOL |
| Loyalty / betrayal | NAT*-priorities (in-group focus on US needs), CONARMY, partyid (?) |
| Authority / subversion | CAPPUN, GUNLAW, COURTS, POLHITOK, POLABUSE, POLATTAK, TAX, fund/relig items |
| Sanctity / degradation | ABANY (alt foundation), HOMOSEX, XMARSEX, PORNLAW, BIBLE, REBORN, POSTLIFE |
| Liberty / oppression | LIBRAC, LIBCOM, SPK*-civil-liberties, SEXEDUC, GRASS, PILLOK |

### Strengths

- Highly cited, replicated in 30+ countries (Atari et al. 2023 for cross-cultural extension)
- Direct validated mapping to political attitudes — well-suited to GSS attitudinal items
- There is a small body of LLM-MFT work in the moral-psych literature (Atari et al. is one cross-cultural validation paper, but it is about *human* MFT structure, not LLM analysis — Joyce should not cite it as "MFT applied to LLMs"). For "MFT applied to LLMs," Joyce should locate primary sources directly via Google Scholar before citing — I have NOT independently verified a Tjuatja et al. paper that uses MFT on LLMs (Tjuatja 2024 is about response biases, not MFT; see §10.1 caveat below)
- 5-6 clusters → meaningful LOO with reasonable item-count per cluster (~10-15 items each)

### Weaknesses / risks

- MFT is contested in moral psychology — Schein & Gray (2018) argue all foundations reduce to harm; Hoover et al. (2019) propose a different factor structure
- Politically loaded — "liberals weight different foundations" framing carries baggage that may distract from a feature-importance paper
- Item-to-foundation mapping has multiple proposed schemes (original 5, extended 6, MFT-2 with 5 alternative factors)

### Verdict

**Strong fit for GSS attitudinal items; moderate risk on contested-theory grounds.** If chosen, pre-reg should commit to a specific factor structure (likely the 6-foundation 2012 version or MFT-2's 5-factor version) and cite the contested status honestly.

---

## 3. Candidate theory: Schwartz Theory of Basic Values (Shalom Schwartz)

### Foundational citation

- Schwartz, S. H. (1992). *Universals in the content and structure of values: Theoretical advances and empirical tests in 20 countries.* Advances in Experimental Social Psychology, 25, 1-65.
- Schwartz, S. H. (2012). *An overview of the Schwartz theory of basic values.* Online Readings in Psychology and Culture, 2(1), Article 11. https://doi.org/10.9707/2307-0919.1116
- Cieciuch, J. & Schwartz, S. H. (2012). *The number of distinct basic values and their structure assessed by PVQ-40.* Journal of Personality Assessment, 94(3), 321-328. https://doi.org/10.1080/00223891.2012.655817

[verify-before-citing] All three Schwartz citations are well-established but Joyce should pull the originals from APA / J. Pers. Assess. archives before pre-reg quoting.

### What it claims

10 universal human values that organize on a circumplex (compatible vs conflicting):

1. **Self-direction** — independent thought, action, creativity
2. **Stimulation** — excitement, novelty, challenge
3. **Hedonism** — pleasure, gratification
4. **Achievement** — personal success via competence
5. **Power** — social status, prestige, control
6. **Security** — safety, harmony, stability
7. **Conformity** — restraint, social-norm adherence
8. **Tradition** — respect, commitment to cultural/religious customs
9. **Benevolence** — preserving welfare of close others
10. **Universalism** — welfare of all people and nature

The 10 group into 4 higher-order quadrants: openness-to-change vs conservation; self-enhancement vs self-transcendence.

### Fit to GSS attitudinal items

**Moderate fit** — Schwartz items are typically self-report values (PVQ instrument), which GSS doesn't directly measure. But many GSS attitudes can be theoretically derived:

| Value | Candidate GSS items |
|---|---|
| Universalism | HELPPOOR, EQWLTH, DISCAFF*, HELPSICK, HELPNOT, NATENVIR |
| Benevolence | RELITEN, ATTEND, religious items, SOCIAL-related |
| Tradition | BIBLE, REBORN, POSTLIFE, religion items, ABANY (against), HOMOSEX (against) |
| Conformity | CAPPUN, COURTS, POLHITOK (pro-authority compliance) |
| Security | NATARMS, NATAID, USWARY, GUNLAW, OWNGUN |
| Power | (limited GSS items) |
| Achievement | (limited GSS items) |
| Hedonism | XMOVIE, GRASS, XMARSEX |
| Stimulation | (limited) |
| Self-direction | LIBRAC, LIBCOM, SPK* (free-speech endorsement) |

### Strengths

- 30+ years of cross-cultural validation in 80+ countries — gold-standard cross-cultural psychology
- Less politically loaded than MFT
- Clean factor structure (PVQ has been extensively psychometrically validated)
- Already used in some LLM-persona work

### Weaknesses / risks

- 10 values may be too granular for our LOO (some values have only 2-3 GSS items mapped)
- GSS doesn't include the standard PVQ instrument; mapping is INDIRECT (we infer values from related attitudes, not measure them)
- The 4 higher-order quadrants might be a better LOO target than the 10 values (cleaner clusters)

### Verdict

**Moderate-to-strong fit if we use the 4 quadrants instead of 10 values.** Lower contestation risk than MFT, but mapping is more INDIRECT (we're inferring values from attitudes rather than measuring values directly).

---

## 4. Candidate theory: Bourdieu's Forms of Capital

### Foundational citation

- Bourdieu, P. (1986). *The Forms of Capital.* In J. Richardson (Ed.), Handbook of Theory and Research for the Sociology of Education (pp. 241-258). Greenwood.
- Bourdieu, P. (1984). *Distinction: A Social Critique of the Judgement of Taste.* Harvard University Press.

### What it claims

Three forms of capital that structure social position and life trajectories:

1. **Economic capital** — money, property, financial assets
2. **Cultural capital** — education, refined taste, knowledge of high culture
3. **Social capital** — network ties, relationships, group membership

Each form can be converted into the others under specific conditions; together they determine "habitus" — durable dispositions for action.

### Fit to GSS attitudinal items

**Weak fit for ATTITUDES** but **strong fit for the demographic + behavioral feature bins**:

| Capital | Candidate GSS items |
|---|---|
| Economic | INCOME, INCOME16, DWELOWN16, SATFIN, FINRELA, WRKSTAT |
| Cultural | EDUC, DEGREE, MAEDUC/PAEDUC, MADEG/PADEG, NEWS, TVHOURS, ETHNIC (cultural origin) |
| Social | MARITAL, ATTEND, RELITEN, partyid (political affiliation as social tie), HOMPOP |

### Strengths

- Strong sociological pedigree
- Maps cleanly onto demographic + behavioral feature bins (which are otherwise under-theorized)
- Less contested than MFT
- Particularly well-suited for GSB / management-school audiences

### Weaknesses / risks

- Bourdieu's framework predicts FEATURES (capitals) → DISPOSITIONS (habitus) → ATTITUDES. We'd be testing the FIRST link (capitals → attitudes) but the framework's strongest predictions are about DISPOSITIONS.
- Doesn't directly organize the attitudinal bin — mostly just the demographic + behavioral bins
- Could be paired with MFT or Schwartz: Bourdieu organizes input (capitals), MFT/Schwartz organizes output (moral attitudes)

### Verdict

**Best as a SUPPLEMENTARY framework for the demographic + behavioral bins**, paired with MFT or Schwartz for the attitudinal bin. Or as the SOLE theoretical layer if Joyce wants to emphasize the sociology lineage.

---

## 5. Candidate theory: Cultural Theory of Risk — Douglas, Wildavsky

### Foundational citation

- Douglas, M. & Wildavsky, A. (1982). *Risk and Culture: An Essay on the Selection of Technological and Environmental Dangers.* University of California Press.
- Kahan, D. M. (2011). *The Tragedy of the Risk-Perception Commons: Culture Conflict, Rationality Conflict, and Climate Change.* Temple Law Review, 83.
- Tetlock, P. E. (2003). *Thinking the unthinkable: Sacred values and taboo cognitions.* Trends in Cognitive Sciences, 7(7), 320-324.

### What it claims

Four cultural worldviews structure how people perceive risk and form political attitudes, organized on two axes (group-vs-individualism × grid-of-prescription):

1. **Hierarchical** — high-group, high-grid; pro-authority, structured roles
2. **Egalitarian** — high-group, low-grid; communitarian, anti-hierarchy
3. **Individualist** — low-group, low-grid; market-trusting, pro-autonomy
4. **Fatalist** — low-group, high-grid; resigned, low-agency

### Fit to GSS attitudinal items

**Strong fit specifically for political and risk-related attitudes**, less direct for moral / religious attitudes.

| Worldview | Candidate GSS items |
|---|---|
| Hierarchical | CAPPUN, COURTS, POLHITOK, NATARMS, USWARY, GUNLAW |
| Egalitarian | HELPPOOR, EQWLTH, DISCAFF*, RACDIF*, NATENVIR, HELPSICK |
| Individualist | LIBRAC, LIBCOM, SPK*, GRASS (drug-policy autonomy), TAX (anti-redistributive) |
| Fatalist | (limited; possibly ABNOMORE/ABDEFECT dispositions) |

### Strengths

- Only 4 categories → very clean LOO with high item-count per cluster
- Strong fit for political-attitude items (the hot core of GSS)
- Less politically loaded than MFT (technical Bayesian-like worldview taxonomy)

### Weaknesses / risks

- "Fatalist" cluster is hard to populate from GSS items
- Less mainstream than MFT or Schwartz — reviewers may push back on theoretical novelty
- Has been used more in risk perception than general attitude prediction

### Verdict

**Strong fit if the paper centers political/risk attitudes.** Good cluster size for LOO. Less established, more risk on reviewer pushback.

---

## 6. Decision criteria

When choosing among candidates, evaluate against:

1. **Coverage** — does the theory's clusters span ≥80% of the 80 attitudinal items? (MFT: yes; Schwartz: partial; Bourdieu: weak; Cultural Theory: yes)
2. **Cluster balance** — do clusters have similar item counts (≥10 per cluster) for meaningful LOO? (MFT 6-cluster: ~10-15 each ✓; Schwartz 10-value: too granular; Schwartz 4-quadrant: balanced ✓; Bourdieu 3-capital: applies to features not attitudes; Cultural Theory: 4-cluster ~10-20 each ✓)
3. **LLM-applicability literature** — has the theory been applied to LLM/persona analysis already? (MFT: yes, in scattered short papers — Joyce to find primary sources; Schwartz: partial coverage in survey-bias work; Bourdieu: rare in computational work; Cultural Theory: rare)
4. **Cross-cultural validation** — supports generalization claim (MFT: cross-cultural; Schwartz: gold-standard; Bourdieu: Western-centric; Cultural Theory: Western-centric)
5. **Reviewer-friendliness for GSB / Management Science / NeurIPS-NLP** — how each will be received (MFT: well-known but contested; Schwartz: respected but mainstream; Bourdieu: GSB-friendly; Cultural Theory: niche)
6. **Falsifiability** — does the theory make sharp predictions about WHICH cluster matters MOST for WHICH outcome that we can verify? (MFT: strong; Schwartz: moderate; Bourdieu: weak; Cultural Theory: moderate)

## 7. Joyce's literature-review checklist

Before locking, Joyce should:

- [ ] Read the foundational papers for at least 2 candidate theories (recommend MFT + Schwartz at minimum, or MFT + Bourdieu for sociology angle)
- [ ] Look for at least one prior application of the chosen theory **to LLM persona / agent analysis** — Joyce should locate a primary source via Google Scholar / arXiv search ("{theory name} LLM persona" / "{theory name} large language model" / "{theory name} simulated agents"). NOTE: do NOT cite Atari et al. 2023 here — that paper is a *human* MFT cross-cultural validation, not an LLM-on-MFT application; see §10.1 for the corrected interpretation
- [ ] Consider Bayati's preference — sociology-tradition (Bourdieu) vs cog-psych (MFT/Schwartz) vs political-psych (Cultural Theory) signals different paper communities
- [ ] Decide on factor structure (e.g., MFT-5 vs MFT-6, Schwartz-10 vs Schwartz-4-quadrant)
- [ ] Update §8 below with the locked decision

## 8. Locked decision

```
_locked_theory:        (not yet locked)
_locked_factor_structure: (not yet locked)
_lock_date:            (not yet locked)
_lock_rationale:       (not yet locked)
```

Once Joyce updates this section, the next steps are:
1. Build `gss_theory_taxonomy.json` mapping each attitudinal GSS variable → theory cluster
2. Add `_audit_f_print()` smoke test that prints the new cluster organization for review
3. Extend `compute_phase1_headline_multimodel` to compute LOO on theory-cluster groups in addition to 4-bin groups
4. **File an OSF pre-reg amendment** introducing the theory-bin LOO family (the initial OSF pre-reg locks 4-bin LOO only — see `gss_phase1_design.md` §8.7 + §13). The amendment must be filed *before* any theory-bin re-aggregation runs; the 4-bin primary analysis goes through unchanged.

---

## 9. Honest acknowledgment

This document was scaffolded by AI based on familiar canonical citations. **Joyce must verify the citations, read the original sources, and make her own decision.** The mappings I've sketched are first-pass guesses; the locked mapping requires expert (Joyce + Bayati) judgment after primary-source reading. Treat this as a starting menu, not a literature review.

I have not searched arXiv / Google Scholar to find the latest (2024-2026) work on theory-driven LLM persona analysis. Joyce should do that as part of her review.

---

## 10. Prior work — has anyone used theoretical frameworks for LLM personas?

This section answers Joyce's direct question: *"have other papers / businesses already used theoretical frameworks for persona construction?"* The honest answer is **partially, in scattered ways, but not the way the thesis proposes**. Below: what I know, what I don't, and what the gap is.

### 10.1 Academic LLM-persona work — VERIFY EACH BEFORE CITING

⚠️ **All citations below need Joyce to verify directly via the publisher / arXiv before they appear in the OSF pre-registration or paper text. LLM citation hallucination is a known risk.** I have removed entries where I could not verify the existence of the cited work; the table below contains only papers whose existence and broad topic match my best recall, but author lists, year, journal, and exact title still need confirmation.

| Citation (VERIFY before quoting) | What they did (verify) | Theoretical layer? |
|---|---|---|
| **Park, Bernstein, Liang et al. 2024-2025**, "Generative Agent Simulations of 1,000 People," arXiv:2411.10109 | 2-hour AVP-style interviews → LLM persona → predict GSS/BFI/games | **None — atheoretical**, raw transcripts |
| **Argyle, Busby et al. 2023**, "Out of One, Many: Using Language Models to Simulate Human Samples," *Political Analysis* | Demographic priming (age, race, gender, party) → LLM "samples" → study political behavior | **None — demographic priming only** |
| **Aher, Arriaga, Kalai 2023**, "Using Large Language Models to Simulate Multiple Humans," *ICML 2023* | Demographic-only LLM agents → replicate Milgram, Ultimatum, etc. | **None — demographic priming** |
| **Horton 2023**, "Large Language Models as Simulated Economic Agents," NBER WP | Economic-rational-agent framing of LLMs | **Stylized econ theory** but not theory-of-persons |
| **Santurkar, Durmus et al. 2023**, "Whose Opinions Do Language Models Reflect?" arXiv:2303.17548 | Measure GPT-3.5 demographic alignment with Pew/ATP groups | **Demographic priming**; opinions framed by ideology |
| **Bisbee et al. 2024**, "Synthetic Replacements for Human Survey Data? The Perils of Large Language Models," *Political Analysis* | Test if GPT-4 demographic personas replicate ANES — finds inconsistencies | **Demographic priming** |
| **Tjuatja, Chen et al. 2024**, "Do LLMs Exhibit Human-Like Response Biases?", arXiv:2311.04076 | Tests whether LLMs reproduce known survey-research response biases (acquiescence, social desirability, etc.) | **Survey-methodology bias theory** — NOT moral-foundations or values theory; do NOT cite as "MFT applied to LLMs" |
| **Atari et al. 2023**, "Morality beyond the WEIRD: How the nomological network of morality varies across cultures," *JPSP* | Cross-cultural moral foundations validation in *humans* (extension of MFT to non-WEIRD samples) | **Moral Foundations Theory** — applied to *human* cross-cultural validation, NOT to LLM persona construction; do NOT cite as "MFT applied to LLM personas" |

[REMOVED 2026-05-06] An earlier draft listed "Hewitt, Ashokkumar et al. 2024, 'Predicting Results of Social Science Experiments Using Large Language Models,' NBER WP w32068" — I could not verify that NBER working paper number resolves to a real paper, so it has been removed pending verification by Joyce. There is real recent work on LLMs predicting social-science experiment outcomes (Hewitt et al.; also Manning, Zhu & Horton), but Joyce must locate the canonical citation directly rather than relying on this scaffold.

### 10.2 What is NOT in this list (to my knowledge)

I have NOT found a paper that:

> *Constructs LLM personas using a pre-registered theoretical framework (Moral Foundations / Schwartz / Bourdieu / Big Five etc.) to organize the input features, AND empirically compares that theoretical organization against an atheoretical baseline.*

This is the gap Joyce's Phase 1c proposes to fill.

The closest adjacencies I can identify:
- **Atari et al. 2023** is a *human* cross-cultural validation of MFT — it does NOT measure LLM alignment; cite it only as background for MFT's cross-cultural pedigree, not as a precedent for "MFT-on-LLM."
- **Tjuatja et al. 2024** uses survey-methodology theory (response biases) as a probe of LLM behavior — it is NOT an MFT/values application and should not be cited as such.
- **Park et al. 2024** is the closest methodological forerunner but is explicitly atheoretical — they use raw interview transcripts.

Joyce's literature search should look specifically for *2024-2026 short papers* that apply Moral Foundations / Schwartz / Bourdieu / cultural-theory-of-risk frameworks as **persona-construction inputs** (not as evaluation probes). My recall does not include such a paper, but workshops at NeurIPS / EMNLP / ACL 2024-2025 are the most likely source.

**Caveat**: I have NOT searched arXiv for 2024-2026 papers exhaustively. There is non-zero probability that a 2025 or 2026 paper has done exactly this. Joyce's literature search must verify.

### 10.3 Industry / startup landscape

These are commercial products in adjacent space; I have only public-information-level knowledge of their methods.

| Company | What they do (publicly) | Theoretical framework used? |
|---|---|---|
| **Simile** (Park lab spinout) | Persona-based prediction at commercial scale | Public materials suggest **atheoretical** (transcript-based, like Park 2024) |
| **Aaru** | Election prediction + market research via LLM personas | Public claims focus on ENGINEERING (multi-model ensemble, recursive refinement) — **no public theory-driven framework** |
| **Cookiy** | AI-moderated qualitative research interviews | Tool for COLLECTION, not persona construction |
| **Yabble** | AI-moderated commercial qual + persona generation | Marketing-segmentation taxonomies (commercial), not academic theory |
| **Voicepanel / Synthetic Users / Persona AI / Ad-Lib AI** | Commercial synthetic-respondent panels | Marketing-persona taxonomies; **no public academic-theory grounding** |

**Key observation**: industry has converged on engineering improvements (better models, more data, ensembling) rather than theoretical grounding. Atheoretical wins for product because customers don't pay for "MFT-grounded" — they pay for "predicts elections / sells product."

This is **good news for Joyce's thesis claim**: an academic atomic-paper-quality contribution that introduces theory-driven structure WHERE INDUSTRY HAS NOT is a clean contribution, because:
1. Industry won't have done it (commercial pressure goes the other way)
2. Academic literature has tested theories ON LLMs but not applied them as persona-construction principles
3. Bayati's GSB program audience values theoretical grounding more than industry does

### 10.4 What this means for Joyce's literature review

When Joyce does her own search, she should look for:
1. **Recent (2024-2026) arXiv papers** on theory-grounded persona construction — verify whether anything supersedes what I've listed
2. **Workshops at NeurIPS / ICML / ACL** on LLM-personas — many recent workshops have produced relevant short papers
3. **Bayati's network** — does anyone in his GSB / management-science circle do related work?
4. **Citation graph from Park et al. 2024** — papers that cite Park (Google Scholar "cited by") and apply theoretical structure

The thesis novelty claim should be conservative until verified:
- "We are not aware of prior work that systematically applies a pre-registered theoretical framework to organize LLM persona inputs and empirically compares to an atheoretical baseline."
- After thorough search: drop "to our knowledge" and assert directly.

### 10.5 What I'd recommend Joyce add to the OSF pre-registration

A short related-work section saying:

> *Prior work in LLM persona simulation has used demographic priming (Argyle et al. 2023; Aher et al. 2023; Santurkar et al. 2023), interview-transcript priming (Park et al. 2024-2025), or stylized economic-agent priming (Horton 2023). Theoretical frameworks have been used to probe LLM response biases (e.g., Tjuatja et al. 2024) but, to our knowledge, no prior published work applies a pre-registered theory of human cognition or values as the organizing principle for persona input features and empirically compares to an atheoretical baseline. Phase 1c of this thesis (see §13 of the design document) proposes to fill that gap by applying [chosen theory] as a pre-registered organizing principle for the persona's input features, and empirically comparing the theoretical organization against an atheoretical 4-bin baseline.*

(Joyce: tighten "to our knowledge" to a confident assertion only after the literature search rules out 2024-2026 superseding work. The reviewer test is: would a domain expert immediately produce a counter-example?)

This positions the contribution clearly, distinguishes it from prior work, and avoids over-claiming.

---

## 11. ⚠️ Honest disclaimer (read before citing anything in §10)

The citations in §10 are my best recall of work I believe I've encountered. Before any of these citations are used in OSF pre-registration or paper text, **Joyce must verify each one by retrieving the actual paper**:

- arXiv IDs must resolve to a real abstract page
- Author lists, year, and title must match
- Claims about what each paper did must come from reading the abstract or beyond

**LLM citation hallucination is a known risk.** Verify before quoting. If a citation doesn't resolve, drop it from the paper rather than approximating.

I was honest above about uncertainty and explicitly said "to my knowledge / verify." Don't carry that vagueness into the final paper — verify and replace with confident citation, or remove.
