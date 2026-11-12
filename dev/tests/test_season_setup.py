"""New-season setup for the Bonus Features: draft results + season picker (BUG-047 Enh)."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scout import season_config
from scout.analysis_tools import games as gm
from scout.orchestrator.run_menu import _clean_path

DRAFT = "Rd,Smith,Jones\n1,Ann A,Bob B\n2,Cal C,Dee D\nTeam,Cubs,Mets\n"


class DraftResultsTests(unittest.TestCase):
    def _run(self, text, division="Majors", name="draft.csv"):
        cfg = {"divisions": {"Majors": {"type": "league", "csv": "old.csv"}, "Wild": {"type": "travel"}}}
        saved = {}
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / name
            src.write_text(text, encoding="utf-8")
            with patch.object(season_config, "_load_cfg", return_value=(Path("x.yaml"), cfg)), \
                 patch.object(season_config, "_save_cfg", side_effect=lambda p, c: saved.update(c)), \
                 patch.object(season_config, "_SEASONS_DIR", Path(d) / "seasons"):
                dest = season_config.set_draft_results("2027-Spring", division, src)
                copied = dest.read_text(encoding="utf-8")
        return dest, copied, saved

    def test_copies_csv_and_sets_path(self):
        dest, copied, saved = self._run(DRAFT)
        self.assertEqual(dest.parts[-4:], ("2027-Spring", "Majors", "Reports", "draft.csv"))
        self.assertEqual(copied, DRAFT)
        self.assertEqual(saved["divisions"]["Majors"]["csv"], "Majors/Reports/draft.csv")

    def test_rejects_non_draft_csv(self):
        with self.assertRaises(ValueError):
            self._run("name,team\nAnn,Cubs\n")

    def test_rejects_non_csv_and_travel_division(self):
        with self.assertRaises(ValueError):
            self._run(DRAFT, name="draft.xlsx")
        with self.assertRaises(ValueError):
            self._run(DRAFT, division="Wild")


class SeasonPickerTests(unittest.TestCase):
    SEASONS = [{"id": "2026-Fall", "is_active": True}, {"id": "2027-Spring", "is_active": False}]

    def test_loaded_season_runs_in_place(self):
        with patch.object(gm, "list_seasons", return_value=self.SEASONS), \
             patch.object(gm, "SEASON_ID", "2026-Fall"), patch.object(gm.os, "execve") as ex:
            self.assertEqual(gm.choose_season("m", "2026-Fall"), "2026-Fall")
        ex.assert_not_called()

    def test_other_season_reruns_with_env(self):
        with patch.object(gm, "list_seasons", return_value=self.SEASONS), \
             patch.object(gm, "SEASON_ID", "2026-Fall"), patch.object(gm.os, "execve") as ex:
            gm.choose_season("scout.analysis_tools.run_all", "2027-Spring")
        argv, env = ex.call_args[0][1], ex.call_args[0][2]
        self.assertEqual(argv[-2:], ["--season", "2027-Spring"])
        self.assertIn("scout.analysis_tools.run_all", argv)
        self.assertEqual(env["SCOUT_SEASON"], "2027-Spring")

    def test_unknown_season(self):
        with patch.object(gm, "list_seasons", return_value=self.SEASONS):
            with self.assertRaises(SystemExit):
                gm.choose_season("m", "1999-Fall")

    def test_prompt_enter_keeps_loaded_season(self):
        with patch.object(gm, "list_seasons", return_value=self.SEASONS), \
             patch.object(gm, "SEASON_ID", "2026-Fall"), \
             patch.object(gm.sys.stdin, "isatty", return_value=True), \
             patch("builtins.input", return_value=""), patch("builtins.print"):
            self.assertEqual(gm.choose_season("m"), "2026-Fall")


class CleanPathTests(unittest.TestCase):
    def test_dragged_and_quoted_paths(self):
        self.assertEqual(_clean_path("/Users/me/My\\ Draft.csv "), "/Users/me/My Draft.csv")
        self.assertEqual(_clean_path("'/Users/me/My Draft.csv'"), "/Users/me/My Draft.csv")


class SuggestAgesTests(unittest.TestCase):
    PREV = {"divisions": {"Majors": {"type": "league", "age": "11U"},
                          "Wild": {"type": "travel", "age": "12U"},
                          "Mavs": {"type": "travel", "age": "10U", "tournament_team": True}}}

    def _suggest(self, season_id):
        seasons = [{"id": "2026-spring"}, {"id": "2026-Fall"}]
        with patch.object(season_config, "list_seasons", return_value=seasons), \
             patch.object(season_config, "load_season_yaml", return_value=("2026-Fall", self.PREV)):
            return season_config.suggest_ages(season_id)

    def test_season_order(self):
        self.assertLess(season_config._season_order("2026-spring"), season_config._season_order("2026-Fall"))
        self.assertLess(season_config._season_order("2026-Fall"), season_config._season_order("2027-Spring"))
        self.assertIsNone(season_config._season_order("AllStars"))

    def test_spring_keeps_ages_and_carries_tournament(self):
        prev, ages, tournament = self._suggest("2027-Spring")
        self.assertEqual(prev, "2026-Fall")
        self.assertEqual((ages["Wild"], ages["Mavs"], ages["Majors"]), ("12U", "10U", "11U"))
        self.assertEqual(tournament, ["Mavs"])

    def test_fall_bumps_travel_only(self):
        _prev, ages, _t = self._suggest("2027-Fall")
        self.assertEqual((ages["Wild"], ages["Mavs"], ages["Majors"]), ("13U", "11U", "11U"))

    def test_bump_age(self):
        self.assertEqual(season_config.bump_age("9U"), "10U")
        self.assertEqual(season_config.bump_age(None), None)

    def test_list_seasons_skips_non_season_yaml(self):
        ids = [s["id"] for s in season_config.list_seasons()]
        self.assertNotIn("archetype_baselines", ids)
        self.assertNotIn("season_template", ids)


if __name__ == "__main__":
    unittest.main()
