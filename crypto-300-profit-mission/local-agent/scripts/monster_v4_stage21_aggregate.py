#!/usr/bin/env python3
"""Stage21 immutable verified ZIP reaggregation, risk and single-slot diagnostics.

Research-only. Inputs MUST match publisher-verified original GHA output
archive SHA256 and extracted JSON SHA256 from the committed run manifest.
No trading signals or selected dates may be changed here.
"""
import argparse
import hashlib
import json
import statistics
import zipfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]/"monster/evidence"
MANIFEST=ROOT/"monster_stage21_extended_untouched_dates_prereg_20261011.json"
PROOF=ROOT/"monster_stage21_real_10date_ci_artifact_proof_20261011.json"
ARM_NAMES=("A_ALL_D1_FIXED_24H_20BPS","B_ALL_D1_BOUNDED_6H_20BPS",
           "C_QUALITY_D1_FIXED_24H_20BPS",
           "D_QUALITY_D1_BOUNDED_6H_20BPS",
           "E_QUALITY_D1_BOUNDED_6H_100BPS")
MAX_JSON=12_000_000

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_zip(path,expected):
    data=Path(path).read_bytes()
    if sha(data)!=expected["zip_sha256"]:
        raise ValueError("STAGE21_ZIP_HASH_MISMATCH:"+expected["date"])
    with zipfile.ZipFile(path) as z:
        name="monster_stage21_"+expected["date"]+".json"
        if z.namelist()!=[name] or z.getinfo(name).file_size>MAX_JSON:
            raise ValueError("STAGE21_UNEXPECTED_ZIP_MEMBER")
        raw=z.read(name)
    if sha(raw)!=expected["raw_json_sha256"]:
        raise ValueError("STAGE21_ORIGINAL_JSON_SHA_MISMATCH")
    doc=json.loads(raw)
    if doc.get("schema")!="MONSTER_STAGE21_FROZEN_NEW_DATES_EXACT_V4_STAGE20_RULES_V1" or doc.get("date")!=expected["date"]:
        raise ValueError("STAGE21_RAW_IDENTITY_FAIL")
    if doc.get("locked_prior_strategy_git_blob_sha1")!=expected["stage20_git_blob_sha1"]:
        raise ValueError("STAGE21_ALTERED_STRATEGY")
    cases=doc.get("cases")
    if not isinstance(cases,list) or len(cases)!=758 or len({x["symbol"] for x in cases})!=758:
        raise ValueError("STAGE21_FULL_UNIVERSE_MISSING")
    summary=doc["summary"]
    if (Counter(c["status"] for c in cases)!=Counter(summary["source_status"])
            or summary["valid_60h"]!=sum(c["status"]=="COMPLETE_60H" for c in cases)):
        raise ValueError("STAGE21_SOURCE_COUNTS_MISMATCH")
    return doc

def performance(trades):
    good=[x for x in trades if x["status"]=="PRICE_PROXY_ONLY"]
    vals=[x["net_pct"] for x in good]
    return {"selected":len(trades),"evaluable":len(good),
        "wins":sum(x>0 for x in vals),"losses":sum(x<0 for x in vals),
        "median_net_pct":round(statistics.median(vals),6) if vals else None,
        "mean_net_pct":round(statistics.mean(vals),6) if vals else None,
        "sum_independent_30usdt_pnl":round(sum(x*0.3 for x in vals),6),
        "censored_count":len(trades)-len(good),
        "censored_reasons":dict(Counter(x["status"] for x in trades if x["status"]!="PRICE_PROXY_ONLY")),
        "worst_pct":round(min(vals),6) if vals else None,
        "best_pct":round(max(vals),6) if vals else None,
        "exit_reasons":dict(Counter(x.get("exit_reason","FIXED_24H")
             for x in good))}

