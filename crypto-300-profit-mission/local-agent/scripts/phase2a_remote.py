"""Explicit opt-in Phase 2A runner. Real private GitHub, synthetic data, no sends.

Evidence/runtime output must be outside any Git checkout. This script never pushes
public code or enables automations. Each invocation chooses a fresh test namespace.
"""
import argparse
import copy
import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from mission_agent.clock import Clock, FakeClock, stamp
from mission_agent.config import Config
from mission_agent.db.repository import Repository
from mission_agent.models import Event
from mission_agent.hashing import canonical, digest, loads, seal
from mission_agent.queue.batch import build_batch
from mission_agent.queue.remote import publish_remote
from mission_agent.queue.reconciliation import reconcile
from mission_agent.decision.fixture_consumer import consume
from mission_agent.transport.github import GitHubAPI, GitHubTransport, RemoteError, Conflict, REPOSITORY


def save(path, value):
    path.write_bytes(canonical(value)); path.chmod(0o600)


def stats(api):
    return {k: getattr(api, k) for k in ('requests', 'commits', 'uploaded', 'downloaded')}


def make_matrix(root, run_id, api):
    t = GitHubTransport('mac', run_id + '-matrix', api=api, max_batch_bytes=100000)
    clock = Clock()
    result = []
    previous = None
    for size in (1000, 10000, 50000, 90000, 99000):
        # Valid synthetic envelope, padding in explicit transport probe field.
        # Individual items stay <=2KB, <=40 normal and <=8 urgent.
        event = Event.synthetic('TEST_ACTION_CANDIDATE', 'SYNTH', stamp(clock.now()), 0,
                                {'fixture_decision': 'WATCH'}, str(size))
        item = {'schema_version': 1, 'event_id': event.event_id, 'event_type': event.event_type,
                'source': 'synthetic', 'asset': 'SYNTH', 'observed_at_utc': event.observed_at_utc,
                'created_at_utc': event.observed_at_utc, 'priority': 0,
                'payload': event.payload, 'payload_sha256': digest(event.payload)}
        from datetime import timedelta
        value = {'schema_version': 1, 'batch_id': 'synthetic-probe:' + str(size),
                 'generated_at': stamp(clock.now()), 'valid_until': stamp(clock.now() + timedelta(hours=2)),
                 'item_count': 1, 'items': [item], 'transport_probe_padding': ''}
        value['transport_probe_padding'] = 'x' * (size - len(canonical(seal(value))))
        batch = seal(value)
        assert len(canonical(batch)) == size
        assert consume(batch, clock)['decision_count'] == 1
        proof = t.publish_batch(batch, previous)
        previous = proof.blob_sha
        remote = t.read('mac-data', t._path('ingest', batch['batch_id']))
        entry = {'requested_bytes': size, 'remote_bytes': len(remote.data),
                 'sha256': __import__('hashlib').sha256(remote.data).hexdigest(),
                 'path': remote.path, 'branch': remote.branch, 'commit_sha': remote.commit_sha,
                 'api_received_bytes': len(remote.data), 'api_hash_match': remote.data == canonical(batch)}
        result.append(entry)
        save(root / ('matrix-' + str(size) + '.json'), batch)
    save(root / 'matrix.json', result)
    save(root / 'matrix-stats.json', stats(api))


def worker(root, run_id, stage):
    api = GitHubAPI()
    t = GitHubTransport('mac', run_id, api=api)
    repo = Repository(root / 'mission.sqlite')
    if stage == 'publish-crash':
        config = Config.for_remote(root)
        clock = repo.clock
        labels = ['IGNORE', 'WATCH', 'ACTIONABLE_RISK', 'ACTIONABLE_OPPORTUNITY']
        for i in range(100):
            event = Event.synthetic('TEST_ACTION_CANDIDATE', 'SYNTH', stamp(clock.now()), int(i % 5 == 0),
                                    {'fixture_decision': labels[i % 4], 'ordinal': i, 'padding': 'x' * 1400}, str(i))
            # bool priority is intentionally converted to the contractual integer.
            repo.ingest(event)
        batch = build_batch(repo, config)
        publish_remote(repo, t, batch['batch_id'])
        save(root / 'first-batch.json', batch)
    elif stage == 'receipt-crash':
        # Read only. Prove receipt existed and was read, then SIGKILL before reconciliation.
        batch = loads((root / 'first-batch.json').read_bytes())
        receipt = t.read_receipt(batch['batch_id'])
        save(root / 'pre-crash-receipt.json', receipt)
    save(root / (stage + '-stats.json'), stats(api))
    # Deliberate real process death. SQLite connections are not gracefully closed.
    os.kill(os.getpid(), signal.SIGKILL)


