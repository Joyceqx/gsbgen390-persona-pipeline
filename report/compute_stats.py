"""Compute every statistic the Phase 1A report needs, from the raw run files.

Sources
-------
  outputs/gss_phase1_records_n200_*_{P0,P1,P2}.json   cheap panel (4 models × 3 prompts × N=200)
  outputs/anchor_r1on_n100.json                       GPT-4o, R1 ON  (Anchor B, our protocol)
  outputs/anchor_r1off_n100.json                      GPT-4o, R1 OFF (Anchor A, Park-exact)
  outputs/primary_eval_human_variance_2024.json       DQ-3 human variance reference

Conventions (locked, RESEARCH_DESIGN.md §7)
  normalized abs-err per sample:
    parse_fail   -> 1.0                       (conservative; penalises evasion)
    ordinal ok   -> |pred-truth| / code_range
    categorical  -> 0 if exact else 1.0
  exact-match (Park's metric) is computed over PARSED samples only (n_ok).
  All cell/marginal MAE numbers are RESPONDENT-MACRO (mean over respondents of
  the per-respondent mean over items) to match the selector.

Outputs report/phase1a_stats.json + prints a cross-check against the §7 selector
and notes/park_comparability.md so the report's numbers are auditable.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pvariance

import numpy as np
from scipy.stats import wilcoxon

ROOT = Path("/Users/joyce/Developer/gsbgen390")
OUT = ROOT / "report" / "phase1a_stats.json"
sys.path.insert(0, str(ROOT / "src"))
from gss_pipeline import format_eval_question, load_taxonomy  # noqa: E402

# ---- item metadata ---------------------------------------------------------
tx = load_taxonomy()
PRIMARY = [it["id"] for it in tx["primary_eval"]["items"]]
CONSTRUCT = {it["id"]: it.get("construct_family", it.get("construct", "")) for it in tx["primary_eval"]["items"]}
META = {}
for it in tx["primary_eval"]["items"]:
    _, m = format_eval_question(it)
    codes = sorted(m["valid_codes"])
    META[it["id"]] = {"K": len(codes), "lo": min(codes), "hi": max(codes),
                      "range": (max(codes) - min(codes)) or 1}

HUMAN_VAR = {k: v["human_variance"]
             for k, v in json.loads((ROOT / "outputs/primary_eval_human_variance_2024.json").read_text())["items"].items()}

MODELS = ["qwen/qwen3-max", "deepseek/deepseek-v3.1-terminus",
          "meta-llama/llama-4-maverick", "moonshotai/kimi-k2-0905"]
SHORT = {"qwen/qwen3-max": "Qwen3-Max", "deepseek/deepseek-v3.1-terminus": "DeepSeek-V3.1",
         "meta-llama/llama-4-maverick": "Llama-4-Mav", "moonshotai/kimi-k2-0905": "Kimi-K2"}
COST = {"qwen/qwen3-max": 9.8e-4, "deepseek/deepseek-v3.1-terminus": 3.2e-4,
        "meta-llama/llama-4-maverick": 1.8e-4, "moonshotai/kimi-k2-0905": 7.2e-4,
        "openai/gpt-4o-2024-08-06": 2.4e-3}
PROMPTS = ["P0", "P1", "P2"]
SCALE_KIND = {it: ("binary" if META[it]["K"] == 2 else "ordinal") for it in PRIMARY}

CHEAP = {p: ROOT / f"outputs/gss_phase1_records_n200_qwen3-ma-deepseek-llama-4--kimi-k2-_seed42_{p}.json"
         for p in PROMPTS}
ANCHOR_ON = ROOT / "outputs/anchor_r1on_n100.json"     # Anchor B
ANCHOR_OFF = ROOT / "outputs/anchor_r1off_n100.json"   # Anchor A

BOOT_B, SEED = 10_000, 42


# ---- unified per-sample scorer ---------------------------------------------
def sample_nae_exact(s, code_range):
    """Return (normalized_abs_err, is_exact_or_None). is_exact is None when the
    sample is a parse_fail (excluded from exact-match denominator)."""
    if s.get("skipped_missing_truth"):
        return None, None
    if s.get("parse_fail"):
        return 1.0, None                      # conservative; not counted in EM denom
    ae, cm = s.get("abs_err"), s.get("cat_match")
    if ae is not None:
        return ae / code_range, 1 if ae == 0 else 0
    if cm is not None:
        return (0.0 if cm == 1 else 1.0), 1 if cm == 1 else 0
    return None, None


def iter_samples(records, item):
    cr = META[item]["range"]
    for r in records:
        for s in r["per_item_scores"].get(item, []):
            yield r["respondent_id"], s, cr


# ---- per (records, item) aggregate -----------------------------------------
def agg_item(records, item):
    cr = META[item]["range"]
    n_total = n_ok = n_exact = n_pf = 0
    nae_all = []
    preds = []
    truths_by_rid = {}
    by_rid_nae = defaultdict(list)
    by_rid_em = defaultdict(list)
    pred_by_rid = defaultdict(list)            # for respondent-level variance (DQ-3)
    for rid, s, _ in iter_samples(records, item):
        if s.get("skipped_missing_truth"):
            continue
        n_total += 1
        nae, ex = sample_nae_exact(s, cr)
        nae_all.append(nae)
        by_rid_nae[rid].append(nae)
        if s.get("parse_fail"):
            n_pf += 1
            by_rid_em[rid].append(0)
            continue
        n_ok += 1
        if ex == 1:
            n_exact += 1
        by_rid_em[rid].append(ex)
        pc = s.get("persona_code")
        if pc is not None:
            preds.append(pc)
            pred_by_rid[rid].append(pc)
        t = s.get("truth")
        if t is not None and rid not in truths_by_rid:
            truths_by_rid[rid] = t
    # respondent-level prediction (mean across n_samples) -> population variance
    rid_pred_mean = [mean(v) for v in pred_by_rid.values() if v]
    model_var = pvariance(rid_pred_mean) if len(rid_pred_mean) >= 2 else 0.0
    hv = HUMAN_VAR.get(item)
    var_ratio = (model_var / hv) if hv else None
    pred_dist = Counter(preds)
    return {
        "n_total": n_total, "n_ok": n_ok, "n_pf": n_pf, "n_exact": n_exact,
        "em": (n_exact / n_ok) if n_ok else None,
        "parse_fail_rate": (n_pf / n_total) if n_total else None,
        "mae_norm_item": mean(nae_all) if nae_all else None,   # sample-level mean
        "per_rid_nae": {k: mean(v) for k, v in by_rid_nae.items()},
        "per_rid_em": {k: mean(v) for k, v in by_rid_em.items() if v},
        "truths": truths_by_rid,
        "distinct_codes": len(pred_dist),
        "top1_share": (max(pred_dist.values()) / sum(pred_dist.values())) if pred_dist else None,
        "var_ratio": var_ratio,
    }


def respondent_macro_mae(per_item_aggs):
    """Mean over respondents of (mean over that respondent's items of normalized
    abs-err). per_item_aggs: list of agg_item dicts. Matches the §7 selector."""
    rid_vals = defaultdict(list)
    for a in per_item_aggs:
        for rid, v in a["per_rid_nae"].items():
            rid_vals[rid].append(v)
    means = [mean(v) for v in rid_vals.values() if v]
    return mean(means) if means else None, means


def boot_ci(values, b=BOOT_B, seed=SEED):
    if not values or len(values) < 2:
        return None, None
    a = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    boots = a[rng.integers(0, len(a), size=(b, len(a)))].mean(axis=1)
    return float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def maj_baseline_mae(records_for_truth):
    """Majority-class baseline normalized MAE (respondent-macro). One truth per
    (item, respondent); predict each item's modal truth."""
    modes = {}
    truths = {}
    for item in PRIMARY:
        a = agg_item(records_for_truth, item)
        truths[item] = a["truths"]
        if a["truths"]:
            modes[item] = Counter(a["truths"].values()).most_common(1)[0][0]
    rid_vals = defaultdict(list)
    for item in PRIMARY:
        cr = META[item]["range"]
        for rid, t in truths[item].items():
            rid_vals[rid].append(abs(t - modes[item]) / cr)
    means = [mean(v) for v in rid_vals.values() if v]
    return mean(means) if means else None, modes


