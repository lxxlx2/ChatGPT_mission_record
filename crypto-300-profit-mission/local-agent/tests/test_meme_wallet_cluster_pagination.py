"""CA history reads beyond one page; synthetic RPC only, no chain requests."""
from decimal import Decimal
import pytest
from mission_agent.meme import cluster
from mission_agent.meme.cluster import Holder, WalletClusterAnalyzer, RPCJobBudgetExceeded


def rows(start,count):
    return [{"signature":f"s-{i}","slot":10000-i,"blockTime":10000-i} for i in range(start,start+count)]


class PageRPC:
    endpoint="fixture";calls=0;cache_hits=0
    def __init__(self,pages):self.pages=list(pages);self.requests=[];self.transactions=[]
    def call(self,method,params,ttl=0):
        if method=='getSignaturesForAddress':
            self.requests.append((params[0],dict(params[1])))
            item=self.pages.pop(0)
            if isinstance(item,Exception):raise item
            return item
        if method=='getTransaction':
            sig=params[0];self.transactions.append(sig)
            return {"blockTime":10000-int(sig.split('-')[1]),"fixture_signature":sig}
        raise AssertionError(method)


def make(pages):
    a=WalletClusterAnalyzer('Mint',rpc=PageRPC(pages))
    h=Holder('ta','A',100,0,'ORDINARY','fixture')
    return a,h


def window(a):return list(a.history_coverage.values())[-1]


def test_pages_advance_exclusive_cursor_and_wait_for_explicit_empty_page():
    a,h=make([rows(0,2),rows(2,1),[]])
    out=list(a._signature_pages(h,'ta',2,3,'holder'))
    assert [x['signature'] for x in out]==['s-0','s-1','s-2']
    assert a.rpc.requests==[('ta',{'commitment':'finalized','limit':2}),('ta',{'commitment':'finalized','limit':2,'before':'s-1'}),('ta',{'commitment':'finalized','limit':2,'before':'s-2'})]
    assert window(a)['pages']==3
    assert window(a)['stop_reason']=='PROVIDER_EMPTY_PAGE'
    assert window(a)['provider_pagination_end_observed'] is True
    assert window(a)['history_complete'] is False
    assert window(a)['oldest_block_time']==9998


def test_page_limit_keeps_short_page_incomplete_and_retains_cursor():
    a,h=make([rows(0,1)])
    assert len(list(a._signature_pages(h,'ta',50,1,'holder')))==1
    assert window(a)['stop_reason']=='PAGE_LIMIT'
    assert window(a)['provider_pagination_end_observed'] is False
    assert window(a)['next_before']=='s-0'


def test_overlap_does_not_duplicate_transaction_work():
    a,h=make([rows(0,2),rows(1,2),[]])
    assert [m['signature'] for m in a._signature_pages(h,'ta',2,3,'holder')]==['s-0','s-1','s-2']
    assert window(a)['signature_count']==3
    assert window(a)['duplicates_skipped']==1


def test_repeating_provider_page_stops_without_loop_or_false_exhaustion():
    a,h=make([rows(0,2),rows(0,2)])
    assert len(list(a._signature_pages(h,'ta',2,8,'holder')))==2
    assert len(a.rpc.requests)==2
    assert window(a)['stop_reason']=='CURSOR_STALLED'
    assert window(a)['provider_pagination_end_observed'] is False


def test_conflicting_signature_slot_is_not_accepted():
    a,h=make([rows(0,2),[dict(rows(1,1)[0],slot=9990)]])
    list(a._signature_pages(h,'ta',2,3,'holder'))
    assert window(a)['stop_reason']=='SOURCE_PAGE_CONFLICT'
    assert window(a)['next_before']=='s-1'


@pytest.mark.parametrize('bad',[None,{},[{}],[{'signature':123}],rows(0,3)])
def test_malformed_signature_page_cannot_be_an_empty_history(bad):
    a,h=make([bad])
    assert list(a._signature_pages(h,'ta',2,2,'holder'))==[]
    assert window(a)['stop_reason']=='MALFORMED_SIGNATURE_PAGE'
    assert window(a)['provider_pagination_end_observed'] is False


def test_read_failure_keeps_last_processed_cursor_and_safe_error():
    a,h=make([rows(0,2),TimeoutError('https://private.invalid/SECRET')])
    assert len(list(a._signature_pages(h,'ta',2,4,'holder')))==2
    assert window(a)['next_before']=='s-1'
    assert window(a)['stop_reason']=='SOURCE_UNAVAILABLE'
    assert 'SECRET' not in str(a.tx_errors)


