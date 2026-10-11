"""Stage26 168h continuity, 10 actual official-day source identity and no-lookahead."""
import sys
import unittest
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal as D
from pathlib import Path
from unittest.mock import patch

scripts=Path(__file__).parents[1]/"scripts"
if str(scripts) not in sys.path:sys.path.insert(0,str(scripts))
import monster_v4_stage26_continuous168h as m

def synthetic_minutes(day):
    anchor=m.replay.parse_ms(day.isoformat()+"T06:00:00Z")
    base=anchor-24*3600_000
    rows=[]
    for i in range(216*60):
        ts=base+i*60_000
        close=D("1")
        high=D("1.1")
        if i==1440+120*60:
            high=D("2.1")
        rows.append((ts,close,high,D(".9"),close,D("1000"),4))
    return rows

class Tests(unittest.TestCase):
    def test_six_old_dates_and_unchanged_production_blobs(self):
        cfg=m.frozen()
        self.assertEqual(len(cfg["frozen_dates_utc"]),6)
        self.assertEqual(cfg["frozen_universe"]["all_758_attempted_each_date"],True)
    def test_strict_168h_1m_cross_within_observation_not_future_exit(self):
        day=date(2026,8,4)
        bars=synthetic_minutes(day)
        at=m.first_real_1m_cross(day,bars,"1",2)
        expected=m.replay.parse_ms("2026-08-04T06:00:00Z")+120*3600_000
        self.assertEqual(at,expected)
        self.assertIsNone(m.first_real_1m_cross(day,bars,"1",5))
        bars[1440+120*60]=(bars[1440+120*60][0],D("1"),D("1.5"),D("1"),D("1"),D("1"),1)
        bars[1440+168*60]=(bars[1440+168*60][0],D("1"),D("4"),D("1"),D("1"),D("1"),1)
        self.assertIsNone(m.first_real_1m_cross(day,bars,"1",2))
    def test_monthly_GT_is_never_skipped_as_negative_watch(self):
        result=m.evaluate_one({"symbol":"XUSDT",
             "hourly":{"status":"MONTH_ARCHIVE_MISSING_404"}},
             date(2025,11,4),
             minute_source=lambda *a: (_ for _ in ()).throw(AssertionError("must skip")))
        self.assertEqual(result["status"],"CENSORED_GT_NOT_COMPLETE_168H")
    def test_source_day_404_is_not_no_watch(self):
        def gone(*a):
            raise ValueError("SOURCE_NOT_HISTORICALLY_AVAILABLE_HTTP_404")
        r=m.evaluate_one({"symbol":"XUSDT",
            "hourly":{"status":"VERIFIED_COMPLETE_168H"}},
             date(2025,11,4),minute_source=gone)
        self.assertEqual(r["status"],"CENSORED_MISSING_MINUTE_ARCHIVE")
    def test_source_ten_publisher_SHA_continuity_mandatory(self):
        day=date(2025,11,4)
        def download(symbol,day):
            day_start=int(datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()*1000)
            bars=[(day_start+i*60_000,D("1"),D("1"),D("1"),D("1"),D("10"),1)
                  for i in range(1440)]
            return bars,{"sha256":"a"*64,"verified_published_sha256":True}
        bars,proof=m.read_complete_216h("TESTUSDT",day,download=download)
        self.assertEqual(len(proof),10)
        self.assertEqual(len(bars),216*60)
        self.assertEqual(bars[0][0],m.replay.parse_ms("2025-11-03T06:00:00Z"))
        self.assertEqual(bars[-1][0],m.replay.parse_ms("2025-11-12T05:59:00Z"))
    def test_bad_source_sha_rejected(self):
        day=date(2025,11,4)
        def downloader(sym,d):
            return [(0,)]*1440,{"sha256":"short","verified_published_sha256":False}
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_PUBLISHER_SHA"):
            m.read_complete_216h("TESTUSDT",day,download=downloader)
    def test_genuine_future_label_not_used_as_scanner_parameter(self):
        day=date(2026,8,4)
        bars=synthetic_minutes(day)
        called={}
        def scanner(symbol,d,rows):
            called["args"]=(symbol,d,len(rows))
            return {"watch_count":0,"watch_utcs":[],"setups":0,"polls":3360,
                    "invalidations":0,"zero_trade_minute_polls":0,
                    "trade_proxies":[]}
        r=m.evaluate_one({"symbol":"TESTUSDT","hourly":{
            "status":"VERIFIED_COMPLETE_168H","baseline_1h_open":"1",
            "maximum_high_multiple":"2.1",
            "gross_high_ge_2x":True,"gross_high_ge_5x":False,
            "gross_high_ge_10x":False}},
            day,minute_source=lambda s,d:(bars,[{"date":"2026-08-04","sha256":"f"*64}]*10),
            engine=scanner)
        self.assertEqual(r["status"],"COMPLETE_168H_CONTINUOUS_V4")
        self.assertEqual(called["args"],("TESTUSDT",day,216*60))
        self.assertEqual(r["labels"]["2x"]["classification"],"NO_WATCH_IN_CONTINUOUS_168H")
    def test_poll_continuity_no_sqlite_reinitialization_no_hourly_selection(self):
        day=date(2025,11,4);bars=synthetic_minutes(day)
        store=[]
        class FakeDB:
            def __init__(self):self.events=[]
            def execute(self,sql,*args):
                if "SELECT event_id" in sql:return self.events
                if "SELECT status,COUNT" in sql:return []
                raise ValueError(sql)
            def close(self):pass
        def store_open(path):
            db=FakeDB();store.append(db);return db
        times=[]
        def observe(db,venue,ts,rows):
            times.append(ts)
            if len(times) in (5,3350):
                db.events.append({"event_id":str(len(times)),
                    "event_type":"WATCH_EARLY","observed_ms":ts,"payload":"{}"})
        with patch.object(m.live,"open_store",store_open),\
             patch.object(m.live,"observe_snapshot",observe),\
             patch.object(m.live,"process_queue",lambda db,t,fetch:None):
            r=m.scan_continuous("TESTUSDT",day,bars)
        self.assertEqual(len(store),1)
        self.assertEqual(len(times),3360)
        self.assertEqual(times[0],m.replay.parse_ms("2025-11-04T06:03:00Z"))
        self.assertEqual(times[-1],m.replay.parse_ms("2025-11-11T05:54:00Z"))
        self.assertEqual(r["watch_count"],2)
        self.assertEqual(r["continuous_sqlite_reset_count"],0)
        self.assertTrue(r["polls"]>3000)
if __name__=="__main__":
    unittest.main()
