#!/usr/bin/env python3
"""Stage163 fixed Spot T0: read-only, all-market archived HTTP quote friction.

One point-in-time *descriptive* bookTicker + 24hr ticker analysis; NOT a signal
model, PIT 7-day replay, fill quote, liquidity warranty, or trade execution.
No HTTP, private keys, notifications, orders, schedules, or SQLite.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import zipfile

try:
    import monster_v4_stage163_spot_one_shot_raw_http_source as original
except ImportError:
    from scripts import monster_v4_stage163_spot_one_shot_raw_http_source as original

ROOT = Path(__file__).resolve().parents[2] / "monster"
ARCHIVE = ROOT / "evidence" / "monster_stage163_spot_original_http_t0_actual"
ZIP = ARCHIVE / "source_raw_http.zip"
RECEIPTS = ARCHIVE / "source_receipts.json"
ZIP_SHA256 = "b47e206345c0a04b16b37c38795d726553ef83ca679f443f9fba89805483216b"
T0_MS = 1792274680094
EXPECTED_ACTIVE = 511
SCHEMA = "MONSTER_STAGE163_SPOT_T0_ORIGINAL511_BBO_FRICTION_NO_TRADES_V1"
TEN_THOUSAND = Decimal("10000")


def dec(value):
    try:
        x = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("STAGE163_BAD_DECIMAL_SOURCE") from exc
    if not x.is_finite():
        raise ValueError("STAGE163_NONFINITE_SOURCE_PRICE_OR_QUANTITY")
    return x


def fmt(x, places=6):
    return format(x.quantize(Decimal(1).scaleb(-places)), "f")


def percentile(values, p):
    if not values:
        raise ValueError("STAGE163_EMPTY_PERCENTILE")
    ordered = sorted(values)
    index = ((len(ordered) - 1) * p) // 100
    return fmt(ordered[index], 6)


def load_archived(zip_path=ZIP, receipts_path=RECEIPTS):
    raw_zip = Path(zip_path).read_bytes()
    receipt_bytes = Path(receipts_path).read_bytes()
    if hashlib.sha256(raw_zip).hexdigest() != ZIP_SHA256:
        raise ValueError("STAGE163_ARCHIVED_T0_SOURCE_ZIP_SHA_DRIFT")
    m = json.loads(receipt_bytes)
    if (m.get("schema") != original.SCHEMA or
        m.get("source_zip_sha256") != ZIP_SHA256 or
        m.get("stats", {}).get("source_server_time_ms") != T0_MS):
        raise ValueError("STAGE163_ARCHIVED_T0_RECEIPT_IDENTITY_DRIFT")
    endpoints = {name for name, _ in original.ENDPOINTS}
    if set(m["source_sha_receipts"]) != endpoints:
        raise ValueError("STAGE163_ARCHIVED_T0_RECEIPT_ENDPOINT_DRIFT")
    with zipfile.ZipFile(zip_path) as z:
        expected = {name + ".response.raw.json" for name in endpoints}
        expected.add("source_manifest.json")
        if set(z.namelist()) != expected or len(z.namelist()) != len(expected):
            raise ValueError("STAGE163_ARCHIVED_T0_ZIP_MEMBER_DRIFT")
        blobs = {}
        for name in endpoints:
            receipt = m["source_sha_receipts"][name]
            raw = z.read(name + ".response.raw.json")
            if (len(raw) != receipt["body_byte_length"] or
                hashlib.sha256(raw).hexdigest() != receipt["body_sha256"] or
                receipt["http_status"] != 200 or
                not receipt["url"].startswith(original.BASE + "/api/v3/")):
                raise ValueError("STAGE163_ARCHIVED_T0_ORIGINAL_HTTP_SHA_DRIFT:" + name)
            blobs[name] = json.loads(raw)
        inner = json.loads(z.read("source_manifest.json"))
        if (inner.get("source_sha_receipts") != m["source_sha_receipts"]
            or inner.get("stats") != m["stats"]
            or inner.get("source_venue") != "Binance Spot"):
            raise ValueError("STAGE163_ARCHIVED_T0_MANIFEST_DRIFT")
    return blobs, m


def evaluate(blobs, receipts, research_notional=None):
    info = blobs["exchangeInfo"]
    if int(info["serverTime"]) != T0_MS:
        raise ValueError("STAGE163_NOT_FROZEN_T0")
    universe = [s for s in info["symbols"] if s.get("quoteAsset") == "USDT"
                and s.get("isSpotTradingAllowed") is not False
                and s.get("status") == "TRADING"]
    if len(universe) != EXPECTED_ACTIVE:
        raise ValueError("STAGE163_FULL511_FROZEN_COHORT_CHANGED")
    names = [s["symbol"] for s in universe]
    if len(names) != len(set(names)):
        raise ValueError("STAGE163_SPOT_UNIVERSE_DUPLICATE")
    for kind in ("bookTicker", "ticker24"):
        entries = blobs[kind]
        if not isinstance(entries, list) or len({r["symbol"] for r in entries}) != len(entries):
            raise ValueError("STAGE163_MARKET_ROWS_DUPLICATE_OR_MISSING:" + kind)
    books = {x["symbol"]: x for x in blobs["bookTicker"]}
    tickers = {x["symbol"]: x for x in blobs["ticker24"]}
    missing = sorted(set(names) - set(books) | set(names) - set(tickers))
    if missing:
        raise ValueError("STAGE163_T0_BBO_OR_24H_SOURCE_MISSING:" + ",".join(missing[:5]))
    if research_notional is not None:
        n = dec(research_notional)
        if n <= 0:
            raise ValueError("STAGE163_RESEARCH_NOTIONAL_MUST_BE_POSITIVE")
    else:
        n = None
    rows = []
    for s in sorted(universe, key=lambda v: v["symbol"]):
        name = s["symbol"]
        book, ticker = books[name], tickers[name]
        bid, ask = dec(book["bidPrice"]), dec(book["askPrice"])
        bqty, aqty = dec(book["bidQty"]), dec(book["askQty"])
        volume = dec(ticker["quoteVolume"])
        if bid <= 0 or ask < bid or bqty < 0 or aqty < 0 or volume < 0:
            raise ValueError("STAGE163_T0_INVALID_BBO_OR_24H_VOLUME:" + name)
        bid_n, ask_n = bid * bqty, ask * aqty
        spread = TEN_THOUSAND * (ask - bid) / ((ask + bid) / 2)
        cross = TEN_THOUSAND * (ask - bid) / ask
        row = {
            "symbol": name,
            "venue": "BINANCE_SPOT",
            "best_bid_usdt": str(bid), "best_ask_usdt": str(ask),
            "best_bid_quantity": str(bqty), "best_ask_quantity": str(aqty),
            "displayed_bid_notional_usdt": fmt(bid_n, 6),
            "displayed_ask_notional_usdt": fmt(ask_n, 6),
            "24h_rolling_quote_volume_usdt": fmt(volume, 6),
            "instantaneous_top_quote_spread_bps": fmt(spread),
            "instantaneous_cross_quote_loss_bps_before_fees": fmt(cross),
            "both_sides_show_positive_size": bqty > 0 and aqty > 0,
        }
        if n is not None:
            # This is only a *single-snapshot displayed top-level* size check.
            # It says nothing about later exit L2, actual fills or executable P&L.
            row["optional_research_notional_both_top_quotes_show_size"] = (
                ask_n >= n and bid_n >= n)
        rows.append(row)
    spreads = [dec(r["instantaneous_top_quote_spread_bps"]) for r in rows]
    losses = [dec(r["instantaneous_cross_quote_loss_bps_before_fees"]) for r in rows]
    askdepth = [dec(r["displayed_ask_notional_usdt"]) for r in rows]
    biddepth = [dec(r["displayed_bid_notional_usdt"]) for r in rows]
    volumes = [dec(r["24h_rolling_quote_volume_usdt"]) for r in rows]
    if len(rows) != EXPECTED_ACTIVE:
        raise ValueError("STAGE163_T0_511_ROWS_NOT_RETAINED")
    result = {
        "schema": SCHEMA, "source": "ARCHIVED_BINANCE_SPOT_OFFICIAL_HTTP_T0",
        "source_zip_sha256": ZIP_SHA256, "exchange_server_time_ms": T0_MS,
        "exchange_server_time_utc": datetime.fromtimestamp(T0_MS / 1000, timezone.utc).isoformat().replace("+00:00", "Z"),
        "quote_collection_window_utc": {
            kind: [receipts["source_sha_receipts"][kind]["start_utc"],
                   receipts["source_sha_receipts"][kind]["end_utc"]]
            for kind in ("bookTicker", "ticker24")},
        "t0_active_spot_usdt_denominator": EXPECTED_ACTIVE,
        "symbols_represent_complete_511_source_cohort": True,
        "displayed_positive_size_both_sides": sum(r["both_sides_show_positive_size"] for r in rows),
        "quote_spread_bps_p10_median_p90": [percentile(spreads, p) for p in (10, 50, 90)],
        "instantaneous_cross_quote_loss_before_fees_bps_p10_median_p90": [
            percentile(losses, p) for p in (10, 50, 90)],
        "best_ask_displayed_notional_usdt_p10_median_p90": [percentile(askdepth, p) for p in (10, 50, 90)],
        "best_bid_displayed_notional_usdt_p10_median_p90": [percentile(biddepth, p) for p in (10, 50, 90)],
        "rolling_24h_quote_volume_usdt_p10_median_p90": [percentile(volumes, p) for p in (10, 50, 90)],
        "research_notional_is_user_supplied_only": n is not None,
        "research_notional_usdt": str(n) if n is not None else "UNKNOWN_NOT_SPECIFIED",
        "research_notional_top_quote_size_coverage": {
            "count": sum(r["optional_research_notional_both_top_quotes_show_size"] for r in rows),
            "denominator": EXPECTED_ACTIVE,
        } if n is not None else "NOT_EVALUATED_WITHOUT_EXPLICIT_RESEARCH_AMOUNT",
        "original_exited_24h_funding_economics": "NOT_SCORABLE",
        "bid_ask_venues_not_simultaneous": True,
        "no_historical_exit_L2": True, "no_observed_actual_fills": True,
        "quote_is_not_trade_guarantee": True,
        "current_market_quote": False,
        "historical_T0_observed_once_not_forward_live_signal": True,
        "true_full_forward_spot_7d": "NOT_YET_MATURE",
        "user_fee_tier": "UNKNOWN", "G4": "UNKNOWN", "G6": "NO_GO",
        "NO_MERGE": True, "NO_DEPLOY": True, "NO_GMAIL": True, "NO_TRADE": True,
        "rows": rows,
    }
    return result


def main():
    p = argparse.ArgumentParser(description="Read-only 511 Spot archived T0 quote friction")
    p.add_argument("--output", type=Path)
    p.add_argument("--research-notional-usdt", help="Optional research sensitivity; never inferred or traded")
    args = p.parse_args()
    blobs, receipts = load_archived()
    d = evaluate(blobs, receipts, args.research_notional_usdt)
    if args.output:
        if args.output.exists():
            raise ValueError("STAGE163_REPORT_REFUSE_OVERWRITE")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as f:
            json.dump(d, f, sort_keys=True, indent=2, ensure_ascii=False)
            f.write("\n")
    summary = {k:v for k,v in d.items() if k != "rows"}
    print("MONSTER_STAGE163_ORIGINAL511_QUOTE_FRICTION_ONLY", json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
