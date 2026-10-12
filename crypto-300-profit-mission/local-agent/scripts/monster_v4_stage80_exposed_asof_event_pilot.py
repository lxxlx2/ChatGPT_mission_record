#!/usr/bin/env python3
"""Whole-cohort exploratory event-only pilot, NOT 3m continuous replay or OOS."""
from __future__ import annotations

import argparse
import collections
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
try:
    from monster_v4_stage80_dual_entry_core import (Features, evaluate, load_contract, sha_blob,
        decimal, utc_ms)
except ImportError:
    from scripts.monster_v4_stage80_dual_entry_core import (Features, evaluate, load_contract, sha_blob,
        decimal, utc_ms)

EVIDENCE = Path(__file__).resolve().parents[2] / "monster" / "evidence"
RAW48 = "monster_stage48_full936_real_closed1m_original_D0_event_features.jsonl"
RAW64 = "monster_stage64_all519_D0_asof61m_official_1m_taker_trades_SHA.jsonl"
PINS = {RAW48:"642b7b1fb0603b122f97f458e7396b35969a9b6c",
        RAW64:"8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a"}
SCHEMA = "MONSTER_STAGE80_EXPOSED_EVENT_TIMES_ONLY_TWO_SOURCE_COHORT_PILOT_V1"


def rows(name: str, folder: Path):
    raw=(folder/name).read_bytes()
    if sha_blob(raw)!=PINS[name]:
        raise ValueError("STAGE80_RAW_SOURCE_BLOB_MISMATCH:"+name)
    data=[json.loads(s) for s in raw.decode("utf-8").splitlines() if s.strip()]
    if len(data)!= (936 if name==RAW48 else 519):
        raise ValueError("STAGE80_ORIGINAL_RAW_COHORT_COUNT_CHANGED")
    return data


def bucket(date: str, at: str) -> tuple[str, int]:
    start = utc_ms(date + "T06:00:00Z")
    delta = utc_ms(at) - start
    if delta < 0 or delta >= 7*24*3_600_000:
        raise ValueError("STAGE80_ORIGINAL_UTC06_WINDOW_DRIFT")
    return date, delta//(24*3_600_000)


def features48(row):
    return Features(decimal(row["ret60_pct"]),decimal(row["quote15_USDT"]),
                    int(row["trades15"]),
                    decimal(row["normalized_quote15_vs_prior45"]) if row["normalized_quote15_vs_prior45"] is not None else None,
                    decimal(row["last_closed_close"]))


def features64(row):
    f=row["features_ASOF_ONLY"]
    return Features(decimal(f["ret60_pct"]),decimal(f["quote15_USDT"]),
                    int(f["trade_count15"]),
                    decimal(f["quote15_normalized_prev45"]) if f["quote15_normalized_prev45"] is not None else None,
                    None)


def stage48(data,contract):
    group=collections.defaultdict(list)
    for row in data:
        if not row["actual_1m_official_source_closes_before_D0_utc"]:
            raise ValueError("STAGE80_STAGE48_CAUSAL_SOURCE_FALSE")
        group[(row["date"],row["symbol"])].append(row)
    if len(group)!=437:raise ValueError("STAGE80_STAGE48_COIN_DATE_COUNT_NOT_437")
    upgraded=[]
    event_count=0
    events_by_label=collections.Counter()
    for (date,symbol),events in sorted(group.items()):
        events.sort(key=lambda row:row["asof_D0_WATCH_UTC"])
        if events[0]["watch_ordinal"]!=1 or events[0]["is_repeated_original_watch"]:
            raise ValueError("STAGE80_FIRST_D0_IDENTITY_DRIFT")
        flags={x["historical_2x_from_window_anchor"] for x in events}
        if len(flags)!=1:raise ValueError("STAGE80_GT_LABEL_INCONSISTENT")
        state=None
        for index,row in enumerate(events):
            event_count+=1
            if row["watch_ordinal"]!=index+1 or row["is_repeated_original_watch"]!=(index>0):
                raise ValueError("STAGE80_WATCH_ORDER_OR_DUPLICATE")
            f=features48(row)
            state,verdict=evaluate(state,venue="USDM",symbol=symbol,at_utc=row["asof_D0_WATCH_UTC"],
                                   features=f,is_first_d0=index==0,contract=contract,
                                   relative_first_pct=decimal(row["ret_from_first_WATCH_last_close_pct"]))
            events_by_label[(verdict,"gt2" if flags.pop() else "non2")] += 1
            flags={x["historical_2x_from_window_anchor"] for x in events}
            if verdict in ("DIRECT_AT_FIRST_D0","REIGNITION_AFTER_D0"):
                upgraded.append({"date":date,"symbol":symbol,"at":row["asof_D0_WATCH_UTC"],
                                 "path":verdict,"gt2_label":row["historical_2x_from_window_anchor"],
                                 "before_2x":row["label_only_strictly_before_first_2x_utc"],
                                 "gt5_label":row["historical_gt5x"],
                                 "gt10_label":row["historical_gt10x"]})
    if event_count!=936:raise ValueError("STAGE80_WATCH_COUNT_DRIFT")
    per_day=collections.Counter(bucket(x["date"],x["at"]) for x in upgraded)
    return {
      "attempted_event_rows":event_count,"unique_watch_coin_dates":len(group),
      "distinct_upgraded":len(upgraded),
      "direct":sum(x["path"]=="DIRECT_AT_FIRST_D0" for x in upgraded),
      "reignition_observed_repeated_watch_only":sum(x["path"]=="REIGNITION_AFTER_D0" for x in upgraded),
      "upgraded_future_calendar2x":sum(x["gt2_label"] for x in upgraded),
      "upgraded_before_calendar2x_first_cross_strict_only":sum(x["gt2_label"] and x["before_2x"] for x in upgraded),
      "upgraded_calendar_non2x":sum(not x["gt2_label"] for x in upgraded),
      "mean_candidates_per_UTC06_day":round(len(upgraded)/42,4),
      "peak_candidates_per_UTC06_day":max(per_day.values(),default=0),
      "per_date":{"%s"%d:sum(x["date"]==d for x in upgraded) for d in sorted({k[0] for k in group})},
      "note":"These are only original D0 events, NOT every intervening 3m after first WATCH. NOT complete D1 strategy, not oos, no 5m capture claim."
    }


