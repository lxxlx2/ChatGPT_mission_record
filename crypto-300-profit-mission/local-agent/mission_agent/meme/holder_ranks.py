"""Bounded, mint-filtered finalized token account enumeration and Owner ranks.

Source contract: https://solana.com/docs/rpc/http/getprogramaccounts and
https://www.solana-program.com/docs/token . No indexer, signer or order flow.
"""
import hashlib
import json
from decimal import Decimal

LEGACY_TOKEN_PROGRAM='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
TOKEN_2022_PROGRAM='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
PROGRAMS={LEGACY_TOKEN_PROGRAM,TOKEN_2022_PROGRAM}
MAX_RESPONSE_BYTES=64*1024*1024
MAX_ACCOUNTS=200000
BINARY_SLICE={'offset':0,'length':166}
ALPHABET='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
DEFAULT_SPECIAL={'LP','AMM_POOL','PROTOCOL_VAULT','ESCROW','VESTING','LOCK','BURN','CEX','BRIDGE','ROUTER','PUBLIC_INFRA','PUBLIC_PROGRAM','MARKET_MAKER'}

class HolderRankSourceError(ValueError):
    pass


def valid_pubkey(value):
    if not isinstance(value,str) or not 32<=len(value)<=44:return False
    n=0
    for ch in value:
        if ch not in ALPHABET:return False
        n=n*58+ALPHABET.index(ch)
    zeroes=len(value)-len(value.lstrip('1'))
    return zeroes+(n.bit_length()+7)//8==32


def valid_enumeration_query(params):
    if not isinstance(params,list) or len(params)!=2 or not isinstance(params[0],str) or params[0] not in PROGRAMS:return False
    cfg=params[1]
    if not isinstance(cfg,dict) or set(cfg)-{'encoding','commitment','withContext','filters','minContextSlot','dataSlice'}:return False
    if cfg.get('encoding')=='base64':
        if cfg.get('dataSlice')!=BINARY_SLICE:return False
    elif cfg.get('encoding')!='jsonParsed' or 'dataSlice' in cfg:return False
    if cfg.get('commitment')!='finalized' or cfg.get('withContext') is not True:return False
    filters=cfg.get('filters')
    if not isinstance(filters,list):return False
    expected_size=[{'dataSize':165}] if params[0]==LEGACY_TOKEN_PROGRAM else []
    if len(filters)!=len(expected_size)+1 or filters[:-1]!=expected_size:return False
    rule=filters[-1]
    if not isinstance(rule,dict) or set(rule)!={'memcmp'}:return False
    match=rule['memcmp']
    if not isinstance(match,dict) or set(match)!={'offset','bytes'} or type(match['offset']) is not int or match['offset']!=0 or not valid_pubkey(match['bytes']):return False
    slot=cfg.get('minContextSlot')
    return slot is None or (type(slot) is int and slot>0)


def _b58(raw):
    n=int.from_bytes(raw,'big');out=''
    while n:n,r=divmod(n,58);out=ALPHABET[r]+out
    return '1'*(len(raw)-len(raw.lstrip(b'\0')))+out


def _parsed_row(account,mint,decimals):
    data=account.get('data');parsed=data.get('parsed') if isinstance(data,dict) else None
    info=parsed.get('info') if isinstance(parsed,dict) else None
    if not isinstance(info,dict) or parsed.get('type')!='account' or info.get('mint')!=mint or not valid_pubkey(info.get('owner')) or not isinstance(info.get('state'),str) or info.get('state') not in {'initialized','frozen'}:raise HolderRankSourceError('ACCOUNT_ROW_INVALID')
    token=info.get('tokenAmount');amount=token.get('amount') if isinstance(token,dict) else None
    if not isinstance(amount,str) or not 1<=len(amount)<=20 or not amount.isascii() or not amount.isdigit() or int(amount)>2**64-1 or type(token.get('decimals')) is not int or token['decimals']!=decimals:raise HolderRankSourceError('ACCOUNT_ROW_INVALID')
    return int(amount),info['owner']


def _binary_row(account,mint,program):
    """SPL token Account layout: mint 0..32, owner 32..64, amount 64..72, state 108.
    Token-2022 extended accounts carry AccountType=2 at byte 165."""
    import base64,binascii
    data=account.get('data');space=account.get('space')
    if not isinstance(data,list) or len(data)!=2 or data[1]!='base64' or not isinstance(data[0],str) or type(space) is not int:raise HolderRankSourceError('ACCOUNT_ROW_INVALID')
    try:b=base64.b64decode(data[0],validate=True)
    except (binascii.Error,ValueError):raise HolderRankSourceError('ACCOUNT_ROW_INVALID')
    if program==LEGACY_TOKEN_PROGRAM:ok=space==165 and len(b)==165
    else:ok=(space==165 and len(b)==165) or (space>165 and len(b)==166 and b[165]==2)
    if not ok or _b58(b[0:32])!=mint or b[108] not in (1,2):raise HolderRankSourceError('ACCOUNT_ROW_INVALID')
    return int.from_bytes(b[64:72],'little'),_b58(b[32:64])


