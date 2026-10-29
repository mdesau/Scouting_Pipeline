"""Unit tests for roster collision handling in scrape_gc_boxscores (kids sharing initials)."""

import unittest

from scout.scraping import scrape_gc_boxscores as bx


def _player(name, initials, jersey):
    return {"name": name, "initials": initials, "jersey": jersey, "ab": 1, "bb": 0, "so": 0}


class CollisionKeyTests(unittest.TestCase):
    def test_shared_three_letter_prefix_gets_longer_key(self):
        self.assertEqual(bx._disambig_key("C B", "Carson", {"Car B"}), "Cars B")

    def test_identical_first_names_use_jersey(self):
        self.assertEqual(bx._disambig_key("J W", "Jax", {"Jax W"}, jersey="5"), "Jax W #5")

    def test_same_jersey_is_same_kid_even_with_different_first_name(self):
        self.assertTrue(bx._same_kid("DJ", "2", "Dheeraj", "2"))
        self.assertFalse(bx._same_kid("Jax", "5", "Jax", "7"))


class AccumulateTests(unittest.TestCase):
    def test_carter_and_carson_stay_separate(self):
        rosters = {}
        bx._accum_player(rosters, "Royals", _player("Carter B", "C B", "2"), "g1", 1)
        bx._accum_player(rosters, "Royals", _player("Carson B", "C B", "1"), "g1", 5)
        bx._accum_player(rosters, "Royals", _player("Carson B", "C B", "1"), "g2", 5)
        team = rosters["Royals"]
        self.assertEqual(team["_collision_map"]["C B"], ["Car B", "Cars B"])
        self.assertEqual(team["Cars B"]["games_seen"], 2)
        self.assertEqual(team["Car B"]["games_seen"], 1)

    def test_nickname_with_same_jersey_merges(self):
        rosters = {}
        bx._accum_player(rosters, "Cubs", _player("DJ B", "D B", "2"), "g1", 3)
        bx._accum_player(rosters, "Cubs", _player("Dheeraj B", "D B", "2"), "g2", 3)
        self.assertNotIn("_collision_map", rosters["Cubs"])
        self.assertEqual(rosters["Cubs"]["D B"]["games_seen"], 2)


class BoxPitchingTests(unittest.TestCase):
    BLOCK = {"pitchers": [{"name": "Grayson L", "jersey": "5", "ip": "1.0"},
                          {"name": "Tristan L", "jersey": "7", "ip": "2.0"},
                          {"name": "TEAM", "jersey": "", "ip": "3.0"}],
             "extra": "WP: Tristan L\nPitches-Strikes: Tristan L 27-13, Grayson L 16-12\n"
                      "Batters Faced: Tristan L 8, Grayson L 7"}

    def test_parse_pitching_order_counts_and_outs(self):
        rows = bx.parse_pitching(self.BLOCK)
        self.assertEqual([r["name"] for r in rows], ["Grayson L", "Tristan L"])
        self.assertEqual((rows[1]["pitches"], rows[1]["strikes"], rows[1]["bf"], rows[1]["outs"]), (27, 13, 8, 6))

    def test_box_fixes_starter_shared_initials_and_pitch_counts(self):
        from collections import defaultdict
        from scout.analysis_tools import pitching_usage as mur
        rosters = {"Rays": {"Tri L": {"display": "Tristan L. #7", "jersey": "7"},
                            "Tro L": {"display": "Troy L. #4", "jersey": "4"},
                            "G L": {"display": "Grayson L. #5", "jersey": "5"},
                            "_collision_map": {"T L": ["Tri L", "Tro L"]}}}
        apps = defaultdict(mur.new_app)
        apps[("Rays", "G L", "g")]["pitches"] = 14
        apps[("Rays", "T L", "g")]["pitches"] = 25
        mur._apply_box(apps, "g", "Rays", bx.parse_pitching(self.BLOCK), rosters)
        self.assertNotIn(("Rays", "T L", "g"), apps)
        self.assertEqual(apps[("Rays", "Tri L", "g")]["pitches"], 27)
        self.assertEqual(apps[("Rays", "G L", "g")]["pitches"], 16)
        self.assertTrue(apps[("Rays", "G L", "g")]["start"])


if __name__ == "__main__":
    unittest.main()
