#!/usr/bin/env python3
"""Monster Stage34, full 18 historical windows, immutable original 108 ZIPs.

DATA ANALYSIS ONLY. No score tuning, BTC strategy, holding horizon, cash model,
historical orderbook assumption, live alerts, automatic trade or production change.
"""
import argparse
import collections
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import statistics
import zipfile

STAGES=(26,30,32)
FINAL_COUNTS={26:(2719,1132,40),30:(2514,760,33),32:(2543,499,15)}
COLS=("stage","date","symbol","source_status","joint_source_complete",
      "future_2x_high","future_5x_high","future_10x_high",
      "watch_count_3m","first_watch_utc_3m","first_2x_high_cross_utc",
      "first_watch_lead_minutes_2x","nearest_pre_cross_watch_lead_minutes_2x",
      "first_2x_watch_class","scope")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def parse(utc):
    return datetime.fromisoformat(utc.replace("Z","+00:00"))

def normalized_case(stage,r):
    complete=r["status"]==("COMPLETE_BOTH_168H" if stage==32 else "COMPLETE_168H_CONTINUOUS_V4")
    d={"stage":stage,"date":r["date"],"symbol":r["symbol"],
       "source_status":r["status"],"joint_source_complete":int(complete),
       "future_2x_high":"","future_5x_high":"","future_10x_high":"",
       "watch_count_3m":"","first_watch_utc_3m":"",
       "first_2x_high_cross_utc":"","first_watch_lead_minutes_2x":"",
       "nearest_pre_cross_watch_lead_minutes_2x":"",
       "first_2x_watch_class":"CENSORED_SOURCE",
       "scope":"PER_SYMBOL_ORIGINAL_PRODUCTION_V4_HISTORICAL"}
    if not complete:
        return d
    label=r["labels_original3m"] if stage==32 else r["labels"]
    arm=r["V4_original3m"] if stage==32 else r["continuous"]
    watch=arm["watch_utcs"]
    assert arm["watch_count"]==len(watch) and sorted(watch)==watch
    d["watch_count_3m"]=len(watch)
    d["first_watch_utc_3m"]=watch[0] if watch else ""
    for k,col in (("2x","future_2x_high"),("5x","future_5x_high"),("10x","future_10x_high")):
        d[col]=int(label[k]["is_gt_positive"] if stage==32 else label[k]["gross_hourly_high_gt"])
    gt2=bool(d["future_2x_high"])
    if not gt2:
        d["first_2x_watch_class"]="NON_2X_WITH_WATCH" if watch else "NON_2X_WITHOUT_WATCH"
        return d
    cross=label["2x"]["cross_1m_high_UTC"] if stage==32 else label["2x"]["real_1m_cross_utc"]
    if not cross:
        raise ValueError("COMPLETE_GT2_MISSING_TRUE_FIRST_CROSS")
    d["first_2x_high_cross_utc"]=cross
    prior=[w for w in watch if parse(w)<parse(cross)]
    same=[w for w in watch if parse(w)==parse(cross)]
    if prior:
        nearest=max(prior)
        d["first_2x_watch_class"]="EARLY_STRICT"
        d["nearest_pre_cross_watch_lead_minutes_2x"]=int((parse(cross)-parse(nearest)).total_seconds()/60)
    elif same:
        d["first_2x_watch_class"]="SAME_MINUTE_NOT_EARLY"
        d["nearest_pre_cross_watch_lead_minutes_2x"]=0
    elif watch:
        d["first_2x_watch_class"]="LATE"
    else:
        d["first_2x_watch_class"]="NO_WATCH"
    if watch:
        d["first_watch_lead_minutes_2x"]=int((parse(cross)-parse(watch[0])).total_seconds()/60)
    return d

