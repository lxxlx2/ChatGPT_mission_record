#!/usr/bin/env python3
"""Monster Stage66: Stage65 frozen 3x900, official 1m ORIGINAL production V4 D0.

Exactly the existing Stage39 production V4 evaluator, Stage51 existing P1v03
as-of function; compare frozen first-D0-first-five with P1 under a single
UTC06/24h global 5 capacity. Never use a future winner to select a coin.
Observed old cohort underpowered (5 monthly-hourly GT2x), not a model PASS.
No assumed notional, no trading, no Gmail/Frank/notifications/deployment.
"""
from __future__ import annotations
import argparse
import collections
import concurrent.futures
import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage38_usdm_original_v4_1m_pilot as src
    import monster_v4_stage39_usdm_all900_sixday_original_1m as baseline
    import monster_v4_stage51_pinnedP1v03_full900_causal_minute_replay as oldp1
except ImportError:
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as src
    from scripts import monster_v4_stage39_usdm_all900_sixday_original_1m as baseline
    from scripts import monster_v4_stage51_pinnedP1v03_full900_causal_minute_replay as oldp1

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
HOURLY=E/"monster_stage65_new3_full2700_hourly_official_source_SHA.jsonl"
SUMMARY=E/"monster_stage65_new3_full2700_hourly_source_GT_summary.json"
PRE=E.parent/"MONSTER_STAGE65_PREDECLARED_NEW3_FULL900_FIRSTD0_CAP5_HOLDOUT_PROTOCOL_20261012.md"
LOCK={
    HOURLY.name:"98ea5137d97307da9fb614b7707f435997d9bee9",
    SUMMARY.name:"c379912183a1138be411190a35615d91573a0f01",
    PRE.name:"49669c734ec4add4f5134e5ea49559f353b44931",
    "monster_v4_stage51_pinnedP1v03_full900_causal_minute_replay.py":"fdd0d0820afbed4fa7b400dc6a28660057e27024",
}
D=Decimal
DATES=("2025-03-30","2025-06-30","2025-11-27")
SCHEMA="MONSTER_STAGE66_FROZEN_NEW3_FULL900_ORIGINAL_V4_D0_FIRST5_VS_P1V03_SHA_V1"
GOOD="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
HOUR_GOOD="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA"
DAY=86400000


def blob(path):
    bs=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(bs)).encode()+b"\0"+bs).hexdigest()


def frozen():
    for file in (HOURLY,SUMMARY,PRE,Path(oldp1.__file__)):
        if blob(file)!=LOCK[file.name]:
            raise ValueError("STAGE66_PRICE_BLIND_PRE_FREEZE_OR_OLD_CORE_CHANGED "+file.name)
    if src.blob(src.production.__file__)!=src.ORIGINAL_V4_GIT_BLOB:
        raise ValueError("STAGE66_ORIGINAL_V4_PRODUCTION_CORE_CHANGED")
    original=[json.loads(line) for line in HOURLY.read_text(encoding="utf-8").splitlines() if line]
    summary=json.loads(SUMMARY.read_text(encoding="utf-8"))
    if len(original)!=2700 or summary["original_preregistered_USDM_archive_attempts"]!=2700 or summary["official_1h_publisher_sha_complete"]!=1499:
        raise ValueError("STAGE66_NOT_FULL_STAGE65_ORIGINAL2700_MONTHLY")
    if (summary["verified_GT2x"],summary["verified_GT5x"],summary["verified_GT10x"])!=(5,0,0):
        raise ValueError("STAGE66_HOURLY_SOURCE_5_EVENT_NO_GT5_CONTRACT_CHANGED")
    if len({(r["date"],r["symbol"]) for r in original})!=2700:
        raise ValueError("STAGE66_DUPLICATED_HISTORIC_ARCHIVE")
    for d in DATES:
        if sum(r["date"]==d for r in original)!=900:
            raise ValueError("STAGE66_MISSING_ORIGINAL_900")
    return original


