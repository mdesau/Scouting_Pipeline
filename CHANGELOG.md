# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Components:** Hitting (`gen_hitting.py`), Pitching (`gen_pitching.py`), Scraping (`scrape_gc_playbyplay.py`, `scrape_gc_boxscores.py`), Orchestrator (`run_menu.py`), Web UI (`src/web/server.py`)

---

## [Unreleased]
<!-- Daily/nightly work-in-progress goes here. Move to a versioned section when tagging. -->

---

## [3.2.0] - 2026-06-30

### Added — Season Management

- **`season_config.py`** — Three new functions for season lifecycle management:
  - `list_seasons()` — scans `config/*.yaml`, returns id/display_name/is_active for each
  - `set_active_season()` — writes `active_season.txt`; guards against missing configs
  - `create_season()` — scaffolds new season from `config/season_template.yaml`: fills in GC org IDs, auto-derives display name, creates `seasons/<id>/` folder tree (Scorebooks, Scouting_Reports, Wild/, Storm/)
  - `_scaffold_season_dirs()` — private helper that creates the on-disk folder structure

- **`config/season_template.yaml`** — Well-commented scaffold for new seasons. Empty team lists for all 4 divisions; placeholder GC org IDs. Never set as active directly — used by `create_season()`.

- **Terminal menu (`run_menu.py`)** — Season management sub-menu:
  - `[4] Manage seasons` option in the main menu
  - `manage_seasons()`: sub-menu with Switch / Create / Back
  - `_switch_season_wizard()`: lists all seasons, activates chosen, prints restart notice
  - `_create_season_wizard()`: prompts for season ID, display name, Majors + Minors GC org IDs; confirms summary; calls `create_season()`; prints next-steps
  - `print_header()`: season name now dynamic (`SEASON_ID`) — no longer hardcoded

- **Web UI (`server.py` + `index.html` + `app.js` + `style.css`)** — Season management in the browser:
  - `GET /api/seasons` — returns all seasons + active ID
  - `POST /api/seasons/active` — switches active season; returns `restart_required: true`
  - `POST /api/seasons` — creates new season (same args as `create_season()`)
  - Header season dropdown (`#seasonSelect`): switches season with confirmation + restart notice; hidden in view-only mode
  - New **Seasons tab**: existing seasons list with Activate buttons + Create New Season form (season ID, display name, Majors/Minors GC IDs, set-active checkbox)

### Changed
- **`run_menu.py` version** bumped to `3.2.0`
- **New season workflow** in `season_config.py` docstring updated to reflect automated wizard (no more manual file copy)

---

## [3.1.3] - 2026-06-30

### Fixed
- **Newly added Wild/Storm team missing from web UI dropdown** (Web UI) — `api_divisions()` was serving a startup-time snapshot of division data; now reads YAML fresh on every request so teams added via "Add Team" appear immediately without a server restart. (BUG-17)

### Changed
- **Teams sorted alphabetically in all dropdowns and terminal menus** (Web UI + Orchestrator) — Wild/Storm team lists were previously returned in YAML insertion order. Now sorted alphabetically in `api_divisions()` (web UI) and `get_team_list()` (terminal menu), matching the existing Majors/Minors sort behavior.

---

## [3.1.2] - 2026-06-29

### Changed
- **Repository relocated** — moved from `WCWAA/2026/Spring/` to `WCWAA/Scout/` (out of the season-year folder). Completes the rename that was deferred during the v3.0.0 restructure. All code uses relative paths anchored to `__file__`, so no source logic changed; git history, remote, and tags carried over intact.
- **Virtual environment moved to repo root** — `Dev/venv/` → `venv/`, rebuilt fresh after the move (venvs hard-code absolute paths). All launchers and the outside-repo nightly launchd wrapper (`~/Library/LaunchAgents/run_wcwaa_nightly.sh`) updated to the new path.
- **`run_menu.py` version** — bumped from a stale `2.1.0` to `3.1.2`.

### Moved
- **AllStars one-time builds** — `AllStars-9u/` and `AllStars-12u/` relocated into `seasons/2026-spring/AllStars/{9U,12U}/` as team folders (script + reports travel together), keeping these dead one-time builds out of the tracked repo.

### Removed
- **Empty pre-v3.0.0 shells** — `Dev/Hitting_Scout/`, `Dev/Pitching_Savant/`, and `Scout_Development/` (all gitignored leftovers) deleted, along with a stray `src/Logs/`.
- **Dead `.gitignore` rules** — pruned ignore entries for the removed `Dev/...`, `Scout_Development/`, and `AllStars-9u|12u/` paths.