def read_108(proofs,artifact_dir):
    rows=[]
    receipts=[]
    dates=set()
    for stage in STAGES:
        doc=json.loads(Path(proofs[stage]).read_text(encoding="utf-8"))
        artifacts=doc["artifacts"]
        if len(artifacts)!=36 or len({(a["date"],a["shard"]) for a in artifacts})!=36:
            raise ValueError("MISSING_OR_DUPLICATE_IMMUTABLE_ORIGINAL_SOURCE")
        perdate=collections.defaultdict(list)
        for a in artifacts:
            aid=int(a["artifact_id"])
            path=Path(artifact_dir)/f"{aid}.zip"
            data=path.read_bytes()
            if sha(data)!=a["zip_sha256"]:
                raise ValueError(f"ORIGINAL_ARTIFACT_ZIP_SHA_MISMATCH {stage} {aid}")
            with zipfile.ZipFile(path) as z:
                names=z.namelist()
                expected=f"monster_stage{stage}_{a['date']}_shard{a['shard']}.json"
                if names!=[expected]:
                    raise ValueError(f"ORIGINAL_ARTIFACT_UNEXPECTED_MEMBER {stage} {aid} {names}")
                raw=z.read(expected)
            if sha(raw)!=a["raw_json_sha256"]:
                raise ValueError(f"ORIGINAL_INNER_JSON_SHA_MISMATCH {stage} {aid}")
            j=json.loads(raw)
            if j["date"]!=a["date"] or j["shard"]!=a["shard"]:
                raise ValueError("WRONG_ORIGINAL_DATE_SHARD")
            cases=j["results"] if stage==32 else j["cases"]
            if len(cases) not in (126,127):
                raise ValueError("WRONG_SHARD_COIN_COUNT")
            if len({r["symbol"] for r in cases})!=len(cases):
                raise ValueError("DUPLICATE_SYMBOL_IN_SHARD")
            perdate[a["date"]].extend(cases)
            receipts.append({"stage":stage,"date":a["date"],"shard":a["shard"],"artifact_id":aid,"zip_sha256":sha(data),"inner_json_sha256":sha(raw)})
        if len(perdate)!=6:
            raise ValueError("RESEARCH_DATES_WRONG")
        for date,rs in perdate.items():
            if len(rs)!=758 or len({r["symbol"] for r in rs})!=758:
                raise ValueError("FULL_758_UNIVERSE_WRONG")
            if date in dates:
                raise ValueError("HISTORICAL_DATE_EXPOSED_TWICE")
            dates.add(date)
            rows.extend(normalized_case(stage,r) for r in rs)
    if len(rows)!=13644 or len(dates)!=18 or len(receipts)!=108:
        raise ValueError("FULL_MARKET_ORIGINAL108_INCOMPLETE")
    frozen_by_date=collections.defaultdict(set)
    for r in rows:
        frozen_by_date[r["date"]].add(r["symbol"])
    if len({tuple(sorted(s)) for s in frozen_by_date.values()})!=1:
        raise ValueError("NOT_SAME_FROZEN_758_SYMBOL_SET")
    return sorted(rows,key=lambda r:(r["date"],r["symbol"])),receipts

def summary(rows,receipts):
    desc={"schema":"MONSTER_STAGE34_FULL18_DATE_13644_ORIGINAL108_SHA_DISCOVERY_CENSUS_V1",
          "historical_exposed_data_only":True,"real_trade_PnL_and_historical_L2":"UNVERIFIED",
          "independent_other_AI_review":"NOT_DONE","deployment":"NO_GO","real_gmail":"OFF","automated_trading":"NO_GO",
          "attempted":len(rows),"source_verified_complete":0,
          "cohorts":{},"all_dates":[],"overall":{},"immutable_original_artifact_receipts":receipts}
    groups={"ALL":rows}
    for s in STAGES:
        groups[str(s)]=[r for r in rows if r["stage"]==s]
    for date in sorted({r["date"] for r in rows}):
        groups[date]=[r for r in rows if r["date"]==date]
    for key,subset in groups.items():
        complete=[r for r in subset if r["joint_source_complete"]]
        positives=[r for r in complete if r["future_2x_high"]==1]
        watch_pairs=[r for r in complete if r["watch_count_3m"]>0]
        pre=[r for r in positives if r["first_2x_watch_class"]=="EARLY_STRICT"]
        leads=[r["nearest_pre_cross_watch_lead_minutes_2x"] for r in pre]
        out={
          "attempted":len(subset),"complete":len(complete),"censored_source":len(subset)-len(complete),
          "watch_events":sum(r["watch_count_3m"] for r in complete),
          "watch_symbol_dates":len(watch_pairs),
          "gt2x":len(positives),
          "gt5x":sum(r["future_5x_high"] for r in complete),
          "gt10x":sum(r["future_10x_high"] for r in complete),
          "2x_early_strict":len(pre),
          "2x_same_minute_not_early":sum(r["first_2x_watch_class"]=="SAME_MINUTE_NOT_EARLY" for r in positives),
          "2x_late":sum(r["first_2x_watch_class"]=="LATE" for r in positives),
          "2x_no_watch":sum(r["first_2x_watch_class"]=="NO_WATCH" for r in positives),
          "watch_and_not_2x_under_calendar_label":sum(r["future_2x_high"]==0 for r in watch_pairs),
          "no_watch_and_not_2x_under_calendar_label":sum(r["future_2x_high"]==0 and r["watch_count_3m"]==0 for r in complete),
          "early_nearest_pre_cross_lead_min":min(leads) if leads else None,
          "early_nearest_pre_cross_lead_median_min":statistics.median(leads) if leads else None,
          "early_lead_at_least_5min":sum(m>=5 for m in leads),
          "early_lead_at_least_15min":sum(m>=15 for m in leads),
          "early_lead_at_least_60min":sum(m>=60 for m in leads),
        }
        if key=="ALL":desc["overall"]=out;desc["source_verified_complete"]=len(complete)
        elif key in ("26","30","32"):desc["cohorts"][key]=out
        else:desc["all_dates"].append({"date":key,**out})
    for stage,counts in FINAL_COUNTS.items():
        c=desc["cohorts"][str(stage)]
        if (c["complete"],c["watch_events"],c["gt2x"])!=counts:
            raise ValueError(f"STAGE{stage}_AGGREGATE_SUMMARY_MISMATCH: {c}")
    if desc["overall"]["gt2x"]!=88 or desc["overall"]["2x_early_strict"]!=84:
        raise ValueError("FROZEN_GT_RECONCILIATION_FAIL")
    return desc

