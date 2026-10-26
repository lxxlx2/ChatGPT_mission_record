"""F1c synthetic-only Dashboard release state machine — NO production command runner.

All stage events are pre-supplied fixture data. No subprocess execution, HTTP,
launchctl, or modification to Dashboard runner, plist, DB, policy or service.
The only write possible is an F1 private *test fixture* evidence record for a
synthetic nonzero bootstrap. Never point evidence_dir at production or reuse
this state machine as a real Dashboard deployment interface.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from scripts.frank_c2a_f1b_offline_recovery import rehearse_failed_bootstrap_recovery


OLD_SOURCE_SHA = "914e9e47fed2e60bc24690fcb083413a64d4e681"
REVIEWED_C1_SHA = "4fdf2238a4db2347975689913e49142b760dc091"
LOOPBACK = "127.0.0.1:8766"
_HEX64 = re.compile(r"[a-f0-9]{64}\Z")


@dataclass(frozen=True)
class Protected:
    """Already-redacted fixture identities, never raw paths, tokens or payloads."""

    loop_fingerprint: str
    v1_fingerprint: str
    notification_fingerprint: str
    d2_whole_file_sha256: str
    other_listeners_fingerprint: str


@dataclass(frozen=True)
class Runtime:
    dashboard_source_sha: str
    manifest_sha256: str
    runner_sha256: str
    dashboard_listener: str
    dashboard_healthy: bool
    protected: Protected


@dataclass(frozen=True)
class Pins:
    old_manifest_sha256: str
    new_manifest_sha256: str
    old_runner_sha256: str
    new_runner_sha256: str


@dataclass(frozen=True)
class Fixture:
    """Inert release scenario; all fields are precomputed, never probes."""

    old_before: Runtime
    old_before_switch: Runtime
    candidate_manifest_verified: bool
    candidate_import_verified: bool
    exactly_one_runner_source_line: bool
    bootout_completed: bool
    bootstrap_outcome: subprocess.CompletedProcess | BaseException | None
    candidate_after: Runtime | None
    # Independent FINAL protection observation supplied after G3 GET/browser checks.
    # This must not be inferred from candidate_after or old_before_switch.
    protected_after_g3: Protected | None
    legacy_get_pass: bool
    d2_get_pass: bool
    chrome_readonly_pass: bool
    rollback_operation_ok: bool
    old_after_rollback: Runtime | None


@dataclass(frozen=True)
class FixtureVerdict:
    status: str
    failed_gate: str | None
    evidence_status: str
    simulated_switches: int
    simulated_restores: int
    simulated_verifies: int
    gates_passed: tuple[str, ...]
    # Never return raw output, command arguments, full runtime or private path.


def _hash(value: str) -> bool:
    return isinstance(value, str) and bool(_HEX64.fullmatch(value))


def _runtime_matches(runtime: Runtime | None, sha: str, manifest: str, runner: str) -> bool:
    return bool(
        runtime is not None
        and runtime.dashboard_source_sha == sha
        and runtime.manifest_sha256 == manifest
        and runtime.runner_sha256 == runner
        and runtime.dashboard_listener == LOOPBACK
        and runtime.dashboard_healthy is True
    )


def _pins_valid(pins: Pins) -> bool:
    return all(_hash(x) for x in (
        pins.old_manifest_sha256, pins.new_manifest_sha256,
        pins.old_runner_sha256, pins.new_runner_sha256,
    )) and pins.old_manifest_sha256 != pins.new_manifest_sha256 and (
        pins.old_runner_sha256 != pins.new_runner_sha256
    )


def rehearse_release(
    pins: Pins,
    scenario: Fixture,
    *,
    evidence_dir: Path,
) -> FixtureVerdict:
    """G0/G1/G2/G3/G4 with one independent synthetic rollback after any G2 risk.

    A reported PASS is ONLY "FIXTURE_RELEASE_PASS", never a production verdict.
    The given snapshot booleans/digests are synthetic assertions and are not
    actual Mac/launchd/HTTP or filesystem measurements.
    """
    gates: list[str] = []

    def output(status: str, gate: str | None, evidence: str = "NOT_APPLICABLE",
               switches: int = 0, restores: int = 0, verifies: int = 0) -> FixtureVerdict:
        return FixtureVerdict(status, gate, evidence, switches, restores, verifies, tuple(gates))

    old = scenario.old_before
    if not _pins_valid(pins) or not _runtime_matches(
        old, OLD_SOURCE_SHA, pins.old_manifest_sha256, pins.old_runner_sha256
    ):
        return output("FIXTURE_BLOCKED_NO_CHANGE", "G0")
    if not _hash(old.protected.d2_whole_file_sha256) or not all((
        old.protected.loop_fingerprint, old.protected.v1_fingerprint,
        old.protected.notification_fingerprint, old.protected.other_listeners_fingerprint,
    )):
        return output("FIXTURE_BLOCKED_NO_CHANGE", "G0_PROTECTED")
    gates.append("G0")

    if (scenario.candidate_manifest_verified is not True
            or scenario.candidate_import_verified is not True
            or scenario.exactly_one_runner_source_line is not True):
        return output("FIXTURE_BLOCKED_NO_CHANGE", "G1")
    gates.append("G1")

    if scenario.old_before_switch != old:
        return output("FIXTURE_BLOCKED_NO_CHANGE", "G2_RECHECK")
    gates.append("G2_RECHECK")

    def old_restored() -> bool:
        return bool(
            _runtime_matches(
                scenario.old_after_rollback, OLD_SOURCE_SHA,
                pins.old_manifest_sha256, pins.old_runner_sha256,
            ) and scenario.old_after_rollback.protected == old.protected
        )

    def restore_failure(failed_gate: str, observation: subprocess.CompletedProcess |
                        BaseException | None) -> FixtureVerdict:
        # Synthetic "switches" is ONE intended cutover gate, not actual
        # launchctl calls, and this is *not* a physical fallback mechanism.
        call_count = [0]

        def fake_restore() -> None:
            call_count[0] += 1
            if scenario.rollback_operation_ok is not True:
                raise RuntimeError("SYNTHETIC_ROLLBACK_FAILED")

        def fake_verify() -> bool:
            return old_restored()

        result = rehearse_failed_bootstrap_recovery(
            observation=observation, private_evidence_dir=evidence_dir,
            restore_spy=fake_restore, verify_spy=fake_verify,
        )
        status = {
            "ROLLBACK_VERIFIED": "FIXTURE_ROLLED_BACK",
            "ROLLBACK_FAILED_STOP": "FIXTURE_ROLLBACK_FAILED_STOP",
            "ROLLBACK_UNVERIFIED_STOP": "FIXTURE_ROLLBACK_UNVERIFIED_STOP",
        }[result.restore_status]
        return output(
            status, failed_gate, result.evidence_status,
            switches=1, restores=call_count[0], verifies=result.verification_attempts,
        )

    if scenario.bootout_completed is not True:
        # A bootout *attempt* could have partially changed the service state.
        return restore_failure("G2_BOOTOUT", None)
    gates.append("G2_BOOTOUT")

    outcome = scenario.bootstrap_outcome
    if not (isinstance(outcome, subprocess.CompletedProcess)
            and type(outcome.returncode) is int and outcome.returncode == 0):
        return restore_failure("G2_BOOTSTRAP", outcome)
    gates.append("G2_BOOTSTRAP")

    if (not _runtime_matches(
            scenario.candidate_after, REVIEWED_C1_SHA,
            pins.new_manifest_sha256, pins.new_runner_sha256,
        ) or scenario.candidate_after.protected != old.protected):
        return restore_failure("G3_RUNTIME_OR_PROTECTED", None)
    if (scenario.legacy_get_pass is not True
            or scenario.d2_get_pass is not True
            or scenario.chrome_readonly_pass is not True):
        return restore_failure("G3_GET_OR_BROWSER", None)
    gates.append("G3")
    # G4 uses its OWN later synthetic observation; comparing the G3 value again
    # would be tautological after G2_RECHECK and G3_RUNTIME_OR_PROTECTED.
    # Missing or changed closing-state data is fail-closed even if G3 passed.
    if (scenario.protected_after_g3 is None
            or scenario.protected_after_g3 != old.protected):
        return restore_failure("G4_PROTECTED", None)
    gates.append("G4")

    return output("FIXTURE_RELEASE_PASS", None, switches=1)
