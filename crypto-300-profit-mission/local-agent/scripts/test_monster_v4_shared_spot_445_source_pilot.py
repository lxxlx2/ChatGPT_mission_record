#!/usr/bin/env python3
"""Real original process_queue + original old per-symbol V4 core, synthetic pilot."""
import unittest

import monster_v4_shared_spot_445_source_pilot as pilot
from test_monster_v4_shared_spot_d0_d1_original_core import fixture, fake_receipts


class Frozen445PilotTests(unittest.TestCase):
    def test_01_lexicographic_no_known_watch_selector(self):
        selected=pilot.frozen_selection(8)
        self.assertEqual(len(selected),8)
        self.assertEqual(tuple(sorted(selected)),selected)
        self.assertEqual(selected, pilot.frozen_selection())
        self.assertIn("0GUSDT",selected)
        self.assertNotIn("BTCUSDT",selected)
        eligible=pilot.shared.original_source_freeze()[1][pilot.DAY.isoformat()]["complete_symbols"]
        self.assertEqual(selected,tuple(eligible[:8]))

    def test_02_cannot_inflate_source_population(self):
        for value in (0,17,-1,0.5,True,"8"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError,"PILOT_SIZE"):
                    pilot.frozen_selection(value)

    def test_03_actual_original_d0_and_global_d1_same_raw_minute_watch_clock(self):
        symbols=pilot.frozen_selection(2)
        first=symbols[0]
        calls=[]
        def fake_reader(symbol,day):
            calls.append((symbol,day))
            return fixture(symbol,impulse=(symbol==first)),fake_receipts(symbol)
        result=pilot.run_pilot(2,source_reader=fake_reader)
        self.assertEqual(len(calls),2)
        self.assertEqual(tuple(s for s,_ in calls),symbols)
        self.assertFalse(result["source_origin_verified"])
        self.assertTrue(result["matched_D0_watch_exact_for_all_pilot_symbols"])
        self.assertEqual(result["original_per_symbol_watch_total"],1)
        self.assertEqual(result["execution_counts"]["D0_watch_new"],1)
        self.assertEqual(result["execution_counts"]["polls"],3360)
        self.assertFalse(result["true_full_758_replay"])
        self.assertTrue(result["not_full_445_shared_replay"])
        self.assertEqual(result["original_758_coverage"]["original_758_denominator"],758)
        self.assertEqual(result["original_758_coverage"]["source_missing_or_incomplete_original_stage26"],313)
        self.assertEqual(result["original_758_coverage"]["source_complete_but_not_replayed"],443)
        self.assertEqual(result["market_coverage"],"SYNTHETIC_TEST_ONLY")
        self.assertEqual(len(result["publisher_proof"]),2)
        self.assertEqual(len(result["publisher_proof"][0]["publisher_daily_sha"]),10)

    def test_04_refuses_to_verify_external_source_from_injected_reader(self):
        sym=pilot.frozen_selection(1)[0]
        def forged(symbol,day):
            return fixture(symbol,impulse=False),fake_receipts(symbol)
        result=pilot.run_pilot(1,source_reader=forged)
        self.assertFalse(result["source_origin_verified"])
        self.assertEqual(result["source_attestation"],"SYNTHETIC_INJECTED_NOT_OFFICIAL")
        self.assertEqual(result["original_758_coverage"]["per_symbol"][0]["source_disposition"],
                         "PRELOADED_CACHE_REPLAYED_ORIGIN_UNATTESTED")


if __name__=="__main__":
    unittest.main()
