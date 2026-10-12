#!/usr/bin/env python3
"""Monster Stage61: all166 original D0 first WATCH -> P1 eligibility latency.

Only frozen Stage55 as-of fields and Stage60 historical evaluation.
No future features in P1 decision, no TTL tuning or notional assumption.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import statistics
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

E = Path(__file__).resolve().parents[2] / "monster" / "evidence"
SRC = E / "monster_stage55_all166_candidate_asof_features_and_fate.csv"
PATH = E / "monster_stage60_all166_signal_to_24h_verified_futures_price_proxy.jsonl"
PIN = {
    SRC.name: "dca780246adb28e045ed77f0f96eb4bd034fb2e7",
    PATH.name: "c76b9b73c11924cb3fdc36fb852074ff9b49b3b8",
}
SCHEMA = "MONSTER_STAGE61_ORIGINAL166_FIRST_D0_TO_P1_3MIN_POLL_LATENCY_V1"
D = Decimal
HOURS = (15, 60, 360, 1440)


def gitblob(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def timestamp(text):
    obj = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if obj.utcoffset() != timedelta(0) or obj.second or obj.microsecond:
        raise ValueError("STAGE61_CLOCK_UNALIGNED_OR_NON_UTC")
    return obj


def freeze():
    for p in (SRC, PATH):
        if gitblob(p) != PIN[p.name]:
            raise ValueError("STAGE61_FROZEN_INPUT_DRIFT " + p.name)
    with SRC.open(encoding="utf-8", newline="") as f:
        old = list(csv.DictReader(f))
    outcome = [json.loads(s) for s in PATH.read_text(encoding="utf-8").splitlines() if s]
    index = {(x["date"], x["symbol"]): x for x in outcome}
    if len(old) != 166 or len(outcome) != 166 or len(index) != 166:
        raise ValueError("STAGE61_ORIGINAL166_DRIFT")
    if len({(r["date"], r["symbol"]) for r in old}) != 166:
        raise ValueError("STAGE61_REPEATED_ASOF_CANDIDATE")
    return old, index


def derive(row, result):
    if row["date"] != result["date"] or row["symbol"] != result["symbol"]:
        raise ValueError("STAGE61_JOIN_WRONG_COIN")
    if (row["research_delivered"] == "True") != bool(result["original_v03_urgent_delivered"]):
        raise ValueError("STAGE61_ORIGINAL_BUDGET_FATE_DRIFT")
    if row["eligible_timestamp_UTC"] != result["eligible_timestamp_UTC"]:
        raise ValueError("STAGE61_SIGNAL_TIME_CHANGED")
    if result["source_status"] != "COMPLETE_OFFICIAL_DAILY_USDM_1M_PUBLISHER_SHA_PRICE_PATH":
        raise ValueError("STAGE61_MISSING_REAL_STAGE60_FUTURE_1M_DATA")
    polls = int(row["polls_until_eligible"])
    if not 1 <= polls <= 3360:
        raise ValueError("STAGE61_ORIGINAL_P1_SCAN_TICKS_INVALID")
    end = timestamp(row["eligible_timestamp_UTC"])
    first = end - timedelta(minutes=(polls - 1) * 3)
    scan_begin = timestamp(row["date"] + "T06:00:00Z")
    scan_end = scan_begin + timedelta(days=7)
    if not scan_begin <= first <= end < scan_end or int((end-scan_begin).total_seconds()) % 180:
        raise ValueError("STAGE61_FIRST_D0_OUTSIDE_REPLAY_WINDOW")
    is_first = row["mode"] == "FIRST_D0_IMMEDIATE"
    is_ongoing = row["mode"] == "ONGOING_3M_SECOND_IGNITION"
    if not (is_first or is_ongoing) or (is_first != (polls == 1)):
        raise ValueError("STAGE61_BAD_P1_REAL_MODE_AND_DELAY")
    ret_from_first = D(row["ret_from_first_D0_pct"])
    if is_first and ret_from_first != 0:
        raise ValueError("STAGE61_FIRST_D0_RET_NEEDS_ZERO")
    horizons = {}
    for mins in HOURS:
        old = result["forward_horizons"][str(mins)]
        horizons[str(mins)] = {
            "proxy_close_return_pct": old["end_close_return_pct_PROXY"],
            "proxy_max_high_pct_NOT_FILL": old["potential_max_high_pct_NOT_AN_EXIT_FILL"],
            "proxy_min_low_pct_NOT_FILL": old["adverse_min_low_pct_NOT_AN_EXIT_FILL"],
        }
    return {
        "date": row["date"], "symbol": row["symbol"],
        "first_D0_watch_reconstructed_UTC": first.isoformat().replace("+00:00", "Z"),
        "first_P1_eligible_UTC": row["eligible_timestamp_UTC"],
        "original_P1_mode": row["mode"],
        "original_P1_polls_to_eligibility": polls,
        "D0_to_P1_wait_minutes": (polls-1)*3,
        "ret_D0_closed_close_to_P1_pre_signal_closed_pct_ASOF": str(ret_from_first),
        "original_P1_delivered_research": row["research_delivered"] == "True",
        "posthoc_calendar_high2x_label_ONLY": row["future_label_AFTER_signal"],
        "futures_price_path_from_post_signal_proxy_EVALUATION_ONLY": horizons,
        "USER_ORDER_NOTIONAL": None,
        "NO_NEW_TIME_GATE_OR_STRATEGY": True,
    }


def summary(xs):
    def median(key):
        arr = [D(str(x[key])) for x in xs]
        return str(statistics.median(arr)) if arr else None
    def median_path(h, key):
        arr = [D(x["futures_price_path_from_post_signal_proxy_EVALUATION_ONLY"][str(h)][key]) for x in xs]
        return str(statistics.median(arr)) if arr else None
    return {
        "n": len(xs),
        "delay_minutes_median": median("D0_to_P1_wait_minutes"),
        "delay_minutes_max": max((r["D0_to_P1_wait_minutes"] for r in xs), default=None),
        "price_change_first_D0_to_P1_asof_pct_median": median("ret_D0_closed_close_to_P1_pre_signal_closed_pct_ASOF"),
        "post_P1_proxy_close_24h_pct_median": median_path(1440, "proxy_close_return_pct"),
        "post_P1_proxy_24h_positive_cases": sum(
            D(x["futures_price_path_from_post_signal_proxy_EVALUATION_ONLY"]["1440"]["proxy_close_return_pct"]) > 0 for x in xs),
        "post_P1_proxy_HIGH_at_least_2x_24h_NOT_FILL": sum(
            D(x["futures_price_path_from_post_signal_proxy_EVALUATION_ONLY"]["1440"]["proxy_max_high_pct_NOT_FILL"]) >= 100 for x in xs),
    }


def describe(rows):
    subsets = {
        "ALL_166": rows,
        "FIRST_D0_IMMEDIATE": [r for r in rows if r["original_P1_mode"] == "FIRST_D0_IMMEDIATE"],
        "ONGOING_SECOND_IGNITION": [r for r in rows if r["original_P1_mode"] == "ONGOING_3M_SECOND_IGNITION"],
        "D0_WAIT_OVER_60_MIN": [r for r in rows if r["D0_to_P1_wait_minutes"] > 60],
        "D0_WAIT_OVER_360_MIN": [r for r in rows if r["D0_to_P1_wait_minutes"] > 360],
        "D0_WAIT_OVER_1440_MIN": [r for r in rows if r["D0_to_P1_wait_minutes"] > 1440],
        "ORIGINAL_URGENT_DELIVERED": [r for r in rows if r["original_P1_delivered_research"]],
        "ORIGINAL_URGENT_OVER_BUDGET": [r for r in rows if not r["original_P1_delivered_research"]],
        "POSTHOC_EARLY_CALENDAR_2X": [r for r in rows if r["posthoc_calendar_high2x_label_ONLY"] == "FUTURE_2X_AND_CANDIDATE_BEFORE_5MIN"],
        "POSTHOC_ORDINARY": [r for r in rows if r["posthoc_calendar_high2x_label_ONLY"] == "ORDINARY_NOT_CALENDAR_2X"],
    }
    return {
        "schema": SCHEMA, "locked_source_blobs": PIN,
        "original_count": len(rows),
        "group_descriptive_only": {k:summary(v) for k,v in subsets.items()},
        "first_vs_ongoing_counts": {
            "immediate": len(subsets["FIRST_D0_IMMEDIATE"]),
            "ongoing": len(subsets["ONGOING_SECOND_IGNITION"]),
        },
        "NO_NEW_DELAY_OR_ALERT_THRESHOLD": True,
        "ALL_SAMPLE_ALREADY_EXPOSED": True,
        "SOURCE_IS_VERIFIED_USDM_NOT_EXECUTABLE_SPOT": True,
        "NO_ASSUMED_ORDER_SIZE": True,
        "P1_V03":"REJECTED",
        "OTHER_AI_REVIEW":"NOT_DONE",
        "MONSTER_DEPLOY":"NO_GO",
        "GMAIL":"OFF",
        "AUTOTRADE":"NO_GO",
    }


def selftest():
    simple = {
        "date": "2025-10-02", "symbol": "TESTUSDT",
        "eligible_timestamp_UTC": "2025-10-02T08:00:00Z",
        "polls_until_eligible": "11",
        "mode": "ONGOING_3M_SECOND_IGNITION",
        "ret_from_first_D0_pct": "20",
        "research_delivered": "True",
        "future_label_AFTER_signal": "ORDINARY_NOT_CALENDAR_2X",
    }
    future = {
        "date": simple["date"], "symbol": simple["symbol"],
        "eligible_timestamp_UTC": simple["eligible_timestamp_UTC"],
        "original_v03_urgent_delivered": True,
        "source_status": "COMPLETE_OFFICIAL_DAILY_USDM_1M_PUBLISHER_SHA_PRICE_PATH",
        "forward_horizons": {str(h):{
            "end_close_return_pct_PROXY": "-3.0",
            "potential_max_high_pct_NOT_AN_EXIT_FILL": "10",
            "adverse_min_low_pct_NOT_AN_EXIT_FILL": "-11"} for h in HOURS},
    }
    got = derive(simple, future)
    assert got["D0_to_P1_wait_minutes"] == 30
    assert got["first_D0_watch_reconstructed_UTC"] == "2025-10-02T07:30:00Z"
    assert summary([got])["post_P1_proxy_close_24h_pct_median"] == "-3.0"
    bad = dict(simple, polls_until_eligible="1")
    try:
        derive(bad, future)
    except ValueError as e:
        assert "REAL_MODE" in str(e)
    else:
        raise AssertionError("STAGE61_MODE_DRIFT_NOT_CAUGHT")
    print("STAGE61_ORIGINAL_3MIN_CAUSAL_DELAY_ASOF_PRICE_JOIN_SELFTEST_PASS")


def main():
    arg = argparse.ArgumentParser()
    arg.add_argument("--selftest", action="store_true")
    arg.add_argument("--out", type=Path)
    opts = arg.parse_args()
    if opts.selftest:
        selftest()
        return
    if not opts.out:
        arg.error("--out required")
    old, index = freeze()
    records = [derive(x,index[(x["date"],x["symbol"])]) for x in old]
    if len(records)!=166:
        raise ValueError("STAGE61_MISSING_ORIGINAL166")
    results = describe(records)
    if (results["first_vs_ongoing_counts"]["immediate"],
        results["first_vs_ongoing_counts"]["ongoing"]) != (46,120):
        raise ValueError("STAGE61_ORIGINAL_FIRST_SECOND_COHORT_DRIFT")
    opts.out.mkdir(parents=True, exist_ok=True)
    (opts.out/"monster_stage61_original166_firstD0_to_P1_latency_and_24h_proxy.jsonl").write_text(
        "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in records),encoding="utf-8")
    (opts.out/"monster_stage61_original166_D0_to_P1_waittime_summary.json").write_text(
        json.dumps(results,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("STAGE61_ORIGINAL166_FIRST_D0_P1_LATENCY_DIAGNOSTIC "+
          json.dumps({k:results["group_descriptive_only"][k] for k in (
              "ALL_166","FIRST_D0_IMMEDIATE","ONGOING_SECOND_IGNITION")},sort_keys=True))


if __name__ == "__main__":
    main()
