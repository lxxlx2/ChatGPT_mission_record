"""Real historical source replay; no network and no synthetic victories."""
import importlib.util
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/monster_v4_historical_replay.py"
sp = importlib.util.spec_from_file_location("monster_v4_historical_replay", SCRIPT)
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)


class MonsterHistoricalRealReplayTests(unittest.TestCase):
    def test_genuine_normal_and_gt5x_cases_use_same_production_d0_d1(self):
        paths=[
            m.EVIDENCE/"monster_v4_replay_1m_spot_XTZUSDT_2025-03-02.json",
            m.EVIDENCE/"monster_v4_replay_1m_spot_BROCCOLI714USDT_2025-12-31.json"]
        cases=[m.replay_case(*m.load_case(path)) for path in paths]
        self.assertEqual(len(cases),2)
        for c in cases:
            self.assertEqual(c["bars_verified"],3600)
            self.assertGreater(c["polls"],200)
            self.assertEqual(c["ticker24"],
                "1440_REAL_1M_QUOTE_SUM_PROXY_NOT_BINANCE_TICKER")
            self.assertFalse(c["forward_out_of_sample"])
            self.assertFalse(c["historical_execution_verified"])

    def test_real_gap_cases_are_rejected_instead_of_backfilled(self):
        for symbol,date in (("CHZUSDT","2021-03-07"),
                            ("STPTUSDT","2021-09-30")):
            p=m.EVIDENCE/("monster_v4_replay_1m_spot_"+symbol+"_"+date+".json")
            with self.subTest(symbol=symbol):
                with self.assertRaisesRegex(ValueError,"SOURCE_MARKED_INCOMPLETE"):
                    m.load_case(p)

    def test_one_minute_gap_detected_even_if_fake_metadata_says_contiguous(self):
        src=json.loads((m.EVIDENCE/"monster_v4_replay_1m_spot_XTZUSDT_2025-03-02.json")
                       .read_text(encoding="utf-8"))
        src["bars"][100][0]+=60000
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"mutated.json"
            p.write_text(json.dumps(src),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"GAPPED_OR_REORDERED_1M_HISTORY"):
                m.load_case(p)

    def test_trade_proxy_explicitly_not_actual_fill(self):
        path=m.EVIDENCE/"monster_v4_replay_1m_spot_BROCCOLI714USDT_2025-12-31.json"
        _,bars=m.load_case(path)
        t0=bars[0][0]
        trade=m._proxy_trade(bars,t0,t0+1900*60000,180000,20)
        self.assertEqual(trade["status"],"PRICE_PROXY_ONLY")
        self.assertFalse(trade["historical_book_verified"])
        self.assertEqual(trade["fee_per_side_bps_assumed"],10)
        self.assertEqual(trade["slippage_per_side_bps_assumed"],20)
        self.assertEqual(m._proxy_trade(bars,t0,t0+3500*60000,180000,20)["status"],
                         "CENSORED_NO_COMPLETE_EXIT")

    def test_real_cases_report_stale_not_profitable_pass(self):
        paths=sorted(m.EVIDENCE.glob("monster_v4_replay_1m_*.json"))
        result=m.run(paths)
        self.assertGreaterEqual(result["summary"]["cases_replayed"],10)
        self.assertGreaterEqual(result["summary"]["cases_skipped"],2)
        self.assertFalse(result["summary"]["profitability_validated"])
        self.assertEqual(result["summary"]["production_gate"],"NO_GO")
        self.assertEqual(result["source"],"OFFICIAL_BINANCE_1M_CANDLES_FROZEN_GIT")


if __name__=="__main__":
    unittest.main()
