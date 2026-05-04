# WCWAA Scouting Report Pipeline — Bug Tracker

> **Format:** Each entry includes Date, Problem, Fix, and Workaround (if no code fix).

---

## BUG 1: Infield spray chart dots overlapping pitcher’s mound

**Date:** Apr 10, 2026

**Problem:** Dots plotted for infield hits (2B, SS, 3B, 1B, P zones) were placed too close to home plate, landing visually inside or on top of the pitcher’s mound circle on the spray chart. A ball hit to "2B" looked like it was hit to the pitcher, even when the P% showed 0%.

**Fix:** Pushed the inner radius for infield dot scatter from `r_mnd*1.5` to `r_if*0.58`, which clears the top of the mound circle in all infield sectors.
- File: `gen_reports.py` → `draw_field_spray_chart()`
- Change: `px, py = _rand_in_sector(a1, a2, r_if*0.58, r_if)`

**Workaround:** N/A — fully fixed.

---

## BUG 2: GC noise text absorbed into inning headers — half-innings silently dropped

**Date:** Apr 10, 2026

**Problem:** GameChanger raw text sometimes contains status text (`"Runner Out"`, `"3 Outs"`, `"J B at bat"`) with no separator between the team name and the first play. `parse_gc_raw()` absorbed this noise into the inning team name string, producing malformed headers like `===Bottom 2nd - Crushers White 10URunner Out3 Outs...===`. `INNING_RE` uses exact team name matching, so these headers never matched — entire half-innings were silently skipped. Affected: Crushers White 10U g06 Bottom 2nd (8 PAs lost, incl. R R home run) and g06 Bottom 4th (2 PAs lost). Total impact: 115 → 129 PAs recovered.

**Fix:** Added `TEAM_NOISE_RE` as a secondary split-point detector alongside the existing `OUTCOME_RE` in `parse_gc_raw()`. The parser now splits on whichever comes first — an outcome keyword OR a noise pattern.
- File: `parse_gc_text.py` → `parse_gc_raw()`
- Added pattern: `Runner Out | Batter Out | N Outs | X X at bat | score lines`

**Workaround:** N/A — fully fixed.

---

## BUG 3: Sacrifice Fly returned UNKNOWN outcome — counted as AB incorrectly

**Date:** Apr 10, 2026

**Problem:** `"Sacrifice Fly"` was added to `OUTCOME_KWS` but `parse_outcome()` had no branch to handle it, returning `UNKNOWN ("?")`. The `"?"` outcome fell through to the AB aggregation `else`-branch, counting every sacrifice fly as an AB. This inflated AB counts and deflated AVG/OBP/SLG. Sacrifice Bunt had the same issue.

**Fix:** Added `SF` and `SB` constants. Wired through `parse_outcome()`, `parse_ball_type()`, `BIP_OUTCOMES`, and AB aggregation.
- File: `gen_reports.py` (all sections above)

**Workaround:** N/A — fully fixed.

---

## BUG 4: Home Run not counting as FB+LD% *(symptom of Bug 2)*

**Date:** Apr 10, 2026

**Problem:** R R’s home run in g06 showed 0 FB+LD% in the Crushers White 10U report. Root cause: the HR was in g06 Bottom 2nd, one of the half-innings silently dropped by Bug 2. It was never parsed at all — not a classification error, a missing inning.

**Fix:** Fixing Bug 2 recovered the entire Bottom 2nd including the HR. No separate fix needed.

**Workaround:** N/A — resolved as part of Bug 2 fix.

---

## BUG 5: Team folder name case mismatch — team produces 0 PAs

**Date:** Apr 10, 2026

**Problem:** Team folder created as `"Crushers White 10u"` (lowercase `u`) but GC inning headers use `"Crushers White 10U"` (uppercase `U`). `INNING_RE` performs case-sensitive exact string matching — 0 PAs parsed across all games.

**Fix:** Two-step rename via temp name (required on macOS case-insensitive filesystem):

    mv "Crushers White 10u" "Crushers White 10u_tmp"
    mv "Crushers White 10u_tmp" "Crushers White 10U"

Always verify the team folder name matches the GC inning header exactly before running `gen_reports.py`.

**Workaround:** N/A — fully fixed, but requires care on initial folder creation.

---

