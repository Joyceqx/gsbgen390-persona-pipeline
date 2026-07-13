"""Compute the metric / regression / router statistics from Prof. Bayati's
reanalysis, on the identical raw prediction CSV, and save report/bayati_stats.json
for the figures and report.

  - exact match + normalized error per row (parse failures penalised)
  - model & prompt regression coefficients (vs Random / vs P0), respondent-CLUSTERED
  - model & prompt marginal means
  - per-item flip (exact match vs normalized error)
  - llama-vs-kimi collapse-vs-hedge dissection (top-1 share where llama beats kimi)
  - router: best-single vs router vs oracle on both metrics (his fixed 100/100 split)
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path("/Users/joyce/Developer/gsbgen390")
CSV = ROOT / "report" / "csv" / "phase1a_raw_predictions.csv"
OUT = ROOT / "report" / "bayati_stats.json"

RANGE = {'ABANY':1,'CAPPUN':1,'GUNLAW':1,'FEPOL':1,'RACDIF1':1,'CONFINAN':2,
         'CONLEGIS':2,'SATFIN':2,'FECHLD':3,'HELPPOOR':4,'POLVIEWS':6,'PARTYID':6}
K = {'ABANY':2,'CAPPUN':2,'GUNLAW':2,'FEPOL':2,'RACDIF1':2,'CONFINAN':3,
     'CONLEGIS':3,'SATFIN':3,'FECHLD':4,'HELPPOOR':5,'POLVIEWS':7,'PARTYID':8}
SH = {'Random':'Random','moonshotai/kimi-k2-0905':'kimi',
      'deepseek/deepseek-v3.1-terminus':'deepseek',
      'meta-llama/llama-4-maverick':'llama','qwen/qwen3-max':'qwen'}

df = pd.read_csv(CSV)
df['range'] = df['item'].map(RANGE)
ok = df['parse_ok'].values
df['exact'] = np.where(ok, (df['true_code'] == df['pred_code']).astype(float), 0.0)
df['nerr'] = np.where(ok, df['abs_err'] / df['range'], 1.0)
df['model'] = pd.Categorical(df['model'], list(SH.keys()))   # Random = ref
df['prompt'] = pd.Categorical(df['prompt'], ['P0', 'P1', 'P2'])

out = {}

# ---- regressions (respondent-clustered) ------------------------------------
def regression(dv):
    m = smf.ols(f'{dv} ~ C(model)+C(prompt)+C(item)', data=df).fit(
        cov_type='cluster', cov_kwds={'groups': df['respondent_id']})
    ci = m.conf_int()
    terms = {}
    for slug, sh in SH.items():
        if sh == 'Random':
            continue
        t = f'C(model)[T.{slug}]'
        terms[f'{sh}_vs_Random'] = {'coef': float(m.params[t]), 'lo': float(ci.loc[t][0]),
                                    'hi': float(ci.loc[t][1]), 'p': float(m.pvalues[t])}
    for p in ['P1', 'P2']:
        t = f'C(prompt)[T.{p}]'
        terms[f'{p}_vs_P0'] = {'coef': float(m.params[t]), 'lo': float(ci.loc[t][0]),
                               'hi': float(ci.loc[t][1]), 'p': float(m.pvalues[t])}
    return {'r2': float(m.rsquared), 'n': int(m.nobs), 'intercept': float(m.params['Intercept']),
            'terms': terms}

out['reg_exact'] = regression('exact')
out['reg_nerr'] = regression('nerr')

# ---- marginal means --------------------------------------------------------
out['means'] = {
    'exact': {'by_model': {SH[k]: float(v) for k, v in df.groupby('model', observed=True)['exact'].mean().items()},
              'by_prompt': {p: float(v) for p, v in df.groupby('prompt', observed=True)['exact'].mean().items()}},
    'nerr': {'by_model': {SH[k]: float(v) for k, v in df.groupby('model', observed=True)['nerr'].mean().items()},
             'by_prompt': {p: float(v) for p, v in df.groupby('prompt', observed=True)['nerr'].mean().items()}},
}

# ---- per-item flip (exact vs nerr) -----------------------------------------
bi = df.groupby('item').agg(levels=('range', lambda s: int(s.iloc[0]) + 1),
                            exact=('exact', 'mean'), nerr=('nerr', 'mean'))
out['per_item_flip'] = {it: {'levels': int(r.levels), 'exact': float(r.exact), 'nerr': float(r.nerr)}
                        for it, r in bi.iterrows()}

# ---- llama vs kimi collapse-vs-hedge dissection ----------------------------
diss = {}
for it in RANGE:
    ki = df[(df.model == 'moonshotai/kimi-k2-0905') & (df.item == it)]
    ll = df[(df.model == 'meta-llama/llama-4-maverick') & (df.item == it)]
    llo = ll[ll.parse_ok]['pred_code']
    diss[it] = {'K': K[it], 'kimi_nerr': float(ki['nerr'].mean()), 'llama_nerr': float(ll['nerr'].mean()),
                'llama_top1': float(llo.value_counts().iloc[0] / len(llo))}
out['llama_kimi_dissection'] = diss

# ---- router (his fixed split: seed 42, prompt P1, 4 real LLMs) --------------
CAND = ['deepseek/deepseek-v3.1-terminus', 'meta-llama/llama-4-maverick',
        'moonshotai/kimi-k2-0905', 'qwen/qwen3-max']
d = df[(df.prompt == 'P1') & (df.model.isin(CAND))].copy()
items = sorted(d['item'].unique())
resp = np.array(sorted(d['respondent_id'].unique()))
perm = np.random.RandomState(42).permutation(resp)
TEST, TRAIN = set(perm[:100]), set(perm[100:])
tr, te = d[d.respondent_id.isin(TRAIN)], d[d.respondent_id.isin(TEST)]

def learn(metric):
    return {it: (tr[tr.item == it].groupby('model', observed=True)[metric].mean().idxmin() if metric == 'nerr'
                 else tr[tr.item == it].groupby('model', observed=True)[metric].mean().idxmax()) for it in items}

def per_resp_sums(choice, best_single, metric):
    rows = []
    for r, g in te.groupby('respondent_id'):
        rv = np.concatenate([g[(g.item == it) & (g.model == choice[it])][metric].values for it in items])
        sv = g[g.model == best_single][metric].values
        rows.append((rv.sum(), len(rv), sv.sum(), len(sv)))
    return np.array(rows)

def boot(sums, metric, B=3000, seed=1):
    rs = np.random.RandomState(seed); n = len(sums)
    R = np.empty(B); S = np.empty(B)
    for b in range(B):
        s = sums[rs.randint(0, n, n)]
        R[b] = s[:, 0].sum() / s[:, 1].sum(); S[b] = s[:, 2].sum() / s[:, 3].sum()
    gap = (S - R) if metric == 'nerr' else (R - S)
    pct = lambda a: [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]
    return pct(R), pct(S), float(gap.mean()), pct(gap)

def oracle(metric):
    vals = []
    for it in items:
        sub = te[te.item == it]; tm = sub.groupby('model', observed=True)[metric].mean()
        oc = tm.idxmin() if metric == 'nerr' else tm.idxmax()
        vals.append(sub[sub.model == oc][metric].values)
    return float(np.concatenate(vals).mean())

router = {}
for metric in ['exact', 'nerr']:
    choice = learn(metric)
    bs = (tr.groupby('model', observed=True)[metric].mean().idxmin() if metric == 'nerr'
          else tr.groupby('model', observed=True)[metric].mean().idxmax())
    sums = per_resp_sums(choice, bs, metric)
    rmean = float(sums[:, 0].sum() / sums[:, 1].sum()); smean = float(sums[:, 2].sum() / sums[:, 3].sum())
    rci, sci, gmean, gci = boot(sums, metric)
    # routed-model collapse (top-1 share of routed model on its item, full data)
    pol = {}
    for it in items:
        m = choice[it]; o = df[(df.model == m) & (df.item == it) & df.parse_ok]['pred_code']
        pol[it] = {'model': SH[m], 'top1': float(o.value_counts().iloc[0] / len(o))}
    router[metric] = {'router': rmean, 'router_ci': rci, 'best_single': smean, 'best_single_name': SH[bs],
                      'best_single_ci': sci, 'oracle': oracle(metric), 'gain': gmean, 'gain_ci': gci,
                      'policy': pol}
out['router'] = router
out['router_meta'] = {'train': len(TRAIN), 'test': len(TEST), 'prompt': 'P1'}

OUT.write_text(json.dumps(out, indent=2))
print("wrote", OUT.relative_to(ROOT))
print(f"\nKimi vs Random:  exact {out['reg_exact']['terms']['kimi_vs_Random']['coef']:+.4f} "
      f"(p={out['reg_exact']['terms']['kimi_vs_Random']['p']:.2f})   "
      f"nerr {out['reg_nerr']['terms']['kimi_vs_Random']['coef']:+.4f} "
      f"(p={out['reg_nerr']['terms']['kimi_vs_Random']['p']:.2f})")
print(f"Router nerr gain: {router['nerr']['gain']:+.4f} CI {router['nerr']['gain_ci']}")
print(f"Router exact gain: {router['exact']['gain']:+.4f} CI {router['exact']['gain_ci']}")
print("nerr router policy collapse:", {it: f"{v['model']}({v['top1']:.2f})" for it, v in router['nerr']['policy'].items() if v['top1'] > 0.9})
