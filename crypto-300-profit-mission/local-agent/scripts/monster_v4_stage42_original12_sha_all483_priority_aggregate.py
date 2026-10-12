#!/usr/bin/env python3
"""Stage42 frozen P1 post-Stage39 483-first-watch source-complete exposed pilot.

Precommitted rule, no threshold searching. Original ZIP SHA and publisher source
proofs checked. Attach FUTURE historical GT only in THIS aggregate AFTER the
P1 candidate was actually computed from contemporaneous closed 1m source.
No false independent-OOS, fill, trade or deploy claims.
"""
import argparse,collections,csv,hashlib,json,statistics,zipfile
from datetime import datetime,timedelta,timezone
from pathlib import Path

EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
DAYS=("2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19")
EXPECTED=(36,100,75,80,113,79)
SCHEMA="MONSTER_STAGE42_ORIGINAL12_SHA_ALL483_EXPOSED_PRIORITY_RESEARCH_AGGREGATE_V1"
INNER="MONSTER_STAGE42_EXPOSED483_P1_RESEARCH_ONLY_ORIGINAL_V4_FIRST_WATCH_REAL_SHA_V1"

def sha(data):return hashlib.sha256(data).hexdigest()
def parsed(t):return datetime.fromisoformat(t.replace("Z","+00:00"))

def read(manifest,folder):
    if manifest.get("run_id")!=38211198743 or len(manifest.get("artifacts",[]))!=12:
        raise ValueError("STAGE42_WRONG_ORIGINAL12_CI_SOURCE")
    out=[];receipts=[]
    for x in manifest["artifacts"]:
        d=x["date"];shard=int(x["shard"]);aid=int(x["artifact_id"])
        if d not in DAYS or shard not in (0,1) or any(p["date"]==d and p["shard"]==shard for p in receipts):
            raise ValueError("STAGE42_MISSING_OR_DUP_SOURCE_SHARD")
        data=(Path(folder)/(str(aid)+".zip")).read_bytes()
        if sha(data)!=x["zip_sha256"]:raise ValueError("STAGE42_SOURCE_ORIGINAL_ARTIFACT_SHA_FAIL")
        name=f"monster_stage42_{d}_shard{shard}.json"
        with zipfile.ZipFile(Path(folder)/(str(aid)+".zip")) as z:
            if z.namelist()!=[name]:raise ValueError("STAGE42_UNEXPECTED_ZIP_MEMBER")
            raw=z.read(name)
        item=json.loads(raw)
        if item["schema"]!=INNER or item["date"]!=d or item["shard"]!=shard or item["source_errors"]:
            raise ValueError("STAGE42_ORIGINAL_SOURCE_CONTRACT_FAIL")
        if len(item["rows"])!=item["selected_cases"] or any(r["date"]!=d for r in item["rows"]):
            raise ValueError("STAGE42_SOURCE_DROPPED_ONE_FIRST_WATCH")
        for r in item["rows"]:
            p=r["research_p1"]
            if r["source_status"]!="VERIFIED_CAUSAL_P1_ASOF":
                raise ValueError("STAGE42_EXPOSED_PILOT_SOURCE_MISSING")
            if len(r["source_dated_1m_publisher_SHA"]) not in (1,2):
                raise ValueError("STAGE42_SOURCE_DAILY_ARCHIVE_PROOFS_MISSING")
            if not all(x.get("verified_official_publisher_SHA256") and len(x["zip_sha256"])==64
                       for x in r["source_dated_1m_publisher_SHA"]):
                raise ValueError("STAGE42_OFFICIAL_PUBLISHER_SHA_NOT_PRESENT")
            if p["D0_WATCH_UTC"]!=r["stage39_first_v4_WATCH_UTC"]:
                raise ValueError("STAGE42_HISTORICAL_D0_TIME_CHANGED")
            if p["status"] not in ("P1_RESEARCH_ELIGIBLE","P1_NOT_ESCALATED","P1_OUTSIDE_FROZEN_ACTIVE_WINDOW"):
                raise ValueError("STAGE42_UNEXPECTED_PRIORITY_MODEL_STATE")
            if p["status"]=="P1_RESEARCH_ELIGIBLE":
                if (parsed(p["decision_asof_UTC"])-parsed(p["D0_WATCH_UTC"])).total_seconds()!=360:
                    raise ValueError("STAGE42_PRIORITY_CLOCK_NOT_6MIN_CAUSAL")
                if p["P1_escalation_UTC"]!=p["decision_asof_UTC"] or p.get("no_buy") is not True:
                    raise ValueError("STAGE42_PRIORITY_BUY_OR_TIME_VIOLATION")
            if p["status"]=="P1_NOT_ESCALATED" and p.get("P1_escalation_UTC") is not None:
                raise ValueError("STAGE42_FALSE_ESCALATION")
        out+=item["rows"]
        receipts.append({"date":d,"shard":shard,"artifact_id":aid,
            "original_zip_sha256":sha(data),"original_json_sha256":sha(raw),
            "first_watch_cases":len(item["rows"])})
    if {(r["date"],r["shard"]) for r in receipts}!={(d,s) for d in DAYS for s in (0,1)}:
        raise ValueError("STAGE42_NOT_ALL12_ORIGINAL_SOURCES")
    return sorted(out,key=lambda r:(r["date"],r["symbol"])),sorted(receipts,key=lambda r:(r["date"],r["shard"]))

