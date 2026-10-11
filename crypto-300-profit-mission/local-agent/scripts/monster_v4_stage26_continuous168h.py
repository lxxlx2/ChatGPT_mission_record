#!/usr/bin/env python3
"""Stage26: original production V4 continuous 168h, original 758 x six.

Retrospective already exposed dates; not a new holdout. Every archived label
candidate is attempted, not just known winners. Full 168h single SQLite state
per symbol, official Binance publisher-checksummed 10 daily Spot 1m archives.
The full-market global queue capacity, historical listings/L2 and real fills
are NOT reproduced by independent per-symbol databases.
"""
import argparse
import bisect
import concurrent.futures
import hashlib
import json
import statistics
import sys
import tempfile
import urllib.error
from collections import Counter
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_archive_universe_replay as archive
    import monster_v4_historical_replay as replay
    import monster_v4_stage24_aggregate as previous
    import monster_v4_shadow as live
except ImportError:
    from scripts import monster_v4_archive_universe_replay as archive
    from scripts import monster_v4_historical_replay as replay
    from scripts import monster_v4_stage24_aggregate as previous
    from scripts import monster_v4_shadow as live

EVIDENCE=previous.EVIDENCE
PREREG=EVIDENCE/"monster_stage26_full168h_original_v4_continuous_758x6_prereg_20261011.json"
DAY_INDEX=EVIDENCE/"monster_stage24_6date_original_zip_shas_and_results_20261011.json"
DAY_ANCHOR_HOUR_UTC=6
SHARDS=6
EXPECTED_MINUTES=216*60
WARMUP_MINUTES=24*60
ACTIVE_MINUTES=168*60
HOLD_EXIT_MINUTES=24*60

def git_sha(path):
    data=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def frozen():
    m=json.loads(PREREG.read_text(encoding="utf-8"))
    if m.get("schema")!="MONSTER_STAGE26_SIX_FIXED_DATES_FULL_168H_PER_SYMBOL_CONTINUOUS_V4_RETROSPECTIVE_V1":
        raise ValueError("STAGE26_NOT_FROZEN")
    from_repo={
      "v4_production_functions":live.__file__,
      "v4_replayer_and_cost":replay.__file__,
      "official_spot_archive_parser":archive.source.__file__,
      "prior_stage24_verified_sha_aggregator":previous.__file__}
    for key,source in from_repo.items():
        if git_sha(source)!=m["original_blob_sha1"][key]:
            raise ValueError("STAGE26_ORIGINAL_PRODUCTION_CODE_DRIFT:"+key)
    dates=["2025-11-04","2025-12-04","2026-02-04",
           "2026-04-04","2026-08-04","2026-09-04"]
    if m["frozen_dates_utc"]!=dates:
        raise ValueError("STAGE26_CALENDAR_CHANGED")
    if m["source_contract"]["first_poll"]!="06:03:00 UTC relative to frozen date 06:00 start, 3m poll at closed minute with same 24h-start initialization as Stage24 baseline":
        raise ValueError("STAGE26_FIRST_POLL_CHANGED")
    return m

def load_frozen_day_artifact(source_zip,day):
    cfg=frozen()
    if day not in cfg["frozen_dates_utc"]:
        raise ValueError("STAGE26_UNREGISTERED_DATE")
    register=json.loads(DAY_INDEX.read_text(encoding="utf-8"))
    original={x["date"]:x for x in register["artifacts"]}
    if set(original)!=set(cfg["frozen_dates_utc"]):
        raise ValueError("STAGE26_STAGE24_DAY_INVENTORY_DRIFT")
    artifact=previous.open_artifact(source_zip,original[day])
    if len(artifact["cases"])!=758 or len({r["symbol"] for r in artifact["cases"]})!=758:
        raise ValueError("STAGE26_INCOMPLETE_ALL_MARKET_INDEX")
    return artifact

