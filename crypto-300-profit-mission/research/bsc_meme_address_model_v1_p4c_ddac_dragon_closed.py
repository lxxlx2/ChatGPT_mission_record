#!/usr/bin/env python3
"""P4-C: deterministic owner-signed closed original DDAC 龙虾 negative BNB round.

Pin original Git blob hashes, decode actual successful Four TokenSale, verify
ERC20 inventory closure, two signed exit receipts, paid gas, and historical
owner native BNB. BNB window net IS NOT a profitable repeat or follower alpha.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4b-dragon-ddac-real-pre-dex-buy-2026-10-14.json","f89362368ad47f1cde2d8475f9e7b8a688093f83"),("bsc-meme-address-model-v1-p4c-major3-owner-transfer-exit-raw-2026-10-15.json","30425f9ee554bdf8f883b1c85e01261f1cf438df"),("bsc-meme-address-model-v1-p4c-dragon-native-block-balance-raw-2026-10-15.json","938823f19b83aa1584c611047ac70dec28bdba88"),("bsc-meme-address-model-v1-p4c-dragon-three-tx-header-and-inbound-raw-2026-10-15.json","c10889537f981c8b2e58baf4e9800a1882decfee"),("bsc-meme-address-model-v1-p4c-dragon-approval-and-sale-full-receipts-2026-10-15.json","1cec4b49bd3da060f20d0f84f1d25c21e5f2b6ff"),("bsc-meme-address-model-v1-p4b-23x19-early-opportunity-ledger-2026-10-14.json","f88ed9abfcb0f321ec31e98a029303aca48a8623"))
SCHEMA="BSC_P4C_DDAC_DRAGON_SIGNED_CLOSED_NATIVE_LOSS_ROUND"
SCOPE="One frozen original 23-wallet DDAC early Dragon owner-signed Four.meme buy and fully closed original token inventory through one successful owner-signed Four.meme TokenSale, account exact in both raw events and on-chain transfer; original BNB wallet before/after exact blocks and two successful signed sale-block gas receipts. Native net wallet change includes both sale-block tx gas; purchase-block buy fee not separately decomposed. P5 followability and profit ranking remain unresolved."
SALE_TOPIC="0x0a5575b3648bae2210cee56bf33254cc1ddfbc7bf637c0af2ac18b14fb1bae19"

def require(condition,msg):
    if not condition:
        raise ValueError(msg)

def blob_sha(payload):
    return hashlib.sha1(b"blob "+str(len(payload)).encode()+b"\0"+payload).hexdigest()

def load(root=ROOT):
    docs=[]
    for filename,sha in PINS:
        raw=(root/filename).read_bytes()
        require(blob_sha(raw)==sha,"Source Git blob mismatch: "+filename)
        docs.append(json.loads(raw))
    return docs

def word(hex_data,i):
    require(isinstance(hex_data,str) and hex_data.startswith("0x") and len(hex_data)==2+64*8,
            "TokenSale canonical 8 word event invalid")
    return int(hex_data[2+64*i:2+64*(i+1)],16)

def build(src):
    require(len(src)==6,"source manifest must contain six original documents")
    buy_doc,all_out,native,headers,receipts,grid=src
    buy=buy_doc["fact"]
    owner=buy["buyer_EOA"].lower()
    CA=buy["exact_CA"].lower()
    manager=buy["manager"].lower()
    require(buy_doc["summary"]["original_signed_DDAC_buys_in_this_fixed_sample"]==1
            and buy["market_window_classification"]=="ACTUAL_SIGNED_PRE_DEX_LAUNCHPAD_BUY_OBSERVED"
            and buy["TokenPurchase_account"].lower()==owner
            and buy["original_erc20_transfer_recipient"].lower()==owner
            and buy["original_erc20_transfer_raw_amount"]==buy["TokenPurchase_amount_token_raw"]
            and buy["sell_status"]=="UNRESOLVED",
            "original frozen independent buy proof changed")
    require(grid["summary"]["wallets"]==23
            and grid["summary"]["major_exact_CAs"]==19
            and grid["summary"]["implicit_wallet_CA_cells"]==437
            and grid["summary"]["one_source_proven_owner_signed_pre_dex_buy"]==1
            and len(grid["known_early_owner_trades"])==1
            and grid["known_early_owner_trades"][0]["wallet"].lower()==owner,
            "23x19 denominator or DDAC original source changed")
    asc=next((r for r in all_out["rows"] if r["token"]=="龙虾" and r["order"]=="asc"),None)
    desc=next((r for r in all_out["rows"] if r["token"]=="龙虾" and r["order"]=="desc"),None)
    require(asc is not None and desc is not None
            and asc["status"]==desc["status"]=="COMPLETE_PAGE"
            and asc["pageKey"] is None and desc["pageKey"] is None
            and len(asc["transfers"])==len(desc["transfers"])==2
            and [t["hash"] for t in asc["transfers"]]==[t["hash"] for t in reversed(desc["transfers"])],
            "Original EOA 2-transfer replay not exhaustive or conflicting")
    moved=asc["transfers"][0]
    purchase_amount=int(buy["TokenPurchase_amount_token_raw"])
    moved_amount=int(moved["rawContract"]["value"],16)
    require(moved["from"].lower()==owner and moved["to"].lower()==manager
            and moved["rawContract"]["address"].lower()==CA
            and moved_amount==purchase_amount
            and int(moved["blockNum"],16)>buy["buyer_original_tx_block"],
            "Actual original inventory not returned to Four manager")
    appro=next((r for r in receipts["rows"] if r["selection"]["txhash"]!=moved["hash"]),None)
    sold=next((r for r in receipts["rows"] if r["selection"]["txhash"]==moved["hash"]),None)
    require(appro is not None and sold is not None and len(receipts["rows"])==2
            and all(r["read_status"]=="COMPLETE" and r["receipt"]["status"]=="0x1" for r in receipts["rows"]),
            "approval or sale original full-success receipts absent")
    sale_receipt=sold["receipt"]
    require(sale_receipt["transactionHash"].lower()==moved["hash"].lower()
            and int(sale_receipt["blockNumber"],16)==int(moved["blockNum"],16)
            and appro["receipt"]["transactionHash"].lower()!=moved["hash"].lower(),
            "sold transaction was not the original manager transfer")
    sale_events=[e for e in sale_receipt["logs"]
                 if e["address"].lower()==manager and e["topics"][0].lower()==SALE_TOPIC]
    require(len(sale_events)==1,"original successful Four TokenSale not unique")
    evt=sale_events[0]
    require(evt["transactionHash"].lower()==moved["hash"].lower()
            and int(evt["blockNumber"],16)==int(moved["blockNum"],16)
            and evt.get("removed") is not True
            and word(evt["data"],0)==int(CA,16)
            and word(evt["data"],1)==int(owner,16)
            and word(evt["data"],3)==moved_amount,
            "TokenSale original account/token/amount is not original signed wallet")
    sale_cost=word(evt["data"],4)
    sale_fee=word(evt["data"],5)
    require(sale_cost>sale_fee>0,"sale event amounts invalid")
    require(native["schema"]=="BSC_P4C_DRAGON_DDAC_HISTORIC_NATIVE_WALLET_FOUR_BLOCK_READBACK"
            and len(native["balances"])==4
            and [x["block"] for x in native["balances"]]==
                [buy["buyer_original_tx_block"]-1,buy["buyer_original_tx_block"],
                 int(moved["blockNum"],16)-1,int(moved["blockNum"],16)]
            and all(x["status"]=="COMPLETE" for x in native["balances"]),
            "native original historic wallet block states incomplete")
    bal=[int(x["balance_wei"]) for x in native["balances"]]
    debit=bal[0]-bal[1]
    credit=bal[3]-bal[2]
    require(debit>0 and credit>0 and bal[1]==bal[2]
            and native["buy_block_native_delta_wei"]==str(-debit)
            and native["sell_block_native_delta_wei"]==str(credit),
            "native economic wallet window changed or not continuous")
    block_activity=native["owner_external_source_activity"]
    require(len(block_activity)==2
            and [x["block"] for x in block_activity]==
                [buy["buyer_original_tx_block"],int(moved["blockNum"],16)]
            and all(x["status"]=="COMPLETE_PAGE" and x["pageKey"] is None for x in block_activity)
            and [len(x["transfers"]) for x in block_activity]==[1,2],
            "owner signed transaction denominator incomplete")
    sale_block_ids={x["hash"].lower() for x in block_activity[1]["transfers"]}
    require(sale_block_ids=={r["receipt"]["transactionHash"].lower() for r in receipts["rows"]}
            and block_activity[0]["transfers"][0]["hash"].lower()==buy["buyer_original_tx"].lower(),
            "sale-window unrelated third signed EOA transaction or missing owner buy")
    require(len(headers["rows"])==3
            and all(x["transaction_verified"] and x["tx_from"].lower()==owner for x in headers["rows"])
            and {x["source"]["txhash"].lower() for x in headers["rows"]}==
                sale_block_ids|{buy["buyer_original_tx"].lower()}
            and len(headers["external_inbound"])==2
            and all(x["status"]=="COMPLETE_PAGE" and not x["transfers"] and x["pageKey"] is None
                    for x in headers["external_inbound"]),
            "additional external EOA transfer or nonowner funds not source audited")
    original_gas=[
        {"tx":r["receipt"]["transactionHash"],
         "gas_used":str(int(r["receipt"]["gasUsed"],16)),
         "gas_price_wei":str(int(r["receipt"]["effectiveGasPrice"],16)),
         "gas_fee_wei":str(int(r["receipt"]["gasUsed"],16)*int(r["receipt"]["effectiveGasPrice"],16))}
        for r in (appro,sold)
    ]
    gas=sum(int(x["gas_fee_wei"]) for x in original_gas)
    gross=credit+gas
    require(gross==sale_cost-2*sale_fee,
            "Four original TokenSale cost and quote refund do not settle with EOA BNB change + exact gas")
    net=credit-debit
    require(net<0 and moved_amount==purchase_amount,
            "selected DDAC original round no longer a fully sold negative native round")
    roi_bps=-((-net*10000)//debit)
    return {
        "schema":SCHEMA,"scope":SCOPE,
        "source_manifest":[{"path":PREFIX+n,"git_blob_sha":sha} for n,sha in PINS],
        "summary":{
            "frozen_wallets":23,"frozen_major_CAs":19,
            "original_signed_owner_buys_economically_closed":1,
            "actual_negative_native_owner_rounds":1,"actual_positive_native_owner_rounds":0,
            "remaining_wallet_CAs_not_audited_for_economic_closure":436,
            "market_U_fully_qualified":0,"live_production":"NO_GO"
        },
        "round":{
            "token":"龙虾","exact_CA":CA,"owner":owner,
            "entry_tx":buy["buyer_original_tx"],
            "entry_block":buy["buyer_original_tx_block"],
            "exit_tx":moved["hash"],"exit_block":int(moved["blockNum"],16),
            "elapsed_blocks":int(moved["blockNum"],16)-buy["buyer_original_tx_block"],
            "entry_token_amount_raw":str(purchase_amount),
            "exit_token_amount_raw":str(moved_amount),
            "residual_token_raw":str(purchase_amount-moved_amount),
            "exit_TokenSale_cost_event_wei":str(sale_cost),
            "exit_TokenSale_fee_event_wei":str(sale_fee),
            "original_buy_event_cost_wei":buy["TokenPurchase_cost_quote_wei"],
            "original_buy_event_fee_wei":buy["TokenPurchase_protocol_fee_wei"],
            "pre_buy_wallet_BNB_wei":str(bal[0]),
            "post_buy_wallet_BNB_wei":str(bal[1]),
            "pre_exit_wallet_BNB_wei":str(bal[2]),
            "post_exit_wallet_BNB_wei":str(bal[3]),
            "native_buy_block_debit_wei":str(debit),
            "native_exit_block_credit_after_gas_wei":str(credit),
            "exit_block_original_signed_txs":original_gas,
            "exit_block_total_signed_gas_wei":str(gas),
            "exit_event_implied_prepay_credit_wei":str(sale_cost-2*sale_fee),
            "exit_native_balance_plus_gas_wei":str(gross),
            "exit_venue_verified_successful":"FOUR_MEME_TOKENSALE",
            "native_closed_owner_round_net_wei":str(net),
            "native_closed_owner_round_roi_bps_trunc":roi_bps,
            "native_closed_owner_round_classification":"REALIZED_NEGATIVE_BNB_WINDOW",
            "same_block_owners_txs":2,"original_buy_block_owner_txs":1,
            "other_external_native_inbound_in_two_blocks":"NONE_IN_BOUNDED_EXTERNAL_TX_QUERIES",
            "same_wallet_BNB_between_buy_and_exit_unchanged":True,
            "source_buy_full_receipt":"TRUNCATED",
            "buyer_follower_entry_after_1_5_15min":"UNRESOLVED",
            "global_first_executable_market_U":"UNRESOLVED",
            "production":"NO_GO"
        }
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
