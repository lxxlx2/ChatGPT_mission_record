"""PumpSwap raw account snapshots, injected RPC only; no executable quote."""
import base64
import copy
import json
import pytest
from mission_agent.meme.pool_vaults import collect_pool_vault_snapshot,PROGRAM,POOL_DISCRIMINATOR,MAX_RPC_BYTES
from mission_agent.meme.cluster import WalletClusterAnalyzer,RPCJobBudgetExceeded
from test_meme_holder_ranks import key,P,P22

MINT=key(1000);QUOTE=key(2000);POOL=key(3000);BASE_VAULT=key(4000);QUOTE_VAULT=key(5000)


def k(n):return n.to_bytes(32,'big')


def pool():
    b=bytearray(287);b[:8]=POOL_DISCRIMINATOR;b[8]=255
    for offset,n in [(11,7000),(43,1000),(75,2000),(107,6000),(139,4000),(171,5000),(211,8000)]:b[offset:offset+32]=k(n)
    b[203:211]=(1000).to_bytes(8,'little')
    return b


def mint(decimals=0,program=P):
    b=bytearray(82);b[36:44]=(1000000).to_bytes(8,'little');b[44]=decimals;b[45]=1
    if program==P22:b.extend(bytes(83));b.append(1);b.extend(bytes(4))
    return b


def vault(token,raw,program=P):
    b=bytearray(165);b[:32]=k(token);b[32:64]=k(3000);b[64:72]=raw.to_bytes(8,'little');b[108]=1
    if program==P22:b.append(2);b.extend(bytes(4))
    return b


def account(owner,data):return {'owner':owner,'executable':False,'data':[base64.b64encode(data).decode(),'base64']}


class RPC:
    def __init__(self):
        self.requests=[];self.slot=101;self.budget=False
        self.discovery=account(PROGRAM,pool())
        self.values=[account(PROGRAM,pool()),account(P,vault(1000,100)),account(P,vault(2000,200)),account(P,mint()),account(P,mint())]
    def call(self,method,params,ttl=0):
        self.requests.append((method,params))
        if method=='getAccountInfo':return {'context':{'slot':100},'value':self.discovery}
        if self.budget:raise RPCJobBudgetExceeded('RPC_JOB_WIRE_BUDGET_EXHAUSTED')
        assert method=='getMultipleAccounts'
        return {'context':{'slot':self.slot},'value':self.values}


def market(reverse=False):
    return {'status':'OK','source':'DEXSCREENER_API','mint':QUOTE if reverse else MINT,'main_pair':{'pair_address':POOL,'base_address':QUOTE if reverse else MINT,'quote_address':MINT if reverse else QUOTE}}


def collect(rpc=None,reverse=False):return collect_pool_vault_snapshot(QUOTE if reverse else MINT,market(reverse),rpc or RPC())


def change_data(account,mutate):
    b=bytearray(base64.b64decode(account['data'][0]));mutate(b);account['data'][0]=base64.b64encode(b).decode()


@pytest.mark.parametrize('reverse',[False,True])
def test_pool_and_vaults_are_re_read_in_one_actual_context_not_pinned_to_discovery(reverse):
    rpc=RPC();out=collect(rpc,reverse)
    assert out['status']=='VAULT_BALANCE_SNAPSHOT'
    assert out['discovery_slot']==100 and out['snapshot_slot']==101
    assert rpc.requests[1][1][0]==[POOL,BASE_VAULT,QUOTE_VAULT,MINT,QUOTE]
    assert rpc.requests[1][1][1]['minContextSlot']==100
    assert out['target']['raw']==('200' if reverse else '100')
    assert out['quote']['raw']==('100' if reverse else '200')
    assert out['raw_vault_quote_per_target']==('0.5' if reverse else '2')
    assert out['price_usd']=='UNVERIFIED' and out['liquidity_usd']=='UNVERIFIED'
    assert out['executable_quote']=='NOT_COMPUTED'
    assert out['indexer_snapshot_parity']=='UNVERIFIED'
    assert len(out['response_sha256'])==64


@pytest.mark.parametrize('bad',['unsupported_program','discriminator','pair','duplicate_vault','layout','new_nonzero_tail'])
def test_unverified_pool_never_reads_untrusted_vault_addresses(bad):
    rpc=RPC()
    if bad=='unsupported_program':rpc.discovery['owner']=P
    else:
        def mutate(b):
            if bad=='discriminator':b[0]^=1
            elif bad=='pair':b[43:75]=k(99)
            elif bad=='duplicate_vault':b[171:203]=b[139:171]
            elif bad=='layout':del b[220:]
            elif bad=='new_nonzero_tail':b.extend(b'\x01')
        change_data(rpc.discovery,mutate)
    out=collect(rpc)
    assert out['status'] in {'INCOMPLETE_EVIDENCE','UNSUPPORTED'}
    assert len(rpc.requests)==1 and out.get('raw_vault_quote_per_target') is None


