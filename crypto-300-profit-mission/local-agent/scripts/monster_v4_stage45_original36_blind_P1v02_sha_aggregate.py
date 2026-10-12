#!/usr/bin/env python3
"""Stage45 original 36 SHA verify actual six presealed date all900 V4 / P1v02.

Compare pre-frozen strategy gates vs ALL source-complete normal/2x/5x/10x pairs.
P1 results from production first WATCH and contemporary minute only.
No outcome selection, no retroactive threshold tuning, no buy fills, no deploy.
"""
import argparse,collections,csv,hashlib,json,statistics,zipfile
from datetime import datetime,timedelta,timezone
from pathlib import Path

SCHEMA="MONSTER_STAGE45_ORIGINAL36_SHA_FROZEN_SIX_DAY_P1V02_FUTURES_TRUTH_V1"
SRC="MONSTER_STAGE45_6_BLIND_DATES_ORIGINAL_V4_AND_FROZEN_IMMEDIATE_P1V02_FULL_MARKET_V1"
RUN=38213103621
DATES=("2025-01-09","2025-09-02","2026-01-26","2026-02-24","2026-03-28","2026-05-10")
VALID="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
UP="P1_V02_UPGRADE_IMMEDIATE_FIRST_WATCH"

def sha(data):return hashlib.sha256(data).hexdigest()
def parse(t):return datetime.fromisoformat(t.replace("Z","+00:00"))
def read_all(manifest,folder):
    if manifest.get("source_run_id")!=RUN or len(manifest.get("artifacts",[]))!=36:
        raise ValueError("STAGE45_SOURCE_RUN_PIN_OR_36_ARTIFACTS_MISSING")
    allrows=[];receipts=[];seen=set()
    for a in manifest["artifacts"]:
        day=a["date"];shard=int(a["shard"]);aid=int(a["artifact_id"])
        if day not in DATES or shard not in range(6) or (day,shard) in seen:
            raise ValueError("STAGE45_ORIGINAL_SOURCE_IDENTITY_BAD")
        seen.add((day,shard))
        p=Path(folder)/(str(aid)+".zip")
        raw_zip=p.read_bytes()
        if sha(raw_zip)!=a["zip_sha256"]:raise ValueError("STAGE45_ORIGINAL_GITHUB_ARTIFACT_SHA_MISMATCH")
        inner=f"monster_stage45_{day}_shard{shard}.json"
        with zipfile.ZipFile(p) as z:
            if z.namelist()!=[inner]:raise ValueError("STAGE45_WRONG_INSIDE_FILENAME")
            raw=z.read(inner)
        obj=json.loads(raw)
        if obj.get("schema")!=SRC or obj["date"]!=day or obj["shard"]!=shard or not obj["all900_original_frozen"] or len(obj["rows"])!=150:
            raise ValueError("STAGE45_ORIGINAL_SOURCE_NOT_COMPLETE")
        for r in obj["rows"]:
            if r["date"]!=day or r["source_status"] not in (
               VALID,"CENSORED_STAGE44_HOURLY_SOURCE","CENSORED_DAILY_1M_404",
               "CENSORED_DAILY_1M_GAP","CENSORED_PUBLISHER_VERIFIED_1H_VS_1M_PRICE_CONFLICT"):
                raise ValueError("STAGE45_BAD_SOURCE_STATUS")
            if r["source_status"]==VALID:
                if r["polls"]!=3360 or len(r["verified_9_daily_publisher_sha256"])!=9 or not r["unchanged_V4_original_futures"]:
                    raise ValueError("STAGE45_PUBLISHER_SOURCE_OR_V4_NOT_PROVEN")
                if not r["verified_original_hourly_publisher_SHA256"] or not all(
                  len(p["publisher_ZIP_sha256"])==64 for p in r["verified_original_hourly_publisher_SHA256"]):
                    raise ValueError("STAGE45_HOURLY_PUBLISHER_SHA_NOT_REAL")
                if any(len(p["zip_sha256"])!=64 or not p["verified_official_publisher_SHA256"]
                       for p in r["verified_9_daily_publisher_sha256"]):
                    raise ValueError("STAGE45_PUBLISHER_DAILY_SHA_NOT_PROVEN")
                watches=r["WATCH_UTC"]
                if r["p1_status"]==UP:
                    if not watches or not r["p1_asof_no_future_bars"] or r["p1_decision_UTC"]!=watches[0]:
                        raise ValueError("STAGE45_P1_TIME_TRAVEL_OR_NOT_FROM_FIRST_D0")
                    quote=float(r["p1_quote15_usdt"]);pct=float(r["p1_ret60_pct"])
                    relative=float(r["p1_q15_normalized_ratio"]) if r["p1_q15_normalized_ratio"] is not None else None
                    if not (pct>=8 or (quote>=1_000_000 and relative is not None and relative>=1.5)):
                        raise ValueError("STAGE45_P1_CANNOT_RECOMPUTE_SEALED_THRESHOLDS")
                elif r["p1_status"] not in ("P1_V02_NOT_UPGRADED_D0_PRESERVED","P1_SOURCE_UNSCORABLE","NO_D0_WATCH"):
                    raise ValueError("STAGE45_UNKNOWN_FROZEN_P1_STATE")
                if not watches and r["p1_status"]!="NO_D0_WATCH":
                    raise ValueError("STAGE45_WATCH_SUPPRESSED_IN_P1")
                if r["p1_status"]=="NO_D0_WATCH" and watches:
                    raise ValueError("STAGE45_MISSING_P1_FOR_REAL_D0")
        allrows+=obj["rows"]
        receipts.append({"date":day,"shard":shard,"artifact_id":aid,
                         "original_GitHub_zip_SHA256":sha(raw_zip),"original_JSON_SHA256":sha(raw),
                         "source_complete":obj["valid_source_with_V4"]})
    if seen!={(d,s) for d in DATES for s in range(6)}:
        raise ValueError("STAGE45_NOT_SIX_DATE_36_SHARDS")
    return sorted(allrows,key=lambda r:(r["date"],r["symbol"])),sorted(receipts,key=lambda r:(r["date"],r["shard"]))

