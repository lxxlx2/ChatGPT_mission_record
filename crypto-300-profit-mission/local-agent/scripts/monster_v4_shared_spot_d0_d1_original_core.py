#!/usr/bin/env python3
"""One frozen Spot universe, ONE persistent SQLite, original D0+queue D1.

Historical non-production source-verified research. No real 24h ticker/L2,
historical exchangeInfo PIT, Gmail, trading, background task or deployment.
Incomplete 758 source coverage MUST NOT be reported as 758-symbol replay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sqlite3
import tempfile

import monster_v4_shadow as production
import monster_v4_stage26_continuous168h as old
import monster_v4_historical_replay as minutes

SCHEMA = "MONSTER_SHARED_SPOT_ONE_SQLITE_ORIGINAL_D0_D1_CAUSAL_V1"
MIN = 60_000
WARMUP = 1440
ACTIVE = 10080
TOTAL = 12960
TICK = 3 * MIN
FROZEN_ORIGINAL_POPULATION = 758
FROZEN_DATES = ("2025-11-04", "2025-12-04", "2026-02-04",
                "2026-04-04", "2026-08-04", "2026-09-04")
ORIGINAL_SHADOW_BLOB = "bc958b3d90a8a52afa51515cb53f7e5fafaffaaa"
SECONDARY_FREEZE = (Path(__file__).resolve().parents[2] / "monster/evidence"
                    / "monster_shared_spot_stage26_original758_secondary_freeze_20261016.json")
SECONDARY_FREEZE_BLOB = "8467bfc0db7cb888f805f30eaae301a812fbb20d"
SECONDARY_ROSTER_SHA256 = "cea49caae4245dad910cc096bdaea953387bdfea64667a49916756d12297074a"
BTC_ETH_SECONDARY_PIN = (SECONDARY_FREEZE.parent /
    "monster_shared_spot_BTC_ETH_20_publisher_daily_sha_secondary_pin_20261016.json")
BTC_ETH_SECONDARY_PIN_BLOB = "08fdc8cf8054ad93089a93bcd1e3e6d26877367f"


def check_secondary_daily_sha_pins(symbol, original_receipts):
    raw = BTC_ETH_SECONDARY_PIN.read_bytes()
    blob = hashlib.sha1(
        b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if blob != BTC_ETH_SECONDARY_PIN_BLOB:
        raise ValueError("SHARED_SPOT_SECONDARY_DAILY_SOURCE_PIN_DRIFT")
    manifest = json.loads(raw)
    members = {s["symbol"]: s["days"] for s in manifest["symbols"]}
    if set(members) != {"BTCUSDT","ETHUSDT"}:
        raise ValueError("SHARED_SPOT_SECONDARY_DAILY_SOURCE_SYMBOLS_DRIFT")
    if symbol not in members:
        return "NO_PRIOR_PER_DAY_SHA_PIN_UNVERIFIED_HISTORICAL_SOURCE"
    got = [{"day": r["date"],"sha256": r["sha256"]} for r in original_receipts]
    if got != members[symbol]:
        raise ValueError("SHARED_SPOT_HISTORICAL_PUBLISHER_DAILY_SHA_PIN_CHANGED")
    return "MATCHED_PREVIOUSLY_GIT_ARCHIVED_20_DAILY_PUBLISHER_SHA"


def original_source_freeze():
    raw = SECONDARY_FREEZE.read_bytes()
    git_blob = hashlib.sha1(
        b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if git_blob != SECONDARY_FREEZE_BLOB:
        raise ValueError("SHARED_SPOT_FROZEN_ORIGINAL_ROSTER_SOURCE_BLOB_DRIFT")
    census = json.loads(raw)
    cohort = tuple(census["roster"])
    digest = hashlib.sha256(("\n".join(cohort)+"\n").encode()).hexdigest()
    if (digest != SECONDARY_ROSTER_SHA256 or
            census.get("original_roster_sha256") != SECONDARY_ROSTER_SHA256 or
            len(cohort) != FROZEN_ORIGINAL_POPULATION or
            tuple(sorted(cohort)) != cohort or len(set(cohort)) != len(cohort)):
        raise ValueError("SHARED_SPOT_SECONDARY_FROZEN_758_ROSTER_INVALID")
    day_map = {d["date"]:d for d in census["frozen_dates"]}
    if set(day_map) != set(FROZEN_DATES):
        raise ValueError("SHARED_SPOT_SECONDARY_FROZEN_DATES_CHANGED")
    for d in day_map.values():
        complete = d["complete_symbols"]
        if (len(complete) != d["eligible"] or
                len(complete) + d["censored"] != FROZEN_ORIGINAL_POPULATION or
                not set(complete).issubset(cohort) or
                len(set(complete)) != len(complete)):
            raise ValueError("SHARED_SPOT_SECONDARY_FROZEN_SOURCE_STATUS_CHANGED")
    return cohort, day_map


def original_758_coverage(day, replayed_roster, *, source_attested=False):
    cohort, day_map = original_source_freeze()
    if day.isoformat() not in day_map:
        raise ValueError("SHARED_SPOT_DATE_NOT_ORIGINAL_FROZEN")
    recorded_complete = set(day_map[day.isoformat()]["complete_symbols"])
    selected = set(replayed_roster)
    if not selected.issubset(recorded_complete):
        raise ValueError("SHARED_SPOT_REPLAY_REQUEST_NOT_ORIGINAL_SOURCE_COMPLETE")
    states = [
        {"symbol": sym, "source_disposition":
         (("OFFICIAL_VERIFIED_AND_REPLAYED_SUBSET" if source_attested
           else "PRELOADED_CACHE_REPLAYED_ORIGIN_UNATTESTED") if sym in selected else
          "CENSORED_SOURCE_MISSING_OR_INCOMPLETE_AT_STAGE26" if sym not in recorded_complete else
          "SOURCE_COMPLETE_AT_STAGE26_NOT_REPLAYED")}
        for sym in cohort
    ]
    return {
        "original_758_denominator": len(cohort),
        "original_frozen_roster_sha256": SECONDARY_ROSTER_SHA256,
        "original_roster_pre_registered_in_20261011_manifest": False,
        "two_unsupported_unicode_not_added_to_758": True,
        "point_in_time_listing": "UNVERIFIED",
        "source_complete_original_stage26":len(recorded_complete),
        "source_missing_or_incomplete_original_stage26":len(cohort)-len(recorded_complete),
        "source_complete_but_not_replayed":len(recorded_complete)-len(selected),
        "replayed_verifiable_subset":len(selected),
        "coverage_status":"SOURCE_COMPLETE_SUBSET_NOT_FULL_758",
        "per_symbol":states
    }


def production_blob():
    p = Path(production.__file__)
    raw = p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def assert_original_core():
    if production_blob() != ORIGINAL_SHADOW_BLOB:
        raise ValueError("SHARED_SPOT_PRODUCTION_D0_D1_CORE_DRIFT")


def utc_ms(day):
    return int(datetime(day.year, day.month, day.day, 6,
                        tzinfo=timezone.utc).timestamp() * 1000)


def clean_roster(symbols):
    if (not isinstance(symbols, (list, tuple)) or not symbols
            or len(symbols) != len(set(symbols))):
        raise ValueError("SHARED_SPOT_INVALID_ROSTER_DUPLICATE_OR_EMPTY")
    for sym in symbols:
        if (not isinstance(sym, str) or not sym.isascii()
                or not sym.endswith("USDT") or not sym.isalnum()):
            raise ValueError("SHARED_SPOT_INVALID_SYMBOL_IDENTITY")
    return tuple(sorted(symbols))


def setup_cache(path):
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=DELETE")
    db.executescript("""
    CREATE TABLE tick_source(
        tick_ms INTEGER NOT NULL, symbol TEXT NOT NULL,
        last_price TEXT NOT NULL, past24h_quote TEXT NOT NULL,
        PRIMARY KEY(tick_ms,symbol));
    CREATE TABLE closed5m_source(
        symbol TEXT NOT NULL, end_ms INTEGER NOT NULL,
        candle_json TEXT NOT NULL, PRIMARY KEY(symbol,end_ms));
    CREATE TABLE source_receipts(symbol TEXT PRIMARY KEY, receipts_json TEXT NOT NULL);
    """)
    return db


def prepare_symbol(db, symbol, day, bars, source_receipts):
    """Strictly verified 1m source in; no original WATCH/SETUP inputs."""
    start = utc_ms(day) - WARMUP * MIN
    if (len(bars) != TOTAL or bars[0][0] != start
            or any(type(r[0]) is not int or r[0] != start + i*MIN
                   or len(r) != 7 for i, r in enumerate(bars))
            or any(r[1] <= 0 or r[2] <= 0 or r[3] <= 0 or
                   r[4] <= 0 or r[5] < 0 or r[6] < 0 or
                   r[3] > min(r[1],r[4]) or r[2] < max(r[1],r[4])
                   for r in bars)):
        raise ValueError("SHARED_SPOT_SOURCE_12960_CONTIGUOUS_1M_REQUIRED")
    expected_days = [(day+timedelta(days=i)).isoformat()
                     for i in range(-1,9)]
    if (not isinstance(source_receipts, list) or len(source_receipts) != 10
            or [p.get("date") for p in source_receipts] != expected_days
            or any(p.get("verified_published_sha256") is not True
                   or len(p.get("sha256","")) != 64
                   or any(c not in "0123456789abcdef" for c in p["sha256"])
                   for p in source_receipts)):
        raise ValueError("SHARED_SPOT_10_OFFICIAL_PUBLISHER_SHAS_REQUIRED")
    prefix = [Decimal(0)]
    for r in bars:
        prefix.append(prefix[-1]+r[5])
    rows = []
    for i in range(WARMUP + 2, WARMUP + ACTIVE, 3):
        tick = bars[i][0]+MIN
        quote = prefix[i+1]-prefix[i+1-WARMUP]
        rows.append((tick, symbol, str(bars[i][4]), str(quote)))
    candles = minutes.make_closed_five_minute_bars(bars)
    with db:
        db.executemany("INSERT INTO tick_source VALUES(?,?,?,?)", rows)
        db.executemany("INSERT INTO closed5m_source VALUES(?,?,?)",
                       ((symbol, int(c[6]), json.dumps(c))
                        for c in candles))
        db.execute("INSERT INTO source_receipts VALUES(?,?)",
                   (symbol, json.dumps(source_receipts, sort_keys=True)))
    return {"symbol":symbol,"poll_rows":len(rows),"closed_5m":len(candles),
            "publisher_days":len(source_receipts),
            "original_publisher_sha256_by_day":[
                {"day":p["date"],"sha256":p["sha256"]}
                for p in source_receipts]}


def assert_complete_cache(db, roster, day):
    """Fail closed BEFORE exposing any synthetic partial-market D0."""
    anchor = utc_ms(day)
    target_ticks = ACTIVE//3
    expected = len(roster)*target_ticks
    if db.execute("SELECT COUNT(*) FROM tick_source").fetchone()[0] != expected:
        raise ValueError("SHARED_SPOT_INCOMPLETE_ALL_SYMBOL_TICK_DENOMINATOR")
    if db.execute("SELECT COUNT(*) FROM source_receipts").fetchone()[0] != len(roster):
        raise ValueError("SHARED_SPOT_MISSING_VERIFIED_ORIGINAL_1M_SOURCE")
    if db.execute("SELECT COUNT(*) FROM closed5m_source").fetchone()[0] != len(roster)*(TOTAL//5):
        raise ValueError("SHARED_SPOT_INCOMPLETE_VERIFIED_5M_DERIVATIVE")
    if db.execute("SELECT COUNT(DISTINCT symbol) FROM tick_source").fetchone()[0] != len(roster):
        raise ValueError("SHARED_SPOT_UNREGISTERED_OR_MISSING_SYMBOL")
    first = anchor+3*MIN
    last = anchor+ACTIVE*MIN
    bounds = db.execute("SELECT MIN(tick_ms),MAX(tick_ms),COUNT(DISTINCT tick_ms) FROM tick_source").fetchone()
    if bounds != (first,last,target_ticks):
        raise ValueError("SHARED_SPOT_GLOBAL_3M_CLOCK_CHANGED")
    found = [r[0] for r in db.execute("SELECT DISTINCT symbol FROM tick_source ORDER BY symbol")]
    if tuple(found) != roster:
        raise ValueError("SHARED_SPOT_GLOBAL_UNIVERSE_CHANGED")
    bad = db.execute("""
        SELECT tick_ms FROM tick_source GROUP BY tick_ms
        HAVING COUNT(*) != ? LIMIT 1""",(len(roster),)).fetchone()
    if bad:
        raise ValueError("SHARED_SPOT_TICK_FULL_UNIVERSE_INCOMPLETE")
    return {"poll_ticks":target_ticks,"symbol_date_count":len(roster),
            "expected_source_rows":expected}


def verified_closed_5m_for_original_d1(db, roster, venue, sym, at_ms):
    """Validate research source BEFORE handing candles to production D1.

    Historical data defects are fatal to this replay; original production
    catches ValueError as a retry, which would corrupt D1 deferred/LATE.
    This callback never changes the frozen production evaluator or queue.
    """
    if venue != "spot" or sym not in roster:
        raise RuntimeError("SHARED_SPOT_ORIGINAL_D1_SOURCE_UNEXPECTED_INSTRUMENT")
    try:
        arr = db.execute("""
            SELECT candle_json FROM closed5m_source
            WHERE symbol=? AND end_ms<?
            ORDER BY end_ms DESC LIMIT 8
        """, (sym, at_ms)).fetchall()
        candles = [json.loads(x[0]) for x in reversed(arr)]
        last_closed_end = (at_ms // (5 * MIN)) * (5 * MIN) - 1
        expected = [last_closed_end - (7 - i) * 5 * MIN
                    for i in range(8)]
        if len(candles) != 8:
            raise ValueError("HISTORICAL_D1_SOURCE_MISSING_CLOSED_5M")
        for i, candle in enumerate(candles):
            if not isinstance(candle, list) or len(candle) != 8:
                raise ValueError("HISTORICAL_D1_SOURCE_BAD_CANDLE_SHAPE")
            if (type(candle[0]) is not int or type(candle[6]) is not int or
                    candle[6] != expected[i] or
                    candle[0] != expected[i] - 5 * MIN + 1 or
                    candle[6] >= at_ms):
                raise ValueError("HISTORICAL_D1_SOURCE_BAD_OPEN_CLOSE_CLOCK")
            values = []
            for idx in (1, 2, 3, 4, 5, 7):
                item = candle[idx]
                if isinstance(item, bool):
                    raise ValueError("HISTORICAL_D1_SOURCE_BOOL_NUMERIC")
                number = Decimal(str(item))
                if not number.is_finite():
                    raise ValueError("HISTORICAL_D1_SOURCE_NONFINITE_NUMERIC")
                values.append(number)
            op, hi, lo, close, volume, quote = values
            if (min(op, hi, lo, close) <= 0 or
                    not (lo <= op <= hi and lo <= close <= hi) or
                    volume < 0 or quote <= 0):
                raise ValueError("HISTORICAL_D1_SOURCE_BAD_OHLC_OR_QUOTE")
        # Fail closed if the ORIGINAL evaluator rejects these same candles
        # for any further feature/continuity reason. It is read-only and
        # will be evaluated normally once more by process_queue().
        production.evaluate_closed_5m(candles, at_ms)
        return candles
    except (ValueError, TypeError, IndexError, KeyError,
            OverflowError, ArithmeticError) as exc:
        raise RuntimeError(
            "SHARED_SPOT_ORIGINAL_D1_SOURCE_INVALID_CANDLE") from exc


def run_shared(db, day, symbols, *, market_coverage_label, frozen_verified_roster=None):
    """One production DB, full-list D0 ONCE/tick, global FIFO D1 ONCE/tick."""
    assert_original_core()
    roster = clean_roster(symbols)
    if day.isoformat() not in FROZEN_DATES:
        raise ValueError("SHARED_SPOT_DATE_NOT_FROZEN_RETROSPECTIVE")
    if market_coverage_label not in ("SYNTHETIC_TEST_ONLY",
                                     "OFFICIAL_VERIFIED_SUBSET_ONLY",
                                     "FULL_758_OFFICIAL_VERIFIED"):
        raise ValueError("SHARED_SPOT_COVERAGE_LABEL_UNKNOWN")
    if market_coverage_label == "FULL_758_OFFICIAL_VERIFIED":
        # Historic source census has 1,829/4,548 missing symbol-dates.
        # Even a caller-supplied second roster cannot enable FULL.
        raise ValueError("SHARED_SPOT_FULL_758_NOT_VERIFIED_SOURCE_CENSORED")
    if market_coverage_label != "SYNTHETIC_TEST_ONLY":
        original_758_coverage(day, roster)
    coverage = assert_complete_cache(db, roster, day)
    counts = Counter()
    with tempfile.TemporaryDirectory(prefix="monster_shared_spot_original_D0_D1_") as td:
        store = production.open_store(Path(td)/"one_global_758_or_subset.sqlite")
        try:
            def real_historical_closed_5m(venue, sym, at_ms):
                return verified_closed_5m_for_original_d1(
                    db, roster, venue, sym, at_ms)

            start, end = utc_ms(day), utc_ms(day)+ACTIVE*MIN
            for tick in range(start+3*MIN,end+1,TICK):
                rows = db.execute("""
                    SELECT symbol,last_price,past24h_quote
                    FROM tick_source WHERE tick_ms=? ORDER BY symbol""",
                    (tick,)).fetchall()
                if len(rows) != len(roster) or tuple(x[0] for x in rows) != roster:
                    raise ValueError("SHARED_SPOT_MISSING_SYMBOL_AT_GLOBAL_POLL")
                # In particular, not 758 calls each holding ONE symbol in
                # independent SQLite: this is the original complete-time D0.
                d0 = production.observe_snapshot(store, "spot", tick, [
                    {"symbol":sym, "lastPrice":price,"quoteVolume":quote}
                    for sym,price,quote in rows])
                d1 = production.process_queue(
                    store,tick,real_historical_closed_5m,limit=8)
                counts["polls"] += 1
                counts["D0_watch_new"] += d0["watch_new"]
                for key in ("selected","completed","deferred","late"):
                    counts["D1_"+key] += d1[key]
            events = [dict(x) for x in store.execute("""
                SELECT event_id,venue,symbol,event_type,observed_ms,payload
                FROM events ORDER BY observed_ms,event_id""")]
            queue = [dict(x) for x in store.execute("""
                SELECT id,venue,symbol,first_seen_ms,last_seen_ms,status,
                       attempts,deadline_ms,last_error,last_evaluated_bar_ms
                FROM candidate_queue ORDER BY first_seen_ms,id""")]
        finally:
            store.close()
    by_event = Counter(x["event_type"] for x in events)
    by_status = Counter(x["status"] for x in queue)
    if counts["D0_watch_new"] != by_event["WATCH_EARLY"]:
        raise ValueError("SHARED_SPOT_WATCH_SOURCE_AND_EVENT_DRIFT")
    if counts["polls"] != ACTIVE//3:
        raise ValueError("SHARED_SPOT_CLOCK_COUNT_DRIFT")
    return {
        "schema":SCHEMA,
        "trigger_commit_sha":os.environ.get("GITHUB_SHA","LOCAL_UNVERIFIED"),
        "shared_replayer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "date":day.isoformat(),
        "origin_core_blob":ORIGINAL_SHADOW_BLOB,
        "source": ("SYNTHETIC_FIXTURE_ONLY" if market_coverage_label=="SYNTHETIC_TEST_ONLY"
                   else "PRELOADED_MINUTE_CACHE_PROVENANCE_UNATTESTED"),
        "source_origin_verified": False,
        "source_attestation": "PRELOADED_CACHE_UNATTESTED_USE_CONTROLLED_OFFICIAL_READER",
        "source_level":"ARCHIVED_1M_ZIP_CHECKSUM_AND_DERIVED_CLOSED_5M",
        "market_coverage":("SYNTHETIC_TEST_ONLY"
                           if market_coverage_label=="SYNTHETIC_TEST_ONLY"
                           else "UNATTESTED_SUBSET_CACHE"),
        "frozen_original_universe_attempted":FROZEN_ORIGINAL_POPULATION,
        "actually_complete_symbols":len(roster),
        "true_full_758_replay": False,
        "original_758_coverage": (
            original_758_coverage(day,roster)
            if market_coverage_label!="SYNTHETIC_TEST_ONLY"
            else {"original_758_denominator":758,
                  "coverage_status":"SYNTHETIC_NO_HISTORICAL_SOURCE_CLAIM"}),
        "not_real_historical_24h_ticker_or_PIT_listing":True,
        "only_original_production_D0_and_D1_called":True,
        "one_shared_sqlite_for_all_symbols":True,
        "historical_exposed_not_OOS":True,
        "real_market_order_or_mail":"OFF",
        "G4":"UNKNOWN","G6":"NO_GO",
        "source_coverage":coverage,
        "execution_counts":dict(counts),
        "event_type_counts":dict(by_event),
        "queue_status_counts":dict(by_status),
        "queue_rows":queue,
        "events":events,
    }


def run_official_subset(day, symbols):
    roster = clean_roster(symbols)
    original_758_coverage(day,roster)
    with tempfile.TemporaryDirectory(prefix="monster_verified_minutes_") as td:
        with setup_cache(Path(td)/"verified_1m_closed5m_cache.sqlite") as db:
            prep = []
            for sym in roster:
                bars, receipt = old.read_complete_216h(sym,day)
                pin_status = check_secondary_daily_sha_pins(sym,receipt)
                # Stage26 read_complete_216h() verified all ten
                # publisher CHECKSUM objects before returning compact
                # {date,sha256} provenance; preserve that trust boundary.
                attested = [dict(item,
                                 verified_published_sha256=True,
                                 verified_by="STAGE26_OFFICIAL_CHECKSUM_READER")
                            for item in receipt]
                result = prepare_symbol(db,sym,day,bars,attested)
                result["previously_archived_daily_sha_check"] = pin_status
                prep.append(result)
            result = run_shared(db,day,roster,
                                market_coverage_label="OFFICIAL_VERIFIED_SUBSET_ONLY")
    result["source_origin_verified"] = True
    result["original_758_coverage"] = original_758_coverage(day,roster,source_attested=True)
    result["source"] = "OFFICIAL_SPOT_1M_PUBLISHER_SHA_WITH_STORED_PAST_24H_PROXY"
    result["market_coverage"] = "OFFICIAL_VERIFIED_SUBSET_ONLY"
    result["source_attestation"] = "STAGE26_PUBLISHER_ZIP_SHA256_CHECKSUM_VERIFIED_AT_RUN_TIME"
    result["historically_precommitted_publisher_SHA_for_all_symbols"] = False
    result["prior_daily_SHA_secondary_pin_matches"] = sum(
        p["previously_archived_daily_sha_check"] ==
        "MATCHED_PREVIOUSLY_GIT_ARCHIVED_20_DAILY_PUBLISHER_SHA"
        for p in prep)
    result["prepared_verified_minute_sources"] = prep
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--date",required=True,choices=FROZEN_DATES)
    p.add_argument("--official-symbol",action="append",required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("SHARED_SPOT_OUTPUT_EXISTS")
    result=run_official_subset(date.fromisoformat(args.date),
                               args.official_symbol)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("x",encoding="utf-8") as h:
        h.write(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("SHARED_SPOT_CAUSAL_VERIFIED_SUBSET "+
          json.dumps({k:result[k] for k in
             ("date","actually_complete_symbols","event_type_counts",
              "queue_status_counts","true_full_758_replay")},sort_keys=True))


if __name__=="__main__":
    main()