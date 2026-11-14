"""One-bank binary balance mass check, not independent RPC-provider parity.

Legacy SPL supply invariant and layouts: solana-program/token state.rs blob
1bf00f7a1b28eb0b776d3bc90605c7e44bfdbcfd. getMultipleAccounts (max100):
https://solana.com/docs/rpc/http/getmultipleaccounts . No account-history,
beneficial-control, filtered-role or independent enumeration claim.
"""
import hashlib
import json
import re
import time
from decimal import Decimal,localcontext,ROUND_HALF_EVEN
from .holder_ranks import valid_pubkey,PROGRAMS,LEGACY_TOKEN_PROGRAM,MAX_ACCOUNTS
from .pool_vaults import _data,_layout,_mint,_key,_option,PoolSourceError

MAX_FULL_ACCOUNTS=99
MAX_SAMPLE_ACCOUNTS=10


def _uint(v):
    if not isinstance(v,str) or not 1<=len(v)<=20 or not v.isascii() or not v.isdigit():return None
    n=int(v);return n if n<=2**64-1 else None


def _selected(rows,max_full_accounts=MAX_FULL_ACCOUNTS):
    if len(rows)<=max_full_accounts:return sorted(rows,key=lambda r:r['token_account']),'ALL_ENUMERATED_ONE_BATCH'
    groups={}
    for row in rows:groups.setdefault(row['owner'],[]).append(row)
    owners=sorted(groups,key=lambda o:(-sum(int(r['raw']) for r in groups[o]),o))
    chosen=[min(groups[o],key=lambda r:(-int(r['raw']),r['token_account'])) for o in owners[:MAX_SAMPLE_ACCOUNTS]]
    seen={r['token_account'] for r in chosen}
    for row in sorted(rows,key=lambda r:(-int(r['raw']),r['token_account'])):
        if len(chosen)>=MAX_SAMPLE_ACCOUNTS:break
        if row['token_account'] not in seen:chosen.append(row);seen.add(row['token_account'])
    return sorted(chosen,key=lambda r:r['token_account']),'BOUNDED_OWNER_SAMPLE'


# Token-2022 ExtensionType ids whose state changes raw-amount/supply mass
# semantics: TransferFeeConfig/Amount (withheld fees), confidential balances.
MASS_BLOCKING_EXTENSIONS={1:'transferFeeConfig',2:'transferFeeAmount',4:'confidentialTransferMint',5:'confidentialTransferAccount',
                          16:'confidentialTransferFeeConfig',17:'confidentialTransferFeeAmount',24:'confidentialMintBurn'}


def token2022_extension_types(raw):
    """TLV list after AccountType byte (offset 166). None when malformed."""
    if len(raw)<=166:return []
    out=[];o=166
    while o+4<=len(raw):
        kind=int.from_bytes(raw[o:o+2],'little');size=int.from_bytes(raw[o+2:o+4],'little')
        if kind==0 and size==0:break
        if o+4+size>len(raw):return None
        out.append(kind);o+=4+size
    return out


