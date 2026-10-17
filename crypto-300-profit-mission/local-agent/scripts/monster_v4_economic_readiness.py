#!/usr/bin/env python3
"""Cross-cohort evidence-based Monster economic NO_GO check; no trading.

Reconciles previously exposed, separately sampled Stage30 and Stage152 research.
Never joins their trades or interprets old price proxies as actual fills.
"""
import argparse
import hashlib
import json
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[2] / "monster" / "evidence"
STAGE30 = "monster_stage30_six_new_dates_758x6_real_profit_and_GT_AUDITED_20261011.json"
STAGE152 = "monster_stage152_original305_integrity_and_economics_summary.json"
BLOBS = {
    STAGE30: "9b73bb711ed498192c1407286eb2304538876344",
    STAGE152: "518e7aa0d8db83fd1b818513ae7e72b165252806",
}
SCHEMA = "MONSTER_ECONOMIC_READINESS_CROSS_COHORT_NO_GO_V1"


def source(evidence_dir, filename):
    raw = (Path(evidence_dir) / filename).read_bytes()
    header = ("blob " + str(len(raw)) + "\0").encode()
    if hashlib.sha1(header + raw).hexdigest() != BLOBS[filename]:
        raise ValueError("ECONOMIC_EVIDENCE_SOURCE_BLOB_DRIFT:" + filename)
    return json.loads(raw)


