#!/usr/bin/env python3
"""
server.py — Local web UI for the WCWAA Scout Pipeline
=============================================================================

WHAT THIS IS
────────────
A small Flask web server that puts a clean, friendly graphical front-end on
top of the existing scouting pipeline. It is the visual replacement for the
text-based menu in run_menu.py — same capabilities, nicer experience:

  • Pick a division → pick a team → click "Build Reports"   (live log streams)
  • Browse every existing report and open the PDF in one click
  • Add a new Wild / Storm opponent from a GameChanger URL
  • Switch between seasons or create a new season from the Seasons tab

WHY A LOCAL SERVER (AND NOT A PLAIN HTML FILE)?
───────────────────────────────────────────────
A browser cannot run Python for security reasons — a static .html file on
Google Drive can DISPLAY things but can never SCRAPE GameChanger or BUILD a
PDF. Those steps need Python + Playwright + the project's virtualenv, which
only exist on this Mac. So:

  • This server runs locally on the Mac (http://127.0.0.1:5050) and is the
    ONLY place reports can be built. It reuses the proven pipeline by shelling
    out to run_menu.py (the exact same path the terminal menu and the nightly
    cron job use — see WHY SUBPROCESS below).

  • The generated PDFs live in the Google-Drive-synced seasons/ folder, so
    they are automatically available on any device (including a phone) through
    the native Google Drive app. Mobile = view-only by nature, which matches
    how the pipeline is used: build on the Mac, view anywhere.

WHY SHELL OUT TO run_menu.py INSTEAD OF IMPORTING run_pipeline()?
──────────────────────────────────────────────────────────────────
run_pipeline() prints progress to stdout and each underlying script configures
its own argparse + logging. Running `run_menu.py --division X --team Y` as a
subprocess:
  • Streams live progress to the web page line-by-line (Server-Sent Events)
  • Avoids logging-config conflicts between scripts inside one process
  • Reuses the SINGLE proven code path (DRY) — no second copy of pipeline logic
  • Cannot wedge the web server if a scraper hangs (it is an isolated process)

DEBUG / CONFIG FLAGS
────────────────────
  HOST / PORT  — where the server listens (loopback only by default = private).
  DEBUG        — Flask auto-reload + verbose tracebacks. Off by default.
  Set SCOUT_WEB_HOST=0.0.0.0 to expose the build UI to other devices on your
  Wi-Fi (e.g. reach it from a phone on the same network). Off by default
  because binding to all interfaces is a wider surface than loopback.
"""

import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

from flask import (
    Flask, Response, jsonify, request,
    send_file, send_from_directory, abort,
)

# ---------------------------------------------------------------------------
# PATH BOOTSTRAP — locate season_config.py + run_menu.py helpers in src/
# ---------------------------------------------------------------------------
# This file lives at src/web/server.py.
#   season_config.py  → src/             (one level up)
#   run_menu.py       → src/orchestrator/
# Adding both to sys.path lets us import the shared, already-tested helpers
# instead of duplicating any logic here.
_SRC_DIR = Path(__file__).resolve().parent.parent          # → Scout/src/
for _p in (str(_SRC_DIR), str(_SRC_DIR / "orchestrator")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from season_config import (  # noqa: E402
    SCOUT_ROOT, SEASON_DIR, SEASON_ID,
    build_scraper_divisions, add_team_to_yaml,
    list_seasons, set_active_season, create_season,
)
# Reuse the menu's helpers verbatim (DRY): team listing, URL parsing, folder
# naming. These are pure functions with no interactive side effects.
from run_menu import (  # noqa: E402
    get_team_list, _parse_gc_url, _slug_to_folder_name,
)

# ── Config flags ────────────────────────────────────────────────────────────
HOST = os.environ.get("SCOUT_WEB_HOST", "127.0.0.1")  # loopback only by default
PORT = int(os.environ.get("SCOUT_WEB_PORT", "5050"))
DEBUG = os.environ.get("SCOUT_WEB_DEBUG", "0") == "1"

# Version string stamped on every response as X-Scout-Version.
# The web UI reads this header during boot to detect stale server processes
# (a server started before a code update that added new API endpoints).
# Bump this whenever a new API endpoint is added. See BUG-19.
SERVER_VERSION = "3.3.2"

# Ordered list of divisions to surface in the UI. Mirrors the pipeline's order.
DIVISION_ORDER = ["Majors", "Minors", "Wild", "Storm"]

# Path to run_menu.py — the single entry point we shell out to for every build.
RUN_MENU = _SRC_DIR / "orchestrator" / "run_menu.py"

# ── Run lock ────────────────────────────────────────────────────────────────
# Only one build may run at a time. A second request while a build is active
# gets a clear "busy" response instead of two scrapers fighting over the same
# GameChanger session file and the same output PDFs.
_run_lock = threading.Lock()

# Flask serves index.html + css/ + js/ straight out of this folder.
_WEB_DIR = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=None)


