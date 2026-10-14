#!/usr/bin/env python3
"""Three precommitted ADFF/2ADF/A83B rounds: token-close != cashflow-close.

Reads Git-blob-pinned original owner selected events and actual configured
WBNB vs Q3B pool transfer logs. Excludes same-block unrelated quote event.
Does not elevate signs from wallet native event-block scopes to settled PnL.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4c-three-unclosed-router-event-precommit-2026-10-15.json","9816653aae69785222ec75eb85c0abb19e1dd555"),("bsc-meme-address-model-v1-p4c-three-unclosed-ADFF-transfer-probe-2026-10-15.json","ec26c14395b770ca036f6ee765603edd273717bc"),("bsc-meme-address-model-v1-p4c-three-unclosed-ADFF-WBNB-targeted-2026-10-15.json","46034ffaec8ee79eed07de879c862f02f401d517"),("bsc-meme-address-model-v1-p4c-three-unclosed-2ADF-token-events-2026-10-15.json","937e1710dcebb1a4aca34e9c88654f3e4bbac59a"),("bsc-meme-address-model-v1-p4c-three-unclosed-A83B-token-events-2026-10-15.json","df135ffb256daa98ebe14586e5b8e562d8486c90"),("bsc-meme-address-model-v1-p4c-three-unclosed-NIULAI-WBNB-pool-2026-10-15.json","52642057666f7f02de56439887b9ead0522ba47c"),("bsc-meme-address-model-v1-p4c-three-unclosed-NIULAI-Q3B-outflow-2026-10-15.json","49fd8b4ed14e2fb3cde5931e5ef22e10ea830fb9"),("bsc-meme-address-model-v1-p4c-sevenwallet-balanced-signers-native-outcome-2026-10-15.json","3c4f07ebee061e16bebad3f0a307227b4b958823"))
RESULT="OWNER_TOKEN_QUANTITY_CLOSED_QUOTE_ROUTER_ECONOMICS_UNRESOLVED"

def check(v,msg):
    if not v:raise ValueError(msg)
def sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def load(root=ROOT):
    data=[]
    for name,blob in PINS:
        b=(root/name).read_bytes()
        check(sha(b)==blob,"source Git blob drift "+name)
        data.append(json.loads(b))
    return data
def decoded(log,kind):
    check(len(log["topics"])==3 and log["topics"][0]=="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef","incorrect ERC20 Transfer topic")
    return {"tx":log["transactionHash"],"raw":str(int(log["data"],16)),"from":"0x"+log["topics"][1][-40:],"to":"0x"+log["topics"][2][-40:]}
def build(d):
    check(len(d)==8,"required exact eight source documents")
    pre,dragon,dragon_wbnb,niulai2,niulaiA,niulai_wbnb,niulai_q3b,batch=d
    check(pre["schema"]=="BSC_P4C_THREE_UNCLOSED_ORIGINAL_TX_LOG_PROBE"
          and pre["original_batch_source_blob_sha"]==batch["source_manifest"][0]["git_blob_sha"]
          and pre["production"]=="NO_GO" and len(pre["selected"])==3
          and all(x.get("production",x.get("summary",{}).get("production"))=="NO_GO" for x in d)
          and batch["summary"]["frozen_recent_active_wallets"]==7
          and len(batch["rounds"])==5,
          "frozen three-round source cohort changed")
    selection_names=["ADFF_DRAGON_R4","2ADF_NIULAI_R3","A83B_NIULAI_R2"]
    check([v["round"] for v in pre["selected"]]==selection_names,"selection or order drift")
    allselected={tx[0] for r in pre["selected"] for tx in r["txs"]}
    check(len(allselected)==7 and len({(r["wallet"],r["round"]) for r in pre["selected"]})==3,
          "source original tx subset not exactly 7")
    check(all(x["status"]=="COMPLETE" for raw in (dragon.get("res"),niulai2["rows"],niulaiA["rows"],dragon_wbnb["rows"],niulai_wbnb["rows"],niulai_q3b["rows"]) for x in raw),
          "bounded source ethGetLogs incomplete")
    check(all(len(r["logs"])==0 for r in niulai_wbnb["rows"]),
          "unexpected direct WBNB source in Niulai pool invalidates classification")
    rounds=[]
    for sel in pre["selected"]:
        key=sel["round"]
        samples=set(x[0] for x in sel["txs"])
        signedblock={x[0]:x[1] for x in sel["txs"]}
        tokenDoc=dragon["res"] if key=="ADFF_DRAGON_R4" else niulai2["rows"] if key=="2ADF_NIULAI_R3" else niulaiA["rows"]
        observed=[]
        for r in tokenDoc:
            for event in r["logs"]:
                if event["transactionHash"] not in samples:continue
                check(r["block"]==signedblock[event["transactionHash"]],"token original signed tx in incorrect block")
                check(event["address"].lower()==sel["CA"].lower(),"token CA drift")
                e=decoded(event,"token")
                e={"block":r["block"],"direction":r["direction"],**e}
                check((r["direction"]=="IN" and e["to"]==sel["wallet"]) or
                      (r["direction"]=="OUT" and e["from"]==sel["wallet"]),
                      "token signed-owner movement not proven")
                observed.append(e)
        incoming=[x for x in observed if x["direction"]=="IN"]
        outgoing=[x for x in observed if x["direction"]=="OUT"]
        total_in=sum(int(x["raw"]) for x in incoming)
        total_out=sum(int(x["raw"]) for x in outgoing)
        check(total_in>0 and total_in==total_out and incoming and outgoing
              and len(set(x["tx"] for x in observed))==len(samples),
              "original signed inventory not fully closed")
        burn=sum(int(x["raw"]) for x in outgoing if x["to"]==sel["CA"])
        check((burn==0 if key=="ADFF_DRAGON_R4" else burn==total_out//100),
              "historical token withheld 1 pct on Niulai sale not verified")
        source_quote=dragon_wbnb["rows"] if key=="ADFF_DRAGON_R4" else niulai_q3b["rows"]
        quote_name="WBNB" if key=="ADFF_DRAGON_R4" else "Q3B"
        quote_ca=pre["WBNB"] if quote_name=="WBNB" else niulai_q3b["quote_CA"]
        qflows=[]
        for row in source_quote:
            for event in row["logs"]:
                if event["transactionHash"] not in samples:continue
                e=decoded(event,"quote")
                block=row.get("b",row.get("block"))
                check(block==signedblock[e["tx"]] and event["address"].lower()==quote_ca.lower(),
                      "source quote receipt not original signed transaction")
                check(e["to"]=="0x1de460f363af910f51726def188f9004276bf4bc",
                      "quote routed to unexpected receiver")
                qflows.append({"original_signed_tx":e["tx"],"block":block,"raw":e["raw"],"from":e["from"],"to":e["to"]})
        check(len(qflows)==1 and qflows[0]["original_signed_tx"]==sel["txs"][-1][0],
              "exact original sell quote ERC20 exit incomplete")
        prior=next(x for x in batch["rounds"] if x["round_key"]==key)
        check(prior["actual_settled_owner_native_round_status"]==
              "UNRESOLVED_ECONOMIC_CASHFLOW_OR_FULL_RECEIPTS" and
              prior["wallet"]==sel["wallet"] and prior["exact_CA"]==sel["CA"],
              "partial 7-wallet sample was already falsely promoted")
        rounds.append({
            "round_key":key,"wallet":sel["wallet"],"token":"龙虾" if key=="ADFF_DRAGON_R4" else "牛来",
            "exact_CA":sel["CA"],
            "source_signed_tx_count":len(samples),
            "original_token_in_raw":str(total_in),"original_token_out_raw":str(total_out),
            "original_token_residual_raw":"0",
            "original_onchain_buy_events":incoming,
            "original_onchain_sell_events":outgoing,
            "returned_to_token_contract_fee_raw":str(burn),
            "returned_to_pool_raw":str(total_out-burn),
            "quote_asset_source":quote_name,
            "quote_asset_contract":quote_ca,
            "source_quote_to_router_transfers":qflows,
            "native_owner_block_net_wei":prior["native_account_selected_block_net_wei"],
            "native_owner_block_sign":prior["native_account_selected_block_direction"],
            "evidence":RESULT,
            "strict_native_settled_profit_qualification":False,
            "first_observer_executable_U":"UNRESOLVED",
            "follower_1_5_15min":"UNRESOLVED"
        })
    extra=[]
    for row in niulai_q3b["rows"]:
        for event in row["logs"]:
            if event["transactionHash"] in allselected:continue
            extra.append({
                "block":row["block"],"tx":event["transactionHash"],
                "quote_raw":str(int(event["data"],16)),
                "reason":"NOT_PRESELECTED_OWNER_SIGNED_TX_EXCLUDE"
            })
    check(len(extra)==1 and extra[0]["block"]==116113193,
          "unrelated other-wallet same-block Q3B quote row contamination")
    check([x["native_owner_block_sign"] for x in rounds]==
          ["POSITIVE_NATIVE_BLOCK_SCOPE","POSITIVE_NATIVE_BLOCK_SCOPE","NEGATIVE_NATIVE_BLOCK_SCOPE"],
          "previous native economic positive/negative controls invalidated")
    return {
      "schema":"BSC_P4C_THREE_FROZEN_ROUNDS_OWNER_TOKEN_INVENTORY_CLOSED_QUOTE_CAUSAL_ROUTE_OPEN",
      "source_manifest":[{"path":PREFIX+n,"git_blob_sha":h} for n,h in PINS],
      "summary":{
        "fixed_rounds":3,"fixed_original_owner_signed_txs":7,
        "source_canonical_token_inventory_closed":3,
        "native_window_positive_observed":2,
        "native_window_negative_observed":1,
        "new_settled_native_profitable_rounds":0,
        "new_settled_native_unprofitable_rounds":0,
        "unrelated_same_block_Q3B_outflows_excluded":len(extra),
        "positive_profit_rank_approved":False,
        "production":"NO_GO"
      },
      "rounds":rounds,
      "excluded_unrelated_quote_events":extra
    }
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-dir",type=Path,default=ROOT)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
