#!/usr/bin/env python3
"""ADR-005 frozen November Spot T0 raw-archive admission: OFFLINE and fail closed.

Accepts only the original Stage163 six-endpoint public HTTP response-body ZIP
and a matching original receipt JSON, captured before one pre-registered UTC
window. Never downloads, modifies source, schedules, sends, or trades.
An internally consistent receipt is NOT cryptographic proof of real-time origin.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

import monster_v4_stage163_spot_one_shot_raw_http_source as source

SCHEMA="MONSTER_ADR005_NOVEMBER_SPOT_FORWARD_T0_RAW_SOURCE_PREFLIGHT_V1"
WINDOWS=(
    "2026-11-02T00:00:00Z",
    "2026-11-16T00:00:00Z",
    "2026-12-01T00:00:00Z",
)
WINDOW_MS=7*24*3600_000
MAX_T0_LOOKBACK_MS=15*60_000
CLOCK_SKEW_MAX_US=60_000_000
EPOCH=datetime(1970,1,1,tzinfo=timezone.utc)
SYMBOL=re.compile(r"[A-Z0-9]+\Z")
REQUIRED_ENDPOINTS={name:source.BASE+endpoint for name,endpoint in source.ENDPOINTS}


def parse_us(value):
    if not isinstance(value,str) or not value.endswith("Z"):
        raise ValueError("ADR005_T0_UTC_Z_TIMESTAMP_REQUIRED")
    try:
        dt=datetime.fromisoformat(value[:-1]+"+00:00")
    except (TypeError,ValueError) as exc:
        raise ValueError("ADR005_T0_BAD_UTC_TIMESTAMP") from exc
    delta=dt-EPOCH
    micros=(delta.days*86400+delta.seconds)*1_000_000+delta.microseconds
    if micros<=0:
        raise ValueError("ADR005_T0_NONPOSITIVE_CLOCK")
    return micros


def frozen_window(start_utc):
    if start_utc not in WINDOWS:
        raise ValueError("ADR005_T0_UNREGISTERED_NOVEMBER_WINDOW")
    return parse_us(start_utc)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _receipt_source(path):
    p=Path(path)
    if not p.is_file() or p.is_symlink():
        raise ValueError("ADR005_T0_RECEIPTS_FILE_MISSING_OR_SYMLINK")
    raw=p.read_bytes()
    if len(raw)>2_000_000:
        raise ValueError("ADR005_T0_RECEIPTS_TOO_LARGE")
    try:
        return json.loads(raw)
    except (ValueError,UnicodeError) as exc:
        raise ValueError("ADR005_T0_RECEIPTS_JSON_INVALID") from exc


def read_source_bundle(zip_path, receipt_path):
    """Verify all original raw members/sha/receipt bindings before any clock gate."""
    p=Path(zip_path)
    if not p.is_file() or p.is_symlink():
        raise ValueError("ADR005_T0_ARCHIVE_MISSING_OR_SYMLINK")
    raw=p.read_bytes()
    if not raw or len(raw)>40_000_000:
        raise ValueError("ADR005_T0_ARCHIVE_SIZE_INVALID")
    receipts=_receipt_source(receipt_path)
    if receipts.get("source_zip_sha256")!=digest(raw):
        raise ValueError("ADR005_T0_SOURCE_ZIP_SHA256_MISMATCH")
    if (receipts.get("schema")!=source.SCHEMA
        or receipts.get("source_venue")!="Binance Spot"
        or receipts.get("allowed_base")!=source.BASE
        or receipts.get("source_is_true_http_response_body_bytes") is not True):
        raise ValueError("ADR005_T0_ORIGINAL_STAGE163_RECEIPT_SCHEMA_INVALID")
    expected={name+".response.raw.json" for name in REQUIRED_ENDPOINTS}
    expected.add("source_manifest.json")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos=archive.infolist()
            if (len(infos)!=len(expected)
                or {x.filename for x in infos}!=expected
                or any(x.is_dir() or x.file_size>30_000_000 for x in infos)):
                raise ValueError("ADR005_T0_SOURCE_ZIP_MEMBERS_INVALID")
            manifest=json.loads(archive.read("source_manifest.json"))
            if (manifest.get("schema")!=source.SCHEMA
                or manifest.get("source_sha_receipts")!=receipts.get("source_sha_receipts")
                or manifest.get("stats")!=receipts.get("stats")):
                raise ValueError("ADR005_T0_INTERNAL_MANIFEST_OR_RECEIPT_DRIFT")
            digest_map=receipts.get("source_sha_receipts")
            if not isinstance(digest_map,dict) or set(digest_map)!=set(REQUIRED_ENDPOINTS):
                raise ValueError("ADR005_T0_ENDPOINT_SET_INCOMPLETE")
            payload={}
            timestamps={}
            for name,url in REQUIRED_ENDPOINTS.items():
                entry=digest_map[name]
                original=archive.read(name+".response.raw.json")
                if (not isinstance(entry,dict)
                    or entry.get("url")!=url or entry.get("http_status")!=200
                    or entry.get("body_byte_length")!=len(original)
                    or entry.get("body_sha256")!=digest(original)
                    or entry.get("raw_http_bytes_available") is not True):
                    raise ValueError("ADR005_T0_RAW_HTTP_RECEIPT_SHA_OR_ORIGIN_DRIFT:"+name)
                start=parse_us(entry.get("start_utc"))
                end=parse_us(entry.get("end_utc"))
                if end<start:
                    raise ValueError("ADR005_T0_REQUEST_CLOCK_BACKWARDS")
                timestamps[name]=(start,end)
                payload[name]=json.loads(original)
    except (zipfile.BadZipFile,UnicodeError,KeyError,TypeError) as exc:
        raise ValueError("ADR005_T0_CORRUPT_OR_INCOMPLETE_ARCHIVE") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("ADR005_T0_INVALID_RAW_HTTP_JSON") from exc
    return payload,timestamps,receipts,digest(raw)


def admit_window(start_utc,zip_path,receipt_path):
    """Strict contemporaneous T0 source receipt window; no future-lookback mixing."""
    start=frozen_window(start_utc)
    bodies,clocks,receipt,zip_sha=read_source_bundle(zip_path,receipt_path)
    ordered=[n for n,_ in source.ENDPOINTS]
    for a,b in zip(ordered,ordered[1:]):
        if clocks[a][1]>clocks[b][0]:
            raise ValueError("ADR005_T0_CROSS_ENDPOINT_CHRONOLOGY_INVALID")
    capture_first=clocks[ordered[0]][0]
    capture_last=clocks[ordered[-1]][1]
    # All capture requests finish before the frozen start. Never backdate a
    # response sampled in the new OOS window to make T0 appear prospective.
    if (capture_first<start-MAX_T0_LOOKBACK_MS*1000
        or capture_last>start
        or clocks["exchangeInfo"][1]>start):
        raise ValueError("ADR005_T0_RECEIPT_NOT_WITHIN_PRESTART_15MIN")
    time_before=bodies["clock_before"].get("serverTime")
    time_info=bodies["exchangeInfo"].get("serverTime")
    time_after=bodies["clock_after"].get("serverTime")
    if any(type(v) is not int or v<=0 for v in (time_before,time_info,time_after)):
        raise ValueError("ADR005_T0_SERVER_CLOCK_FIELDS_INVALID")
    if not time_before<=time_info<=time_after:
        raise ValueError("ADR005_T0_SERVER_CLOCK_NONMONOTONIC")
    # Server endpoint sample must be within each UTC client request interval,
    # modulo a bounded clock uncertainty; not proof of authentic wall-clock.
    for name,t in (("clock_before",time_before),("exchangeInfo",time_info),
                   ("clock_after",time_after)):
        lo,hi=clocks[name]
        if not lo-CLOCK_SKEW_MAX_US<=t*1000<=hi+CLOCK_SKEW_MAX_US:
            raise ValueError("ADR005_T0_SERVER_CLIENT_CLOCK_INCONSISTENT:"+name)
    if (time_info*1000<start-MAX_T0_LOOKBACK_MS*1000
        or time_info*1000>start):
        raise ValueError("ADR005_T0_SERVER_TIME_NOT_PRESTART")
    info=bodies["exchangeInfo"]
    symbols=info.get("symbols")
    if not isinstance(symbols,list) or len(symbols)<1000:
        raise ValueError("ADR005_T0_EXCHANGEINFO_FULL_MARKET_NOT_PRESENT")
    all_seen=set()
    rows=[]
    for item in symbols:
        if not isinstance(item,dict):
            raise ValueError("ADR005_T0_NONOBJECT_MARKET_SYMBOL")
        name=item.get("symbol")
        if (not isinstance(name,str) or not SYMBOL.fullmatch(name)
            or name in all_seen):
            raise ValueError("ADR005_T0_MARKET_ID_DUPLICATE_OR_INVALID")
        all_seen.add(name)
        status=item.get("status")
        quote=item.get("quoteAsset")
        if (not isinstance(status,str) or not status
            or not isinstance(quote,str) or not quote):
            raise ValueError("ADR005_T0_MARKET_STATUS_OR_QUOTE_UNKNOWN")
        allowed=item.get("isSpotTradingAllowed")
        if allowed is not None and type(allowed) is not bool:
            raise ValueError("ADR005_T0_SPOT_TRADING_PERMISSION_INVALID")
        rows.append({"symbol":name,"status_at_capture":status,
                     "quote_asset":quote,"isSpotTradingAllowed":allowed,
                     "eligible_spot_usdt_t0":quote=="USDT" and status=="TRADING"
                         and allowed is not False,
                     "crypto_asset_type_at_event":"UNKNOWN",
                     "account_trading_permission_at_event":"UNKNOWN"})
    eligible=sorted(x["symbol"] for x in rows if x["eligible_spot_usdt_t0"])
    if not eligible:
        raise ValueError("ADR005_T0_NO_SPOT_USDT_CANDIDATES")
    # Reuse old Stage163 structural payload parser, but never its frozen T0
    # 511 denominator or source ZIP SHA for a genuinely new November cohort.
    counters=source.validate_payload(
        {name:json.dumps(bodies[name]).encode() for name in bodies},
        {name:{"end_utc":datetime.fromtimestamp(
            clocks[name][1]//1_000_000,timezone.utc).isoformat().replace("+00:00","Z")}
         for name in bodies})
    if counters["spot_usdt_active"]!=len(eligible):
        raise ValueError("ADR005_T0_STAGE163_POPULATION_RECONCILIATION_DRIFT")
    return {
        "schema":SCHEMA,"window_start_utc":start_utc,
        "window_end_exclusive_utc":(
            datetime.fromtimestamp((start//1000+WINDOW_MS)/1000,timezone.utc)
            .isoformat().replace("+00:00","Z")),
        "frozen_window":True,"venue":"BINANCE_SPOT",
        "archive_sha256":zip_sha,
        "raw_exchangeinfo_body_sha256":receipt["source_sha_receipts"]["exchangeInfo"]["body_sha256"],
        "raw_request_receipt_hash_verified":True,
        "captured_within_15m_and_completed_before_window":True,
        "request_first_us":capture_first,"request_last_us":capture_last,
        "exchangeinfo_server_time_ms":time_info,
        "all_market_symbol_attempts":len(rows),
        "t0_spot_usdt_candidates":len(eligible),
        "t0_spot_usdt_symbol_ids":eligible,
        "all_market_original_rows":rows,
        "source_authenticity":"SELF_REPORTED_HTTP_RECEIPTS_NOT_EXCHANGE_SIGNED",
        "issuer_historical_data":"NOT_YET_VERIFIED",
        "dynamic_listings_during_window":"UNKNOWN",
        "historical_causal_available_at":"UNPROVEN",
        "G0":"PARTIAL_NOT_FULL_DYNAMIC_PIT",
        "G1":"NOT_SCORABLE","G2":"UNKNOWN","G3":"NOT_SCORABLE",
        "G4":"UNKNOWN","G5":"INDEPENDENT_REVIEW_PENDING",
        "G6":"NO_GO","NO_MERGE":True,"NO_DEPLOY":True,
        "NO_AUTOMATIONS":True,"NO_GMAIL":True,"NO_TRADES":True,
    }


def preflight(start_utc,asof_utc,zip_path=None,receipt_path=None):
    start=frozen_window(start_utc)
    asof=parse_us(asof_utc)
    if (zip_path is None)!=(receipt_path is None):
        raise ValueError("ADR005_T0_BOTH_ARCHIVE_AND_RECEIPTS_REQUIRED")
    if zip_path is not None:
        # Admit only if the purported original client receipt has already
        # completed at the explicitly supplied, independently assessed as-of.
        result=admit_window(start_utc,zip_path,receipt_path)
        if result["request_last_us"]>asof:
            raise ValueError("ADR005_T0_FUTURE_RECEIPT_RELATIVE_TO_ASOF")
        result["source_ready_state"]="T0_ARCHIVE_STRUCTURALLY_ADMITTED_ORIGIN_UNVERIFIED"
        result["asof_utc_supplied"]=asof_utc
        return result
    if asof<start-MAX_T0_LOOKBACK_MS*1000:
        state="WAITING_FOR_PRESTART_SOURCE_WINDOW"
    elif asof<=start:
        state="T0_CAPTURE_WINDOW_NO_SOURCE_SUPPLIED"
    else:
        state="T0_MISSING_CANNOT_RETROACTIVELY_PASS_PIT"
    return {"schema":SCHEMA,"window_start_utc":start_utc,
            "asof_utc_supplied":asof_utc,
            "venue":"BINANCE_SPOT","source_ready_state":state,
            "G0":"POPULATION_UNKNOWN","G1":"NOT_SCORABLE",
            "G2":"UNKNOWN","G3":"NOT_SCORABLE","G4":"UNKNOWN",
            "G5":"INDEPENDENT_REVIEW_PENDING","G6":"NO_GO",
            "NO_MERGE":True,"NO_DEPLOY":True,
            "NO_AUTOMATIONS":True,"NO_GMAIL":True,"NO_TRADES":True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--window-start-utc",required=True,choices=WINDOWS)
    p.add_argument("--asof-utc",required=True)
    p.add_argument("--source-zip",type=Path)
    p.add_argument("--source-receipts",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    report=preflight(a.window_start_utc,a.asof_utc,a.source_zip,a.source_receipts)
    if a.out:
        if a.out.exists() or a.out.is_symlink():
            raise ValueError("ADR005_T0_OUTPUT_REFUSE_OVERWRITE")
        a.out.parent.mkdir(parents=True,exist_ok=True)
        with a.out.open("x",encoding="utf-8") as f:
            json.dump(report,f,sort_keys=True,indent=2,ensure_ascii=False)
            f.write("\n")
    print("ADR005_FROZEN_NOVEMBER_SPOT_T0_OFFLINE_PREFLIGHT",
          json.dumps({k:v for k,v in report.items()
                      if k not in ("all_market_original_rows","t0_spot_usdt_symbol_ids")},
                     sort_keys=True))


if __name__=="__main__":
    main()
