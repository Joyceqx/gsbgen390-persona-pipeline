# Cookiy Brief — Study 2: Survey-Only (Park's Condition D)

**Design:** Mirror of Study 1 but without the open-ended interview portion. Each respondent answers ~18 construction-survey items (covering demographic, behavioral, psychological, and attitudinal domains — your four proposal categories) followed by the same 15 held-out eval items as Study 1. The persona is built from the construction-survey responses and evaluated against the eval responses.

This is a **between-subjects** comparison with Study 1: different panel respondents in each arm, so we report side-by-side per-arm means rather than within-subjects deltas. With N=2 in the interview arm and N=1 in the survey arm, the pilot is a feasibility demonstration only — not a statistical comparison. The deliverable is "both pipelines run end-to-end on Cookiy-collected data and produce interpretable metrics." The comparison to Park's "surveys-only ≈ interview-only" finding awaits a higher-N follow-up study.

**Recruit parameters:**
- N: **1** real participant (panel-recruit, separate from Study 1) — feasibility demonstration of the survey-conditioned pipeline; statistical comparison across arms awaits higher-N follow-up
- Duration: 15 min
- Country: US · Language: English · Age: 18+
- Targeting: broad — no further narrowing
- Format: structured Cookiy interview (same module as Study 1, but no open-ended section)

**Cost: ~1 × $10 = $10**

---

## Study structure: TWO SECTIONS (both structured, no probing)

### Section 1 — Construction survey (~8 min, 18 items)

**Verbatim opening line — moderator says this at the start:**

> "Thanks for joining. This is a structured survey — I'll read about thirty short questions and you'll give me a quick answer for each. There are no right answers and no follow-ups; we'll just go straight through the list. Let's start."

Section-level guidance for the moderator:
- Read each item in the exact order below.
- Capture the answer and move on. Do NOT probe, do NOT ask follow-ups, do NOT discuss reasoning.
- ~25–30 seconds per item including the question read.

**The 18 construction items** (each is its own discrete question for `question_list`; followups: empty; tag: "no probe"):

**Demographic (5 items)**

1. **Q-1.** "Which age range applies to you: 18 to 24, 25 to 34, 35 to 44, 45 to 54, or 55 or older?" `[c_age]`
2. **Q-2.** "How would you describe your gender: man, woman, non-binary, or prefer not to say?" `[c_gender]`
3. **Q-3.** "What's the highest level of education you've completed: high school, some college, bachelor's degree, master's degree, or doctorate?" `[c_education]`
4. **Q-4.** "Which range describes your household's annual income before taxes: under 50,000 dollars; 50 to 100,000; 100 to 200,000; or over 200,000 dollars?" `[c_income]`
5. **Q-5.** "Which US region do you live in: Northeast, Midwest, South, or West?" `[c_region]`

**Behavioral history (5 items)**

6. **Q-6.** "How many hours per week do you typically work or study: under 20, 20 to 40, 40 to 60, or over 60 hours?" `[c_workhrs]`
7. **Q-7.** "How often do you exercise: never, monthly, weekly, several times per week, or daily?" `[c_exercise]`
8. **Q-8.** "How many hours per day do you typically spend on social media: under 1, 1 to 2, 2 to 4, or 4 or more hours?" `[c_socmedia]`
9. **Q-9.** "Did you vote in the last presidential election: yes, no, or were not eligible?" `[c_voted]`
10. **Q-10.** "How often do you attend religious services: never, only on special occasions, monthly, or weekly or more often?" `[c_relattend]`

**Psychological (4 items)**

11. **Q-11.** "If forced to choose, would you rather take a guaranteed 500 dollars, or take a 50-50 chance of getting nothing or 1,200 dollars? Pick A for the guaranteed amount or B for the gamble." `[c_risk]`
12. **Q-12.** "On a scale of 1 to 5, where 1 means 'I plan my day in advance' and 5 means 'I prefer to go with the flow,' which best describes you?" `[c_planning]`
13. **Q-13.** "On a scale of 1 to 5, where 1 is strongly disagree and 5 is strongly agree: I am optimistic about how my next 5 years will go. Your rating?" `[c_optimism]`
14. **Q-14.** "On a scale of 1 to 5, where 1 means 'I research extensively before making important decisions' and 5 means 'I mostly trust my gut,' which best describes you?" `[c_decstyle]`

**Attitudinal (4 items)**

15. **Q-15.** "Which of these matters most to you right now: A) career success, B) family and relationships, C) personal growth, D) financial security, or E) helping others? Pick one." `[c_priority]`
16. **Q-16.** "On a scale of 1 to 5, where 1 is strongly disagree and 5 is strongly agree: I prefer maintaining tradition to embracing change. Your rating?" `[c_tradition]`
17. **Q-17.** "On a scale of 1 to 5, where 1 means 'society works best when individuals look after themselves' and 5 means 'society works best when communities take care of each other,' which best describes your view?" `[c_indiv_comm]`
18. **Q-18.** "On a scale of 1 to 5, where 1 is strongly disagree and 5 is strongly agree: I generally trust major institutions like the government, media, and corporations. Your rating?" `[c_inst_trust]`

