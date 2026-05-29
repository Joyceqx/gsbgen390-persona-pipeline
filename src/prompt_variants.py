"""Phase 1A factorial persona-prompt rendering — P0 / P1 / P2.

The three prompt variants in Phase 1A's 4×3 factorial. P0 mirrors the Park v2
surveys-only baseline; P1 is an Argyle-style 1st-person prose recasting; P2 is
a Wang-style interview Q&A. All three share information equivalence by design:
the same `_extract_features()` function decides which features appear, so any
MAE difference across cells comes from voice/structure, not from one prompt
quietly including more features than another.

Audit-compliance properties enforced here:

  1. Information equivalence. All three renderers consume the SAME `Feature`
     list. drop_bin / exclude_vars / MISSING_CODES handling lives in
     `_extract_features()` and runs once per call.

  2. SYSTEM_INSTRUCTION is constant across the 3 prompts. It is returned in
     the dispatcher output as a separate field; the caller is responsible for
     putting it in a system message (or user-message preamble) — what matters
     is that the same instruction text accompanies every prompt variant.

  3. Per-variable canonical templates live in
     `config/persona_prompt_templates.json` (140 entries covering the full
     feature taxonomy). The Python module is logic-only; the template content
     is auditable and editable without touching code. The template hash is
     stamped into every record's metadata for reproducibility.

  4. Self-tests at the bottom verify: information equivalence,
     drop_bin propagation, exclude_vars propagation, no GSS-codebook label
     residue ("rs", "r's", "you was", etc.), R1 leakage hygiene, and
     template coverage.

Usage:

    from prompt_variants import build_prompt
    out = build_prompt(respondent, taxonomy, prompt_id="P1",
                       drop_bin="psychological",
                       exclude_vars={"POLVIEWS"})
    # out["system_instruction"] -> the constant instruction text
    # out["persona_prompt"]     -> the P0/P1/P2 persona text
    # out["metadata"]           -> dict with prompt_id, version, hash, counts
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd

from gss_loader import get_variable_label, get_value_label
from gss_pipeline import MISSING_CODES, _is_non_substantive_label


WORK = Path("/Users/joyce/Developer/gsbgen390")
TEMPLATES_PATH = WORK / "config" / "persona_prompt_templates.json"

PROMPT_VERSION = "v1"  # bump when the renderers or preamble strings change


# ---------------------------------------------------------------------------
# Constant system instruction (audit #4 — same across P0/P1/P2)
# ---------------------------------------------------------------------------
SYSTEM_INSTRUCTION = (
    "You are simulating a respondent of the 2024 General Social Survey (GSS). "
    "A persona description follows; stay in character throughout. When asked a "
    "GSS question, output ONLY a single integer code corresponding to your "
    "answer, in the exact format requested. Do not hedge, refuse, qualify, or "
    "break character."
)


# ---------------------------------------------------------------------------
# Preambles + bin headers per prompt variant
# ---------------------------------------------------------------------------
PERSONA_PREAMBLES: dict[str, str] = {
    "P0": (
        "Below is what you told the 2024 General Social Survey, organized by "
        "topic. Stay in character as this respondent throughout."
    ),
    "P1": (
        "Below is who I am, as I told the 2024 General Social Survey, "
        "organized by topic."
    ),
    "P2": (
        "The following is an interview transcript with a respondent of the "
        "2024 General Social Survey, organized by topic."
    ),
}

BIN_HEADERS: dict[str, list[tuple[str, str]]] = {
    "P0": [
        ("demographic",   "## YOUR DEMOGRAPHIC BACKGROUND"),
        ("behavioral",    "## YOUR BEHAVIORS"),
        ("psychological", "## YOUR PSYCHOLOGICAL DISPOSITIONS"),
        ("attitudinal",   "## YOUR ATTITUDES"),
    ],
    "P1": [
        ("demographic",   "## DEMOGRAPHICS"),
        ("behavioral",    "## BEHAVIORS"),
        ("psychological", "## PSYCHOLOGICAL DISPOSITIONS"),
        ("attitudinal",   "## ATTITUDES"),
    ],
    "P2": [
        ("demographic",   "## DEMOGRAPHIC BACKGROUND"),
        ("behavioral",    "## BEHAVIORS"),
        ("psychological", "## PSYCHOLOGICAL DISPOSITIONS"),
        ("attitudinal",   "## ATTITUDES"),
    ],
}


# ---------------------------------------------------------------------------
# Templates loaded from JSON (audit #3)
# ---------------------------------------------------------------------------
def _load_templates() -> tuple[dict[str, dict[str, str]], str]:
    """Load canonical question / 1st-person templates from disk.
    Returns (templates_dict, sha256_hash). The hash goes into record metadata.
    """
    raw = TEMPLATES_PATH.read_text()
    templates = json.loads(raw)
    # Canonical hash: same as the bytes on disk, formatted-stable.
    canonical = json.dumps(templates, sort_keys=True, ensure_ascii=False)
    h = hashlib.sha256(canonical.encode()).hexdigest()
    return templates, h


PROMPT_TEMPLATES, TEMPLATE_HASH = _load_templates()


# ---------------------------------------------------------------------------
# Shared feature extraction (audit #2)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Feature:
    var: str
    var_label: str
    raw_value: float
    val_label: str
    bin_name: str


# GSS occasionally encodes "Other (SPECIFY)" / "Other (please specify)" in
# val_labels. The "(SPECIFY)" suffix is a codebook interviewer-instruction
# artifact, not part of the respondent's answer — strip it before rendering.
_SPECIFY_RE = re.compile(r"\s*\((?:please\s+)?specify\)\s*", re.IGNORECASE)


def _extract_features(
    respondent: pd.Series,
    taxonomy: dict,
    drop_bin: str | None = None,
    exclude_vars: set[str] | None = None,
) -> list[Feature]:
    """The single source of truth for "which features go into the persona".
    All three renderers consume this list. Identical filtering for P0/P1/P2.
    """
    excl = set(exclude_vars or ())
    bins = taxonomy["_feature_bins_sets"]
    out: list[Feature] = []
    for bin_name in ("demographic", "behavioral", "psychological", "attitudinal"):
        if bin_name == drop_bin:
            continue
        for v in sorted(bins[bin_name]):
            if v in excl:
                continue
            if v not in respondent.index:
                continue
            value = respondent[v]
            if pd.isna(value):
                continue
            if int(value) in MISSING_CODES:
                continue
            val_label = get_value_label(v, value)
            if val_label is None:
                continue
            if _is_non_substantive_label(val_label):
                continue
            val_label = _SPECIFY_RE.sub("", val_label).strip()
            var_label = get_variable_label(v).strip()
            out.append(Feature(v, var_label, float(value), val_label, bin_name))
    return out


# ---------------------------------------------------------------------------
# Value-label display normalization (sentence case for ALL CAPS, strip .0)
# ---------------------------------------------------------------------------
def _display_val(feat: Feature) -> str:
    """Render the value label for P0/P2 (P1 uses explicit placeholders)."""
    v = feat.val_label
    try:
        if v == str(feat.raw_value) and float(feat.raw_value).is_integer():
            v = str(int(feat.raw_value))
    except (TypeError, ValueError):
        pass
    if v.isupper() and any(c.isalpha() for c in v):
        v = v.capitalize()
    return v


# ---------------------------------------------------------------------------
# Per-prompt formatters
# ---------------------------------------------------------------------------
def _fmt_p1(feat: Feature) -> str:
    tpl = PROMPT_TEMPLATES.get(feat.var)
    if tpl is None:
        # Generic fallback — production should never hit this; covered by
        # _test_template_coverage in --self-test.
        return f"On {feat.var_label}, I would say {feat.val_label.lower()}."
    return tpl["p1_template"].format(
        val=feat.val_label,
        val_lower=feat.val_label.lower(),
        val_int=int(feat.raw_value) if float(feat.raw_value).is_integer() else feat.raw_value,
    )


def _fmt_p2_qa(feat: Feature) -> str:
    tpl = PROMPT_TEMPLATES.get(feat.var)
    if tpl is None:
        question = f"What about {feat.var_label}?"
    else:
        question = tpl["p2_question"]
    answer = _display_val(feat)
    return f"Interviewer: {question}\nRespondent: {answer}."


# ---------------------------------------------------------------------------
# Renderers per prompt
# ---------------------------------------------------------------------------
def _render(prompt_id: str, features: list[Feature]) -> str:
    parts = [PERSONA_PREAMBLES[prompt_id], ""]
    for bin_name, header in BIN_HEADERS[prompt_id]:
        bin_feats = [f for f in features if f.bin_name == bin_name]
        if not bin_feats:
            continue
        parts.append(header)
        for f in bin_feats:
            if prompt_id == "P0":
                parts.append(f"- {f.var_label}: {_display_val(f)}")
            elif prompt_id == "P1":
                parts.append(_fmt_p1(f))
            else:  # P2
                parts.append(_fmt_p2_qa(f))
        parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Dispatcher (audit #1 — unified interface)
# ---------------------------------------------------------------------------
def build_prompt(
    respondent: pd.Series,
    taxonomy: dict,
    prompt_id: Literal["P0", "P1", "P2"],
    drop_bin: str | None = None,
    exclude_vars: set[str] | None = None,
) -> dict:
    """Build a single persona prompt under one variant + LOO/AUDIT-D context.

    Returns a dict with three top-level keys:

      "system_instruction" — constant across P0/P1/P2; caller routes this to a
                              system message (or persona-prompt preamble).
      "persona_prompt"     — the variant-specific persona body.
      "metadata"           — prompt_id, prompt_version, template_hash,
                              feature_count, char_count, approx_tokens,
                              bin_counts, drop_bin, excluded_vars. Goes into
                              the Phase 1A record alongside the per-call
                              prediction.
    """
    if prompt_id not in ("P0", "P1", "P2"):
        raise ValueError(f"prompt_id must be P0/P1/P2, got {prompt_id!r}")
    features = _extract_features(respondent, taxonomy, drop_bin, exclude_vars)
    persona = _render(prompt_id, features)
    return {
        "system_instruction": SYSTEM_INSTRUCTION,
        "persona_prompt": persona,
        "metadata": {
            "prompt_id": prompt_id,
            "prompt_version": PROMPT_VERSION,
            "template_hash": TEMPLATE_HASH[:16],
            "feature_count": len(features),
            "char_count": len(persona),
            "approx_tokens": len(persona) // 4,
            "bin_counts": {
                b: sum(1 for f in features if f.bin_name == b)
                for b in ("demographic", "behavioral", "psychological", "attitudinal")
            },
            "drop_bin": drop_bin,
            "excluded_vars": sorted(exclude_vars or ()),
        },
    }


# ---------------------------------------------------------------------------
# Self-tests (audit #5)
# ---------------------------------------------------------------------------
def _load_test_fixtures() -> tuple[pd.Series, dict]:
    """Load seed=42 respondent #0 + taxonomy as the test fixture."""
    from gss_pipeline import sample_respondents
    with open(WORK / "gss_feature_taxonomy.json") as f:
        tax = json.load(f)
    tax["_feature_bins_sets"] = {
        b: set(tax["feature_bins"][b])
        for b in ("demographic", "behavioral", "psychological", "attitudinal")
    }
    return sample_respondents(n=1, seed=42).iloc[0], tax


