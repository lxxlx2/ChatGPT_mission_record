"""Synthetic clocks and provider replies only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import format_datetime
from io import BytesIO
import json
from urllib.parse import urlsplit
from tempfile import TemporaryDirectory
import threading
import unittest
from urllib.error import HTTPError

from mission_agent.meme.holder_ranks import _b58
from mission_agent.meme.market import DexScreenerMarketClient, DexScreenerRequestBudget, LOCAL_MARKET_PACING
from mission_agent.mission_control.market_observations import normalize_market
from mission_agent.mission_control.research_data import ResearchData


A, B, C = [_b58(bytes([n]) * 32) for n in (1, 2, 3)]


class DexScreenerPacingTest(unittest.TestCase):
    def setUp(self):
        self.elapsed = 0
        self.wall = 1795737600
        self.calls = []
        self.budget = DexScreenerRequestBudget(
            max_per_minute=2, monotonic=lambda: self.elapsed, wall_clock=lambda: self.wall)
        self.first = self.client()
        self.second = self.client()

    def client(self, transport=None):
        return DexScreenerMarketClient(open_url=transport or self.empty, clock=lambda: self.wall,
                                      request_budget=self.budget)

    def empty(self, request, *, timeout):
        self.calls.append(request.full_url)
        return BytesIO(b"[]")

    def test_single_batch_and_extra_worker_share_rolling_window_without_raw_side_effect(self):
        self.assertEqual(self.first.token_snapshot(A)["reason"], "NO_BASE_TOKEN_PAIR")
        self.assertEqual([r["mint"] for r in self.second.token_snapshots([B, C])], [B, C])
        self.assertEqual(len(self.calls), 2)
        self.assertIsNotNone(self.first.last_response_evidence)
        self.elapsed = 59.99
        blocked = self.first.token_snapshot(B)
        self.assertEqual(blocked["reason"], LOCAL_MARKET_PACING)
        self.assertEqual(normalize_market(B, blocked, received_at=self.wall)["reason"], LOCAL_MARKET_PACING)
        self.assertEqual(normalize_market(A, blocked, received_at=self.wall)["reason"], "OBSERVATION_TIME_INVALID")
        self.assertIsNone(blocked["observed_at"])
        self.assertIsNone(self.first.last_response_evidence)
        self.assertEqual(len(self.calls), 2)
        self.elapsed = 60
        self.assertEqual(self.first.token_snapshot(B)["reason"], "NO_BASE_TOKEN_PAIR")
        self.assertEqual(len(self.calls), 3)

    def test_terminal_429_sets_cooldown_for_other_route_and_preserves_actual_receipt(self):
        for batch_first, retry, duration in (
            (False, "25", 25),
            (True, format_datetime(datetime.fromtimestamp(self.wall + 30, timezone.utc), usegmt=True), 30),
            (False, None, 60),
        ):
            with self.subTest(batch_first=batch_first, retry=retry):
                self.elapsed = 0
                self.calls.clear()
                self.budget = DexScreenerRequestBudget(monotonic=lambda: self.elapsed, wall_clock=lambda: self.wall)

                def rate_limited(request, *, timeout):
                    self.calls.append(request.full_url)
                    raise HTTPError(request.full_url, 429, "test", {} if retry is None else {"Retry-After": retry},
                                    BytesIO(b'{"fixture":"429"}'))

                source, sibling = self.client(rate_limited), self.client()
                first = source.token_snapshots([A, C])[0] if batch_first else source.token_snapshot(A)
                self.assertEqual(first["reason"], "HTTP_429")
                self.assertEqual(source.last_response_evidence["response_bytes"], b'{"fixture":"429"}')
                self.elapsed = duration - 0.01
                self.assertEqual(sibling.token_snapshot(B)["reason"], LOCAL_MARKET_PACING)
                self.assertTrue(all(row["reason"] == LOCAL_MARKET_PACING for row in sibling.token_snapshots([B, C])))
                self.assertEqual(len(self.calls), 1)
                self.elapsed = duration
                self.assertEqual(sibling.token_snapshot(B)["reason"], "NO_BASE_TOKEN_PAIR")
                self.assertEqual(len(self.calls), 2)

    def test_concurrent_workers_admit_only_available_slots_under_one_injected_budget(self):
        barrier = threading.Barrier(6)

        def read(n):
            client = self.client()
            barrier.wait(timeout=3)
            return (client.token_snapshot(A) if n % 2 else client.token_snapshots([B])[0])["reason"]

        with ThreadPoolExecutor(max_workers=6) as workers:
            reasons = list(workers.map(read, range(6)))
        self.assertEqual(reasons.count(LOCAL_MARKET_PACING), 4)
        self.assertEqual(reasons.count("NO_BASE_TOKEN_PAIR"), 2)
        self.assertEqual(len(self.calls), 2)

    def test_bulk_rate_limit_preserves_last_complete_capture_and_stops_before_later_batches(self):
        def market_reply(request, *, timeout):
            self.calls.append(request.full_url)
            mints = urlsplit(request.full_url).path.rsplit("/", 1)[-1].split(",")
            pairs = [{"chainId": "solana", "pairAddress": C, "baseToken": {"address": mint},
                      "quoteToken": {"address": B}, "priceUsd": "1.25"} for mint in mints]
            return BytesIO(json.dumps(pairs).encode())

        with TemporaryDirectory() as root:
            market = ResearchData(root, wallet=A, rpc_factory=lambda: self.fail("market only"),
                                  market_client=self.client(market_reply),
                                  observed_mints=lambda: [_b58(n.to_bytes(32, "big")) for n in range(1, 66)],
                                  clock=lambda: self.wall)
            try:
                def run(key, scope, **extra):
                    submitted = market.submit("market", {"idempotency_key": key, "scope": scope, **extra})
                    market.executor.submit(lambda: None).result(timeout=5)
                    return market.job(submitted["job_id"])

                prior = run("first-one-mint", "mint", mint=A)
                self.assertEqual(prior["state"], "DONE")
                self.assertEqual(market.latest("market")["rows"][0]["price_usd"], "1.25")
                job = run("second-all-mints", "observed")
                self.assertEqual(job["state"], "ERROR")
                self.assertTrue(job["resume_allowed"])
                self.assertEqual(job["errors"], [{"code": LOCAL_MARKET_PACING}])
                self.assertIsNone(job["result_ref"])
                self.assertEqual(market.latest("market")["snapshot_id"], prior["result_ref"])
                self.assertEqual(len(self.calls), 2)  # First report + one batch, not every batch.
                staged = market._query("SELECT body FROM frank_market_stage WHERE job_id=?",
                                       (job["job_id"],))
                self.assertEqual(len(staged), 60)
                rows = [json.loads(row["body"]) for row in staged]
                self.assertEqual(sum(r["reason"] == LOCAL_MARKET_PACING and r["observed_at"] is None
                                     and r["source_ref"] is None for r in rows), 30)
            finally:
                market.executor.shutdown(wait=True)
