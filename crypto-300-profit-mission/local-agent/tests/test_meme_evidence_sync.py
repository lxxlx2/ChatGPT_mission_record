"""No-network safety and end-to-end fake-Git tests for evidence export."""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from mission_agent.mission_control.evidence_sync import (
    BRANCH, PREFIX, EvidenceSpool, GitEvidencePublisher, canonical, safe
)

MINT = "HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy"
JOB = "1234567890abcdef1234567890abcdef"


class FakeGit(GitEvidencePublisher):
    """Byte-exact stand-in for GitHub contents: no actual network/auth."""
    def __init__(self, spool, *, now=1791711000):
        super().__init__(spool, clock=lambda: now)
        self.remote = {}
        self.calls = []

    def _gh(self, method, remote, payload=None):
        self.calls.append((method, remote))
        assert remote.startswith(PREFIX + "/")
        if method == "GET":
            raw = self.remote.get(remote)
            if raw is None:
                return None
            return {"sha": "stable-cas", "encoding": "base64",
                    "content": base64.b64encode(raw).decode("ascii")}
        if method == "PUT":
            assert payload["branch"] == BRANCH
            assert "ghp_" not in str(payload)
            raw = base64.b64decode(payload["content"])
            self.remote[remote] = raw
            return {"content": {"sha": "new-sha"}}
        raise AssertionError(method)


def test_ca_snapshot_sanitizes_and_reads_back(tmp_path):
    queue = EvidenceSpool(tmp_path)
    report = {"mint": MINT, "schema_version": 2, "metrics": {"RAW_TOP10": "25"},
              "holders": [{"owner": MINT, "supply_pct": "1.1"}],
              "market": {"url": "https://public.example/token?api_key=secret123",
                         "price_usd": "1"},
              "wallet": {"seed_phrase": "never", "token": "ghp_never"},
              "rpc_endpoint": "https://private.example/secret-api-key",
              "execution_quote_30_usdc": {"status": "OK"},
              "coverage": {"top_accounts_resolved": 20}}
    queue.ca_done(mint=MINT, job_id=JOB, report=report)
    source = json.loads((queue.pending / "ca" / (JOB + ".json")).read_text())
    assert "wallet" not in source["data"]
    assert "execution_quote_30_usdc" not in source["data"]
    assert "rpc_endpoint" not in source["data"]
    assert source["data"]["holders"][0]["owner"] == MINT
    assert source["data"]["market"]["url"] == "[REDACTED]"
    pub = FakeGit(queue)
    result = pub.sync()
    assert result["status"] == "SYNC_OK"
    assert result["uploaded"] == 1
    assert list((queue.pending / "ca").glob("*.json")) == []
    assert f"{PREFIX}/ca/{MINT}/{JOB}.json" in pub.remote
    assert any(op == "GET" for op, _ in pub.calls)


def test_invalid_ca_identity_does_not_queue(tmp_path):
    q = EvidenceSpool(tmp_path)
    with pytest.raises(ValueError):
        q.ca_done(mint="../escape", job_id=JOB, report={"mint": MINT})
    with pytest.raises(ValueError):
        q.ca_done(mint=MINT, job_id=JOB, report={"mint": "mismatch"})
    assert list((q.pending).rglob("*.json")) == []


def test_frank_poll_is_deduped_and_15min_flush(tmp_path):
    q = EvidenceSpool(tmp_path)
    last = "2026-10-11T01:00:14+00:00"
    health = {"poll_count": 500, "last_poll_at": last, "last_successful_poll": last,
              "status": "RUNNING", "last_processed_slot": 123,
              "last_processed_signature": "safe-sig", "rpc_url": "https://host/key",
              "gmail_password": "secret"}
    p = q.frank_scan(poll_count=500, health=health)
    duplicate = q.frank_scan(poll_count=500, health=health)
    assert p == duplicate
    assert json.loads(p.read_text())["bucket_utc"] == "2026-10-11/0100"
    assert "rpc_url" not in p.read_text() and "secret" not in p.read_text()
    open_bucket = FakeGit(q, now=datetime(2026, 10, 11, 1, 5, tzinfo=timezone.utc).timestamp())
    assert open_bucket.sync()["uploaded"] == 0
    ready = FakeGit(q, now=datetime(2026, 10, 11, 1, 16, tzinfo=timezone.utc).timestamp())
    res = ready.sync()
    assert res["uploaded"] == 1
    data = json.loads(ready.remote[f"{PREFIX}/frank/2026-10-11/0100.json"])
    assert data["record_count"] == 1
    assert data["events"][0]["poll_count"] == 500


