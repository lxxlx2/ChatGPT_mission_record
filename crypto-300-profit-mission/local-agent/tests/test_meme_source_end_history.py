"""Source-driven history drains real collector paths using offline RPC fixtures."""
import copy
from mission_agent.meme import cluster
from mission_agent.meme.cluster import WalletClusterAnalyzer, Holder
from test_meme_wallet_cluster_pagination import PageRPC, rows
from test_meme_owner_account_history import analyzer, A, B, T1, T2, TB
from test_meme_holder_ranks import account, key, MINT, P


def test_buy_beyond_eighth_page_is_found_and_completed_window_is_not_restarted(monkeypatch):
    rpc=PageRPC([rows(i,1) for i in range(12)]+[[]])
    a=WalletClusterAnalyzer('Mint',rpc=rpc,exhaust_history=True)
    h=Holder('ta','A',100,0,'ORDINARY','fixture')
    monkeypatch.setattr(cluster,'classify',lambda sig,tx,owner:
        {'classification':'ACTIVE_TRADE','trade':{'mint':'Mint','direction':'BUY'}} if sig=='s-11' else {})
    first=a._scan_holder(h,{'ta':'A'},{'A'},1)
    assert first['signature']=='s-11'
    assert len(rpc.requests)==13 and len(rpc.transactions)==12
    state=a.history_attempts[0]
    assert state['page_limit'] is None
    assert state['stop_reason']=='PROVIDER_EMPTY_PAGE' and state['next_before']=='s-11'
    assert state['history_complete'] is False
    assert a._scan_holder(h,{'ta':'A'},{'A'},1)==first
    assert len(rpc.requests)==13 and len(rpc.transactions)==12


def test_interrupted_page_replays_without_losing_pending_signatures_or_cursor():
    rpc=PageRPC([rows(0,2),rows(0,2),rows(2,1),[]])
    a=WalletClusterAnalyzer('Mint',rpc=rpc,exhaust_history=True)
    h=Holder('ta','A',1,0,'ORDINARY','fixture')
    stream=a._signature_pages(h,'ta',2,1,'holder')
    assert next(stream)['signature']=='s-0'
    stream.close()
    assert a.history_attempts[0]['next_before'] is None
    assert [r['signature'] for r in a._signature_pages(h,'ta',2,1,'holder')]==['s-0','s-1','s-2']
    assert a.history_attempts[0]['signature_count']==3
    assert a.history_attempts[0]['stop_reason']=='PROVIDER_EMPTY_PAGE'
    assert len(a.history_attempts)==1


def test_source_failure_is_terminal_and_does_not_become_empty_or_leak_error():
    rpc=PageRPC([rows(0,1),TimeoutError('https://private.invalid/SECRET')])
    a=WalletClusterAnalyzer('Mint',rpc=rpc,exhaust_history=True)
    h=Holder('ta','A',1,0,'ORDINARY','fixture')
    assert len(list(a._signature_pages(h,'ta',1,1,'holder')))==1
    state=a.history_attempts[0]
    assert state['next_before']=='s-0' and state['stop_reason']=='SOURCE_UNAVAILABLE'
    assert state['provider_pagination_end_observed'] is False
    assert list(a._signature_pages(h,'ta',1,1,'holder'))==[]
    assert len(rpc.requests)==2
    assert 'SECRET' not in str(a.tx_errors)


def test_repeated_page_still_stops_source_driven_history():
    rpc=PageRPC([rows(0,2),rows(0,2)])
    a=WalletClusterAnalyzer('Mint',rpc=rpc,exhaust_history=True)
    h=Holder('ta','A',1,0,'ORDINARY','fixture')
    assert len(list(a._signature_pages(h,'ta',2,1,'holder')))==2
    assert a.history_attempts[0]['stop_reason']=='CURSOR_STALLED'
    assert len(rpc.requests)==2


def test_same_historical_address_has_separate_owner_continuations():
    rpc=PageRPC([[],[]])
    a=WalletClusterAnalyzer('Mint',rpc=rpc,exhaust_history=True)
    for owner in ['A','B']:
        assert list(a._signature_pages(Holder('ta',owner,1,0,'ORDINARY','fixture'),'ta',1,1,'holder'))==[]
    assert len(a.history_attempts)==2
    assert {r['owner'] for r in a.history_attempts}=={'A','B'}


def test_all_verified_current_accounts_are_selected_without_four_account_cap(monkeypatch):
    records=[account(i,301,100 if i==1 else 0) for i in [1,2,3,5,6,7,8]]+[account(4,302,900)]
    a,rpc=analyzer(monkeypatch,records=records,windows={T1:['shared']},times={'shared':300},exhaust_history=True)
    a._scan_funding=lambda *args:None
    out=a.analyze()
    summary=next(r for r in out['coverage']['owner_account_history'] if r['owner']==A)
    assert len(summary['accounts_selected'])==7
    assert summary['accounts_not_selected']==0 and summary['account_selection_complete'] is True
    assert out['coverage']['history_scan_mode']=='SOURCE_END'
    for field in ['owner_history_account_limit','report_extra_history_account_limit','historical_account_frontier_limit','historical_account_observation_limit']:
        assert out['coverage'][field] is None
    assert out['coverage']['owners_not_scanned']==[]
    assert all(w['stop_reason']=='PROVIDER_EMPTY_PAGE' for w in out['coverage']['history_windows'])


