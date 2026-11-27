#!/usr/bin/env python3
"""P4-C 877AF MARSCOIN two signed owner inventory-closed native-scope-only rounds.

Never convert truncated historical receipts into success or exact gas, and never
confuse token contract levy or mere native wallet block delta with full PnL.
"""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4c-next239e877af-economic-original-probe-precommit-2026-10-15.json","5c9608d13e92f4e36a9fa0950fb065abb9869a0b"),("bsc-meme-address-model-v1-p4c-next239e877af-original-ca-events-part2-2026-10-15.json","54ce5476e47e7cac51df1dccfefd43d324ff883f"),("bsc-meme-address-model-v1-p4c-next239e877af-receipts-part2-2026-10-15.json","e21ea9acf50cae583ba2a4b1414f4ffd4a5df279"),("bsc-meme-address-model-v1-p4c-next239e877af-native-block-part2-2026-10-15.json","9e4c2974cf949ba5e3f5e6d01ad70a676035fa03"))
TOPIC="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
def require(v,s):
    if not v:raise ValueError(s)
def blob_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def load(root=ROOT):
    out=[]
    for n,h in PINS:
        data=(root/n).read_bytes()
        require(blob_sha(data)==h,"877AF original source drift")
        out.append(json.loads(data))
    return out
def build(d):
    require(len(d)==4,"877AF original 4 documents required")
    plan,events,receipts,balances=d
    require([v["episode_index"] for v in plan["batches"]]==[29,30,37,38] and
            events["part"]==receipts["part"]==balances["part"]==2 and
            len(receipts["rows"])==len(balances["rows"])==6 and
            all(x["production"]=="NO_GO" for x in d),
            "wrong immutable original 877AF cohort and source part")
    result=[]
    for original in plan["batches"][2:]:
        acquired=sent=levy=to_pool=0
        records=[]
        for orig in original["original_signed_txs"]:
            selected=[e for row in events["results"] for e in row["logs"]
                      if row["tx"]==orig["tx"] and e["transactionHash"]==orig["tx"]]
            rc=[x for x in receipts["rows"] if x["source"]["tx"]==orig["tx"]]
            bs=[x for x in balances["rows"] if x["block"]==orig["block"]]
            require(len(rc)==len(bs)==1 and rc[0]["status"]=="TRUNCATED"
                    and rc[0]["source"]["block"]==orig["block"]
                    and bs[0]["pre"]["status"]==bs[0]["post"]["status"]=="COMPLETE"
                    and bs[0]["delta_wei"]==str(int(bs[0]["post"]["wei"])-int(bs[0]["pre"]["wei"])),
                    "missing or spoofed historical owner transaction or native balance")
            uniq=set()
            for e in selected:
                key=(e["blockHash"],e["transactionHash"],e["logIndex"])
                require(key not in uniq and e["removed"] is False
                        and e["topics"][0]==TOPIC and e["address"].lower()==original["ca"].lower()
                        and int(e["blockNumber"],16)==orig["block"],
                        "duplicate / noncanonical ERC20 event")
                uniq.add(key)
            rcv=[e for e in selected if "0x"+e["topics"][2][-40:].lower()==original["owner"].lower()]
            out=[e for e in selected if "0x"+e["topics"][1][-40:].lower()==original["owner"].lower()]
            amountin=sum(int(e["data"],16) for e in rcv)
            amountout=sum(int(e["data"],16) for e in out)
            require((amountin>0)!=(amountout>0),"missing owner token buy/sell")
            acquired+=amountin;sent+=amountout
            levy+=sum(int(e["data"],16) for e in out if "0x"+e["topics"][2][-40:].lower()==original["ca"].lower())
            to_pool+=sum(int(e["data"],16) for e in out if "0x"+e["topics"][2][-40:].lower()!=original["ca"].lower())
            records.append({
                "hash":orig["tx"],"block":orig["block"],"action":"BUY" if amountin else "SELL",
                "owner_tokens_received_raw":str(amountin),"owner_tokens_sent_raw":str(amountout),
                "native_BNB_block_delta_wei":bs[0]["delta_wei"],
                "full_receipt_status":"TRUNCATED",
                "true_WBNB_or_Q3B_wallet_cashflow":"UNRESOLVED"
            })
        require(acquired>0 and acquired==sent and levy+to_pool==sent,
                "877AF exact owner inventory cannot close or source levy changes")
        result.append({
            "p2_ledger_index":original["episode_index"],"owner":original["owner"],
            "token":original["token"],"exact_CA":original["ca"],"txs":records,
            "raw_tokens_received":str(acquired),"raw_tokens_sent":str(sent),
            "remaining_token_inventory_raw":"0",
            "raw_tokens_sent_to_token_contract":str(levy),
            "raw_tokens_sent_to_pool":str(to_pool),
            "native_eoa_selected_block_deltas_wei":str(sum(int(x["native_BNB_block_delta_wei"]) for x in records)),
            "economic_status":"OWNER_TOKEN_CLOSE_BUT_NONNATIVE_QUOTE_GAS_UNRESOLVED",
            "qualified_realized_net_profit":False
        })
    require([r["p2_ledger_index"] for r in result]==[37,38]
            and int(result[0]["native_eoa_selected_block_deltas_wei"])>0
            and int(result[1]["native_eoa_selected_block_deltas_wei"])<0,
            "negative original P2 controls silently omitted")
    return {"schema":"BSC_P4C_877AF_MARSCOIN_BOTH_OWNER_INVENTORY_CLOSED_QUOTE_OPEN",
            "source_manifest":[{"path":PREFIX+n,"git_blob_sha":sha} for n,sha in PINS],
            "summary":{"wallets":1,"major_CA":1,"original_rounds":2,
                       "original_signed_txs":6,"raw_owner_full_token_quantity_closed":2,
                       "complete_success_receipts":0,"receipt_truncated":6,
                       "original_real_BNB_winner_rounds_newly_qualified":0,
                       "original_real_BNB_loser_rounds_newly_qualified":0,
                       "qualified_observer_trades":0,"production":"NO_GO"},
            "rounds":result}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
