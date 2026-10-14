#!/usr/bin/env python3
"""One-shot frozen-window full-market official 1m replay, exact original V4 core.

Research only. Existing Stage97 capture must be present and independently
attested, user has not authorized any schedule, installation, or live alerts.
One symbol per worker, stable SHA-hash shard; missing source is not a loser.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date
import hashlib
import json
from pathlib import Path

try:
    import monster_v4_stage116_forward_population_score as scoring
    import monster_v4_stage117_first_d0_fast_attention_core as early_candidate
except ImportError:
    from scripts import monster_v4_stage116_forward_population_score as scoring
    from scripts import monster_v4_stage117_first_d0_fast_attention_core as early_candidate

old=scoring.old
v4=old.v4
REPLAY_SCHEMA=scoring.REPLAY_SCHEMA
SHARDS=24
PACKET_SCHEMA="MONSTER_STAGE116_REAL_OFFICIAL_FUTURE_WINDOW_SHARD_V1"


def shard_no(symbol):
    return int(hashlib.sha256(symbol.encode("ascii")).hexdigest()[:8],16)%SHARDS


def absent(symbol,window,exc):
    return {
        "date":window[:10],"venue":"BINANCE_USDM",
        "symbol":symbol,
        "source_status":"CENSORED_OR_UNAVAILABLE_OFFICIAL_DAILY_1M",
        "error_type":type(exc).__name__,
        "source_unavailable_reason":str(exc)[:220],
        "D0_first_UTC":None,"D1_first_UTC":None,
        "Crypto_identity":"UNKNOWN_NEEDS_INDEPENDENT_ASOF_PROOF",
        "D2_execution":"UNKNOWN",
        "gross_future_labels_not_real_profit":{},
        "original_data_unavailable_not_a_negative_case":True,
    }


def replay_one(symbol,window,fetch=None):
    if fetch is None:fetch=v4.minute_source
    try:
        bars,receipts=fetch(symbol,window[:10])
    except FileNotFoundError as exc:
        return absent(symbol,window,exc)
    # Propagate checksum, bad provenance and non-404 transient network errors:
    # these are operational failures, not an ordinary delisting or no winner.
    original=old.replay_raw_symbol(symbol,window,bars,receipts)
    # The rejected old D1 stays unchanged; Stage117 fast first-D0 is a
    # separately frozen candidate from closed minutes strictly before t.
    first=original["D0_first_UTC"]
    if first is None:
        original["stage117_new_first_D0_candidate"]=None
    else:
        original["stage117_new_first_D0_candidate"]=(
            early_candidate.from_closed_minutes(
                venue="USDM",symbol=symbol,first_d0_utc=first,
                minute_bars=bars))
    return original


def source_shard(snapshot,window,shard,workers=3,fetch=None):
    if shard not in range(SHARDS) or workers not in range(1,5):
        raise ValueError("STAGE116_SHARD_OR_WORKER_POLICY")
    universe=scoring.audited_capture(snapshot,window)
    symbols=sorted(x["symbol"] for x in universe["rows"]
                   if x["candidate_for_raw_USDM_attempt"] and shard_no(x["symbol"])==shard)
    if not symbols:
        return {
            "schema":PACKET_SCHEMA,
            "window_start_utc":window,"shard":shard,
            "window_exchange_info_sha256":universe["raw_sha256"],
            "original_model_source_sha":old.MODEL_SOURCE_V4,
            "original_d1_contract_sha":old.D1_SOURCE_CONTRACT,
            "rows":[],"empty_shard":True,
            "live_deployment":"NO_GO",
        }
    rows=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending={pool.submit(replay_one,symbol,window,fetch):symbol for symbol in symbols}
        for future in as_completed(pending):
            symbol=pending[future]
            try:
                result=future.result()
            except Exception as exc:
                raise RuntimeError(
                    "STAGE116_ORIGINAL_MODEL_OR_OFFICIAL_SOURCE_INTEGRITY_FAILURE "+
                    symbol+" "+str(exc)) from exc
            if result["symbol"]!=symbol or result["date"]!=window[:10]:
                raise ValueError("STAGE116_SHARD_SYMBOL_RESULT_MISMATCH")
            rows.append(result)
            print("STAGE116_FORWARD_OFFICIAL_SOURCE "+window+" "+symbol+" "+
                  result["source_status"],flush=True)
    if len(rows)!=len(symbols):
        raise ValueError("STAGE116_SOURCE_ATTEMPT_ROW_LOST")
    return {
        "schema":PACKET_SCHEMA,
        "window_start_utc":window,
        "shard":shard,
        "window_exchange_info_sha256":universe["raw_sha256"],
        "original_model_source_sha":old.MODEL_SOURCE_V4,
        "original_d1_contract_sha":old.D1_SOURCE_CONTRACT,
        "rows":sorted(rows,key=lambda z:z["symbol"]),
        "empty_shard":False,
        "source_attested_stage97":True,
        "research_only":True,
        "live_deployment":"NO_GO",
    }


def aggregate_shards(snapshot,window,shards:list[dict]):
    if len(shards)!=SHARDS:
        raise ValueError("STAGE116_REQUIRES_EXACT_ALL24_REAL_FORWARD_SHARDS")
    universe=scoring.audited_capture(snapshot,window)
    allrows=[]
    seen=set()
    for item in shards:
        key=item.get("shard")
        if (item.get("schema")!=PACKET_SCHEMA or key not in range(SHARDS) or
            key in seen or item["window_start_utc"]!=window or
            item["window_exchange_info_sha256"]!=universe["raw_sha256"] or
            item["original_model_source_sha"]!=old.MODEL_SOURCE_V4 or
            item["original_d1_contract_sha"]!=old.D1_SOURCE_CONTRACT):
            raise ValueError("STAGE116_SHARD_DATE_SHA_OR_UNIVERSE_DRIFT")
        seen.add(key)
        if any(shard_no(x["symbol"])!=key for x in item["rows"]):
            raise ValueError("STAGE116_HASH_SHARD_CONSISTENCY_FAILED")
        allrows+=item["rows"]
    if seen!=set(range(SHARDS)):
        raise ValueError("STAGE116_MISSING_SHARD")
    out={
        "schema":REPLAY_SCHEMA,
        "window_start_utc":window,
        "venue":"BINANCE_USDM",
        "window_exchange_info_sha256":universe["raw_sha256"],
        "original_model_source_sha":old.MODEL_SOURCE_V4,
        "original_d1_contract_sha":old.D1_SOURCE_CONTRACT,
        "rows":sorted(allrows,key=lambda z:z["symbol"]),
        "research_only":True,
        "new_model_deployed":False,
    }
    scoring.validate_replay(window,out,universe)
    return out


def selftest():
    assert shard_no("CATUSDT")==shard_no("CATUSDT")
    assert shard_no("CATUSDT") in range(SHARDS)
    assert len({str(i) for i in range(SHARDS)})==24
    missing=absent("CATUSDT",scoring.WINDOWS[0],FileNotFoundError("404"))
    assert missing["D0_first_UTC"] is None
    assert missing["source_status"].startswith("CENSORED")
    assert "stage117_new_first_D0_candidate" not in missing
    try:aggregate_shards({},scoring.WINDOWS[0],[])
    except ValueError as ex:assert "EXACT_ALL24" in str(ex)
    else:raise AssertionError("STAGE116_ALLOW_MISSING_UNIVERSE_SHARDS")
    print("STAGE116_OFFICIAL_ONE_SHOT_24_SHARDS_RESEARCH_ONLY_TEST_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest",action="store_true")
    ap.add_argument("--snapshot-file",type=Path)
    ap.add_argument("--window",choices=list(scoring.WINDOWS))
    ap.add_argument("--shard",type=int)
    ap.add_argument("--workers",type=int,default=3)
    ap.add_argument("--aggregate-dir",type=Path)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    if args.selftest:
        selftest()
        return
    if args.snapshot_file is None or args.window is None or args.out is None:
        ap.error("--snapshot-file --window --out required, no live capture enabled")
    snapshot=json.loads(args.snapshot_file.read_text())
    if args.aggregate_dir is not None:
        allparts=[]
        for i in range(SHARDS):
            f=args.aggregate_dir/("monster-stage116-"+args.window[:10]+f"-s{i}.json")
            if not f.is_file():
                raise ValueError("STAGE116_MISSING_EXACT_ARCHIVE_SHARD "+str(i))
            allparts.append(json.loads(f.read_text()))
        result=aggregate_shards(snapshot,args.window,allparts)
    else:
        if args.shard is None:ap.error("--shard required for research replay")
        result=source_shard(snapshot,args.window,args.shard,args.workers)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("STAGE116_OFFLINE_OFFICIAL_UNIVERSE_REPLAY "+
          json.dumps({"window":args.window,"rows":len(result["rows"]),
                      "read_only":True,"deployment":"NO_GO"}))


if __name__=="__main__":
    main()
