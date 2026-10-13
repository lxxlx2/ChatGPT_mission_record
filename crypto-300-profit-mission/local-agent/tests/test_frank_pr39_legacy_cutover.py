"""Legacy Loop controlled cutover: isolated, deterministic, fail-stopped.

Real: git archive/hash, SQLite (WAL, ledger invariants, backup API, migration), runner
rewriting, plist parsing, release marker verification, the journal and all phases.
Fake: launchd/process table, process identity, HTTP, scanner snapshot, wait loops.
No production path, no Gmail provider, no real service is touched.
"""
import importlib.util
import json
import os
import plistlib
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('frank_pr39_controlled_release', ROOT / 'scripts/frank_pr39_controlled_release.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
from mission_agent.mission_control.db import ControlDB, utc
from mission_agent.mission_control.delivery import GmailDelivery, LocalDelivery
from mission_agent.hashing import digest

USER = 'tester'
POLICY_TEXT = json.dumps({'status': 'FROZEN_APPROVED', 'live_delivery_approved': True, 'policy_id': 'P1'}, sort_keys=True) + '\n'
OPS_FILES = {
    'mission_agent/__init__.py': '',
    'mission_agent/mission_control/__init__.py': '',
    'mission_agent/mission_control/server.py': 'SERVER = "ops-release"\n',
    'mission_agent/mission_control/static/index.html': '<html>ops</html>\n',
    'mission_agent/mission_control/static/app.js': 'const UI="ops-release";\n',
    'config/follow_policy_v1.approved.json': POLICY_TEXT,
    'scripts/mission_meme_v1.py': "print('mission')\n",
}
LEGACY_HEAD_FILES = {
    'mission_agent/__init__.py': '',
    'mission_agent/mission_control/__init__.py': '',
    'mission_agent/mission_control/server.py': 'SERVER = "legacy-head"\n',
    'mission_agent/mission_control/static/index.html': '<html>legacy</html>\n',
    'mission_agent/mission_control/static/app.js': 'const UI="legacy-head";\n',
    'config/follow_policy_v1.approved.json': POLICY_TEXT,
    'scripts/mission_meme_v1.py': "print('mission')\n",
}
LEGACY_DISK = {
    'mission_agent/mission_control/server.py': 'SERVER = "legacy-disk"\n',
    'mission_agent/mission_control/static/app.js': 'const UI="legacy-disk";\n',
}
LEGACY_EXTRA = {'mission_agent/mission_control/delivery_review.py': 'REVIEW = "legacy-extra"\n'}


def git_env():
    return {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@x',
            'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@x'}


def make_repo(path, files):
    path.mkdir(parents=True)
    for rel, text in files.items():
        target = path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
    subprocess.run(['git', 'init', '-q', str(path)], check=True)
    subprocess.run(['git', '-C', str(path), 'add', '-A'], check=True)
    subprocess.run(['git', '-C', str(path), 'commit', '-q', '-m', 'fixture'], check=True, env=git_env())
    return subprocess.run(['git', '-C', str(path), 'rev-parse', 'HEAD'], capture_output=True, text=True,
                          check=True).stdout.strip()


def head_blob(repo, rel):
    return subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD:' + rel], capture_output=True,
                          text=True, check=True).stdout.strip()


def blob_of(path):
    return subprocess.run(['git', 'hash-object', str(path)], capture_output=True, text=True,
                          check=True).stdout.strip()


def loop_runner_text(local, prod, venv, pointer, policy, approved, rpc):
    return f'''#!/bin/bash
set -euo pipefail
LOCAL_AGENT="{local}"
PROD="{prod}"
VENV="{venv}"
CONTROL_POINTER="{pointer}"
POLICY="{policy}"
APPROVED_HASH_FILE="{approved}"
RPC_FILE="{rpc}"
export PATH="/usr/bin:/bin"
CONTROL="$(cat "$CONTROL_POINTER")"
APPROVED_HASH="$(cat "$APPROVED_HASH_FILE")"
SOLANA_RPC_URLS="$(cat "$RPC_FILE")"
export SOLANA_RPC_URLS
cd "$LOCAL_AGENT"
exec env PYTHONPATH=. "$VENV/bin/python" scripts/mission_meme_v1.py loop \\
  --production-root "$PROD" \\
  --control-root "$CONTROL" \\
  --policy "$POLICY" \\
  --live-delivery \\
  --approved-policy-sha256 "$APPROVED_HASH" \\
  --interval 5
'''


def dash_runner_text(local, prod, venv, pointer, rpc):
    return f'''#!/bin/bash
set -euo pipefail
LOCAL_AGENT="{local}"
PROD="{prod}"
VENV="{venv}"
CONTROL_POINTER="{pointer}"
PORT_FILE="{rpc}.port"
RPC_FILE="{rpc}"
export PATH="/usr/bin:/bin"
CONTROL="$(cat "$CONTROL_POINTER")"
PORT="$(cat "$PORT_FILE")"
SOLANA_RPC_URLS="$(cat "$RPC_FILE")"
export SOLANA_RPC_URLS
cd "$LOCAL_AGENT"
exec env PYTHONPATH=. "$VENV/bin/python" scripts/mission_meme_v1.py serve \\
  --production-root "$PROD" \\
  --control-root "$CONTROL" \\
  --host 127.0.0.1 \\
  --port "$PORT"
'''


