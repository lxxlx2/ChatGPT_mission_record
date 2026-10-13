#!/usr/bin/env python3
"""Stage110 immutable original519/305 population and honest confirmation economics."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import statistics

try:
    import monster_v4_stage110_d1_continuous_confirm as s110
except ImportError:
    from scripts import monster_v4_stage110_d1_continuous_confirm as s110

old=s110.old
SCHEMA="MONSTER_STAGE110_ALL519_D0_ALL305_D1_REAL_1M_STATE_EVALUATION_V1"

def dmedian(a):
    return str(statistics.median(a)) if a else None

def summary(xs):
    returns=[Decimal(x["confirmed_next_open_to_24h_close"]["gross_pct"])
             for x in xs if x["confirmed_next_open_to_24h_close"]]
    return {"confirmed_with_trade_bars":len(returns),
            "price_proxy_positive":sum(v>0 for v in returns),
            "gross_median_pct":dmedian(returns),
            "price_proxy_loss20":sum(v<=-20 for v in returns),
            "price_proxy_up50":sum(v>=50 for v in returns),
            "price_proxy_up100":sum(v>=100 for v in returns),
            "price_proxy_only_not_executable_net":True}

def bucket_counts(xs):
    bins=Counter()
    for x in xs:
        start=old.utc_ms(x["date"]+"T06:00:00Z")
        stamp=old.utc_ms(x["decision_visible_UTC"])
        n=(stamp-start)//86_400_000
        if x["date"] not in old.DATES or not 0<=n<7:
            raise ValueError("STAGE110_CONFIRMATION_OUTSIDE_ORIGINAL_7_DAY_WINDOW")
        bins[(x["date"],n)]+=1
    all_days=[{"date":d,"utc06_day":n,"priority_count":bins[(d,n)]}
              for d in old.DATES for n in range(7)]
    return {"complete_days":42,
            "total_confirmations":len(xs),
            "avg_per_day":str(Decimal(len(xs))/42),
            "peak_per_day":max(d["priority_count"] for d in all_days),
            "passes_avg5_and_peak12":len(xs)<=210 and
                max(d["priority_count"] for d in all_days)<=12,
            "full_42_day_counts":all_days}

def collect(directory:Path):
    files=sorted(directory.glob("monster-stage110-*.json"))
    if len(files)!=24:
        raise ValueError("STAGE110_EXACT_24_SOURCE_SHARDS_REQUIRED")
    original,archived,previous,census,census_list=s110.frozen()
    seen=set()
    actual=[]
    for file in files:
        packet=json.loads(file.read_text())
        date,shard=packet["date"],packet["shard"]
        if packet["schema"]!=s110.SCHEMA or (date,shard) in seen:
            raise ValueError("STAGE110_SHARD_SCHEMA_OR_DUPLICATE_CHANGED")
        seen.add((date,shard))
        expected=old.shard_rows(date,shard,original)
        left={(r["date"],r["symbol"]) for r in expected}
        right={(r["date"],r["symbol"]) for r in packet["rows"]}
        if left!=right or len(left)!=len(packet["rows"]):
            raise ValueError("STAGE110_ORIGINAL_D1_SHARD_CASE_MISSING")
        if (packet["initial_D0_preserved"]!=519 or
            packet["initial_D1_preserved"]!=305):
            raise ValueError("STAGE110_D0_AND_D1_IDENTITY_LOST")
        for item in packet["rows"]:
            key=item["date"],item["symbol"]
            x=census[key]
            if (x["D1_FIRST_UTC"]!=item["D1_FIRST_UTC"]
                or x["D0_FIRST_UTC"]!=item["D0_FIRST_UTC"]
                or x["D1_PATH"]!=item["D1_PATH"]
                or len(item["source_days_real_official_sha"])<3):
                raise ValueError("STAGE110_D0_OR_SOURCE_EVIDENCE_DRIFT")
        actual.extend(packet["rows"])
    if seen!={(d,s) for d in old.DATES for s in range(4)}:
        raise ValueError("STAGE110_MISSING_DATE_SHARD")
    if len(actual)!=305 or len({(x["date"],x["symbol"]) for x in actual})!=305:
        raise ValueError("STAGE110_ORIGINAL_305_MISSING")
    return sorted(actual,key=lambda r:(r["date"],r["symbol"])),census_list

def audit(rows,census):
    original_keys={(x["date"],x["symbol"]) for x in census}
    new_keys={(x["date"],x["symbol"]) for x in rows}
    no_d1=[{"date":x["date"],"symbol":x["symbol"],
            "D0_FIRST_UTC":x["D0_FIRST_UTC"],
            "state":"D0_WATCH_RETAINED_NO_ORIGINAL_D1",
            "old_D0_early5_2x_EVAL_ONLY":x["D0_at_least_5m_before_2x"]}
           for x in census if (x["date"],x["symbol"]) not in new_keys]
    if len(no_d1)!=214 or not new_keys.issubset(original_keys):
        raise ValueError("STAGE110_ALL519_D0_NOT_CLOSED")
    priority=[x for x in rows if x["state"] in (
             "PRIORITY_CONFIRMED","CONFIRMED_BUT_NO_TRADE_BAR")]
    invalid=[x for x in rows if x["state"]=="INVALIDATED_EARLY_8PCT"]
    expired=[x for x in rows if x["state"]=="EXPIRED_NO_CONTINUOUS_CONFIRM"]
    if len(priority)+len(invalid)+len(expired)!=305:
        raise ValueError("STAGE110_UNKNOWN_OR_DROPPED_D1_STATE")
    checked=[x for x in priority if x["confirmed_next_open_to_24h_close"]]
    major=sum(x["D0_at_least_5m_before_2x"] for x in census)
    prior_major=sum(x["D1_at_least_5m_before_2x"] for x in census)
    new_major=sum(x["new_priority_early5_2x"] for x in priority)
    if major!=28 or prior_major!=27 or new_major>27:
        raise ValueError("STAGE110_ORIGINAL_GT2_OR_NEW_GT2_IMPLAUSIBLE")
    gaps=[{"date":x["date"],"symbol":x["symbol"],"D1_PATH":x["D1_PATH"],
           "old_D1_FIRST_UTC":x["D1_FIRST_UTC"],
           "original_old_early5":x["original_D1_early5_2x"],
           "new_state":x["state"],"confirmed_visible_UTC":x["decision_visible_UTC"],
           "original_2x_FIRST_HIGH_UTC":x["first_2x_HIGH_EVALUATION_ONLY"]}
          for x in rows if x["original_D1_early5_2x"] and
          not x["new_priority_early5_2x"]]
    if len(gaps)!=27-new_major:
        raise ValueError("STAGE110_MAJOR_WINNERS_UNACCOUNTED")
    load=bucket_counts(priority)
    economics=summary(priority)
    gates={
      "G2_major2x_prioritized_before_2x_ge5m_at_least_80pct":
          new_major*5>=major*4,
      "G3_max5_daily_avg_max12_day":load["passes_avg5_and_peak12"],
      "G4_24h_gross_price_median_gt0_RESEARCH_ONLY":
          economics["gross_median_pct"] is not None and
          Decimal(economics["gross_median_pct"])>0,
      "G0_FROZEN_ASOF_CRYPTO_SCOPE_PROVEN":False,
      "G4 वास्तविक_real_net_profit_proven":False,
    }
    # The last two are actually honest deployment gates, not fail-the-historic
    # strategy once G2/G3/price-only are separately judged.
    research_gates={k:gates[k] for k in list(gates)[:3]}
    rare=[]
    for x in rows:
        c=next(z for z in census if z["date"]==x["date"] and z["symbol"]==x["symbol"])
        for m in (5,10):
            k="historical_anchor_GT"+str(m)
            if c[k]:
                cross=c["true_first_"+str(m)+"x_HIGH_UTC_EVALUATION_ONLY"]
                lead=(cross is not None and x["state"] in (
                      "PRIORITY_CONFIRMED","CONFIRMED_BUT_NO_TRADE_BAR")
                      and old.utc_ms(cross)-old.utc_ms(x["decision_visible_UTC"])>=5*s110.MIN)
                rare.append({"date":x["date"],"symbol":x["symbol"],
                    "historic_multiple":m,"new_confirmed_early5":bool(lead),
                    "priority_state":x["state"],
                    "first_multiple_HIGH_UTC_EVAL_ONLY":cross})
    out={
       "schema":SCHEMA,"date_groups":list(old.DATES),
       "all_D0_original_preserved":519,"all_D1_original_preserved":305,
       "D0_WATCH_without_original_D1":no_d1,
       "all_source_cases":rows,
       "state_count":dict(Counter(x["state"] for x in rows)),
       "priority_by_path":{p:{"count":sum(x["D1_PATH"]==p for x in priority),
                               "economics":summary([x for x in priority if x["D1_PATH"]==p])}
                            for p in (s110.DIRECT,s110.REIGNITION)},
       "confirmed_24h_price_only_economics":economics,
       "original_all305_24h_positive":133,
       "original_all305_24h_gross_median":"-2.7992",
       "original_D1_7day_2x_early5_over_D0_28":prior_major,
       "stage110_2x_early5_over_D0_28":new_major,
       "missed_original_early_2x_cases":gaps,
       "rare_5x_10x_EVAL_ONLY":rare,
       "stage110_attention_by_all_42_complete_days":load,
       "research_gates":research_gates,
       "raw_scope_execution_gates":gates,
       "strategy_research_decision":(
           "HISTORICAL_G2_G3_AND_PRICE_ONLY_PASS_NOT_OOS_OR_REAL_NET"
           if all(research_gates.values())
           else "REJECTED_STAGE110_PRE_REGISTERED_HISTORICAL_GATES"),
       "future_OOS":"NOT_DONE",
       "real_executable_net_profit":"UNKNOWN",
       "actual_trading_and_gmail":"OFF",
       "frank":"UNCHANGED",
       "source_is_full_crypto_point_in_time":"PARTIAL",
       "monster_deployment":"NO_GO",
    }
    return out

def selftest():
    assert s110.SCHEMA.startswith("MONSTER_STAGE110")
    assert summary([])["gross_median_pct"] is None
    assert bucket_counts([])["complete_days"]==42
    assert bucket_counts([])["passes_avg5_and_peak12"]
    assert len(old.DATES)==6
    print("STAGE110_ALL519_D0_305_D1_AGGREGATOR_NO_GAP_42D_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--artifact-dir",type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    if args.selftest:selftest();return
    if not args.artifact_dir or not args.out:
        p.error("--artifact-dir --out required")
    rows,census=collect(args.artifact_dir)
    result=audit(rows,census)
    args.out.mkdir(parents=True,exist_ok=True)
    target=args.out/"monster_stage110_real519D0_305D1_causal_confirm_states.json"
    target.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE110_HISTORIC_MODEL_REAL_SHA_RESULTS "+json.dumps({
        "strategy":result["strategy_research_decision"],
        "states":result["state_count"],
        "g2":result["stage110_2x_early5_over_D0_28"],
        "attention":result["stage110_attention_by_all_42_complete_days"]["avg_per_day"],
        "peak":result["stage110_attention_by_all_42_complete_days"]["peak_per_day"],
        "gross":result["confirmed_24h_price_only_economics"]["gross_median_pct"],
        },sort_keys=True))

if __name__=="__main__":
    main()
