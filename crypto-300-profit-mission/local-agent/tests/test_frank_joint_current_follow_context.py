"""F01 current eligible candidates with A05/F02 evidence: real localhost HTTP tests.

Everything is a local synthetic fixture, not current wallet/RPC evidence.
"""
from datetime import datetime, timedelta
from http.client import HTTPConnection
from pathlib import Path
import json
import time

from scripts import frank_joint_readonly_http as joint
from scripts.frank_f02_readonly_positions_api import make_handler as f02_handler
from test_frank_joint_readonly_http import (
    control_handler, make_f02, serving, sources,
)
from scripts.frank_reconcile_frozen32_offline import load_frozen_roster, ROSTER
from test_frank_f02_manual_refresh import WALLET
from test_frank_a04_a05_chain_capture import pk


def _get(port, path="/api/research/current-follow-context", headers=None):
    conn = HTTPConnection("127.0.0.1", port, timeout=4)
    try:
        conn.request("GET", path, headers=headers or {})
        result = conn.getresponse()
        return result.status, dict(result.getheaders()), json.loads(result.read())
    finally:
        conn.close()


def test_real_three_loopback_services_show_current_candidate_and_exact_a05(tmp_path):
    mint, other, data = sources()
    summary, service = make_f02(tmp_path)
    before = Path(summary["sidecar"]).read_bytes()
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        bridge = joint.JointReadOnly(control_port=ctrl.server_port,
                                     f02_port=f02.server_port)
        with serving(joint.make_handler(bridge)) as front:
            status, headers, doc = _get(front.server_port)
            assert status == 200
            assert headers["Cache-Control"] == "no-store, max-age=0"
            assert doc["kind"] == "FRANK_CURRENT_F01_WITH_A05_RESEARCH_CONTEXT"
            assert doc["status"] == "CURRENT_F01_CANDIDATES_ARCHIVED_A05_ONLY"
            assert doc["candidate_count"] == 1
            assert doc["f01_valid_until_epoch"] >= time.time()
            assert doc["upstream"] == {
                "f01": "SOURCE_READ", "f02": "SOURCE_READ",
                "c02": "NOT_QUERIED"}
            row = doc["candidates"][0]
            assert row["mint"] == mint
            assert row["f01_decision"] == "BUY"
            assert row["wallet_observation_state"] == "OPEN_ACCOUNT_NONZERO"
            assert row["observed_quantity"] == "123.000000"
            assert row["token_account_count"] == 1
            assert row["current_wallet_position_verified"] is False
            assert row["may_trade_based_on_combination"] is False
            assert doc["combined_trade_permission"] is False
            assert not doc["ca_query_executed"]
            assert not doc["initiated_solana_rpc"]
            assert not doc["writes_production_sqlite"]
            assert _get(front.server_port, "/api/research/current-follow-context?mint=" + other)[0] == 400
            assert _get(front.server_port,
                        headers={"Host": "external.example"})[0] == 421
            assert _get(front.server_port,
                        "/api/research/current-follow-context/")[0] == 404
    assert Path(summary["sidecar"]).read_bytes() == before
    assert data["requests"] == ["/api/follow-opportunities"]
    assert not any("cluster" in r or "POST:" in r for r in data["requests"])


def test_expired_a05_masks_quantity_without_removing_f01_candidate(tmp_path):
    mint, _, data = sources()
    _, service = make_f02(tmp_path)
    observed = datetime.fromisoformat(service.positions()["capture_observed_at_utc"])
    actual = service.positions
    service.positions = lambda: actual(as_of_utc=observed + timedelta(seconds=301))
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        doc = joint.JointReadOnly(control_port=ctrl.server_port,
                                  f02_port=f02.server_port).current_follow_context()
    assert doc["candidate_count"] == 1
    assert doc["status"] == "CANDIDATES_WITH_A05_SOURCE_GAP"
    row = doc["candidates"][0]
    assert row["mint"] == mint
    assert row["f01_decision"] == "BUY"
    assert row["wallet_observation_state"] == "SOURCE_UNAVAILABLE"
    assert row["observed_quantity"] is None
    assert row["token_account_count"] is None


