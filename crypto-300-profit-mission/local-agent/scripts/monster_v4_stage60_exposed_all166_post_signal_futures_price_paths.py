#!/usr/bin/env python3
"""Stage60: 166 original P1v03 decisions, verified USD-M *post-signal* price paths.

No strategy model/threshold fitting, order-size assumption, orderbook fill,
real-world profit claim, trade execution, Gmail or deployment. Full 166 exposed
cohort incl. original delivered and omitted, with all futures sources validated.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import csv
import hashlib
import json
import statistics
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage38_usdm_original_v4_1m_pilot as publisher
except ImportError:
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as publisher

E = Path(__file__).resolve().parents[2] / "monster" / "evidence"
C = E / "monster_stage55_all166_candidate_asof_features_and_fate.csv"
V = E / "monster_stage59_all166_cross_venue_evidence_matrix.jsonl"
S = E / "monster_stage59_all166_venue_evidence_coverage_summary.json"
PIN = {
    C.name: "dca780246adb28e045ed77f0f96eb4bd034fb2e7",
    V.name: "422df2dc1b5decf9596f2ad44e2a8f428e3975ae",
    S.name: "a925ce851df2b12fa5082ade802ff33cd1bf5f19",
}
SCHEMA = "MONSTER_STAGE60_EXPOSED_ALL166_ORIGINAL_P1_SIGNAL_FUTURES_PROXY_15_60_360_1440_V1"
D = Decimal
ONE = 60000
HORIZONS = (15, 60, 360, 1440)
GOOD = "COMPLETE_OFFICIAL_DAILY_USDM_1M_PUBLISHER_SHA_PRICE_PATH"
CENSORED = "CENSORED_OFFICIAL_DAILY_ARCHIVE_UNAVAILABLE"
VENUES = (
    "HISTORIC_BINANCE_SPOT_REAL_TRADES_SHA_VERIFIED",
    "BINANCE_ALPHA_ANNOUNCED_BEFORE_SIGNAL_NO_FILL_VERIFICATION",
    "UNKNOWN_ALTERNATIVE_VENUE_NOT_CHECKED",
)
FUTURE_LABELS = (
    "FUTURE_2X_AND_CANDIDATE_BEFORE_5MIN",
    "FUTURE_2X_BUT_CANDIDATE_LATE",
    "ORDINARY_NOT_CALENDAR_2X",
)


def gitblob(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def frozen():
    for p in (C, V, S):
        if gitblob(p) != PIN[p.name]:
            raise ValueError("STAGE60_FROZEN_SOURCE_GIT_BLOB_CHANGED " + p.name)
    with C.open(newline="", encoding="utf-8") as handle:
        original = list(csv.DictReader(handle))
    venues = [json.loads(s) for s in V.read_text(encoding="utf-8").splitlines() if s]
    prior = json.loads(S.read_text(encoding="utf-8"))
    if len(original) != 166 or len(venues) != 166 or prior["all_original_usdm_candidates"] != 166:
        raise ValueError("STAGE60_NOT_FULL_EXPOSED_166")
    by_venue = {(x["date"], x["futures_symbol"]): x for x in venues}
    if len(by_venue) != 166 or len({(x["date"], x["symbol"]) for x in original}) != 166:
        raise ValueError("STAGE60_DUPLICATE_166")
    for row in original:
        key = (row["date"], row["symbol"])
        item = by_venue.get(key)
        if item is None or item["eligible_timestamp_UTC"] != row["eligible_timestamp_UTC"]:
            raise ValueError("STAGE60_ORIGINAL_CLOCK_OR_VENUE_MISMATCH")
        if row["future_label_AFTER_signal"] not in FUTURE_LABELS or item["venue_evidence_status"] not in VENUES:
            raise ValueError("STAGE60_ORIGINAL_COHORT_LABEL_DRIFT")
        if (row["research_delivered"] == "True") != bool(item["original_priority_research_delivered"]):
            raise ValueError("STAGE60_ORIGINAL_PRIORITY_BUDGET_DRIFT")
    if sum(r["research_delivered"] == "True" for r in original) != 127:
        raise ValueError("STAGE60_ORIGINAL127_BUDGET_FATES_CHANGED")
    return original, by_venue


def asof_ms(iso):
    clock = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if clock.utcoffset() != timedelta(0) or clock.second != 0 or clock.microsecond != 0:
        raise ValueError("STAGE60_BAD_ORIGINAL_UTC_MINUTE_CLOCK")
    return int(clock.timestamp() * 1000)


def pct(price, baseline):
    if baseline <= 0:
        raise ValueError("STAGE60_BAD_PROXY_BASELINE")
    return (price / baseline - 1) * 100


def evaluate_bars(ordered):
    if len(ordered) != 1440:
        raise ValueError("STAGE60_NOT_1440_POST_SIGNAL_SOURCE_MINUTES")
    entry = ordered[0][4]
    if entry <= 0:
        raise ValueError("STAGE60_BAD_FIRST_POST_SIGNAL_CLOSE")
    outcomes = {}
    for h in HORIZONS:
        # Begin at next minute's OPEN after the reference 1m bar has CLOSED.
        later = ordered[1:h]
        if len(later) != h-1:
            raise ValueError("STAGE60_MISSING_PRICE_HORIZON")
        close = ordered[h-1][4]
        max_high = max(b[2] for b in later)
        min_low = min(b[3] for b in later)
        if min(close, max_high, min_low) <= 0:
            raise ValueError("STAGE60_BAD_POST_SIGNAL_OHLC")
        outcomes[str(h)] = {
            "end_close_price": str(close),
            "end_close_return_pct_PROXY": str(pct(close, entry)),
            "later_high_price_NOT_AN_EXIT_FILL": str(max_high),
            "potential_max_high_pct_NOT_AN_EXIT_FILL": str(pct(max_high, entry)),
            "later_low_price_NOT_AN_EXIT_FILL": str(min_low),
            "adverse_min_low_pct_NOT_AN_EXIT_FILL": str(pct(min_low, entry)),
            "all_intrahorizon_bars_closed_after_proxy": True,
        }
    return entry, outcomes


def source_case(row, venue, loader=publisher.verified_1m_day):
    at = asof_ms(row["eligible_timestamp_UTC"])
    last_open = at + (max(HORIZONS)-1) * ONE
    dates = sorted({
        datetime.fromtimestamp(at / 1000, timezone.utc).date(),
        datetime.fromtimestamp(last_open / 1000, timezone.utc).date()
    })
    if len(dates) not in (1, 2):
        raise ValueError("STAGE60_UNEXPECTED_DATE_SPAN")
    common = {
        "date": row["date"], "symbol": row["symbol"],
        "eligible_timestamp_UTC": row["eligible_timestamp_UTC"],
        "original_mode": row["mode"],
        "original_v03_urgent_delivered": row["research_delivered"] == "True",
        "venue_evidence_status": venue["venue_evidence_status"],
        "posthoc_calendar2x_label_EVALUATION_ONLY": row["future_label_AFTER_signal"],
        "USD_M_FUTURES_PRICE_PATH_ONLY": True,
        "FIRST_BAR_AFTER_SIGNAL_PROXY_NOT_A_FILL": True,
        "ORDER_NOTIONAL": None,
        "EXECUTION_PRICE_AND_NET_PROFIT": "UNKNOWN",
        "PRICE_PATH_USED_TO_CHANGE_STRATEGY": False,
    }
    merged, receipts = {}, []
    for day in dates:
        try:
            daily, proof = loader(row["symbol"], day)
        except FileNotFoundError:
            return {
                **common, "source_status": CENSORED,
                "source_missing_official_day": day.isoformat(),
                "source_SHA_receipts_for_available_days": receipts,
                "entry_price_first_post_signal_close_PROXY": None,
                "forward_horizons": None,
            }
        if len(daily) != 1440:
            raise ValueError("STAGE60_VERIFIED_PUBLISHER_DAY_NOT_1440")
        if any(x[0] in merged for x in daily):
            raise ValueError("STAGE60_DUPLICATE_SOURCE_MINUTE")
        merged.update((x[0], x) for x in daily)
        if not proof.get("verified_official_publisher_SHA256"):
            raise ValueError("STAGE60_PUBLISHER_SHA_NOT_VERIFIED")
        receipts.append(proof)
    timeline = [at + i * ONE for i in range(max(HORIZONS))]
    if any(t not in merged for t in timeline):
        return {
            **common, "source_status": "CENSORED_GAPPED_REAL_MINUTE_TIME",
            "source_SHA_receipts_for_available_days": receipts,
            "entry_price_first_post_signal_close_PROXY": None,
            "forward_horizons": None,
        }
    entry, outcomes = evaluate_bars([merged[t] for t in timeline])
    return {
        **common, "source_status": GOOD,
        "source_SHA_receipts_for_available_days": receipts,
        "entry_price_first_post_signal_close_PROXY": str(entry),
        "forward_horizons": outcomes,
    }


def aggregate(group):
    completed = [x for x in group if x["source_status"] == GOOD]
    result = {"count": len(group), "source_complete": len(completed),
              "censored_reasons": dict(sorted(collections.Counter(
                  x["source_status"] for x in group if x["source_status"] != GOOD
              ).items())),
              "horizons": {}}
    for h in HORIZONS:
        label = str(h)
        def decimals(key):
            return [D(x["forward_horizons"][label][key]) for x in completed]
        closes = decimals("end_close_return_pct_PROXY")
        max_up = decimals("potential_max_high_pct_NOT_AN_EXIT_FILL")
        max_dn = decimals("adverse_min_low_pct_NOT_AN_EXIT_FILL")
        result["horizons"][label] = {
            "proxy_close_positive": sum(x > 0 for x in closes),
            "proxy_close_median_pct": str(statistics.median(closes)) if closes else None,
            "max_high_potential_median_pct_NOT_FILL": str(statistics.median(max_up)) if max_up else None,
            "worst_low_median_pct_NOT_FILL": str(statistics.median(max_dn)) if max_dn else None,
            "max_high_at_least_double_from_post_signal_proxy_NOT_FILL": sum(x >= 100 for x in max_up),
        }
    return result


def summarize(all_rows):
    by_budget = {
        "ORIGINAL_DELIVERED": aggregate([r for r in all_rows if r["original_v03_urgent_delivered"]]),
        "ORIGINAL_OVER_BUDGET": aggregate([r for r in all_rows if not r["original_v03_urgent_delivered"]]),
    }
    by_posthoc = {k: aggregate([r for r in all_rows if r["posthoc_calendar2x_label_EVALUATION_ONLY"] == k])
                  for k in FUTURE_LABELS}
    by_venue = {k: aggregate([r for r in all_rows if r["venue_evidence_status"] == k]) for k in VENUES}
    return {
        "schema": SCHEMA,
        "lock_original_github_blobs": PIN,
        "exposed_historic_source_cases": len(all_rows),
        "all": aggregate(all_rows),
        "by_original_urgent_budget_status": by_budget,
        "by_posthoc_calendar2x_label_EVALUATION_ONLY": by_posthoc,
        "by_venue_evidence_type_DESCRIPTIVE_ONLY": by_venue,
        "MFE_IS_NOT_REALIZED_RETURN": True,
        "OHLC_HIGH_LOW_DO_NOT_PROVE_FILL": True,
        "NO_ASSUMED_ORDER_SIZE": True,
        "HISTORIC_SAMPLE_ALREADY_EXPOSED_NOT_HOLDOUT": True,
        "P1V03_FROZEN_VERDICT": "REJECTED",
        "NEW_STRATEGY_FIT": "NOT_DONE",
        "OTHER_AI_REVIEW": "NOT_DONE",
        "MONSTER_DEPLOY": "NO_GO",
        "GMAIL": "OFF",
        "AUTOTRADE": "NO_GO",
    }


def selftest():
    t = asof_ms("2025-02-03T23:55:00Z")
    bars = []
    for i in range(1440):
        p = D(100)+D(i)/D(100)
        bars.append((t+i*ONE,p,p+D("0.2"),p-D("0.2"),p,D(100),10))
    entry, output = evaluate_bars(bars)
    assert entry == 100
    assert D(output["15"]["end_close_return_pct_PROXY"]) == D("0.14")
    assert output["15"]["later_high_price_NOT_AN_EXIT_FILL"] == "100.34"
    assert output["1440"]["end_close_price"] == "114.39"
    # A malicious future candle must not affect earlier horizons.
    damaged = list(bars)
    damaged[100] = (bars[100][0],D(100),D(100000),D(1),D(999),D(100),10)
    _, newer = evaluate_bars(damaged)
    assert newer["15"] == output["15"] and newer["60"] == output["60"]
    assert newer["360"] != output["360"]
    try:
        evaluate_bars(bars[:100])
    except ValueError as exc:
        assert "1440" in str(exc)
    else:
        raise AssertionError("STAGE60_MUST_REFUSE_TRUNCATION")
    print("STAGE60_15_60_360_1440_TIME_CAUSALITY_POST_SIGNAL_PROXY_TEST_PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.out or not 1 <= args.workers <= 8:
        ap.error("--out and 1..8 workers required")
    rows, venue_map = frozen()
    data, errors = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(source_case, r, venue_map[(r["date"], r["symbol"])]): r
            for r in rows
        }
        for future in concurrent.futures.as_completed(futures):
            row = futures[future]
            try:
                data.append(future.result())
            except Exception as exc:
                errors.append({"date": row["date"], "symbol": row["symbol"],
                               "type": type(exc).__name__, "detail": str(exc)[:200]})
            if (len(data)+len(errors)) % 20 == 0:
                print("STAGE60_REAL_USDM_SOURCE_PROGRESS " + json.dumps({
                    "count": len(data)+len(errors), "errors": len(errors)}, sort_keys=True), flush=True)
    if errors or len(data) != 166:
        raise RuntimeError("STAGE60_OFFICIAL_PUBLISHER_SHA_OR_MODEL_HARD_ERROR " +
                           json.dumps(errors[:25], sort_keys=True))
    data.sort(key=lambda r: (r["date"], r["symbol"]))
    result = summarize(data)
    if sum(result["all"]["censored_reasons"].values()) + result["all"]["source_complete"] != 166:
        raise ValueError("STAGE60_166_EVIDENCE_NOT_ACCOUNTED")
    if sum(x["original_v03_urgent_delivered"] for x in data) != 127:
        raise ValueError("STAGE60_ORIGINAL_CAP_CHANGED")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "monster_stage60_all166_signal_to_24h_verified_futures_price_proxy.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True, ensure_ascii=False)+"\n" for r in data),
        encoding="utf-8")
    (args.out / "monster_stage60_full166_signal_price_paths_summary.json").write_text(
        json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print("STAGE60_FULL166_EXPOSED_REAL_USDM_POST_SIGNAL_PRICE_PATH_SHA " +
          json.dumps({"cases":len(data),"complete":result["all"]["source_complete"],
                      "censored":result["all"]["censored_reasons"]}, sort_keys=True))


if __name__ == "__main__":
    main()
