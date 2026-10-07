"""Integer raw-unit economic evidence; conservative mechanical classifications.

Program identity primary references:
https://github.com/raydium-io/raydium-library
https://github.com/pump-fun/pump-public-docs/tree/main/idl
https://github.com/MeteoraAg/dlmm-sdk/blob/main/idls/dlmm.json
https://github.com/MeteoraAg/damm-v2-sdk
https://github.com/orca-so/whirlpools
https://github.com/Bonasa-Tech/manifest
Registry membership never suffices without wallet authority, opposing owned
flows and a swap instruction bound to the invoked recognized program.
"""
import hashlib
import json
from ..hashing import digest
from .rpc import RPC,WALLET

INFRA_PROGRAMS=frozenset({'11111111111111111111111111111111','TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb','ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL','ComputeBudget111111111111111111111111111111','MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'})
DEX_PROGRAMS=frozenset({'675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8',
                       'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4'})
PARSER_VERSION='frank-v7'
WSOL='So11111111111111111111111111111111111111112'
DEX_PROGRAMS=DEX_PROGRAMS | frozenset({
    'CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK',
    'CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C',
    'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA',
    '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P',
    'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo',
    # Officially documented markets recovered by the historical coverage audit.
    'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc',  # Orca Whirlpools
    'cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG',  # Meteora DAMM v2
    'MNFSTqtC93rEfYHB6hF82sKdZpUDFWkViLByLd1k1Ms',  # Manifest core
})
AUTH_FIELDS=frozenset({'authority','owner','multisigAuthority','transferAuthority','delegate','withdrawAuthority','stakeAuthority'})
AUTH_OWNER_TYPES=frozenset({'transfer','transferChecked','closeAccount','burn','burnChecked','approve','approveChecked','revoke','setAuthority'})

class IncompleteTransaction(ValueError):pass

