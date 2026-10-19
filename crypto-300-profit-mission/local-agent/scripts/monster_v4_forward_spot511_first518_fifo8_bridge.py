#!/usr/bin/env python3
"""Read-only first 518 real-publisher 1m-source Spot511 -> frozen D0 / D1 FIFO8 research.

Historical *post-publication* reconstructed rolling quote24 is a 1m proxy.
This does not reconstruct real exchange ticker24, PIT listing, L2 or live alerts.
No schedules, exchange API calls, mail, orders or production DB access.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import zipfile

import monster_v4_historical_replay as minute
import monster_v4_shadow as production
import monster_v4_shared_spot_d0_d1_original_core as original
import monster_v4_shared_d1_zeroquote_research_v2 as zeroq
import monster_v4_stage166_spot511_official_1m_intake as admitted

EVIDENCE = Path(__file__).resolve().parents[2] / "monster/evidence"
SCHEMA = "MONSTER_FORWARD_SPOT511_FIRST518_OFFICIAL_1M_CAUSAL_PROXY_FIFO8_V1"
DAY_UTC = ("2026-10-16", "2026-10-17", "2026-10-18")
START = int(datetime(2026, 10, 17, 22, 6, tzinfo=timezone.utc).timestamp()*1000)
END = int(datetime(2026, 10, 19, tzinfo=timezone.utc).timestamp()*1000)
TICK_MS = 180000
EXPECTED_TICKS = 518
MIN_MS = 60000
EXPECTED_BARS = 4320
RECEIPTS = (
    ("monster_forward_spot511_oct16_17_real_issuer_zip_receipts_v1.json",
     "issuer_real_zip_receipts", "date_utc", "checksum_sha256"),
    ("monster_forward_spot511_unicode4_original_publisher_supplement_v1.json",
     "actual_items", "date_utc", "publisher_checksum_sha256"),
    ("monster_forward_spot511_oct18_real_issuer_zip_receipts_v1.json",
     "original_source_pair_receipts", "source_day", "publisher_checksum_sha256"),
)

def evidence_receipts(roster):
    expected = {(symbol, day) for symbol in roster for day in DAY_UTC}
    accepted = {}
    for filename, field, date_field, checksum_field in RECEIPTS:
        doc = json.loads((EVIDENCE/filename).read_text(encoding="utf-8"))
        for item in doc[field]:
            key = (item["symbol"], item[date_field])
            if item["status"] != "VERIFIED_FULL_DAY_1440":
                # The original Oct16-17 4 failed Unicode requests are
                # superseded by only the separately verified 4 publisher files.
                if filename == RECEIPTS[0][0] and key[0] in (
                    "币安人生USDT", "牛来USDT") and key[1] in DAY_UTC[:2]:
                    continue
                raise ValueError("MONSTER518_UNEXPECTED_SOURCE_FAILURE")
            if key not in expected or key in accepted:
                raise ValueError("MONSTER518_DUPLICATE_OR_FOREIGN_SOURCE_RECEIPT")
            zsha = item.get("zip_sha256", item.get("original_zip_sha256"))
            csha = item[checksum_field]
            if not all(isinstance(x, str) and len(x)==64
                       and all(c in "0123456789abcdef" for c in x)
                       for x in (zsha,csha)):
                raise ValueError("MONSTER518_SOURCE_SHA_FORMAT_INVALID")
            accepted[key] = (zsha, csha)
    if set(accepted) != expected or len(accepted) != 1533:
        raise ValueError("MONSTER518_INCOMPLETE_FROZEN_511_X_3_RECEIPTS")
    return accepted

def source_files(directories):
    zips = {}
    checksums = {}
    for root in directories:
        for path in Path(root).rglob("*"):
            if not path.is_file():
                continue
            if path.name.endswith(".zip.CHECKSUM"):
                target = checksums
            elif path.name.endswith(".zip"):
                target = zips
            else:
                continue
            if path.name in target:
                raise ValueError("MONSTER518_DUPLICATED_ORIGINAL_ARCHIVE_NAME")
            target[path.name] = path
    return zips, checksums

def tick_input(tick_ms, start_ms, prefix, bars):
    """Use only completed minutes before an observation tick."""
    i = (tick_ms-start_ms)//MIN_MS-1
    if i < 1439 or i >= len(bars) or bars[i][0]+MIN_MS != tick_ms:
        raise ValueError("MONSTER518_MISSING_CLOSED_MINUTE_AT_TICK")
    q = prefix[i+1]-prefix[i-1439]
    if q < 0:
        raise ValueError("MONSTER518_INVALID_ROLLING_QUOTE")
    return (tick_ms, bars[i][4], q)

def parse_symbol_three_days(symbol, receipts, zips, checksums):
    out=[]
    verified=[]
    for day in DAY_UTC:
        name=f"{symbol}-1m-{day}.zip"
        zp=zips.get(name)
        cp=checksums.get(name+".CHECKSUM")
        if zp is None or cp is None:
            raise ValueError("MONSTER518_ORIGINAL_PUBLISHER_BYTES_MISSING")
        actual=admitted.validate_daily_zip(zp,cp,symbol,date.fromisoformat(day))
        want_z,want_c=receipts[(symbol,day)]
        if (actual["zip_sha256"]!=want_z
                or hashlib.sha256(cp.read_bytes()).hexdigest()!=want_c):
            raise ValueError("MONSTER518_GIT_RECEIPT_ARTIFACT_SHA_MISMATCH")
        with zipfile.ZipFile(zp) as archive:
            csvname=f"{symbol}-1m-{day}.csv"
            with archive.open(csvname) as inp:
                rd=csv.reader(io.TextIOWrapper(inp,encoding="utf-8",newline=""))
                day_rows=[]
                for row in rd:
                    day_rows.append((
                        int(row[0])//1000,
                        Decimal(row[1]),Decimal(row[2]),Decimal(row[3]),
                        Decimal(row[4]),Decimal(row[7]),int(row[8])))
        if len(day_rows)!=1440:
            raise ValueError("MONSTER518_AFTER_VALIDATION_SOURCE_ROW_DRIFT")
        out.extend(day_rows)
        verified.append({"date":day,"sha256":want_z})
    if len(out)!=EXPECTED_BARS or any(
            out[i][0] != out[0][0]+i*MIN_MS for i in range(EXPECTED_BARS)):
        raise ValueError("MONSTER518_CONTINUOUS_THREE_DAYS_REQUIRED")
    return out,verified

def build(source_dirs):
    roster = admitted.frozen_roster()
    if len(roster)!=511:
        raise ValueError("MONSTER518_ORIGINAL_T0_ROSTER_DRIFT")
    receipt_map=evidence_receipts(roster)
    zips,checksums=source_files(source_dirs)
    if len(zips)!=1533 or len(checksums)!=1533:
        raise ValueError("MONSTER518_ACTUAL_ARTIFACT_1533_PAIRS_REQUIRED")
    valid_ascii=tuple(x for x in roster if x.isascii())
    unicode_missing=[x for x in roster if not x.isascii()]
    if len(valid_ascii)!=509 or len(unicode_missing)!=2:
        raise ValueError("MONSTER518_UNICODE_MODEL_SCOPE_CHANGED")
    with tempfile.TemporaryDirectory(prefix="monster518_readonly_") as work:
        source = original.setup_cache(Path(work)/"verified_source.sqlite")
        try:
            for symbol in roster:
                bars,_proof=parse_symbol_three_days(
                    symbol,receipt_map,zips,checksums)
                prefix=[Decimal(0)]
                for row in bars:
                    prefix.append(prefix[-1]+row[5])
                ticks=[]
                for tick in range(START,END,TICK_MS):
                    at,last,q=tick_input(tick,bars[0][0],prefix,bars)
                    ticks.append((at,symbol,str(last),str(q)))
                candles=minute.make_closed_five_minute_bars(bars)
                with source:
                    source.executemany(
                        "INSERT INTO tick_source VALUES(?,?,?,?)",ticks)
                    source.executemany(
                        "INSERT INTO closed5m_source VALUES(?,?,?)",
                        ((symbol,int(c[6]),json.dumps(c)) for c in candles))
                    source.execute(
                        "INSERT INTO source_receipts VALUES(?,?)",
                        (symbol,json.dumps(_proof,sort_keys=True)))
            n=source.execute("SELECT COUNT(*) FROM tick_source").fetchone()[0]
            if n!=511*EXPECTED_TICKS:
                raise ValueError("MONSTER518_SOURCE_POLL_POPULATION_INCOMPLETE")
            shadow=production.open_store(Path(work)/"frozen_D0_D1.sqlite")
            stats={"zero_quote_source_slots_consumed":0,
                   "terminal_unsupported":0,"by_symbol":Counter(),
                   "max_slots_in_single_tick":0}
            totals=Counter()
            try:
                def verified_5m(venue,symbol,tick):
                    return original.verified_closed_5m_for_original_d1(
                        source,valid_ascii,venue,symbol,tick)
                for tick in range(START,END,TICK_MS):
                    rows=source.execute(
                        "SELECT symbol,last_price,past24h_quote FROM tick_source "
                        "WHERE tick_ms=? ORDER BY symbol",(tick,)).fetchall()
                    if len(rows)!=511 or [x[0] for x in rows]!=roster:
                        raise ValueError("MONSTER518_NON_ATOMIC_GLOBAL_POPULATION")
                    d0=production.observe_snapshot(shadow,"spot",tick,[
                        {"symbol":x[0],"lastPrice":x[1],"quoteVolume":x[2]}
                        for x in rows])
                    if d0["source_total"]!=511 or d0["valid"]!=509 or d0["invalid"]!=2:
                        raise ValueError("MONSTER518_PRODUCTION_D0_UNICODE_UNEXPECTED")
                    d1=zeroq.experimental_queue_handler(
                        shadow,tick,verified_5m,source,limit=8,
                        original_queue=production.process_queue,stats=stats)
                    totals["poll_ticks"]+=1
                    totals["watch_new"]+=d0["watch_new"]
                    for k,v in d1.items():
                        totals["D1_"+k]+=v
                events=[dict(x) for x in shadow.execute(
                    "SELECT event_id,venue,symbol,event_type,observed_ms,payload "
                    "FROM events ORDER BY observed_ms,event_id")]
                queue=[dict(x) for x in shadow.execute(
                    "SELECT id,venue,symbol,first_seen_ms,deadline_ms,status,"
                    "last_error,last_evaluated_bar_ms FROM candidate_queue "
                    "ORDER BY first_seen_ms,id")]
            finally:
                shadow.close()
        finally:
            source.close()
    counts=Counter(x["event_type"] for x in events)
    qcounts=Counter(x["status"] for x in queue)
    if totals["poll_ticks"]!=EXPECTED_TICKS or totals["watch_new"]!=counts["WATCH_EARLY"]:
        raise ValueError("MONSTER518_EVENT_OR_CLOCK_DRIFT")
    if stats["max_slots_in_single_tick"]>8 or len(queue)!=counts["WATCH_EARLY"]:
        raise ValueError("MONSTER518_FIFO8_QUEUE_INVARIANT_DRIFT")
    return {
        "schema":SCHEMA,
        "source_calendar_days":list(DAY_UTC),
        "frozen_T0_spot_USDT_TRADING":len(roster),
        "publisher_verified_zip_checksum_pairs":len(receipt_map),
        "publisher_verified_closed_1m_bars":len(roster)*EXPECTED_BARS,
        "first_poll_utc":"2026-10-17T22:06:00Z",
        "end_exclusive_utc":"2026-10-19T00:00:00Z",
        "strict_3m_global_polls":EXPECTED_TICKS,
        "global_tick_source_rows":511*EXPECTED_TICKS,
        "original_production_D0_valid_symbols_per_tick":509,
        "original_production_D0_invalid_unicode_symbols_per_tick":unicode_missing,
        "source_all_511_included_but_D0_still_excludes_unicode":True,
        "ticker24_source":"CLOSED_1M_1440_ROLLING_QUOTE_PROXY_NOT_BINANCE_TICKER24",
        "real_streaming_ticker24_PIT":False,
        "venue":"spot",
        "D0_original_function_unchanged":True,
        "D1_FIFO8_original_for_supported_source":True,
        "D1_zero_quote_uses_existing_research_V2_not_production":True,
        "queue_at_partial_right_boundary_may_be_pending":True,
        "partial_window_not_final_OOS":True,
        "D0_D1_totals":dict(totals),
        "event_type_counts":dict(counts),
        "queue_status_counts":dict(qcounts),
        "zero_quote_unsupported_attempt_slots":stats["zero_quote_source_slots_consumed"],
        "zero_quote_terminal_candidates":stats["terminal_unsupported"],
        "WATCH_event_identity": [
            {"event_id":x["event_id"],"symbol":x["symbol"],
             "observed_ms":x["observed_ms"]}
            for x in events if x["event_type"]=="WATCH_EARLY"],
        "SETUP_event_identity": [
            {"event_id":x["event_id"],"symbol":x["symbol"],
             "observed_ms":x["observed_ms"]}
            for x in events if x["event_type"]=="SETUP_ACTIVE"],
        "full_OOS_7d_replay":"NOT_DONE",
        "point_in_time_dynamic_listing":"UNVERIFIED",
        "trades_fills_L2_fees_bid_ask":"UNVERIFIED",
        "executable_net_profit":"UNKNOWN",
        "independent_other_AI_review":"NOT_DONE",
        "G0":"PARTIAL","G4":"UNKNOWN","G6":"NO_GO",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_GMAIL":True,"NO_TRADE":True
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,action="append",required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists() or a.out.is_symlink():
        raise ValueError("MONSTER518_OUTPUT_EXISTS_REFUSE_OVERWRITE")
    result=build(a.source_dir)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
                     encoding="utf-8")
    print("MONSTER518_REAL_PUBLISHER_PARTIAL_CAUSAL_D0_D1_REPLAY",
          json.dumps({k:result[k] for k in
            ("strict_3m_global_polls","event_type_counts","queue_status_counts",
             "G0","G4","G6")},ensure_ascii=False,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
