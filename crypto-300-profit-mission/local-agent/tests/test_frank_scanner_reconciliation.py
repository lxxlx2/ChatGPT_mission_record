import hashlib
import json
from pathlib import Path
import sqlite3
import stat

import pytest

from mission_agent.hashing import digest
from mission_agent.signals.reconciliation import ReconciliationError, reconcile_snapshot
from mission_agent.signals.store import Ledger
from scripts.audit_frank_scanner_snapshot import main


WALLET = "1" * 31 + "2"
OTHER = "1" * 31 + "3"
POLICY = "a" * 64
ACCUM = "FRANK_ACCUMULATION_SIGNAL"


def signature(last):
    return "1" * 63 + last


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tx(last="2", slot=101, **expected):
    return {"signature": signature(last), "slot": slot, **expected}


def reference(*transactions, **changes):
    return {
        "schema_version": 1, "chain": "solana", "commitment": "finalized", "complete": True,
        "start_slot": 100, "end_slot": 105, "finalized_through_slot": 105,
        "source_id": "independent_reference", "capture_sha256": "b" * 64,
        "wallet": WALLET, "person_id": "frank", "policy_sha256": POLICY,
        "transactions": list(transactions), **changes,
    }


@pytest.fixture
def db(tmp_path):
    ledger = Ledger(tmp_path / "ledger.sqlite")
    ledger.checkpoint(WALLET, signature("9"), 105)
    ledger.db.executescript("""
        CREATE TABLE signature_detections(wallet TEXT, signature TEXT, person_id TEXT, slot INTEGER);
        CREATE TABLE v1_seen(wallet TEXT, signature TEXT);
        CREATE TABLE v1_meta(key TEXT PRIMARY KEY, value TEXT);
    """)
    ledger.db.execute("INSERT INTO v1_meta VALUES('policy_hash',?)", (POLICY,))
    try:
        yield ledger.db
    finally:
        ledger.db.close()


def insert(db, event, *, wallet=WALLET, person="frank", classification="PASSIVE_TRANSFER",
           detection=True, indexed=True, processed=True):
    sig, slot = event["signature"], event["slot"]
    if detection:
        db.execute("INSERT INTO signature_detections VALUES(?,?,?,?)", (wallet, sig, person, slot))
    if indexed:
        body = {"wallet": wallet, "signature": sig, "slot": slot, "person_id": person,
                "classification": classification}
        db.execute("INSERT INTO signatures(wallet,signature,person_id,slot,raw_hash,raw_reference,body,alert_state,alert_reason)"
                   " VALUES(?,?,?,?,?,?,?,'NO','fixture')",
                   (wallet, sig, person, slot, "c" * 64, "private-fixture-path", json.dumps(body)))
    if processed:
        db.execute("INSERT INTO v1_seen VALUES(?,?)", (wallet, sig))


def emit(db, event, *, stage="PRECONFIRM", channel="local", valid_digest=True):
    body = {"signal_id": "d" * 64, "person_id": "frank", "signal_type": ACCUM,
            "stage": stage, "policy_hash": POLICY, "triggering_signature": event["signature"]}
    db.execute("INSERT INTO signals VALUES(?,?,?,?,?,?,?,?,?)",
               (body["signal_id"], "frank", "fixture", "episode", ACCUM, stage, "1000",
                digest(body) if valid_digest else "e" * 64, json.dumps(body)))
    if channel is not None:
        db.execute("INSERT INTO outbox(signal_id,channel,status,receipt) VALUES(?,?,'COMMAND_ACCEPTED',?)",
                   (body["signal_id"], channel, '{"private":"local-receipt"}'))


def inputs(tmp_path, db, manifest):
    target = tmp_path / "backup.sqlite"
    with sqlite3.connect(target) as backup:
        db.backup(backup)
        backup.execute("PRAGMA journal_mode=DELETE")
    ref = tmp_path / "reference.json"
    ref.write_text(json.dumps(manifest))
    return target, checksum(target), ref, checksum(ref)


def run(tmp_path, db, manifest):
    args = inputs(tmp_path, db, manifest)
    result = reconcile_snapshot(*args, scanner_source_id="primary_scanner")
    assert checksum(args[0]) == args[1]
    assert not Path(str(args[0]) + "-wal").exists()
    return result


