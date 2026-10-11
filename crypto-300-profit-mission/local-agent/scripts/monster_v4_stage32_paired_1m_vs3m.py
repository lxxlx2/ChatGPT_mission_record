#!/usr/bin/env python3
"""Stage32 paired truly unseen six-date full758 original-V4 3m versus 1m poll.

Original 3m engine unmodified, candidate 1m uses EXACT SAME production V4
observe_snapshot/process_queue but at 60-second poll cadence. Same exact 216h
publisher SHA verified Binance Spot 1m bars + monthly 1h retrospective truth.
One SQLite per symbol per arm; not the global multi-symbol live D1 queue.
WATCH is NOT a BUY and 2x/5x HIGH is NOT a realized trade.
"""
import argparse
import bisect
import concurrent.futures
import json
import statistics
import sys
import tempfile
import urllib.error
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage16_seven_day_labels as gt
    import monster_v4_stage26_continuous168h as original
    import monster_v4_stage30_newdates_full168h as inventory
    import monster_v4_historical_replay as replay
    import monster_v4_shadow as production
except ImportError:
    from scripts import monster_v4_stage16_seven_day_labels as gt
    from scripts import monster_v4_stage26_continuous168h as original
    from scripts import monster_v4_stage30_newdates_full168h as inventory
    from scripts import monster_v4_historical_replay as replay
    from scripts import monster_v4_shadow as production

PROOF=original.EVIDENCE/"monster_stage32_6newdate_1m_vs3m_full758_prereg_20261012.json"
SHARDS=6
NEW_DAYS=("2025-03-19","2025-06-19","2025-09-19","2025-12-19","2026-01-19","2026-03-19")

def frozen():
    p=json.loads(PROOF.read_text(encoding="utf-8"))
    if (p["schema"]!="MONSTER_STAGE32_SIX_FRESH_DATE_1MIN_VS_ORIGINAL_3MIN_FULL758_V4_PREREG_V1"
        or tuple(p["frozen_dates_utc"])!=NEW_DAYS or p["complete_original_spot_universe"]!=758):
        raise ValueError("STAGE32_FROZEN_DATE_OR_COHORT_DRIFT")
    blobs={"monster_v4_shadow_blob_sha1":production.__file__,
           "stage26_original_scanner_blob_sha1":original.__file__,
           "stage16_GT_blob_sha1":gt.__file__,
           "stage30_inventory_reader_blob_sha1":inventory.__file__}
    for k,v in blobs.items():
        if original.git_sha(v)!=p["frozen_production_files"][k]:
            raise ValueError("STAGE32_ORIGINAL_SOURCE_OR_MODEL_BLOB_CHANGED:"+k)
    # Existing Stage30 artifact cohort remains original-758 SHA verified
    inventory.frozen()
    return p

def scan_one_minute(symbol,day,bars):
    """1m frequency only; no threshold/indicator/proxy/production edits."""
    anchor=replay.parse_ms(day.isoformat()+"T06:00:00Z")
    base=anchor-original.WARMUP_MINUTES*60000
    if len(bars)!=original.EXPECTED_MINUTES or bars[0][0]!=base:
        raise ValueError("STAGE32_1MIN_SOURCE_START_OR_LENGTH")
    if any(r[0]!=base+i*60000 for i,r in enumerate(bars)):
        raise ValueError("STAGE32_1MIN_GAPPED_SOURCE")
    prefix=[Decimal(0)]
    for bar in bars:prefix.append(prefix[-1]+bar[5])
    candles=replay.make_closed_five_minute_bars(bars)
    ends=[int(c[6]) for c in candles]
    poll_start=original.WARMUP_MINUTES
    stop=original.WARMUP_MINUTES+original.ACTIVE_MINUTES
    polls=0;zero=0
    with tempfile.TemporaryDirectory(prefix="monster32_1m_") as td:
        db=production.open_store(Path(td)/"V4_ONLY_CADENCE_1min.sqlite")
        try:
            def closed5(_venue,_symbol,observed):
                p=bisect.bisect_left(ends,observed)
                return candles[max(0,p-8):p]
            for i in range(poll_start,stop):
                ms=bars[i][0]+60000
                if bars[i][6]==0 or bars[i][5]==0:zero+=1
                quote=prefix[i+1]-prefix[i+1-replay.ROLLING_24H_BARS]
                production.observe_snapshot(db,"spot",ms,[{"symbol":symbol,
                    "lastPrice":str(bars[i][4]),"quoteVolume":str(quote)}])
                production.process_queue(db,ms,closed5)
                polls+=1
            for extra in range(1,8):
                ms=anchor+original.ACTIVE_MINUTES*60000+extra*180000
                production.process_queue(db,ms,closed5)
            events=[dict(r) for r in db.execute(
                "SELECT event_type,observed_ms FROM events ORDER BY observed_ms,event_id")]
            watch=[r for r in events if r["event_type"]=="WATCH_EARLY"]
            setups=[r for r in events if r["event_type"]=="SETUP_ACTIVE"]
            invalid=[r for r in events if r["event_type"]=="INVALIDATED"]
            qstatus={r["status"]:r["n"] for r in db.execute(
                "SELECT status,COUNT(*) AS n FROM candidate_queue GROUP BY status")}
        finally:
            db.close()
    trade=[];funding_until=0
    for w in watch:
        enter=w["observed_ms"]+180000
        overlap=enter<funding_until
        if overlap:
            low={"status":"SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED"}
            stress=None
        else:
            low=replay._proxy_trade(bars,base,w["observed_ms"],180000,20)
            stress=replay._proxy_trade(bars,base,w["observed_ms"],180000,100)
            funding_until=enter+24*3600000
        trade.append({"watch_utc":replay.utc(w["observed_ms"]),
            "proxy_20bps":low,"proxy_100bps":stress})
    return {"watch_count":len(watch),"setups":len(setups),"invalidations":len(invalid),
        "polls":polls,"zero_trade_minute_polls":zero,
        "watch_utcs":[replay.utc(w["observed_ms"]) for w in watch],
        "setup_utcs":[replay.utc(w["observed_ms"]) for w in setups],
        "queue_final_status":qstatus,"trade_proxies":trade,
        "continuous_sqlite_reset_count":0,
        "scope":"PER_SYMBOL_V4_SAME_RULES_HIGHER_POLL_FREQUENCY_NOT_REAL_GLOBAL_QUEUE"}

