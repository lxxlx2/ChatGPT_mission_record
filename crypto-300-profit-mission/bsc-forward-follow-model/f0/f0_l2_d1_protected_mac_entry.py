#!/usr/bin/env python3
"""F0 supervised Mac entry: exact-release review-only preflight, NO live send.

Narrow purpose: identify the actual immutable checkout/imported bytes, validate
the *candidate* read-only one-use permit scope, and report the fixed registry
boundary to Codex. This does not treat an operator-supplied permit/manifest as
authorization. Real D2 approval and a separately explicit D3 run remain absent.

All executable entrypoints in this SHA deny actual BSC RPC/WS *before* creating
a grant-consumption marker or an HTTPSConnection. No key/signature is issued.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import importlib
import json
import os
import pwd
from pathlib import Path
import platform
import stat
import sys

from f0_l2_d1_bundle import _strict_permit
from f0_l2_d1_grant import PRIVATE_FIXED_REGISTRY
from f0_l2_d1_mac_provenance import (
    CRITICAL_MODULES, review_loaded_runtime_offline,
)
from f0_l2_d1_preflight import validate_window_contract


# This release has neither D2 exact permit nor D3 explicit execution approval.
# These are NOT flags supplied by an environment variable, permit or CLI.
_D2_REVIEWED_PERMIT_SHA256 = None
_D3_REVIEWED_EXECUTION_RECORD_SHA256 = None
_REAL_SENDER_RELEASED = False

OFFLINE_REPORT_SCHEMA = "f0-d1-mac-supervised-preflight-NO-LIVE-v1"


def _private_directory(path: Path, *, allow_missing=False):
    if (not isinstance(path, Path) or not path.is_absolute()
            or path.is_symlink()):
        raise ValueError("D1_MAC_PRIVATE_DIRECTORY_INVALID")
    if not path.exists():
        if allow_missing:
            return False
        raise ValueError("D1_MAC_PRIVATE_DIRECTORY_MISSING")
    info = path.lstat()
    if (not stat.S_ISDIR(info.st_mode)
            or info.st_mode & 0o077):
        raise ValueError("D1_MAC_PRIVATE_DIRECTORY_PERMISSIONS")
    return True


def _os_user_home():
    """OS account home, not a caller-adjustable HOME environment variable."""
    return Path(pwd.getpwuid(os.getuid()).pw_dir)


def _inspect_fixed_registry():
    """Observes but never creates, changes or consumes the fixed Mac root."""
    path = PRIVATE_FIXED_REGISTRY
    if not isinstance(path, Path) or not path.is_absolute():
        raise ValueError("D1_MAC_FIXED_REGISTRY_NOT_ABSOLUTE")
    expected = (_os_user_home() / "Library" / "Application Support"
                / "MissionEvidence" / "f0-grant-registry")
    if path != expected:
        raise ValueError("D1_MAC_FIXED_REGISTRY_PATH_ENV_MISMATCH")
    # Verify pre-existing components; do not resolve or accept symlink swaps.
    cursor = Path(path.anchor)
    for piece in path.parts[1:]:
        cursor /= piece
        if cursor.is_symlink():
            raise ValueError("D1_MAC_FIXED_REGISTRY_SYMLINK")
    ready = _private_directory(path, allow_missing=True)
    return {
        "fixed_private_registry": str(path),
        "registry_exists_and_private": ready,
        "registry_opened": False,
        "marker_consumed": False,
    }


def inspect_supervised_mac_scope_offline(
        checkout_root: Path, expected_sha: str, permit_raw: bytes, *,
        evidence_root: Path):
    """Verify actual Mac checkout, strict scope and module path, no writes.

    The permit bytes are UNAUTHORIZED review input, not a real D2 permit.
    Caller cannot pass a live-enable flag, signer root or registry root.
    """
    if platform.system() != "Darwin":
        raise ValueError("D1_MAC_ONLY_NO_NETWORK_OR_GRANT")
    if not isinstance(checkout_root, Path) or not checkout_root.is_absolute():
        raise ValueError("D1_MAC_CHECKOUT_ROOT_INVALID")
    if not isinstance(evidence_root, Path) or not evidence_root.is_absolute():
        raise ValueError("D1_MAC_EVIDENCE_ROOT_INVALID")
    if not _private_directory(evidence_root):
        raise ValueError("D1_MAC_EVIDENCE_ROOT_NOT_PRIVATE")
    evidence_resolved = evidence_root.resolve()
    registry_resolved = PRIVATE_FIXED_REGISTRY.resolve()
    if (evidence_resolved == registry_resolved
            or evidence_resolved in registry_resolved.parents
            or registry_resolved in evidence_resolved.parents):
        raise ValueError("D1_MAC_EVIDENCE_CANNOT_OVERLAP_REGISTRY")
    permit = _strict_permit(permit_raw)
    if permit["approved_commit_sha"] != expected_sha:
        raise ValueError("D1_MAC_PERMIT_CODE_SHA_MISMATCH")
    # Candidate scope must be valid *now*, but NEVER creates a real permit.
    now_utc = datetime.now(timezone.utc)
    scope = validate_window_contract(permit, now_utc)
    if permit["max_response_bytes"] != 2_000_000:
        raise ValueError("D1_MAC_ARCHIVE_CAP_NOT_ENFORCEABLE")
    # Use only the fixed F0 reviewed module list, no operator-injected modules.
    for name in CRITICAL_MODULES:
        importlib.import_module(name)
    source = review_loaded_runtime_offline(checkout_root, expected_sha)
    registry = _inspect_fixed_registry()
    return {
        "schema": OFFLINE_REPORT_SCHEMA,
        "verified_locally": True,
        "reviewed_sha": expected_sha,
        "permit_raw_sha256": sha256(permit_raw).hexdigest(),
        "untrusted_candidate_permit": True,
        "utc_basis": "LOCAL_SYSTEM_UTC_NOT_EXTERNAL_ATTESTATION",
        "checked_at_utc": now_utc.isoformat(),
        "scope": scope,
        "source": source,
        "fixed_registry_state": registry,
        "max_live_slots": permit["max_inflight"],
        "max_live_total_attempts": permit["max_total_attempts"],
        "post_gap_ms": permit["min_start_gap_ms"],
        "evidence_root": str(evidence_root),
        "release_approval_binds_this_exact_sha": False,
        "d2_permit_approved": False,
        "d3_run_approved": False,
        "real_sender_bound_to_unique_coordinator": False,
        "network_requests": 0,
        "decision": "D1_BLOCKED_AUTHORITY",
        "production": "PRODUCTION_NO_GO",
    }


def send_live(*_args, **_kwargs):
    """Must deny before checking or mutating registry, evidence or sockets."""
    raise ValueError("D1_MAC_PROTECTED_SEND_DISABLED_D2_D3_REQUIRED")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="F0 D1 local Mac preflight only (NO LIVE NETWORK)")
    parser.add_argument("--verify-only", action="store_true", required=True)
    parser.add_argument("--checkout-root", type=Path, required=True)
    parser.add_argument("--approved-code-sha", required=True)
    parser.add_argument("--candidate-scope", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args(argv)
    candidate = args.candidate_scope
    if (not candidate.is_absolute() or candidate.is_symlink()
            or not candidate.is_file()
            or not candidate.stat().st_mode & 0o170000 == 0o100000
            or candidate.stat().st_mode & 0o077
            or candidate.stat().st_size > 8192):
        raise ValueError("D1_MAC_UNSAFE_CANDIDATE_SCOPE_FILE")
    # No output-file option, service mode, real-socket or '--run' flag exists.
    report = inspect_supervised_mac_scope_offline(
        args.checkout_root, args.approved_code_sha,
        candidate.read_bytes(), evidence_root=args.evidence_root)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
