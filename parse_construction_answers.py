#!/usr/bin/env python3
"""
Extract the 18 construction-survey answers from Cookiy Study 2 transcripts.

Sister script to parse_eval_answers.py, same architecture: anchor on the
moderator's question stem, walk forward through the participant's reply
and the moderator's confirmation utterance, prefer the moderator's logged
value when present.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# (item_id, anchor regex, answer_type, options-or-None)
# answer_type ∈ {"likert5", "categorical", "binary"}
ITEMS = [
    # Demographic
    ("c_age",       r"age range applies|18\W+to\W+24|25\W+to\W+34",
     "categorical", ["18-24", "25-34", "35-44", "45-54", "55+"]),
    ("c_gender",    r"describe your gender|gender.{0,40}(?:man|woman|non-binary)",
     "categorical", ["man", "woman", "non-binary", "prefer not to say"]),
    ("c_education", r"highest level of education|high school.{0,30}some college",
     "categorical", ["high school", "some college", "bachelor", "master", "doctorate"]),
    ("c_income",    r"household.{0,40}income|under.{0,15}50,?000|50\W+to\W+100",
     "categorical", ["under 50", "50 to 100", "100 to 200", "over 200"]),
    ("c_region",    r"US region|Northeast.{0,15}Midwest|where do you live",
     "categorical", ["northeast", "midwest", "south", "west"]),
    # Behavioral
    ("c_workhrs",   r"hours per week.{0,40}(?:work|study)|under\W+20.{0,15}20\W+to\W+40",
     "categorical", ["under 20", "20 to 40", "40 to 60", "over 60"]),
    ("c_exercise",  r"how often.{0,15}exercise|never.{0,15}monthly.{0,15}weekly",
     "categorical", ["never", "monthly", "weekly", "several times", "daily"]),
    ("c_socmedia",  r"social media|hours per day.{0,40}(?:social|spend)",
     "categorical", ["under 1", "1 to 2", "2 to 4", "4 or more"]),
    ("c_voted",     r"vote.{0,40}(?:last presidential|election)",
     "categorical", ["yes", "no", "not eligible"]),
    ("c_relattend", r"religious services|how often.{0,15}attend",
     "categorical", ["never", "special occasions", "monthly", "weekly"]),
    # Psychological
    ("c_risk",      r"guaranteed\W+\$?500|guaranteed.{0,15}500.{0,15}dollar|gamble|fifty.fifty",
     "categorical", ["A", "B"]),
    ("c_planning",  r"plan my day in advance|go with the flow",
     "likert5",     None),
    ("c_optimism",  r"optimistic about (?:how )?(?:your |my )?next 5 years|optimistic.{0,20}5 years",
     "likert5",     None),
    ("c_decstyle",  r"research extensively|trust my gut|mostly trust",
     "likert5",     None),
    # Attitudinal
    ("c_priority",  r"matters most to you right now|career success.{0,40}family",
     "categorical", ["A", "B", "C", "D", "E"]),
    ("c_tradition", r"prefer maintaining tradition|embracing change",
     "likert5",     None),
    ("c_indiv_comm", r"individuals look after themselves|communities take care",
     "likert5",     None),
    ("c_inst_trust", r"trust major institutions|government.{0,15}media.{0,15}corporation",
     "likert5",     None),
]

NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
}

MOD_CONFIRMATION_RE = re.compile(
    r"\b(?:"
    r"I'?ll\s+(?:mark|record|note|put)|"
    r"I'?ve\s+(?:noted|recorded|marked|got)|"
    r"I\s+(?:see|have)\s+(?:that|noted|recorded|marked|down)|"
    r"noted\s+(?:that\s+)?as|"
    r"recorded\s+(?:that\s+)?as|"
    r"got\s+that\s+as|"
    r"have\s+that\s+down\s+as|"
    r"thank you for"
    r")\b",
    re.IGNORECASE,
)

MOD_REPROMPT_RE = re.compile(
    r"apologize|\bsorry\b|state\s+that\s+again|repeat|"
    r"could\s+you\s+(?:repeat|clarify|give\s+me)|let\s+me\s+rephrase|"
    r"as\s+a\s+rating|on\s+(?:that\s+)?one\s+to\s+five",
    re.IGNORECASE,
)


def first_sentence(text: str) -> str:
    m = re.search(r"^(.+?[.!?])(?:\s|$)", text)
    return m.group(1) if m else text


def find_likert(text: str, max_val: int = 5):
    """Pick the LAST Likert-valued integer or word in text."""
    found = []
    for m in re.finditer(r"(?<!\d)([1-9])(?!\d)", text):
        v = int(m.group(1))
        if 1 <= v <= max_val:
            found.append((m.start(), v))
    for word, val in NUM_WORDS.items():
        if val > max_val:
            continue
        for m in re.finditer(rf"\b{word}\b", text, re.IGNORECASE):
            found.append((m.start(), val))
    found.sort()
    return found[-1][1] if found else None


def find_categorical(text: str, options) -> str | None:
    t = text.lower()
    # Try direct match for short options
    matches = []
    for opt in options:
        if opt.lower() in t:
            matches.append((t.index(opt.lower()), opt))
    if matches:
        matches.sort()
        return matches[-1][1]
    # Try letter-only options (e.g., "A", "B")
    for opt in options:
        if len(opt) == 1 and opt.isalpha():
            if re.search(rf"\b(?:{opt}|the letter {opt}|option {opt}|number {opt})\b", text, re.IGNORECASE):
                return opt
    return None


def collect_response(transcript, start_idx, max_lookahead=15):
    user_parts = []
    mod_confirm = ""
    n = len(transcript)
    for j in range(start_idx + 1, min(start_idx + 1 + max_lookahead, n)):
        t = transcript[j]
        if t["role"] == "user":
            user_parts.append(t["content"])
            continue
        c = t["content"]
        if MOD_CONFIRMATION_RE.search(c):
            mod_confirm = first_sentence(c)
            break
        if MOD_REPROMPT_RE.search(c):
            continue
        break
    return " ".join(user_parts), mod_confirm


def extract_answer(transcript, anchor_re, answer_type, options):
    pat = re.compile(anchor_re, re.IGNORECASE)
    for i, turn in enumerate(transcript):
        if turn["role"] != "assistant" or not pat.search(turn["content"]):
            continue
        user_text, mod_confirm = collect_response(transcript, i)
        if answer_type == "likert5":
            mod_val = find_likert(mod_confirm, 5) if mod_confirm else None
            user_val = find_likert(user_text, 5) if user_text else None
            return mod_val if mod_val is not None else user_val
        if answer_type == "categorical":
            mod_match = find_categorical(mod_confirm, options) if mod_confirm else None
            user_match = find_categorical(user_text, options) if user_text else None
            return mod_match or user_match
    return None


def parse_transcript(path: Path):
    data = json.loads(path.read_text())
    turns = data.get("transcript", [])
    row = {"participant_id": path.stem}
    for item_id, anchor_re, answer_type, options in ITEMS:
        row[item_id] = extract_answer(turns, anchor_re, answer_type, options)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", help="Transcript JSON files")
    ap.add_argument("--out", default=None, help="CSV output path")
    args = ap.parse_args()

    rows = [parse_transcript(Path(p)) for p in args.paths]
    fields = ["participant_id"] + [item_id for item_id, _, _, _ in ITEMS]

    if args.out:
        with open(args.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {len(rows)} rows to {args.out}", file=sys.stderr)
    else:
        w = csv.DictWriter(sys.stdout, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
