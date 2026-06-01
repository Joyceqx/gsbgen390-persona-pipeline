#!/bin/bash
# Phase 1A 进度 + 健康检查（panel F'' 跑期间任何时候可用）
# Usage: bash check.sh

cd "$(dirname "$0")"

echo "═══════════════════════════════════════════"
echo "  Phase 1A 状态 — $(date '+%a %b %d %H:%M')"
echo "═══════════════════════════════════════════"

# 1. 死活
if tmux ls 2>/dev/null | grep -q phase1a && ps aux | grep "src/gss_driver" | grep -v grep > /dev/null; then
  echo "✓ 还在跑"
else
  if [ -f "outputs/phase1a_raw.parquet" ]; then
    echo "🎉 跑完了！outputs/phase1a_raw.parquet 已生成"
  else
    echo "⚠️ 死了——看 outputs/phase1a_run.log 末尾 + 跑 bash launch_phase1a.sh 续上"
  fi
fi

# 2. 进度 + ETA
echo
echo "📊 进度 + ETA"
python3 << 'PY'
import re, glob, json
from datetime import datetime, timedelta
try:
    with open('outputs/phase1a_run.log') as f: log = f.read()
    respondents = re.findall(r'respondent (\d+)/200', log)
    elapsed = re.findall(r'elapsed (\d+)s', log)
    if respondents and elapsed:
        n = int(respondents[-1])
        t = int(elapsed[-1])
        per = t / n
        # 已完成的 prompt JSON（每 200 respondent 出一个）
        jsons = sorted(glob.glob('outputs/gss_phase1_records_n200*_seed42_P*.json'))
        # 看最新 JSON 里 respondent 数判断哪个 prompt 正在跑
        which_prompt_idx = 0  # P0, P1, P2 → 0, 1, 2
        if jsons:
            with open(jsons[-1]) as fp:
                latest = json.load(fp)
            n_in_latest = len(set(r['respondent_id'] for r in latest))
            # 如果最新 JSON 有 200 个 respondent → 这个 prompt 完成，下一个进行中
            # 否则 → 这个 prompt 正在跑
            which_prompt_idx = len(jsons) if n_in_latest >= 200 else len(jsons) - 1
        # 剩余: 当前 prompt 还剩 + 未来 prompts
        future_prompts = max(0, 2 - which_prompt_idx)
        remaining_in_current = 200 - n
        total_remaining = (remaining_in_current + 200 * future_prompts) * per
        eta = datetime.now() + timedelta(seconds=total_remaining)
        completed_prompts = ', '.join('P' + j.split('_P')[1][0] for j in jsons)
        print(f"   当前: P{which_prompt_idx} respondent {n}/200")
        print(f"   速度: {per:.0f}s/resp = {60/per:.2f} resp/min")
        print(f"   完成 ETA: {eta.strftime('%a %b %d %H:%M')}  ({total_remaining/3600:.1f}h 后)")
        print(f"   已开始 JSON: {completed_prompts if completed_prompts else 'none yet'}")
    else:
        print("   no respondent data yet")
except Exception as e:
    print(f"   err: {e}")
PY

# 3. 各 model 表现（仅 P0 JSON 存在时）
JSON=$(ls outputs/gss_phase1_records_n200*_seed42_P0.json 2>/dev/null | head -1)
if [ -n "$JSON" ]; then
echo
echo "🎯 各 model 表现（基于 $(python3 -c "import json; print(len(set(r['respondent_id'] for r in json.load(open('$JSON')))))") respondents on P0）"
python3 << PY
import json, sys
sys.path.insert(0, 'src')
from gss_pipeline import format_eval_question, load_taxonomy

with open('$JSON') as f: records = json.load(f)
tx = load_taxonomy()
ranges = {}
for it in tx['primary_eval']['items']:
    _, meta = format_eval_question(it)
    codes = meta['valid_codes']
    ranges[it['id']] = (min(codes), max(codes))

stats = {}
for r in records:
    m = r['model']
    if m not in stats: stats[m] = {'ok':0, 'tot':0, 'nae':0.0}
    for item, samples in r['per_item_scores'].items():
        rng = ranges.get(item)
        if not rng or rng[1]==rng[0]: continue
        denom = rng[1]-rng[0]
        for s in samples:
            stats[m]['tot'] += 1
            if s.get('parse_fail'):
                stats[m]['nae'] += 1.0
            else:
                stats[m]['ok'] += 1
                if s.get('abs_err') is not None:
                    stats[m]['nae'] += s['abs_err']/denom
                elif s.get('cat_match') is not None:
                    stats[m]['nae'] += (1-s['cat_match'])/denom

print(f"   {'Model':<40s} {'Parse':>8s}  {'MAE_cons':>10s}")
print(f"   {'-'*40} {'-'*8}  {'-'*10}")
for m in sorted(stats.keys()):
    s = stats[m]
    rate = s['ok']/s['tot'] if s['tot'] else 0
    mae = s['nae']/s['tot'] if s['tot'] else 0
    dq1 = "✓" if rate >= 0.90 else "⚠️"
    print(f"   {m:<40s} {rate:>7.1%}{dq1}  {mae:>10.3f}")
print(f"\n   (majority baseline ~ 0.27 — MAE 低于 baseline 越多越好)")
PY
fi

echo
echo "═══════════════════════════════════════════"
echo "  快捷监控: tail -f outputs/phase1a_run.log"
echo "  进 tmux: tmux attach -t phase1a (Ctrl+B D 离开)"
echo "═══════════════════════════════════════════"
