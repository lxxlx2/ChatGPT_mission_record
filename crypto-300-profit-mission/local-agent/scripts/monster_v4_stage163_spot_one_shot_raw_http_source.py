#!/usr/bin/env python3
"""One time original-byte public Binance Spot PIT-source probe; never scheduled.

Read-only public HTTP from Binance's documented data-api.binance.vision.
DO NOT treat a single snapshot as a 7-day independent OOS or profit test.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

BASE="https://data-api.binance.vision"
SCHEMA="MONSTER_STAGE163_SPOT_ORIGINAL_HTTP_ONESHOT_V1"
ENDPOINTS=[
    ("clock_before","/api/v3/time"),
    ("exchangeInfo","/api/v3/exchangeInfo"),
    ("bookTicker","/api/v3/ticker/bookTicker"),
    ("ticker24","/api/v3/ticker/24hr"),
    ("depth_BTCUSDT_probe","/api/v3/depth?symbol=BTCUSDT&limit=100"),
    ("clock_after","/api/v3/time"),
]

def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def validate_payload(payloads,receipts):
    if set(payloads)!={x for x,_ in ENDPOINTS}:
        raise ValueError("MONSTER163_REQUIRED_PUBLIC_HTTP_SOURCE_MISSING")
    try:
        blobs={k:json.loads(v) for k,v in payloads.items()}
    except (ValueError,TypeError) as exc:
        raise ValueError("MONSTER163_RAW_JSON_INVALID") from exc
    info=blobs["exchangeInfo"]
    symbols=info.get("symbols")
    if not isinstance(symbols,list) or len(symbols)<1000:
        raise ValueError("MONSTER163_COMPLETE_EXCHANGEINFO_ABSENT")
    ids=[s["symbol"] for s in symbols]
    if len(ids)!=len(set(ids)):
        raise ValueError("MONSTER163_DUPLICATE_INSTRUMENT")
    raw_t0=int(info["serverTime"])
    before=int(blobs["clock_before"]["serverTime"])
    after=int(blobs["clock_after"]["serverTime"])
    if not before-30000<=raw_t0<=after+30000 or after<before:
        raise ValueError("MONSTER163_BINANCE_CLOCK_OR_SOURCE_TIME_DRIFT")
    if abs(raw_t0-int(datetime.fromisoformat(
            receipts["exchangeInfo"]["end_utc"].replace("Z","+00:00")).timestamp()*1000))>60000:
        raise ValueError("MONSTER163_EXCHANGE_VS_CLIENT_TIME_DRIFT")
    usdt=[s for s in symbols if s.get("quoteAsset")=="USDT"
          and s.get("isSpotTradingAllowed") is not False]
    active=[s for s in usdt if s["status"]=="TRADING"]
    if not 250<=len(active)<=1200:
        raise ValueError("MONSTER163_ACTIVE_SPOT_USDT_POPULATION_IMPOSSIBLE")
    books=blobs["bookTicker"]
    ticker=blobs["ticker24"]
    if not isinstance(books,list) or not isinstance(ticker,list):
        raise ValueError("MONSTER163_MARKET_SOURCE_ARRAY_MISSING")
    bmap={s["symbol"]:s for s in books}
    tmap={s["symbol"]:s for s in ticker}
    if len(bmap)!=len(books) or len(tmap)!=len(ticker):
        raise ValueError("MONSTER163_MARKET_SOURCE_DUPLICATE_KEY")
    valid_book=[s for s in active if s["symbol"] in bmap
        and float(bmap[s["symbol"]]["bidPrice"])>0
        and float(bmap[s["symbol"]]["askPrice"])>=float(bmap[s["symbol"]]["bidPrice"])
        and float(bmap[s["symbol"]]["bidQty"])>=0
        and float(bmap[s["symbol"]]["askQty"])>=0]
    depth=blobs["depth_BTCUSDT_probe"]
    if (not depth.get("lastUpdateId")
        or not depth.get("bids") or not depth.get("asks")):
        raise ValueError("MONSTER163_BTC_L2_PROBE_BAD_SOURCE")
    return {
        "market_identity_record_count":len(symbols),
        "market_statuses":dict(sorted(Counter(s["status"] for s in symbols).items())),
        "spot_usdt_all_states":len(usdt),
        "spot_usdt_active":len(active),
        "spot_usdt_break":sum(s["status"]=="BREAK" for s in usdt),
        "all_market_bbo_rows":len(books),
        "all_market_24hr_ticker_rows":len(ticker),
        "active_spot_usdt_bbo_matched":sum(s["symbol"] in bmap for s in active),
        "active_spot_usdt_valid_top_book":len(valid_book),
        "active_spot_usdt_ticker24_matched":sum(s["symbol"] in tmap for s in active),
        "spot_eth_usdt_and_other_venues_not_equivalent_to_usdm":True,
        "btc_l2_bid_levels":len(depth["bids"]),
        "btc_l2_ask_levels":len(depth["asks"]),
        "source_server_time_ms":raw_t0,
        "source_server_time_utc":datetime.fromtimestamp(
            raw_t0/1000,timezone.utc).isoformat().replace("+00:00","Z"),
    }

def fetch(name,endpoint):
    url=BASE+endpoint
    start=utc_now()
    req=urllib.request.Request(url,headers={
        "Accept":"application/json","Accept-Encoding":"identity",
        "User-Agent":"Monster-ResearchOnly-OriginalSource/1.0"})
    with urllib.request.urlopen(req,timeout=35) as resp:
        if resp.status!=200:
            raise RuntimeError("MONSTER163_OFFICIAL_HTTP_NON200")
        raw=resp.read(30_000_000)
        header_date=resp.headers.get("Date")
        mime=resp.headers.get("Content-Type")
    end=utc_now()
    if not raw or len(raw)>=30_000_000:
        raise RuntimeError("MONSTER163_HTTP_BODY_EMPTY_OR_TOO_LARGE")
    if not (mime and "json" in mime.lower()):
        raise RuntimeError("MONSTER163_HTTP_NOT_JSON_CONTENT_TYPE")
    return raw,{"url":url,"start_utc":start,"end_utc":end,
                "http_status":200,"response_date_header":header_date,
                "content_type":mime,"body_byte_length":len(raw),
                "body_sha256":sha(raw),"raw_http_bytes_available":True}

def capture(dest:Path,summary:Path):
    if dest.exists() or summary.exists() or dest.is_symlink() or summary.is_symlink():
        raise ValueError("MONSTER163_NO_OVERWRITE")
    payloads={}
    receipts={}
    for name,endpoint in ENDPOINTS:
        raw,receipt=fetch(name,endpoint)
        payloads[name]=raw
        receipts[name]=receipt
        print("BINANCE_SPOT_RAW_HTTP_ACQUIRED",name,receipt["body_byte_length"],
              receipt["body_sha256"],flush=True)
    stats=validate_payload(payloads,receipts)
    manifest={
        "schema":SCHEMA,"source_venue":"Binance Spot",
        "source_provider":"Official Binance public market-data-only URL",
        "allowed_base":BASE,"source_is_true_http_response_body_bytes":True,
        "raw_http_body_integrity_sha256_per_endpoint":True,
        "response_is_not_exchange_signed":True,
        "single_observation_not_live_multiday_capture":True,
        "complete_historical_listing_change_receipts":False,
        "true_PIT_multi_day_universe":"NOT_PROVEN",
        "future_1m_causal_forward_7d_data":"NOT_COLLECTED",
        "real_fill_entry_exit_price":"UNAVAILABLE",
        "fee_tier_and_order_notional":"USER_NOT_SPECIFIED",
        "G4":"UNKNOWN","G6":"NO_GO",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_GMAIL":True,"NO_TRADE":True,
        "source_sha_receipts":receipts,"stats":stats}
    dest.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(dest,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=8) as zf:
        for key,raw in payloads.items():
            zf.writestr(key+".response.raw.json",raw)
        zf.writestr("source_manifest.json",
                    (json.dumps(manifest,sort_keys=True,indent=2)+"\n").encode())
    manifest["source_zip_sha256"]=sha(dest.read_bytes())
    manifest["source_zip_bytes"]=dest.stat().st_size
    manifest["artifact_internal_manifest_zip_sha_note"]="Zip internal manifest omits zip SHA because it cannot self-hash"
    with summary.open("x") as target:
        json.dump(manifest,target,sort_keys=True,indent=2)
        target.write("\n")
    print("MONSTER163_RAW_HTTP_PIT_SOURCE_READY_NO_MODEL_VALIDATION",
          json.dumps({"source_zip_sha256":manifest["source_zip_sha256"],
                      "stats":stats},sort_keys=True),flush=True)

def selftest():
    base=1792274080000
    req={"exchangeInfo":{"serverTime":base,"symbols":[
        {"symbol":f"SYM{i}USDT","status":"TRADING",
         "quoteAsset":"USDT","isSpotTradingAllowed":True} for i in range(1100)]},
         "clock_before":{"serverTime":base-3000},
         "clock_after":{"serverTime":base+6000},
         "bookTicker":[{"symbol":f"SYM{i}USDT","bidPrice":"1",
                        "askPrice":"1.01","bidQty":"3","askQty":"3"}
                       for i in range(1100)],
         "ticker24":[{"symbol":f"SYM{i}USDT","quoteVolume":"100"}
                     for i in range(1100)],
         "depth_BTCUSDT_probe":{"lastUpdateId":1,"bids":[["1","2"]],
                                 "asks":[["1.01","2"]]}}
    # Frozen selftest never obtains network or manufactures user market source.
    rec={k:{"end_utc":datetime.fromtimestamp(
        base/1000,timezone.utc).isoformat().replace("+00:00","Z")} for k in req}
    decoded={k:json.dumps(v).encode() for k,v in req.items()}
    outcome=validate_payload(decoded,rec)
    assert outcome["spot_usdt_active"]==1100
    req["bookTicker"][0]["symbol"]="SYM1USDT"
    try:
        validate_payload({k:json.dumps(v).encode() for k,v in req.items()},rec)
        raise AssertionError("DUPLICATE_SOURCE_NOT_REJECTED")
    except ValueError as exc:
        assert "DUPLICATE" in str(exc)
    print("MONSTER163_SPOT_RAW_HTTP_SOURCE_SELFTEST_PASS_RESEARCH_ONLY")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest",action="store_true")
    ap.add_argument("--out",type=Path)
    ap.add_argument("--manifest",type=Path)
    args=ap.parse_args()
    if args.selftest:
        selftest()
    else:
        if args.out is None or args.manifest is None:
            ap.error("--out and --manifest are mandatory for one-shot source")
        capture(args.out,args.manifest)

if __name__=="__main__":
    main()
