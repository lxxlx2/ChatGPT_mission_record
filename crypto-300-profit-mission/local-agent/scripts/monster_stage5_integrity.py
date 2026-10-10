#!/usr/bin/env python3
"""Strict read-only integrity gate for the fixed 60-case Monster Stage5 artifact.

Verifies frozen event identity and cohort membership; cannot substitute for raw
Binance API replay, future shadow monitoring, or actual trading fill validation.
"""
import argparse
import csv
import json
import math
import statistics
from collections import Counter
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[2] / "monster" / "evidence"
BASELINE = "monster_stage3_combined_60case_360_scenario_20261010.csv"
FULL = "monster_stage5_first_watch_prestates_60case_20261010.csv"
SHORT = "monster_stage5_short_listing_causal_features_20261010.csv"
IDENTITY = ("cohort", "group", "venue", "symbol", "watch_utc")
COHORTS = {"FULLMARKET_SAMPLED": 30, "GT5X_PREHIT_POSITIVE": 30}
NUMERIC = ("ret1_pct","ret4_pct","btc_ret1_pct","btc_ret4_pct",
           "relative1_pct","relative4_pct","quote_last_hour_usdt",
           "upper_wick_range_pct","now_ret24_pct")
REQUIRED_NO_SHORT = ("ret1_pct", "ret4_pct", "relative1_pct", "relative4_pct",
                     "vol_ratio_prev23", "quote_last4_share_pct",
                     "positive_steps_last4", "breakout_prev23_pct",
                     "upper_wick_range_pct")

def read(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("MISSING_HEADER")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("DUPLICATE_COLUMNS")
        rows = list(reader)
    if not rows:
        raise ValueError("NO_ROWS")
    for row in rows:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("CSV_MALFORMED")
    return rows

def key(row):
    return tuple(row.get(n, "") for n in IDENTITY)

def index(rows, kind):
    found={}
    for row in rows:
        identity=key(row)
        if any(not s for s in identity) or identity in found:
            raise ValueError(kind + "_DUPLICATE_OR_INCOMPLETE_IDENTITY")
        found[identity]=row
    return found

def number(row, field, required=False):
    raw=row.get(field, "")
    if raw is None or raw=="":
        if required:
            raise ValueError("MISSING_"+field)
        return None
    try:
        v=float(raw)
    except (TypeError,ValueError) as exc:
        raise ValueError("INVALID_"+field) from exc
    if not math.isfinite(v):
        raise ValueError("NONFINITE_"+field)
    return v

def approximately(a,b):
    return abs(a-b)<=0.00004

def validate(directory=EVIDENCE):
    directory=Path(directory)
    baseline=[x for x in read(directory/BASELINE) if x["model"]=="NOW"]
    full=read(directory/FULL)
    short=read(directory/SHORT)
    if len(baseline)!=60 or len(full)!=60 or len(short)!=18:
        raise ValueError("UNEXPECTED_FROZEN_COUNTS")
    b=index(baseline,"BASELINE")
    f=index(full,"STAGE5")
    s=index(short,"SHORT")
    if b.keys()!=f.keys():
        raise ValueError("FROZEN_SAMPLE_CHANGED")
    if Counter(x["cohort"] for x in full)!=Counter(COHORTS):
        raise ValueError("COHORT_UNBALANCED")
    expected_short={k for k,r in f.items() if r["status"]=="TOKEN_DATA_MISSING"}
    if set(s)!=expected_short:
        raise ValueError("SHORT_HISTORY_LOST_OR_EXTRA")
    if len(expected_short)!=18:
        raise ValueError("EXPECTED_18_PARTIAL_HISTORY")
    for identity,row in f.items():
        src=b[identity]
        if row["status"] not in ("OK","TOKEN_DATA_MISSING"):
            raise ValueError("BAD_FULL_HISTORY_STATUS")
        if not row["watch_utc"].endswith("Z"):
            raise ValueError("WATCH_TIME_NOT_UTC")
        now=number(row,"now_ret24_pct",True)
        if not approximately(now,number(src,"ret24_pct",True)):
            raise ValueError("OUTCOME_SOURCE_MISMATCH")
        for label in ("gt_maxhigh_x","gt_maxclose_x"):
            if row[label]!=src[label]:
                raise ValueError("FUTURE_LABEL_CHANGED")
        if row["status"]=="OK":
            for col in REQUIRED_NO_SHORT:
                number(row,col,True)
            if row["error"]:
                raise ValueError("OK_WITH_ERROR")
        else:
            for col in REQUIRED_NO_SHORT:
                if row[col]!="":
                    raise ValueError("SHORT_HISTORY_SHOULD_NOT_PRETEND_FULL24")
        for field in NUMERIC:
            number(row,field)
        if row["status"]=="OK":
            r1=number(row,"ret1_pct",True)-number(row,"btc_ret1_pct",True)
            r4=number(row,"ret4_pct",True)-number(row,"btc_ret4_pct",True)
            if not approximately(r1,number(row,"relative1_pct",True)) or not approximately(r4,number(row,"relative4_pct",True)):
                raise ValueError("BTC_RELATIVE_ARITHMETIC_MISMATCH")
    for identity,row in s.items():
        if row["status"]!="PARTIAL_LISTING_HISTORY":
            raise ValueError("INVALID_SHORT_RECOVERY_STATUS")
        n=number(row,"available_closed_hours",True)
        if n<1 or n>=24 or int(n)!=n:
            raise ValueError("INVALID_SHORT_HOUR_COUNT")
        if row["error"]:
            raise ValueError("SHORT_RECOVERED_HAS_ERROR")
        if row["now_ret24_pct"]!=f[identity]["now_ret24_pct"]:
            raise ValueError("SHORT_OUTCOME_CHANGED")
        if row["gt_maxclose_x"]!=f[identity]["gt_maxclose_x"]:
            raise ValueError("SHORT_LABEL_CHANGED")
        for label, minimum in [("ret1_pct",2),("ret4_pct",5),
                               ("positive_steps_last4",5),
                               ("vol_ratio_preavailable",4)]:
            value=number(row,label)
            if n<minimum and value is not None:
                raise ValueError("INVENTED_INSUFFICIENT_SHORT_HISTORY_"+label)
        r1=number(row,"ret1_pct")
        rel1=number(row,"relative1_pct")
        b1=number(row,"btc_ret1_pct")
        if r1 is not None and (rel1 is None or b1 is None or not approximately(r1-b1,rel1)):
            raise ValueError("SHORT_RELATIVE_MISMATCH")
        r4=number(row,"ret4_pct")
        rel4=number(row,"relative4_pct")
        b4=number(row,"btc_ret4_pct")
        if r4 is not None and (rel4 is None or b4 is None or not approximately(r4-b4,rel4)):
            raise ValueError("SHORT_RELATIVE4_MISMATCH")
    full_count=Counter(x["cohort"] for x in full if x["status"]=="OK")
    short_count=Counter(x["cohort"] for x in short)
    return {
        "state":"READ_ONLY_COHORT_INTEGRITY_VERIFIED",
        "full_24h_valid":dict(sorted(full_count.items())),
        "short_listing_recovered":dict(sorted(short_count.items())),
        "frozen_total":len(full), "short_rows":len(short),
        "note":"Historical labeled cohorts are exposed. This is NOT trading performance validation."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",type=Path,default=EVIDENCE)
    opts=p.parse_args()
    print(json.dumps(validate(opts.evidence),indent=2,sort_keys=True))

if __name__=="__main__":
    main()
