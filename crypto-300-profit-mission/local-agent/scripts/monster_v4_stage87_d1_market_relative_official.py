#!/usr/bin/env python3
"""Stage87 market-relative D1 features using published SHA BTC/ETH reference 1m only."""
from __future__ import annotations

import argparse
import collections
from datetime import datetime, timedelta, timezone
import json
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage38_usdm_original_v4_1m_pilot as pub
    from monster_v4_stage80_dual_entry_core import (
        from_archived_closed_bars, sha_blob, decimal, utc_ms)
except ImportError:
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as pub
    from scripts.monster_v4_stage80_dual_entry_core import (
        from_archived_closed_bars, sha_blob, decimal, utc_ms)

E=Path(__file__).resolve().parents[2]/"monster/evidence"
SOURCE=E/"monster_stage85_all305_official_D1_asof_features.jsonl"
PIN="622299fec16400e189cb8fa668ecbc8bc31ec630"
DATES=("2025-01-30","2025-06-02","2025-08-01","2025-10-02","2026-06-21","2026-07-28")
REFERENCES=("BTCUSDT","ETHUSDT")
SCHEMA="MONSTER_STAGE87_USDM_REFERENCE_RET60_MARKET_EXCESS_305_CAUSAL_V1"
MINUTE=60000


def frozen_rows():
    raw=SOURCE.read_bytes()
    if sha_blob(raw)!=PIN:
        raise ValueError("STAGE87_STAGE85_ORIGINAL_ASOF_BLOB_CHANGED")
    rows=[json.loads(s) for s in raw.decode().splitlines() if s.strip()]
    if len(rows)!=305 or len({(x["date"],x["symbol"]) for x in rows})!=305:
        raise ValueError("STAGE87_NOT_FULL305")
    if any(x["source_status"]!="COMPLETE_OFFICIAL_BINANCE_SHA_ASOF_D1" for x in rows):
        raise ValueError("STAGE87_ORIGINAL_SOURCE_NOT_ALL_COMPLETE")
    return rows


def days_for(rows):
    days=set()
    for row in rows:
        ts=utc_ms(row["D1_FIRST_UTC"])
        first=datetime.fromtimestamp((ts-61*MINUTE)/1000,timezone.utc).date()
        last=datetime.fromtimestamp((ts-MINUTE)/1000,timezone.utc).date()
        for i in range((last-first).days+1):
            days.add(first+timedelta(days=i))
    return sorted(days)


def asof(source,ts):
    closed=[source.get(ts-i*MINUTE) for i in range(61,0,-1)]
    if any(row is None for row in closed):
        raise ValueError("STAGE87_REFERENCE_MISSING_REAL_ASOF_BAR")
    return from_archived_closed_bars(closed,ts)


