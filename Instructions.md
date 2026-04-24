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
- **Git:** Local repo on `main`, tagged `v0.1.0`, `v0.2.0`, `v1.0.0`, `v2.0.0` (current)
- **GitHub remote:** `https://github.com/mdesau/Scouting_Pipeline` (private)
  - PAT stored in `.git/config` remote URL — rotate at github.com/settings/tokens if needed

```
e9f338e  (tag: v2.0.0) chore: __version__ = 2.0.0, version banner, CHANGELOG v1.0.0+v2.0.0
0d7e2e7  fix: gen_reports --team filter uses partial match for Wild/Storm
fd26a40  fix: Wild/Storm PDF jersey numbers missing — load_wild_roster dual key format (Bug 11)
c7a0109  fix: scrape_box_scores --team filter; Step 2 respects single-team selection (Bug 10)
cc76d6e  docs: log Bugs 7-9 in Bugs_List.txt, Instructions.md, CHANGELOG
00d8d40  fix: SCHEDULE_JS team-page date/filename + date import (Bugs 8-9)
ea04909  fix: SCHEDULE_JS final detection for Wild/Storm team pages (Bug 7)
f858c3d  feat: add interactive_menu.py — numbered pipeline menu
c2828e4  feat: rename run_weekly.sh → run_scout.sh; add SBA Alabama + TN Nationals
0e4c05e  (tag: v1.0.0) docs: log Bug 6 — SS spray chart zone mapped to 3B
```

### Scripts Overview (line counts as of Apr 23, 2026)
| Script | Lines | Role | Has --verbose | Has DEBUG_CONFIG | Has try/except |
|---|---|---|---|---|---|
| `gc_scraper.py` | 532 | Playwright: GC schedule → .txt game files | ✅ | ✅ | ✅ |
| `scrape_box_scores.py` | 820 | Playwright: GC box scores → rosters.json | ✅ | ✅ | — |
| `gen_reports.py` | 1756 | Stat engine + PDF generator | ✅ | ✅ | ✅ (run_wild) |
| `parse_gc_text.py` | 270 | Raw GC text → WCWAA format (utility) | — | — | — |
| `run_scout.sh` | 55 | Shell launcher — activates venv, calls interactive_menu.py | — | — | — |
| `interactive_menu.py` | ~300 | Interactive pipeline menu — numbered team/division picker, add-new-team flow | — | — | — |

---

## Project Summary

Automated scouting report pipeline for Weddington youth baseball leagues (Spring 2026).
Pulls play-by-play data from GameChanger (GC), computes batting stats + archetypes,
and generates multi-page PDF scouting reports for four divisions:

| Division | Age | Teams | Scope |
|---|---|---|---|
| Majors | 11U in-house | 11 teams | Full league — reports on all opponents |
| Minors | 9U in-house | 14 teams | Full league |
| Wild | 11U travel | 5 opponent teams | Reports on travel opponents only |
| Storm | 9U travel | 3 opponent teams | Reports on travel opponents only |

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
      gc_scraper.py            ← Playwright: GC schedule pages → .txt game files
      scrape_box_scores.py     ← Playwright: GC box scores → rosters.json + roster.txt
      parse_gc_text.py         ← converts raw GC page text → WCWAA .txt format
      gen_reports.py           ← stat engine + ReportLab PDF generator (all 4 divisions)
      run_scout.sh             ← pipeline launcher: activates venv, calls interactive_menu.py
      interactive_menu.py      ← interactive numbered menu (division/team picker, add-new-team)
      gc_session.json          ← saved Playwright GC login session (auth cookies) [gitignored]
      archetype_reference.txt  ← archetype system design notes
    Logs/                      ← runtime logs [gitignored]
      gen_reports_YYYYMMDD_HHMMSS.log
      gc_scraper_YYYYMMDD_HHMMSS.log
      scrape_box_scores_YYYYMMDD_HHMMSS.log

  Majors/
    Reports/
      Scorebooks/              ← .txt and -Reviewed.txt play-by-play game files
      Scouting_Reports/        ← output PDFs
      rosters.json             ← player names + jersey #s (built by scrape_box_scores.py)
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

