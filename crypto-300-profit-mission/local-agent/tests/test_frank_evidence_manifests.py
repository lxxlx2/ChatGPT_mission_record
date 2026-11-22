"""Immutable captures: all local rows, old corrections, raw duplicate legs."""
import hashlib
import io
import json
import socket
import sqlite3
from email.message import Message
from types import SimpleNamespace

import pytest

from mission_agent.mission_control.evidence_manifests import EvidenceManifests, ManifestError
from mission_agent.mission_control.server import Handler
from test_frank_activity_paging import make_db, add_row, NOW, MINT_A


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket, "socket", lambda *a,**k: (_ for _ in ()).throw(AssertionError("MANIFEST_NETWORK_FORBIDDEN")))


@pytest.fixture
def store(tmp_path):
    source = tmp_path / "source.sqlite"
    make_db(source, 137)
    return EvidenceManifests(tmp_path / "private", source, clock=lambda: NOW, code_sha="a"*40)


def all_pages(store, identity, **kwargs):
    cursor, rows, totals = None, [], set()
    while True:
        page = store.activity(identity, cursor=cursor, **kwargs)
        rows.extend(page["rows"]); totals.add(page["total_signatures"])
        assert page["immutable_source_snapshot"] and not page["full_chain_verified"]
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert totals == {len(rows)}
    return rows


def test_get_does_not_create_missing_store(store):
    assert store.manifests()["rows"] == [] and not store.root.exists()
    with pytest.raises(ManifestError, match="MANIFEST_NOT_FOUND"):
        store.activity("a"*32)
    assert not store.root.exists()


def test_source_corrections_and_backfill_cannot_change_saved_rows(store):
    before = hashlib.sha256(store.source.read_bytes()).hexdigest()
    first = store.create("activity", "first")
    old = all_pages(store, first["manifest_id"], limit=19)
    assert len(old) == 137 == len({r["index_rowid"] for r in old})
    assert first["counts"]["frank_activity_rows"] == 137
    assert hashlib.sha256(store.source.read_bytes()).hexdigest() == before
    with sqlite3.connect(store.source) as db:
        db.execute("UPDATE signatures SET body='{}' WHERE rowid=1")
        add_row(db, 999)
    reopened = EvidenceManifests(store.root, store.source, clock=lambda: NOW+1, code_sha="b"*40)
    assert reopened.create("activity", "first") == first
    assert all_pages(reopened, first["manifest_id"], limit=11) == old
    second = reopened.create("activity", "corrected")
    new = all_pages(reopened, second["manifest_id"], limit=17)
    assert len(new) == 138 and new != old
    assert second["code_sha"] == "b"*40 and first["code_sha"] == "a"*40


def test_fact_revision_preserves_unchanged_ids_and_links_corrections(store):
    first = store.create("facts", "fact-first")
    before = {r["index_rowid"]: r["transaction_fact"] for r in all_pages(store, first["manifest_id"])}
    with sqlite3.connect(store.source) as db:
        db.execute("UPDATE signatures SET body='{}' WHERE rowid=1")
        # A row absent from the new source remains recoverable in the parent.
        db.execute("DELETE FROM signatures WHERE rowid=2")
        add_row(db, 999)
    child = store.create("facts", "fact-child", first["manifest_id"])
    assert child["fact_revision_counts"] == {"new":1, "revised":1, "unchanged":135, "parent_only":1}
    after = {r["index_rowid"]: r["transaction_fact"] for r in all_pages(store, child["manifest_id"])}
    assert after[1]["supersedes_id"] == before[1]["fact_id"]
    assert after[1]["fact_id"] != before[1]["fact_id"]
    assert after[3] == before[3]
    assert before[2] and 2 not in after
    repeated = store.create("facts", "repeated", child["manifest_id"])
    again = {r["index_rowid"]: r["transaction_fact"] for r in all_pages(store, repeated["manifest_id"])}
    assert again == after
    assert repeated["fact_revision_counts"]["revised"] == 0
    assert {r["index_rowid"]:r["transaction_fact"] for r in all_pages(store, first["manifest_id"])} == before
    assert store.create("facts", "fact-child", first["manifest_id"]) == child
    with pytest.raises(ManifestError, match="IDEMPOTENCY_CONFLICT"):
        store.create("facts", "fact-child", child["manifest_id"])


def test_fact_parent_contract_rejects_wrong_kind_or_missing_manifest(store):
    legacy = store.create("activity", "activity")
    with pytest.raises(ManifestError, match="PARENT_FACTS_NOT_AVAILABLE"):
        store.create("facts", "child", legacy["manifest_id"])
    with pytest.raises(ManifestError, match="PARENT_MANIFEST_NOT_FOUND"):
        store.create("facts", "child", "a"*32)
    with pytest.raises(ManifestError, match="FACTS_REQUIRED_FOR_SUPERSESSION"):
        store.create("activity", "child", legacy["manifest_id"])
    assert store.manifests()["total_matching"] == 1


