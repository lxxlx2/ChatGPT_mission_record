"""CA overview and holder drills must stay scoped with source-end history available."""

from copy import deepcopy
from unittest.mock import Mock

import pytest

from mission_agent.meme.cluster import WalletClusterAnalyzer
from test_meme_owner_account_history import A, B, MINT, T1, T2, TB, TZ, analyzer
from test_meme_holder_ranks import account, key


def test_overview_publishes_narrative_early_without_history_or_independent_holder_reads(monkeypatch):
    events = []
    story = {
        "status": "PARTIAL",
        "story_summary": {"status": "OBSERVED_SOURCE", "items": [{"text": "Project story"}]},
        "evidence": [{"source_url": "https://example.org/story"}],
        "official_recognition": "NO_VERIFIABLE_CLAIM",
    }
    review, rpc = analyzer(
        monkeypatch,
        query_scope="overview",
        exhaust_history=True,
        read_launch_identity=True,
        independent_rpc=Mock(side_effect=AssertionError("overview must not reread owners")),
        progress_callback=lambda stage, details: events.append((stage, details)),
    )
    snap_narrative = Mock(return_value=story)
    review.narrative_snapshot = snap_narrative
    review.launch_snapshot = lambda profile: {
        "pump": {"status": "VERIFIED_CHAIN_STATE", "creator": A, "bonding_curve": T1}
    }
    flow = {"status": "PARTIAL", "reason": "LAUNCH_WINDOW_NOT_LOCATED", "dev": {"creator": A}}
    from mission_agent.meme import launch_flow

    collect_launch = Mock(return_value=flow)
    monkeypatch.setattr(launch_flow, "collect_launch_flow", collect_launch)
    report = review.analyze()

    stages = [stage for stage, _ in events]
    detail = dict(events)
    assert stages.index("BASE_READY") < stages.index("NARRATIVE_READY") < stages.index("HOLDERS_READY")
    assert detail["NARRATIVE_READY"]["narrative"]["official_recognition"] == "NO_VERIFIABLE_CLAIM"
    assert detail["NARRATIVE_READY"]["narrative"]["evidence"] == story["evidence"]
    assert detail["HOLDERS_READY"]["holder_count"] == 2
    assert detail["LAUNCH_FLOW_READY"]["quick_check"]["dev"]["creator"] == A
    assert collect_launch.call_args.kwargs["current_balances"] == {A: 150, B: 850}
    assert report["query_scope"] == "overview"
    assert report["narrative"] == story
    assert report["coverage"]["history_scan_mode"] == "ON_DEMAND"
    assert report["coverage"]["history_windows"] == []
    assert report["metrics"]["LARGEST_PROBABLE_CONTROL_CLUSTER_PCT"] == "UNRESOLVED"
    assert {"WALLET_HISTORY_ON_DEMAND", "LAUNCH_FLOW_INCOMPLETE"} <= set(report["coverage"]["gaps"])
    assert rpc.history == []
    review.independent_rpc.assert_not_called()


def test_wallet_scope_reuses_parent_and_scans_only_selected_accounts_to_source_end(monkeypatch):
    summary, _ = analyzer(monkeypatch, query_scope="overview", exhaust_history=True)
    base = summary.analyze()
    original = deepcopy(base)
    wallet, rpc = analyzer(
        monkeypatch,
        query_scope="wallet",
        focus_owner=A,
        wallet_base=base,
        exhaust_history=True,
    )
    wallet.token_profile = Mock(side_effect=AssertionError("wallet must reuse the bound report"))
    wallet.market_snapshot = Mock(side_effect=AssertionError("wallet must reuse the bound report"))
    wallet.holders = Mock(side_effect=AssertionError("wallet must reuse the bound report"))
    report = wallet.analyze()

    assert base == original
    assert report["query_scope"] == "wallet"
    assert report["focus_owner"] == A
    assert report["wallet_detail"]["owner"] == A
    assert report["wallet_detail"]["deep_scanned"] is True
    assert report["wallet_detail"]["raw"] == "150"
    assert report["wallet_detail"]["balance_observed_at"] == base["observed_at"]
    assert report["wallet_detail"]["first_acquisition"]["signature"] == "oldest"
    requested_addresses = {address for address, _ in rpc.history}
    assert {T1, T2, TZ} <= requested_addresses
    assert requested_addresses <= {T1, T2, TZ, A}
    assert TB not in requested_addresses
    assert all(window["owner"] == A for window in report["coverage"]["history_windows"])
    assert len(report["coverage"]["owner_account_history"]) == 1
    assert report["coverage"]["snapshot_observed_at"] == base["observed_at"]
    wallet.token_profile.assert_not_called()


def test_wallet_scope_rejects_wrong_mint_snapshot():
    with pytest.raises(ValueError, match="WALLET_SCOPE_REQUIRES_BOUND_REPORT"):
        WalletClusterAnalyzer(MINT, rpc=Mock(), query_scope="wallet", focus_owner=A, wallet_base={"mint": B})


def test_narrative_failure_does_not_discard_available_base_evidence(monkeypatch):
    events = []
    review, _ = analyzer(
        monkeypatch, query_scope="overview", progress_callback=lambda stage, details: events.append((stage, details))
    )
    review.narrative_snapshot = Mock(side_effect=ValueError("untrusted source body"))
    report = review.analyze()
    assert report["narrative"]["reason"] == "NARRATIVE_SOURCE_UNAVAILABLE"
    assert report["narrative"]["official_recognition"] == "UNVERIFIED"
    assert dict(events)["NARRATIVE_READY"]["narrative"]["status"] == "UNAVAILABLE"
    assert report["holder_rankings"]["status"] == "COMPLETE_SNAPSHOT"


def test_wallet_scope_can_read_small_ranked_owner_without_expanding_other_wallets(monkeypatch):
    small_owner, small_account = key(303), key(5)
    records = [account(1, 301, 100), account(2, 301, 50), account(3, 301, 0),
               account(4, 302, 849), account(5, 303, 1)]
    overview, _ = analyzer(monkeypatch, records=records, query_scope="overview", exhaust_history=True)
    base = overview.analyze()
    assert small_owner not in {r["owner"] for r in base["holders"]}
    assert small_owner in {r["owner"] for r in base["holder_rankings"]["owners"]}

    wallet, rpc = analyzer(monkeypatch, records=records, query_scope="wallet", focus_owner=small_owner,
                           wallet_base=base, windows={small_account: ["opening"]}, times={"opening": 100},
                           exhaust_history=True)
    out = wallet.analyze()

    assert out["wallet_detail"]["raw"] == "1"
    assert out["wallet_detail"]["first_acquisition"]["signature"] == "opening"
    assert {address for address, _ in rpc.history} == {small_account, small_owner}
    assert all(window["owner"] == small_owner for window in out["coverage"]["history_windows"])
