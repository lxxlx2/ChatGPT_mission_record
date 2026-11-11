"""Pinned mainnet pool identity layouts. Raw vault identity, never swap pricing.

References are upstream Git blob IDs, not proof of deployed upgrade semantics.
Unknown programs/layouts fail closed. PDA authority uses the program's stored
bump; no guessed label, token symbol, indexer dexId, or entire-Owner exclusion.
"""
import hashlib
from .holder_ranks import ALPHABET, valid_pubkey

CPMM='CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C'
AMM_V4='675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8'
CLMM='CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK'
WHIRLPOOL='whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc'
DLMM='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
PUMP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
LAYOUTS={
    CPMM:dict(name='RAYDIUM_CPMM',length=637,account='PoolState',offsets=(168,200,72,104),reference='bc80829f58f8652bcffba9c559327dd37f63f507'),
    AMM_V4:dict(name='RAYDIUM_AMM_V4',length=752,account=None,offsets=(400,432,336,368),reference='a541c7cde9d2de797fe36b4fdb4f0e05428a71a8'),
    CLMM:dict(name='RAYDIUM_CLMM',length=1544,account='PoolState',offsets=(73,105,137,169),reference='309cf1842be657698128a8de270943e90cc48ab7'),
    WHIRLPOOL:dict(name='ORCA_WHIRLPOOL',length=653,account='Whirlpool',offsets=(101,181,133,213),reference='66586dc10495a66561d481ad3e79ca54d8455c46'),
    DLMM:dict(name='METEORA_DLMM',length=904,account='LbPair',offsets=(88,120,152,184),reference='6715f5cf19dffa8651a185ac0dd823218c6a2a75'),
}
SUPPORTED_PROGRAMS={PUMP,*LAYOUTS}


def pubkey_bytes(value):
    if not valid_pubkey(value):raise ValueError('INVALID_PUBLIC_KEY')
    n=0
    for char in value:n=n*58+ALPHABET.index(char)
    return n.to_bytes(32,'big')


def stored_bump_authority(program,seed,bump):
    # Mainnet program ownership + exact layout/stored bump + observed SPL
    # authority are checked together. This is not a PDA address search.
    from .pool_vaults import _key
    if type(bump) is not int or not 0<=bump<=255:raise ValueError('POOL_BUMP_INVALID')
    return _key(hashlib.sha256(seed+bytes([bump])+pubkey_bytes(program)+b'ProgramDerivedAddress').digest())


def decode_pool(account,address):
    from .pool_vaults import _pool,_data,_key,PoolSourceError
    if not valid_pubkey(address):raise PoolSourceError('POOL_ADDRESSES_INVALID')
    program=account.get('owner') if isinstance(account,dict) else None
    if program==PUMP:
        ids,params=_pool(account)
        return {**ids,'authority':address,'program':program,'protocol':'PUMPSWAP',
                'reference_blob':'d907b16a91f035aeb3c3182bfa0972a91bf23a86','parameters':params}
    spec=LAYOUTS.get(program)
    if spec is None:raise PoolSourceError('UNSUPPORTED_POOL_PROGRAM')
    b=_data(account,program)
    if len(b)!=spec['length']:raise PoolSourceError('UNSUPPORTED_POOL_LAYOUT')
    if spec['account'] and b[:8]!=hashlib.sha256(('account:'+spec['account']).encode()).digest()[:8]:raise PoolSourceError('POOL_DISCRIMINATOR_INVALID')
    if program==AMM_V4 and not 1<=int.from_bytes(b[:8],'little')<=7:raise PoolSourceError('POOL_STATE_INVALID')
    authority=address
    try:
        if program==CPMM:authority=stored_bump_authority(program,b'vault_and_lp_mint_auth_seed',b[328])
        if program==AMM_V4:authority=stored_bump_authority(program,b'amm authority',int.from_bytes(b[8:16],'little'))
    except ValueError:raise PoolSourceError('POOL_BUMP_INVALID')
    ids={name:_key(b[o:o+32]) for name,o in zip(('base_mint','quote_mint','base_vault','quote_vault'),spec['offsets'])}
    if len(set(ids.values()))!=4 or address in ids.values():raise PoolSourceError('POOL_ADDRESSES_INVALID')
    declared={}
    if program==CPMM:declared={'token_programs':[_key(b[232:264]),_key(b[264:296])],'mint_decimals':[b[331],b[332]]}
    if program==CLMM:declared={'mint_decimals':[b[233],b[234]]}
    if program==AMM_V4:declared={'mint_decimals':[int.from_bytes(b[32:40],'little'),int.from_bytes(b[40:48],'little')]}
    return {**ids,**declared,'authority':authority,'program':program,'protocol':spec['name'],
            'reference_blob':spec['reference'],'parameters':{}}
