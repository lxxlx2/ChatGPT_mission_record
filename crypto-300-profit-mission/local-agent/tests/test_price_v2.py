"""Offline V2 contract, episode lifecycle, leakage and equivalence tests."""
import json
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
import pytest
from mission_agent.market.bar import MINUTE,Bar
from mission_agent.market.calibration.contract import contract,CalibrationOnly,Partition,immutable_json,FREEZE
from mission_agent.market.calibration.episodes import PricePoint,GroundTruth,Activations,RuleSignal,PriceFeatures,material
from mission_agent.market.calibration.signals import configs,projection,selector,signal
from mission_agent.market.calibration.replay import activate
from mission_agent.market.calibration.evaluate import stats,aggregate,gates,rank
from mission_agent.hashing import seal


def point(i,move='.04',other=None):
    f={'missing_data':False,'return_1h':move,'return_4h':'0','return_15m':'0','return_24h':'0','return_5m':'0',
       'reversal_15m':'0','gt_breakout_three':False,'breakout_two':False,'realized_vol_5m':'.01',
       'trailing_24h_vol_median':'.01','distance_from_24h_high':'0','distance_from_24h_low':'0',
       'relative_return_vs_btc_1h':'0','relative_return_vs_btc_4h':'0'}
    if other:f.update(other)
    return PricePoint('BTC',i*MINUTE,'100',f,'0','0',0,'a'*64,0)


def gt_sequence(values):
    gt=GroundTruth('BTC')
    for i,value in enumerate(values):gt.step(point(i,value))
    gt.finish(len(values)*MINUTE,True)
    return gt.episodes


def test_freeze_contract_324_unique_global_configs():
    cfg=contract();grid=configs(cfg)
    assert len(grid)==len({tuple(x.values()) for x in grid})==324
    assert cfg['assets']==['BTC','ETH','SOL','BNB']
    assert cfg['partitions']['AUDIT'][1]==1790747820000


def test_gt_90_minute_signal_one_episode():
    eps=gt_sequence(['.04']*90)
    assert len(eps)==1 and eps[0]['first_material_time']==0
    assert eps[0]['episode_type_set']==['FAST_MOVE']

@pytest.mark.parametrize('inactive',[1,15,29])
def test_gt_flicker_keeps_episode(inactive):
    assert len(gt_sequence(['.04']+['0']*inactive+['.04']))==1

@pytest.mark.parametrize('inactive',[30,31,60])
def test_gt_completed_reset_new_episode(inactive):
    assert len(gt_sequence(['.04']+['0']*inactive+['.04']))==2


def test_gt_material_reversal_immediate():
    eps=gt_sequence(['.04']*10+['-.04']*10)
    assert len(eps)==2 and [e['direction'] for e in eps]==['UP','DOWN']
    assert eps[1]['first_material_time']==10*MINUTE


def test_gt_multi_family_union_and_causal_onset():
    engine=GroundTruth('BTC');engine.step(point(0));engine.step(point(1,other={'return_4h':'.08'}));engine.finish(2*MINUTE,True)
    assert engine.episodes[0]['episode_type_set']==['FAST_MOVE','MEDIUM_MOVE']
    assert engine.episodes[0]['first_material_time']==0
    assert D(engine.episodes[0]['peak_magnitude'])==D('.08')


def test_gt_conflict_priority_preserves_first_family_direction():
    engine=GroundTruth('BTC');engine.step(point(0,other={'return_4h':'-.08'}));engine.finish(MINUTE,True)
    assert engine.conflicts==1 and engine.episodes[0]['direction']=='UP'
    assert engine.episodes[0]['episode_type_set']==['FAST_MOVE']


def test_candidate_r4_84_minute_persistence_one_activation():
    engine=Activations('SOL')
    for i in range(84):engine.step(RuleSignal(i*MINUTE,8,0))
    assert len(engine.events)==1 and engine.events[0]['rule_ids']==['R4']


def test_candidate_rule_added_and_reversal_without_cooldown():
    engine=Activations('ETH');engine.step(RuleSignal(0,8,0));engine.step(RuleSignal(MINUTE,9,0));engine.step(RuleSignal(2*MINUTE,0,1))
    assert [e['activation_reason'] for e in engine.events]==['ACTIVATION','RULE_ADDED','REVERSAL']
    assert engine.episode_count==2

@pytest.mark.parametrize('quiet,expected',[(29,1),(30,2)])
def test_candidate_reset_boundary(quiet,expected):
    engine=Activations('SOL');engine.step(RuleSignal(0,8,0))
    for i in range(1,quiet+1):engine.step(RuleSignal(i*MINUTE,0,0))
    engine.step(RuleSignal((quiet+1)*MINUTE,8,0))
    assert len(engine.events)==expected


def test_individual_rule_rearm_while_another_rule_sustains_episode():
    engine=Activations('SOL');engine.step(RuleSignal(0,9,0))
    for i in range(1,31):engine.step(RuleSignal(i*MINUTE,8,0))
    engine.step(RuleSignal(31*MINUTE,9,0))
    assert engine.episode_count==1 and engine.events[-1]['rule_ids']==['R1']


