"""No-network safety and end-to-end fake-Git tests for evidence export."""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import zipfile
from unittest.mock import patch

import pytest

from scripts.frank_evidence_bootstrap import refresh_zip_summary

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



def test_large_ca_report_preserves_complete_sanitized_evidence_in_git(tmp_path):
    queue = EvidenceSpool(tmp_path)
    # 700 independent bounded evidence rows are deliberately larger than
    # the old single-file cutoff: never silently discard their signatures.
    evidence = [{"signature": f"sig-{i:06d}", "owner": MINT,
                 "amount_raw": str(i), "memo": "x" * 350}
                for i in range(700)]
    report = {"mint": MINT, "schema_version": 2,
              "trade_evidence": evidence, "metrics": {"RAW_TOP10": "25"},
              "rpc_url": "https://secret.invalid/key"}
    queue.ca_done(mint=MINT, job_id=JOB, report=report)
    manifest = json.loads((queue.pending / "ca" / (JOB + ".json")).read_text())
    assert manifest["export_completeness"] == "ALL_SELECTED_FIELDS_IN_CHUNKS"
    assert len(manifest["data_chunks"]) >= 2
    pub = FakeGit(queue)
    assert pub.sync()["status"] == "SYNC_OK"
    assert list((queue.pending / "ca").glob("*.json")) == []
    chunks = []
    for rec in manifest["data_chunks"]:
        remote = f"{PREFIX}/ca/{MINT}/{JOB}/{rec['file']}"
        chunk = json.loads(pub.remote[remote])
        chunks.append(base64.b64decode(chunk["payload_b64"]))
    reconstructed = json.loads(b"".join(chunks))
    assert len(reconstructed["trade_evidence"]) == 700
    assert reconstructed["trade_evidence"][-1]["signature"] == "sig-000699"
    assert reconstructed["metrics"]["RAW_TOP10"] == "25"
    assert "rpc_url" not in reconstructed


def test_incomplete_ca_part_retains_manifest_and_pending_files(tmp_path):
    queue = EvidenceSpool(tmp_path)
    report = {"mint": MINT, "trade_evidence":
              [{"signature": f"sig-{i}", "memo": "z" * 700} for i in range(700)]}
    queue.ca_done(mint=MINT, job_id=JOB, report=report)
    meta = json.loads((queue.pending / "ca" / (JOB + ".json")).read_text())
    assert meta["data_chunks"]
    first_part = queue.pending / "ca-parts" / JOB / meta["data_chunks"][0]["file"]
    first_part.unlink()
    result = FakeGit(queue).sync()
    assert result["status"] == "SYNC_PARTIAL"
    assert (queue.pending / "ca" / (JOB + ".json")).exists()

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
               "holders": [{"owner": MINT, "pubkey": MINT, "source": "DEX"}],
               "url": "https://safe.example/path?wallet=abc",
               "trade_evidence": [{"signature": "a"}]}
    result = safe(payload)
    assert "api_key" not in result
    assert "bearer" not in result
    assert "private_notes" not in result
    assert result["holders"][0]["owner"] == MINT
    assert result["holders"][0]["pubkey"] == MINT
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


