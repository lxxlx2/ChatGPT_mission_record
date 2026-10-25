"""C1 synthetic-only CA job budget tests; no network or production state."""
import json
import io
import tempfile
import urllib.request
import urllib.response
from email.message import Message
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from mission_agent.meme.cluster import (
    Holder, RPCError, RPCJobBudgetExceeded, SolanaReadOnlyRPC, WalletClusterAnalyzer,
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
                def assert_can_publish(self):
                    return None
            class FailingAnalyzer:
                def __init__(self, *args, **kwargs):
                    pass
                def analyze(self):
                    raise RPCJobBudgetExceeded("RPC_JOB_WIRE_BUDGET_EXHAUSTED")
            with (
                patch.object(server, "SolanaReadOnlyRPC", FailingRPC),
                patch.object(server, "WalletClusterAnalyzer", FailingAnalyzer),
                patch.object(server, "load_registry", return_value={}),
            ):
                worker._run("job")
            job = worker.jobs["job"]
            self.assertEqual(job["status"], "ERROR")
            self.assertEqual(job["error"]["type"], "RPC_JOB_BUDGET_EXHAUSTED")
            self.assertEqual(job["progress"]["stage"], "RPC_BUDGET_EXHAUSTED")
            self.assertEqual(job["progress"]["wire_attempts"], 2)
            self.assertEqual(job["progress"]["wire_attempt_limit"], 2500)
            self.assertFalse((root / "reports" / "mint" / "latest.json").exists())
            self.assertFalse((root / "reports" / "mint").exists())



class TestReviewP1Regressions(unittest.TestCase):
    def test_actual_default_urllib_redirect_handler_rejects_second_exchange(self):
        # Use the actual urllib opener/error/redirect handler chain; HTTPS I/O itself
        # is wholly synthetic so this test can never reach the network.
        exchanges = []
        def synthetic_https(self, request):
            exchanges.append((request.full_url, request.get_method()))
            headers = Message()
            headers["Location"] = "https://unlisted.example/escape"
            reply = urllib.response.addinfourl(
                io.BytesIO(b""), headers, request.full_url, code=302,
            )
            reply.msg = "Found"
            return reply
        with (
            patch("urllib.request.getproxies", return_value={}),
            patch.object(urllib.request.HTTPSHandler, "https_open", synthetic_https),
        ):
            rpc = SolanaReadOnlyRPC(
                "https://primary.example", fallback_endpoints=[],
                max_wire_attempts=1, max_elapsed_seconds=60, min_interval=0,
            )
            with self.assertRaisesRegex(Exception, "RPC_REDIRECT_FORBIDDEN"):
                rpc.call("getTokenSupply", ["mint"])
        self.assertEqual(exchanges, [("https://primary.example", "POST")])
        self.assertEqual(rpc.calls, 1)

    def test_last_six_rate_limits_return_budget_not_generic_rpc_error(self):
        clock = Clock()
        responses = []
        def limited(request, timeout):
            responses.append(1)
            return Response({"error": {"code": 429, "message": "rate limit"}})
        rpc = SolanaReadOnlyRPC(
            "https://only.example", fallback_endpoints=[],
            open_url=limited, sleep=clock.sleep, monotonic=clock.monotonic,
            min_interval=0, max_wire_attempts=6, max_elapsed_seconds=300,
        )
        with self.assertRaisesRegex(RPCJobBudgetExceeded, "RPC_JOB_WIRE_BUDGET_EXHAUSTED"):
            rpc.call("getTokenSupply", ["mint"])
        self.assertEqual(len(responses), 6)
        self.assertEqual(rpc.calls, 6)
        with self.assertRaises(RPCJobBudgetExceeded):
            rpc.assert_can_publish()

    def test_valid_final_allowed_success_may_still_publish(self):
        clock = Clock()
        rpc = SolanaReadOnlyRPC(
            "https://only.example", fallback_endpoints=[],
            open_url=lambda request, timeout: Response({"result": {"ok": True}}),
            sleep=clock.sleep, monotonic=clock.monotonic,
            max_wire_attempts=1, max_elapsed_seconds=100, min_interval=0,
        )
        self.assertEqual(rpc.call("getTokenSupply", ["mint"]), {"ok": True})
        self.assertEqual(rpc.calls, 1)
        rpc.assert_can_publish()  # count==limit is NOT itself an error after success.

    def test_last_failed_transport_crosses_deadline_after_final_retry(self):
        clock = Clock()
        count = []
        def failed_transport(request, timeout):
            count.append(timeout)
            clock.sleep(10 if len(count) < 6 else 85)
            raise TimeoutError("SYNTHETIC_OFFLINE_TRANSPORT_ERROR")
        rpc = SolanaReadOnlyRPC(
            "https://only.example", fallback_endpoints=[],
            open_url=failed_transport, sleep=clock.sleep, monotonic=clock.monotonic,
            max_wire_attempts=20, max_elapsed_seconds=180, min_interval=0,
        )
        with self.assertRaisesRegex(RPCJobBudgetExceeded, "RPC_JOB_TIME_BUDGET_EXHAUSTED"):
            rpc.call("getTokenSupply", ["mint"])
        self.assertEqual(rpc.calls, 6)
        self.assertEqual(len(count), 6)
        with self.assertRaises(RPCJobBudgetExceeded):
            rpc.assert_can_publish()

    def test_nonretryable_final_rpc_error_cannot_be_published_as_success(self):
        clock = Clock()
        rpc = SolanaReadOnlyRPC(
            "https://only.example", fallback_endpoints=[],
            open_url=lambda request, timeout: Response({"error": {"code": -32000}}),
            monotonic=clock.monotonic, sleep=clock.sleep,
            max_wire_attempts=1, max_elapsed_seconds=100, min_interval=0,
        )
        # This is a genuine RPCError, unlike a retryable 429; a best-effort
        # holder/funder handler could otherwise suppress it.
        with self.assertRaises(RPCError):
            rpc.call("getTokenSupply", ["mint"])
        self.assertEqual(rpc.calls, 1)
        with self.assertRaisesRegex(RPCJobBudgetExceeded, "RPC_JOB_WIRE_BUDGET_EXHAUSTED"):
            rpc.assert_can_publish()

    def test_real_funding_analyzer_and_worker_final_failure_never_save_or_publish(self):
        # Real RPC adapter, real _scan_funding, real analyze and real _run;
        # no network, no actual publication, no user data.
        class OneHolderAnalyzer(WalletClusterAnalyzer):
            def token_profile(self):
                return {"status": "OK"}
            def market_snapshot(self):
                return {"status": "UNAVAILABLE", "source": "FIXTURE"}
            def holders(self):
                return 1000, 0, [Holder("ta", "owner", 100, 0, "ORDINARY", "fixture")]
            def _scan_holder(self, holder, mapping, owners, history_limit=None):
                return {"signature": "first", "block_time": 123}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_latest = root / "reports" / "mint" / "latest.json"
            old_latest.parent.mkdir(parents=True)
            old_bytes = b'{"previous":true}'
            old_latest.write_bytes(old_bytes)
            clock = Clock()
            calls = []
            def synthetic_transport(request, timeout):
                calls.append(request.full_url)
                method = json.loads(request.data)["method"]
                if method == "getSignaturesForAddress":
                    return Response({"result": [{"signature": "synthetic-signature"}]})
                clock.sleep(5)
                raise TimeoutError("SYNTHETIC_OFFLINE_TIMEOUT")

            def real_rpc_factory(*args, **kwargs):
                kwargs.update({
                    "fallback_endpoints": [], "open_url": synthetic_transport,
                    "sleep": clock.sleep, "monotonic": clock.monotonic,
                    "min_interval": 0, "max_wire_attempts": 6,
                    "max_elapsed_seconds": 100,
                })
                return SolanaReadOnlyRPC(*args, **kwargs)

            class EvidenceSpool:
                def ca_done(self, **kwargs):
                    raise AssertionError("ca_done must never run on budget failure")
            class EvidenceExecutor:
                def submit(self, *args):
                    raise AssertionError("successful evidence submit must never run")
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
            worker.rpc_endpoint = "https://only.example"
            worker.rpc_endpoints = ["https://only.example"]
            worker.registry_path = root / "registry.json"
            worker.market_client = None
            worker.evidence_enabled = True
            worker.evidence_spool = EvidenceSpool()
            worker.evidence_executor = EvidenceExecutor()
            limited_budgets = {
                "deep": {"max_wire_attempts": 6, "max_elapsed_seconds": 100},
            }
            with (
                patch.object(server, "SolanaReadOnlyRPC", real_rpc_factory),
                patch.object(server, "WalletClusterAnalyzer", OneHolderAnalyzer),
                patch.object(server, "load_registry", return_value={}),
                patch.object(server, "CLUSTER_RPC_JOB_BUDGETS", limited_budgets),
            ):
                worker._run("job")
            job = worker.jobs["job"]
            self.assertEqual(job["status"], "ERROR")
            self.assertEqual(job["error"]["type"], "RPC_JOB_BUDGET_EXHAUSTED")
            self.assertEqual(job["progress"]["stage"], "RPC_BUDGET_EXHAUSTED")
            self.assertEqual(job["progress"]["wire_attempt_limit"], 6)
            self.assertEqual(len(calls), 6)
            self.assertEqual(old_latest.read_bytes(), old_bytes)
            self.assertEqual(sorted(p.name for p in old_latest.parent.iterdir()), ["latest.json"])


if __name__ == "__main__":
    unittest.main()