def export(rows,result,out):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    with (out/"monster_stage34_full18date_13644_coin_date_controls.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=COLS,lineterminator="\n")
        w.writeheader();w.writerows(rows)
    with (out/"monster_stage34_88_gt2x_first_cross_watch_registry.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=COLS,lineterminator="\n")
        w.writeheader();w.writerows(r for r in rows if r["future_2x_high"]==1)
    (out/"monster_stage34_18date_discovery_census_verified.json").write_text(
      json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STAGE34_108_ORIGINAL_SHA_PASS "+json.dumps({k:v for k,v in result["overall"].items() if k in (
       "complete","censored_source","watch_events","watch_symbol_dates","gt2x","gt5x","gt10x","2x_early_strict","2x_late","2x_no_watch","watch_and_not_2x_under_calendar_label",
       "early_nearest_pre_cross_lead_median_min","early_lead_at_least_5min")},sort_keys=True))

def selftest():
    def case(watch,cross="2025-01-01T01:00:00Z"):
        return {"status":"COMPLETE_BOTH_168H","date":"2025-01-01","symbol":"TESTUSDT",
        "V4_original3m":{"watch_utcs":watch,"watch_count":len(watch)},
        "labels_original3m":{k:{"is_gt_positive":k=="2x","cross_1m_high_UTC":cross if k=="2x" else None} for k in ("2x","5x","10x")}}
    cases=[(["2025-01-01T00:57:00Z"],"EARLY_STRICT",3),
           (["2025-01-01T01:00:00Z"],"SAME_MINUTE_NOT_EARLY",0),
           (["2025-01-01T01:03:00Z"],"LATE",""),
           ([],"NO_WATCH","")]
    for watch,label,lead in cases:
        r=normalized_case(32,case(watch))
        assert r["first_2x_watch_class"]==label
        assert r["nearest_pre_cross_watch_lead_minutes_2x"]==lead
    missing=normalized_case(32,{"status":"CENSORED_GT_NOT_COMPLETE_168H","date":"2025-01-01","symbol":"TESTUSDT"})
    assert missing["future_2x_high"]=="" and missing["first_2x_watch_class"]=="CENSORED_SOURCE"
    print("STAGE34_CAUSAL_CLASSIFICATION_SELFTEST_PASS")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--selftest",action="store_true")
    parser.add_argument("--stage26-proof",type=Path)
    parser.add_argument("--stage30-proof",type=Path)
    parser.add_argument("--stage32-proof",type=Path)
    parser.add_argument("--artifacts-dir",type=Path)
    parser.add_argument("--out",type=Path)
    a=parser.parse_args()
    if a.selftest:
        selftest()
        return
    required=(a.stage26_proof,a.stage30_proof,a.stage32_proof,a.artifacts_dir,a.out)
    if any(x is None for x in required):
        parser.error("proofs for all 3 cohorts, artifact directory and output required")
    rows,receipts=read_108({26:a.stage26_proof,30:a.stage30_proof,32:a.stage32_proof},a.artifacts_dir)
    export(rows,summary(rows,receipts),a.out)

if __name__=="__main__":
    main()
