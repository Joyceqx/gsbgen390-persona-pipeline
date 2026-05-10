# Cookiy Brief — Combined 15-min Session × N=2 (PATCHED for video-interview format)

**Recruit parameters:**
- N: **2** real participants (panel-recruit) — minimal viable pilot for the interview arm; the survey arm (Study 2) carries the main weight at N=10
- Duration: 15 min
- Country: US · Language: English · Age: 18+
- Targeting: broad — no further narrowing

**Format note:** Cookiy is a video-interview platform. The moderator speaks aloud and the audio is auto-transcribed. Eval-item answers will be parsed downstream by anchoring on question stems in the transcript (no literal text markers needed — those wouldn't appear in a speech-to-text transcript anyway).

---

## Study structure: TWO SECTIONS

### Section 1 — Open-ended interview (~9 min, 6 probes with follow-ups)

Conversational, warm, nonjudgmental. Probe for **concrete recent stories**, not abstractions. 2–3 sentences per probe minimum. Follow-up if the participant gives a one-line answer. The 6 probes are already wired into the discussion guide as `question_list`.

### Section 2 — Structured rating section (~6 min, 15 discrete items)

**Verbatim transition line — moderator says this immediately after Section 1 wraps:**

> "Great, thank you for sharing all that. For the last few minutes I'm going to switch to a structured rating section. I'll read fifteen short statements and ask you to give me a quick rating or pick one option for each. There are no right answers — just go with your gut. Ready?"

**Section-level guidance for the moderator:**
- Read each item in the exact order below.
- For each item, capture the participant's answer and move on.
- **Do NOT probe, do NOT ask follow-ups, do NOT discuss reasoning.** Section 2 is strict Q-and-A.
- Maintain a steady pace: ~25–30 seconds per item including the question read.

**The 15 questions for Section 2's `question_list`** (each is its own discrete question; followups: empty; pacing tag: "no probe"):

1. **Q-1.** "On a scale of 1 to 5, where 1 is strongly disagree and 5 is strongly agree: I see myself as someone who is reserved. What's your rating?" *(answer: 1–5)* `[bfi_e_r]`

2. **Q-2.** "On the same 1-to-5 scale: I see myself as someone who is generally trusting. Your rating?" *(1–5)* `[bfi_a]`

3. **Q-3.** "1 to 5: I see myself as someone who tends to be lazy. Your rating?" *(1–5)* `[bfi_c_r]`

4. **Q-4.** "1 to 5: I see myself as someone who is relaxed and handles stress well. Your rating?" *(1–5)* `[bfi_n_r]`

5. **Q-5.** "1 to 5: I see myself as someone who has few artistic interests. Your rating?" *(1–5)* `[bfi_o_r]`

6. **Q-6.** "1 to 5: I see myself as someone who is outgoing and sociable. Your rating?" *(1–5)* `[bfi_e]`

7. **Q-7.** "1 to 5: I see myself as someone who tends to find fault with others. Your rating?" *(1–5)* `[bfi_a_r]`

8. **Q-8.** "1 to 5: I see myself as someone who does a thorough job. Your rating?" *(1–5)* `[bfi_c]`

9. **Q-9.** "1 to 5: I see myself as someone who gets nervous easily. Your rating?" *(1–5)* `[bfi_n]`

10. **Q-10.** "1 to 5: I see myself as someone who has an active imagination. Your rating?" *(1–5)* `[bfi_o]`

11. **Q-11.** "Now a different format. Taken all together, how would you say things are these days — would you say that you are *very happy*, *pretty happy*, or *not too happy*? Pick one." *(categorical, 3 options)* `[happy]`

12. **Q-12.** "Generally speaking, would you say that *most people can be trusted*, that *you can't be too careful in dealing with people*, or *it depends*? Pick one." *(categorical, 3 options)* `[trust]`

13. **Q-13.** "On a seven-point scale where 1 is extremely liberal, 4 is moderate, and 7 is extremely conservative, where would you place yourself politically? Give me a number from 1 to 7." *(integer 1–7)* `[polviews]`

14. **Q-14.** "On the whole, how satisfied are you with the work you do — *very satisfied*, *moderately satisfied*, *a little dissatisfied*, or *very dissatisfied*? Pick one." *(categorical, 4 options)* `[satjob]`

15. **Q-15.** "Last one. Back to the 1-to-5 agreement scale: When I find a brand I like, I tend to stick with it for years. What's your rating?" *(1–5)* `[loyal]`

**After Q-15:** Moderator says "Thanks, that's everything. Have a great rest of your day," and ends the session.

---

## Notes for Cookiy when patching the guide

- The 15 questions above should each be added as a separate question in `question_list` for Section 2.
- For each Section 2 question: `followups: []`, guideline tag: "do not probe, capture answer and move on."
- The `[id]` tags in brackets are for downstream pipeline anchoring — moderator does NOT speak them.
- Section 1's existing 6 probes remain unchanged.
- Sample size: 2.
- Participant profile: US, English, 18+.

---

## How parsing will work downstream

Since the transcript is auto-transcribed audio, no literal text markers will be present. The pipeline parser will:

1. Locate Section 2 by anchoring on the verbatim transition line ("...switch to a structured rating section...").
2. For each of the 15 eval items, anchor on the item's stem (e.g., the phrase "is reserved" for Q-1, "generally trusting" for Q-2, etc.) and capture the participant's next utterance.
3. Parse the captured utterance for the relevant answer type (1–5 integer, 1–7 integer, or categorical match).
4. Cookiy's auto-generated report may also surface structured ratings — if so, that's a faster path than transcript parsing. Worth checking once R1's transcript and report are both in hand.

---

## When transcripts come back

For each respondent, save:
- Transcript: `/Users/joyce/Documents/GSBGEN390/responses/R{1,2}/transcript.txt`
- Demographics: `/Users/joyce/Documents/GSBGEN390/responses/R{1,2}/demographics.json` (whatever Cookiy exposes — age range, gender, region, education, etc.)
- Cookiy report (if generated): `/Users/joyce/Documents/GSBGEN390/responses/R{1,2}/cookiy_report.{json,pdf}`

Then ping me — I'll run the pipeline on the new structure once R1 lands so we can verify parsing works before R2 and R3 burn budget.
