#!/usr/bin/env python3
"""Real official 1m Stage101 D1 exits; original305 all retained, price-only."""
from __future__ import annotations
import argparse
import concurrent.futures
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path

try:
    import monster_v4_stage88_d1_24h72h_official_paths as old
except ImportError:
    from scripts import monster_v4_stage88_d1_24h72h_official_paths as old

SCHEMA="MONSTER_STAGE101_ALL305_D1_CAUSAL_REAL1M_EXIT_PRICE_PROXIES_V1"
SOURCE=old.E/"monster_stage88_all305_D1_post_signal_24h72h_price_paths.jsonl"
PIN="86e96b726f677a15f5a7c8d740e3caca5c83e3fc"
MIN=60000
STOP_LOSS=Decimal("0.85")
TRAIL_ARM=Decimal("1.25")
TRAIL_RETAIN=Decimal("0.80")
COMPLETE="COMPLETE_OFFICIAL_1M_SHA_PRICE_ONLY_PROXY"


def frozen():
    if old.sha_blob(SOURCE.read_bytes())!=PIN:
        raise ValueError("STAGE101_STAGE88_ALL305_GIT_BLOB_CHANGED")
    arr=[json.loads(s) for s in SOURCE.read_text().splitlines() if s.strip()]
    original,index=old.frozen()
    if len(arr)!=305 or len(original)!=305:
        raise ValueError("STAGE101_MISSING_ORIGINAL305")
    source={(x["date"],x["symbol"]):x for x in arr}
    if len(source)!=305 or set(source)!={(x["date"],x["symbol"]) for x in original}:
        raise ValueError("STAGE101_STAGE88_NO_LONGER_MATCHES_STAGE85")
    for item in original:
        x=source[(item["date"],item["symbol"])]
        if (x["D1_FIRST_UTC"]!=item["D1_FIRST_UTC"]
            or x["D0_FIRST_UTC"]!=item["D0_FIRST_UTC"]
            or x["D1_PATH"]!=item["D1_PATH"]
            or x["h24"]["status"]!=COMPLETE or x["h72"]["status"]!=COMPLETE):
            raise ValueError("STAGE101_ORIGINAL_TIMES_OR_SOURCE_CHANGED")
    return original,source


def fixed_bars_result(bars:list[tuple],entry:Decimal,minutes:int):
    if len(bars)<minutes:
        raise ValueError("STAGE101_TRUNCATED_FIXED_HORIZON")
    r=bars[minutes-1]
    return {
        "exit_bar_UTC":old.publisher.stamp(r[0]),
        "exit_price":str(r[4]),
        "gross_price_return_pct":old.pct(r[4],entry),
        "elapsed_minutes":minutes,
        "exit_bar_trade_count":r[6],
        "price_only_no_real_execution":True,
    }


def trailing_72h(bars:list[tuple],entry:Decimal):
    if len(bars)!=4320 or entry<=0:
        raise ValueError("STAGE101_MISSING_72H_PRICE")
    hard=entry*STOP_LOSS
    peak=entry
    armed=False
    result=None
    for idx,bar in enumerate(bars):
        t,o,h,l,c,q,n=bar
        if not (0<l<=min(o,c) and h>=max(o,c) and n>=0):
            raise ValueError("STAGE101_INVALID_OFFICIAL_OHLC")
        stop=max(hard,peak*TRAIL_RETAIN) if armed else hard
        # Stop derived only from completed earlier-minute bars, not this bar's HIGH.
        if o<=stop:
            result=(idx,bar,o,"BAR_OPEN_GAPPED_BELOW_STOP",armed,stop,peak)
            break
        if l<=stop:
            result=(idx,bar,stop,
                    "PRIOR_MINUTE_TRAIL_LOW_TOUCH" if armed and stop>hard
                    else "HARD15_LOW_TOUCH",armed,stop,peak)
            break
        # Updating high ONLY after stop checks prevents same-minute future lookahead.
        peak=max(peak,h)
        if peak>=entry*TRAIL_ARM:
            armed=True
    if result is None:
        bar=bars[-1]
        result=(len(bars)-1,bar,bar[4],"72H_TIMEOUT_CLOSE",armed,
                max(hard,peak*TRAIL_RETAIN) if armed else hard,peak)
    idx,bar,exit_price,why,was_armed,active_stop,known_peak=result
    return {
        "exit_reason":why,
        "exit_bar_UTC":old.publisher.stamp(bar[0]),
        "exit_price_price_only":str(exit_price),
        "gross_price_return_pct":old.pct(exit_price,entry),
        "minutes_from_entry":idx+1,
        "exit_bar_trade_count":bar[6],
        "trail_armed_before_exit":was_armed,
        "stop_known_before_exit_minute":str(active_stop),
        "peak_of_completed_minutes_before_or_at_exit":str(known_peak),
        "price_only_not_a_filled_stop":True,
    }


