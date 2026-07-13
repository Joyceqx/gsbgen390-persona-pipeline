#!/bin/bash
# Phase 1B 进度 + 健康检查（跑期间任何时候可用）
# Usage: bash scripts/check_phase1b.sh

cd "$(dirname "$0")/.."

echo "═══════════════════════════════════════════"
echo "  Phase 1B 状态 — $(date '+%a %b %d %H:%M')"
echo "═══════════════════════════════════════════"

# 1. 死活
if tmux ls 2>/dev/null | grep -q phase1b && ps aux | grep "src/gss_driver" | grep -v grep > /dev/null; then
  echo "✓ 还在跑"
else
  N_REC=$(python3 -c "import json; print(len(json.load(open('outputs/gss_phase1_records_n3309_random_seed42.json'))))" 2>/dev/null || echo 0)
  if [ "$N_REC" -ge 19854 ]; then
    echo "🎉 跑完了！$N_REC/19854 records"
  else
    echo "⚠️ 死了（$N_REC/19854 records）——看 outputs/phase1b_run.log 末尾 + 跑 bash scripts/launch_phase1b.sh 续上"
  fi
fi

# 2. 进度 + ETA
echo
echo "📊 进度 + ETA"
python3 << 'PY'
import re, json
from datetime import datetime, timedelta
try:
    with open('outputs/phase1b_run.log') as f:
        log = f.read()
    resp = re.findall(r'respondent (\d+)/3309', log)
    if resp:
        cur = int(resp[-1])
        print(f'   当前: respondent {cur}/3309 ({cur/3309*100:.1f}%)')
    speeds = re.findall(r'([\d.]+) respondents/min', log)
    if speeds and resp:
        spd = float(speeds[-1])
        remaining = (3309 - cur) / spd if spd > 0 else 0
        eta = datetime.now() + timedelta(minutes=remaining)
        print(f'   速度: {spd:.1f} resp/min → 剩余 ~{remaining/60:.1f} 小时')
        print(f'   ETA:  {eta.strftime("%a %b %d %H:%M")}')
except FileNotFoundError:
    print('   （还没有 log）')
PY

# 3. 记录健康
echo
echo "🏥 记录健康（parse/provider 错误）"
python3 << 'PY'
import json
try:
    d = json.load(open('outputs/gss_phase1_records_n3309_random_seed42.json'))
    n_ok = n_pf = n_pe = 0
    models = {}
    for r in d:
        models[r['model']] = models.get(r['model'], 0) + 1
        for samples in r['per_item_scores'].values():
            for s in samples:
                if s.get('skipped_missing_truth'):
                    continue
                et = s.get('error_type', 'ok')
                if et == 'ok': n_ok += 1
                elif et == 'parse_fail': n_pf += 1
                else: n_pe += 1
    tot = n_ok + n_pf + n_pe
    print(f'   records: {len(d)}/19854 | calls ok={n_ok} parse_fail={n_pf} provider_err={n_pe}' + (f' ({(n_pf+n_pe)/tot*100:.2f}% bad)' if tot else ''))
    print(f'   dispatch mix: ' + ', '.join(f"{m.split('/')[-1]}={c//6}" for m, c in sorted(models.items())))
except FileNotFoundError:
    print('   （还没有输出文件）')
PY

# 4. caffeinate + 电源
echo
echo "🔋 电源"
ps aux | grep "caffeinate -i -s" | grep -v grep > /dev/null && echo "   ✓ caffeinate 在运行" || echo "   ⚠️ caffeinate 不在了"
pmset -g batt | head -2 | tail -1 | sed 's/^/   /'
