"""
gen_pitching.py — Pitching Savant: Stat Engine + PDF Generator
================================================================
Reads WCWAA play-by-play game files (same .txt format written by Hitting_Scout's
scrape_gc_playbyplay.py), parses pitching statistics from the perspective of any
requested team, computes league percentile rankings within the division, and generates
Baseball-Savant-style PDF pitcher cards.

Workflow Summary:
  1. Import DIVISIONS from Hitting_Scout's scraper (single source of truth for teams)
  2. Locate game files for the requested division/team
  3. Parse each game file: identify pitcher changes, attribute every PA and its
     pitch sequence to the correct pitcher
  4. Aggregate stats across all games (IP, S%, FPS%, Whiff%, FPSO%, FPSH%, K/9,
     K:BB, K%, BB/9, 0BB, GB%, FB+LD%, IP)
  5. Compute league-wide percentile rankings across all pitchers in the division
  6. Generate PDF with one card per pitcher (4 per page) using the Baseball Savant
     slider bar style (single-colour bar + percentile bubble)

Usage:
    python3 gen_pitching.py --division Majors
    python3 gen_pitching.py --division Majors --team Cubs
    python3 gen_pitching.py --division Wild --team "T24 Garnet 11U"
    python3 gen_pitching.py --verbose

Version: 0.1.0
"""

__version__ = "0.1.0"

# ===========================================================================
# Standard library imports
# ===========================================================================
import os
import re
import sys
import math
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import date
from collections import defaultdict

# ===========================================================================
# Third-party imports
# ===========================================================================
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

# ===========================================================================
# DEBUG CONFIGURATION
# Flip to True for detailed diagnostic output while developing.
# ===========================================================================
DEBUG_PITCHER_DETECTION = False  # Log every pitcher change detected
DEBUG_PA_ATTRIBUTION    = False  # Log each PA attributed to which pitcher
DEBUG_STAT_CALC         = False  # Log intermediate stat calculations
DEBUG_PERCENTILES       = False  # Log percentile rank computation

LOGS_DIR = Path(__file__).parent.parent / "Logs"

# ===========================================================================
# PATH SETUP — locate Hitting_Scout scripts + data directories
# ===========================================================================
# This script lives in Dev/Pitching_Savant/Scripts/
# Hitting_Scout lives at the same level: ../Hitting_Scout/Scripts/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)                      # Dev/Pitching_Savant/
DEV_DIR = os.path.dirname(PROJECT_DIR)                          # Dev/
SPRING_DIR = os.path.dirname(DEV_DIR)                          # Spring/
SCOUT_SCRIPTS = os.path.join(DEV_DIR, "Hitting_Scout", "Scripts")

# Import DIVISIONS from Hitting_Scout's scraper — single source of truth
# We use importlib to avoid modifying sys.path permanently
import importlib.util

# Temporarily add Scout's Scripts dir to sys.path so the scraper's own imports
# (e.g. parse_gc_text) resolve correctly when we load it
_scout_in_path = SCOUT_SCRIPTS in sys.path
if not _scout_in_path:
    sys.path.insert(0, SCOUT_SCRIPTS)

_scraper_path = os.path.join(SCOUT_SCRIPTS, "scrape_gc_playbyplay.py")
_spec = importlib.util.spec_from_file_location("_scout_scraper", _scraper_path)
_scout_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scout_mod)
DIVISIONS_RAW = _scout_mod.DIVISIONS

# Also grab gen_hitting.py's DIVISIONS for folder paths
_gen_path = os.path.join(SCOUT_SCRIPTS, "gen_hitting.py")
_spec2 = importlib.util.spec_from_file_location("_gen_hitting", _gen_path)
_gen_mod = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(_gen_mod)
DIVISIONS_PATHS = _gen_mod.DIVISIONS


# ===========================================================================
# LOGGING
# ===========================================================================