# ============================================================================
# LOAD
# ============================================================================
# Cheap panel: read from the PARQUET (the authoritative §7 selector source) so
# every cheap number matches the selector exactly. The parquet already encodes
# binary items as abs_err 0/1 and resolves the PARTYID "Other"-category edge
# case to ordinal distance; reading the per-prompt JSONs instead would re-open
# that 6/3210-sample edge case and drift ~0.0015 off the selector. The anchor
# (not in the parquet) is read from JSON through the identical scorer.
import pandas as pd  # noqa: E402

PQ = pd.read_parquet(ROOT / "outputs/phase1a_raw.parquet")
PQ = PQ[PQ["condition"] == "Full"]


def _pq_records(sub):
    """Convert parquet rows -> JSON-record shape so agg_item can consume them.
    Each record: {respondent_id, per_item_scores: {item: [sample,...]}}."""
    out = {}
    for row in sub.itertuples(index=False):
        rec = out.setdefault(row.respondent_id, {"respondent_id": row.respondent_id, "per_item_scores": defaultdict(list)})
        rec["per_item_scores"][row.item].append({
            "parse_fail": not bool(row.parse_ok),
            "abs_err": (None if pd.isna(row.abs_err) else int(row.abs_err)),
            "cat_match": None,
            "persona_code": (None if pd.isna(row.pred_code) else int(row.pred_code)),
            "truth": (None if pd.isna(row.true_code) else int(row.true_code)),
            "skipped_missing_truth": False,
        })
    return list(out.values())


