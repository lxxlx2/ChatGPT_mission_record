#!/usr/bin/env python3
"""Source-locked original69 WATCH/47 D1 -> archived Spot quote receipt time audit.

Offline only. The captured all-market bookTicker from original Stage163 is an
historical T0 receipt, NOT 2026-10-18..24 decision-time order books. All
quotes are time-qualified BEFORE any liquidity, fee or trade interpretation.
No HTTP, orders, mail, SQLite writes, default size, or scheduled behavior.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import monster_v4_stage163_spot_t0_quote_friction as s163

SCHEMA = "MONSTER_SPOT511_REAL69_D1_D2_SOURCE_RECEIPT_TEMPORAL_JOIN_V1"
PINNED_V2_REAL69_SHA256 = "2f5e27d37c2b7ae333079b08155e392d78413212571bc681d149b4e91a1cf84c"
PINNED_ORIGINAL_4599_SHA256 = "bf8d1a1fd9916257fe39b0da1ae008fbe77e7ef35e09e1d61b24fe05641adbc1"
ALLOWED_STATES = {"RESEARCH_SETUP", "NO_SETUP", "SOURCE_UNSCORED", "LATE_UNSCORED"}
# Engineering diagnostic ONLY, not a retroactive preregistered model threshold.
MAX_ARCHIVED_RECEIPT_AGE_MS = 180_000


def _millis(iso):
    timestamp = s163.parse_utc(iso)
    return int(timestamp.timestamp() * 1000)


def load_locked_real69(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("D2_LOCKED_REAL69_FILE_REQUIRED")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PINNED_V2_REAL69_SHA256:
        raise ValueError("D2_PINNED_REAL69_BYTES_CHANGED")
    data = json.loads(raw)
    rows = data.get("sqlite_episode_rows")
    if (data.get("schema") != "MONSTER_ADR005_EXPOSED_REAL69_ORIGINAL_SQLITE_REPLAY_V1"
            or data.get("pinned_original_4599_sha256") != PINNED_ORIGINAL_4599_SHA256
            or data.get("frozen_original_watch_events") != 69
            or data.get("status_counts") != {"RESEARCH_SETUP": 47,
                 "NO_SETUP": 18, "SOURCE_UNSCORED": 4}
            or data.get("G6") != "NO_GO" or not isinstance(rows,list)
            or len(rows) != 69):
        raise ValueError("D2_ORIGINAL_RESEARCH_COHORT_DRIFT")
    ids=set()
    counts=Counter()
    setup_ids=set()
    for row in rows:
        if (not isinstance(row,dict) or row.get("status") not in ALLOWED_STATES
                or not isinstance(row.get("symbol"),str)
                or not row["symbol"].endswith("USDT")
                or not isinstance(row.get("watch_event_id"),str)
                or row["watch_event_id"] in ids
                or type(row.get("first_seen_ms")) is not int
                or row["first_seen_ms"] % 180_000
                or type(row.get("deadline_ms")) is not int
                or row["deadline_ms"]-row["first_seen_ms"] != 900_000):
            raise ValueError("D2_ORIGINAL_WATCH_IDENTITY_OR_CLOCK_DRIFT")
        ids.add(row["watch_event_id"])
        counts[row["status"]]+=1
        is_setup=row["status"]=="RESEARCH_SETUP"
        if is_setup:
            if (not isinstance(row.get("research_event_id"),str)
                    or row["research_event_id"] in setup_ids
                    or type(row.get("research_observed_ms")) is not int
                    or not row["first_seen_ms"]<=row["research_observed_ms"]<=row["deadline_ms"]):
                raise ValueError("D2_ORIGINAL_D1_SETUP_ID_OR_CLOCK_DRIFT")
            setup_ids.add(row["research_event_id"])
        elif row.get("research_event_id") is not None or row.get("research_observed_ms") is not None:
            raise ValueError("D2_NON_SETUP_WITH_RESEARCH_EVENT")
    if dict(counts)!=data["status_counts"] or len(setup_ids)!=47:
        raise ValueError("D2_COMPLETE_COHORT_STATUS_CENSUS_DRIFT")
    return rows


def classify_receipt_time(signal_ms, available_ms, *, max_age_ms=MAX_ARCHIVED_RECEIPT_AGE_MS):
    """Classify only source age vs retrospective event time, never actual fill."""
    if (type(signal_ms) is not int or type(available_ms) is not int
            or min(signal_ms, available_ms)<=0
            or type(max_age_ms) is not int or max_age_ms<0):
        raise ValueError("D2_INVALID_RECEIPT_OR_SIGNAL_CLOCK")
    if available_ms>signal_ms:
        return "ARCHIVED_QUOTE_NOT_YET_RECEIVED_AT_EVENT_CLOCK"
    if signal_ms-available_ms>max_age_ms:
        return "ARCHIVED_QUOTE_STALE_AT_EVENT_CLOCK"
    return "ARCHIVED_NON_ATOMIC_BBO_WITHOUT_EXCHANGE_QUOTE_EVENT_TIME"


def analyze(rows, quote_archive, *, max_age_ms=MAX_ARCHIVED_RECEIPT_AGE_MS):
    if not isinstance(rows,list) or len(rows)!=69:
        raise ValueError("D2_EXACT_69_RESEARCH_EVENT_ROWS_REQUIRED")
    if (quote_archive.get("source_zip_sha256")!=s163.ZIP_SHA256
            or quote_archive.get("schema")!=s163.SCHEMA
            or quote_archive.get("t0_active_spot_usdt_denominator")!=511
            or quote_archive.get("t0_causal_quote_at_t0_proven") is not False
            or quote_archive.get("eligible_for_t0_asof_executable_execution_or_signal_backtest") is not False):
        raise ValueError("D2_ARCHIVED_SPOT_QUOTE_PROVENANCE_DRIFT")
    availability=_millis(quote_archive["quote_bundle_not_available_until_client_receipt_utc"])
    roster=quote_archive["rows"]
    if (len(roster)!=511
            or len({x["symbol"] for x in roster})!=511
            or any(x.get("venue")!="BINANCE_SPOT" for x in roster)):
        raise ValueError("D2_FROZEN_SPOT_QUOTE_POPULATION_INVALID")
    symbol_roster={r["symbol"] for r in roster}
    results=[]
    counts=Counter()
    d1_counts=Counter()
    for row in rows:
        symbol=row["symbol"]
        if symbol not in symbol_roster:
            status="ARCHIVED_QUOTE_SYMBOL_NOT_IN_FROZEN_T0_ROSTER"
        else:
            status=classify_receipt_time(row["first_seen_ms"],availability,max_age_ms=max_age_ms)
        # Research D1 event exists at a distinct tick. Verify both WATCH
        # receipt and SETUP receipt separately, never equate them.
        d1status=(classify_receipt_time(row["research_observed_ms"],availability,max_age_ms=max_age_ms)
                  if row["status"]=="RESEARCH_SETUP" and symbol in symbol_roster else
                  "NO_D1_RESEARCH_SETUP" if row["status"]!="RESEARCH_SETUP" else
                  "ARCHIVED_QUOTE_SYMBOL_NOT_IN_FROZEN_T0_ROSTER")
        counts[status]+=1
        d1_counts[d1status]+=1
        results.append({
            "watch_event_id":row["watch_event_id"],
            "symbol":symbol,
            "watch_ms_retrospective":row["first_seen_ms"],
            "d1_research_status":row["status"],
            "d1_research_observed_ms_retrospective":row["research_observed_ms"],
            "watch_quote_receipt_status":status,
            "d1_quote_receipt_status":d1status,
            "archived_quote_available_at_client_receipt_ms":availability,
            "watch_vs_archived_receipt_age_ms":row["first_seen_ms"]-availability,
            "historical_quote_at_signal":False,
            "signal_time_live_ingest_proof":False,
            "source_is_original_full_depth_l2_at_signal":False,
            "user_actual_fee_or_notional_known":False,
            "actual_exit_bid_quote":None,
            "executable_net_return":None,
            "can_confirm_g4":False,
        })
    if len(results)!=69 or sum(counts.values())!=69 or sum(d1_counts.values())!=69:
        raise RuntimeError("D2_COHORT_LOSS")
    return {
        "schema":SCHEMA,
        "source_real69_v2_sha256":PINNED_V2_REAL69_SHA256,
        "archived_original_t0_zip_sha256":s163.ZIP_SHA256,
        "source_t0_ms":s163.T0_MS,
        "archived_bookticker_available_only_from_client_receipt_utc":
            quote_archive["quote_bundle_not_available_until_client_receipt_utc"],
        "engineering_receipt_max_age_ms_not_model_threshold":max_age_ms,
        "original_watch_total":69,
        "original_d1_research_setup_total":47,
        "watch_receipt_status_counts":dict(sorted(counts.items())),
        "d1_receipt_status_counts":dict(sorted(d1_counts.items())),
        "G4_signal_time_bidask_proven":0,
        "G4_total_required_independent_buy_exit_cases":30,
        "G4_grade":"UNKNOWN_NOT_ZERO_TRADABLE_COINS",
        "retroactive_archive_is_not_historical_live_receive_time":True,
        "bookticker_is_non_atomic_L1_not_future_exit_L2":True,
        "real_execution_or_profit":"NOT_OBSERVED",
        "nominal_amount":"UNSPECIFIED",
        "G1":"NOT_SCORABLE","G2":"UNKNOWN","G3":"EXPOSED_NOT_PASSED",
        "G4":"UNKNOWN","G6":"NO_GO",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_SCHEDULE":True,
        "NO_GMAIL":True,"NO_TRADES":True,
        "events":results,
    }


def run(real69_path, *, max_age_ms=MAX_ARCHIVED_RECEIPT_AGE_MS):
    rows=load_locked_real69(real69_path)
    blobs,receipts=s163.load_archived()
    archive=s163.evaluate(blobs,receipts,research_notional=None)
    return analyze(rows,archive,max_age_ms=max_age_ms)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--real69-v2-json",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--max-receipt-age-ms",type=int,default=MAX_ARCHIVED_RECEIPT_AGE_MS)
    args=p.parse_args()
    report=run(args.real69_v2_json,max_age_ms=args.max_receipt_age_ms)
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("D2_REPORT_CANNOT_OVERWRITE")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
    print(json.dumps({k:v for k,v in report.items() if k!="events"},sort_keys=True))


if __name__=="__main__":
    main()
