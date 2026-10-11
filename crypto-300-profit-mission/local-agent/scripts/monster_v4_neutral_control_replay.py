#!/usr/bin/env python3
"""Stage10: market-time-neutral, pre-registered controls using REAL V4 D0/D1.

Selection was committed before historical Binance queries. This is a
currently-listed-only survivor cohort and small 12h windows, NOT an unbiased
historical-market false-positive rate or an out-of-sample trading validation.
"""
import argparse
import json
import statistics
from pathlib import Path

try:
    import monster_v4_historical_replay as replay
except ImportError:
    from scripts import monster_v4_historical_replay as replay

EVIDENCE = replay.EVIDENCE
MANIFEST = EVIDENCE / "monster_stage10_neutral_preregistered_24case_20261011.json"
FETCH = EVIDENCE / "monster_stage10_fetch_status_20261011.json"


def fnv1a32(value):
    h = 2166136261
    for char in value:
        h = ((h ^ ord(char)) * 16777619) & 0xffffffff
    return h


def validate_registration(manifest, fetch):
    universe = manifest["universe_symbols"]
    if len(universe) != manifest["universe_count"] or len(set(universe)) != len(universe):
        raise ValueError("UNIVERSE_NOT_FROZEN")
    selected = manifest["selected"]
    anchors = manifest["anchors_utc"]
    if len(selected) != 24 or len(anchors) != 6 or len(set(x["symbol"] for x in selected)) != 24:
        raise ValueError("INVALID_PRECOMMITTED_SAMPLE")
    recalculated = []
    used = set()
    for date_anchor in anchors:
        date = date_anchor[:10]
        ordered = sorted(universe, key=lambda sym: (
            fnv1a32(manifest["study_seed"] + "|" + date + "|" + sym), sym))
        choices = [symbol for symbol in ordered if symbol not in used][:4]
        for symbol in choices:
            used.add(symbol)
            recalculated.append((symbol, date_anchor,
                                 fnv1a32(manifest["study_seed"] + "|" + date + "|" + symbol)))
    if recalculated != [(x["symbol"], x["anchor_utc"], x["fnv1a32"]) for x in selected]:
        raise ValueError("SELECTION_NOT_REPRODUCIBLE")
    unavailable = fetch["unavailable"]
    if len(unavailable) != 7 or fetch["n"] != len(selected):
        raise ValueError("SOURCE_STATUS_INCOMPLETE")
    registered = {(x["symbol"], x["anchor_utc"]) for x in selected}
    refused = {(x["symbol"], x["anchor_utc"]) for x in unavailable}
    if not refused.issubset(registered) or len(refused) != len(unavailable):
        raise ValueError("UNREGISTERED_SOURCE_EXCLUSION")
    if any(x["first_returned_bar_ms"] <= x["requested_start_ms"] for x in unavailable):
        raise ValueError("INVALID_SOURCE_CENSORSHIP")
    return selected, refused


