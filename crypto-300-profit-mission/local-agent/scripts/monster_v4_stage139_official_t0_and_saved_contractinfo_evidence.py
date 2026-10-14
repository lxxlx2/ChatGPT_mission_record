#!/usr/bin/env python3
"""Stage139: offline Binance T0 instrument scope and saved contractInfo events.

Recorded source clocks and local SHA do not attest network origin. No fetching,
WebSockets, service installation, trade/BUY signal, Gmail or model tuning.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import monster_v4_stage131_dynamic_listing_g1_population_bridge as s131
import monster_v4_stage133_manual_actual_t0_forward_proof as s133
import monster_v4_stage134_t0_population_readiness_bridge as s134
import monster_v4_stage105_capture_universe_core as s105

SCHEMA = "MONSTER_STAGE139_OFFICIAL_T0_AND_SAVED_CONTRACTINFO_PIT_EVIDENCE_V1"
EVENT_SCHEMA = "MONSTER_STAGE139_SAVED_CONTRACTINFO_RAW_RECEIPTS_V1"
ARRIVALS_SCHEMA = s134.ARRIVAL_SCHEMA
MAX_RECEIVE_LAG_MS = 15 * 60_000
MINUTE = 60_000


def scope_classification(underlying):
    if underlying == "COIN":
        return "OFFICIAL_COIN_TYPED_ISSUER_UNVERIFIED"
    if isinstance(underlying, str) and underlying:
        return "OFFICIAL_NOT_COIN_TYPED_AT_T0"
    return "UNKNOWN_TYPE_ASOF_T0"


def minute_observable(received_ms):
    """Never backdate an event to event E or onboard ot."""
    return (received_ms // MINUTE + 1) * MINUTE


def inspect(t0_packet, saved_events=None):
    # Stage133 recomputes the original three ordered raw request receipts,
    # frozen as-of roster, and Stage134 all venue-denominator identity.
    t0 = s134.verified_t0_receipt(t0_packet)
    ledger = s134.reconcile(t0_packet)
    original = json.loads(
        t0["raw_http_records"]["official_exchange_info"]["raw"])
    symbols = {r["symbol"]: r for r in original["symbols"]}
    first = t0["exact_usdt_perpetual_symbols"]
    if set(first) != {x["symbol_exact"] for x in
                     ledger["stage131_reconciled_population"]["raw_population_rows"]}:
        raise ValueError("STAGE139_T0_DENOMINATOR_DISAGREEMENT")
    instrument_rows = []
    scope = Counter()
    for symbol in first:
        raw = symbols[symbol]
        underlying = raw.get("underlyingType")
        row = {
            "symbol_exact": symbol,
            "observation": "ORIGINAL_T0_RAW_EXCHANGE_INFO_ONLY",
            "source_raw_exchangeinfo_SHA256": t0[
                "original_raw_full_exchange_info_sha256"],
            "status": raw["status"],
            "contractType": raw["contractType"],
            "quoteAsset": raw["quoteAsset"],
            "baseAsset": raw.get("baseAsset"),
            "marginAsset": raw.get("marginAsset"),
            "underlyingType": underlying if underlying is not None else "UNKNOWN",
            "underlyingSubType": raw.get("underlyingSubType", "UNKNOWN"),
            "onboardDate_ms": raw.get("onboardDate"),
            "asof_instrument_scope": scope_classification(underlying),
            "issuer_identity_independently_verified": False,
            "contract_units_independently_verified": False,
            "first_executable_trading_minute_proven": False,
            "eligible_to_claim_crypto_G1": False,
        }
        instrument_rows.append(row)
        scope[row["asof_instrument_scope"]] += 1

    if saved_events is None:
        records = []
        provided = False
    else:
        if (not isinstance(saved_events, dict)
                or saved_events.get("schema") != EVENT_SCHEMA
                or set(saved_events) != {"schema", "rows"}
                or not isinstance(saved_events["rows"], list)):
            raise ValueError("STAGE139_SAVED_RAW_CONTRACTINFO_SCHEMA_REQUIRED")
        records = saved_events["rows"]
        provided = True

    start = s131.stamp(t0["new_forward_start_utc"])
    end = s131.stamp(t0["new_forward_end_exclusive_utc"])
    full_initial = set(first)
    seen = {}
    candidates = {}
    events = []
    statuses = Counter()
    for index, receipt in enumerate(records):
        if (not isinstance(receipt, dict)
                or set(receipt) != {
                    "raw", "raw_sha256", "received_ms", "source_stream"}
                or receipt["source_stream"] != "!contractInfo"
                or not isinstance(receipt["raw"], str)
                or not receipt["raw"]):
            raise ValueError("STAGE139_RAW_EVENT_RECEIPT_REQUIRED")
        received = receipt["received_ms"]
        if type(received) is not int or received <= 0:
            raise ValueError("STAGE139_EVENT_RECEIVE_CLOCK_REQUIRED")
        digest = hashlib.sha256(receipt["raw"].encode("utf-8")).hexdigest()
        if receipt["raw_sha256"] != digest:
            raise ValueError("STAGE139_EVENT_RAW_SHA256_DRIFT")
        try:
            payload = json.loads(receipt["raw"])
        except (ValueError, TypeError) as exc:
            raise ValueError("STAGE139_EVENT_RAW_JSON_INVALID") from exc
        if not isinstance(payload, dict) or payload.get("e") != "contractInfo":
            raise ValueError("STAGE139_WRONG_EVENT_KIND")
        at, onboard = payload.get("E"), payload.get("ot")
        sym, st, ct, state = (payload.get("s"), payload.get("st"),
                              payload.get("ct"), payload.get("cs"))
        if (type(at) is not int or at <= 0 or
                type(onboard) is not int or onboard <= 0 or
                not s105.valid_exact_venue_symbol(sym) or
                not isinstance(state, str) or not state or
                not isinstance(ct, str) or not ct or
                type(st) is not int):
            raise ValueError("STAGE139_INVALID_CONTRACTINFO_EVENT_FIELDS")
        if received < at or received - at > MAX_RECEIVE_LAG_MS:
            raise ValueError("STAGE139_EVENT_RECEIPT_CLOCK_UNTRUSTWORTHY")
        key = (sym, at)
        if key in seen:
            if seen[key] != digest:
                raise ValueError("STAGE139_SAME_EVENT_CLOCK_CONFLICT")
            statuses["duplicate_exact_receipt"] += 1
            continue
        seen[key] = digest
        minute = minute_observable(received)
        if st != 1:
            kind = "NOT_USDM_CONTRACT_EVENT"
        elif ct != "PERPETUAL" or not sym.endswith("USDT"):
            kind = "NOT_USDT_PERPETUAL_CONTRACT_EVENT"
        elif not start <= minute < end:
            kind = "OUT_OF_NEW_FORWARD_WINDOW_NOT_CANDIDATE"
        elif state != "TRADING":
            kind = "NONTRADING_CONTRACT_EVENT_NOT_LISTING"
        elif sym in full_initial:
            kind = "T0_EXISTING_ACTIVE_CONTRACT_UPDATE_NOT_ARRIVAL"
        else:
            kind = "RECEIVED_TRADING_STATE_IN_WINDOW_UNVERIFIED_ARRIVAL"
            old = candidates.get(sym)
            if old is None or minute < old["rounded_observation_ms"]:
                candidates[sym] = {
                    "symbol": sym,
                    "rounded_observation_ms": minute,
                    "received_ms": received,
                    "source_event_ms": at,
                    "event_raw_sha256": digest,
                    "declared_onboard_ms_not_execution_time": onboard,
                    "prior_T0_state": (symbols[sym].get("status")
                                       if sym in symbols else "NOT_IN_T0_EXCHANGEINFO"),
                }
        statuses[kind] += 1
        events.append({
            "event_index": index,
            "symbol_exact": sym,
            "source_raw_SHA256": digest,
            "source_event_utc": s133.iso(at),
            "source_received_utc": s133.iso(received),
            "onboard_declared_utc_not_first_fill": s133.iso(onboard),
            "rounded_first_observed_utc_not_first_trade": s133.iso(minute),
            "contract_status_claim": state,
            "contract_type_claim": ct,
            "contract_system_type": st,
            "classification": kind,
            "issuer_and_executable_listing_asof_proven": False,
        })
    arrivals = {
        "schema": ARRIVALS_SCHEMA,
        "rows": [{
            "symbol": value["symbol"],
            "first_observed_minute_utc": s133.iso(value["rounded_observation_ms"]),
            "source_status": "RAW_UNVERIFIED_CANDIDATE",
        } for value in sorted(candidates.values(),
                              key=lambda item: (item["rounded_observation_ms"], item["symbol"]))],
    }
    # Make Stage131/134 responsible for the real full-population duplicate and
    # window constraints rather than independently implementing those gates.
    reconciled = s134.reconcile(t0_packet, arrivals)
    if (reconciled["t0_active_usdt_perpetual_attempts"] != len(first)
            or reconciled["stage131_reconciled_population"]["raw_symbol_attempts"]
            != len(first) + len(arrivals["rows"])):
        raise ValueError("STAGE139_PIT_EVENT_TO_POPULATION_LOSS")
    return {
        "schema": SCHEMA,
        "phase": "OFFLINE_SAVED_ASOF_EVIDENCE_AUDIT_ONLY",
        "stage133_original_packet_sha256": ledger["stage133_packet_integrity_sha256"],
        "t0_exchange_info_original_SHA256": t0[
            "original_raw_full_exchange_info_sha256"],
        "new_forward_start_utc": t0["new_forward_start_utc"],
        "new_forward_end_exclusive_utc": t0["new_forward_end_exclusive_utc"],
        "original_full_T0_exchangeinfo_symbol_count": len(symbols),
        "initial_USDM_perpetual_USDT_attempts": len(first),
        "initial_type_classification_counts": dict(scope),
        "initial_original_instrument_rows": instrument_rows,
        "saved_contractinfo_events_provided": provided,
        "raw_event_receipts_supplied": len(records),
        "unique_event_receipts_accepted": len(events),
        "event_classification_counts": dict(statuses),
        "event_evidence_rows": events,
        "in_window_UNVERIFIED_event_candidates": len(arrivals["rows"]),
        "stage134_all_source_attempts": reconciled[
            "stage131_reconciled_population"]["raw_symbol_attempts"],
        "stage134_compatible_unverified_candidate_rows": arrivals,
        "continuous_seven_day_stream_capture_proven": False,
        "in_window_listing_population_complete": False,
        "origin_independently_attested": False,
        "issuer_identity_independently_verified": False,
        "real_time_trading_tradeable_at_receipt": "UNKNOWN",
        "historical_stage116_first": "SOURCE_FAILED_NO_BACKFILL",
        "stage118_127": "REJECTED_UNCHANGED",
        "stage132_buy_proxy": "NEGATIVE_UNCHANGED",
        "G0": "PARTIAL", "G1": "NOT_SCORABLE", "G2_G3": "NOT_PASSED",
        "G4": "UNKNOWN", "G5": "NOT_DONE", "G6": "NO_GO",
        "model_buy": "NO_GO", "Gmail": "OFF",
        "Frank": "UNCHANGED", "scheduled_capture": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--t0", type=Path, required=True)
    parser.add_argument("--saved-contract-events", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--arrivals-out", type=Path)
    a = parser.parse_args()
    packet = json.loads(a.t0.read_text(encoding="utf-8"))
    events = (json.loads(a.saved_contract_events.read_text(encoding="utf-8"))
              if a.saved_contract_events else None)
    result = inspect(packet, events)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False,
                                sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if a.arrivals_out is not None:
        a.arrivals_out.parent.mkdir(parents=True, exist_ok=True)
        a.arrivals_out.write_text(json.dumps(
            result["stage134_compatible_unverified_candidate_rows"],
            ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": SCHEMA,
        "t0_usdm_attempts": result["initial_USDM_perpetual_USDT_attempts"],
        "optional_in_window_events": result["in_window_UNVERIFIED_event_candidates"],
        "G0": result["G0"], "G1": result["G1"],
        "G6": result["G6"]}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
