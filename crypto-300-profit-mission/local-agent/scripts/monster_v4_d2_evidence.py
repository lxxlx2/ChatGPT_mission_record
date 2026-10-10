#!/usr/bin/env python3
"""Recompute Stage 6 D2 from preserved genuine Binance public 100-level snapshots."""
import json
from pathlib import Path

try:
    from monster_v4_d2 import evaluate_spot_execution
except ImportError:
    from scripts.monster_v4_d2 import evaluate_spot_execution

EVIDENCE = (Path(__file__).resolve().parents[2] / "monster" /
            "evidence/monster_stage6_spot_orderbook_3symbol_20261011.json")


def replay(path=EVIDENCE):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("evidence_version")!="monster_stage6_spot_orderbook_3symbol_v1":
        raise ValueError("WRONG_EVIDENCE_VERSION")
    result=[]
    for e in data["snapshots"]:
        x=evaluate_spot_execution(e["symbol_info"],e["book"],
                                  e["exchange_info_server_time_ms"],
                                  budget_usdt="30",assumed_fee_bps="10")
        result.append({
            "symbol":e["symbol"],"collection_time_utc":e["collection_time_utc"],
            "best_bid":x["best_bid"],"best_ask":x["best_ask"],
            "spread_bps":x["spread_bps"],
            "instant_roundtrip_loss_usdt":x["instant_roundtrip_loss_usdt"],
            "instant_roundtrip_cost_bps":x["instant_roundtrip_cost_bps"],
            "depth_fully_filled":x["depth_fully_filled"],
            "snapshot_executable_proxy":x["snapshot_executable_proxy"],
            "research_liquidity_gate":x["research_liquidity_gate"],
            "fee_assumption_bps_per_side":x["fee_assumption_bps_per_side"]
        })
    return {"snapshot_count":len(result),
            "classification":"EXPOST_SNAPSHOT_COST_NOT_FORWARD_PNL",
            "simultaneous_atomic_books":False,"actual_fill_verified":False,
            "results":result}


if __name__=="__main__":
    print(json.dumps(replay(),indent=2,sort_keys=True))
