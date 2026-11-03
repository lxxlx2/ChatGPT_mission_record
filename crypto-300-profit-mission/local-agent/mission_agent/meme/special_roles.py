"""Bounded multi-pool account roles and reproducible known-exclusion ranks.

No finite chain query proves every CEX/MM identity. Unlabelled accounts stay
UNKNOWN, never implicitly ORDINARY. Complete filtered ranks require exhaustive
role evidence; exact known-exclusion arithmetic is separately scoped.
"""
import hashlib
import json
from decimal import Decimal,localcontext,ROUND_HALF_EVEN
from .holder_ranks import valid_pubkey,DEFAULT_SPECIAL
from .holder_binary import collect_holder_binary_check,verified_holder_mass
from .pool_programs import decode_pool
from .pool_vaults import PoolSourceError,_slot

MAX_POOLS=8
LP_ROLES={'LP','AMM_POOL','PROTOCOL_VAULT'}


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def percent(raw,supply):
    if not supply:return 'UNRESOLVED'
    with localcontext() as ctx:
        ctx.prec=80;ctx.rounding=ROUND_HALF_EVEN
        return str((Decimal(raw)*100/Decimal(supply)).quantize(Decimal('0.0001')))


def registry_role(mint,account,owner,slot,registry):
    """Only dated token-specific evidence, no legacy blanket normalization flag.

    A registry attribution is an evidenced claim, not proof of on-chain
    controller identity. It can be excluded under an explicitly named policy;
    it can never independently certify all roles or a chain-verified CEX.
    """
    rows=registry.get('role_evidence',[]) if isinstance(registry,dict) else []
    matches=[]
    for r in rows[:5000] if isinstance(rows,list) else []:
        if not isinstance(r,dict) or r.get('mint')!=mint or r.get('role') not in DEFAULT_SPECIAL|{'ORDINARY','EOA','DEV','CREATOR','TREASURY'}:continue
        if r.get('scope') not in {'TOKEN_ACCOUNT','OWNER'} or r.get('address')!=(account if r.get('scope')=='TOKEN_ACCOUNT' else owner):continue
        if type(r.get('valid_from_slot')) is not int or type(r.get('valid_until_slot')) is not int or not r['valid_from_slot']<=slot<=r['valid_until_slot']:continue
        if not isinstance(r.get('evidence_url'),str) or not r['evidence_url'].startswith('https://') or not isinstance(r.get('evidence_sha256'),str) or len(r['evidence_sha256'])!=64 or any(c not in '0123456789abcdef' for c in r['evidence_sha256']):continue
        if r.get('classification')!='VERIFIED_ATTRIBUTION' or not r.get('label_version'):continue
        matches.append(r)
    if not matches:return None
    if len({r['role'] for r in matches})!=1:return {'role':'UNKNOWN','reason':'CONFLICTING_REGISTRY_ATTRIBUTION'}
    r=matches[0]
    return {'role':r['role'],'basis':'DATED_REGISTRY_ATTRIBUTION','classification':'ATTRIBUTION_CLAIM',
            'evidence_url':r['evidence_url'],'evidence_sha256':r['evidence_sha256'],'label_version':r['label_version'],
            'valid_from_slot':r['valid_from_slot'],'valid_until_slot':r['valid_until_slot'],'scope':r['scope']}


