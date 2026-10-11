#!/usr/bin/env python3
"""Stage21: ten NEW frozen historical dates, byte-identical Stage20 rules.

Import unchanged Stage20 risk/quality and production V4 replay. This wrapper
changes ONLY preregistered dates and records source/censoring evidence.
Historical price/cost proxies are NOT real fills. Never trades or emails.
"""
import argparse
import concurrent.futures
import hashlib
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

try:
    import monster_v4_stage20_quality_exit_holdout as previous
except ImportError:
    from scripts import monster_v4_stage20_quality_exit_holdout as previous

EVIDENCE=previous.archive.source.EVIDENCE
MANIFEST=EVIDENCE/"monster_stage21_extended_untouched_dates_prereg_20261011.json"
STAGE20_SCRIPT=Path(previous.__file__).resolve()
WORKERS=8

def frozen_manifest():
    m=json.loads(MANIFEST.read_text(encoding="utf-8"))
    if m.get("schema")!="MONSTER_STAGE21_FIXED_NEW_DATES_UNCHANGED_STAGE20_QUALITY_EXIT_V1":
        raise ValueError("STAGE21_UNKNOWN_PREREGISTRATION")
    if tuple(m["frozen_dates_utc"])!=(
            "2025-03-09","2025-04-09","2025-05-09","2025-06-09",
            "2025-07-09","2025-08-09","2025-09-09","2025-10-09",
            "2026-03-09","2026-06-09"):
        raise ValueError("STAGE21_DATE_DRIFT")
    if m["universe_count"]!=758 or m["archived_universe_sha256"]!=(
            "0c2604d838fc3d7c28d0e8819fde1bb42deb6fb22360182a49c1b82bb6d25348"):
        raise ValueError("STAGE21_UNIVERSE_DRIFT")
    raw=STAGE20_SCRIPT.read_bytes()
    blobhash=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if blobhash!=m["exact_stage20_code_git_blob_sha1"]:
        raise ValueError("STAGE21_PREVIOUS_STRATEGY_CODE_CHANGED")
    if not m["quality_gates_unchanged"]:
        raise ValueError("STAGE21_GATES_CHANGED")
    previous.frozen_manifest()
    return m,blobhash

def run_day(day_str, *, inventory_get=previous.stage15.inventory,
            benchmark_fetch=previous.official_60h,
            worker=previous.run_symbol, workers=WORKERS):
    prereg,locked_hash=frozen_manifest()
    if day_str not in prereg["frozen_dates_utc"]:
        raise ValueError("STAGE21_UNREGISTERED_DATE")
    if not 1<=workers<=WORKERS:
        raise ValueError("STAGE21_BAD_CONCURRENCY")
    cfg=previous.frozen_manifest()
    symbols,inv=previous.universe(cfg,inventory_get)
    # Never apply a returns-based symbol filter; all 758 attempted per date.
    day=date.fromisoformat(day_str)
    btc,btc_proof=benchmark_fetch("BTCUSDT",day)
    result=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        submitted={pool.submit(worker,s,day,btc):s for s in symbols}
        for future in concurrent.futures.as_completed(submitted):
            row=future.result()
            if row.get("symbol")!=submitted[future]:
                raise ValueError("STAGE21_WORKER_SYMBOL_MISMATCH")
            result.append(row)
            if len(result)%100==0:
                print("STAGE21_PROGRESS "+json.dumps(
                    {"date":day_str,"done":len(result),"expected":758}),
                    file=sys.stderr,flush=True)
    result.sort(key=lambda x:x["symbol"])
    summary=previous.summarize(result)
    if summary["attempted"]!=758:
        raise ValueError("STAGE21_INCOMPLETE_UNIVERSE")
    return {
      "schema":"MONSTER_STAGE21_FROZEN_NEW_DATES_EXACT_V4_STAGE20_RULES_V1",
      "date":day_str,
      "locked_prior_strategy_git_blob_sha1":locked_hash,
      "manifest":"monster_stage21_extended_untouched_dates_prereg_20261011.json",
      "official_data":"Binance daily Spot 1m ZIP verified publisher SHA256",
      "btc_verified_source_sha256":btc_proof,
      "symbol_universe_frozen_sha256":inv["archive_only_sha256"],
      "summary":summary,
      "cases":result,
      "no_new_watch":True,"no_trading":True,"no_gmail":True,
      "mac_deployment":"NO_GO",
      "known_limitations":"retrospective isolated days, 2026-10-listed survivorship bias, no actual L2 fills"
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--date",required=True)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    report=run_day(args.date)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    s=report["summary"]
    print("STAGE21_RESULT_JSON "+json.dumps({"date":args.date,"summary":s},sort_keys=True),
          flush=True)
    if s["valid_60h"]<100:
        raise SystemExit("STAGE21_TOO_FEW_COMPLETE_SOURCES")
    if any(s["source_status"].get(k,0) for k in
        ("SOURCE_NETWORK_FAILED","SOURCE_HTTP_FAILURE","SOURCE_INTEGRITY_REJECTED")):
        raise SystemExit("STAGE21_OFFICIAL_SOURCE_FAILURE_OR_INTEGRITY")
if __name__=="__main__":
    main()
