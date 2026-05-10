"""GSS Phase 1 persona pipeline — for each sampled respondent, build persona
prompts under 5 conditions (full + 4 LOO ablations) and predict the 12
primary_eval items. Sensitivity pass over ~118 sensitivity_eval items uses
per-item exclusion.

Locked design: see gss_phase1_design.md (v 2026-05-05) and
gss_feature_taxonomy.json (v 0.3-locked-2026-05-05).

Audit checkpoint status (locked + smoke-tested):
  AUDIT-A persona prompt template     ✅ --print-prompt
  AUDIT-B eval question phrasing      ✅ --print-questions
  AUDIT-C scoring rules               ✅ --test-scoring (7 hand assertions)
  AUDIT-D sensitivity exclusion       ✅ --test-exclusion (with hard asserts)
  AUDIT-E aggregation                 ✅ --test-aggregation (5 hand assertions)
  Multi-model panel extension         ✅ --test-multimodel (synthetic 4-model)
  LLM dispatcher (llm_router.py)      ✅
  Top-level driver (gss_driver.py)    ✅

Usage (no LLM yet):
    python3 gss_pipeline.py --print-prompt       # AUDIT-A
    python3 gss_pipeline.py --print-questions    # AUDIT-B
    python3 gss_pipeline.py --test-scoring       # AUDIT-C
    python3 gss_pipeline.py --test-exclusion     # AUDIT-D
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from gss_loader import (
    MISSING_CODES,
    _spec,
    get_value_label,
    get_variable_label,
    load_gss,
)

WORK = Path("/Users/joyce/Documents/GSBGEN390")
TAXONOMY_PATH = WORK / "gss_feature_taxonomy.json"
BATTERY_MAP_PATH = WORK / "gss_battery_map.json"


# ---------------------------------------------------------------------------
# Taxonomy + data loading
# ---------------------------------------------------------------------------

def load_taxonomy(path: Path = TAXONOMY_PATH) -> dict:
    """Load and post-process the locked feature taxonomy."""
    raw = json.loads(path.read_text())
    # Materialize the bin-set objects for fast membership tests
    raw["_primary_eval_set"] = {it["id"] for it in raw["primary_eval"]["items"]}
    raw["_sensitivity_eval_set"] = set(raw["sensitivity_eval"]["items"])
    raw["_feature_bins_sets"] = {
        name: set(items)
        for name, items in raw["feature_bins"].items()
        if not name.startswith("_")
    }
    raw["_all_features_set"] = set().union(*raw["_feature_bins_sets"].values())
    return raw


# Cached battery-map loader (R1 — locked 2026-05-08, gss_phase1_design.md §9c.R1)
_BATTERY_MAP_CACHE: dict | None = None


def load_battery_map(path: Path = BATTERY_MAP_PATH) -> dict:
    """Load gss_battery_map.json and add reverse-lookup helpers.

    Returns a dict with:
        "batteries": {battery_name -> {"items": [...], "construct": "..."}}
        "singletons": [item_ids ...]
        "_var_to_battery": {var_id -> battery_name (or None)}
        "_battery_items_set": {battery_name -> frozenset(items)}
    """
    global _BATTERY_MAP_CACHE
    if _BATTERY_MAP_CACHE is not None:
        return _BATTERY_MAP_CACHE
    raw = json.loads(path.read_text())
    var_to_battery: dict[str, str] = {}
    battery_items_set: dict[str, frozenset[str]] = {}
    for bname, bdef in raw["batteries"].items():
        items = frozenset(bdef["items"])
        battery_items_set[bname] = items
        for v in items:
            if v in var_to_battery:
                raise ValueError(
                    f"Battery map malformed: {v} appears in both "
                    f"{var_to_battery[v]} and {bname}. Items must be in at most one battery."
                )
            var_to_battery[v] = bname
    raw["_var_to_battery"] = var_to_battery
    raw["_battery_items_set"] = battery_items_set
    _BATTERY_MAP_CACHE = raw
    return raw


def battery_excludes_for_item(item_id: str, battery_map: dict | None = None) -> set[str]:
    """For R1: return the set of variable ids that must be excluded from the
    persona prompt when predicting `item_id`.

    Returns the entire battery (including item_id itself) if item_id is in a
    battery; otherwise returns the singleton {item_id}. The caller usually
    union's this with any other per-item exclusions (e.g., the predicted item
    itself in the sensitivity pass).
    """
    bm = battery_map or load_battery_map()
    bname = bm["_var_to_battery"].get(item_id)
    if bname is None:
        return {item_id}
    return set(bm["_battery_items_set"][bname])


def sample_respondents(n: int, year: int = 2024, seed: int = 42) -> pd.DataFrame:
    """Random sample of N GSS respondents without replacement.
    Pre-registered seed=42 in gss_phase1_design.md §5.
    """
    df = load_gss(year=year)
    if n >= len(df):
        return df.copy()
    return df.sample(n=n, random_state=seed).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 🔍 AUDIT-A: Persona prompt template
# ---------------------------------------------------------------------------
# This is the SINGLE BIGGEST METHODOLOGICAL CHOICE in the whole pipeline.
# Defaults committed below; review and approve before locking.
#
# Decisions baked in (each is reviewable):
#   1. Role framing: "You are a person who completed the 2024 GSS. Below are your
#      survey answers." (Park-style "you are this person" framing.)
#   2. Feature representation: variable label (from .do `label var`) + ":" + value
#      label (from .do `label values`). E.g. "favor or oppose death penalty for
#      murder: OPPOSE". This mirrors Park's surveys-only condition format.
#   3. Bin organization: features GROUPED BY BIN with section headers
#      (## DEMOGRAPHICS, ## BEHAVIORS, etc.). LOO drops an entire section.
#   4. Within-bin order: alphabetical by variable name (deterministic / Park-comparable).
#   5. Missing items: NOT included in prompt (per locked design — drop missing-coded).
#   6. Reverse-coded scales: presented in their NATIVE direction (matching what a
#      real respondent saw), since we will also receive predictions in native
#      direction; scoring will compute MAE in native scale.
#   7. Trailing instruction: the prompt ends with a one-line role reminder.
#      Per-question questions are added separately at LLM call time.
# ---------------------------------------------------------------------------

# Section headers, in fixed order, for the 4 bins
BIN_DISPLAY = [
    ("demographic",   "## YOUR DEMOGRAPHIC BACKGROUND"),
    ("behavioral",    "## YOUR BEHAVIORS"),
    ("psychological", "## YOUR PSYCHOLOGICAL DISPOSITIONS"),
    ("attitudinal",   "## YOUR ATTITUDES"),
]

PERSONA_PREAMBLE = """You are a person who completed the 2024 General Social Survey \
(GSS). Below is what you told the survey, organized by topic. Stay in character as \
this respondent throughout — your views, your demographics, your behaviors are as \
described.

You may be asked further survey questions. Answer ENTIRELY IN CHARACTER as this \
person, drawing on the consistency of the views and life context shown below. \
Always commit to a single answer in the requested format. No "it depends" hedges, \
no refusals, no qualifications about being an AI."""

PERSONA_TRAILER = """---

