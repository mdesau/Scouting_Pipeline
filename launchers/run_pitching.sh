#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# run_pitching.sh — Pitching Savant standalone launcher
#
# USAGE
# ─────
# Run all four divisions:
#   bash launchers/run_pitching.sh
#
# Run a single division:
#   bash launchers/run_pitching.sh --division Wild
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

# Ensure the scout package is importable (one-time editable install).
python -c "import scout" 2>/dev/null || pip install -e "$REPO_ROOT"

if [[ $# -eq 0 ]]; then
    for div in Majors Minors Wild Storm; do
        python -m scout.pitching.gen_pitching --division "$div"
    done
else
    python -m scout.pitching.gen_pitching "$@"
fi
