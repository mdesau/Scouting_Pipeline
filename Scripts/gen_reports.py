#!/usr/bin/env python3
"""
WCWAA 2026 Spring — Consolidated Scouting Report Generator
Handles Majors, Minors, Wild, and Storm divisions.

Supports:
  - Majors: Full league pre-scan for archetype percentiles
  - Minors: Rangers C K disambiguation, Beau Amerine roster addition
  - Wild: Opponent folders, optional roster.txt, fixed thresholds
  - Batting order tracking: avg_batting_pos per batter
  - -Reviewed.txt marking after successful parse
  - Timing metrics per team and total
  - 2-page card layout (players split evenly across pages 1–2)
  - Single-page summary + notes (page 3)
"""

import os, re, csv, json, math, time, argparse, logging
from collections import defaultdict
from datetime import date
from pathlib import Path

TODAY = date.today().strftime("%B %d, %Y")

# ---------------------------------------------------------------------------
# DEBUG CONFIGURATION
# ---------------------------------------------------------------------------
# These flags control HEAVY debug output that dumps raw data to the log file.
# For light debugging, use --verbose (shows all logger.debug on screen).
#
# WHY THIS MATTERS:
#   When a player's PA count looks wrong or an archetype label seems off,
#   you need to see the intermediate parsing steps. These flags expose:
#   - Each PA as it's extracted from the game file (outcome, zone, pitch seq)
#   - Archetype scoring breakdown (approach calc, result thresholds)
#   Without them, you'd have to add temporary print() calls, debug, then
#   remember to remove them — error-prone and time-wasting.
# ---------------------------------------------------------------------------
DEBUG_PA_PARSING   = False   # Log every PA as it's parsed from game files
DEBUG_ARCHETYPES   = False   # Log archetype scoring details per batter
DEBUG_PITCH_SEQ    = False   # Log token-by-token pitch sequence parsing
LOGS_DIR = Path(__file__).parent.parent / "Logs"

