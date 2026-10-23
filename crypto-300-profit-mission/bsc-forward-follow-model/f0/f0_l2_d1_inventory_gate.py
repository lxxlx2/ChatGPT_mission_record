#!/usr/bin/env python3
"""D1 OFFLINE inventory attestations and one-use FAKE session rehearsal.

No production trust roots, no live sender, no real authorization or CLI.
The two public entry points accept only test-injected keys and private
temporary registry paths. Results NEVER authorize real network requests.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from f0_l2_d1_bundle import (_strict_permit, validate_offline_bundle,
                             run_gated_fake_session)
from f0_l2_d1_grant import (
    OfflineGrantRegistry, _ed25519_public_key, _verify_signature,
    _public_key_fingerprint)
from f0_l2_d1_inventory import (
    tracked_f0_source_manifest_offline,
    installed_ed25519_distribution_inventory_offline)

ATTEST_SCHEMA = "bsc-f0-d1-inventory-attestation-OFFLINE-v1"
EXACT_FIELDS = frozenset({
    "schema", "source_commit_sha", "permit_sha256",
    "tracked_source_manifest_sha256", "wheel_file_manifest_sha256",
    "python_executable_sha256", "cryptography_version",
    "wheel_unhashed_count", "complete_dependency_closure_attested"
})


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        check(key not in result, "D1_ATTEST_DUPLICATE_JSON_FIELD")
        result[key] = value
    return result


def inventory_attestation_message(role, raw_bytes, commit_sha):
    """Bytes signed by each ephemeral verifier role; never a grant."""
    check(role in ("user", "reviewer") and type(raw_bytes) is bytes and
          len(raw_bytes) <= 8192 and type(commit_sha) is str and
          len(commit_sha) == 40 and
          all(c in "0123456789abcdef" for c in commit_sha),
          "D1_ATTEST_MESSAGE_INVALID")
    return (ATTEST_SCHEMA + "\n" + role + "\n" +
            hashlib.sha256(raw_bytes).hexdigest() + "\n" +
            commit_sha + "\n").encode("ascii")


def offline_inventory_statement(permit_raw, expected_sha, checkout_root):
    """Reconstruct locally measured inventory. Values remain UNTRUSTED.

    RECORD and runtime files are operator-controlled. A future production
    design needs independent wheel/interpreter/import closure attestation.
    """
    permit = _strict_permit(permit_raw)
    check(permit["approved_commit_sha"] == expected_sha,
          "D1_ATTEST_COMMIT_NOT_BOUND")
    source = tracked_f0_source_manifest_offline(checkout_root, expected_sha)
    wheel = installed_ed25519_distribution_inventory_offline()
    return {
        "schema": ATTEST_SCHEMA,
        "source_commit_sha": expected_sha,
        "permit_sha256": hashlib.sha256(permit_raw).hexdigest(),
        "tracked_source_manifest_sha256":
            source["tracked_source_manifest_sha256"],
        "wheel_file_manifest_sha256": wheel["wheel_file_manifest_sha256"],
        "python_executable_sha256": wheel["python_executable_sha256"],
        "cryptography_version": wheel["distribution_version"],
        "wheel_unhashed_count": len(wheel["record_entries_without_hash"]),
        "complete_dependency_closure_attested": False,
    }


def verify_test_inventory_attestation(permit_raw, expected_sha,
                                       checkout_root, raw_statement,
                                       signatures, test_only_trust_roots):
    """Compare actual installed bytes with two-role signed test commitment.

    The trust roots are INJECTED and must never be used to unlock a socket.
    A signature made with arbitrary test keys has NO production authority.
    """
    check(type(raw_statement) is bytes and
          0 < len(raw_statement) <= 8192 and
          type(signatures) is dict and
          set(signatures) == {"user", "reviewer"} and
          type(test_only_trust_roots) is dict and
          set(test_only_trust_roots) == {"user", "reviewer"},
          "D1_ATTEST_INVALID_ARGUMENT")
    try:
        statement = json.loads(raw_statement, object_pairs_hook=_unique_json)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("D1_ATTEST_JSON_INVALID") from exc
    check(type(statement) is dict and
          set(statement) == EXACT_FIELDS and
          statement.get("complete_dependency_closure_attested") is False,
          "D1_ATTEST_UNREVIEWED_FIELDS_OR_FALSE_PROVENANCE")
    live = offline_inventory_statement(permit_raw, expected_sha, checkout_root)
    check(statement == live,
          "D1_ATTEST_RUNTIME_BYTES_OR_SCOPE_MISMATCH")
    key_fingerprints = []
    key_ids = []
    for role in ("user", "reviewer"):
        root = test_only_trust_roots[role]
        proof = signatures[role]
        check(type(root) is dict and
              set(root) == {"key_id", "public_pem"} and
              type(proof) is dict and
              set(proof) == {"key_id", "signature"} and
              type(root["key_id"]) is str and
              root["key_id"] == proof["key_id"] and
              type(root["public_pem"]) is bytes,
              "D1_ATTEST_SIGNER_ROLE_MISMATCH")
        key_ids.append(root["key_id"])
        key_fingerprints.append(_public_key_fingerprint(root["public_pem"]))
        check(_verify_signature(
            root["public_pem"],
            inventory_attestation_message(role, raw_statement, expected_sha),
            proof["signature"]), "D1_ATTEST_BAD_SIGNATURE")
    check(key_ids[0] != key_ids[1] and
          key_fingerprints[0] != key_fingerprints[1],
          "D1_ATTEST_SAME_SIGNER_FORBIDDEN")
    return {
        "status": "OFFLINE_INVENTORY_TEST_SIGNED_NOT_PRODUCTION_TRUSTED",
        "source_commit_sha": expected_sha,
        "inventory_statement_sha256": hashlib.sha256(raw_statement).hexdigest(),
        "complete_dependency_closure_attested": False,
        "production_trust_roots_enrolled": False,
        "actual_rpc_requests": 0,
    }


def consume_then_run_fake_once(source, evidence_root, *, permit_raw,
                               expected_sha, proofs, test_only_trust_roots,
                               checkout_root, reviewed_files, now,
                               raw_inventory_statement, inventory_signatures,
                               offline_test_registry_root,
                               test_only_fake_post_utc_clock=None):
    """Sole sequence: verify all test inputs -> O_EXCL consume -> FAKE only.

    This is NOT an implementation of production authorization. Because roots,
    time and registry path are injected, no caller can use this as evidence
    of real user consent. An irreversible marker remains after any exception.
    """
    checked = validate_offline_bundle(
        permit_raw, expected_sha, proofs, test_only_trust_roots,
        checkout_root, reviewed_files, now)
    statement = verify_test_inventory_attestation(
        permit_raw, expected_sha, checkout_root, raw_inventory_statement,
        inventory_signatures, test_only_trust_roots)
    permit = _strict_permit(permit_raw)
    check(isinstance(evidence_root, Path) and evidence_root.is_absolute()
          and evidence_root.is_dir() and not evidence_root.is_symlink()
          and evidence_root.stat().st_mode & 0o077 == 0
          and isinstance(offline_test_registry_root, Path) and
          offline_test_registry_root.is_absolute() and
          evidence_root.resolve() != offline_test_registry_root.resolve(),
          "D1_TEST_EVIDENCE_OR_REGISTRY_ROOT_INVALID")
    # Strict source whitelist and static signed fake archive cap BEFORE
    # consuming. The wrapped bundle repeats those checks; no live callback.
    from f0_l2_d1_coordinator import FakeSource, SealedMemoryHTTPSSource
    check(type(source) in (FakeSource, SealedMemoryHTTPSSource)
          and "reply" not in getattr(source, "__dict__", {})
          and "reply_over_memory_https" not in getattr(source, "__dict__", {})
          and permit["max_response_bytes"] == 2_000_000,
          "D1_TEST_SOURCE_OR_RAW_CAP_INVALID")
    registry = OfflineGrantRegistry(offline_test_registry_root)
    marker = registry.consume(permit["grant_id"],
                              checked["permit_sha256"])
    # Any failure AFTER this line leaves the marker spent; no refund/retry.
    result = run_gated_fake_session(
        source, evidence_root, permit_raw=permit_raw,
        expected_sha=expected_sha, proofs=proofs,
        test_only_trust_roots=test_only_trust_roots,
        checkout_root=checkout_root, reviewed_files=reviewed_files,
        now=now,
        test_only_fake_post_utc_clock=test_only_fake_post_utc_clock)
    return {
        "mode": "OFFLINE_TEST_ONLY_ONE_USE_FAKE_SESSION",
        "marker": marker,
        "inventory": statement,
        "session": result,
        "not_a_real_grant": True,
        "actual_rpc_requests": 0,
        "production": "NO_GO",
        "f0_status": "NOT_PASSED",
    }
