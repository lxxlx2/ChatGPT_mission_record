#!/usr/bin/env python3
"""Stage94: true as-of D1 features vs subsequently observed 24/72h PRICE proxy.
All 305 source-verified cases. Descriptive only, NEVER select a trade or tune D1.
"""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

E = Path(__file__).resolve().parents[2] / "monster/evidence"
ASOF=E/"monster_stage85_all305_official_D1_asof_features.jsonl"
PATHS=E/"monster_stage88_all305_D1_post_signal_24h72h_price_paths.jsonl"
PINS={
    ASOF.name:"622299fec16400e189cb8fa668ecbc8bc31ec630",
    PATHS.name:"86e96b726f677a15f5a7c8d740e3caca5c83e3fc",
}
DATES=("2025-01-30","2025-06-02","2025-08-01",
       "2025-10-02","2026-06-21","2026-07-28")
FEATURES={
    "ret60_pct":"asof_D1_ret60_pct",
    "quote15_USDT":"asof_D1_quote15_USDT",
    "trade15":"asof_D1_trade15",
    "quote_ratio_prev45":"asof_D1_normalized_quote15_prev45",
    "return_from_first_D0_pct":"asof_D1_ret_from_first_D0_pct",
    "minutes_since_first_D0":"from_first_d0_delay_minutes",
}
LABELS=(
    "h24_up","h72_up",
    "h24_gross_ge50","h72_gross_ge50",
    "h24_gross_ge100","h72_gross_ge100",
    "h24_gross_loss_le20",
)
SCHEMA="MONSTER_STAGE94_ALL305_ASOF_FEATURE_VS_POST_SIGNAL_GROSS_PRICE_AUC_V1"
COMPLETE="COMPLETE_OFFICIAL_1M_SHA_PRICE_ONLY_PROXY"


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def decimal(v) -> Decimal:
    if v is None or isinstance(v,bool):
        raise ValueError("STAGE94_NOT_NUMERIC")
    try:
        d=Decimal(str(v))
    except (ValueError,InvalidOperation):
        raise ValueError("STAGE94_NOT_NUMERIC") from None
    if not d.is_finite():
        raise ValueError("STAGE94_NONFINITE_NUMBER")
    return d


def read():
    for path in (ASOF,PATHS):
        if blob(path.read_bytes())!=PINS[path.name]:
            raise ValueError("STAGE94_REAL_SOURCE_BLOB_CHANGED "+path.name)
    before=[json.loads(s) for s in ASOF.read_text().splitlines() if s.strip()]
    after=[json.loads(s) for s in PATHS.read_text().splitlines() if s.strip()]
    if len(before)!=305 or len(after)!=305:
        raise ValueError("STAGE94_EXACT_FULL305_REQUIRED")
    keys=("date","symbol","D0_FIRST_UTC","D1_FIRST_UTC","D1_PATH")
    def to_index(xs):
        answer={}
        for x in xs:
            k=tuple(x[y] for y in keys)
            if k in answer:
                raise ValueError("STAGE94_DUPLICATE_FULL_CASE_KEY")
            answer[k]=x
        return answer
    a,b=to_index(before),to_index(after)
    if a.keys()!=b.keys():
        raise ValueError("STAGE94_NOT_SAME_ORIGINAL305_D1_TIMESTAMPS")
    if set(x["date"] for x in before)!=set(DATES):
        raise ValueError("STAGE94_NOT_ALL_SIX_LOCKED_DATES")
    result=[]
    for k in sorted(a):
        x,y=a[k],b[k]
        if x["source_status"]!="COMPLETE_OFFICIAL_BINANCE_SHA_ASOF_D1" or any(
            y[h]["status"]!=COMPLETE for h in ("h24","h72")):
            raise ValueError("STAGE94_NOT_ALL_OFFICIAL_SOURCE_COMPLETED")
        if (x["identity"]!=y["identity"]
            or not y["entry_delayed_1m"]["entry_open"]
            or y["entry_delayed_1m"]["status"]!="BAR_HAS_TRADES_PRICE_ONLY"
            or x["calendar_2x_evaluation_only"]!=y["historical_anchor_2x_EVALUATION_ONLY"]):
            raise ValueError("STAGE94_SOURCE_IDENTITY_ENTRY_OR_OLD_GT_LABEL_DRIFT")
        for h in ("h24","h72"):
            if y[h]["minutes"]!=(1440 if h=="h24" else 4320):
                raise ValueError("STAGE94_WRONG_EXIT_HORIZON")
            entry=decimal(y["entry_delayed_1m"]["entry_open"])
            ret=(decimal(y[h]["exit_close"])/entry-1)*100
            if abs(ret-decimal(y[h]["fixed_exit_gross_return_pct"]))>Decimal("0.00000000001"):
                raise ValueError("STAGE94_GROSS_RETURN_NOT_RECOMPUTED_FROM_REAL_SOURCE")
        result.append((x,y))
    if sum(x["D1_PATH"]=="DIRECT_AT_FIRST_D0" for x,_ in result)!=164 or sum(
        x["D1_PATH"]=="REIGNITION_AFTER_D0" for x,_ in result)!=141:
        raise ValueError("STAGE94_FROZEN_D1_PATH_CLASS_DRIFT")
    return result


def label(post: dict, key: str) -> bool:
    v=decimal(post["h24" if key.startswith("h24") else "h72"]["fixed_exit_gross_return_pct"])
    if key.endswith("_up"):
        return v>0
    if key.endswith("_ge50"):
        return v>=50
    if key.endswith("_ge100"):
        return v>=100
    if key=="h24_gross_loss_le20":
        return v<=-20
    raise ValueError("STAGE94_UNKNOWN_PREDECLARED_LABEL")


