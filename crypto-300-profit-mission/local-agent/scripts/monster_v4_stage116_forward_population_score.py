#!/usr/bin/env python3
"""Stage116 true-forward G0/G1/G2/G3 score over PRE-FROZEN Stage105 windows.
Offline ONLY. No network, scheduled capture, email, auto order or installation.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

try:
    import monster_v4_stage105_capture_universe_core as scope
    import monster_v4_stage97_one_shot_usdm_capture as capture
    import monster_v4_stage91_forward_oos_replay_gate as old
except ImportError:
    from scripts import monster_v4_stage105_capture_universe_core as scope
    from scripts import monster_v4_stage97_one_shot_usdm_capture as capture
    from scripts import monster_v4_stage91_forward_oos_replay_gate as old

SCHEMA = "MONSTER_STAGE116_FROZEN_THREE_WINDOW_FORWARD_G0_G1_G2_G3_V1"
REPLAY_SCHEMA = "MONSTER_STAGE116_ARCHIVED_ORIGINAL_V4_D0_D1_WINDOW_ROWS_V1"
WINDOWS = scope.WINDOWS
MIN = 60_000
DAY = 86_400_000
PROVENANCE = "STAGE97_AUTHENTICATED_BINANCE_TIME_EXCHANGEINFO_RECHECK"


def stamp(ms: int) -> str:
    return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat().replace("+00:00","Z")


def asof(ms_str: str | None):
    if ms_str is None:
        return None
    if not isinstance(ms_str,str) or not ms_str.endswith("Z"):
        raise ValueError("STAGE116_NOT_UTC_STRING")
    t=datetime.fromisoformat(ms_str[:-1]+"+00:00")
    if t.microsecond or t.second:
        raise ValueError("STAGE116_NONMINUTE_EVENT")
    return int(t.timestamp()*1000)


def raw_jsonproof(item: dict) -> dict:
    if not isinstance(item,dict) or not isinstance(item.get("raw"),str):
        raise ValueError("STAGE116_MISSING_RAW_HTTP_PROOF")
    return {**item, "json":json.loads(item["raw"])}


def audited_capture(snapshot: dict, window: str):
    """Replay Stage97 original HTTPS time proofs, not trust named ATTTESTED."""
    if (not isinstance(snapshot,dict)
        or snapshot.get("schema")!=capture.SCHEMA
        or snapshot.get("window_start_utc")!=window):
        raise ValueError("STAGE116_WRONG_OR_STALE_CAPTURE_SCHEMA")
    packet=snapshot["raw_market_packet"]
    if packet.get("window_start_utc")!=window:
        raise ValueError("STAGE116_CAPTURE_WINDOW_NOT_PINNED")
    before=raw_jsonproof(snapshot["before_official_time"])
    after=raw_jsonproof(snapshot["after_official_time"])
    info=snapshot["exchange_info_http_capture"]
    market_raw=packet["raw_exchangeInfo_json"]
    market={
        **info,
        "url":capture.EXCHANGE_URL,
        "raw":market_raw,
        "json":json.loads(market_raw),
    }
    again=capture.verify_time_proof(before,after,market,window)
    if again["raw_market_packet"]!=packet:
        raise ValueError("STAGE116_BINANCE_CAPTURE_RECHECK_DRIFT")
    universe=scope.freeze_universe(packet)
    if (universe["capture_ms"]!=packet["capture_ms"]
        or universe["raw_sha256"]!=packet["raw_sha256"]):
        raise ValueError("STAGE116_MARKET_POPULATION_TAMPERED")
    return universe


def validate_replay(window: str, original: dict, universe: dict):
    if (not isinstance(original,dict)
        or original.get("schema")!=REPLAY_SCHEMA
        or original.get("window_start_utc")!=window
        or original.get("window_exchange_info_sha256")!=universe["raw_sha256"]
        or original.get("venue")!="BINANCE_USDM"
        or original.get("original_model_source_sha")!=old.MODEL_SOURCE_V4
        or original.get("original_d1_contract_sha")!=old.D1_SOURCE_CONTRACT):
        raise ValueError("STAGE116_REPLAY_NOT_FROZEN_ORIGINAL_MODEL")
    rows=original.get("rows")
    if not isinstance(rows,list):
        raise ValueError("STAGE116_NO_REPLAY_ROWS")
    allowed={r["symbol"] for r in universe["rows"] if r["candidate_for_raw_USDM_attempt"]}
    actual=[r.get("symbol") for r in rows]
    if len(actual)!=len(set(actual)) or set(actual)!=allowed:
        raise ValueError("STAGE116_FULL_MARKET_ATTEMPT_DENOMINATOR_DRIFT")
    start=scope.verify_window(window)
    for r in rows:
        if r.get("date")!=window[:10] or r.get("venue")!="BINANCE_USDM":
            raise ValueError("STAGE116_BAD_REPLAY_DATE_OR_VENUE")
        if r.get("source_status")!="COMPLETE_REAL_1M_PUBLISHER_SHA_MODEL_REPLAY":
            continue
        receipts=r.get("source_9_days_SHA256",[])
        expected=[(date.fromisoformat(window[:10])+timedelta(days=i)).isoformat()
                  for i in range(-1,8)]
        if ([z.get("date") for z in receipts]!=expected
            or any(z.get("bars")!=1440 or z.get("verified_official_publisher_SHA256") is not True
                   or not isinstance(z.get("zip_sha256"),str)
                   or len(z["zip_sha256"])!=64
                   or any(c not in "0123456789abcdef" for c in z["zip_sha256"])
                   for z in receipts)):
            raise ValueError("STAGE116_REAL_OFFICIAL_MINUTE_RECEIPTS_INVALID")
        for field in ("D0_first_UTC","D1_first_UTC"):
            t=asof(r.get(field))
            if t is not None and not start<=t<start+7*DAY:
                raise ValueError("STAGE116_SIGNAL_NOT_IN_FROZEN_WEEK")
        if r.get("D1_first_UTC") is not None and r.get("D0_first_UTC") is None:
            raise ValueError("STAGE116_ORPHAN_D1_WITHOUT_FIRST_D0")
        if r.get("D0_first_UTC") and r.get("D1_first_UTC"):
            if asof(r["D1_first_UTC"])<asof(r["D0_first_UTC"]):
                raise ValueError("STAGE116_FIRST_D1_BEFORE_D0")
        f=r.get("gross_future_labels_not_real_profit")
        if not isinstance(f,dict):
            raise ValueError("STAGE116_MISSING_FUTURE_EVALUATION_ONLY_LABELS")
        for m in (2,5,10):
            event=asof(f.get(f"first_GT{m}x_HIGH_UTC_EVALUATION_ONLY"))
            if event is not None and not start<=event<start+7*DAY:
                raise ValueError("STAGE116_FUTURE_LABEL_OUTSIDE_FIXED_WINDOW")
            d0=asof(r.get("D0_first_UTC"))
            d1=asof(r.get("D1_first_UTC"))
            if bool(f.get(f"D0_first_pre_GT{m}x_5m"))!=(
                d0 is not None and event is not None and d0+5*MIN<=event):
                raise ValueError("STAGE116_EARLY_D0_2X5X10X_LABEL_DRIFT")
            if bool(f.get(f"D1_first_pre_GT{m}x_5m"))!=(
                d1 is not None and event is not None and d1+5*MIN<=event):
                raise ValueError("STAGE116_EARLY_D1_2X5X10X_LABEL_DRIFT")
    return rows


def metrics(rows_by_window: dict):
    """RAW USD-M mixed identity descriptive ONLY, never crypto-only PASS."""
    t=Counter()
    daily=Counter()
    labels=Counter()
    perwindow={}
    for w in WINDOWS:
        if w not in rows_by_window:
            continue
        local=Counter()
        start=scope.verify_window(w)
        for r in rows_by_window[w]:
            t["all_original_population"]+=1
            local["original_attempts"]+=1
            if r["source_status"]!="COMPLETE_REAL_1M_PUBLISHER_SHA_MODEL_REPLAY":
                local["source_incomplete"]+=1
                t["source_incomplete"]+=1
                continue
            t["source_complete"]+=1
            local["source_complete"]+=1
            d0=asof(r.get("D0_first_UTC"))
            d1=asof(r.get("D1_first_UTC"))
            if d0 is not None:local["first_D0"]+=1
            if d1 is not None:
                local["first_D1"]+=1
                bucket=(d1-start)//DAY
                if not 0<=bucket<7:raise ValueError("STAGE116_D1_DAY_OUTSIDE_WEEK")
                daily[(w,bucket)]+=1
            f=r["gross_future_labels_not_real_profit"]
            for m in (2,5,10):
                event=asof(f.get(f"first_GT{m}x_HIGH_UTC_EVALUATION_ONLY"))
                if event is None:
                    continue
                labels[f"gross_{m}x"]+=1
                local[f"gross_{m}x"]+=1
                if d0 is not None and d0<event:
                    labels[f"D0_strict_early_{m}x"]+=1
                if d0 is not None and d0+5*MIN<=event:
                    labels[f"D0_early5_{m}x"]+=1
                    if d1 is not None and d1+5*MIN<=event:
                        labels[f"D1_early5_given_D0_{m}x"]+=1
        perwindow[w]=dict(local)
    days=[daily[(w,i)] for w in WINDOWS for i in range(7)
          if w in rows_by_window]
    return {
        "original_market_venue":"BINANCE_USDM_USDT_PERPETUAL",
        "full_market_source_status":dict(t),
        "gross_2x_5x_10x_posthoc":dict(labels),
        "per_original_window":perwindow,
        "original_D1_burden":({
            "days_included":len(days),"total":sum(days),
            "average_per_day":str(sum(days)/len(days)) if days else None,
            "peak_per_day":max(days) if days else None,
            "per_day":{w:[daily[(w,i)] for i in range(7)] for w in WINDOWS
                       if w in rows_by_window}
        }),
        "comparison_scope":"RAW_USDM_MIXED_UNCERTIFIED_CRYPTO_NOT_A_MODEL_PASS",
    }



def descriptive_raw_gate(stats: dict, complete_windows: bool) -> dict:
    """Compute all frozen fractions exactly, but raw USD-M ≠ confirmed Crypto."""
    labels=stats["gross_2x_5x_10x_posthoc"]
    g1=labels.get("gross_2x",0)
    early=labels.get("D0_early5_2x",0)
    strict=labels.get("D0_strict_early_2x",0)
    g2denom=early
    g2num=labels.get("D1_early5_given_D0_2x",0)
    days=stats["original_D1_burden"]["days_included"]
    alerts=stats["original_D1_burden"]["total"] if days else 0
    peak=stats["original_D1_burden"]["peak_per_day"] if days else None
    window_positives=sum(v.get("gross_2x",0)>0 for v
                         in stats["per_original_window"].values())
    enough=(complete_windows and days==21 and window_positives>=3
            and g1>=20)
    return {
        "scope":"RAW_USDM_FUTURES_MIXED_IDENTITY_DESCRIPTIVE_ONLY_NOT_G0_CRYPTO",
        "original_2x_case_count":g1,
        "window_count_with_2x":window_positives,
        "D0_first_strict_pre2x_count":strict,
        "D0_first_early5_2x_count":early,
        "D1_first_early5_among_D0_early5_count":g2num,
        "G1_strict_percentage":str(strict*100/g1) if g1 else None,
        "G1_early5_percentage":str(early*100/g1) if g1 else None,
        "G2_early5_retention_percentage":str(g2num*100/g2denom) if g2denom else None,
        "G3_mean_raw_D1_per_day":str(alerts/days) if days else None,
        "G3_peak_raw_D1_per_day":peak,
        "raw_G1_has_minimum_independent_sample":enough,
        "raw_G1_thresholds_met_not_crypto_gate":
            bool(enough and strict*100>=90*g1 and early*100>=85*g1),
        "raw_G2_threshold_met_not_crypto_gate":
            (bool(g2denom and g2num*100>=80*g2denom)
             if complete_windows and enough else None),
        "raw_G3_threshold_met_not_crypto_gate":
            bool(complete_windows and days==21 and alerts<=5*days
                 and peak is not None and peak<=12),
        "no_trading_or_actual_execution_info":True,
    }


def score(captures: dict, replays: dict):
    details={}
    validated={}
    failures=[]
    for w in WINDOWS:
        cap=captures.get(w)
        raw=replays.get(w)
        if cap is None:
            details[w]={"source_status":"PENDING_AUTHENTICATED_FROZEN_WINDOW_CAPTURE"}
            failures.append("MISSING_CAPTURE:"+w)
            continue
        # Once supplied, invalid recorded evidence must FAIL, never be ignored.
        universe=audited_capture(cap,w)
        if raw is None:
            details[w]={"source_status":"PENDING_NINE_DAY_MARKET_WIDE_OFFICIAL_MINUTE_REPLAY",
                        "asof_candidate_count":universe["usd_m_usdt_perpetual_asof_candidates"]}
            failures.append("MISSING_REPLAY:"+w)
            continue
        rows=validate_replay(w,raw,universe)
        ok=sum(x["source_status"]=="COMPLETE_REAL_1M_PUBLISHER_SHA_MODEL_REPLAY" for x in rows)
        unknown=sum(x.get("Crypto_identity")!="VERIFIED_CRYPTO_ASOF" for x in rows)
        # No self-declared source tag can prove crypto identity or market fill.
        if any(x.get("Crypto_identity") not in (
              "UNKNOWN_NEEDS_INDEPENDENT_ASOF_PROOF", "CONFIRMED_NONCRYPTO_OUT_OF_SCOPE",
              "VERIFIED_CRYPTO_ASOF") for x in rows):
            raise ValueError("STAGE116_UNKNOWN_IDENTITY_ENUM")
        details[w]={
            "source_status":"RAW_USDM_REPLAY_COMPLETE_BUT_CRYPTO_SCOPE_NOT_ATTESTED"
                if ok==len(rows) else "SOURCE_CENSORED",
            "asof_candidate_count":len(rows),
            "official_minute_source_complete":ok,
            "unknown_or_nonverified_crypto_identity_count":unknown,
            "point_in_time_crypto_only_population_attested":False,
        }
        validated[w]=rows
        if ok!=len(rows):
            failures.append("SOURCE_INCOMPLETE:"+w)
        if unknown:
            failures.append("ASOF_CRYPTO_IDENTITY_UNCONFIRMED:"+w)
    rawstats=metrics(validated)
    rawgate=descriptive_raw_gate(rawstats,len(validated)==3 and
                                 not any("SOURCE_INCOMPLETE" in x for x in failures))
    return {
        "schema":SCHEMA,
        "preregistered_windows_UTC":list(WINDOWS),
        "per_window_evidence":details,
        "gates":{
            "G0":"PARTIAL_SOURCE_OR_SCOPE" if failures else "PARTIAL_NEEDS_INDEPENDENT_CRYPTO_PROOF",
            "G1":"NOT_SCORABLE_NO_VERIFIED_FULL_CRYPTO_MARKET",
            "G2":"NOT_SCORABLE_NO_VERIFIED_FULL_CRYPTO_MARKET",
            "G3":"RAW_ATTENTION_DESCRIPTIVE_NOT_CRYPTO_G3_PASS",
            "G4":"EXECUTION_UNKNOWN_NO_REAL_NET",
            "G5":"NOT_DONE_OTHER_AI_REVIEW",
            "G6":"NO_GO",
        },
        "raw_venue_descriptive_only":rawstats,
        "raw_venue_threshold_computation_not_a_crypto_model_PASS":rawgate,
        "incomplete_reason_codes":failures,
        "original_frozen_discovery_thresholds":{
            "G1_min_independent_2x":20,
            "G1_min_distinct_windows":3,
            "G1_first_D0_strict_early_pct_at_least":90,
            "G1_first_D0_early5_pct_at_least":85,
            "G2_first_D1_of_first_D0_early5_2x_pct_at_least":80,
            "G3_mean_high_attention_per_day_at_most":5,
            "G3_peak_high_attention_per_day_at_most":12,
            "G4_independent_trades_minimum":30,
        },
        "model_rule_changed":"NO",
        "source_vs_execution_distinct":True,
        "synthetic_unit_test_not_external_source_evidence":True,
        "real_executable_net":"UNKNOWN",
        "trading":"NO_GO","monster_deployment":"NO_GO",
        "gmail":"OFF","Frank":"UNCHANGED","Stage99":"UNCHANGED",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest",action="store_true")
    ap.add_argument("--capture-dir",type=Path)
    ap.add_argument("--replay-dir",type=Path)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    if args.selftest:
        selftest()
        return
    if args.out is None:ap.error("--out required")
    captures={}
    replays={}
    for w in WINDOWS:
        day=w[:10]
        if args.capture_dir is not None:
            # Stage99 is already user-approved/installed for these THREE
            # fixed one-shot capture windows. Read its exact Git archive path;
            # never create or enable another scheduler as a substitute.
            f=args.capture_dir/("monster_stage97_point_in_time_usdm_"+
                                day+"_raw_https.json")
            if f.is_file():captures[w]=json.loads(f.read_text())
        if args.replay_dir is not None:
            f=args.replay_dir/("monster-stage116-"+day+"-replay.json")
            if f.is_file():replays[w]=json.loads(f.read_text())
    result=score(captures,replays)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("STAGE116_REAL_FORWARD_SOURCE_AWARE_SCORE "+
          json.dumps({k:v for k,v in result.items() if k!="raw_venue_descriptive_only"},sort_keys=True))


def selftest():
    # Full-source absence NEVER counted as no winners/zero market return.
    o=score({}, {})
    assert len(o["incomplete_reason_codes"])==3
    assert o["raw_venue_descriptive_only"]["original_D1_burden"]["days_included"]==0
    assert o["gates"]["G1"].startswith("NOT_SCORABLE")
    # Future labels cannot manufacture earlier signals.
    w=WINDOWS[0];start=scope.verify_window(w)
    fake={"date":w[:10],"symbol":"CATUSDT","venue":"BINANCE_USDM",
      "source_status":"COMPLETE_REAL_1M_PUBLISHER_SHA_MODEL_REPLAY",
      "D0_first_UTC":stamp(start+MIN),"D1_first_UTC":stamp(start+3*MIN),
      "gross_future_labels_not_real_profit":{
        "first_GT2x_HIGH_UTC_EVALUATION_ONLY":stamp(start+10*MIN),
        "first_GT5x_HIGH_UTC_EVALUATION_ONLY":None,
        "first_GT10x_HIGH_UTC_EVALUATION_ONLY":None,
        "D0_first_pre_GT2x_5m":True,"D1_first_pre_GT2x_5m":True,
        "D0_first_pre_GT5x_5m":False,"D1_first_pre_GT5x_5m":False,
        "D0_first_pre_GT10x_5m":False,"D1_first_pre_GT10x_5m":False,
      }}
    m=metrics({w:[fake]})
    assert m["gross_2x_5x_10x_posthoc"]["D0_early5_2x"]==1
    assert m["gross_2x_5x_10x_posthoc"]["D1_early5_given_D0_2x"]==1
    assert m["original_D1_burden"]["per_day"][w][0]==1
    gate=descriptive_raw_gate(m,False)
    assert gate["raw_G1_has_minimum_independent_sample"] is False
    assert gate["raw_G2_threshold_met_not_crypto_gate"] is None
    assert sum(m["original_D1_burden"]["per_day"][w])==1
    assert asof(stamp(start+MIN))==start+MIN

    # Integration fixture: exact Stage97 HTTPS timestamp proof + actual
    # exchangeInfo byte SHA + Stage91 nine official day-receipt schema,
    # without claiming this synthetic body was received from Binance.
    before_at=start-2*MIN
    fake_market={"serverTime":start-86_400_000,"symbols":[{
        "symbol":"CATUSDT","status":"TRADING","contractType":"PERPETUAL",
        "quoteAsset":"USDT","baseAsset":"CAT","onboardDate":start-DAY}]}
    first=capture.fixture(capture.TIME_URL,
                          {"serverTime":before_at+100},before_at,before_at+200)
    exchange=capture.fixture(capture.EXCHANGE_URL,fake_market,
                             before_at+200,before_at+400)
    last=capture.fixture(capture.TIME_URL,
                         {"serverTime":before_at+500},before_at+400,before_at+600)
    mock_proof=capture.verify_time_proof(first,last,exchange,w)
    checked=audited_capture(mock_proof,w)
    assert checked["usd_m_usdt_perpetual_asof_candidates"]==1
    fake["source_9_days_SHA256"]=[
        {"date":(date.fromisoformat(w[:10])+timedelta(days=i)).isoformat(),
         "zip_sha256":"a"*64,
         "verified_official_publisher_SHA256":True,"bars":1440}
        for i in range(-1,8)]
    fake["Crypto_identity"]="UNKNOWN_NEEDS_INDEPENDENT_ASOF_PROOF"
    packet={"schema":REPLAY_SCHEMA,"window_start_utc":w,
       "window_exchange_info_sha256":checked["raw_sha256"],
       "venue":"BINANCE_USDM",
       "original_model_source_sha":old.MODEL_SOURCE_V4,
       "original_d1_contract_sha":old.D1_SOURCE_CONTRACT,
       "rows":[fake]}
    assert validate_replay(w,packet,checked)[0]["symbol"]=="CATUSDT"
    output=score({w:mock_proof},{w:packet})
    assert output["raw_venue_descriptive_only"]["gross_2x_5x_10x_posthoc"]["gross_2x"]==1
    assert output["raw_venue_threshold_computation_not_a_crypto_model_PASS"]["raw_G1_has_minimum_independent_sample"] is False
    assert len(output["incomplete_reason_codes"])==3
    corrupt=json.loads(json.dumps(packet))
    corrupt["rows"][0]["gross_future_labels_not_real_profit"]["D0_first_pre_GT2x_5m"]=False
    try:validate_replay(w,corrupt,checked)
    except ValueError as ex:assert "EARLY_D0" in str(ex)
    else:raise AssertionError("STAGE116_ALLOW_FALSE_G1_EARLY_LABEL")
    wrongproof=json.loads(json.dumps(mock_proof))
    wrongproof["raw_market_packet"]["raw_sha256"]="b"*64
    try:audited_capture(wrongproof,w)
    except ValueError:pass
    else:raise AssertionError("STAGE116_ALLOW_FORGED_EXCHANGE_INFO_SHA")
    print("STAGE116_ALL_MARKET_STAGE97_AND_STAGE91_SOURCE_CAUSAL_INTEGRATION_SELFTEST_PASS")


if __name__=="__main__":
    main()
