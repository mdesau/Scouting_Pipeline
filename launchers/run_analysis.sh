#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# run_analysis.sh — build all three analysis reports for a league division
#
# USAGE
#   bash launchers/run_analysis.sh                          # Minors, download new games first
#   bash launchers/run_analysis.sh --division Majors
#   bash launchers/run_analysis.sh --division Minors --no-scrape
# ─────────────────────────────────────────────────────────────────────────────

LAUNCHERS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$LAUNCHERS_DIR/.." && pwd)"
VENV_DIR="$REPO_ROOT/venv"

cd "$REPO_ROOT"

if [[ -f "$VENV_DIR/bin/activate" ]]; then
    source "$VENV_DIR/bin/activate"
else
    echo "⚠️  WARNING: venv not found at $VENV_DIR"
fi

python -c "import scout" 2>/dev/null || pip install -e "$REPO_ROOT"

python -m scout.analysis_tools.run_all "$@"
