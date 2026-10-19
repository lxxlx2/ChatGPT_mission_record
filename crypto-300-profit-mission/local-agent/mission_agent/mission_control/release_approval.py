"""User-signed, external release approval; no AI/self-digest authorization.

The public verification key must be provisioned separately by the operator/
administrator in a root-owned directory, never created by installer or PR.
This module validates policy approval, NOT permission to restart/deploy.
"""
from __future__ import annotations

import hashlib
import os
import json
import re
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TRUSTED_APPROVAL_KEY = Path(
    "/Library/Application Support/FrankMeme/release-approval-public-key.pem"
)
SCOPE = "FRANK_MC_DECISION_LOCAL_AND_GMAIL_ONLY"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SHA1 = re.compile(r"[0-9a-f]{40}\Z")
_FIELDS = {
    "schema_version", "scope", "policy_sha256", "integration_sha",
    "approved_by", "approved_at", "expires_at", "deployment_approved",
}


def trusted_checkout_identity(checkout: Path) -> str:
    """Resolve Git identity for *this* checkout, not inherited Git state.

    Sanitize all GIT_* variables, use the system git executable and validate
    repository discovery against the actual on-disk .git root. Fail closed.
    """
    checkout = Path(checkout).resolve(strict=True)
    expected_root = next(
        (p for p in (checkout, *checkout.parents)
         if (p / ".git").is_file() or (p / ".git").is_dir()),
        None,
    )
    if expected_root is None:
        raise ValueError("RELEASE_GIT_ROOT_NOT_FOUND")
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    def git(*args: str) -> str:
        try:
            result = subprocess.run(
                ["/usr/bin/git", "-C", str(checkout), *args],
                env=clean_env, capture_output=True, text=True,
                timeout=10, check=True,
            )
        except (OSError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired) as exc:
            raise ValueError("RELEASE_GIT_IDENTITY_UNVERIFIED") from exc
        return result.stdout.strip()
    top = Path(git("rev-parse", "--show-toplevel")).resolve(strict=True)
    if top != expected_root:
        raise ValueError("RELEASE_GIT_CHECKOUT_ROOT_MISMATCH")
    actual_sha = git("rev-parse", "--verify", "HEAD^{commit}")
    if _SHA1.fullmatch(actual_sha) is None:
        raise ValueError("RELEASE_GIT_COMMIT_IDENTITY_INVALID")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("LIVE_RELEASE_WORKTREE_DIRTY")
    return actual_sha


def _instant(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("APPROVAL_TIME_INVALID")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("APPROVAL_TIME_INVALID") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("APPROVAL_TIME_NOT_OFFSET_AWARE")
    return dt.astimezone(timezone.utc)


def _check_trust_anchor(key: Path) -> None:
    # Disallow symlinks and same-user replacement of trusted key or directory.
    try:
        file_info, parent_info = key.lstat(), key.parent.lstat()
    except OSError as exc:
        raise ValueError("EXTERNAL_APPROVAL_TRUST_ANCHOR_NOT_PROVISIONED") from exc
    if (not stat.S_ISREG(file_info.st_mode)
            or not stat.S_ISDIR(parent_info.st_mode)
            or file_info.st_uid != 0 or parent_info.st_uid != 0
            or file_info.st_mode & 0o022 or parent_info.st_mode & 0o022):
        raise ValueError("EXTERNAL_APPROVAL_TRUST_ANCHOR_UNSAFE")


def verify_signed_release_approval(
    *, record_path: Path, signature_path: Path, policy_path: Path,
    externally_approved_sha: str, code_commit_sha: str,
    trusted_key: Path = TRUSTED_APPROVAL_KEY,
    enforce_protected_key: bool = True,
    now: datetime | None = None,
) -> dict:
    """Verify exact signed bytes, user-approved policy and deployed code.

    trusted_key override and enforce_protected_key=False are exclusively
    for isolated unit tests. Production CLI never exposes those options.
    """
    key = Path(trusted_key)
    if enforce_protected_key:
        _check_trust_anchor(key)
    record = Path(record_path)
    signature = Path(signature_path)
    if record.is_symlink() or signature.is_symlink():
        raise ValueError("APPROVAL_INPUT_SYMLINK_REJECTED")
    raw = record.read_bytes()
    if len(raw) > 8192 or not raw:
        raise ValueError("APPROVAL_RECORD_SIZE_INVALID")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("APPROVAL_RECORD_MALFORMED") from exc
    if not isinstance(data, dict) or set(data) != _FIELDS:
        raise ValueError("APPROVAL_RECORD_FIELDS_INVALID")
    if (data["schema_version"] != 1
            or data["scope"] != SCOPE
            or data["deployment_approved"] is not False
            or not isinstance(data["approved_by"], str)
            or not data["approved_by"].strip()):
        raise ValueError("APPROVAL_SCOPE_OR_OWNER_INVALID")
    if (not isinstance(externally_approved_sha, str)
            or _SHA256.fullmatch(externally_approved_sha) is None
            or not isinstance(code_commit_sha, str)
            or _SHA1.fullmatch(code_commit_sha) is None):
        raise ValueError("APPROVAL_IDENTITY_INVALID")
    actual = hashlib.sha256(Path(policy_path).read_bytes()).hexdigest()
    if (data["policy_sha256"] != actual
            or data["policy_sha256"] != externally_approved_sha
            or data["integration_sha"] != code_commit_sha):
        raise ValueError("APPROVAL_POLICY_OR_CODE_MISMATCH")
    approved_at, expires_at = _instant(data["approved_at"]), _instant(data["expires_at"])
    present = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if not approved_at <= present < expires_at:
        raise ValueError("APPROVAL_NOT_CURRENT")
    # Detached RSA/SHA256 signature over the entire original manifest bytes.
    # No trusted key, signer, or signed manifest is generated by this verifier.
    try:
        # Verify the exact bytes already parsed above (stdin), not a second
        # reading of a mutable record path. Prevent content-swap TOCTOU.
        check = subprocess.run(
            ["/usr/bin/openssl", "dgst", "-sha256", "-verify", str(key),
             "-signature", str(signature)],
            input=raw, capture_output=True, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("APPROVAL_SIGNATURE_TOOL_UNAVAILABLE") from exc
    if check.returncode != 0 or b"Verified OK" not in check.stdout:
        raise ValueError("APPROVAL_SIGNATURE_INVALID")
    return {
        "policy_sha256": actual,
        "integration_sha": code_commit_sha,
        "scope": SCOPE,
        "expires_at": expires_at.isoformat(),
        "approval_record_sha256": hashlib.sha256(raw).hexdigest(),
    }


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Verify independently signed release consent")
    p.add_argument("--record", required=True, type=Path)
    p.add_argument("--signature", required=True, type=Path)
    p.add_argument("--policy", required=True, type=Path)
    p.add_argument("--approved-policy-sha256", required=True)
    p.add_argument("--code-commit-sha", required=True)
    a = p.parse_args()
    proof = verify_signed_release_approval(
        record_path=a.record, signature_path=a.signature,
        policy_path=a.policy,
        externally_approved_sha=a.approved_policy_sha256,
        code_commit_sha=a.code_commit_sha,
    )
    print(json.dumps({"status": "SIGNED_POLICY_APPROVAL_VALIDATED", **proof}, sort_keys=True))
    print("DEPLOYMENT_OR_RESTART_AUTHORIZATION: NOT_GRANTED_BY_THIS_RECORD")


if __name__ == "__main__":
    main()
