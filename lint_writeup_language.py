"""§11.1 forbidden-language linter (locked 2026-05-09 night per Audit-3 M-new-7).

Scans Phase 1 writeup-bearing files for the forbidden phrases pre-registered in
`gss_phase1_design.md` §11.1, plus the §1.0 forbidden-language list. Exits with
a non-zero status (and a per-file violation report) if any forbidden phrase
appears in a non-quoted, non-design-doc context.

USAGE
    python3 lint_writeup_language.py                # scan default file set
    python3 lint_writeup_language.py path1 path2    # explicit files
    python3 lint_writeup_language.py --self-test    # synthetic positives + negatives

Locked rules:
- The design doc itself, OSF preregistration, the linter, and audit reports
  are EXEMPT — they discuss the forbidden phrases by name. Only writeup-bearing
  files (abstract, WRITEUP.md, README, dashboard JSON, etc.) are gated.
- A line that immediately negates a forbidden phrase ("we do NOT compute X",
  "X is forbidden", "❌ X") is allowed — the forbidden-form table itself uses
  this construction.

EXIT CODES
- 0  no violations
- 1  one or more violations
- 2  invocation error (missing files etc.)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parent

# Forbidden phrases: literal substrings to flag. Each entry is (canonical-id,
# pattern, why). Patterns are case-insensitive, matched on the raw line.
FORBIDDEN: list[tuple[str, str, str]] = [
    ("F1_normalized_park_fidelity",
     r"normalized\s+park[-\s]+style\s+fidelity",
     "We report raw metrics; no test-retest denominator. §1.0 / §11.1."),
    ("F2_causal_feature_importance",
     r"causal\s+feature\s+importance",
     "LOO + Battery LOO estimate predictive dependence under a fixed prompt-construction "
     "procedure, NOT causal effects. §1.0 / §11.1."),
    ("F3_general_human_simulation",
     r"general\s+human[-\s]+simulation\s+ability",
     "Single-wave attitude prediction does not generalize to BFI/games/long-term. §1.0."),
    ("F4_robust_across_LLM_families_unqualified",
     r"robust(ly)?\s+across\s+LLM\s+families",
     "Restricted to the N=200 panel comparison; does NOT apply to the N=3309 headline. §11.1."),
    ("F5_LLM_persona_reasoning",
     r"LLM\s+persona\s+reasoning",
     "Requires the §9c.4 R2-comparator caveat in scope to be defensible. §1.0."),
    ("F6_matches_park_82pct",
     r"matches?\s+park\W*s?\s+82%",
     "We do NOT compute Park-style normalized accuracy. §11.1."),
    ("F7_persona_fidelity_bare",
     r"\bpersona\s+fidelity\b",
     "Use 'within-wave attitudinal prediction' or 'single-wave GSS attitudes'. §11.1."),
    ("F8_attitudinal_dominance_unqualified",
     # Catches abstract-level claims; MUST be paired with R1+R2 caveat or auto-corr disclosure.
     # Pattern revised 2026-05-10 per Audit-fresh-2 F3a: was previously noun-only
     # (attitudinal dominance), missing the verb form (attitudinal features dominate)
     # which is the bare claim §1.0/§11 actually warn against.
     r"attitudinal\s+(features\s+)?(dominance|dominate(s)?)",
     "Bare claim is vulnerable to the auto-correlation tautology (M-new-1). "
     "Pair with R1 + R2 + outcome-stratification caveat. §1.0 / §11."),
    ("F9_attitudinal_features_dominate_humans",
     r"attitudinal\s+features\s+dominate\s+human[-\s]+simulation",
     "Phase 1 cannot make this claim — it's GSS-attitude-prediction-internal. §11."),
    ("F10_normalized_accuracy",
     r"normalized\s+accuracy",
     "We do NOT compute Park's normalized accuracy. §11.1."),
    ("F11_LLM_internal_state",
     # OSF §12 row 7 ("LLM internal-state claim") — added 2026-05-10 per Audit-fresh-2
     # F3b: OSF added this as the most aggressive new constraint but had zero linter
     # enforcement until this row. Matches LLM/model/persona as the agent.
     r"(LLM|model|persona)\s+(understands|internalized|internalizes|uses\s+the\s+schema)",
     "LLM/model internal-state claims are forbidden — the project measures predictive "
     "dependence, NOT internal representation. OSF §12 row 7 / §1.0."),
]

# Pre-compile patterns at import time (Audit-fresh-5 my-review item 9).
# Tiny perf win at current scan size; matters when paper-writing scans larger
# trees of dashboard markdown / abstract drafts.
_FORBIDDEN_COMPILED: list[tuple[str, "re.Pattern[str]", str]] = [
    (rule_id, re.compile(pat, flags=re.IGNORECASE), why)
    for rule_id, pat, why in FORBIDDEN
]

# Lines starting with these markers indicate the phrase is being NEGATED
# (we deliberately list it as forbidden), so don't flag.
NEGATION_MARKERS = (
    "❌",
    "forbidden",
    "do not",
    "does not",
    "we don't",
    "we do not",
    "must not",
    "avoid",
    "never",
    "f1_",  # rule IDs in this file
    "f2_", "f3_", "f4_", "f5_", "f6_", "f7_", "f8_", "f9_", "f10_",
)

# Files exempt from the linter — they discuss forbidden phrases by design.
EXEMPT_NAMES = {
    "lint_writeup_language.py",
    "gss_phase1_design.md",
    "osf_preregistration_v1.md",
    "tier1_tool_schemas.md",
    "theory_interpretation_guide.md",
    "theory_review_round2.md",
    "LIT_REVIEW.md",
    "PROJECT_SYNTHESIS.md",
    "STATUS.md",
    "HANDOFF.md",
    "MEETING_HANDOUT.md",
    "WRITEUP.md",   # NOTE: WRITEUP.md is the pilot writeup; a future paper-WRITEUP.md
                    # for Phase 1 should NOT be exempt — rename to phase1_writeup.md
                    # and remove from this list.
    "FUTURE_DESIGN.md",
    "thesis_phase2_design.md",
    "replication_scoping.md",
    "GSBGEN390_audit_summary.md",
    "CLAUDE_PROJECT_IMPROVEMENT_PROMPT.md",
    "CLAUDE.md",
}

# Default scan target — files that DO bear writeup-style claims and must be gated.
DEFAULT_SCAN_TARGETS = [
    "README.md",
    "docs/",                             # GitHub Pages content (any markdown)
    "phase1_writeup.md",                 # future
    "phase1_abstract.md",                # future
    "phase1_dashboard.json",             # future
    "outputs/build_site_data.json",      # dashboard data file (if present)
]


def _iter_lines(path: Path):
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for ln, line in enumerate(f, start=1):
                yield ln, line.rstrip("\n")
    except OSError as e:
        print(f"[lint] cannot read {path}: {e}", file=sys.stderr)


def _is_negated(line: str) -> bool:
    """Heuristic: line is part of a forbidden-form table or explicit negation."""
    low = line.lstrip().lower()
    return any(low.startswith(m) for m in NEGATION_MARKERS) or "forbidden form" in low


def lint_file(path: Path) -> list[tuple[int, str, str, str]]:
    """Return list of (line_number, rule_id, line_text, why) violations."""
    if not path.exists() or not path.is_file():
        return []
    if path.name in EXEMPT_NAMES:
        return []
    hits: list[tuple[int, str, str, str]] = []
    for ln, line in _iter_lines(path):
        if _is_negated(line):
            continue
        for rule_id, pat, why in _FORBIDDEN_COMPILED:
            if pat.search(line):
                hits.append((ln, rule_id, line.strip(), why))
    return hits


def _resolve_targets(args_paths: list[str]) -> list[Path]:
    if args_paths:
        out = []
        for p in args_paths:
            pp = Path(p)
            if not pp.is_absolute():
                pp = WORK / pp
            if pp.is_dir():
                out.extend(sorted(pp.rglob("*.md")))
                out.extend(sorted(pp.rglob("*.json")))
            else:
                out.append(pp)
        return out
    out = []
    for p in DEFAULT_SCAN_TARGETS:
        pp = WORK / p
        if pp.is_dir():
            out.extend(sorted(pp.rglob("*.md")))
            out.extend(sorted(pp.rglob("*.json")))
        elif pp.exists():
            out.append(pp)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="§11.1 forbidden-language linter for Phase 1 writeup files.",
    )
    ap.add_argument("paths", nargs="*", help="files/dirs to scan (default: writeup targets)")
    ap.add_argument("--self-test", action="store_true",
                    help="run synthetic positive/negative tests")
    ns = ap.parse_args(argv)

    if ns.self_test:
        return _self_test()

    targets = _resolve_targets(ns.paths)
    if not targets:
        print("[lint] no files to scan (run from project root, or pass paths).",
              file=sys.stderr)
        return 0

    total_hits = 0
    by_file: dict[Path, list[tuple[int, str, str, str]]] = {}
    for t in targets:
        hits = lint_file(t)
        if hits:
            by_file[t] = hits
            total_hits += len(hits)

    if not total_hits:
        print(f"✓ §11.1 lint: 0 violations across {len(targets)} files")
        return 0

    print(f"✗ §11.1 lint: {total_hits} violations across {len(by_file)} file(s)\n")
    for path, hits in by_file.items():
        rel = path.relative_to(WORK) if WORK in path.parents or path == WORK else path
        print(f"  {rel}")
        for ln, rule_id, text, why in hits:
            print(f"    L{ln:>5}  [{rule_id}]  {text[:100]}")
            print(f"             why: {why}")
        print()
    return 1


def _self_test() -> int:
    """Synthetic positive + negative + negation cases.

    Refactored 2026-05-10 night per Audit-fresh-5 my-review item 6: tests
    now route through `lint_file()` on a tmp file, so any regression in
    lint_file's exempt-path / negation-handling logic is caught (previously
    the test re-implemented the regex match loop, duplicating logic).
    """
    import tempfile
    print("=== §11.1 lint self-test ===\n")
    # Positives: each forbidden phrase, plain context (must be flagged)
    positives = [
        "Our LLM persona reasoning matches the GSS data closely.",
        "We report normalized accuracy on the 12 primary_eval items.",
        "Robust across LLM families with no caveats.",
        "This is a measure of causal feature importance.",
        "Persona fidelity is high in our results.",
        "Our findings show attitudinal features dominate human-simulation.",
        # Audit-fresh-2 F3a additions — verb form
        "In our N=3309 headline, attitudinal features dominate the prediction.",
        "Attitudinal dominates over demographic features.",
        # Audit-fresh-2 F3b additions — LLM internal-state claims
        "The LLM understands the cognitive schema of moral foundations.",
        "The LLM internalized respondent preferences across batteries.",
        "The model uses the schema of self-transcendence values.",
    ]
    # Negatives: same phrases in negation / forbidden-form context (must NOT flag)
    negatives = [
        "❌ 'normalized Park-style fidelity' (we report raw metrics)",
        "We do NOT compute normalized accuracy.",
        "Forbidden form: 'robust across LLM families'.",
        "Avoid the bare claim 'attitudinal features dominate'.",
        "❌ 'the LLM understands X' is a forbidden internal-state claim.",
    ]

    def _scan_via_lint_file(lines: list[str]) -> int:
        """Round-trip the lines through a tmp .md file via lint_file().
        Returns count of UNIQUE lines flagged (one line can match multiple
        forbidden patterns and produce multiple hits — for the assertion
        below we want lines-flagged, not total-hits)."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="_lint_test.md", delete=False, encoding="utf-8"
        ) as f:
            f.write("\n".join(lines) + "\n")
            tmp_path = Path(f.name)
        try:
            hits = lint_file(tmp_path)
            return len({h[0] for h in hits})  # unique line numbers
        finally:
            tmp_path.unlink(missing_ok=True)

    n_pos_lines_hit = _scan_via_lint_file(positives)
    n_neg_lines_hit = _scan_via_lint_file(negatives)

    # [3] Exempt-name test: lint_file() should return [] on an exempt-named
    # file even if the content is full of violations. We need an exact-name
    # match (lint_file checks `path.name in EXEMPT_NAMES`), so build a tmp
    # directory and write the test file as STATUS.md inside it.
    with tempfile.TemporaryDirectory() as tmpdir:
        exempt_path = Path(tmpdir) / "STATUS.md"
        exempt_path.write_text("\n".join(positives) + "\n")
        n_exempt_hits = len(lint_file(exempt_path))

    # [4] JSON file test (Audit-fresh-5 my-review item 10): the linter scans
    # JSON dashboard files too; verify forbidden phrases inside JSON string
    # values are still flagged.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        f.write('{\n  "abstract_v1": "We report normalized accuracy on '
                'primary_eval items.",\n  "tagline": "robust across LLM families"\n}\n')
        json_tmp = Path(f.name)
    try:
        n_json_hits = len({h[0] for h in lint_file(json_tmp)})
    finally:
        json_tmp.unlink(missing_ok=True)

    # [5] Directory-recursion test: _resolve_targets should pull both .md
    # and .json files from a passed directory recursively.
    with tempfile.TemporaryDirectory() as tmpdir:
        sub = Path(tmpdir) / "subdir"
        sub.mkdir()
        (Path(tmpdir) / "top.md").write_text("Robust across LLM families.\n")
        (sub / "nested.json").write_text(
            '{"x": "we report normalized accuracy"}\n'
        )
        targets = _resolve_targets([str(tmpdir)])
        # Should resolve at least 2 files (top.md + nested.json)
        n_targets = len(targets)
        n_dir_hits = sum(len(lint_file(t)) for t in targets)

    expected_pos = len(positives)
    expected_neg = 0
    print(f"[1] positives lines flagged via lint_file(): "
          f"{n_pos_lines_hit}/{expected_pos} (expected {expected_pos})")
    print(f"[2] negatives lines flagged via lint_file(): "
          f"{n_neg_lines_hit}/{len(negatives)} (expected {expected_neg})")
    print(f"[3] exempt-name file (STATUS.md) flagged: "
          f"{n_exempt_hits} hits across positives (expected 0 — file is exempt)")
    print(f"[4] JSON file flagged: {n_json_hits} unique lines "
          f"(expected ≥ 2 — both forbidden phrases live on different lines)")
    print(f"[5] directory recursion: {n_targets} files resolved, "
          f"{n_dir_hits} total hits (expected ≥ 2 files, ≥ 2 hits)")

    ok = (
        n_pos_lines_hit == expected_pos
        and n_neg_lines_hit == expected_neg
        and n_exempt_hits == 0
        and n_json_hits >= 2
        and n_targets >= 2
        and n_dir_hits >= 2
    )
    if ok:
        print("\n✓ §11.1 LINT SELF-TEST PASSED")
        return 0
    print("\n✗ SELF-TEST FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
