"""Read-only Frank local-trade quantity gap audit; no PnL inference."""
from collections import Counter, defaultdict
from decimal import Decimal

_BUY = {"BUY", "ADD", "REENTRY"}
_SELL = {"SELL", "EXIT", "SELL_POSITION_UNRESOLVED"}
_SOURCE = "COMPLETE_LOCAL_RECOGNIZED_TRADES_NOT_FULL_CHAIN"


def analyze(history, snapshots):
    if (history.get("source_scope") != _SOURCE or
        history.get("record_count") != len(history.get("records", [])) or
        history.get("person_id") != "frank"):
        raise ValueError("INVALID_HISTORY_SOURCE")
    if (snapshots.get("wallet") != "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
        or snapshots.get("commitment") != "finalized"
        or snapshots.get("network") != "solana-mainnet"
        or snapshots.get("status") != "VERIFIED_POINT_IN_TIME_MINT_FILTERED_SOLANA_ACCOUNT_READS"):
        raise ValueError("INVALID_SNAPSHOT_SOURCE")
    balances = {}
    for v in snapshots["records"]:
        key = v["mint"]
        if key in balances or not 32 <= len(key) <= 44:
            raise ValueError("INVALID_SNAPSHOT_MINT")
        raw, dec, slot = v["raw_amount"], v["decimals"], v["slot"]
        if (not isinstance(raw, str) or not raw.isascii() or not raw.isdecimal()
            or type(dec) is not int or not 0 <= dec <= 18
            or type(slot) is not int or slot <= 0):
            raise ValueError("INVALID_SNAPSHOT_AMOUNT")
        balances[key] = (Decimal(raw) / (Decimal(10) ** dec), slot)
    groups = defaultdict(list)
    sides = Counter()
    for r in history["records"]:
        if r["side"] not in _BUY | _SELL:
            raise ValueError("INVALID_TRADE_SIDE")
        groups[r["mint"]].append(r)
        sides[r["side"]] += 1
    counts = Counter()
    out = []
    gross_buy = gross_sell = Decimal(0)
    for mint, rows in sorted(groups.items()):
        buy = sell = Decimal(0)
        buys = sells = unresolved = no_after = 0
        usdc_buy = usdc_sell = Decimal(0)
        for r in rows:
            details = r["trade_raw_fields"]
            raw, dec = details.get("token_amount_raw"), details.get("token_decimals")
            if (type(dec) is not int or not 0 <= dec <= 18 or
                not isinstance(raw, str) or not raw.isascii() or not raw.isdecimal()):
                raise ValueError("INVALID_TRADE_UNITS")
            quantity = Decimal(raw) / Decimal(10) ** dec
            if quantity != Decimal(r["observed_token_quantity"]):
                raise ValueError("TOKEN_RAW_AMOUNT_MISMATCH")
            if r["side"] in _BUY:
                buy += quantity
                buys += 1
            else:
                sell += quantity
                sells += 1
            unresolved += r["side"] == "SELL_POSITION_UNRESOLVED"
            no_after += details.get("position_after_raw") is None
            quote = r["observed_quote"]
            if (quote.get("asset") == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
                and quote.get("status") == "LOCAL_USDC_DIRECT_PREDICATE"):
                amount = Decimal(quote["quantity"])
                if not amount.is_finite() or amount < 0:
                    raise ValueError("INVALID_QUOTE")
                if r["side"] in _BUY:
                    usdc_buy += amount
                else:
                    usdc_sell += amount
        net = buy - sell
        dated = balances.get(mint)
        diff = dated[0] - net if dated else None
        counts["snapshot_match" if diff == 0 else
               "snapshot_gap" if diff is not None else "snapshot_missing"] += 1
        counts["sell_only_no_local_buy"] += buys == 0 and sells > 0
        counts["negative_net_with_local_buys"] += net < 0 and buys > 0
        counts["unresolved_sell_events"] += unresolved
        counts["missing_position_after_events"] += no_after
        gross_buy += usdc_buy
        gross_sell += usdc_sell
        out.append({"mint": mint, "buy_events": buys, "sell_events": sells,
                    "unresolved_sell_events": unresolved, "missing_position_after": no_after,
                    "indexed_buy_quantity": str(buy), "indexed_sell_quantity": str(sell),
                    "indexed_net_quantity": str(net),
                    "gross_local_buy_usdc": str(usdc_buy), "gross_local_sell_usdc": str(usdc_sell),
                    "dated_chain_quantity": str(dated[0]) if dated else None,
                    "dated_chain_slot": dated[1] if dated else None,
                    "unexplained_quantity_delta": str(diff) if diff is not None else None,
                    "realized_pnl_usd": None})
    return {"source_scope": _SOURCE, "history_records": len(history["records"]),
            "history_mints": len(groups), "trade_sides": dict(sides),
            "counts": dict(counts), "gross_local_buy_usdc": str(gross_buy),
            "gross_local_sell_usdc": str(gross_sell), "wallet_pnl_usd": None,
            "chain_complete": False, "per_mint": out}
