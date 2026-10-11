#!/usr/bin/env python3
"""Stage32 all36 true artifact ZIP+inner JSON SHA case matched two-cadence decision.

Requires original 758 candidates x6 days. Never select winners, gate incomplete
/ corrupt monthly 1h or 10 daily 1m publisher SHA; report data censoring.
Fund 30/300U every time-ordered WATCH with original Stage27 cash ledger.
"""
import argparse
import collections
import hashlib
import json
import statistics
import zipfile
from pathlib import Path
try:
    import monster_v4_stage32_paired_1m_vs3m as research
    import monster_v4_stage27_shared_queue_cash_ledger as cash
except ImportError:
    from scripts import monster_v4_stage32_paired_1m_vs3m as research
    from scripts import monster_v4_stage27_shared_queue_cash_ledger as cash

ARTIFACT_PROOF=research.original.EVIDENCE/"monster_stage32_36_actual_fresh_dual_poll_artifact_proof_20261012.json"
SCHEMA="MONSTER_STAGE32_PAIRED_FRESH_758_TWO_CADENCES_REAL_SOURCE_V1"

def verify_zip(path,claim):
    blob=Path(path).read_bytes()
    if hashlib.sha256(blob).hexdigest()!=claim["zip_sha256"]:
        raise ValueError("STAGE32_ARTIFACT_ZIP_SHA256_MISMATCH")
    member=f"monster_stage32_{claim['date']}_shard{claim['shard']}.json"
    with zipfile.ZipFile(path) as z:
        if z.namelist()!=[member] or z.getinfo(member).file_size>40_000_000:
            raise ValueError("STAGE32_UNKNOWN_OR_TOO_LARGE_ARTIFACT_MEMBER")
        raw=z.read(member)
    if hashlib.sha256(raw).hexdigest()!=claim["raw_json_sha256"]:
        raise ValueError("STAGE32_ARTIFACT_JSON_SHA256_MISMATCH")
    d=json.loads(raw)
    if d["schema"]!=SCHEMA or d["date"]!=claim["date"] or d["shard"]!=claim["shard"]:
        raise ValueError("STAGE32_SHA_MATCH_BUT_WRONG_SOURCE_IDENTITY")
    cases=d["results"]
    if len(cases) not in (126,127) or len({x["symbol"] for x in cases})!=len(cases):
        raise ValueError("STAGE32_SOURCE_SHARD_NOT_ALL_126_127")
    if any(x["date"]!=d["date"] for x in cases):
        raise ValueError("STAGE32_MIXED_CALENDAR_COINS")
    if len(cases)!=d["summary"]["total_attempted"]:
        raise ValueError("STAGE32_ATTEMPTED_SOURCE_COUNT_NOT_MATCHED")
    for row in cases:
        if row["status"]!="COMPLETE_BOTH_168H":
            if row["status"] not in ("CENSORED_GT_NOT_COMPLETE_168H","CENSORED_MISSING_MINUTE_ARCHIVE","CENSORED_GAPPED_216H_MINUTE_ARCHIVE"):
                raise ValueError("STAGE32_SOURCE_FAILURE_DROPPED_AS_CENSOR")
            continue
        if len(row.get("monthly_GT_official_publisher_SHA256",""))!=64:
            raise ValueError("STAGE32_MISSING_TRUE_MONTHLY_PUBLISHER_SHA")
        proof=row.get("ten_daily_1m_publisher_sha256")
        if len(proof)!=10 or len({p["date"] for p in proof})!=10 or any(len(p.get("sha256",""))!=64 for p in proof):
            raise ValueError("STAGE32_MISSING_TRUE_DAILY_PUBLISHER_SHA")
        a,b=row["V4_original3m"],row["V4_candidate1m"]
        if (a["polls"],b["polls"])!=(3360,10080):
            raise ValueError("STAGE32_ARM_NOT_TRUE_ORIGINAL_FULL168H")
        for src in (a,b):
            if src["continuous_sqlite_reset_count"]!=0 or len(src["trade_proxies"])!=src["watch_count"]:
                raise ValueError("STAGE32_REPLAY_WATCH_OR_STATE_DRIFT")
        for multiple in (2,5,10):
            t=str(multiple)+"x"
            if row["labels_original3m"][t]["is_gt_positive"]!=row["labels_candidate1m"][t]["is_gt_positive"]:
                raise ValueError("STAGE32_DIFFERENT_FUTURE_TRUTH_BY_CADENCE")
    if sum(x["status"]=="COMPLETE_BOTH_168H" for x in cases)!=d["summary"]["paired_valid"]:
        raise ValueError("STAGE32_VALID_CASE_COUNT_DISAGREES")
    return d

