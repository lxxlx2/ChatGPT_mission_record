"""No market network: frozen priority reproduction and forensic-only guards."""
from pathlib import Path
import pytest
from mission_agent.market.forensics.policies import pick,CandidatePolicy,DiagnosticGT,expanded
from mission_agent.market.forensics.metrics import suspicious,classify,stability,wilson
from mission_agent.market.forensics.guard import ForensicGuard,protected_hashes,preservation
from mission_agent.market.calibration.episodes import GroundTruth,PricePoint
from mission_agent.market.calibration.contract import read_winner,MODULE
from mission_agent.market.bar import MINUTE
from mission_agent.market.calibration.episodes import material


def signals():
    return [{'name':'FAST_MOVE','active':True,'direction':'UP','magnitude':'.04','threshold':'.04','normalized_exceedance':'1'},
            {'name':'MEDIUM_MOVE','active':True,'direction':'DOWN','magnitude':'.14','threshold':'.07','normalized_exceedance':'2'}]


def point(i,reverse=False):
    features={'missing_data':False,'return_1h':'.04' if not reverse else '0','return_4h':'-.14','return_15m':'0','return_24h':'0','return_5m':'0',
              'reversal_15m':'0','gt_breakout_three':False,'breakout_two':False,'realized_vol_5m':'.01','trailing_24h_vol_median':'.01',
              'distance_from_24h_high':'0','distance_from_24h_low':'0','relative_return_vs_btc_1h':'0','relative_return_vs_btc_4h':'0'}
    return PricePoint('SOL',i*MINUTE,'100',features,'0','0',0,'hash',0)


def test_current_gt_priority_is_first_active_family():
    g=GroundTruth('SOL');g.step(point(0));assert g.active['direction']=='UP' and g.conflicts==1
    assert material(point(0))[0][0]=='FAST_MOVE'
    assert pick('P0',signals())==('UP','FAST_MOVE')


def test_lowest_rule_priority_opposes_larger_magnitude():
    rules=[dict(s,name=name) for s,name in zip(signals(),('R1','R4'))]
    engine=CandidatePolicy('SOL','P0');result=engine.step(0,rules)
    assert result['selected_direction']=='UP' and result['up_mask']==1 and result['down_mask']==8
    assert result['events'][0]['rule_ids']==['R1']


def test_gt_up_down_up_fragmentation_reproducible():
    engine=GroundTruth('SOL')
    for i,reverse in enumerate((False,True,False)):engine.step(point(i,reverse))
    engine.finish(3*MINUTE,True)
    assert [e['direction'] for e in engine.episodes]==['UP','DOWN','UP']
    edges=suspicious(engine.episodes)
    assert len(edges)==1 and edges[0]['opposite_durations_seconds']==[60]

@pytest.mark.parametrize('gap,opposite_duration,expected',[(10,5,True),(11,5,False),(10,6,False),(0,1,True)])
def test_suspicious_fragmentation_boundary(gap,opposite_duration,expected):
    eps=[{'episode_id':'a','direction':'UP','first_material_time':0,'end_time':MINUTE},
         {'episode_id':'b','direction':'DOWN','first_material_time':MINUTE,'end_time':MINUTE+opposite_duration*MINUTE},
         {'episode_id':'c','direction':'UP','first_material_time':MINUTE+gap*MINUTE,'end_time':20*MINUTE}]
    assert bool(suspicious(eps))==expected


def test_classifier_frozen_precedence_deterministic():
    evidence={'fragmentation':True,'candidate_conflict':True,'lifecycle':True,'late':True}
    first=classify(evidence)
    assert first==classify(evidence) and first['primary']=='B_GT_DIRECTION_CONFLICT_FRAGMENTATION'
    assert len(first['secondary'])==3


def test_classifier_cannot_hide_unknown():
    with pytest.raises(ValueError,match='UNEXPLAINED'):classify({})
    assert classify({'other_explanation':'explicit'})['primary']=='H_OTHER'

@pytest.mark.parametrize('policy',['P0','P1','P2','P3'])
def test_counterfactual_arbitration_deterministic(policy):
    assert pick(policy,signals(),'UP')==pick(policy,signals(),'UP')
    assert pick('P1',signals(),'UP')[0]=='UP'
    assert pick('P2',signals(),'UP')[0]=='DOWN'
    assert pick('P3',signals(),'UP')[0]=='UP'


