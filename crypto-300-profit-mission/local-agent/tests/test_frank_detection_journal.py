import pytest
from mission_agent.db.repository import Repository
from mission_agent.hashing import digest
from mission_agent.frank import collector as module

def evidence(sig,slot):
 e={'signature':sig,'slot':slot,'block_time':1,'mechanical_classification':'UNKNOWN','token_balance_deltas':[]};return {**e,'evidence_sha256':digest(e)}

class RPC:
 def signatures(self,**kwargs):return [{'signature':'new'},{'signature':'seed'}]
 def transaction(self,sig):return {'raw':sig}

def test_detection_survives_raw_before_sqlite_crash(tmp_path,monkeypatch):
 monkeypatch.setattr(module,'verify_acceptance',lambda _:None);monkeypatch.setattr(module,'normalize',lambda sig,tx:evidence(sig,2));monkeypatch.setattr(module,'clusters',lambda rows:[])
 stamps=iter([10.,20.,30.,40.]);monkeypatch.setattr(module.time,'time',lambda:next(stamps))
 repo=Repository(tmp_path/'db.sqlite');c=module.FrankCollector(repo,tmp_path/'raw',{},RPC(),durable_detection=True);c.store.put(evidence('seed',1),advance=True)
 original=c.store.put
 monkeypatch.setattr(c.store,'put',lambda *a,**k:(_ for _ in ()).throw(RuntimeError('crash_before_sqlite')))
 with pytest.raises(RuntimeError,match='crash_before_sqlite'):c.cycle()
 assert c.store.cursor()['signature']=='seed' and (tmp_path/'raw/new.json.gz').is_file()
 monkeypatch.setattr(c.store,'put',original);result=c.cycle();assert result['normalized']==1 and result['latencies'][0]['detected_at']=='10.0'
 assert repo.db.execute('SELECT detected_at FROM frank_observations WHERE signature=?',('new',)).fetchone()[0]=='10.0';repo.close()