@app.after_request
def _add_version_header(response):
    """Stamp every response with the server version.

    WHY: Python loads server.py once at startup. If the source file is updated
    (e.g. after a git pull) the running process is stale — it will lack any
    new API endpoints added in the update. The X-Scout-Version header lets
    the browser-side code detect this mismatch and show a restart prompt
    instead of silently leaving season dropdowns empty. See BUG-19.
    """
    response.headers["X-Scout-Version"] = SERVER_VERSION
    return response


# ════════════════════════════════════════════════════════════════════════════
# STATIC PAGES
# ════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Serve the single-page app shell."""
    return send_from_directory(_WEB_DIR, "index.html")


@app.route("/css/<path:filename>")
def css(filename):
    """Serve stylesheets from src/web/css/."""
    return send_from_directory(_WEB_DIR / "css", filename)


@app.route("/js/<path:filename>")
def js(filename):
    """Serve scripts from src/web/js/."""
    return send_from_directory(_WEB_DIR / "js", filename)


# ════════════════════════════════════════════════════════════════════════════
# JSON API
# ════════════════════════════════════════════════════════════════════════════

@app.route("/api/divisions")
def api_divisions():
    """
    Return every division and its team list for the Build dropdowns.

    Query params:
        season — season ID to load (default: active SEASON_ID)

    WHY WE REBUILD DIVISIONS ON EVERY REQUEST
    ──────────────────────────────────────────
    build_scraper_divisions() reads the season YAML each time it is called.
    This ensures newly-added Wild/Storm teams (written to the YAML by
    add_team_to_yaml()) appear in the dropdown immediately — without needing
    a server restart. The YAML read is fast (< 1 ms) and this endpoint is
    only called on page load, season switch, and after an "Add Team" action.

    Team lists come from two sources (DRY — same data as the terminal menu):
      • Wild/Storm: extracted directly from fresh YAML data, sorted alpha.
        We bypass get_team_list() here because that function reads from a
        module-level DIVISIONS cache in run_menu.py (frozen at import time)
        — it would return stale data for teams added mid-session.
      • Majors/Minors: get_team_list() reads rosters.json fresh each call,
        so it is already correct and we continue to use it.
    """
    season = (request.args.get("season") or "").strip() or SEASON_ID
    # Read fresh from YAML on every request so newly-added teams appear
    # immediately without a server restart. (See docstring above.)
    divisions = build_scraper_divisions(season_id=season)
    out = []
    for div in DIVISION_ORDER:
        meta = divisions.get(div, {})
        div_type = "league" if meta.get("type") == "org" else "travel"

        if div in ("Wild", "Storm"):
            # Extract names from fresh YAML data and sort alphabetically.
            teams = sorted(name for (_, _, name) in meta.get("teams", []))
        else:
            # Majors/Minors: get_team_list() reads rosters.json fresh — correct.
            teams = get_team_list(div)

        out.append({
            "name": div,
            "type": div_type,
            "teams": teams,
        })
    return jsonify({"season": season, "divisions": out})


