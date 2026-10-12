#!/usr/bin/env python3
"""Stage63: FULL original all-market D0 WATCH (not P1-survivor conditioned).

Uses original Stage52 source-locked 5400 instrument dates; 519 original first
D0 WATCH; all 166 P1 survivors must exactly equal Stage62 first D0 prices and
four post-signal horizons. Exactly the unchanged Stage60 verified USD-M core.
Research-only, exposed case histories, no buyer claims, no order size, no deploy.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import hashlib
import json
import statistics
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage60_exposed_all166_post_signal_futures_price_paths as m60
except ImportError:
    from scripts import monster_v4_stage60_exposed_all166_post_signal_futures_price_paths as m60

E = Path(__file__).resolve().parents[2] / "monster" / "evidence"
ALL = E / "monster_stage52_all5400_originalV4_P1v03_true_minute_source_cases.jsonl"
MARKET = E / "monster_stage52_pinned_v03_all5400_36SHA_true_global_cap_metrics.json"
PAIRS = E / "monster_stage62_all166_first_D0_vs_P1_official_24h_pair_source_SHA.jsonl"
LOCK = {
    ALL.name: "ad7544f97e8a0d6c1f2635aa54052cca42d08cf1",
    MARKET.name: "42d455a6cc9d0164a8dd94aa12a475bad5ed126e",
    PAIRS.name: "962b1ae289aa0af3f612499e169a686fc63645a1",
    "monster_v4_stage60_exposed_all166_post_signal_futures_price_paths.py": "6a638e84cf837ffc84a301649612e8f2f5dc1deb",
}
GOOD = "COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
PRICE_OK = m60.GOOD
SCHEMA = "MONSTER_STAGE63_ALL519_ORIGINAL_FULLMARKET_D0_WATCH_SHA_PAIRED166_V1"
D = Decimal
DAYS = ("2025-01-30", "2025-06-02", "2025-08-01", "2025-10-02", "2026-06-21", "2026-07-28")
EXPECTED_DATE_WATCH = (161, 34, 54, 75, 100, 95)
H = (15, 60, 360, 1440)


def blob(path):
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def freeze():
    for p in (ALL, MARKET, PAIRS, Path(m60.__file__)):
        if blob(p) != LOCK[p.name]:
            raise ValueError("STAGE63_FROZEN_ORIGINAL_GIT_BLOB_DRIFT " + p.name)
    with ALL.open(encoding="utf-8") as f:
        original = [json.loads(line) for line in f if line.strip()]
    with PAIRS.open(encoding="utf-8") as f:
        paired = [json.loads(line) for line in f if line.strip()]
    market = json.loads(MARKET.read_text(encoding="utf-8"))
    if len(original)!=5400 or len(paired)!=166 or market["attempted"]!=5400 or market["publisher_1h_and_1m_valid"]!=3377:
        raise ValueError("STAGE63_NOT_ORIGINAL_5400_OR_166")
    keys={(r["date"],r["symbol"]) for r in original}
    if len(keys)!=5400 or any(sum(1 for r in original if r["date"]==d)!=900 for d in DAYS):
        raise ValueError("STAGE63_ORIGINAL_FULL_MARKET_KEY_DRIFT")
    original_watch=[]
    original_P1=[]
    for r in original:
        if r["source_status"]!=GOOD:
            if r.get("WATCH_UTC") or r.get("p1v03_eligible_unbudgeted") is not None:
                raise ValueError("STAGE63_CENSORED_ORIGINAL_CONTAINS_V4_SIGNALS")
            continue
        if r["WATCH_UTC"]:
            original_watch.append(r)
        if r["p1v03_eligible_unbudgeted"] is not None:
            original_P1.append(r)
    counts=[sum(r["date"]==d for r in original_watch) for d in DAYS]
    if (len(original_watch),len(original_P1),counts)!=(519,166,list(EXPECTED_DATE_WATCH)):
        raise ValueError("STAGE63_ORIGINAL_V4_WATCH_COUNT_OR_P1_DRIFT " + str(counts))
    mcounts=[x["D0_watch_coin_dates"] for x in market["all_date_stats"]]
    if mcounts!=counts:
        raise ValueError("STAGE63_ORIGINAL_STAGE52_WATCH_SUMMARY_DRIFT")
    bypair={(x["date"],x["symbol"]):x for x in paired}
    if len(bypair)!=166:
        raise ValueError("STAGE63_166_PAIRED_KEYS_INVALID")
    byp1={(x["date"],x["symbol"]) for x in original_P1}
    if set(bypair)!=byp1:
        raise ValueError("STAGE63_P1_SURVIVORS_NOT_ALL_ORIGINAL166")
    for row in original_watch:
        key=row["date"],row["symbol"]
        if key in bypair and row["WATCH_UTC"][0]!=bypair[key]["earliest_D0_watch_UTC"]:
            raise ValueError("STAGE63_ORIGINAL_FIRST_WATCH_NOT_PAIRED166 " + str(key))
    return original_watch, bypair


def real_source_case(row, survivor, collector=m60.source_case):
    first=row["WATCH_UTC"][0]
    origin=m60.asof_ms(row["date"]+"T06:00:00Z")
    t=m60.asof_ms(first)
    if t<origin or t>=origin+7*86400000 or (t-origin)%180000:
        raise ValueError("STAGE63_D0_WATCH_NOT_IN_3MIN_CAUSAL_REPLAY")
    c=row["p1v03_eligible_unbudgeted"]
    reached=c is not None
    if reached!=bool(survivor):
        raise ValueError("STAGE63_P1_FULLMARKET_AND_166_SUBCOHORT_IDENTITY_WRONG")
    if reached and m60.asof_ms(c["at_UTC"])<t:
        raise ValueError("STAGE63_P1_ELIGIBLE_BEFORE_FIRST_D0")
    for x in row["source_daily_minute_official_SHA"]:
        if not x["verified_official_publisher_SHA256"]:
            raise ValueError("STAGE63_ORIGINAL_STAGE52_PUBLISHER_DAILY_SHA_UNVERIFIED")
    temp={
        "date":row["date"],"symbol":row["symbol"],
        "eligible_timestamp_UTC":first,"mode":"FIRST_ORIGINAL_D0_WATCH",
        "research_delivered":"False",
        "future_label_AFTER_signal":"ORIGINAL_GT2X_HISTORIC_EVALUATION_ONLY",
    }
    # Venue eligibility was never checked for all 519, label UNKNOWN not FILL.
    case=collector(temp,{"venue_evidence_status":"NOT_A_SPOT_EXECUTION_TEST"})
    if case["source_status"]!=PRICE_OK:
        return {
            "date":row["date"],"symbol":row["symbol"],"first_D0_watch_UTC":first,
            "source_status":case["source_status"],
            "historical_calendar_2x_EVALUATION_ONLY":bool(row["hourly_gt2x"]),
            "historical_calendar_5x_EVALUATION_ONLY":bool(row["hourly_gt5x"]),
            "reached_P1_historically":reached,"D0_price_path":None,
            "source_receipts_for_available_days":case.get("source_SHA_receipts_for_available_days"),
            "CENSORED_SOURCE_DETAILS":case,
        }
    receipts=case["source_SHA_receipts_for_available_days"]
    src_by_date={x["date"]:x["zip_sha256"] for x in row["source_daily_minute_official_SHA"]}
    # Stage52's nine official days include one warmup and do NOT cover the
    # after-window 24h follow-up for original D0 signals on the last UTC06 day.
    # New extra-day official ZIPs are valid ONLY with independently verified
    # publisher SHA, are explicitly isolated from the original Stage52 proofs,
    # and cannot silently overwrite a pinned original-day ZIP.
    extra_days=[]
    for receipt in receipts:
        verified=receipt["verified_official_publisher_SHA256"]
        if not verified:
            raise ValueError("STAGE63_UNVERIFIED_PUBLISHER_SHA")
        expect=src_by_date.get(receipt["date"])
        if expect is not None:
            if expect!=receipt["zip_sha256"]:
                raise ValueError("STAGE63_RELOADED_OFFICIAL_SOURCE_DISAGREES_STAGE52_ORIGINAL_36_SHA " + str((row["date"],row["symbol"],receipt["date"])))
        else:
            allowed=(datetime.fromisoformat(row["date"]).date()+timedelta(days=8)).isoformat()
            if receipt["date"]!=allowed:
                raise ValueError("STAGE63_UNEXPECTED_EXTRA_DAY_OUTSIDE_ORIGINAL_SOURCES " + str((row["date"],row["symbol"],receipt["date"])))
            extra_days.append(receipt)
    if reached:
        prior=survivor
        if prior["source_status"]!=PRICE_OK or prior["earliest_D0_watch_UTC"]!=first:
            raise ValueError("STAGE63_SURVIVOR_SOURCE_OR_EVENT_IDENTITY_DRIFT")
        if case["entry_price_first_post_signal_close_PROXY"]!=prior["first_D0_price_PROXY"]:
            raise ValueError("STAGE63_FIRST_D0_PRICE_PARITY_166_FAIL")
        for h in H:
            horizon=case["forward_horizons"][str(h)]
            old=prior["paired_horizons"][str(h)]
            fields={
                "end_close_return_pct_PROXY":"first_D0_forward_close_return_pct_PROXY",
                "potential_max_high_pct_NOT_AN_EXIT_FILL":"first_D0_forward_high_upside_pct_NOT_FILL",
                "adverse_min_low_pct_NOT_AN_EXIT_FILL":"first_D0_forward_low_risk_pct_NOT_FILL",
            }
            for field, oldfield in fields.items():
                if horizon[field]!=old[oldfield]:
                    raise ValueError("STAGE63_166_PRICE_PATH_PARITY_FAIL "+str((row["date"],row["symbol"],h,field)))
        if receipts!=prior["first_D0_official_minute_SHA_receipts"]:
            raise ValueError("STAGE63_166_PUBLISHER_SHA_RECEIPT_PARITY_FAIL")
    return {
        "date":row["date"],"symbol":row["symbol"],
        "first_D0_watch_UTC":first,
        "source_status":PRICE_OK,
        "historical_calendar_2x_EVALUATION_ONLY":bool(row["hourly_gt2x"]),
        "historical_calendar_5x_EVALUATION_ONLY":bool(row["hourly_gt5x"]),
        "historical_calendar_10x_EVALUATION_ONLY":bool(row["hourly_gt10x"]),
        "reached_P1_historically":reached,
        "P1_eligible_UTC_if_any":c["at_UTC"] if c else None,
        "first_D0_price_PROXY":case["entry_price_first_post_signal_close_PROXY"],
        "D0_price_path":case["forward_horizons"],
        "official_USDM_1m_publisher_SHA_receipts":receipts,
        "new_publisher_SHA_days_outside_original_Stage52_36_artifacts":extra_days,
        "original_P1_survivor_independent_166_parity":True if reached else None,
        "NOT_SPOT_EXECUTION_PROOF":True,"USER_ORDER_NOTIONAL":None,
        "NOT_RECOMPUTED_V4_OR_P1":True,
    }


def summarize(group):
    good=[x for x in group if x["source_status"]==PRICE_OK]
    def stats(h):
        s=str(h)
        close=[D(x["D0_price_path"][s]["end_close_return_pct_PROXY"]) for x in good]
        mfe=[D(x["D0_price_path"][s]["potential_max_high_pct_NOT_AN_EXIT_FILL"]) for x in good]
        mae=[D(x["D0_price_path"][s]["adverse_min_low_pct_NOT_AN_EXIT_FILL"]) for x in good]
        return {
            "complete":len(close),
            "terminal_close_positive_count":sum(v>0 for v in close),
            "terminal_close_return_pct_median_PROXY":str(statistics.median(close)) if close else None,
            "futures_high_upside_pct_median_NOT_FILL":str(statistics.median(mfe)) if mfe else None,
            "futures_low_adverse_pct_median_NOT_FILL":str(statistics.median(mae)) if mae else None,
            "futures_high_at_least_2x_from_first_D0_proxy_NOT_FILL":sum(x>=100 for x in mfe),
        }
    return {
        "n":len(group),"complete":len(good),
        "censored_by_status":dict(sorted(collections.Counter(x["source_status"] for x in group if x["source_status"]!=PRICE_OK).items())),
        "horizons":{str(h):stats(h) for h in H},
    }


def aggregate(rows):
    groups={
        "ALL_ORIGINAL_519_D0_WATCH":rows,
        "REACHED_P1_SURVIVOR_166":[r for r in rows if r["reached_P1_historically"]],
        "NEVER_REACHED_P1_353":[r for r in rows if not r["reached_P1_historically"]],
        "HISTORICAL_7DAY_CALENDAR_2X_EVAL_ONLY":[r for r in rows if r["historical_calendar_2x_EVALUATION_ONLY"]],
        "ORDINARY_NO_CALENDAR_2X_EVAL_ONLY":[r for r in rows if not r["historical_calendar_2x_EVALUATION_ONLY"]],
    }
    for day in DAYS:
        groups["DAY_"+day]=[r for r in rows if r["date"]==day]
    totals={k:summarize(v) for k,v in groups.items()}
    return {
        "schema":SCHEMA,"frozen_original_source_blobs":LOCK,
        "counts":{
            "original_all_market_attempted":5400,"original_valid_1h_and_1m":3377,
            "original_D0_coin_dates":len(rows),
            "P1_survivors":len(groups["REACHED_P1_SURVIVOR_166"]),
            "D0_without_P1":len(groups["NEVER_REACHED_P1_353"]),
            "original_166_paired_source_price_and_SHA_matches":sum(r.get("original_P1_survivor_independent_166_parity")==True for r in rows),
        },
        "groups":totals,
        "extended_post_original_window_candidates_with_new_publisher_SHA":sum(bool(r.get("new_publisher_SHA_days_outside_original_Stage52_36_artifacts")) for r in rows),
        "extended_post_original_window_is_separately_proved_not_old_stage52_source":True,
        "HISTORICAL_SOURCE_NOT_HOLDOUT":True,
        "P1_V03":"REJECTED","NO_ASSUMED_ORDER_SIZE":True,
        "ALL_PRICE_IS_USDM_FUTURES_NOT_REAL_SPOT_OR_ALPHA_FILL":True,
        "NEW_MODEL_AND_PROFIT_REPLAY":"NOT_DONE",
        "OTHER_AI_REVIEW":"NOT_DONE","MONSTER_DEPLOY":"NO_GO",
        "GMAIL":"OFF","AUTOTRADE":"NO_GO",
    }


def selftest():
    class Source:
        def __call__(self, dummy, venue):
            if venue["venue_evidence_status"]!="NOT_A_SPOT_EXECUTION_TEST":
                raise AssertionError("Unexpected venue")
            return {
                "source_status":PRICE_OK,
                "entry_price_first_post_signal_close_PROXY":"100",
                "forward_horizons":{str(h):{
                    "end_close_return_pct_PROXY":"3",
                    "potential_max_high_pct_NOT_AN_EXIT_FILL":"5",
                    "adverse_min_low_pct_NOT_AN_EXIT_FILL":"-2",
                } for h in H},
                "source_SHA_receipts_for_available_days":[{
                    "date":"2025-01-30","zip_sha256":"a"*64,
                    "verified_official_publisher_SHA256":True,
                }],
            }
    row={
        "date":"2025-01-30","symbol":"TESTUSDT",
        "source_daily_minute_official_SHA":[{
            "date":"2025-01-30","zip_sha256":"a"*64,
            "verified_official_publisher_SHA256":True,
        }],
        "WATCH_UTC":["2025-01-30T06:00:00Z"],
        "p1v03_eligible_unbudgeted":None,
        "hourly_gt2x":False,"hourly_gt5x":False,"hourly_gt10x":False,
    }
    x=real_source_case(row,None,Source())
    assert x["source_status"]==PRICE_OK and x["reached_P1_historically"]==False
    assert summarize([x])["horizons"]["1440"]["terminal_close_return_pct_median_PROXY"]=="3"
    try:
        real_source_case(dict(row,source_daily_minute_official_SHA=[dict(row["source_daily_minute_official_SHA"][0],zip_sha256="b"*64)]),None,Source())
    except ValueError as e:
        assert "DISAGREES_STAGE52" in str(e)
    else:
        raise AssertionError("STAGE63_ORIGINAL_PUBLISHER_SHA_NOT_ENFORCED")
    # A missing Stage52 proof is acceptable ONLY for date+8 extension,
    # after independently verifying the new publisher .CHECKSUM.
    extra=dict(row,source_daily_minute_official_SHA=row["source_daily_minute_official_SHA"])
    class ExtraSource:
        def __call__(self,dummy,venue):
            q=Source()(dummy,venue)
            q["source_SHA_receipts_for_available_days"]=q["source_SHA_receipts_for_available_days"] + [{
                "date":"2025-02-07","zip_sha256":"c"*64,"verified_official_publisher_SHA256":True
            }]
            return q
    assert len(real_source_case(extra,None,ExtraSource())[
        "new_publisher_SHA_days_outside_original_Stage52_36_artifacts"]) == 1
    class InvalidExtra:
        def __call__(self,dummy,venue):
            q=ExtraSource()(dummy,venue)
            q["source_SHA_receipts_for_available_days"][-1]["date"]="2025-02-08"
            return q
    try:
        real_source_case(extra,None,InvalidExtra())
    except ValueError as e:
        assert "UNEXPECTED_EXTRA_DAY" in str(e)
    else:
        raise AssertionError("STAGE63_EXTRA_DAY_UNBOUNDED")
    print("STAGE63_P1_NONSURVIVOR_SOURCE_SHA_AND_FULL519_SELECTION_SELFTEST_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest",action="store_true")
    ap.add_argument("--out",type=Path)
    ap.add_argument("--workers",type=int,default=7)
    x=ap.parse_args()
    if x.selftest:selftest();return
    if not x.out or x.workers not in range(1,9):
        ap.error("--out and 1..8 workers required")
    market,old=freeze()
    output=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=x.workers) as pool:
        futures={pool.submit(real_source_case,r,old.get((r["date"],r["symbol"]))):r for r in market}
        for future in concurrent.futures.as_completed(futures):
            row=futures[future]
            try:output.append(future.result())
            except Exception as e:
                errors.append({"date":row["date"],"symbol":row["symbol"],"error":type(e).__name__+":"+str(e)[:260]})
            if (len(output)+len(errors))%35==0:
                print("STAGE63_ORIGINAL_FULLMARKET_D0_REDOWNLOAD_PROGRESS "+json.dumps({
                    "done":len(output)+len(errors),"errors":len(errors),
                    "complete":sum(z["source_status"]==PRICE_OK for z in output)},sort_keys=True),flush=True)
    if errors or len(output)!=519:
        raise RuntimeError("STAGE63_SOURCE_FAIL_NO_SUCCESS_CLAIM "+json.dumps(errors[:40],sort_keys=True))
    output.sort(key=lambda a:(a["date"],a["symbol"]))
    summary=aggregate(output)
    if (summary["counts"]["P1_survivors"],summary["counts"]["D0_without_P1"],
        summary["counts"]["original_166_paired_source_price_and_SHA_matches"])!=(166,353,166):
        raise ValueError("STAGE63_NON_SURVIVOR_COUNTS_OR_INDEPENDENT166_PARITY_FAILED")
    if summary["groups"]["ALL_ORIGINAL_519_D0_WATCH"]["complete"]!=519:
        raise ValueError("STAGE63_INCOMPLETE_D0_STUDY_MARKED_FAIL_NEEDS_EXPLICIT_CENSORED_REPORT")
    x.out.mkdir(parents=True,exist_ok=True)
    (x.out/"monster_stage63_all519_original_D0_full_market_official_SHA_paths.jsonl").write_text(
        "".join(json.dumps(q,sort_keys=True,ensure_ascii=False)+"\n" for q in output),encoding="utf-8")
    (x.out/"monster_stage63_all519_D0_and_nonP1_353_summary.json").write_text(
        json.dumps(summary,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("STAGE63_OFFICIAL_519_FIRST_D0_24H_RESULTS "+json.dumps({
        "all":summary["groups"]["ALL_ORIGINAL_519_D0_WATCH"]["horizons"]["1440"],
        "never_P1":summary["groups"]["NEVER_REACHED_P1_353"]["horizons"]["1440"],
        "source_166_match":summary["counts"]["original_166_paired_source_price_and_SHA_matches"]
    },sort_keys=True))


if __name__=="__main__":
    main()
