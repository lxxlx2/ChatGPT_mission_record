#!/usr/bin/env python3
"""Replay selected 239E original buy/sell block timestamps, not follower clock or P5."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES={
 "freeze":("bsc-meme-address-model-v1-p4b-239e-original-4tx-real-historical-time-prefreeze-2026-10-18.json","e89d485eb0d6189b2f050da1ef6524c0d2b57b02"),
 "readback":("bsc-meme-address-model-v1-p4b-239e-four-original-tx-real-blocktimestamp-2026-10-18.json","96f5780e6d699b6f0d8218b5029b3d14c8fa1ea0"),
 "original":("bsc-meme-address-model-v1-p4c-239e-dragon-two-owner-native-settlements-2026-10-15.json","46e90123b98d5324e05388b17b8a3bbb77cb5361"),
 "math":("bsc-meme-address-model-v1-p4b-239e-dragon-two-exit-v2-two-sided-math-readback-2026-10-18.json","cc09edff6a464b21ab1609980becc1afa4548ad1")
}
def check(x,s):
 if not x: raise ValueError("P4B_239E_REAL_CLOCK_"+s)
def load(folder=ROOT):
 out={}
 for k,(name,pin) in SOURCES.items():
  raw=(folder/name).read_bytes()
  check(hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()==pin,"SOURCE_SHA_"+k)
  out[k]=json.loads(raw)
 return out
def build(d):
 freeze,rb,real,math=(d[k] for k in ("freeze","readback","original","math"))
 check(rb["source_prefreeze"]=={"file":SOURCES["freeze"][0],
           "git_blob_sha":SOURCES["freeze"][1],
           "committed_before_this_RPC_batch":True} and
       freeze["method"]=="eth_getTransactionByHash" and
       freeze["network"]=="bnb-mainnet" and
       freeze["max_calls"]==rb["requested"]==rb["executed"]==rb["valid_full_JSON"]==4 and
       rb["retries"]==0 and len(rb["selected_tx_records"])==len(freeze["calls"])==4 and
       len(rb["derived_cases"])==2 and
       rb["tool_return_grade"]==
         "TOOL_PARSED_COMPLETE_TRANSACTION_JSON_FIELDS_NOT_PROVIDER_TRANSPORT_BYTEWISE_CAPTURED",
       "SOURCE_SCOPE_AND_TOOL_GRADE")
 check(freeze["source_pins"]=={
       "real_signed_rounds":SOURCES["original"][1],
       "historical_new_math_readback":SOURCES["math"][1],
       "original_frozen_239e_endblock_balance":"7e930c57fb5ba3a3dfd795575c059ade9f8a387d"} and
       freeze["cutoffs_seconds_after_actual_owner_first_signed_buy"]==[60,300,900] and
       freeze["no_retries"] is True and freeze["no_reselection"] is True and
       freeze["gates"]=={
        "original_owner_balance_at_arbitrary_cutoff":"NOT_CHAIN_BALANCE_REQUERIED",
        "public_signal_arrival":"UNRESOLVED",
        "follower_real_buy_and_exit":"UNRESOLVED",
        "follower_profit_at_1_5_15":"UNRESOLVED",
        "PUBLIC_EXECUTABLE_U":"UNRESOLVED",
        "P4_B":"PARTIAL","P5":"BLOCKED","PRODUCTION":"NO_GO"} and
       rb["gates"]=={
        "P4_B":"PARTIAL","PUBLIC_EXECUTABLE_U":"UNRESOLVED",
        "P5":"BLOCKED","PRODUCTION":"NO_GO",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_GMAIL":True,"NO_TRADE":True},
       "FREEZE_FIELDS_AND_NO_PROFIT_PROMOTION")
 check(len(real["rounds"])==2 and len(math["cases"])==2 and
       [r["case"] for r in math["cases"]]==
       ["239E_R1_OWNER_REAL_NATIVE_LOSS","239E_R2_OWNER_REAL_NATIVE_PROFIT"],
       "ORIGINAL_SIGNED_SOURCE_SCOPE")
 rows=[]
 for i,(case,orig) in enumerate(zip(("R1","R2"),real["rounds"])):
  part=rb["selected_tx_records"][i*2:i*2+2]
  planned=freeze["calls"][i*2:i*2+2]
  check([x["case"] for x in part]==[case,case] and
        [x["role"] for x in part]==["ORIGINAL_FIRST_BUY","ORIGINAL_FINAL_SELL"] and
        [x["case"] for x in planned]==[case,case] and
        [x["role"] for x in planned]==[x["role"] for x in part],
        "BUY_SELL_ROLE_AND_ORDER")
  seconds=[]
  for record,spec,tx in zip(part,planned,(orig["txs"][0],orig["txs"][-1])):
   check(record["transactionHash"]==spec["hash"]==tx["hash"] and
         int(record["raw_blockNumber_hex"],16)==spec["expected_block"]==tx["block"] and
         record["raw_from"]==orig["owner"]==
           "0x239e74bfbd02d71cdc70fecc2d505dc13acfb337" and
         record["raw_to"]=="0xca980f000771f70b15647069e9e541ef73f71f2f" and
         record["raw_chainId_hex"]=="0x38" and
         int(record["raw_signed_transaction_value_hex"],16)==
           (int(tx["original_wbnb_transfer_wei"]) if tx["action"]=="BUY" else 0) and
         record["eth_getTransactionByHash_valid_full_JSON"] is True and
         record["tool_output_truncated"] is False and
         1200<=record["provider_tool_text_chars"]<=2000,
         "SIGNED_TX_BLOCK_AUTHOR_AND_VALUE")
   timestamp=int(record["raw_blockTimestamp_hex"],16)
   check(record["utc_derived_from_timestamp"]==
         datetime.fromtimestamp(timestamp,timezone.utc).isoformat().replace("+00:00","Z") and
         timestamp>0 and int(record["raw_transactionIndex_hex"],16)>=0,
         "SOURCE_TRANSACTION_BLOCK_TIME")
   seconds.append(timestamp)
  entry,exit=seconds
  check(exit>entry and
        orig["txs"][-1]["action"]=="SELL" and
        orig["token_inventory_residual_raw"]=="0" and
        all(q["complete_receipt"] is True for q in orig["txs"]),
        "CLOSED_REAL_OWNER_EPISODE")
  check((int(orig["original_native_wallet_net_wei"])>0)==(i==1) and
        (int(math["cases"][i]["two_independent_static_quote_gross_delta_wei"])>0)==(i==1),
        "REAL_PROFIT_SIGN_VS_UNEXECUTED_MATH_SIGN")
  derived=rb["derived_cases"][i]
  check(derived["case"]==case and
        derived["first_signed_buy_unix_seconds"]==entry and
        derived["last_signed_sell_unix_seconds"]==exit and
        derived["signed_first_buy_to_final_sell_seconds"]==exit-entry and
        derived["first_buy_before_final_sell"] is True,
        "REAL_CLOCK_RECONCILIATION")
  cutoffs=[]
  for v,seconds_into in zip(derived["cutoffs_from_original_first_buy_seconds"],[60,300,900]):
   left=entry+seconds_into>=exit
   check(v=={
      "seconds":seconds_into,
      "owner_final_sell_already_mined_by_this_timestamp":left,
      "owner_final_sell_not_yet_mined_by_this_timestamp":not left,
      "no_inference_about_interim_unsampled_onchain_token_balance":True},
      "NO_INTERIM_CHAIN_BALANCE_OR_OBSERVER_CLAIM")
   cutoffs.append({"seconds_after_first_original_buy_block":seconds_into,
       "original_final_signed_sell_already_mined":left,
       "historic_owner_full_balance_at_exact_cutoff":"UNRESOLVED",
       "actual_public_follower_signal_arrived":"UNRESOLVED",
       "real_follower_eligible_fill_and_net":"UNRESOLVED"})
  rows.append({"case":case,"original_owner_real_net_BNB_wei":orig["original_native_wallet_net_wei"],
               "first_original_buy_unix_seconds":entry,
               "last_original_sell_unix_seconds":exit,
               "duration_first_buy_to_final_sell_seconds":exit-entry,
               "cutoffs":cutoffs,
               "actual_copy_strategy_1_5_15_minute_return":"UNRESOLVED"})
 check([x["duration_first_buy_to_final_sell_seconds"] for x in rows]==[1550,634] and
       [[x["original_final_signed_sell_already_mined"] for x in y["cutoffs"]] for y in rows]==
       [[False,False,False],[False,False,True]],
       "TWO_ACTUAL_MATURITY_TIMES")
 return {
   "schema":"BSC_P4B_2026_239E_ORIGINAL_REAL_BLOCK_TIME_SIGNAL_LIFESPAN_NO_FOLLOWER_ROI",
   "source_pins":{k:v[1] for k,v in SOURCES.items()},
   "sampled_original_rounds":rows,
   "scope_grade":"ORIGINAL_SIGNED_TX_CHAIN_BLOCK_TIMESTAMP_NOT_PUBLIC_OBSERVER_WALL_CLOCK",
   "full_historical_balances_at_exact_minute_cutoff":"UNRESOLVED",
   "first_public_tradable_U":"UNRESOLVED",
   "fixed_delay_net_follower_return":"UNRESOLVED",
   "P4_B":"PARTIAL","P5":"BLOCKED","PRODUCTION":"NO_GO"
 }
if __name__=="__main__":
 print(json.dumps(build(load()),ensure_ascii=False,indent=2,sort_keys=True))
