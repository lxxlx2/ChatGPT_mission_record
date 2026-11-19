#!/usr/bin/env python3
"""BSC P4-C original 8E6B meme '4' 19 source-signed tx / five independent checks.

This source replay confirms real original EOA native BNB WBNB execution.
It does NOT certify the first publicly executable opportunity, user follower
profits, or all unrelated same-block internal transfers.
"""
import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4c-8e6b-token4-two-rounds19-precommit-2026-10-15.json","738da1a4a3dfc9304ee188b326b7d307da50145c"),("bsc-meme-address-model-v1-p4c-8e6b-token4-independent-five-part1-2026-10-15.json","75372f649a8ce75188d41b011df6febe33ecbe84"),("bsc-meme-address-model-v1-p4c-8e6b-token4-independent-five-part2-2026-10-15.json","79a43a6c97085e8e796a8288fffdf175618d26f3"),("BSC_MEME_STAGE24_8E6B_TOKEN4_TWO_ROUNDS_THREE_MAJOR_POSITIVE_COHORT_2026-10-13.json","d56c90eff2d062dbb186f5c89e0f59760d6a8d1c"),("BSC_MEME_8E6B_4_EXACT_SETTLEMENT_RECONCILIATION_2026-10-11.json","69cc2ec8e27d3d8427645cdbfdfe5c8043376fe1"),("BSC_MEME_8E6B_4_ORIGIN_RECEIPT_VERIFICATION_2026-10-11.json","41021e96c0f22023a829e8aae8a460d4752d08ef"),("BSC_MEME_8E6B_4_NATIVE_BLOCK_AUDIT_2026-10-11.json","c5f478fd6593d775db16aac0a54c19b180f61ec0"))
SCOPE="Pin original 8E6B / token 4 across frozen P2 indices 16 loss and 17 gain, all 19 originally owner-signed successful settled EOA native transactions and WBNB exits, gas, route residual. Five preselected live independent full signer/receipt+WBNB mint-burn/native block checks. Original wallet native result (not follower alpha). Fees/residual receiver unknown, first global public U not established; no real 1/5/15min signal."
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
DEPOSIT="0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c"
WITHDRAW="0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65"

def gate(v,msg):
    if not v:raise ValueError(msg)
def sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def load(root=ROOT):
    docs=[]
    for file,blob in PINS:
        raw=(root/file).read_bytes()
        gate(sha(raw)==blob,"fixed historical Git source drift "+file)
        docs.append(json.loads(raw))
    return docs
