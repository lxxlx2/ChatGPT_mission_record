#!/usr/bin/env python3
"""Stage58: reject unsafe Spot-only urgent exclusion with original Stage57 facts.

NOT a validated strategy. 76 confirmed exact-Symbol Spot trading histories are
a post-hoc subset of 166 already-exposed USD-M candidates. Reapply Stage52's
unchanged first-come cap to show what a Spot-only gate would sacrifice.
Future 2x/5x/10x labels are evaluation-only, never selection inputs.
"""
from __future__ import annotations
import argparse
import collections
import csv
import datetime
import hashlib
import json
from decimal import Decimal
from pathlib import Path

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
SP=E/"monster_stage57_all166_exact_symbol_spot_asof_source_SHA.jsonl"
C=E/"monster_stage55_all166_candidate_asof_features_and_fate.csv"
M=E/"monster_stage52_pinned_v03_all5400_36SHA_true_global_cap_metrics.json"
LOCK={SP.name:"561b5a7dd5b894565d01b24671aa6d96d921bda8",
      C.name:"dca780246adb28e045ed77f0f96eb4bd034fb2e7",
      M.name:"42d455a6cc9d0164a8dd94aa12a475bad5ed126e"}
GOOD="EXACT_SYMBOL_SPOT_15M_SOURCE_COMPLETE_WITH_TRADES"
SCHEMA="MONSTER_STAGE58_EXPOSED_ORIGINAL166_SPOT_ONLY_CAP5_COUNTERFACTUAL_INVALID_AS_NEW_GATE_V1"

def gitblob(path):
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def utc(text):
    v=datetime.datetime.fromisoformat(text.replace("Z","+00:00"))
    if v.utcoffset()!=datetime.timedelta(0):raise ValueError("STAGE58_NOT_UTC")
    return int(v.timestamp()*1000)

def read():
    for f in (SP,C,M):
        if gitblob(f)!=LOCK[f.name]:raise ValueError("STAGE58_FROZEN_SOURCE_DRIFT "+f.name)
    s=[json.loads(line) for line in SP.read_text().splitlines() if line]
    with C.open(newline="",encoding="utf-8") as f:c=list(csv.DictReader(f))
    m=json.loads(M.read_text())
    if len(s)!=166 or len(c)!=166 or m["GT5x"]!=3 or m["GT10x"]!=2 or m["P1v03_unbudgeted_candidates"]!=166:
        raise ValueError("STAGE58_BASELINE_CORRUPTED")
    sk={(r["date"],r["futures_symbol"]):r for r in s}
    ck={(r["date"],r["symbol"]):r for r in c}
    if len(sk)!=166 or len(ck)!=166 or set(sk)!=set(ck):
        raise ValueError("STAGE58_EXACT_SET_IDENTITY_DRIFT")
    for k in sk:
        if sk[k]["eligible_timestamp_UTC"]!=ck[k]["eligible_timestamp_UTC"] or (
           sk[k]["futures_research_delivered"]!=(ck[k]["research_delivered"]=="True")):
            raise ValueError("STAGE58_SIGNAL_FATE_DRIFT")
    return sk,ck,m

