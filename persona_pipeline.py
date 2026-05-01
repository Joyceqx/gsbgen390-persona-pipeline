"""
persona_pipeline.py — Mini-replication of Park et al. (2024) generative-agent persona.

Two-arm design (after pivots forced by Cookiy's 15-min cap and no cross-study pairing):

    STUDY 1 (interview arm, N=2): combined session — ~9 min open interview
        + ~6 min held-out eval read by the same moderator. Pipeline splits the
        transcript and runs Conditions A (demographics), B (self-description from
        probe 1), C (interview transcript) per respondent.

    STUDY 2 (survey arm, N=1): structured Cookiy interview — 18 construction
        items + same 15 eval items. Pipeline splits, parses each construction
        answer, and runs Conditions A (demographics extracted from construction)
        and D (full construction-survey-conditioned persona).

Self-consistency: each item asked twice per condition at temp 0.7; we report
both accuracy-vs-truth and self-consistency.

Default model: gpt-4o-2024-08-06 (matches Park 2024). Override with $MODEL.

Inputs (all under $GSBGEN390_DIR, default /Users/joyce/Documents/GSBGEN390/):
    eval_battery.json                          — 15-item eval
    construction_battery.json                  — 18-item construction (Study 2 only)
    responses/R{N}/transcript.txt              — Study 1 transcripts
    responses/R{N}/demographics.json           — optional demographic metadata
    responses_s2/R{N}/transcript.txt           — Study 2 transcripts

Outputs (also under $GSBGEN390_DIR):
    derived/{arm}/R{N}/                        — extracted segments + truth answers
        interview_text.txt                     — Study 1 only
        construction_answers.json              — Study 2 only
        truth_answers.json                     — both
        persona_description.txt                — Study 1 only
    persona_answers/{arm}/R{N}_{cond}.json     — primary + samples per condition
    metrics_per_respondent.json
    metrics_aggregate.json
    metrics_table.md
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, stdev
from typing import Any

WORK = Path(os.environ.get(
    "GSBGEN390_DIR",
    "/Users/joyce/Documents/GSBGEN390",
))
BATTERY_PATH = WORK / "eval_battery.json"
CONSTRUCTION_PATH = WORK / "construction_battery.json"
S1_DIR = WORK / "responses"
S2_DIR = WORK / "responses_s2"
DERIVED = WORK / "derived"
ANSWERS = WORK / "persona_answers"

DEFAULT_MODEL = os.environ.get("MODEL", "gpt-4o-2024-08-06")
DEFAULT_TEMPERATURE = 0.7
N_SAMPLES = 2


# ---------------------------------------------------------------------------
# Battery loaders
# ---------------------------------------------------------------------------

@dataclass
class Item:
    section_id: str
    item_id: str
    text: str
    answer_format: str  # "likert_5", "likert_7", "categorical", "numeric", "free_text"
    options: list[str] | None = None
    trait: str | None = None
    reverse: bool = False
    stem_anchor: str = ""  # phrase for finding this item in a transcript


def load_eval_battery(path: Path = BATTERY_PATH) -> list[Item]:
    """Load eval battery. Each item must have an explicit `anchor` field
    chosen to be a robust transcript-search phrase."""
    data = json.loads(path.read_text())
    items: list[Item] = []
    for section in data["sections"]:
        sid = section["id"]
        if sid == "bfi10":
            stem = section["stem"]
            for it in section["items"]:
                items.append(Item(
                    section_id=sid,
                    item_id=it["id"],
                    text=f"{stem} {it['text']}",
                    answer_format="likert_5",
                    trait=it["trait"],
                    reverse=it["reverse"],
                    stem_anchor=it.get("anchor", it["text"]),
                ))
        elif sid == "consumer":
            for it in section["items"]:
                items.append(Item(
                    section_id=sid,
                    item_id=it["id"],
                    text=it["text"],
                    answer_format="likert_5",
                    stem_anchor=it.get("anchor", it["text"][:40]),
                ))
        elif sid == "gss":
            for it in section["items"]:
                scale = it["scale"]
                if scale == "numeric_hours":
                    fmt = "numeric"; opts = None
                elif isinstance(scale, list) and all(s.isdigit() for s in scale):
                    fmt = "likert_7"; opts = list(scale)
                else:
                    fmt = "categorical"; opts = list(scale)
                items.append(Item(
                    section_id=sid,
                    item_id=it["id"],
                    text=it["text"],
                    answer_format=fmt,
                    options=opts,
                    stem_anchor=it.get("anchor", it["text"][:50]),
                ))
    return items


def load_construction_battery(path: Path = CONSTRUCTION_PATH) -> list[Item]:
    """Construction battery for Study 2. If the file doesn't exist yet,
    derive items from the inlined definition below (so we can refactor
    pipeline first, generate construction_battery.json second)."""
    if not path.exists():
        return _default_construction_items()
    data = json.loads(path.read_text())
    items: list[Item] = []
    for it in data["items"]:
        items.append(Item(
            section_id=it.get("category", "construction"),
            item_id=it["id"],
            text=it["text"],
            answer_format=it["format"],
            options=it.get("options"),
            stem_anchor=it.get("anchor", it["text"][:50]),
        ))
    return items


def _default_construction_items() -> list[Item]:
    """Fallback if construction_battery.json is missing — mirrors cookiy_brief_study2.md."""
    return [
        Item("demographic", "c_age",       "Age range",        "categorical", ["18-24","25-34","35-44","45-54","55+"], stem_anchor="Which age range applies"),
        Item("demographic", "c_gender",    "Gender",           "categorical", ["man","woman","non-binary","prefer not to say"], stem_anchor="describe your gender"),
        Item("demographic", "c_education", "Education",        "categorical", ["high school","some college","bachelor's","master's","doctorate"], stem_anchor="highest level of education"),
        Item("demographic", "c_income",    "Household income", "categorical", ["under 50","50 to 100","100 to 200","over 200"], stem_anchor="household's annual income"),
        Item("demographic", "c_region",    "US region",        "categorical", ["Northeast","Midwest","South","West"], stem_anchor="Which US region"),
        Item("behavioral",  "c_workhrs",   "Work hours",       "categorical", ["under 20","20 to 40","40 to 60","over 60"], stem_anchor="hours per week do you typically work"),
        Item("behavioral",  "c_exercise",  "Exercise freq",    "categorical", ["never","monthly","weekly","several times per week","daily"], stem_anchor="how often do you exercise"),
        Item("behavioral",  "c_socmedia",  "Social media hrs", "categorical", ["under 1","1 to 2","2 to 4","4 or more"], stem_anchor="hours per day do you typically spend on social media"),
        Item("behavioral",  "c_voted",     "Voted last election","categorical", ["yes","no","not eligible"], stem_anchor="vote in the last presidential election"),
        Item("behavioral",  "c_relattend", "Religious attendance","categorical", ["never","special occasions","monthly","weekly or more"], stem_anchor="attend religious services"),
        Item("psychological","c_risk",     "Risk tolerance",   "categorical", ["A","B"], stem_anchor="guaranteed 500 dollars"),
        Item("psychological","c_planning", "Planning style",   "likert_5", stem_anchor="plan my day in advance"),
        Item("psychological","c_optimism", "Optimism",         "likert_5", stem_anchor="optimistic about how my next 5 years"),
        Item("psychological","c_decstyle", "Decision style",   "likert_5", stem_anchor="research extensively before making important decisions"),
        Item("attitudinal", "c_priority", "Life priority",     "categorical", ["A","B","C","D","E"], stem_anchor="matters most to you right now"),
        Item("attitudinal", "c_tradition","Tradition",         "likert_5", stem_anchor="prefer maintaining tradition"),
        Item("attitudinal", "c_indiv_comm","Individualism",    "likert_5", stem_anchor="individuals look after themselves"),
        Item("attitudinal", "c_inst_trust","Institutional trust","likert_5", stem_anchor="trust major institutions"),
    ]


# ---------------------------------------------------------------------------
# Transcript splitting + answer parsing
# ---------------------------------------------------------------------------

# Phrases that mark transition into the structured eval section. Multiple
# variants because the moderator may paraphrase slightly across respondents.
EVAL_TRANSITION_ANCHORS = [
    "structured rating section",
    "fifteen short statements",
    "fifteen more short statements",
    "switch to a structured",
    "structured survey",  # Study 2 opener
]

# For Study 2, the boundary between construction (Section 1) and eval (Section 2).
S2_EVAL_TRANSITION_ANCHORS = [
    "fifteen more short statements",
    "for the last few minutes",
    "same format as before",
]


def find_first_anchor(text: str, anchors: list[str]) -> int:
    """Return the character index of the first matching anchor phrase, or -1."""
    text_l = text.lower()
    best = -1
    for a in anchors:
        idx = text_l.find(a.lower())
        if idx != -1 and (best == -1 or idx < best):
            best = idx
    return best


# Eval-section detection by question-stem phrases that ALWAYS appear in the eval segment
# regardless of how the moderator paraphrased the transition.
EVAL_STEM_PHRASES = [
    "is reserved",
    "generally trusting",
    "tends to be lazy",
    "tend to be lazy",
    "is generally a trusting",
    "see yourself as someone who is reserved",
]


def split_study1_transcript(text: str) -> tuple[str, str]:
    """Split combined-session transcript into (interview_material, eval_qa).

    Strategy: look for any of the eval question stems. The earliest occurrence
    of an eval stem in moderator text marks where Section 2 (eval) starts.
    Fallback to verbal-transition anchors, then to 60% heuristic.
    """
    # Strategy 1: find earliest eval stem
    text_lower = text.lower()
    earliest = -1
    for stem in EVAL_STEM_PHRASES:
        i = text_lower.find(stem.lower())
        if i != -1 and (earliest == -1 or i < earliest):
            earliest = i
    if earliest != -1:
        # Back up to start of that line so we don't split mid-sentence
        line_start = text.rfind("\n", 0, earliest)
        idx = line_start + 1 if line_start != -1 else earliest
        return text[:idx].strip(), text[idx:].strip()
    # Strategy 2: verbal transition anchor
    idx = find_first_anchor(text, EVAL_TRANSITION_ANCHORS)
    if idx == -1:
        idx = int(len(text) * 0.6)
        print("WARN: No eval-transition anchor found; using 60% heuristic split.")
    return text[:idx].strip(), text[idx:].strip()


def split_study2_transcript(text: str) -> tuple[str, str]:
    """Split structured-only transcript into (construction_qa, eval_qa).
    Same eval-stem strategy as Study 1.
    """
    text_lower = text.lower()
    earliest = -1
    for stem in EVAL_STEM_PHRASES:
        i = text_lower.find(stem.lower())
        if i != -1 and (earliest == -1 or i < earliest):
            earliest = i
    if earliest != -1:
        line_start = text.rfind("\n", 0, earliest)
        idx = line_start + 1 if line_start != -1 else earliest
        return text[:idx].strip(), text[idx:].strip()
    idx = find_first_anchor(text, S2_EVAL_TRANSITION_ANCHORS)
    if idx == -1:
        idx = int(len(text) * 0.55)
        print("WARN: No S2 transition anchor found; using 55% heuristic split.")
    return text[:idx].strip(), text[idx:].strip()


# Capture the participant's response after a stem appears in moderator text.
# The transcript probably has speaker labels — we tolerate variation.
SPEAKER_PATTERNS = [
    r"^(?P<speaker>moderator|interviewer|cookiy|host)[:\s\-]",
    r"^(?P<speaker>participant|respondent|user|interviewee)[:\s\-]",
]


def parse_utterances(text: str) -> list[tuple[str, str]]:
    """Best-effort split into (role, utterance) pairs.

    role ∈ {'moderator','participant','unknown'}.
    Tolerates: 'MODERATOR:', 'Moderator -', '[00:15] Moderator:', etc.
    Falls back to alternating-speaker assumption if no labels found.
    """
    lines = text.splitlines()
    utterances: list[tuple[str, str]] = []
    current_role: str | None = None
    buf: list[str] = []

    moderator_re = re.compile(
        r"^\s*(?:\[[\d:]+\]\s*)?(moderator|interviewer|cookiy|host|ai|assistant|a)\s*[:\-–]\s*",
        re.IGNORECASE,
    )
    participant_re = re.compile(
        r"^\s*(?:\[[\d:]+\]\s*)?(participant|respondent|user|interviewee|p\d*|r\d*|joyce)\b\s*[:\-–]?\s*",
        re.IGNORECASE,
    )

    def flush():
        if current_role and buf:
            utterances.append((current_role, " ".join(buf).strip()))
        buf.clear()

    for line in lines:
        m_mod = moderator_re.match(line)
        m_par = participant_re.match(line)
        if m_mod:
            flush()
            current_role = "moderator"
            buf.append(moderator_re.sub("", line))
        elif m_par:
            flush()
            current_role = "participant"
            buf.append(participant_re.sub("", line))
        else:
            buf.append(line)
    flush()

    if not utterances or all(r == "unknown" for r, _ in utterances):
        # Fallback: chunked alternation. Treat as one big participant utterance.
        return [("participant", text.strip())]
    return utterances


def find_answer_after_stem(transcript_text: str,
                           stem: str,
                           max_chars_after: int = 400) -> str:
    """Find stem in transcript, return next participant utterance (or chunk).

    Robust to speaker-label parsing succeeding or failing.
    """
    utterances = parse_utterances(transcript_text)
    stem_l = stem.lower()
    # Pass 1: structured — find moderator utterance containing stem, return next participant utterance.
    for i, (role, txt) in enumerate(utterances):
        if role == "moderator" and stem_l in txt.lower():
            for j in range(i + 1, len(utterances)):
                if utterances[j][0] == "participant":
                    return utterances[j][1].strip()
            break
    # Pass 2: unstructured — find stem in raw text, capture next chars.
    text_l = transcript_text.lower()
    idx = text_l.find(stem_l)
    if idx == -1:
        return ""
    after = transcript_text[idx + len(stem):][:max_chars_after]
    # Try to isolate the participant utterance: stop at next speaker tag.
    for label in ["MODERATOR", "Moderator", "Interviewer", "INTERVIEWER", "Cookiy"]:
        end = after.find(label)
        if end != -1:
            after = after[:end]
    return after.strip(" \n\t.:?;,")


def parse_answers_from_qa(qa_text: str, items: list[Item]) -> dict[str, str]:
    """For each item, anchor on stem and extract the participant's answer."""
    answers: dict[str, str] = {}
    for it in items:
        ans = find_answer_after_stem(qa_text, it.stem_anchor)
        if ans:
            answers[it.item_id] = ans
    return answers


