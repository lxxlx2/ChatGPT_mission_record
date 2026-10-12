#!/usr/bin/env python3
"""Historical Monster D1 research candidate: chronological per-date walk-forward.

Not a production D1 replacement, investment signal, deployed system, OOS
validation or realized/executable net PnL. Strictly uses historical as-of features.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import json
import math
from pathlib import Path
import statistics

try:
    import monster_v4_stage94_d1_asof_vs_post_signal_return as s94
except ImportError:
    from scripts import monster_v4_stage94_d1_asof_vs_post_signal_return as s94

SCHEMA = "MONSTER_STAGE100_CHRONOLOGICAL_4FOLD_D1_PRIORITY_GROSS_PRICE_RESEARCH_V1"
DATES = tuple(s94.DATES)
FEATURES = (
    "asof_D1_ret60_pct",
    "asof_D1_quote15_USDT",
    "asof_D1_trade15",
    "asof_D1_normalized_quote15_prev45",
    "asof_D1_ret_from_first_D0_pct",
    "from_first_d0_delay_minutes",
    "D1_PATH",
)
LR = 0.12
L2 = 1.0
ITER = 800
MINUTE_MS = 60_000
DAY_MS = 1440 * MINUTE_MS
TRAIN_ALLOWED_D1_PRIORITY_AVERAGE_PER_DAY = 5


def time_ms(s: str) -> int:
    d=datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.tzinfo is None:raise ValueError("STAGE100_BAD_UTC")
    return int(d.timestamp()*1000)


def feature_vector(x:dict) -> list[float]:
    if x["D1_PATH"] not in ("DIRECT_AT_FIRST_D0","REIGNITION_AFTER_D0"):
        raise ValueError("STAGE100_BAD_D1_PATH")
    values=[
        float(s94.decimal(x["asof_D1_ret60_pct"])),
        float(s94.decimal(x["asof_D1_quote15_USDT"])),
        float(s94.decimal(x["asof_D1_trade15"])),
        float(s94.decimal(x["asof_D1_normalized_quote15_prev45"])),
        float(s94.decimal(x["asof_D1_ret_from_first_D0_pct"])),
        float(s94.decimal(x["from_first_d0_delay_minutes"])),
    ]
    if any(not math.isfinite(v) for v in values) or any(v<0 for v in
             (values[1],values[2],values[3],values[5])):
        raise ValueError("STAGE100_NONFINITE_OR_NEGATIVE_VOLUME_OR_DELAY")
    return [values[0], math.log1p(values[1]), math.log1p(values[2]),
            math.log1p(values[3]), values[4],math.log1p(values[5]),
            float(x["D1_PATH"]=="REIGNITION_AFTER_D0")]


def read_rows():
    pairs=s94.read()  # SHA-locked exact305 and after-D1 minute source, joined by five keys
    rows=[]
    for x,y in pairs:
        entry=y["entry_delayed_1m"]
        if (entry["status"]!="BAR_HAS_TRADES_PRICE_ONLY"
            or any(y[k]["status"]!=s94.COMPLETE for k in ("h24","h72"))):
            raise ValueError("STAGE100_HISTORIC_SOURCE_MISSING")
        t=time_ms(x["D1_FIRST_UTC"])
        window=time_ms(x["date"]+"T06:00:00Z")
        if t<window or t>=window+7*DAY_MS:
            raise ValueError("STAGE100_D1_OUTSIDE_ORIGINAL_SEVEN_DAYS")
        h24=s94.decimal(y["h24"]["fixed_exit_gross_return_pct"])
        h72=s94.decimal(y["h72"]["fixed_exit_gross_return_pct"])
        if s94.decimal(entry["entry_open"])<=0:
            raise ValueError("STAGE100_INVALID_POSTSIGNAL_ENTRY")
        # All observed outcomes are kept only for fit(training) / after-the-fact evaluation.
        rows.append({
            "date":x["date"],"symbol":x["symbol"],
            "D0_FIRST_UTC":x["D0_FIRST_UTC"],
            "D1_FIRST_UTC":x["D1_FIRST_UTC"],
            "D1_PATH":x["D1_PATH"],"identity":x["identity"],
            "feature_vector_asof_only":feature_vector(x),
            "training_24h_up_label_EVAL_ONLY":int(h24>0),
            "h24_gross_price_return_pct_EVAL_ONLY":str(h24),
            "h72_gross_price_return_pct_EVAL_ONLY":str(h72),
            "h24_MAE_pct_EVAL_ONLY":y["h24"]["max_adverse_LOW_pct_not_realized"],
            "h24_close_drawdown_pct_EVAL_ONLY":y["h24"]["max_close_to_close_drawdown_pct"],
            "major2x_early5_EVAL_ONLY":bool(x["early5_gt2_evaluation_only"]),
            "h72_tail100_EVAL_ONLY":bool(h72>=100),
        })
    if len(rows)!=305 or len({(x["date"],x["symbol"]) for x in rows})!=305:
        raise ValueError("STAGE100_NOT_ALL_FROZEN305")
    return sorted(rows,key=lambda x:(x["date"],x["symbol"]))


def logistic(z:float)->float:
    return 1.0/(1.0+math.exp(-max(-30.,min(30.,z))))


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def fit(training: list[dict]):
    if not training:
        raise ValueError("STAGE100_EMPTY_TRAIN")
    X=[r["feature_vector_asof_only"] for r in training]
    n=len(X)
    d=len(X[0])
    if d!=len(FEATURES) or any(len(x)!=d for x in X):
        raise ValueError("STAGE100_WRONG_FROZEN_VECTOR")
    mean=[sum(x[j] for x in X)/n for j in range(d)]
    std=[statistics.pstdev(x[j] for x in X) for j in range(d)]
    std=[x if x>1e-12 else 1.0 for x in std]
    norm=[[1.0]+[(x[j]-mean[j])/std[j] for j in range(d)] for x in X]
    y=[r["training_24h_up_label_EVAL_ONLY"] for r in training]
    if len(set(y))!=2:
        raise ValueError("STAGE100_TRAIN_WITHOUT_BOTH_24H_CLASSES")
    w=[0.0]*(d+1)
    for _ in range(ITER):
        gradients=[0.0]*(d+1)
        for a,target in zip(norm,y):
            e=logistic(dot(w,a))-target
            for j in range(d+1):gradients[j]+=e*a[j]
        for j in range(d+1):
            gradients[j]=gradients[j]/n+(L2*w[j]/n if j else 0)
            w[j]-=LR*gradients[j]
    if any(not math.isfinite(t) for t in w):
        raise ValueError("STAGE100_NONFINITE_WEIGHTS")
    return {"bias_and_coefficients":w,"training_feature_mean":mean,
            "training_feature_std":std,"training_n":n,
            "training_class_positive":sum(y),
            "regularization":L2,"lr":LR,"epochs":ITER,
            "features":FEATURES}


def predict(model:dict,r:dict)->float:
    x=r["feature_vector_asof_only"]
    a=[1.0]+[(x[j]-model["training_feature_mean"][j])/model[
        "training_feature_std"][j] for j in range(len(x))]
    p=logistic(dot(model["bias_and_coefficients"],a))
    if not 0<=p<=1:raise ValueError("STAGE100_INVALID_PROBABILITY")
    return p


def frozen_threshold(model,training,n_dates):
    n=min(len(training),TRAIN_ALLOWED_D1_PRIORITY_AVERAGE_PER_DAY*7*n_dates)
    if n==len(training):
        return 0.0
    scores=sorted((predict(model,x) for x in training),reverse=True)
    threshold=scores[n-1]
    return threshold


def median(nums):
    if not nums:return None
    return str(statistics.median([s94.decimal(x) for x in nums]))


def auc(rows,scorekey,labelkey):
    pos=[x[scorekey] for x in rows if x[labelkey]]
    neg=[x[scorekey] for x in rows if not x[labelkey]]
    if not pos or not neg:return None
    wins=sum(2 if a>b else 1 if a==b else 0 for a in pos for b in neg)
    return str(Decimal(wins)/Decimal(2*len(pos)*len(neg)))


def group_summary(rows,*,name:str):
    if not rows:
        return {"name":name,"n":0,"h24_median":None,"h24_up":0,
                "h72_median":None,"h72_tail100":0,"major2x_early5":0}
    h24=[x["h24_gross_price_return_pct_EVAL_ONLY"] for x in rows]
    h72=[x["h72_gross_price_return_pct_EVAL_ONLY"] for x in rows]
    return {"name":name,"n":len(rows),"h24_up":sum(
            x["training_24h_up_label_EVAL_ONLY"] for x in rows),
            "h24_up_fraction":str(Decimal(sum(
                x["training_24h_up_label_EVAL_ONLY"] for x in rows))/len(rows)),
            "h24_median":median(h24),"h72_median":median(h72),
            "h24_loss20":sum(s94.decimal(v)<=-20 for v in h24),
            "h24_MAE_median":median(x["h24_MAE_pct_EVAL_ONLY"] for x in rows),
            "h24_close_drawdown_median":median(
                x["h24_close_drawdown_pct_EVAL_ONLY"] for x in rows),
            "h72_tail100":sum(x["h72_tail100_EVAL_ONLY"] for x in rows),
            "major2x_early5":sum(x["major2x_early5_EVAL_ONLY"] for x in rows)}


def daily_load(rows,dates):
    count=Counter()
    for x in rows:
        date=x["date"]
        start=time_ms(date+"T06:00:00Z")
        ix=(time_ms(x["D1_FIRST_UTC"])-start)//DAY_MS
        if date not in dates or not 0<=ix<7:
            raise ValueError("STAGE100_WRONG_DAILY_BUCKET")
        count[(date,ix)]+=1
    total_days=7*len(dates)
    full=[{"date":d,"utc06_day":i,"count":count[(d,i)]}
          for d in dates for i in range(7)]
    return {"total":len(rows),"days":total_days,
            "average_per_day":str(Decimal(len(rows))/total_days),
            "max_per_day":max(v["count"] for v in full),
            "meets_5avg_and_12peak":len(rows)<=5*total_days
                  and max(v["count"] for v in full)<=12,
            "full_daily":full}


def run(rows):
    if set(x["date"] for x in rows)!=set(DATES):
        raise ValueError("STAGE100_ALL_SIX_ORIGINAL_COHORTS_MANDATORY")
    out=[]
    scored=[]
    for idx in range(2,len(DATES)):
        train_dates=DATES[:idx]
        test_date=DATES[idx]
        training=[x for x in rows if x["date"] in train_dates]
        testing=[x for x in rows if x["date"]==test_date]
        if not training or not testing:
            raise ValueError("STAGE100_NO_TRAIN_OR_HOLDOUT")
        model=fit(training)
        cutoff=frozen_threshold(model,training,len(train_dates))
        if any(x["date"]>=test_date for x in training):
            raise ValueError("STAGE100_FUTURE_DATE_LEAKAGE_IN_TRAIN")
        today=[]
        for case in testing:
            p=predict(model,case)
            proposal={**case,
                "trained_on_dates":list(train_dates),
                "score_only_from_asof_features":p,
                "priority_research_only":p>=cutoff}
            today.append(proposal)
            scored.append(proposal)
        promoted=[x for x in today if x["priority_research_only"]]
        non=[x for x in today if not x["priority_research_only"]]
        out.append({
          "fold":idx-1,"train_dates":list(train_dates),
          "holdout_date":test_date,
          "train_n":len(training),"test_n":len(testing),
          "train_only_model":model,
          "train_only_cutoff":cutoff,
          "holdout_auc_h24_up":auc(today,"score_only_from_asof_features",
                                   "training_24h_up_label_EVAL_ONLY"),
          "holdout_original_D1":group_summary(today,name="ALL_UNCHANGED_D1"),
          "holdout_priority":group_summary(promoted,name="PRIORITY_RESEARCH"),
          "holdout_lower_priority":group_summary(non,name="SETUP_STILL_VISIBLE"),
          "holdout_original_daily":daily_load(today,(test_date,)),
          "holdout_priority_daily":daily_load(promoted,(test_date,)),
          "missing_high_upside_2x_from_priority":[
              {"symbol":x["symbol"],"date":x["date"],
               "D1_utc":x["D1_FIRST_UTC"],"score":x["score_only_from_asof_features"]}
              for x in non if x["major2x_early5_EVAL_ONLY"]],
          "missing_72h_100pct_tails_from_priority":[
              {"symbol":x["symbol"],"date":x["date"],
               "D1_utc":x["D1_FIRST_UTC"],"score":x["score_only_from_asof_features"]}
              for x in non if x["h72_tail100_EVAL_ONLY"]],
        })
    if len(scored)!=sum(x["date"] in DATES[2:] for x in rows):
        raise ValueError("STAGE100_HOLDOUT_COVERAGE_LOST")
    prioritized=[x for x in scored if x["priority_research_only"]]
    original=group_summary(scored,name="ORIGINAL_D1_HOLDOUT_CENSUS")
    selected=group_summary(prioritized,name="PRIORITY_RESEARCH_HOLDOUT_CENSUS")
    major=original["major2x_early5"]
    tail=original["h72_tail100"]
    load=daily_load(prioritized,DATES[2:])
    # Evaluation after four frozen holdout tests, never alter cutoff by future label.
    result={
      "schema":SCHEMA,
      "stage85_and_stage88_sha_pins":s94.PINS,
      "population_all_original_D1":len(rows),
      "historically_exposed_train_only_first_two_dates":list(DATES[:2]),
      "test_dates_chronological":list(DATES[2:]),
      "tested_all_D1_count":len(scored),
      "folds":out,
      "pooled_original_D1":original,
      "pooled_priority_research":selected,
      "pooled_priority_daily":load,
      "candidate_retention_major2x_early5":(
        str(Decimal(selected["major2x_early5"])/major) if major else None),
      "candidate_retention_72h_tail100":(
        str(Decimal(selected["h72_tail100"])/tail) if tail else None),
      "candidate_acceptability_exposed_only":(
        "CANDIDATE_PASSES_HISTORY_ONLY_NOT_DEPLOYABLE"
        if prioritized and load["meets_5avg_and_12peak"]
           and median(x["h24_gross_price_return_pct_EVAL_ONLY"] for x in prioritized)
           and s94.decimal(selected["h24_median"])>0
           and major>0 and selected["major2x_early5"]*100>=80*major
        else "REJECTED_HISTORIC_PRICE_OR_G3_OR_MAJOR_RECALL"),
      "G3_original_D1":"REJECTED_UNCHANGED",
      "G0_full_crypto_market":"NOT_ESTABLISHED",
      "real_net_execution_profit":"UNKNOWN",
      "no_lookahead_training":"CHRONOLOGICAL_PRIOR_DATES_ONLY",
      "not_independent_OOS":"EXPOSED_CHRONOLOGICAL_DIAGNOSTIC_ONLY",
      "new_thresholds_adopted_in_D1":"NONE",
      "other_AI_review":"NOT_DONE","deployment":"NO_GO",
      "gmail":"OFF","autotrade":"NO_GO","frank":"UNCHANGED",
      "raw_holdout_case_scores":scored,
    }
    return result


def selftest():
    vec={
     "D1_PATH":"DIRECT_AT_FIRST_D0",
     "asof_D1_ret60_pct":"11.5",
     "asof_D1_quote15_USDT":"10000",
     "asof_D1_trade15":250,
     "asof_D1_normalized_quote15_prev45":"2",
     "asof_D1_ret_from_first_D0_pct":"0",
     "from_first_d0_delay_minutes":0
    }
    assert len(feature_vector(vec))==len(FEATURES)
    fake=[]
    for i in range(20):
        fake.append({"feature_vector_asof_only":[float(i),1,2,1,0,0,float(i%2)],
                     "training_24h_up_label_EVAL_ONLY":int(i%3==0)})
    trained=fit(fake)
    assert trained["training_n"]==20
    p=predict(trained,fake[0])
    # Changing ONLY a future label on evaluation rows MUST NOT change a
    # previously trained model score, and direct D0/D1 path stays zero.
    fake[0]["training_24h_up_label_EVAL_ONLY"]=1-fake[0]["training_24h_up_label_EVAL_ONLY"]
    assert predict(trained,fake[0])==p
    assert feature_vector(vec)[-1]==0
    assert auc([
      {"score":2,"label":1},{"score":1,"label":0}], "score","label")=="1"
    print("STAGE100_HISTORIC_WALK_FORWARD_NO_FUTURE_FEATURES_FIXED_MODEL_AND_LOAD_SELFTEST_PASS")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--selftest",action="store_true")
    parser.add_argument("--backtest",action="store_true")
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    if args.selftest:selftest();return
    if not args.backtest or not args.out:parser.error("--backtest --out required")
    result=run(read_rows())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    summary={k:result[k] for k in (
       "population_all_original_D1","tested_all_D1_count",
       "candidate_retention_major2x_early5","candidate_retention_72h_tail100",
       "candidate_acceptability_exposed_only","not_independent_OOS")}
    summary["priority_n"]=result["pooled_priority_research"]["n"]
    summary["h24_median"]=result["pooled_priority_research"]["h24_median"]
    summary["daily_peak"]=result["pooled_priority_daily"]["max_per_day"]
    print("STAGE100_HISTORY_ONLY_WALK_FORWARD "+json.dumps(summary,sort_keys=True))


if __name__=="__main__":
    main()
