#!/usr/bin/env python3
"""Stage93 source-locked original V4 900x6 WATCH recall: include NO-WATCH 2x."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

E = Path(__file__).resolve().parents[2] / "monster/evidence"
SOURCE = E / "monster_stage39_all5400_usdm_real1m_originalV4_cases.jsonl"
BASELINE = E / "monster_stage39_36original_SHA_all5400_futures_discovery_summary.json"
PIN_SOURCE = "a2f66aa2331d02d14c0276b446381dc6856cba0e"
PIN_BASELINE = "d4dae1d2a2cd4e43bd8f1cb0fcb16b0724240080"
DATES = ("2025-01-19","2025-04-19","2025-07-19",
         "2025-10-19","2026-04-19","2026-07-19")
COMPLETE = "COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
SCHEMA = "MONSTER_STAGE93_EXPOSED_900X6_WHOLE_FROZEN_USDM_SOURCE_RECALL_V1"
MIN = 60000


def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def time_ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z","+00:00")).timestamp()*1000)


def score(watches: list[str], cross: str|None) -> dict:
    if cross is None:
        return {"class":"NO_GROSS_MULTIPLE","first_watch_lead_min":None}
    if not watches:
        return {"class":"NO_WATCH","first_watch_lead_min":None}
    first = time_ms(watches[0])
    at = time_ms(cross)
    lead = (at-first)/MIN
    cls = ("EARLY_GE5" if lead>=5 else "EARLY_UNDER5" if lead>0
           else "SAME_MINUTE" if lead==0 else "LATE")
    return {"class":cls,"first_watch_lead_min":lead}


def read():
    if blob(SOURCE.read_bytes()) != PIN_SOURCE or blob(BASELINE.read_bytes()) != PIN_BASELINE:
        raise ValueError("STAGE93_ORIGINAL_STAGE39_SOURCE_OR_REPORT_BLOB_CHANGED")
    raw = [json.loads(v) for v in SOURCE.read_text().splitlines() if v.strip()]
    summary = json.loads(BASELINE.read_text())
    if len(raw)!=5400 or len({(x["date"],x["symbol"]) for x in raw})!=5400:
        raise ValueError("STAGE93_NOT_ORIGINAL_5400_COIN_DATES")
    for d in DATES:
        subset=[x for x in raw if x["date"]==d]
        if len(subset)!=900:
            raise ValueError("STAGE93_WRONG_900_EACH_DATE")
    expected={
        "full_stage37_hourly_source_attempts":5400,
        "gt2x_full_source":51,
        "gt2x_early_strict":48,
        "all_source_complete_with_any_WATCH_coin_dates":483,
    }
    for field,n in expected.items():
        if summary[field]!=n:
            raise ValueError("STAGE93_STAGE39_BASELINE_CHANGED_"+field)
    return raw, summary


def audit(raw,baseline):
    statuses=Counter(x["source_status"] for x in raw)
    good=[x for x in raw if x["source_status"]==COMPLETE]
    if len(good)!=3283 or len(raw)-len(good)!=2117:
        raise ValueError("STAGE93_ORIGINAL_SOURCE_COMPLETE_COUNTS_DRIFT")
    winners=[]
    bydate={}
    for day in DATES:
        coin=[x for x in good if x["date"]==day]
        category=Counter()
        for row in coin:
            event=row.get("first_true_2x_HIGH_minute_UTC")
            flag=row.get("original_GT2x_1h")
            if flag not in ("True","False"):
                raise ValueError("STAGE93_UNEXPECTED_ORIGINAL_GT2_LABEL")
            if bool(event)!=(flag=="True"):
                raise ValueError("STAGE93_ORIGINAL_FIRST_HIGH_LABEL_DISAGREES")
            watches=row["WATCH_UTC"]
            if len(watches)!=row["watch_count"] or watches!=sorted(set(watches)):
                raise ValueError("STAGE93_ORIGINAL_WATCHES_DUPLICATED_OR_UNSORTED")
            decision=score(watches,event)
            if event:
                # Historical scorer categorizes *some* strict-prior WATCH; the
                # first-WATCH view must be identical on strict timing.
                if (decision["class"] in ("EARLY_GE5","EARLY_UNDER5")) != (
                    row["classification"]=="STRICTLY_EARLY_WATCH"):
                    raise ValueError("STAGE93_PREVIOUS_CAUSAL_CLASS_DISAGREES")
                category[decision["class"]]+=1
                winners.append({
                    "date":day,"symbol":row["symbol"],
                    "first_real_1m_2x_HIGH_UTC":event,
                    "first_original_D0_WATCH_UTC":watches[0] if watches else None,
                    "all_original_WATCH_events":len(watches),
                    "first_watch_lead_min":decision["first_watch_lead_min"],
                    "first_watch_class":decision["class"],
                    "last_original_2x_class":row["classification"],
                    "historical_usdm_symbol_venue":"BINANCE_USDM",
                    "point_in_time_trading_and_crypto_identity":"UNVERIFIED",
                })
        bydate[day]={
            "source_complete":len(coin),
            "source_censored":900-len(coin),
            "original_D0_eligible_WATCH":sum(x["watch_count"]>0 for x in coin),
            "real_2x":sum(category.values()),
            "first_watch_classes":dict(category)}
    classify=Counter(x["first_watch_class"] for x in winners)
    strictly=sum(classify[s] for s in ("EARLY_GE5","EARLY_UNDER5"))
    early5=classify["EARLY_GE5"]
    if len(winners)!=51 or strictly!=48 or \
       classify["NO_WATCH"]!=1 or classify["SAME_MINUTE"]!=1 or classify["LATE"]!=1:
        raise ValueError("STAGE93_ALL51_WRONG_ORIGINAL_FIRST_D0_CLASSIFICATION")
    for field,got in (
        ("gt2x_full_source",len(winners)),
        ("gt2x_early_strict",strictly),
        ("gt2x_no_watch",classify["NO_WATCH"]),
        ("gt2x_same_minute_not_early",classify["SAME_MINUTE"]),
        ("gt2x_late_watch",classify["LATE"]),
    ):
        if baseline[field]!=got:
            raise ValueError("STAGE93_ORIGINAL_STAGE39_SUMMARY_DISAGREES_"+field)
    watch_count=sum(x["watch_count"]>0 for x in good)
    if watch_count!=baseline["all_source_complete_with_any_WATCH_coin_dates"]:
        raise ValueError("STAGE93_ORIGINAL_483_COIN_DATES_DISAGREE")
    return {
      "schema":SCHEMA,
      "source_stage39_all5400_git_blob":PIN_SOURCE,
      "summary_stage39_git_blob":PIN_BASELINE,
      "dates":list(DATES),
      "all_frozen_900x6_attempts":len(raw),
      "source_complete":len(good),
      "source_censored":len(raw)-len(good),
      "censoring_by_reason":dict(statuses),
      "observed_gt2x_in_source_complete":len(winners),
      "strictly_first_D0_pre_first_2x_HIGH":strictly,
      "first_D0_early_at_least_5min":early5,
      "source_complete_2x_firstD0_strict_fraction":str(strictly/len(winners)),
      "source_complete_2x_firstD0_early5_fraction":str(early5/len(winners)),
      "source_complete_2x_firstD0_classifications":dict(classify),
      "non2x_source_complete":len(good)-len(winners),
      "watch_coin_dates_all_source_complete":watch_count,
      "per_original_day":bydate,
      "all_source_complete_2x_case_registry":sorted(
          winners,key=lambda x:(x["date"],x["symbol"])),
      "formally_full_crypto_market_G1":"NOT_SCORABLE_POINT_IN_TIME_UNIVERSE_UNKNOWN",
      "historical_scope":"EXPOSED_ARCHIVAL_900_PER_DAY_ONLY",
      "point_in_time_symbol_active_population":"UNVERIFIED",
      "crypto_only":"NOT_VERIFIED",
      "unseen_future_G0_G1":"NOT_DONE",
      "D1_G3":"REJECTED_EXPOSED",
      "executable_profit":"UNKNOWN",
      "no_new_thresholds":True,"no_live_deployment":True,
      "other_AI_review":"NOT_DONE","gmail":"OFF","autotrade":"NO_GO","frank":"UNCHANGED"
    }


def selftest():
    ts="2025-01-19T08:00:00Z"
    assert score([],ts)["class"]=="NO_WATCH"
    assert score(["2025-01-19T07:55:00Z"],ts)["class"]=="EARLY_GE5"
    assert score(["2025-01-19T07:57:00Z"],ts)["class"]=="EARLY_UNDER5"
    assert score([ts],ts)["class"]=="SAME_MINUTE"
    assert score(["2025-01-19T08:03:00Z"],ts)["class"]=="LATE"
    assert score([ts],None)["class"]=="NO_GROSS_MULTIPLE"
    assert len(DATES)==6
    print("STAGE93_FIRST_D0_VS_REAL_FIRST_HIGH_TIMING_SYNTHETIC_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--audit",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.audit or not a.out:
        p.error("--audit --out required; future dates and trading unsupported")
    o=audit(*read())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("STAGE93_ALL5400_SOURCE_VALID_FULL_UNIVERSE_HISTORIC_RECALL "+json.dumps({
        k:o[k] for k in ("all_frozen_900x6_attempts","source_complete","source_censored",
                        "observed_gt2x_in_source_complete",
                        "strictly_first_D0_pre_first_2x_HIGH",
                        "first_D0_early_at_least_5min",
                        "source_complete_2x_firstD0_classifications")},sort_keys=True))


if __name__=="__main__":
    main()
