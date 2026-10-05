import copy,json
from pathlib import Path
import pytest
np=pytest.importorskip('numpy')
from mission_agent.monster.screen_v3 import configurations,Confirmations,supplemental,dual_confirmation,daily_stats,winner,validation_status,search

def inputs(n=20):
 f=np.zeros((n,16));f[:,0]=.03;f[:,1]=.1;f[:,2]=.1;f[:,4]=3;f[:,5]=2;f[:,6]=2;f[:,8]=.1;f[:,9]=.1;f[:,10]=.1;f[:,13]=3000;f[:,14]=200000;f[:,15]=1;r=np.ones((n,5))*.99;x=np.ones((n,4));x[:,2]=100;x[:,3]=.99
 return f,r,x,np.arange(n),['spot']*n

def test_finite_architecture_grid():
 c=configurations();assert len(c)==72 and len(set(c))==72;assert c[0]==(2,50000,'QUALITY_OR_RS',.5,False);assert search()['entity_ceiling']=={'median':100,'p95':150}

def test_persistence_no_single_bar_spike_and_gap_reset():
 f,r,x,e,v=inputs();s=Confirmations(20,configs=[configurations()[0]]);assert not s.step(f,r,x,e,v)[0].any();assert s.step(f,r,x,e,v)[0].all();g=f.copy();g[:]=np.nan;assert not s.step(g,r,x,e,v)[0].any();assert not s.step(f,r,x,e,v)[0].any();assert s.step(f,r,x,e,v)[0].all()

def test_volume_quality_liquidity_proxy_and_unknown_age():
 f,r,x,e,v=inputs();cfg=(2,100000,'QUALITY',.5,False);s=Confirmations(20,configs=[cfg]);f[:,14]=1000;s.step(f,r,x,e,v);assert not s.step(f,r,x,e,v)[0].any()
 f[:,14]=200000;x[:,2]=1;s=Confirmations(20,configs=[cfg]);s.step(f,r,x,e,v);assert not s.step(f,r,x,e,v)[0].any()
 x[:,2]=100;x[:,3]=np.nan;f[:,13]=np.nan;s=Confirmations(20,configs=[cfg]);s.step(f,r,x,e,v);assert not s.step(f,r,x,e,v)[0].any()

def test_verified_young_age_allows_short_quote_history():
 f,r,x,e,v=inputs();f[:,13]=50;f[:,14]=60000;x[:,3]=np.nan;cfg=(2,100000,'QUALITY',.5,False);s=Confirmations(20,configs=[cfg]);s.step(f,r,x,e,v);assert s.step(f,r,x,e,v)[0].all()

def test_conditional_futures_not_universal_and_no_identity_guess():
 f,r,x,e,v=inputs();a,p=dual_confirmation(f,e,v);assert not a.any();s=Confirmations(20,configs=[(2,100000,'QUALITY',.5,True)]);s.step(f,r,x,e,v);assert s.step(f,r,x,e,v)[0].all()
 e[1]=e[0];v[1]='futures';f[1,1]=-.2;a,p=dual_confirmation(f,e,v);assert a[0] and not p[0]
 s=Confirmations(20,configs=[(2,100000,'QUALITY',.5,True)]);s.step(f,r,x,e,v);assert not s.step(f,r,x,e,v)[0][0,0]
 f[1,1]=.2;a,p=dual_confirmation(f,e,v);assert p[0]

def test_future_perturbation_supplemental_and_gap():
 b=[[i*3600000,1,1.2,.8,1,10,100+i,20] for i in range(200)];a=supplemental(b);c=copy.deepcopy(b);c[190][6]=1e12;c[190][2]=5;z=supplemental(c);np.testing.assert_equal(a[:190],z[:190]);assert a[168,3]==1
 g=b[:100]+b[101:];assert np.isnan(supplemental(g)[-1,3])

