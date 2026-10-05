from scripts.frank_shadow_service import snapshot_health,atomic_json,ForwardTransport
from scripts.frank_shadow_launchagent import configuration,IDENTIFIER
from mission_agent.db.repository import Repository
from mission_agent.frank.store import FrankStore
from mission_agent.hashing import digest
import json

def test_shadow_configuration_constrained(tmp_path):
 c=configuration(tmp_path,tmp_path/'state',tmp_path/'manual',tmp_path/'raw',tmp_path/'processed')
 assert c['Label']==IDENTIFIER and c['KeepAlive'] and c['RunAtLoad']
 assert 'scripts.frank_shadow_service' in c['ProgramArguments']
 assert all(x not in str(c) for x in ['Gmail','ChatGPT','production'])
 assert ForwardTransport('test-run',api=object()).namespace=='runtime-v2-test/frank-forward-shadow/test-run'

def test_health_counts_only_real_observations(tmp_path):
 repo=Repository(tmp_path/'db.sqlite');s=FrankStore(repo)
 for sig,kind,obs in [('seed','ACTIVE_SWAP_LIKE',None),('real','PASSIVE_RECEIPT_LIKE',{'detected_at':'1','normalized_at':'2'})]:
  e={'signature':sig,'slot':1,'block_time':0,'mechanical_classification':kind};e['evidence_sha256']=digest(e);s.put(e,observation=obs)
 h=snapshot_health(repo,{});assert h['new_signatures']==1 and h['passive_count']==1 and h['active_count']==0;repo.close()

def test_health_replacement_is_readable(tmp_path):
 p=tmp_path/'health.json';atomic_json(p,{'poll':1});atomic_json(p,{'poll':2});assert json.loads(p.read_text())=={'poll':2};assert p.stat().st_mode&0o777==0o600


def test_transport_rejects_nonforward_before_remote(tmp_path,monkeypatch):
 from scripts import frank_shadow_service as module
 repo=Repository(tmp_path/'forward.sqlite');FrankStore(repo);repo.close()
 monkeypatch.setattr(module,'build_batch',lambda *args:{'items':[{'payload':{'signature':'historical'}}]})
 monkeypatch.setattr(module,'validate_shadow_batch',lambda b:None)
 monkeypatch.setattr(module,'ForwardTransport',lambda *args:(_ for _ in ()).throw(AssertionError('remote must not be constructed')))
 import pytest
 with pytest.raises(ValueError,match='REAL_FORWARD_ACTIVE_OBSERVATION_REQUIRED'):module.transport_once(tmp_path,'test')
