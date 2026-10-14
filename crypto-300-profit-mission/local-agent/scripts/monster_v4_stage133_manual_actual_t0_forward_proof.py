#!/usr/bin/env python3
"""Stage133 manual one-shot forward market T0 evidence. NO schedule/monitor/orders.

The official request sequence is made ONLY with --capture-request. Offline
validation cannot cryptographically prove that unauthenticated file bytes came
from the source; preserve limits and source process provenance explicitly.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import monster_v4_stage97_one_shot_usdm_capture as stage97
import monster_v4_stage105_capture_universe_core as stage105

SCHEMA = "MONSTER_STAGE133_ACTUAL_T0_FORWARD_RAW_HTTP_PACKET_V1"
REQUEST_SCHEMA = "MONSTER_STAGE133_USER_REQUESTED_ONE_SHOT_V1"
STEP = 300_000
MAX_CLOCK_DRIFT = stage97.CLOCK_MAX_DRIFT_MS
FUTURE_MIN = 5 * 60_000
MAX_BYTES = stage97.MAX_BYTES
TIME_URL = stage97.TIME_URL
EXCHANGE_URL = stage97.EXCHANGE_URL
MIRROR_TIME_URL = "https://www.binance.com/fapi/v1/time"
MIRROR_EXCHANGE_URL = "https://www.binance.com/fapi/v1/exchangeInfo"


def exact_uint(v):
    if type(v) is not int or v <= 0:
        raise ValueError("STAGE133_INVALID_POSITIVE_INTEGER_TIMESTAMP")
    return v


def iso(ms):
    return datetime.fromtimestamp(ms/1000, timezone.utc).isoformat().replace("+00:00","Z")


def read_response(packet, url):
    if not isinstance(packet, dict) or packet.get("url") != url:
        raise ValueError("STAGE133_WRONG_OFFICIAL_ENDPOINT_OR_RESPONSE")
    raw = packet.get("raw")
    if not isinstance(raw,str) or not raw or len(raw.encode("utf-8"))>MAX_BYTES:
        raise ValueError("STAGE133_MISSING_RAW_HTTP_OR_OVERSIZE")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    if packet.get("raw_sha256") != digest:
        raise ValueError("STAGE133_RAW_SHA256_CHANGED")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("STAGE133_INVALID_RAW_JSON") from None
    if not isinstance(data,dict):
        raise ValueError("STAGE133_RAW_JSON_NOT_OBJECT")
    if "json" in packet and packet["json"]!=data:
        raise ValueError("STAGE133_JSON_DECODED_PAYLOAD_NOT_RAW")
    start=exact_uint(packet.get("request_start_ms"))
    end=exact_uint(packet.get("response_end_ms"))
    if start>end:
        raise ValueError("STAGE133_NEGATIVE_REQUEST_DURATION")
    return data,start,end,digest


def validate_three_http_records(first, exchange, last):
    # Stage140 explicit one-time source extension: preserve actual HTTPS URL.
    # Strictly same-host three receipts; no fapi/www mixed requests or redirects.
    # Original frozen fapi packet content remains byte-for-byte compatible.
    source_time = first.get("url") if isinstance(first, dict) else None
    if source_time == TIME_URL:
        source_exchange = EXCHANGE_URL
    elif source_time == MIRROR_TIME_URL:
        source_exchange = MIRROR_EXCHANGE_URL
    else:
        raise ValueError("STAGE133_UNKNOWN_EXACT_TIME_ENDPOINT")
    before, b0,b1, sha_b = read_response(first,source_time)
    market, x0,x1, sha_x = read_response(exchange,source_exchange)
    after, a0,a1, sha_a = read_response(last,source_time)
    if not(b0<=b1<=x0<=x1<=a0<=a1):
        raise ValueError("STAGE133_UNORDERED_OFFICIAL_REQUESTS")
    start_server=exact_uint(before.get("serverTime"))
    end_server=exact_uint(after.get("serverTime"))
    if start_server>end_server:
        raise ValueError("STAGE133_SERVER_CLOCK_BACKWARD")
    for server,lo,hi in ((start_server,b0,b1),(end_server,a0,a1)):
        if abs(server-(lo+hi)//2)>MAX_CLOCK_DRIFT:
            raise ValueError("STAGE133_BINANCE_TIME_CLOCK_DRIFT")
    if not isinstance(market.get("symbols"),list) or not market["symbols"]:
        raise ValueError("STAGE133_FULL_EXCHANGE_UNIVERSE_MISSING")
    seen=set()
    by_status=Counter()
    venue_usdt=[]
    full_rows=[]
    for item in market["symbols"]:
        if not isinstance(item,dict):
            raise ValueError("STAGE133_EXCHANGEINFO_NON_OBJECT")
        symbol=item.get("symbol")
        if not stage105.valid_exact_venue_symbol(symbol):
            raise ValueError("STAGE133_BAD_EXACT_UNICODE_VENUE_SYMBOL")
        if symbol in seen:
            raise ValueError("STAGE133_DUPLICATE_EXCHANGEINFO_SYMBOL")
        seen.add(symbol)
        by_status[str(item.get("status","MISSING"))]+=1
        full_rows.append(item)
        if (item.get("status")=="TRADING" and
            item.get("contractType")=="PERPETUAL" and
            item.get("quoteAsset")=="USDT"):
            venue_usdt.append(symbol)
    # Strictly after evidence completion; never backdate the start.
    start=(a1//STEP+2)*STEP
    if not FUTURE_MIN<start-a1<=2*STEP:
        raise ValueError("STAGE133_BAD_FUTURE_START_DERIVATION")
    # Reference hash incorporates ordered independent endpoint receipts;
    # it is an integrity seal for the artifact, NOT signed Binance evidence.
    record={"schema":SCHEMA,
        "source_mode":"OPERATOR_MANUALLY_REQUESTED_STDLIB_HTTPS_ONE_SHOT_ONLY",
        "provenance_limit":"RECORDED_HTTPS_BINANCE_UNSIGNABLE_TLS_AFTER_FACT_NOT_EXTERNAL_ATTESTATION",
        "required_three_official_endpoints":[source_time,source_exchange,source_time],
        "raw_http_records":{"official_before_time":first,"official_exchange_info":exchange,"official_after_time":last},
        "ordered_source_sha256":[sha_b,sha_x,sha_a],
        "last_http_response_end_ms":a1,
        "start_derivation":"(floor(last_http_response_end_ms/300000)+2)*300000",
        "new_forward_start_utc":iso(start),
        "new_forward_start_epoch_ms":start,
        "new_forward_end_exclusive_utc":iso(start+stage105.WINDOW_MS),
        "time_from_final_response_to_start_ms":start-a1,
        "historical_stage116_original_first_start":"2026-10-14T06:00:00Z",
        "historical_stage116_original_first_status":"SOURCE_FAILED_NO_BACKFILL",
        "frozen_old_three_window_scoring_reused_without_new_sources":False,
        "exchange_full_original_symbols":len(full_rows),
        "exchange_current_trading_perpetual_usdt":len(venue_usdt),
        "exact_usdt_perpetual_symbols":sorted(venue_usdt),
        "full_exchange_info_including_inactive_equity_held_in_original_raw":True,
        "original_raw_full_exchange_info_sha256":sha_x,
        "source_status_counts":dict(sorted(by_status.items())),
        "time_stamped_trading_status_claim_from_recorded_exchange_response":True,
        "independent_crypto_issuer_and_contract_unit_verification":"UNVERIFIED",
        "in_window_new_listings":"NOT_YET_OBSERVED",
        "minute_level_forward_detection":"NOT_YET_OBSERVED",
        "future_all_market_7day_source":"PENDING_WINDOW_END",
        "future_OOS_2x_positive_denominator":"NOT_YET_OBSERVED",
        "one_shot_observation_is_real_time_alert_delivery":False,
        "stage130_and_132_historical_31_strategy_profit":"REJECTED_OR_NEGATIVE_PROXY_UNCHANGED",
        "G0":"PARTIAL","G1":"NOT_SCORABLE","G2_G3":"NOT_PASSED",
        "G4":"UNKNOWN","independent_other_AI_review":"NOT_DONE",
        "monster_deployment":"NO_GO","Frank":"UNCHANGED","Gmail":"OFF",
        "automatic_followup_scheduled":False}
    if source_time == MIRROR_TIME_URL:
        # Explicitly disclose the Binance website mirror hostname and the
        # potentially stale embedded exchangeInfo serverTime field. Never
        # claim the latter is the actual moment this symbol set last changed.
        embedded = market.get("serverTime")
        record["alternate_source_host"] = (
            "www.binance.com HTTPS website FAPI mirror, NOT documented fapi.binance.com API base")
        record["fapi_mirror_exchangeinfo_embedded_serverTime"] = (
            embedded if type(embedded) is int else None)
        record["fapi_mirror_embedded_exchangeinfo_serverTime_age_ms_at_capture"] = (
            x1 - embedded if type(embedded) is int else None)
        record["mirror_contents_are_guaranteed_current_at_T0"] = False
        record["mirror_host_source_equivalence_independently_attested"] = False
    return record


def one_shot_capture(req,get=stage97.strict_get):
    if (not isinstance(req,dict) or req.get("schema")!=REQUEST_SCHEMA or
            req.get("explicit_manual_request") is not True):
        raise ValueError("STAGE133_EXPLICIT_MANUAL_REQUEST_REQUIRED")
    # No implicit timers or date-derived automatic loops, single endpoint sequence.
    first=get(TIME_URL,max_bytes=4096)
    exchange=get(EXCHANGE_URL,max_bytes=MAX_BYTES)
    last=get(TIME_URL,max_bytes=4096)
    return validate_three_http_records(first,exchange,last)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--capture-request",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.capture_request is None:
        p.error("no network without --capture-request; missing explicit human manual authorization")
    request=json.loads(a.capture_request.read_text(encoding="utf-8"))
    result=one_shot_capture(request)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("raw_http_records","exact_usdt_perpetual_symbols")},ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