def one_case(asof:dict,archived:dict,*,reader=old.publisher.verified_1m_day):
    time=old.utc_ms(asof["D1_FIRST_UTC"])
    receipt_index={x["date"]:x["zip_sha256"] for x in
                   archived["source_days_verified"]}
    lookup={}
    received=[]
    for day in old.days_for(time):
        candles,receipt=reader(asof["symbol"],day)
        if len(candles)!=1440 or not receipt["verified_official_publisher_SHA256"]:
            raise ValueError("STAGE101_NOT_FULL_OFFICIAL_SHA_DAY")
        actual=receipt["zip_sha256"]
        if receipt["date"]!=day.isoformat() or receipt_index.get(day.isoformat())!=actual:
            raise ValueError("STAGE101_REAL_SOURCE_DOES_NOT_MATCH_STAGE88_SHA")
        received.append(receipt)
        for bar in candles:
            if bar[0] in lookup:raise ValueError("STAGE101_DUPLICATE_REAL_MINUTE")
            lookup[bar[0]]=bar
    entry_time=time+MIN
    actual=[lookup.get(entry_time+i*MIN) for i in range(4320)]
    if any(x is None for x in actual):
        raise ValueError("STAGE101_GAPPED_AFTER_D1_72H")
    entry=actual[0][1]
    if entry<=0 or entry!=Decimal(archived["entry_delayed_1m"]["entry_open"]):
        raise ValueError("STAGE101_NEXT_MINUTE_ENTRY_NOT_STAGE88")
    if actual[0][6]<=0 or actual[0][5]<=0:
        raise ValueError("STAGE101_ENTRY_WITHOUT_ACTUAL_TRADE")
    # Recalculate exactly the entire 24/72h stage88 price paths.
    t24=old.score_path(lookup,time,1440,entry)
    t72=old.score_path(lookup,time,4320,entry)
    for h,c in (("h24",t24),("h72",t72)):
        if c["status"]!=COMPLETE or c["fixed_exit_gross_return_pct"]!=archived[
            h]["fixed_exit_gross_return_pct"]:
            raise ValueError("STAGE101_ORIGINAL_STAGE88_FIXED_EXIT_CHANGED")
    return {
        "date":asof["date"],"symbol":asof["symbol"],
        "D0_FIRST_UTC":asof["D0_FIRST_UTC"],
        "D1_FIRST_UTC":asof["D1_FIRST_UTC"],
        "D1_PATH":asof["D1_PATH"],
        "identity":asof["identity"],
        "original_major_2x_early5_EVAL_ONLY":bool(asof[
             "early5_gt2_evaluation_only"]),
        "entry_UTC":old.publisher.stamp(entry_time),
        "entry_price_proxy":str(entry),
        "verified_official_publisher_1m_sha":received,
        "original_fixed_24h":fixed_bars_result(actual,entry,1440),
        "original_fixed_72h":fixed_bars_result(actual,entry,4320),
        "fixed_6h_price_exit":fixed_bars_result(actual,entry,360),
        "fixed_12h_price_exit":fixed_bars_result(actual,entry,720),
        "hard15_trail20_after25_72h":trailing_72h(actual,entry),
        "real_executable_pnl":"UNKNOWN",
        "no_live_order_email_deployment":True,
    }


