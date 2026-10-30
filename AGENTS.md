# WCWAA Scout Pipeline

This file is the authoritative reference for the WCWAA Scout pipeline.
Load it at the start of every new AI coding session (GitHub Copilot, Claude, etc.).
It covers every design decision, known bug, and operational detail accumulated
across the full build history of this project.

**Code root (all repo-relative paths below are relative to this):**
`~/Documents/VSCode/Personal/Scout/`

**Data root (season reports — kept on Google Drive so they sync + view anywhere):**
`~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My Drive/Baseball/WCWAA/Scout/data/real/`
Override with the `SCOUT_DATA_ROOT` env var. Only `seasons/` (and `_archive/`) lives here; logs +
the GameChanger login (Scout Chrome profile) stay local under the code root at `data/real/{logs,sessions}`.

**Best practices prompt:** When starting a new session, the user may paste their
"Code Mentor" prompt which defines conventions for debugging, git hygiene, error
handling, and code style. Follow those guidelines throughout.

---

## Current State

| Field             | Value                                                                                                             |
| ----------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Version**       | 5.3.1                                                                                                             |
| **Last commit**   | `fix: v5.3.1 — blank hitting report for spaced team names; true batting order for cards` (tag `v5.3.1`)           |
| **Branch**        | `main`                                                                                                            |
| **Uncommitted**   | User's web UI edits (`web/index.html`, `web/js/app.js`); Spring 2026 roster rebuild (BUG-036 note) — next session |
| **Code location** | `~/Documents/VSCode/Personal/Scout/` (moved off Google Drive 2026-08)                                             |
| **Data location** | season reports on Google Drive via `SCOUT_DATA_ROOT` (default `.../WCWAA/Scout/data/real`)                        |

### Session Handoff Protocol

When starting a new session on this project:

1. **Load this file first** — it's the authoritative context document
2. **Read the Code Mentor principles** — user may re-paste them; follow them throughout
3. **Check `git status`** — note any uncommitted changes before touching anything
4. **Check `active_season.txt`** — confirms which season config is active
5. **Scan `[Unreleased]` in CHANGELOG.md** — see what work is in-flight
6. **Review open items in [docs/BUGS.md](docs/BUGS.md)** — the single backlog: `(O)`/`(IP)` bugs and `(Enh)` items (rules: `docs/Principles and Practices.md` §12)

At session end, update this **Current State** table with the latest version and last commit SHA before closing.

---

## Development Environment

- **Python 3.9.6** (macOS system Python)
- **Virtual environment:** `venv/` (repo root) — shared across all components; always activate before running scripts
- **Package install:** `pip install -e .` (via `pyproject.toml`) exposes the `scout` package; run entry points as `python -m scout.<pkg>.<module>`
- **Key packages:** Playwright 1.58.0 (CDP driver only), ReportLab 4.4.10, Flask, PyYAML
- **Google Chrome** must be installed in `/Applications` — scraping drives it (BUG-022). Playwright's bundled Chromium is unused.
- **Tests:** `python -m unittest discover -s dev/tests`
- **Frozen deps:** `requirements.txt` in repo root
- **Git:** Local repo at `~/Documents/VSCode/Personal/Scout/` on `main` branch. Season data lives separately on Google Drive (see Data root above).
- **GitHub remote:** `https://github.com/mdesau/Scouting_Pipeline` (private)
  - PAT stored in `.git/config` remote URL — rotate at github.com/settings/tokens if needed

### Version History

```
v5.3.1  fix: hitting report blank for team names with a space (BUG-041); cards in true typical batting order (BUG-042)
v5.3.0  feat: quality-pitcher availability on game lines + LL consecutive-days rule (BUG-039 Enh); box-score pitching = official starter/pitch counts (BUG-040)
v5.2.2  fix: roster name collisions + jersey rule (BUG-036); late additions + Majors draft/bracket (BUG-037 Enh); division prompt (BUG-038 Enh)
v5.2.1  feat: one command for all three analysis tools (run_all / run_analysis.sh, BUG-035 Enh)
v5.2.0  feat: analysis tools — usage workbook, tournament odds, draft report card (BUG-030/031/032 Enh); README rewrite; nightly 10 AM fix
v5.1.0  feat: auto-rename travel-team folders on GC header mismatch (BUG-023 Enh); BUGS.md restructured to §12
v5.0.0  feat!: scrape via real Google Chrome + Scout profile (GC blocks headless, BUG-022), session preflight, per-season divisions
v4.0.0  refactor!: dev/src/scout installable package layout + SCOUT_DATA_ROOT
v3.4.0  feat: Create / Modify Season UI + optional Majors/Minors + Tournament Teams (per-season travel divisions)
v3.3.2  fix: BUG-020 — report PDFs 404 in web UI (season id dropped from /report path)
v3.3.1  fix: BUG-019 stale server detection + X-Scout-Version response header
v3.3.0  feat: per-tab season selectors in web UI (BUG-018) + "All seasons" View Reports filter
v3.2.1  docs: Instructions.md refactor
v3.2.0  feat: season management — list/create/switch seasons (terminal + web UI)
v3.1.3  fix: BUG-017 — newly added team missing from web UI dropdown + alphabetical sort
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

> **The open backlog lives in [docs/BUGS.md](docs/BUGS.md)** as `BUG-### (Enh)` / `BUG-###` entries
> (one canonical tracker, per `docs/Principles and Practices.md` §12). Former items #5–#7 moved
> there as BUG-024, BUG-025, BUG-026. This table keeps the completed milestones for history.

