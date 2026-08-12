#!/bin/bash
# run_pitching_nightly.sh — Headless Pitching Savant runner

LAUNCHERS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$LAUNCHERS_DIR/.." && pwd)"
LOGS_DIR="$REPO_ROOT/data/real/logs"
VENV_DIR="$REPO_ROOT/venv"

mkdir -p "$LOGS_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOGS_DIR/nightly_pitching_${STAMP}.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================================"
echo "  Pitching Savant — Nightly Run"
echo "  Started: $(date)"
echo "========================================================"

if [[ -f "$VENV_DIR/bin/activate" ]]; then
    source "$VENV_DIR/bin/activate"
    echo "✅ venv activated"
else
    echo "❌ ERROR: venv not found at $VENV_DIR"; exit 1
fi

cd "$REPO_ROOT"
python -c "import scout" 2>/dev/null || pip install -e "$REPO_ROOT"
python -m scout.pitching.gen_pitching --division all
EXIT_CODE=$?
echo "========================================================"
echo "  ✅ Pitching Savant nightly complete: $(date)"
echo "========================================================"
exit $EXIT_CODE
