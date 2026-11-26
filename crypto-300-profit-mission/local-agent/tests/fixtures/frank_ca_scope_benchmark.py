"""Measure staged CA queue and market HTTP behavior with injected fixtures only.

Run from local-agent:
  python -B tests/fixtures/frank_ca_scope_benchmark.py --commit <full SHA> --samples 12

This measures fixture behavior and localhost HTTP, not Chrome, provider
latency, Solana correctness, or production SLA.
"""
import argparse
from collections import Counter
import hashlib
import http.client
import io
import json
import math
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
from threading import Event, Lock, Thread
import time
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mission_agent.meme.holder_ranks import _b58
from mission_agent.meme.job_checkpoint import source_fingerprint
from mission_agent.mission_control import server

FULL, TARGET, PEER, FIRST, SECOND, THIRD = [_b58(bytes([i]) * 32) for i in range(1, 7)]
FULL_FIXTURE_MS = 200
DETAIL_FIXTURE_MS = 40
CLOCK = time.perf_counter
PATH = "/api/cluster-analysis"
FIXTURE_PORTS = set()


def local_only(event, args):
    if event == "socket.bind" and args[1] != ("127.0.0.1", 0):
        raise RuntimeError("only ephemeral loopback bind is allowed")
    if event in {"socket.connect", "socket.getaddrinfo"}:
        addr = args[1] if event == "socket.connect" else args[:2]
        if not isinstance(addr, tuple) or len(addr) != 2 or addr[0] != "127.0.0.1" or addr[1] not in FIXTURE_PORTS:
            raise RuntimeError("only the fixture HTTP port is allowed")
    if event in {"subprocess.Popen", "os.system"}:
        raise RuntimeError("no subprocesses are allowed in the fixture")


