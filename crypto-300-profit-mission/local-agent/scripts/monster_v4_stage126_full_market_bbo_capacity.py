#!/usr/bin/env python3
"""Stage126 source-locked all-market *displayed* BBO capacity, no trading."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from statistics import median

from monster_v4_stage124_manual_snapshot_comparison import load

SCHEMA = "MONSTER_STAGE126_ALL_MARKET_BBO_DISPLAYED_CAPACITY_V1"
MAX_ABS_SOURCE_LAG_MS = 60000


def decimal(value):
    try:
        x = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("INVALID_NUMERIC")
    if not x.is_finite():
        raise ValueError("NONFINITE_NUMERIC")
    return x


def dist(values):
    if not values:
        return {"n": 0, "min": None, "p25": None, "median": None, "p75": None, "p90": None, "max": None}
    ordered = sorted(values)
    n = len(ordered)
    return {
        "n": n,
        "min": str(ordered[0]),
        "p25": str(ordered[(n - 1) // 4]),
        "median": str(median(ordered)),
        "p75": str(ordered[(n - 1) * 3 // 4]),
        "p90": str(ordered[(n - 1) * 9 // 10]),
        "max": str(ordered[-1]),
    }


def price_cohort(ticker):
    if ticker is None:
        return "ROLLING_24H_UNKNOWN"
    try:
        p = decimal(ticker.get("priceChangePercent"))
    except ValueError:
        return "ROLLING_24H_UNKNOWN"
    if p >= 10:
        return "ROLLING_24H_UP_GE10"
    if p <= -10:
        return "ROLLING_24H_DOWN_LE10"
    return "ROLLING_24H_OTHER"


def evaluate(symbol, meta, book, ticker, batch_ms):
    row = {
        "symbol": symbol,
        "venue": "BINANCE_USDM_PERPETUAL_USDT",
        "base_asset_as_exchange_labeled": meta.get("baseAsset"),
        "underlying_type_exchange_claim": meta.get("underlyingType"),
        "rolling_24h_ret_cohort_NOT_FUTURE": price_cohort(ticker),
        "source_status": None,
        "bbo_event_epoch_ms": None,
        "bbo_batch_minus_event_ms": None,
        "bid_price": None, "ask_price": None,
        "bid_qty_contract_units": None, "ask_qty_contract_units": None,
        "bid_display_quote_USDT_proxy": None,
        "ask_display_quote_USDT_proxy": None,
        "two_sided_common_contract_qty_proxy": None,
        "visible_roundtrip_buy_quote_USDT_ceiling_proxy": None,
        "spread_bps": None,
        "crypto_asset_identity": "UNVERIFIED",
        "contract_unit_to_spot_token_mapping": "UNVERIFIED",
        "no_user_notional_or_deep_book": True,
        "actual_bid_ask_fills_or_net": "UNKNOWN",
    }
    if book is None:
        row["source_status"] = "MISSING_BBO"
        return row
    try:
        bid = decimal(book.get("bidPrice"))
        ask = decimal(book.get("askPrice"))
        bq = decimal(book.get("bidQty"))
        aq = decimal(book.get("askQty"))
    except ValueError:
        row["source_status"] = "INVALID_BBO_NUMBER"
        return row
    if bid <= 0 or ask <= 0 or ask < bid or bq < 0 or aq < 0:
        row["source_status"] = "INVALID_BBO_PRICE_SIZE_OR_CROSSED"
        return row
    stamp = book.get("time")
    if type(stamp) is not int or stamp <= 0:
        row["source_status"] = "INVALID_BBO_TIME"
        return row
    row.update({
        "bbo_event_epoch_ms": stamp,
        "bbo_batch_minus_event_ms": batch_ms - stamp,
        "bid_price": str(bid),
        "ask_price": str(ask),
        "bid_qty_contract_units": str(bq),
        "ask_qty_contract_units": str(aq),
        "spread_bps": str((ask-bid) * Decimal(20000) / (ask+bid)),
    })
    if abs(batch_ms - stamp) > MAX_ABS_SOURCE_LAG_MS:
        row["source_status"] = "SOURCE_TIME_GAP_GT_60S"
        return row
    if bq == 0 or aq == 0:
        row["source_status"] = "ZERO_OR_INCOMPLETE_DISPLAYED_SIZE"
        return row
    common = min(bq, aq)
    row.update({
        "source_status": "VALID_FRESH_DISPLAYED_BBO",
        "bid_display_quote_USDT_proxy": str(bid*bq),
        "ask_display_quote_USDT_proxy": str(ask*aq),
        "two_sided_common_contract_qty_proxy": str(common),
        "visible_roundtrip_buy_quote_USDT_ceiling_proxy": str(common*ask),
    })
    return row


def analyze(snapshot):
    rows = []
    status = Counter()
    groups = defaultdict(lambda: defaultdict(list))
    for symbol in sorted(snapshot["active"]):
        row = evaluate(
            symbol, snapshot["active"][symbol],
            snapshot["bbo"].get(symbol), snapshot["rolling"].get(symbol), snapshot["batch_ms"],
        )
        rows.append(row)
        status[row["source_status"]] += 1
        if row["source_status"] == "VALID_FRESH_DISPLAYED_BBO":
            groups["ALL_VALID"]["spread_bps"].append(decimal(row["spread_bps"]))
            for field in ("bid_display_quote_USDT_proxy", "ask_display_quote_USDT_proxy",
                          "visible_roundtrip_buy_quote_USDT_ceiling_proxy"):
                groups["ALL_VALID"][field].append(decimal(row[field]))
            cat = row["rolling_24h_ret_cohort_NOT_FUTURE"]
            groups[cat]["spread_bps"].append(decimal(row["spread_bps"]))
            groups[cat]["visible_roundtrip_buy_quote_USDT_ceiling_proxy"].append(
                decimal(row["visible_roundtrip_buy_quote_USDT_ceiling_proxy"]))
    assert len(rows) == len(snapshot["active"]) and sum(status.values()) == len(rows)
    return {
        "schema": SCHEMA,
        "batch_utc_actual_archived": snapshot["batch"],
        "source_manifest": snapshot["manifest"],
        "all_exchangeinfo_symbols": len(snapshot["market"]),
        "full_active_usdt_perpetual_denominator": len(rows),
        "full_cohort_coverage": snapshot["coverage"],
        "bbo_status_counts": dict(sorted(status.items())),
        "bbo_freshness_engineering_cutoff_ms": MAX_ABS_SOURCE_LAG_MS,
        "valid_capacity_distribution_by_retro_24h_cohort": {
            category: {field: dist(values) for field, values in sorted(metrics.items())}
            for category, metrics in sorted(groups.items())
        },
        "all_venue_symbol_rows": rows,
        "source_is_connected_binance_structured_not_raw_https": True,
        "bbo_and_ticker_are_not_atomic": True,
        "liquidity_capacity_is_displayed_L1_upper_bound_not_actual_fill": True,
        "ret24h_is_backward_looking_not_model_forecast": True,
        "notional_quote": "UNSPECIFIED",
        "underlying_crypto_identity": "UNVERIFIED",
        "spot_futures_multiplier": "UNVERIFIED",
        "first_D0_causal_alert_recall": "NOT_SCORABLE_FROM_SNAPSHOT",
        "entry_and_future_exit_actual_net": "UNKNOWN",
        "stage118_historical_model": "REJECTED_UNCHANGED",
        "G0": "PARTIAL",
        "G4": "UNKNOWN",
        "independent_other_AI_review": "NOT_DONE",
        "monster_deployment": "NO_GO",
        "gmail": "OFF",
        "frank": "UNCHANGED",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expect-active", type=int, default=None)
    a = parser.parse_args()
    result = analyze(load(a.manifest))
    if a.expect_active is not None and result["full_active_usdt_perpetual_denominator"] != a.expect_active:
        raise ValueError("STAGE126_FROZEN_DENOMINATOR_NOT_MATCHED")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "all_venue_symbol_rows"}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