def test_job_budget_exception_propagates_without_advancing_cursor():
    a,h=make([rows(0,2),RPCJobBudgetExceeded('RPC_JOB_WIRE_BUDGET_EXHAUSTED')])
    with pytest.raises(RPCJobBudgetExceeded):list(a._signature_pages(h,'ta',2,4,'holder'))
    assert window(a)['next_before']=='s-1'
    assert window(a)['stop_reason']=='JOB_BUDGET'


def test_consumer_interruption_does_not_commit_half_processed_page_cursor():
    a,h=make([rows(0,2)])
    stream=a._signature_pages(h,'ta',2,2,'holder',before='anchor')
    assert next(stream)['signature']=='s-0'
    stream.close()
    assert window(a)['next_before']=='anchor'
    assert window(a)['stop_reason']=='INTERRUPTED'


@pytest.mark.parametrize('limit,pages',[(0,1),(1001,1),(1,0),(1,9),(1,True)])
def test_invalid_page_bounds_fail_before_rpc(limit,pages):
    a,h=make([])
    with pytest.raises(ValueError):list(a._signature_pages(h,'ta',limit,pages,'holder'))
    assert a.rpc.requests==[]


def test_holder_buy_older_than_100_signatures_is_found_on_second_page(monkeypatch):
    a,h=make([rows(0,100),rows(100,20),[]])
    a._history_page_limit=3
    monkeypatch.setattr(cluster,'classify',lambda sig,tx,owner:{'classification':'ACTIVE_TRADE','trade':{'mint':'Mint','direction':'BUY'}} if sig=='s-110' else {})
    first=a._scan_holder(h,{'ta':'A'},{'A'},100)
    assert first['signature']=='s-110'
    assert len(a.rpc.transactions)==120
    assert window(a)['provider_pagination_end_observed'] is True
    assert window(a)['history_complete'] is False


def test_funding_older_than_50_signatures_is_found_on_second_page(monkeypatch):
    a,h=make([rows(0,50),rows(50,10),[]])
    a._funding_page_limit=3
    monkeypatch.setattr(cluster,'_native_funders',lambda tx,owner:[('PAYER',100)] if tx['fixture_signature']=='s-55' else [])
    a._scan_funding(h,{'signature':'buy-anchor','block_time':11000},{'A'},50)
    assert a.funding[0]['signature']=='s-55'
    assert a.rpc.requests[0][1]['before']=='buy-anchor'
    assert a.rpc.requests[1][1]['before']=='s-49'
    assert window(a)['phase']=='funding'


def test_standard_worker_enables_bounded_adaptive_pages_without_changing_job_budgets():
    from mission_agent.mission_control.server import CLUSTER_PRESETS,CLUSTER_RPC_JOB_BUDGETS
    assert CLUSTER_PRESETS['standard']['adaptive_history_max_pages']==8
    assert CLUSTER_PRESETS['standard']['adaptive_funding_max_pages']==8
    assert CLUSTER_RPC_JOB_BUDGETS['standard']=={'max_wire_attempts':1200,'max_elapsed_seconds':1800}


def test_page_cache_can_be_reused_in_a_fresh_analyzer_without_wire_reads(tmp_path):
    import json
    class Response:
        def __init__(self,result):self.result=result
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def read(self):return json.dumps({'result':self.result}).encode()
    wire=[]
    def transport(request,timeout):
        body=json.loads(request.data);opts=body['params'][1];wire.append(dict(opts))
        return Response(rows(0,2) if 'before' not in opts else [])
    cache=cluster.RpcCache(tmp_path/'cache.sqlite')
    try:
        rpc=cluster.SolanaReadOnlyRPC('https://fixture.example',fallback_endpoints=[],cache=cache,open_url=transport,min_interval=0)
        a=WalletClusterAnalyzer('Mint',rpc=rpc);h=Holder('ta','A',100,0,'ORDINARY','fixture')
        assert len(list(a._signature_pages(h,'ta',2,2,'holder')))==2
        assert rpc.calls==2
    finally:cache.close()
    cache=cluster.RpcCache(tmp_path/'cache.sqlite')
    try:
        def denied(*args,**kwargs):raise AssertionError('NO_WIRE_EXPECTED')
        rpc=cluster.SolanaReadOnlyRPC('https://fixture.example',fallback_endpoints=[],cache=cache,open_url=denied,min_interval=0)
        a=WalletClusterAnalyzer('Mint',rpc=rpc)
        assert len(list(a._signature_pages(h,'ta',2,2,'holder')))==2
        assert rpc.calls==0 and rpc.cache_hits==2
        assert window(a)['provider_pagination_end_observed'] is True
    finally:cache.close()


