#!/usr/bin/env python3
"""Compute (never assert via hardcoded True) author-side first518 equality gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "MONSTER_FIRST518_SPLIT1018_SOURCE_AND_COMPUTED_EVIDENCE_V2"
NAME = "monster_first518_split1018_sha_validated_computed_comparison_v2_20261019.json"
EVIDENCE = Path(__file__).resolve().parents[2] / "monster/evidence"
FIELDS = ("WATCH_event_identity", "SETUP_event_identity",
          "D0_D1_totals", "event_type_counts", "queue_status_counts")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def hashfile(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def report(index, bridge, economics, earlier_bridge, earlier_economics,
           earlier_operator, *, run_input_commit):
    assert index["schema"] == "MONSTER_FIRST518_OCT16_17_ORIGINAL_1018_SPLIT_FOR_INDEPENDENT_AUDIT_V1"
    comparison = {
        "replay_events_identical_to_pre_fix":
            all(bridge[k] == earlier_bridge[k] for k in FIELDS),
        "economics_8_8_all_horizons_identical_to_pre_fix":
            economics["both_alternative_non_combined_signal_views"]
            == earlier_economics["both_alternative_non_combined_signal_views"]
            and economics["paired_SETUP_after_WATCH_delay_minutes"]
            == earlier_economics["paired_SETUP_after_WATCH_delay_minutes"],
        "operator_snapshot_identical_to_previous_archive":
            bridge["operator_readonly_from_same_original_D0_D1_SQLite"]
            == earlier_operator["operator_snapshot"],
        "original_1533_full_source_verified_from_shards":
            index["total_verified_issuer_pairs"] == 1018
            and bridge["publisher_verified_zip_checksum_pairs"] == 1533
            and bridge["publisher_verified_closed_1m_bars"] == 2_207_520
            and economics["original_artifact_name_pairs_verified_here"] == 1533
            and economics["signal_symbol_days_publisher_sha_reverified_here"] == 24,
        "all_8_early_watches_and_8_setups":
            bridge["event_type_counts"].get("WATCH_EARLY") == 8
            and bridge["event_type_counts"].get("SETUP_ACTIVE") == 8,
        "all_8_expired_d2_not_captured_no_buy":
            bridge["operator_readonly_from_same_original_D0_D1_SQLite"]["window_total"] == 8
            and all(x["signal"] == "EXPIRED" and x["d2_status"] == "NOT_CAPTURED"
                    and x["recommendation"] == "RESEARCH_REVIEW_ONLY_NO_BUY"
                    for x in bridge["operator_readonly_from_same_original_D0_D1_SQLite"]["opportunities"]),
    }
    if not all(comparison.values()):
        raise ValueError("MONSTER_AUDIT_COMPUTED_COMPARISON_FAILED:" + repr(comparison))
    return {
        "schema": SCHEMA,
        "fixed_code_input_commit": run_input_commit,
        "old_Codex_audit_commit": "eed4ea67e7868770367fbacffc1e9058ce59b635",
        "original_artifact_id": 12167818438,
        "original_1018_daily_issuer_zip_checksum_pairs_repacked": index["total_verified_issuer_pairs"],
        "all_1533_daily_issuer_zip_checksum_pairs_replayed": bridge["publisher_verified_zip_checksum_pairs"],
        "minute_rows": bridge["publisher_verified_closed_1m_bars"],
        "shard_manifest_sha256": index["shard_manifest_sha256"],
        "shard_pair_counts": index["shard_pair_counts"],
        "shard_artifact_prefix": "monster-first518-issuer-original1018-shard-",
        "computed_from_actual_JSON_field_comparisons": comparison,
        "independent_Codex_replay": "NOT_DONE",
        "not_current_live_market": True,
        "historical_24h_ticker_reconstructed_not_actual": True,
        "G0": "PARTIAL", "G4": "UNKNOWN", "G6": "NO_GO",
        "NO_MERGE": True, "NO_DEPLOY": True, "NO_GMAIL": True, "NO_TRADE": True,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-index", type=Path, required=True)
    ap.add_argument("--bridge", type=Path, required=True)
    ap.add_argument("--economics", type=Path, required=True)
    ap.add_argument("--fixed-commit", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = report(
        read(args.shard_index), read(args.bridge), read(args.economics),
        read(EVIDENCE / "monster_forward_spot511_first518_official_minute_causal_fifo8_actual_v1.json"),
        read(EVIDENCE / "monster_forward_spot511_first518_8watch_8setup_fixed_horizons_actual_v1.json"),
        read(EVIDENCE / "monster_first518_real_operator_d0_d1_d2_no_buy_research_p2_fixed_v1.json"),
        run_input_commit=args.fixed_commit,
    )
    if args.out.exists():
        raise ValueError("MONSTER_AUDIT_RESULT_ALREADY_EXISTS")
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2,
                                   ensure_ascii=False) + "\n")
    print("MONSTER_1018_SHARDS_COMPUTED_COMPARISON_PASS",
          json.dumps(result["computed_from_actual_JSON_field_comparisons"],
                     sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
