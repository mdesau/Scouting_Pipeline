#!/usr/bin/env python3
"""
stat_analysis.py — Statistical Distribution Analysis for Hitting Stats
======================================================================
Generates a styled HTML report showing the statistical distribution of 8 key
batting stats across all 4 divisions. Designed as a reference tool for
recalibrating the archetype system using relative (percentile-based) thresholds
instead of static cutoffs.

Workflow:
    1. Imports parsing functions from gen_hitting.py (same parser, no duplication)
    2. For each division (Majors, Minors, Wild, Storm):
       a. Discovers all game files
       b. Parses all PAs for all teams
       c. Computes per-batter stats via compute_stats()
       d. Filters to qualified batters (PA >= MIN_PA)
    3. For each of the 8 stats, computes 13 statistical measures
    4. Outputs a single styled HTML file with 4 division sections

Stats Analyzed:
    AVG, OBP, SLG, C%, Swing%, SM%, CStr%, FPT%

Statistical Measures (13):
    N, Mean, Median, Std Dev, Min, Max,
    P10, P20, P33, P67, P80, P90, IQR (P75 - P25)

Usage:
    cd Dev/Hitting_Scout/Scripts
    python3 stat_analysis.py [--min-pa 10] [--output path/to/output.html]

Output:
    HTML file at Dev/Hitting_Scout/Scripts/stat_analysis_report.html (default)

Dependencies:
    - gen_hitting.py (same directory — imported directly)
    - numpy (for percentile/std dev calculations)
    - Game files on disk (no scraping, uses existing data)

Version: Part of Scout Pipeline v2.8.0+
"""

import os
import sys
import argparse
import numpy as np
from collections import defaultdict
from datetime import datetime

# ---------------------------------------------------------------------------
# Import parsing infrastructure from gen_hitting.py
# ---------------------------------------------------------------------------
# WHY IMPORT vs DUPLICATE:
#   gen_hitting.py already has battle-tested parsing logic. Duplicating would
#   create a maintenance burden (any parser fix would need to be applied twice).
#   Importing keeps stat_analysis.py as a pure *consumer* of the parsed data.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_hitting import (
    DIVISIONS, BASE,
    parse_game_for_team, compute_stats, compute_team_totals,
    get_wild_opponents, load_wild_roster,
    load_box_rosters, build_rosters,
    fmt_avg, fmt_pct,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_MIN_PA = 15       # Minimum PAs to qualify — filters noise from pinch-hitters
DEFAULT_OUTPUT = os.path.join(BASE, "Dev", "Hitting_Scout", "Scripts", "stat_analysis_report.html")

# The 8 stats we're analyzing, in display order
STATS = [
    ("avg",      "AVG",   "ratio"),   # format type: ratio (.325), pct (42%), or raw (1.200)
    ("obp",      "OBP",   "ratio"),
    ("slg",      "SLG",   "ratio"),
    ("c_pct",    "C%",    "pct"),
    ("swing_pct","Swing%","pct"),
    ("sm_pct",   "SM%",   "pct"),
    ("cstr_pct", "CStr%", "pct"),
    ("fpt_pct",  "FPT%",  "pct"),
]

