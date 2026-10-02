import importlib.util
import pytest
np=pytest.importorskip('numpy')
from mission_agent.monster.screen_v2 import activations,configurations,Lifecycle,entity_id,midrank
from mission_agent.monster.features_v2 import features

def test_or_path_does_not_require_v1_volume_and_range():
 f=np.full((20,16),np.nan);f[:,14]=20000;f[:,2]=.1;r=np.zeros((20,5));r[:,0]=.99
 active=activations(f,r,configurations()[0]);assert active[:,0].all();assert not active[:,1:].any()

def test_future_perturbation_cannot_change_past_features():
 bars=[[i*3600000,1,1.1,.9,1+i*.001,1,100,10] for i in range(100)];btc={x[0]:1 for x in bars};a=features(bars,btc,0);bars[80][4]=5;b=features(bars,btc,0);np.testing.assert_equal(a[:80],b[:80])

def test_lifecycle_add_dedupe_gap_reset():
 s=Lifecycle(1);a=np.zeros((1,5),bool);a[0,0]=True;assert s.step(0,a,np.ones(1,bool))[0][1]=='PATH_ACTIVATED';assert s.step(3600000,a,np.ones(1,bool))==[];a[0,1]=True;assert s.step(7200000,a,np.ones(1,bool))[0][1]=='PATH_ADDED';assert s.step(14400000,a,np.ones(1,bool))[0][3]

def test_entity_conservative_and_grid():
 assert entity_id('spot','MMTUSDT','MMT',True)==entity_id('futures','MMTUSDT','MMT',True)
 assert entity_id('spot','1000XUSDT','1000X',True).startswith('ENTITY_AMBIGUOUS')
 assert entity_id('spot','MMTUSDT').startswith('ENTITY_AMBIGUOUS')
 assert len(configurations())==243
 assert np.isnan(midrank([1,2])).all()

def test_entity_events_keep_instrument_identity_and_merge_overlap():
 from scripts.monster_v2_replay import entity_events,metrics
 def event(i,anchor,peak):return {'event_id':str(i),'monster_entity_id':'coin:X','anchor_time':anchor,'peak_time':peak,'max7d':10,'crossings':{'2':anchor+2,'5':anchor+3,'10':peak,'20':None},'instrument_index':i}
 merged=entity_events([event(0,100,110),event(1,105,115),event(0,200,210)])
 assert len(merged)==2 and merged[0]['instrument_indices']==[0,1] and merged[0]['instrument_event_ids']==['0','1']
 result=metrics(merged,np.array([101,-1]));assert result['10']['events']==2 and result['10']['recall']==.5 and result['10']['strict_before2']==.5

def test_btc_gap_blocks_relative_return_without_blocking_absolute():
 bars=[[i*3600000,1,1.1,.9,1+i*.001,1,100,10] for i in range(30)];btc={x[0]:1 for x in bars};del btc[10*3600000]
 f=features(bars,btc,0);assert np.isfinite(f[12,1]) and np.isnan(f[12,8]);assert np.isfinite(f[15,8])

def test_chunked_replay_end_to_end_train_only(tmp_path,monkeypatch):
 import gzip,json,sqlite3
 from scripts import monster_v2_replay as replay
 from mission_agent.monster.features_v2 import features,HOUR
 monkeypatch.setattr(replay,'TRAIN_END',replay.START+14*24*HOUR)
 rows=[[replay.START-HOUR+i*HOUR,1,20 if i==52 else 1.1,.9,2 if i==52 else 1,1,20000 if i==52 else 1000,100 if i==52 else 1] for i in range(337)]
 btc={r[0]:1 for r in rows};data=features(rows,btc,rows[0][0]);db=sqlite3.connect(tmp_path/'features.sqlite');db.execute('CREATE TABLE feature(venue TEXT,week INTEGER,symbol INTEGER,body BLOB)');meta=[]
 for i in range(20):
  path=tmp_path/(str(i)+'.gz');path.write_bytes(gzip.compress(json.dumps(rows).encode()));meta.append({'index':i,'venue':'spot','symbol':f'X{i}USDT','bars_path':str(path),'monster_entity_id':f'coin:{i}','earliest_archive_month':'2021-01'})
  for week in range(2):
   chunk=data[week*168:(week+1)*168];db.execute('INSERT INTO feature VALUES(?,?,?,?)',('spot',week,i,gzip.compress(chunk.tobytes())))
 db.commit();db.close();(tmp_path/'feature-manifest.json').write_text(json.dumps(meta));reports=replay.replay(tmp_path,'train')
 assert len(reports)==243 and reports[0]['entity']['20']['events']==20
 assert reports[0]['entity']['20']['recall']==1 and reports[0]['entity']['20']['strict_before2']==0
 assert not (tmp_path/'validation-result.json').exists()