def test_failed_network_retains_queue(tmp_path):
    q = EvidenceSpool(tmp_path)
    q.ca_done(mint=MINT, job_id=JOB, report={"mint": MINT, "coverage": {}})
    pub = FakeGit(q)
    def fail(method, remote, payload=None):
        raise RuntimeError("FAKE_GH_UNAVAILABLE")
    pub._gh = fail
    result = pub.sync()
    assert result["status"] == "SYNC_PARTIAL"
    assert result["uploaded"] == 0
    assert (q.pending / "ca" / (JOB + ".json")).exists()


def test_remote_idempotent_and_no_duplicate_frank_event(tmp_path):
    q = EvidenceSpool(tmp_path)
    last = "2026-10-11T01:01:00+00:00"
    q.frank_scan(poll_count=42, health={"status": "RUNNING", "last_poll_at": last})
    pub = FakeGit(q, now=datetime(2026, 10, 11, 1, 18, tzinfo=timezone.utc).timestamp())
    assert pub.sync()["uploaded"] == 1
    p = q.frank_scan(poll_count=42, health={"status": "RUNNING", "last_poll_at": last})
    assert p.is_file()
    assert pub.sync()["uploaded"] == 1
    snap = json.loads(pub.remote[f"{PREFIX}/frank/2026-10-11/0100.json"])
    assert snap["record_count"] == 1
    assert len(snap["events"]) == 1


def test_gh_client_passes_content_via_stdin_and_scrubs_errors(tmp_path):
    q = EvidenceSpool(tmp_path)
    pub = GitEvidencePublisher(q)
    with patch("subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], 0, stdout=b'{"sha":"123"}', stderr=b"")
        pub._gh("PUT", PREFIX + "/ca/" + MINT + "/" + JOB + ".json",
                {"branch": BRANCH, "content": "secret_base64"})
        args, kwargs = run.call_args
        assert "--input" in args[0]
        assert "secret_base64" not in " ".join(args[0])
        assert b"secret_base64" in kwargs["input"]
        assert kwargs["timeout"] == 25
    with patch("subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], 1, stdout=b"",
                            stderr=b"https://secret-provider.invalid?api_key=private_key")
        with pytest.raises(RuntimeError, match="GH_API_PUT_FAILED"):
            pub._gh("PUT", PREFIX + "/ca/" + MINT + "/" + JOB + ".json", {})


def test_no_private_detail_in_generic_sanitizer():
    payload = {"api_key": "secret", "bearer": "token", "private_notes": "none",
               "holders": [{"owner": MINT, "source": "DEX"}],
               "url": "https://safe.example/path?wallet=abc",
               "trade_evidence": [{"signature": "a"}]}
    result = safe(payload)
    assert "api_key" not in result
    assert "bearer" not in result
    assert "private_notes" not in result
    assert result["holders"][0]["owner"] == MINT
    assert result["url"] == "https://safe.example/path"



def test_frank_trade_and_signal_samples_are_data_only(tmp_path):
    spool = EvidenceSpool(tmp_path)
    health = {"poll_count": 9, "last_poll_at": "2026-10-11T02:01:00+00:00",
              "last_processed_signature": "sig", "status": "RUNNING"}
    row = {"mint": MINT, "signature": "tx-1", "side": "SELL", "block_time": 1791712800,
           "observed_quote_asset": "USDC", "observed_quote_quantity": "7031.556770",
           "body": {"gmail_token": "must_not_export"}, "local_rpc_key": "must_not_export"}
    signal = {"mint": MINT, "pattern": "MULTIPLE",
              "position_state": "OPEN", "private_key": "must_not_export"}
    file = spool.frank_scan(poll_count=9, health=health,
                            recent_trades=[row], signal_candidates=[signal])
    exported = json.loads(file.read_text())
    assert exported["recent_recognized_trades_sample"][0]["observed_quote_quantity"] == "7031.556770"
    assert exported["signal_eligible_candidates_sample"][0]["pattern"] == "MULTIPLE"
    assert "gmail_token" not in file.read_text()
    assert "must_not_export" not in file.read_text()
    assert exported["chain_completeness_verified"] is False

def test_code_is_opt_in_and_not_added_to_frank_writer():
    root = Path(__file__).resolve().parents[1]
    server = (root / "mission_agent" / "mission_control" / "server.py").read_text()
    service = (root / "mission_agent" / "mission_control" / "service.py").read_text()
    writer = (root / "scripts" / "frank_local_signal_service.py").read_text()
    assert 'MISSION_EVIDENCE_EXPORT_ENABLED' in server
    assert 'MISSION_EVIDENCE_EXPORT_ENABLED' in service
    assert 'MISSION_EVIDENCE_EXPORT_ENABLED' not in writer
