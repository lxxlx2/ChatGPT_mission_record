"""Isolated CA job checkpoint tests. No real transport or production state."""
from concurrent.futures import Future
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from mission_agent.mission_control.server import ClusterJobManager
from mission_agent.meme import cluster
from mission_agent.meme.job_checkpoint import JobCheckpoint, CheckpointRPC, CheckpointClient, CheckpointError


MINT = 'So11111111111111111111111111111111111111112'


class HoldingExecutor:
    def __init__(self): self.calls = []

    def submit(self, *args):
        self.calls.append(args)
        return Future()

    def shutdown(self, *args, **kwargs):
        pass


def test_acknowledged_unfinished_job_survives_manager_recreation_without_rpc(tmp_path):
    first = ClusterJobManager(tmp_path)
    first.executor.shutdown()
    first.executor = HoldingExecutor()
    try:
        submitted = first.submit(MINT)
        restarted = ClusterJobManager(tmp_path)
        try:
            restored = restarted.get(submitted['job_id'])
            assert restored is not None
            assert restored['job_id'] == submitted['job_id']
            assert restored['mint'] == MINT
            assert restored['status'] == 'PAUSED'
            assert restored['resume_available'] is True
            assert restarted.jobs == {}
        finally:
            restarted.executor.shutdown()
    finally:
        first.executor.shutdown()


JOB = 'a' * 32
BUDGET = {'max_wire_attempts': 8, 'max_elapsed_seconds': 60}


def create_checkpoint(path, *, budget=None, clock=None):
    kwargs = {'clock': clock} if clock is not None else {}
    JobCheckpoint.create(path, {'job_id': JOB, 'mint': MINT, 'preset': 'standard', 'created_at': 1},
                         'fixture-binding', budget or BUDGET, **kwargs)


class Response:
    def __init__(self, value): self.value = value
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps({'result': self.value}).encode()


def wrapped(checkpoint, transport, *, cache=None):
    rpc = cluster.SolanaReadOnlyRPC('https://fixture.invalid/PRIVATE_TOKEN', fallback_endpoints=[],
        open_url=transport, cache=cache, min_interval=0, **checkpoint.transport_budget())
    return CheckpointRPC(checkpoint, rpc)


def run_holder_window(root, crash=False):
    root = Path(root)
    checkpoint = JobCheckpoint(root, JOB)
    checkpoint.begin('fixture-binding')
    def transport(request, timeout):
        req = json.loads(request.data); method, params = req['method'], req['params']
        with (root/'transport-trace.jsonl').open('a') as f:
            f.write(json.dumps([method, params[0]])+'\n')
        if method == 'getSignaturesForAddress':
            value = [] if 'before' in params[1] else [
                {'signature': 's'+str(i), 'slot': 100-i, 'blockTime': 200-i} for i in range(3)]
        else:
            assert method == 'getTransaction'
            sig = params[0]
            if crash and sig == 's2': os._exit(73)
            i = int(sig[1:])
            value = {'slot': 100-i, 'blockTime': 200-i,
                'transaction': {'signatures': [sig], 'message': {'accountKeys': [], 'instructions': []}},
                'meta': {'err': None, 'preBalances': [], 'postBalances': [], 'preTokenBalances': [], 'postTokenBalances': []}}
        return Response(value)
    rpc = wrapped(checkpoint, transport)
    engine = cluster.WalletClusterAnalyzer(MINT, rpc=rpc, history_max_pages=2)
    holder = cluster.Holder('token-account', 'owner', 1, 0, 'ORDINARY', 'fixture')
    original = cluster.classify
    cluster.classify = lambda sig, tx, owner: {'classification': 'ACTIVE_TRADE', 'trade': {
        'mint': MINT, 'direction': 'BUY', 'quote_asset': 'USDC', 'quote_amount_raw': '1',
        'quote_decimals': 0, 'token_amount_raw': '1', 'token_decimals': 0}} if sig == 's2' else {'classification': 'UNKNOWN_NEEDS_REVIEW'}
    try:
        first = engine._scan_holder(holder, {'token-account': 'owner'}, {'owner'}, 3)
        rpc.assert_can_publish()
        return {'first': first, 'trades': engine.trades, 'window': engine.history_attempts[0],
                'provenance': checkpoint.provenance()}
    finally:
        cluster.classify = original
        checkpoint.close()


