"""F1 synthetic-only evidence gate checks: absolutely no real subprocess calls."""
import base64
import json
import os
import stat
import subprocess
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from scripts.frank_c2a_f1_evidence import (
    CAPTURE_LIMIT, RECORD_FILENAME, EvidenceGateError,
    checkpoint_then_simulate_rollback, persist_failed_bootstrap,
)


def private_dir(tmp_path):
    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    return folder


def failure(*, rc=5, stdout=b"", stderr=b"unexpected failed bootstrap"):
    return subprocess.CompletedProcess(
        args=["/bin/launchctl", "bootstrap", "gui/501", "/topsecret/path.plist"],
        returncode=rc, stdout=stdout, stderr=stderr,
    )


def test_failure_evidence_fsynced_before_mock_rollback(tmp_path):
    root = private_dir(tmp_path)
    observed = []
    evidence = failure(rc=37, stdout=b"out", stderr=b"stderr\x00raw")

    def rollback_spy(path):
        saved = json.loads(path.read_text())
        assert saved["returncode"] == 37
        assert base64.b64decode(saved["stderr"]["captured_base64"]) == b"stderr\x00raw"
        assert saved["argv_saved"] is False
        observed.append(path)

    with patch("os.fsync", wraps=os.fsync) as fsync:
        result = checkpoint_then_simulate_rollback(root, evidence, rollback_spy,
            recorded_at_utc=datetime(2026, 10, 25, 22, 2, 54, tzinfo=timezone.utc))
        assert fsync.call_count >= 3
    assert observed == [result]
    assert result.name == RECORD_FILENAME
    assert stat.S_IMODE(result.stat().st_mode) == 0o600
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert "topsecret" not in result.read_text()
    assert not any(x.name.endswith(".tmp") for x in root.iterdir())


def test_failed_fsync_blocks_mock_rollback(tmp_path):
    root = private_dir(tmp_path)
    called = []
    with patch("os.fsync", side_effect=OSError("synthetic disk failure")):
        with pytest.raises(EvidenceGateError, match="EVIDENCE_PERSIST_FAILED"):
            checkpoint_then_simulate_rollback(root, failure(), called.append)
    assert called == []
    assert not (root / RECORD_FILENAME).exists()


def test_no_overwrite_or_second_rollback_on_repeat(tmp_path):
    root = private_dir(tmp_path)
    before = persist_failed_bootstrap(root, failure(rc=10))
    original = before.read_bytes()
    called = []
    with pytest.raises(EvidenceGateError, match="EVIDENCE_ALREADY_EXISTS"):
        checkpoint_then_simulate_rollback(root, failure(rc=20), called.append)
    assert before.read_bytes() == original
    assert not called


def test_symlink_evidence_dir_rejected(tmp_path):
    root = private_dir(tmp_path)
    sym = tmp_path / "shortcut"
    sym.symlink_to(root, target_is_directory=True)
    with pytest.raises(EvidenceGateError, match="EVIDENCE_DIR_SYMLINK"):
        persist_failed_bootstrap(sym, failure())
    assert not (root / RECORD_FILENAME).exists()


def test_nonprivate_directory_fails_closed(tmp_path):
    root = private_dir(tmp_path)
    os.chmod(root, 0o755)
    called = []
    with pytest.raises(EvidenceGateError, match="EVIDENCE_DIR_NOT_PRIVATE"):
        checkpoint_then_simulate_rollback(root, failure(), called.append)
    assert not called


def test_preexisting_symlink_record_not_followed(tmp_path):
    root = private_dir(tmp_path)
    target = tmp_path / "unrelated.txt"
    target.write_text("private data")
    (root / RECORD_FILENAME).symlink_to(target)
    with pytest.raises(EvidenceGateError, match="EVIDENCE_ALREADY_EXISTS"):
        persist_failed_bootstrap(root, failure())
    assert target.read_text() == "private data"


def test_long_streams_bounded_and_truncation_disclosed(tmp_path):
    root = private_dir(tmp_path)
    output = b"x" * (CAPTURE_LIMIT + 245)
    record_path = persist_failed_bootstrap(root, failure(stdout=output, stderr=output))
    content = json.loads(record_path.read_text())
    assert content["stdout"]["truncated"] is True
    assert content["stderr"]["truncated"] is True
    assert content["stdout"]["total_bytes"] == len(output)
    assert len(base64.b64decode(content["stdout"]["captured_base64"])) == CAPTURE_LIMIT
    assert content["stdout"]["sha256"] == content["stderr"]["sha256"]


