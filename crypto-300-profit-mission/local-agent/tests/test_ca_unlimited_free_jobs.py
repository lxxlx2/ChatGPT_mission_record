"""Explicitly unmetered manual CA work, using synthetic transport only."""
import json
import sqlite3

import pytest

from mission_agent.meme.job_checkpoint import JobCheckpoint, CheckpointError, canonical, digest
from mission_agent.mission_control.server import CLUSTER_PRESETS, CLUSTER_RPC_JOB_BUDGETS, ClusterJobManager

JOB = 'c' * 32
UNLIMITED = {'max_wire_attempts': None, 'max_elapsed_seconds': None}


def create(root, budget=UNLIMITED, clock=lambda: 100.):
    JobCheckpoint.create(root, {'job_id': JOB, 'mint': 'fixture', 'preset': 'standard', 'created_at': 99.},
                         'binding', budget, clock=clock)


def rewrite_meta(root, update):
    with sqlite3.connect(root / (JOB + '.sqlite')) as db:
        meta = json.loads(db.execute('SELECT body FROM metadata WHERE id=1').fetchone()[0])
        meta.update(update)
        body = canonical(meta)
        db.execute('UPDATE metadata SET body=?,sha=? WHERE id=1', (body, digest(body)))


def test_unlimited_checkpoint_persists_counts_and_resumes_without_a_new_quota(tmp_path):
    now = [100.]
    create(tmp_path, clock=lambda: now[0])
    first = JobCheckpoint(tmp_path, JOB, clock=lambda: now[0])
    first.begin('binding', UNLIMITED)
    assert first.transport_budget() == UNLIMITED
    for _ in range(1201):
        first.before_wire(0)
    first.invoke('fixture', 'first', [], {}, lambda: {'observed': 1})
    first.finish('ERROR')
    first.close()
    now[0] = 10000.
    second = JobCheckpoint(tmp_path, JOB, clock=lambda: now[0])
    public = second.public_job()
    assert public['resume_available'] is True
    assert public['remaining_wire_attempts'] is None and public['resume_deadline_at'] is None
    second.begin('binding', UNLIMITED)
    assert second.invoke('fixture', 'first', [], {}, lambda: pytest.fail('MUST_REPLAY')) == {'observed': 1}
    second.before_wire(0)
    assert second.meta['wire_used'] == 1202
    assert second.meta['resume_count'] == 1 and second.meta['started_at'] == 100.
    assert second.transport_budget() == UNLIMITED
    second.assert_can_publish()
    second.finish('DONE')
    second.close()
    saved = JobCheckpoint(tmp_path, JOB, readonly=True, clock=lambda: now[0])
    assert saved.public_job()['resume_available'] is False
    saved.close()


@pytest.mark.parametrize('budget', [
    {'max_wire_attempts': None, 'max_elapsed_seconds': 60},
    {'max_wire_attempts': 2, 'max_elapsed_seconds': None},
])
def test_optional_limits_are_independent_and_finite_limits_remain_enforced(tmp_path, budget):
    now = [100.]
    create(tmp_path, budget, clock=lambda: now[0])
    checkpoint = JobCheckpoint(tmp_path, JOB, clock=lambda: now[0])
    checkpoint.begin('binding', budget)
    if budget['max_wire_attempts'] is None:
        checkpoint.before_wire(0)
        now[0] = 160.
        with pytest.raises(CheckpointError, match='TIME_BUDGET_EXHAUSTED'):
            checkpoint.before_wire(0)
    else:
        now[0] = 10000.
        checkpoint.before_wire(0)
        checkpoint.before_wire(0)
        with pytest.raises(CheckpointError, match='WIRE_BUDGET_EXHAUSTED'):
            checkpoint.before_wire(0)
    checkpoint.close()


