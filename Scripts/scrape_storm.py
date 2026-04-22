#!/usr/bin/env python3
"""
scrape_storm.py
Processes raw page-text dumps (saved from get_page_text) for ITAA 9U Spartans games
and writes properly formatted .txt scorebooks to the Storm Games folder.

Usage: python3 scrape_storm.py
Raw text files are read from /tmp/storm_raw/ and output goes to Storm/ITAA 9U Spartans/Games/
"""

import os, re
from parse_gc_text import parse_gc_raw

# Resolve paths relative to this script so it works locally from Spring/Scripts/
_HERE     = os.path.dirname(os.path.abspath(__file__))
GAMES_DIR = os.path.join(_HERE, "..", "Storm", "ITAA 9U Spartans", "Games")
RAW_DIR   = "/tmp/storm_raw"

# (raw_filename, output_filename)
GAME_MAP = [
    ("g1.txt", "Mar06-ITAA_Spartans_10U_vs_ITAA_9U_Spartans.txt"),
    ("g2.txt", "Mar08-ITAA_9U_Spartans_vs_Davidson_Force_9U.txt"),
    ("g3.txt", "Mar08b-ITAA_9U_Spartans_vs_SCRA_9U_Cardinals.txt"),
    ("g4.txt", "Mar22-Titans_9U_vs_ITAA_9U_Spartans.txt"),
    ("g5.txt", "Mar22b-Pineville_Blue_Sox_9U_vs_ITAA_9U_Spartans.txt"),
    ("g6.txt", "Mar22c-Pineville_Blue_Sox_9U_vs_ITAA_9U_Spartans.txt"),
    ("g7.txt", "Mar29-ITAA_9U_Spartans_vs_MARA_9U_Stingers.txt"),
    ("g8.txt", "Mar29b-SCRA_9U_Cardinals_vs_ITAA_9U_Spartans.txt"),
]

os.makedirs(GAMES_DIR, exist_ok=True)

processed = 0
for raw_fname, out_fname in GAME_MAP:
    raw_path = os.path.join(RAW_DIR, raw_fname)
    if not os.path.exists(raw_path):
        print(f"  [skip] {raw_fname} not found")
        continue

    with open(raw_path) as f:
        raw = f.read()

    # Extract URL and date from the get_page_text header block
    url_m  = re.search(r'URL:\s*(https?://\S+)', raw)
    date_m = re.search(r'((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+)', raw)

    result = parse_gc_raw(
        raw,
        game_url  = url_m.group(1)  if url_m  else '',
        game_date = date_m.group(1) if date_m else '',
    )

    out_path = os.path.join(GAMES_DIR, out_fname)
    with open(out_path, 'w') as f:
        f.write(result)

    # Count PAs (lines starting with a capital letter initial pattern)
    pa_count = len([l for l in result.splitlines() if re.match(r'^[A-Z] [A-Z] ', l)])
    print(f"  ✓ {out_fname}  ({pa_count} PAs)")
    processed += 1

print(f"\nDone — {processed}/{len(GAME_MAP)} files written to {GAMES_DIR}")
