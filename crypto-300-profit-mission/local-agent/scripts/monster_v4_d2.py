#!/usr/bin/env python3
"""Read-only Monster V4 Spot D2 order-book execution approximation.

No orders, account endpoints, Gmail, or automated trading. The 30 USDT
immediate round trip is a snapshot liquidity COST proxy, NOT PnL forecast.
"""
import argparse
import json
import time
from decimal import Decimal, ROUND_DOWN
from pathlib import Path

try:
    from monster_v4_shadow import binance_json, positive, nonnegative
except ImportError:
    from scripts.monster_v4_shadow import binance_json, positive, nonnegative

SPOT_API = "https://api.binance.com"
D2_BOOK_LEVELS = 100
D2_RESEARCH_MAX_SPREAD_BPS = Decimal("100")
D2_RESEARCH_MAX_ROUNDTRIP_BPS = Decimal("250")


def _book_side(levels, side):
    if not isinstance(levels, list) or not levels:
        raise ValueError("EMPTY_" + side)
    result = []
    prev = None
    for level in levels:
        if not isinstance(level, (list, tuple)) or len(level) < 2:
            raise ValueError("INVALID_" + side)
        price = positive(level[0], side + "_PRICE")
        qty = positive(level[1], side + "_QTY")
        if prev is not None:
            if side == "BIDS" and price >= prev:
                raise ValueError("UNSORTED_BIDS")
            if side == "ASKS" and price <= prev:
                raise ValueError("UNSORTED_ASKS")
        result.append((price, qty))
        prev = price
    return result


def _sweep_quote(asks, quote_budget):
    remaining = quote_budget
    acquired = Decimal(0)
    for price, qty in asks:
        taken = min(remaining, price * qty)
        if taken <= 0:
            continue
        acquired += taken / price
        remaining -= taken
        if remaining <= Decimal("0.000000000000001"):
            remaining = Decimal(0)
            break
    return acquired, quote_budget - remaining, remaining


def _sweep_base(bids, base_qty):
    remaining = base_qty
    received = Decimal(0)
    for price, qty in bids:
        taken = min(remaining, qty)
        received += taken * price
        remaining -= taken
        if remaining <= Decimal("0.000000000000001"):
            remaining = Decimal(0)
            break
    return received, remaining


def _floor_step(value, step):
    if step == 0:
        return value
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def _filters(symbol_info):
    filters = {f["filterType"]: f for f in symbol_info.get("filters", [])}
    lot = filters.get("MARKET_LOT_SIZE") or filters.get("LOT_SIZE")
    if not lot:
        raise ValueError("UNKNOWN_MARKET_LOT_FILTER")
    # A zero market step is legitimate; the SELL quantity needs to respect
    # both the market constraint and base precision. A nonzero LOT_SIZE also
    # provides a conservative floor when MARKET_LOT_SIZE stepSize=0.
    fallback = filters.get("LOT_SIZE", {})
    market_step = nonnegative(lot.get("stepSize"), "MARKET_STEP")
    base_step = nonnegative(fallback.get("stepSize", "0"), "LOT_STEP")
    step = market_step if market_step else base_step
    min_qty = nonnegative(lot.get("minQty", "0"), "MIN_QTY")
    max_qty = positive(lot.get("maxQty"), "MAX_QTY")
    limits = filters.get("NOTIONAL") or filters.get("MIN_NOTIONAL")
    if limits is None:
        raise ValueError("UNKNOWN_NOTIONAL_FILTER")
    min_notional = nonnegative(limits.get("minNotional"), "MIN_NOTIONAL")
    max_notional = positive(limits.get("maxNotional", "1E40"), "MAX_NOTIONAL")
    return step, min_qty, max_qty, min_notional, max_notional


