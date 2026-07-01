# WCWAA Scouting Report Pipeline — Bug Tracker

> **Format:** Each entry includes Bug ID, Date, Component, Problem, Fix, and Status.
> **Components:** Hitting (`gen_hitting.py`), Pitching (`gen_pitching.py`), Scraping (`scrape_gc_*.py`), Parser (`parse_gc_text.py`), Orchestrator (`run_menu.py`), Web UI (`server.py`)
>
> Entries are listed in reverse chronological order (newest first). Bug IDs are sequential and never reused.

---

## BUG-20 · [STATUS: RV]

**Title:** "Not Found" when opening any report PDF from the web UI — season segment dropped from path

**Severity:** High
**Date Reported:** 2026-07-01
**Release Found:** v3.3.1
**Release Fixed:** v3.3.2

### Observable Problem
In the web UI's View Reports tab, clicking any Hitting or Pitching report opens a new tab that
shows a Flask "Not Found" (404) page instead of the PDF. The address bar shows a URL like
`http://127.0.0.1:5050/report/Majors/Reports/Scouting_Reports/Braves_Rue-Scout-Hitting_2026.pdf`.

### Steps to Reproduce
1. Start the server (`Start Scout.command`)
2. Open http://127.0.0.1:5050 → View Reports tab
3. Click any team's "Hitting" or "Pitching" pill
4. Expected: the PDF opens in a new tab — Actual: 404 "Not Found"

### Fix Explanation *(Exec Level — No Code)*
Reports are stored per season under `seasons/<season-id>/<Division>/…`. The page builds the list
of report links using a path that started at the *season folder* — so the season id (e.g.
`2026-spring`) was left out of the link. But the part of the server that actually delivers a PDF
starts looking from the *seasons* folder, one level higher, and so it needs the season id in the
path. Because the two halves disagreed by exactly one folder level, every report link pointed at a
location that did not exist, producing a 404. The link builder now includes the season id, so the
delivered path lines up with where the files actually live.

### Fix Details *(Technical)*
Root cause: an asymmetry introduced during the v3.3.0 per-season report work.
- `api_reports()` built each report's relative path with `pdf.relative_to(season_dir)` where
  `season_dir = seasons/<sid>/` — dropping the `<sid>` segment.
- `serve_report()` resolves `/report/<path>` with `(seasons_root / relpath)` where
  `seasons_root = seasons/` — so it *requires* the `<sid>` segment.

Fix (`src/web/server.py`, `api_reports()`): changed the relative base to the seasons root —
`rel = str(pdf.relative_to(seasons_root))` — so emitted paths now include the season id
(e.g. `2026-spring/Majors/Reports/Scouting_Reports/…pdf`), matching what `serve_report()` expects.
The path-traversal guard in `serve_report()` was already correct and needed no change. Verified
end-to-end: `GET /report/2026-spring/Majors/…-Hitting_2026.pdf` → HTTP 200, PDF bytes returned.

### Workaround
None in the UI. (Files could be opened directly from the Google Drive folder as a manual bypass.)

---

## BUG-19 · [STATUS: RV]

**Title:** Season dropdowns empty + header shows "loading…" — stale server process

**Severity:** High
**Date Reported:** 2026-07-01
**Release Found:** v3.3.0
**Release Fixed:** v3.3.1

### Observable Problem
After opening the web UI, the Season dropdowns on the Build and Add Team tabs are completely
empty, the View Reports tab shows only "All seasons" with no individual seasons listed, and the
header subtitle stays "loading…" indefinitely instead of showing the active season name.
The status indicator shows "Server online" (the server is reachable), yet no season data loads.

### Steps to Reproduce
1. Start the server once with an older build of `server.py` (pre-v3.2.0)
2. Update `server.py` to v3.2.0 or later (e.g. via `git pull`)
3. Do NOT restart the server — leave the old process running
4. Open or refresh http://127.0.0.1:5050
5. Expected: Season dropdowns populated with "2026 Spring ✓" — Actual: all season selects empty, header shows "loading…"

