#!/usr/bin/env python3
"""Stage109 pre-registered genuine two-path D1 priority classification research.

Train 2 independent path-specific logistic models only on completed earlier
historical windows. A seventh feature is the number of earlier D1 events in
the SAME 7-day calendar window during the 24h preceding this exact D1 time.
No training/evaluation labels may ever enter the as-of feature vector.

Do NOT use this as a trade, live alert, executable net-return or OOS signal.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
from collections import Counter
from decimal import Decimal
import json
import math
from pathlib import Path

try:
    import monster_v4_stage100_historical_d1_priority_walkforward as s100
except ImportError:
    from scripts import monster_v4_stage100_historical_d1_priority_walkforward as s100

SCHEMA="MONSTER_STAGE109_SEPARATE_DIRECT_REIGNITION_CAUSAL_CROWD_PRIOR_24H_4FOLD_V1"
DIRECT="DIRECT_AT_FIRST_D0"
REIGNITION="REIGNITION_AFTER_D0"
PATHS=(DIRECT,REIGNITION)
DATES=tuple(s100.DATES)
DAY_MS=86400000
HOURS24_MS=DAY_MS
TRAIN_BUDGET_PER_COMPLETE_UTC06_DAY=4
FEATURES_ASOF_ONLY=(
    "asof_ret60_pct", "log1p_asof_quote15_USDT",
    "log1p_asof_trade15", "log1p_asof_quote15_relative45",
    "asof_ret_since_first_D0_pct", "log1p_delay_from_D0_min",
    "log1p_number_prior_D1_in_last_24h",
)


def add_causal_crowd(rows: list[dict]) -> list[dict]:
    by_date={}
    for row in rows:
        if row["date"] not in DATES or row["D1_PATH"] not in PATHS:
            raise ValueError("STAGE109_UNKNOWN_DATE_OR_PATH")
        by_date.setdefault(row["date"],[]).append(s100.time_ms(row["D1_FIRST_UTC"]))
    for date, times in by_date.items():
        if len(times)!=len(set((date, x["symbol"]) for x in rows if x["date"]==date)):
            raise ValueError("STAGE109_DUPLICATE_COIN_DATE")
    sorted_by_date={date:sorted(times) for date,times in by_date.items()}
    answer=[]
    for row in rows:
        at=s100.time_ms(row["D1_FIRST_UTC"])
        times=sorted_by_date[row["date"]]
        previous=bisect_left(times,at)
        # Inclusive lower bound at t-24h, strictly exclusive upper bound t.
        start=bisect_left(times,at-HOURS24_MS)
        count=previous-start
        vec=row["feature_vector_asof_only"]
        if len(vec)!=len(s100.FEATURES) or not math.isfinite(float(count)):
            raise ValueError("STAGE109_PRE_FROZEN_ASOF_VECTOR_INVALID")
        updated={**row,
            "asof_known_D1_prior_24h_event_count":count,
            "feature_vector_asof_only":list(vec[:6])+[math.log1p(count)],
            "prior_date_source":"ONLY_ALREADY_OCCURRED_D1_IN_SAME_FROZEN_7DAY_WINDOW",
        }
        answer.append(updated)
    return answer


def training_quotas(training: list[dict],n_training_dates:int) -> dict[str,int]:
    if n_training_dates < 2 or not training:
        raise ValueError("STAGE109_INSUFFICIENT_DATE_TRAINING")
    if len(set(row["date"] for row in training))!=n_training_dates:
        raise ValueError("STAGE109_TRAINING_DATE_COVERAGE_CHANGED")
    counts=Counter(x["D1_PATH"] for x in training)
    if set(counts)!=set(PATHS):
        raise ValueError("STAGE109_EARLIER_DATES_MISSING_A_PATH")
    total=TRAIN_BUDGET_PER_COMPLETE_UTC06_DAY*7*n_training_dates
    if total>=len(training):
        return dict(counts)
    quotas={p:(total*counts[p])//len(training) for p in PATHS}
    remaining=total-sum(quotas.values())
    by_remainder=sorted(PATHS,key=lambda p:(
        -(total*counts[p])%len(training),p))
    # Use explicit decreasing remainder; don't choose threshold by test outcome.
    by_remainder=sorted(PATHS,key=lambda p:(
        -((total*counts[p])%len(training)),p))
    for path in by_remainder[:remaining]:
        quotas[path]+=1
    if sum(quotas.values())!=total or any(quotas[p]<1 for p in PATHS):
        raise ValueError("STAGE109_TRAIN_ONLY_GROUP_QUOTA_INVALID")
    return quotas


def path_threshold(model:dict,training:list[dict],quota:int) -> float:
    if quota<0:
        raise ValueError("STAGE109_NEGATIVE_TRAINING_QUOTA")
    if quota==0:
        return 1.1
    if quota>=len(training):
        return 0.0
    values=sorted((s100.predict(model,r) for r in training),reverse=True)
    return values[quota-1]


def run(rows: list[dict]) -> dict:
    if len(rows)!=305 or set(r["date"] for r in rows)!=set(DATES):
        raise ValueError("STAGE109_CANNOT_DROP_ANY_FROZEN_D1_ROWS")
    enriched=add_causal_crowd(rows)
    outputs=[]
    case_scores=[]
    for idx in range(2,len(DATES)):
        prior=DATES[:idx]
        holdout=DATES[idx]
        training=[r for r in enriched if r["date"] in prior]
        testing=[r for r in enriched if r["date"]==holdout]
        if any(r["date"]>=holdout for r in training):
            raise ValueError("STAGE109_FUTURE_DATE_LEAKAGE")
        quota=training_quotas(training,len(prior))
        trained={}
        for path in PATHS:
            grp=[r for r in training if r["D1_PATH"]==path]
            model=s100.fit(grp)
            trained[path]={
                "model":model,
                "cutoff":path_threshold(model,grp,quota[path]),
                "train_n":len(grp),
                "train_target_budget":quota[path],
            }
        scored=[]
        for r in testing:
            pair=trained[r["D1_PATH"]]
            p=s100.predict(pair["model"],r)
            x={
                **r,
                "trained_on_dates":list(prior),
                "separate_model":r["D1_PATH"],
                "score_only_from_asof_features":p,
                "path_training_only_cutoff":pair["cutoff"],
                "priority_research_only":p>=pair["cutoff"],
            }
            scored.append(x)
            case_scores.append(x)
        promoted=[x for x in scored if x["priority_research_only"]]
        rest=[x for x in scored if not x["priority_research_only"]]
        outputs.append({
            "train_dates":list(prior),
            "test_date":holdout,
            "train_n":len(training),
            "test_n":len(scored),
            "train_only_separate_path_models":trained,
            "holdout_auc_24h_up":s100.auc(
                scored,"score_only_from_asof_features",
                "training_24h_up_label_EVAL_ONLY"),
            "holdout_original":s100.group_summary(scored,name="ALL_D1_SETUP_PRESERVED"),
            "holdout_priority":s100.group_summary(promoted,name="PATH_PRIORITY"),
            "holdout_unpromoted":s100.group_summary(rest,name="D1_SETUP_STILL_RETAINED"),
            "holdout_priority_daily":s100.daily_load(promoted,(holdout,)),
            "missed_early_major_2x": [
                {"date":x["date"],"symbol":x["symbol"],
                 "D1_FIRST_UTC":x["D1_FIRST_UTC"],
                 "path":x["D1_PATH"],"score":x["score_only_from_asof_features"]}
                for x in rest if x["major2x_early5_EVAL_ONLY"]
            ],
            "missed_72h_100pct_right_tail":[
                {"date":x["date"],"symbol":x["symbol"],
                 "path":x["D1_PATH"],"score":x["score_only_from_asof_features"]}
                for x in rest if x["h72_tail100_EVAL_ONLY"]
            ],
        })
    all_test=[x for x in case_scores]
    if len(all_test)!=214 or len({(x["date"],x["symbol"]) for x in all_test})!=214:
        raise ValueError("STAGE109_HISTORICAL_214_TEST_ROWS_NOT_CLOSED")
    pri=[x for x in all_test if x["priority_research_only"]]
    base=s100.group_summary(all_test,name="ORIGINAL_214_D1")
    chosen=s100.group_summary(pri,name="STAGE109_PRIORITY")
    load=s100.daily_load(pri,DATES[2:])
    major=base["major2x_early5"]
    right=base["h72_tail100"]
    gates={
        "G2_major_2x_early5_retention":(
            major>0 and chosen["major2x_early5"]*100>=80*major),
        "G3_attention_5avg_12peak":load["meets_5avg_and_12peak"],
        "G4_h24_positive_price_median_not_net_pnl":(
            len(pri)>0 and s100.s94.decimal(chosen["h24_median"])>0),
        "historical_72h_right_tail100_retention_80pct":(
            right>0 and chosen["h72_tail100"]*100>=80*right),
    }
    missed=[{
        "date":x["date"],"symbol":x["symbol"],
        "D1_FIRST_UTC":x["D1_FIRST_UTC"],"D1_PATH":x["D1_PATH"],
        "prior24h":x["asof_known_D1_prior_24h_event_count"],
        "h24_return_gross":x["h24_gross_price_return_pct_EVAL_ONLY"],
        "h72_return_gross":x["h72_gross_price_return_pct_EVAL_ONLY"],
        "original_major2x_early5_EVAL_ONLY":x["major2x_early5_EVAL_ONLY"],
        "h72_100pct_tail_EVAL_ONLY":x["h72_tail100_EVAL_ONLY"],
        "reason":"NOT_PRIORITY_STILL_RETAINED_IN_D1_SETUP",
    } for x in all_test if not x["priority_research_only"]]
    baseline=s100.run(rows)
    return {
        "schema":SCHEMA,
        "source_stage85_and_88_git_blob_pins":s100.s94.PINS,
        "preregistered_features_asof_only":list(FEATURES_ASOF_ONLY),
        "no_future_test_label_or_future_day_in_training":True,
        "chronological_exposed_not_new_OOS":True,
        "frozen_dates":list(DATES),
        "original_D0_AND_STAGE79_D1_unchanged":True,
        "all_original_D1_preserved":len(enriched),
        "source_D1_paths":dict(Counter(x["D1_PATH"] for x in enriched)),
        "complete_305_asof_crowd_cases":[{
            "date":x["date"],"symbol":x["symbol"],
            "D1_FIRST_UTC":x["D1_FIRST_UTC"],
            "D1_PATH":x["D1_PATH"],
            "asof_D1_prior_24h_count":x["asof_known_D1_prior_24h_event_count"],
        } for x in enriched],
        "train_only_budget_per_utc06_day":TRAIN_BUDGET_PER_COMPLETE_UTC06_DAY,
        "folds":outputs,
        "raw_holdout_case_scores":case_scores,
        "nonpriority_retained_setup_with_future_evaluation":missed,
        "pooled_original_D1":base,
        "pooled_path_priority_research":chosen,
        "pooled_path_priority_daily":load,
        "retention_major2x_early5":(
            str(Decimal(chosen["major2x_early5"])/major) if major else None),
        "retention_right_tail_72h100":(
            str(Decimal(chosen["h72_tail100"])/right) if right else None),
        "gates":gates,
        "candidate_status":(
            "HISTORICAL_RESEARCH_PASSES_GATES_NOT_FORWARD_VALIDATED"
            if all(gates.values()) else "REJECTED_FROZEN_HISTORICAL_MODEL_GATES"),
        "failed_gates":[k for k,v in gates.items() if not v],
        "control_frozen_stage100":{
            "model_status":baseline["candidate_acceptability_exposed_only"],
            "tested_all_D1_count":baseline["tested_all_D1_count"],
            "priority_n":baseline["pooled_priority_research"]["n"],
            "priority_h24_median":baseline["pooled_priority_research"]["h24_median"],
            "major2x_retention":baseline["candidate_retention_major2x_early5"],
            "right_tail_retention":baseline["candidate_retention_72h_tail100"],
            "attention":{k:v for k,v in baseline["pooled_priority_daily"].items()
                          if k!="full_daily"},
        },
        "real_bid_ask_depth_slippage_fills_fee_notional":"UNKNOWN",
        "other_ai_review_of_new_strategy":"NOT_DONE",
        "no_monster_deployment":"NO_GO","gmail":"OFF","auto_trade":"NO_GO",
        "frank":"UNCHANGED",
    }


def selftest() -> None:
    rows=[{
        "date":DATES[0],"symbol":f"S{i}USDT","D1_FIRST_UTC":time,
        "D1_PATH":DIRECT if i%2==0 else REIGNITION,
        "feature_vector_asof_only":[0.0]*7,
        "training_24h_up_label_EVAL_ONLY":int(i%3==0),
    } for i,time in enumerate((
        "2025-01-30T06:01:00Z",
        "2025-01-30T06:01:00Z",
        "2025-01-30T06:02:00Z",
        "2025-01-31T06:03:00Z",
    ))]
    prefix=add_causal_crowd(rows)
    assert [r["asof_known_D1_prior_24h_event_count"] for r in prefix]==[0,0,2,0]
    later=rows+[{
        **rows[-1],"symbol":"FUTUREUSDT","D1_FIRST_UTC":"2025-02-02T06:05:00Z"
    }]
    changed=add_causal_crowd(later)
    assert [x["asof_known_D1_prior_24h_event_count"] for x in changed[:4]]==[0,0,2,0]
    a=[]
    for path in PATHS:
        for i in range(30 if path==DIRECT else 70):
            a.append({"date":DATES[i%2], "D1_PATH":path})
    q=training_quotas(a,2)
    assert sum(q.values())==56 and q[DIRECT]>0 and q[REIGNITION]>0
    print("STAGE109_TWO_PATH_CAUSAL_CROWD_FORWARD_FROZEN_QUOTA_SELFTEST_PASS")


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--backtest",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.backtest or args.out is None:
        p.error("use --backtest --out")
    result=run(s100.read_rows())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,
                                   sort_keys=True)+"\n")
    brief={
      "source_305_preserved":result["all_original_D1_preserved"],
      "tested_214":len(result["raw_holdout_case_scores"]),
      "priority_n":result["pooled_path_priority_research"]["n"],
      "h24_median":result["pooled_path_priority_research"]["h24_median"],
      "major_early5_retention":result["retention_major2x_early5"],
      "tail_retention":result["retention_right_tail_72h100"],
      "daily_avg":result["pooled_path_priority_daily"]["average_per_day"],
      "daily_peak":result["pooled_path_priority_daily"]["max_per_day"],
      "failed_gates":result["failed_gates"],
      "decision":result["candidate_status"],
      "not_OOS":"EXPOSED_HISTORICAL_DATE_ORDER_ONLY",
    }
    print("STAGE109_REAL305_TWO_PATH_CAUSAL_CROWD_MODEL "+json.dumps(brief,sort_keys=True))


if __name__=="__main__":
    main()