def test_raw_duplicate_trade_legs_and_source_tables_are_preserved(store):
    with sqlite3.connect(store.source) as db:
        db.execute("INSERT INTO trades SELECT * FROM trades LIMIT 1")
        raw_legs = db.execute("SELECT count(*) FROM trades").fetchone()[0]
    metadata = store.create("facts", "facts")
    rows = all_pages(store, metadata["manifest_id"], limit=37)
    assert metadata["counts"]["all_source_trade_legs"] == raw_legs
    assert sum(len(r["raw_trade_legs"]) for r in rows) == raw_legs
    artifact = store.artifacts / (metadata["manifest_id"]+".sqlite")
    with sqlite3.connect(artifact) as db:
        assert db.execute("SELECT count(*) FROM trades").fetchone()[0] == raw_legs
    assert artifact.stat().st_mode & 0o777 == 0o600


def test_facts_reference_raw_rows_without_exposing_arbitrary_source_columns(store):
    with sqlite3.connect(store.source) as db:
        db.execute("ALTER TABLE trades ADD COLUMN extra TEXT")
        db.execute("UPDATE trades SET extra='PRIVATE_UNEXPECTED_KEY'")
    saved = store.create("facts", "facts-private")
    page = store.activity(saved["manifest_id"], limit=1000)
    assert "PRIVATE_UNEXPECTED_KEY" not in json.dumps(page)
    assert [leg for row in page["rows"] for leg in row["raw_trade_legs"]]
    artifact = store.artifacts / (saved["manifest_id"] + ".sqlite")
    with sqlite3.connect(artifact) as db:
        assert db.execute("SELECT extra FROM trades LIMIT 1").fetchone()[0] == "PRIVATE_UNEXPECTED_KEY"


def test_committed_wal_content_is_in_capture_without_checkpointing_source(store):
    db = sqlite3.connect(store.source)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA wal_autocheckpoint=0")
    add_row(db, 999); db.commit()
    before = hashlib.sha256(store.source.read_bytes()).hexdigest()
    metadata = store.create("activity", "wal")
    assert metadata["counts"]["frank_activity_rows"] == 138
    assert len(all_pages(store, metadata["manifest_id"])) == 138
    assert hashlib.sha256(store.source.read_bytes()).hexdigest() == before
    db.close()


def test_corrupt_artifact_is_rejected_instead_of_refalling_to_live_source(store):
    metadata = store.create("activity", "first")
    path = store.artifacts/(metadata["manifest_id"]+".sqlite")
    with path.open("ab") as out:
        out.write(b"changed")
    with pytest.raises(ManifestError, match="MANIFEST_ARTIFACT_INTEGRITY_FAILED") as exc:
        store.activity(metadata["manifest_id"])
    assert exc.value.http_status == 503


def test_corrupt_metadata_is_not_reflected_or_claimed_valid(store):
    first=store.create("activity","first")
    with sqlite3.connect(store.path) as db:
        body=dict(first);body["code_sha"]="SECRET_PRIVATE_PATH"
        db.execute("UPDATE manifests SET body=?",(json.dumps(body),))
    with pytest.raises(ManifestError,match="^MANIFEST_METADATA_INTEGRITY_FAILED$"):
        store.manifests()
    with pytest.raises(ManifestError,match="^MANIFEST_METADATA_INTEGRITY_FAILED$"):
        store.create("activity","first")


def test_failed_capture_is_not_published_and_key_remains_retryable(store, monkeypatch):
    import mission_agent.mission_control.evidence_manifests as module
    original = module.activity
    def fail(*args,**kwargs):
        raise ValueError("/Users/private SECRET_RPC_KEY")
    monkeypatch.setattr(module, "activity", fail)
    with pytest.raises(ManifestError, match="^MANIFEST_CAPTURE_FAILED$"):
        store.create("activity", "retry")
    assert store.manifests()["rows"] == []
    assert list(store.artifacts.iterdir()) == []
    monkeypatch.setattr(module, "activity", original)
    assert store.create("activity", "retry")["state"] == "COMPLETE"


def test_reused_key_for_other_kind_or_source_is_conflict(store, tmp_path):
    store.create("activity", "one")
    with pytest.raises(ManifestError, match="IDEMPOTENCY_CONFLICT"):
        store.create("facts", "one")
    other = tmp_path / "other.sqlite"; make_db(other, 3)
    with pytest.raises(ManifestError, match="IDEMPOTENCY_CONFLICT"):
        EvidenceManifests(store.root, other, clock=lambda: NOW).create("activity", "one")


def test_activity_cursor_is_bound_to_manifest_and_filters(store):
    first = store.create("activity", "first")
    cursor = store.activity(first["manifest_id"], limit=3)["next_cursor"]
    for params in ({"kind":"ACTIVE_TRADE"}, {"days":7}):
        with pytest.raises(ManifestError, match="MANIFEST_CURSOR_QUERY_CHANGED"):
            store.activity(first["manifest_id"],cursor=cursor,**params)
    second = store.create("activity", "second")
    with pytest.raises(ManifestError, match="MANIFEST_CURSOR_QUERY_CHANGED"):
        store.activity(second["manifest_id"],cursor=cursor)
    active = all_pages(store, first["manifest_id"], kind="ACTIVE_TRADE", limit=3)
    assert len(active) == 28
    with pytest.raises(ManifestError, match="^INVALID_MANIFEST_CURSOR$") as exc:
        store.activity(first["manifest_id"],cursor="not-a-cursor")
    assert exc.value.http_status == 400


