#!/usr/bin/env python3
"""Stage44 sealed six date-only blind USD-M hourly discovery GT truth census.

Exactly 900 original Stage36 historical archived plain-USDT names per frozen day,
not just known winners. Fetch publisher-SHA verified Binance USD-M 1h *monthly*
archives, including TWO months when a 168h window crosses a month boundary.
Never use outcome to select symbols/dates or classify missing as nonwinner.
Frozen P1v02 thresholds exist in Stage44 prereg BEFORE first market fetch.
No trade, user alerts, Frank, Gmail or production modifications.
"""
import argparse,collections,csv,hashlib,json,sys
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed

try:import monster_v4_stage37_usdm_sixdate_full900_hourly_labels as archive
except ImportError:from scripts import monster_v4_stage37_usdm_sixdate_full900_hourly_labels as archive

BASE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
CONTRACT=BASE/"monster_stage44_six_blinddate_900_usdm_and_P1_v02_prereg_20261012.json"
LEDGER=BASE/"monster_stage43_frozen_exposure_ledger_and_blind_dates.json"
INVENTORY=BASE/"monster_stage36_official_usdm_archive_vs_spot758.json"
FROZEN_DAYS=("2025-01-09","2025-09-02","2026-01-26","2026-02-24","2026-03-28","2026-05-10")
SCHEMA="MONSTER_STAGE44_BLIND_DISJOINT_DATE_USDM_ALL900_1H_OFFICIAL_SHA_GT_V1"

def locked():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    ledger=json.loads(LEDGER.read_text(encoding="utf-8"))
    if (p.get("schema")!="MONSTER_STAGE44_SIX_DATE_STAGE43_AUDIT_LOCKED_900_USDM_BLIND_HOURLY_AND_P1V02_PROTOCOL_V1" or
        tuple(p["dates"])!=FROZEN_DAYS or
        archive.blob(LEDGER)!=p["stage43_ledger"]["git_blob_sha1"] or
        p["source_inventory_sha"]!=archive.blob(INVENTORY) or
        ledger["selection"]["holdout_selected_blind_by_hashed_date_only"]!=list(FROZEN_DAYS) or
        ledger["market_data_queried_in_this_run"]!=False):
        raise ValueError("STAGE44_ORIGINAL_FROZEN_LEDGER_DATE_OR_900_ID_DRIFT")
    raw=json.loads(INVENTORY.read_text(encoding="utf-8"))
    symbols=sorted(x["symbol"] for x in raw["source_rows"] if x["archive_symbol_class"]=="EXACT_PLAIN_USDT_ARCHIVED")
    if len(symbols)!=900 or len(set(symbols))!=900:
        raise ValueError("STAGE44_FROZEN_900_CHANGED")
    return symbols

def months(day):
    d=date.fromisoformat(day)
    last=d+timedelta(days=7)
    out=[d.strftime("%Y-%m")]
    if last.strftime("%Y-%m")!=out[0]:
        out.append(last.strftime("%Y-%m"))
    return out

def eval_coin(symbol,day,source=archive.monthly_source):
    stamp=int(datetime.fromisoformat(day+"T06:00:00+00:00").timestamp()*1000)
    samples={};proof=[]
    result={"date":day,"symbol":symbol,"source_status":"PENDING",
            "venue":"BINANCE_USDM_ARCHIVED_ORIGINAL_SYMBOL",
            "historical_perpetual_type":"UNVERIFIED","real_trade_fill":"NOT_PROVEN"}
    for month in months(day):
        j,err=source(symbol,month)
        if err:
            result.update(source_status="CENSORED_PUBLISHER_MONTHLY_1H_404",
                          missing_month=month,source_proofs=proof)
            return result
        original=j["bars"]
        proof.append({"month":month,"publisher_ZIP_sha256":j["publisher_zip_sha256"],"hourly_bars":len(original)})
        for k,v in original.items():
            if k in samples and samples[k]!=v:
                raise ValueError("STAGE44_CONFLICTING_OFFICIAL_HOURLY_CROSSMONTH")
            samples[k]=v
    stamps=[stamp+i*3600000 for i in range(168)]
    found=[k for k in stamps if k in samples]
    if len(found)!=168:
        result.update(source_status="CENSORED_NOT_168_CONSECUTIVE_HOURS",
                      available_1h_bars=len(found),source_proofs=proof)
        return result
    candle=[samples[k] for k in stamps]
    baseline=candle[0][0]
    high=max(x[1] for x in candle)
    if baseline<=0:raise ValueError("STAGE44_ZERO_BASELINE")
    result.update(source_status="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA",
                  baseline_utc=day+"T06:00:00Z",
                  baseline_1h_open=str(baseline),
                  max_high_multiple=str(high/baseline),
                  source_proofs=proof)
    for n in (2,5,10):
        index=next((i for i,x in enumerate(candle) if x[1]>=baseline*n),None)
        result[f"gt{n}x"]=index is not None
        result[f"first_gt{n}x_1h_utc"]=(datetime.fromtimestamp(stamps[index]/1000,timezone.utc).isoformat().replace("+00:00","Z") if index is not None else None)
    return result