def test_causal_close_retention_overextension():
 f,r,x,e,v=inputs();s=Confirmations(20,configs=[configurations()[0]]);s.step(f,r,x,e,v);f[:,15]=.5;assert not s.step(f,r,x,e,v)[0].any()
 f,r,x,e,v=inputs();s=Confirmations(20,configs=[configurations()[0]]);s.step(f,r,x,e,v);f[:,0]=.6;assert not s.step(f,r,x,e,v)[0].any()

def test_rs_independent_family_requires_market_not_beta():
 f,r,x,e,v=inputs();f[:,14]=20000;s=Confirmations(20,configs=[configurations()[0]]);s.step(f,r,x,e,v);assert not s.step(f,r,x,e,v)[0].any();f[0,1]=.3;s=Confirmations(20,configs=[configurations()[0]]);s.step(f,r,x,e,v);assert s.step(f,r,x,e,v)[0][0,0]

def test_calendar_zero_days_median_nearest_rank_p95():
 assert daily_stats([0]*19+[20])=={'median':0,'p95':0};assert daily_stats([0,2])['median']==1

def report(id,recall=1,median=10,p95=20):
 e={str(t):{'events':20 if t==5 else 7 if t==10 else 2,'recall':recall,'strict_before2':recall,'lead_hours':{'2':5}} for t in [5,10,20]}
 return {'config_id':id,'entity':e,'median_entities_day':median,'p95_entities_day':p95,'ceiling_pass':median<=100 and p95<=150,'years':{'2021':{'entity':e}}}

def test_winner_no_manual_choice_ceiling_and_no_winner():
 bad=report('bad',1,101,150);good=report('good',.9);assert winner([bad,good])==good;assert winner([bad]) is None
 a=report('a',1,20);b=report('b',.9,1);assert winner([b,a])==a;assert winner([a,b])==a

def test_validation_gate_samples_and_no_winner_lock(tmp_path,monkeypatch):
 from scripts import monster_v3_replay as replay
 module=tmp_path/'module';(module/'config').mkdir(parents=True);(module/'config/monster_d1_v3_winner.json').write_text(json.dumps({'status':'MONSTER_D1_V3_NEEDS_REDESIGN','winner':None}));monkeypatch.setattr(replay,'MODULE',module)
 with pytest.raises(AssertionError,match='VALIDATION_LOCK_NO_WINNER'):replay.locked_winner(tmp_path)
 r=report('a');assert validation_status(r)=='MONSTER_D1_V3_VALIDATION_PASS';r['entity']['5']['events']=19;assert validation_status(r)=='INSUFFICIENT_DATA'

def test_before2x_strict_and_year_anchor_split():
 from scripts.monster_v2_replay import metrics,HOUR
 e=[{'max7d':10,'crossings':{'2':2*HOUR,'5':3*HOUR,'10':4*HOUR,'20':None},'peak_time':4*HOUR}];m=metrics(e,np.array([2*HOUR]));assert m['5']['recall']==1 and m['5']['strict_before2']==0;assert m['5']['lead_hours']['2']==0

def test_deterministic_same_input():
 f,r,x,e,v=inputs();a=Confirmations(20);b=Confirmations(20)
 for i in range(5):np.testing.assert_equal(a.step(f,r,x,e,v)[0],b.step(f,r,x,e,v)[0])

def test_config_freeze_drift_and_unique_entity_count(tmp_path,monkeypatch):
 from scripts import monster_v3_replay as replay
 module=tmp_path/'module';module.mkdir();(module/'x').write_text('changed');(tmp_path/'freeze.json').write_text(json.dumps({'commit':'sha','files':{'x':'bad'}}));monkeypatch.setattr(replay,'MODULE',module);monkeypatch.setattr(replay.subprocess,'check_output',lambda *a,**k:b'original')
 with pytest.raises(AssertionError,match='V3_FREEZE_DRIFT'):replay.verify_freeze(tmp_path)
 mapping=np.array([0,0,1]);counts=np.zeros(2,bool);np.logical_or.at(counts,mapping,np.array([True,True,False]));assert counts.sum()==1