@pytest.mark.parametrize('bad',['missing','wrong_authority','wrong_mint','program_mismatch','uninitialized_vault','uninitialized_mint','slot_before_discovery','pool_replaced','bad_base64'])
def test_bad_batch_keeps_precision_unresolved(bad):
    rpc=RPC()
    if bad=='missing':rpc.values[1]=None
    elif bad=='program_mismatch':rpc.values[3]['owner']=P22
    elif bad=='slot_before_discovery':rpc.slot=99
    elif bad=='bad_base64':rpc.values[1]['data']=['bad','base64']
    else:
        index=0 if bad=='pool_replaced' else 3 if bad=='uninitialized_mint' else 1
        def mutate(b):
            if bad=='wrong_authority':b[32:64]=k(99)
            elif bad=='wrong_mint':b[:32]=k(99)
            elif bad=='uninitialized_vault':b[108]=0
            elif bad=='uninitialized_mint':b[45]=0
            elif bad=='pool_replaced':b[139:171]=k(99)
        change_data(rpc.values[index],mutate)
    out=collect(rpc)
    assert out['status']=='INCOMPLETE_EVIDENCE'
    assert out.get('raw_vault_quote_per_target') is None


def test_zero_target_balance_does_not_divide_or_fabricate_a_quote():
    rpc=RPC();rpc.values[1]=account(P,vault(1000,0))
    out=collect(rpc)
    assert out['target']['raw']=='0' and out['raw_vault_quote_per_target']=='UNRESOLVED'
    assert out['executable_quote']=='NOT_COMPUTED'


def test_precision_and_token2022_extensions_are_retained_without_claiming_tradability():
    rpc=RPC();rpc.values[1]=account(P22,vault(1000,100,P22));rpc.values[3]=account(P22,mint(6,P22));rpc.values[4]=account(P,mint(9))
    out=collect(rpc)
    assert out['status']=='VAULT_BALANCE_SNAPSHOT'
    assert out['target']['quantity']=='0.000100' and out['quote']['quantity']=='2.00E-7'
    assert out['raw_vault_quote_per_target']=='0.002'
    assert 'TOKEN_2022_ADJUSTMENTS_UNVERIFIED' in out['flags']


def test_virtual_reserves_fees_and_frozen_delegate_state_never_become_a_price():
    rpc=RPC()
    def pool_flags(b):
        b[245:261]=(500).to_bytes(16,'little',signed=True);b[271:279]=(10).to_bytes(8,'little');b[279:287]=(5).to_bytes(8,'little')
    change_data(rpc.values[0],pool_flags)
    def vault_flags(b):b[108]=2;b[72:76]=(1).to_bytes(4,'little')
    change_data(rpc.values[1],vault_flags)
    out=collect(rpc)
    assert out['pool_parameters']['virtual_quote_reserves']=='500'
    assert out['pool_parameters']['protocol_fees']=='10'
    assert out['raw_vault_quote_per_target']=='2'
    assert {'VIRTUAL_QUOTE_RESERVES_PRESENT','FROZEN_VAULT','VAULT_DELEGATE_PRESENT'}<=set(out['flags'])
    assert out['price_usd']=='UNVERIFIED'


def test_legacy_layout_keeps_optional_fields_unknown_instead_of_default_zero():
    rpc=RPC()
    for record in (rpc.discovery,rpc.values[0]):change_data(record,lambda b:b.__delitem__(slice(211,None)))
    out=collect(rpc)
    assert out['status']=='VAULT_BALANCE_SNAPSHOT'
    assert out['pool_parameters']['virtual_quote_reserves'] is None
    assert 'POOL_OPTIONAL_FIELDS_UNAVAILABLE' in out['flags']


def test_secondary_read_budget_exception_propagates():
    rpc=RPC();rpc.budget=True
    with pytest.raises(RPCJobBudgetExceeded):collect(rpc)


def test_bad_market_identity_does_not_initiate_any_rpc():
    rpc=RPC();source=market();source['mint']=QUOTE
    out=collect_pool_vault_snapshot(MINT,source,rpc)
    assert out['status']=='NOT_REQUESTED' and rpc.requests==[]


def test_actual_analyzer_standard_opt_in_and_overall_incomplete(monkeypatch):
    from mission_agent.mission_control.server import CLUSTER_PRESETS,CLUSTER_RPC_JOB_BUDGETS
    from mission_agent.meme.cluster import report_completeness
    assert CLUSTER_PRESETS['standard']['read_pool_vaults'] is True
    assert not CLUSTER_PRESETS['quick'].get('read_pool_vaults')
    assert CLUSTER_RPC_JOB_BUDGETS['standard']['max_wire_attempts']==1200
    a=WalletClusterAnalyzer(MINT,rpc=RPC(),read_pool_vaults=True)
    out=a.pool_vault_snapshot(market())
    assert out['status']=='VAULT_BALANCE_SNAPSHOT'
    assert report_completeness({'market':market(),'pool_vaults':out})['status']=='INCOMPLETE_EVIDENCE'