def test_real_rpc_wire_budget_stops_transaction_loop_inside_page_without_false_cursor(monkeypatch):
    import json
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def read(self):return json.dumps({'result':rows(0,2)}).encode()
    rpc=cluster.SolanaReadOnlyRPC('https://fixture.example',fallback_endpoints=[],open_url=lambda *args,**kwargs:Response(),min_interval=0,max_wire_attempts=1)
    a=WalletClusterAnalyzer('Mint',rpc=rpc)
    h=Holder('ta','A',100,0,'ORDINARY','fixture')
    with pytest.raises(RPCJobBudgetExceeded):a._scan_holder(h,{'ta':'A'},{'A'},2)
    assert rpc.calls==1
    assert window(a)['next_before'] is None
    assert window(a)['stop_reason']=='JOB_BUDGET'
    with pytest.raises(RPCJobBudgetExceeded):rpc.assert_can_publish()


def test_classification_failure_remains_visible_and_does_not_leak_exception(monkeypatch):
    a,h=make([rows(0,1)])
    def fail(*args):raise RuntimeError('SECRET_PROVIDER_OR_PATH')
    monkeypatch.setattr(cluster,'classify',fail)
    assert a._scan_holder(h,{'ta':'A'},{'A'},1) is None
    assert a.tx_errors==[{'signature':'s-0','phase':'holder_classify','error':'RuntimeError'}]


def test_actual_standard_analyze_reaches_fourth_history_page_and_keeps_bounded_status(monkeypatch):
    from mission_agent.mission_control.server import CLUSTER_PRESETS
    rpc=PageRPC([rows(0,12),rows(0,30),rows(30,30),rows(60,30),rows(90,30),rows(120,30),rows(150,30),rows(180,30),rows(210,30)])
    a=WalletClusterAnalyzer('Mint',rpc=rpc,**CLUSTER_PRESETS['standard'])
    a.launch_snapshot=lambda profile:{'version':1,'status':'NOT_REQUESTED'}
    a.holders=lambda:(1000,0,[Holder('ta','A',100,0,'UNRESOLVED','fixture')])
    a.token_profile=lambda:{'status':'OK','mint_authority':None,'freeze_authority':None}
    a.market_snapshot=lambda:{'status':'UNAVAILABLE'}
    funding_plans=[]
    a._scan_funding=lambda holder,first,owners,*args:funding_plans.append((first,a._funding_page_limit))
    monkeypatch.setattr(cluster,'classify',lambda sig,tx,owner:{'classification':'ACTIVE_TRADE','trade':{'mint':'Mint','direction':'BUY'}} if sig=='s-110' else {})
    report=a.analyze()
    assert report['holders'][0]['first_acquisition']['signature']=='s-110'
    assert report['holders'][0]['first_acquisition']['status']=='CONFIRMED_BOUNDED'
    history=report['coverage']['history_windows'][-1]
    assert report['coverage']['holder_history_pages']==9
    assert history['pages']==8 and history['signature_count']==240
    assert history['stop_reason']=='PAGE_LIMIT' and history['history_complete'] is False
    assert 'HISTORY_PAGINATION_INCOMPLETE' in report['coverage']['gaps']
    assert funding_plans[-1][0]['signature']=='s-110'
    assert funding_plans[-1][1]==8



def test_deeper_acquisition_does_not_reuse_later_funding_as_first_buy_prefunding():
    a,h=make([])
    a.history_per_holder=12;a.adaptive_history_per_holder=30
    h.role='UNRESOLVED'
    a.holders=lambda:(1000,0,[h])
    a.token_profile=lambda:{'status':'OK','mint_authority':None,'freeze_authority':None}
    a.market_snapshot=lambda:{'status':'UNAVAILABLE'}
    a._scan_holder=lambda holder,mapping,owners,limit:{'block_time':100 if limit==12 else 80,'signature':f'buy-{limit}'}
    def funding(holder,first,owners,*args):
        a.funding.append({'owner':'A','source':f'payer-{first["block_time"]}','lamports':100,'signature':f'fund-{first["block_time"]}','block_time':first['block_time']-10})
    a._scan_funding=funding
    report=a.analyze()
    assert report['holders'][0]['first_acquisition']['block_time']==80
    assert report['holders'][0]['funding']['block_time']==70
    assert len(report['funding_evidence'])==2
