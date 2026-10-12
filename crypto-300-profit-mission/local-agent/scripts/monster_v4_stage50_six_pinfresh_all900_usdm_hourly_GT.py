#!/usr/bin/env python3
"""Stage50 independently frozen source-only six date all900 USD-M true 1h GT.

Reuse established Stage44 official Binance USD-M month SHA parser and 168h
continuous hour GT engine; don't rewrite market/OHLC logic to get prettier GT.
No reading of next-stage minute model results, no threshold adjustment or BUY.
"""
from __future__ import annotations
import argparse,collections,concurrent.futures,json
from pathlib import Path
try:
    import monster_v4_stage44_six_blind_hourly_truth as orig44
    import monster_v4_stage38_usdm_original_v4_1m_pilot as sha
except ImportError:
    from scripts import monster_v4_stage44_six_blind_hourly_truth as orig44
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as sha

EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
PRE=EVIDENCE/"monster_stage49_v03_second_ignition_strategy_and_holdout_prereg_20261012.json"
EXPOSURE=EVIDENCE/"monster_stage49_frozen_after_stage48_exposure_and_new_dates.json"
INVENTORY=EVIDENCE/"monster_stage36_official_usdm_archive_vs_spot758.json"
DATES=("2025-01-30","2025-06-02","2025-08-01","2025-10-02","2026-06-21","2026-07-28")
SCHEMA="MONSTER_STAGE50_NEW_FROZEN_STAGE49_900x6_BINANCE_PUBLISHER_SHA_TRUE_HOURLY_GT_V1"

def locked():
    prereg=json.loads(PRE.read_text(encoding="utf-8"))
    ledger=json.loads(EXPOSURE.read_text(encoding="utf-8"))
    if (prereg["schema"]!="MONSTER_STAGE49_V03_SECOND_IGNITION_PRIOR_TO_NEW_USDM_MARKET_PRICE_PREREG_V1" or
        tuple(prereg["dates"])!=DATES or
        sha.blob(EXPOSURE)!=prereg["exposure_source_git_blob_sha1"] or
        sha.blob(INVENTORY)!=prereg["original_inventory_blob_sha1"] or
        ledger["selection"]["holdout_selected_blind_by_hashed_date_only"]!=list(DATES) or
        ledger["market_data_queried_in_this_run"]!=False):
        raise ValueError("STAGE50_FROZEN_DATE_SOURCE_PREREG_OR_UNIVERSE_DRIFT")
    inv=json.loads(INVENTORY.read_text(encoding="utf-8"))
    syms=sorted(x["symbol"] for x in inv["source_rows"] if x["archive_symbol_class"]=="EXACT_PLAIN_USDT_ARCHIVED")
    if len(syms)!=900 or len(set(syms))!=900:raise ValueError("STAGE50_NOT_ORIGINAL900")
    return syms

def research(day,shard,workers=4):
    syms=locked()
    if day not in DATES or shard not in range(6) or workers not in (1,2,3,4):
        raise ValueError("STAGE50_SHARD_OR_FROZEN_DATE_INVALID")
    sample=[s for i,s in enumerate(syms) if i%6==shard]
    if len(sample)!=150:raise ValueError("STAGE50_MISSING_SYMBOLS")
    values=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        tasks={pool.submit(orig44.eval_coin,s,day):s for s in sample}
        for task in concurrent.futures.as_completed(tasks):
            s=tasks[task]
            try:
                r=task.result()
                if (r["date"],r["symbol"])!=(day,s):
                    raise ValueError("STAGE50_WRONG_RESULT_IDENTITY")
                values.append(r)
            except Exception as e:
                errors.append({"symbol":s,"error":type(e).__name__+":"+str(e)[:180]})
    if errors or len(values)!=150:raise RuntimeError("STAGE50_SOURCE_FAILURE_CLOSED "+json.dumps(errors[:8]))
    counts=collections.Counter(r["source_status"] for r in values)
    complete=[r for r in values if r["source_status"]=="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA"]
    return {"schema":SCHEMA,"date":day,"shard":shard,"all_original_900_symbols":True,
      "status_counts":dict(counts),"source_verified":len(complete),
      "gt2x":sum(x["gt2x"] for x in complete),
      "gt5x":sum(x["gt5x"] for x in complete),
      "gt10x":sum(x["gt10x"] for x in complete),
      "rows":sorted(values,key=lambda x:x["symbol"]),
      "no_prior_GT_based_symbol_selection":True,"new_priority_rule":"P1V03_FROZEN_NOT_TESTED",
      "Monster_deployment":"NO_GO","Gmail":"OFF","Frank":"UNCHANGED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--date");p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:
        orig44.test()
        assert DATES[0]=="2025-01-30" and len(DATES)==6
        print("STAGE50_OFFICIAL_MONTHLY_SHA_CROSSMONTH_REUSABLE_GT_SELFTEST_PASS")
        return
    if not a.date or a.shard is None or not a.out:p.error("--date --shard --out required")
    result=research(a.date,a.shard,a.workers)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print("STAGE50_ALL900_BLIND_OFFICIAL_SOURCE_SHA_GT "+json.dumps({
        k:result[k] for k in ("date","shard","source_verified","gt2x","gt5x","gt10x")},sort_keys=True))
if __name__=="__main__":main()
