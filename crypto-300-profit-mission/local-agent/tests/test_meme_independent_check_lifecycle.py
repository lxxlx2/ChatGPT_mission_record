"""Independent RPC budgets start at their first use; no live transport."""
import json

import pytest

from mission_agent.meme.cluster import RPCError, RPCJobBudgetExceeded, SolanaReadOnlyRPC
from mission_agent.meme.independent_check import collect_independent_balance_check
from mission_agent.meme.job_checkpoint import CheckpointError
from mission_agent.mission_control import server


MINT = 'So11111111111111111111111111111111111111112'


class Clock:
    def __init__(self): self.now = 0
    def __call__(self): return self.now
    def advance(self, seconds): self.now += seconds


class Response:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps({'result': self.payload}).encode()


def payload():
    return {'context': {'slot': 7}, 'value': [
        {'data': {'parsed': {'info': {'supply': '100'}}}}
    ]}


class Parsed:
    def __init__(self, error=None): self.error, self.calls = error, 0
    def call(self, *args):
        self.calls += 1
        if self.error is not None: raise self.error
        return payload()


def manager():
    value = server.ClusterJobManager.__new__(server.ClusterJobManager)
    value.rpc_endpoints = ['https://primary.example']
    return value


def install_fake_secondary(monkeypatch, clock, created, reads):
    def transport(request, timeout):
        reads.append('secondary')
        return Response(payload())

    class Secondary(SolanaReadOnlyRPC):
        def __init__(self, url, **kwargs):
            super().__init__(url, **kwargs, monotonic=clock, min_interval=0,
                             open_url=transport, sleep=clock.advance)
            created.append(self)

    monkeypatch.setattr(server, 'SolanaReadOnlyRPC', Secondary)
    monkeypatch.setenv('SOLANA_RPC_SECONDARY', 'https://secondary.example')


def test_manager_defers_secondary_construction_until_collector_use(monkeypatch):
    clock, created, reads = Clock(), [], []
    install_fake_secondary(monkeypatch, clock, created, reads)
    deferred = manager()._independent_rpc()
    assert created == [] and reads == []
    assert callable(deferred)


def test_slow_primary_work_does_not_preexpire_secondary_first_wire(monkeypatch):
    clock, created, reads = Clock(), [], []
    install_fake_secondary(monkeypatch, clock, created, reads)
    deferred = manager()._independent_rpc()
    clock.advance(120)  # Prior main analysis exceeds the secondary's 60 seconds.

    def transport(request, timeout):
        reads.append('primary')
        clock.advance(5)
        return Response(payload())

    primary = SolanaReadOnlyRPC('https://primary.example', fallback_endpoints=[],
        max_wire_attempts=1200, max_elapsed_seconds=1800, monotonic=clock,
        min_interval=0, open_url=transport, sleep=clock.advance)
    primary_started = primary._budget_started_at
    result = collect_independent_balance_check(MINT, [], primary, deferred, clock=clock)
    assert result['status'] == 'SAME_SLOT_ALL_MATCH'
    assert result['secondary_wire_attempts'] == 1
    assert reads == ['primary', 'secondary']
    assert len(created) == 1 and created[0]._budget_started_at == 125
    assert created[0].max_wire_attempts is None and created[0].max_elapsed_seconds is None
    assert created[0].calls == 1 and primary.calls == 1
    assert primary._budget_started_at == primary_started


@pytest.mark.parametrize('disabled', ['', '0', 'https://primary.example'])
def test_disabled_secondary_does_not_create_a_factory_or_read_primary(monkeypatch, disabled):
    monkeypatch.setenv('SOLANA_RPC_SECONDARY', disabled)
    secondary = manager()._independent_rpc()
    primary = Parsed()
    result = collect_independent_balance_check(MINT, [], primary, secondary)
    assert secondary is None and result['status'] == 'NOT_REQUESTED' and primary.calls == 0


@pytest.mark.parametrize('error', [RPCJobBudgetExceeded('RPC_JOB_TIME_BUDGET_EXHAUSTED'),
    RPCJobBudgetExceeded('RPC_JOB_WIRE_BUDGET_EXHAUSTED'),
    CheckpointError('CA_CHECKPOINT_READ_SEQUENCE_CHANGED')])
