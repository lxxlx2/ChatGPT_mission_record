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


def role_coverage(records,check,exact):
    """Partition observed account balances; a pool role never labels an Owner."""
    groups={};totals={'chain_role_raw':0,'attribution_claim_raw':0,'unknown_role_raw':0};unknown_accounts=0
    for row in records:
        raw=int(row['raw']);owner=row['owner']
        group=groups.setdefault(owner,{'owner':owner,'raw':0,'account_count':0,
            'chain_role_raw':0,'attribution_claim_raw':0,'unknown_role_raw':0,'chain_roles':set(),'claimed_roles':set()})
        category='chain_role_raw' if row['classification']=='CHAIN_ACCOUNT_ROLE' else 'attribution_claim_raw' if row['classification']=='ATTRIBUTION_CLAIM' else 'unknown_role_raw'
        group['raw']+=raw;group['account_count']+=1;group[category]+=raw;totals[category]+=raw
        if raw and category=='unknown_role_raw':unknown_accounts+=1
        if raw and category!='unknown_role_raw':group['chain_roles' if category=='chain_role_raw' else 'claimed_roles'].add(row['role'])
    owners=[]
    for group in sorted(groups.values(),key=lambda g:(-g['raw'],g['owner'])):
        if not group['raw']:continue
        owners.append({**group,**{k:str(group[k]) for k in ('raw',*totals)},
            'chain_roles':sorted(group['chain_roles']),'claimed_roles':sorted(group['claimed_roles']),
            'mixed_evidence':sum(group[k]>0 for k in totals)>1})
    return {'version':1,'status':'EXACT_OBSERVED_ROLE_PARTITION' if exact else 'OBSERVED_ROLE_PARTITION_ONLY',
        'scope':'PER_TOKEN_ACCOUNT_EVIDENCE_NOT_WHOLE_OWNER_IDENTITY',
        'holder_snapshot_slot':check.get('snapshot_slot'),'holder_response_sha256':check.get('response_sha256'),
        'observed_account_count':len(records),'observed_raw':str(sum(totals.values())),
        **{k:str(v) for k,v in totals.items()},'unknown_positive_account_count':unknown_accounts,
        'unknown_nonzero_owner_count':sum(int(o['unknown_role_raw'])>0 for o in owners),
        'unknown_pct_of_mint_supply':percent(totals['unknown_role_raw'],int(check['mint_supply_raw'])) if exact else 'UNRESOLVED',
        'all_special_roles_normalized':False,'owners':owners}


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
    out['role_coverage']=role_coverage(out['records'],check,mass and not out['conflicts'])
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
         'discovery_scope':'BOUNDED_INDEXER_OWNER_AND_PROGRAM_HINTS_NOT_ALL_POOLS',
         'owner_hint_scope':'SELF_AUTHORITY_POOL_OWNERS_NOT_GLOBAL_AUTHORITY_REVERSE_LOOKUP',
         'rejected_owner_pool_hints':0}
    if not isinstance(source,dict) or source.get('requested') is not True:return {**out,'status':'NOT_REQUESTED','reason':'NO_ENUMERATION'}
    good_market=isinstance(market,dict) and market.get('status')=='OK' and market.get('source')=='DEXSCREENER_API' and market.get('mint')==mint
    out['indexer_discovery_status']='AVAILABLE' if good_market else 'UNAVAILABLE'
    index_hints=([market.get('main_pair')]+(market.get('pool_candidates') if isinstance(market.get('pool_candidates'),list) else [])) if good_market else []
    indices=[]
    for hint in index_hints[:65]:
        if not isinstance(hint,dict) or hint.get('base_address')!=mint:continue
        a=hint.get('pair_address');q=hint.get('quote_address')
        if not all(valid_pubkey(k) for k in (a,q,mint)) or len({mint,a,q})!=3:continue
        indices.append({'pool_address':a,'quote_mint':q,'candidate_sources':['DEXSCREENER_API'],'owner_hints':[]})
    owner_hints=source.get('owner_pool_hints');owner_hints=owner_hints if isinstance(owner_hints,list) else []
    accounts=source.get('accounts') if isinstance(source.get('accounts'),list) else []
    accounts_by_address={r['token_account']:r for r in accounts if isinstance(r,dict) and valid_pubkey(r.get('token_account'))}
    slot=source.get('snapshot_slot');sha=source.get('response_sha256');owners=[]
    def hash_ok(v):return isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v)
    for h in owner_hints[:8]:
        good=isinstance(h,dict) and source.get('mint')==mint and type(slot) is int and slot>0 and hash_ok(sha)
        if good:
            a=h.get('pair_address');q=h.get('quote_address');v=h.get('target_vault');ref=accounts_by_address.get(v) if isinstance(v,str) else None
            good=(h.get('source')=='SOLANA_FINALIZED_OWNER_ACCOUNT_LAYOUT' and h.get('hint_status')=='STRUCTURAL_POOL_HINT_NOT_ROLE_PROOF'
                and h.get('base_address')==mint and h.get('authority')==a and all(valid_pubkey(k) for k in (a,q,v)) and len({mint,a,q,v})==4
                and type(h.get('enumeration_slot')) is int and h['enumeration_slot']==slot and h.get('enumeration_response_sha256')==sha
                and type(h.get('owner_metadata_slot')) is int and h['owner_metadata_slot']>=slot and hash_ok(h.get('owner_metadata_response_sha256'))
                and ref is not None and ref.get('owner')==a)
        if not good:out['rejected_owner_pool_hints']+=1;continue
        owners.append({'pool_address':a,'quote_mint':q,'candidate_sources':['HOLDER_OWNER_ACCOUNT'],'owner_hints':[h]})
    out['owner_pool_hints_available']=len(owners)
    from .pool_discovery import collect_global_pool_hints
    program_discovery=collect_global_pool_hints(mint,source,rpc)
    out['program_pool_discovery']=program_discovery
    program_hints=[{'pool_address':h['pair_address'],'quote_mint':h['quote_address'],
                    'candidate_sources':['MINT_FILTERED_PROGRAM_QUERY'],'owner_hints':[],'program_hints':[h]}
                   for h in program_discovery['hints']]
    out['program_pool_hints_available']=len(program_hints)
    # Keep the main pair first, then alternate owner and remaining index hints.
    # A long index list cannot starve every owner-derived candidate.
    ordered=indices[:1]
    for i in range(max(len(owners),len(indices[1:]),len(program_hints))):
        if i<len(owners):ordered.append(owners[i])
        if i<len(program_hints):ordered.append(program_hints[i])
        if i<len(indices[1:]):ordered.append(indices[i+1])
    merged={}
    for hint in ordered:
        a=hint['pool_address']
        if a not in merged:merged[a]=hint.copy();merged[a]['candidate_sources']=list(hint['candidate_sources']);merged[a]['owner_hints']=list(hint['owner_hints']);merged[a]['program_hints']=list(hint.get('program_hints',[]))
        else:
            row=merged[a]
            if row['quote_mint']!=hint['quote_mint']:row['hint_quote_conflict']=True
            row['candidate_sources']=sorted(set(row['candidate_sources']+hint['candidate_sources']))
            row['owner_hints']+=hint['owner_hints'];row['program_hints']+=hint.get('program_hints',[])
    all_candidates=list(merged.values());out['candidate_count']=len(all_candidates)
    index_skipped=market.get('pool_candidates_not_selected',0) if good_market else 0
    index_skipped=index_skipped if type(index_skipped) is int and index_skipped>=0 else 0
    owner_summary=source.get('owner_pool_discovery') or {};owner_skipped=owner_summary.get('hints_not_selected',0) if isinstance(owner_summary,dict) else 0
    owner_skipped=owner_skipped if type(owner_skipped) is int and owner_skipped>=0 else 0
    out['not_selected_pool_hints']=max(0,len(all_candidates)-MAX_POOLS)+index_skipped+owner_skipped+max(0,len(owner_hints)-8)+max(0,len(index_hints)-65)+program_discovery.get('hints_not_selected',0)
    candidates=all_candidates[:MAX_POOLS]
    def holder_only(reason):
        # Pool discovery is optional role evidence, not a prerequisite for
        # dated account attribution. Never treat a missing pool as ordinary.
        lower=max(slot if type(slot) is int and slot>0 else 0,out.get('discovery_slot',0))
        class HolderRPC:
            def call(self,method,params,ttl=0):
                addresses,cfg=params;cfg={**cfg,'minContextSlot':max(cfg.get('minContextSlot',0),lower)}
                result=rpc.call(method,[addresses,cfg],ttl=ttl)
                return result
        check=collect_holder_binary_check(mint,source,HolderRPC())
        if type(check.get('snapshot_slot')) is int and check['snapshot_slot']<lower:
            check.update(status='UNAVAILABLE',reason='HOLDER_CONTEXT_BEFORE_DISCOVERY',full_positive_mass_reconciled=False)
        out.update(audit_path='HOLDER_ONLY_NO_BOUND_POOL',pool_discovery_reason=reason,balance_check=check,
                   snapshot_slot=check.get('snapshot_slot'),cohort_response_sha256=check.get('response_sha256'),
                   rankings=derive_special_ranks(mint,check,[],registry))
        return out
    if not candidates:return holder_only('NO_VALID_POOL_HINTS')
    discovery_cfg={'encoding':'base64','commitment':'finalized'}
    owner_slots=[h['owner_metadata_slot'] for p in candidates for h in p['owner_hints']]
    owner_slots+=[h['program_snapshot_slot'] for p in candidates for h in p['program_hints']]
    if owner_slots:discovery_cfg['minContextSlot']=max(owner_slots)
    response=rpc.call('getMultipleAccounts',[[p['pool_address'] for p in candidates],discovery_cfg],ttl=30)
    discovery_slot=_slot(response);values=response.get('value')
    out['discovery_slot']=discovery_slot;out['discovery_response_sha256']=digest(response)
    if not isinstance(values,list) or len(values)!=len(candidates):return holder_only('DISCOVERY_RESPONSE_INVALID')
    accepted=[]
    for candidate,account in zip(candidates,values):
        address=candidate['pool_address'];quote=candidate['quote_mint']
        row={**candidate,'status':'UNVERIFIED'}
        try:
            if row.get('hint_quote_conflict'):raise PoolSourceError('POOL_HINT_QUOTE_CONFLICT')
            d=decode_pool(account,address)
            for h in row['owner_hints']:
                target_vault=d['base_vault'] if d['base_mint']==mint else d['quote_vault'] if d['quote_mint']==mint else None
                if d['authority']!=h['authority'] or target_vault!=h['target_vault']:raise PoolSourceError('OWNER_HINT_POOL_CHANGED')
                if discovery_slot<h['owner_metadata_slot']:raise PoolSourceError('DISCOVERY_BEFORE_OWNER_HINT')
            for h in row['program_hints']:
                target_vault=d['base_vault'] if d['base_mint']==mint else d['quote_vault'] if d['quote_mint']==mint else None
                if d['program']!=h['pool_program'] or d['authority']!=h['authority'] or target_vault!=h['target_vault']:raise PoolSourceError('PROGRAM_HINT_POOL_CHANGED')
                if discovery_slot<h['program_snapshot_slot']:raise PoolSourceError('DISCOVERY_BEFORE_PROGRAM_HINT')
            if {d['base_mint'],d['quote_mint']}!={mint,quote}:raise PoolSourceError('POOL_PAIR_MISMATCH')
            row.update(status='DISCOVERED',decoded=d);accepted.append(row)
        except (ValueError,TypeError,KeyError) as exc:row['reason']=str(exc) if isinstance(exc,PoolSourceError) else 'POOL_RESPONSE_INVALID'
        out['pools'].append(row)
    if not accepted:return holder_only('NO_SUPPORTED_POOL_IDENTITIES')
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
    out.update(audit_path='POOL_AND_HOLDER_COHORT',snapshot_slot=captured['slot'],cohort_response_sha256=captured['hash'],
               rankings=derive_special_ranks(mint,check,out['pools'],registry))
    return out


def withhold_legacy_normalization(ranks,audit):
    """A blanket flag cannot certify the new exhaustive identity contract."""
    if audit.get('status')=='NOT_REQUESTED':return
    audit['legacy_normalization_before_audit']={
        'normalization_complete':ranks.get('normalization_complete'),
        'metrics':dict(ranks.get('metrics') or {})}
    ranks['normalization_complete']=False
    for name in ('GLOBAL_EX_LP_OWNER_TOP10_PCT','GLOBAL_EX_SPECIAL_OWNER_TOP10_PCT'):
        if name in (ranks.get('metrics') or {}):ranks['metrics'][name]='UNRESOLVED'
