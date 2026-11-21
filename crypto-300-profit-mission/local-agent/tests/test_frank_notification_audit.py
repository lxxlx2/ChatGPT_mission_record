import hashlib
from io import BytesIO
import json
from types import SimpleNamespace

import pytest

from mission_agent.hashing import digest
from mission_agent.mission_control.db import ControlDB, utc
from mission_agent.mission_control.delivery import GmailDelivery, LocalDelivery
from mission_agent.mission_control.frank_notification_audit import (
    FrankNotificationAudit, NotificationAuditError,
)
from mission_agent.mission_control.server import Handler
from test_frank_gmail_delivery import Provider as ScannerFake, setup
from test_mission_control_delivery import Provider as ControlFake


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def fixture(tmp_path):
    ledger, _, scanner_gmail, signal_id = setup(tmp_path)
    control = ControlDB(tmp_path / "mission-control.sqlite")
    signal = ledger.db.execute("SELECT * FROM signals WHERE signal_id=?", (signal_id,)).fetchone()
    payload = {
        "person_id": "frank", "mint": signal["mint"], "episode_id": "episode-fixture",
        "source_signal_id": signal_id, "source_signal_type": "FRANK_MULTIPLE_SIGNAL",
        "decision": "BUY", "created_at": utc(), "policy_id": "FIXTURE",
        "policy_hash": digest("fixture"),
        "inputs": {"pattern": "MULTIPLE", "position_state": "OPEN",
                   "buy_count": 3, "sell_count": 0, "latest_side": "BUY",
                   "latest_signature": "4" * 86},
        "metrics": {}, "reasons": [], "missing": [], "invalidation": [],
    }
    event = control.record(payload, "FIXTURE", payload["policy_hash"])["event"]
    control_gmail = GmailDelivery(control)
    control_gmail.enqueue(event, mode="LIVE", forbidden=False)
    LocalDelivery(control, run=lambda *_a, **_k: pytest.fail("local send forbidden")).enqueue(
        event, forbidden=True,
    )
    reader = FrankNotificationAudit(tmp_path / "db", control.path, tmp_path)
    yield ledger, control, scanner_gmail, control_gmail, reader, signal_id, event["decision_id"]
    ledger.db.close()
    control.close()


def test_audit_reconciles_channels_and_keeps_opaque_delivery_details_private(fixture):
    ledger, control, scanner_gmail, control_gmail, audit, signal_id, decision_id = fixture
    first = ScannerFake()
    first.read_failures = 1
    scanner_gmail.drain(first)
    unknown = audit.page(notification_id=signal_id, channel="gmail")["rows"][0]
    assert unknown["delivery"]["status"] == "SENT_UNVERIFIED"
    assert unknown["delivery"]["receipt_proof"] == "OUTCOME_UNVERIFIED"
    assert unknown["delivery"]["attempt_count"] == 1
    scanner_gmail.drain(first)
    assert len(first.sent) == 1

    second = ControlFake()
    control_gmail.drain(second, authorization_guard=lambda: True)
    before = (_sha(audit.paths["SCANNER_V1"]), _sha(control.path))
    assert not audit.annotation_path.exists()
    scanner_rows = audit.page(notification_id=signal_id)["rows"]
    mission_rows = audit.page(notification_id=decision_id)["rows"]
    assert (_sha(audit.paths["SCANNER_V1"]), _sha(control.path)) == before
    assert {row["source_namespace"] for row in scanner_rows} == {"SCANNER_V1"}
    assert [row["channel"] for row in scanner_rows] == ["gmail", "local"]
    assert [row["channel"] for row in mission_rows] == ["gmail", "local"]
    assert scanner_rows[0]["delivery"]["receipt_proof"] == "GMAIL_SENT_READBACK"
    assert scanner_rows[0]["times"]["legacy_sent_at"] is not None
    assert scanner_rows[0]["times"]["recipient_delivery_at"] is None
    assert scanner_rows[0]["times"]["signal_emitted_at"] is None
    assert mission_rows[0]["signal_id"] == signal_id
    assert mission_rows[0]["delivery"]["receipt_proof"] == "GMAIL_SENT_READBACK"
    assert mission_rows[0]["latency"]["recorded_acceptance_to_gmail_readback"]["status"] == "OBSERVED"
    assert mission_rows[1]["delivery"]["status"] == "DRY_RUN_AUDIT"
    serialized = json.dumps(scanner_rows + mission_rows)
    assert "owner@example.invalid" not in serialized
    assert "gmail-1" not in serialized
    assert not audit.annotation_path.exists()


def test_source_stages_keep_real_clock_and_unknown_boundaries(fixture):
    ledger, _, _, _, audit, signal_id, _ = fixture
    sig = "3" * 86
    body = json.loads(ledger.db.execute("SELECT body FROM signals WHERE signal_id=?", (signal_id,)).fetchone()[0])
    body["triggering_signature"] = sig
    ledger.db.execute("UPDATE signals SET body=? WHERE signal_id=?", (json.dumps(body), signal_id))
    ledger.db.execute("INSERT INTO signatures VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        ("fixture-wallet", sig, "frank", 124, 1700000000, "2023-11-14T22:13:23+00:00",
         "2023-11-14T22:13:22+00:00", "1" * 64, "/private/DO_NOT_DISCLOSE", "{}", "YES", "fixture"))
    ledger.db.execute("CREATE TABLE signature_detections(wallet,signature,slot,block_time,seen_at)")
    ledger.db.execute("INSERT INTO signature_detections VALUES(?,?,?,?,?)",
                       ("fixture-wallet", sig, 124, 1700000000, 1700000001))
    row = audit.page(notification_id=signal_id, channel="gmail")["rows"][0]
    assert row["source"]["signature"] == sig
    assert row["source"]["signature_basis"] == "SIGNAL_TRIGGER"
    assert row["source"]["slot"] == 124
    assert row["latency"]["event_to_detect"] == {"seconds": 1.0, "status": "OBSERVED"}
    assert row["latency"]["detect_to_index"] == {"seconds": 2.0, "status": "OBSERVED"}
    assert row["latency"]["index_to_classify"] == {"seconds": None, "status": "CLOCK_ORDER_UNVERIFIED"}
    assert row["latency"]["classify_to_signal"] == {"seconds": None, "status": "UNRECORDED"}
    assert "DO_NOT_DISCLOSE" not in json.dumps(row)


