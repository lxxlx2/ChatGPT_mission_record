"""Stage29 no-parameter optimization: ensure all burst/watch outcomes are preserved."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]/"scripts"
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import monster_v4_stage29_watch_burst_price_research as m

def coin(sym,watch="2026-02-06T00:36:00Z",ret=12,censored=False,overlap=False):
    p={"status":"SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED"} if overlap else (
       {"status":"CENSORED_ZERO_VOLUME_EXIT"} if censored else
       {"status":"PRICE_PROXY_ONLY","net_pct":ret})
    p100=None if overlap else (
       {"status":"CENSORED_ZERO_VOLUME_EXIT"} if censored else
       {"status":"PRICE_PROXY_ONLY","net_pct":ret-1.5})
    return {"date":"2026-02-04","symbol":sym,
      "status":"COMPLETE_168H_CONTINUOUS_V4",
      "continuous":{"watch_utcs":[watch],"watch_count":1,
          "trade_proxies":[{"watch_utc":watch,"proxy_20bps":p,"proxy_100bps":p100}]},
      "labels":{"2x":{"gross_hourly_high_gt":False}}}

class Tests(unittest.TestCase):
    def test_frozen_source_and_no_BUY_rule_selection(self):
        d=m.contract()
        self.assertEqual(d["watch_events"],1132)
        self.assertTrue(d["no_model_threshold_updates"])
    def test_one_watch_is_isolated(self):
        r=m.make_event_cases([coin("XUSDT")])
        self.assertEqual(r[0]["bucket"],"ISOLATED_1")
        self.assertEqual(m.arm_stats(r,20)["wins"],1)
    def test_two_seven_eight_same_poll_group_bins(self):
        for n,b in [(2,"LOCAL_2_TO_7"),(7,"LOCAL_2_TO_7"),(8,"BURST_8PLUS"),(98,"BURST_8PLUS")]:
            rows=m.make_event_cases([coin(f"X{i}USDT") for i in range(n)])
            self.assertTrue(all(r["bucket"]==b for r in rows))
    def test_censored_and_overlapping_are_never_tradable_profit(self):
        rows=m.make_event_cases([coin("AUSDT",ret=-8),
             coin("BUSDT",censored=True),coin("CUSDT",overlap=True)])
        arm=m.arm_stats(rows,20)
        self.assertEqual(arm["watch_count"],3)
        self.assertEqual(arm["proxy_evaluable"],1)
        self.assertEqual(arm["losses"],1)
        self.assertEqual(arm["source_censored_excluding_overlap"],1)
        self.assertEqual(arm["same_symbol_24h_overlap_skip"],1)
    def test_false_alignment_does_not_infer_future_2x(self):
        invalid=coin("XUSDT")
        invalid["continuous"]["trade_proxies"][0]["watch_utc"]="2026-02-06T00:39:00Z"
        with self.assertRaisesRegex(ValueError,"MISMATCHED_TRADE_WATCH"):
            m.make_event_cases([invalid])
    def test_duplicates_in_same_cohort_fail(self):
        x=coin("XUSDT")
        with self.assertRaisesRegex(ValueError,"DUPLICATE_SOURCE_WATCH"):
            m.make_event_cases([x,x])
    def test_bps_cost_runs_on_exact_same_trade_denominator(self):
        x=m.make_event_cases([coin("XUSDT",ret=12)])
        a=m.arm_stats(x,20);b=m.arm_stats(x,100)
        self.assertEqual((a["proxy_evaluable"],b["proxy_evaluable"]),(1,1))
        self.assertGreater(a["median_net_pct"],b["median_net_pct"])

if __name__=="__main__":unittest.main()
