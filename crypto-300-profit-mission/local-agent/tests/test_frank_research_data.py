"""Private research jobs and real in-process Handler dispatch, without listeners.

These tests exercise durable retries, source identity, full-set pagination and
read/write separation. Injected captures do not claim live source acceptance.
"""
import copy
import hashlib
import io
import json
import socket
import sqlite3
import uuid
from email.message import Message
from types import SimpleNamespace

import pytest

from mission_agent.meme.holder_ranks import _b58
from mission_agent.mission_control import research_data
from mission_agent.mission_control.research_data import ResearchData
from mission_agent.mission_control.server import Handler


def key(number):
    return _b58(number.to_bytes(32, "big"))


class QueueExecutor:
    """A controlled process boundary: no background thread or race-based wait."""
    def __init__(self):
        self.pending = []

    def submit(self, function, *args):
        self.pending.append((function, args))

    def run(self):
        function, args = self.pending.pop(0)
        function(*args)


@pytest.fixture(autouse=True)
def no_sockets(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("RESEARCH_TEST_MUST_NOT_OPEN_SOCKET")
    monkeypatch.setattr(socket, "socket", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


@pytest.fixture
def make_research(tmp_path):
    def create(*, root=None, binding="source-a", clock=lambda: 100.,
               mints=None, market=None, models=None):
        obj = ResearchData(root or tmp_path / "private-research", wallet=key(900),
                           rpc_factory=lambda: object(), market_client=market,
                           observed_mints=lambda: list(mints or []),
                           model_positions=lambda: dict(models or {}),
                           binding=binding, code_sha="a" * 40, clock=clock)
        obj.executor.shutdown(wait=True)
        obj.executor = QueueExecutor()
        return obj
    return create


def snapshot(count=1, *, observed_at="100", identity=None):
    rows = [{"mint": key(n + 1), "raw_amount": str(n), "decimals": 6,
             "program_ids": ["token-program"], "accounts": [], "account_count": 1}
            for n in range(count)]
    return {"schema_version": 1, "snapshot_id": identity or str(uuid.uuid4()),
            "status": "COMPLETE_WITHIN_SCOPE", "scope": "FULL_OWNER_OPEN_ACCOUNTS_AT_FINALIZED_PROGRAM_SLOTS",
            "observed_at": observed_at, "expires_at": "400", "rows": rows,
            "programs": [{"program_id": "token-program", "slot": 42}],
            "sources": [], "native_sol": {"raw_amount": "1", "decimals": 9, "slot": 42},
            "account_count": count, "mint_count": count, "same_slot_atomic": False}


def capture(monkeypatch, data, calls=None):
    def fake_capture(wallet, rpc, *, clock, save_receipt, checkpoint):
        if calls is not None:
            calls.append(wallet)
        checkpoint({"program_id": "first", "slot": 42})
        checkpoint({"program_id": "second", "slot": 43})
        return copy.deepcopy(data)
    monkeypatch.setattr(research_data, "capture_owner", fake_capture)


def finish_balance(obj, monkeypatch, data=None, request_key="balance-one", calls=None):
    capture(monkeypatch, data or snapshot(), calls)
    job = obj.submit("balance", {"idempotency_key": request_key})
    obj.executor.run()
    assert obj.job(job["job_id"])["state"] == "DONE"
    return obj.job(job["job_id"])


def files(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file() and not path.name.endswith('-shm')
            and not (path.name.endswith('-wal') and path.stat().st_size == 0)}


def test_gets_do_not_create_a_missing_store_or_start_source_work(make_research):
    obj = make_research()
    assert not obj.root.exists()
    assert obj.latest("balance") is None
    assert obj.latest_attempt("balance") is None
    assert obj.job("a" * 32) is None
    assert obj.market_rows() == {}
    assert obj.positions()["current_balance_verified"] is False
    assert not obj.root.exists()
    assert obj.executor.pending == []


def test_completed_job_is_durable_and_same_key_never_recaptures(make_research, monkeypatch):
    obj = make_research()
    calls = []
    first = finish_balance(obj, monkeypatch, snapshot(43), calls=calls)
    assert len(calls) == 1
    reopened = make_research(root=obj.root)
    second = reopened.submit("balance", {"idempotency_key": "balance-one"})
    assert second["job_id"] == first["job_id"]
    assert second["state"] == "DONE"
    assert reopened.executor.pending == []
    assert reopened.latest("balance")["snapshot_id"] == first["result_ref"]
    assert reopened.resume(first["job_id"])["state"] == "DONE"
    assert reopened.executor.pending == []


def test_same_key_different_request_is_a_conflict_not_new_work(make_research):
    obj = make_research()
    first = obj.submit("market", {"idempotency_key": "market-one", "scope": "mint", "mint": key(1)})
    with pytest.raises(ValueError, match="^IDEMPOTENCY_CONFLICT$"):
        obj.submit("market", {"idempotency_key": "market-one", "scope": "mint", "mint": key(2)})
    assert len(obj.executor.pending) == 1
    assert obj.job(first["job_id"])["kind"] == "market"


def test_active_duplicate_request_coalesces_and_retry_key_stays_bound_after_done(make_research, monkeypatch):
    obj = make_research()
    capture(monkeypatch, snapshot())
    first = obj.submit("balance", {"idempotency_key": "first-key"})
    joined = obj.submit("balance", {"idempotency_key": "retry-key"})
    assert joined["job_id"] == first["job_id"]
    assert len(obj.executor.pending) == 1
    obj.executor.run()
    reopened = make_research(root=obj.root)
    again = reopened.submit("balance", {"idempotency_key": "retry-key"})
    assert again["job_id"] == first["job_id"]
    assert reopened.executor.pending == []


def test_process_restart_requires_explicit_resume_and_recaptures_both_programs(make_research, monkeypatch):
    obj = make_research()
    first = obj.submit("balance", {"idempotency_key": "interrupted"})
    running = obj.job(first["job_id"])
    running.update(state="RUNNING", progress={"stage": "PROGRAM_CAPTURED", "completed_items": 1})
    obj._save(running)
    reopened = make_research(root=obj.root)
    before = files(obj.root)
    recovered = reopened.job(first["job_id"])
    assert recovered["state"] == "PAUSED" and recovered["reason"] == "PROCESS_INTERRUPTED"
    assert recovered["resume_allowed"] is True
    assert files(obj.root) == before
    assert reopened.executor.pending == []
    calls = []
    capture(monkeypatch, snapshot(2), calls)
    resumed = reopened.resume(first["job_id"])
    assert resumed["job_id"] == first["job_id"]
    reopened.executor.run()
    done = reopened.job(first["job_id"])
    assert done["state"] == "DONE" and len(calls) == 1
    assert done["progress"]["completed_items"] == 2


def test_new_source_binding_cannot_resume_or_reuse_a_previous_job(make_research):
    obj = make_research()
    first = obj.submit("balance", {"idempotency_key": "source-bound"})
    changed = make_research(root=obj.root, binding="source-b")
    with pytest.raises(ValueError, match="^SOURCE_BINDING_CHANGED$"):
        changed.resume(first["job_id"])
    with pytest.raises(ValueError, match="^SOURCE_BINDING_CHANGED$"):
        changed.submit("balance", {"idempotency_key": "source-bound"})
    assert changed.executor.pending == []


def test_positions_keep_all_75_mints_and_cursor_is_snapshot_bound(make_research, monkeypatch):
    obj = make_research(models={key(2): "CLOSED", key(1): "OPEN"})
    data = snapshot(75)
    finish_balance(obj, monkeypatch, data)
    rows, cursor = [], None
    for _ in range(10):
        page = obj.positions(limit=17, cursor=cursor)
        assert page["snapshot_id"] == data["snapshot_id"]
        assert page["total_matching"] == 75
        assert page["current_balance_verified"] is True
        assert page["same_slot_atomic"] is False
        rows.extend(page["rows"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert len(rows) == 75 and len({row["mint"] for row in rows}) == 75
    assert {row["mint"] for row in rows} == {row["mint"] for row in data["rows"]}
    assert rows[0]["reconciliation"] == rows[1]["reconciliation"] == "DIFFERENT"
    assert obj.positions(mint=key(60))["rows"][0]["mint"] == key(60)


def test_cursor_continues_original_snapshot_after_new_latest_but_rejects_changed_query(make_research, monkeypatch):
    obj = make_research()
    old = snapshot(43)
    finish_balance(obj, monkeypatch, old, request_key="old")
    first = obj.positions(limit=3)
    newer = snapshot(2)
    finish_balance(obj, monkeypatch, newer, request_key="new")
    second = obj.positions(limit=3, cursor=first["next_cursor"])
    assert second["snapshot_id"] == old["snapshot_id"]
    assert second["rows"] == [dict(row, model_state="UNKNOWN", chain_state="NONZERO", reconciliation="NOT_ASSESSED")
                              for row in old["rows"][3:6]]
    with pytest.raises(ValueError, match="^CURSOR_QUERY_CHANGED$"):
        obj.positions(mint=key(1), cursor=first["next_cursor"])
    with pytest.raises(ValueError, match="^CURSOR_QUERY_CHANGED$"):
        obj.positions(snapshot_id=newer["snapshot_id"], cursor=first["next_cursor"])


def test_changed_source_snapshot_is_not_claimed_current(make_research, monkeypatch):
    obj = make_research()
    finish_balance(obj, monkeypatch)
    changed = make_research(root=obj.root, binding="source-b")
    with pytest.raises(ValueError, match="^SOURCE_BINDING_CHANGED$"):
        changed.positions()


def test_failure_keeps_previous_snapshot_and_masks_sensitive_error(make_research, monkeypatch):
    obj = make_research()
    old = snapshot(2)
    finish_balance(obj, monkeypatch, old, request_key="good")
    def fail(wallet, rpc, **kwargs):
        kwargs["checkpoint"]({"program_id": "first", "slot": 99})
        raise TimeoutError("https://secret.invalid/v2/SECRET_KEY /Users/private/database.sqlite")
    monkeypatch.setattr(research_data, "capture_owner", fail)
    second = obj.submit("balance", {"idempotency_key": "failed"})
    obj.executor.run()
    failed = obj.job(second["job_id"])
    assert failed["state"] == "ERROR" and failed["resume_allowed"] is True
    assert "SECRET_KEY" not in json.dumps(failed) and "/Users/private" not in json.dumps(failed)
    assert obj.latest("balance")["snapshot_id"] == old["snapshot_id"]
    assert obj.positions()["latest_refresh_attempt"]["job_id"] == failed["job_id"]
    assert obj.positions()["rows"] == obj.positions(snapshot_id=old["snapshot_id"])["rows"]


def test_stale_snapshot_retains_dated_values_without_claiming_current(make_research, monkeypatch):
    now = [100.]
    obj = make_research(clock=lambda: now[0])
    finish_balance(obj, monkeypatch)
    now[0] = 401.
    result = obj.positions()
    assert result["status"] == "STALE_ARCHIVED" and result["current_balance_verified"] is False
    assert result["observed_at"] == "100" and result["rows"][0]["raw_amount"] == "0"
    now[0] = 99.
    assert obj.positions()["current_balance_verified"] is False


def test_reading_saved_jobs_positions_and_market_does_not_mutate_files(make_research, monkeypatch):
    obj = make_research()
    done = finish_balance(obj, monkeypatch, snapshot(41))
    before = files(obj.root)
    for _ in range(3):
        assert obj.job(done["job_id"])["state"] == "DONE"
        obj.latest("balance")
        obj.positions(limit=7)
        obj.market_rows()
        obj.latest_attempt("market")
    assert files(obj.root) == before
    assert obj.executor.pending == []


def test_source_ledger_is_read_only_and_never_replaced_by_private_storage(make_research, monkeypatch, tmp_path):
    source = tmp_path / "source-ledger.sqlite"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE source_event(id INTEGER PRIMARY KEY,body TEXT)")
        db.execute("INSERT INTO source_event VALUES(1,'SOURCE_BYTES_MUST_REMAIN')")
    before = source.read_bytes()
    obj = make_research(root=tmp_path / "separate-derived-store")
    finish_balance(obj, monkeypatch, snapshot(41))
    obj.positions()
    assert source.read_bytes() == before
    assert obj.path.resolve() != source.resolve()
    with sqlite3.connect(source) as db:
        assert db.execute("SELECT body FROM source_event").fetchone()[0] == "SOURCE_BYTES_MUST_REMAIN"


def handler(obj, path, *, method="GET", body=None, origin="http://127.0.0.1:8766", read_header=True):
    value = object.__new__(Handler)
    value.state = SimpleNamespace(research=obj)
    value.path = path
    value.headers = Message()
    value.headers["Host"] = "127.0.0.1:8766"
    if origin is not None:
        value.headers["Origin"] = origin
    if read_header:
        value.headers["X-Frank-Research-Read"] = "1"
    value.headers["Content-Type"] = "application/json"
    raw = body if isinstance(body, bytes) else json.dumps(body or {}).encode()
    value.headers["Content-Length"] = str(len(raw))
    value.rfile, value.wfile = io.BytesIO(raw), io.BytesIO()
    replies = []
    value.send_response = lambda status, *args: replies.append(status)
    value.send_header = lambda *args: None
    value.end_headers = lambda: None
    value.send_error = lambda status, *args: replies.append(status)
    getattr(value, "do_" + method)()
    assert len(replies) == 1
    payload = json.loads(value.wfile.getvalue()) if value.wfile.getvalue() else None
    return replies[0], payload


@pytest.mark.parametrize("path", ["/api/frank-balance-refresh", "/api/frank-market-refresh", "/api/frank-balance-refresh/resume"])
@pytest.mark.parametrize("origin", ["http://127.0.0.1:8767", "http://localhost:8766", None])
def test_real_handler_rejects_cross_port_cross_host_or_missing_origin_before_work(make_research, path, origin):
    obj = make_research()
    status, payload = handler(obj, path, method="POST", body={"idempotency_key": "key"}, origin=origin)
    assert status == 403 and payload["error"] in {"EXACT_SAME_ORIGIN_REQUIRED", "CROSS_ORIGIN_POST_FORBIDDEN"}
    assert not obj.root.exists() and obj.executor.pending == []


@pytest.mark.parametrize("body,code", [
    (b'{"idempotency_key":"x","idempotency_key":"y"}', "DUPLICATE_JSON_FIELD"),
    ({"idempotency_key": "x", "wallet": key(3)}, "INVALID_FIELDS"),
    ({"idempotency_key": "x", "amount_usdc": 30}, "INVALID_FIELDS"),
    ({"idempotency_key": "x", "scope": "mint"}, "INVALID_FIELDS"),
    (b'{"idempotency_key":NaN}', "NONFINITE_JSON"),
    ([], "INVALID_JSON_OBJECT"),
])
def test_real_handler_rejects_invalid_balance_fields_and_duplicate_json(make_research, body, code):
    obj = make_research()
    # Empty JSON list must remain a list, rather than the helper's default object.
    if body == []:
        body = b'[]'
    status, payload = handler(obj, "/api/frank-balance-refresh", method="POST", body=body)
    assert status == 400 and payload["error"] == code
    assert not obj.root.exists() and obj.executor.pending == []


@pytest.mark.parametrize("path", ["/api/frank-positions", "/api/frank-market-observations",
                                  "/api/frank-balance-refresh?refresh_id=" + "a" * 32,
                                  "/api/frank-market-refresh?refresh_id=" + "a" * 32])
def test_real_handler_get_requires_custom_header_and_has_no_source_side_effect(make_research, path):
    obj = make_research()
    status, payload = handler(obj, path, read_header=False)
    assert status == 403 and payload["error"] == "SAME_ORIGIN_READ_REQUIRED"
    assert not obj.root.exists()
    assert obj.executor.pending == []


def test_real_handler_submit_then_exact_job_get_and_positions_are_no_listener_flows(make_research, monkeypatch):
    obj = make_research()
    capture(monkeypatch, snapshot(41))
    status, submitted = handler(obj, "/api/frank-balance-refresh", method="POST", body={"idempotency_key": "handler"})
    assert status == 202
    obj.executor.run()
    status, job = handler(obj, "/api/frank-balance-refresh?refresh_id=" + submitted["job_id"])
    assert status == 200 and job["state"] == "DONE"
    status, page = handler(obj, "/api/frank-positions?limit=100")
    assert status == 200 and page["mint_count"] == 41 and len(page["rows"]) == 41
    assert obj.executor.pending == []


@pytest.mark.parametrize("query", ["limit=0", "limit=1001", "limit=1&limit=2", "extra=1"])
def test_real_handler_rejects_invalid_position_query_without_starting_work(make_research, query):
    obj = make_research()
    status, _ = handler(obj, "/api/frank-positions?" + query)
    assert status == 400 and not obj.root.exists()


def test_bulk_market_processes_all_65_mints_in_three_capacity_batches(make_research,monkeypatch):
    from test_frank_market_observations import snapshot as market_snapshot
    calls=[]
    class Batch:
        def token_snapshots(self,mints):
            calls.append(list(mints))
            return [market_snapshot(m,when=100) for m in mints]
    obj=make_research(mints=[key(i) for i in range(1,66)],market=Batch())
    monkeypatch.setattr(research_data.time,'sleep',lambda _:None)
    job=obj.submit('market',{'scope':'observed','idempotency_key':'all65'})
    obj.executor.run()
    done=obj.job(job['job_id'])
    assert done['state']=='DONE'
    assert [len(group) for group in calls]==[30,30,5]
    assert done['progress']['completed_items']==65 and len(obj.market_rows())==65
    assert len(obj._query('SELECT mint FROM frank_market_stage WHERE job_id=?',(job['job_id'],)))==65


def test_missing_snapshot_still_discovers_persisted_interrupted_refresh_without_writes(make_research):
    obj=make_research()
    job=obj.submit('balance',{'idempotency_key':'first-process'})
    reopened=make_research(root=obj.root)
    before=files(obj.root)
    data=reopened.positions()
    assert data['rows'] is None and data['latest_refresh_attempt']['job_id']==job['job_id']
    assert data['latest_refresh_attempt']['state']=='PAUSED'
    assert files(obj.root)==before and reopened.executor.pending==[]
