#!/usr/bin/env python3
"""
Extract the 15 held-out eval answers from Cookiy interview transcripts.

Each transcript JSON has shape:
    {"transcript": [{"role": "assistant"|"user", "content": "..."}, ...]}

Usage:
    python parse_eval_answers.py <transcript.json> [<transcript.json> ...] [--out path.csv]

Strategy: anchor on each item's distinctive question stem in moderator turns,
then walk forward collecting the participant's response(s) until we hit
either a moderator confirmation ("I have that down as a three.") or a
new mod question. The mod confirmation's FIRST SENTENCE is the gold
signal — it is what Cookiy actually recorded.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# (item_id, anchor regex, answer_type)
# Anchors loosened to tolerate moderator paraphrases observed in real transcripts.
ITEMS = [
    ("bfi_e_r",  r"\bis reserved\b",                                                "likert5"),
    ("bfi_a",    r"\bgenerally\W+(?:a\W+)?trust(?:ing|y)\b",                        "likert5"),
    ("bfi_c_r",  r"\btends?\W+to\W+be\W+lazy\b",                                    "likert5"),
    ("bfi_n_r",  r"\brelaxed.{0,15}handles?\W+stress\b",                            "likert5"),
    ("bfi_o_r",  r"\bfew\W+artistic\W+interests?\b",                                "likert5"),
    ("bfi_e",    r"\boutgoing.{0,15}sociable\b",                                    "likert5"),
    ("bfi_a_r",  r"\bfind\W+fault\W+with\W+others\b",                               "likert5"),
    ("bfi_c",    r"\b(?:does|do)\W+a\W+thorough\W+job\b",                           "likert5"),
    ("bfi_n",    r"\bgets?\W+nervous\W+easily\b",                                   "likert5"),
    ("bfi_o",    r"\bactive\W+imagination\b",                                       "likert5"),
    ("happy",    r"very\W+happy.{0,40}pretty\W+happy.{0,40}not\W+too\W+happy",      "happy"),
    ("trust",    r"most\W+people\W+can\W+be\W+trusted",                             "trust"),
    ("polviews", r"extremely\W+liberal.{0,150}extremely\W+conservative",            "likert7"),
    ("satjob",   r"satisfied\W+are\W+you\W+with\W+the\W+work",                      "satjob"),
    ("loyal",    r"stick\W+with\W+it\W+for\W+years",                                "likert5"),
]

NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7,
    # Participants sometimes phrase as ordinals ("I am a fourth")
    "first": 1, "second": 2, "third": 3, "fourth": 4,
    "fifth": 5, "sixth": 6, "seventh": 7,
}

MOD_CONFIRMATION_RE = re.compile(
    r"\b("
    r"I'?ll\s+(?:mark|record|note)|"
    r"I'?ve\s+(?:noted|recorded|marked|got)|"
    r"I\s+have\s+(?:noted|recorded|marked|that\s+down)|"
    r"noted\s+that\s+as|"
    r"recorded\s+that\s+as|"
    r"got\s+that\s+as|"
    r"I'?ll\s+put\s+that\s+down|"
    r"have\s+that\s+down\s+as"
    r")\b",
    re.IGNORECASE,
)

MOD_REPROMPT_RE = re.compile(
    r"apologize|\bsorry\b|state\s+that\s+again|repeat|asking\s+for\s+your\s+rating|"
    r"could\s+you\s+(?:repeat|clarify)|let\s+me\s+rephrase",
    re.IGNORECASE,
)

# 18 construction-survey items (Park Condition D, Section 1 of the survey arm)
CONSTRUCTION_ITEMS = [
    ("c_age",        r"\bage\W+range\W+applies\b",                    "categorical"),
    ("c_gender",     r"\b(?:describe\W+)?your\W+gender\b",             "categorical"),
    ("c_education",  r"\b(?:level|highest\W+level)\W+of\W+education\b", "categorical"),
    ("c_income",     r"\b(?:annual\W+)?(?:household.{0,15}income|income\W+before\W+taxes)\b", "categorical"),
    ("c_region",     r"\bUS\W+region\b",                               "categorical"),
    ("c_workhrs",    r"\bhours\W+per\W+week.{0,30}(?:work|study)\b",   "categorical"),
    ("c_exercise",   r"\b(?:do\W+you|often\W+do\W+you)\W+exercise\b",  "categorical"),
    ("c_socmedia",   r"\bsocial\W+media\b",                            "categorical"),
    ("c_voted",      r"\bvote\W+in\W+the\W+last\W+presidential\b",     "categorical"),
    ("c_relattend",  r"\battend\W+religious\W+services\b",             "categorical"),
    ("c_risk",       r"\bguaranteed\W+(?:500|five\W+hundred)\b|\b50.?50\W+chance\b", "categorical"),
    ("c_planning",   r"\bplan(?:ning)?\W+(?:my|your)\W+day\W+in\W+advance\b", "likert5"),
    ("c_optimism",   r"\boptimistic\b.{0,40}\bnext\b.{0,15}\b(?:5|five)\W+years\b", "likert5"),
    ("c_decstyle",   r"\bresearch\W+extensively\b",                    "likert5"),
    ("c_priority",   r"\bmatters\W+most\W+to\W+you\W+right\W+now\b",   "categorical"),
    ("c_tradition",  r"\bmaintaining\W+tradition\b",                   "likert5"),
    ("c_indiv_comm", r"\bindividuals\W+look\W+after\W+(?:themselves|themselv)\b", "likert5"),
    ("c_inst_trust", r"\b(?:major\W+institutions|trust\W+major\W+institutions)\b", "likert5"),
]

# Per-item categorical option lists (label, regex). Order matters: most specific first.
CATEGORICAL_OPTIONS = {
    "c_age": [
        ("55 or older",  r"\b(?:fifty.?five|55).{0,15}(?:older|plus|\+)|\b55\W+or\W+older\b|\bolder\b"),
        ("45-54",        r"\b(?:forty.?five|45).{0,20}(?:fifty.?four|54)\b"),
        ("35-44",        r"\b(?:thirty.?five|35).{0,20}(?:forty.?four|44)\b"),
        ("25-34",        r"\b(?:twenty.?five|25).{0,20}(?:thirty.?four|34)\b"),
        ("18-24",        r"\beighteen\b|\b18\W+to\W+(?:24|twenty.?four)\b|\b(?:18|eighteen).{0,15}(?:24|twenty.?four)\b"),
    ],
    "c_gender": [
        ("Prefer not to say", r"\bprefer\W+not\W+to\W+say\b|\bdecline\b|\bdon.?t\W+want\W+to\W+say\b"),
        ("Non-binary",   r"\bnon.?binary\b|\bnonbinary\b|\benby\b"),
        ("Woman",        r"\bwoman\b|\bfemale\b"),
        ("Man",          r"\b(?:a\W+)?man\b|\bmale\b|\bguy\b"),
    ],
    "c_education": [
        ("Doctorate",    r"\bdoctorate\b|\bph\.?\W?d\b|\bdoctoral\b"),
        ("Master's degree", r"\bmaster.?s\b|\bgraduate\W+degree\b"),
        ("Bachelor's degree", r"\bbachelor.?s\b|\bcollege\W+degree\b|\bundergrad(?:uate)?\W+degree\b"),
        ("Some college", r"\bsome\W+college\b"),
        ("High school",  r"\bhigh\W+school\b|\bhs\W+(?:diploma|grad)\b"),
    ],
    "c_income": [
        ("Over $200,000", r"\b(?:over|more)\W+(?:than\W+)?(?:two\W+hundred|200,000|200k)\b|\b200,?000\+\b"),
        ("$100,000-200,000", r"\b(?:one\W+hundred|100,?000|100k).{0,30}(?:two\W+hundred|200,?000|200k)\b|\b100\W+to\W+200\b"),
        ("$50,000-100,000",  r"\b(?:fifty|50,?000|50k).{0,30}(?:one\W+hundred|100,?000|100k|hundred\W+thousand)\b|\b50\W+to\W+100\b"),
        ("Under $50,000",    r"\bunder\W+(?:fifty|50,?000|50k)\b|\bless\W+than\W+(?:fifty|50)\b"),
    ],
    "c_region": [
        ("Northeast",    r"\bnortheast\b|\bnorth.?east\b"),
        ("Midwest",      r"\bmidwest\b|\bmid.?west\b"),
        ("West",         r"\bwest\b"),
        ("South",        r"\bsouth\b"),
    ],
    "c_workhrs": [
        ("Over 60",      r"\b(?:over|more\W+than)\W+(?:60|sixty)\b"),
        ("40-60",        r"\b(?:forty|40).{0,15}(?:sixty|60)\b"),
        ("20-40",        r"\b(?:twenty|20).{0,15}(?:forty|40)\b"),
        ("Under 20",     r"\bunder\W+(?:20|twenty)\b|\bless\W+than\W+(?:20|twenty)\b"),
    ],
    "c_exercise": [
        ("Daily",        r"\bdaily\b|\bevery\W+day\b"),
        ("Several times per week", r"\bseveral\W+times\b|\b(?:few|3|three)\W+times\W+(?:a|per)\W+week\b"),
        ("Weekly",       r"\bweekly\b|\bonce\W+a\W+week\b"),
        ("Monthly",      r"\bmonthly\b|\bonce\W+a\W+month\b"),
        ("Never",        r"\bnever\b|\bdon.?t\W+exercise\b"),
    ],
    "c_socmedia": [
        ("4 or more",    r"\b(?:4|four)\W+or\W+more\b|\b(?:more\W+than|over)\W+(?:4|four)\b"),
        ("2-4",          r"\b(?:2|two)\W+to\W+(?:4|four)\b|\b(?:2|two).{0,5}(?:4|four)\W+hours\b"),
        ("1-2",          r"\b(?:1|one)\W+to\W+(?:2|two)\b|\b(?:1|one).{0,5}(?:2|two)\W+hours\b"),
        ("Under 1",      r"\bunder\W+(?:1|one)\b|\bless\W+than\W+(?:1|one)\b"),
    ],
    "c_voted": [
        ("Were not eligible", r"\bnot\W+eligible\b|\bineligible\b|\bcouldn.?t\W+vote\b|\bunder\W*age\b"),
        ("Yes",          r"\byes\b|\bI\W+voted\b|\bdid\W+vote\b"),
        ("No",           r"\bno\b|\bdidn.?t\W+vote\b|\bdid\W+not\W+vote\b"),
    ],
    "c_relattend": [
        ("Weekly or more", r"\bweekly\b|\bevery\W+week\b|\bmore\W+often\b"),
        ("Monthly",      r"\bmonthly\b|\bonce\W+a\W+month\b"),
        ("Special occasions", r"\bspecial\W+occasions?\b|\bholidays\b|\bonly\W+on\b"),
        ("Never",        r"\bnever\b|\bdon.?t\W+attend\b"),
    ],
    "c_risk": [
        ("A (guaranteed $500)", r"\bguaranteed\b|\b500\b|\bfive\W+hundred\b|\b\bA\b\b|\bsafe\b|\bsure\W+thing\b"),
        ("B (gamble)",   r"\bgamble\b|\b1,?200\b|\btwelve\W+hundred\b|\b50.?50\b|\bchance\b|\bB\b|\brisk\b"),
    ],
    "c_priority": [
        ("E (helping others)",    r"\b(?:e|letter\W+e|helping\W+others?)\b"),
        ("D (financial security)", r"\b(?:d|letter\W+d|financial\W+security|money)\b"),
        ("C (personal growth)",   r"\b(?:c|letter\W+c|personal\W+growth)\b"),
        ("B (family/relationships)", r"\b(?:b|letter\W+b|family|relationships?)\b"),
        ("A (career success)",    r"\b(?:a|letter\W+a|career(?:\W+success)?)\b"),
    ],
}

# Combined anchor list for boundary detection (any eval or construction question)
ALL_ANCHORS = (
    [re.compile(rx, re.IGNORECASE) for _, rx, _ in ITEMS]
    + [re.compile(rx, re.IGNORECASE) for _, rx, _ in CONSTRUCTION_ITEMS]
)


def first_sentence(text: str) -> str:
    m = re.search(r"^(.+?[.!?])(?:\s|$)", text)
    return m.group(1) if m else text


def find_likert_all(text: str, max_val: int):
    """All Likert-valued positions found in text, sorted by occurrence."""
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
    return [v for _, v in found]


def find_likert(text: str, max_val: int = 5, prefer: str = "last"):
    """Return one Likert int. prefer='last' picks the last one mentioned (final answer)."""
    vals = find_likert_all(text, max_val)
    if not vals:
        return None
    return vals[-1] if prefer == "last" else vals[0]


def find_happy(text: str):
    t = text.lower()
    if re.search(r"\bnot\W+too\W+happy\b", t):
        return "Not too happy"
    if re.search(r"\bpretty\W+happy\b", t):
        return "Pretty happy"
    if re.search(r"\bvery\W+happy\b", t):
        return "Very happy"
    return None


def find_trust(text: str):
    t = text.lower()
    if re.search(r"can.?t\W+be\W+too\W+careful", t):
        return "You can't be too careful"
    if re.search(r"cannot\W+be\W+trusted|can.?t\W+be\W+trusted|don.?t\W+trust", t):
        return "You can't be too careful"
    if re.search(r"\bit\W+depends\b|\bdepends\b", t):
        return "Depends"
    if re.search(r"most\W+people\W+can\W+be\W+trusted|trust\W+most\W+people|can\W+be\W+trusted", t):
        return "Most people can be trusted"
    return None


def find_satjob(text: str):
    t = text.lower()
    if re.search(r"\bvery\W+dissatisfied\b", t):
        return "Very dissatisfied"
    if re.search(r"\b(?:a\W+)?little\W+dissatisfied\b", t):
        return "A little dissatisfied"
    if re.search(r"\bmoderately\W+satisfied\b", t):
        return "Moderately satisfied"
    if re.search(r"\bvery\W+satisfied\b", t):
        return "Very satisfied"
    return None


def collect_response(transcript, start_idx: int, max_lookahead: int = 15):
    """Walk forward from a question turn. Collect user turns and the FIRST
    moderator confirmation. Stop at confirmation or at the next eval question.
    Tolerate mod re-prompts (apologies, restate-the-question)."""
    user_parts = []
    mod_confirm = ""
    n = len(transcript)
    for j in range(start_idx + 1, min(start_idx + 1 + max_lookahead, n)):
        t = transcript[j]
        if t["role"] == "user":
            user_parts.append(t["content"])
            continue
        # moderator turn
        c = t["content"]
        if MOD_CONFIRMATION_RE.search(c):
            mod_confirm = first_sentence(c)
            break
        if MOD_REPROMPT_RE.search(c):
            continue  # mod is re-asking; keep going
        # Any other mod turn (next question, generic ack, wrap-up) ends the answer window.
        break
    return " ".join(user_parts), mod_confirm


def find_categorical(text: str, item_id: str):
    if not text:
        return None
    options = CATEGORICAL_OPTIONS.get(item_id, [])
    for label, pat in options:
        if re.search(pat, text, re.IGNORECASE):
            return label
    return None


def extract_answer(transcript, anchor_re, answer_type, item_id=None):
    pat = re.compile(anchor_re, re.IGNORECASE)
    for i, turn in enumerate(transcript):
        if turn["role"] != "assistant" or not pat.search(turn["content"]):
            continue
        user_text, mod_confirm = collect_response(transcript, i)
        if answer_type in ("likert5", "likert7"):
            max_val = 5 if answer_type == "likert5" else 7
            mod_val = find_likert(mod_confirm, max_val) if mod_confirm else None
            user_val = find_likert(user_text, max_val) if user_text else None
            return mod_val if mod_val is not None else user_val
        if answer_type == "happy":
            return find_happy(mod_confirm) or find_happy(user_text)
        if answer_type == "trust":
            return find_trust(mod_confirm) or find_trust(user_text)
        if answer_type == "satjob":
            return find_satjob(mod_confirm) or find_satjob(user_text)
        if answer_type == "categorical" and item_id:
            # Prefer user's direct answer for categoricals (mod's confirmation often paraphrases)
            return find_categorical(user_text, item_id) or find_categorical(mod_confirm, item_id)
    return None


def parse_transcript(path: Path, item_list):
    data = json.loads(path.read_text())
    turns = data.get("transcript", [])
    row = {"participant_id": path.stem}
    for item_id, anchor_re, answer_type in item_list:
        row[item_id] = extract_answer(turns, anchor_re, answer_type, item_id)
    return row


def write_csv(rows, fields, path):
    if path:
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {len(rows)} rows to {path}", file=sys.stderr)
    else:
        w = csv.DictWriter(sys.stdout, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", help="Transcript JSON files")
    ap.add_argument("--out", default=None, help="Eval CSV output path (default: stdout)")
    ap.add_argument("--construction-out", default=None,
                    help="Construction-items CSV output. Items missing in interview transcripts are written as null.")
    args = ap.parse_args()

    paths = [Path(p) for p in args.paths]
    eval_rows = [parse_transcript(p, ITEMS) for p in paths]
    eval_fields = ["participant_id"] + [iid for iid, _, _ in ITEMS]
    write_csv(eval_rows, eval_fields, args.out)

    if args.construction_out:
        cons_rows = [parse_transcript(p, CONSTRUCTION_ITEMS) for p in paths]
        cons_fields = ["participant_id"] + [iid for iid, _, _ in CONSTRUCTION_ITEMS]
        write_csv(cons_rows, cons_fields, args.construction_out)


if __name__ == "__main__":
    main()