def test_sparse_batch_incremental_states_and_ids_equal():
    cfg=contract();params=configs(cfg)[0]
    # projection R4 first level index9; includes long persistence and reset.
    rows=[{'time':0,'end':83*MINUTE,'up':1<<9,'down':0},
          {'time':84*MINUTE,'end':114*MINUTE,'up':0,'down':0},
          {'time':115*MINUTE,'end':160*MINUTE,'up':0,'down':1<<9}]
    a=activate('SOL',rows,params,cfg);b=activate('SOL',rows,params,cfg,True)
    assert a==b and len(a[0])==2
    assert len({e['event_id'] for e in a[0]})==2


def test_sparse_expiry_with_continuous_other_rule():
    cfg=contract();params=configs(cfg)[0]
    rows=[{'time':0,'end':MINUTE,'up':(1<<0)|(1<<9),'down':0},
          {'time':2*MINUTE,'end':60*MINUTE,'up':1<<9,'down':0},
          {'time':61*MINUTE,'end':120*MINUTE,'up':(1<<0)|(1<<9),'down':0}]
    assert activate('SOL',rows,params,cfg)==activate('SOL',rows,params,cfg,True)

@pytest.mark.parametrize('role',['validation','audit','validation/calibration'])
def test_optimizer_cannot_load_other_paths(tmp_path,role):
    with pytest.raises((ValueError,FileNotFoundError)):CalibrationOnly(tmp_path/role)


def test_optimizer_copied_validation_receipt_rejected(tmp_path):
    directory=tmp_path/'calibration';directory.mkdir()
    (directory/'partition.json').write_text(json.dumps(seal({'role':'VALIDATION','range':[1785563820000,1788155820000],'freeze_commit':FREEZE})))
    with pytest.raises(ValueError,match='ROLE_RANGE'):CalibrationOnly(directory)

@pytest.mark.parametrize('value',[{},[],{'event_type':'RAW_PRICE_CANDIDATE'},{'episode_id':'gt'}])
def test_gt_and_candidate_builder_cannot_read_each_others_outputs(value):
    with pytest.raises(TypeError):GroundTruth('BTC').step(value)
    with pytest.raises(TypeError):projection(value,contract())
    with pytest.raises(TypeError):Activations('BTC').step(value)


def test_optimizer_requires_calibration_capability():
    from mission_agent.market.calibration.optimizer import optimize
    with pytest.raises(TypeError):optimize(object())


def test_immutable_winner_cannot_overwrite(tmp_path):
    path=tmp_path/'winner.json';immutable_json(path,{'one':1})
    with pytest.raises(FileExistsError):immutable_json(path,{'one':2})
    assert json.loads(path.read_text())=={'one':1}


def test_validation_seals_attempt_before_partition_open_and_rejects_repeat(tmp_path,monkeypatch):
    import scripts.price_v2_validate as runner
    winner={'payload_sha256':'abc','thresholds':{},'event_type':'PRICE_RULE_V2_CANDIDATE'}
    monkeypatch.setattr(runner,'read_winner',lambda _: (winner,'commit'))
    opened=[]
    def denied(*args):opened.append(1);raise ValueError('stop before data')
    monkeypatch.setattr(runner,'Partition',denied)
    with pytest.raises(ValueError):runner.run(tmp_path,tmp_path/'winner','VALIDATION')
    with pytest.raises(FileExistsError):runner.run(tmp_path,tmp_path/'winner','VALIDATION')
    assert opened==[1]


def test_validation_cli_accepts_exactly_one_winner():
    import subprocess,sys,os
    result=subprocess.run([sys.executable,'scripts/price_v2_validate.py','--root','x','--winner','a','b'],capture_output=True,text=True,env={**os.environ,'PYTHONPATH':str(Path.cwd())})
    assert result.returncode==2 and 'unrecognized arguments' in result.stderr


def test_hit_window_direction_and_late_not_primary_credit():
    episodes=[{'episode_id':'e','first_material_time':20*MINUTE,'direction':'UP'}]
    def event(t,d='UP'):return {'time':t*MINUTE,'direction':d,'event_id':str(t)+d,'episode_id':'c','rule_ids':['R1']}
    result=stats([event(21)],episodes,0,100*MINUTE,1)
    assert result['episode_hit']==0 and result['late_5m_diagnostic']==1
    assert stats([event(5)],episodes,0,100*MINUTE,1)['episode_hit']==1
    assert stats([event(4),event(20,'DOWN')],episodes,0,100*MINUTE,1)['episode_hit']==0


def test_noise_gate_rejects_flood_even_perfect_recall():
    m={'episode_count':20,'episode_hit':20,'median_day':'1','p95_day':1,'max_day':155}
    total={'episode_count':20,'episode_hit':20,'combined_p95_day':1}
    assert gates({'SOL':m},total)==['SOL_MAX_LOAD']