def read_complete_216h(symbol,day,download=archive.get_day):
    """Strictly 10 official day ZIP + CHECKSUM, 12960 consecutive 1m bars.

    End includes 24h price-exit support after seven-day scan. No hourly
    ground-truth price is ever used by the scanner.
    """
    start=datetime(day.year,day.month,day.day,6,tzinfo=timezone.utc)-timedelta(hours=24)
    begin=int(start.timestamp()*1000)
    daily=[day+timedelta(days=i) for i in range(-1,9)]
    raw=[];proof=[]
    for day_ in daily:
        a,p=download(symbol,day_)
        if not isinstance(a,list) or len(a)!=1440:
            raise ValueError("STAGE26_INVALID_DAY_ROWS")
        if not isinstance(p,dict) or len(p.get("sha256",""))!=64 or p.get("verified_published_sha256") is not True:
            raise ValueError("STAGE26_UNVERIFIED_PUBLISHER_SHA")
        raw.extend(a)
        proof.append({"date":day_.isoformat(),"sha256":p["sha256"]})
    left=next((i for i,r in enumerate(raw) if r[0]==begin),None)
    if left is None:raise ValueError("STAGE26_MISSING_PRECISE_WARMUP_START")
    bars=raw[left:left+EXPECTED_MINUTES]
    if len(bars)!=EXPECTED_MINUTES or any(r[0]!=begin+i*60_000 for i,r in enumerate(bars)):
        raise ValueError("STAGE26_INCOMPLETE_216H_CONTIGUOUS_1M")
    return bars,proof

def scan_continuous(symbol,day,bars):
    """One SQLite store; exactly original V4 functions, never per-day reset."""
    anchor=replay.parse_ms(day.isoformat()+"T06:00:00Z")
    base=anchor-WARMUP_MINUTES*60_000
    if len(bars)!=EXPECTED_MINUTES or bars[0][0]!=base:
        raise ValueError("STAGE26_BAD_216H_START_OR_COUNT")
    if any(x[0]!=base+i*60_000 for i,x in enumerate(bars)):
        raise ValueError("STAGE26_NONCONTIGUOUS_MINUTE_DATA")
    prefix=[Decimal(0)]
    for bar in bars:
        prefix.append(prefix[-1]+bar[5])
    candles=replay.make_closed_five_minute_bars(bars)
    ends=[int(c[6]) for c in candles]
    first=WARMUP_MINUTES+2
    stop=WARMUP_MINUTES+ACTIVE_MINUTES
    no_traded=0;polls=0
    with tempfile.TemporaryDirectory(prefix="monster_stage26_continuous_") as temp:
        db=live.open_store(Path(temp)/"original.sqlite")
        try:
            def closed_5m(_venue,_symbol,now_ms):
                n=bisect.bisect_left(ends,now_ms)
                return candles[max(0,n-8):n]
            for i in range(first,stop,3):
                observed=bars[i][0]+60_000
                if bars[i][6]==0 or bars[i][5]==0:
                    no_traded+=1
                quote=prefix[i+1]-prefix[i+1-replay.ROLLING_24H_BARS]
                live.observe_snapshot(db,"spot",observed,[{
                   "symbol":symbol,"lastPrice":str(bars[i][4]),
                   "quoteVolume":str(quote)}])
                live.process_queue(db,observed,closed_5m)
                polls+=1
            # The trailing D1 queue may need a few more closed-5m bars without
            # changing any WATCH exposure after the 168h observation window.
            for extra in range(1,8):
                observed=anchor+ACTIVE_MINUTES*60_000+extra*180000
                live.process_queue(db,observed,closed_5m)
            raw=[dict(r) for r in db.execute(
                "SELECT event_id,event_type,observed_ms,payload FROM events ORDER BY observed_ms,event_id")]
            watches=[r for r in raw if r["event_type"]=="WATCH_EARLY"]
            setups=[r for r in raw if r["event_type"]=="SETUP_ACTIVE"]
            invalids=[r for r in raw if r["event_type"]=="INVALIDATED"]
            queue_status={r["status"]:r["n"] for r in db.execute(
                "SELECT status,COUNT(*) AS n FROM candidate_queue GROUP BY status")}
        finally:
            db.close()
    first_watch=watches[0]["observed_ms"] if watches else None
    trades=[];capital_free=0
    for w in watches:
        enter=w["observed_ms"]+180_000
        overlap=enter<capital_free
        if overlap:
            record={"status":"SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED"}
        else:
            record=replay._proxy_trade(bars,base,w["observed_ms"],180000,20)
            capital_free=enter+24*3600_000
        cost_stress=(None if overlap else replay._proxy_trade(
            bars,base,w["observed_ms"],180000,100))
        trades.append({"watch_utc":replay.utc(w["observed_ms"]),
            "proxy_20bps":record,"proxy_100bps":cost_stress})
    return {"watch_count":len(watches),"setups":len(setups),
        "invalidations":len(invalids),"polls":polls,"zero_trade_minute_polls":no_traded,
        "watch_utcs":[replay.utc(x["observed_ms"]) for x in watches],
        "setup_utcs":[replay.utc(x["observed_ms"]) for x in setups],
        "queue_final_status":queue_status,
        "trade_proxies":trades,
        "continuous_sqlite_reset_count":0,
        "scope":"PER_SYMBOL_PERSISTENT_168H_NO_CROSS_SYMBOL_GLOBAL_QUEUE_LIMIT"}

