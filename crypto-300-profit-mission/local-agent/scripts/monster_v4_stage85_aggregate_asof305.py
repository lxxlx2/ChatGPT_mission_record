#!/usr/bin/env python3
"""Stage85 aggregate only after exactly all 24 as-of source shards pass."""
from __future__ import annotations

import argparse
import collections
import json
import statistics
from pathlib import Path

try:
    import monster_v4_stage85_305_d1_asof_evidence as stage85
    from monster_v4_stage80_dual_entry_core import decimal, utc_ms
except ImportError:
    from scripts import monster_v4_stage85_305_d1_asof_evidence as stage85
    from scripts.monster_v4_stage80_dual_entry_core import decimal, utc_ms

SCHEMA="MONSTER_STAGE85_FULL305_REAL_PUBLISHER_SHA_ASOF_FEATURE_CENSUS_V1"
D24=24*3600000


def load_complete(folder: Path):
    paths=sorted(folder.glob("monster-stage85-*.json"))
    if len(paths)!=24:
        raise ValueError("STAGE85_INCOMPLETE_24_SHARDS "+str(len(paths)))
    seen,all_rows=set(),[]
    for p in paths:
        x=json.loads(p.read_text())
        if x["schema"]!=stage85.SCHEMA:
            raise ValueError("STAGE85_UNEXPECTED_STAGE85_SOURCE_SCHEMA")
        k=(x["date"],x["shard"])
        if k in seen or k[0] not in stage85.DATES or k[1] not in range(4):
            raise ValueError("STAGE85_DUPLICATE_OR_UNKNOWN_SHARD")
        seen.add(k)
        expected={(r["date"],r["symbol"]) for r in stage85.selected(*k)}
        got={(r["date"],r["symbol"]) for r in x["rows"]}
        if len(x["rows"])!=len(expected) or expected!=got:
            raise ValueError("STAGE85_MISSING_OR_ADDED_FROZEN_D1")
        if x["expected_first_D1_events"] != len(expected):
            raise ValueError("STAGE85_COUNT_MISMATCH")
        all_rows+=x["rows"]
    if seen!={(d,s) for d in stage85.DATES for s in range(4)} or len(all_rows)!=305:
        raise ValueError("STAGE85_MISSING_FULL305")
    original, _=stage85.load_sources()
    if {(r["date"],r["symbol"]) for r in all_rows}!={(r["date"],r["symbol"]) for r in original}:
        raise ValueError("STAGE85_305_SOURCE_CENSUS_DIFFERENT")
    return sorted(all_rows,key=lambda x:(x["date"],x["symbol"]))


