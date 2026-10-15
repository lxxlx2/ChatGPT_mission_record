"""No-RPC exact-CA F01/C02/F02 read-only display contract regressions."""
from copy import deepcopy

from mission_agent.mission_control.frank_ca_f02_alignment import align_frank_ca_f02

MINT = "So11111111111111111111111111111111111111112"
OTHER = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SHA = "a" * 64


def sources():
    eligible = {"mint": MINT, "person_id": "frank", "decision": "BUY",
                "source_signal_id": "frozen-source-1"}
    f01 = {"status": "OK", "eligible": [eligible], "not_followed": []}
    c02 = {
        "mint": MINT, "chain": "solana",
        "token_identity": {"identity_status": "VERIFIED",
                           "conflict_status": "NO_CONFLICT_OBSERVED",
                           "display_label": "Verified Name"},
        "assessment": {"narrative_status": "NOT_AUTOMATICALLY_VERIFIED"},
    }
    mints = [{"mint": MINT, "state": "OPEN_ACCOUNT_NONZERO",
              "observed_quantity": "123.000000", "token_account_count": 1}]
    mints += [{"mint": f"synthetic-{i}", "state": "NO_OPEN_ACCOUNT_OBSERVED",
               "observed_quantity": None, "token_account_count": None}
              for i in range(31)]
    f02 = {
        "kind": "F02_RESEARCH_ARCHIVED_OWNER_POSITIONS",
        "person_id": "frank", "chain": "solana",
        "target_mint_count": 32, "mints": mints,
        "capture_fresh": True, "archive_observation_usable": True,
        "readiness": "FRESH_VERIFIED_ARCHIVED_OBSERVATION",
        "capture_age_seconds": 10, "max_age_seconds": 300,
        "verified_full_wire_capture_sha256": SHA,
        "latest_capture_sha256": SHA, "latest_attempt_capture_sha256": SHA,
        "source_observation_status": "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC",
        "latest_attempt_source_status": "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC",
        "capture_observed_at_utc": "2026-10-15T06:10:01Z",
    }
    return f01, c02, f02


def aligned(f01=None, c02=None, f02=None):
    src = sources()
    return align_frank_ca_f02(
        mint=MINT, follow=src[0] if f01 is None else f01,
        ca_report=src[1] if c02 is None else c02,
        f02_positions=src[2] if f02 is None else f02)


def test_exact_mint_signal_market_and_archival_observation_separate():
    out = aligned()
    assert out["f01"]["status"] == "F01_ELIGIBLE"
    assert out["f01"]["frozen_decision"] == "BUY"
    assert out["f02"]["state"] == "OPEN_ACCOUNT_NONZERO"
    assert out["f02"]["observed_quantity"] == "123.000000"
    assert out["f02"]["archived_source_only"] is True
    assert out["c02"]["status"] == "CA_EXACT_MINT_IDENTITY_VERIFIED"
    assert out["c02"]["narrative_status"] == "NOT_AUTOMATICALLY_VERIFIED"
    assert out["combined_trade_permission"] is False


def test_old_f02_archive_never_upgrades_to_current_observed_quantity():
    f01, c02, f02 = sources()
    f02["readiness"] = "STALE_ARCHIVED_SOURCE"
    out = aligned(f01, c02, f02)
    assert out["f01"]["status"] == "F01_ELIGIBLE"
    assert out["f02"]["state"] == "SOURCE_UNAVAILABLE"
    assert out["f02"]["observed_quantity"] is None
    assert out["f02"]["token_account_count"] is None
    assert out["f02"]["capture_sha256"] is None


def test_source_metadata_tie_and_partial_attempt_never_resurrect_old_balance():
    f01, c02, f02 = sources()
    f02["latest_attempt_source_status"] = "PARTIAL_SOURCE"
    assert aligned(f01, c02, f02)["f02"]["observed_quantity"] is None
    f02["latest_attempt_source_status"] = "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC"
    f02["latest_attempt_capture_sha256"] = "b" * 64
    assert aligned(f01, c02, f02)["f02"]["observed_quantity"] is None
    f02["latest_attempt_capture_sha256"] = SHA
    f02["capture_age_seconds"] = 299
    assert aligned(f01, c02, f02)["f02"]["observed_quantity"] is None


