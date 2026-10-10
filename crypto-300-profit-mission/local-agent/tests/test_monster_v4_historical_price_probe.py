"""Source-grounded historical D0 price-only probe; not a full V4 model replay."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1]/"scripts/monster_v4_historical_price_probe.py"
spec = importlib.util.spec_from_file_location("monster_v4_historical_price_probe", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class HistoricalPriceProbeTests(unittest.TestCase):
    def test_official_1m_histories_contiguous_and_real(self):
        samples=[m.price_probe(path) for path in m.PATHS]
        self.assertEqual([x["symbol"] for x in samples],
                         ["XTZUSDT", "BROCCOLI714USDT"])
        for x in samples:
            self.assertEqual(x["raw_1m_bars"],240)
            self.assertEqual(x["sampled_3m_snapshots"],80)
            self.assertFalse(x["full_V4_backtest"])
            self.assertFalse(x["historical_orderbook_available"])
            self.assertFalse(x["24h_ticker_history_reconstructed"])

    def test_known_historical_5x_positive_not_detected_in_this_4h_window(self):
        sample=m.price_probe(m.PATHS[1])
        self.assertEqual(sample["symbol"],"BROCCOLI714USDT")
        self.assertEqual([x["window_trigger_count"] for x in sample["triggers"]],
                         [0,0,0])
        self.assertEqual(sample["triggers"][2]["at_historical_watch_pct"],"5.655931")

    def test_gap_in_source_must_raise(self):
        src=json.loads(m.PATHS[0].read_text(encoding="utf-8"))
        src["bars"][40][0]+=60000
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/"invalid.json"
            target.write_text(json.dumps(src),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"GAPPED_1M_BARS"):
                m.price_probe(target)


if __name__=="__main__":
    unittest.main()
