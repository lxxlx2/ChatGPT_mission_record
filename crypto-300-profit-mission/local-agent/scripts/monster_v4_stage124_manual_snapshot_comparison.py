#!/usr/bin/env python3
"""Stage124 repeatable connected Binance MANUAL research snapshot evidence audit.

Read-only, offline. No live API, scheduled task, email, orders, or false OOS.
Future user-requested batches share a manifest and source-file shape.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from statistics import median

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
SCHEMA="MONSTER_STAGE124_CURRENT_MANUAL_MARKET_SNAPSHOT_COMPARISON_V1"


def utc_ms(x):
    if not isinstance(x,str) or not x.endswith("Z"):
        raise ValueError("STAGE124_MANIFEST_TIMESTAMP_NOT_UTC")
    t=datetime.fromisoformat(x.replace("Z","+00:00"))
    return int(t.timestamp()*1000)


def num(value, field):
    try:
        x=Decimal(str(value))
    except (InvalidOperation,TypeError,ValueError):
        raise ValueError("STAGE124_INVALID_NUMERIC_"+field)
    if not x.is_finite():
        raise ValueError("STAGE124_NONFINITE_NUMERIC_"+field)
    return x


def stats(vals):
    if not vals:return {"complete_n":0,"median":None,"p25":None,"p75":None,"p90":None}
    a=sorted(vals)
    n=len(a)
    return {
        "complete_n":n,
        "median":str(median(a)),
        "p25":str(a[(n-1)//4]),
        "p75":str(a[((n-1)*3)//4]),
        "p90":str(a[(n-1)*9//10]),
        "min":str(a[0]),"max":str(a[-1]),
    }


def unique(rows,kind):
    if not isinstance(rows,list):
        raise ValueError("STAGE124_NONLIST_"+kind)
    seen={}
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get("symbol"),str):
            raise ValueError("STAGE124_MISSING_SYMBOL_"+kind)
        symbol=row["symbol"]
        if symbol in seen:
            raise ValueError("STAGE124_DUPLICATE_SYMBOL_"+kind)
        seen[symbol]=row
    return seen


def load(manifest_path:Path):
    """Require exact user-archived eight original full-source file parts."""
    manifest_path=manifest_path.resolve()
    if manifest_path.parent!=E.resolve():
        raise ValueError("STAGE124_MANIFEST_OUTSIDE_MISSION_EVIDENCE")
    m=json.loads(manifest_path.read_text())
    if (m.get("schema")!="MONSTER_STAGE123_NEW_LIVE_BINANCE_STRUCTURED_MARKET_OBSERVATION_V1"
        or m.get("disclosure",{}).get("this_is_new_exploratory_baseline_not_original_OOS") is not True):
        raise ValueError("STAGE124_NOT_MANUAL_CONNECTOR_SOURCE_MANIFEST")
    rawtime=m["batch_utc"]["mid"]
    batch=utc_ms(rawtime)
    file_specs=m["source_paths"]
    if not isinstance(file_specs,list) or len(file_specs)!=8:
        raise ValueError("STAGE124_REQUIRE_ALL_EIGHT_FULL_SOURCE_FILES")
    symbols=[]
    seenParts=set()
    ticker=bbo=mark=None
    files=[]
    for spec in file_specs:
        relative=spec["path"]
        name=Path(relative).name
        if relative!="crypto-300-profit-mission/monster/evidence/"+name:
            raise ValueError("STAGE124_EVIDENCE_SOURCE_PATH_NOT_EXACT")
        location=(E/name).resolve()
        if location.parent!=E.resolve() or not location.is_file():
            raise ValueError("STAGE124_SOURCE_FILE_MISSING")
        data=location.read_text()
        # Original Stage123 manifest stores JS source-string length INCLUDING
        # the final newline. The UTF-8 Chinese names are preserved exactly.
        if spec["length"]!=len(data) or not data.endswith("\n"):
            raise ValueError("STAGE124_ARCHIVED_SOURCE_LENGTH_CHANGED")
        payload=json.loads(data)
        if payload.get("batch_observation_utc")!=rawtime:
            raise ValueError("STAGE124_NOT_SAME_BINANCE_BATCH")
        if name.endswith("_rolling24h_all.json"):
            if ticker is not None:raise ValueError("STAGE124_DUPLICATE_TICKER_FILE")
            ticker=unique(payload.get("all_tickers"),"24H")
        elif name.endswith("_bbo_all.json"):
            if bbo is not None:raise ValueError("STAGE124_DUPLICATE_BBO_FILE")
            bbo=unique(payload.get("all_quotes"),"BBO")
        elif name.endswith("_mark_all.json"):
            if mark is not None:raise ValueError("STAGE124_DUPLICATE_MARK_FILE")
            mark=unique(payload.get("all_marks"),"MARK")
        elif "_exchangeinfo_" in name:
            part=payload.get("slice_start")
            if (not isinstance(part,int) or part<0 or part%200
                    or part in seenParts):
                raise ValueError("STAGE124_UNORDERED_OR_DUPLICATE_EXCHANGEINFO_PART")
            seenParts.add(part)
            if payload.get("source_full_symbol_count")!=m["coverage"]["raw_exchange_info_count"]:
                raise ValueError("STAGE124_ORIGINAL_TOTAL_POPULATION_CHANGED")
            chunk=payload.get("symbols")
            if not isinstance(chunk,list):
                raise ValueError("STAGE124_INVALID_EXCHANGEINFO_CHUNK")
            symbols.append((part,chunk))
        else:
            raise ValueError("STAGE124_UNEXPECTED_EVIDENCE_FILENAME")
        files.append(name)
    if len(symbols)!=5 or {p for p,_ in symbols}!={0,200,400,600,800}:
        raise ValueError("STAGE124_FIVE_EXCHANGEINFO_CHUNKS_MISSING")
    original=[s for _,arr in sorted(symbols) for s in arr]
    if ticker is None or bbo is None or mark is None:
        raise ValueError("STAGE124_REQUIRED_MARKET_FEED_MISSING")
    allsyms=unique(original,"EXCHANGEINFO")
    active={n:s for n,s in allsyms.items()
            if s.get("status")=="TRADING" and
            s.get("contractType")=="PERPETUAL" and s.get("quoteAsset")=="USDT"}
    claimed=m["coverage"]
    if (len(allsyms)!=claimed["raw_exchange_info_count"] or
        len(active)!=claimed["active_usdt_perpetual_count"] or
        len(ticker)!=claimed["rolling_24h_tickers"] or
        len(bbo)!=claimed["bbo_count"] or
        len(mark)!=claimed["mark_count"]):
        raise ValueError("STAGE124_MANIFEST_FULL_DENOMINATOR_OR_FEEDS_DRIFT")
    coverage={
       "full_original_exchange_symbols":len(allsyms),
       "active_usdt_perpetual_symbols":len(active),
       "all_24h_ticker_symbols":len(ticker),
       "all_BBO_symbols":len(bbo),
       "all_mark_price_symbols":len(mark),
       "active_24h_ticker_observed":sum(n in ticker for n in active),
       "active_BBO_observed":sum(n in bbo for n in active),
       "active_mark_observed":sum(n in mark for n in active),
       "missing_24h_active":sorted(set(active)-set(ticker)),
       "missing_BBO_active":sorted(set(active)-set(bbo)),
       "missing_mark_active":sorted(set(active)-set(mark)),
       "nonascii_active_symbols":sorted(n for n in active if not n.isascii()),
    }
    if (coverage["active_24h_ticker_observed"]!=claimed["active_covered_24h"] or
        coverage["active_BBO_observed"]!=claimed["active_covered_bbo"] or
        coverage["active_mark_observed"]!=claimed["active_covered_mark"]):
        raise ValueError("STAGE124_FROZEN_FULL_COVERAGE_COUNTS_DRIFT")
    return {"batch":rawtime,"batch_ms":batch,"manifest":manifest_path.name,
            "market":allsyms,"active":active,"rolling":ticker,"bbo":bbo,"mark":mark,
            "files":files,"coverage":coverage}


def analyze(snapshot):
    prices=[]
    turnover=[]
    spreads=[]
    funding=[]
    health=Counter()
    age=[]
    for name in sorted(snapshot["active"]):
        t=snapshot["rolling"].get(name)
        b=snapshot["bbo"].get(name)
        k=snapshot["mark"].get(name)
        if t is not None:
            v=num(t.get("quoteVolume"),"QUOTE24H")
            p=num(t.get("priceChangePercent"),"RETURN24H")
            if v<0:raise ValueError("STAGE124_NEGATIVE_24H_VOLUME")
            turnover.append(v)
            prices.append(p)
            health["up"]+=int(p>0)
            health["down"]+=int(p<0)
            health["flat"]+=int(p==0)
            health["up10"]+=int(p>=10)
            health["up20"]+=int(p>=20)
            health["down10"]+=int(p<=-10)
            age.append(snapshot["batch_ms"]-int(t.get("closeTime")))
        if b is not None:
            bid=num(b.get("bidPrice"),"BID")
            ask=num(b.get("askPrice"),"ASK")
            if bid<=0 or ask<=0 or ask<bid:
                health["invalid_BBO"]+=1
            else:
                spreads.append((ask-bid)*Decimal(20000)/(ask+bid))
            age.append(snapshot["batch_ms"]-int(b.get("time")))
        if k is not None:
            mp=num(k.get("markPrice"),"MARK")
            if mp<=0:health["invalid_mark"]+=1
            f=k.get("lastFundingRate")
            if f is not None:funding.append(num(f,"FUNDING"))
            age.append(snapshot["batch_ms"]-int(k.get("time")))
    return {
        "batch_observed_utc":snapshot["batch"],
        "original_manifest":snapshot["manifest"],
        "coverage":snapshot["coverage"],
        "24h_change_pct_distribution":stats(prices),
        "24h_quote_USDT_distribution":stats(turnover),
        "displayed_BBO_spread_bps_distribution":stats(spreads),
        "reported_last_funding_rate_distribution":stats(funding),
        "24h_market_breadth":dict(health),
        "active_source_timestamp_lag_ms":{
           "min":min(age) if age else None,
           "median":str(median(age)) if age else None,
           "max":max(age) if age else None,
           "older_than_60_minutes":sum(x>3600000 for x in age),
           "negative_lag_count_non_atomic_feeds":sum(x<0 for x in age),
        },
        "no_future_signal_early_alert_from_24h_rolling_metrics":True,
        "crypto_issuer_certification":"NOT_VERIFIED",
        "price_only_not_actual_fill":True,
        "real_executable_net":"UNKNOWN",
    }


def pair(before,after):
    if after["batch_ms"]<=before["batch_ms"]:
        raise ValueError("STAGE124_PRIOR_BATCH_NOT_BEFORE_CURRENT")
    old=set(before["active"])
    new=set(after["active"])
    both=sorted(old&new)
    values=[]
    no_mark=[]
    before_only=[]
    after_only=[]
    for name in both:
        b=before["mark"].get(name)
        a=after["mark"].get(name)
        if b is None or a is None:
            no_mark.append(name)
            continue
        p=num(b.get("markPrice"),"OLD_MARK")
        q=num(a.get("markPrice"),"NEW_MARK")
        if p<=0 or q<=0:
            no_mark.append(name)
            continue
        values.append(((q/p)-1)*100)
    return {
      "older_batch_UTC":before["batch"],
      "newer_batch_UTC":after["batch"],
      "elapsed_hours":str(Decimal(after["batch_ms"]-before["batch_ms"])/Decimal(3600000)),
      "same_venue_exact_symbol_retained_active":len(both),
      "previous_active_not_currently_active":sorted(old-new),
      "newly_active_vs_previous":sorted(new-old),
      "paired_mark_to_mark_gross_percentage_distribution":stats(values),
      "retained_but_missing_pair_mark_price":no_mark,
      "retained_with_valid_pair":len(values),
      "observed_2x_or_more_between_two_snapshot_mark_prices_ONLY":
          sum(x>=100 for x in values),
      "observed_loss20pct_or_more_between_snapshot_mark_prices_ONLY":
          sum(x<=-20 for x in values),
      "comparison_is_descriptive_not_1m_signal_recall":True,
      "notional_fees_orderbook_depth_and_real_net":"UNKNOWN",
    }


def selftest():
    assert stats([Decimal(1),Decimal(3),Decimal(2)])["median"]=="2"
    a={"batch":"2026-10-14T09:48:24Z","batch_ms":0,
       "active":{"龙虾USDT":{},"BTСUSDT":{}},
       "mark":{"龙虾USDT":{"markPrice":"1"}}}
    b={"batch":"2026-10-28T06:00:00Z","batch_ms":14*86_400_000,
       "active":{"龙虾USDT":{},"新币USDT":{}},
       "mark":{"龙虾USDT":{"markPrice":"2"}}}
    p=pair(a,b)
    assert p["observed_2x_or_more_between_two_snapshot_mark_prices_ONLY"]==1
    assert p["paired_mark_to_mark_gross_percentage_distribution"]["median"]=="100"
    assert p["same_venue_exact_symbol_retained_active"]==1
    assert p["newly_active_vs_previous"]==["新币USDT"]
    assert p["previous_active_not_currently_active"]==["BTСUSDT"]
    try:pair(b,a)
    except ValueError:pass
    else:raise AssertionError("STAGE124_FUTURE_MARK_AS_PAST_ALLOWED")
    print("STAGE124_MANUAL_FULL_MARKET_UNICODE_CENSOR_AND_PAIRING_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--manifest",type=Path)
    p.add_argument("--previous-manifest",type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    if args.selftest:
        selftest()
        return
    if args.manifest is None or args.out is None:
        p.error("--manifest --out required")
    now=load(args.manifest)
    result={
        "schema":SCHEMA,
        "report":analyze(now),
        "manual_collection_no_automatic_schedule":True,
        "source_authentication":"BINANCE_CONNECTOR_STRUCTURED_NOT_RAW_STAGE97_TLS_BODY",
        "original_fixed_2026_10_14_0600_stage99":"SOURCE_FAILED_NO_BACKFILL",
        "new_OOS_early_detection_performance":"NOT_SCORED",
        "Stage118_strategy":"REJECTED",
        "G0_crypto":"PARTIAL",
        "G4_real_net":"UNKNOWN",
        "Monster_deployment":"NO_GO",
        "Frank":"UNCHANGED",
    }
    if args.previous_manifest is not None:
        result["paired_snapshot_comparison"]=pair(load(args.previous_manifest),now)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print("STAGE124_REAL_FULL_MARKET_OFFLINE_REPORT "+json.dumps({
       "batch":now["batch"],"active":len(now["active"]),
       "source_coverage":now["coverage"],
       "previous_snapshot_paired":args.previous_manifest is not None,
       "actual_strategy_deployment":"NO_GO"},ensure_ascii=False))


if __name__=="__main__":
    main()