def test_zero_ground_truth_never_passes():
    assert 'AGGREGATE_RECALL' in gates({}, {'episode_count':0,'episode_hit':0,'combined_p95_day':0})


def test_winner_rank_exact_fraction_and_higher_threshold_tie():
    def row(x):return {'metrics':{'BTC':{'episode_count':10,'episode_hit':9}},'aggregate':{'episode_count':10,'episode_hit':9,'combined_p95_day':2,'total_candidate_episodes':3},'thresholds':{'R1':x}}
    assert rank(row('.03'),['R1'])>rank(row('.02'),['R1'])


def test_v1_v2_parallel_projection_does_not_modify_features():
    from mission_agent.market.rules import hits
    p=point(0,other={'return_24h':'.13'});before=dict(p.features)
    result=projection(p,contract());assert 'R4' in hits(p.features,'BTC')
    assert p.features==before and result[2]&8
    engine=Activations('BTC');indices=selector(configs(contract())[0],contract())
    for i in range(84):engine.step(signal(i*MINUTE,result[0],result[1],indices))
    assert len(engine.events)==1


def test_feature_engine_incremental_provisional_does_not_change_result():
    a=PriceFeatures();b=PriceFeatures()
    for i in range(1500):
        bar=Bar('BTC','binance_spot','BTCUSDT',i*MINUTE,'100','100','100','100','1')
        assert b.push(replace(bar,is_closed=False)) is None
        assert a.push(bar)==b.push(bar)


def test_winner_committed_bytes_cannot_be_mutated(tmp_path,monkeypatch):
    import mission_agent.market.calibration.contract as module
    from mission_agent.hashing import digest
    frozen=seal({'event_type':'PRICE_RULE_V2_CANDIDATE','freeze_commit':FREEZE,'search_config_hash':digest(contract()),'thresholds':{'R2':'.04'}})
    path=tmp_path/'winner.json';immutable_json(path,frozen);committed=path.read_bytes()
    contract_original=contract()
    monkeypatch.setattr(module,'MODULE',tmp_path)
    monkeypatch.setattr(module,'contract',lambda:contract_original)
    def command(args,**kwargs):return 'commit' if '--format=%H' in args else committed
    monkeypatch.setattr(module.subprocess,'check_output',command)
    assert module.read_winner(path)[0]==frozen
    altered=seal({k:v for k,v in frozen.items() if k!='payload_sha256'}|{'thresholds':{'R2':'.05'}})
    path.write_text(json.dumps(altered))
    with pytest.raises(ValueError,match='MUTATED'):module.read_winner(path)


def test_audit_cannot_mutate_committed_winner(tmp_path,monkeypatch):
    import scripts.price_v2_validate as runner
    from mission_agent.market.calibration.evaluate import aggregate
    winner={'payload_sha256':'winner','thresholds':{}}
    p=tmp_path/'winner';p.write_bytes(b'committed immutable winner\n');before=p.read_bytes()
    (tmp_path/'validation-result.json').write_text(json.dumps({'status':'VALIDATION_PASS','winner_hash':'winner'}))
    monkeypatch.setattr(runner,'read_winner',lambda _: (winner,'commit'))
    class Capability:
        config={'assets':[]};receipt={'payload_sha256':'partition'};start=0;end=1
    monkeypatch.setattr(runner,'Partition',lambda *args:Capability())
    monkeypatch.setattr(runner,'prepare',lambda _: {})
    monkeypatch.setattr(runner,'score',lambda *args: ({'failures':[],'metrics':{},'state_hashes':{},'aggregate':{}},{}))
    runner.run(tmp_path,p,'AUDIT')
    assert p.read_bytes()==before
    assert (tmp_path/'audit-result.json').exists()


def test_freeze_committed_documents_cannot_be_changed(tmp_path,monkeypatch):
    import mission_agent.market.calibration.contract as module
    frozen={name:(module.MODULE/name).read_bytes() for name in module.FILES}
    for name,data in frozen.items():
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    monkeypatch.setattr(module,'MODULE',tmp_path)
    monkeypatch.setattr(module.subprocess,'check_output',lambda args,**kwargs:frozen[args[2].split(':',1)[1].removeprefix(module.REPO_PATH)])
    assert module.contract()['configs']==324
    (tmp_path/module.FILES[0]).write_bytes(b'{}')
    with pytest.raises(ValueError,match='FREEZE_MUTATED'):module.contract()

@pytest.mark.parametrize('role',['validation','audit'])
def test_process_io_guard_rejects_held_out_reads(tmp_path,role):
    from mission_agent.market.calibration.contract import LeakageGuard
    guard=LeakageGuard(tmp_path)
    with pytest.raises(ValueError,match='DATA_LEAKAGE'):guard.check('open',(str(tmp_path/role/'BTC-canonical.json.gz'),'r',0))
    guard.check('open',(str(tmp_path/'calibration'/'BTC-canonical.json.gz'),'r',0))
    assert len(guard.rejected)==1 and len(guard.reads)==1
