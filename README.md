# WCWAA Scout Pipeline
![Version](https://img.shields.io/badge/version-3.3.1-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

Automated scouting report pipeline for Weddington youth baseball leagues (Spring 2026).
Pulls live play-by-play data from [GameChanger](https://web.gc.com), computes batting stats, player archetypes, and pitching percentiles, then generates multi-page PDF scouting reports — all from a single terminal command run after each game week.

---

## Divisions Covered

| Division | Level | Teams | Scope |
|---|---|---|---|
| **Majors** | 11U in-house | 11 teams | Full league |
| **Minors** | 9U in-house | 14 teams | Full league |
| **Wild** | 11U travel | 10 opponents | Opponent reports only |
| **Storm** | 9U travel | 18 opponents | Opponent reports only |

---

## First-Time Setup (Do This Once)

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
source venv/bin/activate
```

> **Why a virtual environment?** It isolates this project's dependencies (Flask, Playwright, ReportLab) from your system Python.

### 4. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 5. Log in to GameChanger (one time)

This opens a real browser window. Log in manually — the session is saved to `sessions/gc_session.json` and reused automatically for all future runs.

```bash
python3 src/scraping/scrape_gc_playbyplay.py --login
```

> **When to repeat:** Only when you see a "session expired" error — typically every few weeks.

---

## User Options

### Option A — Web UI (Easiest)

Double-click **`launchers/Start Scout.command`** in Finder. This starts the local
web server and opens the app in your browser at **http://127.0.0.1:5050**.

From the app you can:
- **Build Reports** — pick a division → team → click Build; the pipeline log streams live on the page
- **View Reports** — browse every generated PDF and open it in one click
- **Add Team** — register a new Wild / Storm opponent from a GameChanger URL
- **Seasons** — create a new season or switch the active season

> Close the Terminal window the launcher opened (or press Ctrl+C in it) to stop the server.
> Reports can only be **built** while the server is running on this Mac; the PDFs themselves
> sync via Google Drive and can be **viewed anywhere**, including a phone (via the Google Drive app).

### Option B — Interactive Terminal Menu

```bash
bash launchers/run_scout.sh
```

Choose from:
- `[0]` Full pipeline — all divisions, all teams (hitting + pitching)
- `[1]` Single division
- `[2]` Single team
- `[3]` Add a new Wild / Storm opponent
- `[4]` Manage seasons — create or switch the active season

Or skip the menu with flags:
```bash
bash launchers/run_scout.sh --division Majors
bash launchers/run_scout.sh --division Wild --team "QC Flight Baseball 11U"
```

### Option C — Nightly Scheduled Run (Automatic)

Runs daily at **10:00 AM EDT** via macOS `launchd`. Configured in:
```
launchers/com.wcwaa.scout_pipeline.plist
```

```bash
# Verify scheduled
launchctl list | grep wcwaa

# Trigger immediately
launchctl start com.wcwaa.scout_pipeline
```

### launchd Reference

The `.plist` is the schedule config (when to run); `~/Library/LaunchAgents/run_wcwaa_nightly.sh` is the local wrapper it triggers (what to run).

> **Execution chain:** plist → `~/Library/LaunchAgents/run_wcwaa_nightly.sh` (local disk) → `run_menu.py --all`
>
> **Auto-load resilience:** `~/.zprofile` contains a one-liner that re-registers the job on every login, in case macOS skipped it at boot (e.g., Google Drive not yet mounted). No manual `launchctl load` needed after reboots.
>
> **Why a local wrapper?** The plist invokes a script on the local filesystem (not Google Drive) so launchd can always execute it regardless of GDrive mount state. The wrapper then reaches into the GDrive repo to call `run_menu.py`.

| Action | Command |
|---|---|
| **Check if scheduled** | `launchctl list \| grep wcwaa` — look for `com.wcwaa.scout_pipeline` in output |
| **Check last exit code** | `launchctl list com.wcwaa.scout_pipeline` — `"LastExitStatus" = 0` means success |
| **Disable** | `launchctl unload ~/Library/LaunchAgents/com.wcwaa.scout_pipeline.plist` |
| **Re-enable** | `launchctl load ~/Library/LaunchAgents/com.wcwaa.scout_pipeline.plist` |
| **Change time** | Edit `Hour` in the plist, then unload + reload |

Plist location: `launchers/com.wcwaa.scout_pipeline.plist` (symlinked to `~/Library/LaunchAgents/`).

---

## Pipeline Steps

| Step | Script | What it does |
|---|---|---|
| 1 | `scrape_gc_playbyplay.py` | Scrapes GC schedule pages → saves .txt game files |
| 2 | `scrape_gc_boxscores.py` | Scrapes GC box scores → builds rosters |
| 3 | `gen_hitting.py` | Parses game files → computes batting stats → generates hitting PDFs |
| 4 | `gen_pitching.py` | Parses game files → computes pitching stats → generates Savant-style pitching PDFs |

---

## Running Individual Parts

```bash
# Regenerate hitting PDFs for one team (no scraping)
python3 src/hitting/gen_hitting.py --division Majors --team Cubs

# Regenerate pitching PDFs for one division
python3 src/pitching/gen_pitching.py --division Majors

# Scrape one division only
python3 src/scraping/scrape_gc_playbyplay.py --division Storm

# Check what new games are available without downloading
python3 src/scraping/scrape_gc_playbyplay.py --check

# Launch just the web UI (without the .command launcher)
python3 src/web/server.py
```

---

## Output Files

| File | Location | Description |
|---|---|---|
| `*-Scout-Hitting_2026.pdf` | Division report folders | Hitting scouting reports |
| `*-Scout-Pitching_2026.pdf` | Division report folders | Pitching scouting reports |
| `rosters.json` | `seasons/2026-spring/Majors/Reports/`, `.../Minors/Reports/` | Player names + jersey numbers |
| `roster.txt` | `seasons/2026-spring/Wild/[Team]/`, `.../Storm/[Team]/` | Travel opponent rosters |
| `*.txt` game files | Scorebooks/Games folders | Play-by-play from GC |

> All season data files and PDFs live under `seasons/` and are gitignored. See `examples/` for samples.

---

## Project Structure

```
Scout/                           <- repo root
|-- README.md
|-- Instructions.md              <- detailed AI session context file
|-- CHANGELOG.md                 <- unified version history
|-- BUGS.md                      <- unified bug tracker
|-- requirements.txt
|-- config/
|   |-- 2026-spring.yaml          <- season data: teams, GC IDs, paths
|   +-- active_season.txt         <- one line: "2026-spring"
|-- src/
|   |-- season_config.py          <- central config loader (all scripts import this)
|   |-- hitting/                  <- gen_hitting.py, stat_analysis.py
|   |-- pitching/                 <- gen_pitching.py, pitcher_icon.png
|   |-- scraping/                 <- scrape_gc_playbyplay.py, scrape_gc_boxscores.py, parse_gc_text.py
|   |-- orchestrator/             <- run_menu.py
|   +-- web/                      <- server.py, index.html, css/, js/  (web UI)
|-- launchers/                    <- run_scout.sh, run_pitching.sh, *_nightly.sh,
|                                    Start Scout.command, com.wcwaa.scout_pipeline.plist
|-- sessions/                     <- gc_session.json [gitignored]
|-- logs/                         <- pipeline_summary.log [gitignored]
|-- seasons/2026-spring/          <- game data + PDFs [gitignored]
|   |-- Majors/  Minors/  Wild/  Storm/  Coach_Pitch/  AllStars/
+-- venv/                         <- shared Python venv [gitignored]
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `ImportError: playwright` or `flask` | venv not activated | `source venv/bin/activate` |
| `Session expired` | gc_session.json stale | `python3 src/scraping/scrape_gc_playbyplay.py --login` |
| `0 PAs` for a team | Folder name ≠ GC inning header | Check exact spelling |
| `?X X?` in output | Player not in roster | Run `scrape_gc_boxscores.py` |
| `WARNING UNKNOWN` | Unrecognised play description | Add to `OUTCOME_TYPES` |
| Web UI says "View-only" on the Mac | Server not running | Double-click `launchers/Start Scout.command` |

---

## Documentation

- **[Instructions.md](Instructions.md)** — Complete technical reference (design decisions, function maps, data formats). Load this at the start of any AI-assisted coding session.
- **[CHANGELOG.md](CHANGELOG.md)** — All version history with component tags.
- **[BUGS.md](BUGS.md)** — All known bugs and their resolution status.