def run_day(day,reader=pub.verified_1m_day):
    if day not in DATES:
        raise ValueError("STAGE87_NON_FROZEN_DAY")
    rows=[x for x in frozen_rows() if x["date"]==day]
    if not rows:
        raise ValueError("STAGE87_NO_FROZEN_TARGETS")
    days=days_for(rows)
    reference={}
    proofs=[]
    unknown_days=set()
    for symbol in REFERENCES:
        candle={}
        for d in days:
            try:
                bars,proof=reader(symbol,d)
            except FileNotFoundError:
                unknown_days.add((symbol,d.isoformat()))
                continue
            if not proof["verified_official_publisher_SHA256"] or len(bars)!=1440:
                raise ValueError("STAGE87_MISSING_OFFICIAL_REFERENCE_SHA")
            proofs.append({"symbol":symbol,**proof})
            for bar in bars:
                if bar[0] in candle:
                    raise ValueError("STAGE87_DUPLICATE_MINUTE")
                candle[bar[0]]=bar
        reference[symbol]=candle
    result=[]
    for row in rows:
        ts=utc_ms(row["D1_FIRST_UTC"])
        out={"date":row["date"],"symbol":row["symbol"],
             "D1_FIRST_UTC":row["D1_FIRST_UTC"],"D1_PATH":row["D1_PATH"],
             "source_original_D1_SHA":PIN,
             "original_D1_ret60_pct":row["asof_D1_ret60_pct"],
             "original_D1_quote_ratio":row["asof_D1_normalized_quote15_prev45"],
             "benchmark_status":"UNKNOWN"}
        try:
            f_btc=asof(reference["BTCUSDT"],ts)
            f_eth=asof(reference["ETHUSDT"],ts)
        except ValueError as exc:
            if "REFERENCE_MISSING_REAL_ASOF_BAR" not in str(exc):
                raise
            out.update(benchmark_status="CENSORED_REFERENCE_OFFICIAL_DAILY_UNKNOWN")
            result.append(out)
            continue
        if f_btc.quote15_relative45 is None or f_eth.quote15_relative45 is None:
            out.update(benchmark_status="CENSORED_REFERENCE_PRIOR45_ZERO")
            result.append(out)
            continue
        mean_ret=(f_btc.ret60_pct+f_eth.ret60_pct)/2
        mean_quote=(f_btc.quote15_relative45+f_eth.quote15_relative45)/2
        own_ret=decimal(row["asof_D1_ret60_pct"])
        own_quote=decimal(row["asof_D1_normalized_quote15_prev45"])
        out.update(
          benchmark_status="COMPLETE_SHA_VERIFIED_BTC_ETH_REFERENCE",
          BTC_ret60_pct=str(f_btc.ret60_pct),ETH_ret60_pct=str(f_eth.ret60_pct),
          benchmark_market_avg_ret60_pct=str(mean_ret),
          candidate_excess_ret60_vs_BTC_pct=str(own_ret-f_btc.ret60_pct),
          candidate_excess_ret60_vs_ETH_pct=str(own_ret-f_eth.ret60_pct),
          candidate_excess_ret60_vs_BTCETH_mean_pct=str(own_ret-mean_ret),
          BTC_normalized_quote15_prev45=str(f_btc.quote15_relative45),
          ETH_normalized_quote15_prev45=str(f_eth.quote15_relative45),
          benchmark_market_avg_quote_ratio=str(mean_quote),
          candidate_excess_quote_ratio_vs_BTCETH_mean=str(own_quote-mean_quote))
        result.append(out)
    if len(result)!=len(rows):
        raise ValueError("STAGE87_REFERENCE_DROPPED_OLD_D1")
    return {"schema":SCHEMA,"date":day,"original_D1_count":len(rows),
        "benchmark_complete":sum(x["benchmark_status"]=="COMPLETE_SHA_VERIFIED_BTC_ETH_REFERENCE" for x in result),
        "benchmark_censored":sum(x["benchmark_status"]!="COMPLETE_SHA_VERIFIED_BTC_ETH_REFERENCE" for x in result),
        "official_reference_source_day_SHA":proofs,
        "official_reference_missing_days":[{"symbol":s,"date":d} for s,d in sorted(unknown_days)],
        "rows":sorted(result,key=lambda x:(x["date"],x["symbol"])),
        "NO_BTC_ETH_WATCHES":True,"NO_NEW_THRESHOLDS":True,
        "OOS":"NOT_DONE","DEPLOY":"NO_GO","GMAIL":"OFF","AUTOTRADE":"NO_GO"}


def selftest():
    source=frozen_rows()
    selected=[x for d in DATES for x in source if x["date"]==d]
    assert len(selected)==305
    assert len({(x["date"],x["symbol"]) for x in selected})==305
    sample=[{"D1_FIRST_UTC":"2025-01-30T06:00:00Z"}]
    assert [d.isoformat() for d in days_for(sample)]==["2025-01-30"]
    print("STAGE87_ALL305_ORIGINAL_COHORT_AND_BTCETH_ONLY_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--date")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.date or not a.out:
        p.error("--date and --out required")
    result=run_day(a.date)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE87_OFFICIAL_REFERENCE_COMPLETE "+json.dumps({
        k:result[k] for k in ("date","original_D1_count","benchmark_complete",
                "benchmark_censored")},sort_keys=True))

if __name__=="__main__":
    main()
