"""G2: actual dashboard D1 API & D2 dated watchlist without network or writer."""
import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mission_agent.mission_control import server, wallet_activity

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "meme/evidence/frank-v2-thirty-two-mint-finalized-2026-10-11.json"
SIG = "2" * 88
MINT = "7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump"


def source_db(path, now):
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE signatures(wallet TEXT,signature TEXT,person_id TEXT,
                                block_time INTEGER,body TEXT);
        CREATE TABLE trades(wallet TEXT,signature TEXT,mint TEXT,side TEXT);
        """)
        for i, classification in enumerate(
            ["ACTIVE_TRADE", "PASSIVE_TRANSFER", "UNKNOWN_NEEDS_REVIEW"]
        ):
            signature = chr(ord("2") + i) * 88
            db.execute("INSERT INTO signatures VALUES(?,?,?,?,?)",
                       ("wallet", signature, "frank", now-100-i,
                        json.dumps({"classification":classification})))
        db.execute("INSERT INTO trades VALUES(?,?,?,?)",
                   ("wallet", SIG, MINT, "BUY"))


class G2ReadOnlyIntegrationTests(unittest.TestCase):
    def test_wallet_activity_is_independent_of_follow_decisions(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "forward.sqlite"
            now = int(time.time())
            source_db(p, now)
            before = p.read_bytes()
            state = server.DashboardState.__new__(server.DashboardState)
            state.frank = SimpleNamespace(database=p)
            value = state.frank_signed_activity(1)
            self.assertEqual(value["status"], "INDEXED_LOCAL_ONLY")
            self.assertEqual(value["signatures"], 3)
            self.assertEqual(value["trade_legs"], 1)
            self.assertEqual(value["categories"]["PASSIVE_TRANSFER"], 1)
            self.assertEqual(value["categories"]["UNKNOWN_NEEDS_REVIEW"], 1)
            self.assertFalse(value["full_chain_verified"])
            self.assertFalse(value["current_balance_verified"])
            self.assertEqual(p.read_bytes(), before)

    def test_missing_source_is_not_zero_trades(self):
        with tempfile.TemporaryDirectory() as folder:
            state = server.DashboardState.__new__(server.DashboardState)
            state.frank = SimpleNamespace(database=Path(folder) / "missing.sqlite")
            result = state.frank_signed_activity(1)
            self.assertEqual(result["status"], "UNAVAILABLE")
            self.assertIsNone(result["signatures"])

    def test_source_overflow_reports_failure_not_truncation(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "forward.sqlite"
            source_db(p, int(time.time()))
            with self.assertRaisesRegex(ValueError, "NOT_TRUNCATED"):
                wallet_activity.activity(p, int(time.time()), max_rows=2)
            state = server.DashboardState.__new__(server.DashboardState)
            state.frank = SimpleNamespace(database=p)
            with patch.object(server, "read_signed_activity", side_effect=ValueError("INDEX_WINDOW_TOO_LARGE_NOT_TRUNCATED")):
                result = state.frank_signed_activity(7)
            self.assertEqual(result["reason"], "INDEX_WINDOW_TOO_LARGE_NOT_TRUNCATED")
            self.assertIsNone(result["signatures"])

    def test_api_rejects_unbounded_ranges_and_handles_seven_days(self):
        handler = server.Handler.__new__(server.Handler)
        handler._allowed_host = lambda: True
        handler._json = lambda payload, status=200: (payload, status)
        handler.state = SimpleNamespace(frank_signed_activity=lambda days: {"days":days})
        handler.path = "/api/frank-signed-activity?days=7"
        self.assertEqual(handler.do_GET(), ({"days":7}, 200))
        for suffix in ("?days=30", "?days=1&days=7", "?other=1"):
            handler.path = "/api/frank-signed-activity" + suffix
            self.assertEqual(handler.do_GET()[1], 400)

    def test_dated_repo_evidence_used_only_when_no_manual_import(self):
        evidence = json.loads(SNAPSHOT.read_text("utf-8"))
        first = evidence["records"][0]["mint"]
        observed = {"status":"OK", "scope":"LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN",
                    "summary":{"total_observed":1},
                    "rows":[{"mint":first, "local_model_state":"UNKNOWN"}]}
        with tempfile.TemporaryDirectory() as folder:
            state = server.DashboardState.__new__(server.DashboardState)
            state.control_root = Path(folder)
            state.frank = SimpleNamespace(database=Path(folder) / "forward.sqlite",person_id="frank")
            with patch.object(server, "read_frank_watchlist", return_value=observed):
                output = state.frank_observed_watchlist()
            self.assertEqual(output["snapshot_status"], "DATED_POINT_IN_TIME_NOT_LIVE")
            self.assertEqual(output["snapshot_origin"], "REPO_DATED_2026_10_11_NOT_LIVE")
            self.assertFalse(output["chain_completeness_verified"])
            self.assertFalse(output["market_values_verified"])
            self.assertFalse(output["rows"][0]["current_chain_balance_verified"])
            self.assertIsNone(output["rows"][0]["market_value_usd"])

    def test_malformed_manual_import_never_silently_falls_back(self):
        observed = {"status":"OK", "scope":"LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN",
                    "summary":{}, "rows":[]}
        with tempfile.TemporaryDirectory() as folder:
            state = server.DashboardState.__new__(server.DashboardState)
            state.control_root = Path(folder)
            state.frank = SimpleNamespace(database=Path(folder) / "forward.sqlite",person_id="frank")
            (state.control_root / "frank-inventory-snapshot.json").write_text('{"invalid":true}')
            with patch.object(server, "read_frank_watchlist", return_value=observed):
                output = state.frank_observed_watchlist()
            self.assertEqual(output["snapshot_status"], "SNAPSHOT_INVALID_READ_ONLY_IGNORED")

    def test_frontend_integrated_into_existing_ui(self):
        path = Path(server.__file__).with_name("static")
        html = (path / "index.html").read_text("utf-8")
        js = (path / "app.js").read_text("utf-8")
        self.assertIn('id="signed-activity-rows"', html)
        self.assertIn("refreshSignedActivity(true);", js)
        self.assertIn("get('/api/frank-signed-activity?days='", js)
        self.assertIn("get('/api/decisions').catch(() => null)", js)


if __name__ == "__main__":
    unittest.main()
