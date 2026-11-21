"""Read the two Frank delivery histories; archive notes in a separate SQLite file."""
from __future__ import annotations

import base64
from contextlib import ExitStack, closing
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import unicodedata

from ..hashing import digest
from .db import open_control_ro, utc

CHANNELS = {"gmail", "local"}
IDENTITY = re.compile(r"[a-f0-9]{64}")
SIGNATURE = re.compile(r"[1-9A-HJ-NP-Za-km-z]{64,88}")
STATES = {
    "COMMAND_ACCEPTED", "CREDENTIAL_BLOCKED", "DRY_RUN_AUDIT", "IN_FLIGHT",
    "MANUAL_REVIEW", "PENDING", "PERMANENT_ERROR", "RETRYABLE_ERROR",
    "RETRY_PENDING", "SENDING", "SENT_UNVERIFIED", "SENT_VERIFIED",
}
DELIVERY_ERRORS = {
    "GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND",
    "GMAIL_DELIVERY_OR_READBACK_RETRY_PENDING", "GMAIL_LIVE_APPROVAL_EXPIRED_BEFORE_SEND",
    "GMAIL_OLD_POLICY_PENDING_BLOCKED", "GMAIL_RETRY_LIMIT_REACHED",
    "GMAIL_SENT_OUTCOME_UNRESOLVED_TOO_LONG", "INVALID_FROZEN_EMAIL_CONTENT",
    "INVALID_SENT_RECEIPT", "LEGACY_SIGNAL_NOT_V1_GMAIL_AUTHORITY",
    "LOCAL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND",
    "LOCAL_GMAIL_CREDENTIAL_UNAVAILABLE", "LOCAL_LIVE_APPROVAL_EXPIRED_BEFORE_DISPATCH",
    "LOCAL_OLD_POLICY_PENDING_BLOCKED", "MISSING_FROZEN_EMAIL_CONTENT",
    "MULTIPLE_SENT_IDENTITIES_REQUIRE_REVIEW", "NO_LOCAL_GMAIL_CREDENTIAL", "NOT_A_SENT_RECEIPT",
    "SEND_OUTCOME_UNCERTAIN_WAITING_SENT", "SENT_IDENTITY_OR_CONTENT_MISMATCH",
}
# Both schemas use this query shape, but with separate stable IDs and ledgers.
SOURCE_QUERIES = {
    "SCANNER_V1": """
        SELECT s.signal_id AS id, o.channel, o.status, o.attempts, o.receipt, o.last_error,
               NULL AS enqueued_at, NULL AS snapshot_id, s.content_hash, s.mint,
               s.signal_id, s.signal_type, s.body, NULL AS decision,
               NULL AS decision_at, NULL AS policy_hash, NULL AS policy_id
        FROM signals s JOIN outbox o USING(signal_id)
        WHERE s.person_id='frank'
    """,
    "MISSION_CONTROL": """
        SELECT e.decision_id AS id, o.channel, o.status, o.attempts, o.receipt, o.last_error,
               o.created_at AS enqueued_at, e.snapshot_id, o.content_hash, e.mint,
               s.source_signal_id AS signal_id, s.source_signal_type AS signal_type,
               e.body, e.decision, e.created_at AS decision_at, s.policy_hash, s.policy_id
        FROM decision_events e JOIN decision_outbox o USING(decision_id)
        JOIN decision_snapshots s USING(snapshot_id)
        WHERE e.person_id='frank'
    """,
}


class NotificationAuditError(ValueError):
    def __init__(self, code, status=400):
        super().__init__(code)
        self.code, self.http_status = code, status


