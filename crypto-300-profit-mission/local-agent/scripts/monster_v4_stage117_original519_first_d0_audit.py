#!/usr/bin/env python3
"""Offline EXPOSED original519 first D0 fast attention candidate validation.

Reuses EXACT Stage117 pure signal core, Stage79 first gate and Stage64
61 closed minute official as-of features. Never promote historic 2x labels
to decision input, use raw market first D0 only, not full-market denominator.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha1
import json
from pathlib import Path

try:
    import monster_v4_stage117_first_d0_fast_attention_core as core
    import monster_v4_stage80_dual_entry_core as existing
except ImportError:
    from scripts import monster_v4_stage117_first_d0_fast_attention_core as core
    from scripts import monster_v4_stage80_dual_entry_core as existing

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
BASE=E/"monster_stage64_all519_D0_asof61m_official_1m_taker_trades_SHA.jsonl"
SOURCE83=E/"monster_stage83_all519_source_and_D1_result.jsonl"
PIN64="8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a"
PIN83="c76b3a137c8dbe56feed3a79a63adcc0752f5e2e"
SCHEMA="MONSTER_STAGE117_FROZEN_FIRST_D0_ORIGINAL519_EXPOSED_FULL_AUDIT_V1"
DATES=("2025-01-30","2025-06-02","2025-08-01","2025-10-02",
       "2026-06-21","2026-07-28")


def git_blob(raw):
    return sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def load():
    a=BASE.read_bytes()
    b=SOURCE83.read_bytes()
    if git_blob(a)!=PIN64 or git_blob(b)!=PIN83:
        raise ValueError("STAGE117_SOURCE_SHA_DRIFT")
    x=[json.loads(line) for line in a.decode().splitlines() if line]
    y=[json.loads(line) for line in b.decode().splitlines() if line]
    if len(x)!=519 or len(y)!=519:
        raise ValueError("STAGE117_ORIGINAL519_SOURCE_POPULATION_DRIFT")
    k=lambda r:(r["date"],r["symbol"])
    akeys={k(r) for r in x}
    bkeys={k(r) for r in y}
    if len(akeys)!=519 or akeys!=bkeys or {r["date"] for r in x}!=set(DATES):
        raise ValueError("STAGE117_ORIGINAL519_COIN_DATE_IDENTITY_DRIFT")
    return x,{k(r):r for r in y}


def features(r):
    v=r["features_ASOF_ONLY"]
    if not (r["HOLDOUT"] is False and
            r["source_status"]=="COMPLETE_OFFICIAL_DAILY_USDM_61M_PUBLISHER_SHA_NO_FUTURE"
            and v["historical_usdm_executed_trades60"] is True):
        raise ValueError("STAGE117_UNVERIFIED_OR_HOLDOUT_FEATURE_INPUT")
    f=existing.Features(
        ret60_pct=existing.decimal(v["ret60_pct"]),
        quote15_usdt=existing.decimal(v["quote15_USDT"]),
        trade15=v["trade_count15"],
        quote15_relative45=(existing.decimal(v["quote15_normalized_prev45"])
                            if v["quote15_normalized_prev45"] is not None else None),
        closed_price=None,
    )
    f.validate()
    if (len(r["publisher_SHA_receipts"])<1
        or any(not p.get("checksum_verified") or
               len(p.get("official_zip_sha256",""))!=64
               for p in r["publisher_SHA_receipts"])):
        raise ValueError("STAGE117_61M_SOURCE_PUBLISHER_SHA_MISSING")
    return f


def utc_ms(dt):
    return int(datetime.fromisoformat(dt.replace("Z","+00:00")).timestamp()*1000)


def audit():
    rows, labels=load()
    seen_ids=set()
    by_day=Counter()
    by_anchor=Counter()
    result=[]
    count=Counter()
    for r in sorted(rows,key=lambda x:(x["date"],x["symbol"])):
        k=r["date"],r["symbol"]
        old=labels[k]
        if r["first_D0_UTC"]!=old["D0_FIRST_UTC"]:
            raise ValueError("STAGE117_STAGE83_SOURCE_FIRST_D0_DRIFT")
        decision=core.evaluate_first_d0(
            venue="USDM",symbol=r["symbol"],first_d0_utc=r["first_D0_UTC"],
            feature=features(r))
        if decision["event_id"] in seen_ids:
            raise ValueError("STAGE117_EVENT_ID_NOT_GLOBALLY_UNIQUE")
        seen_ids.add(decision["event_id"])
        t=utc_ms(r["first_D0_UTC"])
        anchor=utc_ms(r["date"]+"T06:00:00Z")
        offset=(t-anchor)//86_400_000
        if not 0<=offset<7:
            raise ValueError("STAGE117_FIRST_D0_OUTSIDE_ORIGINAL_SEVEN_DAYS")
        is_fast=decision["model_decision"]=="EARLY_ATTENTION_CANDIDATE"
        early2=bool(old["D0_at_least_5m_before_2x"])
        if early2 and old["true_first_2x_HIGH_UTC_EVALUATION_ONLY"] is None:
            raise ValueError("STAGE117_GT2_EARLY_EVALUATION_TIME_MISSING")
        count["total_first_D0"]+=1
        count["fast"]+=int(is_fast)
        count["original_early5_2x"]+=int(early2)
        count["new_fast_early5_2x"]+=int(is_fast and early2)
        count["original_first_D1"]+=int(old["D1_FIRST_UTC"] is not None)
        day=r["date"]+"|"+str(offset)
        by_day[day]+=int(is_fast)
        by_anchor[r["date"]]+=int(is_fast)
        result.append({
            "date":r["date"],"symbol":r["symbol"],
            "D0_UTC":r["first_D0_UTC"],
            "Stage117_first_d0_decision":decision,
            "future_original_early_2x5m_EVALUATION_ONLY":early2,
            "future_original_2x_cross_EVALUATION_ONLY":
                old["true_first_2x_HIGH_UTC_EVALUATION_ONLY"],
            "original_stage83_first_D1_UTC":old["D1_FIRST_UTC"],
            "exposed_historical_not_OOS":True,
        })
    if (count["total_first_D0"]!=519 or count["original_first_D1"]!=305
        or count["original_early5_2x"]!=28 or len(seen_ids)!=519):
        raise ValueError("STAGE117_ORIGINAL519_305D1_28EARLY_DRIFT")
    all42=[by_day[date+"|"+str(i)] for date in DATES for i in range(7)]
    if len(all42)!=42 or sum(all42)!=count["fast"]:
        raise ValueError("STAGE117_42DAY_EVENTS_DRIFT")
    return {
        "schema":SCHEMA,
        "source_original_stage64_D0_asof_Git_blob":PIN64,
        "source_original_stage83_D1_2x_Git_blob":PIN83,
        "source_original_stage79_first_gate_Git_blob":existing.CONTRACT_SHA,
        "cohort_exposed_not_new_OOS":True,
        "source_market_scope":"BINANCE_USDM_RESEARCH_UNCERTIFIED_CRYPTO",
        "D0_original":count["total_first_D0"],
        "original_first_D1":count["original_first_D1"],
        "Stage117_firstD0_fast_attention":count["fast"],
        "original_D0_early5_2x":count["original_early5_2x"],
        "Stage117_fast_early5_2x":count["new_fast_early5_2x"],
        "historical_G2_28_candidate_recall_percent":(
            str(Decimal(count["new_fast_early5_2x"])*100/
                Decimal(count["original_early5_2x"]))),
        "historical_G2_80_percent_achieved":(
            count["new_fast_early5_2x"]*100>=28*80),
        "historical_attention_42d":{
            "mean_per_day":str(Decimal(count["fast"])/42),
            "peak_per_day":max(all42),
            "passes_existing_G3_load_target":(
                count["fast"]<=5*42 and max(all42)<=12),
            "all_42_bucket_counts":all42,
            "by_original_anchor":dict(by_anchor),
        },
        "no_backward_threshold_fitting":True,
        "no_unseen_data":True,
        "original_d0_retained_for_all_519":True,
        "crypto_asof_identity_gate":"NOT_DONE",
        "real_execution_net":"UNKNOWN",
        "independent_other_AI_review":"NOT_DONE",
        "monster_deployment":"NO_GO",
    },result


def selftest():
    assert git_blob(b"test")=="30d74d258442c7c65512eafab474568dd706c430"
    assert len(DATES)==6
    assert existing.load_contract()["entry_first"]["ret60_pct_gte"]=="8"
    print("STAGE117_HISTORIC_519_ORIGINAL_SOURCE_LOCK_TEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--out",type=Path)
    p.add_argument("--cases",type=Path)
    a=p.parse_args()
    if a.selftest:
        selftest()
        return
    if a.out is None or a.cases is None:
        p.error("--out --cases required")
    summary,rows=audit()
    for dest in (a.out,a.cases):dest.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n")
    a.cases.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows))
    print("STAGE117_FROZEN_FIRST_D0_EXPOSED_ONLY_REAL_519 "+
          json.dumps({k:v for k,v in summary.items() if k!="historical_attention_42d"},sort_keys=True))


if __name__=="__main__":
    main()
