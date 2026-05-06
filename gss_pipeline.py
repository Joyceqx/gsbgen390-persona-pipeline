"""GSS Phase 1 persona pipeline — for each sampled respondent, build persona
prompts under 5 conditions (full + 4 LOO ablations) and predict the 12
primary_eval items. Sensitivity pass over ~118 sensitivity_eval items uses
per-item exclusion.

Locked design: see gss_phase1_design.md (v 2026-05-05) and
gss_feature_taxonomy.json (v 0.3-locked-2026-05-05).

Audit checkpoint status:
  AUDIT-A persona prompt template     ✅ locked + smoke test (--print-prompt)
  AUDIT-B eval question phrasing      ✅ locked + smoke test (--print-questions)
  AUDIT-C scoring rules               ✅ locked + smoke test (--test-scoring)
  AUDIT-D sensitivity exclusion       ✅ locked + smoke test (--test-exclusion)
  AUDIT-E aggregation                 🔒 designed; implementation pending
  LLM dispatcher + driver             🔒 pending after AUDIT-E lock

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


def _format_feature_line(varname: str, value) -> str | None:
    """Render one feature as a labeled line.
    Returns None if the value is missing/coded-missing (caller filters these out).
    """
    if pd.isna(value) or int(value) in MISSING_CODES:
        return None
    var_label = get_variable_label(varname).strip()
    val_label = get_value_label(varname, value)
    if val_label is None:
        return None
    # Compact format: "- variable description: VALUE LABEL"
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
    Pulls from the parsed .do label set; sorted by code; excludes missing codes.
    """
    spec = _spec()
    set_name = spec["var_to_label_set"].get(item_id.upper())
    if not set_name:
        return []
    label_set = spec["value_label_sets"].get(set_name, {})
    pairs = [
        (code, label)
        for code, label in label_set.items()
        if code not in MISSING_CODES and code >= 0
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


def truth_code_or_none(value: Any) -> int | None:
    """Convert a respondent's raw GSS value into an integer truth code, or
    None if the value is GSS-missing-coded (in MISSING_CODES from
    gss_loader) or genuinely null.

    Use this BEFORE passing a respondent's value into score_item() as
    truth_code — it is the contract between raw GSS rows and the scorer.
    """
    if value is None or pd.isna(value):
        return None
    try:
        i = int(value)
    except (ValueError, TypeError):
        return None
    if i in MISSING_CODES:
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
    p.add_argument("--test-scoring", action="store_true", help="run AUDIT-C: hand-crafted scoring smoke tests")
    p.add_argument("--test-exclusion", action="store_true", help="run AUDIT-D: sensitivity per-item exclusion test")
    p.add_argument("--save", type=Path, default=None, help="optionally save full prompt to a file")
    return p.parse_args()


if __name__ == "__main__":
    args = _cli()
    if args.print_prompt:
        _audit_a_print(n=args.n, seed=args.seed, save_to=args.save)
    elif args.print_questions:
        _audit_b_print()
    elif args.test_scoring:
        _audit_c_test()
    elif args.test_exclusion:
        _audit_d_test()
    else:
        print("Pipeline scaffold loaded.")
        print(f"  --print-prompt    : AUDIT-A persona-prompt sample (locked)")
        print(f"  --print-questions : AUDIT-B eval-question texts (in review)")
        print(f"Taxonomy: {TAXONOMY_PATH.name}")
        print(f"Loader:   gss_loader.py")
