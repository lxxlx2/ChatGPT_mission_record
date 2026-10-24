#!/usr/bin/env python3
"""P4-C verified real positive 8E6B HAJIMI and Dragon 2026 owner rounds.

Only original precommitted full-quantity-inventory episodes can qualify.
Reconcile actual EOA signed tx, successful receipt, ERC20 TOKEN + WBNB,
historical unique wallet N-1/N BNB balances and original paid gas.
No observer-visible U, 1/5/15-minute follower or entire-wallet rank assumed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("BSC_MEME_STAGE23_8E6B_REPEAT_WINNER_HAJIMI_LOBSTER_IFML_CROSS_MAJOR_ROUNDS_2026-10-13.json","6227e69fabd6c0d991add0d7ff5c6e406babd40b"),("bsc-meme-address-model-v1-p4c-sevenwallet-balanced-five-round-precommit-2026-10-15.json","85a39f4c5c9723e98180a1c018b9dd94588fe3b6"),("bsc-meme-address-model-v1-p4c-sevenwallet-owner-tx-part1-2026-10-15.json","a038983867c6cfbad35c1fcd4b070992eba3fe8f"),("bsc-meme-address-model-v1-p4c-sevenwallet-original-receipt-part1-2026-10-15.json","0351062ea8b6290e465412e38d02a7790ae8f9a3"),("bsc-meme-address-model-v1-p4c-sevenwallet-five-round-native-part1-2026-10-15.json","71d8c4549c176fcf9f78002f648d956aedc4a026"))
EOA="0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0"
WBNB="0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
DETAILS=(
    ("8E6B_HAJIMI_R1","哈基米 / HAJIMI","0x82ec31d69b3c289e541b50e30681fd1acad24444"),
    ("8E6B_DRAGON_R2","龙虾","0xeccbb861c0dda7efd964010085488b69317e4444")
)
SCOPE="Two pre-existing frozen P2 8E6B fully inventory-closed 2026 major rounds, HAJIMI and Dragon. Independently re-read exact original EOA tx, 5 complete successful receipts, original CA token + original WBNB transfers, paid gas, 5 unique historical wallet N-1/N balances. All 5 native changes match signed input + gas on buy or WBNB withdrawal - gas on sale exactly, no invented price mark. True positive for these two *selected signed owner rounds*, not owner lifetime PnL, ability to observe entry, or 1/5/15-minute follower execution."

def require(ok,msg):
    if not ok:
        raise ValueError(msg)

def blob_sha(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def load(root=ROOT):
    results=[]
    for name,sha in PINS:
        raw=(root/name).read_bytes()
        require(blob_sha(raw)==sha,"source evidence changed "+name)
        results.append(json.loads(raw))
    return results

def from_log(log,token):
    require(log["topics"][0]==TRANSFER and len(log["topics"])==3,"not an exact ERC20 Transfer")
    require(log["address"].lower()==token,"original quote/token identity changed")
    return ("0x"+log["topics"][1][-40:]).lower(),("0x"+log["topics"][2][-40:]).lower(),int(log["data"],16)

def build(d):
    require(len(d)==5,"original 8E6B five documents required")
    stage,pre,owner,rc,native=d
    require(stage["wallet"]==EOA and stage["production"]=="NO_GO"
            and stage["summary"]["two_selected_rounds_independently_receipt_gas_WBNB_wallet_reconciled"] is True
            and pre["schema"]=="BSC_P4C_SEVEN_RECENT_WALLET_BALANCED_SIGNED_ROUND_BATCH_FROZEN"
            and len(pre["seven_original_wallets"])==7
            and pre["status"]=="FROZEN_BEFORE_FRESH_RPC"
            and owner["part"]==rc["part"]==native["part"]==1
            and owner["precommit_git_blob_sha"]==PINS[1][1]
            and rc["source_precommit_sha"]!="" and native["precommit_sha"]!=""
            and all(x["production"]=="NO_GO" for x in d),
            "frozen 8E6B evidence cohort/provenance incomplete")
    source=[]
    for key,token,CA in DETAILS:
        pick=next((x for x in pre["sample_rounds"] if x["key"]==key and x["wallet"]==EOA and x["ca"]==CA),None)
        require(pick is not None and len(pick["transactions"]) in (2,3),"original cross major preselection drift")
        prior=(stage["HAJIMI_independent_inventory_rounds"][0] if key=="8E6B_HAJIMI_R1" else
               next(x for x in stage["other_major_meme_rounds"] if x["token"]=="龙虾")["rounds"][1])
        signed=next(x for x in stage["selected_two_major_positive_receipt_proofs"] if x["token"]==token)
        require(prior["token_inventory_returned_zero"] and
                prior["native_wallet_block_scope_wei"]==signed["round_wallet_BNB_net_wei"] and
                signed["closed_raw_token_inventory"] and
                signed["settlement_reconciled_all_sells"],
                "P2 exact historical preselected episode inventory or income unresolved")
        txs=[x for x in rc["rows"] if x["source"]["round"]==key]
        own=[x for x in owner["rows"] if x["source"]["round"]==key]
        snaps=[x for x in native["rows"] if x["round"]==key]
        require(len(txs)==len(own)==len(snaps)==len(pick["transactions"])
                and all(x["status"]=="OWNER_SIGNER_COMPLETE" for x in own)
                and all(x["status"]=="SUCCESS_FULL_RECEIPT" for x in txs)
                and all(x["before"]["status"]==x["after"]["status"]=="COMPLETE" for x in snaps),
                "incomplete independent mined receipt/signer/archive evidence")
        purchases,sales=[],[]
        for i,selection in enumerate(pick["transactions"]):
            tx=txs[i]["source"]; own_tx=own[i]["tx"]; rec=txs[i]["receipt"]; block=snaps[i]
            require(selection["tx"]==tx["tx"]==own[i]["source"]["tx"]
                    and selection["block"]==tx["block"]==block["block"]
                    and own_tx["hash"]==selection["tx"]==rec["hash"]
                    and own_tx["from"]==EOA
                    and int(rec["block"],16)==tx["block"]
                    and rec["status"]=="0x1"
                    and block["wallet"]==EOA
                    and block["delta_wei"]==str(int(block["after"]["balance_wei"])-int(block["before"]["balance_wei"])),
                    "mined economic signer block snapshot not the original selected transaction")
            selected=rec["selected_token_transfer_logs"]
            tokenlogs=[v for v in selected if v["address"].lower()==CA]
            wlogs=[v for v in selected if v["address"].lower()==WBNB]
            require(len(tokenlogs)==len(wlogs)==1,"original receipt token-to-WBNB transfer not unique")
            frm,to,tokenraw=from_log(tokenlogs[0],CA)
            quoteFrom,quoteTo,amountWBNB=from_log(wlogs[0],WBNB)
            paid=int(rec["gasUsed"],16)*int(rec["effectiveGasPrice"],16)
            delta=int(block["delta_wei"])
            if i==0:
                signedBNB=int(own_tx["value"],16)
                require(to==EOA and frm!=EOA
                        and signedBNB>0 and amountWBNB>0
                        and delta==-signedBNB-paid,
                        "owner initial buy token receipt not paid from its own signed native balance")
                purchases.append({
                    "hash":selection["tx"],"block":selection["block"],
                    "received_token_raw":str(tokenraw),
                    "sent_signed_native_wei":str(signedBNB),
                    "WBNB_route_to_pool_wei":str(amountWBNB),
                    "native_wallet_balance_change_wei":str(delta),
                    "gas_wei":str(paid)
                })
            else:
                require(frm==EOA and to!=EOA
                        and quoteTo=="0x13f4ea83d0bd40e75c8222255bc855a974568dd4"
                        and amountWBNB>paid and delta==amountWBNB-paid,
                        "owner source sale WBNB→native settlement incomplete")
                sales.append({
                    "hash":selection["tx"],"block":selection["block"],
                    "sold_token_raw":str(tokenraw),
                    "WBNB_to_router_wei":str(amountWBNB),
                    "native_wallet_balance_change_wei":str(delta),
                    "gas_wei":str(paid)
                })
        totalbought=sum(int(x["received_token_raw"]) for x in purchases)
        totalsold=sum(int(x["sold_token_raw"]) for x in sales)
        spent=-sum(int(x["native_wallet_balance_change_wei"]) for x in purchases)
        credited=sum(int(x["native_wallet_balance_change_wei"]) for x in sales)
        net=credited-spent
        require(totalbought==totalsold and totalbought>0
                and net>0 and str(net)==signed["round_wallet_BNB_net_wei"]
                and all(x["hash"] in signed["sell_hashes"] for x in sales),
                "closed owner inventory or economic native return not original selected winning round")
        source.append({
            "round_key":key,"owner":EOA,"token":token,"exact_CA":CA,
            "source_closed_raw_quantity":True,
            "source_original_EOA_all_signed":True,
            "original_receipt_success_all":True,
            "buy":purchases,"sells":sales,
            "original_full_token_bought_raw":str(totalbought),
            "original_full_token_sold_raw":str(totalsold),
            "residual_raw":"0",
            "native_wallet_buy_block_spend_wei":str(spent),
            "native_wallet_sell_block_total_net_credit_wei":str(credited),
            "actual_native_round_net_wei":str(net),
            "actual_native_roi_bps_trunc":net*10000//spent,
            "classification":"SETTLED_OWNER_NATIVE_POSITIVE_WITH_WBNB_GAS",
            "quote":"BNB_NATIVE_WITH_WBNB_SETTLEMENT",
            "owner_observer_follower_1_5_15min":"UNRESOLVED",
            "first_executable_global_U":"UNRESOLVED",
            "production":"NO_GO"
        })
    require(len(source)==2 and len({x["exact_CA"] for x in source})==2,"two distinct positive original 2026 majors required")
    return {
      "schema":"BSC_P4C_8E6B_INDEPENDENT_TWO_MAJOR_WBNB_GAS_CLOSED_OWNER_POSITIVE",
      "scope":SCOPE,
      "source_manifest":[{"path":PREFIX+name,"git_blob_sha":sha} for name,sha in PINS],
      "summary":{
        "owner_wallets":1,"independent_major_CAs":2,
        "source_proven_signed_positive_native_rounds":2,
        "original_full_success_tx_receipts":5,
        "original_historic_native_blocks":5,
        "profit_in_quote":"BNB_NATIVE",
        "source_proven_native_net_sum_wei":str(sum(int(x["actual_native_round_net_wei"]) for x in source)),
        "signed_outcome":"TWO_POSITIVE_NATIVE_SETTLED_ROUNDS",
        "qualified_observer_trades":0,
        "profit_ranking_ready":False,
        "production":"NO_GO"
      },
      "rounds":source
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