def collect_holder_binary_check(mint,source,rpc,*,max_full_accounts=MAX_FULL_ACCOUNTS):
    out={'version':1,'status':'UNAVAILABLE','owner_top10_pct':'UNRESOLVED','owners':[],'records':[],
         'independent_provider':False,'roles_verified':False,'enumeration_membership_independently_verified':False,
         'full_positive_mass_reconciled':False,'enumeration_relation':'UNVERIFIED',
         'scope':'NONZERO_BALANCE_MASS_NOT_ALL_ACCOUNTS_HISTORY_ROLES_OR_BENEFICIAL_CONTROL',
         'method':'SAME_RPC_BINARY_ACCOUNT_DECODE','source_metrics_before_check':{}}
    if not isinstance(source,dict) or source.get('requested') is not True:return {**out,'status':'NOT_REQUESTED','reason':'NO_ENUMERATION'}
    rows=source.get('accounts');program=source.get('program_id');slot=source.get('snapshot_slot');d=source.get('decimals')
    if source.get('mint')!=mint or not valid_pubkey(mint) or program not in PROGRAMS or type(slot) is not int or slot<=0 or type(d) is not int or not 0<=d<=255 or not isinstance(rows,list) or not 1<=len(rows)<=MAX_ACCOUNTS or type(source.get('account_count')) is not int or source['account_count']!=len(rows) or not isinstance(source.get('response_sha256'),str) or not re.fullmatch('[0-9a-f]{64}',source['response_sha256']):
        return {**out,'reason':'ENUMERATION_UNVERIFIED'}
    seen=set()
    for row in rows:
        if not isinstance(row,dict) or not valid_pubkey(row.get('token_account')) or row['token_account']==mint or row['token_account'] in seen or not valid_pubkey(row.get('owner')) or _uint(row.get('raw')) is None or type(row.get('decimals')) is not int or row['decimals']!=d:
            return {**out,'reason':'ENUMERATION_UNVERIFIED'}
        seen.add(row['token_account'])
    if type(max_full_accounts) is not int or not 10<=max_full_accounts<=99:return {**out,'reason':'BATCH_CAP_INVALID'}
    chosen,selection=_selected(rows,max_full_accounts);addresses=[mint]+[r['token_account'] for r in chosen]
    out.update(mint=mint,program_id=program,enumeration_slot=slot,enumeration_response_sha256=source['response_sha256'],
               enumeration_account_count=len(rows),selected_accounts=addresses[1:],selected_account_count=len(chosen),
               accounts_not_selected=len(rows)-len(chosen),selection=selection,
               source_status_before_check=source.get('status'),source_reason_before_check=source.get('reason'),
               source_metrics_before_check=dict(source.get('metrics') or {}))
    result=rpc.call('getMultipleAccounts',[addresses,{'encoding':'base64','commitment':'finalized','minContextSlot':slot}],ttl=30)
    received=time.time();context=result.get('context') if isinstance(result,dict) else None
    actual=context.get('slot') if isinstance(context,dict) else None;values=result.get('value') if isinstance(result,dict) else None
    if type(actual) is not int or actual<=0 or not isinstance(values,list) or len(values)!=len(addresses):return {**out,'reason':'BINARY_RESPONSE_UNVERIFIED'}
    out.update(snapshot_slot=actual,result_received_at=received,time_semantics='JOB_RECEIVED_RESULT_MAY_BE_CACHED_NOT_BLOCK_TIME',
               response_sha256=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest())
    if actual<slot:return {**out,'reason':'CONTEXT_BEFORE_ENUMERATION'}
    flags=set()
    try:mint_info=_mint(values[0],program,flags)
    except (ValueError,TypeError,KeyError):return {**out,'reason':'MINT_BINARY_UNVERIFIED'}
    supply=int(mint_info['raw']);decimals=mint_info['decimals'];total=0;balances={};counts={};all_valid=True;conflict=decimals!=d
    ext_types=set();ext_ok=True
    if program!=LEGACY_TOKEN_PROGRAM:
        try:
            kinds=token2022_extension_types(_data(values[0],program))
            if kinds is None:ext_ok=False
            else:ext_types.update(kinds)
        except (ValueError,TypeError,KeyError):ext_ok=False
    for reference,account in zip(chosen,values[1:]):
        row={'token_account':reference['token_account'],'enumerated_owner':reference['owner'],'enumerated_raw':reference['raw']}
        if account is None:
            row.update(status='MISSING',reason='ACCOUNT_ABSENT_AT_BINARY_SNAPSHOT');all_valid=False;conflict=True
        else:
            try:
                b=_data(account,program);_layout(b,165,2,program,flags)
                if len(b)<165 or b[108] not in (1,2):raise PoolSourceError('TOKEN_STATE_INVALID')
                for offset in (72,109,129):_option(b,offset)
                owner=_key(b[32:64]);actual_mint=_key(b[:32]);raw=int.from_bytes(b[64:72],'little')
                if program!=LEGACY_TOKEN_PROGRAM:
                    kinds=token2022_extension_types(b)
                    if kinds is None:ext_ok=False
                    else:ext_types.update(kinds)
                identity=actual_mint==mint;matches=identity and owner==reference['owner'] and raw==int(reference['raw'])
                row.update(status='MATCH' if matches else 'DIFFERS',owner=owner,mint=actual_mint,raw=str(raw),
                           difference_from_enumerated_raw=str(raw-int(reference['raw'])),state='frozen' if b[108]==2 else 'initialized')
                if b[108]==2:flags.add('FROZEN_ACCOUNT')
                if _option(b,72):flags.add('DELEGATE_PRESENT')
                if _option(b,129):flags.add('CLOSE_AUTHORITY_PRESENT')
                if _option(b,109):flags.add('WRAPPED_NATIVE_ACCOUNT')
                if not matches:conflict=True
                if not identity:all_valid=False
                else:
                    total+=raw
                    if raw:balances[owner]=balances.get(owner,0)+raw;counts[owner]=counts.get(owner,0)+1
            except (ValueError,TypeError,KeyError):
                row.update(status='UNAVAILABLE',reason='BINARY_ACCOUNT_UNVERIFIED');all_valid=False
        out['records'].append(row)
    prior_supply=_uint(source.get('supply_raw'))
    prior_supply_same=source.get('supply_slot')==actual and type(source.get('supply_slot')) is int
    if prior_supply_same and prior_supply is not None and prior_supply!=supply:conflict=True
    out['enumeration_relation']=('SAME_SLOT_CONTRADICTION' if conflict else 'SAME_SLOT_SAMPLE_MATCH' if all_valid else 'SAME_SLOT_CHECK_INCOMPLETE') if actual==slot else 'DIFFERENT_FINALIZED_SLOTS'
    t22_ok=program==LEGACY_TOKEN_PROGRAM or (ext_ok and not ext_types & set(MASS_BLOCKING_EXTENSIONS))
    if program!=LEGACY_TOKEN_PROGRAM:
        out['token_2022_extension_types']=sorted(ext_types)
        out['token_2022_mass_semantics']='NO_WITHHELD_FEE_OR_CONFIDENTIAL_EXTENSION' if t22_ok else 'MASS_AFFECTING_EXTENSION_OR_UNPARSED'
    complete=t22_ok and all_valid and supply>0 and total==supply and "WRAPPED_NATIVE_ACCOUNT" not in flags
    reason=None if complete else 'TOKEN_2022_MASS_SEMANTICS_UNVERIFIED' if not t22_ok else 'NATIVE_BALANCE_MASS_UNVERIFIED' if 'WRAPPED_NATIVE_ACCOUNT' in flags else 'UNVERIFIED_BINARY_ACCOUNTS' if not all_valid else 'ZERO_SUPPLY' if supply==0 else 'SUPPLY_MASS_NOT_RECONCILED'
    def pct(raw):
        if not complete:return 'UNRESOLVED'
        with localcontext() as ctx:
            ctx.prec=80;ctx.rounding=ROUND_HALF_EVEN
            return str((Decimal(raw)*100/Decimal(supply)).quantize(Decimal('0.0001')))
    owners=[{'owner':o,'raw':str(v),'observed_account_count':counts[o],'supply_pct':pct(v)} for o,v in sorted(balances.items(),key=lambda x:(-x[1],x[0]))]
    out.update(status='RECONCILED_NONZERO_BALANCE_MASS' if complete else 'OBSERVED_SAMPLE_ONLY',reason=reason,
               full_positive_mass_reconciled=complete,all_selected_accounts_decoded=all_valid,
               selected_total_raw=str(total),mint_supply_raw=str(supply),decimals=decimals,
               prior_supply_same_slot=prior_supply_same,prior_supply_matches=(prior_supply==supply) if prior_supply_same else None,
               owners=owners,nonzero_owners_observed=len(owners),owner_top10_pct=pct(sum(int(o['raw']) for o in owners[:10])),flags=sorted(flags))
    return out


