"""Stage21 strict holdout freeze, immutable V4 engine and source integrity."""
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from datetime import date
from unittest.mock import patch

ROOT=Path(__file__).parents[1]
CODE=ROOT/"scripts"/"monster_v4_stage21_extended_holdout.py"
EVIDENCE=ROOT.parent/"monster"/"evidence"
PRIOR=ROOT/"scripts"/"monster_v4_stage20_quality_exit_holdout.py"

def load():
    previous=types.ModuleType("monster_v4_stage20_quality_exit_holdout")
    previous.__file__=str(PRIOR)
    previous.archive=types.SimpleNamespace(source=types.SimpleNamespace(EVIDENCE=EVIDENCE))
    previous.stage15=types.SimpleNamespace(inventory=lambda:{"unused":True})
    previous.frozen_manifest=lambda:{"quality":"locked"}
    previous.universe=lambda cfg,inventory_get: (
       [f"X{i}USDT" for i in range(758)],{"archive_only_sha256":"s3fixed"})
    previous.official_60h=lambda s,d:([1], [{"sha256":"x"*64}])
    previous.run_symbol=lambda s,d,btc: {
        "symbol":s,"status":"SOURCE_MISSING"}
    previous.summarize=lambda rows:{"attempted":len(rows),"valid_60h":0,
             "source_status":{"SOURCE_MISSING":len(rows)}}
    sys.modules[previous.__name__]=previous
    spec=importlib.util.spec_from_file_location("stage21_testable",CODE)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class Stage21FreezeTests(unittest.TestCase):
    def test_original_rule_blob_stays_identical(self):
        m=load()
        cfg,blob=m.frozen_manifest()
        self.assertEqual(blob,cfg["exact_stage20_code_git_blob_sha1"])
        self.assertEqual(len(cfg["frozen_dates_utc"]),10)
        self.assertFalse(cfg["new_monitor"])
    def test_unknown_date_rejected_without_fetch(self):
        m=load()
        with self.assertRaisesRegex(ValueError,"UNREGISTERED_DATE"):
            m.run_day("2026-10-13")
    def test_frozen_dates_no_duplicate_with_stage20(self):
        m=load()
        cfg,_=m.frozen_manifest()
        self.assertFalse(set(cfg["frozen_dates_utc"])&set(cfg["previous_stage20_dates"]))
        self.assertFalse(set(cfg["frozen_dates_utc"])&set(cfg["prior_exposed_stage12_19_dates"]))
    def test_existing_rule_mutation_fails_closed(self):
        m=load()
        cfg,_=m.frozen_manifest()
        with patch.object(m,"STAGE20_SCRIPT",Path(__file__)):
            with self.assertRaisesRegex(ValueError,"PREVIOUS_STRATEGY_CODE_CHANGED"):
                m.frozen_manifest()
    def test_all_symbols_preserved_and_worker_identity(self):
        m=load()
        report=m.run_day("2025-05-09")
        self.assertEqual(report["summary"]["attempted"],758)
        self.assertEqual(len(report["cases"]),758)
        self.assertTrue(report["no_trading"])
        self.assertTrue(report["no_new_watch"])
        def wrong(symbol,day,btc):
            return {"symbol":"NOT_TARGET_USDT","status":"SOURCE_MISSING"}
        with self.assertRaisesRegex(ValueError,"WORKER_SYMBOL_MISMATCH"):
            m.run_day("2026-03-09",worker=wrong)
if __name__=="__main__":
    unittest.main()
