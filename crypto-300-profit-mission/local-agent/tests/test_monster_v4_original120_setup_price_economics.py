"""Independent offline fixture tests: new original120 setup price economics."""
from decimal import Decimal
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location("monster_setup120_economics",
    SCRIPTS/"monster_v4_original120_setup_price_economics.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def bars(n=1700, *, zero_exit=None, high_return=False):
    base=1770000000000 - (1770000000000 % 60000)
    rows=[]
    for i in range(n):
        op=Decimal("1") if not high_return or i < 1443 else Decimal("1.5")
        quote=Decimal("100")
        trades=3
        if zero_exit is not None and i==zero_exit:
            quote=Decimal(0)
            trades=0
        rows.append([base+i*60000,str(op),str(op),str(op),str(op),str(quote),trades])
    return rows


def event(idx, tick, symbol="ABCUSDT"):
    return {"event_id":f"setup-{idx:03d}","event_type":"SETUP_ACTIVE",
            "observed_ms":tick,"symbol":symbol,"venue":"spot","payload":'{"setup_candidate":true}'}


class OriginalSetupPriceTests(unittest.TestCase):
    def test_neutral_market_loses_after_fees_and_slippage(self):
        b=bars()
        h=m.one_horizon(b,b[0][0]+3*60000,60)
        self.assertEqual(h["status"],"PRICE_PROXY_ONLY")
        self.assertLess(Decimal(h["net_percent_fee10_slip20bps_each"]),0)
        self.assertLess(Decimal(h["net_percent_fee10_slip100bps_each"]),
                        Decimal(h["net_percent_fee10_slip20bps_each"]))

    def test_no_same_minute_entry_lookahead(self):
        b=bars()
        e=event(1,b[0][0])
        rows=m.result_for_events([e],{"ABCUSDT":b})
        self.assertEqual(rows[0]["proxy_entry_tick_ms"],b[0][0]+3*60000)
        self.assertEqual(rows[0]["horizons"]["15"]["status"],"PRICE_PROXY_ONLY")

    def test_loss_or_gain_is_not_executable_fill(self):
        b=bars(high_return=True)
        h=m.one_horizon(b,b[0][0]+3*60000,1440)
        self.assertEqual(h["status"],"PRICE_PROXY_ONLY")
        self.assertEqual(h["actual_execution"],"UNVERIFIED")
        self.assertEqual(h["real_orderbook_entry_ask_bid"],"NOT_ARCHIVED")

    def test_zero_trade_exit_censors_instead_of_zero_profit(self):
        b=bars(zero_exit=63)
        h=m.one_horizon(b,b[0][0]+3*60000,60)
        self.assertEqual(h["status"],"CENSORED_NO_EXIT_TRADES")
        self.assertNotIn("net_percent_fee10_slip20bps_each",h)

    def test_zero_trade_near_exit_rejected(self):
        b=bars(zero_exit=61)
        h=m.one_horizon(b,b[0][0]+3*60000,60)
        self.assertEqual(h["status"],"CENSORED_ZERO_TRADE_NEAR_EXIT")

    def test_incomplete_exit_never_assumed_profitable(self):
        b=bars(n=65)
        h=m.one_horizon(b,b[0][0]+3*60000,1440)
        self.assertEqual(h["status"],"CENSORED_NO_COMPLETE_EXIT")
        self.assertNotIn("net_percent_fee10_slip20bps_each",h)

    def test_same_symbol_24h_hold_will_skip_overlapping_setup(self):
        b=bars(n=3000)
        start=b[0][0]
        events=[event(1,start),event(2,start+30*60000),
                event(3,start+1500*60000)]
        rows=m.result_for_events(events,{"ABCUSDT":b})
        self.assertEqual(rows[0]["primary_24h_status"],"PRICE_PROXY_ONLY")
        self.assertEqual(rows[1]["primary_24h_status"],
                        "SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED")
        self.assertEqual(rows[2]["primary_24h_status"],"PRICE_PROXY_ONLY")

    def test_no_overlap_skips_if_previous_24h_censored(self):
        b=bars(n=3500,zero_exit=1443)
        start=b[0][0]
        events=[event(1,start),event(2,start+60*60000)]
        rows=m.result_for_events(events,{"ABCUSDT":b})
        self.assertEqual(rows[0]["primary_24h_status"],"CENSORED_NO_EXIT_TRADES")
        self.assertEqual(rows[1]["primary_24h_status"],"PRICE_PROXY_ONLY")

    def test_row_time_gap_detected(self):
        b=bars(n=12_960)
        b[12][0]+=60000
        with self.assertRaisesRegex(ValueError,"MINUTE_GAP"):
            m.verify_minute_rows(b)

    def test_original_setup_source_sha_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"fake.json"
            p.write_text('{"setup":true}')
            with self.assertRaisesRegex(ValueError,"AB_SHA_DRIFT"):
                m.load_immutable_setups(p)

    def test_horizon_results_count_all_records_no_missing_silent(self):
        b=bars(n=1800)
        start=b[0][0]
        events=[event(i,start+i*1500*60000,"ABCUSDT") for i in range(2)]
        # Second item is censored on missing future bars; no profit imputed.
        rows=m.result_for_events(events,{"ABCUSDT":b})
        stats=m.summarize(rows)
        self.assertEqual(stats["1440"]["price_proxy_valid"],1)
        self.assertEqual(stats["1440"]["status_counts"]["CENSORED_NO_COMPLETE_EXIT"],1)


if __name__ == "__main__":
    unittest.main()
