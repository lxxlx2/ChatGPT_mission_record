#!/usr/bin/env python3
"""Stage105 only: bounded, side-effect-free frozen USD-M source population core.

No historical replay, Shadow module, model import, network call, task, email,
Frank or deployment. Both Stage97 HTTPS collector and Stage91 research reuse
this exact contract; import-time external model execution is impossible here.
"""
from __future__ import annotations

from datetime import datetime,timezone
import hashlib
import json
import unicodedata

SCHEMA = "MONSTER_STAGE91_FROZEN_FORWARD_USDM_FULL_POPULATION_REPLAY_V1"
WINDOWS = (
    "2026-10-14T06:00:00Z",
    "2026-10-28T06:00:00Z",
    "2026-11-11T06:00:00Z",
)
EXCHANGE_INFO_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"
WINDOW_MS = 7 * 24 * 3600_000
MIN = 60_000
FRESH_MAX_MS = 15 * MIN


def num(x):
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError("STAGE91_INT_TIMESTAMP_REQUIRED")
    return x


def sha256_raw(raw: str) -> str:
    if not isinstance(raw, str):
        raise ValueError("STAGE91_EXCHANGE_INFO_RAW_REQUIRED")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_window(utc: str) -> int:
    if utc not in WINDOWS:
        raise ValueError("STAGE91_NOT_ONE_OF_THE_THREE_FROZEN_FORWARD_DATES")
    if not isinstance(utc,str) or not utc.endswith("Z"):
        raise ValueError("STAGE105_UTC_WINDOW_REQUIRED")
    d=datetime.fromisoformat(utc[:-1]+"+00:00")
    if d.second!=0 or d.microsecond!=0:
        raise ValueError("STAGE105_WINDOW_NOT_MINUTE_ALIGNED")
    return int(d.timestamp()*1000)


def valid_exact_venue_symbol(symbol: object) -> bool:
    """Accept exchange-provided Unicode letters/numbers but NO normalization.

    Explicitly reject punctuation, invisible/control and path separators;
    underscores may only separate nonempty identifier components. ASCII
    lowercase is deliberately excluded to retain old USD-M invariants.
    """
    if not isinstance(symbol,str) or not symbol or len(symbol)>160:
        return False
    parts=symbol.split("_")
    if any(not part for part in parts):
        return False
    for part in parts:
        for char in part:
            if ("A"<=char<="Z" or "0"<=char<="9"):
                continue
            if ord(char)>127 and unicodedata.category(char)[0] in ("L","N"):
                continue
            return False
    return True


def freeze_universe(packet: dict) -> dict:
    """Validate only the archived bytes/clock. No claim of live official origin."""
    if not isinstance(packet, dict) or packet.get("schema") != SCHEMA:
        raise ValueError("STAGE91_WRONG_MARKET_SNAPSHOT_SCHEMA")
    start = verify_window(packet.get("window_start_utc"))
    if packet.get("venue") != "BINANCE_USDM" or packet.get("source_url") != EXCHANGE_INFO_URL:
        raise ValueError("STAGE91_WRONG_EXCHANGE_OR_SOURCE_URL")
    cap = num(packet.get("capture_ms"))
    if not start - FRESH_MAX_MS <= cap <= start:
        raise ValueError("STAGE91_UNIVERSE_NOT_CAPTURED_BEFORE_FIXED_START")
    raw = packet.get("raw_exchangeInfo_json")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("STAGE91_EMPTY_OFFICIAL_POPULATION")
    if sha256_raw(raw) != packet.get("raw_sha256"):
        raise ValueError("STAGE91_UNIVERSE_RAW_BYTE_TAMPER")
    try:
        payload = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        raise ValueError("STAGE91_MALFORMED_EXCHANGE_INFO") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("symbols"), list):
        raise ValueError("STAGE91_EXCHANGE_INFO_MISSING_SYMBOLS")
    if not payload["symbols"]:
        raise ValueError("STAGE91_EMPTY_MARKET_POPULATION")
    # Binance's USD-M exchangeInfo official docs explicitly say to IGNORE its
    # serverTime for clock verification; use a separately fetched /fapi/v1/time
    # HTTP body in the Stage97 authenticated capture validator instead.
    server_time = payload.get("serverTime")
    if server_time is not None:
        num(server_time)
    seen, rows = set(), []
    for item in payload["symbols"]:
        if not isinstance(item, dict):
            raise ValueError("STAGE91_NONOBJECT_MARKET_ROW")
        symbol = item.get("symbol")
        # USD-M includes official Unicode crypto symbol names as well as
        # dated delivery identifiers. Validate exact exchange raw text without
        # dropping/rewriting anything and split duplicate vs malformed errors.
        if not valid_exact_venue_symbol(symbol):
            raise ValueError("STAGE91_MARKET_SYMBOL_INVALID")
        if symbol in seen:
            raise ValueError("STAGE91_MARKET_SYMBOL_DUPLICATE")
        seen.add(symbol)
        status = item.get("status")
        contract_type = item.get("contractType")
        quote_asset = item.get("quoteAsset")
        base_asset = item.get("baseAsset")
        if (not isinstance(status,str) or not status
            or not isinstance(contract_type,str) or not contract_type
            or not isinstance(quote_asset,str) or not quote_asset
            or not isinstance(base_asset,str) or not base_asset):
            raise ValueError("STAGE91_INCOMPLETE_OFFICIAL_MARKET_ROW")
        onboard = item.get("onboardDate")
        if onboard is not None:
            num(onboard)
        active_at_capture = (
            status == "TRADING" and contract_type == "PERPETUAL"
            and quote_asset == "USDT" and bool(base_asset)
            and (onboard is None or onboard <= cap)
        )
        rows.append({
            "symbol": symbol, "status_asof_capture": status,
            "contract_type":contract_type, "quote_asset":quote_asset,
            "base_asset":base_asset,
            "onboard_ms":onboard,
            "candidate_for_raw_USDM_attempt":active_at_capture,
            "crypto_identity":"UNKNOWN_NEEDS_INDEPENDENT_PROOF",
            "mapping":"UNKNOWN_UNTIL_INDEPENDENT_UNITS_VERIFIED",
        })
    candidates=[x for x in rows if x["candidate_for_raw_USDM_attempt"]]
    if not candidates:
        raise ValueError("STAGE91_NO_USDT_PERPETUAL_IN_UNIVERSE")
    return {
        "schema":SCHEMA,
        "window_start_utc":packet["window_start_utc"],
        "window_end_utc":datetime.fromtimestamp((start+WINDOW_MS)/1000,timezone.utc).isoformat().replace("+00:00","Z"),
        "raw_sha256":packet["raw_sha256"],
        "capture_ms":cap,
        "population_all_exchange_symbols":len(rows),
        "usd_m_usdt_perpetual_asof_candidates":len(candidates),
        "rows":rows,
        "market_population_archive_consistency":"PASS_UNTRUSTED_ORIGIN",
        "source_authenticity":"UNVERIFIED_EXTERNAL_CAPTURE",
        "exchangeInfo_serverTime_clock_authority":"NONE_OFFICIAL_DOCS_SAY_IGNORE",
        "historical_or_forward_replay":"NOT_RUN",
        "G0_point_in_time_crypto_only":"NOT_DONE",
        "OOS":"NOT_DONE",
        "Gmail":"OFF","Monster_deployment":"NO_GO",
    }