@app.route("/api/reports")
def api_reports():
    """
    Scan the season folder(s) for every generated PDF and return them grouped by
    division, each with its hitting and/or pitching report path.

    Query params:
        season — season ID to scope to, or omit/empty for ALL seasons.

    HOW REPORTS ARE LOCATED
    ───────────────────────
    Two on-disk layouts exist, so we simply recurse each division folder and
    match the project's stable filename convention:

        <stem>-Scout-Hitting_<year>.pdf
        <stem>-Scout-Pitching_<year>.pdf

      • League  (Majors/Minors): .../<Div>/Reports/Scouting_Reports/<stem>-...
      • Travel  (Wild/Storm):    .../<Div>/<TeamFolder>/<stem>-...

    Grouping by <stem> pairs each team's hitting + pitching report together,
    regardless of which layout produced it.

    When scanning all seasons, division sections are prefixed with the season
    name (e.g. "Majors — 2026 Spring") so the user knows which season each
    group belongs to.
    """
    season_filter = (request.args.get("season") or "").strip()
    pat = re.compile(r"^(?P<stem>.+)-Scout-(?P<kind>Hitting|Pitching)_\d{4}\.pdf$")
    seasons_root = SCOUT_ROOT / "seasons"

    # Build the list of (season_id, season_dir) pairs to scan.
    if season_filter:
        scan_list = [(season_filter, seasons_root / season_filter)]
    else:
        # All seasons: discover every seasons/<id>/ folder on disk.
        scan_list = sorted(
            (p.name, p) for p in seasons_root.iterdir() if p.is_dir()
        )

    out = []
    for sid, season_dir in scan_list:
        # Use a season-qualified label when showing all seasons together.
        label_suffix = f" — {sid}" if not season_filter else ""
        for div in DIVISION_ORDER:
            div_dir = season_dir / div
            if not div_dir.is_dir():
                continue

            # stem → {"hitting": relpath, "pitching": relpath, "mtime": float}
            teams: dict[str, dict] = {}
            for pdf in div_dir.rglob("*-Scout-*_*.pdf"):
                m = pat.match(pdf.name)
                if not m:
                    continue
                stem = m.group("stem")
                kind = m.group("kind").lower()
                # Path relative to the seasons/ ROOT (includes the season id),
                # because serve_report() resolves /report/<path> against
                # seasons/ — not a single season dir. Using season_dir here
                # dropped the season segment and caused 404s (BUG-20).
                rel = str(pdf.relative_to(seasons_root))
                entry = teams.setdefault(stem, {"name": _pretty_stem(stem),
                                                "hitting": None,
                                                "pitching": None,
                                                "mtime": 0.0})
                entry[kind] = rel
                entry["mtime"] = max(entry["mtime"], pdf.stat().st_mtime)

            if not teams:
                continue
            team_list = sorted(teams.values(), key=lambda t: t["name"].lower())
            out.append({"name": div + label_suffix, "teams": team_list,
                        "season": sid})

    season_rel = Path("seasons") / (season_filter or "")
    return jsonify({"season": season_filter or "all", "root": str(season_rel),
                    "divisions": out})


@app.route("/report/<path:relpath>")
def serve_report(relpath):
    """
    Stream a single PDF for viewing in the browser.

    SECURITY: the requested path is resolved and confirmed to live INSIDE the
    seasons/ root folder before anything is served. This blocks path-traversal
    attempts (e.g. ../../etc/passwd) from reaching files outside seasons/.

    Paths are now relative to the seasons/ root (not a single season), so they
    work correctly for both single-season and all-seasons report views.
    """
    seasons_root = (SCOUT_ROOT / "seasons").resolve()
    target = (seasons_root / relpath).resolve()
    if seasons_root not in target.parents or not target.is_file():
        abort(404)
    return send_file(target, mimetype="application/pdf")