def selftest():
    p=Decimal
    entry=p("100")
    start=old.utc_ms("2025-02-01T00:00:00Z")
    rows=[(start+i*MIN,entry,p("100"),p("100"),entry,p("100000"),300)
          for i in range(4320)]
    case=trailing_72h(rows,entry)
    assert case["exit_reason"]=="72H_TIMEOUT_CLOSE"
    assert case["gross_price_return_pct"]=="0"
    after=list(rows)
    after[0]=(start,entry,p("125"),p("100"),p("101"),p("100000"),300)
    after[1]=(start+MIN,p("101"),p("110"),p("99"),p("99"),p("100000"),300)
    q=trailing_72h(after,entry)
    assert q["exit_reason"]=="PRIOR_MINUTE_TRAIL_LOW_TOUCH"
    assert q["gross_price_return_pct"]=="0"
    # Stop first even if HIGH would arm trail within same candle.
    after[0]=(start,entry,p("200"),p("84"),p("101"),p("100000"),300)
    first=trailing_72h(after,entry)
    assert first["exit_reason"]=="HARD15_LOW_TOUCH"
    assert first["gross_price_return_pct"]=="-15.00"
    # Opening gap must not claim the better stop price.
    after[0]=(start,p("80"),p("100"),p("79"),p("80"),p("100000"),300)
    gap=trailing_72h(after,entry)
    assert gap["exit_reason"]=="BAR_OPEN_GAPPED_BELOW_STOP"
    assert gap["gross_price_return_pct"]=="-20.0"
    print("STAGE101_PRICE_ONLY_STOP_FIRST_PREVIOUS_MINUTE_TRAIL_GAP_AND_72H_SELFTEST_PASS")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--selftest",action="store_true")
    parser.add_argument("--date")
    parser.add_argument("--shard",type=int)
    parser.add_argument("--out",type=Path)
    parser.add_argument("--workers",type=int,default=3)
    args=parser.parse_args()
    if args.selftest:selftest();return
    if not args.date or args.shard is None or not args.out:
        parser.error("--date --shard --out required")
    if args.workers not in range(1,5):
        raise ValueError("STAGE101_WORKER_LIMIT")
    allx,arch=frozen()
    cases=old.shard_rows(args.date,args.shard,allx)
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(one_case,x,arch[(x["date"],x["symbol"])]):x
                 for x in cases}
        for future in concurrent.futures.as_completed(futures):
            x=futures[future]
            try:
                item=future.result()
            except Exception as exc:
                raise RuntimeError("STAGE101_CASE_FAIL_CLOSED "+x["symbol"]+" "+
                    type(exc).__name__+":"+str(exc)) from exc
            results.append(item)
            print("STAGE101_VERIFIED "+x["date"]+" "+x["symbol"]+" "+item[
                 "hard15_trail20_after25_72h"]["exit_reason"],flush=True)
    if len(results)!=len(cases):
        raise ValueError("STAGE101_COHORT_LOSS")
    out={
        "schema":SCHEMA,"date":args.date,"shard":args.shard,
        "original_case_count":len(cases),
        "real_official_SHA_verified_source":"ALL",
        "stage88_source_blob":PIN,"rows":sorted(results,key=lambda x:x["symbol"]),
        "price_proxy_only":True,"other_ai_review":"NOT_DONE",
        "monster_deployment":"NO_GO","gmail":"OFF","autotrade":"NO_GO"}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE101_ORIGINAL_COHORT_SHARD_COMPLETE "+json.dumps({
        "date":args.date,"shard":args.shard,"n":len(cases)},sort_keys=True))


if __name__=="__main__":
    main()
