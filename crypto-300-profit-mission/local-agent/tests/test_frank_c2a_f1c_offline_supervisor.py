"""Synthetic F1c release gates; no Mac runner, launchctl, network or production IO."""
from dataclasses import replace
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.frank_c2a_f1c_offline_supervisor import (
    LOOPBACK, OLD_SOURCE_SHA, REVIEWED_C1_SHA, Fixture, Pins, Protected, Runtime,
    rehearse_release,
)


def fixture(tmp_path):
    private = tmp_path / "private"
    private.mkdir(mode=0o700)
    pins = Pins(
        old_manifest_sha256="a"*64, new_manifest_sha256="b"*64,
        old_runner_sha256="c"*64, new_runner_sha256="d"*64,
    )
    protected = Protected(
        loop_fingerprint="LOOP_SAME", v1_fingerprint="V1_SAME",
        notification_fingerprint="NO_SEND", d2_whole_file_sha256="e"*64,
        other_listeners_fingerprint="OTHERS_SAME",
    )
    old = Runtime(OLD_SOURCE_SHA, pins.old_manifest_sha256,
                  pins.old_runner_sha256, LOOPBACK, True, protected)
    new = Runtime(REVIEWED_C1_SHA, pins.new_manifest_sha256,
                  pins.new_runner_sha256, LOOPBACK, True, protected)
    case = Fixture(
        old_before=old, old_before_switch=old,
        candidate_manifest_verified=True, candidate_import_verified=True,
        exactly_one_runner_source_line=True, bootout_completed=True,
        bootstrap_outcome=subprocess.CompletedProcess(
            ["SYNTHETIC_BOOTSTRAP"], 0, stdout=b"", stderr=b"",
        ),
        candidate_after=new,
        protected_after_g3=replace(protected),  # later, independently supplied snapshot
        legacy_get_pass=True, d2_get_pass=True,
        chrome_readonly_pass=True, rollback_operation_ok=True,
        old_after_rollback=old,
    )
    return pins, case, private


def run(tmp_path, modify=None):
    pins, case, private = fixture(tmp_path)
    if modify:
        pins, case = modify(pins, case)
    return rehearse_release(pins, case, evidence_dir=private), private


def test_complete_synthetic_release_pass_never_creates_evidence(tmp_path):
    res, private = run(tmp_path)
    assert res.status == "FIXTURE_RELEASE_PASS"
    assert res.gates_passed == (
        "G0", "G1", "G2_RECHECK", "G2_BOOTOUT", "G2_BOOTSTRAP", "G3", "G4",
    )
    assert (res.simulated_switches, res.simulated_restores, res.simulated_verifies) == (1, 0, 0)
    assert not list(private.iterdir())


@pytest.mark.parametrize("change", [
    lambda p, c: (p, replace(c, old_before=replace(c.old_before, dashboard_source_sha=REVIEWED_C1_SHA))),
    lambda p, c: (p, replace(c, old_before=replace(c.old_before, dashboard_listener="0.0.0.0:8766"))),
    lambda p, c: (p, replace(c, old_before=replace(c.old_before, dashboard_healthy=False))),
    lambda p, c: (replace(p, old_manifest_sha256="bad"), c),
    lambda p, c: (replace(p, new_manifest_sha256=p.old_manifest_sha256), c),
    lambda p, c: (replace(p, new_runner_sha256=p.old_runner_sha256), c),
    lambda p, c: (p, replace(c, old_before=replace(c.old_before,
        protected=replace(c.old_before.protected, d2_whole_file_sha256="bad")))),
    lambda p, c: (p, replace(c, old_before=replace(c.old_before,
        protected=replace(c.old_before.protected, loop_fingerprint="")))),
])
def test_g0_drift_prevents_any_mutation(tmp_path, change):
    res, private = run(tmp_path, change)
    assert res.status == "FIXTURE_BLOCKED_NO_CHANGE"
    assert res.failed_gate in {"G0", "G0_PROTECTED"}
    assert res.simulated_switches == res.simulated_restores == 0
    assert not list(private.iterdir())


@pytest.mark.parametrize("field", [
    "candidate_manifest_verified", "candidate_import_verified",
    "exactly_one_runner_source_line",
])
def test_g1_failure_has_no_switch_or_rollback(tmp_path, field):
    res, private = run(tmp_path, lambda p, c: (p, replace(c, **{field: False})))
    assert res.status == "FIXTURE_BLOCKED_NO_CHANGE"
    assert res.failed_gate == "G1"
    assert res.simulated_switches == res.simulated_restores == 0
    assert not list(private.iterdir())


def test_pre_switch_runtime_drift_blocks_without_cutover(tmp_path):
    res, _ = run(tmp_path, lambda p, c: (
        p, replace(c, old_before_switch=replace(c.old_before, runner_sha256="f"*64)),
    ))
    assert res.status == "FIXTURE_BLOCKED_NO_CHANGE"
    assert res.failed_gate == "G2_RECHECK"
    assert res.simulated_restores == res.simulated_switches == 0


