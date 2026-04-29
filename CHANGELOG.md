# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
<!-- Daily/nightly work-in-progress goes here. Move to a versioned section when tagging. -->

---

## [2.0.0] - 2026-04-24

### Added
- **`run_menu.py`** — new interactive pipeline launcher replacing the bare `run_scout.sh` logic:
  - Numbered menu: `[0]` full pipeline (default), `[1]` single division, `[2]` single team, `[3]` add new Wild/Storm opponent, `[Q]` quit
  - CLI passthrough mode: `bash run_scout.sh --division Wild --team "QC Flight"` skips the menu and runs directly
  - Team lists built dynamically from `scrape_gc_playbyplay.DIVISIONS` (single source of truth — no duplication)
  - Majors/Minors team lists read from `rosters.json` keys
  - Add-new-team flow: parses GC URL → suggests folder name → inserts into both scraper files → creates folder structure
  - Session file check upfront — warns before menu if `gc_session.json` is missing
- **Pipeline version string** — `__version__ = "2.0.0"` in `run_menu.py`; displayed in menu header and `run_scout.sh` launch banner
- **`--team` filter in `scrape_gc_boxscores.py`** — Step 2 now respects single-team
  selection for Wild/Storm divisions. `scrape_team_division()` and `run()` accept a
  `team_filter` param (partial, case-insensitive match against team name). `argparse`
  gains a `--team` argument. `run_menu.py` Step 2 now passes `team_args`
  alongside `div_args` so a single-team run only scrapes that one team's box scores.
  *(Bug 10 — see Bugs_List.txt)*
- **Two new Wild opponents** added to `scrape_gc_playbyplay.py`, `scrape_gc_boxscores.py`, and `Instructions.md`:
  - SBA Alabama National 12U — team_id `Wn2Abf32IXOz`, slug `2026-summer-sba-alabama-national-12u`
  - TN Nationals Heichelbech 12U — team_id `QebtI4WHVMPn`, slug `2026-summer-tn-nationals-heichelbech-12u`
  - Folder structures created: `Wild/SBA Alabama National 12U/Games/` and `Wild/TN Nationals Heichelbech 12U/Games/`

### Changed
- **Renamed `run_weekly.sh` → `run_scout.sh`** — all references updated in `Instructions.md`, `README.md`, `CHANGELOG.md`, and the script header
- **`run_scout.sh`** simplified to ~55 lines (venv activation + `python3 run_menu.py "$@"`)
- **`gen_reports.py` `--team` filter** — `run_wild()` now uses partial case-insensitive match (was exact match, broke single-team PDF regeneration)
- **`load_wild_roster()`** — now indexes each player under both `"R B"` (roster.txt key) and `"Ryder B"` (game-file format) so jersey numbers resolve correctly for Wild/Storm PDFs *(Bug 11 — see Bugs_List.txt)*

### Fixed
- **Wild/Storm PDF cards missing jersey numbers** — `load_wild_roster()` key format mismatch with game-file initials format *(Bug 11)*
- **Step 2 ignored `--team` for Wild/Storm** — `scrape_gc_boxscores.py` always scraped all division teams even for single-team runs *(Bug 10)*
- **`SCHEDULE_JS` `final` detection broken for Wild/Storm team pages** — score pattern `/^[WL]\s+\d+-\d+/` added alongside `FINAL` check *(Bug 7)*
- **SCHEDULE_JS team-page filenames had wrong date and team name** — leaf-node date detection + `is_home` + team-name-based filename construction *(Bug 8)*
- **`NameError: date not defined` in `scrape_gc_boxscores.py`** *(Bug 9)*

---

## [1.0.0] - 2026-04-23

> Tagged retroactively on `0e4c05e` — last commit before interactive menu and `run_scout.sh` rename.
> Represents the fully working pipeline with Majors, Minors, Wild, and Storm all operational
> under the original `run_weekly.sh` launcher.