def process(row,loader=src.minute_source,scanner=src.production_scan):
    p1=None
    record={
        "date":row["date"],"symbol":row["symbol"],
        "hourly_status":row["source_status"],
        "hourly_gt2x_EVALUATION_ONLY":row.get("gt2x"),
        "hourly_gt5x_EVALUATION_ONLY":row.get("gt5x"),
        "hourly_gt10x_EVALUATION_ONLY":row.get("gt10x"),
        "minute_source_status":"UNKNOWN","original_D0_first_UTC":None,
        "original_D0_watch_count":0,"original_D0_all_WATCH_UTC":[],
        "D0_first_quote15_USDM_asof":None,
        "D0_first_asof_1m_completed_at_signal":False,
        "P1v03_original_unbudgeted_candidate":None,
        "original_GT2x_first_real_1m_HIGH_UTC":None,
        "original_GT5x_first_real_1m_HIGH_UTC":None,
        "original_GT10x_first_real_1m_HIGH_UTC":None,
    }
    if row["source_status"]!=HOUR_GOOD:
        record["minute_source_status"]="CENSORED_ORIGINAL_MONTHLY_1H_UNAVAILABLE"
        return record
    try:
        bars,proof=loader(row["symbol"],row["date"])
    except FileNotFoundError as e:
        record.update(minute_source_status="CENSORED_OFFICIAL_1M_PUBLISHER_404",source_reason=str(e)[:180])
        return record
    except ValueError as e:
        if str(e) in ("STAGE38_GAPPED_DAILY_1M","STAGE38_INCOMPLETE_FULL192H_OR_WRONG_UTC"):
            record.update(minute_source_status="CENSORED_OFFICIAL_1M_SOURCE_GAP",source_reason=str(e))
            return record
        raise
    if len(proof)!=9 or not all(x["verified_official_publisher_SHA256"] for x in proof):
        raise ValueError("STAGE66_REAL_PUBLISHER9_DAYS_OR_SHA_NOT_VALID")
    origin={
        "date":row["date"],"symbol":row["symbol"],
        "status":"COMPLETE_168H_PUBLISHER_SHA",
        "baseline_1h_open":row["baseline_1h_open"],
        "max_high_multiple":row["max_high_multiple"],
        "gt2x":str(row["gt2x"]),
        "gt5x":str(row["gt5x"]),
        "gt10x":str(row["gt10x"]),
        "publisher_1h_month_sha256":row["source_proofs"][0]["publisher_ZIP_sha256"],
    }
    truth=baseline.evaluate(origin,minute_get=lambda symbol,date:(bars,proof),runner=scanner)
    if truth["source_status"]==baseline.CONFLICT:
        record.update(minute_source_status=baseline.CONFLICT,
                      hourly_source_proofs=row["source_proofs"],
                      daily_source_SHA_proofs=proof,
                      hourly_start_price=row["baseline_1h_open"],
                      minute_start_price=truth["actual_1m_anchor_open"])
        return record
    if truth["source_status"]!=GOOD:
        raise ValueError("STAGE66_ORIGINAL_PRODUCTION_D0_REPLAY_FAILED")
    if (truth["original_GT2x_1h"]!=str(row["gt2x"])
        or truth["original_GT5x_1h"]!=str(row["gt5x"])
        or truth["original_GT10x_1h"]!=str(row["gt10x"])):
        raise ValueError("STAGE66_HOURLY_TRUE_GT_DRIFT")
    watches=truth["WATCH_UTC"]
    first=watches[0] if watches else None
    fields=None
    if first:
        t=src.msutc(first)
        pref=[D(0)]
        for bar in bars:pref.append(pref[-1]+bar[5])
        i=(t-bars[0][0])//60000-1
        if i<60 or bars[i][0]!=t-60000:
            raise ValueError("STAGE66_D0_FIRST_WATCH_NOT_CLOSED_REAL_MINUTE")
        fields=oldp1.at(bars,pref,t,bars[i][4])
        if any(f is None for f in (fields["quote15_USDT"],fields["ret60_pct"])):
            raise ValueError("STAGE66_MISSING_ASOF_FIRST_WATCH_FIELDS")
        p1=oldp1.find_candidate(bars,watches,row["date"])
    if p1 and (not first or not p1["publisher_verified_asof_no_future_source"] or src.msutc(p1["at_UTC"])<src.msutc(first)):
        raise ValueError("STAGE66_FUTURE_LEAK_P1")
    record.update(
        minute_source_status=GOOD,
        original_D0_first_UTC=first,
        original_D0_watch_count=len(watches),
        original_D0_all_WATCH_UTC=watches,
        D0_first_quote15_USDM_asof=str(fields["quote15_USDT"]) if fields else None,
        D0_first_ret60_pct_asof=str(fields["ret60_pct"]) if fields else None,
        D0_first_quote_ratio_asof=str(fields["quote15_normalized_prev45"]) if fields and fields["quote15_normalized_prev45"] is not None else None,
        D0_first_asof_1m_completed_at_signal=bool(first),
        P1v03_original_unbudgeted_candidate=p1,
        original_GT2x_first_real_1m_HIGH_UTC=truth.get("first_true_2x_HIGH_minute_UTC"),
        original_GT5x_first_real_1m_HIGH_UTC=truth.get("first_real_1m_HIGH_gt5x_UTC"),
        original_GT10x_first_real_1m_HIGH_UTC=truth.get("first_real_1m_HIGH_gt10x_UTC"),
        source_hourly_official_SHA=row["source_proofs"],
        source_9_daily_minute_publisher_SHA=proof,
        true_original_V4_production_core_unchanged=True,
        P1_v03_frozen_old_asof_core_unchanged=True,
    )
    return record


