#!/usr/bin/env python3
"""Research-only, exact-integer/Fraction FIFO replay of normalized token executions.

Normalization and on-chain provenance are caller assertions, NOT independently verified
by this script. No whole-wallet PnL, valuations, API requests or trading actions.
"""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
import re

SOURCE_SHA = '954f3aba66be21911dd627fa40dd3dd0a9fd1d26'
ADDR = re.compile(r'0x[0-9a-fA-F]{40}\Z')
HASH = re.compile(r'0x[0-9a-fA-F]{64}\Z')
INT = re.compile(r'(?:0|[1-9][0-9]*)\Z')
PROOFS = ('receipt_success', 'base_flow_verified', 'quote_flow_verified', 'fee_included_in_quote_net')


def positive_int(value, name, zero=False):
    if not isinstance(value, str) or not INT.fullmatch(value):
        raise ValueError(f'{name}: require a nonnegative decimal integer string')
    n = int(value)
    if not zero and n == 0:
        raise ValueError(f'{name}: must be positive')
    return n


def timestamp(value):
    if not isinstance(value, str) or not value.endswith('Z'):
        raise ValueError('timestamp must be an ISO-8601 UTC Z string')
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as ex:
        raise ValueError('invalid timestamp') from ex
    if dt.utcoffset().total_seconds() != 0:
        raise ValueError('timestamp must be UTC')
    return dt


def frac_str(x):
    return str(x.numerator) if x.denominator == 1 else f'{x.numerator}/{x.denominator}'


def validate(doc, manifest):
    if doc.get('schema') != 'mission-normalized-token-executions-v1':
        raise ValueError('unsupported execution schema')
    if doc.get('source_blob_sha') != SOURCE_SHA or manifest.get('source_blob_sha') != SOURCE_SHA:
        raise ValueError('source sha mismatch')
    items = manifest.get('items', [])
    if manifest.get('total') != 449 or len(items) != 449:
        raise ValueError('source size mismatch')
    addresses = [x.get('address', '') for x in items]
    if len(set(a.lower() for a in addresses)) != 449 or any(
        x.get('index') != i or x.get('batch') != (i-1)//20+1
        or not isinstance(x.get('address'), str) or not ADDR.fullmatch(x['address'])
        for i, x in enumerate(items, 1)
    ):
        raise ValueError('source address/order/batch identity mismatch')
    row = doc.get('source_row')
    if type(row) is not int or not 1 <= row <= 449 or items[row-1].get('index') != row:
        raise ValueError('invalid source row')
    wallet = doc.get('wallet')
    if not isinstance(wallet, str) or not ADDR.fullmatch(wallet) or wallet.lower() != items[row-1]['address'].lower():
        raise ValueError('source wallet identity mismatch')
    token = doc.get('token_contract')
    if not isinstance(token, str) or not ADDR.fullmatch(token):
        raise ValueError('invalid token contract')
    if doc.get('network') not in ('bnb-mainnet', 'eth-mainnet', 'base-mainnet'):
        raise ValueError('invalid network')
    if not isinstance(doc.get('quote_asset'), str) or not doc['quote_asset']:
        raise ValueError('missing quote asset')
    if doc.get('quote_asset') not in ('NATIVE_BNB', 'NATIVE_ETH') and not ADDR.fullmatch(doc['quote_asset']):
        raise ValueError('quote asset must be a chain-native identifier or contract')
    if doc['quote_asset'] == 'NATIVE_BNB' and doc['network'] != 'bnb-mainnet':
        raise ValueError('native quote/network mismatch')
    if doc['quote_asset'] == 'NATIVE_ETH' and doc['network'] == 'bnb-mainnet':
        raise ValueError('native quote/network mismatch')
    for field in ('base_decimals','quote_decimals'):
        if type(doc.get(field)) is not int or not 0 <= doc[field] <= 36:
            raise ValueError('invalid token decimals')
    if doc.get('opening_inventory') != 'ZERO_WITH_SOURCE_PROOF' or doc.get('opening_base_raw') != '0':
        raise ValueError('unverified opening inventory; cost basis unresolved')
    if not isinstance(doc.get('opening_proof_ref'), str) or not doc['opening_proof_ref'].strip():
        raise ValueError('opening inventory evidence required')
    if doc.get('all_token_movements_accounted_for') is not True or not isinstance(doc.get('full_token_flow_proof_ref'), str) or not doc['full_token_flow_proof_ref'].strip():
        raise ValueError('unknown deposits/transfers or incomplete token movement evidence')
    if not isinstance(doc.get('ending_base_raw'), str):
        raise ValueError('ending balance required')
    positive_int(doc['ending_base_raw'], 'ending_base_raw', zero=True)
    events = doc.get('executions')
    if not isinstance(events, list) or not events:
        raise ValueError('no executed trade events')
    seen = set()
    last_key = None
    for idx, e in enumerate(events):
        if not isinstance(e, dict) or e.get('side') not in ('BUY', 'SELL'):
            raise ValueError(f'event {idx}: unsupported/unknown transaction; retain as unresolved')
        h = e.get('tx_hash')
        if not isinstance(h, str) or not HASH.fullmatch(h) or h.lower() in seen:
            raise ValueError('missing/duplicate tx hash (multifill requires audited aggregation)')
        seen.add(h.lower())
        if type(e.get('block')) is not int or e['block'] < 0:
            raise ValueError('invalid execution block')
        t = timestamp(e.get('timestamp_utc'))
        key = (e['block'], t)
        if last_key is not None and (key[0] <= last_key[0] or key[1] < last_key[1]):
            raise ValueError('out-of-order blocks or timestamps; same-block multifills need audited aggregation')
        last_key = key
        if any(e.get(flag) is not True for flag in PROOFS):
            raise ValueError('receipt, token flow, quote flow, or fee not proven')
        if not isinstance(e.get('evidence_ref'), str) or not e['evidence_ref'].strip():
            raise ValueError('missing transaction evidence reference')
        positive_int(e.get('balance_after_raw'), 'balance_after_raw', zero=True)
        fee_asset = e.get('fee_currency')
        if fee_asset == doc['quote_asset']:
            pass
        elif fee_asset in ('NATIVE_BNB', 'NATIVE_ETH') and doc['quote_asset'] not in ('NATIVE_BNB','NATIVE_ETH'):
            positive_int(e.get('gas_converted_quote_raw'), 'gas_converted_quote_raw', zero=True)
            if not isinstance(e.get('gas_fx_source_ref'), str) or not e['gas_fx_source_ref'].strip():
                raise ValueError('cross-currency gas requires execution-time FX evidence')
        else:
            raise ValueError('unknown or unsupported gas/quote currency conversion')
        positive_int(e.get('base_qty_raw'), 'base_qty_raw')
        positive_int(e.get('quote_net_raw'), 'quote_net_raw', zero=False)
        if e['side'] == 'BUY' and e.get('quote_cashflow_direction') != 'OUT':
            raise ValueError('buy quote direction mismatch')
        if e['side'] == 'SELL' and e.get('quote_cashflow_direction') != 'IN':
            raise ValueError('sell quote direction mismatch')
    return events


