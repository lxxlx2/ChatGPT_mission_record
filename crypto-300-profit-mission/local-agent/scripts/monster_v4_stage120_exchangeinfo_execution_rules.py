#!/usr/bin/env python3
"""Stage120 USD-M AS-OF exchangeInfo contract filters + price/depth preflight.

Pure offline research. Real snapshot must come from original Stage97 one-shot
authorised capture, verified by Stage116. No current API fetch, no orders,
no inferred cryptocurrency asset/contract multiplier and NO live PnL.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime,timezone,timedelta
from decimal import Decimal, InvalidOperation, ROUND_DOWN
import json
from pathlib import Path

try:
    import monster_v4_stage116_forward_population_score as source
    import monster_v4_stage90_d2_execution_proof as d2
    import monster_v4_stage97_one_shot_usdm_capture as cap
except ImportError:
    from scripts import monster_v4_stage116_forward_population_score as source
    from scripts import monster_v4_stage90_d2_execution_proof as d2
    from scripts import monster_v4_stage97_one_shot_usdm_capture as cap

SCHEMA="MONSTER_STAGE120_BINANCE_USDM_ASOF_CONTRACT_TRADE_FILTER_V1"
DOC_URL="https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data"
FILTER_KEYS=("LOT_SIZE","MARKET_LOT_SIZE","PRICE_FILTER","MIN_NOTIONAL","NOTIONAL")
DAY=86_400_000
MAX_MARKET_DELAY=d2.MAX_ASOF_LAG_MS


def number(value,label):
    if isinstance(value,bool) or value is None:
        raise ValueError("STAGE120_MISSING_NUMERIC_"+label)
    try:
        n=Decimal(str(value))
    except (InvalidOperation,ValueError):
        raise ValueError("STAGE120_INVALID_NUMERIC_"+label) from None
    if not n.is_finite():
        raise ValueError("STAGE120_NONFINITE_NUMERIC_"+label)
    return n


def bounds(f,low,high,step):
    mn=number(f[low],low)
    mx=number(f[high],high)
    st=number(f[step],step)
    if not (mn>=0 and mx>=0 and mn<=mx and st>=0):
        raise ValueError("STAGE120_BAD_EXCHANGEINFO_QUANTITY_BOUNDS")
    return {"min":str(mn),"max":str(mx),"step":str(st),
            "disabled_limit_or_step":mn==0 or mx==0 or st==0}


def parse_filters(meta):
    source_filters=meta.get("filters")
    if not isinstance(source_filters,list):
        return {"status":"FILTERS_UNKNOWN","reasons":["NO_ASOF_FILTERS"],
                "rules":{}}
    raw={}
    reasons=[]
    for item in source_filters:
        if not isinstance(item,dict) or not isinstance(item.get("filterType"),str):
            reasons.append("MALFORMED_EXCHANGEINFO_FILTER")
            continue
        kind=item["filterType"]
        if kind in raw:
            reasons.append("DUPLICATE_FILTER_"+kind)
        else:
            raw[kind]=item
    rules={}
    for kind in ("LOT_SIZE","MARKET_LOT_SIZE"):
        v=raw.get(kind)
        if v is None:
            reasons.append("MISSING_"+kind)
            continue
        try:
            rules[kind]=bounds(v,"minQty","maxQty","stepSize")
            if rules[kind]["disabled_limit_or_step"]:
                reasons.append("DISABLED_OR_ZERO_"+kind)
        except (ValueError,KeyError,TypeError):
            reasons.append("MALFORMED_"+kind)
    f=raw.get("PRICE_FILTER")
    if f is None:
        reasons.append("MISSING_PRICE_FILTER")
    else:
        try:
            rules["PRICE_FILTER"]=bounds(f,"minPrice","maxPrice","tickSize")
            if rules["PRICE_FILTER"]["disabled_limit_or_step"]:
                reasons.append("DISABLED_OR_ZERO_PRICE_FILTER")
        except (ValueError,KeyError,TypeError):
            reasons.append("MALFORMED_PRICE_FILTER")
    sources=[]
    for k in ("MIN_NOTIONAL","NOTIONAL"):
        if k not in raw:
            continue
        sources.append(k)
        f=raw[k]
        try:
            low=number(f["notional"] if k=="MIN_NOTIONAL" else f["minNotional"],k)
            if low<=0:raise ValueError("STAGE120_MIN_NOTIONAL_DISABLED")
            result={"minimum_quote_notional":str(low)}
            if k=="NOTIONAL":
                upper=number(f["maxNotional"],"maxNotional")
                if upper<=0 or upper<low:raise ValueError("STAGE120_INVALID_MAX_NOTIONAL")
                result["maximum_quote_notional"]=str(upper)
            rules[k]=result
        except (ValueError,KeyError,TypeError):
            reasons.append("MALFORMED_OR_DISABLED_"+k)
    if not sources:
        reasons.append("NO_MIN_NOTIONAL_RULE")
    if len(sources)>1:
        reasons.append("DUAL_NOTIONAL_CONTRACT_NEEDS_RECONCILIATION")
    return {"status":"COMPLETE_ASOF_FILTER_METADATA_NOT_EXECUTION" if not reasons
                    else "TRADE_RULES_PARTIAL_OR_INVALID",
            "reasons":sorted(set(reasons)),
            "rules":rules,
            "filter_names_all":sorted(raw)}


def catalog(snapshot,window):
    universe=source.audited_capture(snapshot,window)
    packet=snapshot["raw_market_packet"]
    data=json.loads(packet["raw_exchangeInfo_json"])
    by={}
    counters=Counter()
    for meta in data["symbols"]:
        name=meta["symbol"]
        if name in by:raise ValueError("STAGE120_DUPLICATE_SOURCE_SYMBOL")
        filt=parse_filters(meta)
        eligible=(meta["status"]=="TRADING"
                  and meta["contractType"]=="PERPETUAL"
                  and meta["quoteAsset"]=="USDT"
                  and (meta.get("onboardDate") is None
                       or meta["onboardDate"]<=universe["capture_ms"]))
        counts={
            "contract_status":meta["status"],
            "contract_type":meta["contractType"],
            "quote_asset":meta["quoteAsset"],
        }
        for v in counts:
            counters[v+":"+str(counts[v])]+=1
        counters["all_exchange_symbols"]+=1
        counters["raw_futures_candidates"]+=int(eligible)
        counters["raw_perpetual_filter_complete"]+=int(eligible and
                        filt["status"]=="COMPLETE_ASOF_FILTER_METADATA_NOT_EXECUTION")
        by[name]={
            "schema":SCHEMA,
            "venue":"BINANCE_USDM",
            "symbol":name,
            "snapshot_window":window,
            "exchangeInfo_original_raw_sha256":universe["raw_sha256"],
            "snapshot_capture_ms":universe["capture_ms"],
            "status_at_snapshot":meta["status"],
            "contract_type_at_snapshot":meta["contractType"],
            "base_asset_text":meta["baseAsset"],
            "pair_text":meta.get("pair"),
            "quote_asset_text":meta["quoteAsset"],
            "underlying_type_text":meta.get("underlyingType"),
            "underlying_subtype_text":meta.get("underlyingSubType"),
            "onboard_ms":meta.get("onboardDate"),
            "asof_original_raw_USDM_candidate":eligible,
            "filter_rules_at_snapshot":filt,
            "crypto_underlying_issuer_positive_proof":"NOT_ESTABLISHED",
            "multiplier_asset_mapping_proof":"NOT_ESTABLISHED",
            "at_later_signal_time_TRADING_proof":"NOT_ESTABLISHED",
            "actual_order_execution":"NOT_OBSERVED",
            "real_net_PNL":"UNKNOWN",
            "no_buy_or_local_deploy":True,
        }
    expected={r["symbol"]:r["candidate_for_raw_USDM_attempt"]
              for r in universe["rows"]}
    if len(expected)!=len(by) or any(name not in by or
       by[name]["asof_original_raw_USDM_candidate"]!=flag
       for name,flag in expected.items()):
        raise ValueError("STAGE120_ORIGINAL_STAGE105_ASOF_UNIVERSE_DRIFT")
    if counters["all_exchange_symbols"]!=universe["population_all_exchange_symbols"]:
        raise ValueError("STAGE120_EXCHANGEINFO_POPULATION_COUNT_DRIFT")
    return {
        "schema":SCHEMA,
        "window":window,
        "raw_market_SHA":universe["raw_sha256"],
        "capture_ms":universe["capture_ms"],
        "source_authenticity":
            "STAGE97_RECORDED_BINANCE_TIME_AND_HTTP_BODY_PARITY",
        "counters":dict(sorted(counters.items())),
        "per_symbol":by,
        "G0_true_crypto_classification":"NOT_ESTABLISHED",
        "G4_actual_executable_profit":"UNKNOWN",
        "model_rejected_Stage118":"REJECTED",
        "Monster_deployment":"NO_GO",
    }


def at_signal(symbol_meta,observed_ms):
    if not isinstance(observed_ms,int) or isinstance(observed_ms,bool):
        raise ValueError("STAGE120_BAD_SIGNAL_TIME")
    snap=symbol_meta["snapshot_capture_ms"]
    out={
        "schema":SCHEMA,"venue":symbol_meta["venue"],
        "symbol":symbol_meta["symbol"],
        "observed_ms":observed_ms,
        "snapshot_capture_ms":snap,
        "snapshot_SHA":symbol_meta["exchangeInfo_original_raw_sha256"],
        "metadata_rule_status":symbol_meta["filter_rules_at_snapshot"]["status"],
        "rule_missing_reasons":symbol_meta["filter_rules_at_snapshot"]["reasons"],
        "candidate_asof_snapshot":symbol_meta["asof_original_raw_USDM_candidate"],
        "source_crypto_identity":"UNVERIFIED",
        "multiplier_mapping":"UNVERIFIED",
        "real_fill":"NOT_OBSERVED",
        "actual_net":"UNKNOWN",
    }
    if observed_ms < snap:
        out["venue_status_at_signal"]="INVALID_SIGNAL_BEFORE_SNAPSHOT"
    elif observed_ms == snap:
        out["venue_status_at_signal"]="SNAPSHOT_TIME_ONLY_NO_INDEPENDENT_CRYPTO_ID"
    else:
        out["venue_status_at_signal"]="UNKNOWN_FROZEN_PREWINDOW_SNAPSHOT_NOT_LATER_TRADING_PROOF"
    return out


def market_preflight(symbol_meta,*,book=None,notional_quote=None,observed_ms=None):
    """Optional quote test; cannot be an executable trade without real auth.

    A Stage90-compatible USD-M raw L2 snapshot is a *price-only* display,
    not independently certified market depth provenance nor a fill.
    """
    result={
        "schema":SCHEMA,"symbol":symbol_meta["symbol"],
        "source_rule_status":symbol_meta["filter_rules_at_snapshot"]["status"],
        "notional_quote_explicit":str(notional_quote) if notional_quote is not None else None,
        "status":"NOTIONAL_UNKNOWN" if notional_quote is None else "NOT_SCORABLE",
        "actual_fill":"NOT_OBSERVED",
        "net_executable_profit":"UNKNOWN",
        "crypto_identity":"UNVERIFIED",
        "contract_mapping":"UNVERIFIED",
        "live_buy":"NOT_AUTHORIZED",
    }
    if not symbol_meta["asof_original_raw_USDM_candidate"]:
        result["status"]="NOT_ASOF_USDM_CANDIDATE"
        return result
    if symbol_meta["filter_rules_at_snapshot"]["status"]!="COMPLETE_ASOF_FILTER_METADATA_NOT_EXECUTION":
        result["status"]="FILTERS_UNKNOWN"
        return result
    if notional_quote is None:return result
    amount=number(notional_quote,"notional")
    if amount<=0:raise ValueError("STAGE120_EXPLICIT_QUOTE_MUST_BE_POSITIVE")
    rules=symbol_meta["filter_rules_at_snapshot"]["rules"]
    f=rules["MIN_NOTIONAL"] if "MIN_NOTIONAL" in rules else rules["NOTIONAL"]
    mn=number(f["minimum_quote_notional"],"min_quote")
    if amount<mn:
        result["status"]="BELOW_MIN_NOTIONAL"
        return result
    if "maximum_quote_notional" in f and amount>number(f["maximum_quote_notional"],"max_quote"):
        result["status"]="ABOVE_MAX_NOTIONAL"
        return result
    if book is None:
        result["status"]="BOOK_UNKNOWN"
        return result
    if (not isinstance(book,dict)
        or book.get("symbol")!=symbol_meta["symbol"]
        or book.get("venue")!="BINANCE_USDM"
        or book.get("source_url")!=d2.SOURCE_URLS["BINANCE_USDM"]
        or not d2.verified_raw_book(book,"BINANCE_USDM")):
        result["status"]="BOOK_INVALID"
        return result
    if observed_ms is None or not isinstance(observed_ms,int) or isinstance(observed_ms,bool):
        result["status"]="SIGNAL_TIME_MISSING"
        return result
    if not (observed_ms<=book["event_ms"]<=book["capture_ms"]<=observed_ms+MAX_MARKET_DELAY):
        result["status"]="BOOK_STALE_OR_LATE"
        return result
    try:
        bids=d2.levels(book["bids"],True)
        asks=d2.levels(book["asks"],False)
    except (ValueError,TypeError):
        result["status"]="BOOK_LEVELS_INVALID"
        return result
    if bids[0][0]>=asks[0][0]:
        result["status"]="BOOK_CROSSED"
        return result
    wanted=d2.buy_with_quote(asks,amount)
    if wanted is None:
        result["status"]="ASK_DEPTH_INSUFFICIENT"
        return result
    desired_qty,_=wanted
    lot=rules["MARKET_LOT_SIZE"]
    step=number(lot["step"],"market_step")
    min_qty=number(lot["min"],"market_min")
    max_qty=number(lot["max"],"market_max")
    if step<=0 or min_qty<=0 or max_qty<min_qty:
        result["status"]="MARKET_SIZE_RULE_UNKNOWN"
        return result
    qty=(desired_qty/step).to_integral_value(rounding=ROUND_DOWN)*step
    if not min_qty<=qty<=max_qty:
        result["status"]="QUANTITY_OUTSIDE_MARKET_LOT_SIZE"
        return result
    need=qty
    actual_quote=Decimal(0)
    for px,available in asks:
        take=min(need,available)
        actual_quote+=px*take
        need-=take
        if need==0:break
    if need>0:
        result["status"]="ASK_DEPTH_INSUFFICIENT"
        return result
    if actual_quote<mn:
        result["status"]="ROUNDED_QUOTE_BELOW_MIN_NOTIONAL"
        return result
    gross_bid=d2.sell_base(bids,qty)
    if gross_bid is None:
        result["status"]="BID_DEPTH_INSUFFICIENT"
        return result
    received,_=gross_bid
    result.update({
        "status":"SNAPSHOT_GROSS_SPREAD_DEPTH_ONLY_NOT_EXECUTABLE",
        "market_base_qty_rounded_step":str(qty),
        "intended_quote_max":str(amount),
        "simulated_buy_quote_excluding_fees":str(actual_quote),
        "same_book_simulated_sell_quote_excluding_fees":str(received),
        "simulated_immediate_roundtrip_friction_quote_excluding_fees":
            str(actual_quote-received),
        "market_lot_step":str(step),
        "snapshot_is_not_separately_authenticated_or_a_fill":True,
        "fee_and_future_exit":"UNKNOWN",
    })
    return result


def synthetic_snapshot(window):
    start=source.scope.verify_window(window)
    t=start-2*60_000
    filters=[
        {"filterType":"LOT_SIZE","minQty":"0.01","maxQty":"1000","stepSize":"0.01"},
        {"filterType":"MARKET_LOT_SIZE","minQty":"0.01","maxQty":"1000","stepSize":"0.01"},
        {"filterType":"PRICE_FILTER","minPrice":"0.01","maxPrice":"10000","tickSize":"0.01"},
        {"filterType":"MIN_NOTIONAL","notional":"5.0"}
    ]
    def coin(name,status="TRADING",contract="PERPETUAL",quote="USDT",fil=None):
        return {"symbol":name,"status":status,"contractType":contract,
                "quoteAsset":quote,"baseAsset":name.removesuffix("USDT"),
                "underlyingType":"COIN","onboardDate":start-DAY,
                "filters":filters if fil is None else fil}
    market={"serverTime":start-DAY,"symbols":[
        coin("TESTUSDT"),coin("1000DOGEUSDT"),coin("AAPLBUSDT"),
        coin("HALTUSDT",status="BREAK"),
        coin("QUARTERUSDT",contract="CURRENT_QUARTER"),
        coin("OTHERBUSD",quote="BUSD"),
        coin("MISSINGUSDT",fil=[filters[0]])]}
    first=cap.fixture(cap.TIME_URL,{"serverTime":t+100},t,t+200)
    exch=cap.fixture(cap.EXCHANGE_URL,market,t+200,t+400)
    last=cap.fixture(cap.TIME_URL,{"serverTime":t+500},t+400,t+600)
    return cap.verify_time_proof(first,last,exch,window)


def selftest():
    import copy
    w=source.WINDOWS[0]
    s=synthetic_snapshot(w)
    items=catalog(s,w)
    assert items["counters"]["all_exchange_symbols"]==7
    assert items["counters"]["raw_futures_candidates"]==4
    assert items["counters"]["raw_perpetual_filter_complete"]==3
    tested=items["per_symbol"]["TESTUSDT"]
    mult=items["per_symbol"]["1000DOGEUSDT"]
    assert mult["multiplier_asset_mapping_proof"]=="NOT_ESTABLISHED"
    assert items["per_symbol"]["AAPLBUSDT"]["crypto_underlying_issuer_positive_proof"]=="NOT_ESTABLISHED"
    assert items["per_symbol"]["MISSINGUSDT"]["filter_rules_at_snapshot"]["status"]=="TRADE_RULES_PARTIAL_OR_INVALID"
    assert items["per_symbol"]["HALTUSDT"]["asof_original_raw_USDM_candidate"] is False
    assert market_preflight(tested)["status"]=="NOTIONAL_UNKNOWN"
    assert market_preflight(tested,notional_quote="3")["status"]=="BELOW_MIN_NOTIONAL"
    assert market_preflight(tested,notional_quote="100")["status"]=="BOOK_UNKNOWN"
    assert at_signal(tested,tested["snapshot_capture_ms"]+60000)[
        "venue_status_at_signal"]=="UNKNOWN_FROZEN_PREWINDOW_SNAPSHOT_NOT_LATER_TRADING_PROOF"
    ev=source.scope.verify_window(w)+3*60000
    fixture=d2.synthetic_fixture()[1]
    b=copy.deepcopy(fixture["book"])
    b["symbol"]="TESTUSDT"
    b["event_ms"]=ev+500
    b["capture_ms"]=ev+1000
    d2.bind_fixture_raw({"book":b})
    outcome=market_preflight(tested,notional_quote="100",
                             book=b,observed_ms=ev)
    assert outcome["status"]=="SNAPSHOT_GROSS_SPREAD_DEPTH_ONLY_NOT_EXECUTABLE"
    assert outcome["net_executable_profit"]=="UNKNOWN"
    assert outcome["market_base_qty_rounded_step"]=="0.99"
    deep=copy.deepcopy(b)
    deep["asks"]=[["101","0.01"]]
    d2.bind_fixture_raw({"book":deep})
    assert market_preflight(tested,notional_quote="100",
           book=deep,observed_ms=ev)["status"]=="ASK_DEPTH_INSUFFICIENT"
    compromised=copy.deepcopy(s)
    compromised["raw_market_packet"]["raw_sha256"]="f"*64
    try:catalog(compromised,w)
    except ValueError:pass
    else:raise AssertionError("STAGE120_ACCEPTED_TAMPERED_BINANCE_SOURCE")
    duplicate=parse_filters({"filters":[
        {"filterType":"LOT_SIZE","stepSize":"1","minQty":"1","maxQty":"10"},
        {"filterType":"LOT_SIZE","stepSize":"1","minQty":"1","maxQty":"10"}]})
    assert "DUPLICATE_FILTER_LOT_SIZE" in duplicate["reasons"]
    assert duplicate["status"]!="COMPLETE_ASOF_FILTER_METADATA_NOT_EXECUTION"
    print("STAGE120_FROZEN_EXCHANGEINFO_ALL_SYMBOLS_RULES_LOT_ROUNDING_NO_DEFAULT_AMOUNT_NO_FAKE_G0_TEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--snapshot",type=Path)
    p.add_argument("--window",choices=list(source.WINDOWS))
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:return selftest()
    if None in (a.snapshot,a.window,a.out):
        p.error("--snapshot --window --out required, no network or live source capture")
    data=json.loads(a.snapshot.read_text())
    result=catalog(data,a.window)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("STAGE120_ORIGINAL_EXCHANGEINFO_FULL_SCOPE "+
          json.dumps({k:v for k,v in result.items() if k!="per_symbol"},sort_keys=True))


if __name__=="__main__":
    main()
