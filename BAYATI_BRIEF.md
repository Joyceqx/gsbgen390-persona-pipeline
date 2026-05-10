# GSBGEN390 Phase 1 OSF v1 — Executive Brief for Prof. Bayati

**Author**: Joyce Yu · **Advisor**: Prof. Mohsen Bayati · **Date**: 2026-05-10
**Purpose**: Request signoff on OSF v1 preregistration before paid Phase 1 runs

---

## TL;DR (read first; 1 minute)

1. **Phase 1 design is locked + ready for OSF filing**, contingent on your signoff.
2. **Budget**: ~$756 total Phase 1 (I can absorb modest expansion if you request).
3. **One ask**: please review the OSF v1 draft and confirm the 7 §17 items below (6 already locked by my decisions on 2026-05-10; you're the external dependency on the 7th).
4. **Timeline**: I'd like to start Phase 1a smoke as soon as you sign off, with Phase 1b paid runs ~1 week after.

If you have ~30 minutes today: **read this brief end-to-end + skim the §17 table at the end**. If you have ~2 hours: also read `osf_preregistration_v1.md` end-to-end. If you can give 5 minutes verbally: I can walk you through it at our next meeting.

---

## What changed since your last review (the methodological evolution)

The Phase 1 design has been through six rounds of external audit since the previous version you saw. Material changes (in approximately decreasing order of importance):

### Sample size + sampling

- **Phase 1a**: N=100 → **N=200 with a pre-registered 100/100 selection/validation split**. The §12.2 selector now scores ONLY on the first 100; the held-out 100 is scored independently after selection and reported as `validation_mae` alongside the Phase 1b headline. This is the post-selection-inference defense that an external reviewer (Audit-3) flagged as the single most important methodological fix.
- **Phase 1b**: N=1,500 random sample → **N=3,309 full GSS 2024 cross-section**. Removes the "we sampled to a budget" framing.

### Model panel

- Cheap panel: ~~MiniMax-M1~~ → **Llama-3.3-70B-Instruct (Meta)**. The panel is now 3 China-trained (Qwen / DeepSeek / Kimi) + 1 Western-trained (Llama-Meta), defending against the "all-China-trained" cross-family generalization attack at Western venues. Pre-OSF swap; no amendment needed.

### Sensitivity scope (Joyce decision Option A, locked 2026-05-10)

- Cheap panel: primary_eval only (60 prompts/respondent).
- GPT-4o anchor (N=100 selection-split subset, n_samples=2): primary + sensitivity (the only Park-comparable run; produces the per-item raw-accuracy anchor table side-by-side with Park v2 SI Table 3).
- This matches OSF §3.2's "sensitivity_eval used only on GPT-4o anchor" literal wording.

### Statistical infrastructure

- Bootstrap: B=1,000 percentile → **B=10,000 BCa via scipy.stats.bootstrap** with percentile fallback for degenerate inputs. The B=1,000 percentile floor was 0.001, colliding with the joint-34 Holm critical p of 0.00147 (a Codex audit catch); B=10,000 puts the floor safely below.
- Effect-size thresholds (small <0.02 / modest 0.02-0.05 / substantive ≥0.05) anchored to Funder & Ozer (2019) — gates substantive interpretation alongside Holm significance.

### Selection-rule guardrails (all pre-registered)

- DQ-1 parse-failure ceiling (>30% → disqualify)
- DQ-3 per-item relative-variance gate (mode-collapse guard)
- 5%-quality / 1%-cost tie-break
- **All-DQ-fail → PAUSE for human review** (NOT silent Qwen fallback — the previously-pre-registered Qwen fallback was REMOVED because all-DQ-fail is a SIGNAL, and continuing on a failed model wastes ~$209-481).
- Named-Qwen fallback retained ONLY for true quality+cost ties.

### Co-primary analyses (this is the headline scientific design)

- **4-bin LOO ablation** (broad feature-category attribution): drop one feature bin at a time from the persona prompt; report respondent-macro Likert ΔMAE with Holm-Bonferroni primary correction at α=0.05.
- **34-battery LOO** (mechanistic cluster-level attribution): drop one construct-level battery at a time across all 4 bins; nested Holm-Bonferroni within each bin + joint-34 Holm sensitivity gate for cross-bin claims.
- **Bin-level Shapley decomposition** (16 conditions): robustness re-aggregation of the 4-bin LOO; shares the 4-bin primary family multiplicity.

### Leakage hygiene

- **R1 battery exclusion** (mirrors Park v2's BFI whole-trait-block hold-out applied to GSS): when predicting any primary_eval item, the entire battery containing that item is dropped from the persona prompt.
- **R2 regression-baseline comparator** (Ridge / multinomial Logistic on the same R1-respecting feature pool): non-LLM baseline that quantifies the "predictable from this input pool" upper bound; framed as a rhetorical decomposition with explicit asymmetric-missing-data caveat, NOT as a literal causal partition.

### Theory framework — Discussion-section ONLY (this is the anti-HARKing move)

The 6 candidate frameworks (MFT / Schwartz / Bourdieu / Cultural Theory / Inglehart-Welzel / Big Five) are used as **qualitative interpretive scaffolding in the Discussion section only** — never as confirmatory hypotheses. Null or mixed theoretical alignment is published with equal prominence to positive alignment. This is the central anti-HARKing commitment in the design and the main reason Phase 1 reads as a methods paper rather than a horse-race-of-theories paper.

---

## Budget breakdown (~$756 total)

| Sub-phase | What runs | Cost |
|---|---|---|
| Smoke | N=10 cheap × primary only | ~$1 |
| Phase 1a cheap | N=200 × 4 cheap models × primary only | ~$17 |
| Phase 1b cheap | N=3,309 × single §12.2-selected model × primary only | ~$71 |
| GPT-4o anchor | N=100 selection-split subset × primary + sensitivity × n=2 (one run, serves both 1a + 1b reporting) | ~$148 |
| **Subtotal: core Phase 1** | | **~$237** |
| Battery LOO co-primary | 34 batteries × 12 items × 3,309 respondents × 1 model | ~$481 |
| Shapley extension | 11 multi-bin LOO conditions × 12 items × N=200 × 4 cheap | ~$38 |
| **Subtotal: Phase 1c** | | **~$519** |
| **GRAND TOTAL** | | **~$756** |

**Budget evolution** (so you see the iteration): early back-of-envelope ~$280-300 → Codex N9 audit corrected to ~$450 → Audit-3 full-sample + 100/100 split + Llama swap pushed to ~$875 → Joyce Option A (cheap-panel primary-only; sensitivity anchor-only) settled at **~$756**.

**If budget is a concern**: I can defer Battery LOO to Phase 1d (saves $481 in Phase 1, total drops to ~$237) and decide after Phase 1b headline whether to spend the $481. Three other reductions are available (~$263 / ~$209 / ~$96 savings respectively) if Phase 1c needs to fit a tighter envelope.

---

## What I need from you

### One required ask: OSF §17 signoff

Below is the full §17 status. Items ①②③④⑤⑦ are LOCKED by my decisions on 2026-05-10. **Item ⑥ is the external blocker — your signoff on the OSF v1 draft as a whole.**

| # | Item | Joyce decision | Bayati action needed |
|---|---|---|---|
| ① | 6-theory candidate list (MFT / Schwartz / Bourdieu / Cultural Theory / Inglehart-Welzel / Big Five) | ✅ Locked: keep all 6 | Confirm OK |
| ② | Null-alignment commitment (Discussion-only, equal prominence to positive findings) | ✅ Locked: text approved | Confirm OK |
| ③ | Discussion section structure | ✅ Locked: data-organized (one subsection per empirical finding) | Confirm OK |
| ④ | Inglehart-Welzel citation verification | ✅ Locked: cross-checked 2026-05-10 night against publisher pages + WVS + Wikipedia; one new caveat added (Beugelsdijk & Welzel 2010 single-factor critique) | Confirm OK |
| ⑤ | Driver runtime extension timing | ✅ Locked: Phase 1b-result-conditional (write the ~1-day Battery LOO + Shapley orchestration driver AFTER Phase 1b results, so we decide whether $481 Phase 1c is justified) | Confirm OK |
| ⑥ | **Bayati final signoff on OSF v1** | — | **THIS IS YOUR ASK** |
| ⑦ | Phase 1 ~$756 budget | ✅ Locked: I'll cover; can absorb modest expansion if you prefer the $875 variant or want different reductions | Confirm budget OK |

### Three "if you want to discuss" items

1. **Phase 1-alone vs Phase 1+2 thesis path**: the auto-correlation tautology (attitudinal-features-predict-attitudinal-outcomes can be partly mechanical) is the strongest single-paper attack on Phase 1. Phase 1 alone can be defended by reframing as a methods paper (leakage hygiene + selector + dual-headline split). Phase 1 + Phase 2 together (with the BFI + behavioral-game outcomes Phase 2 collects) provides the cross-outcome contrast that fully defangs the tautology. Strategic decision affecting Phase 2 recruitment timeline. I'd appreciate your read.

2. **Phase 1c orchestration timing**: the Battery LOO + Shapley orchestration drivers are currently NOT-IMPLEMENTED stubs in `gss_driver.py` (the analyzers ARE implemented and self-tested). I'm planning to implement orchestration AFTER Phase 1b results — so we can see whether the Phase 1b headline justifies the $481 Phase 1c spend before investing the ~1 day of driver work. Confirm OK or push for earlier.

3. **Phase 2 design** (`thesis_phase2_design.md`) is untouched since April 30 and needs its own revision pass — separate session, not blocking OSF v1.

---

## What to read (in order, if you want to go deep)

| File | Time | Why |
|---|---|---|
| This brief (`BAYATI_BRIEF.md`) | 5 min | TL;DR + budget + asks |
| `osf_preregistration_v1.md` | 30-45 min | Full OSF preregistration v1 — the document you're signing off on |
| `gss_phase1_design.md` | 30 min | Canonical live design (sample sizes / panel / sensitivity scope / §12.2 selector) |
| `RUNBOOK.md` | 10 min | Exact paid-run commands + cost projection per step (so you see how the $756 is dispatched) |
| `theory_review_round2.md` | 20 min | Theory framework comparison; §2.2 has the Inglehart-Welzel cite verification I did |

**All files are in the GitHub repository** at `https://github.com/Joyceqx/gsbgen390-persona-pipeline`. GitHub renders markdown directly; you can read everything in the browser without cloning. The current pre-lock commit is `4b8a8df` (with subsequent fixes — I'll send you the final pre-lock hash once §17 ④/⑤ documentation lands in a follow-up commit).

---

## Decision asks summary (you can reply in 4 lines)

1. OSF v1 §17 ①–⑤+⑦ as locked above: **OK / amend X**
2. Budget ~$756 (or $875 variant): **OK / amend X**
3. Phase 1 alone vs Phase 1+2 thesis path: **defer to later / discuss now / want to commit to X now**
4. Phase 1c orchestration timing: **OK to defer / want earlier**

---

Thank you for your guidance through this — the design has improved materially across each audit round, and the OSF reads as a much stronger preregistration than the original draft. Looking forward to your signoff.

— Joyce

*Document prepared 2026-05-10 night per OSF §17 item ⑥*
