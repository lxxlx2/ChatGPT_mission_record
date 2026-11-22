import json
import uuid
import pytest
from mission_agent.meme.cluster import RpcCache, SolanaReadOnlyRPC, WalletClusterAnalyzer, Holder
from mission_agent.meme.job_checkpoint import JobCheckpoint, CheckpointRPC, CheckpointError

OPTIONS={'commitment':'finalized','encoding':'jsonParsed','maxSupportedTransactionVersion':1}
TTL=3650*86400

class Response:
    def __init__(self,value):self.value=value
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,*args):return json.dumps(self.value).encode()

def rpc_with(wires,mode='normal'):
    def transport(req,timeout):
        q=json.loads(req.data);wires.append(q)
        if isinstance(q,list):
            rows=[{'jsonrpc':'2.0','id':x['id'],'result':{'signature':x['params'][0]}} for x in q][::-1]
            if mode=='duplicate':rows[0]['id']=rows[1]['id']
            if mode=='partial':rows[0]={'jsonrpc':'2.0','id':rows[0]['id'],'error':{'code':-32005,'message':'SECRET_PROVIDER_TEXT'}}
            if mode=='null':rows[0]['result']=None
            return Response(rows)
        return Response({'jsonrpc':'2.0','id':1,'result':{'signature':q['params'][0]}})
    return SolanaReadOnlyRPC('https://primary.invalid/SECRET',fallback_endpoints=[],open_url=transport,min_interval=0,sleep=lambda _:None)

def schedule(rpc,sigs):
    method=getattr(rpc,'prefetch_transactions',None)
    if method:method(sigs,ttl=TTL)

def test_four_transactions_use_one_wire_and_restore_out_of_order_ids():
    wires=[];rpc=rpc_with(wires);sigs=['s1','s2','s3','s4'];schedule(rpc,sigs)
    assert [rpc.call('getTransaction',[s,OPTIONS],ttl=TTL)['signature'] for s in sigs]==sigs
    assert len(wires)==rpc.calls==1

@pytest.mark.parametrize('count',[5,29,109])
def test_cold_and_reopened_warm_cache_preserve_every_signature_across_sizes(tmp_path,count):
    signatures=[f'fixture-{count}-{i}' for i in range(count)]
    def collect(rpc,batched):
        if batched:schedule(rpc,signatures)
        return [rpc.call('getTransaction',[s,OPTIONS],ttl=TTL) for s in signatures]

    baseline_calls=[]
    expected=collect(rpc_with(baseline_calls),False)
    assert len(baseline_calls)==count
    path=tmp_path/'rpc.sqlite'
    cold_calls=[]
    cold=rpc_with(cold_calls);cold.cache=RpcCache(path)
    assert collect(cold,True)==expected
    cold.cache.close()
    warm_calls=[]
    warm=rpc_with(warm_calls);warm.cache=RpcCache(path)
    assert collect(warm,True)==expected
    warm.cache.close()
    assert len(cold_calls)==(count+3)//4
    assert not warm_calls and warm.cache_hits==count

@pytest.mark.parametrize('mode',['duplicate','partial','null'])
def test_invalid_partial_or_null_batch_never_drops_a_transaction_or_leaks_source_text(mode):
    wires=[];rpc=rpc_with(wires,mode);sigs=['s1','s2','s3','s4'];schedule(rpc,sigs)
    assert [rpc.call('getTransaction',[s,OPTIONS],ttl=TTL)['signature'] for s in sigs]==sigs
    assert 'SECRET' not in str(getattr(rpc,'transaction_batch_stats',{}))
    assert len(wires)>1

def checkpoint(tmp_path):
    binding={'source':'fixture'};budget={'max_wire_attempts':None,'max_elapsed_seconds':None};job={'job_id':uuid.uuid4().hex,'mint':'Mint','preset':'standard','created_at':1000}
    JobCheckpoint.create(tmp_path,job,binding,budget,clock=lambda:1000)
    cp=JobCheckpoint(tmp_path,job['job_id'],clock=lambda:1000);cp.begin(binding,budget)
    return cp,binding,budget,job['job_id']

