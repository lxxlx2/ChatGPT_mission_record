#!/usr/bin/env python3
"""Monster Stage69: unchanged Stage68 P2 on older six already-exposed 5400.

No new selection/threshold. Audit original 127/166 budget reference exactly,
519 real as-of D0 quote sources, all 29 2x incl 3 5x and 2 10x.
Not independent performance evidence, not actual realizable profit.
"""
from __future__ import annotations
import argparse,csv,collections,hashlib,json
from decimal import Decimal as D
from pathlib import Path
try:import monster_v4_stage68_exposed2700_dual_lane_watch_p1_halfday_reserve as core
except ImportError:from scripts import monster_v4_stage68_exposed2700_dual_lane_watch_p1_halfday_reserve as core

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
T=E/"monster_stage52_all5400_originalV4_P1v03_true_minute_source_cases.jsonl"
OLD=E/"monster_stage55_all166_candidate_asof_features_and_fate.csv"
D0=E/"monster_stage64_all519_D0_asof61m_official_1m_taker_trades_SHA.jsonl"
SUM=E/"monster_stage52_pinned_v03_all5400_36SHA_true_global_cap_metrics.json"
P=E.parent/"MONSTER_STAGE69_P2_FROZEN_OLDER6_FULL5400_ROBUSTNESS_CONTRACT_20261012.md"
BLOBS={
 T.name:"ad7544f97e8a0d6c1f2635aa54052cca42d08cf1",
 OLD.name:"dca780246adb28e045ed77f0f96eb4bd034fb2e7",
 D0.name:"8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a",
 SUM.name:"42d455a6cc9d0164a8dd94aa12a475bad5ed126e",
 P.name:"06f56e47543c50ae4c66b65fc0b7895e0a92f564",
 "monster_v4_stage68_exposed2700_dual_lane_watch_p1_halfday_reserve.py":"f933e8315e4fe94d632ab8118cf1a2a4ff66a892",
}
VALID="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
DATES=("2025-01-30","2025-06-02","2025-08-01","2025-10-02","2026-06-21","2026-07-28")
FIELDS={2:"first_true_2x_HIGH_minute_UTC",5:"first_real_1m_HIGH_gt5x_UTC",10:"first_real_1m_HIGH_gt10x_UTC"}

def blob(f):
    a=f.read_bytes()
    return hashlib.sha1(b"blob "+str(len(a)).encode()+b"\0"+a).hexdigest()

def load():
    for p in (T,OLD,D0,SUM,P,Path(core.__file__)):
        if blob(p)!=BLOBS[p.name]:raise ValueError("STAGE69_ORIGINAL_SHA_CHANGED "+p.name)
    t=[json.loads(x) for x in T.read_text(encoding="utf-8").splitlines() if x]
    w=[json.loads(x) for x in D0.read_text(encoding="utf-8").splitlines() if x]
    with OLD.open(encoding="utf-8",newline="") as f:old=list(csv.DictReader(f))
    metric=json.loads(SUM.read_text(encoding="utf-8"))
    if (len(t),len(w),len(old))!=(5400,519,166):raise ValueError("STAGE69_MISSING_ANY_ORIGINAL")
    valid=[x for x in t if x["source_status"]==VALID]
    if (len(valid),sum(bool(x["WATCH_UTC"]) for x in valid),
        sum(bool(x["p1v03_eligible_unbudgeted"]) for x in valid),
        sum(x["hourly_gt2x"] for x in valid),
        sum(x["hourly_gt5x"] for x in valid),
        sum(x["hourly_gt10x"] for x in valid))!=(3377,519,166,29,3,2):
        raise ValueError("STAGE69_SOURCE_GT_AND_ORIGINAL_ASOF_TOTALS_CHANGED")
    if metric["P1v03_budget_delivered"]!=127 or metric["P1v03_budgeted_early_ge5min_GT2x_from_D0_pre5"]!=21:
        raise ValueError("STAGE69_ORIGINAL_FROZEN_STAGE52_RESULT_CHANGED")
    for date in DATES:
        if sum(x["date"]==date for x in t)!=900:raise ValueError("STAGE69_MISSING_DATE900")
    seen=lambda a:len({(x["date"],x["symbol"]) for x in a})==len(a)
    if not all(seen(a) for a in (t,w,old)):raise ValueError("STAGE69_DUPLICATE_COHORT")
    return t,valid,{(x["date"],x["symbol"]):x for x in w},old

