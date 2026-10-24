"""D1 candidate REAL sender D2/D3 structural contract; always NO LIVE."""
from __future__ import annotations

from datetime import timedelta
from hashlib import sha256
import http.client
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_f0_l2_d1_protected_mac_entry as mac_fixture
from f0_l2_d1_real_sender_contract import (
    D3_SCHEMA, bind_real_https_candidate_offline,
    require_real_sender_release, send_live,
)
from f0_l2_d1_protected_mac_entry import (
    inspect_real_https_sender_candidate_offline,)


class RealSenderContractTests(unittest.TestCase):
    def setUp(self):
        self.fixture = mac_fixture.MacEntryNoNetworkTests(
            "test_actual_mac_entry_scope_has_no_grant_or_send_and_fixed_root")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.f = self.fixture.f
        self.registry = self.fixture.registry
        self.out = self.f.out
        self.manifest = "a" * 64
        self.fixture.mock_runtime.update({
            "tracked_source_manifest_sha256": self.manifest,
        })
        self.permit = json.loads(self.f.raw)
        self.intent = {
            key: self.permit[key] for key in (
                "approved_commit_sha", "grant_id", "window_start_utc",
                "window_end_utc", "endpoint", "chain_id", "methods",
                "read_only", "free_only", "no_retries", "no_ws", "background",
                "max_total_attempts", "max_block_reads",
                "max_head_refreshes", "max_inflight", "min_start_gap_ms",
                "head_ttl_ms", "request_timeout_ms", "max_response_bytes",
                "max_dispatch_seconds",
            )
        }
        self.intent.update({
            "schema": D3_SCHEMA,
            "permit_sha256": sha256(self.f.raw).hexdigest(),
            "run_id": "d3-independent-test-run-0001",
            "source_manifest_sha256": self.manifest,
            "execute_once": True,
        })

    def bytes(self, intent=None):
        return json.dumps(intent if intent is not None else self.intent,
                          separators=(",", ":"), sort_keys=True).encode()

    def inspect(self, *, intent=None, permit=None, at=None, **overrides):
        class UTCClock:
            @staticmethod
            def now(_tz):
                return at if at is not None else self.f.now
        with patch(
            "f0_l2_d1_protected_mac_entry.platform.system",
            return_value="Darwin",
        ), patch(
            "f0_l2_d1_protected_mac_entry.datetime", UTCClock,
        ), patch(
            "f0_l2_d1_protected_mac_entry.PRIVATE_FIXED_REGISTRY",
            self.registry,
        ), patch(
            "f0_l2_d1_protected_mac_entry._os_user_home",
            return_value=self.fixture.home,
        ), patch(
            "f0_l2_d1_protected_mac_entry.review_loaded_runtime_offline",
            return_value=self.fixture.mock_runtime,
        ), patch(
            "http.client.HTTPSConnection",
            side_effect=AssertionError("D1_FORBIDS_REAL_HTTPS"),
        ) as conn:
            out = inspect_real_https_sender_candidate_offline(
                self.f.repo, self.f.sha,
                permit if permit is not None else self.f.raw,
                self.bytes(intent), evidence_root=self.out)
            conn.assert_not_called()
            return out

    def test_bound_candidate_still_denies_network_and_real_sender(self):
        report = self.inspect()
        self.assertEqual(report["candidate"]["approved_commit_sha"],
                         self.f.sha)
        self.assertEqual(report["candidate"]["slots"], 3)
        self.assertEqual(report["candidate"]["coordinator"],
                         "EXISTING_SINGLE_GLOBAL_3_SLOT_ONLY")
        self.assertEqual(report["candidate"]["endpoint"],
                         "https://bsc-dataseed.bnbchain.org")
        self.assertEqual(report["candidate"]["max_attempts"], 9)
        self.assertEqual(report["candidate"]["min_actual_post_gap_ms"], 250)
        self.assertEqual(report["candidate"]["actual_rpc_calls"], 0)
        self.assertFalse(report["candidate"]["real_https_enabled"])
        self.assertFalse(report["d2_signed_approval_verified"])
        self.assertFalse(report["d3_signed_execution_approved"])
        self.assertFalse(report["production_marker_consumed"])
        self.assertEqual(report["decision"], "D1_BLOCKED_AUTHORITY")
        self.assertEqual(list(self.registry.iterdir()), [])
        self.assertEqual(list(self.out.iterdir()), [])

    def test_narrower_budget_cannot_increase_capacity_or_dispatch_rate(self):
        low = dict(self.intent, max_total_attempts=5,
                   max_block_reads=3, max_head_refreshes=0,
                   max_dispatch_seconds=8, min_start_gap_ms=500)
        info = self.inspect(intent=low)["candidate"]
        self.assertEqual(info["max_attempts"], 5)
        self.assertEqual(info["min_actual_post_gap_ms"], 500)
        for update in (
            {"max_total_attempts": 10},
            {"max_inflight": 4},
            {"min_start_gap_ms": 249},
            {"request_timeout_ms": 6000},
            {"max_response_bytes": 2000001},
            {"max_dispatch_seconds": 13},
            {"max_head_refreshes": 5},
        ):
            with self.subTest(update=update):
                with self.assertRaises(ValueError):
                    self.inspect(intent=dict(self.intent, **update))
        self.assertFalse(list(self.registry.iterdir()))

    def test_identity_digest_source_manifest_and_nonce_cannot_diverge(self):
        for update in (
            {"approved_commit_sha": "f" * 40},
            {"permit_sha256": "f" * 64},
            {"source_manifest_sha256": "f" * 64},
            {"grant_id": "different-grant-0001"},
            {"run_id": self.permit["grant_id"]},
            {"run_id": "x"},
        ):
            with self.subTest(update=update):
                with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
                    self.inspect(intent=dict(self.intent, **update))
        self.assertFalse(list(self.registry.iterdir()))

    def test_runtime_manifest_or_code_sha_mismatch_denied(self):
        original = self.fixture.mock_runtime["tracked_source_manifest_sha256"]
        self.fixture.mock_runtime["tracked_source_manifest_sha256"] = "f" * 64
        try:
            with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
                self.inspect()
        finally:
            self.fixture.mock_runtime["tracked_source_manifest_sha256"] = original
        with self.assertRaisesRegex(ValueError, "CODE_SHA_MISMATCH"):
            bind_real_https_candidate_offline(
                self.f.raw, self.bytes(), "f" * 40, self.f.now,
                actual_source_manifest_sha256=self.manifest)

    def test_candidate_not_a_signature_and_cannot_activate_sender(self):
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NO_SOCKET")) as conn:
            with self.assertRaisesRegex(ValueError, "NOT_RELEASED_D2_D3"):
                require_real_sender_release(
                    permit_raw=self.f.raw, intent_raw=self.bytes(),
                    injected_trust_root={"user": "attacker"})
            with self.assertRaisesRegex(ValueError, "NOT_RELEASED_D2_D3"):
                send_live(run=True, trusted=True)
            from f0_l2_d1_protected_mac_entry import send_live as entry
            with self.assertRaisesRegex(ValueError, "D2_D3_REQUIRED"):
                entry(run=True)
            conn.assert_not_called()
        self.assertFalse(list(self.registry.iterdir()))
        self.assertFalse(list(self.out.iterdir()))

    def test_expired_candidate_or_d3_window_change_denied(self):
        with self.assertRaisesRegex(ValueError, "WINDOW_INACTIVE"):
            self.inspect(at=self.f.now + timedelta(hours=1))
        with self.assertRaisesRegex(ValueError, "WINDOW_MISMATCH"):
            self.inspect(intent=dict(
                self.intent, window_end_utc="2026-10-23T08:01:01Z"))
        self.assertFalse(list(self.registry.iterdir()))

    def test_d3_malformed_duplicate_and_extra_field_refused(self):
        malformed = dict(self.intent, execute_once=False)
        with self.assertRaisesRegex(ValueError, "TRANSPORT_SCOPE_INVALID"):
            self.inspect(intent=malformed)
        with self.assertRaisesRegex(ValueError, "FIELD_SET_INVALID"):
            self.inspect(intent=dict(self.intent, enable_live=True))
        duplicate = self.bytes()[:-1] + b',"run_id":"second-run-id-0001"}'
        with self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_FIELD"):
            bind_real_https_candidate_offline(
                self.f.raw, duplicate, self.f.sha, self.f.now,
                actual_source_manifest_sha256=self.manifest)

    def test_strict_types_and_non_enforceable_smaller_raw_cap_denied(self):
        for update in (
            {"max_total_attempts": True},
            {"max_inflight": True},
            {"min_start_gap_ms": True},
        ):
            with self.subTest(update=update):
                with self.assertRaises(ValueError):
                    self.inspect(intent=dict(self.intent, **update))
        with self.assertRaisesRegex(ValueError, "RAW_CAP_NOT_ENFORCEABLE"):
            self.inspect(intent=dict(self.intent, max_response_bytes=1_000_000))
        self.assertEqual(list(self.registry.iterdir()), [])

    def test_no_test_output_child_marker_or_socket_from_inspection(self):
        with self.assertRaisesRegex(ValueError, "RELEASE_CONSTANTS_INVALID"):
            with patch(
                "f0_l2_d1_protected_mac_entry._D2_REVIEWED_PERMIT_SHA256",
                "a" * 64,
            ):
                self.inspect()
        self.assertFalse(list(self.registry.iterdir()))
        self.assertFalse(list(self.out.iterdir()))


if __name__ == "__main__":
    unittest.main()
