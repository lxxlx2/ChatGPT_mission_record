"""Owner-account pool discovery without indexer dependency, injected RPC only."""
import copy,hashlib
import pytest
from test_meme_pool_vaults import account,k,P,MINT,QUOTE,POOL,BASE_VAULT,QUOTE_VAULT,pool,PROGRAM
from test_meme_holder_ranks import account as token_row,key
from mission_agent.meme.holder_ranks import collect_mint_holder_ranks


def source_with_owner_pool(slot=101,mutate=None,owners=1):
    records=[token_row(4000,3000,600),token_row(9000,3000,400)]
    raw=pool()
    if mutate:mutate(raw)
    metadata=account(PROGRAM,raw)
    class RPC:
        calls=[]
        def call(self,method,params,ttl=0):
            self.calls.append((method,params))
            if method=='getProgramAccounts':return {'context':{'slot':100},'value':records}
            return {'context':{'slot':slot},'value':[metadata for _ in params[0]]}
    rpc=RPC();rpc.calls=[]
    result=collect_mint_holder_ranks(MINT,P,1000,0,100,rpc,lambda *args:('PROGRAM_OWNED_UNRESOLVED','fixture'))
    return result,rpc,metadata


def test_existing_owner_reads_extract_a_pool_hint_without_an_extra_request():
    result,rpc,_=source_with_owner_pool()
    hint=result['owner_pool_hints'][0]
    assert len(rpc.calls)==2
    assert hint['pair_address']==POOL and hint['base_address']==MINT and hint['quote_address']==QUOTE
    assert hint['target_vault']==BASE_VAULT and hint['authority']==POOL
    assert hint['owner_metadata_slot']==101 and hint['enumeration_slot']==100
    assert hint['enumeration_response_sha256']==result['response_sha256']
    assert len(hint['owner_metadata_response_sha256'])==64
    assert result['owner_pool_discovery']['scope']=='SELF_AUTHORITY_POOL_OWNERS_NOT_GLOBAL_AUTHORITY_REVERSE_LOOKUP'

@pytest.mark.parametrize('bad',['not_target_mint','vault_not_held','bad_layout','older_slot'])
def test_nonmatching_owner_account_never_becomes_a_pool_hint(bad):
    def mutate(b):
        if bad=='not_target_mint':b[43:75]=k(9999)
        elif bad=='vault_not_held':b[139:171]=k(9999)
        elif bad=='bad_layout':b[0]^=1
    result,_,_=source_with_owner_pool(slot=99 if bad=='older_slot' else 101,mutate=mutate)
    assert result['owner_pool_hints']==[]


def owner_source():
    s,_,_=source_with_owner_pool()
    return s


def cohort_rpc(source,metadata,actual=102):
    from mission_agent.meme.pool_programs import pubkey_bytes
    m=bytearray(82);m[36:44]=(1000).to_bytes(8,'little');m[45]=1
    values={MINT:account(P,m),POOL:metadata}
    for r in source['accounts']:
        b=bytearray(165);b[:32]=pubkey_bytes(MINT);b[32:64]=pubkey_bytes(r['owner']);b[64:72]=int(r['raw']).to_bytes(8,'little');b[108]=1
        values[r['token_account']]=account(P,b)
    class RPC:
        calls=[]
        def call(self,method,params,ttl=0):
            self.calls.append((method,params));return {'context':{'slot':actual},'value':[values[a] for a in params[0]]}
    r=RPC();r.calls=[];return r


