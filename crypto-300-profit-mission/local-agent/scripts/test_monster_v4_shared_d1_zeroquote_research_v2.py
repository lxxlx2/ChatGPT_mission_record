#!/usr/bin/env python3
"""Causal research-only zero quote handling; no modified approved D0/D1."""
import json
import sqlite3
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


    def _nine_pending_d1_sqlite(self, path, now):
        store=variant.production.open_store(path)
        first=now-10*shared.MIN
        with store:
            for ch in "ABCDEFGHI":
                store.execute("""INSERT INTO candidate_queue
                    (venue,symbol,first_seen_ms,last_seen_ms,priority,
                     reason,status,attempts,retry_after_ms,deadline_ms)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    ("spot","A"+ch+"USDT",first,now,1,"SQL_FAILURE_PROBE",
                     "PENDING",0,0,now+15*shared.MIN))
        return store

    def _valid_source_for_tick(self, now):
        return [[end-5*shared.MIN+1,"1","1.1","0.9","1.05",
                 "5",end,"1000"] for end in
                [now-1-(7-i)*5*shared.MIN for i in range(8)]]

    def _v2_stats(self):
        return {"zero_quote_source_slots_consumed":0,
                "terminal_unsupported":0,"by_symbol":Counter(),
                "max_slots_in_single_tick":0}

    def test_08_sql_update_abort_restores_mask_after_true_producer_inner_commit(self):
        tick=shared.utc_ms(DAY)+30*shared.MIN
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"broken_update.sqlite"
            db=self._nine_pending_d1_sqlite(path,tick)
            try:
                with db:
                    db.execute("""CREATE TRIGGER fail_AB_update
                        BEFORE UPDATE ON candidate_queue
                        WHEN NEW.symbol='ABUSDT'
                        BEGIN SELECT RAISE(ABORT,'INJECTED_SQL_FAILURE'); END""")
                with patch.object(variant,"source_zero_closed5m",
                                  side_effect=lambda _db,sym,_t: sym=="AAUSDT"):
                    with self.assertRaisesRegex(sqlite3.IntegrityError,
                                                 "INJECTED_SQL_FAILURE"):
                        variant.experimental_queue_handler(
                            db,tick,lambda *_:self._valid_source_for_tick(tick),None,
                            original_queue=variant.production.process_queue,
                            stats=self._v2_stats())
                self.assertEqual(db.execute("""SELECT retry_after_ms FROM
                    candidate_queue WHERE symbol='AAUSDT'""").fetchone()[0],0)
                self.assertEqual(db.execute("""SELECT retry_after_ms FROM
                    candidate_queue WHERE symbol='AIUSDT'""").fetchone()[0],0)
            finally:
                db.close()
            reopened=sqlite3.connect(path)
            try:
                values=dict(reopened.execute("""SELECT symbol,retry_after_ms
                    FROM candidate_queue WHERE symbol IN ('AAUSDT','AIUSDT')"""))
                self.assertEqual(values,{"AAUSDT":0,"AIUSDT":0})
                self.assertEqual(reopened.execute("PRAGMA integrity_check").fetchone()[0],
                                 "ok")
            finally:
                reopened.close()

    def test_09_source_reader_error_after_committed_producer_restores_both_masks(self):
        tick=shared.utc_ms(DAY)+30*shared.MIN
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"bad_reader.sqlite"
            db=self._nine_pending_d1_sqlite(path,tick)
            observed=[]
            def fetch(_venue,symbol,_tick):
                observed.append(symbol)
                if symbol=="ACUSDT":
                    raise RuntimeError("INJECTED_HISTORY_READ_FAILURE")
                return self._valid_source_for_tick(tick)
            try:
                with patch.object(variant,"source_zero_closed5m",
                                  side_effect=lambda _db,sym,_t:sym=="AAUSDT"):
                    with self.assertRaisesRegex(
                           RuntimeError,"INJECTED_HISTORY_READ_FAILURE"):
                        variant.experimental_queue_handler(
                            db,tick,fetch,None,
                            original_queue=variant.production.process_queue,
                            stats=self._v2_stats())
                self.assertEqual(observed[:2],["ABUSDT","ACUSDT"])
            finally:
                db.close()
            reopened=sqlite3.connect(path)
            try:
                states=dict(reopened.execute("""SELECT symbol,retry_after_ms
                    FROM candidate_queue WHERE symbol IN ('AAUSDT','AIUSDT')"""))
                self.assertEqual(states,{"AAUSDT":0,"AIUSDT":0})
                self.assertEqual(reopened.execute("PRAGMA integrity_check").fetchone()[0],
                                 "ok")
            finally:
                reopened.close()

    def test_10_six_deadline_boundaries_preserve_prior_valid_D1_ownership(self):
        base=shared.utc_ms(DAY)+60*shared.MIN
        for completed in (False,True):
            for delta in (-1,0,1):
                with self.subTest(prior_evaluated=completed,offset=delta):
                    deadline=base
                    tick=deadline+delta
                    with tempfile.TemporaryDirectory() as td:
                        db=variant.production.open_store(
                            Path(td)/"deadline.sqlite")
                        try:
                            with db:
                                db.execute("""INSERT INTO candidate_queue
                                    (venue,symbol,first_seen_ms,last_seen_ms,
                                     priority,reason,status,attempts,
                                     retry_after_ms,deadline_ms,last_error,
                                     last_evaluated_bar_ms)
                                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                                    ("spot","AAUSDT",deadline-15*shared.MIN,tick,
                                     1,"DEADLINE_BOUNDARY","PENDING",0,0,
                                     deadline,variant.WAIT_ERROR,
                                     deadline-5*shared.MIN if completed else None))
                            stats=self._v2_stats()
                            with patch.object(variant,"source_zero_closed5m",
                                              return_value=True):
                                output=variant.experimental_queue_handler(
                                   db,tick,lambda *_:self._valid_source_for_tick(tick),
                                   None,original_queue=variant.production.process_queue,
                                   stats=stats)
                            q=db.execute("""SELECT status,last_error,
                                last_evaluated_bar_ms FROM candidate_queue""").fetchone()
                            if delta==-1:
                                self.assertEqual(q["status"],"PENDING")
                                self.assertEqual(q["last_error"],variant.WAIT_ERROR)
                                self.assertEqual(output["completed"],0)
                            elif completed:
                                self.assertEqual(q["status"],"EVALUATED")
                                self.assertEqual(q["last_error"],
                                                 "NO_SETUP_WITHIN_WINDOW")
                                self.assertEqual(q["last_evaluated_bar_ms"],
                                                 deadline-5*shared.MIN)
                                self.assertEqual(output["completed"],1)
                                self.assertEqual(stats["terminal_unsupported"],0)
                            else:
                                self.assertEqual(q["status"],variant.TERMINAL)
                                self.assertEqual(output["completed"],0)
                                self.assertEqual(stats["terminal_unsupported"],1)
                            self.assertEqual(output["late"],0)
                            self.assertEqual(db.execute("""SELECT COUNT(*)
                                FROM events WHERE event_type='LATE_REVIEW'""").fetchone()[0],0)
                        finally:
                            db.close()

    def test_11_no_prior_quote_failure_reverts_to_original_real_late(self):
        tick=shared.utc_ms(DAY)+35*shared.MIN
        with tempfile.TemporaryDirectory() as td:
            db=variant.production.open_store(Path(td)/"late.sqlite")
            try:
                with db:
                    db.execute("""INSERT INTO candidate_queue
                        (venue,symbol,first_seen_ms,last_seen_ms,priority,
                         reason,status,attempts,retry_after_ms,deadline_ms)
                        VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        ("spot","AAUSDT",tick-17*shared.MIN,tick,1,"OLD_LATE",
                         "PENDING",0,0,tick-shared.MIN))
                out=variant.experimental_queue_handler(
                    db,tick,lambda *_:self._valid_source_for_tick(tick),None,
                    original_queue=variant.production.process_queue,
                    stats=self._v2_stats())
                self.assertEqual(out["late"],1)
                self.assertEqual(db.execute("SELECT status FROM candidate_queue"
                                            ).fetchone()[0],"LATE")
            finally:
                db.close()


if __name__=="__main__":
    unittest.main()
