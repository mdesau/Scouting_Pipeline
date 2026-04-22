# WCWAA Scouting Report — Manual Generation Guide
### For use when working locally in VS Code or when Cowork context is unavailable

**Who this is for:** Someone comfortable opening a terminal and running a command, but not a professional developer. You do not need to understand the code — just follow the steps.

---

## Scripts at a Glance

All five scripts live at:
```
Spring/Development/Scripts/
```

```
┌──────────────────────────┬──────────────────────────────────────────┬──────────────────────────────────────────────┬──────────────────────────┬──────────────────────────────────────────┐
│ Script                   │ What it does                             │ Inputs                                       │ Outputs                  │ When to run                              │
├──────────────────────────┼──────────────────────────────────────────┼──────────────────────────────────────────────┼──────────────────────────┼──────────────────────────────────────────┤
│ gc_scraper.py            │ Logs into GameChanger via Playwright,    │ gc_session.json (saved login),               │ .txt game files in the   │ After each game week to pull new         │
│                          │ walks every team's schedule, pulls       │ DIVISIONS config inside the script           │ correct Scorebooks/ or   │ play-by-play from GameChanger. Run        │
│                          │ play-by-play from /plays pages, converts │                                              │ Games/ folder            │ --login once, then just run it.          │
│                          │ via parse_gc_raw(), saves .txt files.    │                                              │                          │                                          │
│                          │ Covers all 4 divisions. Skips games      │                                              │                          │                                          │
│                          │ already on disk (safe to re-run).        │                                              │                          │                                          │
├──────────────────────────┼──────────────────────────────────────────┼──────────────────────────────────────────────┼──────────────────────────┼──────────────────────────────────────────┤
│ scrape_box_scores.py     │ Scrapes /box-score pages for Majors and  │ gc_session.json (saved login),               │ rosters.json and         │ Run after gc_scraper.py to get first     │
│                          │ Minors (org-based) and team-based box    │ DIVISIONS config inside the script           │ box_verify.json per      │ names + jersey numbers before running    │
│                          │ scores for Storm (team-based). Builds    │                                              │ division. For Storm/Wild,│ gen_reports.py. Only needed for          │
│                          │ rosters.json (first names + jersey #s)   │                                              │ writes roster.txt per    │ Majors/Minors; Storm/Wild use roster.txt.│
│                          │ and box_verify.json (PA cross-check).    │                                              │ team folder.             │                                          │
├──────────────────────────┼──────────────────────────────────────────┼──────────────────────────────────────────────┼──────────────────────────┼──────────────────────────────────────────┤
│ parse_gc_text.py         │ Converts raw GameChanger page text (from │ raw .txt (browser copy or Cowork             │ Structured .txt game     │ Manual fallback: when you have a raw     │
│                          │ a browser copy/download) into structured │ get_page_text output)                        │ file in WCWAA format     │ game file but haven't run gc_scraper.py. │
│                          │ WCWAA format with ===Half Nth - Team===  │                                              │ with inning headers      │ Also imported by gc_scraper.py and       │
│                          │ headers. Also verifies inning count.     │                                              │                          │ scrape_storm.py (they call it directly). │
│                          │ If output path omitted, auto-names file. │                                              │                          │                                          │
├──────────────────────────┼──────────────────────────────────────────┼──────────────────────────────────────────────┼──────────────────────────┼──────────────────────────────────────────┤
│ gen_reports.py           │ Main stat engine + PDF generator.        │ .txt game files in Scorebooks/ or Games/,    │ Scouting report PDF in   │ Run after you have game files in place   │
│                          │ Parses all .txt game files for each      │ rosters.json or CSV (Majors/Minors),         │ Scouting_Reports/ (Maj/  │ (and ideally after scrape_box_scores.py  │
│                          │ team, computes stats (AVG/OBP/SLG/C%/   │ roster.txt (Wild/Storm)                      │ Min) or team folder      │ for Majors/Minors). Handles all 4        │
│                          │ SM%/FPT%/GB%/FB+LD%), assigns archetypes,│                                              │ (Wild/Storm)             │ divisions. Renames parsed files to       │
│                          │ generates spray charts, builds 3-page    │                                              │                          │ -Reviewed.txt when done.                 │
│                          │ (or more) PDF. Runs 4-layer verification.│                                              │                          │                                          │
├──────────────────────────┼──────────────────────────────────────────┼──────────────────────────────────────────────┼──────────────────────────┼──────────────────────────────────────────┤
│ scrape_storm.py          │ Legacy bootstrap script. Reads raw page- │ Raw .txt files in /tmp/storm_raw/ named      │ .txt game files in       │ Only needed if you have raw GC text      │
│                          │ text dumps from /tmp/storm_raw/ and      │ g1.txt, g2.txt, ... per hardcoded GAME_MAP   │ Storm/ITAA 9U Spartans/  │ files that predate gc_scraper.py setup.  │
│                          │ converts them to structured game files   │ in the script                                │ Games/                   │ For new games, use gc_scraper.py instead.│
│                          │ for the ITAA 9U Spartans only. Used to  │                                              │                          │                                          │
│                          │ bootstrap Spartans games before automated│                                              │                          │                                          │
│                          │ scraper was set up. Superseded for new   │                                              │                          │                                          │
│                          │ games by gc_scraper.py.                  │                                              │                          │                                          │
└──────────────────────────┴──────────────────────────────────────────┴──────────────────────────────────────────────┴──────────────────────────┴──────────────────────────────────────────┘
```

