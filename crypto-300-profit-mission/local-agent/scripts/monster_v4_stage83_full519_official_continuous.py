#!/usr/bin/env python3
"""Read-only official Binance USD-M 1m source replay, all Stage64 D0 rows."""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

try:
    import monster_v4_stage38_usdm_original_v4_1m_pilot as publisher
    import monster_v4_stage81_continuous3m_official_pilot as old
    import monster_v4_stage82_official_instrument_scope as scope
    from monster_v4_stage80_dual_entry_core import (
        from_archived_closed_bars, evaluate, load_contract, utc_ms, decimal)
except ImportError:
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as publisher
    from scripts import monster_v4_stage81_continuous3m_official_pilot as old
    from scripts import monster_v4_stage82_official_instrument_scope as scope
    from scripts.monster_v4_stage80_dual_entry_core import (
        from_archived_closed_bars, evaluate, load_contract, utc_ms, decimal)

SCHEMA = "MONSTER_STAGE83_EXPOSED_ALL519_D0_OFFICIAL_1M_CONTINUOUS_3M_V1"
MINUTE = 60000
DAY = 86400000
GOOD = "COMPLETE_OFFICIAL_PREFIX_SHA_VERIFIED_3M_48H"
CENSORED = "CENSORED_DAILY_OFFICIAL_1M_MISSING"
DATES = old.DATES


def selected_for(date: str, shard: int) -> list[dict]:
    if date not in DATES or shard not in range(6):
        raise ValueError("STAGE83_INVALID_FIXED_DATE_SHARD")
    raw = [x for x in old.load_population() if x["date"] == date]
    rows = sorted(raw, key=lambda x: x["symbol"])
    selected = [x for i, x in enumerate(rows) if i % 6 == shard]
    if sum(len([x for x in old.load_population() if x["date"] == d]) for d in DATES) != 519:
        raise ValueError("STAGE83_NOT_ALL_519")
    if not selected:
        raise ValueError("STAGE83_EMPTY_SHARD")
    return selected