class FakeLegacyMac:
    """launchd and process table. Mirrors the real Mac wrapper's contract."""

    def __init__(self, home, legacy_agent, dash_agent, venv):
        self.home = home
        self.support = home / 'Library/Application Support/FrankMeme'
        self.runners = {'loop': self.support / 'mission-loop.sh', 'dashboard': self.support / 'dashboard.sh'}
        self.labels = {k: f'gui/501/com.{USER}.frank-meme.{k}' for k in self.runners}
        self.legacy_agent = str(legacy_agent)
        self.dash_agent = str(dash_agent)
        self.venv = venv
        self.control = None
        self.procs = {}
        self.loaded = {}
        self.holds = set()
        self.events = []
        self.runtime_calls = []
        self.violations = []
        self.next_pid = 6000
        self.before_stop = None
        self.loop_heartbeats = True

    def plist_path(self, key):
        return self.home / 'Library/LaunchAgents' / (self.labels[key].split('/')[-1] + '.plist')

    def add_proc(self, pid, command, cwd, started, state='running'):
        self.procs[pid] = {'command': command, 'cwd': str(cwd), 'started': started, 'state': state}

    def launch(self, label):
        pid = self.loaded.get(label)
        if pid is None or self.procs[pid]['state'] == 'dead':
            raise subprocess.CalledProcessError(1, ['launchctl', 'print', label])
        key = 'loop' if label.endswith('.loop') else 'dashboard'
        return pid, f'pid = {pid}\n\tpath = {self.runners[key]}\n'

    def identity(self, pid):
        proc = self.procs.get(pid)
        if proc is None or proc['state'] == 'dead':
            raise subprocess.CalledProcessError(1, ['ps', '-p', str(pid)])
        return {'pid': pid, 'command': proc['command'], 'started': proc['started'], 'cwd': proc['cwd']}

    def signal_verified(self, pid, expected, signum):
        if self.identity(pid) != expected:
            raise RuntimeError('PROCESS_IDENTITY_CHANGED')
        self.events.append(('signal', pid, int(signum)))
        if signum == signal.SIGSTOP:
            self.procs[pid]['state'] = 'stopped'
        elif signum == signal.SIGCONT:
            self.procs[pid]['state'] = 'running'
        elif signum == signal.SIGKILL:
            self.procs[pid]['state'] = 'dead'

    def alive(self, pid):
        proc = self.procs.get(pid)
        return proc is not None and proc['state'] != 'dead'

    def hold(self, key):
        self.holds.add(key)
        self.events.append(('hold', key))

    def release_hold(self, key):
        self.holds.discard(key)
        self.events.append(('release_hold', key))

    def stop(self, key):
        if self.before_stop is not None:
            self.before_stop(key)
        self.events.append(('stop', key))
        label = self.labels[key]
        pid = self.loaded.get(label)
        self.loaded[label] = None
        # bootout kills a running process; a SIGSTOPped one survives until an explicit SIGKILL.
        if pid is not None and self.procs[pid]['state'] != 'stopped':
            self.procs[pid]['state'] = 'dead'

    def absent(self, key):
        if self.loaded.get(self.labels[key]) is not None:
            raise RuntimeError('AGENT_ABSENCE_UNVERIFIED')

    def wait_dead(self, pids):
        if any(self.alive(pid) for pid in pids):
            raise RuntimeError('OLD_PROCESSES_STILL_ALIVE')

    def worker_pids(self, context):
        roots = {context['new_agent']} | {v['agent'] for v in context['runtime'].values()}
        return [pid for pid, proc in self.procs.items() if proc['state'] != 'dead'
                and 'scripts/mission_meme_v1.py ' in proc['command'] and proc['cwd'] in roots]

    def start(self, key, plist):
        self.holds.discard(key)
        text = self.runners[key].read_text(encoding='utf-8')
        agent = r.field(text, 'LOCAL_AGENT')
        if key == 'loop' and str(agent) == self.legacy_agent:
            self.violations.append('LEGACY_LOOP_RESTART')
        pid = self.next_pid
        self.next_pid += 1
        mode = 'loop' if key == 'loop' else 'serve'
        self.add_proc(pid, f'{self.venv}/bin/python scripts/mission_meme_v1.py {mode} --live-delivery',
                      agent, time.time())
        self.loaded[self.labels[key]] = pid
        self.events.append(('start', key, r.sha(self.runners[key])))
        if key == 'loop' and self.loop_heartbeats:
            stamp = time.time()
            (self.control / 'mission-control-health.json').write_text(json.dumps(
                {'status': 'OK', 'updated_at': __import__('datetime').datetime.fromtimestamp(
                    stamp, __import__('datetime').timezone.utc).isoformat(),
                 'policy_hash': self.policy_hash, 'delivery_allowed': True}), encoding='utf-8')

    def runtime(self, key, text):
        self.runtime_calls.append(key)
        pid = self.loaded.get(self.labels[key])
        if pid is None:
            raise RuntimeError('LAUNCH_PID')
        agent = Path(r.field(text, 'LOCAL_AGENT'))
        plist = self.plist_path(key)
        return {'pid': pid, 'agent': str(agent), 'source': r.source_manifest(agent),
                'plist': str(plist), 'plist_hash': r.sha(plist), 'runner_hash': r.sha(self.runners[key]),
                'started': self.procs[pid]['started']}


