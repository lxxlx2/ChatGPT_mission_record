"""Bounded new-source workflow, real wire replay/SQLite/localhost, no live RPC."""
from datetime import datetime, timedelta, timezone
import http.client
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import threading

import pytest

from mission_agent.mission_control.wallet_chain_capture import SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM
from scripts import frank_f02_manual_refresh as refresh
from scripts.frank_f02_readonly_positions_api import make_handler
from scripts.frank_reconcile_frozen32_offline import ROSTER, load_frozen_roster
from test_frank_a04_a05_chain_capture import entry, pk

WALLET = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"


def reader(*, fail=False):
    calls = []
    mints = load_frozen_roster(ROSTER, WALLET)["records"]

    def read(method, params, ident):
        calls.append((method, params, ident))
        if fail and ident == 2:
            raise TimeoutError("synthetic unavailable")
        program = SPL_TOKEN_PROGRAM if ident == 1 else TOKEN_2022_PROGRAM
        data = [entry(WALLET, mints[ident - 1]["mint"], pk(90 + ident),
                      program, amount="123000000" if ident == 1 else "0")]
        return json.dumps({"jsonrpc": "2.0", "id": ident,
                           "result": {"context": {"slot": 5000 + ident},
                                      "value": data}}).encode()
    return read, calls


def test_default_plan_performs_no_rpc_or_writes(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(refresh, "SESSION_ROOT", tmp_path / "sessions")
    monkeypatch.setattr(refresh, "_wire_rpc", lambda *a: pytest.fail("network called"))
    assert refresh.main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "PLAN_ONLY"
    assert result["network_invoked"] is False
    assert not (tmp_path / "sessions").exists()


def test_fresh_replayed_source_to_real_http_and_ttl(tmp_path):
    read, calls = reader()
    summary, service = refresh.refresh_session(session_root=tmp_path / "sessions", read_raw=read)
    assert summary["status"] == "VERIFIED_MANUAL_RESEARCH_SESSION"
    assert summary["readiness"] == "FRESH_VERIFIED_ARCHIVED_OBSERVATION"
    assert len(calls) == 2
    assert calls[1][1][2]["minContextSlot"] == 5001
    assert all(c[0] == "getTokenAccountsByOwner" and c[1][2]["commitment"] == "finalized" for c in calls)
    assert summary["state_counts"] == {"OPEN_ACCOUNT_NONZERO": 1, "OPEN_ACCOUNT_ZERO": 1,
                                       "NO_OPEN_ACCOUNT_OBSERVED": 30}
    assert Path(summary["sidecar"]).stat().st_mode & 0o777 == 0o600
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(service))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port)
        conn.request("GET", "/api/research/positions")
        response = conn.getresponse()
        assert response.status == 200
        view = json.loads(response.read())
        assert view["verified_full_wire_capture_sha256"] == summary["capture_sha256"]
        assert view["mints"][0]["observed_quantity"] == "123.000000"
        assert view["mints"][1]["observed_raw_amount"] == "0"
        assert view["mints"][2]["observed_raw_amount"] is None
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    observed = datetime.fromisoformat(view["capture_observed_at_utc"])
    expired = service.positions(as_of_utc=observed + timedelta(seconds=301))
    assert expired["state_counts"] == {"SOURCE_UNAVAILABLE": 32}
    assert all(row["observed_quantity"] is None for row in expired["mints"])
    assert len(calls) == 2


def test_failed_new_attempt_never_serves_or_reuses_old_database(tmp_path):
    root = tmp_path / "sessions"
    read, _ = reader()
    old, _ = refresh.refresh_session(session_root=root, read_raw=read)
    old_bytes = Path(old["sidecar"]).read_bytes()
    read, calls = reader(fail=True)
    failure, service = refresh.refresh_session(session_root=root, read_raw=read)
    assert len(calls) == 2 and service is None
    assert failure["status"] == "PARTIAL_SOURCE"
    assert failure["sidecar_created"] is False and failure["old_source_reused"] is False
    assert not (Path(failure["session_directory"]) / "positions.sqlite").exists()
    assert Path(old["sidecar"]).read_bytes() == old_bytes
    assert failure["session_directory"] != old["session_directory"]


def test_cli_execute_without_serving_is_single_bounded_session(tmp_path, monkeypatch, capsys):
    read, calls = reader()
    monkeypatch.setattr(refresh, "SESSION_ROOT", tmp_path / "sessions")
    monkeypatch.setattr(refresh, "_wire_rpc", lambda url: read)
    assert refresh.main(["--execute"]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert len(calls) == 2 and summary["sidecar_created"] is True
    assert "LOCAL_RESEARCH_HTTP_READY" not in summary.values()


def test_occupied_port_fails_before_rpc_or_new_session(tmp_path, monkeypatch):
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(None))
    monkeypatch.setattr(refresh, "SESSION_ROOT", tmp_path / "sessions")
    monkeypatch.setattr(refresh, "_wire_rpc", lambda *a: pytest.fail("network called"))
    try:
        with pytest.raises(OSError):
            refresh.main(["--execute", "--serve", "--port", str(server.server_port)])
        assert not (tmp_path / "sessions").exists()
    finally:
        server.server_close()


def test_invalid_serve_flags_do_not_write(tmp_path, monkeypatch):
    monkeypatch.setattr(refresh, "SESSION_ROOT", tmp_path / "sessions")
    with pytest.raises(SystemExit):
        refresh.main(["--serve"])
    with pytest.raises(SystemExit):
        refresh.main(["--execute", "--port", "0"])
    assert not (tmp_path / "sessions").exists()


def test_old_captured_time_does_not_gain_freshness_on_session_import(tmp_path, monkeypatch):
    collect = refresh.collect_owner_full_receipts
    old = (datetime.now(timezone.utc) - timedelta(seconds=1000)).isoformat()
    monkeypatch.setattr(refresh, "collect_owner_full_receipts",
                        lambda **kw: collect(**kw, observed_at_utc=old))
    read, calls = reader()
    summary, service = refresh.refresh_session(session_root=tmp_path / "sessions", read_raw=read)
    assert summary["readiness"] == "STALE_ARCHIVED_SOURCE"
    assert summary["state_counts"] == {"SOURCE_UNAVAILABLE": 32}
    assert service.positions()["capture_age_seconds"] >= 1000
    assert len(calls) == 2
