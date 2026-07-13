"""Generate the Phase 1A report figures.

Storyline 1 (model + prompt selection) is built from report/databook_stats.json
— i.e. from raw_tables.xlsx, aggregated item-macro (equal weight per item),
with exact-match (EM) as the co-primary metric. Storyline 2 (GPT-4o anchor) is
built from report/phase1a_stats.json (anchor records).

  fig1_cell_forest          EM and MAE_n per cell, 95% CI, collapse-coloured
  fig2_model_prompt_heatmap  EM by model x prompt, marginals
  fig3_item_difficulty       per-item normalized MAE (item-macro, n-weighted)
  fig4_item_lift             per-item lift over majority baseline
  fig5_collapse_heatmap      model x ordinal-item output concentration
  fig6_accuracy_vs_park      exact-match: cheap vs GPT-4o (R1 on/off) vs Park
  fig7_paired_gap            per-respondent paired MAE gap, GPT-4o(R1on) - Qwen.P0
  fig8_r1_cost               per-item leakage-protection cost (battery vs singleton)
"""
from __future__ import annotations
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

ROOT = Path("/Users/joyce/Developer/gsbgen390")
FIG = ROOT / "report" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
DB = json.loads((ROOT / "report" / "databook_stats.json").read_text())   # raw_tables.xlsx, item-macro
S = json.loads((ROOT / "report" / "phase1a_stats.json").read_text())     # anchor records

plt.rcParams.update({
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
    "figure.dpi": 150, "savefig.dpi": 150, "savefig.bbox": "tight",
    "font.family": "DejaVu Sans",
})
INK = "#222222"; BLUE = "#2f6f9f"; RED = "#c0504d"; GREEN = "#4a7c59"
GREY = "#8a8a8a"; ORANGE = "#d98c3f"; GOLD = "#c79a2e"

NP_PATH = ROOT / "report" / "no_persona_stats.json"
NP = json.loads(NP_PATH.read_text()) if NP_PATH.exists() else None
BS_PATH = ROOT / "report" / "bayati_stats.json"
BS = json.loads(BS_PATH.read_text()) if BS_PATH.exists() else None
ITEMS = list(DB["per_item"].keys())
MAJ_MAE = DB["base_rate_mae_macro"]               # 0.2748 item-macro (matches item-macro cell MAEs)
MAJ_EM = DB["majority_em_macro"]                  # item-macro base-rate EM
REC = "kk2|P2"                                    # recommended cell
SINGLETON = {"POLVIEWS", "PARTYID", "CAPPUN", "GUNLAW", "SATFIN"}


def save(fig, name):
    p = FIG / name
    fig.savefig(p); plt.close(fig)
    print("wrote", p.relative_to(ROOT))


