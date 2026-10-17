#!/usr/bin/env python3
"""Compare frozen 2026 original owner outcomes vs FIRST SCOPED DEX liquidity, not public U."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = {
 "freeze": ("bsc-meme-address-model-v1-p4b-three-signed-rounds-6headers-crossmarket-precommit-2026-10-18.json", "be00df3b8c2cb07b81368ecac41ca6bc0c85b217"),
 "header_attempts": ("bsc-meme-address-model-v1-p4b-three-signed-rounds-6headers-source-readback-2026-10-18.json", "213138da6fb6d5a2b4ff4bc18213cb668ca1dee5"),
 "matrix": ("bsc-meme-address-model-v1-p4c-23x19-crosswallet-native-verified-matrix-2026-10-15.json", "39c94ce57937c00528523607c0b3e7e0c20b3693"),
 "positive": ("bsc-meme-address-model-v1-p4c-8e6b-hajimi-dragon-two-verified-native-positive-2026-10-15.json", "dc144d9d259ef1392478d1e25d48f2f649744f20"),
 "negative": ("bsc-meme-address-model-v1-p4c-dragon-ddac-closed-native-loss-2026-10-15.json", "4e76eea4d7ab001360af82f15de5eefc8509c501"),
 "d503": ("bsc-meme-address-model-v1-p4b-dragon-postowner-original-seven-txs-2026-10-16.json", "b06b2ef565ebd74bc7f83ad4a2ea731eeb5cb2b9"),
 "d503_native": ("bsc-meme-address-model-v1-p4b-dragon-two-buyers-historic-native-balances-2026-10-16.json", "9ac3c2bef80e5ada78c87f0949d19f80eb55ecab"),
}
def assert_true(value, code):
 if not value: raise ValueError("P4B_CROSS_MARKET_" + code)
def load(base=ROOT):
 docs={}
 for key,(name,pin) in FILES.items():
  raw=(base/name).read_bytes()
  blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
  assert_true(blob==pin,"PINNED_SOURCE_DRIFT_"+key)
  docs[key]=json.loads(raw)
 return docs
def build(d):
 f,headers,matrix,pos,neg,signed,native=(d[k] for k in
   ("freeze","header_attempts","matrix","positive","negative","d503","d503_native"))
 assert_true(headers["expected_request_count"]==headers["actual_request_count"]==6 and
             headers["scope_precommit"]==FILES["freeze"][0] and
             headers["source_grade"]==
             "PROVIDER_TOOL_CLIPPED_PER_BLOCK_NO_COMPLETE_JSON_NO_TIMESTAMP_HENCE_BLOCK_DISTANCE_ONLY" and
             [z["block"] for z in headers["results"]]==f["new_historical_read_scope"]["blocks"] and
             all(q["length_chars"]==8098 and q["parsed_complete"] is False and
                 q["timestamp"]=="UNRESOLVED" and
                 q["milliTimestamp"]=="UNRESOLVED" and
                 q["status"]=="TOOL_TEXT_TRUNCATED" and
                 q["blockTag"]==hex(q["block"]) for q in headers["results"]),
             "NO_PROVIDER_TIMESTAMP_OR_GLOBAL_FIRST_U")
 assert_true(f["source_git_blobs"]=={
       "matrix":FILES["matrix"][1],"positive_8e6b":FILES["positive"][1],
       "negative_ddac":FILES["negative"][1],
       "actual_post_owner_d503":FILES["d503"][1],
       "source_ddac_D503_BNB":FILES["d503_native"][1]},
             "PRECOMMIT_COHORT_AND_VERSION")
 assert_true(len(matrix["markets"])==19 and len(matrix["wallets"])==23 and
             matrix["summary"]["implicit_wallet_CAs"]==437 and
             matrix["summary"]["qualified_public_entry_follower_signals"]==0 and
             len(f["fixed_original_wallet_rounds"])==3,
             "FROZEN_23x19_UNIVERSE_NOT_A_WIN_RATE")
 assert_true(f["gates"]=={
         "public_first_global_U":"UNRESOLVED",
         "external_causal_copyability":"UNRESOLVED",
         "follower_1_5_15_min_net_return":"UNRESOLVED",
         "P4_B":"PARTIAL","P5":"BLOCKED","production":"NO_GO",
         "restrictions":"NO_MERGE NO_DEPLOY NO_GMAIL NO_TRADE"},
         "OVERCLAIM_PUBLIC_U_P5_OR_TRADE")
 markets={q["exact_CA"]:q for q in matrix["markets"]}
 positives={q["round_key"]:q for q in pos["rounds"]}
 assert_true(len(positives)==2 and
             pos["summary"]["source_proven_signed_positive_native_rounds"]==2,
             "ORIGINAL_TWO_POSITIVE_WALLET_ROUNDS")
 original=neg["round"]
 assert_true(int(original["native_closed_owner_round_net_wei"])<0 and
             original["native_closed_owner_round_classification"]=="REALIZED_NEGATIVE_BNB_WINDOW" and
             original["residual_token_raw"]=="0",
             "DDAC_NEGATIVE_OR_EXIT_UNKNOWN")
 source_rounds={
 "DDAC_DRAGON_NEGATIVE":{
  "wallet":original["owner"],"CA":original["exact_CA"],
  "entry_block":original["entry_block"],"exit_block":original["exit_block"],
  "net":int(original["native_closed_owner_round_net_wei"]),
  "spent":int(original["native_buy_block_debit_wei"]),
  "source_classification":original["native_closed_owner_round_classification"],
 },
 }
 for key,q in positives.items():
  source_rounds[key]={
   "wallet":q["owner"],"CA":q["exact_CA"],
   "entry_block":q["buy"][0]["block"],"exit_block":q["sells"][-1]["block"],
   "net":int(q["actual_native_round_net_wei"]),
   "spent":int(q["native_wallet_buy_block_spend_wei"]),
   "source_classification":q["classification"]
  }
 out=[]
 for a in f["fixed_original_wallet_rounds"]:
  code=a["label"]
  s=source_rounds[{"DDAC_DRAGON_NEGATIVE":"DDAC_DRAGON_NEGATIVE",
        "8E6B_HAJIMI_POSITIVE":"8E6B_HAJIMI_R1",
        "8E6B_DRAGON_POSITIVE":"8E6B_DRAGON_R2"}[code]]
  market=markets[a["CA"]]
  begin=int(a["entry_block"])
  dx=begin-int(market["first_scoped_dex_liquidity_block"])
  assert_true(a["wallet"].lower()==s["wallet"].lower() and
      a["CA"]==s["CA"] and begin==s["entry_block"] and
      int(a["exit_block"])==s["exit_block"] and
      int(a["selected_BNB_native_net_wei"])==s["net"] and s["spent"]>0,
      "OWNER_SIGNED_SOURCES_VS_FROZEN_COHORT")
  assert_true(dx==(-352 if code=="DDAC_DRAGON_NEGATIVE" else
         10902409 if code=="8E6B_HAJIMI_POSITIVE" else 9948153),
         "SIGNED_ENTRY_IS_NOT_ALWAYS_EARLY_MARKET_ENTRY")
  assert_true((s["net"]>0)==(dx>0),"SELECTED_EARLY_OWNER_WAS_NEGATIVE")
  out.append({
   "frozen_case":code,"wallet":s["wallet"],"token":market["token"],
   "exact_CA":a["CA"],"entry_block":begin,"exit_block":s["exit_block"],
   "first_SCOPED_dex_liquidity_block":market["first_scoped_dex_liquidity_block"],
   "owner_entry_minus_first_SCOPED_dex_block_count":dx,
   "market_position":"PRE_SCOPED_DEX_LIQUIDITY" if dx<0 else "POST_SCOPED_DEX_LIQUIDITY",
   "owner_actual_BNB_selected_round_net_wei":str(s["net"]),
   "owner_native_buy_block_spend_wei":str(s["spent"]),
   "owner_signed_native_round_roi_bps_trunc":
      str(s["net"]*10000//s["spent"]),
   "owner_source_grade":s["source_classification"],
   "global_market_first_public_buyable_U":"UNRESOLVED",
   "wallet_actual_public_followers_net_profit":"UNRESOLVED",
   "1_5_15_minute_fixed_delay_follower_ROI":"UNRESOLVED"
  })
 dragon=next(q for q in out if q["frozen_case"]=="DDAC_DRAGON_NEGATIVE")
 later=next(q for q in out if q["frozen_case"]=="8E6B_DRAGON_POSITIVE")
 actual_d503=[q for q in signed["cases"] if q["label"] in ("D503_BUY_1","D503_BUY_2")]
 assert_true([q["block"] for q in actual_d503]==[83636000,83636084] and
             all(q["from"].lower()==
                 "0xd503f69b37efbfe510e37f46a4ca34e0adb1a7aa"
                 and q["receipt"]["status"]=="0x1" for q in actual_d503) and
             dragon["exit_block"]<actual_d503[0]["block"]<
                 later["entry_block"] and
             native["selected_4_blocks_sum_D503_native_delta_wei"]==
                "61218026868859435",
             "SAME_DRAGON_TOKEN_ORIGINAL_OWNER_EXIT_BEFORE_LATER_BUYERS")
 return {
  "schema":"BSC_P4B_2026_THREE_ORIGINAL_WALLET_ACTUAL_OUTCOMES_VS_FIRST_SCOPED_LP",
  "source_sha":{key:item[1] for key,item in FILES.items()},
  "sample":{"wallets_23":23,"exact_CAs_19":19,"original_cells_437":437,
            "handpicked_existing_high_grade_owner_rounds":3,
            "markets_in_this_narrow_comparison":2,
            "followable_global_U_confirmed":0,"observed_causal_follower_profit_rounds":0},
  "matched_three_source_owned_trade_outcomes":out,
  "same_Dragon_market":{"DDAC_actual_owner_exit_block":dragon["exit_block"],
            "D503_real_later_signed_first_buy_block":actual_d503[0]["block"],
            "D503_buy_happened_after_DDAC_exit_blocks":actual_d503[0]["block"]-dragon["exit_block"],
            "8E6B_original_signed_buyer_later_entry_block":later["entry_block"],
            "cannot_claim_D503_followed_DDAC":True,
            "cannot_count_D503_selected_native_block_profit_as_causal_DDAC_following":True},
  "limits":["FIRST_SCOPED_DEX_LIQUIDITY is only first in pre-existing venue/LP source scope, not global market first buy, global tradable U, or creator mint.",
       "This comparison uses already exposed, selected favorable/unfavorable signed wallet samples, not unbiased 437 cell random outcomes or 2026 holdout.",
       "Historical block header timestamp provider responses were clipped for all 6 requested blocks; no market duration/date derived.",
       "No historical buy-at-1m/5m/15m exact clock-time fill, wallet real-time observer message arrival or stateful follower exit simulated."],
  "policy_candidate_only_not_live_signal":"ORIGINAL_SIGNAL_OWNER_POSITION_ALREADY_EXITED_BEFORE_LATER_BUYER_MAY_NEGATE_COPY_SIGNAL",
  "P4_B":"PARTIAL","P5":"BLOCKED","production":"NO_GO"
 }
if __name__=="__main__":
 print(json.dumps(build(load()),ensure_ascii=False,indent=2,sort_keys=True))
