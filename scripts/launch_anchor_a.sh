#!/bin/bash
# Anchor A: GPT-4o + R1 OFF (Park-exact protocol)
# Usage: bash launch_anchor_a.sh

set -e
cd "$(dirname "$0")/.."

echo "=== Killing existing anchor_a session if any ==="
tmux kill-session -t anchor_a 2>/dev/null && echo "  killed" || echo "  none"
sleep 1
rm -f outputs/anchor_a_run.log outputs/anchor_r1off_n100.json

echo "=== Launching anchor_a: GPT-4o + R1 OFF + primary-only + N=100 ==="
tmux new -d -s anchor_a 'caffeinate -i -s python3 src/gss_driver_anchor.py --phase1b-anchor --primary-only --no-r1-exclusion --out outputs/anchor_r1off_n100.json 2>&1 | tee outputs/anchor_a_run.log'

sleep 20

echo "=== Verifying ==="
tmux ls 2>&1 | head -5
echo
echo "[anchor_a python args — should show --no-r1-exclusion + --out anchor_r1off_n100.json]"
ps aux | grep "anchor_r1off" | grep -v grep | head -1
echo
echo "[log head]"
tail -10 outputs/anchor_a_run.log

echo
echo "=== Done. Look for 'R1 battery exclusion = OFF (Park-exact)' in log above. ==="
