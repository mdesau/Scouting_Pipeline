#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# run_scout_nightly.sh — Headless scheduled pipeline runner
#
# PURPOSE
# ───────
# Called by the macOS launchd scheduler (or any automated trigger) to run
# the full WCWAA scouting pipeline — all divisions, all teams — without
# showing the interactive menu.
#
# HOW IT DIFFERS FROM run_scout.sh
# ─────────────────────────────────
# run_scout.sh        — for manual use; shows an interactive numbered menu
# run_nightly_scout.sh — for automated/scheduled use; no menu, no stdin needed
#
# Both share the same underlying pipeline logic (interactive_menu.py run_pipeline).
# This script simply passes --all to skip the menu entirely.
#
# SCHEDULE
# ────────
# Configured to run at 10:00 PM EDT (02:00 UTC) nightly via launchd.
# See: ../launchd/com.wcwaa.scout_pipeline.plist
#
# LOGS
# ────
# stdout + stderr from this wrapper go to:
#   Scout_Development/Logs/nightly_YYYYMMDD_HHMMSS.log
# Each pipeline script (gc_scraper, scrape_box_scores, gen_reports) also
# writes its own dated log to Logs/ as usual.
#
# MANUAL TEST RUN
# ───────────────
# To test this script runs cleanly without waiting for the scheduler:
#   cd .../Scout_Development/Scripts
#   bash run_scout_nightly.sh
# ─────────────────────────────────────────────────────────────────────────────

# Exit immediately if any command fails (so a scraper crash doesn't silently
# continue into gen_reports.py with stale data).
set -e

# ── Resolve paths ────────────────────────────────────────────────────────────
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"
LOGS_DIR="$REPO_ROOT/Logs"
VENV_DIR="$REPO_ROOT/venv"

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
# --all tells interactive_menu.py to skip the menu and run the full pipeline
# (all divisions, all teams). No stdin interaction required.
cd "$SCRIPTS_DIR"
python3 interactive_menu.py --all

echo ""
echo "========================================================"
echo "  ✅ Nightly pipeline complete: $(date)"
echo "========================================================"
