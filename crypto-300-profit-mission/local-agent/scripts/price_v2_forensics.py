"""Explicit read-only exposed-partition forensics. No new rule config or optimizer."""
import argparse,json,time,resource
from pathlib import Path
from mission_agent.market.forensics.guard import protected_hashes,preservation,ForensicGuard,FREEZE
from mission_agent.market.forensics.analyze import reconstruct,miss_causes,path_sanity,WINDOWS,MISSES
from mission_agent.market.forensics.metrics import wilson,suspicious
from mission_agent.market.calibration.contract import read_winner,immutable_json,MODULE
from mission_agent.hashing import canonical


def run(root,output):
    if output.resolve().is_relative_to(root.resolve()):raise ValueError('OUTPUT_MUST_NOT_OVERWRITE_BASELINE_EVIDENCE')
    output.mkdir(parents=True,exist_ok=True,mode=0o700)
    if (output/'summary.json').exists():raise ValueError('IMMUTABLE_FORENSIC_RESULT_ALREADY_EXISTS')
    frozen=protected_hashes();guard=ForensicGuard(root,frozen);guard.install()
    wall=time.monotonic();cpu=time.process_time()
    winner,commit=read_winner(MODULE/'config/price_rule_v2_candidate.json')
    original_cal=json.loads((MODULE/'config/price_rule_v2_calibration_result.json').read_text())
    original_val=json.loads((MODULE/'config/price_rule_v2_validation_result.json').read_text())
    results={};traces=[]
    for role,expected in [('CALIBRATION',original_cal['winner']),('VALIDATION',original_val)]:
        values,trace=reconstruct(root,role,winner['thresholds']);results[role]=values;traces.extend(trace)
        for asset,value in values['assets'].items():
            if value['metrics']['P0']!=expected['metrics'][asset]:
                mismatched=[k for k in value['metrics']['P0'] if value['metrics']['P0'][k]!=expected['metrics'][asset][k]]
                raise ValueError('P0_FROZEN_METRIC_MISMATCH '+asset+' '+','.join(mismatched))
            if value['state_hash']!=expected['state_hashes'][asset]:raise ValueError('P0_FROZEN_STATE_HASH_MISMATCH '+asset)
            if role=='CALIBRATION' and value['feature_hash']!=original_cal['feature_hashes'][asset]:raise ValueError('P0_FROZEN_FEATURE_HASH_MISMATCH '+asset)
    classifications,grouping=miss_causes(results['VALIDATION'],traces)
    windows={}
    for name,(start,end) in WINDOWS.items():
        rows=[r for r in traces if start<=r['time']<=end]
        expected=(end-start)//60000+1
        if len(rows)!=expected or [r['time'] for r in rows]!=list(range(start,end+60000,60000)):raise ValueError('TRACE_MINUTE_COUNT_MISMATCH')
        immutable_json(output/(name+'.json'),rows)
        windows[name]={'rows':len(rows),'range':[start,end],'file':str(output/(name+'.json'))}
    sol=results['VALIDATION']['assets']['SOL'];graph=[]
    start,end=WINDOWS['early-merged']
    for ep in sol['episodes']['P0']:
        if ep['end_time']>=start and ep['first_material_time']<=end:graph.append(ep)
    immutable_json(output/'early-fragmentation-graph.json',graph)
    sanity={'early_merged':path_sanity(traces,*WINDOWS['early-merged']),
            'late_merged':path_sanity(traces,*WINDOWS['late-merged']),
            'cluster_0514_0524':path_sanity(traces,MISSES[0],MISSES[3])}
    sanity['cluster_0514_0524']['possible_episode_fragmentation']=__import__('decimal').Decimal(sanity['cluster_0514_0524']['range_return'])<__import__('decimal').Decimal('.04') and len([ep for ep in graph if MISSES[0]<=ep['first_material_time']<=MISSES[3]])>2
    sanity['onset_closes']={str(t):next(r['bar']['close'] for r in traces if r['time']==t) for t in MISSES}
    result={'status':'PHASE_3B_R_DIAGNOSIS_COMPLETE','freeze_commit':FREEZE,'winner_commit':commit,
            'winner_hash':winner['payload_sha256'],'results':results,'miss_classifications':classifications,'grouping':grouping,
            'windows':windows,'graph':graph,'path_sanity':sanity,'statistical_sensitivity':{'aggregate':wilson(15,20),'SOL':wilson(8,13)},
            'preservation':preservation(frozen),'io_evidence':{'baseline_paths_read':sorted(guard.reads),'audit_reads':0,'network_calls':0,'rejected':guard.violations},
            'resource':{'wall_seconds':str(time.monotonic()-wall),'cpu_seconds':str(time.process_time()-cpu),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
            'V2_VALIDATION_RESULT_PRESERVED':True,'V3':'NOT_AUTHORIZED','PHASE_3C':'NO_GO','PRODUCTION':'NO_GO'}
    immutable_json(output/'summary.json',result)
    print(json.dumps({'status':result['status'],'causes':[{k:x[k] for k in ('onset','primary','secondary')} for x in classifications],
                      'grouping':grouping,'resources':result['resource']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.root,a.output)
