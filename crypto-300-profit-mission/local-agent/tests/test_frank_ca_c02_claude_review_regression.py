"""C02 Claude review fixes: same-name preview identity and casefold parity.

These are product risks R-a/R-b, not changes to frozen Frank V1.
"""
from mission_agent.meme.identity import reconcile_identity
from mission_agent.mission_control.server import ClusterJobManager


MINT_A = "So11111111111111111111111111111111111111112"
MINT_B = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def _profile(mint):
    return {
        "mint": mint, "status": "OK", "mint_account_status": "VERIFIED",
        "metadata": {"status": "VERIFIED", "records": [
            {"mint": mint, "name": "Agency", "symbol": "AGENCY",
             "source": "TOKEN2022_METADATA", "update_authority": None},
        ]},
    }


def _market(mint, name="agency", symbol="Agency"):
    return {"mint": mint, "status": "OK",
            "market_match_status": "EXACT_BASE_MINT_MATCH",
            "identity_records": [
                {"mint": mint, "name": name, "symbol": symbol,
                 "source": "DEXSCREENER_API"},
            ]}


def test_case_only_source_differences_are_not_false_conflicts():
    result = reconcile_identity(MINT_A, _profile(MINT_A), _market(MINT_A))
    assert result["identity_status"] == "VERIFIED"
    assert result["conflict_status"] == "NO_CONFLICT_OBSERVED"
    assert result["name_display_status"] == "CHAIN_METADATA"
    assert result["display_label"] == "Agency"
    # Raw provider evidence is preserved rather than rewritten.
    assert result["sources"][0]["symbol"] == "AGENCY"
    assert result["sources"][1]["name"] == "agency"


def test_substantive_source_differences_still_fail_closed():
    result = reconcile_identity(
        MINT_A, _profile(MINT_A), _market(MINT_A, name="Not Agency"))
    assert result["identity_status"] == "VERIFIED"
    assert result["conflict_status"] == "TOKEN_IDENTITY_CONFLICT"
    assert result["display_name"] is None
    assert result["display_label"] == "身份来源冲突"


def test_two_equal_name_mints_remain_separate_in_base_ready_progress(tmp_path):
    manager = ClusterJobManager(tmp_path / "research-only")
    try:
        for idx, mint in enumerate((MINT_A, MINT_B)):
            job_id = "case-" + str(idx)
            identity = reconcile_identity(mint, _profile(mint), _market(mint))
            manager.jobs[job_id] = {
                "job_id": job_id, "mint": mint, "status": "RUNNING",
                "preset": "standard", "progress": {},
            }
            manager._set_progress(job_id, "BASE_READY", {
                "token_identity": identity,
                "token_profile": {"status": "OK", "mint_authority": None,
                                  "freeze_authority": None},
                "market": {"status": "OK", "price_usd": "0.01",
                           "main_pair": {"liquidity_usd": "1000"}},
            })
            actual = manager.get(job_id)
            assert actual["preview"]["mint"] == mint
            assert actual["progress"]["mint"] == mint
            assert actual["preview"]["token_identity"]["display_label"] == "Agency"
        assert manager.get("case-0")["preview"]["mint"] != manager.get("case-1")["preview"]["mint"]
    finally:
        manager.executor.shutdown(wait=True)
