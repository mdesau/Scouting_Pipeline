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
# CONFIGURATION — edit paths here if your folder structure changes
# ─────────────────────────────────────────────────────────────

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

def setup_logging():
    """Configure logging to both stdout and a dated log file."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"gc_scraper_{stamp}.log"

    fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                            datefmt="%H:%M:%S")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt); fh.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt); sh.setLevel(logging.INFO)

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
            # QC Flight Baseball 11U — team_id needed; find at web.gc.com/teams/[ID]/[slug]/schedule
            # ("TEAM_ID",   "2026-spring-qc-flight-baseball-11u",        "QC Flight Baseball 11U"),
            # T24 Garnet 11U — scouting in progress (Spring 2026)
            ("I2XcyUwmye3p", "2026-spring-t24-garnet-11u",               "T24 Garnet 11U"),
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
            ("XIMp3aUceUsY", "2026-spring-militia-9u",         "MILITIA 9U"),
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

# Discovers all game UUIDs from a schedule page (works for both org and team pages)
SCHEDULE_JS = """
() => {
    const uuidRe = /\\/schedule\\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/;
    const results = [];
    const seen = new Set();
    let currentDate = '';

    document.body.querySelectorAll('*').forEach(el => {
        if (el.children.length === 0 && el.innerText) {
            const t = el.innerText.trim();
            if (/^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) \\w+ \\d+, \\d{4}$/.test(t)) {
                currentDate = t;
            }
        }
        if (el.tagName === 'A') {
            const m = el.href.match(uuidRe);
            if (m && !seen.has(m[1])) {
                seen.add(m[1]);
                const lines = el.innerText.trim().split('\\n').map(x => x.trim()).filter(x => x);
                results.push({
                    date: currentDate,
                    id: m[1],
                    text: lines.join(' | '),
                    final: lines.includes('FINAL')
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
    return page.evaluate(SCHEDULE_JS) or []


def extract_plays_raw(page, plays_url):
    """Navigate to a /plays page and return raw body text, or None on failure."""
    try:
        page.goto(plays_url, wait_until="networkidle", timeout=30_000)
        page.wait_for_selector('.BatsPlays__play', timeout=12_000)
    except PWTimeout:
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
        text_raw = g.get("text", "")
        date_tag = fmt_date(g.get("date", ""))
        game_id  = g["id"]

        # Parse "Away | @ | Home | FINAL | score..." from schedule card text
        parts = [p.strip() for p in text_raw.split('|')]
        away = safe(parts[0]) if len(parts) > 0 else "Away"
        home = safe(parts[1].lstrip('@').strip()) if len(parts) > 1 else "Home"
        # Strip division suffix from team names
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

        out_dir = out_base / team_name / "Games"
        out_dir.mkdir(parents=True, exist_ok=True)

        sched_url = f"{GC_BASE_URL}/teams/{team_id}/{slug}/schedule"
        games = get_schedule(page, sched_url)
        final_games = [g for g in games if g.get("final")]
        logger.info(f"  {team_name}: {len(final_games)} FINAL games found")

        missing = 0
        for g in final_games:
            date_tag = fmt_date(g.get("date", ""))
            game_id  = g["id"]
            text_raw = g.get("text", "")

            # Try to extract away/home from schedule card text
            parts = [p.strip() for p in text_raw.split('|')]
            away = safe(parts[0]) if len(parts) > 0 else "Away"
            home = safe(parts[1].lstrip('@').strip()) if len(parts) > 1 else "Home"

            fname = f"{date_tag}-{away}_vs_{home}.txt"

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

        if check_only and missing == 0:
            logger.info(f"  ✓ {team_name}: all games covered")

    return scraped, skipped, failed


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def run(login_mode=False, divisions_filter=None, team_filter=None, force=False, check_only=False):
    setup_logging()
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

            if cfg["type"] == "org":
                s, sk, f = scrape_org_division(page, div_name, cfg, team_filter, force, check_only)
            else:
                s, sk, f = scrape_team_division(page, div_name, cfg, team_filter, force, check_only)

            total_s += s; total_sk += sk; total_f += f

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
    args = parser.parse_args()

    run(
        login_mode=args.login,
        divisions_filter=args.division,
        team_filter=args.team,
        force=args.force,
        check_only=args.check,
    )
