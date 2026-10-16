"""F01: a live BUY is not enough unless the recorded evidence remains fresh.

A red test against old main is expected until follow_view is implemented.
"""
import pytest

from mission_agent.mission_control.follow_view import partition_candidates

NOW = 1_800_000_000


def candidate(**updates):
    data = {
        "person_id": "frank",
        "mint": "MintSyntheticUnit",
        "episode_id": "e1",
        "pattern": "MULTIPLE",
        "source_signal_id": "sig-101",
        "position_state": "OPEN",
        "current_raw": "12",
        "latest_side": "BUY",
        "latest_at": NOW - 10,
        "latest_buy_at": NOW - 10,
        "decision": "BUY",
        "decision_created_at": NOW - 2,
        "quote_observed_at": NOW - 3,
        "decision_quote": {"status": "OK", "route_exists": True},
        "metrics": {"execution_price_usdc": "0.001", "price_impact_pct": "0.1"},
    }
    data.update(updates)
    return data


def partition(items, status="LIVE"):
    return partition_candidates(
        items, now=NOW, runtime_status=status,
        max_frank_buy_age_seconds=600, max_quote_age_seconds=30,
    )


def test_fresh_buy_and_small_buy_remain_live_only():
    rows = [candidate(mint="buy"), candidate(mint="small", decision="SMALL_BUY")]
    out = partition(rows)
    assert [r["mint"] for r in out["eligible"]] == ["buy", "small"]
    assert out["excluded_count"] == 0
    assert out["eligible_count"] == 2


@pytest.mark.parametrize(("field", "value", "reason"), [
    ("decision", "NO_BUY", "NOT_ACTIONABLE_DECISION"),
    ("decision", "WAIT", "NOT_ACTIONABLE_DECISION"),
    ("decision", "UNASSESSED", "NOT_ACTIONABLE_DECISION"),
    ("position_state", "CLOSED", "MODEL_POSITION_NOT_OPEN"),
    ("position_state", "INVENTORY_UNDETERMINED", "MODEL_POSITION_NOT_OPEN"),
    ("latest_side", "SELL", "LATEST_ACTION_NOT_BUY"),
    ("latest_side", "SELL_POSITION_UNRESOLVED", "LATEST_ACTION_NOT_BUY"),
    ("current_raw", None, "MODEL_INVENTORY_UNKNOWN_OR_ZERO"),
    ("current_raw", "0", "MODEL_INVENTORY_UNKNOWN_OR_ZERO"),
    ("source_signal_id", None, "SOURCE_SIGNAL_UNVERIFIED"),
    ("pattern", "REENTRY_WATCH", "SOURCE_SIGNAL_UNVERIFIED"),
    ("latest_buy_at", NOW - 601, "FRANK_BUY_STALE"),
    ("decision_created_at", NOW - 601, "DECISION_STALE"),
    ("quote_observed_at", NOW - 31, "QUOTE_STALE"),
    ("quote_observed_at", None, "QUOTE_STALE"),
    ("decision_quote", {"status": "UNAVAILABLE"}, "QUOTE_NOT_EXECUTABLE"),
    ("decision_quote", {"status": "OK", "route_exists": False}, "QUOTE_NOT_EXECUTABLE"),
    ("person_id", "person_b", "NOT_APPROVED_FRANK_SCOPE"),
    ("candidate_source", "MISSION_CONTROL_OVERLAY", "NOT_FROZEN_FRANK_SOURCE"),
])
def test_actionable_panel_excludes_non_actionable_and_preserves_history(field, value, reason):
    row = candidate(**{field: value})
    before = dict(row)
    out = partition([row])
    assert out["eligible"] == []
    assert out["excluded_count"] == 1
    assert out["not_followed"][0]["exclusion_reason"] == reason
    assert out["not_followed"][0]["mint"] == row["mint"]
    assert row == before


def test_runtime_down_hides_old_buy_even_if_decision_saved():
    out = partition([candidate()], status="OFFLINE")
    assert out["eligible"] == []
    assert out["not_followed"][0]["exclusion_reason"] == "FRANK_RUNTIME_NOT_LIVE"


def test_no_current_decision_means_exactly_zero_follow_opportunities():
    out = partition([])
    assert out["eligible"] == []
    assert out["eligible_count"] == 0


def test_latest_sell_contradiction_excludes_despite_old_buy_and_quote():
    out = partition([candidate(latest_side="SELL", latest_at=NOW - 1)])
    assert out["eligible_count"] == 0
    assert out["not_followed"][0]["exclusion_reason"] == "LATEST_ACTION_NOT_BUY"


def test_safari_synthetic_buy_with_no_actual_price_or_impact_is_not_followable():
    row = candidate(metrics={}, decision_quote={"status": "OK", "route_exists": True})
    out = partition([row])
    assert out["eligible_count"] == 0
    assert out["not_followed"][0]["exclusion_reason"] == "QUOTE_NOT_EXECUTABLE"
    assert out["not_followed"][0]["decision"] == "BUY"


