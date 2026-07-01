# WCWAA Scout Pipeline

This file is the authoritative reference for the WCWAA Scout pipeline.
Load it at the start of every new AI coding session (GitHub Copilot, Claude, etc.).
It covers every design decision, known bug, and operational detail accumulated
across the full build history of this project.

**Root directory (all paths relative to this):**
`~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My Drive/Baseball/WCWAA/Scout/`

**Best practices prompt:** When starting a new session, the user may paste their
"Code Mentor" prompt which defines conventions for debugging, git hygiene, error
handling, and code style. Follow those guidelines throughout.

---

## Current State

| Field | Value |
|---|---|
| **Version** | 3.3.0 |
| **Last commit** | `41929f2 / docs: rename Weekly Usage section to User Options + bump badge to 3.3.0` |
| **Branch** | `main` |
| **Uncommitted** | None — working tree clean |

### Session Handoff Protocol

When starting a new session on this project:

1. **Load this file first** — it's the authoritative context document
2. **Read the Code Mentor principles** — user may re-paste them; follow them throughout
3. **Check `git status`** — note any uncommitted changes before touching anything
4. **Check `active_season.txt`** — confirms which season config is active
5. **Scan `[Unreleased]` in CHANGELOG.md** — see what work is in-flight
6. **Review open items in BUGS.md** — check for `Open` or `In Progress` bugs

At session end, update this **Current State** table with the latest version and last commit SHA before closing.

---

## Development Environment

- **Python 3.9.6** (macOS system Python)
- **Virtual environment:** `venv/` (repo root) — shared across all components; always activate before running scripts
- **Key packages:** Playwright 1.58.0, Chromium 145, ReportLab 4.4.10
- **Frozen deps:** `requirements.txt` in repo root
- **Git:** Local repo rooted at `Scout/` on `main` branch
- **GitHub remote:** `https://github.com/mdesau/Scouting_Pipeline` (private)
  - PAT stored in `.git/config` remote URL — rotate at github.com/settings/tokens if needed

### Version History
```
v3.3.0  feat: per-tab season selectors in web UI (BUG-18) + "All seasons" View Reports filter
v3.2.1  docs: Instructions.md refactor
v3.2.0  feat: season management — list/create/switch seasons (terminal + web UI)
v3.1.3  fix: BUG-17 — newly added team missing from web UI dropdown + alphabetical sort
v3.1.2  chore: relocate repo to WCWAA/Scout/ + venv at root + AllStars into seasons/
v3.1.0  feat: web UI — local Flask server + HTML front-end (build/view/add via browser)
v3.0.0  refactor: restructure to src/ layout + YAML season config + seasons/ data dir
v2.8.0  feat: add Swing% stat to hitting reports (card footer + summary table)
v2.7.0  feat: pipeline summary log with per-team accounting + deltas + case-insensitive team matching
v2.6.1  fix: launchd auto-load on login via ~/.zprofile (resilient to GDrive mount timing)
v2.6.0  refactor: restructure to Dev/, rename gen_reports→gen_hitting, fix González regex, unify docs
v2.5.0  feat: add Pitching Savant v0.1.0, restructure repo root to Spring/
v2.4.1  fix: schedule lazy-load cutoff (scroll before extracting game cards)
v2.4.0  feat: LG RANK for Wild/Storm + No PAs diagnostic warning
v2.3.0  feat: league rank row + team totals in summary table
v2.2.0  feat: team aggregate card + team totals row in summary table
v2.1.0  chore: nightly scheduler, script renames, doc sync
v2.0.0  chore: version banner, CHANGELOG
v1.0.0  baseline: full pipeline working for all 4 divisions
v0.2.0  early development
v0.1.0  initial commit
```

---

## To Do

| # | Item | Status | Target Version | Notes |
|---|------|--------|----------------|-------|
| 1 | Optimize directory structure for growth and future seasons | ✅ Done | v3.0.0 | `src/`, `launchers/`, `config/`, `seasons/`, YAML season config |
| 2 | Build a user-friendly HTML front end ("HTML-based app") | ✅ Done | v3.1.0 | Local Flask web UI (`src/web/`): build reports with live log, view PDFs, add teams. Double-click `launchers/Start Scout.command`. Build on Mac, view anywhere (incl. mobile via Google Drive). |
| 3 | Season management — create/switch seasons without manual YAML editing | ✅ Done | v3.2.0 | `season_config.list_seasons/create_season/set_active_season`; terminal wizard `[4] Manage seasons`; web UI Seasons tab + header season picker |
| 4 | Per-tab season selectors in web UI (BUG-18) | ✅ Done | v3.3.0 | Build/View/Add Team each have their own season dropdown; View Reports has an "All seasons" option |
| 5 | Leverage stat_analysis.py work to build dynamic archetypes | 🔲 Not Started | v3.3.0 | Replace static archetype cutoffs with percentile-driven thresholds from distribution data |
| 6 | Plan migration or clone to GameChanger board path | 🔲 Not Started | TBD | Evaluate whether pipeline can run without GDrive dependency (local path portability) |

---

## Project Summary

Scout is a single automated pipeline for generating scouting reports for Weddington youth baseball. It has two report components:

