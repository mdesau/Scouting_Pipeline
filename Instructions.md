# WCWAA 2026 Spring — Scouting Report Pipeline

This file is the authoritative reference for the WCWAA scouting report pipeline.
Load it at the start of every new AI coding session (GitHub Copilot, Claude, etc.).
It covers every design decision, known bug, and operational detail accumulated
across the full build history of this project.

**Root directory (all paths relative to this):**
`~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My Drive/Baseball/WCWAA/2026/Spring/`

**Best practices prompt:** When starting a new session, the user may paste their "Code Mentor" prompt which defines conventions for debugging, git hygiene, error handling, and code style. Follow those guidelines throughout.

---

## Development Environment

- **Python 3.9.6** (macOS system Python)
- **Virtual environment:** `Scout_Development/venv/` — always activate before running scripts
- **Key packages:** Playwright 1.58.0, Chromium 145, ReportLab 4.4.10
- **Frozen deps:** `requirements.txt` in project root
- **Git:** Local repo on `main`, tagged `v0.1.0`, `v0.2.0`, `v1.0.0`, `v2.0.0`, `v2.1.0`, `v2.2.0`, `v2.3.0`, `v2.4.0` (current)
- **GitHub remote:** `https://github.com/mdesau/Scouting_Pipeline` (private)
  - PAT stored in `.git/config` remote URL — rotate at github.com/settings/tokens if needed

```
(tag: v2.4.0) feat: LG RANK for Wild/Storm + No PAs diagnostic warning v2.4.0
(tag: v2.3.0) feat: league rank row + team totals in summary table v2.3.0
(tag: v2.2.0) feat: team aggregate card + team totals row in summary table v2.2.0
e9f338e  (tag: v2.0.0) chore: __version__ = 2.0.0, version banner, CHANGELOG v1.0.0+v2.0.0
0d7e2e7  fix: gen_reports --team filter uses partial match for Wild/Storm
fd26a40  fix: Wild/Storm PDF jersey numbers missing — load_wild_roster dual key format (Bug 11)
c7a0109  fix: scrape_box_scores --team filter; Step 2 respects single-team selection (Bug 10)
cc76d6e  docs: log Bugs 7-9 in Bugs_List.txt, Instructions.md, CHANGELOG
00d8d40  fix: SCHEDULE_JS team-page date/filename + date import (Bugs 8-9)
ea04909  fix: SCHEDULE_JS final detection for Wild/Storm team pages (Bug 7)
f858c3d  feat: add run_menu.py — numbered pipeline menu
c2828e4  feat: rename run_weekly.sh → run_scout.sh; add SBA Alabama + TN Nationals
0e4c05e  (tag: v1.0.0) docs: log Bug 6 — SS spray chart zone mapped to 3B
```

### Scripts Overview (line counts as of Apr 23, 2026)
| Script | Lines | Role | Has --verbose | Has DEBUG_CONFIG | Has try/except |
|---|---|---|---|---|---|
| `scrape_gc_playbyplay.py` | 594 | Playwright: GC schedule → .txt game files | ✅ | ✅ | ✅ |
| `scrape_gc_boxscores.py` | 839 | Playwright: GC box scores → rosters.json | ✅ | ✅ | — |
| `gen_reports.py` | 2055 | Stat engine + PDF generator | ✅ | ✅ | ✅ (run_wild) |
| `parse_gc_text.py` | 270 | Raw GC text → WCWAA format (utility) | — | — | — |
| `run_scout.sh` | 55 | Shell launcher — activates venv, calls run_menu.py | — | — | — |
| `run_scout_nightly.sh` | 93 | Headless launcher — no menu; calls run_menu.py --all; used by launchd | — | — | — |
| `run_menu.py` | 656 | Interactive pipeline menu — numbered team/division picker, add-new-team flow | — | — | — |

---

## Project Summary

Automated scouting report pipeline for Weddington youth baseball leagues (Spring 2026).
Pulls play-by-play data from GameChanger (GC), computes batting stats + archetypes,
and generates multi-page PDF scouting reports for four divisions:

| Division | Age | Teams | Scope |
|---|---|---|---|
| Majors | 11U in-house | 11 teams | Full league — reports on all opponents |
| Minors | 9U in-house | 14 teams | Full league |
| Wild | 11U travel | 8 opponent teams | Reports on travel opponents only |
| Storm | 9U travel | 9 opponent teams | Reports on travel opponents only |

---

## Directory Structure

