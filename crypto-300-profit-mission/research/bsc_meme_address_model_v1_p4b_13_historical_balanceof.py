#!/usr/bin/env python3
"""Verify 13 historical owner ERC20 balanceOf tool returns against ORIGINAL signed token flows.

Read-only archive. No claim of fresh/current inventory, causal follower signal, executable U, or P5.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = {
    "freeze": ("bsc-meme-address-model-v1-p4b-2026-thirteen-historic-erc20-owner-balances-prefreeze-2026-10-18.json",
               "b1a5a196fabbea4fa0265a72d1c71d7660e6a899"),
    "readback": ("bsc-meme-address-model-v1-p4b-2026-thirteen-historic-erc20-owner-balances-actual-readback-2026-10-18.json",
                 "7e930c57fb5ba3a3dfd795575c059ade9f8a387d"),
    "ddac": ("bsc-meme-address-model-v1-p4c-dragon-ddac-closed-native-loss-2026-10-15.json",
             "4e76eea4d7ab001360af82f15de5eefc8509c501"),
    "e239": ("bsc-meme-address-model-v1-p4c-239e-dragon-two-owner-native-settlements-2026-10-15.json",
             "46e90123b98d5324e05388b17b8a3bbb77cb5361"),
    "e8": ("bsc-meme-address-model-v1-p4c-8e6b-hajimi-dragon-two-verified-native-positive-2026-10-15.json",
           "dc144d9d259ef1392478d1e25d48f2f649744f20"),
    "d503": ("bsc-meme-address-model-v1-p4b-dragon-postowner-original-seven-txs-2026-10-16.json",
             "b06b2ef565ebd74bc7f83ad4a2ea731eeb5cb2b9")
}
GRADE = "ALCHEMY_TOOL_PARSED_RETURN_32BYTE_NOT_ORIGINAL_PROVIDER_TRANSPORT_FULL"
def check(good, reason):
    if not good:
        raise ValueError("P4B_13_BALANCEOF_" + reason)
def load(directory=ROOT):
    docs={}
    for key,(name,pin) in SOURCES.items():
        raw=(directory/name).read_bytes()
        sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        check(sha==pin,"SOURCE_GIT_BLOB_CHANGED_"+key)
        docs[key]=json.loads(raw)
    return docs
def reconstructed(d):
    source_ddac=d["ddac"]["round"]
    check(source_ddac["entry_block"]==83635776 and
          source_ddac["exit_block"]==83635800 and
          source_ddac["entry_token_amount_raw"]==source_ddac["exit_token_amount_raw"] and
          source_ddac["residual_token_raw"]=="0","DDAC_ORIGINAL_SIGNED_SOURCE")
    flows={"DDAC_DRAGON":[
        (source_ddac["entry_block"],int(source_ddac["entry_token_amount_raw"])),
        (source_ddac["exit_block"],-int(source_ddac["exit_token_amount_raw"]))
    ]}
    p=d["e239"]["rounds"]
    check(len(p)==2 and
          [len(q["txs"]) for q in p]==[3,2] and
          all(q["exact_CA"]==source_ddac["exact_CA"] for q in p) and
          all(q["owner"]==p[0]["owner"] and q["token_inventory_residual_raw"]=="0"
              for q in p),"239E_ORIGINAL_SOURCE")
    flows["239E_DRAGON"]=[]
    for owner_round in p:
        for tx in owner_round["txs"]:
            delta=int(tx["wallet_signed_token_delta_raw"])
            check(tx["action"]==("BUY" if delta>0 else "SELL") and
                  abs(delta)==int(tx["token_raw"]) and
                  tx["complete_receipt"] is True,
                  "239E_SIGNED_DELTA_INVENTORY")
            flows["239E_DRAGON"].append((tx["block"],delta))
    e8=d["e8"]["rounds"]
    check([x["round_key"] for x in e8]==["8E6B_HAJIMI_R1","8E6B_DRAGON_R2"] and
          all(x["source_closed_raw_quantity"] is True and
              x["original_receipt_success_all"] is True and
              x["residual_raw"]=="0" for x in e8),
          "8E6B_ORIGINAL_SOURCE")
    for k,x in zip(("8E6B_HAJIMI","8E6B_DRAGON"),e8):
        flows[k]=[(x["buy"][0]["block"],int(x["buy"][0]["received_token_raw"]))]
        flows[k]+=[(s["block"],-int(s["sold_token_raw"])) for s in x["sells"]]
        check(sum(n for _,n in flows[k])==0,"8E6B_ORIGINAL_SIGNED_INVENTORY")
    cases={
        "DDAC_DRAGON":(source_ddac["owner"],source_ddac["exact_CA"]),
        "239E_DRAGON":(p[0]["owner"],p[0]["exact_CA"]),
        "8E6B_HAJIMI":(e8[0]["owner"],e8[0]["exact_CA"]),
        "8E6B_DRAGON":(e8[1]["owner"],e8[1]["exact_CA"])
    }
    for v in flows.values():
        v.sort()
        running=0
        for _,amt in v:
            running+=amt
            check(running>=0,"SIGNED_INVENTORY_NEVER_NEGATIVE")
        check(running==0,"SIGNED_INVENTORY_COMPLETE_EXIT")
    return cases, flows
def build(d):
    f=d["freeze"]
    raw=d["readback"]
    check(raw["freeze_source"]=={
            "path":SOURCES["freeze"][0],"blob":SOURCES["freeze"][1],
            "was_committed_before_13_rpc":True} and
          f["max_fresh_queries"]==13 and f["frozen_rpc_calls"]==13 and
          raw["total_precommitted_calls"]==raw["total_calls_executed"]==13 and
          raw["retries"]==0 and
          raw["network"]==f["network"]=="bnb-mainnet" and
          raw["selector"]==f["selector"]=="0x70a08231" and
          raw["grading"]==
          "ALCHEMY_TOOL_PARSED_32BYTE_RETURNS_WITH_EXACT_CALL_ARGS_NOT_BYTEWISE_FULL_PROVIDER_REQUEST_AND_RESPONSE_TRANSCRIPT",
          "RPC_SCOPE_OR_PROVENANCE")
    check(raw["gates"]=={
            "public_executable_U":"UNRESOLVED",
            "actual_follower_profit_1_5_15":"UNRESOLVED",
            "P4_B":"PARTIAL","P5":"BLOCKED","production":"NO_GO",
            "permissions":"NO_MERGE NO_DEPLOY NO_GMAIL NO_TRADE"} and
          f["gates"]["qualified_causal_observer_U"]=="UNRESOLVED" and
          f["gates"]["follower_profit_1_5_15_min"]=="UNRESOLVED",
          "NO_REALTIME_OR_FOLLOWER_OVERCLAIM")
    cases,flows=reconstructed(d)
    scope=f["fixed_cases"]
    check(len(scope)==4 and [v["label"] for v in scope]==list(cases) and
          len(raw["historical_exact_CA_and_owner_balance_rows"])==13,
          "CA_OR_WALLET_SCOPE_CHANGED")
    sampled=[]
    matched=0
    n=0
    for case in scope:
        label=case["label"]
        wallet,CA=cases[label]
        check(wallet.lower()==case["wallet"].lower() and
              CA.lower()==case["CA"].lower(),"FROZEN_SIGNER_CASE_CHANGED")
        for point in case["checkpoints"]:
            row=raw["historical_exact_CA_and_owner_balance_rows"][n]
            block=point["block"]
            identifier=f"{label}:{block}"
            expected=sum(amount for b,amount in flows[label] if b<=block)
            check(row["label"]==label and row["block"]==block and
                  row["checkpoint_reason"]==point["reason"] and
                  row["wallet"]==case["wallet"].lower() and
                  row["token_CA"]==case["CA"].lower(),
                  "CHECKPOINT_IDENTITY")
            check(expected>=0 and
                  str(expected)==f["predeclared_expected_bounded_reconstructed_raw"][identifier],
                  "OLD_SIGNED_FLOW_VS_PRE_RPC_FROZEN_EXPECTATION")
            calldata="0x70a08231"+wallet[2:].lower().rjust(64,"0")
            blocktag=hex(block)
            check(row["eth_call_calldata"]==calldata and
                  row["eth_call_blockTag"]==blocktag and
                  row["independent_block_hash_and_actual_provider_received_blockTag"]==
                    "NOT_CAPTURED" and
                  row["source_grade"]==GRADE,
                  "HISTORICAL_RPC_PARAMETERS_ONLY_NO_FULL_PROVIDER_CAPTURE")
            h=row["tool_return_hex"]
            check(isinstance(h,str) and len(h)==66 and h.startswith("0x") and
                  all(c in "0123456789abcdefABCDEF" for c in h[2:]) and
                  row["exact_32byte_success"] is True and
                  int(h,16)==int(row["observed_raw_balance"]),
                  "ONCHAIN_UINT256_32BYTE_RETURN")
            check(row["precommitted_selected_event_reconstructed_raw"]==str(expected) and
                  row["observed_raw_balance"]==str(expected) and
                  row["matching_selected_event_raw"] is True,
                  "REAL_CHAIN_BALANCE_VS_SIGNED_TOKENS")
            matched+=1
            sampled.append({"case":label,"block":block,
                "wallet":wallet.lower(),"CA":CA.lower(),
                "historical_block_end_balanceOf_uint256_raw":row["observed_raw_balance"],
                "signed_events_reconstructed_token_raw":str(expected),
                "agreement":"MATCH",
                "historical_full_ERC20_balance_observed":True,
                "current_balance_live_checked":False,
                "public_observer_buy_sell_fills":"UNRESOLVED"})
            n+=1
    check(matched==13 and
          raw["all_rows_match_predeclared_selected_events"] is True and
          raw["zero_balance_at_DDAC_D503_buy_block"] is True and
          raw["zero_balance_for_239E_at_between_rounds_block"] is True and
          raw["nonzero_8E6B_at_first_partial_sale"] is True,
          "ACTUAL_READBACK_MATCH_COUNTS")
    d503=[x for x in d["d503"]["cases"] if x["label"]=="D503_BUY_1"]
    check(len(d503)==1 and d503[0]["block"]==83636000 and
          d503[0]["receipt"]["status"]=="0x1" and
          next(x["historical_block_end_balanceOf_uint256_raw"] for x in sampled
               if x["case"]=="DDAC_DRAGON" and x["block"]==83636000)=="0",
          "DDAC_WAS_ZERO_BALANCE_WHEN_D503_BOUGHT")
    return {
       "schema":"BSC_P4B_2026_THIRTEEN_HISTORIC_CHAIN_OWNER_POSITION_RECONCILIATION",
       "source_pins":{k:pin for k,(_,pin) in SOURCES.items()},
       "provenance_grade":"HISTORICAL_TOOL_PARSED_32BYTE_ETH_CALL_NOT_PROVIDER_TRANSPORT_FULL",
       "counts":{"precommitted_historic_balance_calls":13,
                 "historical_balance_successes":13,
                 "full_onchain_ERC20_balances_equal_selected_signed_flows":13,
                 "unique_wallets":3,"unique_CAs":2,
                 "present_2026_10_18_live_balance_queries":0,
                 "causal_follower_transactions_verified":0},
       "ddac_zero_at_actual_d503_buy_block":True,
       "239e_genuinely_zero_between_signed_rounds":True,
       "hajimi_nonzero_after_first_partial_sell":True,
       "historical_rows":sampled,
       "strict_limits":[
          "Historical ERC20 balanceOf at precisely selected block end only; not a global trace, arbitrary time-series or latest balance",
          "Historical blockTag and calldata were sent via tool args; full provider network transport and block hash not archived",
          "Balance data alone does not prove provider public observer delivery time or actual follower trades",
          "No valid causal 1/5/15 minute BNB PnL, route/gas/tax/capacity or U from this study"
       ],
       "PUBLIC_EXECUTABLE_U":"UNRESOLVED","P4_B":"PARTIAL",
       "P5":"BLOCKED","PRODUCTION":"NO_GO"
    }
if __name__=="__main__":
    print(json.dumps(build(load()),ensure_ascii=False,indent=2,sort_keys=True))
