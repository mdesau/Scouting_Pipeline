#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# run_pitching.sh — Pitching Savant standalone launcher
#
# USAGE
# ─────
# Run all four divisions:
#   bash run_pitching.sh
#
# Run a single division:
#   bash run_pitching.sh --division Wild
#
# Run a single team within a division:
#   bash run_pitching.sh --division Wild --team "Weddington Wild 11U"
# ─────────────────────────────────────────────────────────────────────────────

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPTS_DIR"

# ── Activate shared venv (lives in Scout_Development) ─────────────────────
VENV_DIR="$(cd "$SCRIPTS_DIR/../../Scout_Development/venv" 2>/dev/null && pwd)"
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
else
    echo "⚠️  WARNING: venv not found at $VENV_DIR"
    echo "   Continuing with system Python — may fail if ReportLab is missing."
fi

# ── Run gen_pitching.py ───────────────────────────────────────────────────
if [[ $# -eq 0 ]]; then
    # No args → run all divisions
    for div in Majors Minors Wild Storm; do
        python3 gen_pitching.py --division "$div"
    done
else
    python3 gen_pitching.py "$@"
fi
