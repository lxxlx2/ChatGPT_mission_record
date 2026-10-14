"""A05 complete original HTTP bytes source receipts: no 8KB UI truncation.

Synthetic account payloads are explicit; real Frank RPC evidence is NOT
claimed and must be collected independently after module Review.
"""
import hashlib
import json

import pytest

from mission_agent.mission_control.wallet_chain_capture import (
    SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM,
)
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_full_rpc_evidence import (
    MAX_RAW_RPC_BYTES, collect_owner_full_receipts, replay_owner_full_receipts,
)
from test_frank_a04_a05_chain_capture import (
    OWNER_A, MINT, ATA_A, ATA_B, entry, pk,
)


def _wire(index, slot, accounts):
    response = {
        "jsonrpc": "2.0", "id": index,
        "result": {"context": {"slot": slot}, "value": accounts},
    }
    return json.dumps(response, separators=(",", ":")).encode("utf-8")


def _network(spl, token2022):
    calls = []
    def read_raw(method, params, expected_id):
        calls.append((method, params, expected_id))
        return spl if expected_id == 1 else token2022
    return read_raw, calls


def test_complete_large_original_rpc_beyond_connector_8k_is_archived_and_replayed(tmp_path):
    accounts = [
        entry(OWNER_A, MINT, pk(i), SPL_TOKEN_PROGRAM, amount="1000000")
        for i in range(20, 90)
    ]
    spl = _wire(1, 3200, accounts)
    new = _wire(2, 3201, [
        entry(OWNER_A, MINT, ATA_B, TOKEN_2022_PROGRAM, amount="2500000")
    ])
    assert len(spl) > 8192
    reader, calls = _network(spl, new)
    root = tmp_path / "full"
    result = collect_owner_full_receipts(
        wallet=OWNER_A, evidence_root=root,
        read_raw=reader, min_context_slot=3199,
        observed_at_utc="2026-10-14T12:00:00+00:00",
    )
    m = result["manifest"]
    assert m["complete"] and len(m["receipts"]) == 2 and not m["missing"]
    assert [a["slot"] for a in m["receipts"]] == [3200, 3201]
    assert [x[2] for x in calls] == [1, 2]
    assert calls[0][1][2]["commitment"] == "finalized"
    assert calls[1][1][2]["minContextSlot"] == 3200
    bundle = tmp_path / "full" / result["bundle"].split("/")[-1]
    assert (bundle / "spl-token.json").read_bytes() == spl
    assert (bundle / "token-2022.json").read_bytes() == new
    assert m["receipts"][0]["sha256"] == hashlib.sha256(spl).hexdigest()
    assert m["full_32_mint_roster_verified"] is False
    reconstructed = replay_owner_full_receipts(
        bundle, expected_wallet=OWNER_A)
    assert reconstructed["capture_sha256"] == m["capture_sha256"]
    assert reconstructed["account_count"] == len(accounts) + 1
    assert reconstructed["mints"][0]["raw_amount_observed_sum"] == str(
        len(accounts) * 1000000 + 2500000)
    assert reconstructed["both_programs_observed"]
    assert reconstructed["same_slot_atomic"] is False
    assert reconstructed["wallet_nav_usd"] is None


def test_partial_truncated_program_never_yields_complete_or_importable_snapshot(tmp_path):
    spl = _wire(1, 1300, [
        entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM)])
    truncated = _wire(2, 1301, [
        entry(OWNER_A, MINT, ATA_B, TOKEN_2022_PROGRAM)])[:-9]
    reader, calls = _network(spl, truncated)
    capture = collect_owner_full_receipts(
        wallet=OWNER_A, evidence_root=tmp_path / "evidence",
        read_raw=reader, observed_at_utc="2026-10-14T12:00:00+00:00",
    )
    assert len(calls) == 2
    assert capture["snapshot"] is None
    assert capture["manifest"]["complete"] is False
    assert capture["manifest"]["capture_sha256"] is None
    assert capture["manifest"]["missing"][0]["program_id"] == TOKEN_2022_PROGRAM
    with pytest.raises(ValueError, match="OWNER_SOURCE_NOT_FULLY_VERIFIED"):
        replay_owner_full_receipts(
            capture["bundle"], expected_wallet=OWNER_A)
    assert (tmp_path / "evidence").is_dir()


