#!/usr/bin/env python3
"""Stage26 original 36 GHA ZIP/JSON SHA verified full market full week aggregator.

No ex-post threshold selection. Produces honest source-censored denominator,
D0/SETUP alerts and one/ten 30USDT sequential capital-slot cost proxies.
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
FROZEN=EVIDENCE/"monster_stage26_full168h_original_v4_continuous_758x6_prereg_20261011.json"
PROOF=EVIDENCE/"monster_stage26_verified_sharded_168h_artifact_proof_20261011.json"
SHARDS=6

def utc(time):
    return datetime.fromisoformat(time.replace("Z","+00:00"))

def sha(bytes_):
    return hashlib.sha256(bytes_).hexdigest()

def load_zip(path,expected):
    data=Path(path).read_bytes()
    if sha(data)!=expected["zip_sha256"]:
        raise ValueError("STAGE26_ARTIFACT_ZIP_SHA_CHANGED")
    member=f"monster_stage26_{expected['date']}_shard{expected['shard']}.json"
    with zipfile.ZipFile(path) as z:
        if z.namelist()!=[member] or z.getinfo(member).file_size>15_000_000:
            raise ValueError("STAGE26_UNEXPECTED_ARTIFACT_MEMBER")
        raw=z.read(member)
    if sha(raw)!=expected["raw_json_sha256"]:
        raise ValueError("STAGE26_ARTIFACT_UNCOMPRESSED_JSON_SHA_CHANGED")
    data=json.loads(raw)
    if data.get("schema")!="MONSTER_STAGE26_FULL168H_758_6DATE_PER_SYMBOL_CONTINUOUS_V4_V1":
        raise ValueError("STAGE26_RESULT_SCHEMA_DRIFT")
    if (data.get("date"),data.get("shard"))!=(expected["date"],expected["shard"]):
        raise ValueError("STAGE26_DATE_SHARD_IDENTITY_CHANGED")
    cases=data["cases"]
    if len(cases) not in (126,127) or len({x["symbol"] for x in cases})!=len(cases):
        raise ValueError("STAGE26_SHARD_758_COVERAGE_BROKEN")
    if data["summary"]["attempted"]!=len(cases):
        raise ValueError("STAGE26_SHARD_SUMMARY_COUNT_BAD")
    if Counter(r["status"] for r in cases)!=Counter(data["summary"]["statuses"]):
        raise ValueError("STAGE26_SHARD_SOURCE_STATUS_BAD")
    for row in cases:
        if row["date"]!=expected["date"]:
            raise ValueError("STAGE26_BAD_CASE_DAY")
        if row["status"]=="COMPLETE_168H_CONTINUOUS_V4":
            p=row.get("official_source_SHA256_days",[])
            if len(p)!=10 or len({x["date"] for x in p})!=10 or not all(
                len(x.get("sha256",""))==64 for x in p):
                raise ValueError("STAGE26_OFFICIAL_TEN_DAYS_SOURCE_SHA_MISSING")
            c=row["continuous"]
            if c["continuous_sqlite_reset_count"]!=0 or c["polls"]!=3360:
                raise ValueError("STAGE26_NOT_168H_SINGLE_STATE_REPLAY")
            if row["historical_execution_proven"] is not False:
                raise ValueError("STAGE26_FAKE_EXECUTABLE_PROOF")
    return data

def stats_for_arm(rows,key):
    q=[p[key] for r in rows if r["status"]=="COMPLETE_168H_CONTINUOUS_V4"
       for p in r["continuous"]["trade_proxies"]
       if p[key] is not None]
    eligible=[t["net_pct"] for t in q if t["status"]=="PRICE_PROXY_ONLY"]
    return {"watch_proxy_count":len(q),"evaluable":len(eligible),
      "wins":sum(v>0 for v in eligible),"losses":sum(v<0 for v in eligible),
      "missing_or_skipped":len(q)-len(eligible),
      "censor_and_skips":dict(Counter(t["status"] for t in q
                                  if t["status"]!="PRICE_PROXY_ONLY")),
      "median_net_pct":round(statistics.median(eligible),6) if eligible else None,
      "sum_independent_30usdt_proxy_pnl":round(sum(v*.3 for v in eligible),6)}

def one_or_ten_slot(rows, slots, cost):
    if slots not in (1,10):
        raise ValueError("STAGE26_CAPITAL_SLOTS_MUST_BE_1_OR_10")
    timeline=[]
    for row in rows:
        if row["status"]!="COMPLETE_168H_CONTINUOUS_V4":
            continue
        for item in row["continuous"]["trade_proxies"]:
            p=item[cost]
            if p is None or p["status"]=="SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED":
                continue
            timeline.append((utc(item["watch_utc"]),row["date"],row["symbol"],p))
    timeline.sort(key=lambda x:(x[0],x[1],x[2]))
    availability=[datetime.min.replace(tzinfo=timezone.utc)]*slots
    accepted=[];busy=0
    for when,day,symbol,proxy in timeline:
        entry=when+timedelta(minutes=3)
        free=[(t,i) for i,t in enumerate(availability) if t<=entry]
        if not free:
            busy+=1
            continue
        _,slot=min(free,key=lambda x:(x[0],x[1]))
        availability[slot]=entry+timedelta(hours=24)
        accepted.append({"date":day,"symbol":symbol,
                         "watch_utc":when.isoformat(),
                         "slot":slot,
                         "status":proxy["status"],
                         "net_pct":proxy.get("net_pct")})
    pnl=[r["net_pct"] for r in accepted if r["status"]=="PRICE_PROXY_ONLY"]
    return {"funded_slots":slots,"capital_usdt":slots*30,
       "selected_by_signal_chronology":len(accepted),
       "skipped_due_to_portfolio_busy":busy,
       "evaluable":len(pnl),"wins":sum(v>0 for v in pnl),
       "losses":sum(v<0 for v in pnl),
       "censored_held_24h":len(accepted)-len(pnl),
       "simulated_net_USDT":round(sum(v*.3 for v in pnl),6),
       "not_actual_order_fills":True,
       "selected_cases":accepted}

def summarize(reports,freeze):
    dates=freeze["frozen_dates_utc"]
    if set(d for d,_ in reports)!=set(dates) or len(reports)!=36:
        raise ValueError("STAGE26_ALL_SIX_DATES_36_SHARDS_REQUIRED")
    joined={}
    rows=[]
    for d in dates:
        cases=[r for n in range(6) for r in reports[d,n]["cases"]]
        if len(cases)!=758 or len({r["symbol"] for r in cases})!=758:
            raise ValueError("STAGE26_DATE_NOT_ALL_758_OR_DUPLICATE")
        rows.extend(cases)
        joined[d]=cases
    if any({r["symbol"] for r in joined[dates[0]]}!={r["symbol"] for r in joined[d]} for d in dates):
        raise ValueError("STAGE26_COHORT_DIFFERENT_BETWEEN_MONTHS")
    statuses=Counter(r["status"] for r in rows)
    valid=[r for r in rows if r["status"]=="COMPLETE_168H_CONTINUOUS_V4"]
    gt={}
    for mult in (2,5,10):
        confirmed=[r for r in valid if r["labels"][str(mult)+"x"]["gross_hourly_high_gt"]]
        classes=Counter(r["labels"][str(mult)+"x"]["classification"] for r in confirmed)
        recent6=0
        recent24=0
        recency={}
        for r in confirmed:
            cross=utc(r["labels"][str(mult)+"x"]["real_1m_cross_utc"])
            prior=[(cross-utc(x)).total_seconds()/60 for x in r["continuous"]["watch_utcs"] if utc(x)<=cross]
            nearest=min(prior) if prior else None
            recency[r["date"]+"|"+r["symbol"]]=round(nearest,6) if nearest is not None else None
            recent6+=bool(nearest is not None and 0<=nearest<=360)
            recent24+=bool(nearest is not None and 0<=nearest<=1440)
        gt[str(mult)+"x"]={
           "joint_verified_future_gross_high":len(confirmed),
           "watch_within_prior_6h_count":recent6,
           "watch_within_prior_24h_count":recent24,
           "early_or_same_first_minute_cross":classes["WATCH_BEFORE_OR_AT_REAL_FIRST_1M_CROSS"],
           "late":classes["WATCH_AFTER_REAL_FIRST_1M_CROSS"],
           "no_watch_through_full168h":classes["NO_WATCH_IN_CONTINUOUS_168H"],
           "classifications":dict(classes),
           "positive_event_register":[{
               "date":r["date"],"symbol":r["symbol"],
               "first_cross_1m":r["labels"][str(mult)+"x"]["real_1m_cross_utc"],
               "first_watch_utc":r["labels"][str(mult)+"x"]["first_v4_watch_utc"],
               "classification":r["labels"][str(mult)+"x"]["classification"],
               "lead_minutes":r["labels"][str(mult)+"x"]["lead_minutes"],
               "nearest_prior_watch_lead_minutes":recency[r["date"]+"|"+r["symbol"]]}
                  for r in confirmed]
        }
    watch_cases=[r for r in valid if r["continuous"]["watch_count"]>0]
    watch_hours=Counter(v[:13] for r in valid for v in r["continuous"]["watch_utcs"])
    alerts_by_day=Counter(r["date"] for r in valid for _ in r["continuous"]["watch_utcs"])
    no2x=sum(not r["labels"]["2x"]["gross_hourly_high_gt"] for r in watch_cases)
    cost20=stats_for_arm(rows,"proxy_20bps")
    cost100=stats_for_arm(rows,"proxy_100bps")
    return {
       "schema":"MONSTER_STAGE26_REAL_6DATE_758_FULL168H_ORIGINAL_V4_ARCHIVE_SHA_RECOMPUTE_V1",
       "exactly_36_original_ZIP_and_JSON_SHA256_verified":True,
       "research_dates_already_exposed":True,
       "attempted":len(rows),
       "source_status":dict(statuses),
       "fully_publisher_verified_original_168h_scan":len(valid),
       "original_3min_poll_count":sum(r["continuous"]["polls"] for r in valid),
       "all_watch_events":sum(r["continuous"]["watch_count"] for r in valid),
       "all_setup_events":sum(r["continuous"]["setups"] for r in valid),
       "invalidated_watch_events":sum(r["continuous"]["invalidations"] for r in valid),
       "watch_symbol_dates":len(watch_cases),
       "watch_without_future_gross_2x":no2x,
       "peak_watch_events_in_utc_hour":max(watch_hours.values(),default=0),
       "watch_utc_hour_histogram":dict(watch_hours),
       "per_date":[{"date":d,
            "attempted":len(joined[d]),
            "complete":sum(r["status"]=="COMPLETE_168H_CONTINUOUS_V4" for r in joined[d]),
            "watch_events":alerts_by_day[d],
            "gross2x_both_sources":sum(r["status"]=="COMPLETE_168H_CONTINUOUS_V4" and r["labels"]["2x"]["gross_hourly_high_gt"] for r in joined[d]),
            "early_gt2x":sum(r["status"]=="COMPLETE_168H_CONTINUOUS_V4" and r["labels"]["2x"]["classification"]=="WATCH_BEFORE_OR_AT_REAL_FIRST_1M_CROSS" for r in joined[d])
             } for d in dates],
       "future_price_event_labels":gt,
       "original_v4_watch_24h_20bps_fee_cost":cost20,
       "original_v4_watch_24h_100bps_fee_cost":cost100,
       "single_30USDT_portfolio_20bps":one_or_ten_slot(rows,1,"proxy_20bps"),
       "ten_30USDT_slots_300USDT_portfolio_20bps":one_or_ten_slot(rows,10,"proxy_20bps"),
       "single_30USDT_portfolio_100bps":one_or_ten_slot(rows,1,"proxy_100bps"),
       "ten_30USDT_slots_300USDT_portfolio_100bps":one_or_ten_slot(rows,10,"proxy_100bps"),
       "true_single_shared_global_V4_queue":"UNVERIFIED_PER_SYMBOL_SQLITE_ONLY",
       "actual_historical_orderbook":"UNVERIFIED",
       "independent_other_ai_review":"NOT_DONE",
       "mac_deployment":"NO_GO","trading":"NO_GO","real_gmail":"OFF"}

def run(files,proof=PROOF,manifest=FROZEN):
    record=json.loads(Path(proof).read_text(encoding="utf-8"))
    freeze=json.loads(Path(manifest).read_text(encoding="utf-8"))
    arts={(r["date"],r["shard"]):r for r in record["artifacts"]}
    if len(files)!=36 or len(arts)!=36 or set(d for d,_ in arts)!=set(freeze["frozen_dates_utc"]):
        raise ValueError("STAGE26_MISSING_OR_DUPLICATE_ARTIFACTS")
    reports={}
    for path in files:
        with zipfile.ZipFile(path) as z:
            members=z.namelist()
        if len(members)!=1:raise ValueError("STAGE26_MULTI_MEMBER_ZIP")
        name=members[0]
        if not name.startswith("monster_stage26_") or not name.endswith(".json"):
            raise ValueError("STAGE26_WRONG_MEMBER")
        suffix=name[len("monster_stage26_"):-len(".json")]
        day,number=suffix.split("_shard")
        key=(day,int(number))
        if key not in arts or key in reports:
            raise ValueError("STAGE26_UNREGISTERED_DUPLICATE_DATE_OR_SHARD")
        reports[key]=load_zip(path,arts[key])
    return summarize(reports,freeze)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifact-zips",nargs=36,required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    out=run(a.artifact_zips)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE26_RECOMPUTED "+json.dumps({k:v for k,v in out.items() if k not in (
          "watch_utc_hour_histogram","future_price_event_labels",
          "single_30USDT_portfolio_20bps","ten_30USDT_slots_300USDT_portfolio_20bps",
          "single_30USDT_portfolio_100bps","ten_30USDT_slots_300USDT_portfolio_100bps")} |
        {"future_price_event_labels":{
          k:{name:val for name,val in r.items() if name!="positive_event_register"}
          for k,r in out["future_price_event_labels"].items()},
         "single_30USDT_portfolio_20bps":{k:v for k,v in out["single_30USDT_portfolio_20bps"].items() if k!="selected_cases"},
         "ten_30USDT_slots_300USDT_portfolio_20bps":{k:v for k,v in out["ten_30USDT_slots_300USDT_portfolio_20bps"].items() if k!="selected_cases"}
        },sort_keys=True),flush=True)
if __name__=="__main__":
    main()
