"""Controlled overlap in real market-series parsing, without provider requests."""
from concurrent.futures import ThreadPoolExecutor
import io
import json
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

from mission_agent.meme.ca_market_series import CAMarketSeries
from mission_agent.meme.holder_ranks import _b58


MINT_A, POOL_A, PEER_A, MINT_B, POOL_B, PEER_B = [_b58(bytes([n])*32) for n in range(1, 7)]
AT = 1795737600


def candle(mint, peer, price):
    return {"meta": {"base": {"address": mint}, "quote": {"address": peer}},
            "data": {"type": "ohlcv_request_response", "attributes": {
                "ohlcv_list": [[AT-300, price, price, price, price, 10]]}}}


class MarketSeriesSingleFlightTest(unittest.TestCase):
    def test_other_mint_and_pool_finishes_while_one_chart_is_held(self):
        entered, unblock = threading.Event(), threading.Event()
        urls = []

        def source(req, timeout):
            url = urlsplit(req.full_url)
            target = parse_qs(url.query)["token"][0]
            urls.append((target, "/ohlcv/" in url.path))
            if "/ohlcv/" in url.path:
                if target == MINT_A:
                    entered.set()
                    self.assertTrue(unblock.wait(5))
                body = candle(target, PEER_A if target == MINT_A else PEER_B, 7 if target == MINT_A else 13)
            else:
                body = {"data": []}
            return io.BytesIO(json.dumps(body).encode())

        series = CAMarketSeries(open_url=source, clock=lambda: AT)
        with ThreadPoolExecutor(max_workers=2) as work:
            deferred = work.submit(series.read, MINT_A, POOL_A, PEER_A, "5m")
            try:
                self.assertTrue(entered.wait(2))
                fast = work.submit(series.read, MINT_B, POOL_B, PEER_B, "5m").result(timeout=2)
                self.assertFalse(deferred.done())
                self.assertEqual((fast["mint"], fast["pool"], fast["chart"]["rows"][0][4]), (MINT_B, POOL_B, "13"))
                self.assertEqual(fast["trades"]["status"], "OK")
            finally:
                unblock.set()
            slow = deferred.result(timeout=3)
        self.assertEqual((slow["mint"], slow["pool"], slow["chart"]["rows"][0][4]), (MINT_A, POOL_A, "7"))
        self.assertEqual(urls, [(MINT_A, True), (MINT_B, True), (MINT_B, False), (MINT_A, False)])
        self.assertFalse(series._inflight)

    def test_per_key_overlap_shares_one_request_and_only_leader_claims_source_read(self):
        for fail in (False, True):
            with self.subTest(fail=fail):
                entered, unblock, wait_started = threading.Event(), threading.Event(), threading.Event()
                calls = []
                now = [AT]

                def source(req, timeout):
                    calls.append(req.full_url)
                    if len(calls)>1:
                        entered.set()
                        self.assertTrue(unblock.wait(5))
                        if fail:
                            raise HTTPError(req.full_url, 429, "fixture", {}, None)
                    return io.BytesIO(json.dumps(candle(MINT_A, PEER_A, 1 if len(calls)==1 else 2)).encode())

                series = CAMarketSeries(open_url=source, clock=lambda: now[0], monotonic=lambda: now[0])
                args = (MINT_A, POOL_A, PEER_A, "chart", "5m", "/ohlcv/minute")
                old = series._read_cached(*args)
                now[0] += 61
                with ThreadPoolExecutor(max_workers=2) as work:
                    leader = work.submit(series._read_cached, *args, refresh=True)
                    try:
                        self.assertTrue(entered.wait(2))
                        flight, = series._inflight.values()
                        event_wait = flight.ready.wait

                        def witness(*a, **kw):
                            wait_started.set()
                            return event_wait(*a, **kw)

                        with patch.object(flight.ready, "wait", side_effect=witness):
                            follower = work.submit(series._read_cached, *args, refresh=True)
                            self.assertTrue(wait_started.wait(2))
                            unblock.set()
                            shared = follower.result(timeout=2)
                    finally:
                        unblock.set()
                    wire = leader.result(timeout=2)
                self.assertEqual(len(calls), 2)  # Warm-up plus a single wire request for two refreshes.
                self.assertTrue(wire["source_attempted"])
                self.assertNotIn("source_coalesced", wire)
                self.assertFalse(shared["source_attempted"])
                self.assertTrue(shared["source_coalesced"])
                self.assertEqual(shared["rows"], wire["rows"])
                self.assertEqual(shared["status"], "STALE" if fail else "OK")
                self.assertEqual(shared["observed_at"], old["observed_at"] if fail else now[0])
                self.assertFalse(series._inflight)
