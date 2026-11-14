"""Same-pool independent indexer comparison; injected HTTP only."""
import io
import urllib.request
import urllib.response
import json
import urllib.error
from email.message import Message
import pytest
from mission_agent.meme.market_parity import GeckoTerminalMarketClient,attach_market_comparison,MAX_RESPONSE_BYTES,NoMarketRedirect
from mission_agent.meme.cluster import report_completeness,WalletClusterAnalyzer
from test_meme_holder_ranks import key,MINT

POOL=key(701);QUOTE=key(702)


def primary():
    return {'status':'OK','source':'DEXSCREENER_API','mint':MINT,'observed_at':100,
            'price_usd':'2','main_pair':{'pair_address':POOL,'base_address':MINT,'quote_address':QUOTE,'liquidity_usd':'1000'}}


def payload(reverse=False):
    base,quote=(QUOTE,MINT) if reverse else (MINT,QUOTE)
    return {'data':{'id':'solana_'+POOL,'type':'pool','attributes':{
        'address':POOL,'base_token_price_usd':'8' if reverse else '2.5',
        'quote_token_price_usd':'2.5' if reverse else '8','reserve_in_usd':'900'},
        'relationships':{'base_token':{'data':{'id':'solana_'+base,'type':'token'}},
                         'quote_token':{'data':{'id':'solana_'+quote,'type':'token'}}}}}


class Reply:
    def __init__(self,value):self.body=json.dumps(value).encode();self.read_limits=[]
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):self.read_limits.append(n);return self.body[:n]


def client(value=None):
    calls=[];response=Reply(payload() if value is None else value)
    def transport(req,timeout):calls.append((req.full_url,timeout,dict(req.headers)));return response
    return GeckoTerminalMarketClient(open_url=transport,clock=lambda:102),calls,response


@pytest.mark.parametrize('reverse',[False,True])
def test_exact_pool_and_quote_orientation_compare_same_target_token(reverse):
    c,calls,response=client(payload(reverse));source=primary();out=attach_market_comparison(MINT,source,c)
    assert out['comparison']['status']=='INDEXER_SNAPSHOTS_COMPARED'
    assert out['comparison']['metrics']['price_usd']['independent']=='2.5'
    assert out['comparison']['metrics']['price_usd']['difference_pct_of_primary']=='25.0000'
    assert out['comparison']['metrics']['pool_liquidity_usd']['difference_pct_of_primary']=='-10.0000'
    assert out['comparison']['retrieval_gap_seconds']==2
    assert out['comparison']['same_chain_snapshot'] is False
    assert out['comparison']['provider_asof']=='UNVERIFIED'
    assert source==primary()
    assert calls[0][0]=='https://api.geckoterminal.com/api/v2/networks/solana/pools/'+POOL
    assert len(calls)==1 and calls[0][1]==8
    assert response.read_limits==[MAX_RESPONSE_BYTES+1]


@pytest.mark.parametrize('change',['pool','id','mint','quote','token_type','network'])
def test_wrong_pool_or_token_identity_never_yields_numeric_comparison(change):
    value=payload();data=value['data']
    if change=='pool':data['attributes']['address']=QUOTE
    elif change=='id':data['id']='solana_'+QUOTE
    elif change=='mint':data['relationships']['base_token']['data']['id']='solana_'+key(99)
    elif change=='quote':data['relationships']['quote_token']['data']['id']='solana_'+key(99)
    elif change=='token_type':data['relationships']['base_token']['data']['type']='pool'
    elif change=='network':data['id']='eth_'+POOL
    c,_,_=client(value);out=attach_market_comparison(MINT,primary(),c)
    assert out['independent_market']['status']=='UNAVAILABLE'
    assert out['comparison']['metrics']=={}


@pytest.mark.parametrize('number',[None,'NaN','Infinity','-1',True,'1e999999'])
def test_invalid_numeric_value_is_missing_not_zero_or_a_price_confirmation(number):
    value=payload();value['data']['attributes']['base_token_price_usd']=number
    c,_,_=client(value);out=attach_market_comparison(MINT,primary(),c)
    assert out['comparison']['status']=='PARTIAL_INDEXER_SNAPSHOTS'
    assert out['comparison']['metrics']['price_usd']['status']=='UNAVAILABLE'
    assert out['comparison']['metrics']['pool_liquidity_usd']['status']=='COMPARED'


def test_zero_primary_denominator_does_not_divide_or_invent_percentage():
    c,_,_=client();source=primary();source['price_usd']='0'
    row=attach_market_comparison(MINT,source,c)['comparison']['metrics']['price_usd']
    assert row['difference']=='2.5' and row['difference_pct_of_primary']=='UNRESOLVED'


