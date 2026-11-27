"""No external source or wallet data; exact captured receipt shape only."""
from datetime import datetime, timezone
import hashlib
from http.server import HTTPServer
from pathlib import Path
import json
import stat
import tempfile
from threading import Thread
import time
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen

from mission_agent.mission_control.frank_buys import _read_usd_evidence
from mission_agent.mission_control.server import DashboardState, Handler
from mission_agent.signals.historical_usd_tick import capture_url
from mission_agent.signals.store import Ledger
import test_frank_staged_person_scope as signed_fixture
from scripts.frank_build_usd_evidence import build


AT = 1795737600


class EvidenceBuilderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.output = self.root / "new-local.json"
        self.raw = self.root / "capture.json"
        self.raw.write_text(json.dumps({"result": {"count": 1, "trades": [
            {"symbol": "SOL/USD", "base_asset": "SOL", "quote_asset": "USD", "trade_id": "TEST1",
             "trade_ts": "2026-11-27T00:00:00.2Z", "price": "112.25"}
        ]}}))
        self.receipt = ("SOL", str(AT), capture_url("SOL", AT), self.raw)
        network = patch("socket.socket.connect", side_effect=AssertionError("offline-only"))
        network.start()
        self.addCleanup(network.stop)

    def test_publish_new_private_receipt_and_preserve_v1_decimal_value(self):
        legacy = self.root / "v1.json"
        legacy.write_text('{"version":1,"records":[{"spent_usd":0.98345678901234567890}]}')
        old = legacy.read_bytes()
        self.assertEqual(build(self.output, [self.receipt], legacy=legacy), 1)
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o600)
        value = json.loads(self.output.read_bytes())
        self.assertEqual(value["records"], [{"spent_usd": "0.98345678901234567890"}])
        _, market, digest = _read_usd_evidence(self.output)
        self.assertEqual(str(market[("SOL", AT)]), "112.25")
        self.assertEqual(len(digest), 64)
        self.assertEqual(legacy.read_bytes(), old)
        previous = self.output.read_bytes()
        with self.assertRaises(FileExistsError):
            build(self.output, [self.receipt])
        self.assertEqual(self.output.read_bytes(), previous)
        self.assertFalse(list(self.root.glob(".frank-buy-usd-*")))

    def test_duplicate_or_wrong_second_does_not_publish_partial_input(self):
        conflicting = ("SOL", str(AT + 1), capture_url("SOL", AT + 1), self.raw)
        for args, reason in [
            ([self.receipt, self.receipt], "DUPLICATE_ASSET_AND_SECOND"),
            ([self.receipt, conflicting], "SOURCE_TRADE_INVALID"),
            ([("SOL", "-1", self.receipt[2], self.raw)], "INVALID_TRADE_SECOND"),
            ([("SOL", str(AT), "https://example.com/not-a-recorded-request", self.raw)], "CAPTURE_INVALID"),
        ]:
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(ValueError, reason):
                    build(self.output, args)
                self.assertFalse(self.output.exists())

    def test_offline_builder_bounds_inputs_without_printing_captured_data(self):
        self.raw.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, "LOCAL_INPUT_EXCEEDS_LIMIT"):
            build(self.output, [self.receipt])
        with self.assertRaisesRegex(ValueError, "LOCAL_REGULAR_FILE_REQUIRED"):
            build(self.output, [(*self.receipt[:3], self.root)])
        self.assertFalse(self.output.exists())

class DashboardUSDIntegrationTest(unittest.TestCase):
    def test_saved_input_through_builder_and_real_loopback_read_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prod, control = (root/name for name in ("isolated-prod", "isolated-control"))
            prod.mkdir()
            control.mkdir()
            db = prod / "forward.sqlite"
            ledger = Ledger(db)
            try:
                with patch.object(signed_fixture, "NOW", int(time.time()) - 60):
                    signed_fixture.qualification(control / "frank-buy-qualifications.json")
                    covered = signed_fixture.tx(ledger, "frank", signed_fixture.A1, 1, 4)
                    adjacent = signed_fixture.tx(ledger, "frank", signed_fixture.A1, 2, 4)
                    at = signed_fixture.NOW - 499
            finally:
                ledger.db.close()
            before = hashlib.sha256(db.read_bytes()).digest()
            raw = root / "local-usdc.json"
            stamp = datetime.fromtimestamp(at, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            raw.write_text(json.dumps({"result": {"count": 1, "trades": [
                {"symbol": "USDC/USD", "base_asset": "USDC", "quote_asset": "USD",
                 "trade_id": "LOCAL1", "trade_ts": stamp + ".01Z", "price": "0.987"}
            ]}}))
            build(control / "frank-buy-usd-evidence.json", [("USDC", str(at), capture_url("USDC", at), raw)])

            class FixtureHandler(Handler):
                state = DashboardState(prod, control)

            with HTTPServer(("127.0.0.1", 0), FixtureHandler) as server:
                thread = Thread(target=server.serve_forever)
                thread.start()
                try:
                    endpoint = f"http://127.0.0.1:{server.server_port}/api/frank-buys?days=all"
                    request = Request(endpoint, headers={"X-Frank-Research-Read": "1"})
                    with urlopen(request, timeout=3) as response:
                        doc = json.load(response)
                finally:
                    server.shutdown()
                    thread.join()
            self.assertEqual(doc["status"], "LOCAL_EVIDENCE_ONLY")
            rows = {row["signature"]: row for row in doc["rows"]}
            self.assertEqual(set(rows), {covered, adjacent})
            self.assertEqual(rows[covered]["estimated_spent_usd"], "1.974")
            self.assertEqual(rows[covered]["estimated_entry_price_usd"], "0.4935")
            for row in rows.values():
                self.assertIsNone(row["spent_usd"])
                self.assertIsNone(row["entry_price_usd"])
                self.assertFalse({"raw_base64", "source_sha256", "source_url"} & row.keys())
            self.assertNotIn("estimated_spent_usd", rows[adjacent])
            self.assertEqual(hashlib.sha256(db.read_bytes()).digest(), before)
