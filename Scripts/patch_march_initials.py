# -*- coding: utf-8 -*-
"""
patch_march_initials.py
-----------------------
One-time fix for Bug 15: Crushers White 10U March game files used 2-char
initials (e.g. "A L") while April+ files use full first name (e.g. "Andrew L").
This caused split player cards in the scouting PDF.

This script patches the 7 affected March game files, replacing 2-char initials
with the full first-name format — but ONLY on lines where Crushers White 10U
is batting (to avoid corrupting opponent player names in the same files).

Safe to re-run: already-patched lines won't match the 2-char patterns.
"""

import re
import os

GAMES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "Storm", "Crushers White 10U", "Games"
)

# 2-char initials → full first name + last initial (must match April file format exactly)
ROSTER_MAP = {
    "A C": "Asher C",
    "A L": "Andrew L",
    "D P": "Devan P",
    "J B": "Jack B",
    "J S": "Jordan S",
    "N L": "Nico L",
    "R B": "Reilly B",
    "R R": "Riley R",
}

MARCH_FILES = [
    "Mar07-Crushers_White_10U_vs_Carolina_Titans_Ambrose_Blue_10U-Reviewed.txt",
    "Mar07-North_State_Bombers_10U_vs_Crushers_White_10U-Reviewed.txt",
    "Mar08-Crushers_White_10U_vs_A2K_2034_10U-Reviewed.txt",
    "Mar08-Crushers_White_10U_vs_SBA_Central_Warriors_10U-Reviewed.txt",
    "Mar08-Crushers_White_10U_vs_SBA_Central_Warriors_9-10U-Reviewed.txt",
    "Mar21-Carolina_Sluggers-Seegars_10U_vs_Crushers_White_10U-Reviewed.txt",
    "Mar21-Crushers_White_10U_vs_A2K_2034_10U-Reviewed.txt",
    "Mar22-GoWags_Centurions_vs_Crushers_White_10U-Reviewed.txt",
]


def patch_file(filepath, dry_run=False):
    with open(filepath, "r") as f:
        lines = f.readlines()

    crushers_batting = False
    new_lines = []
    changes = []

    for i, line in enumerate(lines):
        # Track which team is batting based on inning section headers
        # Format: ===Top/Bottom Nth - Team Name===
        if line.startswith("===") and "Crushers White 10U" in line:
            crushers_batting = True
        elif line.startswith("==="):
            crushers_batting = False

        new_line = line
        if crushers_batting:
            for short, full in ROSTER_MAP.items():
                # Only match initials at the very start of a line (the batter slot)
                pattern = r"^" + re.escape(short) + r" "
                if re.match(pattern, line):
                    new_line = re.sub(pattern, full + " ", line, count=1)
                    if new_line != line:
                        changes.append((i + 1, line.rstrip(), new_line.rstrip()))
                    break

        new_lines.append(new_line)

    return new_lines, changes


def main(dry_run=False):
    games_dir = os.path.abspath(GAMES_DIR)
    total_changes = 0

    for fname in MARCH_FILES:
        fpath = os.path.join(games_dir, fname)
        if not os.path.exists(fpath):
            print(f"  SKIP (not found): {fname}")
            continue

        new_lines, changes = patch_file(fpath, dry_run=dry_run)
        total_changes += len(changes)

        if not changes:
            print(f"  OK (no changes needed): {fname}")
            continue

        print(f"  {'DRY RUN' if dry_run else 'PATCHED'}: {fname} — {len(changes)} line(s)")
        for lineno, before, after in changes:
            print(f"    Line {lineno}:")
            print(f"      BEFORE: {before}")
            print(f"      AFTER:  {after}")

        if not dry_run:
            with open(fpath, "w") as f:
                f.writelines(new_lines)

    print(f"\n{'DRY RUN' if dry_run else 'Done'}: {total_changes} total line(s) {'would be ' if dry_run else ''}changed across {len(MARCH_FILES)} file(s).")


if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("=== DRY RUN — no files will be modified ===\n")
    else:
        print("=== PATCHING game files ===\n")
    main(dry_run=dry_run)