**Pipeline position summary:**
```
gc_scraper.py → (Majors/Minors: scrape_box_scores.py) → gen_reports.py → PDF

parse_gc_text.py  ← imported by gc_scraper.py and scrape_storm.py; also standalone fallback
scrape_storm.py   ← legacy only; not part of normal workflow
```

---

## Pipeline Overview

Every scouting report — whether Majors, Minors, Wild, or Storm — follows the **same three-stage pipeline**:

```
Stage 1: FIND            Stage 2: EXTRACT & SAVE         Stage 3a (Maj/Min): ROSTER    Stage 3b: GENERATE
─────────────────        ──────────────────────────       ─────────────────────────────  ──────────────────
Find the game      →     Pull play-by-play text     →    scrape_box_scores.py builds  → Run gen_reports.py
on GameChanger           from GameChanger and             rosters.json (first names +    to compute stats
                         save as a .txt file via           jersey #s) from box scores.   and build the PDF
                         gc_scraper.py (automated)         Skip for Wild/Storm.
                         or manual browser method
```

**Stage 3a only applies to Majors and Minors.** Wild and Storm use `roster.txt` files per team folder — these are built automatically by `scrape_box_scores.py` or can be edited manually.

---

## Division Reference

| Division | GameChanger URL type | Output folder (under Spring/) |
|---|---|---|
| Majors | `web.gc.com/organizations/1CMI2BBazG8C/schedule/[UUID]/plays` | `Majors/Reports/Scorebooks/` |
| Minors | `web.gc.com/organizations/GdcFopba2PbE/schedule/[UUID]/plays` | `Minors/Reports/Scorebooks/` |
| Wild | `web.gc.com/teams/[TEAM-ID]/[slug]/schedule/[UUID]/plays` | `Wild/[TeamName]/Games/` |
| Storm (ITAA own schedule) | `web.gc.com/teams/lTxYlYLH52KU/2026-spring-itaa-9u-spartans/schedule` | — use to find game UUIDs |
| Storm (opponent teams) | `web.gc.com/teams/[OPP-TEAM-ID]/[slug]/schedule/[UUID]/plays` | `Storm/[OpponentTeamName]/Games/` |

> **Storm scouting reports are built on opponents.** You navigate to the *opponent team's* schedule page (not the ITAA Spartans page) to pull their play-by-play. The ITAA schedule page is useful to confirm which opponents you've played, but the play-by-play files live under `Storm/[OpponentTeamName]/Games/`.

> **How to find a game UUID:** Go to the team or org schedule page on GameChanger, click on a completed game, and look at the URL. The UUID is the long string of letters and numbers just before `/plays`.

> **Minors box score note:** The Minors org (`GdcFopba2PbE`) does NOT expose `/box-score` pages — navigating to one redirects to `/info`. `scrape_box_scores.py` cannot currently build `rosters.json` for Minors. Minors reports fall back to last-initial-only names from the CSV. This is a known limitation.

---

## One-Time Setup

You only need to do this once.

### Step 1 — Confirm Python 3 is installed

Open **Terminal** (press `Cmd + Space`, type "Terminal", press Enter).

```bash
python3 --version
```