def extract_self_description(interview_text: str) -> str:
    """Pull Probe 1's answer (self-description) from the interview portion."""
    anchors = [
        "describe yourself to a stranger",
        "paragraph about who you are",
        "who you are — like how you'd describe",
        "describe yourself",
        # Real-Cookiy paraphrases observed in transcripts:
        "a little bit about yourself",
        "tell me a little",
        "tell me a bit about yourself",
        "in a short paragraph, who are you",
        "what's going on in your life",
    ]
    idx = find_first_anchor(interview_text, anchors)
    if idx == -1:
        return ""
    chunk = interview_text[idx:][:1500]
    utterances = parse_utterances(chunk)
    # Concatenate consecutive participant turns after the anchor question turn
    parts = []
    seen_first_user = False
    for role, txt in utterances:
        if role == "participant":
            parts.append(txt.strip())
            seen_first_user = True
        elif seen_first_user:
            # Hit a moderator turn after we've collected user turns — stop
            break
    if parts:
        return " ".join(parts)
    # Fallback: just return the chunk after the anchor
    return chunk.split("\n", 2)[-1].strip()


# ---------------------------------------------------------------------------
# Persona prompt construction
# ---------------------------------------------------------------------------

PERSONA_SYSTEM_RULES = """\
You are role-playing as a specific real person, on the basis of the materials below.
When given a question, answer ENTIRELY IN CHARACTER as that person.

Rules:
- Always commit to a single answer. No "it depends" hedges, no refusals.
- For Likert 1-5 items, output ONLY a single integer 1-5.
- For Likert 1-7 items, output ONLY a single integer 1-7.
- For categorical items, output the exact option text from the provided choices.
- For numeric items, output a single number.
- Use only the materials below + reasonable inference about a person's consistent self.
- If the materials are silent on the question, infer from the personality and values
  the materials DO show, and pick the answer most consistent with that pattern."""


