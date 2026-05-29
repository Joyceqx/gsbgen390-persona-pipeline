"""Preflight checks before paid Phase 1A.

Single-point self-tests in `src/prompt_variants.py --self-test` run on one
respondent and are sufficient for CI hygiene. This file runs the heavier
N=200 × 12 batteries × 3 prompts coverage that should pass before any paid
Phase 1A LLM calls.

Checks:
  1. Coverage. Every panel respondent produces a non-empty feature list under
     all 3 prompts in the Full + 4 single-bin LOO conditions.
  2. Information equivalence (panel-wide). For every respondent and every
     condition, the set of features rendered into P0 == P1 == P2.
  3. R1 leakage hygiene. For every (panel respondent, primary_eval item, prompt
     variant) the rendered persona prompt does NOT mention the eval item's
     own var or any battery-sibling var (per `battery_excludes_for_item`).
  4. Metadata round-trip. Every rendered prompt's metadata carries the
     correct prompt_id, prompt_version, template_hash, feature_count,
     drop_bin, and bin_counts.
  5. No stray formatting artifacts in P1/P2 (ALL CAPS, "(SPECIFY)", unfilled
     `{val}` placeholders, "rs family", etc.).

Run:
    python3 tests/preflight_phase1a.py

Exit code 0 = all checks passed, ready to spend money on Phase 1A. Non-zero
exit = stop and fix before launching the paid run.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

WORK = Path("/Users/joyce/Developer/gsbgen390")
sys.path.insert(0, str(WORK / "src"))

from gss_pipeline import (
    battery_excludes_for_item,
    load_battery_map,
    load_taxonomy,
    sample_respondents,
)
from prompt_variants import (
    BIN_HEADERS,
    PROMPT_TEMPLATES,
    PROMPT_VERSION,
    TEMPLATE_HASH,
    build_prompt,
)

PANEL_N = 200
PANEL_SEED = 42
PROMPTS = ("P0", "P1", "P2")
LOO_BINS = (None, "demographic", "behavioral", "psychological", "attitudinal")


def _header_token_whitelist() -> set[str]:
    """ALL-CAPS tokens that legitimately appear in section headers; ignore them
    when scanning P1/P2 bodies for raw GSS var_label residue."""
    toks: set[str] = {"USA", "NYC", "GDP", "NATO", "SI", "FAQ"}
    for prompt_headers in BIN_HEADERS.values():
        for _, hdr in prompt_headers:
            toks.update(re.findall(r"\b[A-Z]{4,}\b", hdr))
    return toks


def check_coverage(panel, taxonomy) -> list[str]:
    errs = []
    for rid, resp in panel.iterrows():
        for pid in PROMPTS:
            for drop in LOO_BINS:
                out = build_prompt(resp, taxonomy, prompt_id=pid, drop_bin=drop)
                meta = out["metadata"]
                if meta["feature_count"] < 1:
                    errs.append(
                        f"empty feature list: rid={rid} prompt={pid} drop_bin={drop}"
                    )
    return errs


def check_information_equivalence(panel, taxonomy) -> list[str]:
    errs = []
    for rid, resp in panel.iterrows():
        for drop in LOO_BINS:
            counts = {}
            bin_signatures = {}
            for pid in PROMPTS:
                out = build_prompt(resp, taxonomy, prompt_id=pid, drop_bin=drop)
                counts[pid] = out["metadata"]["feature_count"]
                bin_signatures[pid] = tuple(
                    sorted(out["metadata"]["bin_counts"].items())
                )
            if len(set(counts.values())) > 1:
                errs.append(
                    f"feature_count mismatch: rid={rid} drop_bin={drop} counts={counts}"
                )
            if len(set(bin_signatures.values())) > 1:
                errs.append(
                    f"bin_counts mismatch: rid={rid} drop_bin={drop} sigs={bin_signatures}"
                )
    return errs


def check_r1_leakage(panel, taxonomy) -> list[str]:
    """For each primary_eval item × prompt × respondent, the persona prompt
    must not mention any variable in that item's R1 battery exclusion set
    (the eval item itself plus its battery siblings)."""
    errs = []
    battery_map = load_battery_map()
    primary_items = [it["id"] for it in taxonomy["primary_eval"]["items"]]
    for item_id in primary_items:
        excl = battery_excludes_for_item(item_id, battery_map)
        if not excl:
            continue
        for rid, resp in panel.iterrows():
            for pid in PROMPTS:
                out = build_prompt(
                    resp, taxonomy, prompt_id=pid, exclude_vars=excl
                )
                # Inspect metadata first (cheap, exact)
                meta_excl = set(out["metadata"].get("excluded_vars", []))
                missing = excl - meta_excl
                if missing:
                    errs.append(
                        f"R1: rid={rid} item={item_id} prompt={pid} "
                        f"metadata.excluded_vars missing {sorted(missing)}"
                    )
                # And actual rendered body — any battery-sibling var label?
                body = out["persona_prompt"].lower()
                for v in excl:
                    needle = f" {v.lower()}: "
                    if needle in body:
                        errs.append(
                            f"R1: rid={rid} item={item_id} prompt={pid} "
                            f"leaked var '{v}' into body"
                        )
    return errs


def check_metadata_roundtrip(panel, taxonomy) -> list[str]:
    errs = []
    for rid, resp in panel.iterrows():
        for pid in PROMPTS:
            for drop in LOO_BINS:
                out = build_prompt(resp, taxonomy, prompt_id=pid, drop_bin=drop)
                meta = out["metadata"]
                if meta["prompt_id"] != pid:
                    errs.append(f"meta.prompt_id mismatch rid={rid} got={meta['prompt_id']}")
                if meta["prompt_version"] != PROMPT_VERSION:
                    errs.append(
                        f"meta.prompt_version mismatch rid={rid} "
                        f"got={meta['prompt_version']} expected={PROMPT_VERSION}"
                    )
                if not TEMPLATE_HASH.startswith(meta["template_hash"]):
                    errs.append(
                        f"meta.template_hash drift rid={rid} "
                        f"got={meta['template_hash']} expected_prefix_of={TEMPLATE_HASH[:16]}"
                    )
                if meta.get("drop_bin") != drop:
                    errs.append(
                        f"meta.drop_bin mismatch rid={rid} got={meta.get('drop_bin')} expected={drop}"
                    )
    return errs


def check_format_artifacts(panel, taxonomy) -> list[str]:
    """Scan P1/P2 bodies for known formatting glitches across full panel."""
    errs = []
    header_tokens = _header_token_whitelist()
    for rid, resp in panel.iterrows():
        for pid in ("P1", "P2"):
            body = build_prompt(resp, taxonomy, prompt_id=pid)["persona_prompt"]
            # Stray ALL-CAPS tokens (not section headers, not acronyms)
            for tok in set(re.findall(r"\b[A-Z]{4,}\b", body)):
                if tok in header_tokens:
                    continue
                errs.append(f"format ALL-CAPS: rid={rid} prompt={pid} token={tok}")
            # Unfilled placeholders
            if re.search(r"\{val[^}]*\}", body):
                errs.append(f"format unfilled placeholder: rid={rid} prompt={pid}")
            # (SPECIFY) leftover
            if "(SPECIFY)" in body or "(specify)" in body:
                errs.append(f"format SPECIFY residue: rid={rid} prompt={pid}")
            # GSS codebook 'rs family' / 'r's family' (P0 may have these, P1/P2 must not)
            if re.search(r"\b(rs|r's) (family|spouse|wife|husband)\b", body, re.IGNORECASE):
                errs.append(f"format rs/r's family: rid={rid} prompt={pid}")
    return errs


def main() -> int:
    print(f"Phase 1A preflight — panel N={PANEL_N}, seed={PANEL_SEED}")
    print(f"  templates: {len(PROMPT_TEMPLATES)}  hash: {TEMPLATE_HASH[:16]}  version: {PROMPT_VERSION}")
    taxonomy = load_taxonomy()
    panel = sample_respondents(PANEL_N, seed=PANEL_SEED)
    print(f"  loaded panel: {len(panel)} respondents")
    print()

    checks = [
        ("coverage (5 conditions × 3 prompts)", lambda: check_coverage(panel, taxonomy)),
        ("information_equivalence (panel-wide)", lambda: check_information_equivalence(panel, taxonomy)),
        ("r1_leakage (12 batteries × 3 prompts)", lambda: check_r1_leakage(panel, taxonomy)),
        ("metadata_roundtrip", lambda: check_metadata_roundtrip(panel, taxonomy)),
        ("format_artifacts (P1/P2)", lambda: check_format_artifacts(panel, taxonomy)),
    ]

    total_errs = 0
    for name, fn in checks:
        errs = fn()
        if errs:
            total_errs += len(errs)
            print(f"  [{name}] FAILED ({len(errs)} issues)")
            for e in errs[:5]:
                print(f"    - {e}")
            if len(errs) > 5:
                print(f"    ... and {len(errs) - 5} more")
        else:
            print(f"  [{name}] PASSED")

    print()
    if total_errs:
        print(f"✗ PREFLIGHT FAILED — {total_errs} issues. Fix before paid Phase 1A.")
        return 1
    print("✓ ALL PREFLIGHT CHECKS PASSED — ready for paid Phase 1A.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
