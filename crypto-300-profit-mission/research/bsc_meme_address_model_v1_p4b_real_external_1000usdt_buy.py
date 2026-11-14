#!/usr/bin/env python3
"""One ACTUAL external owner-funded USDT->WBNB->Dragon buy, not causal follow or PnL."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCES={
 "owner":("bsc-meme-address-model-v1-p4b-239e-owner-4-historical-balances-v2-12block-swap-denied-2026-10-18.json","e31458ae7778847c3cd36ba4a7bf67d680dc4358"),
 "swap":("bsc-meme-address-model-v1-p4b-239e-single-block-r1-clipped-r2-four-real-v2-swap-events-2026-10-18.json","0994ffa6aab22eb9d9b859031af225a5057088c2"),
 "signed":("bsc-meme-address-model-v1-p4b-239e-r2-one-real-external-buy-signer-other-sell-truncated-2026-10-18.json","02ff39c280646ed4957abc0758919c8b1a595042"),
 "dragon":("bsc-meme-address-model-v1-p4b-239e-r2-external-wallet-real-incremental-buy-erc20-transfer-readback-2026-10-18.json","64900a1e544cb7ecba5cb49ef974befd1d9312bc"),
 "wbnb":("bsc-meme-address-model-v1-p4b-239e-r2-external-buyer-wbnb-not-direct-debit-readback-2026-10-18.json","1e72d2aa622b7838d5067ce57a21afc00e9d657f"),
 "route":("bsc-meme-address-model-v1-p4b-239e-r2-real-external-1000usdt-three-token-route-signed-calldata-2026-10-18.json","aadba0f6cb69752114cf5ea0b9819418f9a3aa74"),
 "usdt":("bsc-meme-address-model-v1-p4b-239e-r2-external-5e60-real-usdt-debit-gas-and-dragon-readback-2026-10-18.json","4288f9819f2815cb4d899c93116b23e19e6fe0ba"),
 "orig239e":("bsc-meme-address-model-v1-p4c-239e-dragon-two-owner-native-settlements-2026-10-15.json","46e90123b98d5324e05388b17b8a3bbb77cb5361")
}
def require(cond,reason):
 if not cond: raise ValueError("P4B_EXTERNAL_1000_USDT_"+reason)
def load(base=ROOT):
 out={}
 for key,(name,sha) in SOURCES.items():
  content=(base/name).read_bytes()
  got=hashlib.sha1(b"blob "+str(len(content)).encode()+b"\x00"+content).hexdigest()
  require(got==sha,"SOURCE_PIN_"+key)
  out[key]=json.loads(content)
 return out
def as_addr(word):
 require(len(word)==64 and word[:24]=="0"*24,"ABI_ADDRESS")
 return "0x"+word[-40:].lower()
def decode_swap_exact_tokens_for_tokens(calldata):
 require(calldata.startswith("0x38ed1739") and len(calldata)>=10+64*9,"ROUTER_INPUT_SELECTOR_OR_LENGTH")
 h=calldata[10:]
 try:
  amount=int(h[0:64],16)
  min_received=int(h[64:128],16)
  offset=int(h[128:192],16)
  recipient=as_addr(h[192:256])
  deadline=int(h[256:320],16)
  require(offset==160,"ABI_DYNAMIC_PATH_OFFSET")
  base=offset*2
  n=int(h[base:base+64],16)
  require(n==3 and len(h)==base+64+64*n,"THREE_EXACT_ROUTE_TOKENS")
  path=[as_addr(h[base+64+i*64:base+64+(i+1)*64]) for i in range(n)]
 except (ValueError,IndexError) as error:
  if isinstance(error,ValueError) and str(error).startswith("P4B_EXTERNAL_1000_USDT_"):
   raise
  raise ValueError("P4B_EXTERNAL_1000_USDT_INVALID_ROUTER_ABI") from error
 return {"amount":amount,"min_out":min_received,"path":path,"recipient":recipient,"deadline":deadline}
def build(d):
 owner,swap,signed,token,wbnb,route,usdt,original=(d[x] for x in
   ("owner","swap","signed","dragon","wbnb","route","usdt","orig239e"))
 pair="0x22af7297243c4eef12e2d5a4f888b92e56bf127c"
 buyer="0x5e600e259e3cff0757e3736223685958665866c6"
 srcowner="0x239e74bfbd02d71cdc70fecc2d505dc13acfb337"
 txhash="0x2b93cfb6ae16ab4943f5f209fff1820f98368fd357cbdcb4f624708440bf8f47"
 usdtCA="0x55d398326f99059ff775485246999027b3197955"
 wbnbCA="0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
 dragonCA="0xeccbb861c0dda7efd964010085488b69317e4444"
 checkblock=85959962
 orig_round=original["rounds"][1]
 require(orig_round["owner"]==srcowner and orig_round["exact_CA"]==dragonCA and
         orig_round["txs"][0]["block"]==85959961 and orig_round["txs"][-1]["block"]==85961371 and
         int(orig_round["original_native_wallet_net_wei"])>0,
         "ORIGINAL_SOURCE_OWNER_PRECEDES_EXTERNAL")
 hold={(r["case"],r["window"]):r for r in owner["holding_readbacks"]}
 require(int(hold[("R2","POST_BUY_EARLY")]["balance_raw"])>0 and
         int(hold[("R2","POST_BUY_LATER")]["balance_raw"])>0 and
         owner["pair_tokens"][0]["decoded_token0"]==wbnbCA and
         owner["pair_tokens"][1]["decoded_token1"]==dragonCA,
         "ORIGINAL_SOURCE_WALLET_STILL_HELD_AT_FIXED_SNAPSHOTS")
 target=swap["results"][1]
 require(swap["results"][0]["complete_json"] is False and
         target["case"]=="R2" and target["complete_json"] is True and
         target["swap_event_count"]==4 and len(target["all_log_objects"])==4 and
         target["distinct_transaction_hashes"]==2,"EXACT_ONE_COMPLETE_PAIR_LOG_BLOCK")
 buylogs=[q for q in target["all_log_objects"] if
           q["transactionHash"]==txhash]
 require(len(buylogs)==1 and
         buylogs[0]["direction"]=="WBNB_IN_DRAGON_OUT" and
         buylogs[0]["transactionIndex"]=="0x2" and
         buylogs[0]["blockNumber"]==hex(checkblock) and
         buylogs[0]["address"]==pair,"SIGNED_BUY_MATCHED_TRUE_PAIR_SWAP")
 amounts=buylogs[0]["decoded_v2_swap_4_uint256"]
 require(int(amounts["amount0In"])>0 and int(amounts["amount1Out"])>0 and
         amounts["amount1In"]==amounts["amount0Out"]=="0",
         "PAIR_AMOUNT_OR_DIRECTION")
 signedbuy=signed["first_buy"]
 require(signedbuy["hash"]==route["exact_hash"]==txhash and
         signedbuy["from"]==route["from"]==buyer and buyer!=srcowner and
         signedbuy["to"]==route["to"]==
           "0x10ed43c718714eb63d5aa57b78b54704e256024e" and
         signedbuy["blockNumber"]==route["blockNumber"]==hex(checkblock) and
         signedbuy["transactionIndex"]==route["transactionIndex"]=="0x2" and
         signedbuy["value"]==route["value"]=="0x0" and
         signedbuy["input_selector"]==route["ABI_selector"]=="0x38ed1739" and
         signed["first_sell"]["tool_return_full_JSON_parseable"] is False,
         "REAL_EXTERNAL_SIGNED_ROUTER_BUY_AND_UNRESOLVED_SELL")
 parsed=decode_swap_exact_tokens_for_tokens(route["input"])
 require(parsed["amount"]==1000000000000000000000 and
         parsed["min_out"]==int(route["decoded"]["minAmountOut_raw"]) and
         parsed["path"]==route["decoded"]["path"]==
           [usdtCA,wbnbCA,dragonCA] and
         parsed["recipient"]==buyer and
         parsed["deadline"]==route["decoded"]["deadline_unix_seconds"] and
         route["decoded"]["amountIn_raw"]==str(parsed["amount"]),
         "SIGNED_USDT_WBNB_DRAGON_ORIGINAL_ROUTE")
 original_received=int(amounts["amount1Out"])
 require(amounts["amount0In"]==route["actual_LP_WBNB_in_wei"]==
         token["one_pair_swap_WBNB_in_wei"]==
         wbnb["pair_matched_input_WBNB_wei"] and
         str(original_received)==route["actual_final_ERC20_received_raw"]==
         token["pair_swap_token_gross_out_raw"],
         "INTERMEDIATE_POOL_QUOTE_NOT_WALLET_DEBIT")
 tokenb=token["balanceOf_rows"]
 require([x["block"] for x in tokenb]==[85959961,85959962,85960573,85961371],
         "FOUR_FIXED_REAL_TOKEN_BALANCES")
 amountsToken=[int(x["parsed_owner_token_balance_raw"]) for x in tokenb]
 require(amountsToken[0]>0 and amountsToken[1]-amountsToken[0]==
         original_received and amountsToken[1]==amountsToken[2]==amountsToken[3] and
         token["raw_token_balance_delta_in_buy_block"]==str(original_received),
         "REAL_ALREADY_OWNED_DRAGON_PLUS_RECEIVED_MORE_AND_NO_CONFIRMED_SELL")
 tr=token["transfer_to_buyer_logs"]
 require(tr["log_count"]==1 and tr["response_full_parseable"] is True,"EXTERNAL_TOKEN_TRANSFER_LOG_FULL")
 t=tr["logs"][0]
 require(t["transactionHash"]==txhash and t["transactionIndex"]=="0x2" and
         t["blockNumber"]==hex(checkblock) and
         t["topics"][1]=="0x"+"0"*24+pair[2:] and
         t["topics"][2]=="0x"+"0"*24+buyer[2:] and
         int(t["data"],16)==original_received,
         "EXTERNAL_FULL_DELIVERY_TRANSFER_NOT_ONLY_PAIR_QUOTE")
 wb=wbnb["balance_snapshots"]
 require([x["block"] for x in wb]==[85959961,85959962] and
         wb[0]["raw"]==wb[1]["raw"] and
         wbnb["transfer_from_wallet_event"]["total"]==0 and
         wbnb["transfer_from_wallet_event"]["complete_json"] is True,
         "PAIR_WBNB_NOT_SIGNER_DIRECT_WBNB_DEBIT")
 snap=usdt["USDT_wallet_balances"]
 require([x["block"] for x in snap]==[85959961,85959962] and
         int(snap[0]["decimal_raw"])-int(snap[1]["decimal_raw"])==
           parsed["amount"] and
         usdt["USDT_wallet_actual_delta_raw"]==str(-parsed["amount"]),
         "REAL_SIGNER_1000_USDT_BALANCE_DEBIT")
 utr=usdt["USDT_transfer_from_signer"]
 require(utr["log_count_full_JSON"]==1 and
         utr["full_JSON_parseable"] is True and
         utr["transactionHash"]==txhash and
         utr["transactionIndex"]=="0x2" and
         utr["topics"][1]=="0x"+"0"*24+buyer[2:] and
         int(utr["data"],16)==parsed["amount"],
         "SIGNED_REAL_USDT_FUNDING_TRANSFER")
 receipt=usdt["receipt"]
 gas_used=int(receipt["gasUsed"],16)
 price=int(receipt["effectiveGasPrice"],16)
 require(receipt["full_JSON_parseable_at_read_time"] is True and
         receipt["complete_original_receipt_bytes_saved"] is False and
         receipt["transactionHash"]==txhash and
         receipt["status"]=="0x1" and receipt["transactionIndex"]=="0x2" and
         gas_used==156632 and
         price==int(signedbuy["gasPrice"],16) and
         gas_used*price==int(receipt["computed_buy_fee_wei"])==
          78316000000000 and
         receipt["logs_count"]==8,
         "REAL_SUCCESS_RECEIPT_GAS_USED_AND_NO_FAKE_RAW")
 require(usdt["verification"]=={
          "amountIn_equals_actual_USDT_wallet_debit":True,
          "full_USDT_transfer_in_same_real_signed_hash":True,
          "token_dragon_real_transfer_equals_signed_wallet_token_increment":True,
          "receipt_success":True,
          "original_wallet_239e_still_held_at_selected_end_blocks":True,
          "external_signer_was_existing_token_holder_before":True,
          "external_realized_sell_or_exit":"UNRESOLVED",
          "independent_public_signal_received":"UNRESOLVED",
          "actual_follower_net_return":"UNRESOLVED"} and
         usdt["gates"]["PUBLIC_EXECUTABLE_U"]=="UNRESOLVED" and
         usdt["gates"]["P5"]=="BLOCKED",
         "CANNOT_REBRAND_EXISTING_HOLDER_AS_PROFITABLE_CAUSAL_FOLLOWER")
 return {
  "schema":"BSC_P4B_REAL_1000USDT_EXTERNAL_SIGNED_ADD_WHILE_SOURCE_OWNER_HELD",
  "source_pins":{key:pair[1] for key,pair in SOURCES.items()},
  "source_evidence_grade":"FULL_SIGNED_ROUTER_INPUT_AND_TOKEN_USDT_TRANSFERS_AND_SELECTED_SUCCESS_RECEIPT_FIELDS",
  "external_wallet":buyer,"source_signal_wallet":srcowner,
  "real_buy_tx":txhash,"historical_signed_buy_block":checkblock,
  "actual_wallet_USDT_spent_raw":str(parsed["amount"]),
  "actual_pair_intermediate_WBNB_in_wei":str(amounts["amount0In"]),
  "actual_dragon_token_received_raw":str(original_received),
  "wallet_dragon_preexisting_before_real_buy_raw":str(amountsToken[0]),
  "wallet_dragon_end_owner_source_exit_raw":str(amountsToken[3]),
  "classification":"ACTUAL_SIGNED_BUY_ALREADY_HAD_TOKENS_EXIT_NOT_PROVEN",
  "receipt_gasUsed_units":str(gas_used),
  "receipt_actual_fee_BNB_wei":str(gas_used*price),
  "actual_complete_receipt_bytes_committed":False,
  "actual_realized_external_wallet_sell_or_PnL":"UNRESOLVED",
  "causal_copy_from_original_239e":"UNRESOLVED",
  "public_first_U":"UNRESOLVED",
  "fixed_delay_follow_profit_1_5_15minute":"UNRESOLVED",
  "P4_B":"PARTIAL","P5":"BLOCKED","PRODUCTION":"NO_GO"
 }
if __name__=="__main__":
 print(json.dumps(build(load()),indent=2,sort_keys=True))
