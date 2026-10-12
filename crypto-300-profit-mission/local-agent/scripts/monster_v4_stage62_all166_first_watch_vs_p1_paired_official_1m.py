#!/usr/bin/env python3
"""Stage62: all166 original D0 and P1, *same core* official 1m 24h price-path logic.

Research-only; first D0 and later P1 are not executable entries. 166 already
exposed P1-qualified cases, NOT all D0 universe and NOT a holdout.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import statistics
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage60_exposed_all166_post_signal_futures_price_paths as m60
except ImportError:
    from scripts import monster_v4_stage60_exposed_all166_post_signal_futures_price_paths as m60

E = Path(__file__).resolve().parents[2] / "monster" / "evidence"
D0 = E / "monster_stage61_original166_firstD0_to_P1_latency_and_24h_proxy.jsonl"
P1 = E / "monster_stage60_all166_signal_to_24h_verified_futures_price_proxy.jsonl"
BLOBS = {
    D0.name: "89634d4b8d049ad607be1f553515d11ff6e82573",
    P1.name: "c76b9b73c11924cb3fdc36fb852074ff9b49b3b8",
    "monster_v4_stage60_exposed_all166_post_signal_futures_price_paths.py": "6a638e84cf837ffc84a301649612e8f2f5dc1deb",
}
GOOD = "COMPLETE_OFFICIAL_DAILY_USDM_1M_PUBLISHER_SHA_PRICE_PATH"
D = Decimal
SCHEMA = "MONSTER_STAGE62_ORIGINAL166_PAIRED_FIRST_D0_AND_P1_REAL_OFFICIAL_USDM_1M_V1"


def blob(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def load():
    for p in (D0, P1, Path(m60.__file__)):
        if blob(p) != BLOBS[p.name]:
            raise ValueError("STAGE62_ORIGINAL_REAL_CORE_OR_SOURCE_CHANGED " + p.name)
    first = [json.loads(x) for x in D0.read_text(encoding="utf-8").splitlines() if x]
    second = [json.loads(x) for x in P1.read_text(encoding="utf-8").splitlines() if x]
    if len(first) != 166 or len(second) != 166:
        raise ValueError("STAGE62_EXPECTED_FULL166")
    pindex = {(r["date"], r["symbol"]): r for r in second}
    if len(pindex) != 166 or len({(r["date"],r["symbol"]) for r in first}) != 166:
        raise ValueError("STAGE62_DUPLICATE_SYMBOL_DATE")
    for row in first:
        p1 = pindex[row["date"],row["symbol"]]
        if (row["first_P1_eligible_UTC"] != p1["eligible_timestamp_UTC"] or
            row["original_P1_delivered_research"] != p1["original_v03_urgent_delivered"] or
            row["posthoc_calendar_high2x_label_ONLY"] != p1["posthoc_calendar2x_label_EVALUATION_ONLY"] or
            p1["source_status"] != GOOD):
            raise ValueError("STAGE62_PAIRED_ORIGINAL_EVENT_TIME_OR_FATE_DRIFT")
    return first,pindex


def calc_case(first,p1,collector=m60.source_case):
    if first["D0_to_P1_wait_minutes"] < 0:
        raise ValueError("STAGE62_NEGATIVE_POLL_DELAY")
    dummy = {
        "date": first["date"], "symbol": first["symbol"],
        "eligible_timestamp_UTC": first["first_D0_watch_reconstructed_UTC"],
        "mode": "FIRST_D0_WATCH",
        "research_delivered": "True" if first["original_P1_delivered_research"] else "False",
        "future_label_AFTER_signal": first["posthoc_calendar_high2x_label_ONLY"],
    }
    old = collector(dummy, {"venue_evidence_status":p1["venue_evidence_status"]})
    if old["source_status"] != GOOD:
        return {
            "date": first["date"], "symbol": first["symbol"],
            "source_status": old["source_status"],
            "earliest_D0_watch_UTC": first["first_D0_watch_reconstructed_UTC"],
            "first_P1_UTC": first["first_P1_eligible_UTC"],
            "D0_SOURCE": old,
            "P1_SOURCE": p1,
            "paired_horizons": None,
        }
    immediate = first["D0_to_P1_wait_minutes"] == 0
    if immediate and (
        old["entry_price_first_post_signal_close_PROXY"] != p1["entry_price_first_post_signal_close_PROXY"] or
        old["forward_horizons"] != p1["forward_horizons"]
    ):
        raise ValueError("STAGE62_SAME_INSTANT_ORIGINAL_FIRST_D0_P1_PRICE_OR_SOURCE_NOT_IDENTICAL")
    first_price = D(old["entry_price_first_post_signal_close_PROXY"])
    p1_price = D(p1["entry_price_first_post_signal_close_PROXY"])
    if first_price <= 0 or p1_price <= 0:
        raise ValueError("STAGE62_INVALID_SOURCE_VERIFIED_CLOSE_PRICE")
    horizons = {}
    for h in m60.HORIZONS:
        k = str(h)
        a = old["forward_horizons"][k]
        q = p1["forward_horizons"][k]
        horizons[k] = {
            "first_D0_forward_close_return_pct_PROXY": a["end_close_return_pct_PROXY"],
            "first_P1_forward_close_return_pct_PROXY": q["end_close_return_pct_PROXY"],
            "first_D0_forward_high_upside_pct_NOT_FILL": a["potential_max_high_pct_NOT_AN_EXIT_FILL"],
            "first_P1_forward_high_upside_pct_NOT_FILL": q["potential_max_high_pct_NOT_AN_EXIT_FILL"],
            "first_D0_forward_low_risk_pct_NOT_FILL": a["adverse_min_low_pct_NOT_AN_EXIT_FILL"],
            "first_P1_forward_low_risk_pct_NOT_FILL": q["adverse_min_low_pct_NOT_AN_EXIT_FILL"],
        }
    return {
        "date": first["date"],"symbol":first["symbol"],
        "source_status": GOOD,
        "earliest_D0_watch_UTC": first["first_D0_watch_reconstructed_UTC"],
        "first_P1_UTC": first["first_P1_eligible_UTC"],
        "D0_to_P1_wait_minutes": first["D0_to_P1_wait_minutes"],
        "original_P1_urgent_delivered": first["original_P1_delivered_research"],
        "original_P1_mode": first["original_P1_mode"],
        "posthoc_calendar2x_label_EVALUATION_ONLY": first["posthoc_calendar_high2x_label_ONLY"],
        "venue_evidence_type": p1["venue_evidence_status"],
        "same_D0_P1_instant_source_price_exact_match": immediate,
        "first_D0_price_PROXY": str(first_price),
        "P1_price_PROXY": str(p1_price),
        "P1_proxy_price_change_since_first_D0_pct_NOT_PNL": str(m60.pct(p1_price,first_price)),
        "first_D0_official_minute_SHA_receipts": old["source_SHA_receipts_for_available_days"],
        "original_P1_official_minute_SHA_receipts": p1["source_SHA_receipts_for_available_days"],
        "paired_horizons": horizons,
        "NO_SPOT_ORDERBOOK_OR_FILL_CLAIM": True,
        "ORDER_NOTIONAL": None,
        "P1V03_REJECTED": True,
    }


def summarize(group):
    valid = [x for x in group if x["source_status"] == GOOD]
    def median(vals):
        return str(statistics.median(vals)) if vals else None
    def feature(h,key):
        return [D(x["paired_horizons"][str(h)][key]) for x in valid]
    metrics = {}
    for h in m60.HORIZONS:
        a = feature(h,"first_D0_forward_close_return_pct_PROXY")
        b = feature(h,"first_P1_forward_close_return_pct_PROXY")
        mha = feature(h,"first_D0_forward_high_upside_pct_NOT_FILL")
        mhb = feature(h,"first_P1_forward_high_upside_pct_NOT_FILL")
        lowa = feature(h,"first_D0_forward_low_risk_pct_NOT_FILL")
        lowb = feature(h,"first_P1_forward_low_risk_pct_NOT_FILL")
        metrics[str(h)] = {
            "D0_close_median_pct_PROXY":median(a),
            "P1_close_median_pct_PROXY":median(b),
            "D0_close_positive_count":sum(v>0 for v in a),
            "P1_close_positive_count":sum(v>0 for v in b),
            "D0_high_at_least_2x_count_NOT_FILL":sum(v>=100 for v in mha),
            "P1_high_at_least_2x_count_NOT_FILL":sum(v>=100 for v in mhb),
            "D0_low_median_pct_NOT_FILL":median(lowa),
            "P1_low_median_pct_NOT_FILL":median(lowb),
        }
    return {
        "n":len(group),"complete":len(valid),
        "missing_source":dict(sorted(__import__("collections").Counter(
            x["source_status"] for x in group if x["source_status"]!=GOOD).items())),
        "D0_to_P1_first_completed_minute_price_change_median_pct_NOT_PNL":
            median([D(x["P1_proxy_price_change_since_first_D0_pct_NOT_PNL"]) for x in valid]),
        "horizons":metrics,
    }


def summary(rows):
    subset={
        "ALL_166":rows,
        "FIRST_D0_EQUALS_P1": [r for r in rows if r["D0_to_P1_wait_minutes"] == 0],
        "SECOND_IGNITION_WITH_DELAY": [r for r in rows if r["D0_to_P1_wait_minutes"] > 0],
        "P1_URGENT_DELIVERED": [r for r in rows if r["original_P1_urgent_delivered"]],
        "P1_URGENT_OVER_BUDGET": [r for r in rows if not r["original_P1_urgent_delivered"]],
    }
    return {
        "schema":SCHEMA,"locked_original_source_blobs":BLOBS,
        "full_exposed_P1_cohort":len(rows),
        "group_results":{name:summarize(xs) for name,xs in subset.items()},
        "first_watch_original_P1_same_minute_source_parity_46":sum(
            x["same_D0_P1_instant_source_price_exact_match"] for x in rows if x["source_status"] == GOOD),
        "NOT_ALL_D0_EVER":True,
        "NOT_A_NEW_MODEL_OR_INDEPENDENT_HOLDOUT":True,
        "MISMATCHED_ENTRY_TIMES_NO_COMPARABLE_EXECUTABLE_PNL":True,
        "NO_ASSUMED_ORDER_NOTIONAL":True,
        "P1V03":"REJECTED","OTHER_AI_REVIEW":"NOT_DONE","DEPLOYMENT":"NO_GO",
        "GMAIL":"OFF","AUTOTRADE":"NO_GO",
    }


def selftest():
    from decimal import Decimal as D
    # Test exact same immutable source core for instant D0/P1, no live network.
    t=m60.asof_ms("2025-10-02T06:00:00Z")
    bars=[(t+i*m60.ONE,D(100),D(100)+D("0.1"),D(99),D(100),D(100),10)
          for i in range(1440)]
    entry,qs=m60.evaluate_bars(bars)
    fake_p1 = {
       "date":"2025-10-02","symbol":"TESTUSDT",
       "eligible_timestamp_UTC":"2025-10-02T06:00:00Z",
       "source_status":GOOD,"original_v03_urgent_delivered":True,
       "posthoc_calendar2x_label_EVALUATION_ONLY":"ORDINARY_NOT_CALENDAR_2X",
       "venue_evidence_status":"UNKNOWN_ALTERNATIVE_VENUE_NOT_CHECKED",
       "entry_price_first_post_signal_close_PROXY":str(entry),
       "forward_horizons":qs,
       "source_SHA_receipts_for_available_days":[{"source":"synthetic"}],
    }
    def fake(_row,_venue):
        return dict(fake_p1,source_SHA_receipts_for_available_days=[{"source":"synthetic"}])
    first = {
       "date":"2025-10-02","symbol":"TESTUSDT",
       "D0_to_P1_wait_minutes":0,
       "first_D0_watch_reconstructed_UTC":"2025-10-02T06:00:00Z",
       "first_P1_eligible_UTC":"2025-10-02T06:00:00Z",
       "original_P1_delivered_research":True,
       "original_P1_mode":"FIRST_D0_IMMEDIATE",
       "posthoc_calendar_high2x_label_ONLY":"ORDINARY_NOT_CALENDAR_2X",
    }
    out=calc_case(first,fake_p1,collector=fake)
    assert out["same_D0_P1_instant_source_price_exact_match"]
    assert summary([out])["group_results"]["ALL_166"]["horizons"]["1440"]["D0_close_median_pct_PROXY"]=="0"
    def mismatched(r,v):
        d=fake(r,v)
        d["entry_price_first_post_signal_close_PROXY"]="99"
        return d
    try:
        calc_case(first,fake_p1,collector=mismatched)
    except ValueError as e:
        assert "NOT_IDENTICAL" in str(e)
    else:
        raise AssertionError("STAGE62_EXACT_SAME_MINUTE_PARITY_NOT_ENFORCED")
    print("STAGE62_SAME_ORIGINAL_24H_MODEL_INSTANT_D0_P1_SOURCE_PARITY_TEST_PASS")


def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--selftest",action="store_true")
    arg.add_argument("--out",type=Path)
    arg.add_argument("--workers",type=int,default=6)
    args=arg.parse_args()
    if args.selftest:selftest();return
    if args.out is None or not 1<=args.workers<=8:arg.error("--out and workers 1..8 required")
    first,after=load()
    rows=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(calc_case,item,after[(item["date"],item["symbol"])]):item for item in first}
        for job in concurrent.futures.as_completed(futures):
            item=futures[job]
            try:rows.append(job.result())
            except Exception as e:
                errors.append({"date":item["date"],"symbol":item["symbol"],
                               "error":type(e).__name__+":"+str(e)[:180]})
            if (len(rows)+len(errors))%20==0:
                print("STAGE62_PAIRED_SOURCE_PROGRESS "+json.dumps({"seen":len(rows)+len(errors),
                                                                   "errors":len(errors)}),flush=True)
    if errors or len(rows)!=166:
        raise RuntimeError("STAGE62_SOURCE_HARD_FAIL "+json.dumps(errors[:25]))
    rows.sort(key=lambda r:(r["date"],r["symbol"]))
    result=summary(rows)
    if result["first_watch_original_P1_same_minute_source_parity_46"]!=46:
        raise ValueError("STAGE62_ORIGINAL46_FIRST_WATCH_PARITY_FAILED")
    if result["group_results"]["ALL_166"]["complete"]!=166:
        raise ValueError("STAGE62_EVIDENCE_INCOMPLETE_NEVER_MARK_PASS")
    if (result["group_results"]["ALL_166"]["horizons"]["1440"]["P1_close_median_pct_PROXY"]
        != "-5.580014270149856168106132745"):
        raise ValueError("STAGE62_STAGE60_ORIGINAL_P1_RESULT_CHANGED")
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"monster_stage62_all166_first_D0_vs_P1_official_24h_pair_source_SHA.jsonl").write_text(
        "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
    (args.out/"monster_stage62_all166_D0_vs_P1_paired_price_path_summary.json").write_text(
        json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print("STAGE62_SOURCE_SHA_PAIRED_ALL166_FUTURES_D0_P1_PRICE_PATHS "+
          json.dumps({"n":len(rows),"matched_at_first":result["first_watch_original_P1_same_minute_source_parity_46"]},sort_keys=True))


if __name__=="__main__":
    main()