## BUG 6: Shortstop (SS) spray chart zone always showed 0% — mapped to 3B

**Date:** Apr 23, 2026

**Problem:** In `FIELDER_ZONES` (`gen_reports.py` line 317), `"shortstop"` was mapped to zone key `"3B"` instead of `"SS"`. The spray chart had SS as its own arc sector (90–112.5°) but `extract_zone()` was tagging every shortstop play as `"3B"`. SS always showed 0%; 3B zone was inflated. Affected all four divisions.

**Fix:** Changed mapping from `("shortstop","3B")` to `("shortstop","SS")`.
- File: `gen_reports.py` → `FIELDER_ZONES` (~line 317)

**Workaround:** N/A — fully fixed.

---

## BUG 7: SCHEDULE_JS ‘final’ detection broken for Wild/Storm team pages

**Date:** Apr 24, 2026

**Problem:** GC team pages (Wild/Storm) show completed games with a score (e.g. `"W 7-5"`) rather than `"FINAL"`. Org pages (Majors/Minors) still use `"FINAL"`. `SCHEDULE_JS` only checked `lines.includes('FINAL')` — every Wild/Storm game was evaluated as non-final and skipped. Both scrapers reported `"0 FINAL games found"` for all Wild/Storm teams.

**Fix:** Added score-pattern detection alongside the `FINAL` check in `SCHEDULE_JS`.
- Files: `scrape_gc_playbyplay.py` and `scrape_gc_boxscores.py` → `SCHEDULE_JS`
- Commit: `ea04909`

**Workaround:** N/A — fully fixed.

---

## BUG 8: SCHEDULE_JS team-page filenames had wrong date and wrong team name

**Date:** Apr 24, 2026

**Problem:** After Bug 7 was fixed, generated filenames were malformed — leading dash (no date) and team name replaced by a location string. Two root causes:
1. **DATE:** Day-abbr (SUN/SAT) and day-number are separate leaf nodes outside the `<a>` card element on team pages, so `currentDateTag` remained empty.
2. **TEAM NAME:** `lines[1]` on team pages is a location string, not the home team name. The correct home name is the team being scouted (from loop variable `team_name`).

**Fix:** Added leaf-node day-abbr detection to set `currentDateTag`; added `is_home` field; used `is_home + team_name` to build correct filename.
- File: `scrape_gc_playbyplay.py` → `SCHEDULE_JS` + `scrape_team_division()`
- Commit: `00d8d40`

**Workaround:** N/A — fully fixed.

---

## BUG 9: scrape_gc_boxscores.py crashed with NameError: ‘date’ not defined

**Date:** Apr 24, 2026

**Problem:** `scrape_team_division()` called `date.today().isoformat()` but only `datetime` was imported, not `date`. Pre-existing lint error that only triggered after Bug 7 was fixed.

**Fix:** Changed `from datetime import datetime` to `from datetime import datetime, date`.
- File: `scrape_gc_boxscores.py` → top-level imports — Commit: `00d8d40`

**Workaround:** N/A — fully fixed.

---

## BUG 10: Step 2 ignored --team filter; always scraped all division teams

**Date:** Apr 2026

**Problem:** When running the pipeline for a single Wild/Storm team, Step 2 (roster scrape) looped through ALL teams in the division. No `--team` arg existed; `run()` and `scrape_team_division()` had no `team_filter` param; `run_menu.py` never forwarded the team filter to Step 2.

**Fix:** Added `team_filter=None` param throughout; wired `--team` arg in `argparse`; updated `run_menu.py` to pass `team_args` to Step 2.
- Files: `scrape_gc_boxscores.py`, `run_menu.py`

**Workaround:** N/A — fully fixed.

---

## BUG 11: Wild/Storm PDF cards show no jersey numbers

**Date:** Apr 2026

**Problem:** Game files use `"FirstName LastInitial"` format (e.g. `"Ryder B"`) for batters, but `roster.txt` keys use `"FirstInitial LastInitial"` (e.g. `"R B"`). The lookup never matched, so every Wild/Storm player displayed without a jersey number.

**Fix:** Extended `load_wild_roster()` to index each entry under both key formats simultaneously — `"R B"` and `"Ryder B"` both resolve to `"Ryder B. #1"`.
- File: `gen_reports.py` → `load_wild_roster()`

