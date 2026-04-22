#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# run_weekly.sh — WCWAA 2026 Spring  |  Full pipeline, one command
#
# Run this from the Scripts folder after each game week:
#   cd ~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My\ Drive/Baseball/WCWAA/2026/Spring/Scout_Development/Scripts
#   bash run_weekly.sh
#
# What it does (in order):
#   1. Scrape all new FINAL play-by-play files from GameChanger (all 4 divisions)
#   2. Update Majors rosters.json with first names + jersey numbers
#   3. Regenerate all scouting report PDFs (Majors, Minors, Wild, Storm)
#
# Notes:
#   - Step 1 skips games that already have a .txt or -Reviewed.txt file (safe to re-run)
#   - Step 2 requires Playwright; run gc_scraper.py --login once if session has expired
#   - Minors jersey numbers are unavailable (GC box score pages redirect to /info)
#   - Wild/Storm jersey numbers come from roster.txt files (built by scrape_box_scores.py)
# ─────────────────────────────────────────────────────────────────────────────

set -e  # Stop on first error

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPTS_DIR"

# ── Activate the project virtual environment ──────────────
# WHY: The venv at Scout_Development/venv/ holds Playwright and ReportLab.
# Without activating it, bare `python3` points at macOS system Python where
# neither package is installed, and every script will crash with ImportError.
# The venv lives one directory up from Scripts/ (i.e., alongside CLAUDE.md).
VENV_DIR="$SCRIPTS_DIR/../venv"
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    echo "✅ Virtual environment activated: $VENV_DIR"
else
    echo "⚠️  WARNING: venv not found at $VENV_DIR"
    echo "   Run this from Scout_Development/ to set it up:"
    echo "   python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    echo "   Continuing with system Python — scripts may fail."
fi

echo ""
echo "======================================================"
echo "  WCWAA 2026 Spring — Weekly Pipeline"
echo "======================================================"
echo ""

# ── Step 1: Scrape new play-by-play files ─────────────────
echo "▶ Step 1/3: Scraping new games from GameChanger..."
python3 gc_scraper.py
echo ""

# ── Step 2: Update rosters + jersey numbers ───────────────
echo "▶ Step 2/3: Updating rosters (Majors jersey numbers + Wild/Storm roster.txt)..."
python3 scrape_box_scores.py
echo ""

# ── Step 3: Regenerate all PDFs ───────────────────────────
echo "▶ Step 3/3: Generating scouting report PDFs..."

echo "  → Majors"
python3 gen_reports.py --division Majors

echo "  → Minors"
python3 gen_reports.py --division Minors

echo "  → Wild"
python3 gen_reports.py --division Wild

echo "  → Storm"
python3 gen_reports.py --division Storm

echo ""
echo "======================================================"
echo "  Done. PDFs saved to:"
echo "  Majors:  Spring/Majors/Reports/Scouting_Reports/"
echo "  Minors:  Spring/Minors/Reports/Scouting_Reports/"
echo "  Wild:    Spring/Wild/[TeamName]/"
echo "  Storm:   Spring/Storm/[TeamName]/"
echo "======================================================"
echo ""
