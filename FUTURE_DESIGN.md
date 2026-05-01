# Future Design — Discussion Agenda for Bayati Meeting

This is the "we know about it, here's how we'd handle it in v2" file. None of these are blockers for tonight's pilot run; all of them deserve a position before the thesis-stage replication. Treat as your structured agenda when the conversation moves from "what did the pilot show" to "what's the real study going to look like."

---

## Group 1 — Methodology to lock down before the real survey arm

**1.1 Eval leakage / in-session priming.**
The interview portion verbally surfaces the same constructs the eval section then asks about (e.g., political views came up in P1's interview content, then was eval'd as `polviews`). The persona prompt for Condition C includes the interview, so the persona has been "primed" with the construct before being evaluated on it. This will inflate Condition C's apparent accuracy compared to what a clean held-out evaluation would show.

*For the real study:* either (a) reproduce Park's protocol with ≥2-week separation between interview and eval, or (b) constrain moderator probes to disjoint constructs (interview only covers domains the eval won't touch). Option (a) is the methodologically rigorous choice; (b) is operationally cheaper but harder to defend.

**1.2 Test-retest denominator.**
Park's headline numbers (74/82/83/86%) are *percentages of test-retest reliability* — i.e., normalized against how consistent participants are with themselves two weeks apart. We don't have a self-retest baseline, so our raw agreement % isn't directly citable against Park's. Either: (a) collect a 2-week retest from at least a subsample at thesis-stage, or (b) commit publicly to never quoting a single number side-by-side with Park's, only relative comparisons within our own data.

**1.3 BFI-10 → BFI-44 upgrade.**
With BFI-10 (2 items per trait), the Big Five trait-level scores are statistically meaningless — a single noisy item per direction. If trait-level metrics (RMSE, correlation) are headline in the thesis, we need BFI-44. If we keep BFI-10, the trait scores should be clearly framed as exploratory only.

**1.4 Pre-registration.**
Everything in the pilot has pivoted on the fly — design changed five times in 1.5 days. Acceptable for pilot; not acceptable for the thesis paper. Lock the eval battery, the construction battery, the four-category taxonomy, the primary metric, and the analysis plan *before* scaling N. OSF or AsPredicted registration is cheap insurance against post-hoc-flexibility critique.

---

## Group 2 — Survey-design implications

**2.1 Outcome-stratified leave-one-category-out is the actual thesis novelty.**
Pilot bundles all 4 categories (demographic / behavioral / psychological / attitudinal) into Condition D and reports a single Likert MAE per condition. Park v2 makes clear that the interview→surveys gap is **not uniform across outcomes** — 0.01 on GSS attitudes, 0.15 on BFI personality, 0.28 on behavioral economic games. So the real thesis result is a **two-way analysis**: feature category × outcome dimension. Drop-attitudinal probably hurts most on GSS items but barely on games; drop-behavioral probably does the opposite. The thesis-stage design needs (a) LOO ablations × (b) ≥30 per arm × (c) eval batteries that span all three outcome types (attitudes / personality / behavior), with confidence intervals on each cell of the category × outcome matrix. **This is the actual design conversation to have at the meeting** — what's the right N, what's the right ablation grain, what's the eval expansion (full BFI-44 + game-style behavioral items), and how do we power the cross-cut comparisons.

**2.2 Demographic-baseline standardization.**
Right now Condition A uses whatever surfaces in the open interview, which is ad-hoc and varies across respondents. Real study needs a fixed demographics schema (age, gender, race, region, education, political ideology — Park's set) collected uniformly via a screening survey, in BOTH the interview arm and the survey arm. This makes Condition A a real apples-to-apples baseline rather than a mush of unequal information.

**2.3 Moderator script discipline.**
Cookiy's AI moderators paraphrase eval items significantly. Real study needs a decision: (a) accept paraphrase variance as deployment realism (current pilot stance — the smart parser handles it), or (b) lock the eval section to a stricter platform (verbatim-script tool) or human moderator. Option (b) is cleaner methodologically; (a) is more honest about what real-world AI persona research actually looks like.

---

## Group 3 — Operational / data-quality notes

These don't need to be central in the conversation but should be flagged as known limitations:

**3.1 Cookiy 15-min cap means our "interview" is ~10% of Park's 2-hour AVP.** This isn't just a sampling difference — it's a different *measurement instrument*. Our interview-conditioned persona has fundamentally less material than Park's. Expect lower interview-condition accuracy; do not interpret a low number as evidence against Park.

**3.2 Panel respondents are noisy.** P1 gave single-word answers, asked the AI moderator about its vendor mid-eval, cut the session early. This sets a ceiling on interview-conditioning quality that's about respondent engagement, not about the architecture. Real study should screen for engagement or use a more attentive recruit pool.

**3.3 N_SAMPLES=2 is a noisy self-consistency estimator.** With only 2 samples per item, "self-MAE" has very high variance. Bump to 5–10 samples per item in the real run. Cost is linear; reliability of the consistency metric improves substantially.

**3.4 Smart parser uses moderator confirmation as gold signal.** When a participant says "a three or four" and the moderator logs "I have that down as a four," we record 4. This biases toward the moderator's interpretation when the participant is genuinely between values. Acceptable for pilot; for the real study, consider also recording the participant's response distribution and reporting it alongside the point estimate.

---

## How to use this document in the meeting

Use it as a **defensive shield**, not a weakness. Walking in saying "I know about these five things and here's my proposed handling for each" is much stronger than presenting numbers and waiting for the prof to find the holes. Read order:

1. Lead with the pilot results (`MEETING_HANDOUT.md`).
2. When the prof asks about limitations or methodology, pivot to **Group 1.1** (eval leakage) — it's the most material methodological concern and you have an answer (Park-style 2-week protocol or disjoint-construct probes).
3. Use **Group 2.1** (LOO-ablation × N) as the natural pivot from "pilot showed direction" to "thesis study design." This is where Bayati's expertise actually matters most.
4. Group 3 stays in your back pocket unless directly asked — these are caveats, not central design choices.

The prof will likely have additions to all three groups. That's the point — this is the *agenda* for the design conversation, not the answer.
