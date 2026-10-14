#!/usr/bin/env python3
"""Stage131: fail-closed retrospective all31 and forward population join scaffold.

No model fitting, net PnL, live data, scheduler, notifier or deployment.
Everything that lacks point-in-time venue+crypto identity proof remains UNKNOWN.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import monster_v4_stage105_capture_universe_core as stage105
import monster_v4_stage129_new_listings_hourly_recovery as stage129

E = Path(__file__).resolve().parents[2] / "monster" / "evidence"
SOURCE = E / "monster_stage130_original31_publisher_sha1m_momentum_archived_summary_20261014.json"
SOURCE_BLOB_SHA = "5777616368f781e3a9db30550f75c39845d11e54"
SOURCE_RAW_SHA256 = "a97037bff9d834f0f59fb3a0ae45942a9c28453dbfc0d01331fd78afa49b8f50"
SCHEMA = "MONSTER_STAGE131_DYNAMIC_LISTING_G1_HISTORICAL_POPULATION_LEDGER_V1"
DAYS = ("2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19")
EXPECTED_PER_DATE = (5,5,5,4,4,8)
WINDOW_MS = 168*60*60*1000
MINUTE_MS = 60000


def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()


def stamp(iso):
    if not isinstance(iso,str) or not iso.endswith("Z"):
        raise ValueError("STAGE131_UTC_TIMESTAMP_REQUIRED")
    try:
        dt=datetime.fromisoformat(iso.replace("Z","+00:00"))
    except ValueError:
        raise ValueError("STAGE131_UTC_TIMESTAMP_INVALID") from None
    if dt.utcoffset().total_seconds()!=0 or dt.second or dt.microsecond:
        raise ValueError("STAGE131_REQUIRE_MINUTE_ALIGNED_UTC")
    return int(dt.timestamp()*1000)


def decode_source(path=SOURCE):
    raw=Path(path).read_bytes()
    if git_blob(raw)!=SOURCE_BLOB_SHA:
        raise ValueError("STAGE131_SOURCE_GIT_BLOB_CHANGED")
    obj=json.loads(raw)
    if obj.get("schema")!="MONSTER_STAGE130_SOURCE_LOCKED_EXPOSED31_CONCISE_ALL_CASES_V1" or obj.get("raw_full31_json_SHA256")!=SOURCE_RAW_SHA256:
        raise ValueError("STAGE131_WRONG_STAGE130_ORIGINAL_SOURCE")
    rows=obj.get("rows")
    if not isinstance(rows,list) or len(rows)!=31 or obj.get("all31_complete")!=31 or obj.get("original_verified_daily_zip_receipts")!=147:
        raise ValueError("STAGE131_ORIGINAL31_OR_SHA_RECEIPTS_CHANGED")
    return obj


def check_historical(obj, later_meta):
    rows=obj["rows"]
    result=[]
    seen=set()
    counts=Counter()
    totals=Counter()
    for r in rows:
        day,symbol=r.get("anchor"),r.get("symbol")
        if day not in DAYS or not stage105.valid_exact_venue_symbol(symbol) or not symbol.endswith("USDT"):
            raise ValueError("STAGE131_INVALID_EXACT_SYMBOL_OR_FROZEN_DATE")
        key=(day,symbol)
        if key in seen:
            raise ValueError("STAGE131_DUPLICATE_HISTORICAL_SYMBOL_DATE")
        seen.add(key)
        counts[day]+=1
        start=stamp(day+"T06:00:00Z")
        end=start+WINDOW_MS
        first=stamp(r.get("first_1m_utc"))
        first_signal=stamp(r["first_momentum_utc"]) if r.get("first_momentum_utc") else None
        first_high=stamp(r["first_gross2x_high_1m_utc"]) if r.get("first_gross2x_high_1m_utc") else None
        if not start<=first<end or not isinstance(r.get("minute_bars"),int) or isinstance(r["minute_bars"],bool) or r["minute_bars"]<=0:
            raise ValueError("STAGE131_HISTORICAL_MINUTE_SOURCE_OUTSIDE_WINDOW")
        if first+r["minute_bars"]*MINUTE_MS!=end:
            raise ValueError("STAGE131_HISTORICAL_MINUTE_SOURCE_WINDOW_GAP")
        if first_signal is not None and (not first+MINUTE_MS<=first_signal<end or first_signal%(3*MINUTE_MS)!=0):
            raise ValueError("STAGE131_NONCAUSAL_FIRST_MOMENTUM_CLOCK")
        if first_high is not None and not first<=first_high<end:
            raise ValueError("STAGE131_FUTURE_2X_LABEL_OUTSIDE_WINDOW")
        cnt=r.get("publisher_daily_zip_sha_receipts")
        if type(cnt) is not int or cnt<1:
            raise ValueError("STAGE131_PUBLISHER_RECEIPT_COUNT_INVALID")
        totals["receipts"]+=cnt
        totals["bars"]+=r["minute_bars"]
        totals["first_momentum_triggers"]+=first_signal is not None
        totals["posthoc_gross_2x"]+=first_high is not None
        early=(first_signal is not None and first_high is not None
               and first_signal+5*MINUTE_MS<=first_high)
        totals["posthoc_gross_2x_early5"]+=early
        ref=later_meta.get(key)
        if ref is None or ref["analysis_status"]!="COMPLETE_FROM_FIRST_OBSERVED_1H_TO_END_PRICE_PROXY_ONLY":
            raise ValueError("STAGE131_HISTORIC_HOURLY_JOIN_INCOMPLETE")
        if ref["first_1h_open_utc"][:13]!=r["first_1m_utc"][:13]:
            raise ValueError("STAGE131_NEW_LISTING_FIRST_HOUR_NOT_MATCHED")
        result.append({
            "window_anchor":day,"venue":"BINANCE_USDM",
            "symbol_exact":symbol,"population_lane":"IN_WINDOW_FIRST_TRADABLE_MINUTE_CANDIDATE",
            "origin":"ORIGINAL_31_EXPOSED_HISTORIC_COHORT",
            "first_observed_1m_open_utc":r["first_1m_utc"],
            "first_minute_close_theoretical_observable_utc":datetime.fromtimestamp((first+MINUTE_MS)/1000,timezone.utc).isoformat().replace("+00:00","Z"),
            "first_frozen_momentum_research_signal_utc":r.get("first_momentum_utc"),
            "first_2x_high_utc_posthoc_evaluation_only":r.get("first_gross2x_high_1m_utc"),
            "research_momentum_early5_vs_gross_2x_posthoc":early if first_high is not None else None,
            "publisher_minute_bars_verified_in_stage130":r["minute_bars"],
            "publisher_zip_checksum_receipts_in_stage130":cnt,
            "later_exchange_underlyingType_label_not_asof_issuer":ref.get("later_exchange_claim_underlyingType"),
            "issuer_identity_asof":"UNVERIFIED",
            "venue_listing_and_orderbook_status_asof":"UNVERIFIED",
            "execution_fee_impact_and_exit":"UNKNOWN",
            "is_original_Stage116_full_week_replay_row":False,
            "new_model_oos":False,
            "eligible_to_claim_G1_crypto_success":False,
            "gross_first_open_to_max_high_multiple_posthoc":r.get("max_high_multiple_FirstOpen_rounded"),
        })
    if [counts[d] for d in DAYS]!=list(EXPECTED_PER_DATE) or totals!=Counter({"receipts":147,"bars":159675,"first_momentum_triggers":19,"posthoc_gross_2x":2,"posthoc_gross_2x_early5":2}):
        raise ValueError("STAGE131_EXPOSED31_REAL_SOURCE_AGGREGATE_DRIFT")
    return sorted(result,key=lambda x:(x["window_anchor"],x["symbol_exact"])),totals


def reconcile_population(window, start_rows, later_rows):
    """Pure future two-lane attempt census. This helper CANNOT attest G0.

    Must be fed independently authenticated capture evidence by a higher layer;
    supplied rows/booleans never confer real exchange proof.
    """
    start=stamp(window)
    end=start+WINDOW_MS
    observed=set()
    rows=[]
    for lane,group in (("PREEXISTING_AT_WINDOW_START",start_rows),
                       ("IN_WINDOW_FIRST_TRADABLE_MINUTE_CANDIDATE",later_rows)):
        if not isinstance(group,list):
            raise ValueError("STAGE131_COHORT_ARRAY_REQUIRED")
        for item in group:
            symbol=item.get("symbol") if isinstance(item,dict) else None
            if not stage105.valid_exact_venue_symbol(symbol) or not symbol.endswith("USDT"):
                raise ValueError("STAGE131_COHORT_SYMBOL_INVALID")
            if symbol in observed:
                raise ValueError("STAGE131_COHORT_DOUBLE_COUNT_OR_LISTING_REUSE")
            observed.add(symbol)
            at=item.get("first_observed_minute_utc")
            if lane.startswith("IN_WINDOW"):
                obs=stamp(at)
                if not start<=obs<end:
                    raise ValueError("STAGE131_LATE_LISTING_MINUTE_OUTSIDE_FROZEN_WINDOW")
            elif at is not None:
                # Before-window start candidates need not have a "listing" event.
                raise ValueError("STAGE131_START_COHORT_MUST_NOT_CARRY_NEW_LISTING_TIME")
            rows.append({
                "window_anchor":window, "venue":"BINANCE_USDM",
                "symbol_exact":symbol, "population_lane":lane,
                "first_observed_minute_utc":at if lane.startswith("IN_WINDOW") else None,
                "source_status":item.get("source_status","UNVERIFIED"),
                "asof_trading_eligibility_verified":False,
                "asof_crypto_issuer_verified":False,
                "crypto_contract_multiplier_verified":False,
                "actual_execution_price_verified":False,
                "missing_future_source_is_negative":False,
                "included_in_raw_attempt_ledger":True,
            })
    return {
        "window_anchor":window,"raw_symbol_attempts":len(rows),
        "preexisting_raw_attempts":len(start_rows),
        "new_listing_raw_attempts":len(later_rows),
        "raw_population_rows":sorted(rows,key=lambda x:x["symbol_exact"]),
        "G0":"PARTIAL_UNTIL_INDEPENDENT_PIT_PROOF",
        "G1":"NOT_SCORABLE_WITHOUT_THREE_REAL_FORWARD_WINDOWS_AND_ASOF_CRYPTO",
        "execution":"UNKNOWN",
        "model_deployment":"NO_GO",
    }


def audit():
    baseline=decode_source()
    previous=stage129.run()
    previous_rows={(v["date"],v["symbol"]):v for v in previous["all_source_cohort_rows"]}
    detailed,totals=check_historical(baseline,previous_rows)
    later_counts=Counter(v["later_exchange_underlyingType_label_not_asof_issuer"] for v in detailed)
    return {
        "schema":SCHEMA,
        "source":"ORIGINAL_STAGE130_GIT_31_PUBLIC_PUBLISHER_SHA_HISTORICAL",
        "stage130_source_git_blob":SOURCE_BLOB_SHA,
        "stage130_full_original_json_SHA256":SOURCE_RAW_SHA256,
        "stage130_all_original_31_case_count":31,
        "stage130_original_daily_sha_zip_receipts":totals["receipts"],
        "stage130_original_minute_bars":totals["bars"],
        "stage130_distinct_first_momentum_research_triggers":totals["first_momentum_triggers"],
        "stage130_gross_2x_posthoc_from_first_open":totals["posthoc_gross_2x"],
        "stage130_momentum_early5_gross2x_exposed_only":totals["posthoc_gross_2x_early5"],
        "stage130_later_exchange_underlyingType_labels_NOT_ASOF_CRYPTO_PROOF":dict(sorted(later_counts.items())),
        "original_Stage93_fixed_week_2x_events_UNCHANGED":51,
        "original_Stage116_first_forward_capture_20261014_0600":"SOURCE_FAILED_NO_BACKFILL",
        "original_Stage116_three_window_G1_cannot_pass_without_first_window":True,
        "manual_capture_20261028_1111_remains_USER_TRIGGER_ONLY":True,
        "complete_authenticated_live_minute_by_minute_universe":"NOT_OBTAINED",
        "G0":"PARTIAL","G1_new_independent_OOS":"NOT_SCORABLE",
        "G2_G3":"REJECTED_PREVIOUS_CANDIDATES_UNCHANGED",
        "G4_actual_net":"UNKNOWN","external_other_AI_review":"NOT_DONE",
        "Monster_deployment":"NO_GO","Gmail":"OFF","Frank":"UNCHANGED",
        "all_retrospective_31_new_listing_population_rows":detailed,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    z=audit()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(z,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in z.items() if k!="all_retrospective_31_new_listing_population_rows"},ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
