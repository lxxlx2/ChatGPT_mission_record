"""Offline tests for configured RPC injection into the existing Frank scanner."""
from pathlib import Path

import pytest

from mission_agent.frank.rpc import RPC, RPCFailure, SolanaRPC
from scripts.frank_local_signal_service import configured_scanner_rpc


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return b'{"jsonrpc":"2.0","id":1,"result":467}'


def _private_config(tmp_path, value):
    path = tmp_path / "solana_rpc_urls"
    path.write_text(value, encoding="utf-8")
    path.chmod(0o600)
    return path


def test_existing_private_rpc_first_endpoint_selected(tmp_path):
    url = "https://solana-mainnet.g.alchemy.com/v2/fixture-only"
    path = _private_config(tmp_path, url + ",https://api.mainnet.solana.com")
    assert configured_scanner_rpc(path) == url


def test_public_rpc_is_default_for_legacy_callers():
    assert SolanaRPC().endpoint == RPC


def test_rpc_request_uses_explicit_endpoint_without_public_fallback():
    endpoint = "https://solana-mainnet.g.alchemy.com/v2/fixture-only"
    actual = []

    def mock_request(req, timeout):
        actual.append((req.full_url, timeout))
        return _Response()

    client = SolanaRPC(request=mock_request, sleep=lambda _: None, endpoint=endpoint)
    assert client.call("getSlot", [{"commitment": "finalized"}]) == 467
    assert actual == [(endpoint, 20)]
    with pytest.raises(ValueError, match="READ_ONLY_METHOD_ALLOWLIST"):
        client.call("sendTransaction", [])
    assert len(actual) == 1


@pytest.mark.parametrize("invalid", [
    "http://example.com/solana",
    "not-a-url",
    "https://",
    "https://user:pass@example.com/",
    "https://example.com/#fragment",
    "https://example.com/ with-spaces",
    "",
])
def test_invalid_rpc_config_fails_closed_without_leaking_url(tmp_path, invalid):
    path = _private_config(tmp_path, invalid)
    with pytest.raises(RuntimeError, match="^FRANK_RPC_CONFIG_UNAVAILABLE_OR_INVALID$") as exc:
        configured_scanner_rpc(path)
    assert invalid not in str(exc.value) if invalid else True


def test_missing_rpc_file_fails_closed(tmp_path):
    with pytest.raises(RuntimeError, match="FRANK_RPC_CONFIG_UNAVAILABLE_OR_INVALID"):
        configured_scanner_rpc(tmp_path / "missing")


def test_world_readable_rpc_config_is_rejected(tmp_path):
    path = _private_config(tmp_path, "https://example.com/private-key")
    path.chmod(0o644)
    with pytest.raises(RuntimeError, match="FRANK_RPC_CONFIG_UNAVAILABLE_OR_INVALID"):
        configured_scanner_rpc(path)


def test_symlink_rpc_config_is_rejected(tmp_path):
    target = _private_config(tmp_path, "https://example.com/private-key")
    symlink = tmp_path / "link"
    symlink.symlink_to(target)
    with pytest.raises(RuntimeError, match="FRANK_RPC_CONFIG_UNAVAILABLE_OR_INVALID"):
        configured_scanner_rpc(symlink)