def full_load(root, run_id):
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    script = str(Path(__file__).resolve())
    def killed(stage):
        proc = subprocess.run([sys.executable, script, '--root', str(root), '--run-id', run_id, '--stage', stage])
        assert proc.returncode == -signal.SIGKILL, proc.returncode
    killed('publish-crash')
    api = GitHubAPI(); mac = GitHubTransport('mac', run_id, api=api)
    gpt = GitHubTransport('gpt', run_id, api=api)
    repo = Repository(root / 'mission.sqlite'); config = Config.for_remote(root)
    first = loads((root / 'first-batch.json').read_bytes())
    original = {r[0] for r in repo.db.execute('SELECT event_id FROM candidates')}
    assert len(original) == 100
    before = api.commits
    proof = publish_remote(repo, mac, first['batch_id'])
    assert api.commits == before  # restart replay performs zero writes
    remote_first = gpt.read_batch(first['batch_id'])
    assert canonical(remote_first) == canonical(first)
    receipt = consume(remote_first, repo.clock)
    receipt_head = gpt.publish_receipt(receipt).blob_sha
    repo.close()
    killed('receipt-crash')
    repo = Repository(root / 'mission.sqlite')
    assert repo.db.execute('SELECT COUNT(*) FROM decisions').fetchone()[0] == 0
    # Recovery reads remote receipt; no fixture judgement repeated for first batch.
    recovered = mac.read_receipt(first['batch_id'])
    assert reconcile(repo, recovered)
    batches = [first]; receipts = [recovered]
    wrong_hash_accepted = missing_accepted = 0
    while (batch := build_batch(repo, config)) is not None:
        publish_remote(repo, mac, batch['batch_id'])
        remote = gpt.read_batch(batch['batch_id'])
        assert canonical(remote) == canonical(batch)
        decision = consume(remote, repo.clock)
        bad = copy.deepcopy(decision); bad['input_payload_sha256'] = '0' * 64
        gpt.write('gpt-data', gpt.namespace + '/faults/wrong-hash.json', bad, immutable=True)
        wrong_hash_accepted += reconcile(repo, mac.read('gpt-data', gpt.namespace + '/faults/wrong-hash.json').value)
        bad = copy.deepcopy(decision); bad['decisions'].pop()
        # Unique per batch so this fault archive is immutable too.
        fault_path = gpt.namespace + '/faults/missing-' + str(len(batches)) + '.json'
        gpt.write('gpt-data', fault_path, bad, immutable=True)
        missing_accepted += reconcile(repo, mac.read('gpt-data', fault_path).value)
        receipt_head = gpt.publish_receipt(decision, receipt_head).blob_sha
        actual = mac.read_receipt(batch['batch_id'])
        assert reconcile(repo, actual)
        batches.append(batch); receipts.append(actual)
        # Only inject wrong-hash file once: subsequent batches need a unique path.
        # Workload has three batches with this item/count/byte ceiling.
        if len(batches) >= 2:
            break
    # Finish remaining workload without repeating the same fault archive identity.
    while (batch := build_batch(repo, config)) is not None:
        publish_remote(repo, mac, batch['batch_id'])
        remote = gpt.read_batch(batch['batch_id'])
        assert canonical(remote) == canonical(batch)
        decision = consume(remote, repo.clock)
        receipt_head = gpt.publish_receipt(decision, receipt_head).blob_sha
        actual = mac.read_receipt(batch['batch_id']); assert reconcile(repo, actual)
        batches.append(batch); receipts.append(actual)
    # No DeliveryEngine or Gmail API; ACTION stays pending and gets only a dry-run manifest.
    actions = [dict(row) for row in repo.db.execute("SELECT event_id,state FROM deliveries WHERE state='DELIVERY_PENDING'")]
    gpt.publish_delivery({'schema_version': 1, 'mode': 'DRY_RUN', 'actions': actions}, 'synthetic-dry-run')
    from mission_agent.health.model import snapshot
    mac.publish_health(snapshot(repo, config, last_e2e='UNKNOWN'))
    assert mac.read_health()['overall'] != 'HEALTHY'
    remote_ids = {i['event_id'] for b in batches for i in gpt.read_batch(b['batch_id'])['items']}
    receipt_ids = {i['event_id'] for b in batches for i in mac.read_receipt(b['batch_id'])['decisions']}
    local = {r[0] for r in repo.db.execute('SELECT event_id FROM candidates')}
    decided = {r[0] for r in repo.db.execute('SELECT event_id FROM decisions')}
    metrics = {'events': 100, 'batches': len(batches), 'max_batch_bytes': max(len(canonical(b)) for b in batches),
               'local_candidate_loss': len(original - local), 'mac_data_loss': len(original - remote_ids),
               'receipt_loss': len(original - receipt_ids), 'reconciliation_loss': len(original - decided),
               'wrong_hash_accepted': int(wrong_hash_accepted), 'missing_event_accepted': int(missing_accepted),
               'dry_run_actions': len(actions), 'real_sends': 0, 'restart_replay_commits': 0,
               'publish_process_sigkill': True, 'receipt_process_sigkill': True,
               'first_batch_judgement_invocations': 1,
               'labels': {row[0]: row[1] for row in repo.db.execute('SELECT decision,COUNT(*) FROM decisions GROUP BY decision')},
               'api': stats(api), 'selected_ceiling': 75000}
    save(root / 'e2e.json', metrics)
    repo.close()


