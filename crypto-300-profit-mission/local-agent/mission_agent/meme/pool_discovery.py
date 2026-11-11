"""Mint-filtered discovery for observed Raydium shared authorities, not roles.

Queries use only pinned mainnet layouts from pool_programs. A seed/bump hash
match is a bounded discovery trigger, not proof of authority ownership. Every
candidate still needs the existing same-bank pool/token re-read before ranking.
"""
import hashlib
import json
import time
from functools import lru_cache
from .holder_ranks import valid_pubkey,PROGRAMS,MAX_ACCOUNTS
from .pool_programs import CPMM,AMM_V4,LAYOUTS,stored_bump_authority,decode_pool
from .pool_vaults import _key,_slot,PoolSourceError,MAX_RPC_BYTES

PROGRAM_SEEDS={CPMM:b'vault_and_lp_mint_auth_seed',AMM_V4:b'amm authority'}
MAX_QUERY_ACCOUNTS=128
MAX_POOL_HINTS=8


def query(mint,program,side,slot):
    spec=LAYOUTS[program]
    filters=[{'dataSize':spec['length']}]
    if spec['account']:filters.append({'memcmp':{'offset':0,'bytes':_key(hashlib.sha256(('account:'+spec['account']).encode()).digest()[:8])}})
    filters.append({'memcmp':{'offset':spec['offsets'][side],'bytes':mint}})
    return [program,{'encoding':'base64','commitment':'finalized','withContext':True,'minContextSlot':slot,'filters':filters}]


def valid_pool_discovery_query(params):
    if not isinstance(params,list) or len(params)!=2 or not isinstance(params[0],str) or params[0] not in PROGRAM_SEEDS:return False
    cfg=params[1]
    if not isinstance(cfg,dict) or set(cfg)!={'encoding','commitment','withContext','minContextSlot','filters'}:return False
    if cfg.get('encoding')!='base64' or cfg.get('commitment')!='finalized' or cfg.get('withContext') is not True:return False
    slot=cfg.get('minContextSlot');filters=cfg.get('filters')
    if type(slot) is not int or slot<=0 or not isinstance(filters,list) or not filters:return False
    if any(not isinstance(f,dict) or ('dataSize' in f and type(f['dataSize']) is not int) or ('memcmp' in f and (not isinstance(f['memcmp'],dict) or type(f['memcmp'].get('offset')) is not int)) for f in filters):return False
    last=filters[-1];match=last.get('memcmp') if isinstance(last,dict) else None
    mint=match.get('bytes') if isinstance(match,dict) else None
    if not valid_pubkey(mint):return False
    return any(params==query(mint,params[0],side,slot) for side in (0,1))


@lru_cache(maxsize=2)
def _authority_candidates(program):
    return frozenset(stored_bump_authority(program,PROGRAM_SEEDS[program],bump) for bump in range(256))


def _uint(value):
    return isinstance(value,str) and 1<=len(value)<=20 and value.isascii() and value.isdigit() and int(value)<=2**64-1