# ---------------------------------------------------------------------------
# Data Collection — gathers all qualified batters per division
# ---------------------------------------------------------------------------
def collect_division_batters(division_name, min_pa):
    """
    Parse all game files for a division and return a list of batter stat dicts.

    For Majors/Minors: reads from the centralized Scorebooks folder.
    For Wild/Storm: reads from per-team Games/ folders.

    Args:
        division_name: One of 'Majors', 'Minors', 'Wild', 'Storm'
        min_pa: Minimum plate appearances to qualify

    Returns:
        List of batter dicts (same shape as compute_stats() output),
        filtered to PA >= min_pa. Each dict is augmented with 'team_key'.
    """
    config = DIVISIONS[division_name]
    all_batters = []

    if config.get("league_scan"):
        # --- Majors / Minors: centralized scorebooks ---
        scorebooks_dir = config["scorebooks"]
        roster_json = config.get("roster_json")
        roster_additions = config.get("roster_additions", {})
        csv_path = config["csv"]
        csv_overrides = config.get("csv_overrides", {})
        teams = config["teams"]

        # Load rosters (prefer box-score JSON for accuracy)
        all_collision_maps = {}
        if roster_json and os.path.exists(roster_json):
            rosters, all_collision_maps = load_box_rosters(roster_json, roster_additions)
        else:
            rosters = build_rosters(csv_path, roster_additions)

        # Get all game files
        if not os.path.isdir(scorebooks_dir):
            return []
        game_files = sorted(
            f for f in os.listdir(scorebooks_dir)
            if f.endswith(".txt") or f.endswith("-Reviewed.txt")
        )

        for team_name, coach_last in teams:
            team_key = f"{team_name}-{coach_last}"
            file_team_key = team_key.replace("'", "")
            csv_team = csv_overrides.get(team_name, team_name)
            roster = rosters.get(f"{csv_team}-{coach_last}", {})
            cmap = all_collision_maps.get(team_key, {})
            all_pas = []

            for fname in game_files:
                if team_key not in fname and file_team_key not in fname:
                    continue
                fpath = os.path.join(scorebooks_dir, fname)
                if not os.path.exists(fpath):
                    continue
                try:
                    pas = parse_game_for_team(fpath, team_key, collision_map=cmap)
                    for i, pa in enumerate(pas, 1):
                        pa["game_id"] = fname
                        pa["game_seq"] = i
                    all_pas.extend(pas)
                except Exception:
                    pass

            batters = compute_stats(all_pas, roster)
            for b in batters:
                b["team_key"] = team_key
            all_batters.extend(batters)

    else:
        # --- Wild / Storm: per-team Games/ folders ---
        wild_base = config["wild_base"]
        opponents = get_wild_opponents(wild_base)

        for opponent_name in opponents:
            team_dir = os.path.join(wild_base, opponent_name)
            games_dir = os.path.join(team_dir, "Games")
            if not os.path.isdir(games_dir):
                continue

            roster = load_wild_roster(team_dir)
            game_files = sorted(
                f for f in os.listdir(games_dir)
                if f.endswith(".txt") or f.endswith("-Reviewed.txt")
            )

            all_pas = []
            for fname in game_files:
                fpath = os.path.join(games_dir, fname)
                try:
                    pas = parse_game_for_team(fpath, opponent_name)
                    for i, pa in enumerate(pas, 1):
                        pa["game_id"] = fname
                        pa["game_seq"] = i
                    all_pas.extend(pas)
                except Exception:
                    pass

            # Build a working roster that includes all initials seen in game data
            roster_wild = {init: init for init in set(pa["initials"] for pa in all_pas)}
            roster_wild.update(roster)
            batters = compute_stats(all_pas, roster_wild)
            for b in batters:
                b["team_key"] = opponent_name
            all_batters.extend(batters)

    # Filter to qualified batters
    qualified = [b for b in all_batters if b["pa"] >= min_pa]
    return qualified


# ---------------------------------------------------------------------------
# Statistical Computation
# ---------------------------------------------------------------------------
def compute_distribution(values):
    """
    Compute 13 statistical measures for a list of numeric values.

    Args:
        values: list of float/int (None values pre-filtered out by caller)

    Returns:
        dict with keys: n, mean, median, std, min, max,
                        p10, p20, p25, p33, p67, p75, p80, p90, iqr
    """
    arr = np.array(values, dtype=float)
    n = len(arr)

    if n == 0:
        return {k: None for k in [
            "n", "mean", "median", "std", "min", "max",
            "p10", "p20", "p25", "p33", "p67", "p75", "p80", "p90", "iqr"
        ]}

    p25 = float(np.percentile(arr, 25))
    p75 = float(np.percentile(arr, 75))

    return {
        "n":      n,
        "mean":   float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std":    float(np.std(arr, ddof=1)) if n > 1 else 0.0,
        "min":    float(np.min(arr)),
        "max":    float(np.max(arr)),
        "p10":    float(np.percentile(arr, 10)),
        "p20":    float(np.percentile(arr, 20)),
        "p25":    p25,
        "p33":    float(np.percentile(arr, 33)),
        "p67":    float(np.percentile(arr, 67)),
        "p75":    p75,
        "p80":    float(np.percentile(arr, 80)),
        "p90":    float(np.percentile(arr, 90)),
        "iqr":    p75 - p25,
    }


def analyze_division(batters):
    """
    Run the 13-measure analysis on all 8 stats for a list of qualified batters.

    Args:
        batters: list of batter dicts (from collect_division_batters)

    Returns:
        dict keyed by stat_key -> distribution dict (from compute_distribution)
    """
    results = {}
    for stat_key, _, _ in STATS:
        # Extract non-None values for this stat
        values = [b[stat_key] for b in batters if b.get(stat_key) is not None]
        results[stat_key] = compute_distribution(values)
    return results


# ---------------------------------------------------------------------------
# HTML Report Generation
# ---------------------------------------------------------------------------
def format_value(val, fmt_type):
    """Format a stat value for display in the HTML table."""
    if val is None:
        return "—"
    if fmt_type == "ratio":
        # Batting average style: .325, 1.200
        if val >= 1.0:
            return f"{val:.3f}"
        return f".{int(round(val * 1000)):03d}"
    elif fmt_type == "pct":
        # Percentage style: 42%
        return f"{val * 100:.1f}%"
    else:
        return f"{val:.3f}"


