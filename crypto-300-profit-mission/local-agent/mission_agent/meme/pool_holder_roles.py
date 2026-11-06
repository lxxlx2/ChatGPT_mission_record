"""Bind only a verified selected target vault, not all LP/special addresses.

PumpSwap Pool program/discriminator/target-vault identity was decoded by
pool_vaults using pump-public-docs IDL blob d907b16a91f035aeb3c3182bfa0972a91bf23a86.
No I/O, role-registry edits, heuristics by DEX name, or historical backfill.
"""
from decimal import Decimal,localcontext,ROUND_HALF_EVEN
import re
from .holder_ranks import valid_pubkey,PROGRAMS
from .holder_binary import _uint,verified_holder_mass
from .pool_vaults import PROGRAM
from .pool_programs import SUPPORTED_PROGRAMS


def _hash(v):return isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) is not None


def build_pool_holder_roles(mint,ranks,pool):
    out={'version':1,'status':'UNAVAILABLE','metric_status':'UNRESOLVED','independent_provider':False,
         'all_special_roles_normalized':False,'holder_mass_verified':False,'owners_after':[],
         'top10_pct_of_mint_supply':'UNRESOLVED','top10_pct_of_remaining':'UNRESOLVED',
         'scope':'ONLY_SELECTED_TARGET_VAULT_NOT_ALL_LP_OR_SPECIAL_ADDRESSES',
         'deduction_basis':'RAW_TARGET_VAULT_NOT_EFFECTIVE_OR_VIRTUAL_RESERVES',
         'conflicts':[]}
    if not isinstance(pool,dict) or pool.get('status')=='NOT_REQUESTED':return {**out,'status':'NOT_REQUESTED','reason':'POOL_NOT_COLLECTED'}
    t=pool.get('target');q=pool.get('quote');pool_slot=pool.get('snapshot_slot')
    if not isinstance(t,dict) or not isinstance(q,dict) or pool.get('status')!='VAULT_BALANCE_SNAPSHOT' or pool.get('source')!='SOLANA_FINALIZED_RAW_ACCOUNTS' or pool.get('pool_program') not in SUPPORTED_PROGRAMS or pool.get('mint')!=mint or t.get('mint')!=mint or t.get('authority')!=pool.get('vault_authority',pool.get('pool_address')) or not all(valid_pubkey(v) for v in (mint,pool.get('pool_address'),t.get('vault'),q.get('mint'))) or mint==q.get('mint') or not isinstance(t.get('token_program'),str) or t.get('token_program') not in PROGRAMS or _uint(t.get('raw')) is None or _uint(t.get('mint_supply_raw')) is None or type(t.get('decimals')) is not int or not 0<=t['decimals']<=255 or type(pool_slot) is not int or pool_slot<=0 or not _hash(pool.get('response_sha256')):
        return {**out,'reason':'POOL_IDENTITY_UNVERIFIED'}
    out.update(mint=mint,pool_address=pool['pool_address'],vault_address=t['vault'],authority=t['authority'],
               pool_slot=pool_slot,pool_response_sha256=pool['response_sha256'],vault_raw=t['raw'],
               pool_program=pool['pool_program'],role='SELECTED_POOL_TARGET_TOKEN_VAULT',role_basis='PROGRAM_DISCRIMINATOR_STORED_VAULT_AND_TOKEN_AUTHORITY',
               reference_blob=pool.get('layout_reference_blob','d907b16a91f035aeb3c3182bfa0972a91bf23a86'))
    c=ranks.get('raw_balance_check') if isinstance(ranks,dict) else None
    if not isinstance(c,dict) or c.get('status') not in {'RECONCILED_NONZERO_BALANCE_MASS','OBSERVED_SAMPLE_ONLY'} or c.get('mint')!=mint or not isinstance(c.get('program_id'),str) or c.get('program_id') not in PROGRAMS or not _hash(c.get('response_sha256')) or not _hash(c.get('enumeration_response_sha256')) or c['enumeration_response_sha256']!=ranks.get('response_sha256') or c.get('enumeration_slot')!=ranks.get('snapshot_slot') or type(c.get('snapshot_slot')) is not int or c['snapshot_slot']<=0 or _uint(c.get('mint_supply_raw')) is None or type(c.get('decimals')) is not int or not isinstance(c.get('records'),list) or len(c['records'])>99:
        return {**out,'reason':'HOLDER_BINARY_PROVENANCE_UNVERIFIED'}
    out.update(holder_slot=c['snapshot_slot'],holder_response_sha256=c['response_sha256'])
    if pool_slot!=c['snapshot_slot']:return {**out,'status':'OBSERVED_AT_DIFFERENT_SLOTS','reason':'SLOTS_NOT_ALIGNED'}
    conflicts=[]
    if c['program_id']!=t['token_program']:conflicts.append('MINT_PROGRAM_DIFFERS')
    if int(c['mint_supply_raw'])!=int(t['mint_supply_raw']):conflicts.append('MINT_SUPPLY_DIFFERS')
    if c['decimals']!=t['decimals']:conflicts.append('MINT_DECIMALS_DIFFER')
    matching=[r for r in c['records'] if isinstance(r,dict) and r.get('token_account')==t['vault']]
    if len(matching)>1:return {**out,'reason':'HOLDER_BINARY_PROVENANCE_UNVERIFIED'}
    record=matching[0] if matching else None;bound=False
    if record is not None:
        if record.get('status')=='MISSING':conflicts.append('VAULT_ABSENT_AT_HOLDER_BANK')
        elif isinstance(record.get('status'),str) and record.get('status') in {'MATCH','DIFFERS'} and _uint(record.get('raw')) is not None and valid_pubkey(record.get('mint')) and valid_pubkey(record.get('owner')):
            if record.get('mint')!=mint:conflicts.append('VAULT_MINT_DIFFERS')
            if record.get('owner')!=t['authority']:conflicts.append('VAULT_AUTHORITY_DIFFERS')
            if int(record['raw'])!=int(t['raw']):conflicts.append('VAULT_AMOUNT_DIFFERS')
            bound=not conflicts
    mass=verified_holder_mass(c,mint)
    out['holder_mass_verified']=mass
    if record is None and int(t['raw'])>0 and mass:conflicts.append('POSITIVE_VAULT_OUTSIDE_CLAIMED_MASS')
    if conflicts:return {**out,'status':'SAME_SLOT_CONTRADICTION','reason':'POOL_HOLDER_SAME_SLOT_CONTRADICTION','conflicts':conflicts}
    if record is None and t['raw']=='0' and mass:
        bound=True;out['vault_binding']='ZERO_VAULT_NOT_SAMPLED'
    elif bound:out['vault_binding']='EXACT_ACCOUNT_MINT_AUTHORITY_AND_AMOUNT'
    if not bound:return {**out,'reason':'TARGET_VAULT_NOT_CORROBORATED'}
    out['status']='SELECTED_VAULT_BOUND'
    if not mass:return {**out,'reason':'HOLDER_MASS_NOT_VERIFIED'}
    supply=int(c['mint_supply_raw']);vault=int(t['raw']);balances={r['owner']:int(r['raw']) for r in c['owners']}
    before=balances.get(t['authority'],0)
    if before<vault or supply<vault:return {**out,'status':'SAME_SLOT_CONTRADICTION','reason':'POOL_HOLDER_SAME_SLOT_CONTRADICTION','conflicts':['VAULT_EXCEEDS_RECONCILED_OWNER_BALANCE']}
    after=before-vault;balances[t['authority']]=after
    owners=sorted(((o,v) for o,v in balances.items() if v),key=lambda x:(-x[1],x[0]));remaining=supply-vault;top=sum(v for _,v in owners[:10])
    def pct(raw,denominator):
        if not denominator:return 'UNRESOLVED'
        with localcontext() as ctx:
            ctx.prec=80;ctx.rounding=ROUND_HALF_EVEN
            return str((Decimal(raw)*100/Decimal(denominator)).quantize(Decimal('0.0001')))
    out.update(metric_status='SINGLE_VAULT_DEDUCTION_ONLY',reason=None,mint_supply_raw=str(supply),remaining_raw=str(remaining),
               pool_owner_raw_before=str(before),pool_owner_raw_after=str(after),top10_raw_after=str(top),
               top10_pct_of_mint_supply=pct(top,supply),top10_pct_of_remaining=pct(top,remaining),
               owners_after=[{'owner':o,'raw':str(v)} for o,v in owners])
    return out


