#!/usr/bin/env python3
"""Stage52: independent original36 SHA, V4 early recall and P1v03 GLOBAL cap.

All Binance original 900 archived USD-M symbols x6 frozen research windows.
True publisher 1h + nine official 1m original source SHA each case.
No profitable BUY assertion, no new thresholds, no Gmail/Mac/Frank changes.
Eligible P1v03 generated as-of inside Stage51; global UTC06 24h cap
performed HERE across all original futures symbols (not per local shard).
"""
from __future__ import annotations
import argparse,collections,datetime as dt,hashlib,json,zipfile
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]/"monster"/"evidence"
ORIG=ROOT/"monster_stage50_full5400_blind_source_publisher_hourly_SHA.jsonl"
RULE=ROOT/"monster_stage49_v03_second_ignition_strategy_and_holdout_prereg_20261012.json"
DAYS=("2025-01-30","2025-06-02","2025-08-01","2025-10-02","2026-06-21","2026-07-28")
RUN=38218974455
SCHEMA="MONSTER_STAGE52_FROZEN_P1V03_ORIGINAL36_SHA_NEWDATE_GLOBAL_BUDGET_AND_HUGE_WINNER_GATES_V1"
SRC="MONSTER_STAGE51_NEW_SIX_DATE_ALL5400_ORIGINAL_V4_ASOF_3M_P1V03_REIGNITION_UNBUDGETED_V1"
GOOD="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
ONE_DAY=86400000
D=Decimal

def sha(b):return hashlib.sha256(b).hexdigest()
def clock(x):return int(dt.datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)
def locked():
    p=json.loads(RULE.read_text())
    if p["schema"]!="MONSTER_STAGE49_V03_SECOND_IGNITION_PRIOR_TO_NEW_USDM_MARKET_PRICE_PREREG_V1" or tuple(p["dates"])!=DAYS:
        raise ValueError("STAGE52_ORIGINAL_FROZEN_DATE_RULE_CHANGED")
    rows=[json.loads(x) for x in ORIG.read_text().splitlines() if x]
    if len(rows)!=5400:raise ValueError("STAGE52_FROZEN_SOURCE5400_MISSING")
    return {(r["date"],r["symbol"]):r for r in rows}