def build_persona_prompt(condition: str,
                         demographics: dict | None = None,
                         description: str | None = None,
                         interview_text: str | None = None,
                         construction_answers: dict[str, str] | None = None,
                         construction_items: list[Item] | None = None) -> str:
    parts = [PERSONA_SYSTEM_RULES, "", "---", "MATERIALS ABOUT THE PERSON YOU ARE PLAYING:", ""]

    if demographics:
        parts.append("## Demographics")
        for k, v in demographics.items():
            if k.startswith("_"):
                continue
            parts.append(f"- {k}: {v}")
        parts.append("")

    if description:
        parts.append("## Persona description (in their own words)")
        parts.append(description.strip())
        parts.append("")

    if interview_text:
        parts.append("## Interview transcript (life history, values, decisions, etc.)")
        parts.append(interview_text.strip())
        parts.append("")

    if construction_answers and construction_items:
        parts.append("## Self-reported survey responses")
        item_lookup = {it.item_id: it for it in construction_items}
        for cid, ans in construction_answers.items():
            it = item_lookup.get(cid)
            if it:
                parts.append(f"- [{it.section_id}] {it.text}: {ans}")
        parts.append("")

    parts += ["---", f"Condition: {condition}"]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Per-question prompt format
# ---------------------------------------------------------------------------