def build(t,valid,watches,old):
    events=[]
    for r in valid:
        key=r["date"],r["symbol"]
        d0=r["WATCH_UTC"][0] if r["WATCH_UTC"] else None
        p1=r["p1v03_eligible_unbudgeted"]
        if p1 and not d0:raise ValueError("STAGE69_P1_WITHOUT_WATCH")
        if d0:
            src=watches[key]
            if src["first_D0_UTC"]!=d0 or src["source_status"]!="COMPLETE_OFFICIAL_DAILY_USDM_61M_PUBLISHER_SHA_NO_FUTURE":
                raise ValueError("STAGE69_D0_FIRST_MINUTE_QUOTE_IS_NOT_VERIFIED")
            events.append({"date":r["date"],"symbol":r["symbol"],"kind":"FIRST_D0_WATCH",
                           "at_UTC":d0,"asof_quote15":src["features_ASOF_ONLY"]["quote15_USDT"]})
        if p1:
            if (p1["first_D0_watch_UTC"]!=d0 or
                not p1["publisher_verified_asof_no_future_source"] or
                core.stamp(p1["at_UTC"])<core.stamp(d0)):
                raise ValueError("STAGE69_ASOF_P1_AND_D0_IDENTITY_FAIL")
            events.append({"date":r["date"],"symbol":r["symbol"],"kind":"P1_FIRST_ASOF_ELIGIBLE",
                           "at_UTC":p1["at_UTC"],"asof_quote15":p1["features"]["quote15_USDT"]})
    if len(events)!=685:raise ValueError("STAGE69_MISSING_WATCH_OR_P1_EVENTS")
    # Independent reference without Stage68's 2+3 pacing.
    p1s=sorted([e for e in events if e["kind"]=="P1_FIRST_ASOF_ELIGIBLE"],
               key=lambda e:(core.stamp(e["at_UTC"]),-D(e["asof_quote15"]),e["symbol"]))
    cap=collections.Counter();ref={}
    for e in p1s:
        key=e["date"],core.relative_day(e["date"],e["at_UTC"])[0]
        admitted=cap[key]<5
        cap[key]+=int(admitted)
        ref[e["date"],e["symbol"]]=admitted
    gold={(x["date"],x["symbol"]):x for x in old}
    if set(gold)!=set(ref) or sum(ref.values())!=127:
        raise ValueError("STAGE69_ORIGINAL_127_BUDGET_NOT_REPRODUCED")
    for key,v in ref.items():
        if v!=(gold[key]["research_delivered"]=="True"):raise ValueError("STAGE69_ORIGINAL_127_FATE_CHANGED "+str(key))
    return events,ref

def score(valid,ref,new):
    found={n:[] for n in (2,5,10)}
    for row in valid:
        key=row["date"],row["symbol"]
        for multiple in (2,5,10):
            if not row["hourly_gt"+str(multiple)+"x"]:continue
            high=row[FIELDS[multiple]]
            d0=row["WATCH_UTC"][0] if row["WATCH_UTC"] else None
            p1=row["p1v03_eligible_unbudgeted"]
            if not high:raise ValueError("STAGE69_GT_EVENT_MISSING_REAL_FIRST_MINUTE_HIGH")
            de=bool(d0 and core.stamp(d0)+5<=core.stamp(high))
            pe=bool(p1 and core.stamp(p1["at_UTC"])+5<=core.stamp(high))
            old=ref.get(key,False);p2=new.get(key,{}).get("urgent",False)
            found[multiple].append({
                "date":row["date"],"symbol":row["symbol"],
                "GT":str(multiple)+"x","first_real_1m_HIGH_UTC_NOT_FILL":high,
                "first_D0_WATCH_UTC":d0,
                "P1_eligible_UTC":p1["at_UTC"] if p1 else None,
                "D0_5min_early":de,"P1_5min_early":pe,
                "old_P1_urgent":old,"P2_urgent":p2,
                "old_budget_and_D0_5min_early":bool(old and de),
                "P2_budget_and_D0_5min_early":bool(p2 and de),
                "old_budget_and_P1_5min_early":bool(old and pe),
                "P2_budget_and_P1_5min_early":bool(p2 and pe),
            })
    if [len(found[k]) for k in (2,5,10)]!=[29,3,2]:
        raise ValueError("STAGE69_GT_SOURCE_COUNTS_DRIFT")
    def stats(rows):
        return {"n":len(rows),**{key:sum(bool(x[key]) for x in rows)
            for key in ("D0_5min_early","P1_5min_early",
                "old_budget_and_D0_5min_early","P2_budget_and_D0_5min_early",
                "old_budget_and_P1_5min_early","P2_budget_and_P1_5min_early")}}
    if (stats(found[2])["D0_5min_early"]!=28 or
        stats(found[2])["old_budget_and_D0_5min_early"]!=22 or
        stats(found[2])["old_budget_and_P1_5min_early"]!=21):
        raise ValueError("STAGE69_ORIGINAL28_EARLY_21_URGENT_FROZEN_REFERENCE_DRIFT")
    return {str(k)+"x":stats(v) for k,v in found.items()},[x for v in found.values() for x in v]

