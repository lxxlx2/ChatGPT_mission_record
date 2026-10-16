#!/usr/bin/env python3
"""Only diagnose genuine shared first32 D1 source failure without changing D0/D1."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch

import monster_v4_shared_spot_d0_d1_original_core as shared
import monster_v4_shared_445_first32_real_comparison as first
import monster_v4_stage26_continuous168h as old
import monster_v4_shared_445_official_source_shards as shards

SCHEMA="MONSTER_FEB2026_FIRST32_ORIGINAL_D1_OFFICIAL_SOURCE_FAIL_CLOSED_DIAGNOSTIC_V1"


def candle_problem(candles):
    if not candles or any(not isinstance(c,list) or len(c)!=8 for c in candles):
        return "MALFORMED_CANDLE_STRUCTURE"
    for c in candles:
        try:
            op,hi,lo,cl,volume,quote=[
                Decimal(str(c[i])) for i in (1,2,3,4,5,7)]
            if not all(x.is_finite() for x in (op,hi,lo,cl,volume,quote)):
                return "NONFINITE_KLINE_FIELDS"
            if min(op,hi,lo,cl)<=0 or not (lo<=op<=hi and lo<=cl<=hi):
                return "INVALID_OHLC_ENVELOPE"
            if volume<0:
                return "NEGATIVE_REAL_VOLUME"
            if quote<=0:
                return "ZERO_OR_NEGATIVE_OFFICIAL_KLINE_QUOTE_UNSUPPORTED_BY_FROZEN_D1"
        except (ValueError,TypeError,ArithmeticError,IndexError):
            return "UNPARSABLE_NUMERIC_KLINE"
    return "UNKNOWN_PRODUCTION_EVALUATOR_OR_TIME_CONTRACT"


def only_clock_and_price(c):
    return {"open_ms":c[0],"close_ms":c[6],"OHLC":[c[i] for i in (1,2,3,4)],
            "volume":c[5],"quote":c[7]}


def diagnose(source_dir):
    sources=[]
    for i in (0,1):
        arc=Path(source_dir)/f"monster_feb445_shard{i:02d}.zip"
        pf=Path(source_dir)/f"monster_feb445_shard{i:02d}.proof.json"
        if not arc.is_file() or not pf.is_file():
            raise ValueError("SHARED_445_FIRST32_DIAGNOSTIC_MISSING_FROZEN_ARTIFACT")
        proof=json.loads(pf.read_text())
        if proof.get("source_origin_verified_at_collection") is not True:
            raise ValueError("SHARED_445_FIRST32_DIAGNOSTIC_UNATTESTED_PROOF")
        rec=list(shards.read_archive(arc,proof=proof,expected_shard=i))
        if [z[0] for z in rec]!=list(shards.members(i)):
            raise ValueError("SHARED_445_FIRST32_DIAGNOSTIC_WRONG_SOURCE_MEMBERS")
        sources.append({"shard":i,"zip_sha256":proof["sha256_zip"],
             "producer_commit":proof["trigger_commit_sha"],
             "symbol_count":len(rec)})
    captured=[]
    old_watches=[]
    original_helper=shared.verified_closed_5m_for_original_d1

    def observe_without_altering(*args,**kwargs):
        db,roster,venue,symbol,at_ms=args
        try:
            return original_helper(*args,**kwargs)
        except RuntimeError as exc:
            if not captured:
                arr=db.execute("""
                    SELECT end_ms,candle_json FROM closed5m_source
                    WHERE symbol=? AND end_ms<? ORDER BY end_ms DESC LIMIT 8
                """,(symbol,at_ms)).fetchall()
                arr=list(reversed(arr))
                decoded=[]
                for row in arr:
                    try:
                        c=json.loads(row[1])
                        decoded.append(only_clock_and_price(c))
                    except (ValueError,IndexError,KeyError,TypeError):
                        decoded.append({"INVALID_JSON_OR_CANDLE_SHAPE":True,
                                        "end_ms":row[0]})
                captured.append({
                  "symbol":symbol,"venue":venue,
                  "D1_requested_utc":datetime.fromtimestamp(at_ms/1000,
                      timezone.utc).isoformat().replace("+00:00","Z"),
                  "D1_requested_ms":at_ms,
                  "research_exception":str(exc),
                  "original_cause":str(exc.__cause__),
                  "source_failure_class":candle_problem(
                      [json.loads(x[1]) for x in arr]
                      if all(x.get("quote") is not None for x in decoded) else []),
                  "eight_closed_5m_source":decoded
                })
            raise

    def original_watches_collector(symbol,day,bars):
        case=old.scan_continuous(symbol,day,bars)
        old_watches.append({"symbol":symbol,
                            "watch_utcs":case["watch_utcs"],
                            "source_model":"ORIGINAL_STAGE26_PER_SYMBOL_NOT_SHARED_D0"})
        return case

    status="UNKNOWN"
    with patch.object(shared,"verified_closed_5m_for_original_d1",
                      side_effect=observe_without_altering):
        try:
            out=first.analyze_two(source_dir,
                                  legacy_scan=original_watches_collector)
        except RuntimeError as exc:
            if str(exc)!="SHARED_SPOT_ORIGINAL_D1_SOURCE_INVALID_CANDLE":
                raise
            if len(captured)!=1:
                raise ValueError("SHARED_445_UNLOCATED_FIRST_D1_SOURCE_FAILURE")
            status="FAIL_CLOSED_OFFICIAL_D1_SOURCE_CONTRACT"
        else:
            status="SUCCESS_UNEXPECTED_PREVIOUS_BLOCKER_NOT_REPRODUCED"
    old_burst=sorted(r["symbol"] for r in old_watches
             if "2026-02-06T00:36:00Z" in r["watch_utcs"])
    return {
      "schema":SCHEMA,
      "status":status,
      "model_report_issued":status!="FAIL_CLOSED_OFFICIAL_D1_SOURCE_CONTRACT",
      "real_445_shared_model_COMPLETED":False,
      "first32_shared_model_COMPLETED":status!="FAIL_CLOSED_OFFICIAL_D1_SOURCE_CONTRACT",
      "old_stage26_32_symbols_scanned":len(old_watches),
      "original_445_complete_denominator":445,
      "historical_758_denominator":758,
      "historical_313_source_censored":313,
      "official_source_archive_proofs":sources,
      "first_fatal_D1_source_request":captured[0] if captured else None,
      "old_stage26_per_symbol_WATCH_20260206_0036_symbols":old_burst,
      "old_stage26_per_symbol_WATCH_20260206_0036_count":len(old_burst),
      "independent_all32_shared_D0_watch_parity_if_failure":"NOT_SCORABLE",
      "do_not_alter_approved_source_contract":True,
      "not_tradeable_recommendation":True,
      "trigger_commit_sha":os.environ.get("GITHUB_SHA","LOCAL_UNVERIFIED"),
      "diagnostic_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      "G4":"UNKNOWN","G6":"NO_GO"
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.out.exists() or a.out.is_symlink():
        raise ValueError("SHARED_445_DIAGNOSTIC_OUTPUT_EXISTS")
    result=diagnose(a.source_dir)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("x",encoding="utf-8") as f:
        f.write(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print("MONSTER_FIRST32_D1_SOURCE_DIAGNOSTIC "+
          json.dumps({"status":result["status"],
            "fatal":result["first_fatal_D1_source_request"],
            "legacy_0036_watch_count":result["old_stage26_per_symbol_WATCH_20260206_0036_count"],
            "model_report_issued":result["model_report_issued"]},sort_keys=True))


if __name__=="__main__":
    main()
