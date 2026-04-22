# WCWAA 2026 Spring — Scouting Report Pipeline
## Claude Code Context File

This file is the authoritative reference for the WCWAA scouting report pipeline.
Load it at the start of every new Claude Code session. It covers every design
decision, known bug, and operational detail accumulated across the full build
history of this project.

**Root directory (all paths relative to this):**
`~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My Drive/Baseball/WCWAA/2026/Spring/`

**Companion file:** `Scout_Development/ManualGuide.md` — step-by-step human walkthrough for manual game file creation.

**Best practices prompt:** When starting a new session, the user may paste their "Code Mentor" prompt which defines conventions for debugging, git hygiene, error handling, and code style. Follow those guidelines throughout.

---

## Development Environment

- **Python 3.9.6** (macOS system Python)
- **Virtual environment:** `Scout_Development/venv/` — always activate before running scripts
- **Key packages:** Playwright 1.58.0, Chromium 145, ReportLab 4.4.10
- **Frozen deps:** `requirements.txt` in project root
- **Git:** Local repo, 5 commits on `main`, tagged `v0.1.0` at initial setup
- **No remote yet** — user plans a private GitHub repo eventually

```
854f25c  fix: add try/except error handling around division and team loops
c250384  feat: add DEBUG_CONFIG sections + --verbose flag to all 3 main scripts
e803f4a  fix: two bugs in scrape_box_scores.py roster building
7dc194f  fix: repair SCHEDULE_JS date+team parsing for GC's current DOM
8b082f9  (tag: v0.1.0) feat: initial project setup v0.1.0
```

### Scripts Overview (line counts as of Apr 22, 2026)
| Script | Lines | Role | Has --verbose | Has DEBUG_CONFIG | Has try/except |
|---|---|---|---|---|---|
| `gc_scraper.py` | ~535 | Playwright: GC schedule → .txt game files | ✅ | ✅ | ✅ |
| `scrape_box_scores.py` | ~810 | Playwright: GC box scores → rosters.json | ✅ | ✅ | — |
| `gen_reports.py` | ~1755 | Stat engine + PDF generator | ✅ | ✅ | ✅ (run_wild) |
| `parse_gc_text.py` | ~260 | Raw GC text → WCWAA format (utility) | — | — | — |
| `run_weekly.sh` | ~86 | Shell orchestrator | — | — | — |

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
  Scout_Development/
    CLAUDE.md                  ← this file
    Instructions.md            ← older version (superseded by CLAUDE.md)
    ManualGuide.md             ← human walkthrough for manual game file creation
    Scripts/
      gc_scraper.py            ← Playwright: GC schedule pages → .txt game files
      scrape_box_scores.py     ← Playwright: GC box scores → rosters.json + roster.txt
      parse_gc_text.py         ← converts raw GC page text → WCWAA .txt format
      gen_reports.py           ← stat engine + ReportLab PDF generator (all 4 divisions)
      run_weekly.sh            ← one-command wrapper: steps 1→2→3 in sequence
      gc_session.json          ← saved Playwright GC login session (auth cookies)
      archetype_reference.txt  ← archetype system design notes
    Logs/
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
bash run_weekly.sh
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
(`run_weekly.sh` activates the venv automatically.)

Then run login once to save session:
```bash
cd .../Scout_Development/Scripts
python3 gc_scraper.py --login
```

---

## How the Pipeline Works

### Step 1 — gc_scraper.py (Playwright scraper)
- Navigates to GC schedule pages for all configured teams/orgs
- Identifies all FINAL games not yet on disk
- Navigates to the `/plays` page for each game
- Extracts play-by-play text via `page.inner_text()` or JS DOM traversal
- Passes raw text through `parse_gc_text.py` to produce a WCWAA-structured `.txt` file
- Saves to the correct `Scorebooks/` or `Games/` folder

### Step 2 — scrape_box_scores.py (Playwright scraper)
- Navigates to `/box-score` pages for all FINAL games
- Extracts batter names, jersey numbers, and AB/BB/SO stats via JS
- Builds/updates `rosters.json` for Majors and Minors (keyed by team name)
- Builds/updates `roster.txt` for Wild and Storm (per-team flat files)
- Writes `box_verify.json` for Layer 4 cross-check in gen_reports.py
- Detects **duplicate initials** automatically (e.g. Brian Allen + Ben Allen both → "B A"):
  stores both under 3-char disambiguation keys ("Bri A", "Ben A") and writes a
  `_collision_map` entry so gen_reports.py can split their plate appearances correctly

### Step 3 — gen_reports.py (stat engine + PDF generator)
- Loads rosters from `rosters.json` (Majors/Minors) or `roster.txt` (Wild/Storm)
- Reads all `.txt` and `-Reviewed.txt` game files for each team
- Parses each file via `INNING_RE` + `DESC_RE` to extract plate appearances
- Runs 4-layer verification on each game (see Verification section)
- Computes per-batter stats: PA, AB, H, BB, HBP, TB, K, BIP, GB%, FB%, SM%, CStr%, FPT%
- Assigns each batter an archetype label (Approach × Result)
- Generates a multi-page PDF: player cards (pages 1-N) + summary table + scouting notes

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

## Unresolved Players — ?N P? and ?C C? in Cubs-Holtzer