You should see something like `Python 3.11.4`. If you get "command not found", download Python from [python.org](https://www.python.org/downloads/).

### Step 2 — Install required libraries

```bash
pip3 install reportlab playwright --break-system-packages
playwright install chromium
```

The `playwright install chromium` step downloads a browser (~150 MB) and takes a minute. You only do this once.

### Step 3 — Navigate to your Scripts folder

Your scripts live at:
```
~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My Drive/Baseball/WCWAA/2026/Spring/Development/Scripts/
```

To navigate there in Terminal:
```bash
cd ~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My\ Drive/Baseball/WCWAA/2026/Spring/Development/Scripts
```

> **Shortcut:** Type `cd ` (with a space), then drag the Scripts folder from Finder into the Terminal window. It will auto-fill the path.

Confirm it worked:
```bash
ls
```
You should see five files: `gen_reports.py`, `parse_gc_text.py`, `scrape_storm.py`, `gc_scraper.py`, `scrape_box_scores.py` (plus `archetype_reference.txt` and `Bugs_List.txt`).

### Step 4 — Log in to GameChanger (one time only)

This saves your GameChanger session so the scraper can run headlessly in the future:

```bash
python3 gc_scraper.py --login
```

A Chrome browser window will open. Log in to GameChanger normally. Once you can see your teams/schedule, come back to Terminal and press Enter. Your session is saved to `gc_session.json` in the Scripts folder — future runs use it automatically without opening a browser.

---

## Stage 2 — Get Games into the System

### Option A: Automated Scraper (recommended)

From the Scripts folder in Terminal:

```bash
# Scrape all new FINAL games across all divisions
python3 gc_scraper.py

# Scrape one division only
python3 gc_scraper.py --division Majors
python3 gc_scraper.py --division Storm

# Scrape games for one team only
python3 gc_scraper.py --team "Braves-Rue"
python3 gc_scraper.py --team "ITAA 9U Spartans"

# Force re-scrape even if file already exists
python3 gc_scraper.py --force
```

The scraper will:
1. Load the schedule page for each division
2. Find every game marked FINAL
3. Skip any game that already has a `.txt` file (so running it repeatedly is safe)
4. Navigate to each new game's `/plays` page, extract the text, convert it, and save it to the right folder automatically

Expected output:
```
Division: Majors
  Loading: https://web.gc.com/organizations/1CMI2BBazG8C/schedule
  12 FINAL games found
  [skip] Mar15-Braves-Rue_vs_Guardians-Esau.txt
  Scraping Apr06-Cubs-Holtzer vs Rays-Madero ... OK → Apr06-Cubs-Holtzer_vs_Rays-Madero.txt
  ...
Done.  Scraped: 3  Skipped: 9  Failed: 0
```

Logs are saved to `Development/Logs/gc_scraper_YYYYMMDD_HHMMSS.log`.

**Adding a new Wild or Storm opponent team to the scraper:**

Open `gc_scraper.py` in VS Code. Find the `"Wild"` or `"Storm"` section in `DIVISIONS` (around line 95). Add an entry to the `"teams"` list:

```python
"Storm": {
    "teams": [
        ("lTxYlYLH52KU", "2026-spring-itaa-9u-spartans", "ITAA 9U Spartans"),   # existing
        ("VdoWDJdlCgAH", "2026-spring-mara-9u-stingers",  "MARA 9U Stingers"),  # existing
        ("OPP_TEAM_ID",  "opponent-team-slug",             "Opponent Team Name"), # new
    ],
    ...
},
```

To find the `TEAM_ID` and `slug`, go to the opponent team's schedule page on GameChanger and look at the URL:
```
https://web.gc.com/teams/TEAM_ID/team-slug-here/schedule
```

---

### Option B: Manual (one game at a time)

Use this when the scraper fails on a specific game, or you just need to add one game quickly.

**Step 1 — Find the game's /plays URL**

| Division | Schedule page |
|---|---|
| Majors | `https://web.gc.com/organizations/1CMI2BBazG8C/schedule` |
| Minors | `https://web.gc.com/organizations/GdcFopba2PbE/schedule` |
| Storm (ITAA own games) | `https://web.gc.com/teams/lTxYlYLH52KU/2026-spring-itaa-9u-spartans/schedule` |
| Storm (opponent team) | Navigate to the opponent team's own schedule page on GameChanger |
| Wild | Navigate to the Wild team's schedule page on GameChanger |

Click the game, then make sure `/plays` is at the end of the URL. Wait for all plays to finish loading on screen.

**Step 2 — Extract the raw text**

Open DevTools (`F12` or right-click → Inspect → Console tab). Paste this and press Enter:

```javascript
(() => {
  const blob = new Blob([document.body.innerText], {type: 'text/plain'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'game_raw.txt';
  a.click();
})();
```

A file called `game_raw.txt` downloads to your Downloads folder.

**Step 3 — Convert and save**

Run `parse_gc_text.py` to convert and place the file. The output path is optional — if omitted, the filename is auto-derived from the game date and team names:

```bash
# Explicit output path (recommended — gives you full control over the name)
python3 parse_gc_text.py ~/Downloads/game_raw.txt \
  "../../Majors/Reports/Scorebooks/Apr06-Braves-Rue_vs_Guardians-Esau.txt"

# Auto-name (file placed in same folder as the raw input)
python3 parse_gc_text.py ~/Downloads/game_raw.txt
```

The script will also print a parse verification summary — look for `✓ All inning headers accounted for`. If you see `⚠ N inning header(s) in raw not found in parsed output`, open the raw file and check for unusual GameChanger noise text before the first play in that inning.

**File naming rules:**

```
MonDD-AwayTeam-CoachLast_vs_HomeTeam-CoachLast.txt   ← Majors/Minors
MonDD-AwayTeam_vs_HomeTeam.txt                        ← Wild/Storm
```

- Month abbreviation + day, no space: `Mar15`, `Apr06`, `May01`
- Underscores instead of spaces in team names
- Underscore before and after `vs`
- No apostrophes: `As` not `A's`

**Sanity check:** Open the saved file — it should start with `GAME:` and look like this:
```
GAME: Mon Mar 15 | https://web.gc.com/organizations/1CMI2BBazG8C/schedule/[UUID]/plays

===Bottom 6th - Guardians-Esau===
Walk |  | Ball 1, Ball 2, Ball 3, Ball 4.
J E walks, B D pitching.
Ground Out | 1 Out | Strike 1 looking, In play.
T A grounds out to second baseman.
```

If it looks garbled or blank, the page may not have fully loaded — wait a few seconds and try the console snippet again.

---

## Stage 3a — Build Rosters with Jersey Numbers (Majors/Minors only)

This step is **optional but strongly recommended** for Majors and Minors. Without it, player names show as last-initial only (e.g., `T. Alvarez`) with no jersey numbers. With it, names show as `Tyler A. #1`.

```bash
# Both divisions
python3 scrape_box_scores.py

# One division only
python3 scrape_box_scores.py --division Majors

# Re-scrape all games (not just new ones)
python3 scrape_box_scores.py --force
```

This writes two JSON files per division:
- `Majors/Reports/rosters.json` — player first names + jersey numbers, keyed by initials
- `Majors/Reports/box_verify.json` — per-game AB/BB/SO totals for cross-check

`gen_reports.py` automatically picks these up next time it runs. If the JSON files don't exist, it falls back to the CSV (initials-only names, no jerseys).

> **Minors limitation:** The Minors org does not expose box score pages. `scrape_box_scores.py` cannot currently build `rosters.json` for Minors. Minors reports use CSV fallback names only.

**For Wild/Storm:** `scrape_box_scores.py` builds a `roster.txt` file per team folder (using team-based box score URLs) rather than a shared JSON. These `roster.txt` files are also editable manually if you need to correct a name or add a player that didn't appear in box scores.

---

## Stage 3b — Generate the Scouting Report

Once your game file(s) are in the right folder (and `rosters.json` is built for Majors), run:

```bash
# One specific Majors team
python3 gen_reports.py --division Majors --team Guardians

# Multiple Majors teams
python3 gen_reports.py --division Majors --team Guardians Braves Cubs

# All Majors teams
python3 gen_reports.py --division Majors

# All Minors teams
python3 gen_reports.py --division Minors

# Storm (all teams in Storm folder)
python3 gen_reports.py --division Storm

# One Storm team
python3 gen_reports.py --division Storm --team "MARA 9U Stingers"

# Wild (all teams in Wild folder)
python3 gen_reports.py --division Wild
```

> **Team name tip for Majors/Minors:** Use just the team nickname, no coach name — e.g. `Guardians` not `Guardians-Esau`. The script matches by nickname only.

> **Team name tip for Wild/Storm:** Use the exact folder name — e.g. `"MARA 9U Stingers"`. Case and spacing must match the folder name exactly (this must also match the team name as it appears in the inning headers of the game files).

### What to Expect in the Terminal

**Majors / Minors** output:
```
=== Guardians-Esau ===
  Mar15-Braves-Rue_vs_Guardians-Esau.txt: 22 PAs  [✓]
  Apr06-Braves-Rue_vs_Guardians-Esau.txt: 19 PAs  [✓]
  ...
  Total PA: 148  |  6 games  |  ✓ all checks passed
    Tyler A. #1         PA=18  AVG=.412  OBP=.500  SLG=.647  C%=85%  SM%=22%  CStr%=14%  FPT%=60%
    ...
  → /Spring/Majors/Reports/Scouting_Reports/Guardians_Esau-Scout_2026.pdf
  → Marked reviewed: Mar15-Braves-Rue_vs_Guardians-Esau-Reviewed.txt
```

**Wild / Storm** output:
```
=== MARA 9U Stingers ===
  Found 17 game files
  Feb23-MARA_9U_Stingers_vs_...-Reviewed.txt: 20 PAs  [✓]
  ...
  Total PA: 340  |  17 games  |  ✓ all checks passed
  → /Spring/Storm/MARA 9U Stingers/MARA_9U_Stingers_Scout_2026.pdf
```

Files that have been successfully parsed get renamed to `-Reviewed.txt` automatically so you know they've been processed. If a file fails to parse, it stays as-is and is listed as "skipped" in the PDF header.

Logs are saved to `Development/Logs/gen_reports_YYYYMMDD_HHMMSS.log`.

### Where the PDFs Go

```
Majors:  Spring/Majors/Reports/Scouting_Reports/TeamName_CoachLast-Scout_2026.pdf
Minors:  Spring/Minors/Reports/Scouting_Reports/TeamName_CoachLast-Scout_2026.pdf
Storm:   Spring/Storm/[TeamName]/TeamName_Scout_2026.pdf
Wild:    Spring/Wild/[TeamName]/TeamName_Scout_2026.pdf
```

> **Majors/Minors filename note:** the separator between team name and coach last name is an **underscore**, and the hyphen comes *before* "Scout" — e.g. `Guardians_Esau-Scout_2026.pdf`.

---

## PDF Format

The PDF contains:

**Card pages (variable count):** Player cards in a 2-column grid, maximum 3 rows per page. Teams with 7–12 players produce 2 card pages; 13–18 players produce 3 card pages, and so on. This cap ensures consistent card size and spray chart quality regardless of roster size.

Each card contains:
- Player name + jersey number (name in white, `#N` in amber), archetype label (2-word, see below), pitching approach in italic
- PA / AB counts (upper right)
- Stat boxes: AVG · OBP · SLG · C%
- Spray chart: heat-map fan showing ball-in-play frequency by zone (amber = ground ball, blue = fly ball/line drive). Zones: RF, CF, LF (outfield), 1B, 2B, SS, 3B (infield), P (pitcher)
- GB% bar (amber) and FB+LD% bar (blue)
- Footer: SM% · CStr% · FPT%

**Summary page (always the last page):** Full stat table for all batters + compact 1–2 sentence scouting notes per batter with 3+ PA.

### Stat Definitions

| Stat | Formula | Notes |
|---|---|---|
| AVG | H ÷ AB | — |
| OBP | (H + BB + HBP) ÷ (AB + BB + HBP) | — |
| SLG | TB ÷ AB | — |
| C% | (AB − K) ÷ AB | Contact rate. Both swinging AND looking Ks count against it. |
| GB% | Ground ball BIP ÷ total BIP | — |
| FB+LD% | (Fly ball + line drive BIP) ÷ total BIP | — |
| SM% | Swing-and-miss ÷ total swings | Requires pitch sequence data in game file |
| CStr% | Called strikes ÷ total pitches | Requires pitch sequence data |
| FPT% | First-pitch takes ÷ first-pitch takes+swings | Higher = more patient; only counts PAs where first pitch is recorded |

### Archetype Labels

Each card shows a 2-word archetype: **Approach × Result**. Cards with `*` suffix have 5–9 PA (small sample warning). Cards with fewer than 5 PA show `—`.

**Approach** (how the batter behaves at the plate):
- `Aggressive` — swings early; FPT% < 40% or high SM% vs. low CStr%
- `Disciplined` — selective; wide OBP-AVG gap (walks)
- `Passive` — takes pitches, FPT% > 70%, but doesn't walk enough to be Disciplined

**Result** (production outcome, relative to teammates):
- `Walker` — BB/PA in top-33%, walks are primary OBP driver
- `Overmatched` — C% in bottom-33% or SM% > 50%
- `Power` — SLG in top-33%, meaningful ISO
- `Contact` — default; puts ball in play

For Wild and Storm, thresholds are fixed (SLG top-33 = .450, C% bottom-33 = .500, BB/PA top-33 = .200) since there's no league-wide context for travel ball opponents.

---

## Troubleshooting

**"No module named reportlab"**
```bash
pip3 install reportlab --break-system-packages
```

**"No module named playwright"**
```bash
pip3 install playwright --break-system-packages && playwright install chromium
```

**"0 PAs" for a team / no stats showing**

The most common cause is a team name mismatch. The script matches the inning headers inside each game file against the team name.

**For Majors/Minors:** the game filename must contain the team key (e.g. `Guardians-Esau`) and the inning headers inside must match exactly (e.g. `===Bottom 3rd - Guardians-Esau===`).

**For Wild/Storm:** the team *folder name* must exactly match the team name as it appears in the inning headers. For example, if the game file contains `===Bottom 3rd - MARA 9U Stingers===`, the folder must be named `MARA 9U Stingers` — not `Mara 9U Stingers`, not `MARA Stingers`. Open a game file in a text editor and check the header spelling before creating the folder.

> **macOS case sensitivity warning:** macOS file system is case-insensitive by default. If you create a folder with the wrong case (e.g., `Crushers White 10u` instead of `Crushers White 10U`) and try to rename it, Finder or `mv` may silently do nothing. Use a two-step rename through a temp name:
> ```bash
> mv "Crushers White 10u" "Crushers White 10u_tmp"
> mv "Crushers White 10u_tmp" "Crushers White 10U"
> ```

Run a single team to see per-file detail:
```bash
python3 gen_reports.py --division Majors --team Guardians
python3 gen_reports.py --division Storm --team "MARA 9U Stingers"
```

**"⚠ N inning header(s) missing from parsed output" from parse_gc_text.py**

An inning header appeared in the raw GC text but didn't make it into the converted file. This usually means a GC noise pattern (score line, "Runner Out", out-count) appeared between the team name and the first play, confusing the parser. Open the raw file and look at that inning for unusual text.

**"⚠ BOX-VERIFY" warnings in gen_reports.py output**

The parsed AB or BB count for a player differs from the box score by more than 1. This can mean a play was missed in parsing. Check the game file for that player in that game.

**"⚠ ORDER" or "⚠ GAP" warnings in gen_reports.py output**

Batting order consistency check failed for a game. One batter has more PAs than someone who bats before them. Usually means a play was missed or a substitution note was mis-parsed.

**Unresolved player "?F L?" in output**

This only applies to **Majors/Minors** (Wild/Storm show raw initials as a fallback). The player's initials don't match anyone in `rosters.json` or the CSV. Fix options:
1. Run `scrape_box_scores.py` to build/update `rosters.json` — this usually resolves it automatically.
2. Or add manually to `DIVISIONS["Minors"]["roster_additions"]` in `gen_reports.py`:
```python
"roster_additions": {
    "Guardians-Esau": {"T H": "T. Hartford #5"},
},
```

**"FileNotFoundError" when running the script**

Check that the output folder exists. Create it if needed:
```bash
mkdir -p "../../Majors/Reports/Scouting_Reports"
```

**Script runs but you can't find the PDF**

Look in your Google Drive folder — it may take a moment to sync. The path is:
```
My Drive/Baseball/WCWAA/2026/Spring/[Division]/Reports/Scouting_Reports/
```

---

## Quick Reference

| Task | Command (run from `Development/Scripts/` folder) |
|---|---|
| **First-time login** | `python3 gc_scraper.py --login` |
| **Scrape all new games** | `python3 gc_scraper.py` |
| Scrape one division | `python3 gc_scraper.py --division Majors` |
| Scrape one team | `python3 gc_scraper.py --team "Braves-Rue"` |
| Force re-scrape | `python3 gc_scraper.py --force` |
| Build Majors rosters + jersey #s | `python3 scrape_box_scores.py --division Majors` |
| Build all box rosters | `python3 scrape_box_scores.py` |
| Convert one raw game file | `python3 parse_gc_text.py ~/Downloads/game_raw.txt "../../Majors/Reports/Scorebooks/MonDD-Away_vs_Home.txt"` |
| Generate one Majors team | `python3 gen_reports.py --division Majors --team TeamName` |
| Generate all Majors | `python3 gen_reports.py --division Majors` |
| Generate all Minors | `python3 gen_reports.py --division Minors` |
| Generate Storm | `python3 gen_reports.py --division Storm` |
| Generate one Storm team | `python3 gen_reports.py --division Storm --team "MARA 9U Stingers"` |
| Generate Wild | `python3 gen_reports.py --division Wild` |
| Install libraries | `pip3 install reportlab playwright --break-system-packages && playwright install chromium` |
| Navigate to Scripts | `cd ~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My\ Drive/Baseball/WCWAA/2026/Spring/Development/Scripts` |
| See files in current folder | `ls` |

---

## Claude Code / VS Code Onboarding Prompt

Use this as your first message when opening a new Claude Code session or GitHub Copilot chat in VS Code. Copy the entire block.

```
You are helping me with the WCWAA 2026 Spring baseball scouting report pipeline.

## Who I Am
I'm the coach and league admin for WCWAA (Weddington-area recreational + ITAA travel baseball),
Spring 2026. I use this pipeline to generate scouting reports for upcoming opponents.

## Project Location
Everything lives in Google Drive, synced locally:
  ~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com/My Drive/Baseball/WCWAA/2026/Spring/

Referred to below as "Spring/". All script paths are relative to this root.

## Directory Structure
Spring/
  Development/
    Scripts/               ← all Python scripts live here
    Logs/                  ← timestamped log files from all script runs
    ManualGuide.md         ← this documentation
    Bugs_List.txt          ← bug history log
    archetype_reference.txt← archetype system reference
  Majors/
    Reports/
      Scorebooks/          ← .txt play-by-play game files (Majors)
      Scouting_Reports/    ← output PDFs (Majors)
      rosters.json         ← first names + jersey #s (built by scrape_box_scores.py)
      box_verify.json      ← per-game AB/BB/SO for cross-check
  Minors/
    Reports/
      Scorebooks/          ← .txt play-by-play game files (Minors)
      Scouting_Reports/    ← output PDFs (Minors)
      rosters.json         ← (not yet built — Minors box scores inaccessible)
  Wild/
    [TeamName]/
      Games/               ← .txt play-by-play game files
      roster.txt           ← initials → display name + jersey (optional)
      [TeamName]_Scout_2026.pdf
  Storm/
    [TeamName]/
      Games/               ← .txt play-by-play game files
      roster.txt           ← initials → display name + jersey (optional)
      [TeamName]_Scout_2026.pdf

## Scripts (all in Development/Scripts/)
- gc_scraper.py          Playwright scraper — logs into GC, pulls /plays pages for all 4 divisions,
                         converts via parse_gc_raw(), saves .txt files. Run after each game week.
                         Uses gc_session.json (saved login cookie) in the same folder.
- scrape_box_scores.py   Playwright scraper — pulls /box-score pages to build rosters.json
                         (first names + jersey #s) and box_verify.json. Majors only (Minors
                         box scores inaccessible). Also builds roster.txt for Storm/Wild teams.
- parse_gc_text.py       Converts raw GC page text → WCWAA structured .txt format.
                         Imported by gc_scraper.py. Also standalone: python3 parse_gc_text.py raw.txt out.txt
                         Runs verify_parse() automatically — prints ⚠ for missing inning headers.
- gen_reports.py         Main stat engine + ReportLab PDF generator. Parses all .txt game files,
                         computes per-batter stats, assigns archetypes, generates spray charts,
                         writes PDF. Handles all 4 divisions. Renames parsed files to -Reviewed.txt.
- scrape_storm.py        Legacy bootstrap only. Converts /tmp/storm_raw/gN.txt files for ITAA 9U
                         Spartans early games. Use gc_scraper.py for all new games instead.

## Normal Weekly Workflow
1. python3 gc_scraper.py                         # pull new /plays game files
2. python3 scrape_box_scores.py --division Majors # update rosters.json (Majors only)
3. python3 gen_reports.py --division Majors       # regenerate Majors PDFs
   python3 gen_reports.py --division Storm        # regenerate Storm PDFs

## GameChanger URL Patterns
  Majors org:   https://web.gc.com/organizations/1CMI2BBazG8C/schedule
  Minors org:   https://web.gc.com/organizations/GdcFopba2PbE/schedule
  Storm ITAA:   https://web.gc.com/teams/lTxYlYLH52KU/2026-spring-itaa-9u-spartans/schedule
  Storm Stingers: https://web.gc.com/teams/VdoWDJdlCgAH/2026-spring-mara-9u-stingers/schedule
  Wild/other:   https://web.gc.com/teams/[TEAM_ID]/[slug]/schedule

## Game File Format (.txt)
Line 1: GAME: Mon Mar 15 | https://web.gc.com/.../plays
Inning headers: ===Bottom 3rd - Guardians-Esau===   or  ===Top 6th - MARA 9U Stingers===
Plays: outcome keyword line  (e.g. "Walk | | Ball 1, Ball 2, Ball 3, Ball 4.")
       narrative line        (e.g. "J E walks, B D pitching.")

Filenames:
  Majors/Minors: MonDD-AwayTeam-CoachLast_vs_HomeTeam-CoachLast.txt
  Wild/Storm:    MonDD-AwayTeam_vs_HomeTeam.txt
  After parsing: same name + "-Reviewed" appended before .txt

## Roster Sources (by division)
  Majors:  rosters.json (first name + jersey, from box scores) OR CSV fallback (last initial only)
  Minors:  CSV fallback only (rosters.json not yet built)
  Wild/Storm: roster.txt per team folder (format: "T A, Tyler A. #1") OR raw initials fallback

## Player Name Format
  All 4 divisions use: "FirstName LastInitial. #jersey"  e.g. "Tyler A. #1", "Hayes H. #4"
  On PDF cards: name renders in white 9pt bold, "#N" renders in amber immediately after.

## Stat Definitions
  AVG = H / AB
  OBP = (H + BB + HBP) / (AB + BB + HBP)
  SLG = TB / AB
  C%  = (AB - K_total) / AB     # K_total = swinging K + looking K
  GB% = ground ball BIP / total BIP
  FB+LD% = (fly ball + line drive BIP) / total BIP
  SM% = swing-and-miss / total swings   (from pitch sequence in game file)
  CStr% = called strikes / total pitches (from pitch sequence)
  FPT% = first-pitch takes / (takes + swings on first pitch)  — higher = more patient

## Archetype System (2-word label on each card)
  Approach: Aggressive (early swinger) | Disciplined (selective, walks) | Passive (takes too much)
  Result:   Walker (BB-driven OBP) | Overmatched (low C% or high SM%) | Power (top-33% SLG) | Contact (default)
  Majors/Minors use league-relative percentile thresholds; Wild/Storm use fixed thresholds.
  Cards with 5-9 PA show label + "*"; < 5 PA show "—"

## PDF Structure
  Card pages: 2-column grid, max 3 rows per page (6 cards max). Larger rosters use extra pages.
  Last page: summary stat table + compact 1-2 sentence scouting notes (batters with 3+ PA only).

## Verification Layers (gen_reports.py runs these automatically)
  Layer 1: Inning continuity — checks for skipped innings per team per game
  Layer 2: Unknown outcomes — flags unrecognized play descriptions
  Layer 3: Batting order check — PA counts must be consistent with lineup order
  Layer 4: Box score cross-check — parsed AB/BB vs. box score AB/BB (when rosters.json exists)
  All warnings print as ⚠ lines and are saved to the log file.

## Known Issues / Limitations
- Minors /box-score pages redirect to /info — rosters.json cannot be built for Minors
- Wild teams list in gc_scraper.py is currently empty (no Wild opponents added yet)
- Summary page PDF subtitle uses division_label from DIVISIONS config (Majors, Minors, Weddington Wild, Weddington Storm)

## My Task
[DESCRIBE YOUR TASK HERE — examples:
  "New Majors games were scraped. Regenerate the Guardians-Esau report."
  "Add a new Storm opponent team (SCRA 9U Cardinals). Here is their GC team URL."
  "The Stingers report shows ?J K? unresolved. Here is the roster.txt contents."
  "A game file is showing 0 PAs for Padres-Schick. Help me debug."
]
```

---
