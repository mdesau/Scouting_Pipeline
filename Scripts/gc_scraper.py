#!/usr/bin/env python3
"""
gc_scraper.py — GameChanger DOM Scraper for WCWAA 2026 Spring
=============================================================
Navigates every game's /plays page via Playwright, extracts
play-by-play text from the React DOM, converts it to WCWAA format
via parse_gc_raw(), and saves .txt files to the correct folder.

Covers all four divisions: Majors, Minors, Wild, Storm.

Usage
-----
# First time only — opens a real browser window for you to log in
python3 gc_scraper.py --login

# All subsequent runs — fully automated, browser hidden
python3 gc_scraper.py

# One division only
python3 gc_scraper.py --division Majors
python3 gc_scraper.py --division Storm

# One team only
python3 gc_scraper.py --team "Braves-Rue"
python3 gc_scraper.py --team "ITAA 9U Spartans"

# Check which games are missing without scraping (safe, read-only)
python3 gc_scraper.py --check
python3 gc_scraper.py --check --division Minors --team Rangers

# Force re-scrape even if .txt or -Reviewed.txt already exists
python3 gc_scraper.py --force

Setup (one time)
-----
pip3 install playwright --break-system-packages
playwright install chromium
"""

import argparse
import logging
import re
import time
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("ERROR: playwright not installed.")
    print("Run: pip3 install playwright --break-system-packages && playwright install chromium")
    raise

from parse_gc_text import parse_gc_raw

# ─────────────────────────────────────────────────────────────
# DEBUG CONFIGURATION
# ─────────────────────────────────────────────────────────────
# These flags enable expensive debug output that is too verbose for normal runs
# but invaluable when diagnosing GC DOM changes or scraping failures.
#
# HOW TO USE:
#   For light debugging: run with --verbose (shows all logger.debug messages)
#   For heavy debugging: flip a flag below to True, then run normally.
#
# WHY FLAGS INSTEAD OF JUST --verbose:
#   --verbose shows targeted debug messages (game skips, date parsing, etc.)
#   These flags dump RAW DATA (full JS output, full page text) which can be
#   hundreds of lines — you only want that when hunting a specific issue.
# ─────────────────────────────────────────────────────────────
DEBUG_SCHEDULE_RAW = False   # Dump full SCHEDULE_JS return (every game card's raw fields)
DEBUG_PAGE_TEXT    = False   # Dump raw page text from each /plays page before parsing

SPRING_DIR = Path(
    "~/Library/CloudStorage/GoogleDrive-mdesau@gmail.com"
    "/My Drive/Baseball/WCWAA/2026/Spring"
).expanduser()

GC_BASE_URL  = "https://web.gc.com"
SESSION_FILE = Path(__file__).parent / "gc_session.json"
LOGS_DIR     = Path(__file__).parent.parent / "Logs"

# ─────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────