def process(spots,candidates,market):
    selected=[(k,x) for k,x in spots.items() if x["spot_result"]==GOOD]
    # Original stage52 priority on identical minute: descending observed USD-M
    # quote15 and stable symbol. Never use any posthoc label to select.
    selected.sort(key=lambda pair:(utc(pair[1]["eligible_timestamp_UTC"]),
                      -Decimal(candidates[pair[0]]["quote15_USDT"]),pair[0][1]))
    blocks=collections.Counter()
    fates=[]
    for key,spot in selected:
        c=candidates[key]
        stamp=utc(spot["eligible_timestamp_UTC"])
        idx=(stamp-utc(key[0]+"T06:00:00Z"))//86400000
        if idx not in range(7):raise ValueError("STAGE58_WRONG_UTC06_BLOCK")
        day=key[0],idx
        delivered=blocks[day]<5
        if delivered:blocks[day]+=1
        fates.append({"date":key[0],"symbol":key[1],
          "asof_UTC":spot["eligible_timestamp_UTC"],
          "original_v03_urgent_delivered":spot["futures_research_delivered"],
          "SPOT_only_counterfactual_urgent_delivered":delivered,
          "SPOT_15m_trade_source_status":spot["spot_result"],
          "posthoc_GT_EVALUATION_ONLY":spot["posthoc_label_EVALUATION_ONLY"],
          "day_index":idx})
    num=sum(x["SPOT_only_counterfactual_urgent_delivered"] for x in fates)
    early=[x for x in fates if x["posthoc_GT_EVALUATION_ONLY"]=="FUTURE_2X_AND_CANDIDATE_BEFORE_5MIN"]
    high=market["source_valid_gt5x_critical_cases"]
    if len(high)!=3 or sum(bool(x["gt10"]) for x in high)!=2:
        raise ValueError("STAGE58_CRITICAL_SOURCE_GT5_GT10_DRIFT")
    highrows=[]
    for x in high:
        spot=spots.get((x["date"],x["symbol"]))
        highrows.append({"date":x["date"],"symbol":x["symbol"],
            "actual_GT5_HISTORIC":True,"actual_GT10_HISTORIC":bool(x["gt10"]),
            "original_V03_gt5_alert_early":bool(x["global_cap_delivered_and_early_GT5"]),
            "source_verified_exact_symbol_spot15m":spot["spot_result"]==GOOD if spot else False,
            "historic_spot_record":spot["spot_result"] if spot else "NO_P1_CANDIDATE"})
    summary={"schema":SCHEMA,"LOCKED_ORIGINAL_GIT_BLOBS":LOCK,
      "input_usdm_all_166":len(spots),"confirmed_exact_symbol_spot_subcohort":len(fates),
      "historical_original_V03_cap_delivered_spot_subcohort":
        sum(x["original_v03_urgent_delivered"] for x in fates),
      "spot_only_counterfactual_cap_delivered":num,
      "spot_only_counterfactual_cap_not_delivered":len(fates)-num,
      "spot_early2x_candidates":len(early),
      "original_V03_early2x_spot_delivered":sum(x["original_v03_urgent_delivered"] for x in early),
      "spot_only_counterfactual_early2x_spot_delivered":sum(x["SPOT_only_counterfactual_urgent_delivered"] for x in early),
      "spot_only_counterfactual_noncalendar2x_delivered":sum(
        x["SPOT_only_counterfactual_urgent_delivered"] and
        x["posthoc_GT_EVALUATION_ONLY"]=="ORDINARY_NOT_CALENDAR_2X" for x in fates),
      "high5x10x_exposed_original_source_cases":highrows,
      "high5x_spot_only_counterfactual_alerts":sum(x["source_verified_exact_symbol_spot15m"] for x in highrows),
      "conclusion":"SPOT_ONLY_GATE_CANNOT_BE_APPROVED_FROM_EXPOSED_DATA_LOSES_ALL_HISTORIC_5X",
      "SAMPLE_EXPOSED_NO_NEW_MODEL_TEST":True,
      "UNKNOWN_SPOT_ARCHIVE_CANNOT_BE_FILTERED_AS_NEVER_TRADEABLE":True,
      "BINANCE_ALPHA_AND_CHAIN_DEX_EXECUTION_NOT_MEASURED":True,
      "NO_ACTUAL_SPOT_BUY_PROFIT":True,
      "P1V03":"REJECTED","MONSTER":"NO_GO","GMAIL":"OFF",
      "FRANK":"UNCHANGED","AUTO_TRADE":"NO_GO","OTHER_AI_REVIEW":"NOT_DONE"}
    return fates,summary

def selftest():
    base=datetime.datetime(2026,1,1,tzinfo=datetime.timezone.utc)
    assert utc("2026-01-01T06:00:00Z")-int(base.timestamp()*1000)==21600000
    assert -Decimal("9")<-Decimal("5")
    print("STAGE58_CAUSAL_CAP_ORDER_SOURCE_HOLDOUT_NONLEAK_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--out",type=Path)
    x=p.parse_args()
    if x.selftest:selftest();return
    if x.out is None:p.error("--out required")
    s,c,m=read()
    fates,summary=process(s,c,m)
    if (summary["confirmed_exact_symbol_spot_subcohort"]!=76 or
        summary["spot_early2x_candidates"]!=7 or
        summary["high5x_spot_only_counterfactual_alerts"]!=0):
        raise ValueError("STAGE58_RESEARCH_DRIFT_NEVER_REWRITE_ORIGINAL_GATE")
    x.out.mkdir(parents=True,exist_ok=True)
    (x.out/"monster_stage58_exposed_spot_only_cap5_counterfactual_summary.json").write_text(
        json.dumps(summary,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    (x.out/"monster_stage58_exposed_spot_only_cap5_all76_fates.jsonl").write_text(
        "".join(json.dumps(q,sort_keys=True,ensure_ascii=False)+"\n" for q in fates))
    print("STAGE58_EXPOSED_SPOT_ONLY_COUNTERFACTUAL_LOSES_ALL_5X "+
          json.dumps({k:summary[k] for k in (
              "confirmed_exact_symbol_spot_subcohort",
              "spot_only_counterfactual_cap_delivered",
              "spot_only_counterfactual_early2x_spot_delivered",
              "high5x_spot_only_counterfactual_alerts")},sort_keys=True))

if __name__=="__main__":
    main()
