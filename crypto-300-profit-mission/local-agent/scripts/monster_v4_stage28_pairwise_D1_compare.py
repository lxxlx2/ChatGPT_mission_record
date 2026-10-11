#!/usr/bin/env python3
"""Stage28 exact per-event D1 reconciliation, SHA-gated original 36+6 ZIPs.

Survivor/known-winner selection is prohibited. Compare all 826 historical
per-symbol V4 SETUP UTCs with all real production shared-queue SETUP UTCs.
A delayed D1 is not described as a permanently lost economic trade.
"""
import argparse
import collections
import json
import zipfile
from pathlib import Path

try:
    import monster_v4_stage27_shared_queue_cash_ledger as original
    import monster_v4_stage28_aggregate as shared
except ImportError:
    from scripts import monster_v4_stage27_shared_queue_cash_ledger as original
    from scripts import monster_v4_stage28_aggregate as shared

EVIDENCE=original.EVIDENCE
OLD_PROOF=original.previous.PROOF
NEW_PROOF=shared.PROOF

def old_source_cases(archives):
    all_rows=original.original_cases(archives)
    return all_rows

def shared_reports(archives):
    index=json.loads(NEW_PROOF.read_text(encoding="utf-8"))
    bydate={x["date"]:x for x in index["artifacts"]}
    if len(archives)!=6 or set(bydate)!=set(shared.DATES):
        raise ValueError("STAGE28B_NOT_ALL_FROZEN_SHARED_DAY_FILES")
    out={}
    for p in archives:
        with zipfile.ZipFile(p) as z:
            members=z.namelist()
        if len(members)!=1:raise ValueError("STAGE28B_EXTRA_ARTIFACT_MEMBERS")
        day=members[0].removeprefix("monster_stage28_").removesuffix("_real_shared_sqlite.json")
        if day not in bydate or day in out:raise ValueError("STAGE28B_DUPLICATE_SHARED_DAY")
        out[day]=shared.read_artifact(p,bydate[day])
    return out

def compare(old_rows,new_rows):
    original_exact={}
    for x in old_rows:
        if x["status"]!="COMPLETE_168H_CONTINUOUS_V4":
            continue
        for utc in x["continuous"]["setup_utcs"]:
            key=(x["date"],x["symbol"],utc)
            if key in original_exact:raise ValueError("STAGE28B_DUPLICATE_INDIVIDUAL_SETUP")
            source_watch=x["continuous"]["watch_utcs"]
            proxy=[p for p in x["continuous"]["trade_proxies"] if p["watch_utc"] in source_watch]
            original_exact[key]={"date":x["date"],"symbol":x["symbol"],"original_setup_utc":utc,
                                 "original_watch_utc":source_watch,
                                 "watch_trade_20bps_price_proxy":proxy}
    shared_exact={}
    queue_by_symbol={}
    for day,obj in new_rows.items():
        for q in obj["queue_final"]:
            key=(day,q["symbol"])
            queue_by_symbol.setdefault(key,[]).append(q)
        for setup in obj["setups"]:
            key=(day,setup["symbol"],setup["utc"])
            if key in shared_exact:raise ValueError("STAGE28B_DUPLICATE_SHARED_SETUP")
            shared_exact[key]={"date":day,"symbol":setup["symbol"],
                               "shared_setup_utc":setup["utc"]}
    left=set(original_exact)-set(shared_exact)
    right=set(shared_exact)-set(original_exact)
    matched=set(original_exact)&set(shared_exact)
    missing=[]
    new=[]
    for k in sorted(left):
        data=original_exact[k]
        same_symbol=[x["utc"] for x in new_rows[k[0]]["setups"] if x["symbol"]==k[1]]
        source_proxies=[]
        for watch in data["watch_trade_20bps_price_proxy"]:
            v=watch.get("proxy_20bps")
            source_proxies.append({"watch_utc":watch["watch_utc"],
                  "status":v["status"] if v else None,
                  "net_pct":v.get("net_pct") if v else None})
        missing.append({"date":k[0],"symbol":k[1],"old_D1_utc":k[2],
           "new_same_symbol_D1_times":same_symbol,
           "latest_shared_queue_state":queue_by_symbol.get((k[0],k[1]),[]),
           "watch_24h_20bps_price_proxies":source_proxies})
    for k in sorted(right):
        new.append({"date":k[0],"symbol":k[1],"shared_D1_utc":k[2],
           "old_same_symbol_D1_times":[old_key[2] for old_key in original_exact if old_key[:2]==k[:2]]})
    if len(original_exact)!=826 or len(shared_exact)!=828:
        raise ValueError("STAGE28B_ORIGINAL_826_OR_SHARED_828_CHANGED")
    return {
      "schema":"MONSTER_STAGE28_EXACT_REAL_D1_826_VS_828_EVENT_RECONCILIATION_V1",
      "all_original_36_and_shared_6_ZIP_JSON_SHA_REVERIFIED":True,
      "old_individual_D1_count":len(original_exact),
      "new_real_shared_D1_count":len(shared_exact),
      "exact_symbol_timestamp_intersection":len(matched),
      "original_only_count":len(left),"shared_only_count":len(right),
      "original_only_events":missing,"shared_only_events":new,
      "not_full_shared_global_D0":True,
      "historical_5m_vs_reconstructed_1m_inconsistency_not_excluded":True,
      "user_money_or_real_orderbook":"NOT_VERIFIED",
      "other_AI_review":"NOT_DONE","deployment":"NO_GO"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stage26-original-zips",nargs=36,required=True,type=Path)
    p.add_argument("--stage28-original-zips",nargs=6,required=True,type=Path)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=compare(old_source_cases(args.stage26_original_zips),
                   shared_reports(args.stage28_original_zips))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE28_PAIRWISE_D1_JSON "+json.dumps({
       k:v for k,v in result.items() if k not in ("original_only_events","shared_only_events")},sort_keys=True),flush=True)
if __name__=="__main__":
    main()
