#!/usr/bin/env python3
"""Stage12: full CURRENT 504-symbol USDT Spot universe, one calendar-window replay.

Never a historical point-in-time universe, independent out-of-sample holdout,
profitability proof, live monitoring system, Gmail sender, or trading program.
Official free Binance public 1m ZIP and .CHECKSUM; all 504 preregistered
before source access. Uses EXACT production V4 D0/D1 Python functions.
"""
import argparse
import concurrent.futures
import json
import statistics
import sys
import time
import urllib.error
from collections import Counter
from datetime import date,timedelta
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_archive_crosscheck as source
    import monster_v4_historical_replay as replay
except ImportError:
    from scripts import monster_v4_archive_crosscheck as source
    from scripts import monster_v4_historical_replay as replay

REGISTRY = source.EVIDENCE / "monster_stage12_all504_spot_universe_preregistered_20261011.json"
DAY = date(2026,9,17)
ANCHOR = "2026-09-17T12:00:00Z"
SIMULATED = "CURRENT_LISTING_SURVIVOR_COHORT_NOT_UNBIASED"
MAX_WORKERS = 8


def get_day(symbol,day,download=source.read_url):
    url=source.zip_url(symbol,day)
    for attempt in range(3):
        try:
            return source.extract_verified_archive(download(url),
                                                   download(url+".CHECKSUM",2048),
                                                   symbol,day)
        except urllib.error.HTTPError as e:
            if e.code in (403,404):
                raise ValueError("SOURCE_NOT_HISTORICALLY_AVAILABLE_HTTP_"+str(e.code))
            if attempt==2:
                raise
            time.sleep(1+attempt)
        except (urllib.error.URLError,TimeoutError,ConnectionError):
            if attempt==2:
                raise
            time.sleep(1+attempt)


def run_symbol(symbol,download=source.read_url,calendar_day=None,calendar_anchor=None):
    """Reuse identical Stage12 production D0/D1 scoring for frozen new dates.

    Calendar parameters select only WHICH historical bars to fetch, not model
    thresholds, outcome labels, entry/exit or treatment of missing sources.
    """
    day = DAY if calendar_day is None else calendar_day
    anchor = ANCHOR if calendar_anchor is None else calendar_anchor
    if replay.parse_ms(anchor) != replay.parse_ms(day.isoformat()+"T12:00:00Z"):
        raise ValueError("INVALID_CALENDAR_ANCHOR")
    days=[day+timedelta(days=i) for i in (-1,0,1)]
    raw=[]
    proof=[]
    try:
        for day in days:
            rows,detail=get_day(symbol,day,download)
            raw.extend(rows)
            proof.append(detail)
        bars=raw[360:3960]
        start=replay.parse_ms(anchor)-30*3600_000
        if len(bars)!=3600 or any(x[0]!=start+i*60_000 for i,x in enumerate(bars)):
            raise ValueError("INCOMPLETE_60H_REAL_ARCHIVE")
        obj={"symbol":symbol,"venue":"spot",
             "cohort":"STAGE12_PREREG_ALL_CURRENT_SPOT_USDT_CALENDAR",
             "old_watch_utc":anchor}
        case=replay.replay_case(obj,bars,include_zero_trade_ticks=True)
        profits=[]
        trade_states=Counter()
        for t in case["trade_proxies"]:
            p=t["scenario_0_20_100bps"]["20"]
            trade_states[p["status"]]+=1
            if p["status"]=="PRICE_PROXY_ONLY":
                profits.append(p["net_pct"])
        d1_proxies=[]
        for setup in case["setup_events"]:
            setup_time=replay.parse_ms(setup["utc"])
            # This is an explicitly hypothetical trade 3m after D1 confirmation.
            # Trading is NOT enabled; no historical L2 depth exists.
            simulated=replay._proxy_trade(bars,bars[0][0],setup_time,180000,20)
            d1_proxies.append({"setup_utc":setup["utc"],"proxy":simulated})
        return {"symbol":symbol,"status":"COMPLETE_60H",
                "archive_sha256":[p["sha256"] for p in proof],
                "verified_minute_bars":len(bars),
                "polls":case["polls"],
                "zero_trade_poll_proxy":case["polls_zero_trade_minute"],
                "watch_events":case["watch_count"],
                "first_watch_utc":case["first_watch_utc"],
                "setups":case["d1_setups"],
                "d1_queue":case["d1_queue"],
                "trade_proxy_statuses":dict(trade_states),
                "24h_assumed_20bps_net_pct":profits,
                "setup_triggered_24h_proxy_20bps":d1_proxies,
                "no_historical_l2_book":True,
                "signal_is_not_a_buy_order":True}
    except ValueError as exc:
        # Invalid or unverifiable data are NOT scored as no-WATCH winners.
        problem=str(exc)
        if problem.startswith("SOURCE_NOT_HISTORICALLY_AVAILABLE"):
            status="SOURCE_MISSING"
        elif problem in ("GAPPED_ARCHIVE_DAY","INCOMPLETE_60H_REAL_ARCHIVE"):
            status="SOURCE_PARTIAL_OR_NONCONTIGUOUS_HISTORICAL_CANDLES"
        else:
            status="SOURCE_INTEGRITY_REJECTED"
        return {"symbol":symbol,"status":status,
                "error":type(exc).__name__+":"+str(exc)[:160]}
    except (urllib.error.URLError,urllib.error.HTTPError,TimeoutError,ConnectionError,OSError) as exc:
        return {"symbol":symbol,"status":"SOURCE_NETWORK_FAILED",
                "error":type(exc).__name__+":"+str(exc)[:160]}


