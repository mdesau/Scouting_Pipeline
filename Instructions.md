# WCWAA 2026 Spring — Scouting Report Pipeline
## Session Kickoff Reference (AI Assistant + Local Use)

Paste this file as context at the start of every new Cowork/Claude session.
Companion file: `Scout_Development/ManualGuide.md` — step-by-step human walkthrough + VS Code onboarding prompt.

**All scripts and this file live at:**
`~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My Drive/Baseball/WCWAA/2026/Spring/Scout_Development/`

---

## Current State (April 2026)

- **Four divisions active:** Majors (11 teams), Minors (14 teams), Wild (11U travel opponents), Storm (ITAA 9U travel opponents)
- **Single unified script:** `gen_reports.py` handles all four divisions
- **Roster source:** `rosters.json` for Majors/Minors (first names + jersey numbers when scraped); `roster.txt` per team folder for Wild/Storm
- **Jersey numbers:** Fully supported in `gen_reports.py` (renders in amber on cards). Populated by running `scrape_box_scores.py` locally. Currently populated for Padres-Schick only; all other Majors/Minors teams show first names only until next local `scrape_box_scores.py` run.
- **Minors jersey limitation:** GC box score pages for Minors org redirect to `/info` — jersey numbers cannot be scraped for Minors. First-name-only display is permanent for Minors until GC fixes this.
- **PDF format:** 2-column card grid, max 3 rows/page, heat-map spray chart, summary table + scouting notes on final page. Approved and in production.
- **Unresolved players in Cubs-Holtzer:** `?N P?` and `?C C?` — initials not matching rosters.json. Fix by running `scrape_box_scores.py --division Majors` locally.

---

## Directory Structure

```
Spring/
  Scout_Development/           <- ALL scripts and docs live here
    Instructions.md            <- this file (session kickoff reference)
    ManualGuide.md             <- human walkthrough + VS Code onboarding prompt
    Scripts/
      gc_scraper.py            <- Playwright: GC schedule -> .txt game files (all 4 divisions)
      scrape_box_scores.py     <- Playwright: GC box scores -> rosters.json + roster.txt
      parse_gc_text.py         <- raw GC page text -> WCWAA .txt format (also imported by scrapers)
      gen_reports.py           <- stat engine + ReportLab PDF generator (all 4 divisions)
      run_weekly.sh            <- one-command wrapper: scrape -> rosters -> all PDFs
      scrape_storm.py          <- legacy bootstrap only (early Spartans games; superseded)
      gc_session.json          <- saved GC login session (Playwright auth cookie)
      archetype_reference.txt  <- archetype system design notes
    Logs/
      gen_reports_YYYYMMDD_HHMMSS.log
      gc_scraper_YYYYMMDD_HHMMSS.log
      scrape_box_scores_YYYYMMDD_HHMMSS.log

  Majors/
    Reports/
      Scorebooks/              <- .txt and -Reviewed.txt play-by-play files
      Scouting_Reports/        <- output PDFs
      rosters.json             <- first names + jersey #s (run scrape_box_scores.py locally)
      box_verify.json          <- per-game AB/BB/SO cross-check

  Minors/
    Reports/
      Scorebooks/
      Scouting_Reports/
      rosters.json             <- first names only (jerseys unavailable -- see Known Limitations)

  Wild/
    [TeamName]/                <- folder name MUST exactly match GC inning header team name
      Games/                   <- .txt and -Reviewed.txt play-by-play files
      roster.txt               <- optional: "INITIALS, Display Name #jersey"
      [TeamName]_Scout_2026.pdf

  Storm/
    [TeamName]/
      Games/
      roster.txt
      [TeamName]_Scout_2026.pdf
```

---

## Weekly Workflow (LOCAL -- run on your Mac)

**One command covers everything:**
```bash
cd ~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My\ Drive/Baseball/WCWAA/2026/Spring/Scout_Development/Scripts
bash run_weekly.sh
```

**Or step by step:**
```bash
python3 gc_scraper.py                          # Step 1: pull all new FINAL game files
python3 scrape_box_scores.py                   # Step 2: update rosters + jersey numbers
python3 gen_reports.py --division Majors       # Step 3: regenerate PDFs
python3 gen_reports.py --division Minors
python3 gen_reports.py --division Wild
python3 gen_reports.py --division Storm
```

> `gc_scraper.py` skips games that already have a `.txt` or `-Reviewed.txt` file -- always safe to re-run.
> Use `--check` to preview without writing files: `python3 gc_scraper.py --check`

---

## Common Commands