---

## [3.1.1] - 2026-06-29

### Documentation
- **README.md + Instructions.md accuracy pass** — fixed all stale pre-v3.0.0 paths (`Dev/Hitting_Scout/Scripts/` → `src/...`), corrected division counts (Wild 8→10, Storm 12→17), refreshed the directory tree, scripts overview, launchers table, function maps, add-team workflow, teams reference, and prerequisites to match the v3.1.0 layout.
- **Web UI documented** — added Web UI sections to README (usage Option A) and Instructions (`server.py` endpoint map + config flags); README version badge 2.8.0 → 3.1.0.

### Removed
- **Orphaned legacy files** retired in the v3.0.0 restructure but still tracked: `pilot_card.py`, `patch_march_initials.py`, `scrape_storm.py`, three dev-artifact PDFs, and a stray `Scout_Development/` log.
- **`examples/`** relocated from `Dev/Hitting_Scout/examples/` to the repo root.

---

## [3.1.0] - 2026-06-29

### Added — Web UI (HTML front-end)
- **`src/web/server.py`** — Local Flask server (loopback `127.0.0.1:5050` by default) that puts a clean graphical front-end on the pipeline. It is the visual replacement for the `run_menu.py` text menu — same capabilities, friendlier experience.
  - `GET /api/divisions` — divisions + team lists (reuses `get_team_list()` so the web UI and terminal menu always match)
  - `GET /api/reports` — scans `seasons/<id>/` for every `*-Scout-{Hitting,Pitching}_<year>.pdf` and groups them by division/team
  - `GET /report/<path>` — streams a PDF for in-browser viewing (with path-traversal protection — paths are confirmed inside `seasons/` before serving)
  - `GET /api/run?division=&team=` — builds reports and **streams the live log** to the page via Server-Sent Events (shells out to `run_menu.py`, the same proven path the terminal + nightly cron use — DRY). Guarded by a single-run lock.
  - `POST /api/add_team` — registers a new Wild/Storm opponent from a GameChanger URL (reuses `_parse_gc_url()` + `add_team_to_yaml()`)
- **`src/web/index.html` + `css/style.css` + `js/app.js`** — single-page app: Build Reports (division → team → live log), View Reports (open any PDF), Add Team. Vanilla JS, no build step.
- **`launchers/Start Scout.command`** — double-clickable launcher: activates the venv, starts the server, and opens the browser automatically.
- **Flask 3.1.3** added to `requirements.txt`.

### Notes
- **Build vs. view:** Reports can only be **built** on the Mac (the engine needs Python + Playwright + the venv). The generated PDFs sync via Google Drive, so they can be **viewed anywhere** — including on a phone through the Google Drive app. The web UI auto-detects when the server is unreachable and switches to a friendly view-only message.
- **Unbuffered streaming:** the build subprocess runs with `python -u` + `PYTHONUNBUFFERED=1` so log lines stream live rather than arriving in one dump at the end.

---

## [3.0.0] - 2026-06-28

### Changed — Directory Restructure (breaking: all script paths changed)
- **`src/` layout** — All Python source files moved from `Dev/Hitting_Scout/Scripts/` and `Dev/Pitching_Savant/Scripts/` into `src/{hitting,pitching,scraping,orchestrator}/`
- **`launchers/`** — All shell scripts and launchd plist consolidated from two separate Script directories into a single `launchers/` folder at repo root
- **`seasons/` data directory** — Season-specific data (`Majors/`, `Minors/`, `Wild/`, `Storm/`) moved from repo root into `seasons/2026-spring/` (gitignored)
- **`sessions/`** — `gc_session.json` moved from `Dev/Hitting_Scout/Scripts/` to `sessions/` at repo root (gitignored)
- **`logs/`** — Unified log directory at repo root replacing split `Dev/Hitting_Scout/Logs/` + `Dev/Pitching_Savant/Logs/`