def original_cohort(reports):
    days=research.NEW_DAYS
    if set(reports)!=set(days) or any(set(reports[d])!=set(range(6)) for d in days):
        raise ValueError("STAGE32_MISSING_ANY_OF_36_SIX_DAY_SHARDS")
    all_rows={}
    for day in days:
        rows=[r for sh in range(6) for r in reports[day][sh]["results"]]
        if len(rows)!=758 or len({r["symbol"] for r in rows})!=758:
            raise ValueError("STAGE32_INCOMPLETE_DATE_758_SYMBOLS")
        all_rows[day]=rows
    stable={r["symbol"] for r in all_rows[days[0]]}
    if any({x["symbol"] for x in all_rows[d]}!=stable for d in days):
        raise ValueError("STAGE32_FULL_MARKET_COHORT_CHANGED_ACROSS_FROZEN_DATES")
    return [r for d in days for r in all_rows[d]]

def candidate_entries(valid,arm,slippage):
    entries=[];overlap=0
    for row in valid:
        for t in row[arm]["trade_proxies"]:
            p=t["proxy_"+str(slippage)+"bps"]
            if p is None or p["status"]=="SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED":
                overlap+=1
                continue
            if p["status"]!="PRICE_PROXY_ONLY" and not p["status"].startswith("CENSORED_"):
                raise ValueError("STAGE32_BAD_REAL_MINUTE_TRADE_PROXY_STATUS")
            entries.append({"date":row["date"],"symbol":row["symbol"],
                "watch_utc":t["watch_utc"],"proxy_status":p["status"],"net_pct":p.get("net_pct")})
    entries.sort(key=lambda x:(x["watch_utc"],x["date"],x["symbol"]))
    if len(entries)+overlap!=sum(r[arm]["watch_count"] for r in valid):
        raise ValueError("STAGE32_FUTURE_EXIT_SELECTION_LOSS")
    return entries,overlap

def arm_economics(valid,arm):
    d={}
    for cost in (20,100):
        entries,skips=candidate_entries(valid,arm,cost)
        px=[r["net_pct"] for r in entries if r["proxy_status"]=="PRICE_PROXY_ONLY"]
        censored=len(entries)-len(px)
        if len(px)+censored+skips!=sum(r[arm]["watch_count"] for r in valid):
            raise ValueError("STAGE32_TRADE_SOURCE_MISSING_OR_OVERLAP")
        cash_cases={}
        for initial,slots in ((30,1),(300,10)):
            for unknown_return in (100,0):
                key=f"{initial}U_{slots}SLOT_{cost}BPS_CENSORED_{unknown_return}PCT"
                value=cash.money_ledger(entries,initial,slots,"FIXED_30U",cost,unknown_return)
                cash_cases[key]={k:v for k,v in value.items() if k!="selected_cases"}
        d[str(cost)]={"all_watch":len(entries)+skips,"valid_trade_proxies":len(px),
             "source_exit_censored":censored,"prior_same_symbol_overlap":skips,
             "wins":sum(x>0 for x in px),"losses":sum(x<0 for x in px),
             "median_net_pct":round(statistics.median(px),6) if px else None,
             "independent_each_30U_PnL":round(sum(.3*x for x in px),6),
             "cash_funded_no_overdraft":cash_cases}
    return d