You will now be asked one or more additional GSS questions. Answer in character, \
in the exact format requested by each question."""


# Label patterns that indicate non-substantive responses (positive integer codes
# that nevertheless mean "no real answer"). Per Codex audits 2026-05-06: must be
# tight enough to NOT false-positive on substantive labels containing 'na' as a
# substring (e.g., 'China', 'Native American', 'Inter-Nondenominational',
# 'Argentina', 'French Guiana').
#
# Strategy: split into two pattern sets — "exact-match-only" for short codes
# that would otherwise false-positive (na, dk), and "substring-match" for long
# distinctive phrases.
_NON_SUBSTANTIVE_EXACT = frozenset((
    # short codes that must match the WHOLE label (after lower+strip)
    "na", "n/a", "n.a.", "dk", "dk/na", "na/dk",
))
_NON_SUBSTANTIVE_SUBSTRINGS = (
    # long enough that substring-matching is safe
    "refused", "no answer", "don't know", "do not know",
    "inapplicable", "not applicable", "skipped on web",
    "uncodable", "iap",  # IAP is a GSS-specific term: 'inapplicable'
    "not asked", "not in survey",
)


def _is_non_substantive_label(label: str) -> bool:
    """Detect labels that should be treated as missing for persona purposes
    even when the underlying code is positive (not in MISSING_CODES).

    Two-tier match:
      1. Whole-label match against short codes that would false-positive
         as substrings (na, dk, n/a).
      2. Substring match against long distinctive phrases (refused, don't
         know, inapplicable, IAP, etc.).
    """
    if label is None:
        return False
    s = label.strip().lower()
    if not s:
        return True
    if s in _NON_SUBSTANTIVE_EXACT:
        return True
    return any(p in s for p in _NON_SUBSTANTIVE_SUBSTRINGS)


def _format_feature_line(varname: str, value) -> str | None:
    """Render one feature as a labeled line.
    Returns None if the value is missing/coded-missing OR if the label text
    indicates a non-substantive response (REFUSED / DK / IAP / etc.).
    """
    if pd.isna(value) or int(value) in MISSING_CODES:
        return None
    var_label = get_variable_label(varname).strip()
    val_label = get_value_label(varname, value)
    if val_label is None:
        return None
    if _is_non_substantive_label(val_label):
        # Positive-coded but non-substantive (e.g., OWNGUN=3 REFUSED). Treat
        # as missing for persona prompts to avoid teaching the LLM to refuse.
        return None
    return f"- {var_label}: {val_label}"


def build_persona_prompt(
    respondent: pd.Series,
    taxonomy: dict,
    drop_bin: str | None = None,
    exclude_vars: set[str] | list[str] | None = None,
) -> tuple[str, dict[str, int]]:
    """Build the persona system prompt for one respondent under one condition.

    Args:
        respondent: a row from the loaded GSS DataFrame (one respondent).
        taxonomy: the loaded taxonomy dict.
        drop_bin: name of bin to drop ('demographic'/'behavioral'/'psychological'/
            'attitudinal'), or None for the FULL condition (used by primary LOO).
        exclude_vars: optional iterable of variable names to drop from the
            prompt regardless of bin (used by AUDIT-D sensitivity per-item
            exclusion: when predicting sensitivity item X, X must not appear
            in the persona's feature list).

    Returns:
        (prompt_text, stats_dict).
    """
    bins = taxonomy["_feature_bins_sets"]
    excl: set[str] = set(exclude_vars or ())
    parts = [PERSONA_PREAMBLE, ""]
    stats: dict[str, int] = {}

    for bin_name, header in BIN_DISPLAY:
        if drop_bin == bin_name:
            stats[bin_name] = 0
            continue
        bin_vars = sorted(bins[bin_name])
        lines = []
        for v in bin_vars:
            if v in excl:
                continue
            if v not in respondent.index:
                continue
            line = _format_feature_line(v, respondent[v])
            if line is not None:
                lines.append(line)
        stats[bin_name] = len(lines)
        if lines:
            parts.append(header)
            parts.extend(lines)
            parts.append("")

    parts.append(PERSONA_TRAILER)
    prompt = "\n".join(parts)
    stats["total_features"] = sum(stats[b] for b, _ in BIN_DISPLAY)
    stats["char_count"] = len(prompt)
    stats["approx_tokens"] = len(prompt) // 4
    stats["excluded_vars"] = sorted(excl)
    return prompt, stats


# ---------------------------------------------------------------------------
# 🔍 AUDIT-B: Eval question phrasing
# ---------------------------------------------------------------------------
# For each primary_eval item, build the user-message question that follows
# the persona system message in a single LLM call.
#
# Decisions baked in (each is reviewable):
#   B.1  Question stem = the GSS variable label (from .do file). Some are
#        terse ("women not suited for politics"); others are descriptive
#        ("favor or oppose death penalty for murder"). Used verbatim
#        for Park-comparability — Park v2 used GSS items as-is.
#   B.2  Output format = a single integer code corresponding to one of the
#        listed options. Unified across item types (likert3/4/5/7, binary,
#        and sparse-anchored scales like HELPPOOR). Easy to parse.
#   B.3  Options shown WITH their numeric codes so LLM has the same
#        information a human GSS respondent has from the codebook.
#   B.4  Sparse-anchored scales (HELPPOOR: only 1, 3, 5 have anchor labels;
#        2 and 4 are valid intermediate codes) get a special instruction
#        permitting intermediate codes.
#   B.5  PARTYID special case: ordinal 0-6 plus a separate "Other party"
#        code 7. We present all 8 options. Scoring (AUDIT-C) decides how
#        to treat code 7.
#
# Token-budget note: most primary_eval question prompts are <100 tokens.
# Two exceptions are intentional:
#   - FECHLD (~103 tokens): canonical GSS question text from override map
#     (instructional preamble is part of the GSS administered wording)
#   - HELPPOOR (~170 tokens): canonical 1-vs-5 anchor wording is long by
#     design; sparse-anchor instruction adds ~30 tokens
# The "<100 tokens" target is a sanity check, not a hard invariant.
# ---------------------------------------------------------------------------

# Items where the codebook supplies sparse anchors (intermediate values valid).
_SPARSE_ANCHOR_ITEMS = {"HELPPOOR"}

# Question-stem overrides: for 4 items, the .do `label var` is a terse summary
# (e.g. "women not suited for politics") that hides the actual GSS question
# wording AND the answer-polarity. We override with the canonical GSS question
# text from the GSS codebook for clarity and Park-comparability.
# Source: GSS 1972-2024 Cumulative Codebook entries for these variables.
_STEM_OVERRIDE = {
    "FECHLD": (
        "Now I'm going to read several more statements. As I read each one, please tell me "
        "whether you strongly agree, agree, disagree, or strongly disagree. "
        "Statement: \"A working mother can establish just as warm and secure a relationship "
        "with her children as a mother who does not work.\""
    ),
    "FEPOL": (
        "Tell me if you agree or disagree with this statement: "
        "\"Most men are better suited emotionally for politics than are most women.\""
    ),
    "RACDIF1": (
        "On the average, Black people have worse jobs, income, and housing than white people. "
        "Do you think these differences are mainly due to discrimination?"
    ),
    "HELPPOOR": (
        "Some people think that the government in Washington should do everything possible to "
        "improve the standard of living of all poor Americans (they are at point 1 on the scale). "
        "Other people think it is not the government's responsibility, and that each person should "
        "take care of himself (they are at point 5). Where would you place yourself on this scale, "
        "or haven't you made up your mind on this?"
    ),
}


def _scale_options_for(item_id: str) -> list[tuple[int, str]]:
    """Return the (code, label) pairs that define this item's response scale.
    Pulls from the parsed .do label set; sorted by code; excludes negative
    missing codes AND positive-coded non-substantive labels (REFUSED / DK /
    IAP / NA / etc.).

    Why filter non-substantive labels here: scoring (`score_item`,
    `truth_code_or_none`) treats labels like OWNGUN=3 ('REFUSED') and
    INCOME=13 ('Refused') as missing on the truth side via
    `_is_non_substantive_label`. If the formatter still presents those codes
    as valid model outputs, the LLM can emit a code that scores as missing
    on truth but is "valid" on its own output side — an asymmetry that
    silently inflates parse-failure-equivalent behavior. Filter here so
    presentation and scoring agree.
    """
    spec = _spec()
    set_name = spec["var_to_label_set"].get(item_id.upper())
    if not set_name:
        return []
    label_set = spec["value_label_sets"].get(set_name, {})
    pairs = [
        (code, label)
        for code, label in label_set.items()
        if code not in MISSING_CODES
        and code >= 0
        and not _is_non_substantive_label(label)
    ]
    return sorted(pairs, key=lambda p: p[0])


def format_eval_question(item: dict) -> tuple[str, dict[str, Any]]:
    """Build the user-message text for one primary_eval item, plus a small
    metadata dict used downstream by the scorer.

    Returns:
        (question_text, meta) where meta = {
            "id": variable_id,
            "format": likert3 / likert4 / likert5 / likert7 / binary,
            "valid_codes": list of int codes the LLM may output,
            "code_to_label": {int -> str label},
            "is_sparse_anchored": bool,
        }
    """
    item_id = item["id"]
    # Use override stem when available (canonical GSS wording); else fall back to
    # the .do file's `label var` summary.
    variable_label = _STEM_OVERRIDE.get(item_id, get_variable_label(item_id))
    options = _scale_options_for(item_id)
    is_sparse = item_id in _SPARSE_ANCHOR_ITEMS

    # Sensitivity-item overrides (set by derive_sensitivity_item in gss_driver):
    # if item carries _valid_codes_override / _is_sparse_override, honor them.
    valid_codes_override = item.get("_valid_codes_override")
    if valid_codes_override is not None:
        # Filter the label set to the override's codes, preserving labels for
        # the ones we have, and synthesizing "(unanchored)" for missing intermediate codes.
        existing_labels = dict(options)
        options = [(c, existing_labels.get(c, "(unanchored intermediate)"))
                   for c in valid_codes_override]
        is_sparse = item.get("_is_sparse_override", False)

    option_lines = [f"  {code}. {label}" for code, label in options]
    valid_codes = [c for c, _ in options]
    code_to_label = {c: l for c, l in options}

    if is_sparse and len(options) >= 2:
        full_range = list(range(min(valid_codes), max(valid_codes) + 1))
        for c in full_range:
            if c not in code_to_label:
                code_to_label[c] = "(unanchored intermediate)"
        valid_codes = full_range

    code_min = min(valid_codes)
    code_max = max(valid_codes)

    if is_sparse:
        instruction = (
            f"Output ONLY a single integer code from {code_min} to {code_max}. "
            f"Codes between the labeled anchors above (e.g. 2 and 4) are valid intermediate "
            f"positions; pick whichever single integer best matches this person's view."
        )
    else:
        instruction = f"Output ONLY a single integer code ({code_min}-{code_max})."

    question = (
        f"GSS question: {variable_label}\n\n"
        f"Options:\n"
        + "\n".join(option_lines)
        + f"\n\n{instruction}"
    )

    meta = {
        "id": item_id,
        "format": item["format"],
        "valid_codes": valid_codes,
        "code_to_label": code_to_label,
        "is_sparse_anchored": is_sparse,
    }
    return question, meta


def _audit_b_print():
    """Print all 12 primary_eval questions for review."""
    taxonomy = load_taxonomy()
    print(f"\n=== AUDIT-B: 12 primary_eval question prompts ===")
    print(f"    Each block below is what GPT-4o sees as a USER message immediately after")
    print(f"    the persona SYSTEM message (locked in AUDIT-A).\n")
    for i, item in enumerate(taxonomy["primary_eval"]["items"], 1):
        question, meta = format_eval_question(item)
        print(f"{'─' * 72}")
        print(f"[{i:>2}/12]  {item['id']}  (format: {meta['format']}, codes: {meta['valid_codes']}, "
              f"sparse: {meta['is_sparse_anchored']})")
        print(f"        construct: {item['construct']}")
        print(f"{'─' * 72}")
        print(question)
        print()


def _audit_b_test_no_refusal_options():
    """Regression: every primary_eval and sensitivity_eval item, when run
    through `format_eval_question` (with sensitivity overrides applied where
    they exist), MUST present only substantive answer options to the LLM.

    Truth-side scoring filters non-substantive labels (REFUSED / DK / IAP /
    NA) as missing; the formatter must agree, otherwise the model can emit
    a code that is "valid output" but "missing truth" — an asymmetry that
    silently inflates parse-failure-equivalent behavior.

    Caught the OWNGUN=3 ('REFUSED') and INCOME=13 ('Refused') leak in the
    2026-05-06 audit. Fails LOUDLY if anyone reintroduces a non-substantive
    code into a presented option list.
    """
    taxonomy = load_taxonomy()

    # Lazy import to avoid circular dependency: the sensitivity overrides
    # live in the driver module.
    try:
        from gss_driver import SENSITIVITY_FORMAT_OVERRIDES, derive_sensitivity_item
    except ImportError as e:
        raise RuntimeError(
            "AUDIT-B regression test needs gss_driver.SENSITIVITY_FORMAT_OVERRIDES "
            f"and derive_sensitivity_item: {e}"
        )

    failures: list[str] = []

    # Primary eval items: as-is.
    for item in taxonomy["primary_eval"]["items"]:
        _, meta = format_eval_question(item)
        for code in meta["valid_codes"]:
            label = meta["code_to_label"].get(code, "")
            if _is_non_substantive_label(label):
                failures.append(
                    f"PRIMARY {item['id']}: option {code}={label!r} is non-substantive"
                )

    # Sensitivity eval items: route through the driver's derive helper so
    # the same overrides used at run-time are exercised here.
    for vname in taxonomy["sensitivity_eval"]["items"]:
        sens_item = derive_sensitivity_item(vname)
        if sens_item is None:
            continue
        _, meta = format_eval_question(sens_item)
        for code in meta["valid_codes"]:
            label = meta["code_to_label"].get(code, "")
            if _is_non_substantive_label(label):
                failures.append(
                    f"SENSITIVITY {vname}: option {code}={label!r} is non-substantive"
                )

    if failures:
        msg = (
            "AUDIT-B regression FAILED: presented options include non-substantive "
            "labels that truth-side scoring treats as missing.\n  - "
            + "\n  - ".join(failures)
        )
        raise AssertionError(msg)

    n_prim = len(taxonomy["primary_eval"]["items"])
    n_sens = len(taxonomy["sensitivity_eval"]["items"])
    print(
        f"✓ AUDIT-B regression: no non-substantive options exposed "
        f"({n_prim} primary + {n_sens} sensitivity items checked)"
    )


# ---------------------------------------------------------------------------
# 🔍 AUDIT-C: Scoring rules
# ---------------------------------------------------------------------------
# Decisions baked in (locked 2026-05-05 with Joyce sign-off):
#   C.1  Three primary metrics: Likert MAE, % within ±1, categorical match
#        rate. All are computed PER RESPONDENT × CONDITION; aggregation to
#        headline is the AUDIT-E step.
#   C.2  Treatment per item:
#        - format ∈ {likert3, likert4, likert5, likert7}: Likert MAE
#        - format == binary: categorical exact-match (NOT 1-step Likert,
#          per Park v2 convention)
#        - PARTYID: contingent. If truth==7 OR persona==7 ("Other party"),
#          score as categorical; else Likert MAE on 0-6.
#   C.3  LLM-output parsing: extract first integer; fail if not in valid_codes.
#        Parse failures NOT included in Likert/cat metrics; tracked as a
#        separate parse-failure-rate QA metric.
#   C.4  Missing items (GSS-coded missing for that respondent): excluded
#        from that respondent's scoring. Pre-registered missingness rule.
#   C.5  Self-consistency: % of items where both LLM samples gave the same
#        integer. Reported as supplementary stability QA metric.
# ---------------------------------------------------------------------------

import re
from statistics import mean


def truth_code_or_none(value: Any, varname: str | None = None) -> int | None:
    """Convert a respondent's raw GSS value into an integer truth code, or
    None if the value is GSS-missing-coded OR if its label is non-substantive
    (REFUSED / DK / IAP / etc., which are positive integer codes outside the
    MISSING_CODES set but still aren't real answers).

    Pass `varname` to enable label-based filtering (recommended). Without
    `varname`, only MISSING_CODES filtering applies.
    """
    if value is None or pd.isna(value):
        return None
    try:
        i = int(value)
    except (ValueError, TypeError):
        return None
    if i in MISSING_CODES:
        return None
    if varname is not None:
        lbl = get_value_label(varname, i)
        if lbl is not None and _is_non_substantive_label(lbl):
            return None
    return i


def parse_response(raw: str, valid_codes: list[int]) -> int | None:
    """Extract first integer from raw LLM text; return None if absent or
    not in valid_codes (out-of-range / unparseable)."""
    if raw is None:
        return None
    m = re.search(r"-?\d+", raw)
    if m is None:
        return None
    try:
        code = int(m.group())
    except ValueError:
        return None
    return code if code in valid_codes else None


def classify_item_for_scoring(
    item_id: str, format_str: str, persona_code: int, truth_code: int
) -> str:
    """Decide whether to score this (item, response, truth) as 'likert' or
    'categorical' per AUDIT-C.2 and C.3.
    """
    if format_str == "binary":
        return "categorical"
    if item_id == "PARTYID":
        # Code 7 = "Other party" is off-the-scale. Treat as categorical when
        # either side picks it; treat as Likert otherwise.
        if persona_code == 7 or truth_code == 7:
            return "categorical"
        return "likert"
    return "likert"


def score_item(
    item_id: str,
    format_str: str,
    valid_codes: list[int],
    persona_raw: str,
    truth_code: int | None,
) -> dict[str, Any]:
    """Score one (respondent, item, sample) outcome.

    Returns a dict with truth, parsed code, treatment ('likert' or
    'categorical'), abs_err / within1 / cat_match (only the relevant ones
    are populated based on treatment), and parse_fail flag.

    If truth_code is None (respondent didn't answer this item per GSS
    missingness), scoring is skipped — caller should not include this in
    aggregation. We still parse the persona response for diagnostic logs.
    """
    persona_code = parse_response(persona_raw, valid_codes)
    out: dict[str, Any] = {
        "truth": truth_code,
        "persona_raw": persona_raw,
        "persona_code": persona_code,
        "parse_fail": persona_code is None,
        "treatment": None,
        "abs_err": None,
        "within1": None,
        "cat_match": None,
        "skipped_missing_truth": truth_code is None,
    }
    if persona_code is None or truth_code is None:
        return out
    treatment = classify_item_for_scoring(item_id, format_str, persona_code, truth_code)
    out["treatment"] = treatment
    if treatment == "likert":
        out["abs_err"] = abs(persona_code - truth_code)
        out["within1"] = int(out["abs_err"] <= 1)
    else:
        out["cat_match"] = int(persona_code == truth_code)
    return out


def aggregate_respondent_condition(
    per_item_scores: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Aggregate per-item scores across the n_samples for one (respondent,
    condition) into the per-respondent metrics record.

    Args:
        per_item_scores: {item_id: [score_dict_sample0, score_dict_sample1, ...]}
            One entry per item the respondent had a non-missing truth for.

    Returns:
        per-respondent-condition metrics dict (see AUDIT-C.7 schema).
    """
    likert_errs = []
    likert_within = []
    cat_matches = []
    parse_fails_total = 0
    parse_fails_denom = 0
    self_consistency_matches = []

    for item_id, sample_scores in per_item_scores.items():
        # Skip items with no truth (respondent didn't answer)
        if all(s.get("skipped_missing_truth") for s in sample_scores):
            continue

        # Per-sample: gather likert / cat / parse_fail
        for s in sample_scores:
            if s.get("skipped_missing_truth"):
                continue
            parse_fails_denom += 1
            if s["parse_fail"]:
                parse_fails_total += 1
                continue
            if s["treatment"] == "likert":
                likert_errs.append(s["abs_err"])
                likert_within.append(s["within1"])
            elif s["treatment"] == "categorical":
                cat_matches.append(s["cat_match"])

        # Self-consistency: do samples 0 and 1 agree on parsed code?
        if len(sample_scores) >= 2:
            a, b = sample_scores[0], sample_scores[1]
            if (
                not a.get("skipped_missing_truth")
                and not b.get("skipped_missing_truth")
                and a["persona_code"] is not None
                and b["persona_code"] is not None
            ):
                self_consistency_matches.append(
                    1 if a["persona_code"] == b["persona_code"] else 0
                )

    return {
        "likert_mae": round(mean(likert_errs), 3) if likert_errs else None,
        "likert_within1_pct": round(100 * mean(likert_within), 1) if likert_within else None,
        "cat_match_pct": round(100 * mean(cat_matches), 1) if cat_matches else None,
        "self_consistency_pct": (
            round(100 * mean(self_consistency_matches), 1)
            if self_consistency_matches
            else None
        ),
        "parse_failure_pct": (
            round(100 * parse_fails_total / parse_fails_denom, 1) if parse_fails_denom else 0.0
        ),
        "n_likert_obs": len(likert_errs),
        "n_cat_obs": len(cat_matches),
        "n_parse_fail": parse_fails_total,
        "n_consistency_pairs": len(self_consistency_matches),
    }


# ---------------------------------------------------------------------------
# AUDIT-C smoke test — hand-crafted scoring scenarios
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 🔍 AUDIT-E: Aggregation rules
# ---------------------------------------------------------------------------
# Locked decisions (from gss_phase1_design.md §10):
#   E.1  Three aggregations:
#        - PRIMARY: respondent-macro-averaged. Each respondent contributes
#          one number per (condition, metric); these are averaged.
#        - SECONDARY: item-macro (mean per item across respondents, then
#          mean across items) and pooled (flat mean over all observations).
#   E.2  Bootstrap CIs at respondent level, B=1000, 95% percentile.
#   E.3  LOO ΔMAE = MAE(LOO_drop_bin) − MAE(Full). PAIRED bootstrap:
#        resample respondents once, compute Full and LOO from the same
#        resample, then take delta. Do NOT independently bootstrap.
#   E.4  Output: gss_phase1_per_respondent.csv + gss_phase1_headline.csv +
#        gss_phase1_persona_answers.json (diagnostics).
# ---------------------------------------------------------------------------

import random as _aud_e_random  # explicit import scope; not the missing-data 'random'


def _likert_errors_for_record(record: dict[str, Any]) -> list[int]:
    """Flatten one (respondent, condition) record to its list of Likert
    abs-errors across items × samples (excluding parse-fails, missing-truth,
    and categorical-treated items)."""
    errs: list[int] = []
    for samples in record.get("per_item_scores", {}).values():
        for s in samples:
            if (
                s.get("treatment") == "likert"
                and s.get("abs_err") is not None
                and not s.get("parse_fail")
                and not s.get("skipped_missing_truth")
            ):
                errs.append(s["abs_err"])
    return errs


def _cat_matches_for_record(record: dict[str, Any]) -> list[int]:
    """Flatten one (respondent, condition) record to list of 0/1 categorical
    matches across items × samples."""
    matches: list[int] = []
    for samples in record.get("per_item_scores", {}).values():
        for s in samples:
            if (
                s.get("treatment") == "categorical"
                and s.get("cat_match") is not None
                and not s.get("parse_fail")
                and not s.get("skipped_missing_truth")
            ):
                matches.append(s["cat_match"])
    return matches


def _per_respondent_metric(record: dict[str, Any], metric: str) -> float | None:
    """Compute one (respondent, condition) summary for the named metric.
    Returns None if the respondent has zero contributing observations.
    """
    if metric == "likert_mae":
        errs = _likert_errors_for_record(record)
        return mean(errs) if errs else None
    if metric == "likert_within1_pct":
        errs = _likert_errors_for_record(record)
        if not errs:
            return None
        return 100 * sum(1 for e in errs if e <= 1) / len(errs)
    if metric == "cat_match_pct":
        matches = _cat_matches_for_record(record)
        return 100 * mean(matches) if matches else None
    raise ValueError(f"unknown metric: {metric}")


def aggregate_condition(
    records: list[dict[str, Any]], condition: str, metric: str = "likert_mae"
) -> dict[str, Any]:
    """Compute respondent-macro, item-macro, and pooled aggregations for one
    (condition, metric).

    Returns:
        {
            "n_respondents_contributing": int,
            "respondent_macro": float | None,   # PRIMARY
            "per_respondent_values": {rid: float},  # for paired bootstrap downstream
            "item_macro": float | None,         # secondary
            "pooled": float | None,             # secondary
            "n_total_observations": int,
        }
    """
    cond_records = [r for r in records if r.get("condition") == condition]

    # Respondent-macro — primary
    per_resp: dict[int, float] = {}
    for r in cond_records:
        v = _per_respondent_metric(r, metric)
        if v is not None:
            per_resp[r["respondent_id"]] = v
    respondent_macro = mean(per_resp.values()) if per_resp else None

    # Pooled and item-macro need observation-level info
    if metric == "likert_mae":
        per_item_errs: dict[str, list[int]] = {}
        all_obs: list[int] = []
        for r in cond_records:
            for item, samples in r.get("per_item_scores", {}).items():
                for s in samples:
                    if (
                        s.get("treatment") == "likert"
                        and s.get("abs_err") is not None
                        and not s.get("parse_fail")
                        and not s.get("skipped_missing_truth")
                    ):
                        per_item_errs.setdefault(item, []).append(s["abs_err"])
                        all_obs.append(s["abs_err"])
        item_macro = (
            mean([mean(errs) for errs in per_item_errs.values()]) if per_item_errs else None
        )
        pooled = mean(all_obs) if all_obs else None
        n_total = len(all_obs)
    elif metric == "likert_within1_pct":
        per_item_within: dict[str, list[int]] = {}
        all_obs_w: list[int] = []
        for r in cond_records:
            for item, samples in r.get("per_item_scores", {}).items():
                for s in samples:
                    if s.get("treatment") == "likert" and s.get("within1") is not None:
                        per_item_within.setdefault(item, []).append(s["within1"])
                        all_obs_w.append(s["within1"])
        item_macro = (
            100 * mean([mean(v) for v in per_item_within.values()]) if per_item_within else None
        )
        pooled = 100 * mean(all_obs_w) if all_obs_w else None
        n_total = len(all_obs_w)
    elif metric == "cat_match_pct":
        per_item_cat: dict[str, list[int]] = {}
        all_obs_c: list[int] = []
        for r in cond_records:
            for item, samples in r.get("per_item_scores", {}).items():
                for s in samples:
                    if s.get("treatment") == "categorical" and s.get("cat_match") is not None:
                        per_item_cat.setdefault(item, []).append(s["cat_match"])
                        all_obs_c.append(s["cat_match"])
        item_macro = (
            100 * mean([mean(v) for v in per_item_cat.values()]) if per_item_cat else None
        )
        pooled = 100 * mean(all_obs_c) if all_obs_c else None
        n_total = len(all_obs_c)
    else:
        item_macro = pooled = None
        n_total = 0

    return {
        "n_respondents_contributing": len(per_resp),
        "respondent_macro": respondent_macro,
        "per_respondent_values": per_resp,
        "item_macro": item_macro,
        "pooled": pooled,
        "n_total_observations": n_total,
    }


def bootstrap_ci(
    per_respondent_values: dict[int, float],
    B: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float]:
    """Percentile bootstrap CI on the mean of per-respondent values.
    Resampling is at respondent level (per locked design §10).

    Returns: (ci_lo, ci_hi) at the (alpha/2, 1 - alpha/2) percentiles.
    Returns (nan, nan) if input is empty.
    """
    if not per_respondent_values:
        return (float("nan"), float("nan"))
    rng = _aud_e_random.Random(seed)
    rids = list(per_respondent_values.keys())
    n = len(rids)
    boot_means: list[float] = []
    for _ in range(B):
        sample = [per_respondent_values[rng.choice(rids)] for _ in range(n)]
        boot_means.append(mean(sample))
    boot_means.sort()
    lo_idx = int((alpha / 2) * B)
    hi_idx = int((1 - alpha / 2) * B) - 1
    return (boot_means[lo_idx], boot_means[hi_idx])


def paired_bootstrap_loo_delta(
    full_per_resp: dict[int, float],
    loo_per_resp: dict[int, float],
    B: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict[str, float]:
    """Paired bootstrap for ΔMAE = MAE(LOO) − MAE(Full).

    Locked design §10: resample respondents ONCE per replicate, compute MAE
    on Full and LOO from THE SAME resample, then take delta. Mathematically
    equivalent to bootstrapping per-respondent deltas (paired Δ → mean Δ).

    Args:
        full_per_resp: respondent_id → per-respondent metric under Full
        loo_per_resp:  respondent_id → per-respondent metric under LOO
    Both dicts must use the same metric (e.g., likert_mae).

    Returns: {
        "mean_delta": float,
        "ci_lo": float,
        "ci_hi": float,
        "n_paired_respondents": int,
    }
    """
    common_rids = sorted(set(full_per_resp) & set(loo_per_resp))
    if not common_rids:
        return {"mean_delta": float("nan"), "ci_lo": float("nan"), "ci_hi": float("nan"),
                "n_paired_respondents": 0}

    # Per-respondent paired delta
    per_resp_delta = {rid: loo_per_resp[rid] - full_per_resp[rid] for rid in common_rids}
    mean_delta = mean(per_resp_delta.values())

    # Paired bootstrap: resample respondents, take mean of their deltas
    rng = _aud_e_random.Random(seed)
    n = len(common_rids)
    boot_deltas: list[float] = []
    for _ in range(B):
        sample = [per_resp_delta[rng.choice(common_rids)] for _ in range(n)]
        boot_deltas.append(mean(sample))
    boot_deltas.sort()
    lo_idx = int((alpha / 2) * B)
    hi_idx = int((1 - alpha / 2) * B) - 1

    return {
        "mean_delta": mean_delta,
        "ci_lo": boot_deltas[lo_idx],
        "ci_hi": boot_deltas[hi_idx],
        "n_paired_respondents": n,
    }


def compute_phase1_headline(
    records: list[dict[str, Any]],
    conditions: list[str] | None = None,
    metrics: tuple[str, ...] = ("likert_mae", "likert_within1_pct", "cat_match_pct"),
    bootstrap_B: int = 1000,
    seed: int = 42,
    full_condition: str = "full",
    loo_conditions: tuple[str, ...] = (
        "loo_drop_demographic",
        "loo_drop_behavioral",
        "loo_drop_psychological",
        "loo_drop_attitudinal",
    ),
) -> dict[str, Any]:
    """End-to-end headline computation for Phase 1.

    For each condition × metric, compute respondent-macro / item-macro /
    pooled with respondent-level percentile bootstrap CIs at B replicates.

    For each LOO condition × metric, additionally compute the paired-
    bootstrap ΔMAE_bin against the Full condition.

    Returns a nested dict suitable for serializing to gss_phase1_headline.csv.
    """
    if conditions is None:
        conditions = sorted({r["condition"] for r in records})

    headline: dict[str, Any] = {"per_condition": {}, "loo_deltas": {}}

    for cond in conditions:
        headline["per_condition"][cond] = {}
        for metric in metrics:
            agg = aggregate_condition(records, cond, metric=metric)
            ci = bootstrap_ci(agg["per_respondent_values"], B=bootstrap_B, seed=seed)
            headline["per_condition"][cond][metric] = {
                "n_respondents_contributing": agg["n_respondents_contributing"],
                "n_total_observations": agg["n_total_observations"],
                "respondent_macro": agg["respondent_macro"],
                "respondent_macro_ci_lo": ci[0],
                "respondent_macro_ci_hi": ci[1],
                "item_macro": agg["item_macro"],
                "pooled": agg["pooled"],
            }

    # LOO deltas (paired bootstrap), against Full
    full_aggs_by_metric = {
        metric: aggregate_condition(records, full_condition, metric=metric) for metric in metrics
    }
    for loo_cond in loo_conditions:
        if loo_cond not in conditions:
            continue
        headline["loo_deltas"][loo_cond] = {}
        for metric in metrics:
            full_agg = full_aggs_by_metric[metric]
            loo_agg = aggregate_condition(records, loo_cond, metric=metric)
            delta_result = paired_bootstrap_loo_delta(
                full_agg["per_respondent_values"],
                loo_agg["per_respondent_values"],
                B=bootstrap_B,
                seed=seed,
            )
            headline["loo_deltas"][loo_cond][metric] = delta_result

    return headline


# ---------------------------------------------------------------------------
# AUDIT-E multi-model extension (task #13)
# ---------------------------------------------------------------------------
# When records carry a "model" field (locked design §12), aggregation is
# extended:
#   - Per-model headline: filter records by model → existing aggregator.
#   - Panel median: synthesize records where each item's persona_code is the
#     median across all models for that (respondent, condition, item, sample).
#     Then re-score and aggregate.
#   - Cross-model agreement %: % of (respondent, item, sample) tuples where
#     all models output the same persona_code (excluding parse failures).
# ---------------------------------------------------------------------------

def filter_records_by_model(records: list[dict[str, Any]], model: str) -> list[dict[str, Any]]:
    """Return records belonging to a specific model. Preserves all other fields."""
    return [r for r in records if r.get("model") == model]


def _panel_aggregate_code(
    codes: list[int],
    valid_codes: list[int],
    item_id: str,
    item_format: str | None,
    respondent_id: int | None = None,
) -> int:
    """Aggregate model codes into a single 'panel' code.

    Locked design (gss_phase1_design.md §12 + Codex audit 2026-05-06;
    tie-break bug fix Codex audit M5 2026-05-09 night):

      - Likert items (likert3+): MEDIAN, snapped to nearest valid code.
        Tie-break: deterministic by hash of (item_id, respondent_id, codes_tuple)
        — symmetric, no directional bias.

      - Binary / categorical items: MODE (most common code).
        Tie-break: same deterministic-hash rule. **PRIOR BUG**: tie-break
        toward `min(candidates)` systematically biased binary items toward
        code 1 (e.g., ABANY=YES, CAPPUN=Favor, GUNLAW=Allowed). Fixed
        2026-05-09 night per Codex M5.

      - PARTYID contingent: if any model output 7 ('Other party'), MODE
        (because 7 is off the ordinal scale); else MEDIAN.

    The deterministic hash is reproducible for fixed (seed=42 in upstream
    sampling, item_id, respondent_id, codes) and breaks the prior
    directional bias toward lower code values.
    """
    from statistics import median as _median
    from collections import Counter
    import hashlib

    def _deterministic_pick(candidates: list[int]) -> int:
        """Pick one of candidates deterministically without directional bias.
        Uses SHA-256 over (item_id, respondent_id, sorted(codes), sorted(candidates))
        modulo len(candidates). Reproducible and unbiased."""
        if len(candidates) == 1:
            return int(candidates[0])
        key = (
            f"{item_id}|"
            f"{respondent_id if respondent_id is not None else 'NA'}|"
            f"{','.join(str(c) for c in sorted(codes))}|"
            f"{','.join(str(c) for c in sorted(candidates))}"
        )
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()
        idx = int(h[:8], 16) % len(candidates)
        return int(sorted(candidates)[idx])

    use_mode = (
        item_format == "binary"
        or item_format == "categorical"
        or (item_id == "PARTYID" and 7 in codes)
    )

    if use_mode:
        counts = Counter(codes)
        top = max(counts.values())
        candidates = [c for c, n in counts.items() if n == top]
        chosen = _deterministic_pick(candidates)
        # Ensure chosen is a valid code (always should be, but defensive)
        if chosen not in valid_codes:
            chosen = min(valid_codes, key=lambda c: abs(c - chosen))
        return int(chosen)
    else:
        med_raw = _median(codes)
        # Snap median to nearest valid code; if multiple valid codes are
        # equidistant, deterministic-hash pick (no longer min-bias).
        min_dist = min(abs(c - med_raw) for c in valid_codes)
        candidates = [c for c in valid_codes if abs(c - med_raw) == min_dist]
        chosen = _deterministic_pick(candidates)
        return int(chosen)


def synthesize_panel_median_records(
    records: list[dict[str, Any]],
    valid_codes_by_item: dict[str, list[int]],
    expected_models: list[str],
    item_format_by_id: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """For each (respondent, condition, item, sample_idx), aggregate model
    codes into a single panel code and re-score against truth.

    Locked rule: median for Likert, mode for binary/categorical (and for
    PARTYID when any model outputs 7 — see _panel_aggregate_code).

    Excludes any (respondent, condition, item, sample_idx) where ANY model
    parse-failed → no implicit imputation.

    Args:
        valid_codes_by_item: {item_id: [valid integer codes]}
        expected_models: REQUIRED locked panel list (e.g. MODEL_PANEL_PRIMARY).
            Tuples missing any expected model are dropped (no silent
            partial-panel synthesis). Per Codex audit 2026-05-06 — earlier
            versions made this optional; the helper contract is now strict.
        item_format_by_id: {item_id: 'binary'|'likert3'|'likert4'|...|'categorical'}.
            If None, defaults to inferring from len(valid_codes) (likert{N} for ≥3,
            binary for 2). Pass-through expected to come from primary_eval +
            sensitivity_eval format declarations.
    """
    if not expected_models:
        raise ValueError(
            "expected_models is required (no silent partial-panel synthesis). "
            "Pass the locked panel list, e.g. list(MODEL_PANEL_PRIMARY)."
        )
    item_format_by_id = item_format_by_id or {}

    # Group by (respondent_id, condition) → list of model records
    grouped: dict[tuple, list[dict]] = {}
    for r in records:
        key = (r["respondent_id"], r["condition"])
        grouped.setdefault(key, []).append(r)

    out_records = []
    for (rid, cond), model_records in grouped.items():
        models_present = {r.get("model") for r in model_records}
        if expected_models is not None:
            missing = set(expected_models) - models_present
            if missing:
                # Skip incomplete-panel groups; caller can audit.
                continue
        if len(model_records) < 2:
            continue
        panel_per_item: dict[str, list[dict]] = {}
        all_items: set = set()
        for mr in model_records:
            all_items.update(mr.get("per_item_scores", {}).keys())
        for item_id in all_items:
            sample_lists = [mr.get("per_item_scores", {}).get(item_id, []) for mr in model_records]
            n_samples = min(len(sl) for sl in sample_lists) if sample_lists else 0
            samples_out: list[dict] = []
            for s_idx in range(n_samples):
                codes = []
                truth = None
                for sl in sample_lists:
                    s = sl[s_idx]
                    truth = s.get("truth") if truth is None else truth
                    if s.get("parse_fail") or s.get("persona_code") is None:
                        codes = None
                        break
                    codes.append(int(s["persona_code"]))
                if codes is None:
                    samples_out.append({
                        "treatment": None, "abs_err": None, "within1": None,
                        "cat_match": None, "parse_fail": True, "persona_code": None,
                        "truth": truth, "skipped_missing_truth": truth is None,
                    })
                    continue

                vcodes = valid_codes_by_item.get(
                    item_id, list(range(int(min(codes)), int(max(codes)) + 1))
                )
                # Resolve item format: prefer explicit per-item map; else infer.
                fmt = item_format_by_id.get(item_id)
                if fmt is None:
                    fmt = "binary" if len(vcodes) == 2 else f"likert{len(vcodes)}"

                panel_code = _panel_aggregate_code(codes, vcodes, item_id, fmt, respondent_id=rid)

                if truth is None:
                    samples_out.append({
                        "treatment": None, "abs_err": None, "within1": None,
                        "cat_match": None, "parse_fail": False,
                        "persona_code": panel_code, "truth": None,
                        "skipped_missing_truth": True,
                    })
                    continue

                # Re-classify treatment using the same rule score_item uses
                treatment = classify_item_for_scoring(item_id, fmt, panel_code, int(truth))
                if treatment == "likert":
                    abs_err = abs(panel_code - int(truth))
                    samples_out.append({
                        "treatment": "likert", "abs_err": abs_err,
                        "within1": int(abs_err <= 1), "cat_match": None,
                        "parse_fail": False, "persona_code": panel_code,
                        "truth": int(truth), "skipped_missing_truth": False,
                    })
                else:
                    samples_out.append({
                        "treatment": "categorical", "abs_err": None, "within1": None,
                        "cat_match": int(panel_code == int(truth)),
                        "parse_fail": False, "persona_code": panel_code,
                        "truth": int(truth), "skipped_missing_truth": False,
                    })
            panel_per_item[item_id] = samples_out
        out_records.append({
            "respondent_id": rid,
            "condition": cond,
            "model": "panel",
            "per_item_scores": panel_per_item,
        })
    return out_records


def cross_model_agreement_pct(
    records: list[dict[str, Any]],
    expected_models: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """% of (respondent, condition, item, sample_idx) tuples where ALL
    expected models parsed successfully AND output the same persona_code.

    Locked design (gss_phase1_design.md §12 + Codex audit 2026-05-06):
    strict definition — agreement requires ALL models present + parsed +
    identical. Tuples where any model parse-failed or is missing from the
    record set count as NON-agreement (numerator=0) and ARE included in the
    denominator. This avoids inflating agreement under parse failures.

    Args:
        expected_models: list of model slugs that should be present.
            If None, defaults to set of distinct models found in records.

    Returns: {
        condition: {
            "agreement_pct": float,
            "n_tuples": int,
            "n_strict_agreed": int,
            "n_lost_to_parse_or_missing": int,
        }
    }
    """
    from collections import defaultdict

    if expected_models is None:
        expected_models = sorted({r.get("model") for r in records if r.get("model")})

    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        grouped[(r["respondent_id"], r["condition"])].append(r)

    by_cond_total: dict[str, int] = defaultdict(int)
    by_cond_agreed: dict[str, int] = defaultdict(int)
    by_cond_lost: dict[str, int] = defaultdict(int)

    for (rid, cond), model_records in grouped.items():
        records_by_model = {r.get("model"): r for r in model_records}
        # Are all expected models present for this (rid, cond)?
        all_present = all(m in records_by_model for m in expected_models)
        items: set = set()
        for mr in model_records:
            items.update(mr.get("per_item_scores", {}).keys())
        for item_id in items:
            sample_lists_by_model = {
                m: records_by_model[m].get("per_item_scores", {}).get(item_id, [])
                for m in expected_models if m in records_by_model
            }
            if not sample_lists_by_model:
                continue
            n_samples = min(len(sl) for sl in sample_lists_by_model.values()) if sample_lists_by_model else 0
            for s_idx in range(n_samples):
                by_cond_total[cond] += 1
                if not all_present:
                    by_cond_lost[cond] += 1
                    continue
                codes = []
                any_fail = False
                for m in expected_models:
                    sl = sample_lists_by_model[m]
                    s = sl[s_idx]
                    if s.get("parse_fail") or s.get("persona_code") is None:
                        any_fail = True
                        break
                    codes.append(int(s["persona_code"]))
                if any_fail:
                    by_cond_lost[cond] += 1
                    continue
                if len(set(codes)) == 1:
                    by_cond_agreed[cond] += 1

    out: dict[str, dict[str, Any]] = {}
    for cond, n_total in by_cond_total.items():
        out[cond] = {
            "agreement_pct": round(100 * by_cond_agreed[cond] / n_total, 1) if n_total else 0.0,
            "n_tuples": n_total,
            "n_strict_agreed": by_cond_agreed[cond],
            "n_lost_to_parse_or_missing": by_cond_lost[cond],
        }
    return out


def compute_phase1_headline_multimodel(
    records: list[dict[str, Any]],
    valid_codes_by_item: dict[str, list[int]],
    item_format_by_id: dict[str, str] | None = None,
    expected_models: list[str] | None = None,
    bootstrap_B: int = 1000,
    seed: int = 42,
) -> dict[str, Any]:
    """End-to-end multi-model headline.

    Args:
        expected_models: locked panel list (e.g. MODEL_PANEL_PRIMARY).
            Strict cross-model agreement requires all expected models present
            + parsed + identical. If None, defaults to models observed in
            records.
        item_format_by_id: explicit per-item format ('binary' / 'likert3' /
            'likert4' / etc.) used by panel-mode-vs-median routing.

    Returns:
        {
            "n_models": int,
            "models": [...],
            "per_model": {model: compute_phase1_headline output},
            "panel": compute_phase1_headline output for panel synthesis,
            "cross_model_agreement": {condition: {pct, n_tuples, n_agreed, n_lost}},
        }
    """
    models = sorted({r.get("model") for r in records if r.get("model")})
    if not models:
        raise ValueError("No 'model' field in records — use compute_phase1_headline for single-model")
    if expected_models is None:
        expected_models = models

    out: dict[str, Any] = {
        "n_models": len(models),
        "models": models,
        "expected_models": list(expected_models),
        "per_model": {},
        "panel": None,
        "cross_model_agreement": cross_model_agreement_pct(records, expected_models=expected_models),
    }

    for m in models:
        m_records = filter_records_by_model(records, m)
        out["per_model"][m] = compute_phase1_headline(
            m_records, bootstrap_B=bootstrap_B, seed=seed
        )

    if len(models) >= 2:
        panel_records = synthesize_panel_median_records(
            records,
            valid_codes_by_item,
            expected_models=list(expected_models),
            item_format_by_id=item_format_by_id,
        )
        out["panel"] = compute_phase1_headline(
            panel_records, bootstrap_B=bootstrap_B, seed=seed
        )
    return out


# ---------------------------------------------------------------------------
# AUDIT-E smoke test — synthetic per-respondent records, hand-checked
# ---------------------------------------------------------------------------

def _audit_e_test():
    """Verify aggregation math and paired-bootstrap correctness on a
    synthetic dataset where the answers can be hand-calculated."""
    print("\n=== AUDIT-E: aggregation smoke test ===\n")

    # ---- Build synthetic records ----
    # 3 respondents. 3 items: ITEM_A (likert), ITEM_B (likert), ITEM_C (cat).
    # 2 samples per item.
    # Two conditions: "full" and "loo_drop_attitudinal".
    # Hand-calc the expected aggregates below.

    def make_item_score(treatment, abs_err=None, within1=None, cat_match=None, parse_fail=False):
        return {
            "treatment": treatment,
            "abs_err": abs_err,
            "within1": within1,
            "cat_match": cat_match,
            "parse_fail": parse_fail,
            "skipped_missing_truth": False,
        }

    records = [
        # Respondent 1, full: ITEM_A errs [0, 1], ITEM_B errs [2, 0], ITEM_C cat [1, 0]
        {
            "respondent_id": 1, "condition": "full",
            "per_item_scores": {
                "ITEM_A": [
                    make_item_score("likert", abs_err=0, within1=1),
                    make_item_score("likert", abs_err=1, within1=1),
                ],
                "ITEM_B": [
                    make_item_score("likert", abs_err=2, within1=0),
                    make_item_score("likert", abs_err=0, within1=1),
                ],
                "ITEM_C": [
                    make_item_score("categorical", cat_match=1),
                    make_item_score("categorical", cat_match=0),
                ],
            },
        },
        # Respondent 2, full: ITEM_A errs [1, 1], ITEM_B errs [3, 2], ITEM_C cat [1, 1]
        {
            "respondent_id": 2, "condition": "full",
            "per_item_scores": {
                "ITEM_A": [
                    make_item_score("likert", abs_err=1, within1=1),
                    make_item_score("likert", abs_err=1, within1=1),
                ],
                "ITEM_B": [
                    make_item_score("likert", abs_err=3, within1=0),
                    make_item_score("likert", abs_err=2, within1=0),
                ],
                "ITEM_C": [
                    make_item_score("categorical", cat_match=1),
                    make_item_score("categorical", cat_match=1),
                ],
            },
        },
        # Respondent 3, full: ITEM_A errs [0, 0], ITEM_B errs [1, 1], ITEM_C cat [0, 0]
        {
            "respondent_id": 3, "condition": "full",
            "per_item_scores": {
                "ITEM_A": [
                    make_item_score("likert", abs_err=0, within1=1),
                    make_item_score("likert", abs_err=0, within1=1),
                ],
                "ITEM_B": [
                    make_item_score("likert", abs_err=1, within1=1),
                    make_item_score("likert", abs_err=1, within1=1),
                ],
                "ITEM_C": [
                    make_item_score("categorical", cat_match=0),
                    make_item_score("categorical", cat_match=0),
                ],
            },
        },
        # Same 3 respondents under loo_drop_attitudinal — Likert errors are
        # WORSE (LOO removes useful features).
        {
            "respondent_id": 1, "condition": "loo_drop_attitudinal",
            "per_item_scores": {
                "ITEM_A": [
                    make_item_score("likert", abs_err=2, within1=0),
                    make_item_score("likert", abs_err=2, within1=0),
                ],
                "ITEM_B": [
                    make_item_score("likert", abs_err=3, within1=0),
                    make_item_score("likert", abs_err=2, within1=0),
                ],
                "ITEM_C": [
                    make_item_score("categorical", cat_match=0),
                    make_item_score("categorical", cat_match=0),
                ],
            },
        },
        {
            "respondent_id": 2, "condition": "loo_drop_attitudinal",
            "per_item_scores": {
                "ITEM_A": [
                    make_item_score("likert", abs_err=2, within1=0),
                    make_item_score("likert", abs_err=1, within1=1),
                ],
                "ITEM_B": [
                    make_item_score("likert", abs_err=3, within1=0),
                    make_item_score("likert", abs_err=3, within1=0),
                ],
                "ITEM_C": [
                    make_item_score("categorical", cat_match=0),
                    make_item_score("categorical", cat_match=0),
                ],
            },
        },
        {
            "respondent_id": 3, "condition": "loo_drop_attitudinal",
            "per_item_scores": {
                "ITEM_A": [
                    make_item_score("likert", abs_err=2, within1=0),
                    make_item_score("likert", abs_err=1, within1=1),
                ],
                "ITEM_B": [
                    make_item_score("likert", abs_err=2, within1=0),
                    make_item_score("likert", abs_err=2, within1=0),
                ],
                "ITEM_C": [
                    make_item_score("categorical", cat_match=1),
                    make_item_score("categorical", cat_match=0),
                ],
            },
        },
    ]

    # ---- Hand-calc expected values ----
    # Full / likert_mae:
    #   R1: errs [0,1,2,0]  → mean = 0.75
    #   R2: errs [1,1,3,2]  → mean = 1.75
    #   R3: errs [0,0,1,1]  → mean = 0.5
    #   respondent_macro = mean(0.75, 1.75, 0.5) = 1.0
    expected_full_likert_macro = 1.0

    # Full / likert_mae item-macro:
    #   ITEM_A errs across resp×samples: [0,1, 1,1, 0,0] → mean = 3/6 = 0.5
    #   ITEM_B errs: [2,0, 3,2, 1,1] → mean = 9/6 = 1.5
    #   item_macro = mean(0.5, 1.5) = 1.0
    expected_full_likert_item_macro = 1.0

    # Full / likert_mae pooled:
    #   all 12 likert errs: [0,1,2,0, 1,1,3,2, 0,0,1,1] → sum=12 → mean 1.0
    expected_full_likert_pooled = 1.0

    # Full / cat_match_pct respondent-macro:
    #   R1: [1, 0] → 50%
    #   R2: [1, 1] → 100%
    #   R3: [0, 0] → 0%
    #   respondent_macro = mean(50, 100, 0) = 50%
    expected_full_cat_macro = 50.0

    # ---- Run aggregations ----
    print("[1] Aggregating Full condition")
    agg_full_likert = aggregate_condition(records, "full", "likert_mae")
    print(f"   respondent_macro: {agg_full_likert['respondent_macro']:.3f}  (expected {expected_full_likert_macro})")
    print(f"   item_macro:       {agg_full_likert['item_macro']:.3f}  (expected {expected_full_likert_item_macro})")
    print(f"   pooled:           {agg_full_likert['pooled']:.3f}  (expected {expected_full_likert_pooled})")
    assert abs(agg_full_likert["respondent_macro"] - expected_full_likert_macro) < 1e-9
    assert abs(agg_full_likert["item_macro"] - expected_full_likert_item_macro) < 1e-9
    assert abs(agg_full_likert["pooled"] - expected_full_likert_pooled) < 1e-9
    print("   ✓ all three aggregations match")

    print("\n[2] Categorical aggregation (Full)")
    agg_full_cat = aggregate_condition(records, "full", "cat_match_pct")
    print(f"   respondent_macro: {agg_full_cat['respondent_macro']:.1f}%  (expected {expected_full_cat_macro})")
    assert abs(agg_full_cat["respondent_macro"] - expected_full_cat_macro) < 1e-9
    print("   ✓ matches")

    print("\n[3] Bootstrap CI (Full likert_mae)")
    ci_lo, ci_hi = bootstrap_ci(agg_full_likert["per_respondent_values"], B=1000, seed=42)
    print(f"   per-respondent values: {agg_full_likert['per_respondent_values']}")
    print(f"   95% CI: [{ci_lo:.3f}, {ci_hi:.3f}]")
    # With per-resp values (0.75, 1.75, 0.5) and N=3, CI should be quite wide
    # but bracket the point estimate 1.0
    assert ci_lo <= 1.0 <= ci_hi, f"CI [{ci_lo}, {ci_hi}] does not bracket point estimate 1.0"
    print("   ✓ CI brackets point estimate")

    print("\n[4] Paired bootstrap LOO delta (loo_drop_attitudinal vs full)")
    # Expected per-respondent deltas:
    #   LOO_likert_mae per respondent:
    #     R1: errs [2,2,3,2] → 9/4 = 2.25
    #     R2: errs [2,1,3,3] → 9/4 = 2.25
    #     R3: errs [2,1,2,2] → 7/4 = 1.75
    #   Full per-resp: 0.75, 1.75, 0.5
    #   Per-resp delta: 2.25-0.75=1.5, 2.25-1.75=0.5, 1.75-0.5=1.25
    #   mean delta = (1.5 + 0.5 + 1.25)/3 = 3.25/3 ≈ 1.0833
    expected_mean_delta = (1.5 + 0.5 + 1.25) / 3
    full_per_resp = aggregate_condition(records, "full", "likert_mae")["per_respondent_values"]
    loo_per_resp = aggregate_condition(records, "loo_drop_attitudinal", "likert_mae")["per_respondent_values"]
    delta_result = paired_bootstrap_loo_delta(full_per_resp, loo_per_resp, B=1000, seed=42)
    print(f"   per-resp Full: {full_per_resp}")
    print(f"   per-resp LOO:  {loo_per_resp}")
    print(f"   paired mean Δ:  {delta_result['mean_delta']:.4f}  (expected {expected_mean_delta:.4f})")
    print(f"   95% CI:         [{delta_result['ci_lo']:.4f}, {delta_result['ci_hi']:.4f}]")
    print(f"   n_paired:       {delta_result['n_paired_respondents']}")
    assert abs(delta_result["mean_delta"] - expected_mean_delta) < 1e-9, \
        f"paired mean delta should equal mean of per-resp deltas; got {delta_result['mean_delta']} vs expected {expected_mean_delta}"
    assert delta_result["n_paired_respondents"] == 3
    # Δ should be positive (LOO hurt accuracy → MAE went up)
    assert delta_result["mean_delta"] > 0
    print("   ✓ paired delta matches per-resp delta mean exactly (paired bootstrap property)")

    print("\n[5] End-to-end compute_phase1_headline()")
    headline = compute_phase1_headline(
        records,
        conditions=["full", "loo_drop_attitudinal"],
        metrics=("likert_mae", "cat_match_pct"),
        bootstrap_B=500,  # smaller for speed
        seed=42,
        loo_conditions=("loo_drop_attitudinal",),
    )
    full_lik = headline["per_condition"]["full"]["likert_mae"]
    print(f"   Full likert_mae headline: {full_lik['respondent_macro']:.3f} "
          f"[{full_lik['respondent_macro_ci_lo']:.3f}, {full_lik['respondent_macro_ci_hi']:.3f}]")
    delta = headline["loo_deltas"]["loo_drop_attitudinal"]["likert_mae"]
    print(f"   LOO Δ likert_mae:         {delta['mean_delta']:.3f} "
          f"[{delta['ci_lo']:.3f}, {delta['ci_hi']:.3f}]")
    assert abs(full_lik["respondent_macro"] - 1.0) < 1e-9
    assert delta["mean_delta"] > 0
    print("   ✓ end-to-end orchestrator works")

    print("\n✓ ALL AUDIT-E AGGREGATION TESTS PASSED")


def _audit_e_multimodel_test():
    """Smoke test for multi-model panel aggregation (task #13)."""
    print("\n=== AUDIT-E multi-model panel smoke test ===\n")

    def mk(treatment, abs_err=None, within1=None, cat_match=None, persona_code=None,
           truth=None, parse_fail=False):
        return {
            "treatment": treatment, "abs_err": abs_err, "within1": within1,
            "cat_match": cat_match, "persona_code": persona_code, "truth": truth,
            "parse_fail": parse_fail, "skipped_missing_truth": truth is None,
        }

    # 2 respondents × 2 conditions (full + loo) × 4 models × 2 items
    # Item ITEM_A: likert5, truth=3
    # Item ITEM_B: binary, truth=1
    valid_codes_by_item = {"ITEM_A": [1,2,3,4,5], "ITEM_B": [1,2]}

    def build_resp(rid, cond, model, item_a_code, item_b_code, truth_a=3, truth_b=1):
        scores = {}
        if item_a_code is not None:
            scores["ITEM_A"] = [mk("likert", abs_err=abs(item_a_code-truth_a),
                                   within1=int(abs(item_a_code-truth_a)<=1),
                                   persona_code=item_a_code, truth=truth_a)]
        if item_b_code is not None:
            scores["ITEM_B"] = [mk("categorical", cat_match=int(item_b_code==truth_b),
                                   persona_code=item_b_code, truth=truth_b)]
        return {"respondent_id": rid, "condition": cond, "model": model,
                "per_item_scores": scores}

    # 4 models all giving slightly different codes for resp 1, full
    # Resp 1 / full: A_codes [3, 3, 4, 3], B_codes [1, 1, 1, 2] → median A=3, B=1
    # Resp 1 / loo:  A_codes [4, 4, 5, 4], B_codes [2, 2, 1, 2] → median A=4, B=2
    # Resp 2 / full: A_codes [2, 3, 3, 3], B_codes [1, 1, 1, 1] → median A=3, B=1
    # Resp 2 / loo:  A_codes [3, 3, 4, 3], B_codes [2, 1, 1, 1] → median A=3, B=1
    models = ["m1", "m2", "m3", "m4"]
    records = []
    # resp 1 full
    a_codes = [3, 3, 4, 3]; b_codes = [1, 1, 1, 2]
    for i, m in enumerate(models):
        records.append(build_resp(1, "full", m, a_codes[i], b_codes[i]))
    # resp 1 loo
    a_codes = [4, 4, 5, 4]; b_codes = [2, 2, 1, 2]
    for i, m in enumerate(models):
        records.append(build_resp(1, "loo_drop_attitudinal", m, a_codes[i], b_codes[i]))
    # resp 2 full
    a_codes = [2, 3, 3, 3]; b_codes = [1, 1, 1, 1]
    for i, m in enumerate(models):
        records.append(build_resp(2, "full", m, a_codes[i], b_codes[i]))
    # resp 2 loo
    a_codes = [3, 3, 4, 3]; b_codes = [2, 1, 1, 1]
    for i, m in enumerate(models):
        records.append(build_resp(2, "loo_drop_attitudinal", m, a_codes[i], b_codes[i]))

    print(f"[1] built {len(records)} records ({len(records)//4} resp-conditions × 4 models)")

    # Cross-model agreement (strict — all 4 models present + parsed + identical)
    item_format_by_id = {"ITEM_A": "likert5", "ITEM_B": "binary"}
    agree = cross_model_agreement_pct(records, expected_models=models)
    print(f"\n[2] cross-model agreement (strict, all-4 required):")
    for c, info in agree.items():
        print(f"   {c:<28s} {info['agreement_pct']}%  "
              f"(n_tuples={info['n_tuples']}, agreed={info['n_strict_agreed']}, "
              f"lost={info['n_lost_to_parse_or_missing']})")
    # full: 4 (resp,item) tuples × 1 sample = 4 tuples
    # ITEM_A/r1 [3,3,4,3] → 0; ITEM_B/r1 [1,1,1,2] → 0; ITEM_A/r2 [2,3,3,3] → 0;
    # ITEM_B/r2 [1,1,1,1] → 1. Agreement = 1/4 = 25%.
    assert agree["full"]["agreement_pct"] == 25.0, f"expected full=25.0, got {agree['full']['agreement_pct']}"
    assert agree["full"]["n_tuples"] == 4
    assert agree["full"]["n_strict_agreed"] == 1
    print("   ✓ strict agreement % matches hand calc")

    # Panel synthesis (median for likert, mode for binary)
    panel = synthesize_panel_median_records(
        records, valid_codes_by_item, expected_models=list(models),
        item_format_by_id=item_format_by_id,
    )
    print(f"\n[3] panel synthesis: {len(panel)} records (median for ITEM_A likert, mode for ITEM_B binary)")
    # resp 1 full: ITEM_A codes [3,3,4,3] → median 3.0 → 3, abs_err=0;
    #              ITEM_B codes [1,1,1,2] → mode 1 (3 of 4), cat_match=1
    r1_full = next(r for r in panel if r["respondent_id"] == 1 and r["condition"] == "full")
    assert r1_full["per_item_scores"]["ITEM_A"][0]["abs_err"] == 0
    assert r1_full["per_item_scores"]["ITEM_B"][0]["cat_match"] == 1
    print("   ✓ resp 1 full panel ITEM_A median=3 abs_err=0, ITEM_B mode=1 cat_match=1")

    # resp 1 loo: ITEM_A codes [4,4,5,4] → median 4 → abs_err=1
    #              ITEM_B codes [2,2,1,2] → mode 2 → cat_match=0 (truth=1)
    r1_loo = next(r for r in panel if r["respondent_id"] == 1 and r["condition"] == "loo_drop_attitudinal")
    assert r1_loo["per_item_scores"]["ITEM_A"][0]["abs_err"] == 1
    assert r1_loo["per_item_scores"]["ITEM_B"][0]["cat_match"] == 0
    print("   ✓ resp 1 loo  panel ITEM_A median=4 abs_err=1, ITEM_B mode=2 cat_match=0")

    # Verify mode tie-break is now deterministic-but-unbiased (M5 fix
    # 2026-05-09 night). Prior bug: tie-break always picked min(candidates),
    # systematically biasing binary items toward code 1 (e.g., ABANY=YES,
    # CAPPUN=Favor, GUNLAW=Allowed). Fixed to use hash-based pick.
    # For codes=[1,1,2,2], the result is in {1, 2} but determined by hash.
    tied_a = _panel_aggregate_code([1, 1, 2, 2], [1, 2], "FAKE_BIN", "binary", respondent_id=1)
    tied_a_repeat = _panel_aggregate_code([1, 1, 2, 2], [1, 2], "FAKE_BIN", "binary", respondent_id=1)
    tied_b = _panel_aggregate_code([1, 1, 2, 2], [1, 2], "FAKE_BIN", "binary", respondent_id=2)
    assert tied_a in (1, 2), f"expected valid code; got {tied_a}"
    assert tied_a == tied_a_repeat, f"deterministic: same inputs must give same output (got {tied_a} vs {tied_a_repeat})"
    print(f"   ✓ binary tie [1,1,2,2] → mode in {{1,2}} (deterministic-hash, NOT min-biased): rid=1→{tied_a}, rid=2→{tied_b}")
    # Confirm symmetric across many respondent IDs (no systematic bias toward 1)
    bias_check = [_panel_aggregate_code([1,1,2,2], [1,2], "FAKE_BIN", "binary", respondent_id=i) for i in range(200)]
    pct_one = sum(1 for c in bias_check if c == 1) / len(bias_check)
    assert 0.35 < pct_one < 0.65, f"expected ~50/50 across rids (no bias); got {pct_one:.0%} ones"
    print(f"   ✓ tie-break unbiased across 200 rids: {pct_one:.0%} ones (target ~50%)")

    # PARTYID code-7 contingent: when any model outputs 7, use mode
    # codes=[3,4,7,7] → mode 7; should NOT be median 5.5→5/6
    pid_code = _panel_aggregate_code([3, 4, 7, 7], [0,1,2,3,4,5,6,7], "PARTYID", "likert7")
    assert pid_code == 7, f"PARTYID with 7 in codes should use mode; expected 7, got {pid_code}"
    print("   ✓ PARTYID [3,4,7,7] → mode=7 (any-model-7 triggers categorical)")

    # End-to-end multi-model headline
    print(f"\n[4] compute_phase1_headline_multimodel()")
    out = compute_phase1_headline_multimodel(
        records, valid_codes_by_item,
        item_format_by_id=item_format_by_id,
        expected_models=models,
        bootstrap_B=200,
    )
    print(f"   models tracked:           {out['models']}")
    print(f"   has per-model headlines:  {list(out['per_model'].keys())}")
    print(f"   has panel:                {out['panel'] is not None}")
    print(f"   cross-model agreement:    {out['cross_model_agreement']}")
    panel_full = out["panel"]["per_condition"]["full"]["likert_mae"]
    print(f"   panel Full likert_mae:    {panel_full['respondent_macro']:.3f} "
          f"[{panel_full['respondent_macro_ci_lo']:.3f}, {panel_full['respondent_macro_ci_hi']:.3f}]")
    assert "loo_drop_attitudinal" in out["panel"]["loo_deltas"]
    print("   ✓ multi-model orchestrator returns expected structure")

    # Codex 2026-05-06 fix: helper now requires expected_models (no silent partial)
    print("\n[5] synthesize_panel_median_records contract: expected_models is required")
    try:
        synthesize_panel_median_records(records, valid_codes_by_item, expected_models=None)
        raise AssertionError("expected_models=None should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ raises ValueError when expected_models is None: {str(e)[:60]}…")
    try:
        synthesize_panel_median_records(records, valid_codes_by_item, expected_models=[])
        raise AssertionError("expected_models=[] should have raised ValueError")
    except ValueError:
        print(f"   ✓ raises ValueError when expected_models is []")

    print("\n✓ ALL MULTI-MODEL AGGREGATION TESTS PASSED")


def _audit_d_test():
    """AUDIT-D smoke test: pick a sensitivity_eval item that's also in a feature
    bin, build a sensitivity-pass prompt for one respondent, and assert that
    the excluded item does NOT appear in the prompt while other items DO.

    Locked rule: when predicting sensitivity item X, X is excluded from the
    persona's feature list; OTHER sensitivity items in feature bins remain.
    """
    print("\n=== AUDIT-D: sensitivity per-item exclusion smoke test ===\n")
    taxonomy = load_taxonomy()
    sample = sample_respondents(n=1, seed=42)
    respondent = sample.iloc[0]
    rid = int(respondent.get("ID_", -1))

    # Pick 3 sensitivity items that ARE in feature bins (any bin) and verify
    # exclusion works for each.
    sens = taxonomy["_sensitivity_eval_set"]
    feats = taxonomy["_all_features_set"]
    overlap = sorted(sens & feats)
    test_targets = ["ABDEFECT", "ATTEND", "HAPPY"]  # all in overlap; one per typical bin
    test_targets = [t for t in test_targets if t in overlap]
    print(f"Test targets (sensitivity items also in feature bins): {test_targets}\n")

    full_prompt, full_stats = build_persona_prompt(respondent, taxonomy, drop_bin=None)
    print(f"FULL condition (no exclusion) — total features: {full_stats['total_features']}")

    for target in test_targets:
        excl_prompt, excl_stats = build_persona_prompt(
            respondent, taxonomy, drop_bin=None, exclude_vars=[target]
        )
        # The target's variable label appears in the prompt as
        # "- {get_variable_label(target)}: ..." — check exact line presence.
        var_label = get_variable_label(target).strip()
        target_line_marker = f"- {var_label}:"

        target_in_full = target_line_marker in full_prompt
        target_in_excl = target_line_marker in excl_prompt

        # Pick another item that ALSO appears in the full prompt as a real feature
        # (i.e., respondent answered it). The assertion below requires it to
        # still be present in the excluded prompt — this protects against future
        # regressions where exclude_vars accidentally drops too much.
        other = None
        other_marker = None
        for cand in [x for x in test_targets if x != target]:
            cand_label = get_variable_label(cand).strip()
            cand_marker = f"- {cand_label}:"
            if cand_marker in full_prompt:
                other = cand
                other_marker = cand_marker
                break
        other_still_present = (other_marker in excl_prompt) if other_marker else None

        size_diff_full_minus_excl = full_stats["total_features"] - excl_stats["total_features"]
        print(f"--- excluding {target} ('{var_label}') ---")
        print(f"   in FULL prompt:                       {'YES' if target_in_full else 'no  (item not asked of respondent — skip)'}")
        print(f"   in EXCLUDED prompt:                   {'YES (BUG)' if target_in_excl else 'no  ✓'}")
        if other:
            print(f"   other sens item {other!r:<10s} still present: {'yes ✓' if other_still_present else 'NO (BUG)'}")
        print(f"   feature count (full - excluded):      {size_diff_full_minus_excl:+d} (expected +1 if target was answered, 0 otherwise)")
        print()

        if target_in_full:
            # Hard assertions: the implementation MUST excise the target and
            # MUST NOT collaterally remove other sensitivity-in-feature items.
            assert not target_in_excl, f"BUG: {target} still appears in excluded prompt"
            assert size_diff_full_minus_excl == 1, (
                f"BUG: feature count delta should be 1 when target was answered, got "
                f"{size_diff_full_minus_excl}"
            )
            if other_marker is not None:
                assert other_still_present, (
                    f"BUG: excluding {target} unexpectedly also removed {other} "
                    f"(other sensitivity items must remain — locked rule)"
                )
        # if target wasn't in full (respondent didn't answer it), exclusion is a no-op — that's fine

    print("✓ AUDIT-D: per-item exclusion verified on respondent ID_=" + str(rid))


def _audit_c_test():
    """Run hand-crafted scoring scenarios to verify the logic.
    Each scenario asserts an expected outcome.
    """
    print("\n=== AUDIT-C: scoring smoke test ===\n")

    # --- C-test 1: parse_response edge cases ---
    print("[1] parse_response edge cases")
    cases = [
        ("4", [1,2,3,4,5,6,7], 4),
        (" 4 ", [1,2,3,4,5,6,7], 4),
        ("I would say 4", [1,2,3,4,5,6,7], 4),
        ("4. Moderate", [1,2,3,4,5,6,7], 4),
        ("8", [1,2,3,4,5,6,7], None),       # out of range
        ("definitely four", [1,2,3,4,5,6,7], None),  # word, not integer
        ("", [1,2,3,4,5,6,7], None),
        (None, [1,2,3,4,5,6,7], None),
    ]
    for raw, codes, expected in cases:
        got = parse_response(raw, codes)
        ok = got == expected
        sym = "✓" if ok else "✗"
        print(f"    {sym} parse_response({raw!r}, {codes[:3]}...) → {got!r} (expected {expected!r})")
        assert ok, f"parse_response({raw!r}) failed"

    # --- C-test 2: Likert scoring (POLVIEWS, truth=4) ---
    print("\n[2] Likert MAE (POLVIEWS, truth=4)")
    valid = [1,2,3,4,5,6,7]
    s1 = score_item("POLVIEWS", "likert7", valid, "4", 4)
    assert s1["treatment"] == "likert" and s1["abs_err"] == 0 and s1["within1"] == 1
    print(f"    ✓ persona='4', truth=4 → treatment={s1['treatment']}, abs_err={s1['abs_err']}, within1={s1['within1']}")

    s2 = score_item("POLVIEWS", "likert7", valid, "6", 4)
    assert s2["treatment"] == "likert" and s2["abs_err"] == 2 and s2["within1"] == 0
    print(f"    ✓ persona='6', truth=4 → abs_err={s2['abs_err']}, within1={s2['within1']}")

    s3 = score_item("POLVIEWS", "likert7", valid, "5", 4)
    assert s3["abs_err"] == 1 and s3["within1"] == 1
    print(f"    ✓ persona='5', truth=4 → within1={s3['within1']} (boundary)")

    # --- C-test 3: Binary scoring (CAPPUN as categorical) ---
    print("\n[3] Binary categorical (CAPPUN)")
    s4 = score_item("CAPPUN", "binary", [1,2], "1", 1)
    assert s4["treatment"] == "categorical" and s4["cat_match"] == 1 and s4["abs_err"] is None
    print(f"    ✓ binary same code → cat_match=1, abs_err is None (no Likert)")

    s5 = score_item("CAPPUN", "binary", [1,2], "2", 1)
    assert s5["cat_match"] == 0
    print(f"    ✓ binary different code → cat_match=0")

    # --- C-test 4: PARTYID special case ---
    print("\n[4] PARTYID contingent treatment")
    valid_p = [0,1,2,3,4,5,6,7]
    # Both 0-6 → Likert
    s6 = score_item("PARTYID", "likert7", valid_p, "2", 5)
    assert s6["treatment"] == "likert" and s6["abs_err"] == 3
    print(f"    ✓ persona=2, truth=5 (both 0-6) → likert, abs_err=3")
    # Truth=7 → categorical
    s7 = score_item("PARTYID", "likert7", valid_p, "2", 7)
    assert s7["treatment"] == "categorical" and s7["cat_match"] == 0
    print(f"    ✓ persona=2, truth=7 → categorical (truth is 'Other party'), cat_match=0")
    # Persona=7 → categorical
    s8 = score_item("PARTYID", "likert7", valid_p, "7", 3)
    assert s8["treatment"] == "categorical" and s8["cat_match"] == 0
    print(f"    ✓ persona=7, truth=3 → categorical (persona is 'Other party'), cat_match=0")
    # Both 7 → categorical match
    s9 = score_item("PARTYID", "likert7", valid_p, "7", 7)
    assert s9["treatment"] == "categorical" and s9["cat_match"] == 1
    print(f"    ✓ persona=7, truth=7 (both 'Other') → cat_match=1")

    # --- C-test 5: Parse failure ---
    print("\n[5] Parse failure handling")
    s10 = score_item("POLVIEWS", "likert7", valid, "I refuse to answer", 4)
    assert s10["parse_fail"] is True and s10["abs_err"] is None and s10["cat_match"] is None
    print(f"    ✓ unparseable → parse_fail=True, no metrics populated")

    # --- C-test 6: Missing truth ---
    print("\n[6] Missing-truth skip")
    s11 = score_item("POLVIEWS", "likert7", valid, "4", None)
    assert s11["skipped_missing_truth"] is True and s11["abs_err"] is None
    print(f"    ✓ truth=None → skipped_missing_truth=True")

    # --- C-test 7: Aggregation across multiple items + samples ---
    print("\n[7] Aggregation: mixed Likert + categorical + 2 samples + 1 parse fail + 1 missing")
    per_item = {
        # POLVIEWS truth=4, samples [4, 5] → both likert; abs_err [0, 1]; within1 [1, 1]
        "POLVIEWS": [
            score_item("POLVIEWS", "likert7", valid, "4", 4),
            score_item("POLVIEWS", "likert7", valid, "5", 4),
        ],
        # CAPPUN truth=1, samples [1, 2] → both categorical; cat_match [1, 0]
        "CAPPUN": [
            score_item("CAPPUN", "binary", [1,2], "1", 1),
            score_item("CAPPUN", "binary", [1,2], "2", 1),
        ],
        # GUNLAW truth=2, sample 0 parses, sample 1 unparseable
        "GUNLAW": [
            score_item("GUNLAW", "binary", [1,2], "2", 2),
            score_item("GUNLAW", "binary", [1,2], "uh idk", 2),  # parse fail
        ],
        # FECHLD truth missing for this respondent
        "FECHLD": [
            score_item("FECHLD", "likert4", [1,2,3,4], "2", None),
            score_item("FECHLD", "likert4", [1,2,3,4], "3", None),
        ],
    }
    agg = aggregate_respondent_condition(per_item)
    print(f"    aggregated: {agg}")
    # Likert: POLVIEWS samples 0+1 → errs [0, 1] → MAE = 0.5; within1 = 100%
    assert agg["likert_mae"] == 0.5, f"likert_mae expected 0.5, got {agg['likert_mae']}"
    assert agg["likert_within1_pct"] == 100.0
    # Categorical: CAPPUN samples [1, 0] + GUNLAW sample 0 = [1] → 3 obs, 2 matches → 66.7%
    assert agg["cat_match_pct"] == 66.7, f"cat_match_pct expected 66.7, got {agg['cat_match_pct']}"
    # Parse fails: 1 (the GUNLAW "uh idk"); denom = 6 (excluding 2 missing-truth) → 16.7%
    assert agg["parse_failure_pct"] == 16.7, f"parse_failure_pct expected 16.7, got {agg['parse_failure_pct']}"
    assert agg["n_likert_obs"] == 2
    assert agg["n_cat_obs"] == 3
    assert agg["n_parse_fail"] == 1
    # Self-consistency: POLVIEWS (4 vs 5 → mismatch=0); CAPPUN (1 vs 2 → 0); GUNLAW (sample 1 unparseable → skipped); FECHLD (missing → skipped)
    # → 2 pairs, 0 matches → 0.0%
    assert agg["self_consistency_pct"] == 0.0
    print(f"    ✓ all aggregation assertions pass")

    print("\n✓ ALL AUDIT-C SCORING TESTS PASSED")


# ---------------------------------------------------------------------------
# Audit-A smoke test — run me to inspect what the persona will see
# ---------------------------------------------------------------------------

def _audit_a_print(n: int = 1, seed: int = 42, save_to: Path | None = None):
    """Print a sample persona prompt for review.

    Generates: 1 full prompt (verbose) + 4 LOO prompts (counts + section
    headers only, to verify the right bin was dropped).
    """
    taxonomy = load_taxonomy()
    sample = sample_respondents(n=n, seed=seed)
    print(f"\n=== Sampled {len(sample)} respondent(s) for AUDIT-A inspection ===")
    print(f"    Seed: {seed}, year: 2024")
    print(f"    Bin sizes (declared): " +
          ", ".join(f"{b}={len(taxonomy['_feature_bins_sets'][b])}" for b, _ in BIN_DISPLAY))

    for i, respondent in sample.iterrows():
        rid = int(respondent.get("ID_", -1))
        print(f"\n{'=' * 72}")
        print(f"RESPONDENT {i+1}/{len(sample)} — GSS ID_={rid}, AGE={respondent.get('AGE')}, "
              f"SEX={get_value_label('SEX', respondent.get('SEX'))}, "
              f"EDUC={get_value_label('EDUC', respondent.get('EDUC'))}")
        print('=' * 72)

        # ----- Full condition (verbose) -----
        full_prompt, full_stats = build_persona_prompt(respondent, taxonomy, drop_bin=None)
        print(f"\n--- CONDITION: FULL (all 4 bins) ---")
        print(f"  Bin item counts: " +
              ", ".join(f"{b}={full_stats[b]}" for b, _ in BIN_DISPLAY) +
              f"  → total features: {full_stats['total_features']}")
        print(f"  Prompt length: {full_stats['char_count']:,} chars (~{full_stats['approx_tokens']:,} tokens)")
        print(f"\n>>>>> FULL PROMPT BEGINS BELOW (this is what GPT-4o will literally see) >>>>>\n")
        print(full_prompt)
        print(f"\n<<<<< FULL PROMPT ENDS <<<<<")

        # ----- LOO conditions (summary only) -----
        print(f"\n--- CONDITION: LOO ABLATIONS (showing dropped bin → remaining bin counts) ---")
        for bin_name, _ in BIN_DISPLAY:
            _, loo_stats = build_persona_prompt(respondent, taxonomy, drop_bin=bin_name)
            print(f"  drop {bin_name:<14s}: " +
                  ", ".join(f"{b}={loo_stats[b]}" for b, _ in BIN_DISPLAY) +
                  f"  → total: {loo_stats['total_features']} features, "
                  f"~{loo_stats['approx_tokens']:,} tokens")

        if save_to is not None:
            (save_to.parent / f"audit_a_respondent_{rid}_full.txt").write_text(full_prompt)
            print(f"\n  Saved full prompt to {save_to.parent / f'audit_a_respondent_{rid}_full.txt'}")


def _cli():
    p = argparse.ArgumentParser(
        description="GSS Phase 1 persona pipeline. AUDIT-A through AUDIT-D locked; "
                    "AUDIT-E (aggregation) and LLM dispatcher pending. Use the smoke-test "
                    "flags below to inspect each locked checkpoint."
    )
    p.add_argument("--n", type=int, default=1, help="number of respondents to sample for inspection")
    p.add_argument("--seed", type=int, default=42, help="random seed for sampling (locked at 42)")
    p.add_argument("--print-prompt", action="store_true", help="run AUDIT-A: print a sample persona prompt")
    p.add_argument("--print-questions", action="store_true", help="run AUDIT-B: print all 12 primary_eval questions")
    p.add_argument("--test-question-options", action="store_true",
                   help="run AUDIT-B regression: assert no presented option label is non-substantive "
                        "(REFUSED / DK / IAP / NA) for any primary or sensitivity item")
    p.add_argument("--test-scoring", action="store_true", help="run AUDIT-C: hand-crafted scoring smoke tests")
    p.add_argument("--test-exclusion", action="store_true", help="run AUDIT-D: sensitivity per-item exclusion test")
    p.add_argument("--test-aggregation", action="store_true", help="run AUDIT-E: aggregation + paired bootstrap test")
    p.add_argument("--test-multimodel", action="store_true", help="run AUDIT-E multi-model panel test (task #13)")
    p.add_argument("--save", type=Path, default=None, help="optionally save full prompt to a file")
    return p.parse_args()


if __name__ == "__main__":
    args = _cli()
    if args.print_prompt:
        _audit_a_print(n=args.n, seed=args.seed, save_to=args.save)
    elif args.print_questions:
        _audit_b_print()
    elif args.test_question_options:
        _audit_b_test_no_refusal_options()
    elif args.test_scoring:
        _audit_c_test()
    elif args.test_exclusion:
        _audit_d_test()
    elif args.test_aggregation:
        _audit_e_test()
    elif args.test_multimodel:
        _audit_e_multimodel_test()
    else:
        print("Pipeline scaffold loaded.")
        print(f"  --print-prompt    : AUDIT-A persona-prompt sample (locked)")
        print(f"  --print-questions : AUDIT-B eval-question texts (in review)")
        print(f"Taxonomy: {TAXONOMY_PATH.name}")
        print(f"Loader:   gss_loader.py")