def setup_logging(verbose=False):
    """Configure module logger: file (DEBUG) + stdout (INFO). Call once in main().

    Args:
        verbose: If True, stdout handler shows DEBUG-level messages.
                 Default is INFO-only on screen; DEBUG always goes to log file.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    stamp    = date.today().strftime("%Y%m%d") + "_" + time.strftime("%H%M%S")
    log_path = LOGS_DIR / f"gen_reports_{stamp}.log"

    fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                            datefmt="%H:%M:%S")

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt); fh.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt); sh.setLevel(logging.DEBUG if verbose else logging.INFO)

    log = logging.getLogger("gen_reports")
    log.setLevel(logging.DEBUG)
    log.addHandler(fh)
    log.addHandler(sh)
    log.info(f"Log → {log_path}")
    return log

# Module-level logger (handlers added by setup_logging() at runtime).
# Falls back to NullHandler so the module is safe to import without calling main().
logger = logging.getLogger("gen_reports")
logger.addHandler(logging.NullHandler())

# Resolve Spring folder relative to this script's own location.
# When the script lives in Spring/Scripts/, ".." points to Spring/.
# This works both locally (Scripts folder) and in Cowork sessions.
BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

DIVISIONS = {
    "Majors": {
        "scorebooks":      f"{BASE}/Majors/Reports/Scorebooks",
        "output":          f"{BASE}/Majors/Reports/Scouting_Reports",
        "csv":             f"{BASE}/Majors/Reports/Spring 2026 Draft Results.xlsx - Majors.csv",
        "roster_json":     f"{BASE}/Majors/Reports/rosters.json",
        "verify_json":     f"{BASE}/Majors/Reports/box_verify.json",
        "csv_overrides":   {"Diamondbacks": "Dbacks"},
        "roster_additions": {},
        "league_scan": True,
        "label_suffix": "Majors",
        "teams": [
            ("Guardians","Esau"), ("Royals","Hall"), ("Diamondbacks","Vandiford"),
            ("Marlins","McLendon"), ("Dodgers","Pearson"), ("As","Blanco"),
            ("Braves","Rue"), ("Twins","Ewart"), ("Padres","Schick"),
            ("Cubs","Holtzer"), ("Rays","Madero"),
        ],
    },
    "Minors": {
        "scorebooks":      f"{BASE}/Minors/Reports/Scorebooks",
        "output":          f"{BASE}/Minors/Reports/Scouting_Reports",
        "csv":             f"{BASE}/Minors/Reports/Spring 2026 Draft Results.xlsx - Minors.csv",
        "roster_json":     f"{BASE}/Minors/Reports/rosters.json",
        "verify_json":     f"{BASE}/Minors/Reports/box_verify.json",
        "csv_overrides":   {},
        "roster_additions": {"Mets-Hornung": {"B A": "B. Amerine"}},
        "league_scan": True,
        "label_suffix": "Minors",
        "teams": [
            ("Astros","Barbour"), ("Dodgers","Winchester"), ("Padres","Midkiff"),
            ("Reds","Naturale"), ("Rangers","Leonard"), ("Yankees","DePasquale"),
            ("Marlins","Eberlin"), ("Guardians","Plunkett"), ("Angels","Casper"),
            ("Braves","Brooks"), ("Cubs","Verlinde"), ("Brewers","Linnenkohl"),
            ("Rays","Pearson"), ("Mets","Hornung"),
        ],
    },
    "Wild": {
        "wild_base":   f"{BASE}/Wild",
        "league_scan": False,
        "label_suffix": "Weddington Wild",
        "fixed_thresholds": {"slg_top33": 0.450, "c_bot33": 0.500, "bb_top33": 0.200},
    },
    "Storm": {
        "wild_base":   f"{BASE}/Storm",
        "league_scan": False,
        "label_suffix": "Weddington Storm",
        "fixed_thresholds": {"slg_top33": 0.450, "c_bot33": 0.500, "bb_top33": 0.200},
    },
}

# ---------------------------------------------------------------------------
# 1. Roster
# ---------------------------------------------------------------------------
def build_rosters(csv_path, roster_additions=None):
    if roster_additions is None:
        roster_additions = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    coaches, teams, player_rows = rows[0][1:], rows[-1][1:], rows[1:-1]
    rosters = {}
    for col_idx, (coach, team) in enumerate(zip(coaches, teams)):
        coach_last = coach.split()[-1]
        team_clean = team.replace("'", "")
        team_key   = f"{team_clean}-{coach_last}"
        roster = {}
        for prow in player_rows:
            if col_idx + 1 >= len(prow): continue
            full_name = prow[col_idx + 1].strip()
            if not full_name: continue
            parts = full_name.split()
            if len(parts) < 2: continue
            initials = f"{parts[0][0]} {parts[1][0]}"
            display  = f"{parts[0][0]}. {' '.join(parts[1:])}"
            roster[initials] = display
        roster.update(roster_additions.get(team_key, {}))
        rosters[team_key] = roster
    return rosters


def load_box_rosters(json_path, roster_additions=None):
    """
    Load team rosters from a box-score-scraped rosters.json file.

    Returns:
        (rosters, all_collision_maps)

        rosters: {team_key: {initials_or_disam_key: display_str}}
            Same shape as build_rosters() — the rest of the pipeline is unchanged.
            When two players on a team share initials, their entries are stored
            under disambiguated 5-char keys (e.g. "Bri A", "Ben A") rather than
            the original 2-char key ("B A").

        all_collision_maps: {team_key: {2-char-init: [5-char-key-early, 5-char-key-late]}}
            Passed through to parse_game_for_team() so it can split plate
            appearances between disambiguated players based on batting order.

    roster_additions: optional {team_key: {initials: display_str}} manual overrides.
    """
    if roster_additions is None:
        roster_additions = {}
    if not os.path.exists(json_path):
        logger.warning(f"rosters.json not found at {json_path} — falling back to empty rosters")
        logger.warning("Run scrape_box_scores.py first to build the roster file.")
        return {}, {}
    with open(json_path, encoding="utf-8") as f:
        raw = json.load(f)
    rosters = {}
    all_collision_maps = {}
    for team_key, players in raw.items():
        cmap = players.get("_collision_map", {})
        if cmap:
            all_collision_maps[team_key] = cmap
        roster = {
            init: entry["display"]
            for init, entry in players.items()
            if not init.startswith("_") and isinstance(entry, dict)
        }
        roster.update(roster_additions.get(team_key, {}))
        rosters[team_key] = roster
    return rosters, all_collision_maps


def load_box_verify(json_path):
    """
    Load per-game box score verification data from box_verify.json.
    Returns dict keyed by game_id, or empty dict if file missing.
    """
    if not os.path.exists(json_path):
        return {}
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def _disambiguate_pas(pas, collision_map):
    """
    When two players on a team share 2-char initials (e.g. "B A" for both
    Brian Allen and Ben Allen), replace every PA's initials with the correct
    disambiguated 5-char key ("Bri A" or "Ben A") based on within-game
    batting-order occurrence order.

    collision_map: {2-char-init: [5-char-key-earlier-batter, 5-char-key-later-batter]}
        The FIRST key in the list is the player who bats EARLIER in the lineup,
        so the 1st, 3rd, 5th, … occurrences (0-indexed: 0, 2, 4, …) map to that
        player, and 2nd, 4th, 6th, … map to the second.

    PAs are sorted by inning (chronological) before counting so the occurrence
    counter is stable regardless of whether game files are stored in forward or
    reverse chronological order.
    """
    if not collision_map:
        return pas

    # Determine which initials in this game actually appear in a collision
    game_inits = {pa["initials"] for pa in pas}
    active_collisions = {init: keys for init, keys in collision_map.items()
                         if init in game_inits}
    if not active_collisions:
        return pas

    # Tag each PA with its position in the original list for stable sort
    for i, pa in enumerate(pas):
        pa["_orig_idx"] = i

    # Sort chronologically: inning first, then original file order within inning
    sorted_pas = sorted(pas, key=lambda p: (p["inning"], p["_orig_idx"]))

    # Count occurrences of each collided initials and assign disambiguated key
    counters = {init: 0 for init in active_collisions}
    for pa in sorted_pas:
        init = pa["initials"]
        if init in active_collisions:
            keys = active_collisions[init]
            pa["initials"] = keys[counters[init] % len(keys)]
            counters[init] += 1

    # Clean up temporary field
    for pa in pas:
        pa.pop("_orig_idx", None)

    return pas


def verify_box_score(team_key, batters, box_verify):
    """
    Layer 4 — cross-check parsed stats against box score totals.
    Compares each batter's parsed AB and BB against box score AB/BB.
    Logs a warning for any discrepancy > 1 in either stat.

    box_verify: the full dict from load_box_verify().
    """
    if not box_verify:
        return

    # Build box score totals per initials for this team across all games
    bs_totals = defaultdict(lambda: {"ab": 0, "bb": 0, "so": 0})
    for game_id, game in box_verify.items():
        for side in ("away", "home"):
            if game.get(f"{side}_team") == team_key or \
               game.get(f"{side}_team", "").replace(" ", "_") in team_key:
                for p in game.get(side, []):
                    init = p["initials"]
                    bs_totals[init]["ab"] += p.get("ab", 0)
                    bs_totals[init]["bb"] += p.get("bb", 0)
                    bs_totals[init]["so"] += p.get("so", 0)

    if not bs_totals:
        return  # This team not found in box verify data (expected for opponents)

    for b in batters:
        init = b["initials"]
        bs   = bs_totals.get(init)
        if not bs:
            continue
        ab_diff = abs(b["ab"] - bs["ab"])
        bb_diff = abs(b["bb"] - bs["bb"])
        if ab_diff > 1:
            logger.warning(
                f"  ⚠ BOX-VERIFY [{team_key}] {init}: "
                f"parsed AB={b['ab']} vs box score AB={bs['ab']} (diff={ab_diff})"
            )
        if bb_diff > 1:
            logger.warning(
                f"  ⚠ BOX-VERIFY [{team_key}] {init}: "
                f"parsed BB={b['bb']} vs box score BB={bs['bb']} (diff={bb_diff})"
            )

# ---------------------------------------------------------------------------
# 2. Outcome constants
# ---------------------------------------------------------------------------
WALK="BB"; HBP="HBP"; K_SWING="K_SW"; K_LOOK="K_LK"
SINGLE="1B"; DOUBLE="2B"; TRIPLE="3B"; HR="HR"
GO="GO"; FO="FO"; PO="PO"; LO="LO"; FC="FC"; ERROR="E"; DP="DP"; SF="SF"; SB="SB"; UNKNOWN="?"
BIP_OUTCOMES = {SINGLE,DOUBLE,TRIPLE,HR,GO,FO,PO,LO,FC,ERROR,DP,SF,SB}

FIELDER_ZONES = [
    ("left fielder","LF"),("center fielder","CF"),("right fielder","RF"),
    ("left field","LF"),("center field","CF"),("right field","RF"),
    ("shortstop","SS"),("third baseman","3B"),
    ("second baseman","2B"),("first baseman","1B"),
    ("pitcher","P"),("catcher","HP"),
]

def extract_zone(desc):
    dl = desc.lower()
    hits = [(dl.find(kw), zone) for kw, zone in FIELDER_ZONES if dl.find(kw) != -1]
    return sorted(hits)[0][1] if hits else None

def parse_ball_type(desc, oc):
    if oc in (GO,FC,DP,SB): return "GB"   # bunt/ground-ball outcomes
    if oc in (FO,PO,SF):    return "FB"   # fly-ball outcomes (SF is a fly ball)
    if oc == LO:            return "LD"
    dl = desc.lower()
    if "ground ball" in dl: return "GB"
    if "line drive" in dl:  return "LD"
    if "pop fly" in dl:     return "FB"
    if "flies out" in dl:   return "FB"
    if "ground" in dl:      return "GB"
    if oc == HR:            return "FB"
    return None

def parse_outcome(desc, ol):
    dl = desc.lower(); ol = (ol or "").lower()
    if "is hit by pitch" in dl:                                         return HBP
    if "walks" in dl:                                                   return WALK
    if "strikes out swinging" in dl:                                    return K_SWING
    if "strikes out looking" in dl:                                     return K_LOOK
    if "strikes out" in dl:                                             return K_SWING
    if "dropped 3rd strike" in ol or "out at first on dropped 3rd strike" in dl: return K_SWING
    if "home run" in dl:                                                return HR
    if "triples" in dl:                                                 return TRIPLE
    if "doubles" in dl:                                                 return DOUBLE
    if "singles" in dl:                                                 return SINGLE
    if "lines into a double play" in dl or "pops into a double play" in dl: return DP
    if "grounds into fielder" in dl:                                    return FC
    if "grounds out" in dl:                                             return GO
    if "flies out" in dl:                                               return FO
    if "infield fly" in dl:                                             return FO  # Infield fly rule → flyball out
    if "lines out" in dl:                                               return LO
    if "pops out" in dl:                                                return PO
    if "out on sacrifice fly" in dl or "sacrifice fly" in dl:          return SF
    if "sacrifice bunt" in dl or "bunts out" in dl:                    return SB
    if "reaches on" in dl:                                              return ERROR
    if "walk" in ol:                               return WALK
    if "single" in ol:                             return SINGLE
    if "double" in ol and "double play" not in ol: return DOUBLE
    if "triple" in ol:                             return TRIPLE
    if "home run" in ol:                           return HR
    if "strikeout" in ol:                          return K_SWING
    if "ground out" in ol:                         return GO
    if "fly out" in ol:                            return FO
    if "infield fly" in ol:                        return FO  # Infield fly rule → flyball out
    if "pop out" in ol:                            return PO
    if "line out" in ol:                           return LO
    if "sacrifice fly" in ol:                      return SF
    if "sacrifice bunt" in ol:                     return SB
    if "hit by pitch" in ol:                       return HBP
    if "error" in ol:                              return ERROR
    if "fielder" in ol:                            return FC
    if "double play" in ol:                        return DP
    return UNKNOWN

# ---------------------------------------------------------------------------
# 3. Pitch sequence parsing — includes FPT (First Pitch Take)
# ---------------------------------------------------------------------------
PITCH_TOK = re.compile(
    r'\b(Ball\s+\d+|Strike\s+\d+\s+looking|Strike\s+\d+\s+swinging|Foul|In\s+play)\b',
    re.IGNORECASE
)

def parse_pitch_seq(seq_text):
    """
    Returns pitch count dict.
    fpt_take: True = first pitch was taken (ball or called strike)
              False = first pitch was swung at (swinging strike, foul, in play)
              None = no pitch data / couldn't determine
    """
    c = {"balls":0,"called_str":0,"swing_miss":0,"fouls":0,"in_play":0,"fpt_take":None}
    tokens = list(PITCH_TOK.finditer(seq_text))
    for i, m in enumerate(tokens):
        t = m.group(1).lower()
        if t.startswith("ball"):        c["balls"] += 1
        elif "looking" in t:            c["called_str"] += 1
        elif "swinging" in t:           c["swing_miss"] += 1
        elif t == "foul":               c["fouls"] += 1
        elif t.startswith("in"):        c["in_play"] += 1
        if i == 0:
            if t.startswith("ball") or "looking" in t:
                c["fpt_take"] = True   # took first pitch
            else:
                c["fpt_take"] = False  # swung at first pitch
    return c

# ---------------------------------------------------------------------------
# 4. Game file parser
# ---------------------------------------------------------------------------
# Handles both:
#   Minors: ===Bottom 3rd - Mets-Hornung===
#   Majors: === Top 6th - Guardians-Esau ===
#   Majors: === Bottom 6th - Twins-Ewart Majors ===
#   Tolerates missing closing ===  (some -Reviewed.txt files lost it during manual editing)
INNING_RE  = re.compile(r'^=== ?(?:Top|Bottom) (\d+)(?:st|nd|rd|th) - (.+?) ?(?:Majors|Minors)? ?(?:===)?$')
DESC_RE    = re.compile(r'^([A-Z][A-Za-z]*) ([A-Z][a-z]*) (.+)\.$')  # first group handles initials ("H"), double-initials ("TJ"), or full names ("Dylan"); last group handles single initial or full last name
OUTCOME_KWS = {"Walk","Single","Double","Triple","Home Run","Strikeout",
               "Ground Out","Fly Out","Pop Out","Line Out","Hit By Pitch",
               "Error","Fielder's Choice","Double Play",
               "Sacrifice Fly","Sacrifice Bunt","Dropped 3rd Strike"}
SKIP_KWS   = ("Inning Ended","Half-inning ended","Inning Changed",
              "Current inning","Count changed","Score changed",
              "Runner Out","Scorer Message")

def parse_game_for_team(filepath, team_key, collision_map=None):
    """
    Parse one game file and return a list of PA dicts for team_key.

    collision_map: optional {2-char-init: [5-char-key-earlier, 5-char-key-later]}
        When provided, plate appearances whose initials are a known collision
        (e.g. "B A" shared by Brian Allen and Ben Allen) are automatically
        reassigned to the correct disambiguated key ("Bri A" or "Ben A") using
        within-game batting-order occurrence order.
    """
    with open(filepath, encoding='utf-8') as f:
        lines = f.read().splitlines()
    pas = []
    in_target = False; cur_inning = 0; cur_outcome = None; cur_pitch_lines = []
    for line in lines:
        line = line.strip()
        m = INNING_RE.match(line)
        if m:
            cur_inning = int(m.group(1))
            in_target  = (m.group(2) == team_key)
            cur_outcome = None; cur_pitch_lines = []
            continue
        if not in_target or not line or line.startswith("GAME:"): continue
        if any(line.startswith(k) for k in SKIP_KWS):            continue
        parts = line.split("|")
        raw = parts[0].strip()
        if raw in OUTCOME_KWS:
            cur_outcome = raw
            # Pitch sequence often lives on the same line after the pipes
            # e.g. "Single |  | SCR9 9 - IT9S 10Strike 1 looking, Ball 1, Foul, In play."
            # Grab everything after the last "|" and seed cur_pitch_lines with it
            tail = parts[-1].strip() if len(parts) > 1 else ""
            cur_pitch_lines = [tail] if tail else []
            continue
        m2 = DESC_RE.match(line)
        if m2:
            fi, li, rest = m2.group(1), m2.group(2), m2.group(3)
            # Skip substitution notes like "C M in for pitcher K R, Foul, In play."
            if rest.startswith("in for") or rest.startswith("in at"):
                continue
            full = f"{fi} {li} {rest}."
            oc   = parse_outcome(full, cur_outcome)
            zone = extract_zone(full) if oc not in (WALK,HBP,K_SWING,K_LOOK) else None
            bt   = parse_ball_type(full, oc) if oc not in (WALK,HBP,K_SWING,K_LOOK) else None
            pc   = parse_pitch_seq(" ".join(cur_pitch_lines))
            pas.append({"initials":f"{fi} {li}","outcome":oc,"zone":zone,"ball_type":bt,
                        "is_bip":oc in BIP_OUTCOMES,"k_swing":oc==K_SWING,"k_look":oc==K_LOOK,
                        "inning":cur_inning,"pitch":pc})
            cur_outcome = None; cur_pitch_lines = []; continue
        if cur_outcome is not None:
            cur_pitch_lines.append(line)

    # Apply duplicate-initials disambiguation if a collision map was provided
    if collision_map:
        pas = _disambiguate_pas(pas, collision_map)

    return pas


# ---------------------------------------------------------------------------
# 4b. Verification helpers
# ---------------------------------------------------------------------------

def check_inning_continuity(filepath, team_key):
    """
    Layer 1 — scan a parsed game file and check for inning sequence gaps for
    team_key.  Returns a (possibly empty) list of warning strings.
    """
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    innings_found = set()
    for m in re.finditer(
            r'^=== ?(Top|Bottom) (\d+)(?:st|nd|rd|th) - (.+?) ?(?:Majors|Minors)? ?===',
            content, re.MULTILINE):
        if m.group(3).strip() == team_key:
            innings_found.add(int(m.group(2)))

    if not innings_found:
        return [f"  ⚠ INNING: no innings found for '{team_key}' — check team name spelling"]

    warnings = []
    max_inn = max(innings_found)
    # Always check from 1 — a missing inning 1 is just as significant as a
    # mid-game gap and would corrupt our batting-order inference
    missing = [n for n in range(1, max_inn + 1) if n not in innings_found]
    if missing:
        warnings.append(
            f"  ⚠ INNING GAP: '{team_key}' missing inning(s) "
            f"{missing} (found: {sorted(innings_found)}) in {os.path.basename(filepath)}"
        )
    return warnings


def check_batting_order(fname, pas):
    """
    Layer 3 — given PAs from ONE game in chronological order, check that PA
    counts per batter are consistent with the batting-order invariant:

        For every adjacent pair (batter[i], batter[i+1]) in lineup order:
            PA[i] - PA[i+1]  ∈ {0, 1}

    Returns a (possibly empty) list of warning strings.
    Assumes no substitutions (confirmed by league rules).

    NOTE: Layer 4 (box score cross-check) now provides ground-truth AB/BB
    verification for all divisions. Layer 3 is retained for debug diagnostics
    only — its warnings are logged at DEBUG level and do not surface in normal
    output or contribute to the per-game warning count reported to the user.
    """
    if not pas:
        return []

    # Sort by inning number so chronological first-appearance is correct even
    # when the parsed file is in reverse-chronological order (GC "Reverse
    # Chronological" mode).  Python's sort is stable so within-inning PA
    # order is preserved.
    ordered = sorted(pas, key=lambda p: p["inning"])

    # Infer lineup order from chronological first-appearance
    lineup_pos = {}
    for pa in ordered:
        init = pa["initials"]
        if init not in lineup_pos:
            lineup_pos[init] = len(lineup_pos) + 1   # 1-indexed

    # Count PAs per batter in this game
    pa_counts = {}
    for pa in pas:
        pa_counts[pa["initials"]] = pa_counts.get(pa["initials"], 0) + 1

    lineup = sorted(lineup_pos.keys(), key=lambda x: lineup_pos[x])
    warnings = []
    for i in range(len(lineup) - 1):
        cur_b, nxt_b = lineup[i], lineup[i + 1]
        cur_c, nxt_c = pa_counts[cur_b], pa_counts[nxt_b]
        delta = cur_c - nxt_c

        if nxt_c > cur_c:
            warnings.append(
                f"  ⚠ ORDER [{os.path.basename(fname)}]: "
                f"{nxt_b} (#{i+2}, {nxt_c} PA) has MORE PAs than "
                f"{cur_b} (#{i+1}, {cur_c} PA) — possible missed PA or parse error"
            )
        elif delta > 1:
            warnings.append(
                f"  ⚠ GAP [{os.path.basename(fname)}]: "
                f"{cur_b} (#{i+1}, {cur_c} PA) → {nxt_b} (#{i+2}, {nxt_c} PA) "
                f"— delta {delta}, expected max 1 — possible missed inning"
            )
    return warnings


def verify_game(fpath, team_key, pas, fname):
    """
    Run all verification layers for one game file.  Prints warnings to console.
    Returns total warning count for the caller to accumulate.
    """
    warnings = []

    # Layer 1: inning continuity
    warnings += check_inning_continuity(fpath, team_key)

    # Layer 2: unknown outcomes
    unknowns = [pa for pa in pas if pa["outcome"] == UNKNOWN]
    if unknowns:
        warnings.append(
            f"  ⚠ UNKNOWN [{os.path.basename(fname)}]: "
            f"{len(unknowns)} PA(s) with unrecognised outcome — "
            f"batters: {', '.join(pa['initials'] for pa in unknowns)}"
        )

    # Layer 3: batting order PA consistency (debug only — superseded by Layer 4)
    order_warnings = check_batting_order(fname, pas)
    for w in order_warnings:
        logger.debug(w.strip())   # debug level: not shown in normal output

    for w in warnings:
        logger.warning(w.strip())
    return len(warnings)


# ---------------------------------------------------------------------------
# 5. Stat aggregation
# ---------------------------------------------------------------------------
def compute_stats(pas, roster):
    batters = defaultdict(lambda: {
        "pa":0,"ab":0,"h":0,"tb":0,"bb":0,"hbp":0,
        "singles":0,"doubles":0,"triples":0,"hrs":0,
        "k_sw":0,"k_lk":0,"bip":0,"gb":0,"fb_ld":0,
        "zones":defaultdict(int),
        "zone_detail":defaultdict(lambda:{"gb":0,"fb_ld":0,"other":0}),
        "p_balls":0,"p_called_str":0,"p_swing_miss":0,"p_fouls":0,"p_in_play":0,
        "fpt_takes":0,"fpt_swings":0,        # FPT tracking
        "batting_positions": defaultdict(list),  # {game_id: [first_game_seq, ...]}
    })
    for pa in pas:
        b = batters[pa["initials"]]
        b["pa"] += 1
        oc = pa["outcome"]
        if oc == WALK:          b["bb"] += 1
        elif oc == HBP:         b["hbp"] += 1
        elif oc in (SF, SB):    pass   # sacrifice: not an AB, handled via is_bip
        else:
            b["ab"] += 1
            if oc == SINGLE:   b["h"]+=1; b["tb"]+=1; b["singles"]+=1
            elif oc == DOUBLE: b["h"]+=1; b["tb"]+=2; b["doubles"]+=1
            elif oc == TRIPLE: b["h"]+=1; b["tb"]+=3; b["triples"]+=1
            elif oc == HR:     b["h"]+=1; b["tb"]+=4; b["hrs"]+=1
            elif oc == K_SWING: b["k_sw"]+=1
            elif oc == K_LOOK:  b["k_lk"]+=1
        if pa["is_bip"]:
            b["bip"]+=1
            bt = pa["ball_type"]
            z  = pa["zone"]
            if bt == "GB":
                b["gb"]+=1;    btype_key="gb"
            elif bt in ("FB","LD"):
                b["fb_ld"]+=1; btype_key="fb_ld"
            else:
                # Infer ball type from zone when not explicit in description
                # Outfield zones → FB/LD (blue); infield zones → GB (amber)
                if   z in ("LF","CF","RF"):       b["fb_ld"]+=1; btype_key="fb_ld"
                elif z in ("3B","2B","1B","P"):   b["gb"]+=1;    btype_key="gb"
                else:                                             btype_key="other"
            if z:
                b["zones"][z]+=1
                b["zone_detail"][z][btype_key]+=1
        pc = pa.get("pitch", {})
        b["p_balls"]      += pc.get("balls", 0)
        b["p_called_str"] += pc.get("called_str", 0)
        b["p_swing_miss"] += pc.get("swing_miss", 0)
        b["p_fouls"]      += pc.get("fouls", 0)
        b["p_in_play"]    += pc.get("in_play", 0)
        fpt = pc.get("fpt_take")
        if fpt is True:  b["fpt_takes"] += 1
        elif fpt is False: b["fpt_swings"] += 1

        # Batting order tracking: record first appearance per game
        game_id = pa.get("game_id")
        game_seq = pa.get("game_seq")
        if game_id is not None and game_seq is not None:
            if game_id not in b["batting_positions"]:
                b["batting_positions"][game_id] = game_seq

    results = []
    for init, b in batters.items():
        display = roster.get(init, f"?{init}?")
        ab=b["ab"]; h=b["h"]; bb=b["bb"]; hbp=b["hbp"]; tb=b["tb"]
        bip=b["bip"]; gb=b["gb"]; fb_ld=b["fb_ld"]; k_sw=b["k_sw"]
        avg = (h/ab)            if ab>0 else None
        obp = ((h+bb+hbp)/(ab+bb+hbp)) if (ab+bb+hbp)>0 else None
        slg = (tb/ab)           if ab>0 else None
        # C% = contact rate: (AB - K) / AB  (all strikeouts penalize, BB/HBP excluded from AB)
        k_total = k_sw + b["k_lk"]
        c_pct  = ((ab - k_total) / ab)  if ab > 0 else None
        gb_pct = (gb/bip)           if bip>0 else None
        fb_pct = (fb_ld/bip)        if bip>0 else None
        swings  = b["p_swing_miss"] + b["p_fouls"] + b["p_in_play"]
        total_p = b["p_balls"] + b["p_called_str"] + swings
        sm_pct   = (b["p_swing_miss"] / swings)  if swings > 0 else None
        cstr_pct = (b["p_called_str"] / total_p) if total_p > 0 else None
        fpt_total = b["fpt_takes"] + b["fpt_swings"]
        fpt_pct   = (b["fpt_takes"] / fpt_total)  if fpt_total > 0 else None

        # Batting order: compute average first-appearance position across games
        batting_positions = b["batting_positions"]
        if batting_positions:
            avg_batting_pos = sum(batting_positions.values()) / len(batting_positions)
        else:
            avg_batting_pos = 999  # default if no batting order data

        results.append({
            "initials":init,"display":display,"pa":b["pa"],
            "ab":ab,"h":h,"bb":bb,"hbp":hbp,"tb":tb,"bip":bip,
            "k_sw":k_sw,"k_lk":b["k_lk"],"gb":gb,"fb_ld":fb_ld,
            "avg":avg,"obp":obp,"slg":slg,"c_pct":c_pct,
            "gb_pct":gb_pct,"fb_pct":fb_pct,
            "sm_pct":sm_pct,"cstr_pct":cstr_pct,"fpt_pct":fpt_pct,
            "avg_batting_pos":avg_batting_pos,
            "zones_sorted":sorted(b["zones"].items(), key=lambda x:-x[1]),
            "zone_detail":dict(b["zone_detail"]),
            "singles":b["singles"],"doubles":b["doubles"],
            "triples":b["triples"],"hrs":b["hrs"],
        })
    results.sort(key=lambda x:(x.get("avg_batting_pos", 999), x["display"]))
    return results

def fmt_avg(v):
    if v is None: return "---"
    if v >= 1.0:  return f"{v:.3f}"
    return f".{int(round(v*1000)):03d}"

def fmt_pct(v):
    if v is None: return "--"
    return f"{int(round(v*100))}%"

# ---------------------------------------------------------------------------
# 6. Archetype — 2-word batter label (Approach × Result)
#
# Approach: Aggressive / Disciplined / Passive
#   - Aggressive : FPT% < 0.40  (swings first pitch >60% of the time)
#   - Passive    : FPT% > 0.70  (takes first pitch >70%, often freezes on strikes)
#   - Disciplined: FPT% 0.40–0.70 AND OBP − AVG ≥ 0.060 (takes pitches selectively)
#   - Falls back to Aggressive (low FPT) or Passive (high FPT) if gap too small
#
# Result: Power / Contact / Overmatched / Walker  (roster-relative percentiles)
#   - Walker     : top-third BB/PA in roster
#   - Overmatched: bottom-third C% in roster  (too many strikeouts)
#   - Power      : top-third SLG in roster AND SLG ≥ 1.5× AVG
#   - Contact    : everything else (default — puts ball in play)
#
# PA gate: < 5 PA → None (card shows "—")
#          5–9 PA → label + "*"
#         10+  PA → clean label
# ---------------------------------------------------------------------------
def _roster_percentiles(all_batters):
    """Compute roster-relative thresholds for Result labels."""
    def pct33(vals):
        s = sorted(v for v in vals if v is not None)
        if not s: return None
        return s[max(0, len(s) - len(s)//3 - 1)]   # top-33rd cutoff

    slg_vals = [b["slg"] for b in all_batters if b["ab"] > 0]
    c_vals   = [b["c_pct"] for b in all_batters if b["ab"] > 0]
    bb_pa    = [b["bb"]/b["pa"] if b["pa"] > 0 else None for b in all_batters]

    return {
        "slg_top33": pct33(slg_vals),
        "c_bot33":   sorted(v for v in c_vals if v is not None)[len(c_vals)//3] if c_vals else None,
        "bb_top33":  pct33(bb_pa),
    }

def get_archetype(b, all_batters=None):
    pa  = b["pa"]
    if pa < 5:
        return None   # too small — caller renders "—"

    fpt   = b.get("fpt_pct")
    avg   = b["avg"]
    obp   = b["obp"]
    slg   = b["slg"]
    sm    = b.get("sm_pct")      # swing-and-miss %
    cstr  = b.get("cstr_pct")    # called strike %

    # ── Approach ────────────────────────────────────────────────────────────
    # SM% vs CStr% relationship is checked FIRST — it overrides FPT%-based inference.
    # High SM% >> CStr% means the player is swinging aggressively and missing,
    # not getting frozen — that's Aggressive regardless of how often they take
    # the first pitch.
    obp_avg_gap = (obp - avg) if (obp is not None and avg is not None) else 0

    sm_aggressive = (
        sm   is not None and cstr is not None
        and sm   >= 0.55                # meaningful swing-and-miss rate
        and sm   >  cstr * 1.5         # swinging >> getting frozen → attacking the ball
    )

    if sm_aggressive:
        approach = "Aggressive"
    elif fpt is None:
        approach = "Disciplined"       # no FPT data — fall back gracefully
    elif fpt < 0.40:
        approach = "Aggressive"
    elif obp_avg_gap >= 0.060:
        # Wide OBP-AVG gap signals selectivity (walks) — Disciplined, not Passive
        approach = "Disciplined"
    elif fpt > 0.70:
        approach = "Passive"
    elif fpt < 0.55:
        approach = "Aggressive"
    else:
        approach = "Passive"

    # ── Result ──────────────────────────────────────────────────────────────
    if all_batters:
        thresholds = _roster_percentiles(all_batters)
    else:
        thresholds = {"slg_top33": 0.450, "c_bot33": 0.500, "bb_top33": 0.200}

    slg_top = thresholds["slg_top33"]
    c_bot   = thresholds["c_bot33"]
    bb_top  = thresholds["bb_top33"]

    bb_pa    = b["bb"] / b["pa"] if b["pa"] > 0 else 0
    h        = b["h"];  bb = b["bb"]
    bb_share = bb / (h + bb) if (h + bb) > 0 else 0
    c_pct    = b["c_pct"]   # use directly — 0.0 is valid data, not missing

    # Walker: walks must be the primary OBP engine, not a side effect of hitting.
    # Requires all four conditions:
    #   1. BB/PA in top-33% of league          (walks frequently)
    #   2. BB/(H+BB) > 33%                     (walks meaningful share of times on base)
    #   3. C% < 70%                            (not a contact/power hitter — hits drive OBP for those)
    #   4. OBP − AVG ≥ .100                    (walks visibly elevating OBP above hit production)
    # A player who hits .350 and also walks isn't a Walker — AVG/SLG tell that story better.
    is_walker = (
        bb_top is not None and bb_pa >= bb_top
        and bb_share > 0.33
        and (c_pct is None or c_pct < 0.70)
        and obp_avg_gap >= 0.100
    )

    # Overmatched: hard triggers (either alone sufficient) OR soft combined trigger.
    #   Hard 1: SM% > 50%             — swinging and missing too often regardless of context
    #   Hard 2: C% ≤ bottom-33%       — making contact below league floor
    #   Soft:   SM% ≥ 35% AND C% < 65% AND AVG < .250
    #           Catches "Disciplined Overmatched" mis-labels: a batter who takes pitches
    #           (high FPT%) and draws some walks can land in Disciplined even when their
    #           elevated whiff rate + weak contact + weak AVG paint a clear overmatched
    #           picture. Low CStr% does NOT rescue from this — it just means they're
    #           chasing rather than getting frozen, which is its own problem.
    is_overmatched = (
        (sm is not None and sm > 0.50)
        or (c_bot is not None and c_pct is not None and c_pct <= c_bot)
        or (sm  is not None and sm  >= 0.35
            and c_pct is not None and c_pct < 0.65
            and avg  is not None and avg  < 0.250)
    )

    # Power: top-33% SLG AND (SLG ≥ 1.2× AVG OR ISO ≥ .120)
    iso = (slg - avg) if (slg is not None and avg is not None) else 0
    is_power = (
        slg_top is not None and slg is not None
        and slg >= slg_top
        and avg is not None and avg > 0
        and (slg >= 1.2 * avg or iso >= 0.120)
    )

    if is_walker:        result = "Walker"
    elif is_overmatched: result = "Overmatched"
    elif is_power:       result = "Power"
    else:                result = "Contact"

    label = f"{approach} {result}"
    if pa < 10:
        label += "*"
    return label

# ---------------------------------------------------------------------------
# 7. Pitching approach — mapped from archetype label (strip "*" before lookup)
# ---------------------------------------------------------------------------
PITCHING_APPROACH = {
    "Aggressive Power":      "Edges + Mix Speed",
    "Aggressive Contact":    "Edges + Mix Speed",
    "Aggressive Overmatched":"Climb the Ladder",
    "Aggressive Walker":     "Outside - In",
    "Disciplined Power":     "Keep Mixing",
    "Disciplined Contact":   "Keep Mixing",
    "Disciplined Overmatched":"Attack the Zone",
    "Disciplined Walker":    "Attack the Zone",
    "Passive Power":         "Attack & Expand",
    "Passive Contact":       "Attack & Expand",
    "Passive Overmatched":   "Attack the Zone",
    "Passive Walker":        "Attack the Zone",
}

def get_pitching_approach(arch):
    if not arch or arch == "—":
        return "—"
    return PITCHING_APPROACH.get(arch.rstrip("*"), "—")

# ---------------------------------------------------------------------------
# 8. Scouting notes — full (3 sentences) and short (1-2 sentences)
# ---------------------------------------------------------------------------
def generate_notes(b):
    pa = b["pa"]
    if pa < 3: return f"Small sample — {pa} PA. Monitor as season progresses."
    bip=b["bip"]; gb_pct=b["gb_pct"]; fb_pct=b["fb_pct"]
    c_pct=b["c_pct"]; k_sw=b["k_sw"]; bb=b["bb"]; hbp=b["hbp"]
    sm_pct=b["sm_pct"]; fpt=b.get("fpt_pct"); zones=b["zones_sorted"]
    parts = []
    tend = []
    if bip > 0 and gb_pct is not None:
        if gb_pct >= 0.60:   tend.append("heavy ground ball hitter")
        elif gb_pct >= 0.45: tend.append("ground ball-oriented")
        elif fb_pct is not None and fb_pct >= 0.55: tend.append("fly ball/line drive hitter")
    if c_pct is not None:
        if c_pct >= 0.80:   tend.append("strong contact rate")
        elif c_pct <= 0.50: tend.append("swing-and-miss concern")
    if sm_pct is not None and sm_pct >= 0.35: tend.append(f"elevated whiff rate ({fmt_pct(sm_pct)} SM%)")
    if fpt is not None and fpt >= 0.65: tend.append("patient at the plate")
    if fpt is not None and fpt < 0.30:  tend.append("aggressive first-pitch hacker")
    if bb + hbp >= 3: tend.append("draws walks")
    if not tend: tend.append("balanced profile")
    parts.append(f"{b['display']} shows a {', '.join(tend)}.")
    stats = []
    if gb_pct is not None and bip > 0: stats.append(f"{fmt_pct(gb_pct)} GB%")
    if c_pct is not None: stats.append(f"{fmt_pct(c_pct)} contact rate")
    if sm_pct is not None: stats.append(f"{fmt_pct(sm_pct)} SM%")
    if fpt is not None: stats.append(f"{fmt_pct(fpt)} FPT%")
    if zones and bip > 0:
        z,cnt = zones[0]; pct = int(round(cnt/bip*100))
        stats.append(f"{pct}% of BIP to {z}")
    if stats: parts.append(f"Key numbers: {'; '.join(stats)}.")
    plan = []
    if bip > 0 and zones:
        tz = zones[0][0]
        if tz in ("LF","3B"):   plan.append("pull hitter — shift infield left, defend line")
        elif tz in ("RF","1B"): plan.append("oppo tendency — shade defense away")
        else:                   plan.append("up-the-middle — play honest defense")
    if gb_pct is not None and bip > 0 and gb_pct >= 0.55: plan.append("corners in for GB")
    if sm_pct is not None and sm_pct >= 0.35: plan.append("attack early with hard stuff / spin")
    if c_pct is not None and c_pct <= 0.50 and k_sw >= 2: plan.append("challenge early in count")
    if fpt is not None and fpt >= 0.65: plan.append("attack first pitch aggressively")
    if fpt is not None and fpt < 0.30: plan.append("make him chase out of zone")
    if not plan: plan.append("monitor spray chart as sample grows")
    parts.append(f"Plan: {'; '.join(plan)}.")
    return " ".join(parts)

def generate_notes_short(b, all_batters=None):
    """Compact 1-2 sentence note for the single-page summary view."""
    pa = b["pa"]
    if pa < 3: return f"Small sample ({pa} PA) — monitor."
    archetype = get_archetype(b, all_batters) or "—"
    zones = b["zones_sorted"]; bip = b["bip"]
    stats = []
    if zones and bip > 0:
        z,cnt = zones[0]; pct = int(round(cnt/bip*100))
        stats.append(f"{pct}% to {z}")
    if b["gb_pct"] is not None and bip > 0: stats.append(f"{fmt_pct(b['gb_pct'])} GB%")
    if b["sm_pct"] is not None:             stats.append(f"{fmt_pct(b['sm_pct'])} SM%")
    if b.get("fpt_pct") is not None:        stats.append(f"{fmt_pct(b['fpt_pct'])} FPT%")
    line1 = f"{archetype} — {'; '.join(stats[:3])}."
    plan = []
    if zones and bip > 0:
        tz = zones[0][0]
        if tz in ("LF","3B"):   plan.append("shift left")
        elif tz in ("RF","1B"): plan.append("shade away")
        else:                   plan.append("play honest")
    if b["sm_pct"] is not None and b["sm_pct"] >= 0.35: plan.append("attack early/hard")
    if b.get("fpt_pct") is not None and b["fpt_pct"] >= 0.65: plan.append("be aggressive first pitch")
    if b.get("fpt_pct") is not None and b["fpt_pct"] < 0.30:  plan.append("pitch out of zone")
    line2 = f"Plan: {'; '.join(plan[:2])}." if plan else ""
    return f"{line1} {line2}".strip()

# ---------------------------------------------------------------------------
# 8. -Reviewed.txt marking
# ---------------------------------------------------------------------------
def mark_reviewed(filepath):
    if filepath.endswith('-Reviewed.txt'):
        return filepath
    new_path = filepath[:-4] + '-Reviewed.txt'
    os.rename(filepath, new_path)
    return new_path

# ---------------------------------------------------------------------------
# 9. PDF — drawing helpers
# ---------------------------------------------------------------------------
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Table, TableStyle

PAGE_W, PAGE_H = letter
MARGIN = 0.45 * inch

C_NAVY  = colors.HexColor("#1a2b4a")
C_AMBER = colors.HexColor("#f5a623")
C_BLUE  = colors.HexColor("#4a90d9")
C_GREEN = colors.HexColor("#27ae60")
C_GRAY  = colors.HexColor("#95a5a6")
C_LGRAY = colors.HexColor("#ecf0f1")
C_WHITE = colors.white
C_RED   = colors.HexColor("#e74c3c")
C_LTBLUE = colors.HexColor("#7fa8cc")

def draw_header(c, title, subtitle):
    c.setFillColor(C_NAVY)
    c.rect(0, PAGE_H-48, PAGE_W, 48, fill=1, stroke=0)
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(PAGE_W/2, PAGE_H-26, title)
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(PAGE_W/2, PAGE_H-42, subtitle)

def draw_diamond(c, cx, cy, size=16):
    s = size
    pts = [(cx,cy+s),(cx+s,cy),(cx,cy-s),(cx-s,cy)]
    c.setFillColor(colors.HexColor("#e8f4f8")); c.setStrokeColor(C_NAVY); c.setLineWidth(0.8)
    p = c.beginPath(); p.moveTo(*pts[0])
    for pt in pts[1:]: p.lineTo(*pt)
    p.close(); c.drawPath(p, fill=1, stroke=1)
    c.setStrokeColor(C_NAVY); c.setLineWidth(0.4)
    for i in range(4): c.line(pts[i][0],pts[i][1],pts[(i+1)%4][0],pts[(i+1)%4][1])
    c.setFillColor(C_WHITE)
    for pt in pts: c.circle(pt[0],pt[1],2,fill=1,stroke=0)
    c.setFillColor(C_AMBER); c.circle(cx,cy+s*0.3,1.8,fill=1,stroke=0)
    return {
        "LF": (cx-s*1.55, cy+s*0.85), "CF": (cx, cy+s*1.55), "RF": (cx+s*1.55, cy+s*0.85),
        "3B": (cx-s*1.55, cy),         "2B": (cx+s*0.05, cy+s*0.42), "1B": (cx+s*1.55, cy),
        "P":  (cx, cy+s*0.3),          "HP": (cx, cy-s*1.3),
    }

def draw_dots(c, zone_pos, zone_detail):
    """Draw BIP dots: amber=GB, blue=FB+LD. No gray — unclassified inferred by zone at parse time."""
    for zone,(x,y) in zone_pos.items():
        detail = zone_detail.get(zone, {"gb":0,"fb_ld":0,"other":0})
        gb    = detail.get("gb", 0)
        fb_ld = detail.get("fb_ld", 0)
        # "other" suppressed — should be near-zero after zone inference
        dot_list = ([C_AMBER]*gb) + ([C_BLUE]*fb_ld)
        n = len(dot_list)
        if n == 0: continue
        for k, col in enumerate(dot_list):
            c.setFillColor(col)
            c.circle(x + k*7 - (n-1)*3.5, y, 3, fill=1, stroke=0)

# ── Heat-map spray chart (new design) ─────────────────────────────────────────
_HEAT_GREENS = ["#1b5e20", "#2e7d32", "#43a047", "#81c784", "#c8e6c9"]
_OF_ZONES    = ("RF", "CF", "LF")
_IF_ZONES    = ("1B", "2B", "SS", "3B")
_ALL_ZONES   = list(_OF_ZONES) + list(_IF_ZONES) + ["P"]

_ZONE_ANG = {
    "RF": (math.radians(45),    math.radians(75)),
    "CF": (math.radians(75),    math.radians(105)),
    "LF": (math.radians(105),   math.radians(135)),
    "1B": (math.radians(45),    math.radians(67.5)),
    "2B": (math.radians(67.5),  math.radians(90)),
    "SS": (math.radians(90),    math.radians(112.5)),
    "3B": (math.radians(112.5), math.radians(135)),
}

def _arc_pts(cx, cy, r, a1, a2, steps=22):
    return [(cx + r * math.cos(a1 + (a2-a1)*i/steps),
             cy + r * math.sin(a1 + (a2-a1)*i/steps))
            for i in range(steps+1)]

def _filled_sector(c, cx, cy, a1, a2, r_in, r_out, fill, lw=0.6, steps=20):
    outer = _arc_pts(cx, cy, r_out, a1, a2, steps)
    inner = _arc_pts(cx, cy, r_in,  a1, a2, steps)
    pts   = outer + list(reversed(inner))
    c.setFillColor(fill); c.setStrokeColor(colors.white); c.setLineWidth(lw)
    p = c.beginPath(); p.moveTo(*pts[0])
    for pt in pts[1:]: p.lineTo(*pt)
    p.close(); c.drawPath(p, fill=1, stroke=1)

def draw_field_spray_chart(c, cx, cy, zone_counts, zone_detail, hb=18):
    """
    Heat-map spray chart.
    cx, cy  : home-plate position (bottom-centre of the field shape)
    zone_counts : {zone: int} — all 8 zones must be present
    zone_detail : {zone: {gb: int, fb_ld: int}}
    hb      : scale factor (half-base distance in pts); derived dynamically from card size
    """
    import random as _rnd
    _rng = _rnd.Random(42)

    r_if  = hb * 1.82    # infield / outfield boundary
    r_of  = hb * 3.10    # outfield wall
    r_wt  = hb * 3.35    # warning-track outer edge
    r_mnd = hb * 0.30    # pitcher's mound radius
    pm_y  = cy + hb * 0.62   # mound centre

    total = max(sum(zone_counts.values()), 1)
    rank  = {z: i for i, (z, _) in enumerate(
                 sorted(zone_counts.items(), key=lambda x: -x[1]))}

    def _zfill(z):
        return colors.HexColor(_HEAT_GREENS[min(rank[z], 4)])
    def _ztxt(z):
        return C_WHITE if rank[z] <= 2 else C_NAVY

    # ── Warning track ──
    wt_pts = _arc_pts(cx, cy, r_wt, math.radians(45), math.radians(135), 60)
    c.setFillColor(colors.HexColor("#c8a870"))
    c.setStrokeColor(colors.HexColor("#7a5c1a")); c.setLineWidth(1.0)
    p = c.beginPath(); p.moveTo(cx, cy)
    for pt in wt_pts: p.lineTo(*pt)
    p.close(); c.drawPath(p, fill=1, stroke=1)

    # ── Outfield sectors ──
    for zone in _OF_ZONES:
        a1, a2 = _ZONE_ANG[zone]
        _filled_sector(c, cx, cy, a1, a2, r_if, r_of, _zfill(zone))

    # ── Infield sectors ──
    for zone in _IF_ZONES:
        a1, a2 = _ZONE_ANG[zone]
        _filled_sector(c, cx, cy, a1, a2, r_mnd*1.35, r_if, _zfill(zone), lw=0.5)

    # ── Pitcher's mound ──
    c.setFillColor(_zfill("P")); c.setStrokeColor(colors.white); c.setLineWidth(0.5)
    c.circle(cx, pm_y, r_mnd, fill=1, stroke=1)

    # ── Foul lines only — no diamond baselines, no bases ──
    c.setStrokeColor(colors.white); c.setLineWidth(1.3)
    for deg in (45, 135):
        a = math.radians(deg)
        c.line(cx, cy, cx + r_wt*math.cos(a), cy + r_wt*math.sin(a))

    # ── Percentage labels only — no zone-name abbreviations ──
    fp = 6.5   # percentage font size
    def _lbl_pos(zone):
        if zone == "P": return cx, pm_y
        a1, a2 = _ZONE_ANG[zone]
        amid = (a1+a2) / 2
        r = ((r_if+r_of)*0.5 if zone in _OF_ZONES
             else (r_mnd*1.35+r_if)*0.70)
        return cx + r*math.cos(amid), cy + r*math.sin(amid)

    for zone in _ALL_ZONES:
        lx, ly = _lbl_pos(zone)
        n   = zone_counts.get(zone, 0)
        pct = round(n / total * 100)
        c.setFillColor(_ztxt(zone))
        c.setFont("Helvetica-Bold", fp)
        c.drawCentredString(lx, ly - 2.5, f"{pct}%")

    # ── BIP dots ──
    dot_r = 1.5   # fixed 1.5pt radius per user preference

    def _rand_in_sector(a1, a2, ri, ro):
        a = _rng.uniform(a1+0.05, a2-0.05)
        r = _rng.uniform(ri*1.12, ro*0.90)
        return cx + r*math.cos(a), cy + r*math.sin(a)

    for zone in _ALL_ZONES:
        det  = zone_detail.get(zone, {})
        for col, cnt in ((C_AMBER, det.get("gb",0)), (C_BLUE, det.get("fb_ld",0))):
            for _ in range(cnt):
                if zone == "P":
                    a  = _rng.uniform(0, 2*math.pi)
                    r  = _rng.uniform(0, r_mnd*0.82)
                    px, py = cx + r*math.cos(a), pm_y + r*math.sin(a)
                elif zone in _OF_ZONES:
                    a1, a2 = _ZONE_ANG[zone]
                    px, py = _rand_in_sector(a1, a2, r_if, r_of)
                else:
                    a1, a2 = _ZONE_ANG[zone]
                    # Push infield dots into outer 45% of the infield arc so they
                    # don't visually overlap the pitcher's mound circle.
                    # r_mnd*1.5 = hb*0.45 was too low — mound extends to hb*0.92.
                    # r_if*0.58 = hb*1.06 clears the mound in all infield sectors.
                    px, py = _rand_in_sector(a1, a2, r_if*0.58, r_if)
                c.setFillColor(col); c.setStrokeColor(colors.white); c.setLineWidth(0.4)
                c.circle(px, py, dot_r, fill=1, stroke=1)

def draw_stat_box(c, x, y, w, h, lbl, val, val_color=None):
    c.setFillColor(C_LGRAY); c.roundRect(x, y, w, h, 2, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7); c.setFillColor(colors.black)
    c.drawCentredString(x+w/2, y+h-8, lbl)
    c.setFont("Helvetica-Bold", 7); c.setFillColor(val_color or colors.black)
    c.drawCentredString(x+w/2, y+2, val)

def draw_bar(c, x, y, w, h, pct, col, lbl, fill_text_white=False):
    """
    Horizontal fill bar with dynamic text coloring.
    fill_text_white: True for dark fills (blue) — use white when text sits on fill,
                     black when text sits on the unfilled gray portion.
                     False for light fills (amber) — always use black text.
    """
    c.setFillColor(C_LGRAY); c.roundRect(x, y, w, h, 2, fill=1, stroke=0)
    fw = w * (pct or 0)
    if fw > 0: c.setFillColor(col); c.roundRect(x, y, fw, h, 2, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 6)
    # Left label: sits at x+2; on fill if any fill exists (fw > 4)
    lbl_on_fill = fw > 4
    c.setFillColor(C_WHITE if (lbl_on_fill and fill_text_white) else colors.black)
    c.drawString(x+2, y+2, lbl)
    # Right percentage: sits at x+w-2; on fill only if bar is nearly full
    pct_on_fill = fw >= w - 22
    c.setFillColor(C_WHITE if (pct_on_fill and fill_text_white) else colors.black)
    c.drawRightString(x+w-2, y+2, fmt_pct(pct))

def draw_card(c, b, x, y, cw, ch, all_batters=None):
    c.setFillColor(C_WHITE); c.setStrokeColor(C_NAVY); c.setLineWidth(0.5)
    c.roundRect(x, y, cw, ch, 4, fill=1, stroke=1)
    pad = 5; iw = cw - 2*pad; ix = x + pad

    # ── Header: 3 rows so name and archetype never compete for horizontal space ──
    #   Row 1: Name (left)  |  "PA / AB" label (right)
    #   Row 2: Archetype    centered full-width (bold white)
    #   Row 3: Approach     centered (amber italic)  |  values (right white)
    header_h = 38
    c.setFillColor(C_NAVY)
    c.roundRect(x, y+ch-header_h, cw, header_h, 4, fill=1, stroke=0)

    arch     = get_archetype(b, all_batters) or "—"
    approach = get_pitching_approach(arch)

    row1_y = y + ch - 10   # name + "PA / AB" label
    row2_y = y + ch - 22   # archetype
    row3_y = y + ch - 34   # approach + PA/AB values

    # Row 1 — Name (left, 9pt bold white) + #jersey (amber) | "PA / AB" label (right, white)
    # Split display string at "#" so jersey renders in amber: "Tyler A. #1"
    raw_display = b["display"]
    if "#" in raw_display:
        nm_part, jersey_part = raw_display.rsplit("#", 1)
        nm_part    = nm_part.strip()
        jersey_str = "#" + jersey_part.strip()
    else:
        nm_part    = raw_display
        jersey_str = ""
    if len(nm_part) > 14: nm_part = nm_part[:13] + "…"
    c.setFillColor(C_WHITE); c.setFont("Helvetica-Bold", 9)
    c.drawString(x+pad, row1_y, nm_part)
    if jersey_str:
        nm_w = c.stringWidth(nm_part, "Helvetica-Bold", 9)
        c.setFillColor(C_AMBER)
        c.drawString(x+pad + nm_w + 2, row1_y, jersey_str)
    c.setFillColor(C_WHITE); c.setFont("Helvetica", 6.5)
    c.drawRightString(x+cw-pad, row1_y, "PA / AB")

    # Row 2 — Archetype centered, 9pt bold white
    c.setFont("Helvetica-Bold", 9); c.setFillColor(C_WHITE)
    c.drawCentredString(x+cw/2, row2_y, arch)

    # Row 3 — Approach centered amber italic 9pt (matches archetype) | PA/AB values right white
    c.setFont("Helvetica-Oblique", 9); c.setFillColor(C_AMBER)
    c.drawCentredString(x+cw/2, row3_y, f"({approach})")
    c.setFont("Helvetica-Bold", 6.5); c.setFillColor(C_WHITE)
    c.drawRightString(x+cw-pad, row3_y, f"{b['pa']} / {b['ab']}")

    cy = y + ch - header_h - 2

    # ── 4 Stat boxes: AVG OBP SLG C% — slightly compact to offset taller header ──
    bh = 20; bw = (iw - 6) / 4
    for si, (lbl, val) in enumerate([
        ("AVG", fmt_avg(b["avg"])), ("OBP", fmt_avg(b["obp"])),
        ("SLG", fmt_avg(b["slg"])), ("C%",  fmt_pct(b["c_pct"]))
    ]):
        draw_stat_box(c, ix+si*(bw+2), cy-bh, bw, bh, lbl, val)
    cy -= bh + 8   # extra gap so field clears stat boxes

    # ── Spray chart (heat-map) ──
    # bars + footer below this point need ~37 pts
    _static_below = 9 + 2 + 9 + 3 + 10 + 4
    _available    = int(cy - (y + _static_below))
    # hb: width-limited (full field diameter = 2 * hb * 3.35 must fit in iw)
    _hb_w = iw / 6.70
    # hb: height-limited
    _hb_h = max(0, _available - 10) / 3.38
    hb = min(_hb_w, _hb_h)
    # chart_h: sized to contain the field exactly, capped by available space
    chart_h = max(60, min(int(hb * 3.38) + 16, _available))
    # Build zone_counts dict ensuring all 8 zones present
    _zc = {z: 0 for z in _ALL_ZONES}
    for z, cnt in b["zones_sorted"]:
        if z in _zc: _zc[z] = cnt
    home_y = (cy - chart_h) + hb * 0.48   # home plate sits near chart-area bottom
    draw_field_spray_chart(c, x + cw/2, home_y, _zc, b["zone_detail"], hb=hb)
    cy -= chart_h + 2

    # ── GB% bar (amber, dark label) ──
    bh2 = 9
    draw_bar(c, ix, cy-bh2, iw, bh2, b["gb_pct"],  C_AMBER, "GB%",    fill_text_white=False)
    cy -= bh2 + 2

    # ── FB+LD% bar (blue) — white text on fill, black text on gray ──
    draw_bar(c, ix, cy-bh2, iw, bh2, b["fb_pct"],  C_BLUE,  "FB+LD%", fill_text_white=True)
    cy -= bh2 + 3

    # ── Footer: SM% | CStr% | FPT% — bold 7pt ──
    sm_color = (C_RED   if (b["sm_pct"] or 0) >= 0.35 else
                C_GREEN if (b["sm_pct"] is not None and b["sm_pct"] <= 0.20) else C_NAVY)
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(sm_color)
    c.drawString(ix, cy-10, f"SM%: {fmt_pct(b['sm_pct'])}")
    c.setFillColor(C_NAVY)
    c.drawCentredString(x+cw/2, cy-10, f"CStr%: {fmt_pct(b['cstr_pct'])}")
    c.drawRightString(ix+iw, cy-10, f"FPT%: {fmt_pct(b.get('fpt_pct'))}")

# ---------------------------------------------------------------------------
# 10. PDF generation
# ---------------------------------------------------------------------------
def generate_pdf(team_key, label, batters, n_games, skipped, out_path, league_batters=None, division_label="Majors"):
    c = rl_canvas.Canvas(out_path, pagesize=letter)
    skip_note = f"  |  Skipped: {', '.join(skipped)}" if skipped else ""
    sub = f"{n_games} games  |  Generated {TODAY}{skip_note}"
    active = [b for b in batters if b["pa"] > 0]
    # Use league-wide batters for percentile thresholds if available; else fall back to team roster
    arch_ctx = [b for b in (league_batters or []) if b["pa"] >= 5] or active

    # ── Player Card Pages — 2-col, max 3 rows per page ───────────────────────
    # Cap at 3 rows regardless of roster size so card/spray-chart height stays
    # consistent.  Rosters > 6 players spill onto additional card pages.
    header_text = f"{label}  —  {division_label} Hitter Scouting Report"
    ncols      = 2
    col_gap    = 10
    card_w     = (PAGE_W - 2*MARGIN - (ncols-1)*col_gap) / ncols
    top_y      = PAGE_H - 56
    avail_h    = top_y - MARGIN
    row_gap    = 6
    MAX_ROWS   = 3                          # never squeeze more than 3 rows onto one page
    per_page   = ncols * MAX_ROWS           # 6 cards per page

    # Fixed card height based on MAX_ROWS so every report looks identical
    card_h = (avail_h - (MAX_ROWS - 1) * row_gap) / MAX_ROWS
    card_h = max(140, min(320, card_h))

    card_pages = [active[i:i+per_page] for i in range(0, max(1, len(active)), per_page)]

    for page_num, page_batters in enumerate(card_pages):
        if page_num > 0:
            c.showPage()
        draw_header(c, header_text, sub)

        for idx, b in enumerate(page_batters):
            col = idx % ncols
            row = idx // ncols
            cx2 = MARGIN + col * (card_w + col_gap)
            cy2 = top_y - (row + 1) * (card_h + row_gap) + row_gap
            draw_card(c, b, cx2, cy2, card_w, card_h, all_batters=arch_ctx)

    # ── PAGE 3: Summary Table + Compact Notes ────────────────────────────────
    c.showPage()
    draw_header(c, f"{label}  —  Summary & Scouting Notes",
                f"{division_label}  |  Spring 2026  |  {n_games} games")

    # Table
    hdr = ["Hitter","AVG","OBP","SLG","C%",
           "#1 Zone","#2 Zone","#3 Zone","#4 Zone",
           "GB%","FB+%","SM%","CStr%","FPT%"]
    data = [hdr]
    for b in active:
        zs = b["zones_sorted"]; bip = b["bip"]
        zcells = []
        for i in range(4):
            if i < len(zs):
                z,cnt = zs[i]; p = int(round(cnt/bip*100)) if bip>0 else 0
                zcells.append(f"{z} {p}%")
            else: zcells.append("—")
        data.append([
            b["display"],
            fmt_avg(b["avg"]),fmt_avg(b["obp"]),fmt_avg(b["slg"]),fmt_pct(b["c_pct"]),
        ] + zcells + [
            fmt_pct(b["gb_pct"]),fmt_pct(b["fb_pct"]),
            fmt_pct(b["sm_pct"]),fmt_pct(b["cstr_pct"]),fmt_pct(b.get("fpt_pct")),
        ])

    col_ws = [1.00*inch,
              0.38*inch,0.38*inch,0.38*inch,0.38*inch,
              0.56*inch,0.56*inch,0.56*inch,0.56*inch,
              0.36*inch,0.36*inch,0.36*inch,0.38*inch,0.36*inch]
    tbl = Table(data, colWidths=col_ws)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),C_NAVY),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,0),6.5),
        ("FONTNAME",(0,1),(-1,-1),"Helvetica"),("FONTSIZE",(0,1),(-1,-1),6.5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE,C_LGRAY]),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),("ALIGN",(0,0),(0,-1),"LEFT"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("GRID",(0,0),(-1,-1),0.3,C_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("LEFTPADDING",(0,0),(-1,-1),2),("RIGHTPADDING",(0,0),(-1,-1),2),
    ]))
    t_top = PAGE_H - 58
    tw, th = tbl.wrapOn(c, PAGE_W - 2*MARGIN, PAGE_H)
    tbl.drawOn(c, MARGIN, t_top - th)

    # Scouting Notes — compact 1-2 line format
    ny = t_top - th - 12
    c.setFont("Helvetica-Bold", 11); c.setFillColor(C_NAVY)
    c.drawString(MARGIN, ny, "Key Scouting Notes")
    c.setLineWidth(1); c.setStrokeColor(C_NAVY)
    c.line(MARGIN, ny-2, MARGIN+145, ny-2)
    ny -= 14

    for b in active:
        if ny < MARGIN + 10:
            c.showPage(); ny = PAGE_H - MARGIN - 20
        c.setFont("Helvetica-Bold", 8); c.setFillColor(C_BLUE)
        c.drawString(MARGIN, ny, b["display"]); ny -= 10
        note = generate_notes_short(b, all_batters=arch_ctx)
        c.setFont("Helvetica", 7.5); c.setFillColor(C_NAVY)
        # Wrap note at 108 chars, max 2 lines
        words = note.split(); line = ""; lines_written = 0
        for w in words:
            test = line + (" " if line else "") + w
            if len(test) <= 108:
                line = test
            else:
                if lines_written < 2:
                    c.drawString(MARGIN+8, ny, line); ny -= 9; lines_written += 1
                line = w
        if line and lines_written < 2:
            c.drawString(MARGIN+8, ny, line); ny -= 9
        ny -= 4
    c.save()
    logger.info(f"  → {out_path}")

# ---------------------------------------------------------------------------
# 11. Teams list + league pre-scan
# ---------------------------------------------------------------------------
TEAMS = [
    ("Guardians",    "Esau"),
    ("Royals",       "Hall"),
    ("Diamondbacks", "Vandiford"),
    ("Marlins",      "McLendon"),
    ("Dodgers",      "Pearson"),
    ("As",           "Blanco"),
    ("Braves",       "Rue"),
    ("Twins",        "Ewart"),
    ("Padres",       "Schick"),
    ("Cubs",         "Holtzer"),
    ("Rays",         "Madero"),
]

def get_wild_opponents(wild_base):
    """Discover opponent team folders under Wild/. Skip Sample_Opponent."""
    teams = []
    if not os.path.isdir(wild_base):
        return teams
    for name in sorted(os.listdir(wild_base)):
        if name.startswith(".") or name == "Sample_Opponent":
            continue
        team_dir = os.path.join(wild_base, name)
        games_dir = os.path.join(team_dir, "Games")
        if os.path.isdir(team_dir) and os.path.isdir(games_dir):
            teams.append(name)
    return teams

def load_wild_roster(team_dir):
    """Load optional roster.txt: lines of 'INITIALS, Display Name'. # = comment."""
    roster = {}
    roster_path = os.path.join(team_dir, "roster.txt")
    if not os.path.exists(roster_path):
        return roster
    with open(roster_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",", 1)
            if len(parts) == 2:
                roster[parts[0].strip()] = parts[1].strip()
    return roster

