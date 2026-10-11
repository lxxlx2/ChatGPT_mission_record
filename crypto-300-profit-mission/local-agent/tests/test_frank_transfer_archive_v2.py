"""Safe Frank passive-transfer Git artifact: no network except mocked Git.

Enforces reconstructable full sanitized records, manifest-last commits,
no silent partial loss, explicit retry and hard source identity.
"""
from __future__ import annotations
import base64
import json
import pytest
from mission_agent.mission_control.evidence_sync import (
    EvidenceSpool, GitEvidencePublisher, PREFIX
)
from mission_agent.mission_control.transfer_archive import (
    queue_transfer_history, sync_transfer_history, _validated_parts
)
from mission_agent.mission_control.wallet_transfers import SOURCE_SCOPE

MINT = "J7bhFegCHZAeRzdYDwmbSp1CJ1bDJkutSg26B4SXpump"
FRANK = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"


class FakeGit(GitEvidencePublisher):
    def __init__(self, spool):
        super().__init__(spool)
        self.remote = {}
        self.methods = []
        self.fail_on = None

    def _gh(self, method, remote, payload=None):
        assert remote.startswith(PREFIX + "/")
        self.methods.append((method, remote))
        if method == "GET":
            content = self.remote.get(remote)
            if content is None:
                return None
            return {"encoding": "base64", "content": base64.b64encode(content).decode(),
                    "sha": "dummy-cas"}
        if method == "PUT":
            if self.fail_on and self.fail_on in remote:
                raise RuntimeError("FAKE_GIT_DOWN")
            assert payload["branch"] == "evidence/frank-ca-local"
            self.remote[remote] = base64.b64decode(payload["content"])
            return {"content": {"sha": "dummy"}}
        raise AssertionError(method)


def source(n):
    rows = []
    for i in range(n):
        rows.append({
            "signature": f"sig-{i:05d}",
            "slot": 454705300 + i,
            "local_classification": "PASSIVE_TRANSFER",
            "wallet_is_signer": False,
            "wallet_is_fee_payer": False,
            "source_scope": "LOCAL_NORMALIZED_INDEX_ONLY",
            "transfer_flows": [{"mint": MINT, "direction": "IN",
                                "raw_amount": str(2846838050235+i), "decimals": 6,
                                "source": "another-public-token-account",
                                "destination": "frank-public-token-account"}],
            "wallet_owned_token_deltas": [{"mint": MINT, "owner": FRANK,
                                            "delta": str(2846838050235+i)}],
            "api_key": "DO_NOT_EXPORT",
            "memo": "x"*200,
        })
    return {"schema_version": 1, "person_id": "frank",
            "source_scope": SOURCE_SCOPE, "record_count": n, "records": rows,
            "chain_history_complete": False, "pnl_verified": False}


def test_transfer_chunks_have_identity_and_roundtrip_without_truncation(tmp_path):
    spool = EvidenceSpool(tmp_path)
    file = queue_transfer_history(spool, source(700))
    manifest, parts = _validated_parts(spool, file)
    assert len(parts) > 1
    assert manifest["record_count"] == 700
    pub = FakeGit(spool)
    result = sync_transfer_history(spool, pub)
    assert result["status"] == "SYNC_OK"
    assert result["uploaded"] == 1
    assert result["pending"] == 0
    ident = manifest["snapshot_id"]
    restored = json.loads(b"".join(base64.b64decode(json.loads(pub.remote[
        f"{PREFIX}/frank-transfer-history/{ident}/{info['file']}"])["payload_b64"])
        for info in manifest["parts"]))
    assert restored["record_count"] == 700
    assert restored["records"][-1]["signature"] == "sig-00699"
    assert "DO_NOT_EXPORT" not in json.dumps(restored)
    assert "api_key" not in json.dumps(restored)
    manifest_remote = f"{PREFIX}/frank-transfer-history/{file.name}"
    assert manifest_remote in pub.remote
    assert pub.methods[-1] == ("GET", manifest_remote)
    assert not file.exists()


def test_corrupt_piece_fails_before_remote_writes_and_keeps_manifest(tmp_path):
    spool = EvidenceSpool(tmp_path)
    file = queue_transfer_history(spool, source(50))
    manifest = json.loads(file.read_text())
    part = spool.pending / "frank-transfer-history-parts" / manifest["snapshot_id"] / "part-0000.json"
    packed = json.loads(part.read_text())
    packed["payload_b64"] = base64.b64encode(b"wrong").decode()
    part.write_text(json.dumps(packed))
    pub = FakeGit(spool)
    outcome = sync_transfer_history(spool, pub)
    assert outcome["status"] == "SYNC_PARTIAL"
    assert file.exists()
    assert not any(method == "PUT" for method, _ in pub.methods)


def test_git_error_keeps_pending_and_retry_is_safe(tmp_path):
    spool = EvidenceSpool(tmp_path)
    file = queue_transfer_history(spool, source(32))
    pub = FakeGit(spool)
    pub.fail_on = "part-0000"
    first = sync_transfer_history(spool, pub)
    assert first["status"] == "SYNC_PARTIAL"
    assert first["pending"] == 1
    assert file.exists()
    pub.fail_on = None
    second = sync_transfer_history(spool, pub)
    assert second["status"] == "SYNC_OK"
    assert second["pending"] == 0
    third = sync_transfer_history(spool, pub)
    assert third["uploaded"] == 0


@pytest.mark.parametrize("tamper", ["identity", "count", "parts"])
def test_manifest_integrity_fail_closed(tmp_path, tamper):
    spool=EvidenceSpool(tmp_path)
    p=queue_transfer_history(spool,source(5))
    data=json.loads(p.read_text())
    if tamper == "identity":
        data["snapshot_id"]="0"*64
    if tamper == "count":
        data["record_count"]=7
    if tamper == "parts":
        data["parts"][0]["file"]="../wrong.json"
    p.write_text(json.dumps(data))
    result=sync_transfer_history(spool,FakeGit(spool))
    assert result["status"] == "SYNC_PARTIAL"
    assert p.exists()


def test_source_or_record_count_discrepancy_is_never_queued(tmp_path):
    spool = EvidenceSpool(tmp_path)
    report=source(2)
    report["record_count"]=1
    with pytest.raises(ValueError):
        queue_transfer_history(spool, report)
    report=source(1)
    report["person_id"]="someone_else"
    with pytest.raises(ValueError):
        queue_transfer_history(spool, report)
    assert list((spool.pending/"frank-transfer-history").glob("*.json")) == []
