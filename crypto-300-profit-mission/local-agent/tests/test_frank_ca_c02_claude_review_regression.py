"""C02 Claude review fixes: same-name preview identity and casefold parity.

These are product risks R-a/R-b, not changes to frozen Frank V1.
"""
import base64
import struct

from mission_agent.meme.identity import (
    reconcile_identity, read_metadata, decode_key, TOKEN22, METAPLEX,
)
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


def test_metaplex_and_token2022_source_case_only_difference_is_not_conflict():
    def field(txt):
        raw = txt.encode("utf-8")
        return struct.pack("<I", len(raw)) + raw
    authority = decode_key(MINT_B)
    binary = (bytes([4]) + authority + decode_key(MINT_A) +
              field("agency") + field("Agency") + field(""))
    metaplex = {"context": {"slot": 100},
                "value": {"owner": METAPLEX,
                          "data": [base64.b64encode(binary).decode("ascii"), "base64"]}}
    class StubRPC:
        def call(self, method, params, ttl=60):
            assert method == "getAccountInfo"
            assert params[1]["commitment"] == "finalized"
            return metaplex
    state = {"owner": TOKEN22, "data": {"parsed": {"type": "mint", "info": {
        "extensions": [
            {"extension": "metadataPointer", "state": {"metadataAddress": MINT_A}},
            {"extension": "tokenMetadata", "state": {
                "mint": MINT_A, "name": "Agency", "symbol": "AGENCY",
                "updateAuthority": MINT_B,
            }},
        ],
    }}}}
    results = read_metadata(MINT_A, StubRPC(),
                            {"context": {"slot": 99}, "value": state})
    assert results["status"] == "VERIFIED"
    assert len(results["records"]) == 2
    assert {r["name"] for r in results["records"]} == {"Agency", "agency"}
    assert {r["symbol"] for r in results["records"]} == {"Agency", "AGENCY"}


def test_unicode_casefold_expansion_is_real_identity_conflict():
    profile = _profile(MINT_A)
    profile["metadata"]["records"][0]["name"] = "Straße"
    profile["metadata"]["records"][0]["symbol"] = "STR"
    market = _market(MINT_A, name="STRASSE", symbol="STR")
    observed = reconcile_identity(MINT_A, profile, market)
    assert observed["identity_status"] == "VERIFIED"
    assert observed["conflict_status"] == "TOKEN_IDENTITY_CONFLICT"
    assert observed["display_name"] is None


def test_different_update_authority_still_conflicts_when_names_differ_only_in_case():
    def field(value):
        raw = value.encode()
        return struct.pack("<I", len(raw)) + raw
    first_authority = decode_key(MINT_B)
    second_authority = decode_key(MINT_A)
    binary = (bytes([4]) + first_authority + decode_key(MINT_A) +
              field("agency") + field("Agency") + field(""))
    metaplex = {"context": {"slot": 100}, "value": {
        "owner": METAPLEX,
        "data": [base64.b64encode(binary).decode("ascii"), "base64"],
    }}
    class RPC:
        def call(self, method, params, ttl=60):
            return metaplex
    mint_account = {"context": {"slot": 99}, "value": {
        "owner": TOKEN22,
        "data": {"parsed": {"type": "mint", "info": {"extensions": [
            {"extension": "metadataPointer", "state": {"metadataAddress": MINT_A}},
            {"extension": "tokenMetadata", "state": {
                "mint": MINT_A, "name": "Agency", "symbol": "AGENCY",
                "updateAuthority": MINT_A,
            }},
        ]}}},
    }}
    assert first_authority != second_authority
    outcome = read_metadata(MINT_A, RPC(), mint_account)
    assert outcome["status"] == "TOKEN_IDENTITY_CONFLICT"
    assert len(outcome["records"]) == 2


def test_invalid_width_mint_rejected_before_job_is_created(tmp_path):
    from mission_agent.mission_control.server import ClusterJobManager
    import pytest
    manager = ClusterJobManager(tmp_path / "research-only")
    try:
        with pytest.raises(ValueError, match="INVALID_SOLANA_CA"):
            manager.submit("1" * 33, "standard")
        assert not manager.jobs
    finally:
        manager.executor.shutdown(wait=True)
