import asyncio
import base64
import contextlib
import io
import json
import os
import tempfile
import unittest
from email import policy
from email.parser import BytesParser
from pathlib import Path
from unittest.mock import patch

from machine_launch_detector import Journal, Rpc
from machine_launch_gmail import GmailAlerts, marker_for, message_for
from machine_fun_runtime import GmailDetector, StartupBlocked, gmail_from_existing, rpc_from_existing
from test_machine_launch_detector import FakeRpc, tx_template

EVENT = {
    "signature": "5TestSignature11111111111",
    "slot": 462500000,
    "block_time": 1793200000,
    "instruction": "InitializeV2",
    "mint": "TokenMint111",
    "pool": "LaunchPool111",
    "creator": "Creator111",
    "payer": "Payer111",
    "quote_mint": "So11111111111111111111111111111111111111112",
    "platform_config": "3hVbfgB77tL1qDKhtMQoe4Gv7qPN2dGmKpD2KxWP2sPb",
    "evidence": "CHAIN_PLATFORM_CANDIDATE_UNENDORSED",
}


class StubGmail:
    def __init__(self):
        self.recipient = "owner@example.test"
        self.messages = {}
        self.send_count = 0
        self.fail_after_send = False
        self.fail_before_send = False
        self.allow_search = True

    def ready(self):
        pass

    def sent_matches(self, event):
        if not self.allow_search:
            raise OSError("Gmail read unavailable")
        return [mid for mid, raw in self.messages.items() if marker_for(event).encode() in raw]

    def send(self, raw):
        self.send_count += 1
        if self.fail_before_send:
            raise OSError("network timeout")
        mid = "gmail-" + str(self.send_count)
        self.messages[mid] = raw
        if self.fail_after_send:
            raise OSError("reply lost after Google accepted")
        return {"id": mid}

    def verify(self, event, gmail_id):
        raw = self.messages.get(gmail_id)
        if not raw:
            return False
        email = BytesParser(policy=policy.default).parsebytes(raw)
        body = email.get_body(preferencelist=("plain",)).get_content()
        return (marker_for(event) in body and event["signature"] in body and
                str(email["To"]) == self.recipient)


