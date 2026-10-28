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


if __name__ == "__main__":
    unittest.main()