@pytest.mark.parametrize('bad',['mint_type','account_type','mint_padding','multisig','option','pool_bool','decoded_limit'])
def test_malformed_binary_layouts_are_explicitly_incomplete(bad):
    rpc=RPC()
    if bad in {'mint_type','account_type','mint_padding','multisig'}:
        rpc.values[1]=account(P22,vault(1000,100,P22));rpc.values[3]=account(P22,mint(6,P22))
    if bad=='mint_type':change_data(rpc.values[3],lambda b:b.__setitem__(165,2))
    elif bad=='account_type':change_data(rpc.values[1],lambda b:b.__setitem__(165,1))
    elif bad=='mint_padding':change_data(rpc.values[3],lambda b:b.__setitem__(83,1))
    elif bad=='multisig':change_data(rpc.values[1],lambda b:b.extend(bytes(355-len(b))))
    elif bad=='option':change_data(rpc.values[1],lambda b:b.__setitem__(72,2))
    elif bad=='pool_bool':change_data(rpc.values[0],lambda b:b.__setitem__(243,2))
    else:change_data(rpc.values[1],lambda b:b.extend(bytes(16385)))
    assert collect(rpc)['status']=='INCOMPLETE_EVIDENCE'


def test_native_mint_zero_supply_does_not_invalidate_real_vault_amount():
    rpc=RPC();change_data(rpc.values[4],lambda b:b.__setitem__(slice(36,44),bytes(8)))
    out=collect(rpc)
    assert out['status']=='VAULT_BALANCE_SNAPSHOT' and out['quote']['mint_supply_raw']=='0'


def test_tiny_balance_ratio_never_rounds_to_zero():
    rpc=RPC();rpc.values[3]=account(P,mint(0));rpc.values[4]=account(P,mint(255))
    assert Decimal(collect(rpc)['raw_vault_quote_per_target'])==Decimal('2E-255')


from decimal import Decimal


def test_raw_transport_response_limit_is_bounded_nonretryable_and_not_cached():
    from mission_agent.meme.cluster import SolanaReadOnlyRPC,RPCError
    reads=[];requests=[]
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def read(self,n):reads.append(n);return b' '*n
    def open_url(*args,**kwargs):requests.append(1);return Response()
    rpc=SolanaReadOnlyRPC('https://fixture.test',open_url=open_url,sleep=lambda *_:None,min_interval=0)
    for _ in range(2):
        with pytest.raises(RPCError,match='RPC_POOL_RESPONSE_LIMIT'):
            rpc.call('getMultipleAccounts',[[POOL],{'encoding':'base64','commitment':'finalized'}])
    assert reads==[MAX_RPC_BYTES+1]*2 and len(requests)==2


def test_wrapper_masks_rpc_errors_but_keeps_budget_exceptions_terminal():
    from mission_agent.meme.cluster import RPCError
    class FailingRPC:
        def call(self,*a,**kw):raise RPCError('SECRET')
    out=WalletClusterAnalyzer(MINT,rpc=FailingRPC(),read_pool_vaults=True).pool_vault_snapshot(market())
    assert out['reason']=='RPC_UNAVAILABLE' and 'SECRET' not in json.dumps(out)
    assert WalletClusterAnalyzer(MINT,rpc=FailingRPC()).pool_vault_snapshot(market())['status']=='NOT_REQUESTED'


def test_markdown_retains_raw_snapshot_with_explicit_nonpricing_scope():
    from mission_agent.meme.cluster import markdown
    text=markdown({'mint':MINT,'pool_vaults':collect(),'metrics':{},'assessment':{},'coverage':{},'holders':[]})
    assert 'Raw selected-pool vault balance evidence' in text and 'VAULT_BALANCE_SNAPSHOT' in text
    assert 'not price or executable quote' in text


def test_analyze_persists_the_opted_in_raw_pool_snapshot():
    from test_meme_wallet_cluster import analyzer
    a=analyzer();a.mint=MINT;a.rpc=RPC();a.read_pool_vaults=True
    a.market_snapshot=lambda:market()
    a._scan_holder=lambda *args,**kwargs:None
    report=a.analyze()
    assert report['pool_vaults']['snapshot_slot']==101
    assert report['pool_vaults']['target']['raw']=='100'
    from mission_agent.meme.cluster import report_completeness
    assert report_completeness(report)['status']=='INCOMPLETE_EVIDENCE'