def test_f01_expiry_and_corrupt_eligibility_fail_closed(tmp_path):
    _, _, data = sources()
    _, service = make_f02(tmp_path)
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        bridge = joint.JointReadOnly(control_port=ctrl.server_port,
                                     f02_port=f02.server_port)
        data["f01"]["as_of_epoch"] = time.time() - 600
        result = bridge.current_follow_context()
        assert result["status"] == "F01_SOURCE_UNAVAILABLE"
        assert result["candidate_count"] is None
        assert result["candidates"] == []
        assert result["upstream"]["f02"] == "NOT_READ"
        data["f01"]["as_of_epoch"] = "CURRENT_TEST_TIME"
        data["f01"]["eligible"][0]["decision"] = "SELL"
        assert bridge.current_follow_context()["status"] == "F01_SOURCE_UNAVAILABLE"
        data["f01"]["eligible"][0]["decision"] = "BUY"
        data["f01"]["eligible"].append(dict(data["f01"]["eligible"][0]))
        data["f01"]["eligible_count"] = 2
        assert bridge.current_follow_context()["candidate_count"] is None


def test_empty_valid_f01_is_not_the_same_as_source_unavailable(tmp_path):
    _, _, data = sources()
    data["f01"]["eligible"] = []
    data["f01"]["eligible_count"] = 0
    _, service = make_f02(tmp_path)
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        out = joint.JointReadOnly(control_port=ctrl.server_port,
                                  f02_port=f02.server_port).current_follow_context()
    assert out["status"] == "NO_CURRENT_ELIGIBLE_CANDIDATES"
    assert out["candidate_count"] == 0
    assert out["candidates"] == []


def test_f02_connection_loss_still_shows_f01_candidate_with_unknown_position(tmp_path):
    mint, _, data = sources()
    with serving(control_handler(data)) as ctrl:
        out = joint.JointReadOnly(control_port=ctrl.server_port,
                                  f02_port=1).current_follow_context()
    assert out["status"] == "CANDIDATES_WITH_A05_SOURCE_GAP"
    assert out["candidate_count"] == 1
    assert out["upstream"]["f02"] == "SOURCE_UNAVAILABLE"
    assert out["candidates"][0]["mint"] == mint
    assert out["candidates"][0]["wallet_observation_state"] == "SOURCE_UNAVAILABLE"
    assert out["candidates"][0]["observed_quantity"] is None
    assert out["combined_trade_permission"] is False



def _one_candidate(data, mint, *, decision="BUY"):
    data["f01"]["eligible"] = [{
        "mint": mint, "person_id": "frank",
        "decision": decision, "source_signal_id": "review-source-1",
    }]
    data["f01"]["eligible_count"] = 1


def test_j1_zero_account_requires_review_in_native_http_without_changing_buy(tmp_path):
    _, zero_mint, data = sources()
    _one_candidate(data, zero_mint)
    summary, service = make_f02(tmp_path)
    before = Path(summary["sidecar"]).read_bytes()
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        bridge = joint.JointReadOnly(control_port=ctrl.server_port,
                                     f02_port=f02.server_port)
        with serving(joint.make_handler(bridge)) as front:
            status, _, doc = _get(front.server_port)
    assert status == 200
    assert doc["candidate_count"] == 1
    assert doc["status"] == "CANDIDATES_REQUIRING_CROSS_SOURCE_REVIEW"
    row = doc["candidates"][0]
    assert row["mint"] == zero_mint and row["f01_decision"] == "BUY"
    assert row["wallet_observation_state"] == "OPEN_ACCOUNT_ZERO"
    assert row["observed_quantity"] == "0.000000"
    assert row["review_required_reason"] == (
        "F01_SIGNAL_VS_ARCHIVED_WALLET_REQUIRES_REVIEW")
    assert not row["may_trade_based_on_combination"]
    assert not doc["combined_trade_permission"]
    assert Path(summary["sidecar"]).read_bytes() == before
    assert data["requests"] == ["/api/follow-opportunities"]


def test_j1_no_open_account_observed_preserves_review_without_inventing_zero(tmp_path):
    _, _, data = sources()
    target = load_frozen_roster(ROSTER, WALLET)["records"][2]["mint"]
    _one_candidate(data, target, decision="SMALL_BUY")
    _, service = make_f02(tmp_path)
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        result = joint.JointReadOnly(
            control_port=ctrl.server_port,
            f02_port=f02.server_port).current_follow_context()
    assert result["status"] == "CANDIDATES_REQUIRING_CROSS_SOURCE_REVIEW"
    row = result["candidates"][0]
    assert row["mint"] == target
    assert row["f01_decision"] == "SMALL_BUY"
    assert row["wallet_observation_state"] == "NO_OPEN_ACCOUNT_OBSERVED"
    assert row["observed_quantity"] is None
    assert row["token_account_count"] is None
    assert row["review_required_reason"] == (
        "F01_SIGNAL_VS_ARCHIVED_WALLET_REQUIRES_REVIEW")
    assert row["historical_sale_confirmed"] is False


