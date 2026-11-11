"""Complete mint-account enumeration and owner ranking, synthetic RPC only."""
import copy
import pytest
from mission_agent.meme import holder_ranks as ranks

P='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
P22='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'

def key(n):
    alphabet='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    data=n.to_bytes(32,'big');out=''
    while n:n,r=divmod(n,58);out=alphabet[r]+out
    return '1'*(len(data)-len(data.lstrip(b'\0')))+out

MINT=key(1000)

def account(n,owner,amount,program=P):
    return {'pubkey':key(n),'account':{'owner':program,'executable':False,'data':{'parsed':{'type':'account','info':{'mint':MINT,'owner':key(owner),'state':'initialized','tokenAmount':{'amount':str(amount),'decimals':0}}}}}}

class RPC:
    def __init__(self,records,slot=100):self.records=records;self.slot=slot;self.requests=[]
    def call(self,method,params,ttl=0):
        self.requests.append((method,params))
        if method=='getProgramAccounts':return {'context':{'slot':self.slot},'value':self.records}
        if method=='getMultipleAccounts':return {'context':{'slot':100},'value':[{'owner':'11111111111111111111111111111111'} for _ in params[0]]}
        raise AssertionError(method)

def run(records,**kwargs):
    rpc=RPC(records,slot=kwargs.pop('slot',100))
    report=ranks.collect_mint_holder_ranks(MINT,P,1000,0,100,rpc,lambda owner,info:('LP','fixture') if owner==key(200) else ('ORDINARY','fixture'),normalization_declared=True,**kwargs)
    return report,rpc


def test_lp_heavy_ranks_beyond_raw_twenty_find_the_actual_eligible_owner_top10():
    records=[account(i,200,40) for i in range(1,21)]
    records += [account(30+i,300+i,20) for i in range(10)]
    out,rpc=run(records)
    assert out['status']=='COMPLETE_SNAPSHOT'
    assert out['account_count']==30 and out['nonzero_owner_count']==11
    assert out['metrics']['GLOBAL_OWNER_TOP10_PCT']=='98.0000'
    assert out['metrics']['GLOBAL_EX_LP_OWNER_TOP10_PCT']=='20.0000'
    assert len(out['owners'])==11
    assert out['owners'][0]['raw']=='800' and out['owners'][0]['account_count']==20
    opts=rpc.requests[0][1][1]
    assert opts['withContext'] is True and opts['encoding']=='base64' and opts['dataSlice']=={'offset':0,'length':166}
    assert opts['filters']==[{'dataSize':165},{'memcmp':{'offset':0,'bytes':MINT}}]
    assert opts['minContextSlot']==100


def test_owner_aggregation_precedes_ranking_even_when_each_account_is_small():
    records=[account(i,100+i,40) for i in range(1,21)]
    records += [account(30+i,500,20) for i in range(10)]
    out,_=run(records)
    assert out['owners'][0]['owner']==key(500)
    assert out['owners'][0]['raw']=='200'
    assert out['metrics']['GLOBAL_OWNER_TOP10_PCT']=='56.0000'


@pytest.mark.parametrize('change',['mint','program','amount','decimals','owner','type','duplicate','unparsed'])
def test_invalid_or_duplicate_account_rows_never_produce_global_ranks(change):
    records=[account(1,301,1000)]
    row=records[0];info=row['account']['data']['parsed']['info']
    if change=='mint':info['mint']=key(999)
    elif change=='program':row['account']['owner']=P22
    elif change=='amount':info['tokenAmount']['amount']='-1'
    elif change=='decimals':info['tokenAmount']['decimals']=9
    elif change=='owner':info['owner']='invalid'
    elif change=='type':row['account']['data']['parsed']['type']='mint'
    elif change=='duplicate':records.append(copy.deepcopy(row))
    elif change=='unparsed':row['account']['data']=['AA==','base64']
    with pytest.raises(ranks.HolderRankSourceError):run(records)


def test_account_limit_rejects_instead_of_truncating_and_promoting():
    with pytest.raises(ranks.HolderRankSourceError,match='ACCOUNT_LIMIT'):run([account(1,301,1000)],max_accounts=0)


