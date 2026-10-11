"""Frozen Stage19 gradual Watch scan and unchanged V4 comparison."""
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

FILE=Path(__file__).parents[1]/"scripts"/"monster_v4_stage19_gradual_watch.py"

def load():
    tmp=Path(tempfile.gettempdir())/"monster-stage19-test"
    tmp.mkdir(exist_ok=True)
    candidate={"rolling_6h_close_return_min_pct":10,
        "rolling_2h_close_return_min_pct":3,
        "trailing_24h_quote_usdt_min":250000,"signal_cooldown_minutes":1440,
        "entry_delay_min":3,"hold_minutes":1440,
        "assumed_fee_per_side_bps":10,"assumed_slippage_per_side_bps":20}
    (tmp/"monster_stage19_gradual_watch_exploratory_prereg_20261011.json").write_text(json.dumps({
        "schema":"MONSTER_STAGE19_EXPLORATORY_GRADUAL_WATCH_FIXED_BEFORE_REAL_BULK_1M_REPLAY_V1",
        "candidate_v1":candidate,
        "dates":["2025-11-17","2026-02-17","2026-05-17","2026-08-17","2026-09-17"],
        "frozen_full_universe":758,
        "archive_only_set_sha256":"frozen_hash"}))
    a=types.ModuleType("monster_v4_archive_universe_replay")
    a.source=types.SimpleNamespace(EVIDENCE=tmp)
    a.get_day=None
    v=types.ModuleType("monster_v4_historical_replay")
    v.utc=lambda ms: str(ms)
    v.parse_ms=lambda date_str:12*3600000
    v.replay_case=lambda *a,**k:None
    v._proxy_trade=lambda *a,**k:None
    s=types.ModuleType("monster_v4_stage15_archive_only")
    s.FROZEN_DATES=("2025-11-17","2026-02-17","2026-05-17","2026-08-17","2026-09-17")
    s.inventory=lambda:{"archive_only_sha256":"frozen_hash",
               "archive_only_symbols":[f"X{i}USDT" for i in range(254)]}
    s.frozen_current504=lambda:{f"Y{i}USDT" for i in range(504)}
    for m in (a,v,s):sys.modules[m.__name__]=m
    spec=importlib.util.spec_from_file_location("stage19_testable",FILE)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def bars(*,is_gradual=False,volume=1000):
    rows=[]
    for i in range(3600):
        price=Decimal("1")
        if is_gradual:
            price=Decimal("1")+(Decimal(max(0,i-1080))/Decimal(1000))
        rows.append((i*60000,price,price,price,price,Decimal(volume),1))
    return rows

class Stage19Tests(unittest.TestCase):
    def test_unchanged_frozen_gate_and_758_union(self):
        m=load()
        self.assertEqual(m.frozen()["candidate_v1"]["rolling_6h_close_return_min_pct"],10)
        self.assertEqual(len(m.union()),758)

    def test_gradual_trend_generates_watch(self):
        m=load()
        candidate,diag=m.price_gates(bars(is_gradual=True))
        self.assertIsNotNone(candidate)
        self.assertGreater(diag["eligible_trade_3m_polls"],0)
        self.assertGreaterEqual(candidate["6h_change_pct"],10)
        self.assertGreaterEqual(candidate["2h_change_pct"],3)

    def test_flat_market_no_false_watch(self):
        m=load()
        c,debug=m.price_gates(bars())
        self.assertIsNone(c)
        self.assertEqual(debug["6h_momentum_polls"],0)

    def test_low_liquidity_blocks_gradual_watch(self):
        m=load()
        c,_=m.price_gates(bars(is_gradual=True,volume=1))
        self.assertIsNone(c)

    def test_profit_censored_not_zero_or_profit(self):
        m=load()
        cases=[{"status":"COMPLETE_60H","symbol":"XUSDT",
             "v4_watch_count":0,"v4_d1_count":0,
             "gradual_first_watch":{"incremental_before_old_v4":True,
                        "24h_trade_price_proxy":{"status":"CENSORED_ZERO_VOLUME_EXIT"}}}]
        summary=m.summarize(cases)
        self.assertEqual(summary["gradual_censored"],{"CENSORED_ZERO_VOLUME_EXIT":1})
        self.assertEqual(summary["gradual_24h_price_proxy_evaluable"],0)
        self.assertIsNone(summary["gradual_24h_price_proxy_median_pct"])

    def test_unknown_date_rejected(self):
        m=load()
        with self.assertRaisesRegex(ValueError,"DATE_NOT_FROZEN"):
            m.run_day("2026-06-12",symbols=["XUSDT"])

if __name__=="__main__":
    unittest.main()