def test_manifest_list_cursor_freezes_fence_and_preserves_kind_filter(store):
    for n in range(5):
        store.create("facts" if n%2 else "activity",str(n))
    first = store.manifests(kind="activity",limit=1)
    assert first["total_matching"] == 3 and first["next_cursor"]
    store.create("activity", "later")
    cursor, ids = first["next_cursor"], [first["rows"][0]["manifest_id"]]
    while cursor:
        page = store.manifests(kind="activity",limit=1,cursor=cursor)
        assert page["total_matching"] == 3
        ids.extend(r["manifest_id"] for r in page["rows"]); cursor=page["next_cursor"]
    assert len(ids) == len(set(ids)) == 3
    with pytest.raises(ManifestError, match="MANIFEST_CURSOR_QUERY_CHANGED"):
        store.manifests(kind="facts",cursor=first["next_cursor"])


def call(store, path, method="GET", body=None, origin="http://127.0.0.1:8766", read=True):
    obj = object.__new__(Handler)
    obj.state=SimpleNamespace(evidence_manifests=store, frank=SimpleNamespace(database=store.source))
    obj.path=path;obj.headers=Message();obj.headers["Host"]="127.0.0.1:8766"
    if origin is not None:obj.headers["Origin"]=origin
    if read:obj.headers["X-Frank-Research-Read"]="1"
    obj.headers["Content-Type"]="application/json"
    raw=body if isinstance(body,bytes) else json.dumps(body).encode()
    obj.headers["Content-Length"]=str(len(raw));obj.rfile=io.BytesIO(raw);obj.wfile=io.BytesIO()
    codes=[];obj.send_response=lambda code,*a:codes.append(code);obj.send_header=lambda *a:None
    obj.end_headers=lambda:None;obj.send_error=lambda code,*a:codes.append(code)
    getattr(obj,"do_"+method)()
    return codes[0],json.loads(obj.wfile.getvalue()) if obj.wfile.getvalue() else None


def test_http_create_is_complete_201_and_exact_id_get_and_page(store):
    code, metadata=call(store,"/api/frank-evidence-manifests","POST",{"kind":"activity","idempotency_key":"http"})
    assert code == 201 and metadata["state"] == "COMPLETE"
    identity=metadata["manifest_id"]
    assert call(store,"/api/frank-evidence-manifests?manifest_id="+identity)[1]["rows"] == [metadata]
    code,page=call(store,"/api/frank-evidence-activity?manifest_id="+identity+"&limit=11")
    assert code==200 and len(page["rows"])==11 and page["total_signatures"]==137


def test_same_origin_coverage_reads_index_without_opening_derived_store(store, monkeypatch):
    monkeypatch.setattr("mission_agent.mission_control.server.time.time", lambda: NOW)
    path = "/api/frank-coverage?days=7"
    assert call(store, path, read=False)[0] == 403
    assert call(store, path, origin="http://localhost:8766")[0] == 403
    for invalid in ("days=7&days=all", "mint=x", "days=", "days=3"):
        assert call(store, "/api/frank-coverage?" + invalid)[0] == 400
    status, payload = call(store, path)
    assert status == 200 and payload["data"]["days"] == 7
    assert payload["data"]["indexed_signatures"] == 137
    assert payload["coverage"]["full_chain_verified"] is False
    assert not store.root.exists()


@pytest.mark.parametrize("origin",[None,"http://localhost:8766","http://127.0.0.1:8767"])
def test_http_create_requires_exact_origin_before_storage(store,origin):
    assert call(store,"/api/frank-evidence-manifests","POST",{},origin=origin)[0]==403
    assert not store.root.exists()


@pytest.mark.parametrize("body",[
    {"kind":"positions","idempotency_key":"x"}, {"kind":[],"idempotency_key":"x"},
    {"kind":"activity","idempotency_key":"x","wallet":"other"},
    b'{"kind":"activity","kind":"facts","idempotency_key":"x"}',
    {"kind":"activity","idempotency_key":""}, b'{"kind":NaN}',
])
def test_http_invalid_create_does_not_publish_or_leak(store,body):
    code,payload=call(store,"/api/frank-evidence-manifests","POST",body)
    assert code==400 and payload["error"].isupper() and not store.root.exists()


@pytest.mark.parametrize("path",[
    "/api/frank-evidence-manifests?wallet=x", "/api/frank-evidence-manifests?limit=0",
    "/api/frank-evidence-activity", "/api/frank-evidence-activity?manifest_id=../secret",
    "/api/frank-evidence-manifests?kind=x&kind=y",
])
def test_http_invalid_reads_and_custom_header(store,path):
    assert call(store,path)[0]==400
    assert call(store,path,read=False)[0]==403
    assert not store.root.exists()