**One command covers the full pipeline:**
```bash
cd ~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My\ Drive/Baseball/WCWAA/2026/Spring/Scout_Development/Scripts
bash run_scout.sh
```

**Step by step:**
```bash
python3 gc_scraper.py                     # Step 1: pull all new FINAL game files from GC
python3 scrape_box_scores.py              # Step 2: update rosters.json + jersey numbers
python3 gen_reports.py --division Majors  # Step 3: regenerate PDFs per division
python3 gen_reports.py --division Minors
python3 gen_reports.py --division Wild
python3 gen_reports.py --division Storm
```

Step 1 skips games already on disk (safe to re-run). Step 2 is incremental by default.
Use `--force` to re-scrape all games: `python3 gc_scraper.py --force`

---

## Common Commands

```bash
# Single team
python3 gen_reports.py --division Majors --team Cubs
python3 gen_reports.py --division Minors --team Rangers
python3 gen_reports.py --division Wild --team "T24 Garnet 11U"

# Single division scrape
python3 gc_scraper.py --division Storm
python3 gc_scraper.py --team "MARA 9U Stingers"

# Preview without writing (scraper dry-run)
python3 gc_scraper.py --check

# First-time login OR session expired
python3 gc_scraper.py --login
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
python3 gc_scraper.py --login
```

---

## How the Pipeline Works

### Step 1 — gc_scraper.py (Playwright scraper)
**What it does:** Navigates GC schedule pages for all 4 divisions, finds new FINAL games, downloads play-by-play text, converts via `parse_gc_text.py`, saves `.txt` game files.

**Key functions & locations:**
| Function | ~Line | Purpose |
|---|---|---|
| `main()` | ~470 | CLI entry point — parses `--division`, `--team`, `--login`, `--check`, `--force`, `--verbose` |
| `run_all_divisions()` | ~490 | Loops over `DIVISIONS` dict; calls `scrape_team_division()` per team |
| `scrape_team_division()` | ~200 | Core per-team logic: loads schedule, finds FINAL games, scrapes each |
| `scrape_plays_page()` | ~280 | Navigates to `/plays` URL, extracts raw page text via Playwright |
| `SCHEDULE_JS` | ~130 | JS string injected into browser to extract game cards from GC's React DOM |
| `DIVISIONS` dict | ~85 | All team IDs, slugs, folder paths — **edit here to add/remove teams** |
| `DEBUG_SCHEDULE_RAW`, `DEBUG_PAGE_TEXT` | ~70 | Debug flags for raw JS dumps |

**Dependencies:** `parse_gc_text.parse_gc_raw()`, `gc_session.json`

---

### Step 2 — scrape_box_scores.py (Playwright scraper)
**What it does:** Navigates GC `/box-score` pages, extracts player names + jersey numbers + AB/BB/SO stats, builds/updates `rosters.json` (Majors/Minors) and `roster.txt` (Wild/Storm), writes `box_verify.json`.

