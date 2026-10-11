#!/usr/bin/env python3
"""Recompute Stage20 pooled arm metrics and same-case comparisons from CI ZIPs.

Archive contents and their SHA256 must match Git-tracked immutable evidence.
This does NOT import future labels, retune thresholds or assert real fills.
"""
import argparse
import hashlib
import json
import statistics
import zipfile
from collections import Counter
from pathlib import Path

EVIDENCE=Path(__file__).resolve().parents[2]/"monster/evidence"
RECORD=EVIDENCE/"monster_stage20_actual_four_holdout_quality_exit_ci_20261011.json"
PREREG=EVIDENCE/"monster_stage20_quality_exit_holdout_prereg_20261011.json"
MAX_JSON_BYTES=8_000_000

def digest(data):
    return hashlib.sha256(data).hexdigest()

def load_archive(zip_path,expected):
    source=Path(zip_path)
    rawzip=source.read_bytes()
    if digest(rawzip)!=expected["zip_sha256"]:
        raise ValueError("STAGE20_ARTIFACT_ZIP_SHA256_MISMATCH_"+expected["date"])
    with zipfile.ZipFile(source) as z:
        names=z.namelist()
        if names!=["monster_stage20_"+expected["date"]+".json"]:
            raise ValueError("STAGE20_ARTIFACT_MEMBER_MISMATCH")
        if z.getinfo(names[0]).file_size>MAX_JSON_BYTES:
            raise ValueError("STAGE20_ARTIFACT_OVERSIZE")
        raw=z.read(names[0])
    if digest(raw)!=expected["raw_json_sha256"]:
        raise ValueError("STAGE20_ARTIFACT_JSON_SHA256_MISMATCH")
    report=json.loads(raw)
    if (report.get("schema")!="MONSTER_STAGE20_FOUR_FROZEN_HOLDOUT_D1_QUALITY_EXIT_V1"
            or report.get("date")!=expected["date"]
            or report.get("frozen_prereg")!=PREREG.name):
        raise ValueError("STAGE20_ARTIFACT_DATE_OR_SCHEMA_MISMATCH")
    rows=report["cases"]
    if len(rows)!=758 or len({row["symbol"] for row in rows})!=758:
        raise ValueError("STAGE20_INCOMPLETE_SYMBOL_UNIVERSE")
    status=Counter(x["status"] for x in rows)
    if dict(status)!=report["summary"]["source_status"]:
        raise ValueError("STAGE20_SOURCE_STATUS_MANIPULATED")
    if status["COMPLETE_60H"]!=report["summary"]["valid_60h"]:
        raise ValueError("STAGE20_COMPLETE_COUNT_CHANGED")
    return report

def stats(trades):
    counts=Counter(t["status"] for t in trades)
    vals=[t["net_pct"] for t in trades if t["status"]=="PRICE_PROXY_ONLY"]
    return {"selected":len(trades),"evaluable":len(vals),
            "positive":sum(x>0 for x in vals),
            "negative":sum(x<0 for x in vals),
            "median_net_pct":round(statistics.median(vals),6) if vals else None,
            "mean_net_pct":round(statistics.mean(vals),6) if vals else None,
            "proxy_sum_independent_30usdt":round(sum(x*0.3 for x in vals),6),
            "censored":{k:v for k,v in counts.items() if k!="PRICE_PROXY_ONLY"}}

def paired(cases,left,right):
    values=[]
    for c in cases:
        p=c["arm_proxies"]
        l=p[left];r=p[right]
        if (l is None or r is None or l["status"]!="PRICE_PROXY_ONLY"
                or r["status"]!="PRICE_PROXY_ONLY"):
            continue
        values.append(r["net_pct"]-l["net_pct"])
    return {"matched_evaluable":len(values),
            "right_better":sum(x>0 for x in values),
            "right_worse":sum(x<0 for x in values),
            "right_minus_left_median_pp":round(statistics.median(values),6) if values else None,
            "right_minus_left_mean_pp":round(statistics.mean(values),6) if values else None,
            "right_minus_left_30usdt_sum":round(sum(x*0.3 for x in values),6)}

