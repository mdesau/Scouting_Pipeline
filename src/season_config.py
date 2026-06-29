#!/usr/bin/env python3
"""
season_config.py — Season Configuration Loader
===============================================
Central module that all pipeline scripts import to get their paths and
division data. Eliminates hardcoded season paths from every script.

HOW IT WORKS
------------
1. Reads config/active_season.txt (or SCOUT_SEASON env var) to find the
   active season ID (e.g. "2026-spring").
2. Loads config/<season_id>.yaml which contains all team metadata.
3. Builds DIVISIONS dicts in the exact shape each script expects.

WHY A CENTRAL CONFIG MODULE?
-----------------------------
Previously, team names, GC IDs, and folder paths were duplicated across
scrape_gc_playbyplay.py, scrape_gc_boxscores.py, and gen_hitting.py.
Adding one team required editing three files. Now there is one YAML file
and one Python loader — all scripts import from here (DRY principle).

NEW SEASON WORKFLOW
-------------------
1. cp config/2026-spring.yaml config/2026-fall.yaml
2. Edit the new YAML (update teams, IDs, paths as needed)
3. echo "2026-fall" > config/active_season.txt
4. mkdir -p seasons/2026-fall/{Majors,Minors,Wild,Storm}/Reports
5. Run the pipeline — it picks up the new season automatically.

ADDING A TEAM MID-SEASON
-------------------------
Use the interactive menu (bash launchers/run_scout.sh -> option [3]).
The wizard calls add_team_to_yaml() in this module to update the YAML.
No Python source files need editing.

EXPORTS
-------
SCOUT_ROOT      : Path  — repo root (Scout/ directory)
SEASON_ID       : str   — active season identifier
SEASON_DIR      : Path  — seasons/<season_id>/
get_season_dir(): Path  — same as SEASON_DIR (callable for testing)
build_scraper_divisions()  : dict — shape for scrape_gc_playbyplay/boxscores
build_hitting_divisions()  : dict — shape for gen_hitting + stat_analysis
add_team_to_yaml()         : bool — appends a new travel team to the YAML

REFERENCED IN
-------------
  scrape_gc_playbyplay.py, scrape_gc_boxscores.py,
  gen_hitting.py, gen_pitching.py, stat_analysis.py, run_menu.py

Version: Part of Scout Pipeline v3.0.0+
"""

import os
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Path Bootstrap
# ---------------------------------------------------------------------------
# This file lives at src/season_config.py.
# SCOUT_ROOT is two levels up: src/ → Scout/
SCOUT_ROOT = Path(__file__).resolve().parent.parent   # → Scout/
_CONFIG_DIR = SCOUT_ROOT / "config"
_SEASONS_DIR = SCOUT_ROOT / "seasons"
_ACTIVE_SEASON_FILE = _CONFIG_DIR / "active_season.txt"


# ---------------------------------------------------------------------------
# Active Season Resolution
# ---------------------------------------------------------------------------
def get_active_season_id() -> str:
    """
    Return the active season identifier.

    Priority order:
      1. SCOUT_SEASON environment variable (useful for CI/testing)
      2. config/active_season.txt (normal operation)

    Returns:
        str: Season ID like "2026-spring" or "2026-fall"

    Raises:
        RuntimeError: If neither source is configured.
    """
    # WHY ENV VAR: Lets you override the active season without editing a file.
    # Useful when testing a new season config before officially switching.
    if "SCOUT_SEASON" in os.environ:
        return os.environ["SCOUT_SEASON"].strip()

    if _ACTIVE_SEASON_FILE.exists():
        return _ACTIVE_SEASON_FILE.read_text(encoding="utf-8").strip()

    raise RuntimeError(
        "No active season configured.\n"
        "  Option 1: Set environment variable SCOUT_SEASON=2026-spring\n"
        f"  Option 2: Create {_ACTIVE_SEASON_FILE} with season ID on first line"
    )


