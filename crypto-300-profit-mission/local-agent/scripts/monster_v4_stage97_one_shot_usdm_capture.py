#!/usr/bin/env python3
"""One-shot, manually triggered point-in-time USD-M population capture.

No scheduler, service, monitoring, trading, notifications or state mutation.
Actual HTTPS GETs occur ONLY with --capture-request in the frozen 15-minute window.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

try:
    import monster_v4_stage91_forward_oos_replay_gate as freeze
except ImportError:
    from scripts import monster_v4_stage91_forward_oos_replay_gate as freeze

TIME_URL = "https://fapi.binance.com/fapi/v1/time"
EXCHANGE_URL = freeze.EXCHANGE_INFO_URL
MAX_BYTES = 5_000_000
CLOCK_MAX_DRIFT_MS = 5000
WINDOW_MS = 15 * 60000
SCHEMA = "MONSTER_STAGE97_ONE_SHOT_AUTHENTICATED_HTTPS_USDM_UNIVERSE_V1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now_ms() -> int:
    return int(time.time()*1000)


def strict_get(url: str, *, max_bytes=MAX_BYTES) -> dict:
    if url not in (TIME_URL, EXCHANGE_URL):
        raise ValueError("STAGE97_NON_OFFICIAL_HTTPS_HOST_OR_PATH")
    req=urllib.request.Request(url,headers={
        "User-Agent":"Monster-Stage97-OneShot-GitHubEvidence/1.0",
        "Accept":"application/json"})
    before=now_ms()
    with urllib.request.urlopen(req,timeout=14) as response:
        if response.status!=200:
            raise ValueError("STAGE97_UNEXPECTED_HTTP_STATUS")
        raw=response.read(max_bytes+1)
        final_url=response.url
        content_type=response.headers.get("Content-Type","")
        if len(raw)>max_bytes or not raw:
            raise ValueError("STAGE97_EMPTY_OR_OVERSIZE_RESPONSE")
    after=now_ms()
    if final_url!=url or "json" not in content_type.lower():
        raise ValueError("STAGE97_HTTP_REDIRECT_OR_NON_JSON_SOURCE")
    text=raw.decode("utf-8","strict")
    try:
        payload=json.loads(text)
    except json.JSONDecodeError:
        raise ValueError("STAGE97_HTTP_BODY_NOT_JSON") from None
    if not isinstance(payload,dict):
        raise ValueError("STAGE97_HTTP_BODY_NOT_OBJECT")
    return {"url":url,"raw":text,"raw_sha256":sha(raw),
            "request_start_ms":before,"response_end_ms":after,
            "content_type":content_type,
            "json":payload}


def check_window(window: str, now: int) -> int:
    start=freeze.verify_window(window)
    if not isinstance(now,int) or isinstance(now,bool) \
       or not start-WINDOW_MS<=now<=start:
        raise ValueError("STAGE97_OUTSIDE_REAL_CAPTURE_15MIN_BEFORE_WINDOW_START")
    return start


def verify_time_proof(first:dict, after:dict,exchange:dict,window:str) -> dict:
    """Raw-byte tampering, official TIME clock drift, and monotonic HTTP bounds."""
    for x in (first, after):
        if x.get("url")!=TIME_URL:
            raise ValueError("STAGE97_TIME_SOURCE_NOT_BINANCE")
        raw=x.get("raw")
        if not isinstance(raw,str) or sha(raw.encode("utf-8"))!=x.get("raw_sha256"):
            raise ValueError("STAGE97_TIME_RAW_SHA_CHANGED")
        payload=json.loads(raw)
        if payload!=x.get("json") or not isinstance(payload.get("serverTime"),int):
            raise ValueError("STAGE97_OFFICIAL_TIME_RAW_MISMATCH")
        mid=(x["request_start_ms"]+x["response_end_ms"])//2
        if abs(payload["serverTime"]-mid)>CLOCK_MAX_DRIFT_MS:
            raise ValueError("STAGE97_INDEPENDENT_BINANCE_SERVER_CLOCK_DRIFT")
        if x["request_start_ms"]>x["response_end_ms"]:
            raise ValueError("STAGE97_NEGATIVE_HTTP_TIME")
    if exchange.get("url")!=EXCHANGE_URL:
        raise ValueError("STAGE97_WRONG_USDM_EXCHANGE_INFO_URL")
    raw=exchange.get("raw")
    if not isinstance(raw,str) or sha(raw.encode("utf-8"))!=exchange.get("raw_sha256"):
        raise ValueError("STAGE97_EXCHANGE_INFO_RAW_SHA_CHANGED")
    if json.loads(raw)!=exchange.get("json"):
        raise ValueError("STAGE97_EXCHANGE_INFO_JSON_RAW_CONFLICT")
    if not (first["request_start_ms"]<=first["response_end_ms"]
            <=exchange["request_start_ms"]<=exchange["response_end_ms"]
            <=after["request_start_ms"]<=after["response_end_ms"]):
        raise ValueError("STAGE97_NOT_CAUSALLY_ORDERED_TLS_GETS")
    before_server=first["json"]["serverTime"]
    after_server=after["json"]["serverTime"]
    if not before_server<=after_server:
        raise ValueError("STAGE97_OFFICIAL_BINANCE_TIME_WENT_BACKWARDS")
    capture=exchange["response_end_ms"]
    start=check_window(window,capture)
    if not start-WINDOW_MS<=before_server<=capture+CLOCK_MAX_DRIFT_MS:
        raise ValueError("STAGE97_OFFICIAL_CLOCK_OUTSIDE_WINDOW")
    if not start-WINDOW_MS<=after_server<=start+CLOCK_MAX_DRIFT_MS:
        raise ValueError("STAGE97_OFFICIAL_AFTER_CLOCK_OUTSIDE_WINDOW")
    packet={
        "schema":freeze.SCHEMA,
        "venue":"BINANCE_USDM","window_start_utc":window,
        "source_url":EXCHANGE_URL,
        "capture_ms":capture,
        "raw_exchangeInfo_json":raw,
        "raw_sha256":exchange["raw_sha256"],
    }
    identity=freeze.freeze_universe(packet)
    return {"schema":SCHEMA,"window_start_utc":window,
      "raw_market_packet":packet,
      "before_official_time":{
        key:first[key] for key in ("url","raw","raw_sha256","request_start_ms","response_end_ms")},
      "after_official_time":{
        key:after[key] for key in ("url","raw","raw_sha256","request_start_ms","response_end_ms")},
      "exchange_info_http_capture":{
        key:exchange[key] for key in ("url","raw_sha256","request_start_ms","response_end_ms","content_type")},
      "source_implementation":"PYTHON_STDLIB_HTTPS_STANDARD_TLS",
      "provenance_ci_env":{
        "GITHUB_RUN_ID":os.environ.get("GITHUB_RUN_ID"),
        "GITHUB_RUN_ATTEMPT":os.environ.get("GITHUB_RUN_ATTEMPT"),
        "GITHUB_SHA":os.environ.get("GITHUB_SHA"),
        "GITHUB_REF":os.environ.get("GITHUB_REF"),
      },
      "snapshot_symbol_summary":{
        k:identity[k] for k in ("population_all_exchange_symbols",
                 "usd_m_usdt_perpetual_asof_candidates")},
      "source_authenticity":"RECORDED_HTTPS_BINANCE_REQUEST_AND_RESPONSE_CLOCK_PROOF",
      "crypto_only_classification":"NOT_VERIFIED",
      "intrawindow_new_listings":"NOT_VERIFIED",
      "G0_full_venue_OOS":"PARTIAL",
      "G1_G2_G3":"NOT_EVALUATED",
      "D1_G3_HISTORICAL":"REJECTED",
      "actual_trades":"NONE",
      "gmail":"OFF","monster_deploy":"NO_GO",
      "autotrade":"NO_GO","frank":"UNCHANGED"}


def capture_one(request:dict,*,get=strict_get,clock=now_ms) -> dict:
    if (not isinstance(request,dict) or
        request.get("schema")!="MONSTER_STAGE97_USER_REQUEST_V1"
        or request.get("authorized_one_shot") is not True):
        raise ValueError("STAGE97_EXPLICIT_ONE_SHOT_GIT_REQUEST_REQUIRED")
    window=request.get("window_start_utc")
    check_window(window,clock())
    first=get(TIME_URL,max_bytes=4096)
    check_window(window,clock())
    exchange=get(EXCHANGE_URL,max_bytes=MAX_BYTES)
    check_window(window,clock())
    last=get(TIME_URL,max_bytes=4096)
    check_window(window,clock())
    return verify_time_proof(first,last,exchange,window)


def fixture(url,body,before,after):
    raw=json.dumps(body,separators=(",",":"))
    return {"url":url,"raw":raw,"raw_sha256":sha(raw.encode()),"json":body,
            "request_start_ms":before,"response_end_ms":after,
            "content_type":"application/json"}


def selftest():
    window=freeze.WINDOWS[0]
    start=freeze.verify_window(window)
    assert check_window(window,start-1000)==start
    for dt in (-16*60000,1000):
        try:check_window(window,start+dt)
        except ValueError as e:assert "OUTSIDE_REAL" in str(e)
        else:raise AssertionError("STAGE97_TIME_MUST_FAIL_CLOSED")
    market={
        "serverTime":start-86_400_000,  # officially ignored, NOT a clock
        "symbols":[{"symbol":"SYNTHUSDT","status":"TRADING",
                    "contractType":"PERPETUAL","baseAsset":"SYNTH",
                    "quoteAsset":"USDT","onboardDate":start-86400000}]
    }
    st=start-2*60000
    first=fixture(TIME_URL,{"serverTime":st+100},st,st+200)
    exchange=fixture(EXCHANGE_URL,market,st+200,st+400)
    last=fixture(TIME_URL,{"serverTime":st+500},st+400,st+600)
    proved=verify_time_proof(first,last,exchange,window)
    assert proved["snapshot_symbol_summary"]["usd_m_usdt_perpetual_asof_candidates"]==1
    assert proved["source_authenticity"].startswith("RECORDED_HTTPS")
    modified=json.loads(json.dumps(exchange))
    modified["json"]["symbols"][0]["symbol"]="TAMPERUSDT"
    try:verify_time_proof(first,last,modified,window)
    except ValueError as e:assert "RAW_CONFLICT" in str(e)
    else:raise AssertionError("STAGE97_TAMPERED_SOURCE_SHOULD_FAIL")
    drift=json.loads(json.dumps(last))
    drift["json"]["serverTime"]=st+20000
    drift["raw"]=json.dumps(drift["json"],separators=(",",":"))
    drift["raw_sha256"]=sha(drift["raw"].encode())
    try:verify_time_proof(first,drift,exchange,window)
    except ValueError as e:assert "CLOCK_DRIFT" in str(e)
    else:raise AssertionError("STAGE97_OFFICIAL_TIME_DRIFT_SHOULD_FAIL")
    request={"schema":"MONSTER_STAGE97_USER_REQUEST_V1",
             "window_start_utc":window,"authorized_one_shot":True}
    def reader(url,*,max_bytes):
        return {TIME_URL:first,EXCHANGE_URL:exchange}[url]
    try:capture_one(request,get=reader,clock=lambda:start+1000)
    except ValueError as e:assert "OUTSIDE_REAL" in str(e)
    else:raise AssertionError("STAGE97_FUTURE_TIME_MUST_BLOCK_ALL_HTTP_GETS")
    assert len(freeze.WINDOWS)==3
    print("STAGE97_OFFICIAL_TIME_SEPARATE_FROM_EXCHANGEINFO_CLOCK_RAW_SHA_AND_ONESHOT_GATE_SELFTEST_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--capture-request",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:
        selftest();return
    if not a.capture_request or not a.out:
        p.error("offline --selftest or explicit --capture-request and --out required")
    request=json.loads(a.capture_request.read_text())
    result=capture_one(request)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE97_REAL_HTTPS_FROZEN_UNIVERSE_CAPTURED "+json.dumps({
        "window":result["window_start_utc"],
        "source":result["source_authenticity"],
        "symbols":result["snapshot_symbol_summary"]},sort_keys=True))


if __name__=="__main__":
    main()
