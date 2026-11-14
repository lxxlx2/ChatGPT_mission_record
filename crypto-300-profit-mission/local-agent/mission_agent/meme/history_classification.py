"""CA account-history interpretations; never change the shared Frank classifier.

An absent wallet message account has no native balance/authority evidence. Token
Program ownership plus conserved inbound instructions can still prove a passive
receipt. A caller-selected Mint also disambiguates a strictly bound two-token
exchange, without assigning a USD value or an exact routed acquisition cost.
"""
from collections import defaultdict
import hashlib
import json

from ..frank.parser import _program_id, DEX_PROGRAMS, AUTH_FIELDS
from ..signals.classifier import QUOTE_MINTS

TOKEN_PROGRAMS = frozenset({'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
                            'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'})


def _uint(value):
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        raise ValueError('RAW_AMOUNT_INVALID')
    number = int(value)
    if number >= 2**64: raise ValueError('RAW_AMOUNT_INVALID')
    return number


def _instructions(tx):
    message = tx['transaction']['message']; keys = message['accountKeys']
    if not keys or any(not isinstance(k, dict) or not isinstance(k.get('pubkey'), str)
                       or type(k.get('signer')) is not bool for k in keys):
        raise ValueError('KEYS_INVALID')
    names = [k['pubkey'] for k in keys]
    if len(names) != len(set(names)): raise ValueError('KEYS_INVALID')
    outer = message['instructions']; inner = tx['meta']['innerInstructions']
    if not isinstance(outer, list) or not isinstance(inner, list): raise ValueError('INSTRUCTIONS_INVALID')
    rows = [(i, ix) for i, ix in enumerate(outer)]
    for group in inner:
        i = group['index']
        if type(i) is not int or not 0 <= i < len(outer): raise ValueError('INSTRUCTIONS_INVALID')
        rows.extend((i, ix) for ix in group['instructions'])
    return names, rows


def _passive_owner_receipt(tx, owner, target):
    names, instructions = _instructions(tx); meta = tx['meta']
    version=tx.get('version','legacy')
    if owner in names or meta['err'] is not None or isinstance(version,bool) or version not in ('legacy', 0, 1): return False
    if type(meta.get('fee')) is not int or meta['fee'] < 0: return False
    if any(not isinstance(meta.get(k), list) or len(meta[k]) != len(names)
           or any(type(v) is not int or v < 0 for v in meta[k]) for k in ('preBalances', 'postBalances')): return False
    before, after = {}, {}
    for source, dest in ((meta['preTokenBalances'], before), (meta['postTokenBalances'], after)):
        if not isinstance(source, list): return False
        for row in source:
            i = row['accountIndex']; d = row['uiTokenAmount']['decimals']
            if type(i) is not int or not 0 <= i < len(names) or i in dest: return False
            if type(d) is not int or not 0 <= d <= 255: return False
            dest[i] = (row['owner'], row['mint'], d, _uint(row['uiTokenAmount']['amount']))
    owned = {}; expected = {}
    for i in before.keys() | after.keys():
        pre, post = before.get(i), after.get(i)
        if pre and post and pre[:3] != post[:3]: return False
        identity = post or pre
        if identity[0] != owner: continue
        delta = (post[3] if post else 0) - (pre[3] if pre else 0)
        if delta < 0 or (delta and identity[1] != target): return False
        owned[names[i]] = identity; expected[names[i]] = delta
    if not any(expected.values()): return False
    observed = defaultdict(int)
    for _, ix in instructions:
        program = _program_id(ix, names); parsed = ix.get('parsed')
        if not isinstance(parsed, dict): continue
        info = parsed.get('info')
        if not isinstance(info, dict): return False
        # Owner absence is not authority evidence, including parsed third-party
        # fields claiming that absent key. Do not promote such a payload.
        if any(info.get(field) == owner for field in AUTH_FIELDS): return False
        if program not in TOKEN_PROGRAMS or parsed.get('type') not in {'transfer', 'transferChecked'}: continue
        src, dst = info.get('source'), info.get('destination')
        if src in owned and dst not in owned: return False
        if dst not in owned or src in owned: continue
        if src not in names or info.get('authority', info.get('multisigAuthority')) not in names: return False
        identity = owned[dst]
        if parsed['type'] == 'transferChecked':
            amount = info['tokenAmount']
            if info.get('mint') != identity[1] or amount['decimals'] != identity[2]: return False
            raw = _uint(amount['amount'])
        else:
            raw = _uint(info['amount'])
            source_identity = next((v for i, v in {**before, **after}.items() if names[i] == src), None)
            if source_identity is None or source_identity[1:3] != identity[1:3]: return False
        observed[dst] += raw
    return all(observed[address] == delta for address, delta in expected.items())


