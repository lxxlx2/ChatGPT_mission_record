#!/usr/bin/env python3
"""Stage118 single frozen price OR flow model -> all519 asof provenance audit.
Same pure rule can be invoked with Stage56 official closed 1m taker record.
Historical 2x is ONLY after-the-fact evaluation, never an input.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
from decimal import Decimal
import json
from pathlib import Path
from statistics import median

try:
    import monster_v4_stage118_first_d0_dual_lane_flow_core as core
    import monster_v4_stage117_original519_first_d0_audit as prior
except ImportError:
    from scripts import monster_v4_stage118_first_d0_dual_lane_flow_core as core
    from scripts import monster_v4_stage117_original519_first_d0_audit as prior

E=prior.E
PRIOR114=E/"monster_stage114_real519_d0_d1_priority_paired_entry_actual.json"
PIN114="de64a09ff4f8b35009fd1ff71a284542fd5de5ac"
SCHEMA="MONSTER_STAGE118_PRICE_OR_FLOW_FIRST_D0_519_ACTUAL_EXPOSED_V1"
D=Decimal


def descript(vals):
    s=sorted(vals)
    return {
        "valid_complete_price_proxy":len(s),
        "positive_count":sum(x>0 for x in s),
        "nonpositive_count":sum(x<=0 for x in s),
        "price_only_gross_median_pct":str(median(s)) if s else None,
        "theoretical_20bps_per_side_price_median_pct":
            str(median([((1+v/100)*D("0.998")/D("1.002")-1)*100 for v in s]))
            if s else None,
        "gross_loss20pct_or_worse_count":sum(x<=-20 for x in s),
        "gross_gain100pct_or_more_count":sum(x>=100 for x in s),
        "true_orderbook_real_net":"UNKNOWN",
    }


def frozen_sources():
    src,old=prior.load()
    raw=PRIOR114.read_bytes()
    if prior.git_blob(raw)!=PIN114:
        raise ValueError("STAGE118_STAGE114_REAL_PRICE_GIT_SOURCE_DRIFT")
    records=json.loads(raw)["all_519_original_cases"]
    by={(r["date"],r["symbol"]):r for r in records}
    if len(by)!=519 or len(records)!=519:
        raise ValueError("STAGE118_STAGE114_ORIGINAL519_COIN_DATE_DRIFT")
    if {(r["date"],r["symbol"]) for r in src}!=set(by):
        raise ValueError("STAGE118_PRICE_SOURCE_COHORT_DIFFERENT")
    return src,old,by


def run():
    src,old,price=frozen_sources()
    rows=[]
    stats=Counter()
    categories=Counter()
    anchor=Counter()
    days=Counter()
    date_prices=defaultdict(list)
    lane_prices=defaultdict(list)
    lane_censor=Counter()
    seen=set()
    misses=[]
    for r in sorted(src,key=lambda q:(q["date"],q["symbol"])):
        key=(r["date"],r["symbol"])
        first=old[key]
        if r["first_D0_UTC"]!=first["D0_FIRST_UTC"]:
            raise ValueError("STAGE118_ORIGINAL_D0_EVENT_TIME_CHANGED")
        if r["source_status"]!="COMPLETE_OFFICIAL_DAILY_USDM_61M_PUBLISHER_SHA_NO_FUTURE":
            raise ValueError("STAGE118_MISSING_REAL_ASOF_61M_SOURCE")
        if not r["publisher_SHA_receipts"] or any(
            not p["checksum_verified"] or len(p["official_zip_sha256"])!=64
            for p in r["publisher_SHA_receipts"]):
            raise ValueError("STAGE118_SOURCE_PUBLISHER_CHECKSUM_MISSING")
        p=price[key]
        if p["date"]!=r["date"] or p["symbol"]!=r["symbol"] or p["D1_chronology"] not in (
            "NONE","NO_PRIORITY","D1_BEFORE_PRIORITY","D1_AFTER_PRIORITY","D1_EQUALS_PRIORITY"):
            raise ValueError("STAGE118_STAGE114_PRICE_CASE_BAD_ORIGINAL_ID")
        v=core.evaluate_first_d0(venue="USDM",symbol=r["symbol"],
              first_d0_utc=r["first_D0_UTC"],asof=r["features_ASOF_ONLY"])
        if v["event_id"] in seen:
            raise ValueError("STAGE118_GLOBAL_EVENT_ID_COLLISION")
        seen.add(v["event_id"])
        price_lane=v["PRICE_unchanged_Stage117_lane"]
        fast=v["fast_attention"]
        stats["D0_all"]+=1
        stats["new_early_attention"]+=int(fast)
        stats["prior_Stage117_price_attention"]+=int(price_lane)
        stats["flow_qualified"]+=int(v["FLOW_new_taker_buy_lane"])
        stats["flow_only_added"]+=int(fast and not price_lane)
        early=bool(first["D0_at_least_5m_before_2x"])
        if early and first["true_first_2x_HIGH_UTC_EVALUATION_ONLY"] is None:
            raise ValueError("STAGE118_EARLY_GT2_NO_ASOF_LABEL_TIME")
        stats["orig_D0_early2x_5min"]+=int(early)
        stats["new_fast_early2x_5min"]+=int(fast and early)
        stats["prior_price_early2x_5min"]+=int(price_lane and early)
        stats["D1_present"]+=int(first["D1_FIRST_UTC"] is not None)
        categories[v["decision"]]+=1
        t=prior.utc_ms(r["first_D0_UTC"])
        start=prior.utc_ms(r["date"]+"T06:00:00Z")
        bucket=(t-start)//86_400_000
        if not 0<=bucket<7:
            raise ValueError("STAGE118_D0_NOT_IN_SIX_ANCHOR_WEEK")
        days[(r["date"],bucket)]+=int(fast)
        anchor[r["date"]]+=int(fast)
        if early and not fast:
            misses.append({"date":r["date"],"symbol":r["symbol"],
                "D0_UTC":r["first_D0_UTC"],
                "future_GT2_UTC_EVALUATION_ONLY":
                    first["true_first_2x_HIGH_UTC_EVALUATION_ONLY"],
                "price_only_asof_original":r["features_ASOF_ONLY"]["ret60_pct"],
                "flow_taker_buy15":r["features_ASOF_ONLY"]["taker_buy_share15"],
                "flow_taker_buy60":r["features_ASOF_ONLY"]["taker_buy_share60"]})
        prices=p["entry_price_proxy_gross_by_horizon"]["D0"]
        if set(prices)!={"5","1440"}:
            raise ValueError("STAGE118_ORIGINAL_D0_PRICE_PROXY_HORIZON_DRIFT")
        for h in ("5","1440"):
            if prices[h] is not None:
                val=D(prices[h])
                if not val.is_finite():raise ValueError("STAGE118_NONFINITE_PRICE_PROXY")
                lane_prices[v["decision"]+"|"+h].append(val)
                if fast:
                    lane_prices["ALL_NEW_ATTENTION|"+h].append(val)
                date_prices[r["date"]+"|"+v["decision"]+"|"+h].append(val)
            else:
                lane_censor[v["decision"]+"|"+h]+=1
                if fast:lane_censor["ALL_NEW_ATTENTION|"+h]+=1
        rows.append({
            "date":r["date"],"symbol":r["symbol"],
            "original_D0_UTC":r["first_D0_UTC"],
            "decision":v,
            "source_SHA":r["publisher_SHA_receipts"],
            "original_stage83_first_D1_UTC":first["D1_FIRST_UTC"],
            "original_D0_early2x5m_EVALUATION_ONLY":early,
            "original_GT2_UTC_EVALUATION_ONLY":
                first["true_first_2x_HIGH_UTC_EVALUATION_ONLY"],
            "D0_5m_24h_gross_price_proxy_ONLY":prices,
            "original_crypto_identity_UNVERIFIED":first["identity"],
            "true_executable_net":"UNKNOWN",
        })
    if (len(rows)!=519 or stats["D0_all"]!=519
        or stats["prior_Stage117_price_attention"]!=164
        or stats["orig_D0_early2x_5min"]!=28
        or stats["prior_price_early2x_5min"]!=17
        or stats["D1_present"]!=305
        or len(misses)+stats["new_fast_early2x_5min"]!=28):
        raise ValueError("STAGE118_ORIGINAL_PRIOR_519_OR_17_28_SOURCE_DRIFT")
    buckets=[days[(date,i)] for date in prior.DATES for i in range(7)]
    total=sum(buckets)
    if total!=stats["new_early_attention"]:
        raise ValueError("STAGE118_42DAY_NOTIFICATION_COUNT_DRIFT")
    recall=stats["new_fast_early2x_5min"]*100>=28*80
    load=total<=42*5 and max(buckets)<=12
    if not recall:status="REJECTED_HISTORICAL_EARLY_2X_RECALL"
    elif not load:status="REJECTED_HISTORICAL_DAILY_ATTENTION_BURDEN"
    else:status="HISTORICALLY_PASSES_RAW_G2_G3_OOS_AND_REAL_NET_UNPROVEN"
    allprices={
        key:{**descript(vals),"censored_price_proxy":lane_censor[key]}
        for key,vals in sorted(lane_prices.items())}
    # Return explicitly empty profiles for no valid sample; not zero returns.
    for k in categories:
        for h in ("5","1440"):
            name=k+"|"+h
            allprices.setdefault(name,{**descript([]),
                                       "censored_price_proxy":lane_censor[name]})
    summary={
        "schema":SCHEMA,
        "research_decision":status,
        "source_frozen_stage64_blob":prior.PIN64,
        "source_frozen_stage83_blob":prior.PIN83,
        "source_stage114_fixed_price_blob":PIN114,
        "complete_original_D0":stats["D0_all"],
        "previous_stage117_first_price_path":stats["prior_Stage117_price_attention"],
        "previous_stage117_first_price_early2x5m":stats["prior_price_early2x_5min"],
        "new_two_lane_first_D0_attention":stats["new_early_attention"],
        "flow_only_extra_attention":stats["flow_only_added"],
        "flow_qualified_all":stats["flow_qualified"],
        "original_D0_early2x5m":28,
        "new_D0_fast_early2x5m":stats["new_fast_early2x_5min"],
        "G2_original_D0_right_tail_recall_pct":str(D(stats["new_fast_early2x_5min"])*100/D(28)),
        "G2_historical_raw_80pct":recall,
        "G3_historical_raw_mean_42_days":str(D(total)/D(42)),
        "G3_historical_raw_peak_day":max(buckets),
        "G3_historical_raw_5_12":load,
        "full_42_UTC06_day_attention_bins":buckets,
        "first_D0_attention_per_original_anchor":dict(sorted(anchor.items())),
        "first_D0_lane_counts":dict(sorted(categories.items())),
        "original_11_Stage117_losses_now_remaining_major_misses":
            sorted(misses,key=lambda x:(x["date"],x["symbol"])),
        "real_original_D0_price5m_24h_lanes_PRICE_ONLY":allprices,
        "per_original_anchor_date_per_lane_24h_price_ONLY":{
            key:{**descript(vals),"censored_not_assumed_loss":True}
            for key,vals in sorted(date_prices.items()) if key.endswith("|1440")},
        "unclassified_crypto_and_contract_units":"STILL_UNKNOWN",
        "original_D1_pop":305,
        "historical_labels_used_only_for_posthoc_evaluation":True,
        "new_OOS":"NOT_DONE",
        "real_venue_BID_ASK_depth_cost_net":"UNKNOWN",
        "other_AI_independent_review":"NOT_DONE",
        "Monster_deployment":"NO_GO",
    }
    return summary,rows


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--out",type=Path)
    p.add_argument("--cases",type=Path)
    a=p.parse_args()
    if a.selftest:
        assert prior.git_blob(b"test")=="30d74d258442c7c65512eafab474568dd706c430"
        core.selftest()
        print("STAGE118_ALL519_REAL_OFFICIAL_INPUT_FORMAT_SELFTEST_PASS")
        return
    if a.out is None or a.cases is None:p.error("--out --cases required")
    val,rows=run()
    for dest in (a.out,a.cases):dest.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(val,indent=2,sort_keys=True)+"\n")
    a.cases.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows))
    print("STAGE118_FULL519_REAL_EXPOSED_TRUTH "+json.dumps(
        {k:v for k,v in val.items() if k not in (
            "real_original_D0_price5m_24h_lanes_PRICE_ONLY",
            "per_original_anchor_date_per_lane_24h_price_ONLY",
            "original_11_Stage117_losses_now_remaining_major_misses",
            "full_42_UTC06_day_attention_bins")},sort_keys=True))


if __name__=="__main__":
    main()
