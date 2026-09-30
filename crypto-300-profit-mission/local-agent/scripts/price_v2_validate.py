"""One-shot held-out gate; exactly one committed sealed winner. No optimizer import."""
import argparse
from pathlib import Path
from mission_agent.market.calibration.contract import read_winner,Partition,immutable_json
from mission_agent.market.calibration.replay import prepare,score
from mission_agent.hashing import seal


def run(root,winner_path,role):
    winner,commit=read_winner(winner_path)
    if role=='AUDIT':
        import json
        prior=json.loads((root/'validation-result.json').read_text())
        if prior['status']!='VALIDATION_PASS' or prior['winner_hash']!=winner['payload_sha256']:raise ValueError('AUDIT_REQUIRES_SAME_WINNER_VALIDATION_PASS')
    receipt=root/(role.lower()+'-opened.json')
    immutable_json(receipt,seal({'winner_hash':winner['payload_sha256'],'winner_commit':commit,'role':role}))
    partition=Partition(root,role);prepared=prepare(partition)
    result,events=score(prepared,winner['thresholds'],partition.config)
    result.update({'winner_hash':winner['payload_sha256'],'winner_commit':commit,'partition_hash':partition.receipt['payload_sha256'],
                   'status':role+'_PASS' if not result['failures'] else role+'_FAIL','audit_label':'AUDIT_NOT_BLIND' if role=='AUDIT' else 'CHRONOLOGICAL_HELD_OUT'})
    incremental,_=score(prepared,winner['thresholds'],partition.config,True)
    result['equivalence']={a:result['metrics'][a]['event_ids_hash']==incremental['metrics'][a]['event_ids_hash'] and result['state_hashes'][a]==incremental['state_hashes'][a] for a in partition.config['assets']}
    if not all(result['equivalence'].values()):result['status']='PHASE_3B_FAIL_EVALUATION_MODEL'
    if role=='AUDIT':
        from mission_agent.market.calibration.evaluate import stats
        result['v1_comparison']={a:stats(v['v1_events'],v['episodes'],partition.start,partition.end,len(v['v1_clusters'])) for a,v in prepared.items()}
        result['v1_clusters']={a:v['v1_clusters'] for a,v in prepared.items()}
        result['episodes']={a:v['episodes'] for a,v in prepared.items()}
        result['events']=events
    immutable_json(root/(role.lower()+'-result.json'),result)
    # Byte-level winner recheck after evaluation. Audit can only write its own result.
    after,_=read_winner(winner_path)
    if after!=winner:raise ValueError('PHASE_3B_FAIL_DATA_LEAKAGE_WINNER_MUTATED')
    print(result['status'],result['aggregate'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--winner',type=Path,required=True)
    p.add_argument('--role',choices=['VALIDATION','AUDIT'],default='VALIDATION')
    a=p.parse_args();run(a.root,a.winner,a.role)
