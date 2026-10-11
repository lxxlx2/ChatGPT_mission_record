#!/usr/bin/env python3
"""Stage23 full-ten-archive rehash + risk/overextension holdout verdict.

Uses original SHA256 matched per-date outputs, identical research sim exits,
and 30USDT capital-slot chronology. No optimizer, production or orderbook fills.
"""
import argparse
import hashlib
import json
import statistics
import zipfile
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path

EVIDENCE=Path(__file__).resolve().parents[2]/"monster/evidence"
PROOF=EVIDENCE/"monster_stage23_real10_frozen_d1_overextension_artifact_proof_20261011.json"
MANIFEST=EVIDENCE/"monster_stage23_unseen_overextension_filter_prereg_20261011.json"
ARMS=("D_BASELINE_STAGE20_QUALITY_BOUNDED6H_20BPS",
      "F_OVEREXTENSION_FILTER_QUALITY_BOUNDED6H_20BPS",
      "G_OVEREXTENSION_FILTER_QUALITY_BOUNDED6H_100BPS")

def digest(data):return hashlib.sha256(data).hexdigest()

def read_zip(path, expected):
    zipped=Path(path).read_bytes()
    if digest(zipped)!=expected["zip_sha256"]:
        raise ValueError("STAGE23_ZIP_SHA256_MISMATCH")
    member="monster_stage23_"+expected["date"]+".json"
    with zipfile.ZipFile(path) as z:
        if z.namelist()!=[member] or z.getinfo(member).file_size>12_000_000:
            raise ValueError("STAGE23_BAD_ZIP_MEMBER")
        raw=z.read(member)
    if digest(raw)!=expected["raw_json_sha256"]:
        raise ValueError("STAGE23_RAW_JSON_SHA256_MISMATCH")
    obj=json.loads(raw)
    if obj.get("schema")!="MONSTER_STAGE23_FROZEN_NEW_DATES_FIRST_D1_OVEREXTENSION_V1" or obj["date"]!=expected["date"]:
        raise ValueError("STAGE23_SOURCE_IDENTITY_CHANGED")
    if obj.get("unchanged_stage20_git_blob")!="93e2065e354182be3d2136be49c760674b485381":
        raise ValueError("STAGE23_ORIGINAL_V4_CODE_DIFFERENT")
    if len(obj["cases"])!=758 or len({x["symbol"] for x in obj["cases"]})!=758:
        raise ValueError("STAGE23_NOT_FULL_758_UNIVERSE")
    if Counter(x["status"] for x in obj["cases"])!=Counter(obj["summary"]["status"]):
        raise ValueError("STAGE23_SOURCE_COUNTS_MISMATCH")
    return obj

def metrics(selected):
    valid=[x for x in selected if x["status"]=="PRICE_PROXY_ONLY"]
    values=[x["net_pct"] for x in valid]
    return {
      "selected":len(selected),"evaluable":len(valid),
      "wins":sum(x>0 for x in values),"losses":sum(x<0 for x in values),
      "median_net_pct":round(statistics.median(values),6) if values else None,
      "mean_net_pct":round(statistics.mean(values),6) if values else None,
      "sum_independent_30u":round(sum(x*.3 for x in values),6),
      "censored":len(selected)-len(valid),
      "exits":dict(Counter(x.get("exit_reason") for x in valid))}

def single_slot(candidates,arm):
    # Signals evaluated chronologically, no sorting by future price or success.
    queue=sorted((datetime.fromisoformat(r["first_v4_d1_utc"].replace("Z","+00:00")),
                day,r) for day,r in candidates
                if r["frozen_arm_proxies"][arm] is not None)
    free=datetime.min.replace(tzinfo=timezone.utc)
    kept=[];skipped=0
    for signal,day,row in queue:
        entry=signal+timedelta(minutes=3)
        if entry<free:
            skipped+=1
            continue
        p=row["frozen_arm_proxies"][arm]
        if p["status"]=="PRICE_PROXY_ONLY" and p.get("exit_utc"):
            exit_=datetime.fromisoformat(p["exit_utc"].replace("Z","+00:00"))
            free=max(entry+timedelta(minutes=1),exit_)
        else:
            free=entry+timedelta(hours=6)
        kept.append(p)
    v=[x["net_pct"] for x in kept if x["status"]=="PRICE_PROXY_ONLY"]
    return {"selected_by_clock":len(kept),"skipped_capital_busy":skipped,
        "evaluable":len(v),"wins":sum(x>0 for x in v),
        "losses":sum(x<0 for x in v),"censored":len(kept)-len(v),
        "simulated_30u_net_usdt":round(sum(x*.3 for x in v),6),
        "actual_executed_trades":False}