| #   | Item                                                                  | Status   | Target Version | Notes                                                                                                                                                                                          |
| --- | --------------------------------------------------------------------- | -------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Optimize directory structure for growth and future seasons            | ✅ Done  | v3.0.0         | `src/`, `launchers/`, `config/`, `seasons/`, YAML season config                                                                                                                                |
| 2   | Build a user-friendly HTML front end ("HTML-based app")               | ✅ Done  | v3.1.0         | Local Flask web UI (`src/web/`): build reports with live log, view PDFs, add teams. Double-click `launchers/Start Scout.command`. Build on Mac, view anywhere (incl. mobile via Google Drive). |
| 3   | Season management — create/switch seasons without manual YAML editing | ✅ Done  | v3.2.0         | `season_config.list_seasons/create_season/set_active_season`; terminal wizard `[4] Manage seasons`; web UI Seasons tab + header season picker                                                  |
| 4   | Per-tab season selectors in web UI (BUG-018)                          | ✅ Done  | v3.3.0         | Build/View/Add Team each have their own season dropdown; View Reports has an "All seasons" option                                                                                              |
| 5   | Dynamic archetypes                                                    | ➡️ Moved | —              | [BUG-024 (Enh)](docs/BUGS.md#bug-024-enh--status-o)                                                                                                                                            |
| 6   | Drop the `TEAM` row from travel `roster.txt`                          | ➡️ Moved | —              | [BUG-025 (Enh)](docs/BUGS.md#bug-025-enh--status-o)                                                                                                                                            |
| 7   | Rebuild the whole travel division on single-team runs                 | ➡️ Moved | —              | [BUG-026 (Enh)](docs/BUGS.md#bug-026-enh--status-o)                                                                                                                                            |

---

## Project Summary

Scout is a single automated pipeline for generating scouting reports for Weddington youth baseball. It has two report components:

| Component    | Purpose                                                                                                            | Output                      |
| ------------ | ------------------------------------------------------------------------------------------------------------------ | --------------------------- |
| **Hitting**  | Scrapes GameChanger, computes batting stats + archetypes, generates hitting PDFs                                   | `*-Scout-Hitting_2026.pdf`  |
| **Pitching** | Reads same game files, computes pitching stats + league percentiles, generates Baseball Savant-style pitcher cards | `*-Scout-Pitching_2026.pdf` |

Both components share the same virtual environment, game file data, and scraping infrastructure. Users can run hitting only, pitching only, or both together — from the terminal menu, CLI flags, the nightly scheduler, or the **web UI** (`scout/web/`). All entry points ultimately drive the same `run_menu.py` pipeline.

### Divisions

Two division **types**, set per season in the YAML:

| Type                    | Examples                  | Scraped from                      | Reports                                 |
| ----------------------- | ------------------------- | --------------------------------- | --------------------------------------- |
| **League** (`league`)   | Majors (11U), Minors (9U) | GC organization schedule (org ID) | Every team in the league                |
| **Travel / Tournament** | Wild, Storm, Mavs         | Each listed team's GC schedule    | Each listed team (our team + opponents) |

> Divisions are **per season** — the season YAML is the only list. Code never hardcodes
> Majors/Minors/Wild/Storm; it reads `DIVISIONS` and dispatches on type (`org`/league vs.
> travel). Travel divisions can be switched off with `active: false`. 2026-Fall: Majors, Minors,
> Wild, and the tournament division **Mavs** (Storm inactive). See "Teams Reference".

---

## Scripts Overview (approx. line counts as of v5.0.0, Oct 2026)

All paths below are under `dev/src/scout/`.

| Script                             | Lines | Component    | Role                                                                                                                                                                |
| ---------------------------------- | ----- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --- | ---------------------------------- | ---- | -------- | ------------------------------------------------------------------------------------ |
| `hitting/gen_hitting.py`           | ~2140 | Hitting      | Stat engine + PDF generator                                                                                                                                         |
| `pitching/gen_pitching.py`         | ~1300 | Pitching     | Stat engine + PDF generator                                                                                                                                         |
| `orchestrator/run_menu.py`         | ~1160 | Orchestrator | Pipeline orchestrator (preflight + 4 steps) + add-team wizard + season management                                                                                   |
| `season_config.py`                 | ~960  | Config       | Central loader: reads `config/<season>.yaml`, builds DIVISIONS dicts, `add_team_to_yaml()`, season lifecycle (`list_seasons`, `create_season`, `set_active_season`) |
| `scraping/scrape_gc_boxscores.py`  | ~780  | Scraping     | GC box scores → rosters                                                                                                                                             |
| `web/server.py`                    | ~760  | Web          | Flask server backing the HTML front-end (build/view/add/seasons/logs)                                                                                               |
| `hitting/stat_analysis.py`         | ~600  | Hitting      | Distribution/percentile analysis → HTML report (feeds dynamic archetypes, BUG-024 Enh)                                                                              |
| `scraping/scrape_gc_playbyplay.py` | ~590  | Scraping     | GC schedule → .txt game files; `--login` / `--check-session` entry points                                                                                           |
| `scraping/parse_gc_text.py`        | ~270  | Parser       | Raw GC text → WCWAA format (utility)                                                                                                                                |
| `scraping/gc_browser.py`           | ~210  | Scraping     | Launch/drive real Chrome (Scout profile) + GC session check (v5.0.0)                                                                                                |
| `scraping/diag_schedule.py`        | ~144  | Scraping     | Schedule diagnostics (legacy utility — still headless, non-functional since BUG-022)                                                                                |     | `analysis_tools/pitching_usage.py` | ~500 | Analysis | League workbook: pitcher usage, team usage, team comparison (+ top-3 QP), draft tabs |
| `analysis_tools/tourney_odds.py`   | ~640  | Analysis     | Monte Carlo tournament futures → dated PDF board (bracket from season YAML `postseason:`)                                                                           |
| `analysis_tools/draft_roi.py`      | ~420  | Analysis     | Draft grades, per-pick ROI, steals/busts → PDF + workbook tabs                                                                                                      |
| `analysis_tools/games.py`          | ~110  | Analysis     | Shared: runs per half-inning from GC score strings, dates, postseason config, weather rollbacks; cached `division_data()`, `rerun_commands()`                       |
| `analysis_tools/run_all.py`        | ~80   | Analysis     | One command for all three tools: scrape once, parse once, build workbook + odds PDF + draft card                                                                    |

> **Web front-end assets** (not Python): `web/index.html` (~250 lines), `web/css/style.css` (~260 lines), `web/js/app.js` (~770 lines).
>
> **Tests:** `dev/tests/test_fall_league_readiness.py` (play-by-play validation, session classification, league team discovery, folder reconcile) and `dev/tests/test_analysis_tools.py` (draft snake order, name matching, rest rules, odds, rollbacks).

### Shell Launchers (all in `launchers/`)

| Script                                        | Purpose                                                                                                                                                                                                                                        |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `launchers/Start Scout.command`               | **Double-click launcher** for the web UI: activates venv, starts `python -m scout.web.server`, opens browser at http://127.0.0.1:5050                                                                                                          |
| `launchers/run_scout.sh`                      | Manual launcher: activates venv, calls `run_menu.py` (interactive menu or `--division`/`--team` passthrough)                                                                                                                                   |
| `launchers/run_scout_nightly.sh`              | Headless launcher for manual testing; calls `run_menu.py --all` under `caffeinate -i`                                                                                                                                                          |
| `~/Library/LaunchAgents/run_wcwaa_nightly.sh` | **Actual nightly launcher** (local disk): called by the launchd plist; `cd`s into the code root and runs `caffeinate -i python -m scout.orchestrator.run_menu --all`. Lives outside the repo — **update its `SCOUT=` path if the repo moves.** |
| `launchers/run_pitching.sh`                   | Standalone manual launcher for pitching PDFs only                                                                                                                                                                                              |
| `launchers/run_pitching_nightly.sh`           | Standalone headless launcher for pitching PDFs only                                                                                                                                                                                            |
| `launchers/run_analysis.sh`                   | All three analysis tools for a league division (`--division`, `--no-scrape`) → `scout.analysis_tools.run_all`                                                                                                                                  |
| `launchers/com.wcwaa.scout_pipeline.plist`    | launchd schedule config (symlinked to `~/Library/LaunchAgents/`)                                                                                                                                                                               |

---

## Directory Structure

```
Scout/                               <- git repo root (~/Documents/VSCode/Personal/Scout)
|-- .git/
|-- .gitignore
|-- README.md                        <- project overview
|-- AGENTS.md                        <- this file
|-- pyproject.toml                   <- editable-install config (pip install -e .) -> `scout` package
|-- requirements.txt                 <- pip freeze (Flask, Playwright, ReportLab, PyYAML)
|
|-- config/                          <- season configuration (the only place teams live)
|   |-- 2026-spring.yaml             <- single source of truth: GC IDs, slugs, coaches, paths
|   |-- 2026-Fall.yaml
|   |-- season_template.yaml         <- scaffold for new seasons (used by create_season())
|   +-- active_season.txt            <- one line: e.g. "2026-Fall" (switch seasons here)
|
|-- dev/
|   +-- src/scout/                   <- the `scout` Python package (all source)
|       |-- season_config.py         <- central loader: SCOUT_ROOT, DATA_ROOT, SEASONS_ROOT,
|       |                               LOGS_DIR, SESSIONS_DIR, SEASON_DIR,
|       |                               build_scraper_divisions(), build_hitting_divisions(),
|       |                               list_divisions(), add_team_to_yaml(), season lifecycle.
|       |-- hitting/
|       |   |-- gen_hitting.py        <- Step 3: stat engine + hitting PDFs
|       |   |-- stat_analysis.py      <- distribution/percentile analysis -> HTML report
|       |   +-- archetype_reference.txt
|       |-- pitching/
|       |   |-- gen_pitching.py       <- Step 4: stat engine + pitching PDFs
|       |   +-- pitcher_icon.png      <- Savant-style pitcher silhouette
|       |-- scraping/
|       |   |-- gc_browser.py            <- real Chrome (Scout profile) launcher + GC session check
|       |   |-- scrape_gc_playbyplay.py  <- Step 1: GC schedule -> .txt game files (+ --login, --check-session)
|       |   |-- scrape_gc_boxscores.py   <- Step 2: GC box scores -> rosters
|       |   |-- parse_gc_text.py         <- utility: raw GC text -> WCWAA format
|       |   +-- diag_schedule.py         <- utility: schedule diagnostics
|       |-- orchestrator/
|       |   +-- run_menu.py           <- pipeline orchestrator (Steps 1-4) + add-team + seasons
|       |-- analysis_tools/           <- on-demand league analysis (not part of the nightly pipeline)
|       |   |-- games.py              <- shared run/score/date parsing + postseason config (cached per division)
|       |   |-- run_all.py            <- all three tools in one run (launchers/run_analysis.sh)
|       |   |-- pitching_usage.py     <- league workbook (usage, team comparison, QP, draft tabs)
|       |   |-- tourney_odds.py       <- tournament futures PDF
|       |   +-- draft_roi.py          <- draft report card PDF
|       +-- web/                      <- HTML front-end
|           |-- server.py             <- Flask server (build/view/add + live log SSE)
|           |-- index.html            <- single-page app shell
|           |-- css/style.css
|           +-- js/app.js
|
|-- docs/                            <- CHANGELOG.md, BUGS.md, Principles and Practices.md
|-- dev/tests/                       <- unittest suite (python -m unittest discover -s dev/tests)
|-- dev/tmp/                         <- [gitignored] scratch probes / mockups
|-- data/samples/                    <- example game file + sample scouting PDF (tracked)
|
|-- launchers/                       <- all shell scripts + launchd plist (see table above)
|
|-- data/real/                       <- [gitignored] LOCAL runtime data (stays with the code)
|   |-- logs/                        <- dated run logs + pipeline_summary.log
|   +-- sessions/
|       |-- gc_chrome_profile/       <- Scout Chrome profile = the GC login (never commit)
|       +-- gc_session.json          <- legacy (pre-v5.0.0), unused by the scrapers
|
+-- venv/                            <- shared Python venv [gitignored]


Google Drive (data root -- set by SCOUT_DATA_ROOT; default shown):
~/Library/CloudStorage/.../WCWAA/Scout/data/real/
|-- _archive/                        <- set-aside data (e.g. 2026-Fall_backup_2026-10-26, excluded games)
+-- seasons/                         <- [not in repo] all season report data
    +-- 2026-Fall/  2026-spring/ ...
        |-- Majors/Reports/          <- Scorebooks/, Scouting_Reports/, rosters.json, box_verify.json
        |-- Minors/Reports/          <- same structure
        |-- <TravelDiv>/[TeamName]/  <- Wild/, Storm/, Mavs/ ...: Games/, roster.txt, *-Scout-*.pdf
        |-- AllStars/                <- one-time AllStars builds (9U, 12U)
        +-- Coach_Pitch/
```

> **Note (code/data split):** Code lives under the repo root (`~/Documents/VSCode/Personal/Scout`).
> Season report data lives on Google Drive, resolved via `SEASONS_ROOT = DATA_ROOT/seasons`
> where `DATA_ROOT` = the `SCOUT_DATA_ROOT` env var (default: the GDrive `.../Scout/data/real`).
> Logs + the GC login (Scout Chrome profile) stay local under the code root at `data/real/{logs,sessions}`.
> All code anchors paths to `__file__`/env via `season_config.py`, so the repo can be
> relocated freely (as in this 2026-08 move from `WCWAA/Scout/` to `~/Documents/VSCode/Personal/Scout`).

---

## Pipeline Workflow

The pipeline runs a preflight + 4 steps, orchestrated by `run_menu.py`:

| Step      | Script                                    | What it does                                                                                                         |
| --------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Preflight | `scrape_gc_playbyplay.py --check-session` | Opens Scout Chrome, confirms GC answers. Fail → Steps 1–2 skipped, 3–4 still run; nightly shows a macOS notification |
| 1         | `scrape_gc_playbyplay.py`                 | Scrapes GC schedule pages, downloads play-by-play, saves .txt game files                                             |
| 2         | `scrape_gc_boxscores.py`                  | Scrapes GC box scores, builds/updates rosters.json + roster.txt                                                      |
| 3         | `gen_hitting.py`                          | Parses game files, computes batting stats + archetypes, generates hitting PDFs                                       |
| 4         | `gen_pitching.py`                         | Parses same game files, computes pitching stats + percentiles, generates pitching PDFs                               |

Step 1 skips games already on disk (safe to re-run) and any game listed in `exclude_games`. Step 2 is incremental by default (`--force` rebuilds rosters from scratch).

**Completed-game detection:** org pages (Majors/Minors) show `FINAL`; team pages show a
result like `W 7-5`, `L 9-11`, or `T 4-4` (`SCHEDULE_JS`, both scrapers).

**Single-team runs and rankings:** LG RANK (hitting) and percentiles (pitching) compare every
team in the division, but a `--team` run only rewrites that team's PDFs. After adding/scraping a
new team, refresh the rest with `gen_hitting --division X` + `gen_pitching --division X`
(no scraping, seconds). LG RANK is disabled when a travel division has only one team.

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

**Option C -- nightly scheduled (launchd at 10am EDT):**

```bash
launchctl list | grep wcwaa          # verify scheduler active
launchctl start com.wcwaa.scout_pipeline  # trigger immediately
```

> **Execution chain:** plist (symlinked from `launchers/`) → `~/Library/LaunchAgents/run_wcwaa_nightly.sh` (local disk) → `python -m scout.orchestrator.run_menu --all`
>
> **Auto-load:** `~/.zprofile` re-registers the job on every login (`launchctl load`
> of the plist symlink) so it survives reboots. The symlink must point at the repo's
> `launchers/com.wcwaa.scout_pipeline.plist`; the wrapper's `SCOUT=` must point at the code root.

**Option D -- CLI direct:**

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

**Step-by-step manual** (from the code root, venv active):

```bash
python -m scout.scraping.scrape_gc_playbyplay --check-session  # Preflight
python -m scout.scraping.scrape_gc_playbyplay --division Mavs   # Step 1 (--check = dry run)
python -m scout.scraping.scrape_gc_boxscores --division Mavs    # Step 2
python -m scout.hitting.gen_hitting --division Mavs             # Step 3
python -m scout.pitching.gen_pitching --division Mavs           # Step 4
```

---

## GameChanger Access (Scout Chrome) — v5.0.0, BUG-022

**Why:** GC's firewall (AWS WAF) returns 403 to every headless or Playwright-launched browser.
It only serves a normal, visible Google Chrome window. A valid login does not help.

**How it works** (all in `scout/scraping/gc_browser.py`):

1. The scraper launches installed Google Chrome as a plain process with the **Scout profile**
   (`data/real/sessions/gc_chrome_profile` — separate from the user's everyday Chrome) and a
   local-only DevTools port (127.0.0.1:9223). The window is placed off-screen.
2. Playwright attaches over CDP (`connect_over_cdp`) and drives the page. Playwright is now only
   the driver; its bundled Chromium is unused.
3. Chrome is closed gracefully (CDP `Browser.close`) when Steps 1–2 finish.

GC auth lives in the profile's localStorage (`eden-auth-tokens`), so it persists between runs.
`gc_session.json` is legacy and not read by the scrapers.

**Commands:**

```bash
python -m scout.scraping.scrape_gc_playbyplay --login           # sign in (on-screen window, press ENTER when teams show)
python -m scout.scraping.scrape_gc_playbyplay --check-session   # exit 0 ok | 2 signed out | 3 blocked/Chrome error
```

`--login` is only needed when the session check says the login expired (password change,
GC forced sign-out, profile reset).

**Runtime requirements & behavior:**

| Mac state at run time  | Result                                                                           |
| ---------------------- | -------------------------------------------------------------------------------- |
| Awake, logged in       | Runs; a second Chrome icon appears in the Dock during Steps 1–2 — don't close it |
| Asleep at 10am         | launchd runs the missed job once on wake                                         |
| Shut down / logged out | Job doesn't run until next schedule after login                                  |
| Screen locked          | Untested                                                                         |
| Sleeps mid-run         | Prevented by `caffeinate -i` in the nightly wrappers                             |

Only one Scout Chrome at a time (port 9223). The web UI run lock already serializes builds;
a manual run overlapping the 10am nightly would fail fast with "port in use".

---

## Analysis Tools (`scout.analysis_tools`) — on demand, not in the nightly pipeline

League-division analysis built on the same game files. **All three at once** (scrapes Steps 1–2 once,
parses games once via the cached `games.division_data()`, then builds every report):
`bash launchers/run_analysis.sh --division Minors` = `python -m scout.analysis_tools.run_all --division Minors`
(`--no-scrape` to reuse saved games). Individually (after scraping):

| Command                                                           | Output (in `<Div>/Reports/` on the data root)                                                     |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `python -m scout.analysis_tools.pitching_usage --division Minors` | `<season>_<Div>_Pitching_Usage_and_Team_Comparison.xlsx` (usage, team comparison, QP, draft tabs) |
| `python -m scout.analysis_tools.tourney_odds --division Minors`   | `<season>_<Div>_Tournament_Futures_asof_<last game date>.pdf`                                     |
| `python -m scout.analysis_tools.draft_roi --division Minors`      | `<season>_<Div>_Draft_Report_Card.pdf` + `.xlsx` (same content) + rebuilds the workbook           |

**Season inputs (no code edits needed):**

- **Draft:** the division's `csv:` path in the season YAML (rows = rounds, columns = coaches, last row =
  team names; snake order in round-1 column order).
- **Playoffs:** the division's `postseason:` block — `start`, `bracket` (`game: [date, slotA, slotB]`,
  slots are team keys or `W#`/`L#`), `order`, `winners_final`, `final`, `if_necessary`, plus
  `seeding_games` / `seeding_games_by_team`, `official_records` (W/L/T overrides) and `rollbacks`
  (`game-uuid: last official inning`, e.g. weather). Games on/after `start` count as playoffs.

**Model notes:** runs per half-inning come from GC's running score strings (match every final score).
Pitcher ratings (`tourney_odds.build_ratings`) are opponent-adjusted runs-allowed indexes; the odds
sim enforces 2-inning / 50-pitch limits, rest days (1–20 = 0, 21–35 = 1, 36–50 = 2) and no 3 straight days
(`record_outing` / `eligible`); game lines list each team's top-3 quality arms available. Who pitched and
pitch counts come from box-score pitching tables (`box_verify.json` `*_pitching`, reconciled in
`pitching_usage._apply_box`); play-by-play supplies pitch-level detail. Draft value =
batting linear-weight runs above average + pitching runs saved, per team game.

---

## Function Map -- Hitting Component

> Function maps list **name + purpose** only — no line numbers (they drift on every edit).
> Use your editor's "Go to Symbol" (⇧⌘O in VS Code) to jump to any function by name.

### scrape_gc_playbyplay.py (Step 1 -- Playwright scraper)

Navigates GC schedule pages, finds FINAL games, downloads play-by-play text, converts via `parse_gc_text.py`, saves `.txt` game files.

| Function                 | Purpose                                                                                                                                                                        |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Entry**                |                                                                                                                                                                                |
| `run()`                  | CLI entry point -- parses `--division`, `--team`, `--login`, `--check-session`, `--check`, `--force`, `--verbose`; runs via `gc_browser.run_with_session()`; returns exit code |
| **Scrapers**             |                                                                                                                                                                                |
| `scrape_org_division()`  | Org-level scraper (Majors/Minors): loads org schedule, finds FINAL games                                                                                                       |
| `scrape_team_division()` | Team-level scraper (travel divisions): loads per-team schedule page                                                                                                            |
| **Extraction**           |                                                                                                                                                                                |
| `extract_plays_raw()`    | Navigates to `/plays` URL, extracts raw page text; rejects logged-out / inning-less pages (`_has_valid_plays_content()`, BUG-021)                                              |
| `get_schedule()`         | Runs `SCHEDULE_JS` in browser, returns parsed schedule array                                                                                                                   |
| `is_covered()`           | Checks whether a game file already exists on disk (skip logic)                                                                                                                 |
| `SCHEDULE_JS`            | JS injected into browser to extract game cards from GC's React DOM                                                                                                             |
| **Helpers**              |                                                                                                                                                                                |
| `setup_logging()`        | Configures file + console logging with `--verbose` support                                                                                                                     |
| `fmt_date()`             | Normalizes GC date strings to `MonDD` format for filenames                                                                                                                     |
| `safe()`                 | Sanitizes team name for use in filenames                                                                                                                                       |
| **Config**               |                                                                                                                                                                                |
| `DIVISIONS` dict         | `build_scraper_divisions()` from `season_config` (loaded from `config/<season>.yaml`) -- **do NOT edit here; edit the YAML or use the add-team wizard**                        |

**Dependencies:** `parse_gc_text.parse_gc_raw()`, `season_config.build_scraper_divisions()`, `gc_browser` (Chrome + session)

### scrape_gc_boxscores.py (Step 2 -- Playwright scraper)

Navigates GC `/box-score` pages, extracts player names + jersey numbers + AB/BB/SO, builds rosters.json (Majors/Minors) and roster.txt (travel teams), writes box_verify.json.

| Function                 | Purpose                                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| **Entry**                |                                                                                                                    |
| `run()`                  | CLI entry point -- parses `--division`, `--team`, `--force`, `--verbose`; runs via `gc_browser.run_with_session()` |
| **Scrapers**             |                                                                                                                    |
| `scrape_division()`      | Org-level scraper (Majors/Minors)                                                                                  |
| `scrape_team_division()` | Team-level scraper (travel divisions); roster.txt lists everyone who appeared in any box score (no Layer 4)        |
| **Player accounting**    |                                                                                                                    |
| `_accum_player()`        | Core per-player accumulator: detects collisions, promotes to 5-char keys                                           |
| `merge_player()`         | Merges new box score data into existing roster entry                                                               |
| `_first_name_from()`     | Extracts first name from GC display string                                                                         |
| `_disambig_key()`        | Builds 5-char disambiguation key (e.g. `B A` -> `Bri A`)                                                           |
| `display_name()`         | Formats `"FirstName L. #jersey"` display string                                                                    |
| `_prepare_for_save()`    | Strips transient fields before writing to disk                                                                     |
| **Normalization**        |                                                                                                                    |
| `normalize_team_name()`  | Applies `TEAM_NAME_ALIASES` to fix GC name differences                                                             |
| `TEAM_NAME_ALIASES`      | Maps GC box score team name variants -> canonical keys                                                             |
| **Helpers & Config**     |                                                                                                                    |
| `setup_logging()`        | Configures logging                                                                                                 |
| `DIVISIONS` dict         | `build_scraper_divisions()` from `season_config` (same source as scrape_gc_playbyplay.py -- always in sync)        |

**Jersey numbers:** Minors box scores once redirected to `/info` (KC-005, now Historical); current
rosters have jerseys except for players GC lists without one.

### gen_hitting.py (Step 3 -- Hitting stat engine + PDF generator)

Reads game `.txt` files, parses every plate appearance, computes batting stats + archetypes, generates multi-page PDF scouting reports via ReportLab.

| Function                     | Purpose                                                                                                   |
| ---------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Entry & Division Runners** |                                                                                                           |
| `main()`                     | CLI entry point -- parses `--division`, `--team`, `--verbose`                                             |
| `run_league()`               | Division runner for Majors/Minors                                                                         |
| `run_wild()`                 | Travel division runner (any travel division): two-pass with LG RANK (needs ≥2 teams)                      |
| `build_league_context()`     | Pre-scans all scorebooks; returns league-wide percentile data                                             |
| `get_wild_opponents()`       | Discovers travel-team folders on disk                                                                     |
| `load_wild_roster()`         | Reads `roster.txt` for a travel opponent                                                                  |
| **PDF Rendering**            |                                                                                                           |
| `generate_pdf()`             | ReportLab PDF assembly: team card + player cards + summary/notes                                          |
| `draw_card()`                | Renders one player or team card: spray chart, stat bars, archetype, 4-stat footer (Sw%, SM%, CStr%, FPT%) |
| `draw_field_spray_chart()`   | Heat-map spray chart with BIP dots                                                                        |
| `draw_stat_box()`            | Renders a single stat label + value box                                                                   |
| `draw_bar()`                 | Renders a horizontal percentage bar                                                                       |
| `draw_header()`              | Draws PDF page header                                                                                     |
| `mark_reviewed()`            | Renames processed game file to `-Reviewed.txt`                                                            |
| **Notes & Archetypes**       |                                                                                                           |
| `generate_notes()`           | Full narrative scouting note for a batter                                                                 |
| `generate_notes_short()`     | Compact note for summary page                                                                             |
| `get_pitching_approach()`    | Archetype -> pitching recommendation lookup                                                               |
| `get_archetype()`            | Applies Approach x Result label using percentiles                                                         |
| `_roster_percentiles()`      | Computes league-wide percentile thresholds                                                                |
| `_rank_stat()`               | Dense rank helper for LG RANK row                                                                         |
| `PITCHING_APPROACH`          | Archetype -> pitching recommendation lookup dict                                                          |
| **Stats**                    |                                                                                                           |
| `compute_team_totals()`      | Aggregates all batters -> single team-level stat dict                                                     |
| `compute_stats()`            | Aggregates PA list -> per-batter stat dict                                                                |
| **Verification**             |                                                                                                           |
| `verify_game()`              | Runs all verification layers on a parsed game                                                             |
| `check_batting_order()`      | Verification layer 3                                                                                      |
| `check_inning_continuity()`  | Verification layer 1                                                                                      |
| `verify_box_score()`         | Verification layer 4: cross-checks vs box_verify.json                                                     |
| **Parsing**                  |                                                                                                           |
| `parse_game_for_team()`      | Core parser: reads .txt file, extracts PAs per batter                                                     |
| `parse_pitch_seq()`          | Parses pitch sequence string into swing/take/foul counts                                                  |
| `parse_outcome()`            | Maps play description -> outcome code                                                                     |
| `parse_ball_type()`          | Classifies BIP as ground ball, fly ball, or line drive                                                    |
| `extract_zone()`             | Extracts fielding zone for spray chart                                                                    |
| `INNING_RE`                  | Regex for `===Top/Bottom N - TeamName===` headers                                                         |
| **Rosters & I/O**            |                                                                                                           |
| `_disambiguate_pas()`        | Splits shared-initials PAs using `_collision_map`                                                         |
| `load_box_verify()`          | Loads box_verify.json                                                                                     |
| `load_box_rosters()`         | Loads rosters.json                                                                                        |
| **Setup & Config**           |                                                                                                           |
| `setup_logging()`            | Configures logging                                                                                        |
| `DIVISIONS` dict             | `build_hitting_divisions()` from `season_config` (folder paths + roster file locations, loaded from YAML) |

### gc_browser.py (Shared -- real Chrome access to GC)

Single place that launches/drives Chrome for both scrapers. See "GameChanger Access" above.

| Function / Constant  | Purpose                                                                                                            |
| -------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `gc_chrome()`        | Context manager: launch Scout Chrome (off-screen unless `on_screen`), attach via CDP, yield Page, close gracefully |
| `check_session()`    | Load `/teams`, record `/me/*` API statuses → `ok` / `signed_out` / `blocked`                                       |
| `classify_session()` | Pure decision logic for `check_session()` (unit-tested)                                                            |
| `run_with_session()` | Open Chrome → check → `work(page)`; returns `EXIT_CODES` value                                                     |
| `login()`            | On-screen sign-in flow used by `--login`                                                                           |
| `EXIT_CODES`         | `{ok: 0, signed_out: 2, blocked: 3}` — `run_menu` keys off these                                                   |
| `ChromeLaunchError`  | Chrome missing, port 9223 busy, or profile already open                                                            |

### parse_gc_text.py (Utility)

Converts raw GC page text into WCWAA-structured `.txt` game file format. Called by `scrape_gc_playbyplay.py` -- never run directly.

| Function         | Purpose                                                        |
| ---------------- | -------------------------------------------------------------- |
| `parse_gc_raw()` | Main entry: raw text string -> formatted game file string      |
| `GC_NAME_FIXES`  | Dict of known GC data errors to auto-correct                   |
| `OUTCOME_TYPES`  | Outcome string -> code mapping (must sync with gen_hitting.py) |

### season_config.py (Central Config Loader)

Gateway module — every script imports from here. Reads `active_season.txt` → loads `config/<season>.yaml` → exposes all season data as module-level constants and helper functions. Also manages the season lifecycle (create, list, switch).

| Function / Constant             | Purpose                                                                                                               |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Path Constants**              |                                                                                                                       |
| `SCOUT_ROOT`                    | Absolute path to the code repo root (derived from `__file__`)                                                         |
| `DATA_ROOT`                     | Data root holding season reports — from the `SCOUT_DATA_ROOT` env var (default: GDrive `.../Scout/data/real`)         |
| `SEASONS_ROOT`                  | `DATA_ROOT/seasons` — parent of all season data dirs                                                                  |
| `LOGS_DIR`                      | Local dated run logs (`SCOUT_ROOT/data/real/logs`)                                                                    |
| `SESSIONS_DIR` / `SESSION_FILE` | Local GC session dir (holds `gc_chrome_profile/`); `SESSION_FILE` = legacy `gc_session.json`                          |
| `SEASON_ID`                     | Active season ID (e.g. `"2026-Fall"`) — read from `active_season.txt` at import                                       |
| `SEASON_DIR`                    | `SEASONS_ROOT/<season_id>/` data directory                                                                            |
| **DIVISIONS Builders**          |                                                                                                                       |
| `build_scraper_divisions()`     | Builds `DIVISIONS` dict for scraping scripts (GC org ID, team slugs, team IDs, `exclude_games` set)                   |
| `build_hitting_divisions()`     | Builds `DIVISIONS` dict for hitting/pitching scripts; empty league team lists fall back to `rosters.json` keys        |
| `list_divisions()`              | Single source of truth for a season's divisions (name, type, active, team count) — used by the web UI                 |
| **Team Management**             |                                                                                                                       |
| `add_team_to_yaml()`            | Adds a team to a travel division in the active season YAML (idempotent)                                               |
| `update_season()`               | Modify Season (web UI): org IDs, display name, travel divisions                                                       |
| **Season Lifecycle**            |                                                                                                                       |
| `list_seasons()`                | Scans `config/*.yaml` (excluding template); returns `[{id, display_name, is_active}]`                                 |
| `set_active_season()`           | Writes a new season ID to `active_season.txt`; guards for missing config                                              |
| `create_season()`               | Scaffolds a new season YAML from `season_template.yaml` (fills GC IDs, display name); calls `_scaffold_season_dirs()` |
| `_scaffold_season_dirs()`       | Private helper — creates on-disk folder tree for a new season (`seasons/<id>/Majors/`, `Minors/`, `Wild/`, `Storm/`)  |

> **Important:** `SEASON_ID` and `SEASON_DIR` are module-level constants resolved at import time.
> Calling `set_active_season()` updates `active_season.txt` on disk, but the **running process still
> uses the old values** until restarted. All season-switch responses include a `restart_required` flag.

### run_menu.py (Orchestrator)

Interactive numbered menu + CLI passthrough. Calls Steps 1->2->3->4 as subprocesses.

| Function                  | Purpose                                                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Entry & Menu**          |                                                                                                               |
| `main()`                  | CLI entry point -- parses `--all`, `--division`, `--team`, `--help`                                           |
| `interactive_menu()`      | Menu: [0] Full, [1] Division, [2] Team, [3] Add a new Tournament Team, [4] Manage seasons                     |
| **Season Management**     |                                                                                                               |
| `manage_seasons()`        | Sub-menu: [1] Switch season, [2] Create season, [B] Back                                                      |
| `_switch_season_wizard()` | Lists all seasons → user picks one → calls `set_active_season()` → prints restart notice                      |
| `_create_season_wizard()` | Interactive wizard: season ID, display name, Majors/Minors GC org IDs → `create_season()` → prints next-steps |
| **Add Team**              |                                                                                                               |
| `add_new_team()`          | Wizard: paste GC URL → `add_team_to_yaml()` + creates `seasons/<season>/<Div>/<Team>/Games/`                  |
| `_slug_to_folder_name()`  | Converts GC slug to folder name                                                                               |
| `_parse_gc_url()`         | Extracts `team_id` and `slug` from a GC schedule URL                                                          |
| **Pipeline**              |                                                                                                               |
| `_run()`                  | Subprocess wrapper with exit-code handling                                                                    |
| `_gc_session_ok()`        | Preflight: runs `--check-session`; on failure prints the fix and (nightly) calls `_notify()`                  |
| `_notify()`               | macOS notification via `osascript`                                                                            |
| `run_pipeline()`          | Runs steps 1->2->3->4 as subprocesses for given scope                                                         |
| `get_team_list()`         | Travel divisions: reads DIVISIONS tuples (sorted alphabetically); league divisions: reads rosters.json keys   |
| **UI Helpers**            |                                                                                                               |
| `print_header()`          | Prints the menu banner; season name is dynamic from `SEASON_ID` (not hardcoded)                               |
| `check_session()`         | Warns at menu start if the Scout Chrome profile (GC login) is missing                                         |

> **Team additions** now write to `config/<season>.yaml` via `season_config.add_team_to_yaml()`
> (the old `_insert_team_into_file()` text-replacement on Python source was removed in v3.0.0).

**Step 4 integration:** `run_pipeline()` runs `python -m scout.pitching.gen_pitching` (`_MOD_PITCHING`) after gen_hitting.

> **Never "test" `run_menu` with arbitrary arguments** — any non-`--help` argument is CLI
> passthrough and starts a real pipeline run.

### server.py (Web UI -- `SERVER_VERSION` 5.0.0)

Local Flask server that backs the HTML front-end. Reuses `get_team_list()`, `_parse_gc_url()`,
`_slug_to_folder_name()` from run_menu.py and `add_team_to_yaml()`, `list_seasons()`, `set_active_season()`,
`create_season()` from season_config (DRY).
Builds run by shelling out to `run_menu.py --division X --team Y` (same proven path as the
terminal menu + nightly cron), streaming live output to the page via Server-Sent Events.

| Endpoint                                  | Purpose                                                                               |
| ----------------------------------------- | ------------------------------------------------------------------------------------- |
| `GET /` + `/css/*` + `/js/*`              | Serve the single-page app                                                             |
| `GET /api/divisions`                      | Active divisions of the season + team lists (fresh call each request — BUG-017 fix)   |
| `GET /api/reports`                        | Scan `seasons/<id>/` for `*-Scout-{Hitting,Pitching}_*.pdf`, grouped by division/team |
| `GET /report/<path>`                      | Stream a PDF (with path-traversal protection — must resolve inside `seasons/`)        |
| `GET /api/logs`, `/api/logs/<name>`       | Dev tab log viewer (list / raw text; path-traversal guarded)                          |
| `GET /api/run?division=&team=`            | Build reports; stream live log via SSE; guarded by a single-run lock                  |
| `POST /api/add_team`                      | Add a team to a travel division from a GC URL                                         |
| `GET /api/seasons`                        | Returns all seasons + active ID (`list_seasons()` fresh each call)                    |
| `POST /api/seasons/active`                | Switches active season; returns `restart_required: true`                              |
| `POST /api/seasons`                       | Creates a new season from wizard data (`create_season()`)                             |
| `GET/POST /api/seasons/<id>`              | Read / modify a season (`update_season()`)                                            |
| `POST /api/seasons/<id>/tournament_teams` | Add/update a season's tournament (travel) divisions                                   |

> **Version header (v3.3.1, BUG-019):** `SERVER_VERSION` + an `@app.after_request` hook
> (`_add_version_header()`) stamp `X-Scout-Version` on every response. The front-end also
> checks `res.ok` on `/api/seasons`; a stale process (missing the endpoint) triggers a
> "Server restart required" banner instead of silently empty season dropdowns. Bump
> `SERVER_VERSION` whenever a new API endpoint is added.

**Config flags (env):** `SCOUT_WEB_HOST` (default `127.0.0.1`), `SCOUT_WEB_PORT` (default `5050`),
`SCOUT_WEB_DEBUG` (`0`/`1`). Set `SCOUT_WEB_HOST=0.0.0.0` to reach the build UI from another
device on the same Wi-Fi. The build subprocess runs with `python -u` + `PYTHONUNBUFFERED=1`
so log lines stream live instead of arriving in one dump.

---

## Function Map -- Pitching Component

### gen_pitching.py (Step 4 -- Pitching stat engine + PDF generator)

Reads game `.txt` files from the opponent's perspective (who was pitching), computes 13 pitching stats, ranks all pitchers in the division by percentile, generates Baseball Savant-style pitcher profile cards with colored slider bars.

**Config source:** `DIVISIONS` is built from `season_config.build_hitting_divisions()` (team IDs, slugs, and folder paths all come from `config/<season>.yaml`). Uses the shared venv. No inter-script imports — it has its own local `parse_outcome()`/`parse_ball_type()`/`parse_pitch_seq()`.

| Function                         | Purpose                                                                                                                                                              |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Setup**                        |                                                                                                                                                                      |
| `setup_logging()`                | Configures file + console logging                                                                                                                                    |
| **Parsing**                      |                                                                                                                                                                      |
| `parse_outcome()`                | Maps play description -> outcome code (mirrors gen_hitting.py)                                                                                                       |
| `parse_ball_type()`              | Classifies BIP as GB, FB, or LD                                                                                                                                      |
| `parse_pitch_seq()`              | Parses pitch sequence -> swing/take/foul/ball/strike counts                                                                                                          |
| `parse_game_for_pitching_team()` | Core parser: reads .txt file, extracts PAs attributed to each pitcher. Uses carry-forward logic for pitcher tracking + pre-scan to skip games not involving the team |
| **Stats**                        |                                                                                                                                                                      |
| `compute_pitcher_stats()`        | Aggregates all PAs for one pitcher -> 13-stat dict (ERA-proxy, WHIP, K/9, BB/9, K%, BB%, K/BB, BABIP, HR/9, FPSH%, GB%, FB+LD%, C%)                                  |
| `compute_percentile_rank()`      | Ranks a value against all values in the division; supports `low_is_good` flip                                                                                        |
| `compute_all_percentiles()`      | Builds percentile rows for every pitcher across all 13 stats                                                                                                         |
| **PDF Rendering**                |                                                                                                                                                                      |
| `pct_to_color()`                 | Maps percentile (0-100) to red->yellow->green color                                                                                                                  |
| `draw_gradient_bar()`            | Draws the colored Savant-style slider bar                                                                                                                            |
| `draw_bubble()`                  | Draws the percentile bubble on the slider                                                                                                                            |
| `draw_axis_labels()`             | Draws "Poor" / "Great" axis labels                                                                                                                                   |
| `draw_stat_row()`                | Renders one stat row: label, value, slider bar, percentile bubble                                                                                                    |
| `draw_pitcher_icon()`            | Draws the Savant pitcher silhouette PNG in card header                                                                                                               |
| `draw_pitcher_card()`            | Renders a complete pitcher card (header + 13 stat rows)                                                                                                              |
| `card_origin()`                  | Computes x,y position for 4-cards-per-page layout                                                                                                                    |
| `generate_pitching_pdf()`        | Assembles full PDF: pages of 4 cards each                                                                                                                            |
| **File I/O**                     |                                                                                                                                                                      |
| `find_game_files()`              | Finds .txt and -Reviewed.txt game files in a directory                                                                                                               |
| `load_rosters_json()`            | Loads rosters.json for Majors/Minors display names                                                                                                                   |
| `load_roster_txt()`              | Loads roster.txt for travel-team display names                                                                                                                       |
| `dedup_pitcher_names()`          | Merges initials-only entries into full-name counterparts (e.g. "K D" -> "Kilean D"); discards unresolvable orphan initials                                           |
| **Division Runners**             |                                                                                                                                                                      |
| `run_league_division()`          | Runs Majors or Minors: two-pass (collect all pitchers -> compute percentiles -> generate per-team PDFs)                                                              |
| `run_travel_division()`          | Runs any travel division: auto-discovers team folders, applies dedup, same two-pass flow                                                                             |
| `main()`                         | CLI entry point -- parses `--division`, `--team`, `--verbose`                                                                                                        |

### Pitching Stats Computed (13 stats, 2 flipped)

| Stat      | Formula                                             | Direction                 |
| --------- | --------------------------------------------------- | ------------------------- |
| ERA-proxy | (ER / IP) x 9 -- ER estimated as (H+BB+HBP-K) x 0.3 | Low is good               |
| WHIP      | (H + BB) / IP                                       | Low is good               |
| K/9       | (K / IP) x 9                                        | High is good              |
| BB/9      | (BB / IP) x 9                                       | **Low is good (flipped)** |
| K%        | K / PA                                              | High is good              |
| BB%       | BB / PA                                             | Low is good               |
| K/BB      | K / BB                                              | High is good              |
| BABIP     | (H - HR) / (AB - K - HR + SF)                       | Low is good               |
| HR/9      | (HR / IP) x 9                                       | Low is good               |
| FPSH%     | First-pitch strikes+hits / PA                       | **Low is good (flipped)** |
| GB%       | Ground balls / BIP                                  | High is good              |
| FB+LD%    | (Fly balls + line drives) / BIP                     | Low is good               |
| C%        | Contact % = (AB - K) / AB                           | Low is good               |

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
- Travel-team folder names MUST exactly match the GC inning header spelling (`GC_NAME_FIXES` handles known GC quirks)
- Majors/Minors team key is `TeamName-CoachLast` (e.g. `Cubs-Holtzer`)
- Pitching component uses `, [NAME] pitching` lines to track pitcher changes

---

## Roster Format

### Majors/Minors -- rosters.json

```json
{
  "Cubs-Holtzer": {
    "S K": { "display": "Sullivan K. #12", "jersey": "12", "ab": 40 },
    "Bri A": { "display": "Brian A. #5", "jersey": "5" },
    "_collision_map": { "B A": ["Bri A", "Ben A"] }
  }
}
```

### Travel teams -- roster.txt

```
# T24 Garnet 11U -- roster.txt
T M, Tyler M. #4
S G, Srijan G. #11
```

> Our own teams (e.g. Mavs, where the user is staff) get full last names from GC
> (`Atley Scott.`); opponents get last initials. Rosters include every player who appeared
> in any box score (guests too) plus a non-player `TEAM` row (KC-003; cleanup BUG-025 Enh).

---

## Duplicate Initials Handling (Brian/Ben Allen Bug)

**Problem:** Two players share initials `B A` on Cubs-Holtzer.
**Fix:** `scrape_gc_boxscores.py` promotes both to 5-char keys (`Bri A`, `Ben A`) and writes `_collision_map`. `gen_hitting.py._disambiguate_pas()` alternates PA assignments by batting order.

---

## Verification System (4 Layers)

| Layer | Check                                                     | Severity                         |
| ----- | --------------------------------------------------------- | -------------------------------- |
| 1     | Inning continuity -- no skipped innings                   | Log only                         |
| 2     | Unknown outcomes -- unrecognised play descriptions        | WARNING (stdout)                 |
| 3     | Batting order -- PA counts consistent with lineup         | Log only                         |
| 4     | Box score cross-check -- parsed AB/BB vs. box_verify.json | Log only (league divisions only) |

None stop PDF generation. Travel divisions have no box_verify.json, so Layer 4 doesn't run for them.

---

## Archetype System (Hitting Reports)

Each player card shows a 2-word label: **Approach x Result**.

**Approach** (plate discipline): Aggressive, Passive, or Disciplined
**Result** (league-relative): Walker, Overmatched, Power, or Contact

Cards with 5-9 PA show `*` suffix. Fewer than 5 PA: `--`.

**Pitching approach matrix:**

| Archetype                      | Recommendation    |
| ------------------------------ | ----------------- |
| Aggressive Power/Contact       | Edges + Mix Speed |
| Aggressive Overmatched         | Climb the Ladder  |
| Aggressive Walker              | Outside - In      |
| Disciplined Power/Contact      | Keep Mixing       |
| Disciplined Overmatched/Walker | Attack the Zone   |
| Passive Power/Contact          | Attack & Expand   |
| Passive Overmatched/Walker     | Attack the Zone   |

---

## Adding a New Tournament Team (travel divisions)

Teams live in `config/<season>.yaml` — **never** edited into Python source. Three ways:

1. **Web UI (easiest):** Start Scout.command -> "Add Team" tab -> paste the GC schedule URL.
2. **Terminal menu:** `bash launchers/run_scout.sh` -> option [3] "Add a new Tournament Team".
3. **Manual:** add a `{name, gc_id, gc_slug}` entry under `divisions.<Div>.teams` in the YAML,
   then create `seasons/<season>/<Div>/<Exact Team Name>/Games/`.

All three call `season_config.add_team_to_yaml()` (idempotent — guards duplicates) and create the
`Games/` folder. The folder name MUST match the GC inning-header spelling exactly; verify it after
the first game is scraped. New travel _divisions_ (like Mavs) are added via the web UI's Modify
Season → Tournament Divisions.

### Excluding games (scrimmages / test games)

List GC game UUIDs (from the `/schedule/<uuid>/plays` URL) under a team or a division:

```yaml
- name: Weddington Mavericks 10U
  gc_id: P6jwWo3uwTln
  gc_slug: 2026-fall-weddington-mavericks-10u
  exclude_games:
    - 1f0e0307-13db-4031-8533-57cddeb36db1
```

Both scrapers skip listed games. Files already on disk must be moved out of `Games/`
(convention: `_archive/<season>_excluded_games/<Div>/` on the data root), then rebuild the
roster with `scrape_gc_boxscores --division <Div> --force` and re-run Steps 3–4.

> The web UI / wizard rewrite the YAML with PyYAML, so **comments in the YAML are dropped**.
> Keep notes in AGENTS.md, not YAML comments.

## Starting a New Season

Use the season management wizard — no more manual file copying:

1. **Web UI:** Seasons tab -> "Create New Season" form.
2. **Terminal:** `bash launchers/run_scout.sh` -> option [4] "Manage seasons" -> [2] "Create".

Both call `season_config.create_season()`, which:

- Copies `config/season_template.yaml` to `config/<season-id>.yaml`
- Fills in the GC org IDs you provide (Majors + Minors change each season)
- Creates `seasons/<season-id>/Majors/`, `Minors/`, `Wild/`, `Storm/` folder tree
- Optionally sets the new season as active immediately

Travel team lists start empty — add teams via "Add Team" as games are scheduled.
After switching seasons, **restart the terminal session or web server** so `SEASON_ID` reloads.

---

## Teams Reference (Fall 2026 — active)

> Source of truth: `config/2026-Fall.yaml`. Rebuilt from scratch 2026-10-26 (old Fall data in
> `_archive/2026-Fall_backup_2026-10-26`).

| Division | Type       | Teams                                                                                            |
| -------- | ---------- | ------------------------------------------------------------------------------------------------ |
| Majors   | League     | GC org `tJkIoODIMpip`; teams discovered from box scores (`rosters.json`)                         |
| Minors   | League     | GC org `aGeTxcjpQ6Y2`; teams discovered from box scores (`rosters.json`)                         |
| Wild     | Travel     | Weddington Wild 12U                                                                              |
| Mavs     | Tournament | Weddington Mavericks 10U (Aug 22 scrimmages excluded), Carolina Locos White 10U, QC Crushers 10U |
| Storm    | Travel     | inactive this season                                                                             |

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
cd ~/Documents/VSCode/Personal/Scout
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
# Google Chrome must be installed in /Applications (Playwright's Chromium is not used)
python -m scout.scraping.scrape_gc_playbyplay --login           # sign in to GC in the Scout Chrome window
```

---

## Stat Formulas Reference (Hitting)

| Stat   | Formula                                                   |
| ------ | --------------------------------------------------------- |
| PA     | All plate appearances (BB + HBP + AB + SF + SB)           |
| AB     | PA - (BB + HBP + SF + SB)                                 |
| AVG    | H / AB                                                    |
| OBP    | (H + BB + HBP) / (AB + BB + HBP)                          |
| SLG    | TB / AB                                                   |
| C%     | (AB - K_total) / AB                                       |
| GB%    | Ground ball BIP / total BIP                               |
| FB+LD% | (Fly ball + line drive BIP) / total BIP                   |
| Swing% | Total swings (miss + foul + in-play) / total pitches seen |
| SM%    | Swing-and-miss / total swings                             |
| CStr%  | Called strikes / total pitches seen                       |
| FPT%   | First-pitch takes / (takes + swings on first pitch)       |

---

## Troubleshooting

| Symptom                                                                    | Likely Cause                                       | Fix                                                                                                                                                                            |
| -------------------------------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `0 PAs` for a team                                                         | Team name mismatch (folder vs. inning header)      | Punctuation/spacing/case-only differences are auto-fixed: `reconcile_team_folders()` renames the folder + YAML name and logs `✔ Renamed folder`. Other spellings: fix manually |
| `?F L?` in output                                                          | Player initials not in rosters.json                | Run scrape_gc_boxscores.py; or add to roster_additions                                                                                                                         |
| `WARNING UNKNOWN`                                                          | Play outcome not in OUTCOME_TYPES                  | Add to parser                                                                                                                                                                  |
| Jersey numbers missing (Minors)                                            | Box scores inaccessible                            | Known permanent limitation                                                                                                                                                     |
| "GameChanger session expired" / exit 2                                     | Scout profile signed out                           | `python -m scout.scraping.scrape_gc_playbyplay --login`                                                                                                                        |
| "GameChanger refused the Scout browser" / exit 3, or `0 FINAL games found` | GC blocking the browser, or Chrome failed to start | Run `--check-session -v`; see BUG-022. Never switch back to headless                                                                                                           |
| "Port 9223 is already in use"                                              | Another Scout run or Scout Chrome still open       | Close it / wait for the other run                                                                                                                                              |
| "Chrome exited immediately"                                                | Scout profile open in another Chrome window        | Quit that window and retry                                                                                                                                                     |
| High pitcher count (travel)                                                | Initials-only names not deduped                    | Check dedup_pitcher_names() logic                                                                                                                                              |
| Player with accented name missing                                          | Regex uses ASCII-only char class                   | Verify `[a-z\u00C0-\u024F]` in regex (BUG-016 fix)                                                                                                                             |
| No LG RANK row on a travel team                                            | Only one team in that division                     | Add more teams; then `gen_hitting --division X` refreshes all                                                                                                                  |
| LG RANK / pitching percentiles look stale                                  | Other teams' PDFs built before new team was added  | `gen_hitting --division X` + `gen_pitching --division X`                                                                                                                       |
| Scrimmage counted in a team's stats                                        | Game not excluded                                  | Add its UUID to `exclude_games` (see "Excluding games")                                                                                                                        |