def paired(records,left,right):
    diff=[]
    for _,c in records:
        a=c["arm_proxies"][left]
        b=c["arm_proxies"][right]
        if a is None or b is None or a["status"]!="PRICE_PROXY_ONLY" or b["status"]!="PRICE_PROXY_ONLY":
            continue
        diff.append(b["net_pct"]-a["net_pct"])
    return {"n":len(diff),"right_better":sum(x>0 for x in diff),
        "right_worse":sum(x<0 for x in diff),
        "median_improvement_pp":round(statistics.median(diff),6) if diff else None,
        "mean_improvement_pp":round(statistics.mean(diff),6) if diff else None,
        "incremental_30usdt_sum":round(sum(x*0.3 for x in diff),6)}

def slot30_usdt(records,arm):
    """One 30-USDT slot, no overlapping candidate entries.

    Chronological by signal timestamp only, no future PnL ranking. A censored
    selected signal reserves six hours, preventing optimistic reallocation.
    1m proxy exit from research output, not actual bid/ask execution.
    """
    ordered=sorted(
        ((datetime.fromisoformat(c["first_v4_d1_utc"].replace("Z","+00:00")),
           day,c) for day,c in records
           if c["arm_proxies"][arm] is not None),
        key=lambda x:(x[0],x[1],x[2]["symbol"]))
    next_free=datetime.min.replace(tzinfo=timezone.utc)
    accepted=[];blocked=0
    for signal_time,day,c in ordered:
        entry=signal_time+timedelta(minutes=3)
        if entry<next_free:
            blocked+=1
            continue
        proxy=c["arm_proxies"][arm]
        if proxy["status"]=="PRICE_PROXY_ONLY" and "exit_utc" in proxy:
            candidate_free=datetime.fromisoformat(proxy["exit_utc"].replace("Z","+00:00"))
            next_free=max(entry+timedelta(minutes=1),candidate_free)
        else:
            next_free=entry+timedelta(hours=6)
        accepted.append({"day":day,"symbol":c["symbol"],
            "setup_utc":c["first_v4_d1_utc"],
            "proxy_status":proxy["status"],
            "net_pct":proxy.get("net_pct")})
    vals=[c["net_pct"] for c in accepted if c["proxy_status"]=="PRICE_PROXY_ONLY"]
    return {"selected_by_signal_chronology":len(accepted),
        "blocked_by_capital_overlap":blocked,
        "evaluable":len(vals),
        "censored_reserves_six_hours":len(accepted)-len(vals),
        "wins":sum(x>0 for x in vals),"losses":sum(x<0 for x in vals),
        "simulated_sum_30usdt":round(sum(x*.3 for x in vals),6),
        "not_actual_order_fills":True,
        "selected_evidence":accepted}

