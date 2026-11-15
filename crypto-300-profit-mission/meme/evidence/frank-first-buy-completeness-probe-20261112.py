"""Read-only, network-free reproducer for fixed SHA aad880991565d148aa6cc2f74fa0de1f5e6c27c7.
Run from source worktree:
PYTHONPATH=<fixed-aad-local-agent> python -B <this-script>
Only the read RPC stub below is reachable. No service, sockets or production writes.
"""
import json
from pathlib import Path
import subprocess
import sys

def no_network(event,args):
    if event.startswith("socket."):
        raise AssertionError("OFFLINE_PROBE_NETWORK_DENIED")
sys.addaudithook(no_network)
from mission_agent.meme import cluster
from mission_agent.meme.cluster import WalletClusterAnalyzer, Holder
from mission_agent.meme.holder_ranks import _b58

EXPECTED="aad880991565d148aa6cc2f74fa0de1f5e6c27c7"
source=Path(cluster.__file__).resolve().parents[2]
assert subprocess.check_output(["git","-C",str(source),"rev-parse","HEAD"],text=True).strip()==EXPECTED
assert not subprocess.check_output(["git","-C",str(source),"status","--porcelain","--","mission_agent"],text=True)
MINT="So11111111111111111111111111111111111111112"
ACCOUNT=_b58(bytes(31)+b"\x02")
OWNER=_b58(bytes(31)+b"\x03")

class StubRPC:
    endpoint='OFFLINE_FIXTURE'; endpoints=[]; calls=0; cache_hits=0
    def __init__(self,with_buy): self.requests=[]; self.with_buy=with_buy
    def call(self,method,params,ttl=0):
        self.requests.append({'method':method,'params':params})
        if method=='getSignaturesForAddress':
            if params[1].get('before'): return []
            rows=[{'signature':'unreadable-older-tx','slot':7,'blockTime':7}]
            if self.with_buy: rows.insert(0,{'signature':'known-buy','slot':9,'blockTime':9})
            return rows
        if method=='getTransaction':
            if params[0]=='unreadable-older-tx': raise TimeoutError('synthetic unavailable transaction')
            return {'slot':9,'blockTime':9,'transaction':{'signatures':['known-buy'],'message':{'accountKeys':[],'instructions':[]}},'meta':{'err':None,'preBalances':[],'postBalances':[],'preTokenBalances':[],'postTokenBalances':[]}}
        raise AssertionError('UNEXPECTED_OFFLINE_METHOD:'+method)

class Probe(WalletClusterAnalyzer):
    def token_profile(self): return {'status':'OK','program_id':'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','is_initialized':True,'mint_authority':None,'freeze_authority':None}
    def holders(self): return 100,0,[Holder(ACCOUNT,OWNER,100,0,'ORDINARY','fixture')]
    def _holder_ranks(self,*args):
        # Isolate the first-buy decision from holder enumeration; original
        # current-account selection, history reader and completeness logic run.
        return {'requested':True,'status':'COMPLETE_SNAPSHOT','supply_raw':'100','normalization_complete':False,'metrics':{},'owners':[{'owner':OWNER,'raw':'100','role':'ORDINARY'}],'accounts':[{'token_account':ACCOUNT,'owner':OWNER,'raw':'100','decimals':0}]}
    def _scan_funding(self,*args,**kwargs): return None

original_classify=cluster.classify
cluster.classify=lambda sig,tx,owner: {'classification':'ACTIVE_TRADE','trade':{'mint':MINT,'direction':'BUY'}}
results=[]
try:
    for with_buy in (False,True):
        rpc=StubRPC(with_buy)
        a=Probe(MINT,rpc=rpc,deep_holders=1,history_max_pages=2,enumerate_holder_ranks=True)
        r=a.analyze()
        results.append({'with_successfully_classified_later_buy':with_buy,'first_acquisition':r['holders'][0]['first_acquisition'],'transaction_errors':r['transaction_errors'],'history_windows':r['coverage']['history_windows'],'owner_account_history':r['coverage']['owner_account_history'],'stub_requests':rpc.requests})
finally:
    cluster.classify=original_classify
assert results[0]['transaction_errors'] and results[1]['transaction_errors']
assert results[0]['first_acquisition']['status']=='NO_MARKET_BUY_IN_COMPLETE_ACCOUNT_HISTORY'
assert results[1]['first_acquisition']['status']=='CONFIRMED_ACCOUNT_COMPLETE'
print(json.dumps({'verdict':'CONFIRMED_FALSE_COMPLETENESS_ON_UNREAD_TRANSACTION','head':'aad880991565d148aa6cc2f74fa0de1f5e6c27c7','scope':'OFFLINE_SYNTHETIC_RPC_STUB; NO_NETWORK; NO_SOURCE_MODIFICATION','results':results},ensure_ascii=False,indent=2))
