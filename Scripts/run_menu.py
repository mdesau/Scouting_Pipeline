#!/usr/bin/env python3
"""
run_menu.py — Interactive pipeline launcher for WCWAA Scout Pipeline
=============================================================================

WORKFLOW SUMMARY
────────────────
This script is called by run_scout.sh every time the pipeline is launched.
It behaves in one of two modes:

  MODE 1 — CLI passthrough (when args are supplied):
    run_scout.sh --division Wild --team "QC Flight Baseball 11U"
    → Skips the menu entirely. Args are passed straight through to the
      underlying scripts, preserving the power-user / cron-job workflow.

  MODE 2 — Interactive menu (when no args are supplied):
    run_scout.sh
    → Displays a numbered menu. User picks a scope, then the script
      calls scrape_gc_playbyplay.py, scrape_gc_boxscores.py, and gen_reports.py
      via subprocess with the correct --division / --team flags.

MENU OPTIONS
────────────
  [0] Full pipeline — all divisions, all teams (default — press ENTER)
  [1] Single division — all teams in one division
  [2] Single team — drill down: pick division → pick team
  [3] Add a new Wild / Storm opponent to the pipeline
  [Q] Quit

WHY SUBPROCESS INSTEAD OF IMPORT + CALL?
─────────────────────────────────────────
Each script (scrape_gc_playbyplay.py, scrape_gc_boxscores.py, gen_reports.py) configures
its own argparse and logging. Calling them as subprocesses:
  - Keeps their stdout/stderr streaming live to the terminal (user sees progress)
  - Avoids logging config conflicts between scripts
  - Exactly mirrors what the user would see running each script manually
  - Makes it easy to add new scripts to the pipeline in the future

HOW "ADD NEW TEAM" WORKS
────────────────────────
  1. User pastes a GC schedule URL.
  2. Script parses team_id and slug from the URL.
  3. Script suggests a folder name (derived from slug); user confirms or edits.
  4. User picks Wild or Storm.
  5. Script inserts one line into DIVISIONS in scrape_gc_playbyplay.py and
     scrape_gc_boxscores.py (both files updated atomically).
  6. Script creates Wild/<TeamName>/Games/ or Storm/<TeamName>/Games/.
  7. User is reminded to verify the folder name after the first game is scraped
     (folder name MUST match GC's inning header spelling exactly).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
# Scripts/ directory — where this file lives and where all scripts are located
SCRIPTS_DIR = Path(__file__).parent

# Spring/ directory — parent of Scout_Development/; holds Majors/, Minors/, Wild/, Storm/
SPRING_DIR = Path(
    "~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com"
    "/My Drive/Baseball/WCWAA/2026/Spring"
).expanduser()

# Session file written by scrape_gc_playbyplay.py --login
SESSION_FILE = SCRIPTS_DIR / "gc_session.json"

# Rosters for Majors/Minors (keyed by team name like "Cubs-Holtzer")
MAJORS_ROSTER = SPRING_DIR / "Majors" / "Reports" / "rosters.json"
MINORS_ROSTER = SPRING_DIR / "Minors" / "Reports" / "rosters.json"

# ── Import DIVISIONS from scrape_gc_playbyplay ───────────────────────────────────────
# WHY: We import the live DIVISIONS dict rather than duplicating it here.
# This means adding a team to scrape_gc_playbyplay.py automatically updates the menu —
# no second place to edit. This is the DRY principle in action.
try:
    from scrape_gc_playbyplay import DIVISIONS
except ImportError:
    print("ERROR: Could not import DIVISIONS from scrape_gc_playbyplay.py.")
    print("Make sure you are running this from the Scripts/ directory.")
    sys.exit(1)


# ════════════════════════════════════════════════════════════════════════════
# HELPER UTILITIES
# ════════════════════════════════════════════════════════════════════════════

__version__ = "2.1.0"

def print_header():
    """Print the pipeline banner shown at the top of every menu screen."""
    print()
    print("=" * 58)
    print("  WCWAA 2026 Spring — Scouting Pipeline")
    print(f"  v{__version__}")
    print("=" * 58)
    print()


def check_session():
    """
    Warn the user if gc_session.json is missing.

    The session file holds GC login cookies saved by scrape_gc_playbyplay.py --login.
    Without it, both scrape_gc_playbyplay.py and scrape_gc_boxscores.py will fail
    immediately with an authentication error.

    We warn here (before showing the menu) so the user can fix it upfront
    rather than waiting through menu navigation only to hit an error.
    """
    if not SESSION_FILE.exists():
        print("⚠️  WARNING: gc_session.json not found.")
        print("   The scraper needs a saved GameChanger login session.")
        print("   Run this first, then re-launch:")
        print("     python3 scrape_gc_playbyplay.py --login")
        print()


def ask(prompt, default=None):
    """
    Prompt the user for input, returning default if they just press ENTER.

    Args:
        prompt:  The question to display (no trailing space needed).
        default: Value to return if user presses ENTER with no input.

    Returns:
        Stripped string entered by user, or default if blank.
    """
    try:
        response = input(prompt).strip()
        return response if response else default
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C or Ctrl+D — exit cleanly
        print("\n\nAborted.")
        sys.exit(0)


def pick_from_list(title, options):
    """
    Display a numbered list and return the user's chosen item.

    Args:
        title:   Heading text printed above the list.
        options: List of strings to display and choose from.

    Returns:
        The chosen string from options, or None if the user quits.

    Example:
        pick_from_list("Select a division:", ["Majors", "Minors", "Wild", "Storm"])
        → prints [1] Majors  [2] Minors  [3] Wild  [4] Storm
        → user types "2" → returns "Minors"
    """
    print(title)
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    print()

    while True:
        raw = ask("Choice (or Q to quit): ")
        if raw is None or raw.upper() == "Q":
            return None
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx]
        print(f"  Please enter a number between 1 and {len(options)}, or Q.")


def get_team_list(division):
    """
    Return the list of team names for a given division.

    For Wild/Storm: reads the tuples from DIVISIONS (team_id, slug, name).
    For Majors/Minors: reads the keys from rosters.json so the list stays
    current without any extra configuration.

    Args:
        division: One of "Majors", "Minors", "Wild", "Storm".

    Returns:
        List of team name strings, or [] if none found.
    """
    if division in ("Wild", "Storm"):
        # Each entry is a (team_id, slug, display_name) tuple
        return [name for (_, _, name) in DIVISIONS[division].get("teams", [])]

    # Majors / Minors — read team keys from rosters.json
    roster_path = MAJORS_ROSTER if division == "Majors" else MINORS_ROSTER
    if not roster_path.exists():
        print(f"  ⚠️  {roster_path} not found — run scrape_gc_boxscores.py first.")
        return []
    with open(roster_path, encoding="utf-8") as f:
        data = json.load(f)
    # rosters.json keys are team names (e.g. "Cubs-Holtzer"); skip internal keys
    return sorted(k for k in data.keys() if not k.startswith("_"))


# ════════════════════════════════════════════════════════════════════════════
# PIPELINE EXECUTION
# ════════════════════════════════════════════════════════════════════════════

def run_pipeline(division=None, team=None):
    """
    Execute the full 3-step pipeline for the given scope.

    Steps:
      1. scrape_gc_playbyplay.py — scrape new game files from GameChanger
      2. scrape_gc_boxscores.py  — update rosters.json / roster.txt
      3. gen_reports.py       — regenerate PDFs

    Step 1 skips games that already have a .txt or -Reviewed.txt on disk,
    so re-running is always safe — only genuinely new games are scraped.

    Args:
        division: Division name string, or None for all divisions.
        team:     Team name string, or None for all teams in division.
    """
    # Build the --division and --team flags for each script call
    # WHY list(filter(None, [...])):  Python's clean way to build an arg list
    # that omits items when they are None (no flag added if no filter needed).
    div_args  = ["--division", division] if division else []
    team_args = ["--team",     team]     if team     else []

    # Step 1: Scrape new game files
    # gen_reports.py accepts --team natively; scrape_gc_playbyplay uses it as a name filter
    print()
    print("─" * 58)
    scope = f"{division or 'ALL'}" + (f" → {team}" if team else " (all teams)")
    print(f"▶ Step 1/3  Scrape new games  [{scope}]")
    print("─" * 58)
    _run(["python3", "scrape_gc_playbyplay.py"] + div_args + team_args)

    # Step 2: Update rosters
    # --team is now supported by scrape_gc_boxscores.py for Wild/Storm team-based divisions.
    # For Majors/Minors (org-based), --team is ignored — the full division roster JSON
    # is always updated together since all teams share one file.
    print()
    print("─" * 58)
    print(f"▶ Step 2/3  Update rosters    [{scope}]")
    print("─" * 58)
    _run(["python3", "scrape_gc_boxscores.py"] + div_args + team_args)

    # Step 3: Generate PDFs
    # For single-team runs, pass --team so only that PDF is regenerated (fast).
    # For all-team runs, iterate each division explicitly.
    print()
    print("─" * 58)
    print(f"▶ Step 3/3  Generate PDFs     [{scope}]")
    print("─" * 58)

    if division:
        _run(["python3", "gen_reports.py", "--division", division] + team_args)
    else:
        # No division filter → run all four divisions
        for div in ["Majors", "Minors", "Wild", "Storm"]:
            print(f"  → {div}")
            _run(["python3", "gen_reports.py", "--division", div])

    print()
    print("=" * 58)
    print("  ✅ Pipeline complete.")
    print(f"  Scope: {scope}")
    print("=" * 58)
    print()


def _run(cmd):
    """
    Run a subprocess command from the Scripts/ directory.

    Uses subprocess.run() rather than os.system() because:
      - We get a return code we can check
      - stdout/stderr stream live (user sees progress in real time)
      - Shell injection is not possible (args are a list, not a string)

    Args:
        cmd: List of command + arguments, e.g. ["python3", "scrape_gc_playbyplay.py", "--division", "Wild"]

    Raises:
        SystemExit if the command returns a non-zero exit code.
    """
    result = subprocess.run(cmd, cwd=str(SCRIPTS_DIR))
    if result.returncode != 0:
        print(f"\n⚠️  Command failed with exit code {result.returncode}: {' '.join(cmd)}")
        print("   Check the output above for error details.")
        print("   The pipeline has stopped. Fix the issue and re-run.")
        sys.exit(result.returncode)


# ════════════════════════════════════════════════════════════════════════════
# ADD NEW TEAM FEATURE
# ════════════════════════════════════════════════════════════════════════════

def _parse_gc_url(url):
    """
    Extract team_id and slug from a GameChanger schedule URL.

    GC schedule URLs follow this exact format:
      https://web.gc.com/teams/{team_id}/{slug}/schedule

    Args:
        url: Full GC schedule URL string.

    Returns:
        (team_id, slug) tuple, or (None, None) if parsing fails.

    Example:
        Input:  "https://web.gc.com/teams/Wn2Abf32IXOz/2026-summer-sba-alabama-national-12u/schedule"
        Output: ("Wn2Abf32IXOz", "2026-summer-sba-alabama-national-12u")
    """
    # Regex: match the two path segments between /teams/ and /schedule
    match = re.search(r"/teams/([^/]+)/([^/]+)/schedule", url)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def _slug_to_folder_name(slug):
    """
    Convert a GC slug to a suggested folder name.

    GC slugs look like: "2026-summer-sba-alabama-national-12u"
    We strip the leading year-season prefix and title-case the rest.

    Args:
        slug: GC URL slug string.

    Returns:
        Suggested folder name string.

    Example:
        "2026-summer-sba-alabama-national-12u" → "SBA Alabama National 12U"
        "2026-spring-qc-flight-baseball-11u"   → "QC Flight Baseball 11U"

    Note:
        Short alpha words (<=3 chars) are uppercased as likely acronyms (QC, SBA, TN).
        4-char acronyms like "ITAA" will come out title-cased ("Itaa") — the
        user is always prompted to confirm or edit the name before it is used.
    """
    # Remove leading YYYY-season- prefix (e.g. "2026-summer-", "2026-spring-")
    cleaned = re.sub(r"^\d{4}-(?:spring|summer|fall|winter)-", "", slug)
    # Replace hyphens with spaces and title-case each word
    words = cleaned.replace("-", " ").split()
    # Uppercase common abbreviations; title-case everything else
    result = []
    for word in words:
        # Keep known uppercase patterns: 12U, 11U, 9U, QC, SBA, TN, SC, etc.
        if re.match(r"^\d+[uU]$", word):          # age groups like 12u → 12U
            result.append(word.upper())
        elif len(word) <= 3 and word.isalpha():   # short words → uppercase (QC, SBA, TN)
            result.append(word.upper())
        else:
            result.append(word.title())
    return " ".join(result)


def _insert_team_into_file(filepath, division, team_id, slug, folder_name):
    """
    Insert a new team tuple into the DIVISIONS dict in a Python source file.

    Finds the closing bracket of the correct division's teams list and
    inserts the new tuple on the line just before it.

    This works by finding a unique anchor string in the file — the line
    that immediately follows the teams list closing bracket. Because each
    division's anchor is unique, the replacement is unambiguous.

    Args:
        filepath:    Path to the Python file to modify.
        division:    "Wild" or "Storm" — which section to insert into.
        team_id:     GC team ID string.
        slug:        GC URL slug string.
        folder_name: Exact folder name for the team directory.

    Returns:
        True if insertion was successful, False otherwise.
    """
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    # New tuple line (12 spaces indent to match existing tuples)
    new_line = f'            ("{team_id}", "{slug}", "{folder_name}"),'

    # Each file has slightly different structure after the teams list,
    # so we need different anchor strings for each file.
    filename = Path(filepath).name

    if filename == "scrape_gc_playbyplay.py":
        anchors = {
            "Wild":  '        ],\n        "output_base": SPRING_DIR / "Wild",',
            "Storm": '        ],\n        "output_base": SPRING_DIR / "Storm",',
        }
    else:  # scrape_gc_boxscores.py
        anchors = {
            "Wild":  '        ],\n    },\n    # \u2500\u2500 Storm opponents',
            "Storm": '        ],\n    },\n}',
        }

    anchor = anchors.get(division)
    if not anchor or anchor not in content:
        print(f"  ⚠️  Could not find insertion point in {filename}.")
        print(f"     Please add this line manually to the {division} teams list:")
        print(f"     {new_line}")
        return False

    # Replace anchor with: new_line + newline + anchor
    new_content = content.replace(anchor, f"{new_line}\n{anchor}", 1)

    # Write to a backup before overwriting (safety net)
    backup = Path(filepath).with_suffix(".py.bak")
    with open(backup, "w", encoding="utf-8") as f:
        f.write(content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def add_new_team():
    """
    Interactive flow to add a new Wild or Storm opponent to the pipeline.

    Steps:
      1. Paste a GC schedule URL → auto-parse team_id and slug
      2. Confirm or edit the suggested folder name
      3. Choose Wild or Storm division
      4. Insert into scrape_gc_playbyplay.py and scrape_gc_boxscores.py
      5. Create the Games/ folder structure on disk
      6. Print reminder about verifying folder name after first scrape

    IMPORTANT NOTE ON FOLDER NAMES:
    The folder name MUST match the team name as GameChanger writes it in the
    inning headers of game files (e.g. "===Top 1st - SBA Alabama National 12U===").
    The suggested name is a best guess from the URL slug. Always open the first
    scraped game file and verify the inning header spelling before relying on
    the PDF output.
    """
    print("\n── Add a New Wild / Storm Opponent ──────────────────────")
    print("Paste the team's GameChanger schedule URL and press ENTER.")
    print("URL format: https://web.gc.com/teams/{team_id}/{slug}/schedule")
    print()

    url = ask("Schedule URL: ")
    if not url:
        print("  No URL entered — returning to menu.")
        return

    team_id, slug = _parse_gc_url(url)
    if not team_id:
        print("  ⚠️  Could not parse team_id and slug from that URL.")
        print("     Expected format: https://web.gc.com/teams/{team_id}/{slug}/schedule")
        return

    suggested_name = _slug_to_folder_name(slug)

    print()
    print(f"  Parsed:  team_id = {team_id}")
    print(f"           slug    = {slug}")
    print(f"  Suggested folder name: \"{suggested_name}\"")
    print()
    print("  ⚠️  The folder name MUST exactly match the team name in GC's inning")
    print("     headers. Verify by opening the first scraped game file and checking:")
    print("     ===Top 1st - <TeamName>===")
    print()

    folder_name = ask(f'Press ENTER to accept "{suggested_name}", or type a new name: ',
                      default=suggested_name)
    print()

    # Choose Wild or Storm
    division = pick_from_list("Add to which division?", ["Wild", "Storm"])
    if not division:
        print("  Cancelled.")
        return

    print()
    print(f"  Adding \"{folder_name}\" to {division}...")

    # Modify scrape_gc_playbyplay.py
    scraper_path = SCRIPTS_DIR / "scrape_gc_playbyplay.py"
    ok1 = _insert_team_into_file(scraper_path, division, team_id, slug, folder_name)

    # Modify scrape_gc_boxscores.py
    boxscore_path = SCRIPTS_DIR / "scrape_gc_boxscores.py"
    ok2 = _insert_team_into_file(boxscore_path, division, team_id, slug, folder_name)

    # Create folder structure
    team_dir = SPRING_DIR / division / folder_name / "Games"
    team_dir.mkdir(parents=True, exist_ok=True)

    if ok1 and ok2:
        print()
        print(f"  ✅ \"{folder_name}\" added to {division}.")
        print(f"     scrape_gc_playbyplay.py — updated (backup: scrape_gc_playbyplay.py.bak)")
        print(f"     scrape_gc_boxscores.py  — updated (backup: scrape_gc_boxscores.py.bak)")
        print(f"     Folder created: {division}/{folder_name}/Games/")
        print()
        print("  Next steps:")
        print("  1. Run the pipeline (option [0]) to scrape the first batch of games.")
        print(f"  2. Open a game file in {division}/{folder_name}/Games/")
        print("     and verify the team name in the inning header matches the folder name.")
        print("  3. If they differ, rename the folder (two-step to avoid macOS case bug):")
        print(f'       mv "{division}/{folder_name}" "{division}/tmp"')
        print(f'       mv "{division}/tmp" "{division}/<Corrected Name>"')
        print("     Then update the folder name in scrape_gc_playbyplay.py and scrape_gc_boxscores.py.")
    else:
        print()
        print("  ⚠️  Partial failure — check messages above and edit scripts manually.")


# ════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ════════════════════════════════════════════════════════════════════════════

def interactive_menu():
    """
    Display the main menu and route the user to the correct pipeline scope.

    The menu is shown when run_scout.sh is called with no arguments.
    Default action (pressing ENTER) is option [0] — full pipeline — which
    matches the original run_scout.sh behaviour so existing muscle memory works.
    """
    print_header()
    check_session()

    print("What would you like to run?\n")
    print("  [0] Full pipeline — ALL divisions, all teams  (default — press ENTER)")
    print("  [1] Single division — all teams")
    print("  [2] Single team")
    print("  [3] Add a new Wild / Storm opponent")
    print("  [Q] Quit")
    print()

    choice = ask("Choice [0]: ", default="0")

    if choice.upper() == "Q":
        print("Goodbye.")
        sys.exit(0)

    # ── [0] Full pipeline ────────────────────────────────────────────────────
    if choice == "0":
        print("\n▶ Running full pipeline for all divisions...")
        run_pipeline()

    # ── [1] Single division ──────────────────────────────────────────────────
    elif choice == "1":
        print()
        division = pick_from_list("Select a division:", ["Majors", "Minors", "Wild", "Storm"])
        if not division:
            return
        print(f"\n▶ Running full pipeline for {division} (all teams)...")
        run_pipeline(division=division)

    # ── [2] Single team ──────────────────────────────────────────────────────
    elif choice == "2":
        print()
        division = pick_from_list("Select a division:", ["Majors", "Minors", "Wild", "Storm"])
        if not division:
            return

        teams = get_team_list(division)
        if not teams:
            print(f"  No teams found for {division}. Check rosters.json or DIVISIONS config.")
            return

        print()
        team = pick_from_list(f"Select a team in {division}:", teams)
        if not team:
            return

        print(f"\n▶ Running full pipeline for {division} → {team}...")
        run_pipeline(division=division, team=team)

    # ── [3] Add new opponent ─────────────────────────────────────────────────
    elif choice == "3":
        add_new_team()

    else:
        print(f"  Unrecognised choice: '{choice}'. Please run again and enter 0–3 or Q.")
        sys.exit(1)


# ════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════

def main():
    """
    Entry point. Decides whether to show the menu or pass CLI args through.

    CLI passthrough mode:
      Any argument that looks like a script flag (starts with -- or is a known
      division name) triggers direct execution, skipping the menu.
      This preserves backwards compatibility with any scripts or habits that
      call run_scout.sh --division Wild etc.

    Interactive mode:
      No arguments → show the menu.
    """
    # sys.argv[0] is the script name; sys.argv[1:] are the user's arguments
    user_args = sys.argv[1:]

    if user_args:
        # ── CLI passthrough ──────────────────────────────────────────────────
        # Parse --division and --team from the passthrough args so we can call
        # run_pipeline() with the correct scope (which handles all 3 steps).
        #
        # Supported passthrough forms:
        #   --all                                    (headless full pipeline — used by run_nightly_scout.sh)
        #   --division Wild
        #   --division Wild --team "QC Flight Baseball 11U"
        #   --team "Cubs-Holtzer"   (division inferred as None → all divisions searched)
        division = None
        team = None

        # --all: explicit full-pipeline flag for headless/scheduled runs.
        # Skips the menu and runs all divisions with no filtering.
        if "--all" in user_args:
            print_header()
            print("▶ Headless mode — running full pipeline for ALL divisions")
            run_pipeline(division=None, team=None)
            return

        i = 0
        while i < len(user_args):
            if user_args[i] == "--division" and i + 1 < len(user_args):
                division = user_args[i + 1]
                i += 2
            elif user_args[i] == "--team" and i + 1 < len(user_args):
                team = user_args[i + 1]
                i += 2
            else:
                i += 1

        print_header()
        scope = f"{division or 'ALL'}" + (f" → {team}" if team else "")
        print(f"▶ CLI mode — running pipeline for: {scope}")
        run_pipeline(division=division, team=team)

    else:
        # ── Interactive menu ─────────────────────────────────────────────────
        interactive_menu()


if __name__ == "__main__":
    main()
