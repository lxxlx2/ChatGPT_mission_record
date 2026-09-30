"""Integer raw-unit economic evidence; conservative mechanical classifications."""
import hashlib
import json
from ..hashing import digest
from .rpc import RPC,WALLET

INFRA_PROGRAMS=frozenset({'11111111111111111111111111111111','TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb','ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL','ComputeBudget111111111111111111111111111111','MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'})
DEX_PROGRAMS=frozenset({'675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8',
                       'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4'})
AUTH_FIELDS=frozenset({'authority','owner','multisigAuthority','transferAuthority','delegate','withdrawAuthority','stakeAuthority'})
AUTH_OWNER_TYPES=frozenset({'transfer','transferChecked','closeAccount','burn','burnChecked','approve','approveChecked','revoke','setAuthority'})

class IncompleteTransaction(ValueError):pass

def normalize(signature,tx,wallet=WALLET):
    if tx is None:raise IncompleteTransaction('UNAVAILABLE_ON_PUBLIC_RPC')
    if tx.get('version','legacy') not in ('legacy',0,1):raise IncompleteTransaction('UNSUPPORTED_VERSION')
    meta=tx.get('meta');message=tx.get('transaction',{}).get('message')
    if not isinstance(meta,dict) or not isinstance(message,dict):raise IncompleteTransaction('MISSING_META_MESSAGE')
    keys=message.get('accountKeys',[])
    if not keys or any(not isinstance(k,dict) or 'pubkey' not in k or 'signer' not in k for k in keys):raise IncompleteTransaction('JSON_PARSED_KEYS_REQUIRED')
    names=[k['pubkey'] for k in keys]
    if wallet not in names:raise IncompleteTransaction('WALLET_NOT_REFERENCED')
    i=names.index(wallet);pre=meta.get('preBalances');post=meta.get('postBalances')
    if not isinstance(pre,list) or not isinstance(post,list) or len(pre)!=len(keys) or len(post)!=len(keys):raise IncompleteTransaction('BALANCE_VECTOR_INCOMPLETE')
    if meta.get('preTokenBalances') is None or meta.get('postTokenBalances') is None:raise IncompleteTransaction('TOKEN_BALANCE_METADATA_MISSING')
    outer=message.get('instructions');inner=meta.get('innerInstructions')
    if not isinstance(outer,list) or inner is None:raise IncompleteTransaction('INSTRUCTION_METADATA_MISSING')
    all_ix=[('outer',n,ix) for n,ix in enumerate(outer)]
    for group in inner:
        for n,ix in enumerate(group['instructions']):all_ix.append(('inner',f"{group['index']}:{n}",ix))
    authorities=[];programs=set();created=[];closed=[];types=[]
    for scope,index,ix in all_ix:
        program=ix.get('programId')
        if not program and 'programIdIndex' in ix:program=names[ix['programIdIndex']]
        if program:programs.add(program)
        parsed=ix.get('parsed',{});parsed=parsed if isinstance(parsed,dict) else {};info=parsed.get('info',{});kind=parsed.get('type','');types.append(kind)
        for field in sorted(AUTH_FIELDS):
            if field in info:
                authorizing=field not in ('owner','delegate') or (field=='owner' and kind in AUTH_OWNER_TYPES)
                authorities.append({'scope':scope,'instruction':str(index),'program_id':program,'type':kind,'field':field,'account':info[field],'matches_wallet':info[field]==wallet,'is_authority_evidence':authorizing})
        if kind in ('create','createIdempotent','initializeAccount','initializeAccount2','initializeAccount3'):
            created.append({'scope':scope,'instruction':str(index),'account':info.get('account'),'owner':info.get('owner',info.get('wallet')),'mint':info.get('mint')})
        if kind=='closeAccount':closed.append({'scope':scope,'instruction':str(index),'account':info.get('account'),'destination':info.get('destination'),'owner':info.get('owner')})
    before={b['accountIndex']:b for b in meta['preTokenBalances']};after={b['accountIndex']:b for b in meta['postTokenBalances']};deltas=[]
    for index in sorted(before.keys()|after.keys()):
        a=before.get(index);b=after.get(index);identity=b or a
        if a and b and (a['mint']!=b['mint'] or a['uiTokenAmount']['decimals']!=b['uiTokenAmount']['decimals']):raise IncompleteTransaction('TOKEN_IDENTITY_CHANGED')
        if a and b and a.get('owner')!=b.get('owner'):raise IncompleteTransaction('TOKEN_OWNER_CHANGED')
        if 'owner' not in identity:raise IncompleteTransaction('TOKEN_OWNER_MISSING')
        amount_pre=int(a['uiTokenAmount']['amount']) if a else 0;amount_post=int(b['uiTokenAmount']['amount']) if b else 0
        deltas.append({'mint':identity['mint'],'owner':identity['owner'],'pre_amount':str(amount_pre),'post_amount':str(amount_post),'delta':str(amount_post-amount_pre),'decimals':identity['uiTokenAmount']['decimals'],'account_index':index,'wallet_owned':identity['owner']==wallet})
    signer=keys[i]['signer'];fee_payer=i==0;fee=meta.get('fee')
    if type(fee) is not int:raise IncompleteTransaction('FEE_MISSING')
    sol_delta=post[i]-pre[i];economic_sol=sol_delta+(fee if fee_payer else 0)
    owned=[d for d in deltas if d['wallet_owned'] and int(d['delta'])];by_mint={}
    for d in owned:by_mint[d['mint']]=by_mint.get(d['mint'],0)+int(d['delta'])
    values=list(by_mint.values())
    auth=any(a['matches_wallet'] and a['is_authority_evidence'] for a in authorities);active=signer or auth
    logs=meta.get('logMessages') or []
    # DEX interaction alone is insufficient: require authority/signature and opposing economic flows.
    # Native SOL also contains rent refunds/deposits. Without decoded consideration,
    # only opposing owned-token mint deltas establish an exchange in this decoder.
    paired=any(x>0 for x in values) and any(x<0 for x in values)
    dex=bool(programs & DEX_PROGRAMS)
    swap_instruction=any('swap' in k.lower() or 'route' in k.lower() for k in types) or any('Instruction: Swap' in x or 'Instruction: Route' in x or 'Instruction: SharedAccountsRoute' in x for x in logs)
    if meta['err'] is not None:label='UNKNOWN'
    elif active and dex and paired and swap_instruction:label='ACTIVE_SWAP_LIKE'
    elif not active and not fee_payer and not auth and any(x>0 for x in values) and not any(x<0 for x in values):label='PASSIVE_RECEIPT_LIKE'
    elif active and any(k in ('delegate','deactivate','withdraw','split','merge') for k in types) and any(ix.get('program')=='stake' for _,_,ix in all_ix):label='STAKE_LIKE'
    elif programs<=INFRA_PROGRAMS and active and any(k in ('transfer','transferChecked') for k in types) and values and all(x<=0 for x in values):label='TRANSFER_OUT_LIKE'
    elif programs<=INFRA_PROGRAMS and any(k in ('transfer','transferChecked') for k in types) and values and all(x>=0 for x in values):label='TRANSFER_IN_LIKE'
    else:label='UNKNOWN'
    evidence={'event_id':f'frank:tx:{signature}','signature':signature,'slot':tx['slot'],'block_time':tx.get('blockTime'),'tx_err':meta['err'],'fee':fee,'version':tx.get('version','legacy'),'wallet':wallet,'wallet_is_signer':signer,'wallet_is_fee_payer':fee_payer,'wallet_token_owner':any(d['wallet_owned'] for d in deltas),'authority_accounts':authorities,'inner_instruction_authority_evidence':[a for a in authorities if a['scope']=='inner' and a['is_authority_evidence']],'program_ids':sorted(programs),'pre_SOL_lamports':str(pre[i]),'post_SOL_lamports':str(post[i]),'SOL_delta_lamports':str(sol_delta),'fee_adjusted_SOL_delta_lamports':str(economic_sol),'token_balance_deltas':deltas,'created_token_accounts':created,'closed_token_accounts':closed,'instruction_count':len(outer),'inner_instruction_count':len(all_ix)-len(outer),'source_rpc':RPC,'mechanical_classification':label,'classification_evidence':{'wallet_authority':auth,'dex_program_interaction':dex,'swap_instruction_evidence':swap_instruction,'opposing_economic_flows':paired},'raw_transaction_sha256':hashlib.sha256(json.dumps(tx,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),'limitations':['SOL delta includes account rent; fee adjustment is not a swap cost','Unknown program decoders remain UNKNOWN; no PnL','Owner-level changes alone do not establish active swap']}
    evidence['evidence_sha256']=digest(evidence);return evidence


def clusters(evidence,window_seconds=60):
    """Mint/program connected deterministic active clusters; chronological transaction evidence."""
    out=[];current={}
    rows=sorted((e for e in evidence if e['mechanical_classification']=='ACTIVE_SWAP_LIKE' and e['block_time'] is not None),key=lambda e:(e['block_time'],e['slot'],e['signature']))
    for e in rows:
        for d in e['token_balance_deltas']:
            if not d['wallet_owned'] or not int(d['delta']):continue
            mint=d['mint'];c=current.get(mint);programs=set(e['program_ids']) & DEX_PROGRAMS
            if c is None or e['block_time']-c['last_time']>window_seconds or not programs & set(c['program_ids']):
                c={'cluster_id':'frank:cluster:v1:'+digest({'mint':mint,'first_signature':e['signature']}),'token':mint,'first_tx':e['signature'],'last_tx':e['signature'],'first_time':e['block_time'],'last_time':e['block_time'],'tx_count':0,'gross_in':'0','gross_out':'0','net_token_delta':'0','net_SOL_delta_lamports':'0','program_ids':sorted(programs),'signatures':[]};out.append(c);current[mint]=c
            delta=int(d['delta']);c['last_tx']=e['signature'];c['last_time']=e['block_time'];c['program_ids']=sorted(programs|set(c['program_ids']))
            c['gross_in']=str(int(c['gross_in'])+max(0,delta));c['gross_out']=str(int(c['gross_out'])+max(0,-delta));c['net_token_delta']=str(int(c['net_token_delta'])+delta)
            if e['signature'] not in c['signatures']:
                c['tx_count']+=1;c['signatures'].append(e['signature']);c['net_SOL_delta_lamports']=str(int(c['net_SOL_delta_lamports'])+int(e['SOL_delta_lamports']))
    for c in out:c['mechanical_classification']='HIGH_FREQUENCY_CLUSTER' if c['tx_count']>=3 else 'ACTIVE_CLUSTER'
    return out
