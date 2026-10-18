"""WATCH vs SETUP causal-at-entry cash lock and descriptive matching regressions."""
from decimal import Decimal
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

scripts=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(scripts))
spec=importlib.util.spec_from_file_location("monster_watch_setup_value",
    scripts/"monster_v4_watch_vs_setup_incremental_value.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def candles(n=3000, *, gap=None, price_after=None):
    first=1770187200000
    out=[]
    for i in range(n):
        quote="150"
        trades=4
        if i==gap:
            quote="0"
            trades=0
        price="1" if price_after is None or i<price_after else "2"
        out.append([first+60000*i,price,price,price,price,quote,trades])
    return out


def ev(num,tick,typ="WATCH_EARLY",symbol="BTCUSDT"):
    return {"event_id":f"event{num}","event_type":typ,"symbol":symbol,
            "observed_ms":tick,"venue":"spot"}


class IncrementalValueTests(unittest.TestCase):
    def test_actual_entry_precedes_exit_and_retains_friction(self):
        bars=candles()
        e=ev(1,bars[0][0])
        rows=m.per_arm([e],{"BTCUSDT":bars},causal_symbol_lock=False)
        self.assertEqual(rows[0]["proxy_entry_ms"],e["observed_ms"]+180000)
        self.assertEqual(rows[0]["status"],"PRICE_PROXY_ONLY")
        self.assertLess(Decimal(rows[0]["price_proxy"]["net_percent_fee10_slip20bps_each"]),0)

    def test_lock_at_entry_even_when_exit_24h_censored(self):
        bars=candles(gap=1443)
        t=bars[0][0]
        events=[ev(1,t),ev(2,t+3600000)]
        rows=m.per_arm(events,{"BTCUSDT":bars},causal_symbol_lock=True)
        self.assertEqual(rows[0]["status"],"CENSORED_NO_EXIT_TRADES")
        self.assertEqual(rows[1]["status"],"SKIP_SAME_SYMBOL_24H_LOCKED_AT_ENTRY")

    def test_nonadmissible_entry_does_not_lock_later_source(self):
        bars=candles(gap=3)
        t=bars[0][0]
        events=[ev(1,t),ev(2,t+360000)]
        rows=m.per_arm(events,{"BTCUSDT":bars},causal_symbol_lock=True)
        self.assertEqual(rows[0]["status"],"CENSORED_NO_ENTRY_TRADES")
        self.assertEqual(rows[1]["status"],"PRICE_PROXY_ONLY")

    def test_causal_lock_expires_at_entry_time_not_signal_time(self):
        bars=candles()
        t=bars[0][0]
        events=[ev(1,t),ev(2,t+1440*60000)]
        rows=m.per_arm(events,{"BTCUSDT":bars},causal_symbol_lock=True)
        self.assertEqual(rows[0]["status"],"PRICE_PROXY_ONLY")
        self.assertEqual(rows[1]["status"],"PRICE_PROXY_ONLY")

    def test_arm_denominators_and_invalid_source_not_imputed(self):
        bars=candles(gap=3)
        t=bars[0][0]
        rows=m.per_arm([ev(1,t),ev(2,t+360000)],{"BTCUSDT":bars},causal_symbol_lock=False)
        s=m.arm_summary(rows)
        self.assertEqual(s["original_total_signal_events"],2)
        self.assertEqual(s["price_proxy_valid"],1)
        self.assertEqual(s["status_counts"]["CENSORED_NO_ENTRY_TRADES"],1)
        self.assertEqual(s["wins"]+s["losses"]+s["flats"],1)

    def test_unique_watch_to_setup_match_and_waiting_entry_price_change(self):
        bars=candles(price_after=7)
        t=bars[0][0]
        watch=[ev(1,t)]
        setup=[ev(2,t+360000,"SETUP_ACTIVE")]
        queue=[{"id":8,"symbol":"BTCUSDT","first_seen_ms":t,"deadline_ms":t+900000}]
        pairs,stat=m.matches(watch,setup,queue,{"BTCUSDT":bars})
        self.assertEqual(stat["source_join_counts"],{"UNIQUE":1})
        self.assertEqual(stat["entry_both_admissible"],1)
        self.assertEqual(stat["median_setup_entry_price_change_vs_watch_percent"],"100")
        self.assertIn("paired_setup_minus_watch_net_percentage_points",pairs[0])
        self.assertEqual(pairs[0]["setup_delay_after_watch_minutes"],6)
        self.assertTrue(stat["historically_knowing_future_setup_at_watch_is_oracle_only"])

    def test_ambiguous_original_queues_not_force_matched(self):
        bars=candles()
        t=bars[0][0]
        watch=[ev(1,t),ev(2,t+180000)]
        setup=[ev(3,t+360000,"SETUP_ACTIVE")]
        queues=[
          {"id":11,"symbol":"BTCUSDT","first_seen_ms":t,"deadline_ms":t+900000},
          {"id":12,"symbol":"BTCUSDT","first_seen_ms":t+180000,"deadline_ms":t+1080000}
        ]
        pairs,s=m.matches(watch,setup,queues,{"BTCUSDT":bars})
        self.assertEqual(s["source_join_counts"],{"AMBIGUOUS":1})
        self.assertEqual(s["entry_both_admissible"],0)
        self.assertNotIn("setup_entry_price_change_vs_watch_entry_percent",pairs[0])

    def test_wrong_stage162_original_sha_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"fake.json"
            p.write_text('{"fake":"source"}')
            with self.assertRaisesRegex(ValueError,"SOURCE_SHA256_MISMATCH"):
                m.load_events(p)

    def test_prior_economics_formula_exact_blob_is_not_mutable(self):
        actual=m.git_blob(Path(m.previous.__file__).read_bytes())
        self.assertEqual(actual,m.PREVIOUS_SCRIPT_BLOB)


if __name__=="__main__":
    unittest.main()
