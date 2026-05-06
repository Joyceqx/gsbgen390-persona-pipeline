"""GSS Phase 1 persona pipeline — for each sampled respondent, build persona
prompts under 5 conditions (full + 4 LOO ablations) and predict the 12
primary_eval items. Sensitivity pass over ~118 sensitivity_eval items uses
per-item exclusion.

Locked design: see gss_phase1_design.md (v 2026-05-05) and
gss_feature_taxonomy.json (v 0.2-locked-2026-05-05).

This is a partial scaffold — completed only through AUDIT-A (persona prompt
template). LLM call, scoring, and aggregation come after subsequent audit
sign-offs.

Usage (smoke test mode, no LLM):
    python3 gss_pipeline.py --n 1 --print-prompt
"""
from __future__ import annotations

import argparse
import json
import random
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
) -> tuple[str, dict[str, int]]:
    """Build the persona system prompt for one respondent under one condition.

    Args:
        respondent: a row from the loaded GSS DataFrame (one respondent).
        taxonomy: the loaded taxonomy dict.
        drop_bin: name of bin to drop ('demographic'/'behavioral'/'psychological'/
            'attitudinal'), or None for the FULL condition.

    Returns:
        (prompt_text, stats_dict) — stats_dict has per-bin item counts and
        an overall character-length sanity for token budgeting.
    """
    bins = taxonomy["_feature_bins_sets"]
    parts = [PERSONA_PREAMBLE, ""]
    stats: dict[str, int] = {}

    for bin_name, header in BIN_DISPLAY:
        if drop_bin == bin_name:
            stats[bin_name] = 0
            continue
        bin_vars = sorted(bins[bin_name])  # alphabetical, deterministic
        lines = []
        for v in bin_vars:
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
    stats["approx_tokens"] = len(prompt) // 4  # rough token estimate
    return prompt, stats


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
    p = argparse.ArgumentParser(description="GSS Phase 1 persona pipeline (AUDIT-A scaffold)")
    p.add_argument("--n", type=int, default=1, help="number of respondents to sample for inspection")
    p.add_argument("--seed", type=int, default=42, help="random seed for sampling (locked at 42)")
    p.add_argument("--print-prompt", action="store_true", help="run AUDIT-A: print a sample persona prompt")
    p.add_argument("--save", type=Path, default=None, help="optionally save full prompt to a file")
    return p.parse_args()


if __name__ == "__main__":
    args = _cli()
    if args.print_prompt:
        _audit_a_print(n=args.n, seed=args.seed, save_to=args.save)
    else:
        print("Pipeline scaffold loaded. Pass --print-prompt to run AUDIT-A inspection.")
        print(f"Taxonomy: {TAXONOMY_PATH.name}")
        print(f"Loader:   gss_loader.py")
        print(f"Status:   AUDIT-A complete; AUDIT-B (eval question phrasing) is next.")
