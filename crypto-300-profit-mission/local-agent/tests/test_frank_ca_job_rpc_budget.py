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
            max_wire_attempts=20, max_elapsed_seconds=140, min_interval=0,
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


class TestCompletedCAReportIdentity(unittest.TestCase):
    """Actual worker persistence path in temp dir; no RPC or production writes."""

    def test_successful_worker_saves_real_job_id_to_timestamp_and_latest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            worker = object.__new__(server.ClusterJobManager)
            worker.lock = threading.Lock()
            worker.jobs = {
                "a" * 32: {
                    "job_id": "a" * 32, "mint": "So11111111111111111111111111111111111111112",
                    "preset": "quick", "status": "QUEUED",
                    "created_at": 1, "started_at": None,
                    "finished_at": None, "progress": {"stage": "QUEUED"},
                    "error": None,
                },
            }
            worker.max_retained_jobs = 64
            worker.cache_path = root / "cache.sqlite"
            worker.report_root = root / "reports"
            worker.rpc_endpoint = "https://synthetic.example"
            worker.rpc_endpoints = ["https://synthetic.example"]
            worker.registry_path = root / "registry.json"
            worker.market_client = None
            worker.evidence_enabled = False

            class StubRPC:
                def __init__(self, *args, **kwargs):
                    self.calls = 0

                def assert_can_publish(self):
                    return None

            class StubAnalyzer:
                def __init__(self, *args, **kwargs):
                    pass

                def analyze(self):
                    return {"schema_version": 2, "source": "SOLANA_FINALIZED_JSON_RPC",
                            "mint": "So11111111111111111111111111111111111111112",
                            "coverage": {}, "observed_at": 100, "holders": [],
                            "metrics": {}, "assessment": {}, "token_profile": {},
                            "limitations": []}

            with (
                patch.object(server, "SolanaReadOnlyRPC", StubRPC),
                patch.object(server, "WalletClusterAnalyzer", StubAnalyzer),
                patch.object(server, "load_registry", return_value={}),
                patch.object(server, "markdown", return_value="synthetic report\n"),
                patch.object(worker, "_attach_assessment_history", return_value=None),
            ):
                worker._run("a" * 32)

            self.assertEqual(worker.jobs["a" * 32]["status"], "DONE")
            report_dir = root / "reports" / "So11111111111111111111111111111111111111112"
            stored = json.loads((report_dir / "latest.json").read_text())
            self.assertEqual(stored["ca_job_id"], "a" * 32)
            self.assertEqual(stored["mint"], "So11111111111111111111111111111111111111112")
            dated = list(report_dir.glob("20*.json"))
            self.assertEqual(len(dated), 1)
            self.assertEqual(json.loads(dated[0].read_text())["ca_job_id"], "a" * 32)
            by_id = root / "reports" / "_jobs" / ("a" * 32 + ".json")
            self.assertEqual(json.loads(by_id.read_text())["ca_job_id"], "a" * 32)
            marker = json.loads((root / "reports" / "_jobs" / ("a" * 32 + ".done.json")).read_text())
            self.assertEqual(marker["status"], "DONE")
            self.assertEqual(marker["report_sha256"], server.hashlib.sha256(by_id.read_bytes()).hexdigest())
            worker.jobs.clear()
            recovered = worker.get("a" * 32)
            self.assertEqual(recovered["status"], "DONE")
            self.assertTrue(recovered["restored_from_saved_report"])
            self.assertEqual(worker.latest(recovered["mint"], job_id="a" * 32)["ca_job_id"], "a" * 32)
            self.assertIsNone(worker.get("b" * 32))
            self.assertIsNone(worker.latest(recovered["mint"], job_id="b" * 32))
            with self.assertRaises(ValueError):
                worker.latest(recovered["mint"], job_id="../invalid")

            # New B on the same mint overwrites latest while A stays by-ID.
            worker.jobs["b" * 32] = {
                "job_id": "b" * 32, "mint": recovered["mint"],
                "preset": "quick", "status": "QUEUED", "created_at": 2,
                "started_at": None, "finished_at": None,
                "progress": {"stage": "QUEUED"}, "error": None,
            }
            with (
                patch.object(server, "SolanaReadOnlyRPC", StubRPC),
                patch.object(server, "WalletClusterAnalyzer", StubAnalyzer),
                patch.object(server, "load_registry", return_value={}),
                patch.object(server, "markdown", return_value="synthetic report\\n"),
                patch.object(worker, "_attach_assessment_history", return_value=None),
            ):
                worker._run("b" * 32)
            self.assertEqual(worker.jobs["b" * 32]["status"], "DONE")
            self.assertEqual(worker.latest(recovered["mint"])["ca_job_id"], "b" * 32)
            self.assertEqual(worker.latest(recovered["mint"], job_id="a" * 32)["ca_job_id"], "a" * 32)
            self.assertEqual(worker.latest(recovered["mint"], job_id="b" * 32)["ca_job_id"], "b" * 32)
            self.assertIsNone(worker.latest("11111111111111111111111111111111", job_id="a" * 32))
            worker.jobs.clear()
            self.assertEqual(worker.get("a" * 32)["status"], "DONE")
            self.assertEqual(worker.get("b" * 32)["status"], "DONE")
            by_id.write_text(json.dumps({"mint": recovered["mint"], "ca_job_id": "b" * 32}))
            self.assertIsNone(worker.get("a" * 32))
            self.assertIsNone(worker.latest(recovered["mint"], job_id="a" * 32))

    @staticmethod
    def _worker(root, job_id, mint):
        worker = object.__new__(server.ClusterJobManager)
        worker.lock = threading.Lock()
        worker.jobs = {job_id: {
            "job_id": job_id, "mint": mint, "preset": "quick",
            "status": "QUEUED", "created_at": 1, "started_at": None,
            "finished_at": None, "error": None, "progress": {"stage": "QUEUED"},
        }}
        worker.max_retained_jobs = 64
        worker.cache_path = root / "cache.sqlite"
        worker.report_root = root / "reports"
        worker.rpc_endpoint = "https://synthetic.example"
        worker.rpc_endpoints = [worker.rpc_endpoint]
        worker.registry_path = root / "registry.json"
        worker.market_client = None
        worker.evidence_enabled = False
        return worker

    @staticmethod
    def _run_fake(worker, job_id, injected=None):
        mint = worker.jobs[job_id]["mint"]
        class StubRPC:
            def __init__(self, *args, **kwargs):
                self.calls = 0
            def assert_can_publish(self):
                return None
        class StubAnalyzer:
            def __init__(self, *args, **kwargs):
                pass
            def analyze(self):
                return {
                    "schema_version": 2, "source": "SOLANA_FINALIZED_JSON_RPC",
                    "mint": mint, "observed_at": 100.0, "coverage": {},
                    "holders": [], "metrics": {}, "assessment": {},
                    "token_profile": {}, "limitations": [],
                }
        original = server._atomic_write_text
        def writer(path, payload):
            if injected is not None:
                injected(Path(path))
            return original(path, payload)
        with (
            patch.object(server, "SolanaReadOnlyRPC", StubRPC),
            patch.object(server, "WalletClusterAnalyzer", StubAnalyzer),
            patch.object(server, "load_registry", return_value={}),
            patch.object(server, "markdown", return_value="synthetic report\\n"),
            patch.object(worker, "_attach_assessment_history", return_value=None),
            patch.object(server, "_atomic_write_text", writer),
        ):
            worker._run(job_id)

    def test_mandatory_stage_failures_do_not_publish_recoverable_done(self):
        mint = "So11111111111111111111111111111111111111112"
        job_id = "c" * 32
        for failed in (job_id + ".json", "latest.json", job_id + ".done.json"):
            with self.subTest(failed=failed), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                worker = self._worker(root, job_id, mint)
                out = worker.report_root / mint
                out.mkdir(parents=True)
                old_latest = '{"mint":"OLD","status":"historical"}'
                (out / "latest.json").write_text(old_latest)
                def raise_at(path):
                    if path.name == failed:
                        raise OSError("SYNTHETIC_WRITE_FAILED")
                self._run_fake(worker, job_id, injected=raise_at)
                self.assertEqual(worker.get(job_id)["status"], "ERROR")
                self.assertIsNone(worker._saved_job_report(job_id))
                marker = worker.report_root / "_jobs" / (job_id + ".done.json")
                self.assertFalse(marker.exists())
                if failed in (job_id + ".json", "latest.json"):
                    self.assertEqual((out / "latest.json").read_text(), old_latest)
                worker.jobs.clear()
                self.assertIsNone(worker.get(job_id))
                old_fallback = worker.latest(mint, job_id=job_id)
                self.assertTrue(old_fallback is None or old_fallback.get("ca_job_id") is None)

    def test_precommit_pruning_failure_does_not_restore_done(self):
        mint = "So11111111111111111111111111111111111111112"
        job_id = "d" * 32
        with tempfile.TemporaryDirectory() as directory:
            worker = self._worker(Path(directory), job_id, mint)
            with patch.object(worker, "_prune_jobs_locked", side_effect=[
                OSError("SYNTHETIC_PRECOMMIT_FAILURE"), None,
            ]):
                self._run_fake(worker, job_id)
            self.assertEqual(worker.get(job_id)["status"], "ERROR")
            worker.jobs.clear()
            self.assertIsNone(worker.get(job_id))
            self.assertIsNone(worker.latest(mint, job_id=job_id))

    def test_structural_damage_with_matching_digest_still_cannot_restore(self):
        mint = "So11111111111111111111111111111111111111112"
        job_id = "e" * 32
        with tempfile.TemporaryDirectory() as directory:
            worker = self._worker(Path(directory), job_id, mint)
            self._run_fake(worker, job_id)
            self.assertEqual(worker.get(job_id)["status"], "DONE")
            report_path = worker.report_root / "_jobs" / (job_id + ".json")
            marker_path = worker.report_root / "_jobs" / (job_id + ".done.json")
            report = json.loads(report_path.read_text())
            raw_report = report_path.read_bytes()
            raw_marker = marker_path.read_bytes()
            for broken in (
                {"mint": mint, "ca_job_id": job_id},
                {**report, "observed_at": "yesterday"},
                {**report, "coverage": []},
                {**report, "source": "UNSUPPORTED"},
            ):
                with self.subTest(removed_fields=list(set(report) - set(broken))):
                    report_path.write_text(json.dumps(broken))
                    marker = json.loads(raw_marker)
                    marker["report_sha256"] = server.hashlib.sha256(report_path.read_bytes()).hexdigest()
                    marker_path.write_text(json.dumps(marker))
                    worker.jobs.clear()
                    self.assertIsNone(worker.get(job_id))
                    self.assertIsNone(worker.latest(mint, job_id=job_id))
            report_path.write_bytes(raw_report)
            marker_path.write_bytes(raw_marker)
            self.assertEqual(worker.get(job_id)["status"], "DONE")
            marker_path.unlink()
            self.assertIsNone(worker.get(job_id))
            self.assertIsNone(worker.latest(mint, job_id=job_id))

    def test_report_digest_mismatch_does_not_restore(self):
        mint = "So11111111111111111111111111111111111111112"
        job_id = "f" * 32
        with tempfile.TemporaryDirectory() as directory:
            worker = self._worker(Path(directory), job_id, mint)
            self._run_fake(worker, job_id)
            worker.jobs.clear()
            report_path = worker.report_root / "_jobs" / (job_id + ".json")
            report = json.loads(report_path.read_text())
            report["metrics"]["changed"] = 1
            report_path.write_text(json.dumps(report))
            self.assertIsNone(worker.get(job_id))
            self.assertIsNone(worker.latest(mint, job_id=job_id))