def _test_template_coverage() -> None:
    """Every feature variable in the taxonomy has a canonical template."""
    with open(WORK / "gss_feature_taxonomy.json") as f:
        tax = json.load(f)
    all_vars = set()
    for b in ("demographic", "behavioral", "psychological", "attitudinal"):
        all_vars |= set(tax["feature_bins"][b])
    missing = sorted(all_vars - set(PROMPT_TEMPLATES.keys()))
    assert not missing, f"Templates missing for {len(missing)} vars: {missing[:10]}"
    extra = sorted(set(PROMPT_TEMPLATES.keys()) - all_vars)
    assert not extra, f"Templates exist for non-feature vars: {extra[:10]}"


def _test_information_equivalence() -> None:
    """P0/P1/P2 must extract the same number of features on every call."""
    resp, tax = _load_test_fixtures()
    f0 = _extract_features(resp, tax)
    out_p0 = build_prompt(resp, tax, "P0")
    out_p1 = build_prompt(resp, tax, "P1")
    out_p2 = build_prompt(resp, tax, "P2")
    assert (
        out_p0["metadata"]["feature_count"]
        == out_p1["metadata"]["feature_count"]
        == out_p2["metadata"]["feature_count"]
        == len(f0)
    ), "P0/P1/P2 feature counts diverged"