def setup_logging(verbose=False):
    """Configure file + stdout logging. Call once in main()."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = date.today().strftime("%Y%m%d") + "_" + time.strftime("%H%M%S")
    log_path = LOGS_DIR / f"gen_pitching_{stamp}.log"

    fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                            datefmt="%H:%M:%S")

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt); fh.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt); sh.setLevel(logging.DEBUG if verbose else logging.INFO)

    log = logging.getLogger("gen_pitching")
    log.setLevel(logging.DEBUG)
    log.addHandler(fh); log.addHandler(sh)
    log.info(f"Pitching Savant v{__version__} — Log → {log_path}")
    return log


logger = logging.getLogger("gen_pitching")
logger.addHandler(logging.NullHandler())


# ===========================================================================
# CONSTANTS — Parsing
# ===========================================================================

# Regex for inning headers (same as gen_hitting.py)
INNING_RE = re.compile(
    r'^=== ?(?:Top|Bottom) (\d+)(?:st|nd|rd|th) - (.+?) ?(?:Majors|Minors)? ?(?:===)?$'
)

# Regex for half-inning direction
HALF_INNING_RE = re.compile(
    r'^=== ?(Top|Bottom) (\d+)(?:st|nd|rd|th) - (.+?) ?(?:Majors|Minors)? ?(?:===)?$'
)

# Regex to detect pitcher named at end of a description line: "..., X Y pitching."
PITCHER_NAMED_RE = re.compile(r',\s+([A-Z][A-Za-z]*)\s+([A-Z][a-z\u00C0-\u024F]*)\s+pitching\b')

# Regex to detect lineup change introducing a new pitcher:
# "Lineup changed: X Y in at pitcher"
LINEUP_CHANGE_RE = re.compile(
    r'Lineup changed:\s+([A-Z][A-Za-z]*)\s+([A-Z][a-z\u00C0-\u024F]*)\s+in at pitcher'
)

# Description line regex (matches the action line like "B A singles to left fielder.")
DESC_RE = re.compile(r'^([A-Z][A-Za-z]*) ([A-Z][a-z]*) (.+)\.$')

# Outcome keywords that appear as the first field in a pipe-delimited line
OUTCOME_KWS = {"Walk", "Single", "Double", "Triple", "Home Run", "Strikeout",
               "Ground Out", "Fly Out", "Pop Out", "Line Out", "Hit By Pitch",
               "Error", "Fielder's Choice", "Double Play",
               "Sacrifice Fly", "Sacrifice Bunt", "Dropped 3rd Strike",
               "Infield Fly"}

SKIP_KWS = ("Inning Ended", "Half-inning ended", "Inning Changed",
            "Current inning", "Count changed", "Score changed",
            "Runner Out", "Scorer Message")

# Pitch token regex (same as gen_hitting.py)
PITCH_TOK = re.compile(
    r'\b(Ball\s+\d+|Strike\s+\d+\s+looking|Strike\s+\d+\s+swinging|Foul(?:\s+tip)?|In\s+play)\b',
    re.IGNORECASE
)

# Outcome codes
WALK = "BB"; HBP = "HBP"; K_SWING = "K_SW"; K_LOOK = "K_LK"
SINGLE = "1B"; DOUBLE = "2B"; TRIPLE = "3B"; HR = "HR"
GO = "GO"; FO = "FO"; PO = "PO"; LO = "LO"; FC = "FC"
ERROR = "E"; DP = "DP"; SF = "SF"; SB = "SB"; UNKNOWN = "?"

BIP_OUTCOMES = {SINGLE, DOUBLE, TRIPLE, HR, GO, FO, PO, LO, FC, ERROR, DP, SF, SB}
HIT_OUTCOMES = {SINGLE, DOUBLE, TRIPLE, HR}
OUT_OUTCOMES = {GO, FO, PO, LO, FC, DP, SF, SB, K_SWING, K_LOOK}
# Outcomes that count as At-Bats (exclude BB, HBP, SF, SB from denominator)
NON_AB = {WALK, HBP, SF, SB}


# ===========================================================================
# OUTCOME PARSER (reused from gen_hitting.py logic)
# ===========================================================================

def parse_outcome(desc, outcome_label):
    """Map a play description + outcome label to an outcome code."""
    dl = desc.lower()
    ol = (outcome_label or "").lower()
    if "is hit by pitch" in dl:                                     return HBP
    if "walks" in dl:                                               return WALK
    if "strikes out swinging" in dl:                                return K_SWING
    if "strikes out looking" in dl:                                 return K_LOOK
    if "strikes out" in dl:                                         return K_SWING
    if "dropped 3rd strike" in ol or "out at first on dropped 3rd strike" in dl: return K_SWING
    if "home run" in dl:                                            return HR
    if "triples" in dl:                                             return TRIPLE
    if "doubles" in dl:                                             return DOUBLE
    if "singles" in dl:                                             return SINGLE
    if "lines into a double play" in dl or "pops into a double play" in dl: return DP
    if "grounds into fielder" in dl:                                return FC
    if "grounds out" in dl:                                         return GO
    if "flies out" in dl:                                           return FO
    if "infield fly" in dl:                                         return FO
    if "lines out" in dl:                                           return LO
    if "pops out" in dl:                                            return PO
    if "out on sacrifice fly" in dl or "sacrifice fly" in dl:      return SF
    if "sacrifice bunt" in dl or "bunts out" in dl:                return SB
    if "reaches on" in dl:                                          return ERROR
    if "foul tip" in dl:                                            return K_SWING
    # Fallback to outcome label
    if "walk" in ol:               return WALK
    if "single" in ol:             return SINGLE
    if "double" in ol and "double play" not in ol: return DOUBLE
    if "triple" in ol:             return TRIPLE
    if "home run" in ol:           return HR
    if "strikeout" in ol:          return K_SWING
    if "ground out" in ol:         return GO
    if "fly out" in ol:            return FO
    if "infield fly" in ol:        return FO
    if "pop out" in ol:            return PO
    if "line out" in ol:           return LO
    if "sacrifice fly" in ol:      return SF
    if "sacrifice bunt" in ol:     return SB
    if "hit by pitch" in ol:       return HBP
    if "error" in ol:              return ERROR
    if "fielder" in ol:            return FC
    if "double play" in ol:        return DP
    return UNKNOWN


def parse_ball_type(desc, oc):
    """Classify a BIP as ground ball, fly ball, or line drive."""
    if oc in (GO, FC, DP, SB): return "GB"
    if oc in (FO, PO, SF):     return "FB"
    if oc == LO:               return "LD"
    dl = desc.lower()
    if "ground ball" in dl:    return "GB"
    if "line drive" in dl:     return "LD"
    if "pop fly" in dl:        return "FB"
    if "flies out" in dl:      return "FB"
    if "ground" in dl:         return "GB"
    if oc == HR:               return "FB"
    return None


# ===========================================================================
# PITCH SEQUENCE PARSER
# ===========================================================================

def parse_pitch_seq(seq_text):
    """
    Parse a pitch sequence string into counts.

    Returns dict with:
        balls, called_str, swing_miss, fouls, in_play, total_pitches, total_swings,
        first_pitch_strike (bool or None)
    """
    c = {
        "balls": 0, "called_str": 0, "swing_miss": 0, "fouls": 0, "in_play": 0,
        "first_pitch_strike": None
    }
    tokens = list(PITCH_TOK.finditer(seq_text))
    for i, m in enumerate(tokens):
        t = m.group(1).lower()
        if t.startswith("ball"):         c["balls"] += 1
        elif "looking" in t:             c["called_str"] += 1
        elif "swinging" in t:            c["swing_miss"] += 1
        elif t.startswith("foul"):       c["fouls"] += 1
        elif t.startswith("in"):         c["in_play"] += 1

        # Determine if first pitch was a strike
        if i == 0:
            if t.startswith("ball"):
                c["first_pitch_strike"] = False
            else:
                # Strike looking, strike swinging, foul, in play — all strikes
                c["first_pitch_strike"] = True

    c["total_pitches"] = c["balls"] + c["called_str"] + c["swing_miss"] + c["fouls"] + c["in_play"]
    c["total_swings"] = c["swing_miss"] + c["fouls"] + c["in_play"]
    c["total_strikes"] = c["called_str"] + c["swing_miss"] + c["fouls"] + c["in_play"]
    return c


# ===========================================================================
# GAME FILE PARSER — PITCHER PERSPECTIVE
# ===========================================================================

def parse_game_for_pitching_team(filepath, pitching_team_key):
    """
    Parse a game file and return a list of PA dicts from the PITCHING perspective
    of pitching_team_key.

    This means we look at the half-innings where the OTHER team is batting, because
    that's when pitching_team_key is on the mound.

    For Majors/Minors:
      - Each game has Team-A vs Team-B
      - Both teams' names appear in inning headers
      - We find innings where the batting team is NOT pitching_team_key

    For Wild/Storm:
      - Each game has Opponent vs our-team
      - Same logic: find innings where a different team name is batting

    Args:
        filepath:          Path to the .txt game file.
        pitching_team_key: The team whose pitchers we want stats for.

    Returns:
        dict: {pitcher_initials: [list of PA dicts]}
        Each PA dict has: outcome, ball_type, pitch_seq, inning, batter_initials
    """
    with open(filepath, encoding="utf-8") as f:
        lines = f.read().splitlines()

    # --- Pre-scan: verify the pitching team actually appears in this game ---
    # The team must appear as a BATTING team in at least one inning header
    # (meaning they're in this game). If they don't appear at all, skip entirely.
    # Example: a Cubs-vs-Braves game file has no Guardians innings, so we skip it.
    teams_in_game = set()
    for line in lines:
        m_pre = HALF_INNING_RE.match(line.strip())
        if m_pre:
            teams_in_game.add(m_pre.group(3).strip())

    if pitching_team_key not in teams_in_game:
        return {}  # This game doesn't involve our team at all

    # Track current state
    current_pitcher = None     # initials of the active pitcher (carry-forward)
    batting_team = None        # team name currently batting
    in_opponent_at_bat = False # True when pitching_team_key is pitching
    cur_inning = 0
    cur_outcome = None
    cur_pitch_lines = []

    # Collect PAs attributed to each pitcher
    pitcher_pas = defaultdict(list)  # {pitcher_initials: [PA dicts]}

    for line in lines:
        line = line.strip()

        # --- Check for inning header ---
        m = HALF_INNING_RE.match(line)
        if m:
            cur_inning = int(m.group(2))
            batting_team = m.group(3).strip()
            # We are pitching when the batting team is NOT us
            in_opponent_at_bat = (batting_team != pitching_team_key)
            cur_outcome = None
            cur_pitch_lines = []

            if DEBUG_PITCHER_DETECTION:
                logger.debug(f"  Inning {cur_inning} — batting: {batting_team} "
                             f"— we pitch: {in_opponent_at_bat}")
            continue

        if not in_opponent_at_bat:
            continue
        if not line or line.startswith("GAME:"):
            continue
        if any(line.startswith(k) for k in SKIP_KWS):
            continue

        # --- Check for pitcher change via "Lineup changed" ---
        lc_match = LINEUP_CHANGE_RE.search(line)
        if lc_match:
            new_pitcher = f"{lc_match.group(1)} {lc_match.group(2)}"
            current_pitcher = new_pitcher
            if DEBUG_PITCHER_DETECTION:
                logger.debug(f"  Pitcher change (lineup): {current_pitcher}")
            # The rest of the line may contain pitch sequence tokens — fall through

        # --- Check for pitcher named in description line ---
        pitcher_match = PITCHER_NAMED_RE.search(line)
        if pitcher_match:
            named_pitcher = f"{pitcher_match.group(1)} {pitcher_match.group(2)}"
            current_pitcher = named_pitcher
            if DEBUG_PITCHER_DETECTION and not lc_match:
                logger.debug(f"  Pitcher named: {current_pitcher}")

        # --- Outcome line (pipe-delimited) ---
        parts = line.split("|")
        raw = parts[0].strip()
        if raw in OUTCOME_KWS:
            cur_outcome = raw
            tail = parts[-1].strip() if len(parts) > 1 else ""
            cur_pitch_lines = [tail] if tail else []
            continue

        # --- Description line (batter action) ---
        m2 = DESC_RE.match(line)
        if m2:
            fi, li, rest = m2.group(1), m2.group(2), m2.group(3)
            # Skip substitution lines
            if rest.startswith("in for") or rest.startswith("in at"):
                continue

            full = f"{fi} {li} {rest}."
            oc = parse_outcome(full, cur_outcome)
            bt = parse_ball_type(full, oc) if oc in BIP_OUTCOMES else None
            pc = parse_pitch_seq(" ".join(cur_pitch_lines))

            pa = {
                "batter": f"{fi} {li}",
                "outcome": oc,
                "ball_type": bt,
                "pitch_seq": pc,
                "inning": cur_inning,
            }

            # Attribute to current pitcher (carry-forward)
            if current_pitcher:
                pitcher_pas[current_pitcher].append(pa)
                if DEBUG_PA_ATTRIBUTION:
                    logger.debug(f"    PA: {fi} {li} → {oc} | pitcher={current_pitcher}")
            else:
                # No pitcher identified yet — this can happen in inning 1
                # before any "pitching" text appears. Store under "UNKNOWN".
                pitcher_pas["UNKNOWN"].append(pa)
                if DEBUG_PA_ATTRIBUTION:
                    logger.debug(f"    PA: {fi} {li} → {oc} | pitcher=UNKNOWN")

            cur_outcome = None
            cur_pitch_lines = []
            continue

        # --- Continuation line (pitch sequence text between outcome and desc) ---
        if cur_outcome is not None:
            cur_pitch_lines.append(line)

    return dict(pitcher_pas)


# ===========================================================================
# STAT AGGREGATION
# ===========================================================================

def compute_pitcher_stats(pitcher_pas_all_games):
    """
    Given a list of all PAs faced by a pitcher (aggregated across games),
    compute the full stat line.

    Args:
        pitcher_pas_all_games: list of PA dicts (from parse_game_for_pitching_team)

    Returns:
        dict with all computed stats, or None if no PAs.
    """
    pas = pitcher_pas_all_games
    if not pas:
        return None

    total_pa = len(pas)

    # --- Count outcomes ---
    strikeouts = sum(1 for p in pas if p["outcome"] in (K_SWING, K_LOOK))
    walks = sum(1 for p in pas if p["outcome"] == WALK)
    hbp = sum(1 for p in pas if p["outcome"] == HBP)
    hits = sum(1 for p in pas if p["outcome"] in HIT_OUTCOMES)
    outs = sum(1 for p in pas if p["outcome"] in OUT_OUTCOMES)

    # --- Outs for IP calculation ---
    # Each PA that results in an out counts as 1 out.
    # SF and SB are outs. DP counts as 2 outs for the pitcher.
    total_outs = 0
    for p in pas:
        if p["outcome"] == DP:
            total_outs += 2
        elif p["outcome"] in OUT_OUTCOMES:
            total_outs += 1

    # IP as decimal: 20 outs = 6.2 (6 full innings + 2 extra outs displayed as .2)
    full_innings = total_outs // 3
    extra_outs = total_outs % 3
    ip_display = f"{full_innings}.{extra_outs}"      # e.g. "6.2"
    ip_exact = total_outs / 3.0                       # e.g. 6.667 for rate stats

    # --- Pitch sequence aggregation ---
    total_pitches = 0
    total_strikes = 0
    total_swings = 0
    total_swing_miss = 0
    fps_count = 0       # PAs where first pitch was a strike
    fps_out = 0         # PAs with FPS that ended in an out
    fps_hit = 0         # PAs with FPS that ended in a hit

    for p in pas:
        pc = p["pitch_seq"]
        total_pitches += pc["total_pitches"]
        total_strikes += pc["total_strikes"]
        total_swings += pc["total_swings"]
        total_swing_miss += pc["swing_miss"]

        if pc["first_pitch_strike"] is True:
            fps_count += 1
            if p["outcome"] in OUT_OUTCOMES:
                fps_out += 1
            elif p["outcome"] in HIT_OUTCOMES:
                fps_hit += 1

    # --- Ball in play type breakdown ---
    bip_total = sum(1 for p in pas if p["outcome"] in BIP_OUTCOMES)
    gb_count = sum(1 for p in pas if p["ball_type"] == "GB")
    fb_count = sum(1 for p in pas if p["ball_type"] == "FB")
    ld_count = sum(1 for p in pas if p["ball_type"] == "LD")

    # --- Zero-walk innings (raw count) ---
    # Group PAs by inning, check which innings had zero walks
    innings_seen = defaultdict(list)
    for p in pas:
        innings_seen[p["inning"]].append(p)
    zero_bb_innings = sum(
        1 for inn_pas in innings_seen.values()
        if not any(pa["outcome"] == WALK for pa in inn_pas)
    )

    # --- Compute rates (with safe division) ---
    def safe_div(num, den):
        return num / den if den > 0 else None

    s_pct = safe_div(total_strikes, total_pitches)
    fps_pct = safe_div(fps_count, total_pa)
    whiff_pct = safe_div(total_swing_miss, total_swings)
    fpso_pct = safe_div(fps_out, fps_count)
    fpsh_pct = safe_div(fps_hit, fps_count)
    k_per_9 = (strikeouts * 9) / ip_exact if ip_exact > 0 else None
    k_bb_ratio = safe_div(strikeouts, walks)
    k_pct = safe_div(strikeouts, total_pa)
    bb_per_9 = (walks * 9) / ip_exact if ip_exact > 0 else None
    gb_pct = safe_div(gb_count, bip_total)
    fb_ld_pct = safe_div(fb_count + ld_count, bip_total)

    return {
        "pa": total_pa,
        "ip_display": ip_display,
        "ip_exact": ip_exact,
        "total_outs": total_outs,
        "strikeouts": strikeouts,
        "walks": walks,
        "hits": hits,
        "s_pct": s_pct,
        "fps_pct": fps_pct,
        "whiff_pct": whiff_pct,
        "fpso_pct": fpso_pct,
        "fpsh_pct": fpsh_pct,
        "k_per_9": k_per_9,
        "k_bb_ratio": k_bb_ratio,
        "k_pct": k_pct,
        "bb_per_9": bb_per_9,
        "zero_bb_innings": zero_bb_innings,
        "gb_pct": gb_pct,
        "fb_ld_pct": fb_ld_pct,
        # Raw counts for Games Started (counted externally)
    }


# ===========================================================================
# PERCENTILE RANKING
# ===========================================================================

# Stat keys and whether they are "low is good" (flipped for percentile)
STAT_KEYS = [
    # (key,         display_label, low_is_good, format_type)
    ("s_pct",       "S%",      False, "pct"),
    ("fps_pct",     "FPS%",    False, "pct"),
    ("whiff_pct",   "Whiff%",  False, "pct"),
    ("fpso_pct",    "FPSO%",   False, "pct"),
    ("k_per_9",     "K/9",     False, "dec1"),
    ("k_bb_ratio",  "K:BB",    False, "dec1"),
    ("k_pct",       "K%",      False, "pct"),
    ("zero_bb_innings", "0BB", False, "int"),
    ("gb_pct",      "GB%",     False, "pct"),
    ("fb_ld_pct",   "FB+LD%",  False, "pct"),
    ("ip_exact",    "IP",      False, "ip"),
    ("fpsh_pct",    "FPSH%",   True,  "pct"),   # FLIP: lower = better
    ("bb_per_9",    "BB/9",    True,  "dec1"),   # FLIP: lower = better
]


def compute_percentile_rank(value, all_values, low_is_good):
    """
    Compute percentile rank (0–100) for a value within a list of all values.

    For normal stats (high is good): rank = % of pitchers you are >= to.
    For flipped stats (low is good): rank = % of pitchers you are <= to.

    This ensures red ALWAYS means "great" and blue ALWAYS means "poor".

    Args:
        value:       The pitcher's stat value.
        all_values:  List of all pitchers' values for this stat.
        low_is_good: If True, lower raw value = better = higher percentile.

    Returns:
        Integer 0–100 percentile.
    """
    if value is None or not all_values:
        return 50  # Default to average if we can't compute

    # Remove None values
    valid = [v for v in all_values if v is not None]
    if not valid:
        return 50

    n = len(valid)
    if n == 1:
        return 50  # Solo pitcher = average by definition

    if low_is_good:
        # Lower is better: count how many are >= this value (worse or equal)
        rank = sum(1 for v in valid if v >= value) / n
    else:
        # Higher is better: count how many are <= this value (worse or equal)
        rank = sum(1 for v in valid if v <= value) / n

    # Convert to 0–100 scale
    return max(1, min(99, int(round(rank * 100))))


def compute_all_percentiles(all_pitcher_stats):
    """
    Given a dict of {pitcher_name: stats_dict}, compute percentile ranks for
    every stat for every pitcher.

    Args:
        all_pitcher_stats: dict {pitcher_key: stats_dict}

    Returns:
        dict {pitcher_key: [(label, value_str, percentile_int), ...]}
    """
    # Build pools: for each stat key, collect all values across all pitchers
    pools = {}
    for key, label, low_is_good, fmt in STAT_KEYS:
        pools[key] = [s[key] for s in all_pitcher_stats.values() if s is not None]

    result = {}
    for pitcher_key, stats in all_pitcher_stats.items():
        if stats is None:
            continue
        rows = []
        for key, label, low_is_good, fmt in STAT_KEYS:
            val = stats[key]
            pct = compute_percentile_rank(val, pools[key], low_is_good)

            # Format the display value
            if val is None:
                val_str = "—"
            elif fmt == "pct":
                val_str = f"{int(round(val * 100))}%"
            elif fmt == "dec1":
                val_str = f"{val:.1f}"
            elif fmt == "ip":
                val_str = stats["ip_display"]
            elif fmt == "int":
                val_str = str(int(val))
            else:
                val_str = str(val)

            rows.append({
                "label": label,
                "value": val_str,
                "pct": pct,
                "low_is_good": low_is_good,
            })
        result[pitcher_key] = rows
    return result


# ===========================================================================
# PDF GENERATION — Baseball Savant style slider cards
# ===========================================================================

# Design constants (same as pilot_card.py)
PAGE_W, PAGE_H = letter
MARGIN     = 0.45 * inch
GUTTER     = 0.18 * inch
COLS       = 2
ROWS       = 2
CARDS_PER_PAGE = COLS * ROWS
CARD_W = (PAGE_W - 2 * MARGIN - (COLS - 1) * GUTTER) / COLS
CARD_H = (PAGE_H - 2 * MARGIN - (ROWS - 1) * GUTTER) / ROWS

HEADER_H   = 44
STAT_ROW_H = 20
LABEL_W    = 58
VALUE_W    = 36
BAR_H      = 9
BUBBLE_R   = 7
PADDING    = 8

FONT_NAME      = "Helvetica"
FONT_BOLD      = "Helvetica-Bold"
FONT_SIZE_HDR  = 11.5
FONT_SIZE_SUBHDR = 9
FONT_SIZE_STAT = 7.5
FONT_SIZE_BUBBLE = 6.5
FONT_SIZE_AXIS = 8

# Colours
COL_DARK_BLUE  = colors.Color(0.09, 0.18, 0.55)
COL_LIGHT_BLUE = colors.Color(0.42, 0.62, 0.87)
COL_GREY       = colors.Color(0.78, 0.78, 0.78)
COL_PINK       = colors.Color(0.90, 0.55, 0.52)
COL_RED        = colors.Color(0.82, 0.11, 0.11)
COL_CARD_BG    = colors.Color(0.91, 0.91, 0.91)  # Slightly darker grey for contrast against white page
COL_HEADER_BG  = colors.HexColor("#f5a623")   # Amber/orange — matches Scout hitting cards
COL_WHITE      = colors.white
COL_BLACK      = colors.black
COL_NAVY       = colors.HexColor("#1a2b4a")   # Dark navy — header text on orange
COL_DIVIDER    = colors.Color(0.80, 0.80, 0.80)


def pct_to_color(pct):
    """Map percentile (0–100) to the appropriate band colour."""
    if pct >= 90: return COL_RED
    if pct >= 60: return COL_PINK
    if pct >= 40: return COL_GREY
    if pct >= 10: return COL_LIGHT_BLUE
    return COL_DARK_BLUE


def draw_gradient_bar(c, x, y, bar_w, pct):
    """Draw a solid-colour bar whose length = percentile position."""
    bar_y = y - BAR_H / 2
    fill_w = bar_w * (pct / 100)
    c.setFillColor(pct_to_color(pct))
    c.rect(x, bar_y, fill_w, BAR_H, stroke=0, fill=1)


def draw_bubble(c, x, y, bar_w, pct):
    """Draw the percentile circle at the tip of the bar."""
    bubble_x = x + bar_w * (pct / 100)
    c.setFillColor(pct_to_color(pct))
    c.setStrokeColor(COL_WHITE)
    c.setLineWidth(0.8)
    c.circle(bubble_x, y, BUBBLE_R, stroke=1, fill=1)
    c.setFillColor(COL_WHITE)
    c.setFont(FONT_BOLD, FONT_SIZE_BUBBLE)
    c.drawCentredString(bubble_x, y - FONT_SIZE_BUBBLE / 2 + 1, str(pct))


def draw_axis_labels(c, card_x, axis_y, card_inner_w):
    """Draw POOR / AVG / GREAT header above stat rows."""
    bar_x = card_x + LABEL_W
    bar_w = card_inner_w - LABEL_W - VALUE_W
    c.setFont(FONT_NAME, FONT_SIZE_AXIS)
    c.setFillColor(COL_DARK_BLUE)
    c.drawString(bar_x, axis_y, "POOR")
    c.setFillColor(COL_GREY)
    c.drawCentredString(bar_x + bar_w / 2, axis_y, "AVG")
    c.setFillColor(COL_RED)
    c.drawRightString(bar_x + bar_w, axis_y, "GREAT")


def draw_stat_row(c, card_x, row_y, card_inner_w, stat, row_idx):
    """Draw one stat row: label + bar + bubble + value."""
    label = stat["label"]
    value = stat["value"]
    pct   = stat["pct"]

    bar_x = card_x + LABEL_W
    bar_w = card_inner_w - LABEL_W - VALUE_W
    bar_y_ctr = row_y

    # Row divider
    if row_idx > 0:
        c.setStrokeColor(COL_DIVIDER)
        c.setLineWidth(0.3)
        c.line(card_x, row_y + STAT_ROW_H / 2,
               card_x + card_inner_w, row_y + STAT_ROW_H / 2)

    # Stat label
    c.setFillColor(COL_BLACK)
    c.setFont(FONT_NAME, FONT_SIZE_STAT)
    c.drawString(card_x, bar_y_ctr - FONT_SIZE_STAT / 2 + 1, label)

    # Bar + bubble
    draw_gradient_bar(c, bar_x, bar_y_ctr, bar_w, pct)
    draw_bubble(c, bar_x, bar_y_ctr, bar_w, pct)

    # Raw value
    c.setFillColor(COL_BLACK)
    c.setFont(FONT_BOLD, FONT_SIZE_STAT)
    val_x = card_x + card_inner_w - VALUE_W + 3
    c.drawString(val_x, bar_y_ctr - FONT_SIZE_STAT / 2 + 1, value)


# Path to the pitcher silhouette image (from Baseball Savant)
PITCHER_ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pitcher_icon.png")


def draw_pitcher_icon(c, x, y, size=20):
    """
    Draw the Baseball Savant pitcher silhouette by embedding the actual PNG.
    Falls back to a simple circle if the image file is missing.

    The image has a transparent background and is dark-coloured, so we draw
    it at the specified size inside the dark header — the white background of
    the image blends with the header when rendered at small size.

    Args:
        c:    ReportLab canvas.
        x, y: Centre point where the icon should appear.
        size: Height of the rendered image in points.
    """
    if os.path.isfile(PITCHER_ICON_PATH):
        # The image is roughly square; render at size × size
        img_w = size * 0.85
        img_h = size
        # drawImage takes bottom-left corner
        c.drawImage(PITCHER_ICON_PATH,
                    x - img_w / 2, y - img_h / 2,
                    width=img_w, height=img_h,
                    mask='auto',  # honour PNG transparency
                    preserveAspectRatio=True)
    else:
        # Fallback: simple circle placeholder
        c.setFillColor(COL_WHITE)
        c.circle(x, y, size / 3, stroke=0, fill=1)


def draw_pitcher_card(c, card_x, card_y, pitcher_info):
    """
    Draw a complete pitcher card.

    Args:
        c:            ReportLab canvas.
        card_x, card_y: Bottom-left corner of card.
        pitcher_info: dict with keys: name, jersey, team, gs, ip, stats (list of row dicts)
    """
    # Card background
    c.setFillColor(COL_CARD_BG)
    c.setStrokeColor(COL_DIVIDER)
    c.setLineWidth(0.5)
    c.roundRect(card_x, card_y, CARD_W, CARD_H, 4, stroke=1, fill=1)

    # Header
    c.setFillColor(COL_HEADER_BG)
    c.roundRect(card_x, card_y + CARD_H - HEADER_H, CARD_W, HEADER_H, 4, stroke=0, fill=1)
    c.rect(card_x, card_y + CARD_H - HEADER_H, CARD_W, HEADER_H / 2, stroke=0, fill=1)

    # Pitcher icon (right side of header, vertically centred)
    icon_x = card_x + CARD_W - PADDING - 12
    icon_y = card_y + CARD_H - HEADER_H + HEADER_H * 0.35
    draw_pitcher_icon(c, icon_x, icon_y, size=18)

    c.setFillColor(COL_NAVY)
    c.setFont(FONT_BOLD, FONT_SIZE_HDR)
    name_str = f"{pitcher_info['name']}  {pitcher_info['jersey']}"
    c.drawString(card_x + PADDING, card_y + CARD_H - HEADER_H + HEADER_H * 0.55, name_str)

    c.setFont(FONT_NAME, FONT_SIZE_SUBHDR)
    sub_str = f"{pitcher_info['team']}   GS: {pitcher_info['gs']}   IP: {pitcher_info['ip']}"
    c.drawString(card_x + PADDING, card_y + CARD_H - HEADER_H + HEADER_H * 0.15, sub_str)

    # Axis labels
    inner_x = card_x + PADDING
    inner_w = CARD_W - 2 * PADDING
    axis_y = card_y + CARD_H - HEADER_H - 10
    draw_axis_labels(c, inner_x, axis_y, inner_w)

    # Stat rows
    first_row_y = axis_y - STAT_ROW_H * 0.8
    for idx, stat in enumerate(pitcher_info["stats"]):
        row_y = first_row_y - idx * STAT_ROW_H
        draw_stat_row(c, inner_x, row_y, inner_w, stat, idx)


def card_origin(slot_idx):
    """Return (x, y) bottom-left of card at slot_idx (0–3)."""
    col = slot_idx % COLS
    row = slot_idx // COLS
    x = MARGIN + col * (CARD_W + GUTTER)
    y = PAGE_H - MARGIN - (row + 1) * CARD_H - row * GUTTER
    return x, y


def generate_pitching_pdf(team_key, pitcher_cards, output_path):
    """
    Generate a full PDF with all pitcher cards for a team.

    Args:
        team_key:      Team name (used in PDF title).
        pitcher_cards: List of pitcher_info dicts ready for draw_pitcher_card().
        output_path:   Absolute path where the PDF will be written.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=letter)
    c.setTitle(f"{team_key} — Pitching Savant 2026")

    for i, card in enumerate(pitcher_cards):
        slot = i % CARDS_PER_PAGE
        if slot == 0 and i > 0:
            c.showPage()
        cx, cy = card_origin(slot)
        draw_pitcher_card(c, cx, cy, card)

    c.save()
    logger.info(f"  PDF → {output_path}")


