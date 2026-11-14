"""Keep a safe last source error distinct from an independent budget stop."""
import json
import urllib.error

import pytest

from mission_agent.meme.cluster import RPCError, SolanaReadOnlyRPC
from mission_agent.meme.independent_check import collect_independent_balance_check

MINT = 'So11111111111111111111111111111111111111112'
SECRET = 'https://fixture.invalid/PRIVATE_TOKEN?api_key=PRIVATE_QUERY'


class Clock:
    def __init__(self): self.now = 0
    def __call__(self): return self.now
    def sleep(self, seconds): self.now += seconds


def payload():
    return {'context': {'slot': 7}, 'value': [
        {'data': {'parsed': {'info': {'supply': '100'}}}}
    ]}


class Primary:
    def call(self, *args): return payload()


class Response:
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps({'result': payload()}).encode()


def secondary(transport, clock):
    return SolanaReadOnlyRPC(SECRET, fallback_endpoints=[], open_url=transport,
        sleep=clock.sleep, monotonic=clock, min_interval=0,
        max_wire_attempts=4, max_elapsed_seconds=60)


@pytest.mark.parametrize('code', [403, 429])
def test_budget_stop_preserves_last_http_status_without_private_details(code):
    clock = Clock()
    def transport(request, timeout):
        raise urllib.error.HTTPError(SECRET, code, 'PRIVATE_REASON', {}, None)
    rpc = secondary(transport, clock)
    result = collect_independent_balance_check(MINT, [], Primary(), rpc, clock=clock)
    assert result['status'] == 'UNAVAILABLE'
    assert result['reason'] == 'RPC_JOB_WIRE_BUDGET_EXHAUSTED'
    assert result.get('last_source_error') == 'HTTP_' + str(code)
    assert result['secondary_wire_attempts'] == rpc.calls == 4
    assert rpc.max_wire_attempts == 4 and rpc.max_elapsed_seconds == 60
    assert not any(s in json.dumps(result) for s in ['PRIVATE_TOKEN', 'PRIVATE_QUERY', 'PRIVATE_REASON'])


def test_budget_stop_retains_timeout_class_not_timeout_message():
    clock = Clock()
    def transport(request, timeout): raise TimeoutError(SECRET)
    rpc = secondary(transport, clock)
    result = collect_independent_balance_check(MINT, [], Primary(), rpc, clock=clock)
    assert result['reason'] == 'RPC_JOB_WIRE_BUDGET_EXHAUSTED'
    assert result.get('last_source_error') == 'TimeoutError'
    assert rpc.calls == 4 and SECRET not in json.dumps(result)


def test_success_after_retry_clears_last_source_failure():
    clock, attempts = Clock(), []
    def transport(request, timeout):
        attempts.append(1)
        if len(attempts) == 1:
            raise urllib.error.HTTPError(SECRET, 429, 'PRIVATE_REASON', {}, None)
        return Response()
    rpc = secondary(transport, clock)
    result = collect_independent_balance_check(MINT, [], Primary(), rpc, clock=clock)
    assert result['status'] == 'SAME_SLOT_ALL_MATCH'
    assert result['secondary_wire_attempts'] == 2
    assert result.get('last_source_error') is None
    assert rpc.last_wire_error_code is None


@pytest.mark.parametrize('field', [SECRET, 'HTTP_429\n' + SECRET, 'RPC_' + '1' * 100, {'raw': SECRET}, None])
def test_custom_rpc_cannot_publish_untrusted_error_field(field):
    class Custom:
        calls = 1
        last_wire_error_code = field
        def call(self, *args): raise RPCError(SECRET)
    result = collect_independent_balance_check(MINT, [], Primary(), Custom())
    assert result['reason'] == 'RPCError'
    assert result.get('last_source_error') is None
    assert 'PRIVATE_TOKEN' not in json.dumps(result)


def test_legacy_rpc_without_error_field_remains_unknown():
    class Legacy:
        calls = 4
        def call(self, *args): raise RPCError('RPC_JOB_WIRE_BUDGET_EXHAUSTED')
    result = collect_independent_balance_check(MINT, [], Primary(), Legacy())
    assert result['reason'] == 'RPC_JOB_WIRE_BUDGET_EXHAUSTED'
    assert result.get('last_source_error') is None
    assert result['secondary_wire_attempts'] == 4
