#!/usr/bin/env python3
"""P4-C 239E two signed Dragon source-settled actual BNB economic outcomes.

Reconcile full original receipt WBNB deposits/withdrawals, exact EOA
token inventory, paid Gas, router residual, historical EOA BNB N-1/N,
one matching EOA external tx per block and zero unrelated external deposits.
Source original six files are immutable by their Git blob SHA.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4c-next239e877af-economic-original-probe-precommit-2026-10-15.json","5c9608d13e92f4e36a9fa0950fb065abb9869a0b"),("bsc-meme-address-model-v1-p4c-next239e877af-original-ca-events-part1-2026-10-15.json","61681197d617a40b13042058bd7bb6d9850e3057"),("bsc-meme-address-model-v1-p4c-next239e877af-receipts-part1-2026-10-15.json","c39006096b7edf879bb4deffde7d0e5fa3592cae"),("bsc-meme-address-model-v1-p4c-next239e877af-native-block-part1-2026-10-15.json","603e58adc19a240583c91d66ab8e70286edc36d5"),("bsc-meme-address-model-v1-p4c-next239e877af-239e-owner-external-exclusivity-2026-10-15.json","135d5a8addb4f5578b472f52dd4900eb733226a2"),("bsc-meme-address-model-v1-p4c-next239e877af-239e-owner-inbound-external-2026-10-15.json","e606fd130c9632abd7aa8a1f72b03e3f3225ef44"))
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
WITHDRAW="0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65"
DEPOSIT="0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c"
SCOPE="Original fixed P2 #29 and #30 239E Dragon, 5 original complete success receipts, original exact CA token round trips, actual WBNB deposit and withdrawal events, unique EOA external activity, no external inflow, historical owner native balances, gas, directly observed residual intermediary costs. Residual fee attribution not proven; global market U and follower delayed P5 unknown. Applies only selected owner events, not lifetime PnL or all trades."
def require(v,message):
    if not v:raise ValueError(message)
def blob_sha(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def load(root=ROOT):
    data=[]
    for name,sha in PINS:
        raw=(root/name).read_bytes()
        require(blob_sha(raw)==sha,"frozen source drift "+name)
        data.append(json.loads(raw))
    return data

def build(d):
    require(len(d)==6,"must have 6 independent original source documents")
    pre,events,receipts,balance,outgoing,incoming=d
    require(pre["schema"]=="BSC_P4C_PRECOMMITTED_FOUR_ROUND_ECONOMIC_ORIGINAL_TX_PROBE_V1"
            and len(pre["batches"])==4
            and [v["episode_index"] for v in pre["batches"]]==[29,30,37,38]
            and events["part"]==receipts["part"]==balance["part"]==1
            and len(receipts["rows"])==len(balance["rows"])==len(outgoing["rows"])==len(incoming["rows"])==5
            and all(x["production"]=="NO_GO" for x in d),
            "immutable balanced source population or production changed")
    require(len({(q["round"],q["block"],q["direction"]) for q in events["results"]})==10,
            "duplicate or missing 239E original transaction/block direction")
    rows=[]
    for source in pre["batches"][:2]:
        wallet=source["owner"].lower();ca=source["ca"].lower()
        record={"p2_ledger_index":source["episode_index"],"owner":source["owner"],"token":source["token"],"exact_CA":source["ca"],
                "original_tx_count":len(source["original_signed_txs"]),"token_received_raw":"0","token_sold_raw":"0",
                "token_inventory_residual_raw":None,"original_native_wallet_net_wei":None,
                "original_input_wbnb_pool_raw":"0","original_output_wbnb_pool_raw":"0",
                "original_network_gas_wei":"0","actual_extra_route_delta_wei":"0",
                "source_status":"OWNER_NATIVE_BNB_CLOSED_WITH_UNNAMED_ROUTE_COST",
                "not_claimed":"PROTOCOL_FEE_SEMANTICS_UNKNOWN_AND_FOLLOWER_UNTESTED","txs":[]}
        total_in=total_out=net=gas_total=extra_total=buy_wbnb=sell_wbnb=0
        for picked in source["original_signed_txs"]:
            h=picked["tx"].lower(); block=picked["block"]
            rs=[x for x in receipts["rows"] if x["source"]["tx"].lower()==h]
            bs=[x for x in balance["rows"] if x["block"]==block]
            outs=[x for x in outgoing["rows"] if x["block"]==block]
            ins=[x for x in incoming["rows"] if x["block"]==block]
            require(len(rs)==len(bs)==len(outs)==len(ins)==1,"missing/duplicate original source row")
            r=rs[0];b=bs[0];o=outs[0];i=ins[0]
            require(r["status"]=="SUCCESS_FULL_RECEIPT"
                    and r["source"]["block"]==block
                    and r["receipt"]["status"]=="0x1"
                    and b["delta_wei"]==str(int(b["post"]["wei"])-int(b["pre"]["wei"]))
                    and b["pre"]["status"]==b["post"]["status"]=="COMPLETE"
                    and o["status"]==i["status"]=="COMPLETE"
                    and o["tx"]==i["tx"]==h
                    and len(o["txs"])==1 and o["txs"][0]["hash"].lower()==h
                    and len(i["txs"])==0
                    and not o["page_key_present"] and not i["page_key_present"],
                    "original successful signed exclusive EOA source required")
            tokenevents=[]
            for q in events["results"]:
                if q["tx"].lower()!=h:continue
                require(q["status"]=="RPC_COMPLETE" and q["block"]==block
                        and q["owner"].lower()==wallet and q["ca"].lower()==ca,
                        "token evidence incompatible with original source")
                for log in q["logs"]:
                    if log["transactionHash"].lower()!=h:continue
                    require(log["address"].lower()==ca
                            and log["topics"][0]==TRANSFER and len(log["topics"])==3
                            and log.get("removed") is False
                            and int(log["blockNumber"],16)==block,
                            "original ERC20 transfer not canonical live event")
                    tokenevents.append(log)
            tin=[x for x in tokenevents if "0x"+x["topics"][2][-40:].lower()==wallet]
            tout=[x for x in tokenevents if "0x"+x["topics"][1][-40:].lower()==wallet]
            received=sum(int(x["data"],16) for x in tin)
            sold=sum(int(x["data"],16) for x in tout)
            require((received>0)!=(sold>0),"must be an original buy or sell")
            isbuy=received>0
            loglist=r["receipt"]["selected_logs"]
            wbnb=[x for x in loglist if x["address"].lower()==pre["WBNB"].lower()]
            transfers=[x for x in wbnb if x["topics"][0]==TRANSFER]
            unwrap=[x for x in wbnb if x["topics"][0]==(DEPOSIT if isbuy else WITHDRAW)]
            require(len(transfers)==1 and len(unwrap)==1
                    and int(transfers[0]["data"],16)==int(unwrap[0]["data"],16),
                    "full original WBNB mint/burn and paired transfer not closed")
            amt=int(transfers[0]["data"],16)
            gas=int(r["receipt"]["gasUsed"],16)*int(r["receipt"]["effectiveGasPrice"],16)
            delta=int(b["delta_wei"])
            route_residual=(-delta-amt-gas) if isbuy else (amt-delta-gas)
            require(route_residual>=0 and amt>0,"unexplained or invalid route cost")
            record["txs"].append({
                "hash":picked["tx"],"block":block,"action":"BUY" if isbuy else "SELL",
                "token_raw":str(sum(int(x["data"],16) for x in tokenevents)),
                "wallet_signed_token_delta_raw":str(received-sold),
                "original_wbnb_transfer_wei":str(amt),"gas_wei":str(gas),
                "original_owner_native_block_delta_wei":str(delta),
                "observed_router_cost_residual_wei":str(route_residual),
                "complete_receipt":True,"original_owner_single_external_tx_in_block":True,
                "other_external_native_deposit_absent":True
            })
            total_in+=received;total_out+=sold;net+=delta;gas_total+=gas;extra_total+=route_residual
            if isbuy:buy_wbnb+=amt
            else:sell_wbnb+=amt
        require(total_in==total_out and total_in>0
                and len(record["txs"])==len(source["original_signed_txs"])
                and (net<0 if source["episode_index"]==29 else net>0)
                and str(net)==source["original_native_net_scope_wei"],
                "raw inventory or actual owner native return incompatible with P2 freeze")
        debit=sum(-int(x["original_owner_native_block_delta_wei"]) for x in record["txs"] if x["action"]=="BUY")
        record.update({
            "token_received_raw":str(total_in),"token_sold_raw":str(total_out),"token_inventory_residual_raw":"0",
            "original_native_wallet_net_wei":str(net),
            "original_input_wbnb_pool_raw":str(buy_wbnb),
            "original_output_wbnb_pool_raw":str(sell_wbnb),
            "original_network_gas_wei":str(gas_total),
            "actual_extra_route_delta_wei":str(extra_total),
            "native_original_EOA_profit_sign":"POSITIVE" if net>0 else "NEGATIVE",
            "native_signed_debit_wei":str(debit)
        })
        rows.append(record)
    return {
        "schema":"BSC_P4C_239E_DRAGON_TWO_REAL_OWNER_WBNB_NATIVE_ROUNDS",
        "source_manifest":[{"path":PREFIX+n,"git_blob_sha":h} for n,h in PINS],
        "scope":SCOPE,
        "summary":{
          "owner_wallets":1,"major_CA":1,"original_closed_owner_rounds":2,
          "source_signed_original_transactions":5,"complete_success_receipts":5,
          "owner_native_original_profit_rounds":1,"owner_native_original_loss_rounds":1,
          "unattributed_router_cost_labels":"UNRESOLVED",
          "profitable_wallet_rank_ready":False,"followable_signals":0,"production":"NO_GO"
        },
        "rounds":rows
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-dir",type=Path,default=ROOT)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.write_text(json.dumps(build(load(args.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
