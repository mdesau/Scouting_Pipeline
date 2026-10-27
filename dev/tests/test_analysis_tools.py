"""Unit tests for scout.analysis_tools (draft order, name matching, rest rules, odds, rollbacks)."""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from scout.analysis_tools import draft_roi, tourney_odds
from scout.analysis_tools import games as gm


class DraftOrderTests(unittest.TestCase):
    def test_snake_order_and_overall_pick_numbers(self):
        csv_text = (",CoachA,CoachB,CoachC\n"
                    "1,A1,B1,C1\n"
                    "2,A2,B2,C2\n"
                    "3,A3,,\n"
                    ",Ants,Bees,Cats\n")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "draft.csv"
            p.write_text(csv_text, encoding="utf-8")
            picks = {x["name"]: x for x in draft_roi.load_draft(p)}
        self.assertEqual([picks[n]["pick"] for n in ("A1", "B1", "C1", "C2", "B2", "A2", "A3")],
                         [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(picks["C2"]["team"], "Cats-CoachC")

    def test_nickname_and_last_initial_matching(self):
        idx = {"Yankees-X": {"J S": {"first": "Jake", "last_init": "S", "display": "Jake S. #10"}}}
        team, keys = draft_roi.match_pick({"name": "Jacob Suarez", "team": "Yankees-X"}, idx)
        self.assertEqual((team, keys), ("Yankees-X", ["J S"]))

    def test_match_falls_back_to_team_actually_played_for(self):
        idx = {"Orioles-X": {}, "Royals-Y": {"S C": {"first": "Sterling", "last_init": "C", "display": "Sterling C."}}}
        team, keys = draft_roi.match_pick({"name": "Sterling Congelliere", "team": "Orioles-X"}, idx)
        self.assertEqual(team, "Royals-Y")


class TourneyRuleTests(unittest.TestCase):
    def test_rest_days_rule(self):
        self.assertEqual([tourney_odds.rest_days(p) for p in (20, 21, 35, 36, 50)], [0, 1, 1, 2, 2])

    def test_american_odds(self):
        self.assertEqual(tourney_odds.american(0.5), "-100")
        self.assertEqual(tourney_odds.american(0.25), "+300")
        self.assertEqual(tourney_odds.american(0.0), "OFF")


class RollbackTests(unittest.TestCase):
    def test_rollback_drops_innings_after_official_inning(self):
        game = ("GAME: Oct05 | https://web.gc.com/x/schedule/11111111-2222-3333-4444-555555555555/plays\n\n"
                "===Bottom 2nd - Home===\n"
                "Single | AWY 1 - HOM 3 | In play.\nH B singles to left fielder, H A scores.\n"
                "===Top 2nd - Away===\n"
                "Single | AWY 1 - HOM 2 | In play.\nA B singles to left fielder, A A scores.\n"
                "===Bottom 1st - Home===\n"
                "Home Run | AWY 0 - HOM 2 | In play.\nH C homers on a fly ball to left field.\n"
                "===Top 1st - Away===\n"
                "Strikeout | 1 Out | Strike 1 looking, Strike 2 looking, Strike 3 looking.\n"
                "A C strikes out looking, H P pitching.\n")
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "Oct05-Away_vs_Home.txt").write_text(game, encoding="utf-8")
            full = gm.load_games(Path(d), {"start": date(2026, 10, 22)})[0]
            rolled = gm.load_games(Path(d), {"start": date(2026, 10, 22),
                                             "rollbacks": {"11111111-2222-3333-4444-555555555555": 1}})[0]
        self.assertEqual(full["runs"], {"Away": 1, "Home": 3})
        self.assertEqual(rolled["runs"], {"Away": 0, "Home": 2})
        self.assertFalse(rolled["playoff"])


if __name__ == "__main__":
    unittest.main()
