#!/usr/bin/env python3
"""Stage96 frozen H1 future right-tail research: same D0/D1, real 12 daily SHA 1m.

All actions are offline read-only analysis; no scheduling, trading, email or monitoring.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
import time

try:
    import monster_v4_stage38_usdm_original_v4_1m_pilot as v4
    import monster_v4_stage80_dual_entry_core as d1
    import monster_v4_stage91_forward_oos_replay_gate as forward
    import monster_v4_stage88_d1_24h72h_official_paths as paths
    import monster_v4_stage94_d1_asof_vs_post_signal_return as historic
except ImportError:
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as v4
    from scripts import monster_v4_stage80_dual_entry_core as d1
    from scripts import monster_v4_stage91_forward_oos_replay_gate as forward
    from scripts import monster_v4_stage88_d1_24h72h_official_paths as paths
    from scripts import monster_v4_stage94_d1_asof_vs_post_signal_return as historic

SCHEMA = "MONSTER_STAGE96_H1_PRESIGNAL_D0_D1_PRICE_PROGRESS_TO_72H_TAIL_V1"
GIT_REGRESSION = "MONSTER_STAGE96_EXPOSED305_H1_PRESIGNAL_VS_POST72H_REGRESSION_V1"
FUTURE_WINDOW_DAYS = tuple(x[:10] for x in forward.WINDOWS)
DATES_REQUIRED = tuple(range(-1, 11))
FUTURE_BARS = v4.BARS + 3 * 1440
RIGHT_TAIL = Decimal("100")
SAMPLE_MIN = 20
DISTINCT_WINDOWS_MIN = 3
MIN = v4.MINUTE_MS
MAX_OFFICIAL_ZIP_DAYS = 12


def days_for(start: str):
    forward.verify_window(start)
    day = date.fromisoformat(start[:10])
    return [day+timedelta(days=k) for k in DATES_REQUIRED]


def checked_full_72h_source(symbol: str, window_start: str, *,
                            reader=v4.verified_1m_day, now_ms=None):
    """12 complete official dates, warmup 24h + 7-day model + 72h outcome."""
    forward.verify_window(window_start)
    days = days_for(window_start)
    cutoff = v4.msutc((days[-1]+timedelta(days=1)).isoformat()+"T00:00:00Z")
    if now_ms is None:
        now_ms=int(time.time()*1000)
    if now_ms < cutoff:
        raise ValueError("STAGE96_LAST_72H_HORIZON_NOT_CALENDAR_COMPLETE")
    all_bars=[]
    receipts=[]
    for day in days:
        candles,receipt=reader(symbol,day)
        if len(candles)!=1440 or not receipt.get("verified_official_publisher_SHA256") \
           or receipt.get("bars")!=1440 or receipt.get("date")!=day.isoformat() \
           or len(receipt.get("zip_sha256",""))!=64:
            raise ValueError("STAGE96_UNVERIFIED_OFFICIAL_DAY")
        start=v4.msutc(day.isoformat()+"T00:00:00Z")
        if any(x[0]!=start+i*MIN for i,x in enumerate(candles)):
            raise ValueError("STAGE96_OFFICIAL_MINUTE_GAP_OR_CLOCK_CONFLICT")
        all_bars.extend(candles)
        receipts.append(receipt)
    bars=all_bars[360:360+FUTURE_BARS]
    begin=forward.verify_window(window_start)-24*3600000
    if len(bars)!=FUTURE_BARS or any(x[0]!=begin+i*MIN for i,x in enumerate(bars)):
        raise ValueError("STAGE96_FULL_72H_CONTIGUOUS_TIMELINE_NOT_PRESENT")
    forward.source_ready(symbol,window_start,bars[:v4.BARS],receipts[:9])
    if len(receipts)!=12:
        raise ValueError("STAGE96_OFFICIAL_12_SHA_REQUIRED")
    return bars,receipts


def frozen_entry_features(bars, utc: str):
    t=d1.utc_ms(utc)
    base=bars[0][0]
    if (t-base)%MIN:
        raise ValueError("STAGE96_D0_D1_EVENT_NOT_ON_FULL_1M")
    i=(t-base)//MIN
    if i<61 or i>len(bars):
        raise ValueError("STAGE96_TOO_FEW_ALREADY_CLOSED_MINUTES")
    return d1.from_archived_closed_bars(bars[i-61:i],t)


def replay_extended(symbol, window_start: str, bars, receipts, *,
                    runner=v4.production_scan):
    """Only labels after the actual original stage79 D1; preserve NO-D1 case."""
    if len(bars)!=FUTURE_BARS or len(receipts)!=12:
        raise ValueError("STAGE96_INVALID_COMPLETE_12_DAY_INPUT")
    original=forward.replay_raw_symbol(symbol,window_start,
            bars[:v4.BARS],receipts[:9],runner=runner)
    answer={
        "schema":SCHEMA,"window_start_utc":window_start,"symbol":symbol,
        "date":window_start[:10], "venue":"BINANCE_USDM",
        "D0_first_UTC":original["D0_first_UTC"],
        "D1_first_UTC":original["D1_first_UTC"],
        "D1_entry_path":original["D1_entry_path"],
        "original_G1_G2_G5_G10":original["gross_future_labels_not_real_profit"],
        "original_D0_WATCH_count":original["D0_WATCH_COUNT"],
        "publisher_verified_daily_sha256":receipts,
        "official_complete_source_12days":True,
        "point_in_time_crypto_identity":"UNVERIFIED",
        "point_in_time_exchange_listing":"UNVERIFIED",
        "real_execution":"UNKNOWN",
        "user_notional":"UNSPECIFIED","oos":"NOT_DONE",
        "G3_existing_D1":"REJECTED_HISTORICAL_MODEL",
        "no_trade_or_notification":True,
    }
    if not original["D1_first_UTC"]:
        answer.update(H1_status="NOT_APPLICABLE_NO_D1",
                      H1_asof_D0_to_D1_progress_pct=None,
                      fixed_72h_gross_return_pct=None,
                      tail_ge100_after_D1_72h=None,
                      post_signal_h24=None,post_signal_h72=None)
        return answer
    if not original["D0_first_UTC"]:
        raise ValueError("STAGE96_D1_WITHOUT_D0")
    first=frozen_entry_features(bars,original["D0_first_UTC"])
    later=frozen_entry_features(bars,original["D1_first_UTC"])
    if first.closed_price is None or later.closed_price is None:
        raise ValueError("STAGE96_NO_VALID_CLOSED_PRICE")
    progress=(later.closed_price/first.closed_price-1)*100
    t=d1.utc_ms(original["D1_first_UTC"])
    barindex={x[0]:x for x in bars}
    entry=barindex.get(t+MIN)
    if entry is None or entry[5]<=0 or entry[6]<=0:
        answer.update(H1_status="CENSORED_NO_ACTUAL_ENTRY_MINUTE_TRADES",
                      H1_asof_D0_to_D1_progress_pct=str(progress),
                      fixed_72h_gross_return_pct=None,
                      tail_ge100_after_D1_72h=None,
                      post_signal_h24=None,post_signal_h72=None)
        return answer
    main_entry=entry[1]
    h24=paths.score_path(barindex,t,1440,main_entry)
    h72=paths.score_path(barindex,t,4320,main_entry)
    if h24["status"]!=paths.COMPLETE or h72["status"]!=paths.COMPLETE:
        raise ValueError("STAGE96_COMPLETE_12_OFFICIAL_DAYS_YET_POSTD1_PRICE_CENSORED")
    gross=Decimal(h72["fixed_exit_gross_return_pct"])
    answer.update(
        H1_status="COMPLETE_SHA_PRICE_ONLY_PROXY",
        H1_asof_D0_to_D1_progress_pct=str(progress),
        first_D0_preclosed_price=str(first.closed_price),
        first_D1_preclosed_price=str(later.closed_price),
        next_minute_open_price_only_entry=str(main_entry),
        fixed_72h_gross_return_pct=str(gross),
        tail_ge100_after_D1_72h=bool(gross>=RIGHT_TAIL),
        post_signal_h24=h24,
        post_signal_h72=h72,
    )
    return answer


def pairwise_auc(pos,neg):
    if not pos or not neg:
        return None
    score=sum(2 if Decimal(x["H1_asof_D0_to_D1_progress_pct"]) >
                     Decimal(y["H1_asof_D0_to_D1_progress_pct"]) else
              1 if Decimal(x["H1_asof_D0_to_D1_progress_pct"]) ==
                   Decimal(y["H1_asof_D0_to_D1_progress_pct"]) else 0
              for x in pos for y in neg)
    return str(Decimal(score)/(2*len(pos)*len(neg)))


def evaluate_h1(rows, window_starts=forward.WINDOWS, *,
                full_market_certified=False, exposed=False):
    """Never represent a sparse D1-tail cohort as complete full-market OOS."""
    dates={x[:10] for x in window_starts}
    if len(window_starts)!=len(dates) or any(x!=d+"T06:00:00Z"
                 for x,d in zip(window_starts,(x[:10] for x in window_starts))):
        raise ValueError("STAGE96_NONFROZEN_UTC06_WINDOWS")
    if not exposed and tuple(window_starts)!=forward.WINDOWS:
        raise ValueError("STAGE96_FUTURE_WINDOWS_CHANGED")
    if not rows or len(rows)!=len({(x["date"],x["symbol"]) for x in rows}):
        raise ValueError("STAGE96_DUPLICATE_OR_EMPTY_FORWARD_COHORT")
    if set(x["date"] for x in rows)!=dates:
        raise ValueError("STAGE96_MISSING_ONE_OF_THREE_FIXED_WINDOWS")
    valid=[]
    missing=0
    for row in rows:
        if row["date"] not in dates:
            raise ValueError("STAGE96_NONFROZEN_COHORT_DATE")
        if row["H1_status"]=="COMPLETE_SHA_PRICE_ONLY_PROXY":
            if (not row["D1_first_UTC"] or row["tail_ge100_after_D1_72h"] is None
                or row["H1_asof_D0_to_D1_progress_pct"] is None):
                raise ValueError("STAGE96_POSITIVE_LABEL_OR_ASOF_MISSING")
            valid.append(row)
        elif row["H1_status"]=="NOT_APPLICABLE_NO_D1":
            if row["D1_first_UTC"] is not None:
                raise ValueError("STAGE96_NO_D1_LABEL_LEAK")
        else:
            missing+=1
    pos=[x for x in valid if x["tail_ge100_after_D1_72h"]]
    neg=[x for x in valid if not x["tail_ge100_after_D1_72h"]]
    bydate={}
    eligible=[]
    for d in sorted(dates):
        ps=[x for x in pos if x["date"]==d]
        ns=[x for x in neg if x["date"]==d]
        auc=pairwise_auc(ps,ns)
        bydate[d]={"D1_scored":len(ps)+len(ns),"right_tail_ge100":len(ps),
                    "other_D1":len(ns),"within_window_pair_count":len(ps)*len(ns),
                    "same_date_auc":auc}
        if auc is not None:
            eligible.append(Decimal(auc))
    independent_positive_dates=sum(v["right_tail_ge100"]>0 for v in bydate.values())
    # Secondary robustness diagnosis only: DIRECT D1 starts at D0 so H1 progress
    # is mechanically zero; pooled AUC can partly reflect entry-path mixture.
    # This must NEVER replace the one preregistered overall H1 acceptance metric.
    entry_path_robustness={}
    for path in ("DIRECT_AT_FIRST_D0","REIGNITION_AFTER_D0"):
        part=[x for x in valid if x.get("D1_entry_path")==path]
        p=[x for x in part if x["tail_ge100_after_D1_72h"]]
        n=[x for x in part if not x["tail_ge100_after_D1_72h"]]
        per_date={}
        for d in sorted(dates):
            one=[x for x in p if x["date"]==d]
            other=[x for x in n if x["date"]==d]
            per_date[d]={"positive":len(one),"control":len(other),
                         "auc":pairwise_auc(one,other)}
        filled=[Decimal(x["auc"]) for x in per_date.values() if x["auc"] is not None]
        entry_path_robustness[path]={
          "n":len(part),"positive":len(p),"negative":len(n),
          "global_auc":pairwise_auc(p,n),
          "same_date_equal_date_auc":str(sum(filled)/len(filled)) if filled else None,
          "positive_date_count":sum(v["positive"]>0 for v in per_date.values()),
          "per_date":per_date,
          "posthoc_secondary_diagnostic_not_primary_H1":True,
        }
    threshold_sufficient=(len(pos)>=SAMPLE_MIN and independent_positive_dates>=DISTINCT_WINDOWS_MIN)
    if not full_market_certified and not exposed:
        outcome="BLOCKED_G0_FULL_CRYPTO_UNIVERSE_AND_LISTINGS_UNVERIFIED"
    elif missing:
        outcome="BLOCKED_MISSING_SOURCE_DO_NOT_TREAT_AS_NEGATIVES"
    elif not threshold_sufficient:
        outcome="UNDERPOWERED_NOT_VALIDATED"
    else:
        outcome="RESEARCH_H1_SCORABLE_BUT_G2_G3_G4_REVIEW_NOT_PASSED"
    return {
        "schema":"MONSTER_STAGE96_H1_FROZEN_FORWARD_EVALUATOR_V1",
        "old_exposed_regression":exposed,
        "fixed_window_dates":sorted(dates),
        "raw_symbol_date_attempts_present":len(rows),
        "D1_source_complete_with72h":len(valid),
        "source_censored":missing,
        "right_tail_72h_ge100":len(pos),
        "non_tail_D1":len(neg),
        "right_tail_positive_distinct_dates":independent_positive_dates,
        "min_positive_required":SAMPLE_MIN,
        "min_independent_window_dates_required":DISTINCT_WINDOWS_MIN,
        "global_auc_not_for_decision":pairwise_auc(pos,neg),
        "within_date_macro_auc":(
            str(sum(eligible)/len(eligible)) if eligible else None),
        "same_date_auc_by_window":bydate,
        "entry_path_robustness_exposed_or_forward_descriptive_only":entry_path_robustness,
        "sufficient_statistical_support":threshold_sufficient,
        "G0_full_market_crypto_population_complete":full_market_certified,
        "H1_verdict":outcome,
        "future_prediction_claim":"NONE",
        "retuned_old_D0_D1":"NO",
        "real_executable_net_pnl":"UNKNOWN",
        "OOS":"NOT_DONE","other_ai_review":"NOT_DONE",
        "deployment":"NO_GO","gmail":"OFF","autotrade":"NO_GO","frank":"UNCHANGED",
    }


def historical_regression():
    """Read old *exposed* 305 only as a mathematical test: never fresh OOS."""
    pairs=historic.read()
    rows=[]
    for observed,post in pairs:
        ret=Decimal(post["h72"]["fixed_exit_gross_return_pct"])
        rows.append({
            "date":observed["date"],"symbol":observed["symbol"],
            "D1_first_UTC":observed["D1_FIRST_UTC"],
            "D1_entry_path":observed["D1_PATH"],
            "H1_status":"COMPLETE_SHA_PRICE_ONLY_PROXY",
            "H1_asof_D0_to_D1_progress_pct":
                observed["asof_D1_ret_from_first_D0_pct"],
            "tail_ge100_after_D1_72h":ret>=RIGHT_TAIL,
        })
    out=evaluate_h1(rows,
        tuple(d+"T06:00:00Z" for d in historic.DATES),
        full_market_certified=False,exposed=True)
    if (out["D1_source_complete_with72h"]!=305
        or out["right_tail_72h_ge100"]!=5
        or out["right_tail_positive_distinct_dates"]!=4
        or abs(Decimal(out["within_date_macro_auc"])-
               Decimal("0.8724989450204967446346756692"))>Decimal("0.000000000000001")):
        raise ValueError("STAGE96_STAGE94_EXPOSED_FROZEN5_AND_AUC_CHANGED")
    groups=out["entry_path_robustness_exposed_or_forward_descriptive_only"]
    if (groups["DIRECT_AT_FIRST_D0"]["n"]!=164
        or groups["DIRECT_AT_FIRST_D0"]["positive"]!=1
        or groups["REIGNITION_AFTER_D0"]["n"]!=141
        or groups["REIGNITION_AFTER_D0"]["positive"]!=4):
        raise ValueError("STAGE96_STAGE94_PATH_STRATA_164_141_OR_TAILS_CHANGED")
    out["H1_verdict"]="EXPOSED_MATH_REGRESSION_NOT_PREDICTIVE"
    out["exposed_source_blobs"]=historic.PINS
    return out


def selftest():
    assert len(DATES_REQUIRED)==12 and FUTURE_BARS==15840
    assert len(days_for(forward.WINDOWS[0]))==12
    ref=forward.WINDOWS[0]
    start=forward.verify_window(ref)
    early=15984 # synthetic irrelevant anchor
    try:
        checked_full_72h_source("CATUSDT",ref,now_ms=start)
    except ValueError as ex:
        assert "NOT_CALENDAR_COMPLETE" in str(ex)
    else:
        raise AssertionError("STAGE96_SHOULD_BLOCK_EARLY_FINALIZATION")
    # Test scoring without any IO; no future archive can be assumed.
    def row(d,s,progress,is_tail):
        return {"date":d,"symbol":s,"D1_first_UTC":d+"T10:00:00Z",
                "H1_status":"COMPLETE_SHA_PRICE_ONLY_PROXY",
                "H1_asof_D0_to_D1_progress_pct":str(progress),
                "tail_ge100_after_D1_72h":is_tail}
    demo=[]
    for d in FUTURE_WINDOW_DAYS:
        demo.extend([row(d,"WUSDT",4,False),row(d,"XUSDT",8,True)])
    under=evaluate_h1(demo,full_market_certified=True)
    assert under["right_tail_72h_ge100"]==3
    assert under["H1_verdict"]=="UNDERPOWERED_NOT_VALIDATED"
    assert under["within_date_macro_auc"]=="1"
    assert evaluate_h1(demo)["H1_verdict"]=="BLOCKED_G0_FULL_CRYPTO_UNIVERSE_AND_LISTINGS_UNVERIFIED"
    regression=historical_regression()
    assert regression["H1_verdict"]=="EXPOSED_MATH_REGRESSION_NOT_PREDICTIVE"

    # Synthetic publisher days: verify the SAME Stage91 original V4/D1 core,
    # as-of price progress, and genuinely later delayed-entry 72h exit path.
    start_ms=forward.verify_window(ref)
    begin=start_ms-24*3600000
    d0_idx=v4.WARMUP+3
    synthetic=[]
    for i in range(FUTURE_BARS):
        last15=d0_idx-15<=i<d0_idx
        preclosed_price=Decimal("110") if last15 else Decimal("100")
        q=Decimal("150000") if last15 else Decimal("50000")
        n=1000 if last15 else 300
        synthetic.append((begin+i*MIN,Decimal("100"),
                 max(Decimal("100"),preclosed_price),Decimal("100"),
                 preclosed_price,q,n))
    receipts=[
      {"date":d.isoformat(),"zip_sha256":"a"*64,
       "verified_official_publisher_SHA256":True,"bars":1440}
      for d in days_for(ref)
    ]
    first_at=v4.stamp(start_ms+3*MIN)
    def scanner(_symbol,_date,_bars):
        return {"polls":3360,"WATCH_UTC":[first_at],
                "watch_count":1,"SETUP_UTC":[],"setup_count":0}
    basecase=replay_extended("CATUSDT",ref,synthetic,receipts,runner=scanner)
    assert basecase["D0_first_UTC"]==first_at
    assert basecase["D1_first_UTC"]==first_at
    assert basecase["D1_entry_path"]=="DIRECT_AT_FIRST_D0"
    assert basecase["H1_status"]=="COMPLETE_SHA_PRICE_ONLY_PROXY"
    assert basecase["H1_asof_D0_to_D1_progress_pct"]=="0"
    assert basecase["tail_ge100_after_D1_72h"] is False
    changed=list(synthetic)
    exit_idx=d0_idx+4320
    old=changed[exit_idx]
    changed[exit_idx]=(old[0],old[1],Decimal("300"),old[3],
                       Decimal("300"),old[5],old[6])
    # This is a synthetic after-the-fact higher price, not an entry selector.
    upgraded=replay_extended("CATUSDT",ref,changed,receipts,runner=scanner)
    assert upgraded["D1_first_UTC"]==first_at
    assert upgraded["H1_asof_D0_to_D1_progress_pct"]==basecase["H1_asof_D0_to_D1_progress_pct"]
    assert upgraded["tail_ge100_after_D1_72h"] is True
    assert Decimal(upgraded["fixed_72h_gross_return_pct"])>=RIGHT_TAIL
    def none_scanner(_symbol,_date,_bars):
        return {"polls":3360,"WATCH_UTC":[],"watch_count":0,
                "SETUP_UTC":[],"setup_count":0}
    no_d1=replay_extended("CATUSDT",ref,synthetic,receipts,runner=none_scanner)
    assert no_d1["H1_status"]=="NOT_APPLICABLE_NO_D1"
    assert no_d1["tail_ge100_after_D1_72h"] is None
    print("STAGE96_FROZEN_H1_12SHA_DAY_SYNTHETIC_SAME_CORE_D1_72H_FUTURE_INVARIANCE_AND_OLD305_REGRESSION_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--historical-regression",action="store_true")
    p.add_argument("--window")
    p.add_argument("--symbol")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:
        selftest()
        return
    if a.historical_regression:
        result=historical_regression()
    elif a.window and a.symbol:
        forward.verify_window(a.window)
        bars,receipts=checked_full_72h_source(a.symbol,a.window)
        result=replay_extended(a.symbol,a.window,bars,receipts)
    else:
        p.error("choose --selftest, --historical-regression, or --window plus --symbol")
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE96_H1_72H_CAUSAL_REPORT "+json.dumps({
        key:result[key] for key in ("H1_verdict","D1_source_complete_with72h",
                "right_tail_72h_ge100","within_date_macro_auc","H1_status",
                "H1_asof_D0_to_D1_progress_pct","fixed_72h_gross_return_pct")
        if key in result},sort_keys=True))


if __name__=="__main__":
    main()