def summarize(rows,receipts):
    if len(rows)!=483 or len({(r["date"],r["symbol"]) for r in rows})!=483:
        raise ValueError("STAGE42_NOT_FULL483_SOURCE")
    for d,n in zip(DAYS,EXPECTED):
        if sum(r["date"]==d for r in rows)!=n:raise ValueError("STAGE42_SIX_DATE_COUNT_NOT_FROZEN")
    eligible=[r for r in rows if r["research_p1"]["status"]=="P1_RESEARCH_ELIGIBLE"]
    noteligible=[r for r in rows if r not in eligible]
    winners=[r for r in rows if r["prior_stage39_GT2x"]]
    baseline=[r for r in winners if r["original_stage39_EARLY_2x"]]
    notwin=[r for r in rows if not r["prior_stage39_GT2x"]]
    if (len(winners),len(baseline),len(notwin))!=(50,48,433):
        raise ValueError("STAGE42_GT_AND_CONTROL_DENOMINATOR_DRIFT")
    trueearly=[]
    future_same=[]
    for r in eligible:
        when=r["research_p1"]["P1_escalation_UTC"]
        crossed=r["prior_stage39_first_2x_high_1m_UTC"]
        if not crossed:continue
        lead=(parsed(crossed)-parsed(when)).total_seconds()/60
        if lead>0:trueearly.append((r,lead))
        else:future_same.append((r,lead))
    p1_5m=[r for r,lead in trueearly if lead>=5]
    baselines_ge5=[r for r in baseline if
        (parsed(r["prior_stage39_first_2x_high_1m_UTC"])-parsed(r["stage39_first_v4_WATCH_UTC"])).total_seconds()/60>=5]
    # This uses FIRST D0 timing as precommitted priority entry, not nearest later WATCH.
    def daily_count(d):
        start=parsed(d+"T06:00:00Z")
        counts=[]
        for k in range(7):
            lower=start+timedelta(days=k);upper=lower+timedelta(days=1)
            counts.append(sum(lower<=parsed(r["research_p1"]["P1_escalation_UTC"])<upper
                for r in eligible if r["research_p1"]["P1_escalation_UTC"]))
        return counts
    date_rows=[]
    for d in DAYS:
        cohort=[r for r in rows if r["date"]==d]
        pe=[r for r in eligible if r["date"]==d]
        counts=daily_count(d)
        date_rows.append({"date":d,"original_v4_FIRST_WATCH_coin_dates":len(cohort),
            "future2x_with_D0":sum(r["prior_stage39_GT2x"] for r in cohort),
            "P1_eligible":len(pe),
            "P1_future2x_coin_dates":sum(r["prior_stage39_GT2x"] for r in pe),
            "P1_not_calendar2x":sum(not r["prior_stage39_GT2x"] for r in pe),
            "P1_upgrades_per_each_utc_anchor_day":counts})
    all_counts=sum((r["P1_upgrades_per_each_utc_anchor_day"] for r in date_rows),[])
    if len(all_counts)!=42 or sum(all_counts)!=len(eligible):
        raise ValueError("STAGE42_ALERT_DAY_COUNT_MISMATCH")
    return {
      "schema":SCHEMA,"exposed_historical_only_not_out_of_sample":True,
      "frozen_original_v4_full6date_source_watch_cohort":483,
      "frozen_original_future2x_in_WATCH_cohort":50,
      "frozen_original_v4_first_watch_strict_early_future2x":48,
      "frozen_original_WATCH_without_calendar2x":433,
      "P1_eligible":len(eligible),"P1_not_eligible":len(noteligible),
      "P1_eligible_historical_future2x":sum(r["prior_stage39_GT2x"] for r in eligible),
      "P1_eligible_historical_not2x":sum(not r["prior_stage39_GT2x"] for r in eligible),
      "P1_strictly_pre_1m_cross_gt2x":len(trueearly),
      "P1_strictly_pre_1m_cross_at_least_5min":len(p1_5m),
      "P1_late_or_equal_to_cross":len(future_same),
      "P1_retains_baseline_first_D0_lead_ge5min_cases":sum(r in baselines_ge5 for r in p1_5m),
      "D0_first_watch_ge5min_future2x_base_denominator":len(baselines_ge5),
      "P1_eligible_future5x":sum(r["prior_stage39_GT5x"] for r in eligible),
      "P1_eligible_future10x":sum(r["prior_stage39_GT10x"] for r in eligible),
      "P1_alerts_per_42_utc_days":all_counts,
      "P1_mean_per_day":round(len(eligible)/42,6),
      "P1_max_per_day":max(all_counts),
      "P1_mean_le5_per_day_gate":len(eligible)/42<=5,
      "P1_daily_max_le12_gate":max(all_counts)<=12,
      "P1_at_least_80pct_of_baseline_first_D0_gt2x_ge5min_gate":
         ((sum(r in baselines_ge5 for r in p1_5m)/len(baselines_ge5))>=.80) if baselines_ge5 else None,
      "per_date":date_rows,"original12_source_artifact_SHA_receipts":receipts,
      "old_dataset_thresholds_unchanged":True,
      "future_executable_net_return":"UNVERIFIED_NO_HISTORICAL_L2",
      "otherAIreview":"NOT_DONE","deploy":"NO_GO","Gmail":"OFF","Frank":"UNCHANGED","trading":"NO_GO"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--zips",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    rows,receipts=read(json.loads(a.manifest.read_text()),a.zips)
    stats=summarize(rows,receipts)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage42_original12_SHA_first483_P1_metrics.json").write_text(json.dumps(stats,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    with (a.out/"monster_stage42_all483_firstWATCH_priority_source_cases.jsonl").open("w") as f:
        for r in rows:f.write(json.dumps(r,sort_keys=True,ensure_ascii=False)+"\n")
    print("STAGE42_ORIGINAL12_GITHUB_ZIP_SHA_483_EXPOSED_P1_RECOMPUTED "+json.dumps({
      k:stats[k] for k in ("P1_eligible","P1_eligible_historical_future2x","P1_strictly_pre_1m_cross_gt2x",
          "P1_strictly_pre_1m_cross_at_least_5min","P1_mean_per_day","P1_max_per_day",
          "P1_mean_le5_per_day_gate","P1_at_least_80pct_of_baseline_first_D0_gt2x_ge5min_gate")},sort_keys=True))
if __name__=="__main__":main()