def pairwise(pos,neg,feature):
    if not pos or not neg:
        return {"auc":None,"pairs":0,"positive":len(pos),"negative":len(neg)}
    points=0
    for x in pos:
        a=decimal(x[0][feature])
        for y in neg:
            b=decimal(y[0][feature])
            points+=2 if a>b else 1 if a==b else 0
    pairs=len(pos)*len(neg)
    return {"auc":str(Decimal(points)/(2*pairs)),"pairs":pairs,
            "positive":len(pos),"negative":len(neg)}


def asof(pair):
    return {key:pair[0][orig] for key,orig in FEATURES.items()}


def median(values):
    if not values:return None
    ordered=sorted(decimal(x) for x in values)
    m=len(ordered)//2
    return str(ordered[m] if len(ordered)%2 else (ordered[m-1]+ordered[m])/2)


def audit(pairs):
    rows=[(asof(pair),pair[1]) for pair in pairs]
    labels={}
    for target in LABELS:
        pos=[pair for pair in rows if label(pair[1],target)]
        neg=[pair for pair in rows if not label(pair[1],target)]
        bydate={}
        valid=[]
        for d in DATES:
            ps=[x for x in pos if x[1]["date"]==d]
            ns=[x for x in neg if x[1]["date"]==d]
            bydate[d]={
                "n_positives":len(ps),"n_controls":len(ns),
                "asof_auc_higher_means_positive":{
                    feature:pairwise(ps,ns,feature) for feature in FEATURES}}
            if ps and ns:
                valid.append(d)
        summary={}
        for feature in FEATURES:
            pool=pairwise(pos,neg,feature)
            values=[decimal(bydate[d]["asof_auc_higher_means_positive"][feature]["auc"])
                    for d in valid]
            summary[feature]={
                "global_auc_including_cross_date_pairs":pool["auc"],
                "global_pair_count":pool["pairs"],
                "within_date_macro_equal_date_auc":str(sum(values)/len(values))
                    if values else None,
                "same_date_eligible_window_count":len(values),
                "same_date_auc_by_window":{
                    d:bydate[d]["asof_auc_higher_means_positive"][feature]["auc"]
                    for d in DATES}}
        labels[target]={
            "positive":len(pos),"negative":len(neg),
            "count_by_date":{d:{"positives":bydate[d]["n_positives"],
                 "controls":bydate[d]["n_controls"]} for d in DATES},
            "auc":summary,
            "status":"DESCRIPTIVE_EXPOSED_PRICE_ONLY" if valid else "INSUFFICIENT_WITHIN_DATE_PAIRS"}
    ret={}
    for h in ("h24","h72"):
        values=[decimal(x[1][h]["fixed_exit_gross_return_pct"]) for x in rows]
        ret[h]={
            "total":len(values),
            "median_gross_price_change_pct":median(values),
            "positive_fixed_exit_count":sum(x>0 for x in values),
            "ge50_fixed_exit_count":sum(x>=50 for x in values),
            "ge100_fixed_exit_count":sum(x>=100 for x in values),
            "min_price_proxy_pct":str(min(values)),
            "max_price_proxy_pct":str(max(values))}
    if (len(pairs)!=305 or ret["h24"]["positive_fixed_exit_count"]!=133
        or ret["h72"]["positive_fixed_exit_count"]!=103):
        raise ValueError("STAGE94_STAGE88_FROZEN_RETURN_RESULT_DRIFT")
    return {
      "schema":SCHEMA,
      "original_source_git_blobs":PINS,
      "fixed_all305_D1":len(pairs),
      "source_verified_both_horizons":len(pairs),
      "market_scope":"MIXED_BINANCE_USDM_CENSUS_NOT_CRYPTO_ONLY",
      "price_only_return_summary":ret,
      "post_signal_only_fixed_exit_labels":labels,
      "features_only_at_or_before_D1":list(FEATURES),
      "no_retuned_strategy":True,
      "no_claim_predictive_power_from_exposed_dates":True,
      "date_correlated_population":True,
      "OOS":"NOT_DONE","real_executable_net_pnl":"UNKNOWN",
      "G3_D1":"REJECTED_EXPOSED","other_ai_review":"NOT_DONE",
      "deployment":"NO_GO","gmail":"OFF","autotrade":"NO_GO","frank":"UNCHANGED"}


def selftest():
    q=lambda val:({"x":val},None)
    assert pairwise([q(2)],[q(1)],"x")["auc"]=="1"
    assert pairwise([q(2)],[q(2)],"x")["auc"]=="0.5"
    assert pairwise([q(1)],[q(2)],"x")["auc"]=="0"
    assert pairwise([],[],"x")["auc"] is None
    assert median(["1","3"])=="2"
    assert len(FEATURES)==6 and len(LABELS)==7
    print("STAGE94_REAL_POST_SIGNAL_24H72H_LABEL_ASOF_AUC_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--audit",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.audit or not a.out:
        p.error("--audit and --out required")
    out=audit(read())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE94_ALL305_POST_SIGNAL_PRICE_ONLY_ASOF "+json.dumps({
      "n":out["fixed_all305_D1"],
      "24h_up":out["price_only_return_summary"]["h24"]["positive_fixed_exit_count"],
      "72h_up":out["price_only_return_summary"]["h72"]["positive_fixed_exit_count"],
      "24h_ge50":out["price_only_return_summary"]["h24"]["ge50_fixed_exit_count"],
      "72h_ge100":out["price_only_return_summary"]["h72"]["ge100_fixed_exit_count"],
      "24h_up_asof_same_date_auc":{
         k:v["within_date_macro_equal_date_auc"]
         for k,v in out["post_signal_only_fixed_exit_labels"]["h24_up"]["auc"].items()},
    },sort_keys=True))


if __name__=="__main__":
    main()
