# WCWAA Scouting Report Pipeline — Bug Tracker

> **Format:** Each entry includes Bug ID, Date, Component, Problem, Fix, and Status.
> **Components:** Hitting (`gen_hitting.py`), Pitching (`gen_pitching.py`), Scraping (`scrape_gc_*.py`), Parser (`parse_gc_text.py`), Orchestrator (`run_menu.py`)
>
> Entries are listed in reverse chronological order (newest first). Bug IDs are sequential and never reused.

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
