#!/usr/bin/env python3
"""Original Monster D0 + isolated RBTC D1 over ALL admitted frozen Spot T0 symbols.

RESEARCH-ONLY OFFLINE SOURCE-PROXY REPLAY. Formal run revalidates raw T0 HTTP
and publisher files through approved admission.run(). It then scans every
admitted symbol at each of 3360 frozen UTC 3m ticks; NO post-hoc sample
selection, BTC substitution, trading, messaging, network or scheduler.
Official *daily* bars are not proof of availability at original poll time:
even an original-core WATCH produced here is a RECONSTRUCTED_PROXY_WATCH and
MUST NOT populate G1/G2/G3 actual-prediction denominators.

The symbol-major -> tick-major spool is in a temporary isolated SQLite file.
It avoids holding every token's full 8-day Decimal tape in RAM. Source
readiness and the full original cohort are checked BEFORE replay begins.
"""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile

import monster_v4_shadow as original
import monster_v4_adr005_forward_spot_score_admission as admission
import monster_v4_adr005_forward_spot_t0_gate as t0
import monster_v4_adr005_forward_verified_minute_tape as tape
import monster_v4_d1_rbtc15_episode_research as research

SCHEMA="MONSTER_ADR005_SPOT_FROZEN_COHORT_OFFLINE_SOURCE_PROXY_D0_RBTC_D1_SWEEP_V2"
TICK_MS=180_000
FIVE_MS=300_000
EXPECTED_TICKS=t0.WINDOW_MS//TICK_MS
BTC="BTCUSDT"
INPUT_CLASS="RETROSPECTIVE_OFFICIAL_DAILY_1M_RECONSTRUCTED_PROXY_NOT_LIVE_TICKER"


def verified_cohort(report):
    """Require all frozen T0 symbols, including BTC, not merely winners."""
    if (not isinstance(report,dict)
        or report.get("schema")!=admission.SCHEMA
        or report.get("window_start_utc") not in t0.WINDOWS
        or report.get("original_market_census_venue")!="BINANCE_SPOT"
        or report.get("replay_engine_executed") is not False
        or report.get("metrics_from_future_labels_computed") is not False):
        raise ValueError("ADR005_SWEEP_AUTHENTIC_SOURCE_ADMISSION_REQUIRED")
    rows=report.get("symbols")
    if not isinstance(rows,list) or not rows or len(rows)!=report.get("original_t0_symbols_total"):
        raise ValueError("ADR005_SWEEP_T0_COHORT_INCOMPLETE")
    by={}
    for row in rows:
        if (not isinstance(row,dict) or not isinstance(row.get("symbol"),str)
            or row["symbol"] in by or not t0.SYMBOL.fullmatch(row["symbol"])
            or not row["symbol"].endswith("USDT")):
            raise ValueError("ADR005_SWEEP_INVALID_OR_DUPLICATE_SYMBOL")
        by[row["symbol"]]=row
    if BTC not in by or not report.get("btc_benchmark_research_d1_source_ready"):
        raise ValueError("ADR005_SWEEP_BTC_BENCHMARK_SOURCE_REQUIRED")
    for symbol,row in by.items():
        if (row.get("baseline_24h_source_verified") is not True
            or row.get("candidate_own_observation_7d_source_verified") is not True):
            raise ValueError("ADR005_SWEEP_ALL_T0_SYMBOLS_OBSERVATION_SOURCE_REQUIRED")
        if symbol!=BTC and row.get(
                "technically_eligible_for_offline_rbtc_d1_source_replay") is not True:
            raise ValueError("ADR005_SWEEP_CANDIDATE_RBTC_D1_SOURCE_REQUIRED")
    return by


def _spool_inputs(db, by, tape_factory, start_ms):
    db.execute("""CREATE TABLE full_market_proxy_context(
        tick_ms INTEGER NOT NULL,symbol TEXT NOT NULL,
        price TEXT NOT NULL,quote24 TEXT NOT NULL)""")
    inserted=0
    for symbol in sorted(by):
        minute=tape_factory(symbol)
        if minute.symbol!=symbol or minute.start_ms!=start_ms:
            raise ValueError("ADR005_SWEEP_TAPE_IDENTITY_OR_START_DRIFT")
        tuples=[]
        for tick in range(start_ms,start_ms+t0.WINDOW_MS,TICK_MS):
            row=minute.original_d0_context(tick)
            if row["symbol"]!=symbol:
                raise ValueError("ADR005_SWEEP_MINUTE_CONTEXT_IDENTITY_DRIFT")
            tuples.append((tick,symbol,row["lastPrice"],row["quoteVolume"]))
        db.executemany("INSERT INTO full_market_proxy_context VALUES(?,?,?,?)",tuples)
        inserted+=len(tuples)
    expected=len(by)*EXPECTED_TICKS
    if inserted!=expected:
        raise RuntimeError("ADR005_SWEEP_ORIGINAL_COHORT_SPOOL_INCOMPLETE")
    db.execute("CREATE UNIQUE INDEX full_market_proxy_tick_symbol ON full_market_proxy_context(tick_ms,symbol)")
    db.commit()
    return inserted


