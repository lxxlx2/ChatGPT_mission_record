#!/usr/bin/env python3
"""P4-C exact 8E6B '4' original native economic round replay.

Nineteen existing complete-original-source records are cross-joined with
five new PRESELECTED independently fetched signer/receipt/BNB snapshots.
The two buy-input versus actual WBNB mint gaps are measured, not labelled
to an unproven fee recipient. Owner historical result != follower alpha.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4c-8e6b-token4-two-rounds19-precommit-2026-10-15.json","738da1a4a3dfc9304ee188b326b7d307da50145c"),("bsc-meme-address-model-v1-p4c-8e6b-token4-independent-five-part1-2026-10-15.json","75372f649a8ce75188d41b011df6febe33ecbe84"),("bsc-meme-address-model-v1-p4c-8e6b-token4-independent-five-part2-2026-10-15.json","79a43a6c97085e8e796a8288fffdf175618d26f3"),("BSC_MEME_STAGE24_8E6B_TOKEN4_TWO_ROUNDS_THREE_MAJOR_POSITIVE_COHORT_2026-10-13.json","d56c90eff2d062dbb186f5c89e0f59760d6a8d1c"),("BSC_MEME_8E6B_4_EXACT_SETTLEMENT_RECONCILIATION_2026-10-11.json","69cc2ec8e27d3d8427645cdbfdfe5c8043376fe1"),("BSC_MEME_8E6B_4_ORIGIN_RECEIPT_VERIFICATION_2026-10-11.json","41021e96c0f22023a829e8aae8a460d4752d08ef"))
SCOPE="Existing source-closed historic 8E6B token 4 both original P2 negative/positive episodes. 19 already source-audited original owner signed successful token+WBNB+Gas+native records, 5 independently preselected new RPC transaction/receipt/owner balance spot checks. Buy tx native input vs actual WBNB Deposit differs in 2 spot checks, record raw observed gap not guessed fee beneficiary. Historic owner economic PnL only; potential winner sample is outcome-selected, not public-entry/follower execution or 2026-only recurrence. NOT promoted to globally ranked wallet, observer U/P5 zero, independent review pending."
DEPOSIT="0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c"
WITHDRAW="0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65"
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
def require(ok,msg):
    if not ok:raise ValueError(msg)
def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def load(root=ROOT):
    out=[]
    for name,sha in PINS:
        raw=(root/name).read_bytes()
        require(git_blob(raw)==sha,"immutable exact source blob changed: "+name)
        out.append(json.loads(raw))
    return out
def build(d):
    require(len(d)==6,"six original Git pinned source files required")
    pre,part1,part2,stage,recon,origin=d
    require(pre["schema"]=="BSC_P4C_ORIGINAL_8E6B_TOKEN4_TWO_ROUNDS_19TX_5INDEPENDENT_SPOT_PRECOMMIT_V1"
            and pre["network"]=="bnb-mainnet" and pre["production"]=="NO_GO"
            and pre["production_guard"]=="NO_GO"
            and stage["production"]=="NO_GO"
            and pre["original_wallet"]==stage["wallet"]==origin["wallet"]
            and pre["major_exact_CA"]==stage["first_major_4"]["ca"]
            and pre["model_rank"]=="NOT_RANKED"
            and pre["observer_first_executable_U"]=="UNRESOLVED"
            and part1["part"]==1 and part2["part"]==2
            and part1["precommit_sha"]==part2["precommit_sha"]==PINS[0][1]
            and part1["production"]==part2["production"]=="NO_GO"
            and origin["self_signed_count"]==origin["receipt_success_count"]==origin["count"]==19
            and len(recon["rows"])==19 and len(pre["all_19_original_selected_txs"])==19,
            "original source closed cohort and signers not fixed")
    freeze=stage["first_major_4"]["rounds"]
    require(len(freeze)==len(pre["original_rounds"])==2
            and [r["round"] for r in freeze]==[1,2]
            and [x["p2_index"] for x in pre["original_rounds"]]==[16,17]
            and [r["sign"] for r in freeze]==["NEGATIVE","POSITIVE"]
            and [r["buy_count"] for r in freeze]==[1,1]
            and [r["sell_count"] for r in freeze]==[1,16],
            "original two native negative/positive cases were reselected")
    flat=[x for r in freeze for x in r["transactions"]]
    require(len(flat)==19
            and len({x["hash"] for x in flat})==19
            and len({x["block"] for x in flat})==19
            and [x["hash"] for x in flat]==[x["hash"] for x in pre["all_19_original_selected_txs"]],
            "19 immutable original signed transactions altered or omitted")
    rounds=[]
    for i,r in enumerate(freeze):
        inventory=gross=cost=gas=diff=native=0
        checked=[]
        for t in r["transactions"]:
            older=[x for x in recon["rows"] if x["hash"]==t["hash"]]
            original=[x for x in origin["transactions"] if x["hash"]==t["hash"]]
            require(len(older)==len(original)==1,"original source recon and receipt missing/duplicated")
            old=older[0];rc=original[0]
            require(t["original_owner_signed"] is True
                    and t["original_receipt_status"]=="SUCCESS"
                    and rc["original_signer_matches"] is True
                    and rc["receipt_status"]=="SUCCESS"
                    and rc["from"].lower()==pre["original_wallet"].lower()
                    and rc["block"]==t["block"]
                    and old["signer_and_receipt"]=="SELF_SIGNED_SUCCESS"
                    and old["block"]==t["block"]
                    and t["hash"] in {x["hash"] for x in pre["all_19_original_selected_txs"]},
                    "original success and BNB chain signer mismatch")
            buy=int(t["native_value_in_wei"])
            withdrawal=int(t["receipt_WBNB_withdraw_wei"])
            network_gas=int(t["receipt_gas_wei"])
            route_cost=int(t["quote_route_difference_wei"])
            owner_delta=int(t["wallet_block_native_delta_wei"])
            token_delta=int(t["token_delta_raw"])
            require(owner_delta==withdrawal-buy-network_gas-route_cost
                    and old["wallet_delta_wei"]==str(owner_delta)
                    and old["wbnb_withdraw_wei"]==str(withdrawal)
                    and old["buy_wei"]==str(buy)
                    and old["gas_wei"]==str(network_gas)
                    and rc["native_wallet_block_delta_wei"]==str(owner_delta),
                    "source paid gas WBNB native full reconciliation broken")
            inventory+=token_delta
            require(inventory>=0 and t["inventory_after_raw"]==str(inventory)
                    and (buy>0 and withdrawal==0 if t["direction"]=="in"
                         else buy==0 and withdrawal>0 and t["direction"]=="out"),
                    "source original token inventory or buy/sale direction invalid")
            cost+=buy;gross+=withdrawal;gas+=network_gas;diff+=route_cost;native+=owner_delta
            checked.append({
                "hash":t["hash"],"block":t["block"],
                "action":"BUY" if t["direction"]=="in" else "SELL",
                "original_signed_success":True,
                "original_token_delta_raw":t["token_delta_raw"],
                "original_token_inventory_after_raw":t["inventory_after_raw"],
                "original_BNB_input_wei":t["native_value_in_wei"],
                "original_WBNB_withdraw_wei":t["receipt_WBNB_withdraw_wei"],
                "original_Gas_wei":t["receipt_gas_wei"],
                "original_observed_exit_route_delta_wei":t["quote_route_difference_wei"],
                "original_owner_native_block_net_wei":t["wallet_block_native_delta_wei"]
            })
        sums=r["sums"]
        require(inventory==0 and r["zero_inventory_close"] is True
                and cost==int(sums["native_value_in_wei"])
                and gross==int(sums["receipt_WBNB_withdraw_wei"])
                and gas==int(sums["receipt_gas_wei"])
                and diff==int(sums["quote_route_difference_wei"])
                and native==int(sums["wallet_block_native_delta_wei"]),
                "original round full source native outcome not closed")
        previous=pre["original_rounds"][i]
        require(previous["round"]==r["round"] and previous["p2_index"]==16+i
                and previous["original_tx_count"]==len(checked)
                and previous["stage_native_wei"]==str(native)
                and previous["full_raw_inventory_zero"] is True,
                "original research precommit outcome or sample altered")
        rounds.append({
            "original_round":r["round"],"original_p2_ledger_index":16+i,
            "token":"4","wallet":pre["original_wallet"],"exact_CA":pre["major_exact_CA"],
            "original_trades":checked,
            "trade_count":len(checked),"original_buy_count":r["buy_count"],
            "original_sell_count":r["sell_count"],
            "original_inventory_closed_raw":"0",
            "original_BNB_purchase_total_wei":str(cost),
            "original_WBNB_sale_withdraw_total_wei":str(gross),
            "original_paid_Gas_total_wei":str(gas),
            "original_observed_exit_route_difference_total_wei":str(diff),
            "original_wallet_native_net_wei":str(native),
            "sign":"POSITIVE" if native>0 else "NEGATIVE",
            "source_status":"PREVIOUS_ORIGINAL_19_FULL_EVIDENCE_REPLAYED_REVIEW_PENDING"
        })
    independently=part1["rows"]+part2["rows"]
    picks=pre["fresh_original_five_spot_readback"]
    require(len(independently)==len(picks)==5 and
            len({x["selected"]["hash"] for x in independently})==5,
            "must independently check all five frozen positions, not cherry-picked")
    checked=[]
    all_trades=[v for r in rounds for v in r["original_trades"]]
    for pos,spot in enumerate(independently):
        picked=picks[pos]
        selected=spot["selected"]
        require(selected==picked and spot["original_eoa_signed_status"]=="OWNER_SIGNED_CHAIN56"
                and spot["receipt_status"]=="SUCCESS_FULL",
                "one of five original independent spot checks incomplete")
        tx=spot["original_transaction"]
        require(tx is not None
                and tx["hash"]==selected["hash"]
                and tx["from"].lower()==pre["original_wallet"].lower()
                and int(tx["chainId"],16)==56
                and int(tx["blockNumber"],16)==selected["block"],
                "fresh 5 original EOA BNB chain signer and block mismatch")
        originals=[t for t in all_trades if t["hash"]==selected["hash"]]
        require(len(originals)==1 and spot["native_delta_wei"]==originals[0]["original_owner_native_block_net_wei"]
                and spot["native_before"] is not None and spot["native_after"] is not None
                and int(spot["native_after"])-int(spot["native_before"])==int(spot["native_delta_wei"]),
                "fresh 5 owner native N-1/N wrong block or balance")
        t=originals[0]
        meta=spot["receipt_meta"]
        require(meta is not None and meta["status"]=="0x1"
                and not any(spot["provider_errors"].values()),"incomplete original success source")
        gas=int(meta["gasUsed"],16)*int(meta["effectiveGasPrice"],16)
        require(gas==int(t["original_Gas_wei"]),"fresh original paid Gas mismatch")
        action=t["action"]
        contract_topic=DEPOSIT if action=="BUY" else WITHDRAW
        logs=meta["selected_wbnb_logs"]
        mint=[x for x in logs if x["topics"][0]==contract_topic]
        transfer=[x for x in logs if x["topics"][0]==TRANSFER]
        require(len(mint)==len(transfer)==1 and
                mint[0]["transactionHash"]==transfer[0]["transactionHash"]==t["hash"] and
                int(mint[0]["data"],16)==int(transfer[0]["data"],16),
                "actual original WBNB deposit-withdraw and transfer amount not paired")
        amount=int(mint[0]["data"],16)
        if action=="SELL":
            require(amount==int(t["original_WBNB_withdraw_wei"]),"actual original WBNB exit mismatch")
        else:
            require(amount>0 and amount<=int(t["original_BNB_input_wei"]),"actual buy WBNB mint must not exceed BNB paid")
        checked.append({
            "hash":selected["hash"],"block":selected["block"],
            "original_round":selected["case"],"action":action,
            "original_chain56_signer_confirmed":True,"full_success_receipt_confirmed":True,
            "historical_native_wei_reconfirmed":spot["native_delta_wei"],
            "historical_gas_wei_reconfirmed":str(gas),
            "actual_WBNB_deposit_or_withdraw_wei":str(amount),
            "actual_WBNB_original_transfer_wei":str(int(transfer[0]["data"],16)),
            "buy_original_BNB_value_wei":t["original_BNB_input_wei"],
            "buy_native_input_minus_WBNB_deposit_wei":
               str(int(t["original_BNB_input_wei"])-amount) if action=="BUY" else None,
            "observed_final_WBNB_receiver_or_spender":
               "0x"+transfer[0]["topics"][2][-40:] if action=="BUY"
               else "0x"+transfer[0]["topics"][1][-40:]
        })
    require([x["buy_native_input_minus_WBNB_deposit_wei"] for x in checked if x["action"]=="BUY"]
            ==["5000000000000000","3000000000000000"],
            "buy source native input/WBNB actual mint gap is not zero")
    return {
      "schema":"BSC_P4C_8E6B_TOKEN4_19_ORIGINAL_NATIVE_SETTLED_TWO_ROUNDS_WITH_FIVE_INDEPENDENT_SPOT",
      "scope":SCOPE,"source_manifest":[{"path":PREFIX+n,"git_blob_sha":h} for n,h in PINS],
      "summary":{
        "historic_wallets":1,"major_CA":1,"original_rounds":2,
        "original_signer_success_source_records":19,"independent_live_spot_tx_count":5,
        "spot_chain56_owner_verified":5,"spot_full_success_receipt_verified":5,
        "spot_original_Gas_native_balance_matches":5,
        "spot_WBNB_deposit_or_withdraw_original_match":5,
        "original_negative_native_rounds":1,"original_positive_native_rounds":1,
        "original_total_native_wei":str(sum(int(r["original_wallet_native_net_wei"]) for r in rounds)),
        "independent_reviewer_approved_this_sha":False,
        "public_observer_first_executable_U":"UNRESOLVED",
        "lagged_1_5_15_min_follower_signal_count":0,
        "production":"NO_GO"
      },
      "rounds":rounds,"spot_checks":checked
    }
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-dir",type=Path,default=ROOT)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.write_text(json.dumps(build(load(args.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