def days_needed(date: str, first_ms: int, hours: int) -> tuple[list, int]:
    start = first_ms - 61 * MINUTE
    anchor_end = utc_ms(date + "T06:00:00Z") + 7 * DAY
    end = min(first_ms + hours * 3600000, anchor_end)
    if end <= first_ms or first_ms - utc_ms(date + "T06:00:00Z") >= 7 * DAY:
        raise ValueError("STAGE83_BAD_D0_OR_WINDOW")
    last_tick = first_ms + ((end - first_ms - 1) // (3 * MINUTE)) * (3 * MINUTE)
    last_bar_start = last_tick - MINUTE
    if last_bar_start < start:
        raise ValueError("STAGE83_IMPOSSIBLE_BARS")
    begin_day = datetime.fromtimestamp(start / 1000, tz=timezone.utc).date()
    end_day = datetime.fromtimestamp(last_bar_start / 1000, tz=timezone.utc).date()
    return [begin_day + timedelta(days=i) for i in range((end_day - begin_day).days + 1)], end


def original_status(record: dict) -> None:
    if (record["HOLDOUT"] is not False
        or record["source_status"] != "COMPLETE_OFFICIAL_DAILY_USDM_61M_PUBLISHER_SHA_NO_FUTURE"
        or record["date"] not in DATES):
        raise ValueError("STAGE83_NOT_ORIGINAL_STAGE64_VERIFIED_ASOF")
    if utc_ms(record["first_D0_UTC"]) % (3 * MINUTE):
        raise ValueError("STAGE83_D0_NOT_3MIN_REAL_CLOCK")


def replay(record: dict, *, reader=publisher.verified_1m_day,
           contract=None, registry=None) -> dict:
    original_status(record)
    if contract is None:
        contract = load_contract()
    if registry is None:
        registry = scope.official_registry()
    date, symbol = record["date"], record["symbol"]
    start = utc_ms(record["first_D0_UTC"])
    requested, end = days_needed(date, start, contract["from_first_d0_expiration_hours"])
    out = {
        "date": date, "symbol": symbol, "first_D0_UTC": record["first_D0_UTC"],
        "calendar_anchor_GT2x_EVALUATION_ONLY": record["original_7day_calendar_2x_EVALUATION_ONLY"],
        "source_status": "UNKNOWN",
        "identity": scope.category("USDM", symbol, record["first_D0_UTC"], registry),
        "D0_RETAINED": True,
        "first_D1_UTC": None, "first_D1_path": None,
        "executable_order": "NOT_AUTHORIZED",
    }
    all_bars = []
    receipts = []
    for d in requested:
        try:
            bars, proof = reader(symbol, d)
        except FileNotFoundError:
            out.update(source_status=CENSORED,
                       missing_official_day=d.isoformat(),
                       publisher_sha_verified_prefix=receipts,
                       first_D0_known_original_source=True)
            return out
        if not proof["verified_official_publisher_SHA256"] or len(bars) != 1440:
            raise ValueError("STAGE83_MISSING_OFFICIAL_DAILY_PUBLISHER_SHA")
        receipts.append(proof)
        all_bars.extend(bars)
    if not all_bars or any(all_bars[i][0] != all_bars[0][0] + i * MINUTE
                           for i in range(len(all_bars))):
        raise ValueError("STAGE83_NONCONTIGUOUS_OR_MISORDERED_SOURCE")
    actual_sha = {r["date"]: r["zip_sha256"] for r in receipts}
    for proof in record["publisher_SHA_receipts"]:
        if (not proof["checksum_verified"]
            or proof["date"] not in actual_sha
            or proof["official_zip_sha256"] != actual_sha[proof["date"]]):
            raise ValueError("STAGE83_PRIOR_61M_PUBLISHER_SHA_CONFLICT")
    first_index = (start - all_bars[0][0]) // MINUTE
    if first_index < 61 or first_index >= len(all_bars):
        raise ValueError("STAGE83_SOURCE_START_BEFORE_FIRST_61_CLOSED")
    initial = from_archived_closed_bars(all_bars[first_index-61:first_index], start)
    old.compare_stage64(initial, record)
    state = None
    ticks = 0
    for t in range(start, end, 3 * MINUTE):
        idx = (t - all_bars[0][0]) // MINUTE
        f = from_archived_closed_bars(all_bars[idx-61:idx], t)
        state, result = evaluate(
            state, venue="USDM", symbol=symbol,
            at_utc=publisher.stamp(t), features=f,
            is_first_d0=(ticks == 0), contract=contract)
        ticks += 1
        if result in ("DIRECT_AT_FIRST_D0", "REIGNITION_AFTER_D0"):
            out["first_D1_UTC"] = publisher.stamp(t)
            out["first_D1_path"] = result
            break
    if state is None or state.first_utc != record["first_D0_UTC"]:
        raise ValueError("STAGE83_ORIGINAL_FIRST_D0_CHANGED")
    out.update(
        source_status=GOOD, original_stage64_first61min_parity=True,
        official_daily_publisher_SHA_receipts=receipts,
        evaluated_closed_3m_ticks=ticks,
        first_observable_quote15_USDT=str(initial.quote15_usdt),
        FIRST_D0_NEVER_DROPPED=True)
    return out


def selftest():
    all_rows = old.load_population()
    shards = [selected_for(d, i) for d in DATES for i in range(6)]
    flat = [r for group in shards for r in group]
    if len(flat) != 519 or len({(x["date"], x["symbol"]) for x in flat}) != 519:
        raise AssertionError("STAGE83_BAD_519_SHARD_UNION")
    assert sorted((r["date"], r["symbol"]) for r in flat) == sorted(
        (r["date"], r["symbol"]) for r in all_rows)
    first = utc_ms("2025-01-30T06:00:00Z")
    need, final_end = days_needed("2025-01-30", first, 48)
    assert len(need) == 3 and need[0].isoformat() == "2025-01-30" and need[-1].isoformat() == "2025-02-01"
    assert final_end == first + 48 * 3600000
    print("STAGE83_FROZEN_COMPLETE_519_COIN_DATE_SHARDS_TEST_PASS")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--date")
    p.add_argument("--shard", type=int)
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.date or args.shard is None or not args.out:
        p.error("--date, --shard, --out required")
    if args.workers not in range(1, 5):
        raise ValueError("STAGE83_LIMIT_WORKERS_1_TO_4")
    tasks = selected_for(args.date, args.shard)
    contract, registry = load_contract(), scope.official_registry()
    results, errors = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(replay, row, contract=contract, registry=registry): row
                   for row in tasks}
        for future in concurrent.futures.as_completed(futures):
            row = futures[future]
            try:
                result = future.result()
                if result["symbol"] != row["symbol"] or result["date"] != row["date"]:
                    raise ValueError("STAGE83_CROSS_SYMBOL_DRIFT")
                results.append(result)
                print("STAGE83_CASE " + json.dumps({
                    k: result[k] for k in ("date", "symbol", "source_status",
                                            "identity", "first_D1_UTC", "first_D1_path")
                }, sort_keys=True), flush=True)
            except Exception as e:
                errors.append({"date": row["date"], "symbol": row["symbol"],
                               "reason": type(e).__name__ + ":" + str(e)[:260]})
    if errors or len(results) != len(tasks):
        raise RuntimeError("STAGE83_FAIL_CLOSED_HARD_ERRORS " + json.dumps(errors[:30]))
    result = {
        "schema": SCHEMA, "date": args.date, "shard": args.shard,
        "original_Stage64_complete_coin_dates": len(tasks),
        "source_complete": sum(x["source_status"] == GOOD for x in results),
        "source_censored": sum(x["source_status"] == CENSORED for x in results),
        "d1_upgraded": sum(x["first_D1_UTC"] is not None for x in results),
        "rows": sorted(results, key=lambda x: x["symbol"]),
        "unscored_source_kept_as_unknown": True,
        "historically_exposed": True, "oos": "NOT_DONE",
        "real_exec_profit": "UNKNOWN", "deployment": "NO_GO", "gmail": "OFF",
        "autotrade": "NO_GO", "Frank": "UNCHANGED"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + "\n")
    print("STAGE83_SHARD_SUMMARY " + json.dumps(
        {k: result[k] for k in ("date", "shard", "original_Stage64_complete_coin_dates",
                                 "source_complete", "source_censored", "d1_upgraded")},
        sort_keys=True))


if __name__ == "__main__":
    main()