# ---------------------------------------------------------------------------
# FIG 1 — two-panel cell forest: EM (higher better) and MAE_n (lower better)
# ---------------------------------------------------------------------------
def fig1():
    cells = DB["cells"]
    order = sorted(cells, key=lambda k: -cells[k]["em"])     # rank by EM desc
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.4, 6.0), sharey=True)
    y = np.arange(len(order))[::-1]
    for yi, k in zip(y, order):
        c = cells[k]
        collapse = c["n_collapse"] > 0
        col = RED if collapse else BLUE
        rec = (k == REC)
        # EM panel
        axL.errorbar(c["em"], yi, xerr=[[c["em"] - c["em_ci"][0]], [c["em_ci"][1] - c["em"]]],
                     fmt="o", color=col, ecolor=col, elinewidth=1.5, capsize=3,
                     ms=9 if rec else 6, mec=GOLD if rec else col, mew=2.4 if rec else 0, zorder=3)
        # MAE panel
        axR.errorbar(c["mae_n"], yi, xerr=[[c["mae_n"] - c["mae_ci"][0]], [c["mae_ci"][1] - c["mae_n"]]],
                     fmt="o", color=col, ecolor=col, elinewidth=1.5, capsize=3,
                     ms=9 if rec else 6, mec=GOLD if rec else col, mew=2.4 if rec else 0, zorder=3)
    labels = []
    for k in order:
        c = cells[k]
        lab = f'{c["name"]} × {c["prompt"]}'
        if k == REC:
            lab = "★ " + lab
        if c["n_collapse"]:
            lab += f'  ({c["n_collapse"]} collapse)'
        labels.append(lab)
    axL.set_yticks(y); axL.set_yticklabels(labels, fontsize=9)
    axL.axvline(MAJ_EM, color=INK, ls="--", lw=1.2)
    axL.text(MAJ_EM, y.max() + 0.35, f"base rate {MAJ_EM:.2f}", color=INK, fontsize=8, ha="center")
    axL.set_xlabel("Exact-match accuracy  (higher = better)")
    axL.set_title("Accuracy: no statistical winner", loc="left", fontsize=11.5)
    axR.axvline(MAJ_MAE, color=INK, ls="--", lw=1.2)
    axR.text(MAJ_MAE, y.max() + 0.35, f"base rate {MAJ_MAE:.2f}", color=INK, fontsize=8, ha="center")
    axR.set_xlabel("Normalized MAE  (lower = better)")
    axR.set_title("Error: lowest-MAE cells are the collapsed ones", loc="left", fontsize=11.5)
    fig.suptitle("All 12 cheap (model × prompt) cells overlap — ranked by exact-match",
                 fontsize=13, fontweight="bold", x=0.02, ha="left", y=1.005)
    axR.legend(handles=[
        Patch(color=BLUE, label="no output collapse"),
        Patch(color=RED, label="≥1 item collapses (top-1 share > 0.95)"),
        Patch(facecolor="white", edgecolor=GOLD, linewidth=2.4, label="★ recommended for Phase 1B"),
    ], loc="lower right", fontsize=8.5, frameon=True)
    fig.tight_layout()
    save(fig, "fig1_cell_forest.png")


# ---------------------------------------------------------------------------
# FIG 2 — model x prompt heatmap (exact-match, item-macro)
# ---------------------------------------------------------------------------
def fig2():
    models = ["q3m", "ds31", "l4m", "kk2"]; names = {"q3m": "Qwen3-Max", "ds31": "DeepSeek-V3.1", "l4m": "Llama-4-Mav", "kk2": "Kimi-K2"}
    prompts = ["P0", "P1", "P2"]
    M = np.array([[DB["cells"][f"{m}|{p}"]["em"] for p in prompts] for m in models])
    C = np.array([[DB["cells"][f"{m}|{p}"]["n_collapse"] for p in prompts] for m in models])
    fig, ax = plt.subplots(figsize=(6.8, 5.0))
    vmax = max(abs(M - MAJ_EM).max(), 0.01)
    im = ax.imshow(M, cmap="RdBu", vmin=MAJ_EM - vmax, vmax=MAJ_EM + vmax, aspect="auto")
    ax.set_xticks(range(3)); ax.set_xticklabels(
        [f"{p}\n{lab}" for p, lab in zip(prompts, ["key-value\n(Park)", "1st-person\n(Argyle)", "interview\n(Wang)"])], fontsize=9)
    ax.set_yticks(range(4)); ax.set_yticklabels([names[m] for m in models])
    for i in range(4):
        for j in range(3):
            txt = f"{M[i, j]:.3f}"
            if C[i, j] > 0:
                txt += f"\n({C[i, j]} collapse)"
            ax.text(j, i, txt, ha="center", va="center",
                    color="white" if abs(M[i, j] - MAJ_EM) > vmax * 0.55 else INK, fontsize=9.5, fontweight="bold")
    ax.set_title("Exact-match by model × prompt  (blue = above base rate)", loc="left")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label(f"exact-match accuracy  (white = base rate {MAJ_EM:.2f})", fontsize=8)
    pm = [np.mean([DB["cells"][f"{m}|{p}"]["em"] for m in models]) for p in prompts]
    mm = [np.mean([DB["cells"][f"{m}|{p}"]["em"] for p in prompts]) for m in models]
    txt = ("prompt means:  " + "   ".join(f"{p} {v:.3f}" for p, v in zip(prompts, pm))
           + "\nmodel means:  " + "   ".join(f"{names[m].split('-')[0]} {v:.3f}" for m, v in zip(models, mm)))
    ax.text(0.0, -0.30, txt, transform=ax.transAxes, fontsize=8.5, color=INK, va="top")
    save(fig, "fig2_model_prompt_heatmap.png")