def test_p4_one_envelope_with_opposite_subsignals():
    engine=DiagnosticGT('SOL','P4')
    engine.step(point(0),signals());engine.step(point(1,True),[signals()[1]]);engine.finish(2*MINUTE,True)
    assert len(engine.episodes)==1 and engine.episodes[0]['direction']=='ENVELOPE'
    assert engine.episodes[0]['onset_directions']==['DOWN','UP']


def test_p4_candidate_concurrent_events_one_envelope():
    rules=[dict(s,name=name) for s,name in zip(signals(),('R1','R4'))]
    engine=CandidatePolicy('SOL','P4');events=engine.step(0,rules)['events']
    assert len(events)==2 and len({e['episode_id'] for e in events})==1
    assert {e['direction'] for e in events}=={'UP','DOWN'}

@pytest.mark.parametrize('name',['price_rule_v3.json','PRICE_RULE_V3_CANDIDATE.json'])
def test_counterfactual_cannot_write_v3_config(tmp_path,name):
    guard=ForensicGuard(tmp_path,[])
    with pytest.raises(ValueError,match='V3_WRITE'):guard.check('open',(str(tmp_path/name),'w',0))


def test_audit_access_forbidden_and_symlink_resolved(tmp_path):
    audit=tmp_path/'audit';audit.mkdir();file=audit/'bars';file.touch();alias=tmp_path/'calibration';alias.symlink_to(audit)
    guard=ForensicGuard(tmp_path,[])
    with pytest.raises(ValueError,match='AUDIT_ACCESS'):guard.check('open',(str(alias/'bars'),'r',0))


def test_winner_config_write_forbidden():
    path=MODULE/'config/price_rule_v2_candidate.json';guard=ForensicGuard(MODULE,[str(path)])
    with pytest.raises(ValueError,match='FROZEN'):guard.check('open',(str(path),'w',0))
    winner,commit=read_winner(path);assert commit=='0b3d0cff2199c2bab42d07b42d4e5b8b9259e654'


def test_market_network_forbidden(tmp_path):
    with pytest.raises(ValueError,match='NETWORK'):ForensicGuard(tmp_path,[]).check('socket.connect',())


def test_wilson_and_90pct_sensitivity():
    agg=wilson(15,20);sol=wilson(8,13)
    assert agg['maximum_misses_at_90pct']==2 and sol['maximum_misses_at_90pct']==1
    assert float(agg['wilson95'][0])<.75<float(agg['wilson95'][1])


def test_expanded_signals_match_frozen_material_active_set():
    thresholds={'R1':'.03','R2':'.04','R3':'.08','R4':'.14','R7_multiplier':'3','R7_move':'.02'}
    families,rules=expanded(point(0),thresholds)
    assert [s['name'] for s in families if s['active']]==[s[0] for s in material(point(0))]
    assert rules[1]['active'] and rules[1]['direction']=='UP'

@pytest.mark.parametrize('policy',['P1','P2','P3','P4'])
def test_counterfactual_full_lifecycle_repeatability(policy):
    first=DiagnosticGT('SOL',policy);second=DiagnosticGT('SOL',policy)
    ca=CandidatePolicy('SOL',policy);cb=CandidatePolicy('SOL',policy)
    for i in range(90):
        raw=signals() if i<10 or i>=50 else []
        first.step(point(i),raw);second.step(point(i),raw)
        rules=[dict(s,name=name) for s,name in zip(raw,('R1','R4'))]
        assert ca.step(i*MINUTE,rules)==cb.step(i*MINUTE,rules)
    first.finish(90*MINUTE,True);second.finish(90*MINUTE,True)
    assert first.episodes==second.episodes and ca.events==cb.events


def test_threshold_late_classification_does_not_change_primary_window():
    explanation=classify({'late':True,'threshold_gap':True})
    assert explanation['primary']=='E_HIT_WINDOW_TIMING'
    assert explanation['secondary']==['A_TRUE_THRESHOLD_GAP']
