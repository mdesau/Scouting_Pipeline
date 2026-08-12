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
      calls scrape_gc_playbyplay.py, scrape_gc_boxscores.py, and gen_hitting.py
      via subprocess with the correct --division / --team flags.

MENU OPTIONS
────────────
  [0] Full pipeline — all divisions, all teams (default — press ENTER)
  [1] Single division — all teams in one division
  [2] Single team — drill down: pick division → pick team
  [3] Add a new Wild / Storm opponent to the pipeline
  [4] Manage seasons — switch active season or create a new one
  [Q] Quit

WHY SUBPROCESS INSTEAD OF IMPORT + CALL?
─────────────────────────────────────────
Each script (scrape_gc_playbyplay.py, scrape_gc_boxscores.py, gen_hitting.py) configures
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

import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Package imports — every pipeline module lives under the scout package.
# ---------------------------------------------------------------------------
from scout.season_config import (
    SCOUT_ROOT, SEASON_DIR, SEASON_ID, LOGS_DIR, SESSION_FILE,
    build_scraper_divisions, add_team_to_yaml,
    list_seasons, set_active_season, create_season,
)

# ── Paths ───────────────────────────────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).parent
# SEASON_DIR is the active season's data root (e.g. seasons/2026-spring/).
# SESSION_FILE (GC auth) and LOGS_DIR come from season_config (single source).
MAJORS_ROSTER = SEASON_DIR / "Majors" / "Reports" / "rosters.json"
MINORS_ROSTER = SEASON_DIR / "Minors" / "Reports" / "rosters.json"

# Each pipeline step is run as a module: `python -m scout.<pkg>.<module>`.
_MOD_PLAYBYPLAY = "scout.scraping.scrape_gc_playbyplay"
_MOD_BOXSCORES  = "scout.scraping.scrape_gc_boxscores"
_MOD_HITTING    = "scout.hitting.gen_hitting"
_MOD_PITCHING   = "scout.pitching.gen_pitching"

# ── DIVISIONS from season_config (DRY — single source of truth) ─────────────
# Previously imported from scrape_gc_playbyplay.py. Now loaded from YAML via
# season_config so the menu, scrapers, and stat engines all stay in sync
# without any inter-script imports.
DIVISIONS = build_scraper_divisions()


# ════════════════════════════════════════════════════════════════════════════
# HELPER UTILITIES
# ════════════════════════════════════════════════════════════════════════════

__version__ = "4.0.0"

def print_header():
    """Print the pipeline banner shown at the top of every menu screen."""
    print()
    print("=" * 58)
    print("  WCWAA Scout — Scouting Pipeline")
    print(f"  Season : {SEASON_ID}")
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
        print("     python -m scout.scraping.scrape_gc_playbyplay --login")
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
        # Each entry is a (team_id, slug, display_name) tuple.
        # Sorted alphabetically to match Majors/Minors behaviour (rosters.json
        # keys are already sorted via sorted() below).
        return sorted(name for (_, _, name) in DIVISIONS[division].get("teams", []))

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

