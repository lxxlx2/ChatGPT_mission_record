"""Origin evidence follows the production checkpoint path; all I/O is injected."""
import hashlib
import json
import sqlite3

import pytest

from mission_agent.meme.cluster import RPCJobBudgetExceeded, WalletClusterAnalyzer
from mission_agent.meme.job_checkpoint import CheckpointClient, CheckpointError, JobCheckpoint
from mission_agent.meme.narrative import PublicNarrativeClient, collect_origin


MINT = 'So11111111111111111111111111111111111111112'
JOB = 'b' * 32
METADATA = {'status': 'VERIFIED_CHAIN_STATE', 'uri': 'https://metadata.example/token.json',
            'name': 'Fixture', 'symbol': 'FIX', 'is_mutable': False}
MARKET = {'status': 'OK', 'source': 'DEXSCREENER_API', 'mint': MINT}


def checkpoint(path):
    JobCheckpoint.create(path, {'job_id': JOB, 'mint': MINT, 'preset': 'standard', 'created_at': 1},
                         'fixture', {'max_wire_attempts': 8, 'max_elapsed_seconds': 60}, clock=lambda: 10)
    value = JobCheckpoint(path, JOB, clock=lambda: 10)
    value.begin('fixture')
    return value


def analyzer(client, metadata=METADATA):
    value = WalletClusterAnalyzer(MINT, rpc=None, narrative_client=client)
    value._launch_metadata = metadata
    return value


def client(reads):
    def fetch_html(url):
        reads.append(('html', url))
        return {'status': 'UNAVAILABLE', 'reason': 'HTTP_403'}

    def fetch_json(url):
        reads.append(('json', url))
        if url == METADATA['uri']:
            return {'status': 'OK', 'json': {'name': 'Fixture', 'symbol': 'FIX',
                    'description': 'A fictional crawler project.',
                    'twitter': 'https://x.com/fixture/status/12345'}}
        assert url == 'https://api.fxtwitter.com/fixture/status/12345'
        return {'status': 'OK', 'json': {'tweet': {'url': 'https://x.com/fixture/status/12345',
                'id': '12345', 'author': {'screen_name': 'fixture'}, 'created_timestamp': 5,
                'text': 'A fictional crawler project.'}}}

    return PublicNarrativeClient(fetch=fetch_html, fetch_json=fetch_json, clock=lambda: 10)


def test_real_analyzer_origin_is_recorded_then_replayed_without_source_reads(tmp_path):
    first = checkpoint(tmp_path)
    reads = []
    result = analyzer(CheckpointClient(first, client(reads), 'narrative')).narrative_snapshot(MARKET)
    assert result['origin']['status'] == 'PARTIAL'
    assert result['origin']['ca_link_status'] == 'CREATOR_METADATA_LINKS_POST'
    assert [row['request']['operation'] for row in first.entries] == ['collect', 'collect_origin']
    assert len(reads) == 3  # One HTML hint, metadata JSON and one linked post.
    first.assert_can_publish()
    first.close()
    database = tmp_path / (JOB + '.sqlite')
    original_sha = hashlib.sha256(database.read_bytes()).hexdigest()

    class Denied:
        def collect(self, *args): pytest.fail('REPLAY_MUST_NOT_READ_HTML')
        def collect_origin(self, *args): pytest.fail('REPLAY_MUST_NOT_READ_ORIGIN')

    second = JobCheckpoint(tmp_path, JOB, readonly=True, clock=lambda: 10)
    replayed = analyzer(CheckpointClient(second, Denied(), 'narrative')).narrative_snapshot(MARKET)
    assert replayed == result
    second.assert_can_publish()
    assert second.replayed == 2
    second.close()
    assert hashlib.sha256(database.read_bytes()).hexdigest() == original_sha


def test_legacy_narrative_client_does_not_gain_an_unsupported_origin_operation(tmp_path):
    value = checkpoint(tmp_path)

    class Legacy:
        def collect(self, mint, market): return {'status': 'UNAVAILABLE', 'evidence': []}

    wrapped = CheckpointClient(value, Legacy(), 'narrative')
    assert not hasattr(wrapped, 'collect_origin')
    assert 'origin' not in analyzer(wrapped).narrative_snapshot(MARKET)
    assert len(value.entries) == 1 and value.entries[0]['request']['operation'] == 'collect'
    value.close()