def stage64(data,contract):
    keys=set()
    selected=[]
    for row in data:
        key=(row["date"],row["symbol"])
        if key in keys:raise ValueError("STAGE80_STAGE64_DUPLICATE_FIRST")
        keys.add(key)
        if row["source_status"]!="COMPLETE_OFFICIAL_DAILY_USDM_61M_PUBLISHER_SHA_NO_FUTURE" or row["HOLDOUT"]:
            raise ValueError("STAGE80_STAGE64_SOURCE_OR_EXPOSURE_INCONSISTENT")
        state,verdict=evaluate(None,venue="USDM",symbol=row["symbol"],at_utc=row["first_D0_UTC"],
                               features=features64(row),is_first_d0=True,contract=contract)
        if verdict == "DIRECT_AT_FIRST_D0":
            selected.append({"date":row["date"],"symbol":row["symbol"],"at":row["first_D0_UTC"],
                             "gt2_label":row["original_7day_calendar_2x_EVALUATION_ONLY"]})
    if len(keys)!=519:raise ValueError("STAGE80_STAGE64_NOT_519")
    day=collections.Counter(bucket(x["date"],x["at"]) for x in selected)
    return {
        "all_original_first_d0":len(keys),"direct_d1":len(selected),
        "source_original_2x_count":sum(x["original_7day_calendar_2x_EVALUATION_ONLY"] for x in data),
        "direct_historic_calendar2x":sum(x["gt2_label"] for x in selected),
        "direct_historic_non2x":sum(not x["gt2_label"] for x in selected),
        "mean_candidates_per_UTC06_day":round(len(selected)/42,4),
        "peak_candidates_per_UTC06_day":max(day.values(),default=0),
        "per_date":{d:sum(x["date"]==d for x in selected) for d in sorted({x["date"] for x in data})},
        "note":"First WATCH only. Other 3m continuous evaluations NOT present; label is calendar-anchored future 2x, not attainable returns."
    }


def selftest():
    c=load_contract()
    sample={"date":"2025-01-30","symbol":"TESTUSDT","first_D0_UTC":"2025-01-30T06:00:00Z",
            "features_ASOF_ONLY":{"ret60_pct":"8","quote15_USDT":"1000000",
               "quote15_normalized_prev45":"1.3","trade_count15":10000}}
    f=features64(sample)
    assert evaluate(None,venue="USDM",symbol="TESTUSDT",at_utc=sample["first_D0_UTC"],
                    features=f,is_first_d0=True,contract=c)[1]=="DIRECT_AT_FIRST_D0"
    another=dict(sample,features_ASOF_ONLY=dict(sample["features_ASOF_ONLY"],ret60_pct="7.99999"))
    assert evaluate(None,venue="USDM",symbol="TESTUSDT",at_utc=another["first_D0_UTC"],
                    features=features64(another),is_first_d0=True,contract=c)[1]=="WATCH_RETAINED"
    assert bucket("2025-01-30","2025-01-30T06:00:00Z")==("2025-01-30",0)
    print("STAGE80_EXPOSED_PILOT_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--evidence",type=Path,default=EVIDENCE)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    c=load_contract()
    s48=stage48(rows(RAW48,a.evidence),c)
    s64=stage64(rows(RAW64,a.evidence),c)
    result={"schema":SCHEMA,"input_source_git_blobs":PINS,"frozen_contract_git_blob":"292e0cefe2089214dbde48ee50d6baf6cf590f8e",
            "stage48":s48,"stage64":s64,"full_3m_continuous_replay":"NOT_DONE",
            "forward_oos":"NOT_DONE","execution_net_pnl":"UNKNOWN",
            "no_production_side_effects":True,"monster_deployment":"NO_GO",
            "gmail":"OFF","autotrade":"NO_GO","frank":"UNCHANGED"}
    raw=json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(raw,encoding="utf-8")
    print(raw)


if __name__=="__main__":
    main()
