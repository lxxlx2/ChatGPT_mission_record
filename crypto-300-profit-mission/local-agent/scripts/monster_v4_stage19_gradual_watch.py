#!/usr/bin/env python3
"""Stage19: unmodified V4 versus separately preregistered gradual WATCH.

Historical pre-exposed five dates; not out of sample; all eligible 758 Spot
symbols attempted; zero trading or notifications. Source = official 1m ZIP
with publisher checksum. Gradual gates frozen before the bulk run.
"""
import argparse
import concurrent.futures
import json
import statistics
import sys
import urllib.error
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_archive_universe_replay as archive
    import monster_v4_historical_replay as replay
    import monster_v4_stage15_archive_only as stage15
except ImportError:
    from scripts import monster_v4_archive_universe_replay as archive
    from scripts import monster_v4_historical_replay as replay
    from scripts import monster_v4_stage15_archive_only as stage15

PREREG = archive.source.EVIDENCE / "monster_stage19_gradual_watch_exploratory_prereg_20261011.json"
WORKERS = 8

def frozen():
    config=json.loads(PREREG.read_text(encoding="utf-8"))
    if config.get("schema")!="MONSTER_STAGE19_EXPLORATORY_GRADUAL_WATCH_FIXED_BEFORE_REAL_BULK_1M_REPLAY_V1":
        raise ValueError("STAGE19_UNKNOWN_PREREG")
    strategy=config["candidate_v1"]
    signature=(strategy["rolling_6h_close_return_min_pct"],
               strategy["rolling_2h_close_return_min_pct"],
               strategy["trailing_24h_quote_usdt_min"],
               strategy["signal_cooldown_minutes"],strategy["entry_delay_min"],
               strategy["hold_minutes"],strategy["assumed_fee_per_side_bps"],
               strategy["assumed_slippage_per_side_bps"])
    if signature!=(10,3,250000,1440,3,1440,10,20):
        raise ValueError("STAGE19_FROZEN_GATE_CHANGED")
    if config.get("dates")!=list(stage15.FROZEN_DATES) or config["frozen_full_universe"]!=758:
        raise ValueError("STAGE19_FROZEN_DATES_CHANGED")
    return config

def union(inventory_get=stage15.inventory):
    config=frozen()
    inv=inventory_get()
    if (inv["archive_only_sha256"]!=config["archive_only_set_sha256"]
            or len(inv["archive_only_symbols"])!=254):
        raise ValueError("STAGE19_UNIVERSE_DRIFT")
    symbols=sorted(stage15.frozen_current504() | set(inv["archive_only_symbols"]))
    if len(symbols)!=758:
        raise ValueError("STAGE19_UNIVERSE_BAD_SIZE")
    return symbols

def price_gates(bars):
    """Same completed 1m close/cumulative quotes as historical V4, 3m polls."""
    if len(bars)!=3600 or any(bars[i+1][0]-bars[i][0]!=60000
                              for i in range(len(bars)-1)):
        raise ValueError("STAGE19_NONCONTIGUOUS_SOURCE")
    quotes=[Decimal(0)]
    for b in bars:
        quotes.append(quotes[-1]+b[5])
    candidate=None; n_eligible=0;n_6h=0;n_2h=0;n_liq=0
    for i in range(1442,2160,3):
        observed=bars[i][0]+60000
        close=bars[i][4]
        if close<=0 or bars[i][6]<=0 or bars[i][5]<=0:
            continue
        ret6=close/bars[i-360][4]-1
        ret2=close/bars[i-120][4]-1
        rolling=quotes[i+1]-quotes[i+1-1440]
        n_eligible+=1
        n_6h+=int(ret6>=Decimal("0.10"))
        n_2h+=int(ret2>=Decimal("0.03"))
        n_liq+=int(rolling>=Decimal("250000"))
        if (ret6>=Decimal("0.10") and ret2>=Decimal("0.03")
                and rolling>=Decimal("250000") and candidate is None):
            candidate={
                "watch_ms":observed,
                "watch_utc":replay.utc(observed),
                "6h_change_pct":round(float(ret6*100),6),
                "2h_change_pct":round(float(ret2*100),6),
                "quote24_usdt":str(rolling),
                "label":"EXPLORE_GRADUAL_WATCH",
            }
    return candidate,{"eligible_trade_3m_polls":n_eligible,
                      "6h_momentum_polls":n_6h,
                      "2h_momentum_polls":n_2h,
                      "quote24_polls":n_liq}

