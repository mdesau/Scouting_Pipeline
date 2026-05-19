# WCWAA 2026 Spring — Scouting Report Pipeline

This file is the authoritative reference for the WCWAA scouting report pipeline.
Load it at the start of every new AI coding session (GitHub Copilot, Claude, etc.).
It covers every design decision, known bug, and operational detail accumulated
across the full build history of this project.

**Root directory (all paths relative to this):**
`~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My Drive/Baseball/WCWAA/2026/Spring/`

**Best practices prompt:** When starting a new session, the user may paste their
"Code Mentor" prompt which defines conventions for debugging, git hygiene, error
handling, and code style. Follow those guidelines throughout.

---

## Development Environment

- **Python 3.9.6** (macOS system Python)
- **Virtual environment:** `Scout_Development/venv/` — shared by both apps; always activate before running scripts
- **Key packages:** Playwright 1.58.0, Chromium 145, ReportLab 4.4.10
- **Frozen deps:** `requirements.txt` in repo root
- **Git:** Local repo rooted at `Spring/` on `main` branch
- **GitHub remote:** `https://github.com/mdesau/Scouting_Pipeline` (private)
  - PAT stored in `.git/config` remote URL — rotate at github.com/settings/tokens if needed

### Version History
```
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

## Project Summary

Two apps in one repo — automated scouting reports for Weddington youth baseball (Spring 2026).

| App | Purpose | Output |
|---|---|---|
| **Scout Development** | Scrapes GameChanger, computes batting stats + archetypes, generates hitting PDFs | `*-Scout-Hitting_2026.pdf` |
| **Pitching Savant** | Reads same game files, computes pitching stats + league percentiles, generates Baseball Savant-style pitcher cards | `*-Scout-Pitching_2026.pdf` |

Both apps share the same virtual environment and game file data.

### Divisions

| Division | Age | Teams | Scope |
|---|---|---|---|
| Majors | 11U in-house | 11 teams | Full league — reports on all opponents |
| Minors | 9U in-house | 14 teams | Full league |
| Wild | 11U travel | 8 opponent teams | Reports on travel opponents only |
| Storm | 9U travel | 12 opponent teams | Reports on travel opponents only |

---

## Scripts Overview (line counts as of May 17, 2026)

| Script | Lines | App | Role |
|---|---|---|---|
| `Scout_Development/Scripts/gen_hitting.py` | 2067 | Scout | Stat engine + PDF generator (hitting) |
| `Pitching_Savant/Scripts/gen_pitching.py` | 1315 | Pitching | Stat engine + PDF generator (pitching) |
| `Scout_Development/Scripts/scrape_gc_boxscores.py` | 841 | Scout | Playwright: GC box scores → rosters |
| `Scout_Development/Scripts/run_menu.py` | 673 | Scout | Pipeline orchestrator (4-step: scrape → rosters → hitting → pitching) |
| `Scout_Development/Scripts/scrape_gc_playbyplay.py` | 632 | Scout | Playwright: GC schedule → .txt game files |
| `Pitching_Savant/Scripts/pilot_card.py` | 521 | Pitching | Early proof-of-concept (superseded by gen_pitching.py) |
| `Scout_Development/Scripts/parse_gc_text.py` | 270 | Scout | Raw GC text → WCWAA format (utility) |
| `Scout_Development/Scripts/diag_schedule.py` | 144 | Scout | Schedule diagnostics (utility) |
| `Scout_Development/Scripts/patch_march_initials.py` | 117 | Scout | One-time March game file patch (utility) |
| `Scout_Development/Scripts/scrape_storm.py` | 62 | Scout | Legacy Storm scraper (superseded) |

### Shell Launchers

| Script | Purpose |
|---|---|
| `Scout_Development/Scripts/run_scout.sh` | Manual launcher: activates venv, calls run_menu.py (interactive) |
| `Scout_Development/Scripts/run_scout_nightly.sh` | Headless launcher: no menu; calls `run_menu.py --all` (for launchd) |
| `Pitching_Savant/Scripts/run_pitching.sh` | Standalone manual launcher for pitching PDFs only |
| `Pitching_Savant/Scripts/run_pitching_nightly.sh` | Standalone headless launcher for pitching PDFs only |

---

## Directory Structure

```
Spring/                              <- git repo root (v2.5.0)
|-- .git/
|-- .gitignore
|-- README.md                        <- project overview (shared)
|-- Instructions.md                  <- this file (shared)
|-- requirements.txt                 <- pip freeze (shared)
|
|-- Scout_Development/               <- App 1: Scraping + Hitting Reports
|   |-- CHANGELOG.md                 <- per-app version history
|   |-- BUGS.md                      <- per-app bug tracker
|   |-- Scripts/
|   |   |-- scrape_gc_playbyplay.py  <- Step 1: GC schedule -> .txt game files
|   |   |-- scrape_gc_boxscores.py   <- Step 2: GC box scores -> rosters
|   |   |-- gen_hitting.py           <- Step 3: stat engine + hitting PDFs
|   |   |-- parse_gc_text.py         <- utility: raw GC text -> WCWAA format
|   |   |-- run_menu.py              <- pipeline orchestrator (Steps 1-4)
|   |   |-- run_scout.sh             <- manual launcher
|   |   |-- run_scout_nightly.sh     <- headless launcher (launchd)
|   |   |-- gc_session.json          <- Playwright session [gitignored]
|   |   +-- archetype_reference.txt  <- archetype system design notes
|   |-- examples/
|   |-- launchd/
|   |   +-- com.wcwaa.scout_pipeline.plist
|   |-- Logs/                        <- [gitignored]
|   +-- venv/                        <- shared Python venv [gitignored]
|
|-- Pitching_Savant/                 <- App 2: Pitching Profile Cards
|   |-- CHANGELOG.md
|   |-- BUGS.md
|   |-- Scripts/
|   |   |-- gen_pitching.py          <- Step 4: stat engine + pitching PDFs
|   |   |-- pilot_card.py            <- early POC (superseded)
|   |   |-- pitcher_icon.png         <- Savant-style pitcher silhouette
|   |   |-- run_pitching.sh          <- standalone manual launcher
|   |   +-- run_pitching_nightly.sh  <- standalone headless launcher
|   +-- Logs/                        <- [gitignored]
|
|-- Majors/                          <- [gitignored] game data + PDFs
|   +-- Reports/
|       |-- Scorebooks/              <- .txt game files
|       |-- Scouting_Reports/        <- hitting + pitching PDFs
|       |-- rosters.json
|       +-- box_verify.json
|-- Minors/                          <- [gitignored] same structure
|-- Wild/                            <- [gitignored] travel teams
|   +-- [TeamName]/
|       |-- Games/                   <- .txt game files
|       |-- roster.txt
|       |-- *-Scout-Hitting_2026.pdf
|       +-- *-Scout-Pitching_2026.pdf
|-- Storm/                           <- [gitignored] travel teams (same structure)
+-- Coach_Pitch/                     <- [gitignored] separate division
```

---

## Pipeline Workflow

The pipeline runs 4 steps, orchestrated by `run_menu.py`:

| Step | Script | What it does |
|---|---|---|
| 1 | `scrape_gc_playbyplay.py` | Scrapes GC schedule pages, downloads play-by-play, saves .txt game files |
| 2 | `scrape_gc_boxscores.py` | Scrapes GC box scores, builds/updates rosters.json + roster.txt |
| 3 | `gen_hitting.py` | Parses game files, computes batting stats + archetypes, generates hitting PDFs |
| 4 | `gen_pitching.py` | Parses same game files, computes pitching stats + percentiles, generates pitching PDFs |

Step 1 skips games already on disk (safe to re-run). Step 2 is incremental by default.

### Running the Pipeline

**Option A -- interactive menu:**
```bash
cd .../Scout_Development/Scripts
bash run_scout.sh
```

**Option B -- nightly scheduled (launchd at 10pm EDT):**
```bash
launchctl list | grep wcwaa          # verify scheduler active
launchctl start com.wcwaa.scout_pipeline  # trigger immediately
```

**Option C -- CLI direct:**
```bash
# Full pipeline, all divisions
bash run_scout.sh --all

