#!/usr/bin/env python3
"""Stage23: NEW 10-day first-D1 quality-with-overextension filter holdout.

Existing V4 D0/D1 and Stage20 entry/stop/exit are unchanged and Git-blob-locked.
Single new rule (quality AND BTC-relative 60m <=12 pp) was preregistered
BEFORE reading any of the ten new calendar windows. No live actions.
"""
import argparse
import concurrent.futures
import hashlib
import json
import statistics
import sys
from collections import Counter
from datetime import date
from pathlib import Path

try:
    import monster_v4_stage20_quality_exit_holdout as previous
except ImportError:
    from scripts import monster_v4_stage20_quality_exit_holdout as previous

PREREG=previous.archive.source.EVIDENCE/"monster_stage23_unseen_overextension_filter_prereg_20261011.json"
SOURCE=Path(previous.__file__).resolve()
WORKERS=8

def frozen():
    config=json.loads(PREREG.read_text(encoding="utf-8"))
    if config["schema"]!="MONSTER_STAGE23_NEW_CALENDAR_HOLDOUT_OVEREXTENSION_FROZEN_PRE_DATA_V1":
        raise ValueError("STAGE23_BAD_PREREG_SCHEMA")
    if tuple(config["dates"])!=("2025-01-23","2025-02-23","2025-03-23",
        "2025-04-23","2025-05-23","2025-06-23","2025-07-23",
        "2025-08-23","2025-09-23","2025-10-23"):
        raise ValueError("STAGE23_DATE_DRIFT")
    if (config["experimental_filter"]["threshold_pp"]!=12.0 or
            config["universe"]["all_symbols"]!=758):
        raise ValueError("STAGE23_FILTER_OR_UNIVERSE_CHANGED")
    raw=SOURCE.read_bytes()
    sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if sha!=config["code_lock"]["prior_stage20_script_git_blob_sha1"]:
        raise ValueError("STAGE23_STAGE20_CODE_CHANGED")
    previous.frozen_manifest()
    return config,sha

def apply_filter(row):
    # Never modify original D0 WATCH/D1 event result, only simulator eligibility.
    if row["status"]!="COMPLETE_60H" or "arm_proxies" not in row:
        return dict(row)
    out=dict(row)
    qualified=row["quality"]["quality_pass"]
    relative=row["quality"]["relative_60m_return_pp"]
    if not isinstance(relative,(int,float)):
        raise ValueError("STAGE23_UNKNOWN_RELATIVE_STRENGTH")
    selected=qualified and relative<=12
    out["overextension_eligible"]=selected
    out["overextension_reject_causes"]=(["PREVIOUS_QUALITY_REJECTED"] if not qualified else
        (["BTC_RELATIVE_60M_GT_12PP"] if not selected else []))
    arm=row["arm_proxies"]
    out["frozen_arm_proxies"]={
      "D_BASELINE_STAGE20_QUALITY_BOUNDED6H_20BPS":
         arm["D_QUALITY_D1_BOUNDED_6H_20BPS"],
      "F_OVEREXTENSION_FILTER_QUALITY_BOUNDED6H_20BPS":
         arm["D_QUALITY_D1_BOUNDED_6H_20BPS"] if selected else None,
      "G_OVEREXTENSION_FILTER_QUALITY_BOUNDED6H_100BPS":
         arm["E_QUALITY_D1_BOUNDED_6H_100BPS"] if selected else None
    }
    return out