# ---------------------------------------------------------------------------
# FIG 3 — per-item difficulty (normalized MAE, item-macro, n-weighted)
# ---------------------------------------------------------------------------
def fig3():
    d = DB["per_item"]
    order = sorted(ITEMS, key=lambda it: d[it]["mae_n"])
    vals = [d[it]["mae_n"] for it in order]
    colors = [ORANGE if d[it]["tx"] == "cat" else BLUE for it in order]
    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    y = np.arange(len(order))
    ax.barh(y, vals, color=colors, alpha=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels([f'{it}  (K={d[it]["K"]}, n≈{d[it]["n_eff"]})' for it in order], fontsize=8.8)
    ax.invert_yaxis()
    ax.set_xlabel("Normalized MAE  (pooled over the 12 cheap cells; lower = easier)")
    ax.set_title("Per-item difficulty: party ID and ideology easiest, race / death-penalty hardest", loc="left")
    ax.legend(handles=[Patch(color=BLUE, label="ordinal (Likert)"),
                       Patch(color=ORANGE, label="binary")], loc="lower right", fontsize=9)
    save(fig, "fig3_item_difficulty.png")


# ---------------------------------------------------------------------------
# FIG 4 — per-item lift over majority baseline
# ---------------------------------------------------------------------------
def fig4():
    d = DB["per_item"]
    order = sorted(ITEMS, key=lambda it: d[it]["lift_maj"])
    vals = [d[it]["lift_maj"] for it in order]
    colors = [GREEN if v > 0 else RED for v in vals]
    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    y = np.arange(len(order))
    ax.barh(y, vals, color=colors, alpha=0.9)
    ax.axvline(0, color=INK, lw=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels([f'{it}  (EM {d[it]["em"]:.2f} vs base rate {d[it]["maj_em"]:.2f})' for it in order], fontsize=8.6)
    ax.invert_yaxis()
    ax.set_xlabel("Lift over base-rate baseline   (EM − base) / (1 − base)")
    ax.set_title("Where the LLM adds signal: only party ID and abortion clearly beat\n"
                 "the base rate ('always guess the most common answer')", loc="left")
    ax.legend(handles=[Patch(color=GREEN, label="LLM beats base rate"),
                       Patch(color=RED, label="LLM worse than base rate")], loc="lower right", fontsize=9)
    save(fig, "fig4_item_lift.png")


# ---------------------------------------------------------------------------
# FIG 5 — output concentration / mode collapse (ordinal items, from databook)
# ---------------------------------------------------------------------------
def fig5():
    models = ["q3m", "ds31", "l4m", "kk2"]; names = {"q3m": "Qwen3-Max", "ds31": "DeepSeek-V3.1", "l4m": "Llama-4-Mav", "kk2": "Kimi-K2"}
    ord_items = [it for it in ITEMS if DB["collapse_mat"]["q3m"][it]["K"] >= 3]
    M = np.array([[DB["collapse_mat"][m][it]["top1"] for it in ord_items] for m in models])
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    im = ax.imshow(M, cmap="OrRd", vmin=0.3, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(ord_items)))
    ax.set_xticklabels([f"{it}\n(K={DB['collapse_mat']['q3m'][it]['K']})" for it in ord_items], fontsize=8.5)
    ax.set_yticks(range(4)); ax.set_yticklabels([names[m] for m in models])
    for i in range(4):
        for j in range(len(ord_items)):
            v = M[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    color="white" if v > 0.78 else INK, fontsize=9, fontweight="bold" if v > 0.95 else "normal")
    ax.set_title("Output concentration on ordinal items: the confidence battery collapses to one answer", loc="left")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03); cb.set_label("top-1 answer share", fontsize=8)
    ax.text(0.0, -0.42, "Top-1 share > 0.95 (bold) = mode collapse: the model emits one code regardless of persona.\n"
                        "CONFINAN / CONLEGIS collapse for every model except Kimi-K2 — the basis for the Phase 1B recommendation.",
            transform=ax.transAxes, fontsize=8, color=GREY, va="top")
    save(fig, "fig5_collapse_heatmap.png")