@app.route("/api/add_team", methods=["POST"])
def api_add_team():
    """
    Register a new Wild / Storm opponent from a GameChanger schedule URL.

    Accepts an optional "season" field in the JSON body to target a specific
    season's YAML and Games/ folder. Defaults to the active SEASON_ID.

    Reuses _parse_gc_url() + _slug_to_folder_name() + add_team_to_yaml() so the
    web flow writes the SAME YAML the terminal "Add new team" option does.
    Creates the team's Games/ folder so the next pipeline run can scrape it.
    """
    data = request.get_json(silent=True) or {}
    season       = (data.get("season")      or "").strip() or SEASON_ID
    url          = (data.get("url")         or "").strip()
    division     = (data.get("division")    or "").strip()
    folder_override = (data.get("folder_name") or "").strip()

    if division not in ("Wild", "Storm"):
        return jsonify({"ok": False, "error": "Division must be Wild or Storm."}), 400

    team_id, slug = _parse_gc_url(url)
    if not team_id or not slug:
        return jsonify({"ok": False, "error": "Could not parse a GameChanger schedule URL. "
                                              "Expected …/teams/<id>/<slug>/schedule."}), 400

    folder_name = folder_override or _slug_to_folder_name(slug)

    # Append to the season YAML (idempotent — guards duplicates).
    try:
        add_team_to_yaml(division, team_id, slug, folder_name, season_id=season)
    except Exception as e:  # surface YAML write problems to the UI clearly
        return jsonify({"ok": False, "error": f"Failed to update season config: {e}"}), 500

    # Create the Games/ folder the scraper will drop game files into.
    target_season_dir = SCOUT_ROOT / "seasons" / season
    games_dir = target_season_dir / division / folder_name / "Games"
    games_dir.mkdir(parents=True, exist_ok=True)

    return jsonify({
        "ok": True,
        "season": season,
        "division": division,
        "team_id": team_id,
        "slug": slug,
        "folder_name": folder_name,
        "note": "Verify the folder name matches GameChanger's inning-header "
                "spelling exactly after the first game is scraped.",
    })


@app.route("/api/seasons")
def api_seasons():
    """
    Return all available seasons and which one is currently active.

    Used by the web UI season selector to populate the dropdown and mark
    the active entry. list_seasons() scans config/*.yaml each call (fast),
    so newly-created seasons appear without a server restart.

    Response shape:
        {
            "active":  "2026-spring",
            "seasons": [
                {"id": "2026-fall",   "display_name": "2026 Fall",   "is_active": false},
                {"id": "2026-spring", "display_name": "2026 Spring", "is_active": true},
            ]
        }
    """
    return jsonify({"active": SEASON_ID, "seasons": list_seasons()})


@app.route("/api/seasons/active", methods=["POST"])
def api_set_active_season():
    """
    Switch the active season by updating active_season.txt.

    Body (JSON): {"season_id": "2026-fall"}

    IMPORTANT: The server process must be restarted after switching — SEASON_ID
    and SEASON_DIR are resolved once at module import time. The response always
    includes a "restart_required" flag so the UI can display the notice.
    """
    data = request.get_json(silent=True) or {}
    season_id = (data.get("season_id") or "").strip()

    if not season_id:
        return jsonify({"ok": False, "error": "season_id is required."}), 400

    try:
        set_active_season(season_id)
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404

    return jsonify({
        "ok": True,
        "season_id": season_id,
        "restart_required": True,
        "note": "Restart the server for the season change to take effect: "
                "stop the server (Ctrl+C) and re-launch Start Scout.command.",
    })


@app.route("/api/seasons", methods=["POST"])
def api_create_season():
    """
    Scaffold a new season config and folder structure.

    Body (JSON):
        {
            "season_id":    "2026-fall",        required
            "majors_gc_id": "abc123",           required
            "minors_gc_id": "def456",           required
            "display_name": "2026 Fall",        optional (auto-derived if omitted)
            "set_active":   false               optional (default false)
        }

    On success:
        • Writes config/<season_id>.yaml from the season template
        • Creates seasons/<season_id>/ folder tree
        • Optionally updates active_season.txt (if set_active=true)

    Returns 409 if the season already exists, 500 if template is missing.
    """
    data = request.get_json(silent=True) or {}
    season_id    = (data.get("season_id")    or "").strip()
    majors_gc_id = (data.get("majors_gc_id") or "").strip()
    minors_gc_id = (data.get("minors_gc_id") or "").strip()
    display_name = (data.get("display_name") or "").strip() or None
    set_active   = bool(data.get("set_active", False))

    if not season_id:
        return jsonify({"ok": False, "error": "season_id is required."}), 400
    if not majors_gc_id:
        return jsonify({"ok": False, "error": "majors_gc_id is required."}), 400
    if not minors_gc_id:
        return jsonify({"ok": False, "error": "minors_gc_id is required."}), 400

    try:
        yaml_path = create_season(
            season_id=season_id,
            majors_gc_id=majors_gc_id,
            minors_gc_id=minors_gc_id,
            display_name=display_name,
            set_active=set_active,
        )
    except FileExistsError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    return jsonify({
        "ok": True,
        "season_id": season_id,
        "yaml": yaml_path.name,
        "set_active": set_active,
        "restart_required": set_active,
        "note": (
            "Restart the server to use the new season."
            if set_active else
            "Use the season dropdown to switch to this season, then restart the server."
        ),
    })


