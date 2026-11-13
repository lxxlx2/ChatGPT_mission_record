"""Both providers replay original raw reads; no live network or frozen verdict."""
import io
import json
import urllib.error
import pytest
from mission_agent.meme.cluster import SolanaReadOnlyRPC, RPCError
from mission_agent.meme.job_checkpoint import JobCheckpoint, CheckpointRPC, CheckpointSecondaryRPC
from test_ca_unlimited_free_jobs import create, JOB, UNLIMITED

class Response:
    def __init__(self,result):self.result=result
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,*args):return json.dumps({'result':self.result}).encode()

def rpc(open_url):
    return SolanaReadOnlyRPC('https://fixture.invalid',fallback_endpoints=[],open_url=open_url,
                             min_interval=0,sleep=lambda delay:None)

def test_primary_and_secondary_raw_sequence_replay_without_wire_and_separate_counters(tmp_path):
    create(tmp_path)
    cp=JobCheckpoint(tmp_path,JOB,clock=lambda:100.)
    cp.begin('binding',UNLIMITED)
    requests=[]
    primary=CheckpointRPC(cp,rpc(lambda req,timeout:(requests.append('p'),Response({'value':'PRIMARY'}))[1]))
    secondary=CheckpointSecondaryRPC(cp,rpc(lambda req,timeout:(requests.append('s'),Response({'value':'SECONDARY'}))[1]))
    for client,expected in [(primary,'PRIMARY'),(secondary,'SECONDARY'),(primary,'PRIMARY'),(secondary,'SECONDARY')]:
        assert client.call('getMultipleAccounts',[[],{}])=={'value':expected}
    assert requests==['p','s','p','s']
    assert primary.calls==2 and secondary.calls==2
    assert cp.meta['wire_used']==2 and cp.meta['secondary_rpc']['wire_used']==2
    assert [e['request']['channel'] for e in cp.entries]==['rpc','secondary_rpc','rpc','secondary_rpc']
    cp.finish('ERROR');cp.close()
    cp=JobCheckpoint(tmp_path,JOB,clock=lambda:100.)
    cp.begin('binding',UNLIMITED)
    denied=lambda *a,**k:pytest.fail('REPLAY_MUST_NOT_SEND_WIRE')
    primary=CheckpointRPC(cp,rpc(denied));secondary=CheckpointSecondaryRPC(cp,rpc(denied))
    for client,expected,count in [(primary,'PRIMARY',2),(secondary,'SECONDARY',1),(primary,'PRIMARY',2),(secondary,'SECONDARY',2)]:
        assert client.call('getMultipleAccounts',[[],{}])=={'value':expected}
        assert client.calls==count
    cp.assert_can_publish()
    assert cp.replayed==4 and cp.meta['wire_used']==2 and cp.meta['secondary_rpc']['wire_used']==2
    cp.close()

def test_secondary_failure_and_safe_diagnostics_replay_then_success_clears_code(tmp_path):
    create(tmp_path)
    cp=JobCheckpoint(tmp_path,JOB,clock=lambda:100.);cp.begin('binding',UNLIMITED)
    fail=[True]
    def transport(req,timeout):
        if fail[0]:raise urllib.error.HTTPError(req.full_url,403,'PRIVATE_SECRET',{},io.BytesIO(b'SECRET_BODY'))
        return Response({'value':'OK'})
    secondary=CheckpointSecondaryRPC(cp,rpc(transport))
    with pytest.raises(RPCError):secondary.call('getMultipleAccounts',[['first'],{}])
    count=secondary.calls
    assert count>0 and secondary.last_wire_error_code=='HTTP_403'
    fail[0]=False
    assert secondary.call('getMultipleAccounts',[['second'],{}])=={'value':'OK'}
    assert secondary.last_wire_error_code is None
    assert cp.entries[0]['outcome']=='ERROR' and 'SECRET' not in json.dumps(list(cp.entries))
    cp.finish('ERROR');cp.close()
    cp=JobCheckpoint(tmp_path,JOB,clock=lambda:100.);cp.begin('binding',UNLIMITED)
    secondary=CheckpointSecondaryRPC(cp,rpc(lambda *a,**k:pytest.fail('NO_WIRE')))
    with pytest.raises(RPCError):secondary.call('getMultipleAccounts',[['first'],{}])
    assert secondary.calls==count and secondary.last_wire_error_code=='HTTP_403'
    assert secondary.call('getMultipleAccounts',[['second'],{}])=={'value':'OK'}
    assert secondary.calls==count+1 and secondary.last_wire_error_code is None
    cp.assert_can_publish();cp.close()
