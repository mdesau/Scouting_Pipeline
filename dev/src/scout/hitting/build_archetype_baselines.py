"""
build_archetype_baselines.py — build config/archetype_baselines.yaml (BUG-024)
==============================================================================
Reads every kid's plate appearances from the chosen seasons, groups kids by division age
(league vs. travel), measures how repeatable each stat is (first half vs. second half of the
season) to set the small-sample pull, and writes each group's percentile cutoffs.

Run only when you want new baselines (e.g. after a season adds a new age group):
    python -m scout.hitting.build_archetype_baselines                          # all seasons
    python -m scout.hitting.build_archetype_baselines --seasons 2026-spring 2026-Fall

Season paths are fixed at import, so each season is read in its own subprocess (--collect).
"""

import argparse
import json
import logging
import math
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

import yaml

from scout.hitting import archetypes as arch
from scout.season_config import list_seasons, team_name_age

MIN_PA = 15          # kids below this don't shape the cutoffs
MIN_GROUP = 60       # qualified kids a group needs for its own cutoffs
MIN_HALF_DEN = 5     # per-half denominator needed for the repeatability check
MODULE = "scout.hitting.build_archetype_baselines"
# Teams whose name age doesn't match the level they play (kept across rebuilds in the YAML).
DEFAULT_IGNORE = []


# ── Collect (runs inside one season's process) ──────────────────────────────

def _date_key(fname):
    try:
        return datetime.strptime(fname[:5], "%b%d").timetuple()[1:3], fname
    except ValueError:
        return (99, 99), fname


def _team_rows(gh, files_pas, roster, meta):
    """One row per kid: counts for the full season and each half (by game date)."""
    files_pas = sorted(files_pas, key=lambda fp: _date_key(fp[0]))
    mid = len(files_pas) // 2
    out = {}
    for scope, fps in (("full", files_pas), ("h1", files_pas[:mid]), ("h2", files_pas[mid:])):
        pas = [pa for _, p in fps for pa in p]
        for b in (gh.compute_stats(pas, roster) if pas else []):
            out.setdefault(b["initials"], dict(meta))[scope] = arch.counts(b)
    return [r for r in out.values() if "full" in r]


def _league_rows(gh, cfg, meta):
    rosters, cmaps = gh.load_box_rosters(cfg["roster_json"], cfg["roster_additions"])
    files = sorted(f for f in os.listdir(cfg["scorebooks"]) if f.endswith(".txt"))
    rows = []
    for team_name, coach in cfg["teams"]:
        tk = f"{team_name}-{coach}"
        fk = gh.file_key(tk)
        roster = rosters.get(f"{cfg['csv_overrides'].get(team_name, team_name)}-{coach}", {})
        fps = []
        for f in files:
            if tk in f or fk in f:
                try:
                    fps.append((f, gh.parse_game_for_team(os.path.join(cfg["scorebooks"], f), tk,
                                                          collision_map=cmaps.get(tk, {}))))
                except Exception:
                    pass
        rows += _team_rows(gh, fps, roster, meta)
    return rows


def _travel_rows(gh, cfg, meta):
    rows = []
    for team in gh.get_wild_opponents(cfg["wild_base"]):
        gdir = os.path.join(cfg["wild_base"], team, "Games")
        if not os.path.isdir(gdir):
            continue
        fps = []
        for f in sorted(os.listdir(gdir)):
            if f.endswith(".txt"):
                try:
                    fps.append((f, gh.parse_game_for_team(os.path.join(gdir, f), team)))
                except Exception:
                    pass
        roster = {p["initials"]: p["initials"] for _, ps in fps for p in ps}
        roster.update(gh.load_wild_roster(os.path.join(cfg["wild_base"], team)))
        rows += _team_rows(gh, fps, roster, {**meta, "team": team})
    return rows


def collect(out_path):
    """Write every kid's counts for the loaded season (SCOUT_SEASON) to out_path."""
    logging.disable(logging.WARNING)
    from scout.hitting import gen_hitting as gh
    from scout.season_config import SEASON_ID, load_season_yaml
    _sid, season_cfg = load_season_yaml()
    rows = []
    for div, cfg in gh.DIVISIONS.items():
        age = season_cfg["divisions"][div].get("age")
        if not age:
            print(f"  {SEASON_ID} {div}: no `age:` — skipped", file=sys.stderr)
            continue
        if "scorebooks" in cfg and os.path.isdir(cfg["scorebooks"]):
            rows += _league_rows(gh, cfg, {"season": SEASON_ID, "kind": "league", "div_age": age})
        elif "wild_base" in cfg and os.path.isdir(cfg["wild_base"]):
            rows += _travel_rows(gh, cfg, {"season": SEASON_ID, "kind": "travel", "div_age": age})
    Path(out_path).write_text(json.dumps(rows), encoding="utf-8")


