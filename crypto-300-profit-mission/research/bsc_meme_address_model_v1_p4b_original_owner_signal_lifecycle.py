#!/usr/bin/env python3
"""Reconstruct five selected signed-owner signal lifecycles, NOT live balances or copyable ROI."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = {
    "freeze": ("bsc-meme-address-model-v1-p4b-5owner-rounds-signal-lifecycle-precommit-2026-10-18.json", "a7bda9fcdc8b645da0e9f88fb4664d79f86daa4e"),
    "ddac": ("bsc-meme-address-model-v1-p4c-dragon-ddac-closed-native-loss-2026-10-15.json", "4e76eea4d7ab001360af82f15de5eefc8509c501"),
    "e239": ("bsc-meme-address-model-v1-p4c-239e-dragon-two-owner-native-settlements-2026-10-15.json", "46e90123b98d5324e05388b17b8a3bbb77cb5361"),
    "e8": ("bsc-meme-address-model-v1-p4c-8e6b-hajimi-dragon-two-verified-native-positive-2026-10-15.json", "dc144d9d259ef1392478d1e25d48f2f649744f20"),
    "matrix": ("bsc-meme-address-model-v1-p4c-23x19-crosswallet-native-verified-matrix-2026-10-15.json", "39c94ce57937c00528523607c0b3e7e0c20b3693"),
    "d503": ("bsc-meme-address-model-v1-p4b-dragon-postowner-original-seven-txs-2026-10-16.json", "b06b2ef565ebd74bc7f83ad4a2ea731eeb5cb2b9"),
}

def require(ok, reason):
    if not ok:
        raise ValueError("P4B_OWNER_LIFECYCLE_" + reason)

def load(root=ROOT):
    result={}
    for key,(name,pin) in FILES.items():
        data=(root/name).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
        require(actual==pin, "SOURCE_BLOB_DRIFT_"+key)
        result[key]=json.loads(data)
    return result

def add_event(events, block, tx, action, raw, receipt_grade):
    require(isinstance(block,int) and block>0 and len(tx)==66 and tx.startswith("0x") and
            action in ("BUY","SELL") and int(raw)>0, "SIGNER_EVENT_ENCODING")
    events.append({
        "block":block,"tx":tx.lower(),"action":action,
        "token_delta_raw":str(int(raw) if action=="BUY" else -int(raw)),
        "receipt_source_grade":receipt_grade
    })

def build(d):
    f,ddac,e239,e8,matrix,d503=(d[k] for k in ("freeze","ddac","e239","e8","matrix","d503"))
    require(f["original_cohort"]=={"wallets":23,"exact_CAs":19,"cells":437} and
            len(matrix["wallets"])==23 and len(matrix["markets"])==19 and
            matrix["summary"]["implicit_wallet_CAs"]==437 and
            [c["case"] for c in f["checkpoints_by_signer"]]==f["preselected_round_keys"],
            "COHORT_OR_PRESELECTED_CHECKPOINT_DRIFT")
    require(f["sources"]=={
       "ddac":FILES["ddac"][0],"ddac_blob":FILES["ddac"][1],
       "e239":FILES["e239"][0],"e239_blob":FILES["e239"][1],
       "e8":FILES["e8"][0],"e8_blob":FILES["e8"][1],
       "matrix":FILES["matrix"][0],"matrix_blob":FILES["matrix"][1],
       "d503":FILES["d503"][0],"d503_blob":FILES["d503"][1]},
       "FROZEN_SOURCE_PIN_MAP")
    require(f["max_new_chain_rpc_calls"]==0 and
            f["gates"]=={
               "public_causal_observer_U":"UNRESOLVED",
               "live_wallet_position_authority":"NO_CHAIN_CURRENT_RECONCILIATION",
               "fixed_delay_1_5_15_minute_follower_profit":"UNRESOLVED",
               "P4_B":"PARTIAL","P5":"BLOCKED","production":"NO_GO",
               "permissions":"NO_MERGE NO_DEPLOY NO_GMAIL NO_TRADE"},
            "HISTORICAL_POSITION_NOT_LIVE_SIGNAL")
    markets={m["exact_CA"] for m in matrix["markets"]}
    wallets={w["wallet"].lower() for w in matrix["wallets"]}
    d=ddac["round"]
    require(d["residual_token_raw"]=="0" and d["entry_token_amount_raw"]==
            d["exit_token_amount_raw"] and
            d["native_closed_owner_round_classification"]=="REALIZED_NEGATIVE_BNB_WINDOW" and
            d["native_closed_owner_round_net_wei"]=="-92169615514614272" and
            d["entry_block"]==83635776 and d["exit_block"]==83635800,
            "DDAC_CLOSED_REALIZED_NEGATIVE_PROOF")
    rounds=[]
    ddac_events=[]
    add_event(ddac_events,d["entry_block"],d["entry_tx"],"BUY",d["entry_token_amount_raw"],
              "ORIGINAL_BUY_RECEIPT_TRUNCATED_BUT_SIGNED_AND_BLOCK_BALANCE")
    add_event(ddac_events,d["exit_block"],d["exit_tx"],"SELL",d["exit_token_amount_raw"],
              "ORIGINAL_SIGNED_SALE_AND_SELECTED_NATIVE_SETTLEMENT")
    rounds.append({"key":"DDAC_DRAGON_R1","wallet":d["owner"].lower(),
        "CA":d["exact_CA"],"events":ddac_events,
        "signed_owner_native_net_wei":str(d["native_closed_owner_round_net_wei"]),
        "economic_grade":"SETTLED_OWNER_NATIVE_NEGATIVE_WINDOW_BUY_RECEIPT_TRUNCATED"})

    require(len(e239["rounds"])==2 and
            [len(z["txs"]) for z in e239["rounds"]]==[3,2] and
            [z["native_original_EOA_profit_sign"] for z in e239["rounds"]]==["NEGATIVE","POSITIVE"],
            "239E_TWO_REAL_ROUNDS_MIXED_SIGNS")
    for i,z in enumerate(e239["rounds"]):
        events=[]
        require(z["token_inventory_residual_raw"]=="0" and
                z["token_received_raw"]==z["token_sold_raw"] and
                all(q["complete_receipt"] is True and
                    q["original_owner_single_external_tx_in_block"] is True for q in z["txs"]),
                "239E_SIGNED_RECEIPT_AND_TOKEN_CLOSURE")
        for tx in z["txs"]:
            require(tx["action"] in ("BUY","SELL") and
                    int(tx["wallet_signed_token_delta_raw"]) ==
                    (int(tx["token_raw"]) if tx["action"]=="BUY" else -int(tx["token_raw"])),
                    "239E_OWNER_SIGNED_TOKEN_DELTA")
            add_event(events,tx["block"],tx["hash"],tx["action"],tx["token_raw"],
                      "ORIGINAL_COMPLETE_SUCCESS_RECEIPT_AND_WALLET_DELTA")
        require((i==0 and z["original_native_wallet_net_wei"]=="-15332805033002259" and
                 z["txs"][0]["block"]==85954137 and z["txs"][1]["block"]==85954824 and
                 z["txs"][2]["block"]==85957578) or
                (i==1 and z["original_native_wallet_net_wei"]=="22647938898252522" and
                 z["txs"][0]["block"]==85959961 and z["txs"][1]["block"]==85961371),
                "239E_LOCKED_HISTORIC_TWO_ROUNDS")
        rounds.append({"key":"239E_DRAGON_R"+str(i+1),"wallet":z["owner"].lower(),
            "CA":z["exact_CA"],"events":events,
            "signed_owner_native_net_wei":str(z["original_native_wallet_net_wei"]),
            "economic_grade":"OWNER_NATIVE_BNB_CLOSED_WITH_UNNAMED_ROUTE_COST"})

    require(len(e8["rounds"])==2 and
            [z["round_key"] for z in e8["rounds"]]==["8E6B_HAJIMI_R1","8E6B_DRAGON_R2"],
            "8E6B_TWO_DISTINCT_SELECTED_CAS")
    for z in e8["rounds"]:
        require(z["source_closed_raw_quantity"] is True and
                z["source_original_EOA_all_signed"] is True and
                z["original_receipt_success_all"] is True and z["residual_raw"]=="0" and
                len(z["buy"])==1 and len(z["sells"]) in (1,2) and
                z["classification"]=="SETTLED_OWNER_NATIVE_POSITIVE_WITH_WBNB_GAS",
                "8E6B_SIGNED_SOURCE_AND_NET_PROFIT")
        ev=[]
        add_event(ev,z["buy"][0]["block"],z["buy"][0]["hash"],"BUY",
                  z["buy"][0]["received_token_raw"],"ORIGINAL_COMPLETE_GAS_WBNB_SUCCESS")
        for sell in z["sells"]:
            add_event(ev,sell["block"],sell["hash"],"SELL",
                      sell["sold_token_raw"],"ORIGINAL_COMPLETE_GAS_WBNB_SUCCESS")
        require(sum(int(q["sold_token_raw"]) for q in z["sells"])==
                int(z["original_full_token_bought_raw"])==
                int(z["original_full_token_sold_raw"]),
                "8E6B_CLOSED_INVENTORY_AND_PARTIAL_SALE")
        rounds.append({"key":z["round_key"],"wallet":z["owner"].lower(),
          "CA":z["exact_CA"],"events":ev,
          "signed_owner_native_net_wei":str(z["actual_native_round_net_wei"]),
          "economic_grade":"SETTLED_OWNER_NATIVE_POSITIVE_WITH_WBNB_GAS"})
    require([x["key"] for x in rounds]==f["preselected_round_keys"] and
            {x["wallet"] for x in rounds}.issubset(wallets) and
            all(x["CA"] in markets for x in rounds) and
            len({x["wallet"] for x in rounds})==3 and
            len({x["CA"] for x in rounds})==2,
            "FROZEN_FIVE_EPISODES_THREE_WALLETS_TWO_CAS")
    output_rounds=[]
    timeline=defaultdict(list)
    for rnd in rounds:
        bal=0
        events=[]
        old_block=-1
        for i,x in enumerate(rnd["events"]):
            delta=int(x["token_delta_raw"])
            require(x["block"]>old_block and
                    (delta>0 if x["action"]=="BUY" else delta<0) and
                    bal+delta>=0 and
                    x["action"]==("BUY" if i==0 else x["action"]),
                    "ROUND_SIGNED_ORDER_OR_OVERSOLD")
            old=bal
            bal+=delta
            status=("OPEN_NEW_EPISODE" if i==0 else
                   "OPEN_ADDED_TO_EXISTING_EPISODE" if delta>0 else
                   "OPEN_PARTIAL_EXIT" if bal>0 else "CLOSED_EXACT_SELECTED_EPISODE")
            x={**x,"position_after_SELECTED_signer_events_raw":str(bal),
               "historical_selected_event_state":status,"not_live_chain_balance":True}
            events.append(x)
            timeline[(rnd["wallet"],rnd["CA"])].append({**x,"episode":rnd["key"]})
        require(bal==0 and events[-1]["historical_selected_event_state"]==
                "CLOSED_EXACT_SELECTED_EPISODE","CLOSED_ROUND_MUST_END_ZERO")
        output_rounds.append({"key":rnd["key"],"wallet":rnd["wallet"],"CA":rnd["CA"],
          "original_owner_native_net_wei":rnd["signed_owner_native_net_wei"],
          "owner_net_sign":"POSITIVE" if int(rnd["signed_owner_native_net_wei"])>0 else "NEGATIVE",
          "source_economic_grade":rnd["economic_grade"],"events":events,
          "receipt_or_source_current_wallet_state":"NOT_LIVE_RECONCILED"})

    require([x["block"] for x in timeline[(rounds[1]["wallet"],rounds[1]["CA"])]] ==
            [85954137,85954824,85957578,85959961,85961371],
            "239E_CLOSED_OLD_ROUND_BEFORE_NEW_BUY")
    require(all(x["block"]<y["block"] for key,items in timeline.items()
                for x,y in zip(items,items[1:])),
            "SAME_WALLET_CA_HISTORICAL_SIGNED_ORDER")

    checkpoint_outputs=[]
    for cp in f["checkpoints_by_signer"]:
        rd=next(x for x in rounds if x["key"]==cp["case"])
        sourced=timeline[(rd["wallet"],rd["CA"])]
        for block in cp["blocks"]:
            old=[x for x in sourced if x["block"]<=block]
            last=old[-1] if old else None
            checkpoint_outputs.append({
                "fixed_checkpoint_case":cp["case"],"as_of_HISTORICAL_block_end":block,
                "wallet":rd["wallet"],"exact_CA":rd["CA"],
                "last_selected_event_hash":last["tx"] if last else None,
                "current_selected_episode":last["episode"] if last else None,
                "historical_SIGNED_EVENT_reconstructed_state":
                   last["historical_selected_event_state"] if last else "NO_SELECTED_TX_YET_NOT_PROVEN_FLAT",
                "selected_events_net_token_raw":last["position_after_SELECTED_signer_events_raw"] if last else None,
                "actual_full_onchain_wallet_inventory_at_arbitrary_block":"UNRESOLVED",
                "public_observer_alert_arrival_at_that_block":"UNRESOLVED",
                "follower_buy_and_sell_fill":"UNRESOLVED"
            })
    d503_buys=[x for x in d503["cases"] if x["label"] in ("D503_BUY_1","D503_BUY_2")]
    require(len(d503_buys)==2 and [z["block"] for z in d503_buys]==[83636000,83636084] and
            d503_buys[0]["block"]>ddac_events[-1]["block"] and
            next(x for x in checkpoint_outputs
                 if x["fixed_checkpoint_case"]=="DDAC_DRAGON_R1"
                 and x["as_of_HISTORICAL_block_end"]==83636000)
                ["historical_SIGNED_EVENT_reconstructed_state"]==
                "CLOSED_EXACT_SELECTED_EPISODE",
            "D503_DID_NOT_ARRIVE_BEFORE_DDAC_EXIT")
    require(sum(int(x["signed_owner_native_net_wei"]) for x in rounds if x["key"].startswith("239E_"))==
            7315133865250263 and
            len([x for x in output_rounds if x["owner_net_sign"]=="POSITIVE"])==3 and
            len([x for x in output_rounds if x["owner_net_sign"]=="NEGATIVE"])==2,
            "CURATED_POSITIVE_NEGATIVE_NOT_WIN_RATE")
    return {
      "schema":"BSC_P4B_2026_FIVE_SIGNED_OWNER_EPISODES_EVENT_SOURCED_SIGNAL_LIFECYCLE_NOT_LIVE",
      "source_pins":{k:v[1] for k,v in FILES.items()},
      "scope":{"original_frozen_wallets":23,"original_exact_CAs":19,"original_possible_cells":437,
               "selected_research_episodes":5,"selected_owners":3,"selected_markets":2,
               "selected_positive_native_owner_episodes":3,
               "selected_negative_native_owner_episodes":2,
               "independent_public_eligible_signal_opportunities":0,
               "return_winrate_representative_of_437":False},
      "rounds":output_rounds,"historical_checkpoints":checkpoint_outputs,
      "original_DDAC_late_external_buyer":{
          "owner_selected_full_exit_block":83635800,
          "independent_D503_first_signed_buy_block":83636000,
          "selected_old_buy_signal_already_closed":True,
          "could_prove_D503_copied_DDAC":False},
      "original_239E_same_token_rounds_net_wei":"7315133865250263",
      "policy_candidate":"EXACT_SIGNED_EXIT_INVALIDATES_PRIOR_SELECTED_BUY_EPISODE; FURTHER_BUY_IS_NEW_EPISODE; PARTIAL_EXIT_REMAINS_NONZERO",
      "method":"HISTORICAL_SOURCED_SIGNER_EVENTS_ONLY_NO_ARBITRARY_BLOCK_RPC_RECONCILIATION",
      "limits":["As-of block end selected signer-event reconstruction is not current or complete arbitrary-block onchain balance.",
                "Repeated buys within same open episode are not independent signal successes.",
                "Selected 5 rounds are intentionally research-chosen, not random or statistical winrate.",
                "No observed delivery time to trader; 1/5/15-minute follower price, fill, gas and PnL unresolved."],
      "PUBLIC_EXECUTABLE_U":"UNRESOLVED","P4_B":"PARTIAL","P5":"BLOCKED","PRODUCTION":"NO_GO"
    }

if __name__=="__main__":
    print(json.dumps(build(load()),ensure_ascii=False,indent=2,sort_keys=True))
