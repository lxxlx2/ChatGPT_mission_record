"""Small end-to-end replay proof; production frozen kernel remains unchanged."""
import gzip,json,sqlite3
import pytest
np=pytest.importorskip('numpy')
from scripts import monster_v3_replay as replay
from mission_agent.monster.screen_v3 import configurations

def fixture(tmp_path,monkeypatch):
 source=tmp_path/'source';root=tmp_path/'run';source.mkdir();root.mkdir();monkeypatch.setattr(replay,'WARMUP',replay.START);monkeypatch.setattr(replay,'TRAIN_END',replay.START+14*replay.DAY);monkeypatch.setattr(replay,'health',lambda:{'pid':1,'poll_count':1,'rpc_429_count':0})
 # Short fixture has no2022/2023 calendar; isolate production full-three-year stats.
 original_stats=replay.daily_stats;monkeypatch.setattr(replay,'daily_stats',lambda c:original_stats(c) if len(c) else {'median':None,'p95':None})
 meta=[];db=sqlite3.connect(source/'features.sqlite');db.execute('CREATE TABLE feature(week INTEGER,symbol INTEGER,body BLOB)');aux=sqlite3.connect(root/'supplemental.sqlite');aux.execute('CREATE TABLE feature(week INTEGER,symbol INTEGER,body BLOB)')
 for i in range(20):
  meta.append({'index':i,'venue':'spot' if i%2==0 else 'futures','symbol':str(i),'monster_entity_id':'verified:'+str(i//2)})
  for w in range(2):
   f=np.zeros((168,16),np.float32);f[:,0]=.03;f[:,1]=.1;f[:,2]=.1;f[:,4]=3;f[:,5]=2;f[:,6]=2;f[:,8]=.1;f[:,9]=.1;f[:,10]=.1;f[:,13]=3000;f[:,14]=200000;f[:,15]=1;a=np.ones((168,4),np.float32);a[:,2]=100;a[:,3]=.99
   db.execute('INSERT INTO feature VALUES(?,?,?)',(w,i,gzip.compress(f.tobytes())));aux.execute('INSERT INTO feature VALUES(?,?,?)',(w,i,gzip.compress(a.tobytes())))
 db.commit();db.close();aux.commit();aux.close();(source/'feature-manifest.json').write_text(json.dumps(meta));e={'event_id':'e','monster_entity_id':'verified:0','anchor_time':replay.START,'peak_time':replay.START+5*replay.HOUR,'max7d':10,'crossings':{'2':replay.START+2*replay.HOUR,'5':replay.START+3*replay.HOUR,'10':replay.START+4*replay.HOUR,'20':None},'instrument_index':0};(source/'train-instrument-events.json').write_text(json.dumps([e]));return source,root

def test_replay_calendar_year_entity_and_before2(tmp_path,monkeypatch):
 source,root=fixture(tmp_path,monkeypatch);r=replay.replay(source,root,'train',selected={'parameters':configurations()[0]})[0];assert r['days']==14;assert r['entity']['10']['prehit']==1 and r['entity']['10']['strict_before2']==1;assert r['years']['2021']['entity']['5']['events']==1;assert r['median_entities_day']==0
 data=np.load(root/'train-first-triggers.npz');assert data['daily_entity'][0,0]==10 and data['daily_instrument'][0,0]==20;assert not (root/'validation-instrument-events.json').exists()

def test_full_input_rerun_is_identical(tmp_path,monkeypatch):
 source,root=fixture(tmp_path,monkeypatch);a=replay.replay(source,root,'train',selected={'parameters':configurations()[0]});second=tmp_path/'rerun';second.mkdir();(second/'supplemental.sqlite').symlink_to(root/'supplemental.sqlite');b=replay.replay(source,second,'train',selected={'parameters':configurations()[0]});assert a==b

def test_validation_without_committed_winner_never_discovers_labels(tmp_path,monkeypatch):
 source,root=fixture(tmp_path,monkeypatch);monkeypatch.setattr(replay,'locked_winner',lambda root:(_ for _ in ()).throw(AssertionError('LOCKED')));monkeypatch.setattr(replay,'discover',lambda *a:pytest.fail('labels opened'))
 with pytest.raises(AssertionError,match='LOCKED'):replay.replay(source,root,'validation',selected={'config_id':'fake','parameters':configurations()[0]})
