#!/usr/bin/env python3
"""Stage92 single-source G1/G2/G3 evaluation. No live action, no tuning or trading."""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path

try:
    import monster_v4_stage91_forward_oos_replay_gate as stage91
    from monster_v4_stage80_dual_entry_core import utc_ms
except ImportError:
    from scripts import monster_v4_stage91_forward_oos_replay_gate as stage91
    from scripts.monster_v4_stage80_dual_entry_core import utc_ms

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
STAGE83=E/"monster_stage83_all519_source_and_D1_result.jsonl"
PIN83="c76b3a137c8dbe56feed3a79a63adcc0752f5e2e"
HISTORIC_DATES=("2025-01-30","2025-06-02","2025-08-01",
                "2025-10-02","2026-06-21","2026-07-28")
SCHEMA="MONSTER_STAGE92_G1_G2_G3_FULLCOHORT_EVALUATOR_V1"
DAY_MS=24*3600000
MIN=60_000
VERIFIED="COMPLETE_SOURCE_9_DAYS_SHA_VERIFIED"
CENSORED="SOURCE_CENSORED_FUTURE_GT_UNSCORED"


def blob(raw:bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def exposed_history():
    raw=STAGE83.read_bytes()
    if blob(raw)!=PIN83:
        raise ValueError("STAGE92_HISTORIC_519_SOURCE_DRIFT")
    rows=[json.loads(x) for x in raw.decode().splitlines() if x.strip()]
    if len(rows)!=519 or len({(x["date"],x["symbol"]) for x in rows})!=519:
        raise ValueError("STAGE92_HISTORIC_519_NOT_COMPLETE")
    converted=[]
    for row in rows:
        if row["source_status"]!="COMPLETE_OFFICIAL_PREFIX_SHA_VERIFIED_3M_48H":
            raise ValueError("STAGE92_HISTORIC_G0_SOURCE_CHANGED")
        converted.append({
            "date":row["date"],"symbol":row["symbol"],
            "source_status":VERIFIED,
            "first_D0_utc":row["D0_FIRST_UTC"],
            "first_D1_utc":row["D1_FIRST_UTC"],
            "first_GT2x_high_utc":row["true_first_2x_HIGH_UTC_EVALUATION_ONLY"],
            "first_GT5x_high_utc":row["true_first_5x_HIGH_UTC_EVALUATION_ONLY"],
            "first_GT10x_high_utc":row["true_first_10x_HIGH_UTC_EVALUATION_ONLY"],
            "venue":"BINANCE_USDM",
            "point_in_time_crypto_only":"UNKNOWN"
        })
    return converted


def convert_raw_forward(result:dict)->dict:
    """Adapt exact Stage91 same-core result, not an independent strategy rewrite."""
    labels=result["gross_future_labels_not_real_profit"]
    return {
        "date":result["date"],"symbol":result["symbol"],
        "source_status": VERIFIED if result["source_status"].startswith("COMPLETE_REAL_1M_")
                         else CENSORED,
        "venue":result["venue"],
        "first_D0_utc":result["D0_first_UTC"],
        "first_D1_utc":result["D1_first_UTC"],
        **{f"first_GT{n}x_high_utc":labels[f"first_GT{n}x_HIGH_UTC_EVALUATION_ONLY"]
           for n in (2,5,10)},
        "point_in_time_crypto_only":result["Crypto_identity"],
    }


def early_strict(t, crossing) -> bool:
    return t is not None and crossing is not None and utc_ms(t)<utc_ms(crossing)


def early5(t,crossing) -> bool:
    return t is not None and crossing is not None and utc_ms(t)+5*MIN<=utc_ms(crossing)


def summarize(rows:list[dict], windows:tuple[str,...], *,
              scope_proof_complete:bool=False,
              full_window_listing_coverage:bool=False,
              forward:bool=False) -> dict:
    if not windows or len(set(windows))!=len(windows):
        raise ValueError("STAGE92_MISSING_OR_DUPLICATE_ANCHOR_DATES")
    starts={day:utc_ms(day+"T06:00:00Z") for day in windows}
    if forward and set(day+"T06:00:00Z" for day in windows)!=set(stage91.WINDOWS):
        raise ValueError("STAGE92_FORWARD_DATES_NOT_FROZEN")
    if not rows or len(rows)!=len({(x["date"],x["symbol"]) for x in rows}):
        raise ValueError("STAGE92_EMPTY_OR_DUPLICATE_COIN_DATE")
    for row in rows:
        if row["date"] not in starts or row["venue"]!="BINANCE_USDM":
            raise ValueError("STAGE92_MIXED_OR_UNFROZEN_MARKET")
        start,end=starts[row["date"]],starts[row["date"]]+7*DAY_MS
        if row["source_status"] not in (VERIFIED,CENSORED):
            raise ValueError("STAGE92_INVALID_SOURCE_STATUS")
        for key in ("first_D0_utc","first_D1_utc"):
            t=row.get(key)
            if t is not None and not start<=utc_ms(t)<end:
                raise ValueError("STAGE92_D0_D1_OUTSIDE_FROZEN_WINDOW")
        if row["first_D1_utc"] is not None and row["first_D0_utc"] is None:
            raise ValueError("STAGE92_D1_CANNOT_PRECEDE_ABSENT_D0")
        if row["first_D1_utc"] is not None and utc_ms(row["first_D1_utc"])<utc_ms(row["first_D0_utc"]):
            raise ValueError("STAGE92_D1_PRECEDES_FIRST_D0")
        for n in (2,5,10):
            k=f"first_GT{n}x_high_utc"
            cross=row.get(k)
            if row["source_status"]!=VERIFIED and cross is not None:
                raise ValueError("STAGE92_CENSORED_FUTURE_LABEL_MUST_BE_NULL")
            if cross is not None and not start<=utc_ms(cross)<end:
                raise ValueError("STAGE92_FUTURE_HIGH_OUTSIDE_LABEL_WINDOW")
    complete=[x for x in rows if x["source_status"]==VERIFIED]
    censored=[x for x in rows if x["source_status"]==CENSORED]
    gt2=[x for x in complete if x["first_GT2x_high_utc"] is not None]
    gt5=[x for x in complete if x["first_GT5x_high_utc"] is not None]
    gt10=[x for x in complete if x["first_GT10x_high_utc"] is not None]
    d0_strict=[x for x in gt2 if early_strict(x["first_D0_utc"],x["first_GT2x_high_utc"])]
    d0_5=[x for x in gt2 if early5(x["first_D0_utc"],x["first_GT2x_high_utc"])]
    d1_5=[x for x in d0_5 if early5(x["first_D1_utc"],x["first_GT2x_high_utc"])]
    day_buckets=Counter()
    for row in rows:
        d1=row["first_D1_utc"]
        if d1 is None:continue
        k=(row["date"],(utc_ms(d1)-starts[row["date"]])//DAY_MS)
        day_buckets[k]+=1
    full_daily=[
        {"date":date,"utc06_day_index":i,"D1_FIRST_UPGRADES":day_buckets[(date,i)]}
        for date in windows for i in range(7)
    ]
    d1_count=sum(x["D1_FIRST_UPGRADES"] for x in full_daily)
    n_days=7*len(windows)
    peak=max(x["D1_FIRST_UPGRADES"] for x in full_daily)
    gt2_windows=len({x["date"] for x in gt2})
    source_complete=len(censored)==0
    observed_only_threshold=bool(
        len(gt2)>=20 and gt2_windows>=3 and
        len(d0_strict)*100>=90*len(gt2) and len(d0_5)*100>=85*len(gt2))
    genuine_full_market=bool(forward and scope_proof_complete
                             and full_window_listing_coverage and source_complete)
    g1={"n_2x":len(gt2),"n_2x_windows":gt2_windows,
        "d0_strict_early":len(d0_strict),"d0_strict_early_fraction":(
          str(Decimal(len(d0_strict))/len(gt2)) if gt2 else None),
        "d0_early5":len(d0_5),"d0_early5_fraction":(
          str(Decimal(len(d0_5))/len(gt2)) if gt2 else None),
        "conditional_on_present_D0_population":not genuine_full_market,
        "observed_subcohort_thresholds_descriptive_only":observed_only_threshold,
        "research_thresholds_numerically_met":(
            observed_only_threshold if genuine_full_market else None)}
    g2={"eligible_d0_early5_2x":len(d0_5),"d1_early5_2x":len(d1_5),
        "d1_retained_fraction":str(Decimal(len(d1_5))/len(d0_5)) if d0_5 else None,
        "research_threshold_numerically_met":bool(
           len(d0_5)>0 and len(d1_5)*100>=80*len(d0_5)),
        "missed_symbol_dates":[{"date":x["date"],"symbol":x["symbol"]}
                 for x in d0_5 if x not in d1_5]}
    g3={"D1_first_upgrades":d1_count,"full_calendar_utc06_days":n_days,
        "daily_mean":str(Decimal(d1_count)/n_days),
        "daily_peak":peak,
        "research_thresholds_numerically_met":bool(
          d1_count<=5*n_days and peak<=12),
        "daily":full_daily}
    major={}
    for n,grp in ((5,gt5),(10,gt10)):
        major[f"{n}x"]={
            "n":len(grp),
            "d0_early5":sum(early5(x["first_D0_utc"],x[f"first_GT{n}x_high_utc"]) for x in grp),
            "d1_early5":sum(early5(x["first_D1_utc"],x[f"first_GT{n}x_high_utc"]) for x in grp)}
    historical_exposed=not forward
    verdict="NOT_DONE_FUTURE_SOURCE_NOT_PRESENT" if forward else "EXPOSED_HISTORICAL_ONLY"
    if forward:
        if not scope_proof_complete or not full_window_listing_coverage:
            verdict="BLOCKED_G0_POINT_IN_TIME_POPULATION_AND_LISTINGS"
        elif not source_complete:
            verdict="BLOCKED_G0_CENSORED_HISTORICAL_SOURCE"
        elif not (g1["research_thresholds_numerically_met"] and
                  g2["research_threshold_numerically_met"] and
                  g3["research_thresholds_numerically_met"]):
            verdict="REJECTED_G1_G2_OR_G3"
        else:
            verdict="G1_G2_G3_RESEARCH_MET_G4_REVIEW_STILL_BLOCKED"
    return {"schema":SCHEMA,"population":len(rows),"full_minute_verified":len(complete),
        "censored_source":len(censored),"historically_exposed":historical_exposed,
        "G0_point_in_time_market_listing_and_crypto_population_proven":scope_proof_complete,
        "G0_intrawindow_listings_and_status_changes_proven":full_window_listing_coverage,
        "G3_scope_note":"lower bound when source cohort contains WATCH-only symbols",
        "G1":g1,"G2":g2,"G3":g3,"G5_G10":major,
        "OOS_verdict":verdict,"D2_real_executable_net_pnl":"UNKNOWN",
        "other_AI_review":"NOT_DONE","deployment":"NO_GO",
        "gmail":"OFF","autotrade":"NO_GO","frank":"UNCHANGED"}


def selftest():
    old=exposed_history()
    output=summarize(old,HISTORIC_DATES,scope_proof_complete=False,forward=False)
    assert output["population"]==519
    assert output["full_minute_verified"]==519
    assert output["G1"]["conditional_on_present_D0_population"]
    assert output["G1"]["research_thresholds_numerically_met"] is None
    assert output["G1"]["observed_subcohort_thresholds_descriptive_only"]
    assert output["G2"]["eligible_d0_early5_2x"]==28
    assert output["G2"]["d1_early5_2x"]==27
    assert output["G3"]["D1_first_upgrades"]==305
    assert output["G3"]["full_calendar_utc06_days"]==42
    assert output["G3"]["daily_peak"]==52
    assert not output["G3"]["research_thresholds_numerically_met"]
    assert output["OOS_verdict"]=="EXPOSED_HISTORICAL_ONLY"
    assert len(output["G2"]["missed_symbol_dates"])==1
    assert output["G2"]["missed_symbol_dates"][0]["symbol"]=="SOONUSDT"
    changed=list(old)
    changed[0]=dict(changed[0],date="2026-10-14")
    try:
        summarize(changed,HISTORIC_DATES,forward=False)
    except ValueError as exc:
        assert "UNFROZEN" in str(exc)
    else:
        raise AssertionError("STAGE92_HISTORIC_COIN_DATE_RECLASSIFICATION_MUST_FAIL")
    try:
        summarize(old,HISTORIC_DATES,forward=True)
    except ValueError as exc:
        assert "FORWARD_DATES" in str(exc)
    else:
        raise AssertionError("STAGE92_HISTORIC_WINDOWS_MUST_NEVER_BE_VALID_FORWARD_OOS")
    print("STAGE92_EXPOSED_SOURCE519_ACTUAL_G2_27OF28_G3_305_PEAK52_REJECTED_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--audit-historical",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:
        selftest()
        return
    if not a.audit_historical:
        p.error("Stage92 only permits frozen historical regression or selftest; forward OOS not available")
    data=summarize(exposed_history(),HISTORIC_DATES,scope_proof_complete=False,forward=False)
    raw=json.dumps(data,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(raw,encoding="utf-8")
    print("STAGE92_EXPOSED_HISTORICAL_METRIC_REGRESSION "+json.dumps({
        "G1_2x":data["G1"]["n_2x"],
        "G2_eligible":data["G2"]["eligible_d0_early5_2x"],
        "G2_retained":data["G2"]["d1_early5_2x"],
        "G3_upgraded":data["G3"]["D1_first_upgrades"],
        "G3_daily_peak":data["G3"]["daily_peak"],
        "OOS":data["OOS_verdict"]},sort_keys=True))


if __name__=="__main__":
    main()
