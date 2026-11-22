"""Persistent user intent, independent of chain facts and notification paths."""
import hashlib
import io
import json
import socket
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from email.message import Message
from types import SimpleNamespace

import pytest

from mission_agent.meme.holder_ranks import _b58
from mission_agent.mission_control.server import DashboardState, Handler
from mission_agent.mission_control.watch_metadata import WatchMetadataStore, WatchMetadataError


def mint(n=1):
    return _b58(n.to_bytes(32, "big"))


def patch(revision=0, key="one", **values):
    return {"expected_revision": revision, "idempotency_key": key, **(values or {"pinned": True})}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("WATCH_METADATA_NETWORK_FORBIDDEN")
    monkeypatch.setattr(socket, "socket", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


def test_read_missing_store_has_no_files_and_default_is_not_chain_evidence(tmp_path):
    root = tmp_path / "missing"
    store = WatchMetadataStore(root)
    assert store.get(mint())["revision"] == 0
    assert store.get(mint())["persisted"] is False
    assert store.list(mint=mint())["returned"] == 1
    assert store.list()["rows"] == store.events(mint())["rows"] == []
    assert store.preferences() == (0, [])
    assert not root.exists()


def test_durable_multiline_note_idempotency_and_append_only_before_after(tmp_path):
    store = WatchMetadataStore(tmp_path, clock=lambda: 100.)
    note = '第一行\n<img src=x onerror=alert(1)>\r\t第二行'
    body = patch(note=note, pinned=True, watch_override="FOLLOW")
    first = store.update(mint(), body)
    reopened = WatchMetadataStore(tmp_path, clock=lambda: 999.)
    assert reopened.update(mint(), body) == first
    assert reopened.get(mint())["note"] == note
    assert reopened.get(mint())["revision"] == 1
    second = reopened.update(mint(), patch(1, "two", note="", watch_override="HIDE"))
    assert second["revision"] == 2 and second["pinned"] is True
    events = reopened.events(mint())["rows"]
    assert len(events) == 2
    assert events[0]["before"]["note"] == note and events[0]["after"]["note"] == ""
    assert events[1]["before"]["persisted"] is False
    assert events[0]["after"]["last_event_id"] == second["event_id"]
    assert (tmp_path / "frank-research.sqlite").stat().st_mode & 0o777 == 0o600


def test_stale_revision_and_reused_key_never_overwrite_or_duplicate(tmp_path):
    store = WatchMetadataStore(tmp_path)
    store.update(mint(), patch())
    for body, reason in [(patch(0, "other", note="lost"), "REVISION_CONFLICT"),
                         (patch(1, "one", note="changed"), "IDEMPOTENCY_CONFLICT")]:
        with pytest.raises(WatchMetadataError, match=reason) as exc:
            store.update(mint(), body)
        assert exc.value.http_status == 409
    assert len(store.events(mint())["rows"]) == 1
    assert store.get(mint())["note"] == ""


def test_concurrent_edit_has_exactly_one_winner_and_one_audit_event(tmp_path):
    def write(key):
        try:
            return WatchMetadataStore(tmp_path).update(mint(), patch(key=key))["revision"]
        except WatchMetadataError as exc:
            return exc.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(write, ["a", "b"]))
    assert sorted(map(str, outcomes)) == ["1", "REVISION_CONFLICT"]
    assert len(WatchMetadataStore(tmp_path).events(mint())["rows"]) == 1


def test_shared_research_tables_and_source_files_are_untouched(tmp_path):
    source = tmp_path / "forward.sqlite"
    source.write_bytes(b"source ledger is never opened")
    db = sqlite3.connect(tmp_path / "frank-research.sqlite")
    db.execute("CREATE TABLE jobs(id TEXT PRIMARY KEY, body TEXT)")
    db.execute("INSERT INTO jobs VALUES('existing','unaltered')")
    db.execute("PRAGMA user_version=23")
    db.commit(); db.close()
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    store = WatchMetadataStore(tmp_path)
    store.update(mint(), patch())
    db = sqlite3.connect(store.path)
    assert db.execute("SELECT * FROM jobs").fetchall() == [("existing", "unaltered")]
    assert db.execute("PRAGMA user_version").fetchone()[0] == 23
    db.close()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before