def failures(root, run_id):
    api = GitHubAPI(); t = GitHubTransport('mac', run_id + '-faults', api=api, sleep=lambda _: None)
    checks = {}
    path = t._path('health')
    first = t.write('mac-data', path, {'seq': 1}); checks['new_file_create'] = True
    second = t.write('mac-data', path, {'seq': 2}, first.blob_sha); checks['existing_CAS_update'] = True
    before = api.commits; t.write('mac-data', path, {'seq': 2}); checks['same_payload_retry'] = api.commits == before
    try: t.write('mac-data', path, {'seq': 3}, first.blob_sha)
    except Conflict: checks['stale_expected_rejected'] = True
    # Actual server 409: bypass transport guard solely to exercise raw GitHub stale SHA response.
    endpoint = t._endpoint('mac-data', path)
    body = {'message': 'Phase 2A stale SHA negative test', 'branch': 'mac-data', 'sha': first.blob_sha,
            'content': __import__('base64').b64encode(canonical({'seq': 3})).decode()}
    try: api.request('PUT', endpoint, body)
    except RemoteError as exc: checks['real_stale_SHA_409'] = exc.status == 409
    assert t.read('mac-data', path).value == {'seq': 2}
    archive = t._path('ingest', 'immutable-test')
    t.write('mac-data', archive, {'batch_id': 'immutable-test', 'test': 1}, immutable=True)
    before = api.commits
    t.write('mac-data', archive, {'batch_id': 'immutable-test', 'test': 1}, immutable=True)
    checks['archive_same_hash'] = api.commits == before
    try: t.write('mac-data', archive, {'batch_id': 'immutable-test', 'test': 2}, immutable=True)
    except Conflict: checks['archive_different_hash'] = checks['different_payload_same_batch'] = True
    for role, branch in [('mac', 'gpt-data'), ('gpt', 'mac-data')]:
        test = GitHubTransport(role, run_id + '-faults', api=api)
        try: test.write(branch, path, {})
        except ValueError: checks['wrong_branch_' + role] = True
    try: GitHubTransport('mac', run_id, api=api, repository='lxxlx2/ChatGPT_mission_record')
    except ValueError: checks['wrong_repo'] = True
    try: t.read('mac-data', t.namespace + '/missing.json')
    except RemoteError as exc: checks['GitHub_404'] = exc.status == 404
    # Manual writer uses raw API with current SHA, then stale transport caller must conflict.
    body['sha'] = second.blob_sha; body['content'] = __import__('base64').b64encode(canonical({'seq': 99})).decode()
    api.request('PUT', endpoint, body)
    try: t.write('mac-data', path, {'seq': 4}, second.blob_sha)
    except Conflict: checks['manual_change_rejected'] = t.read('mac-data', path).value == {'seq': 99}
    # Simulated network/rate-limit wrapper surrounds REAL remote API; no local file substitute.
    class Fault:
        def __init__(self, error): self.error = error; self.fired = False
        def request(self, method, endpoint, body=None):
            if method == 'PUT' and not self.fired:
                self.fired = True; raise self.error
            return api.request(method, endpoint, body)
    for label, error in [('timeout', RemoteError(0)), ('rate_limit', RemoteError(429, {'Retry-After': '0'}))]:
        fault = GitHubTransport('mac', run_id + '-faults', api=Fault(error), sleep=lambda _: None)
        checks[label + '_simulation'] = fault.write('mac-data', fault.namespace + '/faults/' + label + '.json', {'synthetic': True}).value == {'synthetic': True}
    from datetime import timedelta
    clock = FakeClock('2026-01-01T00:00:00Z')
    stale = seal({'schema_version': 1, 'batch_id': 'stale-synthetic', 'generated_at': stamp(clock.now()),
                  'valid_until': stamp(clock.now() + timedelta(seconds=1)), 'item_count': 0, 'items': []})
    t.publish_batch(stale)
    try: consume(t.read_batch(), Clock())
    except ValueError: checks['stale_current_rejected'] = True
    assert all(checks.values()), checks
    save(root / 'faults.json', {'checks': checks, 'api': stats(api)})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--stage', choices=['matrix', 'full', 'faults', 'publish-crash', 'receipt-crash'], required=True)
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=True, mode=0o700)
    args.root.chmod(0o700)
    check = subprocess.run(['git', '-C', str(args.root), 'rev-parse', '--is-inside-work-tree'], capture_output=True)
    if check.returncode == 0:
        raise ValueError('runtime evidence must be outside Git')
    if args.stage == 'full' and (args.root / 'mission.sqlite').exists():
        raise ValueError('full run requires a fresh SQLite root; use worker stages only for recovery')
    if args.stage == 'matrix': make_matrix(args.root, args.run_id, GitHubAPI())
    elif args.stage == 'full': full_load(args.root, args.run_id)
    elif args.stage == 'faults': failures(args.root, args.run_id)
    else: worker(args.root, args.run_id, args.stage)
