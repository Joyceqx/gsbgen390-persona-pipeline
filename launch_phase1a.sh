#!/bin/bash
# Phase 1A paid launch script — single source of truth, copy-paste-safe.
# Usage: bash launch_phase1a.sh

set -e
cd "$(dirname "$0")"

echo "=== Pre-flight ==="
tmux kill-session -t phase1a 2>/dev/null && echo "  killed existing phase1a session" || echo "  no existing session"
sleep 1

echo "=== Launching panel F'' Phase 1A ==="
tmux new -d -s phase1a 'caffeinate -i -s python3 src/gss_driver.py --phase1a 2>&1 | tee -a outputs/phase1a_run.log'
sleep 30

echo "=== Verifying ==="
echo "[tmux session]"
tmux ls 2>&1 | head -1
echo "[python process]"
ps aux | grep gss_driver | grep -v grep | head -1
echo "[caffeinate]"
ps aux | grep "caffeinate -i -s python3" | grep -v grep | head -1
echo "[log head]"
tail -15 outputs/phase1a_run.log

echo
echo "=== If you see 'respondent 1/200' above + caffeinate process, you're good ==="
echo "To monitor: tail -f outputs/phase1a_run.log"
echo "To kill:    tmux kill-session -t phase1a"