def build(d):
    gate(len(d)==7,"seven source Git documents mandatory")
    pre,spot1,spot2,stage,settled,original,audit=d
    gate(pre["schema"]=="BSC_P4C_ORIGINAL_8E6B_TOKEN4_TWO_ROUNDS_19TX_5INDEPENDENT_SPOT_PRECOMMIT_V1"
         and pre["network"]=="bnb-mainnet" and pre["production"]=="NO_GO"
         and [r["p2_index"] for r in pre["original_rounds"]]==[16,17]
         and [r["original_tx_count"] for r in pre["original_rounds"]]==[2,17]
         and len(pre["all_19_original_selected_txs"])==19
         and len(pre["fresh_original_five_spot_readback"])==5
         and spot1["part"]==1 and spot2["part"]==2
         and spot1["precommit_sha"]==spot2["precommit_sha"]==PINS[0][1]
         and spot1["production"]==spot2["production"]==stage["production"]=="NO_GO"
         and stage["wallet"]==pre["original_wallet"]
         and stage["first_major_4"]["ca"]==pre["major_exact_CA"]
         and stage["first_major_4"]["token_inventory_final_raw"]=="0"
         and settled["wallet"]==original["wallet"]==audit["wallet"]==pre["original_wallet"]
         and len(settled["rows"])==19 and original["count"]==19
         and original["receipt_success_count"]==original["self_signed_count"]==19
         and original["token_history_complete"] and original["token_in_out_quantity_equal"],
         "original 19 source signed buy-sell evidence or frozen cohort wrong")
    gate(len(stage["first_major_4"]["rounds"])==2
         and stage["first_major_4"]["original_in_count"]==2
         and stage["first_major_4"]["original_out_count"]==17
         and stage["first_major_4"]["original_19_self_signed_receipts_success"] is True
         and audit["erc20_quantity_equal"] is True,
         "stage original self-signed 19 tx and raw inventory must close")
    spot=spot1["rows"]+spot2["rows"]
    gate(len(spot)==5 and len(set(x["selected"]["hash"] for x in spot))==5
         and set(x["selected"]["hash"] for x in spot)==set(x["hash"] for x in pre["fresh_original_five_spot_readback"]),
         "five independently precommitted original txs cannot change")
    old={x["hash"]:x for x in settled["rows"]}
    origin={x["hash"]:x for x in original["transactions"]}
    gate(len(old)==len(origin)==19,"duplicate or missing original 19 source hashes")
    alltx=[]
    for x in pre["all_19_original_selected_txs"]:
        hx=x["hash"]
        gate(hx in old and hx in origin,"original selected signer hash not in source")
        z=old[hx]
        signed=origin[hx]
        stagepos=stage["first_major_4"]["rounds"][x["case"]-1]["transactions"]
        match=[s for s in stagepos if s["hash"]==hx]
        gate(len(match)==1 and z["block"]==signed["block"]==x["block"]==match[0]["block"]
             and x["direction"]==z["direction"]==signed["direction"]==match[0]["direction"]
             and match[0]["token_delta_raw"]==x["stage_token_delta_raw"]
             and signed["original_signer_matches"] is True
             and signed["receipt_status"]=="SUCCESS"
             and z["signer_and_receipt"]=="SELF_SIGNED_SUCCESS",
             "original signed source event/CA/tx/episode mismatch")
        dlt=int(z["wallet_delta_wei"]);gross=int(z["wbnb_withdraw_wei"])
        cost=int(z["buy_wei"]);gas=int(z["gas_wei"]);extra=int(z["gross_minus_buy_gas_native_wei"])
        gate(gross-cost-gas-extra==dlt
             and dlt==int(x["native_delta_wei"])
             and gross==int(x["stage_wbnb_withdraw_wei"])
             and gas==int(x["stage_gas_wei"])
             and dlt==int(match[0]["wallet_block_native_delta_wei"])
             and extra>=0 and gas>0,
             "original native WBNB price/Gas/fee residual not actually closed")
        newly=next((q for q in spot if q["selected"]["hash"]==hx),None)
        independent=None
        if newly:
            rc=newly.get("receipt_meta") or {}
            tr=newly.get("original_transaction") or {}
            logs=rc.get("selected_wbnb_logs",[])
            outgoing=[a for a in logs if a["topics"][0]==TRANSFER]
            bridge=[a for a in logs if a["topics"][0]==(DEPOSIT if x["direction"]=="in" else WITHDRAW)]
            gate(newly["original_eoa_signed_status"]=="OWNER_SIGNED_CHAIN56"
                 and newly["receipt_status"]=="SUCCESS_FULL"
                 and newly["native_delta_wei"]==str(dlt)
                 and tr.get("hash")==hx and tr.get("from","").lower()==pre["original_wallet"].lower()
                 and int(tr["blockNumber"],16)==x["block"]
                 and int(tr["chainId"],16)==56
                 and len(outgoing)==len(bridge)==1
                 and int(outgoing[0]["data"],16)==int(bridge[0]["data"],16)
                 and int(rc["gasUsed"],16)*int(rc["effectiveGasPrice"],16)==gas,
                 "independent mainnet signed full receipt/WBNB/N-1-N failed")
            observed=int(outgoing[0]["data"],16)
            gate(observed==gross if x["direction"]=="out" else 0<observed<=cost,
                 "fresh WBNB event not actual paired original deposit/withdraw")
            independent={"original_receipt_success":True,"original_signer":True,
                         "independent_native_N_minus1_N":True,
                         "gas_wei":str(gas),
                         "paired_WBNB_deposit_or_withdrawal_wei":str(observed)}
        alltx.append({"p2_index":16 if x["case"]==1 else 17,
            "hash":hx,"block":x["block"],"direction":x["direction"],
            "original_signed_success":True,"original_native_delta_wei":str(dlt),
            "original_wbnb_withdraw_wei":str(gross),
            "original_buy_native_msg_wei":str(cost),"paid_gas_wei":str(gas),
            "route_residual_wei":str(extra),
            "original_token_delta_raw":match[0]["token_delta_raw"],
            "original_token_inventory_after_raw":match[0]["inventory_after_raw"],
            "independent_spot":independent})
    gate(len(alltx)==19 and len({x["hash"] for x in alltx})==19
         and sum(x["independent_spot"] is not None for x in alltx)==5,
         "signed original tx universe changed")
    rounds=[]
    for v in pre["original_rounds"]:
        samples=[x for x in alltx if x["p2_index"]==v["p2_index"]]
        net=sum(int(x["original_native_delta_wei"]) for x in samples)
        paid=sum(int(x["paid_gas_wei"]) for x in samples)
        residual=sum(int(x["route_residual_wei"]) for x in samples)
        gate(len(samples)==v["original_tx_count"] and net==int(v["stage_native_wei"])
             and samples[-1]["original_token_inventory_after_raw"]=="0"
             and v["full_raw_inventory_zero"]
             and ((net<0 and v["sign"]=="NEGATIVE") or
                  (net>0 and v["sign"]=="POSITIVE")),
             "negative/positive original round suppressed or post hoc reranked")
        rounds.append({"p2_index":v["p2_index"],"original_episode":v["round"],
                       "wallet":pre["original_wallet"],"exact_CA":pre["major_exact_CA"],
                       "token":"4","original_tx_count":len(samples),
                       "original_token_inventory_residual_raw":"0",
                       "original_owner_native_net_wei":str(net),
                       "paid_gas_wei":str(paid),
                       "route_residual_wei":str(residual),
                       "original_owner_economic_sign":"POSITIVE" if net>0 else "NEGATIVE",
                       "observer_followable_profit":"UNRESOLVED"})
    return {"schema":"BSC_P4C_8E6B_TOKEN4_TWO_SETTLED_OWNER_NATIVE_ROUNDS_19TX_FIVE_SPOT",
            "scope":SCOPE,
            "source_manifest":[{"path":PREFIX+n,"git_blob_sha":b} for n,b in PINS],
            "summary":{"wallets":1,"major_CAs":1,"original_native_economic_rounds":2,
                "original_owner_signed_successful_txs":19,
                "original_native_positive_rounds":1,
                "original_native_negative_rounds":1,
                "independently_rechecked_full_transactions":5,
                "new_followable_signals":0,"production":"NO_GO"},
            "rounds":rounds,"original_transactions":alltx}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-dir",type=Path,default=ROOT)
    parser.add_argument("--output",type=Path,required=True)
    opts=parser.parse_args()
    opts.output.write_text(json.dumps(build(load(opts.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
