#!/usr/bin/env python3
"""Stage138 — offline Stage133..Stage137 one-shot evidence scorecard / multi-window ledger.

Default phase PLAN is read-only, no live GET and no model replay. Evaluate
uses saved original-format Binance publisher ZIP+CHECKSUM only. Never BUY.
No real-time alarm, independent source HTTP origin or PIT crypto certification.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import monster_v4_stage131_dynamic_listing_g1_population_bridge as s131
import monster_v4_stage133_manual_actual_t0_forward_proof as s133
import monster_v4_stage136_manual_publisher_archive_acquisition as s136
import monster_v4_stage135_full_market_publisher_minute_coverage as s135
import monster_v4_stage137_dynamic_t0_original_core_causal_replay as s137

SCHEMA = "MONSTER_STAGE138_MANUAL_FORWARD_G0_G3_READINESS_SCORECARD_V1"
AGG_SCHEMA = "MONSTER_STAGE138_DISJOINT_FORWARD_WINDOW_EVIDENCE_LEDGER_V1"
STATES = (
    "SOURCE_CENSORED_NO_REPLAY",
    "MODEL_SYMBOL_UNSUPPORTED_NOT_A_NO_WATCH",
    "NEW_LISTING_REPLAY_NOT_YET_SUPPORTED_PIT_UNVERIFIED",
    "ORIGINAL_ASCII_V4_D0_AND_FROZEN_D1_CAUSAL_OFFLINE",
    "ORIGINAL_V4_NUMERIC_CORE_WITH_UNICODE_IDENTITY_ADAPTER_CAUSAL_OFFLINE",
)
FROZEN_THRESHOLDS = {
    "G1_min_nonoverlapping_new_forward_windows": 3,
    "G1_min_independently_verified_crypto_2x": 20,
    "G1_first_D0_strict_before_2x_pct_gte": 90,
    "G1_first_D0_at_least_5m_before_2x_pct_gte": 85,
    "G2_D1_early5_retains_D0_early5_pct_gte": 80,
    "G3_D1_per_day_mean_lte": 5,
    "G3_D1_per_day_peak_lte": 12,
    "G4_independent_real_roundtrip_net_cases_gte": 30,
}
GATES = {
    "G0": "PARTIAL",
    "G1": "NOT_SCORABLE",
    "G2_G3": "NOT_PASSED",
    "G4": "UNKNOWN",
    "G5": "NOT_DONE",
    "G6": "NO_GO",
}


def canonical_hash(obj):
    return hashlib.sha256(json.dumps(
        obj, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def check_window(clock_start, clock_end):
    start, end = s131.stamp(clock_start), s131.stamp(clock_end)
    if end - start != 7 * 86_400_000:
        raise ValueError("STAGE138_WINDOW_NOT_EXACT_FROZEN_168H")
    return start, end


def summarize_rows(rows, start, end):
    if not isinstance(rows, list) or not rows:
        raise ValueError("STAGE138_EMPTY_FULL_MARKET_LEDGER")
    seen = set()
    c = Counter()
    daily = [0] * 7
    for row in rows:
        symbol = row.get("symbol_exact")
        status = row.get("replay_status")
        if (not isinstance(symbol, str) or not symbol or symbol in seen or
                row.get("population_lane") not in (
                    "PREEXISTING_AT_WINDOW_START",
                    "IN_WINDOW_FIRST_TRADABLE_MINUTE_CANDIDATE") or
                status not in STATES):
            raise ValueError("STAGE138_BAD_OR_DUPLICATE_POPULATION_ROW")
        seen.add(symbol)
        c["full_market_attempts"] += 1
        c[status] += 1
        if status not in (STATES[3], STATES[4]):
            if row.get("D0_first_UTC") is not None or row.get("D1_first_UTC") is not None:
                raise ValueError("STAGE138_CENSORED_OR_UNSUPPORTED_HAS_SIGNAL")
            continue
        labels = row.get("gross_future_labels_not_real_profit")
        if not isinstance(labels, dict):
            raise ValueError("STAGE138_COMPLETE_ROW_MISSING_GROSS_LABELS")
        c["original_core_source_compatible"] += 1
        first_d0 = row.get("D0_first_UTC")
        first_d1 = row.get("D1_first_UTC")
        if first_d0 is not None:
            d0_ms = s131.stamp(first_d0)
            if d0_ms < start or d0_ms >= end or d0_ms % 180_000:
                raise ValueError("STAGE138_INVALID_ORIGINAL_D0_CLOCK")
            c["unique_first_D0"] += 1
        if first_d1 is not None:
            d1_ms = s131.stamp(first_d1)
            if (first_d0 is None or d1_ms < d0_ms
                    or not start <= d1_ms < end or d1_ms % 180_000):
                raise ValueError("STAGE138_ORPHAN_OR_INVALID_D1_CLOCK")
            c["unique_first_D1"] += 1
            daily[(d1_ms - start) // 86_400_000] += 1
        for m in (2, 5, 10):
            name = f"first_GT{m}x_HIGH_UTC_EVALUATION_ONLY"
            strict = f"D0_first_strict_pre_GT{m}x"
            early = f"D0_first_pre_GT{m}x_5m"
            upgraded = f"D1_first_pre_GT{m}x_5m"
            crossing = labels.get(name)
            if crossing is None:
                if any(labels.get(x) is not False for x in (strict, early, upgraded)):
                    raise ValueError("STAGE138_GROSS_LABEL_WITHOUT_CROSSING")
                continue
            crossing_ms = s131.stamp(crossing)
            if not start <= crossing_ms < end:
                raise ValueError("STAGE138_GROSS_HIGH_OUTSIDE_WINDOW")
            expected = (
                bool(first_d0 is not None and d0_ms < crossing_ms),
                bool(first_d0 is not None and d0_ms + 5 * 60_000 <= crossing_ms),
                bool(first_d1 is not None and d1_ms + 5 * 60_000 <= crossing_ms),
            )
            actual = tuple(labels.get(x) for x in (strict, early, upgraded))
            if actual != expected:
                raise ValueError("STAGE138_GROSS_LABEL_ARITHMETIC_DRIFT")
            c[f"gross_{m}x"] += 1
            c[f"D0_strict_{m}x"] += expected[0]
            c[f"D0_early5_{m}x"] += expected[1]
            c[f"D1_early5_{m}x"] += expected[2]
            c[f"D1_early5_given_D0_{m}x"] += expected[1] and expected[2]
    if sum(c[status] for status in STATES) != c["full_market_attempts"]:
        raise ValueError("STAGE138_LOSSY_POPULATION_STATUS")
    if sum(daily) != c["unique_first_D1"]:
        raise ValueError("STAGE138_D1_DAILY_TOTAL_DRIFT")
    return dict(c), daily


def plan_or_evaluate(packet, archive_root, arrivals=None, *, phase="plan"):
    if phase not in ("plan", "evaluate"):
        raise ValueError("STAGE138_UNKNOWN_PHASE")
    planned = s136.acquire(packet, archive_root, arrivals, fetch_manual=False)
    if planned["mode"] != "OFFLINE_PLAN" or planned["newly_fetched_checksum_verified"] != 0:
        raise ValueError("STAGE138_PLAN_REQUESTED_UNEXPECTED_FETCH")
    start, end = check_window(
        planned["window_utc_start"], planned["window_utc_end_exclusive"])
    base = {
        "schema": SCHEMA, "phase": phase.upper(),
        "new_forward_start_utc": planned["window_utc_start"],
        "new_forward_end_exclusive_utc": planned["window_utc_end_exclusive"],
        "stage133_original_raw_packet_canonical_sha256": planned["stage134_t0_source_sha256"],
        "stage136_offline_source_plan": planned,
        "stage77_frozen_acceptance": FROZEN_THRESHOLDS,
        "original_2026_10_14_0600_stage116": "SOURCE_FAILED_NO_BACKFILL",
        "stage118_127": "REJECTED_UNCHANGED",
        "stage132_gross_first_signal_buy_economics": "NEGATIVE_UNCHANGED",
        "provenance_limits": [
            "T0_PACKAGED_HTTP_BYTES_SELF_CONSISTENT_NOT_INDEPENDENT_ORIGIN",
            "LOCAL_PUBLISHER_ZIP_CHECKSUM_SELF_CONSISTENT_NOT_HTTP_PROVENANCE",
            "CRYPTO_ISSUER_ASOF_IDENTITY_UNVERIFIED",
            "IN_WINDOW_FIRST_LISTING_CENSUS_UNVERIFIED",
            "ARCHIVED_CAUSAL_REPLAY_NOT_REAL_TIME_DELIVERY",
            "EXECUTABLE_NOTIONAL_DEPTH_FEES_EXIT_MISSING",
        ],
        "G0": "PARTIAL", "G1": "NOT_SCORABLE", "G2_G3": "NOT_PASSED",
        "G4": "UNKNOWN", "G5": "NOT_DONE", "G6": "NO_GO",
        "model_buy": "NO_GO", "scheduled_collection": False,
        "Gmail": "OFF", "Frank": "UNCHANGED",
    }
    if phase == "evaluate":
        source = s135.audit(packet, archive_root, arrivals)
        replay = s137.run(packet, archive_root, arrivals)
        if (source["stage133_receipt_packet_SHA256"] !=
                planned["stage134_t0_source_sha256"] or
                replay["stage133_original_packet_sha256"] !=
                source["stage133_receipt_packet_SHA256"] or
                replay["new_forward_start_utc"] != base["new_forward_start_utc"] or
                replay["new_forward_end_exclusive_utc"] != base["new_forward_end_exclusive_utc"]):
            raise ValueError("STAGE138_SOURCE_T0_BRIDGE_DRIFT")
        rows = replay["all_source_population_rows"]
        summary, daily = summarize_rows(rows, start, end)
        if (len(rows) != source["full_market_attempts"] or
                len(rows) != replay["model_attempts_scored_or_classified"] or
                len(rows) != planned["full_initial_venue_symbol_attempts"] +
                             planned["in_window_arrival_candidates_unverified"] or
                summary["full_market_attempts"] != len(rows) or
                summary.get("SOURCE_CENSORED_NO_REPLAY", 0) !=
                    source["source_missing_or_gapped"] or
                summary.get("original_core_source_compatible", 0) !=
                    replay["raw_usdm_venue_descriptive_only"].get(
                        "model_compatible_complete", 0) or
                daily != replay["raw_D1_daily_by_UTC_forward_day"]):
            raise ValueError("STAGE138_CENSUS_OR_CORE_REPLAY_DISAGREEMENT")
        for symbol_row, source_row in zip(rows, source["per_symbol_source_audit"]):
            if (symbol_row["symbol_exact"] != source_row["symbol_exact"] or
                    symbol_row["population_lane"] != source_row["population_lane"] or
                    symbol_row["original_archive_source_status"] != source_row["source_status"] or
                    symbol_row["covered_minute_count"] != source_row["observed_minute_count"]):
                raise ValueError("STAGE138_POPULATION_SOURCE_ROW_DRIFT")
        base.update({
            "stage135_source_audit": source,
            "stage137_unmodified_core_replay": replay,
            "population_rows": rows,
            "population_summary": summary,
            "raw_D1_daily": daily,
            "original_unmodified_V4_git_blob": replay["original_unmodified_V4_git_blob"],
            "original_stage80_contract_sha": replay["original_unmodified_stage80_contract_sha"],
            "raw_venue_research_only_2x": {
                "gross_2x": summary.get("gross_2x", 0),
                "D0_strict_pre_2x": summary.get("D0_strict_2x", 0),
                "D0_early5_pre_2x": summary.get("D0_early5_2x", 0),
                "D1_early5_pre_2x": summary.get("D1_early5_2x", 0),
                "complete_preexisting_core_compatible": summary.get(
                    "original_core_source_compatible", 0),
                "denominator_not_point_in_time_crypto": True,
            },
            "hypothetical_model_replay_is_not_G0_G1_proof": True,
        })
    base["manifest_self_consistency_sha256_NOT_ATTESTATION"] = canonical_hash(base)
    return base


def verify_evaluate_manifest(report):
    if not isinstance(report, dict) or report.get("schema") != SCHEMA or report.get("phase") != "EVALUATE":
        raise ValueError("STAGE138_AGGREGATE_REQUIRES_EVALUATE_MANIFESTS")
    digest = report.get("manifest_self_consistency_sha256_NOT_ATTESTATION")
    unsealed = {k: v for k, v in report.items()
                if k != "manifest_self_consistency_sha256_NOT_ATTESTATION"}
    if digest != canonical_hash(unsealed):
        raise ValueError("STAGE138_MANIFEST_SELF_HASH_MISMATCH")
    start, end = check_window(
        report.get("new_forward_start_utc"),
        report.get("new_forward_end_exclusive_utc"))
    rows = report.get("population_rows")
    summary, daily = summarize_rows(rows, start, end)
    source, replay, planned = (
        report.get("stage135_source_audit"),
        report.get("stage137_unmodified_core_replay"),
        report.get("stage136_offline_source_plan"))
    if any(not isinstance(x, dict) for x in (source, replay, planned)):
        raise ValueError("STAGE138_MISSING_SOURCE_PROVENANCE_CHAIN")
    if (summary != report.get("population_summary") or
            daily != report.get("raw_D1_daily") or
            daily != replay.get("raw_D1_daily_by_UTC_forward_day") or
            len(rows) != replay.get("model_attempts_scored_or_classified") or
            len(rows) != source.get("full_market_attempts") or
            len(rows) != planned.get("full_initial_venue_symbol_attempts", -1) +
                          planned.get("in_window_arrival_candidates_unverified", -1) or
            source.get("stage133_receipt_packet_SHA256") !=
                report.get("stage133_original_raw_packet_canonical_sha256") or
            replay.get("stage133_original_packet_sha256") !=
                report.get("stage133_original_raw_packet_canonical_sha256") or
            report.get("original_unmodified_V4_git_blob") !=
                s137.v4.ORIGINAL_V4_GIT_BLOB or
            report.get("original_stage80_contract_sha") !=
                s137.d1.CONTRACT_SHA or
            report.get("original_unmodified_V4_git_blob") !=
                replay.get("original_unmodified_V4_git_blob") or
            report.get("original_stage80_contract_sha") !=
                replay.get("original_unmodified_stage80_contract_sha") or
            any(report.get(k) != v for k, v in GATES.items()) or
            report.get("model_buy") != "NO_GO" or
            report.get("scheduled_collection") is not False):
        raise ValueError("STAGE138_FORGED_OR_DRIFTED_EVALUATE_COUNTERS")
    return start, end, summary, daily


def aggregate(reports):
    if not reports:
        raise ValueError("STAGE138_NO_WINDOW_MANIFESTS")
    checked = [(verify_evaluate_manifest(r), r) for r in reports]
    checked.sort(key=lambda pair: pair[0][0])
    seen_t0 = set()
    windows = []
    all_counts = Counter()
    daily_all = []
    prior_end = None
    for (start, end, summary, days), report in checked:
        t0_digest = report["stage133_original_raw_packet_canonical_sha256"]
        if t0_digest in seen_t0 or prior_end is not None and start < prior_end:
            raise ValueError("STAGE138_DUPLICATE_OR_OVERLAPPING_FORWARD_WINDOW")
        seen_t0.add(t0_digest)
        prior_end = end
        all_counts.update(summary)
        daily_all.extend(days)
        windows.append({
            "start_utc": report["new_forward_start_utc"],
            "end_exclusive_utc": report["new_forward_end_exclusive_utc"],
            "stage133_packet_sha256_not_origin_proof": t0_digest,
            "raw_venue": summary,
            "censored_count": summary.get("SOURCE_CENSORED_NO_REPLAY", 0),
            "D1_by_forward_UTC_day": days,
            "NOT_INDEPENDENTLY_VERIFIABLE_FROM_MANIFEST": True,
        })
    aggregate_count = sum(all_counts[k] for k in STATES)
    if aggregate_count != all_counts["full_market_attempts"]:
        raise ValueError("STAGE138_AGGREGATE_POPULATION_LOSS")
    raw_2x = all_counts.get("gross_2x", 0)
    n_days = len(daily_all)
    def pct(n, d):
        return round(100 * n / d, 3) if d else None
    result = {
        "schema": AGG_SCHEMA, "input_manifests_count": len(reports),
        "declared_disjoint_window_count_not_verified_as_external_market_source": len(windows),
        "stage77_frozen_acceptance": FROZEN_THRESHOLDS,
        "per_window_source_retained": windows,
        "all_original_venue_population_descriptive_only": dict(all_counts),
        "raw_venue_replay_rate_diagnostics_NOT_crypto_accuracy": {
            "mixed_venue_2x_HIGH_with_source": raw_2x,
            "D0_strict_2x_pct_mixed_venue": pct(all_counts.get("D0_strict_2x", 0), raw_2x),
            "D0_early5_2x_pct_mixed_venue": pct(all_counts.get("D0_early5_2x", 0), raw_2x),
            "D1_early5_pct_of_D0_early5_mixed_venue": pct(
                all_counts.get("D1_early5_given_D0_2x", 0),
                all_counts.get("D0_early5_2x", 0)),
            "D1_per_day_mean_mixed_venue": round(sum(daily_all)/n_days, 4),
            "D1_per_day_peak_mixed_venue": max(daily_all),
            "cannot_measure_issuer_confirmed_crypto_true_positives": True,
            "cannot_measure_real_time_alert_delivery": True,
            "cannot_measure_executable_net_profit": True,
        },
        "independent_evidence_NOT_PROVEN_by_saved_manifests": [
            "ORIGINAL_HTTP_ENDPOINT_SOURCE_INDEPENDENCE",
            "ORIGINAL_ZIP_EXTERNAL_SOURCE_ORIGIN",
            "PIT_CRYPTO_ISSUER_IDENTITY_AND_FULL_NEW_LISTING_CENSUS",
            "LIVE_D0_ALERT_AND_D1_DELIVERY_DELAY",
            "G4_EXECUTABLE_BUY_SELL_NOTIONAL_COSTS_EXITS",
            "INDEPENDENT_OTHER_AI_REVIEW",
        ],
        "old_stage116_2026_10_14_0600": "SOURCE_FAILED_NO_BACKFILL",
        **GATES, "model_buy": "NO_GO",
        "scheduled_collection": False, "Gmail": "OFF", "Frank": "UNCHANGED",
    }
    result["manifest_self_consistency_sha256_NOT_ATTESTATION"] = canonical_hash(result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--t0", type=Path)
    p.add_argument("--archive-root", type=Path)
    p.add_argument("--arrival-candidates", type=Path)
    p.add_argument("--phase", choices=("plan", "evaluate"), default="plan")
    p.add_argument("--aggregate", type=Path, nargs="+")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.aggregate is not None:
        if a.t0 is not None or a.archive_root is not None or a.arrival_candidates is not None:
            p.error("--aggregate excludes --t0, --archive-root, --arrival-candidates")
        manifests = [json.loads(x.read_text(encoding="utf-8")) for x in a.aggregate]
        result = aggregate(manifests)
    else:
        if a.t0 is None or a.archive_root is None:
            p.error("explicit --t0 and --archive-root required; default mode is offline PLAN")
        packet = json.loads(a.t0.read_text(encoding="utf-8"))
        arrivals = json.loads(a.arrival_candidates.read_text(encoding="utf-8")
                            ) if a.arrival_candidates else None
        result = plan_or_evaluate(
            packet, a.archive_root, arrivals, phase=a.phase)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print(json.dumps({
        "schema": result["schema"],
        "phase": result.get("phase", "OFFLINE_AGGREGATION"),
        "windows": result.get("input_manifests_count", 1),
        "G0": result["G0"], "G1": result["G1"], "G6": result["G6"],
        "model_buy": result["model_buy"],
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
