"""Synthetic publisher ZIPs exercise unchanged original D0/D1 input APIs.

This does NOT establish historical T0, original-live PIT, OOS G1 or profit.
"""
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile

import monster_v4_adr005_forward_verified_minute_tape as tape
import monster_v4_adr005_forward_spot_score_admission as admission
import monster_v4_adr005_forward_spot_t0_gate as t0
import monster_v4_stage166_spot511_official_1m_intake as publisher
import monster_v4_shadow as original
from monster_v4_d1_rbtc15_last5_research import evaluate_research_candidate


class ForwardSourceVerifiedTapeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.start="2026-11-02T00:00:00Z"
        self.asof="2026-11-09T00:00:00Z"
        self.start_ms=t0.frozen_window(self.start)//1000

    def day_file(self,symbol,day,*,changed=False):
        zip_path,checksum=publisher.daily_paths(self.root,symbol,day)
        zip_path.parent.mkdir(parents=True,exist_ok=True)
        begin=int(datetime.combine(day,datetime.min.time(),timezone.utc).timestamp())*1_000_000
        initial=Decimal(100) if symbol=="AAAUSDT" else Decimal(200)
        lines=[]
        for j in range(1440):
            val=(initial*Decimal("1.10") if changed and j>=1 else initial)
            ms=begin+j*60_000_000
            lines.append(f"{ms},{val},{val},{val},{val},1,{ms+59_999_999},1000,10,1,1,0\n")
        with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(f"{symbol}-1m-{day.isoformat()}.csv","".join(lines))
        checksum.write_text(f"{hashlib.sha256(zip_path.read_bytes()).hexdigest()}  {zip_path.name}\n")
        return zip_path,checksum

    def make_days(self,symbols=("AAAUSDT","BTCUSDT")):
        first=date(2026,11,1)
        for symbol in symbols:
            for i in range(8):
                self.day_file(symbol,first+timedelta(days=i),
                              changed=(symbol=="AAAUSDT" and i==1))

    def fake_score(self,with_btc=True):
        target={
            "symbol":"AAAUSDT","baseline_24h_source_verified":True,
            "candidate_own_observation_7d_source_verified":True,
            "technically_eligible_for_offline_rbtc_d1_source_replay":with_btc,
        }
        btc={
            "symbol":"BTCUSDT","baseline_24h_source_verified":True,
            "candidate_own_observation_7d_source_verified":True,
            "technically_eligible_for_offline_rbtc_d1_source_replay":False,
        }
        return {"schema":admission.SCHEMA,"window_start_utc":self.start,
                "original_market_census_venue":"BINANCE_SPOT",
                "replay_engine_executed":False,
                "metrics_from_future_labels_computed":False,
                "symbols":[target,btc] if with_btc else [target]}

    def test_proper_complete_original_1m_context_and_six_closed5(self):
        self.make_days()
        own,btc=tape.from_score_admission(self.fake_score(),self.root,"AAAUSDT",
                                           asof_utc=self.asof)
        self.assertIsNotNone(btc)
        first=own.original_d0_context(self.start_ms)
        second=own.original_d0_context(self.start_ms+180_000)
        self.assertEqual(first["lastPrice"],"100")
        self.assertEqual(second["lastPrice"],"110.00")
        self.assertEqual(first["quoteVolume"],"1440000")
        bars=own.six_closed_5m(self.start_ms+180_000)
        benchmark=btc.six_closed_5m(self.start_ms+180_000)
        self.assertEqual(len(bars),6)
        self.assertEqual(len(benchmark),6)
        self.assertEqual(bars[-1][0]+tape.FIVE_MS-1,bars[-1][6])
        self.assertLess(bars[-1][6],self.start_ms+180_000)
        self.assertEqual([x[0] for x in bars],[x[0] for x in benchmark])
        self.assertEqual(own.original_d1_fetch("spot","AAAUSDT",
                         self.start_ms+180_000),bars)
        with self.assertRaisesRegex(ValueError,"IDENTITY_MISMATCH"):
            own.original_d1_fetch("futures","AAAUSDT",self.start_ms+180_000)
        with self.assertRaisesRegex(ValueError,"IDENTITY_MISMATCH"):
            own.original_d1_fetch("spot","BTCUSDT",self.start_ms+180_000)
        self.assertFalse(own.original_tick_quote_or_listing_PIT_proven)

    def test_actual_original_d0_and_preregistered_d1_cores_on_synthetic_prices(self):
        self.make_days()
        own,btc=tape.from_score_admission(self.fake_score(),self.root,"AAAUSDT",
                                           asof_utc=self.asof)
        db=sqlite3.connect(":memory:")
        db.row_factory=sqlite3.Row
        db.executescript(original.SCHEMA)
        try:
            first=self.start_ms
            second=first+180_000
            observation1=[own.original_d0_context(first),btc.original_d0_context(first)]
            observation2=[own.original_d0_context(second),btc.original_d0_context(second)]
            self.assertEqual(original.observe_snapshot(db,"spot",first,observation1)["watch_new"],0)
            self.assertEqual(original.observe_snapshot(db,"spot",second,observation2)["watch_new"],1)
            watch=dict(db.execute("SELECT event_id,symbol,observed_ms FROM events "
                                  "WHERE event_type='WATCH_EARLY'").fetchone())
            self.assertEqual(watch["symbol"],"AAAUSDT")
            self.assertEqual(watch["observed_ms"],second)
            now=first+6*60_000
            coinbars=own.six_closed_5m(now)
            btcbars=btc.six_closed_5m(now)
            features=original.evaluate_closed_5m(coinbars,now)
            self.assertEqual(features["closed_5m"],6)
            result=evaluate_research_candidate(
                symbol="AAAUSDT",observed_ms=now,watch_ms=second,
                deadline_ms=second+900_000,coin_closed5=coinbars,
                btc_closed5=btcbars)
            self.assertIn(result["state"],("RESEARCH_NO_SETUP_YET","RESEARCH_SETUP"))
            self.assertEqual(result["classification"],"OFFLINE_RESEARCH_ONLY_NOT_BUY")
        finally:
            db.close()

    def test_missing_btc_can_load_d0_alone_but_not_claim_rbtc_d1_ready(self):
        self.make_days(("AAAUSDT",))
        own,btc=tape.from_score_admission(self.fake_score(with_btc=False),
                                          self.root,"AAAUSDT",asof_utc=self.asof)
        self.assertIsNone(btc)
        self.assertEqual(own.original_d0_context(self.start_ms)["lastPrice"],"100")

    def test_no_issuer_file_for_one_day_rejected_even_when_synthetic_report_claims_ready(self):
        self.make_days()
        archive,checksum=publisher.daily_paths(self.root,"BTCUSDT",date(2026,11,4))
        archive.unlink()
        with self.assertRaisesRegex(ValueError,"MISSING_OR_SYMLINK_ISSUER_SOURCE"):
            tape.from_score_admission(self.fake_score(),self.root,"AAAUSDT",
                                      asof_utc=self.asof)

    def test_corrupted_publisher_zip_is_rejected_before_input_materialization(self):
        self.make_days()
        archive,checksum=publisher.daily_paths(self.root,"AAAUSDT",date(2026,11,2))
        archive.write_bytes(archive.read_bytes()+b"tamper")
        with self.assertRaisesRegex(ValueError,"STAGE166_OFFICIAL_ZIP_SHA256_MISMATCH"):
            tape.from_score_admission(self.fake_score(),self.root,"AAAUSDT",
                                      asof_utc=self.asof)

    def test_last_observation_day_unclosed_by_one_microsecond_is_rejected(self):
        self.make_days()
        with self.assertRaisesRegex(ValueError,"UNCLOSED_ISSUER_DAY"):
            tape.from_score_admission(self.fake_score(),self.root,"AAAUSDT",
                asof_utc="2026-11-08T23:59:59.999999Z")

    def test_future_or_offgrid_poll_fails_closed(self):
        self.make_days()
        own,btc=tape.from_score_admission(self.fake_score(),self.root,"AAAUSDT",
                                           asof_utc=self.asof)
        for tick in (self.start_ms-180_000,
                     self.start_ms+7*86400_000,self.start_ms+60_000,
                     self.start_ms+1):
            with self.assertRaisesRegex(ValueError,"TICK_OUTSIDE_FROZEN_UTC3M_WINDOW"):
                own.original_d0_context(tick)
            with self.assertRaisesRegex(ValueError,"TICK_OUTSIDE_FROZEN_UTC3M_WINDOW"):
                own.six_closed_5m(tick)

    def test_no_original_t0_or_untrusted_report_cannot_autogenerate_live_events(self):
        with self.assertRaisesRegex(ValueError,"SCORE_SOURCE_ADMISSION_REQUIRED"):
            tape.from_score_admission({},"/tmp","AAAUSDT",asof_utc=self.asof)
        with self.assertRaisesRegex(ValueError,"NON_BTC_TARGET"):
            tape.from_score_admission(self.fake_score(),self.root,"BTCUSDT",
                                      asof_utc=self.asof)


if __name__=="__main__":
    unittest.main()