# Pre-group cheap records by (model_slug, prompt) and the Random column by prompt.
_CHEAP_CACHE = {}
for model in MODELS:
    for p in PROMPTS:
        _CHEAP_CACHE[(model, p)] = _pq_records(PQ[(PQ.model == model) & (PQ.prompt == p)])
_RANDOM_CACHE = {p: _pq_records(PQ[(PQ.model == "Random") & (PQ.prompt == p)]) for p in PROMPTS}


def model_recs(prompt, model, cohort=None):
    recs = _CHEAP_CACHE[(model, prompt)]
    if cohort is None:
        return recs
    return [r for r in recs if r["respondent_id"] in cohort]


def load(path, cohort=None, cond="full"):
    recs = json.loads(Path(path).read_text())
    return [r for r in recs
            if r.get("condition", "full") == cond and (cohort is None or r["respondent_id"] in cohort)]


# cohort: anchor respondents (first 100 of seed=42). Verified == anchor IDs below.
anchor_on = load(ANCHOR_ON)           # GPT-4o R1 ON  (Anchor B)
anchor_off = load(ANCHOR_OFF)         # GPT-4o R1 OFF (Anchor A)
COHORT_100 = set(r["respondent_id"] for r in anchor_on)
assert COHORT_100.issubset(set(PQ.respondent_id.unique())), "anchor cohort not subset of panel"
assert len(COHORT_100) == 100


# ============================================================================
# STORYLINE 1 — model + prompt selection (N=200 full panel)
# ============================================================================
stats = {"meta": {"n_panel": 200, "n_anchor": 100, "items": PRIMARY,
                  "construct": CONSTRUCT, "scale_kind": SCALE_KIND,
                  "K": {it: META[it]["K"] for it in PRIMARY},
                  "cost_per_call": COST, "short": SHORT}}

# --- 12 real cells + Random×3 : cell-level normalized MAE + CI --------------
cells = {}
per_item_cell = {}   # (model_short, prompt, item) -> agg
for model in MODELS:
    for p in PROMPTS:
        recs = model_recs(p, model)
        aggs = [agg_item(recs, it) for it in PRIMARY]
        for it, a in zip(PRIMARY, aggs):
            per_item_cell[(SHORT[model], p, it)] = a
        mae, means = respondent_macro_mae(aggs)
        lo, hi = boot_ci(means)
        pf = sum(a["n_pf"] for a in aggs) / max(1, sum(a["n_total"] for a in aggs))
        n_var = sum(1 for a in aggs if a["var_ratio"] is not None)
        n_fail = sum(1 for a in aggs if a["var_ratio"] is not None and a["var_ratio"] < 0.30)
        cells[f"{SHORT[model]}|{p}"] = {
            "model": SHORT[model], "model_slug": model, "prompt": p,
            "norm_mae": mae, "ci_lo": lo, "ci_hi": hi,
            "parse_fail_rate": pf, "cost": COST[model],
            "dq3_fail_frac": n_fail / n_var if n_var else None,
            "dq3_n_fail": n_fail, "dq3_n_items": n_var,
        }

