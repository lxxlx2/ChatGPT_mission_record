"""Stage31 genuine original D0 gate causality and source identity fail closed."""
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

P=Path(__file__).parents[1]/"scripts"
if str(P) not in sys.path:sys.path.insert(0,str(P))
import monster_v4_stage31_five_case_causal_trace as m

class Stage31Tests(unittest.TestCase):
    def test_five_frozen_cases_and_real_source_blobs(self):
        f=m.contract()
        self.assertEqual(len(f["frozen_cases"]),5)
        self.assertEqual(f["frozen_cases"][1]["symbol"],"PENGUUSDT")
        self.assertEqual(f["frozen_cases"][4]["target_m"],5)
    def test_not_allowed_with_less_than_18_sha_original_shards(self):
        with self.assertRaisesRegex(ValueError,"REQUIRE_ALL18_ORIGINAL_SHARDS"):
            m.original_five_cases([])
    def test_exact_snapshot_momentum_quote_cooldown_matches_production(self):
        anchor=int(datetime(2025,4,25,tzinfo=timezone.utc).timestamp()*1000)
        with tempfile.TemporaryDirectory() as d:
            db=m.live.open_store(Path(d)/"stage31.sqlite")
            try:
                for idx in range(6):
                    ms=anchor+idx*180000
                    price=Decimal("1") if idx<5 else Decimal("1.06")
                    quot=Decimal("200000")
                    pred=m.diagnostic_predicates(db,"TESTUSDT",ms,price,quot)
                    if idx==0:self.assertEqual(pred["D0_gate_explanation"],"NO_3M_15M_60M_THRESHOLD")
                    if idx==5:self.assertEqual(pred["D0_gate_explanation"],"ELIGIBLE_FOR_ORIGINAL_WATCH")
                    actual=m.live.observe_snapshot(db,"spot",ms,[{
                        "symbol":"TESTUSDT","lastPrice":str(price),"quoteVolume":str(quot)}])
                    if idx==5:self.assertEqual(actual["watch_new"],1)
                last=anchor+6*180000
                pred=m.diagnostic_predicates(db,"TESTUSDT",last,Decimal("1.13"),Decimal("200000"))
                self.assertEqual(pred["D0_gate_explanation"],"ALREADY_WATCHED_6H_COOLDOWN")
            finally:db.close()
    def test_quote_gate_distinct_from_no_momentum(self):
        anchor=int(datetime(2025,4,25,tzinfo=timezone.utc).timestamp()*1000)
        with tempfile.TemporaryDirectory() as d:
            db=m.live.open_store(Path(d)/"t.sqlite")
            try:
                m.live.observe_snapshot(db,"spot",anchor,[{
                    "symbol":"TESTUSDT","lastPrice":"1","quoteVolume":"50000"}])
                p=m.diagnostic_predicates(db,"TESTUSDT",anchor+180000,Decimal("1.06"),Decimal("90000"))
                self.assertEqual(p["D0_gate_explanation"],"QUOTE24_LT_100K")
                x=m.live.observe_snapshot(db,"spot",anchor+180000,[{
                    "symbol":"TESTUSDT","lastPrice":"1.06","quoteVolume":"90000"}])
                self.assertEqual(x["watch_new"],0)
            finally:db.close()
    def test_future_high_unavailable_in_feature_contract(self):
        self.assertEqual(m.diagnostic_predicates.__code__.co_varnames[:5],
            ("db","symbol","now_ms","price","quote"))
        self.assertNotIn("cross",m.diagnostic_predicates.__code__.co_varnames)
    def test_unknown_original_month_or_target_cannot_change(self):
        f=m.contract()
        self.assertEqual({x["day"] for x in f["frozen_cases"]},
                         {"2025-01-19","2025-04-19","2025-07-19"})
if __name__=="__main__":unittest.main()