def _slot(value):return type(value) is int and value>0


MAX_OWNER_POOL_HINTS=8


def discover_owner_pool_hint(mint,owner,account,metadata_slot,enumeration_slot,enumeration_hash,metadata_hash,account_owners):
    """Reuse observed owner metadata; a hint alone never excludes a balance."""
    from .pool_programs import decode_pool,SUPPORTED_PROGRAMS
    if not isinstance(account,dict) or not isinstance(account.get('owner'),str) or account.get('owner') not in SUPPORTED_PROGRAMS:return None
    if not valid_pubkey(mint) or not valid_pubkey(owner) or not _slot(metadata_slot) or not _slot(enumeration_slot) or metadata_slot<enumeration_slot:return None
    try:d=decode_pool(account,owner)
    except (ValueError,TypeError,KeyError,OverflowError):return None
    # Pool-authority protocols can be discovered through token owners. Shared
    # Raydium global authorities cannot be inverted into a list of pool states.
    if d['authority']!=owner or mint not in {d['base_mint'],d['quote_mint']}:return None
    side='base' if d['base_mint']==mint else 'quote';other='quote' if side=='base' else 'base'
    target_vault=d[side+'_vault']
    if account_owners.get(target_vault)!=owner:return None
    return {'source':'SOLANA_FINALIZED_OWNER_ACCOUNT_LAYOUT','hint_status':'STRUCTURAL_POOL_HINT_NOT_ROLE_PROOF',
            'pair_address':owner,'base_address':mint,'quote_address':d[other+'_mint'],
            'target_vault':target_vault,'authority':owner,'pool_program':d['program'],
            'reference_blob':d['reference_blob'],'owner_metadata_slot':metadata_slot,'enumeration_slot':enumeration_slot,
            'enumeration_response_sha256':enumeration_hash,'owner_metadata_response_sha256':metadata_hash}


