#!/usr/bin/env python3
"""Stage73 real Binance source: remove only future days after known first D0.

Same immutable original V4 D0 core, verify all *past* WATCH exact UTC events
are still present despite incomplete forward source and unscoreable full week.
Already exposed known histories; regression only, NEVER model validation.
"""
from __future__ import annotations
import argparse
import json
from datetime import date
from pathlib import Path

try:
    import monster_v4_stage73_m03_all2700_verified_prefix_discovery as s
except ImportError:
    from scripts import monster_v4_stage73_m03_all2700_verified_prefix_discovery as s

CASES=(
    ("2025-06-30","HFTUSDT","2025-07-02"),
    ("2025-06-30","HUSDT","2025-07-03"),
    ("2025-11-27","PIPPINUSDT","2025-11-29"),
)
SCHEMA="MONSTER_STAGE73_REAL_OFFICIAL_SHA_FUTURE_DAY_WITHHELD_PREFIX_CAUSALITY_TEST_V1"


def evaluate_case(cohort,symbol,missing_day,sources,old):
    lookup=(cohort,symbol)
    frozen=old[lookup]
    if frozen["minute_source_status"]!=s.GOOD or not frozen["original_D0_first_UTC"]:
        raise ValueError("STAGE73_TEST_REQUIRES_REAL_ORIGINAL_FIRST_WATCH")
    if date.fromisoformat(missing_day)<=date.fromisoformat(cohort):
        raise ValueError("STAGE73_TEST_TRUNCATION_IS_NOT_FUTURE")
    def bounded_reader(name,dt):
        if dt.isoformat()>=missing_day:
            raise FileNotFoundError("STAGE73_SYNTHETIC_FUTURE_DAY_WITHHELD_"+missing_day)
        return s.original.verified_1m_day(name,dt)
    bars,proof,cut=s.sequential_source(symbol,cohort,reader=bounded_reader)
    if not cut or cut["date"]!=missing_day or len(proof)<2:
        raise ValueError("STAGE73_FUTURE_SOURCE_WITHHOLD_FAILED")
    result=s.scan_verified_prefix(symbol,cohort,bars)
    if not result["polls"]:
        raise ValueError("STAGE73_LOST_EXISTING_FIRST_WATCH_WARMUP")
    last_i=s.original.WARMUP+2+3*(result["polls"]-1)
    last_tick_ms=bars[last_i][0]+s.ONE
    old_prefix=[t for t in frozen["original_D0_all_WATCH_UTC"]
                if s.original.msutc(t)<=last_tick_ms]
    if not old_prefix or result["WATCH_UTC"]!=old_prefix:
        raise ValueError("STAGE73_REAL_PUBLISHER_SHA_FUTURE_SOURCE_REMOVAL_ERASED_OLD_WATCH "+
                         json.dumps({"expected":old_prefix,"actual":result["WATCH_UTC"]}))
    if s.original.msutc(result["WATCH_UTC"][0])>=s.original.msutc(missing_day+"T00:00:00Z"):
        raise ValueError("STAGE73_FIRST_WATCH_NOT_BEFORE_GAP")
    return {
        "date":cohort,"symbol":symbol,
        "real_original_first_watch_UTC":frozen["original_D0_first_UTC"],
        "first_watch_survives_future_day_source_404":result["WATCH_UTC"][0],
        "all_source_observable_watch_events_strict_parity":True,
        "observable_prefix_v4_poll_count":result["polls"],
        "verified_original_Binance_USDM_daily_1m_publisher_SHAs":proof,
        "first_missing_day_INJECTED_TEST_ONLY":missing_day,
        "true_real_source_not_claimed_missing":True,
        "no_future_GT_score_because_test_future_day_removed":True,
        "no_user_trading_or_live_alert":True,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    sources,old=s.originals()
    if len(sources)!=2700:raise ValueError("STAGE73_WRONG_SOURCE_LOCK")
    results=[evaluate_case(*r,sources,old) for r in CASES]
    if len(results)!=3 or any(not x["all_source_observable_watch_events_strict_parity"] for x in results):
        raise ValueError("STAGE73_FUTURE_GAP_PARITY_TEST_INCOMPLETE")
    value={"schema":SCHEMA,
           "exposed_real_winners_tested_not_new_historical_holdout":3,
           "all_real_publisher_SHA_and_prefix_watch_identities_equal_to_stage66":True,
           "three_real_prefix_future_source_gaps":results,
           "M03_SOURCE_GAP_NOW_DOES_NOT_ERASE_REAL_PAST_WATCH_EVENTS":True,
           "LIVE_TRADABLE_MARKET_AND_NEW_NET_PNL_STILL_UNKNOWN":True,
           "STAGE73_M03_FULL2700_AND_INDEPENDENT_REVIEW":"SEPARATE_GATES",
           "DEPLOYMENT":"NO_GO"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("STAGE73_THREE_REAL_OFFICIAL_SOURCE_FUTURE_DAY_WITHHELD_FIRST_WATCH_SURVIVES "+
          json.dumps([{k:x[k] for k in ("symbol","first_watch_survives_future_day_source_404",
                                         "observable_prefix_v4_poll_count")} for x in results],sort_keys=True))


if __name__=="__main__":
    main()