def build_league_context(game_files, rosters, config, all_collision_maps=None):
    """
    Pre-scan ALL teams' scorebooks to build a league-wide batter list.
    Used to compute league-relative percentile thresholds for archetype Result labels.
    Silent — no output printed.

    all_collision_maps: optional {team_key: {2-char-init: [dis1, dis2]}} from
        load_box_rosters() — passed through to parse_game_for_team() so duplicate-
        initials splitting applies during the league pre-scan as well.
    """
    league_batters = []
    csv_overrides = config.get("csv_overrides", {})
    scorebooks_dir = config.get("scorebooks")
    teams = config.get("teams", [])
    coll_maps = all_collision_maps or {}

    for team_name, coach_last in teams:
        team_key = f"{team_name}-{coach_last}"
        csv_team = csv_overrides.get(team_name, team_name)
        roster   = rosters.get(f"{csv_team}-{coach_last}", {})
        cmap     = coll_maps.get(team_key, {})
        all_pas  = []
        for fname in game_files:
            if team_key not in fname: continue
            fpath = os.path.join(scorebooks_dir, fname)
            try:
                all_pas.extend(parse_game_for_team(fpath, team_key, collision_map=cmap))
            except Exception:
                pass
        league_batters.extend(compute_stats(all_pas, roster))
    return league_batters