---

### Section 2 — Held-out eval (~6 min, 15 items)

**Verbatim transition line — moderator says this immediately after Q-18:**

> "Thanks. For the last few minutes I'll read fifteen more short statements and ask you to give me a quick rating or pick one option for each. Same format as before — no follow-ups, just go with your gut."

The 15 eval items are **identical** to Study 1's Section 2 (questions Q-1 through Q-15 in the Study 1 brief). Use the same wording, same order, same `[id]` tags. Reproduced here for Cookiy's convenience:

19. **Q-19.** "On a scale of 1 to 5, where 1 is strongly disagree and 5 is strongly agree: I see myself as someone who is reserved. What's your rating?" `[bfi_e_r]`
20. **Q-20.** "On the same 1-to-5 scale: I see myself as someone who is generally trusting. Your rating?" `[bfi_a]`
21. **Q-21.** "1 to 5: I see myself as someone who tends to be lazy. Your rating?" `[bfi_c_r]`
22. **Q-22.** "1 to 5: I see myself as someone who is relaxed and handles stress well. Your rating?" `[bfi_n_r]`
23. **Q-23.** "1 to 5: I see myself as someone who has few artistic interests. Your rating?" `[bfi_o_r]`
24. **Q-24.** "1 to 5: I see myself as someone who is outgoing and sociable. Your rating?" `[bfi_e]`
25. **Q-25.** "1 to 5: I see myself as someone who tends to find fault with others. Your rating?" `[bfi_a_r]`
26. **Q-26.** "1 to 5: I see myself as someone who does a thorough job. Your rating?" `[bfi_c]`
27. **Q-27.** "1 to 5: I see myself as someone who gets nervous easily. Your rating?" `[bfi_n]`
28. **Q-28.** "1 to 5: I see myself as someone who has an active imagination. Your rating?" `[bfi_o]`
29. **Q-29.** "Now a different format. Taken all together, how would you say things are these days — would you say that you are very happy, pretty happy, or not too happy? Pick one." `[happy]`
30. **Q-30.** "Generally speaking, would you say that most people can be trusted, that you can't be too careful in dealing with people, or it depends? Pick one." `[trust]`
31. **Q-31.** "On a seven-point scale where 1 is extremely liberal, 4 is moderate, and 7 is extremely conservative, where would you place yourself politically? Give me a number from 1 to 7." `[polviews]`
32. **Q-32.** "On the whole, how satisfied are you with the work you do — very satisfied, moderately satisfied, a little dissatisfied, or very dissatisfied? Pick one." `[satjob]`
33. **Q-33.** "Last one. Back to the 1-to-5 agreement scale: When I find a brand I like, I tend to stick with it for years. What's your rating?" `[loyal]`

**After Q-33:** Moderator says "Thanks, that's everything. Have a great rest of your day," and ends the session.

---

## Notes for Cookiy when generating the discussion guide

- All 33 items above are discrete `question_list` entries.
- For all items: `followups: []`, guideline tag: "do not probe, capture answer and move on."
- The `[id]` tags in brackets are downstream pipeline anchors; moderator does NOT speak them.
- Two sections only: Section 1 (Q-1 through Q-18) and Section 2 (Q-19 through Q-33), with the verbatim transition line between them.
- Sample size: 1.
- Participant profile: US, English, 18+, broad.
- This study is **independent** of Study 1 — different panel respondents, no pairing required.

---

## Why ~18 construction items and which categories matter

The 18 items are split 5/5/4/4 across the four feature categories from your proposal taxonomy (demographic, behavioral, psychological, attitudinal). This isn't enough items per category to do real feature-importance analysis at this scale — but it lets the persona pipeline build a survey-conditioned prompt that actually contains content from all four categories, so the comparison to interview-conditioned persona is fair (both have multi-domain input).

For the eventual thesis study, you'll want 8–15 items per category (60+ total) and a much larger N to actually compare category contributions. The pilot is just demonstrating that the survey-only persona-construction pipeline works end-to-end.

---

## When transcripts come back

For each Study 2 respondent (different respondents than Study 1), save:
- Transcript: `/Users/joyce/Documents/GSBGEN390/responses_s2/R1/transcript.txt`
- Demographics: `responses_s2/R1/demographics.json`
- Cookiy report (if generated): `responses_s2/R1/cookiy_report.{json,pdf}`

Note the **separate** `responses_s2/` folder — keeps Study 1 and Study 2 transcripts cleanly partitioned. The pipeline will read both folders and produce per-arm + cross-arm metrics.
