#!/usr/bin/env python3
"""Stage147: original Stage140 real 525 venue BBO source-quality and no-fill gate.

Pure offline. Never downloads, places an order, changes original V4 D0/D1,
assumes user notional, or treats a BBO quote as an L2 fill. Independent
Binance publisher provenance/issuer/contract-multiplier remain UNVERIFIED.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

SCHEMA = "MONSTER_STAGE147_REAL525_STAGE140_BBO_ONLY_EXECUTION_READINESS_V1"
SOURCE_DIR = (Path(__file__).resolve().parents[2] / "monster" / "evidence" /
              "monster_stage140_user_authorized_real_www_mirror_20261015" /
              "t0_2026-10-14T175247096Z")
SOURCES = {
    "ticker24": "usdm_all_24h_ticker",
    "bbo": "usdm_all_best_bid_ask",
    "mark": "usdm_all_mark_price",
}
MANIFEST_NAMES = {
    "ticker24": "usdm_all_24h_ticker",
    "bbo": "usdm_all_best_bid_ask",
    "mark": "usdm_all_mark_price",
}


def positive(value, field):
    if isinstance(value, bool) or value is None:
        raise ValueError("STAGE147_INVALID_NUMERIC_" + field)
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("STAGE147_INVALID_NUMERIC_" + field) from None
    if not n.is_finite() or n <= 0:
        raise ValueError("STAGE147_INVALID_NUMERIC_" + field)
    return n


def read_verified_source(root, name, manifest):
    receipt = manifest["optional_all_market_marketdata_receipts"][MANIFEST_NAMES[name]]
    if receipt["file"] != SOURCES[name] + "_raw_http.json":
        raise ValueError("STAGE147_MANIFEST_FILENAME_DRIFT")
    obj = json.loads((root / receipt["file"]).read_text(encoding="utf-8"))
    if not isinstance(obj.get("raw"), str):
        raise ValueError("STAGE147_RAW_HTTP_BODY_NOT_PRESERVED")
    raw = obj["raw"].encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    if (digest != obj.get("raw_sha256") or digest != receipt["raw_sha256"]
            or obj.get("decoded_row_count") != receipt["decoded_row_count"]
            or obj.get("decoded_top_level_type") != "list"
            or obj.get("url", "").split("/fapi/v1/")[0] != "https://www.binance.com"
            or not isinstance(obj.get("request_start_ms"), int)
            or not isinstance(obj.get("response_end_ms"), int)
            or obj["request_start_ms"] > obj["response_end_ms"]):
        raise ValueError("STAGE147_ORIGINAL_HTTP_RECEIPT_SHA_OR_META_MISMATCH")
    rows = json.loads(obj["raw"])
    if not isinstance(rows, list) or len(rows) != receipt["decoded_row_count"]:
        raise ValueError("STAGE147_RAW_HTTP_ROWCOUNT_MISMATCH")
    indexed = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("symbol"), str):
            raise ValueError("STAGE147_BAD_ORIGINAL_MARKET_ROW")
        key = row["symbol"]
        if key in indexed:
            raise ValueError("STAGE147_DUPLICATE_ORIGINAL_MARKET_SOURCE_SYMBOL")
        indexed[key] = row
    return indexed, {
        "raw_SHA256": digest, "original_URL": obj["url"],
        "request_start_ms": obj["request_start_ms"],
        "response_end_ms": obj["response_end_ms"],
        "original_all_market_source_rows": len(rows),
    }


def analyze_rows(universe, sources, receipts, quote_scenario=None):
    """Preserve every original symbol. Single-quote data NEVER proves fill."""
    if quote_scenario is not None:
        amount = positive(quote_scenario, "explicit_quote_scenario")
    else:
        amount = None
    if len(universe) != len({r["symbol_exact"] for r in universe}):
        raise ValueError("STAGE147_DUPLICATE_ORIGINAL_525_SYMBOL")
    counters = Counter()
    spread_bps = []
    bid_visible = []
    ask_visible = []
    ages_ms = []
    results = []
    quote_time = receipts["bbo"]["response_end_ms"]
    for original in universe:
        symbol = original["symbol_exact"]
        typ = original["asof_instrument_scope"]
        row = {
            "symbol_exact": symbol, "asof_instrument_scope": typ,
            "issuer_identity_independently_verified": False,
            "first_executable_trading_minute_proven": False,
            "source_timestamp_observation_only": True,
            "full_L2_depth": "MISSING", "future_exit_book": "MISSING",
            "actual_fill": "NOT_OBSERVED", "net_executable_profit": "UNKNOWN",
            "G4_verified_executable_case": False,
        }
        counters["original_venue_attempts"] += 1
        if typ == "OFFICIAL_COIN_TYPED_ISSUER_UNVERIFIED":
            counters["coin_typed_issuer_unverified"] += 1
        else:
            counters["other_venue_type_issuer_unverified"] += 1
        a = sources["bbo"].get(symbol)
        b = sources["ticker24"].get(symbol)
        c = sources["mark"].get(symbol)
        row["all_three_source_joined"] = bool(a is not None and b is not None and c is not None)
        if not row["all_three_source_joined"]:
            row["status"] = "SOURCE_CENSORED_MISSING_BBO_TICKER_OR_MARK"
            counters["source_censored"] += 1
            results.append(row)
            continue
        try:
            bid = positive(a["bidPrice"], "bid_price")
            ask = positive(a["askPrice"], "ask_price")
            bid_qty = positive(a["bidQty"], "bid_qty")
            ask_qty = positive(a["askQty"], "ask_qty")
            turnover = positive(b["quoteVolume"], "historical_24h_quote")
            mark = positive(c["markPrice"], "mark_price")
            age = quote_time - a["time"]
            if ask <= bid or not isinstance(a["time"], int) or isinstance(a["time"], bool) or age < 0:
                raise ValueError("STAGE147_BAD_BBO_EVENT_TIME_OR_CROSSED")
        except (KeyError, ValueError, TypeError, ArithmeticError):
            row["status"] = "SOURCE_INVALID_BBO_MARK_OR_TICKER"
            counters["source_invalid"] += 1
            results.append(row)
            continue
        spread = (ask-bid)/((ask+bid)/2)*10000
        bid_top = bid*bid_qty
        ask_top = ask*ask_qty
        spread_bps.append(spread)
        bid_visible.append(bid_top)
        ask_visible.append(ask_top)
        ages_ms.append(age)
        row.update({
            "status": "HISTORICAL_BBO_ONLY_G4_NOT_SCORABLE",
            "book_ticker_source_raw_SHA256": receipts["bbo"]["raw_SHA256"],
            "book_ticker_response_end_ms": quote_time,
            "book_ticker_original_event_ms": a["time"],
            "book_ticker_event_age_ms_relative_to_response_end": age,
            "best_bid_price": str(bid), "best_ask_price": str(ask),
            "best_bid_displayed_qty": str(bid_qty),
            "best_ask_displayed_qty": str(ask_qty),
            "midpoint_spread_bps": str(spread),
            "best_bid_displayed_price_times_quantity_proxy": str(bid_top),
            "best_ask_displayed_price_times_quantity_proxy": str(ask_top),
            "saved_24h_ticker_quote_volume": str(turnover),
            "saved_mark_price": str(mark),
            "quote_proxy_has_verified_USDT_contract_multiplier": False,
            "quote_scenario_explicit": str(amount) if amount is not None else None,
            "scenario_is_not_actual_user_notional_or_fill": True,
        })
        if amount is not None:
            row["ask_top_price_times_qty_at_least_scenario_proxy"] = ask_top >= amount
            row["bid_top_price_times_qty_at_least_scenario_proxy"] = bid_top >= amount
            counters["scenario_ask_top_proxy_below"] += int(ask_top < amount)
            counters["scenario_bid_top_proxy_below"] += int(bid_top < amount)
            counters["scenario_either_side_top_proxy_below"] += int(
                ask_top < amount or bid_top < amount)
        counters["source_quote_valid_but_not_L2"] += 1
        results.append(row)

    def selected(values, p):
        if not values:
            return None
        ordered = sorted(values)
        return str(ordered[int((len(ordered)-1)*p)])
    metrics = {
        "valid_BBO_rows": counters["source_quote_valid_but_not_L2"],
        "spread_bps_P50": selected(spread_bps, .5),
        "spread_bps_P90": selected(spread_bps, .9),
        "bid_price_times_qty_proxy_P50": selected(bid_visible, .5),
        "ask_price_times_qty_proxy_P50": selected(ask_visible, .5),
        "book_event_age_ms_relative_to_response_end_P50": selected(ages_ms, .5),
        "book_event_age_ms_relative_to_response_end_max": selected(ages_ms, 1),
    }
    return {
        "schema": SCHEMA, "source_is_archived_real_oneshot_not_live": True,
        "source_host_equivalence_independently_attested": False,
        "all_market_population_rows": results,
        "counts": dict(counters),
        "descriptive_only": metrics,
        "explicit_scenario_quote": str(amount) if amount is not None else None,
        "no_default_transaction_size": amount is None,
        "contract_unit_multiplier_independently_verified": False,
        "required_future_original_L2_depth_enter_and_exit": "MISSING",
        "required_live_venue_rules_and_identity": "UNVERIFIED",
        "required_independently_sourced_fee_and_funding": "MISSING",
        "required_real_paired_order_or_exit_evidence": "MISSING",
        "required_30_independent_executable_cases": "NOT_DONE",
        "G0": "PARTIAL", "G1": "NOT_SCORABLE",
        "G2_G3": "NOT_PASSED", "G4": "UNKNOWN",
        "G5_Stage145_review_only_at_51f2": "APPROVE_FIXED_CODE_ONLY",
        "G6": "NO_GO", "NO_MERGE_NO_DEPLOY_NO_GMAIL_NO_TRADE": True,
    }


def audit(source_root=SOURCE_DIR, *, quote_scenario=None):
    root = Path(source_root)
    manifest = json.loads((root/"stage140_evidence_manifest.json").read_text())
    snapshot = json.loads((root/"stage139_original_T0_asof_contract_metadata.json").read_text())
    universe = snapshot["initial_original_instrument_rows"]
    if (manifest.get("schema") != "MONSTER_STAGE140_EXPLICIT_REAL_ONESHOT_20261015_SUMMARY_V1"
            or len(universe) != 525
            or manifest.get("active_perpetual_USDT_venue_attempts") != 525
            or snapshot.get("initial_USDM_perpetual_USDT_attempts") != 525
            or len({r["symbol_exact"] for r in universe}) != 525
            or any(r.get("source_raw_exchangeinfo_SHA256") != manifest["full_original_exchangeinfo_SHA256"]
                   for r in universe)):
        raise ValueError("STAGE147_ORIGINAL_UNIVERSE_OR_T0_SOURCE_CHANGED")
    data, receipts = {}, {}
    for key in ("bbo", "ticker24", "mark"):
        data[key], receipts[key] = read_verified_source(root, key, manifest)
    result = analyze_rows(universe, data, receipts, quote_scenario=quote_scenario)
    result["original_T0_exchangeInfo_SHA256"] = manifest["full_original_exchangeinfo_SHA256"]
    result["source_receipts"] = receipts
    result["original_saved_capture_utc"] = manifest["capture_UTC"]
    result["source_note"] = (
        "Original source saved at WWW mirror. Source SHA proves byte integrity, "
        "not official origin, executable futures contract unit, depth, fills, or exits.")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=SOURCE_DIR)
    parser.add_argument("--scenario-quote", help="EXPLICIT, analysis-only quote-proxy threshold; not an order")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.source_root, quote_scenario=args.scenario_quote)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True,
                                   ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"schema": result["schema"],
                      "original_venue_attempts": result["counts"]["original_venue_attempts"],
                      "valid_BBO_rows": result["descriptive_only"]["valid_BBO_rows"],
                      "G4": result["G4"],
                      "source_only": True, "out": str(args.out)}))


if __name__ == "__main__":
    main()
