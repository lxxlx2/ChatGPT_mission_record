#!/usr/bin/env python3
"""Finite 2026 Flap post-signed-buy mathematical quote replay; never tradable-U signal."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = {
    "freeze": ("bsc-meme-address-model-v1-p4b-flap-major2-nplus1-roundtrip-math-precommit-2026-10-17.json",
               "57408d1a792235ce43eebcb10d7096c97e9b3aea"),
    "readback": ("bsc-meme-address-model-v1-p4b-flap-major2-nplus1-roundtrip-math-supplement-v2-2026-10-18.json",
                 "cc96297ace51a74efb8b800f0fd0bed385fcbce4"),
    "raw_v1": ("bsc-meme-address-model-v1-p4b-flap-major2-nplus1-roundtrip-math-readback-2026-10-17.json",
               "b7c618582b969c61772deb8a07dbd0e706a187e4"),
    "market": ("bsc-meme-address-model-v1-p4b-19ca-unified-early-market-buy-evidence-2026-10-14.json",
               "c42ad01e896f30262f89f7852f927fc84fb3ea18"),
    "first_signed": ("bsc-meme-address-model-v1-p4b-flap-major2-original-buys-and-quotes-2026-10-14.json",
                     "d69f2ddfade437a1d8b0fc49585eb4ca0f9268e9"),
    "prebuy_quotes": ("bsc-meme-address-model-v1-p4b-flap-major2-bidirectional-quotes-raw-2026-10-14.json",
                     "43fe6d36fbeeda43e07a2b65874c4292e5d91606"),
}

def check(ok, label):
    if not ok:
        raise ValueError("P4B_FLAP_POSTBUY_" + label)

def load(root=ROOT):
    docs = {}
    for key,(name,sha) in SOURCES.items():
        raw = (root/name).read_bytes()
        actual = hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        check(actual == sha, "SOURCE_BLOB_DRIFT_"+key)
        docs[key] = json.loads(raw)
    return docs

def calldata(selector, from_token, to_token, value):
    return (selector + from_token.lower()[2:].zfill(64) +
            to_token.lower()[2:].zfill(64) + format(value, "064x"))

def rawuint256(value):
    check(isinstance(value,str) and value.startswith("0x") and len(value) == 66,
          "INVALID_32BYTE_ETHCALL_RETURN")
    try:
        n = int(value,16)
    except ValueError as e:
        raise ValueError("P4B_FLAP_POSTBUY_INVALID_HEX_ETHCALL") from e
    check(n>0, "ZERO_MATH_QUOTE")
    return n

def build(docs):
    pre,read,market,original,old_quote = (docs[k] for k in
                                         ("freeze","readback","market","first_signed","prebuy_quotes"))
    check(read["source_precommit_blob_sha"] == SOURCES["freeze"][1] and
          pre["source_reviewed_baseline"] ==
          "dd3d529c99853b89f2be299235cdb499c2ad365f",
          "FREEZE_IDENTITY")
    check(pre["max_calls"] == 4 and read["read_count"] == 4 and
          read["complete_results"] == 4 and
          pre["contract"] == "0xe2ce6ab80874fa9fa2aae65d277dd6b8e65c9de0" and
          pre["selector"] == "0xfc847c2b",
          "SCOPE_OR_ABI_DRIFT")
    check(len(market["rows"]) == 19 and len(pre["cases"]) == 2 and len(read["rows"]) == 2
          and len(original["rows"]) == 2 and len(old_quote["rows"]) == 2,
          "TWO_PRECOMMITTED_MARKETS_ONLY")
    check([c["token"] for c in pre["cases"]] == ["牛来","MARSCOIN"],
          "CASE_ORDER")
    immutable_v1 = docs["raw_v1"]
    check(read["source_v1"] ==
          {"path":SOURCES["raw_v1"][0],"git_blob_sha":SOURCES["raw_v1"][1],
           "source_role":"IMMUTABLE_ORIGINAL_RPC_READBACK_SELECTED_FIELDS"} and
          read["supplement_provenance"] ==
          "POST_HOC_AUDIT_ENRICHMENT_NOT_NEW_RPC_QUERY" and
          read["supplement_confirms_provider_request_capture"] is False and
          read["request_evidence_grade"] == "SCRIPT_RECONSTRUCTED_NOT_PROVIDER_CAPTURED",
          "V1_V2_PROVENANCE_NOT_CAPTURED")
    check(read["schema"] ==
          "BSC_P4B_FLAP_2026_TWO_SIDED_QUOTE_NPLUS1_BLOCK_END_SUPPLEMENT_V2" and
          read["actual_provider_raw_transcript_archived"] is False and
          "look-ahead" in read["limits"][-1], "BLOCK_END_GRADE")
    check(read["method"].startswith("quoteExactInput fixed frozen") and
          "Original Alchemy V1 source readback" in read["source"] and
          "no provider transport capture" in read["source"],
          "READ_ONLY_MATH_ORIGIN")
    check(read["gates"] == {
          "global_public_executable_U":"UNRESOLVED",
          "actual_persisted_buy_and_sell":"UNRESOLVED",
          "capital_at_public_U":"UNRESOLVED","P5":"BLOCKED",
          "PRODUCTION":"NO_GO","restrictions":"NO_MERGE NO_DEPLOY NO_GMAIL NO_TRADE"},
          "PREMATURE_REALIZED_OR_PRODUCTION")
    mkt = {r["token"]:r for r in market["rows"]}
    fresh=[]
    for i,c in enumerate(pre["cases"]):
        x=read["rows"][i]
        o=original["rows"][i]
        old=old_quote["rows"][i]
        coin=c["token"]
        check(all(y["token"] == coin for y in (x,o,old,mkt[coin])) and
              mkt[coin]["exact_CA"] == c["CA"] == x["exact_CA"] == o["exact_CA"] == old["CA"],
              "TOKEN_CA_CORRESPONDENCE")
        check(c["quote_CA"] == x["quote_CA"] == o["actual_quote_CA"] == old["quote_CA"] ==
              mkt[coin]["observed_early_purchase_quote_CA"] and
              o["historical_quote_decimals"] == 18 and
              old["fixed_quote_in_raw"] == pre["amount_quote_in_raw"],
              "QUOTE_ASSET_AND_DECIMALS")
        check(c["witness_block_N"] == x["original_witness_block_N"] ==
              o["first_sampled_buy_block"] == old["first_observed_buy_block"] ==
              mkt[coin]["selected_early_buy_block"] and
              c["read_block_Nplus1"] == x["block"] == c["witness_block_N"] + 1,
              "POST_WITNESS_READ_BLOCK")
        check(o["original_first_purchase_event_match"] == "CONFIRMED" and
              c["source_original_signer"] == o["original_EOA_signer"] ==
              mkt[coin]["selected_early_buy_signer"] and
              c["buyer_is_in_original23"] is False and
              mkt[coin]["selected_signer_is_in_original_23"] is False and
              o["first_global_U"] == "UNRESOLVED",
              "EARLY_ACTUAL_SIGNED_OWNER_EVIDENCE")
        check((o["buy_tax_bps"],o["sell_tax_bps"]) == ((100,100) if i==0 else (300,300)) and
              old["quote_block"] == c["witness_block_N"]-1 and
              old["buy_read"]["status"] == "COMPLETE_QUOTE_ONLY",
              "EARLY_PREBUY_OR_TAX_SOURCE")
        check(x["source_contract"].lower() == pre["contract"].lower() and
              x["math_function"] == pre["function"],
              "PORTAL_IDENTITY")
        check(x["buy"]["rpc_status"] == "COMPLETE_32BYTE_VIEW_ONLY" and
              x["reverse"]["rpc_status"] == "COMPLETE_32BYTE_VIEW_ONLY" and
              x["caller"] == "NO_FROM_SET_VIEW" and
              x["signed_actual_buy"] is False and x["signed_actual_sell"] is False and
              x["hypothetical_purchase_did_change_chain_state"] is False and
              x["assumed_sufficient_real_spendable_quote"] is False and
              x["qualified_public_market_U"] == "UNRESOLVED" and
              x["gas_tax_slippage_historical_settlement"] == "UNRESOLVED" and
              x["public_observer_latency"] == "UNRESOLVED",
              "MATH_MISLABELLED_ACTUAL_TRADE")
        amount_in = int(pre["amount_quote_in_raw"])
        buy_out = rawuint256(x["buy"]["raw_return"])
        quote_out = rawuint256(x["reverse"]["raw_return"])
        check(x["buy"]["input_quote_raw"] == str(amount_in) and
              x["buy"]["decoded_token_raw"] == str(buy_out) and
              x["buy"]["rpc_calldata"] == calldata(pre["selector"],c["quote_CA"],c["CA"],amount_in),
              "BUY_ETHCALL_INPUT_OUTPUT")
        for leg in ("buy", "reverse"):
            req = x[leg]["request"]
            check(x[leg]["request_grade"] ==
                  "SCRIPT_RECONSTRUCTED_NOT_PROVIDER_CAPTURED",
                  "SCRIPT_RECONSTRUCTED_SELF_CONSISTENCY")
            check(req == {
                "network":"bnb-mainnet", "method":"eth_call",
                "to":pre["contract"], "data":x[leg]["rpc_calldata"],
                "blockTag":hex(c["witness_block_N"]+1),
                "from":None, "value":None},
                "SCRIPT_RECONSTRUCTED_SELF_CONSISTENCY")
        check("lookahead" in x["Nplus1_block_end_lookahead_caveat"] or
              "look-ahead" in x["Nplus1_block_end_lookahead_caveat"] or
              "intra-block" in x["Nplus1_block_end_lookahead_caveat"],
              "INTRABLOCK_LOOKAHEAD_CAVEAT_REQUIRED")
        check(x["reverse"]["input_token_raw"] == str(buy_out) and
              x["reverse"]["decoded_quote_raw"] == str(quote_out) and
              x["reverse"]["rpc_calldata"] == calldata(pre["selector"],c["CA"],c["quote_CA"],buy_out),
              "INVERSE_QUOTE_SAME_HISTORIC_STATE")
        check(quote_out < amount_in and
              x["static_two_read_difference_quote_raw"] == str(amount_in-quote_out) and
              x["static_two_read_loss_bps_times_1e4"] ==
              str((amount_in-quote_out)*100000000//amount_in),
              "MATH_PRICE_DIFFERENCE_DOES_NOT_PROVE_PROFIT")
        fresh.append({
            "token":coin,"exact_CA":c["CA"],"quote_CA":c["quote_CA"],
            "historical_read_block_Nplus1":x["block"],
            "buy_request_blockTag":x["buy"]["request"]["blockTag"],
            "reverse_request_blockTag":x["reverse"]["request"]["blockTag"],
            "actual_early_signed_buy_witness_N":c["witness_block_N"],
            "source_historical_buy_sell_tax_bps":[o["buy_tax_bps"],o["sell_tax_bps"]],
            "fixed_quote_input_raw":str(amount_in),
            "post_N_buy_math_token_output_raw":str(buy_out),
            "same_end_state_reverse_math_quote_raw":str(quote_out),
            "two_independent_static_quote_difference_raw":str(amount_in-quote_out),
            "quote_math_gap_bps_times_1e4":str((amount_in-quote_out)*100000000//amount_in),
            "actual_post_witness_follower_buy_then_sell": "UNRESOLVED",
            "historic_original_quote_to_BNB_or_USD_conversion":"UNRESOLVED",
            "actual_post_hypothetical_purchase_market_state":"NOT_SIMULATED",
            "public_first_buy_and_sell_executable_U":"UNRESOLVED",
            "P5_one_five_fifteen_minute_return":"UNRESOLVED"
        })
    check(len(immutable_v1["rows"]) == len(read["rows"]) == 2 and
          all(immutable_v1[k] == read[k] for k in
              ("source_precommit_blob_sha","source_reviewed_code_baseline",
               "network","method","read_count","complete_results","gates")),
          "IMMUTABLE_V1_SOURCE_DATA_DRIFT")
    for orig, enrich in zip(immutable_v1["rows"], read["rows"]):
        for key,value in orig.items():
            if key in ("buy","reverse"):
                check(all(enrich[key].get(k) == v for k,v in value.items()),
                      "IMMUTABLE_V1_QUOTE_FIELD_DRIFT")
            else:
                check(enrich.get(key) == value,
                      "IMMUTABLE_V1_SELECTED_FIELD_DRIFT")
    return {"schema":"BSC_P4B_FLAP_2026_NPLUS1_MATH_ONLY_TWO_ASSETS_REPLAY",
            "source_sha":{k:v[1] for k,v in SOURCES.items()},
            "summary":{"scoped_tokens":2,"quote_calls":4,
                       "isolated_bidirectional_math_quotes_2of2":2,
                       "persisted_hypothetical_follow_trade_fills":0,
                       "verified_public_executable_U":0,
                       "P4_B":"PARTIAL","P5":"BLOCKED","production":"NO_GO"},
            "rows":fresh}

if __name__ == "__main__":
    print(json.dumps(build(load()),ensure_ascii=False,indent=2,sort_keys=True))