# ---------------------------------------------------------------------------
# FIG 6 — exact-match: cheap vs GPT-4o vs Park   (anchor stats)
# ---------------------------------------------------------------------------
def fig6():
    # Protocol-matched at P0 (GPT-4o anchor only ran P0), N=100 paired cohort.
    o = S["overall_em_100"]; pk = S["park_reference"]
    bars = [("Base rate\n(majority class)", o["majority"], GREY, "R1 on"),
            ("Cheap panel\n(4 models, P0)", o["cheap_panel_P0"], BLUE, "R1 on"),
            ("GPT-4o\n(our protocol)", o["gpt4o_R1on"], GREEN, "R1 on"),
            ("GPT-4o\n(Park-exact)", o["gpt4o_R1off"], "#2e5d3a", "R1 off")]
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    x = np.arange(len(bars))
    ax.bar(x, [b[1] for b in bars], color=[b[2] for b in bars], width=0.62, alpha=0.92)
    for xi, b in zip(x, bars):
        ax.text(xi, b[1] + 0.008, f"{b[1]:.3f}", ha="center", fontsize=9, fontweight="bold")
        ax.text(xi, 0.012, b[3], ha="center", color="white", fontsize=7.5, fontweight="bold")
    ax.axhline(pk["strategyA_raw"], color="#7a4fa0", ls="--", lw=1.4)
    ax.text(len(bars) - 0.5, pk["strategyA_raw"] + 0.004, f"Park v2 surveys-only, Strategy A = {pk['strategyA_raw']:.2f}", ha="right", color="#7a4fa0", fontsize=8.5)
    ax.axhline(pk["strategyB_raw"], color="#7a4fa0", ls=":", lw=1.2)
    ax.text(len(bars) - 0.5, pk["strategyB_raw"] - 0.018, f"Park v2, Strategy B = {pk['strategyB_raw']:.2f}", ha="right", color="#7a4fa0", fontsize=8.5)
    ax.set_xticks(x); ax.set_xticklabels([b[0] for b in bars], fontsize=8.8)
    ax.set_ylim(0, 0.70); ax.set_ylabel("Exact-match accuracy (raw, Park's metric)")
    ax.set_title("Cheap vs frontier vs Park: under our leakage protocol everyone hugs the base-rate baseline", loc="left")
    ax.text(0.0, -0.16, "Park reference is AGGREGATE over Park's full item set (no per-item surveys-only table exists). "
                        "Park normalizes by 0.7953 human test-retest; shown here as raw to match our metric.", transform=ax.transAxes, fontsize=8, color=GREY, va="top")
    save(fig, "fig6_accuracy_vs_park.png")


# ---------------------------------------------------------------------------
# FIG 7 — paired cheap-vs-frontier gap (anchor stats)
# ---------------------------------------------------------------------------
def fig7():
    pr = S["paired_cheap_vs_frontier"]; diff = np.array(pr["diff_values"])
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.hist(diff, bins=22, color=BLUE, alpha=0.55, edgecolor="white")
    ax.axvline(0, color=INK, lw=1.3); ax.axvline(pr["mean_diff_frontier_minus_cheap"], color=RED, lw=2)
    ax.axvspan(pr["diff_ci_lo"], pr["diff_ci_hi"], color=RED, alpha=0.12)
    ax.set_xlabel("Per-respondent normalized-MAE gap:  GPT-4o (R1 on)  −  cheap cell (Qwen3-Max×P0)")
    ax.set_ylabel("respondents")
    ax.set_title("Holding the protocol fixed, GPT-4o and the cheap cell are a statistical tie", loc="left")
    txt = (f"mean gap = {pr['mean_diff_frontier_minus_cheap']:+.4f}   95% CI [{pr['diff_ci_lo']:+.4f}, {pr['diff_ci_hi']:+.4f}]\n"
           f"Wilcoxon p = {pr['wilcoxon_p']:.2f}  (n.s.)   GPT-4o better on {pr['frac_respondents_gpt_better']*100:.0f}% of {pr['n_pairs']} respondents")
    ax.text(0.98, 0.95, txt, transform=ax.transAxes, ha="right", va="top", fontsize=9, bbox=dict(boxstyle="round", fc="white", ec=GREY))
    ax.text(0.02, 0.95, "← GPT-4o better", transform=ax.transAxes, color=GREEN, fontsize=9, va="top")
    ax.text(0.98, 0.55, "cheap better →", transform=ax.transAxes, color=BLUE, fontsize=9, ha="right")
    save(fig, "fig7_paired_gap.png")


