#!/usr/bin/env python3
"""PR39 dual-service release. Default is production-read-only inventory.

Apply requires exact release SHA and two explicit authorization flags. No network
provider, signal synthesis, Git merge, Frank scanner mutation or SQLite restore.
All output is aggregate/redacted. Private journal enables fail-closed recovery.
"""
from __future__ import annotations
import argparse
import ctypes
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import fcntl
import getpass
import hashlib
import tarfile
import io
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import shlex
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from urllib.parse import quote

PRODUCT = 'bda7ef0dfd89e6c1b11f9020163bf754bed5ae74'
PR39 = 'da5adc0ae63141e8e2b5fb6735224c6405412e6a'
MAIN = '71f223c12b239ffbca66932b8e1f5216ac2bc5a8'
PREFIX = 'crypto-300-profit-mission/local-agent/'
ALLOWED = {'mission_agent/mission_control/' + p for p in (
    'db.py', 'delivery.py', 'payment_evidence.py', 'server.py', 'service.py',
    'static/app.js', 'static/styles.css')}
TABLES = ('decision_events', 'decision_snapshots', 'decision_outbox',
          'gmail_delivery', 'local_delivery')
TERMINAL = {
    'gmail_delivery': {'SENT_VERIFIED', 'MANUAL_REVIEW', 'PERMANENT_ERROR', 'DRY_RUN_AUDIT'},
    'local_delivery': {'COMMAND_ACCEPTED', 'MANUAL_REVIEW', 'DRY_RUN_AUDIT'},
    'decision_outbox': {'SENT_VERIFIED', 'MANUAL_REVIEW', 'PERMANENT_ERROR',
                        'DRY_RUN_AUDIT', 'COMMAND_ACCEPTED'},
}
REASONS = {'GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND',
           'GMAIL_SENT_OUTCOME_UNRESOLVED_TOO_LONG', 'GMAIL_RETRY_LIMIT_REACHED',
           'LOCAL_GMAIL_CREDENTIAL_UNAVAILABLE', 'GMAIL_DELIVERY_OR_READBACK_RETRY_PENDING',
           'SEND_OUTCOME_UNCERTAIN_WAITING_SENT', 'MULTIPLE_SENT_IDENTITIES_REQUIRE_REVIEW',
           'SENT_IDENTITY_OR_CONTENT_MISMATCH'}
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mission_agent.hashing import digest

DDL = '''CREATE TABLE IF NOT EXISTS local_delivery_presentation(
 decision_id TEXT PRIMARY KEY, title TEXT NOT NULL, summary TEXT NOT NULL,
 content_hash TEXT NOT NULL,
 FOREIGN KEY(decision_id) REFERENCES local_delivery(decision_id))'''


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def run(argv, **kw):
    return subprocess.run(argv, capture_output=True, text=True, check=True,
                          timeout=kw.pop('timeout', 20), **kw).stdout.strip()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ro(path):
    require(Path(path).is_file(), 'DB_MISSING')
    db = sqlite3.connect('file:' + quote(str(Path(path).resolve()), safe='/') + '?mode=ro',
                         uri=True, isolation_level=None, timeout=2)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    return db


def integrity(db):
    require([r[0] for r in db.execute('PRAGMA integrity_check')] == ['ok'], 'SQLITE_INTEGRITY')
    require(not db.execute('PRAGMA foreign_key_check').fetchall(), 'SQLITE_FOREIGN_KEYS')


def ledger(path):
    with closing(ro(path)) as db:
        db.execute('BEGIN')
        integrity(db)
        result = {t: [dict(r) for r in db.execute('SELECT * FROM ' + t + ' ORDER BY rowid')]
                  for t in TABLES}
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        result['local_delivery_presentation'] = (
            [dict(r) for r in db.execute('SELECT * FROM local_delivery_presentation ORDER BY rowid')]
            if 'local_delivery_presentation' in tables else [])
        for t, terminal in TERMINAL.items():
            for row in result[t]:
                require(row['status'] in terminal, 'ACTIVE_OR_UNKNOWN_QUEUE_' + t)
        for row in result['gmail_delivery']:
            require(digest({'subject': row['subject'], 'body': row['body']}) == row['content_hash'],
                    'GMAIL_FROZEN_BODY_HASH')
            require(row['wire_message_id'] == '<mission.' + digest({
                    'decision_id': row['decision_id'], 'mode': row['delivery_mode']}) + '@local.invalid>',
                    'GMAIL_WIRE_IDENTITY')
        for row in result['decision_events']:
            require(digest(json.loads(row['body'])) == row['content_hash'], 'DECISION_BODY_HASH')
        # Every receipt must have its corresponding outbox entry and identical state/hash.
        outbox = {(r['decision_id'], r['channel']): r for r in result['decision_outbox']}
        for table, channel in (('gmail_delivery', 'gmail'), ('local_delivery', 'local')):
            for row in result[table]:
                peer = outbox.get((row['decision_id'], channel))
                require(peer is not None and peer['status'] == row['status'] and
                        peer['content_hash'] == row['content_hash'], 'OUTBOX_RECEIPT_CONFLICT')
        return result


def assert_preserved(before, after, *, exact=False):
    for table in before:
        keys = ('decision_id', 'channel') if table == 'decision_outbox' else (
            ('snapshot_id',) if table == 'decision_snapshots' else ('decision_id',))
        indexed = {tuple(r[k] for k in keys): r for r in after[table]}
        for row in before[table]:
            require(indexed.get(tuple(row[k] for k in keys)) == row, 'LEGACY_ROW_MUTATED_' + table)
        if exact:
            require(len(after[table]) == len(before[table]), 'NEW_RECORDS_ROLLBACK_BLOCKED')


def review_reasons(state):
    rows = [r for r in state['gmail_delivery'] if r['delivery_mode'] == 'LIVE'
            and r['status'] == 'MANUAL_REVIEW']
    counts = Counter(r['last_error'] if r['last_error'] in REASONS else 'UNVERIFIED_OTHER_REASON'
                     for r in rows)
    stale_unsent = sum(r['last_error'] == 'GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND'
                      and r['attempt_count'] == 0 and not r['sent_at'] and not r['gmail_message_id']
                      and not r['readback_verified'] for r in rows)
    return {'manual_review_live': len(rows), 'reason_counts': dict(counts),
            'expired_before_any_send': stale_unsent,
            'requires_private_review': len(rows) - stale_unsent}



RELEASE_MARKER = '.pr39-release-manifest.json'

# Provenance: scripts/deploy_frank_dashboard_review_badge.py PATCHES
# from the committed Mission repo. These are known legacy UI overlays,
# NOT authorization to trust a running process or bypass any rollout gate.
HISTORICAL_UI_LEGACY_BLOBS = {
    'mission_agent/mission_control/server.py': (
        'b5eb4af5c945cc1b62337d48393fe02243f9505f',
        'f5e00781ea4af45b4d6b15a09b8cb000f5b744f4'),
    'mission_agent/mission_control/static/app.js': (
        '8f0ac1beace94f01894c151576bc276f48f1b4a4',
        '14985b35b019054d5ff9871e002c32421345ff17'),
}
HISTORICAL_UI_LEGACY_EXTRA = {
    'mission_agent/mission_control/delivery_review.py':
        '62f5fa85bf41cd95e4a31a373910f81970368ea6',
}