def run(paths,proof_file=PROOF,manifest_file=MANIFEST):
    proof=json.loads(Path(proof_file).read_text(encoding="utf-8"))
    prereg=json.loads(Path(manifest_file).read_text(encoding="utf-8"))
    days=prereg["dates"]
    artifacts={r["date"]:r for r in proof["artifacts"]}
    if len(paths)!=10 or len(days)!=10 or len(artifacts)!=10 or set(days)!=set(artifacts):
        raise ValueError("STAGE23_REQUIRE_ALL_FROZEN_DATES")
    reports={}
    for path in paths:
        with zipfile.ZipFile(path) as z:
            file=z.namelist()[0]
        date=file.removeprefix("monster_stage23_").removesuffix(".json")
        if date not in artifacts or date in reports:
            raise ValueError("STAGE23_DUPLICATE_OR_NONFROZEN_DATE")
        reports[date]=read_zip(path,artifacts[date])
    if set(reports)!=set(days):
        raise ValueError("STAGE23_INCOMPLETE_DATES")
    cases=[(d,r) for d in days for r in reports[d]["cases"]]
    valid=[(d,r) for d,r in cases if r["status"]=="COMPLETE_60H"]
    d1=[(d,r) for d,r in valid if "frozen_arm_proxies" in r]
    matched={}
    for arm in ARMS:
        p=[r["frozen_arm_proxies"][arm] for _,r in d1 if r["frozen_arm_proxies"][arm] is not None]
        matched[arm]=metrics(p)
        if matched[arm]["selected"]!=sum(reports[day]["summary"][arm]["selected"] for day in days):
            raise ValueError("STAGE23_ARM_DENOMINATOR_MISMATCH")
    f=matched[ARMS[1]]
    original=matched[ARMS[0]]
    rejected=[r for _,r in d1 if r["quality"]["quality_pass"] and not r["overextension_eligible"]]
    lost_profits=sum(r["frozen_arm_proxies"][ARMS[0]]["status"]=="PRICE_PROXY_ONLY" and
                    r["frozen_arm_proxies"][ARMS[0]]["net_pct"]>0 for r in rejected)
    avoided_stops=sum(r["frozen_arm_proxies"][ARMS[0]]["status"]=="PRICE_PROXY_ONLY" and
                    r["frozen_arm_proxies"][ARMS[0]]["exit_reason"]=="STOP" for r in rejected)
    complete_dates=sum(any(d==day and r["overextension_eligible"] and
                      r["frozen_arm_proxies"][ARMS[1]]["status"]=="PRICE_PROXY_ONLY"
                      for d,r in d1) for day in days)
    slot=single_slot(d1,ARMS[1])
    gate=prereg["success_gate"]
    gates={
      "min_30_evaluable":f["evaluable"]>=gate["f_evaluable_min"],
      "min_6_distinct_dates":complete_dates>=gate["distinct_f_evaluable_dates_min"],
      "win_rate_ge_55pct":f["evaluable"]>0 and f["wins"]/f["evaluable"]>=gate["f_winning_fraction_min"],
      "net_median_positive":f["median_net_pct"] is not None and f["median_net_pct"]>0,
      "independent_30usdt_sum_positive":f["sum_independent_30u"]>0,
      "single_slot_30usdt_positive":slot["simulated_30u_net_usdt"]>0,
      "censor_fraction_le_20pct":f["selected"]>0 and f["censored"]/f["selected"]<=gate["f_censor_fraction_max"]
    }
    return {"schema":"MONSTER_STAGE23_EXACT_10_ORIGINAL_ARTIFACTS_RECOMPUTED_V1",
       "all_official_artifact_zip_and_raw_json_sha256_verified":True,
       "dates":days,
       "summary":{"attempted":len(cases),"complete_60h":len(valid),
          "status":dict(Counter(x["status"] for _,x in cases)),
          "v4_watch":sum(r["v4_watch"] for _,r in valid),
          "v4_d1":sum(r["v4_d1_episodes"] for _,r in valid),
          "unique_d1":len(d1),
          "original_quality":sum(r["quality"]["quality_pass"] for _,r in d1),
          "overextension_filter_selected":sum(r["overextension_eligible"] for _,r in d1),
          "filter_rejected_original_quality":len(rejected),
          "lost_positive_baseline_proxy":lost_profits,
          "avoided_baseline_stop_proxy":avoided_stops},
       "arms":matched,"single_slot_30u_filtered":slot,
       "gates":gates,"all_preregistered_gates_passed":all(gates.values()),
       "real_orderbook_depth":"UNVERIFIED","strategy_deployed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifact-zips",nargs=10,required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    out=run(a.artifact_zips)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE23_AGGREGATED "+json.dumps({"summary":out["summary"],
       "arms":out["arms"],"gates":out["gates"],
       "pass":out["all_preregistered_gates_passed"],
       "slot":out["single_slot_30u_filtered"]},sort_keys=True),flush=True)
if __name__=="__main__":
    main()