@app.route("/api/run")
def api_run():
    """
    Build reports for a scope and stream the live log back to the browser.

    The browser opens this as a Server-Sent Events (SSE) stream via EventSource,
    so each line the pipeline prints appears on the page in real time — exactly
    like watching the terminal, but in the web UI.

    Query params:
        division — division name, or omitted/"" for ALL divisions
        team     — team name, or omitted/"" for all teams in the division

    Concurrency: guarded by _run_lock. If a build is already running, this
    immediately streams a single "busy" message and closes.
    """
    division = (request.args.get("division") or "").strip()
    team = (request.args.get("team") or "").strip()
    # Optional season override — uses the SCOUT_SEASON env var so run_menu.py
    # (and season_config.py) pick it up without any argument changes.
    season = (request.args.get("season") or "").strip()

    def stream():
        # Non-blocking lock acquire: reject overlapping builds with a clear note.
        if not _run_lock.acquire(blocking=False):
            yield _sse("error", "A build is already running. Please wait for it to finish.")
            yield _sse("done", "busy")
            return
        try:
            # -u forces UNBUFFERED stdout in the child. WHY: Python block-buffers
            # print() when stdout is a pipe (not a TTY), so without -u the whole
            # build's output would arrive in one dump at the end instead of
            # streaming line-by-line to the live log. PYTHONUNBUFFERED is set too
            # as a belt-and-suspenders guard for any grandchild processes.
            cmd = [sys.executable, "-u", str(RUN_MENU)]
            if division:
                cmd += ["--division", division]
            if team:
                cmd += ["--team", team]
            scope = (division or "ALL") + (f" → {team}" if team else "")
            yield _sse("log", f"▶ Building reports for: {scope}")

            # cwd = SCOUT_ROOT so all the scripts' relative paths resolve.
            # stderr→stdout so warnings/errors stream inline with progress.
            env = {**os.environ, "PYTHONUNBUFFERED": "1"}
            # If a specific season was requested, pass it via SCOUT_SEASON so
            # season_config.py picks it up at import time in the subprocess —
            # without changing active_season.txt or restarting the server.
            if season:
                env["SCOUT_SEASON"] = season
            proc = subprocess.Popen(
                cmd, cwd=str(SCOUT_ROOT),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, env=env,
            )
            for line in iter(proc.stdout.readline, ""):
                yield _sse("log", line.rstrip("\n"))
            proc.stdout.close()
            code = proc.wait()
            if code == 0:
                yield _sse("log", "✅ Build complete.")
                yield _sse("done", "ok")
            else:
                yield _sse("log", f"❌ Build exited with code {code}.")
                yield _sse("done", "error")
        finally:
            _run_lock.release()

    # no-cache + keep-alive headers so the browser does not buffer the stream.
    return Response(stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no",
                             "Connection": "keep-alive"})


# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _sse(event, data):
    """
    Format one Server-Sent Events message.

    SSE is line-based text; multi-line payloads must prefix each line with
    'data:'. We JSON-encode the payload so newlines/quotes survive intact.
    """
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _pretty_stem(stem):
    """
    Turn a PDF filename stem into a readable team name for the Reports list.

    Examples:
        "A's_Blanco"            → "A's-Blanco"
        "Weddington_Wild_11U"   → "Weddington Wild 11U"

    League stems use Team_Coach (one underscore separating the two); travel
    stems use Word_Word_Word. We can't perfectly distinguish them, so we keep
    it simple and just swap underscores for spaces — readable enough for a list.
    """
    return stem.replace("_", " ")


def main():
    """Start the local server (loopback by default) and print the URL to open."""
    url = f"http://{HOST if HOST != '0.0.0.0' else '127.0.0.1'}:{PORT}"
    print("=" * 58)
    print("  WCWAA Scout — Web UI")
    print(f"  Season : {SEASON_ID}")
    print(f"  Open   : {url}")
    if HOST == "0.0.0.0":
        print("  (Bound to 0.0.0.0 — reachable from other devices on your Wi-Fi)")
    print("  Press Ctrl+C to stop.")
    print("=" * 58)
    app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True)


if __name__ == "__main__":
    main()
