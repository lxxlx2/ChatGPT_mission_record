#!/usr/bin/env python3
"""Frozen BSC external-wallet Dragon inventory window, not economic profit.

All selected historical token Transfer pages must close before any quantity
claim. Their amounts are not confirmed tokenIn wallet USDT cashflow or PnL.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FILES={
 "in1":("bsc-meme-address-model-v1-p4b-5e60-earlier-ten-inbound-dragon-cost-basis-censored-2026-10-18.json","cee0c1be380f9509d5c30b73cc64d1350ad66c87"),
 "in2out1":("bsc-meme-address-model-v1-p4b-5e60-historical-dragon-in-page2-out-page1-censored-2026-10-18.json","bcb9bb22e57c5030ecb8e0addd31b67d9b4bbf5d"),
 "in3out2":("bsc-meme-address-model-v1-p4b-5e60-historic-dragon-in3-out2-readback-2026-10-18.json","6635527c2e2f17b238165c25ebf10fb4d334feda"),
 "in4":("bsc-meme-address-model-v1-p4b-5e60-prior-inbound-page4-final-33in17out-2026-10-18.json","ec3fafb7d95f1928438f6cd3aa5a1bde32da252b"),
 "state":("bsc-meme-address-model-v1-p4b-5e60-real-opening-966415-and-33in17out-inventory-2026-10-18.json","7c732dddf4b7693b769cfd98a980d92dd5afeed4"), 
 "buy":("bsc-meme-address-model-v1-p4b-239e-r2-external-5e60-real-usdt-debit-gas-and-dragon-readback-2026-10-18.json","4288f9819f2815cb4d899c93116b23e19e6fe0ba")
}
def check(condition,key):
    if not condition:
        raise ValueError("P4B_5E60_INVENTORY_"+key)
def load(base=ROOT):
    found={}
    for key,(name,pin) in FILES.items():
        raw=(base/name).read_bytes()
        sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        check(sha==pin,"GIT_PIN_"+key)
        found[key]=json.loads(raw)
    return found
def audit(d):
    first,part,extra,last,state,buy=(d[x] for x in ("in1","in2out1","in3out2","in4","state","buy"))
    w="0x5e600e259e3cff0757e3736223685958665866c6"
    pair="0x22af7297243c4eef12e2d5a4f888b92e56bf127c"
    token="0xeccbb861c0dda7efd964010085488b69317e4444"
    check(first["returned_count"]==10 and first["pageKey_exists"] is True and
        first["complete_full_window"] is False and
        first["page_key_preserved"]==part["results"]["INBOUND_PAGE2"]["original_cursor"] and
        len(first["rows"])==10,"PAGE1_CURSOR")
    p2=part["results"]["INBOUND_PAGE2"]
    o1=part["results"]["OUTBOUND_PAGE1"]
    p3=extra["in_page3"]
    o2=extra["out_page2"]
    p4=last
    check(all(len(x)==n for x,n in [
        (p2["rows"],10),(o1["rows"],10),(p3["rows"],10),
        (o2["rows"],7),(p4["rows"],3)]) and
        p2["next_pageKey"]==p3["prevCursor"] and
        p3["nextCursor"]==p4["input_cursor"] and
        p4["remaining_pageKey"] is None and
        p4["window_complete_inbound_stream"] is True and
        o1["next_pageKey"]==o2["prevCursor"] and
        o2["nextCursor"] is None and
        o2["complete_for_bounded_outgoing_stream"] is True,
        "EXACT_PAGINATION_CHAIN")
    inbound=(
        [(x["block"],x["hash"],x["raw_Dragon_received"],x["from"],x["to"])
         for x in first["rows"]]+
        [(x["block"],x["hash"],x["raw_amount_uint"],x["from"],x["to"])
         for x in p2["rows"]]+
        [(x["block"],x["hash"],x["rawUint"],x["from"],x["to"])
         for x in p3["rows"]]+
        [(x["block"],x["hash"],x["rawUint"],x["from"],x["to"])
         for x in p4["rows"]])
    outbound=(
        [(x["block"],x["hash"],x["raw_amount_uint"],x["from"],x["to"])
         for x in o1["rows"]]+
        [(x["block"],x["hash"],x["rawUint"],x["from"],x["to"])
         for x in o2["rows"]])
    check(len(inbound)==33 and len(outbound)==17 and
        len({x[1] for x in inbound})==33 and
        len({x[1] for x in outbound})==17 and
        all(85900000 <= x[0] <= 85959961 for x in inbound+outbound) and
        all(inbound[i][0]<=inbound[i+1][0] for i in range(32)) and
        all(outbound[i][0]<=outbound[i+1][0] for i in range(16)) and
        all(x[3]==pair and x[4]==w for x in inbound) and
        all(x[3]==w and x[4]==pair for x in outbound),
        "EXACT_IN_AND_OUT_IDENTITIES")
    check(all(isinstance(x[2],str) and x[2].isdigit() and int(x[2])>0
              for x in inbound+outbound),"VALID_ERC20_UINT256_AMOUNTS")
    ins=sum(int(x[2]) for x in inbound)
    outs=sum(int(x[2]) for x in outbound)
    check(ins==2096771771412964976312348 and
          outs==2728013687115437116815271,
          "FROZEN_RAW_TRANSFER_TOTALS")
    check(state["contract"]==token and state["wallet"]==w and
          state["calls"]==2 and state["retries"]==0 and
          len(state["observations"])==2,"TWO_REAL_HISTORIC_BALANCES")
    old,new=state["observations"]
    check(old["block"]==85899999 and new["block"]==85959961 and
          len(old["rawResponse"])==len(new["rawResponse"])==66 and
          int(old["rawResponse"],16)==int(old["rawDecimal"]) and
          int(new["rawResponse"],16)==int(new["rawDecimal"]),
          "ACTUAL_CHAIN_BALANCE_HEX_MATCHES_RAW")
    opening=int(old["rawDecimal"])
    closing=int(new["rawDecimal"])
    check(opening==966415729394361448864776 and
          closing==335173813691889308361853 and
          opening+ins-outs==closing and
          state["fixed_window_transfers"]["inbound_count"]==33 and
          state["fixed_window_transfers"]["outbound_count"]==17 and
          state["fixed_window_transfers"]["inbound_raw"]==str(ins) and
          state["fixed_window_transfers"]["outbound_raw"]==str(outs) and
          state["fixed_window_transfers"]["owner_balance_match"] is True,
          "REAL_OPEN_PLUS_FLOW_EQUALS_REAL_CLOSE")
    check(buy["external_wallet_dragon_state"]["before_buy_raw"]==
          new["rawDecimal"] and
          buy["signed_Router_decoded"]["amountIn_USDT_raw"]==
              "1000000000000000000000" and
          buy["verification"]["actual_follower_net_return"]=="UNRESOLVED",
          "SAME_5E60_PRE_1000USDT_STATE_AND_NO_PNL_PROMOTION")
    check(state["economic_classification"][
        "wallet_opening_Dragon_before_frozen_window"]==
        "NONZERO_966415_OLD_COST_UNRESOLVED" and
        state["P5"]=="BLOCKED" and
        state["PUBLIC_EXECUTABLE_U"]=="UNRESOLVED",
        "COST_BASIS_STILL_MISSING")
    return {
        "schema":"BSC_P4B_2026_5E60_EXACT_33_IN_17_OUT_HISTORIC_TOKEN_INVENTORY_REPLAY",
        "source_git_blob_sha":{k:v[1] for k,v in FILES.items()},
        "window_from":85900000,"window_to":85959961,
        "previous_block_wallet_Dragon_raw":str(opening),
        "historical_inbound_transfer_count":33,
        "historical_inbound_Dragon_raw":str(ins),
        "historical_outbound_transfer_count":17,
        "historical_outbound_Dragon_raw":str(outs),
        "wallet_Dragon_at_pre_1000USDT_buy_block":str(closing),
        "exact_balance_equation_holds":True,
        "previous_966415_Dragon_cost_basis":"UNRESOLVED_PRE_WINDOW",
        "net_profit":"UNRESOLVED_ORIGINAL_CASH_COST_NOT_KNOWN",
        "public_first_U":"UNRESOLVED",
        "P4_B":"PARTIAL","P5":"BLOCKED","PRODUCTION":"NO_GO"
    }
if __name__=="__main__":
    print(json.dumps(audit(load()),indent=2,sort_keys=True))