def release_manifest(root):
    """Immutable staged release: verify every file byte and reject any extra source."""
    marker = root / RELEASE_MARKER
    require(marker.is_file() and not marker.is_symlink(), 'RELEASE_MARKER_MISSING')
    expected = json.loads(marker.read_text(encoding='utf-8'))['files']
    for rel, expected_digest in expected.items():
        local = root / rel
        require(local.is_file() and not local.is_symlink(), 'RELEASE_FILE_MISSING')
        require(sha(local) == expected_digest, 'RELEASE_MANIFEST_MISMATCH')
    for base in ('mission_agent', 'config'):
        for local in (root / base).rglob('*'):
            if local.is_file() and local.suffix in {'.py', '.js', '.css', '.html', '.json'}:
                require(local.relative_to(root).as_posix() in expected, 'RELEASE_EXTRA_FILE')
    return dict(expected)


def stage_immutable_release(mac, root, expected, source):
    """Copy the exact approved SHA into a private read-only directory. Production runners
    never point at the operator's mutable checkout or cache clone."""
    root = Path(root).resolve()
    repo = Path(run(['git', '-C', str(root), 'rev-parse', '--show-toplevel']))
    prefix = '' if root == repo else root.relative_to(repo).as_posix() + '/'
    final = mac.support / 'pr39-immutable-releases' / expected[:12]
    if final.exists():
        require(release_manifest(final) == source, 'EXISTING_IMMUTABLE_RELEASE_MISMATCH')
        require(all(not (path.stat().st_mode & 0o222)
                    for path in [final, *final.rglob('*')]), 'EXISTING_RELEASE_NOT_READ_ONLY')
        return final
    staging = final.with_name(final.name + '.staging-%d' % os.getpid())
    require(not staging.exists(), 'RELEASE_STAGING_EXISTS')
    staging.mkdir(parents=True, mode=0o700)
    try:
        args = ['git', '-C', str(repo), 'archive', '--format=tar', expected]
        if prefix:
            args += ['--', prefix.rstrip('/')]
        data = subprocess.run(args, capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            for member in archive.getmembers():
                require(not (member.issym() or member.islnk() or member.name.startswith('/')
                             or '..' in Path(member.name).parts), 'ARCHIVE_MEMBER_UNSAFE')
            if hasattr(tarfile, 'data_filter'):
                archive.extractall(staging, filter='data')
            else:
                archive.extractall(staging)
        local = staging / prefix.rstrip('/') if prefix else staging
        staged = {rel: sha(local / rel) for rel in source if (local / rel).is_file()}
        require(staged == source, 'STAGED_RELEASE_SOURCE_MISMATCH')
        (local / RELEASE_MARKER).write_text(json.dumps({'expected': expected, 'files': staged}, sort_keys=True), encoding='utf-8')
        require(release_manifest(local) == source, 'STAGED_RELEASE_MARKER_MISMATCH')
        # Publish the fully verified bytes *before* removing directory write
        # permission: rename needs permission on the nested source's parent.
        local.rename(final)
        for path in sorted(final.rglob('*'), reverse=True):
            os.chmod(path, 0o555 if path.is_dir() else 0o444)
        os.chmod(final, 0o555)
        require(all(not (path.stat().st_mode & 0o222)
                    for path in [final, *final.rglob('*')]), 'STAGED_RELEASE_NOT_READ_ONLY')
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    return final


def source_manifest(root):
    """Check actual bytes, including ignored extra executable sources, not only HEAD."""
    root = Path(root).resolve()
    if (root / RELEASE_MARKER).is_file():
        return release_manifest(root)
    repo = Path(run(['git', '-C', str(root), 'rev-parse', '--show-toplevel']))
    prefix = '' if root == repo else root.relative_to(repo).as_posix() + '/'
    paths = run(['git', '-C', str(repo), 'ls-tree', '-r', '--name-only', 'HEAD', '--',
                 prefix + 'mission_agent', prefix + 'config', prefix + 'scripts/mission_meme_v1.py']).splitlines()
    require(paths, 'EMPTY_SOURCE')
    result = {}
    for path in paths:
        local = repo / path
        require(local.is_file() and not local.is_symlink(), 'SOURCE_MISSING_OR_SYMLINK')
        expected = run(['git', '-C', str(repo), 'rev-parse', 'HEAD:' + path])
        actual = run(['git', '-C', str(repo), 'hash-object', str(local)])
        require(expected == actual, 'SOURCE_MIXED_BYTES')
        result[path[len(prefix):]] = sha(local)
    for base in ('mission_agent', 'config'):
        for local in (root / base).rglob('*'):
            if local.is_file() and local.suffix in {'.py', '.js', '.css', '.html', '.json'}:
                require(local.relative_to(root).as_posix() in result, 'SOURCE_EXTRA_FILE')
    return result


def source_drift_diagnostic(root, *, limit=30):
    """Read-only forensic facts for an unverified live checkout.

    Diagnoses but NEVER authorizes SOURCE_MIXED_BYTES. Git HEAD is not enough
    to prove what a previously patched macOS production worktree is executing.
    Only repository-relative code paths and hashes are reported; no file bodies,
    home paths, credentials, wallet data or identifiers leave this function.
    """
    root = Path(root).resolve()
    repo = Path(run(['git', '-C', str(root), 'rev-parse', '--show-toplevel']))
    prefix = '' if root == repo else root.relative_to(repo).as_posix() + '/'
    raw_paths = run(['git', '-C', str(repo), 'ls-tree', '-r', '--name-only', 'HEAD', '--',
                     prefix + 'mission_agent', prefix + 'config',
                     prefix + 'scripts/mission_meme_v1.py']).splitlines()
    require(raw_paths, 'EMPTY_SOURCE')
    mismatches = []
    changes = 0
    for repository_path in raw_paths:
        relative = repository_path[len(prefix):]
        local = root / relative
        expected = run(['git', '-C', str(repo), 'rev-parse', 'HEAD:' + repository_path])
        observed = (run(['git', '-C', str(repo), 'hash-object', str(local)])
                    if local.is_file() and not local.is_symlink() else None)
        if expected != observed:
            changes += 1
            if len(mismatches) < limit:
                mismatches.append({'file': relative, 'expected_git_blob': expected,
                                   'observed_git_blob': observed, 'reason':
                                   'BYTES_DIFFER' if observed else 'MISSING_OR_SYMLINK'})
    known = {p[len(prefix):] for p in raw_paths}
    extra_count = 0
    extras = []
    extra_blobs = {}
    for base in ('mission_agent', 'config'):
        for local in (root / base).rglob('*'):
            if local.is_file() and local.suffix in {'.py', '.js', '.css', '.html', '.json'}:
                relative = local.relative_to(root).as_posix()
                if relative not in known:
                    extra_count += 1
                    if len(extras) < limit:
                        extras.append(relative)
                        extra_blobs[relative] = (
                            run(['git', '-C', str(repo), 'hash-object', str(local)])
                            if not local.is_symlink() else None)
    # Classification is strictly explanatory. A match cannot prove the
    # old loop actually loaded these bytes or the current runner settings.
    expected_mismatches = {
        rel: {'file': rel, 'expected_git_blob': pair[0],
              'observed_git_blob': pair[1], 'reason': 'BYTES_DIFFER'}
        for rel, pair in HISTORICAL_UI_LEGACY_BLOBS.items()
    }
    legacy_exact = (
        changes == len(expected_mismatches) and
        {x['file']: x for x in mismatches} == expected_mismatches and
        extra_count == len(HISTORICAL_UI_LEGACY_EXTRA) and
        extra_blobs == HISTORICAL_UI_LEGACY_EXTRA
    )
    return {'status': 'BYTES_VERIFIED' if not (changes or extra_count) else 'UNVERIFIED_SOURCE_DRIFT',
            'historical_overlay_classification': (
                'DOCUMENTED_LEGACY_DISK_BYTES_RUNTIME_UNVERIFIED' if legacy_exact
                else 'NO_EXACT_LEGACY_MATCH'),
            'tracked_files': len(raw_paths), 'different_or_missing_count': changes,
            'untracked_executable_count': extra_count,
            'mismatches': mismatches, 'unexpected_source_paths': extras,
            'unexpected_source_git_blobs': extra_blobs,
            'results_truncated': changes > limit or extra_count > limit,
            'note': 'Diagnostic only; does not relax runtime/source release gate'}


class _DarwinProcBSDInfo(ctypes.Structure):
    """Apple XNU sys/proc_info.h struct proc_bsdinfo (public ABI)."""
    _fields_ = ([(name, ctypes.c_uint32) for name in (
        'pbi_flags', 'pbi_status', 'pbi_xstatus', 'pbi_pid', 'pbi_ppid',
        'pbi_uid', 'pbi_gid', 'pbi_ruid', 'pbi_rgid',
        'pbi_svuid', 'pbi_svgid', 'rfu_1')] +
        [('pbi_comm', ctypes.c_char * 16),
         ('pbi_name', ctypes.c_char * 32)] +
        [(name, ctypes.c_uint32) for name in (
            'pbi_nfiles', 'pbi_pgid', 'pbi_pjobc',
            'e_tdev', 'e_tpgid')] +
        [('pbi_nice', ctypes.c_int32),
         ('pbi_start_tvsec', ctypes.c_uint64),
         ('pbi_start_tvusec', ctypes.c_uint64)])


def darwin_precise_process_start(pid, ps_second):
    """Independent, microsecond-resolution process birth; fail closed if invalid.

    libproc.proc_pidinfo(PROC_PIDTBSDINFO=3) returns a fixed-size BSD info
    structure with pbi_start_tvsec/pbi_start_tvusec. Cross-check against
    /bin/ps's rounded-down lstart second to avoid misreading ABI offsets,
    race/PID reuse, or unrecognized macOS layouts. NEVER restart processes.
    """
    require(sys.platform == 'darwin', 'KERNEL_PROCESS_BIRTH_UNAVAILABLE')
    try:
        lib = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
        read = lib.proc_pidinfo
        read.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_uint64,
                         ctypes.c_void_p, ctypes.c_int)
        read.restype = ctypes.c_int
        info = _DarwinProcBSDInfo()
        size = ctypes.sizeof(info)
        count = read(int(pid), 3, 0, ctypes.byref(info), size)
    except (OSError, ValueError, AttributeError) as exc:
        raise RuntimeError('KERNEL_PROCESS_BIRTH_UNAVAILABLE') from exc
    require(count == size and info.pbi_pid == int(pid)
            and 0 <= info.pbi_start_tvusec < 1_000_000,
            'KERNEL_PROCESS_BIRTH_UNVERIFIED')
    observed = float(info.pbi_start_tvsec) + info.pbi_start_tvusec / 1_000_000
    require(int(observed) == int(ps_second), 'PROCESS_BIRTH_VS_PS_MISMATCH')
    return observed


