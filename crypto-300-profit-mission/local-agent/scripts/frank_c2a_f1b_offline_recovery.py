"""F1b OFFLINE FAILURE-RECOVERY MODEL. Does not execute commands or change services.

This deliberately separate helper consumes *already obtained* synthetic outcomes and
calls only injected test spies. DO NOT wire this module to a live Dashboard runner.
The purpose is to verify that an inability to save diagnostic evidence never
suppresses the independent, one-shot emergency-recovery attempt.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from scripts.frank_c2a_f1_evidence import persist_failed_bootstrap


@dataclass(frozen=True)
class OfflineRecoveryResult:
    """Non-sensitive verdict; never includes raw argv, stdout or stderr."""

    evidence_status: str
    restore_status: str
    restore_attempts: int
    verification_attempts: int
    recorded_file: Path | None = None  # PRIVATE on local fixture only; never upload


def rehearse_failed_bootstrap_recovery(
    *,
    observation: subprocess.CompletedProcess | BaseException | None,
    private_evidence_dir: Path,
    restore_spy: Callable[[], None],
    verify_spy: Callable[[], bool],
    persist_spy: Callable[..., Path] = persist_failed_bootstrap,
) -> OfflineRecoveryResult:
    """Exercise one failure => independent single restore => strict verify.

    Every spy is a caller-supplied SYNTHETIC function, NEVER launchctl.
    A known returncode==0 is not a failed bootstrap; do not call recovery spies.
    All other outcomes represent a possibly interrupted/failed attempt.
    Evidence failure is recorded separately and may not prevent restoration.
    This cannot recover from SIGKILL, power loss, or a crash outside this process.
    """
    if (isinstance(observation, subprocess.CompletedProcess)
            and type(observation.returncode) is int and observation.returncode == 0):
        raise ValueError("OFFLINE_NOT_A_FAILED_BOOTSTRAP")

    evidence_status = "NOT_CAPTURED"
    recorded_file = None
    attempts = 0
    checked = 0

    try:
        if isinstance(observation, subprocess.CompletedProcess):
            try:
                recorded_file = persist_spy(private_evidence_dir, observation)
                if not isinstance(recorded_file, Path):
                    raise TypeError("INVALID_EVIDENCE_RECEIPT")
                evidence_status = "RECORDED"
            except BaseException:
                # No exception data in verdict: it may contain private stderr,
                # local paths or credentials. Restoration must still be tried.
                evidence_status = "CAPTURE_FAILED"
                recorded_file = None
        elif isinstance(observation, subprocess.TimeoutExpired):
            # TimeoutExpired may contain output but has no completed return code.
            # Do not forge a CompletedProcess(returncode=1) or claim full evidence.
            evidence_status = "NO_COMPLETED_RETURN_CODE_TIMEOUT"
        elif observation is None:
            evidence_status = "NO_BOOTSTRAP_RESULT"
        elif isinstance(observation, BaseException):
            evidence_status = "NO_COMPLETED_RETURN_CODE_EXCEPTION"
        else:
            evidence_status = "UNSUPPORTED_OBSERVATION"

    finally:
        # Independent of the entire capture branch, including disk/full fsync,
        # EVIDENCE_STREAM_NOT_CAPTURED, KeyboardInterrupt and SystemExit.
        attempts += 1
        try:
            restore_spy()
        except BaseException:
            # Do not mask failed restoration as success or auto-retry.
            return OfflineRecoveryResult(
                evidence_status, "ROLLBACK_FAILED_STOP", attempts, checked, recorded_file
            )

    checked += 1
    try:
        verified = verify_spy()
    except BaseException:
        return OfflineRecoveryResult(
            evidence_status, "ROLLBACK_UNVERIFIED_STOP", attempts, checked, recorded_file
        )
    if verified is not True:
        return OfflineRecoveryResult(
            evidence_status, "ROLLBACK_UNVERIFIED_STOP", attempts, checked, recorded_file
        )
    return OfflineRecoveryResult(
        evidence_status, "ROLLBACK_VERIFIED", attempts, checked, recorded_file
    )