def test_sum_mismatch_cannot_be_complete_even_when_rpc_returns_valid_json():
    out,_=run([account(1,301,900)])
    assert out['status']=='INCOMPLETE_EVIDENCE'
    assert out['reason']=='SUPPLY_SUM_MISMATCH'
    assert out['metrics']['GLOBAL_OWNER_TOP10_PCT']=='UNRESOLVED'


def test_different_slots_do_not_upgrade_a_matching_total_to_exact_percentages():
    out,_=run([account(1,301,1000)],slot=101)
    assert out['status']=='INCOMPLETE_EVIDENCE'
    assert out['reason']=='SNAPSHOT_SLOT_UNRECONCILED'
    assert out['owners'][0]['raw']=='1000'
    assert out['owners'][0]['supply_pct']=='UNRESOLVED'


def test_unknown_normalization_preserves_raw_global_rank_but_not_exclusion_claims():
    rpc=RPC([account(1,301,1000)])
    out=ranks.collect_mint_holder_ranks(MINT,P,1000,0,100,rpc,lambda *args:('UNRESOLVED','fixture'),normalization_declared=False)
    assert out['status']=='COMPLETE_SNAPSHOT'
    assert out['metrics']['GLOBAL_OWNER_TOP10_PCT']=='100.0000'
    assert out['metrics']['GLOBAL_EX_LP_OWNER_TOP10_PCT']=='UNRESOLVED'


def test_token2022_does_not_use_165_byte_filter_that_would_exclude_extensions():
    rpc=RPC([account(1,301,1000,P22)])
    out=ranks.collect_mint_holder_ranks(MINT,P22,1000,0,100,rpc,lambda *args:('ORDINARY','fixture'))
    assert out['status']=='COMPLETE_SNAPSHOT'
    assert rpc.requests[0][1][1]['filters']==[{'memcmp':{'offset':0,'bytes':MINT}}]


def test_owner_metadata_batches_never_exceed_rpc_hundred_account_limit():
    records=[account(i,1000+i,1) for i in range(1,201)]+[account(300,2000,800)]
    _,rpc=run(records)
    batches=[params[0] for method,params in rpc.requests if method=='getMultipleAccounts']
    assert [len(b) for b in batches]==[100,100,1]


@pytest.mark.parametrize('result',[[],{'value':[]},{'context':{'slot':100},'value':[],'hasMore':True}])
def test_missing_context_or_nonstandard_truncation_envelope_is_rejected(result):
    rpc=RPC([]);rpc.call=lambda *args,**kwargs:result
    with pytest.raises(ranks.HolderRankSourceError):ranks.collect_mint_holder_ranks(MINT,P,1000,0,100,rpc,lambda *args:('ORDINARY','fixture'))


def test_same_slot_top20_disagreement_prevents_complete_global_claim():
    out,_=run([account(1,301,1000)],expected_top_accounts={key(1):900},largest_slot=100)
    assert out['status']=='INCOMPLETE_EVIDENCE' and out['reason']=='TOP20_RECONCILIATION_MISMATCH'
    assert out['metrics']['GLOBAL_OWNER_TOP10_PCT']=='UNRESOLVED'


def profile():return {'status':'OK','program_id':P,'is_initialized':True,'mint_authority':None,'freeze_authority':None}


def test_actual_analyzer_adds_full_owner_rank_without_replacing_top20_history_sample():
    from mission_agent.meme.cluster import Holder,WalletClusterAnalyzer
    records=[account(i,200,40) for i in range(1,21)]+[account(30+i,300+i,20) for i in range(10)]
    a=WalletClusterAnalyzer(MINT,rpc=RPC(records),enumerate_holder_ranks=True,special_registry={'normalization_complete':True,'addresses':{key(200):{'role':'LP','source':'fixture'}}})
    def sample():
        a._snapshot_slots={'supply':100,'largest_accounts':100,'account_batches':[100,100]}
        a._largest_account_snapshot={key(i):40 for i in range(1,21)}
        return 1000,0,[Holder(key(i),key(200),40,0,'LP','fixture') for i in range(1,21)]
    a.holders=sample;a.token_profile=profile;a.market_snapshot=lambda:{'status':'UNAVAILABLE'}
    a._scan_holder=lambda *args:None;a._scan_funding=lambda *args:None
    out=a.analyze()
    assert out['analysis_completeness']['status']=='INCOMPLETE_EVIDENCE'
    assert 'wallet_history' in out['analysis_completeness']['missing_required']
    assert len(out['holders'])==20
    assert out['holder_rankings']['account_count']==30
    assert out['coverage']['eligible_owner_rank_complete'] is True
    assert out['coverage']['sample_owner_rank_complete'] is False
    assert 'ELIGIBLE_OWNER_RANKS_INCOMPLETE' not in out['coverage']['gaps']
    assert out['metrics']['GLOBAL_EX_LP_OWNER_TOP10_PCT']=='20.0000'
    assert out['metrics']['EX_LP_TOP10_PCT']=='UNRESOLVED'
    assert 'GLOBAL_OWNER_HISTORY_NOT_SCANNED' in out['coverage']['gaps']
    assert out['assessment']['cluster_status']=='WALLET_CLUSTER_UNRESOLVED'


