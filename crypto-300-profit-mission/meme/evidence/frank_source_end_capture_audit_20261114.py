"""Replay a source-end CA report from both providers' immutable captured reads.

Offline only; no frozen independent verdict, source calls, report overwrite or
freshness claim. Input reports/checkpoints stay private and read-only.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from unittest.mock import patch
sys.dont_write_bytecode=True
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--agent',type=Path,required=True)
p.add_argument('--expected-sha',required=True)
p.add_argument('--capture',type=Path,required=True)
p.add_argument('--summary',type=Path,required=True)
a=p.parse_args()
assert subprocess.check_output(['git','-C',str(a.agent),'rev-parse','HEAD']).decode().strip()==a.expected_sha
assert not subprocess.check_output(['git','-C',str(a.agent),'status','--porcelain']).strip()
assert a.summary.resolve() not in {(a.capture/n).resolve() for n in ['report.json','checkpoint.sqlite','done.json','status.json']}
events=Counter()
def audit(event,args):
    if event.startswith('socket.'):
        events[event]+=1
        raise AssertionError('OFFLINE_NO_SOCKET')
sys.addaudithook(audit)
sys.path.insert(0,str(a.agent))
from mission_agent.meme import cluster,pool_vaults,independent_check
from mission_agent.meme.job_checkpoint import JobCheckpoint,CheckpointRPC,CheckpointSecondaryRPC,CheckpointClient,canonical
from mission_agent.mission_control.server import CLUSTER_PRESETS
raw=(a.capture/'report.json').read_bytes();report=json.loads(raw)
cpfile=a.capture/'checkpoint.sqlite';before=hashlib.sha256(cpfile.read_bytes()).hexdigest()
db=sqlite3.connect(cpfile.absolute().as_uri()+'?mode=ro',uri=True)
meta=json.loads(db.execute('SELECT body FROM metadata WHERE id=1').fetchone()[0]);db.close()
cp=JobCheckpoint(a.capture,meta['job_id'],readonly=True,clock=lambda:meta['last_saved_at']) if cpfile.name==meta['job_id']+'.sqlite' else None
# JobCheckpoint uses its canonical private filename; copy only when the capture
# directory uses the portable checkpoint.sqlite name. Never alter the original.
import tempfile,shutil
work=tempfile.TemporaryDirectory(prefix='frank-two-source-replay-')
root=Path(work.name);root.chmod(0o700)
copy=root/(meta['job_id']+'.sqlite');shutil.copyfile(cpfile,copy);copy.chmod(0o600)
cp=JobCheckpoint(root,meta['job_id'],readonly=True,clock=lambda:meta['last_saved_at'])
def deny(*args,**kwargs):raise AssertionError('UNCAPTURED_SOURCE_READ')
class Client:
    token_snapshot=pool_snapshot=collect=collect_origin=staticmethod(deny)
rpc=CheckpointRPC(cp,cluster.SolanaReadOnlyRPC('https://offline-primary.invalid',fallback_endpoints=['https://offline-fallback.invalid'],open_url=deny,min_interval=0))
clients={name:CheckpointClient(cp,Client(),name) for name in ['market_client','independent_market_client','narrative_client']}
def secondary():
    return CheckpointSecondaryRPC(cp,cluster.SolanaReadOnlyRPC('https://offline-secondary.invalid',fallback_endpoints=[],open_url=deny,min_interval=0))
original_pool=pool_vaults.collect_pool_vault_snapshot
original_independent=independent_check.collect_independent_balance_check
def pool(*args,**kwargs):
    stamp=(report.get('pool_vaults') or {}).get('observed_at',report['observed_at'])
    with patch.object(pool_vaults.time,'time',return_value=stamp):return original_pool(*args,**kwargs)
def independent(*args,**kwargs):
    # Retrieval timing is captured at the RPC log boundary. Business values,
    # actual slots, both raw provider responses and all source failures replay.
    kwargs['clock']=lambda:cp.entries[cp.index-1]['finished_at']
    return original_independent(*args,**kwargs)
try:
    with patch.object(cluster.time,'time',return_value=report['observed_at']),patch.object(pool_vaults,'collect_pool_vault_snapshot',pool),patch.object(independent_check,'collect_independent_balance_check',independent):
        derived=cluster.WalletClusterAnalyzer(meta['mint'],rpc=rpc,special_registry=cluster.load_registry(a.agent/'config/meme_special_addresses.json'),independent_rpc=secondary,**CLUSTER_PRESETS[meta['preset']],**clients).analyze()
    rpc.assert_can_publish();assert cp.index==cp.replayed==meta['entry_count']
    channels=Counter(e['request']['channel'] for e in cp.entries)
    differences=[]
    def compare(old,new,path=''):
        if type(old)!=type(new):differences.append(path);return
        if isinstance(old,dict):
            for key in old.keys()|new.keys():
                child=path+'.'+key if path else key
                if key not in old or key not in new:differences.append(child)
                else:compare(old[key],new[key],child)
        elif isinstance(old,list):
            if len(old)!=len(new):differences.append(path+'.length')
            for i,(left,right) in enumerate(zip(old,new)):compare(left,right,path+f'[{i}]')
        elif old!=new:differences.append(path)
    compare({k:report[k] for k in derived},derived)
    def allowed(path):
        # holder_binary labels these two local time.time() fields explicitly as
        # JOB_RECEIVED_RESULT_MAY_BE_CACHED_NOT_BLOCK_TIME. They are not slots,
        # source as-of timestamps, response values or evidence identities.
        return (path in {'coverage.rpc_call_count_scope','rpc_endpoint','pool_vaults.market_comparison.result_received_at','pool_vaults.market_comparison.source_result_received_at','independent_balance_check.read_gap_seconds','special_address_roles.balance_check.result_received_at','holder_rankings.raw_balance_check.result_received_at'}
                or (path.startswith('independent_balance_check.batches[') and path.endswith('].read_gap_seconds')))
    forbidden=[s for s in differences if not allowed(s)]
    assert not forbidden,forbidden[:25]
    result={'source_sha':a.expected_sha,'report_sha256':hashlib.sha256(raw).hexdigest(),'checkpoint_sha256':before,
            'replayed_reads':cp.replayed,'channels':dict(channels),'primary_reserved_wire_attempts':meta['wire_used'],
            'secondary_reserved_wire_attempts':meta.get('secondary_rpc',{}).get('wire_used',0),
            'secondary_verdict_frozen':False,'business_differences':forbidden,'normalized_local_timing_or_endpoint_paths':differences,
            'socket_events':dict(events),'checkpoint_original_hash_unchanged':hashlib.sha256(cpfile.read_bytes()).hexdigest()==before}
    assert result['checkpoint_original_hash_unchanged'] and not events
    a.summary.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='normalized_local_timing_or_endpoint_paths'}))
finally:
    cp.close();work.cleanup()
