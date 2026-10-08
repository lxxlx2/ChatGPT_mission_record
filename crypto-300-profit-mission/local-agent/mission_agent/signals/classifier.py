"""Conservative user-level classification over immutable jsonParsed chain evidence."""
from collections import defaultdict
from ..frank.parser import normalize, IncompleteTransaction, WSOL, INFRA_PROGRAMS
from .policy import USDC

USDT='Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
QUOTE_MINTS = frozenset({WSOL, USDC, USDT})

def classify(signature, tx, wallet):
    base = {'signature': signature, 'wallet': wallet, 'slot': tx.get('slot'),
            'block_time': tx.get('blockTime'), 'classification': 'UNKNOWN_NEEDS_REVIEW',
            'classification_reason': 'INSUFFICIENT_MARKET_EXCHANGE_EVIDENCE',
            'frank_is_signer': False, 'frank_is_authority': False, 'trade': None}
    try:
        e = normalize(signature, tx, wallet)
    except (IncompleteTransaction, KeyError, TypeError, ValueError, IndexError) as exc:
        base['classification_reason'] = 'INCOMPLETE_CHAIN_METADATA:' + type(exc).__name__
        return base
    base.update(frank_is_signer=e['wallet_is_signer'],
                frank_is_authority=e['classification_evidence']['wallet_authority'], evidence=e)
    label = e['mechanical_classification']
    if e['tx_err'] is not None:
        base.update(classification='FAILED_TX', classification_reason='TRANSACTION_FAILED')
        return base
    groups = defaultdict(lambda: {'delta': 0, 'pre': 0, 'post': 0, 'decimals': None})
    for d in e['token_balance_deltas']:
        if not d['wallet_owned']: continue
        g = groups[d['mint']]
        if g['decimals'] is not None and g['decimals'] != d['decimals']:
            base['classification_reason']='WALLET_MINT_DECIMALS_CONFLICT'
            return base
        g.update(delta=g['delta']+int(d['delta']), pre=g['pre']+int(d['pre_amount']),
                 post=g['post']+int(d['post_amount']), decimals=d['decimals'])
    # Transient WSOL flow is decoded transfer evidence, never inferred from rent-inclusive SOL delta.
    for f in e['decoded_transient_token_flows']:
        g = groups[f['mint']]
        if g['decimals'] is not None and g['decimals'] != f['decimals']:
            base['classification_reason']='WALLET_MINT_DECIMALS_CONFLICT'
            return base
        g['delta'] += int(f['net_transfer_raw']); g['decimals'] = f['decimals']
    changed = {m:g for m,g in groups.items() if g['delta']}
    authority = e['wallet_is_signer']
    if label == 'ACTIVE_SWAP_LIKE' and authority:
        tokens = [(m,g) for m,g in changed.items() if m not in QUOTE_MINTS]
        quotes = [(m,g) for m,g in changed.items() if m in QUOTE_MINTS]
        details={
            'changed_assets':[
                {'mint':m,'delta':str(g['delta']),'decimals':g['decimals']}
                for m,g in sorted(changed.items())
            ],
            'target_assets':[m for m,_ in tokens],
            'quote_assets':[m for m,_ in quotes],
        }
        # Multiple positive non-quote balances are economically multi-target at
        # the wallet boundary. Receive/spend conservation can identify a residual
        # flow candidate, but cannot prove user intent or bind that spend to the
        # other target without router/market-call level evidence. Keep such cases
        # fail-closed instead of collapsing them into a single ACTIVE_TRADE.
        if len(tokens)>1:
            flow_by_mint=defaultdict(lambda:{'in_raw':0,'out_raw':0,'first_in':None,'first_out':None,'last_out':None})
            token_mints={m for m,_ in tokens}
            for flow in e.get('wallet_token_transfer_flows') or []:
                mint=flow.get('mint')
                if mint not in token_mints:continue
                try:raw=int(flow.get('raw_amount') or 0)
                except (TypeError,ValueError):continue
                order=(int(flow.get('outer_index',0)),int(flow.get('inner_index',-1)))
                item=flow_by_mint[mint]
                if flow.get('direction')=='IN':
                    item['in_raw']+=raw
                    if item['first_in'] is None or order<item['first_in']:item['first_in']=order
                elif flow.get('direction')=='OUT':
                    item['out_raw']+=raw
                    if item['first_out'] is None or order<item['first_out']:item['first_out']=order
                    if item['last_out'] is None or order>item['last_out']:item['last_out']=order
            created_mints={
                a.get('mint') for a in e.get('created_token_accounts') or []
                if a.get('owner')==wallet and a.get('mint')
            }
            residual_candidates=[]
            for mint,g in tokens:
                flow=flow_by_mint[mint]
                if (
                    mint in created_mints and g['pre']==0 and g['delta']>0
                    and flow['in_raw']>0 and flow['out_raw']>0
                    and flow['first_in'] is not None and flow['first_out'] is not None
                    and flow['first_in']<flow['first_out']
                    and flow['in_raw']-flow['out_raw']==g['delta']
                ):
                    residual_candidates.append({
                        'mint':mint,'net_delta':str(g['delta']),
                        'gross_in_raw':str(flow['in_raw']),'gross_out_raw':str(flow['out_raw']),
                        'first_in_order':list(flow['first_in']),'last_out_order':list(flow['last_out']),
                        'proof':'CREATED_ZERO_PRE_RECEIVED_THEN_SPENT_CONSERVED_RESIDUAL_ONLY',
                        'route_binding':'UNPROVEN',
                    })
            details['residual_flow_candidates']=residual_candidates
            base.update(
                classification_reason='AMBIGUOUS_USER_EXCHANGE_ASSETS',
                classification_details=details,
            )
            return base
        effective_tokens=tokens
        if len(effective_tokens)==1 and quotes:
            mint,g=effective_tokens[0]
            opposing=[(m,q) for m,q in quotes if g['delta']*q['delta']<0]
            details['opposing_quote_assets']=[m for m,_ in opposing]
            if len(opposing)==1:
                quote,q=opposing[0]
                composite=len(quotes)>1
                amount_predicate='USDC_DIRECT_NUMERIC' if quote==USDC and not composite else 'UNDETERMINED'
                amount_reason=None
                if composite:amount_reason='COMPOSITE_QUOTE_LEGS'
                elif quote!=USDC:amount_reason='NON_USDC_QUOTE'
                quote_legs=[
                    {'asset':'SOL' if qm==WSOL else qm,'raw_delta':str(qg['delta']),'decimals':qg['decimals']}
                    for qm,qg in sorted(quotes,key=lambda x:x[0])
                ]
                # No observed wallet-owned transfer through an additional mint
                # supports a simple single-target quote for research. Missing
                # flow evidence or an additional non-target/quote mint is unresolved.
                flows=e.get('wallet_token_transfer_flows')
                route_mints=sorted({
                    flow.get('mint') for flow in (flows or [])
                    if isinstance(flow,dict) and flow.get('mint')
                    and flow['mint'] not in ({mint} | QUOTE_MINTS)
                })
                route_status=(
                    'UNVERIFIED' if flows is None or route_mints
                    else 'NO_INTERMEDIATE_TRANSFER_OBSERVED'
                )
                if route_mints:
                    # Gross input with an unresolved routed residual is not
                    # verified final-target cost, even if the input is USDC.
                    amount_predicate='UNDETERMINED'
                    amount_reason='ROUTED_RESIDUAL_ASSETS'
                base.update(
                    classification='ACTIVE_TRADE',
                    classification_reason=(
                        'SIGNED_DEX_SWAP_SINGLE_TARGET_PRIMARY_QUOTE_WITH_AUXILIARY_LEGS'
                        if composite else 'SIGNED_DEX_SWAP_OPPOSING_OWNED_FLOWS'
                    ),
                    classification_details=details,
                    trade={
                        'mint':mint,'direction':'BUY' if g['delta']>0 else 'SELL',
                        'token_amount_raw':str(abs(g['delta'])),'token_decimals':g['decimals'],
                        'quote_asset':'SOL' if quote==WSOL else quote,
                        'quote_amount_raw':str(abs(q['delta'])),'quote_decimals':q['decimals'],
                        'referenced_pre_raw':str(g['pre']),'referenced_post_raw':str(g['post']),
                        'amount_predicate':amount_predicate,'amount_predicate_reason':amount_reason,
                        'quote_legs':quote_legs,
                        'route_intermediate_assets':(
                            [{'mint':m} for m in route_mints] if route_mints
                            else None if flows is None else []
                        ),
                        'route_intermediate_evidence_status':route_status,
                        'route_amount_semantics':(
                            'GROSS_QUOTE_OUT_NOT_EXACT_FINAL_TARGET_COST'
                            if route_mints else 'DIRECT_OR_SINGLE_TARGET_QUOTE'
                        ),
                    },
                )
                return base
        base.update(
            classification_reason='AMBIGUOUS_USER_EXCHANGE_ASSETS',
            classification_details=details,
        )
        return base
    if label=='ACTIVE_SWAP_LIKE':
        base['classification_reason']='WALLET_NOT_SIGNER_AUTHORITY_UNPROVEN'
        return base
    passive = not e['wallet_is_signer'] and not e['classification_evidence']['wallet_authority']
    created = [a for a in e['created_token_accounts'] if a['owner']==wallet]
    keys=tx['transaction']['message']['accountKeys']
    owned_accounts={keys[d['account_index']]['pubkey'] for d in e['token_balance_deltas'] if d['wallet_owned']}
    instructions=list(tx['transaction']['message']['instructions'])
    for group in tx['meta']['innerInstructions']:instructions.extend(group['instructions'])
    inbound_transfer=False
    for ix in instructions:
        parsed=ix.get('parsed',{})
        if not isinstance(parsed,dict):continue
        info=parsed.get('info',{})
        if parsed.get('type') in ('transfer','transferChecked') and info.get('destination') in owned_accounts:
            inbound_transfer=True
    if passive and created and not changed and not e['native_incoming_transfer_evidence'] and set(e['program_ids'])<=INFRA_PROGRAMS:
        base.update(classification='ATA_CREATE',classification_reason='THIRD_PARTY_ATA_CREATE')
    elif passive and label=='PASSIVE_RECEIPT_LIKE' and (inbound_transfer or e['native_incoming_transfer_evidence']):
        base.update(classification='PASSIVE_TRANSFER',classification_reason='FRANK_NOT_SIGNER')
    elif label in ('TRANSFER_OUT_LIKE','TRANSFER_IN_LIKE'):
        base.update(classification='PASSIVE_TRANSFER',classification_reason='PLAIN_TRANSFER_NO_MARKET_EXCHANGE')
    elif e['wallet_is_fee_payer'] and not changed and set(e['program_ids'])<= {'ComputeBudget111111111111111111111111111111','MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'}:
        base.update(classification='FEE',classification_reason='FEE_ONLY')
    return base
