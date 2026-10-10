#!/usr/bin/env python3
"""Time-causal V4 D0/D1 replay of genuine official partial listing histories.

Deduplicate overlapping Binance REST pages by exact 1m timestamp+content.
No padding of missing pre-listing history, no fake 24h volumes, no fills.
This output is a SEPARATE short-history exploratory stratum, not added to
the fully pre-warmed sample as if independent apples-to-apples validation.
"""
import json
import sqlite3
import statistics
import tempfile
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_historical_replay as full
    import monster_v4_shadow as live
except ImportError:
    from scripts import monster_v4_historical_replay as full
    from scripts import monster_v4_shadow as live

EVIDENCE=full.EVIDENCE


def normalize_partial(path):
    src=json.loads(Path(path).read_text(encoding="utf-8"))
    if src.get("schema")!="MONSTER_V4_1M_REPLAY_BAR_V1":
        raise ValueError("UNKNOWN_SOURCE_SCHEMA")
    if src.get("data_integrity")!="INCOMPLETE":
        raise ValueError("NOT_A_SHORT_HISTORY_CASE")
    unique={}
    duplicates=0
    for item in src["bars"]:
        if len(item)!=7:
            raise ValueError("INVALID_SOURCE_RECORD")
        t=int(item[0])
        values=(t,*map(full.dec,item[1:6]),int(item[6]))
        if values[5]<0 or values[6]<0:
            raise ValueError("NEGATIVE_VOLUME")
        if min(values[1:5])<=0 or values[3]>min(values[1],values[4]) or values[2]<max(values[1],values[4]):
            raise ValueError("BAD_OHLC")
        if t in unique:
            duplicates+=1
            if unique[t]!=values:
                raise ValueError("CONFLICTING_OVERLAPPING_SOURCE_PAGES")
        unique[t]=values
    bars=sorted(unique.values())
    if len(bars)<30:
        raise ValueError("INSUFFICIENT_PARTIAL_1M_BARS")
    if any(bars[i][0]-bars[i-1][0]!=60_000 for i in range(1,len(bars))):
        raise ValueError("GAPPED_PARTIAL_1M_BARS")
    original_first=src["first_bar_open_ms"]
    if bars[0][0]<=original_first:
        raise ValueError("PARTIAL_SOURCE_START_NOT_AFTER_REQUESTED")
    return src,bars,duplicates


