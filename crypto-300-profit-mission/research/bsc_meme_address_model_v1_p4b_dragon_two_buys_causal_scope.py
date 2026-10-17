#!/usr/bin/env python3
"""2026 Dragon historical actual post-owner signed roundtrip timing, not causal follower ROI."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCES={
 "freeze":("bsc-meme-address-model-v1-p4b-dragon-d503-two-buy-gas-trace-precommit-2026-10-18.json","d09f5502e449d768182a5e3d9710c2c9561c6509"),
 "probe":("bsc-meme-address-model-v1-p4b-dragon-d503-two-buy-gas-trace-free-tier-result-2026-10-18.json","833ffbc7b6adf73389cf18417cde45305764d6c5"),
 "signed":("bsc-meme-address-model-v1-p4b-dragon-postowner-original-seven-txs-2026-10-16.json","b06b2ef565ebd74bc7f83ad4a2ea731eeb5cb2b9"),
 "headers":("bsc-meme-address-model-v1-p4b-dragon-postowner-four-execution-block-headers-2026-10-16.json","e1f03de64a7716625ad5968df8fd389b48e8b261"),
 "native":("bsc-meme-address-model-v1-p4b-dragon-two-buyers-historic-native-balances-2026-10-16.json","9ac3c2bef80e5ada78c87f0949d19f80eb55ecab"),
 "inventory":("bsc-meme-address-model-v1-p4b-dragon-two-buyers-historic-token-inventory-2026-10-16.json","06bba24e15530cf9f0f7fde24ab876fcc764d173"),
 "original_freeze":("bsc-meme-address-model-v1-p4b-dragon-postowner-signed-roundtrip-precommit-2026-10-16.json","a0937b2aca1c83cd99bf7e0678538a6067cc2d3f")
}

def require(b,s):
 if not b: raise ValueError("P4B_DRAGON_CAUSAL_SCOPE_"+s)

def load(root=ROOT):
 documents={}
 for k,(filename,pin) in SOURCES.items():
  raw=(root/filename).read_bytes()
  h=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
  require(h==pin,"SOURCE_SHA_DRIFT_"+k)
  documents[k]=json.loads(raw)
 return documents

def build(d):
 freeze,probe,signed,headers,native,inv,pre=(d[x] for x in
              ("freeze","probe","signed","headers","native","inventory","original_freeze"))
 case=freeze["probe_set"]
 require(freeze["max_live_readonly_calls"]==4 and probe["actual_calls"]==4 and
         probe["freeze_git_blob"]==SOURCES["freeze"][1] and
         probe["capture_grade"]=="TOOL_SUMMARIZED_PROVIDER_CLIPPED_RECEIPTS_AND_EXPLICIT_FREE_TIER_REJECTION_NOT_COMPLETE_RAW",
         "BOUNDED_ACTUAL_RPC_AND_SOURCE_GRADE")
 require(len(case)==len(probe["results"])==2 and
         [x["label"] for x in case]==["D503_BUY_1","D503_BUY_2"] and
         signed["token_exact_CA"]==freeze["exact_CA"]==inv["token_exact_CA"]==
         pre["token_exact_CA"]=="0xeccbb861c0dda7efd964010085488b69317e4444",
         "FROZEN_EXACT_CA_AND_BUYERS")
 require(freeze["owner_original_early_signal"]["block"] ==
         signed["original_DDAC_source_block"] ==
         headers["original_owner_block"] == pre["owner"]["block"] == 83635776 and
         freeze["owner_original_early_signal"]["tx"]==pre["owner"]["buy_hash"],
         "ORIGINAL_SIGNAL_IDENTITY")
 require(probe["gates"]=={
         "actual_original_complete_buy_gas_receipts":"UNRESOLVED",
         "verified_direct_public_follower_signal":"UNRESOLVED",
         "stateful_hypothetical_follower_buy_sell":"UNRESOLVED",
         "follower_net_return_1_5_15_min":"UNRESOLVED",
         "P4_B":"PARTIAL","P5":"BLOCKED","production":"NO_GO",
         "permissions":"NO_MERGE NO_DEPLOY NO_GMAIL NO_TRADE"},
         "FALSIFIED_OBSERVER_PROFIT_GATE")
 buyer=freeze["candidate_D503"].lower()
 originalcases={q["label"]:q for q in signed["cases"]}
 headersby={int(q["block"]):q for q in headers["rows"]}
 moves={int(q["block"]):q for q in native["movements"]}
 tokens={(q["wallet"].lower(),int(q["block"])):int(q["token_raw"]) for q in inv["samples"]}
 owner_ms=int(headers["owner_original_milliTimestamp_hex"],16)
 output=[]
 for i,q in enumerate(case):
  receipt=probe["results"][i]
  real=originalcases[q["label"]]
  expected=pre["actual_buy_candidates_frozen_before_new_exit_RPC"][0]
  require(expected["wallet"].lower()==buyer and
          (q["tx"]==real["tx"]==receipt["tx"]) and
          int(q["block"])==int(real["block"]) and
          int(q["tx_value_wei"])==int(real["tx_value_wei"]) and
          real["from"].lower()==buyer and real["kind"]=="purchase" and
          real["receipt"]["status"]=="0x1", "ORIGINAL_SIGNED_ACTUAL_BUY_IDENTITY")
  r=receipt["ethGetTransactionReceipt"]
  t=receipt["debugTraceTransaction"]
  require(r["rpc_text_chars"]==8098 and r["complete_parseable_JSON"] is False and
          r["visible_status"]=="0x1" and
          r["visible_transaction_specific_gasUsed"]=="UNRESOLVED" and
          r["visible_effectiveGasPrice"]=="UNRESOLVED" and
          t["status"]=="UNAVAILABLE_FREE_TIER" and
          t["call_trace"]=="UNKNOWN" and
          "not available on the Free tier" in t["provider_error_exact"],
          "PROVIDER_CLIPPED_OR_DENIED_NOT_PROFIT")
  buy_block=int(q["block"])
  sale_label="D503_SELL_"+str(i+1)
  approve_label="D503_APPROVE_"+str(i+1)
  sold=originalcases[sale_label]
  approved=originalcases[approve_label]
  sell_block=int(sold["block"])
  require(sold["kind"]=="sale" and
          approved["kind"]=="approve" and
          sold["receipt"]["status"]==approved["receipt"]["status"]=="0x1" and
          sold["from"].lower()==approved["from"].lower()==buyer and
          approved["block"]==sold["block"] and sell_block>buy_block and
          sold["matched_original_event"]["words"][3]==real["matched_original_event"]["words"][3],
          "ORIGINAL_SIGNED_SALE_AND_INVENTORY_IDENTITY")
  require(tokens[(buyer,buy_block-1)]==0 and
          tokens[(buyer,buy_block)]==int(real["matched_original_event"]["words"][3]) and
          tokens[(buyer,sell_block)]==0,
          "EXACT_TOKEN_INVENTORY_CLOSED")
  buy_m=moves[buy_block]
  sold_m=moves[sell_block]
  debit=-int(buy_m["block_native_delta_wei"])
  credit=int(sold_m["block_native_delta_wei"])
  require(debit>int(real["tx_value_wei"])>0 and credit>0 and
          int(buy_m["end_balance_wei"])-int(buy_m["pre_balance_wei"])==-debit and
          int(sold_m["end_balance_wei"])-int(sold_m["pre_balance_wei"])==credit,
          "NATIVE_SELECTED_BLOCK_DIRECTIONS")
  # Do not infer unknown buy gasUsed from near-integer balance residuals.
  require(real["receipt"]["gas_used_wei_gas_units"] is None and
          sold["receipt"]["complete"] is True and approved["receipt"]["complete"] is True,
          "HISTORIC_BUY_RECEIPT_STILL_TRUNCATED")
  buy_ms=int(headersby[buy_block]["milliTimestamp_hex"],16)
  sell_ms=int(headersby[sell_block]["milliTimestamp_hex"],16)
  require(0<buy_ms-owner_ms<sell_ms-owner_ms and
          headersby[buy_block]["response_is_truncated"] in (True,False) and
          headersby[sell_block]["response_is_truncated"] in (True,False),
          "HISTORICAL_HEADER_TIME_ORDER")
  buy_delay=buy_ms-owner_ms
  exit_delay=sell_ms-owner_ms
  require(60000<buy_delay<300000 and exit_delay<300000,
          "NO_AFTER_60S_EXECUTION_IN_SELECTED_ACTUAL_BUYS")
  diff=credit-debit
  require(diff>0,"SELECTED_BLOCK_NATIVE_GRADE_ONLY")
  output.append({
      "case":q["label"],"actual_buy_hash":real["tx"],"actual_signed_sale_hash":sold["tx"],
      "selected_owner_signal_block":int(pre["owner"]["block"]),
      "owner_to_actual_buy_block_timestamp_ms":buy_delay,
      "owner_to_actual_sell_block_timestamp_ms":exit_delay,
      "real_buyer_hold_timestamp_ms":sell_ms-buy_ms,
      "actual_buyer_execution_signed_buy_and_sell":True,
      "selected_buy_block_BNB_debit_wei":str(debit),
      "selected_sale_block_BNB_credit_wei":str(credit),
      "selected_TWO_block_native_delta_wei":str(diff),
      "selected_block_return_to_total_debits_bps_x1e4":
       str(diff*100000000//debit),
      "actual_buy_gas_used":"UNRESOLVED",
      "internal_native_calltrace":"UNAVAILABLE_FREE_TIER",
      "owner_public_observer_arrival_time":"UNRESOLVED",
      "causal_wallet_attributable_roundtrip_profit":"UNRESOLVED",
      "actual_follower_ROI":"UNRESOLVED"
  })
 require(len(output)==2 and sum(int(x["selected_TWO_block_native_delta_wei"]) for x in output)==
         int(native["selected_4_blocks_sum_D503_native_delta_wei"])==
         61218026868859435,
         "TOTAL_FOUR_REAL_BLOCK_DELTA_NOT_FOLLOWER_RETURN")
 require(tokens[("0xe11b917d591db3bf40ecb5bf7ea4ea5af503460c",83636127)] > 0,
         "FROZEN_E11B_NO_CURVE_EXIT_STILL_UNKNOWN_NOT_LOSS")
 return {
   "schema":"BSC_P4B_DRAGON_D503_ACTUAL_2026_SIGNED_ROUNDTRIPS_CUTOFF_WINDOW_OBSERVATION_NOT_ROI",
   "source_sha":{k:v[1] for k,v in SOURCES.items()},
   "selection_grade":"ALREADY_EXPOSED_TWO_ACTUAL_MARKET_BUYERS_AND_ONE_EXIT_UNKNOWN",
   "boundary_source":"HISTORICAL_BLOCK_HEADER_TIMESTAMPS_NOT_PUBLIC_OBSERVER_SIGNAL_ARRIVAL",
   "cutoffs_after_DDAC_original_buy_seconds":{
     "60":{"D503_buy_and_subsequent_exit_both_inside_cutoff":0,"causal_follower_net_return":"UNRESOLVED"},
     "300":{"D503_buy_and_subsequent_exit_both_inside_cutoff":2,"causal_follower_net_return":"UNRESOLVED"},
     "900":{"D503_buy_and_subsequent_exit_both_inside_cutoff":2,"causal_follower_net_return":"UNRESOLVED"}
   },
   "selected_four_blocks_sum_native_delta_wei":str(sum(int(x["selected_TWO_block_native_delta_wei"]) for x in output)),
   "verified_original_buyer_complete_transaction_gas_receipts":0,
   "verified_causal_external_follower_entries":0,
   "P4_B":"PARTIAL","P5":"BLOCKED","production":"NO_GO","rows":output
 }

if __name__=="__main__":
 print(json.dumps(build(load()),ensure_ascii=False,indent=2,sort_keys=True))
