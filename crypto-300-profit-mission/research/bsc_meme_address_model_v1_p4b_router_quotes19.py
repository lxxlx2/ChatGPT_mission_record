#!/usr/bin/env python3
"""Reconstruct historical PancakeSwap V2 mathematical quotes for all 19 frozen CA.

No simulation of token tax, WBNB wrap, transfer, sell, actual router transaction,
historical public arrival, launchpad paths, wallet collateral or profit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFIX = "crypto-300-profit-mission/research/"
PINS = (("bsc-meme-address-model-v1-p4b-19ca-v2-router-quote-precommit-2026-10-14.json","b1e39dbd718cd18acad29b5a3c0275eeca852f06"),("bsc-meme-address-model-v1-p4b-v2-first-observable-buy-part1-2026-10-14.json","e5a2ff572815199c684d6eb46d85f8a87d96bfca"),("bsc-meme-address-model-v1-p4b-v2-first-observable-buy-part2-2026-10-14.json","5521dd9b0d3570c370e2552dc3b99ff0d753ddb5"),("bsc-meme-address-model-v1-p4b-v2-first-observable-buy-part3-2026-10-14.json","b384af035f3c901c26f554b7376ca5244e86f05f"),("bsc-meme-address-model-v1-p4b-v2-first-observable-buy-part4-2026-10-14.json","70a822a3b431fa72b8dfa51106eb10e8ac4deab7"),("bsc-meme-address-model-v1-p4b-v2-first-observable-buy-part5-2026-10-14.json","2042288fd5cca42626ca0614a49073b1e54dc192"))
SCHEMA = "BSC_P4B_19CA_001WBNB_HISTORICAL_V2_ROUTER_MATH_QUOTES"
DESCRIPTION = "Historical frozen V2 WBNB pair end-state at block first liquidity+1, actual eth_call router getAmountsOut for fixed 0.01 WBNB, exact 0.25% V2 fee and spot-mid reference; mathematical quotes only, no token transfer/reverse sale/gas or global U"

def require(flag, message):
    if not flag:
        raise ValueError(message)

def blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def load(root=ROOT):
    docs = []
    for filename, pinned in PINS:
        data = (root / filename).read_bytes()
        require(blob_sha(data)==pinned, "Git source blob mismatch: " + filename)
        docs.append(json.loads(data))
    return docs

def word(encoded, index, count):
    require(isinstance(encoded,str) and encoded.startswith("0x")
            and len(encoded) == 2 + 64 * count, "wrong ABI length")
    return int(encoded[2+index*64:2+(index+1)*64],16)

def build(sources):
    require(len(sources)==6, "must supply six source inputs")
    freeze,*parts = sources
    require(freeze["schema"]=="BSC_P4B_FROZEN19_FIRST_OBSERVABLE_V2_ROUTER_QUOTE_PRECOMMIT"
            and freeze["network"]=="bnb-mainnet"
            and freeze["router"]=="0x10ed43c718714eb63d5aa57b78b54704e256024e"
            and freeze["router_selector"]=="0xd06ca61f"
            and freeze["pair_selector"]=="0x0902f1ac"
            and freeze["quote_CA"]=="0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
            and freeze["fixed_input_WBNB_wei"]=="10000000000000000"
            and freeze["production"]=="NO_GO"
            and len(freeze["rows"])==19,
            "historical quote cohort changed")
    raw=[]
    for i,part in enumerate(parts):
        expected=(i*4,min(18,(i+1)*4-1))
        require(part["schema"]=="BSC_P4B_V2_FIRST_OBSERVABLE_RAW_RESERVES_AND_ROUTER_BUY_QUOTE"
                and part["part"]==i+1
                and part["index_range"]==list(expected)
                and part["precommit_blob_sha"]==PINS[0][1]
                and part["production"]=="NO_GO", "raw part scope or origin changed")
        raw.extend(part["rows"])
    require(len(raw)==19 and len({x["pool"] for x in raw})==19, "duplicate or missing pair")
    rows=[]
    W=freeze["quote_CA"].lower()
    stake=int(freeze["fixed_input_WBNB_wei"])
    for idx,(claim,actual) in enumerate(zip(freeze["rows"],raw)):
        require(claim["index"]==actual["index"]==idx
                and actual["read_status"]=="COMPLETE"
                and actual["token"]==claim["token"]
                and actual["exact_CA"]==claim["exact_CA"]
                and actual["pool"]==claim["pool"]
                and actual["read_block"]==claim["read_block"]==claim["first_positive_reserves_block"]+1
                and actual["first_positive_reserves_block"]==claim["first_positive_reserves_block"]
                and actual["stake_wei"]==claim["stake_wei"]==freeze["fixed_input_WBNB_wei"]
                and actual["no_token_transfer_executed"] is True,
                "source selection, source block, or execution evidence changed")
        reserve0=word(actual["raw_getReserves"],0,3)
        reserve1=word(actual["raw_getReserves"],1,3)
        # Pair token0/1 sorting is by uint160 address ascending, not pool quote label.
        wbnb_is_zero=W < claim["exact_CA"].lower()
        rW,rT=(reserve0,reserve1) if wbnb_is_zero else (reserve1,reserve0)
        require(rW>0 and rT>0, "one side of pair has no liquidity")
        raw_quote=actual["raw_router_buy_quote"]
        require(word(raw_quote,0,4)==32 and word(raw_quote,1,4)==2
                and word(raw_quote,2,4)==stake, "ABI getAmountsOut dynamic array mismatch")
        router_target=word(raw_quote,3,4)
        calculated=stake*9975*rT//(rW*10000+stake*9975)
        require(calculated>0 and router_target==calculated,
                "router raw quote disagrees with pinned historical reserves/9975 fee")
        bps=10000-(router_target*10000*rW)//(stake*rT)
        require(0<=bps<=10000, "invalid spot impact")
        rows.append({
            "index":idx,"token":claim["token"],"exact_CA":claim["exact_CA"],"pool":claim["pool"],
            "first_positive_reserves_block":claim["first_positive_reserves_block"],
            "historical_read_block":claim["read_block"],
            "quote_token":"WBNB","quote_in_wei":claim["stake_wei"],
            "pair_wbnb_reserve_wei":str(rW),"pair_target_reserve_raw":str(rT),
            "quote_target_out_raw":str(router_target),
            "pancake_v2_fee_multiplier":"9975/10000",
            "router_matches_pair_reserves":True,
            "spot_mid_vs_router_output_gap_bps":bps,
            "quoted_tokens_are_unadjusted_for_tax":True,
            "historical_token_transfer_simulation":"NOT_PERFORMED",
            "historical_reverse_sell":"UNRESOLVED",
            "gas_and_actual_execution":"UNRESOLVED",
            "global_market_first_U":"UNRESOLVED",
            "qualified_23_wallet_opportunity":"UNRESOLVED",
            "production":"NO_GO"
        })
    gaps=[x["spot_mid_vs_router_output_gap_bps"] for x in rows]
    summary={
        "exact_CAs":19,
        "raw_historical_pair_reads_complete":19,
        "raw_historical_v2_router_buy_quotes_complete":19,
        "reserve_formula_cross_checks_passed":19,
        "fixed_input_WBNB_wei":freeze["fixed_input_WBNB_wei"],
        "descriptive_min_price_gap_bps":min(gaps),
        "descriptive_max_price_gap_bps":max(gaps),
        "quote_read_success_but_tax_sellability_unknown":19,
        "first_global_market_U_qualified":0,
        "production":"NO_GO"
    }
    return {
        "schema":SCHEMA,"scope":DESCRIPTION,
        "source_manifest":[{"path":PREFIX+n,"git_blob_sha":h} for n,h in PINS],
        "summary":summary,"rows":rows
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-dir",type=Path,default=ROOT)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.write_text(json.dumps(build(load(args.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