def run(day,shard,workers):
    original=locked()
    if day not in FROZEN_DAYS or shard not in range(6) or workers not in (1,2,3,4):
        raise ValueError("STAGE44_DATE_OR_SHARD_NOT_FROZEN")
    chosen=[s for i,s in enumerate(original) if i%6==shard]
    if len(chosen)!=150:raise ValueError("STAGE44_SHARD_NOT_150")
    cases=[];errors=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(eval_coin,s,day):s for s in chosen}
        for future in as_completed(jobs):
            s=jobs[future]
            try:
                r=future.result()
                if r["symbol"]!=s:raise ValueError("STAGE44_WRONG_COIN_RESULT")
                cases.append(r)
            except Exception as e:
                errors.append({"symbol":s,"failure_type":type(e).__name__,"message":str(e)[:180]})
            if (len(cases)+len(errors))%25==0:
                print("STAGE44_REAL_SOURCE_PROGRESS "+json.dumps({"date":day,"shard":shard,"done":len(cases),"hard_errors":len(errors),"goal":150}),flush=True)
    if errors or len(cases)!=150:
        raise RuntimeError("STAGE44_SOURCE_INTEGRITY_OR_NETWORK_FAIL_CLOSED "+json.dumps(errors[:6]))
    statuses=collections.Counter(r["source_status"] for r in cases)
    good=[r for r in cases if r["source_status"]=="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA"]
    return {"schema":SCHEMA,"date":day,"shard":shard,"locked_universe_symbol_names":900,
        "locked_new_date_without_7d_overlap_in_pinned_history":True,
        "original_source_status_counts":dict(statuses),"all150_attempted":True,
        "valid":len(good),"gt2x":sum(r["gt2x"] for r in good),
        "gt5x":sum(r["gt5x"] for r in good),"gt10x":sum(r["gt10x"] for r in good),
        "rows":sorted(cases,key=lambda r:r["symbol"]),
        "new_rule_P1_v02_untested":True,"Mac_deployment":"NO_GO","Gmail":"OFF","Frank":"UNCHANGED"}

def test():
    assert months("2025-01-09")==["2025-01"]
    assert months("2026-01-26")==["2026-01","2026-02"]
    assert months("2026-02-24")==["2026-02","2026-03"]
    target="2026-01-26"
    ts=int(datetime.fromisoformat(target+"T06:00:00+00:00").timestamp()*1000)
    left={};right={}
    for i in range(168):
        s=ts+i*3600000
        bucket=left if datetime.fromtimestamp(s/1000,timezone.utc).strftime("%Y-%m")=="2026-01" else right
        bucket[s]=(Decimal(1),Decimal(5 if i==130 else 1),Decimal(1),Decimal(10))
    def fetch(_sym,mon):
        return {"bars":left if mon=="2026-01" else right,"publisher_zip_sha256":"a"*64},None
    r=eval_coin("TESTUSDT",target,source=fetch)
    assert r["source_status"]=="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA"
    assert r["gt2x"] and r["gt5x"] and not r["gt10x"] and len(r["source_proofs"])==2
    r=eval_coin("TESTUSDT",target,source=lambda _s,m:(None,"SOURCE_404") if m=="2026-02" else fetch(_s,m))
    assert r["source_status"]=="CENSORED_PUBLISHER_MONTHLY_1H_404" and "gt2x" not in r
    print("STAGE44_CROSS_MONTH_REAL_PUBLISHER_SHA_168H_EXPOSURE_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--date")
    p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.selftest:test();return
    if a.date is None or a.shard is None or a.output is None:p.error("--date --shard --output required")
    j=run(a.date,a.shard,a.workers)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(j,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("STAGE44_BLINDDATE_SHA_HOURLY_GT_CENSUS "+json.dumps({
       k:j[k] for k in ("date","shard","valid","gt2x","gt5x","gt10x","original_source_status_counts")},sort_keys=True))
if __name__=="__main__":main()
