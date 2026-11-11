"""Real collector paths with synthetic current accounts and transaction histories."""
import pytest
from mission_agent.meme import cluster
from mission_agent.meme.cluster import WalletClusterAnalyzer,Holder,RPCJobBudgetExceeded
from test_meme_holder_ranks import RPC,account,key,MINT,P,profile

A=key(301);B=key(302)
T1=key(1);T2=key(2);TZ=key(3);TB=key(4)


class HistoryRPC(RPC):
    endpoint='fixture';calls=0;cache_hits=0
    def __init__(self,records,windows=None,times=None):
        super().__init__(records);self.windows=windows or {};self.times=times or {}
        self.history=[];self.transactions=[];self.fail_address=None
    def call(self,method,params,ttl=0):
        if method=='getSignaturesForAddress':
            address= params[0];self.history.append((address,dict(params[1])))
            if address==self.fail_address:raise RPCJobBudgetExceeded('RPC_JOB_WIRE_BUDGET_EXHAUSTED')
            if params[1].get('before'):return []
            return [{'signature':s,'slot':self.times[s],'blockTime':self.times[s]} for s in self.windows.get(address,[])]
        if method=='getTransaction':
            sig=params[0];self.transactions.append(sig)
            return {'blockTime':self.times[sig],'fixture_sig':sig}
        return super().call(method,params,ttl)


def analyzer(monkeypatch,records=None,windows=None,times=None,**kwargs):
    records=records or [account(1,301,100),account(2,301,50),account(3,301,0),account(4,302,850)]
    rpc=HistoryRPC(records,windows or {T1:['shared'],T2:['shared','earlier'],TZ:['oldest']},times or {'shared':300,'earlier':200,'oldest':100})
    kwargs.setdefault("history_per_holder",12)
    a=WalletClusterAnalyzer(MINT,rpc=rpc,enumerate_holder_ranks=True,deep_holders=1,**kwargs)
    def sample():
        a._snapshot_slots={'supply':100,'largest_accounts':100,'account_batches':[100,100]}
        amounts={r['pubkey']:int(r['account']['data']['parsed']['info']['tokenAmount']['amount']) for r in records}
        a._largest_account_snapshot={T1:amounts.get(T1,100),TB:amounts.get(TB,850)}
        return sum(amounts.values()),0,[Holder(T1,A,amounts.get(T1,100),0,'ORDINARY','fixture'),Holder(TB,B,amounts.get(TB,850),0,'ORDINARY','fixture')]
    a.holders=sample;a.token_profile=profile;a.market_snapshot=lambda:{'status':'UNAVAILABLE'}
    monkeypatch.setattr(cluster,'classify',lambda sig,tx,owner:{'classification':'ACTIVE_TRADE','trade':{'mint':MINT,'direction':'BUY','token_amount_raw':'10','token_decimals':0}})
    return a,rpc


def test_second_and_zero_balance_accounts_find_earliest_buy_and_correct_funding_anchor(monkeypatch):
    a,rpc=analyzer(monkeypatch);anchors=[]
    a._scan_funding=lambda h,first,*args:anchors.append(first['signature'])
    out=a.analyze()
    assert {address for address,_ in rpc.history}=={T1,T2,TZ}
    assert out['holders'][0]['first_acquisition']['signature']=='oldest'
    assert anchors==['oldest']
    assert rpc.transactions.count('shared')==1
    assert len(out['trade_evidence'])==3
    summary=out['coverage']['owner_account_history'][0]
    assert summary['current_accounts_observed']==3
    assert summary['accounts_with_windows']==[T1,T2,TZ]
    assert summary['account_selection_complete'] is True
    assert summary['history_complete'] is False
    assert summary['closed_account_history']=='NOT_ENUMERATED'
    assert out['analysis_completeness']['status']=='INCOMPLETE_EVIDENCE'


def test_enumeration_retains_zero_balance_accounts_for_current_owner_discovery(monkeypatch):
    a,_=analyzer(monkeypatch);a._scan_funding=lambda *args:None
    out=a.analyze();rows=out['holder_rankings']['accounts']
    assert len(rows)==4
    assert next(r for r in rows if r['token_account']==TZ)['raw']=='0'
    assert len(out['holder_rankings']['owners'])==2
    assert out['holder_rankings']['owners'][0]['raw']=='850'


def test_owner_account_cap_keeps_unselected_accounts_explicit(monkeypatch):
    records=[account(i,301,100 if i==1 else 0) for i in [1,2,3,5,6,7,8]]+[account(4,302,900)]
    a,rpc=analyzer(monkeypatch,records=records,windows={T1:['shared']},times={'shared':300})
    a._scan_funding=lambda *args:None
    out=a.analyze();summary=out['coverage']['owner_account_history'][0]
    assert len(summary['accounts_selected'])==4
    assert summary['accounts_not_selected']==3
    assert summary['selection_stop_reason']=='OWNER_ACCOUNT_LIMIT'
    assert summary['account_selection_complete'] is False
    assert 'OWNER_ACCOUNT_SELECTION_INCOMPLETE' in out['coverage']['gaps']
    assert len(rpc.history)==4


def test_extra_report_account_cap_is_shared_by_owners_and_reused_during_deepening(monkeypatch):
    records=[];holders=[]
    for i in range(6):
        owner=400+i
        for j in range(4):records.append(account(100+i*4+j,owner,10))
        holders.append(Holder(key(100+i*4),key(owner),10,0,'UNRESOLVED','fixture'))
    a,rpc=analyzer(monkeypatch,records=records,windows={},times={},adaptive_history_per_holder=30)
    a.deep_holders=6
    def sample():
        a._snapshot_slots={'supply':100,'largest_accounts':100,'account_batches':[100,100]}
        return 240,0,holders
    a.holders=sample;a._scan_funding=lambda *args:None
    out=a.analyze();summaries=out['coverage']['owner_account_history']
    assert sum(len(r['accounts_selected'])-1 for r in summaries)==12
    assert any(r['selection_stop_reason']=='REPORT_EXTRA_ACCOUNT_LIMIT' for r in summaries)
    assert out['coverage']['additional_history_accounts_selected']==12
    assert len({address for address,_ in rpc.history})==18
    assert all(len(r['accounts_selected'])<=4 for r in summaries)