def replay(doc, manifest):
    # Fail closed: invalid/unknown events produce no misleading partial profit tally.
    try:
        events = validate(doc, manifest)
        cutoff = timestamp(doc['window_start_utc'])
        window_end = timestamp(doc['window_end_utc'])
        if cutoff > window_end:
            raise ValueError('bad window')
        lots = []
        trades = []
        for e in events:
            amount = int(e['base_qty_raw'])
            quote = Fraction(int(e['quote_net_raw']))
            if e['side'] == 'BUY':
                lots.append({'qty':amount, 'cost':quote, 'buy_hash':e['tx_hash']})
                if sum(l['qty'] for l in lots) != int(e['balance_after_raw']):
                    raise ValueError('intermediate token balance mismatch after BUY')
                continue
            remaining = amount
            cost = Fraction(0)
            matches = []
            while remaining:
                if not lots:
                    raise ValueError('SELL without verified historical acquisition/inventory')
                lot = lots[0]
                n = min(remaining, lot['qty'])
                allocated_cost = lot['cost'] * n / lot['qty']
                cost += allocated_cost
                matches.append({'buy_tx_hash':lot['buy_hash'], 'base_qty_raw':str(n),
                                'allocated_cost_quote_raw':frac_str(allocated_cost)})
                lot['qty'] -= n
                lot['cost'] -= allocated_cost
                remaining -= n
                if lot['qty'] == 0:
                    lots.pop(0)
            if sum(l['qty'] for l in lots) != int(e['balance_after_raw']):
                raise ValueError('intermediate token balance mismatch after SELL')
            gain = quote - cost
            t = timestamp(e['timestamp_utc'])
            trades.append({'sell_tx_hash':e['tx_hash'], 'sold_at_utc':e['timestamp_utc'],
                           'token_sold_raw':str(amount), 'proceeds_quote_raw':frac_str(quote),
                           'allocated_cost_quote_raw':frac_str(cost), 'realized_quote_raw':frac_str(gain),
                           'result':'GAIN' if gain > 0 else 'LOSS' if gain < 0 else 'FLAT',
                           'within_fixed_30d_window':cutoff <= t <= window_end,
                           'fifo_lots':matches})
        remaining_qty = sum(lot['qty'] for lot in lots)
        if remaining_qty != int(doc['ending_base_raw']):
            raise ValueError('ending token balance does not reconcile')
        realized_all = sum((Fraction(x['realized_quote_raw']) for x in trades), Fraction())
        recent = sum((Fraction(x['realized_quote_raw']) for x in trades if x['within_fixed_30d_window']), Fraction())
        return {'schema':'mission-token-fifo-replay-v1','status':'CLAIM_REPLAY_ONLY',
                'network':doc['network'],'source_row':doc['source_row'],'wallet':doc['wallet'],
                'token_contract':doc['token_contract'],'quote_asset':doc['quote_asset'],
                'matched_sells':trades,'unspent_base_raw':str(remaining_qty),
                'remaining_basis_quote_raw':frac_str(sum((l['cost'] for l in lots),Fraction())),
                'all_period_realized_quote_raw':frac_str(realized_all),
                'window_realized_quote_raw':frac_str(recent),
                'gain_exits':sum(x['result']=='GAIN' for x in trades),
                'loss_exits':sum(x['result']=='LOSS' for x in trades),
                'wallet_30d_pnl':'UNRESOLVED','wallet_lifetime_pnl':'UNRESOLVED',
                'note':'Normalized events and proof flags are assertions from saved sources; not independently chain-verified; no USD or wallet-level PnL.'}
    except (KeyError, ValueError, TypeError, ZeroDivisionError) as ex:
        return {'schema':'mission-token-fifo-replay-v1','status':'PNL_UNRESOLVED',
                'reason':str(ex),'wallet_30d_pnl':'UNRESOLVED','wallet_lifetime_pnl':'UNRESOLVED',
                'matched_sells':[]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--events',type=Path,required=True)
    ap.add_argument('--output',type=Path)
    args = ap.parse_args()
    result = replay(json.loads(args.events.read_text()),json.loads(args.manifest.read_text()))
    text = json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.write_text(text)
    else:
        print(text,end='')
    if result['status'] != 'CLAIM_REPLAY_ONLY':
        raise SystemExit(3)

if __name__ == '__main__':
    main()
