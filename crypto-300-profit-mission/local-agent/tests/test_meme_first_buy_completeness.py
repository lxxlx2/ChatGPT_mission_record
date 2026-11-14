"""Current-account exhaustion must not hide unread or unclassified transactions."""
import pytest
from mission_agent.meme import cluster
from mission_agent.meme.cluster import Holder, WalletClusterAnalyzer, report_completeness
from mission_agent.meme.holder_ranks import _b58

MINT='So11111111111111111111111111111111111111112'
ACCOUNT=_b58(bytes(31)+b'\x02')
OTHER_ACCOUNT=_b58(bytes(31)+b'\x04')
OWNER=_b58(bytes(31)+b'\x03')
PROGRAM='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'


def transaction(signature,slot):
    return {'slot':slot,'blockTime':slot,
            'transaction':{'signatures':[signature],
                           'message':{'accountKeys':[],'instructions':[]}},
            'meta':{'err':None,'preBalances':[],'postBalances':[],
                    'preTokenBalances':[],'postTokenBalances':[]}}


class RPC:
    endpoint='OFFLINE_FIXTURE';endpoints=[];calls=0;cache_hits=0
    def __init__(self,older_result,with_buy):
        self.older_result=older_result;self.with_buy=with_buy;self.requests=[]
    def call(self,method,params,ttl=0):
        self.requests.append((method,params))
        if method=='getSignaturesForAddress':
            if params[1].get('before'):return []
            rows=[{'signature':'older','slot':7,'blockTime':7}]
            if self.with_buy:rows.insert(0,{'signature':'later-buy','slot':9,'blockTime':9})
            return rows
        if method=='getTransaction':
            if params[0]=='later-buy':return transaction('later-buy',9)
            if isinstance(self.older_result,Exception):raise self.older_result
            return self.older_result
        raise AssertionError(method)


class Probe(WalletClusterAnalyzer):
    def token_profile(self):
        return {'status':'OK','program_id':PROGRAM,'is_initialized':True,
                'mint_authority':None,'freeze_authority':None}
    def holders(self):return 100,0,[Holder(ACCOUNT,OWNER,100,0,'ORDINARY','fixture')]
    def _holder_ranks(self,*args):
        accounts=[{'token_account':a,'owner':OWNER,'raw':'100' if a==ACCOUNT else '0','decimals':0}
                  for a in self.accounts]
        return {'requested':True,'status':'COMPLETE_SNAPSHOT','supply_raw':'100',
                'normalization_complete':False,'metrics':{},
                'owners':[{'owner':OWNER,'raw':'100','role':'ORDINARY'}],'accounts':accounts}
    def _scan_funding(self,*args,**kwargs):return None


def analyze(monkeypatch,older_result,with_buy,*,classification=None,two_accounts=False):
    original=cluster.classify
    def classify(sig,tx,owner):
        if sig=='later-buy':return {'classification':'ACTIVE_TRADE','trade':{'mint':MINT,'direction':'BUY'}}
        if classification=='actual':return original(sig,tx,owner)
        if isinstance(classification,Exception):raise classification
        return {'classification':classification or 'NO_ACTION','trade':None}
    monkeypatch.setattr(cluster,'classify',classify)
    rpc=RPC(older_result,with_buy)
    analyzer=Probe(MINT,rpc=rpc,deep_holders=1,history_max_pages=2,enumerate_holder_ranks=True)
    analyzer.accounts=[ACCOUNT,OTHER_ACCOUNT] if two_accounts else [ACCOUNT]
    return analyzer.analyze(),rpc


@pytest.mark.parametrize('with_buy',[False,True])
@pytest.mark.parametrize('failure',['timeout','null','classification_exception','incomplete_metadata'])
def test_exhausted_pages_do_not_promote_unread_or_unclassified_older_transaction(monkeypatch,with_buy,failure):
    value=transaction('older',7);classification=None
    if failure=='timeout':value=TimeoutError('https://private.invalid/DO_NOT_PUBLISH')
    elif failure=='null':value=None
    elif failure=='classification_exception':classification=ValueError('DO_NOT_PUBLISH')
    else:
        value.pop('meta');classification='actual'
    report,rpc=analyze(monkeypatch,value,with_buy,classification=classification)
    first=report['holders'][0]['first_acquisition']
    assert first['status']==('CONFIRMED_BOUNDED' if with_buy else 'UNRESOLVED')
    assert report['transaction_errors']
    assert all(e.get('phase','').startswith('holder') for e in report['transaction_errors'])
    assert 'DO_NOT_PUBLISH' not in str(report)
    window=report['coverage']['history_windows'][0]
    assert window['stop_reason']=='PROVIDER_EMPTY_PAGE'
    assert window['next_before']=='older' and window['signature_count']==(2 if with_buy else 1)
    assert rpc.requests[-1][1][1]['before']=='older'
    assert len(report['trade_evidence'])==(1 if with_buy else 0)


@pytest.mark.parametrize('with_buy',[False,True])
def test_successful_exhaustion_still_reports_current_account_scope(monkeypatch,with_buy):
    report,rpc=analyze(monkeypatch,transaction('older',7),with_buy,two_accounts=True)
    first=report['holders'][0]['first_acquisition']
    assert first['status']==('CONFIRMED_ACCOUNT_COMPLETE' if with_buy else 'NO_MARKET_BUY_IN_COMPLETE_ACCOUNT_HISTORY')
    assert first['history_scope']=='ALL_SIGNATURES_OF_CURRENT_TOKEN_ACCOUNTS; CLOSED_ACCOUNTS_NOT_ENUMERATED'
    assert report['transaction_errors']==[]
    assert len(report['trade_evidence'])==(1 if with_buy else 0)
    for sig in (['older','later-buy'] if with_buy else ['older']):
        assert sum(m=='getTransaction' and p[0]==sig for m,p in rpc.requests)==1
    assert len(report['coverage']['history_windows'])==2


@pytest.mark.parametrize('method,cause',[
    (None,'SAME_SLOT_SUPPLY_RECONCILED'),
    ('NO_MINT_AUTHORITY_MONOTONIC_SUPPLY_BRACKET','NO_MINT_AUTHORITY_MONOTONIC_SUPPLY_BRACKET'),
])
def test_balance_completeness_names_the_actual_supply_reconciliation(method,cause):
    ranks={'requested':True,'status':'COMPLETE_SNAPSHOT','normalization_complete':False}
    if method:ranks['supply_bracket']={'method':method,'before_slot':1,'after_slot':3}
    report={'holder_rankings':ranks}
    row=next(r for r in report_completeness(report)['requirements'] if r['id']=='holder_balances')
    assert row['cause']==cause
    assert row['status']=='VERIFIED_SNAPSHOT'
