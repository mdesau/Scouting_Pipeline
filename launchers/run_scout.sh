#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# run_scout.sh — WCWAA Scout Pipeline launcher
#
# USAGE
# ─────
# Interactive mode (shows a menu — pick division, team, or run everything):
#   bash launchers/run_scout.sh
#
# CLI mode (skip menu — run directly with flags):
#   bash launchers/run_scout.sh --division Wild
#   bash launchers/run_scout.sh --division Majors --team "Cubs-Holtzer"
#
# First time / session expired:
#   python -m scout.scraping.scrape_gc_playbyplay --login
#
# WHAT THIS SCRIPT DOES
# ─────────────────────
# 1. Activates the project virtual environment (venv/ at repo root)
# 2. Hands control to run_menu.py, which:
#    — Shows an interactive numbered menu when called with no arguments
#    — Passes CLI flags straight through to the pipeline when arguments are given
#
# WHY A PYTHON SCRIPT HANDLES THE MENU (not bash):
#   The menu needs team names which come from the YAML config. Python can load
#   that config directly via season_config.py. Bash cannot. This keeps one
#   source of truth (DRY principle) — adding a team to the YAML automatically
#   updates the menu with zero extra work.
# ─────────────────────────────────────────────────────────────────────────────

# Resolve paths — launchers/ sits one level below Scout/ (repo root)
LAUNCHERS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$LAUNCHERS_DIR/.." && pwd)"

# Navigate to repo root so relative imports in Python scripts resolve correctly
cd "$REPO_ROOT"

# ── Activate the project virtual environment ──────────────────────────────
# The venv lives at the repo root (Scout/venv/) — shared across all components.
VENV_DIR="$REPO_ROOT/venv"
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
else
    echo "⚠️  WARNING: venv not found at $VENV_DIR"
    echo "   Recreate it with:"
    echo "   python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    echo "   Continuing with system Python — scripts may fail if Playwright/ReportLab missing."
fi

# ── Ensure the scout package is importable (one-time editable install) ────
python -c "import scout" 2>/dev/null || pip install -e "$REPO_ROOT"

# ── Hand off to the Python menu / pipeline runner ─────────────────────
python -m scout.orchestrator.run_menu "$@"
