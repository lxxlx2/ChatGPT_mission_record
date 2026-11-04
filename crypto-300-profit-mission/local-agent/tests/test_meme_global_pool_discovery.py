"""Filtered shared-authority discovery; every response and wire is injected."""
import copy,json
import pytest
from mission_agent.meme.pool_discovery import query,valid_pool_discovery_query,collect_global_pool_hints,MAX_QUERY_ACCOUNTS
from mission_agent.meme.pool_programs import CPMM,AMM_V4,stored_bump_authority,pubkey_bytes,decode_pool
from mission_agent.meme.special_roles import collect_special_roles
from test_meme_pool_vaults import MINT,QUOTE,POOL,BASE_VAULT,QUOTE_VAULT,P,account,k
from test_meme_special_roles import SPECS,pool_bytes
from test_meme_holder_ranks import key


def fixture(program=CPMM,reverse=False):
    spec=next(s for s in SPECS if s[0]==program);b=pool_bytes(spec)
    if reverse:
        a,z=spec[3][:2];b[a:a+32],b[z:z+32]=b[z:z+32],b[a:a+32]
        a,z=spec[3][2:];b[a:a+32],b[z:z+32]=b[z:z+32],b[a:a+32]
    metadata=account(program,b);d=decode_pool(metadata,POOL);authority=d['authority']
    source={'requested':True,'status':'COMPLETE_SNAPSHOT','mint':MINT,'program_id':P,'snapshot_slot':100,'supply_slot':100,
        'response_sha256':'a'*64,'account_count':2,'decimals':0,'supply_raw':'1000','total_raw':'1000','metrics':{},
        'accounts':[{'token_account':BASE_VAULT,'owner':authority,'raw':'600','decimals':0},{'token_account':key(9000),'owner':authority,'raw':'400','decimals':0}]}
    m=bytearray(82);m[36:44]=(1000).to_bytes(8,'little');m[45]=1
    values={POOL:metadata,MINT:account(P,m)}
    for row in source['accounts']:
        token=bytearray(165);token[:32]=pubkey_bytes(MINT);token[32:64]=pubkey_bytes(authority);token[64:72]=int(row['raw']).to_bytes(8,'little');token[108]=1
        values[row['token_account']]=account(P,token)
    class RPC:
        def __init__(self):self.calls=[];self.mutate=None;self.error=None
        def call(self,method,params,ttl=0):
            self.calls.append((method,copy.deepcopy(params)))
            if self.error:raise self.error
            if method=='getProgramAccounts':
                assert valid_pool_discovery_query(params)
                offset=params[1]['filters'][-1]['memcmp']['offset'];side=spec[3][:2].index(offset)
                mint=d['base_mint' if side==0 else 'quote_mint']
                result={'context':{'slot':101},'value':[{'pubkey':POOL,'account':copy.deepcopy(metadata)}] if mint==MINT else []}
                if self.mutate:self.mutate(result)
                return result
            assert method=='getMultipleAccounts' and len(params[0])<=100
            return {'context':{'slot':102},'value':[copy.deepcopy(values[a]) for a in params[0]]}
    return source,RPC(),metadata

@pytest.mark.parametrize('program',[CPMM,AMM_V4])
@pytest.mark.parametrize('reverse',[False,True])
def test_shared_global_authority_discovers_both_mint_sides_without_market_or_owner_pool_hint(program,reverse):
    source,rpc,_=fixture(program,reverse);out=collect_special_roles(MINT,source,{'status':'UNAVAILABLE'},rpc)
    g=out['program_pool_discovery'];p=out['pools'][0]
    assert g['logical_queries']==2 and len(g['hints'])==1
    assert p['candidate_sources']==['MINT_FILTERED_PROGRAM_QUERY'] and p['status']=='POOL_IDENTITY_BOUND'
    assert len(rpc.calls)==4 and [m for m,_ in rpc.calls]==['getProgramAccounts']*2+['getMultipleAccounts']*2
    assert out['rankings']['metrics']['known_ex_lp']['deducted_raw']=='600'
    assert out['rankings']['metrics']['known_ex_lp']['owners']==[{'owner':source['accounts'][0]['owner'],'raw':'400'}]
    assert out['rankings']['metrics']['known_ex_lp']['top10_pct_of_mint_supply']=='40.0000'
    assert out['rankings']['metrics']['known_ex_lp']['top10_pct_of_remaining']=='100.0000'
    assert out['all_special_roles_normalized'] is False
    assert rpc.calls[2][1][1]['minContextSlot']==101


def test_no_observed_shared_authority_means_no_program_discovery_reads():
    source,rpc,_=fixture()
    for row in source['accounts']:row['owner']=key(999)
    out=collect_global_pool_hints(MINT,source,rpc)
    assert out['status']=='NOT_REQUESTED' and out['reason']=='NO_OBSERVED_SHARED_AUTHORITY' and not rpc.calls

