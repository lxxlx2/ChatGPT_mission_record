#!/usr/bin/env python3
"""Mac/CI F0 code-and-loaded-module provenance audit; OFFLINE diagnostic only.

All tracked F0 byte contents must match a clean immutable Git HEAD, while
the actual imported critical modules must resolve to this reviewed tree.
Python executable and cryptography installation hashes are reported for
independent Codex comparison. These locally obtained values are NOT their
own trusted reference and grant no permission to use the network.
"""
from __future__ import annotations

import sys
from hashlib import sha256
from pathlib import Path

from f0_l2_d1_inventory import (
    SOURCE_PREFIX, tracked_f0_source_manifest_offline,
    installed_ed25519_distribution_inventory_offline,
)

# Do not accept a caller-selected list that omits a critical module.
CRITICAL_MODULES = (
    "f0_l1_http_wire",
    "f0_l2_d1_coordinator",
    "f0_l2_d1_concrete_https",
    "f0_l2_d1_bundle",
    "f0_l2_d1_inventory",
    "f0_l2_d1_inventory_gate",
    "f0_l2_d1_grant",
    "f0_l2_d1_post_utc",
    "f0_l2_d1_preflight",
    "f0_l2_d1_recovery",
    "f0_l2_d1_integrated_exit",
)


def review_loaded_runtime_offline(checkout_root: Path, exact_sha: str):
    """Require loaded code to be from this SHA; no imports or network.

    Must run only after the tests have imported each named module from their
    independently reviewed repo checkout. The output is a measurement, not
    signed user authority or a malicious-OS remote attestation.
    """
    tree = tracked_f0_source_manifest_offline(checkout_root, exact_sha)
    digests = tree["reviewed_path_digests"]
    loaded = {}
    expected_dir = (
        checkout_root / SOURCE_PREFIX
    ).resolve()
    for name in CRITICAL_MODULES:
        module = sys.modules.get(name)
        if module is None or getattr(module, "__spec__", None) is None:
            raise ValueError("D1_RUNTIME_CRITICAL_MODULE_NOT_LOADED:" + name)
        relative = SOURCE_PREFIX + name + ".py"
        expected = expected_dir / (name + ".py")
        if relative not in digests:
            raise ValueError("D1_RUNTIME_MODULE_NOT_IN_FROZEN_GIT:" + name)
        disk = Path(getattr(module, "__file__", "/missing")).resolve()
        origin = Path(str(module.__spec__.origin)).resolve()
        if disk != expected or origin != expected:
            raise ValueError("D1_RUNTIME_UNREVIEWED_IMPORT_ORIGIN:" + name)
        loaded[name] = {
            "relative_path": relative,
            "sha256": digests[relative],
        }
    wheel = installed_ed25519_distribution_inventory_offline()
    python_path = Path(sys.executable)
    if not python_path.is_file():
        raise ValueError("D1_RUNTIME_PYTHON_EXECUTABLE_UNAVAILABLE")
    return {
        "status": "REVIEWED_LOCAL_BYTES_MATCH_NOT_LIVE_AUTHORIZATION",
        "source_commit_sha": exact_sha,
        "tracked_source_manifest_sha256": tree[
            "tracked_source_manifest_sha256"],
        "tracked_paths_checked": tree["all_tracked_f0_files_checked"],
        "critical_module_origins_checked": loaded,
        "cryptography_version": wheel["distribution_version"],
        "cryptography_manifest_sha256": wheel[
            "wheel_file_manifest_sha256"],
        "wheel_entries_without_record_hash": len(
            wheel["record_entries_without_hash"]),
        "python_executable_sha256": sha256(
            python_path.read_bytes()).hexdigest(),
        "independent_reference_verified": False,
        "full_native_runtime_attested": False,
        "production_grant_authorized": False,
        "network_requests": 0,
    }


def send_live(*_args, **_kwargs):
    raise ValueError("D1_MAC_PROVENANCE_NOT_A_LIVE_PERMIT")