def test_invalid_clock_rolls_back_entire_change(tmp_path):
    good = WatchMetadataStore(tmp_path)
    good.update(mint(), patch())
    bad = WatchMetadataStore(tmp_path, clock=lambda: float("nan"))
    with pytest.raises(WatchMetadataError, match="CLOCK_INVALID"):
        bad.update(mint(), patch(1, "two", note="lost"))
    assert good.get(mint())["revision"] == 1
    assert len(good.events(mint())["rows"]) == 1
    # Failure did not consume the request key.
    assert good.update(mint(), patch(1, "two", note="kept"))["revision"] == 2


@pytest.mark.parametrize("body", [
    [], {}, patch(True), patch(-1), patch(2**63), patch(key=""), patch(key="x\n"),
    patch(pinned=1), patch(note=None), patch(note="x"*4001), patch(note="\x00"),
    patch(note="\ud800"), patch(watch_override=[]), patch(watch_override={}),
    patch(watch_override="SELL"), patch(wallet=mint()), patch(person_id="other"),
])
def test_invalid_requests_rejected_without_store_creation(tmp_path, body):
    store = WatchMetadataStore(tmp_path / "missing")
    with pytest.raises(WatchMetadataError) as exc:
        store.update(mint(), body)
    assert exc.value.http_status == 400 and not store.root.exists()


@pytest.mark.parametrize("value", ["", "x", "1"*44, "../secret", None, [], "0"*32])
def test_invalid_mint_has_fixed_public_error(tmp_path, value):
    with pytest.raises(WatchMetadataError, match="^INVALID_METADATA_MINT$"):
        WatchMetadataStore(tmp_path).get(value)


