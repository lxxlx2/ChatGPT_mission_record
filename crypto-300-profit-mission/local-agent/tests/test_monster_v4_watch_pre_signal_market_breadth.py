"""Source-clock and anti-lookahead regressions for original-WATCH market breadth."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from decimal import Decimal

scripts=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(scripts))
spec=importlib.util.spec_from_file_location(
    "monster_pre_watch_breadth",scripts/"monster_v4_watch_pre_signal_market_breadth.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def rows(n=70, *, start=1800000000000):
    start-=start%60_000
    return [[start+60_000*i,"1","1","1",str(Decimal("1")+(Decimal(i)/100)),
             "100",3] for i in range(n)]


class PreSignalBreadthTests(unittest.TestCase):
    def test_exactly_60_minute_closed_candle_return_prior_to_watch(self):
        candles=rows()
        t=candles[69][0]
        got=m.prior_60m_percent(candles,t)
        before=Decimal(candles[6][4])
        after=Decimal(candles[66][4])
        self.assertEqual(got,(after/before-1)*100)

    def test_future_prices_at_watch_and_after_cannot_change_features(self):
        candles=rows()
        t=candles[69][0]
        expected=m.prior_60m_percent(candles,t)
        for i in range(67,70):
            candles[i][4]="999999"
        self.assertEqual(m.prior_60m_percent(candles,t),expected)

    def test_signal_which_lacks_63minute_history_is_not_fake_neutral(self):
        candles=rows()
        t=candles[59][0]
        self.assertIsNone(m.prior_60m_percent(candles,t))

    def test_input_minute_gap_or_nonexistent_close_cannot_pass(self):
        candles=rows()
        t=candles[69][0]
        candles[6][0]+=60_000
        self.assertIsNone(m.prior_60m_percent(candles,t))

    def test_zero_and_nonfinite_price_not_valid_regime(self):
        candles=rows()
        t=candles[69][0]
        candles[66][4]="NaN"
        self.assertIsNone(m.prior_60m_percent(candles,t))
        candles[66][4]="0"
        self.assertIsNone(m.prior_60m_percent(candles,t))

    def test_fake_original_ab_rejected_before_looking_at_outcomes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"fake-ab.json"
            e=Path(d)/"fake-economics.json"
            p.write_text("{}")
            e.write_text("{}")
            with self.assertRaisesRegex(ValueError,"AB_SOURCE_SHA_DRIFT"):
                m.load_fixed_inputs(p,e)

    def test_return_is_decimal_exact_not_float_routing_threshold(self):
        candles=rows()
        t=candles[69][0]
        result=m.prior_60m_percent(candles,t)
        self.assertIsInstance(result,Decimal)
        self.assertGreater(result,0)


if __name__=="__main__":
    unittest.main()