def stats(rows):
    valid=[r for r in rows if r["status"]=="COMPLETE_60H"]
    d1=[r for r in valid if "arm_proxies" in r]
    out={"attempted":len(rows),
      "status":dict(Counter(r["status"] for r in rows)),
      "complete_60h":len(valid),
      "v4_watch_events":sum(r["v4_watch"] for r in valid),
      "v4_d1_events":sum(r["v4_d1_episodes"] for r in valid),
      "unique_first_d1":len(d1),
      "original_quality_selected":sum(r["quality"]["quality_pass"] for r in d1),
      "new_filter_selected":sum(r["overextension_eligible"] for r in d1),
      "new_filter_rejection_reasons":dict(Counter(k for r in d1
                   for k in r["overextension_reject_causes"]))}
    names=("D_BASELINE_STAGE20_QUALITY_BOUNDED6H_20BPS",
           "F_OVEREXTENSION_FILTER_QUALITY_BOUNDED6H_20BPS",
           "G_OVEREXTENSION_FILTER_QUALITY_BOUNDED6H_100BPS")
    for name in names:
        p=[r["frozen_arm_proxies"][name] for r in d1
            if r["frozen_arm_proxies"][name] is not None]
        v=[x["net_pct"] for x in p if x["status"]=="PRICE_PROXY_ONLY"]
        out[name]={"selected":len(p),"evaluated":len(v),
                   "wins":sum(x>0 for x in v),"losses":sum(x<0 for x in v),
                   "net_median_pct":round(statistics.median(v),6) if v else None,
                   "net_mean_pct":round(statistics.mean(v),6) if v else None,
                   "pnl_sum_assumed_independent_30u":round(sum(vv*.30 for vv in v),6),
                   "censored":len(p)-len(v),
                   "exit_reasons":dict(Counter(x.get("exit_reason") for x in p
                                         if x["status"]=="PRICE_PROXY_ONLY"))}
    missed=[r for r in d1 if r["quality"]["quality_pass"] and not r["overextension_eligible"]
            and r["frozen_arm_proxies"][names[0]] is not None
            and r["frozen_arm_proxies"][names[0]]["status"]=="PRICE_PROXY_ONLY"]
    out["rejected_evaluable_original_quality"]={
        "count":len(missed),"would_stop":sum(r["frozen_arm_proxies"][names[0]]["exit_reason"]=="STOP" for r in missed),
        "would_take_profit":sum(r["frozen_arm_proxies"][names[0]]["exit_reason"]=="TAKE_PROFIT" for r in missed),
        "would_timeout":sum(r["frozen_arm_proxies"][names[0]]["exit_reason"]=="TIMEOUT_6H" for r in missed),
        "would_profit_net":sum(r["frozen_arm_proxies"][names[0]]["net_pct"]>0 for r in missed)}
    return out

def run(day_string,worker=previous.run_symbol,
        source_get=previous.official_60h,workers=WORKERS):
    cfg,sha=frozen()
    if day_string not in cfg["dates"]:
        raise ValueError("STAGE23_NONFROZEN_DATE")
    if not 1<=workers<=WORKERS:
        raise ValueError("STAGE23_UNSAFE_CONCURRENCY")
    syms,inv=previous.universe(previous.frozen_manifest())
    day=date.fromisoformat(day_string)
    btc,btc_proof=source_get("BTCUSDT",day)
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(worker,s,day,btc):s for s in syms}
        for future in concurrent.futures.as_completed(futures):
            row=future.result()
            if row.get("symbol")!=futures[future]:
                raise ValueError("STAGE23_IDENTITY_CHANGED")
            results.append(apply_filter(row))
            if len(results)%100==0:
                print("STAGE23_PROGRESS "+json.dumps({
                    "date":day_string,"processed":len(results),"attempted":758}),
                    file=sys.stderr,flush=True)
    results.sort(key=lambda x:x["symbol"])
    if len(results)!=758:
        raise ValueError("STAGE23_INCOMPLETE_FROZEN_UNIVERSE")
    return {"schema":"MONSTER_STAGE23_FROZEN_NEW_DATES_FIRST_D1_OVEREXTENSION_V1",
        "date":day_string,"source":"BINANCE_SPOT_DAILY_1M_PUBLISHER_SHA256",
        "unchanged_stage20_git_blob":sha,"archive_only_symbol_sha256":inv["archive_only_sha256"],
        "btc_daily_source":btc_proof,"summary":stats(results),"cases":results,
        "experiment_only":True,"independent_other_ai_review":"NOT_DONE",
        "deployment":"NO_GO","gmail":False,"trading":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--date",required=True)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    data=run(args.date)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE23_RESULT_JSON "+json.dumps(data["summary"],sort_keys=True),flush=True)
    if data["summary"]["complete_60h"]<100:
        raise SystemExit("STAGE23_INCOMPLETE_HISTORY")
    if any(data["summary"]["status"].get(s) for s in (
       "SOURCE_NETWORK_FAILED","SOURCE_HTTP_FAILURE","SOURCE_INTEGRITY_REJECTED")):
        raise SystemExit("STAGE23_SOURCE_INTEGRITY_OR_NETWORK_FAILURE")
if __name__=="__main__":
    main()