def collect_mint_holder_ranks(mint,program,supply,decimals,supply_slot,rpc,role_resolver,*,normalization_declared=False,max_accounts=MAX_ACCOUNTS,special_roles=DEFAULT_SPECIAL,expected_top_accounts=None,largest_slot=None,owner_reader=None,supply_recheck=None,supply_fixed_above=False):
    if type(supply) is not int or not 0<=supply<=2**64-1 or type(decimals) is not int or not 0<=decimals<=255:raise HolderRankSourceError('SUPPLY_INVALID')
    if not valid_pubkey(mint) or program not in PROGRAMS:raise HolderRankSourceError('IDENTITY_INVALID')
    cfg={'encoding':'base64','dataSlice':dict(BINARY_SLICE),'commitment':'finalized','withContext':True,
         'filters':([{'dataSize':165}] if program==LEGACY_TOKEN_PROGRAM else [])+[{'memcmp':{'offset':0,'bytes':mint}}]}
    if _slot(supply_slot):cfg['minContextSlot']=supply_slot
    result=rpc.call('getProgramAccounts',[program,cfg],ttl=30)
    if not isinstance(result,dict) or set(result)-{'context','value'} or not isinstance(result.get('context'),dict) or not _slot(result['context'].get('slot')) or not isinstance(result.get('value'),list):
        raise HolderRankSourceError('ENVELOPE_INVALID')
    records=result['value'];snapshot_slot=result['context']['slot']
    if len(records)>max_accounts:raise HolderRankSourceError('ACCOUNT_LIMIT')
    seen=set();balances={};counts={};nonzero=0;account_balances={};accounts=[]
    for row in records:
        if not isinstance(row,dict) or not valid_pubkey(row.get('pubkey')) or row['pubkey'] in seen:raise HolderRankSourceError('ACCOUNT_ROW_INVALID')
        seen.add(row['pubkey']);account=row.get('account')
        if not isinstance(account,dict) or account.get('owner')!=program or account.get('executable') is not False:raise HolderRankSourceError('ACCOUNT_ROW_INVALID')
        raw,owner_key=_binary_row(account,mint,program) if isinstance(account.get('data'),list) else _parsed_row(account,mint,decimals)
        account_balances[row["pubkey"]]=raw
        accounts.append({"token_account":row["pubkey"],"owner":owner_key,"raw":str(raw),"decimals":decimals})
        if raw:
            nonzero+=1;owner=owner_key;balances[owner]=balances.get(owner,0)+raw;counts[owner]=counts.get(owner,0)+1
    enumeration_hash=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    owner_ids=sorted(balances);roles={};role_slots=[];owner_role_slots={};role_reason=None;pool_hints=[]
    account_owners={r['token_account']:r['owner'] for r in accounts}
    for offset in range(0,len(owner_ids),100):
        batch=owner_ids[offset:offset+100]
        response=owner_reader(batch,snapshot_slot) if owner_reader else rpc.call('getMultipleAccounts',[batch,{'encoding':'jsonParsed','commitment':'finalized','minContextSlot':snapshot_slot}],ttl=60)
        if not isinstance(response,dict) or not isinstance(response.get('context'),dict) or not _slot(response['context'].get('slot')) or not isinstance(response.get('value'),list) or len(response['value'])!=len(batch):
            role_reason='OWNER_METADATA_UNAVAILABLE';role_slots.append(None)
            for owner in owner_ids[offset:]:
                roles[owner]=role_resolver(owner,{'value':None});owner_role_slots[owner]=None
            break
        role_slots.append(response['context']['slot'])
        metadata_hash=hashlib.sha256(json.dumps(response,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        for owner,account in zip(batch,response['value']):
            roles[owner]=role_resolver(owner,{'value':account});owner_role_slots[owner]=response['context']['slot']
            hint=discover_owner_pool_hint(mint,owner,account,response['context']['slot'],snapshot_slot,enumeration_hash,metadata_hash,account_owners)
            if hint:pool_hints.append(hint)
    pool_hints.sort(key=lambda h:(-balances[h['authority']],h['pair_address']))
    pool_hints_not_selected=max(0,len(pool_hints)-MAX_OWNER_POOL_HINTS)
    pool_hints=pool_hints[:MAX_OWNER_POOL_HINTS]
    total=sum(balances.values())
    top_reconciled=(all(account_balances.get(k)==v for k,v in expected_top_accounts.items()) if expected_top_accounts is not None and largest_slot==snapshot_slot else None)
    supply_bracket=None
    if supply>0 and total==supply and snapshot_slot!=supply_slot and supply_fixed_above and supply_recheck is not None and _slot(supply_slot) and supply_slot<snapshot_slot:
        # No mint authority => supply can only shrink. Equal finalized supply at
        # slots before and after the enumeration slot fixes it at that slot.
        try:after=supply_recheck()
        except Exception:after=None
        if isinstance(after,tuple) and len(after)==2 and after[0]==supply and _slot(after[1]) and after[1]>=snapshot_slot:
            supply_bracket={'before_slot':supply_slot,'after_slot':after[1],'method':'NO_MINT_AUTHORITY_MONOTONIC_SUPPLY_BRACKET'}
    complete=supply>0 and total==supply and (snapshot_slot==supply_slot or supply_bracket is not None) and top_reconciled is not False
    reason=None if complete else 'SUPPLY_SUM_MISMATCH' if total!=supply else 'SNAPSHOT_SLOT_UNRECONCILED' if snapshot_slot!=supply_slot else 'SUPPLY_UNAVAILABLE'
    if top_reconciled is False:reason='TOP20_RECONCILIATION_MISMATCH'
    role_complete=(bool(owner_ids) and normalization_declared is True and all(s==snapshot_slot for s in role_slots)
                   and all(role in special_roles or role in {'ORDINARY','EOA','DEV','CREATOR','TREASURY'} for role,_ in roles.values()))
    def pct(raw):return str((Decimal(raw)*100/Decimal(supply)).quantize(Decimal('0.0001'))) if complete else 'UNRESOLVED'
    owners=[{'owner':owner,'raw':str(raw),'account_count':counts[owner],'role':roles[owner][0],
             'role_source':roles[owner][1],'role_slot':owner_role_slots[owner],'supply_pct':pct(raw)} for owner,raw in sorted(balances.items(),key=lambda x:(-x[1],x[0]))]
    def top10(excluded):return sum(int(r['raw']) for r in [r for r in owners if r['role'] not in excluded][:10])
    metrics={'GLOBAL_OWNER_TOP10_PCT':pct(top10(set())),
             'GLOBAL_EX_LP_OWNER_TOP10_PCT':pct(top10({'LP','AMM_POOL','PROTOCOL_VAULT'})) if role_complete else 'UNRESOLVED',
             'GLOBAL_EX_SPECIAL_OWNER_TOP10_PCT':pct(top10(special_roles)) if role_complete else 'UNRESOLVED'}
    return {'requested':True,'status':'COMPLETE_SNAPSHOT' if complete else 'INCOMPLETE_EVIDENCE','reason':reason,
            'source':'SOLANA_FINALIZED_GET_PROGRAM_ACCOUNTS','mint':mint,'program_id':program,
            'snapshot_slot':snapshot_slot,'supply_slot':supply_slot,'supply_bracket':supply_bracket,'encoding':cfg['encoding'],'largest_slot':largest_slot,'top20_reconciled':top_reconciled,'owner_metadata_slots':role_slots,
            'response_sha256':enumeration_hash,
            'owner_pool_hints':pool_hints,'owner_pool_discovery':{'scope':'SELF_AUTHORITY_POOL_OWNERS_NOT_GLOBAL_AUTHORITY_REVERSE_LOOKUP',
                'retained_hints':len(pool_hints),'hints_not_selected':pool_hints_not_selected,'max_hints':MAX_OWNER_POOL_HINTS,'additional_rpc_calls':0},
            'account_count':len(records),'nonzero_accounts':nonzero,'nonzero_owner_count':len(owners),
            'total_raw':str(total),'supply_raw':str(supply),'decimals':decimals,
            'normalization_complete':role_complete,'owner_metadata_reason':role_reason,'metrics':metrics,'owners':owners,
            'accounts':sorted(accounts,key=lambda r:r['token_account'])}
