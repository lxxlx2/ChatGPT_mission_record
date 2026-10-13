#!/usr/bin/env python3
"""Stage110: causal, historical, official Binance 1m D1 confirmation model.
Read-only; NEVER a live monitor, email, trade, or Mac launch agent.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
try:
    import monster_v4_stage101_exit_minute_backtest as stage101
except ImportError:
    from scripts import monster_v4_stage101_exit_minute_backtest as stage101

old=stage101.old
MIN=60000
SCHEMA="MONSTER_STAGE110_REAL1M_CAUSAL_POST_D1_CONTINUOUS_CONFIRM_V1"
PIN101="19dfc89ab10aaf23f068bee924cddc85d5bcc3e1"
DIRECT="DIRECT_AT_FIRST_D0"
REIGNITION="REIGNITION_AFTER_D0"

def frozen():
    p=old.E/"monster_stage101_all305_real1m_historic_exit_paths.jsonl"
    if old.sha_blob(p.read_bytes())!=PIN101:
        raise ValueError("STAGE110_PRIOR_ALL305_BLOB_CHANGED")
    previous=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    source,archived=stage101.frozen()
    bykey={(x["date"],x["symbol"]):x for x in previous}
    census_path=old.SOURCE83
    if old.sha_blob(census_path.read_bytes())!=old.PIN83:
        raise ValueError("STAGE110_FULL_D0_519_SOURCE_CHANGED")
    census=[json.loads(x) for x in census_path.read_text().splitlines() if x.strip()]
    bycensus={(x["date"],x["symbol"]):x for x in census}
    if (len(source)!=305 or len(previous)!=305 or len(bykey)!=305
        or len(census)!=519 or len(bycensus)!=519
        or sum(x["D0_at_least_5m_before_2x"] for x in census)!=28
        or set(bykey)!={(x["date"],x["symbol"]) for x in source}):
        raise ValueError("STAGE110_FULL519_305_COHORT_MISMATCH")
    for x in source:
        k=x["date"],x["symbol"]
        if (bykey[k]["D1_FIRST_UTC"]!=x["D1_FIRST_UTC"]
            or bykey[k]["D1_PATH"]!=x["D1_PATH"]
            or bycensus[k]["D1_FIRST_UTC"]!=x["D1_FIRST_UTC"]
            or bykey[k]["original_fixed_24h"]["gross_price_return_pct"]
               !=archived[k]["h24"]["fixed_exit_gross_return_pct"]):
            raise ValueError("STAGE110_ORIGINAL_D1_OR_PRIOR_PRICE_DRIFT")
    return source,archived,bykey,bycensus,census

def decision(path,close,quote15,bars):
    """bars start one completed minute after frozen D1 bar (t+1m).
    Decision on bar K only visible at t+(K+1)m. Never use HIGH as outcome.
    """
    if path not in (DIRECT,REIGNITION) or len(bars)<30:
        raise ValueError("STAGE110_UNKNOWN_PATH_OR_MISSING_30M")
    close=Decimal(close)
    quote15=Decimal(quote15)
    if close<=0 or quote15<=0:
        raise ValueError("STAGE110_INVALID_PRE_D1_BASELINE")
    normal3=quote15/5
    preceding=None
    for i in range(30):
        candle=bars[i]
        if candle is None or len(candle)!=7 or not (
            candle[1]>0 and candle[4]>0 and candle[5]>=0 and candle[6]>=0):
            raise ValueError("STAGE110_MISSING_OR_BAD_ONE_MINUTE_BAR")
        k=i+1
        if candle[4]<=close*Decimal("0.92"):
            return {"state":"INVALIDATED_EARLY_8PCT","k":k,
                    "reason":"CLOSED_MINUTE_PRICE_LE92PCT"}
        if k%3:continue
        block=bars[k-3:k]
        quote=sum((x[5] for x in block),Decimal(0))
        trades=sum(x[6] for x in block)
        blockclose=block[-1][4]
        match=False
        if path==REIGNITION:
            match=(quote>=normal3*Decimal("1.20") and
                   trades>0 and blockclose>=close*Decimal("1.01"))
        elif preceding is not None:
            match=(quote>=normal3 and preceding["quote"]>=normal3
                   and trades>0 and preceding["trades"]>0
                   and blockclose>=preceding["close"]
                   and blockclose>=close*Decimal("1.02"))
        if match:
            return {"state":"PRIORITY_CONFIRMED","k":k,
                    "reason":"DIRECT_TWO_CLOSED_3M_BLOCKS" if path==DIRECT
                             else "REIGNITION_ONE_CLOSED_3M_BLOCK",
                    "last3_quote":str(quote),"baseline3_quote":str(normal3)}
        preceding={"quote":quote,"trades":trades,"close":blockclose}
    return {"state":"EXPIRED_NO_CONTINUOUS_CONFIRM","k":30,
            "reason":"NO_ASOF_CONFIRM_WITHIN_30_FULL_MINUTES"}

def replay(x,archive,previous,census,reader=old.publisher.verified_1m_day):
    t=old.utc_ms(x["D1_FIRST_UTC"])
    original={d["date"]:d["zip_sha256"] for d in
              previous["verified_official_publisher_1m_sha"]}
    expected={d["date"]:d["zip_sha256"] for d in archive["source_days_verified"]}
    if original!=expected:
        raise ValueError("STAGE110_ORIGINAL_PUBLISHER_SHA_RECEIPTS_DRIFT")
    lookup={}
    proofs=[]
    for day in old.days_for(t):
        candles,receipt=reader(x["symbol"],day)
        if (len(candles)!=1440 or not receipt["verified_official_publisher_SHA256"]
            or receipt["date"]!=day.isoformat()
            or receipt["zip_sha256"]!=original.get(day.isoformat())):
            raise ValueError("STAGE110_OFFICIAL_DAILY_SHA_MISSING_OR_CHANGED")
        proofs.append(receipt)
        for bar in candles:
            if bar[0] in lookup:raise ValueError("STAGE110_DUPLICATE_REAL_MINUTE")
            lookup[bar[0]]=bar
    first=lookup.get(t)
    if first is None or first[4]!=Decimal(x["asof_D1_last_closed_price"]):
        raise ValueError("STAGE110_D1_REAL_CLOSE_NOT_FROZEN_ASOF")
    future=[lookup.get(t+i*MIN) for i in range(1,1471)]
    if any(bar is None for bar in future):
        raise ValueError("STAGE110_CAUSAL_OR_24H_PRICE_SOURCE_GAP")
    outcome=decision(x["D1_PATH"],first[4],
                     x["asof_D1_quote15_USDT"],future[:30])
    k=outcome["k"]
    if future[k-1][0]!=t+k*MIN:
        raise ValueError("STAGE110_BAR_CLOCK_INCONSISTENT")
    visible=t+(k+1)*MIN
    confirmed=outcome["state"]=="PRIORITY_CONFIRMED"
    first_gt2=census["true_first_2x_HIGH_UTC_EVALUATION_ONLY"]
    early2=(confirmed and first_gt2 is not None
            and old.utc_ms(first_gt2)-visible>=5*MIN)
    trade=None
    status=outcome["state"]
    if confirmed:
        entry=lookup[visible]
        exitbar=lookup[visible+1439*MIN]
        if (entry[6]<=0 or entry[5]<=0 or exitbar[6]<=0):
            status="CONFIRMED_BUT_NO_TRADE_BAR"
        else:
            pct=old.pct(exitbar[4],entry[1])
            gross=Decimal(pct)/100
            fees={}
            for f in (Decimal("0.002"),Decimal("0.01")):
                fees[str(int(f*10000))+"bps_each_side_pct"]=str(
                    ((1+gross)*(1-f)/(1+f)-1)*100)
            trade={"next1m_open_UTC":old.publisher.stamp(visible),
                   "next1m_open":str(entry[1]),
                   "24h_last_bar_close_UTC":old.publisher.stamp(visible+1440*MIN),
                   "24h_exit_close":str(exitbar[4]),
                   "gross_pct":pct,"fee_sensitivity_only":fees,
                   "actual_bid_ask_notional_slippage_and_net":"UNKNOWN"}
    return {
        "date":x["date"],"symbol":x["symbol"],"identity":x["identity"],
        "D0_FIRST_UTC":x["D0_FIRST_UTC"],
        "D1_FIRST_UTC":x["D1_FIRST_UTC"],"D1_PATH":x["D1_PATH"],
        "state":status,"decision":outcome,
        "decision_visible_UTC":old.publisher.stamp(visible),
        "original_D0_early5_2x":census["D0_at_least_5m_before_2x"],
        "original_D1_early5_2x":census["D1_at_least_5m_before_2x"],
        "first_2x_HIGH_EVALUATION_ONLY":first_gt2,
        "new_priority_early5_2x":bool(early2),
        "confirmed_next_open_to_24h_close":trade,
        "old_D1_h24_gross_pct_EVAL_ONLY":previous["original_fixed_24h"]["gross_price_return_pct"],
        "source_days_real_official_sha":proofs,
        "real_executable_net_pnl":"UNKNOWN"}

def selftest():
    t=old.utc_ms("2025-02-01T00:00:00Z")
    D=Decimal
    def rows(closes,vol=D("150")):
        return [(t+i*MIN,D("100"),D("103"),D("90"),D(str(closes[i])),vol,2)
                for i in range(len(closes))]
    normal=[D("100")]*30
    directed=rows(normal)
    directed[5]=(directed[5][0],D("100"),D("103"),D("90"),D("103"),D("150"),2)
    result=decision(DIRECT,D("100"),D("1000"),directed)
    assert result["state"]=="PRIORITY_CONFIRMED" and result["k"]==6
    ignited=rows(normal,vol=D("100"))
    ignited[2]=(ignited[2][0],D("100"),D("103"),D("90"),D("102"),D("100"),2)
    result=decision(REIGNITION,D("100"),D("1000"),ignited)
    assert result["state"]=="PRIORITY_CONFIRMED" and result["k"]==3
    ignited[0]=(ignited[0][0],D("100"),D("103"),D("90"),D("92"),D("100"),2)
    assert decision(REIGNITION,D("100"),D("1000"),ignited)["state"]=="INVALIDATED_EARLY_8PCT"
    assert decision(DIRECT,D("100"),D("1000"),rows(normal,vol=D(0)))["state"]=="EXPIRED_NO_CONTINUOUS_CONFIRM"
    assert decision(DIRECT,D("100"),D("1000"),directed+rows([999]*100))==decision(
        DIRECT,D("100"),D("1000"),directed)
    print("STAGE110_FROZEN_DIRECT_REIGNITION_CAUSAL_CONFIRM_INVALIDATE_EXPIRE_FUTURE_INVARIANCE_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest",action="store_true")
    ap.add_argument("--date")
    ap.add_argument("--shard",type=int)
    ap.add_argument("--workers",type=int,default=3)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    if args.selftest:selftest();return
    if not args.date or args.shard is None or not args.out:
        ap.error("--date --shard --out required")
    if args.workers not in range(1,5):raise ValueError("STAGE110_WORKERS_LIMIT")
    population,archives,prev,census,full=frozen()
    group=old.shard_rows(args.date,args.shard,population)
    output=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs={pool.submit(replay,x,archives[(x["date"],x["symbol"])],
                          prev[(x["date"],x["symbol"])],
                          census[(x["date"],x["symbol"])]):x for x in group}
        for job in concurrent.futures.as_completed(jobs):
            x=jobs[job]
            try: y=job.result()
            except Exception as err:
                raise RuntimeError("STAGE110_SOURCE_CASE_FAILED "+
                    x["symbol"]+" "+str(err)) from err
            output.append(y)
            print("STAGE110_SHA_VERIFIED "+x["date"]+" "+x["symbol"]+" "+y["state"],flush=True)
    if len(output)!=len(group):raise ValueError("STAGE110_SHARD_ROW_LOSS")
    result={"schema":SCHEMA,"date":args.date,"shard":args.shard,
            "initial_D0_preserved":519,"initial_D1_preserved":305,
            "Stage101_Git_blob_PIN":PIN101,"Stage83_Git_blob_PIN":old.PIN83,
            "rows":sorted(output,key=lambda y:y["symbol"]),
            "research_not_OOS_or_deployment":True}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE110_SHARD_COMPLETE "+json.dumps({"date":args.date,"shard":args.shard,
         "n":len(output),"states":dict(Counter(y["state"] for y in output))},sort_keys=True))

if __name__=="__main__":
    main()