def _create_bridge_watch_ledger(db):
    """An independent intake audit; never edits frozen research episode state.

    Every non-BTC original WATCH has exactly one row. A second original WATCH
    while this venue/symbol has a pending research episode is explicitly
    overlap-censored (not admitted, not a NO_SETUP, never silently dropped).
    """
    db.execute("""CREATE TABLE bridge_watch_disposition (
        original_watch_event_id TEXT PRIMARY KEY,
        venue TEXT NOT NULL,
        symbol TEXT NOT NULL,
        original_watch_ms INTEGER NOT NULL,
        research_admission_status TEXT NOT NULL
            CHECK(research_admission_status IN
                ('ADMITTED_EPISODE','OVERLAP_PENDING_UNSCORED')),
        blocking_pending_episode_watch_event_id TEXT,
        CHECK((research_admission_status='ADMITTED_EPISODE'
               AND blocking_pending_episode_watch_event_id IS NULL)
           OR (research_admission_status='OVERLAP_PENDING_UNSCORED'
               AND blocking_pending_episode_watch_event_id IS NOT NULL))
    )""")


def _bridge_original_watch(db,event):
    """Preserve original WATCH identity and the unmodified one-PENDING contract.

    This is deliberately *not* a fake terminal-state transition. An overlap
    has no complete independent episode and remains UNSCORED for this offline
    source-proxy replay; later research opportunities must not be backfilled.
    """
    if (event["venue"]!="spot" or event["event_type"]!="WATCH_EARLY"
        or event["symbol"]==BTC or type(event["observed_ms"]) is not int
        or event["observed_ms"]%TICK_MS
        or event["event_id"]!=original.event_key(
            event["venue"],event["symbol"],"WATCH_EARLY",event["observed_ms"])):
        raise ValueError("ADR005_SWEEP_BRIDGE_ORIGINAL_WATCH_IDENTITY_INVALID")
    exists=db.execute(
        "SELECT 1 FROM bridge_watch_disposition WHERE original_watch_event_id=?",
        (event["event_id"],)).fetchone()
    if exists is not None:
        raise RuntimeError("ADR005_SWEEP_DUPLICATE_ORIGINAL_WATCH_BRIDGE")
    overlapping=db.execute(
        "SELECT watch_event_id FROM episode "
        "WHERE venue=? AND symbol=? AND status='PENDING'",
        (event["venue"],event["symbol"])).fetchone()
    if overlapping is not None:
        blocking=overlapping["watch_event_id"]
        if blocking==event["event_id"]:
            raise RuntimeError("ADR005_SWEEP_SAME_WATCH_PENDING_REPLAY_DRIFT")
        status="OVERLAP_PENDING_UNSCORED"
    else:
        if not research.admit_original_watch(db,event):
            raise RuntimeError("ADR005_SWEEP_DUPLICATE_RESEARCH_EPISODE")
        blocking=None
        status="ADMITTED_EPISODE"
    with db:
        db.execute("""INSERT INTO bridge_watch_disposition
            (original_watch_event_id,venue,symbol,original_watch_ms,
             research_admission_status,blocking_pending_episode_watch_event_id)
            VALUES(?,?,?,?,?,?)""",
            (event["event_id"],event["venue"],event["symbol"],
             event["observed_ms"],status,blocking))
    return status


