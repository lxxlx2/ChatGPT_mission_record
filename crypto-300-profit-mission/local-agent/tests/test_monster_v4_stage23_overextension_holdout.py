"""Stage23 original V4 signal count preserved; strictly frozen pre-D1 screen."""
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

TARGET=Path(__file__).parents[1]/"scripts"/"monster_v4_stage23_overextension_holdout.py"
SOURCE=Path(__file__).parents[1]/"scripts"/"monster_v4_stage20_quality_exit_holdout.py"
EVIDENCE=Path(__file__).parents[2]/"monster"/"evidence"

def load():
    old=types.ModuleType("monster_v4_stage20_quality_exit_holdout")
    old.__file__=str(SOURCE)
    old.archive=types.SimpleNamespace(source=types.SimpleNamespace(EVIDENCE=EVIDENCE))
    old.frozen_manifest=lambda:{}
    old.universe=lambda cfg:([f"X{i}USDT" for i in range(758)],{"archive_only_sha256":"sha"})
    old.official_60h=lambda symbol,day:([1],[])
    old.run_symbol=lambda symbol,day,btc:{"symbol":symbol,"status":"SOURCE_MISSING"}
    sys.modules[old.__name__]=old
    spec=importlib.util.spec_from_file_location("testable_stage23",TARGET)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def row(relative,pass_quality=True):
    proxy={"status":"PRICE_PROXY_ONLY","net_pct":1.5,"exit_reason":"TAKE_PROFIT"}
    return {"symbol":"XUSDT","status":"COMPLETE_60H","v4_watch":2,
      "v4_d1_episodes":1,"first_v4_d1_utc":"2025-04-23T07:00:00Z",
      "quality":{"quality_pass":pass_quality,"relative_60m_return_pp":relative},
      "arm_proxies":{"D_QUALITY_D1_BOUNDED_6H_20BPS":proxy if pass_quality else None,
                     "E_QUALITY_D1_BOUNDED_6H_100BPS":proxy if pass_quality else None}}

class FrozenOverextension(unittest.TestCase):
    def test_prereg_and_stage20_git_blob_lock(self):
        m=load()
        cfg,sha=m.frozen()
        self.assertEqual(cfg["experimental_filter"]["threshold_pp"],12.0)
        self.assertEqual(sha,"93e2065e354182be3d2136be49c760674b485381")
    def test_unchanged_production_watch_and_d1(self):
        m=load()
        base=row(13.0)
        result=m.apply_filter(base)
        self.assertEqual(base["v4_watch"],result["v4_watch"])
        self.assertEqual(result["v4_d1_episodes"],1)
        self.assertFalse(result["overextension_eligible"])
        self.assertIsNone(result["frozen_arm_proxies"]["F_OVEREXTENSION_FILTER_QUALITY_BOUNDED6H_20BPS"])
        self.assertIsNotNone(result["frozen_arm_proxies"]["D_BASELINE_STAGE20_QUALITY_BOUNDED6H_20BPS"])
    def test_exact_threshold_keeps_and_high_above_rejects(self):
        m=load()
        self.assertTrue(m.apply_filter(row(12.0))["overextension_eligible"])
        self.assertFalse(m.apply_filter(row(12.000001))["overextension_eligible"])
    def test_prior_quality_rejection_not_new_setup(self):
        m=load()
        x=m.apply_filter(row(0.0,pass_quality=False))
        self.assertFalse(x["overextension_eligible"])
        self.assertEqual(x["overextension_reject_causes"],["PREVIOUS_QUALITY_REJECTED"])
    def test_unknown_date_rejected(self):
        m=load()
        with self.assertRaisesRegex(ValueError,"NONFROZEN_DATE"):
            m.run("2025-11-23")
    def test_mutated_original_stage20_strategy_detected(self):
        m=load()
        with patch.object(m,"SOURCE",Path(__file__)):
            with self.assertRaisesRegex(ValueError,"STAGE20_CODE_CHANGED"):
                m.frozen()
    def test_all_758_attempts_and_no_live_actions(self):
        m=load()
        r=m.run("2025-01-23",workers=2)
        self.assertEqual(r["summary"]["attempted"],758)
        self.assertFalse(r["trading"])
        self.assertEqual(r["deployment"],"NO_GO")
if __name__=="__main__":
    unittest.main()
