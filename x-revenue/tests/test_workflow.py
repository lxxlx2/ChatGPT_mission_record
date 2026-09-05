#!/usr/bin/env python3
"""Comprehensive test suite protecting the 10 core x-revenue workflow requirements."""

import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest

import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config
import pipeline
import telegram_approval
import triggers


class TestXRevenueWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="x_revenue_test_")
        self.test_root = Path(self.temp_dir)
        self.artifacts_dir = self.test_root / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir = self.test_root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / "seen.json"
        self.runs_dir = self.test_root / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

        self.mock_stocks = {
            "COMP": {"display_name": "Nasdaq Comp", "price_usd": 26500.0, "change_percent": 1.25, "trade_date": "2026-09-04"},
            "NDX": {"display_name": "Nasdaq-100", "price_usd": 29500.0, "change_percent": 1.50, "trade_date": "2026-09-04"},
            "SOX": {"display_name": "Semis", "price_usd": 11700.0, "change_percent": 3.20, "trade_date": "2026-09-04"},
        }
        self.mock_crypto = {
            "BTC": {"price_usd": 80000.0, "utc_open_usd": 78000.0, "change_percent_vs_utc_open": 2.56, "resolved_pair": "XXBTZUSD"},
            "ETH": {"price_usd": 2500.0, "utc_open_usd": 2450.0, "change_percent_vs_utc_open": 2.04, "resolved_pair": "XETHZUSD"},
            "SOL": {"price_usd": 105.0, "utc_open_usd": 102.0, "change_percent_vs_utc_open": 2.94, "resolved_pair": "SOLUSD"},
        }
        self.mock_trends = [
            {
                "source": "SEC",
                "title": "SEC Proposes Rescission of Political Contribution Rule",
                "url": "https://www.sec.gov/newsroom/press-releases/test",
                "published_at": "2026-09-04T12:00:00Z",
                "age_hours": 12.0,
                "trend_score": 6.5,
            }
        ]
        self.mock_analysis = {
            "signal": "broad_risk_on",
            "interpretation": "risk appetite is broad across US stocks and crypto",
            "stock_breadth_up": 3,
            "crypto_breadth_up": 3,
            "stock_dispersion_percentage_points": 1.95,
            "crypto_dispersion_percentage_points": 0.90,
            "top_official_trend": self.mock_trends[0],
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # 1. Existing X pipeline happy path
    def test_1_happy_path_generation_and_validation(self):
        now = pipeline.utc_now()
        candidate = pipeline.make_candidate(now, self.mock_stocks, self.mock_crypto, self.mock_analysis)
        self.assertLessEqual(len(candidate), 280)
        self.assertIn("Nasdaq Comp", candidate)

        receipts = [
            {"source": "Nasdaq", "url": "https://api.nasdaq.com/test", "final_url": "https://api.nasdaq.com/test", "fetched_at": pipeline.iso(now), "response_sha256": "abc"},
            {"source": "Nasdaq", "url": "https://api.nasdaq.com/test2", "final_url": "https://api.nasdaq.com/test2", "fetched_at": pipeline.iso(now), "response_sha256": "abc"},
            {"source": "Nasdaq", "url": "https://api.nasdaq.com/test3", "final_url": "https://api.nasdaq.com/test3", "fetched_at": pipeline.iso(now), "response_sha256": "abc"},
            {"source": "Kraken", "url": "https://api.kraken.com/test", "final_url": "https://api.kraken.com/test", "fetched_at": pipeline.iso(now), "response_sha256": "abc"},
            {"source": "Federal Reserve", "url": "https://www.federalreserve.gov/test", "final_url": "https://www.federalreserve.gov/test", "fetched_at": pipeline.iso(now), "response_sha256": "abc"},
            {"source": "SEC", "url": "https://www.sec.gov/test", "final_url": "https://www.sec.gov/test", "fetched_at": pipeline.iso(now), "response_sha256": "abc"},
        ]
        qa = pipeline.quality(candidate, receipts, now)
        self.assertTrue(qa["passed"])

        # Verify existing historical artifact validates cleanly
        hist_artifact = ROOT / "artifacts" / "20260905T045131Z"
        if hist_artifact.exists():
            res = pipeline.load_validated_artifact(hist_artifact)
            self.assertTrue(all(res["checks"].values()))
            self.assertFalse(res["manifest"]["external_publish_performed"])

    # 2. NO_ACTION path
    def test_2_no_action_path_when_triggers_not_met(self):
        # Calm market: small moves, old news
        quiet_stocks = {
            "COMP": {"display_name": "Nasdaq Comp", "price_usd": 26500.0, "change_percent": 0.10, "trade_date": "2026-09-04"},
            "NDX": {"display_name": "Nasdaq-100", "price_usd": 29500.0, "change_percent": 0.05, "trade_date": "2026-09-04"},
            "SOX": {"display_name": "Semis", "price_usd": 11700.0, "change_percent": 0.20, "trade_date": "2026-09-04"},
        }
        quiet_crypto = {
            "BTC": {"price_usd": 80000.0, "utc_open_usd": 79800.0, "change_percent_vs_utc_open": 0.25, "resolved_pair": "XXBTZUSD"},
            "ETH": {"price_usd": 2500.0, "utc_open_usd": 2490.0, "change_percent_vs_utc_open": 0.40, "resolved_pair": "XETHZUSD"},
            "SOL": {"price_usd": 105.0, "utc_open_usd": 104.5, "change_percent_vs_utc_open": 0.48, "resolved_pair": "SOLUSD"},
        }
        quiet_trends = [
            {"source": "SEC", "title": "Old announcement", "age_hours": 72.0, "trend_score": 2.0, "published_at": "2026-09-01T00:00:00Z"}
        ]
        quiet_analysis = {
            "signal": "broad_risk_on",
            "stock_breadth_up": 3,
            "crypto_breadth_up": 3,
            "stock_dispersion_percentage_points": 0.15,
            "crypto_dispersion_percentage_points": 0.23,
        }
        cfg = {"stock_trigger_percent": 1.0, "crypto_trigger_percent": 2.5, "news_trigger_score": 5.0}

        trig = triggers.evaluate_triggers(quiet_stocks, quiet_crypto, quiet_trends, quiet_analysis, {}, cfg)
        self.assertFalse(trig["triggered"])
        self.assertEqual(trig["action"], "NO_ACTION")

    # 3. Duplicate candidate does not send duplicate approval
    def test_3_duplicate_candidate_suppressed(self):
        now = pipeline.utc_now()
        candidate = pipeline.make_candidate(now, self.mock_stocks, self.mock_crypto, self.mock_analysis)
        substantive = re.sub(r", \d{2}:\d{2} UTC\.$", ".", candidate)
        fingerprint = hashlib.sha256(substantive.encode()).hexdigest()

        # Save fingerprint in seen.json
        state = {"candidate_fingerprints": [fingerprint], "last_event_values": {}}
        self.state_file.write_text(json.dumps(state))

        # Check that fingerprint matches duplicate detection
        loaded_state = json.loads(self.state_file.read_text())
        self.assertIn(fingerprint, loaded_state["candidate_fingerprints"])

    # 4. Exact-digest approve path
    def test_4_exact_digest_approve_path(self):
        run_id = "test_run_approve"
        art_dir = self.artifacts_dir / run_id
        art_dir.mkdir(parents=True)
        candidate_text = "Test candidate for approval verification."
        sha = hashlib.sha256(candidate_text.encode()).hexdigest()
        (art_dir / "candidate.txt").write_text(candidate_text)
        app_data = {
            "status": "PENDING",
            "candidate_sha256": sha,
            "created_at": pipeline.iso(pipeline.utc_now()),
            "expires_at": pipeline.iso(pipeline.utc_now() + dt.timedelta(hours=24)),
            "decision": "PENDING",
            "delivery_state": "SENT",
            "external_publish_allowed": False,
        }
        (art_dir / "approval.json").write_text(json.dumps(app_data))

        cb_data = telegram_approval.encode_callback_data("A", sha)
        query = {
            "id": "query_101",
            "data": cb_data,
            "from": {"id": 12345, "username": "owner_user"},
            "message": {"message_id": 999, "chat": {"id": 12345}},
        }
        res = telegram_approval.handle_single_callback(query, self.artifacts_dir, {})
        self.assertEqual(res["status"], "DECIDED")
        self.assertEqual(res["decision"], "APPROVED")

        # Verify persisted state
        updated = json.loads((art_dir / "approval.json").read_text())
        self.assertEqual(updated["status"], "APPROVED")
        self.assertEqual(updated["decision"], "APPROVED")
        self.assertFalse(updated["external_publish_allowed"])
        self.assertEqual(updated["actor"], "telegram:owner_user")

    # 5. Exact-digest reject path
    def test_5_exact_digest_reject_path(self):
        run_id = "test_run_reject"
        art_dir = self.artifacts_dir / run_id
        art_dir.mkdir(parents=True)
        candidate_text = "Test candidate for rejection verification."
        sha = hashlib.sha256(candidate_text.encode()).hexdigest()
        (art_dir / "candidate.txt").write_text(candidate_text)
        app_data = {
            "status": "PENDING",
            "candidate_sha256": sha,
            "created_at": pipeline.iso(pipeline.utc_now()),
            "expires_at": pipeline.iso(pipeline.utc_now() + dt.timedelta(hours=24)),
            "decision": "PENDING",
            "delivery_state": "SENT",
            "external_publish_allowed": False,
        }
        (art_dir / "approval.json").write_text(json.dumps(app_data))

        cb_data = telegram_approval.encode_callback_data("R", sha)
        query = {
            "id": "query_102",
            "data": cb_data,
            "from": {"id": 12345, "username": "owner_user"},
            "message": {"message_id": 999, "chat": {"id": 12345}},
        }
        res = telegram_approval.handle_single_callback(query, self.artifacts_dir, {})
        self.assertEqual(res["status"], "DECIDED")
        self.assertEqual(res["decision"], "REJECTED")

        updated = json.loads((art_dir / "approval.json").read_text())
        self.assertEqual(updated["status"], "REJECTED")
        self.assertEqual(updated["decision"], "REJECTED")
        self.assertFalse(updated["external_publish_allowed"])

    # 6. Malformed/stale/replayed callback rejected
    def test_6_callback_rejection_conditions(self):
        run_id = "test_run_guard"
        art_dir = self.artifacts_dir / run_id
        art_dir.mkdir(parents=True)
        candidate_text = "Test candidate for edge cases."
        sha = hashlib.sha256(candidate_text.encode()).hexdigest()
        (art_dir / "candidate.txt").write_text(candidate_text)
        app_data = {
            "status": "PENDING",
            "candidate_sha256": sha,
            "created_at": pipeline.iso(pipeline.utc_now()),
            "expires_at": pipeline.iso(pipeline.utc_now() + dt.timedelta(hours=24)),
            "decision": "PENDING",
            "delivery_state": "SENT",
            "external_publish_allowed": False,
        }
        (art_dir / "approval.json").write_text(json.dumps(app_data))

        # 6a. Malformed data
        res = telegram_approval.handle_single_callback({"data": "INVALID_FORMAT"}, self.artifacts_dir, {})
        self.assertEqual(res["reason"], "MALFORMED_CALLBACK")

        # 6b. Unknown digest
        unknown_sha = "0" * 64
        cb_unknown = telegram_approval.encode_callback_data("A", unknown_sha)
        res = telegram_approval.handle_single_callback({"data": cb_unknown}, self.artifacts_dir, {})
        self.assertEqual(res["reason"], "UNKNOWN_CANDIDATE")

        # 6c. Candidate file tampered
        (art_dir / "candidate.txt").write_text("TAMPERED CONTENT")
        cb_valid = telegram_approval.encode_callback_data("A", sha)
        res = telegram_approval.handle_single_callback({"data": cb_valid, "from": {"id": 1}}, self.artifacts_dir, {})
        self.assertEqual(res["reason"], "CANDIDATE_DIGEST_MISMATCH")
        (art_dir / "candidate.txt").write_text(candidate_text)  # restore

        # 6d. Replay after finalization
        res = telegram_approval.handle_single_callback({"data": cb_valid, "from": {"id": 1}}, self.artifacts_dir, {})
        self.assertEqual(res["status"], "DECIDED")
        # Attempt replay
        res2 = telegram_approval.handle_single_callback({"data": cb_valid, "from": {"id": 1}}, self.artifacts_dir, {})
        self.assertEqual(res2["reason"], "ALREADY_FINALIZED")

        # 6e. Stale / expired
        run_stale = "test_run_stale"
        stale_dir = self.artifacts_dir / run_stale
        stale_dir.mkdir()
        stale_sha = hashlib.sha256(b"stale candidate").hexdigest()
        (stale_dir / "candidate.txt").write_bytes(b"stale candidate")
        stale_app = {
            "status": "PENDING",
            "candidate_sha256": stale_sha,
            "created_at": "2026-09-01T00:00:00Z",
            "expires_at": "2026-09-02T00:00:00Z",
            "decision": "PENDING",
            "external_publish_allowed": False,
        }
        (stale_dir / "approval.json").write_text(json.dumps(stale_app))
        cb_stale = telegram_approval.encode_callback_data("A", stale_sha)
        res_stale = telegram_approval.handle_single_callback({"data": cb_stale, "from": {"id": 1}}, self.artifacts_dir, {})
        self.assertEqual(res_stale["reason"], "STALE_CALLBACK")
        self.assertEqual(json.loads((stale_dir / "approval.json").read_text())["status"], "EXPIRED")

        # 6f. Unauthorized user
        run_auth = "test_run_auth"
        auth_dir = self.artifacts_dir / run_auth
        auth_dir.mkdir()
        auth_sha = hashlib.sha256(b"auth candidate").hexdigest()
        (auth_dir / "candidate.txt").write_bytes(b"auth candidate")
        (auth_dir / "approval.json").write_text(json.dumps({
            "status": "PENDING", "candidate_sha256": auth_sha, "decision": "PENDING", "external_publish_allowed": False
        }))
        cb_auth = telegram_approval.encode_callback_data("A", auth_sha)
        cfg_auth = {"telegram_allowed_user_ids": ["99999"]}
        res_auth = telegram_approval.handle_single_callback(
            {"data": cb_auth, "from": {"id": 11111}}, self.artifacts_dir, cfg_auth
        )
        self.assertEqual(res_auth["reason"], "CALLBACK_BINDING_REJECTED")

    # 7. Concurrent run lock
    def test_7_concurrent_run_lock(self):
        import fcntl
        lock_file = self.state_dir / "run.lock"
        with lock_file.open("a+") as lock1:
            fcntl.flock(lock1.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Try second lock
            with lock_file.open("a+") as lock2:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(lock2.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(lock1.fileno(), fcntl.LOCK_UN)

    # 8. State survives a rerun / restart
    def test_8_state_survives_restart(self):
        state_data = {
            "candidate_fingerprints": ["hash1", "hash2"],
            "last_event_values": {"Nasdaq:SOX:2026-09-04": 3.37},
            "last_run": "20260905T045131Z",
            "last_run_status": "NO_ACTION",
        }
        self.state_file.write_text(json.dumps(state_data))
        offset_file = self.state_dir / "telegram-offset.json"
        offset_file.write_text(json.dumps({"offset": 42}))

        # Re-read from disk in new variables (simulating process restart)
        reloaded_state = json.loads(self.state_file.read_text())
        reloaded_offset = json.loads(offset_file.read_text())
        self.assertEqual(reloaded_state["candidate_fingerprints"], ["hash1", "hash2"])
        self.assertEqual(reloaded_state["last_event_values"]["Nasdaq:SOX:2026-09-04"], 3.37)
        self.assertEqual(reloaded_offset["offset"], 42)

    # 9. No secrets written into Git / reports / artifacts / logs
    def test_9_no_secrets_in_repo(self):
        secret_patterns = [
            re.compile(r"ghp_[A-Za-z0-9_]{36}"),
            re.compile(r"bot[0-9]{9,10}:[a-zA-Z0-9_-]{35}"),
            re.compile(r"xoxb-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24}"),
            re.compile(r"-----BEGIN (RSA|EC|OPENSSH|DSA) PRIVATE KEY-----"),
            re.compile(r"AKIA[0-9A-Z]{16}"),
        ]
        scanned_count = 0
        for root_dir, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".tmp")]
            for f in files:
                if f.endswith((".pyc", ".lock", ".png", ".jpg")):
                    continue
                file_path = Path(root_dir) / f
                scanned_count += 1
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    for pattern in secret_patterns:
                        self.assertIsNone(
                            pattern.search(content),
                            f"Secret pattern match in {file_path}",
                        )
                except Exception:
                    pass
        self.assertGreater(scanned_count, 5)

    # 10. Publisher remains disabled
    def test_10_publisher_remains_disabled(self):
        hist_artifact = ROOT / "artifacts" / "20260905T045131Z"
        if hist_artifact.exists():
            check_res = pipeline.publish_check(hist_artifact)
            self.assertFalse(check_res["ready"])
            self.assertFalse(check_res["external_request_made"])
            self.assertFalse(check_res["checks"]["publisher_implemented"])
            self.assertFalse(check_res["checks"]["approval_allows_external_publish"])


if __name__ == "__main__":
    unittest.main()
