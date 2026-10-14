"""C02 adversarial fixtures are synthetic; not live business acceptance."""
from mission_agent.meme.identity import reconcile_identity, metadata_address, read_metadata

MINT='So11111111111111111111111111111111111111112'
OTHER='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'

def test_conflict_never_selects_market_silently():
    profile={'mint':MINT,'status':'OK','mint_account_status':'VERIFIED','metadata':{'status':'VERIFIED','records':[{'mint':MINT,'name':'Agency','symbol':'Agency','source':'CHAIN'}]}}
    market={'status':'OK','mint':MINT,'name':'Other','symbol':'Other','identity_records':[{'mint':MINT,'name':'Other','symbol':'Other','source':'DEX'}]}
    result=reconcile_identity(MINT,profile,market)
    assert result['conflict_status']=='TOKEN_IDENTITY_CONFLICT'
    assert result['display_name'] is None

def test_name_dedup_and_same_name_different_mint_isolation():
    for mint in (MINT,OTHER):
        profile={'mint':mint,'status':'OK','mint_account_status':'VERIFIED','metadata':{'status':'VERIFIED','records':[{'mint':mint,'name':'Agency','symbol':'Agency','source':'CHAIN'}]}}
        result=reconcile_identity(mint,profile,{'status':'UNAVAILABLE'})
        assert result['mint']==mint
        assert result['display_label']=='Agency'

def test_wrong_mint_profile_fails_closed():
    result=reconcile_identity(MINT,{'mint':OTHER,'status':'OK','mint_account_status':'VERIFIED','metadata':{'status':'VERIFIED','records':[{'mint':OTHER,'name':'Agency','symbol':'A'}]}},{})
    assert result['identity_status']=='UNCONFIRMED'
    assert result['display_name'] is None

def test_rpc_failure_records_attempt():
    class RPC:
        def call(self,*args,**kwargs): raise TimeoutError()
    result=read_metadata(MINT,RPC(),{})
    assert result['status']=='UNCONFIRMED'
    assert result['attempts'][0]['reason']=='TimeoutError'

def test_token2022_self_metadata_exact_mint():
    value={'owner':'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb','data':{'parsed':{'type':'mint','info':{'extensions':[{'extension':'metadataPointer','state':{'metadataAddress':MINT}},{'extension':'tokenMetadata','state':{'mint':MINT,'name':'Agency','symbol':'Agency','updateAuthority':OTHER}}]}}}}
    class RPC:
        def call(self,*args,**kwargs): return {'value':None,'context':{'slot':1}}
    result=read_metadata(MINT,RPC(),{'value':value,'context':{'slot':2}})
    assert result['records'][0]['update_authority']==OTHER
    assert result['records'][0]['mint']==MINT
    assert result['status']=='VERIFIED'

def test_pda_is_deterministic_and_mint_specific():
    assert metadata_address(MINT)==metadata_address(MINT)
    assert metadata_address(MINT)!=metadata_address(OTHER)


def test_saved_official_rpc_real_same_name_mints_and_programs():
    import json
    from pathlib import Path
    from mission_agent.meme.cluster import WalletClusterAnalyzer
    root=Path(__file__).resolve().parents[2]/'meme/evidence/c02'
    rows=json.loads((root/'official-rpc-attempts.json').read_text())
    markets=json.loads((root/'raw-market-responses.json').read_text())
    from mission_agent.meme.market import DexScreenerMarketClient
    from test_meme_market_and_rpc import Response
    class Replay:
        def call(self,method,params,ttl=0):
            assert method=='getAccountInfo'
            return next(r['response']['result'] for r in rows if r['request']['params']==params)
    mint_a=rows[0]['mint'];mint_b='4cdbUv2X2TUymvdBYSo4DrKXChMVwSnHHZjMyWhBpump'
    results=[]
    for mint in (mint_a,mint_b,OTHER):
        payload=next(r['response'] for r in markets if r['url'].endswith('/'+mint))
        market=DexScreenerMarketClient(open_url=lambda *a,**k:Response(payload)).token_snapshot(mint)
        profile=WalletClusterAnalyzer(mint,rpc=Replay()).token_profile()
        result=reconcile_identity(mint,profile,market);results.append(result)
        assert result['identity_status']=='VERIFIED'
        assert result['market_match_status']=='EXACT_BASE_MINT_MATCH'
        assert all(r['mint']==mint for r in result['sources'])
    assert results[0]['display_label']==results[1]['display_label']=='Agency'
    assert results[0]['mint']!=results[1]['mint']
    assert results[2]['display_label']=='USD Coin / USDC'


