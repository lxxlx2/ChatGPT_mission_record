"""Offline tests for configured RPC injection into the existing Frank scanner."""
import json
from pathlib import Path
import sys

import pytest

from mission_agent.frank.rpc import RPC, RPCFailure, SolanaRPC
from scripts import frank_local_signal_service as service
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


def test_unset_explicit_path_reuses_existing_mac_config(monkeypatch, tmp_path):
    endpoint = "https://example.test/fixture-private-token"
    root = tmp_path / "Library/Application Support/FrankMeme"
    root.mkdir(parents=True)
    _private_config(root, endpoint)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert configured_scanner_rpc() == endpoint


def _scanner_args(tmp_path, config, *, check=False):
    policy = Path(service.__file__).resolve().parents[1] / "config/frank_local_signal_v1.json"
    args = [
        "frank_local_signal_service.py",
        "--root", str(tmp_path),
        "--registry", str(tmp_path / "registry.json"),
        "--policy", str(policy),
        "--authority-lock", str(tmp_path / "authority.lock"),
        "--rpc-config", str(config),
    ]
    return args + (["--check"] if check else [])


@pytest.mark.parametrize("check", [False, True])
def test_cli_rejects_invalid_explicit_config_before_using_any_default_or_state(
    monkeypatch, tmp_path, capsys, check,
):
    fallback = tmp_path / "Library/Application Support/FrankMeme"
    fallback.mkdir(parents=True)
    _private_config(fallback, "https://example.test/valid-default")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    config = _private_config(tmp_path, "https://example.test:fixture-private-token")
    monkeypatch.setattr(sys, "argv", _scanner_args(tmp_path, config, check=check))
    monkeypatch.setattr(service, "load_policy", lambda *a: pytest.fail("policy must not be loaded"))
    monkeypatch.setattr(service, "Ledger", lambda *a: pytest.fail("ledger must not be opened"))
    monkeypatch.setattr(service, "WalletRPC", lambda *a, **k: pytest.fail("RPC must not be initialized"))
    with pytest.raises(SystemExit) as stopped:
        service.main()
    assert stopped.value.code == 2
    out = capsys.readouterr()
    assert out.out == "" and out.err == "FRANK_RPC_CONFIG_UNAVAILABLE_OR_INVALID\n"
    assert not (tmp_path / "authority.lock").exists()


def _scanner_state(tmp_path):
    from mission_agent.frank.rpc import WALLET
    from mission_agent.signals.store import Ledger

    wallets = [WALLET, "fixture-second-wallet"]
    (tmp_path / "registry.json").write_text(json.dumps({
        "persons": [{"person_id": "frank", "enabled": True, "wallets": [
            {"chain": "solana", "address": wallet} for wallet in wallets
        ]}],
    }))
    ledger = Ledger(tmp_path / "forward.sqlite")
    for wallet in wallets:
        ledger.checkpoint(wallet, "seed", 11)
    ledger.db.close()
    return wallets


def test_explicit_config_preflight_passes_without_network_or_endpoint_output(monkeypatch, tmp_path, capsys):
    wallets = _scanner_state(tmp_path)
    endpoint = "https://example.test/fixture-private-token"
    config = _private_config(tmp_path, endpoint)
    before = {path.name:path.read_bytes() for path in tmp_path.iterdir()}
    monkeypatch.setattr(sys, "argv", _scanner_args(tmp_path, config, check=True))
    monkeypatch.setattr(service, "Ledger", lambda *a, **k: pytest.fail("preflight must not initialize a writable ledger"))
    monkeypatch.setattr(service, "Engine", lambda *a, **k: pytest.fail("preflight must not migrate the model"))
    monkeypatch.setattr(service, "Scanner", lambda *a, **k: pytest.fail("preflight must not run Scanner"))
    monkeypatch.setattr(service, "WalletRPC", lambda *a, **k: pytest.fail("preflight must not initialize RPC"))
    service.main()
    output = capsys.readouterr()
    assert endpoint not in output.out and not output.err
    status = json.loads(output.out)
    assert status["status"] == "PREFLIGHT_PASS" and len(status["cursor"]) == len(wallets)
    assert not (tmp_path / "authority.lock").exists()
    assert {path.name:path.read_bytes() for path in tmp_path.iterdir()} == before


def test_preflight_holds_on_snapshot_with_pending_wal_bytes(monkeypatch, tmp_path, capsys):
    _scanner_state(tmp_path)
    config = _private_config(tmp_path, "https://example.test/fixture-private-token")
    (tmp_path / "forward.sqlite-wal").write_bytes(b"unfinished local writes")
    monkeypatch.setattr(sys, "argv", _scanner_args(tmp_path, config, check=True))
    with pytest.raises(SystemExit) as stopped:
        service.main()
    assert stopped.value.code == 2
    assert capsys.readouterr().err == "SCANNER_SNAPSHOT_WAL_NOT_INCLUDED\n"
    assert not (tmp_path / "authority.lock").exists()


def test_scanner_claims_single_writer_lock_before_database_setup(monkeypatch, tmp_path):
    _scanner_state(tmp_path)
    config = _private_config(tmp_path, "https://example.test/fixture-private-token")
    monkeypatch.setattr(sys, "argv", _scanner_args(tmp_path, config))
    monkeypatch.setattr(service, "Ledger", lambda *a, **k: pytest.fail("locked writer must not open the database"))
    with (tmp_path / "authority.lock").open("a") as held:
        service.fcntl.flock(held, service.fcntl.LOCK_EX|service.fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            service.main()
    assert not (tmp_path / "service.lock").exists()


def test_service_entrypoint_injects_explicit_endpoint_into_every_wallet(monkeypatch, tmp_path):
    expected_wallets = _scanner_state(tmp_path)
    endpoint = "https://example.test/fixture-private-token"
    config = _private_config(tmp_path, endpoint + ",https://example.test/unused")
    monkeypatch.setattr(sys, "argv", _scanner_args(tmp_path, config))
    monkeypatch.setattr(service.signal, "signal", lambda *a: None)
    monkeypatch.setattr(service, "LocalNotifier", lambda *a, **k: pytest.fail("test must not initialize a notifier"))
    received = []

    def stop_before_transport(ledger, wallets, raw, *, rpcs, mode):
        received.extend(rpcs)
        assert mode == "LIVE"
        assert set(wallets) == set(rpcs) == set(expected_wallets)
        assert all(rpc.wallet == wallet and rpc.endpoint == endpoint for wallet, rpc in rpcs.items())
        ledger.db.close()
        raise SystemExit(0)

    monkeypatch.setattr(service, "Scanner", stop_before_transport)
    with pytest.raises(SystemExit) as stopped:
        service.main()
    assert stopped.value.code == 0 and received == expected_wallets


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
    "https://example.com/#",
    "https://example.com/path\x00",
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


def test_directory_rpc_config_is_rejected_and_descriptor_closed(monkeypatch, tmp_path):
    opened = []
    original_fstat = service.os.fstat

    def track(fd):
        opened.append(fd)
        return original_fstat(fd)

    monkeypatch.setattr(service.os, "fstat", track)
    with pytest.raises(RuntimeError, match="^FRANK_RPC_CONFIG_UNAVAILABLE_OR_INVALID$"):
        configured_scanner_rpc(tmp_path)
    assert len(opened) == 1
    with pytest.raises(OSError):
        original_fstat(opened[0])


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
