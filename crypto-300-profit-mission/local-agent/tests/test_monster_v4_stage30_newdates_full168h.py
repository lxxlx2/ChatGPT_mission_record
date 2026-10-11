"""Stage30 new full-market holdout immutable UTC calendar/source and no GT lookahead."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
S=Path(__file__).parents[1]/"scripts"
if str(S) not in sys.path:sys.path.insert(0,str(S))
import monster_v4_stage30_newdates_full168h as m

class NewDateTests(unittest.TestCase):
    def test_frozen_six_new_dates_and_original_function_blobs(self):
        f=m.frozen()
        self.assertEqual(f["new_dates_UTC"],["2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19"])
        self.assertEqual(f["cohort_source"]["original_stage24_known_758_universe_artifact_id"],11700651924)
        self.assertEqual(f["primary_success_gates"]["burst_distinct_market_poll_episodes_min_for_claim"],6)
    def test_new_gt_missing_not_negative(self):
        with patch.object(m.gt,"label",return_value={"symbol":"TUSDT","status":"MONTH_ARCHIVE_MISSING_404"}):
            v=m.eval_one("TUSDT",m.date(2025,1,19))
        self.assertEqual(v["status"],"CENSORED_GT_NOT_COMPLETE_168H")
        self.assertTrue(v["truth_missing_is_not_no_watch"])
    def test_source_download_failure_aborts_not_false_negative(self):
        with patch.object(m.gt,"label",return_value={"symbol":"TUSDT","status":"SOURCE_NETWORK_FAILED_URLError"}):
            with self.assertRaisesRegex(RuntimeError,"OFFICIAL_HOURLY_NETWORK_OR_INTEGRITY_FAILURE"):
                m.eval_one("TUSDT",m.date(2025,1,19))
    def test_official_gt_matches_original_stage26_scanner_without_future_labels(self):
        orig={"symbol":"TUSDT","status":"VERIFIED_COMPLETE_168H","baseline_1h_open":"1",
              "maximum_high_multiple":"2.1",
              "gross_high_ge_2x":True,"gross_high_ge_5x":False,"gross_high_ge_10x":False}
        recorded={}
        def record(item,day):
            recorded["hourly"]=item["hourly"]
            return {"symbol":item["symbol"],"status":"COMPLETE_168H_CONTINUOUS_V4","continuous":{
                "watch_count":1,"setups":0,"polls":3360,"trade_proxies":[]},"labels":{
                "2x":{"gross_hourly_high_gt":True,"classification":"WATCH_BEFORE_OR_AT_REAL_FIRST_1M_CROSS"},
                "5x":{"gross_hourly_high_gt":False},"10x":{"gross_hourly_high_gt":False}}}
        with patch.object(m.gt,"label",return_value=orig),patch.object(m.runner,"evaluate_one",record):
            res=m.eval_one("TUSDT",m.date(2025,1,19))
        self.assertEqual(recorded["hourly"],orig)
        self.assertEqual(res["symbol"],"TUSDT")
    def test_all_source_statuses_censorship_in_summary(self):
        x={"symbol":"TUSDT","status":"CENSORED_GT_NOT_COMPLETE_168H"}
        y={"symbol":"XUSDT","status":"COMPLETE_168H_CONTINUOUS_V4",
           "labels":{str(k)+"x":{"gross_hourly_high_gt":False} for k in (2,5,10)},
           "continuous":{"watch_count":0,"setups":0,"polls":3360,"trade_proxies":[]}}
        d=m.summarize([x,y])
        self.assertEqual(d["joint_verifiable"],1)
        self.assertEqual(d["attempted"],2)
        self.assertEqual(d["source_status_counts"]["CENSORED_GT_NOT_COMPLETE_168H"],1)
    def test_source_manifest_universe_size_mismatch_rejected(self):
        with patch.object(m,"original_universe",return_value=["AUSDT"]*758):
            with self.assertRaisesRegex(ValueError,"SOURCE_SHARD_SIZE_MISMATCH"):
                m.replay_shard("2025-01-19",0,Path("/tmp/not_used.zip"))
    def test_unknown_date_aborts_before_price_reads(self):
        with self.assertRaisesRegex(ValueError,"UNREGISTERED_DAY"):
            m.replay_shard("2025-02-19",0,Path("/tmp/not_used.zip"))
if __name__=="__main__":unittest.main()
