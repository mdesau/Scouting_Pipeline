# WCWAA Scouting Pipeline — VS Code / Claude Code Build Plan
## Transferring from Cowork to a Fully Local, Automated Pipeline

This document is written for a developer (or Claude Code) picking up this project
in VS Code. It explains what the end-goal automation looks like, what already exists,
what needs to be built or fixed, and the recommended architecture.

---

## Executive Summary — End-to-End Steps

1. **Install prerequisites** — Python 3, Playwright, ReportLab, one-time setup on Mac
2. **Log in to GameChanger** — one-time browser login saved to `gc_session.json`
3. **Scrape new game files** — `gc_scraper.py` pulls play-by-play from GC for all divisions
4. **Update rosters** — `scrape_box_scores.py` pulls player names + jersey numbers from box scores
5. **Generate PDFs** — `gen_reports.py` parses game files, computes stats, renders scouting reports
6. **One-command orchestration** — `run_weekly.sh` chains steps 3→4→5 with a single `bash` call

After each game week, the entire pipeline runs in one terminal command. No browser
interaction required once the session is saved. New PDFs appear directly in the
Google Drive folder structure.

---

## Detailed Explanation of Each Step

---

### Step 1 — Install Prerequisites

**What this is:** One-time Mac setup. Never needs to repeat unless on a new machine.

**What to run:**
```bash
pip3 install playwright reportlab --break-system-packages
playwright install chromium
```

**Why Playwright:** `gc_scraper.py` and `scrape_box_scores.py` use Playwright to
control a real Chromium browser. GameChanger is a JavaScript-heavy single-page app
— it cannot be scraped with simple HTTP requests. Playwright renders the full page
and extracts data via JavaScript just like a user would.

**Why this works locally but not in Cowork:** The Cowork sandbox blocks `web.gc.com`
on its network allowlist and doesn't persist installed packages between sessions.
Running locally sidesteps both constraints entirely.

**What Claude Code should do here:**
- Verify `python3 --version` (needs 3.9+)
- Run the two install commands above
- Verify installation: `python3 -c "from playwright.sync_api import sync_playwright; print('OK')`
- If any step fails, diagnose and fix (common issue: `pip3` vs `pip`, path issues on macOS)

---

### Step 2 — Log In to GameChanger (One-Time)

**What this is:** Playwright opens a real browser window. You log into GameChanger
manually. The session (cookies) is saved to `gc_session.json` and reused by all
future script runs.

**What to run:**
```bash
cd ~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My\ Drive/Baseball/WCWAA/2026/Spring/Scout_Development/Scripts
python3 gc_scraper.py --login
```

**When to repeat:** Only when you see a "session expired" or "not logged in" error,
typically every few weeks. Re-run `--login` to refresh.

**What Claude Code should do here:**
- Run the command above
- Confirm `gc_session.json` was created/updated
- Note: if running headless (no display), may need to add `headless=False` to the Playwright launch call so the browser window actually appears

---

### Step 3 — Scrape New Game Files (`gc_scraper.py`)

**What this script does:**
- Reads the configured division/team list from `DIVISIONS` dict in the script
- For each division, navigates to the GC schedule page
- Identifies all games marked `FINAL`
- Skips any game whose UUID already has a `.txt` or `-Reviewed.txt` file on disk
- For new games: navigates to the `/plays` URL, extracts the full play-by-play text
- Passes text through `parse_gc_text.py` to convert to WCWAA structured format
- Saves to the correct folder (`Scorebooks/` for Majors/Minors, `Games/` for Wild/Storm)

**Key file:** `Scripts/gc_scraper.py`

**How teams/divisions are configured:**
```python
DIVISIONS = {
    "Majors": {"type": "org", "org_id": "1CMI2BBazG8C", ...},
    "Minors": {"type": "org", "org_id": "GdcFopba2PbE", ...},
    "Wild":   {"type": "teams", "teams": [
        ("1yv2qtI89QSD", "2026-spring-arena-national-browning-11u", "Arena National Browning 11U"),
        ("I2XcyUwmye3p", "2026-spring-t24-garnet-11u", "T24 Garnet 11U"),
        ...
    ]},
    "Storm":  {"type": "teams", "teams": [...]},
}
```

To add a new opponent: get the team's GC URL, extract `team_id` and `slug`, add
one tuple to `"teams"` in BOTH `gc_scraper.py` AND `scrape_box_scores.py`.

