"""Staged physical HTTPS uses ONE original three-slot coordinator, no socket."""
from __future__ import annotations

import hashlib
import http.client
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_coordinator import (
    FakeSource, GlobalStartGate, ExclusiveEvidence, run_fake_concurrent,
    _run_staged_physical_patched_offline)
from f0_l2_d2_physical_source_offline import (
    StagedPhysicalHTTPSReadOnlySource, send_live)
from f0_l2_d1_https import HOST, PORT


class StagedPhysicalHTTPSOneCoordinatorTests(unittest.TestCase):
    @staticmethod
    def source():
        return StagedPhysicalHTTPSReadOnlySource()

    @staticmethod
    def evidence(base):
        result = Path(base).resolve() / "evidence"
        result.mkdir(mode=0o700)
        return result

    @staticmethod
    def scope():
        return {"max_total": 2, "max_blocks": 1, "max_refreshes": 0,
                "head_min_poll_age_ms": 250, "spacing_ms": 250,
                "window_ms": 2800}

    def scenario(self, *, kind="ok"):
        with tempfile.TemporaryDirectory() as d:
            root = self.evidence(d)
            witness = []
            fake = FakeSource(delay_ms=0, first_head=1000, growth_bps=0)
            class Reply:
                def __init__(self, status, headers, data):
                    self.status = status
                    self.hdrs = list(headers.items())
                    self.data = data
                def getheaders(self):
                    return self.hdrs
                def read(self, amount):
                    return self.data[:amount]
            class Connection:
                def __init__(self):
                    self.sock = None
                    self.payload = None
                    self.connected = False
                def connect(self):
                    journal = [
                        json.loads(line) for line in
                        (root / "attempts.jsonl").read_text().splitlines()]
                    if not any(row["event"] == "RESERVE_UNKNOWN" for row in journal):
                        raise AssertionError("CONSTRUCTOR_WITHOUT_DURABLE_RESERVATION")
                    self.connected = True
                    self.sock = object()
                    witness.append(("connect", None))
                def request(self, method, path, *, body, headers):
                    self.payload = json.loads(body)
                    if (not self.connected or method != "POST" or
                            path != "/" or headers.get("Host") != HOST or
                            headers.get("Accept-Encoding") != "identity"):
                        raise AssertionError("WRONG_TEST_PHYSICAL_POST")
                    journal = [
                        json.loads(line) for line in
                        (root / "attempts.jsonl").read_text().splitlines()]
                    rid = self.payload["id"]
                    if not any(row["event"] == "RESERVE_UNKNOWN" and
                               row["id"] == rid for row in journal):
                        raise AssertionError("POST_WITHOUT_MATCHING_RID")
                    witness.append(("post", rid))
                def getresponse(self):
                    if self.payload is None:
                        raise AssertionError("RESPONSE_BEFORE_POST")
                    status, headers, data = FakeSource.reply(fake, self.payload)
                    if kind == "redirect":
                        status = 302
                        headers = {"location": "https://unapproved.invalid/",
                                   "content-type": "application/json"}
                    return Reply(status, headers, data)
                def close(self):
                    self.sock = None
                    witness.append(("close", self.payload["id"] if self.payload
                                    is not None else None))
            def patched_ctor(host, *, port, timeout, context):
                if (host != HOST or port != PORT or not 0 < timeout <= 5
                        or not context.check_hostname):
                    raise AssertionError("WRONG_TLS_ORIGIN")
                witness.append(("constructor", None))
                return Connection()
            with (
                patch("http.client.HTTPSConnection",
                      side_effect=patched_ctor),
                patch.object(socket, "create_connection",
                             side_effect=AssertionError("NO_REAL_SOCKET")),
            ):
                report = _run_staged_physical_patched_offline(
                    self.source(), root, **self.scope())
            rows = [
                json.loads(line) for line in
                (root / "attempts.jsonl").read_text().splitlines()]
            raws = {p.name: p.read_bytes() for p in
                    (root / "raw_responses").glob("*.body")}
            modes = [p.stat().st_mode & 0o077 for p in
                     (root / "raw_responses").glob("*.body")]
            return report, witness, rows, raws, modes

    def test_public_fake_entry_rejects_physical_type_before_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.evidence(d)
            with (
                patch.object(ExclusiveEvidence, "__init__",
                             side_effect=AssertionError("NO_WRITER")) as writer,
                patch("http.client.HTTPSConnection",
                      side_effect=AssertionError("NO_CONSTRUCTOR")) as ctor,
            ):
                with self.assertRaisesRegex(ValueError,
                        "D2_STAGED_SOURCE_CONSTRUCTOR_OR_AUTHORITY_DENIED"):
                    run_fake_concurrent(self.source(), root)
                writer.assert_not_called()
                ctor.assert_not_called()
            self.assertEqual(list(root.iterdir()), [])

    def test_unpatched_physical_constructor_denied_before_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.evidence(d)
            with patch.object(ExclusiveEvidence, "__init__",
                              side_effect=AssertionError("NO_WRITER")) as writer:
                with self.assertRaisesRegex(ValueError,
                        "D2_STAGED_SOURCE_CONSTRUCTOR_OR_AUTHORITY_DENIED"):
                    _run_staged_physical_patched_offline(
                        self.source(), root, **self.scope())
                writer.assert_not_called()
            self.assertEqual(list(root.iterdir()), [])

    def test_existing_single_coordinator_handles_distinct_physical_slot(self):
        report, witness, rows, raw, modes = self.scenario()
        self.assertEqual(report["mode"],
                         "D2_STAGED_PHYSICAL_HTTPS_PATCHED_NO_SOCKET_TEST_ONLY")
        self.assertEqual(report["network_requests"], 0)
        self.assertIsNone(report["synthetic_source_growth_bps"])
        self.assertEqual(report["reserved"], 2)
        self.assertEqual(report["settled"], 2)
        self.assertEqual(report["max_shared_slots"], 1)
        self.assertEqual(len([x for x in witness if x[0] == "post"]), 2)
        self.assertEqual(len([x for x in witness if x[0] == "constructor"]), 2)
        self.assertGreaterEqual(report["min_actual_fake_start_gap_ms"], 248.5)
        self.assertEqual(len(raw), 2)
        self.assertEqual(modes, [0, 0])
        reservations = [x for x in rows if x["event"] == "RESERVE_UNKNOWN"]
        settlements = [x for x in rows if x["event"] == "SETTLE"]
        for reserve in reservations:
            settle = next(x for x in settlements if x["id"] == reserve["id"])
            self.assertLess(rows.index(reserve), rows.index(settle))
            self.assertEqual(settle["raw_sha256"],
                             hashlib.sha256(raw[settle["raw_name"]]).hexdigest())

    def test_complete_redirect_raw_archived_but_never_committed(self):
        report, witness, rows, raw, modes = self.scenario(kind="redirect")
        self.assertEqual(report["reserved"], 1)
        self.assertEqual(report["settled"], 1)
        self.assertEqual(report["contiguous_commits"], 0)
        self.assertEqual(report["stop"], "RPC_OR_HEAD_FAULT")
        self.assertEqual(len([x for x in witness if x[0] == "post"]), 1)
        settlement = next(x for x in rows if x["event"] == "SETTLE")
        self.assertEqual(settlement["state"], "FAILED")
        self.assertIn("TRANSPORT_REJECTED_RAW", settlement["reason"])
        self.assertEqual(settlement["http_status"], 302)
        self.assertEqual(settlement["raw_sha256"],
                         hashlib.sha256(raw[settlement["raw_name"]]).hexdigest())
        self.assertEqual(modes, [0])

    def test_exact_source_no_callback_instance_override_or_subclass(self):
        source = self.source()
        with self.assertRaises((AttributeError, TypeError)):
            source.reply_transport_evidence_offline = lambda *_: None
        class Altered(StagedPhysicalHTTPSReadOnlySource):
            pass
        with tempfile.TemporaryDirectory() as d:
            root = self.evidence(d)
            with self.assertRaisesRegex(
                    ValueError, "D2_STAGED_SOURCE_EXACT_TYPE_REQUIRED"):
                _run_staged_physical_patched_offline(
                    Altered(), root, **self.scope())
            self.assertEqual(list(root.iterdir()), [])

    def test_direct_gate_with_real_ctor_cannot_start_any_send(self):
        gate = GlobalStartGate(250)
        with self.assertRaisesRegex(
                ValueError, "D2_STAGED_DURABLE_RESERVATION_PROOF_REQUIRED"):
            gate.run(
                {"jsonrpc": "2.0", "id": 1,
                 "method": "eth_chainId", "params": []},
                self.source(), block_head_deadline=None,
                dispatch_deadline=__import__("time").monotonic() + 5,
                timeout_ms=1000, reservation_guard=lambda _req: None)
        self.assertEqual(gate.starts, [])

    def test_direct_lower_gate_rejects_lambda_even_with_patched_https(self):
        gate = GlobalStartGate(250)
        with patch(
                "http.client.HTTPSConnection",
                side_effect=AssertionError("CONSTRUCTOR_MUST_NOT_OPEN")
                ) as ctor:
            with self.assertRaisesRegex(
                    ValueError, "D2_STAGED_DURABLE_RESERVATION_PROOF_REQUIRED"):
                gate.run(
                    {"jsonrpc": "2.0", "id": 1,
                     "method": "eth_chainId", "params": []},
                    self.source(), block_head_deadline=None,
                    dispatch_deadline=__import__("time").monotonic() + 5,
                    timeout_ms=1000, reservation_guard=lambda _req: None)
            ctor.assert_not_called()
        self.assertEqual(gate.starts, [])

    def test_direct_staged_transport_rejects_lambda_before_patched_tls(self):
        with patch(
                "http.client.HTTPSConnection",
                side_effect=AssertionError("CONSTRUCTOR_MUST_NOT_OPEN")
                ) as ctor:
            with self.assertRaisesRegex(
                    ValueError, "D2_STAGED_SOURCE_COORDINATOR_PROOF_REQUIRED"):
                self.source().reply_transport_evidence_offline(
                    {"jsonrpc": "2.0", "id": 1,
                     "method": "eth_chainId", "params": []},
                    lambda: None, 1.0, reservation_guard=lambda _req: None)
            ctor.assert_not_called()

    def test_public_live_entry_refuses_even_patched_test_source(self):
        with self.assertRaisesRegex(ValueError, "NOT_RELEASED_D2_D3"):
            send_live(self.source(), permit=True)


if __name__ == "__main__":
    unittest.main()
