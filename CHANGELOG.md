# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
<!-- Daily/nightly work-in-progress goes here. Move to a versioned section when tagging. -->

### Added
- **DEBUG_CONFIG sections** in all 3 main scripts (`gc_scraper.py`, `scrape_box_scores.py`,
  `gen_reports.py`) — toggleable flags for heavy debug output (raw JS dumps, PA-level
  tracing, archetype scoring breakdowns)
- **`--verbose` / `-v` flag** on all 3 scripts — shows `logger.debug()` messages on
  screen (normally only written to log file). Light debugging without touching code.
- **`diag_schedule.py`** diagnostic tool — dumps raw schedule page DOM for debugging
  GC layout changes

### Fixed
- **SCHEDULE_JS date + team parsing** (`gc_scraper.py`) — GC changed their DOM from
  full-date headers to month headers + day-in-first-card. Filenames were coming out
  as `-Sat_vs_21.txt` instead of `Mar21-Marlins-Eberlin_vs_Angels-Casper.txt`.
  Rewrote JS to track month headers and carry date forward for same-day games.
- **`merge_player` KeyError on `'games'` key** (`scrape_box_scores.py`) — old roster
  entries lacked the `games`/`games_seen` keys added in a schema update. Added
  `setdefault()` migration guard.
- **Duplicate team keys in `rosters.json`** (`scrape_box_scores.py`) — GC box score
  pages render some names differently from play-by-play headers (e.g. `As-Blanco` vs
  `A's-Blanco`). Added `TEAM_NAME_ALIASES` dict + `normalize_team_name()` function.

### Verified (pipeline milestones)
- ✅ `gc_scraper.py --login` — session saved to `gc_session.json`
- ✅ `gc_scraper.py --division Majors` — 35 games scraped, correct filenames
- ✅ `gc_scraper.py --division Minors` — 45 games scraped, correct filenames
- ✅ `scrape_box_scores.py --division Majors` — 11 clean team keys, no duplicates;
  collision detection working (5 teams with shared initials)
- ✅ `gen_reports.py --division Majors --team Cubs` — Brian A. #1 and Benjamin A. #2
  appear as separate player cards; PDF generated successfully

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
  - `gc_scraper.py` — Playwright-based GC schedule + play-by-play scraper
  - `scrape_box_scores.py` — Playwright-based roster + jersey number scraper
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
  0.2.0 — Full end-to-end pipeline verified for all 4 divisions
  0.3.0 — All known bugs fixed (Infield Fly, $awyer, QC Flight team_id)
  0.4.0 — T24 Garnet 11U complete (all 8 remaining games scraped)
  1.0.0 — Pipeline stable, tested, and running reliably each game week
-->
