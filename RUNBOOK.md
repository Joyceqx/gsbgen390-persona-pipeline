# GSBGEN390 Phase 1 — Paid-Run Runbook

**Locked 2026-05-10 night** per Audit-fresh-4 review (TL;DR table added per
Audit-fresh-5 my-review item 8). This is the canonical step-by-step sequence
for the OSF-locked paid Phase 1 run. Total budget **~$756** (Option A:
cheap-panel primary-only; sensitivity_eval anchor-only).

> **Before any step below**: confirm OSF v1 (`osf_preregistration_v1.md`) is
> filed and the design lock matches `gss_phase1_design.md`. The paid runs
> consume the OSF lock as their pre-registration; running before lock is a
> deviation that requires an amendment.

## TL;DR — six-row paid-run summary

| # | Step | Command | Cost | Wall-clock | Output |
|---|---|---|---|---|---|
| 1 | Smoke | `python3 gss_driver.py --smoke` | ~$0.10 | 1-2 min | `outputs/gss_phase1_records_n1_*.json` (~5 records) |
| 2a | Phase 1a cheap | `python3 gss_driver.py --phase1a` | ~$17 | 6-10 hr | `outputs/gss_phase1_records_n200_*.json` (~4,000 records) |
| 2b | GPT-4o anchor | `python3 gss_driver.py --phase1b-anchor` | ~$148 | 2-4 hr | `outputs/gss_phase1_records_n100_gpt-4o_seed42.json` (~600 records) |
| 3 | §12.2 selector | `python3 select_phase1b_model.py outputs/gss_phase1_records_n200_*.json` | $0 | <1 min | stdout: selected slug + `validation_mae` |
| 4 | Phase 1b cheap | `python3 gss_driver.py --phase1b --phase1b-model SLUG` | ~$71 | 2-12 days | `outputs/gss_phase1_records_n3309_*.json` (~16,545 records) |
| 5 | Headline analysis | (CLI wrapper pending; see Step 5 details) | $0 | ~5 min | `outputs/gss_phase1_headline.{csv,json}` |
| 6 | Phase 1c (DEFERRED) | (orchestration not yet implemented) | ~$519 | post-1b | `outputs/gss_phase1c_*` |

---

## Pre-flight (one-time, free)

```bash
cd /Users/joyce/Documents/GSBGEN390

# 0.1 — confirm no stray partial outputs at canonical paths
ls outputs/gss_phase1_records*.json
# Expected: "no matches found"
# If files exist: review + delete or pass --force-resume-partial deliberately.

# 0.2 — confirm no stale background driver processes (paid spend hazard)
ps aux | grep -E "gss_driver|phase1" | grep -v grep
# Expected: empty output

# 0.3 — confirm OpenRouter API key
test -s OpenRouter_api.txt || echo "MISSING: put key in OpenRouter_api.txt"

# 0.4 — confirm GPT-4o key for anchor
test -s Openai_api.txt || echo "MISSING: put key in Openai_api.txt"

# 0.5 — pre-flight all self-tests
python3 battery_loo.py --self-test
python3 shapley_decomposition.py --self-test
python3 select_phase1b_model.py --self-test
python3 lint_writeup_language.py --self-test
python3 gss_pipeline.py --test-aggregation
python3 gss_pipeline.py --test-multimodel
python3 validate_taxonomy.py
python3 lint_writeup_language.py
# Expected: all "✓ ALL ... PASSED"
```

---

## Step 1 — Smoke (~$1, minutes-to-tens-of-minutes)

Verify API plumbing on cheap × primary only. **Per §9f rule: SMOKE IS
FOR PLUMBING ONLY — do NOT open the JSON and read codes.** If smoke output
informs a design tweak, that's a silent pre-registration violation.

```bash
# Minimal — 1 respondent × 1 model × primary, ~1-2 minutes:
python3 gss_driver.py --smoke

# Slightly larger plumbing check — N=10 × 4 cheap × primary, ~10-30 minutes:
python3 gss_driver.py --n 10 --primary-only
```

Expected output:
- `--smoke`: `outputs/gss_phase1_records_n1_qwen-2.5_seed42.json`, ~5 records
  (1 respondent × 1 model × 5 conditions)
