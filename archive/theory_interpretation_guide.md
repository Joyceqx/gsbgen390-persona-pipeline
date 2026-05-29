# Theory Interpretation Guide
## (Discussion-section memo for Phase 1; NOT an OSF confirmatory family)

**Version**: v0.1 (replaces the earlier `osf_preregistration_appendix_a_theory_predictions.md` v0.1 DRAFT under the 2026-05-09 lean-design lock)
**Locked**: target 2026-05-12 (must lock before Phase 1a fires, but with much lower stakes than a confirmatory horse-race appendix would have had)
**Companion files**:
- `gss_phase1_design.md` §13.3 — locks "theory interpretation is secondary, primary findings do not depend on theory alignment"
- `archive/theory_review.md` + `theory_review_round2.md` — full literature scaffolds (kept; not affected by slim-down)
- `tier1_tool_schemas.md` — locked schemas for the two secondary tools (Shapley + Battery LOO)

---

## Purpose

The Phase 1 paper has **one** clean primary contribution — *which survey-collectible feature categories actually improve LLM persona prediction of GSS attitude outcomes?* — answered by the 4-bin LOO and its Shapley robustness check. After the primary results are in, the Discussion section should situate the empirical pattern in relation to existing cognitive and sociological frameworks, **but theory does NOT drive any primary claim** (per `gss_phase1_design.md` §13.3).

This memo serves two roles:

1. **Pre-commit a list of candidate frameworks** (so the Discussion does not pick its frame post-hoc from whatever happens to fit best after seeing the data).
2. **State the broad direction each framework would predict** (qualitatively — no hard numeric thresholds), so reviewers can verify the Discussion's interpretation is consistent with what each framework canonically claims.

This memo does NOT:
- Define a horse race with hard win/lose thresholds.
- Promise that "one theory wins" or that any theory drives a primary claim.
- Require numeric Spearman ρ thresholds, agreement scores, or "supports / partial / refutes" verdicts.
- Trigger any Phase 1c re-analysis or refinement experiment.

---

## How this memo is used

After Phase 1a + 1b results are in, the paper's Discussion section will:

1. Summarize the empirical pattern from the primary 4-bin LOO + Shapley + Battery LOO results.
2. Walk through each candidate framework below, noting **qualitatively** which aspects of the empirical pattern do or do not align with what the framework canonically claims.
3. Be **honest about mixed or null alignment**: if no framework cleanly explains the empirical pattern, the Discussion says so.

The Discussion is structured around the **data**, not the theory list. The theory list is interpretive scaffolding, not a fixed frame.

---

## Candidate frameworks (interpretive only — qualitative predictions only)

The six frameworks below are the candidates Joyce surveyed in `archive/theory_review.md` + `theory_review_round2.md`. They are listed here so the Discussion section's framework choice is pre-committed; they do NOT trigger any quantitative test.

For each framework, we note:
- The framework's broad direction (which feature categories should matter, by the framework's logic).
- A short identifiability note (how it differs qualitatively from neighboring frameworks).

### 1. Moral Foundations Theory (MFT) — Haidt & Graham

- **Source**: Haidt & Graham 2007 *Soc. Justice Res.*; Graham, Haidt & Nosek 2009 *JPSP*; Atari et al. 2023 *JPSP* (cross-cultural validation, *human* MFT — NOT LLM-on-MFT).
- **Broad prediction**: attitudes are central; among attitudes, **moral / religious / civil-liberties batteries** (abortion, sexual_morality, religious_belief, civil_lib_*) should dominate over institutional or economic batteries.
- **Identifiability vs neighbors**: MFT differs from Inglehart-Welzel by NOT centrally predicting AGE or generational cohort effects.

### 2. Schwartz Theory of Basic Values

- **Source**: Schwartz 1992 *Adv. Exp. Soc. Psychol.* 25:1-65; Schwartz 2012 *Online Readings in Psychology and Culture* 2(1) [DOI 10.9707/2307-0919.1116]; Cieciuch & Schwartz 2012 *J. Pers. Assess.* 94(3):321-328.
- **Broad prediction**: attitudes are central; the universalism axis suggests **economic_help + racial_inequality_perception** batteries should be visible alongside the moral/religious cluster MFT predicts.
- **Identifiability vs MFT**: Schwartz puts more weight on universalism (economic / racial); MFT puts more weight on sanctity (abortion / sexual / religious). Both predict attitudinal-bin dominance.

### 3. Bourdieu's Forms of Capital

- **Source**: Bourdieu 1986 "The Forms of Capital"; Bourdieu 1984 *Distinction*.
- **Broad prediction**: **demographic + behavioral bins matter most** (capitals → habitus → attitudes). Predicts the OPPOSITE bin ranking from MFT/Schwartz.
- **Identifiability**: this is the cleanest cleavage in the candidate set. If demographic + behavioral dominate, Bourdieu is the natural interpretive frame; if attitudinal dominates, Bourdieu is partial at best.

### 4. Cultural Theory of Risk (Douglas-Wildavsky)

