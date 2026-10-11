#!/usr/bin/env python3
"""Stage15: Binance archived Spot USDT symbols absent from frozen current504.

Archived symbol directories are NOT point-in-time exchangeInfo / delisting
proof. Historical price records are verified with publisher ZIP SHA256 and
replayed via unchanged production V4 D0/D1. Research only.
"""
import argparse
import concurrent.futures
import hashlib
import json
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

try:
    import monster_v4_archive_universe_replay as archive
except ImportError:
    from scripts import monster_v4_archive_universe_replay as archive

BUCKET = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
ROOT = "data/spot/daily/klines/"
S3_NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
FROZEN_DATES = ("2025-11-17", "2026-02-17", "2026-05-17", "2026-08-17", "2026-09-17")
MAX_PAGES = 30
MAX_SYMBOLS = 12000
WORKERS = 8

def read_url(url, *, method="GET"):
    req = urllib.request.Request(url, method=method,
                                 headers={"User-Agent": "MonsterResearchArchiveInventory/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read() if method == "GET" else response.status

def list_ever_spot_symbols(read=read_url):
    """Enumerate published S3 directory prefixes, including historical pairs."""
    found, token, used_tokens = set(), None, set()
    for _ in range(MAX_PAGES):
        query = {"list-type": "2", "prefix": ROOT, "delimiter": "/", "max-keys": "1000"}
        if token:
            query["continuation-token"] = token
        raw = read(BUCKET + "?" + urllib.parse.urlencode(query))
        if not isinstance(raw, bytes):
            raise ValueError("S3_LIST_RESPONSE_NOT_BYTES")
        root = ET.fromstring(raw)
        if root.tag != S3_NS + "ListBucketResult":
            raise ValueError("S3_LIST_NOT_BUCKET_RESULT")
        if root.findtext(S3_NS + "Prefix") != ROOT:
            raise ValueError("S3_LIST_WRONG_PREFIX")
        for node in root.findall(S3_NS + "CommonPrefixes"):
            folder = node.findtext(S3_NS + "Prefix", "")
            if not folder.startswith(ROOT) or not folder.endswith("/"):
                raise ValueError("S3_LIST_INVALID_FOLDER")
            symbol = folder[len(ROOT):-1]
            if (not symbol or "/" in symbol or not symbol.isascii()
                    or not symbol.isalnum() or symbol.upper() != symbol):
                raise ValueError("S3_LIST_INVALID_SYMBOL:" + repr(folder))
            found.add(symbol)
            if len(found) > MAX_SYMBOLS:
                raise ValueError("S3_LIST_TOO_MANY_SYMBOLS")
        truncated = root.findtext(S3_NS + "IsTruncated")
        if truncated not in ("true", "false"):
            raise ValueError("S3_LIST_TRUNCATION_UNSPECIFIED")
        if truncated == "false":
            if not found:
                raise ValueError("S3_LIST_EMPTY")
            return sorted(found)
        new_token = root.findtext(S3_NS + "NextContinuationToken")
        if not new_token or new_token in used_tokens:
            raise ValueError("S3_LIST_BAD_CONTINUATION")
        used_tokens.add(new_token)
        token = new_token
    raise ValueError("S3_LIST_PAGE_LIMIT")

def frozen_current504():
    manifest = json.loads(archive.REGISTRY.read_text(encoding="utf-8"))
    return set(archive.validate_manifest(manifest))

def inventory(read=read_url):
    ever = list_ever_spot_symbols(read)
    current = frozen_current504()
    ever_usdt = sorted(s for s in ever if s.endswith("USDT"))
    historical_only = sorted(set(ever_usdt) - current)
    missing_current = sorted(current - set(ever_usdt))
    if len(missing_current) > max(50, len(current)//10):
        raise ValueError("S3_LIST_TOO_MANY_MISSING_CURRENT_SPOT_SYMBOLS")
    if not historical_only:
        raise ValueError("S3_LIST_NO_ARCHIVE_ONLY_SYMBOLS")
    return {
        "schema": "MONSTER_STAGE15_ARCHIVED_SPOT_USDT_INVENTORY_V1",
        "source": "BINANCE_OFFICIAL_S3_PUBLIC_ARCHIVE_PREFIX_DIRECTORY",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "EVER_ARCHIVED_USDT_SPOT_MINUS_FROZEN_20261011_SPOT504",
        "not_point_in_time_exchangeinfo": True,
        "not_proven_delisted": True,
        "all_archive_symbols": len(ever),
        "all_archive_usdt_count": len(ever_usdt),
        "frozen_current_count": len(current),
        "current_missing_archive_count": len(missing_current),
        "current_missing_archive_symbols": missing_current,
        "archive_only_usdt_count": len(historical_only),
        "archive_only_symbols": historical_only,
        "archive_only_sha256": hashlib.sha256(
            ("\n".join(historical_only) + "\n").encode()).hexdigest(),
        "frozen_dates": list(FROZEN_DATES),
        "data_usage": "ARCHIVE_EXISTENCE_THEN_VERIFIED_MINUTE_REPLAY",
        "deployment": "NO_GO",
    }

def historical_day_exists(symbol, day, read=read_url):
    url = archive.source.zip_url(symbol, day)
    try:
        code = read(url, method="HEAD")
        return "DATE_ZIP_PRESENT" if code == 200 else "SOURCE_HEAD_UNEXPECTED_STATUS_" + str(code)
    except urllib.error.HTTPError as exc:
        return "DATE_ARCHIVE_404" if exc.code == 404 else "SOURCE_HEAD_HTTP_" + str(exc.code)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return "SOURCE_HEAD_NETWORK_FAILED_" + type(exc).__name__

def replay_one(symbol, day, head=historical_day_exists, runner=archive.run_symbol):
    check = head(symbol, day)
    if check != "DATE_ZIP_PRESENT":
        return {"symbol": symbol, "status": check, "watch_events": None, "setups": None}
    row = runner(symbol, calendar_day=day,
                 calendar_anchor=day.isoformat() + "T12:00:00Z")
    if row.get("symbol") != symbol:
        raise ValueError("STAGE15_REPLAY_ID_MISMATCH")
    return row

def run_day(daystr, *, read=read_url, head=historical_day_exists,
            runner=archive.run_symbol, symbols=None, workers=WORKERS):
    if daystr not in FROZEN_DATES:
        raise ValueError("NON_FROZEN_STAGE15_DATE")
    day = date.fromisoformat(daystr)
    inv = inventory(read) if symbols is None else None
    chosen = inv["archive_only_symbols"] if symbols is None else list(symbols)
    if len(chosen) != len(set(chosen)) or not all(s.endswith("USDT") for s in chosen):
        raise ValueError("INVALID_ARCHIVE_ONLY_INPUT")
    if not 1 <= workers <= WORKERS:
        raise ValueError("UNSAFE_CONCURRENCY")
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(replay_one, sym, day, head, runner): sym for sym in chosen}
        for future in concurrent.futures.as_completed(futures):
            item = future.result()
            if item["symbol"] != futures[future]:
                raise ValueError("WORKER_ID_MISMATCH")
            rows.append(item)
            if len(rows) % 100 == 0:
                print("STAGE15_PROGRESS " + json.dumps({
                    "day": daystr, "attempted": len(rows), "target": len(chosen)}),
                    file=sys.stderr, flush=True)
    rows.sort(key=lambda x: x["symbol"])
    counts = Counter(x["status"] for x in rows)
    valid = [x for x in rows if x["status"] == "COMPLETE_60H"]
    pnl, censored = [], Counter()
    for case in valid:
        for event in case.get("setup_triggered_24h_proxy_20bps", []):
            trade = event["proxy"]
            if trade["status"] == "PRICE_PROXY_ONLY":
                pnl.append(trade["net_pct"])
            else:
                censored[trade["status"]] += 1
    return {
        "schema": "MONSTER_STAGE15_ARCHIVE_ONLY_S3_1M_V4_PRODUCTION_REPLAY_V1",
        "research_only": True,
        "historical_exchangeinfo_unavailable": True,
        "not_true_point_in_time_universe": True,
        "status_scope": "NOT_CURRENT_504_BUT_HISTORICALLY_ARCHIVED_SPOT_USDT",
        "day": daystr,
        "frozen_before_ohlcv_requests": symbols is None,
        "inventory": inv,
        "source": "BINANCE_OFFICIAL_S3_DIRECTORY_AND_VERIFIED_DAILY_1M_SHA256",
        "summary": {
            "archive_only_attempted": len(rows),
            "statuses": dict(counts),
            "full_60h": len(valid),
            "watch_episodes": sum(x["watch_events"] for x in valid),
            "d1_episodes": sum(x["setups"] for x in valid),
            "watch_symbols": [x["symbol"] for x in valid if x.get("watch_events", 0) > 0],
            "d1_proxy_evaluable": len(pnl),
            "d1_proxy_profit": sum(x > 0 for x in pnl),
            "d1_proxy_loss": sum(x < 0 for x in pnl),
            "d1_proxy_median_pct": round(statistics.median(pnl), 6) if pnl else None,
            "d1_censored": dict(censored),
        },
        "cases": rows,
        "not_proven": "HISTORICAL_FULL_UNIVERSE_OR_5X_RECALL_OR_REAL_FILL",
        "strategy_validated": False,
        "other_ai_review_done": False,
        "deployment": "NO_GO",
        "real_mail_sent": False,
        "trading_enabled": False,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", choices=FROZEN_DATES, required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = run_day(args.date)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("STAGE15_RESULT_JSON " + json.dumps(report["summary"], sort_keys=True), flush=True)
    statuses = report["summary"]["statuses"]
    if report["summary"]["archive_only_attempted"] < 20:
        raise SystemExit("STAGE15_INCOMPLETE_ARCHIVE_ONLY_INVENTORY")
    if any(("NETWORK_FAILED" in key or "SOURCE_HEAD_HTTP_" in key or
            "SOURCE_INTEGRITY_REJECTED" in key) for key in statuses):
        raise SystemExit("STAGE15_SOURCE_INTEGRITY_OR_AVAILABILITY_UNKNOWN")

if __name__ == "__main__":
    main()