def analyze(a, b):
    if a.get("schema") != "MONSTER_STAGE30_FULL_NEW_DATE_V4_168H_STRICT_36_ARTIFACT_SHA_AGGREGATE_SUCCESS_V1":
        raise ValueError("STAGE30_WRONG_EVIDENCE_SCHEMA")
    if b.get("schema") != "MONSTER_STAGE151_ALL305_PREREG_HISTORICAL_EXPOSED_ECONOMICS_V1":
        raise ValueError("STAGE152_WRONG_EVIDENCE_SCHEMA")
    s = a["all_24h_original_WATCH_20bps"]
    f = a["original_WATCH_funded_fixed_lot_300USDT_10_slots"]["optimistic_unknown_exit_20bps"]
    d = b["full305"]
    x = d["confirmed_1440m_complete_unfilled_price_proxy"]["full_illustrative_fee_distribution"]
    y = d["confirmed_360m_complete_unfilled_price_proxy"]["full_illustrative_fee_distribution"]
    state = d["states"]
    no_pullback = d["no_model_entry_state_baseline_by_state"]["NO_PULLBACK_WITHIN_120M"]
    if (a["attempted"], a["source_full_168h_joint"], a["WATCH"]) != (4548, 2514, 760):
        raise ValueError("STAGE30_CENSORED_POPULATION_DRIFT")
    if (s["watch_count"], s["proxy_evaluable"], s["wins"], s["losses"],
            s["same_symbol_24h_overlap_skip"], s["source_censored_excluding_overlap"]) != (760, 430, 133, 297, 250, 80):
        raise ValueError("STAGE30_PRICE_COHORT_DRIFT")
    source_status = s["source_proxy_status_counts"]
    # Non-evaluable does NOT mean exit-only: no entry trades and insufficient
    # entry-or-exit minute quote also have their own explicit source classes.
    missing_classes = {
        "CENSORED_NO_COMPLETE_EXIT",
        "CENSORED_ZERO_VOLUME_EXIT",
        "CENSORED_ZERO_VOLUME_NEAR_EXIT",
        "CENSORED_NO_ENTRY_TRADES",
        "CENSORED_MINUTE_QUOTE_LT_30_USDT",
    }
    if set(source_status) != missing_classes | {
            "PRICE_PROXY_ONLY", "SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED"}:
        raise ValueError("STAGE30_UNKNOWN_PROXY_STATUS_CLASS")
    source_censor_breakdown = {k: source_status[k] for k in sorted(missing_classes)}
    if source_censor_breakdown != {
            "CENSORED_MINUTE_QUOTE_LT_30_USDT": 18,
            "CENSORED_NO_COMPLETE_EXIT": 1,
            "CENSORED_NO_ENTRY_TRADES": 1,
            "CENSORED_ZERO_VOLUME_EXIT": 21,
            "CENSORED_ZERO_VOLUME_NEAR_EXIT": 39,
    }:
        raise ValueError("STAGE30_PROXY_STATUS_BREAKDOWN_DRIFT")
    if (any(not isinstance(n, int) or isinstance(n, bool) or n < 0
            for n in source_status.values())
            or sum(source_censor_breakdown.values()) != s["source_censored_excluding_overlap"]
            or source_status["PRICE_PROXY_ONLY"] != s["proxy_evaluable"]
            or source_status["SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED"] != s["same_symbol_24h_overlap_skip"]
            or sum(source_status.values()) != s["watch_count"]):
        raise ValueError("STAGE30_PROXY_STATUS_BREAKDOWN_DRIFT")
    if sum(state.values()) != d["n"] or (d["n"], state["PULLBACK_RECLAIM_CONFIRMED_PRICE_ONLY"],
            state["NO_PULLBACK_WITHIN_120M"], state["PULLBACK_NO_RECLAIM"]) != (305, 184, 113, 8):
        raise ValueError("STAGE152_D1_COHORT_DRIFT")
    if x["n"] != 184 or y["n"] != 184 or x["positive"] > x["n"] or y["positive"] > y["n"]:
        raise ValueError("STAGE152_INCOMPLETE_CONFIRMATIONS")
    if (b["G4"], b["G6"], b["real_bid_ask_depth_fees_fill_and_net"]) != ("UNKNOWN", "NO_GO", "UNKNOWN"):
        raise ValueError("STAGE152_RELEASE_GATE_DRIFT")
    if f["not_real_wallet_execution"] is not True or f["censored_principal_recovery_pct_UNVERIFIED"] != 100 or f["cash_overdrawn"]:
        raise ValueError("STAGE30_FUNDED_PROXY_CONTRACT_DRIFT")
    if not a["original_WATCH_funded_fixed_lot_300USDT_10_slots"]["optimistic_unknown_exit_100bps"]["realized_proxy_profit_USDT"] < 0:
        raise ValueError("STAGE30_HIGH_SLIPPAGE_STRESS_CHANGED")
    if s["median_net_pct"] >= 0 or f["realized_proxy_profit_USDT"] >= 0:
        raise ValueError("STAGE30_UNEXPECTED_ECONOMIC_RESULT_RECHECK")
    if float(x["median_pct"]) >= 0 or float(y["median_pct"]) >= 0:
        raise ValueError("STAGE152_UNEXPECTED_ECONOMIC_RESULT_RECHECK")
    if no_pullback["n"] != state["NO_PULLBACK_WITHIN_120M"]:
        raise ValueError("STAGE152_NO_ENTRY_DENOMINATOR_DRIFT")
    return {
        "schema": SCHEMA,
        "verdict": "FAIL_ECONOMIC_RELEASE_GATE_NO_BUY",
        "mode": "EXPOSED_HISTORICAL_EVIDENCE_RECONCILIATION_ONLY",
        "source_git_blobs": BLOBS,
        "source_cohorts_are_different_no_pooling": True,
        "stage30_original_spot_v4": {
            "attempted_symbol_dates": a["attempted"],
            "fully_source_verifiable": a["source_full_168h_joint"],
            "watch": s["watch_count"],
            "price_proxy_evaluable": s["proxy_evaluable"],
            "source_censored_excluding_overlap": s["source_censored_excluding_overlap"],
            "source_censor_status_breakdown": source_censor_breakdown,
            "repeat_watch_overlap": s["same_symbol_24h_overlap_skip"],
            "price_proxy_wins": s["wins"],
            "price_proxy_losses": s["losses"],
            "price_proxy_win_fraction_pct": round(100 * s["wins"] / s["proxy_evaluable"], 2),
            "price_proxy_median_net_pct": s["median_net_pct"],
            "historical_funded_300u_10slots_30u_fixed_lot": {
                "assumed_unknown_exit_recovery_pct": 100,
                "slippage_bps_each_side": 20,
                "selected": f["counts"]["selected"],
                "skipped_insufficient_30u_cash": f["counts"]["skip_insufficient_cash_30u"],
                "skipped_busy_slots": f["counts"]["skip_slots_busy"],
                "selected_price_proxy_wins": f["counts"]["winning"],
                "selected_price_proxy_losses": f["counts"]["losing"],
                "final_cash_usdt_price_proxy": f["final_cash_USDT"],
                "net_usdt_price_proxy": f["realized_proxy_profit_USDT"],
            },
            "historical_2x_recall_not_entry_profit": {
                "correct_before_first_2x": a["gross_2x_vs_first_1m"]["early"],
                "later_2x_sample_total": a["gross_2x_vs_first_1m"]["total"],
            },
        },
        "stage152_distinct_original305_d1_research": {
            "original_d1_count": d["n"],
            "pullback_reclaim_price_only_confirmed": state["PULLBACK_RECLAIM_CONFIRMED_PRICE_ONLY"],
            "no_pullback_no_trade": state["NO_PULLBACK_WITHIN_120M"],
            "pullback_no_reclaim_no_trade": state["PULLBACK_NO_RECLAIM"],
            "confirmed_24h_illustrative_fee_positive": x["positive"],
            "confirmed_24h_fee_proxy_median_pct": float(x["median_pct"]),
            "confirmed_6h_fee_proxy_median_pct": float(y["median_pct"]),
            "no_pullback_older_d1_baseline_positive_not_model_trades": no_pullback["positive"],
            "do_not_filter_on_future_exit_minute_turnover": True,
            "user_notional_and_actual_fee_tier": "UNKNOWN",
        },
        "economics_missing": [
            "same_signal_time_bid_ask_L2_and_actual_exit_depth",
            "actual_fee_tier_and_order_notional",
            "real_fills_notification_delivery_and_drawdown",
            "new_independent_forward_cohort",
        ],
        "g4_real_executable_net_profit": "UNKNOWN",
        "g6": "NO_GO",
        "deployment": "NO_GO",
        "gmail": "OFF",
        "trading": "NO_GO",
        "recommendation": "RESEARCH_ONLY_DO_NOT_TRADE",
    }


