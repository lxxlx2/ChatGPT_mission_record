#!/usr/bin/env python3
"""Monster Stage75: all 95 original D0s without verified Spot USDT prior trades.

For each original first WATCH, check exactly four other same-base Binance Spot
quote pairs (USDC/FDUSD/BTC/BNB) at the immediately prior closed 1m.
Reuse Stage74 publisher-SHA ZIP parser; no market listing, CA, order book,
trade execution, future HIGH, automatic money amount or deployment claim.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import json
from pathlib import Path

try:
    import monster_v4_stage74_original196_spot_asof_prior_minute_SHA as spot
except ImportError:
    from scripts import monster_v4_stage74_original196_spot_asof_prior_minute_SHA as spot

ROOT=Path(__file__).resolve().parents[2]/"monster"
PREREG=ROOT/"MONSTER_STAGE75_PREREG_95_MISSING_ORIGINAL_D0_FOUR_SPOT_QUOTE_ARCHIVES_20261013.md"
OLD=ROOT/"evidence"/"monster_stage74_original196_exact_asof_spot_prior_trades_source_SHA.jsonl"
LOCK={
    PREREG.name:"696e5d041556e18c331d33ef3f9a8fe95ffbf433",
    OLD.name:"c9002d380d0b2db786e58461579b862e7afab054",
    "monster_v4_stage74_original196_spot_asof_prior_minute_SHA.py":
      "02aea897fa59598e28fb37d0c32cd718d590a816",
}
QUOTES=("USDC","FDUSD","BTC","BNB")
EXTRA=("SPOT_ARCHIVE_SAME_DAY_NO_PRIOR_1M_BAR",
       "SPOT_DAILY_ARCHIVE_404_UNVERIFIED",
       "SPOT_PRIOR_MINUTE_BAR_ZERO_TRADES",
       "SPOT_PRIOR_MINUTE_TRADES_VERIFIED")
SCHEMA="MONSTER_STAGE75_ORIGINAL95_FOUR_ALT_SPOT_QUOTE_TMINUS1_OFFICIAL_PUBLISHER_SHA_V1"
YES="SPOT_PRIOR_MINUTE_TRADES_VERIFIED"
OLD_NO="SPOT_PRIOR_MINUTE_TRADES_VERIFIED"


def frozen():
    for name,path in ((PREREG.name,PREREG),(OLD.name,OLD),
                      ("monster_v4_stage74_original196_spot_asof_prior_minute_SHA.py",
                       Path(spot.__file__))):
        if spot.blob(path)!=LOCK[name]:
            raise ValueError("STAGE75_FROZEN_UPSTREAM_SOURCE_CHANGED "+name)
    records=[json.loads(x) for x in OLD.read_text(encoding="utf-8").splitlines() if x]
    if len(records)!=196 or len({(x["date"],x["symbol"]) for x in records})!=196:
        raise ValueError("STAGE75_STAGE74_SOURCE_196_NOT_INTACT")
    selected=sorted((x for x in records if x["spot_historical_evidence_status"]!=YES),
                    key=lambda x:(x["date"],x["symbol"]))
    groups=collections.Counter(x["date"] for x in selected)
    if len(selected)!=95 or dict(groups)!={"2025-03-30":14,"2025-06-30":22,"2025-11-27":59}:
        raise ValueError("STAGE75_ORIGINAL95_IDENTITY_UNIVERSE_OR_COUNTS_CHANGED")
    for x in selected:
        if not x["symbol"].endswith("USDT") or x["spot_historical_evidence_status"] not in EXTRA:
            raise ValueError("STAGE75_NOT_A_FROZEN_ORIGINAL_NONUSDT_SPOT_MATCH")
        if x["spot_historical_evidence_status"]==YES:
            raise ValueError("STAGE75_ALREADY_VERIFIED_USDT_NOT_IN_SCOPE")
        if spot.utc_ms(x["original_usdm_first_D0_UTC"])%60000:
            raise ValueError("STAGE75_ORIGINAL_FIRST_D0_NOT_UTC_MINUTE")
    return selected


def review_one(row,lookup=spot.fetch_day):
    symbol=row["symbol"]
    base=symbol[:-4]
    if not base or symbol!=base+"USDT":
        raise ValueError("STAGE75_BAD_EXACT_ORIGINAL_FUTURES_BASE")
    at=row["original_usdm_first_D0_UTC"]
    all_quotes=[]
    for quote in QUOTES:
        pair=base+quote
        candidate={"date":row["date"],"symbol":pair,"original_D0_first_UTC":at}
        checked=spot.classify(candidate,fetcher=lookup)
        state=checked["spot_historical_evidence_status"]
        if state not in EXTRA or checked["spot_day_UTC"]!=at[:10]:
            raise ValueError("STAGE75_BAD_SPOT_QUOTE_CLOSED_1M_STATE")
        if checked["spot_exact_same_symbol"]!=pair:
            raise ValueError("STAGE75_DIFFERENT_BASE_OR_SPOT_SYMBOL")
        receipt=checked["spot_daily_source"]
        if state==YES and (
            not receipt["publisher_zip_sha256"] or
            not checked["spot_prior_1m_number_of_trades"]>0 or
            not spot.D(checked["spot_prior_1m_quote_volume_USDT"])>0
        ):
            raise ValueError("STAGE75_UNPROVEN_T_MINUS_ONE_MINUTE_TRADE")
        all_quotes.append({
            "spot_symbol":pair,
            "quote_asset":quote,
            "asof_spot_prior_minute_UTC":checked["spot_only_completed_one_minute_UTC"],
            "status":state,
            "prior_close_in_quote_asset_NOT_EXECUTABLE_FILL":
                checked["spot_prior_1m_close_NOT_EXACT_TRADE_FILL"],
            "prior_quote_volume_IN_NATIVE_QUOTE_UNITS":
                checked["spot_prior_1m_quote_volume_USDT"],
            "prior_minute_trade_count":checked["spot_prior_1m_number_of_trades"],
            "daily_publisher_sha256":receipt.get("publisher_zip_sha256"),
            "archive_path":receipt.get("archive_path"),
            "archive_observed_rows":receipt.get("number_of_actual_source_minutes"),
        })
    found=[x["quote_asset"] for x in all_quotes if x["status"]==YES]
    return {
        "original_window_date":row["date"],
        "original_futures_symbol":symbol,
        "original_futures_first_D0_UTC":at,
        "original_stage74_spot_USDT_status":row["spot_historical_evidence_status"],
        "alternative_spot_pairs":all_quotes,
        "any_alternative_quote_spot_prior_closed_minute_trades_verified":bool(found),
        "verified_alt_quote_assets":found,
        "exact_base_string_only_no_prefix_multiplier_CA_or_token_identity_mapping":True,
        "historical_orderbook_bid_ask_buyability_and_net_profit":"UNKNOWN",
        "historical_spot_listing_and_all_alpha_dex_venues":"UNKNOWN",
        "NO_USER_NOTIONAL_GMAIL_AUTOTRADE_DEPLOYMENT":True,
    }


def run(shard,workers,out,pilot=False):
    all_95=frozen()
    if pilot:
        names=(("2025-06-30","HUSDT"),
               ("2025-11-27","PIPPINUSDT"),
               ("2025-11-27","TANSSIUSDT"),
               ("2025-11-27","TRADOORUSDT"),
               ("2025-03-30","FARTCOINUSDT"),
               ("2025-06-30","1000000BOBUSDT"))
        lookup={(x["date"],x["symbol"]):x for x in all_95}
        batch=[lookup[key] for key in names]
    else:
        if shard not in range(5):
            raise ValueError("STAGE75_SHARD_MUST_BE_0_TO_4")
        batch=[x for i,x in enumerate(all_95) if i%5==shard]
        if len(batch)!=19:raise ValueError("STAGE75_NOT_EXACT19_PER_SHARD")
    result=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(review_one,row):row for row in batch}
        for job in concurrent.futures.as_completed(jobs):
            row=jobs[job]
            try:result.append(job.result())
            except Exception as err:
                errors.append({"symbol":row["symbol"],"date":row["date"],
                               "reason":type(err).__name__+":"+str(err)[:250]})
    if errors or len(result)!=len(batch):
        raise RuntimeError("STAGE75_OFFICIAL_SOURCE_OR_CAUSAL_AUDIT_FAIL "+json.dumps(errors[:12]))
    result.sort(key=lambda x:(x["original_window_date"],x["original_futures_symbol"]))
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STAGE75_FOUR_QUOTE_HISTORIC_SPOT_RESULT "+json.dumps({
        "pilot":pilot,"shard":shard,"original_d0_count":len(result),
        "checked_quote_symbol_event_pairs":len(result)*len(QUOTES),
        "any_quote_historic_trades":sum(x["any_alternative_quote_spot_prior_closed_minute_trades_verified"]
                                        for x in result),
        "trading_venues_by_quote_asset":{
            q:sum(q in x["verified_alt_quote_assets"] for x in result) for q in QUOTES}},
        sort_keys=True))
    return result


def aggregate(folder,out):
    source=frozen()
    canon={(x["date"],x["symbol"]):x for x in source}
    rows=[]
    for shard in range(5):
        p=folder/f"monster_stage75_original95_shard{shard}.json"
        group=json.loads(p.read_text(encoding="utf-8"))
        if len(group)!=19:raise ValueError("STAGE75_BAD_19_SHARD")
        rows+=group
    ids={(x["original_window_date"],x["original_futures_symbol"]):x for x in rows}
    if len(rows)!=95 or len(ids)!=95 or set(ids)!=set(canon):
        raise ValueError("STAGE75_LOST_OR_DUPLICATED_ORIGINAL95")
    for key,v in ids.items():
        old=canon[key]
        if v["original_futures_first_D0_UTC"]!=old["original_usdm_first_D0_UTC"] or (
            v["original_stage74_spot_USDT_status"]!=old["spot_historical_evidence_status"]
        ):
            raise ValueError("STAGE75_ORIGINAL_SOURCE_OR_D0_TIME_DRIFT")
        if [x["quote_asset"] for x in v["alternative_spot_pairs"]]!=list(QUOTES) or (
            [x["spot_symbol"] for x in v["alternative_spot_pairs"]] !=
            [v["original_futures_symbol"][:-4]+q for q in QUOTES]
        ):
            raise ValueError("STAGE75_NOT_ALL_FOUR_FROZEN_QUOTE_SPOT_PAIRS")
        if v["any_alternative_quote_spot_prior_closed_minute_trades_verified"] != bool(
            v["verified_alt_quote_assets"]
        ) or v["verified_alt_quote_assets"]!=[x["quote_asset"] for x in v["alternative_spot_pairs"] if x["status"]==YES]:
            raise ValueError("STAGE75_ANY_QUOTE_COIN_DATE_DOUBLE_COUNT_OR_DEFINITION_CHANGED")
        for p in v["alternative_spot_pairs"]:
            if p["status"] not in EXTRA:
                raise ValueError("STAGE75_INVALID_OFFICIAL_SPOT_STATUS")
            if p["status"]==YES and (
                not p["daily_publisher_sha256"] or
                p["prior_minute_trade_count"]<=0 or
                spot.D(p["prior_quote_volume_IN_NATIVE_QUOTE_UNITS"])<=0
            ):
                raise ValueError("STAGE75_POSITIVE_TRADE_WITHOUT_PUBLISHER_SOURCE")
    def stats(what):
        return {
            "all_original_D0_without_USDT_1m_prior_trade":len(what),
            "any_of_four_alt_quote_assets_positive":sum(x["any_alternative_quote_spot_prior_closed_minute_trades_verified"] for x in what),
            "none_of_four_alt_quote_assets_positive_NOT_PROOF_UNBUYABLE":sum(
                not x["any_alternative_quote_spot_prior_closed_minute_trades_verified"] for x in what),
            "four_alt_quote_pair_test_attempts":len(what)*4,
            "positive_quote_pair_occurrences":sum(len(x["verified_alt_quote_assets"]) for x in what),
            "per_quote_alternative_pair_status":{
                q:{status:sum(next(p for p in x["alternative_spot_pairs"]
                                  if p["quote_asset"]==q)["status"]==status for x in what)
                   for status in EXTRA} for q in QUOTES},
        }
    s={
        "schema":SCHEMA,"preregistered_contract_git_blob":LOCK[PREREG.name],
        "old_all196_source_git_blob":LOCK[OLD.name],
        "stage74_parser_git_blob":LOCK["monster_v4_stage74_original196_spot_asof_prior_minute_SHA.py"],
        "all_original95_coin_date_signal_identities_verified":True,
        "all95":stats(rows),
        "by_original_UTC06_window":{
            d:stats([x for x in rows if x["original_window_date"]==d])
            for d in ("2025-03-30","2025-06-30","2025-11-27")},
        "all_4_quotes_are_exact_original_futures_base_string_only":True,
        "all_spot_positive_quotes_only_prior_1m_real_trades_not_buyable_ask":True,
        "BNB_and_BTC_quote_volumes_not_converted_to_USD":True,
        "SPOT_LISTING_HISTORICAL_ORDERBOOK_ALPHA_DEX_CA_FILLS":"UNKNOWN",
        "P1_P2":"REJECTED",
        "INDEPENDENT_OTHER_AI_REVIEW_OF_NEW_STAGE75":"NOT_DONE",
        "MONSTER_DEPLOYMENT":"NO_GO","GMAIL":"OFF","AUTOTRADE":"NO_GO",
        "ORDER_NOTIONAL":"UNSPECIFIED",
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"monster_stage75_original95_all380_spot_four_quote_SHA_asof_rows.jsonl").write_text(
        "".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n"
                for x in sorted(rows,key=lambda v:(v["original_window_date"],v["original_futures_symbol"]))),
        encoding="utf-8")
    (out/"monster_stage75_original95_four_quote_spot_source_summary.json").write_text(
        json.dumps(s,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STAGE75_COMPLETE95_ORIGINAL_D0_ALL380_ALT_QUOTE_SOURCE_SHA "+
          json.dumps(s["all95"],sort_keys=True))


def selftest():
    src=frozen()
    assert len(src)==95
    original={"date":"2025-03-30","symbol":"1000000BOBUSDT",
              "original_usdm_first_D0_UTC":"2025-04-02T20:15:00Z",
              "spot_historical_evidence_status":"SPOT_DAILY_ARCHIVE_404_UNVERIFIED"}
    called=[]
    clock=spot.utc_ms(original["original_usdm_first_D0_UTC"])
    def mixed(pair,day):
        called.append((pair,day))
        if pair=="1000000BOBUSDC":
            return ({clock-60000:{"close":"5","quote":"1200","base":"12","trades":42}},
                    {"publisher_zip_sha256":"f"*64,"archive_path":"source","number_of_actual_source_minutes":1})
        if pair=="1000000BOBBTC":
            return ({clock-60000:{"close":"0.0000001","quote":"0.01","base":"1","trades":3}},
                    {"publisher_zip_sha256":"f"*64,"archive_path":"source","number_of_actual_source_minutes":1})
        return None,{"status":"SPOT_DAILY_ARCHIVE_404_UNVERIFIED",
                     "archive_path":"missing","publisher_zip_sha256":None}
    x=review_one(original,lookup=mixed)
    assert x["verified_alt_quote_assets"]==["USDC","BTC"]
    assert [c[0] for c in called]==["1000000BOB"+q for q in QUOTES]
    assert x["any_alternative_quote_spot_prior_closed_minute_trades_verified"]
    assert x["alternative_spot_pairs"][2]["prior_quote_volume_IN_NATIVE_QUOTE_UNITS"]=="0.01"
    assert x["alternative_spot_pairs"][2]["quote_asset"]=="BTC"
    assert len(x["alternative_spot_pairs"])==4
    # Modifying future price cannot influence prior-minute classification.
    def future(pair,day):
        bars,proof=mixed(pair,day)
        if bars:
            bars=dict(bars);bars[clock]={"close":"999999","quote":"999","base":"999","trades":999}
        return bars,proof
    assert review_one(original,lookup=future)==x
    zero=dict(original,symbol="TESTUSDT")
    def no(pair,day):
        return {clock-60000:{"close":"5","quote":"0","base":"0","trades":0}},{
            "publisher_zip_sha256":"a"*64,"archive_path":"source","number_of_actual_source_minutes":1}
    assert not review_one(zero,lookup=no)["any_alternative_quote_spot_prior_closed_minute_trades_verified"]
    print("STAGE75_FOUR_QUOTE_SOURCE_LOCK_IDENTITIES_ASOF_NO_FUTURE_SAME_BASE_NO_UNIT_CONVERSION_TEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--pilot",action="store_true")
    p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--aggregate-dir",type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    if args.selftest:selftest();return
    if args.out is None:p.error("--out required")
    if args.aggregate_dir:
        aggregate(args.aggregate_dir,args.out);return
    run(args.shard,args.workers,args.out,args.pilot)


if __name__=="__main__":
    main()