def test_real_process_exit_inside_page_reconstructs_prefix_and_only_reads_missing_suffix(tmp_path):
    create_checkpoint(tmp_path)
    child = subprocess.run([sys.executable, '-B', '-c',
        "import runpy,sys; ns=runpy.run_path(sys.argv[1]); ns['run_holder_window'](sys.argv[2], crash=True)",
        str(Path(__file__).resolve()), str(tmp_path)], capture_output=True, timeout=15)
    assert child.returncode == 73, child.stderr.decode()
    interrupted = JobCheckpoint(tmp_path, JOB, readonly=True)
    assert interrupted.meta['wire_used'] == 4  # Three saved results and one uncertain attempt.
    assert len(interrupted.entries) == 3
    interrupted.close()
    restored = run_holder_window(tmp_path)
    trace = [json.loads(x) for x in (tmp_path/'transport-trace.jsonl').read_text().splitlines()]
    assert len(trace) == 6
    assert trace[-2:] == [['getTransaction', 's2'], ['getSignaturesForAddress', 'token-account']]
    assert restored['first']['signature'] == 's2' and len(restored['trades']) == 1
    assert restored['window']['signature_count'] == 3
    assert restored['window']['next_before'] == 's2'
    assert restored['window']['stop_reason'] == 'PROVIDER_EMPTY_PAGE'
    assert restored['window']['history_complete'] is False
    assert restored['provenance']['replayed_logical_reads'] == 3
    assert restored['provenance']['reserved_wire_attempts'] == 6


def test_replay_does_not_refresh_expired_rpc_cache_or_count_it_as_new_cache_hit(tmp_path):
    import time
    create_checkpoint(tmp_path/'job')
    cache = cluster.RpcCache(tmp_path/'cache.sqlite')
    cache.put('getTokenSupply', [MINT], {'value': 'historical'}, 30, time.time())
    first = JobCheckpoint(tmp_path/'job', JOB); first.begin('fixture-binding')
    def denied(*args, **kwargs): raise AssertionError('NO_TRANSPORT_EXPECTED')
    rpc = wrapped(first, denied, cache=cache)
    assert rpc.call('getTokenSupply', [MINT], ttl=30) == {'value': 'historical'}
    assert rpc.cache_hits == 1 and rpc.calls == 0
    first.close()
    cache.db.execute('UPDATE rpc_cache SET expires_at=0'); cache.db.commit()
    second = JobCheckpoint(tmp_path/'job', JOB); second.begin('fixture-binding')
    rpc = wrapped(second, denied, cache=cache)
    assert rpc.call('getTokenSupply', [MINT], ttl=30) == {'value': 'historical'}
    assert rpc.calls == 0 and rpc.cache_hits == 1
    assert second.replayed == 1 and second.meta['resume_count'] == 1
    assert cache.db.execute('SELECT expires_at FROM rpc_cache').fetchone()[0] == 0
    second.close(); cache.close()


def test_changed_read_sequence_remains_fail_closed_even_if_a_caller_catches_the_error(tmp_path):
    create_checkpoint(tmp_path)
    first = JobCheckpoint(tmp_path, JOB); first.begin('fixture-binding')
    first.invoke('fixture', 'read', ['old'], {}, lambda: {'value': 'old'})
    first.close()
    second = JobCheckpoint(tmp_path, JOB); second.begin('fixture-binding')
    with pytest.raises(CheckpointError, match='READ_SEQUENCE_CHANGED'):
        second.invoke('fixture', 'read', ['new'], {}, lambda: pytest.fail('MUST_NOT_READ_SOURCE'))
    with pytest.raises(CheckpointError): second.assert_can_publish()
    second.close()


def test_restart_cannot_reset_cumulative_wire_limit(tmp_path):
    budget = {'max_wire_attempts': 2, 'max_elapsed_seconds': 60}
    create_checkpoint(tmp_path, budget=budget)
    wire = []
    def transport(*args, **kwargs): wire.append(1); return Response({'ok': True})
    first = JobCheckpoint(tmp_path, JOB); first.begin('fixture-binding', budget)
    wrapped(first, transport).call('getTokenSupply', ['a']); first.close()
    second = JobCheckpoint(tmp_path, JOB); second.begin('fixture-binding', budget)
    rpc = wrapped(second, transport)
    rpc.call('getTokenSupply', ['a'])
    rpc.call('getTokenSupply', ['b'])
    with pytest.raises(cluster.RPCJobBudgetExceeded): rpc.call('getTokenSupply', ['c'])
    assert len(wire) == 2 and rpc.calls == 2
    assert second.public_job()['resume_available'] is False
    second.close()