def runner_start_time_diagnostic(mac, key, text):
    """Only measure second-granularity ps/runner timestamp ambiguity; never clear it."""
    runner = mac.runners[key]
    pid, _ = mac.launch(mac.labels[key])
    command = run(['/bin/ps', '-p', str(pid), '-o', 'lstart='],
                  env={**os.environ, 'LC_ALL': 'C'})
    process_start_second = time.mktime(time.strptime(
        command, '%a %b %d %H:%M:%S %Y'))
    runner_mtime = runner.stat().st_mtime
    delta = runner_mtime - process_start_second
    result = {'pid': pid, 'runner_hash_sha256': sha(runner),
              'runner_minus_process_start_seconds': round(delta, 6),
              'timestamp_resolution': 'ps_lstart_one_second',
              'status': ('UNVERIFIED_SAME_SECOND' if 0 <= delta < 1
                         else 'RUNNER_NEWER_THAN_PROCESS' if delta >= 1
                         else 'RUNNER_OLDER_THAN_PROCESS'),
              'note': 'Read-only diagnostic; time alone cannot prove loaded runner bytes'}
    if sys.platform == 'darwin':
        try:
            birth = darwin_precise_process_start(pid, process_start_second)
            difference = runner_mtime - birth
            result['kernel_birth_check'] = 'VERIFIED_AGAINST_PS_SECOND'
            result['runner_minus_precise_process_start_seconds'] = round(difference, 6)
            result['status'] = ('RUNNER_NEWER_THAN_PROCESS' if difference >= 0
                                else 'RUNNER_OLDER_THAN_PROCESS')
            result['timestamp_resolution'] = 'kernel_microsecond'
        except RuntimeError as exc:
            result['kernel_birth_check'] = str(exc)
            result['note'] = 'No valid kernel timestamp; old coarse ambiguity remains blocking'
    return result


def source_start_temporal_diagnostic(mac, key):
    """Source-file mtimes against process start, even for legacy overlays.

    This cannot prove which modules Python imported. It can, however,
    establish whether bytes may have been changed after a process started.
    Purely read-only and never used to waive mac.runtime's strict checks.
    """
    text = mac.runners[key].read_text(encoding='utf-8')
    root = field(text, 'LOCAL_AGENT')
    pid, _ = mac.launch(mac.labels[key])
    raw = run(['/bin/ps', '-p', str(pid), '-o', 'lstart='],
              env={**os.environ, 'LC_ALL': 'C'})
    started = time.mktime(time.strptime(raw, '%a %b %d %H:%M:%S %Y'))
    files = []
    for base in ('mission_agent', 'config'):
        for path in (root / base).rglob('*'):
            if path.is_file() and path.suffix in {'.py', '.js', '.css', '.html', '.json'}:
                files.append(path)
    entry = root / 'scripts/mission_meme_v1.py'
    if entry.is_file(): files.append(entry)
    late = []
    for path in files:
        delta = path.stat().st_mtime - started
        if delta >= 0:
            late.append({'file': path.relative_to(root).as_posix(),
                         'seconds_after_reported_start': round(delta, 6)})
    return {'pid': pid, 'source_file_count': len(files),
            'files_not_proven_to_predate_process_count': len(late),
            'late_source_files': late[:30],
            'results_truncated': len(late) > 30,
            'status': ('SOURCE_FILES_MAY_HAVE_CHANGED_AFTER_START' if late
                       else 'ALL_OBSERVED_SOURCE_FILES_PREDATE_PROCESS_SECOND'),
            'note': 'Diagnostic only: source mtime cannot establish imported Python bytes'}