def run_pipeline(division=None, team=None, headless=False):
    """
    Execute the full 4-step pipeline for the given scope.

    Steps:
      1. scrape_gc_playbyplay.py — scrape new game files from GameChanger
      2. scrape_gc_boxscores.py  — update rosters.json / roster.txt
      3. gen_hitting.py          — regenerate hitting PDFs
      4. gen_pitching.py         — regenerate pitching PDFs (Pitching Savant)

    Step 1 skips games that already have a .txt or -Reviewed.txt on disk,
    so re-running is always safe — only genuinely new games are scraped.

    Args:
        division: Division name string, or None for all divisions.
        team:     Team name string, or None for all teams in division.
        headless: If True (nightly/scheduled runs), scraper steps (1+2) use
                  fatal=False so a single GC page timeout does not abort the
                  pipeline before gen_hitting.py runs. gen_hitting always uses
                  fatal=True. Interactive runs keep fatal=True for all steps.
    """
    # Build the --division and --team flags for each script call
    # WHY list(filter(None, [...])):  Python's clean way to build an arg list
    # that omits items when they are None (no flag added if no filter needed).
    pipeline_start = time.time()
    div_args  = ["--division", division] if division else []
    team_args = ["--team",     team]     if team     else []

    # Step 1: Scrape new game files
    # gen_hitting.py accepts --team natively; scrape_gc_playbyplay uses it as a name filter
    print()
    print("─" * 58)
    scope = f"{division or 'ALL'}" + (f" → {team}" if team else " (all teams)")
    print(f"▶ Step 1/4  Scrape new games  [{scope}]")
    print("─" * 58)
    _run([sys.executable, "-m", _MOD_PLAYBYPLAY] + div_args + team_args, fatal=not headless)

    # Step 2: Update rosters
    # --team is now supported by scrape_gc_boxscores.py for Wild/Storm team-based divisions.
    # For Majors/Minors (org-based), --team is ignored — the full division roster JSON
    # is always updated together since all teams share one file.
    print()
    print("─" * 58)
    print(f"▶ Step 2/4  Update rosters    [{scope}]")
    print("─" * 58)
    _run([sys.executable, "-m", _MOD_BOXSCORES] + div_args + team_args, fatal=not headless)

    # Step 3: Generate PDFs
    # For single-team runs, pass --team so only that PDF is regenerated (fast).
    # For all-team runs, iterate each division explicitly.
    print()
    print("─" * 58)
    print(f"▶ Step 3/4  Hitting PDFs      [{scope}]")
    print("─" * 58)

    if division:
        _run([sys.executable, "-m", _MOD_HITTING, "--division", division] + team_args)
    else:
        # No division filter → run all four divisions
        for div in ["Majors", "Minors", "Wild", "Storm"]:
            print(f"  → {div}")
            _run([sys.executable, "-m", _MOD_HITTING, "--division", div])

    # Step 4: Generate Pitching Savant PDFs
    if importlib.util.find_spec(_MOD_PITCHING):
        print()
        print("─" * 58)
        print(f"▶ Step 4/4  Pitching PDFs    [{scope}]")
        print("─" * 58)

        if division:
            _run([sys.executable, "-m", _MOD_PITCHING, "--division", division] + team_args)
        else:
            for div in ["Majors", "Minors", "Wild", "Storm"]:
                print(f"  → {div}")
                _run([sys.executable, "-m", _MOD_PITCHING, "--division", div])

    print()
    print("=" * 58)
    print("  ✅ Pipeline complete.")
    print(f"  Scope: {scope}")
    print("=" * 58)
    print()

    # Write pipeline summary log (post-run accounting)
    try:
        _write_pipeline_summary(pipeline_start, division, team)
    except Exception as e:
        print(f"  ⚠️  Could not write pipeline summary: {e}")


# ════════════════════════════════════════════════════════════════════════════
# PIPELINE SUMMARY LOG
# ════════════════════════════════════════════════════════════════════════════

SUMMARY_LOG = LOGS_DIR / "pipeline_summary.log"


def _load_previous_summary():
    """
    Parse the most recent entry from pipeline_summary.log to get previous PA/IP
    counts per team for computing deltas.

    Returns:
        dict: {division: {team_name: {"pa": int, "ip": float, "games": int}}}
    """
    if not SUMMARY_LOG.exists():
        return {}
    try:
        content = SUMMARY_LOG.read_text(encoding="utf-8")
    except Exception:
        return {}

    # Find the last full entry (between the last two "===" separator blocks)
    entries = content.split("=" * 80)
    # Walk backwards to find the last complete STEP 3 section
    prev = {}
    for block in reversed(entries):
        if "STEP 3" not in block:
            continue
        # Parse per-team lines:  "    Guardians-Esau        14 games   385 PA   ✓ PDF"
        for m in re.finditer(
            r"^\s{4}(\S.+?)\s{2,}(\d+)\s+games?\s+(\d+)\s+PA",
            block, re.MULTILINE
        ):
            team_name = m.group(1).strip()
            prev[team_name] = {
                "games": int(m.group(2)),
                "pa": int(m.group(3)),
            }
        if prev:
            break
    return prev