def test_unverified_primary_pool_never_sends_an_independent_query():
    c,calls,_=client();source=primary();source['main_pair']['base_address']=QUOTE
    out=attach_market_comparison(MINT,source,c)
    assert calls==[] and out['independent_market']['attempted'] is False
    assert out['comparison']['metrics']=={}


@pytest.mark.parametrize('code',[302,404,429])
def test_source_failure_is_one_attempt_and_keeps_primary_without_secret_error(code):
    calls=[]
    def transport(req,timeout):
        calls.append(req.full_url)
        raise urllib.error.HTTPError('https://private.invalid/SECRET',code,'SECRET',Message(),None)
    c=GeckoTerminalMarketClient(open_url=transport,clock=lambda:102)
    out=attach_market_comparison(MINT,primary(),c)
    assert len(calls)==1 and out['price_usd']=='2'
    assert out['independent_market']['reason']=='HTTP_'+str(code)
    assert 'SECRET' not in str(out)


def test_response_limit_does_not_retry_or_parse_truncated_data():
    c,calls,response=client();response.body=b' '* (MAX_RESPONSE_BYTES+2)
    out=attach_market_comparison(MINT,primary(),c)
    assert out['independent_market']['reason']=='RESPONSE_LIMIT' and len(calls)==1


def test_redirect_handler_never_follows_another_host():
    exchanges=[]
    class SyntheticHTTPS(urllib.request.HTTPSHandler):
        def https_open(self,req):
            exchanges.append(req.full_url)
            headers=Message();headers['Location']='https://private.invalid/SECRET'
            reply=urllib.response.addinfourl(io.BytesIO(b''),headers,req.full_url,code=302)
            reply.msg='Found'
            return reply
    opener=urllib.request.build_opener(NoMarketRedirect(),SyntheticHTTPS())
    out=attach_market_comparison(MINT,primary(),GeckoTerminalMarketClient(open_url=opener.open))
    assert len(exchanges)==1
    assert out['independent_market']['reason']=='HTTP_302'
    assert 'SECRET' not in str(out)


def test_successful_indexer_comparison_still_requires_raw_pool_and_holder_reconciliation():
    c,_,_=client();market=attach_market_comparison(MINT,primary(),c)
    report={'market':market};result=report_completeness(report)
    row=next(r for r in result['requirements'] if r['id']=='independent_sources')
    assert row['status']=='PARTIAL'
    assert result['status']=='INCOMPLETE_EVIDENCE'
    assert 'independent_sources' in result['missing_required']


def test_standard_only_worker_opt_in_uses_authorized_free_quota():
    from mission_agent.mission_control.server import CLUSTER_PRESETS,CLUSTER_RPC_JOB_BUDGETS
    assert CLUSTER_PRESETS['standard']['compare_market_sources'] is True
    assert not CLUSTER_PRESETS['quick'].get('compare_market_sources')
    assert not CLUSTER_PRESETS['deep'].get('compare_market_sources')
    assert CLUSTER_RPC_JOB_BUDGETS['standard']=={'max_wire_attempts':None,'max_elapsed_seconds':None}


def test_actual_analyzer_market_path_invokes_injected_second_source_once():
    c,calls,_=client()
    class Primary:
        def token_snapshot(self,mint):assert mint==MINT;return primary()
    a=WalletClusterAnalyzer(MINT,rpc=object(),market_client=Primary(),independent_market_client=c)
    assert a.market_snapshot()['comparison']['status']=='INDEXER_SNAPSHOTS_COMPARED'
    assert len(calls)==1


def test_streaming_body_has_a_read_deadline_and_no_retry():
    ticks=iter([0,0,9]);calls=[]
    class Slow(Reply):
        def read1(self,n):calls.append(n);return b' '
    c=GeckoTerminalMarketClient(open_url=lambda *a,**k:Slow({}),clock=lambda:102,monotonic=lambda:next(ticks))
    out=attach_market_comparison(MINT,primary(),c)
    assert len(calls)==1 and out['independent_market']['reason']=='NETWORK_OR_RESPONSE_INVALID'
    assert out['price_usd']=='2'


def test_explicitly_disabled_comparison_does_not_read_injected_provider():
    c,calls,_=client()
    class Primary:
        def token_snapshot(self,mint):return primary()
    a=WalletClusterAnalyzer(MINT,rpc=object(),market_client=Primary(),independent_market_client=c,compare_market_sources=False)
    assert 'comparison' not in a.market_snapshot() and calls==[]
