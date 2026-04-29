#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# run_scout.sh — WCWAA 2026 Spring  |  Pipeline launcher
#
# USAGE
# ─────
# Interactive mode (shows a menu — pick division, team, or run everything):
#   bash run_scout.sh
#
# CLI mode (skip menu — run directly with flags, same as before):
#   bash run_scout.sh --division Wild
#   bash run_scout.sh --division Majors --team "Cubs-Holtzer"
#
# First time / session expired:
#   python3 scrape_gc_playbyplay.py --login
#
# WHAT THIS SCRIPT DOES
# ─────────────────────
# 1. Activates the project virtual environment (Scout_Development/venv/)
#    — required for Playwright (scraping) and ReportLab (PDF generation).
# 2. Hands control to run_menu.py, which:
#    — Shows an interactive numbered menu when called with no arguments
#    — Passes CLI flags straight through to the pipeline when arguments are given
#
# WHY A PYTHON SCRIPT HANDLES THE MENU (not bash):
#   The menu needs to know all team names to build the numbered lists.
#   Those names live in scrape_gc_playbyplay.py's DIVISIONS dict. Python can import
#   that dict directly — no duplication. Bash cannot. Keeping one source
#   of truth (DRY principle) means adding a team in scrape_gc_playbyplay.py
#   automatically updates the menu with zero extra work.
# ─────────────────────────────────────────────────────────────────────────────

# Navigate to Scripts/ so all python3 calls find scrape_gc_playbyplay.py etc.
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPTS_DIR"

# ── Activate the project virtual environment ──────────────────────────────
# The venv lives one level up from Scripts/ (Scout_Development/venv/).
# Playwright and ReportLab are installed there — NOT in system Python.
VENV_DIR="$SCRIPTS_DIR/../venv"
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
else
    echo "⚠️  WARNING: venv not found at $VENV_DIR"
    echo "   Recreate it with:"
    echo "   cd Scout_Development && python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    echo "   Continuing with system Python — scripts may fail if Playwright/ReportLab missing."
fi

# ── Hand off to the Python menu / pipeline runner ─────────────────────────
# "$@" passes any CLI arguments through unchanged.
# With no arguments → interactive menu is shown.
# With arguments (e.g. --division Wild) → menu is skipped, pipeline runs directly.
python3 run_menu.py "$@"
