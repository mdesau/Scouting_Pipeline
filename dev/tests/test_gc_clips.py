"""Unit tests for scout.video.gc_clips (link parsing, file naming, URL files)."""

import logging
import tempfile
import unittest
from pathlib import Path

from scout.video import gc_clips

_LOG = logging.getLogger("test_gc_clips")
_LOG.addHandler(logging.NullHandler())
_LOG.propagate = False

SHARE_URL = (
    "https://web.gc.com/teams/lIgsauxSLdBC/2026-fall-expos-esau/schedule/"
    "87bccfbe-7385-4f68-ac05-a4d53c28220b/videos/clips/37369a1a-69ef-4dea-b94d-ffb5b711186a"
    "?token=5076018d-8bb6-4d5a-9b1f-556b62930814&c=clip_share_link&pid=Copy"
)


class ParseLinkTests(unittest.TestCase):
    GAME = "https://web.gc.com/teams/lIgsauxSLdBC/2026-fall-expos-esau/schedule/87bccfbe-7385-4f68-ac05-a4d53c28220b"

    def test_share_link(self):
        self.assertEqual(gc_clips.parse_link(SHARE_URL),
                         ("clip", "37369a1a-69ef-4dea-b94d-ffb5b711186a", SHARE_URL))

    def test_game_links_point_at_the_clip_gallery(self):
        gallery = self.GAME + "/videos/clips"
        for url in (gallery, gallery + "/", self.GAME, self.GAME + "/plays", self.GAME + "/videos?x=1"):
            self.assertEqual(gc_clips.parse_link(url),
                             ("game", "87bccfbe-7385-4f68-ac05-a4d53c28220b", gallery), url)

    def test_rejects_other_links(self):
        self.assertIsNone(gc_clips.parse_link("https://web.gc.com/teams/abc/schedule"))
        self.assertIsNone(gc_clips.parse_link("https://example.com/videos/clips/37369a1a-69ef-4dea-b94d-ffb5b711186a"))

    def test_collect_drops_duplicates_and_keeps_order(self):
        other = SHARE_URL.replace("37369a1a-69ef-4dea-b94d-ffb5b711186a", "7d229b7b-3fb3-4856-83fb-7130da3a0d19")
        targets = gc_clips.collect_targets([other, self.GAME, SHARE_URL, "junk", SHARE_URL, self.GAME], _LOG)
        self.assertEqual([t[:2] for t in targets], [
            ("clip", "7d229b7b-3fb3-4856-83fb-7130da3a0d19"),
            ("game", "87bccfbe-7385-4f68-ac05-a4d53c28220b"),
            ("clip", "37369a1a-69ef-4dea-b94d-ffb5b711186a"),
        ])


class NamingTests(unittest.TestCase):
    META = {
        "clip_metadata_id": "37369a1a-69ef-4dea-b94d-ffb5b711186a",
        "event_id": "e1",
        "name": "Stole Base",
        "timestamp": "2026-11-03T23:00:54.908Z",
        "sport_metadata": {"inning": 3, "inning_half": "bottom"},
        "player_metadata": {"player_id": "p1"},
    }

    def _lookups(self):
        lk = gc_clips.new_lookups()
        gc_clips.record_lookup(lk, "https://api.team-manager.gc.com/teams/public/abc/players",
                               [{"id": "p1", "first_name": "Harper", "last_name": "Esau"}])
        gc_clips.record_lookup(lk, "https://api.team-manager.gc.com/teams/9963ed9e-636d-45eb-b8be-aaf53d33f82e",
                               {"id": "t1", "name": "Expos-Esau"})
        gc_clips.record_lookup(lk, "https://api.team-manager.gc.com/events/87bccfbe-7385-4f68-ac05-a4d53c28220b",
                               {"event": {"id": "e1", "team_id": "t1"},
                                "pregame_data": {"opponent_name": "Blue Jays-Patel"}})
        return lk

    def test_full_name(self):
        name = gc_clips.clip_filename(self.META, self._lookups())
        self.assertRegex(name, r"^Expos-Esau_vs_Blue-Jays-Patel_B3_Stole-Base_Harper-Esau_\d{8}-\d{6}\.mp4$")

    def test_missing_team_names_are_left_out(self):
        lk = self._lookups()
        lk["games"].clear()
        self.assertRegex(gc_clips.clip_filename(self.META, lk), r"^B3_Stole-Base_Harper-Esau_\d{8}-\d{6}\.mp4$")

    def test_nothing_known_falls_back_to_clip_id(self):
        meta = {"clip_metadata_id": "37369a1a-69ef-4dea-b94d-ffb5b711186a"}
        self.assertEqual(gc_clips.clip_filename(meta, gc_clips.new_lookups()),
                         "37369a1a-69ef-4dea-b94d-ffb5b711186a.mp4")

    def test_player_filter(self):
        lk = self._lookups()
        self.assertTrue(gc_clips.matches_player(self.META, lk, []))
        self.assertTrue(gc_clips.matches_player(self.META, lk, ["harper"]))
        self.assertTrue(gc_clips.matches_player(self.META, lk, ["Cole", "esau"]))
        self.assertFalse(gc_clips.matches_player(self.META, lk, ["Cole"]))
        unknown = dict(self.META, player_metadata={"player_id": "nobody"})
        self.assertFalse(gc_clips.matches_player(unknown, lk, ["Harper"]))


class ManifestTests(unittest.TestCase):
    def test_existing_clip_via_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            (out / "a.mp4").touch()
            gc_clips.save_manifest(out, {"c1": "a.mp4", "c2": "gone.mp4"})
            manifest = gc_clips.load_manifest(out)
            self.assertEqual(gc_clips.existing_clip(out, manifest, "c1"), out / "a.mp4")
            self.assertIsNone(gc_clips.existing_clip(out, manifest, "c2"))
            self.assertIsNone(gc_clips.existing_clip(out, manifest, "c3"))

    def test_unique_path_never_overwrites_another_clip(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            (out / "x.mp4").touch()
            (out / "mine.mp4").touch()
            owners = {"x.mp4": "c1", "mine.mp4": "c2"}
            self.assertEqual(gc_clips.unique_path(out, "x.mp4", "c9", owners).name, "x_2.mp4")
            self.assertEqual(gc_clips.unique_path(out, "mine.mp4", "c2", owners).name, "mine.mp4")
            (out / "stranger.mp4").touch()
            self.assertEqual(gc_clips.unique_path(out, "stranger.mp4", "c9", owners).name, "stranger_2.mp4")


class UrlFileTests(unittest.TestCase):
    def test_skips_comments_and_blanks(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "clips.txt"
            f.write_text(f"# Harper highlights\n\n  {SHARE_URL}  \n# done\n", encoding="utf-8")
            self.assertEqual(gc_clips.read_url_file(f), [SHARE_URL])


class CookieTests(unittest.TestCase):
    def test_cookie_header(self):
        self.assertEqual(
            gc_clips.cookie_header({"CloudFront-Policy": "a", "CloudFront-Signature": "b"}),
            "CloudFront-Policy=a; CloudFront-Signature=b",
        )


if __name__ == "__main__":
    unittest.main()