def format_item_question(item: Item) -> str:
    if item.answer_format == "likert_5":
        return (f"Item ({item.section_id}/{item.item_id}): {item.text}\n"
                f"Scale: 1=Strongly disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly agree.\n"
                f"Answer with ONLY a single integer 1-5.")
    if item.answer_format == "likert_7":
        return (f"Item ({item.section_id}/{item.item_id}): {item.text}\n"
                f"Answer with ONLY a single integer 1-7.")
    if item.answer_format == "categorical":
        opts = " / ".join(item.options or [])
        return (f"Item ({item.section_id}/{item.item_id}): {item.text}\n"
                f"Choose ONE option, output the option text exactly: {opts}")
    if item.answer_format == "numeric":
        return (f"Item ({item.section_id}/{item.item_id}): {item.text}\n"
                f"Answer with a single number.")
    return f"Item ({item.section_id}/{item.item_id}): {item.text}"


# ---------------------------------------------------------------------------
# LLM dispatch
# ---------------------------------------------------------------------------

def _is_openai(m: str) -> bool:
    return m.startswith(("gpt-", "o1-", "o3-", "o4-"))


def _is_anthropic(m: str) -> bool:
    return m.startswith("claude-")


def _call_openai(system: str, user: str, model: str, temperature: float) -> str:
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model, max_tokens=400, temperature=temperature,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return (resp.choices[0].message.content or "").strip()


