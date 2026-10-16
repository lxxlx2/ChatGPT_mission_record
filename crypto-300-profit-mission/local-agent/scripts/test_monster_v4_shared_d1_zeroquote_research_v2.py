#!/usr/bin/env python3
"""Causal research-only zero quote handling; no modified approved D0/D1."""
import json
from pathlib import Path
import tempfile
import unittest
from collections import Counter
from unittest.mock import patch

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


    def test_06_nine_queue_candidates_zero_first_cannot_promote_ninth_into_slot(self):
        tick=shared.utc_ms(DAY)+30*shared.MIN
        candle_close=tick-1
        candles=[]
        for i in range(8):
            end=candle_close-(7-i)*5*shared.MIN
            candles.append([end-5*shared.MIN+1,"1","1.1","0.9","1.05",
                           "5",end,"1000"])
        with tempfile.TemporaryDirectory() as td:
            store=variant.production.open_store(Path(td)/"queue.sqlite")
            try:
                with store:
                    for letter in "ABCDEFGHI":
                        store.execute("""INSERT INTO candidate_queue
                            (venue,symbol,first_seen_ms,last_seen_ms,priority,
                             reason,status,attempts,retry_after_ms,deadline_ms)
                            VALUES (?,?,?,?,?,?,?,?,?,?)""",
                            ("spot","A"+letter+"USDT",tick-2*shared.MIN,
                             tick,1,"SYNTHETIC_TEST","PENDING",0,0,
                             tick+15*shared.MIN))
                stats={"zero_quote_source_slots_consumed":0,
                    "terminal_unsupported":0,"by_symbol":Counter(),
                    "max_slots_in_single_tick":0}
                with patch.object(variant,"source_zero_closed5m",
                                  side_effect=lambda _db,sym,_t:
                                      sym=="AAUSDT"):
                    result=variant.experimental_queue_handler(
                        store,tick,lambda *_:candles,None,
                        limit=8,original_queue=variant.production.process_queue,
                        stats=stats)
                self.assertEqual(result["selected"],8)
                self.assertEqual(stats["max_slots_in_single_tick"],8)
                self.assertEqual(stats["zero_quote_source_slots_consumed"],1)
                q={r["symbol"]:dict(r) for r in store.execute(
                    "SELECT symbol,retry_after_ms,last_error,status FROM candidate_queue")}
                self.assertEqual(q["AAUSDT"]["last_error"],variant.WAIT_ERROR)
                self.assertEqual(q["AIUSDT"]["retry_after_ms"],0)
                self.assertIsNone(q["AIUSDT"]["last_error"])
                self.assertEqual(q["AIUSDT"]["status"],"PENDING")
                for letter in "BCDEFGH":
                    self.assertGreater(q["A"+letter+"USDT"]["retry_after_ms"],tick)
            finally:
                store.close()

    def test_07_previously_zeroquote_waited_expiry_is_not_fake_late(self):
        tick=shared.utc_ms(DAY)+30*shared.MIN
        with tempfile.TemporaryDirectory() as td:
            store=variant.production.open_store(Path(td)/"queue.sqlite")
            try:
                with store:
                    store.execute("""INSERT INTO candidate_queue
                        (venue,symbol,first_seen_ms,last_seen_ms,priority,
                         reason,status,attempts,retry_after_ms,deadline_ms,
                         last_error)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        ("spot","AAUSDT",tick-20*shared.MIN,tick,1,"TEST",
                         "PENDING",0,0,tick-shared.MIN,variant.WAIT_ERROR))
                stats={"zero_quote_source_slots_consumed":0,
                    "terminal_unsupported":0,"by_symbol":Counter(),
                    "max_slots_in_single_tick":0}
                def never_fetch(*_):
                    self.fail("zeroquote expiry must not issue an out-of-time read")
                result=variant.experimental_queue_handler(
                    store,tick,never_fetch,None,limit=8,
                    original_queue=variant.production.process_queue,stats=stats)
                self.assertEqual(result["late"],0)
                self.assertEqual(result["selected"],1)
                self.assertEqual(stats["terminal_unsupported"],1)
                q=store.execute(
                    "SELECT status,last_error FROM candidate_queue").fetchone()
                self.assertEqual(q["status"],variant.TERMINAL)
                self.assertEqual(q["last_error"],variant.WAIT_ERROR)
            finally:
                store.close()


if __name__=="__main__":
    unittest.main()
