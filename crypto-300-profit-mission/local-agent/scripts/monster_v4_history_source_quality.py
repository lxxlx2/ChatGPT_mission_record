#!/usr/bin/env python3
"""Audit frozen genuine 1m sources for all predeclared Stage5 event identities.

Not a strategy replay. Missing 24h warmup is reported, never filled.
"""
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

EVIDENCE=Path(__file__).resolve().parents[2]/"monster/evidence"
STAGE5=EVIDENCE/"monster_stage5_first_watch_prestates_60case_20261010.csv"


def timestamp(value):
    return int(datetime.fromisoformat(value.replace("Z","+00:00")).timestamp()*1000)


def audit(evidence=EVIDENCE, stage5=STAGE5):
    with Path(stage5).open(encoding="utf-8",newline="") as f:
        identities=list(csv.DictReader(f))
    if len(identities)!=60:
        raise ValueError("UNEXPECTED_STAGE5_CASE_COUNT")
    rows=[]
    for case in identities:
        symbol=case["symbol"];venue=case["venue"];watch=case["watch_utc"]
        expected_time=timestamp(watch)-30*3600_000
        file=Path(evidence)/("monster_v4_replay_1m_"+venue+"_"+symbol+"_"+
                             watch[:10]+".json")
        if not file.is_file():
            rows.append({"venue":venue,"symbol":symbol,"cohort":case["cohort"],
                         "watch_utc":watch,"status":"SOURCE_NOT_FETCHED"})
            continue
        contents=file.read_bytes()
        src=json.loads(contents)
        if ((src["symbol"],src["venue"],src["old_watch_utc"],src["cohort"])
            !=(symbol,venue,watch,case["cohort"])):
            raise ValueError("SOURCE_IDENTITY_MISMATCH:"+symbol)
        bars=src["bars"]
        seen=set();duplicate=0;out_of_order=0;prior=None;first=None
        for item in bars:
            ms=int(item[0])
            if first is None:
                first=ms
            if ms in seen:
                duplicate+=1
            seen.add(ms)
            if prior is not None and ms<=prior:
                out_of_order+=1
            prior=ms
        exact=(len(bars)==3600 and all(
            int(bar[0])==expected_time+60000*i for i,bar in enumerate(bars)))
        if exact and src["data_integrity"]!="CONTIGUOUS_3600":
            raise ValueError("SOURCE_METADATA_DISAGREES_WITH_BARS:"+symbol)
        if not exact and src["data_integrity"]!="INCOMPLETE":
            raise ValueError("SOURCE_INCOMPLETE_UNFLAGGED:"+symbol)
        first_lag=round((first-expected_time)/60000,2) if first is not None else None
        before_old_watch=sum(int(x[0])<timestamp(watch) for x in bars)
        rows.append({
            "venue":venue,"symbol":symbol,"cohort":case["cohort"],
            "group":case["group"],"watch_utc":watch,
            "status":"VALID_60H" if exact else "INCOMPLETE_60H",
            "rows_returned":len(bars),"distinct_minute_bars":len(seen),
            "first_available_vs_expected_minutes":first_lag,
            "raw_rows_before_original_watch":before_old_watch,
            "duplicate_minutes_in_download":duplicate,
            "out_of_order_or_duplicate_positions":out_of_order,
            "sha256_raw_evidence":hashlib.sha256(contents).hexdigest(),
        })
    statuses=Counter(x["status"] for x in rows)
    groups={}
    for kind in ("FULLMARKET_SAMPLED","GT5X_PREHIT_POSITIVE"):
        subset=[x for x in rows if x["cohort"]==kind]
        groups[kind]={"registered":len(subset),
                      "valid":sum(x["status"]=="VALID_60H" for x in subset),
                      "incomplete":sum(x["status"]=="INCOMPLETE_60H" for x in subset),
                      "not_fetched":sum(x["status"]=="SOURCE_NOT_FETCHED" for x in subset)}
    listing=[x for x in rows if x.get("group")=="new_listing_proxy"]
    return {"identity_source":"STAGE5_FROZEN_60_CASES",
            "registered_cases":len(identities),
            "fetched_case_files":sum(x["status"]!="SOURCE_NOT_FETCHED" for x in rows),
            "status_counts":dict(statuses),"cohorts":groups,
            "new_listing_proxy_valid_24h_warmup":sum(
                x["status"]=="VALID_60H" for x in listing),
            "new_listing_proxy_cases":len(listing),
            "missing_data_is_not_model_miss":True,
            "cross_section_is_not_unbiased_full_market":True,
            "cases":rows}


def main():
    print(json.dumps(audit(),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