- `--n 10 --primary-only`: `outputs/gss_phase1_records_n10_<panel>_seed42.json`,
  ~200 records (10 × 4 × 5)
- `parse_failure_rate` < 30% on default cheap models (else investigate
  prompt template / parser before proceeding)

---

## Step 2 — Phase 1a (~$17 cheap + ~$148 anchor = ~$165, ~6-10 hours)

Cheap panel × N=200 primary-only AND GPT-4o anchor × N=100 (the selection
half) primary + sensitivity. Anchor produces the Park-comparable Table 3 input.

```bash
# 2a. Cheap-panel Phase 1a (sequential; ~6 hr at ~5 min/respondent)
python3 gss_driver.py --phase1a

# 2b. GPT-4o anchor — runs once, serves both Phase 1a + Phase 1b reporting
python3 gss_driver.py --phase1b-anchor
```

Expected outputs:
- `outputs/gss_phase1_records_n200_qwen-2.5-deepseek-llama-3.-kimi-k2_seed42.json`
  (~4,000 records: 200 respondents × 4 models × 5 conditions)
- `outputs/gss_phase1_records_n100_gpt-4o_seed42.json`
  (~600 records: 100 respondents × 1 model × 6 condition-records — 5
  primary [Full + 4 LOO] + 1 sensitivity-pass record per respondent. The
  sensitivity-pass record carries 118 per-item scored entries inside its
  `per_item_scores` dict; n_samples=2 multiplies the SAMPLE list inside
  each scored entry, not the record count.)

**Cost guard**: if you accidentally try `python3 gss_driver.py --n 3309`
(panel-wide × full sample), the F9 cost guard refuses with a clear cost
projection (~$839 vs the locked ~$71 single-model 1b). Use the named modes.

---

## Step 3 — §12.2 model selection (free, ~30s)

```bash
python3 select_phase1b_model.py outputs/gss_phase1_records_n200_*.json
```

Expected output (one of):
- `argmin_mae` rationale + a model slug + a `validation_mae` on the held-
  out N=100 (post-selection-inference defense)
- `tie_break_cost` — quality tied within 5%, cheaper model wins
- `fallback_qwen_tie` — quality + cost both tied, named Qwen fallback fires
- `all_dq_fail_pause_for_review` — **STOP** and diagnose; do NOT proceed to
  Phase 1b. The CLI prints `selected: None` + a remediation note.

Record the selected slug: it is the input to Step 4.

**Anti-overfit reporting**: the CLI also prints `validation_mae` on the
held-out N=100. This number must appear alongside the Phase 1b headline in
the abstract / writeup per §12.2 anti-post-selection-inference rule.

---

## Step 4 — Phase 1b (~$71, ~2–12 days wall-clock at sequential rate; budget for ~5 days)

Single §12.2-selected model × N=3,309 (full GSS 2024 cross-section) ×
primary_eval only (60 prompts/respondent).

```bash
python3 gss_driver.py --phase1b --phase1b-model <slug-from-step-3>
```

Expected output:
- `outputs/gss_phase1_records_n3309_<model_tag>_seed42.json`
- ~16,545 records (3309 × 5 conditions × 1 model)

**Resume policy**: if the run is interrupted, simply re-invoke the same
command. The driver's per-respondent atomic-write resume picks up where it
left off. Sensitivity_eval is NOT in this run by design (anchor-only per
OSF §3.2).

---

## Step 5 — Phase 1b headline analysis (free, ~5 min)

> ⚠️ **Implementation gap (locked 2026-05-10 night per Audit-fresh-5)**:
> the production-headline CLI is **not yet wired**. `gss_pipeline.py` exposes
> `compute_phase1_headline()` (locked + tested via `--test-aggregation` self-
> test on synthetic 3-respondent fixture), but there is no `--phase1-headline
> outputs/<records>.json --out outputs/gss_phase1_headline.csv` entry point.
> Before invoking Step 5 on real Phase 1b records, ~30 min of CLI-wrapper
> work is required: a thin `compute_phase1_headline_cli.py` that loads the
> records JSON, calls `compute_phase1_headline()`, and serializes to CSV +
> JSON. Tracked as a non-paid prep item; see "Pending tooling" at end of
> this file.

