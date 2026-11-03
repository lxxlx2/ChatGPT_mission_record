"""Bounded PumpSwap raw snapshot and documented reserve arithmetic, no quote.

Layout: pump-fun/pump-public-docs idl/pump_amm.json blob
 d907b16a91f035aeb3c3182bfa0972a91bf23a86. SPL Token interface state.rs
 1bf00f7a1b28eb0b776d3bc90605c7e44bfdbcfd; Token-2022 extension/mod.rs
 12f066a14f0db3ee65543a48919a82a870db44a6. No SDK, signer or new source.
"""
import base64
import hashlib
import json
import time
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from .holder_ranks import ALPHABET, PROGRAMS, TOKEN_2022_PROGRAM, valid_pubkey

PROGRAM='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
POOL_DISCRIMINATOR=bytes([241,154,109,4,17,177,109,188])
MAX_RPC_BYTES=256*1024
MAX_ACCOUNT_BYTES=16*1024
POOL_LENGTHS={211,243,244,245,261,269,270,271,279,287}


class PoolSourceError(ValueError):pass


def _key(raw):
    n=int.from_bytes(raw,'big');out=''
    while n:n,r=divmod(n,58);out=ALPHABET[r]+out
    return '1'*(len(raw)-len(raw.lstrip(b'\0')))+out


