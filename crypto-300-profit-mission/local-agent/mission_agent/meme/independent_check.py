"""Second-provider balance parity for an explicitly supplied account set.

Both providers are read back-to-back with jsonParsed getMultipleAccounts
(mint + up to 30 accounts by default). Full-set mode batches every supplied
address at this free provider's 10-address request maximum. Only a single common slot
across every batch permits a same-slot claim. This does not independently
enumerate holders or prove that the supplied address set is exhaustive.
"""
import re
import time
from .cluster import RPCJobBudgetExceeded
from .holder_ranks import valid_pubkey
from .job_checkpoint import CheckpointError

MAX_ACCOUNTS=30
# PublicNode's free endpoint returns HTTP403 / JSON-RPC -32602 above ten
# addresses. This is a per-request service constraint, not a report quota.
RPC_BATCH_SIZE=10


def _safe_reason(error):
    code=str(error)
    if re.fullmatch(r'(?:RPC_JOB_(?:TIME|WIRE)_BUDGET_EXHAUSTED|RESPONSE_INVALID|HTTP_[0-9]{3}|RPC_-?[0-9]+|RPC_RATE_LIMITED)',code):return code
    name=type(error).__name__
    return name if name in {'RPCError','TimeoutError','ValueError','TypeError','OSError','KeyError','AttributeError'} else 'SOURCE_UNAVAILABLE'


def _wire_attempts(rpc):
    count=getattr(rpc,'calls',None)
    return count if type(count) is int and count>=0 else None


def _last_source_error(rpc):
    # Optional transport evidence: the budget stop remains the report reason.
    # Validate again because injected/legacy clients need not share our setter.
    code=getattr(rpc,'last_wire_error_code',None)
    if not isinstance(code,str) or len(code)>64:return None
    if re.fullmatch(r'(?:HTTP_[0-9]{3}|RPC_-?[0-9]+|RPC_RATE_LIMITED|RPC_ENVELOPE_INVALID|RPC_POOL_RESPONSE_LIMIT|RPC_HOLDER_RANK_RESPONSE_LIMIT|RPC_ERROR)',code):return code
    return code if code in {'TimeoutError','URLError','OSError','ValueError','JSONDecodeError'} else None


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


def _compare(addresses,primary,secondary):
    rows=[];matches=0;differs=0;missing=0
    for address in addresses:
        x=primary.get(address);y=secondary.get(address)
        if x is None or y is None:status='MISSING';missing+=1
        elif x==y:status='MATCH';matches+=1
        else:status='DIFFERS';differs+=1
        rows.append({'address':address,'kind':(x or y or {}).get('kind'),
                     'primary_raw':(x or {}).get('raw'),'secondary_raw':(y or {}).get('raw'),'status':status,
                     'difference_raw':str(int(y['raw'])-int(x['raw'])) if status=='DIFFERS' and str(x.get('raw')).isdigit() and str(y.get('raw')).isdigit() else None})
    return rows,matches,differs,missing