def read(manifest,zips):
    if manifest.get("source_run_id")!=RUN or len(manifest.get("artifacts",[]))!=36:
        raise ValueError("STAGE52_NOT_PINNED_ORIGINAL36_REAL_CI")
    expected=locked();out=[];receipts=[];ids=set()
    for a in manifest["artifacts"]:
        day=a["date"];shard=int(a["shard"]);id=int(a["artifact_id"])
        if day not in DAYS or shard not in range(6) or (day,shard) in ids:
            raise ValueError("STAGE52_ORIGINAL_SHARD_NOT_FROZEN")
        ids.add((day,shard))
        p=Path(zips)/(str(id)+".zip")
        raw=p.read_bytes()
        if sha(raw)!=a["zip_sha256"]:raise ValueError("STAGE52_ORIGINAL_GITHUB_ZIP_SHA_MISMATCH")
        member=f"monster_stage51_{day}_shard{shard}.json"
        with zipfile.ZipFile(p) as z:
            if z.namelist()!=[member]:raise ValueError("STAGE52_NOT_ORIGINAL_JSON")
            content=z.read(member)
        j=json.loads(content)
        if (j.get("schema")!=SRC or j["date"]!=day or j["shard"]!=shard
            or len(j["rows"])!=150 or j["original_symbol_count"]!=150):
            raise ValueError("STAGE52_STAGE51_ORIGINAL_SOURCE_SHARD_INCOMPLETE")
        for r in j["rows"]:
            old=expected.get((r["date"],r["symbol"]))
            if old is None or old["source_status"]!=r["hourly_status"]:
                raise ValueError("STAGE52_STAGE50_HOURLY_SOURCE_IDENTITY_DRIFT")
            if old["source_status"]=="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA":
                if [r["hourly_gt2x"],r["hourly_gt5x"],r["hourly_gt10x"]]!=[old["gt2x"],old["gt5x"],old["gt10x"]]:
                    raise ValueError("STAGE52_FROZEN_GROSS_GT_WRONG")
            if r["source_status"]==GOOD:
                if r["polls"]!=3360 or not r["original_V4_unchanged"] or len(r["source_daily_minute_official_SHA"])!=9:
                    raise ValueError("STAGE52_ORIGINAL_V4_OR_NINE_PUBLISHER_SHA_BAD")
                if [x["publisher_ZIP_sha256"] for x in old["source_proofs"]] != [x["publisher_ZIP_sha256"] for x in r["source_hourly_official_SHA"]]:
                    raise ValueError("STAGE52_ORIGINAL_HOURLY_PUBLISHER_SHA_CHANGED")
                if not all(x["verified_official_publisher_SHA256"] and len(x["zip_sha256"])==64 for x in r["source_daily_minute_official_SHA"]):
                    raise ValueError("STAGE52_MISSING_TRUE_DAILY_MINUTE_SHA")
                cand=r["p1v03_eligible_unbudgeted"]
                if cand is not None:
                    if not r["WATCH_UTC"] or not cand["publisher_verified_asof_no_future_source"]:
                        raise ValueError("STAGE52_P1V03_WITHOUT_VERIFIED_FIRST_D0")
                    t=clock(cand["at_UTC"]);start=clock(day+"T06:00:00Z")
                    if t<clock(r["WATCH_UTC"][0]) or t>=start+7*ONE_DAY or (t-start)%180000:
                        raise ValueError("STAGE52_CANDIDATE_HISTORICALLY_INVALID")
                    f=cand["features"]
                    ratio=D(f["quote15_normalized_prev45"]) if f["quote15_normalized_prev45"] is not None else None
                    recent=D(f["ret60_pct"]);volume=D(f["quote15_USDT"])
                    since=D(f["ret_from_first_D0_pct"])
                    if cand["kind"]=="FIRST_D0_IMMEDIATE":
                        if t!=clock(r["WATCH_UTC"][0]) or not (ratio is not None and ratio>=D("1.5") and recent>=14 and volume>=3000000):
                            raise ValueError("STAGE52_FIRST_D0_THRESHOLD_NOT_RECOMPUTABLE")
                    elif cand["kind"]=="ONGOING_3M_SECOND_IGNITION":
                        if t<=clock(r["WATCH_UTC"][0]) or not (ratio is not None and ratio>=D("1.5") and recent>=8 and volume>=2000000 and since>=15):
                            raise ValueError("STAGE52_ONGOING_P1V03_THRESHOLD_NOT_RECOMPUTABLE")
                    else:raise ValueError("STAGE52_UNKNOWN_P1_MODE")
            elif r["p1v03_eligible_unbudgeted"] is not None:
                raise ValueError("STAGE52_CENSORED_GOT_PRIORITIZED")
        if sum(r["source_status"]==GOOD for r in j["rows"])!=j["source_complete"]:
            raise ValueError("STAGE52_SOURCE_COMPLETE_SHARD_WRONG")
        out+=j["rows"]
        receipts.append({"date":day,"shard":shard,"artifact_id":id,
          "original_github_zip_SHA256":sha(raw),"original_inside_json_SHA256":sha(content),
          "good_source":j["source_complete"],"unbudgeted":j["p1v03_unbudgeted"]})
    if ids!={(day,i) for day in DAYS for i in range(6)} or len(out)!=5400:
        raise ValueError("STAGE52_MISSING_ANY_OF_36_ORIGINAL_FULL_MARKET")
    if len({(r["date"],r["symbol"]) for r in out})!=5400:
        raise ValueError("STAGE52_DUPLICATED_SYMBOL_DATE")
    return sorted(out,key=lambda r:(r["date"],r["symbol"])),sorted(receipts,key=lambda r:(r["date"],r["shard"]))

def label(r,threshold):
    candidate=r["p1v03_eligible_unbudgeted"]
    target=(r.get("first_true_2x_HIGH_minute_UTC") if threshold==2 else
          r.get("first_real_1m_HIGH_gt"+str(threshold)+"x_UTC"))
    if not target or not candidate:return False
    return clock(candidate["at_UTC"])+5*60000<=clock(target)

def original_early(r,minutes=0):
    if not r["WATCH_UTC"] or not r.get("first_true_2x_HIGH_minute_UTC"):return False
    return any(clock(x)+minutes*60000<=clock(r["first_true_2x_HIGH_minute_UTC"]) and clock(x)<clock(r["first_true_2x_HIGH_minute_UTC"]) for x in r["WATCH_UTC"])

