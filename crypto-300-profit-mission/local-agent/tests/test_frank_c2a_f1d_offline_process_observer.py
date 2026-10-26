"""F1d bounded inert process observation tests; no real child or network."""
import json
import os
from unittest.mock import patch

import pytest

from scripts.frank_c2a_f1d_offline_process_observer import (
    ChildExit, DeadlineReached, Interrupted, PipeData, PipeEOF,
    DEADLINE_MS, MAX_EVENTS, MAX_EVENT_BYTES, MAX_STREAM_BYTES,
    observe_synthetic_stream, safe_status, to_f1_failed_result,
)
from scripts.frank_c2a_f1b_offline_recovery import rehearse_failed_bootstrap_recovery


def complete(rc=13, stdout=b"", stderr=b""):
    return [
        PipeData(0, "stdout", stdout),
        PipeData(1, "stderr", stderr),
        ChildExit(2, rc),
        PipeEOF(3, "stdout"),
        PipeEOF(4, "stderr"),
    ]


def private_dir(tmp_path):
    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    return folder


def test_fully_captured_failed_result_preserves_real_binary_bytes():
    out = observe_synthetic_stream(complete(
        rc=37, stdout=b"head\x00\xff", stderr=b"bad\xf0\x00",
    ))
    assert out.status == "COMPLETE_FAILURE"
    assert (out.returncode, out.stdout, out.stderr) == (37, b"head\x00\xff", b"bad\xf0\x00")
    assert out.stdout_eof and out.stderr_eof
    actual = to_f1_failed_result(out)
    assert (actual.returncode, actual.stdout, actual.stderr) == (
        37, b"head\x00\xff", b"bad\xf0\x00",
    )
    assert actual.args == ["SYNTHETIC_DASHBOARD_BOOTSTRAP_ONLY"]


def test_capture_order_exit_can_follow_both_eofs():
    result = observe_synthetic_stream([
        PipeEOF(0, "stderr"), PipeEOF(1, "stdout"), ChildExit(2, -9),
    ])
    assert result.status == "COMPLETE_FAILURE"
    assert result.returncode == -9


def test_exactly_empty_captured_streams_are_not_uncaptured(tmp_path):
    out = observe_synthetic_stream(complete(rc=7))
    assert out.status == "COMPLETE_FAILURE"
    assert out.stdout_eof and out.stderr_eof
    completed = to_f1_failed_result(out)
    assert completed.stdout == b"" and completed.stderr == b""


def test_f1_evidence_and_f1b_mock_restore_only_after_complete_capture(tmp_path):
    out = observe_synthetic_stream(complete(rc=13, stderr=b"synthetic diagnostic"))
    directory = private_dir(tmp_path)
    calls = []

    def restore():
        assert (directory / "first-bootstrap-attempt.json").is_file()
        data = json.loads((directory / "first-bootstrap-attempt.json").read_text())
        assert data["returncode"] == 13
        assert data["stderr"]["captured_bytes"] == len(b"synthetic diagnostic")
        calls.append("restore")

    def verify():
        calls.append("verify")
        return True

    with patch("subprocess.Popen", side_effect=AssertionError("NO_PROCESS")), \
         patch("subprocess.run", side_effect=AssertionError("NO_RUN")):
        result = rehearse_failed_bootstrap_recovery(
            observation=to_f1_failed_result(out),
            private_evidence_dir=directory,
            restore_spy=restore,
            verify_spy=verify,
        )
    assert (result.evidence_status, result.restore_status) == (
        "RECORDED", "ROLLBACK_VERIFIED",
    )
    assert calls == ["restore", "verify"]


def test_truncated_capture_is_not_treated_as_complete_f1_data(tmp_path):
    sequence = [
        PipeData(1, "stdout", b"A" * MAX_EVENT_BYTES),
        PipeData(2, "stdout", b"A" * MAX_EVENT_BYTES),
        PipeData(3, "stdout", b"EXTRA"),
    ]
    out = observe_synthetic_stream(sequence)
    assert out.status == "STREAM_BUDGET_EXCEEDED"
    assert len(out.stdout) == MAX_STREAM_BYTES
    assert out.stdout_eof is False
    with pytest.raises(ValueError, match="F1D_COMPLETE_FAILURE_REQUIRED"):
        to_f1_failed_result(out)
    directory = private_dir(tmp_path)
    calls = []
    # F1b receives NO result, not a forged CompletedProcess of partial bytes.
    fallback = rehearse_failed_bootstrap_recovery(
        observation=None, private_evidence_dir=directory,
        restore_spy=lambda: calls.append("restore"),
        verify_spy=lambda: calls.append("verify") or True,
    )
    assert fallback.evidence_status == "NO_BOOTSTRAP_RESULT"
    assert fallback.restore_status == "ROLLBACK_VERIFIED"
    assert calls == ["restore", "verify"]
    assert not list(directory.iterdir())


