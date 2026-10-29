"""Temporary CA browser fixture: real Handler/manager, synthetic analyzer, no network.

Invoked only by test_frank_ca_browser.mjs. No DashboardState/production root,
provider clients, keys or production files. The fixture exits when stdin closes.
"""
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from urllib.parse import urlparse
import json
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mission_agent.mission_control import server  # noqa: E402


def offline_audit(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system'}:
        raise RuntimeError('OFFLINE_FIXTURE_NETWORK_OR_PROCESS_DENIED')
    if event == 'socket.bind' and args[1] != ('127.0.0.1', 0):
        raise RuntimeError('ONLY_RANDOM_LOOPBACK_FIXTURE_BIND_ALLOWED')


sys.addaudithook(offline_audit)


class FixtureRPC:
    def __init__(self, *args, **kwargs):
        self.calls = 0

    def assert_can_publish(self):
        pass


class FixtureAnalyzer:
    count = 0

    def __init__(self, mint, **kwargs):
        self.mint = mint
        self.progress = kwargs['progress_callback']

    def analyze(self):
        type(self).count += 1
        name = f'SYNTHETIC_REPORT_{type(self).count}'
        self.progress('TOKEN_PROFILE', {'fixture': True})
        time.sleep(0.15)
        if self.mint == '4' * 32:
            raise ValueError('FIXTURE_ANALYZER_ERROR')
        return {
            'schema_version': 2, 'source': 'SOLANA_FINALIZED_JSON_RPC',
            'mint': self.mint, 'observed_at': time.time(),
            'coverage': {'special_normalization_complete': False,
                         'deep_holders_scanned': 1, 'top_accounts_resolved': 1},
            'holders': [], 'metrics': {}, 'assessment': {}, 'token_profile': {},
            'market': {'status': 'UNAVAILABLE', 'name': name, 'symbol': 'FIXTURE', 'main_pair': {}},
            'limitations': ['SYNTHETIC_ONLY_NO_CHAIN_REQUEST'],
        }


server.SolanaReadOnlyRPC = FixtureRPC
server.WalletClusterAnalyzer = FixtureAnalyzer
server.load_registry = lambda _: {}

with TemporaryDirectory(prefix='frank-ca-browser-') as scratch:
    # Deliberately do not call DashboardState or manager __init__ (providers).
    manager = object.__new__(server.ClusterJobManager)
    manager.lock = threading.Lock()
    manager.jobs = {}
    manager.max_retained_jobs = 64
    manager.report_root = Path(scratch) / 'reports'
    manager.report_root.mkdir()
    manager.cache_path = Path(scratch) / 'cache.sqlite'
    manager.rpc_endpoints = ['https://disabled.invalid']
    manager.rpc_endpoint = manager.rpc_endpoints[0]
    manager.registry_path = Path(scratch) / 'registry.json'
    manager.market_client = None
    manager.evidence_enabled = False
    manager.executor = ThreadPoolExecutor(max_workers=1)

    class FixtureHandler(server.Handler):
        state = SimpleNamespace(cluster_jobs=manager)
        static_root = Path(server.__file__).parent / 'static'

        def log_message(self, *args):
            pass

        def do_GET(self):
            path = urlparse(self.path).path
            if path == '/__fixture/reset-memory':
                # Test-only equivalent of a new manager reading disk, no lifecycle action.
                with manager.lock:
                    manager.jobs.clear()
                return self._json({'cleared': True})
            if path.startswith('/api/') and path not in {'/api/cluster-analysis', '/api/cluster-latest'}:
                lists = {'/api/candidates', '/api/trades', '/api/decisions', '/api/review-activity'}
                return self._json([] if path in lists else {'status': 'TEST_FIXTURE', 'rows': [], 'summary': {}})
            return super().do_GET()

        def do_POST(self):
            # The only POST exercises the real submit/worker with the analyzer replaced above.
            return super().do_POST()

    httpd = ThreadingHTTPServer(('127.0.0.1', 0), FixtureHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    print(json.dumps({'port': httpd.server_port, 'pid': __import__('os').getpid()}), flush=True)
    try:
        sys.stdin.read()
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=3)
        manager.executor.shutdown(wait=True)