For now, run the self-test to confirm the aggregation logic is intact:

```bash
python3 gss_pipeline.py --test-aggregation       # synthetic-fixture self-test
python3 gss_pipeline.py --test-multimodel        # multi-model aggregation test
```

Then (once the wrapper exists, OR via an inline Python invocation):

```python
# Pending: replace with `python3 compute_phase1_headline_cli.py outputs/<records>.json`
import json
from gss_pipeline import compute_phase1_headline
records = json.load(open("outputs/gss_phase1_records_n3309_<model>_seed42.json"))
headline = compute_phase1_headline(records)  # B=10000 BCa default per §10
json.dump(headline, open("outputs/gss_phase1_headline.json", "w"), indent=2)
```

Expected output (once wrapper is built):
- `outputs/gss_phase1_headline.csv` — per-condition × per-metric × bootstrap
  CIs (B=10000 BCa, paired-respondent-level, seed=42)
- `outputs/gss_phase1_headline.json` — same data structured for the dashboard
- 4-bin LOO ΔMAE per bin with Holm-Bonferroni significance
- Practical-effect-size labels (small / modest / substantive) per §8.9

---

## Step 6 — Phase 1c Battery LOO + Shapley (DEFAULT: run as co-primary; orchestration runtime pending)

**Status (corrected 2026-05-10 night)**: Phase 1c is **co-primary by design and the default action after Phase 1b** — NOT contingent on which bin dominates the 4-bin LOO. The Battery LOO answers "within each pre-registered bin, which specific construct-level batteries drive the predictive signal?" — this question is scientifically valuable whether attitudinal, demographic, behavioral, or psychological wins the 4-bin contest, because Phase 1b alone reports only the broad bin-level effect; Phase 1c is the mechanistic complement at battery level.

**When you CAN legitimately skip / scale back Phase 1c** (not the same as "attitudinal didn't dominate"):
- Phase 1b shows ALL 4 bins are near-zero ΔMAE → the entire Phase 1 design under-detected effects; the issue isn't Phase 1c specifically, it's whether the Phase 1 run had sufficient power / leakage hygiene actually worked. Pause, investigate, possibly re-run Phase 1a smoke before continuing.
- Phase 1b exposes a serious methodological problem (parse failure spike, R1 leakage suspected, model-collapse) → fix the problem first; do not throw $481 at a broken pipeline.
- Budget pressure that didn't exist at OSF lock time → use one of the reduction options (Battery LOO at N=1,500 saves $263; attitudinal-only saves $209; defer to Phase 1d).

**Implementation status (locked 2026-05-10 night)**: at the time this runbook was locked, the Battery LOO + Shapley **orchestration drivers** in `gss_driver.py` are NOT-IMPLEMENTED stubs (they print an OSF §13.2 pointer and exit). The **analyzers** (`battery_loo.py`, `shapley_decomposition.py`) ARE implemented and self-tested. The orchestration is deliberately deferred until Phase 1b results are in — not because Phase 1c is contingent on a specific bin winning, but because the ~1 day of driver work is wasted effort if Phase 1b reveals a methodological problem that needs fixing first.

Before invoking Step 6, the orchestration runtime must be implemented to
match `tier1_tool_schemas.md` Tools 1-2. Estimated implementation work:
~1 day. Then:

```bash
# 6a. Battery LOO orchestration (NOT YET RUNNABLE):
python3 gss_driver.py --battery-loo --phase1b-model <slug>
# Expected cost: ~$481 (34 batteries × 12 items × 3,309 respondents × cheap)
# Expected output: outputs/gss_phase1c_battery_loo_<...>.json

# 6b. Shapley 16-condition extension on Phase 1a panel (NOT YET RUNNABLE):
python3 gss_driver.py --shapley
# Expected cost: ~$38 incremental (11 multi-bin LOO × 12 items × N=200 × 4 cheap)

# 6c. Battery LOO analysis (analyzer already exists; uses --input flag):
python3 battery_loo.py --input outputs/gss_phase1c_battery_loo_<...>.json \
                      --battery-map gss_battery_map.json \
                      --output outputs/gss_phase1c_battery_loo_results.json

# 6d. Shapley analysis (uses --input flag):
python3 shapley_decomposition.py --input outputs/gss_phase1c_shapley_<...>.json \
                                  --output outputs/gss_phase1c_shapley_results.json
```