**What Claude Code should build/fix here:**
- Test the script end-to-end against real GC data
- Fix any selector issues if GC has changed its DOM since the script was written
- Add `--dry-run` flag if not already present (list games found without downloading)
- Handle the case where the Playwright session opens a "verify you're human" page
- Complete T24 Garnet 11U scraping (8 remaining games — UUIDs listed in ManualGuide.md)
- Find and add QC Flight Baseball 11U `team_id` (visit their GC schedule URL)

---

### Step 4 — Update Rosters (`scrape_box_scores.py`)

**What this script does:**
- Navigates to GC box score pages for all FINAL games
- Extracts each batter's name, jersey number, and box score stats (AB, BB, SO)
- For Majors/Minors: builds `rosters.json` — one entry per player, keyed by initials
- For Wild/Storm: builds `roster.txt` per team folder
- Detects **duplicate initials** (two players sharing the same 2-char initials) and
  stores them under disambiguated 5-char keys with a `_collision_map` entry
- Writes `box_verify.json` for cross-checking parsed stats against box score data

**Why this runs every week:** Player names and jersey numbers may be missing from
early-season runs. The script is incremental — it only scrapes games not yet in
`box_verify.json`. Over the season, the roster fills in completely.

**Known limitation — Minors jerseys:** The Minors org `/box-score` pages redirect
to `/info`. Jersey numbers cannot be scraped for Minors. This is permanent until
GameChanger fixes it. First-name-only display for Minors is expected behavior.