def candidate(root, expected):
    require(re.fullmatch('[a-f0-9]{40}', expected or '') is not None, 'EXACT_SHA_REQUIRED')
    require(run(['git', '-C', str(root), 'rev-parse', 'HEAD']) == expected, 'RELEASE_SHA')
    require(not run(['git', '-C', str(root), 'status', '--porcelain']), 'RELEASE_DIRTY')
    for pin in (PRODUCT, PR39):
        require(not run(['git', '-C', str(root), 'diff', '--name-only', pin, 'HEAD', '--',
                         'mission_agent', 'config', 'scripts/mission_meme_v1.py']), 'PRODUCT_REVIEW_DRIFT')
    remote = run(['git', 'ls-remote', 'https://github.com/lxxlx2/ChatGPT_mission_record.git',
                  'refs/heads/main', 'refs/pull/39/head'])
    pins = dict(line.split()[::-1] for line in remote.splitlines())
    require(pins.get('refs/pull/39/head') == PR39, 'REMOTE_PR39_HEAD_DRIFT_REVIEW_REQUIRED')
    repo = Path(run(['git', '-C', str(root), 'rev-parse', '--show-toplevel']))
    run(['git', '-C', str(repo), 'fetch', '-q', 'origin', '+refs/heads/main:refs/remotes/origin/main'])
    require(run(['git', '-C', str(repo), 'rev-parse', 'refs/remotes/origin/main']) == pins.get('refs/heads/main'),
            'REMOTE_MAIN_MOVED_DURING_CHECK')
    merged = run(['git', '-C', str(repo), 'merge-tree', '--write-tree', 'refs/remotes/origin/main', PR39]).splitlines()[0]
    changed = run(['git', '-C', str(repo), 'diff', '--name-only', 'refs/remotes/origin/main', merged]).splitlines()
    require(all(p.startswith(PREFIX) or p.startswith('crypto-300-profit-mission/meme/FRANK_PR39_')
                or p == '.github/workflows/frank-presentation-semantics-tests-20261012.yml'
                for p in changed), 'OTHER_MISSION_MERGE_DIFF')
    return source_manifest(root)


def field(text, name):
    matches = re.findall('^' + re.escape(name) + r'="([^"\n]+)"\s*$', text, re.M)
    require(len(matches) == 1 and Path(matches[0]).is_absolute(), 'RUNNER_FIELD_' + name)
    require(not any(c in matches[0] for c in '$`\\'), 'RUNNER_DYNAMIC_FIELD')
    return Path(matches[0]).resolve()


def replace_source(text, root):
    old = field(text, 'LOCAL_AGENT')
    require(not any(c in str(root) for c in '$`"\\\n'), 'UNSAFE_RELEASE_PATH')
    result = text.replace('LOCAL_AGENT="' + str(old) + '"', 'LOCAL_AGENT="' + str(root) + '"')
    require(result != text, 'ALREADY_DEPLOYED_OR_UNRESOLVED')
    if 'MISSION_EVIDENCE_EXPORT_ENABLED' in result:
        require('export MISSION_EVIDENCE_EXPORT_ENABLED=0' in result, 'UNREVIEWED_EXPORT_CONFIG')
    else:
        require(result.count('exec env PYTHONPATH=.') == 1, 'RUNNER_EXEC_LAYOUT')
        result = result.replace('exec env PYTHONPATH=.',
                                'export MISSION_EVIDENCE_EXPORT_ENABLED=0\nexec env PYTHONPATH=.', 1)
    run(['/bin/bash', '-n'], input=result)
    return result


def disk_gate(directory, databases):
    required = 512 * 1024 * 1024 + 3 * sum(Path(p).stat().st_size +
        (Path(str(p) + '-wal').stat().st_size if Path(str(p) + '-wal').exists() else 0)
        for p in databases)
    require(shutil.disk_usage(directory).free >= required, 'DISK_SPACE')
    return required


def backup(src, dest, deadline=30):
    started = time.monotonic()
    def progress(status, remaining, total):
        require(time.monotonic() - started < deadline, 'BACKUP_LOCK_OR_TIMEOUT')
    fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    with closing(ro(src)) as read, closing(sqlite3.connect(dest)) as write:
        read.backup(write, pages=128, progress=progress, sleep=0.05)
        integrity(write)


