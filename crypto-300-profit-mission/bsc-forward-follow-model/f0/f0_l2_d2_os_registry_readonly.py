"""Read-only OS-account-bound *prospective* production registry audit.

No marker is read, created, overwritten, removed or consumed. No live source,
signer, registry constructor, executor or socket is reachable from this module.
Returning filesystem_ready never means D2/D3 grant approval.
"""
from __future__ import annotations

import os
from pathlib import Path
import pwd
import stat

from f0_l2_d1_grant import PRIVATE_FIXED_REGISTRY

_REGISTRY_COMPONENTS = (
    "Library", "Application Support", "MissionEvidence", "f0-grant-registry",
)


def _actual_os_home():
    """Derive account identity from OS UID, never caller HOME."""
    user = pwd.getpwuid(os.getuid())
    home = Path(user.pw_dir)
    if (not home.is_absolute() or home == Path("/")
            or ".." in home.parts or "." in home.parts
            or not home.is_dir() or home.is_symlink()):
        raise ValueError("D2_OS_ACCOUNT_HOME_INVALID")
    info = home.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise ValueError("D2_OS_ACCOUNT_HOME_OWNERSHIP_INVALID")
    return home


def inspect_fixed_production_registry_readonly():
    """Check the *one* OS-home-derived path without touching marker bytes.

    The output denotes directory layout readiness only. It cannot authorize
    production use even if every permission and owner check succeeds.
    Missing paths are reported as NOT READY, never created automatically.
    """
    home = _actual_os_home()
    expected = home.joinpath(*_REGISTRY_COMPONENTS)
    if (not isinstance(PRIVATE_FIXED_REGISTRY, Path)
            or PRIVATE_FIXED_REGISTRY != expected):
        raise ValueError("D2_OS_FIXED_REGISTRY_ENV_OR_PATH_MISMATCH")

    # Walk without following symlink directory components. Ancestors
    # Library/Application Support may be account-readable; the evidence
    # namespace and final grant-registry must be owner-private.
    cursor = home
    for i, piece in enumerate(_REGISTRY_COMPONENTS):
        cursor /= piece
        try:
            info = cursor.lstat()
        except FileNotFoundError:
            return {
                "schema": "f0-d2-os-registry-readonly-NO-GRANT-v1",
                "fixed_registry": str(expected),
                "os_uid": os.getuid(),
                "filesystem_ready": False,
                "reason": "MISSING_COMPONENT_NO_AUTO_CREATE",
                "registry_opened_readonly": False,
                "marker_consumed": False,
                "production_authorized": False,
                "network_requests": 0,
                "production": "PRODUCTION_NO_GO",
            }
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError("D2_OS_REGISTRY_SYMLINK_OR_OWNER_INVALID")
        if i >= 2 and info.st_mode & 0o077:
            raise ValueError("D2_OS_REGISTRY_NOT_PRIVATE")

    # Secure no-follow dir-fd verifies the inode at inspection time. This
    # remains a read-only snapshot, NOT a lease or race-proof guarantee
    # across a later process start.
    flags = (os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
             | getattr(os, "O_NOFOLLOW", 0)
             | getattr(os, "O_CLOEXEC", 0))
    try:
        fd = os.open(expected, flags)
    except OSError as exc:
        raise ValueError("D2_OS_REGISTRY_READONLY_OPEN_DENIED") from exc
    try:
        opened = os.fstat(fd)
        if (not stat.S_ISDIR(opened.st_mode)
                or opened.st_uid != os.getuid()
                or opened.st_mode & 0o077):
            raise ValueError("D2_OS_REGISTRY_OPENED_INODE_INVALID")
        final = expected.lstat()
        if (final.st_dev != opened.st_dev
                or final.st_ino != opened.st_ino):
            raise ValueError("D2_OS_REGISTRY_INODE_CHANGED_DURING_AUDIT")
    finally:
        os.close(fd)
    return {
        "schema": "f0-d2-os-registry-readonly-NO-GRANT-v1",
        "fixed_registry": str(expected),
        "os_uid": os.getuid(),
        "filesystem_ready": True,
        "reason": "PRIVATE_DIRECTORY_ONLY_NOT_AUTHORITY",
        "registry_opened_readonly": True,
        "marker_consumed": False,
        "production_authorized": False,
        "network_requests": 0,
        "production": "PRODUCTION_NO_GO",
    }


def send_live(*_args, **_kwargs):
    raise ValueError("D2_OS_REGISTRY_INSPECTION_NOT_LIVE_AUTHORITY")
