"""Synthetic real-Handler Chrome fixture, never an actual Frank or RPC environment."""
from collections import Counter
import io
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Event, Lock, Thread
import time
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mission_agent.meme.holder_ranks import _b58
from mission_agent.mission_control import server


def offline_only(event, args):
    if event == "socket.bind" and args[1] != ("127.0.0.1", 0):
        raise RuntimeError("EPHEMERAL_LOOPBACK_ONLY")
    if event in {"socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system"}:
        raise RuntimeError("FIXTURE_EXTERNAL_ACTION_DENIED")


def main():
    sys.addaudithook(offline_only)
    # Do not inherit user source selections or notification/export settings.
    for key in tuple(os.environ):
        if key.startswith(("SOLANA_RPC", "JUPITER_", "MISSION_EVIDENCE_")):
            del os.environ[key]
    a, b, owner, peer, pool_a, pool_b = [_b58(bytes([i]) * 32) for i in range(1, 7)]
    release = Event()
    throttle = Event()
    call_lock = Lock()
    calls = Counter()

    def no_network(*_args, **_kwargs):
        raise RuntimeError("UNEXPECTED_PROVIDER_REQUEST")

    rpc_type = server.SolanaReadOnlyRPC
    server.SolanaReadOnlyRPC = lambda *args, **options: rpc_type(*args, open_url=no_network, **options)

    class FixtureAnalyzer:
        def __init__(self, mint, **options):
            self.mint, self.options = mint, options

        def analyze(self):
            scope = self.options["query_scope"]
            if self.mint not in (a, b):
                raise AssertionError("unexpected fixture Mint")
            if self.mint == a and scope == "full":
                if not release.wait(90):
                    raise TimeoutError("fixture stalled")
            pair = {"pair_address": pool_a if self.mint == a else pool_b, "base_address": self.mint,
                    "quote_address": peer, "dex_id": "fixture", "liquidity_usd": "10"}
            market = {"status": "OK", "chain": "solana", "mint": self.mint, "name": "Stage A" if self.mint == a else "Stage B",
                      "symbol": "STGA" if self.mint == a else "STGB", "main_pair": pair, "price_usd": "1"}
            profile = {"status": "OK", "is_initialized": True}
            holder = {"owner": owner, "raw": "100", "ui_amount": "100", "supply_pct": "1", "account_count": 1}
            self.options["progress_callback"]("BASE_READY", {"token_profile": profile, "market": market})
            report = {"schema_version": 2, "source": "SOLANA_FINALIZED_JSON_RPC", "mint": self.mint,
                      "observed_at": time.time(), "coverage": {}, "holders": [holder], "metrics": {},
                      "assessment": {}, "token_profile": profile, "limitations": [], "market": market, "decimals": 0}
            if scope == "wallet":
                base = self.options["wallet_base"]
                if base["mint"] != self.mint or self.options["focus_owner"] != owner:
                    raise AssertionError("unbound fixture wallet")
                report["wallet_detail"] = {**holder, "balance_observed_at": base["observed_at"]}
            return report

    server.WalletClusterAnalyzer = FixtureAnalyzer

    def gecko_fixture(request, timeout):
        path = urlsplit(request.full_url).path.split("/")
        pool = path[6]
        mint = {pool_a: a, pool_b: b}[pool]
        key = "chart" if path[7] == "ohlcv" else "trades"
        with call_lock:
            calls[key] += 1
        if throttle.is_set():
            raise HTTPError(request.full_url, 429, "injected fixture throttle", {}, None)
        result = {"data": []}
        if key == "chart":
            result = {"meta": {"base": {"address": mint}, "quote": {"address": peer}},
                      "data": {"type": "ohlcv_request_response", "attributes": {
                          "ohlcv_list": [[int(time.time()) - 60, 1, 1, 1, 1, 1]],
                      }}}
        return io.BytesIO(json.dumps(result).encode())

    with TemporaryDirectory(prefix="frank-parallel-ca-browser-") as tmp:
        manager = server.ClusterJobManager(Path(tmp), parallel_ca_scopes=True)
        manager.ca_market_series.open_url = gecko_fixture
        manager.independent_market_client.open_url = no_network

        class Handler(server.Handler):
            state = SimpleNamespace(cluster_jobs=manager)
            reads = {"/api/cluster-analysis", "/api/cluster-latest", "/api/cluster-market-series"}

            def do_GET(self):
                path = urlsplit(self.path).path
                if path == "/__fixture/release":
                    release.set()
                    return self._json({"released": True})
                if path == "/__fixture/throttle":
                    throttle.set()
                    return self._json({"throttle": True})
                if path == "/__fixture/counts":
                    with call_lock:
                        return self._json(dict(calls))
                if path.startswith("/api/") and path not in self.reads:
                    lists = {"/api/candidates", "/api/trades", "/api/decisions", "/api/review-activity"}
                    return self._json([] if path in lists else {"status": "FIXTURE", "rows": [], "summary": {}})
                return super().do_GET()

            def do_POST(self):
                if self.path != "/api/cluster-analysis":
                    return self.send_error(404)
                return super().do_POST()

        with server.DashboardHTTPServer(("127.0.0.1", 0), Handler) as host:
            thread = Thread(target=host.serve_forever, daemon=True)
            thread.start()
            print(json.dumps({"port": host.server_port, "mint_a": a, "mint_b": b,
                              "owner": owner, "pool_b": pool_b}), flush=True)
            try:
                sys.stdin.read()
            finally:
                release.set()
                host.shutdown()
                thread.join(timeout=5)
                manager.shutdown()


if __name__ == "__main__":
    main()