def run_league(division, teams_filter=None):
    """Run report generation for a league division (Majors or Minors)."""
    config = DIVISIONS[division]
    scorebooks_dir = config["scorebooks"]
    output_dir     = config["output"]
    roster_json    = config.get("roster_json")
    verify_json    = config.get("verify_json")
    csv_path       = config["csv"]
    csv_overrides  = config["csv_overrides"]
    roster_additions = config["roster_additions"]
    league_scan    = config["league_scan"]
    label_suffix   = config["label_suffix"]
    teams          = config["teams"]

    os.makedirs(output_dir, exist_ok=True)

    # Load rosters: prefer box-score JSON (has first names + jersey numbers);
    # fall back to CSV if JSON hasn't been built yet.
    all_collision_maps = {}
    if roster_json and os.path.exists(roster_json):
        logger.info(f"[{division}] Loading box-score rosters from {roster_json}")
        rosters, all_collision_maps = load_box_rosters(roster_json, roster_additions)
        if all_collision_maps:
            logger.info(f"[{division}] Collision map loaded for: "
                        f"{sorted(all_collision_maps.keys())}")
    else:
        logger.warning(f"[{division}] rosters.json not found — falling back to CSV. "
                       f"Run scrape_box_scores.py to build it.")
        rosters = build_rosters(csv_path, roster_additions)

    # Load box score verification data (may be empty if not yet scraped)
    box_verify = load_box_verify(verify_json) if verify_json else {}

    game_files = sorted(f for f in os.listdir(scorebooks_dir) if f.endswith(".txt"))

    # Build league-wide context if enabled
    league_batters = None
    if league_scan:
        logger.info("Scanning league for archetype percentiles…")
        league_batters = build_league_context(
            game_files, rosters, config, all_collision_maps=all_collision_maps
        )
        eligible = [b for b in league_batters if b["pa"] >= 5]
        logger.info(f"{len(eligible)} qualifying players across {len(teams)} teams.")

    run_start = time.time()
    timings = []
    targets = [(tn, cl) for tn, cl in teams if (teams_filter is None or tn in teams_filter)]

    for team_name, coach_last in targets:
        t_start = time.time()
        team_key = f"{team_name}-{coach_last}"
        csv_team = csv_overrides.get(team_name, team_name)
        roster = rosters.get(f"{csv_team}-{coach_last}", {})
        logger.info(f"\n=== {team_key} ===")
        if not roster:
            logger.warning(f"no roster found for '{csv_team}-{coach_last}'")

        all_game_pas = []
        skipped = []
        parsed_paths = []
        total_warnings = 0
        cmap = all_collision_maps.get(team_key, {})
        for fname in game_files:
            if team_key not in fname:
                continue
            fpath = os.path.join(scorebooks_dir, fname)
            try:
                pas = parse_game_for_team(fpath, team_key, collision_map=cmap)
                # Annotate PAs with game_id and game_seq for batting order tracking
                for i, pa in enumerate(pas, 1):
                    pa["game_id"] = fname
                    pa["game_seq"] = i
                all_game_pas.append((fname, pas))
                parsed_paths.append(fpath)
                nw = verify_game(fpath, team_key, pas, fname)
                total_warnings += nw
                status = "✓" if nw == 0 else f"⚠ {nw} warning(s)"
                logger.info(f"  {fname}: {len(pas)} PAs  [{status}]")
            except Exception as e:
                logger.error(f"SKIP {fname}: {e}")
                skipped.append(fname)

        all_pas = [pa for _, pas in all_game_pas for pa in pas]
        n_games = len(all_game_pas)
        batters = compute_stats(all_pas, roster)

        # Layer 4 — box score cross-check
        verify_box_score(team_key, batters, box_verify)

        total_pa = sum(b["pa"] for b in batters)
        verify_tag = "✓ all checks passed" if total_warnings == 0 else f"⚠ {total_warnings} total warning(s)"
        logger.info(f"  Total PA: {total_pa}  |  {n_games} games  |  {verify_tag}")
        for b in batters:
            logger.info(f"    {b['display']:22s}  PA={b['pa']}  "
                        f"AVG={fmt_avg(b['avg'])}  OBP={fmt_avg(b['obp'])}  "
                        f"SLG={fmt_avg(b['slg'])}  C%={fmt_pct(b['c_pct'])}  "
                        f"SM%={fmt_pct(b['sm_pct'])}  CStr%={fmt_pct(b['cstr_pct'])}  "
                        f"FPT%={fmt_pct(b.get('fpt_pct'))}")

        display_team = "A's" if team_name == "As" else team_name
        label = f"{display_team} ({coach_last})"
        safe = team_name.replace(" ", "_")
        pdf_path = os.path.join(output_dir, f"{safe}_{coach_last}-Scout_2026.pdf")
        generate_pdf(team_key, label, batters, n_games, skipped, pdf_path,
                     league_batters=league_batters, division_label=label_suffix)

        for fpath in parsed_paths:
            new_path = mark_reviewed(fpath)
            if new_path != fpath:
                logger.info(f"  → Marked reviewed: {os.path.basename(new_path)}")

        elapsed = time.time() - t_start
        timings.append((team_key, n_games, total_pa, elapsed))
        logger.info(f"  ⏱  {elapsed:.2f}s")

    total_elapsed = time.time() - run_start
    logger.info("\n" + "="*60)
    logger.info("TIMING SUMMARY")
    logger.info(f"{'Team':<28} {'Games':>5} {'PA':>5} {'Time':>8}")
    logger.info("-"*60)
    for tk, ng, tpa, te in timings:
        logger.info(f"  {tk:<26} {ng:>5} {tpa:>5} {te:>7.2f}s")
    logger.info("-"*60)
    logger.info(f"  {'TOTAL':<26} {sum(t[1] for t in timings):>5} "
                f"{sum(t[2] for t in timings):>5} {total_elapsed:>7.2f}s")
    logger.info("="*60)

