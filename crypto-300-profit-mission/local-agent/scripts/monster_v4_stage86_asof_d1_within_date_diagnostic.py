#!/usr/bin/env python3
"""Stage86 label-open descriptive full305 as-of feature separability; NOT predictive OOS."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
from decimal import Decimal
from pathlib import Path

try:
    from monster_v4_stage80_dual_entry_core import sha_blob, decimal
except ImportError:
    from scripts.monster_v4_stage80_dual_entry_core import sha_blob, decimal

E = Path(__file__).resolve().parents[2] / "monster/evidence"
SOURCE=E/"monster_stage85_all305_official_D1_asof_features.jsonl"
PIN="622299fec16400e189cb8fa668ecbc8bc31ec630"
SCHEMA="MONSTER_STAGE86_EXPOSED_ALL305_SAME_DATE_D1_FEATURE_DIAGNOSTIC_V1"
FEATURES={
    "ret60_pct":"asof_D1_ret60_pct",
    "quote15_USDT":"asof_D1_quote15_USDT",
    "trade15":"asof_D1_trade15",
    "normalized_quote15_prev45":"asof_D1_normalized_quote15_prev45",
    "relative_from_first_D0_pct":"asof_D1_ret_from_first_D0_pct",
    "delay_since_first_D0_minutes":"from_first_d0_delay_minutes",
}

def load():
    raw=SOURCE.read_bytes()
    if sha_blob(raw)!=PIN:
        raise ValueError("STAGE86_STAGE85_PUBLISHER_SOURCE_BLOB_CHANGED")
    rows=[json.loads(s) for s in raw.decode().splitlines() if s.strip()]
    if len(rows)!=305 or len({(x["date"],x["symbol"]) for x in rows})!=305:
        raise ValueError("STAGE86_FULL305_SOURCE_MISSING")
    if any(x["source_status"]!="COMPLETE_OFFICIAL_BINANCE_SHA_ASOF_D1" for x in rows):
        raise ValueError("STAGE86_NOT_ALL305_OFFICIAL_SOURCE")
    if sum(x["early5_gt2_evaluation_only"] for x in rows)!=27 or sum(
        x["calendar_2x_evaluation_only"] for x in rows)!=28:
        raise ValueError("STAGE86_HISTORIC_GT2_COHORT_CHANGED")
    return rows

def pairwise_auc(pos: list[Decimal],negative: list[Decimal]):
    if not pos or not negative:return None
    wins=sum((2 if p>n else 1 if p==n else 0) for p in pos for n in negative)
    return {"pairs":len(pos)*len(negative),
            "auc":round(wins/(2*len(pos)*len(negative)),6),
            "positive_count":len(pos),"negative_count":len(negative)}

def eval_features(items, positives, negatives):
    result={}
    for name,key in FEATURES.items():
        result[name]=pairwise_auc([decimal(x[key]) for x in positives],
                                  [decimal(x[key]) for x in negatives])
    return result

def audit(rows):
    # All historic 2x with D1 after 2x are excluded from the early-positive vs non2x control comparison.
    positive=[x for x in rows if x["early5_gt2_evaluation_only"]]
    controls=[x for x in rows if not x["calendar_2x_evaluation_only"]]
    posthigh=[x for x in rows if x["calendar_2x_evaluation_only"] and not x["early5_gt2_evaluation_only"]]
    if (len(positive),len(controls),len(posthigh))!=(27,277,1):
        raise ValueError("STAGE86_NO_REAL_ALL305_CONTRAST")
    global_metrics=eval_features(rows,positive,controls)
    dates=sorted(set(x["date"] for x in rows))
    per_date={}
    eligible_dates=[]
    for d in dates:
        winners=[x for x in positive if x["date"]==d]
        normals=[x for x in controls if x["date"]==d]
        per_date[d]={
            "early5_2x":len(winners),"non2x_controls":len(normals),
            "d1_candidates":sum(x["date"]==d for x in rows),
            "asof_feature_auc":eval_features(rows,winners,normals)}
        if winners and normals:eligible_dates.append(d)
    macro={}
    for name in FEATURES:
        by_date=[per_date[d]["asof_feature_auc"][name] for d in eligible_dates]
        macro[name]={
            "eligible_dates":len(by_date),
            "macro_equal_date_auc":round(sum(x["auc"] for x in by_date)/len(by_date),6)
            if by_date else None,
            "date_pair_pooled_auc":round(
                sum(x["auc"]*x["pairs"] for x in by_date)/sum(x["pairs"] for x in by_date),6)
            if by_date else None,
            "date_auc_values":{d:per_date[d]["asof_feature_auc"][name]["auc"]
                               for d in eligible_dates}
        }
    all_2x=Counter(x["date"] for x in positive)
    return {"schema":SCHEMA,"source_git_blob":PIN,"source_total":305,
       "label_definition":"historic calendar anchor 2x; positives D1 at least 5min before real first2x HIGH",
       "positive_early5_historic_2x":len(positive),"non2x_controls":len(controls),
       "excluded_post_first2x_candidate":len(posthigh),
       "global_unmatched_pairwise_auc":global_metrics,
       "within_date_equal_weight_auc":macro,
       "per_date":per_date,"calendar2x_positive_by_date":dict(all_2x),
       "caution":"descriptive label-exposed asof ranking only; pairs share dates and subjects; no confidence as predictive, cannot optimize thresholds from these historical labels",
       "no_new_signal_thresholds":True,"new_oos":"NOT_DONE",
       "real_executable_net_pnl":"UNKNOWN","deployment":"NO_GO",
       "gmail":"OFF","autotrade":"NO_GO","frank":"UNCHANGED"}

def selftest():
    a=pairwise_auc([Decimal(2)],[Decimal(1)])
    b=pairwise_auc([Decimal(1)],[Decimal(2)])
    t=pairwise_auc([Decimal(1)],[Decimal(1)])
    assert a["auc"]==1 and b["auc"]==0 and t["auc"]==0.5
    assert pairwise_auc([],[]) is None
    print("STAGE86_PAIRWISE_CAUSAL_FEATURE_DESCRIPTIVE_SELFTEST_PASS")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--selftest",action="store_true")
    a.add_argument("--out",type=Path)
    v=a.parse_args()
    if v.selftest:selftest();return
    result=audit(load())
    raw=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if v.out:
        v.out.parent.mkdir(parents=True,exist_ok=True)
        v.out.write_text(raw)
    print("STAGE86_ALL305_DESCRIPTIVE_AUC "+json.dumps({
        "positives":result["positive_early5_historic_2x"],
        "negative_controls":result["non2x_controls"],
        "global_auc":{k:x["auc"] for k,x in result["global_unmatched_pairwise_auc"].items()},
        "equal_date_auc":{k:x["macro_equal_date_auc"] for k,x in result["within_date_equal_weight_auc"].items()},
        "eligible_days":next(iter(result["within_date_equal_weight_auc"].values()))["date_auc_values"]
    },sort_keys=True))
if __name__=="__main__":
    main()