def test_source_failure_preserves_safe_reason_instead_of_provider_text():
    from mission_agent.meme.cluster import WalletClusterAnalyzer
    rpc=RPC([])
    def failed(*args,**kwargs):raise TimeoutError('https://private.invalid/SECRET')
    rpc.call=failed
    a=WalletClusterAnalyzer(MINT,rpc=rpc,enumerate_holder_ranks=True)
    out=a._holder_ranks(profile(),1000,0)
    assert out['status']=='UNAVAILABLE' and out['reason']=='SOURCE_UNAVAILABLE'
    assert 'SECRET' not in str(out)


def test_new_enumeration_is_opted_in_only_by_standard_worker_plan():
    from mission_agent.mission_control.server import CLUSTER_PRESETS,CLUSTER_RPC_JOB_BUDGETS
    from mission_agent.meme.cluster import WalletClusterAnalyzer
    a=WalletClusterAnalyzer(MINT,rpc=RPC([]))
    assert a._holder_ranks(profile(),1000,0)['status']=='NOT_REQUESTED'
    assert a.rpc.requests==[]
    assert CLUSTER_PRESETS['standard']['enumerate_holder_ranks'] is True
    assert CLUSTER_RPC_JOB_BUDGETS['standard']=={'max_wire_attempts':1200,'max_elapsed_seconds':1800}


@pytest.mark.parametrize('cfg',[{}, {'encoding':'jsonParsed','commitment':'finalized','withContext':True,'filters':[]}])
def test_unfiltered_program_scan_rejected_before_wire_request(cfg):
    from mission_agent.meme.cluster import SolanaReadOnlyRPC
    rpc=SolanaReadOnlyRPC('https://fixture.example',fallback_endpoints=[],open_url=lambda *a,**k:pytest.fail('NO_WIRE'))
    with pytest.raises(ValueError,match='HOLDER_ENUMERATION_QUERY_INVALID'):rpc.call('getProgramAccounts',[P,cfg])
    assert rpc.calls==0


def test_enumeration_response_byte_cap_stops_without_retry_or_cache(monkeypatch):
    from mission_agent.meme import cluster
    monkeypatch.setattr(cluster,'MAX_RESPONSE_BYTES',32)
    sizes=[]
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def read(self,size):sizes.append(size);return b'x'*size
    rpc=cluster.SolanaReadOnlyRPC('https://fixture.example',fallback_endpoints=[],open_url=lambda *a,**k:Response(),min_interval=0)
    with pytest.raises(cluster.RPCError,match='RPC_HOLDER_RANK_RESPONSE_LIMIT'):
        rpc.call('getProgramAccounts',[P,{'encoding':'jsonParsed','commitment':'finalized','withContext':True,'filters':[{'dataSize':165},{'memcmp':{'offset':0,'bytes':MINT}}]}])
    assert sizes==[33] and rpc.calls==1


def test_budget_cannot_be_swallowed_while_reading_full_rank_owner_metadata():
    import json
    from mission_agent.meme import cluster
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def read(self,size):return json.dumps({'result':{'context':{'slot':100},'value':[account(1,301,1000)]}}).encode()
    rpc=cluster.SolanaReadOnlyRPC('https://fixture.example',fallback_endpoints=[],open_url=lambda *a,**k:Response(),min_interval=0,max_wire_attempts=1)
    a=cluster.WalletClusterAnalyzer(MINT,rpc=rpc,enumerate_holder_ranks=True);a._snapshot_slots={'supply':100}
    with pytest.raises(cluster.RPCJobBudgetExceeded):a._holder_ranks(profile(),1000,0)
    assert rpc.calls==1
    with pytest.raises(cluster.RPCJobBudgetExceeded):rpc.assert_can_publish()