def request(port, path, *, post=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request("GET" if post is None else "POST", path, body=None if post is None else json.dumps(post),
                     headers={"X-Frank-Research-Read": "1"} if post is None
                     else {"Content-Type": "application/json"})
        response = conn.getresponse()
        return response.status, json.loads(response.read())
    finally:
        conn.close()


def elapsed(start):
    return round((CLOCK() - start) * 1000, 3)


def percentile(values, p):
    ordered = sorted(values)
    return ordered[math.ceil(p * len(ordered)) - 1]


def run_sample(root, *, parallel):
    entered = Event()
    counter_guard = Lock()
    calls = Counter()
    throttle = Event()
    pairs = [{"pair_address": pool, "base_address": TARGET, "quote_address": PEER, "liquidity_usd": "9"}
             for pool in (FIRST, SECOND, THIRD)]
    profile = {"status": "OK", "is_initialized": True}
    market = {"status": "OK", "chain": "solana", "mint": TARGET, "name": "Synthetic",
              "price_usd": "1", "main_pair": pairs[0], "pool_candidates": pairs}

    class FakeAnalyzer:
        def __init__(self, mint, **opts):
            self.mint = mint
            self.opts = opts

        def analyze(self):
            if self.mint == FULL:
                entered.set()
                time.sleep(FULL_FIXTURE_MS / 1000)
            else:
                self.opts["progress_callback"]("BASE_READY", {"token_profile": profile, "market": market})
                time.sleep(DETAIL_FIXTURE_MS / 1000)
            return {
                "schema_version": 2, "source": "SOLANA_FINALIZED_JSON_RPC", "mint": self.mint,
                "observed_at": time.time(), "coverage": {}, "holders": [], "metrics": {}, "assessment": {},
                "token_profile": profile if self.mint == TARGET else {}, "limitations": [],
                "market": market if self.mint == TARGET else {},
            }

    def gecko_fixture(request, timeout):
        path = urlsplit(request.full_url).path
        with counter_guard:
            calls["chart" if "/ohlcv/" in path else "trades"] += 1
        if throttle.is_set():
            raise HTTPError(request.full_url, 429, "injected", {}, None)
        if "/ohlcv/" in path:
            payload = {"meta": {"base": {"address": TARGET}, "quote": {"address": PEER}},
                       "data": {"type": "ohlcv_request_response", "attributes": {
                           "ohlcv_list": [[int(time.time()) - 60, 1, 1, 1, 1, 1]],
                       }}}
        else:
            payload = {"data": []}
        return io.BytesIO(json.dumps(payload).encode())

    def no_rpc(*_args, **_kwargs):
        raise AssertionError("fixture may not dispatch RPC")

    rpc_class = server.SolanaReadOnlyRPC
    def injected_rpc(*args, **kwargs):
        return rpc_class(*args, **kwargs, open_url=no_rpc)

    manager = server.ClusterJobManager(root, parallel_ca_scopes=parallel)
    manager.ca_market_series.open_url = gecko_fixture
    manager.independent_market_client.open_url = no_rpc

    class LocalHandler(server.Handler):
        state = SimpleNamespace(cluster_jobs=manager)

        def log_message(self, *_):
            pass

    with patch.object(server, "WalletClusterAnalyzer", FakeAnalyzer), patch.object(
        server, "SolanaReadOnlyRPC", injected_rpc
    ), server.DashboardHTTPServer(("127.0.0.1", 0), LocalHandler) as httpd:
        thread = Thread(target=httpd.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
        thread.start()
        port = httpd.server_port
        FIXTURE_PORTS.add(port)
        try:
            status, full = request(port, PATH, post={"mint": FULL, "scope": "full"})
            if status != 202 or not entered.wait(3):
                raise RuntimeError("full fixture did not occupy its worker")
            start = CLOCK()
            status, overview = request(port, PATH, post={"mint": TARGET, "scope": "overview"})
            if status != 202:
                raise RuntimeError("fixture overview submit failed")
            first, polls = None, 0
            path = PATH + "?" + urlencode({"job_id": overview["job_id"]})
            until = CLOCK() + 5
            while CLOCK() < until:
                status, result = request(port, path)
                polls += 1
                if status != 200 or result.get("status") == "ERROR":
                    raise RuntimeError("fixture status poll failed")
                preview = result.get("preview") or {}
                if (first is None and preview.get("market_bound") is True
                        and preview.get("price_usd") == "1" and preview.get("pair_address") == FIRST):
                    first = elapsed(start)
                if result.get("status") == "DONE":
                    break
                time.sleep(.005)
            else:
                raise RuntimeError("fixture overview did not finish")
            status, report = request(port, "/api/cluster-latest?" + urlencode({"mint": TARGET, "job_id": overview["job_id"]}))
            if status != 200 or report.get("mint") != TARGET or report.get("ca_job_id") != overview["job_id"] or first is None:
                raise RuntimeError("fixture first usable preview or scoped report missing")
            rows = {"overview_while_full": {"first_usable_ms": first, "complete_ms": elapsed(start),
                                            "http_requests": 2 + polls, "provider_calls": 0,
                                            "full_status_when_read": manager.get(full["job_id"])["status"]}}

            def measure(pool, period, expected, expected_calls):
                url = "/api/cluster-market-series?" + urlencode(
                    {"mint": TARGET, "job_id": overview["job_id"], "pool": pool, "period": period}
                )
                prior = sum(calls.values())
                started = CLOCK()
                status, data = request(port, url)
                end = elapsed(started)
                states = tuple((data.get(k) or {}).get("status") for k in ("chart", "trades"))
                if (status != 200 or data.get("pool") != pool or data.get("mint") != TARGET
                        or data.get("job_id") != overview["job_id"] or states != expected
                        or sum(calls.values()) - prior != expected_calls):
                    raise RuntimeError("fixture market identity/status mismatch")
                usable = any(bool((data.get(key) or {}).get("rows")) for key in ("chart", "trades"))
                return {"first_usable_ms": end if usable else None, "complete_ms": end,
                        "http_requests": 1, "provider_calls": sum(calls.values()) - prior,
                        "chart": states[0], "trades": states[1],
                        "chart_reason": data["chart"].get("reason"),
                        "trades_reason": data["trades"].get("reason")}

            both = ("OK", "OK")
            rows["market_cold"] = measure(FIRST, "5m", both, 2)
            rows["market_warm"] = measure(FIRST, "5m", both, 0)
            rows["market_switch_pool"] = measure(SECOND, "5m", both, 2)
            throttle.set()
            rows["market_throttle"] = measure(THIRD, "5m", ("UNAVAILABLE", "UNAVAILABLE"), 1)
            if (rows["market_throttle"]["chart_reason"], rows["market_throttle"]["trades_reason"]) != ("HTTP_429", "RATE_LIMIT"):
                raise RuntimeError("fixture throttle was not observed")
            return rows
        finally:
            FIXTURE_PORTS.discard(port)
            httpd.shutdown()
            thread.join(timeout=5)
            manager.shutdown()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--commit", required=True, help="full checked-out source SHA supplied by runner")
    args = parser.parse_args()
    if not 2 <= args.samples <= 100 or not re.fullmatch(r"[a-f0-9]{40}", args.commit):
        parser.error("require 2–100 samples and a full Git commit SHA")
    sys.addaudithook(local_only)
    variants = {}
    for name, parallel in (("serial", False), ("parallel_opt_in", True)):
        samples = []
        for _ in range(args.samples):
            with TemporaryDirectory(prefix="frank-ca-fixture-") as tmp:
                samples.append(run_sample(Path(tmp), parallel=parallel))
        variants[name] = {}
        for case in samples[0]:
            rows = [s[case] for s in samples]
            complete = [r["complete_ms"] for r in rows]
            usable = [r["first_usable_ms"] for r in rows if r["first_usable_ms"] is not None]
            variants[name][case] = {
                "first_usable_samples": len(usable),
                "first_usable_ms": {"p50": percentile(usable, .50), "p95": percentile(usable, .95)} if usable else None,
                "complete_ms": {"p50": percentile(complete, .50), "p95": percentile(complete, .95)},
                "observations": rows,
            }
    print(json.dumps({
        "schema_version": 1, "kind": "SYNTHETIC_LOOPBACK_HTTP_ONLY",
        "commit_supplied_by_runner": args.commit, "product_source_sha256": source_fingerprint(),
        "fixture_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "samples_per_variant": args.samples, "percentile": "nearest-rank",
        "full_fixture_ms": FULL_FIXTURE_MS, "details_fixture_ms": DETAIL_FIXTURE_MS,
        "production_or_live_source_measured": False, "browser_measured": False, "variants": variants,
    }, indent=2))


if __name__ == "__main__":
    main()
