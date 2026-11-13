"""One holder's unknown history cannot relabel another holder's read coverage."""
import pytest

from mission_agent.meme import cluster
from mission_agent.meme.cluster import Holder, WalletClusterAnalyzer
from mission_agent.meme.holder_ranks import _b58
from mission_agent.signals.classifier import classify

MINT='So11111111111111111111111111111111111111112'
A,B,TA,TB=[_b58(bytes(31)+bytes([n])) for n in (2,3,4,5)]
PROGRAM='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'


class RPC:
    calls=0;cache_hits=0;endpoint='OFFLINE';endpoints=[]
    def __init__(self,failure):self.failure=failure
    def call(self,method,params,ttl=0):
        if method=='getSignaturesForAddress':
            if params[1].get('before'):
                if self.failure=='pagination' and params[0]==TA:raise TimeoutError('PRIVATE_URL')
                return []
            sig='a-unknown' if params[0]==TA else 'b-buy'
            return [{'signature':sig,'slot':7,'blockTime':7}]
        assert method=='getTransaction'
        if self.failure=='timeout' and params[0]=='a-unknown':raise TimeoutError('PRIVATE_URL')
        return {'slot':8 if self.failure=='context' and params[0]=='a-unknown' else 7,
                'blockTime':7,'transaction':{'signatures':[params[0]],'message':{'accountKeys':[],'instructions':[]}},
                'meta':{'err':None,'preBalances':[],'postBalances':[],'preTokenBalances':[],'postTokenBalances':[]}}


class Probe(WalletClusterAnalyzer):
    def token_profile(self):return {'status':'OK','program_id':PROGRAM,'is_initialized':True,'mint_authority':None,'freeze_authority':None}
    def holders(self):return 100,0,[Holder(TA,A,50,0,'ORDINARY','fixture'),Holder(TB,B,50,0,'ORDINARY','fixture')]
    def _holder_ranks(self,*args):
        return {'requested':True,'status':'COMPLETE_SNAPSHOT','normalization_complete':False,'metrics':{},
                'accounts':[{'token_account':t,'owner':o,'raw':'50','decimals':0} for t,o in [(TA,A),(TB,B)]],
                'owners':[{'owner':o,'raw':'50','role':'ORDINARY'} for o in [A,B]]}
    def _scan_funding(self,*args,**kwargs):pass


def report(monkeypatch,failure='unknown',repeat=False,legacy=False):
    def classify(sig,tx,owner):
        if owner==A:return {'classification':'UNKNOWN_NEEDS_REVIEW','classification_reason':'WALLET_NOT_SIGNER_AUTHORITY_UNPROVEN'}
        return {'classification':'ACTIVE_TRADE','trade':{'mint':MINT,'direction':'BUY'}}
    monkeypatch.setattr(cluster,'classify',classify)
    p=Probe(MINT,rpc=RPC(failure),enumerate_holder_ranks=True,deep_holders=2,history_max_pages=2,
            history_per_holder=5,adaptive_history_per_holder=6 if repeat else None,adaptive_history_max_pages=2)
    if legacy:
        p._derive_pair_edges=lambda:p.tx_errors.append({'phase':'holder','signature':'legacy','error':'UNSCOPED'})
    return p.analyze()


@pytest.mark.parametrize('failure',['unknown','timeout','context','pagination'])
def test_errors_are_scoped_to_the_owner_whose_scan_produced_them(monkeypatch,failure):
    r=report(monkeypatch,failure)
    firsts={h['owner']:h['first_acquisition'] for h in r['holders']}
    assert firsts[A]['status']=='UNRESOLVED'
    assert firsts[B]['status']=='CONFIRMED_ACCOUNT_COMPLETE'
    assert firsts[B]['history_scope']=='ALL_SIGNATURES_OF_CURRENT_TOKEN_ACCOUNTS; CLOSED_ACCOUNTS_NOT_ENUMERATED'
    assert all(e['owner']==A and e['token_account']==TA for e in r['transaction_errors'])
    assert 'PRIVATE_URL' not in str(r)


def test_unscoped_legacy_holder_error_still_blocks_completeness(monkeypatch):
    r=report(monkeypatch,legacy=True)
    assert next(h for h in r['holders'] if h['owner']==B)['first_acquisition']['status']=='CONFIRMED_BOUNDED'


def test_classification_gap_summary_separates_observations_signatures_and_owner_contexts(monkeypatch):
    r=report(monkeypatch,repeat=True)
    c=r['coverage']['holder_classification_gaps']
    assert c['observation_records']==2 and c['unique_owner_signatures']==c['unique_signatures']==1
    assert c['affected_owners']==1 and c['unscoped_records']==0
    assert c['reason_counts']=={'WALLET_NOT_SIGNER_AUTHORITY_UNPROVEN':1}
    assert all(e['classification_reason']=='WALLET_NOT_SIGNER_AUTHORITY_UNPROVEN' for e in r['transaction_errors'])
    assert len(r['trade_evidence'])==1


def test_owner_missing_from_message_keys_is_diagnosed_without_becoming_a_trade():
    tx={'slot':7,'transaction':{'message':{'accountKeys':[{'pubkey':B,'signer':True}]}},'meta':{}}
    c=classify('fixture',tx,A)
    assert c['classification']=='UNKNOWN_NEEDS_REVIEW' and c['trade'] is None
    assert c['classification_details']['chain_metadata_reason']=='WALLET_NOT_REFERENCED'