@pytest.mark.parametrize("price,impact", [
    (None, "0.1"), ("0", "0.1"), ("not-a-number", "0.1"),
    ("0.01", None), ("0.01", "-0.01"), ("0.01", "NaN"),
])
def test_missing_or_invalid_executable_quote_evidence_is_fail_closed(price, impact):
    row = candidate(metrics={}, decision_quote={
        "status": "OK", "route_exists": True,
        "execution_price_usdc": price, "price_impact_pct": impact,
    })
    out = partition([row])
    assert out["eligible_count"] == 0
    assert out["not_followed"][0]["exclusion_reason"] == "QUOTE_NOT_EXECUTABLE"


def test_complete_quotation_can_live_in_frozen_quote_not_only_metrics():
    row = candidate(metrics={}, decision_quote={
        "status": "OK", "route_exists": True,
        "execution_price_usdc": "0.012", "price_impact_pct": "0.0",
    })
    assert partition([row])["eligible_count"] == 1


def test_reviewer_counterexample_quote_and_metrics_contradiction_is_not_eligible():
    row = candidate(
        decision_quote={"status": "OK", "route_exists": True,
                        "execution_price_usdc": "0.012", "price_impact_pct": "0.1"},
        metrics={"execution_price_usdc": "0", "price_impact_pct": "NaN"},
    )
    out = partition([row])
    assert out["eligible_count"] == 0
    assert out["not_followed"][0]["exclusion_reason"] == "QUOTE_NOT_EXECUTABLE"
    assert row["decision_quote"]["execution_price_usdc"] == "0.012"
    assert row["metrics"]["execution_price_usdc"] == "0"


@pytest.mark.parametrize("key,left,right", [
    ("execution_price_usdc", "0.012", "0.013"),
    ("price_impact_pct", "0.1", "0.2"),
    ("execution_price_usdc", "0.012", "NaN"),
    ("price_impact_pct", "0.1", "-1"),
    ("execution_price_usdc", "0.012", "0"),
])
def test_any_quoting_disagreement_or_invalid_source_blocks_follow(key,left,right):
    quote = {"status": "OK", "route_exists": True,
             "execution_price_usdc": "0.012", "price_impact_pct": "0.1"}
    metrics = {"execution_price_usdc": "0.012", "price_impact_pct": "0.1"}
    quote[key] = left
    metrics[key] = right
    result = partition([candidate(decision_quote=quote, metrics=metrics)])
    assert result["eligible_count"] == 0
    assert result["not_followed"][0]["exclusion_reason"] == "QUOTE_NOT_EXECUTABLE"


def test_validated_quote_projection_used_by_ui_preserves_original_data():
    row = candidate(decision_quote={
        "status": "OK", "route_exists": True,
        "execution_price_usdc": "0.0120", "price_impact_pct": "0.10",
    }, metrics={"execution_price_usdc": "0.012", "price_impact_pct": "0.1"})
    before = {key: dict(row[key]) for key in ("decision_quote", "metrics")}
    result = partition([row])
    assert result["eligible_count"] == 1
    projected = result["eligible"][0]["validated_follow_quote"]
    assert projected == {"execution_price_usdc": "0.0120", "price_impact_pct": "0.10"}
    assert row["decision_quote"] == before["decision_quote"]
    assert row["metrics"] == before["metrics"]


@pytest.mark.parametrize("bad", [
    "1_000", " 0.012", "0.012 ", "\\t0.012", "+0.012",
    "01.0", ".012", "0x10", "1,000",
])
def test_noncanonical_numeric_quote_from_single_source_is_not_eligible(bad):
    row = candidate(
        metrics={},
        decision_quote={
            "status": "OK", "route_exists": True,
            "execution_price_usdc": bad,
            "price_impact_pct": "0.1",
        },
    )
    out = partition([row])
    assert out["eligible_count"] == 0
    assert out["not_followed"][0]["exclusion_reason"] == "QUOTE_NOT_EXECUTABLE"


@pytest.mark.parametrize("nonrepresentable", ["1e-999", "1e999", "1e-324", "1e309"])
def test_backend_excludes_price_outside_browser_number_range(nonrepresentable):
    row = candidate(metrics={}, decision_quote={
        "status": "OK", "route_exists": True,
        "execution_price_usdc": nonrepresentable,
        "price_impact_pct": "0.1",
    })
    out = partition([row])
    assert out["eligible_count"] == 0
    assert out["not_followed"][0]["exclusion_reason"] == "QUOTE_NOT_EXECUTABLE"
    assert row["decision_quote"]["execution_price_usdc"] == nonrepresentable


@pytest.mark.parametrize("price", ["0.012", "0.000000001", "1e-300", "5e-324"])
def test_backend_preserves_browser_representable_positive_price(price):
    row = candidate(metrics={}, decision_quote={
        "status": "OK", "route_exists": True,
        "execution_price_usdc": price,
        "price_impact_pct": "0.1",
    })
    out = partition([row])
    assert out["eligible_count"] == 1
    assert float(out["eligible"][0]["validated_follow_quote"]["execution_price_usdc"]) > 0


def test_browser_unrepresentable_impact_is_not_followable():
    for raw in ("1e999", "1e-999"):
        row = candidate(metrics={}, decision_quote={
            "status": "OK", "route_exists": True,
            "execution_price_usdc": "0.012",
            "price_impact_pct": raw,
        })
        out = partition([row])
        assert out["eligible_count"] == 0
        assert out["not_followed"][0]["exclusion_reason"] == "QUOTE_NOT_EXECUTABLE"