def replay_with_source_tapes(report,tape_factory,workdir):
    """Pure injectable test seam; synthetic callers are NOT authenticated.

    The public run() is the ONLY formal path: it independently reopens the
    actual original HTTP ZIP/receipt and each official issuer checksum first.
    Neither this helper nor test fixture results prove PIT or real OOS.
    """
    by=verified_cohort(report)
    if not callable(tape_factory):
        raise ValueError("ADR005_SWEEP_SOURCE_TAPE_FACTORY_REQUIRED")
    start_ms=t0.frozen_window(report["window_start_utc"])//1000
    root=Path(workdir)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("ADR005_SWEEP_ISOLATED_WORKDIR_REQUIRED")
    store_path=root/"original-proxy-d0.sqlite"
    research_path=root/"independent-rbtc-d1.sqlite"
    if any(x.exists() or x.is_symlink() for x in (store_path,research_path)):
        raise ValueError("ADR005_SWEEP_REFUSE_PREEXISTING_DATABASE")
    original_db=original.open_store(store_path)
    research_db=None
    try:
        count=_spool_inputs(original_db,by,tape_factory,start_ms)
        research_db=research.create_ledger(research_path)
        _create_bridge_watch_ledger(research_db)
        # Only the needed active research symbols and BTC are cached during
        # time-major scanning, with a hard cap independent of T0 cohort size.
        @lru_cache(maxsize=10)
        def closed_source(symbol):
            if symbol not in by:
                raise ValueError("ADR005_SWEEP_RESEARCH_TARGET_NOT_IN_T0")
            item=tape_factory(symbol)
            if item.symbol!=symbol or item.start_ms!=start_ms:
                raise ValueError("ADR005_SWEEP_RBTC_SOURCE_IDENTITY_DRIFT")
            return item

        admitted_watch=0
        overlap_unscored_watch=0
        btc_d0_watches=0
        polls=0
        for tick in range(start_ms,start_ms+t0.WINDOW_MS,TICK_MS):
            records=original_db.execute(
                "SELECT symbol,price,quote24 FROM full_market_proxy_context "
                "WHERE tick_ms=? ORDER BY symbol",(tick,)).fetchall()
            if len(records)!=len(by) or len({r["symbol"] for r in records})!=len(by):
                raise RuntimeError("ADR005_SWEEP_INCOMPLETE_TICK_DENOMINATOR")
            result=original.observe_snapshot(original_db,"spot",tick,[
                {"symbol":r["symbol"],"lastPrice":r["price"],
                 "quoteVolume":r["quote24"]} for r in records])
            if (result["valid"]!=len(by) or result["invalid"]!=0
                or result["source_total"]!=len(by)):
                raise RuntimeError("ADR005_SWEEP_D0_REJECTED_ORIGINAL_MARKET_MEMBER")
            emitted=original_db.execute(
                "SELECT event_id,venue,symbol,event_type,observed_ms "
                "FROM events WHERE event_type='WATCH_EARLY' AND observed_ms=? "
                "ORDER BY event_id",(tick,)).fetchall()
            if len(emitted)!=result["watch_new"]:
                raise RuntimeError("ADR005_SWEEP_WATCH_EVENT_LEDGER_COUNT_DRIFT")
            for event in emitted:
                if event["symbol"]==BTC:
                    btc_d0_watches+=1
                    continue
                classification=_bridge_original_watch(research_db,dict(event))
                if classification=="ADMITTED_EPISODE":
                    admitted_watch+=1
                elif classification=="OVERLAP_PENDING_UNSCORED":
                    overlap_unscored_watch+=1
                else:
                    raise RuntimeError("ADR005_SWEEP_UNKNOWN_RESEARCH_BRIDGE_DISPOSITION")
            def fetch_closed(symbol,at_tick):
                return closed_source(symbol).six_closed_5m(at_tick)
            research.poll_episodes(research_db,tick,fetch_closed)
            polls+=1
        episodes=research.summary(research_db)
        count_d0=original_db.execute(
            "SELECT COUNT(*) FROM events WHERE event_type='WATCH_EARLY'").fetchone()[0]
        dispositions=[dict(row) for row in research_db.execute(
            """SELECT d.original_watch_event_id,d.venue,d.symbol,
               d.original_watch_ms,d.research_admission_status,
               d.blocking_pending_episode_watch_event_id,
               blocker.status AS blocking_episode_status_at_window_end
               FROM bridge_watch_disposition d
               LEFT JOIN episode blocker
                 ON blocker.watch_event_id=d.blocking_pending_episode_watch_event_id
               ORDER BY d.original_watch_ms,d.original_watch_event_id""")]
        status_counts=Counter(x["research_admission_status"] for x in dispositions)
        if (polls!=EXPECTED_TICKS
            or count_d0!=admitted_watch+overlap_unscored_watch+btc_d0_watches
            or len(dispositions)!=admitted_watch+overlap_unscored_watch
            or status_counts["ADMITTED_EPISODE"]!=admitted_watch
            or status_counts["OVERLAP_PENDING_UNSCORED"]!=overlap_unscored_watch
            or any(x["research_admission_status"]=="OVERLAP_PENDING_UNSCORED"
                and x["blocking_episode_status_at_window_end"] is None
                for x in dispositions)
            or episodes["episodes"]!=admitted_watch
            or sum(episodes["status_counts"].values())!=admitted_watch):
            raise RuntimeError("ADR005_SWEEP_EVENT_DENOMINATOR_MISMATCH")
        originals=original_db.execute(
            "SELECT event_id,symbol,observed_ms FROM events "
            "WHERE event_type='WATCH_EARLY' ORDER BY observed_ms,event_id").fetchall()
        digest=hashlib.sha256("".join(
            f"{r['event_id']}\t{r['symbol']}\t{r['observed_ms']}\n"
            for r in originals).encode()).hexdigest()
        return {
            "schema":SCHEMA,
            "window_start_utc":report["window_start_utc"],
            "original_spot_t0_symbol_population":len(by),
            "all_t0_market_symbols_seen_every_poll":True,
            "utc_3minute_full_cohort_polls":polls,
            "source_proxy_context_rows":count,
            "actual_live_24h_ticker_at_original_tick_proven":False,
            "true_original_pit_event_stream_proven":False,
            "source_input_class":INPUT_CLASS,
            "proxy_original_d0_watch_count":count_d0,
            "proxy_btc_d0_watch_excluded_from_research":btc_d0_watches,
            "proxy_nonbtc_original_d0_watch_count":
                admitted_watch+overlap_unscored_watch,
            "proxy_research_D1_admitted_episode_count":admitted_watch,
            "proxy_research_D1_overlap_pending_unscored_watch_count":
                overlap_unscored_watch,
            "proxy_research_D1_original_watch_bridge_status_counts":
                dict(sorted(status_counts.items())),
            "proxy_research_D1_original_watch_bridge_rows":dispositions,
            "overlap_pending_watches_are_research_negative_labels":False,
            "overlap_pending_watches_are_research_setups":False,
            "proxy_original_d0_watch_canonical_sha256":digest,
            "proxy_original_d0_watch_rows":[dict(x) for x in originals],
            "proxy_original_d0_invalidated_rows":[dict(x) for x in
                original_db.execute(
                    "SELECT event_id,symbol,observed_ms FROM events "
                    "WHERE event_type='INVALIDATED' "
                    "ORDER BY observed_ms,event_id")],
            "isolated_proxy_research_D1_episode_count":episodes["episodes"],
            "isolated_proxy_research_D1_status_counts":episodes["status_counts"],
            "isolated_proxy_research_D1_rows":episodes["rows"],
            "right_edge_pending_episodes_not_false_negatives":
                episodes["status_counts"].get("PENDING",0),
            "original_engine_code_modified":False,
            "research_queue_code_modified":False,
            "proxy_watch_events_are_real_historical_signals":False,
            "proxy_setup_events_are_real_historical_signals":False,
            "can_score_preregistered_forward_G1_G2_G3":False,
            "G0":"PARTIAL_RECONSTRUCTED_NOT_PIT",
            "G1":"NOT_SCORABLE","G2":"UNKNOWN","G3":"NOT_SCORABLE",
            "G4":"UNKNOWN","G5":"NEW_FULL_COHORT_REPLAY_REVIEW_PENDING",
            "G6":"NO_GO",
            "NO_MERGE":True,"NO_DEPLOY":True,"NO_MAC":True,
            "NO_AUTOMATIONS":True,"NO_GMAIL":True,"NO_TRADES":True,
            "NO_NEW_RPC":True,
        }
    finally:
        if research_db is not None:
            research_db.close()
        original_db.close()