```
Spring/
  Scout_Development/          ← git repo root (https://github.com/mdesau/Scouting_Pipeline)
    Instructions.md            ← this file (authoritative project context)
    README.md                  ← setup guide + scripts reference for new users
    CHANGELOG.md               ← version history
    requirements.txt
    .gitignore
    examples/
      example_game_file.txt    ← sample parsed play-by-play (one-time reference)
      example_scouting_report.pdf
    Scripts/
      scrape_gc_playbyplay.py            ← Playwright: GC schedule pages → .txt game files
      scrape_gc_boxscores.py     ← Playwright: GC box scores → rosters.json + roster.txt
      parse_gc_text.py         ← converts raw GC page text → WCWAA .txt format
      gen_reports.py           ← stat engine + ReportLab PDF generator (all 4 divisions)
      run_scout.sh             ← manual launcher: activates venv, calls run_menu.py (interactive)
      run_scout_nightly.sh     ← headless launcher: no menu; calls run_menu.py --all (for launchd)
      run_menu.py              ← pipeline orchestrator: interactive menu + CLI passthrough
      gc_session.json          ← saved Playwright GC login session (auth cookies) [gitignored]
      archetype_reference.txt  ← archetype system design notes
    launchd/
      com.wcwaa.scout_pipeline.plist  ← macOS LaunchAgent: fires run_scout_nightly.sh at 10pm EDT
    Logs/                      ← runtime logs [gitignored]
      gen_reports_YYYYMMDD_HHMMSS.log
      scrape_gc_playbyplay_YYYYMMDD_HHMMSS.log
      scrape_gc_boxscores_YYYYMMDD_HHMMSS.log

  Majors/
    Reports/
      Scorebooks/              ← .txt and -Reviewed.txt play-by-play game files
      Scouting_Reports/        ← output PDFs
      rosters.json             ← player names + jersey #s (built by scrape_gc_boxscores.py)
      box_verify.json          ← per-game AB/BB/SO cross-check data

  Minors/
    Reports/
      Scorebooks/
      Scouting_Reports/
      rosters.json             ← names only (jersey #s unavailable — see Known Limitations)
      box_verify.json

  Wild/
    [TeamName]/                ← folder name MUST exactly match GC inning header
      Games/                   ← .txt and -Reviewed.txt game files
      roster.txt               ← optional: "INITIALS, Display Name #jersey"
      [TeamName]_Scout_2026.pdf

  Storm/
    [TeamName]/
      Games/
      roster.txt
      [TeamName]_Scout_2026.pdf
```

---

## Weekly Workflow

**Option A — manual on-demand run (interactive menu):**
```bash
cd ~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My\ Drive/Baseball/WCWAA/2026/Spring/Scout_Development/Scripts
bash run_scout.sh
```

**Option B — nightly scheduled run (automatic via launchd at 10pm EDT):**
```bash
# Verify scheduler is active
launchctl list | grep wcwaa
# Trigger immediately for testing
launchctl start com.wcwaa.scout_pipeline
# Logs at: Scout_Development/Logs/nightly_YYYYMMDD_HHMMSS.log
```
See `launchd/com.wcwaa.scout_pipeline.plist` for install instructions.

**Step by step:**
```bash
python3 scrape_gc_playbyplay.py                     # Step 1: pull all new FINAL game files from GC
python3 scrape_gc_boxscores.py              # Step 2: update rosters.json + jersey numbers
python3 gen_reports.py --division Majors  # Step 3: regenerate PDFs per division
python3 gen_reports.py --division Minors
python3 gen_reports.py --division Wild
python3 gen_reports.py --division Storm
```

Step 1 skips games already on disk (safe to re-run). Step 2 is incremental by default.
Use `--force` to re-scrape all games: `python3 scrape_gc_playbyplay.py --force`

---

## Common Commands

```bash
# Single team
python3 gen_reports.py --division Majors --team Cubs
python3 gen_reports.py --division Minors --team Rangers
python3 gen_reports.py --division Wild --team "T24 Garnet 11U"

# Single division scrape
python3 scrape_gc_playbyplay.py --division Storm
python3 scrape_gc_playbyplay.py --team "MARA 9U Stingers"

# Preview without writing (scraper dry-run)
python3 scrape_gc_playbyplay.py --check

# First-time login OR session expired
python3 scrape_gc_playbyplay.py --login
```

---

## Prerequisites (First-Time Setup on Mac)

Already done — venv exists at `Scout_Development/venv/` with Playwright + ReportLab installed.