def build_world(tmp_path, monkeypatch):
    world = SimpleNamespace(tmp=tmp_path)
    world.ops, world.sha = tmp_path / 'ops', make_repo(tmp_path / 'ops', OPS_FILES)
    world.legacy = tmp_path / 'legacy'
    make_repo(world.legacy, LEGACY_HEAD_FILES)
    for rel, text in LEGACY_DISK.items():
        (world.legacy / rel).write_text(text, encoding='utf-8')
    for rel, text in LEGACY_EXTRA.items():
        (world.legacy / rel).write_text(text, encoding='utf-8')
    monkeypatch.setattr(r, 'HISTORICAL_UI_LEGACY_BLOBS', {
        rel: (head_blob(world.legacy, rel), blob_of(world.legacy / rel)) for rel in LEGACY_DISK})
    monkeypatch.setattr(r, 'HISTORICAL_UI_LEGACY_EXTRA', {rel: blob_of(world.legacy / rel) for rel in LEGACY_EXTRA})
    world.dash = tmp_path / 'dash'
    world.dash_sha = make_repo(world.dash, LEGACY_HEAD_FILES)
    world.venv = tmp_path / 'venv'
    (world.venv / 'bin').mkdir(parents=True)
    (world.venv / 'bin/python').symlink_to(sys.executable)
    world.prod = tmp_path / 'prod'
    world.prod.mkdir()
    world.control = tmp_path / 'control'
    world.control.mkdir()
    home = tmp_path / 'home'
    world.mac = FakeLegacyMac(home, world.legacy, world.dash, world.venv)
    world.mac.control = world.control
    support = world.mac.support
    support.mkdir(parents=True)
    (home / 'Library/LaunchAgents').mkdir(parents=True)
    (home / '.frank_meme_control_root').write_text(str(world.control) + '\n', encoding='utf-8')
    policy = support / 'follow_policy_v1.approved.json'
    policy.write_text(POLICY_TEXT, encoding='utf-8')
    policy_sha = r.sha(policy)
    world.mac.policy_hash = policy_sha
    (support / 'approved_policy_sha256').write_text(policy_sha + '\n', encoding='utf-8')
    rpc = support / 'solana_rpc_urls'
    rpc.write_text('https://example.invalid/rpc\n', encoding='utf-8')
    os.chmod(rpc, 0o600)
    (support / 'dashboard_port').write_text('8766\n', encoding='utf-8')
    (world.control / 'dashboard.port').write_text('8766\n', encoding='utf-8')
    pointer = home / '.frank_meme_control_root'
    world.mac.runners['loop'].write_text(loop_runner_text(world.legacy, world.prod, world.venv, pointer, policy,
                                                          support / 'approved_policy_sha256', rpc), encoding='utf-8')
    world.mac.runners['dashboard'].write_text(dash_runner_text(world.dash, world.prod, world.venv, pointer, rpc),
                                              encoding='utf-8')
    for key in ('loop', 'dashboard'):
        os.chmod(world.mac.runners[key], 0o700)
        plist = world.mac.plist_path(key)
        plist.write_bytes(plistlib.dumps({'Label': world.mac.labels[key].split('/')[-1],
                                          'ProgramArguments': [str(world.mac.runners[key])], 'KeepAlive': True}))
    world.original_loop = world.mac.runners['loop'].read_bytes()
    world.original_dash = world.mac.runners['dashboard'].read_bytes()
    now = time.time()
    started = now - 3600
    world.loop_pid, world.dash_pid = 4242, 4343
    world.mac.add_proc(world.loop_pid, f'{world.venv}/bin/python scripts/mission_meme_v1.py loop --live-delivery',
                       world.legacy, started)
    world.mac.add_proc(world.dash_pid, f'{world.venv}/bin/python scripts/mission_meme_v1.py serve',
                       world.dash, started)
    world.mac.loaded = {world.mac.labels['loop']: world.loop_pid, world.mac.labels['dashboard']: world.dash_pid}
    for rel in list(LEGACY_DISK) + list(LEGACY_EXTRA):
        os.utime(world.legacy / rel, (now, now))
    os.utime(world.mac.runners['loop'], (now, now))
    os.utime(world.mac.runners['dashboard'], (started - 10, started - 10))
    world.mac.runners['dashboard']  # dashboard runner predates its process: strict-runtime shape
    _seed_control(world, policy_sha, now)
    _seed_frank(world)
    world.frank_db = world.prod / 'forward.sqlite'
    world.db = world.control / 'mission-control.sqlite'
    monkeypatch.setattr(r, 'candidate', lambda root, expected: _ops_source(world.ops))
    monkeypatch.setattr(r, 'scanner_inventory', lambda mac, label, prod: {
        'pid': 5555, 'protected': {}, 'source': {}, 'loaded_source_sha256': 'L', 'policy_hash': 'P',
        'entry_hash': 'E', 'loaded_hash': 'H', 'root': 'x'})
    monkeypatch.setattr(r, 'http_check', lambda context, target=False: world.mac.events.append(('http', bool(target))))
    monkeypatch.setattr(r, 'wait_ready', lambda check, seconds: check())
    monkeypatch.setattr(r.time, 'sleep', lambda seconds: None)
    world.authorizations = {'authorize_production_restart': True, 'authorize_future_real_notifications': True,
                            'authorize_legacy_unverified_loop_cutover': True}
    return world


def _ops_source(root):
    manifest = {}
    for base in ('mission_agent', 'config'):
        for path in sorted((root / base).rglob('*')):
            if path.is_file() and path.suffix in {'.py', '.js', '.css', '.html', '.json'}:
                manifest[path.relative_to(root).as_posix()] = r.sha(path)
    manifest['scripts/mission_meme_v1.py'] = r.sha(root / 'scripts/mission_meme_v1.py')
    return manifest


def _seed_control(world, policy_sha, now):
    from datetime import datetime, timezone
    db = ControlDB(world.control / 'mission-control.sqlite')
    payload = {'person_id': 'frank', 'mint': 'TEST_ONLY', 'episode_id': 'fixture',
               'source_signal_type': 'FRANK_MULTIPLE_SIGNAL', 'decision': 'BUY', 'created_at': utc(),
               'inputs': {'buy_count': 3, 'pattern': 'MULTIPLE'}, 'metrics': {}, 'reasons': [], 'missing': [],
               'invalidation': []}
    event = db.record(payload, 'P1', 'H')['event']
    GmailDelivery(db).enqueue(event, mode='DRY_RUN_AUDIT', forbidden=True)
    LocalDelivery(db).enqueue(event, forbidden=True)
    db.db.execute('DROP TABLE local_delivery_presentation')
    db.db.commit()
    db.close()
    world.decision_id = event['decision_id']
    (world.control / 'mission-control-health.json').write_text(json.dumps({
        'status': 'OK', 'updated_at': datetime.fromtimestamp(now, timezone.utc).isoformat(),
        'policy_hash': policy_sha, 'delivery_allowed': True}), encoding='utf-8')
    (world.control / 'loop.pid').write_text(str(world.loop_pid), encoding='utf-8')