def _data(account,program=None):
    if not isinstance(account,dict) or account.get('executable') is not False or (program and account.get('owner')!=program):raise PoolSourceError('ACCOUNT_IDENTITY_INVALID')
    data=account.get('data')
    if not isinstance(data,list) or len(data)!=2 or data[1]!='base64' or not isinstance(data[0],str) or len(data[0])>4*((MAX_ACCOUNT_BYTES+2)//3):raise PoolSourceError('ACCOUNT_ENCODING_INVALID')
    raw=base64.b64decode(data[0],validate=True)
    if len(raw)>MAX_ACCOUNT_BYTES:raise PoolSourceError('ACCOUNT_SIZE_LIMIT')
    return raw


def _pool(account):
    if not isinstance(account,dict) or account.get('owner')!=PROGRAM:raise PoolSourceError('UNSUPPORTED_POOL_PROGRAM')
    b=_data(account,PROGRAM)
    if len(b) not in POOL_LENGTHS and not (len(b)>287 and not any(b[287:])):raise PoolSourceError('UNSUPPORTED_POOL_LAYOUT')
    if b[:8]!=POOL_DISCRIMINATOR:raise PoolSourceError('POOL_DISCRIMINATOR_INVALID')
    if any(b[o] not in (0,1) for o in (243,244,269,270) if len(b)>o):raise PoolSourceError('POOL_BOOLEAN_INVALID')
    ids={name:_key(b[o:o+32]) for name,o in [('base_mint',43),('quote_mint',75),('base_vault',139),('quote_vault',171)]}
    if len(set(ids.values()))!=4:raise PoolSourceError('POOL_ADDRESSES_INVALID')
    params={}
    for name,o,size,signed in [('virtual_quote_reserves',245,16,True),('creator_fee_bps',261,8,False),('protocol_fees',271,8,False),('creator_fees',279,8,False)]:
        params[name]=str(int.from_bytes(b[o:o+size],'little',signed=signed)) if len(b)>=o+size else None
    for name,o in [('is_mayhem_mode',243),('is_cashback_coin',244),('can_edit_creator_fee',269),('is_holder_reward',270)]:params[name]=bool(b[o]) if len(b)>o else None
    return ids,params


def _option(b,offset):
    value=int.from_bytes(b[offset:offset+4],'little')
    if value not in (0,1):raise PoolSourceError('TOKEN_OPTION_INVALID')
    return value


def _token(account,mint_account,mint_id,pool_address,vault_address,flags):
    program=account.get('owner') if isinstance(account,dict) else None
    if program not in PROGRAMS:raise PoolSourceError('TOKEN_PROGRAM_INVALID')
    b=_data(account,program);m=_data(mint_account,program)
    def layout(raw,base,type_id):
        if program==TOKEN_2022_PROGRAM:
            if len(raw)==base:return
            if len(raw)<=165 or len(raw)==355 or raw[165]!=type_id or (base==82 and any(raw[82:165])):raise PoolSourceError('TOKEN_2022_LAYOUT_INVALID')
            flags.add('TOKEN_2022_ADJUSTMENTS_UNVERIFIED')
        elif len(raw)!=base:raise PoolSourceError('TOKEN_LAYOUT_INVALID')
    layout(b,165,2);layout(m,82,1)
    if len(b)<165 or len(m)<82 or m[45]!=1 or b[108] not in (1,2):raise PoolSourceError('TOKEN_STATE_INVALID')
    if _key(b[:32])!=mint_id or _key(b[32:64])!=pool_address:raise PoolSourceError('VAULT_MEMBERSHIP_INVALID')
    for offset in (0,46):_option(m,offset)
    if _option(b,72):flags.add('VAULT_DELEGATE_PRESENT')
    if _option(b,129):flags.add('VAULT_CLOSE_AUTHORITY_PRESENT')
    if _option(b,109):flags.add('WRAPPED_NATIVE_VAULT')
    if b[108]==2:flags.add('FROZEN_VAULT')
    if program==TOKEN_2022_PROGRAM:flags.add('TOKEN_2022_ADJUSTMENTS_UNVERIFIED')
    raw=int.from_bytes(b[64:72],'little');decimals=m[44]
    with localcontext() as ctx:
        ctx.prec=320
        quantity=str(Decimal(raw).scaleb(-decimals))
    return {'mint':mint_id,'vault':vault_address,'authority':pool_address,'token_program':program,'raw':str(raw),'decimals':decimals,'quantity':quantity,'state':'frozen' if b[108]==2 else 'initialized','mint_supply_raw':str(int.from_bytes(m[36:44],'little'))}


# Official protocol documentation is a model basis, not deployed-binary proof.
RESERVE_REFERENCE_BLOBS={
    'PUMP_SWAP_README.md':'c2837ee4dd0f8a4839ec41f920369c05d90ca0fc',
    'NEGATIVE_VIRTUAL_QUOTE_RESERVES.md':'96fa56d171b92e750ad4f965ea71b7cc2fa4b01b',
    'VIRTUAL_QUOTE_RESERVES_FEE_ADJUSTMENT.md':'14d7c316bad91feb976d06e3f88955ae637ea609',
}


def _derive_reserves(base,quote,params,target_mint,flags):
    """Quote-side fees are ALREADY offset by signed virtual reserves.

    Effective = quote vault + virtual. Real = quote vault - waiting fees.
    Boost = virtual + waiting fees. Never subtract waiting fees twice.
    Missing trailing fields use documented zero defaults only in this model;
    observed pool_parameters retain None. No extra collection on report GET.
    """
    out={'version':1,'status':'INCOMPLETE_EVIDENCE','formula':'PUMPSWAP_SIGNED_VQR_V1',
         'reference_blobs':dict(RESERVE_REFERENCE_BLOBS),'deployed_binary_semantics':'UNVERIFIED',
         'effective_quote_per_target':'UNRESOLVED','ratio_precision_digits':80,'ratio_rounding':'ROUND_HALF_EVEN',
         'scope':'DOCUMENTED_RESERVE_ARITHMETIC_NOT_USD_OR_EXECUTABLE_QUOTE',
         'protocol_base_mint':base['mint'],'protocol_quote_mint':quote['mint'],
         'target_mint':target_mint,'quote_mint':quote['mint'] if target_mint==base['mint'] else base['mint']}
    fields=('virtual_quote_reserves','protocol_fees','creator_fees')
    out['documented_zero_defaults']=[k for k in fields if params[k] is None]
    virtual,protocol,creator=(int(params[k]) if params[k] is not None else 0 for k in fields)
    base_raw=int(base['raw']);vault_raw=int(quote['raw']);fees=protocol+creator
    effective=vault_raw+virtual;real=vault_raw-fees;boost=virtual+fees
    if not 0<=effective<=2**64-1:return {**out,'reason':'EFFECTIVE_QUOTE_OUT_OF_RANGE'}
    if real<0:return {**out,'reason':'WAITING_FEES_EXCEED_QUOTE_VAULT'}
    # Documentation calls boost an additional reserve amount; negative boost
    # has no verified model here. Keep raw facts, withhold model conclusions.
    if boost<0:return {**out,'reason':'NEGATIVE_BOOST_COMPONENT_UNVERIFIED'}
    with localcontext() as ctx:
        ctx.prec=320
        bq=Decimal(base_raw).scaleb(-base['decimals'])
        eq=Decimal(effective).scaleb(-quote['decimals'])
        out.update(base_quantity=str(bq),quote_vault_quantity=str(Decimal(vault_raw).scaleb(-quote['decimals'])),
                   waiting_fees_quantity=str(Decimal(fees).scaleb(-quote['decimals'])),
                   real_quote_quantity=str(Decimal(real).scaleb(-quote['decimals'])),
                   effective_quote_quantity=str(eq),boost_component_quantity=str(Decimal(boost).scaleb(-quote['decimals'])))
    out.update(status='DERIVED_PROTOCOL_RESERVES',base_raw=str(base_raw),quote_vault_raw=str(vault_raw),
               virtual_quote_raw=str(virtual),protocol_fees_raw=str(protocol),creator_fees_raw=str(creator),
               waiting_fees_raw=str(fees),real_quote_raw=str(real),effective_quote_raw=str(effective),
               boost_component_raw=str(boost),boost_present=boost!=0,base_decimals=base['decimals'],quote_decimals=quote['decimals'])
    if flags & {'TOKEN_2022_ADJUSTMENTS_UNVERIFIED','FROZEN_VAULT'}:
        out.update(status='ARITHMETIC_ONLY',ratio_reason='TOKEN_ECONOMICS_UNVERIFIED')
    elif not base_raw or not effective:out['ratio_reason']='ZERO_POOL_SIDE'
    else:
        with localcontext() as ctx:
            ctx.prec=80;ctx.rounding=ROUND_HALF_EVEN
            out['effective_quote_per_target']=str(eq/bq if target_mint==base['mint'] else bq/eq)
    return out


def _slot(result):
    ctx=result.get('context') if isinstance(result,dict) else None
    value=ctx.get('slot') if isinstance(ctx,dict) else None
    if type(value) is not int or value<=0:raise PoolSourceError('SNAPSHOT_SLOT_INVALID')
    return value


def collect_pool_vault_snapshot(mint,market,rpc):
    out={'version':1,'status':'NOT_REQUESTED','source':'SOLANA_FINALIZED_RAW_ACCOUNTS','price_usd':'UNVERIFIED','liquidity_usd':'UNVERIFIED','executable_quote':'NOT_COMPUTED','indexer_snapshot_parity':'UNVERIFIED','flags':[]}
    pair=market.get('main_pair') if isinstance(market,dict) else None
    if not isinstance(pair,dict) or market.get('status')!='OK' or market.get('source')!='DEXSCREENER_API' or market.get('mint')!=mint or pair.get('base_address')!=mint or not all(valid_pubkey(v) for v in (mint,pair.get('quote_address'),pair.get('pair_address'))) or len({mint,pair['quote_address'],pair['pair_address']})!=3:
        return {**out,'reason':'PRIMARY_POOL_IDENTITY_UNVERIFIED'}
    pool_address=pair['pair_address'];out.update(status='INCOMPLETE_EVIDENCE',mint=mint,pool_address=pool_address)
    try:
        first=rpc.call('getAccountInfo',[pool_address,{'encoding':'base64','commitment':'finalized'}],ttl=30)
        discovery_slot=_slot(first);out['discovery_slot']=discovery_slot
        ids,_=_pool(first.get('value'))
        if {ids['base_mint'],ids['quote_mint']}!={mint,pair['quote_address']}:raise PoolSourceError('POOL_PAIR_MISMATCH')
        addresses=[pool_address,ids['base_vault'],ids['quote_vault'],ids['base_mint'],ids['quote_mint']]
        if len(set(addresses))!=5:raise PoolSourceError('POOL_ADDRESSES_INVALID')
        response=rpc.call('getMultipleAccounts',[addresses,{'encoding':'base64','commitment':'finalized','minContextSlot':discovery_slot}],ttl=30)
        received_at=time.time()
        slot=_slot(response)
        if slot<discovery_slot:raise PoolSourceError('SNAPSHOT_BEFORE_DISCOVERY')
        values=response.get('value')
        if not isinstance(values,list) or len(values)!=5:raise PoolSourceError('BATCH_INCOMPLETE')
        batch_ids,params=_pool(values[0])
        if batch_ids!=ids:raise PoolSourceError('POOL_CHANGED_SINCE_DISCOVERY')
        flags=set()
        base=_token(values[1],values[3],ids['base_mint'],pool_address,ids['base_vault'],flags)
        quote=_token(values[2],values[4],ids['quote_mint'],pool_address,ids['quote_vault'],flags)
        target,other=(base,quote) if base['mint']==mint else (quote,base)
        if any(v is None for v in params.values()):flags.add('POOL_OPTIONAL_FIELDS_UNAVAILABLE')
        if params['virtual_quote_reserves'] not in (None,'0'):flags.add('VIRTUAL_QUOTE_RESERVES_PRESENT')
        if any(params[k] not in (None,'0') for k in ('protocol_fees','creator_fees')):flags.add('ACCUMULATED_FEES_PRESENT')
        with localcontext() as ctx:
            ctx.prec=80
            ratio=str(Decimal(other['quantity'])/Decimal(target['quantity'])) if int(target['raw']) else 'UNRESOLVED'
        out.update(status='VAULT_BALANCE_SNAPSHOT',observed_at=received_at,snapshot_slot=slot,commitment='finalized',pool_program=PROGRAM,target=target,quote=other,pool_parameters=params,flags=sorted(flags),raw_vault_quote_per_target=ratio,
                   effective_reserves=_derive_reserves(base,quote,params,mint,flags),
                   response_sha256=hashlib.sha256(json.dumps(response,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                   scope='RAW_VAULT_BALANCES_AND_DOCUMENTED_RESERVE_MODEL_NOT_MARKET_PRICE')
    except (ValueError,TypeError,KeyError,OverflowError) as exc:
        out['reason']=str(exc) if isinstance(exc,PoolSourceError) else 'ACCOUNT_RESPONSE_INVALID'
        if out['reason']=='UNSUPPORTED_POOL_PROGRAM':out['status']='UNSUPPORTED'
    return out
