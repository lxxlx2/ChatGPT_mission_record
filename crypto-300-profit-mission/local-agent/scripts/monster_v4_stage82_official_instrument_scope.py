#!/usr/bin/env python3
"""Fail-closed identity scope for Monster crypto model; preserve raw WATCH evidence."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
try:
    from monster_v4_stage80_dual_entry_core import sha_blob, utc_ms
except ImportError:
    from scripts.monster_v4_stage80_dual_entry_core import sha_blob, utc_ms

ROOT = Path(__file__).resolve().parents[2]/"monster"/"evidence"
PIN = "00eb09c18fa91375513c79263d2a962c27530cde"
MANIFEST = ROOT/"monster_stage82_official_tradfi_instrument_scope_20261013.json"
STAGE81 = ROOT/"monster_stage81_official_12_continuous3m_source_replay_summary_20261013.json"
TARGET_VENUE = "USDM"
RESEARCH_ONLY = True


def official_registry():
    raw=MANIFEST.read_bytes()
    if sha_blob(raw)!=PIN:
        raise ValueError("STAGE82_OFFICIAL_INSTRUMENT_PROOF_CHANGED")
    data=json.loads(raw)
    if data["schema"]!="MONSTER_STAGE82_BINANCE_OFFICIAL_TRADFI_CRYPTO_SCOPE_EXCLUSION_V1":
        raise ValueError("STAGE82_BAD_OFFICIAL_REGISTRY_SCHEMA")
    if not data["official_source"].startswith("https://www.binance.com/en/support/announcement/detail/"):
        raise ValueError("STAGE82_OFFICIAL_SOURCE_CHANGED")
    names={x["symbol"]:x for x in data["instruments"]}
    if len(names)!=7:raise ValueError("STAGE82_TRADFI_SOURCE_MISSING")
    for i in names.values():
        if utc_ms(i["launch_time_utc"])<utc_ms(data["official_announcement_published_at_utc"]):
            raise ValueError("STAGE82_BAD_LAUNCH_TIMING")
    return names


def category(venue: str,symbol: str,at_utc: str,registry: dict) -> str:
    t=utc_ms(at_utc)
    if venue!=TARGET_VENUE or not re.fullmatch(r"[A-Z0-9]+USDT",symbol):
        return "VENUE_OR_SYMBOL_IDENTITY_UNVERIFIED"
    if symbol in registry:
        x=registry[symbol]
        if t<utc_ms(x["launch_time_utc"]):
            return "SOURCE_TEMPORAL_IDENTITY_CONFLICT"
        return "CONFIRMED_TRADFI_OUT_OF_CRYPTO_SCOPE"
    if re.match(r"^(?:1000000|1000)[A-Z0-9]+USDT$",symbol):
        return "MULTIPLIER_MAPPING_UNVERIFIED"
    return "CRYPTO_IDENTITY_UNVERIFIED"


def annotate(replay: dict,registry: dict) -> dict:
    if replay["schema"]!="MONSTER_STAGE81_12_SOURCE_VERIFIED_3M_CONTINUOUS_48H_RESEARCH_PILOT_SUMMARY_V1":
        raise ValueError("STAGE82_STAGE81_SOURCE_SCHEMA")
    records=[]
    for r in replay["cases"]:
        base=r["d1_first_UTC"] or r["date"]+"T06:00:00Z"
        c=category("USDM",r["symbol"],base,registry)
        records.append({
            "date":r["date"],"symbol":r["symbol"],
            "raw_d1_research_event":r["d1_first_UTC"] is not None,
            "raw_d1_utc":r["d1_first_UTC"],
            "scope_category":c,
            "crypto_model_d1_eligible":False,
            "D0_JOURNAL_PRESERVED":True
        })
    if len(records)!=12 or sum(x["scope_category"]=="CONFIRMED_TRADFI_OUT_OF_CRYPTO_SCOPE" for x in records)!=2:
        raise ValueError("STAGE82_EXPOSED_TWELVE_SCOPE_PARITY")
    return {"schema":"MONSTER_STAGE82_OFFICIAL_SCOPE_12_PILOT_DIAGNOSTIC_V1",
       "source_official_registry_blob":PIN,
       "source_stage81_trial_result_preserved":True,
       "sampled":len(records),
       "confirmed_TradFi_out_of_scope":2,
       "multiplier_unverified":sum(x["scope_category"]=="MULTIPLIER_MAPPING_UNVERIFIED" for x in records),
       "other_unknown":sum(x["scope_category"]=="CRYPTO_IDENTITY_UNVERIFIED" for x in records),
       "raw_d1_before_classification":sum(x["raw_d1_research_event"] for x in records),
       "crypto_model_eligible_d1":0,
       "warning":"0 eligible is a classification evidence shortfall, not model found 0 crypto candidates. No confirmed crypto-only denominator has been established.",
       "rows":records,"deployment":"NO_GO","gmail":"OFF","autotrade":"NO_GO","frank":"UNCHANGED"}


def selftest():
    registry=official_registry()
    assert category("USDM","LRCXUSDT","2026-07-30T13:33:00Z",registry)=="CONFIRMED_TRADFI_OUT_OF_CRYPTO_SCOPE"
    assert category("USDM","KLACUSDT","2026-07-28T06:00:00Z",registry)=="CONFIRMED_TRADFI_OUT_OF_CRYPTO_SCOPE"
    assert category("USDM","LRCXUSDT","2026-06-22T13:27:00Z",registry)=="SOURCE_TEMPORAL_IDENTITY_CONFLICT"
    assert category("USDM","1000WHYUSDT","2025-08-05T06:00:00Z",registry)=="MULTIPLIER_MAPPING_UNVERIFIED"
    assert category("USDM","KASUSDT","2025-02-03T06:00:00Z",registry)=="CRYPTO_IDENTITY_UNVERIFIED"
    assert category("SPOT","LRCXUSDT","2026-07-30T13:33:00Z",registry)=="VENUE_OR_SYMBOL_IDENTITY_UNVERIFIED"
    print("STAGE82_OFFICIAL_TRADFI_EXCLUSION_AND_UNKNOWN_FAIL_CLOSED_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    registry=official_registry()
    result=annotate(json.loads(STAGE81.read_text()),registry)
    s=json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(s)
    print(s)


if __name__=="__main__":
    main()