def load_season_yaml(season_id: str = None) -> tuple:
    """
    Load the YAML config for the given season (or the active season).

    Args:
        season_id: Season ID string (e.g. "2026-spring"). If None, reads
                   from active_season.txt or SCOUT_SEASON env var.

    Returns:
        (season_id: str, cfg: dict) — the season ID and parsed YAML dict.

    Raises:
        FileNotFoundError: If the season YAML does not exist.
    """
    if season_id is None:
        season_id = get_active_season_id()

    yaml_path = _CONFIG_DIR / f"{season_id}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(
            f"Season config not found: {yaml_path}\n"
            f"Available configs: {list(_CONFIG_DIR.glob('*.yaml'))}"
        )

    with open(yaml_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    return season_id, cfg


def get_season_dir(season_id: str = None) -> Path:
    """
    Return the path to the season data directory.

    Args:
        season_id: If None, uses the active season.

    Returns:
        Path: e.g. Scout/seasons/2026-spring/
    """
    if season_id is None:
        season_id = get_active_season_id()
    return _SEASONS_DIR / season_id


# ---------------------------------------------------------------------------
# Module-Level Convenience Bindings
# ---------------------------------------------------------------------------
# These are the primary exports other scripts use. They resolve once at import
# time so scripts don't need to call functions to get the basic path constants.
SEASON_ID: str = get_active_season_id()
SEASON_DIR: Path = get_season_dir(SEASON_ID)
_SEASON_CFG: dict = load_season_yaml(SEASON_ID)[1]


# ---------------------------------------------------------------------------
# DIVISIONS Builder: Scraper Shape
# ---------------------------------------------------------------------------
def build_scraper_divisions(season_id: str = None) -> dict:
    """
    Build the DIVISIONS dict in the shape expected by scrape_gc_playbyplay.py
    and scrape_gc_boxscores.py.

    Scraper shape (league divisions):
        {
            "type":       "org",
            "id":         <gc_org_id>,           # used by playbyplay
            "org_id":     <gc_org_id>,            # used by boxscores
            "output":     Path,                   # Scorebooks dir (playbyplay)
            "roster_out": Path,                   # rosters.json output (boxscores)
            "verify_out": Path,                   # box_verify.json output (boxscores)
            "label":      str,
        }

    Scraper shape (travel divisions):
        {
            "type":        "teams",
            "teams":       [(gc_id, gc_slug, folder_name), ...],
            "output_base": Path,                  # base dir for Games/ folders (playbyplay)
            "base_dir":    Path,                  # same path (boxscores)
            "label":       str,
        }

    Args:
        season_id: If None, uses the active season.

    Returns:
        dict keyed by division name ("Majors", "Minors", "Wild", "Storm").
    """
    if season_id is None:
        sid, cfg = SEASON_ID, _SEASON_CFG
    else:
        sid, cfg = load_season_yaml(season_id)

    season_dir = get_season_dir(sid)
    divs = {}

    for div_name, div_cfg in cfg["divisions"].items():
        if div_cfg["type"] == "league":
            # Majors / Minors — org-based scraping
            org_id = div_cfg["gc_org_id"]
            divs[div_name] = {
                "type":       "org",
                "id":         org_id,             # scrape_gc_playbyplay key
                "org_id":     org_id,             # scrape_gc_boxscores key
                "output":     season_dir / div_cfg["scorebooks"],
                "roster_out": season_dir / div_cfg["roster_json"],
                "verify_out": season_dir / div_cfg["verify_json"],
                "label":      div_name,
            }
        else:
            # Wild / Storm — team-based scraping
            teams = [
                (t["gc_id"], t["gc_slug"], t["name"])
                for t in div_cfg["teams"]
            ]
            base = season_dir / div_cfg["output_base"]
            divs[div_name] = {
                "type":        "teams",
                "teams":       teams,
                "output_base": base,              # scrape_gc_playbyplay key
                "base_dir":    base,              # scrape_gc_boxscores key
                "label":       div_name,
            }

    return divs


# ---------------------------------------------------------------------------
# DIVISIONS Builder: Hitting Shape
# ---------------------------------------------------------------------------
def build_hitting_divisions(season_id: str = None) -> dict:
    """
    Build the DIVISIONS dict in the shape expected by gen_hitting.py and
    stat_analysis.py.

    Hitting shape (league divisions):
        {
            "scorebooks":      str (path),
            "output":          str (path),
            "csv":             str (path),
            "roster_json":     str (path),
            "verify_json":     str (path),
            "csv_overrides":   {team_name: alternate_csv_key},
            "roster_additions":{team_key: {initials: display}},
            "league_scan":     True,
            "label_suffix":    str,
            "teams":           [(name, coach), ...],
        }

    Hitting shape (travel divisions):
        {
            "wild_base":        str (path),
            "league_scan":      False,
            "label_suffix":     str,
            "fixed_thresholds": {stat_key: float},
        }

    WHY STRINGS NOT PATHS: gen_hitting.py was written to use f-string
    concatenation (f"{BASE}/Majors/..."). We return str to maintain
    backward compatibility with all the existing string path joins.

    Args:
        season_id: If None, uses the active season.

    Returns:
        dict keyed by division name.
    """
    if season_id is None:
        sid, cfg = SEASON_ID, _SEASON_CFG
    else:
        sid, cfg = load_season_yaml(season_id)

    season_dir = get_season_dir(sid)
    divs = {}

    for div_name, div_cfg in cfg["divisions"].items():
        if div_cfg["type"] == "league":
            teams = [(t["name"], t["coach"]) for t in div_cfg["teams"]]
            divs[div_name] = {
                "scorebooks":       str(season_dir / div_cfg["scorebooks"]),
                "output":           str(season_dir / div_cfg["output"]),
                "csv":              str(season_dir / div_cfg["csv"]),
                "roster_json":      str(season_dir / div_cfg["roster_json"]),
                "verify_json":      str(season_dir / div_cfg["verify_json"]),
                "csv_overrides":    dict(div_cfg.get("csv_overrides") or {}),
                "roster_additions": dict(div_cfg.get("roster_additions") or {}),
                "league_scan":      True,
                "label_suffix":     div_cfg.get("label_suffix", div_name),
                "teams":            teams,
            }
        else:
            divs[div_name] = {
                "wild_base":        str(season_dir / div_cfg["output_base"]),
                "league_scan":      False,
                "label_suffix":     div_cfg.get("label_suffix", div_name),
                "fixed_thresholds": dict(div_cfg.get("fixed_thresholds") or {}),
            }

    return divs


# ---------------------------------------------------------------------------
# Add Team to YAML (used by run_menu.py add_new_team wizard)
# ---------------------------------------------------------------------------
def add_team_to_yaml(
    division: str,
    team_id: str,
    slug: str,
    folder_name: str,
    season_id: str = None,
) -> bool:
    """
    Append a new travel team entry to the season YAML and save it.

    Called by run_menu.py's add_new_team() wizard. Replaces the previous
    approach of doing brittle text-replacement on Python source files.

    Args:
        division:    "Wild" or "Storm"
        team_id:     GameChanger team ID string
        slug:        GameChanger URL slug string
        folder_name: Exact folder name (must match GC inning header spelling)
        season_id:   If None, uses the active season.

    Returns:
        True on success, False if division not found or wrong type.

    Raises:
        FileNotFoundError: If the season YAML doesn't exist.
    """
    if season_id is None:
        season_id = get_active_season_id()

    yaml_path = _CONFIG_DIR / f"{season_id}.yaml"

    # Load current config
    with open(yaml_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    div_cfg = cfg.get("divisions", {}).get(division)
    if not div_cfg:
        return False
    if div_cfg.get("type") != "travel":
        # Only travel divisions have per-team entries in the scraper
        return False

    # Guard against duplicates
    existing_names = [t["name"] for t in div_cfg.get("teams", [])]
    if folder_name in existing_names:
        return True  # Already present — idempotent

    # Append the new team
    new_team = {"name": folder_name, "gc_id": team_id, "gc_slug": slug}
    div_cfg["teams"].append(new_team)

    # Write back — PyYAML reformats the file but preserves all data.
    # WHY ACCEPTABLE: The YAML is a data file read by Python, not a human
    # editing target. Formatting loss on team-add is a known trade-off
    # vs. adding a ruamel.yaml dependency.
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=False)

    return True


# ---------------------------------------------------------------------------
# Self-test (python3 src/season_config.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"SCOUT_ROOT : {SCOUT_ROOT}")
    print(f"SEASON_ID  : {SEASON_ID}")
    print(f"SEASON_DIR : {SEASON_DIR}")
    print()

    scraper_divs = build_scraper_divisions()
    hitting_divs = build_hitting_divisions()

    print("Scraper DIVISIONS:")
    for name, d in scraper_divs.items():
        if d["type"] == "org":
            print(f"  {name}: org_id={d['org_id']} output={d['output']}")
        else:
            print(f"  {name}: {len(d['teams'])} teams  output_base={d['output_base']}")

    print()
    print("Hitting DIVISIONS:")
    for name, d in hitting_divs.items():
        if d.get("league_scan"):
            print(f"  {name}: {len(d['teams'])} teams  scorebooks={d['scorebooks']}")
        else:
            print(f"  {name}: travel  wild_base={d['wild_base']}")