def run_symbol(symbol,day, *, get_day=archive.get_day, comparator=replay.replay_case):
    raw=[];sources=[]
    try:
        for offset in (-1,0,1):
            d=day+timedelta(days=offset)
            day_bars,meta=get_day(symbol,d)
            raw.extend(day_bars)
            sources.append({"date":d.isoformat(),"sha256":meta["sha256"]})
        bars=raw[360:3960]
        first=replay.parse_ms(day.isoformat()+"T12:00:00Z")-30*3600000
        if len(bars)!=3600 or any(row[0]!=first+i*60000 for i,row in enumerate(bars)):
            raise ValueError("STAGE19_INCOMPLETE_60H")
        gradual,debug=price_gates(bars)
        baseline=comparator({"symbol":symbol,"venue":"spot",
                             "cohort":"STAGE19_OLD_PRODUCTION_COMPARATOR",
                             "old_watch_utc":day.isoformat()+"T12:00:00Z"},
                            bars,include_zero_trade_ticks=True)
        old_first=baseline["first_watch_utc"]
        old_ms=replay.parse_ms(old_first) if old_first else None
        if gradual is not None:
            watchms=gradual["watch_ms"]
            # Don't retrospectively treat any later historical V4 WATCH as
            # proof the earlier gradual WATCH was redundant.
            incremental=(old_ms is None or watchms<old_ms)
            proxy=replay._proxy_trade(bars,bars[0][0],watchms,180000,20)
            gradual["watch_ms"]=watchms
            gradual["incremental_before_old_v4"]=incremental
            gradual["24h_trade_price_proxy"]=proxy
        return {"symbol":symbol,"status":"COMPLETE_60H",
                "date":day.isoformat(),"archive_sha256":sources,
                "v4_first_watch_utc":old_first,"v4_watch_count":baseline["watch_count"],
                "v4_d1_count":baseline["d1_setups"],
                "gradual_first_watch":gradual,
                "sampling":debug}
    except urllib.error.HTTPError as e:
        return {"symbol":symbol,"status":"SOURCE_MISSING" if e.code==404 else "SOURCE_HTTP_FAILURE",
                "reason":str(e)[:120]}
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        return {"symbol":symbol,"status":"SOURCE_NETWORK_FAILED","reason":str(e)[:120]}
    except ValueError as e:
        return {"symbol":symbol,"status":"SOURCE_PARTIAL_OR_INTEGRITY_REJECTED","reason":str(e)[:120]}

def summarize(cases):
    statuses=Counter(x["status"] for x in cases)
    valid=[x for x in cases if x["status"]=="COMPLETE_60H"]
    watched=[x for x in valid if x["gradual_first_watch"] is not None]
    before=[x for x in watched if x["gradual_first_watch"]["incremental_before_old_v4"]]
    proxies=[x["gradual_first_watch"]["24h_trade_price_proxy"] for x in watched]
    returns=[x["net_pct"] for x in proxies if x["status"]=="PRICE_PROXY_ONLY"]
    bad=Counter(x["status"] for x in proxies if x["status"]!="PRICE_PROXY_ONLY")
    return {"attempted":len(cases),"status_counts":dict(statuses),
        "complete_60h":len(valid),
        "old_v4_watch_episodes":sum(x["v4_watch_count"] for x in valid),
        "old_v4_d1_episodes":sum(x["v4_d1_count"] for x in valid),
        "gradual_candidate_symbol_dates":len(watched),
        "gradual_incremental_before_existing_v4_watch":len(before),
        "gradual_24h_price_proxy_evaluable":len(returns),
        "gradual_24h_price_proxy_win":sum(r>0 for r in returns),
        "gradual_24h_price_proxy_loss":sum(r<0 for r in returns),
        "gradual_24h_price_proxy_median_pct":round(statistics.median(returns),6) if returns else None,
        "gradual_24h_price_proxy_mean_pct":round(statistics.mean(returns),6) if returns else None,
        "gradual_24h_proxy_30usdt_sum":round(sum(r*0.30 for r in returns),6),
        "gradual_censored":dict(bad),
        "research_only":True}

def run_day(date_string, *, symbols=None, worker=run_symbol):
    if date_string not in stage15.FROZEN_DATES:
        raise ValueError("STAGE19_DATE_NOT_FROZEN")
    config=frozen()
    targets=union() if symbols is None else list(symbols)
    if len(set(targets))!=len(targets) or any(not s.endswith("USDT") for s in targets):
        raise ValueError("STAGE19_INVALID_SYMBOL_SET")
    date_value=date.fromisoformat(date_string)
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures={pool.submit(worker,s,date_value):s for s in targets}
        for f in concurrent.futures.as_completed(futures):
            item=f.result()
            if item["symbol"]!=futures[f]:
                raise ValueError("STAGE19_IDENTITY_MISMATCH")
            rows.append(item)
            if len(rows)%100==0:
                print("STAGE19_PROGRESS "+json.dumps({"date":date_string,
                        "processed":len(rows),"target":len(targets)}),file=sys.stderr,flush=True)
    rows.sort(key=lambda x:x["symbol"])
    return {"schema":"MONSTER_STAGE19_EXPLORATORY_GRADUAL_WATCH_V1",
        "date":date_string,"official_source":"BINANCE_SPOT_DAILY_1M_SHA256_PUBLISHER",
        "frozen_current_plus_historical_758":symbols is None,
        "frozen_candidate_rule":config["candidate_v1"],
        "baseline":"UNCHANGED_PRODUCTION_V4_D0_D1",
        "disclosure":"IN_SAMPLE_RESEARCH_NOT_INDEPENDENT_OOS",
        "summary":summarize(rows),"cases":rows,
        "deployment":"NO_GO","real_gmail":False,"trading":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--date",choices=stage15.FROZEN_DATES,required=True)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    result=run_day(args.date)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STAGE19_RESULT_JSON "+json.dumps(result["summary"],sort_keys=True),flush=True)
    if result["summary"]["complete_60h"]<120:
        raise SystemExit("STAGE19_TOO_FEW_VALID_SYMBOLS")
    if any(k in result["summary"]["status_counts"] for k in
           ("SOURCE_NETWORK_FAILED","SOURCE_HTTP_FAILURE","SOURCE_PARTIAL_OR_INTEGRITY_REJECTED")):
        raise SystemExit("STAGE19_SOURCE_UNAVAILABLE_OR_INTEGRITY")

if __name__=="__main__":
    main()
