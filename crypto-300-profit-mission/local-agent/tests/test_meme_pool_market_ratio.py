"""Same-pool quote-unit comparison; injected sources only, no live prices."""
import copy
from decimal import Decimal
import pytest
from test_meme_pool_vaults import RPC,collect,market,MINT,QUOTE,POOL
from test_meme_market_parity import client,payload


def inputs(reverse=False):
    rpc=RPC();raw=collect(rpc,reverse);raw['observed_at']=103
    m=market(reverse)
    m['independent_market']={'status':'OK','attempted':True,'source':'GECKOTERMINAL_PUBLIC_API',
        'mint':QUOTE if reverse else MINT,'quote_address':MINT if reverse else QUOTE,'pool_address':POOL,
        'price_quote_units':'0.6' if reverse else '2.5','price_quote_units_field':'base_token_price_quote_token',
        'target_orientation':'BASE','provider_asof':'UNVERIFIED','observed_at':101,'response_sha256':'b'*64}
    return rpc,m,raw


def compare(m,raw):
    from mission_agent.meme.pool_market import compare_pool_quote_ratio
    return compare_pool_quote_ratio(m['mint'],m,raw)


@pytest.mark.parametrize('reverse',[False,True])
def test_exact_selected_pool_comparison_uses_requested_quote_units_but_never_proves_parity(reverse):
    rpc,m,raw=inputs(reverse);saved=copy.deepcopy((m,raw));out=compare(m,raw)
    assert out['status']=='UNALIGNED_RATIO_COMPARISON'
    assert out['mint']==m['mint'] and out['quote_address']==m['main_pair']['quote_address']
    assert out['model_quote_per_target']==('0.5' if reverse else '2')
    assert out['indexer_quote_per_target']==('0.6' if reverse else '2.5')
    assert out['difference_indexer_minus_model']==('0.1' if reverse else '0.5')
    assert out['difference_pct_of_model']==('20.0000' if reverse else '25.0000')
    assert out['snapshot_slot']==101 and out['retrieval_gap_seconds']==2
    assert out['same_chain_snapshot'] is False and out['provider_asof']=='UNVERIFIED'
    assert out['price_basis_alignment']=='UNVERIFIED' and 'PASS' not in str(out)
    assert len(rpc.requests)==2 and (m,raw)==saved


@pytest.mark.parametrize('bad',['mint','quote','pool','source','hash','field','orientation','raw_pool','raw_mint','raw_hash','model_target','model_quote','model_protocol','slot'])
def test_identity_unit_or_provenance_failure_never_emits_differences(bad):
    _,m,r=inputs();i=m['independent_market']
    if bad in {'mint','quote','pool','source','hash'}:i[{'mint':'mint','quote':'quote_address','pool':'pool_address','source':'source','hash':'response_sha256'}[bad]]='WRONG'
    elif bad=='field':i['price_quote_units_field']='base_token_price_native_currency'
    elif bad=='orientation':i['target_orientation']='QUOTE'
    elif bad=='raw_pool':r['pool_address']=QUOTE
    elif bad=='raw_mint':r['mint']=QUOTE
    elif bad=='raw_hash':r['response_sha256']='WRONG'
    elif bad=='slot':r['snapshot_slot']=True
    else:r['effective_reserves'][{'model_target':'target_mint','model_quote':'quote_mint','model_protocol':'protocol_quote_mint'}[bad]]=POOL
    out=compare(m,r)
    assert out['status']!='UNALIGNED_RATIO_COMPARISON'
    assert out['difference_indexer_minus_model'] is None


@pytest.mark.parametrize('value',[None,'NaN','Infinity','-1','0',True,'1e999999','0.0'])
def test_missing_or_invalid_direct_unit_price_never_falls_back_to_usd_or_native_currency(value):
    _,m,r=inputs();i=m['independent_market'];i['price_quote_units']=value;i['price_usd']='123';m['main_pair']['price_native']='456'
    out=compare(m,r)
    assert out['status']=='UNAVAILABLE' and out['difference_indexer_minus_model'] is None


@pytest.mark.parametrize('status',['ARITHMETIC_ONLY','INCOMPLETE_EVIDENCE'])
def test_unverified_token_economics_or_invalid_model_cannot_become_price_parity(status):
    _,m,r=inputs();r['effective_reserves']['status']=status
    assert compare(m,r)['reason']=='MODEL_RATIO_UNVERIFIED'


