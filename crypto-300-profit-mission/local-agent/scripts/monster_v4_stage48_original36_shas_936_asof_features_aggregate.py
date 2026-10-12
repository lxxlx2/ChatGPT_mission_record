#!/usr/bin/env python3
"""Rehash all Stage48 original 36 GitHub zip bytes and recompute 936 exact D0 features.

Descriptive all-market first vs repeated as-of features; no threshold fit.
Cross-check original Stage45 5400 rows, first-event original P1v0.2 arithmetic,
real Binance per-day official publisher SHA and Stage47 2x repeat baseline.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,statistics,zipfile
from decimal import Decimal
from pathlib import Path

EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
PREV=EVIDENCE/"monster_stage45_blind_all5400_originalV4_P1v02_cases.jsonl"
STAGE47=EVIDENCE/"monster_stage47_all_market_first_and_repeated_D0_watch_vs_real2x_audit.json"
P45="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
SCHEMA="MONSTER_STAGE48_ORIGINAL36_GITHUB_SHA_936_REAL_ASOF_D0_EVENT_FEATURES_V1"
SRC="MONSTER_STAGE48_ALL437_FIRST_REPEAT_936_EVENT_REAL_BINANCE_USDM_ASOF_1M_SHA_V1"
DAYS=("2025-01-09","2025-09-02","2026-01-26","2026-02-24","2026-03-28","2026-05-10")
RUN=38216755205

def sha(b):return hashlib.sha256(b).hexdigest()

def read(manifest,folder):
    if manifest.get("source_run_id")!=RUN or len(manifest.get("artifacts",[]))!=36:
        raise ValueError("STAGE48_WRONG_ORIGINAL36_SOURCE_RUN")
    rows=[];receipts=[];identities=set()
    for item in manifest["artifacts"]:
        d=item["date"];i=int(item["shard"]);aid=int(item["artifact_id"])
        if d not in DAYS or i not in range(6) or (d,i) in identities:
            raise ValueError("STAGE48_DUPLICATE_OR_BAD_SOURCE_SHARD")
        identities.add((d,i))
        raw=(Path(folder)/(str(aid)+".zip")).read_bytes()
        if sha(raw)!=item["zip_sha256"]:raise ValueError("STAGE48_ORIGINAL_GITHUB_ZIP_SHA_NOT_VERIFIED")
        inner=f"monster_stage48_{d}_shard{i}.json"
        with zipfile.ZipFile(Path(folder)/(str(aid)+".zip")) as z:
            if z.namelist()!=[inner]:raise ValueError("STAGE48_WRONG_ORIGINAL_ZIP_INNER")
            content=z.read(inner)
        doc=json.loads(content)
        if (doc.get("schema")!=SRC or doc["date"]!=d or doc["shard"]!=i
            or len(doc["rows"])!=150 or doc["original_full_universe"]!=150):
            raise ValueError("STAGE48_NOT_ORIGINAL_SOURCE_ALL150")
        for r in doc["rows"]:
            if r["date"]!=d:raise ValueError("STAGE48_RESULT_DATE_CHANGED")
            for event in r["events"]:
                if not event["actual_1m_official_source_closes_before_D0_utc"]:
                    raise ValueError("STAGE48_FUTURE_PRICE_LEAK")
            if r["events"]:
                proofs=r.get("official_refetched_daily_publisher_sha_receipts",[])
                if not proofs or not all(
                    x["verified_official_publisher_SHA256"] and len(x["zip_sha256"])==64
                    for x in proofs):
                    raise ValueError("STAGE48_MISSING_REAL_BINANCE_DAILY_SHA")
        rows+=doc["rows"]
        if (doc["actual_watch_coin_dates"]!=sum(bool(r["events"]) for r in doc["rows"]) or
            doc["real_original_D0_WATCH_events"]!=sum(len(r["events"]) for r in doc["rows"])):
            raise ValueError("STAGE48_SHARD_COUNTER_MISMATCH")
        receipts.append({"date":d,"shard":i,"artifact_id":aid,
            "original_GitHub_zip_SHA256":sha(raw),"original_internal_JSON_SHA256":sha(content),
            "actual_watch_coin_dates":doc["actual_watch_coin_dates"],
            "actual_events":doc["real_original_D0_WATCH_events"]})
    if identities!={(day,i) for day in DAYS for i in range(6)}:
        raise ValueError("STAGE48_NOT_ALL_36_SOURCE_CASES")
    return sorted(rows,key=lambda x:(x["date"],x["symbol"])),sorted(receipts,key=lambda x:(x["date"],x["shard"]))

def distribution(values):
    if not values:return {"n":0,"median":None,"p25":None,"p75":None}
    a=sorted(float(x) for x in values)
    def quantile(p):
        ix=(len(a)-1)*p;lo=int(ix);hi=min(lo+1,len(a)-1);return round(a[lo]+(a[hi]-a[lo])*(ix-lo),6)
    return {"n":len(a),"median":quantile(.5),"p25":quantile(.25),"p75":quantile(.75)}

def study(rows,receipts):
    originals=[json.loads(line) for line in PREV.read_text(encoding="utf-8").splitlines() if line]
    if len(rows)!=5400 or len(originals)!=5400:
        raise ValueError("STAGE48_NOT_FULL_5400_ORIGINAL")
    orig={(r["date"],r["symbol"]):r for r in originals}
    if len(orig)!=5400 or len({(r["date"],r["symbol"]) for r in rows})!=5400:
        raise ValueError("STAGE48_DUPLICATE_CASE")
    groups=collections.defaultdict(list);event_rows=[];cases=collections.Counter()
    for r in rows:
        base=orig.get((r["date"],r["symbol"]))
        if base is None or base["source_status"]!=r["source_status"]:
            raise ValueError("STAGE48_STAGE45_COIN_ID_OR_SOURCE_CHANGED")
        if base["source_status"]==P45:
            if len(base["WATCH_UTC"])!=len(r["events"]) or base["watch_count"]!=len(r["events"]):
                raise ValueError("STAGE48_UNCHANGED_ORIGINAL_D0_WATCH_COUNT_NOT_EQUAL")
            expected_receipts={p["date"]:p["zip_sha256"] for p in base["verified_9_daily_publisher_sha256"]}
            for p in r.get("official_refetched_daily_publisher_sha_receipts",[]):
                if expected_receipts[p["date"]]!=p["zip_sha256"]:
                    raise ValueError("STAGE48_REFETCHED_DAILY_ZIP_SHA_CHANGED")
        else:
            if r["events"]:raise ValueError("STAGE48_CENSORED_HAD_FAKE_WATCH")
        for ix,event in enumerate(r["events"]):
            if event["asof_D0_WATCH_UTC"]!=base["WATCH_UTC"][ix] or event["watch_ordinal"]!=ix+1:
                raise ValueError("STAGE48_ASOF_WATCH_EVENT_TIMESTAMP_ID_INVALID")
            if ix==0:
                # Cross-source arithmetic: first D0 Stage48 exact true 1m asof
                # must reproduce prior Stage45 frozen P1v02 input evidence.
                if (Decimal(event["ret60_pct"])!=Decimal(base["p1_ret60_pct"]) or
                    Decimal(event["quote15_USDT"])!=Decimal(base["p1_quote15_usdt"]) or
                    Decimal(event["quote_prev45_USDT"])!=Decimal(base["p1_quote_prev45_usdt"])):
                    raise ValueError("STAGE48_FIRST_WATCH_P1V02_TRUE_SOURCE_VALUE_DRIFT")
            two=base["original_GT2x_1h"]=="True"
            if two:
                if event["label_only_strictly_before_first_2x_utc"]:
                    name="2X_FIRST_EARLY" if ix==0 else "2X_REPEAT_BEFORE_FIRST_2X"
                else:
                    name="2X_FIRST_AFTER_OR_AT_2X" if ix==0 else "2X_REPEAT_AFTER_OR_AT_2X"
            else:
                name="NORMAL_FIRST" if ix==0 else "NORMAL_REPEAT"
            groups[name].append(event)
            event_rows.append({"date":r["date"],"symbol":r["symbol"],
                "historical_2x_from_window_anchor":two,"historical_gt5x":base["original_GT5x_1h"]=="True",
                "historical_gt10x":base["original_GT10x_1h"]=="True",
                "cohort":name,**event})
        cases[base["source_status"]]+=1
    active=[r for r in rows if r["events"]]
    all_events=sum(len(r["events"]) for r in rows)
    if len(active)!=437 or all_events!=936:
        raise ValueError("STAGE48_EXACT_ALL437_936_NOT_REPRODUCED")
    stage47=json.loads(STAGE47.read_text(encoding="utf-8"))
    future2x=[r for r in rows if orig[(r["date"],r["symbol"])]["original_GT2x_1h"]=="True"
              and r["source_status"]==P45]
    early2=[r for r in future2x if sum(e["label_only_strictly_before_first_2x_utc"] for e in r["events"])>=2]
    if (len(future2x)!=41 or len(early2)!=stage47["positive2x_second_WATCH_strictly_before_GT2x"] or
        cases[P45]!=stage47["valid_source_total"]):
        raise ValueError("STAGE48_STAGE47_2X_SECOND_EARLY_OR_VALID_BASELINE_PARITY_FAILED")
    def summarize_features(vals):
        out={"event_count":len(vals)}
        for key in ("ret60_pct","quote15_USDT","normalized_quote15_vs_prior45",
                    "trades15","ret_from_first_WATCH_last_close_pct","minutes_since_previous_D0"):
            out[key]=distribution([e[key] for e in vals if e.get(key) is not None])
        return out
    cohorts={name:summarize_features(events) for name,events in sorted(groups.items())}
    dates=[]
    for date in DAYS:
        casesd=[x for x in rows if x["date"]==date]
        allx=[e for e in event_rows if e["date"]==date]
        dates.append({"date":date,"all_symbol_date":len(casesd),
                      "source_valid":sum(r["source_status"]==P45 for r in casesd),
                      "original_WATCH_coin_dates":sum(bool(r["events"]) for r in casesd),
                      "WATCH_event_count":len(allx),
                      "normal_repeat_WATCH_events":sum(e["cohort"]=="NORMAL_REPEAT" for e in allx),
                      "2x_early_repeat_WATCH_events":sum(e["cohort"]=="2X_REPEAT_BEFORE_FIRST_2X" for e in allx)})
    bulla=[e for e in event_rows if e["symbol"]=="BULLAUSDT" and e["date"]=="2026-01-26" and
           e["cohort"] in ("2X_FIRST_EARLY","2X_REPEAT_BEFORE_FIRST_2X")]
    return {
      "schema":SCHEMA,"original_source_run_id":RUN,
      "original36_GitHub_SHA_receipts":receipts,
      "all5400_original_coin_date_status":dict(cases),
      "total_full_source":cases[P45],
      "original_watch_coin_dates":len(active),
      "actual_original_D0_events":all_events,
      "original_repeated_events":all_events-len(active),
      "historical_2x":len(future2x),
      "early_repeat_positive_2x":len(early2),
      "feature_cohort_statistics":cohorts,
      "date_scoped_background_and_2x":dates,
      "BULLA_FIRST_AND_PRE2X_SECOND_REAL_MINUTE_FEATURES":bulla,
      "source_and_strategy_scope":"EXPLORATORY_DESCRIPTIVE_EXISTING_SIX_EXPOSED_DATES_NOT_NEW_VALIDATION",
      "features_computed_from_only_closed_1m_before_original_WATCH":True,
      "no_new_strategy_thresholds_or_BUY":True,"independent_other_AI_review":"NOT_DONE",
      "true_orderbook_fill":"UNVERIFIED","Monster_deploy":"NO_GO","Frank":"UNCHANGED","Gmail":"OFF","trading":"NO_GO"
    },event_rows

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--zip-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    rows,receipts=read(json.loads(a.manifest.read_text()),a.zip_dir)
    report,events=study(rows,receipts)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage48_original36_SHA_all936_true_asof_minute_features_summary.json").write_text(
        json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    with (a.out/"monster_stage48_full936_real_closed1m_original_D0_event_features.jsonl").open("w",encoding="utf-8") as f:
        for x in events:f.write(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n")
    with (a.out/"monster_stage48_all5400_source_and_437_watch_case_inventory.jsonl").open("w",encoding="utf-8") as f:
        for r in rows:
            keep={k:r[k] for k in ("date","symbol","source_status","frozen_original_D0_watch_count")}
            keep["actual_event_count"]=len(r["events"])
            keep["source_SHA_receipts"]=r.get("official_refetched_daily_publisher_sha_receipts",[])
            f.write(json.dumps(keep,ensure_ascii=False,sort_keys=True)+"\n")
    print("STAGE48_36_ORIGINAL_GITHUB_SHA_OFFICIAL_936_ASOF_FEATURES_SUCCESS "+
        json.dumps({"source_valid":report["total_full_source"],
                    "original_watch_coin_dates":report["original_watch_coin_dates"],
                    "original_D0_events":report["actual_original_D0_events"],
                    "2x_early_second_WATCH_cases":report["early_repeat_positive_2x"]},sort_keys=True))
if __name__=="__main__":main()
