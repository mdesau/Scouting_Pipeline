"""Unit tests for gen_hitting game-file matching and lineup-slot ordering."""

import unittest

from scout.hitting import gen_hitting as gh


class FileKeyTests(unittest.TestCase):
    def test_spaces_and_apostrophes_match_scraper_filenames(self):
        self.assertEqual(gh.file_key("Blue Jays-Patel"), "Blue_Jays-Patel")
        self.assertEqual(gh.file_key("A's-Blanco"), "As-Blanco")


class LineupSlotTests(unittest.TestCase):
    @staticmethod
    def _pa(ini, inning):
        return {"initials": ini, "inning": inning}

    def test_newest_first_file_gives_true_lineup_slots(self):
        # File order is newest-first: inning 2 (C, A) then inning 1 (B, A reversed within the inning).
        pas = [self._pa("C", 2), self._pa("A", 2), self._pa("B", 1), self._pa("A", 1)]
        gh._assign_lineup_slots(pas, "g1")
        self.assertEqual({p["initials"]: p["game_seq"] for p in pas}, {"A": 1, "B": 2, "C": 3})

    def test_oldest_first_file_unchanged(self):
        pas = [self._pa("A", 1), self._pa("B", 1), self._pa("C", 2)]
        gh._assign_lineup_slots(pas, "g1")
        self.assertEqual([p["game_seq"] for p in pas], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
