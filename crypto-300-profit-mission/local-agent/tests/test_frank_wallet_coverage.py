from datetime import datetime, timezone
import hashlib
import json
import sqlite3

import pytest

from mission_agent.mission_control.wallet_activity import activity
from mission_agent.mission_control.wallet_coverage import CoverageError, coverage_for_wallet
from mission_agent.mission_control.wallet_owner_at_slot import FRANK_WALLET


NOW = 1_795_000_000
DAY = 86_400
OTHER_WALLET = "2" * 32
RAW_HASH = "a" * 64


def sig(character):
    return character * 88


@pytest.fixture
def index(tmp_path):
    source = tmp_path / "private-fixture.sqlite"
    with sqlite3.connect(source) as db:
        db.executescript("""
            CREATE TABLE signatures(wallet TEXT, signature TEXT, person_id TEXT,
                block_time INTEGER, body TEXT, raw_hash TEXT, raw_reference TEXT);
            CREATE TABLE trades(wallet TEXT, signature TEXT, mint TEXT, side TEXT);
        """)
        db.executemany("INSERT INTO signatures VALUES (?, ?, ?, ?, ?, ?, ?)", [
            (FRANK_WALLET, sig(code), person, at, body, raw_hash, "/private/secret-path")
            for code, person, at, body, raw_hash in [
                ("1", "frank", NOW, '{"classification":"ACTIVE_TRADE"}', RAW_HASH),
                ("2", "frank", NOW - DAY, '{"classification":"PASSIVE_TRANSFER"}', RAW_HASH),
                ("3", "frank", NOW - 7 * DAY, '{"classification":"FAILED_TX"}', RAW_HASH),
                ("4", "frank", NOW - 30 * DAY, '{"classification":"ATA_CREATE"}', RAW_HASH),
                ("5", "frank", NOW - 30 * DAY - 1, '{"classification":"UNKNOWN_NEEDS_REVIEW"}', RAW_HASH),
                ("6", "frank", None, '{"classification":"unrecognized"}', "https://private.invalid/token"),
                ("7", "frank", NOW, "{invalid JSON", RAW_HASH),
                ("8", "frank", NOW + 1, '{"classification":"ACTIVE_TRADE"}', RAW_HASH),
                ("9", "another_person", NOW, '{"classification":"PASSIVE_TRANSFER"}', RAW_HASH),
            ]
        ])
    return source


@pytest.mark.parametrize("days,total,oldest,untimed,unresolved", [
    (1, 3, NOW - DAY, 0, 1),
    (7, 4, NOW - 7 * DAY, 0, 1),
    (30, 5, NOW - 30 * DAY, 0, 1),
    ("all", 7, NOW - 30 * DAY - 1, 1, 3),
])
def test_matches_index_projection_and_window_bounds(index, days, total, oldest, untimed, unresolved):
    initial_bytes = hashlib.sha256(index.read_bytes()).hexdigest()
    report = coverage_for_wallet(index, NOW, days=days)
    data = report["data"]
    canonical = activity(index, NOW, days)

    assert report["status"] == "PARTIAL_SOURCE"
    assert report["as_of"] == data["end_at"] == data["indexed_newest_at"] == NOW
    assert data["days"] == days
    assert data["start_at"] == (None if days == "all" else NOW - days * DAY)
    assert data["indexed_oldest_at"] == oldest
    assert data["indexed_signatures"] == canonical["signatures"] == total
    assert data["timed_signatures"] == total - untimed
    assert data["untimed_signatures"] == untimed
    assert data["untimed_source_signatures"] == 1
    assert data["parser_unresolved_signatures"] == unresolved
    assert {key: count for key, count in data["categories"].items() if count} == canonical["categories"]
    assert len(data["categories"]) == 6
    assert data["pending_detected_signatures"] is None
    assert data["scanner_observed_at"] is None
    assert report["coverage"] == {
        "full_chain_verified": False, "known_gaps": None, "backfill_status": "UNKNOWN",
        "stop_reason": "UNKNOWN", "stop_observed_at": None,
    }
    assert report["sources"][0]["newest_indexed_raw_ref"] == {"signature": sig("1"), "raw_sha256": RAW_HASH}
    serialized = json.dumps(report)
    assert "private" not in serialized and "invalid JSON" not in serialized
    assert hashlib.sha256(index.read_bytes()).hexdigest() == initial_bytes


def test_reports_empty_index_and_absent_evidence_as_distinct_states(index):
    report = coverage_for_wallet(index, NOW - 40 * DAY, days=1)
    assert report["data"]["indexed_signatures"] == 0
    assert report["data"]["indexed_oldest_at"] is None
    assert report["data"]["indexed_newest_at"] is None
    assert report["data"]["scanner_observed_at"] is None
    assert report["data"]["untimed_source_signatures"] == 1
    assert report["coverage"]["known_gaps"] is None
    assert report["coverage"]["full_chain_verified"] is False


def test_index_digest_binds_source_rows_and_scope(index):
    def fingerprint(days):
        return coverage_for_wallet(index, NOW, days=days)["sources"][0]["source_sha256"]

    original, recent = fingerprint("all"), fingerprint(1)
    assert original != recent
    with sqlite3.connect(index) as db:
        db.execute("UPDATE signatures SET body=? WHERE signature=?",
                   ('{"classification":"UNKNOWN_NEEDS_REVIEW","parser_version":"next"}', sig("5")))
    assert fingerprint("all") != original
    assert fingerprint(1) == recent