# ===========================================================================
# GAME FILE DISCOVERY
# ===========================================================================

def find_game_files(scorebooks_dir):
    """
    Find all .txt game files in a scorebooks directory.
    Includes both regular and -Reviewed.txt files.

    Returns list of absolute paths.
    """
    files = []
    if not os.path.isdir(scorebooks_dir):
        return files
    for fname in os.listdir(scorebooks_dir):
        if fname.endswith(".txt"):
            files.append(os.path.join(scorebooks_dir, fname))
    return sorted(files)


# ===========================================================================
# ROSTER LOADING (for jersey numbers / display names)
# ===========================================================================

def load_rosters_json(path):
    """Load rosters.json and return the full dict."""
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_roster_txt(path):
    """
    Load a Wild/Storm roster.txt file.
    Returns dict {initials: {"display": "Name #jersey", "jersey": "N"}}
    """
    roster = {}
    if not os.path.isfile(path):
        return roster
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",", 1)
            if len(parts) == 2:
                initials = parts[0].strip()
                display = parts[1].strip()
                jersey = ""
                if "#" in display:
                    jersey = display.split("#")[-1].strip()
                roster[initials] = {"display": display, "jersey": jersey}
    return roster


def dedup_pitcher_names(pitcher_dict):
    """
    Merge initials-only pitcher entries into their full-name counterparts.

    E.g. "K D" merges into "Kilean D" because both share last token "D"
    and the first character of "K" matches the first character of "Kilean".

    Args:
        pitcher_dict: dict {pitcher_name: [PA_list]}

    Returns:
        New dict with short-form names merged into long-form names.
    """
    # Separate names into short-form (first token is single char) vs full-form
    short_names = {}
    full_names = {}
    for name, pas in pitcher_dict.items():
        parts = name.split()
        if len(parts) >= 2 and len(parts[0]) == 1:
            short_names[name] = pas
        else:
            full_names[name] = pas

    # For each short name, try to find a matching full name
    merged = dict(full_names)  # start with all full names
    for short_name, short_pas in short_names.items():
        parts = short_name.split()
        first_initial = parts[0][0].upper()
        last_token = parts[-1].upper()

        # Find candidate full names with same last token and first initial
        match = None
        for full_name in full_names:
            fparts = full_name.split()
            if (len(fparts) >= 2
                    and fparts[-1].upper() == last_token
                    and fparts[0][0].upper() == first_initial):
                match = full_name
                break

        if match:
            merged[match] = merged[match] + short_pas
        else:
            # No full-name match found; discard initials-only entries
            # (they are unresolved and cannot be tied to a roster player)
            pass

    return merged