def test_mac_bootstrap_zip_final_status_is_verified_and_preserves_evidence(tmp_path):
    packet = tmp_path / "packet.zip"
    with zipfile.ZipFile(packet, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("summary.json", json.dumps({"git_sync": "NOT_REQUESTED"}))
        archive.writestr("sanitized-pending/frank/event.json", '{"poll_count":200}')
        archive.writestr("frank-d0-local-index.json", '{"local_observed_mints":32}')
    refresh_zip_summary(packet, {"git_sync": "SYNC_OK", "frank": "QUEUED", "ca_queued": 2})
    with zipfile.ZipFile(packet) as archive:
        assert archive.namelist().count("summary.json") == 1
        assert json.loads(archive.read("summary.json"))["git_sync"] == "SYNC_OK"
        assert json.loads(archive.read("sanitized-pending/frank/event.json"))["poll_count"] == 200
        assert json.loads(archive.read("frank-d0-local-index.json"))["local_observed_mints"] == 32
    assert not packet.with_name(packet.name + ".summary-tmp").exists()


def test_git_frank_scan_keeps_full_nonsignal_watchlist(tmp_path):
    spool = EvidenceSpool(tmp_path)
    health = {"poll_count": 900, "status": "RUNNING",
              "last_poll_at": "2026-10-11T03:01:00+00:00"}
    rows = []
    for i in range(32):
        rows.append({"mint": MINT if i == 0 else "H" + str(i).zfill(42),
                     "watch_state": "MODEL_OPEN" if i < 5 else "HISTORY_SELL_ONLY",
                     "local_recognized_buys": 0 if i >= 5 else 1,
                     "local_recognized_sells": 1 if i >= 5 else 0,
                     "wallet_secret": "DO_NOT_PUBLISH",
                     "current_chain_balance_verified": False})
    p = spool.frank_scan(poll_count=900, health=health,
                         observed_watchlist={"summary": {"total_observed": 32}, "rows": rows},
                         signal_candidates=[])
    j = json.loads(p.read_text())
    assert len(j["observed_watchlist"]["rows"]) == 32
    assert j["observed_watchlist"]["total_observed"] == 32
    assert j["observed_watchlist"]["truncated"] is False
    assert j["signal_eligible_candidates_sample"] == []
    assert "DO_NOT_PUBLISH" not in p.read_text()
    assert j["observed_watchlist"]["rows"][0]["watch_state"] == "MODEL_OPEN"


def test_complete_frank_history_export_roundtrip_with_large_chunks(tmp_path):
    spool = EvidenceSpool(tmp_path)
    sigs = [{"signature": f"sig-{i:04d}", "side": "BUY",
             "mint": MINT, "memo": "public-data-" + "w" * 350,
             "gmail_api_key": "DO_NOT_EXPORT"}
            for i in range(700)]
    report = {
        "schema_version": 1, "person_id": "frank",
        "source_scope": "COMPLETE_LOCAL_RECOGNIZED_TRADES_NOT_FULL_CHAIN",
        "record_count": 700, "records": sigs,
        "realized_pnl_usd": None, "chain_completeness_verified": False,
        "private_key": "DO_NOT_EXPORT",
    }
    path = spool.frank_history(report)
    manifest = json.loads(path.read_text())
    assert manifest["record_count"] == 700
    assert len(manifest["parts"]) >= 2
    assert manifest["chain_completeness_verified"] is False
    pub = FakeGit(spool)
    outcome = pub.sync()
    assert outcome["status"] == "SYNC_OK"
    assert outcome["uploaded"] == 1
    prefix = f"{PREFIX}/frank-history/{manifest['snapshot_id']}/"
    parts = []
    for item in manifest["parts"]:
        remote = prefix + item["file"]
        packet = json.loads(pub.remote[remote])
        parts.append(base64.b64decode(packet["payload_b64"]))
    reconstructed = json.loads(b"".join(parts))
    assert reconstructed["record_count"] == 700
    assert len(reconstructed["records"]) == 700
    assert "DO_NOT_EXPORT" not in json.dumps(reconstructed)
    assert json.loads(pub.remote[f"{PREFIX}/frank-history/{path.name}"])["snapshot_id"] == manifest["snapshot_id"]
    assert list((spool.pending / "frank-history").glob("*.json")) == []


def test_frank_history_failed_part_keeps_entire_snapshot_queued(tmp_path):
    spool = EvidenceSpool(tmp_path)
    report = {
        "person_id": "frank",
        "source_scope": "COMPLETE_LOCAL_RECOGNIZED_TRADES_NOT_FULL_CHAIN",
        "record_count": 2,
        "records": [{"signature": "a"}, {"signature": "b"}],
    }
    manifest_file = spool.frank_history(report)
    manifest = json.loads(manifest_file.read_text())
    src = spool.pending / "frank-history-parts" / manifest["snapshot_id"] / "part-0000.json"
    src.unlink()
    result = FakeGit(spool).sync()
    assert result["status"] == "SYNC_PARTIAL"
    assert result["pending_history"] == 1
    assert manifest_file.exists()


def test_frank_git_material_snapshot_retains_all_224_source_scoped_tokens(tmp_path):
    spool = EvidenceSpool(tmp_path)
    rows = []
    for i in range(224):
        source_kind = ("LOCAL_TRADE_OR_MODEL_WITH_SIGNATURE_DELTA" if i < 33
                       else "SIGNATURE_TOKEN_DELTA_ONLY")
        category = ("MODEL_OPEN" if i < 33 else
                    "PASSIVE_RECEIPT_ONLY" if i < 137 else
                    "OTHER_ACCOUNT_ACTIVITY")
        rows.append({
            "mint": "H" + str(i).zfill(42), "watch_state": category,
            "origin_scope": source_kind, "local_model_state": "UNKNOWN",
            "local_recognized_buys": 1 if i < 33 else 0,
            "local_recognized_sells": 0,
            "passive_receipt_events": 1 if 33 <= i < 137 else 0,
            "signature_received_events": 1 if 33 <= i < 137 else 0,
            "signature_observed_in_raw": "1000000" if 33 <= i < 137 else "0",
            "signature_token_amount_decimals": 6,
            "transfer_counterparty_verified": False,
            "pnl_usd": None, "api_key": "MUST_NOT_EXPORT",
        })
    watch = {
        "summary": {
            "total_observed": 224,
            "original_trade_or_model_observed": 33,
            "passive_receipt_only": 104,
            "other_account_activity_only": 87,
        },
        "signature_activity_provenance": {
            "signature_rows_scanned": 1720,
            "wallet_owned_delta_mints": 224,
            "signature_rows_without_parsed_counterparty_flow": 1720,
            "counterparty_flow_is_complete": False,
        }, "rows": rows,
    }
    spool.frank_scan(poll_count=21754, health={
        "poll_count": 21754, "last_poll_at": "2026-10-11T07:24:45+00:00",
        "new_signatures": 1}, observed_watchlist=watch)
    pub = FakeGit(spool)
    result = pub.sync(force=True)
    assert result["status"] == "SYNC_OK"
    remote_events = [
        json.loads(value)["events"]
        for key, value in pub.remote.items()
        if "/frank/" in key and key.endswith(".json")
    ]
    assert len(remote_events) == 1
    archived = remote_events[0][0]["observed_watchlist"]
    assert archived["total_observed"] == 224
    assert archived["exported_count"] == 224
    assert archived["truncated"] is False
    assert archived["passive_receipt_only"] == 104
    assert archived["other_account_activity_only"] == 87
    assert archived["signature_activity_provenance"]["counterparty_flow_is_complete"] is False
    assert len(archived["rows"]) == 224
    assert archived["rows"][33]["passive_receipt_events"] == 1
    assert archived["rows"][33]["transfer_counterparty_verified"] is False
    assert "MUST_NOT_EXPORT" not in str(archived)


def test_immutable_git_content_id_collision_rejected_without_put(tmp_path):
    pub = FakeGit(EvidenceSpool(tmp_path))
    path = f"{PREFIX}/frank-history/" + "a" * 64 + ".json"
    pub.remote[path] = b'{"different":true}'
    with pytest.raises(ValueError, match="IMMUTABLE_GIT_EVIDENCE_COLLISION"):
        pub._upload(path, b'{"different":false}')
    assert pub.remote[path] == b'{"different":true}'
    assert not any(method == "PUT" for method, _ in pub.calls)
    # Repeated identical uploads remain idempotent, without a PUT.
    pub.calls.clear()
    pub._upload(path, b'{"different":true}')
    assert not any(method == "PUT" for method, _ in pub.calls)


def test_existing_frank_time_bucket_may_append_without_mutating_immutable_sources(tmp_path):
    pub = FakeGit(EvidenceSpool(tmp_path))
    path = f"{PREFIX}/frank/2026-10-11/1015.json"
    pub.remote[path] = b'{"events":[1]}'
    pub._upload(path, b'{"events":[1,2]}')
    assert pub.remote[path] == b'{"events":[1,2]}'
    assert any(method == "PUT" for method, _ in pub.calls)


def test_sanitizer_cannot_silently_truncate_arrays_or_export_mac_home_path():
    assert safe({"path": "/Users/alice/private/state.db"})["path"] == "[LOCAL_PATH_REDACTED]"
    assert safe("source=/home/alice/.config/token.json") == "[LOCAL_PATH_REDACTED]"
    assert safe("file /Users/alice/private/state.db") == "[LOCAL_PATH_REDACTED]"
    with pytest.raises(ValueError, match="SAFE_ARRAY_EXCEEDS_LIMIT"):
        safe(list(range(200001)))

def test_sanitizer_blocks_wrapped_file_paths_and_secrets_in_urls():
    from mission_agent.mission_control.evidence_sync import safe
    private_values = [
        'file:///Users/alice/.config/token.json',
        'note=(file:///home/alice/key)',
        'prefix ("/Users/alice/Library/secret.json") suffix',
        "~/Library/Application Support/FrankMeme/token.json",
        "report user.person+key@example.org today",
        '"https://source.invalid/assets/access_token/sensitive-piece"',
        "https://rpc.example/v1/secret-token-ABCDEF01234567890",
        "The path is (https://api.example.com/user/secret?token=abc)",
    ]
    for item in private_values:
        result = safe(item)
        assert result in (
            "[LOCAL_PATH_REDACTED]", "[EMAIL_REDACTED]",
            "[REDACTED]", "[URL_REDACTED]"
        ), item
        assert "alice" not in result and "example.org" not in result
    assert safe("https://safe.example/path?wallet=abc") == "https://safe.example/path"
    assert safe("https://safe.example.com/u/person%40gmail.com") == "[URL_REDACTED]"
    assert safe("https://safe.example.com/keys/%61ccess_token%2Fabcd") == "[URL_REDACTED]"
    assert safe("https://safe.example/") == "https://safe.example/"
    assert safe({"refresh_token": "private-value", "safe": "ok"}) == {"safe": "ok"}


def test_sanitizer_no_secret_retained_in_framed_url_path():
    from mission_agent.mission_control.evidence_sync import safe
    uri = '(https://server.example.com/messaging/bearer/SUPERSECRETTOKENKEY)'
    assert safe(uri) == "[URL_REDACTED]"
    assert safe("http://server.example.com/path/mykey@provider.example") == "[EMAIL_REDACTED]"


def test_r5_public_links_and_plain_text_survive_sanitizer():
    from mission_agent.mission_control.evidence_sync import safe as _s
    gh = ("https://github.com/lxxlx2/ChatGPT_mission_record/blob/research/"
          "frank-wallet-v2-d0-readonly-20261011/crypto-300-profit-mission/meme/evidence/x.json")
    assert _s(gh) == gh
    tx = "https://solscan.io/tx/5wqKv5YuurRKUaJAK5fZtFrNg6GocVZuTTiAPWYrYDaswyUArwAZurpbZFU6WBjHp5z5Bt5bPCkLNKVQHfS6yigx"
    assert _s(tx) == tx
    assert _s("profile: ok") == "profile: ok"
    assert _s("reconfile: 3") == "reconfile: 3"
    assert _s("file transfer note") == "file transfer note"
    assert _s("deposit ~ approx 3") == "deposit ~ approx 3"


def test_r5_secret_path_and_local_path_redaction_remains_active():
    from mission_agent.mission_control.evidence_sync import safe as _s
    assert _s("file:///Users/alice/Library/FrankMeme/state.db") == "[LOCAL_PATH_REDACTED]"
    assert _s("~/Library/Application Support/FrankMeme/policy.json") == "[LOCAL_PATH_REDACTED]"
    assert _s("https://solana-mainnet.g.alchemy.com/v2/FAKE_TEST_KEY_1234567890abcdef") == "[URL_REDACTED]"
    assert _s("https://api.example.com/v1/token/abc") == "[URL_REDACTED]"
    assert _s("https://github.com/x/y/private/notes") == "[URL_REDACTED]"
