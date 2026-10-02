"""One explicitly authorized local Frank shadow; future-only, no alerts or GPT calls."""
import argparse
import fcntl
import gzip
import json
import os
import re
import signal
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from mission_agent.db.repository import Repository
from mission_agent.frank.collector import FrankCollector
from mission_agent.frank.parser import normalize
from mission_agent.frank.rpc import SolanaRPC
from mission_agent.frank.archive import publish as archive
from mission_agent.hashing import canonical, loads
from mission_agent.transport.github import GitHubTransport, RemoteError
from mission_agent.queue.batch import build_batch, publish
from mission_agent.fm.queue import validate_shadow_batch
from mission_agent.config import Config

IDENTIFIER = 'com.jerson.crypto-monitor-frank-shadow'

def utc():
    return datetime.now(timezone.utc).isoformat()

def atomic_json(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp-' + str(os.getpid()))
    with tmp.open('w') as f:
        os.chmod(tmp, 0o600)
        json.dump(value, f, sort_keys=True, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

class ForwardTransport(GitHubTransport):
    def __init__(self, run_id, **kwargs):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', run_id):
            raise ValueError('INVALID_FORWARD_RUN_ID')
        super().__init__('mac', run_id, **kwargs)
        self.namespace = 'runtime-v2-test/frank-forward-shadow/' + run_id

class ObservedRPC(SolanaRPC):
    def __init__(self):
        super().__init__()
        self.success_at = None; self.errors = 0; self.timeouts = 0
        original=self.request
        def observed_request(*args,**kwargs):
            try:return original(*args,**kwargs)
            except TimeoutError:
                self.timeouts+=1;raise
            except __import__('urllib.error',fromlist=['URLError']).URLError as exc:
                if isinstance(getattr(exc,'reason',None),TimeoutError):self.timeouts+=1
                raise
        self.request=observed_request
    def call(self, method, params):
        try:
            result = super().call(method, params)
            self.success_at = utc()
            return result
        except Exception as exc:
            self.errors += 1
            raise

def transport_once(root, run_id):
    repo = Repository(root / 'forward.sqlite')
    try:
        old = next((r for r in repo.db.execute("SELECT payload_json,batch_id FROM batches WHERE state IN ('BUILT','PUBLISHED') ORDER BY generated_at,batch_id") if not (root / ('transport-'+r['batch_id']+'.json')).exists()), None)
        batch = loads(old[0]) if old else build_batch(repo, Config.for_remote(root))
        if batch is None: return None
        validate_shadow_batch(batch)
        # Reject seed/history/non-ACTIVE data before constructing a remote client or making any write.
        for value in batch['items']:
            sig=value['payload']['signature']
            row=repo.db.execute('SELECT t.evidence_json FROM frank_transactions t JOIN frank_observations o USING(signature) WHERE t.signature=?',(sig,)).fetchone()
            if row is None or loads(row[0])['mechanical_classification']!='ACTIVE_SWAP_LIKE':raise ValueError('REAL_FORWARD_ACTIVE_OBSERVATION_REQUIRED')
            if not (root/'raw'/(sig+'.json.gz')).is_file():raise ValueError('REAL_FORWARD_RAW_REQUIRED')
        transport = ForwardTransport(run_id)
        try: expected = transport.read(transport.branch, transport.namespace + '/ingest/current.json').blob_sha
        except RemoteError as exc:
            if exc.status != 404: raise
            expected = None
        publish(repo, transport, batch['batch_id'], expected_sha=expected)
        actual = ForwardTransport(run_id).read_batch(batch['batch_id'])
        if canonical(actual) != canonical(batch): raise ValueError('EXACT_PRIVATE_READBACK_MISMATCH')
        before = transport.api.commits
        transport.publish_batch(batch)
        if transport.api.commits != before: raise ValueError('DUPLICATE_PRIVATE_WRITE')
        completed = time.time()
        latencies = []
        for value in batch['items']:
            payload = value['payload']; sig = payload['signature']
            row = repo.db.execute('SELECT detected_at,normalized_at FROM frank_observations WHERE signature=?', (sig,)).fetchone()
            if row is None: raise ValueError('FORWARD_OBSERVATION_REQUIRED')
            detected, normalized = map(float, row)
            created = datetime.fromisoformat(value['created_at_utc'].replace('Z', '+00:00')).timestamp()
            latencies.append({'signature': sig, 'detection_seconds': detected - payload['block_time'],
                'normalization_seconds': normalized - detected, 'candidate_seconds': max(0, created - normalized),
                'transport_seconds': completed - created, 'total_e2e_seconds': completed - payload['block_time']})
        result = {'status': 'PASS_REAL_ACTIVE_PRIVATE_E2E', 'namespace': transport.namespace,
            'completed_at': utc(), 'batch_id': batch['batch_id'], 'items': batch['item_count'],
            'readback_exact': True, 'duplicate_writes': 0, 'remote_write_commits': before,
            'latencies': latencies, 'gmail': 0, 'notifications': 0, 'production_writes': 0}
        atomic_json(root / ('transport-' + batch['batch_id'] + '.json'), result)
        return result
    finally: repo.close()

def transport_loop(root, run_id, stopping):
    while not stopping.is_set():
        try:
            result = transport_once(root, run_id)
            if result: atomic_json(root / 'transport-health.json', result)
        except Exception as exc:
            atomic_json(root / 'transport-health.json', {'status': 'RETRY_PENDING', 'error': type(exc).__name__, 'at': utc()})
        stopping.wait(5)

def history_loop(root, stopping):
    import subprocess
    module=Path(__file__).resolve().parents[1]
    history=Path('/Users/jerson/Documents/ChatGPT/crypto-monitor-fm2-evidence-20260930/frank/backfill')
    snapshot=Path('/Users/jerson/Documents/ChatGPT/crypto-monitor-fm1-evidence-20260930/frank')
    while not stopping.is_set():
        with (root/'history-worker.log').open('ab') as log:
            proc=subprocess.Popen([str(module/'.venv/bin/python'),'-m','scripts.frank_backfill','--snapshot',str(snapshot),'--root',str(history),'--seconds','300','--forward-health',str(root/'health.json')],cwd=module,stdout=log,stderr=log,start_new_session=True)
            while proc.poll() is None and not stopping.wait(1): pass
            if proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=25)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
        stopping.wait(300)

def snapshot_health(repo, health):
    cursor = repo.db.execute("SELECT signature,slot,block_time,updated_at FROM frank_cursor WHERE name='latest'").fetchone()
    if cursor:
        health.update(latest_signature=cursor['signature'], last_processed_signature=cursor['signature'],
            last_normalized_signature=cursor['signature'], slot=cursor['slot'], blockTime=cursor['block_time'], persisted_at=cursor['updated_at'])
    counts = {}
    last_active = None
    for row in repo.db.execute('SELECT t.evidence_json,o.normalized_at FROM frank_transactions t JOIN frank_observations o USING(signature)'):
        e = loads(row[0]); kind = e['mechanical_classification']; counts[kind] = counts.get(kind, 0) + 1
        if kind == 'ACTIVE_SWAP_LIKE': last_active = max(last_active or '0', row[1], key=float)
    health.update(new_signatures=sum(counts.values()), active_count=counts.get('ACTIVE_SWAP_LIKE', 0),
        passive_count=counts.get('PASSIVE_RECEIPT_LIKE', 0), unknown_count=counts.get('UNKNOWN', 0), classifications=counts, last_active_at=last_active)
    candidates = repo.db.execute("SELECT payload_json,created_at_utc FROM candidates WHERE event_type='RAW_FRANK_CANDIDATE' ORDER BY created_at_utc,event_id").fetchall()
    health['candidate_count'] = len(candidates)
    health['last_candidate_at'] = candidates[-1][1] if candidates else None
    health['last_candidate_signature'] = loads(candidates[-1][0])['signature'] if candidates else None
    return health

def main():
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, required=True)
    for key in ('manual','raw','processed'): p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args(); a.root.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = (a.root / 'service.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    stopping = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT): signal.signal(sig, lambda *_: stopping.set())
    old = json.loads((a.root / 'health.json').read_text()) if (a.root / 'health.json').exists() else {}
    run_id = old.get('run_id', datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    health = {'status':'STARTING','identifier':IDENTIFIER,'run_id':run_id,'started_at':utc(),
        'first_started_at':old.get('first_started_at',utc()), 'pid':os.getpid(), 'restart_count':old.get('restart_count',-1)+1,
        'poll_count':old.get('poll_count',0),'request_count':old.get('request_count',0), 'rpc_429_count':old.get('rpc_429_count',0),
        'rpc_error_count':old.get('rpc_error_count',0),'timeouts':old.get('timeouts',0),'retry':old.get('retry',0),
        'gap_count':0,'unresolved_gap_count':old.get('unresolved_gap_count',0),'candidate_duplicate_count':0,
        'last_poll_at':None,'last_successful_poll':None,'last_rpc_success_at':None,'private_transport_status':'WAITING_REAL_ACTIVE_EVENT',
        'last_active_at':None,'last_candidate_at':None,'last_candidate_signature':None,
        'historical_network_backfill':'BOUNDED300S_IDLE_WINDOW_ONLY', 'gmail':0,'app_alert':0,'automation_mutations':0,'production_writes':0}
    totals = {k:health[k] for k in ('request_count','rpc_429_count','rpc_error_count','timeouts','retry')}
    repo = Repository(a.root / 'forward.sqlite'); rpc = ObservedRPC()
    collector = FrankCollector(repo,a.root / 'raw', {k:str(getattr(a,k)) for k in ('manual','raw','processed')},rpc)
    if collector.store.cursor() is None:
        for path in sorted((a.processed / 'normalized500').glob('*.json.gz')): collector.store.put(json.loads(gzip.decompress(path.read_bytes())))
        latest = rpc.signatures(limit=1)[0]; tx = rpc.transaction(latest['signature'])
        if tx is None: raise ValueError('INITIAL_CURSOR_TRANSACTION_UNAVAILABLE')
        archive(a.root / 'raw' / (latest['signature'] + '.json.gz'),gzip.compress(json.dumps(tx,separators=(',',':')).encode(),mtime=0))
        collector.store.put(normalize(latest['signature'],tx),advance=True)
        atomic_json(a.root / 'initial-boundary.json', {'at':utc(),'cursor':collector.store.cursor(),'forward_observation':False})
    worker = threading.Thread(target=transport_loop,args=(a.root,run_id,stopping),daemon=True); worker.start()
    history_worker = threading.Thread(target=history_loop,args=(a.root,stopping),daemon=True); history_worker.start()
    previous = collector.store.cursor(); atomic_json(a.root / ('restart-' + str(health['restart_count']) + '.json'), {'started_at':utc(),'cursor_before':previous,'integrity':repo.db.execute('PRAGMA integrity_check').fetchone()[0]})
    while not stopping.is_set():
        start = time.monotonic(); health['last_poll_at'] = utc(); health['poll_count'] += 1
        try:
            cycle = collector.cycle(); health.update(status='RUNNING',last_successful_poll=utc(),gap_count=cycle['cursor_gap'])
            health['candidate_duplicate_count'] += cycle['duplicates']
            with (a.root / 'cycles.jsonl').open('a') as f:
                os.chmod(f.name,0o600); json.dump({'at':utc(),'pid':os.getpid(),**cycle},f); f.write('\n');f.flush();os.fsync(f.fileno())
            if health['poll_count'] == old.get('poll_count',0)+1:
                atomic_json(a.root / ('restart-result-' + str(health['restart_count']) + '.json'),{'status':'PASS_CURSOR_BOUNDARY_FOUND','cursor_before':previous,'cursor_after':collector.store.cursor(),'gap':cycle['cursor_gap'],'new_signatures_recovered':cycle['normalized'],'duplicates':cycle['duplicates'],'at':utc()})
        except Exception as exc:
            health.update(status='RPC_RETRY',last_error=type(exc).__name__)
            if str(exc)=='FRANK_CURSOR_GAP_UNRESOLVED': health.update(status='CURSOR_GAP_BLOCKED',unresolved_gap_count=health['unresolved_gap_count']+1,gap_count=1)
        health.update(request_count=totals['request_count']+rpc.calls,rpc_429_count=totals['rpc_429_count']+rpc.rate_limits,
            rpc_error_count=totals['rpc_error_count']+rpc.errors,timeouts=totals['timeouts']+rpc.timeouts,retry=totals['retry']+rpc.retries,last_rpc_success_at=rpc.success_at)
        snapshot_health(repo,health)
        transport_health = a.root / 'transport-health.json'
        if transport_health.exists(): health['private_transport_status'] = json.loads(transport_health.read_text())['status']
        health['active_e2e_status'] = 'FRANK_ACTIVE_E2E_PASS' if health['private_transport_status']=='PASS_REAL_ACTIVE_PRIVATE_E2E' else 'FRANK_ACTIVE_E2E_WAITING_REAL_EVENT'
        health['poll_seconds'] = str(time.monotonic()-start); health['uptime_seconds'] = str(time.time()-datetime.fromisoformat(health['started_at']).timestamp()); atomic_json(a.root / 'health.json',health)
        stopping.wait(max(0,30-(time.monotonic()-start)))
    health['status']='STOPPED';health['stopped_at']=utc();atomic_json(a.root / 'health.json',health);repo.close()

if __name__=='__main__':main()