# ===========================================================================
# DIVISION RUNNERS
# ===========================================================================

def run_league_division(division_name, team_filter=None, verbose=False):
    """
    Run pitching analysis for an org-level division (Majors or Minors).

    Parses ALL games in the division to build league-wide percentile pools,
    then generates PDFs for the requested team(s).
    """
    div_cfg = DIVISIONS_PATHS.get(division_name)
    if not div_cfg:
        logger.error(f"Unknown division: {division_name}")
        return

    scorebooks_dir = div_cfg["scorebooks"]
    output_dir = div_cfg["output"]
    roster_json_path = div_cfg.get("roster_json", "")
    teams = div_cfg.get("teams", [])

    rosters = load_rosters_json(roster_json_path)
    game_files = find_game_files(scorebooks_dir)

    if not game_files:
        logger.warning(f"  No game files found in {scorebooks_dir}")
        return

    logger.info(f"  {division_name}: {len(game_files)} game files, "
                f"{len(teams)} teams")

    # --- Pass 1: Parse ALL games for ALL teams to build league percentile pools ---
    # For each team, find all games where they are pitching
    all_pitcher_stats = {}  # {f"{team_key}|{pitcher_initials}": stats}
    team_pitcher_map = defaultdict(lambda: defaultdict(list))  # {team_key: {pitcher: [PAs]}}
    # Track per-game PAs so we can compute GS (games where pitcher threw inning 1)
    team_pitcher_games = defaultdict(lambda: defaultdict(list))  # {team_key: {pitcher: [per_game_pas_list]}}

    for team_name, coach_last in teams:
        team_key = f"{team_name}-{coach_last}"
        # Handle the A's/As discrepancy
        csv_name = div_cfg.get("csv_overrides", {}).get(team_name, team_name)

        for fpath in game_files:
            pitcher_pas = parse_game_for_pitching_team(fpath, team_key)
            for pitcher, pas in pitcher_pas.items():
                if pitcher == "UNKNOWN":
                    continue
                team_pitcher_map[team_key][pitcher].extend(pas)
                team_pitcher_games[team_key][pitcher].append(pas)

    # Compute stats for every pitcher in the division
    for team_key, pitchers in team_pitcher_map.items():
        for pitcher, pas in pitchers.items():
            stats = compute_pitcher_stats(pas)
            if stats:
                all_pitcher_stats[f"{team_key}|{pitcher}"] = stats

    logger.info(f"  {division_name}: {len(all_pitcher_stats)} pitchers found across all teams")

    # --- Compute percentiles across all pitchers in division ---
    percentiles = compute_all_percentiles(all_pitcher_stats)

    # --- Pass 2: Generate PDFs for requested team(s) ---
    for team_name, coach_last in teams:
        team_key = f"{team_name}-{coach_last}"

        if team_filter:
            if team_filter.lower() not in team_key.lower():
                continue

        pitchers_for_team = team_pitcher_map.get(team_key, {})
        if not pitchers_for_team:
            logger.warning(f"  {team_key}: no pitching data found")
            continue

        # Build card list sorted by IP (most innings first)
        cards = []
        for pitcher, pas in sorted(
            pitchers_for_team.items(),
            key=lambda kv: compute_pitcher_stats(kv[1])["ip_exact"] if compute_pitcher_stats(kv[1]) else 0,
            reverse=True
        ):
            full_key = f"{team_key}|{pitcher}"
            if full_key not in percentiles:
                continue

            stats = all_pitcher_stats[full_key]
            stat_rows = percentiles[full_key]

            # Look up display name + jersey from rosters.json
            # display already contains "FirstName L. #jersey" so we don't need separate jersey
            team_roster = rosters.get(team_key, {})
            if pitcher in team_roster:
                display_name = team_roster[pitcher].get("display", pitcher)
            else:
                display_name = pitcher  # fallback to initials
            jersey = ""  # already embedded in display_name

            # GS = Games Started: count games where this pitcher had a PA in
            # inning 1 (meaning they were on the mound from the start).
            gs = 0
            for game_pas in team_pitcher_games[team_key][pitcher]:
                if any(pa["inning"] == 1 for pa in game_pas):
                    gs += 1

            cards.append({
                "name": display_name,
                "jersey": jersey,
                "team": team_key,
                "gs": gs,
                "ip": stats["ip_display"],
                "stats": stat_rows,
            })

        if not cards:
            logger.warning(f"  {team_key}: no pitcher cards to generate")
            continue

        # Output path: same folder as scouting reports
        safe_team = team_name.replace(" ", "_")
        pdf_path = os.path.join(output_dir,
                                f"{safe_team}_{coach_last}-Scout-Pitching_2026.pdf")
        generate_pitching_pdf(team_key, cards, pdf_path)
        logger.info(f"  {team_key}: {len(cards)} pitchers → PDF")


