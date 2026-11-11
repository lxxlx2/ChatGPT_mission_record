"""Second-provider balance parity for the largest token accounts.

Both providers are read back-to-back with jsonParsed getMultipleAccounts
(mint + up to 30 accounts). Same context slot => exact parity claim; different
slots => near-time comparison only. This never re-enumerates all holders.
"""
import time
from .holder_ranks import valid_pubkey

MAX_ACCOUNTS=30


def _read(rpc,addresses):
    r=rpc.call('getMultipleAccounts',[addresses,{'encoding':'jsonParsed','commitment':'finalized'}])
    slot=((r or {}).get('context') or {}).get('slot') if isinstance(r,dict) else None
    values=(r or {}).get('value') if isinstance(r,dict) else None
    if type(slot) is not int or not isinstance(values,list) or len(values)!=len(addresses):raise ValueError('RESPONSE_INVALID')
    out={}
    for address,v in zip(addresses,values):
        info=(((v or {}).get('data') or {}).get('parsed') or {}).get('info') if isinstance(v,dict) and isinstance(v.get('data'),dict) else None
        if not isinstance(info,dict):out[address]=None;continue
        if 'supply' in info:out[address]={'kind':'mint','raw':str(info.get('supply'))}
        else:out[address]={'kind':'account','raw':str((info.get('tokenAmount') or {}).get('amount')),'owner':info.get('owner'),'mint':info.get('mint')}
    return slot,out


def collect_independent_balance_check(mint,accounts,primary,secondary,*,label='PUBLICNODE',clock=time.time):
    base={'version':1,'status':'UNAVAILABLE','secondary_provider':label,'scope':'LARGEST_TOKEN_ACCOUNTS_AND_MINT_SUPPLY; NOT_FULL_ENUMERATION'}
    if secondary is None:return {**base,'status':'NOT_REQUESTED','reason':'NO_SECONDARY_PROVIDER'}
    addresses=[mint]+[a for a in dict.fromkeys(accounts) if valid_pubkey(a) and a!=mint][:MAX_ACCOUNTS]
    try:
        p_slot,p=_read(primary,addresses);p_at=clock()
        s_slot,s=_read(secondary,addresses);s_at=clock()
    except Exception as exc:return {**base,'reason':str(exc)[:60] or type(exc).__name__}
    rows=[];matches=0;differs=0;missing=0
    for a in addresses:
        x=p.get(a);y=s.get(a)
        if x is None or y is None:status='MISSING';missing+=1
        elif x==y:status='MATCH';matches+=1
        else:status='DIFFERS';differs+=1
        rows.append({'address':a,'kind':(x or y or {}).get('kind'),'primary_raw':(x or {}).get('raw'),'secondary_raw':(y or {}).get('raw'),'status':status,
                     'difference_raw':str(int(y['raw'])-int(x['raw'])) if status=='DIFFERS' and str(x.get('raw')).isdigit() and str(y.get('raw')).isdigit() else None})
    same=p_slot==s_slot
    if differs==0 and missing==0:status='SAME_SLOT_ALL_MATCH' if same else 'NEAR_TIME_ALL_MATCH'
    else:status='SAME_SLOT_MISMATCH' if same else 'NEAR_TIME_DIFFERENCES'
    return {**base,'status':status,'primary_slot':p_slot,'secondary_slot':s_slot,'slot_gap':s_slot-p_slot,
            'read_gap_seconds':round(s_at-p_at,3),'accounts_compared':len(addresses),'matches':matches,'differences':differs,'missing':missing,'rows':rows}