# ---------------------------------------------------------------------------
# FIG 8 — R1 leakage-protection cost per item (anchor stats)
# ---------------------------------------------------------------------------
def fig8():
    rc = S["r1_cost_per_item"]
    order = sorted(ITEMS, key=lambda it: rc[it]["delta_mae_cost"], reverse=True)
    vals = [rc[it]["delta_mae_cost"] for it in order]
    colors = [GREY if it in SINGLETON else BLUE for it in order]
    fig, ax = plt.subplots(figsize=(8.2, 5.4)); y = np.arange(len(order))
    ax.barh(y, vals, color=colors, alpha=0.9); ax.axvline(0, color=INK, lw=1.2)
    ax.set_yticks(y); ax.set_yticklabels([f"{it}" + ("  (singleton)" if it in SINGLETON else "  (battery)") for it in order], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("R1 leakage-protection cost  =  MAE(R1 on) − MAE(R1 off)   [GPT-4o, N=100]")
    ov = S["r1_cost_overall"]
    ax.set_title("Leakage protection costs accuracy only where R1 removes sibling items (batteries)", loc="left")
    ax.legend(handles=[Patch(color=BLUE, label="battery item (R1 drops informative siblings)"),
                       Patch(color=GREY, label="singleton item (R1 is a no-op)")], loc="lower right", fontsize=9)
    ax.text(0.0, -0.13, f"Overall R1 cost = {ov['delta_mae']:+.4f} normalized MAE (95% CI [{ov['delta_ci_lo']:+.4f}, {ov['delta_ci_hi']:+.4f}]). "
                        f"Concentrated on the confidence, redistribution, and abortion batteries.", transform=ax.transAxes, fontsize=8, color=GREY, va="top")
    save(fig, "fig8_r1_cost.png")


# ---------------------------------------------------------------------------
# FIG 9 — persona vs two baselines (base rate, model's own no-persona prior)
# ---------------------------------------------------------------------------
def fig9():
    if NP is None:
        print("skip fig9 (no_persona_stats.json missing)"); return
    pit = NP["per_item"]
    order = [it for it in ITEMS if it in pit]
    order = sorted(order, key=lambda it: pit[it]["cell_em"])
    y = np.arange(len(order)); h = 0.26
    base = [pit[it]["base_rate_em"] for it in order]
    nop = [pit[it]["no_persona_em_mode"] for it in order]
    cell = [pit[it]["cell_em"] for it in order]
    fig, ax = plt.subplots(figsize=(8.6, 6.0))
    ax.barh(y + h, cell, height=h, color=BLUE, label="Kimi-K2 × P2 (full persona)")
    ax.barh(y, base, height=h, color=GREY, label="base-rate guess (oracle floor)")
    ax.barh(y - h, nop, height=h, color=ORANGE, label="no-persona (model's own prior — fair floor)")
    ax.set_yticks(y); ax.set_yticklabels(order, fontsize=9)
    ax.set_xlabel("Exact-match accuracy")
    ax.set_title("Persona vs two baselines: it beats the model's own prior on 9 of 12 questions", loc="left")
    ax.legend(fontsize=8.5, loc="lower right")
    ov = NP["overall"]
    ax.text(0.0, -0.11, f"Overall (questions weighted equally): model's own prior {ov['no_persona_em_mode']:.3f}  <  "
                        f"base rate {ov['base_rate_em']:.3f}  <  full persona {ov['cell_em']:.3f}.  "
                        f"The prior is miscalibrated (leans liberal/Democrat), so it trails even the base rate;\n"
                        f"the persona corrects it (+{ov['cell_em']-ov['no_persona_em_mode']:.3f}). It still actively hurts on FEPOL, CONFINAN, HELPPOOR.",
            transform=ax.transAxes, fontsize=8, color=GREY, va="top")
    save(fig, "fig9_no_persona.png")


# ---------------------------------------------------------------------------
# FIG 10 — regression: how the 5 models and 3 prompts compare (clustered)
# ---------------------------------------------------------------------------
def fig10():
    if BS is None:
        print("skip fig10"); return
    rows = [("kimi_vs_Random", "kimi  vs Random"), ("deepseek_vs_Random", "deepseek  vs Random"),
            ("llama_vs_Random", "llama  vs Random"), ("qwen_vs_Random", "qwen  vs Random"),
            ("P1_vs_P0", "P1  vs P0"), ("P2_vs_P0", "P2  vs P0")]
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 5.2))
    for ax, dv, betterdir, title in [
        (axes[0], "reg_exact", +1, "Exact match  (right = better)"),
        (axes[1], "reg_nerr", -1, "Normalized error  (left = better)")]:
        terms = BS[dv]["terms"]
        y = np.arange(len(rows))[::-1]
        for yi, (key, _) in zip(y, rows):
            t = terms[key]; c, lo, hi, p = t["coef"], t["lo"], t["hi"], t["p"]
            good = (c * betterdir > 0)
            col = (GREEN if good else RED) if p < 0.05 else GREY
            ax.errorbar(c, yi, xerr=[[c - lo], [hi - c]], fmt="o", color=col, ecolor=col,
                        elinewidth=1.6, capsize=3, ms=6)
            ax.text(hi + 0.0015, yi, ("p<0.05" if p < 0.05 else "n.s."), va="center",
                    fontsize=7.5, color=col)
        ax.axvline(0, color=INK, lw=1.2)
        ax.axhspan(1.5, 5.5, color="#f0f0f0", zorder=0)   # shade the 4 model rows
        ax.set_yticks(y); ax.set_yticklabels([lab for _, lab in rows], fontsize=9)
        ax.set_xlabel("coefficient (Δ vs reference)")
        ax.set_title(title, loc="left", fontsize=11)
    fig.suptitle("How the 5 models and 3 prompts compare (regression, respondent-clustered 95% CI)",
                 fontsize=12.5, fontweight="bold", x=0.02, ha="left", y=1.02)
    axes[0].text(0.0, -0.16, "Models compared to the Random policy; prompts to P0. Green = significantly better, red = worse, grey = not distinguishable.\n"
                            "No model significantly beats Random on either metric (only qwen is significantly worse). P1 and P2 both beat P0.",
                 transform=axes[0].transAxes, fontsize=8, color=GREY, va="top")
    fig.tight_layout()
    save(fig, "fig10_regression.png")