def _matches(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _object(value):
    try:
        result = json.loads(value)
    except (ValueError, TypeError, RecursionError):
        return {}
    return result if isinstance(result, dict) else {}


def _instant(value):
    if type(value) in (int, float) or isinstance(value, str) and value.isascii() and value.isdecimal():
        try:
            return datetime.fromtimestamp(float(value), timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        try:
            stamp = datetime.fromisoformat(value)
            if stamp.tzinfo is not None:
                return stamp.astimezone(timezone.utc)
        except (OverflowError, ValueError):
            pass
    return None


def _status(value):
    return value if value in STATES else "UNKNOWN"


def _sha(value):
    return value if _matches(IDENTITY, value) else None


def _token(value):
    return value if isinstance(value, str) and re.fullmatch("[A-Za-z0-9_.:-]{1,128}", value) else None


def _count(value):
    return value if type(value) is int and value >= 0 else None


def _segment(times, start, end):
    first, second = times.get(start), times.get(end)
    if first is None or second is None:
        return {"status": "UNRECORDED", "seconds": None}
    seconds = (second - first).total_seconds()
    if seconds < 0:
        return {"status": "CLOCK_ORDER_UNVERIFIED", "seconds": None}
    return {"status": "OBSERVED", "seconds": round(seconds, 3)}


def _has_table(db, table):
    return db is not None and db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _fields(db, table, identity_column, identity):
    if not _has_table(db, table):
        return {}
    row = db.execute(f"SELECT * FROM {table} WHERE {identity_column}=?", (identity,)).fetchone()
    return dict(row) if row is not None else {}


def _source_evidence(db, signal_id, fallback_signature=None):
    signal = _fields(db, "signals", "signal_id", signal_id) if signal_id else {}
    if signal.get("person_id") != "frank":
        signal = {}
    body = _object(signal.get("body"))
    # V1's stored timestamp is a chain/model trigger instant; the actual time
    # at which the process emitted the signal is absent in the current schema.
    trigger_at = _instant(body.get("triggered_at"))
    signal_signature = body.get("triggering_signature") or body.get("latest_trade_signature")
    signature = signal_signature or fallback_signature
    if not _matches(SIGNATURE, signature):
        signature = None
    source = {"signal_id": signal.get("signal_id"), "signature": signature,
              "signature_basis": ("SIGNAL_TRIGGER" if signal_signature else "DECISION_INPUT") if signature else None,
              "trigger_at": trigger_at.isoformat() if trigger_at else None}
    if signature is None or not _has_table(db, "signatures"):
        return source, {}
    rows = db.execute(
        "SELECT wallet,slot,block_time,seen_at,classified_at,raw_hash FROM signatures "
        "WHERE person_id='frank' AND signature=? LIMIT 2", (signature,)
    ).fetchall()
    if len(rows) != 1:
        return source, {}
    row = rows[0]
    source.update(slot=_count(row["slot"]), raw_hash=_sha(row["raw_hash"]))
    times = {"event_at": _instant(row["block_time"]), "indexed_at": _instant(row["seen_at"]),
             "classified_at": _instant(row["classified_at"])}
    # A second reader with a different wallet must not fill the detection gap.
    if _has_table(db, "signature_detections"):
        detected = db.execute(
            "SELECT seen_at,slot,block_time FROM signature_detections WHERE wallet=? AND signature=?",
            (row["wallet"], signature),
        ).fetchone()
        if detected and detected["slot"] == row["slot"] and detected["block_time"] == row["block_time"]:
            times["detected_at"] = _instant(detected["seen_at"])
    return source, times


def _delivery_evidence(db, namespace, row):
    channel, identity = row["channel"], row["id"]
    v1 = namespace == "SCANNER_V1"
    identity_column = "signal_id" if v1 else "decision_id"
    if channel == "gmail":
        data = _fields(db, "gmail_delivery", identity_column, identity)
    elif not v1:
        data = _fields(db, "local_delivery", identity_column, identity)
    else:
        data = {}
    status = _status(data.get("status", row["status"]))
    receipt = _object(data.get("receipt") or row["receipt"])
    bound = receipt.get(identity_column) == identity
    has_receipt = bool(receipt) and bound
    accepted = _instant(receipt.get("accepted_at")) if bound and status == "COMMAND_ACCEPTED" else None
    recorded = _instant(data.get("sent_at"))
    verified = (channel == "gmail" and has_receipt and status == "SENT_VERIFIED"
                and data.get("readback_verified") == 1
                and isinstance(data.get("gmail_message_id"), str) and bool(data["gmail_message_id"])
                and receipt.get("gmail_message_id") == data["gmail_message_id"])
    if v1:
        verified = (verified and _sha(data.get("content_hash")) is not None
                    and data["content_hash"] == receipt.get("content_hash")
                    and receipt.get("readback_verified") is True)
    else:
        verified = verified and _sha(row["content_hash"]) is not None and data.get("content_hash") == row["content_hash"]
    if verified:
        proof = "GMAIL_SENT_READBACK"
    elif accepted is not None:
        proof = "LOCAL_COMMAND_ACKNOWLEDGMENT"
    elif status in {"SENT_VERIFIED", "SENT_UNVERIFIED", "SENDING", "IN_FLIGHT"} or recorded:
        proof = "OUTCOME_UNVERIFIED"
    else:
        proof = "NO_VERIFIED_RECEIPT"
    # Mission uses last_attempt_at for both send and readback/guard updates.
    attempt = _instant(data.get("last_attempt_at")) if v1 and _count(data.get("attempt_count")) else None
    # Legacy V1 receipts may use either provider internalDate or local
    # readback time for sent_at. Preserve the timestamp without claiming
    # a provider delivery time. Mission sent_at records local acceptance.
    times = {"attempt_at": attempt, "provider_acceptance_recorded_at": recorded if not v1 else None,
             "local_command_at": accepted,
             "legacy_sent_at": recorded if v1 else None,
             "gmail_readback_at": _instant(receipt.get("verified_at")) if verified and not v1 else None}
    error = data.get("last_error") or row["last_error"]
    if error and (not isinstance(error, str) or error not in DELIVERY_ERRORS):
        error = "UNCLASSIFIED_DELIVERY_ERROR"
    activity = _instant(data.get("last_attempt_at"))
    return {
        "status": status, "attempt_count": _count(data.get("attempt_count")),
        "delivery_mode": _token(data.get("delivery_mode")),
        "delivery_forbidden": bool(data["delivery_forbidden"]) if data.get("delivery_forbidden") in (0, 1) else None,
        "content_hash": _sha(data.get("content_hash")),
        "receipt_present": has_receipt, "receipt_proof": proof,
        "error_code": error, "gmail_sent_verified": verified,
        "last_activity_at": activity.isoformat() if activity else None,
    }, times


def _default_annotation(identity, channel):
    return {"notification_id": identity, "channel": channel, "archived": False, "reason": "",
            "revision": 0, "archived_at": None, "event_id": None}


class FrankNotificationAudit:
    def __init__(self, scanner_path, control_path, root, clock=utc):
        self.paths = {"SCANNER_V1": Path(scanner_path), "MISSION_CONTROL": Path(control_path)}
        self.annotation_path = Path(root) / "frank-notification-annotations.sqlite"
        self.clock = clock

    def _connections(self, stack):
        def opened(path):
            if not path.is_file():
                return None
            db = stack.enter_context(closing(open_control_ro(path)))
            db.execute("BEGIN")
            return db
        return {key: opened(path) for key, path in self.paths.items()}, opened(self.annotation_path)

    def _selection(self, connections, notification_id, channel, limit, after=None):
        rows, availability = [], {}
        for namespace, db in connections.items():
            try:
                query = SOURCE_QUERIES[namespace]
                filters = ["channel IN ('gmail','local')", "length(id)=64", "id NOT GLOB '*[^a-f0-9]*'"]
                parameters = []
                for field, value in (("id", notification_id), ("channel", channel)):
                    if value is not None:
                        filters.append(f"{field}=?")
                        parameters.append(value)
                if after is not None:
                    filters.append("(id,channel,?)>(?,?,?)")
                    parameters.extend([namespace, *after])
                sql = "SELECT * FROM (" + query + ") WHERE " + " AND ".join(filters)
                result = db.execute(sql+" ORDER BY id,channel LIMIT ?", (*parameters, limit)).fetchall() if db else None
                availability[namespace] = "AVAILABLE" if result is not None else "UNAVAILABLE"
                if result:
                    rows.extend((row["id"], row["channel"], namespace, row) for row in result)
            except sqlite3.OperationalError as exc:
                if "no such table:" not in str(exc) and "no such column:" not in str(exc):
                    raise
                availability[namespace] = "UNAVAILABLE"
        if "AVAILABLE" not in availability.values():
            raise NotificationAuditError("NOTIFICATION_SOURCE_UNAVAILABLE", 503)
        return sorted(rows, key=lambda row: row[:3]), availability

    @staticmethod
    def _validate(notification_id, channel):
        if notification_id is not None and not _matches(IDENTITY, notification_id):
            raise NotificationAuditError("INVALID_NOTIFICATION_ID")
        if channel is not None and (not isinstance(channel, str) or channel not in CHANNELS):
            raise NotificationAuditError("INVALID_NOTIFICATION_CHANNEL")

    @staticmethod
    def _decode_cursor(cursor, binding):
        try:
            if not isinstance(cursor, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,1024}", cursor):
                raise ValueError
            claimed, after = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
            if (not isinstance(after, list) or len(after) != 3 or not _matches(IDENTITY, after[0])
                    or after[1] not in CHANNELS or after[2] not in SOURCE_QUERIES):
                raise ValueError
        except (ValueError, TypeError, RecursionError, UnicodeError):
            raise NotificationAuditError("INVALID_NOTIFICATION_CURSOR") from None
        if claimed != binding:
            raise NotificationAuditError("NOTIFICATION_CURSOR_SOURCE_CHANGED", 409)
        return after

    def _binding(self, notification_id, channel):
        files = []
        for path in self.paths.values():
            try:
                info = path.stat()
            except FileNotFoundError:
                files.append(None)
            else:
                files.append([info.st_dev, info.st_ino])
        return digest([notification_id, channel, files])

    def page(self, *, notification_id=None, channel=None, limit=100, cursor=None):
        self._validate(notification_id, channel)
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise NotificationAuditError("INVALID_NOTIFICATION_LIMIT")
        try:
            binding = self._binding(notification_id, channel)
            after = self._decode_cursor(cursor, binding) if cursor is not None else None
            with ExitStack() as stack:
                dbs, annotations = self._connections(stack)
                rows, availability = self._selection(dbs, notification_id, channel, limit + 1, after)
                if notification_id is not None and not rows and after is None:
                    if "UNAVAILABLE" in availability.values():
                        raise NotificationAuditError("NOTIFICATION_SOURCE_UNAVAILABLE", 503)
                    raise NotificationAuditError("NOTIFICATION_NOT_FOUND", 404)
                records = [self._item(dbs, annotations, namespace, row) for _, _, namespace, row in rows[:limit]]
                if self._binding(notification_id, channel) != binding:
                    raise NotificationAuditError("NOTIFICATION_CURSOR_SOURCE_CHANGED", 409)
        except (OSError, sqlite3.Error):
            raise NotificationAuditError("NOTIFICATION_AUDIT_UNAVAILABLE", 503) from None
        next_cursor = None
        if len(rows) > limit:
            next_cursor = base64.urlsafe_b64encode(
                json.dumps([binding, rows[limit - 1][:3]], separators=(",", ":")).encode()
            ).decode().rstrip("=")
        return {"status": "PARTIAL" if "UNAVAILABLE" in availability.values() else "OK",
                "sources": availability, "rows": records, "next_cursor": next_cursor}

    @staticmethod
    def _annotation(db, identity, channel, namespace):
        row = None
        if _has_table(db, "frank_notification_annotations"):
            row = db.execute(
                "SELECT notification_id,channel,archived,reason,revision,archived_at,event_id "
                "FROM frank_notification_annotations WHERE notification_id=? AND channel=? AND source_namespace=?",
                (identity, channel, namespace),
            ).fetchone()
        if row is None:
            return _default_annotation(identity, channel)
        return {**dict(row), "archived": row["archived"] == 1}

    def _item(self, connections, annotations, namespace, row):
        body = _object(row["body"])
        inputs = body.get("inputs")
        fallback = inputs.get("latest_signature") if isinstance(inputs, dict) else None
        source, source_times = _source_evidence(connections["SCANNER_V1"], _sha(row["signal_id"]), fallback)
        delivery, delivery_times = _delivery_evidence(connections[namespace], namespace, row)
        times = source_times | delivery_times | {
            "signal_emitted_at": None, "recipient_delivery_at": None,
            "decision_at": _instant(row["decision_at"]), "enqueued_at": _instant(row["enqueued_at"]),
        }
        stages = {
            "event_to_detect": ("event_at", "detected_at"),
            "detect_to_index": ("detected_at", "indexed_at"),
            "index_to_classify": ("indexed_at", "classified_at"),
            "classify_to_signal": ("classified_at", "signal_emitted_at"),
            "signal_to_decision": ("signal_emitted_at", "decision_at"),
            "decision_to_enqueue": ("decision_at", "enqueued_at"),
            "enqueue_to_attempt": ("enqueued_at", "attempt_at"),
            "attempt_to_provider_acceptance_log": ("attempt_at", "provider_acceptance_recorded_at"),
            "recorded_acceptance_to_gmail_readback": ("provider_acceptance_recorded_at", "gmail_readback_at"),
            "attempt_to_recipient_delivery": ("attempt_at", "recipient_delivery_at"),
        }
        return {
            "notification_id": row["id"], "channel": row["channel"], "source_namespace": namespace,
            "mint": _token(row["mint"]), "source": source,
            "policy_id": _token(row["policy_id"] or body.get("policy_id")),
            "policy_hash": _sha(row["policy_hash"] or body.get("policy_hash")),
            "decision_id": row["id"] if namespace == "MISSION_CONTROL" else None,
            "decision": _token(row["decision"]), "snapshot_id": _sha(row["snapshot_id"]),
            "signal_id": _sha(row["signal_id"]), "signal_type": _token(row["signal_type"]),
            "outbox_status": _status(row["status"]), "outbox_attempt_count": _count(row["attempts"]),
            "outbox_content_hash": _sha(row["content_hash"]), "delivery": delivery,
            "archive": self._annotation(annotations, row["id"], row["channel"], namespace),
            "times": {key: value.isoformat() if value else None for key, value in times.items()},
            "latency": {key: _segment(times, *stage) for key, stage in stages.items()},
        }

    def archive(self, *, notification_id, channel, archived, expected_revision, idempotency_key, reason=""):
        self._validate(notification_id, channel)
        if notification_id is None or channel is None or type(archived) is not bool:
            raise NotificationAuditError("INVALID_NOTIFICATION_ARCHIVE")
        if type(expected_revision) is not int or expected_revision < 0:
            raise NotificationAuditError("INVALID_NOTIFICATION_REVISION")
        if (not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 256
                or not isinstance(reason, str) or len(reason) > 1000
                or any(unicodedata.category(c) in {"Cc", "Cs"} for c in idempotency_key + reason)):
            raise NotificationAuditError("INVALID_NOTIFICATION_ANNOTATION")
        request_hash = digest([notification_id, channel, archived, expected_revision, reason])
        try:
            with ExitStack() as stack:
                dbs, _ = self._connections(stack)
                rows, availability = self._selection(dbs, notification_id, channel, 2)
                if not rows:
                    if "UNAVAILABLE" in availability.values():
                        raise NotificationAuditError("NOTIFICATION_SOURCE_UNAVAILABLE", 503)
                    raise NotificationAuditError("NOTIFICATION_NOT_FOUND", 404)
                if len(rows) != 1:
                    raise NotificationAuditError("AMBIGUOUS_NOTIFICATION_ID", 409)
                return self._archive(rows[0][2], notification_id, channel, archived, expected_revision,
                                     digest(idempotency_key), reason, request_hash)
        except (OSError, sqlite3.Error):
            raise NotificationAuditError("NOTIFICATION_AUDIT_UNAVAILABLE", 503) from None

    def _archive(self, namespace, identity, channel, archived, revision, key, reason, request_hash):
        path = self.annotation_path
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        # Don't follow an annotation symlink into an existing operational DB.
        if path.is_symlink():
            raise NotificationAuditError("NOTIFICATION_AUDIT_UNAVAILABLE", 503)
        with closing(sqlite3.connect(path, timeout=5, isolation_level=None)) as db:
            path.chmod(0o600)
            db.row_factory = sqlite3.Row
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE IF NOT EXISTS frank_notification_annotations(
                notification_id TEXT NOT NULL, channel TEXT NOT NULL, source_namespace TEXT NOT NULL,
                archived INTEGER NOT NULL, reason TEXT NOT NULL, revision INTEGER NOT NULL,
                archived_at TEXT, event_id TEXT NOT NULL,
                PRIMARY KEY(notification_id,channel,source_namespace))""")
            db.execute("""CREATE TABLE IF NOT EXISTS frank_notification_annotation_events(
                idempotency_hash TEXT PRIMARY KEY, request_hash TEXT NOT NULL,
                body TEXT NOT NULL)""")
            saved = db.execute(
                "SELECT request_hash,body FROM frank_notification_annotation_events WHERE idempotency_hash=?",
                (key,),
            ).fetchone()
            if saved:
                if saved["request_hash"] != request_hash:
                    raise NotificationAuditError("IDEMPOTENCY_CONFLICT", 409)
                return _object(saved["body"])["after"]
            before = self._annotation(db, identity, channel, namespace)
            if before["revision"] != revision:
                raise NotificationAuditError("REVISION_CONFLICT", 409)
            now = self.clock()
            after = {"notification_id": identity, "channel": channel, "archived": archived,
                     "reason": reason, "revision": revision + 1, "archived_at": now if archived else None,
                     "event_id": digest([namespace, key, request_hash])}
            db.execute("""INSERT INTO frank_notification_annotations VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(notification_id,channel,source_namespace) DO UPDATE SET
                archived=excluded.archived,reason=excluded.reason,revision=excluded.revision,
                archived_at=excluded.archived_at,event_id=excluded.event_id""",
                (identity, channel, namespace, int(archived), reason, revision + 1,
                 after["archived_at"], after["event_id"]))
            db.execute("INSERT INTO frank_notification_annotation_events VALUES(?,?,?)",
                       (key, request_hash, json.dumps({"source_namespace": namespace, "at": now,
                                                       "before": before, "after": after})))
            db.execute("COMMIT")
            return after
