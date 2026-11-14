"""Launchpad identity read from finalized account state (no indexer).

Pump.fun bonding curve: PDA seeds ["bonding-curve", mint] under program
6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P; Anchor account BondingCurve
(discriminator sha256("account:BondingCurve")[:8]) with u64 virtual/real
reserves at 8..48, complete flag at 48 and creator pubkey at 49..81.
Token metadata: Token-2022 tokenMetadata extension (jsonParsed) or the
Metaplex metadata PDA ["metadata", program, mint] (Borsh strings).
"""
import base64
import hashlib
from .holder_ranks import valid_pubkey,find_program_address,b58decode32,_b58

PUMP_PROGRAM='6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
METAPLEX_PROGRAM='metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s'
BONDING_CURVE_DISCRIMINATOR=hashlib.sha256(b'account:BondingCurve').digest()[:8]


def _base64_data(value):
    data=value.get('data') if isinstance(value,dict) else None
    if not isinstance(data,list) or len(data)!=2 or data[1]!='base64':raise ValueError('ENCODING')
    return base64.b64decode(data[0],validate=True)


def decode_bonding_curve(value):
    if not isinstance(value,dict) or value.get('owner')!=PUMP_PROGRAM:raise ValueError('OWNER')
    b=_base64_data(value)
    if len(b)<81 or b[:8]!=BONDING_CURVE_DISCRIMINATOR or b[48] not in (0,1):raise ValueError('LAYOUT')
    u=lambda o:str(int.from_bytes(b[o:o+8],'little'))
    return {'virtual_token_reserves_raw':u(8),'virtual_sol_reserves_lamports':u(16),'real_token_reserves_raw':u(24),
            'real_sol_reserves_lamports':u(32),'token_total_supply_raw':u(40),'complete':bool(b[48]),'creator':_b58(b[49:81])}


def pump_bonding_curve_address(mint):
    return find_program_address([b'bonding-curve',b58decode32(mint)],PUMP_PROGRAM)


def collect_pump_launch(mint,rpc):
    """One getAccountInfo; absence means 'not a Pump.fun bonding-curve mint'."""
    if not valid_pubkey(mint):return {'version':1,'status':'UNAVAILABLE','reason':'MINT_INVALID'}
    curve,bump=pump_bonding_curve_address(mint)
    out={'version':1,'launchpad':'PUMP_FUN','program':PUMP_PROGRAM,'bonding_curve':curve,'bump':bump,
         'derivation':'PDA(["bonding-curve",mint],program)','source':'SOLANA_FINALIZED_ACCOUNT_STATE'}
    result=rpc.call('getAccountInfo',[curve,{'encoding':'base64','commitment':'finalized'}],ttl=60)
    value=(result or {}).get('value') if isinstance(result,dict) else None
    out['slot']=((result or {}).get('context') or {}).get('slot') if isinstance(result,dict) else None
    if value is None:return {**out,'status':'NOT_PUMP_LAUNCH','reason':'BONDING_CURVE_ACCOUNT_ABSENT'}
    try:state=decode_bonding_curve(value)
    except (ValueError,TypeError):return {**out,'status':'NOT_PUMP_LAUNCH','reason':'BONDING_CURVE_LAYOUT_MISMATCH'}
    return {**out,'status':'VERIFIED_CHAIN_STATE',**state,
            'role_scope':'BONDING_CURVE_IS_PROTOCOL_VAULT; CREATOR_FIELD_IS_ONCHAIN_CREATOR_NOT_BENEFICIAL_CONTROL_PROOF'}


def _borsh_string(b,offset):
    n=int.from_bytes(b[offset:offset+4],'little')
    if n>1024 or offset+4+n>len(b):raise ValueError('STRING')
    return b[offset+4:offset+4+n].decode('utf-8','replace').rstrip('\x00').strip(),offset+4+n


def decode_metaplex_metadata(value):
    if not isinstance(value,dict) or value.get('owner')!=METAPLEX_PROGRAM:raise ValueError('OWNER')
    b=_base64_data(value)
    if len(b)<70 or b[0]!=4:raise ValueError('LAYOUT')
    update_authority=_b58(b[1:33]);mint=_b58(b[33:65])
    name,o=_borsh_string(b,65);symbol,o=_borsh_string(b,o);uri,o=_borsh_string(b,o)
    is_mutable=None
    try:
        o+=2;has_creators=b[o];o+=1
        if has_creators==1:
            count=int.from_bytes(b[o:o+4],'little');o+=4+34*count
        o+=1
        is_mutable=bool(b[o])
    except IndexError:pass
    return {'name':name,'symbol':symbol,'uri':uri,'update_authority':update_authority,'mint':mint,'is_mutable':is_mutable}


def collect_token_metadata(mint,token_profile,rpc):
    """URI as committed on chain. Token-2022 extension first, then Metaplex PDA."""
    ext=(token_profile or {}).get('token_metadata') if isinstance(token_profile,dict) else None
    if isinstance(ext,dict) and ext.get('uri'):
        return {'version':1,'status':'VERIFIED_CHAIN_STATE','source':'TOKEN_2022_TOKEN_METADATA_EXTENSION',**ext,
                'is_mutable':ext.get('update_authority') not in (None,'')}
    if not valid_pubkey(mint):return {'version':1,'status':'UNAVAILABLE','reason':'MINT_INVALID'}
    pda,_=find_program_address([b'metadata',b58decode32(METAPLEX_PROGRAM),b58decode32(mint)],METAPLEX_PROGRAM)
    result=rpc.call('getAccountInfo',[pda,{'encoding':'base64','commitment':'finalized'}],ttl=300)
    value=(result or {}).get('value') if isinstance(result,dict) else None
    if value is None:return {'version':1,'status':'UNAVAILABLE','reason':'METADATA_ACCOUNT_ABSENT','metadata_account':pda}
    try:meta=decode_metaplex_metadata(value)
    except (ValueError,TypeError):return {'version':1,'status':'UNAVAILABLE','reason':'METADATA_LAYOUT_UNSUPPORTED','metadata_account':pda}
    if meta['mint']!=mint:return {'version':1,'status':'UNAVAILABLE','reason':'METADATA_MINT_MISMATCH','metadata_account':pda}
    return {'version':1,'status':'VERIFIED_CHAIN_STATE','source':'METAPLEX_METADATA_PDA','metadata_account':pda,**meta}