def test_wire_bytes_over_cap_and_envelope_id_invalid_both_block_capture(tmp_path):
    valid = _wire(1, 1000, [])
    wrong_id = _wire(9, 1001, [])
    for name, bad in [
        ("too-big", b"X" * (MAX_RAW_RPC_BYTES + 1)),
        ("mismatch-id", wrong_id),
        ("rpc-error", b'{"jsonrpc":"2.0","id":2,"error":{"code":-32001}}'),
    ]:
        result = collect_owner_full_receipts(
            wallet=OWNER_A, evidence_root=tmp_path / name,
            read_raw=_network(valid, bad)[0],
            observed_at_utc="2026-10-14T12:00:00+00:00",
        )
        assert result["manifest"]["complete"] is False
        assert len(result["manifest"]["receipts"]) == 1
        assert result["snapshot"] is None


def test_replay_tampered_wire_body_and_receipt_slots_fail_without_sidecar_changes(tmp_path):
    spl = _wire(1, 1200, [])
    t22 = _wire(2, 1201, [])
    result = collect_owner_full_receipts(
        wallet=OWNER_A, evidence_root=tmp_path / "source",
        read_raw=_network(spl, t22)[0],
        observed_at_utc="2026-10-14T12:00:00+00:00",
    )
    bundle = result["bundle"]
    db = WalletEvidenceStore(tmp_path / "isolated.sqlite")
    try:
        original = replay_owner_full_receipts(bundle, expected_wallet=OWNER_A)
        assert db.capture_wallet(original)
        assert db.capture_wallet(original) is False
        assert db.count("ACCOUNT_CAPTURE") == 1
        p = result["bundle"] + "/spl-token.json"
        from pathlib import Path
        Path(p).write_bytes(spl.replace(b"1200", b"1300"))
        with pytest.raises(ValueError, match="OWNER_RAW_RPC_BYTES_SHA_MISMATCH"):
            replay_owner_full_receipts(bundle, expected_wallet=OWNER_A)
        assert db.count("ACCOUNT_CAPTURE") == 1
    finally:
        db.close()


def test_replay_wrong_wallet_and_manifest_program_identity_fail_closed(tmp_path):
    result = collect_owner_full_receipts(
        wallet=OWNER_A, evidence_root=tmp_path / "source",
        read_raw=_network(_wire(1, 800, []), _wire(2, 801, []))[0],
        observed_at_utc="2026-10-14T12:00:00+00:00",
    )
    with pytest.raises(ValueError, match="OWNER_SOURCE_NOT_FULLY_VERIFIED"):
        replay_owner_full_receipts(result["bundle"], expected_wallet=MINT)
    from pathlib import Path
    manifest_file = Path(result["bundle"]) / "manifest.json"
    manifest = json.loads(manifest_file.read_text("utf-8"))
    manifest["receipts"][1]["program_id"] = SPL_TOKEN_PROGRAM
    manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="OWNER_RECEIPT_SOURCE_IDENTITY_INVALID"):
        replay_owner_full_receipts(result["bundle"], expected_wallet=OWNER_A)


def test_no_calls_when_cli_is_plan_only(tmp_path, capsys):
    from scripts.frank_capture_owner_full_receipts import main
    out = tmp_path / "not-created"
    result = main(["--evidence-dir", str(out)])
    assert result == 0
    data = json.loads(capsys.readouterr().out)
    assert data["network_invoked"] is False
    assert not out.exists()


def test_min_context_slot_must_be_respected_by_complete_wire_responses(tmp_path):
    source = collect_owner_full_receipts(
        wallet=OWNER_A, evidence_root=tmp_path / "stale-provider",
        read_raw=_network(_wire(1, 900, []), _wire(2, 1200, []))[0],
        min_context_slot=1000,
        observed_at_utc="2026-10-14T12:00:00+00:00",
    )
    assert not source["manifest"]["complete"]
    assert source["snapshot"] is None
    assert source["manifest"]["missing"][0]["program_id"] == SPL_TOKEN_PROGRAM


def test_replay_refuses_higher_manifest_context_floor_than_actual_slot(tmp_path):
    from pathlib import Path
    captured = collect_owner_full_receipts(
        wallet=OWNER_A, evidence_root=tmp_path / "source",
        read_raw=_network(_wire(1, 1050, []), _wire(2, 1051, []))[0],
        observed_at_utc="2026-10-14T12:00:00+00:00",
    )
    manifest_file = Path(captured["bundle"]) / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest["min_context_slot"] = 1051
    manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="OWNER_RECEIPT_SOURCE_METADATA_MISMATCH"):
        replay_owner_full_receipts(captured["bundle"], expected_wallet=OWNER_A)


def test_owner_wire_archive_rejects_public_repository_checkout_path():
    from pathlib import Path
    from mission_agent.mission_control.wallet_full_rpc_evidence import _assert_directory
    repo = Path(__file__).resolve().parents[3]
    with pytest.raises(ValueError, match="OWNER_EVIDENCE_INSIDE_GIT_CHECKOUT_FORBIDDEN"):
        _assert_directory(repo / "accidentally-commit-wallet-source")


