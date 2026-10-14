"""Frozen Stage127 causal and real519 source acceptance tests."""
import copy
import json
import math
import unittest
from pathlib import Path

import monster_v4_stage127_first_d0_chronological_priority as stage127

ROOT = Path(__file__).resolve().parents[2] / "monster" / "evidence"
SOURCE64 = ROOT/"monster_stage64_all519_D0_asof61m_official_1m_taker_trades_SHA.jsonl"
SOURCE83 = ROOT/"monster_stage83_all519_source_and_D1_result.jsonl"


def read(path):
    return [json.loads(v) for v in path.read_text(encoding="utf-8").splitlines() if v.strip()]


class Stage127Test(unittest.TestCase):
    def test_asof_features_do_not_consume_future_fields(self):
        f = {
            "ret60_pct": "5", "quote15_USDT": "400000",
            "trade_count15": 1000, "quote15_normalized_prev45": "1.01",
            "taker_buy_share15": "0.52", "taker_buy_share60": "0.48",
            "post_D0_24h_close_return_pct_EVALUATION_ONLY": "100000",
        }
        first=stage127.features(f)
        f["post_D0_24h_close_return_pct_EVALUATION_ONLY"] = "-999999"
        self.assertEqual(stage127.features(f),first)
        self.assertEqual(len(first),6)

    def test_asof_invalid_rejected(self):
        base = {
            "ret60_pct": 1, "quote15_USDT": 500, "trade_count15": 100,
            "quote15_normalized_prev45": 1, "taker_buy_share15": .51,
            "taker_buy_share60": .49,
        }
        for k, bad in (("ret60_pct","NaN"),("quote15_USDT",-1),("trade_count15",1.5),
                       ("taker_buy_share15",1.5),("taker_buy_share60",-0.1)):
            with self.subTest(k=k):
                altered=dict(base);altered[k]=bad
                with self.assertRaises(ValueError):
                    stage127.features(altered)

    def test_utc06_seven_days_no_future(self):
        self.assertEqual(stage127.day_bucket("2025-08-01",stage127.parse_utc("2025-08-01T06:00:00Z")),0)
        self.assertEqual(stage127.day_bucket("2025-08-01",stage127.parse_utc("2025-08-08T05:59:59Z")),6)
        with self.assertRaises(ValueError):
            stage127.day_bucket("2025-08-01",stage127.parse_utc("2025-08-08T06:00:00Z"))
        with self.assertRaises(ValueError):
            stage127.day_bucket("2025-08-01",stage127.parse_utc("2025-08-01T05:59:59Z"))

    def test_calibration_no_daily_hard_quota_drop(self):
        rows = [{"anchor":"2025-01-30","utc06_day_bucket":0} for _ in range(20)]
        limit=stage127.calibrate(rows, [0.3]*20)
        self.assertEqual(limit,.3)
        b=stage127.burden(rows,[p>limit for p in [0.3]*20],["2025-01-30"])
        self.assertEqual(b["attention_n"],0)
        self.assertEqual(b["days"],7)

    def test_no_trained_model_until_prior_six_positives(self):
        rows = [{"asof_features":(0.,0.,0.,0.,0.,0.),"evaluated_early5_2x":False,
                 "anchor":"2025-01-30","utc06_day_bucket":0} for _ in range(40)]
        self.assertIsNone(stage127.fit(rows))

    def test_real_519_frozen_sources_and_no_oos_upgrade(self):
        a,b=read(SOURCE64),read(SOURCE83)
        parsed=stage127.parse_inputs(a,b)
        self.assertEqual(len(parsed),519)
        self.assertEqual(sum(r["evaluated_early5_2x"] for r in parsed),28)
        self.assertEqual([sum(1 for r in parsed if r["anchor"]==d) for d in stage127.SIX_ANCHORS],
                         [161,34,54,75,100,95])
        result=stage127.evaluate(parsed)
        self.assertEqual(result["all_original_D0_n"],519)
        self.assertEqual(len(result["rows"]),519)
        self.assertTrue(all(row["original_D0_retained"] for row in result["rows"]))
        self.assertEqual(result["genuine_new_OOS"],"NOT_DONE")
        self.assertEqual(result["G4_real_executable_net"],"UNKNOWN")
        self.assertEqual(result["monster_deployment"],"NO_GO")
        self.assertIn(result["historical_research_verdict"],
                      {"REJECTED_EXPOSED_HISTORICAL","HISTORICAL_DIAGNOSTIC_NOT_OOS"})

    def test_tampered_source_date_and_duplicates_rejected(self):
        a,b=read(SOURCE64),read(SOURCE83)
        broken=copy.deepcopy(a);broken[0]["first_D0_UTC"]="2025-01-01T06:00:00Z"
        with self.assertRaisesRegex(ValueError,"MISMATCH"):
            stage127.parse_inputs(broken,b)
        broken=copy.deepcopy(a);broken[1]=broken[0]
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            stage127.parse_inputs(broken,b)


if __name__ == "__main__":
    unittest.main()
