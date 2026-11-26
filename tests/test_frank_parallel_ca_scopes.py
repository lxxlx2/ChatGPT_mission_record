"""Offline independent CA queue acceptance with real SQLite and localhost GETs."""
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
import http.client
import io
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from mission_agent.meme.ca_market_series import CAMarketSeries
from mission_agent.meme.holder_ranks import _b58
from mission_agent.meme.market_parity import GeckoTerminalMarketClient, GeckoTerminalRequestBudget
from mission_agent.mission_control import server

MINT_A, MINT_B, MINT_C, OWNER, POOL, PEER = [_b58(bytes([n]) * 32) for n in range(1, 7)]


@contextmanager
def read_dashboard(manager):
    class Reader(server.Handler):
        state = SimpleNamespace(cluster_jobs=manager)

        def log_message(self, *_):
            pass

    with server.DashboardHTTPServer(("127.0.0.1", 0), Reader) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            def get(path):
                conn = http.client.HTTPConnection(*httpd.server_address, timeout=5)
                try:
                    conn.request("GET", path)
                    result = conn.getresponse()
                    return result.status, json.loads(result.read())
                finally:
                    conn.close()
            yield get
        finally:
            httpd.shutdown()
            thread.join(timeout=5)


class IndependentScopesTests(unittest.TestCase):
    def test_full_wallet_and_overview_use_independent_queues_and_exact_reports(self):
        full_entered, wallet_entered = threading.Event(), threading.Event()
        release = threading.Event()
        seen_rpc_pacing = []

        class FixtureAnalyzer:
            def __init__(self, mint, **kwargs):
                self.mint, self.kwargs = mint, kwargs

            def analyze(self):
                scope = self.kwargs.get("query_scope", "full")
                self.kwargs["rpc"].call("getTokenSupply", [self.mint])
                if scope == "full" and self.mint == MINT_A:
                    full_entered.set()
                    if not release.wait(10):
                        raise AssertionError("fixture full worker not released")
                if scope == "wallet":
                    base = self.kwargs["wallet_base"]
                    if base["mint"] != self.mint or base["query_scope"] != "overview":
                        raise AssertionError("wrong wallet base")
                    if self.kwargs["focus_owner"] != OWNER:
                        raise AssertionError("wrong wallet owner")
                    wallet_entered.set()
                    if not release.wait(10):
                        raise AssertionError("fixture wallet worker not released")
                return {
                    "schema_version": 2, "source": "SOLANA_FINALIZED_JSON_RPC", "mint": self.mint,
                    "observed_at": 20, "coverage": {}, "holders": [{"owner": OWNER}],
                    "metrics": {}, "assessment": {}, "token_profile": {}, "limitations": [],
                }

        original_rpc = server.SolanaReadOnlyRPC

        def rpc_fixture(*args, **kwargs):
            seen_rpc_pacing.append(kwargs.get("shared_pacing"))
            return original_rpc(*args, **kwargs, open_url=lambda *_a, **_k: io.BytesIO(
                b'{"result":{"value":{"amount":"1","decimals":0}}}'
            ))

        class HoldingExecutor:
            def submit(self, *_):
                return Future()

            def shutdown(self):
                pass

        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "WalletClusterAnalyzer", FixtureAnalyzer), patch.object(
            server, "SolanaReadOnlyRPC", rpc_fixture
        ):
            root = Path(tmp)
            first = server.ClusterJobManager(root)
            self.assertEqual(first._scope_executors, {})
            base = first.submit(MINT_B, scope="overview")
            first.jobs[base["job_id"]]["future"].result(timeout=5)
            self.assertEqual(first.get(base["job_id"])["status"], "DONE")
            first.executor.shutdown()
            first.executor = HoldingExecutor()
            paused = first.submit(MINT_B, scope="wallet", owner=OWNER, base_job_id=base["job_id"])
            first.shutdown()

            manager = server.ClusterJobManager(root, parallel_ca_scopes=True)
            try:
                self.assertIs(manager.ca_market_series.request_budget,
                              manager.independent_market_client.request_budget)
                self.assertEqual(manager.get(paused["job_id"])["status"], "PAUSED")
                full = manager.submit(MINT_A, scope="full")
                self.assertTrue(full_entered.wait(5))
                second_full = manager.submit(MINT_C, scope="full")
                resumed = manager.resume(paused["job_id"], MINT_B)
                self.assertEqual(resumed["job_id"], paused["job_id"])
                self.assertTrue(wallet_entered.wait(5))
                overview = manager.submit(MINT_C, scope="overview")
                manager.jobs[overview["job_id"]]["future"].result(timeout=5)
                with read_dashboard(manager) as get:
                    status, view = get(f'/api/cluster-analysis?job_id={overview["job_id"]}')
                    self.assertEqual((status, view["status"]), (200, "DONE"))
                    exact = f'/api/cluster-latest?mint={MINT_C}&job_id={overview["job_id"]}'
                    status, report = get(exact)
                    self.assertEqual((status, report["mint"], report["query_scope"]), (200, MINT_C, "overview"))
                    self.assertEqual(get(exact.replace(MINT_C, MINT_B))[0], 404)
                    self.assertEqual(manager.get(full["job_id"])["status"], "RUNNING")
                    self.assertEqual(manager.get(second_full["job_id"])["status"], "QUEUED")
                    self.assertEqual(manager.get(resumed["job_id"])["status"], "RUNNING")
                    self.assertFalse(release.is_set())
                    assert seen_rpc_pacing[0] is None
                    self.assertGreaterEqual(len(seen_rpc_pacing), 4)
                    self.assertTrue(all(x is manager._shared_rpc_pacing for x in seen_rpc_pacing[1:]))
                    release.set()
                    for job in (full, second_full, resumed):
                        manager.jobs[job["job_id"]]["future"].result(timeout=5)
                    self.assertEqual(get(exact)[1]["ca_job_id"], overview["job_id"])
                    latest_path = f'/api/cluster-latest?mint={MINT_C}'
                    self.assertEqual(get(latest_path)[1]["ca_job_id"], second_full["job_id"])
                    wallet_path = f'/api/cluster-latest?mint={MINT_B}&job_id={resumed["job_id"]}'
                    wallet = get(wallet_path)[1]
                    self.assertEqual(wallet["base_job_id"], base["job_id"])
                    self.assertEqual(wallet["focus_owner"], OWNER)
                    self.assertEqual(get(f'/api/cluster-latest?mint={MINT_B}')[1]["ca_job_id"], base["job_id"])
            finally:
                release.set()
                manager.shutdown()

    def test_gecko_cooldown_crosses_report_and_chart_without_fake_attempt(self):
        for origin in ("snapshot", "series"):
            with self.subTest(origin=origin):
                now = [0]
                calls = []

                def source(request, timeout):
                    calls.append(request.full_url)
                    if len(calls) == 1:
                        raise HTTPError(request.full_url, 429, "fixture throttle", {}, None)
                    return io.BytesIO(b'{"data":[]}')

                budget = GeckoTerminalRequestBudget(lambda: now[0])
                report = GeckoTerminalMarketClient(open_url=source, request_budget=budget)
                chart = CAMarketSeries(open_url=source, monotonic=lambda: now[0], request_budget=budget)
                snap = lambda: report.pool_snapshot(MINT_A, POOL, PEER)
                series = lambda: chart.read(MINT_A, POOL, PEER, "5m")
                initial = snap() if origin == "snapshot" else series()["chart"]
                self.assertEqual(initial["reason"], "HTTP_429")
                now[0] = 59
                refused = snap()
                self.assertEqual((refused["reason"], refused["attempted"]), ("RATE_LIMIT", False))
                self.assertEqual(series()["chart"]["reason"], "RATE_LIMIT")
                self.assertEqual(len(calls), 1)
                now[0] = 60
                self.assertTrue(snap()["attempted"])
                self.assertEqual(len(calls), 2)

    def test_gecko_budget_is_atomic_under_concurrent_reservations(self):
        now = [0]
        budget = GeckoTerminalRequestBudget(lambda: now[0])
        fanout = threading.Barrier(16)
        def reserve():
            fanout.wait(timeout=5)
            return budget.admit()
        with ThreadPoolExecutor(max_workers=16) as pool:
            admitted = list(pool.map(lambda _: reserve(), range(16)))
        self.assertEqual(sum(admitted), 8)
        now[0] = 59.99
        self.assertFalse(budget.admit())
        now[0] = 60
        self.assertTrue(budget.admit())


if __name__ == "__main__":
    unittest.main()
