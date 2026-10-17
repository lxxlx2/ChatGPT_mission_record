#!/usr/bin/env python3
"""P4-B: original 239E opposite signed outcomes vs two independent Pancake V2 math quotes.

Historical read-only evidence. Does NOT simulate stateful hypothetical buy+sell, token
transfers, gas, tax, public observer delivery or 1/5/15 minute returns.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = {
    "freeze": ("bsc-meme-address-model-v1-p4b-239e-dragon-two-exit-v2-quote-precommit-2026-10-18.json",
               "097cc5d638fea3c79ee83d1600115cd0316a3020"),
    "readback": ("bsc-meme-address-model-v1-p4b-239e-dragon-two-exit-v2-two-sided-math-readback-2026-10-18.json",
                 "cc09edff6a464b21ab1609980becc1afa4548ad1"),
    "original_real": ("bsc-meme-address-model-v1-p4c-239e-dragon-two-owner-native-settlements-2026-10-15.json",
                      "46e90123b98d5324e05388b17b8a3bbb77cb5361"),
    "old_19_quote": ("bsc-meme-address-model-v1-p4b-19ca-v2-001wbnb-router-math-quotes-2026-10-14.json",
                     "1f44ed58bab1dec1b4ccdc4cc449dde90d6131e7"),
    "old_19_precommit": ("bsc-meme-address-model-v1-p4b-19ca-v2-router-quote-precommit-2026-10-14.json",
                         "b1e39dbd718cd18acad29b5a3c0275eeca852f06"),
}

def check(ok, reason):
    if not ok:
        raise ValueError("P4B_239E_EXIT_MATH_" + reason)

def load(root=ROOT):
    out={}
    for k,(name,pin) in SOURCES.items():
        content=(root/name).read_bytes()
        digest=hashlib.sha1(b"blob "+str(len(content)).encode()+b"\0"+content).hexdigest()
        check(digest==pin, "PINNED_SOURCE_CHANGED_"+k)
        out[k]=json.loads(content)
    return out

def word(value):
    return f"{int(value):064x}"

def address_word(value):
    check(isinstance(value,str) and len(value)==42 and value.startswith("0x"),
          "BAD_HEX_ADDRESS")
    return value[2:].lower().rjust(64,"0")

def calldata(amount, token_in, token_out):
    return "0xd06ca61f"+word(amount)+word(64)+word(2)+address_word(token_in)+address_word(token_out)

def all_words(result, count, kind):
    check(isinstance(result,str) and result.startswith("0x") and
          len(result)==2+64*count and
          all(c in "0123456789abcdefABCDEF" for c in result[2:]),
          "BAD_ABI_"+kind)
    return [int(result[2+i*64:2+(i+1)*64],16) for i in range(count)]

def get_reserves(raw):
    a,b,ts=all_words(raw,3,"RESERVES")
    check(a>0 and b>0 and 0<=ts<=0xffffffff,"POOL_NOT_LIQUID")
    return a,b,ts

def get_two_amounts(raw):
    offset,n,amount_in,amount_out=all_words(raw,4,"ROUTER_DYNAMIC_ARRAY")
    check(offset==32 and n==2 and amount_in>0 and amount_out>0,
          "BAD_ROUTER_2_AMOUNTS_ABI")
    return amount_in,amount_out

def math_quote(raw_in, reserve_in, reserve_out):
    return raw_in*9975*reserve_out//(reserve_in*10000+raw_in*9975)

def build(d):
    freeze,readback,real,old,legacy=(d[k] for k in
       ("freeze","readback","original_real","old_19_quote","old_19_precommit"))
    check(readback["source_prefreeze"]=={
       "file":SOURCES["freeze"][0],
       "git_blob_sha":SOURCES["freeze"][1],
       "precommitted_before_any_rpc":True} and
       freeze["max_calls"]==8 and freeze["zero_retries"] is True and
       readback["exact_calls_precommitted"]==readback["exact_calls_executed"]==
       readback["successes"]==8 and readback["retries"]==0 and
       len(readback["calls"])==8 and len(readback["cases"])==2 and
       readback["evidence_grade"]==
         "ALCHEMY_TOOL_RETURN_HEX_AND_TOOL_CALL_ARGS_NOT_PROVIDER_TRANSPORT_FULL",
       "FIXED_EIGHT_TOOL_CALLS_AND_GRADE")
    check(freeze["source_pins"]=={
       "original_two_native_rounds":{"path":SOURCES["original_real"][0],"git_blob":SOURCES["original_real"][1]},
       "original_19_Pancake_V2_math":{"path":SOURCES["old_19_quote"][0],"git_blob":SOURCES["old_19_quote"][1]},
       "original_19_V2_router_freeze":{"path":SOURCES["old_19_precommit"][0],"git_blob":SOURCES["old_19_precommit"][1]},
       "historic_balance_readback_13":{
        "path":"bsc-meme-address-model-v1-p4b-2026-thirteen-historic-erc20-owner-balances-actual-readback-2026-10-18.json",
        "git_blob":"7e930c57fb5ba3a3dfd795575c059ade9f8a387d"}
       } and
       freeze["fixed_hypothetical_gross_WBNB_amount_in_wei"]=="10000000000000000" and
       freeze["fee_formula_bps"]=="9975/10000" and
       freeze["network"]==readback["network"]=="bnb-mainnet" and
       freeze["router_selector"]=="0xd06ca61f" and
       freeze["pool_reserves_selector"]=="0x0902f1ac",
       "PRECOMMIT_SOURCES_OR_FIXED_001_WBNB")
    check(freeze["gates"]=={
        "source_status":"P4B_PARTIAL","public_executable_U":"UNRESOLVED",
        "quote_both_directions_only":"MATH_NOT_STATEFUL_EXECUTION",
        "historical_fixed_delay_1_5_15min_follower_returns":"UNRESOLVED",
        "P5":"BLOCKED","production":"NO_GO",
        "permissions":"NO_MERGE NO_DEPLOY NO_GMAIL NO_TRADE"} and
       readback["gates"]=={
        "P4_B":"PARTIAL","PUBLIC_EXECUTABLE_U":"UNRESOLVED",
        "P5":"BLOCKED","PRODUCTION":"NO_GO",
        "permissions":"NO_MERGE NO_DEPLOY NO_GMAIL NO_TRADE"} and
       readback["assertions"]=={
        "buy_and_sell_quote_sides":"MATH_ONLY_NOT_STATEFUL_EXECUTION",
        "real_owner_actual_2_round_economics":"SOURCE_VERIFIED_BUT_DIFFERENT_SIZE_AND_ROUTE",
        "not_actual_provider_wire_transcript":True,
        "no_token_transfer_execution":True,"no_owner_observer_delivery_timestamp":True,
        "no_fixed_delay_1_5_15min":True,"no_follow_profit_claim":True},
       "NO_FOLLOWER_ROI_PROMOTION")
    check(len(real["rounds"])==len(freeze["rounds"])==2 and
          old["summary"]["raw_historical_v2_router_buy_quotes_complete"]==19 and
          legacy["router"]==freeze["router"] and
          legacy["quote_CA"]==freeze["quote_CA_WBNB"] and
          legacy["router_selector"]==freeze["router_selector"],
          "ORIGINAL_V2_FIXED_MARKET")
    known=next(q for q in old["rows"] if q["exact_CA"]==freeze["exact_CA"])
    check(known["pool"]==freeze["pool"] and
          known["first_positive_reserves_block"]<freeze["rounds"][0]["owner_buy_block"] and
          known["quote_token"]=="WBNB" and
          known["pancake_v2_fee_multiplier"]=="9975/10000",
          "EXACT_PAIR_AND_VENUE_GRADE")
    W=freeze["quote_CA_WBNB"]
    T=freeze["exact_CA"]
    P=freeze["pool"]
    R=freeze["router"]
    stake=int(freeze["fixed_hypothetical_gross_WBNB_amount_in_wei"])
    rows=[]
    for i,(item,prior,actual) in enumerate(zip(freeze["rounds"],real["rounds"],readback["cases"])):
        check(item["case"]==actual["label"] and
              item["owner_real_native_net_wei"]==actual["owner_actual_signed_native_net_wei"]==
                 prior["original_native_wallet_net_wei"] and
              prior["owner"]==freeze["owner"] and prior["exact_CA"]==T and
              prior["txs"][0]["hash"]==item["owner_real_buy_signed_hash"] and
              prior["txs"][-1]["hash"]==item["owner_real_sell_signed_hash"] and
              prior["txs"][0]["block"]==item["owner_buy_block"] and
              prior["txs"][-1]["block"]==item["owner_actual_sell_block"] and
              int(item["owner_buy_block"])+1==int(item["quote_buy_read_block"]) and
              int(item["owner_actual_sell_block"])-1==int(item["quote_sell_read_block"]),
              "REAL_OWNER_NEGATIVE_POSITIVE_EPISODE_IDENTITY")
        check([x["action"] for x in prior["txs"]]==
               (["BUY","BUY","SELL"] if i==0 else ["BUY","SELL"]) and
              prior["token_inventory_residual_raw"]=="0" and
              (int(prior["original_native_wallet_net_wei"])>0)==(i==1),
              "REAL_OWNER_SIGNED_NATIVE_AND_INVENTORY")
        calls=readback["calls"][4*i:4*i+4]
        check([c["phase"] for c in calls]==[
              "BUY_PAIR_RESERVES","BUY_ROUTER_WBNB_TO_DRAGON",
              "PRE_OWNER_SELL_PAIR_RESERVES","PRE_OWNER_SELL_ROUTER_DRAGON_TO_WBNB"] and
              all(c["case"]==item["case"] and c["provider_full_wire_record"] is False and
                  c["tool_return_parseable_hex"] is True for c in calls),
              "PHASE_AND_PROVIDER_TRANSPORT_PROVENANCE")
        expected_buy=calldata(stake,W,T)
        for j,c in enumerate(calls):
            args=c["tool_invoked_with"]
            to=P if j in (0,2) else R
            block=item["quote_buy_read_block"] if j in (0,1) else item["quote_sell_read_block"]
            check(args=={"network":"bnb-mainnet","method":"eth_call",
                   "to":to,"calldata":("0x0902f1ac" if j in (0,2) else
                       (expected_buy if j==1 else calldata(int(actual["buy_maths_quote_dragon_out_raw"]),T,W))),
                   "blockTag":hex(block),"from":None,"value":None},
                   "BOUNDED_ABI_REQUEST_SELF_CONSISTENCY_ONLY")
        buy_0,buy_1,buy_updated=get_reserves(calls[0]["tool_return_hex"])
        sell_0,sell_1,sell_updated=get_reserves(calls[2]["tool_return_hex"])
        actual_buy_in,actual_buy_out=get_two_amounts(calls[1]["tool_return_hex"])
        actual_sell_in,actual_sell_out=get_two_amounts(calls[3]["tool_return_hex"])
        check(actual_buy_in==stake and actual_sell_in==actual_buy_out and
              actual_buy_out==int(actual["buy_maths_quote_dragon_out_raw"]) and
              actual_sell_out==int(actual["sell_maths_quote_WBNB_out_wei"]) and
              actual["hypothetical_fixed_WBNB_in_wei"]==str(stake) and
              actual["strictly_not_realizable_profit"] is True,
              "TWO_QUOTE_AMOUNTS_AND_EXPLICIT_NOT_REALIZED")
        check(math_quote(actual_buy_in,buy_0,buy_1)==actual_buy_out and
              math_quote(actual_sell_in,sell_1,sell_0)==actual_sell_out,
              "REAL_POOL_FEE_MATH_BOTH_END_BLOCKS")
        delta=actual_sell_out-stake
        check(delta==int(actual["two_independent_static_quote_gross_delta_wei"]) and
              (delta>0)==(i==1) and
              (int(prior["original_native_wallet_net_wei"])>0)==(delta>0),
              "GROSS_MATH_DIRECTION_MATCHES_ORIGINAL_REAL_OWNER_DIRECTION_ONLY")
        rows.append({
             "case":item["case"],"owner_original_real_signed_net_wei":prior["original_native_wallet_net_wei"],
             "buy_quoted_block_end":item["quote_buy_read_block"],
             "pre_owner_real_sell_quoted_block_end":item["quote_sell_read_block"],
             "fixed_gross_hypothetical_WBNB_in_wei":str(stake),
             "static_buy_dragon_token_out_raw":str(actual_buy_out),
             "static_reverse_WBNB_out_wei":str(actual_sell_out),
             "static_two_snapshot_gross_math_delta_wei":str(delta),
             "static_two_snapshot_gross_math_delta_bps_trunc":
                 ("-" if delta<0 else "")+str(abs(delta)*10000//stake),
             "buy_pair_WBNB_reserve":str(buy_0),"buy_pair_Dragon_reserve":str(buy_1),
             "sell_pair_WBNB_reserve":str(sell_0),"sell_pair_Dragon_reserve":str(sell_1),
             "getReserves_blockTimestampLast_not_quote_blockTimestamp":[buy_updated,sell_updated],
             "hypothetical_buy_affected_later_pool_state":False,
             "tax_or_real_sell_transfer_tested":False,
             "causal_follower_realized_return":"UNRESOLVED",
             "can_publish_as_1_5_15min_net":"NO"})
    return {
      "schema":"BSC_P4B_2026_239E_DRAGON_TWO_OPPOSITE_OWNER_ROUNDS_UNEXECUTED_SPOT_EXIT_MATH",
      "source_pins":{k:s[1] for k,s in SOURCES.items()},
      "scope":"TWO_ALREADY_SELECTED_239E_ORIGINAL_REAL_ROUNDS_AND_EIGHT_NON_STATEFUL_HISTORICAL_READS",
      "samples":rows,
      "conclusion":"STATIC_MATH_QUOTES_NEGATIVE_FIRST_POSITIVE_SECOND_LIKE_REAL_OWNER_SIGNS_BUT_NOT_CAUSAL_FOLLOWER_PNL",
      "observed_full_provider_wire_request_transcript":False,
      "verified_executable_buy_sell_with_Gas_and_Tax":False,
      "actual_public_observer_delivery_time":"UNRESOLVED",
      "entry_at_fixed_1_5_15minute_delay":"UNRESOLVED",
      "P4_B":"PARTIAL","PUBLIC_EXECUTABLE_U":"UNRESOLVED",
      "P5":"BLOCKED","PRODUCTION":"NO_GO"
    }

if __name__=="__main__":
    print(json.dumps(build(load()),ensure_ascii=False,indent=2,sort_keys=True))