def make_historical_manual_review(db_path, decision_id):
    """Turn the dry-run audit row into one historical zero-attempt pre-send expiry (terminal)."""
    con = sqlite3.connect(db_path)
    wire = '<mission.' + digest({'decision_id': decision_id, 'mode': 'LIVE'}) + '@local.invalid>'
    con.execute("UPDATE gmail_delivery SET delivery_mode='LIVE', wire_message_id=?, status='MANUAL_REVIEW', "
                "last_error='GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND', attempt_count=0 "
                "WHERE decision_id=?", (wire, decision_id))
    con.execute("UPDATE decision_outbox SET status='MANUAL_REVIEW' WHERE decision_id=? AND channel='gmail'",
                (decision_id,))
    con.commit()
    con.close()


def _seed_frank(world):
    con = sqlite3.connect(world.prod / 'forward.sqlite')
    con.execute('CREATE TABLE v1_states(person_id TEXT, mint TEXT, body TEXT)')
    body = json.dumps({'events': [{'direction': 'BUY', 'quote_asset': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
                                   'amount_predicate': 'USDC_DIRECT_NUMERIC'}]})
    con.execute("INSERT INTO v1_states VALUES('frank','Mint111',?)", (body,))
    con.commit()
    con.close()


def apply(world, release_dir, authorizations=None, tmp=None):
    return r.legacy_cutover_apply(world.mac, world.ops, world.sha, 'gui/501/com.jerson.scanner',
                                  release_dir, world.authorizations if authorizations is None else authorizations)


def journal_of(release_dir):
    return json.loads((Path(release_dir) / 'journal.json').read_text(encoding='utf-8'))


def queue_rows(db):
    con = sqlite3.connect(db)
    rows = {t: con.execute(f'SELECT * FROM {t} ORDER BY decision_id').fetchall()
            for t in ('gmail_delivery', 'local_delivery', 'decision_outbox')}
    con.close()
    return rows