def test_unavailable_full_source_uses_known_top20_accounts_without_claiming_complete_set(monkeypatch):
    a,rpc=analyzer(monkeypatch)
    a._holder_ranks=lambda *args:{'requested':True,'status':'UNAVAILABLE','owners':[]}
    a.holders=lambda:(1000,0,[Holder(T1,A,100,0,'ORDINARY','fixture'),Holder(T2,A,50,0,'ORDINARY','fixture')])
    a._scan_funding=lambda *args:None
    out=a.analyze();summary=out['coverage']['owner_account_history'][0]
    assert {x[0] for x in rpc.history}=={T1,T2}
    assert summary['account_source_status']=='OBSERVED_TOP20_ACCOUNTS'
    assert summary['account_selection_complete'] is False
    assert summary['history_complete'] is False


def test_budget_failure_in_secondary_account_propagates(monkeypatch):
    a,rpc=analyzer(monkeypatch);rpc.fail_address=T2
    with pytest.raises(RPCJobBudgetExceeded):a.analyze()
    assert any(w['stop_reason']=='JOB_BUDGET' for w in a.history_attempts)


def test_material_ordinary_owner_outside_prefix_still_propagates_budget_stop(monkeypatch):
    a,rpc=analyzer(monkeypatch,adaptive_history_per_holder=30)
    a._scan_funding=lambda *args:None
    rpc.fail_address=TB
    with pytest.raises(RPCJobBudgetExceeded):a.analyze()
    assert any(address==TB for address,_ in rpc.history)
    assert any(w['stop_reason']=='JOB_BUDGET' for w in a.history_attempts)


def test_duplicate_signature_is_still_classified_separately_for_different_owners(monkeypatch):
    a,rpc=analyzer(monkeypatch);a.deep_holders=2
    rpc.windows[TB]=['shared'];classified=[]
    def classify(sig,tx,owner):
        classified.append((owner,sig));return {}
    monkeypatch.setattr(cluster,'classify',classify);a._scan_funding=lambda *args:None
    a.analyze()
    assert classified.count((A,'shared'))==1
    assert classified.count((B,'shared'))==1


def test_adaptive_scan_keeps_earlier_buy_from_another_account(monkeypatch):
    a,rpc=analyzer(monkeypatch,adaptive_history_per_holder=30)
    a.registry={'addresses':{A:{'role':'UNRESOLVED','source':'fixture'}}}
    # Holder role drives adaptive selection, not just registry metadata.
    base=a.holders
    def sample():
        supply,decimals,rows=base();rows[0].role='UNRESOLVED';return supply,decimals,rows
    a.holders=sample;anchors=[];a._scan_funding=lambda h,first,*args:anchors.append(first['signature']) if first else None
    out=a.analyze()
    assert out['holders'][0]['first_acquisition']['signature']=='oldest'
    assert anchors==['oldest','oldest']
    assert rpc.transactions.count('shared')==1
    assert len(out['trade_evidence'])==3


def test_mismatched_snapshot_owner_never_marks_account_set_verified(monkeypatch):
    a,rpc=analyzer(monkeypatch)
    rpc.records[0]['account']['data']['parsed']['info']['owner']=B
    a._scan_funding=lambda *args:None
    out=a.analyze();summary=out['coverage']['owner_account_history'][0]
    assert out['holder_rankings']['status']=='COMPLETE_SNAPSHOT'
    assert summary['account_source_status']=='SNAPSHOT_OWNER_CONFLICT'
    assert summary['account_selection_complete'] is False
    assert summary['accounts_selected']==[T1]
    assert 'OWNER_ACCOUNT_SNAPSHOT_CONFLICT' in out['coverage']['gaps']


def test_real_worker_secondary_account_budget_stop_preserves_latest_and_no_done(monkeypatch,tmp_path):
    from mission_agent.mission_control import server
    a,rpc=analyzer(monkeypatch);rpc.fail_address=T2
    monkeypatch.setenv('MISSION_EVIDENCE_EXPORT_ENABLED','0')
    manager=server.ClusterJobManager(tmp_path)
    jobid='a'*32
    manager.jobs[jobid]={'job_id':jobid,'mint':MINT,'preset':'standard','status':'QUEUED','created_at':1,'started_at':None,'finished_at':None,'error':None,'progress':{}}
    prior=manager.report_root/MINT/'latest.json';prior.parent.mkdir(parents=True);prior.write_text('{"prior":true}')
    monkeypatch.setattr(server,'SolanaReadOnlyRPC',lambda *args,**kwargs:rpc)
    monkeypatch.setattr(server,'WalletClusterAnalyzer',lambda *args,**kwargs:a)
    monkeypatch.setattr(server,'load_registry',lambda *args:{})
    try:manager._run(jobid)
    finally:manager.executor.shutdown(wait=True)
    assert manager.jobs[jobid]['status']=='ERROR'
    assert manager.jobs[jobid]['error']['type']=='RPC_JOB_BUDGET_EXHAUSTED'
    assert prior.read_text()=='{"prior":true}'
    assert not (manager.report_root/'_jobs'/f'{jobid}.done.json').exists()
    assert not (manager.report_root/'_jobs'/f'{jobid}.json').exists()
