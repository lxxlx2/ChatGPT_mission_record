#!/usr/bin/env python3
"""Recover two real D503 buy gasUsed via adjacent same-block receipt cumulative counters.

This is the selected original tx gas, NOT generic 1/5/15min DDAC-copy trade ROI.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FILES={
 "freeze":("bsc-meme-address-model-v1-p4b-dragon-three-real-buys-adjacent-cumulative-gas-precommit-2026-10-18.json","e640235b63f04996870b1fe9a43d3e48a74be966"),
 "readback":("bsc-meme-address-model-v1-p4b-dragon-three-adjacent-actual-gas-readback-2026-10-18.json","53558e68f2052681a8a0e05b86b5fc00f8fa9cc1"),
 "prior_partial_buy_receipts":("bsc-meme-address-model-v1-p4b-dragon-d503-two-buy-gas-trace-free-tier-result-2026-10-18.json","833ffbc7b6adf73389cf18417cde45305764d6c5"),
 "real_five_signed_tx":("bsc-meme-address-model-v1-p4b-dragon-five-external-signer-original-tx-alchemy-readback-2026-10-18.json","9e8653a684aa88ecdb808b64d647ca676a2327d2"),
 "original_native":("bsc-meme-address-model-v1-p4b-dragon-two-buyers-historic-native-balances-2026-10-16.json","9ac3c2bef80e5ada78c87f0949d19f80eb55ecab"),
 "original_signed":("bsc-meme-address-model-v1-p4b-dragon-postowner-original-seven-txs-2026-10-16.json","b06b2ef565ebd74bc7f83ad4a2ea731eeb5cb2b9"),
 "DDAC_early_exit":("bsc-meme-address-model-v1-p4c-dragon-ddac-closed-native-loss-2026-10-15.json","4e76eea4d7ab001360af82f15de5eefc8509c501")
}
def check(ok,code):
 if not ok: raise ValueError("P4B_ADJACENT_BUY_GAS_"+code)
def load(root=ROOT):
 d={}
 for k,(name,sha) in FILES.items():
  content=(root/name).read_bytes()
  actual=hashlib.sha1(b"blob "+str(len(content)).encode()+b"\0"+content).hexdigest()
  check(actual==sha,"PINNED_BLOB_DRIFT_"+k)
  d[k]=json.loads(content)
 return d
def build(d):
 f,rb,prev,txs,native,signed,ddac=(d[k] for k in (
   "freeze","readback","prior_partial_buy_receipts","real_five_signed_tx",
   "original_native","original_signed","DDAC_early_exit"))
 check(rb["precommit"]=={
    "file":FILES["freeze"][0],"git_blob_sha":FILES["freeze"][1],
    "committed_before_calls":True} and
   f["max_live_reads"]==7 and f["zero_retries"] is True and
   len(f["queries_frozen"])==len(rb["rows"])==3 and
   rb["call_budget"]=={
     "maximum_calls":7,"predecessor_tx_calls_executed":3,
     "preceding_tx_receipt_calls_executed":2,
     "E11B_original_buy_receipt_calls_executed":1,
     "total_calls_executed":6,"retries":0} and
   rb["capture_grade"]==
     "ADJACENT_RECEIPT_TOOL_PARSED_AND_TARGET_OLD_TOOL_VISIBLE_PREFIX_NOT_COMPLETE_TARGET_PROVIDER_WIRE",
   "PRECOMMIT_AND_NO_EXTRA_QUERIES")
 check(f["source_pins"]=={
   "actual_5_signed_tx":FILES["real_five_signed_tx"][1],
   "actual_5_signed_precommit":"47225db058589e131132ac6b308280b81c0cb4ff",
   "original_7_signed_events":FILES["original_signed"][1],
   "old_D503_2_truncated_receipt_cumulative":FILES["prior_partial_buy_receipts"][1],
   "actual_4_wallet_BNB_blocks":FILES["original_native"][1]} and
   f["gates"]=={
     "P4_B":"PARTIAL","PUBLIC_EXECUTABLE_U":"UNRESOLVED","P5":"BLOCKED",
     "PRODUCTION":"NO_GO","permissions":"NO_MERGE NO_DEPLOY NO_GMAIL NO_TRADE"} and
   rb["gates"]=={
     "P4_B":"PARTIAL","PUBLIC_EXECUTABLE_U":"UNRESOLVED","P5":"BLOCKED",
     "PRODUCTION":"NO_GO","NO_MERGE":True,"NO_DEPLOY":True,
     "NO_GMAIL":True,"NO_TRADE":True},
   "FIXED_SOURCES_OR_PRODUCTION_GATE")
 orig={q["label"]:q for q in signed["cases"]}
 five={q["id"]:q["returned"] for q in txs["results"]}
 nativeby={int(x["block"]):x for x in native["movements"]}
 partial={q["label"]:q for q in prev["results"]}
 check(ddac["round"]["exit_block"]==83635800 and
       ddac["round"]["residual_token_raw"]=="0" and
       len(five)==5 and
       [q["case"] for q in rb["rows"]]==[q["case"] for q in f["queries_frozen"]],
       "REAL_DDAC_EXIT_AND_SAME_SAMPLES")
 output=[]
 for row,scope in zip(rb["rows"],f["queries_frozen"]):
  name=row["case"]
  actual=five[name]
  check(name==scope["case"] and
        scope["block"]==int(actual["blockNumber"],16)==row["block"] and
        scope["buy_tx"]==row["target_tx"]==actual["hash"]==orig[name]["tx"] and
        scope["target_transaction_index"]==int(actual["transactionIndex"],16)==
          row["target_transaction_index"] and
        scope["previous_transaction_index"]==scope["target_transaction_index"]-1==
          row["previous_transaction_index"] and
        scope["target_gasPrice_wei"]==row["target_original_tx_gas_price_wei"]==
          str(int(actual["gasPrice"],16)) and
        actual["type"]=="0x0" and orig[name]["receipt"]["status"]=="0x1",
        "CHAIN_TX_ADJACENCY_OR_TARGET_IDENTITY")
  check(row["target_receipt_full_JSON_archived"] is False and
        rb["network"]=="bnb-mainnet",
        "TARGET_FULL_RECEIPT_NOT_ARCHIVED")
  if name.startswith("D503_"):
   old=partial[name]["ethGetTransactionReceipt"]
   check(old["complete_parseable_JSON"] is False and
         old["rpc_text_chars"]==8098 and
         old["visible_cumulativeGasUsed"]==scope["known_target_cumulative_hex"]==
           row["target_cumulativeGasUsed_hex"] and
         row["target_cumulative_source_blob"]==FILES["prior_partial_buy_receipts"][1],
         "ORIGINAL_PINNED_TOOL_VISIBLE_TARGET_CUMULATIVE")
   check(row["previous_tx_full_json_parseable"] is True and
         row["previous_receipt_complete_JSON"] is True and
         row["previous_receipt_same_block_hex"]==actual["blockNumber"] and
         int(row["previous_receipt_index_hex"],16)==row["previous_transaction_index"] and
         row["previous_receipt_status"]=="0x1" and
         int(row["previous_receipt_own_gasUsed_hex"],16)>0 and
         int(row["previous_cumulativeGasUsed_hex"],16)>=
           int(row["previous_receipt_own_gasUsed_hex"],16),
         "REAL_IMMEDIATELY_PRECEDING_TX_RECEIPT")
   consumed=int(row["target_cumulativeGasUsed_hex"],16)-int(
       row["previous_cumulativeGasUsed_hex"],16)
   check(0<consumed<=int(actual["gas"],16) and
         str(consumed)==row["derived_target_gasUsed_units"],
         "ONCHAIN_CUMULATIVE_DELTA_IS_TRANSACTION_GASUSED")
   fee=consumed*int(actual["gasPrice"],16)
   check(str(fee)==row["derived_legacy_tx_fee_wei"],
         "SIGNED_GAS_PRICE_MULTIPLY_DERIVED_GAS")
   actual_out=-int(nativeby[row["block"]]["block_native_delta_wei"])
   original_value=int(actual["value"],16)
   residual=actual_out-original_value-fee
   check(actual_out>0 and
         str(actual_out)==row["observed_actual_buy_block_native_debit_wei"] and
         str(original_value)==row["original_signed_top_level_native_value_wei"] and
         str(residual)==row["native_block_debit_minus_signed_value_plus_calculated_fee_wei"],
         "ALREADY_GAS_INCLUSIVE_NATIVE_WALLET_BLOCK_DELTA")
   output.append({"case":name,"original_tx_hash":actual["hash"],"block":row["block"],
       "original_signed_native_input_BNB_wei":str(original_value),
       "gasUsed_actual_units_from_adjacent_cumulative":str(consumed),
       "signed_legacy_gasPrice_wei":str(int(actual["gasPrice"],16)),
       "derived_actual_buy_gas_fee_BNB_wei":str(fee),
       "wallet_BNB_balance_debit_whole_buy_block_wei":str(actual_out),
       "unattributed_residual_wei":str(residual),
       "gas_fee_already_in_owner_block_native_debit":True,
       "full_unclipped_target_receipt_archived":False,
       "can_claim_followed_original_DDAC":False})
  else:
   check(name=="E11B_BUY_1" and
         row["previous_transaction_index"]==66 and
         row["previous_tx_by_block_response_chars"]==8098 and
         row["previous_tx_complete_JSON_parseable"] is False and
         row["previous_tx_hash_complete_independently_captured"] is False and
         row["previous_receipt_queried"] is False and
         row["target_tool_receipt_chars"]==8098 and
         row["target_receipt_visible_index_hex"]=="0x43" and
         row["target_cumulativeGasUsed_hex"]=="0x8f7e66" and
         row["derived_target_gasUsed_units"]=="UNRESOLVED" and
         row["derived_legacy_tx_fee_wei"]=="UNRESOLVED" and
         row["owner_exit"]=="UNRESOLVED",
         "E11B_UNKNOWN_GAS_AND_EXIT_MUST_REMAIN_UNKNOWN")
 check(len(output)==2 and
       [q["gasUsed_actual_units_from_adjacent_cumulative"] for q in output]==
         ["290567","290567"] and
       [q["derived_actual_buy_gas_fee_BNB_wei"] for q in output]==
         ["871701000000000","2033969000000000"] and
       [q["unattributed_residual_wei"] for q in output]==["-4","-18"],
       "BOTH_TRUE_D503_BUY_GAS_NOT_GUESSED_FROM_NATIVE_RESIDUAL")
 return {"schema":"BSC_P4B_2026_DRAGON_ACTUAL_D503_BUY_GAS_VIA_ADJACENT_RECEIPTS",
  "source_sha":{k:v[1] for k,v in FILES.items()},
  "gas_reconstruction_grade":
    "DERIVED_FROM_ONE_OLD_TOOL_VISIBLE_TARGET_CUMULATIVE_PER_BUY_AND_ONE_NEW_FULL_PREDECESSOR_RECEIPT",
  "true_signed_D503_buy_gas":output,"E11B_unknown_gas_and_exit":True,
  "actual_complete_target_receipt_archived":False,
  "public_observer_follower_signal":False,
  "fixed_delay_realizable_1_5_15min_profit":"UNRESOLVED",
  "P4_B":"PARTIAL","PUBLIC_EXECUTABLE_U":"UNRESOLVED",
  "P5":"BLOCKED","PRODUCTION":"NO_GO"}
if __name__=="__main__":
 print(json.dumps(build(load()),ensure_ascii=False,indent=2,sort_keys=True))