def test_identical_values_are_still_unaligned_and_missing_timestamps_stay_missing():
    _,m,r=inputs();m['independent_market']['price_quote_units']='2';r.pop('observed_at')
    out=compare(m,r)
    assert out['status']=='UNALIGNED_RATIO_COMPARISON' and Decimal(out['difference_indexer_minus_model'])==0
    assert out['retrieval_gap_seconds'] is None and out['chain_result_received_at'] is None
    assert out['same_chain_snapshot'] is False


def test_explicit_gt_reverse_field_is_used_without_reciprocal_or_native_price_guess():
    for reverse,field in [(False,'base_token_price_quote_token'),(True,'quote_token_price_base_token')]:
        data=payload(reverse);data['data']['attributes'][field]='0.12345678901234567890123456789'
        data['data']['attributes']['base_token_price_native_currency']='999'
        from test_meme_market_parity import MINT as GT_MINT,POOL as GT_POOL,QUOTE as GT_QUOTE
        c,calls,_=client(data);out=c.pool_snapshot(GT_MINT,GT_POOL,GT_QUOTE)
        assert out['price_quote_units']=='0.12345678901234567890123456789' and out['price_quote_units_field']==field
        assert len(calls)==1


def test_absent_optional_public_field_is_retained_as_missing_without_extra_request():
    from test_meme_market_parity import MINT as GT_MINT,POOL as GT_POOL,QUOTE as GT_QUOTE
    c,calls,_=client();out=c.pool_snapshot(GT_MINT,GT_POOL,GT_QUOTE)
    assert out['status']=='OK' and out['price_quote_units'] is None and len(calls)==1


def test_actual_analyzer_wires_pure_comparison_without_extra_collection():
    from mission_agent.meme.cluster import WalletClusterAnalyzer
    rpc,m,_=inputs();a=WalletClusterAnalyzer(MINT,rpc=rpc,read_pool_vaults=True)
    out=a.pool_vault_snapshot(m)
    assert out['market_comparison']['status']=='UNALIGNED_RATIO_COMPARISON'
    assert len(rpc.requests)==4  # two earlier injected reads, two new reads
    assert out['observed_at']>0


def test_public_optional_price_number_preserves_wire_decimal_digits():
    import json
    from test_meme_market_parity import MINT as GT_MINT,POOL as GT_POOL,QUOTE as GT_QUOTE,Reply
    from mission_agent.meme.market_parity import GeckoTerminalMarketClient
    data=payload();data['data']['attributes']['base_token_price_quote_token']='LEXICAL_NUMBER'
    reply=Reply(data);reply.body=json.dumps(data).replace('"LEXICAL_NUMBER"','0.12345678901234567890123456789').encode()
    c=GeckoTerminalMarketClient(open_url=lambda *args,**kwargs:reply)
    assert c.pool_snapshot(GT_MINT,GT_POOL,GT_QUOTE)['price_quote_units']=='0.12345678901234567890123456789'


def test_tiny_real_mint_ratio_and_indexer_unit_price_do_not_round_to_zero():
    from test_meme_pool_vaults import account,mint,P
    rpc,m,_=inputs();rpc.values[4]=account(P,mint(255));r=collect(rpc)
    m['independent_market']['price_quote_units']='3e-255'
    out=compare(m,r)
    assert out['status']=='UNALIGNED_RATIO_COMPARISON'
    assert Decimal(out['difference_indexer_minus_model'])==Decimal('1E-255')
    assert out['difference_pct_of_model']=='50.0000'


def test_completeness_and_markdown_keep_non_synchronous_unit_comparison_partial():
    from mission_agent.meme.cluster import report_completeness,markdown
    _,m,r=inputs();r['market_comparison']=compare(m,r)
    report={'mint':MINT,'market':m,'pool_vaults':r,'holders':[],'metrics':{},'assessment':{},'coverage':{}}
    result=report_completeness(report);row=next(x for x in result['requirements'] if x['id']=='independent_sources')
    assert result['status']=='INCOMPLETE_EVIDENCE' and row['status']=='PARTIAL'
    assert row['cause']=='NON_SYNCHRONOUS_POOL_RATIO_REFERENCES_NOT_FULL_PARITY'
    assert 'UNALIGNED_RATIO_COMPARISON' in markdown(report)
