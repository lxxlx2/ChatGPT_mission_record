"""Same-pool quoted-unit references, not time-aligned or executable parity.

Optional GeckoTerminal fields: base_token_price_quote_token and
quote_token_price_base_token, documented at
https://docs.coingecko.com/reference/pool-address . Public responses may omit
these fields. No paid endpoint, native-currency guess, USD cross-rate or I/O.
"""
import math
import re
from decimal import Decimal,InvalidOperation,localcontext,ROUND_HALF_EVEN
from .holder_ranks import valid_pubkey


def quote_number(value):
    if isinstance(value,bool) or value is None or not isinstance(value,(str,int,float,Decimal)):return None
    text=str(value)
    if len(text)>400 or not text.isascii():return None
    try:
        d=Decimal(text)
        if not d.is_finite() or d<=0 or abs(d.adjusted())>300:return None
        return str(d)
    except (InvalidOperation,ValueError,TypeError):return None


def _timestamp(v):
    try:return v if type(v) in (int,float) and v>0 and math.isfinite(v) else None
    except OverflowError:return None


def _hash(v):return isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) is not None


def compare_pool_quote_ratio(mint,market,raw):
    out={'version':1,'status':'UNAVAILABLE','same_chain_snapshot':False,'provider_asof':'UNVERIFIED',
         'price_basis_alignment':'UNVERIFIED','deployed_binary_semantics':'UNVERIFIED',
         'difference_indexer_minus_model':None,'difference_pct_of_model':None,'retrieval_gap_seconds':None,
         'chain_result_received_at':None,'indexer_result_received_at':None,
         'time_semantics':'RESULT_RECEIVED_NOT_CHAIN_SLOT_TIME_OR_PROVIDER_ASOF',
         'scope':'NON_SYNCHRONOUS_REFERENCE_COMPARISON_NOT_USD_OR_EXECUTABLE_PRICE'}
    if not isinstance(market,dict) or not isinstance(raw,dict):return {**out,'reason':'POOL_IDENTITY_UNVERIFIED'}
    pair=market.get('main_pair');ind=market.get('independent_market')
    if not isinstance(pair,dict) or market.get('status')!='OK' or market.get('source')!='DEXSCREENER_API' or market.get('mint')!=mint or pair.get('base_address')!=mint or not all(valid_pubkey(v) for v in (mint,pair.get('pair_address'),pair.get('quote_address'))) or len({mint,pair['pair_address'],pair['quote_address']})!=3:
        return {**out,'reason':'POOL_IDENTITY_UNVERIFIED'}
    if not isinstance(ind,dict) or ind.get('status')!='OK' or ind.get('source')!='GECKOTERMINAL_PUBLIC_API' or ind.get('attempted') is not True or ind.get('mint')!=mint or ind.get('quote_address')!=pair['quote_address'] or ind.get('pool_address')!=pair['pair_address'] or not _hash(ind.get('response_sha256')):
        return {**out,'reason':'INDEXER_IDENTITY_UNVERIFIED'}
    field={'BASE':'base_token_price_quote_token','QUOTE':'quote_token_price_base_token'}.get(ind.get('target_orientation'))
    if field is None or ind.get('price_quote_units_field')!=field:return {**out,'reason':'INDEXER_UNIT_UNVERIFIED'}
    from .pool_vaults import PROGRAM
    target=raw.get('target');quote=raw.get('quote')
    if raw.get('status')!='VAULT_BALANCE_SNAPSHOT' or raw.get('pool_program')!=PROGRAM or raw.get('mint')!=mint or raw.get('pool_address')!=pair['pair_address'] or not _hash(raw.get('response_sha256')) or type(raw.get('snapshot_slot')) is not int or raw['snapshot_slot']<=0 or not isinstance(target,dict) or not isinstance(quote,dict) or target.get('mint')!=mint or quote.get('mint')!=pair['quote_address']:
        return {**out,'reason':'RAW_POOL_IDENTITY_UNVERIFIED'}
    model=raw.get('effective_reserves')
    if not isinstance(model,dict) or model.get('status')!='DERIVED_PROTOCOL_RESERVES':return {**out,'reason':'MODEL_RATIO_UNVERIFIED'}
    if model.get('version')!=1 or model.get('formula')!='PUMPSWAP_SIGNED_VQR_V1' or model.get('target_mint')!=mint or model.get('quote_mint')!=pair['quote_address'] or {model.get('protocol_base_mint'),model.get('protocol_quote_mint')}!={mint,pair['quote_address']}:
        return {**out,'reason':'MODEL_IDENTITY_UNVERIFIED'}
    base=target if model['protocol_base_mint']==mint else quote
    protocol_quote=target if model['protocol_quote_mint']==mint else quote
    if model.get('base_raw')!=base.get('raw') or model.get('quote_vault_raw')!=protocol_quote.get('raw') or model.get('base_decimals')!=base.get('decimals') or model.get('quote_decimals')!=protocol_quote.get('decimals'):
        return {**out,'reason':'MODEL_IDENTITY_UNVERIFIED'}
    model_ratio=quote_number(model.get('effective_quote_per_target'));indexer_ratio=quote_number(ind.get('price_quote_units'))
    if model_ratio is None or indexer_ratio is None:return {**out,'reason':'DIRECT_QUOTE_RATIO_UNAVAILABLE'}
    chain_time=_timestamp(raw.get('observed_at'));indexer_time=_timestamp(ind.get('observed_at'))
    with localcontext() as ctx:
        ctx.prec=700;ctx.rounding=ROUND_HALF_EVEN
        difference=Decimal(indexer_ratio)-Decimal(model_ratio)
        percent=(difference*100/Decimal(model_ratio)).quantize(Decimal('0.0001'))
    out.update(status='UNALIGNED_RATIO_COMPARISON',mint=mint,quote_address=pair['quote_address'],pool_address=pair['pair_address'],
               model_quote_per_target=model_ratio,indexer_quote_per_target=indexer_ratio,indexer_field=field,
               difference_indexer_minus_model=str(difference),difference_pct_of_model=str(percent),
               snapshot_slot=raw['snapshot_slot'],chain_response_sha256=raw['response_sha256'],indexer_response_sha256=ind['response_sha256'],
               chain_result_received_at=chain_time,indexer_result_received_at=indexer_time)
    if chain_time is not None and indexer_time is not None:out['retrieval_gap_seconds']=abs(chain_time-indexer_time)
    return out
