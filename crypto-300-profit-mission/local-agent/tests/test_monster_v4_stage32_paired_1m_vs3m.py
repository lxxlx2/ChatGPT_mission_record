"""Stage32 two-arm unchanged production V4 1m vs3m exact source/cadence guards."""
import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

SCRIPTS=Path(__file__).parents[1]/"scripts"
if str(SCRIPTS) not in sys.path:sys.path.insert(0,str(SCRIPTS))
import monster_v4_stage32_paired_1m_vs3m as m

def sample_bars():
    day=date(2025,3,19)
    zero=m.replay.parse_ms(day.isoformat()+"T06:00:00Z")-24*3600000
    bars=[]
    for i in range(1500):
        v=Decimal("1.06") if i>=1446 else Decimal("1")
        bars.append([zero+i*60000,v,v,v,v,Decimal("200"),1])
    return bars

class Stage32Tests(unittest.TestCase):
    def test_six_new_fixed_dates_and_original_v4_blob_sha(self):
        p=m.frozen()
        self.assertEqual(tuple(p["frozen_dates_utc"]),m.NEW_DAYS)
        self.assertEqual(p["complete_original_spot_universe"],758)
    def test_missing_date_rejected_before_public_download(self):
        with self.assertRaisesRegex(ValueError,"NOT_FROZEN_DAY"):
            m.run("2025-11-19",0,Path("/tmp/absent.zip"))
    def test_anonymous_monthly_fail_closed_on_real_source_error(self):
        with patch.object(m.gt,"label",return_value={"symbol":"TUSDT","status":"SOURCE_NETWORK_FAILED"}):
            with self.assertRaisesRegex(RuntimeError,"HOURLY_NETWORK_OR_INTEGRITY_FAILURE"):
                m.compare_one("TUSDT",date(2025,3,19))
    def test_hourly_missing_not_no_WATCH(self):
        with patch.object(m.gt,"label",return_value={"symbol":"TUSDT","status":"MONTH_ARCHIVE_MISSING_404"}):
            o=m.compare_one("TUSDT",date(2025,3,19))
        self.assertEqual(o["status"],"CENSORED_GT_NOT_COMPLETE_168H")
    def test_new_one_minute_poll_is_true_60s_and_original_only_3min(self):
        bars=sample_bars()
        with patch.object(m.original,"EXPECTED_MINUTES",1500),patch.object(m.original,"ACTIVE_MINUTES",60):
            fast=m.scan_one_minute("TESTUSDT",date(2025,3,19),bars)
            slow=m.original.scan_continuous("TESTUSDT",date(2025,3,19),bars)
        self.assertEqual((fast["polls"],slow["polls"]),(60,20))
        self.assertGreater(fast["watch_count"],0)
        self.assertGreater(slow["watch_count"],0)
        self.assertLess(m.replay.parse_ms(fast["watch_utcs"][0]),m.replay.parse_ms(slow["watch_utcs"][0]))
        self.assertEqual((fast["continuous_sqlite_reset_count"],slow["continuous_sqlite_reset_count"]),(0,0))
    def test_GT_first_cross_class_never_uses_future_High_in_D0(self):
        day=date(2025,3,19)
        watch=day.isoformat()+"T06:07:00Z"
        row={"gross_high_ge_2x":True,"gross_high_ge_5x":False,
             "gross_high_ge_10x":False,"baseline_1h_open":"0.5"}
        bars=sample_bars()
        arm={"watch_utcs":[watch]}
        with patch.object(m.original,"ACTIVE_MINUTES",60):
            result=m.first_cross_class(day,bars,row,arm)
        self.assertEqual(result["2x"]["classification"],"EARLY")
        self.assertFalse(result["5x"]["is_gt_positive"])
    def test_source_consistency_requires_one_hour_month_sha(self):
        bad={"symbol":"TUSDT","status":"VERIFIED_COMPLETE_168H","archive_sha256":""}
        with patch.object(m.gt,"label",return_value=bad):
            with self.assertRaisesRegex(RuntimeError,"UNVERIFIED_MONTHLY"):
                m.compare_one("TUSDT",date(2025,3,19))
if __name__=="__main__":unittest.main()