def verified_holder_mass(check,mint):
    """Validate this stored version's bounded proof before endorsing metrics."""
    if not isinstance(check,dict) or type(check.get('version')) is not int or check.get('version')!=1 or check.get('status')!='RECONCILED_NONZERO_BALANCE_MASS' or check.get('full_positive_mass_reconciled') is not True or check.get('all_selected_accounts_decoded') is not True or (check.get('program_id')!=LEGACY_TOKEN_PROGRAM and not (check.get('program_id') in PROGRAMS and check.get('token_2022_mass_semantics')=='NO_WITHHELD_FEE_OR_CONFIDENTIAL_EXTENSION' and isinstance(check.get('token_2022_extension_types'),list) and not set(check['token_2022_extension_types'])&set(MASS_BLOCKING_EXTENSIONS))) or check.get('mint')!=mint or not valid_pubkey(mint) or check.get('independent_provider') is not False or not isinstance(check.get('flags',[]),list) or 'WRAPPED_NATIVE_ACCOUNT' in check.get('flags',[]):return False
    supply=_uint(check.get('mint_supply_raw'));total=_uint(check.get('selected_total_raw'));rows=check.get('records');owners=check.get('owners');selected=check.get('selected_accounts');slot=check.get('snapshot_slot')
    if not supply or total!=supply or type(slot) is not int or slot<=0 or not isinstance(rows,list) or not 1<=len(rows)<=MAX_FULL_ACCOUNTS or type(check.get('selected_account_count')) is not int or len(rows)!=check.get('selected_account_count') or not isinstance(selected,list) or len(selected)!=len(rows) or any(not valid_pubkey(a) for a in selected) or not isinstance(owners,list):return False
    amounts={};seen=set()
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('status'),str) or row.get('status') not in {'MATCH','DIFFERS'} or row.get('mint')!=mint or not valid_pubkey(row.get('owner')) or not valid_pubkey(row.get('token_account')) or row['token_account'] in seen or _uint(row.get('raw')) is None:return False
        seen.add(row['token_account']);raw=int(row['raw'])
        if raw:amounts[row['owner']]=amounts.get(row['owner'],0)+raw
    if set(selected)!=seen or sum(amounts.values())!=supply:return False
    expected=sorted(amounts.items(),key=lambda x:(-x[1],x[0]))
    if len(owners)!=len(expected) or any(not isinstance(row,dict) or row.get('owner')!=o or row.get('raw')!=str(raw) for row,(o,raw) in zip(owners,expected)):return False
    with localcontext() as ctx:
        ctx.prec=80;ctx.rounding=ROUND_HALF_EVEN
        top=str((Decimal(sum(v for _,v in expected[:10]))*100/Decimal(supply)).quantize(Decimal('0.0001')))
    return check.get('owner_top10_pct')==top