### Fix Explanation *(Exec Level — No Code)*
Python loads `server.py` once when the server process starts. If the code on disk is later
updated (through a git pull or any file save), the already-running process continues using the
old code it loaded at startup. In this case the process was running a pre-v3.2.0 version of
`server.py` that did not have the `/api/seasons` endpoint at all. When the browser asked for
season data it received a 404 error, which the front-end was silently swallowing, leaving the
dropdowns empty with no explanation.

**Immediate fix:** Kill the stale process (PID identified via `lsof -i :5050`) and relaunch
via `Start Scout.command`.

**Long-term fix (shipped in v3.3.1):**
1. `server.py` now stamps a `X-Scout-Version` header on every response so version drift is
   detectable at any time.
2. `app.js` now explicitly checks the HTTP status of the `/api/seasons` call. If the server
   returns anything other than 200 (e.g. a 404 from a stale process), a purple
   "⚠️ Server restart required" banner appears and the header subtitle changes to
   "⚠ Restart server" instead of staying on "loading…".

### Fix Details *(Technical)*
- **`server.py`**: Added `SERVER_VERSION = "3.3.0"` constant. Added `@app.after_request`
  hook `_add_version_header()` that injects `X-Scout-Version: {SERVER_VERSION}` into every
  Flask response.
- **`app.js`**: `loadSeasons()` now checks `res.ok` before calling `res.json()`. If `res.ok`
  is false (any non-2xx, including 404 from a stale server), updates `#seasonLabel` to
  "⚠ Restart server" and un-hides `#staleBanner`. Added `const staleBanner = el("staleBanner")`
  to the element cache.
- **`index.html`**: Added `#staleBanner` div (initially `.hidden`) between `#offlineBanner`
  and `<nav>`. Styled purple/violet to visually distinguish from the amber offline banner.
- **`style.css`**: Added `.stale-banner` and `.stale-banner code` rules.

### Workaround
Kill the Flask process manually (`kill <PID>`, PID found via `lsof -i :5050 -n -P`) and
relaunch via `Start Scout.command`.

---

## BUG-18 · [STATUS: RV]

**Title:** Season selector missing from Build, View Reports, and Add Team tab panels

**Severity:** Medium
**Date Reported:** 2026-06-30
**Release Found:** v3.2.0
**Release Fixed:** v3.3.0

### Observable Problem
When the web UI is open and the server is running, there is no season dropdown inline with the
Division/Team controls on the Build tab, no season filter on the View Reports tab, and no season
selector on the Add Team tab. Users cannot target a specific season from within those panels.

### Steps to Reproduce
1. Start the server (`Start Scout.command`)
2. Open http://127.0.0.1:5050
3. Observe Build tab — no season dropdown next to Division/Team
4. Observe View Reports tab — no season dropdown
5. Observe Add Team tab — no season dropdown above Division
6. Expected: season selector inline on each tab — Actual: no season selector on any operational tab

### Fix Explanation *(Exec Level — No Code)*
The v3.2.0 season management feature added a global season picker to the page header and a
dedicated "Seasons" tab for creating and activating seasons. However, the per-tab inline
season selectors (inline with Division/Team on Build; filter on View Reports; above Division
on Add Team) were never added to those three panels. This is a design gap — the header picker
controls which season is *active* system-wide, but there is no way to target a specific
season's data from within the operational tabs without switching the global active season.

### Fix Details *(Technical)*
Three panels in `index.html` need a season `<select>` added, and `app.js` needs to:
- **Build tab**: Add `#buildSeason` select (populated from `loadSeasons()`, no "All" option) before
  the Division select. Pass `season=` param to `/api/run` and `/api/divisions`. Server may need
  a `?season=` query param on those endpoints to scope the division/team lists and build target.
- **View Reports tab**: Add `#reportsSeason` select before the filter input. Filter `reportsList`
  render to only show PDFs under `seasons/<selected>/`.
- **Add Team tab**: Add `#addSeason` select above the Division select. Pass to `/api/add_team`.

Note: the global header picker (`#seasonSelect`) still makes sense as a convenience for switching
the system-wide active season. These per-tab selectors are about targeting a specific season
for an operation without necessarily switching the global active.

### Workaround
Use the "Seasons" tab (4th tab) to activate the desired season first, then restart the server,
then proceed with Build/View/Add Team. Clunky but functional.

---

## BUG-17 · [STATUS: RV]