def _call_anthropic(system: str, user: str, model: str, temperature: float) -> str:
    from anthropic import Anthropic
    client = Anthropic()
    resp = client.messages.create(
        model=model, max_tokens=400, temperature=temperature,
        system=system, messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


def call_llm(system: str, user: str,
             model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE) -> str:
    if _is_openai(model):
        return _call_openai(system, user, model, temperature)
    if _is_anthropic(model):
        return _call_anthropic(system, user, model, temperature)
    raise ValueError(f"Unknown model provider for '{model}'.")


def run_condition(name: str, system: str, items: list[Item],
                  model: str = DEFAULT_MODEL, n_samples: int = N_SAMPLES,
                  temperature: float = DEFAULT_TEMPERATURE):
    primary, samples = {}, {}
    for it in items:
        q = format_item_question(it)
        ss = [call_llm(system, q, model, temperature) for _ in range(n_samples)]
        primary[it.item_id] = ss[0]
        samples[it.item_id] = ss
        first_short = ss[0][:60].replace("\n", " ")
        ok = "✓" if (len(ss) > 1 and ss[0].strip() == ss[1].strip()) else "✗" if len(ss) > 1 else "·"
        print(f"  [{name}] {it.item_id}: {first_short}  ({ok})")
    return primary, samples


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def parse_likert(s: str, lo: int = 1, hi: int = 5) -> int | None:
    if not s: return None
    for n in re.findall(r"-?\d+", s):
        v = int(n)
        if lo <= v <= hi:
            return v
    return None


def parse_numeric(s: str) -> float | None:
    if not s: return None
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else None


def normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def categorical_match(predicted: str, truth: str, options: list[str]) -> bool:
    p, t = normalize_text(predicted), normalize_text(truth)
    if not p or not t: return False
    for opt in options:
        no = normalize_text(opt)
        if no in p and no in t:
            return True
    return p == t or p.startswith(t) or t.startswith(p)


@dataclass
class ConditionMetrics:
    arm: str = ""
    respondent: str = ""
    name: str = ""
    n_items: int = 0
    likert_mae: float = 0.0
    likert_within1: float = 0.0
    categorical_acc: float = 0.0
    bfi_trait_distance: float = 0.0
    likert_self_mae: float = 0.0
    categorical_self_acc: float = 0.0
    per_item: dict[str, dict[str, Any]] = field(default_factory=dict)


def bfi_trait_scores(answers: dict[str, str], items: list[Item]) -> dict[str, float]:
    by_trait: dict[str, list[float]] = {}
    for it in items:
        if it.section_id != "bfi10":
            continue
        v = parse_likert(answers.get(it.item_id, ""))
        if v is None: continue
        if it.reverse: v = 6 - v
        by_trait.setdefault(it.trait, []).append(v)
    return {t: mean(vs) for t, vs in by_trait.items() if vs}


def score_condition(arm: str, respondent: str, name: str,
                    persona_answers: dict[str, str],
                    persona_samples: dict[str, list[str]],
                    truth_answers: dict[str, str],
                    items: list[Item]) -> ConditionMetrics:
    m = ConditionMetrics(arm=arm, respondent=respondent, name=name)
    likert_errs, num_errs = [], []
    cat_correct = cat_total = 0
    likert_self_errs = []
    cat_self_correct = cat_self_total = 0

    for it in items:
        if it.item_id not in persona_answers or it.item_id not in truth_answers:
            continue
        p_raw = persona_answers[it.item_id]
        t_raw = truth_answers[it.item_id]
        m.per_item[it.item_id] = {"truth": t_raw, "persona": p_raw}
        all_s = persona_samples.get(it.item_id, [p_raw])

        if it.answer_format in ("likert_5", "likert_7"):
            hi = 5 if it.answer_format == "likert_5" else 7
            p = parse_likert(p_raw, 1, hi)
            t = parse_likert(t_raw, 1, hi)
            if p is not None and t is not None:
                likert_errs.append(abs(p - t))
                m.per_item[it.item_id]["err"] = abs(p - t)
            sv = [parse_likert(s, 1, hi) for s in all_s]
            sv = [v for v in sv if v is not None]
            if len(sv) >= 2:
                likert_self_errs.append(abs(sv[0] - sv[1]))
        elif it.answer_format == "categorical":
            cat_total += 1
            ok = categorical_match(p_raw, t_raw, it.options or [])
            cat_correct += int(ok)
            m.per_item[it.item_id]["match"] = ok
            if len(all_s) >= 2:
                cat_self_total += 1
                cat_self_correct += int(categorical_match(all_s[0], all_s[1], it.options or []))
        elif it.answer_format == "numeric":
            p, t = parse_numeric(p_raw), parse_numeric(t_raw)
            if p is not None and t is not None:
                num_errs.append(abs(p - t))

    m.n_items = sum(1 for it in items if it.item_id in persona_answers)
    if likert_errs:
        m.likert_mae = mean(likert_errs)
        m.likert_within1 = sum(1 for e in likert_errs if e <= 1) / len(likert_errs)
    if cat_total:
        m.categorical_acc = cat_correct / cat_total
    if likert_self_errs:
        m.likert_self_mae = mean(likert_self_errs)
    if cat_self_total:
        m.categorical_self_acc = cat_self_correct / cat_self_total

    p_traits = bfi_trait_scores(persona_answers, items)
    t_traits = bfi_trait_scores(truth_answers, items)
    if p_traits and t_traits:
        common = set(p_traits) & set(t_traits)
        if common:
            m.bfi_trait_distance = (sum((p_traits[t] - t_traits[t]) ** 2 for t in common) / len(common)) ** 0.5
    return m


# ---------------------------------------------------------------------------
# Demographics extraction (Study 2: from construction answers)
# ---------------------------------------------------------------------------

def construction_to_demographics(answers: dict[str, str]) -> dict[str, str]:
    """Build a Demographics dict from the demographic block of a construction survey."""
    return {
        "age_range": answers.get("c_age", "unknown"),
        "gender": answers.get("c_gender", "unknown"),
        "education": answers.get("c_education", "unknown"),
        "income_range": answers.get("c_income", "unknown"),
        "region": answers.get("c_region", "unknown"),
    }


# ---------------------------------------------------------------------------
# CSV-truth override (use the audited eval_answers_extracted.csv as gold truth)
# ---------------------------------------------------------------------------

# Maps internal respondent_dir name -> participant_id used in eval_answers_extracted.csv
RESPONDENT_TO_CSV_ID = {
    ("study1", "R1"): "study1_interview_p1",
    ("study1", "R2"): "study1_interview_p2",
    ("study2", "R1"): "study2_survey_p1",
}


def truth_from_csv(arm: str, respondent: str) -> dict[str, str]:
    """Look up the audited truth row for this respondent. Returns empty dict if not found."""
    import csv
    csv_path = WORK / "eval_answers_extracted.csv"
    if not csv_path.exists():
        return {}
    target_pid = RESPONDENT_TO_CSV_ID.get((arm, respondent))
    if not target_pid:
        return {}
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            if row.get("participant_id") == target_pid:
                return {k: v for k, v in row.items() if k != "participant_id" and v not in (None, "")}
    return {}


# ---------------------------------------------------------------------------
# Per-respondent runners
# ---------------------------------------------------------------------------

def process_study1_respondent(resp_dir: Path, eval_items: list[Item]) -> list[ConditionMetrics]:
    """Run Conditions A, B, C on one Study 1 respondent."""
    respondent = resp_dir.name
    print(f"\n--- Study 1 / {respondent} ---")
    transcript_path = resp_dir / "transcript.txt"
    if not transcript_path.exists():
        print(f"  SKIP: no transcript at {transcript_path}")
        return []
    transcript = transcript_path.read_text()
    interview_text, eval_qa = split_study1_transcript(transcript)
    # Override with audited CSV truth (gold signal) if available, otherwise fall back to internal parser.
    csv_truth = truth_from_csv("study1", respondent)
    if csv_truth:
        truth = csv_truth
        print(f"  Truth source: eval_answers_extracted.csv ({len(truth)} items)")
    else:
        truth = parse_answers_from_qa(eval_qa, eval_items)
        print(f"  Truth source: internal parser ({len(truth)}/{len(eval_items)} parsed)")

    description = extract_self_description(interview_text)
    if not description:
        print("  WARN: could not extract self-description from probe 1.")

    demo_path = resp_dir / "demographics.json"
    demographics = json.loads(demo_path.read_text()) if demo_path.exists() else {"respondent_id": respondent}

    derived_dir = DERIVED / "study1" / respondent
    derived_dir.mkdir(parents=True, exist_ok=True)
    (derived_dir / "interview_text.txt").write_text(interview_text)
    (derived_dir / "truth_answers.json").write_text(json.dumps(truth, indent=2))
    (derived_dir / "persona_description.txt").write_text(description)

    conditions = [
        ("A_demographic_only", build_persona_prompt("demographic_only", demographics=demographics)),
        ("B_persona_description", build_persona_prompt("persona_description",
                                                       demographics=demographics, description=description)),
        ("C_interview", build_persona_prompt("interview",
                                             demographics=demographics, interview_text=interview_text)),
    ]
    metrics_list: list[ConditionMetrics] = []
    for cond_name, system in conditions:
        primary, samples = run_condition(f"S1/{respondent}/{cond_name}", system, eval_items)
        ans_dir = ANSWERS / "study1"
        ans_dir.mkdir(parents=True, exist_ok=True)
        (ans_dir / f"{respondent}_{cond_name}.json").write_text(json.dumps({
            "primary": primary, "samples": samples}, indent=2))
        m = score_condition("study1", respondent, cond_name, primary, samples, truth, eval_items)
        metrics_list.append(m)
    return metrics_list


def process_study2_respondent(resp_dir: Path,
                              eval_items: list[Item],
                              construction_items: list[Item]) -> list[ConditionMetrics]:
    """Run Conditions A and D on one Study 2 respondent."""
    respondent = resp_dir.name
    print(f"\n--- Study 2 / {respondent} ---")
    transcript_path = resp_dir / "transcript.txt"
    if not transcript_path.exists():
        print(f"  SKIP: no transcript at {transcript_path}")
        return []
    transcript = transcript_path.read_text()
    construction_qa, eval_qa = split_study2_transcript(transcript)
    construction = parse_answers_from_qa(construction_qa, construction_items)
    # Override eval truth with the audited CSV.
    csv_truth = truth_from_csv("study2", respondent)
    if csv_truth:
        truth = csv_truth
        print(f"  Truth source: eval_answers_extracted.csv ({len(truth)} items)")
    else:
        truth = parse_answers_from_qa(eval_qa, eval_items)
        print(f"  Truth source: internal parser ({len(truth)}/{len(eval_items)} parsed)")
    print(f"  Construction: {len(construction)}/{len(construction_items)} items")

    demographics = construction_to_demographics(construction)

    derived_dir = DERIVED / "study2" / respondent
    derived_dir.mkdir(parents=True, exist_ok=True)
    (derived_dir / "construction_answers.json").write_text(json.dumps(construction, indent=2))
    (derived_dir / "truth_answers.json").write_text(json.dumps(truth, indent=2))

    conditions = [
        ("A_demographic_only", build_persona_prompt("demographic_only", demographics=demographics)),
        ("D_survey_conditioned", build_persona_prompt("survey_conditioned",
                                                       demographics=demographics,
                                                       construction_answers=construction,
                                                       construction_items=construction_items)),
    ]
    metrics_list: list[ConditionMetrics] = []
    for cond_name, system in conditions:
        primary, samples = run_condition(f"S2/{respondent}/{cond_name}", system, eval_items)
        ans_dir = ANSWERS / "study2"
        ans_dir.mkdir(parents=True, exist_ok=True)
        (ans_dir / f"{respondent}_{cond_name}.json").write_text(json.dumps({
            "primary": primary, "samples": samples}, indent=2))
        m = score_condition("study2", respondent, cond_name, primary, samples, truth, eval_items)
        metrics_list.append(m)
    return metrics_list


# ---------------------------------------------------------------------------
# Aggregation + reporting
# ---------------------------------------------------------------------------

def aggregate_within_arm(metrics: list[ConditionMetrics], arm: str, condition: str) -> dict[str, float]:
    rows = [m for m in metrics if m.arm == arm and m.name == condition]
    if not rows:
        return {}
    out = {"n_respondents": len(rows)}
    for field in ["likert_mae", "likert_within1", "categorical_acc",
                  "bfi_trait_distance", "likert_self_mae", "categorical_self_acc"]:
        vals = [getattr(r, field) for r in rows]
        out[field + "_mean"] = round(mean(vals), 3)
        if len(vals) > 1:
            out[field + "_sd"] = round(stdev(vals), 3)
    return out


def write_metrics(all_metrics: list[ConditionMetrics]):
    per_resp = [{
        "arm": m.arm, "respondent": m.respondent, "condition": m.name, "n_items": m.n_items,
        "likert_mae": round(m.likert_mae, 3),
        "likert_within_1_pct": round(100 * m.likert_within1, 1),
        "categorical_acc_pct": round(100 * m.categorical_acc, 1),
        "bfi_trait_rmse": round(m.bfi_trait_distance, 3),
        "likert_self_mae": round(m.likert_self_mae, 3),
        "categorical_self_match_pct": round(100 * m.categorical_self_acc, 1),
    } for m in all_metrics]
    (WORK / "metrics_per_respondent.json").write_text(json.dumps(per_resp, indent=2))

    # Aggregate per (arm, condition)
    arms_conds = sorted({(m.arm, m.name) for m in all_metrics})
    agg = {f"{a}/{c}": aggregate_within_arm(all_metrics, a, c) for a, c in arms_conds}
    (WORK / "metrics_aggregate.json").write_text(json.dumps(agg, indent=2))

    rows = [
        f"Model: {DEFAULT_MODEL} · Temperature: {DEFAULT_TEMPERATURE} · N_SAMPLES: {N_SAMPLES}",
        "",
        "## Per-respondent",
        "",
        "| Arm | R | Condition | n | Likert MAE | within ±1 | Cat. acc. | BFI RMSE | Self-MAE | Self-match |",
        "|-----|---|-----------|---|-----------|-----------|-----------|----------|----------|------------|",
    ]
    for m in all_metrics:
        rows.append(
            f"| {m.arm} | {m.respondent} | {m.name} | {m.n_items} | "
            f"{m.likert_mae:.2f} | {100*m.likert_within1:.0f}% | {100*m.categorical_acc:.0f}% | "
            f"{m.bfi_trait_distance:.2f} | {m.likert_self_mae:.2f} | {100*m.categorical_self_acc:.0f}% |"
        )
    rows += ["", "## Aggregate (within arm × condition)", ""]
    rows.append("| Arm/Condition | n | Likert MAE | Cat. acc. | BFI RMSE |")
    rows.append("|---------------|---|-----------|-----------|----------|")
    def _fmt(val, fmt=":.3f"):
        if isinstance(val, (int, float)):
            return f"{val:{fmt[1:]}}" if fmt.startswith(":") else str(val)
        return "-"
    for k, v in agg.items():
        if not v: continue
        rows.append(
            f"| {k} | {v.get('n_respondents','-')} | "
            f"{_fmt(v.get('likert_mae_mean'))} | "
            f"{_fmt(v.get('categorical_acc_mean'))} | "
            f"{_fmt(v.get('bfi_trait_distance_mean'))} |"
        )
    (WORK / "metrics_table.md").write_text("\n".join(rows))
    print("\n".join(rows))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main():
    print(f"Model: {DEFAULT_MODEL}   Temperature: {DEFAULT_TEMPERATURE}   N_SAMPLES: {N_SAMPLES}")
    print(f"Working directory: {WORK}")

    eval_items = load_eval_battery()
    construction_items = load_construction_battery()
    print(f"Eval items: {len(eval_items)}.  Construction items: {len(construction_items)}.")

    all_metrics: list[ConditionMetrics] = []

    # Study 1
    for resp_dir in sorted(S1_DIR.glob("R*")) if S1_DIR.exists() else []:
        if (resp_dir / "transcript.txt").exists():
            all_metrics.extend(process_study1_respondent(resp_dir, eval_items))

    # Study 2
    for resp_dir in sorted(S2_DIR.glob("R*")) if S2_DIR.exists() else []:
        if (resp_dir / "transcript.txt").exists():
            all_metrics.extend(process_study2_respondent(resp_dir, eval_items, construction_items))

    if not all_metrics:
        print("\nNo respondents processed. Drop transcripts into responses/R*/ or responses_s2/R*/ and re-run.")
        return

    write_metrics(all_metrics)


if __name__ == "__main__":
    main()
