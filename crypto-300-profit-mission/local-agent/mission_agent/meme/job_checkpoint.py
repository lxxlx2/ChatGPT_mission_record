"""Private, foreground-only CA job recovery; this is not the RPC TTL cache.

Replay immutable logical reads to reconstruct the same analyzer, then continue
the missing suffix. Reserve each wire attempt durably before transport. A crash
can overcount an uncertain attempt, never create a fresh job budget. GET only
reads metadata; an explicit POST is required to resume.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import time

from .cluster import RPCError, RPCJobBudgetExceeded

MAX_BYTES = 128 * 1024 * 1024
MAX_ENTRIES = 10000
NONRECOVERABLE = {
    'CA_CHECKPOINT_READ_SEQUENCE_CHANGED', 'CA_CHECKPOINT_READ_CHAIN_INVALID',
    'CA_CHECKPOINT_READ_INVALID', 'CA_CHECKPOINT_REPLAY_INCOMPLETE',
    'CA_CHECKPOINT_PAYLOAD_INVALID', 'CA_CHECKPOINT_SIZE_LIMIT',
    'CA_CHECKPOINT_ERROR_TYPE_UNSUPPORTED',
}


class CheckpointError(RPCJobBudgetExceeded):
    """Fixed non-sensitive code; fail closed through analyzer budget handlers."""

    CODES = {
        'CA_CHECKPOINT_ALREADY_DONE', 'CA_CHECKPOINT_ALREADY_RUNNING', 'CA_CHECKPOINT_BUDGET_INVALID',
        'CA_CHECKPOINT_CLOCK_REGRESSION', 'CA_CHECKPOINT_ERROR_TYPE_UNSUPPORTED',
        'CA_CHECKPOINT_IDENTITY_INVALID', 'CA_CHECKPOINT_ID_INVALID', 'CA_CHECKPOINT_METADATA_INVALID',
        'CA_CHECKPOINT_PATH_UNSAFE', 'CA_CHECKPOINT_PAYLOAD_INVALID', 'CA_CHECKPOINT_PERMISSIONS_UNSAFE',
        'CA_CHECKPOINT_READ_CHAIN_INVALID', 'CA_CHECKPOINT_READ_INVALID', 'CA_CHECKPOINT_READ_SEQUENCE_CHANGED',
        'CA_CHECKPOINT_REPLAY_INCOMPLETE', 'CA_CHECKPOINT_SIZE_LIMIT', 'CA_CHECKPOINT_SOURCE_OR_CONFIG_CHANGED',
        'CA_CHECKPOINT_STORAGE_UNAVAILABLE', 'CA_CHECKPOINT_TIME_BUDGET_EXHAUSTED',
        'CA_CHECKPOINT_WIRE_BUDGET_EXHAUSTED', 'CA_CHECKPOINT_UNAVAILABLE',
        'CA_CHECKPOINT_READ_ONLY',
    }

    def __init__(self, code):
        super().__init__(code if isinstance(code, str) and code in self.CODES else 'CA_CHECKPOINT_UNAVAILABLE')


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    except (ValueError, TypeError, OverflowError) as exc:
        raise CheckpointError('CA_CHECKPOINT_PAYLOAD_INVALID') from exc


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def source_fingerprint():
    root = Path(__file__).resolve().parents[1]
    files = sorted(root.rglob('*.py'))
    return digest(canonical([(str(p.relative_to(root)), hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]))


class JobCheckpoint:
    def __init__(self, root, job_id, *, readonly=False, clock=time.time):
        if not isinstance(job_id, str) or re.fullmatch(r'[0-9a-f]{32}', job_id) is None:
            raise CheckpointError('CA_CHECKPOINT_ID_INVALID')
        self.root, self.job_id, self.clock = Path(root), job_id, clock
        self.path = self.root / (job_id + '.sqlite')
        self.readonly, self.lock_fd, self.replayed, self.index = readonly, None, 0, 0
        self.fault = None
        if self.root.is_symlink() or self.path.is_symlink():
            raise CheckpointError('CA_CHECKPOINT_PATH_UNSAFE')
        if not self.path.is_file():
            raise FileNotFoundError('CA_CHECKPOINT_NOT_FOUND')
        if self.root.stat().st_mode & 0o077 or self.path.stat().st_mode & 0o077:
            raise CheckpointError('CA_CHECKPOINT_PERMISSIONS_UNSAFE')
        try:
            self.db = sqlite3.connect(self.path.absolute().as_uri() + '?mode=ro', uri=True) if readonly else sqlite3.connect(self.path)
            self.db.execute('BEGIN')
            row = self.db.execute('SELECT body,sha FROM metadata WHERE id=1').fetchone()
            if not row or digest(row[0]) != row[1]:
                raise CheckpointError('CA_CHECKPOINT_METADATA_INVALID')
            self.meta = json.loads(row[0])
            if self.meta.get('version') != 1 or self.meta.get('job_id') != job_id:
                raise CheckpointError('CA_CHECKPOINT_IDENTITY_INVALID')
            for key in ('wire_used', 'wire_limit', 'bytes_used', 'entry_count'):
                if type(self.meta.get(key)) is not int or self.meta[key] < 0:
                    raise CheckpointError('CA_CHECKPOINT_METADATA_INVALID')
            if not 0 < self.meta['wire_limit'] or self.meta['wire_used'] > self.meta['wire_limit']:
                raise CheckpointError('CA_CHECKPOINT_BUDGET_INVALID')
            seconds = self.meta.get('seconds_limit')
            if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds <= 0:
                raise CheckpointError('CA_CHECKPOINT_BUDGET_INVALID')
            started, deadline = self.meta.get('started_at'), self.meta.get('deadline_at')
            if started is None:
                if deadline is not None or self.meta['wire_used']:
                    raise CheckpointError('CA_CHECKPOINT_BUDGET_INVALID')
            elif (isinstance(started, bool) or not isinstance(started, (int, float)) or not math.isfinite(started)
                  or not isinstance(deadline, (int, float)) or deadline != started + seconds):
                raise CheckpointError('CA_CHECKPOINT_BUDGET_INVALID')
            if self.meta['bytes_used'] > MAX_BYTES or self.meta['entry_count'] > MAX_ENTRIES:
                raise CheckpointError('CA_CHECKPOINT_SIZE_LIMIT')
            self.entries = []
            head = ''
            for seq, body, sha in self.db.execute('SELECT seq,body,sha FROM reads ORDER BY seq'):
                entry = json.loads(body)
                if seq != len(self.entries) or digest(body) != sha or entry.get('previous_sha') != head:
                    raise CheckpointError('CA_CHECKPOINT_READ_CHAIN_INVALID')
                self.entries.append(entry)
                head = sha
            if len(self.entries) != self.meta['entry_count'] or head != self.meta['head']:
                raise CheckpointError('CA_CHECKPOINT_READ_CHAIN_INVALID')
            self.db.commit()
        except BaseException:
            if hasattr(self, 'db'): self.db.close()
            raise

    @classmethod
    def create(cls, root, job, binding, budget, *, clock=time.time):
        root = Path(root)
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if root.is_symlink() or root.stat().st_mode & 0o077:
            raise CheckpointError('CA_CHECKPOINT_PATH_UNSAFE')
        job_id = job['job_id']
        if re.fullmatch(r'[0-9a-f]{32}', job_id) is None:
            raise CheckpointError('CA_CHECKPOINT_ID_INVALID')
        path = root / (job_id + '.sqlite')
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        now = clock()
        meta = {'version': 1, 'job_id': job_id, 'mint': job['mint'], 'preset': job['preset'],
                'created_at': job['created_at'], 'binding': binding, 'started_at': None, 'deadline_at': None,
                'wire_limit': budget['max_wire_attempts'], 'seconds_limit': budget['max_elapsed_seconds'],
                'wire_used': 0, 'cache_hits': 0, 'endpoint_calls': {}, 'endpoint_failures': {},
                'endpoint_last_at': {}, 'endpoint_cooldown_until': {},
                'bytes_used': 0, 'entry_count': 0, 'head': '', 'last_saved_at': now,
                'last_source_read_at': None, 'resume_count': 0, 'status': 'QUEUED'}
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE metadata(id INTEGER PRIMARY KEY,body TEXT NOT NULL,sha TEXT NOT NULL)')
            db.execute('CREATE TABLE reads(seq INTEGER PRIMARY KEY,body TEXT NOT NULL,sha TEXT NOT NULL)')
            db.execute('CREATE TABLE source_errors(id INTEGER PRIMARY KEY,body TEXT NOT NULL,sha TEXT NOT NULL)')
            body = canonical(meta)
            db.execute('INSERT INTO metadata VALUES(1,?,?)', (body, digest(body)))

    def close(self):
        try:self.db.close()
        finally:
            if self.lock_fd is not None:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                os.close(self.lock_fd)
                self.lock_fd = None

    def _save_meta(self):
        body = canonical(self.meta)
        self.db.execute('UPDATE metadata SET body=?,sha=? WHERE id=1', (body, digest(body)))

    def check_binding(self, binding, budget=None):
        if (self.meta['binding'] != binding or (budget is not None and
            (self.meta['wire_limit'] != budget['max_wire_attempts'] or self.meta['seconds_limit'] != budget['max_elapsed_seconds']))):
            raise CheckpointError('CA_CHECKPOINT_SOURCE_OR_CONFIG_CHANGED')

    def _check_time(self):
        now = self.clock()
        if not math.isfinite(now) or now < self.meta['last_saved_at']:
            raise CheckpointError('CA_CHECKPOINT_CLOCK_REGRESSION')
        if self.meta['deadline_at'] is not None and now >= self.meta['deadline_at']:
            raise CheckpointError('CA_CHECKPOINT_TIME_BUDGET_EXHAUSTED')
        if self.fault:
            raise CheckpointError(self.fault)
        if self.meta.get('blocked_reason'):
            raise CheckpointError(self.meta['blocked_reason'])
        return now

    def begin(self, binding, budget=None):
        if self.readonly:raise CheckpointError('CA_CHECKPOINT_READ_ONLY')
        self.check_binding(binding, budget)
        lock = self.root / (self.job_id + '.lock')
        self.lock_fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self.lock_fd); self.lock_fd = None
            raise CheckpointError('CA_CHECKPOINT_ALREADY_RUNNING')
        # Re-read after taking the lease. A second process may have completed
        # between our initial metadata read and this exclusive acquisition.
        fresh = JobCheckpoint(self.root, self.job_id, clock=self.clock)
        self.db.close()
        self.db, self.meta, self.entries = fresh.db, fresh.meta, fresh.entries
        self.check_binding(binding, budget)
        now = self._check_time()
        if self.meta['status'] == 'DONE':
            raise CheckpointError('CA_CHECKPOINT_ALREADY_DONE')
        with self.db:
            if self.meta['started_at'] is None:
                self.meta['started_at'] = now
                self.meta['deadline_at'] = now + self.meta['seconds_limit']
            else:
                self.meta['resume_count'] += 1
                # Retry only the terminal failed logical read after an explicit
                # resume. Its original error stays in source_errors and all wire
                # reservations remain spent. Earlier caught failures replay.
                if self.entries and self.entries[-1]['outcome'] == 'ERROR':
                    last = self.entries.pop()
                    self.db.execute('DELETE FROM reads WHERE seq=?', (len(self.entries),))
                    self.meta.update(entry_count=len(self.entries), head=last['previous_sha'])
            self.meta.update(status='RUNNING', last_saved_at=now)
            self._save_meta()

    def transport_budget(self):
        now = self._check_time()
        return {'max_wire_attempts': max(1, self.meta['wire_limit'] - self.meta['wire_used']),
                'max_elapsed_seconds': self.meta['deadline_at'] - now}

    def before_wire(self, endpoint_index):
        now = self._check_time()
        if self.meta['wire_used'] >= self.meta['wire_limit']:
            raise CheckpointError('CA_CHECKPOINT_WIRE_BUDGET_EXHAUSTED')
        with self.db:
            self.meta['wire_used'] += 1
            key = str(endpoint_index)
            counts = self.meta['endpoint_calls']
            counts[key] = counts.get(key, 0) + 1
            self.meta['endpoint_last_at'][key] = now
            self.meta['last_saved_at'] = now
            self._save_meta()

    def _append(self, request, outcome, response, started_at):
        now = self._check_time()
        entry = {'request': request, 'outcome': outcome, 'response': response,
                 'started_at': started_at, 'finished_at': now, 'previous_sha': self.meta['head']}
        body = canonical(entry)
        size = len(body.encode()) * (2 if outcome == 'ERROR' else 1)
        if self.meta['bytes_used'] + size > MAX_BYTES or len(self.entries) >= MAX_ENTRIES:
            raise CheckpointError('CA_CHECKPOINT_SIZE_LIMIT')
        with self.db:
            self.db.execute('INSERT INTO reads VALUES(?,?,?)', (len(self.entries), body, digest(body)))
            if outcome == 'ERROR':
                self.db.execute('INSERT INTO source_errors(body,sha) VALUES(?,?)', (body, digest(body)))
            self.meta.update(head=digest(body), entry_count=len(self.entries)+1,
                             bytes_used=self.meta['bytes_used']+size, last_saved_at=now,
                             last_source_read_at=now)
            self._save_meta()
        self.entries.append(json.loads(body))
        self.index += 1

    def invoke(self, channel, operation, args, kwargs, function):
        try:
            self._check_time()
            request = json.loads(canonical({'channel': channel, 'operation': operation, 'args': args, 'kwargs': kwargs}))
            if self.index < len(self.entries):
                entry = self.entries[self.index]
                if entry['request'] != request:
                    raise CheckpointError('CA_CHECKPOINT_READ_SEQUENCE_CHANGED')
                self.index += 1; self.replayed += 1
                if entry['outcome'] == 'ERROR':
                    classes = {'RPCError': RPCError, 'TimeoutError': TimeoutError, 'ValueError': ValueError,
                               'RuntimeError': RuntimeError, 'OSError': OSError}
                    kind = classes.get(entry['response']['type'])
                    if kind is None:
                        raise CheckpointError('CA_CHECKPOINT_ERROR_TYPE_UNSUPPORTED')
                    raise kind(entry['response']['code'])
                if entry['outcome'] != 'OK':
                    raise CheckpointError('CA_CHECKPOINT_READ_INVALID')
                return json.loads(canonical(entry['response']))
            started = self.clock()
            try:
                result = function()
            except CheckpointError:
                raise
            except RPCJobBudgetExceeded:
                raise
            except Exception as exc:
                reason = str(exc)
                safe = reason if re.fullmatch(r'(?:HTTP_[0-9]{3}|RPC_-?[0-9]+|RPC_RATE_LIMITED|RPC_ENVELOPE_INVALID|RPC_POOL_RESPONSE_LIMIT|RPC_HOLDER_RANK_RESPONSE_LIMIT)', reason) else 'RECORDED_SOURCE_ERROR'
                self._append(request, 'ERROR', {'type': type(exc).__name__, 'code': safe}, started)
                raise
            self._append(request, 'OK', result, started)
            return json.loads(canonical(result))
        except CheckpointError as exc:
            self.fault = str(exc)
            raise
        except (sqlite3.Error, OSError) as exc:
            self.fault = 'CA_CHECKPOINT_STORAGE_UNAVAILABLE'
            raise CheckpointError(self.fault) from exc

    def finish(self, status):
        with self.db:
            if status == 'ERROR' and self.fault in NONRECOVERABLE:
                self.meta['blocked_reason'] = self.fault
            self.meta.update(status=status, last_saved_at=max(self.clock(), self.meta['last_saved_at']))
            self._save_meta()

    def assert_can_publish(self):
        self._check_time()
        if self.index != len(self.entries):
            self.fault = 'CA_CHECKPOINT_REPLAY_INCOMPLETE'
            raise CheckpointError(self.fault)

    def public_job(self):
        available = self.meta['status'] != 'DONE' and self.meta['wire_used'] < self.meta['wire_limit']
        try: self._check_time()
        except CheckpointError: available = False
        lock = self.root / (self.job_id + '.lock')
        if lock.exists():
            fd = os.open(lock, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                try:
                    fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
                    fcntl.flock(fd, fcntl.LOCK_UN)
                except OSError:
                    available = False
            finally: os.close(fd)
        return {'job_id': self.job_id, 'mint': self.meta['mint'], 'preset': self.meta['preset'],
                'checkpoint_version': 1,
                'status': 'PAUSED', 'created_at': self.meta['created_at'],
                'started_at': self.meta['started_at'], 'finished_at': None, 'error': None,
                'progress': {'stage': 'PAUSED', 'source': 'SAVED_CA_CHECKPOINT'},
                'resume_available': available, 'restored_from_checkpoint': True,
                'remaining_wire_attempts': self.meta['wire_limit']-self.meta['wire_used'],
                'resume_deadline_at': self.meta['deadline_at']}

    def provenance(self):
        return {'version': 1, 'mode': 'RESUMED_HISTORICAL_JOB' if self.meta['resume_count'] else 'ORIGINAL_JOB',
                'source_epoch_started_at': self.meta['started_at'],
                'last_source_read_at': self.meta['last_source_read_at'],
                'resume_count': self.meta['resume_count'], 'replayed_logical_reads': self.replayed,
                'reserved_wire_attempts': self.meta['wire_used'],
                'reserved_attempts_include_uncertain_crash_outcomes': True,
                'original_deadline_at': self.meta['deadline_at'], 'rpc_cache_ttls_unchanged': True,
                'does_not_prove_current_balances_or_complete_history': True}


class CheckpointRPC:
    def __init__(self, checkpoint, rpc):
        self.checkpoint, self.rpc = checkpoint, rpc
        self.base_cache_hits = checkpoint.meta['cache_hits']
        self.base_failures = dict(checkpoint.meta['endpoint_failures'])
        now, monotonic = checkpoint.clock(), rpc._monotonic()
        for key, value in checkpoint.meta['endpoint_last_at'].items():
            rpc._last_by_endpoint[rpc.endpoints[int(key)]] = monotonic - max(0, now-value)
        for key, value in checkpoint.meta['endpoint_cooldown_until'].items():
            rpc._cooldown_until[rpc.endpoints[int(key)]] = monotonic + max(0, value-now)
        rpc.before_wire = lambda endpoint: checkpoint.before_wire(rpc.endpoints.index(endpoint))
        rpc.transport_updated = self._store_transport

    def _store_transport(self):
        now, monotonic = self.checkpoint._check_time(), self.rpc._monotonic()
        with self.checkpoint.db:
            self.checkpoint.meta['cache_hits'] = self.base_cache_hits + self.rpc.cache_hits
            for endpoint, value in self.rpc.endpoint_failures.items():
                key = str(self.rpc.endpoints.index(endpoint))
                self.checkpoint.meta['endpoint_failures'][key] = self.base_failures.get(key, 0) + value
            for endpoint, value in self.rpc._last_by_endpoint.items():
                self.checkpoint.meta['endpoint_last_at'][str(self.rpc.endpoints.index(endpoint))] = now-max(0, monotonic-value)
            for endpoint, value in self.rpc._cooldown_until.items():
                self.checkpoint.meta['endpoint_cooldown_until'][str(self.rpc.endpoints.index(endpoint))] = now+max(0, value-monotonic)
            self.checkpoint.meta['last_saved_at'] = now
            self.checkpoint._save_meta()

    def __getattr__(self, name):
        return getattr(self.rpc, name)

    @property
    def calls(self): return self.checkpoint.meta['wire_used']

    @property
    def endpoint_calls(self):
        return {self.rpc.endpoints[int(k)]: v for k, v in self.checkpoint.meta['endpoint_calls'].items()}

    @property
    def cache_hits(self): return self.checkpoint.meta['cache_hits']

    @property
    def endpoint_failures(self):
        return {self.rpc.endpoints[int(k)]: v for k, v in self.checkpoint.meta['endpoint_failures'].items()}

    def call(self, method, params, *, ttl=0):
        def read():
            try:
                return self.rpc.call(method, params, ttl=ttl)
            finally:
                self._store_transport()
        return self.checkpoint.invoke('rpc', method, [params], {'ttl': ttl}, read)

    def assert_can_publish(self):
        self.rpc.assert_can_publish()
        self.checkpoint.assert_can_publish()


class CheckpointClient:
    def __init__(self, checkpoint, client, channel):
        self.checkpoint, self.client, self.channel = checkpoint, client, channel

    def _call(self, method, *args):
        return self.checkpoint.invoke(self.channel, method, args, {}, lambda: getattr(self.client, method)(*args))

    def token_snapshot(self, mint): return self._call('token_snapshot', mint)
    def pool_snapshot(self, mint, pool, quote): return self._call('pool_snapshot', mint, pool, quote)
    def collect(self, mint, market): return self._call('collect', mint, market)