def _find_latest_log(prefix, after_time=0):
    """Find the most recent log file matching a prefix in logs/, modified after after_time."""
    logs_dir = LOGS_DIR
    candidates = [f for f in logs_dir.glob(f"{prefix}_*.log") if f.stat().st_mtime >= after_time]
    candidates.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _parse_step1_log(log_path):
    """Parse scrape_gc_playbyplay log for per-division FINAL/new/skipped counts."""
    if not log_path:
        return {}
    content = log_path.read_text(encoding="utf-8", errors="replace")
    results = {}
    current_div = None

    for line in content.splitlines():
        # Division header
        m = re.search(r"Division:\s+(\w+)", line)
        if m:
            current_div = m.group(1)
            if current_div not in results:
                results[current_div] = {"final": 0, "new": 0, "skipped": 0}

        # Org-level: "78 FINAL games found on schedule"
        m = re.search(r"(\d+) FINAL games found on schedule", line)
        if m and current_div:
            results[current_div]["final"] += int(m.group(1))

        # Team-level: "Arena National Browning 11U: 27 FINAL games found"
        m = re.search(r": (\d+) FINAL games found", line)
        if m and current_div:
            results[current_div]["final"] += int(m.group(1))

        # "OK →" means a new game was scraped
        if "OK →" in line and current_div:
            results[current_div]["new"] += 1

    # Skipped = final - new (approximately)
    for div in results:
        results[div]["skipped"] = results[div]["final"] - results[div]["new"]

    return results


def _parse_step2_log(log_path):
    """Parse scrape_gc_boxscores log for per-division scraped/skipped/failed."""
    if not log_path:
        return {}
    content = log_path.read_text(encoding="utf-8", errors="replace")
    results = {}
    current_div = None

    for line in content.splitlines():
        m = re.search(r"Division:\s+(\w+)", line)
        if m:
            current_div = m.group(1)

        # "[Majors] Done — scraped:0  skipped:77  failed:1"
        m = re.search(r"Done — scraped:(\d+)\s+skipped:(\d+)\s+failed:(\d+)", line)
        if m and current_div:
            results[current_div] = {
                "scraped": int(m.group(1)),
                "skipped": int(m.group(2)),
                "failed": int(m.group(3)),
            }
            current_div = None  # reset for next division

    return results


def _parse_step3_log(log_path):
    """
    Parse gen_hitting log for per-team games/PA.
    Returns: {team_name: {"games": int, "pa": int}}
    """
    if not log_path:
        return {}
    content = log_path.read_text(encoding="utf-8", errors="replace")
    results = {}

    # Lines like: "13:20:18  INFO        Guardians-Esau                14   385    0.06s"
    for m in re.finditer(
        r"INFO\s{2,}(\S.+?)\s{2,}(\d+)\s+(\d+)\s+[\d.]+s\s*$",
        content, re.MULTILINE
    ):
        name = m.group(1).strip()
        if name == "TOTAL":
            continue
        results[name] = {"games": int(m.group(2)), "pa": int(m.group(3))}

    return results


def _parse_step4_log(log_path):
    """Parse gen_pitching log for per-division pitcher counts."""
    if not log_path:
        return {}
    content = log_path.read_text(encoding="utf-8", errors="replace")
    results = {}
    current_div = None

    for line in content.splitlines():
        m = re.search(r"Processing division:\s+(\w+)", line)
        if m:
            current_div = m.group(1)

        # "Majors: 78 pitchers found across all teams" or "Storm: 122 pitchers found"
        m = re.search(r"(\w+):\s+(\d+)\s+pitchers found", line)
        if m:
            results[m.group(1)] = {"pitchers": int(m.group(2))}

        # "Guardians-Esau: 6 pitchers → PDF"
        m = re.search(r"(.+?):\s+(\d+)\s+pitchers → PDF", line)
        if m and current_div:
            div_data = results.setdefault(current_div, {"pitchers": 0, "teams": {}})
            if "teams" not in div_data:
                div_data["teams"] = {}
            div_data["teams"][m.group(1).strip()] = int(m.group(2))

    return results