---

## Total cost projection (Option A locked 2026-05-10)

| Step | Cost | Cumulative |
|---|---|---|
| 1 Smoke | ~$1 | $1 |
| 2a Phase 1a cheap | ~$17 | $18 |
| 2b GPT-4o anchor (1a + 1b reporting; one run) | ~$148 | $166 |
| 3 §12.2 selector | $0 | $166 |
| 4 Phase 1b cheap (single selected model) | ~$71 | $237 |
| 5 Headline analysis | $0 | $237 |
| 6a Battery LOO orchestration (DEFERRED) | ~$481 | $718 |
| 6b Shapley orchestration (DEFERRED) | ~$38 | $756 |
| **Total Phase 1** | | **~$756** |

---

## Common pitfalls (lessons from Audit-fresh-3/4)

1. **Don't run `--n 3309` manually**: the F9 cost guard refuses (would burn
   ~$839 vs $71 single-model). Use `--phase1b --phase1b-model SLUG`.
2. **Don't background paid invocations**: the Audit-fresh-3 review caught
   4 zombie driver processes spending API tokens because of an earlier
   `run_in_background:true` invocation. Always run paid commands in the
   foreground.
3. **Don't trust pre-existing files at canonical paths**: the partial-
   resume guard (Audit-fresh-4 P1) refuses to resume from suspiciously-small
   files. If you see the guard fire, investigate the file before bypassing.
4. **Don't open smoke JSON to read codes**: §9f locked rule. Smoke is
   plumbing-only; otherwise the run is silent pre-registration violation.
5. **Don't mix Option A vs older sensitivity-scope notes from
   PROJECT_SYNTHESIS / STATUS / handoff docs**: the canonical sources are
   `gss_phase1_design.md` (live) + `osf_preregistration_v1.md` (OSF). The
   other docs have superseded banners but the bodies still contain pre-
   2026-05-10 numbers.

---

## Reproducibility checklist (artifacts to preserve)

After each step, the following files must exist + be committed (or hashed
per §0 of OSF v1):

- [ ] `outputs/gss_phase1_records_n200_*.json` (Phase 1a cheap panel)
- [ ] `outputs/gss_phase1_records_n100_gpt-4o_seed42.json` (anchor)
- [ ] `outputs/gss_phase1_records_n3309_<model_tag>_seed42.json` (Phase 1b)
- [ ] `outputs/gss_phase1_headline.csv` (analysis)
- [ ] (post-Phase-1c, deferred): Battery LOO + Shapley records + analyses

All output filenames encode `seed42` per the I-10 reproducibility guard;
non-canonical seed runs require explicit `--force-non-canonical-seed` and
a logged amendment.

---

## Pending tooling (must finish before paid Phase 1b headline analysis)

Tracked from Audit-fresh-5 review (locked 2026-05-10 night):

- [ ] **Headline CLI wrapper** (~30 min): a thin script
  `compute_phase1_headline_cli.py` that loads a records JSON, calls
  `gss_pipeline.compute_phase1_headline(records)`, serializes the result
  to both `outputs/gss_phase1_headline.csv` (long-format per-condition ×
  per-metric × CI table for the paper) and `outputs/gss_phase1_headline.json`
  (nested-dict for the dashboard). Currently, the headline computation
  is reachable only by inline Python (Step 5 above).

- [ ] **Battery LOO orchestration driver** (~1 day): extend `gss_driver.py`
  to support a real `--battery-loo` mode that emits
  `condition="battery_loo_drop_<name>"` records matching
  `tier1_tool_schemas.md` Tool 2 v0.4. Currently a NOT-IMPLEMENTED stub
  (per OSF §13.2 disclosure).

- [ ] **Shapley orchestration driver** (~0.5 day): extend `gss_driver.py`
  with a `--shapley` mode emitting `condition="shapley_<subset>"` records
  for the 16-condition enumeration on the Phase 1a panel. Currently a
  NOT-IMPLEMENTED stub.

- [ ] **(Optional) Headline CLI tests**: round-trip a synthetic records
  JSON through the wrapper and assert the CSV + JSON outputs match
  expected aggregations.
