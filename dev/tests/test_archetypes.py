"""Batter archetypes from per-age baselines (BUG-024 Enh)."""

import unittest

from scout.hitting import archetypes as arch
from scout.hitting import build_archetype_baselines as bab

FLAT = [round(i / 20, 4) for i in range(21)]   # cutoffs 0.00 … 1.00: rank = value × 100


def batter(pa=20, **kw):
    b = {"pa": pa, "ab": pa - 4, "h": 5, "tb": 7, "bb": 4, "k_sw": 3, "k_lk": 1, "bip": 10,
         "zone_detail": {"LF": {"gb": 1, "fb_ld": 3}, "SS": {"gb": 4, "fb_ld": 0}},
         "p_balls": 30, "p_called_str": 10, "p_swing_miss": 8, "p_fouls": 6, "p_in_play": 10,
         "fpt_swings": 5, "fpt_takes": 15}
    b.update(kw)
    return b


def baselines():
    base = {"mean": {s: 0.5 for s in arch.STATS}, "pct": {s: FLAT for s in arch.STATS}}
    return {"shrink_k": {s: 0.0 for s in arch.STATS},
            "groups": {"travel 11U": base, "travel 12U": {"kids": 11, "use": "travel 11U"}, "league 9U": base}}


class CountsTests(unittest.TestCase):
    def test_counts(self):
        c = arch.counts(batter())
        self.assertEqual((c["swings"], c["pitches"], c["xb"], c["k"], c["kl"], c["of_air"], c["fp_seen"]),
                         (24, 64, 2, 4, 1, 3, 20))


class RankTests(unittest.TestCase):
    def test_interpolates_and_clamps(self):
        self.assertAlmostEqual(arch.pct_rank(FLAT, 0.33), 33.0)
        self.assertEqual(arch.pct_rank(FLAT, -1), 0.0)
        self.assertEqual(arch.pct_rank(FLAT, 2), 100.0)

    def test_flat_cutoffs_take_highest_point(self):
        cuts = [0.0] * 11 + [round(i / 10, 2) for i in range(1, 11)]
        self.assertEqual(arch.pct_rank(cuts, 0.0), 50.0)

    def test_shrinkage_pulls_small_samples_to_mean(self):
        c = {"k": 4, "pa": 8}
        self.assertAlmostEqual(arch.shrunk_rate(c, "k", 0.25, 8), 0.375)
        self.assertAlmostEqual(arch.shrunk_rate({"k": 40, "pa": 80}, "k", 0.25, 8), (40 + 2) / 88)


class ClassifyTests(unittest.TestCase):
    MID = {s: 50 for s in arch.STATS}

    def p(self, **kw):
        return {**self.MID, **kw}

    def test_default_is_disciplined_contact(self):
        self.assertEqual(arch.classify(self.MID), ("Disciplined", "Contact"))

    def test_approach(self):
        self.assertEqual(arch.classify(self.p(swing=70))[0], "Aggressive")
        self.assertEqual(arch.classify(self.p(fps=80, swing=55))[0], "Aggressive")
        self.assertEqual(arch.classify(self.p(swing=62, ppa=30))[0], "Aggressive")
        self.assertEqual(arch.classify(self.p(cstr=70, kl=50))[0], "Passive")
        self.assertEqual(arch.classify(self.p(cstr=70, kl=40))[0], "Disciplined")

    def test_result_order(self):
        self.assertEqual(arch.classify(self.p(whiff=80, k=70, iso=90, of_air=90))[1], "Overmatched")
        self.assertEqual(arch.classify(self.p(iso=70, of_air=50))[1], "Power")
        self.assertEqual(arch.classify(self.p(iso=70, of_air=40))[1], "Contact")
        self.assertEqual(arch.classify(self.p(swing=30, bb=70))[1], "Walker")
        self.assertEqual(arch.classify(self.p(swing=30, ppa=80))[1], "Walker")
        self.assertEqual(arch.classify(self.p(swing=40, bb=90))[1], "Contact")


class GroupTests(unittest.TestCase):
    def test_use_fallback_and_nearest_age(self):
        b = baselines()
        self.assertEqual(arch.resolve_group(b, "travel 12U"), "travel 11U")
        self.assertEqual(arch.resolve_group(b, "travel 13U"), "travel 11U")
        self.assertEqual(arch.resolve_group(b, "league 10U"), "league 9U")
        self.assertIsNone(arch.resolve_group({"groups": {"league 9U": {}}}, "travel 10U"))

    def test_division_group_key(self):
        self.assertEqual(arch.group_key("travel", "12U"), "travel 12U")
        self.assertIsNone(arch.group_key("travel", None))


class LabelTests(unittest.TestCase):
    def test_pa_gate_and_star(self):
        b = baselines()
        self.assertIsNone(arch.get_label(batter(pa=4), "travel 11U", b))
        self.assertTrue(arch.get_label(batter(pa=7), "travel 11U", b).endswith("*"))
        self.assertFalse(arch.get_label(batter(pa=12), "travel 12U", b).endswith("*"))

    def test_no_group(self):
        self.assertIsNone(arch.get_label(batter(), None, baselines()))


class BuildTests(unittest.TestCase):
    def test_baseline_group_uses_team_name_age(self):
        row = {"kind": "travel", "div_age": "10U", "team": "Mara Cobras 9U"}
        self.assertEqual(bab.baseline_group(row), "travel 9U")
        self.assertEqual(bab.baseline_group({**row, "team": "Weddington Stormtroopers"}), "travel 10U")
        self.assertEqual(bab.baseline_group(row, ignore=["Mara Cobras 9U"]), "travel 10U")
        self.assertEqual(bab.baseline_group({"kind": "league", "div_age": "9U"}), "league 9U")

    def test_small_group_falls_back_to_younger_then_older(self):
        qual = {"travel 9U": [0] * 70, "travel 11U": [0] * 70, "travel 12U": [0] * 5, "travel 8U": [0] * 5}
        self.assertEqual(bab._fallback("travel 12U", qual), "travel 11U")
        self.assertEqual(bab._fallback("travel 8U", qual), "travel 9U")

    def test_shipped_baselines_are_well_formed(self):
        data = arch.load_baselines()
        self.assertIsNotNone(data)
        for g, e in data["groups"].items():
            if "use" in e:
                self.assertIn(e["use"], data["groups"])
                continue
            for s in arch.STATS:
                cuts = e["pct"][s]
                self.assertEqual(len(cuts), len(arch.PCT_POINTS), (g, s))
                self.assertEqual(cuts, sorted(cuts), (g, s))


if __name__ == "__main__":
    unittest.main()