**Key functions & locations:**
| Function | ~Line | Purpose |
|---|---|---|
| `main()` | ~760 | CLI entry point — parses `--division`, `--force`, `--verbose` |
| `run_division()` | ~580 | Loads schedule, iterates FINAL games, calls `scrape_box_score_page()` |
| `scrape_box_score_page()` | ~380 | Extracts batter rows from GC box score via injected JS |
| `merge_player()` | ~260 | Merges new box score data into existing roster entry; handles `setdefault` migration guard |
| `detect_collision()` | ~300 | Detects shared initials (e.g. B A); promotes both to 5-char keys + writes `_collision_map` |
| `normalize_team_name()` | ~80 | Applies `TEAM_NAME_ALIASES` to fix GC rendering differences (e.g. `As-Blanco` vs `A's-Blanco`) |
| `DIVISIONS` dict | ~100 | All team IDs, slugs, output paths — **must match gc_scraper.py exactly** |
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
| `main()` | ~1700 | CLI entry point — parses `--division`, `--team`, `--verbose` |
| `run_majors()` / `run_minors()` | ~1550 | Division runners: pre-scan all teams for league-wide percentile thresholds, then generate each PDF |
| `run_wild()` / `run_storm()` | ~1600 | Travel division runners: per-opponent loop with try/except isolation |
| `parse_game_file()` | ~420 | Core parser: reads `.txt` file, applies `INNING_RE` + `DESC_RE`, extracts PAs per batter |
| `INNING_RE` | ~95 | Regex matching `===Top/Bottom N - TeamName===` headers — **critical: exact team name match** |
| `parse_outcome()` | ~300 | Maps play description string → outcome code (1B, 2B, K, BB, FO, GO, etc.) |
| `OUTCOME_TYPES` | ~110 | Dict of all recognised outcome strings — **add new play types here** |
| `compute_stats()` | ~560 | Aggregates PA list → per-batter stat dict (AVG, OBP, SLG, SM%, etc.) |
| `assign_archetype()` | ~650 | Applies Approach × Result label using league percentiles or fixed thresholds |
| `_disambiguate_pas()` | ~480 | Splits shared-initials PAs using `_collision_map` + batting order alternation |
| `build_pdf()` | ~750 | ReportLab PDF assembly: player cards + summary page |
| `draw_player_card()` | ~800 | Renders one player card: spray chart, stat bars, archetype label, pitching approach |
| `draw_summary_page()` | ~1100 | Renders summary table + two-sentence scouting notes per batter |
| `DIVISIONS` dict | ~130 | Folder paths + roster file locations per division |
| `DEBUG_PA_PARSING`, `DEBUG_ARCHETYPES`, `DEBUG_PITCH_SEQ` | ~42 | Debug flags |

**Dependencies:** `rosters.json` or `roster.txt` (from step 2), `.txt` game files (from step 1).

---

### Utility — parse_gc_text.py
**What it does:** Converts raw GC page text (scraped via Playwright) into the WCWAA-structured `.txt` game file format. Called internally by `gc_scraper.py` — never run directly.

**Key functions & locations:**
| Function | ~Line | Purpose |
|---|---|---|
| `parse_gc_raw()` | ~80 | Main entry: takes raw page text string, returns formatted WCWAA game file string |
| `GC_NAME_FIXES` | ~20 | Dict of known GC data errors to auto-correct (e.g. `"$awyer"` → `"Sawyer"`) |
| `OUTCOME_TYPES` | ~35 | Outcome string → code mapping (must stay in sync with `gen_reports.py`) |

**Dependencies:** None (pure utility, no imports beyond stdlib).

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

The `_collision_map` is written by `scrape_box_scores.py` when two players on the
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
1. `scrape_box_scores.py` — during box score accumulation, detects when a new player's
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
Until `scrape_box_scores.py` is run locally with the new code, the `rosters.json`
has been manually patched with the disambiguation and `_collision_map`.

---

## Verification System (4 Layers, runs on every gen_reports.py call)

| Layer | Check | Logged as |
|---|---|---|
| 1 | Inning continuity — no skipped innings per team per game | `WARNING INNING GAP` |
| 2 | Unknown outcomes — unrecognised play descriptions | `WARNING UNKNOWN` |
| 3 | Batting order — PA counts consistent with lineup (debug only) | `DEBUG ORDER/GAP` |
| 4 | Box score cross-check — parsed AB/BB vs. box_verify.json | `WARNING BOX-VERIFY` |

Warnings appear in the log file and on stdout. They do NOT stop PDF generation.

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
2. In `Scripts/gc_scraper.py`, find the `"Wild"` or `"Storm"` section in `DIVISIONS` (~line 115)
3. Add one tuple to the `"teams"` list:
   ```python
   ("team_id_from_url", "slug-from-url", "Exact Team Name"),
   ```
4. Make the identical addition in `Scripts/scrape_box_scores.py` (same section)
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

