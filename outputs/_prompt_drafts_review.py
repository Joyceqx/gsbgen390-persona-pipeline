"""Render P0 / P1 / P2 prompts on the seed=42 respondent #0 for Joyce review (v2).

v2 changes (per Joyce's "match the literature" feedback):
- P1 follows Argyle 2023's per-variable 1st-person sentence style with category
  openers ("Racially, I am X.", "Ideologically, I am X."). Generic fallback for
  long-tail variables cleans GSS's "r/r's/rs" abbreviations to "I/my/my".
- P2 follows Wang 2025's "What is your X? My X is Y." Q&A style. Same cleanup
  for long-tail variables.
- A per-variable TEMPLATES dict covers the 12 primary_eval items + core
  demographics + high-density behaviors + all psychological + the most common
  attitudinal-bin items, ~50 vars total. Joyce can extend this dict directly.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/Users/joyce/Developer/gsbgen390/src")

import pandas as pd
from gss_loader import load_gss, get_variable_label, get_value_label
from gss_pipeline import (
    sample_respondents,
    build_persona_prompt,
    BIN_DISPLAY,
    _is_non_substantive_label,
)

WORK = Path("/Users/joyce/Developer/gsbgen390")


# ============================================================================
# Per-variable templates for high-priority vars (~50 of 140)
#
# TEMPLATES[varname] = (p1_template, p2_question)
#   p1_template uses {val} as the value-label placeholder.
#   p2_question is the interviewer's question (always paired with
#     "Respondent: My {phrase} is {val}." or a per-template Respondent line).
#
# For vars NOT in TEMPLATES we fall back to a cleaned generic.
# ============================================================================

# Helper: Argyle-style category openers for variables where they read well.
# (P1: "Racially, I am X.", "Ideologically, I am X.", "Politically, I am X.")

TEMPLATES: dict[str, tuple[str, str]] = {
    # ---- Core demographics ----
    "AGE": ("I am {val} years old.", "How old are you?"),
    "SEX": ("I am {val}.", "What is your sex?"),
    "RACE": ("Racially, I am {val}.", "What is your race?"),
    "MARITAL": ("My marital status is {val}.", "What is your marital status?"),
    "DEGREE": ("My highest degree is {val}.", "What is your highest degree?"),
    "EDUC": ("My highest year of school completed is {val}.", "How many years of school have you completed?"),
    "INCOME": ("My total family income is {val}.", "What is your total family income?"),
    "INCOME16": ("When I was 16, my family income was {val}.", "What was your family income when you were 16?"),
    "REGION": ("I live in the {val} region.", "What region of the country do you live in?"),
    "REG16": ("At age 16, I lived in the {val} region.", "What region did you live in at age 16?"),
    "HISPANIC": ("Ethnically, I am {val}.", "Are you Hispanic?"),
    "BORN": ("As to being born in this country, my answer is {val}.", "Were you born in this country?"),
    "ETHNIC": ("My country of family origin is {val}.", "What is your country of family origin?"),
    "FAMILY16": ("At age 16, I was living with {val}.", "Who were you living with at age 16?"),
    "MOBILE16": ("Since age 16, my geographic mobility is: {val}.", "How geographically mobile have you been since age 16?"),
    "MADEG": ("My mother's highest degree is {val}.", "What is your mother's highest degree?"),
    "PADEG": ("My father's highest degree is {val}.", "What is your father's highest degree?"),
    "MAEDUC": ("My mother completed {val} years of school.", "How many years of school did your mother complete?"),
    "PAEDUC": ("My father completed {val} years of school.", "How many years of school did your father complete?"),
    "INCOM16": ("When I was 16, my family income was {val}.", "What was your family income when you were 16?"),
    "HOMPOP": ("At age 16, my family {val}.", "Did your family own or rent your home when you were 16?"),

    # ---- High-density behaviors ----
    "ATTEND": ("I attend religious services {val}.", "How often do you attend religious services?"),
    "PRAY": ("As for prayer, I pray {val}.", "How often do you pray?"),
    "RELIG": ("My religious preference is {val}.", "What is your religious preference?"),
    "RELIG16": ("I was raised {val}.", "In what religion were you raised?"),
    "FUND": ("On religious fundamentalism, I am {val}.", "How fundamentalist are you currently?"),
    "NEWS": ("I read the newspaper {val}.", "How often do you read the newspaper?"),
    "TVHOURS": ("I watch about {val} hours of TV per day.", "How many hours of TV do you watch per day?"),
    "HRS1": ("I worked about {val} hours last week.", "How many hours did you work last week?"),
    "WRKSTAT": ("My labor force status is {val}.", "What is your labor force status?"),
    "WRKSLF": ("As to employment type, I am {val}.", "Are you self-employed or do you work for someone?"),
    "OWNGUN": ("As for having a gun in the home, my answer is {val}.", "Do you have a gun in your home?"),
    "HUNT": ("As to hunting, {val}.", "Do you or your spouse hunt?"),
    "USECOMP": ("As to using a computer, my answer is {val}.", "Do you use a computer?"),
    "PRES16": ("In 2016, my voting status was: {val}.", "Did you vote in the 2016 election?"),
    "PRES20": ("In 2020, I voted for {val}.", "Whom did you vote for in 2020?"),
    "VOTE16": ("In 2016, my voting status was: {val}.", "Did you vote in the 2016 election?"),
    "VOTE20": ("In 2020, I {val}.", "Did you vote in the 2020 election?"),
    "TRUST": ("On trust, I think {val}.", "Generally speaking, can most people be trusted?"),
    "JOBLOSE": ("Regarding losing my job, I am {val}.", "How likely are you to lose your job?"),
    "JOBFIND": ("If I lost my job, finding an equally good one would be {val}.", "How easy would it be to find an equally good job?"),

    # ---- Psychological (all 4 in the bin) ----
    "HAPPY": ("In general, I am {val}.", "How would you describe your general happiness?"),
    "HEALTH": ("My health is {val}.", "How would you describe your health?"),
    "LIFE": ("I find life {val}.", "Do you find life exciting or dull?"),
    "SATJOB": ("With my work, I am {val}.", "How satisfied are you with your work?"),

    # ---- 12 primary_eval items (prediction targets — used as features when not held out) ----
    "POLVIEWS": ("Ideologically, I think of myself as {val}.", "How do you think of yourself politically — liberal or conservative?"),
    "PARTYID": ("Politically, I am a {val}.", "What is your party identification?"),
    "ABANY": ("On abortion for any reason, my answer is {val}.", "Should abortion be available for any reason?"),
    "CAPPUN": ("On the death penalty for murder, I am {val}.", "Are you in favor of or opposed to the death penalty for murder?"),
    "GUNLAW": ("On requiring permits for guns, I am {val}.", "Do you favor or oppose requiring permits for guns?"),
    "FECHLD": ("Regarding a working mother being able to establish a warm relationship with her children, I {val}.",
               "Do you agree or disagree that a working mother can have a warm relationship with her children?"),
    "FEPOL": ("Regarding men being better suited emotionally for politics than women, I {val}.",
              "Do you agree or disagree that men are better suited for politics than women?"),
    "RACDIF1": ("On whether racial inequality is due to discrimination, my answer is {val}.",
                "Do you think differences between Black and White people are mainly due to discrimination?"),
    "CONFINAN": ("In banks and financial institutions, I have {val} confidence.", "How much confidence do you have in banks?"),
    "CONLEGIS": ("In Congress, I have {val} confidence.", "How much confidence do you have in Congress?"),
    "HELPPOOR": ("On the government's role in helping the poor, on a 1-5 scale (1 = government should improve, 5 = people should take care of themselves), I am at {val}.",
                  "On a 1-5 scale, where do you place yourself on the government helping the poor?"),
    "SATFIN": ("With my present financial situation, I am {val}.", "How satisfied are you with your present financial situation?"),

    # ---- Common attitudinal items the respondent has ----
    "ABDEFECT": ("If there is a strong chance of serious defect, abortion: {val}.", "Should abortion be available if there is a strong chance of a serious defect?"),
    "ABHLTH":   ("If the woman's health is seriously endangered, abortion: {val}.", "Should abortion be available if the woman's health is endangered?"),
    "ABNOMORE": ("If she is married and wants no more children, abortion: {val}.", "Should abortion be available if she is married and wants no more children?"),
    "ABPOOR":   ("If she has low income and can't afford more children, abortion: {val}.", "Should abortion be available if she has low income?"),
    "ABRAPE":   ("If she became pregnant as a result of rape, abortion: {val}.", "Should abortion be available if she became pregnant as a result of rape?"),
    "ABSINGLE": ("If she is not married, abortion: {val}.", "Should abortion be available if she is not married?"),
    "SPKATH":   ("On allowing an anti-religionist to teach, I would say: {val}.", "Should an anti-religionist be allowed to teach?"),
    "SPKRAC":   ("On allowing a racist to teach, I would say: {val}.", "Should a racist be allowed to teach?"),
    "DISCAFFW": ("As to whether white people are hurt by affirmative action, I think it is {val}.", "Are white people hurt by affirmative action?"),
    "FEFAM":    ("On the statement 'better for man to work, woman tend home', I {val}.",
                 "Do you agree or disagree that it's better for the man to work and the woman to tend home?"),
    "FEHIRE":   ("On hiring and promoting women, I {val}.", "What do you think about hiring and promoting women?"),
    "FEPRESCH": ("On whether preschool children suffer if their mother works, I {val}.",
                  "Do you agree or disagree that preschool children suffer if their mother works?"),
    "HOMOSEX":  ("On homosexual sex relations, I think it is {val}.", "What do you think about homosexual sex relations?"),
    "LETIN1A":  ("On the number of immigrants nowadays, I think it should be {val}.", "Should the number of immigrants be increased or decreased?"),
    "NATCHLD":  ("On spending for child care, I think we spend {val}.", "Do we spend too much or too little on child care?"),
    "NATENRGY": ("On spending for alternative energy, I think we spend {val}.", "Do we spend too much or too little on alternative energy?"),
    "NATROAD":  ("On spending for highways and bridges, I think we spend {val}.", "Do we spend too much or too little on highways and bridges?"),
    "NATSCI":   ("On spending for scientific research, I think we spend {val}.", "Do we spend too much or too little on scientific research?"),
    "NATSOC":   ("On Social Security spending, I think we spend {val}.", "Do we spend too much or too little on Social Security?"),
    "PILLOK":   ("On giving birth control to teenagers aged 14-16, I {val}.",
                  "Do you agree or disagree that birth control should be available to teenagers 14-16?"),
    "RACDIF2":  ("On whether differences are due to in-born learning ability, my answer is {val}.",
                  "Do you think racial differences are due to in-born ability?"),
    "RACDIF3":  ("On whether differences are due to lack of education, my answer is {val}.", "Do you think they are due to lack of education?"),
    "RACDIF4":  ("On whether differences are due to lack of will, my answer is {val}.", "Do you think they are due to lack of will?"),
    "REBORN":   ("As to a 'born again' experience, my answer is {val}.", "Have you ever had a 'born again' experience?"),
    "RELITEN":  ("As a religious person, I consider myself {val}.", "Do you consider yourself a religious person?"),
    "SEXEDUC":  ("On sex education in public schools, I {val} it.", "Do you favor or oppose sex education in public schools?"),
    "SPANKING": ("On using spanking to discipline a child, I {val}.", "Do you agree or disagree with using spanking to discipline?"),
    "SPRTPRSN": ("As a spiritual person, I consider myself {val}.", "Do you consider yourself a spiritual person?"),
    "LETDIE1":  ("On allowing suicide for someone with an incurable disease, my answer is {val}.",
                  "Should someone with an incurable disease be allowed to end their life?"),
    "SUICIDE2": ("On allowing suicide for someone who is bankrupt, my answer is {val}.", "Should someone who is bankrupt be allowed to commit suicide?"),
    "SUICIDE3": ("On allowing suicide for someone tired of living, my answer is {val}.", "Should someone tired of living be allowed to commit suicide?"),
    "TAX":      ("On my federal income tax, I think it is {val}.", "Do you think your federal income tax is too high?"),
    "XMARSEX":  ("On sex with a person other than one's spouse, I think it is {val}.",
                  "What do you think about sex with a person other than one's spouse?"),
}


# ============================================================================
# Generic-with-cleanup fallback for variables not in TEMPLATES
# ============================================================================

def _clean_label(label: str) -> str:
    """Replace GSS's 'r' abbreviations and tidy up a variable label."""
    s = label.strip()
    # Strip "R's" / "r's" prefix possessive
    s = re.sub(r"^[Rr]'s ", "your ", s)
    s = re.sub(r"^[Rr]s ", "your ", s)
    # Mid-string " r " -> " you " and " r's " -> " your "
    s = re.sub(r"\b[Rr]'s\b", "your", s)
    s = re.sub(r"\b[Rr]\b", "you", s)
    # All-caps phrase -> lowercase (e.g., "VOTED TRUMP OR BIDEN")
    if s.isupper() and len(s) > 3:
        s = s.lower()
    return s