def median(items,field):
    vals=sorted(decimal(x[field]) for x in items if x["source_status"]==stage85.GOOD)
    return str(vals[len(vals)//2]) if vals else None


def aggregate(rows):
    original,_=stage85.load_sources()
    old={(x["date"],x["symbol"]):x for x in original}
    daily=collections.Counter()
    full=collections.Counter()
    entries=[]
    for row in rows:
        before=old[(row["date"],row["symbol"])]
        if (row["D0_FIRST_UTC"]!=before["D0_FIRST_UTC"] or
            row["D1_FIRST_UTC"]!=before["D1_FIRST_UTC"] or
            row["D1_PATH"]!=before["D1_PATH"]):
            raise ValueError("STAGE85_D1_FIRST_HISTORIC_TIMESTAMP_DRIFT")
        if row["source_status"] not in (stage85.GOOD, stage85.MISS):
            raise ValueError("STAGE85_UNKNOWN_CATEGORY")
        if row["source_status"]==stage85.GOOD and not row["stage79_frozen_gate_exactly_true"]:
            raise ValueError("STAGE85_FROZEN_GATE_NOT_TRUE")
        d=(utc_ms(row["D1_FIRST_UTC"])-utc_ms(row["date"]+"T06:00:00Z"))//D24
        if d not in range(7):
            raise ValueError("STAGE85_D1_OUTSIDE_7D_ANCHOR")
        daily[(row["date"],d)] +=1
        full[row["source_status"]]+=1
        entries.append(dict(row,calendar_2x_evaluation_only=bool(before["historical_anchor_GT2"]),
                            early5_gt2_evaluation_only=bool(before["D1_at_least_5m_before_2x"])))
    if len(entries)!=305:
        raise ValueError("STAGE85_SOME_D1_VANISHED")
    valid=[x for x in entries if x["source_status"]==stage85.GOOD]
    crowded = [x for x in valid if x["D1_FIRST_UTC"] >= "2025-02-03T06:00:00Z" and
               x["D1_FIRST_UTC"] < "2025-02-04T06:00:00Z"]
    normal=[x for x in valid if not x["calendar_2x_evaluation_only"]]
    label2=[x for x in valid if x["calendar_2x_evaluation_only"]]
    mem=lambda xs: {
       "ret60_pct":median(xs,"asof_D1_ret60_pct"),
       "quote15_USDT":median(xs,"asof_D1_quote15_USDT"),
       "trade15":median(xs,"asof_D1_trade15"),
       "normalized_quote15_prev45":median(xs,"asof_D1_normalized_quote15_prev45"),
       "relative_first_d0_pct":median(xs,"asof_D1_ret_from_first_D0_pct")
    }
    output={
        "schema":SCHEMA,"source_full519_blob":stage85.PIN83,
        "source_firstD0_stage64_blob":stage85.PIN64,
        "attempted_original_D1":305,
        "source_verified":len(valid),
        "source_censored":len(entries)-len(valid),
        "source_status_counts":dict(full),
        "D1_direct":sum(x["D1_PATH"]=="DIRECT_AT_FIRST_D0" for x in entries),
        "D1_reignition":sum(x["D1_PATH"]=="REIGNITION_AFTER_D0" for x in entries),
        "complete_original_42_daily_bucket_count":42,
        "D1_calendar_2x_evaluation_only":sum(x["calendar_2x_evaluation_only"] for x in entries),
        "D1_early5_2x_evaluation_only":sum(x["early5_gt2_evaluation_only"] for x in entries),
        "day_count_top": [
          {"date":d,"day_index":i,"D1_events":daily[(d,i)]}
          for d,i in sorted(daily,key=lambda k:(-daily[k],k))[:10]
        ],
        "median_asof_features_full":mem(valid),
        "median_asof_features_anchor2x":mem(label2),
        "median_asof_features_normal_non2x":mem(normal),
        "median_asof_features_most_crowded_day":mem(crowded),
        "crowded_day_count":len(crowded),
        "crowded_day_anchor2x":sum(x["calendar_2x_evaluation_only"] for x in crowded),
        "source_valid_for_old_2x":len(label2),
        "not_a_new_D1_policy":True,"no_new_threshold":True,
        "historical_exposed":True,
        "oos":"NOT_DONE","real_executable_net_pnl":"UNKNOWN",
        "other_AI_review":"NOT_DONE","deployment":"NO_GO","gmail":"OFF",
        "autotrade":"NO_GO","frank":"UNCHANGED"}
    return output,entries


def selftest():
    a, _=stage85.load_sources()
    assert len(a)==305
    assert sum(x["D1_PATH"]=="REIGNITION_AFTER_D0" for x in a)==141
    print("STAGE85_AGGREGATE_ALL305_CENSUS_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--artifact-dir",type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    if args.selftest:selftest();return
    if not args.artifact_dir or not args.out:
        p.error("--artifact-dir and --out required")
    rows=load_complete(args.artifact_dir)
    summary,detail=aggregate(rows)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"monster_stage85_all305_official_D1_asof_features.jsonl").write_text(
        "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in detail))
    (args.out/"monster_stage85_all305_official_asof_summary.json").write_text(
        json.dumps(summary,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE85_ALL305_SOURCE_ASOF "+json.dumps({
        k:summary[k] for k in ("attempted_original_D1","source_verified","source_censored",
              "D1_calendar_2x_evaluation_only","D1_early5_2x_evaluation_only",
              "crowded_day_count","median_asof_features_full","median_asof_features_most_crowded_day")
    },sort_keys=True))


if __name__=="__main__":
    main()
