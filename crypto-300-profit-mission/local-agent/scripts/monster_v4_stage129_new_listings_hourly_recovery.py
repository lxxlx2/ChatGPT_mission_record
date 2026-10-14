#!/usr/bin/env python3
"""Research-only offline 31 historic partial-window Binance USD-M 1h source audit.

Never a G1 full-week discovery pass, net profit, or verified crypto issuer.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

from monster_v4_stage124_manual_snapshot_comparison import load as stage123_load

E = Path(__file__).resolve().parents[2] / "monster" / "evidence"
CASE_FILE = E/"monster_stage128_31_later_listings_and_15_historical_clock_conflicts.json"
MANIFEST = E/"monster_stage123_20261014T094824Z_manifest.json"
DAYS = ("2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19")
SHARDS = [E/("monster_stage129_"+d.replace("-","")+"_fixed_listing_candidate_usdm_1h_source.json") for d in DAYS]
SCHEMA = "MONSTER_STAGE129_COMPLETE_FROZEN31_HISTORICAL_PARTIAL_WINDOW_HOURLY_DIAGNOSTIC_V1"
ONE_HOUR = 3600000


def dec(x):
    try:
        v=Decimal(str(x))
    except (InvalidOperation,ValueError,TypeError):
        raise ValueError("STAGE129_INVALID_NUMERIC")
    if not v.is_finite():
        raise ValueError("STAGE129_NONFINITE_NUMERIC")
    return v


def window(day):
    if day not in DAYS:
        raise ValueError("STAGE129_BAD_ORIGINAL_ANCHOR")
    start=int(datetime.fromisoformat(day+"T06:00:00+00:00").timestamp()*1000)
    return start,start+168*ONE_HOUR


def utc(ms):
    return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat().replace("+00:00","Z")


def assess_one(record, expected):
    if record.get("anchor") != expected["anchor"] or record.get("symbol") != expected["symbol"]:
        raise ValueError("STAGE129_WRONG_CASE_IDENTITY")
    start,end=window(record["anchor"])
    q=record.get("request")
    if not isinstance(q,dict) or q != {"symbol":record["symbol"],"interval":"1h","startTime":start,"endTime":end-1,"limit":500}:
        raise ValueError("STAGE129_REQUEST_WAS_NOT_FROZEN")
    rows=record.get("raw_structured_klines")
    outcome={
        "date":record["anchor"], "symbol":record["symbol"],
        "later_onboard_utc":expected["later_onboard_utc"],
        "connected_source_not_raw_http_or_publisher_checksum":True,
        "source_status":record.get("source_status"),
        "bar_count":None, "first_1h_open_utc":None, "last_1h_open_utc":None,
        "first_open_USDT":None,"max_high_USDT":None,"max_high_hour_utc":None,
        "gross_max_high_multiple_from_first_observed_hour":None,
        "gte_2x_gross_firsthour_proxy":None,
        "gte_5x_gross_firsthour_proxy":None,
        "gte_10x_gross_firsthour_proxy":None,
        "full_week_anchor_open_2x_G1":"NOT_COMPARABLE_NEW_LISTING",
        "first_D0_early5":"NOT_SCORABLE_FROM_HOURLY",
        "actual_executable_net":"UNKNOWN",
        "historical_crypto_identity_proof":"UNVERIFIED",
    }
    if record.get("source_status")!="OBSERVED_ARRAY" or rows is None:
        outcome["analysis_status"]="UNAVAILABLE_NOT_A_NEGATIVE"
        return outcome
    if not isinstance(rows,list) or not rows:
        outcome["analysis_status"]="EMPTY_SOURCE_NOT_A_NEGATIVE"
        return outcome
    checked=[]
    for raw in rows:
        if not isinstance(raw,list) or len(raw)!=12 or type(raw[0]) is not int:
            raise ValueError("STAGE129_INVALID_BINANCE_1H_ARRAY")
        t=raw[0]
        if t<start or t>=end or t%ONE_HOUR:
            raise ValueError("STAGE129_SOURCE_TIME_OUTSIDE_FROZEN_HOUR")
        op,high,low,close=[dec(raw[i]) for i in (1,2,3,4)]
        if min(op,high,low,close)<=0 or high <max(op,close) or low>min(op,close) or high<low:
            raise ValueError("STAGE129_SOURCE_OHLC_INVALID")
        checked.append((t,op,high,low,close))
    if len({row[0] for row in checked})!=len(checked) or checked != sorted(checked,key=lambda z:z[0]):
        raise ValueError("STAGE129_DUPLICATE_OR_UNORDERED_BARS")
    has_gap=any(checked[i][0]-checked[i-1][0]!=ONE_HOUR for i in range(1,len(checked)))
    first,last=checked[0][0],checked[-1][0]
    expected_later=int(datetime.fromisoformat(expected["later_onboard_utc"].replace("Z","+00:00")).timestamp()*1000)
    match_later_hour=(first==(expected_later//ONE_HOUR)*ONE_HOUR)
    baseline=checked[0][1]
    max_hour=max(checked,key=lambda z:z[2])
    ratio=max_hour[2]/baseline
    outcome.update({
        "bar_count":len(checked),
        "first_1h_open_utc":utc(first),"last_1h_open_utc":utc(last),
        "later_onboard_floor_hour_matches_first_returned":match_later_hour,
        "first_open_USDT":str(baseline),
        "max_high_USDT":str(max_hour[2]),
        "max_high_hour_utc":utc(max_hour[0]),
        "hourly_gap_count":sum(checked[i][0]-checked[i-1][0]!=ONE_HOUR for i in range(1,len(checked))),
        "full_168h_from_original_anchor":len(checked)==168 and first==start,
        "observed_partial_listing_window_is_contiguous_to_end":not has_gap and last==end-ONE_HOUR,
    })
    if has_gap or last!=end-ONE_HOUR:
        outcome["analysis_status"]="CENSORED_PARTIAL_AFTER_FIRST_OBSERVED_1H"
        return outcome
    outcome.update({
        "analysis_status":"COMPLETE_FROM_FIRST_OBSERVED_1H_TO_END_PRICE_PROXY_ONLY",
        "gross_max_high_multiple_from_first_observed_hour":str(ratio),
        "gte_2x_gross_firsthour_proxy":ratio>=2,
        "gte_5x_gross_firsthour_proxy":ratio>=5,
        "gte_10x_gross_firsthour_proxy":ratio>=10,
    })
    return outcome


def analyze(shards,exceptions,metadata):
    cases=[x for x in exceptions["cases"] if x["category"]=="IN_WINDOW_LATER_ONBOARD_NOT_HISTORICALLY_PROVEN"]
    if len(cases)!=31 or len({(x["anchor"],x["symbol"]) for x in cases})!=31:
        raise ValueError("STAGE129_EXPECT_ORIGINAL_31_FROZEN_LISTING_CASES")
    expected={(x["anchor"],x["symbol"]):x for x in cases}
    seen=set()
    out=[]
    for d in DAYS:
        item=shards.get(d)
        if not isinstance(item,dict) or item.get("anchor")!=d or item.get("schema")!="MONSTER_STAGE129_31_FROZEN_EXPOSED_HISTORICAL_USDM_ONEH_SHARD_V1":
            raise ValueError("STAGE129_ARCHIVED_RAW_SOURCE_SHARD_WRONG")
        a,b=window(d)
        if item.get("utc_start_ms")!=a or item.get("utc_end_inclusive_ms")!=b-1:
            raise ValueError("STAGE129_ARCHIVED_SOURCE_WINDOW_NOT_FROZEN")
        if len(item.get("source_replies",[]))!=item.get("expected_original_cohort"):
            raise ValueError("STAGE129_INCOMPLETE_COHORT_REPLY_FILE")
        for record in item["source_replies"]:
            key=(record.get("anchor"),record.get("symbol"))
            if key not in expected or key in seen:
                raise ValueError("STAGE129_SOURCE_NOT_FROZEN_31_OR_DUPLICATE")
            seen.add(key)
            result=assess_one(record,expected[key])
            meta=metadata.get(record["symbol"])
            result["later_exchange_claim_underlyingType"]=meta.get("underlyingType") if meta else None
            result["later_exchange_claim_underlyingSubType"]=meta.get("underlyingSubType") if meta else None
            result["exchange_label_proves_issuer_identity"]=False
            out.append(result)
    if seen != set(expected):
        raise ValueError("STAGE129_SOME_OF_THE_31_MISSING")
    outcome=Counter(x["analysis_status"] for x in out)
    count2=sum(x["gte_2x_gross_firsthour_proxy"] is True for x in out)
    count5=sum(x["gte_5x_gross_firsthour_proxy"] is True for x in out)
    count10=sum(x["gte_10x_gross_firsthour_proxy"] is True for x in out)
    return {
        "schema":SCHEMA,"source":"BINANCE_USDM_HISTORICAL_1H_CONNECTED_STRUCTURED_NOT_PUBLISHER_SHA",
        "frozen_case_count":31, "response_count":len(out),
        "source_status_counts":dict(sorted(outcome.items())),
        "gross_first_observed_hour_to_later_high_at_least_2x_cases":count2,
        "gross_first_observed_hour_to_later_high_at_least_5x_cases":count5,
        "gross_first_observed_hour_to_later_high_at_least_10x_cases":count10,
        "hourly_1h_peak_not_one_minute_first_cross_or_execution":True,
        "old_Stage93_51_gt2x_denominator_not_changed":True,
        "real_new_G1_crypto_full_market":"NOT_SCORABLE",
        "G0":"PARTIAL","G4_real_net":"UNKNOWN",
        "old_stage118":"REJECTED","old_stage127":"REJECTED",
        "independent_other_AI_review":"NOT_DONE",
        "monster_deployment":"NO_GO","frank":"UNCHANGED",
        "all_source_cohort_rows":sorted(out,key=lambda r:(r["date"],r["symbol"])),
    }


def run():
    shards={}
    for day,path in zip(DAYS,SHARDS):
        shards[day]=json.loads(path.read_text(encoding="utf-8"))
    exceptions=json.loads(CASE_FILE.read_text(encoding="utf-8"))
    market=stage123_load(MANIFEST)["market"]
    return analyze(shards,exceptions,market)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--expect-source-count",type=int,default=None)
    a=ap.parse_args()
    result=run()
    if a.expect_source_count is not None and result["response_count"]!=a.expect_source_count:
        raise ValueError("STAGE129_FROZEN_31_COUNT_DRIFT")
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="all_source_cohort_rows"},ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