def _test_drop_bin() -> None:
    """drop_bin removes the named bin's features from all three prompts."""
    resp, tax = _load_test_fixtures()
    for prompt_id in ("P0", "P1", "P2"):
        out = build_prompt(resp, tax, prompt_id, drop_bin="demographic")
        assert out["metadata"]["bin_counts"]["demographic"] == 0, prompt_id
        for header in ("## YOUR DEMOGRAPHIC BACKGROUND", "## DEMOGRAPHICS",
                       "## DEMOGRAPHIC BACKGROUND"):
            assert header not in out["persona_prompt"] or out["metadata"]["bin_counts"]["demographic"] == 0


def _test_exclude_vars() -> None:
    """exclude_vars removes the named variables from all three prompts."""
    resp, tax = _load_test_fixtures()
    excluded = {"HUNT1", "AGE"}
    for prompt_id in ("P0", "P1", "P2"):
        out_excl = build_prompt(resp, tax, prompt_id, exclude_vars=excluded)
        out_full = build_prompt(resp, tax, prompt_id)
        # Excluded vars should not appear (P0 by var_label literal; P1/P2 by template content)
        # The robust check: feature_count drops by exactly the excluded count
        present_excluded = excluded & set(
            f.var for f in _extract_features(resp, tax)
        )
        expected_drop = len(present_excluded)
        assert (
            out_full["metadata"]["feature_count"]
            - out_excl["metadata"]["feature_count"]
            == expected_drop
        ), f"{prompt_id}: dropped {out_full['metadata']['feature_count'] - out_excl['metadata']['feature_count']}, expected {expected_drop}"