- **Source**: Douglas & Wildavsky 1982 *Risk and Culture*; Kahan 2011 *Temple Law Review*; Tetlock 2003 *Trends in Cog. Sci.*
- **Broad prediction**: attitudes are central; specifically **political-attitude / risk-perception batteries** (police_use_of_force, racial_inequality, economic_help, civil_lib) over **moral-attitude batteries** (abortion, sexual_morality).
- **Identifiability vs MFT**: opposite emphasis on abortion vs civil-liberties batteries.

### 5. Inglehart-Welzel Cultural Map

- **Source**: Inglehart 1977 *The Silent Revolution*; Welzel 2013 *Freedom Rising*; WVS-derived cultural-axis literature. (Round 2 caveat: some Inglehart-Welzel citations in `theory_review_round2.md` §2.2 were recall-based; Joyce should verify primary sources before quoting.)
- **Broad prediction**: attitudes are central; sexual_morality + religious_belief + gender_role_attitudes batteries align with the secular-rational vs traditional axis. **AGE in demographic should be more predictive than under MFT** (cohort effects).
- **Identifiability vs MFT**: AGE-importance is the disambiguator. High overlap on attitudinal-bin batteries.

### 6. Big Five (HEXACO)

- **Source**: Costa & McCrae 1992 *NEO-PI-R Manual*; John & Srivastava 1999 *Handbook of Personality*; Ashton & Lee 2007 *PSPR* (HEXACO).
- **Broad prediction**: **psychological + behavioral bins matter most** (trait → behavior). Big Five is NOT primarily an attitude theory; if attitudinal dominates, Big Five is a poor frame here.
- **Critical caveat**: GSS does not measure Big Five directly; the project uses crude proxies (HAPPY, HEALTH, FAIR, HELPFUL, TRUST as psychological; ATTEND, PRAY, NEWS as behavioral). Even if Big Five operates, weak proxies introduce noise.

---

## Anti-HARKing discipline (preserved in lean form)

Even though this memo is NOT a confirmatory horse race, the slim design preserves anti-HARKing through three commitments:

1. **Theory-list pre-commitment**: the six candidate frameworks above are locked in this memo before Phase 1a fires. The Discussion section may not introduce a *new* framework after seeing the data and treat it as if it were always the natural frame. New frameworks may be discussed but must be flagged as post-hoc.

2. **Primary findings stand alone**: the 4-bin LOO + Shapley + Battery LOO results are reported in the abstract and Section 5 in **engineering / atheoretical language** (e.g., *"attitudinal features dominate; within-bin contribution is concentrated in [batteries]"*). They do NOT depend on which framework the Discussion finds most useful.

3. **Null + mixed alignment reported honestly**: if no framework cleanly explains the empirical pattern, the Discussion says so. Specifically:
   > "The empirical pattern observed in Phase 1 is not fully captured by any of the six candidate frameworks listed in the theory interpretation guide. We discuss partial alignments and the implications below; we do not claim that the LLM persona uses any specific framework."

   This is the primary anti-HARKing commitment. Joyce + Bayati must affirm explicitly that null or mixed alignment is published with equal prominence.

---

## What we explicitly do NOT do (locked under §13.4 deferral list)

- Do NOT run preregistered theory-bin LOO as a confirmatory family.
- Do NOT compute or report `theory_aligned_correlations` Spearman ρ values from RSA.
- Do NOT preregister hard numeric thresholds per theory (e.g., "MFT supports if ρ ≥ 0.4").
- Do NOT run Stage 3 refinement experiments (theory-organized prompts, counterfactual perturbation).
- Do NOT write the abstract claim "the LLM persona uses [Theory X]" or similar mentalistic claim.

---

## Open items for Joyce / Bayati before Phase 1a

These need explicit signoff before OSF lock:

1. **Theory list (§ above)**: is the 6-candidate list final, or do you want to add (e.g., Hofstede, Theory of Planned Behavior, Self-Determination, Dual-Process)? My current judgment is the 6 listed are the ones with clearest GSS-attitude relevance; the others are Phase-2-only or country-level.
2. **Null-alignment reporting commitment**: please affirm explicitly in the OSF that null or mixed theoretical alignment will be published with equal prominence to a positive-alignment result.
3. **Discussion structure**: confirm the Discussion section will be **data-organized** (one subsection per primary finding, with theory frames as interpretive scaffolding within each), NOT theory-organized (one subsection per theory).
4. **`theory_review_round2.md` Inglehart-Welzel verification**: verify the Inglehart-Welzel claims in §2.2 from primary sources before any of these frameworks goes into the Discussion section.

---

## What this memo replaces

- The earlier `osf_preregistration_appendix_a_theory_predictions.md` v0.1 DRAFT (2026-05-09 morning) was a full six-theory horse-race preregistration with hard numeric thresholds, agreement scoring, tie-handling rules, and a Stage 3 refinement plan. That design was slimmed down per Codex's lean-design audit (2026-05-09 afternoon) because a single-theory-wins horse race would push the paper toward "tool-stack paper" territory and away from its clean primary contribution. The slim design preserves anti-HARKing through theory-list pre-commitment + null-reporting commitment, without requiring numeric thresholds.

The full horse-race scheme is preserved in version-control history but is NOT the live design.
