#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# run_pitching_nightly.sh — Headless scheduled Pitching Savant runner
#
# PURPOSE
# ───────
# Called by launchd (or run_scout_nightly.sh) to regenerate all pitching PDFs
# without user interaction. Logs to Pitching_Savant/Logs/.
#
# MANUAL TEST
# ───────────
#   cd .../Pitching_Savant/Scripts && bash run_pitching_nightly.sh
# ─────────────────────────────────────────────────────────────────────────────

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"
LOGS_DIR="$REPO_ROOT/Logs"
VENV_DIR="$(cd "$SCRIPTS_DIR/../../Scout_Development/venv" 2>/dev/null && pwd)"

# ── Log file ─────────────────────────────────────────────────────────────────
mkdir -p "$LOGS_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOGS_DIR/nightly_pitching_${STAMP}.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================================"
echo "  Pitching Savant — Nightly Run"
echo "  Started: $(date)"
echo "  Log: $LOG_FILE"
echo "========================================================"

# ── Activate venv ────────────────────────────────────────────────────────────
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    echo "✅ venv activated: $VENV_DIR"
else
    echo "❌ ERROR: venv not found at $VENV_DIR"
    exit 1
fi

# ── Run all divisions ────────────────────────────────────────────────────────
cd "$SCRIPTS_DIR"
python3 gen_pitching.py --division all
EXIT_CODE=$?

echo ""
echo "========================================================"
echo "  ✅ Pitching Savant nightly complete: $(date)"
echo "========================================================"
exit $EXIT_CODE