# Single division
bash run_scout.sh --division Wild

# Single team
bash run_scout.sh --division Majors --team "Cubs-Holtzer"

# Pitching only (standalone)
cd .../Pitching_Savant/Scripts
bash run_pitching.sh --division Majors
```

**Step-by-step manual:**
```bash
python3 scrape_gc_playbyplay.py                     # Step 1
python3 scrape_gc_boxscores.py                      # Step 2
python3 gen_hitting.py --division Majors             # Step 3
python3 gen_pitching.py --division Majors            # Step 4
```

---

## Function Map -- Scout Development

### scrape_gc_playbyplay.py (Step 1 -- Playwright scraper)
Navigates GC schedule pages, finds FINAL games, downloads play-by-play text, converts via `parse_gc_text.py`, saves `.txt` game files.

| Function | ~Line | Purpose |
|---|---|---|
| `run()` | ~511 | CLI entry point -- parses `--division`, `--team`, `--login`, `--check`, `--force`, `--verbose`; loops divisions |
| `scrape_org_division()` | ~361 | Org-level scraper (Majors/Minors): loads org schedule, finds FINAL games |
| `scrape_team_division()` | ~431 | Team-level scraper (Wild/Storm): loads per-team schedule page |
| `extract_plays_raw()` | ~336 | Navigates to `/plays` URL, extracts raw page text via Playwright |
| `is_covered()` | ~355 | Checks whether a game file already exists on disk (skip logic) |
| `get_schedule()` | ~321 | Runs `SCHEDULE_JS` in browser, returns parsed schedule array |
| `setup_logging()` | ~87 | Configures file + console logging with `--verbose` support |
| `fmt_date()` | ~307 | Normalizes GC date strings to `MonDD` format for filenames |
| `safe()` | ~316 | Sanitizes team name for use in filenames |
| `SCHEDULE_JS` | ~130 | JS injected into browser to extract game cards from GC's React DOM |
| `DIVISIONS` dict | ~85 | All team IDs, slugs, folder paths -- **edit here to add/remove teams** |

**Dependencies:** `parse_gc_text.parse_gc_raw()`, `gc_session.json`

### scrape_gc_boxscores.py (Step 2 -- Playwright scraper)
Navigates GC `/box-score` pages, extracts player names + jersey numbers + AB/BB/SO, builds rosters.json (Majors/Minors) and roster.txt (Wild/Storm), writes box_verify.json.

| Function | ~Line | Purpose |
|---|---|---|
| `run()` | ~798 | CLI entry point -- parses `--division`, `--team`, `--force`, `--verbose` |
| `scrape_division()` | ~515 | Org-level scraper (Majors/Minors) |
| `scrape_team_division()` | ~649 | Team-level scraper (Wild/Storm) |
| `_accum_player()` | ~385 | Core per-player accumulator: detects collisions, promotes to 5-char keys |
| `_prepare_for_save()` | ~491 | Strips transient fields before writing to disk |
| `merge_player()` | ~324 | Merges new box score data into existing roster entry |
| `_first_name_from()` | ~355 | Extracts first name from GC display string |
| `_disambig_key()` | ~376 | Builds 5-char disambiguation key (e.g. `B A` -> `Bri A`) |
| `display_name()` | ~305 | Formats `"FirstName L. #jersey"` display string |
| `normalize_team_name()` | ~288 | Applies `TEAM_NAME_ALIASES` to fix GC name differences |
| `setup_logging()` | ~125 | Configures logging |
| `DIVISIONS` dict | ~100 | Must match scrape_gc_playbyplay.py exactly |
| `TEAM_NAME_ALIASES` | ~60 | Maps GC box score team name variants -> canonical keys |

**Known limitation:** Minors `/box-score` pages redirect to `/info` -- jersey numbers permanently unavailable.

### gen_hitting.py (Step 3 -- Hitting stat engine + PDF generator)
Reads game `.txt` files, parses every plate appearance, computes batting stats + archetypes, generates multi-page PDF scouting reports via ReportLab.

| Function | ~Line | Purpose |
|---|---|---|
| `main()` | ~2031 | CLI entry point -- parses `--division`, `--team`, `--verbose` |
| `run_league()` | ~1729 | Division runner for Majors/Minors |
| `run_wild()` | ~1863 | Travel division runner (Wild/Storm): two-pass with LG RANK |
| `build_league_context()` | ~1675 | Pre-scans all scorebooks; returns league-wide percentile data |
| `get_wild_opponents()` | ~1625 | Discovers Wild/Storm opponent folders on disk |
| `load_wild_roster()` | ~1639 | Reads `roster.txt` for a travel opponent |
| `generate_pdf()` | ~1408 | ReportLab PDF assembly: team card + player cards + summary/notes |
| `draw_card()` | ~1299 | Renders one player or team card: spray chart, stat bars, archetype |
| `draw_field_spray_chart()` | ~1171 | Heat-map spray chart with BIP dots |
| `draw_stat_box()` | ~1272 | Renders a single stat label + value box |
| `draw_bar()` | ~1279 | Renders a horizontal percentage bar |
| `draw_header()` | ~1100 | Draws PDF page header |
| `mark_reviewed()` | ~1071 | Renames processed game file to `-Reviewed.txt` |
| `generate_notes()` | ~997 | Full narrative scouting note for a batter |
| `generate_notes_short()` | ~1042 | Compact note for summary page |
| `get_pitching_approach()` | ~989 | Archetype -> pitching recommendation lookup |
| `get_archetype()` | ~865 | Applies Approach x Result label using percentiles |
| `_roster_percentiles()` | ~848 | Computes league-wide percentile thresholds |
| `_rank_stat()` | ~807 | Dense rank helper for LG RANK row |
| `compute_team_totals()` | ~728 | Aggregates all batters -> single team-level stat dict |
| `compute_stats()` | ~614 | Aggregates PA list -> per-batter stat dict |
| `verify_game()` | ~582 | Runs all verification layers on a parsed game |
| `check_batting_order()` | ~523 | Verification layer 3 |
| `check_inning_continuity()` | ~493 | Verification layer 1 |
| `parse_game_for_team()` | ~430 | Core parser: reads .txt file, extracts PAs per batter |
| `parse_pitch_seq()` | ~389 | Parses pitch sequence string into swing/take/foul counts |
| `parse_outcome()` | ~340 | Maps play description -> outcome code |
| `parse_ball_type()` | ~327 | Classifies BIP as ground ball, fly ball, or line drive |
| `extract_zone()` | ~322 | Extracts fielding zone for spray chart |
| `verify_box_score()` | ~262 | Verification layer 4: cross-checks vs box_verify.json |
| `_disambiguate_pas()` | ~213 | Splits shared-initials PAs using `_collision_map` |
| `load_box_verify()` | ~202 | Loads box_verify.json |
| `load_box_rosters()` | ~159 | Loads rosters.json |
| `setup_logging()` | ~43 | Configures logging |
| `DIVISIONS` dict | ~80 | Folder paths + roster file locations |
| `INNING_RE` | ~420 | Regex for `===Top/Bottom N - TeamName===` headers |
| `PITCHING_APPROACH` | ~952 | Archetype -> pitching recommendation lookup dict |

### parse_gc_text.py (Utility)
Converts raw GC page text into WCWAA-structured `.txt` game file format. Called by `scrape_gc_playbyplay.py` -- never run directly.

| Function | ~Line | Purpose |
|---|---|---|
| `parse_gc_raw()` | ~80 | Main entry: raw text string -> formatted game file string |
| `GC_NAME_FIXES` | ~20 | Dict of known GC data errors to auto-correct |
| `OUTCOME_TYPES` | ~35 | Outcome string -> code mapping (must sync with gen_hitting.py) |

### run_menu.py (Orchestrator)
Interactive numbered menu + CLI passthrough. Calls Steps 1->2->3->4 as subprocesses.

| Function | ~Line | Purpose |
|---|---|---|
| `main()` | ~597 | CLI entry point -- parses `--all`, `--division`, `--team` |
| `interactive_menu()` | ~525 | Menu: [0] Full, [1] Division, [2] Team, [3] Add team |
| `run_pipeline()` | ~207 | Runs steps 1->2->3->4 as subprocesses for given scope |
| `_run()` | ~276 | Subprocess wrapper with exit-code handling |
| `add_new_team()` | ~429 | Wizard: paste GC URL -> creates folder + inserts into scrapers |
| `_parse_gc_url()` | ~303 | Extracts `team_id` and `slug` from a GC schedule URL |
| `_slug_to_folder_name()` | ~327 | Converts GC slug to folder name |
| `_insert_team_into_file()` | ~366 | Inserts a new team tuple into a scraper's DIVISIONS dict |
| `get_team_list()` | ~174 | Reads DIVISIONS to build team picker list |
| `check_session()` | ~103 | Validates gc_session.json exists and is not expired |

**Step 4 integration:** `run_pipeline()` calls `gen_pitching.py` from `Pitching_Savant/Scripts/` after gen_hitting.py. Path resolved via `SPRING_DIR / "Pitching_Savant" / "Scripts" / "gen_pitching.py"`.

---

## Function Map -- Pitching Savant

### gen_pitching.py (Step 4 -- Pitching stat engine + PDF generator)
Reads game `.txt` files from the opponent's perspective (who was pitching), computes 13 pitching stats, ranks all pitchers in the division by percentile, generates Baseball Savant-style pitcher profile cards with colored slider bars.

**Imports from Scout Development:** `DIVISIONS` dict from `scrape_gc_playbyplay.py` (team IDs, slugs) and `DIVISIONS` dict from `gen_hitting.py` (folder paths). Uses shared venv.

| Function | ~Line | Purpose |
|---|---|---|
| `setup_logging()` | ~103 | Configures file + console logging |
| **Parsing** | | |
| `parse_outcome()` | ~189 | Maps play description -> outcome code (mirrors gen_hitting.py) |
| `parse_ball_type()` | ~235 | Classifies BIP as GB, FB, or LD |
| `parse_pitch_seq()` | ~254 | Parses pitch sequence -> swing/take/foul/ball/strike counts |
| `parse_game_for_pitching_team()` | ~293 | Core parser: reads .txt file, extracts PAs attributed to each pitcher. Uses carry-forward logic for pitcher tracking + pre-scan to skip games not involving the team |
| **Stats** | | |
| `compute_pitcher_stats()` | ~444 | Aggregates all PAs for one pitcher -> 13-stat dict (ERA-proxy, WHIP, K/9, BB/9, K%, BB%, K/BB, BABIP, HR/9, FPSH%, GB%, FB+LD%, C%) |
| `compute_percentile_rank()` | ~586 | Ranks a value against all values in the division; supports `low_is_good` flip |
| `compute_all_percentiles()` | ~626 | Builds percentile rows for every pitcher across all 13 stats |
| **PDF Rendering** | | |
| `pct_to_color()` | ~719 | Maps percentile (0-100) to red->yellow->green color |
| `draw_gradient_bar()` | ~728 | Draws the colored Savant-style slider bar |
| `draw_bubble()` | ~736 | Draws the percentile bubble on the slider |
| `draw_axis_labels()` | ~748 | Draws "Poor" / "Great" axis labels |
| `draw_stat_row()` | ~761 | Renders one stat row: label, value, slider bar, percentile bubble |
| `draw_pitcher_icon()` | ~798 | Draws the Savant pitcher silhouette PNG in card header |
| `draw_pitcher_card()` | ~828 | Renders a complete pitcher card (header + 13 stat rows) |
| `card_origin()` | ~875 | Computes x,y position for 4-cards-per-page layout |
| `generate_pitching_pdf()` | ~884 | Assembles full PDF: pages of 4 cards each |
| **File I/O** | | |
| `find_game_files()` | ~912 | Finds .txt and -Reviewed.txt game files in a directory |
| `load_rosters_json()` | ~932 | Loads rosters.json for Majors/Minors display names |
| `load_roster_txt()` | ~940 | Loads roster.txt for Wild/Storm display names |
| `dedup_pitcher_names()` | ~964 | Merges initials-only entries into full-name counterparts (e.g. "K D" -> "Kilean D"); discards unresolvable orphan initials |
| **Division Runners** | | |
| `run_league_division()` | ~1018 | Runs Majors or Minors: two-pass (collect all pitchers -> compute percentiles -> generate per-team PDFs) |
| `run_travel_division()` | ~1141 | Runs Wild or Storm: auto-discovers team folders, applies dedup, same two-pass flow |
| `main()` | ~1282 | CLI entry point -- parses `--division`, `--team`, `--verbose` |

### Pitching Stats Computed (13 stats, 2 flipped)

| Stat | Formula | Direction |
|---|---|---|
| ERA-proxy | (ER / IP) x 9 -- ER estimated as (H+BB+HBP-K) x 0.3 | Low is good |
| WHIP | (H + BB) / IP | Low is good |
| K/9 | (K / IP) x 9 | High is good |
| BB/9 | (BB / IP) x 9 | **Low is good (flipped)** |
| K% | K / PA | High is good |
| BB% | BB / PA | Low is good |
| K/BB | K / BB | High is good |
| BABIP | (H - HR) / (AB - K - HR + SF) | Low is good |
| HR/9 | (HR / IP) x 9 | Low is good |
| FPSH% | First-pitch strikes+hits / PA | **Low is good (flipped)** |
| GB% | Ground balls / BIP | High is good |
| FB+LD% | (Fly balls + line drives) / BIP | Low is good |
| C% | Contact % = (AB - K) / AB | Low is good |

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
- Wild/Storm folder names MUST exactly match the GC inning header spelling
- Majors/Minors team key is `TeamName-CoachLast` (e.g. `Cubs-Holtzer`)
- Pitching Savant uses `, [INITIALS] pitching` lines to track pitcher changes

---

## Roster Format

### Majors/Minors -- rosters.json
```json
{
  "Cubs-Holtzer": {
    "S K":  { "display": "Sullivan K. #12", "jersey": "12", "ab": 40 },
    "Bri A": { "display": "Brian A. #5", "jersey": "5" },
    "_collision_map": { "B A": ["Bri A", "Ben A"] }
  }
}
```

### Wild/Storm -- roster.txt
```
# T24 Garnet 11U -- roster.txt
T M, Tyler M. #4
S G, Srijan G. #11
```

---

## Duplicate Initials Handling (Brian/Ben Allen Bug)

**Problem:** Two players share initials `B A` on Cubs-Holtzer.
**Fix:** `scrape_gc_boxscores.py` promotes both to 5-char keys (`Bri A`, `Ben A`) and writes `_collision_map`. `gen_hitting.py._disambiguate_pas()` alternates PA assignments by batting order.

---

## Verification System (4 Layers)

| Layer | Check | Severity |
|---|---|---|
| 1 | Inning continuity -- no skipped innings | Log only |
| 2 | Unknown outcomes -- unrecognised play descriptions | WARNING (stdout) |
| 3 | Batting order -- PA counts consistent with lineup | Log only |
| 4 | Box score cross-check -- parsed AB/BB vs. box_verify.json | Log only |

None stop PDF generation.

---

## Archetype System (Hitting Reports)

Each player card shows a 2-word label: **Approach x Result**.

**Approach** (plate discipline): Aggressive, Passive, or Disciplined
**Result** (league-relative): Walker, Overmatched, Power, or Contact

Cards with 5-9 PA show `*` suffix. Fewer than 5 PA: `--`.

**Pitching approach matrix:**

| Archetype | Recommendation |
|---|---|
| Aggressive Power/Contact | Edges + Mix Speed |
| Aggressive Overmatched | Climb the Ladder |
| Aggressive Walker | Outside - In |
| Disciplined Power/Contact | Keep Mixing |
| Disciplined Overmatched/Walker | Attack the Zone |
| Passive Power/Contact | Attack & Expand |
| Passive Overmatched/Walker | Attack the Zone |

---

## Adding a New Wild or Storm Opponent

1. Get GC schedule URL: `https://web.gc.com/teams/{team_id}/{slug}/schedule`
2. In `scrape_gc_playbyplay.py`, add tuple to `DIVISIONS["Wild"/"Storm"]["teams"]`
3. Make identical addition in `scrape_gc_boxscores.py`
4. Create folder: `Wild/[Exact Team Name]/Games/` (name must match GC inning headers exactly)

