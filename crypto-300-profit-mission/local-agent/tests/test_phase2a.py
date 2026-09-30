import base64
import hashlib
import urllib.parse
import pytest
from mission_agent.transport.github import GitHubTransport, RemoteError, Conflict, REPOSITORY


class MemoryAPI:
    def __init__(self):
        self.files = {}
        self.calls = []
        self.faults = []
        self.private = True
        self.puts = 0

    def request(self, method, endpoint, body=None):
        self.calls.append((method, endpoint))
        if self.faults and self.faults[0][0] == method:
            _, error, after = self.faults.pop(0)
            if after: self._put(endpoint, body)
            raise error
        if endpoint == '/repos/' + REPOSITORY:
            return {'private': self.private, 'full_name': REPOSITORY}
        if '/git/ref/' in endpoint: return {'object': {'sha': 'head'}}
        if method == 'PUT': return self._put(endpoint, body)
        path = urllib.parse.unquote(endpoint.split('/contents/')[1].split('?')[0])
        if path not in self.files: raise RemoteError(404)
        data = self.files[path]
        return {'path': path, 'size': len(data), 'encoding': 'base64',
                'content': base64.b64encode(data).decode(), 'sha': self.sha(data)}

    @staticmethod
    def sha(data):
        return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

    def _put(self, endpoint, body):
        path = urllib.parse.unquote(endpoint.split('/contents/')[1])
        old = self.files.get(path)
        if (self.sha(old) if old else None) != body.get('sha'): raise RemoteError(409)
        self.files[path] = base64.b64decode(body['content'])
        self.puts += 1
        return {'commit': {'sha': 'commit'}}


@pytest.fixture
def transport():
    api = MemoryAPI()
    return GitHubTransport('mac', 'unit', api=api, sleep=lambda _: None), api


def test_create_cas_replay_and_conflict(transport):
    t, api = transport
    path = t._path('health')
    first = t.write('mac-data', path, {'sequence': 1})
    assert api.puts == 1
    replay = t.write('mac-data', path, {'sequence': 1})
    assert replay.data == first.data and replay.blob_sha == first.blob_sha
    assert api.puts == 1
    second = t.write('mac-data', path, {'sequence': 2}, first.blob_sha)
    assert second.value == {'sequence': 2}
    with pytest.raises(Conflict): t.write('mac-data', path, {'sequence': 3}, first.blob_sha)
    assert api.puts == 2


@pytest.mark.parametrize('after', [False, True])
@pytest.mark.parametrize('status', [0, 429, 503])
def test_ambiguous_put_read_before_retry(transport, status, after):
    t, api = transport
    api.faults = [('PUT', RemoteError(status, {'Retry-After': '0'}), after)]
    assert t.write('mac-data', t._path('health'), {'sequence': 1}).value == {'sequence': 1}
    assert api.puts == 1


@pytest.mark.parametrize('status', [409, 422])
def test_conflict_no_blind_retry(transport, status):
    t, api = transport
    api.faults = [('PUT', RemoteError(status), False)]
    with pytest.raises(RemoteError): t.write('mac-data', t._path('health'), {'sequence': 1})
    assert sum(method == 'PUT' for method, _ in api.calls) == 1


def test_archive_immutable(transport):
    t, api = transport
    path = t._path('ingest', 'same')
    first = t.write('mac-data', path, {'test': 1}, immutable=True)
    t.write('mac-data', path, {'test': 1}, immutable=True)
    with pytest.raises(Conflict, match='HASH_CONFLICT'):
        t.write('mac-data', path, {'test': 2}, first.blob_sha, True)
    assert api.puts == 1


@pytest.mark.parametrize('role,branch', [('mac', 'gpt-data'), ('gpt', 'mac-data')])
def test_role_guard_precedes_network(role, branch):
    api = MemoryAPI(); t = GitHubTransport(role, 'unit', api=api)
    with pytest.raises(ValueError): t.write(branch, t._path('health'), {})
    assert not api.calls


def test_wrong_repo_private_and_paths(transport):
    t, api = transport
    with pytest.raises(ValueError): GitHubTransport('mac', 'unit', api=api, repository='lxxlx2/ChatGPT_mission_record')
    for path in ['runtime-v2/health/current.json', t.namespace + '/../current.json']:
        with pytest.raises(ValueError): t.write('mac-data', path, {})
    api.private = False
    with pytest.raises(ValueError, match='PRIVATE'): t.read('mac-data', t._path('health'))
    assert api.puts == 0


def test_404_no_retry(transport):
    t, api = transport
    with pytest.raises(RemoteError) as error: t.read('mac-data', t._path('health'))
    assert error.value.status == 404


def test_real_send_guard(transport):
    t, api = transport
    gpt = GitHubTransport('gpt', 'unit', api=api)
    with pytest.raises(ValueError): gpt.publish_delivery({'mode': 'SENT'}, 'x')
    assert api.puts == 0


def test_archive_guard_cannot_be_disabled(transport):
    t, api = transport; path = t._path('ingest', 'immutable')
    first = t.write('mac-data', path, {'v': 1})
    with pytest.raises(Conflict, match='HASH_CONFLICT'): t.write('mac-data', path, {'v': 2}, first.blob_sha)
    assert api.puts == 1