@pytest.mark.parametrize('bad',['no_filter','offset','float_offset','length','encoding','without_context','numeric_context','commitment','discriminator','extra','unfiltered_program'])
def test_read_allowlist_rejects_every_relaxed_or_unbounded_program_query(bad):
    params=query(MINT,CPMM,0,100);cfg=params[1]
    if bad=='no_filter':cfg['filters']=[]
    elif bad=='offset':cfg['filters'][-1]['memcmp']['offset']=0
    elif bad=='float_offset':cfg['filters'][-1]['memcmp']['offset']=168.0
    elif bad=='length':cfg['filters'][0]['dataSize']=638
    elif bad=='encoding':cfg['encoding']='jsonParsed'
    elif bad=='without_context':cfg.pop('withContext')
    elif bad=='numeric_context':cfg['withContext']=1
    elif bad=='commitment':cfg['commitment']='processed'
    elif bad=='discriminator':cfg['filters'][1]['memcmp']['bytes']='bad'
    elif bad=='extra':cfg['dataSlice']={'offset':0,'length':32}
    else:params[0]=P
    assert valid_pool_discovery_query(params) is False
    from mission_agent.meme.cluster import SolanaReadOnlyRPC
    r=SolanaReadOnlyRPC('https://fixture.example',fallback_endpoints=[],min_interval=0,open_url=lambda *a,**k:pytest.fail('must reject before wire'))
    with pytest.raises(ValueError,match='HOLDER_ENUMERATION_QUERY_INVALID'):r.call('getProgramAccounts',params)
    assert r.calls==0


def test_filtered_pool_response_has_256KiB_wire_cap_and_no_size_retry_or_cache():
    from mission_agent.meme.cluster import SolanaReadOnlyRPC,RPCError
    from mission_agent.meme.pool_vaults import MAX_RPC_BYTES
    sizes=[]
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def read(self,n):sizes.append(n);return b'x'*n
    r=SolanaReadOnlyRPC('https://fixture.example',fallback_endpoints=[],min_interval=0,open_url=lambda *a,**k:Response())
    with pytest.raises(RPCError,match='RPC_POOL_RESPONSE_LIMIT'):r.call('getProgramAccounts',query(MINT,CPMM,0,100),ttl=30)
    assert sizes==[MAX_RPC_BYTES+1] and r.calls==1

@pytest.mark.parametrize('bad',['envelope','older','too_many','duplicate','filter','layout','wrong_owner','missing_vault'])
def test_incomplete_malformed_or_unrelated_pool_response_never_becomes_an_exclusion(bad):
    source,rpc,_=fixture()
    def mutate(result):
        if not result['value']:return
        if bad=='envelope':result['hasMore']=True
        elif bad=='older':result['context']['slot']=99
        elif bad=='too_many':result['value']*=MAX_QUERY_ACCOUNTS+1
        elif bad=='duplicate':result['value']*=2
        elif bad in {'filter','layout','wrong_owner'}:
            from test_meme_pool_vaults import change_data
            if bad=='wrong_owner':result['value'][0]['account']['owner']=P
            else:change_data(result['value'][0]['account'],lambda b:b.__setitem__(slice(168,200),k(999)) if bad=='filter' else b.__delitem__(slice(630,None)))
        else:
            from test_meme_pool_vaults import change_data
            change_data(result['value'][0]['account'],lambda b:b.__setitem__(slice(72,104),k(999)))
    rpc.mutate=mutate;out=collect_global_pool_hints(MINT,source,rpc)
    assert not out['hints'] and len(rpc.calls)==2
    assert out['status']=='PARTIAL'
    assert all(a.get('coverage')!='ALL_POOLS' for a in out['attempts'])


def test_budget_exception_is_terminal_while_optional_query_failure_stays_a_source_gap():
    from mission_agent.meme.cluster import RPCJobBudgetExceeded,RPCError
    source,rpc,_=fixture();rpc.error=RPCJobBudgetExceeded('RPC_JOB_WIRE_BUDGET_EXHAUSTED')
    with pytest.raises(RPCJobBudgetExceeded):collect_global_pool_hints(MINT,source,rpc)
    assert len(rpc.calls)==1
    source,rpc,_=fixture();rpc.error=RPCError('https://private.invalid/SECRET')
    out=collect_global_pool_hints(MINT,source,rpc)
    assert len(rpc.calls)==2 and out['query_failures']==2 and not out['hints']
    assert 'SECRET' not in str(out) and 'private.invalid' not in str(out)


def test_two_observed_shared_authorities_trigger_at_most_four_fixed_queries():
    source,rpc,_=fixture();source['accounts'][1]['owner']=stored_bump_authority(AMM_V4,b'amm authority',254)
    # Empty response for the second program is still bounded evidence, no pool claim.
    original=rpc.call
    def call(method,params,ttl=0):
        if params[0]==AMM_V4:
            rpc.calls.append((method,params));return {'context':{'slot':101},'value':[]}
        return original(method,params,ttl=ttl)
    rpc.call=call;out=collect_global_pool_hints(MINT,source,rpc)
    assert out['logical_queries']==4 and len(rpc.calls)==4
    assert all(valid_pool_discovery_query(p) for _,p in rpc.calls)


def test_same_pool_from_index_and_program_lookup_is_deducted_once():
    from test_meme_pool_vaults import market
    source,rpc,_=fixture();out=collect_special_roles(MINT,source,market(),rpc)
    assert len(out['pools'])==1
    assert out['pools'][0]['candidate_sources']==['DEXSCREENER_API','MINT_FILTERED_PROGRAM_QUERY']
    assert out['rankings']['metrics']['known_ex_lp']['deducted_raw']=='600'
