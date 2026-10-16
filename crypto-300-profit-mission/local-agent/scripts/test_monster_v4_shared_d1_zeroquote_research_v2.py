#!/usr/bin/env python3
"""Causal research-only zero quote handling; no modified approved D0/D1."""
import json
from pathlib import Path
import tempfile
import unittest

import monster_v4_shared_d1_zeroquote_research_v2 as variant
import monster_v4_shared_spot_d0_d1_original_core as shared
from test_monster_v4_shared_spot_d0_d1_original_core import DAY,fixture,fake_receipts


class ZeroQuoteResearchVariantTests(unittest.TestCase):
    def test_01_original_engine_and_D0_source_blob_still_frozen(self):
        self.assertEqual(shared.production_blob(),shared.ORIGINAL_SHADOW_BLOB)
        shared.assert_original_core()
        self.assertNotEqual(variant.SCHEMA,shared.SCHEMA)

    def test_02_no_quotezero_retains_exact_original_event_and_queue_results(self):
        with tempfile.TemporaryDirectory() as td:
            with shared.setup_cache(Path(td)/"s.sqlite") as cache:
                shared.prepare_symbol(cache,"AAUSDT",DAY,
                                      fixture("AAUSDT",impulse=True),
                                      fake_receipts("AAUSDT"))
                old=shared.run_shared(cache,DAY,("AAUSDT",),
                                       market_coverage_label="SYNTHETIC_TEST_ONLY")
                new=variant.run_v2(cache,DAY,("AAUSDT",),
                                       market_coverage_label="SYNTHETIC_TEST_ONLY")
        self.assertEqual(old["queue_rows"],new["queue_rows"])
        self.assertEqual(old["events"],new["events"])
        self.assertEqual(old["execution_counts"],new["execution_counts"])
        self.assertEqual(old["event_type_counts"],new["event_type_counts"])
        self.assertEqual(new["D1_zero_quote_unsupported_attempt_slots"],0)
        self.assertEqual(new["D1_zero_quote_terminal_candidates"],0)
        self.assertFalse(new["only_original_production_D0_and_D1_called"])
        self.assertEqual(old["execution_counts"]["D0_watch_new"],1)

    def test_03_real_production_source_with_zero_5m_is_censored_not_late(self):
        with tempfile.TemporaryDirectory() as td:
            with shared.setup_cache(Path(td)/"z.sqlite") as db:
                shared.prepare_symbol(db,"AAUSDT",DAY,
                                      fixture("AAUSDT",impulse=True),
                                      fake_receipts("AAUSDT"))
                original=shared.run_shared(db,DAY,("AAUSDT",),
                              market_coverage_label="SYNTHETIC_TEST_ONLY")
                watch=next(e["observed_ms"] for e in original["events"]
                           if e["event_type"]=="WATCH_EARLY")
                closing=(watch//(5*shared.MIN))*(5*shared.MIN)-1
                item=db.execute("""SELECT candle_json FROM closed5m_source
                    WHERE symbol=? AND end_ms=?""",("AAUSDT",closing)).fetchone()
                self.assertIsNotNone(item)
                source=json.loads(item[0])
                source[7]="0"
                db.execute("""UPDATE closed5m_source SET candle_json=?
                    WHERE symbol=? AND end_ms=?""",
                    (json.dumps(source),"AAUSDT",closing))
                db.commit()
                with self.assertRaisesRegex(RuntimeError,
                                             "SHARED_SPOT_ORIGINAL_D1_SOURCE_INVALID_CANDLE"):
                    shared.run_shared(db,DAY,("AAUSDT",),
                        market_coverage_label="SYNTHETIC_TEST_ONLY")
                output=variant.run_v2(db,DAY,("AAUSDT",),
                        market_coverage_label="SYNTHETIC_TEST_ONLY")
        self.assertEqual(output["execution_counts"]["D0_watch_new"],1)
        self.assertEqual(output["execution_counts"]["D1_late"],0)
        self.assertGreater(output["D1_zero_quote_unsupported_attempt_slots"],0)
        self.assertEqual(output["D1_zero_quote_terminal_candidates"],1)
        self.assertEqual(output["queue_status_counts"].get(variant.TERMINAL),1)
        self.assertEqual(output["event_type_counts"].get("SETUP_ACTIVE",0),0)

    def test_04_corrupt_high_even_with_quotezero_is_fatal(self):
        with tempfile.TemporaryDirectory() as td:
            with shared.setup_cache(Path(td)/"bad.sqlite") as db:
                shared.prepare_symbol(db,"AAUSDT",DAY,
                                      fixture("AAUSDT",impulse=True),
                                      fake_receipts("AAUSDT"))
                source=shared.run_shared(db,DAY,("AAUSDT",),
                                  market_coverage_label="SYNTHETIC_TEST_ONLY")
                watch=next(e["observed_ms"] for e in source["events"]
                         if e["event_type"]=="WATCH_EARLY")
                end=(watch//(5*shared.MIN))*(5*shared.MIN)-1
                r=db.execute("""SELECT candle_json FROM closed5m_source
                    WHERE symbol=? AND end_ms=?""",("AAUSDT",end)).fetchone()
                c=json.loads(r[0])
                c[2]="0"
                c[7]="0"
                db.execute("""UPDATE closed5m_source SET candle_json=?
                    WHERE symbol=? AND end_ms=?""",
                    (json.dumps(c),"AAUSDT",end))
                db.commit()
                with self.assertRaisesRegex(RuntimeError,
                    "ZEROQUOTE_RESEARCH_REAL_D1_SOURCE_CORRUPTED"):
                    variant.run_v2(db,DAY,("AAUSDT",),
                        market_coverage_label="SYNTHETIC_TEST_ONLY")

    def test_05_research_only_limit_is_original_eight(self):
        with self.assertRaisesRegex(ValueError,"ORIGINAL_EIGHT_CAPACITY"):
            variant.experimental_queue_handler(None,1,None,None,
                limit=9,original_queue=None,stats={})
        self.assertEqual(variant.TERMINAL,"SOURCE_UNSUPPORTED_D1_ZERO_QUOTE")


if __name__=="__main__":
    unittest.main()