def setup_logging(verbose=False):
    """Configure logging to both stdout and a dated log file.

    Args:
        verbose: If True, stdout handler is set to DEBUG level (shows all
                 debug messages on screen). Default is INFO-only on screen;
                 DEBUG always goes to the log file regardless.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"gc_scraper_{stamp}.log"

    fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                            datefmt="%H:%M:%S")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt); fh.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt); sh.setLevel(logging.DEBUG if verbose else logging.INFO)

    log = logging.getLogger("gc_scraper")
    log.setLevel(logging.DEBUG)
    log.addHandler(fh)
    log.addHandler(sh)
    log.info(f"Log → {log_path}")
    return log

logger = logging.getLogger("gc_scraper")
logger.addHandler(logging.NullHandler())

# Majors and Minors: org-based schedule URLs
# Wild and Storm:    team-based schedule URLs
DIVISIONS = {
    "Majors": {
        "type":      "org",
        "id":        "1CMI2BBazG8C",
        "output":    SPRING_DIR / "Majors" / "Reports" / "Scorebooks",
        "label":     "Majors",
    },
    "Minors": {
        "type":      "org",
        "id":        "GdcFopba2PbE",
        "output":    SPRING_DIR / "Minors" / "Reports" / "Scorebooks",
        "label":     "Minors",
    },
    # ── Wild opponents ────────────────────────────────────────────────────────
    # To add a new opponent:
    #   1. Go to their schedule page on GameChanger
    #   2. Copy the URL — it looks like:
    #      https://web.gc.com/teams/{team_id}/{slug}/schedule
    #   3. Add one line below:  ("team_id", "slug", "Exact Folder Name")
    #      The folder name must exactly match the team name in their GC inning headers.
    # ─────────────────────────────────────────────────────────────────────────
    "Wild": {
        "type":   "teams",
        "teams":  [
            ("1yv2qtI89QSD", "2026-spring-arena-national-browning-11u", "Arena National Browning 11U"),
            ("Kih0oavXNZB3", "2026-spring-south-charlotte-panthers-11u", "South Charlotte Panthers 11U"),
            ("Ye94sB963tUX", "2026-spring-weddington-wild-11u",          "Weddington Wild 11U"),
            ("1gqDRuls0oER", "2026-spring-qc-flight-baseball-11u",          "QC Flight Baseball 11U"),
            ("I2XcyUwmye3p", "2026-spring-t24-garnet-11u",                   "T24 Garnet 11U"),
            ("Wn2Abf32IXOz", "2026-summer-sba-alabama-national-12u",         "SBA Alabama National 12U"),
            ("QebtI4WHVMPn", "2026-summer-tn-nationals-heichelbech-12u",     "TN Nationals Heichelbech 12U"),
        ],
        "output_base": SPRING_DIR / "Wild",
        "label":       "Wild",
    },
    # ── Storm opponents ───────────────────────────────────────────────────────
    # Same format as Wild above. Add new ITAA 9U travel opponents here.
    # ─────────────────────────────────────────────────────────────────────────
    "Storm": {
        "type":   "teams",
        "teams":  [
            ("lTxYlYLH52KU", "2026-spring-itaa-9u-spartans",  "ITAA 9U Spartans"),
            ("VdoWDJdlCgAH", "2026-spring-mara-9u-stingers",  "MARA 9U Stingers"),
            ("lc7rtdls8Ht6", "2026-spring-south-charlotte-challenge-9u-doggett", "South Charlotte Challenge 9U Doggett"),
            ("igECV1q4jzFV", "2026-spring-pineville-blue-sox-9u", "Pineville Blue Sox 9U"),
        ],
        "output_base": SPRING_DIR / "Storm",
        "label":       "Storm",
    },
}

# ─────────────────────────────────────────────────────────────
# JAVASCRIPT — runs inside the browser page
# ─────────────────────────────────────────────────────────────

# Extracts raw page text from a /plays page (same approach as get_page_text)
EXTRACT_PLAYS_JS = "() => document.body.innerText"

# Discovers all game UUIDs from a schedule page (works for both org and team pages).
#
# WHY THE REWRITE (2026-04-21):
#   GC's schedule page no longer has full-date header elements like "Saturday March 21, 2026".
#   Instead it shows month headers ("March 2026") and embeds the day only in the FIRST
#   game card of each new date (e.g. lines = ['Sat', '21', 'TeamA', '@ TeamB', ...]).
#   Same-day subsequent games omit the date entirely from their card.
#
#   Fixes applied:
#   1. Track month/year headers ("March 2026") for the month component of the date.
#   2. Detect day-abbr + day-number at the start of a game card; carry that date
#      forward for same-day games that lack a date prefix.
#   3. Return 'away' and 'home' as separate clean fields (strips leading '@ ').
SCHEDULE_JS = """
() => {
    const uuidRe = /\\/schedule\\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/;
    const results = [];
    const seen = new Set();

    const MONTH_ABBR = {
        'January':'Jan','February':'Feb','March':'Mar','April':'Apr',
        'May':'May','June':'Jun','July':'Jul','August':'Aug',
        'September':'Sep','October':'Oct','November':'Nov','December':'Dec'
    };
    // Uppercase day abbreviations used on team pages (SUN, SAT, MON, etc.)
    const DAY_ABBRS_UPPER = new Set(['MON','TUE','WED','THU','FRI','SAT','SUN']);
    // Title-case day abbreviations used on org pages inside card lines
    const DAY_ABBRS_TITLE = new Set(['Mon','Tue','Wed','Thu','Fri','Sat','Sun']);

    let currentMonthYear = '';  // e.g. 'March 2026'
    let currentDateTag   = '';  // e.g. 'Mar21' — carried forward for same-day games
    let pendingDayAbbr   = '';  // uppercase day seen outside a card (team pages)

    document.body.querySelectorAll('*').forEach(el => {
        if (el.children.length === 0 && el.innerText) {
            const t = el.innerText.trim();

            // Month/year section headers: 'March 2026'
            if (/^(January|February|March|April|May|June|July|August|September|October|November|December) \\d{4}$/.test(t)) {
                currentMonthYear = t;
                return;
            }

            // Team-page date layout: day-abbr (MON/TUE/...) and day-number appear
            // as SEPARATE leaf nodes OUTSIDE the <a> card.
            // We capture them here so they're available when the card link is processed.
            if (DAY_ABBRS_UPPER.has(t)) {
                pendingDayAbbr = t;
                return;
            }
            // Day number follows immediately after the day-abbr leaf node
            if (pendingDayAbbr && /^\\d{1,2}$/.test(t)) {
                const monthParts = currentMonthYear.split(' ');
                const abbr = MONTH_ABBR[monthParts[0]] || monthParts[0].slice(0, 3);
                currentDateTag = abbr + t.padStart(2, '0');
                pendingDayAbbr = '';  // consumed
                return;
            }
            // Any non-digit non-day-abbr resets the pending day abbr
            // (prevents stale day-abbr sticking across month boundaries)
            if (pendingDayAbbr && !/^\\d{1,2}$/.test(t)) {
                pendingDayAbbr = '';
            }
        }

        if (el.tagName === 'A') {
            const m = el.href.match(uuidRe);
            if (m && !seen.has(m[1])) {
                seen.add(m[1]);
                const lines = el.innerText.trim().split('\\n').map(x => x.trim()).filter(x => x);

                // Org-page card layout: day-abbr + day-number INSIDE the card as first two lines
                // e.g. ['Sat', '21', 'Marlins-Eberlin', '@ Angels-Casper', 'FINAL', ...]
                // Team-page card layout: ['vs. TeamName', 'location', 'W 7-5']
                //   — date is already in currentDateTag from the leaf-node detection above
                let offset = 0;
                if (lines.length >= 2 && DAY_ABBRS_TITLE.has(lines[0]) && /^\\d{1,2}$/.test(lines[1])) {
                    // Org page — date embedded in card
                    offset = 2;
                    const monthParts = currentMonthYear.split(' ');
                    const abbr = MONTH_ABBR[monthParts[0]] || monthParts[0].slice(0, 3);
                    currentDateTag = abbr + lines[1].padStart(2, '0');
                }
                // If offset=0 (team page), currentDateTag was already set by leaf-node scan above.
                // Same-day subsequent cards: currentDateTag carries forward automatically.

                // On team pages lines[0] = 'vs. TeamName' or '@ TeamName'
                // On org pages  lines[offset] = 'TeamA', lines[offset+1] = '@ TeamB'
                // We clean vs./@ prefixes from both.
                const rawAway = lines[offset]    || 'Away';
                const rawHome = lines[offset + 1] || '';
                const away = rawAway.replace(/^(vs\\.\\s*|@\\s*)/, '');
                // On team pages home is the location string — skip it; use our team name instead
                // On org pages home is '@ TeamName'
                const home = rawHome.replace(/^@\\s*/, '');                // is_home: true if the card starts with 'vs.' (we are home team on team pages)
                // On org pages this field is unused — away/home are already correct absolute names.
                const is_home = rawAway.startsWith('vs.');
                results.push({
                    date:    currentDateTag,
                    id:      m[1],
                    away:    away,
                    home:    home,
                    is_home: is_home,   // true = we are home (card said 'vs.'); false = we are away ('@')
                    text:    lines.join(' | '),   // kept for debugging
                    // WHY TWO CONDITIONS:
                    // Org pages (Majors/Minors) show 'FINAL' as explicit text.
                    // Team pages (Wild/Storm) show a score like 'W 7-5' or 'L 9-11'
                    // instead of 'FINAL' — no 'FINAL' text ever appears on those pages.
                    // A score pattern means the game is over and has play-by-play data.
                    final: lines.includes('FINAL') ||
                           lines.some(l => /^[WL]\\s+\\d+-\\d+/.test(l))

                });
            }
        }
    });
    return results;
}
"""

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def fmt_date(date_str):
    """'Saturday March 21, 2026' → 'Mar21'"""
    try:
        dt = datetime.strptime(date_str, "%A %B %d, %Y")
        return dt.strftime("%b") + str(dt.day)
    except Exception:
        return re.sub(r'.*?(\w{3})\w*\s+(\d+),.*', r'\1\2', date_str)


def safe(name):
    """Make name safe for use in filenames."""
    return re.sub(r"[/\\:*?\"<>|']", '', name).replace(' ', '_')


def get_schedule(page, url):
    """Load a schedule page and return list of game dicts."""
    logger.info(f"  Loading: {url}")
    page.goto(url, wait_until="networkidle", timeout=30_000)
    time.sleep(2)
    games = page.evaluate(SCHEDULE_JS) or []
    logger.debug(f"  Schedule returned {len(games)} game cards")
    if DEBUG_SCHEDULE_RAW:
        for g in games:
            logger.debug(f"    RAW: date={g.get('date')!r}  away={g.get('away')!r}  "
                         f"home={g.get('home')!r}  final={g.get('final')}  "
                         f"text={g.get('text')!r}")
    return games


def extract_plays_raw(page, plays_url):
    """Navigate to a /plays page and return raw body text, or None on failure."""
    try:
        page.goto(plays_url, wait_until="networkidle", timeout=30_000)
        page.wait_for_selector('.BatsPlays__play', timeout=12_000)
    except PWTimeout:
        logger.debug(f"    Timeout waiting for .BatsPlays__play on {plays_url}")
        return None
    except Exception as e:
        logger.error(f"    [error] {e}")
        return None
    time.sleep(0.5)
    return page.evaluate(EXTRACT_PLAYS_JS)


# ─────────────────────────────────────────────────────────────
# SCRAPE LOGIC
# ─────────────────────────────────────────────────────────────

def is_covered(out_dir, fname):
    """Return True if fname or its -Reviewed.txt variant already exists."""
    reviewed = fname.replace(".txt", "-Reviewed.txt")
    return (out_dir / fname).exists() or (out_dir / reviewed).exists()


def scrape_org_division(page, div_name, cfg, team_filter, force, check_only=False):
    """Scrape all FINAL games for a Majors or Minors division.

    check_only: if True, print missing games and return without scraping.
    """
    org_id   = cfg["id"]
    out_dir  = cfg["output"]
    out_dir.mkdir(parents=True, exist_ok=True)

    sched_url = f"{GC_BASE_URL}/organizations/{org_id}/schedule"
    games = get_schedule(page, sched_url)
    final_games = [g for g in games if g.get("final")]
    logger.info(f"  {len(final_games)} FINAL games found on schedule")

    scraped = skipped = failed = missing = 0
    for g in final_games:
        # SCHEDULE_JS now returns away/home as separate fields — no more splitting
        # the joined text string. date is already formatted as 'Mar21', 'Apr01', etc.
        date_tag = g.get("date", "")      # e.g. 'Mar21'
        game_id  = g["id"]
        away = safe(g.get("away", "Away"))
        home = safe(g.get("home", "Home"))
        # Strip division suffix from team names (e.g. 'Cubs_Majors' → 'Cubs')
        away = re.sub(r'_(Majors|Minors)$', '', away)
        home = re.sub(r'_(Majors|Minors)$', '', home)

        if team_filter and team_filter.lower() not in away.lower() and team_filter.lower() not in home.lower():
            continue

        fname = f"{date_tag}-{away}_vs_{home}.txt"

        if check_only:
            if not is_covered(out_dir, fname):
                plays_url = f"{GC_BASE_URL}/organizations/{org_id}/schedule/{game_id}/plays"
                logger.info(f"  [MISSING] {fname}  →  {plays_url}")
                missing += 1
            else:
                logger.debug(f"  [ok]      {fname}")
            continue

        if is_covered(out_dir, fname) and not force:
            logger.debug(f"  [skip] {fname}")
            skipped += 1
            continue

        plays_url = f"{GC_BASE_URL}/organizations/{org_id}/schedule/{game_id}/plays"
        logger.info(f"  Scraping {date_tag} {away} vs {home} …")

        raw_text = extract_plays_raw(page, plays_url)
        if not raw_text or "No Plays Yet" in raw_text:
            logger.warning(f"  NO PLAYS — {date_tag} {away} vs {home}")
            failed += 1
            continue

        converted = parse_gc_raw(raw_text, game_url=plays_url, game_date=date_tag)
        (out_dir / fname).write_text(converted, encoding="utf-8")
        logger.info(f"  OK → {fname}")
        scraped += 1
        time.sleep(0.3)

    if check_only:
        if missing == 0:
            logger.info(f"  ✓ All {div_name} games covered (no missing scorebooks)")
        else:
            logger.info(f"  ⚠ {missing} game(s) missing from Scorebooks — run without --check to scrape them")
        return 0, 0, 0

    return scraped, skipped, failed


def scrape_team_division(page, div_name, cfg, team_filter, force, check_only=False):
    """Scrape all FINAL games for a Wild or Storm team-based division.

    check_only: if True, print missing games and return without scraping.
    """
    out_base = cfg["output_base"]
    scraped = skipped = failed = 0

    for team_id, slug, team_name in cfg["teams"]:
        if team_filter and team_filter.lower() not in team_name.lower():
            continue

        try:
            out_dir = out_base / team_name / "Games"
            out_dir.mkdir(parents=True, exist_ok=True)

            sched_url = f"{GC_BASE_URL}/teams/{team_id}/{slug}/schedule"
            games = get_schedule(page, sched_url)
            final_games = [g for g in games if g.get("final")]
            logger.info(f"  {team_name}: {len(final_games)} FINAL games found")

            missing = 0
            for g in final_games:
                date_tag  = g.get("date", "")      # e.g. 'Mar21'
                game_id   = g["id"]
                opponent  = safe(g.get("away", "Opponent"))  # opponent name (vs./@ stripped by JS)
                our_team  = safe(team_name)

                # is_home=True  → card said 'vs. Opponent' → we are home team
                #                  filename: opponent_vs_ourTeam
                # is_home=False → card said '@ Opponent'   → we are away team
                #                  filename: ourTeam_vs_opponent
                if g.get("is_home", False):
                    fname = f"{date_tag}-{opponent}_vs_{our_team}.txt"
                else:
                    fname = f"{date_tag}-{our_team}_vs_{opponent}.txt"

                if check_only:
                    if not is_covered(out_dir, fname):
                        plays_url = f"{GC_BASE_URL}/teams/{team_id}/{slug}/schedule/{game_id}/plays"
                        logger.info(f"  [MISSING] {fname}  →  {plays_url}")
                        missing += 1
                    else:
                        logger.debug(f"  [ok]      {fname}")
                    continue

                if is_covered(out_dir, fname) and not force:
                    logger.debug(f"  [skip] {fname}")
                    skipped += 1
                    continue

                plays_url = f"{GC_BASE_URL}/teams/{team_id}/{slug}/schedule/{game_id}/plays"
                logger.info(f"  Scraping {date_tag} {fname} …")

                raw_text = extract_plays_raw(page, plays_url)
                if not raw_text or "No Plays Yet" in raw_text:
                    logger.warning(f"  NO PLAYS — {fname}")
                    failed += 1
                    continue

                converted = parse_gc_raw(raw_text, game_url=plays_url, game_date=date_tag)
                (out_dir / fname).write_text(converted, encoding="utf-8")
                logger.info(f"  OK → {fname}")
                scraped += 1
                time.sleep(0.3)

            if check_only and missing == 0:
                logger.info(f"  ✓ {team_name}: all games covered")

        except Exception as exc:
            logger.error(f"  ⚠ {team_name} failed: {exc}")
            failed += 1

    return scraped, skipped, failed


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def run(login_mode=False, divisions_filter=None, team_filter=None, force=False, check_only=False, verbose=False):
    setup_logging(verbose=verbose)
    with sync_playwright() as pw:
        if login_mode:
            browser = pw.chromium.launch(headless=False)
            ctx = browser.new_context()
        elif SESSION_FILE.exists():
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(storage_state=str(SESSION_FILE))
        else:
            browser = pw.chromium.launch(headless=False)
            ctx = browser.new_context()
            logger.warning("No saved session — browser opened. Log in to https://web.gc.com then press ENTER.")
            input()

        page = ctx.new_page()

        if login_mode:
            page.goto(f"{GC_BASE_URL}/teams")
            logger.info("Log in to GameChanger in the browser window that just opened.")
            logger.info("Once you can see your teams page, press ENTER here.")
            input()
            ctx.storage_state(path=str(SESSION_FILE))
            logger.info(f"Session saved → {SESSION_FILE}")

        if check_only:
            logger.info("MODE: --check only (no files will be written)")

        total_s = total_sk = total_f = 0

        for div_name, cfg in DIVISIONS.items():
            if divisions_filter and div_name not in divisions_filter:
                continue
            if cfg["type"] == "teams" and not cfg.get("teams"):
                logger.info(f"\n[{div_name}] No teams configured — skipping.")
                continue

            logger.info(f"\n{'─'*55}")
            logger.info(f"Division: {div_name}")

            try:
                if cfg["type"] == "org":
                    s, sk, f = scrape_org_division(page, div_name, cfg, team_filter, force, check_only)
                else:
                    s, sk, f = scrape_team_division(page, div_name, cfg, team_filter, force, check_only)
                total_s += s; total_sk += sk; total_f += f
            except Exception as exc:
                logger.error(f"  ⚠ {div_name} failed: {exc}")
                total_f += 1

        ctx.storage_state(path=str(SESSION_FILE))
        browser.close()

    logger.info(f"\n{'='*55}")
    if check_only:
        logger.info("Check complete. Run without --check to scrape any missing games.")
    else:
        logger.info(f"Done.  Scraped: {total_s}  Skipped: {total_sk}  Failed: {total_f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WCWAA GameChanger Scraper")
    parser.add_argument("--login",      action="store_true",
                        help="Open browser for manual login and save session")
    parser.add_argument("--division",   nargs="+", choices=["Majors","Minors","Wild","Storm"],
                        help="Only scrape these divisions (default: all)")
    parser.add_argument("--team",       default=None,
                        help="Only scrape games involving this team name")
    parser.add_argument("--force",      action="store_true",
                        help="Re-scrape even if .txt or -Reviewed.txt already exists")
    parser.add_argument("--check",      action="store_true",
                        help="Check which games are missing from Scorebooks without scraping")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show DEBUG-level messages on screen (normally only written to log file)")
    args = parser.parse_args()

    run(
        login_mode=args.login,
        divisions_filter=args.division,
        team_filter=args.team,
        force=args.force,
        check_only=args.check,
        verbose=args.verbose,
    )
