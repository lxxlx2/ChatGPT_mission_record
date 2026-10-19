import copy
import importlib.util
import json
import sys
import unittest
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from f0_bounded_smoke import (
    ENDPOINT, MAX_CALLS, METHODS, SCOPE, LimitedRPC, NoRedirect,
    fixture_sender, smoke, utc, validate_permit, https_sender, live_failure_report, main,
)
ROOT = Path(__file__).resolve().parents[1]
SAMPLE = json.loads((ROOT / "fixtures" / "bounded_smoke.json").read_text())


def sample():
    return copy.deepcopy(SAMPLE)


def permit(now):
    start = now - timedelta(minutes=1)
    return {
        "scope": SCOPE, "user_authorized": True,
        "approved_endpoint": ENDPOINT, "methods": list(METHODS),
        "cost_policy": "FREE_ONLY_NO_PAYMENT", "local_environment": "USER_MAC_LOCAL_ONLY",
        "max_total_rpc_calls": 4, "max_control_discovery_calls": 1,
        "max_response_bytes": 2_000_000, "no_retries": True, "no_ws": True,
        "store_raw_payloads": False, "retention_hours": 1,
        "storage_root": "/tmp/bsc-f0-smoke-user-approved",
        "window_start_utc": start.isoformat().replace("+00:00", "Z"),
        "window_end_utc": (start+timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
    }


class OfflineSmokeTests(unittest.TestCase):
    def test_full_saved_chain_receipt_success(self):
        report = smoke(fixture_sender(sample()))
        self.assertEqual(report["chain_id"], 56)
        self.assertEqual(report["height"], 1000)
        self.assertEqual(report["full_block_transaction_count"], 1)
        self.assertEqual(report["attempted_rpc_calls"], 4)
        self.assertEqual(report["attempted_control_discovery_calls"], 1)
        self.assertEqual(report["receipt_state"], "IDENTITY_VALIDATED_NOT_FINALITY")
        self.assertEqual(report["e3_actual_count"], 0)
        self.assertEqual(report["quoted_actual_count"], 0)
        self.assertFalse(report["e2_attested"])

    def test_no_tx_only_three_calls(self):
        data = sample()
        data["responses"][2]["result"]["transactions"] = []
        data["responses"].pop()
        out = smoke(fixture_sender(data))
        self.assertEqual(out["attempted_rpc_calls"], 3)
        self.assertEqual(out["receipt_state"], "NOT_TESTED_EMPTY_BLOCK")

    def test_receipt_missing_is_not_success(self):
        data = sample()
        data["responses"][3]["result"] = None
        self.assertEqual(smoke(fixture_sender(data))["receipt_state"], "NOT_YET_AVAILABLE")

    def test_wrong_network_rejected(self):
        data = sample()
        data["responses"][0]["result"] = "0x1"
        with self.assertRaisesRegex(ValueError, "WRONG_CHAIN_ID"):
            smoke(fixture_sender(data))

    def test_hash_only_block_rejected(self):
        data = sample()
        data["responses"][2]["result"]["transactions"] = ["0x" + "11"*32]
        with self.assertRaisesRegex(ValueError, "FULL_BLOCK_TRANSACTIONS_UNAVAILABLE"):
            smoke(fixture_sender(data))

    def test_receipt_block_mismatch_rejected(self):
        data = sample()
        data["responses"][3]["result"]["blockHash"] = "0x" + "99"*32
        with self.assertRaisesRegex(ValueError, "RECEIPT_BLOCK_MISMATCH"):
            smoke(fixture_sender(data))

    def test_receipt_tx_mismatch_rejected(self):
        data = sample()
        data["responses"][3]["result"]["transactionHash"] = "0x" + "99"*32
        with self.assertRaisesRegex(ValueError, "RECEIPT_IDENTITY_MISMATCH"):
            smoke(fixture_sender(data))

    def test_mismatch_in_method_fails_offline(self):
        data = sample()
        data["responses"][1]["method"] = "eth_sendRawTransaction"
        with self.assertRaisesRegex(ValueError, "FIXTURE_REQUEST_MISMATCH"):
            smoke(fixture_sender(data))

    def test_rpc_cap_hard_enforced_even_on_fail(self):
        def broken_sender(endpoint, payload, cap):
            raise ConnectionError("intentional")
        rpc = LimitedRPC(broken_sender, ENDPOINT, 500)
        for _ in range(MAX_CALLS):
            with self.assertRaises(ConnectionError):
                rpc.call("eth_chainId", [])
        with self.assertRaisesRegex(ValueError, "RPC_CALL_CAP_REACHED"):
            rpc.call("eth_chainId", [])
        self.assertEqual(rpc.attempts, 4)

    def test_control_cap_hard_enforced(self):
        rpc = LimitedRPC(lambda endpoint,payload,cap: {"jsonrpc":"2.0", "id":payload["id"], "result":{}}, ENDPOINT, 500)
        rpc.call("eth_getBlockByNumber", ["0x1", True], discovery=True)
        with self.assertRaisesRegex(ValueError, "CONTROL_DISCOVERY_CAP_REACHED"):
            rpc.call("eth_getBlockByNumber", ["0x1", True], discovery=True)
        self.assertEqual(rpc.attempts, 1)

    def test_nonread_method_disallowed(self):
        rpc = LimitedRPC(lambda *args: None, ENDPOINT, 500)
        with self.assertRaisesRegex(ValueError, "METHOD_NOT_APPROVED"):
            rpc.call("eth_sendRawTransaction", [])
        self.assertEqual(rpc.attempts, 0)

    def test_offline_mode_does_not_use_network(self):
        with patch("urllib.request.build_opener", side_effect=AssertionError("network used")):
            self.assertEqual(smoke(fixture_sender(sample()))["attempted_rpc_calls"], 4)

    def test_live_sender_endpoint_is_exact(self):
        with patch("urllib.request.build_opener", side_effect=AssertionError("network used")):
            with self.assertRaisesRegex(ValueError, "ENDPOINT_NOT_APPROVED"):
                https_sender("https://evil.example", {"method":"eth_chainId"}, 10)

    def test_live_redirect_blocked(self):
        with self.assertRaisesRegex(ValueError, "REDIRECT_FORBIDDEN"):
            NoRedirect().redirect_request(None, None, 302, "Moved", {}, "https://evil.example/")

    def test_required_permit_defaults_no_authority(self):
        now = datetime(2026, 10, 20, 0, 0, tzinfo=timezone.utc)
        for missing in (None, {}, {"scope":SCOPE}, {"scope":SCOPE,"user_authorized":False}):
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                validate_permit(missing, now)

    def test_bounded_permit_passes_validation_without_network(self):
        now = datetime(2026, 10, 20, 0, 0, tzinfo=timezone.utc)
        validate_permit(permit(now), now)

    def test_future_or_expired_permit_is_rejected(self):
        now = datetime(2026, 10, 20, 0, 0, tzinfo=timezone.utc)
        p = permit(now)
        for check in [now+timedelta(hours=1), now-timedelta(hours=1)]:
            with self.subTest(check=check), self.assertRaisesRegex(ValueError, "OUTSIDE_APPROVED_WINDOW"):
                validate_permit(p, check)

    def test_cap_mutation_fails(self):
        now = datetime(2026, 10, 20, 0, 0, tzinfo=timezone.utc)
        for k,v in [("max_total_rpc_calls",5), ("max_control_discovery_calls",2),
                    ("max_response_bytes", 3_000_000), ("no_retries", False),
                    ("no_ws", False), ("cost_policy","PAYG"),
                    ("approved_endpoint","https://example.com"),
                    ("methods", ["eth_sendTransaction"])]:
            with self.subTest(key=k):
                p = permit(now)
                p[k] = v
                with self.assertRaises(ValueError):
                    validate_permit(p, now)

    def test_storage_constraints(self):
        now = datetime(2026, 10, 20, 0, 0, tzinfo=timezone.utc)
        for k,v in [("storage_root","/home/user"),("store_raw_payloads",True),
                    ("retention_hours",25)]:
            with self.subTest(k=k):
                p = permit(now)
                p[k] = v
                with self.assertRaises(ValueError):
                    validate_permit(p, now)


class FailingLiveAuditTests(unittest.TestCase):
    def invoke_mock_live(self, sender):
        with tempfile.TemporaryDirectory(prefix="bsc-smoke-review-", dir="/tmp") as location:
            directory = Path(location)
            permit_path = directory / "permit.json"
            report_path = directory / "report.json"
            fake_permit = permit(datetime.now(timezone.utc))
            fake_permit["storage_root"] = location
            permit_path.write_text(json.dumps(fake_permit))
            args = ["f0_bounded_smoke.py", "--execute-live", "--permit", str(permit_path),
                    "--report", str(report_path)]
            with patch.object(sys, "argv", args), patch("f0_bounded_smoke.https_sender", side_effect=sender), \
                 patch("urllib.request.build_opener", side_effect=AssertionError("real network forbidden")):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertNotEqual(cm.exception.code, 0)
            self.assertTrue(report_path.exists(), "failure consumed quota but wrote no report")
            return json.loads(report_path.read_text())

    def test_third_attempt_connection_failure_persists_counts(self):
        send = fixture_sender(sample())
        calls = []
        def fail_third(endpoint, payload, cap):
            calls.append(payload["method"])
            if len(calls) == 3:
                raise ConnectionError("injected private transport detail")
            return send(endpoint, payload, cap)
        r = self.invoke_mock_live(fail_third)
        self.assertEqual(calls, ["eth_chainId", "eth_blockNumber", "eth_getBlockByNumber"])
        self.assertEqual(r["mode"], "AUTHORIZED_PUBLIC_HTTP_SMOKE_FAILED_CLOSED")
        self.assertEqual(r["attempted_rpc_calls"], 3)
        self.assertEqual(r["actual_rpc_calls"], 3)
        self.assertEqual(r["attempted_control_discovery_calls"], 1)
        self.assertEqual(r["error_code"], "NETWORK_ERROR")
        self.assertEqual(r["stop_state"], "BLOCKED_SOURCE")
        self.assertNotIn("injected private", json.dumps(r))
        self.assertEqual(r["e3_actual_count"], 0)

    def test_third_attempt_timeout_persists_counts(self):
        send = fixture_sender(sample())
        calls = []
        def fail_third(endpoint, payload, cap):
            calls.append(payload)
            if len(calls) == 3:
                raise TimeoutError("injected timeout")
            return send(endpoint, payload, cap)
        r = self.invoke_mock_live(fail_third)
        self.assertEqual(len(calls), 3)
        self.assertEqual(r["attempted_rpc_calls"], 3)
        self.assertEqual(r["attempted_control_discovery_calls"], 1)
        self.assertEqual(r["error_code"], "NETWORK_TIMEOUT")

    def test_third_attempt_response_too_large_persists_counts(self):
        send = fixture_sender(sample())
        calls = []
        def fail_third(endpoint, payload, cap):
            calls.append(payload)
            if len(calls) == 3:
                raise ValueError("RESPONSE_TOO_LARGE")
            return send(endpoint, payload, cap)
        r = self.invoke_mock_live(fail_third)
        self.assertEqual(r["attempted_rpc_calls"], 3)
        self.assertEqual(r["error_code"], "RESPONSE_TOO_LARGE")

    def test_third_attempt_bad_envelope_persists_counts(self):
        send = fixture_sender(sample())
        calls = []
        def fail_third(endpoint, payload, cap):
            calls.append(payload)
            if len(calls) == 3:
                return {"jsonrpc": "2.0", "id": payload["id"], "error": {"code": -32000}}
            return send(endpoint, payload, cap)
        r = self.invoke_mock_live(fail_third)
        self.assertEqual(r["attempted_rpc_calls"], 3)
        self.assertEqual(r["error_code"], "RPC_ERROR_OR_BAD_ENVELOPE")

    def test_wrong_chain_failure_first_attempt_persisted(self):
        def wrong_chain(endpoint, payload, cap):
            return {"jsonrpc": "2.0", "id": payload["id"], "result": "0x1"}
        r = self.invoke_mock_live(wrong_chain)
        self.assertEqual(r["attempted_rpc_calls"], 1)
        self.assertEqual(r["attempted_control_discovery_calls"], 0)
        self.assertEqual(r["error_code"], "WRONG_CHAIN_ID")

    def test_successful_mock_live_report_still_has_all_four_counts(self):
        mock_sender = fixture_sender(sample())
        with tempfile.TemporaryDirectory(prefix="bsc-smoke-reviewed-", dir="/tmp") as location:
            folder = Path(location)
            permit_path, report_path = folder / "permit.json", folder / "report.json"
            fake_permit = permit(datetime.now(timezone.utc))
            fake_permit["storage_root"] = location
            permit_path.write_text(json.dumps(fake_permit))
            args = ["f0_bounded_smoke.py", "--execute-live", "--permit", str(permit_path),
                    "--report", str(report_path)]
            with patch.object(sys, "argv", args), patch("f0_bounded_smoke.https_sender", side_effect=mock_sender), \
                 patch("urllib.request.build_opener", side_effect=AssertionError("real network forbidden")):
                main()
            report = json.loads(report_path.read_text())
            self.assertEqual(report["mode"], "AUTHORIZED_PUBLIC_HTTP_SMOKE_NOT_FULL_F0")
            self.assertEqual(report["actual_rpc_calls"], 4)
            self.assertEqual(report["attempted_control_discovery_calls"], 1)
            self.assertEqual(report["stop_state"], "SMOKE_COMPLETE_NOT_F0_PASS")

    def test_discovery_limit_cannot_be_bypassed_with_false_flag(self):
        attempts = []
        def sender(endpoint, payload, cap):
            attempts.append(payload)
            return {"jsonrpc": "2.0", "id": payload["id"], "result": {}}
        rpc = LimitedRPC(sender, ENDPOINT, 500)
        rpc.call("eth_getBlockByNumber", ["0x1", True], discovery=False)
        self.assertEqual(rpc.discovery_attempts, 1)
        with self.assertRaisesRegex(ValueError, "CONTROL_DISCOVERY_CAP_REACHED"):
            rpc.call("eth_getBlockByNumber", ["0x1", True], discovery=False)
        self.assertEqual(rpc.attempts, 1)
        self.assertEqual(len(attempts), 1)

    def test_failure_report_never_exposes_exception_message(self):
        rpc = LimitedRPC(lambda *args: None, ENDPOINT, 500)
        output = live_failure_report(RuntimeError("secret token and url"), rpc)
        self.assertEqual(output["error_code"], "SMOKE_FAILED")
        self.assertNotIn("secret", json.dumps(output))
        self.assertEqual(output["stop_state"], "BLOCKED_SOURCE")


if __name__ == "__main__":
    unittest.main()
