"""Stage24 artifact integrity and full-universe fair denominator reaggregation."""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPTS=Path(__file__).parents[1]/"scripts"
if str(SCRIPTS) not in sys.path:sys.path.insert(0,str(SCRIPTS))
import monster_v4_stage24_aggregate as m

DAYS=("2025-11-04","2025-12-04","2026-02-04","2026-04-04","2026-08-04","2026-09-04")

def sample(symbol,day,positive=False,watch=False):
    status="VERIFIED_COMPLETE_168H"
    hour={"status":status,
         "archive_sha256":"a"*64,"maximum_high_multiple":"2.2" if positive else "1.1",
         "gross_high_ge_2x":positive,"gross_high_ge_5x":False,"gross_high_ge_10x":False,
         "gross_close_ge_2x":False,"gross_close_ge_5x":False,
         "gross_close_ge_10x":False}
    if positive:hour["first_high_2x_hour_index"]=20
    minute={"status":"VERIFIED_COMPLETE_60H_1M",
      "watch_count":1 if watch else 0,"first_watch_utc":day+"T09:00:00Z" if watch else None,
      "price_proxies_20bps":[],"d1_count":0,
      "archive_sha256":[{"sha256":"f"*64}]*3}
    group={"2x":"WATCH_BEFORE_FIRST_CROSSING_HOUR" if positive and watch else
                  "NO_WATCH_IN_FIXED_12H" if positive else "NO_FUTURE_2X_GROSS_HIGH",
           "5x":"NO_FUTURE_5X_GROSS_HIGH","10x":"NO_FUTURE_10X_GROSS_HIGH"}
    return {"symbol":symbol,"day":day,"hourly":hour,"minute":minute,
            "watch_vs_2x_5x_10x":group}

def artificial_report(day,i):
    items=[sample(f"X{j}USDT",day,positive=(i==0 and j==0),watch=(i==0 and j==0))
           for j in range(758)]
    return {"cases":items,"summary":{
         "hourly_status":{"VERIFIED_COMPLETE_168H":758},
         "minute_status":{"VERIFIED_COMPLETE_60H_1M":758},
         "hourly_complete_168h":758,"minute_complete_60h":758,
         "joint_verified_168h_and_60h":758,
         "v4_watch_episodes_all_valid_minute":int(i==0),
         "gross_price_label_results":{
           "2x":{"unambiguous_early_watch_fixed12h":int(i==0),
                  "verified_168h_positive_joint_source":int(i==0)},
           "5x":{"unambiguous_early_watch_fixed12h":0,
                  "verified_168h_positive_joint_source":0},
           "10x":{"unambiguous_early_watch_fixed12h":0,
                  "verified_168h_positive_joint_source":0}}}}

class Stage24Aggregation(unittest.TestCase):
    def test_six_date_equal_denominator_one_real_event_early(self):
        docs={day:artificial_report(day,i) for i,day in enumerate(DAYS)}
        result=m.rebuild(docs,{"frozen_new_dates":list(DAYS)})
        self.assertEqual(result["attempted_symbol_date"],4548)
        self.assertEqual(result["verified_joint_168h_gt_60h_watch"],4548)
        self.assertEqual(result["gross_high_labels"]["2x"]["gross_high_positive_joint"],1)
        self.assertEqual(result["gross_high_labels"]["2x"]["strict_early_count"],1)
        self.assertEqual(result["joint_watch_symbol_dates"],1)
    def test_case_ambiguous_hour_cannot_be_counted_early(self):
        x=sample("AUSDT",DAYS[0],positive=True,watch=True)
        x["watch_vs_2x_5x_10x"]["2x"]="WATCH_INSIDE_CROSSING_HOUR_UNORDERED"
        value=m.count_by_event([x],2)
        self.assertEqual(value["strict_early_count"],0)
        self.assertEqual(value["timing_classes"]["WATCH_INSIDE_CROSSING_HOUR_UNORDERED"],1)
    def test_missing_hour_source_cannot_be_negative_gt(self):
        x=sample("AUSDT",DAYS[0],positive=True,watch=True)
        x["hourly"]={"status":"MONTH_ARCHIVE_MISSING_404"}
        result=m.count_by_event([x],2)
        self.assertEqual(result["gross_high_positive_all_GT"],0)
        self.assertEqual(result["verified_168h_GT"],0)
    def test_missing_date_fail_closed(self):
        docs={day:artificial_report(day,i) for i,day in enumerate(DAYS[:5])}
        with self.assertRaisesRegex(ValueError,"MISSING_OR_EXTRA_DATES"):
            m.rebuild(docs,{"frozen_new_dates":list(DAYS)})
    def test_bad_original_zip_sha_is_blocking(self):
        with tempfile.TemporaryDirectory() as t:
            z=Path(t)/"sample.zip"
            with zipfile.ZipFile(z,"w") as f:f.writestr("something","untrusted")
            with self.assertRaisesRegex(ValueError,"STAGE24_ZIP_SHA256_MISMATCH"):
                m.open_artifact(z,{"date":DAYS[0],"zip_sha256":"0"*64})
if __name__=="__main__":
    unittest.main()