def _smart_val(val: str) -> str:
    """Lowercase all-caps short answers like YES / NO / FAVOR / ALWAYS WRONG so
    they read naturally inside a sentence."""
    if val is None:
        return val
    if val.isupper() and len(val) <= 30:
        return val.lower()
    return val


def _p1_clause(varname: str, value, taxonomy: dict) -> str | None:
    """1st-person clause (Argyle style)."""
    if pd.isna(value):
        return None
    val_label = get_value_label(varname, value)
    if val_label is None or _is_non_substantive_label(val_label):
        return None

    val_clean = _smart_val(val_label)

    if varname in TEMPLATES:
        p1_tpl, _ = TEMPLATES[varname]
        # The {val} slot — for numeric-valued vars like AGE / TVHOURS / HRS1,
        # convert value to int to drop the trailing .0
        try:
            float_v = float(value)
            if float_v == int(float_v):
                fmt_val = str(int(float_v))
            else:
                fmt_val = val_clean
        except (TypeError, ValueError):
            fmt_val = val_clean
        # AGE / TVHOURS / HRS1 / EDUC / MAEDUC / PAEDUC use numeric {val}
        if varname in {"AGE", "TVHOURS", "HRS1"}:
            return p1_tpl.format(val=fmt_val)
        return p1_tpl.format(val=val_clean)

    # Generic fallback
    var_label = get_variable_label(varname).strip()
    cleaned = _clean_label(var_label)
    return f"Regarding {cleaned}, I would say {val_clean}."