def test_same_name_different_ca_must_not_inherit_other_ca_identity_or_wallet():
    f01, c02, f02 = sources()
    c02["mint"] = OTHER
    out = aligned(f01, c02, f02)
    assert out["c02"]["status"] == "CA_MINT_MISMATCH"
    assert out["c02"]["exact_mint_label"] is None
    assert out["c02"]["narrative_status"] == "UNVERIFIED"
    out = align_frank_ca_f02(mint=OTHER, follow=f01, ca_report=c02,
                              f02_positions=f02)
    assert out["f01"]["status"] == "F01_NOT_ELIGIBLE"
    assert out["f02"]["state"] == "OUTSIDE_FROZEN_TARGET_ROSTER"
    assert out["c02"]["exact_mint_label"] == "Verified Name"


def test_ca_conflict_or_wrong_chain_must_not_show_verified_identity():
    f01, c02, f02 = sources()
    c02["token_identity"]["conflict_status"] = "TOKEN_IDENTITY_CONFLICT"
    out = aligned(f01, c02, f02)
    assert out["c02"]["status"] == "CA_IDENTITY_UNCONFIRMED"
    assert out["c02"]["exact_mint_label"] is None
    c02["chain"] = "bsc"
    out = aligned(f01, c02, f02)
    assert out["c02"]["status"] == "CA_CHAIN_MISMATCH"
    assert out["c02"]["exact_mint_label"] is None


def test_no_buy_and_latest_sell_only_F01_policy_controls_signal_status():
    f01, c02, f02 = sources()
    f01["eligible"] = []
    f01["not_followed"] = [{"mint": MINT, "decision": "NO_BUY"}]
    assert aligned(f01, c02, f02)["f01"]["status"] == "F01_NOT_ELIGIBLE"
    f01["eligible"] = [{"mint": MINT, "person_id": "frank",
                        "decision": "WAIT", "source_signal_id": "old"}]
    assert aligned(f01, c02, f02)["f01"]["status"] == "F01_NOT_ELIGIBLE"


def test_zero_or_unobserved_wallet_not_interpreted_as_sell():
    f01, c02, f02 = sources()
    f02["mints"][0].update({"state": "OPEN_ACCOUNT_ZERO", "observed_quantity": "0"})
    out = aligned(f01, c02, f02)
    assert out["cross_source_review_reason"] == "F01_SIGNAL_VS_ARCHIVED_WALLET_REQUIRES_REVIEW"
    assert out["f02"]["observed_quantity"] == "0"
    assert out["f02"]["does_not_confirm_sale_or_current_portfolio"] is True
    f02["mints"][0].update({"state": "NO_OPEN_ACCOUNT_OBSERVED",
                            "observed_quantity": None, "token_account_count": None})
    out = aligned(f01, c02, f02)
    assert out["f02"]["observed_quantity"] is None
    assert out["cross_source_review_reason"] is not None


def test_duplicate_f02_rows_or_f01_eligible_rows_fail_closed_without_duplicate_buy():
    f01, c02, f02 = sources()
    f01["eligible"].append(deepcopy(f01["eligible"][0]))
    assert aligned(f01, c02, f02)["f01"]["status"] == "F01_AMBIGUOUS"
    f01["eligible"].pop()
    f02["mints"][1]["mint"] = MINT
    out = aligned(f01, c02, f02)
    assert out["f02"]["observed_quantity"] is None
    assert out["f02"]["state"] == "SOURCE_UNAVAILABLE"


def test_projection_never_mutates_upstream_sources():
    f01, c02, f02 = sources()
    before = deepcopy((f01, c02, f02))
    out = aligned(f01, c02, f02)
    assert out["no_new_rpc_or_sidecar_writes"] is True
    assert (f01, c02, f02) == before
