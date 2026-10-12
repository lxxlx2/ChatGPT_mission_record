#!/usr/bin/env python3
"""Stage73: original V4 WATCH on strictly verified minute source prefixes.

Deliberately does not require a future week, monthly USD-M 1h ground truth, or
a future spot/DEX trading path before recording historical WATCH events.
Existing Stage66 original full-data records are unchanged and checked exactly.
Research-only and NOT historical exchangeInfo / deploy / alert / trade proof.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import concurrent.futures
import hashlib
import json
import tempfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage66_new3_original_1m_D0_first5_vs_P1v03 as stage66
    import monster_v4_stage38_usdm_original_v4_1m_pilot as original
except ImportError:
    from scripts import monster_v4_stage66_new3_original_1m_D0_first5_vs_P1v03 as stage66
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as original

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
FREEZE=E.parent/"MONSTER_STAGE73_M03_ASOF_WATCH_VS_FUTURE_SCOREABILITY_2700_PREREG_20261013.md"
OLD=E/"monster_stage66_full2700_originalV4_D0_and_P1v03_source_SHA.jsonl"
PIN={
    FREEZE.name:"5a055042777593ade4eaf52c0175679ffd57e7fb",
    OLD.name:"9eb19c22ae8d34d030ccabd7176c3cd4d2e2e3f8",
}
SCHEMA="MONSTER_STAGE73_ALL2700_M03_SOURCE_PREFIX_WATCH_WITHOUT_FUTURE_SCOREABILITY_V1"
GOOD="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
ONE=60000


def gitblob(p):
    raw=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def originals():
    for p in (FREEZE,OLD):
        if gitblob(p)!=PIN[p.name]:
            raise ValueError("STAGE73_PREREG_OR_OLD_2700_GIT_BLOB_CHANGED "+p.name)
    sources=stage66.frozen()
    prior=[json.loads(line) for line in OLD.read_text(encoding="utf-8").splitlines() if line]
    if len(sources)!=2700 or len(prior)!=2700:
        raise ValueError("STAGE73_ORIGINAL2700_NOT_PRESENT")
    indexed={(x["date"],x["symbol"]):x for x in prior}
    if len(indexed)!=2700 or {(s["date"],s["symbol"]) for s in sources}!=set(indexed):
        raise ValueError("STAGE73_ALL2700_SOURCE_POPULATION_MISMATCH")
    if sum(x["minute_source_status"]==GOOD for x in prior)!=1497:
        raise ValueError("STAGE73_ORIGINAL_FUTURE_SCOREABLE_COUNT_MISMATCH")
    return sources,indexed


def scan_verified_prefix(symbol,day,bars):
    """Use exactly Stage38 production.observe_snapshot + process_queue on as-of 3m.

    Bars are uninterrupted, already independently publisher-SHA-verified by
    the caller. Closed 5m candles strictly predate current ms, no future data
    returned to callback. Replays even when last five-minute bar is unfinished.
    """
    begin=original.msutc(day+"T06:00:00Z")-24*3600000
    if len(bars)>original.BARS:
        raise ValueError("STAGE73_PREFIX_LONGER_THAN_ORIGINAL_192H")
    if any(x[0]!=begin+i*ONE for i,x in enumerate(bars)):
        raise ValueError("STAGE73_PREFIX_GAP_OR_INVALID_UTC_ORIGIN")
    if len(bars)<=original.WARMUP+2:
        return {"WATCH_UTC":[],"SETUP_UTC":[],"polls":0,
                "status":"WARMUP_INCOMPLETE_NO_ASOF_DECISION"}
    sums=[Decimal(0)]
    for bar in bars:sums.append(sums[-1]+bar[5])
    closed=original.replay.make_closed_five_minute_bars(bars[:(len(bars)//5)*5])
    closed_ends=[int(c[6]) for c in closed]
    limit=min(len(bars),original.WARMUP+original.ACTIVE)
    polls=0
    with tempfile.TemporaryDirectory(prefix="monster73_prefix_") as d:
        db=original.production.open_store(Path(d)/"stage73_v4_original.sqlite3")
        try:
            def history(_venue,_symbol,at_ms):
                k=bisect.bisect_left(closed_ends,at_ms)
                return closed[max(0,k-8):k]
            for i in range(original.WARMUP+2,limit,3):
                now=bars[i][0]+ONE
                rolling=sums[i+1]-sums[i+1-1440]
                original.production.observe_snapshot(db,"futures",now,[{
                    "symbol":symbol,"lastPrice":str(bars[i][4]),
                    "quoteVolume":str(rolling)
                }])
                original.production.process_queue(db,now,history)
                polls+=1
            events=[dict(row) for row in db.execute(
                "SELECT event_type,observed_ms FROM events ORDER BY observed_ms,event_id")]
        finally:db.close()
    watch=[original.stamp(v["observed_ms"]) for v in events if v["event_type"]=="WATCH_EARLY"]
    setup=[original.stamp(v["observed_ms"]) for v in events if v["event_type"]=="SETUP_ACTIVE"]
    if polls != len(range(original.WARMUP+2,limit,3)):
        raise ValueError("STAGE73_MISCOUNTED_REAL_ORIGINAL_3M_TICKS")
    return {"WATCH_UTC":watch,"SETUP_UTC":setup,"polls":polls,
            "status":"SOURCE_PREFIX_CAUSAL_REAL_V4_REPLAY"}


def sequential_source(symbol,day,reader=None):
    """First missing/invalid *day* ends the observable verified prefix.

    An available day cannot be assembled from unverified partial CSV rows.
    Do not use monthly hourly GT as a precondition for D0 candidate existence.
    """
    if reader is None:reader=original.verified_1m_day
    chunks=[];receipts=[];failed=None
    for offset in range(-1,8):
        dt=date.fromisoformat(day)+timedelta(days=offset)
        try:
            one,proof=reader(symbol,dt)
        except (FileNotFoundError,ValueError) as e:
            if isinstance(e,ValueError) and not str(e).startswith("STAGE38_GAPPED_DAILY_1M"):
                # Especially SHA mismatch and corrupt source: never silently
                # treat source-integrity violations as merely unavailable data.
                raise
            failed={"date":dt.isoformat(),"reason":type(e).__name__+":"+str(e)[:170]}
            break
        if (proof.get("date")!=dt.isoformat() or
            proof.get("verified_official_publisher_SHA256") is not True or
            len(proof.get("zip_sha256",""))!=64 or
            len(one)!=1440 or proof.get("bars")!=1440 or
            any(x[0]!=original.msutc(dt.isoformat()+"T00:00:00Z")+n*ONE for n,x in enumerate(one))):
            raise ValueError("STAGE73_DAILY_SOURCE_SHA_OR_MINUTE_SEQUENCE_NOT_PROVEN")
        chunks.extend(one)
        receipts.append(proof)
    aligned=chunks[6*60:6*60+original.BARS]
    if aligned:
        begin=original.msutc(day+"T06:00:00Z")-24*3600000
        if any(x[0]!=begin+i*ONE for i,x in enumerate(aligned)):
            raise ValueError("STAGE73_DAILY_PREFIX_ASSEMBLY_GAP")
    return aligned,receipts,failed


def original_case(row,older,reader=None,scanner=scan_verified_prefix):
    if (row["date"],row["symbol"])!=(older["date"],older["symbol"]):
        raise ValueError("STAGE73_WRONG_FROZEN_COIN_IDENTITY")
    bars,receipts,failed=sequential_source(row["symbol"],row["date"],reader)
    current=scanner(row["symbol"],row["date"],bars)
    realwatch=current["WATCH_UTC"]
    oldgood=older["minute_source_status"]==GOOD
    if oldgood:
        if failed or len(bars)!=original.BARS or len(receipts)!=9:
            raise ValueError("STAGE73_ORIGINAL_FULL_SOURCE_NOW_INCOMPLETE_SOURCE_CHANGE")
        if receipts!=older["source_9_daily_minute_publisher_SHA"]:
            raise ValueError("STAGE73_1497_ORIGINAL_PUBLISHER_SHA_RECEIPT_DRIFT")
        if realwatch!=older["original_D0_all_WATCH_UTC"]:
            raise ValueError("STAGE73_ORIGINAL1497_FULL_WATCH_LIST_PARITY_FAILED")
        if "SETUP_UTC" in older and current["SETUP_UTC"]!=older["SETUP_UTC"]:
            raise ValueError("STAGE73_ORIGINAL1497_FULL_SETUP_LIST_PARITY_FAILED")
    observable=current["polls"]>0
    return {
        "date":row["date"],"symbol":row["symbol"],
        "original_stage66_hourly_status":row["source_status"],
        "original_stage66_minute_status":older["minute_source_status"],
        "future_7d_scoreable_in_original_Stage66":oldgood,
        "ASOF_PREFIX_VERIFIED_SOURCE_DAYS":len(receipts),
        "ASOF_PREFIX_VERIFIED_1M_BARS":len(bars),
        "ASOF_PREFIX_FIRST_WATCH_UTC":realwatch[0] if realwatch else None,
        "ASOF_PREFIX_ALL_WATCH_UTC":realwatch,
        "ASOF_PREFIX_ALL_SETUP_UTC":current["SETUP_UTC"],
        "ASOF_PREFIX_POLLS":current["polls"],
        "ASOF_PREFIX_STATUS":current["status"] if observable else "UNKNOWN_INSUFFICIENT_PREFIX_NO_V4_TICK",
        "ASOF_PREFIX_LAST_CLOSED_MINUTE_UTC":original.stamp(bars[-1][0]+ONE) if bars else None,
        "SOURCE_FIRST_MISSING_OR_GAPPED_DAY":failed,
        "OFFICIAL_DAILY_PUBLISHER_SHA_RECEIPTS":receipts,
        "OLD1497_EVENT_PARITY_CONFIRMED":True if oldgood else None,
        "FUTURE_OUTCOME_FOR_NEW_PREFIX_WATCH":"UNSCORED_IN_ORIGINAL_FROZEN_RESULT" if not oldgood else "ORIGINAL_FUTURE_LABEL_SEPARATE",
        "ASOF_EXCHANGE_LISTING_AND_SPOT_DEX_BUYABILITY":"UNKNOWN",
        "NO_ACTUAL_TRADE_OR_ORDER_NOTIONAL":True,
    }


def summary(rows):
    if len(rows)!=2700 or len({(v["date"],v["symbol"]) for v in rows})!=2700:
        raise ValueError("STAGE73_NOT_FULL2700")
    counts={}
    for day in stage66.DATES:
        q=[x for x in rows if x["date"]==day]
        cens=[x for x in q if not x["future_7d_scoreable_in_original_Stage66"]]
        counts[day]={
            "frozen_attempts":900,
            "original_future_label_scoreable":sum(x["future_7d_scoreable_in_original_Stage66"] for x in q),
            "new_prefix_has_at_least_one_causal_3m_tick":sum(x["ASOF_PREFIX_POLLS"]>0 for x in q),
            "original_unscored_with_verified_causal_ticks":sum(x["ASOF_PREFIX_POLLS"]>0 for x in cens),
            "original_unscored_with_real_watch":sum(bool(x["ASOF_PREFIX_ALL_WATCH_UTC"]) for x in cens),
            "old_complete_event_parity":sum(x["OLD1497_EVENT_PARITY_CONFIRMED"] is True for x in q),
            "orig_unscored_no_prefix":sum(x["ASOF_PREFIX_POLLS"]==0 for x in cens),
            "first_missing_days":dict(sorted(collections.Counter(
                (x["SOURCE_FIRST_MISSING_OR_GAPPED_DAY"] or {}).get("date","ALL_9_DAYS_COMPLETE") for x in cens).items()))
        }
    total=lambda name:sum(x[name] for x in counts.values())
    return {
        "schema":SCHEMA,"original_source_git_blobs":PIN,
        "research_frozen2700_population":2700,
        "original_future_scoreable_1497_matches":total("old_complete_event_parity"),
        "original_unscored_1203_count":2700-total("original_future_label_scoreable"),
        "original_unscored_with_real_prefix_discovery":total("original_unscored_with_real_watch"),
        "original_unscored_with_verified_V4_ticks":total("original_unscored_with_verified_causal_ticks"),
        "original_unscored_no_valid_D0_tick":total("orig_unscored_no_prefix"),
        "by_date":counts,
        "FACTUAL_MARKET_TRADABILITY_DENOMINATOR":"UNKNOWN_NOT_COVERED_BY_HISTORICAL_ARCHIVE_SYMBOLS",
        "ORIGINAL_CONDITIONED_FUTURE_2X_RECALL":"UNCHANGED_NOT_RECALCULATED",
        "FUTURE_EVENT_LABEL_IN_SOURCE_CENSORED":"UNSCORED_NOT_NEGATIVE",
        "P2":"REJECTED","M03":"PREFIX_DISCOVERY_ACCOUNTED_LISTING_DENOMINATOR_OPEN",
        "INDEPENDENT_REVIEW_OF_THIS_CHANGE":"NOT_DONE",
        "MONSTER_DEPLOY":"NO_GO","GMAIL":"OFF","AUTOTRADE":"NO_GO",
        "ORDER_NOTIONAL":"UNSPECIFIED",
    }


def pilot(rows,old):
    wanted=[
        ("2025-06-30","HFTUSDT"),
        ("2025-06-30","HUSDT"),
        ("2025-11-27","IRYSUSDT"),
        ("2025-11-27","BROCCOLIF3BUSDT"),
        ("2025-11-27","PIPPINUSDT"),
        ("2025-11-27","TANSSIUSDT"),
    ]
    out=[]
    index={(x["date"],x["symbol"]):x for x in rows}
    for key in wanted:
        if key not in index:raise ValueError("STAGE73_PILOT_EXPECTED_ORIGINAL_SYMBOL_MISSING "+str(key))
        out.append(original_case(index[key],old[key]))
    return out


def run(day,shard,workers,rows,old):
    if day not in stage66.DATES or shard not in range(6) or workers not in range(1,5):
        raise ValueError("STAGE73_NONFROZEN_CASE_OR_SHARD")
    cohort=sorted((x for x in rows if x["date"]==day),key=lambda z:z["symbol"])
    selected=[x for i,x in enumerate(cohort) if i%6==shard]
    if len(selected)!=150:raise ValueError("STAGE73_NOT_FROZEN150_ORIGINAL_SHARD")
    output=[];failures=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(original_case,r,old[r["date"],r["symbol"]]):r for r in selected}
        for done in concurrent.futures.as_completed(jobs):
            entry=jobs[done]
            try:output.append(done.result())
            except Exception as e:
                failures.append({"date":entry["date"],"symbol":entry["symbol"],
                                 "hard_error":type(e).__name__+":"+str(e)[:250]})
            if (len(output)+len(failures))%25==0:
                print("STAGE73_INDEPENDENT_ASOF_ALL_SOURCE_PROGRESS "+json.dumps({
                    "date":day,"shard":shard,"processed":len(output)+len(failures),"failures":len(failures)},sort_keys=True),flush=True)
    if failures or len(output)!=150:
        raise RuntimeError("STAGE73_HARD_FAIL_NOT_VERIFIED_SOURCE "+json.dumps(failures[:25],sort_keys=True))
    return sorted(output,key=lambda x:x["symbol"])


def aggregate(folder,out):
    sources,old=originals()
    read=[];seen=set();proofs=[]
    for day in stage66.DATES:
        for i in range(6):
            p=folder/("monster_stage73_"+day+"_shard"+str(i)+".json")
            if not p.exists():raise ValueError("STAGE73_18_SHARDS_NOT_COMPLETE "+str(p))
            j=json.loads(p.read_text(encoding="utf-8"))
            if len(j)!=150:raise ValueError("STAGE73_BAD_150_SHARD_COUNT")
            for row in j:
                key=(row["date"],row["symbol"])
                if key in seen or row["date"]!=day:
                    raise ValueError("STAGE73_DUPLICATE_OR_WRONG_SOURCE_DATE")
                seen.add(key);read.append(row)
            proofs.append({"date":day,"shard":i,"source_file_sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    if seen!={(r["date"],r["symbol"]) for r in sources}:
        raise ValueError("STAGE73_SOME_OF_FROZEN2700_MISSING")
    result=summary(read)
    if result["original_future_scoreable_1497_matches"]!=1497:
        raise ValueError("STAGE73_1497_CONDITIONED_VALIDITY_PARITY_NOT_PROVEN")
    result["original18_shard_SHA256_receipts"]=proofs
    out.mkdir(parents=True,exist_ok=True)
    (out/"monster_stage73_original2700_prefix_watch_separate_from_future_labels.jsonl").write_text(
        "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in sorted(read,key=lambda z:(z["date"],z["symbol"]))),encoding="utf-8")
    (out/"monster_stage73_original2700_asof_prefix_vs_future_scoreability_summary.json").write_text(
        json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("STAGE73_FULL2700_ASOF_SOURCE_PREFIX_SEPARATE_FROM_FUTURE_GT "+
          json.dumps({k:result[k] for k in ("original_future_scoreable_1497_matches",
            "original_unscored_1203_count","original_unscored_with_real_prefix_discovery",
            "original_unscored_with_verified_V4_ticks","original_unscored_no_valid_D0_tick")},sort_keys=True))


def selftest():
    from datetime import datetime,timezone
    date_="2025-11-27"
    start=original.msutc(date_+"T06:00:00Z")-24*3600000
    synthetic=[(start+i*ONE,Decimal(100),Decimal(100),Decimal(100),Decimal(100),Decimal(100),1)
               for i in range(original.WARMUP+130)]
    a=scan_verified_prefix("TESTUSDT",date_,synthetic)
    assert a["polls"]==len(range(original.WARMUP+2,len(synthetic),3)) and not a["WATCH_UTC"]
    extended=synthetic+[(start+i*ONE,Decimal(999),Decimal(1000),Decimal(998),Decimal(999),Decimal(99999),25)
                        for i in range(len(synthetic),len(synthetic)+180)]
    bb=scan_verified_prefix("TESTUSDT",date_,extended)
    assert bb["WATCH_UTC"][:len(a["WATCH_UTC"])]==a["WATCH_UTC"]
    # Full tick-by-tick prefix must match previously emitted signals, even
    # if future bars have very different prices/volume.
    assert all(t in bb["WATCH_UTC"] for t in a["WATCH_UTC"])
    def reader(sym,dd):
        if dd.isoformat()>="2025-11-28":
            raise FileNotFoundError("synthetic future ZIP 404")
        start_day=original.msutc(dd.isoformat()+"T00:00:00Z")
        daybars=[(start_day+i*ONE,Decimal(100),Decimal(100),Decimal(100),Decimal(100),Decimal(100),1)
                 for i in range(1440)]
        return daybars,{"date":dd.isoformat(),"zip_sha256":"a"*64,
                        "verified_official_publisher_SHA256":True,"bars":1440}
    partial,receipts,missing=sequential_source("TESTUSDT",date_,reader)
    assert len(receipts)==2 and missing["date"]=="2025-11-28"
    assert len(partial)==2*1440-360
    assert scan_verified_prefix("TESTUSDT",date_,partial)["polls"]>0
    def bad(sym,dd):
        if dd.isoformat()>="2025-11-26":
            raise ValueError("STAGE38_OFFICIAL_ZIP_HASH_NOT_MATCH_PUBLISHER")
        return reader(sym,dd)
    try:sequential_source("TESTUSDT",date_,bad)
    except ValueError as err:
        assert "HASH_NOT_MATCH" in str(err)
    else:raise AssertionError("STAGE73_UNVERIFIED_SOURCE_ACCEPTED")
    print("STAGE73_CAUSAL_PREFIX_SYNTHETIC_FUTURE_SUFFIX_NOT_NEEDED_SOURCE_GAP_AND_SHA_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--pilot",action="store_true")
    p.add_argument("--date")
    p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=2)
    p.add_argument("--out",type=Path)
    p.add_argument("--aggregate-dir",type=Path)
    args=p.parse_args()
    if args.selftest:selftest();return
    if args.out is None:p.error("--out required")
    rows,old=originals()
    if args.aggregate_dir:
        aggregate(args.aggregate_dir,args.out)
        return
    if args.pilot:
        cases=pilot(rows,old)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(cases,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("STAGE73_REAL_OFFICIAL_PILOT "+json.dumps([{
            "symbol":z["symbol"],"date":z["date"],"prefix_days":z["ASOF_PREFIX_VERIFIED_SOURCE_DAYS"],
            "polls":z["ASOF_PREFIX_POLLS"],"watched":bool(z["ASOF_PREFIX_ALL_WATCH_UTC"]),
            "old_scored":z["future_7d_scoreable_in_original_Stage66"],
            "missing":z["SOURCE_FIRST_MISSING_OR_GAPPED_DAY"]} for z in cases],sort_keys=True))
        return
    if args.date is None or args.shard is None:p.error("--date and --shard required")
    result=run(args.date,args.shard,args.workers,rows,old)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("STAGE73_TRUE_150_CASES_DONE "+json.dumps({
        "date":args.date,"shard":args.shard,"all":len(result),
        "old_valid":sum(q["OLD1497_EVENT_PARITY_CONFIRMED"] is True for q in result),
        "new_old_unscored_watch":sum(not q["future_7d_scoreable_in_original_Stage66"]
                          and bool(q["ASOF_PREFIX_ALL_WATCH_UTC"]) for q in result)},sort_keys=True))


if __name__=="__main__":
    main()
