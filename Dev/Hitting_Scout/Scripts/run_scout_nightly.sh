#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# run_scout_nightly.sh — Headless scheduled pipeline runner
#
# PURPOSE
# ───────
# Headless pipeline runner for manual testing or direct invocation.
# The actual nightly launchd schedule uses ~/Library/LaunchAgents/run_wcwaa_nightly.sh
# (a local wrapper that calls run_menu.py --all directly).
# This script can be used for manual headless runs without the interactive menu.
#
# HOW IT DIFFERS FROM run_scout.sh
# ─────────────────────────────────
# run_scout.sh             — for manual use; shows an interactive numbered menu
# run_scout_nightly.sh     — for manual headless use; no menu, no stdin needed
# run_wcwaa_nightly.sh     — for launchd (lives on local disk, not in repo)
#
# Both share the same underlying pipeline logic (run_menu.py run_pipeline).
# This script simply passes --all to skip the menu entirely.
#
# SCHEDULE
# ────────
# Configured to run at 10:00 AM EDT (14:00 UTC) daily via launchd.
# See: ../launchd/com.wcwaa.scout_pipeline.plist
#
# LOGS
# ────
# stdout + stderr from this wrapper go to:
#   Hitting_Scout/Logs/nightly_YYYYMMDD_HHMMSS.log
# Each pipeline script (scrape_gc_playbyplay, scrape_gc_boxscores, gen_hitting) also
# writes its own dated log to Logs/ as usual.
#
# MANUAL TEST RUN
# ───────────────
# To test this script runs cleanly without waiting for the scheduler:
#   cd .../Hitting_Scout/Scripts
#   bash run_scout_nightly.sh
# ─────────────────────────────────────────────────────────────────────────────

# Exit immediately if any command fails (so a scraper crash doesn't silently
# continue into gen_hitting.py with stale data).
# NOTE: set -e is intentionally NOT used here. The scrapers (Steps 1+2) handle
# their own per-game errors internally and log them. A single GC page timeout
# should not abort the entire pipeline and skip PDF generation (Step 3).
# Instead we capture exit codes and log warnings, then always proceed to Step 3.

# ── Resolve paths ────────────────────────────────────────────────────────────
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"
LOGS_DIR="$REPO_ROOT/Logs"
VENV_DIR="$REPO_ROOT/../venv"

# ── Set up log file for this wrapper ─────────────────────────────────────────
mkdir -p "$LOGS_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOGS_DIR/nightly_${STAMP}.log"

# Redirect all stdout and stderr from this point on to both the log file
# AND the terminal (tee). When run by launchd the terminal output goes to
# the StandardOutPath / StandardErrorPath defined in the plist.
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================================"
echo "  WCWAA Nightly Scout Pipeline"
echo "  Started: $(date)"
echo "  Log: $LOG_FILE"
echo "========================================================"

# ── Activate virtual environment ─────────────────────────────────────────────
# Playwright and ReportLab live in the venv — not in system Python.
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    echo "✅ venv activated: $VENV_DIR"
else
    echo "❌ ERROR: venv not found at $VENV_DIR"
    echo "   Recreate with: cd $REPO_ROOT && python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi

# ── Run the pipeline ──────────────────────────────────────────────────────────
# --all tells run_menu.py to skip the menu and run the full pipeline
# (all divisions, all teams). No stdin interaction required.
cd "$SCRIPTS_DIR"
python3 run_menu.py --all
PIPELINE_EXIT=$?
if [[ $PIPELINE_EXIT -ne 0 ]]; then
    echo ""
    echo "⚠️  WARNING: pipeline exited with code $PIPELINE_EXIT — check log for details"
fi

echo ""
echo "========================================================"
echo "  ✅ Nightly pipeline complete: $(date)"
echo "========================================================"
