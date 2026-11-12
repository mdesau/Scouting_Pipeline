"""
archetypes.py — batter archetype labels (Approach × Result) from frozen per-age baselines (BUG-024)
================================================================================================
Each kid is compared with kids his age: the division's `age:` plus league vs. travel picks a group
("league 9U", "travel 12U", …) in config/archetype_baselines.yaml, which holds that group's
percentile cutoffs. The file is built once by `python -m scout.hitting.build_archetype_baselines`
and reused every season, so a label means the same thing all season and year to year.

Small samples: before ranking, each rate is pulled toward the group average by a stat-specific
amount (`shrink_k`, measured from first-half vs. second-half repeatability). This only steers the
label — the stats printed on the cards are never changed.

Rules (pNN = percentile rank within the age group; full text in the baselines file header):
  Approach  Aggressive  swing% ≥ p67, or first-pitch swing ≥ p75 with swing% ≥ p50,
                        or swing% ≥ p60 with pitches/PA ≤ p33
            Passive     average of called-strike% and looking-K% ranks ≥ p60
            Disciplined everyone else
  Result    Overmatched average of whiff% and K% ranks ≥ p75
            Power       ISO ≥ p67 and OF air balls (FB/LD to LF/CF/RF) per ball in play ≥ p50
            Walker      swing% ≤ p33 and (BB% ≥ p67 or pitches/PA ≥ p75)
            Contact     everyone else
  PA gate   < 5 PA → no label ("—"); 5–9 PA → label + "*"
"""

import logging
from bisect import bisect_right
from functools import lru_cache

import yaml

from scout.season_config import SCOUT_ROOT

logger = logging.getLogger(__name__)

BASELINE_FILE = SCOUT_ROOT / "config" / "archetype_baselines.yaml"
OF_ZONES = ("LF", "CF", "RF")
PCT_POINTS = list(range(0, 101, 5))   # percentile points stored per stat in the baselines file
MIN_LABEL_PA, FULL_LABEL_PA = 5, 10

# stat → (numerator, denominator) keys of counts()
STATS = {
    "swing":  ("swings", "pitches"),
    "cstr":   ("called", "pitches"),
    "whiff":  ("whiffs", "swings"),
    "fps":    ("fp_sw", "fp_seen"),
    "k":      ("k", "pa"),
    "kl":     ("kl", "pa"),
    "bb":     ("bb", "pa"),
    "iso":    ("xb", "ab"),
    "of_air": ("of_air", "bip"),
    "ppa":    ("pitches", "pa"),
}


def counts(b):
    """Raw counts behind the archetype stats, from a gen_hitting.compute_stats() batter dict."""
    zd = b.get("zone_detail") or {}
    swings = b["p_swing_miss"] + b["p_fouls"] + b["p_in_play"]
    return {
        "pa": b["pa"], "ab": b["ab"], "bb": b["bb"], "xb": b["tb"] - b["h"],
        "k": b["k_sw"] + b["k_lk"], "kl": b["k_lk"], "bip": b["bip"],
        "of_air": sum(zd.get(z, {}).get("fb_ld", 0) for z in OF_ZONES),
        "pitches": b["p_balls"] + b["p_called_str"] + swings,
        "swings": swings, "whiffs": b["p_swing_miss"], "called": b["p_called_str"],
        "fp_sw": b["fpt_swings"], "fp_seen": b["fpt_swings"] + b["fpt_takes"],
    }


def group_key(kind, age):
    """'league 9U' / 'travel 12U', or None when the division has no `age:`."""
    return f"{kind} {age}" if age else None


@lru_cache(maxsize=None)
def load_baselines(path=BASELINE_FILE):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_group(baselines, group):
    """The group whose cutoffs apply: its own, its `use:` fallback, or the nearest age of the same kind."""
    groups = baselines["groups"]
    if group not in groups:
        kind, age = group.split()
        same = [g for g in groups if g.startswith(kind + " ") and "use" not in groups[g]]
        if not same:
            return None
        group = min(same, key=lambda g: (abs(int(g.split()[1][:-1]) - int(age[:-1])), g))
    return groups[group].get("use", group)


def pct_rank(cuts, value):
    """Percentile rank (0–100) of value against cutoffs stored at PCT_POINTS (linear in between)."""
    i = bisect_right(cuts, value) - 1
    if i < 0:
        return 0.0
    if i >= len(cuts) - 1:
        return 100.0
    span = cuts[i + 1] - cuts[i]
    return PCT_POINTS[i] + (PCT_POINTS[i + 1] - PCT_POINTS[i]) * ((value - cuts[i]) / span if span else 0)


def shrunk_rate(c, stat, mean, k):
    """Rate pulled toward the group mean: adds k denominator units of league-average results."""
    num, den = STATS[stat]
    return (c[num] + k * mean) / (c[den] + k)


def ranks(c, base, shrink_k):
    return {s: pct_rank(base["pct"][s], shrunk_rate(c, s, base["mean"][s], shrink_k[s])) for s in STATS}


def classify(p):
    """(approach, result) from percentile ranks p."""
    if p["swing"] >= 67 or (p["fps"] >= 75 and p["swing"] >= 50) or (p["swing"] >= 60 and p["ppa"] <= 33):
        approach = "Aggressive"
    elif (p["cstr"] + p["kl"]) / 2 >= 60:
        approach = "Passive"
    else:
        approach = "Disciplined"

    if (p["whiff"] + p["k"]) / 2 >= 75:
        result = "Overmatched"
    elif p["iso"] >= 67 and p["of_air"] >= 50:
        result = "Power"
    elif p["swing"] <= 33 and (p["bb"] >= 67 or p["ppa"] >= 75):
        result = "Walker"
    else:
        result = "Contact"
    return approach, result


_warned = set()


def get_label(b, group, baselines=None):
    """'Aggressive Power', 'Passive Walker*' (5–9 PA), or None (< 5 PA, or no baseline for the group)."""
    if b["pa"] < MIN_LABEL_PA:
        return None
    baselines = baselines or load_baselines()
    resolved = resolve_group(baselines, group) if baselines and group else None
    if not resolved:
        if group not in _warned:
            _warned.add(group)
            logger.warning(f"No archetype baseline for '{group}' — add `age:` to the division in the season "
                           f"YAML or rebuild {BASELINE_FILE.name}; archetypes show '—'.")
        return None
    approach, result = classify(ranks(counts(b), baselines["groups"][resolved], baselines["shrink_k"]))
    return f"{approach} {result}" + ("*" if b["pa"] < FULL_LABEL_PA else "")
