"""Isolated transport timing and backoff; no sockets or real endpoints."""
import io
import json
import unittest
from urllib.error import HTTPError

from mission_agent.meme.cluster import RPCJobBudgetExceeded, SolanaReadOnlyRPC
from mission_agent.meme.provider_pacing import SharedProviderPacing


class Clock:
    now = 100.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class SharedProviderTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.pacing = SharedProviderPacing(monotonic=self.clock.monotonic)
        self.calls = []

    def client(self, endpoint, *, limited=False, fallback=None, budget=None):
        clock = self.clock
        def transport(request, timeout):
            self.calls.append((request.full_url, clock.now))
            if limited:
                raise HTTPError(request.full_url, 429, "fixture", {"Retry-After": "5"}, None)
            return io.BytesIO(json.dumps({"result": "fixture"}).encode())
        return SolanaReadOnlyRPC(endpoint, fallback_endpoints=fallback or [],
                                 min_interval=0.5, shared_pacing=self.pacing,
                                 monotonic=clock.monotonic, sleep=clock.sleep,
                                 open_url=transport, max_wire_attempts=budget)

    def test_two_clients_share_host_interval_but_not_separate_host(self):
        self.client("https://fixture.invalid/a").call("getTokenSupply", ["one"])
        self.client("https://fixture.invalid/b").call("getTokenSupply", ["two"])
        self.client("https://separate.invalid/a").call("getTokenSupply", ["three"])
        self.assertEqual([when for _, when in self.calls], [100.0, 100.5, 100.5])

    def test_terminal_rate_limit_is_shared_in_other_worker(self):
        first = self.client("https://fixture.invalid/a", limited=True, budget=1)
        with self.assertRaises(RPCJobBudgetExceeded):
            first.call("getTokenSupply", ["one"])
        self.client("https://fixture.invalid/b", fallback=["https://spare.invalid/"]).call("getTokenSupply", ["two"])
        self.client("https://fixture.invalid/b").call("getTokenSupply", ["three"])
        self.assertEqual(self.calls, [("https://fixture.invalid/a", 100.0),
                                      ("https://spare.invalid/", 100.0),
                                      ("https://fixture.invalid/b", 105.0)])