def make_scanner_tables(index, *, health):
    with sqlite3.connect(index) as db:
        db.executescript("""
            CREATE TABLE health(wallet TEXT PRIMARY KEY, body TEXT);
            CREATE TABLE signature_detections(wallet TEXT, signature TEXT, person_id TEXT,
                block_time INTEGER, seen_at REAL, state TEXT);
        """)
        db.executemany("INSERT INTO health VALUES (?, ?)", [
            (FRANK_WALLET, json.dumps(health)),
            (OTHER_WALLET, json.dumps({"last_successful_poll": NOW - 1, "status": "RUNNING"})),
        ])
        db.executemany("INSERT INTO signature_detections VALUES (?, ?, ?, ?, ?, ?)", [
            (FRANK_WALLET, sig("A"), "frank", NOW - 10, NOW - 1, "RAW_PENDING"),
            (FRANK_WALLET, sig("B"), "frank", NOW - 2 * DAY, NOW - 1, "RAW_PENDING"),
            (FRANK_WALLET, sig("C"), "frank", None, NOW - 1, "RAW_PENDING"),
            (FRANK_WALLET, sig("D"), "frank", NOW - 10, NOW + 1, "RAW_PENDING"),
            (FRANK_WALLET, sig("E"), "frank", NOW - 10, NOW - 1, "CLASSIFIED_DURABLE"),
            (FRANK_WALLET, sig("1"), "frank", NOW, NOW - 1, "RAW_PENDING"),
            (OTHER_WALLET, sig("F"), "frank", NOW - 10, NOW - 1, "RAW_PENDING"),
            (FRANK_WALLET, sig("G"), "another_person", NOW - 10, NOW - 1, "RAW_PENDING"),
            (FRANK_WALLET, "https://private.invalid/token", "frank", NOW - 10, NOW - 1, "RAW_PENDING"),
        ])


def test_scanner_heartbeat_and_detection_evidence_are_scoped(index):
    make_scanner_tables(index, health={
        "last_successful_poll": NOW - 3.5, "status": "RUNNING", "lag_seconds": 0,
        "last_error": "ValueError:CURSOR_GAP_UNRESOLVED",
    })
    recent = coverage_for_wallet(index, NOW, days=1)
    assert recent["data"]["pending_detected_signatures"] == 1
    assert recent["data"]["scanner_observed_at"] == NOW - 4
    assert recent["coverage"]["known_gaps"] == ["DETECTED_SIGNATURES_NOT_INDEXED"]
    assert recent["coverage"]["stop_reason"] == "UNKNOWN"
    assert len(recent["sources"]) == 3
    assert "private" not in json.dumps(recent)
    full = coverage_for_wallet(index, NOW)
    assert full["data"]["pending_detected_signatures"] == 3
    earlier = coverage_for_wallet(index, NOW - 100, days=1)
    assert earlier["data"]["pending_detected_signatures"] == 0
    assert earlier["data"]["scanner_observed_at"] is None
    assert earlier["coverage"]["known_gaps"] is None


@pytest.mark.parametrize("attempt,processed_signature,expected", [
    (NOW - 1, sig("1"), "CURSOR_GAP_UNRESOLVED"),
    (NOW + 1, sig("1"), "UNKNOWN"),
    (NOW - 1, sig("2"), "UNKNOWN"),
])
def test_stop_reason_requires_matching_timestamped_scanner_evidence(index, attempt, processed_signature, expected):
    failure = "ValueError:CURSOR_GAP_UNRESOLVED"
    make_scanner_tables(index, health={
        "last_successful_poll": NOW - 30, "status": "RETRY_PENDING",
        "last_error": failure, "last_local_signature": sig("1"),
    })
    pending = coverage_for_wallet(index, NOW)["coverage"]
    assert pending["stop_reason"] == "UNKNOWN"
    health = index.with_name("health.json")
    health.write_text(json.dumps({
        "system": "FRANK_ONLY", "last_processed_signature": processed_signature,
        "status": "RETRY_PENDING", "last_error": failure,
        "last_poll_at": datetime.fromtimestamp(attempt, timezone.utc).isoformat(),
    }))
    report = coverage_for_wallet(index, NOW)
    assert report["coverage"]["stop_reason"] == expected
    assert report["coverage"]["stop_observed_at"] == (None if expected == "UNKNOWN" else attempt)
    assert ("CURSOR_GAP_UNRESOLVED" in report["coverage"]["known_gaps"]) == (expected != "UNKNOWN")
    assert report["coverage"]["backfill_status"] == "UNKNOWN"
    assert report["coverage"]["full_chain_verified"] is False


def test_invalid_and_missing_sources_remain_errors(index, tmp_path):
    for invalid_days in (True, 0, 90, "1", "ALL"):
        with pytest.raises(CoverageError) as bad:
            coverage_for_wallet(index, NOW, days=invalid_days)
        assert (bad.value.code, bad.value.http_status) == ("INVALID_INPUT", 400)

    with pytest.raises(CoverageError) as bad:
        coverage_for_wallet(index, float(NOW))
    assert (bad.value.code, bad.value.http_status) == ("INVALID_INPUT", 400)

    for source in (tmp_path / "absent.sqlite", tmp_path / "invalid.sqlite", tmp_path / "link.sqlite"):
        if source.name == "invalid.sqlite":
            source.write_text("sqlite format invalid")
        if source.name == "link.sqlite":
            source.symlink_to(index)
        with pytest.raises(CoverageError) as bad:
            coverage_for_wallet(source, NOW)
        assert (bad.value.code, bad.value.http_status) == ("SOURCE_UNAVAILABLE", 503)
        assert source.name not in str(bad.value)
