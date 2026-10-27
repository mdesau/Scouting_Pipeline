"""Focused checks for safe play-by-play extraction and league team discovery."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scout import season_config
from scout.season_config import _discover_league_teams
from scout.scraping.gc_browser import (
    SESSION_BLOCKED,
    SESSION_OK,
    SESSION_SIGNED_OUT,
    classify_session,
)
from scout.scraping.scrape_gc_playbyplay import _has_valid_plays_content


class PlaysContentValidationTests(unittest.TestCase):
    def test_accepts_body_with_inning_header(self):
        body = "Plays All Plays\nTop 1st - Cubs-Holtzer\nSingle"
        self.assertTrue(_has_valid_plays_content(body))

    def test_rejects_logged_out_body(self):
        body = "Sign in to GameChanger\nTop 1st - Cubs-Holtzer\nSingle"
        self.assertFalse(_has_valid_plays_content(body))

    def test_rejects_body_without_inning_header(self):
        self.assertFalse(_has_valid_plays_content("Sign in or view schedule"))
        self.assertFalse(_has_valid_plays_content(""))
        self.assertFalse(_has_valid_plays_content(None))


class SessionClassificationTests(unittest.TestCase):
    URL = "https://web.gc.com/teams"

    def test_ok_when_account_api_succeeds(self):
        self.assertEqual(
            classify_session("My teams", self.URL, {"/me/user": 200, "/me/teams": 200}),
            SESSION_OK,
        )

    def test_signed_out_on_login_redirect_or_sign_in_text(self):
        self.assertEqual(
            classify_session("", "https://web.gc.com/login", {}), SESSION_SIGNED_OUT
        )
        self.assertEqual(
            classify_session("Sign in to GameChanger", self.URL, {}), SESSION_SIGNED_OUT
        )

    def test_signed_out_on_401(self):
        self.assertEqual(
            classify_session("", self.URL, {"/me/user": 401}), SESSION_SIGNED_OUT
        )

    def test_blocked_on_403_from_firewall(self):
        self.assertEqual(
            classify_session("", self.URL, {"/me/user": 403, "/me/teams": 403}),
            SESSION_BLOCKED,
        )

    def test_blocked_on_account_load_error(self):
        body = "Oops! We couldn't load your account. Reload to try again."
        self.assertEqual(
            classify_session(body, self.URL, {"/me/user": 200}), SESSION_BLOCKED
        )

    def test_blocked_when_account_api_never_answered(self):
        self.assertEqual(classify_session("My teams", self.URL, {}), SESSION_BLOCKED)


class LeagueTeamDiscoveryTests(unittest.TestCase):
    def _build_divisions(self, season_dir, configured_teams):
        season_config_data = {
            "divisions": {
                "Majors": {
                    "type": "league",
                    "scorebooks": "Majors/Reports/Scorebooks",
                    "output": "Majors/Reports/Scouting_Reports",
                    "csv": "draft.csv",
                    "roster_json": "Majors/Reports/rosters.json",
                    "verify_json": "Majors/Reports/box_verify.json",
                    "teams": configured_teams,
                }
            }
        }
        with patch.object(season_config, "SEASON_ID", "test-season"):
            with patch.object(season_config, "_SEASON_CFG", season_config_data):
                with patch.object(
                    season_config, "get_season_dir", return_value=season_dir
                ):
                    return season_config.build_hitting_divisions()

    def test_derives_team_and_coach_from_roster_keys(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            roster_path = Path(temp_dir) / "rosters.json"
            roster_path.write_text(
                json.dumps({"Cubs-Holtzer": {}, "A's-Blanco": {}, "Invalid": {}}),
                encoding="utf-8",
            )

            self.assertEqual(
                _discover_league_teams(roster_path),
                [("A's", "Blanco"), ("Cubs", "Holtzer")],
            )

    def test_builder_discovers_teams_when_yaml_list_is_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            season_dir = Path(temp_dir)
            roster_path = season_dir / "Majors/Reports/rosters.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(
                json.dumps({"Cubs-Holtzer": {}}), encoding="utf-8"
            )

            divisions = self._build_divisions(season_dir, [])

            self.assertEqual(divisions["Majors"]["teams"], [("Cubs", "Holtzer")])

    def test_builder_preserves_configured_team_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            season_dir = Path(temp_dir)
            roster_path = season_dir / "Majors/Reports/rosters.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(
                json.dumps({"Cubs-Holtzer": {}}), encoding="utf-8"
            )
            configured_teams = [{"name": "Spring Team", "coach": "Springcoach"}]

            divisions = self._build_divisions(season_dir, configured_teams)

            self.assertEqual(
                divisions["Majors"]["teams"], [("Spring Team", "Springcoach")]
            )

    def test_missing_roster_file_returns_no_teams(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertEqual(
                _discover_league_teams(Path(temp_dir) / "missing.json"), []
            )


if __name__ == "__main__":
    unittest.main()