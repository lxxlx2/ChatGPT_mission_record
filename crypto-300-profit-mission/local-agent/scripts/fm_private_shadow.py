"""Explicit manual private test batch/readback only; no GPT call or delivery."""
import argparse,json
from pathlib import Path
from mission_agent.db.repository import Repository
from mission_agent.queue.batch import build_batch,publish,item
from mission_agent.transport.github import GitHubTransport,RemoteError
from mission_agent.config import Config
from mission_agent.fm.queue import validate_shadow_batch
from mission_agent.hashing import canonical,verify,loads
from scripts.frank_probe import store

def run(root,run_id,db_name='frank500.sqlite',receipt_name='private-shadow-result.json'):
    repo=Repository(root/db_name);cfg=Config.for_remote(root)
    existing=repo.db.execute("SELECT payload_json FROM batches WHERE state='BUILT' ORDER BY generated_at,batch_id LIMIT 1").fetchone()
    batch=loads(existing[0]) if existing else build_batch(repo,cfg)
    if batch is None:raise ValueError('NO_PENDING_SHADOW_CANDIDATES')
    offline=validate_shadow_batch(batch);transport=GitHubTransport('mac',run_id)
    try:prior=transport.read(transport.branch,transport.namespace+'/ingest/current.json');expected=prior.blob_sha
    except RemoteError as exc:
        if exc.status!=404:raise
        expected=None
    publish(repo,transport,batch['batch_id'],expected_sha=expected)
    # Independent client restart/readback; archive immutable dedupe exact same publish.
    restarted=GitHubTransport('mac',run_id);actual=restarted.read_batch(batch['batch_id'])
    assert canonical(actual)==canonical(batch);before=transport.api.commits;again=transport.publish_batch(batch);assert transport.api.commits==before
    sizes=[len(canonical(x)) for x in batch['items']]
    result={'status':'PASS_PRIVATE_TEST_TRANSPORT','namespace':transport.namespace,'repository':'lxxlx2/crypto-monitor-runtime','branch':'mac-data','batch_id':batch['batch_id'],'item_count':batch['item_count'],'event_types':sorted({x['event_type'] for x in batch['items']}),'batch_bytes':len(canonical(batch)),'maximum_item_bytes':max(sizes),'readback_hash_verified':True,'restart_readback':True,'identical_republish_commits':transport.api.commits-before,'remote_write_commits':transport.api.commits,'remote_read_commit':again.commit_sha,'offline_contract':offline,'gmail_sends':0,'automation_mutations':0,'production_writes':0}
    store(root/receipt_name,result);repo.close();print(json.dumps(result))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--run-id',required=True);p.add_argument('--db-name',default='frank500.sqlite');p.add_argument('--receipt-name',default='private-shadow-result.json');a=p.parse_args();run(a.root,a.run_id,a.db_name,a.receipt_name)