def validate_manifest(reg):
    if reg.get("schema")!="MONSTER_STAGE12_ALL_504_CURRENT_SPOT_USDT_UNIVERSE_PREREG_V1":
        raise ValueError("UNKNOWN_STAGE12_MANIFEST")
    if reg["calendar_anchor_utc"]!=ANCHOR:
        raise ValueError("CHANGED_RESEARCH_TIME")
    s=reg["frozen_symbols"]
    if len(s)!=504 or reg["frozen_count"]!=len(s) or len(set(s))!=504:
        raise ValueError("INCOMPLETE_PREDECLARED_UNIVERSE")
    if any(not x.endswith("USDT") for x in s):
        raise ValueError("INVALID_EXCHANGE_UNIVERSE")
    return s


def run(symbols=None,max_workers=MAX_WORKERS,worker=run_symbol):
    reg=json.loads(REGISTRY.read_text(encoding="utf-8"))
    expected=validate_manifest(reg)
    if symbols is None:
        symbols=expected
    if len(set(symbols))!=len(symbols) or any(s not in expected for s in symbols):
        raise ValueError("NOT_A_MANIFEST_SUBSET")
    if not 1<=max_workers<=MAX_WORKERS:
        raise ValueError("UNSAFE_BULK_REQUEST_CONCURRENCY")
    data=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures={pool.submit(worker,s):s for s in symbols}
        for future in concurrent.futures.as_completed(futures):
            item=future.result()
            if item.get("symbol")!=futures[future]:
                raise ValueError("FUTURE_RESULT_IDENTITY_MISMATCH")
            data.append(item)
            if len(data)%50==0:
                print("RESEARCH_PROGRESS "+json.dumps({
                    "processed":len(data),
                    "precommitted_target_count":len(symbols),
                    "valid":sum(v["status"]=="COMPLETE_60H" for v in data),
                    "missing":sum(v["status"]=="SOURCE_MISSING" for v in data),
                    "network_failures":sum(v["status"]=="SOURCE_NETWORK_FAILED" for v in data)
                }),file=sys.stderr,flush=True)
    data.sort(key=lambda x:x["symbol"])
    statuses=Counter(x["status"] for x in data)
    valid=[x for x in data if x["status"]=="COMPLETE_60H"]
    per_trade=[x for item in valid for x in item["24h_assumed_20bps_net_pct"]]
    d1_trades=[t["proxy"]["net_pct"] for item in valid
               for t in item["setup_triggered_24h_proxy_20bps"]
               if t["proxy"]["status"]=="PRICE_PROXY_ONLY"]
    d1_censored=Counter(t["proxy"]["status"] for item in valid
                        for t in item["setup_triggered_24h_proxy_20bps"]
                        if t["proxy"]["status"]!="PRICE_PROXY_ONLY")
    total_polls=sum(x["polls"] for x in valid)
    total_skipped_recent_trade=sum(x["zero_trade_poll_proxy"] for x in valid)
    summary={
        "pre_registered_total":len(expected),
        "case_count_executed":len(data),
        "full_universe_attempted":len(data)==len(expected),
        "source_status_counts":dict(statuses),
        "full_60h_data_cases":len(valid),
        "verified_official_archive_1m_bars":sum(x["verified_minute_bars"] for x in valid),
        "12h_symbol_windows":len(valid),
        "nominal_symbol_hours":len(valid)*12,
        "observed_3m_ticker_proxy_poll_count":total_polls,
        "zero_trade_closed_minute_fraction":round(total_skipped_recent_trade/max(total_polls,1),6),
        "watch_episodes":sum(x["watch_events"] for x in valid),
        "watch_symbol_count":sum(x["watch_events"]>0 for x in valid),
        "setup_episodes":sum(x["setups"] for x in valid),
        "setup_symbol_count":sum(x["setups"]>0 for x in valid),
        "assumed_30usdt_24h_trade_proxy_cases":len(per_trade),
        "assumed_20bps_per_side_net_return_median_pct":round(statistics.median(per_trade),6) if per_trade else None,
        "assumed_20bps_per_side_net_positive":sum(x>0 for x in per_trade),
        "assumed_20bps_per_side_net_negative":sum(x<0 for x in per_trade),
        "assumed_entry_basis_for_watch_pnl":"FIRST_WATCH_PLUS_3MIN_NOT_D1_SETUP",
        "d1_confirmed_30usdt_24h_proxy_cases":len(d1_trades),
        "d1_confirmed_20bps_net_median_pct":round(statistics.median(d1_trades),6) if d1_trades else None,
        "d1_confirmed_20bps_net_positive":sum(x>0 for x in d1_trades),
        "d1_confirmed_20bps_net_negative":sum(x<0 for x in d1_trades),
        "d1_confirmed_censored_24h_proxy_statuses":dict(d1_censored),
        "completely_unbiased_false_positive_rate":None,
        "deployment":"NO_GO",
    }
    return {"schema":"MONSTER_STAGE12_ALL504_ARCHIVE_V4_PRODUCTION_D0_D1_REPLAY_V1",
            "source":"OFFICIAL_BINANCE_PUBLIC_1M_DAILY_ZIP_CHECKSUM_VERIFIED",
            "anchor":ANCHOR,"market_scope":"2026-10-11_CURRENT_SPOT_USDT_504_ONLY",
            "cohort_type":SIMULATED,"validation_type":"RETROSPECTIVE_KNOWN_PERIOD",
            "observed_return_from_archived_1m_is_fill":False,
            "independent_other_ai_review":False,
            "summary":summary,"cases":data,
            "excluded_failure_are_never_treated_as_zero_watch":True,
            "automated_trading":False,"notification_sent":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--limit",type=int,default=0,
                        help="0=ALL predeclared 504; nonzero is explicitly SMOKE_ONLY")
    args=parser.parse_args()
    targets=validate_manifest(json.loads(REGISTRY.read_text(encoding="utf-8")))
    sample=targets[:args.limit] if args.limit else targets
    report=run(sample)
    report["classification"]="SMOKE_ONLY" if args.limit else "FULL_CURRENT_LISTED_UNIVERSE_ONE_12H_WINDOW"
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"STAGE12_SUMMARY":report["summary"],
                      "SRC_ERROR_CASES":[x for x in report["cases"] if x["status"]!="COMPLETE_60H"],
                      "SIGNAL_CASES":[{k:v for k,v in x.items()
                                        if k not in ("archive_sha256",)}
                                      for x in report["cases"]
                                      if x["status"]=="COMPLETE_60H" and x["watch_events"]>0],
                      "STATUS":report["classification"]},sort_keys=True))
    if report["summary"]["source_status_counts"].get("SOURCE_INTEGRITY_REJECTED",0):
        raise SystemExit("ARCHIVE_CHECKSUM_OR_INTEGRITY_REJECTED")
    if (not args.limit and
            (report["summary"]["full_60h_data_cases"] < 250 or
             report["summary"]["source_status_counts"].get("SOURCE_NETWORK_FAILED",0) > 50)):
        raise SystemExit("INCOMPLETE_OFFICIAL_BULK_SOURCE_COVERAGE")


if __name__=="__main__":
    main()
