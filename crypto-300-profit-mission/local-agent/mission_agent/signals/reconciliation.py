"""Read-only reconciliation against one caller-supplied finalized wallet window."""
from collections import Counter, defaultdict
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from ..hashing import digest, loads


BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
IDENTITY = re.compile(r"[a-zA-Z][a-zA-Z0-9_.-]{0,63}")
SHA256 = re.compile(r"[a-f0-9]{64}")
CLASSIFICATIONS = {"ACTIVE_TRADE", "ATA_CREATE", "PASSIVE_TRANSFER", "FAILED_TX", "FEE"}
SIGNAL_TYPES = {
    "FRANK_ACCUMULATION_SIGNAL": "PRECONFIRM",
    "FRANK_MULTIPLE_SIGNAL": "SUSPECTED_CONVICTION",
}
CHANNELS = {"local", "gmail"}
STAGES = ("detection", "indexed", "classification", "model", "signal", "outbox")
STATUS = ("MATCH", "MISSING", "UNKNOWN", "CONFLICT", "DUPLICATE", "NOT_EXPECTED")


class ReconciliationError(ValueError):
    """Stable diagnostics suitable for the summary CLI."""


def _matches(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _base58_size(value, size):
    if not isinstance(value, str) or not size <= len(value) <= (size * 139 + 99) // 100:
        return False
    number = 0
    for char in value:
        if char not in BASE58:
            return False
        number = number * 58 + BASE58.index(char)
    return len(value) - len(value.lstrip("1")) + (number.bit_length() + 7) // 8 == size


def _slot(value):
    return type(value) is int and 0 <= value <= 2**63 - 1


def _reference(data, scanner_source_id):
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ReconciliationError("REFERENCE_SCHEMA_INVALID")
    if (data.get("chain") != "solana" or data.get("commitment") != "finalized"
            or data.get("complete") is not True or not _slot(data.get("start_slot"))
            or not _slot(data.get("end_slot")) or not _slot(data.get("finalized_through_slot"))
            or not data["start_slot"] <= data["end_slot"] <= data["finalized_through_slot"]):
        raise ReconciliationError("REFERENCE_COMPLETE_FINALIZED_WINDOW_REQUIRED")
    source = data.get("source_id")
    if not _matches(IDENTITY, source) or not _matches(IDENTITY, scanner_source_id):
        raise ReconciliationError("SOURCE_ID_INVALID")
    if source.casefold() == scanner_source_id.casefold():
        raise ReconciliationError("REFERENCE_AND_SCANNER_SOURCE_NOT_DISTINCT")
    if not _matches(SHA256, data.get("capture_sha256")):
        raise ReconciliationError("REFERENCE_CAPTURE_SHA256_REQUIRED")
    if not _base58_size(data.get("wallet"), 32) or not _matches(IDENTITY, data.get("person_id")):
        raise ReconciliationError("REFERENCE_SUBJECT_INVALID")
    transactions = data.get("transactions")
    if not isinstance(transactions, list):
        raise ReconciliationError("REFERENCE_TRANSACTIONS_INVALID")
    unique = set()
    for tx in transactions:
        if (not isinstance(tx, dict) or not _base58_size(tx.get("signature"), 64)
                or not _slot(tx.get("slot")) or not data["start_slot"] <= tx["slot"] <= data["end_slot"]):
            raise ReconciliationError("REFERENCE_TRANSACTION_OUT_OF_SCOPE")
        if tx["signature"] in unique:
            raise ReconciliationError("REFERENCE_DUPLICATE_SIGNATURE")
        unique.add(tx["signature"])
        classification = tx.get("classification")
        if classification is not None and (not isinstance(classification, str) or classification not in CLASSIFICATIONS):
            raise ReconciliationError("REFERENCE_CLASSIFICATION_INVALID")
        signals = tx.get("expected_signals")
        if signals is not None and (not isinstance(signals, list)
                                    or not _matches(SHA256, data.get("policy_sha256"))):
            raise ReconciliationError("REFERENCE_SIGNAL_POLICY_SHA256_REQUIRED")
        signal_types = set()
        for signal in signals or []:
            if not isinstance(signal, dict) or not isinstance(signal.get("type"), str):
                raise ReconciliationError("REFERENCE_SIGNAL_INVALID")
            name, channels = signal["type"], signal.get("channels")
            if (name not in SIGNAL_TYPES or name in signal_types
                    or not isinstance(channels, list) or any(not isinstance(c, str) or c not in CHANNELS for c in channels)
                    or len(channels) != len(set(channels))):
                raise ReconciliationError("REFERENCE_SIGNAL_INVALID")
            signal_types.add(name)
        if (classification is not None or signals is not None) and not _matches(SHA256, tx.get("expectation_sha256")):
            raise ReconciliationError("REFERENCE_EXPECTATION_SHA256_REQUIRED")
    return data


def _sha_file(path):
    with path.open("rb") as stream:
        checksum = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def _snapshot(path, sha256):
    if path.is_symlink() or not path.is_file():
        raise ReconciliationError("SNAPSHOT_STANDALONE_FILE_REQUIRED")
    if any(Path(str(path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
        raise ReconciliationError("SNAPSHOT_SIDECAR_PRESENT_USE_SQLITE_BACKUP")
    if not _matches(SHA256, sha256) or _sha_file(path) != sha256:
        raise ReconciliationError("SNAPSHOT_SHA256_MISMATCH")


def _unique_pairs(values):
    result = {}
    for key, value in values:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _object(value, *, canonical=False):
    try:
        parsed = loads(value) if canonical else json.loads(value, object_pairs_hook=_unique_pairs)
    except (TypeError, ValueError, RecursionError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _state(status, reason):
    return {"status": status, "reason": reason}


def _ledger_row(db, table, wallet, signature):
    # All table names below are fixed by the audit, never taken from input.
    return db.execute(
        f"SELECT * FROM {table} WHERE wallet=? AND signature=? LIMIT 2", (wallet, signature)
    ).fetchall()


def _identity(rows, tx, person_id, missing):
    if not rows:
        return missing
    if len(rows) > 1:
        return _state("DUPLICATE", "MULTIPLE_LEDGER_ROWS_FOR_WALLET_SIGNATURE")
    row = rows[0]
    if row["slot"] == tx["slot"] and "person_id" in row.keys() and row["person_id"] is None:
        return _state("UNKNOWN", "LEDGER_PERSON_NOT_RECORDED")
    if row["slot"] != tx["slot"] or ("person_id" in row.keys() and row["person_id"] != person_id):
        return _state("CONFLICT", "SLOT_OR_PERSON_MISMATCH")
    return _state("MATCH", "LEDGER_IDENTITY_MATCHED")


def _signals(db, person_id, tx, snapshot_signals, bad_unbound_signals, policy_sha256, model, ledger_policy):
    expected = tx.get("expected_signals")
    unknown = _state("UNKNOWN", "REFERENCE_HAS_NO_INDEPENDENT_SIGNAL_EXPECTATION")
    if expected is None:
        return unknown, unknown, []
    held = _state("UNKNOWN", "SIGNAL_EVIDENCE_UNAVAILABLE")
    if snapshot_signals is None or model["status"] != "MATCH":
        return held, held, []
    if not _matches(SHA256, ledger_policy):
        return _state("UNKNOWN", "LEDGER_SIGNAL_POLICY_UNVERIFIED"), held, []
    if ledger_policy != policy_sha256:
        return _state("CONFLICT", "LEDGER_SIGNAL_POLICY_DIFFERS_FROM_REFERENCE"), held, []
    signature = tx["signature"]
    linked = snapshot_signals.get(signature, [])
    if linked:
        # V1 signal records have a triggering signature and person, but no
        # triggering wallet. Only a unique ledger association is attributable.
        owners = db.execute(
            "SELECT wallet FROM signatures WHERE person_id=? AND signature=? LIMIT 2",
            (person_id, signature),
        ).fetchall()
        if len(owners) != 1:
            ambiguous = _state("UNKNOWN", "SIGNAL_WALLET_BINDING_AMBIGUOUS")
            return ambiguous, ambiguous, []
    actual = {}
    for row, body in linked:
        name = row["signal_type"]
        if (name not in SIGNAL_TYPES or not _matches(SHA256, row["signal_id"])
                or body.get("signal_type") != name or body.get("person_id") != person_id
                or body.get("signal_id") != row["signal_id"] or body.get("policy_hash") != policy_sha256
                or body.get("stage") != SIGNAL_TYPES[name] or body["stage"] != row["stage"]
                or digest(body) != row["content_hash"]):
            conflict = _state("CONFLICT", "SIGNAL_IDENTITY_POLICY_OR_DIGEST_MISMATCH")
            return conflict, held, []
        if name in actual:
            duplicate = _state("DUPLICATE", "MULTIPLE_SIGNALS_FOR_SAME_TRIGGER_AND_TYPE")
            return duplicate, held, []
        actual[name] = row["signal_id"]
    expected_by_type = {item["type"]: item["channels"] for item in expected}
    if actual.keys() - expected_by_type.keys():
        return _state("CONFLICT", "UNEXPECTED_SIGNAL_TYPE"), held, []
    if bad_unbound_signals and actual.keys() != expected_by_type.keys():
        return held, held, []
    if not expected:
        if bad_unbound_signals:
            return held, held, []
        absent = _state("NOT_EXPECTED", "NO_SIGNAL_PER_INDEPENDENT_EXPECTATION")
        return absent, absent, []
    if actual.keys() != expected_by_type.keys():
        return _state("MISSING", "EXPECTED_SIGNAL_NOT_RECORDED"), held, []
    matched = _state("MATCH", "EXPECTED_SIGNAL_TYPES_AND_POLICY_MATCHED")
    return matched, held, {actual[name]: channels for name, channels in expected_by_type.items()}


def _outbox(db, expected_channels, tables, fallback):
    if not expected_channels:
        return fallback, []
    if "outbox" not in tables:
        return _state("UNKNOWN", "OUTBOX_TABLE_UNAVAILABLE"), []
    states = []
    expected_rows = []
    known = {"PENDING", "RETRY_PENDING", "IN_FLIGHT", "COMMAND_ACCEPTED", "SENT_VERIFIED",
             "SENT_UNVERIFIED", "DRY_RUN_AUDIT", "CREDENTIAL_BLOCKED", "MANUAL_REVIEW"}
    for signal_id, channels in expected_channels.items():
        recorded = defaultdict(list)
        for row in db.execute("SELECT channel,status FROM outbox WHERE signal_id=?", (signal_id,)):
            recorded[row["channel"]].append(row["status"])
        for channel in recorded.keys() - set(channels):
            states.append({"signal_id": signal_id, "channel": channel if channel in CHANNELS else "UNRECOGNIZED",
                           "ledger_status": "UNEXPECTED_DUPLICATE" if len(recorded[channel]) > 1 else "UNEXPECTED",
                           "recipient_delivery": "UNKNOWN"})
        for channel in channels:
            records = recorded[channel]
            if not records:
                state = "MISSING"
            elif len(records) != 1:
                state = "DUPLICATE"
            else:
                state = records[0] if records[0] in known else "UNKNOWN"
            expected_rows.append({"signal_id": signal_id, "channel": channel, "ledger_status": state,
                                  "recipient_delivery": "UNKNOWN"})
    unexpected = bool(states)
    states.extend(expected_rows)
    if any(row["ledger_status"] in {"DUPLICATE", "UNEXPECTED_DUPLICATE"} for row in states):
        return _state("DUPLICATE", "MULTIPLE_OUTBOX_ROWS_FOR_SIGNAL_AND_CHANNEL"), states
    if any(row["ledger_status"] == "MISSING" for row in states):
        return _state("MISSING", "EXPECTED_OUTBOX_CHANNEL_NOT_RECORDED"), states
    if unexpected:
        return _state("CONFLICT", "UNEXPECTED_OUTBOX_CHANNEL_RECORDED"), states
    if not states:
        return _state("NOT_EXPECTED", "NO_CHANNEL_PER_INDEPENDENT_EXPECTATION"), []
    if any(row["ledger_status"] == "UNKNOWN" for row in states):
        return _state("UNKNOWN", "OUTBOX_STATUS_UNRECOGNIZED"), states
    return _state("MATCH", "OUTBOX_ROWS_PRESENT_RECIPIENT_DELIVERY_UNVERIFIED"), states


def _audit(db, reference):
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        raise ReconciliationError("SNAPSHOT_INTEGRITY_CHECK_FAILED")
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
    if not {"signatures", "cursors"}.issubset(tables):
        raise ReconciliationError("SCANNER_LEDGER_SCHEMA_REQUIRED")
    wallet, person = reference["wallet"], reference["person_id"]
    expected = {tx["signature"]: tx for tx in reference["transactions"]}
    cursor = db.execute("SELECT slot FROM cursors WHERE wallet=? LIMIT 2", (wallet,)).fetchall()
    watermark = cursor[0]["slot"] if len(cursor) == 1 else None
    if not _slot(watermark):
        watermark = None
    indexed = Counter(row["signature"] for row in db.execute(
        "SELECT signature FROM signatures WHERE wallet=? AND slot BETWEEN ? AND ?",
        (wallet, reference["start_slot"], reference["end_slot"]),
    ))
    unexpected = sorted(indexed.keys() - expected.keys(), key=str)
    snapshot_signals, bad_unbound_signals = None, False
    if "signals" in tables:
        snapshot_signals = defaultdict(list)
        for row in db.execute("SELECT signal_id,signal_type,stage,content_hash,body FROM signals WHERE person_id=?",
                              (person,)):
            body = _object(row["body"], canonical=True)
            signature = body and (body.get("triggering_signature") or body.get("latest_trade_signature"))
            if not _base58_size(signature, 64):
                bad_unbound_signals = True
            elif signature in expected:
                snapshot_signals[signature].append((row, body))
    ledger_policy = None
    if "v1_meta" in tables:
        policies = db.execute("SELECT value FROM v1_meta WHERE key='policy_hash' LIMIT 2").fetchall()
        if len(policies) == 1:
            ledger_policy = policies[0]["value"]
    rows = []
    for tx in reference["transactions"]:
        sig = tx["signature"]
        existing = _ledger_row(db, "signatures", wallet, sig)
        missing = (_state("MISSING", "ABSENT_FROM_BACKUP_WITH_LATER_CURSOR")
                   if watermark is not None and watermark > tx["slot"]
                   else _state("UNKNOWN", "SCANNER_CURSOR_NOT_STRICTLY_PAST_SLOT"))
        index_state = _identity(existing, tx, person, missing)
        detection = _state("UNKNOWN", "DETECTION_EVIDENCE_NOT_RECORDED")
        if "signature_detections" in tables:
            absent = detection if existing else missing
            detection = _identity(_ledger_row(db, "signature_detections", wallet, sig), tx, person, absent)
        classification = _state("UNKNOWN", "CLASSIFICATION_EVIDENCE_UNAVAILABLE")
        model = _state("UNKNOWN", "MODEL_PROCESSING_EVIDENCE_UNAVAILABLE")
        recorded_classification = None
        if index_state["status"] == "MATCH":
            record = existing[0]
            body = _object(record["body"])
            if (body is None or body.get("wallet") != wallet or body.get("signature") != sig
                    or body.get("person_id") != person or body.get("slot") != tx["slot"]):
                classification = _state("CONFLICT", "CLASSIFICATION_IDENTITY_MISMATCH")
            elif not _matches(SHA256, record["raw_hash"]):
                classification = _state("UNKNOWN", "CLASSIFICATION_RAW_HASH_NOT_RECORDED")
            else:
                actual = body.get("classification")
                if isinstance(actual, str) and actual in CLASSIFICATIONS:
                    recorded_classification = actual
                    if tx.get("classification") is None:
                        classification = _state("UNKNOWN", "REFERENCE_HAS_NO_INDEPENDENT_CLASSIFICATION")
                    elif actual != tx["classification"]:
                        classification = _state("CONFLICT", "CLASSIFICATION_DIFFERS_FROM_REFERENCE")
                    else:
                        classification = _state("MATCH", "CLASSIFICATION_MATCHES_SUPPLIED_EXPECTATION")
                else:
                    classification = _state("UNKNOWN", "LOCAL_CLASSIFICATION_UNRESOLVED")
            if "v1_seen" in tables:
                processed = _ledger_row(db, "v1_seen", wallet, sig)
                if len(processed) > 1:
                    model = _state("DUPLICATE", "MULTIPLE_MODEL_PROCESSING_ROWS")
                elif processed:
                    model = _state("MATCH", "MODEL_PROCESSING_MARKER_RECORDED")
                else:
                    model = _state("MISSING", "INDEXED_SIGNATURE_NOT_MARKED_MODEL_PROCESSED")
        signal, outbox_fallback, channels = _signals(db, person, tx, snapshot_signals, bad_unbound_signals,
                                                     reference.get("policy_sha256"), model, ledger_policy)
        outbox, channel_rows = _outbox(db, channels, tables, outbox_fallback)
        rows.append({"signature": sig, "slot": tx["slot"], "expected_classification": tx.get("classification"),
                     "recorded_classification": recorded_classification, "stages": {
            "detection": detection, "indexed": index_state, "classification": classification,
            "model": model, "signal": signal, "outbox": outbox,
        }, "channels": channel_rows})
    summary = {stage: dict.fromkeys(STATUS, 0) for stage in STAGES}
    for row in rows:
        for stage, outcome in row["stages"].items():
            summary[stage][outcome["status"]] += 1
    # Duplicate entries outside the expected set are counted separately.
    unexpected_duplicates = sum(indexed[sig] - 1 for sig in unexpected)
    if unexpected or any(counts["MISSING"] or counts["CONFLICT"] or counts["DUPLICATE"]
                         for counts in summary.values()):
        status = "GAPS"
    elif not rows:
        status = "NO_REFERENCE_EVENTS"
    elif any(counts["UNKNOWN"] for counts in summary.values()):
        status = "PARTIAL"
    else:
        status = "MATCHED_WITHIN_SUPPLIED_WINDOW"
    return {
        "status": status, "start_slot": reference["start_slot"], "end_slot": reference["end_slot"],
        "scanner_cursor_slot": watermark, "reference_signatures": len(expected),
        "unexpected_indexed_signatures": len(unexpected), "unexpected_duplicate_index_rows": unexpected_duplicates,
        "stages": summary, "rows": rows,
        "unexpected_signatures": [sig for sig in unexpected if _base58_size(sig, 64)],
        "scope": "SUPPLIED_WINDOW_ONLY",
        "monitoring_start_boundary": "NOT_VERIFIED",
        "reference_provenance": "CALLER_SUPPLIED_SOURCE_AND_CAPTURE_HASH_UNVERIFIED",
        "classification_provenance": "SUPPLIED_EXPECTATIONS_VS_LEDGER_LABELS_ONLY",
        "recipient_delivery": "NOT_VERIFIED",
    }


def reconcile_snapshot(snapshot, snapshot_sha256, reference, reference_sha256, *, scanner_source_id):
    """Audit a standalone SQLite backup and independently prepared reference file."""
    snapshot, reference = Path(snapshot), Path(reference)
    try:
        raw = reference.read_bytes()
        if (not _matches(SHA256, reference_sha256)
                or hashlib.sha256(raw).hexdigest() != reference_sha256):
            raise ReconciliationError("REFERENCE_SHA256_MISMATCH")
        try:
            manifest = _reference(loads(raw), scanner_source_id)
        except (ValueError, RecursionError) as exc:
            if isinstance(exc, ReconciliationError):
                raise
            raise ReconciliationError("REFERENCE_INVALID_JSON") from None
        _snapshot(snapshot, snapshot_sha256)
        with closing(sqlite3.connect(snapshot.resolve().as_uri() + "?mode=ro&immutable=1",
                                     uri=True, timeout=3)) as db:
            result = _audit(db, manifest)
        _snapshot(snapshot, snapshot_sha256)
    except sqlite3.Error:
        raise ReconciliationError("SNAPSHOT_SQLITE_READ_FAILED") from None
    except OSError:
        raise ReconciliationError("AUDIT_INPUT_UNREADABLE") from None
    return {**result, "schema_version": 1, "snapshot_sha256": snapshot_sha256,
            "reference_sha256": reference_sha256, "reference_capture_sha256": manifest["capture_sha256"]}