```bash
# Generate one team
python3 gen_reports.py --division Majors --team Cubs
python3 gen_reports.py --division Minors --team Rangers
python3 gen_reports.py --division Wild --team "T24 Garnet 11U"
python3 gen_reports.py --division Storm --team "MILITIA 9U"

# Scrape one division or team only
python3 gc_scraper.py --division Storm
python3 gc_scraper.py --team "MARA 9U Stingers"

# Force re-scrape (ignores existing files)
python3 gc_scraper.py --force

# First-time or session-expired login
python3 gc_scraper.py --login
```

---

## Adding a New Wild or Storm Opponent

1. Go to the opponent's schedule page on GameChanger -- copy the URL:
   `https://web.gc.com/teams/{team_id}/{slug}/schedule`
2. Open `Scout_Development/Scripts/gc_scraper.py`
3. Find the `"Wild"` or `"Storm"` section in `DIVISIONS` (around line 115)
4. Add one line to the `"teams"` list:
   ```python
   ("team_id_from_url", "slug-from-url", "Exact Team Name"),
   ```
5. Make the same addition in `scrape_box_scores.py` (same section, same format)
6. Create the folder: `Wild/[Exact Team Name]/Games/` or `Storm/[Exact Team Name]/Games/`
7. The folder name **must exactly match** the team name in GC inning headers (check a parsed game file to confirm spelling)

---

## Division Reference

| Division | GC URL type | Game file folder | Roster source | PDF output |
|---|---|---|---|---|
| Majors | `org/1CMI2BBazG8C/schedule/[UUID]/plays` | `Majors/Reports/Scorebooks/` | `rosters.json` | `Majors/Reports/Scouting_Reports/` |
| Minors | `org/GdcFopba2PbE/schedule/[UUID]/plays` | `Minors/Reports/Scorebooks/` | `rosters.json` (names only) | `Minors/Reports/Scouting_Reports/` |
| Wild | `teams/[ID]/[slug]/schedule/[UUID]/plays` | `Wild/[TeamName]/Games/` | `roster.txt` | `Wild/[TeamName]/` |
| Storm | `teams/[ID]/[slug]/schedule/[UUID]/plays` | `Storm/[TeamName]/Games/` | `roster.txt` | `Storm/[TeamName]/` |

---

## Teams Reference (Spring 2026)

### Majors (11 teams)
| Team | Coach | Key used in filenames |
|---|---|---|
| Guardians | Esau | Guardians-Esau |
| Royals | Hall | Royals-Hall |
| Diamondbacks | Vandiford | Diamondbacks-Vandiford |
| Marlins | McLendon | Marlins-McLendon |
| Dodgers | Pearson | Dodgers-Pearson |
| A's | Blanco | As-Blanco |
| Braves | Rue | Braves-Rue |
| Twins | Ewart | Twins-Ewart |
| Padres | Schick | Padres-Schick  <- only team with jersey #s currently |
| Cubs | Holtzer | Cubs-Holtzer |
| Rays | Madero | Rays-Madero |

> CSV/rosters.json store Diamondbacks as `Dbacks` and A's as `As` -- `gen_reports.py` handles this via `csv_overrides`. No manual action needed.

### Minors (14 teams)
| Team | Coach | Key |
|---|---|---|
| Astros | Barbour | Astros-Barbour |
| Dodgers | Winchester | Dodgers-Winchester |
| Padres | Midkiff | Padres-Midkiff |
| Reds | Naturale | Reds-Naturale |
| Rangers | Leonard | Rangers-Leonard |
| Yankees | DePasquale | Yankees-DePasquale |
| Marlins | Eberlin | Marlins-Eberlin |
| Guardians | Plunkett | Guardians-Plunkett |
| Angels | Casper | Angels-Casper |
| Braves | Brooks | Braves-Brooks |
| Cubs | Verlinde | Cubs-Verlinde |
| Brewers | Linnenkohl | Brewers-Linnenkohl |
| Rays | Pearson | Rays-Pearson |
| Mets | Hornung | Mets-Hornung |

> `Mets-Hornung` has a manual `roster_additions` entry in `gen_reports.py` for post-draft player `B A` -> Beau Amerine.

### Wild Opponents (11U travel)
| Team | GC Team ID | Slug | Status |
|---|---|---|---|
| Arena National Browning 11U | `1yv2qtI89QSD` | `2026-spring-arena-national-browning-11u` | Active -- games scraped |
| QC Flight Baseball 11U | *(find URL)* | `2026-spring-qc-flight-baseball-11u` | Games scraped; team_id needed in script |
| South Charlotte Panthers 11U | `Kih0oavXNZB3` | `2026-spring-south-charlotte-panthers-11u` | Active -- games scraped |
| Weddington Wild 11U | `Ye94sB963tUX` | `2026-spring-weddington-wild-11u` | Active -- games scraped |
| T24 Garnet 11U | `I2XcyUwmye3p` | `2026-spring-t24-garnet-11u` | In progress -- Spring 2026 scraping underway |

