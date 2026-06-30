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

if [[ $# -eq 0 ]]; then
    for div in Majors Minors Wild Storm; do
        python3 src/pitching/gen_pitching.py --division "$div"
    done
else
    python3 src/pitching/gen_pitching.py "$@"
fi