def _p2_qa(varname: str, value, taxonomy: dict) -> str | None:
    """Wang-style interviewer/respondent Q&A."""
    if pd.isna(value):
        return None
    val_label = get_value_label(varname, value)
    if val_label is None or _is_non_substantive_label(val_label):
        return None

    val_clean = _smart_val(val_label)

    if varname in TEMPLATES:
        p1_tpl, p2_question = TEMPLATES[varname]
        # Numeric vars: render integer
        try:
            float_v = float(value)
            if float_v == int(float_v):
                fmt_val = str(int(float_v))
            else:
                fmt_val = val_clean
        except (TypeError, ValueError):
            fmt_val = val_clean
        if varname in {"AGE", "TVHOURS", "HRS1"}:
            answer = p1_tpl.format(val=fmt_val)
        else:
            answer = p1_tpl.format(val=val_clean)
        return f"Interviewer: {p2_question}\nRespondent: {answer}"

    # Generic fallback
    var_label = get_variable_label(varname).strip()
    cleaned = _clean_label(var_label)
    return (
        f"Interviewer: What about {cleaned}?\n"
        f"Respondent: {val_clean}."
    )


# ============================================================================
# Preambles + trailers + bin headers (per voice / structure)
# ============================================================================

P1_PREAMBLE = """I am a respondent of the 2024 General Social Survey (GSS). Below is who I am, \
organized by topic. I will answer further survey questions in character, \
drawing on the consistency of the views and life context shown below.

I will commit to a single answer in the requested format. No "it depends" hedges, \
no refusals, no qualifications about being an AI."""