def test_plan_on_exact_legacy_shape_is_eligible_and_read_only(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    before = {p: r.sha(p) for p in tmp_path.rglob('*') if p.is_file()}
    report = r.legacy_cutover_plan(world.mac, world.ops, world.sha, 'gui/501/com.jerson.scanner')
    after = {p: r.sha(p) for p in tmp_path.rglob('*') if p.is_file()}
    assert report['gate'] == r.LEGACY_PLAN_READY
    assert report['deployment_authorized'] is False and report['mutated_production'] is False
    assert report['legacy_loop_runtime'] == 'UNVERIFIED_KNOWN_DISK_OVERLAY_ONLY'
    assert report['legacy_overlay_classification'] == r.LEGACY_OVERLAY_CLASS
    assert 'loop' not in world.mac.runtime_calls, 'the legacy Loop must never receive a runtime PASS'
    assert before == {p: h for p, h in after.items() if p in before}, 'plan mutated the sandbox'


def test_fourth_unexpected_source_file_blocks_before_any_stop(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    (world.legacy / 'mission_agent/mission_control/extra_unknown.py').write_text('X = 1\n', encoding='utf-8')
    with pytest.raises(RuntimeError, match='LEGACY_FINGERPRINT_NOT_EXACT'):
        r.legacy_cutover_plan(world.mac, world.ops, world.sha, 'gui/501/com.jerson.scanner')
    assert not any(e[0] in ('stop', 'signal', 'hold') for e in world.mac.events)


def test_overlay_predating_process_start_is_not_the_legacy_shape(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    old = time.time() - 10 * 3600
    os.utime(world.legacy / 'mission_agent/mission_control/server.py', (old, old))
    with pytest.raises(RuntimeError, match='LEGACY_OVERLAY_NOT_MODIFIED_AFTER_START'):
        r.legacy_cutover_plan(world.mac, world.ops, world.sha, 'gui/501/com.jerson.scanner')


def test_tampered_plist_lifecycle_blocks(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    world.mac.plist_path('loop').write_bytes(plistlib.dumps({
        'Label': world.mac.labels['loop'].split('/')[-1], 'ProgramArguments': [str(world.mac.runners['loop'])],
        'KeepAlive': False}))
    with pytest.raises(RuntimeError, match='LEGACY_PLIST_LIFECYCLE'):
        r.legacy_cutover_plan(world.mac, world.ops, world.sha, 'gui/501/com.jerson.scanner')


def test_duplicate_loop_worker_blocks_before_any_stop(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    world.mac.add_proc(4999, f'{world.venv}/bin/python scripts/mission_meme_v1.py loop --live-delivery',
                       world.legacy, time.time() - 60)
    with pytest.raises(RuntimeError, match='DUPLICATE_OR_UNKNOWN_WORKER_BEFORE_STOP'):
        r.legacy_cutover_plan(world.mac, world.ops, world.sha, 'gui/501/com.jerson.scanner')
    assert not any(e[0] in ('stop', 'signal', 'hold') for e in world.mac.events)


def test_pending_gmail_or_outbox_blocks_before_any_stop(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    con = sqlite3.connect(world.db)
    con.execute("UPDATE gmail_delivery SET status='PENDING' WHERE decision_id=?", (world.decision_id,))
    con.commit()
    con.close()
    with pytest.raises(RuntimeError, match='ACTIVE_OR_UNKNOWN_QUEUE_gmail_delivery'):
        r.legacy_cutover_plan(world.mac, world.ops, world.sha, 'gui/501/com.jerson.scanner')
    assert not any(e[0] in ('stop', 'signal', 'hold') for e in world.mac.events)


def test_mixed_legacy_checkout_is_still_rejected_by_normal_source_gate(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    with pytest.raises(RuntimeError, match='SOURCE_MIXED_BYTES'):
        r.source_manifest(world.legacy)


def test_apply_refuses_without_every_authorization_and_changes_nothing(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    for missing in ('authorize_legacy_unverified_loop_cutover', 'authorize_production_restart',
                    'authorize_future_real_notifications'):
        auth = dict(world.authorizations, **{missing: False})
        with pytest.raises(RuntimeError, match='LEGACY_AUTHORIZATION_INCOMPLETE'):
            apply(world, tmp_path / f'rel-{missing}', auth)
    assert world.mac.events == [] and world.mac.runners['loop'].read_bytes() == world.original_loop


def test_full_legacy_cutover_switches_both_and_never_duplicates_a_writer(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    make_historical_manual_review(world.db, world.decision_id)
    before = queue_rows(world.db)
    release_dir = tmp_path / 'release'
    result = apply(world, release_dir)
    assert result['status'] == 'LEGACY_SUCCESS', result
    journal = journal_of(release_dir)
    assert [h['phase'] for h in journal['history']] == list(r.LEGACY_PHASES)
    order = [e for e in world.mac.events if e[0] in ('signal', 'hold', 'stop', 'start')]
    stop_index = order.index(('stop', 'loop'))
    assert order.index(('signal', world.loop_pid, int(signal.SIGSTOP))) < stop_index
    assert order.index(('signal', world.loop_pid, int(signal.SIGKILL))) > stop_index, 'KILL only after bootout'
    assert order.index(('stop', 'dashboard')) > stop_index
    starts = [e for e in world.mac.events if e[0] == 'start']
    assert [e[1] for e in starts] == ['dashboard', 'loop'], 'dashboard first, then loop'
    staged = (world.mac.support / 'pr39-immutable-releases' / world.sha[:12])
    assert f'LOCAL_AGENT="{staged}' in world.mac.runners['loop'].read_text(encoding='utf-8')
    assert f'LOCAL_AGENT="{staged}' in world.mac.runners['dashboard'].read_text(encoding='utf-8')
    assert world.mac.violations == []
    assert world.mac.procs[world.loop_pid]['state'] == 'dead'
    assert world.mac.loaded[world.mac.labels['loop']] != world.loop_pid
    assert (release_dir / 'legacy-loop-runner.before.sh').read_bytes() == world.original_loop
    after = queue_rows(world.db)
    assert before == after, 'historical delivery rows must be preserved byte-for-byte'
    con = sqlite3.connect(world.db)
    assert con.execute("SELECT name FROM sqlite_master WHERE name='local_delivery_presentation'").fetchone()
    assert con.execute("SELECT COUNT(*) FROM gmail_delivery WHERE status='MANUAL_REVIEW'").fetchone()[0] == 1
    con.close()


def test_pre_freeze_failure_aborts_without_signalling_the_legacy_loop(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    monkeypatch.setattr(r, 'backup', lambda src, dest, deadline=30: (_ for _ in ()).throw(
        sqlite3.OperationalError('database is locked')))
    release_dir = tmp_path / 'release'
    result = apply(world, release_dir)
    assert result['status'] == r.LEGACY_ABORTED and result['mutated_production'] is False
    assert not any(e[0] in ('signal', 'stop', 'hold', 'start') for e in world.mac.events)
    assert world.mac.runners['loop'].read_bytes() == world.original_loop
    assert journal_of(release_dir)['phase'] == r.LEGACY_ABORTED


def test_queue_becoming_active_while_frozen_resumes_the_untouched_loop(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    real_ledger, calls = r.ledger, {'n': 0}

    def flaky(db):
        calls['n'] += 1
        if calls['n'] == 2:
            raise RuntimeError('ACTIVE_OR_UNKNOWN_QUEUE_gmail_delivery')
        return real_ledger(db)
    monkeypatch.setattr(r, 'ledger', flaky)
    release_dir = tmp_path / 'release'
    result = apply(world, release_dir)
    assert result['status'] == r.LEGACY_ABORTED and result['reason'] == 'ACTIVE_OR_UNKNOWN_QUEUE_gmail_delivery'
    assert world.mac.procs[world.loop_pid]['state'] == 'running', 'legacy Loop must be resumed'
    assert ('signal', world.loop_pid, int(signal.SIGCONT)) in world.mac.events
    assert not any(e[0] in ('stop', 'start') for e in world.mac.events)
    assert journal_of(release_dir)['phase'] == r.LEGACY_ABORTED


def test_partial_hold_failure_releases_prior_holds_and_resumes_verified_loop(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    original_hold = world.mac.hold
    def fail_second_hold(key):
        if key == 'dashboard':
            raise RuntimeError('DASHBOARD_HOLD_FAILED')
        return original_hold(key)
    monkeypatch.setattr(world.mac, 'hold', fail_second_hold)
    release_dir = tmp_path / 'release'
    result = apply(world, release_dir)
    assert result['status'] == r.LEGACY_ABORTED
    assert world.mac.holds == set(), 'partially disabled launch agents must be restored'
    assert ('release_hold', 'loop') in world.mac.events
    assert ('signal', world.loop_pid, int(signal.SIGCONT)) in world.mac.events
    assert world.mac.procs[world.loop_pid]['state'] == 'running'
    assert journal_of(release_dir)['phase'] == r.LEGACY_ABORTED
    assert not any(evt[0] == 'start' for evt in world.mac.events)


def test_partial_hold_restore_failure_is_manual_not_false_abort(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    original_hold = world.mac.hold
    def fail_second_hold(key):
        if key == 'dashboard':
            raise RuntimeError('DASHBOARD_HOLD_FAILED')
        return original_hold(key)
    monkeypatch.setattr(world.mac, 'hold', fail_second_hold)
    monkeypatch.setattr(world.mac, 'release_hold',
                        lambda key: (_ for _ in ()).throw(RuntimeError('ENABLE_FAILED')))
    release_dir = tmp_path / 'release'
    with pytest.raises(RuntimeError, match='ENABLE_FAILED'):
        apply(world, release_dir)
    assert journal_of(release_dir)['phase'] == r.LEGACY_MANUAL
    assert world.mac.loaded[world.mac.labels['loop']] is None
    assert not any(evt[0] == 'start' for evt in world.mac.events)


def test_failure_after_stop_never_restarts_the_legacy_loop(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    monkeypatch.setattr(r, 'migrate', lambda path: (_ for _ in ()).throw(RuntimeError('PRESENTATION_SCHEMA')))
    release_dir = tmp_path / 'release'
    with pytest.raises(RuntimeError, match='PRESENTATION_SCHEMA'):
        apply(world, release_dir)
    assert world.mac.violations == [] and world.mac.procs[world.loop_pid]['state'] == 'dead'
    assert not any(e[0] == 'start' for e in world.mac.events)
    assert journal_of(release_dir)['phase'] == r.LEGACY_MANUAL


def test_new_dashboard_started_but_new_loop_fails_stops_new_processes_not_legacy(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    world.mac.loop_heartbeats = False
    release_dir = tmp_path / 'release'
    with pytest.raises(RuntimeError):
        apply(world, release_dir)
    assert world.mac.violations == []
    starts = [e[1] for e in world.mac.events if e[0] == 'start']
    assert starts == ['dashboard', 'loop']
    assert all(world.mac.loaded.get(world.mac.labels[k]) is None for k in ('loop', 'dashboard'))
    assert world.mac.procs[world.loop_pid]['state'] == 'dead'
    assert journal_of(release_dir)['phase'] == r.LEGACY_MANUAL


def test_sigterm_during_unload_is_fail_stopped_and_handlers_restored(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    fired = {'done': False}

    def term(key):
        if key == 'loop' and not fired['done']:
            fired['done'] = True
            os.kill(os.getpid(), signal.SIGTERM)
    world.mac.before_stop = term
    previous = signal.getsignal(signal.SIGTERM)
    release_dir = tmp_path / 'release'
    with pytest.raises(KeyboardInterrupt):
        apply(world, release_dir)
    assert signal.getsignal(signal.SIGTERM) == previous, 'signal handlers must be restored'
    assert world.mac.violations == []
    assert journal_of(release_dir)['phase'] == r.LEGACY_MANUAL


def test_interrupt_while_switching_runners_leaves_loop_unrestarted(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    def interrupt_first(path, text):
        raise KeyboardInterrupt('RELEASE_INTERRUPTED')
    monkeypatch.setattr(r, 'write_runner', interrupt_first)
    release_dir = tmp_path / 'release'
    with pytest.raises(KeyboardInterrupt):
        apply(world, release_dir)
    assert world.mac.runners['loop'].read_bytes() == world.original_loop
    assert not any(e[0] == 'start' for e in world.mac.events)
    assert journal_of(release_dir)['phase'] == r.LEGACY_MANUAL


def test_hard_kill_after_intent_leaves_recoverable_journal_and_no_second_loop(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    release_dir = tmp_path / 'release'
    pid = os.fork()
    if pid == 0:
        try:
            def hard_kill(key):
                if key == 'loop':
                    os._exit(137)            # no finally, no handler, no journal append: SIGKILL-like
            world.mac.before_stop = hard_kill
            apply(world, release_dir)
        finally:
            os._exit(0)
    _, status = os.waitpid(pid, 0)
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 137
    journal = journal_of(release_dir)
    assert journal['intent']['action'] == 'UNLOAD_LOOP_BEFORE_ANY_KILL'
    assert journal['phase'] == 'L30_HOLDS_SET'
    report = r.legacy_recover_inventory(world.mac, release_dir / 'journal.json')
    assert report['action_taken'] == 'NONE' and report['manual_action_required'] is True
    assert report['restarted_services'] is False


def test_recovery_inventory_is_read_only_and_refuses_normal_journals(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    monkeypatch.setattr(r, 'migrate', lambda path: (_ for _ in ()).throw(RuntimeError('PRESENTATION_SCHEMA')))
    release_dir = tmp_path / 'release'
    with pytest.raises(RuntimeError):
        apply(world, release_dir)
    events_before = list(world.mac.events)
    report = r.legacy_recover_inventory(world.mac, release_dir / 'journal.json')
    assert report['action_taken'] == 'NONE' and world.mac.events[:len(events_before)] == events_before
    assert len(world.mac.events) == len(events_before), 'inventory must not signal, stop or start anything'
    normal = tmp_path / 'normal.json'
    normal.write_text(json.dumps({'phase': 'PREPARED', 'expected': 'x'}), encoding='utf-8')
    with pytest.raises(RuntimeError, match='NOT_A_LEGACY_JOURNAL'):
        r.legacy_recover_inventory(world.mac, normal)


def test_normal_recovery_refuses_a_legacy_journal(tmp_path, monkeypatch, capsys):
    world = build_world(tmp_path, monkeypatch)
    monkeypatch.setattr(r, 'migrate', lambda path: (_ for _ in ()).throw(RuntimeError('PRESENTATION_SCHEMA')))
    release_dir = world.mac.support / 'pr39-releases' / 'legacy-run'
    with pytest.raises(RuntimeError):
        r.legacy_cutover_apply(world.mac, world.ops, world.sha, 'gui/501/com.jerson.scanner', release_dir,
                               world.authorizations)
    monkeypatch.setattr(r, 'Mac', lambda *a, **k: world.mac)
    monkeypatch.setattr(sys, 'platform', 'darwin')
    with pytest.raises(RuntimeError, match='LEGACY_JOURNAL_REQUIRES_LEGACY_INVENTORY'):
        r.main(['--expected-release-sha', world.sha, '--recover', str(release_dir / 'journal.json'), '--apply',
                '--authorize-production-restart', '--authorize-future-real-notifications'])


def test_legacy_plan_and_apply_flags_cannot_be_mixed_with_a_normal_apply(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    monkeypatch.setattr(r, 'Mac', lambda *a, **k: world.mac)
    monkeypatch.setattr(sys, 'platform', 'darwin')
    with pytest.raises(RuntimeError, match='LEGACY_PLAN_IS_READ_ONLY'):
        r.main(['--expected-release-sha', world.sha, '--legacy-cutover-plan', '--apply',
                '--authorize-production-restart', '--authorize-future-real-notifications'])
    with pytest.raises(RuntimeError, match='LEGACY_EXPLICIT_AUTHORIZATION_REQUIRED'):
        r.main(['--expected-release-sha', world.sha, '--legacy-cutover-apply', '--apply',
                '--authorize-production-restart', '--authorize-future-real-notifications'])
    assert world.mac.events == []


def test_wal_backup_preserves_uncheckpointed_history(tmp_path):
    src = tmp_path / 'wal.sqlite'
    con = sqlite3.connect(src, isolation_level=None)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA wal_autocheckpoint=0')
    con.execute('CREATE TABLE history(id INTEGER PRIMARY KEY, note TEXT)')
    for i in range(50):
        con.execute('INSERT INTO history(note) VALUES(?)', (f'row-{i}',))
    assert (tmp_path / 'wal.sqlite-wal').stat().st_size > 0, 'the fixture must leave history in the WAL'
    dest = tmp_path / 'backup.sqlite'
    r.backup(src, dest)
    con.close()
    copy = sqlite3.connect(dest)
    assert copy.execute('SELECT COUNT(*) FROM history').fetchone()[0] == 50
    assert copy.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    copy.close()
    assert oct(dest.stat().st_mode & 0o777) == '0o600'


def test_low_disk_blocks_the_plan(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    monkeypatch.setattr(r, 'disk_gate', lambda directory, databases: (_ for _ in ()).throw(
        RuntimeError('DISK_SPACE_INSUFFICIENT')))
    with pytest.raises(RuntimeError, match='DISK_SPACE_INSUFFICIENT'):
        r.legacy_cutover_plan(world.mac, world.ops, world.sha, 'gui/501/com.jerson.scanner')


def test_queue_reappearing_after_stop_blocks_before_migration(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    real_ledger, calls = r.ledger, {'n': 0}

    def reappears(db):
        calls['n'] += 1
        if calls['n'] == 3:            # plan, frozen check, then the post-stop check
            raise RuntimeError('ACTIVE_OR_UNKNOWN_QUEUE_local_delivery')
        return real_ledger(db)
    monkeypatch.setattr(r, 'ledger', reappears)
    release_dir = tmp_path / 'release'
    with pytest.raises(RuntimeError, match='ACTIVE_OR_UNKNOWN_QUEUE_local_delivery'):
        apply(world, release_dir)
    con = sqlite3.connect(world.db)
    assert con.execute("SELECT name FROM sqlite_master WHERE name='local_delivery_presentation'").fetchone() is None, \
        'no DDL may run once the queue is not proven terminal'
    con.close()
    assert world.mac.violations == [] and journal_of(release_dir)['phase'] == r.LEGACY_MANUAL


@pytest.mark.parametrize('drift_from_call, expected', [
    (2, 'SCANNER_CHANGED_DURING_CUTOVER'),   # call 1 = plan, call 2 = post-stop checkpoint (L40)
    (3, 'SCANNER_CHANGED_AFTER_CUTOVER'),    # call 3 = post-switch checkpoint (L90)
])
def test_scanner_drift_at_each_checkpoint_blocks_the_next_step(tmp_path, monkeypatch, drift_from_call, expected):
    world = build_world(tmp_path, monkeypatch)
    calls = {'n': 0}

    def drifting(mac, label, prod):
        calls['n'] += 1
        snap = {'pid': 5555, 'protected': {}, 'source': {}, 'loaded_source_sha256': 'L', 'policy_hash': 'P',
                'entry_hash': 'E', 'loaded_hash': 'H', 'root': 'x'}
        if calls['n'] >= drift_from_call:
            snap['loaded_source_sha256'] = 'CHANGED'
        return snap
    monkeypatch.setattr(r, 'scanner_inventory', drifting)
    release_dir = tmp_path / 'release'
    with pytest.raises(RuntimeError, match=expected):
        apply(world, release_dir)
    assert world.mac.violations == [] and journal_of(release_dir)['phase'] == r.LEGACY_MANUAL


def test_new_dashboard_runtime_failure_at_L80_stops_it_and_never_starts_loop(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    real_runtime = world.mac.runtime

    def bad_dashboard(key, text):
        # field() returns a resolved Path; compare Paths, never a Path with a str.
        if key == 'dashboard' and r.field(text, 'LOCAL_AGENT') != Path(world.dash).resolve():
            raise RuntimeError('RUNTIME_CWD')
        return real_runtime(key, text)
    monkeypatch.setattr(world.mac, 'runtime', bad_dashboard)
    release_dir = tmp_path / 'release'
    with pytest.raises(RuntimeError, match='RUNTIME_CWD'):
        apply(world, release_dir)
    assert not any(e[0] == 'start' and e[1] == 'loop' for e in world.mac.events)
    assert world.mac.loaded.get(world.mac.labels['dashboard']) is None
    assert journal_of(release_dir)['phase'] == r.LEGACY_MANUAL


def test_migration_is_idempotent_and_additive_only(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    r.migrate(world.db)
    r.migrate(world.db)
    con = sqlite3.connect(world.db)
    assert con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='local_delivery_presentation'").fetchone()[0] == 1
    con.close()


@pytest.mark.parametrize('sig', [signal.SIGTERM, signal.SIGINT])
def test_signal_during_unload_is_fail_stopped_for_both_signals(tmp_path, monkeypatch, sig):
    world = build_world(tmp_path, monkeypatch)
    fired = {'done': False}

    def hit(key):
        if key == 'loop' and not fired['done']:
            fired['done'] = True
            os.kill(os.getpid(), sig)
    world.mac.before_stop = hit
    previous = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT)}
    release_dir = tmp_path / 'release'
    with pytest.raises(KeyboardInterrupt):
        apply(world, release_dir)
    assert {s: signal.getsignal(s) for s in previous} == previous
    assert world.mac.violations == [] and journal_of(release_dir)['phase'] == r.LEGACY_MANUAL


def test_success_never_leaves_two_loop_processes_alive(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    result = apply(world, tmp_path / 'release')
    assert result['status'] == 'LEGACY_SUCCESS'
    loops = [pid for pid, p in world.mac.procs.items() if p['state'] != 'dead' and
             'scripts/mission_meme_v1.py loop' in p['command']]
    assert len(loops) == 1, f'exactly one live Loop expected, saw {loops}'
    assert world.loop_pid not in loops


def test_journal_rejects_out_of_order_or_unlogged_phases(tmp_path):
    journal = r.LegacyJournal(tmp_path / 'journal.json', {'expected': 'x'})
    with pytest.raises(RuntimeError, match='LEGACY_PHASE_ORDER'):
        journal.enter('L20_PRESTOP_BACKED_UP')          # skipping L00 and L10 must fail
    journal.enter('L00_RECHECKED')
    journal.intent('STAGE_RELEASE')
    assert json.loads((tmp_path / 'journal.json').read_text())['intent']['action'] == 'STAGE_RELEASE'
    journal.enter('L10_STAGED')
    assert 'intent' not in json.loads((tmp_path / 'journal.json').read_text()), 'completion clears the intent'
    with pytest.raises(RuntimeError, match='LEGACY_TERMINAL_PHASE'):
        journal.terminal('L100_SUCCESS')                 # success is never written through terminal()


def test_cutover_tool_imports_no_gmail_or_delivery_send_path():
    import ast
    tree = ast.parse((ROOT / 'scripts/frank_pr39_controlled_release.py').read_text(encoding='utf-8'))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = [name for name in imported if 'gmail' in name or 'signals' in name or 'delivery' in name
                 or name.startswith('mission_agent.mission_control.service')]
    assert forbidden == [], f'the cutover tool must never reach a provider send path: {forbidden}'


def test_unverifiable_frozen_loop_is_unloaded_so_launchd_cannot_respawn_it(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    real_ledger, calls = r.ledger, {'n': 0}

    def stop_after_freeze(db):
        calls['n'] += 1
        if calls['n'] == 2:
            # The frozen process's identity changes before the resume: it can no longer be trusted.
            world.mac.procs[world.loop_pid]['cwd'] = '/somewhere/else'
            raise RuntimeError('ACTIVE_OR_UNKNOWN_QUEUE_gmail_delivery')
        return real_ledger(db)
    monkeypatch.setattr(r, 'ledger', stop_after_freeze)
    release_dir = tmp_path / 'release'
    with pytest.raises(RuntimeError, match='PROCESS_IDENTITY_CHANGED'):
        apply(world, release_dir)
    assert ('hold', 'loop') in world.mac.events and ('stop', 'loop') in world.mac.events
    assert world.mac.loaded.get(world.mac.labels['loop']) is None, 'the label must be unloaded'
    assert not any(e[0] == 'start' for e in world.mac.events)
    assert journal_of(release_dir)['phase'] == r.LEGACY_MANUAL


def test_legacy_recovery_inventory_is_reachable_from_readonly_cli(tmp_path, monkeypatch, capsys):
    world = build_world(tmp_path, monkeypatch)
    journal = tmp_path / 'manual-legacy.json'
    journal.write_text(json.dumps({'mode': 'LEGACY_CUTOVER',
                                   'phase': r.LEGACY_MANUAL,
                                   'legacy_loop_pid': world.loop_pid,
                                   'dashboard_pid': world.dash_pid,
                                   'history': []}), encoding='utf-8')
    monkeypatch.setattr(r, 'Mac', lambda *a, **k: world.mac)
    monkeypatch.setattr(sys, 'platform', 'darwin')
    before = list(world.mac.events)
    assert r.main(['--expected-release-sha', world.sha,
                   '--recover', str(journal),
                   '--legacy-recover-inventory']) == 0
    output = json.loads(capsys.readouterr().out)
    assert output['mode'] == 'LEGACY_RECOVERY_INVENTORY'
    assert output['action_taken'] == 'NONE'
    assert output['manual_action_required'] is True
    assert world.mac.events == before
    with pytest.raises(RuntimeError, match='RECOVERY_AUTHORIZATION_REQUIRED'):
        r.main(['--expected-release-sha', world.sha, '--recover', str(journal)])
    with pytest.raises(RuntimeError, match='LEGACY_APPLY_CANNOT_RECOVER_JOURNAL'):
        r.main(['--expected-release-sha', world.sha,
                '--legacy-cutover-apply', '--recover', str(journal), '--apply',
                '--authorize-production-restart', '--authorize-future-real-notifications',
                '--authorize-legacy-unverified-loop-cutover'])


def test_failure_after_new_loop_starts_holds_keepalive_before_unloading(tmp_path, monkeypatch):
    world = build_world(tmp_path, monkeypatch)
    world.mac.loop_heartbeats = False
    release_dir = tmp_path / 'release'
    with pytest.raises(RuntimeError):
        apply(world, release_dir)
    assert journal_of(release_dir)['phase'] == r.LEGACY_MANUAL
    assert world.mac.holds == {'loop', 'dashboard'}, 'both LaunchAgents must be disabled'
    starts = [i for i, e in enumerate(world.mac.events) if e[0] == 'start' and e[1] == 'loop']
    assert len(starts) == 1
    last_start = starts[0]
    assert any(e == ('hold', 'loop') for e in world.mac.events[last_start+1:])
    assert any(e == ('hold', 'dashboard') for e in world.mac.events[last_start+1:])
    assert all(world.mac.loaded.get(world.mac.labels[k]) is None for k in ('loop', 'dashboard'))


def test_scanner_snapshot_uses_stable_code_policy_pid_not_dynamic_launchctl_print(monkeypatch):
    counter = {'n': 0}
    def inventory(_mac, _label, _prod):
        counter['n'] += 1
        return {'pid': 52300, 'protected': {'policy':'hash'}, 'source': {'code':'hash'},
                'loaded_source_sha256':'sha256', 'policy_hash':'p', 'entry_hash':'h',
                'loaded_hash': str(counter['n']), 'root': 'stable'}
    monkeypatch.setattr(r, 'scanner_inventory', inventory)
    first = r.legacy_scanner_snapshot(None, None, None)
    second = r.legacy_scanner_snapshot(None, None, None)
    assert first == second
    assert 'loaded_hash' not in first