**To recreate from scratch:**
```bash
cd .../Scout_Development
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

**To activate for manual script runs:**
```bash
source .../Scout_Development/venv/bin/activate
```
(`run_scout.sh` activates the venv automatically.)

Then run login once to save session:
```bash
cd .../Scout_Development/Scripts
python3 scrape_gc_playbyplay.py --login
```

---

## How the Pipeline Works

### Step 1 — scrape_gc_playbyplay.py (Playwright scraper)
**What it does:** Navigates GC schedule pages for all 4 divisions, finds new FINAL games, downloads play-by-play text, converts via `parse_gc_text.py`, saves `.txt` game files.

**Key functions & locations:**
| Function | ~Line | Purpose |
|---|---|---|
| `run()` | ~511 | CLI entry point — parses `--division`, `--team`, `--login`, `--check`, `--force`, `--verbose`; loops divisions |
| `scrape_org_division()` | ~361 | Org-level scraper (Majors/Minors): loads org schedule, finds FINAL games, scrapes each |
| `scrape_team_division()` | ~431 | Team-level scraper (Wild/Storm): loads per-team schedule page, finds FINAL games |
| `extract_plays_raw()` | ~336 | Navigates to `/plays` URL, extracts raw page text via Playwright |
| `is_covered()` | ~355 | Checks whether a game file already exists on disk (skip logic) |
| `get_schedule()` | ~321 | Runs `SCHEDULE_JS` in browser, returns parsed schedule array |
| `setup_logging()` | ~87 | Configures file + console logging with `--verbose` support |
| `fmt_date()` | ~307 | Normalizes GC date strings to `MonDD` format for filenames |
| `safe()` | ~316 | Sanitizes team name for use in filenames |
| `SCHEDULE_JS` | ~130 | JS string injected into browser to extract game cards from GC's React DOM |
| `DIVISIONS` dict | ~85 | All team IDs, slugs, folder paths — **edit here to add/remove teams** |
| `DEBUG_SCHEDULE_RAW`, `DEBUG_PAGE_TEXT` | ~70 | Debug flags for raw JS dumps |

**Dependencies:** `parse_gc_text.parse_gc_raw()`, `gc_session.json`

---

### Step 2 — scrape_gc_boxscores.py (Playwright scraper)
**What it does:** Navigates GC `/box-score` pages, extracts player names + jersey numbers + AB/BB/SO stats, builds/updates `rosters.json` (Majors/Minors) and `roster.txt` (Wild/Storm), writes `box_verify.json`.

**Key functions & locations:**
| Function | ~Line | Purpose |
|---|---|---|
| `run()` | ~798 | CLI entry point — parses `--division`, `--team`, `--force`, `--verbose`; loops divisions |
| `scrape_division()` | ~515 | Org-level scraper (Majors/Minors): loads schedule, iterates FINAL games, accumulates rosters |
| `scrape_team_division()` | ~649 | Team-level scraper (Wild/Storm): per-team schedule page, box score extraction |
| `_accum_player()` | ~385 | Core per-player accumulator: detects collisions, promotes to 5-char keys, writes `_collision_map` |
| `_prepare_for_save()` | ~491 | Strips transient fields before writing rosters.json/roster.txt to disk |
| `merge_player()` | ~324 | Merges new box score data into existing roster entry; handles `setdefault` migration guard |
| `_first_name_from()` | ~355 | Extracts first name from GC display string or existing roster entry |
| `_disambig_key()` | ~376 | Builds 5-char disambiguation key from initials + first name (e.g. `B A` → `Bri A`) |
| `display_name()` | ~305 | Formats `"FirstName L. #jersey"` display string from GC name + jersey |
| `normalize_team_name()` | ~288 | Applies `TEAM_NAME_ALIASES` to fix GC rendering differences (e.g. `As-Blanco` vs `A's-Blanco`) |
| `setup_logging()` | ~125 | Configures file + console logging with `--verbose` support |
| `fmt_date()` | ~257 | Normalizes GC date strings to `MonDD` format |
| `DIVISIONS` dict | ~100 | All team IDs, slugs, output paths — **must match scrape_gc_playbyplay.py exactly** |
| `TEAM_NAME_ALIASES` | ~60 | Maps GC box score team name variants → canonical roster keys |
| `DEBUG_BOX_SCORE_RAW`, `DEBUG_TEAM_NAMES` | ~55 | Debug flags |

**Dependencies:** `gc_session.json`. Outputs consumed by `gen_reports.py`.

**Known limitation:** Minors `/box-score` pages redirect to `/info` — jersey numbers permanently unavailable for Minors. Scraper detects this and skips gracefully.

---

### Step 3 — gen_reports.py (stat engine + PDF generator)
**What it does:** Reads game `.txt` files, parses every plate appearance, computes batting stats + archetypes, generates multi-page PDF scouting reports via ReportLab.