def _program_id(ix,names):
    program=ix.get('programId')
    if program:return program
    if 'programIdIndex' not in ix:return None
    index=ix.get('programIdIndex')
    if type(index) is not int or index<0 or index>=len(names):
        raise IncompleteTransaction('PROGRAM_INDEX_INVALID')
    return names[index]

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
        program=_program_id(ix,names)
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
    # Preserve gross ordered wallet-owned token transfer legs. Net pre/post
    # deltas alone cannot distinguish a final target from a routed intermediate
    # that is received and mostly spent again inside the same atomic transaction.
    account_meta={}
    for d in deltas:
        if 0<=d['account_index']<len(names):
            account_meta[names[d['account_index']]]={'owner':d['owner'],'mint':d['mint']}
    for account in created:
        if account.get('account') and account.get('mint'):
            account_meta.setdefault(account['account'],{'owner':account.get('owner'),'mint':account.get('mint')})
    wallet_token_transfer_flows=[]
    token_programs={'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'}
    for scope,index,ix in all_ix:
        parsed=ix.get('parsed',{});parsed=parsed if isinstance(parsed,dict) else {};info=parsed.get('info',{})
        if parsed.get('type') not in ('transfer','transferChecked') or _program_id(ix,names) not in token_programs:continue
        source=info.get('source');destination=info.get('destination')
        source_meta=account_meta.get(source) or {};destination_meta=account_meta.get(destination) or {}
        source_owned=source_meta.get('owner')==wallet;destination_owned=destination_meta.get('owner')==wallet
        if source_owned==destination_owned:continue
        raw=info.get('amount',info.get('tokenAmount',{}).get('amount'))
        if raw is None:continue
        mint=info.get('mint') or source_meta.get('mint') or destination_meta.get('mint')
        if not mint:continue
        decimals=info.get('tokenAmount',{}).get('decimals')
        if decimals is None:
            matched=next((d for d in deltas if d['mint']==mint and d['wallet_owned']),None)
            decimals=matched.get('decimals') if matched else None
        outer_index=int(str(index).split(':',1)[0])
        inner_index=int(str(index).split(':',1)[1]) if scope=='inner' and ':' in str(index) else -1
        wallet_token_transfer_flows.append({
            'scope':scope,'instruction':str(index),'outer_index':outer_index,'inner_index':inner_index,
            'mint':mint,'direction':'OUT' if source_owned else 'IN','raw_amount':str(int(raw)),
            'decimals':decimals,'source':source,'destination':destination,
        })
    wallet_token_transfer_flows.sort(key=lambda x:(x['outer_index'],x['inner_index'],0 if x['direction']=='OUT' else 1))

    signer=keys[i]['signer'];fee_payer=i==0;fee=meta.get('fee')
    if type(fee) is not int:raise IncompleteTransaction('FEE_MISSING')
    sol_delta=post[i]-pre[i];economic_sol=sol_delta+(fee if fee_payer else 0)
    owned=[d for d in deltas if d['wallet_owned'] and int(d['delta'])];by_mint={}
    for d in owned:by_mint[d['mint']]=by_mint.get(d['mint'],0)+int(d['delta'])
    values=list(by_mint.values())
    auth=any(a['matches_wallet'] and a['is_authority_evidence'] for a in authorities);active=signer or auth
    # Bind log instruction evidence to its invoking program, never to an unrelated CPI.
    stack=[];swap_instruction=False
    for log in meta.get('logMessages') or []:
        parts=log.split()
        if len(parts)>=4 and parts[0]=='Program' and parts[2]=='invoke':stack.append(parts[1])
        elif len(parts)>=3 and parts[0]=='Program' and parts[2] in ('success','failed:'):
            if parts[1] in stack:
                # Pop the innermost matching invocation. Re-entrant CPI can place
                # the same program on the stack more than once.
                pos=len(stack)-1-stack[::-1].index(parts[1])
                stack=stack[:pos]
        elif log.startswith('Program log: Instruction: ') and stack and stack[-1] in DEX_PROGRAMS:
            kind=log.split('Instruction: ',1)[1].lower()
            if kind.startswith(('swap','route','sharedaccountsroute','buy','sell')):swap_instruction=True
    for _,_,ix in all_ix:
        parsed=ix.get('parsed',{})
        program=_program_id(ix,names)
        if isinstance(parsed,dict) and program in DEX_PROGRAMS:
            if parsed.get('type','').lower().startswith(('swap','route','sharedaccountsroute','buy','sell')):swap_instruction=True
    # A token account created and closed inside this transaction may be absent from
    # pre/post vectors. Preserve its decoded transfer flow separately from balances.
    transient=[];transient_accounts=set()
    for account in created:
        address=account['account']
        if address in transient_accounts:continue
        if account['owner']!=wallet or account['mint']!=WSOL:continue
        if not any(c['account']==address and c['owner']==wallet for c in closed):continue
        if any(names[d['account_index']]==address for d in deltas):continue
        amount=0;refs=[]
        for scope,index,ix in all_ix:
            parsed=ix.get('parsed',{});parsed=parsed if isinstance(parsed,dict) else {};info=parsed.get('info',{})
            if parsed.get('type') not in ('transfer','transferChecked'):continue
            if _program_id(ix,names) not in ('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'):continue
            raw=info.get('amount',info.get('tokenAmount',{}).get('amount'))
            if raw is None:continue
            flow=(int(raw) if info.get('destination')==address else 0)-(int(raw) if info.get('source')==address else 0)
            if flow:amount+=flow;refs.append({'scope':scope,'instruction':str(index),'delta':str(flow)})
        transient_accounts.add(address)
        if amount:transient.append({'account':address,'mint':WSOL,'owner':wallet,'decimals':9,'net_transfer_raw':str(amount),'transfer_refs':refs})
    economic_mints=dict(by_mint)
    for flow in transient:economic_mints[flow['mint']]=economic_mints.get(flow['mint'],0)+int(flow['net_transfer_raw'])
    economic_values=list(economic_mints.values())
    paired=any(x>0 for x in economic_values) and any(x<0 for x in economic_values)
    dex=bool(programs & DEX_PROGRAMS)
    native_incoming=[]
    for scope,index,ix in all_ix:
        parsed=ix.get('parsed',{});parsed=parsed if isinstance(parsed,dict) else {};info=parsed.get('info',{})
        if _program_id(ix,names)=='11111111111111111111111111111111' and parsed.get('type')=='transfer' and info.get('destination')==wallet:
            native_incoming.append({'scope':scope,'instruction':str(index),'source':info.get('source'),'lamports':str(info['lamports'])})
    if meta['err'] is not None:label='FAILED'
    elif active and dex and paired and swap_instruction:label='ACTIVE_SWAP_LIKE'
    elif not active and not fee_payer and not auth and (any(x>0 for x in values) or (native_incoming and sol_delta>0)) and not any(x<0 for x in values):label='PASSIVE_RECEIPT_LIKE'
    elif active and any(k in ('delegate','deactivate','withdraw','split','merge') for k in types) and any(ix.get('program')=='stake' for _,_,ix in all_ix):label='STAKE_LIKE'
    elif programs<=INFRA_PROGRAMS and active and any(k in ('transfer','transferChecked') for k in types) and values and all(x<=0 for x in values):label='TRANSFER_OUT_LIKE'
    elif programs<=INFRA_PROGRAMS and any(k in ('transfer','transferChecked') for k in types) and values and all(x>=0 for x in values):label='TRANSFER_IN_LIKE'
    else:label='UNKNOWN'
    evidence={'parser_version':PARSER_VERSION,'decoded_transient_token_flows':transient,'wallet_token_transfer_flows':wallet_token_transfer_flows,'native_incoming_transfer_evidence':native_incoming,'event_id':f'frank:tx:{signature}','signature':signature,'slot':tx['slot'],'block_time':tx.get('blockTime'),'tx_err':meta['err'],'fee':fee,'version':tx.get('version','legacy'),'wallet':wallet,'wallet_is_signer':signer,'wallet_is_fee_payer':fee_payer,'wallet_token_owner':any(d['wallet_owned'] for d in deltas),'authority_accounts':authorities,'inner_instruction_authority_evidence':[a for a in authorities if a['scope']=='inner' and a['is_authority_evidence']],'program_ids':sorted(programs),'pre_SOL_lamports':str(pre[i]),'post_SOL_lamports':str(post[i]),'SOL_delta_lamports':str(sol_delta),'fee_adjusted_SOL_delta_lamports':str(economic_sol),'token_balance_deltas':deltas,'created_token_accounts':created,'closed_token_accounts':closed,'instruction_count':len(outer),'inner_instruction_count':len(all_ix)-len(outer),'source_rpc':RPC,'mechanical_classification':label,'classification_evidence':{'wallet_authority':auth,'dex_program_interaction':dex,'swap_instruction_evidence':swap_instruction,'opposing_economic_flows':paired},'raw_transaction_sha256':hashlib.sha256(json.dumps(tx,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),'limitations':['SOL delta includes account rent; fee adjustment is not a swap cost','Unknown program decoders remain UNKNOWN; no PnL','Owner-level changes alone do not establish active swap']}
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
