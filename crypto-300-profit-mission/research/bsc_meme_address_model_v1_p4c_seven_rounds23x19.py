#!/usr/bin/env python3
"""Correct frozen 23 x 19 denominator: 7 native owner rounds ≠ 7 CA cells.

P2 #16/#17 8E6B token4 occurred in 2025 and remain one MIXED wallet-CA
cell; never silently reclassify as independent 2026 winners or P5 alpha.
"""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4c-23x19-five-native-rounds-mixed239e-2026-10-15.json","7ef825b5e56071687dadbf24d3b4327724e0d831"),("bsc-meme-address-model-v1-p4c-8e6b-token4-two-settled-source-audit-2026-10-15.json","1d085883201da6bbbf47185df60898c0ec8eead1"))
SCOPE="Original 23 × 19 frozen selected research; append source frozen 8E6B original token4 (two 2025 actual signed trades rounds: loss then gain) to source-proven 2026-era major sample Stage4 P2. Unique wallet×CA denominator counts one mixed 8E6B token4 cell, not 2 winners; 7 native owner economic rounds across 5 audited cells, 432 cells not same-grade audited. 2025 stage4 profits must not be represented as 2026 or real-time recommendations. 19 source proof signer success, five independent live receipt, native N-1/N, paid gas and WBNB, route difference not attributed. Profit rank and follower U and P5 remain NO_GO."
NOT_AUDITED="NOT_ECONOMICALLY_AUDITED"
MIXED="MIXED_ORIGINAL_NATIVE_ROUNDS_POSITIVE_AND_NEGATIVE"
def ensure(condition,msg):
    if not condition:raise ValueError(msg)
def sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def load(root=ROOT):
    out=[]
    for name,h in PINS:
        b=(root/name).read_bytes()
        ensure(sha(b)==h,"source Git blob drift "+name)
        out.append(json.loads(b))
    return out
