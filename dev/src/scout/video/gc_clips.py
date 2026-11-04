"""
gc_clips.py — download GameChanger video clips (and optionally stitch a montage)
================================================================================
Accepts two kinds of GC links:

  • Game clip gallery  …/schedule/<game_id>/videos/clips   → every clip of that game
  • Clip share link    …/videos/clips/<clip_id>?token=…    → that one clip

How it works:

  1. Scout Chrome (gc_browser — the same signed-in profile the scrapers use) opens
     each link.
       - Game: the gallery page POSTs api.team-manager.gc.com/clips/search/v2; we
         reuse that request's auth headers to page through the game's full clip list,
         then GET /clips/<id>/playback-data?kind=player for each clip (from inside
         the page, so GC sees the normal browser).
       - Share link: the page GETs /clips/<id>/standalone-playback-data?shareToken=…;
         we capture that response.
     Playback data = the clip's HLS playlist (.m3u8 on vod-archive.gc.com) plus
     CloudFront signed cookies (~24 h).
  2. Chrome closes; ffmpeg downloads each playlist with those cookies and remuxes
     it to .mp4 (no re-encode, GC's original 720p), several at a time.
  3. --montage joins the clips (game clips in game order, links in the order
     given) into one .mp4.

Usage
-----
python -m scout.video.gc_clips GAME_OR_CLIP_URL [...]
python -m scout.video.gc_clips GAME_URL --player Harper --montage "Harper Nov 3"
python -m scout.video.gc_clips GAME_URL --list          # preview, no downloads

Requires ffmpeg/ffprobe (brew install ffmpeg) and the Scout Chrome login
(python -m scout.scraping.scrape_gc_playbyplay --login).
"""

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from scout.scraping.gc_browser import run_with_session
from scout.season_config import LOGS_DIR

DEFAULT_OUT_DIR = Path.home() / "Movies" / "GameChanger Clips"
DEFAULT_JOBS = 4
_PAGE_TIMEOUT_MS = 45000
_SEARCH_PAGE_SIZE = 100

API_BASE = "https://api.team-manager.gc.com"
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_CLIP_URL_RE = re.compile(rf"https://web\.gc\.com/.*/videos/clips/({_UUID})", re.IGNORECASE)
_GAME_URL_RE = re.compile(
    rf"(https://web\.gc\.com/teams/[^/?#]+/[^/?#]+/schedule/({_UUID}))(?:[/?#].*)?$", re.IGNORECASE
)

MONTAGE_WIDTH, MONTAGE_HEIGHT, MONTAGE_FPS = 1280, 720, 30
_SILENCE = ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]

# Runs fetch() inside the GC page so requests carry the real browser's identity.
_FETCH_JS = """async ({url, method, headers, body}) => {
  const r = await fetch(url, {method, headers, body});
  return {status: r.status, text: await r.text()};
}"""


def setup_logging(verbose=False):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f"gc_clips_{datetime.now():%Y%m%d_%H%M%S}.log"
    fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    sh.setLevel(logging.DEBUG if verbose else logging.INFO)
    log = logging.getLogger("gc_clips")
    log.setLevel(logging.DEBUG)
    log.addHandler(fh)
    log.addHandler(sh)
    log.debug(f"Log → {log_path}")
    return log


# ── Input ─────────────────────────────────────────────────────────────────────

def parse_link(url):
    """Classify a GC link → ("clip", clip_id, url) | ("game", game_id, gallery_url) | None."""
    url = url.strip()
    m = _CLIP_URL_RE.match(url)
    if m:
        return ("clip", m.group(1).lower(), url)
    m = _GAME_URL_RE.match(url)
    if m:
        return ("game", m.group(2).lower(), f"{m.group(1)}/videos/clips")
    return None