**Key functions & locations:**
| Function | ~Line | Purpose |
|---|---|---|
| `main()` | ~2031 | CLI entry point — parses `--division`, `--team`, `--verbose` |
| `run_league()` | ~1729 | Division runner for Majors/Minors: pre-scan for percentiles, generate each PDF |
| `run_wild()` | ~1863 | Travel division runner (Wild/Storm): two-pass — Pass 1 parses all opponents + builds `div_team_totals`; Pass 2 generates PDFs with LG RANK context |
| `build_league_context()` | ~1675 | Pre-scans all Majors/Minors scorebooks; returns `(league_batters, league_team_totals)` tuple for percentiles + LG RANK |
| `get_wild_opponents()` | ~1625 | Discovers Wild/Storm opponent folders on disk |
| `load_wild_roster()` | ~1639 | Reads `roster.txt` for a travel opponent |
| `generate_pdf()` | ~1408 | ReportLab PDF assembly: team card + player cards + summary/notes page |
| `draw_card()` | ~1299 | Renders one player or team card: spray chart, stat bars, archetype label, pitching approach |
| `draw_field_spray_chart()` | ~1171 | Heat-map spray chart with BIP dots |
| `draw_stat_box()` | ~1272 | Renders a single stat label + value box |
| `draw_bar()` | ~1279 | Renders a horizontal percentage bar |
| `draw_header()` | ~1100 | Draws PDF page header with title + subtitle |
| `mark_reviewed()` | ~1071 | Renames processed game file to `-Reviewed.txt` |
| `generate_notes()` | ~997 | Full narrative scouting note for a batter |
| `generate_notes_short()` | ~1042 | 1-2 sentence compact note for summary page |
| `get_pitching_approach()` | ~989 | Archetype → pitching recommendation lookup |
| `get_archetype()` | ~865 | Applies Approach × Result label using league percentiles or fixed thresholds |
| `_roster_percentiles()` | ~848 | Computes league-wide percentile thresholds for archetype classification |
| `_rank_stat()` | ~807 | Dense rank helper — rank 1 = highest; returns `"rank/n"` or `"—"`; used in LG RANK row |
| `fmt_pct()` | ~803 | Formats a ratio as `".NNN"` string or `"—"` |
| `fmt_avg()` | ~798 | Formats batting average as `".NNN"` |
| `compute_team_totals()` | ~728 | Aggregates all batters → single team-level stat dict; powers team card + totals row |
| `compute_stats()` | ~614 | Aggregates PA list → per-batter stat dict (AVG, OBP, SLG, SM%, etc.) + raw pitch counts |
| `verify_game()` | ~582 | Runs all verification layers on a parsed game |
| `check_batting_order()` | ~523 | Verification layer 3: checks PA counts consistent with lineup |
| `check_inning_continuity()` | ~493 | Verification layer 1: detects skipped innings |
| `parse_game_for_team()` | ~430 | Core parser: reads `.txt` file, applies `INNING_RE` + `DESC_RE`, extracts PAs per batter |
| `parse_pitch_seq()` | ~389 | Parses pitch sequence string into swing/take/foul counts |
| `parse_outcome()` | ~340 | Maps play description string → outcome code (1B, 2B, K, BB, FO, GO, etc.) |
| `parse_ball_type()` | ~327 | Classifies BIP as ground ball, fly ball, or line drive |
| `extract_zone()` | ~322 | Extracts fielding zone from play description for spray chart |
| `verify_box_score()` | ~262 | Verification layer 4: cross-checks parsed AB/BB vs. box_verify.json |
| `_disambiguate_pas()` | ~213 | Splits shared-initials PAs using `_collision_map` + batting order alternation |
| `load_box_verify()` | ~202 | Loads box_verify.json cross-check data |
| `load_box_rosters()` | ~159 | Loads rosters.json for Majors/Minors |
| `build_rosters()` | ~133 | Builds roster dict from CSV (legacy path) |
| `setup_logging()` | ~43 | Configures file + console logging with `--verbose` support |
| `INNING_RE` | ~420 | Regex matching `===Top/Bottom N - TeamName===` headers — **critical: exact team name match** |
| `BIP_OUTCOMES` | ~312 | Set of all ball-in-play outcome codes — **add new play types to `parse_outcome()` too** |
| `DIVISIONS` dict | ~80 | Folder paths + roster file locations per division |
| `PITCHING_APPROACH` | ~952 | Archetype → pitching recommendation lookup dict |
| `DEBUG_PA_PARSING`, `DEBUG_ARCHETYPES`, `DEBUG_PITCH_SEQ` | ~38 | Debug flags |

**Dependencies:** `rosters.json` or `roster.txt` (from step 2), `.txt` game files (from step 1).

---

### Utility — parse_gc_text.py
**What it does:** Converts raw GC page text (scraped via Playwright) into the WCWAA-structured `.txt` game file format. Called internally by `scrape_gc_playbyplay.py` — never run directly.

**Key functions & locations:**
| Function | ~Line | Purpose |
|---|---|---|
| `parse_gc_raw()` | ~80 | Main entry: takes raw page text string, returns formatted WCWAA game file string |
| `GC_NAME_FIXES` | ~20 | Dict of known GC data errors to auto-correct (e.g. `"$awyer"` → `"Sawyer"`) |
| `OUTCOME_TYPES` | ~35 | Outcome string → code mapping (must stay in sync with `gen_reports.py`) |