def _write_pipeline_summary(start_time, division_filter, team_filter):
    """
    Generate and append a pipeline summary to pipeline_summary.log.

    Reads the log files written during the current run (identified by timestamp),
    extracts key metrics, and computes deltas vs. the previous run.
    """
    end_time = time.time()
    elapsed = end_time - start_time
    elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60):02d}s"
    now = datetime.now()
    timestamp = now.strftime("%a %b %d, %Y %I:%M %p EDT")

    # Load previous summary for deltas
    prev_data = _load_previous_summary()

    # Find the latest log files (written during this run)
    step1_log = _find_latest_log("scrape_gc_playbyplay", start_time)
    step2_log = _find_latest_log("scrape_gc_boxscores", start_time)

    hitting_logs_dir  = LOGS_DIR
    pitching_logs_dir = LOGS_DIR

    step3_logs = sorted(
        [f for f in hitting_logs_dir.glob("gen_hitting_*.log") if f.stat().st_mtime >= start_time],
        reverse=True
    )
    step4_logs = sorted(
        [f for f in pitching_logs_dir.glob("gen_pitching_*.log") if f.stat().st_mtime >= start_time],
        reverse=True
    )

    # Parse each step
    step1 = _parse_step1_log(step1_log)
    step2 = _parse_step2_log(step2_log)

    # Step 3: merge all hitting logs
    step3_teams = {}
    for log_path in step3_logs:
        step3_teams.update(_parse_step3_log(log_path))

    # Step 4: merge all pitching logs
    step4 = {}
    for log_path in step4_logs:
        step4.update(_parse_step4_log(log_path))

    # Build output
    lines = []
    lines.append("=" * 80)
    lines.append(f"PIPELINE SUMMARY — {timestamp}")
    lines.append(f"Scope: {division_filter or 'ALL'}" + (f" → {team_filter}" if team_filter else " (all teams)"))
    lines.append("=" * 80)
    lines.append("")

    # Step 1
    lines.append("STEP 1 — Scrape Play-by-Play")
    for div in ["Majors", "Minors", "Wild", "Storm"]:
        d = step1.get(div, {})
        if d:
            lines.append(f"  {div:8s}: {d.get('final',0):3d} FINAL on schedule | "
                        f"{d.get('new',0):2d} new scraped | "
                        f"{d.get('skipped',0):3d} skipped (on disk)")
    lines.append("")

    # Step 2
    lines.append("STEP 2 — Update Rosters")
    for div in ["Majors", "Minors", "Wild", "Storm"]:
        d = step2.get(div, {})
        if d:
            lines.append(f"  {div:8s}: scraped: {d.get('scraped',0):3d}  "
                        f"skipped: {d.get('skipped',0):3d}  "
                        f"failed: {d.get('failed',0)}")
    lines.append("")

    # Step 3 — per-team detail with deltas
    lines.append("STEP 3 — Hitting PDFs")

    # Group teams by division (use DIVISIONS to figure out which is which)
    div_teams = {"Majors": [], "Minors": [], "Wild": [], "Storm": []}
    for team_name, stats in sorted(step3_teams.items()):
        placed = False
        for div_name in ["Wild", "Storm"]:
            div_team_names = [n for (_, _, n) in DIVISIONS.get(div_name, {}).get("teams", [])]
            if team_name in div_team_names:
                div_teams[div_name].append((team_name, stats))
                placed = True
                break
        if not placed:
            # Check Majors/Minors by looking at team key format (has hyphen)
            if "-" in team_name:
                # Try to figure out from roster files
                if MAJORS_ROSTER.exists():
                    with open(MAJORS_ROSTER, encoding="utf-8") as f:
                        majors_data = json.load(f)
                    if team_name in majors_data:
                        div_teams["Majors"].append((team_name, stats))
                        placed = True
                if not placed and MINORS_ROSTER.exists():
                    with open(MINORS_ROSTER, encoding="utf-8") as f:
                        minors_data = json.load(f)
                    if team_name in minors_data:
                        div_teams["Minors"].append((team_name, stats))
                        placed = True
            if not placed:
                div_teams["Storm"].append((team_name, stats))

    for div in ["Majors", "Minors", "Wild", "Storm"]:
        teams_in_div = div_teams[div]
        if not teams_in_div:
            continue
        lines.append(f"  {div} ({len(teams_in_div)} teams):")
        total_games = 0
        total_pa = 0
        for team_name, stats in teams_in_div:
            games = stats["games"]
            pa = stats["pa"]
            total_games += games
            total_pa += pa
            # Delta
            prev = prev_data.get(team_name, {})
            delta_pa = pa - prev.get("pa", 0) if prev else pa
            delta_str = f" (+{delta_pa})" if delta_pa > 0 and prev else ""
            lines.append(f"    {team_name:<40s} {games:3d} games  {pa:5d} PA{delta_str:<8s} ✓ PDF")
        # Total line
        total_delta = total_pa - sum(prev_data.get(t, {}).get("pa", 0) for t, _ in teams_in_div)
        total_delta_str = f" (+{total_delta})" if total_delta > 0 and prev_data else ""
        lines.append(f"    {'TOTAL':<40s} {total_games:3d} games  {total_pa:5d} PA{total_delta_str}")
        lines.append(f"    {len(teams_in_div)}/{len(teams_in_div)} updated")
        lines.append("")

    # Step 4
    lines.append("STEP 4 — Pitching PDFs")
    for div in ["Majors", "Minors", "Wild", "Storm"]:
        d = step4.get(div, {})
        if d:
            n_pitchers = d.get("pitchers", 0)
            n_teams = len(d.get("teams", {}))
            lines.append(f"  {div:8s}: {n_pitchers:3d} pitchers | {n_teams} teams → PDF")
    lines.append("")

    lines.append(f"PIPELINE COMPLETE — {elapsed_str} total")
    lines.append("=" * 80)
    lines.append("")
    lines.append("")

    # Write (append)
    SUMMARY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  📋 Pipeline summary → {SUMMARY_LOG.name}")


