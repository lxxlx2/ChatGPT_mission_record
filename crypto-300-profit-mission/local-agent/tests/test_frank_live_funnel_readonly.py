"""Genuine native localhost HTTP and privacy tests for read-only Frank funnel."""
from __future__ import annotations

import importlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
m = importlib.import_module("frank_live_funnel_readonly")
FAKE_MINT = "7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump"
SECRET = "PRIVATE_SIDECAR_WALLET_DO_NOT_EXPORT_28c8f3"


class Handler(BaseHTTPRequestHandler):
    routes = {}
    seen = []

    def do_GET(self):
        type(self).seen.append((self.command, self.path))
        status, obj = type(self).routes.get(self.path, (404, {"error": SECRET}))
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass  # An oversized fake body is deliberately refused before reading.

    def do_POST(self):
        raise AssertionError("POST_NOT_PERMITTED")

    def log_message(self, *_):
        pass


class FrankReadOnlyTests(unittest.TestCase):
    def setUp(self):
        Handler.seen = []
        Handler.routes = {
            "/api/runtime": (200, {"status": "LIVE", "heartbeat_age_seconds": 21,
                                   "pid": 123, "pid_alive": True}),
            "/api/control-health": (200, {"secret": SECRET, "outbox_id": FAKE_MINT}),
            "/api/coverage": (200, {"status": "OK", "chain_completeness_verified": False,
                                   "latest_indexed_block_time": time.time() - 120,
                                   "windows": {"24h": {"indexed_signatures": 12,
                                                      "recognized_trades": 6,
                                                      "recognized_buys": 3,
                                                      "recognized_sells": 3,
                                                      "unknown_needs_review": 2}}}),
            "/api/candidates": (200, [{"mint": FAKE_MINT, "signature": SECRET,
                                      "decision": "BUY", "position_state": "CLOSED",
                                      "latest_side": "SELL",
                                      "latest_at": time.time() - 100}]),
            "/api/frank-observed-watchlist": (
                200, {"status": "OK", "rows": [
                    {"mint": FAKE_MINT, "watch_state": "MODEL_OPEN", "signature": SECRET}]}),
            "/api/follow-opportunities": (
                200, {"status": "OK", "eligible": [], "eligible_count": 0,
                      "not_followed": [{"mint": FAKE_MINT, "raw": SECRET,
                                        "exclusion_reason": "QUOTE_STALE"}],
                      "excluded_count": 1, "as_of_epoch": time.time()}),
        }
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_six_real_gets_and_private_zip(self):
        report = m.sample(self.server.server_port)
        self.assertEqual(report["local_f01_interface"],
                         "F01_SOURCE_READ_OK_ELIGIBILITY_NOT_TRADE_AUTHORIZATION")
        source = report["endpoints"]
        self.assertEqual(source["/api/coverage"]["aggregate"]["windows"]["24h"]["indexed_signatures"], 12)
        self.assertEqual(source["/api/candidates"]["aggregate"]["stored_decision_labels_NOT_CURRENT_BUY"],
                         {"BUY": 1})
        self.assertEqual(source["/api/follow-opportunities"]["aggregate"]["exclusion_reasons"],
                         {"QUOTE_STALE": 1})
        self.assertEqual(len(Handler.seen), 6)
        self.assertEqual({method for method, _ in Handler.seen}, {"GET"})
        with tempfile.TemporaryDirectory() as temp:
            location = Path(temp) / "aggregate.zip"
            m.bundle({"samples": [report]}, location)
            with zipfile.ZipFile(location) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(archive.namelist(), ["frank-live-funnel-summary.json"])
                raw = archive.read(archive.namelist()[0]).decode()
                for forbidden in (FAKE_MINT, SECRET, '"pid":', '"signature"'):
                    self.assertNotIn(forbidden, raw)
                self.assertIn("QUOTE_STALE", raw)
            with self.assertRaises(FileExistsError):
                m.bundle({"samples": [report]}, location)

    def test_404_means_f01_interface_missing_not_no_buy(self):
        Handler.routes["/api/follow-opportunities"] = (404, {"error": SECRET})
        report = m.sample(self.server.server_port)
        self.assertEqual(report["local_f01_interface"],
                         "F01_ROUTE_NOT_INSTALLED_IN_RUNNING_BACKEND")
        self.assertNotIn("aggregate", report["endpoints"]["/api/follow-opportunities"])
        self.assertFalse(report["endpoints"]["/api/coverage"]["aggregate"]
                         ["chain_completeness_verified"])

    def test_503_and_oversized_http_fail_closed(self):
        Handler.routes["/api/candidates"] = (503, {"error": SECRET})
        Handler.routes["/api/coverage"] = (200, {"raw": SECRET * 100000})
        result = m.sample(self.server.server_port)["endpoints"]
        self.assertEqual(result["/api/candidates"]["result"], "HTTP_NON_200")
        self.assertEqual(result["/api/coverage"]["result"], "BODY_SIZE_OUT_OF_BOUND")

    def test_private_arbitrary_labels_cannot_leak(self):
        Handler.routes["/api/follow-opportunities"] = (
            200, {"status": SECRET, "eligible": [], "eligible_count": 0,
                  "not_followed": [{"exclusion_reason": SECRET}], "excluded_count": 1})
        report = m.sample(self.server.server_port)
        raw = json.dumps(report)
        self.assertNotIn(SECRET, raw)
        self.assertIn("OTHER_OR_UNKNOWN", raw)

    def test_only_explicit_loopback_endpoint_allowed(self):
        with self.assertRaises(ValueError):
            m.get_json(self.server.server_port, "https://api.mainnet-beta.solana.com")
        with self.assertRaises(ValueError):
            m.get_json(80, "/api/runtime")

    def test_iso_timestamp_or_future_unknown_neutral(self):
        from datetime import datetime, timezone
        now = time.time()
        iso = datetime.fromtimestamp(now - 10, timezone.utc).isoformat()
        self.assertAlmostEqual(m._age(iso, now), 10, delta=.2)
        self.assertIsNone(m._age("2035-01-01", now))
        self.assertIsNone(m._age(True, now))


if __name__ == "__main__":
    unittest.main()
