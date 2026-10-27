"""
gc_browser.py — shared real-Chrome access to GameChanger (see BUG-022)
=====================================================================
GameChanger's firewall (AWS WAF) returns HTTP 403 to every headless or
Playwright-launched browser. It only serves a normal, visible Google Chrome
window. So every GC page load goes through here:

  1. Launch /Applications/Google Chrome.app as a plain process, using the
     dedicated Scout profile (data/real/sessions/gc_chrome_profile) that
     holds the GC login, with a local-only DevTools (CDP) port.
  2. Playwright attaches over CDP and drives the page (navigate, read text).
  3. Chrome is closed gracefully when done so the profile is flushed to disk.

Public API
----------
gc_chrome(log, on_screen=False)  context manager → Playwright Page
check_session(page, log)         → "ok" | "signed_out" | "blocked"
login(log)                       interactive sign-in (user types password in Chrome)
"""

import socket
import subprocess
import time
import urllib.request
from contextlib import contextmanager
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

from scout.season_config import SESSIONS_DIR

GC_BASE_URL = "https://web.gc.com"
GC_API_HOST = "api.team-manager.gc.com"
CHROME_APP = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE_DIR = SESSIONS_DIR / "gc_chrome_profile"
CDP_PORT = 9223
_CDP_URL = f"http://127.0.0.1:{CDP_PORT}"
_STARTUP_TIMEOUT_S = 20

# Off-screen keeps the window "visible" to Chrome/GC but out of the user's way.
_OFFSCREEN_POSITION = "-2400,0"

SESSION_OK = "ok"
SESSION_SIGNED_OUT = "signed_out"
SESSION_BLOCKED = "blocked"


class ChromeLaunchError(RuntimeError):
    pass


def _cdp_ready():
    try:
        with urllib.request.urlopen(f"{_CDP_URL}/json/version", timeout=1):
            return True
    except OSError:
        return False


def _port_in_use():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", CDP_PORT)) == 0


def _launch_chrome(on_screen):
    if _port_in_use():
        raise ChromeLaunchError(
            f"Port {CDP_PORT} is already in use — is another Scout run (or Scout Chrome) "
            "still open? Close it and retry."
        )
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    args = [
        CHROME_APP,
        f"--user-data-dir={PROFILE_DIR}",
        f"--remote-debugging-port={CDP_PORT}",
        "--remote-debugging-address=127.0.0.1",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1280,900",
        # Keep pages running at full speed when the window is behind others.
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
    ]
    if not on_screen:
        args.append(f"--window-position={_OFFSCREEN_POSITION}")
    args.append("about:blank")
    try:
        proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError as exc:
        raise ChromeLaunchError(f"Google Chrome not found at {CHROME_APP}") from exc

    deadline = time.time() + _STARTUP_TIMEOUT_S
    while time.time() < deadline:
        if _cdp_ready():
            return proc
        if proc.poll() is not None:
            raise ChromeLaunchError(
                "Chrome exited immediately — the Scout profile may already be open in "
                "another Chrome window. Close it and retry."
            )
        time.sleep(0.25)
    proc.terminate()
    raise ChromeLaunchError(f"Chrome did not open its control port within {_STARTUP_TIMEOUT_S}s")


@contextmanager
def gc_chrome(log, on_screen=False):
    """Yield a Playwright Page driving a real Chrome window on the Scout profile."""
    proc = _launch_chrome(on_screen)
    log.debug(f"Scout Chrome started (pid {proc.pid}, on_screen={on_screen})")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(_CDP_URL)
            ctx = browser.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            try:
                yield page
            finally:
                try:
                    browser.new_browser_cdp_session().send("Browser.close")
                except Exception:
                    pass
    finally:
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.terminate()
        log.debug("Scout Chrome closed")


def classify_session(page_text, page_url, api_statuses):
    """Decide session state from the /teams page text, final URL, and GC API statuses."""
    text = (page_text or "").casefold()
    if "/login" in (page_url or "") or "sign in to gamechanger" in text:
        return SESSION_SIGNED_OUT
    if 401 in api_statuses.values():
        return SESSION_SIGNED_OUT
    if 403 in api_statuses.values() or "couldn't load your account" in text:
        return SESSION_BLOCKED
    if api_statuses.get("/me/user") == 200:
        return SESSION_OK
    return SESSION_BLOCKED


def check_session(page, log):
    """Load GC's teams page and report whether the Scout profile is signed in and served."""
    api_statuses = {}

    def _track(response):
        parts = urlsplit(response.url)
        if parts.hostname == GC_API_HOST and parts.path.startswith("/me/"):
            api_statuses[parts.path] = response.status

    page.on("response", _track)
    try:
        page.goto(f"{GC_BASE_URL}/teams", wait_until="networkidle", timeout=30000)
    except Exception as exc:
        log.warning(f"GC teams page did not finish loading: {exc}")
    finally:
        page.remove_listener("response", _track)
    state = classify_session(page.locator("body").inner_text(), page.url, api_statuses)
    log.debug(f"Session check: {state}  api={api_statuses}")
    return state


SESSION_MESSAGES = {
    SESSION_OK: "GameChanger session OK.",
    SESSION_SIGNED_OUT: (
        "GameChanger session expired — run:  "
        "python -m scout.scraping.scrape_gc_playbyplay --login"
    ),
    SESSION_BLOCKED: (
        "GameChanger refused the Scout browser (blocked or account failed to load). "
        "See BUG-022 in docs/BUGS.md."
    ),
}


def login(log):
    """Open Scout Chrome on screen, let the user sign in, then verify the session."""
    with gc_chrome(log, on_screen=True) as page:
        page.goto(f"{GC_BASE_URL}/teams", wait_until="domcontentloaded")
        log.info("Sign in to GameChanger in the Chrome window that just opened.")
        log.info("Once you can see your teams page, press ENTER here.")
        input()
        state = check_session(page, log)
    (log.info if state == SESSION_OK else log.error)(SESSION_MESSAGES[state])
    return EXIT_CODES[state]


# Process exit codes shared by the scrapers; run_menu keys off these.
EXIT_CODES = {SESSION_OK: 0, SESSION_SIGNED_OUT: 2, SESSION_BLOCKED: 3}


def run_with_session(log, work):
    """Open Scout Chrome, verify the GC session, then call work(page). Returns an exit code."""
    try:
        with gc_chrome(log) as page:
            state = check_session(page, log)
            if state != SESSION_OK:
                log.error(SESSION_MESSAGES[state])
                return EXIT_CODES[state]
            work(page)
    except ChromeLaunchError as exc:
        log.error(f"Could not start Scout Chrome: {exc}")
        return EXIT_CODES[SESSION_BLOCKED]
    return 0