# Random column (post-hoc deployment baseline, §5.4): use the parquet's
# materialised Random rows (seed=42 hash already routed each (rid,prompt) to one
# of the 4 models). Reporting-only; NOT a selector input.
random_cells = {}
for p in PROMPTS:
    aggs = [agg_item(_RANDOM_CACHE[p], it) for it in PRIMARY]
    mae, means = respondent_macro_mae(aggs)
    lo, hi = boot_ci(means)
    random_cells[p] = {"norm_mae": mae, "ci_lo": lo, "ci_hi": hi}

stats["cells"] = cells
stats["random_cells"] = random_cells

# --- majority baseline + uniform reference ----------------------------------
maj_mae, maj_modes = maj_baseline_mae(model_recs("P0", MODELS[0]))
stats["majority_baseline_mae"] = maj_mae

# --- model main effect / prompt main effect (respondent-macro, pooled) ------
def pooled_mae(prompts, models):
    aggs = []
    for p in prompts:
        for m in models:
            aggs += [agg_item(model_recs(p, m), it) for it in PRIMARY]
    mae, means = respondent_macro_mae(aggs)
    lo, hi = boot_ci(means)
    return {"norm_mae": mae, "ci_lo": lo, "ci_hi": hi}

stats["model_main"] = {SHORT[m]: pooled_mae(PROMPTS, [m]) for m in MODELS}
stats["prompt_main"] = {p: pooled_mae([p], MODELS) for p in PROMPTS}

# --- per-item difficulty (pooled across all 12 cells), + EM and lift --------
item_difficulty = {}
for it in PRIMARY:
    aggs = [agg_item(model_recs(p, m), it) for p in PROMPTS for m in MODELS]
    rid_vals = defaultdict(list)
    rid_em = defaultdict(list)
    for a in aggs:
        for rid, v in a["per_rid_nae"].items():
            rid_vals[rid].append(v)
        for rid, v in a["per_rid_em"].items():
            rid_em[rid].append(v)
    nae_means = [mean(v) for v in rid_vals.values() if v]
    em_means = [mean(v) for v in rid_em.values() if v]
    mae = mean(nae_means) if nae_means else None
    lo, hi = boot_ci(nae_means)
    em = mean(em_means) if em_means else None
    # majority em for this item (full 200 cohort)
    tr = agg_item(model_recs("P0", MODELS[0]), it)["truths"]
    cnt = Counter(tr.values())
    maj_em = max(cnt.values()) / sum(cnt.values()) if cnt else None
    n_eff = aggs[0]["n_ok"]
    item_difficulty[it] = {
        "norm_mae": mae, "ci_lo": lo, "ci_hi": hi, "em": em,
        "maj_em": maj_em, "uniform_em": 1.0 / META[it]["K"],
        "lift_maj": ((em - maj_em) / (1 - maj_em)) if (em is not None and maj_em is not None and maj_em < 1) else None,
        "K": META[it]["K"], "scale": SCALE_KIND[it], "construct": CONSTRUCT[it],
        "n_eff_per_cell": tr and len(tr),
    }
stats["item_difficulty"] = item_difficulty

# --- binary-item exact-match by model (the §7 binary sensitivity check) -----
BINARY = [it for it in PRIMARY if META[it]["K"] == 2]
binary_em = {}
for m in MODELS:
    binary_em[SHORT[m]] = {}
    for it in BINARY:
        # pool over prompts
        aggs = [agg_item(model_recs(p, m), it) for p in PROMPTS]
        n_ok = sum(a["n_ok"] for a in aggs)
        n_ex = sum(a["n_exact"] for a in aggs)
        binary_em[SHORT[m]][it] = (n_ex / n_ok) if n_ok else None
