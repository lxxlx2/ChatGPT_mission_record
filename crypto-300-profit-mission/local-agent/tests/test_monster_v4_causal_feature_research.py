"""Causal Stage8 feature exploration on real 60h Binance source cases."""
import importlib.util
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"scripts/monster_v4_causal_feature_research.py"
spec=importlib.util.spec_from_file_location("monster_v4_causal_feature_research",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class CausalResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=m.research()

    def test_all_40_real_valid_cases_and_20_missing_historical_series_explicit(self):
        self.assertEqual(self.data["frozen_historical_event_cases"],40)
        self.assertEqual(self.data["cases_excluded"],20)
        self.assertTrue(self.data["thresholds_pre_exposed_to_2021_2026_data"])
        self.assertFalse(self.data["independent_unseen_holdout"])

    def test_rules_contain_only_past_trailing_features(self):
        self.assertEqual(set(m.RULES),set(self.data["summary"]))
        self.assertTrue(all(x["return_window"] in (15,60,240) for x in m.RULES.values()))
        self.assertTrue(all(x["vol_ratio"]>0 for x in m.RULES.values()))

    def test_cannot_infer_marketwide_precision_from_selected_cohorts(self):
        self.assertTrue(self.data["false_positive_rate_unknown_in_general_universe"])
        for name,by_cohort in self.data["summary"].items():
            for _,group in by_cohort.items():
                self.assertEqual(group["n"],20)
                self.assertEqual(group["detected"]+group["not_detected"],20)
                self.assertEqual(group["before_old_watch"]+
                                 group["after_old_watch"],group["detected"])


if __name__=="__main__":
    unittest.main()
