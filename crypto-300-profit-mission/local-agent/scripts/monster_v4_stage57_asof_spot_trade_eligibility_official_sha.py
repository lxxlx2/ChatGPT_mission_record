#!/usr/bin/env python3
"""Stage57: verify historic EXACT-SYMBOL Binance Spot activity as of ALL 166 USD-M P1v03 candidates.

Only facts. Each source is Binance's official archived Spot 1m ZIP plus its
publisher CHECKSUM; the previous 15 CLOSED minutes are used. 404 -> unknown,
NEVER "no Spot listing". No future labels in classification or strategy update.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import csv
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "monster" / "evidence"
PREVIOUS = ROOT / "monster_stage56_all166_61m_asof_taker_trades_official_SHA.jsonl"
OLD_SUMMARY = ROOT / "monster_stage56_all166_taker_trades_descriptive_summary.json"
PIN = {
    PREVIOUS.name: "982bddbf05f263423f9cab4f40c0992688cc3499",
    OLD_SUMMARY.name: "50879caf60f7a3795519d5508594e52835be501d",
}
ONE_MIN = 60000
BASE = "https://data.binance.vision/data/spot/daily/klines"
D = Decimal
SCHEMA = "MONSTER_STAGE57_ORIGINAL_166_PINNED_EXACT_SYMBOL_OFFICIAL_SPOT_1M_ASOF_15M_V1"
STATUS_YES = "EXACT_SYMBOL_SPOT_15M_SOURCE_COMPLETE_WITH_TRADES"
STATUS_NO_TRADES = "EXACT_SYMBOL_SPOT_15M_SOURCE_COMPLETE_ZERO_TRADES"
STATUS_404 = "EXACT_SYMBOL_SPOT_ARCHIVE_MISSING_OR_NOT_PUBLISHED_UNKNOWN"
STATUS_GAP = "EXACT_SYMBOL_SPOT_15M_GAPPED_UNKNOWN"
WINDOW = 15


def git_blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def source_rows():
    for p in (PREVIOUS, OLD_SUMMARY):
        if git_blob(p) != PIN[p.name]:
            raise ValueError("STAGE57_STAGE56_SOURCE_BLOB_CHANGED:" + p.name)
    rows = [json.loads(s) for s in PREVIOUS.read_text(encoding="utf-8").splitlines() if s]
    old = json.loads(OLD_SUMMARY.read_text(encoding="utf-8"))
    if (len(rows), old["all_original_candidates"], old["all_source_complete_61m_official_SHA"]) != (166, 166, 166):
        raise ValueError("STAGE57_EXPECTED_166_REAL_USDM_SOURCE_CASES")
    keys = {(x["date"], x["symbol"]) for x in rows}
    if len(keys) != 166:
        raise ValueError("STAGE57_DUPLICATE_166")
    for x in rows:
        if (x["source_type"] != "BINANCE_OFFICIAL_USDM_1M_HISTORICAL_NOT_SPOT"
                or not x["historical_usdm_executed_trades60"]):
            raise ValueError("STAGE57_NOT_ORIGINAL_FUTURES_COHORT")
    return sorted(rows, key=lambda x: (x["date"], x["symbol"]))


def clock_ms(ts):
    t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if t.utcoffset() != timedelta(0) or t.second or t.microsecond:
        raise ValueError("STAGE57_NOT_CLOSED_MINUTE_DECISION_CLOCK")
    return int(t.timestamp() * 1000)


def spot_url(symbol, day):
    if not re.fullmatch(r"[A-Z0-9]{1,35}USDT", symbol):
        raise ValueError("STAGE57_NOT_EXACT_USDT_SYMBOL")
    filename = f"{symbol}-1m-{day.isoformat()}.zip"
    return f"{BASE}/{symbol}/1m/{filename}"


def request(uri, limit, attempts=3):
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(uri, headers={"User-Agent": "Monster-Stage57-Historic-Spot-SHA/1.0"})
            with urllib.request.urlopen(req, timeout=28) as reply:
                data = reply.read(limit + 1)
            if not data or len(data) > limit:
                raise ValueError("STAGE57_EMPTY_OR_TOO_LARGE_ARCHIVE")
            return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt == attempts - 1:
                raise
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            if attempt == attempts - 1:
                raise
        time.sleep(1 + attempt)
    raise RuntimeError("STAGE57_FETCH_RETRIES_EXHAUSTED")


def official_day(symbol, day, fetch=request):
    uri = spot_url(symbol, day)
    archive = fetch(uri, 22_000_000)
    if archive is None:
        return {}, {"date": day.isoformat(), "symbol": symbol, "url": uri,
                    "status": "HTTP_404_UNKNOWN_LISTING_OR_ARCHIVE", "publisher_sha256_verified": False}
    digest_file = fetch(uri + ".CHECKSUM", 2048)
    if digest_file is None:
        raise ValueError("STAGE57_MISSING_OFFICIAL_SPOT_PUBLISHER_CHECKSUM")
    parts = digest_file.decode("utf-8", "strict").strip().split()
    if not parts or not re.fullmatch(r"[0-9A-Fa-f]{64}", parts[0]):
        raise ValueError("STAGE57_INVALID_PUBLISHER_SHA_FORMAT")
    digest = hashlib.sha256(archive).hexdigest()
    if digest != parts[0].lower():
        raise ValueError("STAGE57_SPOT_ORIGINAL_SHA_MISMATCH")
    member = f"{symbol}-1m-{day.isoformat()}.csv"
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        if z.namelist() != [member] or z.getinfo(member).file_size > 85_000_000:
            raise ValueError("STAGE57_UNEXPECTED_SPOT_CSV_MEMBER")
        raw = z.read(member).decode("utf-8-sig")
    result = {}
    for row in csv.reader(io.StringIO(raw)):
        if row and row[0].strip().lower() in ("open_time", "open time", "opentime"):
            continue
        if len(row) < 11 or not row[0].isdigit():
            raise ValueError("STAGE57_INVALID_SPOT_KLINE_ROW")
        timestamp = int(row[0])
        if timestamp >= 10**15:
            if timestamp % 1000:
                raise ValueError("STAGE57_INVALID_SPOT_MICROSECONDS")
            timestamp //= 1000
        if timestamp % ONE_MIN or timestamp < 10**12:
            raise ValueError("STAGE57_UNALIGNED_SPOT_MINUTE")
        o, h, low, c, quote = (D(row[j]) for j in (1, 2, 3, 4, 7))
        trades = int(row[8])
        if min(o, h, low, c) <= 0 or h < max(o, c, low) or low > min(o, c) or quote < 0 or trades < 0:
            raise ValueError("STAGE57_CORRUPT_SPOT_BAR")
        if timestamp in result:
            raise ValueError("STAGE57_DUPLICATE_SPOT_MINUTE")
        result[timestamp] = {"close": str(c), "quote_USDT": str(quote), "trades": trades}
    return result, {"date": day.isoformat(), "symbol": symbol, "url": uri,
                    "status": "VERIFIED_ORIGINAL_BINANCE_SPOT_1M",
                    "archive_SHA256": digest, "publisher_sha256_verified": True,
                    "bars_in_day": len(result)}


def prefix_hint(symbol):
    for prefix in ("1000000", "1000"):
        if symbol.startswith(prefix) and len(symbol) > len(prefix) + 4:
            return {"unverified_contract_size_prefix": prefix,
                    "possible_underlying_name_ONLY": symbol[len(prefix):],
                    "underlying_spot_identity": "UNVERIFIED_DO_NOT_MAP_AUTOMATICALLY"}
    return {"unverified_contract_size_prefix": None,
            "possible_underlying_name_ONLY": None,
            "underlying_spot_identity": "NOT_ASSESSED"}


def review(row, loader=official_day):
    symbol = row["symbol"]
    t = clock_ms(row["eligible_timestamp_UTC"])
    minutes = [t - j * ONE_MIN for j in range(WINDOW, 0, -1)]
    days = sorted({datetime.fromtimestamp(ms / 1000, timezone.utc).date() for ms in minutes})
    bars, receipts = {}, []
    for day in days:
        result, receipt = loader(symbol, day)
        receipts.append(receipt)
        if any(k in bars for k in result):
            raise ValueError("STAGE57_OVERLAPPING_SOURCE_DAYS")
        bars.update(result)
    missing = [x for x in minutes if x not in bars]
    has_404 = any(x["status"] == "HTTP_404_UNKNOWN_LISTING_OR_ARCHIVE" for x in receipts)
    latest = bars.get(t - ONE_MIN)
    fifteen = [bars[x] for x in minutes if x in bars]
    recent_trades = sum(x["trades"] for x in fifteen)
    recent_quote = sum((D(x["quote_USDT"]) for x in fifteen), D(0))
    if has_404:
        status = STATUS_404
    elif missing:
        status = STATUS_GAP
    else:
        status = STATUS_YES if recent_trades > 0 else STATUS_NO_TRADES
    return {
        "date": row["date"], "futures_symbol": symbol,
        "eligible_timestamp_UTC": row["eligible_timestamp_UTC"],
        "futures_event_kind": row["mode"],
        "futures_research_delivered": row["prior_research_delivered"],
        "posthoc_label_EVALUATION_ONLY": row["future_label_POSTHOC_EVALUATION_ONLY"],
        "spot_exact_symbol_checked": symbol,
        "spot_result": status,
        "spot_closed_15m_bars_present": len(fifteen),
        "spot_closed_15m_minute_gaps": len(missing),
        "spot_trades_15m_observed_in_available_source": recent_trades,
        "spot_quote_15m_USDT_observed_in_available_source": str(recent_quote),
        "spot_last_closed_minute_trade_count": latest["trades"] if latest else None,
        "spot_last_closed_minute_close": latest["close"] if latest else None,
        "spot_historical_exchangeInfo_TRADING_status": "UNKNOWN",
        "spot_30USD_historical_orderbook_slippage": "UNKNOWN",
        "spot_same_economic_token_address": "UNVERIFIED",
        "archived_spot_source_not_available_live_at_historical_signal": True,
        "official_spot_daily_SHA256_proofs": receipts,
        **prefix_hint(symbol),
    }


def summarize(rows, controls):
    all_status = collections.Counter(x["spot_result"] for x in rows)
    bygroup = {}
    for k in ("FUTURE_2X_AND_CANDIDATE_BEFORE_5MIN",
              "FUTURE_2X_BUT_CANDIDATE_LATE",
              "ORDINARY_NOT_CALENDAR_2X"):
        grp = [x for x in rows if x["posthoc_label_EVALUATION_ONLY"] == k]
        bygroup[k] = {"count": len(grp),
                      "spot_evidence_by_status": dict(sorted(collections.Counter(x["spot_result"] for x in grp).items()))}
    return {
        "schema": SCHEMA, "original166_locked_input_blobs": PIN,
        "all_historic_USDM_futures_candidates": len(rows),
        "spot_evidence_counts_by_status": dict(sorted(all_status.items())),
        "posthoc_groups_only_for_descriptive_audit": bygroup,
        "BTCUSDT_spot_positive_archive_controls": controls,
        "EXACT_SYMBOL_ONLY": True,
        "NEVER_INFER_NO_LISTING_FROM_ARCHIVE_404": True,
        "NO_HISTORIC_ORDERBOOK_OR_TRADEABLE_BUY_CLAIM": True,
        "P1V03": "REJECTED", "NEW_PRIORITY_RANKER": "NOT_DESIGNED",
        "DEPLOYMENT": "NO_GO", "GMAIL": "OFF", "FRANK": "UNCHANGED",
        "AUTO_TRADE": "NO_GO", "OTHER_AI_REVIEW": "NOT_DONE",
    }


def positive_controls(rows, loader=official_day):
    dates = sorted({x["date"] for x in rows})
    controls = []
    for frozen_date in dates:
        match = next(x for x in rows if x["date"] == frozen_date)
        anchor = {"date": frozen_date, "symbol": "BTCUSDT",
                  "eligible_timestamp_UTC": match["eligible_timestamp_UTC"],
                  "mode": "SOURCE_POSITIVE_CONTROL",
                  "prior_research_delivered": False,
                  "future_label_POSTHOC_EVALUATION_ONLY": "CONTROL_NOT_AN_INVESTMENT_CANDIDATE"}
        item = review(anchor, loader)
        if item["spot_result"] != STATUS_YES:
            raise ValueError("STAGE57_OFFICIAL_SPOT_POSITIVE_CONTROL_FAILED " + frozen_date)
        controls.append({"frozen_date": frozen_date, "timestamp": match["eligible_timestamp_UTC"],
                         "spot_archive_receipts": item["official_spot_daily_SHA256_proofs"],
                         "trades15": item["spot_trades_15m_observed_in_available_source"]})
    return controls


def test():
    tm = "2025-01-02T10:00:00Z"
    t = clock_ms(tm)
    def fake(symbol, day):
        start = int(datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)
        candles = {start + i * ONE_MIN: {"close": "1", "quote_USDT": "10", "trades": 2}
                   for i in range(1440)}
        return candles, {"date": day.isoformat(), "status": "VERIFIED_ORIGINAL_BINANCE_SPOT_1M",
                         "publisher_sha256_verified": True}
    row = {"date": "2025-01-01", "symbol": "TESTUSDT", "eligible_timestamp_UTC": tm,
           "mode": "FIRST_D0_IMMEDIATE", "prior_research_delivered": False,
           "future_label_POSTHOC_EVALUATION_ONLY": "ORDINARY_NOT_CALENDAR_2X"}
    a = review(row, fake)
    assert a["spot_result"] == STATUS_YES and a["spot_trades_15m_observed_in_available_source"] == 30
    def missing(symbol, day):
        return {}, {"date": day.isoformat(), "status": "HTTP_404_UNKNOWN_LISTING_OR_ARCHIVE",
                    "publisher_sha256_verified": False}
    assert review(row, missing)["spot_result"] == STATUS_404
    def future_poison(symbol, day):
        c, p = fake(symbol, day)
        c[t] = {"close": "10000", "quote_USDT": "10000000", "trades": 1000000}
        return c, p
    assert review(row, future_poison)["spot_trades_15m_observed_in_available_source"] == 30
    assert review(dict(row, symbol="1000TESTUSDT"), fake)["underlying_spot_identity"].startswith("UNVERIFIED")
    print("STAGE57_POSITIVE_FUTURE_POISON_ARCHIVE_404_UNKNOWN_TEST_PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if args.selftest:
        test()
        return
    if args.out is None or args.workers not in (1, 2, 3, 4, 5, 6, 7, 8):
        parser.error("--out required and --workers in 1..8")
    cohort = source_rows()
    controls = positive_controls(cohort)
    successes, failures = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(review, row): row for row in cohort}
        for result in concurrent.futures.as_completed(futures):
            row = futures[result]
            try:
                successes.append(result.result())
            except Exception as err:
                failures.append({"date": row["date"], "symbol": row["symbol"],
                                 "cause": type(err).__name__ + ":" + str(err)[:170]})
            if (len(successes) + len(failures)) % 20 == 0:
                print("STAGE57_FULL166_OFFICIAL_SPOT_PROGRESS " + json.dumps({
                    "done": len(successes) + len(failures), "failures": len(failures)}, sort_keys=True), flush=True)
    if failures or len(successes) != 166:
        raise RuntimeError("STAGE57_SOURCE_VERIFICATION_ERROR_NOT_A_SPOT_ABSENCE " +
                           json.dumps(failures[:30], sort_keys=True))
    successes.sort(key=lambda x: (x["date"], x["futures_symbol"]))
    aggregate = summarize(successes, controls)
    if sum(aggregate["spot_evidence_counts_by_status"].values()) != 166:
        raise ValueError("STAGE57_HISTORIC_UNIVERSE_COUNT_DRIFT")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "monster_stage57_all166_exact_symbol_spot_asof_source_SHA.jsonl").write_text(
        "".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in successes),
        encoding="utf-8")
    (args.out / "monster_stage57_all166_spot_trade_activity_source_classification_summary.json").write_text(
        json.dumps(aggregate, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print("STAGE57_ALL166_SOURCE_SHA_EXACT_SYMBOL_SPOT_EVIDENCE_COMPLETE " +
          json.dumps(aggregate["spot_evidence_counts_by_status"], sort_keys=True))


if __name__ == "__main__":
    main()
