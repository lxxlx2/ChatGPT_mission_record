#!/usr/bin/env python3
"""Stage56: inspect true as-of USD-M taker flows and trade count for ALL Stage55 166.

Research-only. No selection, ranking, price-label leakage, buy/sell inference,
spot eligibility assumption, live API, alert, or production state change.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import io
import json
import re
import statistics
import zipfile
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage38_usdm_original_v4_1m_pilot as publisher
except ImportError:
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as publisher

E = Path(__file__).resolve().parents[2] / "monster" / "evidence"
CANDIDATES = E / "monster_stage55_all166_candidate_asof_features_and_fate.csv"
FATES = E / "monster_stage52_all_real_v03_eligible_and_global_budget_fates.jsonl"
CASES = E / "monster_stage52_all5400_originalV4_P1v03_true_minute_source_cases.jsonl"
MARKET = E / "monster_stage52_pinned_v03_all5400_36SHA_true_global_cap_metrics.json"
LOCKS = {
    CANDIDATES.name: "dca780246adb28e045ed77f0f96eb4bd034fb2e7",
    FATES.name: "95ab2eda27880fc53dee7e5fe2d53007e9b9456f",
    CASES.name: "ad7544f97e8a0d6c1f2635aa54052cca42d08cf1",
    MARKET.name: "42d455a6cc9d0164a8dd94aa12a475bad5ed126e",
}
SCHEMA = "MONSTER_STAGE56_SOURCE_LOCKED_ALL166_REAL_USDM_ASOF_TAKER_TRADES_FACTS_V1"
D = Decimal
MIN = 60000


def git_blob(path):
    buf = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(buf)).encode() + b"\0" + buf).hexdigest()


def frozen():
    for path in (CANDIDATES, FATES, CASES, MARKET):
        if git_blob(path) != LOCKS[path.name]:
            raise ValueError("STAGE56_ORIGINAL_GIT_BLOB_DRIFT " + path.name)
    with CANDIDATES.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    fates = [json.loads(x) for x in FATES.read_text().splitlines() if x]
    old = [json.loads(x) for x in CASES.read_text().splitlines() if x]
    market = json.loads(MARKET.read_text())
    if (len(rows), len(fates), len(old), market["publisher_1h_and_1m_valid"],
        len(market["original36_source_sha_receipts"])) != (166, 166, 5400, 3377, 36):
        raise ValueError("STAGE56_ORIGINAL_MARKET_UNIVERSE_CHANGED")
    keys = [(x["date"], x["symbol"]) for x in rows]
    if len(set(keys)) != 166:
        raise ValueError("STAGE56_DUPLICATE_MARKET_CANDIDATE")
    bycase = {(x["date"], x["symbol"]): x for x in old}
    byfate = {(x["date"], x["symbol"]): x for x in fates}
    for row in rows:
        key = row["date"], row["symbol"]
        case, fate = bycase[key], byfate[key]
        eligible = case["p1v03_eligible_unbudgeted"]
        if (case["source_status"] != "COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
            or eligible is None or not eligible["publisher_verified_asof_no_future_source"]
            or eligible["at_UTC"] != row["eligible_timestamp_UTC"]
            or row["eligible_timestamp_UTC"] != fate["asof_UTC"]
            or (row["research_delivered"] == "True") != bool(fate["delivered"])):
            raise ValueError("STAGE56_CANDIDATE_FATE_SOURCE_PARITY_BAD " + str(key))
    return rows


def parse_time(utc):
    t = datetime.fromisoformat(utc.replace("Z", "+00:00"))
    if t.utcoffset() != timedelta(0) or t.second or t.microsecond:
        raise ValueError("STAGE56_INVALID_DECISION_CLOCK")
    return int(t.timestamp() * 1000)


def read_verified_day(symbol, day, read=publisher.get):
    if not re.fullmatch(r"[A-Z0-9]+USDT", symbol):
        raise ValueError("STAGE56_NON_USDT_FUTURES_SYMBOL")
    uri = publisher.url(symbol, day)
    archive = read(uri, publisher.MAX_ZIP)
    receipt = read(uri + ".CHECKSUM", 2048)
    words = receipt.decode("utf-8", "strict").strip().split()
    if not words or not re.fullmatch("[A-Fa-f0-9]{64}", words[0]):
        raise ValueError("STAGE56_OFFICIAL_CHECKSUM_MISSING")
    zip_sha = hashlib.sha256(archive).hexdigest()
    if zip_sha != words[0].lower():
        raise ValueError("STAGE56_OFFICIAL_ZIP_SHA_MISMATCH")
    member = symbol + "-1m-" + day.isoformat() + ".csv"
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        if z.namelist() != [member] or z.getinfo(member).file_size > 25_000_000:
            raise ValueError("STAGE56_UNEXPECTED_PUBLISHER_CSV")
        lines = z.read(member).decode("utf-8-sig")
    ticks = {}
    for line in csv.reader(io.StringIO(lines)):
        if line and line[0].strip().lower() in ("open_time", "open time", "opentime"):
            continue
        if len(line) < 11 or not line[0].isdigit():
            raise ValueError("STAGE56_USDM_BAR_MISSING_TAKER_OR_TRADES")
        t = int(line[0])
        if t >= 10**15:
            if t % 1000:
                raise ValueError("STAGE56_BAD_MICROSECOND_CLOCK")
            t //= 1000
        q, buy = D(line[7]), D(line[10])
        trade_count = int(line[8])
        if (t % MIN or t < 10**12 or q < 0 or buy < 0
            or buy > q or trade_count < 0):
            raise ValueError("STAGE56_INVALID_REAL_TRADES_BAR")
        if t in ticks:
            raise ValueError("STAGE56_DUPLICATE_OFFICIAL_MINUTE")
        ticks[t] = (D(line[4]), q, buy, trade_count)
    if not ticks:
        raise ValueError("STAGE56_EMPTY_PUBLISHER_MINUTES")
    return ticks, {"official_zip_sha256": zip_sha, "date": day.isoformat(),
                   "source_url": uri, "checksum_verified": True}


def asof_features(row, bars):
    now = parse_time(row["eligible_timestamp_UTC"])
    # Ret60: t-1 close vs t-61 close. Volume/taker/trades: t-60 ... t-1.
    indices = [now - i * MIN for i in range(61, 0, -1)]
    if any(t not in bars for t in indices):
        raise ValueError("STAGE56_MISSING_CLOSED_61_MINUTES")
    history = [bars[t] for t in indices]
    current = history[1:]
    recent = current[-15:]
    quote15 = sum((r[1] for r in recent), D(0))
    quote45 = sum((r[1] for r in current[:-15]), D(0))
    quote60 = quote15 + quote45
    taker15 = sum((r[2] for r in recent), D(0))
    taker60 = sum((r[2] for r in current), D(0))
    trades15 = sum(r[3] for r in recent)
    trades60 = sum(r[3] for r in current)
    ret60 = (history[-1][0] / history[0][0] - 1) * 100
    ratio = 3 * quote15 / quote45 if quote45 > 0 else None
    expected = {
        "quote15_USDT": quote15,
        "ret60_pct": ret60,
        "quote15_normalized_prev45": ratio,
    }
    # Recovered independent columns must reconcile the previously frozen source.
    for field, value in expected.items():
        old = D(row[field]) if row[field] else None
        if value != old:
            raise ValueError("STAGE56_OLD_P1_FEATURE_PARITY_FAILED " + field)
    return {
        "quote60_USDT": str(quote60),
        "taker_buy_quote15_USDT": str(taker15),
        "taker_buy_quote60_USDT": str(taker60),
        "taker_buy_share15": str(taker15 / quote15) if quote15 > 0 else None,
        "taker_buy_share60": str(taker60 / quote60) if quote60 > 0 else None,
        "trade_count15": trades15,
        "trade_count60": trades60,
        "minutes_with_positive_quote60": sum(r[1] > 0 for r in current),
        "historical_usdm_executed_trades60": trades60 > 0,
    }


def evaluate(row, fetch=read_verified_day):
    now = parse_time(row["eligible_timestamp_UTC"])
    first = now - 61 * MIN
    last = now - MIN
    first_day = datetime.fromtimestamp(first / 1000, timezone.utc).date()
    last_day = datetime.fromtimestamp(last / 1000, timezone.utc).date()
    if last_day - first_day not in (timedelta(0), timedelta(days=1)):
        raise ValueError("STAGE56_UNEXPECTED_WINDOW")
    whole = {}
    receipts = []
    day = first_day
    while day <= last_day:
        subset, proof = fetch(row["symbol"], day)
        if set(whole).intersection(subset):
            raise ValueError("STAGE56_OVERLAPPING_DAYS")
        whole.update(subset)
        receipts.append(proof)
        day += timedelta(days=1)
    metrics = asof_features(row, whole)
    return {
        "date": row["date"], "symbol": row["symbol"],
        "eligible_timestamp_UTC": row["eligible_timestamp_UTC"],
        "mode": row["mode"],
        "prior_research_delivered": row["research_delivered"] == "True",
        "source_type": "BINANCE_OFFICIAL_USDM_1M_HISTORICAL_NOT_SPOT",
        "source_day_SHA256_receipts": receipts,
        "historical_exchangeInfo_status_at_signal": "UNKNOWN",
        "historical_SPOT_trading_and_30USDT_orderbook": "UNVERIFIED",
        "future_label_POSTHOC_EVALUATION_ONLY": row["future_label_AFTER_signal"],
        **metrics,
    }


def summary(data):
    def group_stats(xs):
        def median(key):
            vals = [D(str(x[key])) for x in xs if x[key] is not None]
            return str(statistics.median(vals)) if vals else None
        return {
            "n": len(xs),
            "taker_buy_share15_median": median("taker_buy_share15"),
            "taker_buy_share60_median": median("taker_buy_share60"),
            "trades60_median": median("trade_count60"),
            "quote60_USDT_median": median("quote60_USDT"),
            "historical_usdm_trades60_observed": sum(x["historical_usdm_executed_trades60"] for x in xs),
            "original_delivered": sum(x["prior_research_delivered"] for x in xs),
        }
    labels = ("FUTURE_2X_AND_CANDIDATE_BEFORE_5MIN",
              "FUTURE_2X_BUT_CANDIDATE_LATE",
              "ORDINARY_NOT_CALENDAR_2X")
    return {
        "schema": SCHEMA,
        "locked_original_git_blobs": LOCKS,
        "all_original_candidates": len(data),
        "all_source_complete_61m_official_SHA": len(data),
        "by_POSTHOC_label_descriptive_only": {
            k: group_stats([x for x in data if x["future_label_POSTHOC_EVALUATION_ONLY"] == k])
            for k in labels
        },
        "NO_NEW_PRIORITY_RULE_OR_THRESHOLD": True,
        "NO_HISTORICAL_SPOT_ORDERBOOK_OR_EXCHANGE_STATUS_CLAIM": True,
        "NO_TRADE_PROFIT_CLAIM": True,
        "ORIGINAL_P1V03": "REJECTED",
        "OTHER_AI_REVIEW": "NOT_DONE",
        "DEPLOYMENT": "NO_GO",
        "FRANK": "UNCHANGED",
        "GMAIL": "OFF",
        "AUTOTRADE": "NO_GO",
    }


def selftest():
    t = "2025-01-02T00:30:00Z"
    now = parse_time(t)
    seq = {now - i * MIN: (D(100), D(100), D(60), 7)
           for i in range(61, 0, -1)}
    row = {"eligible_timestamp_UTC": t, "quote15_USDT": "1500",
           "ret60_pct": "0", "quote15_normalized_prev45": "1"}
    result = asof_features(row, seq)
    assert (result["trade_count60"], result["taker_buy_share15"],
            result["taker_buy_share60"]) == (420, "0.6", "0.6")
    seq[now] = (D(99999), D(100000000), D(100000000), 999)
    assert asof_features(row, seq) == result  # future minute cannot leak
    bad = dict(row, quote15_USDT="1501")
    try:
        asof_features(bad, seq)
        raise AssertionError("STAGE56_PARITY_TAMPER_NOT_BLOCKED")
    except ValueError as err:
        assert "PARITY_FAILED" in str(err)
    del seq[now - 20 * MIN]
    try:
        asof_features(row, seq)
        raise AssertionError("STAGE56_MISSING_MINUTE_NOT_BLOCKED")
    except ValueError as err:
        assert "MISSING_CLOSED" in str(err)
    print("STAGE56_FROZEN_SOURCE_PARITY_CAUSAL_TAKER_61MIN_SELFTEST_PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.out or args.workers not in (1, 2, 3, 4, 5, 6):
        parser.error("--out and --workers in 1..6 required")
    rows = frozen()
    data = []
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = {pool.submit(evaluate, row): row for row in rows}
        for future in concurrent.futures.as_completed(jobs):
            row = jobs[future]
            try:
                data.append(future.result())
            except Exception as exc:
                errors.append({"date": row["date"], "symbol": row["symbol"],
                               "reason": type(exc).__name__ + ":" + str(exc)[:180]})
            if (len(data) + len(errors)) % 20 == 0:
                print("STAGE56_SOURCE_FETCH_PROGRESS " + json.dumps({
                    "seen": len(data) + len(errors), "expected": 166,
                    "failed": len(errors)}), flush=True)
    if errors or len(data) != 166:
        raise RuntimeError("STAGE56_HISTORICAL_SOURCE_NOT_COMPLETE " + json.dumps(errors[:20]))
    data.sort(key=lambda r: (r["date"], r["symbol"]))
    counts = Counter(x["future_label_POSTHOC_EVALUATION_ONLY"] for x in data)
    if [counts[k] for k in ("FUTURE_2X_AND_CANDIDATE_BEFORE_5MIN",
                             "FUTURE_2X_BUT_CANDIDATE_LATE",
                             "ORDINARY_NOT_CALENDAR_2X")] != [27, 2, 137]:
        raise ValueError("STAGE56_ORIGINAL_166_LABEL_DRIFT")
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "monster_stage56_all166_61m_asof_taker_trades_official_SHA.jsonl").write_text(
        "".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in data),
        encoding="utf-8")
    (out / "monster_stage56_all166_taker_trades_descriptive_summary.json").write_text(
        json.dumps(summary(data), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print("STAGE56_ALL166_REAL_ASOF_PUBLISHER_SHA_RECONCILED " +
          json.dumps({"source_verified": len(data), "posthoc_cohorts": dict(counts)},
                     sort_keys=True))


if __name__ == "__main__":
    main()