# ---------------------------------------------------------------------------
# FIG 11 — router (secondary): best single vs router vs oracle ceiling
# ---------------------------------------------------------------------------
def fig11():
    if BS is None:
        print("skip fig11"); return
    R = BS["router"]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.8))
    for ax, metric, title, better in [(axes[0], "exact", "Exact match (higher better)", "+"),
                                       (axes[1], "nerr", "Normalized error (lower better)", "−")]:
        r = R[metric]
        labels = [f"best single\n({r['best_single_name']})", "router", "oracle\n(ceiling)"]
        vals = [r["best_single"], r["router"], r["oracle"]]
        cis = [r["best_single_ci"], r["router_ci"], None]
        cols = [GREY, BLUE, "#cfd8dc"]
        x = np.arange(3)
        for xi, v, ci, c in zip(x, vals, cis, cols):
            err = [[v - ci[0]], [ci[1] - v]] if ci else None
            ax.bar(xi, v, color=c, width=0.6)
            if err:
                ax.errorbar(xi, v, yerr=err, fmt="none", ecolor=INK, elinewidth=1.3, capsize=4)
            ax.text(xi, v + (0.006 if metric == "exact" else 0.004), f"{v:.3f}", ha="center", fontsize=9, fontweight="bold")
        gain = r["gain"]; glo, ghi = r["gain_ci"]
        sig = "excludes 0" if (glo > 0 or ghi < 0) else "crosses 0"
        ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5)
        ax.set_title(f"{title}\nrouter gain {gain:+.3f}  95% CI [{glo:+.3f}, {ghi:+.3f}] ({sig})", loc="left", fontsize=9.5)
    fig.suptitle("Per-question router (Bayati): a modest, real gain on normalized error; low ceiling",
                 fontsize=12, fontweight="bold", x=0.02, ha="left", y=1.03)
    fig.tight_layout()
    save(fig, "fig11_router.png")


for f in (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11):
    f()
print("\nall figures written to", FIG.relative_to(ROOT))