def read_report(evidence_dir=EVIDENCE):
    return analyze(source(evidence_dir, STAGE30), source(evidence_dir, STAGE152))


def main():
    p = argparse.ArgumentParser(description="Monster historical evidence-backed economic gate")
    p.add_argument("--format", choices=("text", "json"), default="text")
    a = p.parse_args()
    r = read_report()
    if a.format == "json":
        print(json.dumps(r, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        s = r["stage30_original_spot_v4"]
        f = s["historical_funded_300u_10slots_30u_fixed_lot"]
        d = r["stage152_distinct_original305_d1_research"]
        print(r["verdict"], "| G4 UNKNOWN | G6 NO_GO")
        print("Stage30: WATCH", s["watch"], "priced", s["price_proxy_evaluable"],
              "win", s["price_proxy_win_fraction_pct"], "% median", s["price_proxy_median_net_pct"], "%")
        print("Stage30 non-evaluable source cases:",
              s["source_censored_excluding_overlap"], "| breakdown:",
              json.dumps(s["source_censor_status_breakdown"], ensure_ascii=False, sort_keys=True))
        print("Stage30 historical 300U proxy:", f["net_usdt_price_proxy"],
              "USDT; cash-blocked", f["skipped_insufficient_30u_cash"],
              "slot-blocked", f["skipped_busy_slots"])
        print("Stage152 different D1 cohort:", d["original_d1_count"], "confirmed",
              d["pullback_reclaim_price_only_confirmed"], "24h fee-proxy median",
              d["confirmed_24h_fee_proxy_median_pct"], "%")
        print("Historical proxy, no actual L2/fills or BUY; samples are NOT pooled.")


if __name__ == "__main__":
    main()