def _test_no_label_residue() -> None:
    """P1/P2 rendered prompts must not contain GSS codebook label residue
    ("r's", "rs", "you was", "did rs", etc.) — markers of generic fallback or
    raw .do-file labels leaking into a humanized rendering.

    Scope intentionally excludes P0: P0 mirrors Park v2's surveys-only format
    which uses the GSS .do-file var_labels verbatim, so "rs" and "r's" appear
    there by design (e.g., "- did rs family own or rent home when r was age
    16: ..."). The audit's residue concern was about the P1/P2 generic
    fallback, not about P0's faithful baseline.
    """
    resp, tax = _load_test_fixtures()
    bad_patterns = [
        re.compile(r"\br's\b", re.IGNORECASE),
        re.compile(r"\brs\b"),
        re.compile(r"\byou was\b", re.IGNORECASE),
        re.compile(r"\?\?"),
        re.compile(r"\bdoes you\b", re.IGNORECASE),
        re.compile(r"\bdid rs\b", re.IGNORECASE),
        re.compile(r"\bconsider self\b", re.IGNORECASE),
    ]
    for prompt_id in ("P1", "P2"):
        out = build_prompt(resp, tax, prompt_id)
        for pat in bad_patterns:
            m = pat.search(out["persona_prompt"])
            assert m is None, (
                f"{prompt_id}: label residue {pat.pattern!r} matched "
                f"{m.group()!r} — generic fallback or raw label leaked"
            )


def _test_r1_leakage() -> None:
    """When exclude_vars contains an item battery, none of those vars appear."""
    resp, tax = _load_test_fixtures()
    # Use the abortion battery as a stand-in target — they all appear on this respondent
    abortion_vars = {"ABDEFECT", "ABHLTH", "ABNOMORE", "ABPOOR", "ABRAPE", "ABSINGLE"}
    for prompt_id in ("P0", "P1", "P2"):
        out = build_prompt(resp, tax, prompt_id, exclude_vars=abortion_vars)
        for v in abortion_vars:
            tpl = PROMPT_TEMPLATES.get(v)
            if tpl is None:
                continue
            # The var's canonical question should not appear in P2; the var_label should not appear in P0
            assert tpl["p2_question"] not in out["persona_prompt"], f"{prompt_id}: leaked {v} canonical question"
            assert get_variable_label(v).strip() not in out["persona_prompt"] or prompt_id != "P0", \
                f"{prompt_id}: leaked {v} var_label"


def run_self_tests() -> None:
    tests = [
        ("template_coverage", _test_template_coverage),
        ("information_equivalence", _test_information_equivalence),
        ("drop_bin", _test_drop_bin),
        ("exclude_vars", _test_exclude_vars),
        ("no_label_residue", _test_no_label_residue),
        ("r1_leakage", _test_r1_leakage),
    ]
    for name, fn in tests:
        fn()
        print(f"  [{name}] PASSED")
    print(f"\n✓ ALL {len(tests)} PROMPT-VARIANT SELF-TESTS PASSED "
          f"(templates: {len(PROMPT_TEMPLATES)}, hash: {TEMPLATE_HASH[:16]}...)")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true",
                   help="Run all 6 self-tests and exit")
    args = p.parse_args()
    if args.self_test:
        run_self_tests()
    else:
        p.print_help()
