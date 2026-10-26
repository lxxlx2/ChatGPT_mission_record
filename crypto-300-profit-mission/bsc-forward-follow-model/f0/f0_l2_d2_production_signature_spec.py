"""PROPOSED production D2/D3 signing byte-format specification, NOT an issuer.

Pure deterministic message encoding only: no signing, verification, trust-root
enrollment, human identity claims, marker, filesystem or network. The proposed
domain is distinct from the reviewed D1/D2-B TEST-ONLY domains and must receive
its OWN governance and independent source review before any real signature.
"""
from __future__ import annotations

import re
import struct

HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9_-]{12,80}\Z")
D2_PROPOSED_DOMAIN = b"bsc-f0-d2-production-permit-PROPOSAL-v1"
D3_PROPOSED_DOMAIN = b"bsc-f0-d3-production-once-PROPOSAL-v1"
ENDPOINT = "https://bsc-dataseed.bnbchain.org"
CHAIN_ID = "56"
METHODS = "eth_chainId,eth_blockNumber,eth_getBlockByNumber"


def _require(ok: bool, label: str):
    if not ok:
        raise ValueError(label)


def _validated_ascii(value: str, pattern, label: str) -> bytes:
    _require(type(value) is str and pattern.fullmatch(value) is not None,
             label)
    return value.encode("ascii")


def _encode_fields(domain: bytes, fields: tuple[tuple[str, bytes], ...]) -> bytes:
    """Unambiguous counted ASCII encoding; no JSON rewrite or delimiters.

    4-byte big-endian length before each name and value, exact field count,
    explicit separation of D2 user/reviewer vs D3 operator domains.
    """
    _require(type(domain) is bytes and domain in
             (D2_PROPOSED_DOMAIN, D3_PROPOSED_DOMAIN),
             "D2_SPEC_UNREVIEWED_DOMAIN")
    _require(type(fields) is tuple and len(fields) <= 16,
             "D2_SPEC_FIELD_COUNT_INVALID")
    parts = [struct.pack(">I", len(domain)), domain,
             struct.pack(">I", len(fields))]
    seen = set()
    for name, value in fields:
        _require(type(name) is str and name.isascii()
                 and name.isidentifier() and name not in seen
                 and type(value) is bytes and len(value) <= 8192,
                 "D2_SPEC_FIELD_INVALID")
        seen.add(name)
        encoded_name = name.encode("ascii")
        parts.extend((struct.pack(">I", len(encoded_name)), encoded_name,
                      struct.pack(">I", len(value)), value))
    return b"".join(parts)


def proposed_d2_signing_bytes(*, role: str, grant_id: str,
                              permit_sha256: str, reviewed_sha: str,
                              source_manifest_sha256: str) -> bytes:
    """One role-specific D2 bytestring; NOT a validated production permit."""
    _require(type(role) is str and role in ("user", "reviewer"),
             "D2_SPEC_ROLE_INVALID")
    return _encode_fields(D2_PROPOSED_DOMAIN, (
        ("role", role.encode("ascii")),
        ("grant_id", _validated_ascii(grant_id, IDENTIFIER,
                                      "D2_SPEC_GRANT_ID_INVALID")),
        ("permit_raw_sha256", _validated_ascii(permit_sha256, HEX64,
                                               "D2_SPEC_DIGEST_INVALID")),
        ("reviewed_git_sha", _validated_ascii(reviewed_sha, HEX40,
                                              "D2_SPEC_SHA_INVALID")),
        ("source_manifest_sha256", _validated_ascii(
            source_manifest_sha256, HEX64, "D2_SPEC_MANIFEST_INVALID")),
        ("chain_id", CHAIN_ID.encode("ascii")),
        ("endpoint", ENDPOINT.encode("ascii")),
        ("methods", METHODS.encode("ascii")),
    ))


def proposed_d3_signing_bytes(*, grant_id: str, run_id: str,
                              intent_sha256: str, permit_sha256: str,
                              reviewed_sha: str,
                              source_manifest_sha256: str) -> bytes:
    """Independent ONE-SHOT operator proposal, not live run authority."""
    grant = _validated_ascii(grant_id, IDENTIFIER,
                              "D3_SPEC_GRANT_ID_INVALID")
    run = _validated_ascii(run_id, IDENTIFIER,
                            "D3_SPEC_RUN_ID_INVALID")
    _require(grant != run, "D3_SPEC_RUN_GRANT_ID_COLLISION")
    return _encode_fields(D3_PROPOSED_DOMAIN, (
        ("role", b"operator"),
        ("grant_id", grant),
        ("run_id", run),
        ("intent_raw_sha256", _validated_ascii(
            intent_sha256, HEX64, "D3_SPEC_INTENT_DIGEST_INVALID")),
        ("permit_raw_sha256", _validated_ascii(
            permit_sha256, HEX64, "D3_SPEC_PERMIT_DIGEST_INVALID")),
        ("reviewed_git_sha", _validated_ascii(
            reviewed_sha, HEX40, "D3_SPEC_SHA_INVALID")),
        ("source_manifest_sha256", _validated_ascii(
            source_manifest_sha256, HEX64, "D3_SPEC_MANIFEST_INVALID")),
        ("chain_id", CHAIN_ID.encode("ascii")),
        ("endpoint", ENDPOINT.encode("ascii")),
        ("methods", METHODS.encode("ascii")),
    ))


def send_live(*_args, **_kwargs):
    raise ValueError("D2_PRODUCTION_SIGNATURE_SPEC_NOT_AUTHORIZATION")