stats["binary_em_by_model"] = binary_em
stats["binary_items"] = BINARY

# --- output collapse diagnostic: per (model, item) distinct codes / top1 ----
collapse = {}
for m in MODELS:
    collapse[SHORT[m]] = {}
    for it in PRIMARY:
        aggs = [agg_item(model_recs(p, m), it) for p in PROMPTS]
        all_preds = Counter()
        # rebuild pred counter pooled across prompts
        preds = []
        for p in PROMPTS:
            for rid, s, cr in iter_samples(model_recs(p, m), it):
                if not s.get("parse_fail") and not s.get("skipped_missing_truth"):
                    pc = s.get("persona_code")
                    if pc is not None:
                        preds.append(pc)
        c = Counter(preds)
        collapse[SHORT[m]][it] = {
            "distinct": len(c), "K": META[it]["K"],
            "top1_share": (max(c.values()) / sum(c.values())) if c else None,
        }
stats["collapse"] = collapse

# ============================================================================
# STORYLINE 2 — GPT-4o anchor (N=100 paired)
# ============================================================================
def anchor_overall(records):
    aggs = [agg_item(records, it) for it in PRIMARY]
    mae, means = respondent_macro_mae(aggs)
    lo, hi = boot_ci(means)
    # overall EM (pooled)
    n_ok = sum(a["n_ok"] for a in aggs)
    n_ex = sum(a["n_exact"] for a in aggs)
    return {"norm_mae": mae, "ci_lo": lo, "ci_hi": hi,
            "em": n_ex / n_ok if n_ok else None,
            "per_item": {it: agg_item(records, it) for it in PRIMARY}}

anchorB = anchor_overall(anchor_on)    # R1 ON
anchorA = anchor_overall(anchor_off)   # R1 OFF

# cheap panel on the SAME 100 respondents, per prompt + selected cell (Qwen×P0)
cheap_100 = {}
for p in PROMPTS:
    aggs = [agg_item(model_recs(p, m, COHORT_100), it) for m in MODELS for it in PRIMARY]
    mae, means = respondent_macro_mae(aggs)
    lo, hi = boot_ci(means)
    cheap_100[p] = {"norm_mae": mae, "ci_lo": lo, "ci_hi": hi}

# "cheap best per respondent" not meaningful; use the §7 selected cell (Qwen×P0)
# and also the panel-pooled cheap @ R1 ON for the headline comparison.
sel_recs = model_recs("P0", "qwen/qwen3-max", COHORT_100)
sel_aggs = [agg_item(sel_recs, it) for it in PRIMARY]
sel_mae, sel_means = respondent_macro_mae(sel_aggs)
sel_lo, sel_hi = boot_ci(sel_means)
sel_em_nok = sum(a["n_ok"] for a in sel_aggs)
sel_em = sum(a["n_exact"] for a in sel_aggs) / sel_em_nok

# per-item EM for cheap-panel (pooled 4 models, P0) on the 100 cohort, vs anchors
anchor_per_item = {}
for it in PRIMARY:
    cheap_aggs = [agg_item(model_recs("P0", m, COHORT_100), it) for m in MODELS]
    n_ok = sum(a["n_ok"] for a in cheap_aggs)
    cheap_em = sum(a["n_exact"] for a in cheap_aggs) / n_ok if n_ok else None
    anchor_per_item[it] = {
        "cheap_panel_em": cheap_em,
        "gpt4o_R1on_em": anchorB["per_item"][it]["em"],
        "gpt4o_R1off_em": anchorA["per_item"][it]["em"],
        "cheap_panel_mae": mean([a["mae_norm_item"] for a in cheap_aggs if a["mae_norm_item"] is not None]),
        "gpt4o_R1on_mae": anchorB["per_item"][it]["mae_norm_item"],
        "gpt4o_R1off_mae": anchorA["per_item"][it]["mae_norm_item"],
        "scale": SCALE_KIND[it], "K": META[it]["K"], "n_eff": cheap_aggs[0]["n_ok"],
    }