def test_bounded_match_and_recipient_delivery_still_unknown(tmp_path, db):
    event = tx(classification="ACTIVE_TRADE", expectation_sha256="f" * 64,
               expected_signals=[{"type": ACCUM, "channels": ["local"]}])
    insert(db, event, classification="ACTIVE_TRADE")
    emit(db, event)
    result = run(tmp_path, db, reference(event))
    assert result["status"] == "MATCHED_WITHIN_SUPPLIED_WINDOW"
    assert all(row["MATCH"] == 1 for row in result["stages"].values())
    assert result["rows"][0]["channels"][0]["ledger_status"] == "COMMAND_ACCEPTED"
    assert result["rows"][0]["channels"][0]["recipient_delivery"] == "UNKNOWN"
    assert result["recipient_delivery"] == "NOT_VERIFIED"
    assert "private-fixture-path" not in json.dumps(result)
    assert "local-receipt" not in json.dumps(result)


def test_absence_at_cursor_slot_is_unknown_and_older_absence_is_missing(tmp_path, db):
    older, same_slot = tx("2", 104), tx("3", 105)
    result = run(tmp_path, db, reference(older, same_slot))
    assert result["status"] == "GAPS"
    assert result["stages"]["indexed"]["MISSING"] == 1
    assert result["stages"]["indexed"]["UNKNOWN"] == 1
    assert result["rows"][1]["stages"]["indexed"]["reason"] == "SCANNER_CURSOR_NOT_STRICTLY_PAST_SLOT"
    assert result["rows"][0]["stages"]["indexed"]["reason"] == "ABSENT_FROM_BACKUP_WITH_LATER_CURSOR"
    assert result["monitoring_start_boundary"] == "NOT_VERIFIED"


def test_unexpected_rows_and_wrong_slot_are_separately_identified(tmp_path, db):
    first = tx("2", 103)
    insert(db, tx("2", 106))
    insert(db, tx("3", 104))
    insert(db, tx("4", 103), wallet=OTHER)
    result = run(tmp_path, db, reference(first))
    assert result["status"] == "GAPS"
    assert result["stages"]["indexed"]["CONFLICT"] == 1
    assert result["unexpected_signatures"] == [signature("3")]


def test_independent_classification_expectation_is_not_inferred(tmp_path, db):
    event = tx()
    insert(db, event)
    result = run(tmp_path, db, reference(event))
    assert result["status"] == "PARTIAL"
    assert result["stages"]["indexed"]["MATCH"] == 1
    assert result["stages"]["classification"]["UNKNOWN"] == 1
    assert result["stages"]["signal"]["UNKNOWN"] == 1


def test_known_label_disagreement_and_duplicate_model_marker_are_visible(tmp_path, db):
    event = tx(classification="ACTIVE_TRADE", expectation_sha256="f" * 64)
    insert(db, event)
    db.execute("INSERT INTO v1_seen VALUES(?,?)", (WALLET, event["signature"]))
    result = run(tmp_path, db, reference(event))
    assert result["stages"]["classification"]["CONFLICT"] == 1
    assert result["stages"]["model"]["DUPLICATE"] == 1


@pytest.mark.parametrize(("channel", "expected_outbox"), [(None, "MISSING"), ("gmail", "MISSING"), ("local", "MATCH")])
def test_signal_type_and_expected_queue_channel_are_separate(tmp_path, db, channel, expected_outbox):
    event = tx(classification="ACTIVE_TRADE", expectation_sha256="f" * 64,
               expected_signals=[{"type": ACCUM, "channels": ["local"]}])
    insert(db, event, classification="ACTIVE_TRADE")
    emit(db, event, channel=channel)
    result = run(tmp_path, db, reference(event))
    assert result["stages"]["signal"]["MATCH"] == 1
    assert result["stages"]["outbox"][expected_outbox] == 1


def test_expected_signal_gap_and_explicitly_no_signal_have_different_states(tmp_path, db):
    first = tx(expectation_sha256="f" * 64, expected_signals=[{"type": ACCUM, "channels": ["local"]}])
    second = tx("3", expectation_sha256="f" * 64, expected_signals=[])
    insert(db, first, classification="ACTIVE_TRADE")
    insert(db, second)
    result = run(tmp_path, db, reference(first, second))
    assert result["stages"]["signal"]["MISSING"] == 1
    assert result["stages"]["signal"]["NOT_EXPECTED"] == 1


def test_unrecognized_outbox_value_is_unknown_without_echoing_ledger_content(tmp_path, db):
    event = tx(expectation_sha256="f" * 64, expected_signals=[{"type": ACCUM, "channels": ["local"]}])
    insert(db, event)
    emit(db, event)
    db.execute("UPDATE outbox SET status=?", ("private malformed row",))
    result = run(tmp_path, db, reference(event))
    item = result["rows"][0]
    assert item["stages"]["outbox"]["reason"] == "OUTBOX_STATUS_UNRECOGNIZED"
    assert item["channels"][0]["recipient_delivery"] == "UNKNOWN"
    assert "private malformed row" not in json.dumps(result)