Or use the interactive menu: `bash run_scout.sh` -> option [3] "Add new team"

---

## Teams Reference (Spring 2026)

### Majors (11 teams)
Guardians-Esau, Royals-Hall, Diamondbacks-Vandiford, Marlins-McLendon,
Dodgers-Pearson, As-Blanco, Braves-Rue, Twins-Ewart, Padres-Schick,
Cubs-Holtzer (has B A collision map), Rays-Madero

### Minors (14 teams)
Astros-Barbour, Dodgers-Winchester, Padres-Midkiff, Reds-Naturale,
Rangers-Leonard, Yankees-DePasquale, Marlins-Eberlin, Guardians-Plunkett,
Angels-Casper, Braves-Brooks, Cubs-Verlinde, Brewers-Linnenkohl,
Rays-Pearson, Mets-Hornung

### Wild (8 teams, 11U travel)
Arena National Browning 11U, South Charlotte Panthers 11U,
Weddington Wild 11U, QC Flight Baseball 11U, T24 Garnet 11U,
SBA Alabama National 12U, TN Nationals Heichelbech 12U, Tega Cay Titans 11U

### Storm (12 teams, 9U travel)
9u Challenge, ITAA 9U Spartans, MARA 9U Stingers,
South Charlotte Challenge 9U Doggett, Pineville Blue Sox 9U,
LKN Lightning 10U, Park Sharon Nationals 10U, Weddington Stormtroopers,
Lake Norman Lightning 9U, Dilworth 9U - Navy, Crushers White 10U,
Weddington 10U Gophers