def test_primary_hard_budget_or_checkpoint_error_is_never_downgraded(error):
    attempts = []
    def secondary(): attempts.append(1); return Parsed()
    with pytest.raises(type(error), match=str(error)):
        collect_independent_balance_check(MINT, [], Parsed(error), secondary)
    assert attempts == []


def test_secondary_checkpoint_failure_is_hard_even_when_optional():
    with pytest.raises(CheckpointError, match='CA_CHECKPOINT_STORAGE_UNAVAILABLE'):
        collect_independent_balance_check(MINT, [], Parsed(),
            Parsed(CheckpointError('CA_CHECKPOINT_STORAGE_UNAVAILABLE')))


def test_preconstructed_secondary_keeps_its_original_deadline_and_budget():
    clock = Clock()
    secondary = SolanaReadOnlyRPC('https://secondary.example', fallback_endpoints=[],
        max_wire_attempts=4, max_elapsed_seconds=60, monotonic=clock, min_interval=0,
        open_url=lambda *args, **kwargs: pytest.fail('EXPIRED_SECONDARY_MUST_NOT_START_WIRE'))
    clock.advance(61)
    result = collect_independent_balance_check(MINT, [], Parsed(), secondary, clock=clock)
    assert result['status'] == 'UNAVAILABLE' and result['reason'] == 'RPC_JOB_TIME_BUDGET_EXHAUSTED'
    assert result['secondary_wire_attempts'] == 0
    assert secondary._budget_started_at == 0 and secondary.calls == 0
    assert secondary.max_wire_attempts == 4 and secondary.max_elapsed_seconds == 60


@pytest.mark.parametrize('limit,expected_wire', [('WIRE', 4), ('TIME', 1)])
def test_secondary_exhaustion_respects_original_four_wire_sixty_second_limits(limit, expected_wire):
    clock = Clock()
    def transport(request, timeout):
        if limit == 'TIME':
            clock.advance(61)
            return Response(payload())
        raise TimeoutError('PRIVATE_TRANSPORT_DETAIL')
    secondary = SolanaReadOnlyRPC('https://secondary.example', fallback_endpoints=[],
        max_wire_attempts=4, max_elapsed_seconds=60, monotonic=clock, min_interval=0,
        open_url=transport, sleep=clock.advance)
    result = collect_independent_balance_check(MINT, [], Parsed(), secondary, clock=clock)
    assert result['status'] == 'UNAVAILABLE'
    assert result['reason'] == 'RPC_JOB_' + limit + '_BUDGET_EXHAUSTED'
    assert result['secondary_wire_attempts'] == expected_wire == secondary.calls
    assert secondary._budget_started_at == 0 and secondary.max_elapsed_seconds == 60
    assert secondary.max_wire_attempts == 4


@pytest.mark.parametrize('phase', ['primary', 'secondary', 'factory'])
def test_unavailable_reason_cannot_echo_private_rpc_url_or_token(phase):
    secret = 'https://rpc.private.invalid/PRIVATE_TOKEN?api_key=SECRET'
    error = RPCError(secret)
    primary = Parsed(error if phase == 'primary' else None)
    if phase == 'factory':
        def secondary(): raise error
    else:
        secondary = Parsed(error if phase == 'secondary' else None)
    result = collect_independent_balance_check(MINT, [], primary, secondary)
    assert result['status'] == 'UNAVAILABLE'
    assert result['reason'] == 'RPCError'
    assert 'PRIVATE_TOKEN' not in json.dumps(result) and 'api_key' not in json.dumps(result)


def test_optional_secondary_cannot_reset_primary_deadline_or_make_it_publishable():
    clock = Clock()
    def transport(request, timeout): return Response(payload())
    primary = SolanaReadOnlyRPC('https://primary.example', fallback_endpoints=[],
        max_wire_attempts=1200, max_elapsed_seconds=1800, monotonic=clock,
        min_interval=0, open_url=transport, sleep=clock.advance)
    clock.advance(1790)
    def secondary():
        clock.advance(11)
        return Parsed()
    collect_independent_balance_check(MINT, [], primary, secondary, clock=clock)
    assert primary._budget_started_at == 0 and primary.max_elapsed_seconds == 1800
    with pytest.raises(RPCJobBudgetExceeded, match='RPC_JOB_TIME_BUDGET_EXHAUSTED'):
        primary.assert_can_publish()