def _collect_full_set(mint,accounts,primary,secondary,label,clock,progress):
    unique=list(dict.fromkeys(accounts))
    invalid=sum(not valid_pubkey(a) for a in unique)
    addresses=[mint]+[a for a in unique if valid_pubkey(a) and a!=mint]
    base={'version':1,'status':'UNAVAILABLE','secondary_provider':label,
          'scope':'ALL_PROVIDED_TOKEN_ACCOUNTS_AND_MINT_SUPPLY; NOT_INDEPENDENT_ENUMERATION',
          'secondary_wire_attempts':0,'last_source_error':None,'requested_addresses':len(addresses),
          'batch_size':RPC_BATCH_SIZE,'batches_completed':0,'provided_account_set_compared':False,
          'accounts_compared':0,'not_compared':len(addresses),'matches':0,'differences':0,'missing':0,
          'batches':[],'rows':[]}
    if secondary is None:return {**base,'status':'NOT_REQUESTED','reason':'NO_SECONDARY_PROVIDER'}
    if not valid_pubkey(mint) or invalid:
        return {**base,'reason':'INVALID_ACCOUNT_ADDRESS','invalid_addresses':invalid+int(not valid_pubkey(mint))}
    rpc=secondary;primary_slots=[];secondary_slots=[];read_gaps=[]
    for offset in range(0,len(addresses),RPC_BATCH_SIZE):
        batch=addresses[offset:offset+RPC_BATCH_SIZE]
        # A primary budget/checkpoint error must still terminate the whole job.
        try:
            p_slot,p=_read(primary,batch);p_at=clock()
        except (RPCJobBudgetExceeded,CheckpointError):raise
        except Exception as exc:
            return {**base,'status':'PARTIAL' if base['batches_completed'] else 'UNAVAILABLE',
                    'reason':_safe_reason(exc),'failed_batch':len(base['batches']),
                    'failure_phase':'PRIMARY','secondary_wire_attempts':_wire_attempts(rpc),
                    'last_source_error':_last_source_error(primary)}
        try:
            if not callable(getattr(rpc,'call',None)):rpc=secondary()
            if rpc is None:
                return {**base,'status':'PARTIAL' if base['batches_completed'] else 'UNAVAILABLE',
                        'reason':'SECONDARY_PROVIDER_UNAVAILABLE','failed_batch':len(base['batches']),
                        'failure_phase':'SECONDARY'}
            s_slot,s=_read(rpc,batch);s_at=clock()
        except CheckpointError:raise
        except Exception as exc:
            return {**base,'status':'PARTIAL' if base['batches_completed'] else 'UNAVAILABLE',
                    'reason':_safe_reason(exc),'failed_batch':len(base['batches']),
                    'failure_phase':'SECONDARY','secondary_wire_attempts':_wire_attempts(rpc),
                    'last_source_error':_last_source_error(rpc)}
        rows,matches,differs,missing=_compare(batch,p,s)
        gap=round(s_at-p_at,3)
        base['batches'].append({'index':len(base['batches']),'address_offset':offset,'address_count':len(batch),
            'primary_slot':p_slot,'secondary_slot':s_slot,'slot_gap':s_slot-p_slot,
            'read_gap_seconds':gap,'matches':matches,'differences':differs,'missing':missing})
        base['rows'].extend(rows)
        base['batches_completed']+=1;base['accounts_compared']+=len(batch)
        base['not_compared']-=len(batch)
        base['matches']+=matches;base['differences']+=differs;base['missing']+=missing
        base['secondary_wire_attempts']=_wire_attempts(rpc)
        primary_slots.append(p_slot);secondary_slots.append(s_slot);read_gaps.append(gap)
        if progress is not None:progress(base['accounts_compared'],len(addresses))
    same=len(set(primary_slots+secondary_slots))==1
    if base['differences']==0 and base['missing']==0:
        status='SAME_SLOT_ALL_MATCH' if same else 'NEAR_TIME_ALL_MATCH'
    else:status='SAME_SLOT_MISMATCH' if same else 'NEAR_TIME_DIFFERENCES'
    return {**base,'status':status,'provided_account_set_compared':True,
            'primary_slot':primary_slots[0],'secondary_slot':secondary_slots[0],
            'slot_gap':secondary_slots[0]-primary_slots[0],
            'primary_slot_range':[min(primary_slots),max(primary_slots)],
            'secondary_slot_range':[min(secondary_slots),max(secondary_slots)],
            'single_common_slot':same,'read_gap_seconds':max(read_gaps),
            'last_source_error':_last_source_error(rpc)}


def collect_independent_balance_check(mint,accounts,primary,secondary,*,label='PUBLICNODE',clock=time.time,full_accounts=False,progress=None):
    if full_accounts:return _collect_full_set(mint,accounts,primary,secondary,label,clock,progress)
    base={'version':1,'status':'UNAVAILABLE','secondary_provider':label,'scope':'LARGEST_TOKEN_ACCOUNTS_AND_MINT_SUPPLY; NOT_FULL_ENUMERATION','secondary_wire_attempts':0,'last_source_error':None}
    if secondary is None:return {**base,'status':'NOT_REQUESTED','reason':'NO_SECONDARY_PROVIDER'}
    addresses=[mint]+[a for a in dict.fromkeys(accounts) if valid_pubkey(a) and a!=mint][:MAX_ACCOUNTS]
    try:
        p_slot,p=_read(primary,addresses);p_at=clock()
    except RPCJobBudgetExceeded:raise
    except Exception as exc:return {**base,'reason':_safe_reason(exc)}
    rpc=secondary
    try:
        if not callable(getattr(rpc,'call',None)):rpc=secondary()
        if rpc is None:return {**base,'reason':'SECONDARY_PROVIDER_UNAVAILABLE'}
        s_slot,s=_read(rpc,addresses);s_at=clock()
    except CheckpointError:raise
    except Exception as exc:return {**base,'reason':_safe_reason(exc),'secondary_wire_attempts':_wire_attempts(rpc),'last_source_error':_last_source_error(rpc)}
    base['secondary_wire_attempts']=_wire_attempts(rpc)
    rows,matches,differs,missing=_compare(addresses,p,s)
    same=p_slot==s_slot
    if differs==0 and missing==0:status='SAME_SLOT_ALL_MATCH' if same else 'NEAR_TIME_ALL_MATCH'
    else:status='SAME_SLOT_MISMATCH' if same else 'NEAR_TIME_DIFFERENCES'
    return {**base,'status':status,'primary_slot':p_slot,'secondary_slot':s_slot,'slot_gap':s_slot-p_slot,
            'read_gap_seconds':round(s_at-p_at,3),'accounts_compared':len(addresses),'matches':matches,'differences':differs,'missing':missing,'rows':rows}
