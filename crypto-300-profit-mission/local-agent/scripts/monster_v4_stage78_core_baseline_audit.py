#!/usr/bin/env python3
"""Read-only, source-pinned Monster D0/D1 baseline audit. No network/trading/Gmail."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PINNED = {
    "monster_stage34_18date_discovery_census_verified.json": "b7501f5ee504833b60efa4504183a4d233dd8bb8",
    "monster_stage35_18date_SHA_verified_first_watch_feature_summary.json": "95d6d435be98cbe6bf7b694861fcc7bb7646b869",
    "monster_stage39_36original_SHA_all5400_futures_discovery_summary.json": "d4dae1d2a2cd4e43bd8f1cb0fcb16b0724240080",
    "monster_stage52_pinned_v03_all5400_36SHA_true_global_cap_metrics.json": "42d455a6cc9d0164a8dd94aa12a475bad5ed126e",
    "monster_stage66_new3_full2700_global_cap5_firstD0_vs_P1v03_summary.json": "6c5cb45c23e57c3e4e1e844efe16b5af46cbd9b3",
    "monster_stage70_offline_sqlite_watch_projection_summary.json": "79a10a59e36ebe0e8240c5deb2f21e182cef018f",
    "monster_stage74_original196_spot_trading_source_summary.json": "d7ab49a3bcb994129677e9c3b2e57df87cdc7e74",
    "monster_stage75_original95_four_quote_spot_source_summary.json": "13380febf0d03816bf9e7a1581055cfc05fcb595",
}
LABELS = ("spot34", "spot35", "usd39", "usd52", "usd66", "sqlite70", "spot74", "spot75")


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def require_equal(label: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise ValueError(f"{label}: {actual!r} != {expected!r}")


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0 or numerator < 0 or numerator > denominator:
        raise ValueError("INVALID_RATIO")
    return round(100.0 * numerator / denominator, 4)


def audit(evidence: Path) -> dict:
    tables = {}
    source_blobs = {}
    for label, (filename, expected_sha) in zip(LABELS, PINNED.items()):
        raw = (evidence / filename).read_bytes()
        actual_sha = git_blob_sha(raw)
        require_equal("GIT_BLOB_SHA:" + filename, actual_sha, expected_sha)
        tables[label] = json.loads(raw)
        source_blobs[label] = actual_sha

    s34, s35, u39, u52, u66, j70, s74, s75 = (tables[k] for k in LABELS)
    a = s34["overall"]
    require_equal("spot34.attempts", a["attempted"], s34["attempted"])
    require_equal("spot34.valid", a["complete"], s34["source_verified_complete"])
    require_equal("spot34.population", a["complete"] + a["censored_source"], a["attempted"])
    require_equal("spot34.gt2_partition", a["2x_early_strict"] + a["2x_late"] +
                  a["2x_no_watch"] + a["2x_same_minute_not_early"], a["gt2x"])
    require_equal("spot34.watch_partition", a["2x_early_strict"] + a["2x_late"] +
                  a["watch_and_not_2x_under_calendar_label"], a["watch_symbol_dates"])
    require_equal("spot34.full_partition", a["watch_symbol_dates"] +
                  a["no_watch_and_not_2x_under_calendar_label"] + a["2x_no_watch"], a["complete"])
    require_equal("spot35.watch_cohort", s35["watch_cases"], a["watch_symbol_dates"])
    require_equal("spot35.early_cohort", s35["first_watch_strictly_pre_2x"], a["2x_early_strict"])
    require_equal("spot35.other_watch_cohort", s35["first_watch_non_2x"],
                  a["watch_and_not_2x_under_calendar_label"])

    require_equal("usd39.source_partition", u39["publisher_1m_and_1h_agree_full"] +
                  u39["source_censored_total"], u39["full_stage37_hourly_source_attempts"])
    require_equal("usd39.gt2", u39["gt2x_early_strict"] + u39["gt2x_late_watch"] +
                  u39["gt2x_same_minute_not_early"] + u39["gt2x_no_watch"], u39["gt2x_full_source"])
    require_equal("usd39.source_valid", u39["full_NOT2x_source_complete"] +
                  u39["gt2x_full_source"], u39["publisher_1m_and_1h_agree_full"])
    require_equal("usd39.dates", sum(d["attempted"] for d in u39["per_date"]),
                  u39["full_stage37_hourly_source_attempts"])
    require_equal("usd39.watch_cohort", sum(d["distinct_WATCH_coin_dates"] for d in u39["per_date"]),
                  u39["all_source_complete_with_any_WATCH_coin_dates"])

    require_equal("usd52.source_valid", u52["publisher_1h_and_1m_valid"],
                  sum(d["valid"] for d in u52["all_date_stats"]))
    require_equal("usd52.urgency_partition", u52["P1v03_budget_delivered"] +
                  u52["P1v03_over_budget"], u52["P1v03_unbudgeted_candidates"])
    require_equal("usd52.retention_gate_failed", u52["frozen_gates"][
                  "global_budgeted_P1v03_retain_D0_5min_early2x_ge80pct"], False)
    require_equal("usd52.verdict", u52["verdict"], "REJECTED_P1V03_FROZEN_GATE")
    require_equal("usd66.attempts", sum(d["attempted"] for d in u66["per_date"]),
                  u66["original_all_archive_attempted"])
    require_equal("usd66.valid", sum(d["minute_source_verified"] for d in u66["per_date"]),
                  u66["original_1m_and_1h_source_valid"])
    require_equal("usd66.underpowered", u66["quality_gates"]["minimum_20_source_valid_2x"], False)
    require_equal("usd66.retention_failed", u66["quality_gates"][
                  "new_first5_retains_80pct_original_D0_early5_2x"], False)

    require_equal("sqlite70.journal", j70["unique_first_D0_watch"] + j70["P1_upgraded"],
                  j70["journal_events"])
    require_equal("sqlite70.watch", sum(j70["stage_counts"].values()),
                  j70["unique_first_D0_watch"])
    require_equal("sqlite70.upgrades", j70["stage_counts"]["URGENT_RESEARCH"] +
                  j70["stage_counts"]["CAP_DEFERRED_RESEARCH"], j70["P1_upgraded"])

    require_equal("spot74.states", sum(s74["states_total"].values()),
                  s74["all_frozen_original_D0_signal_count"])
    verified = s74["states_total"]["SPOT_PRIOR_MINUTE_TRADES_VERIFIED"]
    not_verified = s74["all_frozen_original_D0_signal_count"] - verified
    require_equal("spot75.remaining", not_verified,
                  s75["all95"]["all_original_D0_without_USDT_1m_prior_trade"])
    require_equal("spot75.four_pairs", s75["all95"]["four_alt_quote_pair_test_attempts"],
                  not_verified * 4)
    for quote, states in s75["all95"]["per_quote_alternative_pair_status"].items():
        require_equal("spot75." + quote, sum(states.values()), not_verified)
    require_equal("spot75.any_verified", s75["all95"]["any_of_four_alt_quote_assets_positive"], 0)

    return {
        "schema": "MONSTER_STAGE78_PINNED_CORE_MODEL_EVIDENCE_AUDIT_V1",
        "source_git_blob_sha": source_blobs,
        "historical_exposed_not_forward_validated": True,
        "spot_original_v4": {
            "attempted": a["attempted"], "valid": a["complete"],
            "source_censored": a["censored_source"], "gt2x": a["gt2x"],
            "early_strict": a["2x_early_strict"],
            "early_5m": a["early_lead_at_least_5min"],
            "early_strict_pct": ratio(a["2x_early_strict"], a["gt2x"]),
            "early_5m_pct": ratio(a["early_lead_at_least_5min"], a["gt2x"]),
            "watch_coin_dates": a["watch_symbol_dates"],
            "watch_non_anchor_2x": a["watch_and_not_2x_under_calendar_label"],
            "watch_non_anchor_2x_pct": ratio(
                a["watch_and_not_2x_under_calendar_label"], a["watch_symbol_dates"]),
        },
        "usdm_original_v4": {
            "attempted": u39["full_stage37_hourly_source_attempts"],
            "valid": u39["publisher_1m_and_1h_agree_full"],
            "censored": u39["source_censored_total"], "gt2x": u39["gt2x_full_source"],
            "early_strict": u39["gt2x_early_strict"],
            "early_5m": u39["nearest_strict_pre_cross_ge5_min"],
            "early_strict_pct": ratio(u39["gt2x_early_strict"], u39["gt2x_full_source"]),
            "early_5m_pct": ratio(u39["nearest_strict_pre_cross_ge5_min"], u39["gt2x_full_source"]),
            "watch_coin_dates": u39["all_source_complete_with_any_WATCH_coin_dates"],
            "watch_non_anchor_2x": u39["full_NOT2x_with_WATCH_coin_dates"],
            "watch_non_anchor_2x_pct": ratio(u39["full_NOT2x_with_WATCH_coin_dates"],
                                             u39["all_source_complete_with_any_WATCH_coin_dates"]),
        },
        "p1v03": {"valid": u52["publisher_1h_and_1m_valid"],
                  "d0_pre5_gt2x": u52["D0_early_ge5min_GT2x"],
                  "urgent_pre5_gt2x": u52["P1v03_budgeted_early_ge5min_GT2x_from_D0_pre5"],
                  "retention_pct": ratio(u52["P1v03_budgeted_early_ge5min_GT2x_from_D0_pre5"],
                                         u52["D0_early_ge5min_GT2x"]),
                  "verdict": u52["verdict"]},
        "first5": {"valid": u66["original_1m_and_1h_source_valid"],
                   "d0_pre5_gt2x": u66["original_D0_at_least_5m_pre2x"],
                   "urgent_pre5_gt2x": u66["new_first5_early5_gt2x"],
                   "retention_pct": ratio(u66["new_first5_early5_gt2x"],
                                          u66["original_D0_at_least_5m_pre2x"]),
                   "verdict": "REJECTED_AND_UNDERPOWERED_FROM_STAGE67"},
        "read_only_journal": {"watch": j70["unique_first_D0_watch"],
                              "upgrades": j70["P1_upgraded"], "journal": j70["journal_events"]},
        "original196_spot": {"trades_verified_tminus1": verified, "other_unknown": not_verified,
                             "four_quote_additional_trades_verified": 0},
        "candidate_new_strategy": "NOT_DESIGNED",
        "independent_oos": "NOT_DONE", "real_executable_net_pnl": "UNKNOWN",
        "deployment": "NO_GO", "gmail": "OFF", "autotrade": "NO_GO",
        "frank": "UNCHANGED", "order_notional": "UNSPECIFIED",
    }


def selftest() -> None:
    require_equal("ratio", ratio(2, 5), 40.0)
    try:
        ratio(3, 2)
    except ValueError:
        pass
    else:
        raise AssertionError("INVALID_RATIO_NOT_REJECTED")
    try:
        require_equal("tampered", 1, 2)
    except ValueError:
        pass
    else:
        raise AssertionError("TAMPER_NOT_REJECTED")
    require_equal("git_blob", git_blob_sha(b"test"),
                  hashlib.sha1(b"blob 4\0test").hexdigest())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, default=Path(__file__).resolve().parents[2] /
                        "monster" / "evidence")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        print("STAGE78_SELFTEST_PASS")
        return 0
    result = audit(args.evidence)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