def test_owner_role_slot_drift_keeps_exclusions_unverified_but_preserves_raw_owner_rank():
    rpc=RPC([account(1,301,1000)])
    original=rpc.call
    def call(method,params,ttl=0):
        out=original(method,params,ttl)
        if method=='getMultipleAccounts':out['context']['slot']=101
        return out
    rpc.call=call
    out=ranks.collect_mint_holder_ranks(MINT,P,1000,0,100,rpc,lambda *args:('ORDINARY','fixture'),normalization_declared=True)
    assert out['status']=='COMPLETE_SNAPSHOT'
    assert out['owners'][0]['role_slot']==101
    assert out['metrics']['GLOBAL_OWNER_TOP10_PCT']=='100.0000'
    assert out['metrics']['GLOBAL_EX_LP_OWNER_TOP10_PCT']=='UNRESOLVED'
    assert out['normalization_complete'] is False


def test_owner_identity_failure_preserves_verified_raw_ranks_and_stops_metadata_work():
    from mission_agent.meme.cluster import WalletClusterAnalyzer
    rpc=RPC([account(1,301,1000)])
    original=rpc.call
    def call(method,params,ttl=0):
        if method=='getMultipleAccounts':raise TimeoutError('PRIVATE_PROVIDER_MESSAGE')
        return original(method,params,ttl)
    rpc.call=call
    a=WalletClusterAnalyzer(MINT,rpc=rpc,enumerate_holder_ranks=True)
    a._snapshot_slots={'supply':100}
    out=a._holder_ranks(profile(),1000,0)
    assert out['status']=='COMPLETE_SNAPSHOT'
    assert out['metrics']['GLOBAL_OWNER_TOP10_PCT']=='100.0000'
    assert out['metrics']['GLOBAL_EX_LP_OWNER_TOP10_PCT']=='UNRESOLVED'
    assert out['owner_metadata_reason']=='OWNER_METADATA_UNAVAILABLE'
    assert 'PRIVATE_PROVIDER' not in str(out)


def _raw(n):
    import base64
    return n.to_bytes(32,'big')

def binary_account(n,owner,amount,program=P22,space=170,state=1,account_type=2,mint=None):
    import base64
    from mission_agent.meme.holder_ranks import _b58
    mint_bytes=_raw(1000)
    b=bytearray(166 if space>165 else 165)
    b[0:32]=mint_bytes if mint is None else mint;b[32:64]=_raw(owner);b[64:72]=amount.to_bytes(8,'little');b[108]=state
    if space>165:b[165]=account_type
    return {'pubkey':key(n),'account':{'owner':program,'executable':False,'space':space,'data':[base64.b64encode(bytes(b)).decode(),'base64']}}


def test_binary_slice_rows_decode_owner_and_amount_for_token2022_extensions():
    rpc=RPC([binary_account(1,301,600),binary_account(2,302,400,space=165)])
    out=ranks.collect_mint_holder_ranks(MINT,P22,1000,0,100,rpc,lambda *a:('ORDINARY','fixture'))
    assert out['status']=='COMPLETE_SNAPSHOT' and out['encoding']=='base64'
    assert [(r['owner'],r['raw']) for r in out['owners']]==[(key(301),'600'),(key(302),'400')]


@pytest.mark.parametrize('kw',[{'mint':_raw(999)},{'state':0},{'account_type':1},{'space':166+0,'account_type':3}])
def test_binary_rows_with_wrong_mint_state_or_account_type_are_rejected(kw):
    with pytest.raises(ranks.HolderRankSourceError,match='ACCOUNT_ROW_INVALID'):
        ranks.collect_mint_holder_ranks(MINT,P22,1000,0,100,RPC([binary_account(1,301,1000,**kw)]),lambda *a:('ORDINARY','fixture'))


def test_legacy_program_rejects_extended_binary_rows():
    with pytest.raises(ranks.HolderRankSourceError):
        ranks.collect_mint_holder_ranks(MINT,P,1000,0,100,RPC([binary_account(1,301,1000,program=P)]),lambda *a:('ORDINARY','fixture'))