def test_all_rows_and_audit_events_paged_without_truncation_or_duplicates(tmp_path):
    store = WatchMetadataStore(tmp_path)
    expected = {mint(n) for n in range(1, 139)}
    for n, value in enumerate(expected):
        store.update(value, patch(key=str(n)))
    seen, cursor = [], None
    while True:
        page = store.list(limit=17, cursor=cursor)
        assert page["total_matching"] == 138
        seen.extend(r["mint"] for r in page["rows"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert len(seen) == len(set(seen)) == 138 and set(seen) == expected
    for n in range(1, 12):
        store.update(mint(), patch(n, "event"+str(n), note=str(n)))
    cursor, revisions = None, []
    while True:
        page = store.events(mint(), limit=3, cursor=cursor)
        revisions.extend(r["revision"] for r in page["rows"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert revisions == list(range(12, 0, -1))


def test_cursor_is_bound_to_revision_query_and_database_identity(tmp_path):
    store = WatchMetadataStore(tmp_path)
    for n in range(1, 4):
        store.update(mint(n), patch(key=str(n)))
    cursor = store.list(limit=1)["next_cursor"]
    with pytest.raises(WatchMetadataError, match="CURSOR_QUERY_CHANGED"):
        store.list(mint=mint(), cursor=cursor)
    store.update(mint(), patch(1, "next", pinned=False))
    with pytest.raises(WatchMetadataError, match="CURSOR_REVISION_CHANGED"):
        store.list(cursor=cursor)
    cursor = store.list(limit=1)["next_cursor"]
    replacement = tmp_path / "replacement"
    other = WatchMetadataStore(replacement)
    for n in range(1, 4):
        other.update(mint(n), patch(key=str(n)))
    store.path.unlink()
    other.path.replace(store.path)
    with pytest.raises(WatchMetadataError, match="SOURCE_CHANGED"):
        store.list(cursor=cursor)


def call(store, path, method="GET", body=None, origin="http://127.0.0.1:8766", read=True, host="127.0.0.1:8766", content_type="application/json"):
    obj = object.__new__(Handler)
    obj.state = SimpleNamespace(watch_metadata=store)
    obj.path = path
    obj.headers = Message()
    obj.headers["Host"] = host
    if origin is not None:
        obj.headers["Origin"] = origin
    if read:
        obj.headers["X-Frank-Research-Read"] = "1"
    obj.headers["Content-Type"] = content_type
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    obj.headers["Content-Length"] = str(len(raw))
    obj.rfile, obj.wfile = io.BytesIO(raw), io.BytesIO()
    status = []
    obj.send_response = lambda code, *args: status.append(code)
    obj.send_header = lambda *args: None
    obj.end_headers = lambda: None
    obj.send_error = lambda code, *args: status.append(code)
    getattr(obj, "do_"+method)()
    return status[0], json.loads(obj.wfile.getvalue()) if obj.wfile.getvalue() else None


def test_http_create_reload_retry_revision_and_audit(tmp_path):
    store = WatchMetadataStore(tmp_path)
    path = "/api/frank-watch-metadata/"+mint()
    body = patch(note="literal <script>\nnext", watch_override="FOLLOW")
    status, first = call(store, path, "PATCH", body)
    assert status == 200 and first["revision"] == 1
    assert call(WatchMetadataStore(tmp_path), path, "PATCH", body) == (200, first)
    assert call(store, path, "PATCH", patch(0, "stale"))[0] == 409
    status, result = call(store, "/api/frank-watch-metadata?mint="+mint())
    assert status == 200 and result["rows"][0]["note"] == body["note"]
    status, audit = call(store, "/api/frank-watch-metadata-events?mint="+mint())
    assert status == 200 and audit["total_matching"] == 1


@pytest.mark.parametrize("origin", [None, "http://localhost:8766", "http://127.0.0.1:8767", "https://evil.invalid"])
def test_http_patch_exact_origin_before_write(tmp_path, origin):
    store = WatchMetadataStore(tmp_path / "missing")
    assert call(store, "/api/frank-watch-metadata/"+mint(), "PATCH", patch(), origin=origin)[0] == 403
    assert not store.root.exists()


@pytest.mark.parametrize("path", ["/api/frank-watch-metadata", "/api/frank-watch-metadata-events?mint="+mint()])
def test_http_read_requires_custom_header(tmp_path, path):
    assert call(WatchMetadataStore(tmp_path), path, read=False)[0] == 403


@pytest.mark.parametrize("body", [b'[]', b'{"expected_revision":0,"expected_revision":1}', b'{"pinned":NaN}', b'{', b'"secret"'])
def test_http_invalid_json_is_safe_and_does_not_write(tmp_path, body):
    store = WatchMetadataStore(tmp_path / "missing")
    code, result = call(store, "/api/frank-watch-metadata/"+mint(), "PATCH", body)
    assert code == 400 and "secret" not in json.dumps(result)
    assert not store.root.exists()


@pytest.mark.parametrize("path", ["/api/frank-watch-metadata?wallet=x", "/api/frank-watch-metadata?mint=x&mint=y", "/api/frank-watch-metadata?limit=0", "/api/frank-watch-metadata-events"])
def test_http_invalid_query(tmp_path, path):
    assert call(WatchMetadataStore(tmp_path), path)[0] == 400


def test_user_view_preserves_chain_model_facts_and_exposes_no_notes(tmp_path):
    state = object.__new__(DashboardState)
    state.watch_metadata = WatchMetadataStore(tmp_path)
    state.watch_metadata.update(mint(), patch(note="private", watch_override="HIDE"))
    state.watch_metadata.update(mint(2), patch(key="two", watch_override="FOLLOW"))
    fact = {"mint":mint(), "watch_state":"MODEL_OPEN", "buy_count":7}
    state.frank_observed_watchlist = lambda: {"status":"OK", "rows":[dict(fact)], "summary":{"total_observed":1}}
    result = state.frank_personal_watchlist()
    assert {k:result["rows"][0][k] for k in fact} == fact
    assert result["rows"][1]["watch_state"] == "USER_ONLY"
    assert result["summary"]["total_observed"] == 1
    assert "private" not in json.dumps(result) and '"note"' not in json.dumps(result)


def test_read_storage_failure_does_not_leak_path(tmp_path):
    store = WatchMetadataStore(tmp_path)
    store.path.write_text("not sqlite /Users/private SECRET_KEY")
    code, result = call(store, "/api/frank-watch-metadata")
    assert code == 503 and result == {"error":"WATCH_METADATA_UNAVAILABLE"}