def migrate(path):
    """Only approved additive DDL, with no business updates or history recreation."""
    with closing(sqlite3.connect(path, isolation_level=None, timeout=2)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('BEGIN IMMEDIATE')
        try:
            db.execute(DDL)
            require([r[1:4] for r in db.execute('PRAGMA table_info(local_delivery_presentation)')]
                    == [('decision_id', 'TEXT', 0), ('title', 'TEXT', 1),
                        ('summary', 'TEXT', 1), ('content_hash', 'TEXT', 1)], 'PRESENTATION_SCHEMA')
            fk = db.execute('PRAGMA foreign_key_list(local_delivery_presentation)').fetchall()
            require(len(fk) == 1 and fk[0][2:5] == ('local_delivery', 'decision_id', 'decision_id'),
                    'PRESENTATION_FOREIGN_KEY')
            integrity(db)
            db.execute('COMMIT')
        except BaseException:
            db.execute('ROLLBACK')
            raise


def atomic(path, data, mode=0o700):
    fd, tmp = tempfile.mkstemp(prefix='.pr39-', dir=Path(path).parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            os.fchmod(out.fileno(), mode)
            out.write(data); out.flush(); os.fsync(out.fileno())
        os.replace(tmp, path)
        directory = os.open(Path(path).parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def fresh(path, *, since=0, policy=None):
    body = json.loads(Path(path).read_text())
    stamp = datetime.fromisoformat(body['updated_at'].replace('Z', '+00:00')).timestamp()
    require(since < stamp <= time.time() and time.time() - stamp < 120, 'HEARTBEAT_STALE')
    require(body.get('status') == 'OK', 'HEARTBEAT_STATUS')
    if policy:
        require(body.get('policy_hash') == policy and body.get('delivery_allowed') is True,
                'HEARTBEAT_POLICY')
    return body


def interpreter_matches(venv, command):
    # macOS framework Python uses a launcher: ps shows Python.app rather than
    # the venv symlink. Probe that same configured interpreter without site code.
    expected = venv / 'bin/python'
    tokens = shlex.split(command)
    require(tokens and Path(tokens[0]).is_absolute(), 'INTERPRETER_COMMAND')
    if Path(tokens[0]).samefile(expected): return True
    probe = run([str(expected), '-I', '-B', '-S', '-c',
                 'import os,subprocess,json; print(json.dumps({'
                 '"command":subprocess.check_output(["/bin/ps","-p",str(os.getpid()),'
                 '"-o","command="],text=True)}))'])
    actual = shlex.split(json.loads(probe)['command'])[0]
    return Path(tokens[0]).samefile(actual)


class Mac:
    def __init__(self, home=Path.home()):
        self.home = home
        self.support = home / 'Library/Application Support/FrankMeme'
        self.runners = {'loop': self.support / 'mission-loop.sh',
                        'dashboard': self.support / 'dashboard.sh'}
        self.labels = {k: f'gui/{os.getuid()}/com.{getpass.getuser()}.frank-meme.{k}'
                       for k in self.runners}

    def launch(self, label):
        text = run(['/bin/launchctl', 'print', label])
        pid = re.search(r'^\s*pid = (\d+)\s*$', text, re.M)
        require(pid is not None, 'LAUNCH_PID')
        return int(pid[1]), text

    def alive(self, pid):
        try: os.kill(pid, 0)
        except ProcessLookupError: return False
        state = run(['/bin/ps', '-p', str(pid), '-o', 'stat='])
        return not state.startswith('Z')

    def runtime(self, key, text):
        runner = self.runners[key]
        require(runner.is_file() and not runner.is_symlink(), 'RUNNER_FILE')
        pid, loaded = self.launch(self.labels[key])
        require(str(runner) in loaded, 'LOADED_RUNNER_POINTER')
        plist = self.home / 'Library/LaunchAgents' / (self.labels[key].split('/')[-1] + '.plist')
        data = plistlib.loads(plist.read_bytes())
        require(data['Label'] == self.labels[key].split('/')[-1] and
                data['ProgramArguments'] == [str(runner)] and data.get('KeepAlive') is True,
                'PLIST_POINTER_OR_LIFECYCLE')
        require(not data.get('EnvironmentVariables'), 'UNREVIEWED_LAUNCH_ENV')
        agent = field(text, 'LOCAL_AGENT')
        cmd = run(['/bin/ps', '-p', str(pid), '-o', 'command='])
        require('scripts/mission_meme_v1.py ' + ('loop' if key == 'loop' else 'serve') in cmd,
                'RUNTIME_COMMAND')
        require(interpreter_matches(field(text, 'VENV'), cmd), 'RUNTIME_INTERPRETER')
        cwd = run(['/usr/sbin/lsof', '-a', '-p', str(pid), '-d', 'cwd', '-Fn'])
        require('n' + str(agent) in cwd.splitlines(), 'RUNTIME_CWD')
        start = run(['/bin/ps', '-p', str(pid), '-o', 'lstart='], env={**os.environ, 'LC_ALL': 'C'})
        started = time.mktime(time.strptime(start, '%a %b %d %H:%M:%S %Y'))
        if sys.platform == 'darwin':
            try:
                started = darwin_precise_process_start(pid, started)
            except RuntimeError as exc:
                # If precise evidence is unavailable, retain the existing
                # *stricter* whole-second rule; never infer an earlier runner.
                require(str(exc) == 'KERNEL_PROCESS_BIRTH_UNAVAILABLE',
                        'KERNEL_PROCESS_BIRTH_UNVERIFIED')
        manifest = source_manifest(agent)
        require(all((agent / p).stat().st_mtime < started for p in manifest),
                'SOURCE_MODIFIED_SINCE_PROCESS_START')
        delta = runner.stat().st_mtime - started
        require(not 0 <= delta < 1, 'RUNNER_START_SECOND_AMBIGUOUS')
        require(delta < 0, 'RUNNER_MODIFIED_SINCE_PROCESS_START')
        return {'pid': pid, 'agent': str(agent), 'source': manifest, 'plist': str(plist),
                'plist_hash': sha(plist), 'runner_hash': sha(runner), 'started': started}

    def hold(self, key):
        run(['/bin/launchctl', 'disable', self.labels[key]])

    def release_hold(self, key):
        run(['/bin/launchctl', 'enable', self.labels[key]])

    def stop(self, key):
        # Verify absence independently after bootout; do not swallow bootout failure.
        run(['/bin/launchctl', 'bootout', self.labels[key]], timeout=30)

    def start(self, key, plist):
        self.release_hold(key)
        run(['/bin/launchctl', 'bootstrap', f'gui/{os.getuid()}', plist], timeout=30)

    def absent(self, key):
        proc = subprocess.run(['/bin/launchctl', 'print', self.labels[key]],
                              capture_output=True, timeout=10)
        require(proc.returncode != 0 and b'Could not find service' in proc.stderr,
                'AGENT_ABSENCE_UNVERIFIED')

    def worker_pids(self, context):
        # launchd absence alone is not process-exit evidence (including SIGKILL recovery).
        text = run(['/bin/ps', '-axo', 'pid=,command='])
        roots = {context['new_agent']} | {v['agent'] for v in context['runtime'].values()}
        pids = []
        for line in text.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) != 2 or not any('scripts/mission_meme_v1.py ' + mode in parts[1]
                                         for mode in ('loop', 'serve')):
                continue
            pid = int(parts[0])
            try:
                cwd = run(['/usr/sbin/lsof', '-a', '-p', str(pid), '-d', 'cwd', '-Fn'])
            except subprocess.CalledProcessError:
                require(not self.alive(pid), 'WORKER_IDENTITY_UNVERIFIED')
                continue
            if any('n' + root in cwd.splitlines() for root in roots): pids.append(pid)
        return pids

    def wait_dead(self, pids):
        for _ in range(30):
            if not any(self.alive(p) for p in pids): return
            time.sleep(1)
        raise RuntimeError('OLD_PROCESSES_STILL_ALIVE')


def scanner_inventory(mac, label, prod):
    require(label.startswith('gui/' + str(os.getuid()) + '/') and
            label not in mac.labels.values(), 'SCANNER_LABEL')
    pid, loaded = mac.launch(label)
    cmd = run(['/bin/ps', '-p', str(pid), '-o', 'command='])
    tokens = shlex.split(cmd)
    module = any(tokens[i:i+2] == ['-m', 'scripts.frank_local_signal_service']
                 for i in range(len(tokens)))
    script = any(Path(t).name == 'frank_local_signal_service.py' for t in tokens)
    require(module or script, 'SCANNER_COMMAND')
    cwd = run(['/usr/sbin/lsof', '-a', '-p', str(pid), '-d', 'cwd', '-Fn'])
    roots = [Path(x[1:]) for x in cwd.splitlines() if x.startswith('n')]
    require(len(roots) == 1, 'SCANNER_CWD')
    entry = roots[0] / 'scripts/frank_local_signal_service.py'
    files = sorted((roots[0] / 'mission_agent/signals').glob('*.py')) + [entry,
        roots[0] / 'mission_agent/frank/parser.py', roots[0] / 'mission_agent/frank/rpc.py']
    digest = hashlib.sha256()
    for file in files:
        digest.update(file.name.encode()); digest.update(file.read_bytes())
    relevant = sorted((roots[0] / 'mission_agent/signals').glob('*.py')) + sorted(
        (roots[0] / 'mission_agent/frank').glob('*.py')) + [entry, roots[0] / 'mission_agent/hashing.py']
    source = {p.relative_to(roots[0]).as_posix(): sha(p) for p in relevant}
    body = json.loads((Path(prod).parent / 'health.json').read_text())
    start = datetime.fromisoformat(body['started_at'].replace('Z', '+00:00')).timestamp()
    require(all(p.stat().st_mtime < start for p in relevant), 'SCANNER_SOURCE_AFTER_START')
    require(body.get('pid') == pid and body.get('loaded_source_sha256') == digest.hexdigest(),
            'SCANNER_ACTUAL_LOADED_VERSION')
    tokens = shlex.split(cmd)
    protected = {}
    for flag in ('--policy', '--registry'):
        require(tokens.count(flag) == 1, 'SCANNER_CONFIG_ARG')
        config = Path(tokens[tokens.index(flag) + 1])
        require(config.is_absolute(), 'SCANNER_CONFIG_PATH')
        protected[str(config)] = sha(config)
    require(tokens.count('--root') == 1 and
            Path(tokens[tokens.index('--root') + 1]).resolve() == Path(prod).parent,
            'SCANNER_PRODUCTION_ROOT')
    return {'pid': pid, 'loaded_hash': hashlib.sha256(loaded.encode()).hexdigest(),
            'root': str(roots[0]), 'source': source, 'entry_hash': sha(entry),
            'loaded_source_sha256': digest.hexdigest(), 'policy_hash': body['policy_hash'],
            'protected': protected}


def scanner_check(mac, context):
    pid, _ = mac.launch(context['scanner_label'])
    require(pid == context['scanner']['pid'], 'SCANNER_PID_CHANGED')
    require(sha(Path(context['scanner']['root']) / 'scripts/frank_local_signal_service.py') ==
            context['scanner']['entry_hash'], 'SCANNER_ENTRY_CHANGED')
    require(all(sha(Path(context['scanner']['root']) / p) == h
                for p,h in context['scanner']['source'].items()), 'SCANNER_SOURCE_CHANGED')
    with closing(ro(context['prod_db'])) as db:
        rows = [dict(r) for r in db.execute('SELECT * FROM cursors')]
    prior = {r['wallet']: r for r in context['cursors']}
    require(set(r['wallet'] for r in rows) == set(prior), 'CURSOR_WALLET_CHANGED')
    for row in rows:
        if row['wallet'] in prior:
            old = prior[row['wallet']]
            require(type(row['slot']) is int and row['slot'] >= old['slot'], 'CURSOR_REGRESSION')
            if row['slot'] == old['slot']:
                require(row['signature'] == old['signature'], 'CURSOR_IDENTITY_CHANGED')
    body = json.loads((Path(context['prod_db']).parent / 'health.json').read_text())
    require(0 <= time.time() - datetime.fromisoformat(body['last_successful_poll'].replace('Z', '+00:00')).timestamp()
            < 120 and body.get('status') == 'RUNNING' and body.get('pid') == pid
            and body.get('source_drift') is False and body.get('production_trading') == 'NO_GO',
            'SCANNER_HEARTBEAT')
    require(body.get('loaded_source_sha256') == context['scanner']['loaded_source_sha256'],
            'SCANNER_LOADED_SOURCE_CHANGED')
    require(body.get('policy_hash') == context['scanner']['policy_hash'], 'SCANNER_POLICY_CHANGED')


def protected_check(context):
    require(all(sha(p) == h for p, h in context['protected'].items()), 'PROTECTED_FILE_CHANGED')


def http_check(context, target=False):
    base = 'http://127.0.0.1:' + str(context['port'])
    for endpoint in ('/', '/api/control-health'):
        with urllib.request.urlopen(base + endpoint, timeout=5) as response:
            body = response.read(2_000_000)
            require(response.status == 200, 'DASHBOARD_HTTP')
        if endpoint == '/':
            agent = Path(context['new_agent'] if target else context['runtime']['dashboard']['agent'])
            require(body == (agent / 'mission_agent/mission_control/static/index.html').read_bytes(),
                    'DASHBOARD_HTML_VERSION')
        else:
            health = json.loads(body)
            require(health.get('manual_review_breakdown_available') is True, 'API_DB_READBACK')
    if target:
        with urllib.request.urlopen(base + '/static/app.js', timeout=5) as response:
            require(response.read() == (Path(context['new_agent']) /
                    'mission_agent/mission_control/static/app.js').read_bytes(), 'DASHBOARD_JS_VERSION')


def prepare(mac, root, expected, scanner_label):
    source = candidate(root, expected)
    texts = {k: p.read_text() for k, p in mac.runners.items()}
    runtime = {k: mac.runtime(k, v) for k, v in texts.items()}
    loop = texts['loop']
    fields = {k: field(loop, k) for k in
              ('PROD', 'CONTROL_POINTER', 'POLICY', 'APPROVED_HASH_FILE', 'RPC_FILE', 'VENV')}
    for key in ('PROD', 'CONTROL_POINTER', 'VENV', 'RPC_FILE'):
        require(field(texts['dashboard'], key) == fields[key], 'DASH_LOOP_CONFIG_DISAGREEMENT')
    control = Path(fields['CONTROL_POINTER'].read_text().strip()).resolve()
    db, prod = control / 'mission-control.sqlite', fields['PROD'] / 'forward.sqlite'
    require(db.resolve() != prod.resolve(), 'DB_BOUNDARY')
    for key in runtime:
        delta = {p for p in source.keys() | runtime[key]['source'].keys()
                 if source.get(p) != runtime[key]['source'].get(p)}
        require(delta <= ALLOWED, 'UNREVIEWED_BASELINE_DELTA')
    policy = sha(fields['POLICY'])
    require(fields['APPROVED_HASH_FILE'].read_text().strip() == policy, 'POLICY_EXTERNAL_PIN')
    require(sha(root / 'config/follow_policy_v1.approved.json') == policy, 'APPROVED_POLICY_BYTES')
    policy_body = json.loads(fields['POLICY'].read_text())
    require(policy_body.get('status') == 'FROZEN_APPROVED' and
            policy_body.get('live_delivery_approved') is True, 'POLICY_AUTHORITY')
    state = ledger(db)
    reasons = review_reasons(state)
    fresh(control / 'mission-control-health.json', policy=policy)
    with closing(ro(prod)) as conn:
        integrity(conn)
        cursors = [dict(r) for r in conn.execute('SELECT * FROM cursors')]
    require(cursors and all(type(r['slot']) is int for r in cursors), 'CURSOR_UNVERIFIED')
    protected = {str(p): sha(p) for p in fields.values() if p.is_file()}
    for item in runtime.values(): protected[item['plist']] = item['plist_hash']
    scanner = scanner_inventory(mac, scanner_label, prod)
    protected.update(scanner['protected'])
    from frank_pr39_predeploy_readonly import frank_payment_coverage
    coverage = frank_payment_coverage(prod)
    require(coverage['indexed_states'] > 0 and coverage['latest_buy_predicate_missing'] == 0,
            'FRANK_BUY_COVERAGE')
    for p in (mac.home / 'Library/LaunchAgents').glob('*.plist'):
        if scanner_label.split('/')[-1] == p.stem: protected[str(p)] = sha(p)
    context = {'runtime': runtime, 'old_texts': texts, 'protected': protected,
               'new_agent': str(root), 'new_source': source, 'db': str(db), 'prod_db': str(prod),
               'control': str(control), 'policy': policy, 'before': state,
               'scanner': scanner, 'scanner_label': scanner_label, 'cursors': cursors,
               'port': int((control / 'dashboard.port').read_text()),
               'expected': expected, 'reasons': reasons, 'frank_amount_coverage': coverage}
    require(1 <= context['port'] <= 65535, 'DASHBOARD_PORT')
    disk_gate(mac.support, (db, prod))
    scanner_check(mac, context); http_check(context)
    context['new_texts'] = {k: replace_source(v, root) for k, v in texts.items()}
    return context


def save_journal(path, context, phase):
    context['phase'] = phase
    atomic(path, json.dumps(context, sort_keys=True).encode(), 0o600)


def rollback(mac, context, journal):
    """Stop writers FIRST. Restore code pointers; never copy any database backup."""
    for key in ('loop', 'dashboard'): mac.hold(key)
    pids = set(v['pid'] for v in context['runtime'].values())
    pids.update(mac.worker_pids(context))
    for key in ('loop', 'dashboard'):
        try:
            pid, _ = mac.launch(mac.labels[key])
        except subprocess.CalledProcessError:
            continue
        pids.add(pid)
        mac.stop(key)
    mac.wait_dead(pids)
    require(not mac.worker_pids(context), 'LINGERING_WORKERS_RECOVERY_BLOCKED')
    for key in ('loop', 'dashboard'): mac.absent(key)
    protected_check(context); scanner_check(mac, context)
    for key, text in context['old_texts'].items():
        current = mac.runners[key].read_text()
        require(current in (text, context['new_texts'][key]), 'RUNNER_EXTERNAL_CHANGE')
        require(source_manifest(Path(context['runtime'][key]['agent'])) ==
                context['runtime'][key]['source'], 'OLD_SOURCE_DRIFT')
        atomic(mac.runners[key], text.encode())
    save_journal(journal, context, 'CODE_ROLLED_BACK_SERVICES_STOPPED')
    # Any new decision/delivery after cutover or uncertain receipt prohibits old loop restart.
    assert_preserved(context['before'], ledger(context['db']), exact=True)
    since = time.time()
    try:
        for key in ('dashboard', 'loop'):
            mac.start(key, context['runtime'][key]['plist'])
        wait_ready(lambda: fresh(Path(context['control']) / 'mission-control-health.json',
                                 since=since, policy=context['policy']), 180)
        http_check(context)
        for key in ('loop', 'dashboard'):
            actual = mac.runtime(key, context['old_texts'][key])
            require(actual['source'] == context['runtime'][key]['source'], 'ROLLBACK_RUNTIME_SOURCE')
        scanner_check(mac, context); protected_check(context)
        assert_preserved(context['before'], ledger(context['db']), exact=True)
        save_journal(journal, context, 'ROLLED_BACK')
    except BaseException:
        for key in ('loop', 'dashboard'): mac.hold(key)
        for key in ('loop', 'dashboard'):
            try:
                pid, _ = mac.launch(mac.labels[key])
            except subprocess.CalledProcessError:
                continue
            mac.stop(key); mac.wait_dead([pid])
        raise


def apply(mac, context, journal):
    save_journal(journal, context, 'PREPARED')
    mutated = False
    try:
        for key in ('loop', 'dashboard'):
            require(mac.runtime(key, context['old_texts'][key]) == context['runtime'][key],
                    'RUNTIME_CHANGED_AFTER_PREPARE')
        protected_check(context)
        disk_gate(journal.parent, (context['db'], context['prod_db']))
        for key in ('db', 'prod_db'):
            backup(context[key], journal.parent / (key + '.prestop.sqlite'))
        for index, path in enumerate(context['protected']):
            dest = journal.parent / ('protected-' + str(index))
            atomic(dest, Path(path).read_bytes(), 0o600)
        for key in context['runtime']:
            saved = journal.parent / ('source-' + key)
            saved.mkdir(mode=0o700)
            for relative in context['runtime'][key]['source']:
                dest = saved / relative
                dest.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                atomic(dest, (Path(context['runtime'][key]['agent']) / relative).read_bytes(), 0o600)
        save_journal(journal, context, 'PRESTOP_BACKED_UP')
        save_journal(journal, context, 'QUIESCING')
        mutated = True
        for key in ('loop', 'dashboard'): mac.hold(key)
        mac.stop('loop'); mac.stop('dashboard')
        mac.wait_dead([v['pid'] for v in context['runtime'].values()])
        for key in ('loop', 'dashboard'): mac.absent(key)
        save_journal(journal, context, 'STOPPED')
        # Fresh queue and immutable capture after last old writer has exited.
        context['before'] = ledger(context['db'])
        disk_gate(journal.parent, (context['db'], context['prod_db']))
        for key in ('db', 'prod_db'):
            backup(context[key], journal.parent / (key + '.sqlite'))
        save_journal(journal, context, 'BACKED_UP')
        migrate(context['db'])
        assert_preserved(context['before'], ledger(context['db']), exact=True)
        for key, text in context['new_texts'].items():
            atomic(mac.runners[key], text.encode())
        save_journal(journal, context, 'SWITCHED')
        require(source_manifest(Path(context['new_agent'])) == context['new_source'], 'TARGET_SOURCE_DRIFT')
        protected_check(context); scanner_check(mac, context)
        mac.start('dashboard', context['runtime']['dashboard']['plist'])
        wait_ready(lambda: http_check(context, True), 30)
        mac.runtime('dashboard', context['new_texts']['dashboard'])
        since = time.time()
        mac.start('loop', context['runtime']['loop']['plist'])
        wait_ready(lambda: fresh(Path(context['control']) / 'mission-control-health.json',
                                 since=since, policy=context['policy']), 180)
        for key in ('loop', 'dashboard'):
            actual = mac.runtime(key, context['new_texts'][key])
            require(actual['source'] == context['new_source'] and
                    actual['pid'] != context['runtime'][key]['pid'], 'NEW_RUNTIME_VERSION')
        assert_preserved(context['before'], ledger(context['db']))
        protected_check(context); scanner_check(mac, context); http_check(context, True)
        save_journal(journal, context, 'SUCCESS')
    except BaseException:
        if not mutated:
            save_journal(journal, context, 'ABORTED_NO_MUTATION')
            raise
        try: rollback(mac, context, journal)
        except BaseException:
            # Durable original context survives. No stale DB restoration or blind restart.
            save_journal(journal, context, 'BLOCKED_RECOVERY_REQUIRED')
        raise


def wait_ready(check, seconds):
    until = time.monotonic() + seconds
    while True:
        try: return check()
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
            require(time.monotonic() < until, 'POSTCHECK_TIMEOUT')
            print('WAITING_FOR_VERIFIED_SERVICE_HEALTH', flush=True)
            time.sleep(5)


def collect_evidence(mac, root, expected, scanner_label):
    report = {'audit': 'PR39_MAC_RELEASE_READ_ONLY', 'mutated_production': False,
              'sent_gmail': False, 'restarted_services': False, 'checks': {}}
    def probe(name, fn):
        try:
            value = fn()
            report['checks'][name] = {'status': 'PASS', 'result': value}
        except Exception as exc:
            code = str(exc) if isinstance(exc, RuntimeError) and re.fullmatch('[A-Z_]+', str(exc)) else type(exc).__name__
            report['checks'][name] = {'status': 'UNVERIFIED', 'reason': code}
    def manual():
        pointer = mac.home / '.frank_meme_control_root'
        db = Path(pointer.read_text().strip()) / 'mission-control.sqlite'
        # Reasons can be collected even if the complete queue gate is blocked.
        with closing(ro(db)) as conn:
            state = {'gmail_delivery': [dict(r) for r in conn.execute('SELECT * FROM gmail_delivery')]}
        return review_reasons(state)
    probe('manual_review_reasons', manual)
    # Collect diagnostic facts separately: a legacy production tree may have
    # explicitly reviewed on-disk overlays. Never silently accept such drift.
    for key in mac.runners:
        def source_detail(key=key):
            runner_text = mac.runners[key].read_text(encoding='utf-8')
            return source_drift_diagnostic(field(runner_text, 'LOCAL_AGENT'))
        probe(key + '_source_drift_diagnostic', source_detail)
        def timing_detail(key=key):
            return runner_start_time_diagnostic(mac, key,
                                                mac.runners[key].read_text(encoding='utf-8'))
        probe(key + '_start_time_diagnostic', timing_detail)
        probe(key + '_source_mtime_diagnostic',
              lambda key=key: source_start_temporal_diagnostic(mac, key))
    def db_facts():
        text = mac.runners['loop'].read_text()
        pointer = field(text, 'CONTROL_POINTER')
        control = Path(pointer.read_text().strip())
        prod = field(text, 'PROD') / 'forward.sqlite'
        state = ledger(control / 'mission-control.sqlite')
        from frank_pr39_predeploy_readonly import frank_payment_coverage
        scan = scanner_inventory(mac, scanner_label, prod)
        return {'queue_records': {k: len(v) for k,v in state.items()},
                'frank_amount_coverage': frank_payment_coverage(prod),
                'scanner_pid': scan['pid'], 'scanner_loaded_source_sha256': scan['loaded_source_sha256']}
    probe('databases_and_scanner', db_facts)
    for key in mac.runners:
        def runtime_fact(key=key):
            state = mac.runtime(key, mac.runners[key].read_text())
            return {'pid': state['pid'], 'source_manifest_sha256': hashlib.sha256(
                json.dumps(state['source'], sort_keys=True).encode()).hexdigest(),
                'actual_disk_source_matches_git': True, 'source_predates_process': True,
                'runner_sha256': state['runner_hash']}
        probe(key + '_actual_runtime', runtime_fact)
    def full():
        c = prepare(mac, root, expected, scanner_label)
        return {'scanner_pid': c['scanner']['pid'], 'scanner_loaded_source_sha256':
                c['scanner']['loaded_source_sha256'], 'policy_sha256': c['policy'],
                'cursor_rows': len(c['cursors']), 'frank_amount_coverage': c['frank_amount_coverage'],
                'queue_records': {t: len(v) for t, v in c['before'].items()},
                'manual_review': c['reasons']}
    probe('complete_release_preflight', full)
    report['gate'] = ('PASS_READ_ONLY_RELEASE_INVENTORY' if all(
        v['status'] == 'PASS' for v in report['checks'].values()) else 'UNVERIFIED_RELEASE_BLOCKED')
    return report


def interrupted(signum, frame):
    raise KeyboardInterrupt('RELEASE_INTERRUPTED')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--expected-release-sha', required=True)
    p.add_argument('--scanner-label', default=f'gui/{os.getuid()}/com.jerson.crypto-monitor-frank-local')
    p.add_argument('--collect-evidence', action='store_true', help='Aggregate partial read-only Mac facts, even if a gate fails')
    p.add_argument('--apply', action='store_true')
    p.add_argument('--authorize-production-restart', action='store_true')
    p.add_argument('--authorize-future-real-notifications', action='store_true')
    p.add_argument('--recover', type=Path, help='Private journal from an interrupted release')
    args = p.parse_args(argv)
    require(sys.platform == 'darwin', 'ACTUAL_MAC_REQUIRED')
    require(not args.apply or (args.authorize_production_restart and
            args.authorize_future_real_notifications), 'EXPLICIT_AUTHORIZATION_REQUIRED')
    require(not args.recover or args.apply, 'RECOVERY_AUTHORIZATION_REQUIRED')
    root = Path(__file__).resolve().parents[1]
    mac = Mac()
    require(not args.collect_evidence or not args.apply, 'COLLECTION_MUST_BE_READ_ONLY')
    if args.collect_evidence:
        print(json.dumps(collect_evidence(mac, root, args.expected_release_sha, args.scanner_label),
                         sort_keys=True))
        return 0
    if not args.apply:
        context = prepare(mac, root, args.expected_release_sha, args.scanner_label)
        print(json.dumps({'gate': 'PASS_READ_ONLY_RELEASE_INVENTORY',
                          'manual_review': context['reasons'],
                          'runtime_verified_by': ['loaded_runner', 'process_command', 'process_cwd',
                                                  'source_blobs', 'source_before_process_start'],
                          'mutated_production': False, 'deployment_authorized': False}))
        return 0
    # Lock/journal exist only under explicit apply; dry-run has no filesystem writes.
    release_dir = mac.support / 'pr39-releases'
    release_dir.mkdir(mode=0o700, exist_ok=True)
    with (release_dir / 'release.lock').open('a+b') as lock:
        os.chmod(lock.name, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        unfinished = [f for f in release_dir.glob('*/journal.json')
                      if json.loads(f.read_text())['phase'] not in {'SUCCESS', 'ROLLED_BACK', 'ABORTED_NO_MUTATION'}]
        if args.recover:
            require(args.recover.resolve() in [f.resolve() for f in unfinished], 'RECOVERY_JOURNAL')
            context = json.loads(args.recover.read_text())
            require(context['expected'] == args.expected_release_sha and
                    context['scanner_label'] == args.scanner_label, 'RECOVERY_IDENTITY')
            rollback(mac, context, args.recover)
            print('RECOVERY_CODE_ROLLBACK_COMPLETE_DATABASE_PRESERVED')
            return 0
        require(not unfinished, 'UNFINISHED_RELEASE_RECOVERY_REQUIRED')
        context = prepare(mac, root, args.expected_release_sha, args.scanner_label)
        require(context['reasons']['requires_private_review'] == 0 and
                'UNVERIFIED_OTHER_REASON' not in context['reasons']['reason_counts'],
                'MANUAL_REVIEW_REASONS_REQUIRE_ACCEPTANCE')
        staged = stage_immutable_release(mac, root, args.expected_release_sha, context['new_source'])
        context['new_agent'] = str(staged)
        context['new_texts'] = {k: replace_source(v, staged) for k, v in context['old_texts'].items()}
        location = release_dir / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + str(os.getpid()))
        location.mkdir(mode=0o700)
        for sig in (signal.SIGTERM, signal.SIGINT): signal.signal(sig, interrupted)
        apply(mac, context, location / 'journal.json')
        print('RELEASE_SUCCESS_BOTH_RUNTIME_VERSIONS_VERIFIED_DATABASE_PRESERVED')
    return 0


if __name__ == '__main__':
    try: sys.exit(main())
    except BaseException as exc:
        if isinstance(exc, SystemExit): raise
        safe = str(exc) if isinstance(exc, RuntimeError) and re.fullmatch('[A-Z_]+', str(exc)) else type(exc).__name__
        print(json.dumps({'gate': 'BLOCKED', 'reason': safe, 'production_trading': 'NO_GO'}))
        sys.exit(3)