def _run(cmd, fatal=True):
    """
    Run a subprocess command from the Scripts/ directory.

    Args:
        cmd:   List of command + arguments, e.g. ["python3", "scrape_gc_playbyplay.py"]
        fatal: If True (default), call sys.exit() on non-zero return code.
               If False, log a warning and continue (used for scraper steps in
               headless/nightly runs so a single GC timeout doesn't abort the
               pipeline before gen_hitting.py runs).

    Raises:
        SystemExit if the command returns a non-zero exit code and fatal=True.
    """
    result = subprocess.run(cmd, cwd=str(SCRIPTS_DIR))
    if result.returncode != 0:
        print(f"\n⚠️  Command finished with exit code {result.returncode}: {' '.join(cmd)}")
        print("   Check the output above for error details.")
        if fatal:
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


def add_new_team():
    """
    Interactive flow to add a new Wild or Storm opponent to the pipeline.

    Steps:
      1. Paste a GC schedule URL → auto-parse team_id and slug
      2. Confirm or edit the suggested folder name
      3. Choose Wild or Storm division
      4. Write the new team to config/<season_id>.yaml via add_team_to_yaml()
      5. Create the Games/ folder structure on disk
      6. Print reminder about verifying folder name after first scrape

    WHY YAML NOT PYTHON: Previously this wizard did brittle text-replacement
    on Python source files (scrape_gc_playbyplay.py + scrape_gc_boxscores.py).
    Now we write to the YAML config — a proper data file designed for this.
    No Python source code is modified at runtime.

    IMPORTANT NOTE ON FOLDER NAMES:
    The folder name MUST match the team name as GameChanger writes it in the
    inning headers (e.g. "===Top 1st - SBA Alabama National 12U===").
    The suggested name is a best guess from the URL slug. Always verify by
    opening the first scraped game file.
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

    # Write to YAML config (single source of truth — no Python file editing)
    ok = add_team_to_yaml(division, team_id, slug, folder_name)

    # Create folder structure on disk
    team_dir = SEASON_DIR / division / folder_name / "Games"
    team_dir.mkdir(parents=True, exist_ok=True)

    if ok:
        print()
        print(f"  ✅ \"{folder_name}\" added to {division}.")
        print(f"     config/{SEASON_ID}.yaml updated")
        print(f"     Folder created: seasons/{SEASON_ID}/{division}/{folder_name}/Games/")
        print()
        print("  Next steps:")
        print("  1. Run the pipeline (option [0]) to scrape the first batch of games.")
        print(f"  2. Open a game file in seasons/{SEASON_ID}/{division}/{folder_name}/Games/")
        print("     and verify the team name in the inning header matches the folder name.")
        print("  3. If they differ, rename the folder and update the YAML:")
        print(f"       Edit config/{SEASON_ID}.yaml → find the team's 'name:' field")
    else:
        print()
        print(f"  ⚠️  Could not update YAML. Check config/{SEASON_ID}.yaml manually.")
        print(f"     Add this entry to the {division} teams list:")
        print(f"       - name: \"{folder_name}\"")
        print(f"         gc_id: \"{team_id}\"")
        print(f"         gc_slug: \"{slug}\"")



# ════════════════════════════════════════════════════════════════════════════
# SEASON MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════

def manage_seasons():
    """
    Sub-menu for season management: switch the active season or create a new one.

    Why a sub-menu rather than top-level options?
    Season management is an occasional admin task (once or twice a year).
    Keeping it one level deeper prevents it from cluttering the everyday menu
    that coaches use weekly to build reports.
    """
    print("\n── Manage Seasons ───────────────────────────────────────")
    print(f"  Active season: {SEASON_ID}\n")
    print("  [1] Switch to a different season")
    print("  [2] Create a new season")
    print("  [B] Back to main menu")
    print()

    choice = ask("Choice: ", default="B")

    if choice == "1":
        _switch_season_wizard()
    elif choice == "2":
        _create_season_wizard()
    else:
        return   # Back / anything else → return to main menu


def _switch_season_wizard():
    """
    Let the user pick a different season to make active.

    After switching, active_season.txt is updated. The current terminal
    session still has the old SEASON_ID in memory (Python module globals
    are set at import time), so we print a clear restart notice.

    NOTE: The web server (if running) will also need a restart to pick
    up the new active season. This is documented in the output.
    """
    seasons = list_seasons()

    if len(seasons) <= 1:
        print("\n  Only one season exists. Use option [2] to create a new one.")
        return

    print()
    options = [
        f"{s['display_name']}  {'← active' if s['is_active'] else ''}"
        for s in seasons
    ]
    chosen_label = pick_from_list("Select a season to activate:", options)
    if not chosen_label:
        return

    # Map the chosen label back to the season dict.
    idx = options.index(chosen_label)
    chosen = seasons[idx]

    if chosen["is_active"]:
        print(f"\n  {chosen['display_name']} is already the active season.")
        return

    set_active_season(chosen["id"])
    print()
    print(f"  ✅ Active season updated → {chosen['id']}")
    print()
    print("  ⚠️  RESTART REQUIRED to use the new season:")
    print("     • Terminal: exit and re-run  bash launchers/run_scout.sh")
    print("     • Web UI: stop the server and re-launch  Start Scout.command")
    print()
    print(f"  The pipeline will now target: seasons/{chosen['id']}/")


def _create_season_wizard():
    """
    Interactive wizard to scaffold a new season config and folder structure.

    Prompts for:
      1. Season ID     — e.g. "2026-fall"  (becomes the YAML filename)
      2. Display name  — e.g. "2026 Fall"  (auto-suggested from season ID)
      3. Majors GC org ID  — OPTIONAL (add later via Modify Season in the web UI)
      4. Minors GC org ID  — OPTIONAL
      5. Set as active season now?  (optional — can switch later via [1])

    On success calls season_config.create_season() which:
      • Writes config/<season_id>.yaml (from template)
      • Creates the seasons/<season_id>/ folder tree
      • Optionally updates active_season.txt
    """
    print("\n── Create New Season ────────────────────────────────────")
    print("This wizard scaffolds a new season config and folder structure.")
    print("The GameChanger org IDs for Majors and Minors are OPTIONAL — you can")
    print("create the season now and fill them in later (Modify Season in the web UI).\n")

    # ── Season ID ────────────────────────────────────────────────────────────
    season_id = ask("Season ID (e.g. 2026-fall): ")
    if not season_id:
        print("  No season ID entered — cancelled.")
        return

    # Basic format check: should look like YYYY-season (e.g. 2026-fall).
    if not re.match(r"^\d{4}-\w+$", season_id):
        print(f"  ⚠️  '{season_id}' doesn't look like a valid season ID.")
        print("     Expected format: YYYY-name  (e.g. 2026-fall, 2027-spring)")
        confirm = ask("  Continue anyway? [y/N]: ", default="N")
        if confirm.upper() != "Y":
            return

    # ── Display name ─────────────────────────────────────────────────────────
    # Auto-generate a suggestion: "2026-fall" → "2026 Fall"
    auto_name = " ".join(
        p if p.isdigit() else p.capitalize()
        for p in season_id.split("-")
    )
    display_name = ask(
        f'Display name (press ENTER for "{auto_name}"): ',
        default=auto_name,
    )

    # ── GC org IDs (optional) ────────────────────────────────────────────────
    print()
    print("  GameChanger org IDs for the new season (Majors/Minors league orgs).")
    print("  Optional — press ENTER to skip either and add it later.\n")

    majors_gc_id = ask("  Majors GC org ID (ENTER to skip): ")
    minors_gc_id = ask("  Minors GC org ID (ENTER to skip): ")

    # ── Set active now? ───────────────────────────────────────────────────────
    print()
    set_now = ask("  Set as active season now? [y/N]: ", default="N")
    set_active = set_now.upper() == "Y"

    # ── Confirm before creating ───────────────────────────────────────────────
    print()
    print("  Summary:")
    print(f"    Season ID    : {season_id}")
    print(f"    Display name : {display_name}")
    print(f"    Majors GC ID : {majors_gc_id or '(not set — add later)'}")
    print(f"    Minors GC ID : {minors_gc_id or '(not set — add later)'}")
    print(f"    Set active   : {'Yes' if set_active else 'No (switch later via [4] → [1])'}")
    print()

    confirm = ask("  Create this season? [Y/n]: ", default="Y")
    if confirm.upper() != "Y":
        print("  Cancelled.")
        return

    # ── Create ────────────────────────────────────────────────────────────────
    try:
        yaml_path = create_season(
            season_id=season_id,
            majors_gc_id=majors_gc_id,
            minors_gc_id=minors_gc_id,
            display_name=display_name,
            set_active=set_active,
        )
    except FileExistsError as e:
        print(f"\n  ⚠️  {e}")
        return
    except FileNotFoundError as e:
        print(f"\n  ⚠️  {e}")
        return

    print()
    print(f"  ✅ Season '{season_id}' created!")
    print(f"     Config : config/{yaml_path.name}")
    print(f"     Data   : seasons/{season_id}/")
    print()
    print("  Next steps:")
    print(f"  1. Add Majors + Minors teams to config/{yaml_path.name}")
    print("     (after the draft — add name/coach per team under divisions.Majors/Minors.teams)")
    print("  2. Wild/Storm opponents: use option [3] Add Team as games are scheduled.")
    print("  3. Run scrape_gc_boxscores.py after the first games to build rosters.json.")

    if set_active:
        print()
        print("  ⚠️  RESTART REQUIRED — active season was changed:")
        print("     • Terminal: exit and re-run  bash launchers/run_scout.sh")
        print("     • Web UI: stop the server and re-launch  Start Scout.command")



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
    print("  [4] Manage seasons — switch or create")
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

    # ── [4] Manage seasons ───────────────────────────────────────────────────
    elif choice == "4":
        manage_seasons()

    else:
        print(f"  Unrecognised choice: '{choice}'. Please run again and enter 0–4 or Q.")
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
            run_pipeline(division=None, team=None, headless=True)
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