def first_cross_class(day,bars,hr,arm):
    out={}
    for mult in (2,5,10):
        gt_true=hr["gross_high_ge_"+str(mult)+"x"]
        cross=original.first_real_1m_cross(day,bars,hr["baseline_1h_open"],mult)
        if (cross is not None)!=gt_true:
            raise ValueError("STAGE32_GT_MONTH_HOUR_VS_MINUTE_HIGH_DISAGREE")
        watches=[replay.parse_ms(v) for v in arm["watch_utcs"]]
        earliest=watches[0] if watches else None
        eligible=[w for w in watches if cross is not None and w<=cross]
        nearest=max(eligible) if eligible else None
        status=("NOT_2_5_10X" if not gt_true else
                "NO_WATCH" if earliest is None else
                "EARLY" if earliest<=cross else "LATE")
        out[str(mult)+"x"]={"is_gt_positive":gt_true,"classification":status,
          "cross_1m_high_UTC":replay.utc(cross) if cross is not None else None,
          "first_watch_UTC":arm["watch_utcs"][0] if watches else None,
          "nearest_pre_cross_UTC":replay.utc(nearest) if nearest is not None else None,
          "nearest_pre_cross_lead_min":round((cross-nearest)/60000,3) if nearest is not None else None}
    return out

def compare_one(symbol,day,hourly_get=gt.label,minute_get=original.read_complete_216h):
    h=hourly_get(symbol,day)
    if h.get("symbol")!=symbol:raise ValueError("STAGE32_HOURLY_SYMBOL_DRIFT")
    if h["status"] not in ("MONTH_ARCHIVE_MISSING_404","VERIFIED_COMPLETE_168H","CENSORED_7D_HOURLY_GAP"):
        raise RuntimeError("STAGE32_HOURLY_NETWORK_OR_INTEGRITY_FAILURE:"+h["status"])
    r={"date":day.isoformat(),"symbol":symbol,"hourly_source_status":h["status"]}
    if h["status"]!="VERIFIED_COMPLETE_168H":
        r["status"]="CENSORED_GT_NOT_COMPLETE_168H"
        return r
    if len(h.get("archive_sha256",""))!=64:
        raise RuntimeError("STAGE32_UNVERIFIED_MONTHLY_HOURLY_PUBLISHER_SHA")
    try:
        bars,daily_sha=minute_get(symbol,day)
    except ValueError as e:
        if str(e).startswith("SOURCE_NOT_HISTORICALLY_AVAILABLE_HTTP_"):
            r["status"]="CENSORED_MISSING_MINUTE_ARCHIVE"
        elif str(e) in ("GAPPED_ARCHIVE_DAY","STAGE26_INCOMPLETE_216H_CONTIGUOUS_1M"):
            r["status"]="CENSORED_GAPPED_216H_MINUTE_ARCHIVE"
        else:
            raise
        r["source_censor_reason"]=str(e)[:170]
        return r
    if len(daily_sha)!=10 or any(len(x.get("sha256",""))!=64 for x in daily_sha):
        raise RuntimeError("STAGE32_DAILY_PUBLISHER_SHA_INVALID")
    ctrl=original.scan_continuous(symbol,day,bars)
    exp=scan_one_minute(symbol,day,bars)
    if ctrl["polls"]!=3360 or exp["polls"]!=10080:
        raise RuntimeError("STAGE32_FULL168H_POLL_COUNT_DIFFERENT")
    labels3=first_cross_class(day,bars,h,ctrl)
    labels1=first_cross_class(day,bars,h,exp)
    if any(labels3[str(k)+"x"]["is_gt_positive"]!=labels1[str(k)+"x"]["is_gt_positive"]
           for k in (2,5,10)):
        raise RuntimeError("STAGE32_DIFFERENT_GT_ON_SAME_PRICE_SOURCE")
    r.update({"status":"COMPLETE_BOTH_168H","monthly_GT_official_publisher_SHA256":h["archive_sha256"],
         "ten_daily_1m_publisher_sha256":daily_sha,
         "V4_original3m":ctrl,"V4_candidate1m":exp,
         "labels_original3m":labels3,"labels_candidate1m":labels1,
         "same_prices_and_thresholds":True,"actual_historical_fills":False})
    return r

