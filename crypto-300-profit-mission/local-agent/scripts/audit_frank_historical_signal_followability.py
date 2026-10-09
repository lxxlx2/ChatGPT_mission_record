#!/usr/bin/env python3
"""Bounded, single-run historical signal followability proxy from frozen M3 evidence.

Only public GeckoTerminal pools and 5-minute OHLCV. No private keys, no trades,
no notifications, no live data mutation. Results are NOT executable backtests.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import argparse
import json
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request

API="https://api.geckoterminal.com/api/v2"
REF_ROOT=Path(__file__).resolve().parents[2]
SOURCE=REF_ROOT/"meme/evidence/frank-trade-coverage-sol-usdt-complex-2026-10-04.json"
DELAYS=(300,900,1800,3600)
HORIZONS=(3600,21600,86400)

class BudgetStop(Exception):
    pass

class PublicRates:
    def __init__(self, budget, spacing):
        self.budget,self.spacing=budget,spacing
        self.uses=0
        self.last=0
    def get(self,url):
        if self.uses>=self.budget:raise BudgetStop("MAX_HTTP_REQUESTS_REACHED")
        if self.last:
            wait=self.spacing-(time.monotonic()-self.last)
            if wait>0:time.sleep(wait)
        self.last=time.monotonic()
        self.uses+=1
        request=urllib.request.Request(url,headers={
            "Accept":"application/json","User-Agent":"HistoricalResearchReadonly/1.0"})
        with urllib.request.urlopen(request,timeout=18) as resp:
            return json.load(resp)

def snapshot(path):
    r=json.loads(path.read_text())
    if r.get("history",{}).get("raw_hash_verified")!=6874:
        raise ValueError("SOURCE_HAS_NO_FIXED_VERIFIED_HISTORY")
    models=r["models"]
    signals=models["M3"]["signals"]
    if len(signals)!=32:raise ValueError("SOURCE_SIGNAL_COUNT_CHANGED")
    groups=defaultdict(list)
    for x in signals:
        if x["signal_type"]=="FRANK_ACCUMULATION_SIGNAL":
            groups[x["mint"]].append(x)
    if len(groups)!=18:raise ValueError("SOURCE_MINT_COUNT_CHANGED")
    return sorted(
        ({"mint":mint,"trigger_at":min(int(v["triggered_at"]) for v in xs),
          "sig":min(xs,key=lambda x:x["triggered_at"])["triggering_signature"],
          "signal_type":"FRANK_ACCUMULATION_SIGNAL",
          "signal_count":len([x for x in signals if x["mint"]==mint])}
         for mint,xs in groups.items()),
        key=lambda r:(r["trigger_at"],r["mint"]))

def choose_pool(pool_response,mint,at):
    for item in pool_response.get("data") or []:
        a=item.get("attributes") or {}
        relationships=item.get("relationships") or {}
        base=(relationships.get("base_token") or {}).get("data") or {}
        quote=(relationships.get("quote_token") or {}).get("data") or {}
        side="base" if mint in str(base.get("id","")) else "quote" if mint in str(quote.get("id","")) else None
        stamp=a.get("pool_created_at")
        try:
            created=datetime.fromisoformat(stamp.replace("Z","+00:00")).timestamp()
        except (AttributeError,ValueError):
            continue
        # First API-ranked *at that query date* pool that already existed at trigger.
        # Ranking may be hindsight-biased; do NOT call this best historic liquidity.
        if side and a.get("address") and created<=at:
            return {"address":a["address"],"side":side,"created":stamp,
                    "dex":(relationships.get("dex") or {}).get("data",{}).get("id")}
    return None

def find_forward_close(candles,ts):
    # 5m candle start at >= intended action timestamp (later close lookahead).
    row=next((c for c in candles if c[0]>=ts and c[0]<ts+900),None)
    return {"candle_start":row[0],"close":row[4],"volume":row[5]} if row else None

def compare(candles,signal_at):
    outputs=[]
    for delay in DELAYS:
        entry=find_forward_close(candles,signal_at+delay)
        horizons={}
        for horizon in HORIZONS:
            # HORIZON anchored on trigger, NOT delayed-entry time, so
            # 24h post-signal always same exit target for comparisons.
            exit=find_forward_close(candles,signal_at+horizon)
            pct=(exit["close"]/entry["close"]-1)*100 if (
                exit and entry and entry["close"] and exit["close"]) else None
            horizons[str(horizon)]={"gross_pct":round(pct,6) if pct is not None else None,
                     "exit_candle":exit["candle_start"] if exit else None}
        outputs.append({"delay_seconds":delay,"entry_candle":entry["candle_start"] if entry else None,
                        "entry_usd":entry["close"] if entry else None,"horizons":horizons})
    return outputs

def analyze(signals,limiter,cap=18):
    results=[]
    stopped=None
    for i,signal in enumerate(signals[:cap]):
        case={**signal,"status":"UNVERIFIED"}
        try:
            url=API+"/networks/solana/tokens/"+signal["mint"]+"/pools?page=1"
            pool=choose_pool(limiter.get(url),signal["mint"],signal["trigger_at"])
            if pool is None:
                case["status"]="NO_PRETRIGGER_POOL_ON_FIRST_PROVIDER_PAGE"
            else:
                case["pool"]=pool
                params=urllib.parse.urlencode({
                  "aggregate":5,"before_timestamp":signal["trigger_at"]+86400+900,
                  "limit":320,"currency":"usd","token":pool["side"]})
                response=limiter.get(API+"/networks/solana/pools/"+pool["address"]+
                                     "/ohlcv/minute?"+params)
                candles=sorted((response.get("data") or {}).get("attributes",{}).get("ohlcv_list") or [],
                               key=lambda x:x[0])
                case["bars"]=len(candles)
                case["status"]="OHLCV_PROXY_ONLY" if candles else "NO_BARS"
                if candles:
                    case["proxies"]=compare(candles,signal["trigger_at"])
                    case["bars_range"]=[candles[0][0],candles[-1][0]]
        except BudgetStop as exc:
            case["status"]="STOP_HTTP_BUDGET"
            stopped=str(exc)
            results.append(case)
            break
        except urllib.error.HTTPError as exc:
            case["status"]="HTTP_"+str(exc.code)
            if exc.code==429:
                stopped="HTTP_429_NO_RETRY"
                results.append(case)
                break
        except (OSError,ValueError,TypeError,KeyError) as exc:
            case["status"]="UNVERIFIED_PUBLIC_SOURCE_ERROR_"+type(exc).__name__
        results.append(case)
        print("CASE_JSON:",json.dumps(case,separators=(",",":"),ensure_ascii=False),flush=True)
    bydelay={}
    for d in DELAYS:
        bydelay[str(d)]={}
        for h in HORIZONS:
            values=[o["horizons"][str(h)]["gross_pct"]
                     for case in results for o in case.get("proxies") or []
                     if o["delay_seconds"]==d and
                     o["horizons"][str(h)]["gross_pct"] is not None]
            values.sort()
            positive=sum(x>0 for x in values)
            bydelay[str(d)][str(h)]={
                "n":len(values),"positive":positive,"negative":sum(x<0 for x in values),
                "median_pct":round(statistics.median(values),6) if values else None,
                "mean_pct":round(statistics.mean(values),6) if values else None,
                "mean_without_extremes_pct":round(statistics.mean(values[1:-1]),6)
                  if len(values)>=3 else None}
    return {"status":"COMPLETE_PROXY_SET" if len(results)==cap and not stopped
            else "PARTIAL_UNVERIFIED",
            "mint_signal_population":len(signals),"mints_attempted":len(results),
            "mints_with_proxy":sum(x["status"]=="OHLCV_PROXY_ONLY" for x in results),
            "http_attempts":limiter.uses,"http_budget":limiter.budget,
            "stopped":stopped,"lag_matrix":bydelay,
            "sample_size_not_statistical_generalization":True,
            "public_pool_ranking_hindsight_bias":True,
            "no_historic_executable_quotes":True,"no_slippage_fee_depth":True,
            "not_production_signals":True,"results":results}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,default=SOURCE)
    ap.add_argument("--max-http",type=int,default=36)
    ap.add_argument("--spacing",type=float,default=6.0)
    ap.add_argument("--limit-mints",type=int,default=18)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    if not 1<=args.max_http<=36 or args.spacing<5 or not 1<=args.limit_mints<=18:
        raise SystemExit("BOUNDS_INVALID")
    result=analyze(snapshot(args.source),PublicRates(args.max_http,args.spacing),args.limit_mints)
    if args.output:
        args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("SUMMARY_JSON:",json.dumps({k:v for k,v in result.items() if k!="results"},
                                     ensure_ascii=False,separators=(",",":")),flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
