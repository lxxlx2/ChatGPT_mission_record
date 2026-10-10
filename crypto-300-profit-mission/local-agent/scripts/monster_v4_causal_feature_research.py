#!/usr/bin/env python3
"""Purely exploratory research on frozen official historical 1m features.

Uses ONLY prior closed bars at each 3m decision time; volume-ratio median
comes from 23 PREVIOUS completed hours, excluding current last 60 minutes.
No changes to production V4 rules. Thresholds are exposed to hindsight,
therefore these are NOT independently validated investment rules.
"""
import json
import statistics
from collections import Counter
from decimal import Decimal
from pathlib import Path

try:
    from monster_v4_historical_replay import EVIDENCE, load_case, utc
except ImportError:
    from scripts.monster_v4_historical_replay import EVIDENCE, load_case, utc

RULES={
    "R60_3_VOL4":{"return_window":60,"ret_pct":Decimal("3"),"vol_ratio":Decimal("4")},
    "R60_5_VOL2":{"return_window":60,"ret_pct":Decimal("5"),"vol_ratio":Decimal("2")},
    "R15_2_VOL8":{"return_window":15,"ret_pct":Decimal("2"),"vol_ratio":Decimal("8")},
    "R240_8_VOL2":{"return_window":240,"ret_pct":Decimal("8"),"vol_ratio":Decimal("2")},
}
COOLDOWN_MS=6*3600_000
def features_for_case(src,bars):
    pref=[Decimal(0)]
    for row in bars:
        pref.append(pref[-1]+row[5])
    anchor=int(__import__("datetime").datetime.fromisoformat(
        src["old_watch_utc"].replace("Z","+00:00")).timestamp()*1000)
    found={}
    triggering_events={rule:[] for rule in RULES}
    counts={rule:0 for rule in RULES}
    for i in range(1442,2160,3):
        if bars[i][6] == 0 or bars[i][5] == 0:
            continue
        q24=pref[i+1]-pref[i+1-1440]
        if q24<Decimal("100000"):
            continue
        current_hour=pref[i+1]-pref[i+1-60]
        previous_hours=[
            pref[i+1-60-h*60]-pref[i+1-60-(h+1)*60]
            for h in range(23)]
        m=statistics.median(previous_hours)
        if m<=0:
            continue
        ratio=current_hour/m
        for name,config in RULES.items():
            window=config["return_window"]
            prior=bars[i-window][4]
            if prior<=0:
                continue
            ret=(bars[i][4]/prior-1)*100
            if ret>=config["ret_pct"] and ratio>=config["vol_ratio"]:
                counts[name]+=1
                observed=bars[i][0]+60000
                if name not in found:
                    found[name]={"first_utc":utc(observed),
                        "lead_hours_before_old_watch":round((anchor-observed)/3600000,3),
                        "last_hour_turnover_ratio":round(float(ratio),4),
                        "price_return_pct":round(float(ret),4)}
                previous=triggering_events[name][-1] if triggering_events[name] else None
                if previous is None or observed-previous>=COOLDOWN_MS:
                    triggering_events[name].append(observed)
    return {"symbol":src["symbol"],"venue":src["venue"],"cohort":src["cohort"],
            "old_watch_utc":src["old_watch_utc"],
            "rules":{r:{"triggers_at_3m_resolution":counts[r],
                        "first":found.get(r),
                        "cooldown_filtered_watch_count":len(triggering_events[r])}
                     for r in RULES}}


def research(paths=None):
    if paths is None:
        paths=sorted(EVIDENCE.glob("monster_v4_replay_1m_*.json"))
    cases=[];skipped=[]
    for path in paths:
        try:
            src,bars=load_case(path)
        except ValueError as exc:
            skipped.append({"file":Path(path).name,"reason":str(exc)[:80]})
            continue
        cases.append(features_for_case(src,bars))
    summary={}
    for name in RULES:
        d={}
        for cohort in ("FULLMARKET_SAMPLED","GT5X_PREHIT_POSITIVE"):
            group=[x for x in cases if x["cohort"]==cohort]
            first=[x["rules"][name]["first"] for x in group]
            detected=[x for x in first if x]
            before=sum(x["lead_hours_before_old_watch"]>=0 for x in detected)
            after=sum(x["lead_hours_before_old_watch"]<0 for x in detected)
            d[cohort]={"n":len(group),"detected":len(detected),
                       "before_old_watch":before,"after_old_watch":after,
                       "not_detected":len(group)-len(detected),
                       "all_rule_events":sum(
                           x["rules"][name]["cooldown_filtered_watch_count"] for x in group)}
        summary[name]=d
    return {"analysis_type":"EXPLORATORY_ONLY_CAUSAL_1M_FEATURE_COMPARISON",
            "frozen_historical_event_cases":len(cases),"cases_excluded":len(skipped),
            "source":"OFFICIAL_BINANCE_1M_CANDLES_IN_GIT",
            "rules":{k:{"return_window_min":v["return_window"],
                        "return_threshold_pct":str(v["ret_pct"]),
                        "last60m_quote_vs_prev23h_median":str(v["vol_ratio"])}
                     for k,v in RULES.items()},
            "thresholds_pre_exposed_to_2021_2026_data":True,
            "independent_unseen_holdout":False,
            "false_positive_rate_unknown_in_general_universe":True,
            "summary":summary,"skipped":skipped,"cases":cases}


def main():
    print(json.dumps(research(),indent=2,sort_keys=True))


if __name__=="__main__":
    main()
