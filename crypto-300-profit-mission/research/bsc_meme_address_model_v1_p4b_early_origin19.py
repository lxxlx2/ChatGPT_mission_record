#!/usr/bin/env python3
"""P4-B all 19 original major-CA launch-transfer and Four.meme pre-DEX evidence.

Early ERC20 Transfer != executable buy, original-source first-page != full trade
history, and helper version zero or empty response != negative market evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4b-19ca-cross-venue-candidate-u-2026-10-14.json","49377dad6324a1089ca1233a7db6327443d0e4e6"),("bsc-meme-address-model-v1-p4b-19ca-fourmeme-helper3-precommit-2026-10-14.json","7200471e39e4d28b7d508627cb852dba2755420c"),("bsc-meme-address-model-v1-p4b-fourmeme-helper3-raw-part1-2026-10-14.json","3978a913e01a0d8989c7a17b53084c37252a9df6"),("bsc-meme-address-model-v1-p4b-fourmeme-helper3-raw-part2-2026-10-14.json","4812b475d89a0288c985e14709db601c1da4bb4c"),("bsc-meme-address-model-v1-p4b-fourmeme-helper3-raw-part3-2026-10-14.json","a327bf691bc70a04b4437fcadf2ed0d863b24b22"),("bsc-meme-address-model-v1-p4b-fourmeme-helper3-raw-part4-2026-10-14.json","dfaa1298725385b3eea64bae5a042dffef1e3b16"),("bsc-meme-address-model-v1-p4b-fourmeme-helper3-raw-part5-2026-10-14.json","355bfd41e57eb962e65c446566e590e25956f4ba"),("bsc-meme-address-model-v1-p4b-first10-erc20-pre-dex-precommit-2026-10-14.json","5e0d7b7ecc394520d643880bba725bad214d33d8"),("bsc-meme-address-model-v1-p4b-first10-erc20-pre-dex-part1-2026-10-14.json","a191f0ae9005a219a16de7f821dea9d6c32d60f1"),("bsc-meme-address-model-v1-p4b-first10-erc20-pre-dex-part2-2026-10-14.json","36d53bc08cca0d3b6bfa0d6f38b27b3e7fade24f"),("bsc-meme-address-model-v1-p4b-first10-erc20-pre-dex-part3-2026-10-14.json","accd1018be1d8c99deaae3acfbb98acc495364a1"),("bsc-meme-address-model-v1-p4b-first10-erc20-pre-dex-part4-2026-10-14.json","ed68cd1ae0245132ec1eafa8d7803d12c802d685"),("bsc-meme-address-model-v1-p4b-first10-erc20-pre-dex-part5-2026-10-14.json","7607887812df4ef0219bac8aa069776451b9249a"))
SCHEMA="BSC_P4B_19CA_EARLY_LAUNCH_ACTIVITY_BEFORE_SCOPED_DEX"
SCOPE="19 original exact CAs, first ten ERC20 transfers from chain genesis through first scoped active PancakeSwap pool block inclusive plus Four.meme Helper3 sampled just before that DEX liquidity; earlier ERC20 activity is not necessarily early executable trade; null and zero-helper keep unknown."
ZERO="0x"+"0"*40
FOUR_MANAGER="0x5c952063c7fc8610ffdb798152d69f0b9550762b"

def require(valid,message):
    if not valid:
        raise ValueError(message)

def git_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def load(root=ROOT):
    out=[]
    for n,pin in PINS:
        raw=(root/n).read_bytes()
        require(git_sha(raw)==pin,"source blob changed "+n)
        out.append(json.loads(raw))
    return out

def uinthex(data,i):
    require(isinstance(data,str) and data.startswith("0x") and len(data)==770,
            "expected 12-word Helper3 result")
    return int(data[2+64*i:2+64*(i+1)],16)

def build(docs):
    require(len(docs)==13,"wrong source cohort length")
    cross,hpre,*others=docs
    hparts=others[:5]
    tpre=others[5]
    tparts=others[6:]
    require(cross["summary"]["exact_CAs"]==19
            and cross["summary"]["scoped_active_pools"]==36
            and hpre["schema"]=="BSC_P4B_19CA_FOURMEME_HELPER3_HISTORICAL_ORIGIN_PRECOMMIT"
            and hpre["source_crossvenue_git_blob_sha"]==PINS[0][1]
            and hpre["selector_keccak256"]=="0x1f69565f"
            and hpre["helper_contract"]=="0xf251f83e40a78868fcfa3fa4599dad6494e46034"
            and tpre["schema"]=="BSC_P4B_19CA_FIRST_ERC20_TRANSFERS_UNTIL_EARLIEST_SCOPED_DEX_PRECOMMIT"
            and tpre["source_crossvenue_git_blob_sha"]==PINS[0][1]
            and tpre["order"]=="asc" and tpre["maxCount_hex"]=="0xa"
            and tpre["excludeZeroValue"] is False
            and all(z["production"]=="NO_GO" for z in docs),
            "original 19-token market and source controls not frozen")
    hs,ts=[],[]
    for j,(h,t) in enumerate(zip(hparts,tparts)):
        span=[j*4,min(18,j*4+3)]
        require(h["schema"]=="BSC_P4B_19CA_FOURMEME_HELPER3_PRE_SCOPED_LIQUIDITY_RAW"
                and h["part"]==j+1 and h["index_range"]==span
                and h["precommit_blob_sha"]==PINS[1][1], "Helper3 batch mismatch")
        require(t["schema"]=="BSC_P4B_19CA_FIRST_TEN_PRE_SCOPED_DEX_ERC20_RAW"
                and t["part"]==j+1 and t["index_range"]==span
                and t["precommit_blob_sha"]==PINS[7][1], "asset transfer batch mismatch")
        hs.extend(h["rows"])
        ts.extend(t["rows"])
    require(len(hs)==len(ts)==len(cross["rows"])==len(hpre["rows"])==len(tpre["rows"])==19,
            "all 19 market origins mandatory")
    output=[]
    for i,(src,h,t) in enumerate(zip(cross["rows"],hs,ts)):
        marketblock=src["scoped_first_active_block"]
        ca=src["exact_CA"]
        require(h["index"]==t["index"]==hpre["rows"][i]["index"]==tpre["rows"][i]["index"]==i
                and h["exact_CA"]==t["exact_CA"]==ca
                and h["helper_read_block"]==hpre["rows"][i]["helper_read_block"]==marketblock-1
                and t["earliest_scoped_active_block"]==tpre["rows"][i]["earliest_scoped_active_block"]==marketblock
                and t["to_block_hex"]==tpre["rows"][i]["to_block_hex"]
                and h["token"]==t["token"]==src["token"]
                and t["query_status"]=="COMPLETE"
                and isinstance(t["transfers"],list) and bool(t["transfers"])
                and len(t["transfers"])<=10, "original normalized 19 CA sample altered")
        logs=t["transfers"]
        blocks=[int(z["blockNum"],16) for z in logs]
        require(blocks==sorted(blocks)
                and all(0<=b<=marketblock for b in blocks)
                and all(z["rawContract"]["address"].lower()==ca.lower()
                        and z["category"]=="erc20" for z in logs),
                "first-page ERC20 transfer wrong token or ordering")
        f=logs[0]
        valid=h["rpc_status"]=="COMPLETE_12WORDS"
        if valid:
            v=uinthex(h["raw_getTokenInfo"],0)
            mgr="0x"+h["raw_getTokenInfo"][2+64+24:2+128].lower()
            status=("FOUR_MEME_V2_CANONICAL" if v==2 and mgr==FOUR_MANAGER else
                    "NO_RECOGNIZED_HELPER_MANAGER_AT_PROBE" if v==0 and mgr==ZERO else
                    "HELPER_UNEXPECTED_OR_UNKNOWN")
            launch=str(uinthex(h["raw_getTokenInfo"],6))
            liq=uinthex(h["raw_getTokenInfo"],11)
            require(liq in (0,1),"Helper3 liquidity bool out of range")
        else:
            require(h["rpc_status"]=="UNRESOLVED_OR_REVERT", "read status not recognized")
            status="HELPER_EMPTY_OR_UNREADABLE"
            v=None
            launch=None
            liq=None
        first_block=blocks[0]
        output.append({
            "index":i,"token":src["token"],"exact_CA":ca,
            "first_scoped_dex_positive_block":marketblock,
            "first_observed_erc20_transfer_block":first_block,
            "erc20_first_transfer_before_scoped_dex":first_block<marketblock,
            "blocks_from_first_observed_transfer_to_scoped_dex":marketblock-first_block,
            "source_initial_transfer_hash":f["hash"],
            "source_initial_transfer_from":f["from"],
            "source_initial_transfer_to":f["to"],
            "source_initial_transfer_mint_flag":f["from"].lower()==ZERO,
            "source_transfer_page_count":len(logs),
            "source_page_has_more":t["page_key_present"],
            "pre_dex_helper_status":status,
            "pre_dex_helper_read_block":h["helper_read_block"],
            "pre_dex_helper_version":v,
            "pre_dex_helper_launch_unix":launch,
            "pre_dex_helper_liquidity_added":None if liq is None else liq==1,
            "actual_first_launchpad_token_purchase":"UNRESOLVED",
            "first_global_buy_and_sell_U":"UNRESOLVED",
            "wallet_funds_at_U":"UNRESOLVED",
            "follower_pnl":"UNRESOLVED",
        })
    s={
        "exact_CAs":19,
        "complete_first10_transfer_index_reads":19,
        "token_transfer_initial_block_precedes_scoped_dex":sum(x["erc20_first_transfer_before_scoped_dex"] for x in output),
        "canonical_fourmeme_v2_at_pre_scoped_dex":sum(x["pre_dex_helper_status"]=="FOUR_MEME_V2_CANONICAL" for x in output),
        "unknown_or_empty_helper":sum(x["pre_dex_helper_status"]!="FOUR_MEME_V2_CANONICAL" for x in output),
        "actually_proven_first_market_U":0,
        "production":"NO_GO",
    }
    require((s["token_transfer_initial_block_precedes_scoped_dex"],
             s["canonical_fourmeme_v2_at_pre_scoped_dex"],
             s["unknown_or_empty_helper"])==(19,12,7),"frozen early market source numbers changed")
    return {"schema":SCHEMA,"scope":SCOPE,
            "source_manifest":[{"path":PREFIX+n,"git_blob_sha":sha} for n,sha in PINS],
            "summary":s,"rows":output}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