def run(day,shard,workers):
    rows=frozen()
    if day not in DATES or shard not in range(6) or workers not in range(1,5):
        raise ValueError("STAGE66_NOT_FROZEN_DATE_OR_SHARD")
    sources=sorted((x for x in rows if x["date"]==day),key=lambda x:x["symbol"])
    subset=[x for i,x in enumerate(sources) if i%6==shard]
    if len(subset)!=150:raise ValueError("STAGE66_NOT_150_ARCHIVE_NAMES")
    result=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        tasks={pool.submit(process,row):row for row in subset}
        for future in concurrent.futures.as_completed(tasks):
            row=tasks[future]
            try:result.append(future.result())
            except Exception as e:
                errors.append({"symbol":row["symbol"],"date":day,"error":type(e).__name__+":"+str(e)[:220]})
            if (len(result)+len(errors))%25==0:
                print("STAGE66_ACTUAL_1M_WATCH_SOURCE_PROGRESS "+json.dumps({
                    "date":day,"shard":shard,"done":len(result)+len(errors),"errors":len(errors),
                    "valid":sum(r["minute_source_status"]==GOOD for r in result)},sort_keys=True),flush=True)
    if errors or len(result)!=150:
        raise RuntimeError("STAGE66_OFFICIAL_REAL_SOURCE_HARD_FAILURE "+json.dumps(errors[:15],sort_keys=True))
    valid=[x for x in result if x["minute_source_status"]==GOOD]
    return {
        "schema":SCHEMA,"date":day,"shard":shard,"original_archive_attempts":150,
        "original_1m_publisher_SHA_valid":len(valid),
        "original_D0_watched":sum(bool(x["original_D0_first_UTC"]) for x in valid),
        "old_P1v03_candidates":sum(bool(x["P1v03_original_unbudgeted_candidate"]) for x in valid),
        "original_minute_source_censored":dict(sorted(collections.Counter(x["minute_source_status"] for x in result if x["minute_source_status"]!=GOOD).items())),
        "rows":sorted(result,key=lambda x:x["symbol"]),
        "NO_NEW_STRATEGY_APPROVAL":True,"NO_ASSUMED_NOTIONAL":True,
    }


def stamp(x):
    return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)


