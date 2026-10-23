#!/usr/bin/env python3
"""D1 OFFLINE authorization/lease primitives. NO live runner or permit issuer.

Public-key authorities for real use are intentionally NOT enrolled: D2
requires a separate reviewed trust-root commit and explicit new user grant.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

SCHEMA = "bsc-f0-d1-two-role-approval-offline-v1"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
GRANT_ID = re.compile(r"[a-zA-Z0-9_-]{12,80}\Z")
OPENSSL = "/usr/bin/openssl"
# INTENTIONALLY NO REAL TRUST ROOTS: cannot produce a live authorization.
PINNED_LIVE_TRUST_ROOTS = {}
PRIVATE_FIXED_REGISTRY = (Path.home() / "Library" / "Application Support" /
                          "MissionEvidence" / "f0-grant-registry")


def _need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def approval_message(role, digest, commit):
    _need(role in ("user", "reviewer") and isinstance(digest, str)
          and HEX64.fullmatch(digest) and isinstance(commit, str)
          and HEX40.fullmatch(commit), "D1_APPROVAL_MESSAGE_INVALID")
    return (SCHEMA + "\n" + role + "\n" + digest + "\n" +
            commit + "\n").encode("ascii")


def _verify_signature(pubkey, message, signature):
    """Use vetted OpenSSL Ed25519; no handwritten cryptographic verification."""
    _need(type(pubkey) is bytes and pubkey.startswith(b"-----BEGIN PUBLIC KEY-----")
          and type(signature) is bytes and len(signature) == 64,
          "D1_SIGNED_PROOF_INVALID")
    _need(Path(OPENSSL).is_file(), "D1_OPENSSL_NOT_INSTALLED")
    with tempfile.TemporaryDirectory(prefix="f0-d1-verify-") as dirname:
        base = Path(dirname)
        files = [(base / "k.pem", pubkey), (base / "msg", message),
                 (base / "sig", signature)]
        for location, blob in files:
            with os.fdopen(os.open(location, os.O_CREAT | os.O_EXCL |
                                  os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
                                  0o600), "wb") as out:
                out.write(blob)
                out.flush()
                os.fsync(out.fileno())
        try:
            run = subprocess.run(
                [OPENSSL, "pkeyutl", "-verify", "-pubin",
                 "-inkey", str(files[0][0]), "-rawin",
                 "-in", str(files[1][0]), "-sigfile", str(files[2][0])],
                check=False, capture_output=True, timeout=5,
                env={"PATH": "/usr/bin:/bin", "HOME": str(base)})
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError("D1_VERIFIER_UNAVAILABLE") from exc
        return run.returncode == 0


def _public_key_fingerprint(pubkey):
    """Canonical DER fingerprint: distinct aliases for one key are NOT two roles."""
    try:
        res = subprocess.run(
            [OPENSSL, "pkey", "-pubin", "-outform", "DER"],
            input=pubkey, capture_output=True, check=False,
            timeout=5, env={"PATH":"/usr/bin:/bin"})
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("D1_PUBLIC_KEY_PARSE_FAILED") from exc
    _need(res.returncode == 0 and len(res.stdout) > 0,
          "D1_PUBLIC_KEY_PARSE_FAILED")
    return sha(res.stdout)


def validate_approvals_offline(permit_raw, expected_sha, proofs, trust_roots):
    """Return signed offline verification evidence, NEVER a live run permit.

    trust_roots is injectable ONLY because D1 has no network entrypoint.
    In D2 the trusted keys must be frozen and reviewed separately.
    """
    _need(type(permit_raw) is bytes and 0 < len(permit_raw) <= 8192
          and type(expected_sha) is str and HEX40.fullmatch(expected_sha)
          and type(proofs) is dict and set(proofs) == {"user", "reviewer"}
          and type(trust_roots) is dict
          and set(trust_roots) == {"user", "reviewer"},
          "D1_APPROVAL_SCOPE_INVALID")
    try:
        permit = json.loads(permit_raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("D1_PERMIT_JSON_INVALID") from exc
    _need(type(permit) is dict and permit.get("approved_commit_sha") == expected_sha
          and type(permit.get("grant_id")) is str
          and GRANT_ID.fullmatch(permit["grant_id"])
          and permit.get("endpoint") == "https://bsc-dataseed.bnbchain.org"
          and permit.get("chain_id") == 56
          and permit.get("methods") ==
          ["eth_chainId", "eth_blockNumber", "eth_getBlockByNumber"]
          and type(permit.get("max_total_attempts")) is int
          and 2 <= permit["max_total_attempts"] <= 32
          and type(permit.get("max_block_reads")) is int
          and 1 <= permit["max_block_reads"] <= 24
          and type(permit.get("max_head_refreshes")) is int
          and 0 <= permit["max_head_refreshes"] <= 6
          and type(permit.get("min_start_gap_ms")) is int
          and permit["min_start_gap_ms"] >= 250
          and permit.get("read_only") is True
          and permit.get("free_only") is True
          and permit.get("no_retries") is True
          and permit.get("no_ws") is True
          and permit.get("background") is False,
          "D1_PERMIT_SCOPE_INVALID")
    _need(permit["max_block_reads"] + permit["max_head_refreshes"] + 2 >=
          permit["max_total_attempts"] and
          len(proofs) == 2, "D1_PERMIT_BUDGET_INVALID")
    digest = sha(permit_raw)
    names = []
    key_fingerprints = []
    for role in ("user", "reviewer"):
        proof = proofs[role]
        trust = trust_roots[role]
        _need(type(proof) is dict and set(proof) == {"key_id", "signature"}
              and type(trust) is dict and set(trust) == {"key_id", "public_pem"}
              and type(proof["key_id"]) is str and
              proof["key_id"] == trust["key_id"] and
              type(trust["public_pem"]) is bytes,
              "D1_SIGNER_TRUST_ID_MISMATCH")
        names.append(proof["key_id"])
        key_fingerprints.append(_public_key_fingerprint(trust["public_pem"]))
        if len(key_fingerprints) == 2:
            _need(key_fingerprints[0] != key_fingerprints[1],
                  "D1_SAME_SIGNER_FORBIDDEN")
        _need(_verify_signature(trust["public_pem"],
                                approval_message(role, digest, expected_sha),
                                proof["signature"]),
              "D1_SIGNED_PROOF_INVALID")
    _need(names[0] != names[1] and
          key_fingerprints[0] != key_fingerprints[1],
          "D1_SAME_SIGNER_FORBIDDEN")
    return {"verified_for": "OFFLINE_FAKE_TEST_ONLY_NO_NETWORK",
            "permit_sha256": digest,
            "commit_sha": expected_sha,
            "grant_id": permit["grant_id"],
            "user_key_id": names[0], "reviewer_key_id": names[1]}


def validate_live_trust_roots_not_enrolled():
    """The deliberately locked D1 path MUST deny every prospective live grant."""
    _need(bool(PINNED_LIVE_TRUST_ROOTS), "D1_NO_LIVE_TRUST_ROOT_ENROLLED")
    raise ValueError("D1_LIVE_SENDER_NOT_IMPLEMENTED")


class FixedLocalGrantRegistry:
    """The only D1 registry factory with a non-injectable fixed Mac path.

    Still OFFLINE only. Actual signed live activation is absent in D1.
    """
    def __init__(self):
        self.delegate = OfflineGrantRegistry(PRIVATE_FIXED_REGISTRY)

    def consume(self, grant_id: str, permit_sha256: str):
        return self.delegate.consume(grant_id, permit_sha256)


class OfflineGrantRegistry:
    """Fake-only lease registrar. Shared grant IDs remain spent across outputs.

    Constructor injection is ONLY present in D1 without any live sender.
    A later real runner must *not* accept arbitrary paths from a permit.
    """
    def __init__(self, root: Path):
        _need(isinstance(root, Path) and root.is_absolute() and
              root.is_dir() and not root.is_symlink() and
              (root.stat().st_mode & 0o077) == 0,
              "D1_REGISTRY_NOT_PRIVATE")
        self.root = root

    def consume(self, grant_id: str, permit_sha256: str):
        _need(type(grant_id) is str and GRANT_ID.fullmatch(grant_id)
              and type(permit_sha256) is str and
              HEX64.fullmatch(permit_sha256),
              "D1_GRANT_ID_OR_DIGEST_INVALID")
        _need(not self.root.is_symlink() and
              self.root.is_dir() and (self.root.stat().st_mode & 0o077) == 0,
              "D1_REGISTRY_NOT_PRIVATE")
        # One marker per grant ID; changing output root or permit content
        # cannot make the original identity available again.
        filename = sha(grant_id.encode()) + ".consumed.json"
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            # Use a single already-opened directory fd for BOTH atomic create
            # and directory fsync: directory name replacement mid-operation
            # cannot redirect either call to a different path.
            dfd = os.open(self.root, os.O_RDONLY |
                          getattr(os, "O_DIRECTORY", 0) |
                          getattr(os, "O_NOFOLLOW", 0))
        except OSError as exc:
            raise ValueError("D1_REGISTRY_OPEN_DENIED") from exc
        try:
            try:
                fd = os.open(filename, flags, 0o600, dir_fd=dfd)
            except FileExistsError as exc:
                raise ValueError("D1_GRANT_ALREADY_CONSUMED") from exc
            try:
                with os.fdopen(fd, "wb") as out:
                    out.write((json.dumps({
                        "grant_id_sha256":sha(grant_id.encode()),
                        "permit_sha256":permit_sha256,
                        "outcome":"CONSUMED_OR_UNKNOWN",
                    }, sort_keys=True) + "\n").encode())
                    out.flush()
                    os.fsync(out.fileno())
                os.fsync(dfd)
            except OSError as exc:
                # O_EXCL marker remains consumed even if its durability is
                # uncertain. Never remove it or retry automatically.
                raise ValueError("D1_GRANT_CONSUMPTION_UNCERTAIN_STOP") from exc
        finally:
            os.close(dfd)
        return {"grant_id_sha256": sha(grant_id.encode()),
                "permit_sha256": permit_sha256,
                "status": "CONSUMED_NOT_A_NETWORK_AUTHORIZATION"}
