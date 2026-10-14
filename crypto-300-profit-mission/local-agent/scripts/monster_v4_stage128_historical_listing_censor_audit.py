#!/usr/bin/env python3
"""Source-locked original 5,400 G1 censor and LATER snapshot listing audit.

Offline only. A later Binance exchangeInfo.onboardDate is NOT historical eligibility.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from monster_v4_stage124_manual_snapshot_comparison import load as load_stage123

E = Path(__file__).resolve().parents[2] / "monster" / "evidence"
DAYS = ("2025-01-19", "2025-04-19", "2025-07-19",
        "2025-10-19", "2026-04-19", "2026-07-19")
STAGE37 = E / "monster_stage37_sixdate_all5400_usdm_source_and_GT.csv"
STAGE93 = E / "monster_stage93_original5400_first_watch_full_source_recall.json"
STAGE123 = E / "monster_stage123_20261014T094824Z_manifest.json"
STAGE37_GIT_BLOB = "4b02019195a7a48ef6d33606db9b57d6a3429f4b"
FULL_HOUR = "COMPLETE_168H_PUBLISHER_SHA"
SCHEMA = "MONSTER_STAGE128_LATER_ONBOARD_VS_EXPOSED_5400_CENSOR_DIAGNOSTIC_V1"


def git_blob(path):
    data = Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest()


def read_original_stage37(path=STAGE37):
    path = Path(path)
    if git_blob(path) != STAGE37_GIT_BLOB:
        raise ValueError("STAGE128_HISTORIC_STAGE37_GIT_BLOB_CHANGED")
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 5400:
        raise ValueError("STAGE128_ORIGINAL5400_COUNT_DRIFT")
    seen = set()
    counts = Counter()
    for row in rows:
        k = (row.get("date"), row.get("symbol"))
        if k in seen or row.get("date") not in DAYS or not row.get("symbol"):
            raise ValueError("STAGE128_HISTORICAL_DATE_OR_SYMBOL_INVALID")
        seen.add(k)
        counts[k[0]] += 1
    if any(counts[d] != 900 for d in DAYS):
        raise ValueError("STAGE128_HISTORICAL_900_PER_ANCHOR_DRIFT")
    if sum(r["status"] == FULL_HOUR for r in rows) != 3333:
        raise ValueError("STAGE128_HOURLY_FULL_SOURCE_COUNT_DRIFT")
    return rows


def later_onboard(row):
    if row is None:
        return None, "ABSENT_FROM_LATER_METADATA"
    value = row.get("onboardDate")
    if type(value) is not int or value <= 0:
        return None, "LATER_ONBOARD_UNKNOWN"
    return value, None


def classify(row, later_metadata):
    day = row["date"]
    if day not in DAYS or not isinstance(row.get("symbol"), str) or not row["symbol"]:
        raise ValueError("STAGE128_BAD_HISTORICAL_KEY")
    anchor = int(datetime.fromisoformat(day+"T06:00:00+00:00").timestamp()*1000)
    end = anchor + 7*86400000
    onboard, fallback = later_onboard(later_metadata)
    if row["status"] == FULL_HOUR:
        if fallback:
            kind = "HOURLY_COMPLETE_"+fallback
        elif onboard > anchor:
            kind = "HOURLY_COMPLETE_LATER_METADATA_ONBOARD_CONTRADICTION"
        else:
            kind = "HOURLY_COMPLETE_LATER_METADATA_NOT_CONTRADICTED"
    elif row["status"]:
        if fallback:
            kind = "HOURLY_INCOMPLETE_"+fallback
        elif onboard >= end:
            kind = "HOURLY_INCOMPLETE_LATER_ONBOARD_AT_OR_AFTER_WINDOW_END"
        elif onboard > anchor:
            kind = "HOURLY_INCOMPLETE_LATER_ONBOARD_INSIDE_WINDOW"
        else:
            kind = "HOURLY_INCOMPLETE_LATER_ONBOARD_AT_OR_BEFORE_ANCHOR"
    else:
        raise ValueError("STAGE128_EMPTY_SOURCE_STATUS")
    return {
        "anchor": day, "symbol": row["symbol"],
        "original_stage37_hourly_source_status": row["status"],
        "later_stage123_onboardDate_ms": onboard,
        "later_stage123_onboardDate_UTC": (
            datetime.fromtimestamp(onboard/1000, timezone.utc).isoformat().replace("+00:00","Z")
            if onboard is not None else None),
        "later_metadata_comparison": kind,
        "historical_listing_trading_identity_verified": False,
        "original_gross_2x_evidence_not_reclassified": row.get("gt2x"),
    }


def audit(rows, meta, stage93):
    if not isinstance(meta, dict) or len(meta) != 927:
        raise ValueError("STAGE128_STAGE123_METADATA_NOT_FULL927")
    if len(rows) != 5400 or len({(r["date"],r["symbol"]) for r in rows}) != 5400:
        raise ValueError("STAGE128_HISTORICAL5400_NOT_UNIQUE")
    if stage93.get("all_frozen_900x6_attempts") != 5400 or stage93.get("source_complete") != 3283 or stage93.get("source_censored") != 2117:
        raise ValueError("STAGE128_STAGE93_FULL_CAUSAL_G1_DENOMINATOR_DRIFT")
    if stage93.get("observed_gt2x_in_source_complete") != 51 or stage93.get("first_D0_early_at_least_5min") != 48:
        raise ValueError("STAGE128_STAGE93_GROSS_WINNERS_DRIFT")
    expected_reason = {"CENSORED_DAILY_1M_GAP": 3,
                       "CENSORED_PUBLISHER_VERIFIED_1H_VS_1M_PRICE_CONFLICT": 47,
                       "CENSORED_STAGE37_HOURLY_SOURCE": 2067,
                       "COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4": 3283}
    if stage93.get("censoring_by_reason") != expected_reason:
        raise ValueError("STAGE128_STAGE93_SOURCE_REASONS_DRIFT")
    summary = Counter()
    by_anchor = defaultdict(Counter)
    exceptions = []
    for row in rows:
        item = classify(row, meta.get(row["symbol"]))
        kind = item["later_metadata_comparison"]
        summary[kind] += 1
        by_anchor[row["date"]][kind] += 1
        if kind in ("HOURLY_INCOMPLETE_LATER_ONBOARD_INSIDE_WINDOW",
                    "HOURLY_COMPLETE_LATER_METADATA_ONBOARD_CONTRADICTION"):
            exceptions.append(item)
    if len(rows) != sum(summary.values()):
        raise ValueError("STAGE128_SOURCE_POPULATION_DROPPED")
    for day in DAYS:
        if sum(by_anchor[day].values()) != 900:
            raise ValueError("STAGE128_DAILY_POPULATION_DROPPED")
    complete = sum(v for k,v in summary.items() if k.startswith("HOURLY_COMPLETE_"))
    missing = sum(v for k,v in summary.items() if k.startswith("HOURLY_INCOMPLETE_"))
    if (complete, missing) != (3333,2067):
        raise ValueError("STAGE128_1H_COMPLETENESS_DRIFT")
    raw_misses = stage93["all_source_complete_2x_case_registry"]
    misses = [{"date":x["date"], "symbol":x["symbol"], "first_watch_class":x["first_watch_class"],
               "first_cross_utc":x["first_real_1m_2x_HIGH_UTC"],
               "first_watch_utc":x["first_original_D0_WATCH_UTC"]}
              for x in raw_misses if x["first_watch_class"] != "EARLY_GE5"]
    expected_misses = {( "2025-04-19","CETUSUSDT","LATE"),
                       ("2025-04-19","PENGUUSDT","NO_WATCH"),
                       ("2025-10-19","FUSDT","SAME_MINUTE")}
    if {(m["date"],m["symbol"],m["first_watch_class"]) for m in misses} != expected_misses:
        raise ValueError("STAGE128_EXPOSED_G1_MISSED_CASES_DRIFT")
    return {
        "schema": SCHEMA,
        "original_source": "STAGE37_5400_ARCHIVED_PUBLISHER_SHA_HOURLY_CENSUS",
        "original_stage37_git_blob": STAGE37_GIT_BLOB,
        "later_metadata_source": "STAGE123_20261014T094824Z_CONNECTED_BINANCE_EXCHANGEINFO",
        "later_metadata_proves_historical_listing": False,
        "current_onboard_not_historical_issuer_or_trading_status": True,
        "original_exposed_symbol_date_attempts": 5400,
        "original_exposed_frozen_900_per_date": 900,
        "stage37_hourly_complete": complete,
        "stage37_hourly_missing": missing,
        "stage93_full_1m_verified": 3283,
        "stage93_full_source_censored": 2117,
        "stage93_censored_1m_hourly_disagree": 47,
        "stage93_censored_1m_gap": 3,
        "stage93_hourly_missing_inherited": 2067,
        "stage93_exposed_gross_2x":51,
        "stage93_exposed_D0_first_early5":48,
        "stage93_exposed_gross_futures_2x_early5_rate":48/51,
        "later_metadata_comparison_counts":dict(sorted(summary.items())),
        "later_metadata_comparison_by_anchor":{d:dict(sorted(by_anchor[d].items())) for d in DAYS},
        "later_listing_boundary_and_source_contradiction_cases":exceptions,
        "original_source_complete_gross2x_not_early_cases":misses,
        "independent_true_crypto_universe_asof": "UNVERIFIED",
        "new_forward_validation_G1":"NOT_SCORABLE",
        "confirmed_listing_eligibility_at_historical_anchor":"UNKNOWN",
        "G0":"PARTIAL", "G4_real_net":"UNKNOWN",
        "stage118_model":"REJECTED_UNCHANGED","stage127_model":"REJECTED_UNCHANGED",
        "other_AI_independent_review":"NOT_DONE",
        "monster_deployment":"NO_GO","frank":"UNCHANGED","gmail":"OFF",
    }


def run():
    snap = load_stage123(STAGE123)
    stage93 = json.loads(STAGE93.read_text(encoding="utf-8"))
    return audit(read_original_stage37(), snap["market"], stage93)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--expect-in-window",type=int)
    args=ap.parse_args()
    result=run()
    within=result["later_metadata_comparison_counts"].get("HOURLY_INCOMPLETE_LATER_ONBOARD_INSIDE_WINDOW",0)
    if args.expect_in_window is not None and within != args.expect_in_window:
        raise ValueError("STAGE128_EXPECTED_IN_WINDOW_RESEARCH_COUNT_DRIFT")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items()
                      if k not in ("later_listing_boundary_and_source_contradiction_cases",
                                   "later_metadata_comparison_by_anchor")},sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
