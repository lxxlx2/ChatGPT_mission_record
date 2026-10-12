#!/usr/bin/env python3
"""Source-attested merge of 18 original Binance 1m first-WATCH feature jobs.
Descriptive feature comparison only. Never treat observed label associations as
prospective predictive power, executable profits or deployable thresholds.
"""
import argparse,collections,csv,hashlib,json,re,statistics,zipfile
from pathlib import Path

DAYS=("2025-01-19","2025-03-19","2025-04-19","2025-06-19",
      "2025-07-19","2025-09-19","2025-10-19","2025-11-04","2025-12-04",
      "2025-12-19","2026-01-19","2026-02-04","2026-03-19","2026-04-04",
      "2026-04-19","2026-07-19","2026-08-04","2026-09-04")
FIELDS=("return_3m_pct","return_15m_pct","return_60m_pct",
        "quote_1m_usdt","quote_3m_usdt","quote_15m_usdt","quote_60m_usdt",
        "quote_15m_vs_prior45m_normalized","last1m_share_of_60m_quote",
        "trades_1m","trades_15m","trades_60m",
        "positive_trade_minutes_60m","last_minute_upper_wick_fraction",
        "close_vs_last60m_high_pct")
SCHEMA="MONSTER_STAGE35_ORIGINAL18_GH_ARTIFACT_SHA_1587_SOURCE_FEATURES_V1"

def byte_sha(data):return hashlib.sha256(data).hexdigest()

def rows_from_shards(manifest,folder):
    if manifest.get("source_run_id")!=38205179145 or len(manifest["original_artifacts"])!=18:
        raise ValueError("STAGE35_NOT_EXACT_FROZEN_SOURCE_RUN")
    cases=[];receipts=[]
    for item in manifest["original_artifacts"]:
        d=item["date"]
        if d not in DAYS or any(x["date"]==d for x in receipts):
            raise ValueError("STAGE35_UNKNOWN_OR_DUPLICATE_DAY")
        aid=int(item["artifact_id"])
        data=(Path(folder)/(str(aid)+".zip")).read_bytes()
        if byte_sha(data)!=item["original_zip_sha256"]:
            raise ValueError("STAGE35_GITHUB_ARTIFACT_ZIP_SHA_CHANGED")
        filename=f"monster_stage35_{d}_original_SHA_causal_features.json"
        with zipfile.ZipFile(Path(folder)/(str(aid)+".zip")) as z:
            if z.namelist()!=[filename]:raise ValueError("STAGE35_WRONG_ORIGINAL_ZIP_MEMBER")
            raw=z.read(filename)
        decoded=json.loads(raw)
        if decoded.get("schema")!="MONSTER_STAGE35_CAUSAL_FIRST_WATCH_EXPOSED18_DATE_FEATURE_V1" or decoded.get("date")!=d:
            raise ValueError("STAGE35_BAD_SOURCE_PAYLOAD")
        if decoded["source_errors"] or len(decoded["rows"])!=decoded["complete_features"] or decoded["expected_controls"]!=20:
            raise ValueError("STAGE35_SOURCE_INCOMPLETE")
        for row in decoded["rows"]:
            if row["date"]!=d or not row["only_closed_bars"]:
                raise ValueError("STAGE35_SOURCE_CLOCK_INTEGRITY")
            if not row["publisher_sha256"] or not all(len(x["sha256"])==64 for x in row["publisher_sha256"]):
                raise ValueError("STAGE35_OFFICIAL_SHA_MISSING")
        cases+=decoded["rows"]
        receipts.append({"date":d,"artifact_id":aid,"original_zip_sha256":byte_sha(data),
                         "raw_JSON_sha256":byte_sha(raw),"original_WATCH":decoded["expected_watch"],
                         "control":decoded["expected_controls"]})
    if sorted(x["date"] for x in receipts)!=list(DAYS):raise ValueError("STAGE35_MISSING_DAY")
    return sorted(cases,key=lambda r:(r["date"],r["symbol"])),sorted(receipts,key=lambda r:r["date"])

def quartile(values):
    if not values:return {"n":0,"missing":None,"median":None}
    s=sorted(values)
    def q(p):
        pos=(len(s)-1)*p
        low=int(pos);high=min(low+1,len(s)-1)
        return round(float(s[low]*(1-(pos-low))+s[high]*(pos-low)),6)
    return {"n":len(s),"median":q(.5),"p25":q(.25),"p75":q(.75),"min":q(0),"max":q(1)}