@pytest.fixture
def local_rpc_https_pair(tmp_path, monkeypatch):
    """Real TLS and HTTP sockets. No urllib/urlopen mocks or live RPC calls."""
    import ssl
    import subprocess
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from pathlib import Path

    cert, key = Path(tmp_path / "cert.pem"), Path(tmp_path / "key.pem")
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
        "-keyout", str(key), "-out", str(cert), "-days", "1",
        "-subj", "/CN=localhost",
        "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
    ], check=True, capture_output=True)
    monkeypatch.setenv("SSL_CERT_FILE", str(cert))
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1")

    state = {"mode": "normal", "https_requests": [], "http_requests": []}

    class PlainHTTP(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            state["http_requests"].append(self.path)
            rpc_id = int(self.path.rsplit("=", 1)[-1])
            wire = _wire(rpc_id, 5100 + rpc_id, [])
            self.send_response(200)
            self.send_header("Content-Length", str(len(wire)))
            self.end_headers()
            self.wfile.write(wire)

    plain = ThreadingHTTPServer(("127.0.0.1", 0), PlainHTTP)
    state["http_port"] = plain.server_port

    class SecureHTTPS(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            request_size = int(self.headers["Content-Length"])
            rpc = json.loads(self.rfile.read(request_size))
            rpc_id = rpc["id"]
            state["https_requests"].append((self.command, rpc_id))
            if state["mode"] == "redirect":
                self.send_response(302)
                self.send_header(
                    "Location",
                    f'http://127.0.0.1:{state["http_port"]}/reply?id={rpc_id}')
                self.end_headers()
                return
            wire = _wire(rpc_id, 5100 + rpc_id, [])
            if state["mode"] == "chunked_short":
                self.send_response(200)
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                self.wfile.write(f"{len(wire):X}\r\n".encode() +
                                 wire + b"\r\n")
                self.wfile.flush()
                self.close_connection = True
                return
            declared = len(wire)
            if state["mode"] == "short":
                declared += 100
            elif state["mode"] == "oversize":
                declared = MAX_RAW_RPC_BYTES + 1
            self.send_response(200)
            self.send_header("Content-Length", str(declared))
            self.end_headers()
            self.wfile.write(wire)
            self.wfile.flush()
            self.close_connection = True

    secure = ThreadingHTTPServer(("127.0.0.1", 0), SecureHTTPS)
    server_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_ssl.load_cert_chain(cert, key)
    secure.socket = server_ssl.wrap_socket(secure.socket, server_side=True)
    threads = [
        threading.Thread(target=server.serve_forever, daemon=True)
        for server in (plain, secure)
    ]
    for thread in threads:
        thread.start()
    try:
        yield state, f"https://localhost:{secure.server_port}/rpc"
    finally:
        for server in (plain, secure):
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(timeout=5)


def test_real_https_http_body_fully_received_can_be_replayed(
        tmp_path, local_rpc_https_pair):
    from scripts.frank_capture_owner_full_receipts import _wire_rpc
    state, url = local_rpc_https_pair
    receipt = collect_owner_full_receipts(
        wallet=OWNER_A, evidence_root=tmp_path / "tls-full",
        read_raw=_wire_rpc(url))
    assert receipt["manifest"]["complete"] is True
    assert state["https_requests"] == [("POST", 1), ("POST", 2)]
    assert state["http_requests"] == []
    assert [item["slot"] for item in receipt["manifest"]["receipts"]] == [
        5101, 5102]
    assert replay_owner_full_receipts(
        receipt["bundle"], expected_wallet=OWNER_A
    )["capture_sha256"] == receipt["manifest"]["capture_sha256"]


@pytest.mark.parametrize("mode", [
    "redirect", "short", "chunked_short", "oversize",
])
def test_real_https_transport_incomplete_or_downgraded_must_be_partial(
        mode, tmp_path, local_rpc_https_pair):
    from scripts.frank_capture_owner_full_receipts import _wire_rpc
    state, url = local_rpc_https_pair
    state["mode"] = mode
    receipt = collect_owner_full_receipts(
        wallet=OWNER_A, evidence_root=tmp_path / mode,
        read_raw=_wire_rpc(url))
    assert state["https_requests"] == [("POST", 1), ("POST", 2)]
    assert state["http_requests"] == []
    assert receipt["manifest"]["complete"] is False
    assert receipt["manifest"]["capture_sha256"] is None
    assert receipt["snapshot"] is None
    assert len(receipt["manifest"]["missing"]) == 2
    with pytest.raises(ValueError, match="OWNER_SOURCE_NOT_FULLY_VERIFIED"):
        replay_owner_full_receipts(receipt["bundle"], expected_wallet=OWNER_A)
