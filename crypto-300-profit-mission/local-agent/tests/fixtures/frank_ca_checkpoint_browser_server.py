"""Foreground browser fixture for real CA checkpoint/Handler flow, synthetic I/O.

No production root, credentials, external network, service command or notification.
The process exits when stdin closes. It is not a monitor or installed service.
"""
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from urllib.parse import urlparse
import json
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mission_agent.meme.cluster import SolanaReadOnlyRPC
from mission_agent.meme.job_checkpoint import JobCheckpoint, CheckpointRPC
from mission_agent.mission_control import server


def offline_audit(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system'}:
        raise RuntimeError('OFFLINE_FIXTURE_NETWORK_OR_PROCESS_DENIED')
    if event == 'socket.bind' and args[1] != ('127.0.0.1', 0):
        raise RuntimeError('ONLY_RANDOM_LOOPBACK_FIXTURE_BIND_ALLOWED')


sys.addaudithook(offline_audit)
MINT = 'So11111111111111111111111111111111111111112'
wire, posts = [], []


class Response:
    def __init__(self, value): self.value = value
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps({'result': self.value}).encode()


def transport(request, timeout):
    payload = json.loads(request.data)
    assert payload['method'] in {'getTokenSupply', 'getTokenLargestAccounts'}
    assert payload['params'] == [MINT]
    wire.append(payload['method'])
    return Response({'value': 'SYNTHETIC_BROWSER_CHECKPOINT'})


class FixtureRPC(SolanaReadOnlyRPC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, open_url=transport, min_interval=0)


class FixtureAnalyzer:
    def __init__(self, mint, rpc, **kwargs): self.mint, self.rpc = mint, rpc
    def analyze(self):
        for method in ['getTokenSupply', 'getTokenLargestAccounts']:
            self.rpc.call(method, [self.mint], ttl=30)
        return {'schema_version': 2, 'source': 'SOLANA_FINALIZED_JSON_RPC', 'mint': self.mint,
            'observed_at': time.time(), 'coverage': {'scope': 'SYNTHETIC_BROWSER_CHECKPOINT',
                'special_normalization_complete': False, 'rpc_endpoint_failures': {}},
            'holders': [], 'metrics': {}, 'assessment': {'chain_permission_status': 'UNRESOLVED',
                'cluster_status': 'WALLET_CLUSTER_UNRESOLVED', 'trading_status': 'NO_GO'},
            'market': {'status': 'UNAVAILABLE', 'name': 'SYNTHETIC 恢复验收', 'symbol': 'QA'},
            'token_profile': {'status': 'UNAVAILABLE'}, 'transaction_errors': [],
            'limitations': ['SYNTHETIC_ONLY_NOT_A_REAL_CA_REPORT']}


class HoldingExecutor:
    def submit(self, *args): return Future()


server.SolanaReadOnlyRPC = FixtureRPC
server.WalletClusterAnalyzer = FixtureAnalyzer

with TemporaryDirectory(prefix='frank-ca-checkpoint-browser-') as scratch:
    manager = object.__new__(server.ClusterJobManager)
    manager.control_root = Path(scratch)
    manager.report_root = Path(scratch)/'reports'
    manager.report_root.mkdir()
    manager.checkpoint_root = manager.report_root/'_checkpoints'
    manager.cache_path = Path(scratch)/'cache.sqlite'
    manager.registry_path = Path(scratch)/'registry.json'
    manager.registry_path.write_text('{"schema_version":1,"addresses":{}}')
    manager.rpc_endpoints = ['https://disabled.invalid']
    manager.rpc_endpoint = manager.rpc_endpoints[0]
    manager.market_client = manager.independent_market_client = manager.narrative_client = None
    manager.evidence_enabled = False
    manager.lock, manager.jobs, manager.max_retained_jobs = threading.Lock(), {}, 64
    manager.executor = HoldingExecutor()
    job = manager.submit(MINT)
    checkpoint = JobCheckpoint(manager.checkpoint_root, job['job_id'])
    checkpoint.begin(manager._checkpoint_binding('standard'), server.CLUSTER_RPC_JOB_BUDGETS['standard'])
    CheckpointRPC(checkpoint, FixtureRPC(manager.rpc_endpoint, fallback_endpoints=[],
        **checkpoint.transport_budget())).call('getTokenSupply', [MINT], ttl=30)
    checkpoint.close()
    manager.jobs.clear()  # Only durable state remains; no source is read on GET.
    manager.executor = ThreadPoolExecutor(max_workers=1)

    class FixtureHandler(server.Handler):
        state = SimpleNamespace(cluster_jobs=manager)
        static_root = Path(server.__file__).parent/'static'
        def log_message(self, *args): pass
        def do_GET(self):
            path = urlparse(self.path).path
            if path == '/__fixture/stats':
                return self._json({'job_id': job['job_id'], 'mint': MINT, 'synthetic_wire': wire,
                                   'source_POSTs': len(posts), 'real_RPC': 0, 'production_writes': 0})
            if path.startswith('/api/') and path not in {'/api/cluster-analysis', '/api/cluster-latest'}:
                lists = {'/api/candidates', '/api/trades', '/api/decisions', '/api/review-activity'}
                return self._json([] if path in lists else {'status': 'SYNTHETIC_ONLY', 'rows': [], 'summary': {}})
            return super().do_GET()
        def do_POST(self):
            posts.append(1)
            return super().do_POST()

    httpd = server.DashboardHTTPServer(('127.0.0.1', 0), FixtureHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    print(json.dumps({'port': httpd.server_port, 'job_id': job['job_id'], 'mint': MINT,
                      'synthetic_wire': wire, 'real_RPC': 0, 'production_writes': 0}), flush=True)
    try: sys.stdin.read()
    finally:
        httpd.shutdown(); httpd.server_close(); thread.join(timeout=3)
        manager.executor.shutdown(wait=True)