**Dependencies:** None (pure utility, no imports beyond stdlib).

---

### Orchestrator — run_menu.py
**What it does:** Python-based pipeline orchestrator. Provides an interactive numbered menu for choosing division/team/full-pipeline runs, handles CLI passthrough (`--all`, `--division`, `--team`), and calls steps 1→2→3 as subprocesses. Also contains the "Add New Team" wizard for Wild/Storm opponents.

**Key functions & locations:**
| Function | ~Line | Purpose |
|---|---|---|
| `main()` | ~597 | CLI entry point — parses `--all`, `--division`, `--team`; routes to `run_pipeline()` or `interactive_menu()` |
| `interactive_menu()` | ~525 | Numbered menu: [0] Full pipeline, [1] Single division, [2] Single team, [3] Add new team |
| `run_pipeline()` | ~207 | Runs steps 1→2→3 as subprocesses for a given division/team scope |
| `_run()` | ~276 | Subprocess wrapper with exit-code handling; `fatal` param controls abort-on-error |
| `add_new_team()` | ~429 | Interactive wizard: paste GC URL → creates folder + inserts team into both scrapers |
| `_parse_gc_url()` | ~303 | Extracts `team_id` and `slug` from a GC schedule URL |
| `_slug_to_folder_name()` | ~327 | Converts GC slug to folder name (e.g. `2026-spring-t24-garnet-11u` → `T24 Garnet 11U`) |
| `_insert_team_into_file()` | ~366 | Programmatically inserts a new team tuple into a scraper's `DIVISIONS` dict |
| `get_team_list()` | ~174 | Reads `DIVISIONS` from `scrape_gc_playbyplay.py` to build team picker list |
| `check_session()` | ~103 | Validates `gc_session.json` exists and is not expired |
| `print_header()` | ~93 | Prints the pipeline banner |
| `ask()` | ~122 | Prompt helper with default value support |
| `pick_from_list()` | ~142 | Numbered list picker UI |

**Dependencies:** Imports `DIVISIONS` from `scrape_gc_playbyplay.py`. Called by `run_scout.sh` (interactive) and `run_scout_nightly.sh` (headless via `--all`).

---

## Game File Format

After `parse_gc_text.py` runs, game files look like this:

```
GAME: Mon Mar 15 | https://web.gc.com/teams/I2XcyUwmye3p/2026-spring-t24-garnet-11u/schedule/UUID/plays

===Top 1st - T24 Garnet 11U===
Single | | Strike 1 looking, In play.
B A singles to left fielder.
Walk | | Ball 1, Ball 2, Ball 3, Ball 4.
S K walks, J R pitching.
===Bottom 1st - Dilworth 11U - Navy===
...
```

**Critical rules:**
- `INNING_RE` does exact string matching on the team name in `===` headers
- The folder name for Wild/Storm teams MUST exactly match the team name as GC writes it in those headers
- For Majors/Minors, the team key is `TeamName-CoachLast` (e.g. `Cubs-Holtzer`) — must match the `.txt` filename
- Files may be reverse-chronological (GC default) — parser handles this via inning number sort

---

## Roster Format

### Majors / Minors — rosters.json
```json
{
  "Cubs-Holtzer": {
    "S K":  { "display": "Sullivan K. #12", "jersey": "12", "ab": 40, "bb": 5, "so": 3, "games_seen": 5, "games": [...] },
    "Bri A": { "display": "Brian A. #5",    "jersey": "5",  "ab": 20, "bb": 2, "so": 4, "games_seen": 5, "games": [...] },
    "Ben A": { "display": "Ben A. #8",      "jersey": "8",  "ab": 18, "bb": 1, "so": 3, "games_seen": 5, "games": [...] },
    "_collision_map": { "B A": ["Bri A", "Ben A"] }
  }
}
```

The `_collision_map` is written by `scrape_gc_boxscores.py` when two players on the
same team share 2-char initials. `gen_reports.py` reads it to split plate
appearances between the two players based on batting-order occurrence order
(first occurrence in each game → earlier batter, second → later batter, alternating).

Display string convention: `"FirstName L. #jersey"` e.g. `"Tyler A. #1"`.
If jersey is unavailable: `"Tyler A."` (no `#` suffix).

### Wild / Storm — roster.txt
```
# T24 Garnet 11U — roster.txt
# Format: INITIALS, Display Name #jersey
T M, Tyler M. #4
S G, Srijan G. #11
```

---

## Duplicate Initials Handling (Brian/Ben Allen Bug)

**Problem:** Two players on the same team share initials (e.g., "Brian Allen" and
"Ben Allen" both produce initials `B A`). The play-by-play only contains initials,
so the parser cannot distinguish them without extra context.

