#!/usr/bin/env python3
"""Five preselected owner-signed BSC Meme rounds, 11 token/BNB observations.

Deterministic immutable source replay: never derive realized profit from a
positive owner BNB block delta when a receipt or quote/Gas is incomplete.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4c-ddac-adff-a83b-fivecase-precommit-2026-10-15.json","21ad05ced290877ef66baa8721acd0361a9f595e"),("bsc-meme-address-model-v1-p4c-ddac-adff-a83b-original-rpc-part1-2026-10-15.json","d0054367f05da66944b1a2f53738ffd049cab887"),("bsc-meme-address-model-v1-p4c-ddac-adff-a83b-original-rpc-part2-2026-10-15.json","dca5b3b9f6b7f4d448a6f62110a2326bb12a8992"),("bsc-meme-address-model-v1-p4c-ddac-adff-a83b-exact-ca-events-part1-2026-10-15.json","8ee9fb0a97e78bba6503dcffa47fdae2eae3d4f5"),("bsc-meme-address-model-v1-p4c-ddac-adff-a83b-exact-ca-events-part2-2026-10-15.json","a5547270526005726812ed37cae530645904ffd9"),("bsc-meme-address-model-v1-p4c-ddac-adff-a83b-native-balance-part1-2026-10-15.json","209f0c9c98e4f700c134d8e03f1678ec1f91262b"),("bsc-meme-address-model-v1-p4c-ddac-adff-a83b-native-balance-part2-2026-10-15.json","8191a784c9c2ed104c41ffa8465c259e561e0c8e"),("bsc-meme-address-model-v1-p4c-ddac-adff-a83b-wbnb-mint-burn-part1-2026-10-15.json","6f5e211aa6864404e15287a3b346ad8e7d045575"))
TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SCOPE="Three original frozen EOA wallets DDAC ADFF A83B, five 2026 major Dragon and IFML source-prespecified episodes, 11 exact original chain56 signed transactions. ALL five raw original EOA token-in/token-out inventory closed and all eleven historical owner native balance blocks read. Only 5 full successful original receipt bodies; remaining 6 truncated. No new realized owner profit upgrade, even when original P2 native-block delta positive, until actual quote/gas/fee accounting. Note ADFF P2#44 two distinct token-in Transfer logs within one original signed tx must be counted, not deduplicated. WBNB raw ethGetLogs provider truncated in DDAC sell blocks; do not infer zero transfer."
def must(ok,message):
    if not ok:raise ValueError(message)
def blob_sha(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def load(root=ROOT):
    docs=[]
    for name,sha in PINS:
        raw=(root/name).read_bytes()
        must(blob_sha(raw)==sha,"original source Git blob mismatch "+name)
        docs.append(json.loads(raw))
    return docs
def build(d):
    must(len(d)==8,"eight original immutable records required")
    plan,a,b,ea,eb,ba,bb,wbnb=d
    must(plan["schema"]=="BSC_P4C_NEXT_THREE_OWNERS_TWO_MAJORS_FIVE_ORIGINAL_ROUNDS_PRECOMMIT_V1"
         and [x["p2_index"] for x in plan["rounds"]]==[3,4,43,44,48]
         and plan["summary"]["wallets"]==3 and plan["summary"]["major_exact_CA"]==2
         and plan["summary"]["precommitted_signed_txs"]==11
         and plan["summary"]["source_native_scope_positive"]==2
         and plan["summary"]["source_native_scope_negative"]==3
         and a["part"]==ea["part"]==ba["part"]==wbnb["part"]==1
         and b["part"]==eb["part"]==bb["part"]==2
         and a["precommit_git_blob_sha"]==b["precommit_git_blob_sha"]==ea["precommit_git_blob_sha"]==eb["precommit_git_blob_sha"]==PINS[0][1]
         and all(x["production"]=="NO_GO" for x in d),
         "five precommitted P2 cohorts/parts/status changed")
    rpc=a["rows"]+b["rows"]
    events=ea["rows"]+eb["rows"]
    balances=ba["rows"]+bb["rows"]
    must(len(rpc)==11 and len(balances)==11 and len(events)==22
         and len({x["original"]["hash"] for x in rpc})==11
         and len({x["tx"] for x in balances})==11,
         "missing/duplicate original 11 signed txs or 22 direction logs")
    result=[]
    for selected in plan["rounds"]:
        r={"p2_index":selected["p2_index"],"owner":selected["wallet"],
           "token":selected["token"],"exact_CA":selected["exact_CA"],
           "original_signed_txs":[]}
        buy=sell=native=0
        for source in selected["selected_original_txs"]:
            matches=[x for x in rpc if x["original"]["hash"]==source["hash"]]
            states=[x for x in balances if x["tx"]==source["hash"]]
            txlogs=[x for x in events if x["hash"]==source["hash"]]
            must(len(matches)==len(states)==1 and len(txlogs)==2
                 and {x["direction"] for x in txlogs}=={"IN","OUT"},
                 "source signer tx/balance/exact CA event missing/duplicated")
            rpc_tx=matches[0];snap=states[0]
            must(rpc_tx["original"]["p2_index"]==selected["p2_index"]
                 and rpc_tx["original"]["wallet"].lower()==selected["wallet"].lower()
                 and rpc_tx["original"]["ca"].lower()==selected["exact_CA"].lower()
                 and rpc_tx["original"]["block"]==source["block"]
                 and rpc_tx["status"] in ("FULL_SUCCESS_RECEIPT","OWNER_VERIFIED_RECEIPT_TRUNCATED")
                 and rpc_tx["tx"]["hash"].lower()==source["hash"].lower()
                 and rpc_tx["tx"]["from"].lower()==selected["wallet"].lower()
                 and int(rpc_tx["tx"]["chainId"],16)==56
                 and int(rpc_tx["tx"]["blockNumber"],16)==source["block"]
                 and snap["p2"]==selected["p2_index"]
                 and snap["block"]==source["block"]
                 and snap["before_block"]==source["block"]-1
                 and snap["owner"].lower()==selected["wallet"].lower()
                 and snap["before"]["status"]==snap["after"]["status"]=="COMPLETE"
                 and snap["delta_wei"]==str(int(snap["after"]["wei"])-int(snap["before"]["wei"])),
                 "unconfirmed owner EOA signed identity or original N-1/N BNB balance")
            if rpc_tx["status"]=="FULL_SUCCESS_RECEIPT":
                proof=rpc_tx.get("receipt") or {}
                try:
                    gas=int(proof.get("gasUsed") or "",16)
                    gas_price=int(proof.get("effectiveGasPrice") or "",16)
                except (TypeError,ValueError):
                    raise ValueError("invalid full receipt gas: missing or truncated body")
                must(proof.get("status")=="0x1" and gas>0 and gas_price>0,
                     "full original receipt must be successful with paid gas")
            else:
                must("receipt" not in rpc_tx or rpc_tx["receipt"] is None,
                     "truncated original receipt must not contain claimed full receipt body")
            raw=[]
            identity=set()
            for e in txlogs:
                must(e["status"]=="COMPLETE" and e["ca"].lower()==selected["exact_CA"].lower()
                     and e["owner"].lower()==selected["wallet"].lower()
                     and e["block"]==source["block"],"one-block ERC20 source incomplete")
                for log in e["logs"]:
                    if log["transactionHash"].lower()!=source["hash"].lower():continue
                    must(log["address"].lower()==selected["exact_CA"].lower()
                         and log["topics"][0]==TRANSFER and len(log["topics"])==3
                         and log.get("removed") is False
                         and int(log["blockNumber"],16)==source["block"],
                         "original ERC20 transfer not a canonical live log")
                    key=(log["blockHash"],log["transactionHash"],log["logIndex"])
                    must(key not in identity,"duplicated original ERC20 log index")
                    identity.add(key)
                    item={"direction":e["direction"],"raw":str(int(log["data"],16)),
                          "idx":log["logIndex"],"block":log["blockNumber"],
                          "tx":log["transactionHash"],
                          "to":"0x"+log["topics"][2][-40:],
                          "from":"0x"+log["topics"][1][-40:],
                          "removed":False}
                    must((e["direction"]=="IN" and item["to"].lower()==selected["wallet"].lower())
                         or (e["direction"]=="OUT" and item["from"].lower()==selected["wallet"].lower()),
                         "source original EOA receiver/sender invalid")
                    raw.append(item)
            tin=sum(int(x["raw"]) for x in raw if x["to"].lower()==selected["wallet"].lower())
            tout=sum(int(x["raw"]) for x in raw if x["from"].lower()==selected["wallet"].lower())
            must((tin>0)!=(tout>0),"one selected original tx must buy or sell token")
            buy+=tin;sell+=tout;native+=int(snap["delta_wei"])
            r["original_signed_txs"].append({
                "tx":source["hash"],"block":source["block"],
                "original_signed_EOA":selected["wallet"],
                "receipt_status":rpc_tx["status"],
                "source_original_receipt_success":rpc_tx.get("receipt",{}).get("status","TRUNCATED_NO_FULL"),
                "token_received_raw":str(tin),"token_sent_raw":str(tout),
                "native_block_delta_wei":snap["delta_wei"],
                "owner_token_log_count":len(raw),
                "token_logs":raw
            })
        must(buy>0 and buy==sell and str(native)==selected["source_native_block_scope_net_wei"],
             "original episode token/BNB block-scope != frozen P2 or incomplete sale")
        r.update({
            "raw_original_token_bought":str(buy),
            "raw_original_token_sold":str(sell),"raw_inventory_remaining":"0",
            "native_owner_event_block_scope_delta_wei":str(native),
            "native_scope_sign":selected["source_net_sign"],
            "full_receipt_success_count":sum(x["receipt_status"]=="FULL_SUCCESS_RECEIPT" for x in r["original_signed_txs"]),
            "receipt_truncated_count":sum(x["receipt_status"]=="OWNER_VERIFIED_RECEIPT_TRUNCATED" for x in r["original_signed_txs"]),
            "actual_quote_gas_complete_owner_round":"UNRESOLVED",
            "first_public_executable_U":"UNRESOLVED",
            "followable_1_5_15_min":"UNRESOLVED"
        })
        result.append(r)
    checks=[{"p2":x["p2"],"block":x["block"],"status":x["status"],
             "error":x.get("error"),"original_tx_event_count":sum(z["transactionHash"]==x["tx"] for z in x["logs"])}
            for x in wbnb["rows"]]
    must(len(checks)==5 and checks[0]["status"]=="COMPLETE"
         and sum(x["status"]=="TRUNCATED_OR_ERROR" for x in checks)==4,
         "source original WBNB readback truncation must remain explicit")
    full=sum(r["full_receipt_success_count"] for r in result)
    truncated=sum(r["receipt_truncated_count"] for r in result)
    must(full==5 and truncated==6
         and [r["native_scope_sign"] for r in result]==[
            "POSITIVE_NATIVE_SCOPE","NEGATIVE_NATIVE_SCOPE",
            "NEGATIVE_NATIVE_SCOPE","POSITIVE_NATIVE_SCOPE","NEGATIVE_NATIVE_SCOPE"],
         "original 5 source cases lost negative or truncated evidence")
    return {
      "schema":"BSC_P4C_DDAC_ADFF_A83B_FIVE_SOURCE_ORIGINAL_TOKEN_CLOSED_CASHFLOW_PENDING",
      "scope":SCOPE,
      "source_manifest":[{"path":PREFIX+n,"git_blob_sha":h} for n,h in PINS],
      "summary":{
         "frozen_wallets":3,"frozen_major_exact_CAs":2,
         "source_preselected_rounds":5,"source_preselected_signed_txs":11,
         "verified_owner_signed_chain56_txs":11,
         "original_token_full_inventory_closed_rounds":5,"original_token_inconsistent_rounds":0,
         "owner_native_historical_blocks_complete":11,
         "complete_full_success_receipts":5,"receipt_body_truncated":6,
         "p2_positive_native_block_scope":2,"p2_negative_native_block_scope":3,
         "source_proven_new_realized_BNB_profit_rounds":0,
         "source_proven_new_realized_BNB_loss_rounds":0,
         "first_global_observer_U_qualified":0,"production":"NO_GO"
      },
      "rounds":result,"wbnb_source_status":checks
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