### Storm Opponents (ITAA 9U travel)
| Team | GC Team ID | Slug | Status |
|---|---|---|---|
| ITAA 9U Spartans | `lTxYlYLH52KU` | `2026-spring-itaa-9u-spartans` | Active (home team) |
| MARA 9U Stingers | `VdoWDJdlCgAH` | `2026-spring-mara-9u-stingers` | Report built |
| MILITIA 9U | `XIMp3aUceUsY` | `2026-spring-militia-9u` | In progress -- Spring 2026 scraping underway |
| Crushers White 10U | *(team-based)* | -- | Folder exists in Storm/ |
| 9u Challenge | *(team-based)* | -- | Folder exists in Storm/ |

---

## Running in Cowork (No Playwright Available)

**The constraint:** `gc_scraper.py` and `scrape_box_scores.py` use Playwright (a Python browser automation library). Playwright is not installed in the Cowork sandbox and `web.gc.com` is not on its network allowlist even if installed. These scripts **must be run locally on your Mac.**

**`gen_reports.py` works fine in Cowork** -- no Playwright dependency. Use Cowork to generate/regenerate PDFs once game files are already in place.

**Recommended split:**
- **Local Mac:** `run_weekly.sh` after each game week (scrape + rosters + PDFs)
- **Cowork:** On-demand PDF generation, debugging, Instructions/ManualGuide updates, one-off tasks

**Emergency Cowork scraping** (rare, expensive in tokens):
Use the Chrome MCP tool to navigate to the `/plays` page, extract text via `document.body.innerText` in JS chunks, write to `outputs/raw_TEAM_N.txt`, then convert via `parse_raw_helper.py`. Budget ~10 tool calls per game. Do not attempt more than 3-4 new games per session.

**`parse_raw_helper.py`** (keep in outputs folder for Cowork fallback):
```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/sessions/fervent-sweet-albattani/mnt/Spring/Scout_Development/Scripts')
from parse_gc_text import parse_gc_raw
from pathlib import Path
raw_file  = Path(sys.argv[1])
out_path  = Path(sys.argv[2])
game_url  = sys.argv[3]
game_date = sys.argv[4]
raw_text  = raw_file.read_text(encoding='utf-8')
converted = parse_gc_raw(raw_text, game_url=game_url, game_date=game_date)
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(converted, encoding='utf-8')
print(f"OK -> {out_path}")
```

---

## File Naming Conventions

```
Game files:
  Majors/Minors:  MonDD-AwayTeam-CoachLast_vs_HomeTeam-CoachLast.txt
  Wild/Storm:     MonDD-AwayTeam_vs_HomeTeam.txt

After gen_reports.py processes a file:
  MonDD-Away_vs_Home.txt  ->  MonDD-Away_vs_Home-Reviewed.txt
  (Both .txt and -Reviewed.txt are parsed every run -- -Reviewed is a flag, not an exclusion)

Output PDFs:
  Majors/Minors:  TeamName_CoachLast-Scout_2026.pdf   e.g. Cubs_Holtzer-Scout_2026.pdf
  Wild/Storm:     TeamName_Scout_2026.pdf              e.g. MILITIA_9U_Scout_2026.pdf
```

---

## Known Limitations

| Issue | Detail |
|---|---|
| Minors jersey numbers unavailable | Minors org `/box-score` pages redirect to `/info`. First-name-only display is permanent until GC fixes this. |
| QC Flight Baseball 11U team_id missing | Game files exist but team_id not confirmed. Find by visiting their GC schedule page and reading the URL. |
| SS spray chart zone always 0 | Parser maps both `shortstop` and `third baseman` plays to zone `3B`. SS sector on spray chart will always show 0 BIP. |
| macOS folder rename case sensitivity | macOS is case-insensitive. Use two-step rename for case-only changes: `mv "old" "tmp" && mv "tmp" "New"` |
| gc_session.json expiry | Playwright login cookie expires periodically. Run `python3 gc_scraper.py --login` to refresh. |
| Cubs-Holtzer ?N P? and ?C C? | Two players unresolved in rosters.json. Fix: run `scrape_box_scores.py --division Majors` locally. |
| Infield Fly not in OUTCOME_TYPES | Appears in T24 Garnet 11U games. Logs as `warning UNKNOWN`. Treat as fly ball out -- add to OUTCOME_TYPES in parse_gc_text.py/gen_reports.py. |
| $awyer M in T24 Garnet games | Player name starts with `$` -- DESC_RE won't match. Fix: find/replace `$awyer` -> `Sawyer` in raw game files before running parse_gc_text.py. |