@pytest.mark.parametrize('update', [
    {'wire_limit': True}, {'wire_limit': 0}, {'wire_limit': -1}, {'wire_limit': 1.5},
    {'seconds_limit': False}, {'seconds_limit': 0}, {'seconds_limit': -1}, {'seconds_limit': 'unlimited'},
    {'started_at': 100., 'deadline_at': 200.},
    {'started_at': True}, {'wire_used': True}, {'wire_used': -1},
])
def test_unlimited_metadata_still_rejects_invalid_values(tmp_path, update):
    create(tmp_path)
    rewrite_meta(tmp_path, update)
    with pytest.raises(CheckpointError):
        JobCheckpoint(tmp_path, JOB)


def test_unlimited_jobs_keep_clock_regression_source_binding_and_disk_checks(tmp_path, monkeypatch):
    now = [100.]
    create(tmp_path, clock=lambda: now[0])
    checkpoint = JobCheckpoint(tmp_path, JOB, clock=lambda: now[0])
    with pytest.raises(CheckpointError, match='SOURCE_OR_CONFIG_CHANGED'):
        checkpoint.begin('other', UNLIMITED)
    checkpoint.begin('binding', UNLIMITED)
    now[0] = 99.
    with pytest.raises(CheckpointError, match='CLOCK_REGRESSION'):
        checkpoint.before_wire(0)
    now[0] = 101.
    from mission_agent.meme import job_checkpoint
    from types import SimpleNamespace
    monkeypatch.setattr(job_checkpoint.shutil, 'disk_usage', lambda path:SimpleNamespace(free=0))
    with pytest.raises(CheckpointError, match='STORAGE_UNAVAILABLE'):
        checkpoint.invoke('fixture', 'large', [], {}, lambda: {'value': 'too large'})
    checkpoint.close()


def test_standard_manual_query_uses_source_completion_and_no_total_request_or_time_quota():
    assert CLUSTER_RPC_JOB_BUDGETS['standard'] == UNLIMITED
    assert CLUSTER_PRESETS['standard']['exhaust_history'] is True
    assert CLUSTER_PRESETS['standard']['deep_holders'] == 20
    assert CLUSTER_RPC_JOB_BUDGETS['quick'] == {'max_wire_attempts': 300, 'max_elapsed_seconds': 600}
    assert CLUSTER_RPC_JOB_BUDGETS['deep'] == {'max_wire_attempts': 2500, 'max_elapsed_seconds': 3600}


def test_secondary_provider_has_no_artificial_aggregate_quota(monkeypatch):
    from mission_agent.mission_control import server
    captured = []
    class RPC:
        def __init__(self, endpoint, **kwargs): captured.append(kwargs)
    monkeypatch.setattr(server, 'SolanaReadOnlyRPC', RPC)
    monkeypatch.setenv('SOLANA_RPC_SECONDARY', 'https://secondary.invalid')
    manager = object.__new__(ClusterJobManager)
    manager.rpc_endpoints = ['https://primary.invalid']
    manager._independent_rpc()()
    assert captured == [{'fallback_endpoints': []}]


def test_unlimited_evidence_log_has_no_legacy_entry_or_byte_quota_and_replays_lazily(tmp_path, monkeypatch):
    from mission_agent.meme import job_checkpoint
    monkeypatch.setattr(job_checkpoint,'MAX_BYTES',1)
    monkeypatch.setattr(job_checkpoint,'MAX_ENTRIES',1)
    create(tmp_path)
    cp=JobCheckpoint(tmp_path,JOB,clock=lambda:100.)
    cp.begin('binding',UNLIMITED)
    for i in range(3):
        assert cp.invoke('fixture','read',[i],{},lambda i=i:{'row':i})=={'row':i}
    assert not isinstance(cp.entries,list) and len(cp.entries)==3
    assert cp.provenance()['evidence_entry_limit'] is None
    cp.finish('ERROR');cp.close()
    cp=JobCheckpoint(tmp_path,JOB,clock=lambda:100.)
    cp.begin('binding',UNLIMITED)
    for i in range(3):
        assert cp.invoke('fixture','read',[i],{},lambda:pytest.fail('NO_NEW_READ'))=={'row':i}
    cp.assert_can_publish();cp.close()
