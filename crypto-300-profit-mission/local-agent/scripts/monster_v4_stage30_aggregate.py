#!/usr/bin/env python3
"""Stage30 independent NEW calendar dates: exact 36 signed-source outputs.

Requires 36 real GitHub Actions ZIPs, recomputed each ZIP+inner JSON SHA256.
No source label into WATCH time and no false negative when monthly/1m missing.
8+ burst must have >=6 independent UTC polls over >=3 full date windows to
even consider a generalization claim (not automatically BUY authorization).
"""
import argparse
import collections
import hashlib
import json
import statistics
import zipfile
from pathlib import Path

try:
    import monster_v4_stage27_shared_queue_cash_ledger as prior
    import monster_v4_stage29_watch_burst_price_research as diagnostic
except ImportError:
    from scripts import monster_v4_stage27_shared_queue_cash_ledger as prior
    from scripts import monster_v4_stage29_watch_burst_price_research as diagnostic

EVIDENCE=prior.EVIDENCE
PREREG=EVIDENCE/"monster_stage30_six_new_dates_full758_7d_watch_holdout_prereg_20261011.json"
ARTS=EVIDENCE/"monster_stage30_original36_newdates_artifact_SHA_proof_20261011.json"
SHARDS=6
SCHEMA="MONSTER_STAGE30_NEW_FROZEN_758x6_FULL168H_ORIGINAL_V4_SHA_VERIFIED_V1"

def immutable():
    p=json.loads(PREREG.read_text(encoding="utf-8"))
    if p["schema"]!="MONSTER_STAGE30_NEW_SIX_DATE_758_FULL168H_ORIGINAL_V4_HOLDOUT_FROZEN_BEFORE_SOURCE_V1" or len(p["new_dates_UTC"])!=6:
        raise ValueError("STAGE30_AGG_BAD_FROZEN_CONTRACT")
    return p

def decode(path,proof):
    data=Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest()!=proof["zip_sha256"]:
        raise ValueError("STAGE30_SOURCE_ZIP_SHA_CHANGED")
    expected=f"monster_stage30_{proof['date']}_shard{proof['shard']}.json"
    with zipfile.ZipFile(path) as z:
        if z.namelist()!=[expected] or z.getinfo(expected).file_size>20_000_000:
            raise ValueError("STAGE30_UNEXPECTED_ZIP_MEMBER")
        raw=z.read(expected)
    if hashlib.sha256(raw).hexdigest()!=proof["raw_json_sha256"]:
        raise ValueError("STAGE30_SOURCE_INTERNAL_JSON_SHA_CHANGED")
    doc=json.loads(raw)
    if doc["schema"]!=SCHEMA or (doc["date"],doc["shard"])!=(proof["date"],proof["shard"]):
        raise ValueError("STAGE30_SOURCE_IDENTITY_CHANGED")
    cases=doc["cases"]
    if len(cases) not in (126,127) or len({r["symbol"] for r in cases})!=len(cases):
        raise ValueError("STAGE30_NOT_FULL_SYMBOL_SHARD")
    if doc["summary"]["attempted"]!=len(cases):
        raise ValueError("STAGE30_ATTEMPTED_DISAGREE")
    if collections.Counter(r["status"] for r in cases)!=collections.Counter(doc["summary"]["source_status_counts"]):
        raise ValueError("STAGE30_SOURCE_STATUSES_DISAGREE")
    for r in cases:
        if r["date"]!=proof["date"]:
            raise ValueError("STAGE30_WRONG_ORIGINAL_DATE")
        if r["status"]=="COMPLETE_168H_CONTINUOUS_V4":
            if len(r.get("hourly_GT_monthly_SHA256") or "")!=64 or r.get("hourly_GT_original_status")!="VERIFIED_COMPLETE_168H":
                raise ValueError("STAGE30_PUBLISHER_GT_MONTHLY_SOURCE_SHA_ABSENT")
            hashes=r["official_source_SHA256_days"]
            if len(hashes)!=10 or len({h["date"] for h in hashes})!=10 or any(len(h.get("sha256",""))!=64 for h in hashes):
                raise ValueError("STAGE30_10_GENUINE_OFFICIAL_SOURCE_SHA_MISSING")
            c=r["continuous"]
            if c["continuous_sqlite_reset_count"]!=0 or c["polls"]!=3360:
                raise ValueError("STAGE30_NONCAUSAL_STATE_RESET")
    return doc

def register(data):
    p=immutable()
    if set(data)!=set(p["new_dates_UTC"]) or any(len(data[day])!=SHARDS for day in data):
        raise ValueError("STAGE30_INCOMPLETE_FULL_SIX_DATE_SHARDS")
    result={}
    for day,shards in data.items():
        cases=[r for n in range(SHARDS) for r in shards[n]["cases"]]
        if len(cases)!=758 or len(set(x["symbol"] for x in cases))!=758:
            raise ValueError("STAGE30_NOT_ALL_758_SYMBOL_DATE")
        result[day]=cases
    syms={x["symbol"] for x in result[p["new_dates_UTC"][0]]}
    if any({x["symbol"] for x in rows}!=syms for rows in result.values()):
        raise ValueError("STAGE30_COHORT_CHANGED_BY_DAY")
    return result

