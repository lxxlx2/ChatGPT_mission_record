#!/usr/bin/env python3
"""Stage140: user-authorized ONE-TIME Binance original raw HTTPS capture.

No launchd, cron, looping, websocket, orders, mail, private credentials,
automatic future collection or retry/sleep. Stage133 original 3-source
T0 packet is mandatory; ancillary snapshots are optional and explicitly
labelled if source access fails. CI/connector-sourced stale quotes are not T0.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import os
import time
import urllib.request

import monster_v4_stage133_manual_actual_t0_forward_proof as stage133
import monster_v4_stage134_t0_population_readiness_bridge as stage134
import monster_v4_stage139_official_t0_and_saved_contractinfo_evidence as stage139

AUTHORIZE_SCHEMA = "MONSTER_STAGE140_EXPLICIT_ONE_TIME_USER_BINANCE_CAPTURE_20261015_V1"
EXTRAS = {
    "usdm_all_24h_ticker": "https://fapi.binance.com/fapi/v1/ticker/24hr",
    "usdm_all_best_bid_ask": "https://fapi.binance.com/fapi/v1/ticker/bookTicker",
    "usdm_all_mark_price": "https://fapi.binance.com/fapi/v1/premiumIndex",
}
MAX = 8_000_000


def stamp(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def raw_get(url, *, limit=MAX):
    if url not in EXTRAS.values():
        raise ValueError("STAGE140_NON_ALLOWLISTED_EXTRA_SOURCE")
    req = urllib.request.Request(
        url, headers={"User-Agent": "Monster-Manual-ReadOnly-T0-20261015/1.0",
                      "Accept": "application/json"})
    request_ms = int(time.time() * 1000)
    with urllib.request.urlopen(req, timeout=17) as http:
        if http.status != 200 or http.url != url:
            raise ValueError("STAGE140_SOURCE_REDIRECT_OR_STATUS_INVALID")
        ct = http.headers.get("Content-Type", "")
        data = http.read(limit + 1)
    response_ms = int(time.time() * 1000)
    if not data or len(data) > limit or "json" not in ct.lower():
        raise ValueError("STAGE140_EXTRA_SOURCE_EMPTY_OVERSIZE_OR_WRONG_TYPE")
    text = data.decode("utf-8", "strict")
    decoded = json.loads(text)
    if not isinstance(decoded, (list, dict)):
        raise ValueError("STAGE140_UNEXPECTED_SOURCE_JSON")
    return {"url": url, "raw": text,
            "raw_sha256": hashlib.sha256(data).hexdigest(),
            "request_start_ms": request_ms,
            "response_end_ms": response_ms,
            "source_content_type": ct,
            "decoded_top_level_type": "list" if isinstance(decoded, list) else "dict",
            "decoded_row_count": len(decoded) if isinstance(decoded, list) else None}


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")) + "\n", encoding="utf-8")


def capture(request, output_root):
    if (not isinstance(request, dict)
            or request.get("schema") != AUTHORIZE_SCHEMA
            or request.get("explicit_single_user_instruction") is not True
            or request.get("source") != "OFFICIAL_BINANCE_PUBLIC_MARKET_ONLY"
            or request.get("no_background_schedule") is not True):
        raise ValueError("STAGE140_NO_EXPLICIT_NEW_USER_MANUAL_AUTHORITY")
    root = Path(output_root)
    if root.exists():
        raise ValueError("STAGE140_OUTPUT_DIRECTORY_ALREADY_EXISTS")
    packet = stage133.one_shot_capture({
        "schema": stage133.REQUEST_SCHEMA,
        "explicit_manual_request": True})
    roster = stage134.reconcile(packet)
    scope = stage139.inspect(packet)
    if roster["t0_active_usdt_perpetual_attempts"] != scope[
            "initial_USDM_perpetual_USDT_attempts"]:
        raise ValueError("STAGE140_UNEXPECTED_RAW_POPULATION_DIFFERENCE")
    receipt_ms = packet["last_http_response_end_ms"]
    now = int(time.time()*1000)
    if not 0 <= now-receipt_ms <= 180_000:
        raise ValueError("STAGE140_STALE_REAL_SOURCE_PACKET")
    batch = "t0_" + stamp(receipt_ms).replace(":", "").replace(".", "")
    folder = root / batch
    save(folder / "stage133_original_three_HTTP_T0.json", packet)
    save(folder / "stage139_original_T0_asof_contract_metadata.json", scope)
    # Strict original SHA identity from Stage133 and no synthetic as-of upgrades.
    by_type = scope["initial_type_classification_counts"]
    extras = {}
    # Ancillary quote GETs run only AFTER T0 is safely written. Failed extras
    # never turn a valid original T0 into a false failed T0.
    for name, endpoint in EXTRAS.items():
        try:
            quote = raw_get(endpoint)
            save(folder / (name + "_raw_http.json"), quote)
            extras[name] = {
                "status": "SAVED_REAL_RAW_HTTPS_SHA",
                "raw_sha256": quote["raw_sha256"],
                "response_end_utc": stamp(quote["response_end_ms"]),
                "decoded_row_count": quote["decoded_row_count"],
                "file": name + "_raw_http.json",
            }
        except (OSError, TimeoutError, ValueError, KeyError,
                json.JSONDecodeError) as exc:
            extras[name] = {"status": "SOURCE_FAILED_NOT_RECONSTRUCTED",
                            "exception_type": type(exc).__name__,
                            "error": str(exc)[:240]}
    summary = {
        "schema": "MONSTER_STAGE140_EXPLICIT_REAL_ONESHOT_20261015_SUMMARY_V1",
        "read_only_manual_authorization": True,
        "capture_UTC": stamp(receipt_ms),
        "capture_bangkok_reference": "2026-10-15",
        "new_real_Stage133_T0": packet["new_forward_start_utc"],
        "new_forward_end_exclusive": packet["new_forward_end_exclusive_utc"],
        "original_three_endpoint_receipt_SHA256": packet["ordered_source_sha256"],
        "full_original_exchangeinfo_SHA256": packet[
            "original_raw_full_exchange_info_sha256"],
        "raw_original_all_exchange_symbols": packet["exchange_full_original_symbols"],
        "active_perpetual_USDT_venue_attempts":
            packet["exchange_current_trading_perpetual_usdt"],
        "t0_official_underlying_categories_issuer_unverified": by_type,
        "optional_all_market_marketdata_receipts": extras,
        "source_security": "stdlib_https_official_host_with_saved_local_raw_SHA_not_signed_by_exchange",
        "real_future_one_minute_series": "NOT_CAPTURED_NEW_SEVEN_DAY_WINDOW",
        "in_window_arrival_full_census": "UNKNOWN_NO_CONTINUOUS_WS",
        "point_in_time_crypto_issuer_verified": False,
        "original_first_2026_10_14_0600": "SOURCE_FAILED_NO_BACKFILL",
        "Stage118_Stage127": "REJECTED_UNCHANGED",
        "Stage132_original_immediate_buy_proxy": "NEGATIVE_UNCHANGED",
        "G0": "PARTIAL", "G1": "NOT_SCORABLE",
        "G2_G3": "NOT_PASSED", "G4": "UNKNOWN",
        "G5_other_AI": "NOT_DONE", "G6_monster_deploy": "NO_GO",
        "Gmail": "OFF", "Frank": "UNCHANGED",
        "automatic_capture_or_subscription_created": False,
        "real_trade_execution": "NONE",
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "github_workflow_sha": os.environ.get("GITHUB_SHA"),
        "saved_t0_path": batch + "/stage133_original_three_HTTP_T0.json",
    }
    save(folder / "stage140_evidence_manifest.json", summary)
    print("STAGE140_EXPLICIT_REAL_CAPTURE " + json.dumps(
        {k: summary[k] for k in (
            "capture_UTC", "new_real_Stage133_T0",
            "new_forward_end_exclusive", "raw_original_all_exchange_symbols",
            "active_perpetual_USDT_venue_attempts",
            "t0_official_underlying_categories_issuer_unverified",
            "optional_all_market_marketdata_receipts", "G0", "G1",
            "G6_monster_deploy")}, ensure_ascii=False, sort_keys=True))
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--capture-request", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    args = p.parse_args()
    request = json.loads(args.capture_request.read_text(encoding="utf-8"))
    capture(request, args.output_root)


if __name__ == "__main__":
    main()