**Fix (implemented Apr 2026):**
1. `scrape_gc_boxscores.py` — during box score accumulation, detects when a new player's
   first name differs from the existing player at the same initials. Both are moved to
   5-char disambiguation keys (`Bri A`, `Ben A`) and a `_collision_map` is written.
2. `gen_reports.py` — `_disambiguate_pas()` reads the collision map, sorts PAs
   chronologically by inning, and alternates assignments: odd occurrences → earlier
   batter (first key in collision map), even → later batter.

**Key assumption:** The earlier-batting player in the `_collision_map` list always
bats before the other in every game. This holds for Brian/Ben Allen (Brian bats ahead
of Ben in every game). If this assumption ever breaks, the box-verify layer will
surface the discrepancy.

**Affected team:** Cubs-Holtzer (Brian Allen + Ben Allen, both `B A`).
Until `scrape_gc_boxscores.py` is run locally with the new code, the `rosters.json`
has been manually patched with the disambiguation and `_collision_map`.

---

## Verification System (4 Layers, runs on every gen_reports.py call)

| Layer | Check | Logged as |
|---|---|---|
| 1 | Inning continuity — no skipped innings per team per game | `DEBUG INNING GAP` (log only) |
| 2 | Unknown outcomes — unrecognised play descriptions | `WARNING UNKNOWN` |
| 3 | Batting order — PA counts consistent with lineup (debug only) | `DEBUG ORDER/GAP` |
| 4 | Box score cross-check — parsed AB/BB vs. box_verify.json | `DEBUG BOX-VERIFY` (log only) |

Layer 2 (`WARNING UNKNOWN`) appears on stdout. Layers 1, 3, 4 are debug-only (log file only). None stop PDF generation.

---

## Archetype System

Each player card shows a 2-word label: **Approach × Result**.

**Approach** (based on plate discipline):
- `Aggressive` — FPT% < 40% or SM% >> CStr%
- `Passive` — FPT% > 70% and OBP-AVG gap < .060
- `Disciplined` — OBP-AVG gap ≥ .060 (takes pitches selectively)

**Result** (league-relative percentiles for Majors/Minors; fixed thresholds for Wild/Storm):
- `Walker` — top-33% BB/PA + BB/(H+BB) > 33% + OBP-AVG ≥ .100
- `Overmatched` — bottom-33% C% or SM% > 50%
- `Power` — top-33% SLG + ISO ≥ .120
- `Contact` — default

Cards with 5–9 PA show `*` suffix. Fewer than 5 PA: `—`.

**Pitching approach matrix** (one recommendation per archetype, on each card):
```
Aggressive Power/Contact     → Edges + Mix Speed
Aggressive Overmatched       → Climb the Ladder
Aggressive Walker            → Outside - In
Disciplined Power/Contact    → Keep Mixing
Disciplined Overmatched/Walker → Attack the Zone
Passive Power/Contact        → Attack & Expand
Passive Overmatched/Walker   → Attack the Zone
```

---

## Adding a New Wild or Storm Opponent

1. Get the team's GC schedule URL: `https://web.gc.com/teams/{team_id}/{slug}/schedule`
2. In `Scripts/scrape_gc_playbyplay.py`, find the `"Wild"` or `"Storm"` section in `DIVISIONS` (~line 115)
3. Add one tuple to the `"teams"` list:
   ```python
   ("team_id_from_url", "slug-from-url", "Exact Team Name"),
   ```
4. Make the identical addition in `Scripts/scrape_gc_boxscores.py` (same section)
5. Create the folder structure: `Wild/[Exact Team Name]/Games/`
6. The folder name MUST exactly match GC's inning header spelling — check a parsed game file

---

## Teams Reference (Spring 2026)