def collect_global_pool_hints(mint,source,rpc):
    out={'version':1,'status':'NOT_REQUESTED','scope':'OBSERVED_SHARED_AUTHORITY_MINT_FILTERED_PROGRAM_DISCOVERY_NOT_EXHAUSTIVE',
         'trigger_semantics':'SEED_BUMP_HASH_MATCH_IS_ONLY_A_QUERY_TRIGGER','attempts':[],'hints':[],
         'max_logical_queries':4,'max_accounts_per_query':MAX_QUERY_ACCOUNTS,'max_response_bytes_per_query':MAX_RPC_BYTES,
         'logical_queries':0,'hints_not_selected':0,'membership_reconciliation':'REQUIRES_LATER_SAME_BANK_REREAD'}
    rows=source.get('accounts') if isinstance(source,dict) else None
    slot=source.get('snapshot_slot') if isinstance(source,dict) else None
    sha=source.get('response_sha256') if isinstance(source,dict) else None
    if not isinstance(source,dict) or source.get('requested') is not True or source.get('mint')!=mint or not valid_pubkey(mint) or not isinstance(source.get('program_id'),str) or source.get('program_id') not in PROGRAMS or type(slot) is not int or slot<=0 or not isinstance(sha,str) or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha) or not isinstance(rows,list) or not 1<=len(rows)<=MAX_ACCOUNTS or type(source.get('account_count')) is not int or source.get('account_count')!=len(rows):
        return {**out,'reason':'ENUMERATION_UNVERIFIED'}
    accounts={};owners=set()
    for row in rows:
        if not isinstance(row,dict) or not valid_pubkey(row.get('token_account')) or row['token_account'] in accounts or not valid_pubkey(row.get('owner')) or not _uint(row.get('raw')):return {**out,'reason':'ENUMERATION_UNVERIFIED'}
        accounts[row['token_account']]=row
        if int(row['raw']):owners.add(row['owner'])
    triggered={program:owners&_authority_candidates(program) for program in PROGRAM_SEEDS}
    triggered={program:matched for program,matched in triggered.items() if matched}
    if not triggered:return {**out,'reason':'NO_OBSERVED_SHARED_AUTHORITY'}
    out.update(status='PARTIAL',triggered_programs=sorted(triggered),enumeration_slot=slot,enumeration_response_sha256=sha)
    from .cluster import RPCJobBudgetExceeded,RPCError
    found={}
    for program,matched in triggered.items():
        for side in (0,1):
            params=query(mint,program,side,slot)
            attempt={'program':program,'mint_side':'BASE' if side==0 else 'QUOTE','mint_offset':LAYOUTS[program]['offsets'][side],
                     'filters':params[1]['filters'],'min_context_slot':slot,'status':'UNAVAILABLE','matching_rows':0,'eligible_rows':0}
            out['attempts'].append(attempt);out['logical_queries']+=1
            try:
                response=rpc.call('getProgramAccounts',params,ttl=30)
                attempt['result_received_at']=time.time()
                attempt['time_semantics']='RECEIVED_RESULT_MAY_BE_CACHED_NOT_BLOCK_TIME'
                if not isinstance(response,dict) or set(response)!={'context','value'} or not isinstance(response.get('value'),list):raise PoolSourceError('POOL_ENUM_ENVELOPE_INVALID')
                raw=json.dumps(response,sort_keys=True,separators=(',',':')).encode()
                if len(raw)>MAX_RPC_BYTES:raise PoolSourceError('POOL_ENUM_RESPONSE_LIMIT')
                actual=_slot(response)
                if actual<slot:raise PoolSourceError('POOL_ENUM_SLOT_BEFORE_SOURCE')
                if len(response['value'])>MAX_QUERY_ACCOUNTS:raise PoolSourceError('POOL_ENUM_ACCOUNT_LIMIT')
                digest=hashlib.sha256(raw).hexdigest();seen=set();staged=[]
                for row in response['value']:
                    if not isinstance(row,dict) or not valid_pubkey(row.get('pubkey')) or row['pubkey'] in seen:raise PoolSourceError('POOL_ENUM_ROW_INVALID')
                    seen.add(row['pubkey']);d=decode_pool(row.get('account'),row['pubkey'])
                    if d['program']!=program or d['base_mint' if side==0 else 'quote_mint']!=mint:raise PoolSourceError('POOL_ENUM_FILTER_MISMATCH')
                    vault=d['base_vault' if side==0 else 'quote_vault'];target=accounts.get(vault)
                    if target is None or d['authority'] not in matched or target['owner']!=d['authority']:continue
                    staged.append({'source':'MINT_FILTERED_PROGRAM_QUERY','pair_address':row['pubkey'],'base_address':mint,
                        'quote_address':d['quote_mint' if side==0 else 'base_mint'],'target_vault':vault,'authority':d['authority'],
                        'pool_program':program,'reference_blob':d['reference_blob'],'program_snapshot_slot':actual,
                        'program_response_sha256':digest,'enumeration_slot':slot,'enumeration_response_sha256':sha,
                        'observed_target_vault_raw':target['raw']})
                attempt.update(status='OBSERVED_QUERY_RESULT',snapshot_slot=actual,response_sha256=digest,matching_rows=len(response['value']),eligible_rows=len(staged),
                               coverage='THIS_FILTER_RESPONSE_NOT_ALL_PROTOCOL_POOLS')
                for hint in staged:found[hint['pair_address']]=hint
            except RPCJobBudgetExceeded:raise
            except PoolSourceError as exc:attempt['reason']=str(exc)
            except RPCError as exc:attempt['reason']='POOL_ENUM_RESPONSE_LIMIT' if str(exc)=='RPC_POOL_RESPONSE_LIMIT' else 'RPC_UNAVAILABLE'
            except (ValueError,TypeError,KeyError,OverflowError,TimeoutError,OSError):attempt['reason']='POOL_ENUM_SOURCE_INVALID'
    hints=sorted(found.values(),key=lambda h:(-int(h['observed_target_vault_raw']),h['pair_address']))
    out.update(hints=hints[:MAX_POOL_HINTS],hints_not_selected=max(0,len(hints)-MAX_POOL_HINTS),
               query_failures=sum(a['status']!='OBSERVED_QUERY_RESULT' for a in out['attempts']))
    return out