def arm_censored(events,cost):
    return diagnostic.arm_stats(events,cost)

def funded(evs,slip):
    trades=[];seen_previous=0
    for e in evs:
        p=e["cost_proxies"][str(slip)]
        if p["status"]=="SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED":
            seen_previous+=1
            continue
        trades.append({"date":e["date"],"symbol":e["symbol"],
                       "watch_utc":e["watch_utc"],
                       "proxy_status":p["status"],"net_pct":p.get("net_pct")})
    trades.sort(key=lambda x:(x["watch_utc"],x["date"],x["symbol"]))
    outputs={}
    for initial,slots in ((30,1),(300,10)):
        for censored in (100,0):
            k=f"{initial}USDT_{slots}SLOT_CENSORED_RECOVERY_{censored}PCT"
            record=prior.money_ledger(trades,initial,slots,"FIXED_30U",slip,censored)
            outputs[k]={k:v for k,v in record.items() if k!="selected_cases"}
    return {"eligible_non_overlapping_entries":len(trades),
            "original_same_symbol_overlap_skip":seen_previous,
            "funded_cash_by_recovery_assumption":outputs}

def summarize(full):
    frozen=immutable()
    byday=register(full)
    rows=[r for d in frozen["new_dates_UTC"] for r in byday[d]]
    if len(rows)!=4548:raise ValueError("STAGE30_EXPECT_758_X_6")
    source_counts=collections.Counter(r["status"] for r in rows)
    disallowed=[s for s in source_counts if "NETWORK" in s or "INTEGRITY_REJECTED" in s or "HTTP_FAILED" in s]
    if disallowed:raise ValueError("STAGE30_SOURCE_ERRORS_FAIL_CLOSED:"+repr(disallowed))
    valid=[r for r in rows if r["status"]=="COMPLETE_168H_CONTINUOUS_V4"]
    evs=diagnostic.make_event_cases(valid)
    groups={}
    burst_polls={}
    for g in diagnostic.BINS:
        subset=[e for e in evs if e["bucket"]==g]
        polls={(x["date"],x["watch_utc"]) for x in subset}
        if g=="BURST_8PLUS":
            burst_polls={f"{d}|{t}":sum(x["date"]==d and x["watch_utc"]==t for x in subset)
                        for d,t in sorted(polls)}
        groups[g]={"WATCH_count":len(subset),
            "independent_three_minute_WATCH_poll_episodes":len(polls),
            "independent_frozen_calendar_dates_with_group":len({x["date"] for x in subset}),
            "price_proxy20":arm_censored(subset,20),
            "price_proxy100":arm_censored(subset,100),
            "funded_fixed_lot_20bps":funded(subset,20),
            "funded_fixed_lot_100bps":funded(subset,100),
            "watch_with_frozen_GT2x_coin_baseline_not_individual_2x":sum(x["gross_high_2x_in_frozen_168h"] for x in subset),
            "watch_within_six_hours_of_first_2x":sum(x["minutes_until_first_2x_if_valid"] is not None
                    and 0<=x["minutes_until_first_2x_if_valid"]<=360 for x in subset),
            "per_calendar_date_20bps":{day:arm_censored([x for x in subset if x["date"]==day],20)
                                         for day in frozen["new_dates_UTC"]}}
    b=groups["BURST_8PLUS"]
    q=b["price_proxy20"];stress=b["price_proxy100"]
    censor_fraction=(q["source_censored_excluding_overlap"]/
              max(1,q["source_censored_excluding_overlap"]+q["proxy_evaluable"]))
    cash=b["funded_fixed_lot_20bps"]["funded_cash_by_recovery_assumption"][
          "300USDT_10SLOT_CENSORED_RECOVERY_100PCT"]["realized_proxy_profit_USDT"]
    gate={"independent_burst_poll_episodes_gte_6":b["independent_three_minute_WATCH_poll_episodes"]>=6,
          "burst_dates_gte_3":b["independent_frozen_calendar_dates_with_group"]>=3,
          "burst_evaluable_gte_30":q["proxy_evaluable"]>=30,
          "win_fraction_gte_55pct":q["wins"]/max(1,q["proxy_evaluable"])>=0.55,
          "median20_pct_gt0":q["median_net_pct"] is not None and q["median_net_pct"]>0,
          "median100_pct_gt0":stress["median_net_pct"] is not None and stress["median_net_pct"]>0,
          "300U_funded_optimistic_net_gt0":cash>0,
          "source_exit_censor_fraction_lte_20pct":censor_fraction<=0.2,
          "actual_historical_L2_and_real_fill_verified":False,
          "other_AI_review_complete":False}
    early={}
    for mult in (2,5,10):
        positive=[r for r in valid if r["labels"][str(mult)+"x"]["gross_hourly_high_gt"]]
        cls=collections.Counter(r["labels"][str(mult)+"x"]["classification"] for r in positive)
        recent={}
        for r in positive:
            cross=prior.previous.utc(r["labels"][str(mult)+"x"]["real_1m_cross_utc"])
            past=[(cross-prior.previous.utc(t)).total_seconds()/60
                  for t in r["continuous"]["watch_utcs"] if prior.previous.utc(t)<=cross]
            nearest=min(past) if past else None
            recent[(r["date"],r["symbol"])]=nearest
        early[str(mult)+"x"]={"valid_GT_positives":len(positive),
            "prior_WATCH_within_6h_of_true_cross":sum(x is not None and 0<=x<=360 for x in recent.values()),
            "prior_WATCH_within_24h_of_true_cross":sum(x is not None and 0<=x<=1440 for x in recent.values()),
            "WATCH_before_1m_high_cross":cls["WATCH_BEFORE_OR_AT_REAL_FIRST_1M_CROSS"],
            "late":cls["WATCH_AFTER_REAL_FIRST_1M_CROSS"],
            "no_watch":cls["NO_WATCH_IN_CONTINUOUS_168H"],
            "members":[{"date":r["date"],"symbol":r["symbol"],
                "first_watch_utc":r["labels"][str(mult)+"x"]["first_v4_watch_utc"],
                "first_real_cross_utc":r["labels"][str(mult)+"x"]["real_1m_cross_utc"],
                "classification":r["labels"][str(mult)+"x"]["classification"],
                "nearest_prior_WATCH_lead_min":recent[(r["date"],r["symbol"])]}
                   for r in positive]}
    return {"schema":"MONSTER_STAGE30_FULL_SIX_UNSEEN_DATE_758_168H_ALL_ORIGINAL_SHA_RECOMPUTED_V1",
      "all_36_ZIP_and_raw_JSON_source_SHA256_reverified":True,
      "dates":frozen["new_dates_UTC"],
      "source_attempted":len(rows),"source_complete_valid":len(valid),
      "source_censor_status_counts":dict(source_counts),
      "real_original_3m_polls":sum(r["continuous"]["polls"] for r in valid),
      "WATCH_events":len(evs),
      "D1_SETUPS_individual_per_symbol":sum(r["continuous"]["setups"] for r in valid),
      "independent_watch_price_proxy_20bps":arm_censored(evs,20),
      "independent_watch_price_proxy_100bps":arm_censored(evs,100),
      "verified_2x_5x_10x_rise_by_month_high":early,
      "watch_concurrency_original_same_3min_groups":groups,
      "burst_three_minute_episodes":burst_polls,
      "pre_registered_burst_release_gate":gate,
      "all_required_positive_profit_and_validity_gates":all(gate.values()),
      "independent_other_ai_review":"NOT_DONE",
      "production_V4_changed":False,
      "real_fill_verified":False,
      "full_global_spot_plus_futures_shared_queue_replayed":False,
      "mac_deployment":"NO_GO","real_gmail":"OFF","trading":"NO_GO","frank":"UNCHANGED"}