**Workaround:** N/A — fully fixed.

---

## BUG 12: INNING GAP and BOX-VERIFY warnings producing terminal noise

**Date:** Apr 29, 2026

**Problem:** Every run printed WARNING-level `INNING GAP` and `BOX-VERIFY` messages to the terminal. Nearly every game showed `[⚠ N warning(s)]`, making it hard to spot genuine issues. These checks produce large volumes of low-signal hits because GC play-by-play doesn’t always align perfectly with box score counts.

**Fix:** Demoted both from `logger.warning()` to `logger.debug()`. Still written to the log file but no longer appear on stdout.
- File: `gen_reports.py` → `check_inning_continuity()`, `verify_game()`, `verify_box_score()` — Commit: `v2.3.0`

**Workaround:** N/A — fully fixed.

---

## BUG 13: Majors LG RANK showed x/10 instead of x/11 (A’s-Blanco excluded)

**Date:** Apr 29, 2026

**Problem:** `build_league_context()` matched PDFs by `team_key` appearance in the filename. A’s-Blanco has an apostrophe in `team_key` (`"A's-Blanco"`) but filenames use the stripped form (`"As-Blanco"`). Match always failed → only 10 entries in `league_team_totals` → all Majors LG RANK rows showed x/10.

**Fix:** Added `file_team_key = team_key.replace("'", "")` as a fallback. Filename check now accepts either form.
- File: `gen_reports.py` → `build_league_context()` — Commit: `v2.3.0`

**Workaround:** N/A — fully fixed. Run confirmed: `"11 team totals built"`.

---

## BUG 14: Dilworth 9U - Navy produced 0 PAs — folder name missing dash

**Date:** May 2, 2026

**Problem:** Storm opponent folder named `"Dilworth 9U Navy"` but GC inning headers write `"Dilworth 9U - Navy"`. Exact string match failure → 0 PAs parsed across all 7 game files. The `"No PAs found"` warning gave no diagnostic detail.

**Fix:**
1. Renamed folder: `"Dilworth 9U Navy"` → `"Dilworth 9U - Navy"`
2. Updated team name in both scrapers’ `DIVISIONS["Storm"]["teams"]`.
3. Enhanced `"No PAs found"` warning to list every unique team name seen in inning headers, making future mismatches self-diagnosing.
- Files: `gen_reports.py`; `scrape_gc_playbyplay.py`; `scrape_gc_boxscores.py` — Commit: `v2.4.0`

**Workaround:** N/A — fully fixed.

---

## BUG 15: Split player cards — same player appears twice in PDF *(data format issue)*

**Date:** May 4, 2026
**Status:** ⚠️ CLOSED — NOT A CODE BUG. Data format inconsistency in game files.

**Problem:** Crushers White 10U (Storm) showed duplicate player cards in the PDF — e.g. `"Andrew L. #1"` appeared twice: once with ~27 PAs (April games) and once with ~10 PAs (March games). All 8 roster players were affected.

**Root Cause:** GC used two different name formats across the season for the same players:
- March games (7 files, Mar07–Mar22): 2-char initials — `"A L"`, `"N L"`
- April+ games (12 files, Apr11+): full first name — `"Andrew L"`, `"Nico L"`

`gen_reports.py` accumulates PA stats keyed by the raw name string. Because `"A L" ≠ "Andrew L"`, two separate stat buckets are created per player → two cards in the PDF. **This is not a code bug** — the parser behaves correctly; the inconsistency lives entirely in the source game files.

**Workaround:** Patched 7 March game files to replace 2-char initials with full first-name format, scoped to Crushers White 10U batting half-innings only:

| From | To       | From | To       |
|------|----------|------|----------|
| A C  | Asher C  | A L  | Andrew L |
| D P  | Devan P  | J B  | Jack B   |
| J S  | Jordan S | N L  | Nico L   |
| R B  | Reilly B | R R  | Riley R  |

- Script: `Scripts/patch_march_initials.py` (run once, retained for audit)
- After patch: single card per player with correct cumulative PA totals.

**Prevention:** Always use full first-name + last-initial format (`"Andrew L"`) when reviewing or creating game files. The 2-char format (`"A L"`) was an early-season GC artifact and should not be used.

---

*End of bug log.*