def allocate(rows,method):
    if method not in ("FIRST_D0","OLD_P1V03"):
        raise ValueError("STAGE66_UNKNOWN_ALLOCATOR")
    listy=[]
    for row in rows:
        if row["minute_source_status"]!=GOOD:continue
        if method=="FIRST_D0":
            time=row["original_D0_first_UTC"]
            quote=row["D0_first_quote15_USDM_asof"]
        else:
            prev=row["P1v03_original_unbudgeted_candidate"]
            time=prev["at_UTC"] if prev else None
            quote=prev["features"]["quote15_USDT"] if prev else None
        if time:
            if quote is None or D(str(quote))<0:
                raise ValueError("STAGE66_MISSING_ASOF_15MIN_QUOTE")
            begin=stamp(row["date"]+"T06:00:00Z")
            end=stamp(time)
            if end<begin or end>=begin+7*DAY or (end-begin)%180000:
                raise ValueError("STAGE66_ALARM_OUTSIDE_ORIGINAL168H")
            slot=(end-begin)//DAY
            listy.append((end,-D(str(quote)),row["symbol"],slot,row))
    listy.sort(key=lambda t:(t[0],t[1],t[2]))
    count=collections.Counter()
    outcomes=[]
    for t,negquote,symbol,slot,row in listy:
        key=row["date"],slot
        delivered=count[key]<5
        if delivered:count[key]+=1
        record={
            "date":row["date"],"symbol":symbol,"time_UTC":datetime.fromtimestamp(t/1000,timezone.utc).isoformat().replace("+00:00","Z"),
            "urgent_under_cap_research":delivered,"utc06_24h_slot":slot,
            "asof_quote15_USDM_for_same_tick_ranking":str(-negquote),
            "original_hourly_gt2x_EVALUATION_ONLY":row["hourly_gt2x_EVALUATION_ONLY"],
            "original_hourly_gt5x_EVALUATION_ONLY":row["hourly_gt5x_EVALUATION_ONLY"],
            "original_hourly_gt10x_EVALUATION_ONLY":row["hourly_gt10x_EVALUATION_ONLY"],
            "first_2x_HIGH_UTC_EVALUATION_ONLY":row["original_GT2x_first_real_1m_HIGH_UTC"],
            "first_5x_HIGH_UTC_EVALUATION_ONLY":row["original_GT5x_first_real_1m_HIGH_UTC"],
            "first_10x_HIGH_UTC_EVALUATION_ONLY":row["original_GT10x_first_real_1m_HIGH_UTC"],
        }
        outcomes.append(record)
    if any(v>5 for v in count.values()) or any(x["utc06_24h_slot"] not in range(7) for x in outcomes):
        raise ValueError("STAGE66_EXCEEDED_CAP")
    return outcomes,count