def collect_seasons(seasons):
    rows = []
    for sid in seasons:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            path = tmp.name
        env = {**os.environ, "SCOUT_SEASON": sid}
        subprocess.run([sys.executable, "-m", MODULE, "--collect", path], env=env, check=True)
        rows += json.loads(Path(path).read_text(encoding="utf-8"))
        os.unlink(path)
    return rows


# ── Build ───────────────────────────────────────────────────────────────────
def baseline_group(row, ignore=()):
    """Group a kid shapes: league = division age; travel = the age in the team name (else division age)."""
    age = row["div_age"]
    if row["kind"] == "travel" and row.get("team") not in ignore:
        age = team_name_age(row.get("team")) or age
    return arch.group_key(row["kind"], age)

def _rate(c, stat):
    num, den = arch.STATS[stat]
    return c[num] / c[den] if c[den] else None


def group_means(qual):
    return {g: {s: sum(r["full"][arch.STATS[s][0]] for r in kids) / max(1, sum(r["full"][arch.STATS[s][1]] for r in kids))
                for s in arch.STATS} for g, kids in qual.items()}


def _corr(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx, sy = math.sqrt(sum((x - mx) ** 2 for x in xs)), math.sqrt(sum((y - my) ** 2 for y in ys))
    return sxy / (sx * sy) if sx and sy else 0.0


def shrink_constants(rows, means):
    """k per stat from split-half repeatability r: reliability = n / (n + k)  →  k = n̄ (1 − r) / r."""
    out = {}
    for s, (_num, den) in arch.STATS.items():
        xs, ys, ns = [], [], []
        for r in rows:
            a, b = r.get("h1"), r.get("h2")
            if r["group"] not in means or not a or not b or a[den] < MIN_HALF_DEN or b[den] < MIN_HALF_DEN:
                continue
            m = means[r["group"]][s]
            xs.append(_rate(a, s) - m)
            ys.append(_rate(b, s) - m)
            ns.append((a[den] + b[den]) / 2)
        rel = _corr(xs, ys)
        nbar = sum(ns) / len(ns)
        out[s] = {"k": round(nbar * (1 - rel) / rel if rel > 0.05 else 10 * nbar, 1),
                  "repeatability": round(rel, 2), "per": den}
    return out


def _percentile(sorted_vals, p):
    k = (len(sorted_vals) - 1) * p / 100
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def _fallback(group, qual):
    """Nearest younger group of the same kind with enough kids (else nearest older)."""
    kind, age = group.split()
    n = int(age[:-1])
    ok = [g for g in qual if g.startswith(kind + " ") and len(qual[g]) >= MIN_GROUP]
    younger = sorted((g for g in ok if int(g.split()[1][:-1]) < n), key=lambda g: -int(g.split()[1][:-1]))
    older = sorted((g for g in ok if int(g.split()[1][:-1]) > n), key=lambda g: int(g.split()[1][:-1]))
    return (younger + older or [None])[0]


def build(rows, seasons, ignore=()):
    for r in rows:
        r["group"] = baseline_group(r, ignore)
    qual = defaultdict(list)
    for r in rows:
        if r["full"]["pa"] >= MIN_PA:
            qual[r["group"]].append(r)
    means = group_means(qual)
    shrink = shrink_constants(rows, means)
    ks = {s: v["k"] for s, v in shrink.items()}
    groups = {}
    for g in sorted(qual, key=lambda g: (g.split()[0], int(g.split()[1][:-1]))):
        entry = {"kids": len(qual[g]),
                 "seasons": dict(sorted(Counter(r["season"] for r in qual[g]).items()))}
        if len(qual[g]) < MIN_GROUP:
            entry["use"] = _fallback(g, qual)
        else:
            entry["mean"] = {s: round(means[g][s], 4) for s in arch.STATS}
            entry["pct"] = {}
            for s in arch.STATS:
                vals = sorted(arch.shrunk_rate(r["full"], s, means[g][s], ks[s]) for r in qual[g])
                entry["pct"][s] = [round(_percentile(vals, p), 4) for p in arch.PCT_POINTS]
        groups[g] = entry
    return {"built": str(date.today()), "seasons": list(seasons), "min_pa": MIN_PA,
            "min_group": MIN_GROUP, "ignore_team_name_age": list(ignore),
            "shrink_k": ks, "repeatability": shrink, "groups": groups}


def label_mix(data, rows):
    mix = {}
    for g, entry in data["groups"].items():
        kids = [r for r in rows if r["group"] == g and r["full"]["pa"] >= MIN_PA]
        base = data["groups"][entry.get("use", g)]
        labs = [arch.classify(arch.ranks(r["full"], base, data["shrink_k"])) for r in kids]
        n = len(labs) or 1
        mix[g] = {k: round(100 * v / n) for k, v in Counter(lab for pair in labs for lab in pair).items()}
    return mix


# ── Write (header comments are the human-readable definitions) ───────────────

HEADER = """\
# ===========================================================================
# WCWAA Scout — Batter Archetype Baselines  (BUG-024)
# ===========================================================================
# GENERATED by:  python -m scout.hitting.build_archetype_baselines
# Don't hand-edit the numbers; re-run the script to rebuild (comments are rewritten too).
# Built {built} from seasons: {seasons}
#
# WHAT THIS IS
#   Each hitter gets a 2-word label: APPROACH + RESULT (e.g. "Aggressive Power").
#   A kid is compared only with kids his age, league (Majors/Minors) and travel kept separate.
#   LABELS use the division's `age:` in the season YAML (a Mavs opponent is judged against
#   the level Mavs plays). BASELINES (the numbers below) group travel kids by the age in their
#   TEAM NAME ("QC Crushers 10U" -> 10U), falling back to the division's age when the name has
#   none or the team is listed in `ignore_team_name_age` (teams that play up/down; edit that
#   list, then rebuild). Cutoffs are frozen and reused every season; ages bump in the fall.
#
# STATS (pNN = percentile within the age group: p67 = higher than ~2/3 of kids)
#   Swing%        swings / pitches seen            Called-strike%  called strikes / pitches
#   Whiff%        swings-and-misses / swings       First-pitch swing%  swings at pitch 1 / PAs
#   K%, BB%       strikeouts, walks / PA           Looking-K%      called strike 3 / PA
#   ISO           slugging - average (extra bases) Pitches/PA      length of at-bats
#   OF air%       fly balls + line drives to LF/CF/RF / balls in play
#                 (grounders through to the OF and infield pop-ups don't count)
#
# APPROACH (first match wins)
#   Aggressive    Swing% >= p67, or first-pitch swing% >= p75 with Swing% >= p50,
#                 or Swing% >= p60 with Pitches/PA <= p33
#   Passive       average of Called-strike% and Looking-K% ranks >= p60 (freezes on strikes)
#   Disciplined   everyone else (doesn't chase, doesn't freeze)
#
# RESULT (first match wins)
#   Overmatched   average of Whiff% and K% ranks >= p75
#   Power         ISO >= p67 and OF air% >= p50
#   Walker        Swing% <= p33 and (BB% >= p67 or Pitches/PA >= p75)
#                 (least repeatable label: youth walks depend a lot on the pitcher)
#   Contact       everyone else
#
# SMALL SAMPLES
#   Labels (not card stats) use rates pulled toward the age-group average: each stat adds
#   `shrink_k` units of average results (e.g. K% adds {k_k:.0f} PA of average). A kid with few PA
#   lands near the middle; a full season mostly speaks for itself. Card stats are never changed.
#   < {min_label} PA = no label ("—"); {min_label}-{full_label} PA = label + "*".
#   Only kids with {min_pa}+ PA shape the cutoffs. A group needs {min_group}+ such kids for its own
#   cutoffs; smaller groups `use:` the nearest younger group of the same kind.
#
# GROUPS (kids with {min_pa}+ PA)
{groups}
#
# LABEL MIX (% of kids with {min_pa}+ PA, when built)
{mix}
# ===========================================================================

"""


def write(data, mix, path=arch.BASELINE_FILE):
    groups = "\n".join(f"#   {g:12s} {e['kids']:4d} kids" + (f"  -> uses {e['use']}" if "use" in e else "")
                       for g, e in data["groups"].items())
    mix_lines = "\n".join(f"#   {g:12s} " + ", ".join(f"{k} {v}%" for k, v in sorted(m.items(), key=lambda kv: -kv[1]))
                          for g, m in mix.items())
    header = HEADER.format(built=data["built"], seasons=", ".join(data["seasons"]), k_k=data["shrink_k"]["k"],
                           min_label=arch.MIN_LABEL_PA, full_label=arch.FULL_LABEL_PA - 1, min_pa=MIN_PA,
                           min_group=MIN_GROUP, groups=groups, mix=mix_lines)
    body = yaml.safe_dump(data, sort_keys=False, default_flow_style=None, width=200, allow_unicode=True)
    path.write_text(header + body, encoding="utf-8")
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build config/archetype_baselines.yaml")
    ap.add_argument("--seasons", nargs="+", help="season IDs (default: every season in config/)")
    ap.add_argument("--collect", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.collect:
        collect(args.collect)
        return 0
    seasons = args.seasons or [s["id"] for s in list_seasons()]
    existing = arch.load_baselines() or {}
    ignore = existing.get("ignore_team_name_age", DEFAULT_IGNORE)
    print(f"Reading seasons: {', '.join(seasons)}")
    rows = collect_seasons(seasons)
    teams = {r.get("team") for r in rows}
    ignore = [t for t in ignore if t in teams]
    data = build(rows, seasons, ignore)
    mix = label_mix(data, rows)
    path = write(data, mix)
    print(f"✅ {path}")
    for g, e in data["groups"].items():
        print(f"   {g:12s} {e['kids']:4d} kids" + (f" -> uses {e['use']}" if "use" in e else "")
              + "   " + ", ".join(f"{k} {v}%" for k, v in sorted(mix[g].items(), key=lambda kv: -kv[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
