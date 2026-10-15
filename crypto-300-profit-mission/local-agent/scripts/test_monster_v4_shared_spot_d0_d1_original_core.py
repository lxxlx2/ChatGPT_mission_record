#!/usr/bin/env python3
"""Shared D0 original production regressions; SYNTHETIC only, no source claims."""
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import sqlite3
import tempfile
import unittest

import monster_v4_shared_spot_d0_d1_original_core as sh
import monster_v4_stage26_continuous168h as old

DAY = date(2026,2,4)
START = sh.utc_ms(DAY)-1440*sh.MIN


def fixture(symbol, impulse=False):
    rows=[]
    base=Decimal("100")
    for i in range(sh.TOTAL):
        last=Decimal("120") if impulse and i>=1440+40 else base
        rows.append((START+i*sh.MIN,last,last,last,last,
                    Decimal("100"),4))
    return rows


def fake_receipts(symbol):
    return [{"date":(DAY+timedelta(days=i)).isoformat(),
             "sha256":("a" if symbol=="AAUSDT" else "b")*64,
             "verified_published_sha256":True}
            for i in range(-1,9)]


class SharedOriginalV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.db=sh.setup_cache(Path(cls.temp.name)/"features.sqlite")
        cls.A=fixture("AAUSDT",impulse=True)
        cls.B=fixture("BBUSDT")
        for sym,bars in (("AAUSDT",cls.A),("BBUSDT",cls.B)):
            sh.prepare_symbol(cls.db,sym,DAY,bars,fake_receipts(sym))

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        cls.temp.cleanup()

    def test_01_original_production_v4_core_blob_pinned(self):
        self.assertEqual(sh.production_blob(),sh.ORIGINAL_SHADOW_BLOB)
        sh.assert_original_core()

    def test_02_full_market_two_symbols_one_db_per_tick(self):
        r=sh.run_shared(self.db,DAY,("AAUSDT","BBUSDT"),
                        market_coverage_label="SYNTHETIC_TEST_ONLY")
        self.assertEqual(r["source"],"SYNTHETIC_FIXTURE_ONLY")
        self.assertFalse(r["source_origin_verified"])
        self.assertFalse(r["true_full_758_replay"])
        self.assertTrue(r["one_shared_sqlite_for_all_symbols"])
        self.assertEqual(r["source_coverage"]["poll_ticks"],3360)
        self.assertEqual(r["source_coverage"]["expected_source_rows"],6720)
        self.assertEqual(r["execution_counts"]["polls"],3360)
        self.assertGreaterEqual(r["event_type_counts"].get("WATCH_EARLY",0),1)
        self.assertGreaterEqual(len(r["queue_rows"]),1)
        self.assertTrue(all(x["venue"]=="spot" for x in r["events"]))
        self.assertEqual(r["execution_counts"]["D0_watch_new"],
                         r["event_type_counts"]["WATCH_EARLY"])
        self.__class__.shared_result=r

    def test_03_watch_causal_clock_equals_original_independent_core(self):
        original=old.scan_continuous("AAUSDT",DAY,self.A)
        shared=getattr(self.__class__,"shared_result",None)
        if shared is None:
            shared=sh.run_shared(self.db,DAY,("AAUSDT","BBUSDT"),
                                 market_coverage_label="SYNTHETIC_TEST_ONLY")
        ours=sorted(x["observed_ms"] for x in shared["events"]
                    if x["symbol"]=="AAUSDT" and x["event_type"]=="WATCH_EARLY")
        from monster_v4_historical_replay import parse_ms
        expected=sorted(parse_ms(x) for x in original["watch_utcs"])
        self.assertEqual(ours,expected)
        self.assertTrue(all(ms>=sh.utc_ms(DAY) for ms in ours))

    def test_04_one_symbol_ticker_and_d1_one_sqlite(self):
        with tempfile.TemporaryDirectory() as td:
            with sh.setup_cache(Path(td)/"one.sqlite") as db:
                sh.prepare_symbol(db,"AAUSDT",DAY,self.A,fake_receipts("AAUSDT"))
                x=sh.run_shared(db,DAY,("AAUSDT",),
                                market_coverage_label="SYNTHETIC_TEST_ONLY")
                self.assertEqual(x["source_coverage"]["expected_source_rows"],3360)
                self.assertEqual(x["event_type_counts"].get("WATCH_EARLY"),1)

    def test_05_no_false_full_758_claim_on_two_symbols(self):
        with self.assertRaisesRegex(ValueError,"CANNOT_CLAIM_758"):
            sh.run_shared(self.db,DAY,("AAUSDT","BBUSDT"),
                          market_coverage_label="FULL_758_OFFICIAL_VERIFIED")

    def test_06_missing_tick_any_symbol_rejected_before_model(self):
        with tempfile.TemporaryDirectory() as td:
            with sh.setup_cache(Path(td)/"corrupt.sqlite") as db:
                sh.prepare_symbol(db,"AAUSDT",DAY,self.A,fake_receipts("AAUSDT"))
                sh.prepare_symbol(db,"BBUSDT",DAY,self.B,fake_receipts("BBUSDT"))
                with db:
                    db.execute("DELETE FROM tick_source WHERE symbol='BBUSDT' AND tick_ms=?",
                               (sh.utc_ms(DAY)+6*sh.MIN,))
                with self.assertRaisesRegex(ValueError,"INCOMPLETE_ALL_SYMBOL_TICK"):
                    sh.run_shared(db,DAY,("AAUSDT","BBUSDT"),
                                  market_coverage_label="SYNTHETIC_TEST_ONLY")

    def test_07_unverified_publisher_or_missing_day_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with sh.setup_cache(Path(td)/"receipts.sqlite") as db:
                wrong=fake_receipts("AAUSDT")
                wrong[0]["verified_published_sha256"]=False
                with self.assertRaisesRegex(ValueError,"10_OFFICIAL_PUBLISHER"):
                    sh.prepare_symbol(db,"AAUSDT",DAY,self.A,wrong)
                with self.assertRaisesRegex(ValueError,"10_OFFICIAL_PUBLISHER"):
                    sh.prepare_symbol(db,"AAUSDT",DAY,self.A,
                                      fake_receipts("AAUSDT")[:9])

    def test_08_gapped_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with sh.setup_cache(Path(td)/"missing.sqlite") as db:
                modified=list(self.A)
                j=1290
                modified[j]=(modified[j][0]+sh.MIN,)+modified[j][1:]
                with self.assertRaisesRegex(ValueError,"12960_CONTIGUOUS"):
                    sh.prepare_symbol(db,"AAUSDT",DAY,modified,
                                      fake_receipts("AAUSDT"))

    def test_09_wrong_source_date_or_sha_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with sh.setup_cache(Path(td)/"wrongdate.sqlite") as db:
                receipts=fake_receipts("AAUSDT")
                receipts[3]["date"]="2025-01-01"
                with self.assertRaisesRegex(ValueError,"10_OFFICIAL_PUBLISHER"):
                    sh.prepare_symbol(db,"AAUSDT",DAY,self.A,receipts)
                receipts=fake_receipts("AAUSDT")
                receipts[2]["sha256"]="z"*64
                with self.assertRaisesRegex(ValueError,"10_OFFICIAL_PUBLISHER"):
                    sh.prepare_symbol(db,"AAUSDT",DAY,self.A,receipts)

    def test_09_closed_five_minute_source_has_no_future(self):
        tick=sh.utc_ms(DAY)+3*sh.MIN
        earliest=self.db.execute("""
            SELECT end_ms FROM closed5m_source WHERE symbol='AAUSDT'
            AND end_ms<? ORDER BY end_ms DESC LIMIT 8""",(tick,)).fetchall()
        latest=self.db.execute("""
            SELECT MIN(end_ms) FROM closed5m_source
            WHERE symbol='AAUSDT' AND end_ms>=?""",(tick,)).fetchone()[0]
        self.assertTrue(all(x[0]<tick for x in earliest))
        self.assertGreaterEqual(latest,tick)

    def test_10_mixed_or_duplicate_original_universe_rejected(self):
        for syms in ([],["AAUSDT","AAUSDT"],["AAUSDT","BAD"],["非ASCIIUSDT"]):
            with self.subTest(symbols=syms):
                with self.assertRaisesRegex(ValueError,"INVALID"):
                    sh.clean_roster(syms)

    def test_11_current_758_source_missing_not_borrowed_from_stage26_watch(self):
        self.assertEqual(sh.FROZEN_ORIGINAL_POPULATION,758)
        self.assertEqual(len(sh.FROZEN_DATES),6)
        self.assertEqual(sh.TOTAL,12960)
        self.assertEqual(sh.WARMUP,1440)
        self.assertEqual(sh.ACTIVE,10080)
        self.assertEqual(sh.TICK,3*sh.MIN)
        # No Stage26 WATCH_EARLY timestamp or Stage28 injected WATCH is used
        # as input: the cache contains ONLY authenticated minute features.
        tables={r[0] for r in self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(tables,{
            "tick_source","closed5m_source","source_receipts"})

    def test_12_source_roster_mismatch_before_official_market_claim(self):
        with self.assertRaisesRegex(ValueError,"CANNOT_CLAIM_758"):
            sh.run_shared(self.db,DAY,("AAUSDT",),
                          market_coverage_label="FULL_758_OFFICIAL_VERIFIED")


if __name__=="__main__":
    unittest.main()