def analyze(rows,receipts):
    if len(rows)!=5400 or len({(r["date"],r["symbol"]) for r in rows})!=5400:
        raise ValueError("STAGE45_NOT_ALL_FROZEN_5400_PAIRS")
    for d in DATES:
        if sum(r["date"]==d for r in rows)!=900:raise ValueError("STAGE45_MISSING_A_SEALED_WINDOW")
    valid=[r for r in rows if r["source_status"]==VALID]
    positive=[r for r in valid if r["original_GT2x_1h"]=="True"]
    negative=[r for r in valid if r["original_GT2x_1h"]=="False"]
    high5=[r for r in valid if r["original_GT5x_1h"]=="True"]
    high10=[r for r in valid if r["original_GT10x_1h"]=="True"]
    pre=[r for r in positive if r["classification"]=="STRICTLY_EARLY_WATCH"]
    early5=[r for r in pre if r["nearest_strictly_earlier_WATCH_lead_min"]>=5]
    upgraded=[r for r in valid if r["p1_status"]==UP]
    kept=[r for r in early5 if r["p1_status"]==UP and r["P1_before_1m_high_2x"] and r["P1_lead_gt2x_minutes"]>=5]
    slots=[]
    for d in DATES:
        start=parse(d+"T06:00:00Z")
        for k in range(7):
            slots.append({"window":d,"offset":k,"start":start+timedelta(days=k),"count":0})
    for r in upgraded:
        when=parse(r["p1_decision_UTC"])
        eligible=[s for s in slots if s["start"]<=when<s["start"]+timedelta(days=1)]
        if len(eligible)!=1:raise ValueError("STAGE45_P1_OUTSIDE_FROZEN_WINDOW")
        eligible[0]["count"]+=1
    daily=[{"date_window":s["window"],"block":s["offset"],"count":s["count"]} for s in slots]
    alerts=len(upgraded)
    baseline_5m_rate=len(early5)/len(positive)*100 if positive else None
    early_rate=len(pre)/len(positive)*100 if positive else None
    retained=len(kept)/len(early5)*100 if early5 else None
    avg=alerts/42
    peak=max(s["count"] for s in slots)
    enough=len(positive)>=20
    gates={
        "sufficient_2x_events_at_least20":enough,
        "D0_strict_early_2x_ge90pct":early_rate is not None and early_rate>=90,
        "D0_early_gt2x_lead_ge5min_ge85pct":baseline_5m_rate is not None and baseline_5m_rate>=85,
        "P1_retained_D0_early_ge5min_gt2x_ge80pct":retained is not None and retained>=80,
        "P1_mean_per_24h_block_le5":avg<=5,
        "P1_peak_per_24h_block_le12":peak<=12}
    verdict=("INSUFFICIENT_EVENTS" if not enough else
             "REJECTED_FAIL_GATE" if not all(gates.values()) else
             "HISTORICAL_DISCOVERY_GATES_PASS_NOT_EXECUTION_NOT_OOS_PROSPECTIVE")
    date_rows=[]
    for d in DATES:
        subset=[r for r in valid if r["date"]==d]
        ps=[r for r in subset if r["original_GT2x_1h"]=="True"]
        date_rows.append({"date":d,"source_valid":len(subset),"gt2x":len(ps),
         "gt5x":sum(r["original_GT5x_1h"]=="True" for r in subset),
         "gt10x":sum(r["original_GT10x_1h"]=="True" for r in subset),
         "D0_strict_early2x":sum(r["classification"]=="STRICTLY_EARLY_WATCH" for r in ps),
         "P1_upgrades":sum(r["p1_status"]==UP for r in subset),
         "non2x_P1_upgrades":sum(r["p1_status"]==UP and r["original_GT2x_1h"]=="False" for r in subset),
         "D0_WATCH_events":sum(r["watch_count"] for r in subset)})
    return {
     "schema":SCHEMA,"source_stage45_run_id":RUN,"original36_verified_GitHub_SHA_receipts":receipts,
     "attempted":5400,"source_complete":len(valid),"source_censored":5400-len(valid),
     "status_counts":dict(collections.Counter(r["source_status"] for r in rows)),
     "GT2x_source_complete":len(positive),"GT5x_source_complete":len(high5),"GT10x_source_complete":len(high10),
     "D0_strict_early2x":len(pre),"D0_pre_gt2x_ge5min":len(early5),
     "D0_no_watch_2x":sum(r["classification"]=="NO_WATCH" for r in positive),
     "D0_same_minute_2x":sum(r["classification"]=="SAME_MINUTE_NOT_EARLY" for r in positive),
     "D0_late_watch_2x":sum(r["classification"]=="WATCH_LATE" for r in positive),
     "D0_strict_early5x":sum(r["watch_vs_gt5x_class"]=="STRICTLY_EARLY_WATCH" for r in high5),
     "D0_strict_early10x":sum(r["watch_vs_gt10x_class"]=="STRICTLY_EARLY_WATCH" for r in high10),
     "D0_WATCH_distinct_coin_dates":sum(bool(r["watch_count"]) for r in valid),
     "D0_WATCH_event_total":sum(r["watch_count"] for r in valid),
     "normal_gt2x_FALSE":len(negative),"normal_with_D0_WATCH":sum(r["watch_count"]>0 for r in negative),
     "P1_upgraded_distinct_coin_dates":alerts,
     "P1_upgraded_and_non2x":sum(r["original_GT2x_1h"]=="False" for r in upgraded),
     "P1_retained_early_gt2x_ge5min":len(kept),
     "P1_upgraded_and_2x_GT":sum(r["original_GT2x_1h"]=="True" for r in upgraded),
     "P1_upgraded_and_5x_GT":sum(r["original_GT5x_1h"]=="True" for r in upgraded),
     "P1_upgraded_and_10x_GT":sum(r["original_GT10x_1h"]=="True" for r in upgraded),
     "P1_strict_early5x":sum(r["original_GT5x_1h"]=="True" and r.get("P1_before_1m_high_5x",False) for r in upgraded),
     "P1_strict_early10x":sum(r["original_GT10x_1h"]=="True" and r.get("P1_before_1m_high_10x",False) for r in upgraded),
     "frozen_P1_v02_gates":gates,"verdict":verdict,
     "P1_mean_alerts_per_42_anchored_24h_blocks":round(avg,6),
     "P1_max_alerts_one_anchored_24h_block":peak,
     "P1_42_anchored_24h_alert_blocks":daily,"per_date":date_rows,
     "analysis_uses_future_prices_only_in_scoring":True,
     "source_cohort_overlap_date_audit_not_absolute_novelty":True,
     "historical_market_execution_profit":"UNVERIFIED",
     "independent_other_AI_review":"NOT_DONE","Mac_deployment":"NO_GO",
     "Frank":"UNCHANGED","Gmail":"OFF","automated_trading":"NO_GO"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--zip-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    rows,receipts=read_all(json.loads(a.manifest.read_text()),a.zip_dir)
    report=analyze(rows,receipts)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage45_blind_900x6_SHA_P1v02_metrics_and_gates.json").write_text(
        json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    with (a.out/"monster_stage45_blind_all5400_originalV4_P1v02_cases.jsonl").open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,sort_keys=True,ensure_ascii=False)+"\n")
    print("STAGE45_ORIGINAL36_BINANCE_SHA_BLIND_900x6_GATES "+json.dumps({
        k:report[k] for k in ("source_complete","GT2x_source_complete","GT5x_source_complete",
          "GT10x_source_complete","D0_strict_early2x","P1_upgraded_distinct_coin_dates",
          "P1_retained_early_gt2x_ge5min","verdict")},sort_keys=True))
if __name__=="__main__":main()