def test_two_distinct_mints_stay_separate_and_no_cross_candidate_review(tmp_path):
    mint, second, data = sources()
    data["f01"]["eligible"].append({
        "mint": second, "person_id": "frank",
        "decision": "SMALL_BUY", "source_signal_id": "approved-2",
    })
    data["f01"]["eligible_count"] = 2
    summary, service = make_f02(tmp_path)
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        doc = joint.JointReadOnly(
            control_port=ctrl.server_port,
            f02_port=f02.server_port).current_follow_context()
    assert doc["candidate_count"] == 2
    assert doc["status"] == "CANDIDATES_REQUIRING_CROSS_SOURCE_REVIEW"
    first, zero = doc["candidates"]
    assert first["mint"] == mint and first["observed_quantity"] == "123.000000"
    assert first["review_required_reason"] is None
    assert zero["mint"] == second and zero["observed_quantity"] == "0.000000"
    assert zero["review_required_reason"] is not None
    assert [c["source_signal_id"] for c in doc["candidates"]] == [
        "approved-1", "approved-2"]
    assert not doc["combined_trade_permission"]
    assert data["requests"] == ["/api/follow-opportunities"]
    assert Path(summary["sidecar"]).is_file()


def test_review_and_out_of_roster_source_gap_both_reflected_in_summary(tmp_path):
    _, zero_mint, data = sources()
    outside = pk(210)
    assert outside not in {r["mint"] for r in
                           load_frozen_roster(ROSTER, WALLET)["records"]}
    _one_candidate(data, zero_mint)
    data["f01"]["eligible"].append({
        "mint": outside, "person_id": "frank",
        "decision": "BUY", "source_signal_id": "approved-outside",
    })
    data["f01"]["eligible_count"] = 2
    _, service = make_f02(tmp_path)
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        doc = joint.JointReadOnly(
            control_port=ctrl.server_port,
            f02_port=f02.server_port).current_follow_context()
    assert doc["status"] == "CANDIDATES_WITH_REVIEW_AND_A05_SOURCE_GAP"
    zero, other = doc["candidates"]
    assert zero["review_required_reason"] is not None
    assert other["mint"] == outside
    assert other["wallet_observation_state"] == "OUTSIDE_FROZEN_TARGET_ROSTER"
    assert other["review_required_reason"] is None
    assert other["observed_quantity"] is None


def test_partial_program_source_masks_quantity_without_false_review(tmp_path):
    mint, _, data = sources()
    _, service = make_f02(tmp_path)
    actual = service.positions
    def partial():
        view = actual()
        view["readiness"] = "INCOMPLETE_OR_NO_LATEST_CAPTURE"
        view["archive_observation_usable"] = False
        return view
    service.positions = partial
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        doc = joint.JointReadOnly(
            control_port=ctrl.server_port,
            f02_port=f02.server_port).current_follow_context()
    assert doc["status"] == "CANDIDATES_WITH_A05_SOURCE_GAP"
    row = doc["candidates"][0]
    assert row["mint"] == mint and row["f01_decision"] == "BUY"
    assert row["review_required_reason"] is None
    assert row["wallet_observation_state"] == "SOURCE_UNAVAILABLE"
    assert row["observed_quantity"] is None


def test_existing_f02_one_second_ttl_safety_margin_is_documented_and_tested(tmp_path):
    mint, _, data = sources()
    _, service = make_f02(tmp_path)
    service.max_age_seconds = 120
    original = service.positions
    captured_at = datetime.fromisoformat(original()["capture_observed_at_utc"])
    with serving(control_handler(data)) as ctrl, serving(f02_handler(service)) as f02:
        bridge = joint.JointReadOnly(control_port=ctrl.server_port,
                                     f02_port=f02.server_port)
        for age, state in [(118, "OPEN_ACCOUNT_NONZERO"),
                           (119, "SOURCE_UNAVAILABLE"),
                           (121, "SOURCE_UNAVAILABLE")]:
            service.positions = lambda: original(
                as_of_utc=captured_at + timedelta(seconds=age))
            doc = bridge.current_follow_context()
            assert doc["candidates"][0]["mint"] == mint
            assert doc["candidates"][0]["wallet_observation_state"] == state
            assert (doc["candidates"][0]["observed_quantity"] is not None) == (
                age == 118)
            assert doc["candidates"][0]["review_required_reason"] is None
            assert doc["status"] == ("CURRENT_F01_CANDIDATES_ARCHIVED_A05_ONLY"
                                     if age == 118 else "CANDIDATES_WITH_A05_SOURCE_GAP")
