# WCWAA Scout Pipeline

![Version](https://img.shields.io/badge/version-5.1.0-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

Automated scouting report pipeline for Weddington youth baseball (league + travel/tournament teams).
Pulls play-by-play data from [GameChanger](https://web.gc.com), computes batting stats, player archetypes, and pitching percentiles, then generates multi-page PDF scouting reports — from one command, the web UI, or a nightly schedule.

---

## Divisions Covered

Divisions are defined **per season** in `config/<season>.yaml`. Two kinds:

| Type                    | Examples                  | Source                          | Reports                             |
| ----------------------- | ------------------------- | ------------------------------- | ----------------------------------- |
| **League**              | Majors (11U), Minors (9U) | GC league organization schedule | Every team in the league            |
| **Travel / Tournament** | Wild, Storm, Mavs         | Each listed team's GC schedule  | Each listed team (ours + opponents) |

Active season: **2026 Fall** — Majors, Minors, Wild, Mavs.

---

## First-Time Setup (Do This Once)

### 1. Prerequisites

- macOS with **Python 3.9+** (`python3 --version`)
- **Google Chrome** installed in `/Applications` — the scrapers drive it (GameChanger blocks hidden/automated browsers)

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
pip install -e .
```

### 5. Sign in to GameChanger (one time)

```bash
python -m scout.scraping.scrape_gc_playbyplay --login
```

A Chrome window opens using a separate **Scout profile** (your everyday Chrome is untouched).
Sign in, wait until your teams appear, then press **ENTER** in the terminal. The Scout profile
stays signed in for future runs.

> **When to repeat:** only when a run reports "GameChanger session expired". Check anytime with
> `python -m scout.scraping.scrape_gc_playbyplay --check-session`.

> All commands assume you're in the repo folder with the venv active:
> `cd ~/Documents/VSCode/Personal/Scout && source venv/bin/activate`

---

## User Options

### Option A — Web UI (Easiest)

Double-click **`launchers/Start Scout.command`** in Finder. This starts the local
web server and opens the app in your browser at **http://127.0.0.1:5050**.

From the app you can:

- **Build Reports** — pick a division → team → click Build; the pipeline log streams live on the page
- **View Reports** — browse every generated PDF and open it in one click
- **Add Team** — register a new tournament/travel team from a GameChanger URL
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
- `[3]` Add a new Tournament Team
- `[4]` Manage seasons — create or switch the active season

Or skip the menu with flags:

```bash
bash launchers/run_scout.sh --division Majors
bash launchers/run_scout.sh --division Mavs --team "Weddington Mavericks 10U"
bash launchers/run_scout.sh --all
```

### What you'll see while it runs

Every run starts with a **GameChanger session check**. During scraping (Steps 1–2) a second
Chrome icon appears in the Dock — its window is placed off-screen; **don't close it**. It closes
by itself, then the PDFs are built. If the session check fails, scraping is skipped, PDFs are
still rebuilt from saved games, and the message tells you what to run.

The Mac must be **awake and logged in** while scraping.

### Option C — Nightly Scheduled Run (Automatic)

Runs daily at **10:00 AM EDT** via macOS `launchd` (kept awake with `caffeinate`). If the Mac is
asleep at 10am, the run happens when it wakes. If the GameChanger login has expired, a macOS
notification tells you. Configured in:

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

> **Execution chain:** plist → `~/Library/LaunchAgents/run_wcwaa_nightly.sh` (local disk) → `python -m scout.orchestrator.run_menu --all`
>
> **Auto-load resilience:** `~/.zprofile` contains a one-liner that re-registers the job on every login. No manual `launchctl load` needed after reboots.
>
> **Why a local wrapper?** launchd runs a script on the local disk; its `SCOUT=` line points at the repo folder (update it if the repo moves).

| Action                   | Command                                                                          |
| ------------------------ | -------------------------------------------------------------------------------- |
| **Check if scheduled**   | `launchctl list \| grep wcwaa` — look for `com.wcwaa.scout_pipeline` in output   |
| **Check last exit code** | `launchctl list com.wcwaa.scout_pipeline` — `"LastExitStatus" = 0` means success |
| **Disable**              | `launchctl unload ~/Library/LaunchAgents/com.wcwaa.scout_pipeline.plist`         |
| **Re-enable**            | `launchctl load ~/Library/LaunchAgents/com.wcwaa.scout_pipeline.plist`           |
| **Change time**          | Edit `Hour` in the plist, then unload + reload                                   |

Plist location: `launchers/com.wcwaa.scout_pipeline.plist` (symlinked to `~/Library/LaunchAgents/`).

---

## Pipeline Steps

| Step      | Script                                 | What it does                                                                              |
| --------- | -------------------------------------- | ----------------------------------------------------------------------------------------- |
| Preflight | `scrape_gc_playbyplay --check-session` | Confirms GameChanger answers the Scout Chrome profile                                     |
| 1         | `scrape_gc_playbyplay`                 | Scrapes GC schedule pages → saves .txt game files (skips games already saved or excluded) |
| 2         | `scrape_gc_boxscores`                  | Scrapes GC box scores → builds rosters                                                    |
| 3         | `gen_hitting`                          | Parses game files → computes batting stats → generates hitting PDFs                       |
| 4         | `gen_pitching`                         | Parses game files → computes pitching stats → generates Savant-style pitching PDFs        |

---

## Running Individual Parts

```bash
# Rebuild every PDF in a division (no scraping) — refreshes LG RANK / percentiles for all teams
python -m scout.hitting.gen_hitting --division Mavs
python -m scout.pitching.gen_pitching --division Mavs

# Regenerate hitting PDFs for one team (no scraping)
python -m scout.hitting.gen_hitting --division Majors --team Cubs

# Scrape one division only
python -m scout.scraping.scrape_gc_playbyplay --division Wild

# Check what new games are available without downloading
python -m scout.scraping.scrape_gc_playbyplay --division Wild --check

# Launch just the web UI (without the .command launcher)
python -m scout.web.server
```

> **LG RANK** (league rank row) compares every team in the division and needs at least two teams.
> A single-team run only rewrites that team's PDFs — run the division-wide rebuild above after
> adding a new team so everyone's ranks update.

### Skipping scrimmages

Add the game's GC ID (from its `/schedule/<id>/plays` URL) under the team in the season YAML:

```yaml
- name: Weddington Mavericks 10U
  exclude_games:
    - 1f0e0307-13db-4031-8533-57cddeb36db1
```

If it was already scraped, move its file out of `Games/` and rebuild that division.

---

## Output Files

| File                        | Location                                                  | Description                      |
| --------------------------- | --------------------------------------------------------- | -------------------------------- |
| `*-Scout-Hitting_2026.pdf`  | Division report folders                                   | Hitting scouting reports         |
| `*-Scout-Pitching_2026.pdf` | Division report folders                                   | Pitching scouting reports        |
| `rosters.json`              | `seasons/<season>/Majors/Reports/`, `.../Minors/Reports/` | Player names + jersey numbers    |
| `roster.txt`                | `seasons/<season>/<TravelDiv>/<Team>/`                    | Travel / tournament team rosters |
| `*.txt` game files          | Scorebooks/Games folders                                  | Play-by-play from GC             |

> Season data and PDFs live on Google Drive (`SCOUT_DATA_ROOT`, default
> `~/Library/CloudStorage/GoogleDrive-.../WCWAA/Scout/data/real/seasons/`) — never in git.
> See `data/samples/` for examples.

---

## Project Structure

```
Scout/                           <- repo root (~/Documents/VSCode/Personal/Scout)
|-- README.md
|-- AGENTS.md                    <- detailed technical reference (load for AI sessions)
|-- pyproject.toml / requirements.txt
|-- config/
|   |-- 2026-Fall.yaml  2026-spring.yaml   <- per-season divisions, teams, GC IDs
|   |-- season_template.yaml
|   +-- active_season.txt                  <- e.g. "2026-Fall"
|-- dev/
|   |-- src/scout/                <- the `scout` Python package
|   |   |-- season_config.py      <- central config loader
|   |   |-- scraping/             <- gc_browser.py, scrape_gc_playbyplay.py, scrape_gc_boxscores.py, parse_gc_text.py
|   |   |-- hitting/  pitching/   <- report generators
|   |   |-- orchestrator/         <- run_menu.py
|   |   +-- web/                  <- server.py + front-end
|   +-- tests/                    <- python -m unittest discover -s dev/tests
|-- docs/                         <- CHANGELOG.md, BUGS.md, Principles and Practices.md
|-- launchers/                    <- run_scout.sh, Start Scout.command, nightly scripts, launchd plist
|-- data/real/                    <- [gitignored] logs/ + sessions/gc_chrome_profile (GC login)
+-- venv/                         <- [gitignored]
```

---

## Troubleshooting

| Symptom                                                         | Likely Cause                             | Fix                                                                                                                  |
| --------------------------------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `ImportError: playwright` or `flask`                            | venv not activated                       | `source venv/bin/activate`                                                                                           |
| "GameChanger session expired"                                   | Scout profile signed out                 | `python -m scout.scraping.scrape_gc_playbyplay --login`                                                              |
| "GameChanger refused the Scout browser" / `0 FINAL games found` | GC blocking, or Chrome didn't start      | `--check-session -v`; see BUG-022 in `docs/BUGS.md`                                                                   |
| "Port 9223 is already in use"                                   | Another run (or Scout Chrome) still open | Wait / close it and retry                                                                                            |
| `0 PAs` for a team                                              | Folder name ≠ GC inning header           | Punctuation-only differences (e.g. `OC Crushers - Blue 11U`) are auto-renamed and logged; otherwise fix the spelling |
| `?X X?` in output                                               | Player not in roster                     | Run `scrape_gc_boxscores`                                                                                            |
| `WARNING UNKNOWN`                                               | Unrecognised play description            | Add to `OUTCOME_TYPES`                                                                                               |
| No LG RANK row                                                  | Only one team in the division            | Add teams, then rebuild the division                                                                                 |
| Web UI says "View-only" on the Mac                              | Server not running                       | Double-click `launchers/Start Scout.command`                                                                         |

---

## Documentation

- **[AGENTS.md](AGENTS.md)** — Complete technical reference (design decisions, function maps, data formats). Load this at the start of any AI-assisted coding session.
- **[docs/CHANGELOG.md](docs/CHANGELOG.md)** — Version history with component tags.
- **[docs/BUGS.md](docs/BUGS.md)** — Issue tracker: bugs, enhancements (the open backlog), and known caveats.
