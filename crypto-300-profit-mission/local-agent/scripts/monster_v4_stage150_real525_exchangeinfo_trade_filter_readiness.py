#!/usr/bin/env python3
"""Stage150 saved REAL 525 as-of exchangeInfo filters; no real BUY or G4 scoring.

Stage148 verifies raw Stage133 roster + all Stage140 BBO receipt integrity;
Stage120 parses rules. This module changes neither model, nor data/clock.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path

import monster_v4_stage120_exchangeinfo_execution_rules as stage120
import monster_v4_stage147_saved_real_bbo_execution_readiness as stage147

SCHEMA = "MONSTER_STAGE150_REAL_525_ASOF_EXCHANGEINFO_FILTER_READINESS_V1"
RAW_PACKET = "stage133_original_three_HTTP_T0.json"


def percentile_decimal(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    return str(ordered[int((len(ordered)-1)*fraction)])


def audit(root=stage147.SOURCE_DIR):
    root = Path(root)
    verified = stage147.audit(root)
    if verified["counts"]["original_venue_attempts"] != 525:
        raise ValueError("STAGE150_NOT_ORIGINAL_VALIDATED_525")
    packet = json.loads((root/RAW_PACKET).read_text(encoding="utf-8"))
    exchange = packet["raw_http_records"]["official_exchange_info"]
    original = json.loads(exchange["raw"])
    if not isinstance(original.get("symbols"), list):
        raise ValueError("STAGE150_MISSING_ORIGINAL_EXCHANGEINFO_SYMBOLS")
    by = {}
    for row in original["symbols"]:
        symbol = row.get("symbol")
        if not isinstance(symbol,str) or symbol in by:
            raise ValueError("STAGE150_DUPLICATE_OR_INVALID_ORIGINAL_SYMBOL")
        by[symbol] = row
    counters, reasons = Counter(), Counter()
    records, minimums, market_steps, lot_steps = [], [], [], []
    for old in verified["all_market_population_rows"]:
        symbol = old["symbol_exact"]
        meta = by.get(symbol)
        if meta is None:
            raise ValueError("STAGE150_EXCHANGEINFO_ORIGINAL_MEMBER_MISSING")
        # Source population rows are fully matched to original raw by Stage148
        # before processing. In particular exact original quote/type/onboard
        # cannot be swapped in derivative rows by downstream consumers.
        if (meta.get("status")!="TRADING"
                or meta.get("contractType")!="PERPETUAL"
                or meta.get("quoteAsset")!="USDT"
                or meta.get("baseAsset") is None
                or old["asof_instrument_scope"] not in (
                    "OFFICIAL_COIN_TYPED_ISSUER_UNVERIFIED",
                    "OFFICIAL_NOT_COIN_TYPED_AT_T0")):
            raise ValueError("STAGE150_NOT_ORIGINAL_USDT_PERPETUAL_OR_CATEGORY")
        rules=stage120.parse_filters(meta)
        if rules["status"] not in (
                "COMPLETE_ASOF_FILTER_METADATA_NOT_EXECUTION",
                "TRADE_RULES_PARTIAL_OR_INVALID", "FILTERS_UNKNOWN"):
            raise ValueError("STAGE150_INVALID_STAGE120_FILTER_STATUS")
        counters["all_original_usdm_venue_rows"]+=1
        counters["filter_"+rules["status"]]+=1
        counters["underlying_type_"+str(meta.get("underlyingType","UNKNOWN"))]+=1
        if meta.get("underlyingType")=="COIN":
            counters["COIN_ISSUER_NOT_PROVEN"]+=1
        else:
            counters["INDEX_OR_OTHER_NOT_ELIGIBLE_FOR_CRYPTO_G1"]+=1
        sub = meta.get("underlyingSubType")
        if isinstance(sub,list) and all(isinstance(x,str) for x in sub):
            crypto_claim = "Crypto" in sub
            meme_claim = "Meme" in sub
        else:
            crypto_claim = meme_claim = False
        counters["exchange_subtype_says_Crypto"]+=int(crypto_claim)
        counters["exchange_subtype_says_Meme"]+=int(meme_claim)
        base=meta["baseAsset"]
        prefix=base.startswith(("1000","1000000")) if isinstance(base,str) else False
        counters["base_text_multiplier_like_prefix_not_verified"]+=int(prefix)
        for reason in rules["reasons"]:
            reasons[reason]+=1
        f=rules["rules"]
        notional=(f.get("MIN_NOTIONAL") or f.get("NOTIONAL"))
        minq=notional.get("minimum_quote_notional") if notional else None
        market=f.get("MARKET_LOT_SIZE")
        lot=f.get("LOT_SIZE")
        if minq is not None: minimums.append(Decimal(minq))
        if market and market.get("step") is not None:
            market_steps.append(Decimal(market["step"]))
        if lot and lot.get("step") is not None:
            lot_steps.append(Decimal(lot["step"]))
        records.append({
            "symbol_exact":symbol,
            "base_asset_text":base,
            "quote_asset_text":meta["quoteAsset"],
            "margin_asset_text":meta.get("marginAsset"),
            "underlying_type_exchange_claim":meta.get("underlyingType"),
            "underlying_subtype_exchange_claim":sub,
            "exchange_declares_Crypto_subtype":crypto_claim,
            "exchange_declares_Meme_subtype":meme_claim,
            "base_text_looks_scaled_mapping_not_issuer_evidence":prefix,
            "filter_status":rules["status"],
            "filter_missing_or_invalid_reasons":rules["reasons"],
            "filter_names_original":rules.get("filter_names_all",[]),
            "MARKET_LOT_SIZE":market,
            "LOT_SIZE":lot,
            "PRICE_FILTER":f.get("PRICE_FILTER"),
            "notional_rule":notional,
            "asof_original_quote_source_SHA":verified["original_T0_exchangeInfo_SHA256"],
            "original_exchange_serverTime_may_be_stale":True,
            "exchange_subtype_issuer_positive_proof":False,
            "contract_multiplier_independently_proven":False,
            "quantityPrecision_is_not_market_step":True,
            "quantityPrecision_declaration":meta.get("quantityPrecision"),
            "market_rule_valid_at_later_D0_or_D1":"UNVERIFIED",
            "actual_entry_L2":"MISSING",
            "later_exit_L2":"MISSING",
            "actual_fill":"NOT_OBSERVED",
            "net_executable_profit":"UNKNOWN",
            "G4_verified_executable_case":False,
        })
    if len(records)!=525 or counters["COIN_ISSUER_NOT_PROVEN"]!=523 or counters["INDEX_OR_OTHER_NOT_ELIGIBLE_FOR_CRYPTO_G1"]!=2 or sum(
        n for k,n in counters.items() if k.startswith("filter_"))!=525:
        raise ValueError("STAGE150_ORIGINAL_FULL_POPULATION_NOT_CONSERVED")
    return {
        "schema":SCHEMA,
        "source_saved_raw_original_exchangeInfo_SHA":verified["original_T0_exchangeInfo_SHA256"],
        "source_saved_capture_utc":verified["original_saved_capture_utc"],
        "source_www_mirror_identity_and_freshness_attested":False,
        "full_original_market_population":records,
        "original_source_venue_counts":dict(sorted(counters.items())),
        "stage120_filter_invalid_reason_counts":dict(sorted(reasons.items())),
        "historical_filter_descriptive_only":{
            "minimum_quote_rule_present":len(minimums),
            "minimum_quote_rule_P50":percentile_decimal(minimums,.50),
            "minimum_quote_rule_P90":percentile_decimal(minimums,.90),
            "market_quantity_step_present":len(market_steps),
            "market_quantity_step_P50":percentile_decimal(market_steps,.50),
            "lot_quantity_step_present":len(lot_steps),
            "lot_quantity_step_P50":percentile_decimal(lot_steps,.50),
        },
        "frozen_original_stage120_parser_reused":True,
        "frozen_stage147_real_raw_source_binding_reused":True,
        "no_default_or_implicit_quote_order_size":True,
        "contract_units_and_issuer_independently_unverified":True,
        "not_live_signal_time_trade_rules":True,
        "not_a_trade_or_strategy_recommendation":True,
        "complete_execution_L2_time_entry_exit":"MISSING",
        "G0":"PARTIAL","G1":"NOT_SCORABLE","G2_G3":"NOT_PASSED",
        "G4":"UNKNOWN","G5_Stage148_code_review_only":"APPROVE_AT_41F58CD_SOURCE_ONLY",
        "G6":"NO_GO",
        "NO_MERGE_NO_DEPLOY_NO_GMAIL_NO_TRADE":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-root",type=Path,default=stage147.SOURCE_DIR)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=audit(args.source_root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "schema":result["schema"],
        "source_rows":len(result["full_original_market_population"]),
        "counts":result["original_source_venue_counts"],
        "filter_invalid_reason_counts":result["stage120_filter_invalid_reason_counts"],
        "filter_rule_measures":result["historical_filter_descriptive_only"],
        "G4":result["G4"],"out":str(args.out)},ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
