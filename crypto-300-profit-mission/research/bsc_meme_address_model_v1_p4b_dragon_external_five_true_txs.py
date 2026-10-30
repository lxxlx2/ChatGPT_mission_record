#!/usr/bin/env python3
"""Read-only exact five Dragon external-signer original tx and matched historical funds.

Strong evidence: actual original signed buys/sells, historical ERC20 balance and
selected owner-block BNB deltas. Not evidence of causally following DDAC and not
evidence of complete transaction-specific buy receipt Gas.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FILES={
    "freeze0":("bsc-meme-address-model-v1-p4b-dragon-five-actual-external-tx-independent-fee-precommit-2026-10-18.json","4b2e0f7bf92a6abd05011f8acf416016618eb862"),
    "freeze":("bsc-meme-address-model-v1-p4b-dragon-five-external-signer-original-tx-alchemy-free-precommit-2026-10-18.json","47225db058589e131132ac6b308280b81c0cb4ff"),
    "readback":("bsc-meme-address-model-v1-p4b-dragon-five-external-signer-original-tx-alchemy-readback-2026-10-18.json","9e8653a684aa88ecdb808b64d647ca676a2327d2"),
    "blockscout_denied":("bsc-meme-address-model-v1-p4b-dragon-five-external-blockscout-public-denied-2026-10-18.json","324458ba11dabbd9c6a39db8548b45d83a14a7ad"),
    "original7":("bsc-meme-address-model-v1-p4b-dragon-postowner-original-seven-txs-2026-10-16.json","b06b2ef565ebd74bc7f83ad4a2ea731eeb5cb2b9"),
    "original_native":("bsc-meme-address-model-v1-p4b-dragon-two-buyers-historic-native-balances-2026-10-16.json","9ac3c2bef80e5ada78c87f0949d19f80eb55ecab"),
    "original_inventory":("bsc-meme-address-model-v1-p4b-dragon-two-buyers-historic-token-inventory-2026-10-16.json","06bba24e15530cf9f0f7fde24ab876fcc764d173"),
    "old_ddac":("bsc-meme-address-model-v1-p4c-dragon-ddac-closed-native-loss-2026-10-15.json","4e76eea4d7ab001360af82f15de5eefc8509c501")
}

def ensure(value, reason):
    if not value: raise ValueError("P4B_DRAGON_REAL_EXTERNAL_"+reason)
def load(root=ROOT):
    d={}
    for key,(name,pin) in FILES.items():
        raw=(root/name).read_bytes()
        blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        ensure(blob==pin,"GIT_BLOB_PIN_"+key)
        d[key]=json.loads(raw)
    return d

def build(d):
    f0,f,read,blocked,original,native,inventory,ddac=(d[z] for z in (
        "freeze0","freeze","readback","blockscout_denied","original7",
        "original_native","original_inventory","old_ddac"))
    ensure(f["frozen_prior_same_five"]==FILES["freeze0"][0] and
           f["max_calls"]==read["request_count"]==read["executed_count"]==5 and
           f["retries"]==read["retries"]==0 and
           f["strict_precommitted_selection"] is True and
           len(f0["frozen_reads"])==len(f["frozen_hashes"])==len(read["results"])==5 and
           read["source_precommit"]=={"file":FILES["freeze"][0],
               "git_blob_sha":FILES["freeze"][1],"pre_frozen_before_calls":True} and
           read["source_grade"]==
              "TOOL_PARSED_FULL_TRANSACTION_FIELDS_NOT_COMPLETE_PROVIDER_NETWORK_WIRE_REQUEST_AND_RESPONSE" and
           read["method"]==f["method"]=="eth_getTransactionByHash" and
           f["network"]==read["network"]=="bnb-mainnet",
           "FREE_PROVIDER_SCOPE_AND_PROVENANCE")
    ensure(f["further_source_pins"]=={
       "original_seven":FILES["original7"][1],
       "original_four_balance_delta":FILES["original_native"][1],
       "original_D503_token_inventory":FILES["original_inventory"][1],
       "original_DDAC_full_early_loss":FILES["old_ddac"][1]} and
       blocked["source_scope"]==FILES["freeze0"][0] and
       blocked["no_paid_upgrade"] is True and
       blocked["no_retry_after_explicit_key_denial"] is True and
       blocked["source_grade"]=="PROVIDER_ACCESS_DENIED_NOT_ONCHAIN_RECEIPT" and
       blocked["gas_used"]=="UNRESOLVED" and
       blocked["fee"]=="UNRESOLVED",
       "INDEPENDENT_PROVIDER_ACCESS_DENIED_NOT_ZERO_GAS")
    ensure(read["gates"]=={
      "PUBLIC_EXECUTABLE_U":"UNRESOLVED","P5":"BLOCKED","PRODUCTION":"NO_GO",
      "no_merge":True,"no_deploy":True,"no_gmail":True,"no_trade":True} and
      f["gates"]=={"P4_B":"PARTIAL","PUBLIC_EXECUTABLE_U":"UNRESOLVED",
      "P5":"BLOCKED","production":"NO_GO",
      "permissions":"NO_MERGE NO_DEPLOY NO_GMAIL NO_TRADE"},
      "NO_PUBLIC_OBSERVER_OR_PRODUCTION_OVERCLAIM")
    ensure(original["token_exact_CA"]==f0["token_exact_CA"]==
        ddac["round"]["exact_CA"]=="0xeccbb861c0dda7efd964010085488b69317e4444" and
        ddac["round"]["exit_block"]==83635800 and
        ddac["round"]["residual_token_raw"]=="0" and
        int(ddac["round"]["native_closed_owner_round_net_wei"])<0,
        "OLD_EARLY_OWNER_ALREADY_EXITED")
    index={row["label"]:row for row in original["cases"]}
    inventory_by={(x["wallet"],x["block"]):int(x["token_raw"]) for x in inventory["samples"]}
    native_by={int(x["block"]):x for x in native["movements"]}
    ids=["D503_BUY_1","D503_SELL_1","D503_BUY_2","D503_SELL_2","E11B_BUY_1"]
    ensure([x["id"] for x in f0["frozen_reads"]]==ids and
          [x["case"] for x in f["frozen_hashes"]]==ids and
          [x["id"] for x in read["results"]]==ids and
          all(c["receipt"]["status"]=="0x1" for c in index.values()),
          "ACTUAL_SIGNED_SUCCESS_MATCH_OLD_SOURCE")
    observations=[]
    for a,b,c in zip(f0["frozen_reads"],f["frozen_hashes"],read["results"]):
        oid=a["id"]
        raw=index[oid]
        t=c["returned"]
        ensure(c["read_success"] is True and c["tool_json_parseable"] is True and
               c["receipt_gas_used"]=="UNRESOLVED_NOT_PART_OF_ETH_GET_TRANSACTION_BY_HASH" and
               c["tool_response_chars"]<8098 and
               a["hash"]==b["hash"]==raw["tx"]==t["hash"] and
               a["block"]==b["expected_block"]==raw["block"]==int(t["blockNumber"],16) and
               a["wallet"]==b["owner"]==raw["from"]==t["from"] and
               b["expected_value_wei"]==raw["tx_value_wei"]==str(int(t["value"],16)) and
               t["chainId"]=="0x38" and t["type"]=="0x0",
               "SAME_FIVE_ORIGINAL_TX_IDENTITIES")
        ensure(int(t["gas"],16)>0 and int(t["gasPrice"],16)>0 and
               int(t["blockTimestamp"],16)>0 and
               len(t["blockHash"])==66 and
               t["eth_call_data_head"]==
                 ("0x810c705b" if oid=="E11B_BUY_1" else "0x0b3f5cf9") and
               int(t["input_hex_length"])>0,
               "SOURCE_NATIVE_AND_GAS_LIMIT_FIELDS")
        ensure((t["to"]=="0xb300000b72deaeb607a12d5f54773d1c19c7028d" if oid=="E11B_BUY_1" else
                t["to"]=="0x1de460f363af910f51726def188f9004276bf4bc") and
               t["gasPrice"] in ("0xb2d05e00","0x77359400","0x1a13b8600","0x36ddc97"),
               "ACTUAL_ROUTING_AND_REAL_GAS_PRICE_FIELDS")
        observations.append({
           "case":oid,"hash":t["hash"],"block":int(t["blockNumber"],16),
           "chain_timestamp_s":int(t["blockTimestamp"],16),
           "transaction_index_in_block":int(t["transactionIndex"],16),
           "signed_native_tx_value_wei":str(int(t["value"],16)),
           "signed_gas_price_wei_per_unit":str(int(t["gasPrice"],16)),
           "signed_gas_LIMIT_units":str(int(t["gas"],16)),
           "actual_gasUsed_units":"UNRESOLVED" if "BUY" in oid else raw["receipt"]["gas_used_wei_gas_units"],
           "original_receipt_status":raw["receipt"]["status"],
           "original_status_grade":
              "TRUNCATED_SUCCESS_FIELDS" if "BUY" in oid else "COMPLETE_SUCCESS_RECEIPT",
           "signed_buy_not_causally_observed_DDAC":True
        })
    d503=[v for v in observations if v["case"].startswith("D503")]
    e11b=observations[4]
    ensure([x["block"] for x in d503]==[83636000,83636018,83636084,83636094] and
           d503[0]["transaction_index_in_block"]<e11b["transaction_index_in_block"] and
           e11b["block"]==d503[0]["block"]==83636000 and
           ddac["round"]["exit_block"]<d503[0]["block"],
           "LATER_EXTERNAL_TRADES_AFTER_DDAC_EXIT")
    ensure([q["signed_native_tx_value_wei"] for q in observations]==[
           "190000000000000000","0","220000000000000000","0","12000000000000000"] and
           [q["signed_gas_price_wei_per_unit"] for q in observations]==[
           "3000000000","2000000000","7000000000","2000000000","57531543"],
           "SAME_FIVE_ORIGINAL_TX_NATIVE_INPUTS_AND_PRICE")
    ensure([q["chain_timestamp_s"] for q in d503]==sorted([q["chain_timestamp_s"] for q in d503]) and
           [d503[1]["chain_timestamp_s"]-d503[0]["chain_timestamp_s"],
            d503[3]["chain_timestamp_s"]-d503[2]["chain_timestamp_s"]]==[9,5],
           "REAL_SETTLED_HOLDING_TIMES")
    d503_wallet=f["frozen_hashes"][0]["owner"]
    e11b_wallet=f["frozen_hashes"][4]["owner"]
    ensure([inventory_by[(d503_wallet,z)] for z in
            (83635999,83636000,83636017,83636018,83636083,83636084,83636093,83636094)]==
           [0,5033644503996605000000000,5033644503996605000000000,0,
            0,3119477321356746000000000,3119477321356746000000000,0] and
           [inventory_by[(e11b_wallet,z)] for z in (83635999,83636000,83636127)]==
           [0,347546637309143000000000,347546637309143000000000],
           "FULL_HISTORIC_TOKEN_INVENTORY_AND_EXIT_UNKNOWN")
    selected=[]
    for buy,exit in ((83636000,83636018),(83636084,83636094)):
        bought=-int(native_by[buy]["block_native_delta_wei"])
        credited=int(native_by[exit]["block_native_delta_wei"])
        ensure(bought>0 and credited>0 and
               int(native_by[buy]["end_balance_wei"])-int(native_by[buy]["pre_balance_wei"])==-bought and
               int(native_by[exit]["end_balance_wei"])-int(native_by[exit]["pre_balance_wei"])==credited,
               "ACTUAL_OWNER_SELECTED_NATIVE_BALANCE_SIGNS")
        selected.append({"buy_block":buy,"sell_block":exit,
          "actual_EOA_buy_block_BNB_debit_wei":str(bought),
          "actual_EOA_sell_block_BNB_credit_wei":str(credited),
          "selected_two_block_EOA_BNB_delta_wei":str(credited-bought),
          "gas_is_included_in_native_block_balance_change":True,
          "isolated_single_buy_receipt_gas_used":"UNRESOLVED"})
    ensure([x["selected_two_block_EOA_BNB_delta_wei"] for x in selected]==[
            "24264878154473742","36953148714385693"] and
           str(sum(int(x["selected_two_block_EOA_BNB_delta_wei"]) for x in selected))==
             native["selected_4_blocks_sum_D503_native_delta_wei"]==
             "61218026868859435" and
           all(x["selected_two_block_EOA_BNB_delta_wei"]!=
             ddac["round"]["native_closed_owner_round_net_wei"] for x in selected),
           "SELECTED_EOA_NATIVE_DELTA_NOT_DDAC_FOLLOW_PROFIT")
    known_approve_and_sell_gas=[]
    for approve,sell in (("D503_APPROVE_1","D503_SELL_1"),("D503_APPROVE_2","D503_SELL_2")):
        x=index[approve]["receipt"];y=index[sell]["receipt"]
        ensure(x["complete"] is True and y["complete"] is True and
               int(x["gas_used_wei_gas_units"])==46327 and
               int(y["gas_used_wei_gas_units"])==211830 and
               x["effective_gas_price_wei"]==y["effective_gas_price_wei"]=="2000000000",
               "REAL_APPROVE_AND_SELL_GAS_NOT_BUY_GAS")
        known_approve_and_sell_gas.append(
          str((int(x["gas_used_wei_gas_units"])+int(y["gas_used_wei_gas_units"]))*2000000000))
    ensure(known_approve_and_sell_gas==["516314000000000","516314000000000"],
           "KNOWN_APPROVE_AND_SELL_ONLY_GAS")
    return {
      "schema":"BSC_P4B_2026_FIVE_REAL_EXTERNAL_SIGNED_DRAGON_TX_SEPARATE_BUY_GAS_FROM_SELECTED_NET",
      "source_blobs":{k:v[1] for k,v in FILES.items()},
      "source_grade":"ALCHEMY_TOOL_PARSED_ORIGINAL_TX_WITH_OLDER_SIGNED_RECEIPT_AND_HISTORIC_BALANCE",
      "cohort":{"old_wallets":23,"old_exact_CAs":19,"old_cells":437,
                "D503_actual_closed_rounds":2,"E11B_selected_buy_only_exit_UNKNOWN":1,
                "public_causal_follower_rounds_PROVEN":0},
      "observations":observations,
      "D503_real_selected_two_block_native_movements":selected,
      "D503_two_selected_native_positive_BNB_delta_wei":
         native["selected_4_blocks_sum_D503_native_delta_wei"],
      "D503_approve_plus_sell_verified_GAS_fee_wei_for_each_round":known_approve_and_sell_gas,
      "D503_buy_receipt_gasUsed_verified":False,
      "E11B_unresolved_exit_at_last_bounded_83636127":True,
      "DDAC_original_closed_before_both_external_buyers":True,
      "can_prove_causal_copy_of_DDAC":False,
      "can_publish_realizable_1_5_15min_follower_net_profit":False,
      "limitations":[
         "Selected native delta sums wallet block balances; not guaranteed isolated tx-level economic attribution.",
         "An original signed transaction's gas LIMIT is NOT gasUsed and must not be used as confirmed gas fee.",
         "Independent public Blockscout session was denied; no paid PRO key used.",
         "E11B had nonzero true ERC20 holding at 83636127 but no signed closed exit in bounded source; profit unknown.",
         "Actual D503 positive rounds occurred after DDAC original wallet exited; DDAC follower causality unproven.",
         "No public observed signal delivery time, first U, forced 1/5/15 minute entry or identical funds/slippage."
      ],
      "P4_B":"PARTIAL","PUBLIC_EXECUTABLE_U":"UNRESOLVED",
      "P5":"BLOCKED","PRODUCTION":"NO_GO"
    }
if __name__=="__main__":
    print(json.dumps(build(load()),ensure_ascii=False,indent=2,sort_keys=True))
