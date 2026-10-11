"""Stage24: historical opportunity labels are not V4 inputs or full-7d WATCH."""
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

scripts=Path(__file__).parents[1]/"scripts"
if str(scripts) not in sys.path:
    sys.path.insert(0,str(scripts))
import monster_v4_stage24_full_market_7d_watch_audit as m

def minute(first="2025-11-04T08:00:00Z",n=1):
    return {"status":"VERIFIED_COMPLETE_60H_1M","watch_count":n,
         "first_watch_utc":first if n else None,
         "price_proxies_20bps":[],"all_watch_utc":[first] if n else [],
         "d1_count":0,"polls":239,"zero_traded_minutes":0}
def hour(two=True,index=3):
    return {"status":"VERIFIED_COMPLETE_168H","gross_high_ge_2x":two,
      "gross_high_ge_5x":False,"gross_high_ge_10x":False,
      "gross_close_ge_2x":False,"gross_close_ge_5x":False,
      "gross_close_ge_10x":False,
      "first_high_2x_hour_index":index,
      "maximum_high_multiple":"2.5" if two else "1.2"}

class AuditTests(unittest.TestCase):
    def test_original_unchanged_code_hashes_and_prereg_dates(self):
        cfg=m.frozen()
        self.assertEqual(len(cfg["frozen_new_dates"]),6)
        self.assertEqual(cfg["historical_universe"]["symbols"],758)
    def test_unregistered_calendar_rejected(self):
        with self.assertRaisesRegex(ValueError,"NON_PREREGISTERED_DATE"):
            m.run("2026-10-11",symbols_get=lambda c:([],{}))
    def test_gt_2x_label_not_present_in_v4_signal_features(self):
        day=date(2025,11,4)
        seen={}
        def h(s,d):
            seen["gt"]=True
            return hour(True)
        def l(s,d):
            seen["minute"]=True
            return minute()
        x=m.run_symbol("ABCUSDT",day,hourly_label=h,minute_loader=l)
        self.assertEqual(set(seen),{"gt","minute"})
        self.assertIn("watch_vs_2x_5x_10x",x)
        self.assertNotIn("hourly",x["minute"])
    def test_early_is_strictly_before_hour_start(self):
        day=date(2025,11,4)
        self.assertEqual(m.classification(day,hour(index=3),minute("2025-11-04T08:59:00Z"),2),
          "WATCH_BEFORE_FIRST_CROSSING_HOUR")
        self.assertEqual(m.classification(day,hour(index=3),minute("2025-11-04T09:00:00Z"),2),
          "WATCH_INSIDE_CROSSING_HOUR_UNORDERED")
        self.assertEqual(m.classification(day,hour(index=3),minute("2025-11-04T10:01:00Z"),2),
          "WATCH_AFTER_FIRST_CROSSING_HOUR")
        self.assertEqual(m.classification(day,hour(index=3),minute(None,0),2),
          "NO_WATCH_IN_FIXED_12H")
    def test_censored_hourly_or_minute_never_called_no_watch(self):
        day=date(2025,11,4)
        self.assertEqual(m.classification(day,{"status":"CENSORED_7D_HOURLY_GAP"},
                     minute(None,0),2),"GT_NOT_VERIFIED")
        self.assertEqual(m.classification(day,hour(),{"status":"SOURCE_MISSING_DAY_ARCHIVE"},2),
          "WATCH_SOURCE_UNVERIFIED")
        self.assertEqual(m.classification(day,hour(False),minute(None,0),2),
          "NO_FUTURE_2X_GROSS_HIGH")
    def test_full_universe_missing_is_not_true_negative(self):
        day=date(2025,11,4)
        valid={"symbol":"A","day":day.isoformat(),"hourly":hour(),
               "minute":minute("2025-11-04T07:00:00Z"),
               "watch_vs_2x_5x_10x":{"2x":"WATCH_BEFORE_FIRST_CROSSING_HOUR"}}
        invalid={"symbol":"B","day":day.isoformat(),"hourly":{"status":"MONTH_ARCHIVE_MISSING_404"},
                 "minute":{"status":"SOURCE_MISSING_DAY_ARCHIVE"},
                 "watch_vs_2x_5x_10x":{"2x":"GT_NOT_VERIFIED"}}
        summary=m.summarize([valid,invalid])
        self.assertEqual(summary["joint_verified_168h_and_60h"],1)
        self.assertEqual(summary["hourly_complete_168h"],1)
        self.assertEqual(summary["gross_price_label_results"]["2x"]["unambiguous_early_watch_fixed12h"],1)
        self.assertEqual(summary["v4_watch_symbol_dates_joint"],1)
    def test_original_replayer_drift_fails_closed(self):
        with patch.object(m.replay,"__file__",__file__):
            with self.assertRaisesRegex(ValueError,"STAGE24_LOCKED_ORIGINAL_SOURCE_CHANGED"):
                m.frozen()
    def test_frozen_whole_universe_not_cherry_picked(self):
        day="2025-11-04"
        def simple(symbol,date_value):
            h=hour(False);mm=minute(None,0)
            return {"symbol":symbol,"day":day,"hourly":h,"minute":mm,
                    "watch_vs_2x_5x_10x":{k:"NO_FUTURE_"+k.upper()+"_GROSS_HIGH"
                                          for k in ("2x","5x","10x")}}
        val=m.run(day,symbols_get=lambda _cfg:([f"X{i}USDT" for i in range(758)],
                             {"archive_only_sha256":"0c2604d838fc3d7c28d0e8819fde1bb42deb6fb22360182a49c1b82bb6d25348"}),
                     evaluator=simple,workers=2)
        self.assertEqual(val["summary"]["attempted"],758)
        self.assertEqual(val["summary"]["joint_verified_168h_and_60h"],758)
        self.assertEqual(val["summary"]["gross_price_label_results"]["2x"]["verified_168h_positive_joint_source"],0)

if __name__=="__main__":
    unittest.main()
