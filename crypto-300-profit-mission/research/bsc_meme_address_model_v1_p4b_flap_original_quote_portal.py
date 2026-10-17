#!/usr/bin/env python3
"""Reconcile actual original Flap Portal quote-token receipts; no follower U or owner PnL."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCES={
    "result": ("bsc-meme-address-model-v1-p4b-flap-major2-actual-portal-quote-transfers-2026-10-17.json",
               "db2e47010025fde7adf150c408748806e594a4c2"),
    "from_freeze": ("bsc-meme-address-model-v1-p4b-flap-original-buyer-quote-outflow-precommit-2026-10-17.json",
                    "dcf3ec9a919e8fccfb77adb880ce59f5a94926ed"),
    "to_freeze": ("bsc-meme-address-model-v1-p4b-flap-original-buy-quote-to-portal-precommit-2026-10-17.json",
                  "744146ac730c0f7f2b69539bb63045b5b85b0985"),
    "original": ("bsc-meme-address-model-v1-p4b-flap-major2-original-buys-and-quotes-2026-10-14.json",
                 "d69f2ddfade437a1d8b0fc49585eb4ca0f9268e9")
}
def require(cond,reason):
    if not cond:
        raise ValueError("P4B_FLAP_PORTAL_QUOTE_"+reason)
def load(root=ROOT):
    docs={}
    for key,(filename,sha) in SOURCES.items():
        raw=(root/filename).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        require(actual==sha,"SOURCE_BLOB_DRIFT_"+key)
        docs[key]=json.loads(raw)
    return docs
def replay(data):
    result,first,second,original=(data[n] for n in
                                  ("result","from_freeze","to_freeze","original"))
    require(result["precommits"] ==
            {"from_original_signer_ERC20_Transfer_oneblock_sha":SOURCES["from_freeze"][1],
             "to_portal_ERC20_Transfer_oneblock_sha":SOURCES["to_freeze"][1]} and
            result["source_original_first_buys_git_blob"] == SOURCES["original"][1],
            "PRECOMMIT_PROVENANCE")
    require(len(result["rows"])==len(first["cases"])==len(second["cases"])==
            len(original["rows"])==2 and
            [z["token"] for z in result["rows"]]==["牛来","MARSCOIN"],
            "SCOPE_EXACTLY_TWO")
    require(result["portal"] == second["portal"] ==
            "0xe2ce6ab80874fa9fa2aae65d277dd6b8e65c9de0" and
            result["topic0"] == first["topic0"] == second["topic0"] ==
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            "ABI_FILTER")
    require(result["gates"]==
            {"original_EOA_complete_quote_funding":"UNRESOLVED",
             "public_first_executable_U":"UNRESOLVED","P5":"BLOCKED",
             "production":"NO_GO","permissions":"NO_MERGE NO_DEPLOY NO_GMAIL NO_TRADE"},
            "PREMATURE_FUNDING_OR_U")
    output=[]
    for i,row in enumerate(result["rows"]):
        a,bb,source=first["cases"][i],second["cases"][i],original["rows"][i]
        require(row["token"]==a["token"]==bb["token"]==source["token"] and
                row["token_ca"]==a["tokenCA"]==source["exact_CA"] and
                row["quote_ca"]==a["quoteCA"]==bb["quote"]==source["actual_quote_CA"],
                "TOKEN_QUOTE_CA_ID")
        require(row["signed_buy_original_tx"]==a["original_signed_buy_tx"]==
                bb["original_tx"]==source["signed_tx_hash"] and
                row["original_signed_eoa"]==a["signer"]==source["original_EOA_signer"] and
                row["block"]==a["blockN"]==bb["block"]==source["first_sampled_buy_block"],
                "SOURCE_ORIGINAL_TX_AND_SIGNER")
        require(row["from_signer_quote_ERC20_Transfer_filter_status"]=="COMPLETE_PARSED_JSON" and
                row["from_signer_quote_ERC20_Transfer_count_in_N"]==0 and
                row["to_portal_quote_ERC20_Transfer_filter_status"]=="COMPLETE_PARSED_JSON" and
                row["to_portal_oneblock_all_transfer_count"]==len(row["to_portal_transfers"])==
                (1 if i==0 else 2),
                "FILTERED_QUERY_STATUS_OR_COUNT")
        require(row["source_Original_TokenBought_cost_raw"]==
                source["portal_event_quote_spent_raw"] and
                row["source_Original_TokenBought_fee_raw"]==
                source["portal_event_fee_raw"] and
                int(source["portal_event_fee_raw"])>0 and
                source["original_first_purchase_event_match"]=="CONFIRMED",
                "SOURCE_TOKENBOUGHT_EVENT_COST")
        matched=[]
        seen=set()
        for log in row["to_portal_transfers"]:
            require(log["to"]==second["portal"] and
                    log["from"]!=row["original_signed_eoa"] and
                    log["from"].startswith("0x") and len(log["from"])==42 and
                    log["tx"].startswith("0x") and len(log["tx"])==66 and
                    (log["tx"],log["logIndex"]) not in seen,
                    "PORTAL_TRANSFER_DIRECTION_AND_UNIQUENESS")
            seen.add((log["tx"],log["logIndex"]))
            require(log["raw_value_hex"].startswith("0x") and
                    len(log["raw_value_hex"])==66,
                    "TRANSFER_RAW_AMOUNT_ENCODING")
            if log["tx"]==row["signed_buy_original_tx"]:
                matched.append(log)
        require(len(matched)==1 and
                row["nonmatching_sameblock_count"]==len(row["to_portal_transfers"])-1,
                "REAL_ORIGINAL_TX_MATCH_ONLY")
        value=int(matched[0]["raw_value_hex"],16)
        require(value==int(row["source_Original_TokenBought_cost_raw"])==
                int(row["matching_quote_from_intermediary_to_portal_raw"]) and
                value!=int(source["portal_event_quote_spent_raw"])+
                int(source["portal_event_fee_raw"]),
                "MATCHED_INTERMEDIARY_QUOTE_COST_NOT_GROSS_COST_PLUS_FEE")
        require(source["quote_symbol_is_not_assumed_USD"] is True and
                source["buyer_in_frozen_23"]=="NO" and
                source["causal_profit"]=="UNRESOLVED",
                "EXTERNAL_ORIGINAL_BUYER_PNL_UPGRADE")
        output.append({
            "token":row["token"],"quote_CA":row["quote_ca"],
            "original_signed_buy_tx":row["signed_buy_original_tx"],
            "quote_transfer_payer_is_original_EOA":False,
            "confirmed_portal_recipient_quote_from_intermediary":matched[0]["from"],
            "portal_quote_transfer_matches_TokenBought_cost_exactly":True,
            "matched_portal_received_quote_raw":str(value),
            "actual_signed_EOA_input_currency_and_funding":"UNRESOLVED",
            "separate_event_fee_settlement":"UNRESOLVED",
            "one_block_nonmatching_other_transfer_count":row["nonmatching_sameblock_count"],
            "public_first_executable_U":"UNRESOLVED",
            "same_wallet_realized_follower_profit":"UNRESOLVED"
        })
    return {"schema":"BSC_P4B_FLAP_FIRST_SIGNED_BUY_PORTAL_INTERMEDIARY_QUOTE_MATCHED_SOURCE_REPLAY",
            "source_grading":"TOOL_PARSED_FILTERED_FIELDS_NOT_FULL_RPC_RAW_LOG_PINNED",
            "source_sha":{k:v[1] for k,v in SOURCES.items()},
            "summary":{"selected_markets":2,"actual_original_tx_quote_to_portal_matches":2,
                       "direct_original_signed_EOA_quote_transfer_from_found":0,
                       "follower_public_executable_U":0,
                       "P4_B":"PARTIAL","P5":"BLOCKED","production":"NO_GO"},
            "rows":output}

if __name__=="__main__":
    print(json.dumps(replay(load()),ensure_ascii=False,indent=2,sort_keys=True))
