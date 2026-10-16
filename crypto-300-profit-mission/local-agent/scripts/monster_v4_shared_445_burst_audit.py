#!/usr/bin/env python3
"""Source-pinned causal WATCH/queue postmortem; never a trading backtest.

Consumes genuine one-SQLite 445 full JSON from immutable Actions Artifact
12044872933 and its companion summary, not injected Stage28 queue events.
No market access, no production code import, no side effects beyond --out.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

SCHEMA = "MONSTER_FEB445_ACTUAL_D0_BURST_QUEUE_CAUSAL_AUDIT_V1"
FULL_JSON_SHA256 = "370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf"
TICK_MS = 3 * 60_000
DEADLINE_MS = 15 * 60_000
D1_SLOTS = 8
IMMUTABLE_CODE_BLOBS = {
    "monster_v4_shadow.py": "bc958b3d90a8a52afa51515cb53f7e5fafaffaaa",
    "monster_v4_shared_spot_d0_d1_original_core.py":
        "3a9e4bbd75ff4f5ef6cd0bfe87895d932c95892c",
    "monster_v4_shared_d1_zeroquote_research_v2.py":
        "b16e89f2a20c1dfaaebce1497da8d991d3907ed7",
}


def verify_immutable_model_code():
    source_dir = Path(__file__).resolve().parent
    for filename, expected_git_blob in IMMUTABLE_CODE_BLOBS.items():
        raw = (source_dir / filename).read_bytes()
        git_blob_sha = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw
        ).hexdigest()
        if git_blob_sha != expected_git_blob:
            raise ValueError("MONSTER445_BURST_FROZEN_PRODUCTION_CODE_BLOB_DRIFT")
    return IMMUTABLE_CODE_BLOBS


def iso_utc(milliseconds: int) -> str:
    return (datetime.fromtimestamp(milliseconds / 1000, timezone.utc)
            .isoformat().replace("+00:00", "Z"))


def assess(full_bytes: bytes, summary: dict) -> dict:
    verified_model_code_blobs = verify_immutable_model_code()
    digest = hashlib.sha256(full_bytes).hexdigest()
    if digest != FULL_JSON_SHA256 or summary.get("full_replay_json_sha256") != digest:
        raise ValueError("MONSTER445_BURST_IMMUTABLE_FULL_REPLAY_SHA_MISMATCH")
    source = json.loads(full_bytes)
    if (source.get("actually_complete_symbols") != 445
            or source.get("one_shared_sqlite_for_all_symbols") is not True
            or source.get("execution_counts", {}).get("polls") != 3360
            or source.get("production_D0_unchanged") is not True
            or source.get("D1_model_semantics") != "RESEARCH_V2_SOURCE_UNSUPPORTED_ZEROQUOTE"
            or source.get("all445_original_production_D1_completed") is not False
            or source.get("not_independent_OOS") is not True
            or source.get("not_real_PIT_listing") is not True
            or source.get("true_full_758_replay") is not False
            or source.get("G6") != "NO_GO"):
        raise ValueError("MONSTER445_BURST_REPLAY_IDENTITY_OR_SCOPE_DRIFT")
    events = source["events"]
    queue = source["queue_rows"]
    event_counts = Counter(e["event_type"] for e in events)
    status_counts = Counter(q["status"] for q in queue)
    if (len({e["event_id"] for e in events}) != len(events)
            or dict(event_counts) != source["event_type_counts"]
            or dict(status_counts) != source["queue_status_counts"]
            or len(queue) != 269
            or event_counts["WATCH_EARLY"] != 269
            or source["execution_counts"]["D0_watch_new"] != 269
            or source["D1_max_selected_slots_one_tick"] != D1_SLOTS
            or sum(status_counts.values()) != 269):
        raise ValueError("MONSTER445_BURST_EVENT_QUEUE_ACCOUNTING_DRIFT")
    watches = [e for e in events if e["event_type"] == "WATCH_EARLY"]
    identities = [(e["symbol"], e["observed_ms"]) for e in watches]
    queue_ids = [(q["symbol"], q["first_seen_ms"]) for q in queue]
    if len(set(identities)) != len(watches) or set(queue_ids) != set(identities):
        raise ValueError("MONSTER445_BURST_WATCH_QUEUE_IDENTITY_MISMATCH")
    if any(q["deadline_ms"] - q["first_seen_ms"] != DEADLINE_MS for q in queue):
        raise ValueError("MONSTER445_BURST_DEADLINE_CONTRACT_DRIFT")
    peaks = Counter(e["observed_ms"] for e in watches)
    peak_ms, peak_n = peaks.most_common(1)[0]
    if peak_n != 98 or iso_utc(peak_ms) != "2026-02-06T00:36:00Z":
        raise ValueError("MONSTER445_BURST_FROZEN_TRUE_PEAK_NOT_REPRODUCED")
    peak_watches = [e for e in watches if e["observed_ms"] == peak_ms]
    triggers = Counter()
    for e in peak_watches:
        payload = json.loads(e["payload"])
        for key in ("trigger_3m_5pct", "trigger_15m_8pct", "trigger_60m_15pct"):
            if payload.get(key) is True:
                triggers[key] += 1
    if triggers["trigger_15m_8pct"] != 96 or triggers["trigger_3m_5pct"] != 2:
        raise ValueError("MONSTER445_BURST_PEAK_TRIGGER_RECONCILIATION_DRIFT")
    peak_candidates = [q for q in queue if q["first_seen_ms"] == peak_ms]
    nearby_candidates = [q for q in queue if peak_ms < q["first_seen_ms"] <= peak_ms + TICK_MS]
    peak_statuses = Counter(q["status"] for q in peak_candidates)
    late_outside_peak = sorted(
        (q["symbol"], q["first_seen_ms"]) for q in queue
        if q["status"] == "LATE" and q["first_seen_ms"] != peak_ms)
    if (peak_statuses != {"LATE": 91, "EVALUATED": 7}
            or len(late_outside_peak) != 2
            or [s for s, _ in late_outside_peak] != ["GPSUSDT", "LUNAUSDT"]
            or any(t != peak_ms + TICK_MS for _, t in late_outside_peak)):
        raise ValueError("MONSTER445_BURST_91_93_LATE_ATTRIBUTION_DRIFT")
    setup_events = [e for e in events if e["event_type"] == "SETUP_ACTIVE"]
    if len(setup_events) != 120:
        raise ValueError("MONSTER445_BURST_SETUP_EVENT_COUNT_DRIFT")
    setup_by_event_id = {e["event_id"]: e for e in setup_events}
    setup_matched = 0
    for q in queue:
        eid = hashlib.sha256(
            f"MONSTER_V4|{q['venue']}|{q['symbol']}|SETUP_ACTIVE|{q['id']}".encode()
        ).hexdigest()
        if eid not in setup_by_event_id:
            continue
        e = setup_by_event_id[eid]
        if (q["status"]!="EVALUATED"
                or e["venue"]!=q["venue"] or e["symbol"]!=q["symbol"]
                or not q["first_seen_ms"]<=e["observed_ms"]<=q["deadline_ms"]):
            raise ValueError("MONSTER445_BURST_SETUP_QUEUE_ANCHOR_OR_WINDOW_DRIFT")
        setup_matched += 1
    if setup_matched != len(setup_events) or setup_matched != 120:
        raise ValueError("MONSTER445_BURST_SETUP_EXACT_QUEUE_ID_INCOMPLETE")
    lates = [e for e in events if e["event_type"] == "LATE_REVIEW"]
    late_by_event_id = {e["event_id"]: e for e in lates}
    anchored_lates = []
    for q in queue:
        eid = hashlib.sha256(
            f"MONSTER_V4|{q['venue']}|{q['symbol']}|LATE_REVIEW|{q['id']}".encode()
        ).hexdigest()
        if eid not in late_by_event_id:
            continue
        e = late_by_event_id[eid]
        if (q["status"]!="LATE" or e["venue"]!=q["venue"]
                or e["symbol"]!=q["symbol"] or e["observed_ms"]<=q["deadline_ms"]):
            raise ValueError("MONSTER445_BURST_LATE_QUEUE_ANCHOR_OR_WINDOW_DRIFT")
        anchored_lates.append((q,e))
    if len(anchored_lates)!=len(lates) or len(lates)!=93:
        raise ValueError("MONSTER445_BURST_LATE_EXACT_QUEUE_ID_INCOMPLETE")
    peak_late_events = [e for q,e in anchored_lates
                        if q["first_seen_ms"] == peak_ms]
    late_event_lags = Counter((e["observed_ms"] - peak_ms) // 60_000
                              for e in peak_late_events)
    if sum(late_event_lags.values()) != 91 or min(late_event_lags) < 18:
        raise ValueError("MONSTER445_BURST_LATE_EVENT_TIME_DRIFT")
    # Pure capacity ceiling, NOT a hypothetical win rate or an executable
    # counterfactual. Inclusive ticks 0,3,6,9,12,15 -> six selections.
    ideal_max_slots = (DEADLINE_MS // TICK_MS + 1) * D1_SLOTS
    return {
        "schema": SCHEMA,
        "immutable_full_json_sha256": digest,
        "one_sqlite_original_D0_experimental_D1": True,
        "verified_model_code_git_blobs": verified_model_code_blobs,
        "setup_event_matching": "PRODUCTION_EVENT_KEY_SHA256_EXACT_QUEUE_ID",
        "late_event_matching": "PRODUCTION_EVENT_KEY_SHA256_EXACT_QUEUE_ID",
        "D1_market_zero_quote_is_real_no_trade_not_missing_data": True,
        "D1_research_V2_zero_quote_terminal_is_market_condition": True,
        "D1_research_D1_rates_conditional_on_market_quote_presence": True,
        "D1_original_validates_positive_quote_for_all_8_supplied_candles":
            True,
        "D1_original_selects_last6_only_after_8_candle_positive_validation":
            True,
        "frozen_historical_date": "2026-02-04",
        "source_complete_symbols": 445,
        "original_denominator": 758,
        "historical_censored": 313,
        "global_polls": 3360,
        "total_watches": len(watches),
        "peak_utc": iso_utc(peak_ms),
        "peak_same_tick_watch": peak_n,
        "peak_15m_trigger_count": triggers["trigger_15m_8pct"],
        "peak_3m_trigger_count": triggers["trigger_3m_5pct"],
        "peak_queue_statuses": dict(peak_statuses),
        "peak_related_late": peak_statuses["LATE"],
        "other_late_within_next_3m": [s for s, _ in late_outside_peak],
        "overall_late": status_counts["LATE"],
        "overall_late_share_pct": round(100 * status_counts["LATE"] / len(queue), 4),
        "late_from_peak_share_pct": round(100 * peak_statuses["LATE"] / status_counts["LATE"], 4),
        "late_event_utc_minute_offsets_after_peak": dict(sorted(late_event_lags.items())),
        "D1_per_tick_original_capacity": D1_SLOTS,
        "D1_research_max_selected_slots": source["D1_max_selected_slots_one_tick"],
        "candidate_deadline_minutes": DEADLINE_MS // 60_000,
        "theoretical_inclusive_polls_before_deadline": DEADLINE_MS // TICK_MS + 1,
        "theoretical_max_one_pass_slots_for_peak_with_zero_competition": ideal_max_slots,
        "theoretical_min_peak_not_one_pass_served_by_deadline": max(0, peak_n-ideal_max_slots),
        "setup_event_count": len(setup_events),
        "watch_episodes_with_setup_in_15m": setup_matched,
        "D1_zeroquote_terminal": status_counts["SOURCE_UNSUPPORTED_D1_ZERO_QUOTE"],
        "original_445_D1_replay_completed": False,
        "historical_PIT_listing": "UNVERIFIED",
        "historical_executable_net_profit": "UNVERIFIED",
        "independent_OOS": False,
        "G4": "UNKNOWN", "G6": "NO_GO"
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("MONSTER445_BURST_REPORT_MUST_NOT_OVERWRITE")
    result = assess(args.full.read_bytes(), json.loads(args.summary.read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print("MONSTER445_TRUE_BURST_CAUSAL_AUDIT_RESEARCH_ONLY",
          json.dumps({k: result[k] for k in ("total_watches","peak_same_tick_watch",
                "peak_related_late","overall_late","setup_event_count",
                "theoretical_min_peak_not_one_pass_served_by_deadline",
                "G6")},sort_keys=True))


if __name__ == "__main__":
    main()
