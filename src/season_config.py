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

NEW SEASON WORKFLOW (automated — v3.2.0+)
------------------------------------------
Use the terminal menu [4] Manage seasons → Create new season, or the web UI
Season dropdown → "Create New Season". Both call create_season() below.

Manual fallback (if needed):
  1. Call create_season("2026-fall", majors_gc_id, minors_gc_id) directly
  2. Add Majors/Minors teams to the generated YAML (name/coach per team)
  3. Activate: set_active_season("2026-fall")
  4. Wild/Storm opponents accumulate via "Add Team" during the season.

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
get_season_dir()           : Path  — same as SEASON_DIR (callable for testing)
build_scraper_divisions()  : dict  — shape for scrape_gc_playbyplay/boxscores
build_hitting_divisions()  : dict  — shape for gen_hitting + stat_analysis
add_team_to_yaml()         : bool  — appends a new travel team to the YAML
list_seasons()             : list  — all season configs found in config/
set_active_season()        : None  — writes active_season.txt
create_season()            : Path  — scaffolds new season YAML + folder structure

REFERENCED IN
-------------
  scrape_gc_playbyplay.py, scrape_gc_boxscores.py,
  gen_hitting.py, gen_pitching.py, stat_analysis.py, run_menu.py,
  server.py

Version: Part of Scout Pipeline v3.2.0+
"""

import os
import re
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
        # Tournament-team (travel) divisions can be toggled off for a season
        # without deleting their data. A missing/true `active` flag = included.
        if div_cfg["type"] != "league" and not div_cfg.get("active", True):
            continue
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
        # Skip tournament-team divisions toggled off for this season (see
        # build_scraper_divisions for rationale). League divisions are always on.
        if div_cfg["type"] != "league" and not div_cfg.get("active", True):
            continue
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
# Season Management (v3.2.0+)
# ---------------------------------------------------------------------------

def list_seasons() -> list:
    """
    Return all available seasons found in the config directory.

    Scans config/*.yaml, skipping season_template.yaml (the scaffold file).
    Each entry carries enough info for UI display without loading full configs.

    Returns:
        List of dicts sorted by season_id, each with:
          {"id": str, "display_name": str, "is_active": bool}

    Example:
        [
            {"id": "2026-spring", "display_name": "2026 Spring", "is_active": True},
            {"id": "2026-fall",   "display_name": "2026 Fall",   "is_active": False},
        ]
    """
    active = get_active_season_id()
    seasons = []

    for yaml_path in sorted(_CONFIG_DIR.glob("*.yaml")):
        # The template is a scaffold, not a real season — skip it.
        if yaml_path.stem == "season_template":
            continue
        try:
            with open(yaml_path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            # Use season_id from file content if present; fall back to filename.
            season_id = str(cfg.get("season_id", yaml_path.stem))
            display_name = str(cfg.get("display_name", season_id))
            seasons.append({
                "id": season_id,
                "display_name": display_name,
                "is_active": (season_id == active),
            })
        except Exception:
            # Skip malformed or unreadable YAMLs rather than crashing.
            continue

    return seasons


def set_active_season(season_id: str) -> None:
    """
    Set the active season by writing its ID to active_season.txt.

    All scripts that import season_config will pick up the new season on
    their next startup/import. Running processes (e.g. the web server) need
    to be restarted to see the change.

    Args:
        season_id: Season ID string (e.g. "2026-fall"). A config YAML for
                   this ID must already exist in config/.

    Raises:
        FileNotFoundError: If config/<season_id>.yaml does not exist.
    """
    yaml_path = _CONFIG_DIR / f"{season_id}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(
            f"No config found for season '{season_id}'. "
            f"Create it first with create_season().\n"
            f"Available: {[p.stem for p in _CONFIG_DIR.glob('*.yaml') if p.stem != 'season_template']}"
        )
    # WHY trailing newline: text editors and tools expect POSIX-style files
    # to end with a newline; avoids "no newline at end of file" warnings.
    _ACTIVE_SEASON_FILE.write_text(season_id + "\n", encoding="utf-8")


def create_season(
    season_id: str,
    majors_gc_id: str = "",
    minors_gc_id: str = "",
    display_name: str = None,
    tournament_teams: list = None,
    set_active: bool = False,
) -> "Path":
    """
    Scaffold a new season config from the season template.

    Creates:
      • config/<season_id>.yaml  — season config with provided GC org IDs,
                                   empty team lists for all 4 divisions
      • seasons/<season_id>/     — folder structure for Scorebooks,
                                   Scouting_Reports, Wild/, Storm/

    WHY TEAMS START EMPTY
    ─────────────────────
    GC org IDs are created by the league admin before the season; they are
    the only piece of data known up-front. In-house team rosters are unknown
    until after the draft, and travel opponents are discovered game-by-game.
      • Majors/Minors teams: add manually to the YAML after the draft
        (name + coach per entry under divisions.Majors/Minors.teams).
      • Wild/Storm teams: accumulate via "Add Team" wizard as games are
        scheduled — exactly the same flow as today.

    NOTE ON ACTIVE SEASON
    ─────────────────────
    Switching the active season requires a server restart to take effect
    (SEASON_ID is resolved at module import time for all running scripts).
    The web UI and terminal menu prompt for this restart automatically.

    Args:
        season_id:     Unique identifier, e.g. "2026-fall". Used as the
                       YAML filename and folder name under seasons/.
        majors_gc_id:  GameChanger org ID for Majors. OPTIONAL — pass "" if
                       you don't have it yet; you can fill it in later via
                       update_season(). Find it in the GC admin console.
        minors_gc_id:  GameChanger org ID for Minors. OPTIONAL (same as above).
        display_name:  Human-readable label (e.g. "2026 Fall"). Auto-derived
                       from season_id if not provided:
                         "2026-fall" → "2026 Fall"
                         "2026-spring" → "2026 Spring"
        tournament_teams: Optional list of extra tournament-team names to
                       create as travel divisions alongside Wild/Storm
                       (e.g. ["Mavs"]). Each gets its own folder + YAML entry.
        set_active:    If True, also updates active_season.txt so this
                       season becomes the active one immediately.

    Returns:
        Path to the newly created season YAML file.

    Raises:
        FileExistsError:    If config/<season_id>.yaml already exists.
        FileNotFoundError:  If config/season_template.yaml is missing.
    """
    yaml_path = _CONFIG_DIR / f"{season_id}.yaml"
    if yaml_path.exists():
        raise FileExistsError(
            f"Season config already exists: {yaml_path}\n"
            f"Delete it first if you want to recreate this season."
        )

    template_path = _CONFIG_DIR / "season_template.yaml"
    if not template_path.exists():
        raise FileNotFoundError(
            f"Season template not found: {template_path}\n"
            f"This file should be in the config/ folder of the repo."
        )

    # Auto-generate display_name from season_id if caller did not supply one.
    # Split on "-", capitalize non-numeric parts, preserve year digits:
    #   "2026-fall"   → "2026 Fall"
    #   "2026-spring" → "2026 Spring"
    if display_name is None:
        parts = season_id.split("-")
        display_name = " ".join(
            p if p.isdigit() else p.capitalize()
            for p in parts
        )

    # Load the template as a plain data dict (yaml.safe_load discards comments,
    # which is fine — the generated YAML is a data file, not a human-edit file).
    with open(template_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Fill in season-specific values.
    cfg["season_id"] = season_id
    cfg["display_name"] = display_name
    cfg["divisions"]["Majors"]["gc_org_id"] = majors_gc_id
    cfg["divisions"]["Minors"]["gc_org_id"] = minors_gc_id

    # Add any extra tournament-team (travel) divisions requested at creation.
    for name in (tournament_teams or []):
        name = (name or "").strip()
        if name and name not in cfg["divisions"]:
            cfg["divisions"][name] = _new_travel_division(name)

    # Generate the CSV path using the display name to follow the project
    # convention (e.g. "2026 Fall Draft Results.xlsx - Majors.csv").
    # The actual .xlsx → .csv export must be placed at this path before
    # running gen_hitting.py for the first time.
    cfg["divisions"]["Majors"]["csv"] = (
        f"Majors/Reports/{display_name} Draft Results.xlsx - Majors.csv"
    )
    cfg["divisions"]["Minors"]["csv"] = (
        f"Minors/Reports/{display_name} Draft Results.xlsx - Minors.csv"
    )

    # Write the new season YAML. PyYAML reformats the file (no comments),
    # which is the same known trade-off as add_team_to_yaml().
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=False)

    # Create the on-disk folder structure the pipeline expects.
    _scaffold_season_dirs(_SEASONS_DIR / season_id, cfg)

    if set_active:
        set_active_season(season_id)

    return yaml_path


def _scaffold_season_dirs(season_dir: "Path", cfg: dict) -> None:
    """
    Create the folder tree for a new season based on its config dict.

    League divisions (Majors/Minors) need Scorebooks + Scouting_Reports.
    Travel divisions (Wild/Storm) need only the output_base folder;
    per-team Games/ subfolders are created by add_team_to_yaml() / "Add Team".

    Args:
        season_dir: Root path for this season (seasons/<season_id>/).
        cfg:        Parsed season config dict (from yaml.safe_load).
    """
    for div_cfg in cfg.get("divisions", {}).values():
        if div_cfg.get("type") == "league":
            # Scorebooks: where raw game .txt files land after scraping.
            (season_dir / div_cfg["scorebooks"]).mkdir(parents=True, exist_ok=True)
            # Scouting_Reports: where generated PDFs are written.
            (season_dir / div_cfg["output"]).mkdir(parents=True, exist_ok=True)
        else:
            # Travel: base folder only; Games/ subfolders come later per team.
            (season_dir / div_cfg["output_base"]).mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Season Editing + Tournament Teams (v3.4.0+)
# ---------------------------------------------------------------------------
# A "tournament team" is a per-season travel division that sits alongside
# Majors/Minors/Wild/Storm on disk (seasons/<id>/<Name>/) and holds its own
# opponents. It reuses the existing "travel" division machinery, so no changes
# to the scraper/hitting builders are needed beyond the `active` skip flag.

# Regex for a safe tournament-team name (also the folder + YAML key).
_TT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _'&.\-]{0,48}$")

# Division names that are structural, not user-managed tournament teams.
_RESERVED_DIVISIONS = {"Majors", "Minors"}


def _new_travel_division(name: str) -> dict:
    """Return a fresh travel-division config dict for a tournament team."""
    return {
        "type": "travel",
        "output_base": name,
        "label_suffix": name,
        "fixed_thresholds": {"slg_top33": 0.45, "c_bot33": 0.5, "bb_top33": 0.2},
        "teams": [],
        "tournament_team": True,   # flags a user-added division (vs Wild/Storm)
        "active": True,            # toggled by set_tournament_team_active()
    }


def _load_cfg(season_id: str) -> tuple:
    """Load a season YAML for writing. Returns (yaml_path, cfg)."""
    yaml_path = _CONFIG_DIR / f"{season_id}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"Season config not found: {yaml_path}")
    with open(yaml_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return yaml_path, cfg


def _save_cfg(yaml_path: "Path", cfg: dict) -> None:
    """Write a season config dict back to disk (same format as create_season)."""
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True,
                  sort_keys=False)


def update_season(
    season_id: str,
    display_name: str = None,
    majors_gc_id: str = None,
    minors_gc_id: str = None,
) -> "Path":
    """
    Update editable fields of an existing season (the "Modify" flow).

    Only non-None arguments are applied, so callers can update one field at a
    time. Empty strings ARE applied (e.g. to clear a not-yet-known org ID).

    Args:
        season_id:     Season to modify. Its config YAML must already exist.
        display_name:  New display name, or None to leave unchanged.
        majors_gc_id:  New Majors org ID, or None to leave unchanged.
        minors_gc_id:  New Minors org ID, or None to leave unchanged.

    Returns:
        Path to the updated season YAML.

    Raises:
        FileNotFoundError: If the season config does not exist.
    """
    yaml_path, cfg = _load_cfg(season_id)

    if display_name is not None:
        cfg["display_name"] = display_name
    if majors_gc_id is not None and "Majors" in cfg.get("divisions", {}):
        cfg["divisions"]["Majors"]["gc_org_id"] = majors_gc_id
    if minors_gc_id is not None and "Minors" in cfg.get("divisions", {}):
        cfg["divisions"]["Minors"]["gc_org_id"] = minors_gc_id

    _save_cfg(yaml_path, cfg)
    return yaml_path


def add_tournament_team(season_id: str, name: str) -> bool:
    """
    Add a tournament-team (travel) division to a season + create its folder.

    Idempotent: if a division with this name already exists it is left as-is
    and True is returned. Creates seasons/<season_id>/<name>/ on disk.

    Args:
        season_id: Season to add the tournament team to.
        name:      Tournament team name (also the folder name + YAML key).

    Returns:
        True on success (added or already present).

    Raises:
        FileNotFoundError: If the season config does not exist.
        ValueError:        If the name is empty/invalid or collides with a
                           reserved league division (Majors/Minors).
    """
    name = (name or "").strip()
    if not _TT_NAME_RE.match(name):
        raise ValueError(
            f"Invalid tournament team name: {name!r}. Use letters, numbers, "
            f"spaces, and - _ ' & . only."
        )
    if name in _RESERVED_DIVISIONS:
        raise ValueError(f"'{name}' is a reserved division name.")

    yaml_path, cfg = _load_cfg(season_id)
    divisions = cfg.setdefault("divisions", {})

    if name not in divisions:
        divisions[name] = _new_travel_division(name)
        _save_cfg(yaml_path, cfg)

    # Create the on-disk folder (idempotent) so the scraper can drop games in.
    (get_season_dir(season_id) / name).mkdir(parents=True, exist_ok=True)
    return True


def list_tournament_teams(season_id: str = None) -> list:
    """
    Return all tournament-team (travel) divisions for a season.

    Includes the built-in Wild/Storm travel divisions plus any user-added
    tournament teams. Each entry carries enough info for the UI multi-select.

    Args:
        season_id: If None, uses the active season.

    Returns:
        List of dicts sorted by name, each:
          {"name": str, "active": bool, "team_count": int, "builtin": bool}
        `builtin` is True for Wild/Storm (present in the season template) and
        False for user-added tournament teams.
    """
    if season_id is None:
        season_id = get_active_season_id()
    _, cfg = _load_cfg(season_id)

    out = []
    for div_name, div_cfg in cfg.get("divisions", {}).items():
        if div_cfg.get("type") == "league":
            continue
        out.append({
            "name": div_name,
            "active": bool(div_cfg.get("active", True)),
            "team_count": len(div_cfg.get("teams", []) or []),
            "builtin": not bool(div_cfg.get("tournament_team", False)),
        })
    return sorted(out, key=lambda d: d["name"].lower())


def set_tournament_team_active(season_id: str, name: str, active: bool) -> bool:
    """
    Toggle whether a tournament-team division is included in builds this season.

    Non-destructive: the division and any accumulated opponent data are kept;
    only the `active` flag changes. Inactive divisions are skipped by
    build_scraper_divisions() / build_hitting_divisions().

    Args:
        season_id: Season to modify.
        name:      Tournament team (travel division) name.
        active:    True to include in builds, False to exclude.

    Returns:
        True on success, False if the named travel division was not found.

    Raises:
        FileNotFoundError: If the season config does not exist.
    """
    yaml_path, cfg = _load_cfg(season_id)
    div_cfg = cfg.get("divisions", {}).get(name)
    if not div_cfg or div_cfg.get("type") == "league":
        return False
    div_cfg["active"] = bool(active)
    _save_cfg(yaml_path, cfg)
    return True


def get_season_detail(season_id: str) -> dict:
    """
    Return the editable data for a season, for the "Modify Season" form.

    Args:
        season_id: Season to load.

    Returns:
        {
            "id": str,
            "display_name": str,
            "majors_gc_id": str,
            "minors_gc_id": str,
            "tournament_teams": [ {name, active, team_count, builtin}, ... ],
        }

    Raises:
        FileNotFoundError: If the season config does not exist.
    """
    _, cfg = _load_cfg(season_id)
    divisions = cfg.get("divisions", {})

    def _org(div):
        d = divisions.get(div)
        return str(d.get("gc_org_id", "") or "") if d else ""

    return {
        "id": str(cfg.get("season_id", season_id)),
        "display_name": str(cfg.get("display_name", season_id)),
        "majors_gc_id": _org("Majors"),
        "minors_gc_id": _org("Minors"),
        "tournament_teams": list_tournament_teams(season_id),
    }


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

    print()
    print("Available seasons:")
    for s in list_seasons():
        active_marker = " ← active" if s["is_active"] else ""
        print(f"  {s['id']}  ({s['display_name']}){active_marker}")
