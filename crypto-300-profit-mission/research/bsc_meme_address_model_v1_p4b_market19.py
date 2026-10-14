#!/usr/bin/env python3
"""All 19 major CA entrance evidence; neither mint nor DEX quote proves wallet alpha."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4b-19ca-early-launch-origin-2026-10-14.json","847c83fb1e1c523ebebc152f6fddacdcf128a5b7"),("bsc-meme-address-model-v1-p4b-flap-major2-original-buys-and-quotes-2026-10-14.json","d69f2ddfade437a1d8b0fc49585eb4ca0f9268e9"),("bsc-meme-address-model-v1-p4b-dragon-ddac-real-pre-dex-buy-2026-10-14.json","f89362368ad47f1cde2d8475f9e7b8a688093f83"),("bsc-meme-address-model-v1-p4b-19ca-v2-001wbnb-router-math-quotes-2026-10-14.json","1f44ed58bab1dec1b4ccdc4cc449dde90d6131e7"),("bsc-meme-address-model-v1-p4b-23x19-early-opportunity-ledger-2026-10-14.json","f88ed9abfcb0f321ec31e98a029303aca48a8623"))
ZERO="0x"+"0"*40
def require(v,msg):
    if not v: raise ValueError(msg)
def git_sha(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def load(root=ROOT):
    result=[]
    for name,sha in PINS:
        raw=(root/name).read_bytes()
        require(git_sha(raw)==sha,"Source blob drift "+name)
        result.append(json.loads(raw))
    return result
def build(d):
    require(len(d)==5,"missing five source artifacts")
    early,flap,dragon,quotes,grid=d
    require(early["summary"]["exact_CAs"]==19
        and flap["summary"]["source_original_signed_purchases"]==2
        and dragon["summary"]["original_signed_DDAC_buys_in_this_fixed_sample"]==1
        and quotes["summary"]["reserve_formula_cross_checks_passed"]==19
        and grid["summary"]["wallets"]==23
        and grid["summary"]["implicit_wallet_CA_cells"]==437
        and grid["summary"]["one_source_proven_owner_signed_pre_dex_buy"]==1
        and all(z["summary"]["production"]=="NO_GO" for z in d),
        "Original cohort or evidence status changed")
    fm={x["exact_CA"]:x for x in flap["rows"]}
    require(len(fm)==2,"two exact Flap CAs required")
    dd=dragon["fact"]
    require(dd["buyer_EOA"].lower()==dd["TokenPurchase_account"].lower()
            and dd["realized_net_PnL"]=="UNRESOLVED" and dd["exact_CA"] not in fm,
            "DDAC original purchase evidence altered")
    roster={x["wallet"].lower() for x in grid["wallets"]}
    require(dd["buyer_EOA"].lower() in roster
            and all(x["original_EOA_signer"].lower() not in roster for x in flap["rows"]),
            "Original 23 wallet membership drift")
    out=[]
    require(len(early["rows"])==len(quotes["rows"])==len(grid["markets"])==19,"must keep 19")
    for i,(e,q,g) in enumerate(zip(early["rows"],quotes["rows"],grid["markets"])):
        require(e["index"]==q["index"]==g["i"]==i
                and e["exact_CA"]==q["exact_CA"]==g["ca"]
                and e["first_observed_erc20_transfer_block"]<e["first_scoped_dex_positive_block"]
                and q["router_matches_pair_reserves"] is True
                and q["historical_token_transfer_simulation"]=="NOT_PERFORMED",
                "Exact CA or origination block/DEX quote mismatch")
        f=fm.get(e["exact_CA"])
        a=dd if e["exact_CA"]==dd["exact_CA"] else None
        if f:
            require(f["original_first_purchase_event_match"]=="CONFIRMED"
                    and f["original_EOA_signer"].lower()==f["final_ERC20_recipient"].lower()
                    and f["received_target_raw"]==f["intermediate_hops"][-1]["raw_amount"]
                    and f["actual_quote_CA"]!=ZERO
                    and f["causal_profit"]=="UNRESOLVED",
                    "Flap original owner signer and token transfer unconfirmed")
        kind=("FOUR_MEME_SIGNED_EARLY_BUY" if a else
              "FLAP_SIGNED_EARLY_BUY" if f else
              "EARLY_ERC20_TRANSFER_ONLY_NO_SIGNED_BUY_AUDIT")
        signer=a["buyer_EOA"] if a else f["original_EOA_signer"] if f else None
        out.append({
          "index":i,"token":e["token"],"exact_CA":e["exact_CA"],
          "first_observed_ERC20_transfer_block":e["first_observed_erc20_transfer_block"],
          "first_scoped_Pancake_positive_liquidity_block":e["first_scoped_dex_positive_block"],
          "four_helper_pre_dex_status":e["pre_dex_helper_status"],
          "V2_WBNB_original_mathematical_buy_quote_complete":q["router_matches_pair_reserves"],
          "V2_WBNB_gross_quote_wei":q["quote_in_wei"],
          "V2_WBNB_spot_mid_gap_bps":q["spot_mid_vs_router_output_gap_bps"],
          "earlier_actual_signed_purchase_evidence":kind,
          "selected_early_buy_original_tx":a["buyer_original_tx"] if a else f["signed_tx_hash"] if f else None,
          "selected_early_buy_block":a["buyer_original_tx_block"] if a else f["first_sampled_buy_block"] if f else None,
          "selected_early_buy_signer":signer,
          "selected_signer_is_in_original_23":True if a else False if f else None,
          "observed_early_purchase_quote_CA":ZERO if a else f["actual_quote_CA"] if f else None,
          "observed_early_purchase_quote_label":"BNB_NATIVE" if a else f["quote_symbol_current_metadata"]+" (current metadata only)" if f else None,
          "observed_event_cost_in_original_quote_raw":a["TokenPurchase_cost_quote_wei"] if a else f["portal_event_quote_spent_raw"] if f else None,
          "observed_event_fee_in_original_quote_raw":a["TokenPurchase_protocol_fee_wei"] if a else f["portal_event_fee_raw"] if f else None,
          "launch_config_buy_tax_bps":f["buy_tax_bps"] if f else None,
          "launch_config_sell_tax_bps":f["sell_tax_bps"] if f else None,
          "evidenced_positive_historical_sale":"UNRESOLVED",
          "historical_signed_roundtrip_PnL":"UNRESOLVED",
          "actual_global_observer_market_U":"UNRESOLVED",
          "qualified_23_wallet_missed_profitable_U":"UNRESOLVED",
          "following_at_1_5_15min":"UNRESOLVED",
          "production":"NO_GO"
        })
    summary={
      "frozen_major_exact_CAs":19,
      "original_23_EOA_candidates":23,
      "full_wallet_CA_denominator":437,
      "source_original_signed_early_buy_market_witnesses":sum(x["selected_early_buy_signer"] is not None for x in out),
      "earlier_signed_buy_witnesses_within_frozen_23":sum(x["selected_signer_is_in_original_23"] is True for x in out),
      "earlier_signed_buy_witnesses_outside_frozen_23":sum(x["selected_signer_is_in_original_23"] is False for x in out),
      "remaining_major_CAs_not_yet_signed_early_buy_audited":sum(x["selected_early_buy_signer"] is None for x in out),
      "Four_meme_pre_dex_canonical_sources":early["summary"]["canonical_fourmeme_v2_at_pre_scoped_dex"],
      "Flap_early_original_real_buy_sources":len(flap["rows"]),
      "V2_historical_math_quotes_complete":quotes["summary"]["raw_historical_v2_router_buy_quotes_complete"],
      "global_actual_U_and_sell_capacity_fully_qualified":0,
      "actual_profit_ranks":0,"production":"NO_GO"
    }
    require((summary["source_original_signed_early_buy_market_witnesses"],
             summary["earlier_signed_buy_witnesses_within_frozen_23"],
             summary["earlier_signed_buy_witnesses_outside_frozen_23"],
             summary["remaining_major_CAs_not_yet_signed_early_buy_audited"])==(3,1,2,16),
            "Full 19 frozen early source denominator changed")
    return {
      "schema":"BSC_P4B_19CA_UNIFIED_PREDEX_ACTUAL_BUY_VENUE_WITNESS",
      "scope":"All 19 frozen major exact CAs and prior 23×19 candidate denominator. One DDAC actual Four.meme purchase and two original Flap buys from outside-frozen-23 owner-signers; remaining 16 are not source-audited for earliest signed buy. This is NOT global earliest trade U, confirmed successful later sell, cross-asset USD PnL, missed trade or follower alpha.",
      "source_manifest":[{"path":PREFIX+n,"git_blob_sha":sha} for n,sha in PINS],
      "summary":summary,"rows":out
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