def test_real_metaplex_wrong_owner_mint_truncation_are_rejected():
    import json,copy
    from pathlib import Path
    rows=json.loads((Path(__file__).resolve().parents[2]/'meme/evidence/c02/official-rpc-attempts.json').read_text())
    mint_result=rows[4]['response']['result'];meta=rows[5]['response']['result']
    for kind in ('owner','mint','truncated'):
        bad=copy.deepcopy(meta)
        if kind=='owner':bad['value']['owner']=TOKEN22_FOR_TEST
        else:
            import base64
            raw=base64.b64decode(bad['value']['data'][0])
            raw=raw[:65] if kind=='truncated' else raw[:33]+bytes(32)+raw[65:]
            bad['value']['data'][0]=base64.b64encode(raw).decode()
        class RPC:
            def call(self,*args,**kwargs):return bad
        result=read_metadata(OTHER,RPC(),mint_result)
        assert result['status']=='UNCONFIRMED'
        assert not result['records']

TOKEN22_FOR_TEST='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'


def test_real_null_mint_never_becomes_token_identity():
    import json
    from pathlib import Path
    from mission_agent.meme.cluster import WalletClusterAnalyzer
    rows=json.loads((Path(__file__).resolve().parents[2]/'meme/evidence/c02/official-rpc-attempts.json').read_text())
    class RPC:
        def call(self,*args,**kwargs):return rows[2]['response']['result']
    profile=WalletClusterAnalyzer(rows[2]['mint'],rpc=RPC()).token_profile()
    assert profile['status']=='UNCONFIRMED'
    assert profile['reason']=='MINT_ACCOUNT_NOT_VERIFIED'


def test_same_name_real_mints_rpc_sqlite_cache_stays_exact(tmp_path):
    import json
    from pathlib import Path
    from mission_agent.meme.cluster import SolanaReadOnlyRPC,RpcCache,WalletClusterAnalyzer
    from test_meme_market_and_rpc import Response
    rows=json.loads((Path(__file__).resolve().parents[2]/'meme/evidence/c02/official-rpc-attempts.json').read_text())
    calls=[]
    def open_url(request,**kwargs):
        payload=json.loads(request.data);calls.append(payload['params'][0])
        return Response(next(r['response'] for r in rows if r['request']['params']==payload['params']))
    cache=RpcCache(tmp_path/'research-only.sqlite')
    rpc=SolanaReadOnlyRPC('https://api.mainnet-beta.solana.com',fallback_endpoints=[],min_interval=0,cache=cache,open_url=open_url)
    mint_a=rows[0]['mint'];mint_b='4cdbUv2X2TUymvdBYSo4DrKXChMVwSnHHZjMyWhBpump'
    first=WalletClusterAnalyzer(mint_a,rpc=rpc).token_profile()
    second=WalletClusterAnalyzer(mint_b,rpc=rpc).token_profile()
    again=WalletClusterAnalyzer(mint_a,rpc=rpc).token_profile()
    assert first['metadata']['records'][0]['mint']==again['metadata']['records'][0]['mint']==mint_a
    assert second['metadata']['records'][0]['mint']==mint_b
    assert mint_a in calls and mint_b in calls
    assert rpc.cache_hits>0
    cache.close()


def test_metadata_absent_does_not_promote_real_market_identity():
    import json,copy
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]/'meme/evidence/c02'
    case=json.loads((root/'real-case-results.json').read_text())[0]
    # Explicit counterfactual outage on a real market response; not real issuer state.
    profile=copy.deepcopy(case['token_profile']);profile['metadata']={'status':'UNCONFIRMED','records':[], 'attempts':[{'source':'TOKEN2022_METADATA','reason':'INJECTED_METADATA_MISSING'}]}
    result=reconcile_identity(case['mint'],profile,case['market'])
    assert result['identity_status']=='UNCONFIRMED'
    assert result['display_name'] is None
    assert any(r['source']=='DEXSCREENER_API' for r in result['sources'])
    assert result['metadata_attempts'][0]['reason']=='INJECTED_METADATA_MISSING'
