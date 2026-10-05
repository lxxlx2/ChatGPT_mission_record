"""The optimizer API takes exactly a calibration capability, never another role."""
from .contract import CalibrationOnly,contract,FREEZE
from .replay import prepare,score
from .signals import configs
from .evaluate import rank
from ...hashing import digest,seal


def optimize(capability):
    if type(capability) is not CalibrationOnly:raise TypeError('OPTIMIZER_CALIBRATION_ONLY')
    cfg=contract();prepared=prepare(capability);leaderboard=[]
    for index,parameters in enumerate(configs(cfg)):
        result,_=score(prepared,parameters,cfg);result['config_id']=index
        leaderboard.append(result)
        if (index+1)%36==0:print(f'calibration evaluated {index+1}/324',flush=True)
    passing=[row for row in leaderboard if not row['failures']]
    winner=max(passing,key=lambda row:rank(row,cfg['tie_threshold_order'])) if passing else None
    # Equivalence is assessed without any validation input, for selected winner or
    # a fixed first-grid representative if calibration has no admissible config.
    selected=winner or leaderboard[0]
    incremental,_=score(prepared,selected['thresholds'],cfg,True)
    equivalence={a:incremental['metrics'][a]['event_ids_hash']==selected['metrics'][a]['event_ids_hash'] and incremental['state_hashes'][a]==selected['state_hashes'][a] for a in cfg['assets']}
    if not all(equivalence.values()):raise ValueError('PHASE_3B_FAIL_EVALUATION_MODEL_INCREMENTAL_DIVERGENCE')
    result={'freeze_commit':FREEZE,'partition_hash':capability.receipt['payload_sha256'],'search_config_hash':digest(cfg),
            'configs_evaluated':len(leaderboard),'configs_passing':len(passing),'winner':winner,
            'leaderboard':leaderboard,'episodes':{a:[ep for ep in v['episodes'] if capability.start<ep['first_material_time']<=capability.end] for a,v in prepared.items()},
            'input_hashes':{a:v['input_hash'] for a,v in prepared.items()},'feature_hashes':{a:v['feature_hash'] for a,v in prepared.items()},
            'conflict_counts':{a:v['gt_conflicts'] for a,v in prepared.items()},'equivalence':equivalence,
            'equivalence_config_id':selected['config_id'],'status':'CALIBRATION_WINNER' if winner else 'PHASE_3B_FAIL_NO_CALIBRATION_WINNER'}
    candidate=seal({'event_type':'PRICE_RULE_V2_CANDIDATE','freeze_commit':FREEZE,'search_config_hash':digest(cfg),
                    'calibration_result_hash':digest(result),'thresholds':winner['thresholds'],'config_id':winner['config_id']}) if winner else None
    return result,candidate