def test_batch_results_remain_individual_hash_chained_reads_and_replay_without_socket(tmp_path):
    wires=[];cp,_,_,job=checkpoint(tmp_path);rpc=CheckpointRPC(cp,rpc_with(wires));sigs=['s1','s2','s3','s4'];schedule(rpc,sigs)
    values=[rpc.call('getTransaction',[s,OPTIONS],ttl=TTL) for s in sigs]
    assert len(cp.entries)==4 and cp.meta['wire_used']==1 and len(wires)==1
    cp.assert_can_publish();cp.finish('DONE');cp.close()
    cp=JobCheckpoint(tmp_path,job,readonly=True,clock=lambda:1000);denied=[]
    def no_source(*a,**k):denied.append(True);raise AssertionError('NO_SOURCE')
    raw=SolanaReadOnlyRPC('https://primary.invalid',fallback_endpoints=[],open_url=no_source,min_interval=0)
    replay=CheckpointRPC(cp,raw);schedule(replay,sigs)
    assert [replay.call('getTransaction',[s,OPTIONS],ttl=TTL) for s in sigs]==values
    replay.assert_can_publish();assert cp.replayed==4 and not denied;cp.close()

def test_resume_replays_durable_prefix_and_refetches_only_lost_volatile_suffix(tmp_path):
    wires=[];cp,binding,budget,job=checkpoint(tmp_path);rpc=CheckpointRPC(cp,rpc_with(wires));sigs=['s1','s2','s3','s4'];schedule(rpc,sigs)
    for s in sigs[:2]:rpc.call('getTransaction',[s,OPTIONS],ttl=TTL)
    cp.finish('ERROR');cp.close();assert len(wires)==1
    cp=JobCheckpoint(tmp_path,job,clock=lambda:1000);cp.begin(binding,budget);rpc=CheckpointRPC(cp,rpc_with(wires));schedule(rpc,sigs)
    assert [rpc.call('getTransaction',[s,OPTIONS],ttl=TTL)['signature'] for s in sigs]==sigs
    assert cp.replayed==2 and len(cp.entries)==4 and cp.meta['wire_used']==2 and len(wires)==2
    assert [r['params'][0] for r in wires[-1]]==sigs[2:];rpc.assert_can_publish();cp.close()

def test_changed_replay_sequence_and_failed_reservation_cannot_start_batch_wire(tmp_path):
    wires=[];cp,_,_,_=checkpoint(tmp_path);rpc=CheckpointRPC(cp,rpc_with(wires));schedule(rpc,['s1','s2'])
    rpc.call('getTransaction',['s1',OPTIONS],ttl=TTL);cp.index=0
    with pytest.raises(CheckpointError,match='READ_SEQUENCE_CHANGED'):schedule(rpc,['wrong','s2'])
    assert len(wires)==1;cp.close()
    wires=[];rpc=rpc_with(wires);schedule(rpc,['s1','s2'])
    def denied(endpoint):raise CheckpointError('CA_CHECKPOINT_STORAGE_UNAVAILABLE')
    rpc.before_wire=denied
    with pytest.raises(CheckpointError):rpc.call('getTransaction',['s1',OPTIONS],ttl=TTL)
    assert not wires and rpc.calls==0

def test_source_end_large_pages_preserve_all_signatures_and_empty_end():
    class RPC:
        supports_transaction_batches=True
        def __init__(self):self.requests=[];self.plans=[]
        def call(self,method,params,**kwargs):
            assert method=='getSignaturesForAddress';opts=params[1];self.requests.append(opts)
            start=int(opts['before'].split('-')[1])+1 if 'before' in opts else 0
            return [{'signature':f's-{i}','slot':2000-i,'blockTime':2000-i} for i in range(start,min(1500,start+opts['limit']))]
        def prefetch_transactions(self,signatures,*,ttl):self.plans.append(signatures)
    rpc=RPC();a=WalletClusterAnalyzer('Mint',rpc=rpc,exhaust_history=True)
    got=list(a._signature_pages(Holder('ta','owner',1,0,'ORDINARY','fixture'),'owner',8,1,'funding'))
    assert len(got)==len({x['signature'] for x in got})==1500
    assert [x['limit'] for x in rpc.requests]==[1000,1000,1000]
    assert [len(x) for x in rpc.plans]==[1000,500]
    assert a.history_attempts[0]['stop_reason']=='PROVIDER_EMPTY_PAGE'
