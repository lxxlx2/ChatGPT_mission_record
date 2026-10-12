#!/usr/bin/env python3
"""Stage85: all 305 Stage83 D1 source-verifiable point-in-time features, no tuning."""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

try:
    import monster_v4_stage38_usdm_original_v4_1m_pilot as src
    import monster_v4_stage81_continuous3m_official_pilot as old81
    from monster_v4_stage80_dual_entry_core import (
        Features, WatchState, decimal, evaluate, gate, from_archived_closed_bars,
        load_contract, sha_blob, utc_ms)
except ImportError:
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as src
    from scripts import monster_v4_stage81_continuous3m_official_pilot as old81
    from scripts.monster_v4_stage80_dual_entry_core import (
        Features, WatchState, decimal, evaluate, gate, from_archived_closed_bars,
        load_contract, sha_blob, utc_ms)

E = Path(__file__).resolve().parents[2] / "monster/evidence"
RAW83 = E / "monster_stage83_all519_source_and_D1_result.jsonl"
RAW64 = E / "monster_stage64_all519_D0_asof61m_official_1m_taker_trades_SHA.jsonl"
PIN83 = "c76b3a137c8dbe56feed3a79a63adcc0752f5e2e"
PIN64 = "8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a"
GOOD = "COMPLETE_OFFICIAL_BINANCE_SHA_ASOF_D1"
MISS = "CENSORED_OFFICIAL_DAILY_ZIP_404"
DATES = old81.DATES
SCHEMA = "MONSTER_STAGE85_ALL305_ASOF_D1_OFFICIAL_FEATURE_REPLAY_V1"
MINUTE = 60000


def load_sources() -> tuple[list[dict], dict]:
    raw83, raw64 = RAW83.read_bytes(), RAW64.read_bytes()
    if sha_blob(raw83) != PIN83 or sha_blob(raw64) != PIN64:
        raise ValueError("STAGE85_HISTORIC_STAGE83_OR_STAGE64_SOURCE_CHANGED")
    rows83 = [json.loads(s) for s in raw83.decode().splitlines() if s.strip()]
    rows64 = [json.loads(s) for s in raw64.decode().splitlines() if s.strip()]
    if (len(rows83),len(rows64)) != (519, 519):
        raise ValueError("STAGE85_EXPECTED_COMPLETE_HISTORIC_519")
    index64 = {(x["date"],x["symbol"]):x for x in rows64}
    if len(index64) != 519 or {(x["date"],x["symbol"]) for x in rows83} != set(index64):
        raise ValueError("STAGE85_HISTORIC_COHORT_CHANGED")
    upgrade = [x for x in rows83 if x["D1_FIRST_UTC"] is not None]
    if len(upgrade) != 305 or sum(x["D1_PATH"] == "DIRECT_AT_FIRST_D0" for x in upgrade) != 164 \
            or sum(x["D1_PATH"] == "REIGNITION_AFTER_D0" for x in upgrade) != 141:
        raise ValueError("STAGE85_305_FROZEN_D1_COHORT_CHANGED")
    if any(x["source_status"]!="COMPLETE_OFFICIAL_PREFIX_SHA_VERIFIED_3M_48H" for x in rows83):
        raise ValueError("STAGE85_PREVIOUSLY_COMPLETE_SOURCE_CHANGED")
    return upgrade, index64


def selected(date: str, shard: int) -> list[dict]:
    if date not in DATES or shard not in range(4):
        raise ValueError("STAGE85_INVALID_PREDECLARED_SHARD")
    rows,_ = load_sources()
    day = sorted((x for x in rows if x["date"] == date),key=lambda r:r["symbol"])
    if not day:
        raise ValueError("STAGE85_EMPTY_DATE")
    return [r for i,r in enumerate(day) if i%4 == shard]


def required_days(t0: int,t1: int):
    if t1 < t0 or t1-t0 >= 48*3600000:
        raise ValueError("STAGE85_D1_NOT_INSIDE_STAGE79_48H")
    first=datetime.fromtimestamp((t0-61*MINUTE)/1000,timezone.utc).date()
    last=datetime.fromtimestamp((t1-MINUTE)/1000,timezone.utc).date()
    return [first+timedelta(days=i) for i in range((last-first).days+1)]


def at(bars: list[tuple],ts: int):
    anchor = bars[0][0]
    if ts % MINUTE or (ts-anchor)%MINUTE:
        raise ValueError("STAGE85_BAD_MINUTE_ALIGNMENT")
    i=(ts-anchor)//MINUTE
    if i < 61 or i >= len(bars)+1:
        raise ValueError("STAGE85_MISSING_SOURCE_WINDOW")
    return from_archived_closed_bars(bars[i-61:i],ts)


