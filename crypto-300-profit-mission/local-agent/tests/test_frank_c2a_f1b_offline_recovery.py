"""F1b strictly synthetic recovery; never run live subprocess/launchctl."""
import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.frank_c2a_f1b_offline_recovery import rehearse_failed_bootstrap_recovery


def evidence_directory(tmp_path):
    d = tmp_path / "private"
    d.mkdir(mode=0o700)
    return d


def result(*, rc=5, stdout=b"captured stdout", stderr=b"launch failed"):
    return subprocess.CompletedProcess(
        args=["/bin/launchctl", "bootstrap", "gui/PRIVATE", "/sensitive/launch.plist"],
        returncode=rc, stdout=stdout, stderr=stderr,
    )


def run(outcome, private_dir, *, recorder=None, restore=None, verify=None):
    calls = []
    def restore_spy():
        calls.append("restore")
        if restore is not None:
            restore()
    def verify_spy():
        calls.append("verify")
        return verify() if verify is not None else True
    kwargs = {
        "observation": outcome,
        "private_evidence_dir": private_dir,
        "restore_spy": restore_spy,
        "verify_spy": verify_spy,
    }
    if recorder is not None:
        kwargs["persist_spy"] = recorder
    return rehearse_failed_bootstrap_recovery(**kwargs), calls


def test_normal_capture_really_persisted_before_restore(tmp_path):
    directory = evidence_directory(tmp_path)
    order = []
    def restore_spy():
        record = directory / "first-bootstrap-attempt.json"
        data = json.loads(record.read_text())
        assert data["returncode"] == 37
        assert data["stdout"]["captured_bytes"] > 0
        order.append("restore")
    outcome, calls = run(result(rc=37), directory, restore=restore_spy)
    assert outcome.evidence_status == "RECORDED"
    assert outcome.restore_status == "ROLLBACK_VERIFIED"
    assert outcome.restore_attempts == 1
    assert outcome.verification_attempts == 1
    assert order == ["restore"]
    assert calls == ["restore", "verify"]
    assert "sensitive/launch" not in (directory / "first-bootstrap-attempt.json").read_text()


@pytest.mark.parametrize("stdout,stderr", [
    (None, None), (None, b"failed"), (b"", None), (None, b""), (b"", None),
])
def test_f1_none_capture_fails_but_restore_still_happens(tmp_path, stdout, stderr):
    directory = evidence_directory(tmp_path)
    outcome, calls = run(result(stdout=stdout, stderr=stderr), directory)
    assert outcome.evidence_status == "CAPTURE_FAILED"
    assert outcome.restore_status == "ROLLBACK_VERIFIED"
    assert calls == ["restore", "verify"]
    assert list(directory.iterdir()) == []


@pytest.mark.parametrize("n", [1, 2, 3])
def test_each_fsync_failure_still_restores_once(tmp_path, n):
    directory = evidence_directory(tmp_path)
    real_fsync = os.fsync
    count = [0]
    def fail_nth(fd):
        count[0] += 1
        if count[0] == n:
            raise OSError("synthetic disk/fsync failed")
        return real_fsync(fd)
    with patch("os.fsync", side_effect=fail_nth):
        outcome, calls = run(result(), directory)
    assert outcome.evidence_status == "CAPTURE_FAILED"
    assert outcome.restore_status == "ROLLBACK_VERIFIED"
    assert outcome.restore_attempts == 1
    assert calls == ["restore", "verify"]


def test_full_disk_fails_pre_record_and_restore_proceeds(tmp_path):
    directory = evidence_directory(tmp_path)
    def disk_full(*args, **kwargs):
        raise OSError("synthetic ENOSPC")
    outcome, calls = run(result(), directory, recorder=disk_full)
    assert (outcome.evidence_status, outcome.restore_status) == (
        "CAPTURE_FAILED", "ROLLBACK_VERIFIED"
    )
    assert calls == ["restore", "verify"]


def test_capture_keyboard_interrupt_and_system_exit_do_not_suppress_restore(tmp_path):
    for failure in (KeyboardInterrupt, SystemExit):
        directory = evidence_directory(tmp_path / failure.__name__ if False else tmp_path)
        def interrupted(*args, **kwargs):
            raise failure("SYNTHETIC_INTERRUPTION")
        outcome, calls = run(result(), directory, recorder=interrupted)
        assert outcome.evidence_status == "CAPTURE_FAILED"
        assert calls == ["restore", "verify"]