def test_pool_discovered_from_holder_owner_is_audited_when_market_is_unavailable():
    from mission_agent.meme.special_roles import collect_special_roles
    source,_,metadata=source_with_owner_pool();rpc=cohort_rpc(source,metadata)
    out=collect_special_roles(MINT,source,{'status':'UNAVAILABLE'},rpc)
    assert len(rpc.calls)==2 and len(out['pools'])==1
    assert out['pools'][0]['candidate_sources']==['HOLDER_OWNER_ACCOUNT']
    assert out['pools'][0]['status']=='POOL_IDENTITY_BOUND'
    assert out['rankings']['metrics']['known_ex_lp']['deducted_raw']=='600'
    assert out['rankings']['metrics']['known_ex_lp']['owners']==[{'owner':POOL,'raw':'400'}]
    assert out['rankings']['metrics']['known_ex_lp']['top10_pct_of_mint_supply']=='40.0000'
    assert out['rankings']['metrics']['known_ex_lp']['top10_pct_of_remaining']=='100.0000'
    assert out['discovery_scope']=='BOUNDED_INDEXER_OWNER_AND_PROGRAM_HINTS_NOT_ALL_POOLS'
    assert rpc.calls[0][1][1]['minContextSlot']==101

@pytest.mark.parametrize('bad',['hash','mint','owner','vault','slot'])
def test_malformed_stored_owner_hint_is_not_used_for_discovery(bad):
    from mission_agent.meme.special_roles import collect_special_roles
    s,_,metadata=source_with_owner_pool();h=s['owner_pool_hints'][0]
    if bad=='hash':h['enumeration_response_sha256']='bad'
    elif bad=='mint':h['base_address']=QUOTE
    elif bad=='owner':h['authority']=key(999)
    elif bad=='vault':h['target_vault']=key(999)
    else:h['owner_metadata_slot']=99
    rpc=cohort_rpc(s,metadata);out=collect_special_roles(MINT,s,{'status':'UNAVAILABLE'},rpc)
    assert not rpc.calls and out['reason']=='NO_VALID_POOL_HINTS'
    assert out['rejected_owner_pool_hints']==1


def test_indexer_and_owner_hint_merge_once_and_preserve_both_sources():
    from mission_agent.meme.special_roles import collect_special_roles
    from test_meme_pool_vaults import market
    s,_,metadata=source_with_owner_pool();rpc=cohort_rpc(s,metadata)
    out=collect_special_roles(MINT,s,market(),rpc)
    assert len(out['pools'])==1 and len(rpc.calls[0][1][0])==1
    assert out['pools'][0]['candidate_sources']==['DEXSCREENER_API','HOLDER_OWNER_ACCOUNT']
    assert out['rankings']['metrics']['known_ex_lp']['deducted_raw']=='600'

@pytest.mark.parametrize('program,name,length,offsets',[
    ('whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc','Whirlpool',653,(101,181,133,213)),
    ('CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK','PoolState',1544,(73,105,137,169)),
    ('LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo','LbPair',904,(88,120,152,184))])
@pytest.mark.parametrize('reverse',[False,True])
def test_self_authority_pool_owner_hints_support_each_layout_and_target_orientation(program,name,length,offsets,reverse):
    from mission_agent.meme.holder_ranks import discover_owner_pool_hint
    b=bytearray(length);b[:8]=hashlib.sha256(('account:'+name).encode()).digest()[:8]
    for off,n in zip(offsets,((2000,1000,5000,4000) if reverse else (1000,2000,4000,5000))):b[off:off+32]=k(n)
    h=discover_owner_pool_hint(MINT,POOL,account(program,b),101,100,'a'*64,'b'*64,{BASE_VAULT:POOL})
    assert h['target_vault']==BASE_VAULT and h['quote_address']==QUOTE and h['pool_program']==program


def test_global_authority_pool_state_does_not_turn_authority_into_a_reverse_pool_index():
    from mission_agent.meme.holder_ranks import discover_owner_pool_hint
    from test_meme_special_roles import SPECS,pool_bytes
    program=SPECS[0][0];metadata=account(program,pool_bytes(SPECS[0]))
    assert discover_owner_pool_hint(MINT,POOL,metadata,101,100,'a'*64,'b'*64,{BASE_VAULT:POOL}) is None