**Title:** Newly added Wild/Storm team does not appear in web UI dropdown after "Add Team"

**Severity:** Medium
**Date Reported:** 2026-06-29
**Release Found:** v3.1.0
**Release Fixed:** v3.1.3

### Observable Problem
After adding a new Wild or Storm opponent via the web UI "Add Team" tab, the team does not appear in the Build division/team dropdowns — even though the success message confirms the team was added. A server restart is required to see the new team, which is not obvious to the user.

As a secondary issue, Wild/Storm teams appear in YAML insertion order rather than alphabetically, making long lists harder to scan. Majors/Minors were already alphabetical.

### Steps to Reproduce
1. Open the web UI → Add Team tab
2. Add a valid Wild or Storm opponent via a GC URL
3. Switch to the Build tab and open the division dropdown
4. Expected: new team appears in the dropdown — Actual: team is missing until server restart

### Fix Explanation *(Exec Level — No Code)*
The server was loading division/team data once when it started up and reusing that snapshot for every request. Adding a team updates the config file on disk, but the server was still serving its startup snapshot. Fixed by reading the config file fresh on every request to the divisions endpoint — the read is fast enough that users won't notice. Also sorted Wild/Storm team lists alphabetically to match Majors/Minors behavior.

### Fix Details *(Technical)*
Two module-level caches caused the stale data:
1. `server.py` — `_DIVISIONS = build_scraper_divisions()` was called once at module load. `api_divisions()` used this frozen dict for every subsequent request.
2. `run_menu.py` — `get_team_list()` reads Wild/Storm teams from `run_menu.DIVISIONS`, also a module-level import-time cache. Since `server.py` imports `get_team_list`, this cache is frozen for the server's lifetime.

**Fix:** Removed the module-level `_DIVISIONS` cache from `server.py`. `api_divisions()` now calls `build_scraper_divisions()` fresh on every request (reads YAML — fast, < 1 ms). For Wild/Storm, team names are extracted directly from the fresh data and sorted alphabetically, bypassing the stale `run_menu.DIVISIONS` cache entirely. For Majors/Minors, `get_team_list()` continues to be used — it reads `rosters.json` from disk on each call, so it was already fresh.

`run_menu.py` `get_team_list()` also updated: added `sorted()` to the Wild/Storm return so the terminal menu also displays teams alphabetically (matching Majors/Minors, which was already sorted via `rosters.json` key sort).

Note: The JS side (`app.js` line 219) already correctly re-fetched `/api/divisions` after a successful Add Team response — the bug was entirely server-side.

Files changed: `src/web/server.py`, `src/orchestrator/run_menu.py`

### Workaround
Restart the web server (`Ctrl+C` then `Start Scout.command` again) after adding a team.

---

## BUG-16: Accented characters in player names break regex parsing (González)

**Date:** May 18, 2026 · **Component:** Hitting + Pitching · **Status:** ✅ Fixed