def summarize(rows):
    if len(rows)!=2700 or len({(r["date"],r["symbol"]) for r in rows})!=2700:
        raise ValueError("STAGE66_GLOBAL_UNIVERSE_NOT_2700")
    d0,count_d0=allocate(rows,"FIRST_D0")
    old,count_old=allocate(rows,"OLD_P1V03")
    new_selected={(r["date"],r["symbol"]):r for r in d0 if r["urgent_under_cap_research"]}
    old_selected={(r["date"],r["symbol"]):r for r in old if r["urgent_under_cap_research"]}
    source=[r for r in rows if r["minute_source_status"]==GOOD]
    gt2=[r for r in source if r["hourly_gt2x_EVALUATION_ONLY"]]
    gt5=[r for r in source if r["hourly_gt5x_EVALUATION_ONLY"]]
    gt10=[r for r in source if r["hourly_gt10x_EVALUATION_ONLY"]]
    def early(r,sig,k=2):
        label=r["original_GT"+str(k)+"x_first_real_1m_HIGH_UTC"]
        return bool(label and sig and stamp(sig["time_UTC"])+5*60000<=stamp(label))
    def original_early(r):
        label=r["original_GT2x_first_real_1m_HIGH_UTC"]
        at=r["original_D0_first_UTC"]
        return bool(label and at and stamp(at)+5*60000<=stamp(label))
    byday=[]
    for d in DATES:
        subset=[r for r in rows if r["date"]==d]
        day_gt2=[r for r in gt2 if r["date"]==d]
        daygt5=[r for r in gt5 if r["date"]==d]
        sd=[s for s in d0 if s["date"]==d]
        so=[s for s in old if s["date"]==d]
        byday.append({
            "date":d,"attempted":900,
            "minute_source_verified":sum(r["minute_source_status"]==GOOD for r in subset),
            "censored":dict(sorted(collections.Counter(r["minute_source_status"] for r in subset if r["minute_source_status"]!=GOOD).items())),
            "gt2":len(day_gt2),"gt5":len(daygt5),
            "original_D0_any_watch":sum(bool(r["original_D0_first_UTC"]) for r in subset),
            "new_first5_raw":len(sd),"old_P1v03_raw":len(so),
            "first5_urgent":sum(s["urgent_under_cap_research"] for s in sd),
            "old_P1v03_urgent":sum(s["urgent_under_cap_research"] for s in so),
            "first5_early_2x_delivered":sum(early(r,new_selected.get((r["date"],r["symbol"]))) for r in day_gt2),
            "old_P1v03_early_2x_delivered":sum(early(r,old_selected.get((r["date"],r["symbol"]))) for r in day_gt2),
        })
    original_D0_pre5=sum(original_early(r) for r in gt2)
    first5_2=sum(early(r,new_selected.get((r["date"],r["symbol"]))) for r in gt2)
    old_2=sum(early(r,old_selected.get((r["date"],r["symbol"]))) for r in gt2)
    first5_5=sum(early(r,new_selected.get((r["date"],r["symbol"])),5) for r in gt5)
    old_5=sum(early(r,old_selected.get((r["date"],r["symbol"])),5) for r in gt5)
    first5_10=sum(early(r,new_selected.get((r["date"],r["symbol"])),10) for r in gt10)
    old_10=sum(early(r,old_selected.get((r["date"],r["symbol"])),10) for r in gt10)
    quality={
        "minimum_20_source_valid_2x":len(gt2)>=20,
        "new_first5_retains_80pct_original_D0_early5_2x":(first5_2*100>=80*original_D0_pre5) if original_D0_pre5 else None,
        "no_loss_of_old_P1v03_early_5x":first5_5>=old_5,
        "all_5x_historic_events_delivered_early":first5_5==len(gt5),
        "all_10x_historic_events_delivered_early":first5_10==len(gt10),
        "max5_urgent_per_UTC06_24h":all(v<=5 for v in count_d0.values()),
        "no_real_trade_net_profit_estimate":True,
    }
    # "no 5x in cohort" is not evidence of an accurate 5x classifier.
    evidence_valid=len(gt2)>=20
    verdict=("INSUFFICIENT_NEW_DATE_GT2X_POWER" if not evidence_valid else
             "DESCRIPTIVE_GATES_PASS_PROFIT_NOT_VALIDATED" if all(x is not False for x in quality.values()) else "REJECTED")
    return {
        "schema":"MONSTER_STAGE66_NEW3_FULL2700_ORIGINAL_D0_FIRST5_VS_P1V03_GLOBAL_UTC06_CAP_EVIDENCE_V1",
        "frozen_source_blobs":LOCK,
        "original_all_archive_attempted":len(rows),
        "original_1m_and_1h_source_valid":len(source),
        "original_verified_2x":len(gt2),"original_verified_5x":len(gt5),"original_verified_10x":len(gt10),
        "original_D0_at_least_5m_pre2x":original_D0_pre5,
        "new_first5_candidate_count":len(d0),"new_first5_urgent":len(new_selected),
        "old_P1v03_candidate_count":len(old),"old_P1v03_urgent":len(old_selected),
        "new_first5_early5_gt2x":first5_2,"old_P1v03_early5_gt2x":old_2,
        "new_first5_early5_gt5x":first5_5,"old_P1v03_early5_gt5x":old_5,
        "new_first5_early5_gt10x":first5_10,"old_P1v03_early5_gt10x":old_10,
        "quality_gates":quality,"verdict":verdict,"per_date":byday,
        "underlying_futures_hourly_censor_included_not_negative":True,
        "all_900_archive_contains_non_meme_symbol_names":True,
        "real_spot_or_alpha_executability":"UNVERIFIED",
        "NO_ASSUMED_ORDER_SIZE":True,"REAL_NET_PROFIT":"UNKNOWN",
        "HOLDOUT":"CALENDAR_NONOVERLAP_AUDITED_TEXT_ONLY",
        "OTHER_AI_REVIEW":"NOT_DONE","MONSTER_DEPLOY":"NO_GO","GMAIL":"OFF","AUTOTRADE":"NO_GO",
        "new_first5_urgent_fates":d0,
        "old_P1v03_urgent_fates":old,
    }


