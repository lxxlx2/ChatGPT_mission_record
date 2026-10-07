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
        routed_intermediates=[]
        effective_tokens=tokens
        if len(tokens)>1:
            flow_by_mint=defaultdict(lambda:{
                'in_raw':0,'out_raw':0,'first_in':None,'first_out':None,'last_out':None
            })
            changed_mints=set(changed)
            for flow in e.get('wallet_token_transfer_flows') or []:
                mint=flow.get('mint')
                if mint not in changed_mints:continue
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
            target_first_in={}
            for mint,_ in tokens:
                target_first_in[mint]=flow_by_mint[mint]['first_in']
            for mint,g in tokens:
                f=flow_by_mint[mint]
                # Conservative route proof: the wallet-owned ATA was created in this
                # transaction, the asset was received before being spent again, a
                # positive residual remains, and exactly one other positive target
                # is first received only after that spend. No value/dust threshold.
                if mint not in created_mints or g['delta']<=0 or not f['in_raw'] or not f['out_raw']:
                    continue
                if f['first_in'] is None or f['last_out'] is None or f['first_in']>=f['last_out']:
                    continue
                later_targets=[
                    other for other,_ in tokens if other!=mint and
                    target_first_in.get(other) is not None and target_first_in[other]>f['last_out']
                ]
                upstream_quotes=[
                    qm for qm,qg in quotes
                    if qg['delta']<0 and flow_by_mint[qm]['out_raw']>0 and
                    flow_by_mint[qm]['first_out'] is not None and
                    flow_by_mint[qm]['first_out']<f['first_in']
                ]
                if len(later_targets)==1 and len(upstream_quotes)==1:
                    routed_intermediates.append({
                        'mint':mint,'net_delta':str(g['delta']),
                        'gross_in_raw':str(f['in_raw']),'gross_out_raw':str(f['out_raw']),
                        'first_in_order':list(f['first_in']),'last_out_order':list(f['last_out']),
                        'upstream_quote_asset':upstream_quotes[0],
                        'downstream_target':later_targets[0],
                    })
            routed_mints={x['mint'] for x in routed_intermediates}
            effective_tokens=[(m,g) for m,g in tokens if m not in routed_mints]
            details['routed_intermediate_assets']=routed_intermediates
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
                base.update(
                    classification='ACTIVE_TRADE',
                    classification_reason=(
                        'SIGNED_DEX_SWAP_ROUTED_SINGLE_TARGET_WITH_RESIDUAL_INTERMEDIATE'
                        if routed_intermediates else
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
                        'route_intermediate_assets':routed_intermediates,
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