### Added
- **`src/season_config.py`** — Central config loader. Reads `config/<season_id>.yaml` and provides `SCOUT_ROOT`, `SEASON_DIR`, `build_scraper_divisions()`, `build_hitting_divisions()`, `add_team_to_yaml()`. All scripts import from here.
- **`config/2026-spring.yaml`** — Single source of truth for all team data: GC IDs, slugs, coach names, division paths, roster_additions. Previously duplicated across 3 Python files.
- **`config/active_season.txt`** — One-line file (`2026-spring`) that controls which season YAML is loaded. Change this to switch seasons; no Python edits needed.
- **PyYAML 6.0.3** added to `requirements.txt`; venv rebuilt with corrected symlinks

### Fixed
- **Hardcoded absolute path removed** — `scrape_gc_playbyplay.py` and `scrape_gc_boxscores.py` previously hardcoded `/Users/mesau/.../WCWAA/2026/Spring`. All scripts now use fully relative paths anchored to `__file__` via `season_config.py`.
- **`add_new_team()` wizard** (Orchestrator) — replaced brittle text-replacement on Python source files with `add_team_to_yaml()` which writes cleanly to the YAML config.
- **Broken venv** — Rebuilt after symlink corruption from directory rename (`Scout_Development/` → `Dev/`). Now uses standard `python3 -m venv` at absolute path.

---

## [2.8.0] - 2026-06-22

### Added
- **Swing% stat** (Hitting) — new plate-discipline metric: total swings / total pitches seen. Displayed on individual player cards (footer row, leftmost position) and in the summary table. Card footer now shows 4 stats L→R: Sw% · SM% · CStr% · FPT%. No color thresholds yet (plain navy); archetype integration deferred to next revision.

---

## [2.7.0] - 2026-06-02

### Added
- **Pipeline summary log** (Orchestrator) — `pipeline_summary.log` is appended after each run with per-division and per-team accounting: games processed, PAs, pitchers found, and PDF status. Includes delta column (`+N PA`) showing new data since the previous run. Located at `Dev/Hitting_Scout/Logs/pipeline_summary.log`.

### Fixed
- **Case-insensitive team name matching** (Hitting + Pitching) — folder name `Mara Outlaws 9U` vs inning header `MARA Outlaws 9U` no longer causes 0 PA. All team_key comparisons now use `.lower()` on both sides.

---

## [2.6.1] - 2026-05-29

### Fixed
- **launchd nightly job not surviving reboots** (Infrastructure) — symlink to plist on Google Drive filesystem was not reliably loaded by macOS at boot if GDrive had not finished mounting. Added `~/.zprofile` one-liner that checks and re-registers the job on every login. No second copy of the plist needed; canonical file stays in repo.

---

## [2.6.0] - 2026-05-19

### Fixed
- **Accented characters in player names break regex parsing** (Hitting + Pitching) — regexes used ASCII-only `[a-z]` for last-name capture groups, which silently dropped players with accented names (e.g., `B González`). Fixed by extending to `[a-z\u00C0-\u024F]`. Affected: `gen_hitting.py` (`DESC_RE`), `gen_pitching.py` (`PITCHER_NAMED_RE`, `LINEUP_CHANGE_RE`). See BUG-16.

### Changed
- **Renamed `gen_reports.py` → `gen_hitting.py`** — all references updated across the entire codebase (scripts, shell launchers, docs, launchd plist, AllStars scripts). Logger name and log filenames updated to match.
- **Unified CHANGELOG.md and BUGS.md** — merged per-app files into single project-level files at repo root. Per-app files removed.

---

## [2.5.0] - 2026-05-17

### Added — Pitching Savant (new component)
- **Pitching Savant v0.1.0** (`gen_pitching.py`) — Baseball Savant-style pitcher profile cards
- Computes 13 pitching stats from play-by-play game files (ERA-proxy, WHIP, K/9, BB/9, K%, BB%, K/BB, BABIP, HR/9, FPSH%, GB%, FB+LD%, C%)
- League-wide percentile ranking with colored slider bars (red→yellow→green)
- Supports all 4 divisions: Majors, Minors, Wild, Storm
- Deduplication of initials-only names in travel divisions (Wild/Storm)
- Integrated into Scout pipeline as Step 4 (`run_menu.py`)
- Standalone launchers: `run_pitching.sh`, `run_pitching_nightly.sh`

### Changed
- **Repo restructured** — root moved from `Scout_Development/` to `Spring/`; both apps coexist as sibling directories (`Scout_Development/`, `Pitching_Savant/`)
- **Shared venv** — both apps use `Scout_Development/venv/`

### Infrastructure
- Added `_safe_div` helper, `_compute_derived_stats`, docstrings, and improved comments (refactor commit `d89c8b6`)
- Updated `Instructions.md` with complete function maps for both apps

