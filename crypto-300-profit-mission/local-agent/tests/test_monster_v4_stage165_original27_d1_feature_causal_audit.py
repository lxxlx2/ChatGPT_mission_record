"""Stage165 original-production D1 feature parity and offline source gates."""
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("stage165_module", SCRIPTS / "monster_v4_stage165_original27_d1_feature_causal_audit.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def candles(closes=None, quotes=None):
    closes = closes or ["1", "1", "1", "1", "1.1", "1.2", "1.3", "1.4"]
    quotes = quotes or ["20", "20", "20", "20", "20", "50", "50", "50"]
    base = 1_800_000_000_000
    out = []
    for i, (price, quote) in enumerate(zip(closes, quotes)):
        value = Decimal(price)
        out.append([
            base + i * 300000, price, str(value * Decimal("1.1")),
            str(value * Decimal("0.9")), price, "100",
            base + (i+1)*300000 - 1, quote
        ])
    return out


class TestStage165OriginalD1(unittest.TestCase):
    def test_fully_passing_all_three_conditions_matches_original_production(self):
        records = candles()
        out, ratio, checks = m.classify_original_d1(records, records[-1][6] + 1)
        self.assertTrue(out["setup_candidate"])
        self.assertEqual(ratio, "2.5")
        self.assertTrue(all(checks.values()))
        self.assertEqual(out["positive_steps_last3"], 3)

    def test_fail_positive_steps_without_changing_quote_ratio(self):
        records = candles(closes=["1","1","1","1","1","1","1","1"])
        out, _, checks = m.classify_original_d1(records, records[-1][6]+1)
        self.assertFalse(out["setup_candidate"])
        self.assertFalse(checks["positive_steps_last3_at_least_2"])
        self.assertTrue(checks["recent_vs_earlier_15m_quote_ratio_at_least_1p5"])

    def test_fail_quote_ratio_while_price_trend_stays_positive(self):
        records = candles(quotes=["20"] * 8)
        out, ratio, checks = m.classify_original_d1(records, records[-1][6]+1)
        self.assertFalse(out["setup_candidate"])
        self.assertEqual(ratio, "1")
        self.assertTrue(checks["positive_steps_last3_at_least_2"])
        self.assertFalse(checks["recent_vs_earlier_15m_quote_ratio_at_least_1p5"])

    def test_actual_decimal_ratio_near_1p5_is_not_rounded_to_pass(self):
        q = ["20","20","20","20","20","29.99999","29.99999","29.99999"]
        records = candles(quotes=q)
        out, ratio, checks = m.classify_original_d1(records, records[-1][6]+1)
        self.assertFalse(out["setup_candidate"])
        self.assertLess(Decimal(ratio), Decimal("1.5"))
        self.assertFalse(checks["recent_vs_earlier_15m_quote_ratio_at_least_1p5"])

    def test_original_production_rejects_unclosed_candle(self):
        records = candles()
        with self.assertRaisesRegex(ValueError, "INSUFFICIENT_CLOSED_5M|GAPPED_OR_OPEN_5M"):
            m.classify_original_d1(records, records[0][0]+1)

    def test_frozen_stage162_hash_enforced_before_using_any_synthetic_source(self):
        with tempfile.TemporaryDirectory() as folder:
            x=Path(folder)/"wrong.json"
            y=Path(folder)/"small.json"
            x.write_text('{"fake":true}')
            y.write_text('{"fake":true}')
            with self.assertRaisesRegex(ValueError, "STAGE162_FULL_SOURCE_SHA_DRIFT"):
                m.source_inputs(x, y)


if __name__ == "__main__":
    unittest.main()
