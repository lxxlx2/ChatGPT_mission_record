#!/usr/bin/env python3
"""Append 239E mixed round signs without miscounting 23x19 economic cells."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4c-23x19-crosswallet-native-verified-matrix-2026-10-15.json","39c94ce57937c00528523607c0b3e7e0c20b3693"),("bsc-meme-address-model-v1-p4c-239e-dragon-two-owner-native-settlements-2026-10-15.json","46e90123b98d5324e05388b17b8a3bbb77cb5361"),("bsc-meme-address-model-v1-p4c-877af-marscoin-inventory-closed-quote-unresolved-2026-10-15.json","c116dce9823dff338d887bef07f3ebfd0c8c4adc"))
SCOPE="Freeze original 23x19 and append-only 239E same original 2026 Dragon CA positive and negative buy-sale rounds, 5 source-proven native economic *rounds* but only 4 original owner×CA cells reviewed; 433 other wallet×CA cells unreviewed. 877AF MARSCOIN 2 original quantity-closed source controls remain economic UNKNOWN, not included. Fees actual owner native balance inclusive but 239E route residual fee recipient not attributed. Still no profitable wallet rank, no observer U and no lag follow signal."
MIXED="MIXED_ORIGINAL_NATIVE_ROUNDS_POSITIVE_AND_NEGATIVE"
NA="NOT_ECONOMICALLY_AUDITED"

def require(x,msg):
    if not x:raise ValueError(msg)
def blob_sha(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def load(root=ROOT):
    a=[]
    for n,h in PINS:
        raw=(root/n).read_bytes()
        require(blob_sha(raw)==h,"original source blob drift "+n)
        a.append(json.loads(raw))
    return a
def build(d):
    require(len(d)==3,"3 original source groups required")
    base,owner,partial=d
    old=base["summary"];s=owner["summary"];u=partial["summary"]
    require(base["schema"]=="BSC_P4C_23WALLET_19MAJOR_NATIVE_SETTLED_CROSS_OWNER_ECONOMIC_SNAPSHOT"
            and old["implicit_wallet_CAs"]==437
            and old["verified_native_positive_rounds"]==2
            and old["verified_native_negative_rounds"]==1
            and old["not_economically_audited_cells"]==434
            and len(base["wallets"])==23 and len(base["markets"])==19
            and s["original_closed_owner_rounds"]==2
            and s["complete_success_receipts"]==5
            and s["owner_native_original_profit_rounds"]==s["owner_native_original_loss_rounds"]==1
            and u["original_rounds"]==2
            and u["raw_owner_full_token_quantity_closed"]==2
            and u["receipt_truncated"]==6
            and u["original_real_BNB_winner_rounds_newly_qualified"]==0
            and old["production"]==s["production"]==u["production"]=="NO_GO",
            "unapproved upgrade of original 23x19 economic universe")
    rounds=[]
    for i,r in enumerate(base["verified_economic_rounds"]):
        require(int(r["net_wei"])!=0,"original economic sign vanished")
        rounds.append({**r,"economic_round_key":"ORIGINAL_P4C_VERIFIED_"+str(i),
                       "source_grade":"SETTLED_OWNER_NATIVE_ORIGINAL",
                       "source_status":"SOURCE_VERIFIED_OWNER"})
    require(len(rounds)==3,"base 3 original native economic rounds required")
    for r in owner["rounds"]:
        require(r["token"]=="龙虾" and r["owner"]=="0x239e74bfbd02d71cdc70fecc2d505dc13acfb337"
                and r["token_received_raw"]==r["token_sold_raw"] and
                r["token_inventory_residual_raw"]=="0" and
                r["source_status"]=="OWNER_NATIVE_BNB_CLOSED_WITH_UNNAMED_ROUTE_COST"
                and r["not_claimed"]=="PROTOCOL_FEE_SEMANTICS_UNKNOWN_AND_FOLLOWER_UNTESTED"
                and len(r["txs"])>=2
                and all(x["complete_receipt"] and x["original_owner_single_external_tx_in_block"]
                        and x["other_external_native_deposit_absent"] and int(x["observed_router_cost_residual_wei"])>=0
                        for x in r["txs"]),
                "new 239E original native economics not source eligible")
        require(int(r["original_native_wallet_net_wei"])>0 if r["p2_ledger_index"]==30 else
                int(r["original_native_wallet_net_wei"])<0 and r["p2_ledger_index"]==29,
                "mixed 239E original loss/profit not preserved")
        buys=[x for x in r["txs"] if x["action"]=="BUY"]
        sells=[x for x in r["txs"] if x["action"]=="SELL"]
        require(buys and sells,"not an original signed complete round")
        rounds.append({
            "wallet":r["owner"],"exact_CA":r["exact_CA"],"token":r["token"],
            "quote":"BNB_NATIVE_WITH_WBNB_ROUTE_COST_RESIDUAL",
            "net_wei":r["original_native_wallet_net_wei"],
            "classification":"SIGNED_OWNER_NATIVE_POSITIVE_ROUTE_RESIDUAL_OBSERVED"
              if r["native_original_EOA_profit_sign"]=="POSITIVE"
              else "SIGNED_OWNER_NATIVE_NEGATIVE_ROUTE_RESIDUAL_OBSERVED",
            "buy_tx":buys[0]["hash"],"sell_txs":[x["hash"] for x in sells],
            "economic_round_key":"P2_"+str(r["p2_ledger_index"]),
            "source_grade":"SIGNED_COMPLETE_RECEIPTS_WBNB_NATIVE_WITH_UNNAMED_ROUTE_COST",
            "source_status":"SOURCE_VERIFIED_OWNER_WITH_FEE_SEMANTICS_UNRESOLVED"
        })
    wallets=[]
    seen=False
    for w in base["wallets"]:
        row={**w,"closed_native_round_flags":w["closed_native_round_flags"].copy()}
        if w["wallet"]==owner["rounds"][0]["owner"]:
            matches=[m for m in base["markets"] if m["exact_CA"]==owner["rounds"][0]["exact_CA"]]
            require(len(matches)==1,"same CA not in original frozen 19")
            idx=matches[0]["i"]
            require(row["closed_native_round_flags"][idx]==NA,"already economically audited 239E Dragon")
            row["closed_native_round_flags"][idx]=MIXED
            seen=True
        wallets.append(row)
    require(seen,"239E original owner not in frozen 23")
    total_flags=[x for w in wallets for x in w["closed_native_round_flags"]]
    require(len(total_flags)==437 and total_flags.count(NA)==433 and
            total_flags.count(MIXED)==1,"no unreviewed sample may silently become profitable")
    unresolved=[]
    for x in partial["rounds"]:
        require(x["remaining_token_inventory_raw"]=="0" and
                x["economic_status"]=="OWNER_TOKEN_CLOSE_BUT_NONNATIVE_QUOTE_GAS_UNRESOLVED" and
                not x["qualified_realized_net_profit"] and x["owner"]=="0x877af245c61289b24f0c619a4346cdbc68f1aaac",
                "877AF original MARSCOIN economic unknown falsely upgraded")
        unresolved.append({
           "wallet":x["owner"],"exact_CA":x["exact_CA"],"token":x["token"],
           "p2_ledger_index":x["p2_ledger_index"],
           "remaining_token_inventory_raw":x["remaining_token_inventory_raw"],
           "status":x["economic_status"]
        })
    require(len(rounds)==5 and sum(int(x["net_wei"])>0 for x in rounds)==3
            and sum(int(x["net_wei"])<0 for x in rounds)==2,
            "original 5 source-proven P4-C signed economic round signs changed")
    return {
       "schema":"BSC_P4C_23X19_FIVE_SOURCE_SETTLED_ROUNDS_DISTINCT_CELL_DENOMINATOR",
       "scope":SCOPE,
       "source_manifest":[{"path":PREFIX+n,"git_blob_sha":h} for n,h in PINS],
       "summary":{
          "frozen_wallets":23,"frozen_major_exact_CAs":19,"total_wallet_CA_cells":437,
          "source_verified_original_native_rounds":5,
          "verified_native_positive_original_rounds":3,
          "verified_native_negative_original_rounds":2,
          "reviewed_distinct_wallet_CA_cells":4,
          "not_economically_audited_cells":433,
          "wallets_with_positive_original_rounds":2,
          "wallets_with_both_positive_and_negative_original_rounds":1,
          "wallets_with_profitable_original_rounds_in_two_distinct_major_CA":1,
          "existing_recent_signed_swap_wallets":7,
          "original_MARSCOIN_inventory_closed_but_profit_unknown_rounds":2,
          "public_observer_follower_qualified_signals":0,
          "profit_rank_ready":False,"production":"NO_GO"
       },
       "markets":base["markets"],"wallets":wallets,
       "verified_economic_rounds":rounds,"unresolved_economic_controls":unresolved
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