def test_unsliced_or_wrong_slice_binary_query_rejected_before_wire():
    base={'encoding':'base64','commitment':'finalized','withContext':True,'filters':[{'memcmp':{'offset':0,'bytes':MINT}}]}
    assert not ranks.valid_enumeration_query([P22,base])
    assert not ranks.valid_enumeration_query([P22,{**base,'dataSlice':{'offset':0,'length':72}}])
    assert ranks.valid_enumeration_query([P22,{**base,'dataSlice':{'offset':0,'length':166}}])
    assert not ranks.valid_enumeration_query([P22,{**base,'encoding':'jsonParsed','dataSlice':{'offset':0,'length':166}}])


def test_supply_bracket_upgrades_only_with_fixed_supply_and_equal_later_reading():
    rows=[binary_account(1,301,1000)]
    ok=ranks.collect_mint_holder_ranks(MINT,P22,1000,0,90,RPC(rows,slot=100),lambda *a:('ORDINARY','fixture'),supply_fixed_above=True,supply_recheck=lambda:(1000,105))
    assert ok['status']=='COMPLETE_SNAPSHOT' and ok['supply_bracket']['after_slot']==105
    for kw in [dict(supply_fixed_above=False,supply_recheck=lambda:(1000,105)),dict(supply_fixed_above=True,supply_recheck=lambda:(999,105)),
               dict(supply_fixed_above=True,supply_recheck=lambda:(1000,99)),dict(supply_fixed_above=True,supply_recheck=lambda:1/0)]:
        out=ranks.collect_mint_holder_ranks(MINT,P22,1000,0,90,RPC(rows,slot=100),lambda *a:('ORDINARY','fixture'),**kw)
        assert out['status']=='INCOMPLETE_EVIDENCE' and out['reason']=='SNAPSHOT_SLOT_UNRECONCILED'


def test_curve_check_separates_keypairs_from_pdas():
    assert ranks.on_ed25519_curve('6hSjCsmRARbo6nszzGUN8L8j86JWprnqQXKSBfQeNDc4') is True
    assert ranks.on_ed25519_curve('2B8tftZ5ww8TREMr3pgkgERLNjJyJxEAPWMENViGMsL4') is False
    assert ranks.on_ed25519_curve('FcFu24r8M8TuTAhEjBSJsqhrPxeumUsKg7ZGzXAi4h9M') is False
    assert ranks.on_ed25519_curve('not-a-key') is None


def test_missing_owner_account_is_ordinary_only_when_on_curve():
    from mission_agent.meme.cluster import WalletClusterAnalyzer
    a=WalletClusterAnalyzer(MINT,rpc=RPC([]))
    assert a._role('6hSjCsmRARbo6nszzGUN8L8j86JWprnqQXKSBfQeNDc4',{'value':None})==('ORDINARY','RPC_NO_ACCOUNT_ON_CURVE_KEYPAIR')
    assert a._role('2B8tftZ5ww8TREMr3pgkgERLNjJyJxEAPWMENViGMsL4',{'value':None})==('UNRESOLVED','RPC_NO_ACCOUNT_OFF_CURVE_PDA')
    assert a._role('6hSjCsmRARbo6nszzGUN8L8j86JWprnqQXKSBfQeNDc4',None)==('UNRESOLVED','ACCOUNT_INFO_UNAVAILABLE')


def test_verified_pool_exclusion_uses_only_bound_self_authority_pools(monkeypatch):
    monkeypatch.setattr(ranks,'discover_owner_pool_hint',lambda mint,owner,*a:{'authority':owner,'pair_address':owner,'target_vault':'v'} if owner==key(200) else None)
    records=[account(1,200,500),account(2,301,300),account(3,302,200)]
    out,_=run(records)
    assert out['verified_pool_authorities']==[key(200)]
    assert out['metrics']['GLOBAL_OWNER_TOP10_PCT']=='100.0000'
    assert out['metrics']['GLOBAL_EX_VERIFIED_POOLS_OWNER_TOP10_PCT']=='50.0000'


def test_no_bound_pool_keeps_verified_pool_metric_unresolved():
    out,_=run([account(1,301,1000)])
    assert out['metrics']['GLOBAL_EX_VERIFIED_POOLS_OWNER_TOP10_PCT']=='UNRESOLVED'