| Component | Purpose | Output |
|---|---|---|
| **Hitting** | Scrapes GameChanger, computes batting stats + archetypes, generates hitting PDFs | `*-Scout-Hitting_2026.pdf` |
| **Pitching** | Reads same game files, computes pitching stats + league percentiles, generates Baseball Savant-style pitcher cards | `*-Scout-Pitching_2026.pdf` |

Both components share the same virtual environment, game file data, and scraping infrastructure. Users can run hitting only, pitching only, or both together — from the terminal menu, CLI flags, the nightly scheduler, or the **web UI** (`src/web/`, v3.1.0). All entry points ultimately drive the same `run_menu.py` pipeline.

### Divisions

| Division | Age | Teams | Scope |
|---|---|---|---|
| Majors | 11U in-house | 11 teams | Full league — reports on all opponents |
| Minors | 9U in-house | 14 teams | Full league |
| Wild | 11U travel | 10 opponent teams | Reports on travel opponents only |
| Storm | 9U travel | 17 opponent teams | Reports on travel opponents only |

---

## Scripts Overview (line counts as of v3.2.0, June 30 2026)

| Script | Lines | Component | Role |
|---|---|---|---|
| `src/hitting/gen_hitting.py` | ~2146 | Hitting | Stat engine + PDF generator |
| `src/pitching/gen_pitching.py` | ~1301 | Pitching | Stat engine + PDF generator |
| `src/orchestrator/run_menu.py` | ~1143 | Orchestrator | Pipeline orchestrator (4-step: scrape → rosters → hitting → pitching) + add-team wizard + season management |
| `src/scraping/scrape_gc_boxscores.py` | ~790 | Scraping | Playwright: GC box scores → rosters |
| `src/hitting/stat_analysis.py` | ~605 | Hitting | Distribution/percentile analysis → HTML report (feeds dynamic archetypes, To Do #4) |
| `src/scraping/scrape_gc_playbyplay.py` | ~588 | Scraping | Playwright: GC schedule → .txt game files |
| `src/season_config.py` | ~618 | Config | Central loader: reads `config/<season>.yaml`, builds DIVISIONS dicts, `add_team_to_yaml()`, season lifecycle (`list_seasons`, `create_season`, `set_active_season`) |
| `src/web/server.py` | ~521 | Web | Flask server backing the HTML front-end (build/view/add/seasons) |
| `src/scraping/parse_gc_text.py` | ~270 | Parser | Raw GC text → WCWAA format (utility) |
| `src/scraping/diag_schedule.py` | ~144 | Scraping | Schedule diagnostics (utility) |

> **Web front-end assets** (not Python): `src/web/index.html` (~169 lines), `src/web/css/style.css` (~213 lines), `src/web/js/app.js` (~441 lines).
>
> **Legacy scripts** (`pilot_card.py`, `patch_march_initials.py`, `scrape_storm.py`) were retired in the v3.0.0 restructure and removed from the repo in v3.1.0. Sample files live in `examples/`.

### Shell Launchers (all in `launchers/`)

| Script | Purpose |
|---|---|
| `launchers/Start Scout.command` | **Double-click launcher** for the web UI: activates venv, starts `src/web/server.py`, opens browser at http://127.0.0.1:5050 |
| `launchers/run_scout.sh` | Manual launcher: activates venv, calls `run_menu.py` (interactive menu or `--division`/`--team` passthrough) |
| `launchers/run_scout_nightly.sh` | Headless launcher for manual testing; calls `run_menu.py --all` |
| `~/Library/LaunchAgents/run_wcwaa_nightly.sh` | **Actual nightly launcher** (local disk): called by launchd plist, calls `run_menu.py --all` directly. Lives outside repo so launchd can execute it even if GDrive is slow to mount. |
| `launchers/run_pitching.sh` | Standalone manual launcher for pitching PDFs only |
| `launchers/run_pitching_nightly.sh` | Standalone headless launcher for pitching PDFs only |
| `launchers/com.wcwaa.scout_pipeline.plist` | launchd schedule config (symlinked to `~/Library/LaunchAgents/`) |

---

## Directory Structure

```
Spring/                              <- git repo root (v3.1.0)
|-- .git/
|-- .gitignore
|-- README.md                        <- project overview
|-- Instructions.md                  <- this file
|-- CHANGELOG.md                     <- unified version history
|-- BUGS.md                          <- unified bug tracker
|-- requirements.txt                 <- pip freeze (Flask, Playwright, ReportLab, PyYAML)
|
|-- config/                          <- season configuration (the only place teams live)
|   |-- 2026-spring.yaml             <- single source of truth: GC IDs, slugs, coaches, paths
|   |-- season_template.yaml         <- scaffold for new seasons (used by create_season())
|   +-- active_season.txt            <- one line: "2026-spring" (switch seasons here)
|
|-- src/                             <- all Python source
|   |-- season_config.py             <- central loader: SCOUT_ROOT, SEASON_DIR,
|   |                                    build_scraper_divisions(), build_hitting_divisions(),
|   |                                    add_team_to_yaml(), list_seasons(), create_season(),
|   |                                    set_active_season(). Every script imports from here.
|   |-- hitting/
|   |   |-- gen_hitting.py            <- Step 3: stat engine + hitting PDFs
|   |   |-- stat_analysis.py          <- distribution/percentile analysis -> HTML report
|   |   +-- archetype_reference.txt   <- archetype system design notes
|   |-- pitching/
|   |   |-- gen_pitching.py           <- Step 4: stat engine + pitching PDFs
|   |   +-- pitcher_icon.png          <- Savant-style pitcher silhouette
|   |-- scraping/
|   |   |-- scrape_gc_playbyplay.py   <- Step 1: GC schedule -> .txt game files
|   |   |-- scrape_gc_boxscores.py    <- Step 2: GC box scores -> rosters
|   |   |-- parse_gc_text.py          <- utility: raw GC text -> WCWAA format
|   |   +-- diag_schedule.py          <- utility: schedule diagnostics
|   |-- orchestrator/
|   |   +-- run_menu.py               <- pipeline orchestrator (Steps 1-4) + add-team + season management
|   +-- web/                          <- HTML front-end (v3.1.0)
|       |-- server.py                 <- Flask server (build/view/add endpoints + live log SSE)
|       |-- index.html                <- single-page app shell
|       |-- css/style.css
|       +-- js/app.js
|
|-- launchers/                       <- all shell scripts + launchd plist
|   |-- Start Scout.command           <- double-click: start web UI + open browser
|   |-- run_scout.sh                  <- manual launcher (interactive menu)
|   |-- run_scout_nightly.sh          <- headless launcher (manual testing)
|   |-- run_pitching.sh               <- standalone pitching launcher
|   |-- run_pitching_nightly.sh       <- standalone headless pitching launcher
|   +-- com.wcwaa.scout_pipeline.plist <- launchd schedule (symlinked to ~/Library/LaunchAgents/)
|
|-- sessions/                        <- [gitignored]
|   +-- gc_session.json               <- Playwright GC login session
|-- logs/                            <- [gitignored]
|   +-- pipeline_summary.log          <- appended each run (per-team accounting)
|
|-- seasons/                         <- [gitignored] all season data
|   +-- 2026-spring/
|       |-- Majors/Reports/           <- Scorebooks/, Scouting_Reports/, rosters.json, box_verify.json
|       |-- Minors/Reports/           <- same structure
|       |-- Wild/[TeamName]/           <- Games/, roster.txt, *-Scout-*.pdf
|       |-- Storm/[TeamName]/          <- same structure
|       +-- Coach_Pitch/
|
+-- Dev/
    +-- venv/                         <- shared Python venv [gitignored]
```

> **Note:** The repo root is still physically named `Spring/` on disk; all code uses
> relative paths anchored to `__file__` (via `season_config.py`), so the folder can be
> renamed freely without touching any script.

---

## Pipeline Workflow

The pipeline runs 4 steps, orchestrated by `run_menu.py`:

| Step | Script | What it does |
|---|---|---|
| 1 | `scrape_gc_playbyplay.py` | Scrapes GC schedule pages, downloads play-by-play, saves .txt game files |
| 2 | `scrape_gc_boxscores.py` | Scrapes GC box scores, builds/updates rosters.json + roster.txt |
| 3 | `gen_hitting.py` | Parses game files, computes batting stats + archetypes, generates hitting PDFs |
| 4 | `gen_pitching.py` | Parses same game files, computes pitching stats + percentiles, generates pitching PDFs |

Step 1 skips games already on disk (safe to re-run). Step 2 is incremental by default.

After all 4 steps, `run_menu.py` appends a **pipeline summary** to `logs/pipeline_summary.log` — per-division and per-team accounting with game counts, PAs, and deltas vs. the previous run.

### Running the Pipeline

**Option A -- web UI (easiest):**
```bash
# Double-click launchers/Start Scout.command in Finder, or:
bash "launchers/Start Scout.command"
# Opens http://127.0.0.1:5050 — build, view, and add teams from the browser.
```

**Option B -- interactive menu:**
```bash
bash launchers/run_scout.sh
```

**Option B -- nightly scheduled (launchd at 10am EDT):**
```bash
launchctl list | grep wcwaa          # verify scheduler active
launchctl start com.wcwaa.scout_pipeline  # trigger immediately
```

> **Execution chain:** plist → `~/Library/LaunchAgents/run_wcwaa_nightly.sh` (local disk) → `run_menu.py --all`
>
> **Auto-load:** `~/.zprofile` re-registers the job on every login so it survives
> reboots even when Google Drive mounts late. No manual `launchctl load` needed.

**Option C -- CLI direct:**
```bash
# Full pipeline, all divisions
bash launchers/run_scout.sh --all

# Single division
bash launchers/run_scout.sh --division Wild

# Single team
bash launchers/run_scout.sh --division Majors --team "Cubs-Holtzer"

# Pitching only (standalone)
bash launchers/run_pitching.sh --division Majors
```

**Step-by-step manual:**
```bash
python3 src/scraping/scrape_gc_playbyplay.py                 # Step 1
python3 src/scraping/scrape_gc_boxscores.py                  # Step 2
python3 src/hitting/gen_hitting.py --division Majors          # Step 3
python3 src/pitching/gen_pitching.py --division Majors        # Step 4
```

---

## Function Map -- Hitting Component

### scrape_gc_playbyplay.py (Step 1 -- Playwright scraper)
Navigates GC schedule pages, finds FINAL games, downloads play-by-play text, converts via `parse_gc_text.py`, saves `.txt` game files.

| Function | ~Line | Purpose |
|---|---|---|
| `run()` | ~511 | CLI entry point -- parses `--division`, `--team`, `--login`, `--check`, `--force`, `--verbose`; loops divisions |
| `scrape_org_division()` | ~361 | Org-level scraper (Majors/Minors): loads org schedule, finds FINAL games |
| `scrape_team_division()` | ~431 | Team-level scraper (Wild/Storm): loads per-team schedule page |
| `extract_plays_raw()` | ~336 | Navigates to `/plays` URL, extracts raw page text via Playwright |
| `is_covered()` | ~355 | Checks whether a game file already exists on disk (skip logic) |
| `get_schedule()` | ~321 | Runs `SCHEDULE_JS` in browser, returns parsed schedule array |
| `setup_logging()` | ~87 | Configures file + console logging with `--verbose` support |
| `fmt_date()` | ~307 | Normalizes GC date strings to `MonDD` format for filenames |
| `safe()` | ~316 | Sanitizes team name for use in filenames |
| `SCHEDULE_JS` | ~130 | JS injected into browser to extract game cards from GC's React DOM |
| `DIVISIONS` dict | built at import | `build_scraper_divisions()` from `season_config` (loaded from `config/<season>.yaml`) -- **do NOT edit here; edit the YAML or use the add-team wizard** |

**Dependencies:** `parse_gc_text.parse_gc_raw()`, `season_config.build_scraper_divisions()`, `sessions/gc_session.json`

### scrape_gc_boxscores.py (Step 2 -- Playwright scraper)
Navigates GC `/box-score` pages, extracts player names + jersey numbers + AB/BB/SO, builds rosters.json (Majors/Minors) and roster.txt (Wild/Storm), writes box_verify.json.

| Function | ~Line | Purpose |
|---|---|---|
| `run()` | ~798 | CLI entry point -- parses `--division`, `--team`, `--force`, `--verbose` |
| `scrape_division()` | ~515 | Org-level scraper (Majors/Minors) |
| `scrape_team_division()` | ~649 | Team-level scraper (Wild/Storm) |
| `_accum_player()` | ~385 | Core per-player accumulator: detects collisions, promotes to 5-char keys |
| `_prepare_for_save()` | ~491 | Strips transient fields before writing to disk |
| `merge_player()` | ~324 | Merges new box score data into existing roster entry |
| `_first_name_from()` | ~355 | Extracts first name from GC display string |
| `_disambig_key()` | ~376 | Builds 5-char disambiguation key (e.g. `B A` -> `Bri A`) |
| `display_name()` | ~305 | Formats `"FirstName L. #jersey"` display string |
| `normalize_team_name()` | ~288 | Applies `TEAM_NAME_ALIASES` to fix GC name differences |
| `setup_logging()` | ~125 | Configures logging |
| `DIVISIONS` dict | built at import | `build_scraper_divisions()` from `season_config` (same source as scrape_gc_playbyplay.py -- always in sync) |
| `TEAM_NAME_ALIASES` | ~60 | Maps GC box score team name variants -> canonical keys |

**Known limitation:** Minors `/box-score` pages redirect to `/info` -- jersey numbers permanently unavailable.

### gen_hitting.py (Step 3 -- Hitting stat engine + PDF generator)
Reads game `.txt` files, parses every plate appearance, computes batting stats + archetypes, generates multi-page PDF scouting reports via ReportLab.

| Function | ~Line | Purpose |
|---|---|---|
| `main()` | ~2031 | CLI entry point -- parses `--division`, `--team`, `--verbose` |
| `run_league()` | ~1729 | Division runner for Majors/Minors |
| `run_wild()` | ~1863 | Travel division runner (Wild/Storm): two-pass with LG RANK |
| `build_league_context()` | ~1675 | Pre-scans all scorebooks; returns league-wide percentile data |
| `get_wild_opponents()` | ~1625 | Discovers Wild/Storm opponent folders on disk |
| `load_wild_roster()` | ~1639 | Reads `roster.txt` for a travel opponent |
| `generate_pdf()` | ~1408 | ReportLab PDF assembly: team card + player cards + summary/notes |
| `draw_card()` | ~1299 | Renders one player or team card: spray chart, stat bars, archetype, 4-stat footer (Sw%, SM%, CStr%, FPT%) |
| `draw_field_spray_chart()` | ~1171 | Heat-map spray chart with BIP dots |
| `draw_stat_box()` | ~1272 | Renders a single stat label + value box |
| `draw_bar()` | ~1279 | Renders a horizontal percentage bar |
| `draw_header()` | ~1100 | Draws PDF page header |
| `mark_reviewed()` | ~1071 | Renames processed game file to `-Reviewed.txt` |
| `generate_notes()` | ~997 | Full narrative scouting note for a batter |
| `generate_notes_short()` | ~1042 | Compact note for summary page |
| `get_pitching_approach()` | ~989 | Archetype -> pitching recommendation lookup |
| `get_archetype()` | ~865 | Applies Approach x Result label using percentiles |
| `_roster_percentiles()` | ~848 | Computes league-wide percentile thresholds |
| `_rank_stat()` | ~807 | Dense rank helper for LG RANK row |
| `compute_team_totals()` | ~728 | Aggregates all batters -> single team-level stat dict |
| `compute_stats()` | ~614 | Aggregates PA list -> per-batter stat dict |
| `verify_game()` | ~582 | Runs all verification layers on a parsed game |
| `check_batting_order()` | ~523 | Verification layer 3 |
| `check_inning_continuity()` | ~493 | Verification layer 1 |
| `parse_game_for_team()` | ~430 | Core parser: reads .txt file, extracts PAs per batter |
| `parse_pitch_seq()` | ~389 | Parses pitch sequence string into swing/take/foul counts |
| `parse_outcome()` | ~340 | Maps play description -> outcome code |
| `parse_ball_type()` | ~327 | Classifies BIP as ground ball, fly ball, or line drive |
| `extract_zone()` | ~322 | Extracts fielding zone for spray chart |
| `verify_box_score()` | ~262 | Verification layer 4: cross-checks vs box_verify.json |
| `_disambiguate_pas()` | ~213 | Splits shared-initials PAs using `_collision_map` |
| `load_box_verify()` | ~202 | Loads box_verify.json |
| `load_box_rosters()` | ~159 | Loads rosters.json |
| `setup_logging()` | ~43 | Configures logging |
| `DIVISIONS` dict | built at import | `build_hitting_divisions()` from `season_config` (folder paths + roster file locations, loaded from YAML) |
| `INNING_RE` | ~420 | Regex for `===Top/Bottom N - TeamName===` headers |
| `PITCHING_APPROACH` | ~952 | Archetype -> pitching recommendation lookup dict |

### parse_gc_text.py (Utility)
Converts raw GC page text into WCWAA-structured `.txt` game file format. Called by `scrape_gc_playbyplay.py` -- never run directly.

| Function | ~Line | Purpose |
|---|---|---|
| `parse_gc_raw()` | ~80 | Main entry: raw text string -> formatted game file string |
| `GC_NAME_FIXES` | ~20 | Dict of known GC data errors to auto-correct |
| `OUTCOME_TYPES` | ~35 | Outcome string -> code mapping (must sync with gen_hitting.py) |

### season_config.py (Central Config Loader)
Gateway module — every script imports from here. Reads `active_season.txt` → loads `config/<season>.yaml` → exposes all season data as module-level constants and helper functions. Also manages the season lifecycle (create, list, switch).

| Function / Constant | ~Line | Purpose |
|---|---|---|
| `SCOUT_ROOT` | ~150 | Absolute path to repo root (derived from `__file__`) |
| `SEASON_ID` | ~153 | Active season ID (`"2026-spring"`) — read from `active_season.txt` at import |
| `SEASON_DIR` | ~155 | `seasons/<season_id>/` data directory |
| `build_scraper_divisions()` | ~200 | Builds `DIVISIONS` dict for scraping scripts (GC org ID, team slugs, team IDs) |
| `build_hitting_divisions()` | ~265 | Builds `DIVISIONS` dict for hitting/pitching scripts (folder paths, roster files) |
| `add_team_to_yaml()` | ~330 | Adds a new Wild/Storm team to the active season YAML (idempotent) |
| `list_seasons()` | ~370 | Scans `config/*.yaml` (excluding template); returns `[{id, display_name, is_active}]` |
| `set_active_season()` | ~410 | Writes a new season ID to `active_season.txt`; guards for missing config |
| `create_season()` | ~440 | Scaffolds a new season YAML from `season_template.yaml` (fills GC IDs, display name); calls `_scaffold_season_dirs()` |
| `_scaffold_season_dirs()` | ~560 | Private helper — creates on-disk folder tree for a new season (`seasons/<id>/Majors/`, `Minors/`, `Wild/`, `Storm/`) |

> **Important:** `SEASON_ID` and `SEASON_DIR` are module-level constants resolved at import time.
> Calling `set_active_season()` updates `active_season.txt` on disk, but the **running process still
> uses the old values** until restarted. All season-switch responses include a `restart_required` flag.

### run_menu.py (Orchestrator)
Interactive numbered menu + CLI passthrough. Calls Steps 1->2->3->4 as subprocesses.

| Function | ~Line | Purpose |
|---|---|---|
| `main()` | ~1091 | CLI entry point -- parses `--all`, `--division`, `--team` |
| `interactive_menu()` | ~1019 | Menu: [0] Full, [1] Division, [2] Team, [3] Add team, [4] Manage seasons |
| `manage_seasons()` | ~963 | Sub-menu: [1] Switch season, [2] Create season, [B] Back |
| `_switch_season_wizard()` | ~920 | Lists all seasons → user picks one → calls `set_active_season()` → prints restart notice |
| `_create_season_wizard()` | ~840 | Interactive wizard: season ID, display name, Majors/Minors GC org IDs → `create_season()` → prints next-steps |
| `add_new_team()` | ~752 | Wizard: paste GC URL → `add_team_to_yaml()` + creates `seasons/<season>/<Div>/<Team>/Games/` |
| `_slug_to_folder_name()` | ~713 | Converts GC slug to folder name |
| `_parse_gc_url()` | ~689 | Extracts `team_id` and `slug` from a GC schedule URL |
| `_run()` | ~662 | Subprocess wrapper with exit-code handling |
| `run_pipeline()` | ~251 | Runs steps 1->2->3->4 as subprocesses for given scope |
| `get_team_list()` | ~218 | Wild/Storm: reads DIVISIONS tuples (sorted alphabetically); Majors/Minors: reads rosters.json keys |
| `print_header()` | ~85 | Prints the menu banner; season name is dynamic from `SEASON_ID` (not hardcoded) |
| `check_session()` | ~147 | Warns if `sessions/gc_session.json` is missing |

> **Team additions** now write to `config/<season>.yaml` via `season_config.add_team_to_yaml()`
> (the old `_insert_team_into_file()` text-replacement on Python source was removed in v3.0.0).

**Step 4 integration:** `run_pipeline()` calls `gen_pitching.py` via `_PITCHING_SCRIPT = _SRC_DIR / "pitching" / "gen_pitching.py"` after gen_hitting.py.

### server.py (Web UI -- v3.2.0)
Local Flask server that backs the HTML front-end. Reuses `get_team_list()`, `_parse_gc_url()`,
`_slug_to_folder_name()` from run_menu.py and `add_team_to_yaml()`, `list_seasons()`, `set_active_season()`,
`create_season()` from season_config (DRY).
Builds run by shelling out to `run_menu.py --division X --team Y` (same proven path as the
terminal menu + nightly cron), streaming live output to the page via Server-Sent Events.

| Endpoint | Purpose |
|---|---|
| `GET /` + `/css/*` + `/js/*` | Serve the single-page app |
| `GET /api/divisions` | Divisions + team lists (fresh call each request — BUG-17 fix) |
| `GET /api/reports` | Scan `seasons/<id>/` for `*-Scout-{Hitting,Pitching}_*.pdf`, grouped by division/team |
| `GET /report/<path>` | Stream a PDF (with path-traversal protection — must resolve inside `seasons/`) |
| `GET /api/run?division=&team=` | Build reports; stream live log via SSE; guarded by a single-run lock |
| `POST /api/add_team` | Add a Wild/Storm opponent from a GC URL |
| `GET /api/seasons` | Returns all seasons + active ID (`list_seasons()` fresh each call) |
| `POST /api/seasons/active` | Switches active season; returns `restart_required: true` |
| `POST /api/seasons` | Creates a new season from wizard data (`create_season()`) |

**Config flags (env):** `SCOUT_WEB_HOST` (default `127.0.0.1`), `SCOUT_WEB_PORT` (default `5050`),
`SCOUT_WEB_DEBUG` (`0`/`1`). Set `SCOUT_WEB_HOST=0.0.0.0` to reach the build UI from another
device on the same Wi-Fi. The build subprocess runs with `python -u` + `PYTHONUNBUFFERED=1`
so log lines stream live instead of arriving in one dump.

---

## Function Map -- Pitching Component

### gen_pitching.py (Step 4 -- Pitching stat engine + PDF generator)
Reads game `.txt` files from the opponent's perspective (who was pitching), computes 13 pitching stats, ranks all pitchers in the division by percentile, generates Baseball Savant-style pitcher profile cards with colored slider bars.

**Config source:** `DIVISIONS` is built from `season_config.build_hitting_divisions()` (team IDs, slugs, and folder paths all come from `config/<season>.yaml`). Uses the shared venv. No inter-script imports — it has its own local `parse_outcome()`/`parse_ball_type()`/`parse_pitch_seq()`.

| Function | ~Line | Purpose |
|---|---|---|
| `setup_logging()` | ~103 | Configures file + console logging |
| **Parsing** | | |
| `parse_outcome()` | ~189 | Maps play description -> outcome code (mirrors gen_hitting.py) |
| `parse_ball_type()` | ~235 | Classifies BIP as GB, FB, or LD |
| `parse_pitch_seq()` | ~254 | Parses pitch sequence -> swing/take/foul/ball/strike counts |
| `parse_game_for_pitching_team()` | ~293 | Core parser: reads .txt file, extracts PAs attributed to each pitcher. Uses carry-forward logic for pitcher tracking + pre-scan to skip games not involving the team |
| **Stats** | | |
| `compute_pitcher_stats()` | ~444 | Aggregates all PAs for one pitcher -> 13-stat dict (ERA-proxy, WHIP, K/9, BB/9, K%, BB%, K/BB, BABIP, HR/9, FPSH%, GB%, FB+LD%, C%) |
| `compute_percentile_rank()` | ~586 | Ranks a value against all values in the division; supports `low_is_good` flip |
| `compute_all_percentiles()` | ~626 | Builds percentile rows for every pitcher across all 13 stats |
| **PDF Rendering** | | |
| `pct_to_color()` | ~719 | Maps percentile (0-100) to red->yellow->green color |
| `draw_gradient_bar()` | ~728 | Draws the colored Savant-style slider bar |
| `draw_bubble()` | ~736 | Draws the percentile bubble on the slider |
| `draw_axis_labels()` | ~748 | Draws "Poor" / "Great" axis labels |
| `draw_stat_row()` | ~761 | Renders one stat row: label, value, slider bar, percentile bubble |
| `draw_pitcher_icon()` | ~798 | Draws the Savant pitcher silhouette PNG in card header |
| `draw_pitcher_card()` | ~828 | Renders a complete pitcher card (header + 13 stat rows) |
| `card_origin()` | ~875 | Computes x,y position for 4-cards-per-page layout |
| `generate_pitching_pdf()` | ~884 | Assembles full PDF: pages of 4 cards each |
| **File I/O** | | |
| `find_game_files()` | ~912 | Finds .txt and -Reviewed.txt game files in a directory |
| `load_rosters_json()` | ~932 | Loads rosters.json for Majors/Minors display names |
| `load_roster_txt()` | ~940 | Loads roster.txt for Wild/Storm display names |
| `dedup_pitcher_names()` | ~964 | Merges initials-only entries into full-name counterparts (e.g. "K D" -> "Kilean D"); discards unresolvable orphan initials |
| **Division Runners** | | |
| `run_league_division()` | ~1018 | Runs Majors or Minors: two-pass (collect all pitchers -> compute percentiles -> generate per-team PDFs) |
| `run_travel_division()` | ~1141 | Runs Wild or Storm: auto-discovers team folders, applies dedup, same two-pass flow |
| `main()` | ~1282 | CLI entry point -- parses `--division`, `--team`, `--verbose` |

### Pitching Stats Computed (13 stats, 2 flipped)

| Stat | Formula | Direction |
|---|---|---|
| ERA-proxy | (ER / IP) x 9 -- ER estimated as (H+BB+HBP-K) x 0.3 | Low is good |
| WHIP | (H + BB) / IP | Low is good |
| K/9 | (K / IP) x 9 | High is good |
| BB/9 | (BB / IP) x 9 | **Low is good (flipped)** |
| K% | K / PA | High is good |
| BB% | BB / PA | Low is good |
| K/BB | K / BB | High is good |
| BABIP | (H - HR) / (AB - K - HR + SF) | Low is good |
| HR/9 | (HR / IP) x 9 | Low is good |
| FPSH% | First-pitch strikes+hits / PA | **Low is good (flipped)** |
| GB% | Ground balls / BIP | High is good |
| FB+LD% | (Fly balls + line drives) / BIP | Low is good |
| C% | Contact % = (AB - K) / AB | Low is good |

### Card Design
- 4 cards per page, amber header (#f5a623), dark navy text (#1a2b4a)
- Baseball Savant pitcher silhouette PNG icon
- Each stat row: label, raw value, colored slider bar (red->green), percentile bubble
- Card background: 0.91 grey
- Header fonts: 11.5pt name, 9pt team/IP line

---

## Game File Format

```
GAME: Mon Mar 15 | https://web.gc.com/teams/.../plays

===Top 1st - T24 Garnet 11U===
Single | | Strike 1 looking, In play.
B A singles to left fielder.
Walk | | Ball 1, Ball 2, Ball 3, Ball 4.
S K walks, J R pitching.
===Bottom 1st - Dilworth 11U - Navy===
...
```

**Critical rules:**
- `INNING_RE` does exact string matching on team name in `===` headers
- Wild/Storm folder names MUST exactly match the GC inning header spelling
- Majors/Minors team key is `TeamName-CoachLast` (e.g. `Cubs-Holtzer`)
- Pitching component uses `, [NAME] pitching` lines to track pitcher changes

---

## Roster Format

### Majors/Minors -- rosters.json
```json
{
  "Cubs-Holtzer": {
    "S K":  { "display": "Sullivan K. #12", "jersey": "12", "ab": 40 },
    "Bri A": { "display": "Brian A. #5", "jersey": "5" },
    "_collision_map": { "B A": ["Bri A", "Ben A"] }
  }
}
```

### Wild/Storm -- roster.txt
```
# T24 Garnet 11U -- roster.txt
T M, Tyler M. #4
S G, Srijan G. #11
```

---

## Duplicate Initials Handling (Brian/Ben Allen Bug)

**Problem:** Two players share initials `B A` on Cubs-Holtzer.
**Fix:** `scrape_gc_boxscores.py` promotes both to 5-char keys (`Bri A`, `Ben A`) and writes `_collision_map`. `gen_hitting.py._disambiguate_pas()` alternates PA assignments by batting order.

---

## Verification System (4 Layers)

| Layer | Check | Severity |
|---|---|---|
| 1 | Inning continuity -- no skipped innings | Log only |
| 2 | Unknown outcomes -- unrecognised play descriptions | WARNING (stdout) |
| 3 | Batting order -- PA counts consistent with lineup | Log only |
| 4 | Box score cross-check -- parsed AB/BB vs. box_verify.json | Log only |

None stop PDF generation.

---

## Archetype System (Hitting Reports)

Each player card shows a 2-word label: **Approach x Result**.

**Approach** (plate discipline): Aggressive, Passive, or Disciplined
**Result** (league-relative): Walker, Overmatched, Power, or Contact

Cards with 5-9 PA show `*` suffix. Fewer than 5 PA: `--`.

**Pitching approach matrix:**

| Archetype | Recommendation |
|---|---|
| Aggressive Power/Contact | Edges + Mix Speed |
| Aggressive Overmatched | Climb the Ladder |
| Aggressive Walker | Outside - In |
| Disciplined Power/Contact | Keep Mixing |
| Disciplined Overmatched/Walker | Attack the Zone |
| Passive Power/Contact | Attack & Expand |
| Passive Overmatched/Walker | Attack the Zone |

---

## Adding a New Wild or Storm Opponent

Teams live in `config/<season>.yaml` — **never** edited into Python source anymore. Three ways:

1. **Web UI (easiest):** Start Scout.command -> "Add Team" tab -> paste the GC schedule URL.
2. **Terminal menu:** `bash launchers/run_scout.sh` -> option [3] "Add new team".
3. **Manual:** add a `{name, gc_id, gc_slug}` entry under `divisions.Wild.teams` (or `Storm`) in the YAML,
   then create `seasons/<season>/<Div>/<Exact Team Name>/Games/`.

All three call `season_config.add_team_to_yaml()` (idempotent — guards duplicates) and create the
`Games/` folder. The folder name MUST match the GC inning-header spelling exactly; verify it after
the first game is scraped.

## Starting a New Season

Use the season management wizard — no more manual file copying:

1. **Web UI:** Seasons tab -> "Create New Season" form.
2. **Terminal:** `bash launchers/run_scout.sh` -> option [4] "Manage seasons" -> [2] "Create".

Both call `season_config.create_season()`, which:
- Copies `config/season_template.yaml` to `config/<season-id>.yaml`
- Fills in the GC org IDs you provide (Majors + Minors change each season)
- Creates `seasons/<season-id>/Majors/`, `Minors/`, `Wild/`, `Storm/` folder tree
- Optionally sets the new season as active immediately

Wild/Storm team lists start empty — add opponents via "Add Team" as games are scheduled.
After switching seasons, **restart the terminal session or web server** so `SEASON_ID` reloads.

---

## Teams Reference (Spring 2026)

> Source of truth: `config/2026-spring.yaml`. Counts: Majors 11, Minors 14, Wild 10, Storm 18.

### Majors (11 teams)
Guardians-Esau, Royals-Hall, Diamondbacks-Vandiford, Marlins-McLendon,
Dodgers-Pearson, A's-Blanco, Braves-Rue, Twins-Ewart, Padres-Schick,
Cubs-Holtzer (has B A collision map), Rays-Madero

### Minors (14 teams)
Astros-Barbour, Dodgers-Winchester, Padres-Midkiff, Reds-Naturale,
Rangers-Leonard, Yankees-DePasquale, Marlins-Eberlin, Guardians-Plunkett,
Angels-Casper, Braves-Brooks, Cubs-Verlinde, Brewers-Linnenkohl,
Rays-Pearson, Mets-Hornung

### Wild (10 teams, 11U travel)
Arena National Browning 11U, South Charlotte Panthers 11U, Weddington Wild 11U,
QC Flight Baseball 11U, T24 Garnet 11U, SBA Alabama National 12U,
TN Nationals Heichelbech 12U, Tega CAY Titans 11U, Weddington Vipers 12U,
Mara Bulls 8U 8U

### Storm (18 teams, 9U travel)
ITAA 9U Spartans, MARA 9U Stingers, South Charlotte Challenge 9U Doggett,
Pineville Blue Sox 9U, LKN Lightning 10U, Park Sharon Nationals 10U,
Weddington Stormtroopers, Lake Norman Lightning 9U, Dilworth 9U - Navy,
Crushers White 10U, Weddington 10U Gophers, Titans 9U, Mara Outlaws 9U,
Eagles 9U, Shelby Storm 9U, Carolina River Rats 9U, LKN Storm 9U,
Carolina Locos Black 9U

---

## Prerequisites (First-Time Setup)

```bash
cd .../Scout
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python3 src/scraping/scrape_gc_playbyplay.py --login   # save GC session
```

---

## Stat Formulas Reference (Hitting)

| Stat | Formula |
|---|---|
| PA | All plate appearances (BB + HBP + AB + SF + SB) |
| AB | PA - (BB + HBP + SF + SB) |
| AVG | H / AB |
| OBP | (H + BB + HBP) / (AB + BB + HBP) |
| SLG | TB / AB |
| C% | (AB - K_total) / AB |
| GB% | Ground ball BIP / total BIP |
| FB+LD% | (Fly ball + line drive BIP) / total BIP |
| Swing% | Total swings (miss + foul + in-play) / total pitches seen |
| SM% | Swing-and-miss / total swings |
| CStr% | Called strikes / total pitches seen |
| FPT% | First-pitch takes / (takes + swings on first pitch) |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `0 PAs` for a team | Team name mismatch (folder vs. inning header) | Check exact spelling in game file header vs. folder name |
| `?F L?` in output | Player initials not in rosters.json | Run scrape_gc_boxscores.py; or add to roster_additions |
| `WARNING UNKNOWN` | Play outcome not in OUTCOME_TYPES | Add to parser |
| Jersey numbers missing (Minors) | Box scores inaccessible | Known permanent limitation |
| Session expired error | gc_session.json expired | `python3 src/scraping/scrape_gc_playbyplay.py --login` |
| High pitcher count (Wild/Storm) | Initials-only names not deduped | Check dedup_pitcher_names() logic |
| Player with accented name missing | Regex uses ASCII-only char class | Verify `[a-z\u00C0-\u024F]` in regex (BUG-16 fix) |