def run(files,proof=ARTS):
    rec=json.loads(Path(proof).read_text(encoding="utf-8"))
    p=immutable()
    arts={(a["date"],a["shard"]):a for a in rec["artifacts"]}
    if len(arts)!=36 or len(files)!=36 or set(d for d,_ in arts)!=set(p["new_dates_UTC"]):
        raise ValueError("STAGE30_ARTIFACT_PROOF_NOT_ALL_36")
    loaded={}
    for path in files:
        with zipfile.ZipFile(path) as z:
            names=z.namelist()
        if len(names)!=1 or not names[0].startswith("monster_stage30_") or not names[0].endswith(".json"):
            raise ValueError("STAGE30_WRONG_ZIP_MEMBER")
        d,name=names[0].removeprefix("monster_stage30_").removesuffix(".json").split("_shard")
        key=(d,int(name))
        if key not in arts or key in loaded:
            raise ValueError("STAGE30_DUPLICATE_OR_UNKNOWN_SOURCE")
        loaded[key]=decode(path,arts[key])
    matrix={}
    for (d,s),doc in loaded.items():
        matrix.setdefault(d,{})[s]=doc
    return summarize(matrix)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-zips",nargs=36,required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    d=run(a.original_zips)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    trim={k:v for k,v in d.items() if k not in (
        "watch_concurrency_original_same_3min_groups","verified_2x_5x_10x_rise_by_month_high")}
    trim["rise"]={k:{kk:vv for kk,vv in val.items() if kk!="members"}
                  for k,val in d["verified_2x_5x_10x_rise_by_month_high"].items()}
    trim["burst_group"]={k:v for k,v in d["watch_concurrency_original_same_3min_groups"]["BURST_8PLUS"].items()
                         if k not in ("funded_fixed_lot_20bps","funded_fixed_lot_100bps","per_calendar_date_20bps")}
    print("STAGE30_AGGREGATE_JSON "+json.dumps(trim,sort_keys=True),flush=True)
if __name__=="__main__":main()
