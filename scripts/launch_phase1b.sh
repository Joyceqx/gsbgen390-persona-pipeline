#!/bin/bash
# Phase 1B paid launch script — Random × P1, N=3,309, 6 conditions (~$87, 3-7 days).
# Cell locked per RESEARCH_DESIGN.md §7.1 (Bayati 2026-07-12).
# Usage: bash scripts/launch_phase1b.sh
# Resumable: rerun this script to continue after any interruption.
# NOTE: if interrupted within the first ~165 respondents (<992 records), the
# partial-resume guard refuses a plain rerun. Do NOT delete the JSON (those
# records are paid) — resume manually with:
#   tmux new -d -s phase1b 'caffeinate -i -s python3 src/gss_driver.py \
#     --phase1b --phase1b-model random --phase1b-prompt P1 \
#     --force-resume-partial 2>&1 | tee -a outputs/phase1b_run.log'
# Past 992 records, rerunning this script resumes automatically.

set -e
cd "$(dirname "$0")/.."

echo "=== Pre-flight ==="
tmux kill-session -t phase1b 2>/dev/null && echo "  killed existing phase1b session" || echo "  no existing session"
sleep 1

echo "=== Launching Phase 1B (random dispatch × P1 × 6 conditions) ==="
# caffeinate -i -s: prevent idle + system sleep while the run lives
# (system sleep prevention requires AC power — keep the charger plugged in).
tmux new -d -s phase1b 'caffeinate -i -s python3 src/gss_driver.py --phase1b --phase1b-model random --phase1b-prompt P1 2>&1 | tee -a outputs/phase1b_run.log'
sleep 30

echo "=== Verifying ==="
echo "[tmux session]"
tmux ls 2>&1 | head -2
echo "[python process]"
ps aux | grep gss_driver | grep -v grep | head -1
echo "[caffeinate]"
ps aux | grep "caffeinate -i -s python3" | grep -v grep | head -1
echo "[log tail]"
tail -15 outputs/phase1b_run.log

echo
echo "=== If you see 'respondent 1/3309' above + caffeinate process, you're good ==="
echo "Monitor:  bash scripts/check_phase1b.sh   (progress + ETA + health)"
echo "Or:       tail -f outputs/phase1b_run.log"
echo "Kill:     tmux kill-session -t phase1b"
echo
echo "IMPORTANT while it runs:"
echo "  - Keep the charger plugged in (caffeinate -s only works on AC power)"
echo "  - Do NOT close the lid (lid-close sleeps the Mac regardless of caffeinate)"
echo "    → Screen can be dimmed/off; just leave the lid open"
echo "  - Keep WiFi on; do not shut down"