def run(start,asof,source_zip,receipts,publisher_root):
    """Only formal entry: SHA-backed full-cohort source readmission required."""
    report=admission.run(start,asof,source_zip,receipts,publisher_root)
    by=verified_cohort(report)
    with tempfile.TemporaryDirectory(prefix="monster-adr005-replay-") as temp:
        def tape_factory(symbol):
            return tape.VerifiedForwardSpotMinuteTape(
                publisher_root,symbol,start,asof,by[symbol])
        outcome=replay_with_source_tapes(report,tape_factory,temp)
        if outcome["original_spot_t0_symbol_population"]!=report["original_t0_symbols_total"]:
            raise RuntimeError("ADR005_SWEEP_SOURCE_T0_DENOMINATOR_DRIFT")
        outcome["t0_original_raw_http_zip_sha256"]=report["source_from_admitted_t0_archive_sha256"]
        return outcome


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--window-start-utc",required=True,choices=t0.WINDOWS)
    p.add_argument("--asof-utc",required=True)
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--source-receipts",type=Path,required=True)
    p.add_argument("--publisher-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists() or a.out.is_symlink():
        raise ValueError("ADR005_SWEEP_REFUSE_OVERWRITE")
    outcome=run(a.window_start_utc,a.asof_utc,a.source_zip,
                a.source_receipts,a.publisher_root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("x",encoding="utf-8") as stream:
        json.dump(outcome,stream,sort_keys=True,indent=2,ensure_ascii=False)
        stream.write("\n")
    print("MONSTER_ADR005_RETROSPECTIVE_SOURCE_PROXY_ALL_T0_SPOT_SYMBOLS_ONLY",
          json.dumps({k:v for k,v in outcome.items()
                      if k not in ("proxy_original_d0_watch_rows",
                                   "proxy_original_d0_invalidated_rows",
                                   "proxy_research_D1_original_watch_bridge_rows",
                                   "isolated_proxy_research_D1_rows")},
                     sort_keys=True))


if __name__=="__main__":
    main()