class EmailTests(unittest.TestCase):
    def test_message_contains_full_evidence_and_marker(self):
        raw = message_for(EVENT, "owner@example.test")
        parsed = BytesParser(policy=policy.default).parsebytes(raw)
        text = parsed.get_body(preferencelist=("plain",)).get_content()
        self.assertIn(EVENT["signature"], text)
        self.assertIn(EVENT["mint"], text)
        self.assertIn("UNENDORSED", text)
        self.assertIn(marker_for(EVENT), text)
        self.assertNotIn("Frank MULTIPLE", text)

    def test_new_event_sent_and_verified_once(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = StubGmail()
            alerts = GmailAlerts(Path(folder) / "email.sqlite", Path(folder) / "oauth.json", fake.recipient, lambda: fake)
            alerts.enqueue(EVENT)
            with contextlib.redirect_stdout(io.StringIO()):
                alerts.drain()
                alerts.enqueue(EVENT)
                alerts.drain()
            self.assertEqual(fake.send_count, 1)
            self.assertEqual(alerts.summary(), {"SENT_VERIFIED": 1})

    def test_send_accepted_then_response_lost_reconciles_without_resend(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = StubGmail()
            alerts = GmailAlerts(Path(folder) / "email.sqlite", Path(folder) / "oauth.json", fake.recipient, lambda: fake)
            alerts.enqueue(EVENT)
            fake.fail_after_send = True
            with contextlib.redirect_stderr(io.StringIO()):
                alerts.drain()
            self.assertEqual(alerts.summary(), {"SEND_UNCERTAIN": 1})
            fake.fail_after_send = False
            with contextlib.redirect_stdout(io.StringIO()):
                alerts.drain()
            self.assertEqual(alerts.summary(), {"SENT_VERIFIED": 1})
            self.assertEqual(fake.send_count, 1)

    def test_uncertain_no_sent_match_never_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = StubGmail()
            alerts = GmailAlerts(Path(folder) / "email.sqlite", Path(folder) / "oauth.json", fake.recipient, lambda: fake)
            alerts.enqueue(EVENT)
            fake.fail_before_send = True
            with contextlib.redirect_stderr(io.StringIO()):
                alerts.drain()
            self.assertEqual(fake.send_count, 1)
            fake.fail_before_send = False
            with contextlib.redirect_stderr(io.StringIO()):
                alerts.drain()
            self.assertEqual(fake.send_count, 1)
            self.assertEqual(alerts.summary(), {"SEND_UNCERTAIN": 1})

    def test_sent_search_failure_does_not_send(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = StubGmail()
            fake.allow_search = False
            alerts = GmailAlerts(Path(folder) / "email.sqlite", Path(folder) / "oauth.json", fake.recipient, lambda: fake)
            alerts.enqueue(EVENT)
            with contextlib.redirect_stderr(io.StringIO()):
                alerts.drain()
            self.assertEqual(fake.send_count, 0)
            self.assertEqual(alerts.summary(), {"QUEUED": 1})

    def test_wrong_evidence_cannot_be_enqueued(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = StubGmail()
            alerts = GmailAlerts(Path(folder) / "email.sqlite", Path(folder) / "oauth.json", fake.recipient, lambda: fake)
            alerts.enqueue({**EVENT, "evidence": "UNVERIFIED_ARBITRARY"})
            self.assertEqual(alerts.summary(), {})

    def test_isolated_machine_runtime_inserts_email_event_without_frank_db(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = StubGmail()
            alerts = GmailAlerts(Path(folder) / "emails.sqlite", Path(folder) / "oauth.json", fake.recipient, lambda: fake)
            journal = Journal(Path(folder) / "events.sqlite")
            detector = GmailDetector(FakeRpc([], {"sig1": tx_template()}), journal, alerts)
            with contextlib.redirect_stdout(io.StringIO()):
                asyncio.run(detector.process("sig1", 111))
            self.assertEqual(fake.send_count, 1)
            self.assertEqual(alerts.summary(), {"SENT_VERIFIED": 1})
            journal.close()

    def test_rpc_url_mapping_from_frank_file_never_prints_key(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "solana_rpc_urls"
            file.write_text("https://solana-mainnet.g.alchemy.com/v2/ABCDEFGHabcdefgh12345678\n")
            os.chmod(file, 0o600)
            with patch("machine_fun_runtime.RPC_FILE", file):
                http, ws = rpc_from_existing()
            self.assertEqual(ws, "wss://solana-mainnet.streaming.alchemy.com/v2/ABCDEFGHabcdefgh12345678")
            self.assertEqual(http, "https://solana-mainnet.g.alchemy.com/v2/ABCDEFGHabcdefgh12345678")

    def test_rpc_source_must_be_private_and_authenticated(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "solana_rpc_urls"
            file.write_text("https://api.mainnet-beta.solana.com\n")
            os.chmod(file, 0o600)
            with patch("machine_fun_runtime.RPC_FILE", file):
                with self.assertRaises(StartupBlocked):
                    rpc_from_existing()
            file.write_text("https://solana-mainnet.g.alchemy.com/v2/ABCDEFGHabcdefgh12345678")
            os.chmod(file, 0o644)
            with patch("machine_fun_runtime.RPC_FILE", file):
                with self.assertRaises(StartupBlocked):
                    rpc_from_existing()

    def test_gmail_existing_config_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            oauth = root / "authorized-user.json"
            oauth.write_text(json.dumps({
                "scopes": ["https://www.googleapis.com/auth/gmail.send",
                           "https://www.googleapis.com/auth/gmail.readonly"],
                "client_id": "cid", "client_secret": "secret",
                "refresh_token": "r"
            }))
            os.chmod(oauth, 0o600)
            cfg = root / "gmail-existing-source.json"
            cfg.write_text(json.dumps({"existing_oauth_file": str(oauth), "recipient": "owner@example.test"}))
            os.chmod(cfg, 0o600)
            hint = root / "control"
            hint.write_text(str(root))
            with patch("machine_fun_runtime.ROOT_HINT", hint), patch("machine_fun_runtime.RUNNER_HINT", root / "missing"):
                path, who = gmail_from_existing()
            self.assertEqual(path, oauth)
            self.assertEqual(who, "owner@example.test")


if __name__ == "__main__":
    unittest.main()