### State at v1.0.0
- All 4 divisions generating PDFs: Majors (11 teams), Minors (14 teams), Wild (5 opponents), Storm (5 opponents)
- `run_weekly.sh` — CLI-only launcher (no interactive menu)
- Wild/Storm scraping fully operational (Bugs 7/8/9 fixed in this cycle before tagging)
- SS spray chart zone fix applied *(Bug 6)*
- Full pipeline verified clean on Apr 23 2026

---

## [0.2.0] - 2026-04-22

### Added
- **`Infield Fly` → FO mapping** in both `gen_reports.py` (`parse_outcome()`) and
  `parse_gc_text.py` (`OUTCOME_TYPES`) — infield fly rule plays now correctly parsed
  as flyball outs instead of `WARNING UNKNOWN`
- **QC Flight Baseball 11U** added to both `scrape_gc_playbyplay.py` and `scrape_gc_boxscores.py`
  — team_id `1gqDRuls0oER`, slug `2026-spring-qc-flight-baseball-11u`. PDF generated
  successfully (15 games, 400 PAs)
- **DEBUG_CONFIG sections** in all 3 main scripts (`scrape_gc_playbyplay.py`, `scrape_gc_boxscores.py`,
  `gen_reports.py`) — toggleable flags for heavy debug output (raw JS dumps, PA-level
  tracing, archetype scoring breakdowns)
- **`--verbose` / `-v` flag** on all 3 scripts — shows `logger.debug()` messages on
  screen (normally only written to log file). Light debugging without touching code.
- **`diag_schedule.py`** diagnostic tool — dumps raw schedule page DOM for debugging
  GC layout changes
- **Try/except error handling** in `scrape_gc_playbyplay.py` (division loop + per-team loop in
  `scrape_team_division`) and `gen_reports.py` (`run_wild` per-opponent loop) — one
  timeout or crash no longer kills the entire pipeline

### Fixed
- **`SCHEDULE_JS` `final` detection broken for Wild/Storm team pages** — GC team schedule
  pages show a score (`W 7-5`, `L 9-11`) for completed games instead of the word `FINAL`.
  The org pages (Majors/Minors) still show `FINAL`. Added score-pattern check
  (`/^[WL]\s+\d+-\d+/`) alongside the existing `FINAL` check in both `scrape_gc_playbyplay.py`
  and `scrape_gc_boxscores.py`. All Wild/Storm games were returning 0 FINAL found; fix
  restores detection of all completed games (Weddington Wild: 19 games confirmed visible)
- **SCHEDULE_JS team-page filenames had wrong date and wrong team name** — day-abbr (SUN/SAT)
  and day-number are separate leaf nodes outside the `<a>` card on team pages (unlike org
  pages where they are inside the card). Added leaf-node date detection for uppercase
  day-abbrs + `is_home` boolean field + `team_name`-based filename construction in
  `scrape_team_division()`. Bad files from aborted run deleted before re-scrape.
- **`NameError: date not defined` in `scrape_gc_boxscores.py`** — pre-existing lint error;
  `date` class was not imported alongside `datetime`. Fixed: `from datetime import datetime, date`
- **INNING_RE regex** (`scrape_gc_playbyplay.py`) — regex now tolerates missing closing `===`
  in inning headers. Was causing opponent PAs to leak into the wrong team's report;
  affected 8 game files. Patched 12 broken inning headers in existing scorebooks.
- **`$awyer M` auto-fix** (`parse_gc_text.py`) — `GC_NAME_FIXES` dict wired in;
  dollar sign in player name from GC is corrected automatically on next scrape.
- **SCHEDULE_JS date + team parsing** (`scrape_gc_playbyplay.py`) — GC changed their DOM from
  full-date headers to month headers + day-in-first-card. Filenames were coming out
  as `-Sat_vs_21.txt` instead of `Mar21-Marlins-Eberlin_vs_Angels-Casper.txt`.
  Rewrote JS to track month headers and carry date forward for same-day games.