def attach_pool_holder_roles(mint,ranks,pool):
    out=build_pool_holder_roles(mint,ranks,pool)
    if out['status']!='SAME_SLOT_CONTRADICTION':return out
    c=ranks.get('raw_balance_check') or {};model=pool.get('effective_reserves') or {};market=pool.get('market_comparison') or {}
    out['withdrawn_metrics']={'holder_owner_top10_pct':c.get('owner_top10_pct'),
        'pool_raw_ratio':pool.get('raw_vault_quote_per_target'),'pool_model_ratio':model.get('effective_quote_per_target'),
        'indexer_difference':market.get('difference_indexer_minus_model'),'parsed_ranking_metrics':dict(ranks.get('metrics') or {})}
    c.update(status='INCOMPLETE_EVIDENCE',reason='POOL_HOLDER_SAME_SLOT_CONTRADICTION',full_positive_mass_reconciled=False,owner_top10_pct='UNRESOLVED')
    for row in c.get('owners') or []:row['supply_pct']='UNRESOLVED'
    if ranks.get('snapshot_slot')==out['holder_slot']:
        ranks.update(status='INCOMPLETE_EVIDENCE',reason='POOL_HOLDER_SAME_SLOT_CONTRADICTION')
        ranks['metrics']={k:'UNRESOLVED' for k in ranks.get('metrics') or {}}
        for row in ranks.get('owners') or []:row['supply_pct']='UNRESOLVED'
    pool['raw_vault_quote_per_target']='UNRESOLVED'
    if model:model.update(status='INCOMPLETE_EVIDENCE',reason='POOL_HOLDER_SAME_SLOT_CONTRADICTION',effective_quote_per_target='UNRESOLVED')
    if market:market.update(status='UNAVAILABLE',reason='POOL_HOLDER_SAME_SLOT_CONTRADICTION',difference_indexer_minus_model=None,difference_pct_of_model=None)
    return out