def read_url_file(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


def collect_targets(urls, log):
    """Validate URLs → ordered targets from parse_link(), dropping bad and duplicate links."""
    targets, seen = [], set()
    for url in urls:
        target = parse_link(url)
        if not target:
            log.warning(f"Not a GameChanger game or clip link, skipped: {url}")
            continue
        if target[:2] in seen:
            log.info(f"Duplicate link skipped: {url}")
            continue
        seen.add(target[:2])
        targets.append(target)
    return targets


# ── Naming ────────────────────────────────────────────────────────────────────

def _slug(text):
    return re.sub(r"[^A-Za-z0-9]+", "-", text or "").strip("-")


def new_lookups():
    """Names GC sends alongside a clip page: players, teams, and each game's team/opponent."""
    return {"players": {}, "teams": {}, "games": {}}


def player_name(meta, lookups):
    return lookups["players"].get((meta.get("player_metadata") or {}).get("player_id"), "")


def clip_filename(meta, lookups):
    """e.g. Expos-Esau_vs_Blue-Jays-Patel_T1_Single_Cole-Plunkett_20261103-180054.mp4"""
    parts = []
    game = lookups["games"].get(meta.get("event_id")) or {}
    team = _slug(lookups["teams"].get(game.get("team_id")))
    opponent = _slug(game.get("opponent"))
    if team and opponent:
        parts.append(f"{team}_vs_{opponent}")
    else:
        parts.append(team or opponent)
    sport = meta.get("sport_metadata") or {}
    if sport.get("inning"):
        half = "T" if sport.get("inning_half") == "top" else "B"
        parts.append(f"{half}{sport['inning']}")
    parts.append(_slug(meta.get("name")))
    parts.append(_slug(player_name(meta, lookups)))
    ts = meta.get("timestamp")
    if ts:
        when = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        parts.append(when.astimezone().strftime("%Y%m%d-%H%M%S"))
    name = "_".join(p for p in parts if p)
    return (name or meta["clip_metadata_id"]) + ".mp4"


def matches_player(meta, lookups, wanted):
    """True when no --player filter is set or the clip's player name contains any wanted text."""
    if not wanted:
        return True
    name = player_name(meta, lookups).casefold()
    return any(w.casefold() in name for w in wanted)


# Downloaded clips are tracked by clip ID here, since file names don't carry the ID.
MANIFEST_NAME = ".gc_clips.json"


def load_manifest(out_dir):
    path = out_dir / MANIFEST_NAME
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_manifest(out_dir, manifest):
    (out_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")


def existing_clip(out_dir, manifest, clip_id):
    name = manifest.get(clip_id)
    path = out_dir / name if name else None
    return path if path and path.exists() else None


def unique_path(out_dir, filename, clip_id, owners):
    """Avoid overwriting a different clip that produced the same name (adds _2, _3, …).

    owners maps file name → clip ID for clips already in the folder; a clip may reuse its own name.
    """
    stem, suffix = filename[:-4], filename[-4:]
    candidate, n = filename, 2
    while True:
        owner = owners.get(candidate)
        if owner == clip_id or (owner is None and not (out_dir / candidate).exists()):
            return out_dir / candidate
        candidate = f"{stem}_{n}{suffix}"
        n += 1


# ── Step 1: clip list + playback info from GC (Scout Chrome) ──────────────────

_API_TEAM_RE = re.compile(rf"api\.team-manager\.gc\.com/teams/({_UUID})$", re.IGNORECASE)
_API_EVENT_RE = re.compile(rf"api\.team-manager\.gc\.com/events/({_UUID})$", re.IGNORECASE)


def record_lookup(lookups, url, data):
    """Fold one GC API response (already JSON-decoded) into lookups."""
    path = url.split("?")[0]
    if path.endswith("/players") and isinstance(data, list):
        for p in data:
            name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
            if p.get("id") and name:
                lookups["players"][p["id"]] = name
    elif _API_TEAM_RE.search(path) and isinstance(data, dict) and data.get("name"):
        lookups["teams"][data["id"]] = data["name"]
    elif _API_EVENT_RE.search(path) and isinstance(data, dict):
        event = data.get("event") or {}
        pregame = data.get("pregame_data") or {}
        if event.get("id"):
            lookups["games"][event["id"]] = {
                "team_id": event.get("team_id"),
                "opponent": pregame.get("opponent_name"),
            }


def usable(meta, tag, log):
    if not (meta.get("permissions") or {}).get("can_view", True):
        log.error(f"{tag}: your account can't view this clip")
        return False
    return True


class GameGallery:
    """A game's clip gallery open in Scout Chrome, reusing the page's own API auth headers."""

    def __init__(self, page, gallery_url, log):
        self.page, self.url, self.log = page, gallery_url, log
        self._open()

    def _open(self):
        with self.page.expect_request(
            lambda r: "/clips/search/v2" in r.url and r.method == "POST", timeout=_PAGE_TIMEOUT_MS
        ) as info:
            self.page.goto(self.url, wait_until="domcontentloaded", timeout=_PAGE_TIMEOUT_MS)
        req = info.value
        self.search_url = req.url
        self.search_body = json.loads(req.post_data or "{}")
        self.headers = {k: v for k, v in req.headers.items()
                        if k.startswith("gc-") or k in ("accept", "content-type")}
        # Team/opponent/player names arrive alongside the gallery's first requests.
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

    def _call(self, url, method="GET", body=None, headers=None):
        args = {"url": url, "method": method, "headers": headers, "body": body}
        result = self.page.evaluate(_FETCH_JS, args)
        if result["status"] == 401:
            self.log.debug("GC auth expired mid-run — reloading gallery for a fresh token")
            self._open()
            args["headers"] = {k: v for k, v in self.headers.items() if k in (headers or {})}
            result = self.page.evaluate(_FETCH_JS, args)
        return result

    def clips(self):
        """Every clip in the game, in game order (search hits: name, inning, player, timestamp …)."""
        hits, offset = [], 0
        while offset is not None:
            body = dict(self.search_body, limit=_SEARCH_PAGE_SIZE, offset=offset)
            r = self._call(self.search_url, "POST", json.dumps(body), self.headers)
            if r["status"] != 200:
                raise RuntimeError(f"clip list request failed (HTTP {r['status']})")
            data = json.loads(r["text"])
            hits += data.get("hits") or []
            offset = data.get("next_offset")
            if not data.get("hits"):
                break
        return hits

    def playback(self, clip_id):
        auth = {k: v for k, v in self.headers.items() if k.startswith("gc-")}
        r = self._call(f"{API_BASE}/clips/{clip_id}/playback-data?kind=player", headers=auth)
        if r["status"] != 200:
            raise RuntimeError(f"HTTP {r['status']}")
        data = json.loads(r["text"])
        if not data.get("url"):
            raise RuntimeError("no video URL in playback data")
        return data


def fetch_shared_clip(page, clip_id, url, tag, log):
    """Open a clip share link and capture its standalone playback data (metadata + playback)."""
    marker = f"/clips/{clip_id}/standalone-playback-data"
    try:
        with page.expect_response(
            lambda r: marker in r.url and r.request.method == "GET", timeout=_PAGE_TIMEOUT_MS
        ) as info:
            page.goto(url, wait_until="domcontentloaded", timeout=_PAGE_TIMEOUT_MS)
        resp = info.value
        if not resp.ok:
            hint = ""
            if "token=" not in url:
                hint = " — link has no share token; use the clip's Share → Copy link URL"
            log.error(f"{tag}: GC returned HTTP {resp.status}{hint}")
            return None
        meta = resp.json()
    except Exception as exc:
        log.error(f"{tag}: no playback data ({exc})")
        return None
    if not usable(meta, tag, log):
        return None
    if not (meta.get("playback") or {}).get("url"):
        log.error(f"{tag}: playback data has no video URL")
        return None
    return meta


def resolve_clips(page, targets, skip, players, log, with_playback=True):
    """Expand targets into an ordered clip list.

    Returns (entries, lookups); each entry is {"id", "meta"} where meta is None for clips in
    `skip` (already downloaded) or that failed. Game clips not matching `players` are dropped.
    """
    lookups = new_lookups()

    def _track_names(response):
        if "api.team-manager.gc.com" not in response.url or not response.ok:
            return
        path = response.url.split("?")[0]
        if not (path.endswith("/players") or _API_TEAM_RE.search(path) or _API_EVENT_RE.search(path)):
            return
        try:
            record_lookup(lookups, response.url, response.json())
        except Exception:
            pass

    page.on("response", _track_names)
    entries = []
    try:
        for kind, target_id, url in targets:
            if kind == "clip":
                tag = f"clip {target_id[:8]}"
                meta = None
                if target_id not in skip:
                    meta = fetch_shared_clip(page, target_id, url, tag, log)
                    if meta:
                        log.info(f"{tag}: found {meta.get('name', 'clip')}")
                entries.append({"id": target_id, "meta": meta})
                continue

            try:
                gallery = GameGallery(page, url, log)
                hits = gallery.clips()
            except Exception as exc:
                log.error(f"game {target_id[:8]}: couldn't list clips ({exc})")
                continue
            picked = [h for h in hits if matches_player(h, lookups, players)]
            game = lookups["games"].get(target_id) or {}
            title = " vs ".join(n for n in (lookups["teams"].get(game.get("team_id")), game.get("opponent")) if n)
            note = f" ({len(picked)} match --player)" if players else ""
            log.info(f"game {title or target_id[:8]}: {len(hits)} clips{note}")
            for i, hit in enumerate(picked, 1):
                cid = hit["clip_metadata_id"]
                tag = f"[{i}/{len(picked)}] {cid[:8]}"
                if cid in skip or not usable(hit, tag, log):
                    entries.append({"id": cid, "meta": hit if cid in skip else None})
                    continue
                meta = dict(hit)
                if with_playback:
                    try:
                        meta["playback"] = gallery.playback(cid)
                    except Exception as exc:
                        log.error(f"{tag}: no playback data ({exc})")
                        meta = None
                    else:
                        log.debug(f"{tag}: playback ok — {hit.get('name')}")
                entries.append({"id": cid, "meta": meta})
    finally:
        page.remove_listener("response", _track_names)
    return entries, lookups


# ── Step 2: download ──────────────────────────────────────────────────────────

def cookie_header(cookies):
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


def download_clip(meta, dest):
    """Download one clip to dest. Returns None on success, else an error message."""
    playback = meta["playback"]
    tmp = dest.with_name(dest.stem + ".part.mp4")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-headers", f"Cookie: {cookie_header(playback.get('cookies') or {})}\r\n",
        "-i", playback["url"],
        "-c", "copy", "-movflags", "+faststart",
        str(tmp),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not tmp.exists():
        if tmp.exists():
            tmp.unlink()
        return result.stderr.strip()[-500:] or f"ffmpeg exit {result.returncode}"
    tmp.replace(dest)
    return None


# ── Step 3: montage ───────────────────────────────────────────────────────────

def _has_audio(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    ).stdout
    return bool(out.strip())


def normalize_command(src, dest, has_audio):
    """Re-encode one clip to the montage format (720p30 H.264 + 48 kHz stereo AAC)."""
    vf = (f"scale={MONTAGE_WIDTH}:{MONTAGE_HEIGHT}:force_original_aspect_ratio=decrease,"
          f"pad={MONTAGE_WIDTH}:{MONTAGE_HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={MONTAGE_FPS}")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src)]
    if has_audio:
        cmd += ["-map", "0:v:0", "-map", "0:a:0"]
    else:
        # The join step needs audio in every clip; give silent clips a silent track.
        cmd += [*_SILENCE, "-map", "0:v:0", "-map", "1:a:0", "-shortest"]
    return cmd + [
        "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
        str(dest),
    ]