**Problem:** Players with accented Latin characters in their last name (e.g., `B González`) were silently dropped from both hitting and pitching reports. The regexes used ASCII-only `[a-z]` for the last-name capture group. Affected: Ben González (#99, Weddington Stormtroopers / Storm) — 61 pitching PAs lost (carry-forward attributed them to prior pitcher), batting PAs also unparseable.

**Fix:** Changed `[a-z]` → `[a-z\u00C0-\u024F]` in all three regexes (covers all Latin Extended characters).
- Files: `gen_pitching.py` (`PITCHER_NAMED_RE`, `LINEUP_CHANGE_RE`), `gen_hitting.py` (`DESC_RE`)
- Verification: `B González` now appears with 61 pitching PAs and 34 hitting PAs. G Elliott corrected from 90 → 54 PAs.

---

## BUG-15b: Split player cards — same player appears twice in PDF *(data issue, not code bug)*

**Date:** May 4, 2026 · **Component:** N/A (data) · **Status:** ⚠️ Closed — not a code bug

**Problem:** GC used two name formats across the season for Crushers White 10U: 2-char initials in March (`"A L"`) vs full first name in April+ (`"Andrew L"`). Two stat buckets → two cards per player.

**Workaround:** Patched 7 March game files via `patch_march_initials.py` (run once, retained for audit).

---

## BUG-15: Dilworth 9U - Navy produced 0 PAs — folder name missing dash

**Date:** May 2, 2026 · **Component:** Scraping + Hitting · **Status:** ✅ Fixed (v2.4.0)

**Problem:** Storm opponent folder named `"Dilworth 9U Navy"` but GC headers write `"Dilworth 9U - Navy"`. 0 PAs across all 7 games.

**Fix:** Renamed folder; updated team name in both scrapers; enhanced "No PAs" warning to list team names from headers.
- Files: `scrape_gc_playbyplay.py`, `scrape_gc_boxscores.py`, `gen_hitting.py`

---

## BUG-14: False "Skipped" entries in PDF subtitle — stale game_files list

**Date:** May 10, 2026 · **Component:** Hitting · **Status:** ✅ Fixed (v2.4.1)

**Problem:** `gen_hitting.py` builds file list once at startup; renames `.txt` → `-Reviewed.txt` as it processes. Later team lookups on same file fail with FileNotFoundError. False SKIP label appears.

**Fix:** Before opening a `.txt` path, check existence; if missing, fall back to `-Reviewed.txt`.
- File: `gen_hitting.py` → `run_league()`

---

## BUG-13: Schedule scraper misses games after late April — GC lazy-loads schedule cards

**Date:** May 10, 2026 · **Component:** Scraping · **Status:** ✅ Fixed (v2.4.1)

**Problem:** GC lazy-loads schedule cards. Scraper extracted game data before scrolling → only saw games through late April. 9 Majors + 14 Minors games missed.

**Fix:** Added scroll-to-bottom loop (max 30 passes, 0.8s wait) before running `SCHEDULE_JS`. Loop exits when game count stops growing.
- File: `scrape_gc_playbyplay.py` → `get_schedule()`

---

## BUG-12: INNING GAP and BOX-VERIFY warnings producing terminal noise

**Date:** Apr 29, 2026 · **Component:** Hitting · **Status:** ✅ Fixed

**Problem:** Every run printed WARNING-level messages making it hard to spot genuine issues.

**Fix:** Demoted both from `logger.warning()` to `logger.debug()`. Still in log file.
- File: `gen_hitting.py` → `check_inning_continuity()`, `verify_game()`, `verify_box_score()`

---

## BUG-11: Wild/Storm PDF cards show no jersey numbers

**Date:** Apr 2026 · **Component:** Hitting · **Status:** ✅ Fixed

**Problem:** Game files use `"FirstName LastInitial"` format (e.g. `"Ryder B"`) but `roster.txt` keys use `"FirstInitial LastInitial"` (e.g. `"R B"`). Lookup never matched.

**Fix:** Extended `load_wild_roster()` to index each entry under both key formats.
- File: `gen_hitting.py` → `load_wild_roster()`

---

## BUG-10: Step 2 ignored --team filter; always scraped all division teams

**Date:** Apr 2026 · **Component:** Scraping + Orchestrator · **Status:** ✅ Fixed

**Problem:** When running the pipeline for a single Wild/Storm team, Step 2 looped through ALL teams. No `--team` arg existed.

**Fix:** Added `team_filter=None` param throughout; wired `--team` arg; updated `run_menu.py` to pass `team_args`.
- Files: `scrape_gc_boxscores.py`, `run_menu.py`

---

## BUG-9: scrape_gc_boxscores.py crashed with NameError: 'date' not defined

**Date:** Apr 24, 2026 · **Component:** Scraping · **Status:** ✅ Fixed

**Problem:** `date.today().isoformat()` called but only `datetime` was imported, not `date`.

**Fix:** Changed to `from datetime import datetime, date`.
- File: `scrape_gc_boxscores.py`

---

## BUG-8: SCHEDULE_JS team-page filenames had wrong date and wrong team name

**Date:** Apr 24, 2026 · **Component:** Scraping · **Status:** ✅ Fixed

**Problem:** After Bug 7 was fixed, generated filenames were malformed — leading dash (no date) and team name replaced by a location string. Day-abbr nodes were outside the `<a>` card; `lines[1]` was a location, not team name.

**Fix:** Added leaf-node day-abbr detection; added `is_home` field; used `team_name` for filename.
- File: `scrape_gc_playbyplay.py` → `SCHEDULE_JS` + `scrape_team_division()`

---

## BUG-7: SCHEDULE_JS 'final' detection broken for Wild/Storm team pages

**Date:** Apr 24, 2026 · **Component:** Scraping · **Status:** ✅ Fixed

**Problem:** GC team pages (Wild/Storm) show completed games with a score (e.g. `"W 7-5"`) rather than `"FINAL"`. Both scrapers reported `"0 FINAL games found"` for all Wild/Storm teams.

**Fix:** Added score-pattern detection (`/^[WL]\s+\d+-\d+/`) alongside the `FINAL` check in `SCHEDULE_JS`.
- Files: `scrape_gc_playbyplay.py`, `scrape_gc_boxscores.py`

---

## BUG-6: Shortstop (SS) spray chart zone always showed 0% — mapped to 3B

**Date:** Apr 23, 2026 · **Component:** Hitting · **Status:** ✅ Fixed

**Problem:** In `FIELDER_ZONES`, `"shortstop"` was mapped to zone key `"3B"` instead of `"SS"`. SS always showed 0%; 3B zone was inflated. Affected all four divisions.

**Fix:** Changed mapping from `("shortstop","3B")` to `("shortstop","SS")`.
- File: `gen_hitting.py` → `FIELDER_ZONES`

---

## BUG-5: Team folder name case mismatch — team produces 0 PAs

**Date:** Apr 10, 2026 · **Component:** Hitting · **Status:** ✅ Fixed (filesystem rename)

**Problem:** Team folder created as `"Crushers White 10u"` (lowercase `u`) but GC inning headers use `"Crushers White 10U"`. Case-sensitive matching → 0 PAs parsed.

**Fix:** Renamed folder via temp name (macOS case-insensitive filesystem requires two-step rename).

---

## BUG-4: Home Run not counting as FB+LD% *(symptom of Bug 2)*

**Date:** Apr 10, 2026 · **Component:** Parser · **Status:** ✅ Fixed (by BUG-2 fix)

**Problem:** R R's home run in g06 showed 0 FB+LD%. Root cause: the HR was in a half-inning silently dropped by Bug 2.

---

## BUG-3: Sacrifice Fly returned UNKNOWN outcome — counted as AB incorrectly

**Date:** Apr 10, 2026 · **Component:** Hitting · **Status:** ✅ Fixed

**Problem:** `"Sacrifice Fly"` was in `OUTCOME_KWS` but `parse_outcome()` had no branch to handle it, returning `UNKNOWN`. Every sacrifice fly counted as an AB, inflating AB counts and deflating AVG/OBP/SLG.

**Fix:** Added `SF` and `SB` constants. Wired through `parse_outcome()`, `parse_ball_type()`, `BIP_OUTCOMES`, and AB aggregation.
- File: `gen_hitting.py`

---

## BUG-2: GC noise text absorbed into inning headers — half-innings silently dropped

**Date:** Apr 10, 2026 · **Component:** Parser · **Status:** ✅ Fixed

**Problem:** GameChanger raw text sometimes contains status text (`"Runner Out"`, `"3 Outs"`, `"J B at bat"`) with no separator between the team name and the first play. `parse_gc_raw()` absorbed this noise into the inning team name string, producing malformed headers. Affected: Crushers White 10U g06 (10 PAs lost).

**Fix:** Added `TEAM_NOISE_RE` as a secondary split-point detector alongside `OUTCOME_RE` in `parse_gc_raw()`.
- File: `parse_gc_text.py` → `parse_gc_raw()`

---

## BUG-1: Infield spray chart dots overlapping pitcher's mound

**Date:** Apr 10, 2026 · **Component:** Hitting · **Status:** ✅ Fixed

**Problem:** Dots plotted for infield hits (2B, SS, 3B, 1B, P zones) were placed too close to home plate, landing visually inside or on top of the pitcher's mound circle on the spray chart.

**Fix:** Pushed the inner radius for infield dot scatter from `r_mnd*1.5` to `r_if*0.58`.
- File: `gen_hitting.py` → `draw_field_spray_chart()`

---

*End of bug log.*