def derive_special_ranks(mint,check,pools,registry=None):
    out={'version':1,'mint':mint,'status':'INCOMPLETE_EVIDENCE','all_special_roles_normalized':False,
         'independent_provider':False,'records':[],'metrics':{},'conflicts':[],
         'scope':'KNOWN_ACCOUNT_EXCLUSIONS_NOT_EXHAUSTIVE_SPECIAL_IDENTITIES',
         'holder_snapshot_slot':check.get('snapshot_slot'),'holder_response_sha256':check.get('response_sha256')}
    mass=verified_holder_mass(check,mint);out['holder_mass_verified']=mass
    bindings={}
    for p in pools:
        if p.get('status')!='POOL_IDENTITY_BOUND' or p.get('snapshot_slot')!=check.get('snapshot_slot'):continue
        d=p['decoded'];vault=d['base_vault'] if d['base_mint']==mint else d['quote_vault'] if d['quote_mint']==mint else None
        if vault:bindings.setdefault(vault,[]).append(p)
    for r in check.get('records',[]):
        if r.get('status') not in {'MATCH','DIFFERS'} or r.get('mint')!=mint:continue
        row={'token_account':r['token_account'],'owner':r['owner'],'raw':r['raw'],'role':'UNKNOWN','basis':'NO_VERIFIED_ROLE','classification':'UNVERIFIED'}
        linked=bindings.get(r['token_account'],[])
        if linked:
            authorities={p['decoded']['authority'] for p in linked}
            declarations=[]
            for p in linked:
                d=p['decoded'];side=0 if d['base_mint']==mint else 1
                if d.get('token_programs'):declarations.append(d['token_programs'][side]==check.get('program_id'))
                if d.get('mint_decimals'):declarations.append(d['mint_decimals'][side]==check.get('decimals'))
            if authorities!={r['owner']} or not all(declarations):
                out['conflicts'].append({'token_account':r['token_account'],'reason':'POOL_AUTHORITY_CONTRADICTS_SAME_BANK_TOKEN'})
            else:
                row.update(role='PROTOCOL_VAULT',basis='PROGRAM_LAYOUT_STORED_VAULT_AND_SAME_BANK_TOKEN_AUTHORITY',classification='CHAIN_ACCOUNT_ROLE',
                           pools=[p['pool_address'] for p in linked],programs=sorted({p['decoded']['program'] for p in linked}),
                           references=sorted({p['decoded']['reference_blob'] for p in linked}))
        label=registry_role(mint,r['token_account'],r['owner'],check.get('snapshot_slot'),registry)
        if label:
            if row['role']!='UNKNOWN' and label['role']!=row['role']:
                row['registry_conflict']=label;out['conflicts'].append({'token_account':r['token_account'],'reason':'REGISTRY_CONFLICTS_WITH_CHAIN_ROLE'})
            elif row['role']=='UNKNOWN':row.update(label)
        out['records'].append(row)
    # Exact known-exclusion ranks aggregate AFTER per-token-account subtraction.
    # Keep unknown balances and label their unresolved semantics explicitly.
    supply=int(check.get('mint_supply_raw','0')) if mass else 0
    for name,excluded in [('known_ex_lp',LP_ROLES),('known_ex_special',DEFAULT_SPECIAL)]:
        totals={};deducted=0;unknown=0;claimed=0
        for r in out['records']:
            raw=int(r['raw'])
            if r['role']=='UNKNOWN':unknown+=raw
            if r['classification']=='ATTRIBUTION_CLAIM':claimed+=raw
            if r['role'] in excluded:deducted+=raw
            else:totals[r['owner']]=totals.get(r['owner'],0)+raw
        owners=sorted(((o,n) for o,n in totals.items() if n),key=lambda x:(-x[1],x[0]));top=sum(n for _,n in owners[:10])
        ok=mass and not out['conflicts'];remaining=supply-deducted
        out['metrics'][name]={'status':'EXACT_KNOWN_EXCLUSION_ARITHMETIC' if ok else 'UNRESOLVED',
            'deducted_raw':str(deducted),'remaining_raw':str(remaining) if mass else 'UNRESOLVED',
            'top10_raw':str(top) if ok else 'UNRESOLVED','top10_pct_of_mint_supply':percent(top,supply) if ok else 'UNRESOLVED',
            'top10_pct_of_remaining':percent(top,remaining) if ok else 'UNRESOLVED',
            'unknown_role_raw':str(unknown),'registry_attributed_raw':str(claimed),
            'eligible_owner_count':len(owners) if ok else None,
            'owners':[{'owner':o,'raw':str(n)} for o,n in owners] if ok else [],
            'global_exhaustive_top10':'UNRESOLVED','unknown_roles_can_change_filtered_top10':True}
    if out['conflicts']:out['reason']='ROLE_EVIDENCE_CONTRADICTION'
    elif not mass:out['reason']='HOLDER_MASS_NOT_VERIFIED'
    else:out['reason']='OFFCHAIN_SPECIAL_IDENTITIES_AND_UNDISCOVERED_POOLS_NOT_EXHAUSTIVE'
    return out


