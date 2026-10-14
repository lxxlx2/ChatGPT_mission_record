#!/usr/bin/env python3
"""Stage134: offline Stage133 authentic-receipt-format -> Stage131 census bridge.

A recorded TLS response/hash is not external cryptographic authentication.
This module cannot grant G0/G1, validate seven days, collect data, or send alerts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import monster_v4_stage131_dynamic_listing_g1_population_bridge as stage131
import monster_v4_stage133_manual_actual_t0_forward_proof as stage133

SCHEMA = "MONSTER_STAGE134_STAGE133_TO_STAGE131_FORWARD_READINESS_V1"
ARRIVAL_SCHEMA = "MONSTER_STAGE134_UNVERIFIED_ARRIVAL_CANDIDATES_V1"
WINDOW_MS = 168 * 60 * 60 * 1000


def canonical_sha256(obj):
    return hashlib.sha256(json.dumps(
        obj, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def verified_t0_receipt(packet):
    """Recompute receipt integrity, ordered clocks and complete as-of venue roster.

    This is NOT an independent proof that stored HTTP content came from Binance.
    """
    if not isinstance(packet, dict) or packet.get("schema") != stage133.SCHEMA:
        raise ValueError("STAGE134_BAD_STAGE133_PACKET_SCHEMA")
    raw = packet.get("raw_http_records")
    if not isinstance(raw, dict) or set(raw) != {
            "official_before_time", "official_exchange_info", "official_after_time"}:
        raise ValueError("STAGE134_MISSING_EXACT_THREE_RAW_HTTP_RECORDS")
    recomputed = stage133.validate_three_http_records(
        raw["official_before_time"], raw["official_exchange_info"],
        raw["official_after_time"])
    if packet != recomputed:
        raise ValueError("STAGE134_STAGE133_RECEIPT_OR_ROSTER_DRIFT")
    start = stage131.stamp(packet["new_forward_start_utc"])
    end = stage131.stamp(packet["new_forward_end_exclusive_utc"])
    if (end - start != WINDOW_MS or start != packet["new_forward_start_epoch_ms"]
            or packet["historical_stage116_original_first_status"]
            != "SOURCE_FAILED_NO_BACKFILL"):
        raise ValueError("STAGE134_NEW_WINDOW_OR_OLD_FAILURE_CHANGED")
    return recomputed


def reconcile(packet, arrival_candidates=None):
    t0 = verified_t0_receipt(packet)
    if arrival_candidates is not None:
        if (not isinstance(arrival_candidates, dict)
                or arrival_candidates.get("schema") != ARRIVAL_SCHEMA
                or not isinstance(arrival_candidates.get("rows"), list)
                or set(arrival_candidates) != {"schema", "rows"}):
            raise ValueError("STAGE134_UNVERIFIED_ARRIVAL_SCHEMA_REQUIRED")
        additions = arrival_candidates["rows"]
    else:
        additions = []

    original = json.loads(
        t0["raw_http_records"]["official_exchange_info"]["raw"])
    full_original = original["symbols"]
    originally_seen = {x["symbol"]: x for x in full_original}
    initial = t0["exact_usdt_perpetual_symbols"]
    if any(not x.endswith("USDT") for x in initial):
        raise ValueError("STAGE134_STAGE131_USDT_SCOPE_INCOMPATIBLE")
    baseline = [{"symbol": s, "source_status": "PENDING_OFFICIAL_1M_PUBLISHER_SHA"}
                for s in initial]
    future = []
    classifications = {}
    for item in additions:
        if not isinstance(item, dict) or set(item) != {
                "symbol", "first_observed_minute_utc", "source_status"}:
            raise ValueError("STAGE134_ARRIVAL_EXACT_FIELDS_REQUIRED")
        if not isinstance(item["source_status"], str) or not item["source_status"]:
            raise ValueError("STAGE134_ARRIVAL_SOURCE_STATUS_REQUIRED")
        # Allow only explicitly incomplete source candidates.  A substring
        # scan for "VERIFIED" would also reject "UNVERIFIED", silently
        # losing the very in-window population Stage131 must preserve.
        # A caller cannot assert completed, authenticated or live source.
        if item["source_status"] not in {
                "RAW_UNVERIFIED_CANDIDATE", "UNVERIFIED_CANDIDATE",
                "UNVERIFIED", "PENDING", "PENDING_SOURCE",
                "MISSING_SOURCE", "CENSORED_SOURCE"}:
            raise ValueError("STAGE134_CANNOT_SELF_ATTEST_ARRIVAL")
        symbol = item["symbol"]
        if not isinstance(symbol, str):
            raise ValueError("STAGE134_ARRIVAL_INVALID_SYMBOL")
        future.append({
            "symbol": symbol,
            "first_observed_minute_utc": item["first_observed_minute_utc"],
            "source_status": "UNVERIFIED_OFFLINE_ARRIVAL_CANDIDATE"})
        classifications[symbol] = (
            "T0_PRESENT_BUT_NOT_IN_ACTIVE_USDT_PERPETUAL_ROSTER"
            if symbol in originally_seen else "NOT_PRESENT_IN_T0_EXCHANGEINFO")

    # The existing Stage131 source/time/identity reconciliation owns all
    # population and uniqueness validation. No new-scoring exceptions.
    result = stage131.reconcile_population(
        t0["new_forward_start_utc"], baseline, future)
    if (result["preexisting_raw_attempts"] != len(initial)
            or result["new_listing_raw_attempts"] != len(future)
            or result["raw_symbol_attempts"] != len(initial) + len(future)
            or len(result["raw_population_rows"]) != result["raw_symbol_attempts"]):
        raise ValueError("STAGE134_LOSSY_POPULATION_BRIDGE")

    for row in result["raw_population_rows"]:
        if row["population_lane"] == "PREEXISTING_AT_WINDOW_START":
            # Original T0 HTTP exchangeInfo claim only, NOT independently
            # certified onset / first executable Binance contract minute.
            original_entry = originally_seen[row["symbol_exact"]]
            onboard = original_entry.get("onboardDate")
            start_ms = stage131.stamp(t0["new_forward_start_utc"])
            if (type(onboard) is int and
                    0 < start_ms - onboard < 24 * 3_600_000):
                row["pre_T0_recent_onboarding_claim_ms"] = onboard
                row["pre_T0_recent_onboarding_minute_utc"] = stage133.iso(
                    (onboard // 60_000) * 60_000)
                row["pre_T0_recent_onboarding_provenance"] = (
                    "SAVED_T0_EXCHANGEINFO_ONBOARDDATE_UNVERIFIED_PIT")
        if row["population_lane"] == "IN_WINDOW_FIRST_TRADABLE_MINUTE_CANDIDATE":
            row["arrival_source_classification"] = classifications[row["symbol_exact"]]
            row["in_window_listing_status"] = "UNVERIFIED_PIT_NEW_LISTING_OR_TRANSITION"
        else:
            row["in_window_listing_status"] = "PREEXISTING_VENUE_CANDIDATE_ONLY"
        if row["asof_trading_eligibility_verified"] or row["asof_crypto_issuer_verified"]:
            raise ValueError("STAGE134_BRIDGE_PROMOTED_SOURCE_TO_VERIFIED")

    return {
        "schema": SCHEMA,
        "phase": "OFFLINE_SOURCE_READINESS_INTEGRATION_ONLY",
        "stage133_packet_integrity_sha256": canonical_sha256(packet),
        "stage133_original_exchangeinfo_raw_sha256": t0[
            "original_raw_full_exchange_info_sha256"],
        "recorded_three_https_source_hashes": t0["ordered_source_sha256"],
        "https_origin_external_attestation": "NOT_INDEPENDENTLY_ATTESTED",
        "new_forward_start_utc": t0["new_forward_start_utc"],
        "new_forward_end_exclusive_utc": t0["new_forward_end_exclusive_utc"],
        "window_from_stage133_derived_clock_not_stage116_frozen_date": True,
        "original_stage116_oct14_0600": "SOURCE_FAILED_NO_BACKFILL",
        "full_t0_exchangeinfo_symbols_in_original_raw": len(full_original),
        "t0_active_usdt_perpetual_attempts": len(initial),
        "in_window_arrival_candidates_unverified": len(future),
        "arrival_census_complete": False,
        "arrival_evidence": ("NOT_PROVIDED" if arrival_candidates is None
                             else "UNVERIFIED_CANDIDATES_ONLY"),
        "old_stage116_scorer_unchanged_fixed_three_windows": True,
        "stage131_reconciled_population": result,
        "stage77_frozen_acceptance": {
            "G1_min_independent_2x": 20,
            "G1_min_independent_windows": 3,
            "G1_first_D0_strict_pct": 90,
            "G1_first_D0_early5_pct": 85,
            "G2_first_D1_retention_pct": 80,
            "G3_mean_D1_per_day_max": 5,
            "G3_peak_D1_per_day_max": 12,
            "G4_independent_full_buy_sell_observations_min": 30,
        },
        "blocking_evidence": [
            "REAL_ACTUAL_USER_TRIGGERED_T0_NOT_ATTESTED_BY_OFFLINE_ADAPTER",
            "FULL_168H_ALL_MARKET_MINUTE_PUBLISHER_SHA_NOT_PROVIDED",
            "IN_WINDOW_ARRIVALS_AND_DELISTING_CENSUS_NOT_VERIFIED",
            "POINT_IN_TIME_CRYPTO_ISSUER_AND_SPOT_FUTURES_UNITS_NOT_VERIFIED",
            "REAL_EXECUTION_QUOTES_DEPTH_FEES_NOTIONAL_AND_EXITS_ABSENT",
            "G5_INDEPENDENT_OTHER_AI_REVIEW_NOT_DONE",
        ],
        "G0": "PARTIAL",
        "G1": "NOT_SCORABLE",
        "G2_G3": "NOT_PASSED",
        "G4": "UNKNOWN",
        "G5": "NOT_DONE",
        "G6": "NO_GO",
        "Stage118": "REJECTED_UNCHANGED",
        "Stage127": "REJECTED_UNCHANGED",
        "Stage132_first_momentum_buy_proxy": "NEGATIVE_UNCHANGED",
        "live_market_source_capture": False,
        "scheduled_capture_or_notification_created": False,
        "monster_deployment": "NO_GO",
        "Gmail": "OFF",
        "Frank": "UNCHANGED",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--t0", type=Path, required=True)
    parser.add_argument("--arrival-candidates", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    packet = json.loads(args.t0.read_text(encoding="utf-8"))
    arrivals = (json.loads(args.arrival_candidates.read_text(encoding="utf-8"))
                if args.arrival_candidates is not None else None)
    output = reconcile(packet, arrivals)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(
        output, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    print(json.dumps({
        "schema": SCHEMA,
        "t0_attempts": output["t0_active_usdt_perpetual_attempts"],
        "arrival_candidates_unverified": output["in_window_arrival_candidates_unverified"],
        "G0": output["G0"], "G1": output["G1"],
        "monster_deployment": output["monster_deployment"],
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
