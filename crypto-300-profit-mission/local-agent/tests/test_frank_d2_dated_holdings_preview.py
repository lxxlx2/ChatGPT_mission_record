"""Frank D2: actual repo finalized 32-mint snapshot + honest 926-row preview."""
from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import importlib.util
import json
import tempfile
import threading
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/frank_d2_dated_holdings_preview.py"
spec = importlib.util.spec_from_file_location("frank_d2_preview", SCRIPT)
d2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d2)


def data():
    return json.loads(d2.SNAPSHOT.read_text(encoding="utf-8"))


def mint(i: int) -> str:
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    encoded = ""
    while i:
        encoded = alphabet[i % len(alphabet)] + encoded
        i //= len(alphabet)
    return "A" * 36 + encoded.rjust(8, "1")


def synthetic_watch(count: int = 926):
    archive = data()
    rows = []
    for i, record in enumerate(archive["records"]):
        rows.append({
            "mint": record["mint"], "watch_state": "HISTORICAL_EXIT" if i == 0
                    else "MODEL_OPEN" if i == 1 else "WATCH_UNRESOLVED",
            "local_model_state": "CLOSED" if record["raw_amount"] != "0" else "OPEN",
            "last_event_time": 0, "current_chain_balance_verified": False,
            "market_value_usd": None, "pnl_usd": None,
        })
    rows += [{"mint": mint(i + 1), "watch_state": "PASSIVE_RECEIPT_ONLY",
              "local_model_state": "UNKNOWN", "last_event_time": None}
             for i in range(count - len(rows))]
    return {"status": "OK", "rows": rows,
            "scope": "LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN",
            "chain_completeness_verified": False, "summary": {"total_observed": count}}


class Backend(BaseHTTPRequestHandler):
    requests = []
    payload = {}
    override = None

    def do_GET(self):
        type(self).requests.append((self.command, self.path))
        if self.path != "/api/frank-observed-watchlist":
            self.send_error(404)
            return
        data_ = json.dumps(type(self).payload).encode("utf-8")
        if type(self).override is not None:
            code, mime = type(self).override
        else:
            code, mime = (200, "application/json")
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data_)))
        self.end_headers()
        self.wfile.write(data_)

    def do_POST(self):
        raise AssertionError("POST_TO_WALLET_BACKEND_FORBIDDEN")

    def log_message(self, *_): pass


class D2EvidenceTests(unittest.TestCase):
    def setUp(self):
        Backend.requests = []
        Backend.payload = synthetic_watch()
        Backend.override = None
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), Backend)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(timeout=2)

    def test_checked_in_real_chain_snapshot_32_and_full_926_overlay(self):
        archive = data()
        self.assertEqual(archive["summary"], {"checked": 32, "nonzero": 10, "zero": 22})
        self.assertEqual(archive["date_bangkok"], "2026-10-11")
        raw = d2._watch(self.http.server_port)
        self.assertEqual(Backend.requests, [("GET", "/api/frank-observed-watchlist")])
        html = d2.generate(raw, archive, now=datetime(2026, 10, 19, tzinfo=timezone.utc))
        self.assertIn("本地观察记录", html)
        self.assertIn("2026-10-11", html)
        self.assertIn("约 8 天", html)
        self.assertIn("https://solscan.io/token/", html)
        self.assertIn("NOT_QUERIED_IN_SNAPSHOT", html)
        self.assertIn("历史样本非零", html)
        self.assertIn("当前价格、PnL 与实际 F01 资格均未查询", html)
        self.assertEqual(html.count("<tr data-state='"), 926)
        self.assertIn("样本当时非零<b>10</b>", html)
        self.assertIn("样本当时为零<b>22</b>", html)
        self.assertIn("没有这批余额证据<b>894</b>", html)
        self.assertNotIn("当前 USD 持仓：", html)
        self.assertNotIn("可立即跟单", html)

    def test_dated_snapshot_is_not_live_and_matches_reconciliation(self):
        reconciled = d2.reconcile_watchlist(synthetic_watch(), data())
        self.assertFalse(reconciled["chain_completeness_verified"])
        self.assertEqual(reconciled["snapshot_status"], "DATED_POINT_IN_TIME_NOT_LIVE")
        self.assertEqual(reconciled["snapshot_reconciliation"]["matched_mints"], 32)
        self.assertEqual(reconciled["snapshot_reconciliation"]["nonzero_at_snapshot"], 10)
        self.assertEqual(reconciled["snapshot_reconciliation"]["zero_at_snapshot"], 22)
        self.assertEqual(reconciled["snapshot_reconciliation"]["unresolved_without_snapshot"], 894)
        self.assertTrue(all(x["current_chain_balance_verified"] is False for x in reconciled["rows"]))
        self.assertTrue(all(x["market_value_usd"] is None and x["pnl_usd"] is None
                            for x in reconciled["rows"]))

    def test_arbitrary_watchlist_string_cannot_inject_html(self):
        raw = synthetic_watch(count=32)
        raw["rows"][0]["watch_state"] = "<script>alert('xss')</script>"
        raw["rows"][0]["last_event_time"] = "'><script>alert(1)</script>"
        out = d2.generate(raw, data(), now=datetime(2026, 10, 19, tzinfo=timezone.utc))
        self.assertNotIn("<script>alert", out)
        self.assertNotIn("'><script>alert", out)
        self.assertIn("UNRESOLVED", out)

    def test_invalid_non_json_and_failure_do_not_publish_misleading_preview(self):
        Backend.override = (503, "application/json")
        with self.assertRaises(RuntimeError):
            d2._watch(self.http.server_port)
        Backend.override = (200, "text/html")
        with self.assertRaises(RuntimeError):
            d2._watch(self.http.server_port)
        Backend.override = None
        Backend.payload = {"status": "SOURCE_UNAVAILABLE", "rows": []}
        with self.assertRaises(RuntimeError):
            d2._watch(self.http.server_port)
        self.assertTrue(all(method == "GET" for method, _ in Backend.requests))

    def test_broken_wallet_or_provenance_fails_closed(self):
        bad = data()
        bad["wallet"] = "incorrect"
        with self.assertRaises(d2.reconcile_watchlist.__globals__["InventoryEvidenceError"]):
            d2.generate(synthetic_watch(), bad)
        with self.assertRaises(ValueError):
            d2.render({"snapshot_status": "SNAPSHOT_NOT_PRESENT", "rows": []})

    def test_full_main_real_http_creates_one_local_html_no_prod_mutations(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            pointer = root / "Library/Application Support/FrankMeme/dashboard_port"
            pointer.parent.mkdir(parents=True)
            pointer.write_text(str(self.http.server_port))
            self.assertEqual(d2._port(root), self.http.server_port)
            with patch.object(d2.Path, "home", return_value=root), \
                 patch.object(d2.sys, "platform", "linux"):
                self.assertEqual(d2.main(), 0)
            previews = list((root / "Downloads").glob("frank-d2-dated-inventory-*.html"))
            self.assertEqual(len(previews), 1)
            text = previews[0].read_text("utf-8")
            self.assertIn("NOT_QUERIED_IN_SNAPSHOT", text)
            self.assertIn("样本当时非零<b>10</b>", text)
            self.assertEqual(Backend.requests, [("GET", "/api/frank-observed-watchlist")])
            self.assertFalse((root / ".frank_meme_control_root").exists())
            self.assertFalse((root / "mission-control.sqlite").exists())
            self.assertFalse((root / "forward.sqlite").exists())


if __name__ == "__main__":
    unittest.main()