def test_bootout_error_must_attempt_one_rollback(tmp_path):
    res, _ = run(tmp_path, lambda p, c: (p, replace(c, bootout_completed=False)))
    assert res.status == "FIXTURE_ROLLED_BACK"
    assert res.failed_gate == "G2_BOOTOUT"
    assert res.evidence_status == "NO_BOOTSTRAP_RESULT"
    assert (res.simulated_switches, res.simulated_restores, res.simulated_verifies) == (1, 1, 1)


def test_failed_bootstrap_records_error_before_rollback(tmp_path):
    failed = subprocess.CompletedProcess(
        ["FAKE_SUBPROCESS_ONLY", "/PRIVATE/launcher"], returncode=37,
        stdout=b"output", stderr=b"\x00synthetic error\xff",
    )
    res, private = run(tmp_path, lambda p, c: (p, replace(c, bootstrap_outcome=failed)))
    assert res.status == "FIXTURE_ROLLED_BACK"
    assert res.failed_gate == "G2_BOOTSTRAP"
    assert res.evidence_status == "RECORDED"
    assert (res.simulated_switches, res.simulated_restores, res.simulated_verifies) == (1, 1, 1)
    report = (private / "first-bootstrap-attempt.json").read_text()
    assert '"returncode":37' in report
    assert "PRIVATE/launcher" not in report
    assert "synthetic error" not in str(res)


@pytest.mark.parametrize("result", [
    subprocess.CompletedProcess(["FAKE"], 9, stdout=None, stderr=None),
    subprocess.CompletedProcess(["FAKE"], 9, stdout=b"", stderr=None),
    subprocess.CompletedProcess(["FAKE"], None, stdout=b"", stderr=b""),
    subprocess.TimeoutExpired(["FAKE"], 3, output=b"partial", stderr=None),
    KeyboardInterrupt(),
    SystemExit(),
    None,
])
def test_missing_or_interrupted_bootstrap_never_blocks_restore(tmp_path, result):
    res, _ = run(tmp_path, lambda p, c: (p, replace(c, bootstrap_outcome=result)))
    assert res.status == "FIXTURE_ROLLED_BACK"
    assert res.failed_gate == "G2_BOOTSTRAP"
    assert res.simulated_restores == res.simulated_verifies == 1


@pytest.mark.parametrize("change", [
    lambda c: replace(c, candidate_after=replace(c.candidate_after, dashboard_source_sha=OLD_SOURCE_SHA)),
    lambda c: replace(c, candidate_after=replace(c.candidate_after, manifest_sha256="a"*64)),
    lambda c: replace(c, candidate_after=replace(c.candidate_after, runner_sha256="a"*64)),
    lambda c: replace(c, candidate_after=replace(c.candidate_after, dashboard_listener="127.0.0.1:9999")),
    lambda c: replace(c, candidate_after=replace(c.candidate_after, dashboard_healthy=False)),
    lambda c: replace(c, candidate_after=replace(c.candidate_after,
        protected=replace(c.candidate_after.protected, loop_fingerprint="ALTERED"))),
    lambda c: replace(c, candidate_after=None),
])
def test_g3_new_runtime_or_protected_drift_causes_one_rollback(tmp_path, change):
    res, _ = run(tmp_path, lambda p, c: (p, change(c)))
    assert res.status == "FIXTURE_ROLLED_BACK"
    assert res.failed_gate == "G3_RUNTIME_OR_PROTECTED"
    assert (res.simulated_switches, res.simulated_restores, res.simulated_verifies) == (1, 1, 1)


@pytest.mark.parametrize("field", ["legacy_get_pass", "d2_get_pass", "chrome_readonly_pass"])
def test_g3_get_or_real_browser_claim_missing_causes_rollback(tmp_path, field):
    res, _ = run(tmp_path, lambda p, c: (p, replace(c, **{field: False})))
    assert res.status == "FIXTURE_ROLLED_BACK"
    assert res.failed_gate == "G3_GET_OR_BROWSER"
    assert res.simulated_restores == 1


@pytest.mark.parametrize("after", [
    lambda c: replace(c.old_after_rollback, dashboard_source_sha=REVIEWED_C1_SHA),
    lambda c: replace(c.old_after_rollback, manifest_sha256="f"*64),
    lambda c: replace(c.old_after_rollback, dashboard_listener="127.0.0.1:1111"),
    lambda c: replace(c.old_after_rollback, dashboard_healthy=False),
    lambda c: replace(c.old_after_rollback, protected=replace(c.old_after_rollback.protected,
        notification_fingerprint="WRONG")),
    lambda c: None,
])
def test_rollback_readback_mismatch_must_report_unverified(tmp_path, after):
    res, _ = run(tmp_path, lambda p, c: (p, replace(
        c, legacy_get_pass=False, old_after_rollback=after(c),
    )))
    assert res.status == "FIXTURE_ROLLBACK_UNVERIFIED_STOP"
    assert res.failed_gate == "G3_GET_OR_BROWSER"
    assert (res.simulated_restores, res.simulated_verifies) == (1, 1)


