"""Conservative decoder: balance deltas alone never establish a swap."""
from decimal import Decimal
TYPES={'MARKET_BUY','MARKET_SELL','INTERNAL_TRANSFER','EXTERNAL_TRANSFER','AIRDROP','ATA_CREATE','FEE','CEX_OR_BRIDGE_TRANSFER','PLATFORM_INFRA','UNKNOWN'}
def classify(event,graph):
    e=dict(event); src=e.get('source_owner'); dst=e.get('destination_owner'); t=e.get('block_time',0)
    accepted={a for a in graph.accepted if graph.accepts_at(a,t)}
    infra={w['address'] for w in graph.seed['platform_addresses']}
    e['qualification_blocked']=src in graph.unresolved or dst in graph.unresolved
    if src in accepted and dst in accepted: kind='INTERNAL_TRANSFER'
    elif e.get('raw_event_type') in {'FEE','ATA_CREATE','AIRDROP','CEX_OR_BRIDGE_TRANSFER'}: kind=e['raw_event_type']
    elif e.get('wallet') in infra: kind='PLATFORM_INFRA'
    elif e.get('verified_swap') and e.get('wallet') in accepted and e.get('route_id') and e.get('quote_delta') is not None and e.get('token_delta') is not None:
        base=Decimal(str(e['token_delta'])); quote=Decimal(str(e['quote_delta']))
        kind='MARKET_BUY' if base>0 and quote<0 else 'MARKET_SELL' if base<0 and quote>0 else 'UNKNOWN'
    elif src or dst: kind='EXTERNAL_TRANSFER'
    else: kind='UNKNOWN'
    e['event_type']=kind
    return e
def dedupe(events):
    result={}
    for e in events:
        key=(e['signature'],e.get('wallet'),e.get('route_id'),e.get('mint')) if e.get('verified_swap') else (e['event_id'],)
        if key in result and result[key]!=e:
            # Conflicting pool legs cannot masquerade as a canonical user route.
            result[key]={**result[key],'verified_swap':False,'event_type':'UNKNOWN','confidence':'CONFLICTING_ROUTE_LEGS'}
        else: result[key]=e
    return list(result.values())
def decode_transaction(signature,tx):
    if tx.get('blockTime') is None or not tx.get('meta'): return []
    meta=tx['meta']; message=tx['transaction']['message']; keys=message['accountKeys']
    addresses=[k['pubkey'] if isinstance(k,dict) else k for k in keys]
    signers=[k['pubkey'] for k in keys if isinstance(k,dict) and k.get('signer')]
    instructions=list(message.get('instructions',[]))
    for group in meta.get('innerInstructions',[]): instructions.extend(group['instructions'])
    programs=sorted({i.get('programId') for i in instructions if i.get('programId')})
    common={'signature':signature,'slot':tx['slot'],'block_time':tx['blockTime'],'signers':signers,'fee_payer':addresses[0],'programs':programs,'failed':bool(meta.get('err')),'verified_swap':False}
    balances={}
    for label,rows in [('pre',meta.get('preTokenBalances',[])),('post',meta.get('postTokenBalances',[]))]:
        for b in rows:
            key=(b['accountIndex'],b['mint']); d=balances.setdefault(key,{})
            d[label]=Decimal(b['uiTokenAmount']['amount'])/(Decimal(10)**b['uiTokenAmount']['decimals']);d['owner']=b.get('owner')
    account_owners={addresses[i]:d.get('owner') for (i,m),d in balances.items()}
    out=[]
    for (i,m),d in balances.items():
        out.append({**common,'event_id':f'{signature}:balance:{i}:{m}','wallet':d.get('owner'),'mint':m,'token_account':addresses[i],'token_delta':str(d.get('post',Decimal(0))-d.get('pre',Decimal(0))),'pre_balance':str(d.get('pre',Decimal(0))),'post_balance':str(d.get('post',Decimal(0))),'raw_event_type':'BALANCE_DELTA','confidence':'UNCLASSIFIED'})
    for n,ins in enumerate(instructions):
        parsed=ins.get('parsed',{})
        if not isinstance(parsed,dict): continue
        info=parsed.get('info',{}); typ=parsed.get('type','')
        if typ in {'transfer','transferChecked'} and ins.get('program') in {'spl-token','spl-token-2022'}:
            out.append({**common,'event_id':f'{signature}:transfer:{n}','raw_event_type':'TRANSFER','source_owner':account_owners.get(info.get('source')),'destination_owner':account_owners.get(info.get('destination')),'source_token_account':info.get('source'),'destination_token_account':info.get('destination'),'mint':info.get('mint'),'amount_raw':info.get('amount',info.get('tokenAmount',{}).get('amount')),'confidence':'PARSED_CHAIN'})
        elif ins.get('program')=='spl-associated-token-account':
            out.append({**common,'event_id':f'{signature}:ata:{n}','raw_event_type':'ATA_CREATE','wallet':info.get('wallet'),'confidence':'PARSED_CHAIN'})
    out.append({**common,'event_id':signature+':fee','raw_event_type':'FEE','wallet':addresses[0],'fee_lamports':meta.get('fee'),'confidence':'PARSED_CHAIN'})
    return out