def aggregate(zip_paths,proof=PROOF,manifest=MANIFEST):
    locked=json.loads(Path(manifest).read_text(encoding="utf-8"))
    register=json.loads(Path(proof).read_text(encoding="utf-8"))
    days=locked["frozen_dates_utc"]
    arts=register["artifacts"]
    if len(days)!=10 or len(arts)!=10 or len(zip_paths)!=10:
        raise ValueError("STAGE21_REQUIRED_10_DATES")
    meta={x["date"]:x for x in arts}
    if set(meta)!=set(days):
        raise ValueError("STAGE21_DATE_MISMATCH")
    reports={}
    for path in zip_paths:
        with zipfile.ZipFile(path) as z:
            name=z.namelist()[0]
        day=name.removeprefix("monster_stage21_").removesuffix(".json")
        if day not in meta or day in reports:
            raise ValueError("STAGE21_UNRECOGNIZED_OR_DUPLICATE_DAY")
        reports[day]=read_zip(path,meta[day])
    if set(reports)!=set(days):
        raise ValueError("STAGE21_INCOMPLETE_PREREG_DATES")
    rows=[(day,c) for day in days for c in reports[day]["cases"]]
    valid=[(day,c) for day,c in rows if c["status"]=="COMPLETE_60H"]
    d1=[(day,c) for day,c in valid if "arm_proxies" in c]
    quality=[(day,c) for day,c in d1 if c["quality"]["quality_pass"]]
    arm_stats={}
    for arm in ARM_NAMES:
        arm_stats[arm]=performance([c["arm_proxies"][arm] for _,c in d1
                            if c["arm_proxies"][arm] is not None])
        expected_sel=sum(reports[day]["summary"][arm]["selected"] for day in days)
        expected_eval=sum(reports[day]["summary"][arm]["evaluated"] for day in days)
        if arm_stats[arm]["selected"]!=expected_sel or arm_stats[arm]["evaluable"]!=expected_eval:
            raise ValueError("STAGE21_ARMS_SOURCE_MISMATCH")
    chosen=arm_stats[ARM_NAMES[3]]
    rule=locked["primary_precommitted"]
    distinct=sum(any(c["arm_proxies"][ARM_NAMES[3]]["status"]=="PRICE_PROXY_ONLY"
                for d,c in quality if d==day) for day in days)
    gates={
      "minimum_evaluable":chosen["evaluable"]>=rule["minimum_evaluable"],
      "minimum_distinct_dates":distinct>=rule["minimum_nonoverlapping_unique_dates"],
      "winning_fraction":chosen["evaluable"]>0 and chosen["wins"]/chosen["evaluable"]>=rule["minimum_positive_fraction"],
      "median_positive":chosen["median_net_pct"] is not None and chosen["median_net_pct"]>0,
      "sum_pnl_positive":chosen["sum_independent_30usdt_pnl"]>0,
      "censoring_fraction":chosen["selected"]>0 and chosen["censored_count"]/chosen["selected"]<=rule["max_censor_fraction"]
    }
    return {
      "schema":"MONSTER_STAGE21_FULL_10_ORIGINAL_ZIP_SHA_VERIFIED_RECALC_V1",
      "source_dates":days,"all_10_artifact_zip_and_raw_json_sha256_verified":True,
      "summary":{"attempted":len(rows),"valid_60h":len(valid),
          "source_status":dict(Counter(c["status"] for _,c in rows)),
          "v4_watch":sum(c["v4_watch"] for _,c in valid),
          "v4_d1":sum(c["v4_d1_episodes"] for _,c in valid),
          "unique_d1_symbol_dates":len(d1),
          "quality_selected":len(quality),
          "quality_rejections":dict(Counter(k for _,c in d1 for k,v in c["quality"]["flags"].items() if not v))},
      "all_arms":arm_stats,
      "paired":{"all_v4_24h_vs_6h":paired(d1,ARM_NAMES[0],ARM_NAMES[1]),
                "quality_24h_vs_6h":paired(d1,ARM_NAMES[2],ARM_NAMES[3]),
                "quality_6h_20bps_vs_100bps":paired(d1,ARM_NAMES[3],ARM_NAMES[4])},
      "single_slot_30usdt_6h_20bps":slot30_usdt(quality,ARM_NAMES[3]),
      "single_slot_30usdt_6h_100bps":slot30_usdt(quality,ARM_NAMES[4]),
      "precommitted_gate_result":gates,"all_precommitted_gates_passed":all(gates.values()),
      "100bps_sensitivity_not_hard_gate":True,
      "actual_historical_l2_fill":"UNVERIFIED",
      "independent_other_ai_review":"NOT_DONE",
      "mac_deployment":"NO_GO","trading":"NO_GO","real_gmail":"OFF"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifact-zips",nargs=10,required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    data=aggregate(args.artifact_zips)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE21_RECOMPUTED "+json.dumps({
        "summary":data["summary"],"all_arms":data["all_arms"],
        "gates":data["precommitted_gate_result"],"pass":data["all_precommitted_gates_passed"]},sort_keys=True))
if __name__=="__main__":
    main()
