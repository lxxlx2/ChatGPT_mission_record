"""Observed historical accounts join one bounded read frontier, never recurse."""
import copy
import pytest
from mission_agent.meme.cluster import RPCJobBudgetExceeded
from test_meme_owner_account_history import analyzer,A,T1,T2,TZ,MINT,key
from test_meme_historical_accounts import tx,ACCOUNT

H=ACCOUNT;H2=key(601)


def historical_analyzer(monkeypatch):
    a,rpc=analyzer(monkeypatch);base=rpc.call
    def proof(sig,slot,address=H,closed=True):
        value=tx(post=not closed,close=closed);value['slot']=slot;value['blockTime']=slot
        value['transaction']['signatures']=[sig]
        value['transaction']['message']['accountKeys'][1]['pubkey']=address
        if closed:value['transaction']['message']['instructions'][0]['parsed']['info']['account']=address
        return value
    def call(method,params,ttl=0):
        if method=='getSignaturesForAddress' and params[0]==A:
            rpc.history.append((params[0],dict(params[1])))
            before=params[1].get('before')
            if before=='oldest':return [{'signature':'close-proof','slot':90,'blockTime':90}]
            if before=='ancient':return [{'signature':'next-proof','slot':70,'blockTime':70}]
            return []
        if method=='getSignaturesForAddress' and params[0]==H:
            rpc.history.append((params[0],dict(params[1])))
            if rpc.fail_address==H:raise RPCJobBudgetExceeded('RPC_JOB_WIRE_BUDGET_EXHAUSTED')
            return [{'signature':'ancient','slot':80,'blockTime':80}]
        if method=='getTransaction' and params[0] in {'close-proof','ancient','next-proof'}:
            sig=params[0];rpc.transactions.append(sig)
            return proof(sig,90) if sig=='close-proof' else proof(sig,80,closed=False) if sig=='ancient' else proof(sig,70,H2)
        return base(method,params,ttl)
    rpc.call=call
    return a,rpc


def test_funding_discovery_reads_historical_account_and_moves_earliest_buy_anchor(monkeypatch):
    a,rpc=historical_analyzer(monkeypatch);out=a.analyze()
    assert out['holders'][0]['first_acquisition']['signature']=='ancient'
    assert any(address==A and cfg.get('before')=='ancient' for address,cfg in rpc.history)
    assert rpc.transactions.count('ancient')==1
    records=out['historical_account_evidence']
    assert any(r['account']==H and r['signature']=='close-proof' and r['closure_at_transaction_end']=='CONFIRMED_CLOSED_AT_TRANSACTION_END' for r in records)
    plans=out['coverage']['historical_account_history']
    assert next(r for r in plans if r['account']==H)['selected'] is True
    assert next(r for r in plans if r['account']==H2)['stop_reason']=='FRONTIER_LIMIT'
    assert H2 not in {address for address,_ in rpc.history}
    assert out['coverage']['additional_history_accounts_selected']==3
    assert out['analysis_completeness']['status']=='INCOMPLETE_EVIDENCE'


def test_historical_reads_share_current_owner_account_limit(monkeypatch):
    a,rpc=historical_analyzer(monkeypatch)
    from test_meme_holder_ranks import account
    rpc.records.append(account(5,301,0))
    out=a.analyze();row=next(r for r in out['coverage']['historical_account_history'] if r['account']==H)
    assert row['selected'] is False and row['stop_reason']=='OWNER_ACCOUNT_LIMIT'
    assert H not in {address for address,_ in rpc.history}
    assert out['holders'][0]['first_acquisition']['signature']=='oldest'


def test_missing_success_context_does_not_create_historical_scan(monkeypatch):
    a,rpc=historical_analyzer(monkeypatch);base=rpc.call
    def call(method,params,ttl=0):
        value=base(method,params,ttl)
        if method=='getTransaction' and params[0]=='close-proof':value['meta']['err']={'InstructionError':[0,'Custom']}
        return value
    rpc.call=call;out=a.analyze()
    assert out['historical_account_evidence']==[]
    assert H not in {address for address,_ in rpc.history}
    assert 'HISTORICAL_ACCOUNT_CONTEXT_GAPS' in out['coverage']['gaps']


def test_historical_account_budget_stop_preserves_worker_latest(monkeypatch,tmp_path):
    from mission_agent.mission_control import server
    a,rpc=historical_analyzer(monkeypatch);rpc.fail_address=H
    monkeypatch.setenv('MISSION_EVIDENCE_EXPORT_ENABLED','0')
    manager=server.ClusterJobManager(tmp_path);jobid='b'*32
    manager.jobs[jobid]={'job_id':jobid,'mint':MINT,'preset':'standard','status':'QUEUED','created_at':1,'started_at':None,'finished_at':None,'error':None,'progress':{}}
    prior=manager.report_root/MINT/'latest.json';prior.parent.mkdir(parents=True);prior.write_text('{"prior":true}')
    monkeypatch.setattr(server,'SolanaReadOnlyRPC',lambda *args,**kwargs:rpc)
    monkeypatch.setattr(server,'WalletClusterAnalyzer',lambda *args,**kwargs:a)
    monkeypatch.setattr(server,'load_registry',lambda *args:{})
    try:manager._run(jobid)
    finally:manager.executor.shutdown(wait=True)
    assert manager.jobs[jobid]['status']=='ERROR'
    assert prior.read_text()=='{"prior":true}'
    assert not (manager.report_root/'_jobs'/f'{jobid}.done.json').exists()
    assert any(w['account_origin']=='HISTORICAL_OBSERVED_OWNER' and w['stop_reason']=='JOB_BUDGET' for w in a.history_attempts)


def test_observation_limit_never_silently_implies_exhaustive_discovery(monkeypatch):
    from mission_agent.meme.historical_accounts import MAX_OBSERVATIONS
    a,_=historical_analyzer(monkeypatch)
    for n in range(MAX_OBSERVATIONS+1):
        value=tx(post=False,close=True);sig=f'proof-{n}';value['transaction']['signatures']=[sig]
        # The hard cap applies to distinct retained proof groups. Repeated
        # snapshots of one account are compacted rather than using the quota.
        address=key(2000+n)
        value['transaction']['message']['accountKeys'][1]['pubkey']=address
        value['transaction']['message']['instructions'][0]['parsed']['info']['account']=address
        a._observe_historical_accounts(value,sig,A,100)
    assert len(a.historical_accounts)==MAX_OBSERVATIONS
    assert a._historical_evidence_limited is True
    assert all(len(r['response_sha256'])==64 for r in a.historical_accounts)
    assert a._historical_retention_coverage()['limit_rejected_observations']==1
    assert a._historical_retention_coverage()['complete_history'] is False