def test_archive_is_atomic_persistent_idempotent_and_cannot_requeue(fixture):
    ledger, control, scanner_gmail, control_gmail, audit, signal_id, decision_id = fixture
    first = ScannerFake()
    scanner_gmail.drain(first)
    second = ControlFake()
    second.ambiguous = True
    control_gmail.drain(second, authorization_guard=lambda: True)
    original = [tuple(row) for row in control.db.execute("SELECT * FROM gmail_delivery")]
    source = [tuple(row) for row in ledger.db.execute("SELECT * FROM outbox")]
    request = {"notification_id": decision_id, "channel": "gmail", "archived": True,
               "reason": "Reviewed locally", "idempotency_key": "archive-1", "expected_revision": 0}
    saved = audit.archive(**request)
    reopened = FrankNotificationAudit(audit.paths["SCANNER_V1"], control.path, audit.annotation_path.parent)
    assert reopened.archive(**request) == saved
    assert saved["revision"] == 1 and saved["archived_at"] is not None
    with pytest.raises(NotificationAuditError, match="IDEMPOTENCY_CONFLICT"):
        reopened.archive(**{**request, "reason": "changed request"})
    with pytest.raises(NotificationAuditError, match="REVISION_CONFLICT"):
        reopened.archive(**{**request, "idempotency_key": "archive-2"})
    row = reopened.page(notification_id=decision_id, channel="gmail")["rows"][0]
    assert row["archive"] == saved and row["delivery"]["status"] == "SENT_UNVERIFIED"
    assert not reopened.page(notification_id=decision_id, channel="local")["rows"][0]["archive"]["archived"]
    assert not reopened.page(notification_id=signal_id, channel="gmail")["rows"][0]["archive"]["archived"]
    unarchive = reopened.archive(**{**request, "idempotency_key": "archive-2", "archived": False,
                                    "expected_revision": 1})
    assert unarchive["revision"] == 2 and unarchive["archived_at"] is None
    assert reopened.archive(**request) == saved
    assert [tuple(row) for row in control.db.execute("SELECT * FROM gmail_delivery")] == original
    assert [tuple(row) for row in ledger.db.execute("SELECT * FROM outbox")] == source


def test_cursor_is_keyset_and_bound_to_source_and_filter(fixture):
    _, _, _, _, audit, _, _ = fixture
    expected = audit.page()["rows"]
    rows, cursor = [], None
    while True:
        page = audit.page(limit=1, cursor=cursor)
        rows += page["rows"]
        cursor = page["next_cursor"]
        if not cursor:
            break
    assert rows == expected
    assert len(rows) >= 5
    stale_cursor = audit.page(limit=1)["next_cursor"]
    with pytest.raises(NotificationAuditError, match="NOTIFICATION_CURSOR_SOURCE_CHANGED"):
        audit.page(limit=1, cursor=stale_cursor, channel="gmail")
    with pytest.raises(NotificationAuditError, match="INVALID_NOTIFICATION_CURSOR"):
        audit.page(cursor="e1")
    with pytest.raises(NotificationAuditError, match="NOTIFICATION_NOT_FOUND"):
        audit.page(notification_id="a" * 64)


class Request:
    _allowed_host = lambda self: True
    _research_origin = Handler._research_origin
    _research_post = Handler._research_post
    _notification_audit_get = Handler._notification_audit_get

    def __init__(self, store, path, headers=None, body=None):
        self.state = SimpleNamespace(notification_audit=store)
        self.path = path
        self.headers = {"Host": "127.0.0.1:8766", **(headers or {})}
        self.rfile = BytesIO(body or b"")
        if body:
            self.headers.update({"Content-Type": "application/json", "Content-Length": str(len(body))})

    def _json(self, payload, status=200):
        return status, payload


def test_http_routes_require_same_origin_validate_fields_and_use_existing_identity(fixture):
    _, _, _, _, audit, _, decision_id = fixture
    read = "/api/frank-notification-audit"
    archive = "/api/frank-notification-archive"
    header = {"X-Frank-Research-Read": "1"}
    origin = {"Origin": "http://127.0.0.1:8766"}
    assert Handler.do_GET(Request(audit, read, {}))[0] == 403
    assert Handler.do_GET(Request(audit, read, {**header, "Origin": "http://127.0.0.1:8767"}))[0] == 403
    assert Handler.do_GET(Request(audit, read+"?limit=1&limit=2", header))[0] == 400
    assert Handler.do_GET(Request(audit, read+"?notification_id="+decision_id, header))[0] == 200
    request = json.dumps({"notification_id": decision_id, "channel": "gmail", "archived": True,
                          "idempotency_key": "archive-http", "expected_revision": 0}).encode()
    assert Handler.do_POST(Request(audit, archive, {"Origin": "http://127.0.0.1:8767"}, request))[0] == 403
    assert Handler.do_POST(Request(audit, archive, origin, b'{"archived":true,"archived":false}'))[0] == 400
    assert Handler.do_POST(Request(audit, archive, origin, request))[1]["revision"] == 1
