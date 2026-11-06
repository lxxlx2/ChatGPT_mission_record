"""Local-only service entry probes; all data and effects remain in pytest tmp_path."""
import copy
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from mission_agent.frank.rpc import WALLET
from mission_agent.signals.store import Ledger
from mission_agent.signals.scanner import WalletRPC
from scripts import frank_local_signal_service as service

POLICY = Path(service.__file__).resolve().parents[1] / 'config/frank_local_signal_v1.json'
ENDPOINT = 'https://example.test/fixture-private-token'


def args(monkeypatch, root, registry):
    monkeypatch.setattr(sys, 'argv', ['frank-local', '--root', str(root), '--registry', str(registry), '--policy', str(POLICY), '--authority-lock', str(root / 'authority.lock')])


def config(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    path = tmp_path / 'Library/Application Support/FrankMeme/solana_rpc_urls'
    path.parent.mkdir(parents=True)
    path.write_text(ENDPOINT)
    path.chmod(0o600)
    return path


@pytest.mark.parametrize('failure', ['missing', 'symlink', 'permissions', 'bad-port'])
def test_bad_config_stops_before_database_or_delivery(tmp_path, monkeypatch, failure):
    path = config(monkeypatch, tmp_path)
    if failure == 'missing': path.unlink()
    if failure == 'symlink':
        target = path.with_name('target')
        path.rename(target)
        path.symlink_to(target)
    if failure == 'permissions': path.chmod(0o644)
    if failure == 'bad-port': path.write_text('https://example.test:fixture-secret')
    root = tmp_path / 'state'
    args(monkeypatch, root, tmp_path / 'registry.json')
    def forbidden(*a, **kw): raise AssertionError('database/RPC/delivery must not be constructed')
    for name in ('Ledger', 'WalletRPC', 'LocalNotifier', 'drain'):
        monkeypatch.setattr(service, name, forbidden)
    with pytest.raises(RuntimeError, match='^FRANK_RPC_CONFIG_UNAVAILABLE_OR_INVALID$'):
        service.main()
    assert not root.exists()


@pytest.mark.parametrize('fail_method', [None, 'getSlot', 'getSignaturesForAddress', 'getTransaction'])
def test_service_entry_private_rpc_and_timeout_recovery(tmp_path, monkeypatch, fail_method):
    config(monkeypatch, tmp_path)
    root = tmp_path / 'state'
    root.mkdir()
    registry = tmp_path / 'registry.json'
    registry.write_text(json.dumps({'persons': [{'person_id': 'frank', 'enabled': True, 'wallets': [{'chain': 'solana', 'address': WALLET}]}]}))
    ledger = Ledger(root / 'forward.sqlite')
    ledger.checkpoint(WALLET, 'seed', 11)
    ledger.db.close()
    args(monkeypatch, root, registry)
    handlers, calls, snapshots, model_calls, delivery_calls = {}, [], [], [], []
    now = [0.0]
    def sleep(delay): now[0] += delay
    monkeypatch.setattr(service, 'time', SimpleNamespace(monotonic=lambda: now[0], sleep=sleep, time=time.time))
    monkeypatch.setattr(service.signal, 'signal', lambda sig, handler: handlers.update({sig: handler}))
    failures = [0]
    class Response:
        def __init__(self, value): self.value = value
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return json.dumps({'result': self.value}).encode()
    def request(req, timeout):
        payload = json.loads(req.data)
        method = payload['method']
        calls.append((req.full_url, timeout, method))
        if method == fail_method and failures[0] < 3:
            failures[0] += 1
            raise TimeoutError(ENDPOINT)
        if method == 'getSlot': return Response(13)
        if method == 'getBlockTime': return Response(int(time.time()))
        if method == 'getSignaturesForAddress':
            assert payload['params'][0] == WALLET
            return Response([{'signature': 'new', 'slot': 12}, {'signature': 'seed', 'slot': 11}])
        assert method == 'getTransaction'
        return Response({'slot': 12, 'blockTime': int(time.time()) - 10})
    def wallet_rpc(wallet, *, endpoint):
        assert endpoint == ENDPOINT
        return WalletRPC(wallet, endpoint=endpoint, request=request, sleep=sleep, monotonic=lambda: now[0], jitter=lambda: 0)
    monkeypatch.setattr(service, 'WalletRPC', wallet_rpc)
    original_engine = service.Engine
    def engine(*a, **kw):
        result = original_engine(*a, **kw)
        original_drain = result.drain
        def drain_model(*a, **kw):
            model_calls.append(1)
            return original_drain(*a, **kw)
        result.drain = drain_model
        return result
    monkeypatch.setattr(service, 'Engine', engine)
    monkeypatch.setattr(service, 'LocalNotifier', lambda **kw: object())
    def drain_local(ledger, notifier):
        delivery_calls.append(1)
        handlers[service.signal.SIGTERM]()
        return []
    monkeypatch.setattr(service, 'drain', drain_local)
    original_atomic = service.atomic_json
    def atomic(path, value):
        if path.name == 'health.json': snapshots.append(copy.deepcopy(value))
        return original_atomic(path, value)
    monkeypatch.setattr(service, 'atomic_json', atomic)
    service.main()
    assert len(model_calls) == len(delivery_calls) == 1
    assert all(url == ENDPOINT and timeout == 20 for url, timeout, _ in calls)
    assert 'fixture-private-token' not in json.dumps(snapshots)
    assert all(s['production_trading'] == 'NO_GO' for s in snapshots)
    if fail_method:
        assert failures[0] == 3
        errors = [s for s in snapshots if s['status'] == 'RETRY_PENDING']
        assert len(errors) == 1 and errors[0]['consecutive_errors'] == 1
        assert errors[0]['last_error'] == 'RPCFailure:TIMEOUT_OR_NETWORK'
    assert snapshots[-2]['status'] == 'RUNNING' and snapshots[-2]['consecutive_errors'] == 0
    assert snapshots[-1]['status'] == 'STOPPED'
    first = json.loads((root / 'first-cycle.json').read_text())
    assert first['status'] == 'PASS' and first['gap'] == 0 and first['catchup_signatures'] == 1
    assert first['cursor_before'][WALLET]['signature'] == 'seed'
    assert first['cursor_after'][WALLET]['signature'] == 'new'
    ledger = Ledger(root / 'forward.sqlite')
    assert ledger.cursor(WALLET)['signature'] == 'new'
    assert ledger.db.execute('SELECT count(*) FROM signatures').fetchone()[0] == 1
    assert ledger.db.execute('SELECT count(*) FROM outbox').fetchone()[0] == 0
    assert ledger.db.execute('SELECT count(*) FROM signature_detections WHERE state="RAW_PENDING"').fetchone()[0] == 0
    ledger.db.close()
