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


@pytest.mark.parametrize("authority", ["example.test:fixture-secret", "example.test:65536", "@example.test", ":@example.test"])
def test_invalid_authority_is_rejected_before_transport(tmp_path, authority):
    path = _private_config(tmp_path, "https://" + authority)
    with pytest.raises(RuntimeError, match="^FRANK_RPC_CONFIG_UNAVAILABLE_OR_INVALID$"):
        configured_scanner_rpc(path)


@pytest.mark.parametrize("code,expected", [(-32005, "-32005"), (True, "RPC_ERROR"),
                                        (None, "RPC_ERROR"), ({"url": "fixture-secret"}, "RPC_ERROR")])
def test_only_numeric_provider_error_codes_are_exposed(code, expected):
    import json
    class ErrorResponse(_Response):
        def read(self): return json.dumps({"error": {"code": code}}).encode()
    with pytest.raises(RPCFailure) as exc:
        SolanaRPC(request=lambda *a, **k: ErrorResponse()).call("getSlot", [])
    assert str(exc.value) == expected


def test_provider_error_cannot_leak_private_url_into_scanner_health(tmp_path):
    import json
    from mission_agent.frank.rpc import WALLET
    from mission_agent.signals.scanner import Scanner, WalletRPC
    from mission_agent.signals.store import Ledger

    endpoint = "https://example.test/fixture-private-token"
    class ErrorResponse(_Response):
        def read(self):
            return json.dumps({"error": {"code": endpoint, "message": endpoint}}).encode()

    ledger = Ledger(tmp_path / "db")
    ledger.checkpoint(WALLET, "seed", 11)
    rpc = WalletRPC(WALLET, endpoint=endpoint, request=lambda *a, **k: ErrorResponse())
    scanner = Scanner(ledger, {WALLET: "frank"}, tmp_path / "raw", {WALLET: rpc})
    with pytest.raises(RPCFailure, match="^RPC_ERROR$"):
        scanner.cycle(WALLET)
    health = ledger.db.execute("SELECT body FROM health").fetchone()[0]
    assert endpoint not in health and "fixture-private-token" not in health
    assert ledger.cursor(WALLET)["signature"] == "seed"
    ledger.db.close()


def test_private_transport_timeout_resume_and_duplicate_pages(tmp_path):
    import json
    from mission_agent.frank.rpc import WALLET
    from mission_agent.signals.scanner import Scanner, WalletRPC
    from mission_agent.signals.store import Ledger
    from test_frank_fm import tx

    endpoint = "https://example.test/fixture-private-token"
    calls, sleeps = [], []
    fail = True
    class Result(_Response):
        def __init__(self, value): self.value = value
        def read(self): return json.dumps({"result": self.value}).encode()
    def request(req, timeout):
        payload = json.loads(req.data)
        method, params = payload["method"], payload["params"]
        calls.append((req.full_url, timeout, method, params))
        if method == "getSignaturesForAddress":
            assert params[0] == WALLET and params[1]["commitment"] == "finalized"
            if "before" not in params[1]:
                return Result([{"signature": "new", "slot": 13}, {"signature": "older", "slot": 12}])
            assert params[1]["before"] == "older"
            return Result([{"signature": "older", "slot": 12}, {"signature": "seed", "slot": 11}])
        assert method == "getTransaction"
        if params[0] == "new" and fail:
            raise TimeoutError(endpoint)
        value = tx()
        value["slot"] = 12 if params[0] == "older" else 13
        value["transaction"]["signatures"] = [params[0]]
        return Result(value)

    ledger = Ledger(tmp_path / "db")
    ledger.checkpoint(WALLET, "seed", 11)
    rpc = WalletRPC(WALLET, endpoint=endpoint, request=request, sleep=sleeps.append,
                    monotonic=lambda: 0, jitter=lambda: 0)
    scanner = Scanner(ledger, {WALLET: "frank"}, tmp_path / "raw", {WALLET: rpc})
    with pytest.raises(RPCFailure, match="^TIMEOUT_OR_NETWORK$"):
        scanner.cycle(WALLET)
    assert ledger.cursor(WALLET)["signature"] == "older"
    assert ledger.db.execute("SELECT state FROM signature_detections WHERE signature='new'").fetchone()[0] == "RAW_PENDING"
    assert [c[3][0] for c in calls if c[2] == "getTransaction"] == ["older", "new", "new", "new"]
    assert sleeps.count(1) == 1 and sleeps.count(2) == 1
    assert endpoint not in ledger.db.execute("SELECT body FROM health").fetchone()[0]
    ledger.db.close()

    fail = False
    ledger = Ledger(tmp_path / "db")
    scanner = Scanner(ledger, {WALLET: "frank"}, tmp_path / "raw", {WALLET: rpc})
    scanner.cycle(WALLET)
    assert ledger.cursor(WALLET)["signature"] == "new"
    scanner.cycle(WALLET)
    assert ledger.db.execute("SELECT count(*) FROM signatures").fetchone()[0] == 2
    assert ledger.db.execute("SELECT count(*) FROM signature_detections").fetchone()[0] == 2
    assert ledger.db.execute("SELECT count(*) FROM outbox").fetchone()[0] == 0
    assert json.loads(ledger.db.execute("SELECT body FROM health").fetchone()[0])["consecutive_errors"] == 0
    assert all(url == endpoint and timeout == 20 for url, timeout, *_ in calls)
    ledger.db.close()
