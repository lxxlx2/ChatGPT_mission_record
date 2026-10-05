"""Conservative user-level classification over immutable jsonParsed chain evidence."""
from collections import defaultdict
from ..frank.parser import normalize, IncompleteTransaction, WSOL, INFRA_PROGRAMS

QUOTE_MINTS = frozenset({WSOL, 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'})

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
        if g['decimals'] is not None and g['decimals'] != d['decimals']: return base
        g.update(delta=g['delta']+int(d['delta']), pre=g['pre']+int(d['pre_amount']),
                 post=g['post']+int(d['post_amount']), decimals=d['decimals'])
    # Transient WSOL flow is decoded transfer evidence, never inferred from rent-inclusive SOL delta.
    for f in e['decoded_transient_token_flows']:
        g = groups[f['mint']]; g['delta'] += int(f['net_transfer_raw']); g['decimals'] = f['decimals']
    changed = {m:g for m,g in groups.items() if g['delta']}
    authority = e['wallet_is_signer']
    if label == 'ACTIVE_SWAP_LIKE' and authority:
        tokens = [(m,g) for m,g in changed.items() if m not in QUOTE_MINTS]
        quotes = [(m,g) for m,g in changed.items() if m in QUOTE_MINTS]
        if len(tokens)==1 and len(quotes)==1 and tokens[0][1]['delta']*quotes[0][1]['delta']<0:
            mint,g = tokens[0]; quote,q = quotes[0]
            base.update(classification='ACTIVE_TRADE', classification_reason='SIGNED_DEX_SWAP_OPPOSING_OWNED_FLOWS',
                        trade={'mint':mint,'direction':'BUY' if g['delta']>0 else 'SELL',
                               'token_amount_raw':str(abs(g['delta'])), 'token_decimals':g['decimals'],
                               'quote_asset':'SOL' if quote==WSOL else quote,
                               'quote_amount_raw':str(abs(q['delta'])), 'quote_decimals':q['decimals'],
                               'referenced_pre_raw':str(g['pre']), 'referenced_post_raw':str(g['post'])})
        else:
            base['classification_reason']='AMBIGUOUS_USER_EXCHANGE_ASSETS'
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
