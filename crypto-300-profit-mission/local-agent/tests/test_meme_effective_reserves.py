"""Documented PumpSwap reserve arithmetic; synthetic finalized RPC only."""
from decimal import Decimal,localcontext
import pytest
from test_meme_pool_vaults import RPC,collect,change_data,account,mint,vault,P,P22,MINT,QUOTE


def set_pool(rpc,virtual=0,protocol=0,creator=0):
    def mutate(b):
        b[245:261]=virtual.to_bytes(16,'little',signed=True)
        b[271:279]=protocol.to_bytes(8,'little');b[279:287]=creator.to_bytes(8,'little')
    change_data(rpc.values[0],mutate)


@pytest.mark.parametrize('reverse',[False,True])
def test_negative_virtual_reserves_remove_waiting_fees_once_in_both_directions(reverse):
    rpc=RPC();set_pool(rpc,-15,10,5)
    out=collect(rpc,reverse);r=out['effective_reserves']
    assert r['status']=='DERIVED_PROTOCOL_RESERVES'
    assert r['protocol_base_mint']==MINT and r['protocol_quote_mint']==QUOTE
    assert r['quote_vault_raw']=='200' and r['real_quote_raw']=='185'
    assert r['waiting_fees_raw']=='15' and r['effective_quote_raw']=='185'
    assert r['boost_component_raw']=='0' and r['boost_present'] is False
    with localcontext() as ctx:
        ctx.prec=80;expected=Decimal(100)/Decimal(185) if reverse else Decimal('1.85')
    assert Decimal(r['effective_quote_per_target'])==expected
    assert r['target_mint']==(QUOTE if reverse else MINT)
    assert r['quote_mint']==(MINT if reverse else QUOTE)
    assert out['price_usd']=='UNVERIFIED' and out['executable_quote']=='NOT_COMPUTED'
    assert len(rpc.requests)==2


def test_sweep_preserves_effective_and_real_reserves_without_double_subtracting_fees():
    before=RPC();set_pool(before,-15,10,5)
    after=RPC();after.values[2]=account(P,vault(2000,185));set_pool(after,0,0,0)
    a=collect(before);b=collect(after)
    assert a['raw_vault_quote_per_target']=='2' and b['raw_vault_quote_per_target']=='1.85'
    assert a['effective_reserves']['effective_quote_raw']==b['effective_reserves']['effective_quote_raw']=='185'
    assert a['effective_reserves']['real_quote_raw']==b['effective_reserves']['real_quote_raw']=='185'
    assert a['effective_reserves']['effective_quote_per_target']==b['effective_reserves']['effective_quote_per_target']=='1.85'


def test_boost_is_virtual_plus_waiting_fees_not_virtual_nonzero_alone():
    rpc=RPC();set_pool(rpc,35,10,5);r=collect(rpc)['effective_reserves']
    assert r['real_quote_raw']=='185' and r['boost_component_raw']=='50'
    assert r['effective_quote_raw']=='235' and r['boost_present'] is True
    assert r['effective_quote_per_target']=='2.35'


@pytest.mark.parametrize('virtual,protocol,creator,reason',[
    (-201,0,0,'EFFECTIVE_QUOTE_OUT_OF_RANGE'),
    (2**127-1,0,0,'EFFECTIVE_QUOTE_OUT_OF_RANGE'),
    (0,200,1,'WAITING_FEES_EXCEED_QUOTE_VAULT'),
    (-20,10,5,'NEGATIVE_BOOST_COMPONENT_UNVERIFIED'),
])
def test_inconsistent_model_never_discards_verified_raw_balances_or_emits_ratio(virtual,protocol,creator,reason):
    rpc=RPC();set_pool(rpc,virtual,protocol,creator);out=collect(rpc);r=out['effective_reserves']
    assert out['status']=='VAULT_BALANCE_SNAPSHOT' and out['quote']['raw']=='200'
    assert r['status']=='INCOMPLETE_EVIDENCE' and r['reason']==reason
    assert r['effective_quote_per_target']=='UNRESOLVED'


