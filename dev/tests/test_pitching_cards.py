"""Pitching card header: GP / GS / IP (BUG-048)."""

import json
import tempfile
import unittest
from pathlib import Path

from scout.pitching import gen_pitching as gp


def pa(game, inning):
    return {"game": game, "inning": inning}


class AppearancesTests(unittest.TestCase):
    def test_relief_games_are_not_starts(self):
        pas = [pa("g1", 3), pa("g1", 4), pa("g2", 2), pa("g3", 1), pa("g3", 2)]
        self.assertEqual(gp.appearances(pas), (3, 1))


class OfficialInningsTests(unittest.TestCase):
    def test_box_outs_drive_ip_and_rates(self):
        stats = {"strikeouts": 3, "walks": 2, "ip_exact": 0.0, "ip_display": "0.0", "total_outs": 0,
                 "k_per_9": None, "bb_per_9": None}
        gp.apply_official_innings(stats, 4)
        self.assertEqual(stats["ip_display"], "1.1")
        self.assertAlmostEqual(stats["k_per_9"], 3 * 9 / (4 / 3))
        self.assertAlmostEqual(stats["bb_per_9"], 2 * 9 / (4 / 3))

    def test_zero_outs(self):
        stats = {"strikeouts": 1, "walks": 3}
        gp.apply_official_innings(stats, 0)
        self.assertEqual(stats["ip_display"], "0.0")
        self.assertIsNone(stats["k_per_9"])


class BoxUsageTests(unittest.TestCase):
    def test_starter_is_first_listed(self):
        verify = {
            "g1": {"away_team": "Rays-L", "home_team": "Cubs-M",
                   "away_pitching": [{"name": "Jacob B", "jersey": "4", "outs": 1},
                                     {"name": "Sam C", "jersey": "7", "outs": 8}],
                   "home_pitching": [{"name": "Ann D", "jersey": "1", "outs": 9}]},
            "g2": {"away_team": "Cubs-M", "home_team": "Rays-L",
                   "away_pitching": [{"name": "Ann D", "jersey": "1", "outs": 6}],
                   "home_pitching": [{"name": "Sam C", "jersey": "7", "outs": 9},
                                     {"name": "Jacob B", "jersey": "4", "outs": None}]},
        }
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "box_verify.json"
            path.write_text(json.dumps(verify), encoding="utf-8")
            usage = gp.box_usage(str(path), {})
        self.assertEqual(usage["Rays-L"]["J B"], {"gp": 2, "gs": 1, "outs": 1})
        self.assertEqual(usage["Rays-L"]["S C"], {"gp": 2, "gs": 1, "outs": 17})
        self.assertEqual(usage["Cubs-M"]["A D"], {"gp": 2, "gs": 2, "outs": 15})

    def test_missing_file(self):
        self.assertEqual(gp.box_usage("/nonexistent/box_verify.json", {}), {})


if __name__ == "__main__":
    unittest.main()