Two Cubs-Holtzer players appear across multiple games with initials `N P` and `C C`
but are not in `rosters.json`. They show as `?N P?` and `?C C?` on the scouting report.

**Fix:** Run `scrape_box_scores.py --division Majors` locally. The box score scraper
will pick them up from the GC box score pages and populate `rosters.json`.
Do NOT use the draft CSV as a fallback — box score is the authoritative source.

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
| Padres-Schick | Only team with jersey #s currently in rosters.json |
| Cubs-Holtzer | Has B A collision map (Brian + Ben Allen) + unresolved N P, C C |
| Rays-Madero | |

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
| T24 Garnet 11U | `I2XcyUwmye3p` | In progress — scraping underway |
| QC Flight Baseball 11U | *(find URL)* | Games exist; team_id missing from script |

### Storm Opponents (ITAA 9U travel)
| Team | GC Team ID | Status |
|---|---|---|
| ITAA 9U Spartans | `lTxYlYLH52KU` | Active |
| MARA 9U Stingers | `VdoWDJdlCgAH` | Active |
| MILITIA 9U | `XIMp3aUceUsY` | In progress |

---

## Known Issues / Pending Work

### High Priority — Fix Before Next Weekly Run
| Issue | Details | Fix |
|---|---|---|
| Minors scorebook files missing for away games | gen_reports.py looks for each game in the team's own Scorebooks/ folder, but GC scraper saves each game only once (under home team?). Many teams show `SKIP ... [Errno 2]` and only process 1-3 of 7 games. **This is the biggest data gap.** | Investigate: does gc_scraper save duplicates? Or does gen_reports need to search ALL Scorebooks/ files? Check how Majors handles this — Majors worked fine for all 11 teams. |
| BOX-VERIFY warnings widespread in Minors | Nearly every Minors team shows parsed AB/BB lower than box score. Likely caused by the missing-file issue above (fewer games parsed = fewer PAs). | Fix the missing-file issue first, then re-verify. |

### Medium Priority — Quality Improvements
| Issue | Details | Fix |
|---|---|---|
| `Infield Fly` not in OUTCOME_TYPES | Parsed as unknown outcome | Add `"Infield Fly": "FO"` to `OUTCOME_TYPES` in `gen_reports.py` and `parse_gc_text.py` |
| `$awyer M` in T24 Garnet games | Dollar sign in player name from GC | Find/replace `$awyer` → `Sawyer` in raw game files |
| QC Flight Baseball 11U team_id missing | Can't scrape games | Visit GC schedule URL, copy team_id, add to both scrapers |
| T24 Garnet 11U scraping incomplete | 0 games scraped (page timeout during pipeline run) | May need retry or manual scrape; 8 games in ManualGuide.md |
| QC Flight roster.txt Google Drive timeout | `[Errno 60]` on file read | Google Drive sync issue — try re-syncing or opening file in browser first |

### Low Priority / Cosmetic
| Issue | Details | Fix |
|---|---|---|
| Minors jersey numbers unavailable | GC box score pages for Minors org redirect to /info | Permanent — no fix available |
| SS spray chart zone always 0 | Parser maps both SS and 3B to zone "3B" | Cosmetic only |
| `?N P?` and `?C C?` in Cubs-Holtzer | Players not in rosters.json | Run `scrape_box_scores.py --division Majors` (may already be fixed) |
| `date` variable not defined at line ~767 in `scrape_box_scores.py` | Pre-existing lint error, not from our changes | Check scope; likely needs `date` passed into function |

---

## Latest Pipeline Run Results (Apr 22, 2026)

### Majors (11 teams) ✅
- All 11 teams generated PDFs successfully
- 35 games total, all processed
- No missing files, no errors

### Minors (14 teams) ⚠️
- All 14 PDFs generated, but many teams only processed 1-3 of ~7 games
- Rays-Pearson: 0 PAs (all 7 files SKIP), Mets-Hornung: 0 PAs (all 7 files SKIP)
- Root cause: game files exist in other teams' Scorebooks/ folders but not duplicated
- BOX-VERIFY warnings are a downstream symptom of this

### Wild (5 teams) — 3/5 ✅
- Arena National Browning 11U: 9 games, 212 PAs ✅
- South Charlotte Panthers 11U: 8 games, 194 PAs ✅
- Weddington Wild 11U: 11 games, 284 PAs ✅
- QC Flight Baseball 11U: ❌ Google Drive timeout (`[Errno 60]`)
- T24 Garnet 11U: 0 game files scraped (page timeout during gc_scraper run)

### Storm
- No FINAL games yet this season

---

## Next Session Priorities

**Read these files first:** `CLAUDE.md` (this file), `CHANGELOG.md`, `VSCODE_PLAN.md`

1. **Fix Minors missing-file issue** — This is the #1 priority. Investigate why Minors
   teams can't find away-game scorebooks. Compare with how Majors handles it (Majors
   works correctly). The fix likely involves how gen_reports.py resolves file paths.

2. **Infield Fly → FO** — Quick fix in both `gen_reports.py` and `parse_gc_text.py`

3. **QC Flight team_id** — Find the GC URL, add to both scrapers

4. **T24 Garnet retry** — Re-run `gc_scraper.py --division Wild` to see if the
   timeout was transient

5. **$awyer M fix** — Sed/replace in T24 Garnet game files

6. **Consider v0.2.0 tag** once Minors is fully working

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
