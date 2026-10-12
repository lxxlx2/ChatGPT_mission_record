#!/usr/bin/env python3
"""Monster Stage64: all 519 first D0 original as-of completed 61m USD-M features.

Reuses Stage56 official daily ZIP publisher SHA loader. 519 original D0
timestamps and stage52 provenance pinned, plus 46 independently frozen
immediate-P1 exact feature parity. No future label in rule/selection.
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
    import monster_v4_stage56_usdm_asof_taker_and_tradecount_source_audit as m56
except ImportError:
    from scripts import monster_v4_stage56_usdm_asof_taker_and_tradecount_source_audit as m56

E = Path(__file__).resolve().parents[2] / "monster" / "evidence"
D0 = E / "monster_stage63_all519_original_D0_full_market_official_SHA_paths.jsonl"
ORIG = E / "monster_stage52_all5400_originalV4_P1v03_true_minute_source_cases.jsonl"
P1 = E / "monster_stage56_all166_61m_asof_taker_trades_official_SHA.jsonl"
LOCK = {
    D0.name: "f4bd1de72ecb416fc9aa1593afdac5c67aa46d8b",
    ORIG.name: "ad7544f97e8a0d6c1f2635aa54052cca42d08cf1",
    P1.name: "982bddbf05f263423f9cab4f40c0992688cc3499",
    "monster_v4_stage56_usdm_asof_taker_and_tradecount_source_audit.py": "1a0beaf153d4e6913f1c62fb12b0960894491c80",
}
SCHEMA = "MONSTER_STAGE64_FULL519_FIRST_D0_OFFICIAL_ASOF_61MIN_USDM_TAKER_TRADE_COUNT_V1"
D=Decimal
MIN=60000
GOOD="COMPLETE_OFFICIAL_DAILY_USDM_61M_PUBLISHER_SHA_NO_FUTURE"


def blob(path):
    raw=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def freeze():
    for path in (D0,ORIG,P1,Path(m56.__file__)):
        if blob(path)!=LOCK[path.name]:
            raise ValueError("STAGE64_FROZEN_SOURCE_BLOB_CHANGED "+path.name)
    samples=[json.loads(line) for line in D0.read_text(encoding="utf-8").splitlines() if line]
    with ORIG.open(encoding="utf-8") as f:
        full=[json.loads(line) for line in f if line.strip()]
    prior=[json.loads(line) for line in P1.read_text(encoding="utf-8").splitlines() if line]
    if len(samples)!=519 or len(full)!=5400 or len(prior)!=166:
        raise ValueError("STAGE64_ORIGINAL519_5400_166_DRIFT")
    index={(x["date"],x["symbol"]):x for x in full}
    old={(x["date"],x["symbol"]):x for x in prior}
    if len(index)!=5400 or len(old)!=166 or len({(x["date"],x["symbol"]) for x in samples})!=519:
        raise ValueError("STAGE64_NOT_UNIQUE_519")
    for item in samples:
        key=(item["date"],item["symbol"])
        x=index[key]
        if (item["source_status"]!="COMPLETE_OFFICIAL_DAILY_USDM_1M_PUBLISHER_SHA_PRICE_PATH"
            or x["source_status"]!="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
            or not x["WATCH_UTC"] or x["WATCH_UTC"][0]!=item["first_D0_watch_UTC"]
            or (x["p1v03_eligible_unbudgeted"] is not None)!=item["reached_P1_historically"]):
            raise ValueError("STAGE64_FIRST_D0_REAL_FULL_MARKET_COHORT_DRIFT "+str(key))
    exact=[s for s in samples if (s["date"],s["symbol"]) in old and old[s["date"],s["symbol"]]["eligible_timestamp_UTC"]==s["first_D0_watch_UTC"]]
    if len(exact)!=46:
        raise ValueError("STAGE64_46_ORIGINAL_IMMEDIATE_P1_PARITY_DRIFT")
    return samples,index,old


def raw_features(t, bars):
    indices=[t - i*MIN for i in range(61,0,-1)]
    if any(k not in bars for k in indices):
        raise ValueError("STAGE64_ASOF_MISSING_61_COMPLETE_MINUTES")
    selected=[bars[k] for k in indices]
    core=selected[1:]
    recent=core[-15:]
    quote15=sum((x[1] for x in recent),D(0))
    quote45=sum((x[1] for x in core[:-15]),D(0))
    quote60=quote15+quote45
    take15=sum((x[2] for x in recent),D(0))
    take60=sum((x[2] for x in core),D(0))
    close0=selected[0][0]
    if close0<=0 or selected[-1][0]<=0:
        raise ValueError("STAGE64_UNTRUSTWORTHY_CLOSE")
    return {
        "ret60_pct":str((selected[-1][0]/close0-1)*100),
        "quote15_USDT":str(quote15),
        "quote60_USDT":str(quote60),
        "quote15_normalized_prev45":str(3*quote15/quote45) if quote45>0 else None,
        "taker_buy_quote15_USDT":str(take15),
        "taker_buy_quote60_USDT":str(take60),
        "taker_buy_share15":str(take15/quote15) if quote15>0 else None,
        "taker_buy_share60":str(take60/quote60) if quote60>0 else None,
        "trade_count15":sum(x[3] for x in recent),
        "trade_count60":sum(x[3] for x in core),
        "minutes_with_positive_quote60":sum(x[1]>0 for x in core),
        "historical_usdm_executed_trades60":sum(x[3] for x in core)>0,
    }


def case(sample,origin,prior,loader=m56.read_verified_day):
    t=m56.parse_time(sample["first_D0_watch_UTC"])
    begin=datetime.fromtimestamp((t-61*MIN)/1000,timezone.utc).date()
    end=datetime.fromtimestamp((t-MIN)/1000,timezone.utc).date()
    if (end-begin).days not in (0,1):
        raise ValueError("STAGE64_BROKEN_ASOF_61M_DAYS")
    original_proofs={x["date"]:x["zip_sha256"] for x in origin["source_daily_minute_official_SHA"]}
    bars={};receipts=[]
    day=begin
    while day<=end:
        daily,proof=loader(sample["symbol"],day)
        if proof["official_zip_sha256"] != original_proofs.get(day.isoformat()) or not proof["checksum_verified"]:
            raise ValueError("STAGE64_PUBLISHER_SHA_NOT_IDENTICAL_TO_STAGE52 "+str((sample["date"],sample["symbol"],day)))
        if bars.keys() & daily.keys():
            raise ValueError("STAGE64_DUPLICATE_SOURCE_MINUTES")
        bars.update(daily)
        receipts.append(proof)
        day+=timedelta(days=1)
    features=raw_features(t,bars)
    independent=prior is not None and prior["eligible_timestamp_UTC"]==sample["first_D0_watch_UTC"]
    if independent:
        for key in ("quote60_USDT","taker_buy_quote15_USDT","taker_buy_quote60_USDT",
                    "taker_buy_share15","taker_buy_share60","trade_count15","trade_count60",
                    "minutes_with_positive_quote60","historical_usdm_executed_trades60"):
            v=features[key]
            if v!=prior[key]:
                raise ValueError("STAGE64_INDEPENDENT_STAGE56_46_IMMEDIATE_ASOF_FEATURE_PARITY_FAIL "+key+" "+str((sample["date"],sample["symbol"])))
        if receipts != prior["source_day_SHA256_receipts"]:
            raise ValueError("STAGE64_46_INDEPENDENT_PUBLISHER_SHA_RECEIPT_MISMATCH")
    return {
        "date":sample["date"],"symbol":sample["symbol"],
        "first_D0_UTC":sample["first_D0_watch_UTC"],
        "source_status":GOOD,
        "original_P1_later_reached_EVALUATION_ONLY":sample["reached_P1_historically"],
        "original_7day_calendar_2x_EVALUATION_ONLY":sample["historical_calendar_2x_EVALUATION_ONLY"],
        "post_D0_24h_close_return_pct_EVALUATION_ONLY":sample["D0_price_path"]["1440"]["end_close_return_pct_PROXY"],
        "features_ASOF_ONLY":features,
        "publisher_SHA_receipts":receipts,
        "independent46_original_P1_same_minute_asof_exact_parity":independent,
        "NOT_A_SPOT_FUTURES_ORDER":True,"USER_ORDER_NOTIONAL":None,
        "HOLDOUT":False,
    }


def median(values):
    return str(statistics.median(values)) if values else None


def describe(group):
    def field(key):
        return [D(x["features_ASOF_ONLY"][key]) for x in group if x["features_ASOF_ONLY"][key] is not None]
    return {
        "n":len(group),
        "ret60_median_pct":median(field("ret60_pct")),
        "quote15_median_USDT":median(field("quote15_USDT")),
        "normalized_15m_quote_vs_prior45_median":median(field("quote15_normalized_prev45")),
        "taker_buy_share15_median":median(field("taker_buy_share15")),
        "trades60_median":median(field("trade_count60")),
        "asof_60m_historical_trade_evidence":sum(x["features_ASOF_ONLY"]["historical_usdm_executed_trades60"] for x in group),
    }


def aggregate(rows):
    by_date=collections.defaultdict(list)
    for row in rows:by_date[row["date"]].append(row)
    return {
        "schema":SCHEMA,
        "original_locked_Git_blobs":LOCK,
        "all_original_first_D0":len(rows),
        "full_source_complete":sum(x["source_status"]==GOOD for x in rows),
        "independent_immediate_P1_46_full_ASOF_feature_parity":sum(x["independent46_original_P1_same_minute_asof_exact_parity"] for x in rows),
        "descriptive_only":{
            "ALL_519":describe(rows),
            "P1_REACHED_166":describe([x for x in rows if x["original_P1_later_reached_EVALUATION_ONLY"]]),
            "NO_P1_353":describe([x for x in rows if not x["original_P1_later_reached_EVALUATION_ONLY"]]),
            "ORIGINAL_7DAY_GT2X_29":describe([x for x in rows if x["original_7day_calendar_2x_EVALUATION_ONLY"]]),
            "ORIGINAL_NO_2X_490":describe([x for x in rows if not x["original_7day_calendar_2x_EVALUATION_ONLY"]]),
            "per_original_calendar_date":{k:describe(v) for k,v in sorted(by_date.items())}
        },
        "ALL_SAMPLES_KNOWN_HISTORIC_NOT_HOLDOUT":True,
        "NO_ASOF_THRESHOLD_FIT_OR_PRIORITY_RULE":True,
        "NO_ASSUMED_ORDER_SIZE":True,
        "P1V03":"REJECTED","MONSTER_DEPLOY":"NO_GO",
        "OTHER_AI_REVIEW":"NOT_DONE","GMAIL":"OFF","AUTOTRADE":"NO_GO",
    }


def selftest():
    t=m56.parse_time("2025-01-02T12:00:00Z")
    data={t-i*MIN:(D(100),D(100),D(60),7) for i in range(61,0,-1)}
    observed=raw_features(t,data)
    assert observed["quote15_USDT"]=="1500" and observed["trade_count60"]==420
    assert observed["taker_buy_share15"]=="0.6"
    data[t]=(D(100000),D(100000),D(100000),100000)
    assert raw_features(t,data)==observed
    del data[t-20*MIN]
    try:
        raw_features(t,data)
    except ValueError as e:
        assert "MISSING_61" in str(e)
    else:
        raise AssertionError("STAGE64_FUTURE_OR_MISSING_MINUTE_ALLOWED")
    print("STAGE64_ASOF_61MIN_SOURCE_NO_FUTURE_POISON_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--out",type=Path)
    p.add_argument("--workers",type=int,default=6)
    a=p.parse_args()
    if a.selftest:selftest();return
    if a.out is None or a.workers not in range(1,9):p.error("--out and workers 1..8 required")
    watch,orig,prior=freeze()
    result=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        tasks={pool.submit(case,x,orig[x["date"],x["symbol"]],prior.get((x["date"],x["symbol"]))):x for x in watch}
        for future in concurrent.futures.as_completed(tasks):
            sample=tasks[future]
            try:result.append(future.result())
            except Exception as e:
                errors.append({"date":sample["date"],"symbol":sample["symbol"],"error":type(e).__name__+":"+str(e)[:240]})
            if (len(result)+len(errors))%50==0:
                print("STAGE64_FULL519_REAL_ASOF_PUBLISHER_SOURCE_PROGRESS "+
                      json.dumps({"done":len(result)+len(errors),"errors":len(errors)},sort_keys=True),flush=True)
    if errors or len(result)!=519:
        raise RuntimeError("STAGE64_HISTORIC_ASOF_SOURCE_INCOMPLETE "+json.dumps(errors[:40],sort_keys=True))
    result.sort(key=lambda x:(x["date"],x["symbol"]))
    summary=aggregate(result)
    if summary["independent_immediate_P1_46_full_ASOF_feature_parity"]!=46:
        raise ValueError("STAGE64_PRIOR_STAGE56_46_PARITY_MISSING")
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage64_all519_D0_asof61m_official_1m_taker_trades_SHA.jsonl").write_text(
        "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in result),encoding="utf-8")
    (a.out/"monster_stage64_all519_asof61m_quote_taker_tradecount_summary.json").write_text(
        json.dumps(summary,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("STAGE64_ALL519_REAL_ASOF_COMPLETE "+json.dumps(summary["descriptive_only"]["ALL_519"],sort_keys=True))


if __name__=="__main__":
    main()