def first_real_1m_cross(day,bars,base_open,multiple):
    anchor=replay.parse_ms(day.isoformat()+"T06:00:00Z")
    threshold=Decimal(str(base_open))*Decimal(multiple)
    from_i=WARMUP_MINUTES
    for bar in bars[from_i:from_i+ACTIVE_MINUTES]:
        if bar[2]>=threshold:
            return bar[0]
    return None

def evaluate_one(item,day,minute_source=read_complete_216h,
                 engine=scan_continuous):
    symbol=item["symbol"]
    hourly=item["hourly"]
    if hourly["status"]!="VERIFIED_COMPLETE_168H":
        return {"symbol":symbol,"date":day.isoformat(),
                "status":"CENSORED_GT_NOT_COMPLETE_168H",
                "hourly_status":hourly["status"],
                "truth_missing_is_not_no_watch":True}
    try:
        bars,proof=minute_source(symbol,day)
        result=engine(symbol,day,bars)
        labels={}
        for m in (2,5,10):
            gt=hourly["gross_high_ge_"+str(m)+"x"]
            cross=first_real_1m_cross(day,bars,hourly["baseline_1h_open"],m)
            if bool(cross is not None)!=bool(gt):
                raise ValueError("STAGE26_OFFICIAL_GT_HIGH_VS_VERIFIED_1M_CROSS_DISAGREE")
            first_watch=(replay.parse_ms(result["watch_utcs"][0])
                         if result["watch_utcs"] else None)
            if not gt:
                cls="NO_FUTURE_GROSS_"+str(m)+"X"
            elif first_watch is None:
                cls="NO_WATCH_IN_CONTINUOUS_168H"
            elif first_watch<=cross:
                cls="WATCH_BEFORE_OR_AT_REAL_FIRST_1M_CROSS"
            else:
                cls="WATCH_AFTER_REAL_FIRST_1M_CROSS"
            labels[str(m)+"x"]={"gross_hourly_high_gt":gt,
                "real_1m_cross_utc":replay.utc(cross) if cross is not None else None,
                "first_v4_watch_utc":result["watch_utcs"][0] if result["watch_utcs"] else None,
                "classification":cls,
                "lead_minutes":round((cross-first_watch)/60000,3)
                    if cross is not None and first_watch is not None else None}
        return {"symbol":symbol,"date":day.isoformat(),
             "status":"COMPLETE_168H_CONTINUOUS_V4",
             "official_source_SHA256_days":proof,
             "original_GT_high_multiples":hourly["maximum_high_multiple"],
             "hourly_status":hourly["status"],
             "labels":labels,"continuous":result,
             "historical_execution_proven":False}
    except ValueError as exc:
        reason=str(exc)
        if reason.startswith("SOURCE_NOT_HISTORICALLY_AVAILABLE_HTTP_"):
            state="CENSORED_MISSING_MINUTE_ARCHIVE"
        elif reason in ("GAPPED_ARCHIVE_DAY","STAGE26_INCOMPLETE_216H_CONTIGUOUS_1M"):
            state="CENSORED_GAPPED_216H_MINUTE_ARCHIVE"
        else:
            state="SOURCE_INTEGRITY_REJECTED"
        return {"symbol":symbol,"date":day.isoformat(),
              "status":state,"error":reason[:180],"truth_missing_is_not_no_watch":True}
    except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,OSError,ConnectionError) as exc:
        return {"symbol":symbol,"date":day.isoformat(),
            "status":"SOURCE_NETWORK_FAILURE","error":str(exc)[:180],
            "truth_missing_is_not_no_watch":True}