---

## [2.4.1] - 2026-05-10

### Fixed
- **Schedule scraper now loads full season before extracting games** (Scraping) — added scroll-to-bottom loop before running `SCHEDULE_JS`. GC lazy-loads schedule cards; without scrolling, the scraper only saw games through late April. Recovered 9 Majors and 14 Minors games (May 4–9). See BUG-13.
- **False "Skipped" entries in PDF subtitle eliminated** (Hitting) — `game_files` is built once at startup; as teams are processed their files are renamed to `-Reviewed.txt`. When the second team in a game was processed later, the original `.txt` path was stale. Fix: fall back to `-Reviewed.txt` path transparently. Recovered 9 Majors and 14 Minors games from false skips. See BUG-14.

---

## [2.4.0] - 2026-05-02

### Added
- **LG RANK row for Wild and Storm divisions** (Hitting) — `run_wild()` now uses a two-pass approach: Pass 1 parses all opponent teams and builds `div_team_totals`; Pass 2 generates each PDF passing that list as `league_team_totals`. The light-blue LG RANK row now appears in Wild and Storm summary tables exactly as it does in Majors/Minors.

### Fixed
- **"No PAs found" warning now surfaces actual team names from game files** (Hitting) — when 0 PAs are parsed for a Wild/Storm opponent, the warning message now scans all game file inning headers and lists every unique team name seen. Makes folder-name/inning-header mismatches immediately self-diagnosing.
- **Dilworth 9U - Navy team name corrected** (Scraping) — team name was `"Dilworth 9U Navy"` but GC inning headers write `"Dilworth 9U - Navy"`. Folder renamed to match; both scrapers updated. See BUG-15.

---

## [2.3.0] - 2026-04-29

### Added
- **LG RANK row in summary table** (Hitting) — light-blue row below the Team Totals row showing each stat's dense rank among all teams in the division (e.g. `3/11`). Rank 1 = highest value. Appears only for Majors and Minors.
- **`_rank_stat()` helper** (Hitting) — dense rank; rank 1 = highest, ties share rank; returns `"rank/n"` string.

### Changed
- **`build_league_context()`** (Hitting) — now returns a 2-tuple `(league_batters, league_team_totals)`.
- **`generate_pdf()`** (Hitting) — added `league_team_totals=None` parameter; when provided, appends the LG RANK row.
- **`run_league()`** (Hitting) — unpacks 2-tuple from `build_league_context()`.

### Fixed
- **Majors LG RANK showed `x/10` instead of `x/11`** (Hitting) — A's-Blanco apostrophe in `team_key` didn't match filename. Added `replace("'", "")` fallback. See BUG-13 (old numbering).
- **INNING GAP warnings demoted to `logger.debug()`** (Hitting) — suppressed from terminal output. See BUG-12.
- **BOX-VERIFY warnings demoted to `logger.debug()`** (Hitting) — suppressed from terminal output. See BUG-12.

---

## [2.2.0] - 2026-04-28

### Added
- **Team Aggregate Card** (Hitting) — first card (top-left, green header) on the player card page shows the team's combined offensive profile: aggregate spray chart, stat boxes, bars, and overall archetype.
- **Team Totals row in summary table** (Hitting) — amber-highlighted bold row at the bottom of the summary table.
- **`compute_team_totals()`** (Hitting) — sums all batter counting stats and recomputes derived stats from aggregated totals.

### Changed
- **`draw_card()`** (Hitting) — accepts optional `header_color` parameter; team aggregate card uses green.
- **`compute_stats()` return dict** (Hitting) — now includes raw pitch counting fields so `compute_team_totals()` can sum them correctly.

---

## [2.1.0] - 2026-04-28

### Added
- **`run_scout_nightly.sh`** (Orchestrator) — headless pipeline wrapper for scheduled/automated runs
- **`launchd/com.wcwaa.scout_pipeline.plist`** — macOS LaunchAgent that fires daily at 10:00 AM EDT
- **`--all` flag on `run_menu.py`** (Orchestrator) — explicit headless flag; skips the interactive menu

### Changed
- **Script renames (refactor):**
  - `gc_scraper.py` → `scrape_gc_playbyplay.py`
  - `scrape_box_scores.py` → `scrape_gc_boxscores.py`
  - `interactive_menu.py` → `run_menu.py`
