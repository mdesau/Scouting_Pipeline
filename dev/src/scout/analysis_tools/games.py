"""Shared game-level data for the analysis tools: runs per half-inning, final scores, dates, postseason config."""

import re
from collections import defaultdict
from datetime import date
from functools import lru_cache

from scout.analysis_tools import pitching_usage as mur
from scout.season_config import SEASON_DIR, load_season_yaml

SCORE_RE = re.compile(r"([A-Z0-9\-]{2,5})\s+(\d+)\s+-\s+([A-Z0-9\-]{2,5})\s+(\d+)")
MONTHS = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


def rerun_commands(division):
    """The one command (plus setup) that refreshes every analysis report; printed in each output."""
    return ["cd ~/Documents/VSCode/Personal/Scout", "source venv/bin/activate",
            f"python -m scout.analysis_tools.run_all --division {division}"]


@lru_cache(maxsize=None)
def division_data(division):
    """Parse a division's games once per process: (scorebooks, postseason, games, pitching_usage.analyze()).

    Shared read-only by all three tools, so running them together parses every file only once.
    """
    sb, post = scorebooks_dir(division), postseason(division)
    return sb, post, load_games(sb, post), mur.analyze(sb)


def postseason(division):
    """The division's `postseason:` block from the active season YAML ({} if none)."""
    _sid, cfg = load_season_yaml()
    return cfg["divisions"][division].get("postseason") or {}


def scorebooks_dir(division):
    _sid, cfg = load_season_yaml()
    return SEASON_DIR / cfg["divisions"][division]["scorebooks"]


def game_date(path, year):
    return date(year, MONTHS[path.name[:3]], int(path.name[3:5]))


def last_score(path):
    """Final score pair from the last GC score string in the file (file order is newest-first)."""
    for line in path.read_text(encoding="utf-8").splitlines():
        m = SCORE_RE.search(line)
        if m:
            return sorted([int(m.group(2)), int(m.group(4))])
    return None


def _map_abbreviations(halves):
    """GC score strings use team abbreviations; credit each abbr to the team batting when it rises."""
    votes = defaultdict(lambda: defaultdict(int))
    last = {}
    for h in halves:
        for pa in h["pas"]:
            for k, v in (pa.get("score") or {}).items():
                if v > last.get(k, 0):
                    votes[h["batting"]][k] += 1
                last[k] = max(last.get(k, 0), v)
    out, used = {}, set()
    for team, v in sorted(votes.items(), key=lambda kv: -max(kv[1].values())):
        for abbr, _n in sorted(v.items(), key=lambda kv: -kv[1]):
            if abbr not in used:
                out[team] = abbr; used.add(abbr); break
    return out


def load_games(scorebooks, post):
    """Parse every game file. `post` is the postseason config (start date, weather rollbacks)."""
    start = post.get("start") or date.max
    year = start.year if start != date.max else date.today().year
    rollbacks = post.get("rollbacks") or {}
    games = []
    for path in sorted(scorebooks.glob("*.txt"), key=lambda p: (game_date(p, year), p.name)):
        gid, halves = mur.parse_game(path)
        teams = sorted({h["batting"] for h in halves})
        if len(teams) != 2:
            continue
        runs = {t: 0 for t in teams}
        abbr_of = _map_abbreviations(halves)
        team_of = {a: t for t, a in abbr_of.items()}
        innings = [{"batting": h["batting"], "inning": h["inning"], "runs": 0,
                    "outs": max([p["outs_after"] or 0 for p in h["pas"]] + [0])} for h in halves]
        last = defaultdict(int)
        latest_half = {}  # team -> index of its most recent batting half
        for i, h in enumerate(halves):
            latest_half[h["batting"]] = i
            for pa in h["pas"]:
                for k, v in (pa.get("score") or {}).items():
                    team = team_of.get(k)
                    if v > last[k] and team in latest_half:
                        # A run can surface in the score string only after the half flips.
                        innings[latest_half[team]]["runs"] += v - last[k]
                        runs[team] += v - last[k]
                    last[k] = max(last[k], v)
        final = last_score(path)
        if gid in rollbacks:
            # Official result rolled back to an earlier inning (e.g. weather).
            innings = [h for h in innings if h["inning"] <= rollbacks[gid]]
            runs = {t: sum(h["runs"] for h in innings if h["batting"] == t) for t in teams}
            final = sorted(runs.values())
        d = game_date(path, year)
        games.append({"id": gid, "path": path, "date": d, "teams": teams,
                      "runs": runs, "halves": innings, "final": final,
                      "playoff": d >= start})
    return games
