# Theory-driven feature-engineering: literature review starter

**Author:** Joyce Yu (literature review owner)
**Created:** 2026-05-06 by collaborating Claude session (scaffold only — Joyce owns the actual review)
**Status:** Open. Decision needed before Phase 1a launches.
**Locked theory:** _(not yet locked — see §6 below)_

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
- Has been APPLIED to LLM analysis: e.g., Atari et al. 2023, Tjuatja et al. 2024 used MFT to characterize LLM political alignment
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
- Schwartz, S. H. (2012). *An overview of the Schwartz theory of basic values.* Online Readings in Psychology and Culture, 2(1).
- Cieciuch, J. & Schwartz, S. H. (2012). *The number of distinct basic values and their structure assessed by PVQ-40.*

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
3. **LLM-applicability literature** — has the theory been applied to LLM/persona analysis already? (MFT: yes — Atari et al. 2023, Tjuatja et al. 2024; Schwartz: partial; Bourdieu: rare in computational work; Cultural Theory: rare)
4. **Cross-cultural validation** — supports generalization claim (MFT: cross-cultural; Schwartz: gold-standard; Bourdieu: Western-centric; Cultural Theory: Western-centric)
5. **Reviewer-friendliness for GSB / Management Science / NeurIPS-NLP** — how each will be received (MFT: well-known but contested; Schwartz: respected but mainstream; Bourdieu: GSB-friendly; Cultural Theory: niche)
6. **Falsifiability** — does the theory make sharp predictions about WHICH cluster matters MOST for WHICH outcome that we can verify? (MFT: strong; Schwartz: moderate; Bourdieu: weak; Cultural Theory: moderate)

## 7. Joyce's literature-review checklist

Before locking, Joyce should:

- [ ] Read the foundational papers for at least 2 candidate theories (recommend MFT + Schwartz at minimum, or MFT + Bourdieu for sociology angle)
- [ ] Look for at least one prior application of the chosen theory to LLM persona / agent analysis (Atari et al. 2023 on MFT is a good starter; arXiv search for "{theory name} LLM persona" should surface others)
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
4. Pre-register both 4-bin and theory-cluster LOO together on OSF before Phase 1a launches

---

## 9. Honest acknowledgment

This document was scaffolded by AI based on familiar canonical citations. **Joyce must verify the citations, read the original sources, and make her own decision.** The mappings I've sketched are first-pass guesses; the locked mapping requires expert (Joyce + Bayati) judgment after primary-source reading. Treat this as a starting menu, not a literature review.

I have not searched arXiv / Google Scholar to find the latest (2024-2026) work on theory-driven LLM persona analysis. Joyce should do that as part of her review.