- **`merge_player` KeyError on `'games'` key** (`scrape_gc_boxscores.py`) — old roster
  entries lacked the `games`/`games_seen` keys added in a schema update. Added
  `setdefault()` migration guard.
- **Duplicate team keys in `rosters.json`** (`scrape_gc_boxscores.py`) — GC box score
  pages render some names differently from play-by-play headers (e.g. `As-Blanco` vs
  `A's-Blanco`). Added `TEAM_NAME_ALIASES` dict + `normalize_team_name()` function.
- **`?N P?` and `?C C?` in Cubs-Holtzer** — resolved: Nathan P. #10 and Chase C. #3
  now in `rosters.json`. Confirmed on full pipeline run Apr 22.
- **Google Drive timeout on QC Flight folder** — resolved by toggling offline
  availability (online-only → offline) to force re-sync.

### Verified (pipeline milestones — Session 3, Apr 22 2026)
- ✅ **Full pipeline (`run_weekly.sh`)** — all 4 divisions regenerated clean:
  - Majors: 11 PDFs, 35 games — all 11:50 timestamps confirmed
  - Minors: 14 PDFs, 90 games, 2342 PAs — all ✓
  - Wild: 4/5 PDFs — Arena National (9g), QC Flight (15g/400PA), SC Panthers (8g),
    Weddington Wild (11g); T24 Garnet still 0 FINAL games
  - Storm: 4 PDFs — 9u Challenge (6g), Crushers White (7g), ITAA Spartans (7g),
    MARA Stingers (17g/340PA); MILITIA 9U still 0 game files
- ✅ `?N P?` / `?C C?` gone from Cubs-Holtzer — Nathan P. #10, Chase C. #3 confirmed
- ✅ `scrape_gc_boxscores.py` — 35 Majors + 45 Minors games all "already scraped";
  no new games since last run
- ✅ **Minors fully working** — all 14 teams, 6–7 games each (90 games, 2342 PAs).
  The "missing away-game files" issue from session 1 was a transient Google Drive
  sync delay, not a code bug.
- ✅ QC Flight Baseball 11U: 15 games, 400 PAs, PDF generated
- ✅ T24 Garnet 11U: confirmed 0 FINAL games on GC (not a scraper bug)

---

## [0.1.0] - 2026-04-21

### Added
- Created Python virtual environment (`venv/`) for dependency isolation
- Installed **Playwright 1.58.0** and **Chromium 145** — enables local GC scraping
  (was previously blocked in Cowork sandbox due to network allowlist)
- Installed **ReportLab 4.4.10** — used by `gen_reports.py` for PDF generation
- Created `requirements.txt` — pin exact package versions for reproducible installs
- Created `.gitignore` — excludes `venv/`, `gc_session.json`, logs, `__pycache__`
- Created `CHANGELOG.md` (this file) — tracks all changes going forward
- Transferred full pipeline from Cowork to VS Code local environment:
  - `scrape_gc_playbyplay.py` — Playwright-based GC schedule + play-by-play scraper
  - `scrape_gc_boxscores.py` — Playwright-based roster + jersey number scraper
  - `parse_gc_text.py` — raw GC text → WCWAA structured format converter
  - `gen_reports.py` — stat engine + ReportLab PDF generator (4 divisions)
  - `run_weekly.sh` — one-command pipeline orchestrator

### Changed
- Updated `run_weekly.sh` to activate the `venv` before running Python scripts,
  ensuring Playwright and ReportLab are always available

### Infrastructure
- Git repository initialized
- Version tracking begins at `0.1.0` (initial development phase)

---

<!-- Version Roadmap (targets, not commitments):
  0.2.0 — ✅ RELEASED — Full end-to-end pipeline verified; core bugs fixed
  0.3.0 — Mid-season update: new games scraped, T24 Garnet + MILITIA come online
  1.0.0 — Pipeline stable, tested, and running reliably each game week
-->