def test_original_deadline_and_config_survive_restart(tmp_path):
    now = [100.0]
    create_checkpoint(tmp_path, clock=lambda: now[0])
    first = JobCheckpoint(tmp_path, JOB, clock=lambda: now[0]); first.begin('fixture-binding'); first.close()
    now[0] = 161
    second = JobCheckpoint(tmp_path, JOB, clock=lambda: now[0])
    assert second.public_job()['resume_available'] is False
    with pytest.raises(CheckpointError, match='TIME_BUDGET'): second.begin('fixture-binding')
    second.close()


def test_source_config_and_budget_changes_reject_before_transport(tmp_path):
    create_checkpoint(tmp_path)
    checkpoint = JobCheckpoint(tmp_path, JOB)
    with pytest.raises(CheckpointError, match='SOURCE_OR_CONFIG_CHANGED'): checkpoint.begin('changed')
    with pytest.raises(CheckpointError, match='SOURCE_OR_CONFIG_CHANGED'):
        checkpoint.begin('fixture-binding', {'max_wire_attempts': 100, 'max_elapsed_seconds': 60})
    checkpoint.close()


def test_exclusive_lease_and_stale_reader_cannot_revoke_a_completed_job(tmp_path):
    create_checkpoint(tmp_path)
    early = JobCheckpoint(tmp_path, JOB)
    running = JobCheckpoint(tmp_path, JOB); running.begin('fixture-binding')
    with pytest.raises(CheckpointError, match='ALREADY_RUNNING'): early.begin('fixture-binding')
    running.finish('DONE'); running.close()
    with pytest.raises(CheckpointError, match='ALREADY_DONE'): early.begin('fixture-binding')
    early.close()


def test_corrupt_checkpoint_and_symlinks_never_restore_a_job(tmp_path):
    create_checkpoint(tmp_path)
    with sqlite3.connect(tmp_path/(JOB+'.sqlite')) as db:
        db.execute("UPDATE metadata SET body='{}'")
    with pytest.raises(CheckpointError, match='METADATA_INVALID'): JobCheckpoint(tmp_path, JOB)
    other = tmp_path/'other'; other.mkdir(mode=0o700)
    (other/(JOB+'.sqlite')).symlink_to(tmp_path/(JOB+'.sqlite'))
    with pytest.raises(CheckpointError, match='PATH_UNSAFE'): JobCheckpoint(other, JOB)


def test_checkpoint_failure_prevents_the_wire_attempt(tmp_path):
    create_checkpoint(tmp_path)
    checkpoint = JobCheckpoint(tmp_path, JOB); checkpoint.begin('fixture-binding')
    wire = []
    rpc = wrapped(checkpoint, lambda *args, **kwargs: wire.append(1))
    def fail(index): raise CheckpointError('CA_CHECKPOINT_STORAGE_UNAVAILABLE')
    checkpoint.before_wire = fail
    with pytest.raises(CheckpointError): rpc.call('getTokenSupply', [MINT])
    assert wire == [] and checkpoint.meta['wire_used'] == 0
    checkpoint.close()


def test_client_replay_uses_immutable_values_not_mutated_return_objects(tmp_path):
    create_checkpoint(tmp_path)
    first = JobCheckpoint(tmp_path, JOB); first.begin('fixture-binding')
    class Client:
        def token_snapshot(self, mint): return {'mint': mint, 'nested': {'amount': '1'}}
    result = CheckpointClient(first, Client(), 'market').token_snapshot(MINT)
    result['nested']['amount'] = '999'
    first.close()
    second = JobCheckpoint(tmp_path, JOB); second.begin('fixture-binding')
    class Denied:
        def token_snapshot(self, mint): pytest.fail('MUST_NOT_FETCH_AGAIN')
    assert CheckpointClient(second, Denied(), 'market').token_snapshot(MINT)['nested']['amount'] == '1'
    second.close()


def test_explicit_resume_keeps_identity_and_deduplicates_two_posts(tmp_path):
    first = ClusterJobManager(tmp_path); first.executor.shutdown(); first.executor = HoldingExecutor()
    submitted = first.submit(MINT)
    second = ClusterJobManager(tmp_path); second.executor.shutdown(); second.executor = HoldingExecutor()
    try:
        with pytest.raises(ValueError): second.resume(submitted['job_id'], '1'*32)
        a = second.resume(submitted['job_id'], MINT)
        b = second.resume(submitted['job_id'], MINT)
        assert a['job_id'] == b['job_id'] == submitted['job_id']
        assert len(second.executor.calls) == 1
    finally:
        first.executor.shutdown(); second.executor.shutdown()


def test_checkpoint_exceptions_never_reflect_arbitrary_secrets():
    assert str(CheckpointError('https://private.invalid/PRIVATE_TOKEN')) == 'CA_CHECKPOINT_UNAVAILABLE'