stats["anchor_per_item"] = anchor_per_item

# --- PAIRED cheap-vs-frontier (per respondent normalized MAE) ---------------
# Selected cell (Qwen×P0) vs GPT-4o R1 ON, same 100 respondents.
def per_rid_macro(records):
    aggs = [agg_item(records, it) for it in PRIMARY]
    rid_vals = defaultdict(list)
    for a in aggs:
        for rid, v in a["per_rid_nae"].items():
            rid_vals[rid].append(v)
    return {rid: mean(v) for rid, v in rid_vals.items() if v}

sel_rid = per_rid_macro(sel_recs)
panelB_rid = per_rid_macro([r for p in ["P0"] for m in MODELS for r in model_recs(p, m, COHORT_100)])  # pooled cheap P0
gptB_rid = per_rid_macro(anchor_on)
gptA_rid = per_rid_macro(anchor_off)

common = sorted(set(sel_rid) & set(gptB_rid))
diff = np.array([gptB_rid[r] - sel_rid[r] for r in common])   # frontier - cheap; <0 means GPT better
# paired bootstrap CI on mean difference
rng = np.random.default_rng(SEED)
bd = diff[rng.integers(0, len(diff), size=(BOOT_B, len(diff)))].mean(axis=1)
paired = {
    "n_pairs": len(common),
    "cheap_sel_mae": float(np.mean([sel_rid[r] for r in common])),
    "gpt4o_R1on_mae": float(np.mean([gptB_rid[r] for r in common])),
    "mean_diff_frontier_minus_cheap": float(diff.mean()),
    "diff_ci_lo": float(np.percentile(bd, 2.5)),
    "diff_ci_hi": float(np.percentile(bd, 97.5)),
    "wilcoxon_p": float(wilcoxon(diff).pvalue) if np.any(diff != 0) else None,
    "frac_respondents_gpt_better": float(np.mean(diff < 0)),
    "diff_values": diff.tolist(),
}
stats["paired_cheap_vs_frontier"] = paired

# --- R1-protection cost: Anchor A (R1 OFF) vs B (R1 ON), per item ------------
r1_cost = {}
for it in PRIMARY:
    on = anchorB["per_item"][it]; off = anchorA["per_item"][it]
    r1_cost[it] = {
        "mae_R1on": on["mae_norm_item"], "mae_R1off": off["mae_norm_item"],
        "em_R1on": on["em"], "em_R1off": off["em"],
        "delta_mae_cost": (on["mae_norm_item"] - off["mae_norm_item"]) if (on["mae_norm_item"] is not None and off["mae_norm_item"] is not None) else None,
        "n_eff": off["n_ok"], "scale": SCALE_KIND[it],
    }
stats["r1_cost_per_item"] = r1_cost
# overall R1 cost (paired on the 100 cohort)
r1_common = sorted(set(gptA_rid) & set(gptB_rid))
r1_diff = np.array([gptB_rid[r] - gptA_rid[r] for r in r1_common])  # ON - OFF; >0 means protection costs
brd = r1_diff[rng.integers(0, len(r1_diff), size=(BOOT_B, len(r1_diff)))].mean(axis=1)
stats["r1_cost_overall"] = {
    "mae_R1on": anchorB["norm_mae"], "mae_R1off": anchorA["norm_mae"],
    "em_R1on": anchorB["em"], "em_R1off": anchorA["em"],
    "delta_mae": float(r1_diff.mean()),
    "delta_ci_lo": float(np.percentile(brd, 2.5)), "delta_ci_hi": float(np.percentile(brd, 97.5)),
}

