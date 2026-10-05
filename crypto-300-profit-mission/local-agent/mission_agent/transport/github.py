"""Private GitHub contents transport. Test-only namespace; logical role isolation.

Credentials are obtained in memory from existing gh auth, never persisted here.
CAS callers must supply the last observed blob SHA (None means absent).
"""
import base64
import hashlib
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from ..hashing import canonical, loads, verify

REPOSITORY = 'lxxlx2/crypto-monitor-runtime'


class RemoteError(RuntimeError):
    def __init__(self, status, headers=None):
        self.status = status
        self.headers = {key.lower(): str(value) for key, value in (headers or {}).items()}
        super().__init__(f'GitHub status {status}')


class Conflict(ValueError):
    pass


class GitHubAPI:
    def __init__(self, timeout=30):
        self.timeout = timeout
        self.requests = self.commits = self.uploaded = self.downloaded = 0
        self.token = subprocess.run(['gh', 'auth', 'token'], check=True,
                                    capture_output=True, text=True).stdout.strip()
        if not self.token:
            raise ValueError('GitHub credential unavailable')

    def request(self, method, endpoint, body=None):
        if endpoint != '/repos/' + REPOSITORY and not endpoint.startswith('/repos/' + REPOSITORY + '/'):
            raise ValueError('repository not allowlisted')
        raw = None if body is None else json.dumps(body).encode()
        self.requests += 1
        self.uploaded += len(raw or b'')
        req = urllib.request.Request('https://api.github.com' + endpoint, data=raw,
            method=method, headers={'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = response.read()
                self.downloaded += len(data)
                result = json.loads(data)
                if method == 'PUT':
                    self.commits += 1
                return result
        except urllib.error.HTTPError as exc:
            # Provider body may contain identifiers; never expose it in errors.
            self.downloaded += len(exc.read())
            raise RemoteError(exc.code, dict(exc.headers)) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise RemoteError(0) from None


@dataclass(frozen=True)
class Readback:
    value: dict
    data: bytes
    blob_sha: str
    commit_sha: str
    branch: str
    path: str


class GitHubTransport:
    remote_confirmed = True

    def __init__(self, role, run_id, api=None, repository=REPOSITORY,
                 max_batch_bytes=75000, attempts=3, sleep=time.sleep):
        if repository != REPOSITORY:
            raise ValueError('repository not allowlisted')
        if role not in ('mac', 'gpt') or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', run_id):
            raise ValueError('invalid role/test namespace')
        if not 1 <= max_batch_bytes <= 100000 or not 1 <= attempts <= 5:
            raise ValueError('invalid transport limits')
        self.role, self.namespace = role, 'runtime-v2-test/' + run_id
        self.branch = {'mac': 'mac-data', 'gpt': 'gpt-data'}[role]
        self.api = api or GitHubAPI()
        self.max_batch_bytes, self.attempts, self.sleep = max_batch_bytes, attempts, sleep

    def _request(self, method, endpoint, body=None):
        for attempt in range(self.attempts):
            try:
                return self.api.request(method, endpoint, body)
            except RemoteError as exc:
                retry = exc.status in (0, 429, 500, 502, 503, 504) or (
                    exc.status == 403 and (exc.headers.get('x-ratelimit-remaining') == '0'
                                          or 'retry-after' in exc.headers))
                if not retry or attempt + 1 == self.attempts:
                    raise
                # Never park the runtime indefinitely; preserve work on exhausted retry.
                delay = exc.headers.get('retry-after', '0')
                try: delay = float(delay)
                except ValueError: delay = 0
                if delay > 30:
                    raise
                self.sleep(max(2 ** attempt, delay))

    def _private(self):
        # Verify before every public operation; visibility may change between cycles.
        repo = self._request('GET', '/repos/' + REPOSITORY)
        if repo.get('private') is not True or repo.get('full_name') != REPOSITORY:
            raise ValueError('PRIVATE_REPO_PROVISIONING_REQUIRED')

    def _endpoint(self, branch, path):
        if branch not in ('mac-data', 'gpt-data') or not path.startswith(self.namespace + '/'):
            raise ValueError('branch/path not allowlisted')
        if any(part in ('.', '..', '') for part in path.split('/')):
            raise ValueError('invalid path')
        return '/repos/' + REPOSITORY + '/contents/' + urllib.parse.quote(path, safe='/')

    def read(self, branch, path):
        self._private()
        endpoint = self._endpoint(branch, path)
        head = self._request('GET', '/repos/' + REPOSITORY + '/git/ref/heads/' + branch)['object']['sha']
        # Pin read to a commit, so content/branch provenance cannot drift mid-read.
        result = self._request('GET', endpoint + '?ref=' + head)
        if result.get('path') != path or result.get('encoding') != 'base64':
            raise ValueError('remote read contract mismatch')
        data = base64.b64decode(result['content'])
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if len(data) != result['size'] or blob != result['sha']:
            raise ValueError('remote read truncated/hash mismatch')
        value = loads(data)
        if canonical(value) != data:
            raise ValueError('remote noncanonical bytes')
        return Readback(value, data, blob, head, branch, path)

    def _optional(self, branch, path):
        try: return self.read(branch, path)
        except RemoteError as exc:
            if exc.status == 404: return None
            raise

    def write(self, branch, path, value, expected_sha=None, immutable=False):
        # Role guard is checked before any network call, even with a broad credential.
        if branch != self.branch:
            raise ValueError('wrong writer branch')
        endpoint = self._endpoint(branch, path)
        self._private()
        immutable = immutable or '/archive/' in path
        data = canonical(value)
        old = self._optional(branch, path)
        if old and old.data == data:
            return old
        if immutable and old:
            raise Conflict('HASH_CONFLICT')
        if (old.blob_sha if old else None) != expected_sha:
            raise Conflict('CAS_CONFLICT')
        body = {'message': 'Phase 2A synthetic transport', 'branch': branch,
                'content': base64.b64encode(data).decode()}
        if expected_sha is not None: body['sha'] = expected_sha
        try:
            # A PUT timeout is ambiguous: read before retry, never blind resend.
            result = self.api.request('PUT', endpoint, body)
        except RemoteError as exc:
            if exc.status not in (0, 409, 422, 429, 500, 502, 503, 504, 403): raise
            latest = self._optional(branch, path)
            if latest and latest.data == data: return latest
            if (latest.blob_sha if latest else None) != expected_sha:
                raise Conflict('HASH_CONFLICT' if immutable else 'CAS_CONFLICT') from None
            # Retry only after proving expected state remains unchanged.
            for attempt in range(1, self.attempts):
                retryable = exc.status in (0, 429, 500, 502, 503, 504) or (
                    exc.status == 403 and (exc.headers.get('x-ratelimit-remaining') == '0' or 'retry-after' in exc.headers))
                if not retryable: raise exc
                delay = exc.headers.get('retry-after', '0')
                try: delay = float(delay)
                except ValueError: delay = 0
                if delay > 30: raise exc
                self.sleep(max(2 ** (attempt - 1), delay))
                try:
                    result = self.api.request('PUT', endpoint, body)
                    break
                except RemoteError as newer:
                    exc = newer
                    latest = self._optional(branch, path)
                    if latest and latest.data == data: return latest
                    if (latest.blob_sha if latest else None) != expected_sha:
                        raise Conflict('CAS_CONFLICT') from None
            else: raise exc
        actual = self.read(branch, path)
        if actual.data != data or not result.get('commit', {}).get('sha'):
            raise ValueError('publish readback mismatch')
        # Read the exact write commit too, in case a subsequent branch update raced.
        committed = self._request('GET', endpoint + '?ref=' + result['commit']['sha'])
        if base64.b64decode(committed.get('content', '')) != data or committed.get('sha') != actual.blob_sha:
            raise ValueError('commit readback mismatch')
        return Readback(actual.value, data, actual.blob_sha, result['commit']['sha'], branch, path)

    def _path(self, kind, identity=None):
        if identity is None: return self.namespace + '/' + kind + '/current.json'
        return self.namespace + '/' + kind + '/archive/' + urllib.parse.quote(identity, safe=':_-') + '.json'

    def _publish(self, kind, identity, value, expected_sha):
        self.write(self.branch, self._path(kind, identity), value, immutable=True)
        return self.write(self.branch, self._path(kind), value, expected_sha=expected_sha)

    def publish_batch(self, batch, expected_sha=None):
        if self.role != 'mac': raise ValueError('wrong writer role')
        verify(batch)
        if len(canonical(batch)) > self.max_batch_bytes: raise ValueError('batch exceeds selected ceiling')
        return self._publish('ingest', batch['batch_id'], batch, expected_sha)

    def read_batch(self, batch_id=None):
        result = self.read('mac-data', self._path('ingest', batch_id))
        verify(result.value)
        if len(result.data) > self.max_batch_bytes: raise ValueError('batch exceeds selected ceiling')
        return result.value

    def publish_receipt(self, receipt, expected_sha=None):
        if self.role != 'gpt': raise ValueError('wrong writer role')
        return self._publish('decisions', receipt['input_batch_id'], receipt, expected_sha)

    def read_receipt(self, batch_id=None):
        return self.read('gpt-data', self._path('decisions', batch_id)).value

    def publish_health(self, health, expected_sha=None):
        if self.role != 'mac': raise ValueError('wrong writer role')
        return self.write(self.branch, self._path('health'), health, expected_sha)

    def read_health(self):
        return self.read('mac-data', self._path('health')).value

    def publish_delivery(self, summary, identity, expected_sha=None):
        if self.role != 'gpt' or summary.get('mode') not in ('DRY_RUN', 'MOCK', 'NOT_SENT'):
            raise ValueError('real send forbidden')
        return self._publish('delivery', identity, summary, expected_sha)