def test_all_owners_and_extra_accounts_are_read_without_prefix_or_twelve_account_cap(monkeypatch):
    records=[];holders=[]
    for i in range(6):
        for j in range(4):records.append(account(100+i*4+j,400+i,10))
        holders.append(Holder(key(100+i*4),key(400+i),10,0,'UNRESOLVED','fixture'))
    a,rpc=analyzer(monkeypatch,records=records,windows={},times={},exhaust_history=True)
    a.deep_holders=1
    def sample():
        a._snapshot_slots={'supply':100,'largest_accounts':100,'account_batches':[100,100]}
        return 240,0,holders
    a.holders=sample;a._scan_funding=lambda *args:None
    out=a.analyze()
    assert len(out['coverage']['owner_account_history'])==6
    assert out['coverage']['additional_history_accounts_selected']==18
    assert len(rpc.history)==24
    assert out['coverage']['owners_not_scanned']==[]


def raw_transaction(signature,slot,addresses):
    names=[A,*addresses,P]
    balances=[{'accountIndex':i+1,'owner':A,'mint':MINT,'programId':P,
               'uiTokenAmount':{'amount':'10','decimals':0}} for i in range(len(addresses))]
    return {'slot':slot,'blockTime':slot,'transaction':{'signatures':[signature],
        'message':{'accountKeys':[{'pubkey':n,'signer':n==A} for n in names],'instructions':[]}},
        'meta':{'err':None,'preTokenBalances':balances,'postTokenBalances':copy.deepcopy(balances),
                'preBalances':[1]*len(names),'postBalances':[1]*len(names),'innerInstructions':[]}}


def test_newly_discovered_historical_accounts_are_drained_to_multiple_frontiers(monkeypatch):
    h1,h2,h3=[key(n) for n in (601,602,603)]
    txs={'s1':raw_transaction('s1',30,[T1,h1]),'s2':raw_transaction('s2',20,[h1,h2]),'s3':raw_transaction('s3',10,[h2,h3])}
    windows={T1:'s1',h1:'s2',h2:'s3'}
    class RPC:
        def __init__(self):self.requests=[];self.transactions=[]
        def call(self,method,params,ttl=0):
            if method=='getSignaturesForAddress':
                address,cfg=params;self.requests.append((address,dict(cfg)))
                sig=windows.get(address)
                return [] if cfg.get('before') or not sig else [{'signature':sig,'slot':txs[sig]['slot'],'blockTime':txs[sig]['blockTime']}]
            if method=='getTransaction':self.transactions.append(params[0]);return txs[params[0]]
            raise AssertionError(method)
    rpc=RPC();a=WalletClusterAnalyzer(MINT,rpc=rpc,enumerate_holder_ranks=True,exhaust_history=True)
    holder=Holder(T1,A,10,0,'ORDINARY','fixture')
    a._prepare_owner_account_history([holder],{})
    monkeypatch.setattr(cluster,'classify',lambda *args:{})
    firsts={A:a._scan_owner_history(holder,{T1:A},{A},2)}
    a._scan_historical_account_frontier(firsts,{T1:A},{A},{A:holder})
    assert {address for address,_ in rpc.requests}=={T1,h1,h2,h3}
    assert {r['account'] for r in a.historical_account_scans if r['selected']}=={h1,h2,h3}
    assert all(r['window_stop_reason']=='PROVIDER_EMPTY_PAGE' for r in a.historical_account_scans if r['selected'])
    assert rpc.transactions==['s1','s2','s3']
    assert all(r['history_complete'] is False for r in a.historical_account_scans)


def test_only_verified_protocol_account_is_skipped_unknown_program_owner_is_scanned(monkeypatch):
    a,rpc=analyzer(monkeypatch,exhaust_history=True)
    a._scan_funding=lambda *args:None
    a.special_role_snapshot=lambda *args:{'records':[
        {'owner':A,'token_account':T1,'role':'PROTOCOL_VAULT','classification':'CHAIN_ACCOUNT_ROLE'},
        {'owner':B,'token_account':TB,'role':'AMM_POOL','classification':'UNVERIFIED'}]}
    out=a.analyze()
    assert T1 not in {address for address,_ in rpc.history}
    assert T2 in {address for address,_ in rpc.history} and TB in {address for address,_ in rpc.history}
    assert len(out['coverage']['protocol_history_exclusions'])==1
    summary=next(r for r in out['coverage']['owner_account_history'] if r['owner']==A)
    assert summary['protocol_accounts_not_applicable']==[T1]
    assert out['holders'][0]['first_acquisition']['status']!='NOT_APPLICABLE_PROTOCOL_POOL'
    assert out['holders'][0]['first_acquisition']['status']!='CONFIRMED_ACCOUNT_COMPLETE'


def test_owner_whose_every_verified_current_account_is_protocol_has_explicit_not_applicable(monkeypatch):
    records=[account(1,301,100),account(4,302,900)]
    a,rpc=analyzer(monkeypatch,records=records,exhaust_history=True)
    a._scan_funding=lambda *args:None
    a.special_role_snapshot=lambda *args:{'records':[{'owner':A,'token_account':T1,'role':'PROTOCOL_VAULT','classification':'CHAIN_ACCOUNT_ROLE'}]}
    out=a.analyze()
    assert out['holders'][0]['first_acquisition']['status']=='NOT_APPLICABLE_PROTOCOL_POOL'
    assert T1 not in {address for address,_ in rpc.history}
    assert A not in out['coverage']['owners_not_scanned']