@pytest.mark.parametrize(
    "stdout,stderr",
    [
        (None, None),
        (None, b""),
        (b"", None),
        (None, b"diagnostics"),
        (b"diagnostics", None),
    ],
)
def test_uncaptured_streams_rejected_without_saved_record_or_mock_rollback(
    tmp_path, stdout, stderr,
):
    root = private_dir(tmp_path)
    called = []
    completed = failure(stdout=stdout, stderr=stderr)
    # A missing capture is not a known empty stream. Fail before the first write,
    # and do not call the mock callback (not an actual production rollback).
    with patch("os.fsync", wraps=os.fsync) as fsync:
        with pytest.raises(EvidenceGateError, match="EVIDENCE_STREAM_NOT_CAPTURED"):
            checkpoint_then_simulate_rollback(root, completed, called.append)
    assert fsync.call_count == 0
    assert called == []
    assert list(root.iterdir()) == []


def test_default_completed_process_without_capture_is_not_empty(tmp_path):
    root = private_dir(tmp_path)
    completed = subprocess.CompletedProcess(args=["SYNTHETIC_ONLY"], returncode=5)
    assert completed.stdout is None and completed.stderr is None
    with pytest.raises(EvidenceGateError, match="EVIDENCE_STREAM_NOT_CAPTURED"):
        persist_failed_bootstrap(root, completed)
    assert not list(root.iterdir())


def test_explicitly_captured_empty_streams_get_known_zero_length_and_digest(tmp_path):
    root = private_dir(tmp_path)
    saved = persist_failed_bootstrap(root, failure(stdout=b"", stderr=b""))
    data = json.loads(saved.read_text())
    import hashlib
    for name in ("stdout", "stderr"):
        assert data[name] == {
            "total_bytes": 0,
            "sha256": hashlib.sha256(b"").hexdigest(),
            "captured_bytes": 0,
            "truncated": False,
            "captured_base64": "",
        }


def test_invalid_stream_type_does_not_write_or_call_mock_rollback(tmp_path):
    root = private_dir(tmp_path)
    called = []
    with pytest.raises(EvidenceGateError, match="EVIDENCE_STREAM_INVALID"):
        checkpoint_then_simulate_rollback(
            root, failure(stdout=b"", stderr=object()), called.append,
        )
    assert called == []
    assert not list(root.iterdir())


def test_success_never_writes_or_calls_rollback(tmp_path):
    root = private_dir(tmp_path)
    called = []
    result = failure(rc=0)
    assert checkpoint_then_simulate_rollback(root, result, called.append) is None
    assert not called
    assert not list(root.iterdir())


@pytest.mark.parametrize("rc", [None, 0, True, "1", 1.4])
def test_persist_rejects_invalid_or_success_return_code(tmp_path, rc):
    root = private_dir(tmp_path)
    with pytest.raises(EvidenceGateError):
        persist_failed_bootstrap(root, failure(rc=rc))
    assert not list(root.iterdir())


def test_timestamp_must_be_explicit_utc(tmp_path):
    root = private_dir(tmp_path)
    with pytest.raises(EvidenceGateError, match="EVIDENCE_TIMESTAMP_NOT_UTC"):
        persist_failed_bootstrap(root, failure(), recorded_at_utc=datetime.now())
    with pytest.raises(EvidenceGateError, match="EVIDENCE_TIMESTAMP_NOT_UTC"):
        persist_failed_bootstrap(root, failure(), recorded_at_utc=datetime.now(timezone(timedelta(hours=7))))


def test_unknown_phase_rejected(tmp_path):
    root = private_dir(tmp_path)
    with pytest.raises(EvidenceGateError, match="EVIDENCE_PHASE_NOT_ALLOWED"):
        persist_failed_bootstrap(root, failure(), phase="DASHBOARD_DEPLOY")


def test_no_launchctl_execution_entrypoint(tmp_path):
    root = private_dir(tmp_path)
    with patch("subprocess.run", side_effect=AssertionError("real subprocess forbidden")):
        result = persist_failed_bootstrap(root, failure())
    assert result.exists()