def summarize(rows):
    statuses=Counter(x["status"] for x in rows)
    valid=[r for r in rows if r["status"]=="COMPLETE_168H_CONTINUOUS_V4"]
    gt={}
    for m in (2,5,10):
        good=[x for x in valid if x["labels"][str(m)+"x"]["gross_hourly_high_gt"]]
        classes=Counter(x["labels"][str(m)+"x"]["classification"] for x in good)
        gt[str(m)+"x"]={"joint_verified_event_count":len(good),
          "classifications":dict(classes),
          "early":classes["WATCH_BEFORE_OR_AT_REAL_FIRST_1M_CROSS"],
          "late":classes["WATCH_AFTER_REAL_FIRST_1M_CROSS"],
          "no_watch":classes["NO_WATCH_IN_CONTINUOUS_168H"],
          "missing_minutely_for_verified_GT":sum(
            r["status"] not in ("CENSORED_GT_NOT_COMPLETE_168H","COMPLETE_168H_CONTINUOUS_V4")
            and r.get("hourly_status")=="VERIFIED_COMPLETE_168H" for r in rows)}
    all_proxies=[x["proxy_20bps"] for r in valid for x in r["continuous"]["trade_proxies"]]
    pnl=[x["net_pct"] for x in all_proxies if x["status"]=="PRICE_PROXY_ONLY"]
    alerted=[r for r in valid if r["continuous"]["watch_count"]>0]
    return {"attempted":len(rows),"statuses":dict(statuses),
       "gt_verifiable_but_no_full_minute_source":sum(
            x["status"] not in ("CENSORED_GT_NOT_COMPLETE_168H","COMPLETE_168H_CONTINUOUS_V4")
            for x in rows),
       "joint_complete":len(valid),
       "watch_episodes":sum(r["continuous"]["watch_count"] for r in valid),
       "watch_symbol_dates":len(alerted),
       "setups":sum(r["continuous"]["setups"] for r in valid),
       "polls":sum(r["continuous"]["polls"] for r in valid),
       "zero_trade_proxy_polls":sum(r["continuous"]["zero_trade_minute_polls"] for r in valid),
       "gt_multiple_outcomes":gt,
       "original_v4_24h_price_proxy":{"selected":len(all_proxies),
           "evaluable":len(pnl),"wins":sum(x>0 for x in pnl),
           "losses":sum(x<0 for x in pnl),
           "censored":len(all_proxies)-len(pnl),
           "median_net_pct":round(statistics.median(pnl),6) if pnl else None,
           "sum_assumed_independent_30USDT_pnl":round(sum(x*.3 for x in pnl),6)},
       "not_real_fill":True}

def run_shard(day_string,shard,source_zip,workers=2,evaluator=evaluate_one):
    cfg=frozen()
    if day_string not in cfg["frozen_dates_utc"] or not 0<=shard<SHARDS:
        raise ValueError("STAGE26_DATE_OR_SHARD_INVALID")
    if not 1<=workers<=3:raise ValueError("STAGE26_TOO_MANY_SOURCE_THREADS")
    report=load_frozen_day_artifact(source_zip,day_string)
    source=sorted(report["cases"],key=lambda x:x["symbol"])
    included=[x for i,x in enumerate(source) if i%SHARDS==shard]
    if len(included) not in (126,127):
        raise ValueError("STAGE26_SHARD_SIZE_MISMATCH")
    day=date.fromisoformat(day_string)
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        submitted={pool.submit(evaluator,row,day):row["symbol"] for row in included}
        for future in concurrent.futures.as_completed(submitted):
            result=future.result()
            if result["symbol"]!=submitted[future]:
                raise ValueError("STAGE26_WORKER_SYMBOL_DRIFT")
            rows.append(result)
            if len(rows)%20==0:
                print("STAGE26_PROGRESS "+json.dumps({
                   "day":day_string,"shard":shard,"finished":len(rows),
                   "target":len(included),
                   "complete":sum(x["status"]=="COMPLETE_168H_CONTINUOUS_V4" for x in rows)}),
                   file=sys.stderr,flush=True)
    rows.sort(key=lambda x:x["symbol"])
    return {"schema":"MONSTER_STAGE26_FULL168H_758_6DATE_PER_SYMBOL_CONTINUOUS_V4_V1",
       "date":day_string,"shard":shard,"shards_total":SHARDS,
       "all_universe_attempted_across_shards":True,
       "research_retrospective_dates_exposed":True,
       "source":"BINANCE_OFFICIAL_CHECKSUM_VERIFIED_10_DAILY_1M_SPOT_PER_COMPLETE_GT",
       "original_v4_production_functions_unchanged":True,
       "per_symbol_sqlite_resets_during_168h":0,
       "global_queue_capacity_modeled":False,
       "summary":summarize(rows),"cases":rows,
       "independent_other_ai_review":"NOT_DONE","deployment":"NO_GO",
       "frank":"UNCHANGED","real_gmail":"OFF","trading":"NO_GO"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--date",required=True)
    p.add_argument("--shard",required=True,type=int)
    p.add_argument("--stage24-original-zip",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    result=run_shard(args.date,args.shard,args.stage24_original_zip)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE26_RESULT_JSON "+json.dumps(result["summary"],sort_keys=True),flush=True)
    if any(("NETWORK_FAILURE" in s or "INTEGRITY_REJECTED" in s)
           for s in result["summary"]["statuses"]):
        raise SystemExit("STAGE26_SOURCE_FAIL_CLOSED")
if __name__=="__main__":
    main()
