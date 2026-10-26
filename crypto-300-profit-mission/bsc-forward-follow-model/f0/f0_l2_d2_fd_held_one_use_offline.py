"""D2 held-directory-FD atomic once-marker rehearsal on DISPOSABLE TMP only.

No production OS directory access, real human signer, network source or live
runner. Reuses the one original D1 O_EXCL + file/dir fsync implementation,
not a second registry or authority channel. Never converts a rehearsal
marker into a production marker or grant.
"""
from __future__ import annotations

import os
from pathlib import Path
import pwd
import stat
import tempfile

from f0_l2_d1_grant import (
    PRIVATE_FIXED_REGISTRY, _consume_once_using_open_dirfd,
)

_TMP_PREFIX = "bsc-f0-once-test-"


def rehearse_held_test_registry_once_offline(
        test_root: Path, grant_id: str, permit_sha256: str):
    """Hold the SAME opened test-directory inode through atomic consumption.

    Directory must be an already-created, uid-owned 0700 DIRECT child of
    the OS temp root and use the explicit disposable prefix. Refuse the
    actual fixed production registry, its ancestors and descendants.
    Caller never provides a production grant or executable send function.
    """
    tmp = Path(tempfile.gettempdir()).resolve()
    if (not isinstance(test_root, Path) or not test_root.is_absolute()
            or test_root.is_symlink()
            or test_root.parent.resolve() != tmp
            or not test_root.name.startswith(_TMP_PREFIX)
            or test_root.name == _TMP_PREFIX
            or not test_root.is_dir()):
        raise ValueError("D2_ONCE_TEST_ROOT_NOT_DISPOSABLE")
    actual = test_root.resolve()
    if actual != test_root:
        raise ValueError("D2_ONCE_TEST_ROOT_ALIAS_REFUSED")
    passwd_home = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    prod = passwd_home / "Library" / "Application Support" / (
        "MissionEvidence") / "f0-grant-registry"
    frozen = PRIVATE_FIXED_REGISTRY.resolve()
    if (actual == prod or actual in prod.parents or prod in actual.parents
            or actual == frozen or actual in frozen.parents or
            frozen in actual.parents):
        raise ValueError("D2_ONCE_TEST_PRODUCTION_OVERLAP_DENIED")
    info = actual.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or info.st_mode & 0o077):
        raise ValueError("D2_ONCE_TEST_DIR_OWNER_OR_MODE_INVALID")
    flags = (os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
             | getattr(os, "O_NOFOLLOW", 0)
             | getattr(os, "O_CLOEXEC", 0))
    try:
        dfd = os.open(test_root, flags)
    except OSError as exc:
        raise ValueError("D2_ONCE_TEST_DIR_OPEN_DENIED") from exc
    try:
        opened = os.fstat(dfd)
        current = test_root.lstat()
        if (opened.st_uid != os.getuid()
                or not stat.S_ISDIR(opened.st_mode)
                or opened.st_mode & 0o077
                or (opened.st_dev, opened.st_ino) !=
                   (current.st_dev, current.st_ino)):
            raise ValueError("D2_ONCE_TEST_DIR_INODE_CHANGED")
        result = _consume_once_using_open_dirfd(
            dfd, grant_id, permit_sha256)
        # Never claim 'success' if the original directory name now points
        # at a different inode. Previously spent marker is NEVER deleted.
        try:
            after = test_root.lstat()
        except OSError as exc:
            raise ValueError("D2_ONCE_TEST_DIR_CHANGED_AFTER_CONSUME") from exc
        if ((opened.st_dev, opened.st_ino) !=
                (after.st_dev, after.st_ino)):
            raise ValueError("D2_ONCE_TEST_DIR_CHANGED_AFTER_CONSUME")
    finally:
        os.close(dfd)
    return {
        "schema": "f0-d2-once-held-fd-disposable-test-only-v1",
        "test_marker_sha256": result["grant_id_sha256"],
        "permit_sha256": result["permit_sha256"],
        "status": "TEST_MARKER_CONSUMED_NOT_PRODUCTION",
        "directory_fd_closed": True,
        "real_human_authority_verified": False,
        "production_marker_consumed": False,
        "network_requests": 0,
        "production": "PRODUCTION_NO_GO",
    }


def send_live(*_args, **_kwargs):
    raise ValueError("D2_ONCE_TEST_NOT_LIVE_AUTHORITY")