@pytest.mark.parametrize('mutation', ['size', 'sha', 'content'])
def test_readback_corruption_rejected(transport, mutation):
    t, api = transport
    t.write('mac-data', t._path('health'), {'v': 1})
    original = api.request
    def corrupt(method, endpoint, body=None):
        result = original(method, endpoint, body)
        if method == 'GET' and '/contents/' in endpoint:
            result[mutation] = {'size': 9999, 'sha': '0' * 40, 'content': base64.b64encode(b'{}').decode()}[mutation]
        return result
    api.request = corrupt
    with pytest.raises(ValueError): t.read('mac-data', t._path('health'))


def test_racing_put_conflict_is_not_overwritten(transport):
    t, api = transport; path = t._path('health')
    first = t.write('mac-data', path, {'v': 1})
    original = api.request
    def racing(method, endpoint, body=None):
        if method == 'PUT':
            api.files[path] = b'{"v":99}'
            raise RemoteError(409)
        return original(method, endpoint, body)
    api.request = racing
    with pytest.raises(Conflict): t.write('mac-data', path, {'v': 2}, first.blob_sha)
    assert api.files[path] == b'{"v":99}'
    assert api.puts == 1


def test_timeout_exhaustion_preserves_state(transport):
    t, api = transport; path = t._path('health')
    api.faults = [('PUT', RemoteError(0), False)] * 3
    with pytest.raises(RemoteError): t.write('mac-data', path, {'v': 1})
    assert path not in api.files
    assert sum(m == 'PUT' for m, _ in api.calls) == 3


def test_long_rate_limit_defers_without_retry(transport):
    t, api = transport
    api.faults = [('PUT', RemoteError(429, {'Retry-After': '120'}), False)]
    with pytest.raises(RemoteError): t.write('mac-data', t._path('health'), {'v': 1})
    assert api.puts == 0


def test_remote_confirmed_proof_and_recovery(repo, config, transport):
    from mission_agent.models import Event
    from mission_agent.clock import stamp
    from mission_agent.queue.batch import build_batch
    from mission_agent.queue.remote import publish_remote
    t, api = transport
    repo.ingest(Event.synthetic('TEST_ACTION_CANDIDATE', 'SYNTH', stamp(repo.clock.now()), 0, {}))
    batch = build_batch(repo, config)
    proof = publish_remote(repo, t, batch['batch_id'])
    assert proof.value == batch
    assert repo.db.execute('SELECT state FROM batches').fetchone()[0] == 'REMOTE_CONFIRMED'
    assert repo.db.execute('SELECT state FROM outbox').fetchone()[0] == 'REMOTE_CONFIRMED'
    assert repo.db.execute("SELECT COUNT(*) FROM meta WHERE key LIKE 'remote-proof:%'").fetchone()[0] == 1
    before = api.puts
    publish_remote(repo, t, batch['batch_id'])
    assert api.puts == before


def test_failed_readback_does_not_confirm(repo, config, transport):
    from mission_agent.models import Event
    from mission_agent.clock import stamp
    from mission_agent.queue.batch import build_batch
    from mission_agent.queue.remote import publish_remote
    t, api = transport
    repo.ingest(Event.synthetic('TEST_ACTION_CANDIDATE', 'SYNTH', stamp(repo.clock.now()), 0, {}))
    batch = build_batch(repo, config)
    original = api.request
    def broken(method, endpoint, body=None):
        result = original(method, endpoint, body)
        if method == 'GET' and '/contents/' in endpoint and 'content' in result:
            result['size'] += 1
        return result
    api.request = broken
    with pytest.raises(ValueError): publish_remote(repo, t, batch['batch_id'])
    assert repo.db.execute('SELECT state FROM batches').fetchone()[0] == 'BUILT'
    assert repo.db.execute("SELECT COUNT(*) FROM meta WHERE key LIKE 'remote-proof:%'").fetchone()[0] == 0


def test_remote_config_ceiling_is_selected_not_legacy(config):
    from mission_agent.config import Config
    remote = Config.for_remote(config.runtime_root)
    assert remote.max_batch_bytes == 75000 and remote.transport_mode == "GITHUB_PRIVATE"
    with pytest.raises(ValueError): Config.for_remote(config.runtime_root, max_batch_bytes=100000)


def test_crash_after_remote_before_sqlite_checkpoint_replays(repo, config, transport):
    from mission_agent.models import Event
    from mission_agent.clock import stamp
    from mission_agent.queue.batch import build_batch
    from mission_agent.queue.remote import publish_remote
    t, api = transport
    repo.ingest(Event.synthetic('TEST_ACTION_CANDIDATE', 'SYNTH', stamp(repo.clock.now()), 0, {}))
    batch = build_batch(repo, config)
    t.publish_batch(batch)  # Remote has bytes; SQLite still BUILT, as after a killed publisher.
    assert repo.db.execute('SELECT state FROM batches').fetchone()[0] == 'BUILT'
    before = api.puts
    publish_remote(repo, t, batch['batch_id'])
    assert api.puts == before
    assert repo.db.execute('SELECT state FROM batches').fetchone()[0] == 'REMOTE_CONFIRMED'


@pytest.mark.parametrize('headers', [{'x-ratelimit-remaining': '0'}, {'X-RateLimit-Remaining': '0'}, {'retry-after': '1'}])
def test_rate_limit_403_case_insensitive_headers(transport, headers):
    t, api = transport
    api.faults = [('PUT', RemoteError(403, headers), False)]
    assert t.write('mac-data', t._path('health'), {'v': 1}).value == {'v': 1}
    assert api.puts == 1
