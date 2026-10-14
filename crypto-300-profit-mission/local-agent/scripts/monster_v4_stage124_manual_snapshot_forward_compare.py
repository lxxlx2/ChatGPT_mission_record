#!/usr/bin/env python3
"""Stage124 source-locked full-market pair of USER-REQUESTED manual snapshots.

NO network, timers, daemons, launchd, Gmail, orders, or automatic data
capture. Stage123 is an EXPLORATORY actual T0, NOT original Stage105 OOS.
T1 comes only when the user asks for another live public Binance pull.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from statistics import median

SCHEMA = "MONSTER_STAGE124_MANUAL_FULL_COHORT_TWO_BATCH_PRICE_PROXY_V1"
PREREG = "MONSTER_STAGE124_FROZEN_MANUAL_MARKET_TWO_SNAPSHOT_FORWARD_COMPARISON_PROTOCOL_20261014.md"
BASE = Path(__file__).resolve().parents[3]
EVIDENCE = BASE/"crypto-300-profit-mission"/"monster"/"evidence"
REQUIRED = {
    "rolling24h_all.json":("MONSTER_STAGE123_BINANCE_LIVE_ROLLING24H_FULL_V1","all_tickers"),
    "bbo_all.json":("MONSTER_STAGE123_BINANCE_LIVE_BEST_BID_ASK_FULL_V1","all_quotes"),
    "mark_all.json":("MONSTER_STAGE123_BINANCE_LIVE_MARK_PRICE_ALL_V1","all_marks"),
}
MAX_SOURCE_SPAN_MS=180_000


def val(x,name,positive=True):
    if isinstance(x,bool) or x is None:
        raise ValueError("STAGE124_MISSING_"+name)
    try:
        d=Decimal(str(x))
    except (InvalidOperation,TypeError,ValueError):
        raise ValueError("STAGE124_BAD_"+name) from None
    if not d.is_finite() or (positive and d<=0):
        raise ValueError("STAGE124_NONFINITE_OR_NONPOSITIVE_"+name)
    return d


def millis(iso):
    if not isinstance(iso,str) or not iso.endswith("Z"):
        raise ValueError("STAGE124_NOT_UTC_OBSERVATION")
    parsed=datetime.fromisoformat(iso.replace("Z","+00:00"))
    return int(parsed.timestamp()*1000)


def locked_file(relative):
    if not isinstance(relative,str) or not relative.startswith(
        "crypto-300-profit-mission/monster/evidence/"):
        raise ValueError("STAGE124_NON_ORIGINAL_EVIDENCE_PATH")
    resolved=(BASE/relative).resolve()
    if not resolved.is_relative_to(EVIDENCE.resolve()):
        raise ValueError("STAGE124_SOURCE_PATH_ESCAPES_EVIDENCE")
    if not resolved.is_file():
        raise ValueError("STAGE124_SOURCE_MISSING:"+relative)
    return resolved


def exact_unique_map(rows,kind):
    if not isinstance(rows,list):
        raise ValueError("STAGE124_SOURCE_ARRAY_MISSING_"+kind)
    d={}
    for item in rows:
        if not isinstance(item,dict):
            raise ValueError("STAGE124_INVALID_MARKET_ROW_"+kind)
        sym=item.get("symbol")
        if not isinstance(sym,str) or not sym:
            raise ValueError("STAGE124_BAD_EXACT_SYMBOL_"+kind)
        if sym in d:
            raise ValueError("STAGE124_DUPLICATE_SOURCE_SYMBOL_"+kind)
        d[sym]=item
    return d


def get_batch(manifest_path):
    manifest_path=Path(manifest_path).resolve()
    if manifest_path.parent!=EVIDENCE.resolve() or not manifest_path.is_file():
        raise ValueError("STAGE124_MANIFEST_MUST_BE_GIT_EVIDENCE")
    meta=json.loads(manifest_path.read_text(encoding="utf-8"))
    if (meta.get("schema")!="MONSTER_STAGE123_NEW_LIVE_BINANCE_STRUCTURED_MARKET_OBSERVATION_V1"
        or meta.get("disclosure",{}).get("historical_stage99_status")!="SOURCE_FAILED_NO_BACKFILL"
        or not meta.get("disclosure",{}).get("this_is_new_exploratory_baseline_not_original_OOS")):
        raise ValueError("STAGE124_MARKET_MANIFEST_ORIGIN_DRIFT")
    utc=meta["batch_utc"]["mid"]
    now=millis(utc)
    records=meta.get("source_paths")
    if not isinstance(records,list) or len(records)!=8:
        raise ValueError("STAGE124_EXACT_EIGHT_SOURCE_PARTS_REQUIRED")
    docs={}
    for entry in records:
        rp=entry.get("path")
        file=locked_file(rp)
        fname=file.name
        if fname in docs:
            raise ValueError("STAGE124_DUPLICATE_SOURCE_FILE")
        txt=file.read_text(encoding="utf-8")
        if not isinstance(entry.get("length"),int) or len(txt)!=entry["length"]:
            raise ValueError("STAGE124_SAVED_SOURCE_LENGTH_MISMATCH_"+fname)
        doc=json.loads(txt)
        if doc.get("batch_observation_utc")!=utc:
            raise ValueError("STAGE124_MIXED_SNAPSHOT_SOURCE_BATCH_TIME")
        docs[fname]=doc
    exch=sorted([(name,j) for name,j in docs.items()
                 if "_exchangeinfo_" in name],key=lambda x:x[0])
    if len(exch)!=5:
        raise ValueError("STAGE124_MISSING_ALL_FIVE_FROZEN_MARKET_PARTS")
    symbols=[]
    for i,(name,j) in enumerate(exch):
        if (j.get("schema")!="MONSTER_STAGE123_NATIVE_CONNECTED_BINANCE_EXCHANGEINFO_PART_V1"
            or j.get("slice_start")!=i*200 or
            j.get("source_full_symbol_count")!=meta["coverage"]["raw_exchange_info_count"]):
            raise ValueError("STAGE124_EXCHANGEINFO_SHARD_OR_DENOMINATOR_DRIFT")
        symbols+=j["symbols"]
    exchange=exact_unique_map(symbols,"exchange")
    if len(exchange)!=meta["coverage"]["raw_exchange_info_count"]:
        raise ValueError("STAGE124_EXCHANGEINFO_FULL_DENOMINATOR_MISMATCH")
    others={}
    for suffix,(schema,array_key) in REQUIRED.items():
        candidates=[j for name,j in docs.items() if name.endswith(suffix)]
        if len(candidates)!=1 or candidates[0].get("schema")!=schema:
            raise ValueError("STAGE124_MARKET_FEED_MISSING_"+suffix)
        others[suffix]=exact_unique_map(candidates[0][array_key],suffix)
    eligible={k:v for k,v in exchange.items() if
              v.get("status")=="TRADING" and
              v.get("contractType")=="PERPETUAL" and
              v.get("quoteAsset")=="USDT"}
    if len(eligible)!=meta["coverage"]["active_usdt_perpetual_count"]:
        raise ValueError("STAGE124_ACTIVE_USDT_PERPETUAL_DENOMINATOR_CHANGED")
    all_events={}
    clean_count=0
    missing=Counter()
    for sym in sorted(eligible):
        b=others["bbo_all.json"].get(sym)
        p=others["mark_all.json"].get(sym)
        r=others["rolling24h_all.json"].get(sym)
        if b is None or p is None or r is None:
            reason="+".join(z for z,record in (
                ("NO_BBO",b),("NO_MARK",p),("NO_24H",r)) if record is None)
            all_events[sym]={"source_status":reason}
            missing[reason]+=1
            continue
        try:
            bid=val(b["bidPrice"],"bid")
            ask=val(b["askPrice"],"ask")
            mark=val(p["markPrice"],"mark")
            quote24=val(r["quoteVolume"],"quote24",positive=False)
            if quote24<0 or bid>ask:
                raise ValueError("STAGE124_CROSSED_BOOK_OR_NEGATIVE_TURNOVER")
            timestamps=(int(b["time"]),int(p["time"]),int(r["closeTime"]))
            if any(isinstance(z,bool) or z<now-MAX_SOURCE_SPAN_MS or
                   z>now+MAX_SOURCE_SPAN_MS for z in timestamps):
                raise ValueError("STAGE124_LATE_OR_STALE_ACTIVE_FEED")
            mid=(bid+ask)/2
            all_events[sym]={
                "source_status":"COMPLETE_CURRENT_PRICE_ONLY",
                "best_bid":str(bid),"best_ask":str(ask),
                "mid":str(mid),"mark":str(mark),
                "spread_bps":str((ask-bid)/mid*10000),
                "rolling_quote24_usdt":str(quote24),
                "rolling_change24_pct":r.get("priceChangePercent"),
                "bbo_ms":timestamps[0],"mark_ms":timestamps[1],
                "ticker_close_ms":timestamps[2],
                "contract_pair":eligible[sym].get("pair"),
                "contract_base_asset":eligible[sym].get("baseAsset"),
                "onboard_ms":eligible[sym].get("onboardDate"),
                "exchange_underlying_type":eligible[sym].get("underlyingType"),
                "exchange_underlying_subtype":eligible[sym].get("underlyingSubType"),
                "real_trade":"NOT_OBSERVED",
            }
            clean_count+=1
        except (ValueError,KeyError,TypeError) as exc:
            # Evidence problems are not "losers" and cannot be discarded.
            all_events[sym]={"source_status":"INVALID_REAL_SOURCE:"+type(exc).__name__,
                             "description":str(exc)[:160]}
            missing["INVALID_REAL_SOURCE"]+=1
    return {
        "manifest":str(manifest_path.relative_to(BASE)),
        "batch_utc":utc,"batch_ms":now,
        "original_exchange_symbols":len(exchange),
        "active_original_cohort":len(eligible),
        "source_complete_active":clean_count,
        "source_missing_reasons":dict(sorted(missing.items())),
        "original_active_symbols":all_events,
        "raw_exchange_identity_proof":"CONNECTOR_STRUCTURED_NOT_ORIGINAL_STAGE97_TWOCLOCK",
    }


def summary(values):
    if not values:
        return {"n":0,"median_pct":None,"p10_pct":None,
                "p90_pct":None,"positive":0,"negative":0}
    vs=sorted(values)
    return {"n":len(vs),"median_pct":str(median(vs)),
            "p10_pct":str(vs[int((len(vs)-1)*Decimal("0.10"))]),
            "p90_pct":str(vs[int((len(vs)-1)*Decimal("0.90"))]),
            "positive":sum(v>0 for v in vs),"negative":sum(v<0 for v in vs)}


def compare(first,second):
    if second["batch_ms"]<=first["batch_ms"]:
        raise ValueError("STAGE124_NONCAUSAL_FORWARD_DATE")
    rows=[]
    forward_returns=[]
    mark_returns=[]
    reasons=Counter()
    counts=Counter()
    first_syms=first["original_active_symbols"]
    next_syms=second["original_active_symbols"]
    for symbol in sorted(first_syms):
        a=first_syms[symbol]
        b=next_syms.get(symbol)
        record={
            "symbol":symbol,
            "T0_source_status":a["source_status"],
            "T1_source_status":b["source_status"] if b else "NOT_ACTIVE_OR_ABSENT_T1",
            "T0_datetime_utc":first["batch_utc"],
            "T1_datetime_utc":second["batch_utc"],
            "gross_forward_mid_price_pct":None,
            "gross_forward_mark_price_pct":None,
            "endpoint_ge_2x":None,
            "endpoint_ge_5x":None,
            "endpoint_ge_10x":None,
            "first_2x_crossing_time":"UNKNOWN_SNAPSHOTS_DO_NOT_SUPPLY_1M_HIGH_PATH",
            "not_usable_as_buy_or_real_net":True,
        }
        counts["first_original_active"]+=1
        if a["source_status"]!="COMPLETE_CURRENT_PRICE_ONLY":
            reason="T0_"+a["source_status"]
        elif b is None:
            reason="T1_NOT_ACTIVE_OR_ABSENT"
        elif b["source_status"]!="COMPLETE_CURRENT_PRICE_ONLY":
            reason="T1_"+b["source_status"]
        elif (a["contract_pair"]!=b["contract_pair"] or
              a["contract_base_asset"]!=b["contract_base_asset"] or
              a["onboard_ms"]!=b["onboard_ms"]):
            reason="CONTRACT_IDENTITY_OR_UNIT_MAPPING_CHANGED"
        else:
            u=val(a["mid"],"T0mid")
            v=val(b["mid"],"T1mid")
            m0=val(a["mark"],"T0mark")
            m1=val(b["mark"],"T1mark")
            gross=(v/u-1)*100
            mark=(m1/m0-1)*100
            forward_returns.append(gross)
            mark_returns.append(mark)
            counts["matched_complete_forward"]+=1
            record.update({
                "gross_forward_mid_price_pct":str(gross),
                "gross_forward_mark_price_pct":str(mark),
                "endpoint_ge_2x":v>=u*2,
                "endpoint_ge_5x":v>=u*5,
                "endpoint_ge_10x":v>=u*10,
                "endpoint_le_half_price":v<=u/2,
                "T0_bid_ask_spread_bps":a["spread_bps"],
                "T1_bid_ask_spread_bps":b["spread_bps"],
                "T0_backward_24h_quote_usdt":a["rolling_quote24_usdt"],
                "T1_backward_24h_quote_usdt":b["rolling_quote24_usdt"],
                "T0_observed_quote_ms":a["bbo_ms"],
                "T1_observed_quote_ms":b["bbo_ms"],
                "matched_price_status":"PRICE_PROXY_ONLY_UNREALIZED",
            })
            counts["endpoint_ge_2x"]+=int(v>=u*2)
            counts["endpoint_ge_5x"]+=int(v>=u*5)
            counts["endpoint_ge_10x"]+=int(v>=u*10)
            counts["endpoint_le_half_price"]+=int(v<=u/2)
            rows.append(record)
            continue
        reasons[reason]+=1
        record["censored_reason"]=reason
        rows.append(record)
    assert len(rows)==first["active_original_cohort"]
    if counts["matched_complete_forward"]+sum(reasons.values())!=len(rows):
        raise ValueError("STAGE124_CASE_DENOMINATOR_NOT_CLOSED")
    new=sorted(set(next_syms)-set(first_syms))
    return {
        "schema":SCHEMA,
        "baseline_T0_manifest":first["manifest"],
        "comparison_T1_manifest":second["manifest"],
        "baseline_T0_utc":first["batch_utc"],
        "observed_T1_utc":second["batch_utc"],
        "actual_batch_interval_hours":str(Decimal(second["batch_ms"]-first["batch_ms"])/3_600_000),
        "baseline_original_USDM_active":first["active_original_cohort"],
        "T0_original_symbol_population_including_missing":first["original_exchange_symbols"],
        "T0_original_active_source_complete":first["source_complete_active"],
        "later_T1_active_USDM":second["active_original_cohort"],
        "matched_endpoint_price_only":counts["matched_complete_forward"],
        "right_censored_or_changed_count":sum(reasons.values()),
        "right_censored_by_reason":dict(sorted(reasons.items())),
        "later_newly_active_symbol_count_excluded_from_T0_denominator":len(new),
        "later_newly_active_symbols":new,
        "price_only_matched_endpoint_return":summary(forward_returns),
        "mark_only_matched_endpoint_return":summary(mark_returns),
        "endpoint_at_or_above_2x_in_matched":counts["endpoint_ge_2x"],
        "endpoint_at_or_above_5x_in_matched":counts["endpoint_ge_5x"],
        "endpoint_at_or_above_10x_in_matched":counts["endpoint_ge_10x"],
        "endpoint_at_or_below_half_in_matched":counts["endpoint_le_half_price"],
        "first_2x_high_crossing_unknown_not_scored":True,
        "no_retroactive_listing_lookahead":True,
        "historical_failed_Stage99_not_backfilled":True,
        "OOS_G1_G2_G3":"NOT_SCORABLE_WITH_TWO_NONCONTIGUOUS_SNAPSHOTS",
        "G0_true_crypto":"PARTIAL",
        "G4_actual_net":"UNKNOWN",
        "Stage118_rejected_historical_rule":"REJECTED",
        "Monster":"NO_GO","Frank":"UNCHANGED","Stage99":"UNCHANGED",
        "manual_request_only":True,
    },rows


def readiness(first):
    return {
        "schema":"MONSTER_STAGE124_MANUAL_T0_REAL_SOURCE_READINESS_V1",
        "first_observation_manifest":first["manifest"],
        "batch_utc":first["batch_utc"],
        "full_source_exchange_entries":first["original_exchange_symbols"],
        "original_active_population":first["active_original_cohort"],
        "complete_active_ticker_bbo_mark":first["source_complete_active"],
        "source_gaps":first["source_missing_reasons"],
        "real_T1":"NOT_REQUESTED_OR_ARCHIVED",
        "true_forward_price_proxy":"NOT_YET_OBSERVABLE",
        "G1_G2_G3":"NOT_SCORABLE_FROM_A_SINGLE_CURRENT_SNAPSHOT",
        "G4_real_net":"UNKNOWN",
        "Monster":"NO_GO",
        "automatic_monitor":"OFF",
        "actual_Stage99_stop_command_user_confirmation":"NOT_YET_RECEIVED",
    }


def selftest():
    # Actual Stage123 current snapshot, source-locked from Git on disk.
    t0=get_batch(EVIDENCE/"monster_stage123_20261014T094824Z_manifest.json")
    assert t0["original_exchange_symbols"]==927
    assert t0["active_original_cohort"]==525
    assert t0["source_complete_active"]==525
    assert readiness(t0)["real_T1"]=="NOT_REQUESTED_OR_ARCHIVED"
    first={
        "manifest":"synthetic_only/T0","batch_utc":"2026-10-14T09:00:00Z",
        "batch_ms":1791968400000,
        "original_exchange_symbols":5,
        "active_original_cohort":3,
        "source_complete_active":3,
        "original_active_symbols":{
            "龙虾USDT":{"source_status":"COMPLETE_CURRENT_PRICE_ONLY",
                      "mid":"1","mark":"1","contract_pair":"龙虾USDT",
                      "contract_base_asset":"龙虾","onboard_ms":1,
                      "spread_bps":"5","rolling_quote24_usdt":"1000","bbo_ms":1791968400000},
            "BADUSDT":{"source_status":"COMPLETE_CURRENT_PRICE_ONLY",
                      "mid":"1","mark":"1","contract_pair":"BADUSDT",
                      "contract_base_asset":"BAD","onboard_ms":1,
                      "spread_bps":"5","rolling_quote24_usdt":"1000","bbo_ms":1791968400000},
            "RETIREDUSDT":{"source_status":"COMPLETE_CURRENT_PRICE_ONLY",
                      "mid":"1","mark":"1","contract_pair":"RETIREDUSDT",
                      "contract_base_asset":"RETIRED","onboard_ms":1,
                      "spread_bps":"5","rolling_quote24_usdt":"1000","bbo_ms":1791968400000},
        },
    }
    later={
        **first,"manifest":"synthetic_only/T1",
        "batch_utc":"2026-10-14T12:00:00Z","batch_ms":1791979200000,
        "active_original_cohort":3,
        "original_active_symbols":{
            "龙虾USDT":{**first["original_active_symbols"]["龙虾USDT"],
                     "mid":"2.5","mark":"2.2","bbo_ms":1791979200000},
            "BADUSDT":{**first["original_active_symbols"]["BADUSDT"],
                      "mid":"0.4","mark":"0.5","bbo_ms":1791979200000},
            "NEWUSDT":{**first["original_active_symbols"]["BADUSDT"],
                      "mid":"10","mark":"10","bbo_ms":1791979200000},
        },
    }
    result,events=compare(first,later)
    assert len(events)==3
    assert result["baseline_original_USDM_active"]==3
    assert result["matched_endpoint_price_only"]==2
    assert result["endpoint_at_or_above_2x_in_matched"]==1
    assert result["endpoint_at_or_below_half_in_matched"]==1
    assert result["right_censored_or_changed_count"]==1
    assert result["later_newly_active_symbols"]==["NEWUSDT"]
    assert all(x["first_2x_crossing_time"].startswith("UNKNOWN") for x in events)
    assert all(x["not_usable_as_buy_or_real_net"] for x in events)
    try:compare(later,first)
    except ValueError as exc:assert "NONCAUSAL" in str(exc)
    else:raise AssertionError("STAGE124_HINDSIGHT_REVERSE_T0_T1_ALLOWED")
    print("STAGE124_REAL_927_525_T0_READINESS_AND_SYNTHETIC_T1_CAUSAL_PAIR_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--before",type=Path)
    p.add_argument("--after",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--rows",type=Path)
    args=p.parse_args()
    if args.selftest:
        return selftest()
    if args.before is None or args.out is None:
        p.error("--before and --out required (no background capture)")
    initial=get_batch(args.before)
    if args.after is None:
        result=readiness(initial)
    else:
        result,records=compare(initial,get_batch(args.after))
        if args.rows is None:
            p.error("--rows is required for real two-batch cohort comparison")
        args.rows.parent.mkdir(parents=True,exist_ok=True)
        args.rows.write_text("".join(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n"
                                    for r in records),encoding="utf-8")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items()
                      if k not in ("later_newly_active_symbols",)},ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