def run_wild(teams_filter=None, division="Wild"):
    """Run report generation for Wild or Storm opponent teams."""
    config = DIVISIONS[division]
    wild_base = config["wild_base"]
    label_suffix = config["label_suffix"]
    fixed_thresholds = config["fixed_thresholds"]

    run_start = time.time()
    timings = []
    all_opponents = get_wild_opponents(wild_base)

    if not all_opponents:
        logger.warning(f"No opponent teams found in {wild_base}")
        return

    targets = [t for t in all_opponents if (teams_filter is None or t in teams_filter)]

    for opponent_name in targets:
        try:
            t_start = time.time()
            team_dir = os.path.join(wild_base, opponent_name)
            games_dir = os.path.join(team_dir, "Games")
            output_dir = team_dir  # PDFs go in opponent folder

            logger.info(f"\n=== {opponent_name} ===")

            # Load optional roster
            roster = load_wild_roster(team_dir)

            # Collect game files
            game_files = sorted(f for f in os.listdir(games_dir) if f.endswith(".txt"))
            logger.info(f"  Found {len(game_files)} game files")

            all_game_pas = []
            skipped = []
            parsed_paths = []
            total_warnings = 0
            for fname in game_files:
                fpath = os.path.join(games_dir, fname)
                try:
                    pas = parse_game_for_team(fpath, opponent_name)
                    # Annotate PAs with game_id and game_seq for batting order tracking
                    for i, pa in enumerate(pas, 1):
                        pa["game_id"] = fname
                        pa["game_seq"] = i
                    all_game_pas.append((fname, pas))
                    parsed_paths.append(fpath)
                    nw = verify_game(fpath, opponent_name, pas, fname)
                    total_warnings += nw
                    status = "✓" if nw == 0 else f"⚠ {nw} warning(s)"
                    logger.info(f"  {fname}: {len(pas)} PAs  [{status}]")
                except Exception as e:
                    logger.error(f"SKIP {fname}: {e}")
                    skipped.append(fname)

            all_pas = [pa for _, pas in all_game_pas for pa in pas]
            n_games = len(all_game_pas)

            if not all_pas:
                logger.warning(f"No PAs found for {opponent_name}")
                continue

            # For Wild, use initials directly as display (fallback when roster lookup fails)
            roster_wild = {init: init for init in set(pa["initials"] for pa in all_pas)}
            roster_wild.update(roster)

            batters = compute_stats(all_pas, roster_wild)
            total_pa = sum(b["pa"] for b in batters)
            verify_tag = "✓ all checks passed" if total_warnings == 0 else f"⚠ {total_warnings} total warning(s)"
            logger.info(f"  Total PA: {total_pa}  |  {n_games} games  |  {verify_tag}")
            for b in batters:
                logger.info(f"    {b['display']:22s}  PA={b['pa']}  "
                            f"AVG={fmt_avg(b['avg'])}  OBP={fmt_avg(b['obp'])}  "
                            f"SLG={fmt_avg(b['slg'])}  C%={fmt_pct(b['c_pct'])}  "
                            f"SM%={fmt_pct(b['sm_pct'])}  CStr%={fmt_pct(b['cstr_pct'])}")

            # PDF output
            label = opponent_name
            safe = opponent_name.replace(" ", "_")
            pdf_path = os.path.join(output_dir, f"{safe}_Scout_2026.pdf")

            # Pass None for league_batters to use fixed thresholds
            generate_pdf(opponent_name, label, batters, n_games, skipped, pdf_path,
                         league_batters=None, division_label=label_suffix)

            # Mark files as reviewed
            for fpath in parsed_paths:
                new_path = mark_reviewed(fpath)
                if new_path != fpath:
                    logger.info(f"  → Marked reviewed: {os.path.basename(new_path)}")

            elapsed = time.time() - t_start
            timings.append((opponent_name, n_games, total_pa, elapsed))
            logger.info(f"  ⏱  {elapsed:.2f}s")

        except Exception as exc:
            logger.error(f"  ⚠ {opponent_name} failed: {exc}")

    total_elapsed = time.time() - run_start
    logger.info("\n" + "="*60)
    logger.info("TIMING SUMMARY")
    logger.info(f"{'Opponent':<28} {'Games':>5} {'PA':>5} {'Time':>8}")
    logger.info("-"*60)
    for name, ng, tpa, te in timings:
        logger.info(f"  {name:<26} {ng:>5} {tpa:>5} {te:>7.2f}s")
    logger.info("-"*60)
    logger.info(f"  {'TOTAL':<26} {sum(t[1] for t in timings):>5} "
                f"{sum(t[2] for t in timings):>5} {total_elapsed:>7.2f}s")
    logger.info("="*60)

def main():
    parser = argparse.ArgumentParser(description="WCWAA Scouting Report Generator")
    parser.add_argument("--division", default="Majors",
                        choices=["Majors", "Minors", "Wild", "Storm"],
                        help="Division to generate reports for (default: Majors)")
    parser.add_argument("--team", nargs="*",
                        help="One or more team names to run (omit for all teams in division)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show DEBUG-level messages on screen (normally only in log file)")
    # Legacy positional args: python3 gen_reports.py Guardians (old Majors usage)
    parser.add_argument("legacy_teams", nargs="*", help=argparse.SUPPRESS)
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    teams_filter = args.team or args.legacy_teams or None
    division = args.division

    if division in ("Wild", "Storm"):
        run_wild(teams_filter, division=division)
    else:
        run_league(division, teams_filter)

if __name__ == "__main__":
    main()