def evaluate_spot_execution(symbol_info, book, observed_ms,
                            budget_usdt=Decimal("30"),
                            assumed_fee_bps=Decimal("10")):
    """Estimate instantaneous, same-book BUY then SELL, with explicit fees.

    Flag API/rule unknown or incomplete books as unverified, never executable.
    The assumed taker fee is not the user's actual fee tier/BNB discount.
    """
    symbol = symbol_info.get("symbol")
    if (not isinstance(symbol, str) or not symbol.endswith("USDT")
            or symbol_info.get("status") != "TRADING"
            or not symbol_info.get("isSpotTradingAllowed", True)
            or symbol_info.get("quoteAsset") != "USDT"):
        raise ValueError("NOT_ACTIVE_USDT_SPOT")
    if not isinstance(observed_ms, int) or observed_ms <= 0:
        raise ValueError("INVALID_OBSERVATION_TIME")
    if not isinstance(book, dict) or not isinstance(book.get("lastUpdateId"), int):
        raise ValueError("INVALID_BOOK_SEQUENCE")
    budget = positive(budget_usdt, "BUDGET")
    fee_bps = nonnegative(assumed_fee_bps, "FEE_BPS")
    if fee_bps >= 10000:
        raise ValueError("INVALID_FEE_BPS")
    asks = _book_side(book.get("asks"), "ASKS")
    bids = _book_side(book.get("bids"), "BIDS")
    if bids[0][0] >= asks[0][0]:
        raise ValueError("CROSSED_BOOK")
    step, min_qty, max_qty, min_notional, max_notional = _filters(symbol_info)
    mid = (bids[0][0] + asks[0][0]) / 2
    spread_bps = (asks[0][0] - bids[0][0]) / mid * 10000
    bought_base, quote_spent, buy_unfilled = _sweep_quote(asks, budget)
    # Conservative assumption: buy fee debited in base, sell fee in quote.
    post_buy_fee_base = bought_base * (1 - fee_bps / 10000)
    sellable_base = _floor_step(post_buy_fee_base, step)
    quote_before_sell_fee, sell_unfilled_base = _sweep_base(bids, sellable_base)
    quote_after_sell_fee = quote_before_sell_fee * (1 - fee_bps / 10000)
    roundtrip_loss = budget - quote_after_sell_fee
    roundtrip_bps = roundtrip_loss / budget * 10000
    buy_avg = quote_spent / bought_base if bought_base > 0 else None
    sell_avg = quote_before_sell_fee / (sellable_base - sell_unfilled_base) if (
        sellable_base - sell_unfilled_base > 0) else None
    size_ok = (sellable_base >= min_qty and sellable_base <= max_qty)
    notional_ok = (quote_spent >= min_notional and
                   quote_spent <= max_notional and
                   quote_before_sell_fee >= min_notional)
    fill_ok = (buy_unfilled == 0 and sell_unfilled_base == 0 and
               bought_base > 0 and sellable_base > 0)
    executable_proxy = fill_ok and size_ok and notional_ok
    # RESEARCH FILTER ONLY; not a buy recommendation.
    research_gate = (executable_proxy and
                     spread_bps <= D2_RESEARCH_MAX_SPREAD_BPS and
                     roundtrip_bps <= D2_RESEARCH_MAX_ROUNDTRIP_BPS)
    as_float = lambda x: float(x) if x is not None else None
    return {
        "source": "BINANCE_SPOT_PUBLIC_ORDERBOOK",
        "symbol": symbol, "venue": "spot", "observed_ms": observed_ms,
        "book_last_update_id_not_timestamp": book["lastUpdateId"],
        "book_levels": {"bid": len(bids), "ask": len(asks)},
        "budget_usdt": as_float(budget),
        "fee_assumption_bps_per_side": as_float(fee_bps),
        "fee_source": "USER_UNCONFIRMED_SCENARIO",
        "best_bid": str(bids[0][0]), "best_ask": str(asks[0][0]),
        "spread_bps": as_float(spread_bps),
        "buy_average_price": str(buy_avg) if buy_avg is not None else None,
        "sell_average_price": str(sell_avg) if sell_avg is not None else None,
        "base_bought_gross": str(bought_base),
        "base_sellable_after_fee_and_step": str(sellable_base),
        "buy_quote_unfilled": str(buy_unfilled),
        "sell_base_unfilled": str(sell_unfilled_base),
        "quote_received_after_roundtrip": str(quote_after_sell_fee),
        "instant_roundtrip_loss_usdt": as_float(roundtrip_loss),
        "instant_roundtrip_cost_bps": as_float(roundtrip_bps),
        "min_qty_pass": size_ok, "notional_pass": notional_ok,
        "depth_fully_filled": fill_ok,
        "snapshot_executable_proxy": executable_proxy,
        "research_liquidity_gate": research_gate,
        "classification": "RESEARCH_LIQUIDITY_NOT_BUY",
        "not_verified": [
            "ACTUAL_EXECUTION", "FUTURE_PRICE", "FORWARD_PNL",
            "USER_REAL_FEES", "ORDERBOOK_AGE_OR_COHERENCE",
            "REAL_TIME_LATENCY", "TAXES"
        ]
    }


def get_spot_execution_snapshot(symbol, budget="30", fee_bps="10"):
    if not symbol.isascii() or not symbol.isalnum() or not symbol.endswith("USDT"):
        raise ValueError("INVALID_SYMBOL")
    obs_ms = int(time.time() * 1000)
    info = binance_json(SPOT_API + "/api/v3/exchangeInfo?symbol=" + symbol)
    if len(info.get("symbols", [])) != 1:
        raise ValueError("SYMBOL_NOT_RETURNED")
    book = binance_json(SPOT_API + "/api/v3/depth?symbol=" + symbol +
                        "&limit=" + str(D2_BOOK_LEVELS))
    return evaluate_spot_execution(info["symbols"][0], book, obs_ms,
                                   budget_usdt=budget, assumed_fee_bps=fee_bps)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--budget-usdt", default="30")
    parser.add_argument("--fee-bps", default="10")
    parser.add_argument("--output", type=Path)
    a = parser.parse_args()
    result = get_spot_execution_snapshot(a.symbol, a.budget_usdt, a.fee_bps)
    report = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