def test_origin_timeout_is_sanitized_and_explicit_resume_retries_only_terminal_read(tmp_path):
    value = checkpoint(tmp_path)

    class Failing:
        def collect(self, *args): return {'status': 'UNAVAILABLE'}
        def collect_origin(self, *args): raise TimeoutError('https://private.invalid/PRIVATE_TOKEN')

    wrapped = CheckpointClient(value, Failing(), 'narrative')
    wrapped.collect(MINT, MARKET)
    with pytest.raises(TimeoutError): wrapped.collect_origin(MINT, METADATA, MARKET)
    deadline = value.meta['deadline_at']
    error_body = value.db.execute('SELECT body FROM source_errors').fetchone()[0]
    assert 'PRIVATE_TOKEN' not in error_body
    assert json.loads(error_body)['response'] == {'type': 'TimeoutError', 'code': 'RECORDED_SOURCE_ERROR'}
    value.finish('ERROR')
    value.close()

    replay = JobCheckpoint(tmp_path, JOB, readonly=True, clock=lambda: 10)
    wrapped = CheckpointClient(replay, Failing(), 'narrative')
    wrapped.collect(MINT, MARKET)
    with pytest.raises(TimeoutError, match='RECORDED_SOURCE_ERROR'):
        wrapped.collect_origin(MINT, METADATA, MARKET)
    assert replay.fault is None and replay.replayed == 2
    replay.close()

    class Recovered:
        def collect(self, *args): pytest.fail('COMPLETED_HTML_READ_MUST_REPLAY')
        def collect_origin(self, *args): return {'status': 'UNAVAILABLE', 'reads': []}

    resumed = JobCheckpoint(tmp_path, JOB, clock=lambda: 10)
    assert len(resumed.entries) == 2
    resumed.begin('fixture')
    assert len(resumed.entries) == 1
    wrapped = CheckpointClient(resumed, Recovered(), 'narrative')
    assert wrapped.collect(MINT, MARKET)['status'] == 'UNAVAILABLE'
    assert wrapped.collect_origin(MINT, METADATA, MARKET)['reads'] == []
    assert resumed.meta['deadline_at'] == deadline and resumed.meta['wire_used'] == 0
    assert resumed.db.execute('SELECT COUNT(*) FROM source_errors').fetchone()[0] == 1
    resumed.assert_can_publish()
    resumed.close()


@pytest.mark.parametrize('error', [OSError('PRIVATE_STORAGE_DETAIL'),
    sqlite3.OperationalError('PRIVATE_STORAGE_DETAIL')])
def test_origin_checkpoint_storage_failure_still_fails_closed(tmp_path, monkeypatch, error):
    value = checkpoint(tmp_path)
    def unavailable(*args): raise error
    monkeypatch.setattr(value, '_append', unavailable)
    wrapped = CheckpointClient(value, client([]), 'narrative')
    with pytest.raises(CheckpointError, match='CA_CHECKPOINT_STORAGE_UNAVAILABLE') as caught:
        wrapped.collect_origin(MINT, METADATA, MARKET)
    assert 'PRIVATE_STORAGE_DETAIL' not in str(caught.value)
    assert value.fault == 'CA_CHECKPOINT_STORAGE_UNAVAILABLE' and value.entries == []
    value.close()


def test_changed_origin_metadata_cannot_be_swallowed_as_source_unavailability(tmp_path):
    value = checkpoint(tmp_path)
    analyzer(CheckpointClient(value, client([]), 'narrative')).narrative_snapshot(MARKET)
    value.close()
    replay = JobCheckpoint(tmp_path, JOB, readonly=True, clock=lambda: 10)
    changed = {**METADATA, 'uri': 'https://metadata.example/changed.json'}
    with pytest.raises(CheckpointError, match='CA_CHECKPOINT_READ_SEQUENCE_CHANGED'):
        analyzer(CheckpointClient(replay, client([]), 'narrative'), changed).narrative_snapshot(MARKET)
    replay.close()


@pytest.mark.parametrize('error', [RPCJobBudgetExceeded('RPC_JOB_TIME_BUDGET_EXHAUSTED'),
    CheckpointError('CA_CHECKPOINT_SIZE_LIMIT')])
def test_origin_budget_and_checkpoint_errors_propagate_through_analyzer(tmp_path, error):
    value = checkpoint(tmp_path)

    class Limited:
        def collect(self, *args): return {'status': 'UNAVAILABLE'}
        def collect_origin(self, *args): raise error

    with pytest.raises(type(error), match=str(error)):
        analyzer(CheckpointClient(value, Limited(), 'narrative')).narrative_snapshot(MARKET)
    assert [row['request']['operation'] for row in value.entries] == ['collect']
    value.close()


@pytest.mark.parametrize('error', [RPCJobBudgetExceeded('RPC_JOB_TIME_BUDGET_EXHAUSTED'),
    CheckpointError('CA_CHECKPOINT_SIZE_LIMIT')])
def test_origin_json_fetch_cannot_suppress_budget_or_checkpoint_errors(error):
    def fetch(url): raise error
    with pytest.raises(type(error), match=str(error)):
        collect_origin(MINT, METADATA, MARKET, fetch_json=fetch, clock=lambda: 10)


def test_origin_source_exception_does_not_publish_secret_exception_text():
    def fetch(url): raise TimeoutError('https://private.invalid/PRIVATE_TOKEN')
    result = collect_origin(MINT, METADATA, MARKET, fetch_json=fetch, clock=lambda: 10)
    assert result['status'] == 'UNAVAILABLE'
    assert result['reads'][0]['reason'] == 'TimeoutError'
    assert 'PRIVATE_TOKEN' not in json.dumps(result)
