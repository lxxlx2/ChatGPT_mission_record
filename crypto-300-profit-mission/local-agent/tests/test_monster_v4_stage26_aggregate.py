"""Stage26 30/300U limited-capital and intact original-source accounting."""
import sys
import unittest
from datetime import datetime,timezone
from pathlib import Path

P=Path(__file__).parents[1]/"scripts"
if str(P) not in sys.path:sys.path.insert(0,str(P))
import monster_v4_stage26_aggregate as m

def event(symbol,watch,profit):
    return {"symbol":symbol,"date":"2025-11-04",
        "status":"COMPLETE_168H_CONTINUOUS_V4",
        "continuous":{"watch_count":1,"setups":0,"invalidations":0,"polls":3360,
            "zero_trade_minute_polls":0,
            "watch_utcs":[watch],
            "trade_proxies":[{"watch_utc":watch,
                "proxy_20bps":{"status":"PRICE_PROXY_ONLY","net_pct":profit},
                "proxy_100bps":{"status":"PRICE_PROXY_ONLY","net_pct":profit-1.6}}]},
        "labels":{"2x":{"gross_hourly_high_gt":False},
                  "5x":{"gross_hourly_high_gt":False},
                  "10x":{"gross_hourly_high_gt":False}}}

class AggregateTests(unittest.TestCase):
    def test_single_funding_slot_blocks_overlapping_signals(self):
        rows=[event("AAAUSDT","2025-11-04T12:00:00Z",-8),
              event("BBBUSDT","2025-11-04T12:05:00Z",50)]
        out=m.one_or_ten_slot(rows,1,"proxy_20bps")
        self.assertEqual(out["selected_by_signal_chronology"],1)
        self.assertEqual(out["skipped_due_to_portfolio_busy"],1)
        self.assertEqual(out["simulated_net_USDT"],-2.4)
    def test_ten_slots_allow_both_without_future_ranking(self):
        rows=[event("AAAUSDT","2025-11-04T12:00:00Z",-8),
              event("BBBUSDT","2025-11-04T12:05:00Z",50)]
        result=m.one_or_ten_slot(rows,10,"proxy_20bps")
        self.assertEqual(result["selected_by_signal_chronology"],2)
        self.assertEqual(result["simulated_net_USDT"],12.6)
    def test_same_second_ties_order_by_symbol_not_pnl(self):
        rows=[event("ZZZUSDT","2025-11-04T12:00:00Z",500),
              event("AAAUSDT","2025-11-04T12:00:00Z",-10)]
        r=m.one_or_ten_slot(rows,1,"proxy_20bps")
        self.assertEqual(r["simulated_net_USDT"],-3)
        self.assertEqual(r["selected_cases"][0]["symbol"],"AAAUSDT")
    def test_censored_position_reserves_full_day(self):
        p=event("AAAUSDT","2025-11-04T12:00:00Z",-5)
        p["continuous"]["trade_proxies"][0]["proxy_20bps"]={"status":"CENSORED_ZERO_VOLUME_EXIT"}
        q=event("BBBUSDT","2025-11-04T12:15:00Z",30)
        result=m.one_or_ten_slot([p,q],1,"proxy_20bps")
        self.assertEqual(result["skipped_due_to_portfolio_busy"],1)
        self.assertEqual(result["evaluable"],0)
        self.assertEqual(result["censored_held_24h"],1)
    def test_source_sha_verification_fails_closed(self):
        import tempfile,zipfile
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/"false.zip"
            with zipfile.ZipFile(file,"w") as z:z.writestr("fake","test")
            with self.assertRaisesRegex(ValueError,"ARTIFACT_ZIP_SHA_CHANGED"):
                m.load_zip(file,{"date":"2025-11-04","shard":0,"zip_sha256":"a"*64})
    def test_incomplete_six_dates_not_pooled_as_success(self):
        with self.assertRaisesRegex(ValueError,"ALL_SIX_DATES_36_SHARDS_REQUIRED"):
            m.summarize({},
              {"frozen_dates_utc":["2025-11-04","2025-12-04","2026-02-04",
                  "2026-04-04","2026-08-04","2026-09-04"]})
    def test_valid_trade_statistics_reject_nonfills(self):
        x=event("AAAUSDT","2025-11-04T12:00:00Z",3)
        y=event("BBBUSDT","2025-11-04T14:00:00Z",4)
        y["continuous"]["trade_proxies"][0]["proxy_20bps"]={"status":"CENSORED_ZERO_VOLUME_EXIT"}
        r=m.stats_for_arm([x,y],"proxy_20bps")
        self.assertEqual(r["evaluable"],1)
        self.assertEqual(r["wins"],1)
        self.assertEqual(r["missing_or_skipped"],1)

if __name__=="__main__":unittest.main()