def study(reports):
    src=original_cohort(reports)
    valid=[r for r in src if r["status"]=="COMPLETE_BOTH_168H"]
    n=len(valid)
    statuses=dict(collections.Counter(r["status"] for r in src))
    out={"schema":"MONSTER_STAGE32_FULL6_NEW_DATE_ORIGINAL36_SHA_PAIRED_1M_VS3M_V4_V1",
         "all36_original_ZIP_and_JSON_SHA_recomputed":True,
         "dates":list(research.NEW_DAYS),
         "total_original_758x6_attempts":len(src),"same_market_cohort":True,
         "paired_168h_complete_symbol_dates":n,
         "censored_status_counts":statuses,
         "actual_original_3m_WATCH":sum(r["V4_original3m"]["watch_count"] for r in valid),
         "actual_candidate_1m_WATCH":sum(r["V4_candidate1m"]["watch_count"] for r in valid),
         "actual_original_3m_D1":sum(r["V4_original3m"]["setups"] for r in valid),
         "actual_candidate_1m_D1":sum(r["V4_candidate1m"]["setups"] for r in valid),
         "original_3m_polls":3360*n,"candidate_1m_polls":10080*n}
    for multiple in (2,5,10):
        t=str(multiple)+"x";gtpos=[r for r in valid if r["labels_original3m"][t]["is_gt_positive"]]
        d={"all_2_5_10x_high_GT_count":len(gtpos),"per_event":[]}
        for arm,label in (("3min","labels_original3m"),("1min","labels_candidate1m")):
            cls=collections.Counter(r[label][t]["classification"] for r in gtpos)
            near=[r[label][t]["nearest_pre_cross_lead_min"] for r in gtpos
                  if r[label][t]["nearest_pre_cross_lead_min"] is not None]
            d[arm]={"early":cls["EARLY"],"late":cls["LATE"],"no_watch":cls["NO_WATCH"],
                    "nearest_pre_cross_alert_lead_median":round(statistics.median(near),6) if near else None,
                    "WATCH_within_6h_pre_cross":sum(v<=360 for v in near),
                    "WATCH_within_24h_pre_cross":sum(v<=1440 for v in near)}
        for r in gtpos:
            d["per_event"].append({"date":r["date"],"symbol":r["symbol"],
                "1min":r["labels_candidate1m"][t],"3min":r["labels_original3m"][t]})
        out["GT_"+t]=d
    out["by_date"]={}
    for day in research.NEW_DAYS:
        rows=[r for r in valid if r["date"]==day]
        out["by_date"][day]={"joint_complete":len(rows),
           "WATCH3m":sum(r["V4_original3m"]["watch_count"] for r in rows),
           "WATCH1m":sum(r["V4_candidate1m"]["watch_count"] for r in rows),
           "gross2x":sum(r["labels_original3m"]["2x"]["is_gt_positive"] for r in rows),
           "gross2x_early3m":sum(r["labels_original3m"]["2x"]["classification"]=="EARLY" for r in rows),
           "gross2x_early1m":sum(r["labels_candidate1m"]["2x"]["classification"]=="EARLY" for r in rows)}
    out["economic_original3min"]=arm_economics(valid,"V4_original3m")
    out["economic_candidate1min"]=arm_economics(valid,"V4_candidate1m")
    old=out["economic_original3min"];new=out["economic_candidate1min"]
    def net(d,cost):
        return d[str(cost)]["cash_funded_no_overdraft"][f"300U_10SLOT_{cost}BPS_CENSORED_100PCT"]["realized_proxy_profit_USDT"]
    out["pre_frozen_decision_gates"]={
        "six_original_full_market_date_pairs":len(out["by_date"])==6,
        "1m_improves_or_equals_2x_early_recall":out["GT_2x"]["1min"]["early"]>=out["GT_2x"]["3min"]["early"],
        "1m_300U_20bps_optimistic_returns_positive":net(new,20)>0,
        "1m_300U_100bps_optimistic_returns_positive":net(new,100)>0,
        "1m_net_better_than_3m_at_20bps":net(new,20)>=net(old,20),
        "1m_net_better_than_3m_at_100bps":net(new,100)>=net(old,100),
        "1m_new_candidate_evaluable_gt_30":new["20"]["valid_trade_proxies"]-old["20"]["valid_trade_proxies"]>=30,
        "1m_censored_fraction_lte_20pct":new["20"]["source_exit_censored"]/max(1,new["20"]["source_exit_censored"]+new["20"]["valid_trade_proxies"])<=.2,
        "historical_L2_real_fill_verified":False,
        "independent_other_AI_review_done":False}
    out["all_deploy_gates_passed"]=all(out["pre_frozen_decision_gates"].values())
    out["both_arms_true_global_Spot_plus_Futures_queue"]="NOT_REPLAYED"
    out["historical_L2"] = "UNVERIFIED"
    out["other_AI_review"]="NOT_DONE"
    out["Monster_deployment"]="NO_GO"
    out["Frank"]="UNCHANGED"
    out["real_Gmail"]="OFF"
    out["auto_trading"]="NO_GO"
    return out

def run(files):
    cfg=research.frozen()
    proof=json.loads(ARTIFACT_PROOF.read_text(encoding="utf-8"))
    index={(x["date"],x["shard"]):x for x in proof["artifacts"]}
    if len(index)!=36 or len(files)!=36 or set(k[0] for k in index)!=set(research.NEW_DAYS):
        raise ValueError("STAGE32_NOT_ALL_36_SOURCE_ZIP_PROOFS")
    loaded={}
    for p in files:
        with zipfile.ZipFile(p) as z:
            names=z.namelist()
        if len(names)!=1 or not names[0].startswith("monster_stage32_") or "_shard" not in names[0]:
            raise ValueError("STAGE32_INCORRECT_ORIGINAL_ZIP_MEMBER")
        date,shard=names[0].removeprefix("monster_stage32_").removesuffix(".json").split("_shard")
        key=(date,int(shard))
        if key not in index or key in loaded:
            raise ValueError("STAGE32_MISSING_OR_DUPLICATE_ACTUAL_SOURCE")
        loaded[key]=verify_zip(p,index[key])
    mapping={}
    for (d,s),r in loaded.items():mapping.setdefault(d,{})[s]=r
    return study(mapping)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-zips",nargs=36,required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    r=run(a.original_zips)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    compact={k:v for k,v in r.items() if k not in ("GT_2x","GT_5x","GT_10x","economic_original3min","economic_candidate1min")}
    compact["GT"]={m:{k:v for k,v in r["GT_"+m].items() if k!="per_event"} for m in ("2x","5x","10x")}
    compact["funded"]={arm:{c:{k:v for k,v in money["cash_funded_no_overdraft"].items()
                   if "300U_10SLOT" in k and "100PCT" in k}
                 for c,money in r["economic_"+arm].items()} for arm in ("original3min","candidate1min")}
    compact["price_proxy"]={arm:{k:{k2:v2 for k2,v2 in d.items() if k2!="cash_funded_no_overdraft"}
           for k,d in r["economic_"+arm].items()} for arm in ("original3min","candidate1min")}
    print("STAGE32_FINAL_VERIFIED_JSON "+json.dumps(compact,sort_keys=True),flush=True)
if __name__=="__main__":main()
