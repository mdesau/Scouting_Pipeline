# WCWAA Scout Pipeline — Issue Tracker (`BUGS.md`)

The project's single issue tracker: the developer record of **why** and **how** each issue was
found and fixed. [`CHANGELOG.md`](CHANGELOG.md) is the stakeholder-facing **what** and **when**;
every CHANGELOG `Fixed`/`Added` line names the tracker ID and links to its anchor here.

- **`BUG-###`** — one ID series for defects (untagged), enhancements `(Enh)`, server/infra-only
  changes `(Srv)`, and documentation-only changes `(Docs)`. IDs are sequential and never reused.
- **`KC-###`** — Known Caveats: architectural/environmental limitations, not code bugs.
- Entry rules and templates: `docs/Principles and Practices.md` §12.
- **Renumbered 2026-10-27:** IDs were zero-padded (`BUG-7` → `BUG-007`) and the old `BUG-15b`
  (data issue, not a code bug) became [KC-001](#kc-001--status-historical).

---

## Contents

### Bugs

**Open**

- (O) [BUG-029 — Pitching cards undercount 0-BB innings across games](#bug-029--status-o)

**Resolved or Closed**

- (RV) [BUG-042 — Hitting cards ordered by a partly reversed batting order](#bug-042--status-rv)
- (RV) [BUG-041 — Hitting report blank for teams with a space in the name](#bug-041--status-rv)
- (RV) [BUG-040 — Wrong pitcher credited when the starter isn't named in play-by-play](#bug-040--status-rv)
- (RV) [BUG-036 — Kids with similar first names merged into one roster entry](#bug-036--status-rv)
- (RV) [BUG-034 — Nightly run fired at 2 PM instead of 10 AM](#bug-034--status-rv)
- (RV) [BUG-022 — GameChanger blocks the scraper's headless browser](#bug-022--status-rv)
- (RV) [BUG-021 — Logged-out page text saved as game data](#bug-021--status-rv)
- (RV) [BUG-020 — Report PDFs 404 in the web UI](#bug-020--status-rv)
- (RV) [BUG-019 — Season dropdowns empty (stale server process)](#bug-019--status-rv)
- (RV) [BUG-018 — Season selector missing from web UI tabs](#bug-018--status-rv)
- (RV) [BUG-017 — Newly added team missing from web UI dropdown](#bug-017--status-rv)
- (RV) [BUG-016 — Accented player names dropped (González)](#bug-016--status-rv)
- (RV) [BUG-015 — Dilworth 9U - Navy produced 0 PAs](#bug-015--status-rv)
- (RV) [BUG-014 — False "Skipped" entries in PDF subtitle](#bug-014--status-rv)
- (RV) [BUG-013 — Schedule scraper misses lazy-loaded games](#bug-013--status-rv)
- (RV) [BUG-012 — Verification warnings flood the terminal](#bug-012--status-rv)
- (RV) [BUG-011 — Travel PDF cards show no jersey numbers](#bug-011--status-rv)
- (RV) [BUG-010 — Step 2 ignored the --team filter](#bug-010--status-rv)
- (RV) [BUG-009 — Box-score scraper crashed: `date` not defined](#bug-009--status-rv)
- (RV) [BUG-008 — Team-page game filenames had wrong date/team](#bug-008--status-rv)
- (RV) [BUG-007 — Team pages found 0 completed games](#bug-007--status-rv)
- (RV) [BUG-006 — Shortstop spray zone always 0%](#bug-006--status-rv)
- (RV) [BUG-005 — Folder case mismatch → 0 PAs](#bug-005--status-rv)
- (RV) [BUG-004 — Home run not counted in FB+LD%](#bug-004--status-rv)
- (RV) [BUG-003 — Sacrifice fly counted as an at-bat](#bug-003--status-rv)
- (RV) [BUG-002 — GC noise text dropped half-innings](#bug-002--status-rv)
- (RV) [BUG-001 — Infield spray dots overlap the mound](#bug-001--status-rv)

### Enhancements

**Open**

- (O) [BUG-028 (Enh) — `docs_cleanup.py` tracker/CHANGELOG enforcer](#bug-028-enh--status-o)
- (O) [BUG-027 (Enh) — Box-score cross-check (Layer 4) for travel teams](#bug-027-enh--status-o)
- (O) [BUG-026 (Enh) — Rebuild the whole travel division on single-team runs](#bug-026-enh--status-o)
- (O) [BUG-025 (Enh) — Drop the GC `TEAM` row from travel rosters](#bug-025-enh--status-o)
- (O) [BUG-024 (Enh) — Dynamic, percentile-driven archetypes](#bug-024-enh--status-o)

**Resolved or Closed**

- (RV) [BUG-039 (Enh) — Game lines show which quality pitchers are available](#bug-039-enh--status-rv)
- (RV) [BUG-038 (Enh) — Analysis command asks which division](#bug-038-enh--status-rv)
- (RV) [BUG-037 (Enh) — Draft report card: late additions, Majors setup, multi-word surnames](#bug-037-enh--status-rv)
- (RV) [BUG-035 (Enh) — One command builds all three analysis reports](#bug-035-enh--status-rv)
- (RV) [BUG-032 (Enh) — Draft report card: grades, ROI, steals and busts](#bug-032-enh--status-rv)
- (RV) [BUG-031 (Enh) — Tournament futures ("Vegas odds") board](#bug-031-enh--status-rv)
- (RV) [BUG-030 (Enh) — Pitching usage and team comparison workbook](#bug-030-enh--status-rv)
- (RV) [BUG-023 (Enh) — Folder rename needed upon mismatch during game scrape](#bug-023-enh--status-rv)

### Server

**Open** — none · **Resolved or Closed** — none

### Docs

**Open** — none

**Resolved or Closed**

- (RV) [BUG-033 (Docs) — README rewritten in plain language](#bug-033-docs--status-rv)

### Known Caveats

**Active**

- (Active) [KC-004 — Kids sharing initials can't be told apart in play-by-play](#kc-004--status-active)
- (Active) [KC-003 — GC box scores include a non-player `TEAM` row](#kc-003--status-active)
- (Active) [KC-002 — GameChanger only serves a visible, real Chrome window](#kc-002--status-active)

**Historical**

- (Historical) [KC-005 — Minors box scores redirected to `/info` (no jersey numbers)](#kc-005--status-historical)
- (Historical) [KC-001 — GC switched player-name format mid-season (split cards)](#kc-001--status-historical)

---

## Severity guide

| Severity     | Meaning                                       |
| ------------ | --------------------------------------------- |
| **Critical** | Crash, data loss, or total failure            |
| **High**     | Major break, no workaround                    |
| **Medium**   | Degraded behavior, workaround exists          |
| **Low**      | Cosmetic, minor, or rare                      |
| **Enh**      | Enhancement, optimization, or feature request |

## Status definitions

| Status | Meaning                                                               |
| ------ | --------------------------------------------------------------------- |
| `O`    | Open — confirmed, not yet being worked                                |
| `IP`   | In Progress — actively being investigated or fixed                    |
| `R`    | Resolved — fixed, not yet verified/shipped in a release               |
| `RV`   | Resolved & Verified — verified and shipped (see `Integrated Release`) |
| `C`    | Closed — won't fix, or not actually a code bug (reason documented)    |
| KC     | `Active` (still a real constraint) · `Historical` (no longer applies) |

---

## Bugs

### Open

- (O) [BUG-029 — Pitching cards undercount 0-BB innings across games](#bug-029--status-o)

### Resolved or Closed

- (RV) [BUG-042](#bug-042--status-rv) · [BUG-041](#bug-041--status-rv) · [BUG-040](#bug-040--status-rv) · [BUG-036](#bug-036--status-rv) · [BUG-034](#bug-034--status-rv) · [BUG-022](#bug-022--status-rv) · [BUG-021](#bug-021--status-rv) ·
  [BUG-020](#bug-020--status-rv) · [BUG-019](#bug-019--status-rv) ·
  [BUG-018](#bug-018--status-rv) · [BUG-017](#bug-017--status-rv) ·
  [BUG-016](#bug-016--status-rv) · [BUG-015](#bug-015--status-rv) ·
  [BUG-014](#bug-014--status-rv) · [BUG-013](#bug-013--status-rv) ·
  [BUG-012](#bug-012--status-rv) · [BUG-011](#bug-011--status-rv) ·
  [BUG-010](#bug-010--status-rv) · [BUG-009](#bug-009--status-rv) ·
  [BUG-008](#bug-008--status-rv) · [BUG-007](#bug-007--status-rv) ·
  [BUG-006](#bug-006--status-rv) · [BUG-005](#bug-005--status-rv) ·
  [BUG-004](#bug-004--status-rv) · [BUG-003](#bug-003--status-rv) ·
  [BUG-002](#bug-002--status-rv) · [BUG-001](#bug-001--status-rv)

<!-- template
## BUG-000 · [STATUS: O | IP | R | RV | C]

**Title:**

**Severity:** Critical | High | Medium | Low

**Reported Date:** YYYY-MM-DD

**Release Found:** v0.x.x

**Found By:** mesau (Matt Esau)

**Resolved Date:**

**Resolved By:**

**Integrated Release:** v0.x.x (commit <sha>, tag pushed YYYY-MM-DD) | N/A — Open

### Observable Problem
### Expected Behavior
### Steps to Reproduce
### Root Cause Analysis (RCA)
### Fix Explanation (Exec Level — No Code)
### Fix Details (Technical)
### Verification
### Workaround
### Eng Note
-->

### Detailed Entries

## BUG-042 · [STATUS: RV]

**Title:** Hitting cards ordered by a partly reversed batting order

**Severity:** Medium

**Reported Date:** 2026-10-29

**Release Found:** v5.3.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-29

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.3.1 (commit 5084ab3, tag pushed 2026-10-29)

### Observable Problem

Player cards in the hitting reports weren't in the team's usual batting order (e.g. the Blue Jays' leadoff
and cleanup hitters out of place compared with the box scores).

### Expected Behavior

Cards follow the team's typical batting order.

### Steps to Reproduce

1. Build any league hitting report. 2. Compare the card order with the box-score lineups.
3. Expected the usual order; actual a shuffled order.

### Root Cause Analysis (RCA)

Each batter's lineup spot was his first plate appearance's position in the game file. GC files are
newest-first, and only the innings were re-sorted — within an inning the batters stayed reversed. The
same partly reversed order drove the batting-order split of at-bats between kids sharing initials.

### Fix Explanation (Exec Level — No Code)

Scout now puts each game back in the order it happened before reading the lineup, and orders the cards by
each kid's most common (typical) spot. Card order now matches the box-score lineups.

### Fix Details (Technical)

<span style="color:red">`dev/src/scout/hitting/gen_hitting.py`</span>: new `_chrono_order()` (detects newest-first
files) and `_assign_lineup_slots()` (game_seq = lineup slot) used by `run_league()` / `run_wild()`;
`_disambiguate_pas()` uses `_chrono_order()`; `compute_stats()` adds `typical_batting_pos` (median) and
sorts by it, mean as tie-break. New <span style="color:red">`dev/tests/test_hitting_order.py`</span>.

### Verification

Computed card order for Blue Jays and Expos matches the box-score lineups exactly; 3 new tests (suite 35/35
OK). Fall Minors + Majors hitting reports rebuilt.

### Workaround

None.

### Eng Note

Travel-team reports pick up the fix on their next build (nightly).

---

## BUG-041 · [STATUS: RV]

**Title:** Hitting report blank for teams with a space in the name

**Severity:** High

**Reported Date:** 2026-10-29

**Release Found:** v4.0.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-29

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.3.1 (commit 5084ab3, tag pushed 2026-10-29)

### Observable Problem

The Blue Jays (Minors) hitting report showed 0 games; their pitching report was fine.

### Expected Behavior

Every league team's hitting report includes all of its games.

### Steps to Reproduce

1. Build Minors hitting reports. 2. Open the Blue Jays report. 3. Expected 13 games; actual 0.

### Root Cause Analysis (RCA)

Games are found by looking for the team key in game filenames. The scraper writes filenames with spaces
turned into underscores (`Blue_Jays-Patel`), but the hitting code only stripped apostrophes, so a team
name containing a space matched no files. It also left that team out of league percentiles and LG RANK.

### Fix Explanation (Exec Level — No Code)

The hitting report now looks for games using the same file naming the downloader uses. The Blue Jays
report has all 13 games, and every team's league comparisons now include the Blue Jays.

### Fix Details (Technical)

<span style="color:red">`dev/src/scout/hitting/gen_hitting.py`</span>: new `file_key()` (mirrors
`scrape_gc_playbyplay.safe()`), used in `build_league_context()` and `run_league()`;
<span style="color:red">`stat_analysis.py`</span> uses it too.

### Verification

Minors rebuild: league context 11 of 11 team totals (was 10); Blue Jays 13 games / 343 PA. 2 tests in
`test_hitting_order.py`.

### Workaround

None.

### Eng Note

The old matching dates to the v4.0.0 package move. Only team names with a space were affected (2026 Fall
Minors: Blue Jays).

---

## BUG-040 · [STATUS: RV]

**Title:** Wrong pitcher credited when the starter isn't named in play-by-play

**Severity:** Medium

**Reported Date:** 2026-10-29

**Release Found:** v5.2.2

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-29

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.3.0 (commit aecfb6a, tag pushed 2026-10-29)

### Observable Problem

Minors 10/28 Rays: the odds board said "T L" threw 37 pitches (back 10/31) and couldn't say whether
it was Tristan or Troy. The box score shows Grayson L. started (16 pitches) and Tristan L. threw 27
(back 10/30).

### Expected Behavior

Every appearance is credited to the right kid with the official pitch count.

### Steps to Reproduce

1. Game where the starter records no walk/strikeout (play-by-play never says "X pitching").
2. Run `pitching_usage` / `tourney_odds`. 3. Expected the starter's batters credited to him; actual
   they went to the first pitcher named later.

### Root Cause Analysis (RCA)

Play-by-play only names a pitcher on some events. Batters before the first naming were credited to
the first pitcher named — usually the reliever. Pitch counts were rebuilt from pitch sequences (can
drift), and kids sharing initials couldn't be told apart.

### Fix Explanation (Exec Level — No Code)

Scout now also reads each GameChanger box score's pitching table (names, jersey numbers, pitches,
batters faced, in order pitched). It uses it to credit the starter correctly, to name the right kid
when two share initials, and for official pitch counts. Play-by-play still provides the pitch-level
detail (swings, misses, strikes).

### Fix Details (Technical)

<span style="color:red">`scrape_gc_boxscores.py`</span>: `EXTRACT_BOXSCORE_JS` reads `BoxScore__{away,home}Pitching`
(+ `PitchingExtra`); `parse_pitching()` → `box_verify.json` `away_pitching` / `home_pitching`.
<span style="color:red">`pitching_usage.py`</span>: `analyze(scorebooks, box, rosters)` credits pre-naming
batters to the box starter; `_apply_box()` renames shared-initial apps via `roster_key()` (name +
jersey), sets official pitches/strikes and starter; `_split_shared()` splits one "C B" app when both
kids pitched. <span style="color:red">`games.py`</span>: `division_data()` loads box + rosters.

### Verification

2 new tests (parse, reconcile); suite 32/32 OK. Fall box scores re-downloaded (Majors 38, Minors 74,
all with pitching). Reconciled per-team pitch totals match the box score in 148/148 Minors and 75/76
Majors team-games; every team-game has one starter.

### Workaround

None.

### Eng Note

Remaining Majors mismatch (game 2faefe96, Rays): play-by-play credits "C D" with 5 pitches; the box
score doesn't list him — a GC inconsistency. The scouting-report pitching cards (`gen_pitching`) still
use play-by-play attribution only — candidate follow-up.

---

## BUG-036 · [STATUS: RV]

**Title:** Kids with similar first names merged into one roster entry

**Severity:** Medium

**Reported Date:** 2026-10-28

**Release Found:** v5.2.1

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-28

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.2.2 (commit 132788c, tag pushed 2026-10-28)

### Observable Problem

Carson B. (Royals, Majors) was missing from the roster and draft report even though he played
every game; his teammate Carter B. absorbed his entry. One Minors kid listed by GC as both "DJ" and
"Dheeraj" (#2) was treated as two kids.

### Expected Behavior

Every kid gets exactly one roster entry; two kids with the same initials stay separate.

### Steps to Reproduce

1. Two teammates share initials and the first 3 letters of their first name (Carter / Carson B).
2. Run `scrape_gc_boxscores --division Majors --force`. 3. Expected two entries; actual one `Car B`
   entry listed 17 times in `_collision_map`.

### Root Cause Analysis (RCA)

`_disambig_key()` always used the first 3 letters of the first name, so "Carter" and "Carson" both
became `Car B`; each new game re-added the key, overwriting the other kid. Matching used only the
first name, so a nickname with the same jersey looked like a different kid.

### Fix Explanation (Exec Level — No Code)

When two kids share initials, Scout now uses as many letters of the first name as needed, and uses
jersey numbers: same jersey = same kid; identical first names are told apart by jersey.

### Fix Details (Technical)

<span style="color:red">`dev/src/scout/scraping/scrape_gc_boxscores.py`</span>: `_disambig_key(init, first,
taken, jersey)` grows the prefix until unique (`Car B` / `Cars B`), then `First L #jersey`;
new `_same_kid()` (jersey decides when both present, else first name) used in `_accum_player()`;
`_first_name_from()` handles longer keys. New <span style="color:red">`dev/tests/test_roster_collisions.py`</span>.

### Verification

5 new tests; suite 27/27 OK. Fall Majors + Minors rosters rebuilt (`--force`): Carter #2 / Carson #1
separate, DJ/Dheeraj #2 merged (14 games), Tristan/Troy L and Charlie/Charlier C separate. Hitting,
pitching and analysis reports rebuilt for both divisions.

### Workaround

None.

### Eng Note

Play-by-play still uses initials only, so PAs for kids sharing initials are split by batting order
(KC-004). Spring 2026 rosters (3 affected teams) were not rebuilt — deferred to a later session.

---

## BUG-034 · [STATUS: RV]

**Title:** Nightly run fired at 2 PM instead of 10 AM

**Severity:** Low

**Reported Date:** 2026-10-27

**Release Found:** v5.1.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-27

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.2.0 (commit 077a24e, tag pushed 2026-10-27)

### Observable Problem

The docs say the nightly pipeline runs at 10:00 AM, but it actually ran at 2:00 PM.

### Expected Behavior

The scheduled run starts at 10:00 AM local time.

### Root Cause Analysis (RCA)

`StartCalendarInterval.Hour` in the launchd plist was `14`. launchd uses the Mac's local time, so
14 = 2 PM (likely set as UTC at some point).

### Fix Explanation (Exec Level — No Code)

The schedule file now says 10 AM, and the scheduler was reloaded so it took effect immediately.

### Fix Details (Technical)

<span style="color:red">`launchers/com.wcwaa.scout_pipeline.plist`</span>: `Hour` 14 → 10. Job reloaded with
`launchctl unload` / `load` (plist is symlinked into `~/Library/LaunchAgents/`).

### Verification

`launchctl list | grep wcwaa` shows the job loaded; `plutil -extract StartCalendarInterval.Hour raw`
returns `10`.

### Workaround

None.

---

## BUG-029 · [STATUS: O]

**Title:** Pitching cards undercount 0-BB innings across games

**Severity:** Medium

**Reported Date:** 2026-10-27

**Release Found:** v5.0.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** N/A — Open

**Resolved By:** N/A — Open

**Integrated Release:** N/A — Open

### Observable Problem

The "0BB" stat on pitching cards (innings pitched with no walks) is too low for any pitcher who
pitched in more than one game.

### Expected Behavior

Every inning a pitcher pitched in, in every game, is counted once; the stat is the number of those
innings with zero walks.

### Steps to Reproduce

1. Pick a pitcher who pitched the 1st inning in several games, with no walks in each.
2. Build that team's pitching PDF.
3. Expected: 0BB counts each of those innings — Actual: they count as one.

### Root Cause Analysis (RCA)

`gen_pitching.compute_pitcher_stats()` receives one pitcher's PAs from **all** games combined and
groups them by `p["inning"]` only. PA dicts carry no game ID, so inning 1 of game A and inning 1 of
game B land in the same bucket, and a walk in either game zeroes out both.

### Fix Explanation (Exec Level — No Code)

Not fixed yet. The count needs to treat "inning 1 of each game" as separate innings.

### Fix Details (Technical)

Proposed: tag each PA with its game in `parse_game_for_pitching_team()` callers and group by
`(game, inning)` in `compute_pitcher_stats()`. Add a unit test with the same inning across games.

### Workaround

The Fall Minors usage workbook (`dev/tmp/minors_usage_report.py`) counts 0-BB innings per game
correctly.

### Eng Note

Found while building the Fall 2026 Minors pitching-usage workbook.

---

## BUG-022 · [STATUS: RV]

**Title:** GameChanger blocks the scraper's hidden ("headless") browser — every page comes back empty

**Severity:** Critical

**Reported Date:** 2026-10-26

**Release Found:** v4.0.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-27

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.0.0 (commit ece7ff1, tag pushed 2026-10-27)

### Observable Problem

Scraping finds **0 games** for every team (e.g. "Weddington Mavericks 10U: 0 FINAL games found"),
even though the team has played games and the GameChanger login is valid. Signing in through the
scraper's browser window shows GameChanger's "Oops!" page instead of your teams.

### Expected Behavior

The scraper lists and downloads every completed game for each team.

### Steps to Reproduce

1. `python -m scout.scraping.scrape_gc_playbyplay --division Mavs --check` (v4.0.0 code)
2. Expected: the team's completed games are listed — Actual: `0 FINAL games found`

### Root Cause Analysis (RCA)

The AWS WAF in front of GameChanger rejects headless/automation browser fingerprints
(`navigator.webdriver`, `--enable-automation`, headless UA/GPU traits) with HTTP 403, before the
login is considered. Evidence (2026-10-26, same Scout profile + valid login in every case):

| Browser                                                  | Window                     | `api.team-manager.gc.com/me/*` | Page          |
| -------------------------------------------------------- | -------------------------- | ------------------------------ | ------------- |
| Playwright bundled Chromium (`launch(headless=True)`)    | none                       | 403                            | empty         |
| Playwright `launch_persistent_context(channel="chrome")` | yes, with automation flags | 403 / "Oops!"                  | error         |
| Real Chrome `--headless=new` + `connect_over_cdp`        | none                       | 403                            | empty         |
| Real Chrome, normal window + `connect_over_cdp`          | yes                        | **200**                        | full schedule |

GC auth is a localStorage token (`eden-auth-tokens` on `https://web.gc.com`), not a cookie — why
the old `gc_session.json` storage-state looked "cookie-less".

### Fix Explanation (Exec Level — No Code)

The scraper used to run its own built-in browser **headless** — the browser loads pages but never
opens a window, like a TV with the screen unplugged. GameChanger's security firewall now spots that
kind of browser and refuses to hand it any data, so every page loads empty. A login doesn't help.

GameChanger still serves a **normal Google Chrome window**, so the scraper now opens your installed
Chrome with a separate **Scout profile** (its own logins — your everyday Chrome is never touched),
remote-controls it to read pages, and closes it when scraping is done. You sign in once with
`--login`; it stays signed in. Every run starts with a quick **session check**: if the login has
expired, scraping is skipped (PDFs still rebuild from saved games), the log says what to run, and
nightly runs pop a macOS notification. During scraping a second Chrome icon appears in the Dock
(window placed off-screen); the Mac must be awake and logged in.

### Fix Details (Technical)

New module <span style="color:red">`dev/src/scout/scraping/gc_browser.py`</span> — the single place
that touches Chrome:

- `gc_chrome(log, on_screen=False)` — `subprocess.Popen`s Google Chrome with
  `--user-data-dir=data/real/sessions/gc_chrome_profile`, `--remote-debugging-port=9223` (127.0.0.1),
  `--window-position=-2400,0` (off-screen unless `on_screen`) and background-throttling disabled;
  polls `/json/version`, then `connect_over_cdp()`; on exit sends CDP `Browser.close` (graceful,
  flushes the profile). Raises `ChromeLaunchError` if port 9223 is busy, Chrome is missing, or
  Chrome exits at once.
- `check_session()` / `classify_session()` — load `/teams`, classify `/me/*` API statuses as
  `ok` / `signed_out` / `blocked`.
- `run_with_session(log, work)` — open → check → `work(page)`; returns
  `EXIT_CODES = {ok: 0, signed_out: 2, blocked: 3}`. `login(log)` — on-screen sign-in flow.

Callers: <span style="color:red">`scrape_gc_playbyplay.py`</span> and
<span style="color:red">`scrape_gc_boxscores.py`</span> use `run_with_session()` and exit with its
code; new `--check-session` flag. <span style="color:red">`run_menu.py`</span> adds a Preflight
(`_gc_session_ok()`), skipping Steps 1–2 on failure and calling `_notify()` on `--all`. Nightly
wrappers run under `caffeinate -i`. Playwright's bundled Chromium is no longer used; Google Chrome
must be installed.

### Verification

`dev/tests/test_fall_league_readiness.py::SessionClassificationTests` (6 tests). Live: session check
`ok` with the off-screen window; Mavs scraped 12/12 games, 16-player roster, both PDFs built;
Majors (38) and Minors (70) schedules found in dry runs.

### Workaround

None on v4.0.0. On v5.0.0, if the session check reports "expired", run
`python -m scout.scraping.scrape_gc_playbyplay --login`.

### Eng Note

**Limits:** a logged-in, awake Mac is required while scraping (launchd catches up a missed 10am run
on wake); screen-locked behavior is untested; only one Scout Chrome at a time (port 9223). See
[KC-002](#kc-002--status-active). Legacy `diag_schedule.py` still uses headless Playwright and is
non-functional.

---

## BUG-021 · [STATUS: RV]

**Title:** Play-by-play scraper saves logged-out page text as game data when the GC session expires

**Severity:** High

**Reported Date:** 2026-10-26

**Release Found:** v3.4.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-27

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.0.0 (commit ece7ff1, tag pushed 2026-10-27)

### Observable Problem

When the saved GameChanger login had expired, GC served a logged-out page and the scraper still
saved that page's text as a game file. Reports were built from content that was not the real game,
with no error shown.

### Expected Behavior

A logged-out or empty page is rejected and reported; nothing is written.

### Root Cause Analysis (RCA)

`extract_plays_raw()` waited for the plays element, then returned `document.body.innerText`
unconditionally — no check that plays actually loaded. `parse_gc_raw()` parsed whatever text was
there; game IDs, dates, and team names came from the public schedule page, so filenames and headers
looked correct and masked the bad content.

### Fix Explanation (Exec Level — No Code)

The scraper now checks that a downloaded page really contains innings before saving it, and refuses
any page that says "Sign in to GameChanger". With the session check from
[BUG-022](#bug-022--status-rv), an expired login is reported up front.

### Fix Details (Technical)

<span style="color:red">`scrape_gc_playbyplay.py`</span>: `extract_plays_raw()` →
`_has_valid_plays_content()` rejects bodies containing "Sign in to GameChanger" or lacking a
`Top/Bottom N - Team` inning header; returns `None` (counted as a failed game, nothing written).

### Verification

`dev/tests/test_fall_league_readiness.py::PlaysContentValidationTests` (3 tests). Live: 12 Mavs
games scraped with 0 "Sign in" pages and 12 distinct play-by-play bodies.

### Workaround

Run `python -m scout.scraping.scrape_gc_playbyplay --check-session` before scraping.

### Eng Note

Also shipped with this fix: `season_config.build_hitting_divisions()` derives league teams from
`rosters.json` keys (`_discover_league_teams()`) when the YAML team list is empty.

---

## BUG-020 · [STATUS: RV]

**Title:** "Not Found" when opening any report PDF from the web UI — season segment dropped from path

**Severity:** High

**Reported Date:** 2026-07-01

**Release Found:** v3.3.1

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-07-01

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v3.3.2 (commit 6e8beb2, not tagged)

### Observable Problem

In the web UI's View Reports tab, clicking any Hitting or Pitching report opens a Flask "Not Found"
(404) page instead of the PDF, e.g.
`http://127.0.0.1:5050/report/Majors/Reports/Scouting_Reports/Braves_Rue-Scout-Hitting_2026.pdf`.

### Expected Behavior

The PDF opens in a new tab.

### Steps to Reproduce

1. Start the server (`Start Scout.command`) → http://127.0.0.1:5050 → View Reports
2. Click any team's "Hitting" or "Pitching" pill
3. Expected: the PDF opens — Actual: 404 "Not Found"

### Root Cause Analysis (RCA)

An asymmetry from the v3.3.0 per-season work: `api_reports()` built paths with
`pdf.relative_to(season_dir)` (dropping the `<season-id>` segment), while `serve_report()` resolves
`/report/<path>` from `seasons_root` and requires it.

### Fix Explanation (Exec Level — No Code)

The list of report links left the season name out of each link, but the part of the server that
delivers PDFs needs it. The two halves disagreed by one folder level, so every link pointed at a
location that didn't exist. Links now include the season name.

### Fix Details (Technical)

<span style="color:red">`src/web/server.py`</span> `api_reports()`: relative base changed to the
seasons root (`pdf.relative_to(seasons_root)`), so paths include the season id. The path-traversal
guard in `serve_report()` was already correct.

### Verification

`GET /report/2026-spring/Majors/…-Hitting_2026.pdf` → HTTP 200 with PDF bytes.

### Workaround

None in the UI; open files directly from the Google Drive folder.

---

## BUG-019 · [STATUS: RV]

**Title:** Season dropdowns empty + header shows "loading…" — stale server process

**Severity:** High

**Reported Date:** 2026-07-01

**Release Found:** v3.3.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-07-01

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v3.3.1 (commit f358235, not tagged)

### Observable Problem

The Season dropdowns on Build and Add Team are empty, View Reports shows only "All seasons", and
the header stays on "loading…" — while the status indicator says "Server online".

### Expected Behavior

Season dropdowns are populated and the header shows the active season.

### Steps to Reproduce

1. Start the server with a pre-v3.2.0 `server.py`
2. Update the code (e.g. `git pull`) without restarting the server
3. Open or refresh http://127.0.0.1:5050
4. Expected: seasons listed — Actual: empty selects, header "loading…"

### Root Cause Analysis (RCA)

Python loads `server.py` once at startup; the running process predated the `/api/seasons`
endpoint, returned 404, and the front end silently swallowed the error.

### Fix Explanation (Exec Level — No Code)

The server was running old code from before seasons existed. Now every response is stamped with the
server's version, and the page shows a clear "Server restart required" banner when the server is
out of date instead of staying blank.

### Fix Details (Technical)

- <span style="color:red">`server.py`</span>: `SERVER_VERSION` + `@app.after_request`
  `_add_version_header()` → `X-Scout-Version` on every response.
- <span style="color:red">`app.js`</span>: `loadSeasons()` checks `res.ok`; on failure sets
  "⚠ Restart server" and shows `#staleBanner`.
- <span style="color:red">`index.html`</span> / <span style="color:red">`style.css`</span>:
  `#staleBanner` element and `.stale-banner` styles.

### Workaround

Kill the Flask process (`lsof -i :5050 -n -P`, then `kill <PID>`) and relaunch.

---

## BUG-018 · [STATUS: RV]

**Title:** Season selector missing from Build, View Reports, and Add Team tab panels

**Severity:** Medium

**Reported Date:** 2026-06-30

**Release Found:** v3.2.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-06-30

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v3.3.0 (commit a32b064, tag pushed 2026-06-30)

### Observable Problem

There is no season dropdown on the Build, View Reports, or Add Team tabs, so a season can't be
targeted from within those panels.

### Expected Behavior

Each operational tab has its own season selector (View Reports adds "All seasons").

### Steps to Reproduce

1. Open http://127.0.0.1:5050
2. Check Build, View Reports, and Add Team
3. Expected: a season selector on each — Actual: none

### Root Cause Analysis (RCA)

Design gap in v3.2.0: only a global header picker and a Seasons tab were built; the per-tab
selectors were never added.

### Fix Explanation (Exec Level — No Code)

Each tab now has its own season picker, so you can build, view, or add teams for any season
without switching the system-wide active season.

### Fix Details (Technical)

<span style="color:red">`index.html`</span> / <span style="color:red">`app.js`</span>: `#buildSeason`,
`#reportsSeason` (with "All seasons"), `#addSeason`; `season=` passed to `/api/run`,
`/api/divisions`, `/api/add_team`; <span style="color:red">`server.py`</span> endpoints accept
`?season=`.

### Workaround

Activate the season in the Seasons tab and restart the server.

---

## BUG-017 · [STATUS: RV]

**Title:** Newly added Wild/Storm team does not appear in web UI dropdown after "Add Team"

**Severity:** Medium

**Reported Date:** 2026-06-29

**Release Found:** v3.1.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-06-30

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v3.1.3 (commit 6433f80, tag pushed 2026-06-30)

### Observable Problem

After adding a team in the web UI's Add Team tab, it doesn't appear in the Build dropdowns until
the server is restarted. Travel teams were also listed in insertion order, not alphabetically.

### Expected Behavior

The new team appears immediately; team lists are alphabetical.

### Steps to Reproduce

1. Add Team tab → add a travel team from a GC URL
2. Build tab → open the team dropdown
3. Expected: new team listed — Actual: missing until restart

### Root Cause Analysis (RCA)

Two import-time caches: `server.py` `_DIVISIONS = build_scraper_divisions()` and
`run_menu.DIVISIONS` (used by `get_team_list()`), both frozen for the process lifetime.

### Fix Explanation (Exec Level — No Code)

The server read the team list once at startup. It now re-reads the config on every request
(fast enough to be invisible) and sorts travel teams alphabetically.

### Fix Details (Technical)

<span style="color:red">`src/web/server.py`</span>: removed `_DIVISIONS`; `api_divisions()` calls
`build_scraper_divisions()` per request and sorts travel teams.
<span style="color:red">`src/orchestrator/run_menu.py`</span>: `get_team_list()` sorts travel teams.

### Workaround

Restart the web server after adding a team.

---

## BUG-016 · [STATUS: RV]

**Title:** Accented characters in player names break regex parsing (González)

**Severity:** High

**Reported Date:** 2026-05-18

**Release Found:** v2.5.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-05-19

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v2.6.0 (commit 3dfb876, tag pushed 2026-05-19)

### Observable Problem

Players with accented last names (e.g. `B González`, Weddington Stormtroopers) were silently
dropped from hitting and pitching reports; their pitching PAs were credited to the previous pitcher.

### Expected Behavior

Accented names parse like any other.

### Root Cause Analysis (RCA)

Last-name capture groups used ASCII-only `[a-z]`.

### Fix Explanation (Exec Level — No Code)

The name matcher only understood plain English letters. It now accepts accented Latin letters.

### Fix Details (Technical)

`[a-z]` → `[a-z\u00C0-\u024F]` in <span style="color:red">`gen_pitching.py`</span>
(`PITCHER_NAMED_RE`, `LINEUP_CHANGE_RE`) and <span style="color:red">`gen_hitting.py`</span>
(`DESC_RE`).

### Verification

`B González` now shows 61 pitching PAs and 34 hitting PAs; G Elliott corrected from 90 → 54 PAs.

### Workaround

None.

---

## BUG-015 · [STATUS: RV]

**Title:** Dilworth 9U - Navy produced 0 PAs — folder name missing dash

**Severity:** Medium

**Reported Date:** 2026-05-02

**Release Found:** v2.3.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-05-02

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v2.4.0 (commit bcfa67b, tag pushed 2026-05-02)

### Observable Problem

Storm team "Dilworth 9U Navy" produced 0 PAs across all 7 games.

### Expected Behavior

All of the team's plate appearances are parsed.

### Root Cause Analysis (RCA)

Folder named `Dilworth 9U Navy`; GC inning headers say `Dilworth 9U - Navy`. Team matching is
exact.

### Fix Explanation (Exec Level — No Code)

The folder name was missing a dash that GameChanger uses. The folder and config were renamed, and
the "No PAs" warning now lists the team names actually found in the game files.

### Fix Details (Technical)

Folder renamed; team name updated in <span style="color:red">`scrape_gc_playbyplay.py`</span> and
<span style="color:red">`scrape_gc_boxscores.py`</span>; <span style="color:red">`gen_hitting.py`</span>
"No PAs" warning lists header team names.

### Workaround

Rename the folder to the GC spelling.

### Eng Note

Superseded by automatic handling in [BUG-023 (Enh)](#bug-023-enh--status-rv).

---

## BUG-014 · [STATUS: RV]

**Title:** False "Skipped" entries in PDF subtitle — stale game_files list

**Severity:** Low

**Reported Date:** 2026-05-10

**Release Found:** v2.4.1

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-05-10

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v2.5.0 (commit d5caecc, tag pushed 2026-05-17)

### Observable Problem

League PDF subtitles listed games as "Skipped" that were actually processed.

### Expected Behavior

Only genuinely unreadable games are listed as skipped.

### Root Cause Analysis (RCA)

`run_league()` built the file list once, then renamed `.txt` → `-Reviewed.txt` while processing;
later teams' lookups of the same game hit `FileNotFoundError`.

### Fix Explanation (Exec Level — No Code)

The report builder looked for a file under its old name after renaming it. It now checks for the
renamed copy.

### Fix Details (Technical)

<span style="color:red">`gen_hitting.py`</span> `run_league()`: fall back to `-Reviewed.txt` when the
`.txt` path no longer exists.

### Workaround

None needed (cosmetic).

### Eng Note

Earlier tracker listed v2.4.1 as the fix release, but commit d5caecc landed after the v2.4.1 tag.

---

## BUG-013 · [STATUS: RV]

**Title:** Schedule scraper misses games after late April — GC lazy-loads schedule cards

**Severity:** High

**Reported Date:** 2026-05-10

**Release Found:** v2.4.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-05-10

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v2.4.1 (commit 9dda244, tag pushed 2026-05-10)

### Observable Problem

Recent games were never scraped; 9 Majors + 14 Minors games missed.

### Expected Behavior

Every completed game on the schedule is found.

### Root Cause Analysis (RCA)

GC lazy-loads schedule cards; the scraper read the page before scrolling.

### Fix Explanation (Exec Level — No Code)

GameChanger only shows more games as you scroll. The scraper now scrolls to the bottom first.

### Fix Details (Technical)

<span style="color:red">`scrape_gc_playbyplay.py`</span> `get_schedule()`: scroll loop (max 30
passes, 0.8 s) until the game count stops growing, then run `SCHEDULE_JS`.

### Workaround

None.

---

## BUG-012 · [STATUS: RV]

**Title:** INNING GAP and BOX-VERIFY warnings producing terminal noise

**Severity:** Low

**Reported Date:** 2026-04-29

**Release Found:** v2.2.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-04-29

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v2.3.0 (commit 49a9a62, tag pushed 2026-04-29)

### Observable Problem

Every run printed WARNING-level verification messages, hiding genuine issues.

### Expected Behavior

Routine verification detail goes to the log file only.

### Root Cause Analysis (RCA)

Informational checks logged at `WARNING`.

### Fix Explanation (Exec Level — No Code)

Routine check messages were moved out of the screen output into the log file.

### Fix Details (Technical)

<span style="color:red">`gen_hitting.py`</span> `check_inning_continuity()`, `verify_game()`,
`verify_box_score()`: `logger.warning()` → `logger.debug()`.

### Workaround

None needed.

---

## BUG-011 · [STATUS: RV]

**Title:** Wild/Storm PDF cards show no jersey numbers

**Severity:** Low

**Reported Date:** 2026-04-24

**Release Found:** v1.0.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-04-24

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v2.0.0 (commit fd26a40, tag pushed 2026-04-24)

### Observable Problem

Travel-team player cards had no jersey numbers.

### Expected Behavior

Cards show `#jersey` from `roster.txt`.

### Root Cause Analysis (RCA)

Game files use `"Ryder B"`; `roster.txt` keys use `"R B"` — lookups never matched.

### Fix Explanation (Exec Level — No Code)

The roster and game files wrote names two different ways. The roster is now indexed both ways.

### Fix Details (Technical)

<span style="color:red">`gen_hitting.py`</span> `load_wild_roster()` indexes each entry under both
key formats.

### Workaround

None.

---

## BUG-010 · [STATUS: RV]

**Title:** Step 2 ignored --team filter; always scraped all division teams

**Severity:** Low

**Reported Date:** 2026-04-24

**Release Found:** v1.0.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-04-24

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v2.0.0 (commit c7a0109, tag pushed 2026-04-24)

### Observable Problem

A single-team pipeline run still scraped box scores for every team in the division.

### Expected Behavior

Step 2 scrapes only the selected team.

### Root Cause Analysis (RCA)

`scrape_gc_boxscores.py` had no `--team` argument.

### Fix Explanation (Exec Level — No Code)

The roster step didn't know which team was picked. It now does.

### Fix Details (Technical)

<span style="color:red">`scrape_gc_boxscores.py`</span>: `team_filter` param + `--team` arg;
<span style="color:red">`run_menu.py`</span> passes `team_args` to Step 2.

### Workaround

None needed (slow, not wrong).

---

## BUG-009 · [STATUS: RV]

**Title:** scrape_gc_boxscores.py crashed with NameError: 'date' not defined

**Severity:** High

**Reported Date:** 2026-04-24

**Release Found:** v1.0.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-04-24

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v2.0.0 (commit 00d8d40, tag pushed 2026-04-24)

### Observable Problem

The box-score scraper crashed while writing travel rosters.

### Expected Behavior

Rosters are written without error.

### Root Cause Analysis (RCA)

`date.today()` called, but only `datetime` was imported.

### Fix Explanation (Exec Level — No Code)

A missing import. Added.

### Fix Details (Technical)

<span style="color:red">`scrape_gc_boxscores.py`</span>: `from datetime import datetime, date`.

### Workaround

None.

---

## BUG-008 · [STATUS: RV]

**Title:** SCHEDULE_JS team-page filenames had wrong date and wrong team name

**Severity:** Medium

**Reported Date:** 2026-04-24

**Release Found:** v1.0.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-04-24

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v2.0.0 (commit 00d8d40, tag pushed 2026-04-24)

### Observable Problem

After [BUG-007](#bug-007--status-rv) was fixed, travel game filenames had a leading dash (no date)
and a location string where the team name belonged.

### Expected Behavior

Filenames look like `Apr19-TeamA_vs_TeamB.txt`.

### Root Cause Analysis (RCA)

Day-abbreviation nodes sit outside the `<a>` game card, and `lines[1]` is a location, not a team.

### Fix Explanation (Exec Level — No Code)

The scraper was reading the wrong parts of each schedule card. It now finds the date and team
correctly.

### Fix Details (Technical)

<span style="color:red">`scrape_gc_playbyplay.py`</span> `SCHEDULE_JS`: leaf-node day-abbr detection,
`is_home` field; `scrape_team_division()` uses the configured team name for filenames.

### Workaround

None.

---

## BUG-007 · [STATUS: RV]

**Title:** SCHEDULE_JS 'final' detection broken for Wild/Storm team pages

**Severity:** High

**Reported Date:** 2026-04-24

**Release Found:** v1.0.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-04-24

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v2.0.0 (commit ea04909, tag pushed 2026-04-24)

### Observable Problem

Both scrapers reported "0 FINAL games found" for every Wild/Storm team.

### Expected Behavior

Completed games on team pages are found.

### Root Cause Analysis (RCA)

Team pages show a result (`W 7-5`) instead of `FINAL`.

### Fix Explanation (Exec Level — No Code)

Team schedules mark finished games with the score, not the word "FINAL". The scraper now
recognizes scores too.

### Fix Details (Technical)

<span style="color:red">`scrape_gc_playbyplay.py`</span> and
<span style="color:red">`scrape_gc_boxscores.py`</span> `SCHEDULE_JS`: added `/^[WL]\s+\d+-\d+/`.

### Workaround

None.

### Eng Note

Ties (`T 4-4`) were added to the pattern in v5.0.0.

---

## BUG-006 · [STATUS: RV]

**Title:** Shortstop (SS) spray chart zone always showed 0% — mapped to 3B

**Severity:** Medium

**Reported Date:** 2026-04-23

**Release Found:** v0.2.0

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-04-23

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v1.0.0 (commit b9cd1b3, tag pushed 2026-04-24)

### Observable Problem

SS always showed 0% on spray charts and 3B was inflated, in all divisions.

### Expected Behavior

Balls to the shortstop count in the SS zone.

### Root Cause Analysis (RCA)

`FIELDER_ZONES` mapped `"shortstop"` to `"3B"`.

### Fix Explanation (Exec Level — No Code)

Shortstop plays were filed under third base. Corrected.

### Fix Details (Technical)

<span style="color:red">`gen_hitting.py`</span> `FIELDER_ZONES`: `("shortstop","SS")`.

### Workaround

None.

---

## BUG-005 · [STATUS: RV]

**Title:** Team folder name case mismatch — team produces 0 PAs

**Severity:** Medium

**Reported Date:** 2026-04-10

**Release Found:** Pre-release (before v0.1.0)

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-04-10

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** N/A — data fix (folder rename, no code change)

### Observable Problem

Crushers White 10U produced 0 PAs.

### Expected Behavior

All of the team's plate appearances are parsed.

### Root Cause Analysis (RCA)

Folder `Crushers White 10u` vs GC header `Crushers White 10U`; matching was case-sensitive.

### Fix Explanation (Exec Level — No Code)

The folder name's capitalization didn't match GameChanger's. The folder was renamed.

### Fix Details (Technical)

Two-step rename via a temporary name (macOS filesystems are case-insensitive).

### Workaround

Rename the folder.

### Eng Note

Case-insensitive matching added in commit b1e1c77 (v2.7.0); fully automatic since
[BUG-023 (Enh)](#bug-023-enh--status-rv).

---

## BUG-004 · [STATUS: RV]

**Title:** Home Run not counting as FB+LD% (symptom of BUG-002)

**Severity:** Low

**Reported Date:** 2026-04-10

**Release Found:** Pre-release (before v0.1.0)

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-04-10

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v0.1.0 (commit 8b082f9, tag pushed 2026-04-21)

### Observable Problem

R R's home run in game 6 showed 0 FB+LD%.

### Root Cause Analysis (RCA)

The HR sat in a half-inning dropped by [BUG-002](#bug-002--status-rv).

### Fix Explanation (Exec Level — No Code)

Fixed by the BUG-002 fix; no separate change.

### Workaround

None.

---

## BUG-003 · [STATUS: RV]

**Title:** Sacrifice Fly returned UNKNOWN outcome — counted as AB incorrectly

**Severity:** Medium

**Reported Date:** 2026-04-10

**Release Found:** Pre-release (before v0.1.0)

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-04-10

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v0.1.0 (commit 8b082f9, tag pushed 2026-04-21)

### Observable Problem

Every sacrifice fly counted as an at-bat, lowering AVG/OBP/SLG.

### Expected Behavior

Sacrifices are not at-bats.

### Root Cause Analysis (RCA)

`"Sacrifice Fly"` was in `OUTCOME_KWS` but `parse_outcome()` had no branch for it.

### Fix Explanation (Exec Level — No Code)

The parser didn't recognize sacrifice flies. It now handles sacrifice flies and bunts.

### Fix Details (Technical)

<span style="color:red">`gen_hitting.py`</span>: `SF`/`SB` constants wired through
`parse_outcome()`, `parse_ball_type()`, `BIP_OUTCOMES`, and AB aggregation.

### Workaround

None.

---

## BUG-002 · [STATUS: RV]

**Title:** GC noise text absorbed into inning headers — half-innings silently dropped

**Severity:** High

**Reported Date:** 2026-04-10

**Release Found:** Pre-release (before v0.1.0)

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-04-10

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v0.1.0 (commit 8b082f9, tag pushed 2026-04-21)

### Observable Problem

Some half-innings vanished from reports (Crushers White 10U game 6 lost 10 PAs).

### Expected Behavior

Every half-inning is parsed.

### Root Cause Analysis (RCA)

GC status text (`"Runner Out"`, `"3 Outs"`, `"J B at bat"`) ran into the team name with no
separator; `parse_gc_raw()` absorbed it into the header, so the team never matched.

### Fix Explanation (Exec Level — No Code)

Extra GameChanger status text got glued onto team names. The converter now splits it off.

### Fix Details (Technical)

<span style="color:red">`parse_gc_text.py`</span> `parse_gc_raw()`: `TEAM_NOISE_RE` as a second
split point alongside `OUTCOME_RE`.

### Workaround

None.

---

## BUG-001 · [STATUS: RV]

**Title:** Infield spray chart dots overlapping pitcher's mound

**Severity:** Low

**Reported Date:** 2026-04-10

**Release Found:** Pre-release (before v0.1.0)

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-04-10

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v0.1.0 (commit 8b082f9, tag pushed 2026-04-21)

### Observable Problem

Infield-hit dots were drawn on top of the pitcher's mound.

### Expected Behavior

Infield dots sit in the infield, clear of the mound.

### Fix Explanation (Exec Level — No Code)

The dots were placed too close to home plate. Moved out.

### Fix Details (Technical)

<span style="color:red">`gen_hitting.py`</span> `draw_field_spray_chart()`: inner radius
`r_mnd*1.5` → `r_if*0.58`.

### Workaround

None.

### Eng Note

BUG-001–004 were fixed before the repo existed; the fixes first appear in the initial commit.

---

## Enhancements

### Open

- (O) [BUG-028 (Enh)](#bug-028-enh--status-o) · [BUG-027 (Enh)](#bug-027-enh--status-o) ·
  [BUG-026 (Enh)](#bug-026-enh--status-o) · [BUG-025 (Enh)](#bug-025-enh--status-o) ·
  [BUG-024 (Enh)](#bug-024-enh--status-o)

### Resolved or Closed

- (RV) [BUG-039 (Enh)](#bug-039-enh--status-rv) · [BUG-038 (Enh)](#bug-038-enh--status-rv) · [BUG-037 (Enh)](#bug-037-enh--status-rv) ·
  [BUG-035 (Enh)](#bug-035-enh--status-rv) · [BUG-032 (Enh)](#bug-032-enh--status-rv) · [BUG-031 (Enh)](#bug-031-enh--status-rv) ·
  [BUG-030 (Enh)](#bug-030-enh--status-rv) · [BUG-023 (Enh)](#bug-023-enh--status-rv)

<!-- template: same as Bugs, heading `## BUG-000 (Enh) · [STATUS: …]`, Severity `Enh`,
Release Found `N/A — Enhancement`, RCA `N/A — Enhancement` when there is no defect cause,
Integrated Release `N/A — Open` until shipped. -->

### Detailed Entries

## BUG-039 (Enh) · [STATUS: RV]

**Title:** Game lines show which quality pitchers are available

**Severity:** Enh

**Reported Date:** 2026-10-29

**Release Found:** N/A — Enhancement

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-29

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.3.0 (commit aecfb6a, tag pushed 2026-10-29)

### Observable Problem

Game lines priced in rest, but didn't show which of a team's best arms were unavailable, and the
Little League "no more than 2 consecutive days" rule wasn't applied.

### Expected Behavior

Each game line shows each team's top-3 quality pitchers available, who's out (why, and the date back),
and the line if fully rested; all simulations follow Little League rest rules.

### Root Cause Analysis (RCA)

N/A — Enhancement

### Fix Explanation (Exec Level — No Code)

Rest follows Little League: 1–20 pitches = no rest, 21–35 = 1 day, 36–50 = 2 days, and a kid who
pitched 2 days in a row sits the 3rd. Game lines list available quality arms ("2 of 3"), each
unavailable one (e.g. "Tristan L. #7: 27 pitches 10/28 → back 10/30") and a full-rest comparison.

### Fix Details (Technical)

<span style="color:red">`dev/src/scout/analysis_tools/tourney_odds.py`</span>: `record_outing()` /
`eligible()` (availability tuple: back date, last day, consecutive days, pitches that day; same-day
pitches add), used by `availability()`, `Sim.pick()`, `Sim.game()`; `quality_pitchers()`, `qp_status()`;
game lines carry full-rest odds + QP status into console and PDF.
<span style="color:red">`pitching_usage.py`</span>: `pitcher_display()` and QP tab use `quality_pitchers()`.

### Verification

3 new tests (calendar mapping, 2-straight-days, same-day sum); suite 32/32 OK. 10/29 lines rebuilt
for Majors G8 and Minors G16/G17.

### Workaround

None.

---

## BUG-038 (Enh) · [STATUS: RV]

**Title:** Analysis command asks which division

**Severity:** Enh

**Reported Date:** 2026-10-28

**Release Found:** N/A — Enhancement

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-28

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.2.2 (commit 132788c, tag pushed 2026-10-28)

### Observable Problem

`run_analysis.sh` silently defaulted to Minors when no division was given.

### Expected Behavior

With no `--division`, the command lists the season's league divisions and asks which one to run.

### Root Cause Analysis (RCA)

N/A — Enhancement

### Fix Explanation (Exec Level — No Code)

Running the analysis command without a division now shows a numbered list (e.g. Majors / Minors)
and asks. Unattended runs stop with a clear message instead of waiting for an answer.

### Fix Details (Technical)

<span style="color:red">`dev/src/scout/analysis_tools/run_all.py`</span>: `pick_division()` (league divisions =
those with `scorebooks`; non-TTY → exit listing choices); `--division` no longer defaults.
<span style="color:red">`launchers/run_analysis.sh`</span>, <span style="color:red">`README.md`</span>: usage text.

### Verification

Simulated input (`x` then `2`) re-prompts then picks Minors; `< /dev/null` exits with the choices listed.

### Workaround

Pass `--division`.

---

## BUG-037 (Enh) · [STATUS: RV]

**Title:** Draft report card: late additions, Majors setup, multi-word surnames

**Severity:** Enh

**Reported Date:** 2026-10-28

**Release Found:** N/A — Enhancement

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-28

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.2.2 (commit 132788c, tag pushed 2026-10-28)

### Observable Problem

Kids who joined after the draft (e.g. Giancarlos V., Samuel C. in Majors) got no value or grade;
drafted kids with multi-word surnames ("De La Mora", "la Cour") could fail to match; Majors had no
draft sheet or bracket configured.

### Expected Behavior

Late additions are valued and slotted like picks (no ADP/ROI); all draftees match; all three
analysis reports build for Majors.

### Root Cause Analysis (RCA)

N/A — Enhancement

### Fix Explanation (Exec Level — No Code)

New "Late Additions — Not Drafted" section: kids not on the draft sheet who played 3+ games get
the same value measures and the slot their production earns, without affecting team grades
(one-game subs are left out). Majors now has its draft sheet and playoff bracket, including the
10/17 Padres–Royals forfeit in the official records.

### Fix Details (Technical)

<span style="color:red">`dev/src/scout/analysis_tools/draft_roi.py`</span>: `_late_additions()`
(`LATE_MIN_GAMES = 3`), `steals_busts()` returns the late list, new `SECTIONS` / `METHOD` entries,
row builders handle late adds; `match_pick()` accepts any surname word's initial.
<span style="color:red">`config/2026-Fall.yaml`</span>: Majors `postseason:` (bracket, order, finals,
if-necessary, `official_records` for the forfeit). Draft sheet
`Majors/Reports/2026 Fall Draft Results.xlsx - Majors.csv` added on the data root (Henning moved
to the Twins' round-11 slot, matching who he played for).

### Verification

`run_all --division Majors` and `--division Minors` build 4 files each; Majors seeds match the real
bracket; 5 late additions found across both divisions. Suite 27/27 OK.

### Workaround

None.

### Eng Note

Aaron Jordan (Twins) is drafted but appears in no Majors game or box score — listed as not found.

---

## BUG-035 (Enh) · [STATUS: RV]

**Title:** One command builds all three analysis reports

**Severity:** Enh

**Reported Date:** 2026-10-28

**Release Found:** N/A — Enhancement

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-28

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.2.1 (commit 4ac70b0, tag pushed 2026-10-28)

### Observable Problem

Refreshing the analysis reports took five commands (two scrapes plus one per tool), and each tool
re-read every game file on its own; the draft card even rebuilt its analysis twice.

### Expected Behavior

One command downloads the latest games once and builds all three reports.

### Root Cause Analysis (RCA)

N/A — Enhancement

### Fix Explanation (Exec Level — No Code)

New `run_analysis.sh` launcher (and `run_all` command) downloads games once, reads them once, and
writes the workbook, the tournament odds PDF, and the draft report card. Reports whose inputs aren't
set up for a division (no bracket or no draft sheet) are skipped with a note. Every report's rerun
instructions now show this single command.

### Fix Details (Technical)

<span style="color:red">`dev/src/scout/analysis_tools/run_all.py`</span> (new): scrapes via subprocess
(continues on a session failure), then calls `draft_roi.analyze/build_pdf/build_xlsx`,
`pitching_usage.build_workbook`, `tourney_odds.run`.
<span style="color:red">`games.py`</span>: `division_data()` (`lru_cache`d games + `pitching_usage.analyze`)
and `rerun_commands()`. <span style="color:red">`pitching_usage.py`</span>,
<span style="color:red">`tourney_odds.py`</span> (`main` → `run(division)`),
<span style="color:red">`draft_roi.py`</span> (`analyze` cached): use the shared data and rerun text.
<span style="color:red">`launchers/run_analysis.sh`</span> (new).

### Verification

`run_all --division Minors --no-scrape`: 72 games parsed once, 4 files written in 21 s. Standalone
`pitching_usage` and `draft_roi` still run. Suite 22/22 OK.

### Workaround

None.

---

## BUG-032 (Enh) · [STATUS: RV]

**Title:** Draft report card: grades, ROI, steals and busts

**Severity:** Enh

**Reported Date:** 2026-10-27

**Release Found:** N/A — Enhancement

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-27

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.2.0 (commit 077a24e, tag pushed 2026-10-27)

### Observable Problem

No way to judge how well each coach drafted, even though the draft sheet and every game are on hand.

### Expected Behavior

One command produces a draft report card (PDF and Excel) with team grades, each pick's value vs.
where he was taken, steals, busts, and the full draft board.

### Root Cause Analysis (RCA)

N/A — Enhancement

### Fix Explanation (Exec Level — No Code)

Each kid gets a value (runs added hitting + runs saved pitching vs. an average player, per team
game). ADP = actual pick; ROI ADP = where his value says he should have gone; ROI = the difference.
Teams are graded A+–F on value over their draft slots. The report lists steals, busts, a coaches'-kid
slotting check, and the full board. The Excel copy has one filterable tab per section with
numeric +/- columns that sort correctly.

### Fix Details (Technical)

<span style="color:red">`dev/src/scout/analysis_tools/draft_roi.py`</span> (new): `load_draft` (snake order
from the YAML `csv:` sheet), `roster_index` (merges duplicate-jersey entries), `match_pick` (nicknames,
traded players), `player_values` (linear-weight batting scaled to league runs + pitching runs saved
from `tourney_odds.build_ratings`), `analyze` (ROI ADP, ROI, value over round average, z-score
grades), `build_pdf`, `build_xlsx` (same text via shared constants; real numbers with `+0;-0`
formats; autofilter + frozen header per tab), `add_sheets` (Draft Board / Grades / Steals & Busts
tabs in the BUG-030 workbook).

### Verification

`dev/tests/test_analysis_tools.py`: snake order, nickname match, traded-player fallback. Full
suite 22/22 OK. Output checked: 115 picks, 3 unmatched draftees shown as blank/—, filters on each
tab, ROI stored as integers.

### Workaround

None.

### Eng Note

Three draftees (Landon Anderson, Henry Cato, Elijah Selman) aren't in GC and are excluded from
grades. Kids sharing initials split shared pitching value evenly (KC-004).

---

## BUG-031 (Enh) · [STATUS: RV]

**Title:** Tournament futures ("Vegas odds") board

**Severity:** Enh

**Reported Date:** 2026-10-27

**Release Found:** N/A — Enhancement

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-27

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.2.0 (commit 077a24e, tag pushed 2026-10-27)

### Observable Problem

No way to estimate each team's chances in the double-elimination playoff bracket.

### Expected Behavior

A dated PDF with each team's title odds (American moneyline) and lines for the next games,
re-runnable after every game day, with the bracket set in config.

### Root Cause Analysis (RCA)

N/A — Enhancement

### Fix Explanation (Exec Level — No Code)

Rates every team and pitcher (adjusted for opponents), then plays the bracket 20,000 times inning by
inning, following the 2-inning / 50-pitch limits and rest-day rules, and turns the results into odds
with a 25% sportsbook margin.

### Fix Details (Technical)

<span style="color:red">`dev/src/scout/analysis_tools/tourney_odds.py`</span> (new): `build_ratings`
(opponent-adjusted O/D per team and pitcher, normalized, shrunk), `fit_run_distribution`
(negative binomial, 5-run cap), `Sim` (pitch limits, `rest_days`, emergency arm), `tune` (5-fold CV
log-loss), `seed_order` (head-to-head tiebreak), `build_pdf` (named by last game date).
<span style="color:red">`config/2026-Fall.yaml`</span>: Minors `postseason:` block (bracket, order, dates,
`official_records`, `rollbacks`, `seeding_games`).

### Verification

`dev/tests/test_analysis_tools.py`: rest rules, American odds, rollback. Seeding reproduces the real
bracket; next-game matchups match the published schedule.

### Workaround

None.

### Eng Note

The 9/12 Expos–Marlins 10–10 tie is unconfirmed; if it was an Expos win, add a Marlins
`official_records` override.

---

## BUG-030 (Enh) · [STATUS: RV]

**Title:** Pitching usage and team comparison workbook

**Severity:** Enh

**Reported Date:** 2026-10-27

**Release Found:** N/A — Enhancement

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-27

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.2.0 (commit 077a24e, tag pushed 2026-10-27)

### Observable Problem

No way to see how coaches spread pitching or compare teams side by side, though the game files
already hold everything needed.

### Expected Behavior

One command builds a league workbook, re-runnable after each game day, with season details in
config, not code.

### Root Cause Analysis (RCA)

N/A — Enhancement

### Fix Explanation (Exec Level — No Code)

An Excel workbook: every pitcher's usage, each team's pitching spread, hitting/pitching/lineup
comparison by team, and a version that counts only each team's top 3 pitchers. Rerun steps are on
the Notes tab.

### Fix Details (Technical)

<span style="color:red">`dev/src/scout/analysis_tools/`</span> (new package). `games.py`: runs per
half-inning from GC score strings with per-team abbreviation mapping, weather rollbacks, postseason
config (shared by BUG-031/032). `pitching_usage.py`: `parse_game`, `analyze`, `lineup_stats`,
`write_sheet`, `build_workbook` (Pitcher Usage, Team Usage Summary, Team Comparison, Team Comparison
QP, draft tabs, Notes). <span style="color:red">`requirements.txt`</span>: `openpyxl`.

### Verification

Suite 22/22 OK. All 70 Fall Minors games' parsed runs match GC final scores; league K/BB match box
scores (995 vs 993, 1155 vs 1155).

### Workaround

None.

### Eng Note

On-demand only — not wired into `run_menu` / nightly. Workbook IP undercount (outs field position
when a play also changed the score) was found and fixed while building this.

---

## BUG-028 (Enh) · [STATUS: O]

**Title:** `docs_cleanup.py` — enforce BUGS.md / CHANGELOG.md conventions

**Severity:** Enh

**Reported Date:** 2026-10-27

**Release Found:** N/A — Enhancement

**Found By:** mesau (Matt Esau)

**Resolved Date:** N/A — Open

**Resolved By:** N/A — Open

**Integrated Release:** N/A — Open

### Observable Problem

`Principles and Practices.md` §12 describes a `docs_cleanup.py` tool (dry run / `--write` /
`--check`) that doesn't exist in this repo, so tracker formatting and CHANGELOG cross-links are
kept by hand.

### Expected Behavior

One command checks and fixes headings, ToC status prefixes, anchors, and CHANGELOG lines against
this tracker.

### Root Cause Analysis (RCA)

N/A — Enhancement

### Fix Explanation (Exec Level — No Code)

Not built yet.

### Workaround

Follow §12 by hand.

---

## BUG-027 (Enh) · [STATUS: O]

**Title:** Box-score cross-check (verification Layer 4) for travel teams

**Severity:** Enh

**Reported Date:** 2026-10-27

**Release Found:** N/A — Enhancement

**Found By:** mesau (Matt Esau)

**Resolved Date:** N/A — Open

**Resolved By:** N/A — Open

**Integrated Release:** N/A — Open

### Observable Problem

Travel-team reports are never checked against GameChanger box scores, so a parsing miss would go
unnoticed. League (Majors/Minors) reports are checked.

### Expected Behavior

Parsed AB/BB per player are compared with box-score totals for travel teams too.

### Root Cause Analysis (RCA)

N/A — Enhancement. Not a data limitation (both sources use initials):
`scrape_gc_boxscores.scrape_team_division()` already accumulates AB/BB/SO per player but writes only
names to `roster.txt` and no `box_verify.json`; `gen_hitting.run_wild()` never calls
`verify_box_score()`. Git history shows the check was built for Minors (commit 4e1ce0e) with no
recorded decision to exclude travel teams.

### Fix Explanation (Exec Level — No Code)

Not built yet. The scraper already reads the numbers; they need to be saved and compared.

### Fix Details (Technical)

Proposed: write a per-team `box_verify.json` in `scrape_team_division()` and call
`verify_box_score()` from `run_wild()`.

### Workaround

None.

---

## BUG-026 (Enh) · [STATUS: O]

**Title:** Rebuild the whole travel division on single-team runs

**Severity:** Enh

**Reported Date:** 2026-10-27

**Release Found:** N/A — Enhancement

**Found By:** mesau (Matt Esau)

**Resolved Date:** N/A — Open

**Resolved By:** N/A — Open

**Integrated Release:** N/A — Open

### Observable Problem

After adding and running a new team, the other teams' LG RANK and pitching percentiles stay as of
their last run.

### Expected Behavior

Every team's ranks reflect the current division.

### Root Cause Analysis (RCA)

N/A — Enhancement. `run_wild()` reads every team for rank context but writes PDFs only for the
`--team` target.

### Fix Explanation (Exec Level — No Code)

Not built yet. Proposed: single-team runs still scrape one team, but Steps 3–4 rebuild the whole
division (seconds, no scraping).

### Workaround

`python -m scout.hitting.gen_hitting --division X` and
`python -m scout.pitching.gen_pitching --division X`.

---

## BUG-025 (Enh) · [STATUS: O]

**Title:** Drop the GC `TEAM` row from travel `roster.txt`

**Severity:** Enh

**Reported Date:** 2026-10-26

**Release Found:** N/A — Enhancement

**Found By:** mesau (Matt Esau)

**Resolved Date:** N/A — Open

**Resolved By:** N/A — Open

**Integrated Release:** N/A — Open

### Observable Problem

Every travel roster includes a `TEAM, TEAM` line that isn't a player
([KC-003](#kc-003--status-active)).

### Expected Behavior

Rosters list players only.

### Root Cause Analysis (RCA)

N/A — Enhancement. `scrape_team_division()` copies every box-score row.

### Fix Explanation (Exec Level — No Code)

Not built yet. Skip the `TEAM` row when building rosters.

### Workaround

Harmless as-is; play-by-play never names "TEAM".

---

## BUG-024 (Enh) · [STATUS: O]

**Title:** Dynamic, percentile-driven archetypes

**Severity:** Enh

**Reported Date:** 2026-06-28

**Release Found:** N/A — Enhancement

**Found By:** mesau (Matt Esau)

**Resolved Date:** N/A — Open

**Resolved By:** N/A — Open

**Integrated Release:** N/A — Open

### Observable Problem

Archetype labels use fixed cutoffs that don't adapt to each division's distribution.

### Expected Behavior

Cutoffs come from percentiles of the division's own data.

### Root Cause Analysis (RCA)

N/A — Enhancement.

### Fix Explanation (Exec Level — No Code)

Not built yet. `stat_analysis.py` already produces the distribution data to drive it.

### Workaround

Static cutoffs (current behavior).

### Eng Note

Migrated from AGENTS.md To Do #5.

---

## BUG-023 (Enh) · [STATUS: RV]

**Title:** Folder rename needed upon mismatch during game scrape

**Severity:** Enh

**Reported Date:** 2026-10-27

**Release Found:** N/A — Enhancement

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-27

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.1.0 (commit 8685d18, tag pushed 2026-10-27)

### Observable Problem

A travel team's folder name often differs from GameChanger's inning-header spelling only by
punctuation, e.g. folder `OC Crushers Blue 11U` vs header `OC Crushers - Blue 11U`. The team then
produces 0 PAs and its reports are empty until someone renames the folder and the config entry by
hand:

```
WARNING  No PAs found for 'OC Crushers Blue 11U' — 0 plate appearances parsed across 9 game file(s) …
         Team names seen in these files: [… 'OC Crushers - Blue 11U', …]
```

### Expected Behavior

Punctuation/spacing/case-only differences are detected, logged, and fixed automatically.

### Steps to Reproduce

1. Add a travel team whose suggested folder name drops a punctuation mark GC uses
2. Scrape its games and build reports
3. Expected: reports build — Actual: "No PAs found" warning, empty report

### Root Cause Analysis (RCA)

N/A — Enhancement. Team matching against inning headers is exact (case-insensitive since v2.7.0);
folder names come from the add-team wizard's slug-based suggestion, which can't know GC's display
punctuation.

### Fix Explanation (Exec Level — No Code)

Before building travel-team reports, the pipeline compares each team folder with the team names in
its game files. If they differ only by punctuation, spacing, or capitalization, it logs the
mismatch, renames the folder to GameChanger's spelling, updates the team name in the season config
(so the next scrape uses the new folder), and logs that it did. Real spelling differences are left
alone and still produce the "No PAs" warning.

### Fix Details (Technical)

- <span style="color:red">`dev/src/scout/season_config.py`</span>: `team_name_key()` (casefold,
  strip non-alphanumerics); `reconcile_team_folders(division, base_dir, log)` reads inning-header
  names from each team's `Games/*.txt`, renames on exactly one key match (skips if the target exists
  or contains `/`), and `_rename_team_in_yaml()` updates the YAML. Mismatch → `WARNING`; rename →
  `INFO`; rename with no YAML entry → `WARNING`.
- <span style="color:red">`dev/src/scout/hitting/gen_hitting.py`</span> `run_wild()` and
  <span style="color:red">`dev/src/scout/pitching/gen_pitching.py`</span> `run_travel_division()`
  call it first; `--team` filters compare with `team_name_key()`.

### Verification

`dev/tests/test_fall_league_readiness.py::TeamFolderReconcileTests` (3 tests; suite 16/16 OK).
Live: Mavs rebuild renamed `OC Crushers Blue 11U` → `OC Crushers - Blue 11U`, updated
`config/2026-Fall.yaml`, and built both PDFs (Mavs LG RANK enabled, 4 teams).

### Workaround

Before v5.1.0: rename the folder and the YAML `name:` to the GC spelling.

### Eng Note

Generalizes the manual fixes in [BUG-005](#bug-005--status-rv) and [BUG-015](#bug-015--status-rv).
The rename runs at the start of report building (Steps 3–4), immediately after the scrape.

---

## Server

### Open

None.

### Resolved or Closed

None.

<!-- template: same as Bugs, heading `## BUG-000 (Srv) · [STATUS: …]`, real severity. -->

### Detailed Entries

None yet.

---

## Docs

### Open

None.

### Resolved or Closed

- (RV) [BUG-033 (Docs)](#bug-033-docs--status-rv)

<!-- template: same as Bugs, heading `## BUG-000 (Docs) · [STATUS: …]`, severity usually Low. -->

### Detailed Entries

## BUG-033 (Docs) · [STATUS: RV]

**Title:** README rewritten in plain language

**Severity:** Low

**Reported Date:** 2026-10-27

**Release Found:** N/A — Docs

**Found By:** mesau (Matt Esau)

**Resolved Date:** 2026-10-27

**Resolved By:** mesau (Matt Esau)

**Integrated Release:** v5.2.0 (commit 077a24e, tag pushed 2026-10-27)

### Observable Problem

The README was written for developers and was missing what a new user needs: where reports
land, a plain step-by-step of the pipeline, and how to point Scout at their own report folder.

### Expected Behavior

A non-technical user can understand what Scout does, set it up on a new Mac, and find the reports.

### Root Cause Analysis (RCA)

N/A

### Fix Explanation (Exec Level — No Code)

README rewritten in everyday terms: where everything lives, a 5-step pipeline walkthrough, what the
reports show, new-Mac setup, running options, teams/seasons/scrimmages, the three analysis tools
with plain explanations of how they work, and troubleshooting.

### Fix Details (Technical)

<span style="color:red">`README.md`</span> (full rewrite). New-user gaps closed: `SCOUT_DATA_ROOT` must be set
(the default is the owner's Google Drive), and the nightly wrapper script lives outside the repo so
setup now shows how to create it. <span style="color:red">`AGENTS.md`</span>: draft report card outputs.

### Workaround

None.

---

## Known Caveats

### Active

- (Active) [KC-004](#kc-004--status-active) · [KC-003](#kc-003--status-active) ·
  [KC-002](#kc-002--status-active)

### Historical

- (Historical) [KC-005](#kc-005--status-historical) · [KC-001](#kc-001--status-historical)

<!-- template
## KC-000 · [STATUS: Active | Historical | Resolved YYYY-MM-DD]

**Title:**

**Date Identified:** YYYY-MM-DD

### Exec Description
### Eng Description
### Alternative Solutions
-->

### Detailed Entries

## KC-005 · [STATUS: Historical]

**Title:** Minors box scores redirected to `/info` — jersey numbers unavailable

**Date Identified:** 2026-04-22

### Exec Description

Early in Spring 2026, Minors box-score pages weren't reachable, so Minors reports had no jersey
numbers. No longer the case.

### Eng Description

Minors `/box-score` URLs redirected to `/info`. Current data shows jerseys are present: 146/180
Spring 2026 and 120/138 Fall 2026 Minors players in `rosters.json` have a jersey number; the gaps
are players GC lists without one.

### Alternative Solutions

1. **(Chosen)** None needed — GC now serves the pages.
2. Manual `roster_additions` in the season YAML.

---

## KC-004 · [STATUS: Active]

**Title:** Kids sharing initials can't be told apart in play-by-play

**Date Identified:** 2026-04-21

### Exec Description

GameChanger's play-by-play names players by initials, so two kids on one team with the same
initials look identical.

### Eng Description

Box scores give full first names, so `scrape_gc_boxscores._accum_player()` promotes collisions to
5-char keys and writes `_collision_map`; `gen_hitting._disambiguate_pas()` splits batting PAs by
batting-order occurrence. Pitching lines (`"X Y pitching"`) have no batting order to lean on, so
colliding pitchers are combined. Fall 2026 Minors collisions: Cubs-Leonard `D B`, Giants-Hanshaw
`C C` (three kids), Rays-Levengood `T L`.

### Alternative Solutions

1. **(Chosen)** Collision map for batting; label combined pitchers.
2. Manual per-game pitcher overrides in the season YAML.
3. Pull full names from GC's API (would need authenticated API access).

---

## KC-003 · [STATUS: Active]

**Title:** GC box scores include a non-player `TEAM` row

**Date Identified:** 2026-10-26

### Exec Description

Every GameChanger box score has a "TEAM" totals row, which shows up in travel rosters as if it were
a player.

### Eng Description

The row carries team totals (e.g. Blue Jays-Patel `TEAM` so=89, bb=109). Summing per-player box
score stats without excluding it double-counts. Play-by-play never names "TEAM", so reports are
unaffected. Cleanup tracked in [BUG-025 (Enh)](#bug-025-enh--status-o).

### Alternative Solutions

1. **(Chosen, pending)** Skip the row when building rosters — BUG-025 (Enh).
2. Leave it (harmless clutter).

---

## KC-002 · [STATUS: Active]

**Title:** GameChanger only serves a visible, real Chrome window

**Date Identified:** 2026-10-26

### Exec Description

Scraping only works through a real Chrome window on a Mac that is awake and logged in.

### Eng Description

GC's AWS WAF returns 403 to headless and automation-flagged browsers (see
[BUG-022](#bug-022--status-rv)). The scrapers launch real Chrome with the Scout profile, off-screen,
and drive it over CDP. A sleeping, logged-out, or shut-down Mac can't scrape; launchd runs a missed
10am job on wake; screen-locked behavior is untested.

### Alternative Solutions

1. **(Chosen)** Real Chrome + Scout profile + CDP, off-screen window, `caffeinate` during runs.
2. Official GC data export/API, if one becomes available.
3. Run on an always-on, logged-in machine.

---

## KC-001 · [STATUS: Historical]

**Title:** GC switched player-name format mid-season (split player cards)

**Date Identified:** 2026-05-04

### Exec Description

GameChanger changed how it wrote one team's player names partway through the season, so the same
player showed up as two cards. Not a code bug.

### Eng Description

Crushers White 10U used 2-character initials in March (`"A L"`) and full first names from April
(`"Andrew L"`), creating two stat buckets per player. Formerly tracked as `BUG-15b` (Closed — not a
code bug).

### Alternative Solutions

1. **(Chosen)** One-time patch of 7 March game files (`patch_march_initials.py`, retired in v3.0.0).
2. Index rosters under both name formats (done for jerseys in [BUG-011](#bug-011--status-rv)).