P1_TRAILER = """---

I will now be asked one or more additional GSS questions. I will answer in character, \
in the exact format requested by each question."""

P1_BIN_DISPLAY = [
    ("demographic",   "## ABOUT ME — DEMOGRAPHICS"),
    ("behavioral",    "## ABOUT ME — BEHAVIORS"),
    ("psychological", "## ABOUT ME — PSYCHOLOGICAL DISPOSITIONS"),
    ("attitudinal",   "## ABOUT ME — ATTITUDES"),
]

P2_PREAMBLE = """The following is an interview transcript with a respondent of the 2024 \
General Social Survey (GSS). The respondent answered questions about themselves, \
their behaviors, their psychological dispositions, and their attitudes.

You will later be asked to continue answering in the voice of this same respondent, \
in the exact format requested. You will commit to a single answer per question \
and will not hedge, refuse, or break character."""

P2_TRAILER = """---

Interviewer: I will now ask you a few more questions. Please answer in the same \
format I request for each."""

P2_BIN_DISPLAY = [
    ("demographic",   "## DEMOGRAPHIC BACKGROUND"),
    ("behavioral",    "## BEHAVIORS"),
    ("psychological", "## PSYCHOLOGICAL DISPOSITIONS"),
    ("attitudinal",   "## ATTITUDES"),
]


