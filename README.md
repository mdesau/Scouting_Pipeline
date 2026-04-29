# WCWAA Scouting Pipeline
![Version](https://img.shields.io/badge/version-2.3.0-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

Automated scouting report pipeline for Weddington youth baseball leagues (Spring 2026).

Pulls live play-by-play data from [GameChanger](https://web.gc.com), computes batting stats and player archetypes, and generates multi-page PDF scouting reports — all from a single terminal command run after each game week.

---

## Divisions Covered

| Division | Level | Teams | Scope |
|---|---|---|---|
| **Majors** | 11U in-house | 11 teams | Full league |
| **Minors** | 9U in-house | 14 teams | Full league |
| **Wild** | 11U travel | 5 opponents | Opponent reports only |
| **Storm** | 9U travel | 4 opponents | Opponent reports only |

---

## First-Time Setup (Do This Once)

These steps only need to be done once on a new machine.

### 1. Prerequisites

Make sure you have Python 3.9+ installed:
```bash
python3 --version
```

### 2. Clone the repo
```bash
git clone https://github.com/mdesau/Scouting_Pipeline.git
cd Scouting_Pipeline
```

### 3. Create the virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

> **Why a virtual environment?** It isolates this project's dependencies (Playwright, ReportLab) from your system Python. This prevents version conflicts and means nothing you install here affects anything else on your computer.

### 4. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 5. Configure folder paths

The scripts expect a specific Google Drive folder structure at:
```
~/Library/CloudStorage/GoogleDrive-.../My Drive/Baseball/WCWAA/2026/Spring/
```

If your Google Drive path differs, update the `SPRING_DIR` constant near the top of `scrape_gc_playbyplay.py`, `scrape_gc_boxscores.py`, and `gen_reports.py`.

### 6. Log in to GameChanger (one time)

This opens a real browser window. Log in manually — the session is saved to `gc_session.json` and reused automatically for all future runs.

```bash
cd Scripts
python3 scrape_gc_playbyplay.py --login
```

> **When to repeat:** Only when you see a "session expired" or "not logged in" error — typically every few weeks. Re-run `--login` to refresh.

---

## Weekly Usage (After Each Game Week)

There are two ways to run the pipeline depending on whether you want to trigger it manually or let it run automatically overnight.

---

### Option A — On-Demand (Manual Run)

Run this any time you want to trigger the pipeline yourself — after a game weekend, mid-week spot check, or single-team update:

```bash
cd Scripts
bash run_scout.sh
```

This opens an **interactive menu** where you can choose:
- `[0]` Full pipeline — all divisions, all teams
- `[1]` Single division
- `[2]` Single team
- `[3]` Add a new Wild / Storm opponent

You can also skip the menu entirely by passing flags directly:

```bash
bash run_scout.sh --division Majors
bash run_scout.sh --division Wild --team "QC Flight Baseball 11U"
```

---

### Option B — Nightly Scheduled Run (Automatic)

The pipeline can run automatically every night at **10:00 PM EDT** via macOS `launchd`. This uses a separate headless wrapper that skips the interactive menu entirely — no terminal interaction needed.

**The scheduler is configured via:**
```
launchd/com.wcwaa.scout_pipeline.plist
```

**Install (one-time):**
```bash
ln -sf "$(pwd)/../launchd/com.wcwaa.scout_pipeline.plist" \
       ~/Library/LaunchAgents/com.wcwaa.scout_pipeline.plist
launchctl load ~/Library/LaunchAgents/com.wcwaa.scout_pipeline.plist
```

**Verify it's scheduled:**
```bash
launchctl list | grep wcwaa
```

**Trigger a manual test run immediately (without waiting for 10pm):**
```bash
launchctl start com.wcwaa.scout_pipeline
```

**Uninstall:**
```bash
launchctl unload ~/Library/LaunchAgents/com.wcwaa.scout_pipeline.plist
rm ~/Library/LaunchAgents/com.wcwaa.scout_pipeline.plist
```

> **Note:** If your laptop is asleep at 10pm, launchd will skip that night's run — it does not wake the machine. The pipeline is safe to skip; it only picks up genuinely new FINAL games on the next run.

---

| | `run_scout.sh` | `run_scout_nightly.sh` |
|---|---|---|
| **Triggered by** | You, manually | macOS launchd at 10pm EDT |
| **Menu shown** | ✅ Yes (or CLI passthrough) | ❌ No — headless, no stdin |
| **Scope** | Your choice | All divisions, all teams |
| **Logs** | Per-script logs in `Logs/` | `Logs/nightly_YYYYMMDD_HHMMSS.log` + per-script logs |

---

## Scripts Reference

The table below lists every script in the order it is run, what it does, and what it depends on.

| # | Script | What it does | Depends on | Key flags |
|---|---|---|---|---|
| 1 | `scrape_gc_playbyplay.py` | Navigates GC schedule pages for all 4 divisions; finds new FINAL games; downloads play-by-play text; saves `.txt` game files to the correct folder | `parse_gc_text.py` (called internally), `gc_session.json` (auth) | `--login` `--division` `--team` `--check` `--force` `--verbose` |
| 2 | `scrape_gc_boxscores.py` | Navigates GC box score pages; extracts player names + jersey numbers; builds `rosters.json` (Majors/Minors) and `roster.txt` (Wild/Storm); writes `box_verify.json` for cross-checking | `gc_session.json` (auth) | `--division` `--force` `--verbose` |
| 3 | `gen_reports.py` | Reads all `.txt` game files; parses every plate appearance; computes batting stats + archetypes; generates multi-page PDF scouting reports via ReportLab | `rosters.json` / `roster.txt` (from step 2), game `.txt` files (from step 1) | `--division` `--team` `--verbose` |
| — | `run_scout.sh` | Interactive shell wrapper: shows numbered menu (or CLI passthrough); activates venv; calls steps 1 → 2 → 3 | All three scripts above | `--division` `--team` (passed through) |
| — | `run_scout_nightly.sh` | Headless shell wrapper for scheduled runs: no menu, no stdin; calls `run_menu.py --all`; logs to `Logs/nightly_*.log` | `run_menu.py`, venv | *(none)* |
| — | `run_menu.py` | Python pipeline orchestrator: builds the interactive menu, handles CLI passthrough, and calls the 3 steps as subprocesses | `scrape_gc_playbyplay.py` (imports DIVISIONS) | `--all` `--division` `--team` |
| — | `parse_gc_text.py` | Utility: converts raw GC page text into the WCWAA-structured `.txt` game file format; applies name-fix corrections (e.g. `$awyer` → `Sawyer`) | *(none — pure utility, no external deps)* | *(imported by `scrape_gc_playbyplay.py`, not run directly)* |
| — | `diag_schedule.py` | Diagnostic only: dumps the raw GC schedule page DOM to help debug layout changes; not part of the normal pipeline | `gc_session.json` (auth) | `--division` |

---

## Running Individual Parts

You don't have to run the full pipeline every time. Common single-step commands:

```bash
# Regenerate PDFs for one team (fastest — no scraping)
python3 gen_reports.py --division Majors --team Cubs
python3 gen_reports.py --division Wild --team "QC Flight Baseball 11U"

# Scrape one division only
python3 scrape_gc_playbyplay.py --division Storm

# Check what new games are available without downloading anything
python3 scrape_gc_playbyplay.py --check

# See detailed output while running
python3 gen_reports.py --division Minors --verbose

# Force re-scrape games already on disk
python3 scrape_gc_playbyplay.py --force --division Majors
```

---

## Output Files

| File | Location | Description |
|---|---|---|
| `*-Scout_2026.pdf` | `Majors/Reports/Scouting_Reports/` | Scouting report PDFs (one per team) |
| `rosters.json` | `Majors/Reports/` and `Minors/Reports/` | Player names + jersey numbers, keyed by initials |
| `box_verify.json` | `Majors/Reports/` and `Minors/Reports/` | Per-game AB/BB/SO totals for cross-check verification |
| `roster.txt` | `Wild/[TeamName]/` and `Storm/[TeamName]/` | Flat text roster for travel division opponents |
| `*.txt` game files | `Majors/Reports/Scorebooks/`, `Wild/[TeamName]/Games/` etc. | Play-by-play game files scraped from GC |
| `Logs/*.log` | `Scout_Development/Logs/` | Timestamped log files from each script run |

> **Note:** PDFs, game `.txt` files, and logs are excluded from this repo (see `.gitignore`). See `examples/` for one sample of each output format.

---

## What the Reports Show

Each PDF scouting report includes:

- **Player cards** — one card per batter with:
  - Spray chart (hit zones)
  - Stat bars: AVG, OBP, SLG, C% (contact rate)
  - Discipline stats: SM% (swing-and-miss), CStr% (called strike rate), FPT% (first-pitch take rate)
  - **Archetype label** — a two-word tag combining plate approach and result outcome (e.g. *Disciplined Walker*, *Aggressive Power*)
  - Recommended pitching approach based on archetype
- **Summary page** — stat table across all batters + two-sentence scouting notes per player

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `ImportError: playwright` | venv not activated | Run `source venv/bin/activate` first |
| `Session expired` / login error | `gc_session.json` stale | Run `python3 scrape_gc_playbyplay.py --login` |
| `0 PAs` for a team | Team name mismatch between folder name and GC inning header | Check spelling in game file header vs. folder name |
| `?X X?` in report output | Player initials not in `rosters.json` | Run `scrape_gc_boxscores.py` |
| `WARNING UNKNOWN` in logs | Play description not recognised by parser | Check the game file; if valid play, add to `OUTCOME_TYPES` in `gen_reports.py` |
| `WARNING BOX-VERIFY` in logs | Parsed AB count differs from GC box score | Review game file for missed or duplicate plays |
| PDFs not appearing | Google Drive not synced | Toggle the folder's offline availability to force a re-sync |

---

## Project Structure

```
Scouting_Pipeline/
  README.md
  CHANGELOG.md
  Instructions.md          ← detailed context file for AI-assisted sessions
  requirements.txt
  .gitignore
  Scripts/
    scrape_gc_playbyplay.py
    scrape_gc_boxscores.py
    parse_gc_text.py
    gen_reports.py
    run_scout.sh
    diag_schedule.py
    archetype_reference.txt
  examples/
    example_game_file.txt           ← sample parsed play-by-play file
    example_scouting_report.pdf     ← sample output PDF
```

---

## Instructions.md — The AI Session Context File

`Instructions.md` is a purpose-built context document that is loaded at the start of every AI-assisted coding session (e.g. GitHub Copilot, Claude, ChatGPT).

### Why it exists

AI coding assistants have a **context window** — a limit on how much text they can "remember" within a single conversation. In a long session involving complex code reviews, bug hunts, and multi-file edits, earlier decisions and discoveries get pushed out of the window and are effectively forgotten. This is called **context rot**.

`Instructions.md` solves this by acting as a **persistent memory file** that is manually updated at the end of each session. When a new session starts, the AI reads this file first and immediately has full awareness of:

- Every design decision made and *why* it was made
- All known bugs, their root causes, and their current fix status
- Exact file paths, team IDs, data formats, and naming conventions
- The results of the most recent pipeline run
- What to work on next

Without it, every new session would require re-explaining the project from scratch — wasting time and risking the AI making suggestions that contradict prior decisions.

### What to update after each session

At the end of any session where meaningful work was done, update these sections in `Instructions.md`:

| Section | What to update |
|---|---|
| **Git log block** | Add the new commit hashes and messages |
| **Latest Pipeline Run Results** | Update PA counts, game counts, and any new warnings |
| **Known Issues / Pending Work** | Mark resolved issues as ~~strikethrough~~; add new ones |
| **Next Session Priorities** | Replace completed items with what's actually next |

The goal is that `Instructions.md` + `CHANGELOG.md` together should give any AI (or human) enough context to pick up exactly where the last session left off — with zero verbal re-briefing required.

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/).

| Version | Date | Summary |
|---|---|---|
| `v2.0.0` | Apr 24, 2026 | Interactive menu (`run_menu.py`), `run_scout.sh` rename, `--team` filter, Wild/Storm jersey numbers fixed (Bugs 10–11) |
| `v1.0.0` | Apr 23, 2026 | All 4 divisions fully operational under `run_weekly.sh`; Bugs 6–9 fixed |
| `v0.2.0` | Apr 22, 2026 | Full pipeline verified across all 4 divisions; INNING_RE fix; QC Flight added; Infield Fly mapping |
| `v0.1.0` | Apr 21, 2026 | Initial setup — venv, Playwright, ReportLab, full pipeline transfer to local VS Code |