@pytest.mark.parametrize('length',[211,243,244,245,261,269,270,271,279])
def test_legacy_zero_defaults_are_documented_and_do_not_overwrite_observed_missing_fields(length):
    rpc=RPC()
    for record in (rpc.discovery,rpc.values[0]):change_data(record,lambda b:b.__delitem__(slice(length,None)))
    out=collect(rpc);r=out['effective_reserves']
    assert r['status']=='DERIVED_PROTOCOL_RESERVES' and r['effective_quote_raw']=='200'
    assert r['effective_quote_per_target']=='2'
    if length<261:
        assert out['pool_parameters']['virtual_quote_reserves'] is None
        assert 'virtual_quote_reserves' in r['documented_zero_defaults']
    if length<287:assert 'creator_fees' in r['documented_zero_defaults']


@pytest.mark.parametrize('reverse,base_raw,virtual',[(False,0,0),(False,100,-200),(True,100,-200)])
def test_zero_side_retains_exact_derived_reserves_but_no_pool_ratio(reverse,base_raw,virtual):
    rpc=RPC();rpc.values[1]=account(P,vault(1000,base_raw));set_pool(rpc,virtual,200 if virtual else 0,0)
    r=collect(rpc,reverse)['effective_reserves']
    assert r['effective_quote_raw']==('0' if virtual else '200')
    assert r['effective_quote_per_target']=='UNRESOLVED' and r['ratio_reason']=='ZERO_POOL_SIDE'


@pytest.mark.parametrize('risk',['token2022','frozen'])
def test_unsupported_economic_adjustments_keep_arithmetic_but_withhold_ratio(risk):
    rpc=RPC()
    if risk=='token2022':
        rpc.values[1]=account(P22,vault(1000,100,P22));rpc.values[3]=account(P22,mint(6,P22))
    else:change_data(rpc.values[1],lambda b:b.__setitem__(108,2))
    r=collect(rpc)['effective_reserves']
    assert r['effective_quote_raw']=='200' and r['status']=='ARITHMETIC_ONLY'
    assert r['effective_quote_per_target']=='UNRESOLVED' and r['ratio_reason']=='TOKEN_ECONOMICS_UNVERIFIED'


def test_scaled_reserves_use_exact_mint_decimals_and_preserve_tiny_nonzero_ratio():
    rpc=RPC();set_pool(rpc,-30,20,10);rpc.values[3]=account(P,mint(6));rpc.values[4]=account(P,mint(9))
    r=collect(rpc)['effective_reserves']
    assert Decimal(r['effective_quote_quantity'])==Decimal('0.000000170')
    assert r['effective_quote_per_target']=='0.0017'
    rpc.values[4]=account(P,mint(255))
    assert Decimal(collect(rpc)['effective_reserves']['effective_quote_per_target'])==Decimal('1.7e-249')


def test_model_records_pinned_document_basis_and_remains_not_binary_or_usd_parity():
    from mission_agent.meme.cluster import report_completeness,markdown
    out=collect();r=out['effective_reserves']
    assert r['formula']=='PUMPSWAP_SIGNED_VQR_V1' and len(r['reference_blobs'])==3
    assert r['deployed_binary_semantics']=='UNVERIFIED'
    report={'mint':MINT,'market':{'status':'OK'},'pool_vaults':out,'holders':[],'assessment':{},'metrics':{},'coverage':{}}
    completeness=report_completeness(report)
    assert completeness['status']=='INCOMPLETE_EVIDENCE'
    market=next(x for x in completeness['requirements'] if x['id']=='market')
    assert market['cause']=='DOCUMENTED_RESERVES_WITHOUT_USD_OR_SNAPSHOT_PARITY'
    assert market['status']=='PARTIAL'
    text=markdown(report)
    assert 'effective_reserves' in text and 'not price or executable quote' in text