- **LKN Lightning 10U team_id corrected** (Scraping) — wrong ID replaced in both scrapers

---

## [2.0.0] - 2026-04-24

### Added
- **`run_menu.py`** (Orchestrator) — interactive pipeline launcher with numbered menu, CLI passthrough, team list picker, add-new-team wizard, session file check
- **Pipeline version string** — `__version__ = "2.0.0"` displayed in menu header
- **`--team` filter in `scrape_gc_boxscores.py`** (Scraping) — Step 2 now respects single-team selection for Wild/Storm. See BUG-10.
- **Two new Wild opponents** — SBA Alabama National 12U, TN Nationals Heichelbech 12U

### Changed
- **Renamed `run_weekly.sh` → `run_scout.sh`**
- **`gen_hitting.py` `--team` filter** (Hitting) — `run_wild()` now uses partial case-insensitive match
- **`load_wild_roster()`** (Hitting) — indexes entries under both key formats for jersey number resolution. See BUG-11.

### Fixed
- **Wild/Storm PDF cards missing jersey numbers** (Hitting) — See BUG-11.
- **Step 2 ignored `--team` for Wild/Storm** (Scraping) — See BUG-10.
- **`SCHEDULE_JS` `final` detection broken for Wild/Storm** (Scraping) — See BUG-7.
- **SCHEDULE_JS team-page filenames had wrong date and team name** (Scraping) — See BUG-8.
- **`NameError: date not defined`** (Scraping) — See BUG-9.

---

## [1.0.0] - 2026-04-23

> Tagged retroactively — last commit before interactive menu. Represents the fully working pipeline with all 4 divisions operational.

### State at v1.0.0
- All 4 divisions generating PDFs: Majors (11 teams), Minors (14 teams), Wild (5 opponents), Storm (5 opponents)
- `run_weekly.sh` — CLI-only launcher (no interactive menu)
- Wild/Storm scraping fully operational (Bugs 7/8/9 fixed in this cycle)
- SS spray chart zone fix applied (BUG-6)
- Full pipeline verified clean on Apr 23 2026

---

## [0.2.0] - 2026-04-22

### Added
- **`Infield Fly` → FO mapping** (Hitting + Parser) — infield fly rule plays now correctly parsed as flyball outs
- **QC Flight Baseball 11U** added (Scraping) — 15 games, 400 PAs
- **DEBUG_CONFIG sections** in all 3 main scripts — toggleable flags for heavy debug output
- **`--verbose` / `-v` flag** on all 3 scripts — shows debug messages on screen
- **`diag_schedule.py`** diagnostic tool
- **Try/except error handling** in scrapers and hitting — one timeout no longer kills pipeline

### Fixed
- **SCHEDULE_JS `final` detection broken for Wild/Storm team pages** (Scraping) — See BUG-7.
- **SCHEDULE_JS team-page filenames had wrong date and team name** (Scraping) — See BUG-8.
- **`NameError: date not defined`** (Scraping) — See BUG-9.
- **INNING_RE regex** (Scraping) — now tolerates missing closing `===`
- **`$awyer M` auto-fix** (Parser) — `GC_NAME_FIXES` dict auto-corrects
- **SCHEDULE_JS date + team parsing** (Scraping) — GC DOM change handling
- **`merge_player` KeyError on `'games'` key** (Scraping) — added `setdefault()` guard
- **Duplicate team keys in `rosters.json`** (Scraping) — added `TEAM_NAME_ALIASES`

### Verified (pipeline milestones — Session 3, Apr 22 2026)
- ✅ Full pipeline: Majors 11 PDFs/35 games, Minors 14 PDFs/90 games/2342 PAs
- ✅ Wild: 4/5 PDFs operational; Storm: 4 PDFs operational
- ✅ Minors fully working — 14 teams, 90 games, 2342 PAs

---

## [0.1.0] - 2026-04-21

### Added
- Created Python virtual environment (`venv/`) for dependency isolation
- Installed Playwright 1.58.0 + Chromium 145, ReportLab 4.4.10
- Created `requirements.txt`, `.gitignore`, `CHANGELOG.md`
- Transferred full pipeline from Cowork to VS Code local environment:
  - `scrape_gc_playbyplay.py`, `scrape_gc_boxscores.py`, `parse_gc_text.py`, `gen_hitting.py`, `run_weekly.sh`

### Infrastructure
- Git repository initialized
- Version tracking begins at `0.1.0`
