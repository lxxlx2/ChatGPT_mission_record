"""Offline-only constraints for a future owner-authored BSC once trial."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import socket
import unittest
from unittest.mock import patch

from f0_l1_http_wire import MAX_BODY_BYTES
from f0_l2_d1_physical_foreground_scope import (
    check_physical_foreground_scope, send_live, SCHEMA, METHODS, ENDPOINT,
)

FIXED_SHA = "a" * 40


def example():
    now = datetime.now(timezone.utc)
    return {
        "schema": SCHEMA,
        "approved_commit_sha": FIXED_SHA,
        "grant_id": "operator-one-shot-0001",
        "endpoint": ENDPOINT,
        "methods": list(METHODS),
        "anchor_initial_head": True,
        "max_total": 6,
        "max_blocks": 3,
        "max_refreshes": 1,
        "slots": 3,
        "spacing_ms": 250,
        "head_ttl_ms": 4000,
        "head_min_poll_age_ms": 250,
        "window_ms": 15000,
        "timeout_ms": 3000,
        "max_body_bytes": MAX_BODY_BYTES,
        "hard_seconds": 25,
        "window_start_utc": (now + timedelta(seconds=3)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "window_end_utc": (now + timedelta(seconds=23)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
    }


def pack(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


class PhysicalOnceScopeTests(unittest.TestCase):
    def deny(self, data, error):
        with self.assertRaisesRegex(ValueError, error):
            check_physical_foreground_scope(
                pack(data), independently_reviewed_sha=FIXED_SHA)

    def test_exact_scope_fingerprint_no_permission(self):
        d = example()
        raw = pack(d)
        with (
            patch("socket.create_connection",
                  side_effect=AssertionError("REAL_TCP_FORBIDDEN")) as tcp,
            patch("socket.getaddrinfo",
                  side_effect=AssertionError("REAL_DNS_FORBIDDEN")) as dns,
        ):
            r = check_physical_foreground_scope(
                raw, independently_reviewed_sha=FIXED_SHA)
        self.assertEqual(r["state"], "VALID_SCOPE_ONLY_NOT_AN_AUTHORIZATION")
        self.assertEqual(r["scope_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertFalse(r["real_rpc_permitted"])
        self.assertFalse(r["consent_consumed"])
        self.assertFalse(r["background_enabled"])
        tcp.assert_not_called()
        dns.assert_not_called()

    def test_method_host_and_anchor_cannot_be_changed(self):
        for key, replacement in (
            ("endpoint", "https://evil.example"),
            ("methods", ["eth_sendRawTransaction"]),
            ("methods", list(METHODS) + ["eth_getLogs"]),
            ("anchor_initial_head", False),
            ("anchor_initial_head", 1),
            ("approved_commit_sha", "b" * 40),
            ("grant_id", "bad"),
        ):
            with self.subTest(key=key, value=replacement):
                d = example()
                d[key] = replacement
                self.deny(d, "F0_PHYSICAL_SCOPE_IDENTITY_OR_METHOD_DENIED")

    def test_false_budget_or_boolean_integers_denied(self):
        for key, value in (
            ("max_total", True),
            ("max_total", 33),
            ("max_blocks", 25),
            ("max_refreshes", 6),
            ("slots", 2),
            ("spacing_ms", 249),
            ("timeout_ms", 5001),
            ("max_body_bytes", MAX_BODY_BYTES + 1),
            ("hard_seconds", 76),
        ):
            with self.subTest(key=key, value=value):
                d = example()
                d[key] = value
                self.deny(d, "F0_PHYSICAL_SCOPE_BUDGET_INVALID")

    def test_cross_field_incoherence_stops_preflight(self):
        for mutations in (
            {"max_total": 9},
            {"head_min_poll_age_ms": 3999, "head_ttl_ms": 3500},
            {"window_ms": 25000, "hard_seconds": 25},
        ):
            with self.subTest(mutations=mutations):
                d=example()
                d.update(mutations)
                self.deny(d, "F0_PHYSICAL_SCOPE_INCOHERENT")

    def test_invalid_utc_contract_denied(self):
        now=datetime.now(timezone.utc)
        for a,b in ((-300,-280), (5,66), (30,29), (620,640)):
            with self.subTest(start=a,end=b):
                d=example()
                d["window_start_utc"]=(now+timedelta(seconds=a)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ")
                d["window_end_utc"]=(now+timedelta(seconds=b)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ")
                self.deny(d, "F0_PHYSICAL_SCOPE_UTC_DENIED")

    def test_duplicate_fields_unknown_field_and_big_manifest_denied(self):
        raw=pack(example())
        bad=raw.replace(b'"slots":3', b'"slots":3,"slots":3')
        with self.assertRaisesRegex(ValueError,
                                    "F0_PHYSICAL_SCOPE_DUPLICATE_JSON_KEY"):
            check_physical_foreground_scope(bad,independently_reviewed_sha=FIXED_SHA)
        d=example()
        d["execute_live_without_consent"]=True
        self.deny(d, "F0_PHYSICAL_SCOPE_EXACT_FIELDS_REQUIRED")
        with self.assertRaisesRegex(ValueError,"F0_PHYSICAL_SCOPE_INPUT_INVALID"):
            check_physical_foreground_scope(b"x"*4097,independently_reviewed_sha=FIXED_SHA)

    def test_review_sha_is_external_constraint(self):
        raw=pack(example())
        for sha in ("z"*40, FIXED_SHA+"0", "b"*40):
            with self.subTest(sha=sha):
                with self.assertRaises(ValueError):
                    check_physical_foreground_scope(
                        raw,independently_reviewed_sha=sha)

    def test_no_live_entry_is_released_by_valid_scope(self):
        check_physical_foreground_scope(
            pack(example()),independently_reviewed_sha=FIXED_SHA)
        with self.assertRaisesRegex(ValueError,"LAUNCH_NOT_RELEASED"):
            send_live()

    def test_not_permitted_to_replace_test_capability_or_add_grant_fields(self):
        d=example()
        for key in ("_REVIEW_TEST_ONLY_CAPABILITY",
                    "production_trust_roots", "permit_signed", "nonce"):
            with self.subTest(key=key):
                bad=dict(d)
                bad[key]="user-claims-approval"
                self.deny(bad,"F0_PHYSICAL_SCOPE_EXACT_FIELDS_REQUIRED")


if __name__=="__main__":
    unittest.main()