def test_rollback_operation_failure_no_second_attempt_or_false_success(tmp_path):
    res, _ = run(tmp_path, lambda p, c: (
        p, replace(c, legacy_get_pass=False, rollback_operation_ok=False),
    ))
    assert res.status == "FIXTURE_ROLLBACK_FAILED_STOP"
    assert (res.simulated_restores, res.simulated_verifies) == (1, 0)


def test_never_runs_real_child_or_network_or_launchctl(tmp_path):
    pins, case, private = fixture(tmp_path)
    # This is a PURE fixture. The evidence writer is used only for failed
    # synthetic commands, not production service state.
    with patch("subprocess.Popen", side_effect=AssertionError("NO_SPAWN")), \
         patch("subprocess.run", side_effect=AssertionError("NO_RUN")), \
         patch("os.system", side_effect=AssertionError("NO_SHELL")):
        res = rehearse_release(pins, case, evidence_dir=private)
    assert res.status == "FIXTURE_RELEASE_PASS"



@pytest.mark.parametrize("field,new_value", [
    ("loop_fingerprint", "LOOP_CHANGED_ONLY_AT_G4"),
    ("v1_fingerprint", "V1_CHANGED_ONLY_AT_G4"),
    ("notification_fingerprint", "NOTIFICATIONS_CHANGED_ONLY_AT_G4"),
    ("d2_whole_file_sha256", "f"*64),
    ("other_listeners_fingerprint", "PORTS_CHANGED_ONLY_AT_G4"),
])
def test_g3_pass_but_independent_g4_protected_drift_rolls_back_once(
    tmp_path, field, new_value,
):
    def only_final_snapshot_changes(pins, case):
        final = replace(case.protected_after_g3, **{field: new_value})
        assert case.candidate_after.protected == case.old_before.protected
        return pins, replace(case, protected_after_g3=final)

    verdict, private = run(tmp_path, only_final_snapshot_changes)
    assert verdict.failed_gate == "G4_PROTECTED"
    assert verdict.status == "FIXTURE_ROLLED_BACK"
    assert "G3" in verdict.gates_passed
    assert "G4" not in verdict.gates_passed
    assert verdict.evidence_status == "NO_BOOTSTRAP_RESULT"
    assert (verdict.simulated_switches, verdict.simulated_restores,
            verdict.simulated_verifies) == (1, 1, 1)
    assert not list(private.iterdir())  # No fabricated failing-bootstrap record.


def test_g4_final_observation_missing_fails_closed_and_restores_once(tmp_path):
    verdict, private = run(
        tmp_path, lambda p, c: (p, replace(c, protected_after_g3=None)),
    )
    assert verdict.status == "FIXTURE_ROLLED_BACK"
    assert verdict.failed_gate == "G4_PROTECTED"
    assert "G3" in verdict.gates_passed
    assert "G4" not in verdict.gates_passed
    assert (verdict.simulated_restores, verdict.simulated_verifies) == (1, 1)
    assert not list(private.iterdir())


def test_distinct_unchanged_final_snapshot_allows_g4_pass(tmp_path):
    pins, case, private = fixture(tmp_path)
    assert case.protected_after_g3 == case.candidate_after.protected
    assert case.protected_after_g3 is not case.candidate_after.protected
    verdict = rehearse_release(pins, case, evidence_dir=private)
    assert verdict.status == "FIXTURE_RELEASE_PASS"
    assert verdict.failed_gate is None
    assert verdict.gates_passed[-2:] == ("G3", "G4")
    assert verdict.simulated_restores == 0


def test_g4_drift_with_bad_old_runner_fails_rollback_verification(tmp_path):
    def damaged_rollback(pins, case):
        return pins, replace(
            case,
            protected_after_g3=replace(
                case.protected_after_g3, notification_fingerprint="CHANGED_AFTER_G3",
            ),
            old_after_rollback=replace(
                case.old_after_rollback, runner_sha256="f"*64,
            ),
        )
    verdict, _ = run(tmp_path, damaged_rollback)
    assert verdict.failed_gate == "G4_PROTECTED"
    assert verdict.status == "FIXTURE_ROLLBACK_UNVERIFIED_STOP"
    assert verdict.simulated_restores == 1
    assert verdict.simulated_verifies == 1


def test_g4_drift_restore_action_failure_never_retries(tmp_path):
    def failed_restore(pins, case):
        return pins, replace(
            case, protected_after_g3=replace(
                case.protected_after_g3, d2_whole_file_sha256="f"*64,
            ), rollback_operation_ok=False,
        )
    verdict, _ = run(tmp_path, failed_restore)
    assert verdict.failed_gate == "G4_PROTECTED"
    assert verdict.status == "FIXTURE_ROLLBACK_FAILED_STOP"
    assert verdict.simulated_restores == 1
    assert verdict.simulated_verifies == 0


def test_g3_failure_does_not_fabricate_bootstrap_stderr(tmp_path):
    res, private = run(tmp_path, lambda p, c: (p, replace(c, d2_get_pass=False)))
    assert res.status == "FIXTURE_ROLLED_BACK"
    assert res.evidence_status == "NO_BOOTSTRAP_RESULT"
    assert not list(private.iterdir())