def budget(cases):
    """Apply original UTC06 anchored 7-day global capacity, never shard-local."""
    data=[r for r in cases if r["source_status"]==GOOD and r["p1v03_eligible_unbudgeted"] is not None]
    data=sorted(data,key=lambda x:(clock(x["p1v03_eligible_unbudgeted"]["at_UTC"]),
             -D(x["p1v03_eligible_unbudgeted"]["features"]["quote15_USDT"]),x["symbol"]))
    cnt=collections.Counter();events=[]
    for r in data:
        candidate=r["p1v03_eligible_unbudgeted"];t=clock(candidate["at_UTC"])
        origin=clock(r["date"]+"T06:00:00Z")
        k=(t-origin)//ONE_DAY
        if k not in range(7):raise ValueError("STAGE52_CANDIDATE_OFF_168H_WINDOW")
        key=r["date"],k
        delivered=cnt[key]<5
        if delivered:cnt[key]+=1
        events.append({"date":r["date"],"symbol":r["symbol"],"asof_UTC":candidate["at_UTC"],
             "kind":candidate["kind"],"status":"CAP_DELIVERED_RESEARCH" if delivered else "OVER_BUDGET_RESEARCH_NOT_DELIVERED",
             "window_day_index":k,"delivered":delivered,"source_verifiable":True,
             "quote15_USDT":candidate["features"]["quote15_USDT"],
             "ret60_pct":candidate["features"]["ret60_pct"],
             "ret_from_first_D0_pct":candidate["features"]["ret_from_first_D0_pct"]})
    if any(x>5 for x in cnt.values()):raise ValueError("STAGE52_GLOBAL_CAP_EXCEEDED")
    return events,cnt