def run():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fetch = json.loads(FETCH.read_text(encoding="utf-8"))
    selected, unavailable = validate_registration(manifest, fetch)
    result = []
    sparse_result = []
    excluded = []
    returned = []
    for item in selected:
        symbol, anchor = item["symbol"], item["anchor_utc"]
        if (symbol, anchor) in unavailable:
            excluded.append({"symbol": symbol, "anchor_utc": anchor,
                             "reason": "SOURCE_PREHISTORY_NOT_AVAILABLE"})
            continue
        filename = EVIDENCE / (
            "monster_stage10_neutral_1m_spot_" + symbol + "_" + anchor[:10] + ".json")
        if not filename.is_file():
            raise ValueError("MISSING_PRE_REGISTERED_BAR_SOURCE:" + filename.name)
        src, bars = replay.load_case(filename)
        if (src["symbol"], src["venue"], src["cohort"], src["old_watch_utc"]) != (
                symbol, "spot", "STAGE10_PRE_REGISTERED_NEUTRAL", anchor):
            raise ValueError("SOURCE_IDENTITY_DOES_NOT_MATCH_MANIFEST")
        if src.get("anchor_semantics") != "HASH_PREREGISTERED_CALENDAR_ANCHOR_NOT_PRIOR_WATCH":
            raise ValueError("MISSING_ANCHOR_CAVEAT")
        sparse = replay.replay_case(src, bars)
        actual = replay.replay_case(src, bars, include_zero_trade_ticks=True)
        sparse_result.append(sparse)
        result.append(actual)
        for t in actual["trade_proxies"]:
            a = t["scenario_0_20_100bps"]["20"]
            if a["status"] == "PRICE_PROXY_ONLY":
                returned.append(a["net_pct"])
    if len(result) + len(excluded) != len(selected):
        raise ValueError("SILENT_DROPPED_PRE_REGISTERED_CASE")
    hours = 12 * len(result)
    polled = sum(x["polls"] for x in sparse_result)
    skipped_no_trade = sum(x["polls_skipped_no_trade"] for x in sparse_result)
    dense_polled = sum(x["polls"] for x in result)
    if dense_polled != 240 * len(result) or polled + skipped_no_trade != 240 * len(result):
        raise ValueError("UNACCOUNTED_3MIN_OBSERVATIONS")
    counts = {}
    for case in result:
        day = case["old_research_watch_utc"][:10]
        v = counts.setdefault(day, {"valid_symbols": 0, "watches": 0, "setups": 0})
        v["valid_symbols"] += 1
        v["watches"] += case["watch_count"]
        v["setups"] += case["d1_setups"]
    summary = {
        "frozen_candidates": len(selected), "valid_contiguous_60h": len(result),
        "source_not_historically_available": len(excluded),
        "nominal_window_symbol_hours": hours,
        "intended_3m_poll_intervals": 240 * len(result),
        "actual_nonzero_trade_3m_polls": polled,
        "skipped_zero_trade_3m_polls": skipped_no_trade,
        "actual_nonzero_trade_symbol_hours": round(polled * 3 / 60, 3),
        "dense_ticker_continuity_observed_symbol_hours": round(dense_polled * 3 / 60, 3),
        "dense_ticker_continuity_watches": sum(x["watch_count"] for x in result),
        "sparse_zero_trade_skip_watches": sum(x["watch_count"] for x in sparse_result),
        "dense_ticker_continuity_d1_setups": sum(x["d1_setups"] for x in result),
        "sparse_zero_trade_skip_d1_setups": sum(x["d1_setups"] for x in sparse_result),
        "new_watch_symbols_due_to_dense_policy": [x["symbol"] for x,old in zip(result,sparse_result)
            if x["watch_count"] > 0 and old["watch_count"] == 0],
        "zero_trade_skip_ratio": round(skipped_no_trade / (240 * len(result)), 6),
        "watched_symbols": sum(v["watch_count"] > 0 for v in result),
        "watches": sum(v["watch_count"] for v in result),
        "d1_setup_symbols": sum(v["d1_setups"] > 0 for v in result),
        "setups": sum(v["d1_setups"] for v in result),
        "proxy_exits_n": len(returned),
        "proxy_30usd_net_24h_median_pct": round(statistics.median(returned), 5) if returned else None,
        "proxy_30usd_positive_cases": sum(x > 0 for x in returned),
        "proxy_30usd_negative_cases": sum(x < 0 for x in returned),
        "per_calendar_day": counts,
    }
    return {
        "schema": "MONSTER_STAGE10_PRE_REGISTERED_NEUTRAL_ACTUAL_V4_REPLAY_V1",
        "classification": "SMALL_SURVIVOR_BIASED_MARKET_NEUTRAL_CONTROL",
        "data_source": "FROZEN_GENUINE_BINANCE_SPOT_1M",
        "method": "EXACT_PRODUCTION_D0_D1_CAUSAL_3M_CLOSE_PRICE_PLUS_1M_ROLLING_24H_QUOTE_PROXY",
        "primary_zero_trade_policy": "DENSE_3M_TICKER_CONTINUITY_PROXY_NOT_ACTUAL_HISTORICAL_TICKER",
        "secondary_zero_trade_policy": "SPARSE_SKIPS_ZERO_TRADE_MINUTE_SENSITIVITY_ONLY",
        "source_cutoff": "ALL_24_FIXED_REGISTRATIONS_INCLUDED_NO_SUBSTITUTION",
        "source_unavailable": excluded,
        "summary": summary,
        "cases": [{
            "symbol": x["symbol"], "anchor_utc": x["old_research_watch_utc"],
            "replay_start_utc": x["replay_start_utc"], "replay_end_utc": x["replay_end_utc"],
            "intended_polls": 240,
            "polls": x["polls"], "polls_skipped_no_trade": x["polls_skipped_no_trade"],
            "zero_trade_last_minute_3m_polls": x["polls_zero_trade_minute"],
            "sparse_policy_polls": sparse_result[i]["polls"],
            "sparse_policy_watches": sparse_result[i]["watch_count"],
            "sparse_policy_setups": sparse_result[i]["d1_setups"],
            "watches": x["watch_count"], "first_watch_utc": x["first_watch_utc"],
            "d1_setups": x["d1_setups"], "trade_proxies": x["trade_proxies"],
        } for i,x in enumerate(result)],
        "unverified": [
            "FULL_HISTORICAL_UNIVERSE", "HISTORICAL_BINANCE_TRUE_24H_TICKER",
            "ACTUAL_HISTORICAL_DEPTH_AND_FEES", "REAL_TRADE_FILLS",
            "LONG_TERM_DAILY_FALSE_POSITIVE_RATE", "PROFITABILITY",
            "ANY_UNSEEN_FORWARD_HOLDOUT", "ACTUAL_NOTIFICATION_DELIVERY",
        ],
        "production_gate": "NO_GO", "independent_ai_review_completed": False
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    txt = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(txt + "\n", encoding="utf-8")
    print(json.dumps({"STAGE10_NEUTRAL": result["summary"],
                      "PER_CASE": [{k:v for k,v in case.items() if k!="trade_proxies"}
                                   for case in result["cases"]],
                      "SOURCE_EXCLUDED": result["source_unavailable"],
                      "NO_GO": result["production_gate"]}, sort_keys=True))


if __name__ == "__main__":
    main()