---

## Prerequisites (First-Time Setup)

```bash
cd .../Scout_Development
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python3 Scripts/scrape_gc_playbyplay.py --login   # save GC session
```

---

## Stat Formulas Reference (Hitting)

| Stat | Formula |
|---|---|
| PA | All plate appearances (BB + HBP + AB + SF + SB) |
| AB | PA - (BB + HBP + SF + SB) |
| AVG | H / AB |
| OBP | (H + BB + HBP) / (AB + BB + HBP) |
| SLG | TB / AB |
| C% | (AB - K_total) / AB |
| GB% | Ground ball BIP / total BIP |
| FB+LD% | (Fly ball + line drive BIP) / total BIP |
| SM% | Swing-and-miss / total swings |
| CStr% | Called strikes / total pitches seen |
| FPT% | First-pitch takes / (takes + swings on first pitch) |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `0 PAs` for a team | Team name mismatch (folder vs. inning header) | Check exact spelling in game file header vs. folder name |
| `?F L?` in output | Player initials not in rosters.json | Run scrape_gc_boxscores.py; or add to roster_additions |
| `WARNING UNKNOWN` | Play outcome not in OUTCOME_TYPES | Add to parser |
| Jersey numbers missing (Minors) | Box scores inaccessible | Known permanent limitation |
| Session expired error | gc_session.json expired | `python3 scrape_gc_playbyplay.py --login` |
| High pitcher count (Wild/Storm) | Initials-only names not deduped | Check dedup_pitcher_names() logic |

---

## Next Session Priorities

1. **Code review + refactor** -- apply coding principles audit to both apps
2. **Monitor nightly runs** -- verify launchd fires correctly
3. **Push to GitHub** -- `git push origin main --tags`
