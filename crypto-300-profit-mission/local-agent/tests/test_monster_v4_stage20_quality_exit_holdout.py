"""Stage20 frozen holdout, chronological quality gates and conservative exits."""
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from decimal import Decimal as D
from pathlib import Path

SOURCE=Path(__file__).parents[1]/"scripts"/"monster_v4_stage20_quality_exit_holdout.py"

def load():
    evidence=Path(tempfile.gettempdir())/"monster-stage20-unit"
    evidence.mkdir(exist_ok=True)
    manifest={
        "schema":"MONSTER_STAGE20_FROZEN_HOLDOUT_QUALITY_EXIT_COMPARISON_V1",
        "holdout_dates_utc":["2025-12-13","2026-01-13","2026-04-13","2026-07-13"],
        "expected_symbols":758,
        "archive_only_sha256":"hash",
        "quality_gate":{
            "last_15m_quote_ratio_against_prior_45m_normalized_min":1.5,
            "last_1m_quote_min_usdt":30,
            "last_close_vs_previous_60m_high_drawdown_max_pct":8,
            "relative_60m_return_minus_btc_60m_min_percentage_points":4,
            "max_symbol_60m_return_pct":70},
        "risk_exit":{"stop_loss_pct":8,"take_profit_pct":18,"timeout_min":360,
             "execution_scenarios_bps_per_side":[20,100]},
        "baseline":{"trigger":"V4 production SETUP_ACTIVE from full calendar replay",
                "entry_lag_min":3,"exit_fixed_min":1440,
                "fee_bps_per_side":10,"slippage_bps_per_side":20,"capital_usdt":30},
        "arms":["A_ALL_D1_FIXED_24H_20BPS","B_ALL_D1_BOUNDED_6H_20BPS",
                "C_QUALITY_D1_FIXED_24H_20BPS",
                "D_QUALITY_D1_BOUNDED_6H_20BPS",
                "E_QUALITY_D1_BOUNDED_6H_100BPS"],
    }
    (evidence/"monster_stage20_quality_exit_holdout_prereg_20261011.json").write_text(json.dumps(manifest))
    archive=types.ModuleType("monster_v4_archive_universe_replay")
    archive.source=types.SimpleNamespace(EVIDENCE=evidence)
    archive.get_day=lambda s,d:None
    replay=types.ModuleType("monster_v4_historical_replay")
    replay.parse_ms=lambda _:0
    replay.utc=lambda ms:str(ms)
    replay.replay_case=lambda *a,**k:None
    replay._proxy_trade=lambda *a,**k:None
    stage15=types.ModuleType("monster_v4_stage15_archive_only")
    stage15.inventory=lambda:{"archive_only_sha256":"hash",
        "archive_only_symbols":[f"X{i}USDT" for i in range(254)]}
    stage15.frozen_current504=lambda:{f"Y{i}USDT" for i in range(504)}
    for x in (archive,replay,stage15): sys.modules[x.__name__]=x
    spec=importlib.util.spec_from_file_location("stage20_testable",SOURCE)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

def bars(quote=D("1000"),price=D("100")):
    return [(i*60000,price,price,price,price,quote,10) for i in range(3600)]

def replace(row, index, value):
    z=list(row)
    z[index]=value
    return tuple(z)

