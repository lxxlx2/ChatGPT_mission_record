"""No external source or wallet data; exact captured receipt shape only."""
from pathlib import Path
import json
import stat
import tempfile
import unittest
from unittest.mock import patch

from mission_agent.mission_control.frank_buys import _read_usd_evidence
from mission_agent.signals.historical_usd_tick import capture_url
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