def test_policy_must_match_even_for_an_independently_expected_absence(tmp_path, db):
    event = tx(expectation_sha256="f" * 64, expected_signals=[])
    insert(db, event)
    result = run(tmp_path, db, reference(event, policy_sha256="8" * 64))
    assert result["rows"][0]["stages"]["signal"]["reason"] == "LEDGER_SIGNAL_POLICY_DIFFERS_FROM_REFERENCE"
    assert result["stages"]["signal"]["CONFLICT"] == 1


def test_signal_trigger_shared_by_two_wallets_cannot_be_attributed(tmp_path, db):
    event = tx(expectation_sha256="f" * 64, expected_signals=[{"type": ACCUM, "channels": ["local"]}])
    insert(db, event)
    insert(db, event, wallet=OTHER)
    emit(db, event)
    result = run(tmp_path, db, reference(event))
    assert result["rows"][0]["stages"]["signal"]["reason"] == "SIGNAL_WALLET_BINDING_AMBIGUOUS"
    assert result["stages"]["signal"]["UNKNOWN"] == 1


@pytest.mark.parametrize(("changes", "reason"), [
    ({"complete": False}, "REFERENCE_COMPLETE_FINALIZED_WINDOW_REQUIRED"),
    ({"finalized_through_slot": 104}, "REFERENCE_COMPLETE_FINALIZED_WINDOW_REQUIRED"),
    ({"source_id": "PRIMARY_SCANNER"}, "REFERENCE_AND_SCANNER_SOURCE_NOT_DISTINCT"),
    ({"transactions": [tx(), tx()]}, "REFERENCE_DUPLICATE_SIGNATURE"),
    ({"transactions": [tx(slot=106)]}, "REFERENCE_TRANSACTION_OUT_OF_SCOPE"),
    ({"transactions": [tx(classification="ACTIVE_TRADE")]}, "REFERENCE_EXPECTATION_SHA256_REQUIRED"),
    ({"transactions": [tx(expected_signals=[{"type": ACCUM, "channels": ["local", "local"]}])]}, "REFERENCE_SIGNAL_INVALID"),
])
def test_bad_reference_is_rejected(tmp_path, db, changes, reason):
    args = inputs(tmp_path, db, reference(tx(), **changes))
    with pytest.raises(ReconciliationError, match=reason):
        reconcile_snapshot(*args, scanner_source_id="primary_scanner")


def test_wrong_hash_and_possible_wal_incomplete_copy_are_rejected(tmp_path, db):
    target, sha, ref, ref_sha = inputs(tmp_path, db, reference(tx()))
    with pytest.raises(ReconciliationError, match="SNAPSHOT_SHA256_MISMATCH"):
        reconcile_snapshot(target, "a" * 64, ref, ref_sha, scanner_source_id="primary_scanner")
    with pytest.raises(ReconciliationError, match="REFERENCE_SHA256_MISMATCH"):
        reconcile_snapshot(target, sha, ref, "a" * 64, scanner_source_id="primary_scanner")
    Path(str(target) + "-wal").touch()
    with pytest.raises(ReconciliationError, match="SNAPSHOT_SIDECAR_PRESENT"):
        reconcile_snapshot(target, sha, ref, ref_sha, scanner_source_id="primary_scanner")


def test_empty_reference_is_never_a_pass(tmp_path, db):
    assert run(tmp_path, db, reference())["status"] == "NO_REFERENCE_EVENTS"


def test_cli_stdout_omits_identities_and_private_output_is_exclusive(tmp_path, db, capsys):
    event = tx()
    insert(db, event)
    target, sha, ref, ref_sha = inputs(tmp_path, db, reference(event))
    report = tmp_path / "private.json"
    args = ["--snapshot", str(target), "--snapshot-sha256", sha, "--reference", str(ref),
            "--reference-sha256", ref_sha, "--scanner-source-id", "primary_scanner",
            "--private-report", str(report)]
    assert main(args) == 1
    summary = capsys.readouterr().out
    assert event["signature"] not in summary and WALLET not in summary
    assert json.loads(report.read_bytes())["rows"][0]["signature"] == event["signature"]
    assert stat.S_IMODE(report.stat().st_mode) == 0o600
    before = checksum(report)
    assert main(args) == 2
    assert checksum(report) == before