def run_travel_division(division_name, team_filter=None, verbose=False):
    """
    Run pitching analysis for a travel division (Wild or Storm).

    Each opponent team has its own folder with Games/ subfolder.
    Teams are discovered dynamically from the filesystem (same as gen_hitting).
    """
    div_cfg = DIVISIONS_PATHS.get(division_name)
    if not div_cfg:
        logger.error(f"Unknown division: {division_name}")
        return

    base_dir = div_cfg.get("wild_base", "")
    if not base_dir or not os.path.isdir(base_dir):
        logger.warning(f"  {division_name}: base directory not found: {base_dir}")
        return

    # Discover opponent team folders (skip Sample_Opponent, README, hidden)
    teams = []
    for name in sorted(os.listdir(base_dir)):
        team_dir = os.path.join(base_dir, name)
        if not os.path.isdir(team_dir):
            continue
        if name.startswith(".") or name == "Sample_Opponent":
            continue
        teams.append(name)

    if not teams:
        logger.warning(f"  {division_name}: no teams configured")
        return

    # --- Pass 1: Collect all pitcher data across ALL opponents ---
    all_pitcher_stats = {}
    team_pitcher_map = defaultdict(lambda: defaultdict(list))

    for team_name in teams:
        team_dir = os.path.join(base_dir, team_name)
        games_dir = os.path.join(team_dir, "Games")
        if not os.path.isdir(games_dir):
            games_dir = team_dir

        if not os.path.isdir(games_dir):
            continue

        game_files = find_game_files(games_dir)
        if not game_files:
            continue

        # Load roster for jersey numbers
        roster_path = os.path.join(team_dir, "roster.txt")
        roster = load_roster_txt(roster_path)

        for fpath in game_files:
            pitcher_pas = parse_game_for_pitching_team(fpath, team_name)
            for pitcher, pas in pitcher_pas.items():
                if pitcher == "UNKNOWN":
                    continue
                team_pitcher_map[team_name][pitcher].extend(pas)

    # Deduplicate initials-only names (e.g. "K D" → "Kilean D")
    for team_name in list(team_pitcher_map.keys()):
        team_pitcher_map[team_name] = dedup_pitcher_names(
            dict(team_pitcher_map[team_name])
        )

    # Compute stats for every pitcher
    for team_name, pitchers in team_pitcher_map.items():
        for pitcher, pas in pitchers.items():
            stats = compute_pitcher_stats(pas)
            if stats:
                all_pitcher_stats[f"{team_name}|{pitcher}"] = stats

    logger.info(f"  {division_name}: {len(all_pitcher_stats)} pitchers found")

    # Compute percentiles across the division
    percentiles = compute_all_percentiles(all_pitcher_stats)

    # --- Pass 2: Generate PDFs for requested team(s) ---
    for team_name in teams:

        if team_filter:
            if team_filter.lower() not in team_name.lower():
                continue

        pitchers_for_team = team_pitcher_map.get(team_name, {})
        if not pitchers_for_team:
            continue

        team_dir = os.path.join(base_dir, team_name) if base_dir else ""
        roster_path = os.path.join(team_dir, "roster.txt")
        roster = load_roster_txt(roster_path)
        games_dir = os.path.join(team_dir, "Games")
        if not os.path.isdir(games_dir):
            games_dir = team_dir
        game_files = find_game_files(games_dir)

        cards = []
        for pitcher, pas in sorted(
            pitchers_for_team.items(),
            key=lambda kv: compute_pitcher_stats(kv[1])["ip_exact"] if compute_pitcher_stats(kv[1]) else 0,
            reverse=True
        ):
            full_key = f"{team_name}|{pitcher}"
            if full_key not in percentiles:
                continue

            stats = all_pitcher_stats[full_key]
            stat_rows = percentiles[full_key]

            jersey = ""
            if pitcher in roster:
                jersey = f"#{roster[pitcher]['jersey']}" if roster[pitcher].get("jersey") else ""

            # GS estimate
            gs = sum(
                1 for fpath in game_files
                if pitcher in parse_game_for_pitching_team(fpath, team_name)
            )

            cards.append({
                "name": pitcher,
                "jersey": jersey,
                "team": team_name,
                "gs": gs,
                "ip": stats["ip_display"],
                "stats": stat_rows,
            })

        if not cards:
            continue

        safe = team_name.replace(" ", "_")
        pdf_path = os.path.join(team_dir, f"{safe}-Scout-Pitching_2026.pdf")
        generate_pitching_pdf(team_name, cards, pdf_path)
        logger.info(f"  {team_name}: {len(cards)} pitchers → PDF")


# ===========================================================================
# CLI ENTRY POINT
# ===========================================================================

def main():
    """CLI entry point — parses --division, --team, --verbose."""
    parser = argparse.ArgumentParser(
        description="Pitching Savant: Generate Baseball-Savant-style pitcher cards from WCWAA game files."
    )
    parser.add_argument("--division", "-d",
                        help="Division to process: Majors, Minors, Wild, Storm, or 'all'")
    parser.add_argument("--team", "-t",
                        help="Filter to a single team (partial match)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose/debug output")
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger.info(f"Pitching Savant v{__version__}")

    divisions_to_run = []
    if not args.division or args.division.lower() == "all":
        divisions_to_run = ["Majors", "Minors", "Wild", "Storm"]
    else:
        divisions_to_run = [args.division]

    for div in divisions_to_run:
        logger.info(f"Processing division: {div}")
        if div in ("Majors", "Minors"):
            run_league_division(div, team_filter=args.team, verbose=args.verbose)
        elif div in ("Wild", "Storm"):
            run_travel_division(div, team_filter=args.team, verbose=args.verbose)
        else:
            logger.error(f"Unknown division: {div}")


if __name__ == "__main__":
    main()