def run_one(record: dict, baseline: dict, *, reader=src.verified_1m_day,
            contract: dict | None = None) -> dict:
    if contract is None:
        contract=load_contract()
    day,symbol=record["date"],record["symbol"]
    if (day,symbol)!=(baseline["date"],baseline["symbol"]):
        raise ValueError("STAGE85_FIRST_D0_BASELINE_IDENTITY_DIFF")
    if record["D0_FIRST_UTC"]!=baseline["first_D0_UTC"]:
        raise ValueError("STAGE85_D0_FIRST_CLOCK_DRIFT")
    t0,t1=utc_ms(record["D0_FIRST_UTC"]),utc_ms(record["D1_FIRST_UTC"])
    out={"date":day,"symbol":symbol,"D0_FIRST_UTC":record["D0_FIRST_UTC"],
         "D1_FIRST_UTC":record["D1_FIRST_UTC"],"D1_PATH":record["D1_PATH"],
         "identity":record["identity"],"source_status":"UNKNOWN",
         "D0_PRESERVED":True,"D1_RAW_PRESERVED":True,"no_execution":True}
    prior={p["date"]:p["zip_sha256"] for p in record["source_day_sha256_receipts"]}
    if not prior:
        raise ValueError("STAGE85_MISSING_STAGE83_SOURCE_SHA")
    data,receipts=[],[]
    for dt in required_days(t0,t1):
        try:
            bars,proof=reader(symbol,dt)
        except FileNotFoundError:
            out.update(source_status=MISS,missing_official_day=dt.isoformat(),
                       verified_days_before_missing=receipts)
            return out
        if not proof["verified_official_publisher_SHA256"] or len(bars)!=1440:
            raise ValueError("STAGE85_INVALID_OFFICIAL_DAILY_SHA")
        if prior.get(proof["date"])!=proof["zip_sha256"]:
            raise ValueError("STAGE85_STAGE83_STAGE85_PUBLISHER_ZIP_SHA_DRIFT")
        receipts.append(proof)
        data.extend(bars)
    if not data or any(x[0]!=data[0][0]+i*MINUTE for i,x in enumerate(data)):
        raise ValueError("STAGE85_OFFICIAL_DAYS_NOT_CONTIGUOUS")
    first,last=at(data,t0),at(data,t1)
    old81.compare_stage64(first,baseline)
    if first.closed_price is None or last.closed_price is None:
        raise ValueError("STAGE85_BAD_CLOSED_PRICE")
    rel=(last.closed_price/first.closed_price-1)*100
    is_first=record["D1_PATH"]=="DIRECT_AT_FIRST_D0"
    if is_first != (t0==t1):
        raise ValueError("STAGE85_DIRECT_OR_REIGNITION_TIMESTAMP_MISMATCH")
    if not gate(last,is_first,rel,contract):
        raise ValueError("STAGE85_OLD_FROZEN_D1_NO_LONGER_QUALIFIES")
    # Do not use historical 2x HIGH labels in model decision.
    existing=None if is_first else WatchState(
        venue="USDM",symbol=symbol,first_utc=record["D0_FIRST_UTC"],
        first_price=first.closed_price)
    _,actual=evaluate(existing,venue="USDM",symbol=symbol,
        at_utc=record["D1_FIRST_UTC"],features=last,
        is_first_d0=is_first,contract=contract)
    if actual!=record["D1_PATH"]:
        raise ValueError("STAGE85_OLD_D1_CORE_GATE_PARITY_FAILED")
    out.update(source_status=GOOD, verified_source_publisher_SHA=receipts,
               from_first_d0_delay_minutes=(t1-t0)//MINUTE,
               first_D0_close_price=str(first.closed_price),
               asof_D1_last_closed_price=str(last.closed_price),
               asof_D1_ret60_pct=str(last.ret60_pct),
               asof_D1_quote15_USDT=str(last.quote15_usdt),
               asof_D1_trade15=last.trade15,
               asof_D1_normalized_quote15_prev45=(
                   str(last.quote15_relative45) if last.quote15_relative45 is not None else None),
               asof_D1_ret_from_first_D0_pct=str(rel),
               stage79_frozen_gate_exactly_true=True)
    return out


def selftest():
    rows,index=load_sources()
    union=[x for d in DATES for i in range(4) for x in selected(d,i)]
    if len(union)!=305 or {(x["date"],x["symbol"]) for x in rows} != {
            (x["date"],x["symbol"]) for x in union}:
        raise AssertionError("STAGE85_24_SHARD_UNION_NOT_ALL305")
    origin=utc_ms("2025-01-30T06:00:00Z")
    assert len(required_days(origin,origin)) == 1
    assert len(required_days(origin,origin+47*3600000)) == 3
    assert len(index)==519
    print("STAGE85_ALL305_SOURCE_LOCK_AND_24_SHARD_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--date")
    p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=3)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.date or a.shard is None or not a.out:
        p.error("--date, --shard and --out required")
    if a.workers not in (1,2,3,4):
        raise ValueError("STAGE85_WORKERS_UNBOUNDED")
    tasks=selected(a.date,a.shard)
    _,bases=load_sources()
    contract=load_contract()
    got,errors=[],[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures={pool.submit(run_one,row,bases[(row["date"],row["symbol"])],
                             contract=contract):row for row in tasks}
        for f in concurrent.futures.as_completed(futures):
            row=futures[f]
            try:
                result=f.result()
                got.append(result)
                print("STAGE85_CASE "+json.dumps({
                    k:result[k] for k in ("date","symbol","source_status",
                                          "D1_PATH","from_first_d0_delay_minutes")
                    if k in result},sort_keys=True),flush=True)
            except Exception as e:
                errors.append({"date":row["date"],"symbol":row["symbol"],
                               "reason":type(e).__name__+":"+str(e)[:240]})
    if errors or len(got)!=len(tasks):
        raise RuntimeError("STAGE85_SOURCE_OR_ASOF_GATE_FAIL_CLOSED "+json.dumps(errors[:30]))
    summary={"schema":SCHEMA,"date":a.date,"shard":a.shard,
         "expected_first_D1_events":len(tasks),
         "official_complete":sum(x["source_status"]==GOOD for x in got),
         "censored_official":sum(x["source_status"]==MISS for x in got),
         "rows":sorted(got,key=lambda x:x["symbol"]),
         "NO_MODEL_TUNING":True,"not_oos":True,
         "deployment":"NO_GO","gmail":"OFF","autotrade":"NO_GO"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(summary,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE85_SHARD_PASS "+json.dumps({
        k:summary[k] for k in ("date","shard","expected_first_D1_events",
                               "official_complete","censored_official")},sort_keys=True))


if __name__=="__main__":
    main()