stats["anchor_overall"] = {
    "gpt4o_R1on": {k: anchorB[k] for k in ("norm_mae", "ci_lo", "ci_hi", "em")},
    "gpt4o_R1off": {k: anchorA[k] for k in ("norm_mae", "ci_lo", "ci_hi", "em")},
    "cheap_panel_P0_100": cheap_100["P0"],
    "cheap_panel_byprompt_100": cheap_100,
    "selected_cell_qwen_p0_100": {"norm_mae": sel_mae, "ci_lo": sel_lo, "ci_hi": sel_hi, "em": sel_em},
}
# Park v2 external aggregate reference (notes/park_comparability.md §1, §10)
stats["park_reference"] = {
    "strategyA_norm": 0.82, "strategyA_raw": 0.6425,
    "strategyB_norm": 0.77, "strategyB_raw": 0.6057,
    "headline_norm": 0.82, "headline_raw": 0.6567,
    "note": "AGGREGATE only. Park v2 published NO per-item surveys-only table; "
            "SI Table 3 per-item numbers are the INTERVIEW condition (see "
            "notes/park_comparability.md §2,§6). Do not present per-item ours-vs-Park "
            "as surveys-only. Park raw is exact-match; normalized divides by 0.7953 "
            "human test-retest consistency (no GSS-2024 equivalent -> we report raw).",
}

# --- overall exact-match (100 cohort) for the Park-comparison figure --------
def pooled_em(records_list):
    n_ok = n_ex = 0
    for it in PRIMARY:
        for recs in records_list:
            a = agg_item(recs, it)
            n_ok += a["n_ok"]; n_ex += a["n_exact"]
    return n_ex / n_ok if n_ok else None

# majority accuracy on the 100 cohort (predict modal truth per item)
maj_em_100_nok = maj_em_100_nex = 0
for it in PRIMARY:
    tr = agg_item(model_recs("P0", MODELS[0], COHORT_100), it)["truths"]
    if tr:
        cnt = Counter(tr.values()); mode = cnt.most_common(1)[0][0]
        maj_em_100_nok += len(tr); maj_em_100_nex += cnt[mode]
stats["overall_em_100"] = {
    "majority": maj_em_100_nex / maj_em_100_nok if maj_em_100_nok else None,
    "cheap_panel_P0": pooled_em([model_recs("P0", m, COHORT_100) for m in MODELS]),
    "qwen_p0_selected": sel_em,
    "gpt4o_R1on": anchorB["em"],
    "gpt4o_R1off": anchorA["em"],
}

# ============================================================================
# SAVE + cross-checks
# ============================================================================
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(stats, indent=2, default=float))

print("=" * 70)
print("CROSS-CHECKS")
print("=" * 70)
print(f"{'cell':28s} {'this script':>12s}  (selector parquet: see below)")
for k in sorted(cells, key=lambda k: cells[k]["norm_mae"]):
    c = cells[k]
    print(f"  {k:26s} {c['norm_mae']:.4f}  CI[{c['ci_lo']:.4f},{c['ci_hi']:.4f}]  pf={c['parse_fail_rate']:.3f} dq3_fail={c['dq3_fail_frac']:.2f}")
print(f"\nmajority baseline MAE: {maj_mae:.4f}  (selector reported 0.2707)")
print(f"\nANCHOR (cross-check vs park_comparability.md: A raw 0.527 / B raw 0.492):")
print(f"  Anchor A (R1 OFF) em={anchorA['em']:.4f}  norm_mae={anchorA['norm_mae']:.4f}")
print(f"  Anchor B (R1 ON ) em={anchorB['em']:.4f}  norm_mae={anchorB['norm_mae']:.4f}")
print(f"  R1 protection cost (MAE, ON-OFF): {stats['r1_cost_overall']['delta_mae']:+.4f}")
print(f"\nPAIRED cheap(Qwen×P0) vs GPT-4o R1ON  (n={paired['n_pairs']}):")
print(f"  cheap MAE {paired['cheap_sel_mae']:.4f}  vs  GPT-4o MAE {paired['gpt4o_R1on_mae']:.4f}")
print(f"  frontier-minus-cheap {paired['mean_diff_frontier_minus_cheap']:+.4f} "
      f"CI[{paired['diff_ci_lo']:+.4f},{paired['diff_ci_hi']:+.4f}] "
      f"Wilcoxon p={paired['wilcoxon_p']:.2e}")
print(f"  GPT-4o better on {paired['frac_respondents_gpt_better']*100:.0f}% of respondents")
print(f"\nwrote {OUT}")