@pytest.mark.parametrize("failure", [TimeoutError, RuntimeError, KeyboardInterrupt, SystemExit])
def test_restore_fails_no_success_or_retry(tmp_path, failure):
    directory = evidence_directory(tmp_path)
    def broken():
        raise failure("SYNTHETIC_RESTORE_FAILURE")
    outcome, calls = run(result(), directory, restore=broken)
    assert outcome.restore_status == "ROLLBACK_FAILED_STOP"
    assert outcome.restore_attempts == 1
    assert outcome.verification_attempts == 0
    assert calls == ["restore"]


@pytest.mark.parametrize("verification", [False, 0, None, "true"])
def test_verify_must_return_literal_true(tmp_path, verification):
    directory = evidence_directory(tmp_path)
    outcome, calls = run(result(), directory, verify=lambda: verification)
    assert outcome.restore_status == "ROLLBACK_UNVERIFIED_STOP"
    assert calls == ["restore", "verify"]


def test_verification_exception_cannot_claim_restoration(tmp_path):
    directory = evidence_directory(tmp_path)
    def no_verify():
        raise OSError("synthetic health failed")
    outcome, calls = run(result(), directory, verify=no_verify)
    assert outcome.restore_status == "ROLLBACK_UNVERIFIED_STOP"
    assert calls == ["restore", "verify"]


@pytest.mark.parametrize("exc", [
    subprocess.TimeoutExpired(cmd=["FAKE"], timeout=1, output=b"partial", stderr=None),
    RuntimeError("synthetic process death"), KeyboardInterrupt(), SystemExit(),
    None,
])
def test_timeout_or_missing_process_result_restores_without_forging_return_code(tmp_path, exc):
    directory = evidence_directory(tmp_path)
    outcome, calls = run(exc, directory)
    assert outcome.evidence_status in {
        "NO_COMPLETED_RETURN_CODE_TIMEOUT",
        "NO_COMPLETED_RETURN_CODE_EXCEPTION",
        "NO_BOOTSTRAP_RESULT",
    }
    assert outcome.restore_status == "ROLLBACK_VERIFIED"
    assert outcome.recorded_file is None
    assert calls == ["restore", "verify"]
    assert not list(directory.iterdir())


def test_success_completed_process_is_not_recovery_event(tmp_path):
    directory = evidence_directory(tmp_path)
    with pytest.raises(ValueError, match="OFFLINE_NOT_A_FAILED_BOOTSTRAP"):
        run(result(rc=0), directory)
    assert not list(directory.iterdir())


def test_existing_evidence_remains_unchanged_but_restoration_is_independent(tmp_path):
    directory = evidence_directory(tmp_path)
    first, _ = run(result(rc=1), directory)
    assert first.evidence_status == "RECORDED"
    existing = (directory / "first-bootstrap-attempt.json").read_bytes()
    second, calls = run(result(rc=7), directory)
    assert second.evidence_status == "CAPTURE_FAILED"
    assert second.restore_status == "ROLLBACK_VERIFIED"
    assert (directory / "first-bootstrap-attempt.json").read_bytes() == existing
    assert calls == ["restore", "verify"]


def test_no_real_process_or_network_is_ever_needed(tmp_path):
    directory = evidence_directory(tmp_path)
    with patch("subprocess.Popen", side_effect=AssertionError("NO_SPAWN")), \
         patch("subprocess.run", side_effect=AssertionError("NO_RUN")), \
         patch("os.system", side_effect=AssertionError("NO_SHELL")):
        outcome, calls = run(result(), directory)
    assert outcome.restore_status == "ROLLBACK_VERIFIED"
    assert calls == ["restore", "verify"]


def test_no_private_exception_or_stdout_in_non_sensitive_result(tmp_path):
    directory = evidence_directory(tmp_path)
    secret = "rpc-key=EXAMPLE_SECRET"
    def failed(*args, **kwargs):
        raise OSError(secret)
    outcome, calls = run(result(stderr=secret.encode()), directory, recorder=failed)
    assert secret not in str(outcome)
    assert "sensitive" not in str(outcome)
    assert outcome.evidence_status == "CAPTURE_FAILED"
    assert calls == ["restore", "verify"]