### Majors (11 teams)
| Team-Coach key | Notes |
|---|---|
| Guardians-Esau | |
| Royals-Hall | |
| Diamondbacks-Vandiford | stored as "Dbacks" in CSV/rosters — handled by csv_overrides |
| Marlins-McLendon | |
| Dodgers-Pearson | |
| As-Blanco | A's stored as "As" — handled by csv_overrides |
| Braves-Rue | |
| Twins-Ewart | |
| Padres-Schick | Jersey #s fully populated |
| Cubs-Holtzer | Has B A collision map (Brian + Ben Allen); N P (Nathan P. #10) + C C (Chase C. #3) resolved |
| Rays-Madero | Only 2/13 players have jersey #s scraped — data gap, not a code bug |

### Minors (14 teams)
| Team-Coach key | Notes |
|---|---|
| Astros-Barbour | |
| Dodgers-Winchester | |
| Padres-Midkiff | |
| Reds-Naturale | |
| Rangers-Leonard | |
| Yankees-DePasquale | |
| Marlins-Eberlin | |
| Guardians-Plunkett | |
| Angels-Casper | |
| Braves-Brooks | |
| Cubs-Verlinde | |
| Brewers-Linnenkohl | |
| Rays-Pearson | |
| Mets-Hornung | Manual roster_additions entry: "B A" → "B. Amerine" (Beau Amerine, post-draft add) |

### Wild Opponents (8 teams, 11U travel)
| Team | GC Team ID | Status |
|---|---|---|
| Arena National Browning 11U | `1yv2qtI89QSD` | Active |
| South Charlotte Panthers 11U | `Kih0oavXNZB3` | Active |
| Weddington Wild 11U | `Ye94sB963tUX` | Active |
| QC Flight Baseball 11U | `1gqDRuls0oER` | Active |
| T24 Garnet 11U | `I2XcyUwmye3p` | 0 FINAL games on GC — not a priority |
| SBA Alabama National 12U | `Wn2Abf32IXOz` | Added Apr 23 |
| TN Nationals Heichelbech 12U | `QebtI4WHVMPn` | Added Apr 23 |
| Tega CAY Titans 11U | `PVUBGhDYocE0` | Active |

### Storm Opponents (9 teams, 9U travel)
| Team | GC Team ID | Status |
|---|---|---|
| ITAA 9U Spartans | `lTxYlYLH52KU` | Active |
| MARA 9U Stingers | `VdoWDJdlCgAH` | Active |
| South Charlotte Challenge 9U Doggett | `lc7rtdls8Ht6` | Active |
| Pineville Blue Sox 9U | `igECV1q4jzFV` | Active |
| LKN Lightning 10U | `xduuY8fEkGLx` | Active — team_id corrected Apr 28 |
| Park Sharon Nationals 10U | `HZ3pkdRb5s6P` | Active |
| Weddington Stormtroopers | `L3KLX1oI2VGl` | Active |
| Lake Norman Lightning 9U | `H130ItYghVag` | Active |
| Dilworth 9U - Navy | `eR45wjQRgKYW` | Active — folder name fixed v2.4.0 |

---

## Known Issues / Pending Work

### High Priority — Fix Before Next Weekly Run
| Issue | Details | Fix |
|---|---|---|
| ~~Minors scorebook files missing~~ | ~~gen_reports.py couldn't find away-game scorebooks~~ | **RESOLVED** — was Google Drive sync delay, not a code bug. All 14 teams now working (90 games, 2342 PAs). |
| ~~BOX-VERIFY warnings widespread in Minors~~ | ~~Nearly every Minors team showed parsed AB/BB lower than box score~~ | **RESOLVED** — downstream symptom of the sync issue above. |

### Medium Priority — Quality Improvements
| Issue | Details | Fix |
|---|---|---|
| ~~`Infield Fly` not in OUTCOME_TYPES~~ | ~~Parsed as unknown outcome~~ | **FIXED** — Added to both `gen_reports.py` and `parse_gc_text.py` |
| `$awyer M` in T24 Garnet games | Dollar sign in player name from GC | **READY** — `GC_NAME_FIXES` dict in `parse_gc_text.py` will auto-fix on next scrape |
| ~~QC Flight Baseball 11U team_id missing~~ | ~~Can't scrape games~~ | **FIXED** — team_id `1gqDRuls0oER` added to both scrapers |
| T24 Garnet 11U scraping incomplete | 0 FINAL games on GC | **Not a bug** — games not yet finalized in GameChanger. Re-check weekly. |
| ~~QC Flight roster.txt Google Drive timeout~~ | ~~`[Errno 60]` on file read~~ | **RESOLVED** — toggling offline availability forced re-sync |

### Low Priority / Cosmetic
| Issue | Details | Fix |
|---|---|---|
| Minors jersey numbers unavailable | GC box score pages for Minors org redirect to /info | Permanent — no fix available |
| ~~SS spray chart zone always 0~~ | ~~Parser mapped both SS and 3B to zone "3B" in `FIELDER_ZONES`~~ | **FIXED** — `("shortstop","SS")` corrected in `gen_reports.py` line 317; all PDFs regenerated Apr 23 |
| ~~`?N P?` and `?C C?` in Cubs-Holtzer~~ | ~~Players not in rosters.json~~ | **RESOLVED** — Nathan P. #10 and Chase C. #3 confirmed in rosters.json |
| Rays-Madero jersey gap | Only 2/13 players have jersey #s in rosters.json | Run `scrape_gc_boxscores.py --force --division Majors` if data improves |
| `date` variable not defined at line ~767 in `scrape_gc_boxscores.py` | Pre-existing lint error, not from our changes | **FIXED** Apr 24 — added `date` to `from datetime import datetime, date` |

### Apr 24 2026 (Session 4) — Bugs 7–9 Fixed
| Bug | Details | Fix |
|---|---|---|
| **SCHEDULE_JS `final` detection broken (Wild/Storm)** | Team pages show score (`W 7-5`) not `FINAL` — 0 games found for all Wild/Storm | Added `/^[WL]\s+\d+-\d+/` score-pattern check alongside `FINAL` in both scrapers. Commit `ea04909` |
| **Team-page filenames: no date, wrong team name** | Day-abbr/number outside `<a>` tag — `currentDateTag` stayed empty; location string used as team name | Added leaf-node date detection + `is_home` field + `team_name`-based filename logic. Commit `00d8d40` |
| **`NameError: date not defined`** | `scrape_gc_boxscores.py` crashed on first Wild/Storm roster write | Added `date` to `from datetime import datetime, date`. Commit `00d8d40` |

---

## Latest Pipeline Run Results (Apr 23, 2026 — Session 3 continued)

### New games scraped (Apr 23)
- 4 new FINAL games picked up: Apr22-Guardians-Esau_vs_Cubs-Holtzer, Apr22-Rangers-Leonard_vs_Guardians-Plunkett, Apr22-Brewers-Linnenkohl_vs_Marlins-Eberlin, Apr22-Astros-Barbour_vs_Braves-Brooks
- All 4 processed and reviewed successfully

### Majors (11 teams) ✅
- All 11 PDFs regenerated with SS fix applied
- 39 games total (4 new vs. session 2)

### Minors (14 teams) ✅
- All 14 PDFs regenerated with SS fix applied
- 94 games total (4 new vs. session 2, 2342+ PAs)

### Wild / Storm
- Unchanged from session 2 (no new games scraped for travel divisions)
- All PDFs regenerated with SS fix applied

---

## Next Session Priorities

**Read these files first:** `Instructions.md` (this file), `CHANGELOG.md`

**Current version: v2.4.0** — LG RANK for all four divisions; diagnostic No PAs warning.

1. **Monitor nightly runs** — verify `launchd` fires correctly at 10pm EDT on game nights;
   check `Logs/nightly_*.log` and `Logs/launchd_stdout.log` after first automated run.

2. **macOS notification on pipeline completion/failure** — optional polish; would surface
   a native macOS notification after each nightly run (success or error) without needing
   to check log files manually. Could use `osascript` in `run_scout_nightly.sh`.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `0 PAs` for a team | Team name mismatch (folder vs. inning header) | Check exact spelling in game file header vs. folder name |
| `?F L?` in output | Player initials not in rosters.json | Run scrape_gc_boxscores.py; or add to roster_additions in gen_reports.py |
| `INNING GAP` in log file | Skipped inning in parse (debug-only, log file only) | Check raw game file for noise text blocking inning header match |
| `WARNING UNKNOWN` | Play outcome not in OUTCOME_TYPES | Check the play text; if valid, add to parser |
| `BOX-VERIFY` in log file | Parsed AB/BB differs from box score (debug-only, log file only) | Review game file for missed plays |
| Jersey numbers missing (Majors) | rosters.json not yet populated | Run `scrape_gc_boxscores.py --division Majors` locally |
| Jersey numbers missing (Minors) | Box scores inaccessible | Known permanent limitation |
| Session expired error | gc_session.json expired | Run `python3 scrape_gc_playbyplay.py --login` |
| macOS folder rename case bug | macOS case-insensitive FS | Two-step rename: `mv "old" "tmp" && mv "tmp" "New"` |

---

## Cowork Fallback (Emergency Use Only)

Cowork cannot run `scrape_gc_playbyplay.py` or `scrape_gc_boxscores.py` (Playwright not installed;
`web.gc.com` on network blocklist). **All scraping must run locally via Claude Code.**

`gen_reports.py` runs fine in Cowork — use for on-demand PDF generation when game
files already exist.

**Emergency manual scrape via Cowork Chrome MCP** (3–4 games max, ~10 tool calls/game):
1. Navigate Chrome MCP to the `/plays` URL for the game
2. Extract page text in 600-char chunks via JS: `JSON.stringify(window._gcText.substring(N, N+600))`
   (store full text first: `window._gcText = document.body.innerText`)
3. Assemble chunks into `outputs/raw_TEAM_N.txt`
4. Run `parse_gc_text.py` to convert to WCWAA format
5. Move to the correct `Scorebooks/` or `Games/` folder

---

## Stat Formulas Reference

| Stat | Formula |
|---|---|
| PA | All plate appearances (BB + HBP + AB + SF + SB) |
| AB | PA − (BB + HBP + SF + SB) |
| AVG | H / AB |
| OBP | (H + BB + HBP) / (AB + BB + HBP) |
| SLG | TB / AB |
| C% | (AB − K_total) / AB |
| GB% | Ground ball BIP / total BIP |
| FB+LD% | (Fly ball + line drive BIP) / total BIP |
| SM% | Swing-and-miss / total swings |
| CStr% | Called strikes / total pitches seen |
| FPT% | First-pitch takes / (takes + swings on first pitch) |