def build_montage(paths, dest, log, jobs=DEFAULT_JOBS):
    """Normalize every clip to one format, then join them losslessly (scales to any clip count)."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="gc_montage_"))
    try:
        parts = [tmp_dir / f"{i:04d}.mp4" for i in range(len(paths))]
        log.info(f"Building montage from {len(paths)} clips (re-encoding to 720p) …")
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = {
                pool.submit(subprocess.run, normalize_command(src, part, _has_audio(src)),
                            capture_output=True, text=True): src
                for src, part in zip(paths, parts)
            }
            for fut in as_completed(futures):
                result = fut.result()
                if result.returncode != 0:
                    log.error(f"Montage failed on {futures[fut].name}: {result.stderr.strip()[-500:]}")
                    return False
        listing = tmp_dir / "list.txt"
        listing.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
        result = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
             "-c", "copy", "-movflags", "+faststart", str(dest)],
            capture_output=True, text=True,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    if result.returncode != 0:
        log.error(f"Montage failed: {result.stderr.strip()[-800:]}")
        return False
    log.info(f"✔ Montage → {dest}")
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(description="Download GameChanger video clips (whole games or share links).")
    ap.add_argument("urls", nargs="*",
                    help="Game clip gallery (…/schedule/<game>/videos/clips) or clip share links — quote each one")
    ap.add_argument("-f", "--file", help="Text file with one link per line (# comments ok)")
    ap.add_argument("-o", "--out", default=str(DEFAULT_OUT_DIR),
                    help=f"Download folder (default: {DEFAULT_OUT_DIR})")
    ap.add_argument("-p", "--player", action="append", default=[], metavar="NAME",
                    help="Only game clips whose player name contains NAME (repeatable, case-insensitive)")
    ap.add_argument("-m", "--montage", metavar="NAME.mp4",
                    help="Also join the clips into this file (saved in --out); game clips in game order")
    ap.add_argument("-l", "--list", action="store_true", help="Show the clips that would be saved; download nothing")
    ap.add_argument("-j", "--jobs", type=int, default=DEFAULT_JOBS,
                    help=f"Clips to download/encode at once (default {DEFAULT_JOBS})")
    ap.add_argument("--force", action="store_true", help="Re-download clips already in --out")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    log = setup_logging(args.verbose)
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            log.error(f"{tool} not found — install it with:  brew install ffmpeg")
            return 1

    urls = list(args.urls)
    if args.file:
        urls += read_url_file(args.file)
    targets = collect_targets(urls, log)
    if not targets:
        log.error("No GameChanger game or clip links given.")
        return 1

    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(out_dir)
    have = {} if args.force else {
        cid: path for cid in manifest if (path := existing_clip(out_dir, manifest, cid))
    }

    needs_chrome = any(kind == "game" or tid not in have for kind, tid, _ in targets)
    entries, lookups = [{"id": tid, "meta": None} for _, tid, _ in targets], new_lookups()
    if needs_chrome:
        log.info("Opening Scout Chrome to look up clips …")

        def _work(page):
            nonlocal entries, lookups
            entries, lookups = resolve_clips(page, targets, set(have), args.player, log,
                                             with_playback=not args.list)

        code = run_with_session(log, _work)
        if code != 0:
            return code

    owners = {name: cid for cid, name in manifest.items()}
    plan = []  # (clip_id, meta, dest) to download
    for e in entries:
        cid, meta = e["id"], e["meta"]
        if cid in have:
            continue
        if meta is None:
            continue
        dest = unique_path(out_dir, clip_filename(meta, lookups), cid, owners)
        owners[dest.name] = cid
        plan.append((cid, meta, dest))

    if args.list:
        for e in entries:
            cid = e["id"]
            if cid in have:
                print(f"  have  {have[cid].name}")
        for _, _, dest in plan:
            print(f"  new   {dest.name}")
        log.info(f"{len(have.keys() & {e['id'] for e in entries})} already downloaded, "
                 f"{len(plan)} to download (nothing downloaded — --list)")
        return 0

    saved = {cid: have[cid] for cid in (e["id"] for e in entries) if cid in have}
    if plan:
        log.info(f"Downloading {len(plan)} clip(s), {args.jobs} at a time …")
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            futures = {pool.submit(download_clip, meta, dest): (cid, dest) for cid, meta, dest in plan}
            for done, fut in enumerate(as_completed(futures), 1):
                cid, dest = futures[fut]
                error = fut.result()
                if error:
                    log.error(f"[{done}/{len(plan)}] failed {dest.name}: {error}")
                    continue
                log.info(f"[{done}/{len(plan)}] {dest.name}")
                saved[cid] = dest
                old = manifest.get(cid)
                if old and old != dest.name and (out_dir / old).exists():
                    (out_dir / old).unlink()
                manifest[cid] = dest.name
                save_manifest(out_dir, manifest)

    failed = [e["id"] for e in entries if e["id"] not in saved]
    log.info(f"Done: {len(saved)}/{len(entries)} clips in {out_dir}")
    if failed:
        log.warning(f"Not downloaded: {', '.join(c[:8] for c in failed)}")

    if args.montage:
        ordered = [saved[e["id"]] for e in entries if e["id"] in saved]
        if not ordered:
            log.error("No clips available for the montage.")
            return 1
        name = args.montage if args.montage.lower().endswith(".mp4") else args.montage + ".mp4"
        if not build_montage(ordered, out_dir / name, log, max(1, args.jobs)):
            return 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