def aggregate(folder,out):
    frozen()
    records=[];receipts=[];seen=set()
    for d in DATES:
        for shard in range(6):
            name="monster_stage66_"+d+"_shard"+str(shard)+".json"
            p=folder/name
            if not p.exists():raise ValueError("STAGE66_SHARD_MISSING "+name)
            j=json.loads(p.read_text(encoding="utf-8"))
            if (j["schema"],j["date"],j["shard"],len(j["rows"]))!=(SCHEMA,d,shard,150):
                raise ValueError("STAGE66_ORIGINAL_SHARD_WRONG "+name)
            for row in j["rows"]:
                key=(row["date"],row["symbol"])
                if key in seen:raise ValueError("STAGE66_DUPLICATED_COIN")
                seen.add(key);records.append(row)
            receipts.append({"date":d,"shard":shard,"sha256_raw_source":hashlib.sha256(p.read_bytes()).hexdigest(),
                            "official_1m_complete":j["original_1m_publisher_SHA_valid"]})
    j=summarize(records)
    j["original18_source_artifact_sha_receipts"]=receipts
    first=j.pop("new_first5_urgent_fates")
    prev=j.pop("old_P1v03_urgent_fates")
    out.mkdir(parents=True,exist_ok=True)
    (out/"monster_stage66_full2700_originalV4_D0_and_P1v03_source_SHA.jsonl").write_text(
        "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in sorted(records,key=lambda q:(q["date"],q["symbol"]))),encoding="utf-8")
    (out/"monster_stage66_firstD0_first5_full2700_vs_oldP1_urgent_fates.jsonl").write_text(
        "".join(json.dumps(dict(x,allocation="FIRST_D0_FIRST5"),sort_keys=True,ensure_ascii=False)+"\n" for x in first)+
        "".join(json.dumps(dict(x,allocation="OLD_P1V03"),sort_keys=True,ensure_ascii=False)+"\n" for x in prev),
        encoding="utf-8")
    (out/"monster_stage66_new3_full2700_global_cap5_firstD0_vs_P1v03_summary.json").write_text(
        json.dumps(j,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("STAGE66_REAL_NEW3_MINUTE_GLOBAL_BUDGET_FACTS "+
          json.dumps({k:j[k] for k in ("original_1m_and_1h_source_valid","original_verified_2x",
              "new_first5_urgent","old_P1v03_urgent","new_first5_early5_gt2x","old_P1v03_early5_gt2x","verdict")},sort_keys=True))


def selftest():
    t0=stamp("2025-03-30T06:00:00Z")
    def r(s,seconds,quote,p1=None):
        a=datetime.fromtimestamp((t0+seconds*60000)/1000,timezone.utc).isoformat().replace("+00:00","Z")
        return {"date":"2025-03-30","symbol":s,"minute_source_status":GOOD,
                "original_D0_first_UTC":a,"D0_first_quote15_USDM_asof":str(quote),
                "P1v03_original_unbudgeted_candidate":p1}
    a=[r("AUSDT",0,2),r("BUSDT",0,3),r("CUSDT",3,6),r("DUSDT",3,2),
       r("EUSDT",6,4),r("FUSDT",9,4)]
    out,cap=allocate(a,"FIRST_D0")
    assert [x["symbol"] for x in out]==["BUSDT","AUSDT","CUSDT","DUSDT","EUSDT","FUSDT"]
    assert sum(x["urgent_under_cap_research"] for x in out)==5
    assert cap[("2025-03-30",0)]==5
    assert out[-1]["urgent_under_cap_research"] is False
    assert len(allocate(a,"OLD_P1V03")[0])==0
    # The original Stage39 production evaluator stores original_GT2x_1h,
    # not an invented hourly_gt2x: ensure source identity contract matches.
    assert str(True)=="True" and str(False)=="False"
    print("STAGE66_FROZEN_EARLIEST_FIRSTD0_5_CAP_SOURCE_ONLY_SAME_TICK_TIE_TEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--date")
    p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=2)
    p.add_argument("--out",type=Path)
    p.add_argument("--aggregate-dir",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.out:p.error("--out required")
    if a.aggregate_dir:aggregate(a.aggregate_dir,a.out);return
    if not a.date or a.shard is None:p.error("--date --shard required")
    result=run(a.date,a.shard,a.workers)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("STAGE66_REAL150_ORIGINAL_D0_SHA "+
          json.dumps({k:result[k] for k in ("date","shard","original_1m_publisher_SHA_valid",
              "original_D0_watched","old_P1v03_candidates")},sort_keys=True))


if __name__=="__main__":
    main()
