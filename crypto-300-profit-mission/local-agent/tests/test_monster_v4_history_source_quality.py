"""Data quality audit test on all 60 authentic historical Binance sources."""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/monster_v4_history_source_quality.py"
sp=importlib.util.spec_from_file_location("monster_v4_history_source_quality",SCRIPT)
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)


class SourceQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=m.audit()

    def test_all_predeclared_60_source_files_exist(self):
        x=self.report
        self.assertEqual(x["registered_cases"],60)
        self.assertEqual(x["fetched_case_files"],60)
        self.assertEqual(sum(x["status_counts"].values()),60)
        self.assertEqual(x["cohorts"]["FULLMARKET_SAMPLED"]["registered"],30)
        self.assertEqual(x["cohorts"]["GT5X_PREHIT_POSITIVE"]["registered"],30)

    def test_missing_history_never_counted_as_valid(self):
        x=self.report
        self.assertGreater(x["status_counts"].get("INCOMPLETE_60H",0),0)
        profiles={(z["venue"],z["symbol"]):z for z in x["cases"]}
        self.assertEqual(profiles["spot","XTZUSDT"]["status"],"VALID_60H")
        self.assertEqual(profiles["spot","CHZUSDT"]["status"],"INCOMPLETE_60H")
        self.assertGreater(profiles["spot","CHZUSDT"][
            "first_available_vs_expected_minutes"],0)

    def test_listing_cases_not_silently_excluded(self):
        x=self.report
        self.assertEqual(x["new_listing_proxy_cases"],10)
        self.assertEqual(x["new_listing_proxy_valid_24h_warmup"],0)
        self.assertTrue(x["missing_data_is_not_model_miss"])

    def test_mutated_file_source_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            fname="monster_v4_replay_1m_spot_XTZUSDT_2025-03-02.json"
            src=json.loads((m.EVIDENCE/fname).read_text(encoding="utf-8"))
            src["symbol"]="FAKEUSDT"
            (root/fname).write_text(json.dumps(src),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"SOURCE_IDENTITY_MISMATCH"):
                m.audit(evidence=root)


if __name__=="__main__":
    unittest.main()