---

## Pipeline Mechanics (Internal Reference)

### Game File Format (after parse_gc_text.py)
```
GAME: Mon Mar 15 | https://web.gc.com/teams/[ID]/[slug]/schedule/[UUID]/plays

===Bottom 3rd - T24 Garnet 11U===
Walk | | Ball 1, Ball 2, Ball 3, Ball 4.
R V walks, P W pitching.
Ground Out | 1 Out | Strike 1 looking, In play.
T M grounds out to shortstop.
===Top 4th - Dilworth 11U - Navy===
...
```

`gen_reports.py` parses only the **target team's half-innings**. `INNING_RE` does exact string matching -- folder name must match perfectly.

### Parser Notes
- `DESC_RE` matches narrative lines: `^([A-Z][a-z]?) ([A-Z][a-z]*) (.+)\.$`
- First character must be a capital letter -- names starting with `$` (e.g. `$awyer`) won't match
- Substitution lines (`"C M in for pitcher K R"`) are skipped via `rest.startswith("in for")` guard
- Scorebooks may be in reverse-chronological order (GC default); parser uses inning numbers from headers

### Stat Formulas
| Stat | Formula |
|---|---|
| PA | All plate appearances |
| AB | PA - (BB + HBP + SF + SB) |
| AVG | H / AB |
| OBP | (H + BB + HBP) / (AB + BB + HBP) |
| SLG | TB / AB |
| C% | (AB - K_total) / AB |
| GB% | Ground ball BIP / total BIP |
| FB+LD% | (Fly ball + line drive BIP) / total BIP |
| SM% | Swing-and-miss / total swings |
| CStr% | Called strikes / total pitches |
| FPT% | First-pitch takes / (takes + swings on first pitch) |

### Archetype System (2-word label per card)
**Approach x Result** -- shown on each player card. Cards with 5-9 PA show `*` suffix; fewer than 5 PA show `--`.

**Approach:** Aggressive (early swinger, FPT% < 40% or high SM%) | Disciplined (OBP-AVG >= .060) | Passive (takes too much, FPT% > 70%)
**Result:** Walker (BB-driven OBP, top-33% BB/PA) | Overmatched (low C% or high SM%) | Power (top-33% SLG + ISO >= .120) | Contact (default)

Majors/Minors thresholds: league-wide percentiles computed at script start.
Wild/Storm thresholds: fixed (SLG top-33 = .450, C% bottom-33 = .500, BB/PA top-33 = .200).

### Pitching Approach Matrix
| Archetype | Recommendation |
|---|---|
| Aggressive Power/Contact | Edges + Mix Speed |
| Aggressive Overmatched | Climb the Ladder |
| Aggressive Walker | Outside - In |
| Disciplined Power/Contact | Keep Mixing |
| Disciplined Overmatched/Walker | Attack the Zone |
| Passive Power/Contact | Attack & Expand |
| Passive Overmatched/Walker | Attack the Zone |

### Four-Layer Verification (runs automatically on every gen_reports.py call)
1. **Inning continuity** -- checks for skipped innings per game
2. **Unknown outcomes** -- flags unrecognized play descriptions
3. **Batting order** -- PA counts must be consistent with lineup order
4. **Box score cross-check** -- parsed AB/BB vs. box score (requires `box_verify.json`)

All warnings print as `warning` lines and are saved to the log file. They do NOT stop PDF generation.

### Troubleshooting Quick Reference
| Symptom | Likely Cause | Fix |
|---|---|---|
| `0 PAs` for a team | Team name mismatch (folder vs. inning header) | Check exact spelling; macOS two-step rename for case changes |
| `?F L?` in output | Initials not in rosters.json or CSV | Run `scrape_box_scores.py`; or add to `roster_additions` in gen_reports.py |
| `warning INNING GAP` | Half-inning skipped in parse | Check raw game file for noise text before first play in that inning |
| `warning UNKNOWN` | Outcome type not in OUTCOME_TYPES | Check the play text; add to parser if valid outcome |
| `warning BOX-VERIFY` | Parsed AB/BB differs from box score | Review game file for missed plays |
| Missing jersey numbers (Majors) | rosters.json not yet populated | Run `scrape_box_scores.py --division Majors` locally |
| Missing jersey numbers (Minors) | Box scores inaccessible | Known permanent limitation |
| Session expired | `gc_session.json` expired | Run `python3 gc_scraper.py --login` |