def collect_special_roles(mint,source,market,rpc,registry=None):
    out={'version':1,'status':'INCOMPLETE_EVIDENCE','mint':mint,'pools':[],
         'all_special_roles_normalized':False,'independent_provider':False,'max_pools':MAX_POOLS,
         'discovery_scope':'BOUNDED_INDEXER_HINTS_NOT_ALL_POOLS'}
    if not isinstance(source,dict) or source.get('requested') is not True:return {**out,'status':'NOT_REQUESTED','reason':'NO_ENUMERATION'}
    if not isinstance(market,dict) or market.get('status')!='OK' or market.get('source')!='DEXSCREENER_API' or market.get('mint')!=mint:return {**out,'reason':'POOL_DISCOVERY_SOURCE_UNVERIFIED'}
    hints=[market.get('main_pair')]+(market.get('pool_candidates') or [])
    candidates=[];seen=set()
    for hint in hints:
        if not isinstance(hint,dict) or hint.get('base_address')!=mint:continue
        a=hint.get('pair_address');q=hint.get('quote_address')
        if not all(valid_pubkey(k) for k in (a,q)) or a in seen or len({mint,a,q})!=3:continue
        candidates.append((a,q));seen.add(a)
    out['candidate_count']=len(candidates);out['not_selected_pool_hints']=max(0,len(candidates)-MAX_POOLS)+max(0,market.get('pool_candidates_not_selected',0))
    candidates=candidates[:MAX_POOLS]
    if not candidates:return {**out,'reason':'NO_VALID_POOL_HINTS'}
    response=rpc.call('getMultipleAccounts',[[a for a,_ in candidates],{'encoding':'base64','commitment':'finalized'}],ttl=30)
    discovery_slot=_slot(response);values=response.get('value')
    if not isinstance(values,list) or len(values)!=len(candidates):return {**out,'reason':'DISCOVERY_RESPONSE_INVALID'}
    out['discovery_slot']=discovery_slot;out['discovery_response_sha256']=digest(response)
    accepted=[]
    for (address,quote),account in zip(candidates,values):
        row={'pool_address':address,'quote_mint':quote,'status':'UNVERIFIED'}
        try:
            d=decode_pool(account,address)
            if {d['base_mint'],d['quote_mint']}!={mint,quote}:raise PoolSourceError('POOL_PAIR_MISMATCH')
            row.update(status='DISCOVERED',decoded=d);accepted.append(row)
        except (ValueError,TypeError,KeyError) as exc:row['reason']=str(exc) if isinstance(exc,PoolSourceError) else 'POOL_RESPONSE_INVALID'
        out['pools'].append(row)
    if not accepted:return {**out,'reason':'NO_SUPPORTED_POOL_IDENTITIES'}
    extra=[p['pool_address'] for p in accepted];captured={}
    class CohortRPC:
        def call(self,method,params,ttl=0):
            addresses,cfg=params
            if set(addresses)&set(extra):raise PoolSourceError('COHORT_ADDRESS_COLLISION')
            cfg={**cfg,'minContextSlot':max(cfg.get('minContextSlot',0),discovery_slot)}
            result=rpc.call(method,[addresses+extra,cfg],ttl=ttl)
            actual=_slot(result);vals=result.get('value')
            if actual<cfg['minContextSlot'] or not isinstance(vals,list) or len(vals)!=len(addresses)+len(extra):raise PoolSourceError('COHORT_RESPONSE_INVALID')
            captured.update(slot=actual,hash=digest(result),values=vals[len(addresses):])
            return {'context':result['context'],'value':vals[:len(addresses)]}
    check=collect_holder_binary_check(mint,source,CohortRPC(),max_full_accounts=99-len(extra))
    out['balance_check']=check
    if not captured:return {**out,'reason':check.get('reason','COHORT_UNAVAILABLE')}
    for p,account in zip(accepted,captured['values']):
        try:
            d=decode_pool(account,p['pool_address'])
            if any(d[k]!=p['decoded'][k] for k in ('base_mint','quote_mint','base_vault','quote_vault','authority','program')):raise PoolSourceError('POOL_CHANGED_SINCE_DISCOVERY')
            p.update(status='POOL_IDENTITY_BOUND',decoded=d,snapshot_slot=captured['slot'])
        except (ValueError,TypeError,KeyError) as exc:p.update(status='UNVERIFIED',reason=str(exc) if isinstance(exc,PoolSourceError) else 'POOL_RESPONSE_INVALID')
    out.update(snapshot_slot=captured['slot'],cohort_response_sha256=captured['hash'],
               rankings=derive_special_ranks(mint,check,out['pools'],registry))
    return out