**What Claude Code should build/fix here:**
- Test against Majors to confirm rosters.json populates correctly
- Resolve `?N P?` and `?C C?` for Cubs-Holtzer (they'll appear once this runs)
- Verify Wild/Storm `roster.txt` files are being built correctly
- Confirm `_collision_map` is written for Brian Allen / Ben Allen on Cubs-Holtzer

---

### Step 5 — Generate Scouting Reports (`gen_reports.py`)

**What this script does:**
- Loads rosters from `rosters.json` (Majors/Minors) or `roster.txt` (Wild/Storm)
- Reads the `_collision_map` if present — used to split plate appearances between
  players who share initials (e.g., Brian Allen + Ben Allen both appear as "B A")
- For Majors/Minors: pre-scans all teams to compute league-wide percentile thresholds
  for archetype labels (Power, Contact, Overmatched, Walker)
- For each team: parses all game files, computes per-batter stats, runs 4-layer
  verification, generates a multi-page PDF via ReportLab
- Renames parsed files from `.txt` to `-Reviewed.txt` as a processing flag

**Output per team:**
- 2-column player card grid (pages 1–N): spray chart, stat bars, archetype label,
  pitching approach, AVG/OBP/SLG/C%
- Summary + scouting notes page: stat table across all batters + 2-sentence notes

**What Claude Code should fix here:**
- Add `"Infield Fly"` to `OUTCOME_TYPES` (treat as flyball out — `FO`)
  In `gen_reports.py`, find the `parse_outcome()` function and add:
  `if "infield fly" in ol: return FO`
- Add the same fix to `parse_gc_text.py`
- Fix `$awyer M` — in any T24 Garnet game files, find/replace `$awyer` → `Sawyer`
  before running the parser (or add a pre-processing step in `gc_scraper.py`)

---

### Step 6 — One-Command Orchestration (`run_weekly.sh`)

**What this is:** A shell wrapper that runs steps 3→4→5 in sequence.

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "▶ Step 1/3: Scraping new games..."
python3 gc_scraper.py

echo "▶ Step 2/3: Updating rosters..."
python3 scrape_box_scores.py

echo "▶ Step 3/3: Generating PDFs..."
python3 gen_reports.py --division Majors
python3 gen_reports.py --division Minors
python3 gen_reports.py --division Wild
python3 gen_reports.py --division Storm

echo "Done. PDFs saved to Google Drive folder."
```

**File location:** `Scout_Development/Scripts/run_weekly.sh`

**Usage after each game week:**
```bash
cd ~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My\ Drive/Baseball/WCWAA/2026/Spring/Scout_Development/Scripts
bash run_weekly.sh
```

---

## Recommended Script Architecture

The project follows a **single orchestrator + component scripts** pattern.
This is already the architecture in place. Claude Code should maintain it:

```
run_weekly.sh                    ← orchestrator (shell wrapper)
│
├── gc_scraper.py                ← component: GC play-by-play scraping
│     └── imports parse_gc_text.py   ← utility: raw text → WCWAA format
│
├── scrape_box_scores.py         ← component: GC box score scraping
│
└── gen_reports.py               ← component: stat engine + PDF generation
```

**Why this architecture:**
- Each component script can be run independently for testing or partial updates
- `run_weekly.sh` is a thin wrapper — logic stays in Python, not shell
- Adding a new division or feature only requires touching the relevant component
- Claude Code can test each component in isolation before wiring everything together

**What NOT to do:**
- Don't merge the scrapers into `gen_reports.py` — they have different dependencies
  (Playwright vs. pure Python) and run at different times
- Don't build a GUI or web interface — terminal is the right interface for this

---

## What Claude Code Should Build — Prioritized Task List

### Immediate (session 1)
1. Install Playwright and ReportLab, verify imports work
2. Run `gc_scraper.py --login` — confirm session saves to `gc_session.json`
3. Run `gc_scraper.py --division Majors --check` — confirm schedule page loads and FINAL games are detected
4. Run `scrape_box_scores.py --division Majors` — confirm `rosters.json` updates (resolves `?N P?` and `?C C?`)
5. Run `gen_reports.py --division Majors --team Cubs` — confirm Brian A. / Ben A. appear as separate cards

### Short-term (sessions 2–3)
6. Run full `run_weekly.sh` — confirm end-to-end pipeline works for all 4 divisions
7. Fix `Infield Fly` → `FO` in `parse_outcome()` in both `gen_reports.py` and `parse_gc_text.py`
8. Fix `$awyer M` — add pre-processing in `gc_scraper.py` or `parse_gc_text.py` to catch names starting with `$`
9. Find QC Flight Baseball 11U `team_id` (visit their GC URL) and add to both scraper scripts
10. Complete T24 Garnet 11U — run `gc_scraper.py --team "T24 Garnet 11U"` and verify all games scraped

### Ongoing
11. After each game week: `bash run_weekly.sh`
12. If session expires: `python3 gc_scraper.py --login`
13. When new Wild/Storm opponent added: update DIVISIONS in both scraper scripts + create team folder

---

## Files Claude Code Should NOT Modify

| File | Why |
|---|---|
| `gc_session.json` | Live auth credentials — regenerated by `--login`, never edit manually |
| `Majors/Reports/rosters.json` | Managed by `scrape_box_scores.py` — manual edits get overwritten |
| `*-Reviewed.txt` game files | Already processed — parser reads them; never delete or rename manually |
| `Spring 2026 Draft Results.xlsx` | Upstream draft data — reference only, not modified by pipeline |

---

## Context on How This Was Built

This pipeline was built iteratively in Cowork (Anthropic's desktop AI tool) across
multiple sessions. The key constraints that shaped the design:

- **Cowork sandbox blocks web.gc.com** — all browser scraping had to be done either
  locally (Playwright) or via Chrome MCP (manual, token-expensive). Moving to VS Code
  with Claude Code eliminates this constraint entirely.
- **GameChanger is a SPA** — raw HTTP requests don't work. Playwright is required to
  render the page and extract data via JavaScript.
- **Play-by-play is initials-only** — "B A singles" doesn't tell you if that's Brian
  Allen or Ben Allen. The disambiguation system was built specifically for this.
- **No substitutions in WCWAA** — simplifies batting order inference significantly;
  every player who appears once appears in every inning.
- **Reverse-chronological files** — GC's default mode writes innings newest-first.
  The parser handles both directions via inning number extraction, not line order.

---

## Reference: Key Variables and Constants in gen_reports.py

| Name | Location | Purpose |
|---|---|---|
| `DIVISIONS` | top of file | Division config: paths, team lists, roster sources |
| `INNING_RE` | line ~335 | Regex matching inning headers — team name must match exactly |
| `DESC_RE` | line ~336 | Regex matching play narrative lines — first char must be capital |
| `OUTCOME_TYPES` | line ~337 | Set of valid outcome keyword strings from GC |
| `parse_outcome()` | ~line 257 | Maps play description text → outcome constant |
| `parse_game_for_team()` | ~line 344 | Core parser — returns list of PA dicts for one game |
| `_disambiguate_pas()` | ~line 180 | Splits collision-initials PAs by batting order occurrence |
| `compute_stats()` | ~line 514 | Aggregates PA dicts → per-batter stat dict |
| `get_archetype()` | ~line 662 | Assigns Approach × Result label |
| `generate_pdf()` | ~line 1198 | Renders full PDF from batter list |
| `run_league()` | ~line 1388 | Orchestrates Majors/Minors report generation |
| `run_wild()` | ~line 1509 | Orchestrates Wild/Storm report generation |