class FrozenStage20(unittest.TestCase):
    def test_manifest_and_universe_locked(self):
        m=load()
        cfg=m.frozen_manifest()
        universe,inv=m.universe(cfg)
        self.assertEqual(len(universe),758)
        self.assertEqual(inv["archive_only_sha256"],"hash")
        self.assertEqual(len(m.ARMS),5)

    def test_indicator_uses_only_closed_bars(self):
        m=load()
        sym=bars()
        benchmark=bars()
        idx=1750
        # No future changes may affect a signal at observed 1751m.
        first=m._causal_features(sym,benchmark,(idx+1)*60000)
        for i in range(idx+1,3600):
            sym[i]=replace(sym[i],4,D("999999"))
            sym[i]=replace(sym[i],5,D("999999999"))
        second=m._causal_features(sym,benchmark,(idx+1)*60000)
        self.assertEqual(first,second)
        self.assertFalse(first["quality_pass"])

    def test_quality_gate_accepts_broad_traded_relative_breakout(self):
        m=load()
        sym=bars()
        btc=bars()
        idx=1800
        for i in range(idx-65,idx+1):
            price=D("100")+D(i-(idx-65))*D("0.14")
            quote=D("3000") if i>=idx-14 else D("600")
            sym[i]=(i*60000,price,price,price,price,quote,30)
        result=m._causal_features(sym,btc,(idx+1)*60000)
        self.assertTrue(result["quality_pass"])
        self.assertGreater(result["relative_60m_return_pp"],4)
        self.assertGreater(result["quote_ratio_recent15_to_prior45"],1.5)

    def test_feature_rejects_missing_recent_trade(self):
        m=load()
        sym=bars()
        idx=1850
        sym[idx-3]=replace(sym[idx-3],6,0)
        r=m._causal_features(sym,bars(),(idx+1)*60000)
        self.assertFalse(r["flags"]["last_6m_traded"])

    def test_stop_first_when_both_prices_in_same_minute(self):
        m=load()
        seq=bars()
        # Entry at index 1500 by setup_ms=1497m, open=100.
        candle=list(seq[1504]);candle[2]=D("130");candle[3]=D("80")
        seq[1504]=tuple(candle)
        out=m.bounded_exit(seq,1497*60000,20)
        self.assertEqual(out["exit_reason"],"STOP_FIRST_BOTH_IN_1M")
        self.assertTrue(out["same_candle_both_stop_priority"])
        self.assertLess(out["net_pct"],-8)

    def test_stop_gap_worse_than_target_never_optimistic(self):
        m=load()
        seq=bars()
        seq[1510]=(1510*60000,D("85"),D("88"),D("82"),D("87"),D("1000"),10)
        out=m.bounded_exit(seq,1497*60000,20)
        self.assertEqual(out["exit_reason"],"STOP")
        self.assertEqual(out["exit_price_conservative_1m_proxy"],"85")

    def test_take_profit_and_slippage_sensitivity(self):
        m=load()
        seq=bars()
        seq[1510]=replace(seq[1510],2,D("120"))
        cheap=m.bounded_exit(seq,1497*60000,20)
        expensive=m.bounded_exit(seq,1497*60000,100)
        self.assertEqual(cheap["exit_reason"],"TAKE_PROFIT")
        self.assertGreater(cheap["net_pct"],expensive["net_pct"])

    def test_exit_no_volume_must_be_censored(self):
        m=load()
        seq=bars()
        candle=list(seq[1510]);candle[2]=D("122");candle[5]=D(0);candle[6]=0
        seq[1510]=tuple(candle)
        out=m.bounded_exit(seq,1497*60000)
        self.assertEqual(out["status"],"CENSORED_ZERO_VOLUME_EXIT")
        self.assertNotIn("net_pct",out)

    def test_timeout_6h_not_24h_and_no_lookahead(self):
        m=load()
        seq=bars()
        out=m.bounded_exit(seq,1497*60000)
        self.assertEqual(out["exit_reason"],"TIMEOUT_6H")
        self.assertEqual(out["exit_utc"],str(1860*60000))

    def test_summary_keeps_denominator_and_censors(self):
        m=load()
        cases=[{"symbol":"ABCUSDT","status":"COMPLETE_60H","v4_watch":2,
            "v4_d1_episodes":1,"quality":{"quality_pass":False,"flags":{"x":False}},
            "arm_proxies":{m.ARMS[0]:{"status":"PRICE_PROXY_ONLY","net_pct":-4},
            m.ARMS[1]:{"status":"CENSORED_ZERO_VOLUME_EXIT"},
            m.ARMS[2]:None,m.ARMS[3]:None,m.ARMS[4]:None}},
            {"symbol":"XUSDT","status":"SOURCE_MISSING"}]
        out=m.summarize(cases)
        self.assertEqual(out["attempted"],2)
        self.assertEqual(out["source_status"]["SOURCE_MISSING"],1)
        self.assertEqual(out["quality_accepted"],0)
        self.assertEqual(out[m.ARMS[0]]["negative"],1)
        self.assertEqual(out[m.ARMS[1]]["censored"]["CENSORED_ZERO_VOLUME_EXIT"],1)

if __name__=="__main__":
    unittest.main()
