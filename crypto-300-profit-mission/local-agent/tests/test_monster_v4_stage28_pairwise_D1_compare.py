"""Stage28 all-original per-symbol D1 exact timestamp reconciliation."""
import sys
import unittest
from pathlib import Path
p=Path(__file__).parents[1]/"scripts"
if str(p) not in sys.path:sys.path.insert(0,str(p))
import monster_v4_stage28_pairwise_D1_compare as m
import monster_v4_stage28_aggregate as shared

def mock_six_days():
    when="2025-11-04T12:00:00Z"
    old=[]
    for i in range(826):
        old.append({"date":"2025-11-04","symbol":f"X{i:04d}USDT",
          "status":"COMPLETE_168H_CONTINUOUS_V4",
          "continuous":{"setup_utcs":[when],
            "watch_utcs":["2025-11-04T11:00:00Z"],
            "trade_proxies":[{"watch_utc":"2025-11-04T11:00:00Z",
              "proxy_20bps":{"status":"PRICE_PROXY_ONLY","net_pct":0.2}}]}})
    new={day:{"setups":[],"queue_final":[]} for day in shared.DATES}
    for i in range(823):
        new["2025-11-04"]["setups"].append({"symbol":f"X{i:04d}USDT","utc":when})
    for i in range(5):
        new["2025-11-04"]["setups"].append({"symbol":f"NEW{i:04d}USDT","utc":when})
    return old,new

class Pairwise(unittest.TestCase):
    def test_exact_826_828_identity_823_matched_three_lost_five_new(self):
        old,new=mock_six_days()
        r=m.compare(old,new)
        self.assertEqual((r["old_individual_D1_count"],r["new_real_shared_D1_count"]),(826,828))
        self.assertEqual(r["exact_symbol_timestamp_intersection"],823)
        self.assertEqual((r["original_only_count"],r["shared_only_count"]),(3,5))
        self.assertEqual(r["original_only_events"][0]["symbol"],"X0823USDT")
    def test_same_symbol_later_d1_remains_mismatch_and_explicit(self):
        old,new=mock_six_days()
        new["2025-11-04"]["setups"][0]["utc"]="2025-11-04T12:09:00Z"
        r=m.compare(old,new)
        self.assertEqual(r["exact_symbol_timestamp_intersection"],822)
        self.assertEqual(r["original_only_count"],4)
        self.assertEqual(r["shared_only_count"],6)
        first=next(v for v in r["original_only_events"] if v["symbol"]=="X0000USDT")
        self.assertEqual(first["new_same_symbol_D1_times"],["2025-11-04T12:09:00Z"])
    def test_unexpected_missing_source_d1_count_fails_closed(self):
        old,new=mock_six_days()
        with self.assertRaisesRegex(ValueError,"ORIGINAL_826_OR_SHARED_828_CHANGED"):
            m.compare(old[:825],new)
    def test_exact_all_source_identity_not_l2_execution(self):
        old,new=mock_six_days()
        r=m.compare(old,new)
        self.assertTrue(r["not_full_shared_global_D0"])
        self.assertEqual(r["user_money_or_real_orderbook"],"NOT_VERIFIED")

if __name__=="__main__":unittest.main()