def test_terminal_source_error_is_preserved_and_only_explicit_resume_retries_it(tmp_path):
    create_checkpoint(tmp_path)
    first = JobCheckpoint(tmp_path, JOB); first.begin('fixture-binding')
    def fail(): raise cluster.RPCError('https://private.invalid/PRIVATE_TOKEN')
    with pytest.raises(cluster.RPCError): first.invoke('rpc', 'read', [], {}, fail)
    assert first.db.execute('SELECT COUNT(*) FROM source_errors').fetchone()[0] == 1
    assert 'PRIVATE_TOKEN' not in first.db.execute('SELECT body FROM source_errors').fetchone()[0]
    first.finish('ERROR'); first.close()
    second = JobCheckpoint(tmp_path, JOB)
    assert len(second.entries) == 1  # A read-only open never removes errors or retries.
    second.begin('fixture-binding')
    assert second.entries == []
    assert second.invoke('rpc', 'read', [], {}, lambda: 'recovered') == 'recovered'
    assert second.db.execute('SELECT COUNT(*) FROM source_errors').fetchone()[0] == 1
    second.close()


def test_manager_recovery_refuses_a_changed_registry_without_scheduling_work(tmp_path):
    first = ClusterJobManager(tmp_path); first.executor.shutdown(); first.executor = HoldingExecutor()
    submitted = first.submit(MINT)
    second = ClusterJobManager(tmp_path); second.executor.shutdown(); second.executor = HoldingExecutor()
    second.registry_path = tmp_path/'changed-registry.json'
    second.registry_path.write_text('{"schema_version":1,"addresses":{}}')
    try:
        paused = second.get(submitted['job_id'])
        assert paused['resume_available'] is False
        assert paused['resume_unavailable_reason'] == 'CA_CHECKPOINT_SOURCE_OR_CONFIG_CHANGED'
        with pytest.raises(ValueError): second.resume(submitted['job_id'], MINT)
        assert second.executor.calls == []
    finally:
        first.executor.shutdown(); second.executor.shutdown()


def test_real_worker_resumes_same_job_and_keeps_original_source_time(tmp_path, monkeypatch):
    from mission_agent.mission_control import server
    real_rpc = cluster.SolanaReadOnlyRPC
    wire = []
    def transport(request, timeout):
        req = json.loads(request.data); wire.append(req['method'])
        return Response({'value': req['method']})
    class FixtureRPC(real_rpc):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs, open_url=transport, min_interval=0)
    class FixtureAnalyzer:
        def __init__(self, mint, rpc, **kwargs): self.mint, self.rpc = mint, rpc
        def analyze(self):
            for method in ['getTokenSupply', 'getTokenLargestAccounts']:
                self.rpc.call(method, [self.mint], ttl=30)
            return {'schema_version': 2, 'source': 'SOLANA_FINALIZED_JSON_RPC', 'mint': self.mint,
                'observed_at': 1, 'coverage': {}, 'holders': [], 'metrics': {}, 'assessment': {},
                'token_profile': {}, 'limitations': []}
    monkeypatch.setattr(server, 'SolanaReadOnlyRPC', FixtureRPC)
    monkeypatch.setattr(server, 'WalletClusterAnalyzer', FixtureAnalyzer)
    manager = ClusterJobManager(tmp_path); manager.executor.shutdown(); manager.executor = HoldingExecutor()
    submitted = manager.submit(MINT)
    checkpoint = JobCheckpoint(manager.checkpoint_root, submitted['job_id'])
    checkpoint.begin(manager._checkpoint_binding('standard'), server.CLUSTER_RPC_JOB_BUDGETS['standard'])
    original_started_at = checkpoint.meta['started_at']
    CheckpointRPC(checkpoint, FixtureRPC(manager.rpc_endpoint, fallback_endpoints=manager.rpc_endpoints[1:],
        **checkpoint.transport_budget())).call('getTokenSupply', [MINT], ttl=30)
    checkpoint.close()  # Equivalent to process state loss after this durable source read.
    manager.jobs.clear()
    assert manager.get(submitted['job_id'])['status'] == 'PAUSED'
    manager.resume(submitted['job_id'], MINT)
    manager._run(submitted['job_id'])
    report = manager.latest(MINT, submitted['job_id'])
    assert manager.get(submitted['job_id'])['status'] == 'DONE'
    assert report['ca_job_id'] == submitted['job_id']
    assert report['observed_at'] == original_started_at
    assert report['collection_checkpoint']['mode'] == 'RESUMED_HISTORICAL_JOB'
    assert report['collection_checkpoint']['replayed_logical_reads'] == 1
    assert report['analysis_completeness']['status'] == 'INCOMPLETE_EVIDENCE'
    assert wire == ['getTokenSupply', 'getTokenLargestAccounts']
    assert 'completion does not refresh' in cluster.markdown(report)
    with pytest.raises(ValueError, match='ALREADY_DONE'): manager.resume(submitted['job_id'], MINT)
    manager.executor.shutdown()


