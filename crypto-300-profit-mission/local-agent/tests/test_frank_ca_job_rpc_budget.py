"""C1 synthetic-only CA job budget tests; no network or production state."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from mission_agent.meme.cluster import (
    Holder, RPCJobBudgetExceeded, SolanaReadOnlyRPC, WalletClusterAnalyzer,
)
from mission_agent.mission_control import server


class Clock:
    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


class TestGlobalWireBudget(unittest.TestCase):
    def test_retry_and_fallback_count_all_actual_network_attempts(self):
        clock = Clock()
        endpoints = []
        def always_limited(request, timeout):
            endpoints.append(request.full_url)
            return Response({"error": {"code": 429, "message": "rate limit"}})
        rpc = SolanaReadOnlyRPC(
            "https://primary.example", fallback_endpoints=["https://fallback.example"],
            open_url=always_limited, sleep=clock.sleep, monotonic=clock.monotonic,
            max_wire_attempts=3, max_elapsed_seconds=300,
        )
        with self.assertRaisesRegex(RPCJobBudgetExceeded, "RPC_JOB_WIRE_BUDGET_EXHAUSTED"):
            rpc.call("getTokenSupply", ["mint"])
        self.assertEqual(rpc.calls, 3)
        self.assertEqual(sum(rpc.endpoint_calls.values()), 3)
        self.assertEqual(len(endpoints), 3)
        self.assertTrue(set(endpoints) <= {"https://primary.example", "https://fallback.example"})
        with self.assertRaises(RPCJobBudgetExceeded):
            rpc.call("getTokenSupply", ["second"])
        self.assertEqual(len(endpoints), 3)

    def test_elapsed_deadline_rejects_response_without_cache_or_extra_attempts(self):
        clock = Clock()
        seen = []
        def slow_response(request, timeout):
            seen.append(timeout)
            clock.sleep(31)
            return Response({"result": {"value": "STALE_AFTER_DEADLINE"}})
        rpc = SolanaReadOnlyRPC(
            "https://rpc.example", fallback_endpoints=[],
            open_url=slow_response, sleep=clock.sleep, monotonic=clock.monotonic,
            max_wire_attempts=10, max_elapsed_seconds=30,
        )
        with self.assertRaisesRegex(RPCJobBudgetExceeded, "RPC_JOB_TIME_BUDGET_EXHAUSTED"):
            rpc.call("getTokenSupply", ["mint"])
        self.assertEqual(rpc.calls, 1)
        self.assertEqual(seen, [20.0])
        with self.assertRaises(RPCJobBudgetExceeded):
            rpc.call("getTokenSupply", ["mint"])
        self.assertEqual(rpc.calls, 1)

    def test_cache_hit_does_not_count_as_new_network_attempt(self):
        clock = Clock()
        responses = []
        class Cached:
            def get(self, method, params, now):
                return {"known": True} if params == ["cached"] else None
            def put(self, *args):
                pass
        def open_url(request, timeout):
            responses.append(1)
            return Response({"result": "ok"})
        rpc = SolanaReadOnlyRPC(
            "https://rpc.example", fallback_endpoints=[],
            open_url=open_url, cache=Cached(), sleep=clock.sleep,
            monotonic=clock.monotonic, max_wire_attempts=2, max_elapsed_seconds=300,
        )
        self.assertEqual(rpc.call("getTokenSupply", ["cached"], ttl=60), {"known": True})
        self.assertEqual(rpc.calls, 0)
        self.assertEqual(rpc.call("getTokenSupply", ["uncached"], ttl=60), "ok")
        self.assertEqual(rpc.calls, 1)
        self.assertEqual(len(responses), 1)

    def test_invalid_limits_fail_at_construction(self):
        for wire in [0, -1, True, 1.5]:
            with self.subTest(wire=wire), self.assertRaises(ValueError):
                SolanaReadOnlyRPC("https://rpc.example", fallback_endpoints=[], max_wire_attempts=wire)
        for seconds in [0, -2, float("inf"), float("nan")]:
            with self.subTest(seconds=seconds), self.assertRaises(ValueError):
                SolanaReadOnlyRPC("https://rpc.example", fallback_endpoints=[], max_elapsed_seconds=seconds)


class BudgetFailRPC:
    def call(self, *args, **kwargs):
        raise RPCJobBudgetExceeded("RPC_JOB_WIRE_BUDGET_EXHAUSTED")


class TransactionFailRPC:
    def call(self, method, *args, **kwargs):
        if method == "getSignaturesForAddress":
            return [{"signature": "a-valid-test-signature"}]
        raise RPCJobBudgetExceeded("RPC_JOB_WIRE_BUDGET_EXHAUSTED")


class TestCannotSwallowJobBudget(unittest.TestCase):
    def setUp(self):
        self.holder = Holder("token-account", "owner", 1, 0, "ORDINARY", "test")

    def test_token_profile_and_holder_signature_fail_closed(self):
        analyzer = WalletClusterAnalyzer("mint", rpc=BudgetFailRPC(), market_client=None)
        with self.assertRaises(RPCJobBudgetExceeded):
            analyzer.token_profile()
        with self.assertRaises(RPCJobBudgetExceeded):
            analyzer._scan_holder(self.holder, {}, set())

    def test_funding_signature_and_transaction_fail_closed(self):
        analyzer = WalletClusterAnalyzer("mint", rpc=BudgetFailRPC(), market_client=None)
        first = {"signature": "first", "block_time": 123}
        with self.assertRaises(RPCJobBudgetExceeded):
            analyzer._scan_funding(self.holder, first, set())
        analyzer.rpc = TransactionFailRPC()
        with self.assertRaises(RPCJobBudgetExceeded):
            analyzer._scan_holder(self.holder, {}, set())
        with self.assertRaises(RPCJobBudgetExceeded):
            analyzer._scan_funding(self.holder, first, set())

    def test_real_job_worker_marks_error_and_does_not_persist_latest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            worker = object.__new__(server.ClusterJobManager)
            worker.lock = threading.Lock()
            worker.jobs = {
                "job": {
                    "job_id": "job", "mint": "mint", "preset": "deep",
                    "status": "QUEUED", "created_at": 1, "started_at": None,
                    "finished_at": None, "progress": {"stage": "QUEUED"},
                    "error": None,
                }
            }
            worker.max_retained_jobs = 64
            worker.cache_path = root / "cache.sqlite"
            worker.report_root = root / "reports"
            worker.rpc_endpoint = "https://fake.example"
            worker.rpc_endpoints = ["https://fake.example"]
            worker.registry_path = root / "registry.json"
            worker.market_client = None
            worker.evidence_enabled = False
            class FailingRPC:
                def __init__(self, *args, **kwargs):
                    self.calls = 2
                    self.budget_options = kwargs
            class FailingAnalyzer:
                def __init__(self, *args, **kwargs):
                    pass
                def analyze(self):
                    raise RPCJobBudgetExceeded("RPC_JOB_WIRE_BUDGET_EXHAUSTED")
            with patch.object(server, "SolanaReadOnlyRPC", FailingRPC), \\
                 patch.object(server, "WalletClusterAnalyzer", FailingAnalyzer), \\
                 patch.object(server, "load_registry", return_value={}):
                worker._run("job")
            job = worker.jobs["job"]
            self.assertEqual(job["status"], "ERROR")
            self.assertEqual(job["error"]["type"], "RPC_JOB_BUDGET_EXHAUSTED")
            self.assertEqual(job["progress"]["stage"], "RPC_BUDGET_EXHAUSTED")
            self.assertEqual(job["progress"]["wire_attempts"], 2)
            self.assertEqual(job["progress"]["wire_attempt_limit"], 2500)
            self.assertFalse((root / "reports" / "mint" / "latest.json").exists())
            self.assertFalse((root / "reports" / "mint").exists())


if __name__ == "__main__":
    unittest.main()