def only_closed_5m(bars):
    buckets=defaultdict(list)
    for bar in bars:
        buckets[(bar[0]//300_000)*300_000].append(bar)
    result=[]
    for t in sorted(buckets):
        b=buckets[t]
        if len(b)!=5 or any(x[0]!=t+60000*i for i,x in enumerate(b)):
            continue
        result.append([
            t,str(b[0][1]),str(max(x[2] for x in b)),
            str(min(x[3] for x in b)),str(b[-1][4]),"0",
            t+300_000-1,str(sum((x[5] for x in b),Decimal(0)))])
    return result


def replay_partial(src,bars,duplicates=0):
    anchor=full.parse_ms(src["old_watch_utc"])
    first=bars[0][0]
    if first>=anchor+6*3600_000:
        raise ValueError("NO_BARS_IN_OBSERVATION_WINDOW")
    prefix=[Decimal(0)]
    for row in bars:
        prefix.append(prefix[-1]+row[5])
    candles=only_closed_5m(bars)
    with tempfile.TemporaryDirectory(prefix="monster_v4_short_history_") as td:
        db=live.open_store(Path(td)/"replay.sqlite")
        try:
            last=None
            polls=0
            no_trade=0
            def fetch_closed(_venue,_symbol,now_ms):
                return [b for b in candles if b[0]+300_000<=now_ms][-8:]
            for i,row in enumerate(bars):
                now=row[0]+60_000
                if not(anchor-6*3600_000<=now<=anchor+6*3600_000):
                    continue
                if now%180_000:
                    continue
                if row[5]<=0 or row[6]==0:
                    no_trade+=1
                    continue
                volume24=prefix[i+1]-prefix[max(0,i+1-1440)]
                live.observe_snapshot(db,src["venue"],now,[{
                    "symbol":src["symbol"],"lastPrice":str(row[4]),
                    "quoteVolume":str(volume24)}])
                live.process_queue(db,now,fetch_closed)
                polls+=1
                last=now
            if last:
                for k in range(1,7):
                    live.process_queue(db,last+180_000*k,fetch_closed)
            events=[dict(x) for x in db.execute(
                "SELECT event_id,event_type,observed_ms,payload FROM events ORDER BY observed_ms,event_id")]
            watches=[x for x in events if x["event_type"]=="WATCH_EARLY"]
            setups=[x for x in events if x["event_type"]=="SETUP_ACTIVE"]
            first_watch=watches[0]["observed_ms"] if watches else None
            return {
                "venue":src["venue"],"symbol":src["symbol"],"cohort":src["cohort"],
                "old_watch_utc":src["old_watch_utc"],"first_available_utc":full.utc(first),
                "first_available_minutes_before_old_watch":round((anchor-first)/60000,2),
                "available_contiguous_minutes":len(bars),
                "deduplicated_overlap_records":duplicates,
                "rolling_24h_quote":"SUM_OF_AVAILABLE_1M_QUOTES_SINCE_FIRST_EXCHANGE_KLINE",
                "first_listing_time_officially_verified":False,
                "full_24h_warmup":False,"polls":polls,
                "skipped_poll_zero_trades":no_trade,
                "watch_count":len(watches),
                "first_watch_utc":full.utc(first_watch) if first_watch else None,
                "lead_hours_vs_old_anchor":round((anchor-first_watch)/3600000,3)
                    if first_watch is not None else None,
                "d1_setups":len(setups),
                "watch_events":[{"utc":full.utc(x["observed_ms"]),
                                 "data":json.loads(x["payload"])} for x in watches],
                "setup_events":[{"utc":full.utc(x["observed_ms"])} for x in setups],
                "executable_historical_book":False,
                "historical_return_not_assessed":True,
                "stage":"SHORT_HISTORY_EXPLORATORY_NOT_COMPARABLE_TO_FULL_WARMUP",
                "trading":"NO_GO"}
        finally:
            db.close()


def run_short(paths=None):
    if paths is None:
        paths=sorted(EVIDENCE.glob("monster_v4_replay_1m_*.json"))
    out=[];skipped=[]
    for path in paths:
        try:
            src,bars,dups=normalize_partial(path)
            out.append(replay_partial(src,bars,dups))
        except ValueError as exc:
            if str(exc)=="NOT_A_SHORT_HISTORY_CASE":
                continue
            skipped.append({"file":Path(path).name,"error":str(exc)[:120]})
    cohorts={}
    for kind in ("FULLMARKET_SAMPLED","GT5X_PREHIT_POSITIVE"):
        vals=[x for x in out if x["cohort"]==kind]
        cohorts[kind]={"short_history_cases":len(vals),
                       "cases_with_watch":sum(x["watch_count"]>0 for x in vals),
                       "cases_with_setup":sum(x["d1_setups"]>0 for x in vals),
                       "first_watch_before_old_anchor":sum(
                           x["lead_hours_vs_old_anchor"] is not None and
                           x["lead_hours_vs_old_anchor"]>=0 for x in vals),
                       "total_watch_events":sum(x["watch_count"] for x in vals)}
    newlisting=[x for x in out if x["symbol"] in
        ("EULUSDT","WCTUSDT","ZRCUSDT","STBLUSDT","RECALLUSDT",
         "CTRUSDT","GRVTUSDT","BROCCOLI714USDT","FOLKSUSDT")]
    return {"classification":"SEPARATE_SHORT_HISTORY_OBSERVATIONAL_REPLAY",
            "source":"FROZEN_OFFICIAL_BINANCE_1M_NO_PRESUMED_HISTORY",
            "eligible":len(out),"source_failures":len(skipped),
            "cohorts":cohorts,"new_listing_venue_cases":len(newlisting),
            "historical_liquidity_book":"NOT_AVAILABLE",
            "future_profitability_validated":False,
            "first_listing_timestamp_unverified":True,
            "deploy_gate":"NO_GO",
            "rejected":skipped,"cases":out}


def main():
    print(json.dumps(run_short(),indent=2,sort_keys=True))


if __name__=="__main__":
    main()
