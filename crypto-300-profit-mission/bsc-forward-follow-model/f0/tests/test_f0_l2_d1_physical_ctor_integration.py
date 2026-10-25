"""D1 single-coordinator physical HTTPS constructor path, fully patched OFFLINE.

These tests never call a real HTTPS or socket constructor. No D2/D3 permit.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

F0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F0))

from f0_l2_d1_coordinator import FakeSource, run_fake_concurrent
from f0_l2_d1_concrete_https import (
    PatchedConstructorOfflineSource, send_live,
)
from f0_l2_d1_https import HOST, PORT


class PatchedPhysicalConstructorTests(unittest.TestCase):
    def scenario(self, *, source=None, fail_connect=False,
                 http_failure=None):
        source = source or PatchedConstructorOfflineSource(
            delay_ms=12, growth_bps=10.0)
        if type(source) is not PatchedConstructorOfflineSource:
            raise ValueError("TEST_REQUIRES_EXACT_SOURCE")
        records = []
        lock = threading.Lock()

        class Response:
            def __init__(self, frame):
                self.status, headers, self.body = frame
                self.headers = list(headers.items())

            def getheaders(self):
                return self.headers

            def read(self, size):
                return self.body[:size]

        with tempfile.TemporaryDirectory() as d:
            evidence = Path(d) / "evidence"
            evidence.mkdir(mode=0o700)

            class Connection:
                def __init__(self):
                    self.sock = None
                    self.payload = None
                    self.events = []

                def connect(self):
                    # Network constructor and real socket are both patched.
                    # Every physical CONNECT happens after a durable journal
                    # reservation has been written by the single coordinator.
                    self.events.append("connect")
                    rows = [json.loads(x) for x in
                            (evidence / "attempts.jsonl").read_text().splitlines()]
                    if not any(r["event"] == "RESERVE_UNKNOWN" for r in rows):
                        raise AssertionError("CONNECT_BEFORE_ANY_RESERVATION")
                    if fail_connect:
                        raise TimeoutError("OFFLINE_CONNECT_FAULT")
                    self.sock = object()

                def request(self, method, path, *, body, headers):
                    self.events.append("post")
                    self.payload = json.loads(body)
                    if method != "POST" or path != "/" or headers["Host"] != HOST:
                        raise AssertionError("UNREVIEWED_DESTINATION")
                    if headers["Accept-Encoding"] != "identity":
                        raise AssertionError("UNREVIEWED_ENCODING")
                    rows = [json.loads(x) for x in
                            (evidence / "attempts.jsonl").read_text().splitlines()]
                    if not any(r["event"] == "RESERVE_UNKNOWN"
                               and r["id"] == self.payload["id"] for r in rows):
                        raise AssertionError("POST_WITHOUT_MATCHING_RESERVATION")

                def getresponse(self):
                    self.events.append("response")
                    if self.payload is None:
                        raise AssertionError("RESPONSE_WITHOUT_POST")
                    status, headers, body = FakeSource.reply(source, self.payload)
                    if http_failure == "redirect":
                        status = 302
                        headers = {"location": "https://invalid.test/other",
                                   "content-type": "application/json"}
                    elif http_failure == "compression":
                        headers = dict(headers)
                        headers["content-encoding"] = "gzip"
                    elif http_failure == "read_failure":
                        raise TimeoutError("MEMORY_RESPONSE_READ_FAULT")
                    return Response((status, headers, body))

                def close(self):
                    self.events.append("close")
                    self.sock = None
                    with lock:
                        records.append((self.payload, tuple(self.events)))

            def patched_ctor(host, *, port, timeout, context):
                if (host, port) != (HOST, PORT):
                    raise AssertionError("UNREVIEWED_ORIGIN")
                if not 0 < timeout <= 5:
                    raise AssertionError("UNREVIEWED_TIMEOUT")
                if not context.check_hostname:
                    raise AssertionError("TLS_HOSTNAME_CHECK_DISABLED")
                return Connection()

            # Forbid *any* real socket, even accidental fall-through in
            # ssl/http.client. HTTPSConnection is explicitly patched too.
            with patch.object(socket, "create_connection",
                              side_effect=AssertionError("REAL_SOCKET_FORBIDDEN")):
                with patch("http.client.HTTPSConnection",
                           side_effect=patched_ctor):
                    report = run_fake_concurrent(
                        source, evidence, max_total=8, max_blocks=4,
                        max_refreshes=2, head_min_poll_age_ms=250,
                        window_ms=9000)
            rows = [json.loads(x) for x in
                    (evidence / "attempts.jsonl").read_text().splitlines()]
            raw_files = sorted((evidence / "raw_responses").glob("*.body"))
            raw_modes = [p.stat().st_mode & 0o077 for p in raw_files]
            self.last_raw_bodies = {p.name: p.read_bytes() for p in raw_files}
            return report, rows, records, raw_modes

    def test_patched_concrete_constructor_one_coordinator_three_slots(self):
        report, rows, records, modes = self.scenario()
        self.assertEqual(report["mode"],
                         "D1_OFFLINE_PATCHED_HTTPS_CTOR_NO_SOCKET_TEST_ONLY")
        self.assertEqual(report["network_requests"], 0)
        self.assertTrue(records)
        self.assertLessEqual(report["reserved"], 8)
        self.assertLessEqual(report["block_attempts"], 4)
        self.assertLessEqual(report["max_shared_slots"], 3)
        self.assertGreaterEqual(report["min_actual_fake_start_gap_ms"], 248.5)
        self.assertEqual(report["settled"], report["reserved"])
        self.assertEqual(report["unknown_after_stop"], 0)
        self.assertEqual(len(records), report["reserved"])
        self.assertTrue(all(x[-1] == "close" for _, x in records))
        self.assertTrue(all(mode == 0 for mode in modes))
        ordered = {}
        for i, item in enumerate(rows):
            if item["event"] == "RESERVE_UNKNOWN":
                ordered[item["id"]] = i
            if item["event"] == "SETTLE":
                self.assertLess(ordered[item["id"]], i)
                if item.get("raw_name"):
                    self.assertGreater(len(modes), 0)

    def test_unpatched_constructor_denied_before_connect(self):
        source = PatchedConstructorOfflineSource(delay_ms=0)
        called = []
        with patch.object(socket, "create_connection",
                          side_effect=AssertionError("REAL_SOCKET_FORBIDDEN")):
            with self.assertRaisesRegex(
                    ValueError, "D1_PATCHED_CTOR_REQUIRED_NO_REAL_NETWORK"):
                source.reply_over_memory_https(
                    {"jsonrpc": "2.0", "id": 1,
                     "method": "eth_chainId", "params": []},
                    lambda: called.append(True), 2.0,
                    reservation_guard=lambda _payload: None)
        self.assertEqual(called, [])

    def test_patched_constructor_refuses_missing_coordinator_receipt(self):
        source = PatchedConstructorOfflineSource(delay_ms=0)
        payload = {"jsonrpc": "2.0", "id": 1,
                   "method": "eth_chainId", "params": []}
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NO_CONNECT_EXPECTED")) as ctor:
            with self.assertRaisesRegex(
                    ValueError, "COORDINATOR_RESERVATION_REQUIRED"):
                source.reply_over_memory_https(payload, lambda: None, 2.0)
        self.assertEqual(ctor.call_count, 0)

    def test_invalid_reserved_request_cannot_reach_connect(self):
        source = PatchedConstructorOfflineSource(delay_ms=0)
        payload = {"jsonrpc": "2.0", "id": 1,
                   "method": "eth_chainId", "params": []}
        opened = []
        closed = []

        class Connection:
            sock = None
            def connect(self):
                opened.append(True)
                self.sock = object()
            def close(self):
                closed.append(True)

        def constructor(host, *, port, timeout, context):
            return Connection()

        def deny_reserved(_payload):
            raise ValueError("SAVED_RID_NOT_DURABLE")

        with patch("http.client.HTTPSConnection",
                   side_effect=constructor) as ctor:
            with self.assertRaisesRegex(
                    ValueError, "FAILED_NO_AUTO_RETRY"):
                source.reply_over_memory_https(
                    payload, lambda: None, 2.0,
                    reservation_guard=deny_reserved)
        # Even a constructor that performs I/O eagerly must not be
        # invoked when the coordinator's durable RID proof refuses.
        self.assertEqual(ctor.call_count, 0)
        self.assertFalse(opened)
        self.assertEqual(closed, [])

    def test_connect_fault_is_charged_once_and_never_retried(self):
        r, rows, records, _ = self.scenario(fail_connect=True)
        self.assertEqual(r["reserved"], 1)
        self.assertEqual(r["settled"], 1)
        self.assertEqual(r["block_attempts"], 0)
        self.assertEqual(r["stop"], "RPC_OR_HEAD_FAULT")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0][1], ("connect", "close"))
        self.assertEqual(
            [x["state"] for x in rows if x["event"] == "SETTLE"],
            ["FAILED"])

    def test_http_failure_does_not_become_chain_success(self):
        source = PatchedConstructorOfflineSource(
            delay_ms=10, growth_bps=10.0, fail_head_after=1)
        r, rows, records, _ = self.scenario(source=source)
        self.assertEqual(r["block_attempts"], 0)
        self.assertEqual(r["stop"], "RPC_OR_HEAD_FAULT")
        self.assertEqual(r["reserved"], r["settled"])
        self.assertTrue(records)

    def test_http_302_raw_saved_before_failed_settle_no_follow(self):
        report, rows, records, modes = self.scenario(http_failure="redirect")
        self.assertEqual(report["stop"], "RPC_OR_HEAD_FAULT")
        self.assertEqual(report["reserved"], 1)
        self.assertEqual(report["settled"], 1)
        self.assertEqual(report["contiguous_commits"], 0)
        self.assertEqual(report["network_requests"], 0)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0][1],
                         ("connect", "post", "response", "close"))
        reserve = [x for x in rows if x["event"] == "RESERVE_UNKNOWN"]
        settle = [x for x in rows if x["event"] == "SETTLE"]
        self.assertEqual(len(reserve), 1)
        self.assertEqual(len(settle), 1)
        self.assertLess(rows.index(reserve[0]), rows.index(settle[0]))
        row = settle[0]
        self.assertEqual(row["state"], "FAILED")
        self.assertIn("TRANSPORT_REJECTED_RAW", row["reason"])
        self.assertEqual(row["http_status"], 302)
        self.assertEqual(self.last_raw_bodies[row["raw_name"]],
                         self.last_raw_bodies["001.body"])
        self.assertEqual(row["raw_sha256"],
                         hashlib.sha256(self.last_raw_bodies[row["raw_name"]]).hexdigest())
        self.assertEqual(modes, [0])

    def test_compressed_http_raw_archived_but_never_accepted(self):
        report, rows, records, modes = self.scenario(http_failure="compression")
        self.assertEqual(report["stop"], "RPC_OR_HEAD_FAULT")
        self.assertEqual(report["reserved"], 1)
        self.assertEqual(report["settled"], 1)
        self.assertEqual(report["contiguous_commits"], 0)
        row = next(x for x in rows if x["event"] == "SETTLE")
        self.assertEqual(row["state"], "FAILED")
        self.assertIn("COMPRESSED_REFUSED", row["reason"])
        self.assertEqual(row["http_status"], 200)
        self.assertEqual(row["raw_sha256"],
                         hashlib.sha256(self.last_raw_bodies[row["raw_name"]]).hexdigest())
        self.assertEqual(len(self.last_raw_bodies), 1)
        self.assertEqual(modes, [0])

    def test_post_response_uncertainty_has_no_fabricated_raw(self):
        report, rows, records, modes = self.scenario(http_failure="read_failure")
        self.assertEqual(report["stop"], "RPC_OR_HEAD_FAULT")
        self.assertEqual(report["reserved"], 1)
        self.assertEqual(report["settled"], 1)
        self.assertEqual(report["contiguous_commits"], 0)
        row = next(x for x in rows if x["event"] == "SETTLE")
        self.assertEqual(row["state"], "FAILED")
        self.assertIn("TRANSPORT_FAILED_NO_RAW", row["reason"])
        self.assertNotIn("raw_sha256", row)
        self.assertEqual(self.last_raw_bodies, {})
        self.assertEqual(modes, [])

    def test_public_concrete_live_entry_remains_closed(self):
        with self.assertRaisesRegex(ValueError, "LIVE_DISABLED"):
            send_live()


if __name__ == "__main__":
    unittest.main()
