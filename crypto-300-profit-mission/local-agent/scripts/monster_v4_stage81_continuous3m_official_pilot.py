#!/usr/bin/env python3
"""Stage81: predeclared 12 symbol-days; official USD-M 1m verified continuous D1 pilot."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage38_usdm_original_v4_1m_pilot as src
    from monster_v4_stage80_dual_entry_core import (
        evaluate, load_contract, from_archived_closed_bars, sha_blob, utc_ms, decimal)
except ImportError:
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as src
    from scripts.monster_v4_stage80_dual_entry_core import (
        evaluate, load_contract, from_archived_closed_bars, sha_blob, utc_ms, decimal)

EVIDENCE = Path(__file__).resolve().parents[2] / "monster/evidence"
STAGE64 = EVIDENCE / "monster_stage64_all519_D0_asof61m_official_1m_taker_trades_SHA.jsonl"
SOURCE_SHA = "8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a"
SEED = "MONSTER_STAGE81_EXPOSED_ENGINEERING_PILOT_V1|"
DATES = ("2025-01-30", "2025-06-02", "2025-08-01", "2025-10-02", "2026-06-21", "2026-07-28")
SCHEMA = "MONSTER_STAGE81_12_SOURCE_VERIFIED_3M_CONTINUOUS_48H_RESEARCH_PILOT_V1"


def load_population():
    raw = STAGE64.read_bytes()
    if sha_blob(raw) != SOURCE_SHA:
        raise ValueError("STAGE81_ORIGINAL_FULL519_SOURCE_DRIFT")
    all_rows = [json.loads(s) for s in raw.decode().splitlines() if s.strip()]
    if len(all_rows) != 519 or len({(r["date"], r["symbol"]) for r in all_rows}) != 519:
        raise ValueError("STAGE81_NOT_519_FULL_MARKET_WATCHES")
    if set(x["date"] for x in all_rows) != set(DATES):
        raise ValueError("STAGE81_WRONG_SIX_WINDOWS")
    return all_rows


def choose(rows):
    groups = collections.defaultdict(list)
    for r in rows:
        groups[r["date"]].append(r)
    selected=[]
    for date in DATES:
        daily = sorted(groups[date],key=lambda r:(
            hashlib.sha256((SEED + date + "|" + r["symbol"]).encode()).hexdigest(),r["symbol"]))
        if len(daily)<2:raise ValueError("STAGE81_TOO_FEW_BLIND_CANDIDATES")
        selected.extend(daily[:2])
    if len(selected)!=12 or len({(r["date"],r["symbol"]) for r in selected})!=12:
        raise ValueError("STAGE81_COHORT_NOT_FROZEN")
    return selected


def compare_stage64(f,record):
    baseline=record["features_ASOF_ONLY"]
    required=(("ret60_pct",f.ret60_pct),("quote15_USDT",f.quote15_usdt),
              ("trade_count15",f.trade15),("quote15_normalized_prev45",f.quote15_relative45))
    for name,value in required:
        expected=baseline[name]
        if value is None and expected is None:
            continue
        if value is None or expected is None or abs(decimal(value)-decimal(expected)) > Decimal("0.000000001"):
            raise ValueError("STAGE81_STAGE64_ASOF_PARITY_FAIL:"+name)


def replay_one(record, loader=src.minute_source):
    contract=load_contract()
    date,symbol=record["date"],record["symbol"]
    out={"date":date,"symbol":symbol,"original_first_D0_UTC":record["first_D0_UTC"],
         "original_calendar2x_evaluation_only":record["original_7day_calendar_2x_EVALUATION_ONLY"],
         "source_status":"UNKNOWN","d1_first_UTC":None,"d1_path":None,
         "D0_NO_LOSS":True,"NO_EMAIL_NO_TRADE":True}
    try:
        bars,proof=loader(symbol,date)
    except FileNotFoundError as e:
        out.update(source_status="CENSORED_DAILY_ZIP_404_UNKNOWN",
                   source_error=str(e)[:200])
        return out
    if len(bars)!=src.BARS or len(proof)!=9 or bars[0][0]!=src.msutc(date+"T06:00:00Z")-86400_000:
        raise ValueError("STAGE81_WRONG_OFFICIAL_9DAY_SOURCE")
    if any(not p["verified_official_publisher_SHA256"] or not p["zip_sha256"] for p in proof):
        raise ValueError("STAGE81_PUBLISHER_SHA_NOT_VERIFIED")
    official={p["date"]:p["zip_sha256"] for p in proof}
    for old in record["publisher_SHA_receipts"]:
        if old["date"] not in official or old["official_zip_sha256"]!=official[old["date"]] or not old["checksum_verified"]:
            raise ValueError("STAGE81_PRIOR_SAVED_OFFICIAL_DAY_SHA_DRIFT")
    t_first=utc_ms(record["first_D0_UTC"])
    first_index=(t_first-bars[0][0])//60_000
    if first_index<61 or first_index>=len(bars):
        raise ValueError("STAGE81_FIRST_WATCH_MISSING_ARCHIVED_MINUTE")
    first_features=from_archived_closed_bars(bars[first_index-61:first_index],t_first)
    compare_stage64(first_features,record)
    utc_window_end=utc_ms(date+"T06:00:00Z")+7*86400_000
    limit=min(t_first+contract["from_first_d0_expiration_hours"]*3600_000,utc_window_end)
    state=None
    tick_count=0
    for t in range(t_first,limit,180_000):
        i=(t-bars[0][0])//60_000
        f=from_archived_closed_bars(bars[i-61:i],t)
        timestamp=src.stamp(t)
        state,kind=evaluate(state,venue="USDM",symbol=symbol,at_utc=timestamp,
                            features=f,is_first_d0=(tick_count==0),contract=contract)
        tick_count+=1
        if kind in ("DIRECT_AT_FIRST_D0","REIGNITION_AFTER_D0"):
            out["d1_first_UTC"]=timestamp
            out["d1_path"]=kind
            break
    if state is None or state.first_utc!=record["first_D0_UTC"]:
        raise ValueError("STAGE81_FIRST_WATCH_STATE_DROPPED")
    out.update(source_status="COMPLETE_OFFICIAL_9DAY_VERIFIED_CONTINUOUS_3M",
               original_first_61min_stage64_feature_parity=True,
               actual_ticks_until_first_D1_or_cutoff=tick_count,
               actual_watched_minutes=tick_count*3,
               official_daily_1m_publisher_sha_receipts=proof,
               first_time_ret60_pct=str(first_features.ret60_pct),
               first_time_quote15_usdt=str(first_features.quote15_usdt),
               first_time_trade15=first_features.trade15)
    return out


def selftest():
    all_rows=load_population()
    selected=choose(all_rows)
    reverse=choose(list(reversed(all_rows)))
    assert [(r["date"],r["symbol"]) for r in reverse]==[(r["date"],r["symbol"]) for r in selected]
    assert len(selected)==12
    for r in selected:
        assert "original_7day_calendar_2x_EVALUATION_ONLY" in r
    print("STAGE81_LABEL_BLIND_12_FROZEN_IDENTITY_SELFTEST_PASS")
    print("STAGE81_BLIND_SELECTED_IDENTITIES " + json.dumps(
        [{"date":r["date"],"symbol":r["symbol"]} for r in selected],sort_keys=True))


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--selftest",action="store_true")
    a.add_argument("--out",type=Path)
    a.add_argument("--date")
    a.add_argument("--symbol")
    p=a.parse_args()
    if p.selftest:selftest();return
    selected=choose(load_population())
    if p.date:
        selected=[r for r in selected if r["date"]==p.date and
                  (p.symbol is None or r["symbol"]==p.symbol)]
        if len(selected)!=(1 if p.symbol is not None else 2):
            raise ValueError("STAGE81_NOT_THE_FROZEN_ONE_OR_TWO_PREDECLARED_CASES")
    elif p.symbol:
        raise ValueError("STAGE81_SYMBOL_REQUIRES_DATE")
    results=[]
    for row in selected:
        value=replay_one(row)
        results.append(value)
        print("STAGE81_ONE_CASE "+json.dumps(
            {k:value[k] for k in ("date","symbol","source_status","d1_first_UTC","d1_path")},sort_keys=True),flush=True)
    summary={"schema":SCHEMA,"selected":len(results),
             "source_complete":sum(x["source_status"]=="COMPLETE_OFFICIAL_9DAY_VERIFIED_CONTINUOUS_3M" for x in results),
             "source_censored":sum(x["source_status"]=="CENSORED_DAILY_ZIP_404_UNKNOWN" for x in results),
             "d1_upgrade":sum(x["d1_first_UTC"] is not None for x in results),
             "result":results,"sample_selection":"HASH_SEED_ALL519_FROZEN_TWO_PER_SIX_DATES_NO_FUTURE_LABEL",
             "strategy_thresholds":"FROZEN_STAGE79_UNMODIFIED",
             "this_is_exposed_engineering_pilot_not_market_performance":True,
             "oos":"NOT_DONE","net_profit":"UNKNOWN","deployment":"NO_GO","gmail":"OFF","autotrade":"NO_GO"}
    if summary["source_complete"]+summary["source_censored"]!=summary["selected"]:
        raise ValueError("STAGE81_NOT_ALL_SELECTEES_CLASSIFIED")
    raw=json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if p.out:
        p.out.parent.mkdir(parents=True,exist_ok=True)
        p.out.write_text(raw)
    print("STAGE81_SUMMARY "+json.dumps({k:summary[k] for k in (
        "selected","source_complete","source_censored","d1_upgrade","oos")},sort_keys=True))


if __name__=="__main__":
    main()
