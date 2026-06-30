#!/bin/bash
# =============================================================================
# Start Scout.command — double-click launcher for the WCWAA Scout web UI
# -----------------------------------------------------------------------------
# WHAT IT DOES
#   1. Activates the project virtualenv (venv).
#   2. Starts the local web server (src/web/server.py).
#   3. Opens the UI in your default browser.
#   4. Keeps running until you close the window or press Ctrl+C, which stops
#      the server (reports can only be built while this window is open).
#
# WHY A .command FILE
#   macOS runs .command files in Terminal when double-clicked, so there is no
#   typing required — just double-click this file in Finder to launch the app.
#
# NOTE
#   The very first launch on a brand-new Mac needs the venv + Playwright set up
#   (see README). On this Mac everything is already installed.
# =============================================================================

# Resolve paths relative to this script so it works no matter where it lives.
LAUNCHERS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$LAUNCHERS_DIR/.." && pwd)"
VENV_DIR="$REPO_ROOT/venv"
PORT="${SCOUT_WEB_PORT:-5050}"
URL="http://127.0.0.1:${PORT}"

cd "$REPO_ROOT"

echo "=========================================================="
echo "  WCWAA Scout — starting local web UI"
echo "  Repo: $REPO_ROOT"
echo "=========================================================="

# Activate the virtualenv (contains Flask, Playwright, ReportLab, etc.).
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    source "$VENV_DIR/bin/activate"
else
    echo "⚠️  venv not found at $VENV_DIR"
    echo "    Run the one-time setup first (see README.md)."
    read -r -p "Press Enter to close…"
    exit 1
fi

# Open the browser a moment after the server starts listening.
# Done in a backgrounded subshell so it does not block server startup.
( sleep 1.5; open "$URL" ) &

# Start the server in the foreground. Closing this window / Ctrl+C stops it.
echo "Opening $URL …"
echo "(Close this window or press Ctrl+C to stop the server.)"
python3 src/web/server.py
