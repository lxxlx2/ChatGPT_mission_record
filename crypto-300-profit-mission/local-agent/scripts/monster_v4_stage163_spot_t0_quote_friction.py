#!/usr/bin/env python3
"""Stage163 post-T0 archived Spot/USDT bookTicker friction, reference T0 identity.

One point-in-time *descriptive* bookTicker + 24hr ticker analysis; NOT a signal
model, PIT 7-day replay, fill quote, liquidity warranty, or trade execution.
No HTTP, private keys, notifications, orders, schedules, or SQLite.
"""
import argparse
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
SCHEMA = "MONSTER_STAGE163_SPOT_POST_T0_CLOCK_BRIDGED_511_FRICTION_NO_TRADES_V3"
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

def parse_utc(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("STAGE163_NAIVE_CLIENT_TIMESTAMP")
    return stamp.astimezone(timezone.utc)


def millis(delta):
    return Decimal((delta.days * 86400 + delta.seconds) * 1000000 +
                   delta.microseconds) / Decimal(1000)


def clock_bridge(blobs, receipts):
    """Source-bounded server/client clock offset; not an exchange quote event time."""
    samples = {}
    bounds = []
    for key in ("clock_before", "clock_after"):
        obj = receipts["source_sha_receipts"][key]
        start, end = parse_utc(obj["start_utc"]), parse_utc(obj["end_utc"])
        if start > end:
            raise ValueError("STAGE163_CLOCK_BRIDGE_CHRONOLOGY_INVALID")
        midpoint = start + (end - start) / 2
        server = datetime.fromtimestamp(int(blobs[key]["serverTime"]) / 1000, timezone.utc)
        offset = millis(server - midpoint)
        half = millis(end - start) / 2
        low, high = offset - half, offset + half
        bounds.extend((low, high))
        samples[key] = {
            "server_minus_client_midpoint_ms": fmt(offset, 3),
            "client_half_request_window_ms": fmt(half, 3),
            "server_minus_client_lower_ms": fmt(low, 3),
            "server_minus_client_upper_ms": fmt(high, 3),
            "client_start_utc": obj["start_utc"],
            "client_end_utc": obj["end_utc"],
            "server_time_ms": int(blobs[key]["serverTime"]),
        }
    before = parse_utc(receipts["source_sha_receipts"]["clock_before"]["end_utc"])
    startbook = parse_utc(receipts["source_sha_receipts"]["bookTicker"]["start_utc"])
    endbook = parse_utc(receipts["source_sha_receipts"]["bookTicker"]["end_utc"])
    startticker = parse_utc(receipts["source_sha_receipts"]["ticker24"]["start_utc"])
    endticker = parse_utc(receipts["source_sha_receipts"]["ticker24"]["end_utc"])
    after = parse_utc(receipts["source_sha_receipts"]["clock_after"]["start_utc"])
    if not (before <= startbook <= endbook <= startticker <= endticker <= after):
        raise ValueError("STAGE163_CROSS_ENDPOINT_RECEIPT_CHRONOLOGY_INVALID")
    lower, upper = min(bounds), max(bounds)
    return {
        "samples": samples,
        "server_minus_client_envelope_ms": [fmt(lower, 3), fmt(upper, 3)],
        "sampling_model": "server_time_at_unknown_instant_inside_client_request_RTT",
        "clock_drift_between_samples": "UNVERIFIED",
        "conditional_interval_not_certified_exchange_event_timestamp": True,
    }, lower, upper


def receipt_offsets(receipts):
    """Client receipt bounds relative to exchangeInfo SERVER T0, NOT quote times.

    Cross-clock offsets are approximate, not proof of exchange event time.
    Fail if a declared post-T0 endpoint starts before T0 or time goes backwards.
    """
    reference = datetime.fromtimestamp(T0_MS / 1000, timezone.utc)
    result = {}
    ends = []
    for kind in ("bookTicker", "ticker24"):
        receipt = receipts["source_sha_receipts"][kind]
        start, end = parse_utc(receipt["start_utc"]), parse_utc(receipt["end_utc"])
        if start.tzinfo is None or end.tzinfo is None or start > end:
            raise ValueError("STAGE163_POST_T0_RECEIPT_CHRONOLOGY_INVALID")
        def offset_ms(dt):
            delta = dt - reference
            micros = (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds
            return format(Decimal(micros) / Decimal(1000), ".3f")
        first, last = offset_ms(start), offset_ms(end)
        if Decimal(first) < 0 or Decimal(last) < 0:
            raise ValueError("STAGE163_NOT_POST_T0_RECEIPT_WINDOW")
        result[kind] = {"start_utc": receipt["start_utc"],
                        "end_utc": receipt["end_utc"],
                        "start_offset_from_exchange_t0_ms_approx": first,
                        "end_offset_from_exchange_t0_ms_approx": last}
        ends.append(end)
    return result, max(ends).isoformat(timespec="microseconds").replace("+00:00", "Z")


def evaluate(blobs, receipts, research_notional=None):
    info = blobs["exchangeInfo"]
    if int(info["serverTime"]) != T0_MS:
        raise ValueError("STAGE163_NOT_FROZEN_T0")
    receipt_bound_windows, quote_bundle_available_after_utc = receipt_offsets(receipts)
    bridge, clock_low, clock_high = clock_bridge(blobs, receipts)
    for window in receipt_bound_windows.values():
        for phase in ("start", "end"):
            nominal = Decimal(window[phase + "_offset_from_exchange_t0_ms_approx"])
            window[phase + "_clock_bridged_lower_ms_conditional"] = fmt(nominal + clock_low, 3)
            window[phase + "_clock_bridged_upper_ms_conditional"] = fmt(nominal + clock_high, 3)
        if Decimal(window["start_clock_bridged_lower_ms_conditional"]) <= 0:
            raise ValueError("STAGE163_POST_T0_NOT_PROVEN_UNDER_CLOCK_BRIDGE")
    all_exchange = info["symbols"]
    if len({s["symbol"] for s in all_exchange}) != len(all_exchange):
        raise ValueError("STAGE163_EXCHANGEINFO_DUPLICATE_SYMBOL")
    usdt = [s for s in all_exchange if s.get("quoteAsset") == "USDT"]
    usdt_trading = [s for s in usdt if s["status"] == "TRADING"]
    usdt_break = [s for s in usdt if s["status"] == "BREAK"]
    usdt_other_states = [s for s in usdt if s["status"] not in ("TRADING", "BREAK")]
    eligible_trading = [s for s in usdt_trading if s.get("isSpotTradingAllowed") is not False]
    universe = eligible_trading
    # T0 universe is USDT+TRADING+Spot-allowed only, not ALL Binance Spot.
    # No silently converted BREAK instruments, other quote assets, or new listings.
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
    exchange_ids = {s["symbol"] for s in all_exchange}
    book_only_new_symbols = sorted(set(books) - exchange_ids)
    ticker_only_new_symbols = sorted(set(tickers) - exchange_ids)
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
        quote_status = ("LOCKED_QUOTE" if ask == bid else
                        "ZERO_DISPLAYED_SIZE" if bqty == 0 or aqty == 0 else
                        "DISPLAYED_TWO_SIDED")
        depth_evaluable = quote_status == "DISPLAYED_TWO_SIDED"
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
            "post_t0_bookticker_spread_bps": fmt(spread),
            "post_t0_bookticker_cross_loss_before_fees_bps": fmt(cross),
            "both_sides_show_positive_size": bqty > 0 and aqty > 0,
            "quote_status": quote_status,
            "displayed_depth_distribution_evaluable": depth_evaluable,
            "locked_quote_zero_spread": ask == bid,
        }
        if n is not None:
            # This is only a *single-snapshot displayed top-level* size check.
            # It says nothing about later exit L2, actual fills or executable P&L.
            row["optional_research_notional_displayed_top_quote_size_only"] = (
                depth_evaluable and ask_n >= n and bid_n >= n)
        rows.append(row)
    spreads = [dec(r["post_t0_bookticker_spread_bps"]) for r in rows]
    losses = [dec(r["post_t0_bookticker_cross_loss_before_fees_bps"]) for r in rows]
    depth_rows = [r for r in rows if r["displayed_depth_distribution_evaluable"]]
    askdepth = [dec(r["displayed_ask_notional_usdt"]) for r in depth_rows]
    biddepth = [dec(r["displayed_bid_notional_usdt"]) for r in depth_rows]
    volumes = [dec(r["24h_rolling_quote_volume_usdt"]) for r in rows]
    if len(rows) != EXPECTED_ACTIVE:
        raise ValueError("STAGE163_T0_511_ROWS_NOT_RETAINED")
    def depth_quantiles(values):
        return [percentile(values, p) for p in (10, 50, 90)] if values else "NO_DISPLAYED_TWO_SIDED_DEPTH"
    statuses = {kind: sum(r["quote_status"] == kind for r in rows)
                for kind in ("DISPLAYED_TWO_SIDED", "LOCKED_QUOTE", "ZERO_DISPLAYED_SIZE")}
    result = {
        "schema": SCHEMA, "source": "ARCHIVED_BINANCE_SPOT_OFFICIAL_HTTP_POST_T0_BOOKTICKER",
        "source_zip_sha256": ZIP_SHA256, "exchange_server_time_ms": T0_MS,
        "exchange_server_time_utc": datetime.fromtimestamp(T0_MS / 1000, timezone.utc).isoformat().replace("+00:00", "Z"),
        "post_t0_receipt_windows_vs_exchangeinfo_t0_approx": receipt_bound_windows,
        "clock_bridge_calibration": bridge,
        "quote_bundle_not_available_until_client_receipt_utc": quote_bundle_available_after_utc,
        "receipt_offsets_are_cross_clock_approx_not_exchange_quote_event_timestamps": True,
        "t0_causal_quote_at_t0_proven": False,
        "eligible_for_t0_asof_executable_execution_or_signal_backtest": False,
        "t0_active_spot_usdt_denominator": len(universe),
        "population_definition": "USDT_quote_AND_TRADING_AND_spot_trading_allowed_not_false_at_exchangeInfo_T0",
        "population_scope_is_all_binance_spot": False,
        "population_counts_from_exchangeinfo": {
            "all_exchange_symbol_records": len(all_exchange),
            "usdt_all_statuses_including_spot_disallowed": len(usdt),
            "usdt_trading_any_spot_permission": len(usdt_trading),
            "usdt_trading_spot_allowed": len(eligible_trading),
            "usdt_trading_spot_disallowed": len(usdt_trading)-len(eligible_trading),
            "usdt_break_all_spot_permissions": len(usdt_break),
            "usdt_break_spot_allowed": sum(s.get("isSpotTradingAllowed") is not False for s in usdt_break),
            "usdt_break_spot_disallowed": sum(s.get("isSpotTradingAllowed") is False for s in usdt_break),
            "usdt_other_states": len(usdt_other_states),
        },
        "excluded_market_symbols_not_in_exchangeinfo": {
            "bookTicker": book_only_new_symbols, "ticker24": ticker_only_new_symbols,
        },
        "complete_archived_exchangeinfo_t0_eligible_cohort_represented": (
            len(rows)==len(eligible_trading) and
            set(r["symbol"] for r in rows)==set(s["symbol"] for s in eligible_trading) and
            all(s["symbol"] in books and s["symbol"] in tickers for s in eligible_trading)),

        "displayed_positive_size_both_sides": sum(r["both_sides_show_positive_size"] for r in rows),
        "quote_status_counts": statuses,
        "displayed_depth_distribution_evaluable_count": len(depth_rows),
        "displayed_depth_percentiles_exclude_zero_and_locked_quotes": True,
        "post_t0_bookticker_spread_bps_p10_median_p90": [percentile(spreads, p) for p in (10, 50, 90)],
        "post_t0_same_bookticker_cross_loss_before_fees_bps_p10_median_p90": [
            percentile(losses, p) for p in (10, 50, 90)],
        "best_ask_displayed_notional_usdt_p10_median_p90": depth_quantiles(askdepth),
        "best_bid_displayed_notional_usdt_p10_median_p90": depth_quantiles(biddepth),
        "rolling_24h_quote_volume_usdt_p10_median_p90": [percentile(volumes, p) for p in (10, 50, 90)],
        "research_notional_is_user_supplied_only": n is not None,
        "research_notional_usdt": str(n) if n is not None else "UNKNOWN_NOT_SPECIFIED",
        "research_notional_displayed_top_level_size_coverage_only": {
            "count": sum(r["optional_research_notional_displayed_top_quote_size_only"] for r in rows),
            "denominator": EXPECTED_ACTIVE,
        } if n is not None else "NOT_EVALUATED_WITHOUT_EXPLICIT_RESEARCH_AMOUNT",
        "original_exited_24h_funding_economics": "NOT_SCORABLE",
        "market_endpoint_snapshots_not_atomic": True,
        "no_historical_exit_L2": True, "no_observed_actual_fills": True,
        "quote_is_not_trade_guarantee": True,
        "current_market_quote": False,
        "historical_post_t0_quote_receipts_once_not_forward_live_signal": True,
        "true_full_forward_spot_7d": "NOT_YET_MATURE",
        "user_fee_tier": "UNKNOWN", "G4": "UNKNOWN", "G6": "NO_GO",
        "NO_MERGE": True, "NO_DEPLOY": True, "NO_GMAIL": True, "NO_TRADE": True,
        "rows": rows,
    }
    return result


def main():
    p = argparse.ArgumentParser(description="Read-only 511 Spot post-T0 receipt bounded quote friction")
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
    print("MONSTER_STAGE163_CLOCK_BRIDGED_POST_T0_QUOTE_ONLY", json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
