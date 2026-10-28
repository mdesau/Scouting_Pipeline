"""Build all three analysis reports for a league division with one command.

Downloads new games + rosters once, parses every game once, then writes:
  1. Pitching usage & team comparison workbook (with draft tabs when a draft sheet is configured)
  2. Tournament futures PDF (when a `postseason:` bracket is configured)
  3. Draft report card PDF + XLSX (when a draft `csv:` is configured)

Run from the repo root with the venv active:
    python -m scout.analysis_tools.run_all --division Minors
    python -m scout.analysis_tools.run_all --division Minors --no-scrape   # reuse games already saved
"""

import argparse
import subprocess
import sys
import time

from scout.analysis_tools import draft_roi, tourney_odds
from scout.analysis_tools import games as td
from scout.analysis_tools import pitching_usage as mur
from scout.season_config import SEASON_DIR, SEASON_ID, load_season_yaml

SCRAPERS = ("scout.scraping.scrape_gc_playbyplay", "scout.scraping.scrape_gc_boxscores")


def scrape(division):
    """Run Steps 1–2 for the division. Returns False if GameChanger couldn't be reached."""
    for mod in SCRAPERS:
        print(f"\n── {mod.rsplit('.', 1)[1]} --division {division}", flush=True)
        rc = subprocess.run([sys.executable, "-m", mod, "--division", division]).returncode
        if rc:
            print(f"⚠️  {mod} exited {rc} — building reports from games already saved.")
            return False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--division", default="Minors")
    ap.add_argument("--no-scrape", action="store_true", help="skip downloading; use games already saved")
    args = ap.parse_args()
    division = args.division

    _sid, cfg = load_season_yaml()
    dcfg = cfg["divisions"].get(division)
    if not dcfg or "scorebooks" not in dcfg:
        raise SystemExit(f"{division} is not a league division in config/{SEASON_ID}.yaml")

    t0 = time.time()
    if not args.no_scrape:
        scrape(division)

    print(f"\n── Parsing {division} games", flush=True)
    _sb, _post, games, _ = td.division_data(division)
    print(f"   {len(games)} games")

    outputs, skipped = [], []
    has_draft = bool(dcfg.get("csv")) and (SEASON_DIR / dcfg["csv"]).exists()
    if has_draft:
        print("\n── Draft report card", flush=True)
        res = draft_roi.analyze(division)
        outputs += [draft_roi.build_pdf(res, division), draft_roi.build_xlsx(res, division)]
    else:
        skipped.append("Draft report card (no draft `csv:` for this division)")

    print("\n── Pitching usage & team comparison workbook", flush=True)
    outputs.append(mur.build_workbook(division)[0])

    if td.postseason(division).get("bracket"):
        print("\n── Tournament futures", flush=True)
        outputs.append(tourney_odds.run(division))
    else:
        skipped.append("Tournament futures (no `postseason:` bracket for this division)")

    print(f"\n✅ Done in {time.time() - t0:.0f}s — {len(outputs)} files:")
    for o in outputs:
        print(f"   {o}")
    for s in skipped:
        print(f"   (skipped) {s}")


if __name__ == "__main__":
    main()
