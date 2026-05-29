# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Components:** Hitting (`gen_hitting.py`), Pitching (`gen_pitching.py`), Scraping (`scrape_gc_playbyplay.py`, `scrape_gc_boxscores.py`), Orchestrator (`run_menu.py`)

---

## [Unreleased]
<!-- Daily/nightly work-in-progress goes here. Move to a versioned section when tagging. -->

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