def main():
    a=argparse.ArgumentParser();a.add_argument("--selftest",action="store_true")
    a.add_argument("--out",type=Path);o=a.parse_args()
    if o.selftest:
        core.test()
        print("STAGE69_UNCHANGED_STAGE68_P2_CORE_CAUSAL_TEST_PASS")
        return
    if not o.out:a.error("--out required")
    original,valid,watch,old=load()
    events,ref=build(original,valid,watch,old)
    ledger,state,caps,firsthalf=core.simulate(events)
    if len(ledger)!=685 or len(state)!=519 or max(caps.values())>5 or max(firsthalf.values())>2:
        raise ValueError("STAGE69_P2_FIRST_WATCH_LOSS_OR_CAP_FAIL")
    scores,case_fates=score(valid,ref,state)
    byday=[]
    for date in DATES:
        subset=[x for x in case_fates if x["date"]==date and x["GT"]=="2x"]
        byday.append({"date":date,"source_valid":sum(x["date"]==date for x in valid),
            "WATCH":sum(x["date"]==date and x["kind"]=="FIRST_D0_WATCH" for x in events),
            "P1":sum(x["date"]==date and x["kind"]=="P1_FIRST_ASOF_ELIGIBLE" for x in events),
            "prior_budget":sum(v for (d,s),v in ref.items() if d==date),
            "P2_budget":sum(v for (d,k),v in caps.items() if d==date),
            "gt2":len(subset),
            "P2_budget_D0_early":sum(x["P2_budget_and_D0_5min_early"] for x in subset),
            "P2_budget_P1_early":sum(x["P2_budget_and_P1_5min_early"] for x in subset),
            "old_budget_D0_early":sum(x["old_budget_and_D0_5min_early"] for x in subset),
            "old_budget_P1_early":sum(x["old_budget_and_P1_5min_early"] for x in subset)})
    p2_early=scores["2x"]["P2_budget_and_P1_5min_early"]
    gates={">=20_source_valid_2x":True,
           ">=80pct_of_original28_actual_P1_5min_early_gt2x_after_budget":p2_early*100>=80*28,
           "all_original_gt5x_budget_P1early":scores["5x"]["P2_budget_and_P1_5min_early"]==3,
           "all_original_gt10x_budget_P1early":scores["10x"]["P2_budget_and_P1_5min_early"]==2}
    result={"schema":"MONSTER_STAGE69_ORIGINAL6_5400_FROZEN_P2_EXPOSED_ROBUSTNESS_V1",
        "source_SHA_blobs":BLOBS,"all_original_USDM_archive_attempts":5400,
        "source_valid_1h_1m":3377,"raw_D0_WATCH":519,"original_P1_candidates":166,
        "original_P1_urgent_exact_reproduced":sum(ref.values()),
        "P2_urgent":sum(caps.values()),"P2_halfday_max":max(firsthalf.values()),
        "P2_daily_max":max(caps.values()),"GT_stats":scores,
        "per_date":byday,"gates":gates,
        "verdict":"EXPOSED_ONLY_NOT_A_DEPLOYABLE_MODEL" if all(gates.values()) else "EXPOSED_HISTORICAL_GATES_REJECTED",
        "no_future_in_alerts":True,"real_spot_Alpha_DEX_execution":"UNKNOWN",
        "no_assumed_order_amount":True,"Other_AI_review":"NOT_DONE",
        "P1_v03":"REJECTED","Monster_deploy":"NO_GO","GMAIL":"OFF","AUTOTRADE":"NO_GO"}
    o.out.mkdir(parents=True,exist_ok=True)
    (o.out/"monster_stage69_older6_all685_WATCH_P1_replayed_budget_events.jsonl").write_text(
        "".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in ledger),encoding="utf-8")
    (o.out/"monster_stage69_older6_all29GT2_3GT5_2GT10_individual_fates.jsonl").write_text(
        "".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in case_fates),encoding="utf-8")
    (o.out/"monster_stage69_older6_full5400_exposed_P2_robustness_summary.json").write_text(
        json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STAGE69_EXPOSED_FULL5400_UNCHANGED_P2_VS_REAL_127_URGENT "+
          json.dumps({"old_cap":sum(ref.values()),"P2_cap":sum(caps.values()),
                      "GT":scores,"verdict":result["verdict"]},sort_keys=True))
if __name__=="__main__":
    main()