def build(d):
    ensure(len(d)==2,"original five-round matrix and original two token4 rounds required")
    old,token=d
    s=old["summary"];t=token["summary"]
    ensure(old["schema"]=="BSC_P4C_23X19_FIVE_SOURCE_SETTLED_ROUNDS_DISTINCT_CELL_DENOMINATOR"
           and (s["frozen_wallets"],s["frozen_major_exact_CAs"],s["total_wallet_CA_cells"])==(23,19,437)
           and (s["source_verified_original_native_rounds"],s["verified_native_positive_original_rounds"],s["verified_native_negative_original_rounds"])==(5,3,2)
           and (s["reviewed_distinct_wallet_CA_cells"],s["not_economically_audited_cells"])==(4,433)
           and len(old["wallets"])==23 and len(old["markets"])==19
           and token["schema"]=="BSC_P4C_8E6B_TOKEN4_TWO_SETTLED_OWNER_NATIVE_ROUNDS_19TX_FIVE_SPOT"
           and (t["original_native_economic_rounds"],t["original_owner_signed_successful_txs"],t["independently_rechecked_full_transactions"])==(2,19,5)
           and (t["original_native_positive_rounds"],t["original_native_negative_rounds"])==(1,1)
           and [r["p2_index"] for r in token["rounds"]]==[16,17]
           and [r["original_tx_count"] for r in token["rounds"]]==[2,17]
           and s["production"]==t["production"]=="NO_GO",
           "frozen original denominator or signed original stage24 source grade drift")
    owner=token["rounds"][0]["wallet"];ca=token["rounds"][0]["exact_CA"]
    ensure(owner=="0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0"
           and ca=="0x0a43fc31a73013089df59194872ecae4cae14444"
           and len(token["original_transactions"])==19
           and len({x["hash"] for x in token["original_transactions"]})==19,
           "single 2025 major Meme token4 and exact 19 immutable transactions required")
    found=[x for x in old["markets"] if x["exact_CA"]==ca]
    ensure(len(found)==1,"token4 CA not in original 19 frozen universe")
    ix=found[0]["i"]
    wallets=[]
    for w in old["wallets"]:
        entry={**w,"closed_native_round_flags":w["closed_native_round_flags"].copy()}
        if w["wallet"]==owner:
            ensure(entry["closed_native_round_flags"][ix]==NOT_AUDITED,
                   "8E6B token4 not previously audited? double-count forbidden")
            entry["closed_native_round_flags"][ix]=MIXED
        wallets.append(entry)
    ensure(any(w["wallet"]==owner for w in wallets),"original wallet absent from 23")
    table=[v for w in wallets for v in w["closed_native_round_flags"]]
    ensure(len(table)==437 and table.count(NOT_AUDITED)==432 and table.count(MIXED)==2,
           "wallet×major_CA denominator falsely counts same-owner repeated rounds")
    combined=[{**r} for r in old["verified_economic_rounds"]]
    ensure(len(combined)==5,"five prior separate original signed outcomes must survive")
    for v in token["rounds"]:
        index=v["p2_index"]
        orig=[x for x in token["original_transactions"] if x["p2_index"]==index]
        buy=[x for x in orig if x["direction"]=="in"]
        sell=[x for x in orig if x["direction"]=="out"]
        net=int(v["original_owner_native_net_wei"])
        ensure(len(orig)==v["original_tx_count"] and len(buy)==1 and len(sell)==(1 if index==16 else 16)
               and v["original_token_inventory_residual_raw"]=="0"
               and sum(int(x["original_native_delta_wei"]) for x in orig)==net
               and all(x["original_signed_success"] for x in orig)
               and all(int(x["paid_gas_wei"])>0 for x in orig)
               and ((index==16 and net<0 and v["original_owner_economic_sign"]=="NEGATIVE")
                    or (index==17 and net>0 and v["original_owner_economic_sign"]=="POSITIVE"))
               and v["observer_followable_profit"]=="UNRESOLVED",
               "loss and win must both be real original BNB signed cashflow, not follower")
        combined.append({
          "wallet":owner,"exact_CA":ca,"token":"4",
          "quote":"BNB_NATIVE_WITH_WBNB_RECEIPTS_ROUTE_FEE_RESIDUAL",
          "net_wei":str(net),
          "classification":"SIGNED_OWNER_NATIVE_POSITIVE_ROUTE_RESIDUAL_OBSERVED"
                           if net>0 else "SIGNED_OWNER_NATIVE_NEGATIVE_ROUTE_RESIDUAL_OBSERVED",
          "buy_tx":buy[0]["hash"],
          "sell_txs":[x["hash"] for x in sell],
          "economic_round_key":"P2_"+str(index),
          "source_grade":"SIGNED_ORIGINAL_COMPLETE_RECEIPTS_WBNB_GAS_WITH_FIVE_LIVE_SPOT_CHECKS",
          "source_status":"SOURCE_VERIFIED_OWNER_WITH_FEE_SEMANTICS_UNRESOLVED"
        })
    ensure(len(combined)==7
           and sum(int(r["net_wei"])>0 for r in combined)==4
           and sum(int(r["net_wei"])<0 for r in combined)==3,
           "7 selected original signed round outcomes cannot change")
    return {"schema":"BSC_P4C_23X19_SEVEN_SETTLED_ROUNDS_FIVE_ECONOMIC_CELLS",
       "scope":SCOPE,
       "source_manifest":[{"path":PREFIX+n,"git_blob_sha":h} for n,h in PINS],
       "summary":{
          "frozen_wallets":23,"frozen_major_exact_CA_count":19,
          "total_wallet_CA_cells":437,"source_verified_original_native_rounds":7,
          "verified_native_positive_original_rounds":4,
          "verified_native_negative_original_rounds":3,
          "reviewed_distinct_wallet_CA_cells":5,
          "not_economically_audited_cells":432,
          "wallets_with_positive_original_rounds":2,
          "wallets_with_both_positive_and_negative_original_rounds":2,
          "wallets_with_profitable_original_rounds_in_three_distinct_major_CA":1,
          "source_2025_token4_original_mixed_rounds":2,
          "source_2026_token4_followable_signals":0,
          "original_MARSCOIN_inventory_closed_but_profit_unknown_rounds":2,
          "public_observer_follower_qualified_signals":0,
          "profit_rank_ready":False,"production":"NO_GO"
       },
       "markets":old["markets"],"wallets":wallets,
       "verified_economic_rounds":combined,
       "unresolved_economic_controls":old["unresolved_economic_controls"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