def analyze(rows,receipts):
    if len(rows)!=1587 or len({(r["date"],r["symbol"]) for r in rows})!=1587:
        raise ValueError("STAGE35_INCOMPLETE_FROZEN_1587_CASES")
    watch=[r for r in rows if r["cohort"]=="FIRST_WATCH"]
    ctrl=[r for r in rows if r["cohort"]=="SAME_DATE_OTHER_WATCH_CLOCK_CONTROL"]
    if len(watch)!=1227 or len(ctrl)!=360:
        raise ValueError("STAGE35_WATCH_OR_ORDINARY_CONTROL_COUNT_DRIFT")
    found=[r for r in watch if r["first_2x_watch_class"]=="EARLY_STRICT"]
    late=[r for r in watch if r["first_2x_watch_class"]=="LATE"]
    negatives=[r for r in watch if r["label_future_calendar_2x"]==0]
    if (len(found),len(late),len(negatives))!=(84,2,1141):
        raise ValueError("STAGE35_ORIGINAL_SUCCESS_LABELS_CHANGED")
    clock=collections.defaultdict(list)
    for r in watch:clock[r["asof_utc"]].append(r)
    bursts=[]
    for at,members in clock.items():
        if len(members)>=8:
            bursts.append({"asof_utc":at,"watch_count":len(members),
                           "retrospective_2x_coin_dates":sum(x["label_future_calendar_2x"] for x in members),
                           "retrospective_5x_coin_dates":sum(x["label_future_calendar_5x"] for x in members)})
    bursts.sort(key=lambda x:(-x["watch_count"],x["asof_utc"]))
    byday=[]
    for d in DAYS:
        w=[r for r in watch if r["date"]==d]
        c=[r for r in ctrl if r["date"]==d]
        byday.append({"date":d,"watch_count":len(w),"controls":len(c),
                      "early_2x":sum(r["first_2x_watch_class"]=="EARLY_STRICT" for r in w),
                      "watch_non_2x":sum(r["label_future_calendar_2x"]==0 for r in w)})
        if len(c)!=20:raise ValueError("STAGE35_CONTROL_DATE_INCOMPLETE")
    groups={"EARLY_STRICT_2X_WATCH":found,"LATE_2X_WATCH":late,
            "WATCH_WITHOUT_CALENDAR_2X":negatives,"NO_WATCH_MATCHED_DATE_CLOCK_CONTROL":ctrl}
    distribution={}
    for group,members in groups.items():
        distribution[group]={"count":len(members),"metrics":{}}
        for feature in FIELDS:
            v=[float(r[feature]) for r in members if r[feature] is not None]
            distribution[group]["metrics"][feature]={
                 **quartile(v),"missing":len(members)-len(v)}
    return {
      "schema":SCHEMA,"source":"18 GitHub publisher-SHA verified daily-1m jobs, original V4 research watch times",
      "historical_exposed_no_model_fitted":True,"full_original_stage34_complete_coin_dates":7776,
      "calendar_windows":18,"watch_cases":1227,"ordinary_controls":360,
      "first_watch_strictly_pre_2x":len(found),"first_watch_late_2x":len(late),
      "first_watch_non_2x":len(negatives),
      "no_watch_controls_later_2x":sum(r["label_future_calendar_2x"] for r in ctrl),
      "all_2x_positive_registry":88,
      "source_zip_json_receipts":receipts,
      "date_cohorts":byday,"first_watch_same_three_minute_poll_bursts_gte_8":bursts,
      "descriptive_unadjusted_feature_distributions":distribution,
      "limitations":["Stage34 frozen 2x is seven-day calendar-high outcome, not a fill or model-trained class",
                     "Already exposed historical data, so feature separations are exploratory only",
                     "All WATCH cases versus 20 hashed nonWATCH controls per date are not equal sample fractions",
                     "No point-in-time official exchangeInfo, historical orderbook, Futures, DEX or true fills",
                     "Original V4 per-symbol replay, global queue and real delivery unverified"],
      "independent_other_AI_review":"NOT_DONE","model_deployment":"NO_GO",
      "gmail":"OFF","auto_trading":"NO_GO","Frank":"UNCHANGED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--zips-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    cases,receipts=rows_from_shards(json.loads(a.manifest.read_text()),a.zips_dir)
    report=analyze(cases,receipts)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    j=a.output_dir/"monster_stage35_18date_SHA_verified_first_watch_feature_summary.json"
    j.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    # Machine-auditable complete rows incl negative controls and sources.
    rows=a.output_dir/"monster_stage35_1587_first_watch_and_control_features.jsonl"
    with rows.open("w",encoding="utf-8") as f:
        for r in cases:f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n")
    print("STAGE35_18_REAL_PUBLISHER_SHA_MERGE_PASS "+json.dumps({
        "all":len(cases),"positive":report["first_watch_strictly_pre_2x"],
        "negative":report["first_watch_non_2x"],"ordinary_controls":report["ordinary_controls"],
        "burst_gte8":len(report["first_watch_same_three_minute_poll_bursts_gte_8"])}))
if __name__=="__main__":main()