def test_more_than8_owner_pool_hints_keep_highest_balances_deterministically_without_more_reads():
    from mission_agent.meme.pool_programs import pubkey_bytes
    records=[];metadata={}
    for i in range(12):
        owner=key(3000+i);vault=key(4000+i);b=pool()
        b[139:171]=pubkey_bytes(vault);b[171:203]=pubkey_bytes(key(5000+i))
        records.append(token_row(4000+i,3000+i,i+1));metadata[owner]=account(PROGRAM,b)
    class RPC:
        count=0
        def call(self,method,params,ttl=0):
            self.count+=1
            return {'context':{'slot':100},'value':records if method=='getProgramAccounts' else [metadata[a] for a in params[0]]}
    rpc=RPC();out=collect_mint_holder_ranks(MINT,P,78,0,100,rpc,lambda *args:('PROGRAM_OWNED_UNRESOLVED','fixture'))
    assert rpc.count==2 and len(out['owner_pool_hints'])==8
    assert out['owner_pool_hints'][0]['pair_address']==key(3011)
    assert out['owner_pool_hints'][-1]['pair_address']==key(3004)
    assert out['owner_pool_discovery']['hints_not_selected']==4


def test_changed_discovered_pool_cannot_reuse_a_prior_owner_vault_hint():
    from mission_agent.meme.special_roles import collect_special_roles
    s,_,metadata=source_with_owner_pool();changed=copy.deepcopy(metadata)
    from test_meme_pool_vaults import change_data
    change_data(changed,lambda b:b.__setitem__(slice(139,171),k(9999)))
    out=collect_special_roles(MINT,s,{'status':'UNAVAILABLE'},cohort_rpc(s,changed))
    assert out['pools'][0]['reason']=='OWNER_HINT_POOL_CHANGED'
    assert 'rankings' not in out


def test_malformed_owner_account_program_or_unparsed_layout_never_crashes_extraction():
    from mission_agent.meme.holder_ranks import discover_owner_pool_hint
    for metadata in [{'owner':[]},{'owner':PROGRAM,'executable':False,'data':{'parsed':{}}},None]:
        assert discover_owner_pool_hint(MINT,POOL,metadata,101,100,'a'*64,'b'*64,{BASE_VAULT:POOL}) is None


def test_many_indexer_hints_cannot_starve_owner_pool_candidate_within8_key_cap():
    from mission_agent.meme.special_roles import collect_special_roles
    s,_,metadata=source_with_owner_pool();base_rpc=cohort_rpc(s,metadata);calls=[]
    hints=[{'pair_address':key(6000+i),'base_address':MINT,'quote_address':QUOTE} for i in range(12)]
    class RPC:
        def call(self,method,params,ttl=0):
            calls.append(params)
            if len(calls)==1:return {'context':{'slot':102},'value':[metadata if a==POOL else None for a in params[0]]}
            return base_rpc.call(method,params,ttl=ttl)
    out=collect_special_roles(MINT,s,{'status':'OK','source':'DEXSCREENER_API','mint':MINT,'main_pair':hints[0],'pool_candidates':hints},RPC())
    assert len(calls[0][0])==8 and calls[0][0][0]==key(6000) and calls[0][0][1]==POOL
    assert out['not_selected_pool_hints']==5 and out['candidate_count']==13
    assert out['rankings']['metrics']['known_ex_lp']['deducted_raw']=='600'


def test_discovery_response_before_owner_metadata_is_not_accepted_as_current_pool():
    from mission_agent.meme.special_roles import collect_special_roles
    s,_,metadata=source_with_owner_pool();rpc=cohort_rpc(s,metadata,actual=100)
    out=collect_special_roles(MINT,s,{'status':'UNAVAILABLE'},rpc)
    assert len(rpc.calls)==1 and out['pools'][0]['reason']=='DISCOVERY_BEFORE_OWNER_HINT'
    assert 'rankings' not in out


def test_disagreeing_quote_hints_do_not_silently_select_a_preferred_source():
    from mission_agent.meme.special_roles import collect_special_roles
    from test_meme_pool_vaults import market
    s,_,metadata=source_with_owner_pool();m=market();m['main_pair']['quote_address']=key(8888)
    out=collect_special_roles(MINT,s,m,cohort_rpc(s,metadata))
    assert out['pools'][0]['reason']=='POOL_HINT_QUOTE_CONFLICT' and 'rankings' not in out