### Wild Opponents (11U travel)
| Team | GC Team ID | Status |
|---|---|---|
| Arena National Browning 11U | `1yv2qtI89QSD` | Active |
| South Charlotte Panthers 11U | `Kih0oavXNZB3` | Active |
| Weddington Wild 11U | `Ye94sB963tUX` | Active |
| T24 Garnet 11U | `I2XcyUwmye3p` | 0 FINAL games on GC — not a priority |
| QC Flight Baseball 11U | `1gqDRuls0oER` | Active — slug: `2026-spring-qc-flight-baseball-11u` |
| SBA Alabama National 12U | `Wn2Abf32IXOz` | Added Apr 23 — slug: `2026-summer-sba-alabama-national-12u` |
| TN Nationals Heichelbech 12U | `QebtI4WHVMPn` | Added Apr 23 — slug: `2026-summer-tn-nationals-heichelbech-12u` |

### Storm Opponents (ITAA 9U travel)
| Team | GC Team ID | Status |
|---|---|---|
| ITAA 9U Spartans | `lTxYlYLH52KU` | Active |
| MARA 9U Stingers | `VdoWDJdlCgAH` | Active |
| MILITIA 9U | `XIMp3aUceUsY` | 0 game files on disk yet |

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
| Rays-Madero jersey gap | Only 2/13 players have jersey #s in rosters.json | Run `scrape_box_scores.py --force --division Majors` if data improves |
| `date` variable not defined at line ~767 in `scrape_box_scores.py` | Pre-existing lint error, not from our changes | **FIXED** Apr 24 — added `date` to `from datetime import datetime, date` |

### Apr 24 2026 (Session 4) — Bugs 7–9 Fixed
| Bug | Details | Fix |
|---|---|---|
| **SCHEDULE_JS `final` detection broken (Wild/Storm)** | Team pages show score (`W 7-5`) not `FINAL` — 0 games found for all Wild/Storm | Added `/^[WL]\s+\d+-\d+/` score-pattern check alongside `FINAL` in both scrapers. Commit `ea04909` |
| **Team-page filenames: no date, wrong team name** | Day-abbr/number outside `<a>` tag — `currentDateTag` stayed empty; location string used as team name | Added leaf-node date detection + `is_home` field + `team_name`-based filename logic. Commit `00d8d40` |
| **`NameError: date not defined`** | `scrape_box_scores.py` crashed on first Wild/Storm roster write | Added `date` to `from datetime import datetime, date`. Commit `00d8d40` |

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

**Current version: v2.0.0** — interactive menu pipeline fully operational.

1. **Scheduled / automatic pipeline runs (target v2.1)** — Implement a `launchd`
   LaunchAgent to run the full pipeline automatically (e.g. every Sunday night) so
   PDFs are ready Monday morning without a manual trigger. Create
   `Scout_Development/launchd/com.wcwaa.scout_pipeline.plist` and add to repo
   (user installs manually via symlink to `~/Library/LaunchAgents/`). Key design
   questions to resolve:
   - Full pipeline vs. separate scrape + generate steps (for failure isolation)?
   - Sleeping laptop handling (Wake for network access? Skip + retry?)?
   - stdout/stderr destination when running headless (log file vs. macOS Console)?
   - macOS notification on completion / failure?
   - Version bump to `v2.1.0` after implementation and testing.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `0 PAs` for a team | Team name mismatch (folder vs. inning header) | Check exact spelling in game file header vs. folder name |
| `?F L?` in output | Player initials not in rosters.json | Run scrape_box_scores.py; or add to roster_additions in gen_reports.py |
| `WARNING INNING GAP` | Skipped inning in parse | Check raw game file for noise text blocking inning header match |
| `WARNING UNKNOWN` | Play outcome not in OUTCOME_TYPES | Check the play text; if valid, add to parser |
| `WARNING BOX-VERIFY` | Parsed AB/BB differs from box score | Review game file for missed plays |
| Jersey numbers missing (Majors) | rosters.json not yet populated | Run `scrape_box_scores.py --division Majors` locally |
| Jersey numbers missing (Minors) | Box scores inaccessible | Known permanent limitation |
| Session expired error | gc_session.json expired | Run `python3 gc_scraper.py --login` |
| macOS folder rename case bug | macOS case-insensitive FS | Two-step rename: `mv "old" "tmp" && mv "tmp" "New"` |

---

## Cowork Fallback (Emergency Use Only)

Cowork cannot run `gc_scraper.py` or `scrape_box_scores.py` (Playwright not installed;
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
