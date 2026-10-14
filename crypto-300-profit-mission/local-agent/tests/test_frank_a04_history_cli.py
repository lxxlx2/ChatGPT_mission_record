"""Manual A04 private-sidecar command must be plan-only by default."""
import json
from pathlib import Path
import runpy

import pytest

from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore


ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def pubkey(n):
    integer = int.from_bytes(bytes([n]) * 32, "big")
    encoded = ""
    while integer:
        integer, digit = divmod(integer, 58)
        encoded = ALPHABET[digit] + encoded
    return encoded


def _registry(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps({
        "schema_version": 2,
        "persons": [
            {"person_id": "frank", "display_name": "Frank",
             "enabled": True, "research_enabled": True,
             "wallets": [{"chain": "solana", "address": pubkey(3),
                          "role": "PRIMARY", "valid_from_slot": 100}]},
            {"person_id": "research_b", "display_name": "Research B",
             "enabled": False, "research_enabled": True,
             "wallets": [{"chain": "solana", "address": pubkey(4),
                          "role": "PRIMARY", "valid_from_slot": 100}]},
        ],
    }), encoding="utf-8")
    return path


def _cli():
    file = (Path(__file__).resolve().parents[1] /
            "scripts/frank_research_history_readonly.py")
    return runpy.run_path(str(file))


def test_plan_never_creates_sidecar_or_network_access(tmp_path, capsys):
    cli = _cli()
    sidecar = tmp_path / "archive.sqlite"
    assert cli["main"]([
        "--registry", str(_registry(tmp_path)),
        "--sidecar", str(sidecar),
        "--max-pages", "2", "--tx-budget", "12",
    ]) == 0
    response = json.loads(capsys.readouterr().out)
    assert response["status"] == "PLAN_ONLY"
    assert response["network_invoked"] is False
    assert response["production_written"] is False
    assert response["notifications_enabled"] is False
    assert response["person_id"] == "frank"
    assert not sidecar.exists()


def test_person_scoping_rejects_unknown_before_any_network(tmp_path):
    cli = _cli()
    with pytest.raises(KeyError):
        cli["main"]([
            "--registry", str(_registry(tmp_path)),
            "--person-id", "unknown",
            "--sidecar", str(tmp_path / "bad.sqlite"),
        ])
    assert not (tmp_path / "bad.sqlite").exists()


def test_second_person_research_scope_has_no_live_permission(tmp_path, capsys):
    cli = _cli()
    sidecar = tmp_path / "research_b.sqlite"
    assert cli["main"]([
        "--registry", str(_registry(tmp_path)),
        "--person-id", "research_b", "--sidecar", str(sidecar),
    ]) == 0
    reply = json.loads(capsys.readouterr().out)
    assert reply["wallet"] == pubkey(4)
    assert reply["notifications_enabled"] is False
    assert not sidecar.exists()


def test_invalid_budget_rejected_without_creating_sidecar(tmp_path):
    cli = _cli()
    sidecar = tmp_path / "invalid.sqlite"
    with pytest.raises(ValueError, match="REPLAY_BUDGET_OUT_OF_RANGE"):
        cli["main"]([
            "--registry", str(_registry(tmp_path)),
            "--sidecar", str(sidecar), "--page-size", "1001",
        ])
    assert not sidecar.exists()


def test_live_execution_does_not_touch_prod_sqlite_and_uses_research_sidecar(tmp_path, capsys):
    cli = _cli()
    sidecar = tmp_path / "history.sqlite"
    forward = tmp_path / "forward.sqlite"
    forward.write_bytes(b"PRODUCTION_DO_NOT_TOUCH")
    seen = []
    def stub_url(_url):
        def call(method, params):
            seen.append(method)
            assert method == "getSignaturesForAddress"
            assert params[1]["commitment"] == "finalized"
            return {"result": []}
        return call
    cli["main"].__globals__["rpc_reader"] = stub_url
    assert cli["main"]([
        "--registry", str(_registry(tmp_path)), "--sidecar", str(sidecar),
        "--execute", "--max-pages", "1",
    ]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["pagination_end_observed"] is True
    assert result["history_complete"] is False
    assert result["production_written"] is False
    assert seen == ["getSignaturesForAddress"]
    assert forward.read_bytes() == b"PRODUCTION_DO_NOT_TOUCH"
    store = WalletEvidenceStore(sidecar, read_only=True)
    try:
        assert store.count("RAW_TX") == 0
    finally:
        store.close()


def test_rpc_url_requires_https_without_exposing_token():
    rpc = _cli()["rpc_reader"]
    with pytest.raises(ValueError, match="HTTPS_RPC_URL_REQUIRED"):
        rpc("http://api.example.com/?key=secret")
    with pytest.raises(ValueError, match="HTTPS_RPC_URL_REQUIRED"):
        rpc("https://username:password@rpc.example.com")