def test_provider_cooldown_and_failed_attempt_survive_interruption(tmp_path):
    class Clock:
        now = 100.0
        waits = []
        def time(self): return self.now
        def monotonic(self): return 1000+self.now-100
        def sleep(self, seconds): self.waits.append(seconds); self.now += seconds
    class Interrupted(BaseException): pass
    clock = Clock()
    create_checkpoint(tmp_path, clock=clock.time)
    first = JobCheckpoint(tmp_path, JOB, clock=clock.time); first.begin('fixture-binding')
    class Limited(Response):
        def read(self): return json.dumps({'error': {'code': 429}}).encode()
    def interrupt_sleep(seconds): raise Interrupted()
    transport = cluster.SolanaReadOnlyRPC('https://fixture.invalid', fallback_endpoints=[],
        open_url=lambda *a, **k: Limited(None), sleep=interrupt_sleep, monotonic=clock.monotonic,
        min_interval=.45, **first.transport_budget())
    with pytest.raises(Interrupted): CheckpointRPC(first, transport).call('getTokenSupply', [MINT])
    assert first.meta['wire_used'] == 1
    assert first.meta['endpoint_cooldown_until']['0'] == 101.5
    first.close()
    second = JobCheckpoint(tmp_path, JOB, clock=clock.time); second.begin('fixture-binding')
    transport = cluster.SolanaReadOnlyRPC('https://fixture.invalid', fallback_endpoints=[],
        open_url=lambda *a, **k: Response('ok'), sleep=clock.sleep, monotonic=clock.monotonic,
        min_interval=.45, **second.transport_budget())
    rpc = CheckpointRPC(second, transport)
    assert rpc.call('getTokenSupply', [MINT]) == 'ok'
    assert clock.waits == [1.5]
    assert rpc.calls == 2 and rpc.endpoint_failures['https://fixture.invalid'] == 1
    second.close()


def test_readonly_checkpoint_cannot_start_work_or_create_a_lease(tmp_path):
    create_checkpoint(tmp_path)
    checkpoint = JobCheckpoint(tmp_path, JOB, readonly=True)
    with pytest.raises(CheckpointError, match='READ_ONLY'): checkpoint.begin('fixture-binding')
    assert not (tmp_path/(JOB+'.lock')).exists()
    checkpoint.close()


def test_new_acknowledged_job_with_missing_checkpoint_never_falls_back_to_a_fresh_scan(tmp_path, monkeypatch):
    from mission_agent.mission_control import server
    manager = ClusterJobManager(tmp_path); manager.executor.shutdown(); manager.executor = HoldingExecutor()
    submitted = manager.submit(MINT)
    assert submitted['checkpoint_version'] == 1
    (manager.checkpoint_root/(submitted['job_id']+'.sqlite')).unlink()
    def forbidden(*args, **kwargs): pytest.fail('NEW_JOB_MUST_NOT_FALL_BACK_TO_UNCHECKPOINTED_SCAN')
    monkeypatch.setattr(server, 'SolanaReadOnlyRPC', forbidden)
    manager._run(submitted['job_id'])
    assert manager.get(submitted['job_id'])['status'] == 'ERROR'
    assert not (manager.report_root/'_jobs'/(submitted['job_id']+'.done.json')).exists()
    manager.executor.shutdown()


@pytest.mark.parametrize('stop', ['changed_sequence', 'unconsumed_prefix'])
def test_sequence_integrity_stop_remains_unavailable_after_another_restart(tmp_path, stop):
    create_checkpoint(tmp_path)
    first = JobCheckpoint(tmp_path, JOB); first.begin('fixture-binding')
    first.invoke('fixture', 'read', ['original'], {}, lambda: 'saved')
    first.close()
    second = JobCheckpoint(tmp_path, JOB); second.begin('fixture-binding')
    with pytest.raises(CheckpointError):
        if stop == 'changed_sequence':
            second.invoke('fixture', 'read', ['changed'], {}, lambda: pytest.fail('NO_SOURCE_READ'))
        else:
            second.assert_can_publish()
    second.finish('ERROR'); second.close()
    third = JobCheckpoint(tmp_path, JOB, readonly=True)
    assert third.public_job()['resume_available'] is False
    third.close()