def resolve_history_classification(result, signature, tx, owner, target):
    """Refine only a proved CA account-history context; default results stay intact."""
    if result.get('classification') != 'UNKNOWN_NEEDS_REVIEW': return result
    try:
        if tx['transaction']['signatures'][0] != signature or tx['meta']['err'] is not None: return result
        reason = result.get('classification_reason')
        details = result.get('classification_details') or {}
        if details.get('chain_metadata_reason') == 'WALLET_NOT_REFERENCED' and _passive_owner_receipt(tx, owner, target):
            return {**result, 'classification': 'PASSIVE_TRANSFER',
                    'classification_reason': 'TOKEN_OWNER_CONSERVED_PASSIVE_INBOUND',
                    'classification_details': {'scope': 'TOKEN_OWNER_ACCOUNT_ONLY', 'native_balance': 'UNAVAILABLE',
                                               'authority': 'NOT_ESTABLISHED', 'market_buy': False},
                    'history_resolution': 'PASSIVE_TOKEN_OWNER_RECEIPT'}
        e = result.get('evidence') or {}
        changed = details.get('changed_assets') or []
        if reason != 'AMBIGUOUS_USER_EXCHANGE_ASSETS' or len(changed) != 2: return result
        if e.get('wallet_is_signer') is not True or e.get('mechanical_classification') != 'ACTIVE_SWAP_LIKE': return result
        raw_sha=hashlib.sha256(json.dumps(tx,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        if e.get('signature')!=signature or e.get('wallet')!=owner or e.get('raw_transaction_sha256')!=raw_sha: return result
        values = {x['mint']: (int(x['delta']), x['decimals']) for x in changed}
        if len(values) != 2 or target not in values or set(values) & QUOTE_MINTS: return result
        if any(type(d) is not int or not 0<=d<=255 or abs(delta)>=2**64 for delta,d in values.values()): return result
        quote = next(m for m in values if m != target)
        if values[target][0] * values[quote][0] >= 0: return result
        names, instructions = _instructions(tx)
        market_groups = {i for i, ix in instructions if _program_id(ix, names) in DEX_PROGRAMS}
        groups = []; flows = e.get('wallet_token_transfer_flows') or []
        for mint, (delta, _) in values.items():
            legs = [f for f in flows if f.get('mint') == mint]
            if any(f.get('direction') not in {'IN','OUT'} for f in legs): return result
            net = sum(_uint(f['raw_amount']) * (1 if f['direction'] == 'IN' else -1) for f in legs)
            if net != delta: return result
            groups.append((delta,legs))
        # A recognized swap somewhere else in the transaction cannot bind this
        # pair. With one market-bearing outer group, its verified swap evidence
        # and both conserved wallet legs share the same atomic route context.
        if len(market_groups) != 1: return result
        for delta,legs in groups:
            # All incoming units must come through this market context, not an
            # unrelated airdrop. Additional outgoing units may be fees or other
            # transfers: preserve them in the observed net pair and explicitly
            # withhold exact trade cost/USDC amount rather than dropping them.
            if any(f['direction']=='IN' and f['outer_index'] not in market_groups for f in legs): return result
            direction='IN' if delta>0 else 'OUT'
            if not any(f['direction']==direction and f['outer_index'] in market_groups for f in legs): return result
        delta, decimals = values[target]; quote_delta, quote_decimals = values[quote]
        return {**result, 'classification': 'ACTIVE_TRADE',
                'classification_reason': 'TARGET_MINT_BOUND_TWO_TOKEN_EXCHANGE',
                'history_resolution': 'TARGET_MINT_TWO_TOKEN_EXCHANGE',
                'trade': {'mint': target, 'direction': 'BUY' if delta > 0 else 'SELL',
                          'token_amount_raw': str(abs(delta)), 'token_decimals': decimals,
                          'quote_asset': quote, 'quote_amount_raw': str(abs(quote_delta)), 'quote_decimals': quote_decimals,
                          'amount_predicate': 'UNDETERMINED', 'amount_predicate_reason': 'NON_STANDARD_TOKEN_PAIR',
                          'route_amount_semantics': 'NET_WALLET_PAIR_NOT_EXACT_FINAL_TARGET_COST'}}
    except (KeyError, TypeError, ValueError, IndexError):
        return result


def resolution_record(result, signature, tx, owner, target):
    return {'owner': owner, 'signature': signature, 'mint': target,
            'classification': result['classification'], 'reason': result['history_resolution'],
            'raw_transaction_sha256': hashlib.sha256(json.dumps(tx, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()}