def summarize(rows):
    cc=Counter(x["status"] for x in rows)
    full=[x for x in rows if x["status"]=="COMPLETE_BOTH_168H"]
    d={"total_attempted":len(rows),"source_statuses":dict(cc),
        "paired_valid":len(full),"baseline3m_watch":sum(x["V4_original3m"]["watch_count"] for x in full),
        "candidate1m_watch":sum(x["V4_candidate1m"]["watch_count"] for x in full),
        "baseline3m_D1":sum(x["V4_original3m"]["setups"] for x in full),
        "candidate1m_D1":sum(x["V4_candidate1m"]["setups"] for x in full),
        "baseline3m_polls":sum(x["V4_original3m"]["polls"] for x in full),
        "candidate1m_polls":sum(x["V4_candidate1m"]["polls"] for x in full)}
    for n in (2,5,10):
        keys=str(n)+"x"
        positive=[x for x in full if x["labels_original3m"][keys]["is_gt_positive"]]
        d[keys]={"gt_positive_count":len(positive)}
        for tag,path in (("3m","labels_original3m"),("1m","labels_candidate1m")):
            cls=Counter(x[path][keys]["classification"] for x in positive)
            d[keys][tag]={"early":cls["EARLY"],"late":cls["LATE"],"no_watch":cls["NO_WATCH"]}
    for tag,key in (("3m","V4_original3m"),("1m","V4_candidate1m")):
        for cost in (20,100):
            px=[x["proxy_"+str(cost)+"bps"] for row in full
                for x in row[key]["trade_proxies"]]
            good=[p["net_pct"] for p in px if p is not None and p["status"]=="PRICE_PROXY_ONLY"]
            d[tag+"_cost"+str(cost)]={"all_watch":len(px),"evaluable":len(good),
                "win":sum(x>0 for x in good),"lose":sum(x<0 for x in good),
                "skips_and_censored":len(px)-len(good),
                "median_net_pct":round(statistics.median(good),6) if good else None,
                "independent_30U_PnL":round(sum(v*.3 for v in good),6)}
    return d

def run(daystring,shard,original_zip,workers=2):
    c=frozen()
    if daystring not in NEW_DAYS or shard not in range(SHARDS):
        raise ValueError("STAGE32_NOT_FROZEN_DAY_OR_SHARD")
    if workers not in (1,2):raise ValueError("STAGE32_WORKER_LIMIT")
    symbols=inventory.original_universe(original_zip)
    chosen=[s for i,s in enumerate(symbols) if i%SHARDS==shard]
    if len(chosen) not in (126,127):raise ValueError("STAGE32_EXPECT_126_127_SOURCE_COINS")
    day=date.fromisoformat(daystring)
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(compare_one,s,day):s for s in chosen}
        for task in concurrent.futures.as_completed(futures):
            r=task.result()
            if r["symbol"]!=futures[task]:
                raise RuntimeError("STAGE32_RESULTS_SYMBOL_MISMATCH")
            results.append(r)
            if len(results)%25==0:print("STAGE32_PROGRESS "+json.dumps({
                "day":daystring,"shard":shard,"complete":len(results),
                "total":len(chosen)}),file=sys.stderr,flush=True)
    results.sort(key=lambda x:x["symbol"])
    counts=summarize(results)
    if any("NETWORK" in k or "INTEGRITY" in k for k in counts["source_statuses"]):
        raise RuntimeError("STAGE32_SOURCE_ERRORS_NOT_ACCEPTABLE")
    return {"schema":"MONSTER_STAGE32_PAIRED_FRESH_758_TWO_CADENCES_REAL_SOURCE_V1",
       "date":daystring,"shard":shard,"shards_total":SHARDS,
       "both_arms_original_production_V4":True,
       "full_frozen_universe_attempted":True,
       "official_minute_monthly_sha_verified":True,
       "results":results,"summary":counts,
       "reproduction_not_actual_trading":True,"other_ai_review":"NOT_DONE",
       "deploy":"NO_GO","mail":"OFF","trading":"NO_GO","frank":"UNCHANGED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--date",required=True)
    p.add_argument("--shard",type=int,required=True)
    p.add_argument("--original-758-zip",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    r=run(a.date,a.shard,a.original_758_zip)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE32_SHARD_SUMMARY "+json.dumps(r["summary"],sort_keys=True),flush=True)
if __name__=="__main__":main()
