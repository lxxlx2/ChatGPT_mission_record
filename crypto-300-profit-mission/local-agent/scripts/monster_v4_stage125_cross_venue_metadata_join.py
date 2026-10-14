#!/usr/bin/env python3
"""Research-only metadata join, never an executable trading or identity verdict."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


class MetadataSourceError(ValueError):
    pass


def unwrap_exchange_info(source, label):
    if not isinstance(source, dict):
        raise MetadataSourceError(f"{label}: source must be object")
    source = source.get("structuredContent", source)
    if not isinstance(source, dict) or not isinstance(source.get("symbols"), list):
        raise MetadataSourceError(f"{label}: symbols array missing")
    stamp = source.get("serverTime")
    if type(stamp) is not int or stamp <= 0:
        raise MetadataSourceError(f"{label}: no integer embedded serverTime")
    rows = source["symbols"]
    if not rows:
        raise MetadataSourceError(f"{label}: empty universe")
    seen = set()
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise MetadataSourceError(f"{label}: row {idx} not an object")
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip() or symbol != symbol.strip():
            raise MetadataSourceError(f"{label}: bad symbol at {idx}")
        if symbol in seen:
            raise MetadataSourceError(f"{label}: duplicate symbol {symbol}")
        seen.add(symbol)
        if any(not isinstance(row.get(k), str) for k in ("status", "baseAsset", "quoteAsset")):
            raise MetadataSourceError(f"{label}: missing metadata for {symbol}")
    return stamp, rows


def assess(futures_info, spot_info):
    ftime, futures = unwrap_exchange_info(futures_info, "USD_M")
    stime, spots = unwrap_exchange_info(spot_info, "SPOT")
    cohort_f = [r for r in futures if r["status"] == "TRADING" and r.get("contractType") == "PERPETUAL" and r["quoteAsset"] == "USDT"]
    if not cohort_f:
        raise MetadataSourceError("USD_M: no active perpetual USDT population")
    spot_usdt = {r["symbol"]: r for r in spots if r["quoteAsset"] == "USDT"}
    by_base = defaultdict(list)
    for r in spots:
        if r["status"] == "TRADING" and r.get("isSpotTradingAllowed") is True:
            by_base[r["baseAsset"]].append({"symbol": r["symbol"], "quote_asset": r["quoteAsset"]})
    counters = Counter()
    cohort = []
    for f in sorted(cohort_f, key=lambda r: r["symbol"]):
        s = spot_usdt.get(f["symbol"])
        if s is None:
            grade = "NO_EXACT_SPOT_USDT_SYMBOL"
        elif s["status"] == "TRADING" and s.get("isSpotTradingAllowed") is True:
            grade = "EXACT_SPOT_USDT_METADATA_TRADING_UNVERIFIED"
        else:
            grade = "EXACT_SPOT_USDT_NOT_TRADING_OR_DISABLED"
        counters[grade] += 1
        cohort.append({
            "usdm_symbol": f["symbol"],
            "usdm_base_asset": f["baseAsset"],
            "usdm_pair": f.get("pair"),
            "usdm_underlying_type_exchange_label": f.get("underlyingType"),
            "usdm_underlying_subtype_exchange_label": f.get("underlyingSubType"),
            "exact_spot_usdt_symbol": s["symbol"] if s else None,
            "exact_spot_status": s["status"] if s else None,
            "exact_spot_trading_allowed": s.get("isSpotTradingAllowed") if s else None,
            "exact_join_diagnostic": grade,
            "other_same_base_spot_trading_pairs_diagnostic_only": [v for v in by_base.get(f["baseAsset"], []) if v["symbol"] != f["symbol"]],
            "crypto_identity_confirmed": False,
            "contract_unit_confirmed": False,
            "spot_execution_confirmed": False,
        })
    if sum(counters.values()) != len(cohort_f):
        raise MetadataSourceError("USD_M: incomplete cohort join")
    return {
        "schema": "MONSTER_STAGE125_ASYNC_CROSS_VENUE_METADATA_DIAGNOSTIC_V1",
        "source": "CONNECTED_BINANCE_STRUCTURED_EXCHANGEINFO_NOT_RAW_HTTPS",
        "usdm_embedded_server_time_ms_not_capture_proof": ftime,
        "spot_embedded_server_time_ms_not_capture_proof": stime,
        "embedded_time_difference_ms_not_true_request_skew": stime-ftime,
        "usdm_all_exchangeinfo": len(futures),
        "usdm_active_usdt_perpetual": len(cohort_f),
        "spot_all_exchangeinfo": len(spots),
        "spot_usdt_all_status": len(spot_usdt),
        "spot_usdt_status_trading": sum(r["status"] == "TRADING" for r in spot_usdt.values()),
        "exact_spot_usdt_metadata_trading_unverified": counters["EXACT_SPOT_USDT_METADATA_TRADING_UNVERIFIED"],
        "exact_spot_usdt_not_trading_or_disabled": counters["EXACT_SPOT_USDT_NOT_TRADING_OR_DISABLED"],
        "no_exact_spot_usdt_symbol": counters["NO_EXACT_SPOT_USDT_SYMBOL"],
        "independent_crypto_identity_and_contract_units": "UNVERIFIED",
        "contemporaneous_venue_tradability": "UNVERIFIED",
        "asof_observation_source_clock": "UNVERIFIED",
        "eligible_buy_recommendations": 0,
        "g0": "PARTIAL",
        "g4_actual_net": "UNKNOWN",
        "model_stage118": "REJECTED_UNCHANGED",
        "full_cohort": cohort,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usdm", type=Path, required=True)
    parser.add_argument("--spot", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    a = parser.parse_args()
    with a.usdm.open(encoding="utf-8") as f:
        usdm = json.load(f)
    with a.spot.open(encoding="utf-8") as f:
        spot = json.load(f)
    result = assess(usdm, spot)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k,v in result.items() if k != "full_cohort"}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