def pct_to_bg_color(value, stat_min, stat_max):
    """
    Map a value's position within [min, max] to a background color for heat mapping.
    Returns an rgba CSS string.

    Color scale: blue (low) → white (middle) → red (high)
    This is direction-agnostic — the analyst interprets whether high is good or bad.
    """
    if stat_max == stat_min:
        return "rgba(255, 255, 255, 0.0)"
    # Normalize to 0–1
    t = (value - stat_min) / (stat_max - stat_min)
    # Blue (0) → White (0.5) → Red (1.0)
    if t <= 0.5:
        # Blue to white
        ratio = t / 0.5
        r = int(100 + 155 * ratio)
        g = int(130 + 125 * ratio)
        b = 255
    else:
        # White to red
        ratio = (t - 0.5) / 0.5
        r = 255
        g = int(255 - 125 * ratio)
        b = int(255 - 155 * ratio)
    return f"rgba({r}, {g}, {b}, 0.35)"


def generate_html(all_results, min_pa, output_path):
    """
    Generate the full HTML report from computed analysis results.

    Args:
        all_results: dict keyed by division_name -> {stat_key -> distribution_dict}
        min_pa: the PA minimum used (displayed in header for context)
        output_path: where to write the HTML file
    """
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Measure labels displayed in the table (column headers)
    measures = [
        ("n",      "N"),
        ("mean",   "Mean"),
        ("median", "Median"),
        ("std",    "Std Dev"),
        ("min",    "Min"),
        ("p10",    "P10"),
        ("p20",    "P20"),
        ("p33",    "P33"),
        ("p67",    "P67"),
        ("p80",    "P80"),
        ("p90",    "P90"),
        ("max",    "Max"),
        ("iqr",    "IQR"),
    ]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WCWAA Hitting Stat Analysis — Spring 2026</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: #f8f9fa;
        color: #1a2b4a;
        padding: 24px;
        line-height: 1.5;
    }}
    .header {{
        text-align: center;
        margin-bottom: 32px;
        padding-bottom: 16px;
        border-bottom: 3px solid #1a2b4a;
    }}
    .header h1 {{
        font-size: 1.8rem;
        color: #1a2b4a;
        margin-bottom: 4px;
    }}
    .header .subtitle {{
        font-size: 0.9rem;
        color: #666;
    }}
    .legend {{
        background: #fff;
        border: 1px solid #ddd;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 24px;
        font-size: 0.8rem;
        color: #555;
    }}
    .legend strong {{ color: #1a2b4a; }}
    .division {{
        margin-bottom: 40px;
    }}
    .division h2 {{
        font-size: 1.3rem;
        color: #fff;
        background: #1a2b4a;
        padding: 8px 16px;
        border-radius: 6px 6px 0 0;
        margin-bottom: 0;
    }}
    .division h2 .count {{
        font-size: 0.8rem;
        font-weight: normal;
        opacity: 0.8;
        margin-left: 12px;
    }}
    .stat-section {{
        margin-bottom: 2px;
    }}
    .stat-section h3 {{
        font-size: 0.9rem;
        background: #f5a623;
        color: #1a2b4a;
        padding: 4px 16px;
        font-weight: 700;
        border-left: 4px solid #1a2b4a;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.78rem;
        background: #fff;
    }}
    th {{
        background: #e9ecef;
        color: #1a2b4a;
        padding: 6px 8px;
        text-align: center;
        font-weight: 700;
        border-bottom: 2px solid #1a2b4a;
        white-space: nowrap;
    }}
    td {{
        padding: 5px 8px;
        text-align: center;
        border-bottom: 1px solid #eee;
        font-variant-numeric: tabular-nums;
    }}
    td.stat-name {{
        text-align: left;
        font-weight: 700;
        background: #f8f9fa;
        width: 70px;
    }}
    tr:hover td {{
        background-color: rgba(245, 166, 35, 0.12) !important;
    }}
    .quintile-guide {{
        display: flex;
        gap: 16px;
        margin: 8px 16px 12px;
        font-size: 0.75rem;
    }}
    .quintile-guide span {{
        padding: 2px 8px;
        border-radius: 3px;
    }}
    .q-low {{ background: rgba(100, 130, 255, 0.35); }}
    .q-mid {{ background: rgba(255, 255, 255, 0.35); border: 1px solid #ddd; }}
    .q-high {{ background: rgba(255, 130, 100, 0.35); }}
    .footer {{
        text-align: center;
        margin-top: 32px;
        padding-top: 16px;
        border-top: 1px solid #ddd;
        font-size: 0.75rem;
        color: #999;
    }}
    @media print {{
        body {{ padding: 12px; }}
        .division {{ page-break-inside: avoid; }}
    }}
</style>
</head>
<body>
<div class="header">
    <h1>WCWAA Hitting Stat Distribution Analysis</h1>
    <div class="subtitle">Spring 2026 &nbsp;|&nbsp; Min PA: {min_pa} &nbsp;|&nbsp; Generated: {timestamp}</div>
</div>

<div class="legend">
    <strong>How to read this table:</strong>
    Each row is one of 8 batting stats. Columns show the statistical distribution of that stat
    across all qualified batters in the division. Cell colors show relative position within the
    stat's range (blue = low end, white = middle, red = high end). Direction is intentionally
    neutral — interpret based on the stat (e.g., high SM% is bad; high AVG is good).
    <div class="quintile-guide">
        <span class="q-low">Low end (P10–P20)</span>
        <span class="q-mid">Middle range</span>
        <span class="q-high">High end (P80–P90)</span>
    </div>
</div>
"""

    for div_name in ["Majors", "Minors", "Wild", "Storm"]:
        div_data = all_results.get(div_name)
        if not div_data:
            continue

        # Get N from the first stat (all should have same N)
        first_stat = list(div_data.values())[0]
        n_players = first_stat.get("n", 0) if first_stat else 0

        html += f"""
<div class="division">
    <h2>{div_name}<span class="count">{n_players} qualified batters (≥{min_pa} PA)</span></h2>
    <table>
        <thead>
            <tr>
                <th>Stat</th>
"""
        for _, label in measures:
            html += f"                <th>{label}</th>\n"
        html += "            </tr>\n        </thead>\n        <tbody>\n"

        for stat_key, stat_label, fmt_type in STATS:
            dist = div_data.get(stat_key, {})
            if not dist or dist.get("n") is None:
                html += f"            <tr><td class='stat-name'>{stat_label}</td>"
                html += "<td colspan='13'>— no data —</td></tr>\n"
                continue

            # Get min/max for color scaling
            stat_min = dist["min"]
            stat_max = dist["max"]

            html += f"            <tr>\n                <td class='stat-name'>{stat_label}</td>\n"

            for measure_key, _ in measures:
                val = dist.get(measure_key)
                if val is None:
                    html += "                <td>—</td>\n"
                    continue

                # Format the display value
                if measure_key == "n":
                    display = str(int(val))
                    bg = ""
                elif measure_key == "std" or measure_key == "iqr":
                    # Std dev and IQR: show in same format as the stat but no color
                    display = format_value(val, fmt_type)
                    bg = ""
                else:
                    display = format_value(val, fmt_type)
                    # Apply heat-map coloring for percentile/min/max/mean/median cells
                    bg_color = pct_to_bg_color(val, stat_min, stat_max)
                    bg = f" style='background: {bg_color};'"

                html += f"                <td{bg}>{display}</td>\n"

            html += "            </tr>\n"

        html += "        </tbody>\n    </table>\n</div>\n"

    html += f"""
<div class="footer">
    WCWAA Scout Pipeline v2.8.0 &nbsp;|&nbsp; stat_analysis.py &nbsp;|&nbsp; {timestamp}
</div>
</body>
</html>
"""

    # Write to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate statistical distribution analysis of hitting stats across all divisions."
    )
    parser.add_argument("--min-pa", type=int, default=DEFAULT_MIN_PA,
                        help=f"Minimum PA to qualify (default: {DEFAULT_MIN_PA})")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT,
                        help=f"Output HTML path (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"  WCWAA Hitting Stat Distribution Analysis")
    print(f"  Min PA: {args.min_pa}  |  Output: {os.path.basename(args.output)}")
    print(f"{'='*60}\n")

    all_results = {}

    for div_name in ["Majors", "Minors", "Wild", "Storm"]:
        print(f"  [{div_name}] Collecting batters...", end=" ", flush=True)
        batters = collect_division_batters(div_name, args.min_pa)
        print(f"{len(batters)} qualified (≥{args.min_pa} PA)")

        if batters:
            all_results[div_name] = analyze_division(batters)
        else:
            print(f"    ⚠ No qualified batters found for {div_name}")

    print(f"\n  Generating HTML report...")
    output_path = generate_html(all_results, args.min_pa, args.output)
    print(f"  ✓ Written to: {output_path}")
    print(f"\n{'='*60}")
    print(f"  Done. Open the HTML file in a browser to review.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
