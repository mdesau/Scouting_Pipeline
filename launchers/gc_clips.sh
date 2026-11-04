#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# gc_clips.sh — download GameChanger video clips (whole games or share links) + montage
#
# USAGE (quote every URL — they contain & characters)
#   bash launchers/gc_clips.sh "https://web.gc.com/teams/.../schedule/<game>/videos/clips"
#   bash launchers/gc_clips.sh "<game link>" --player Harper --montage "Harper Nov 3"
#   bash launchers/gc_clips.sh "<game link>" --list          # preview only
#   bash launchers/gc_clips.sh "https://web.gc.com/.../videos/clips/<id>?token=..."
#   bash launchers/gc_clips.sh --help
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

python -m scout.video.gc_clips "$@"