def _render(respondent, taxonomy, preamble, trailer, bin_display, item_fn):
    bins = taxonomy["_feature_bins_sets"]
    parts = [preamble, ""]
    for bin_name, header in bin_display:
        bin_vars = sorted(bins[bin_name])
        lines = []
        for v in bin_vars:
            if v not in respondent.index:
                continue
            line = item_fn(v, respondent[v], taxonomy)
            if line is not None:
                lines.append(line)
        if lines:
            parts.append(header)
            parts.extend(lines)
            parts.append("")
    parts.append(trailer)
    return "\n".join(parts)


# ============================================================================
# Main
# ============================================================================

with open(WORK / "gss_feature_taxonomy.json") as f:
    tax = json.load(f)
tax["_feature_bins_sets"] = {
    b: set(tax["feature_bins"][b])
    for b in ("demographic", "behavioral", "psychological", "attitudinal")
}

resp = sample_respondents(n=1, seed=42).iloc[0]

p0_prompt, _ = build_persona_prompt(resp, tax, drop_bin=None)
p1_prompt = _render(resp, tax, P1_PREAMBLE, P1_TRAILER, P1_BIN_DISPLAY, _p1_clause)
p2_prompt = _render(resp, tax, P2_PREAMBLE, P2_TRAILER, P2_BIN_DISPLAY, _p2_qa)

# Count how many vars used a per-var template vs the generic fallback
template_hits = {b: 0 for b, _ in BIN_DISPLAY}
template_misses = {b: 0 for b, _ in BIN_DISPLAY}
for b, _ in BIN_DISPLAY:
    for v in tax["_feature_bins_sets"][b]:
        if v not in resp.index:
            continue
        val = resp[v]
        if pd.isna(val):
            continue
        vl = get_value_label(v, val)
        if vl is None or _is_non_substantive_label(vl):
            continue
        if v in TEMPLATES:
            template_hits[b] += 1
        else:
            template_misses[b] += 1

out_path = WORK / "outputs" / "_prompt_drafts_review.txt"

coverage = "\n".join(
    f"#   {b}: {template_hits[b]} hand-templated / {template_misses[b]} generic-fallback"
    for b, _ in BIN_DISPLAY
)

manifest = f"""# P0 / P1 / P2 prompt drafts (v2) — seed=42 respondent #0
# Updated 2026-05-29: per-variable templates for ~80 vars, generic-with-cleanup for rest.
#
# Respondent #0 substantive responses (sanity-check):
#   age            = {int(resp['AGE'])}
#   sex            = {get_value_label('SEX', resp['SEX'])}
#   race           = {get_value_label('RACE', resp['RACE'])}
#   marital status = {get_value_label('MARITAL', resp['MARITAL'])}
#   degree         = {get_value_label('DEGREE', resp['DEGREE'])}
#   POLVIEWS truth = {get_value_label('POLVIEWS', resp['POLVIEWS'])}
#   PARTYID truth  = {get_value_label('PARTYID', resp['PARTYID'])}
#
# Per-variable template coverage (this respondent's substantive features):
{coverage}
#
# Joyce, while auditing:
#   1. Per-variable templates in P1: do the sentences read like Argyle's
#      verbatim style? Any awkward phrasings to revise?
#   2. Per-variable templates in P2: do the "Interviewer: ... / Respondent: ..."
#      Q&A pairs match Wang's style?
#   3. Generic fallback: for low-density variables, "Regarding {{cleaned label}},
#      I would say {{val}}." — acceptable? Or do you want me to hand-craft templates
#      for the remaining variables too?
#   4. Preamble/trailer voice — comfortable?

================================================================================
# P0 — Park v2 surveys-only baseline (production builder, 2nd person, key:value)
================================================================================

{p0_prompt}

================================================================================
# P1 — Argyle 2023 1st-person prose (per-variable templates + cleaned generic)
================================================================================

{p1_prompt}

================================================================================
# P2 — Wang 2025 interview Q&A (per-variable Q&A + cleaned generic)
================================================================================

{p2_prompt}
"""

out_path.write_text(manifest)
print(f"Saved to {out_path}")
print(f"P0 length: {len(p0_prompt):>6,} chars / ~{len(p0_prompt)//4:>4,} tokens")
print(f"P1 length: {len(p1_prompt):>6,} chars / ~{len(p1_prompt)//4:>4,} tokens")
print(f"P2 length: {len(p2_prompt):>6,} chars / ~{len(p2_prompt)//4:>4,} tokens")
print()
print(f"Per-variable template coverage:")
for b, _ in BIN_DISPLAY:
    print(f"  {b}: {template_hits[b]} hand-templated / {template_misses[b]} generic-fallback")
