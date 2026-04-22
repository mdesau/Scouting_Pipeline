# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
<!-- Daily/nightly work-in-progress goes here. Move to a versioned section when tagging. -->

### In Progress
- Step 2: Run `gc_scraper.py --login` to save GameChanger session
- Step 3: Verify `gc_scraper.py --division Majors --check` loads schedule correctly
- Step 4: Verify `scrape_box_scores.py --division Majors` resolves `?N P?` / `?C C?`
- Step 5: Verify `gen_reports.py --division Majors --team Cubs` produces separate Brian A. / Ben A. cards

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
