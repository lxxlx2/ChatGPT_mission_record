"""BSC F0 physical foreground read-only trial scope: STRICT CHECK-ONLY.

This is a data contract for a future original-3-slot OS child, NOT a launcher.
No HTTP, no subprocess, no signing, no TEST grant impersonation. No saved
scope or Python-private object is actual user authorization. In particular,
validating this contract MUST NOT bypass the PR231 genuine-HTTPS hard deny.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import re

from f0_l1_http_wire import MAX_BODY_BYTES
from f0_l2_d1_preflight import parse_utc_timestamp

SCHEMA = "bsc-f0-physical-once-foreground-scope-v1"
ENDPOINT = "https://bsc-dataseed.bnbchain.org"
METHODS = ("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber")
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
GRANT = re.compile(r"[a-zA-Z0-9_-]{12,80}\Z")
FIELDS = frozenset((
    "schema", "approved_commit_sha", "grant_id", "endpoint", "methods",
    "anchor_initial_head", "max_total", "max_blocks", "max_refreshes",
    "slots", "spacing_ms", "head_ttl_ms", "head_min_poll_age_ms",
    "window_ms", "timeout_ms", "max_body_bytes",
    "hard_seconds", "window_start_utc", "window_end_utc",
))


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("F0_PHYSICAL_SCOPE_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def check_physical_foreground_scope(raw: bytes, *,
                                    independently_reviewed_sha: str) -> dict:
    """Reject invalid experiment requests WITHOUT network or consent writes.

    SHA must come from the independent fixed review, not from the candidate
    document itself. A future operator launcher must additionally verify
    the clean exact Git checkout, source files, actual OS user, and one-use
    consumed marker before ANY true TLS constructor. This function does not
    perform those actions and must not be used as a release token.
    """
    if (type(raw) is not bytes or not 1 <= len(raw) <= 4096
            or type(independently_reviewed_sha) is not str
            or not SHA40.fullmatch(independently_reviewed_sha)):
        raise ValueError("F0_PHYSICAL_SCOPE_INPUT_INVALID")
    try:
        doc = json.loads(raw, object_pairs_hook=_unique_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("F0_PHYSICAL_SCOPE_JSON_INVALID") from exc
    if type(doc) is not dict or set(doc) != FIELDS:
        raise ValueError("F0_PHYSICAL_SCOPE_EXACT_FIELDS_REQUIRED")
    if (doc["schema"] != SCHEMA
            or doc["approved_commit_sha"] != independently_reviewed_sha
            or type(doc["approved_commit_sha"]) is not str
            or not SHA40.fullmatch(doc["approved_commit_sha"])
            or type(doc["grant_id"]) is not str
            or not GRANT.fullmatch(doc["grant_id"])
            or doc["endpoint"] != ENDPOINT
            or type(doc["methods"]) is not list
            or doc["methods"] != list(METHODS)
            or doc["anchor_initial_head"] is not True):
        raise ValueError("F0_PHYSICAL_SCOPE_IDENTITY_OR_METHOD_DENIED")

    integers = {
        "max_total": (3, 32),
        "max_blocks": (1, 24),
        "max_refreshes": (0, 5),
        "slots": (3, 3),
        "spacing_ms": (250, 5000),
        "head_ttl_ms": (500, 4000),
        "head_min_poll_age_ms": (250, 3999),
        "window_ms": (1000, 60000),
        "timeout_ms": (250, 5000),
        "max_body_bytes": (MAX_BODY_BYTES, MAX_BODY_BYTES),
        "hard_seconds": (3, 75),
    }
    for key, (minimum, maximum) in integers.items():
        val = doc[key]
        if type(val) is not int or not minimum <= val <= maximum:
            raise ValueError("F0_PHYSICAL_SCOPE_BUDGET_INVALID:" + key)
    if (doc["max_total"] >
            doc["max_blocks"] + doc["max_refreshes"] + 3
            or doc["head_min_poll_age_ms"] >= doc["head_ttl_ms"]
            or doc["window_ms"] + doc["timeout_ms"] + 2000 >
            doc["hard_seconds"] * 1000):
        raise ValueError("F0_PHYSICAL_SCOPE_INCOHERENT")

    start = parse_utc_timestamp(doc["window_start_utc"])
    end = parse_utc_timestamp(doc["window_end_utc"])
    now = datetime.now(timezone.utc)
    if (not timedelta(0) < end - start <= timedelta(seconds=60)
            or not now - timedelta(seconds=2) <= start <=
            now + timedelta(minutes=10)
            or end <= now):
        raise ValueError("F0_PHYSICAL_SCOPE_UTC_DENIED")

    return {
        "state": "VALID_SCOPE_ONLY_NOT_AN_AUTHORIZATION",
        "scope_sha256": hashlib.sha256(raw).hexdigest(),
        "reviewed_sha": independently_reviewed_sha,
        "grant_id_sha256": hashlib.sha256(doc["grant_id"].encode()).hexdigest(),
        "method_count": len(METHODS),
        "max_total": doc["max_total"],
        "max_blocks": doc["max_blocks"],
        "max_refreshes": doc["max_refreshes"],
        "anchor_initial_head": True,
        "real_rpc_permitted": False,
        "consent_consumed": False,
        "background_enabled": False,
    }


def send_live(*_args, **_kwargs):
    raise ValueError("F0_PHYSICAL_FOREGROUND_LAUNCH_NOT_RELEASED")