def aggregate(zips, record_path=RECORD,prereg_path=PREREG):
    evidence=json.loads(Path(record_path).read_text(encoding="utf-8"))
    cfg=json.loads(Path(prereg_path).read_text(encoding="utf-8"))
    arts={x["date"]:x for x in evidence["artifacts"]}
    dates=cfg["holdout_dates_utc"]
    if len(dates)!=4 or set(arts)!=set(dates) or len(zips)!=4:
        raise ValueError("STAGE20_EXPECT_FOUR_FROZEN_DATES")
    files={}
    for path in zips:
        # Trust the *signed-by-SHA* content; find expected by actual member name.
        with zipfile.ZipFile(path) as z:
            names=z.namelist()
        if len(names)!=1:
            raise ValueError("STAGE20_MULTIPLE_ZIP_MEMBERS")
        day=names[0].removeprefix("monster_stage20_").removesuffix(".json")
        if day not in arts or day in files:
            raise ValueError("STAGE20_DUPLICATE_OR_NONFROZEN_DAY")
        files[day]=load_archive(path,arts[day])
    if set(files)!=set(dates):
        raise ValueError("STAGE20_MISSING_FROZEN_DAY")
    rows=[(date,r) for date in dates for r in files[date]["cases"]]
    valid=[(d,r) for d,r in rows if r["status"]=="COMPLETE_60H"]
    d1=[(d,r) for d,r in valid if "arm_proxies" in r]
    gates=Counter(k for _,r in d1 for k,v in r["quality"]["flags"].items() if not v)
    arm_order=cfg["arms"]
    by_arm={}
    for arm in arm_order:
        trades=[r["arm_proxies"][arm] for _,r in d1 if r["arm_proxies"][arm] is not None]
        by_arm[arm]=stats(trades)
        assert by_arm[arm]["selected"]==sum(
            files[date]["summary"][arm]["selected"] for date in dates)
        assert by_arm[arm]["evaluable"]==sum(
            files[date]["summary"][arm]["evaluated"] for date in dates)
    quality=by_arm["D_QUALITY_D1_BOUNDED_6H_20BPS"]
    enough_dates=sum(any(r["quality"]["quality_pass"] and
              r["arm_proxies"]["D_QUALITY_D1_BOUNDED_6H_20BPS"]["status"]=="PRICE_PROXY_ONLY"
              for d,r in d1 if d==day) for day in dates)
    gates_config=cfg["gate_for_further_research"]
    decisions={
        "minimum_evaluable":quality["evaluable"]>=gates_config["minimum_nonoverlapping_evaluable_quality_trades"],
        "minimum_distinct_dates":enough_dates>=gates_config["minimum_distinct_holdout_dates"],
        "median_positive":quality["median_net_pct"] is not None and quality["median_net_pct"]>0,
        "win_fraction":quality["evaluable"]>0 and (quality["positive"]/quality["evaluable"])>=gates_config["winning_fraction_min"],
        "sum30_positive":quality["proxy_sum_independent_30usdt"]>0,
        "censor_rate":quality["selected"]>0 and (quality["selected"]-quality["evaluable"])/quality["selected"]<=gates_config["censored_frac_max"],
    }
    checks={
        "attempted":len(rows),"complete_60h":len(valid),
        "v4_watch":sum(r["v4_watch"] for _,r in valid),
        "v4_d1":sum(r["v4_d1_episodes"] for _,r in valid),
        "first_d1_symbol_dates":len(d1),
        "quality_selected":sum(r["quality"]["quality_pass"] for _,r in d1),
        "source_status":dict(Counter(r["status"] for _,r in rows)),
        "quality_rejected_flags":dict(gates)}
    return {"schema":"MONSTER_STAGE20_EXACT_FOUR_ARTIFACT_RECOMPUTATION_V1",
        "artifact_sha256_all_matched":True,"dates":dates,
        "checks":checks,"arms":by_arm,
        "paired":{
            "A_vs_B_same_case":paired([r for _,r in d1],arm_order[0],arm_order[1]),
            "C_vs_D_same_case":paired([r for _,r in d1],arm_order[2],arm_order[3]),
            "D_vs_E_same_case":paired([r for _,r in d1],arm_order[3],arm_order[4])},
        "preregistered_gates":decisions,
        "all_hard_gates_passed":all(decisions.values()),
        "high_slippage_100bps":"PREDECLARED_SENSITIVITY_ONLY_NOT_NEW_HARD_GATE",
        "historical_l2_fill_verified":False,"deployment":"NO_GO"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifact-zips",nargs=4,required=True,type=Path)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    out=aggregate(args.artifact_zips)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE20_AGGREGATED "+json.dumps({"checks":out["checks"],
        "preregistered_gates":out["preregistered_gates"],
        "all_hard_gates_passed":out["all_hard_gates_passed"]},sort_keys=True))

if __name__=="__main__":
    main()