@pytest.mark.parametrize("sequence,expected", [
    ([PipeData(1, "stdout", b"x"), ChildExit(2, 5), PipeEOF(3, "stdout")], "INCOMPLETE_PIPE_CAPTURE"),
    ([PipeEOF(1, "stdout"), PipeEOF(2, "stderr")], "MISSING_EXIT"),
    ([ChildExit(1, 7)], "INCOMPLETE_PIPE_CAPTURE"),
    ([PipeEOF(1, "stderr"), PipeEOF(2, "stdout"), ChildExit(3, 0)], "COMPLETE_SUCCESS"),
    ([DeadlineReached(1)], "DEADLINE_REACHED"),
    ([Interrupted(1)], "INTERRUPTED"),
    ([PipeData(DEADLINE_MS + 1, "stdout", b"x")], "DEADLINE_EXCEEDED"),
    ([PipeData(1, "stdout", b"x"), PipeData(0, "stderr", b"y")], "INVALID_EVENT_CLOCK"),
    ([PipeData(True, "stdout", b"x")], "INVALID_EVENT_CLOCK"),
    ([PipeData(-1, "stdout", b"x")], "INVALID_EVENT_CLOCK"),
    ([PipeData(1, "foo", b"")], "INVALID_PIPE_DATA"),
    ([PipeData(1, "stdout", "not-bytes")], "INVALID_PIPE_DATA"),
    ([PipeData(1, "stdout", b"x" * (MAX_EVENT_BYTES + 1))], "CHUNK_BUDGET_EXCEEDED"),
    ([PipeEOF(1, "bad")], "INVALID_PIPE_EOF"),
    ([PipeEOF(1, "stdout"), PipeEOF(2, "stdout")], "DUPLICATE_EOF"),
    ([PipeEOF(1, "stdout"), PipeData(2, "stdout", b"x")], "DATA_AFTER_EOF"),
    ([ChildExit(1, 8), ChildExit(2, 9)], "INVALID_CHILD_EXIT"),
    ([ChildExit(1, True)], "INVALID_CHILD_EXIT"),
    ([ChildExit(1, "8")], "INVALID_CHILD_EXIT"),
    (complete(rc=0) + [PipeData(5, "stdout", b"late")], "INVALID_TRAILING_EVENT"),
    ([object()], "INVALID_EVENT"),
    ([], "MISSING_EXIT"),
])
def test_bad_or_partial_events_fail_closed(sequence, expected):
    result = observe_synthetic_stream(sequence)
    assert result.status == expected
    if expected != "COMPLETE_SUCCESS":
        with pytest.raises(ValueError, match="F1D_COMPLETE_FAILURE_REQUIRED"):
            to_f1_failed_result(result)


def test_max_events_are_bounded_even_if_input_is_unbounded():
    def infinite():
        step = 0
        while True:
            yield PipeData(0, "stdout", b"")
            step += 1
    result = observe_synthetic_stream(infinite())
    assert result.status == "EVENT_BUDGET_EXCEEDED"
    assert result.events_seen == MAX_EVENTS + 1
    assert result.stdout == b""


def test_both_streams_at_exact_ceiling_are_accepted():
    events = [
        PipeData(0, "stdout", b"A" * MAX_EVENT_BYTES),
        PipeData(1, "stdout", b"A" * MAX_EVENT_BYTES),
        PipeData(2, "stderr", b"B" * MAX_EVENT_BYTES),
        PipeData(3, "stderr", b"B" * MAX_EVENT_BYTES),
        PipeEOF(4, "stdout"), PipeEOF(5, "stderr"), ChildExit(6, 42),
    ]
    result = observe_synthetic_stream(events)
    assert result.status == "COMPLETE_FAILURE"
    assert len(result.stdout) == MAX_STREAM_BYTES
    assert len(result.stderr) == MAX_STREAM_BYTES
    assert to_f1_failed_result(result).returncode == 42


def test_only_one_stream_exceeding_budget_is_explicitly_truncated():
    result = observe_synthetic_stream([
        PipeData(0, "stderr", b"B" * MAX_EVENT_BYTES),
        PipeData(1, "stderr", b"B" * MAX_EVENT_BYTES),
        PipeData(2, "stderr", b"C"),
    ])
    assert result.status == "STREAM_BUDGET_EXCEEDED"
    assert len(result.stderr) == MAX_STREAM_BYTES
    assert result.returncode is None
    assert not result.stderr_eof


def test_terminal_clock_cannot_revert():
    result = observe_synthetic_stream(complete(5) + [DeadlineReached(0)])
    assert result.status == "INVALID_EVENT_CLOCK"
    with pytest.raises(ValueError):
        to_f1_failed_result(result)


def test_safe_status_has_no_secrets_or_raw_payload():
    secret = b"rpc-key=PRIVATE_CREDENTIAL"
    observed = observe_synthetic_stream(complete(rc=8, stderr=secret))
    summary = safe_status(observed)
    assert summary["phase"] == "DASHBOARD_BOOTSTRAP"
    assert summary["status"] == "COMPLETE_FAILURE"
    assert summary["returncode_known"] is True
    assert summary["output_bytes_published"] is False
    assert secret.decode() not in str(summary)
    assert "stdout" not in str(summary)


def test_no_actual_service_or_network_execution(tmp_path):
    with patch("subprocess.run", side_effect=AssertionError("NO_RUN")), \
         patch("subprocess.Popen", side_effect=AssertionError("NO_SPAWN")), \
         patch("os.system", side_effect=AssertionError("NO_SHELL")):
        result = observe_synthetic_stream(complete(rc=17, stderr=b"diagnostics"))
        converted = to_f1_failed_result(result)
        summary = safe_status(result)
    assert converted.returncode == 17
    assert summary["production_probe"] is False