def assess(cases,receipts):
    if len(cases)!=5400:raise ValueError("STAGE52_INCOMPLETE")
    valid=[x for x in cases if x["source_status"]==GOOD]
    gt2=[x for x in valid if x["hourly_gt2x"]]
    gt5=[x for x in valid if x["hourly_gt5x"]]
    gt10=[x for x in valid if x["hourly_gt10x"]]
    pre=[x for x in gt2 if original_early(x,0)]
    pre5=[x for x in gt2 if original_early(x,5)]
    events,blocks=budget(cases)
    delivered={(x["date"],x["symbol"]) for x in events if x["delivered"]}
    kept=[x for x in pre5 if (x["date"],x["symbol"]) in delivered and label(x,2)]
    high5=[x for x in gt5 if (x["date"],x["symbol"]) in delivered and label(x,5)]
    high10=[x for x in gt10 if (x["date"],x["symbol"]) in delivered and label(x,10)]
    capdel=sum(x["delivered"] for x in events)
    slots=[{"date":d,"index":i,"urgent_delivered":blocks[(d,i)]} for d in DAYS for i in range(7)]
    gates={
       "source_valid_2x_at_least20":len(gt2)>=20,
       "unchanged_D0_strictly_early2x_ge90pct":len(pre)/len(gt2)>=.9 if gt2 else False,
       "unchanged_D0_early5min_2x_ge85pct":len(pre5)/len(gt2)>=.85 if gt2 else False,
       "global_budgeted_P1v03_retain_D0_5min_early2x_ge80pct":len(kept)/len(pre5)>=.8 if pre5 else False,
       "all_GT5x_are_budgeted_urgent_early5min":len(gt5)>0 and len(high5)==len(gt5),
       "all_GT10x_are_budgeted_urgent_early5min":len(gt10)>0 and len(high10)==len(gt10),
       "max_urgent_UTC06_24h_at_most5":max(blocks.values(),default=0)<=5,
       "max_urgent_24h_at_most12":max(blocks.values(),default=0)<=12
    }
    verdict=("INSUFFICIENT_GT2X_DENOMINATOR" if len(gt2)<20 else
        "REJECTED_P1V03_FROZEN_GATE" if not all(gates.values()) else
        "PASS_HISTORICAL_DISCOVERY_GATES_ONLY_NOT_BUY_NOT_PRODUCTION")
    missed=[]
    for r in gt5:
        delivered_ok=(r["date"],r["symbol"]) in delivered and label(r,5)
        missed.append({"date":r["date"],"symbol":r["symbol"],"gt10":r["hourly_gt10x"],
          "original_D0_first":r["WATCH_UTC"][0] if r["WATCH_UTC"] else None,
          "real_GT5_FIRST_HIGH_UTC":r["first_real_1m_HIGH_gt5x_UTC"],
          "candidate_UTC":r["p1v03_eligible_unbudgeted"]["at_UTC"] if r["p1v03_eligible_unbudgeted"] else None,
          "global_cap_delivered_and_early_GT5":delivered_ok,
          "candidate_kind":r["p1v03_eligible_unbudgeted"]["kind"] if r["p1v03_eligible_unbudgeted"] else None})
    daily=[]
    for d in DAYS:
        one=[x for x in valid if x["date"]==d]
        cand=[x for x in events if x["date"]==d]
        daily.append({"date":d,"valid":len(one),"gt2":sum(x["hourly_gt2x"] for x in one),
          "gt5":sum(x["hourly_gt5x"] for x in one),"gt10":sum(x["hourly_gt10x"] for x in one),
          "D0_watch_coin_dates":sum(bool(x["WATCH_UTC"]) for x in one),
          "P1v03_raw_candidates":len(cand),
          "P1v03_globally_delivered":sum(x["delivered"] for x in cand),
          "P1v03_budget_overflow":sum(not x["delivered"] for x in cand)})
    return {"schema":SCHEMA,"original_run_id":RUN,"original36_source_sha_receipts":receipts,
      "attempted":5400,"publisher_1h_and_1m_valid":len(valid),
      "source_status":dict(collections.Counter(x["source_status"] for x in cases)),
      "GT2x":len(gt2),"GT5x":len(gt5),"GT10x":len(gt10),
      "D0_strict_early_GT2x":len(pre),"D0_early_ge5min_GT2x":len(pre5),
      "P1v03_unbudgeted_candidates":len(events),
      "P1v03_budget_delivered":capdel,
      "P1v03_over_budget":len(events)-capdel,
      "P1v03_budgeted_early_ge5min_GT2x_from_D0_pre5":len(kept),
      "P1v03_budgeted_early_ge5min_GT5x":len(high5),
      "P1v03_budgeted_early_ge5min_GT10x":len(high10),
      "budgeted_priority_on_non2x_coin_dates":sum(
         x["delivered"] and not next(r["hourly_gt2x"] for r in cases if r["date"]==x["date"] and r["symbol"]==x["symbol"])
         for x in events),
      "frozen_gates":gates,"verdict":verdict,
      "source_valid_gt5x_critical_cases":missed,
      "all_42_actual_UTC06_24h_delivered_blocks":slots,
      "actual_global_budget_peak":max(blocks.values(),default=0),
      "all_date_stats":daily,"point_in_time_listing":"UNVERIFIED",
      "true_exec_profit":"UNVERIFIED_NO_HISTORICAL_L2",
      "model_optimized_after_holdout":False,"other_AI_review":"NOT_DONE",
      "Frank":"UNCHANGED","Gmail":"OFF","Monster_deploy":"NO_GO","auto_trade":"NO_GO"},events

def main():
    p=argparse.ArgumentParser();p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--zip-dir",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();cases,receipts=read(json.loads(a.manifest.read_text()),a.zip_dir)
    report,events=assess(cases,receipts)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage52_pinned_v03_all5400_36SHA_true_global_cap_metrics.json").write_text(
      json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    with (a.out/"monster_stage52_all5400_originalV4_P1v03_true_minute_source_cases.jsonl").open("w") as f:
        for r in cases:f.write(json.dumps(r,sort_keys=True,ensure_ascii=False)+"\n")
    with (a.out/"monster_stage52_all_real_v03_eligible_and_global_budget_fates.jsonl").open("w") as f:
        for r in events:f.write(json.dumps(r,sort_keys=True,ensure_ascii=False)+"\n")
    print("STAGE52_36_ORIGINAL_GITHUB_BINANCE_SHA_FROZEN_P1V03_GLOBAL_GATE "+
      json.dumps({k:report[k] for k in ("publisher_1h_and_1m_valid","GT2x","GT5x","GT10x",
        "D0_strict_early_GT2x","P1v03_unbudgeted_candidates",
        "P1v03_budget_delivered","P1v03_budgeted_early_ge5min_GT2x_from_D0_pre5",
        "P1v03_budgeted_early_ge5min_GT5x","verdict")},sort_keys=True))
if __name__=="__main__":main()
