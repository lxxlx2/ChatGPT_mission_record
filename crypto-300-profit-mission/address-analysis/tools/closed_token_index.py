#!/usr/bin/env python3
"""Offline replay of pinned, reviewed token-roundtrip *source claims*.

This does not verify receipts through RPC or compute whole-wallet PnL.
"""
import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re

SOURCE = '954f3aba66be21911dd627fa40dd3dd0a9fd1d26'
ADDR = re.compile(r'0x[0-9a-fA-F]{40}\Z')


def D(x):
    if isinstance(x, bool) or x is None:
        raise ValueError('Invalid numeric type')
    try:
        v = Decimal(str(x))
    except InvalidOperation as e:
        raise ValueError('Invalid decimal') from e
    if not v.is_finite():
        raise ValueError('Non-finite numeric')
    return v


def index_sources(manifest, rtx, sauce):
    if manifest.get('source_blob_sha') != SOURCE or manifest.get('total') != 449:
        raise ValueError('Wrong source snapshot')
    universe = manifest.get('items', [])
    if len(universe) != 449 or any(x['index'] != i for i, x in enumerate(universe, 1)):
        raise ValueError('Invalid source order')

    def identity(row, wallet):
        if not isinstance(row, int) or isinstance(row, bool) or not 1 <= row <= 449 or not ADDR.fullmatch(wallet):
            raise ValueError('Bad wallet identity')
        if universe[row - 1]['address'].lower() != wallet.lower():
            raise ValueError('Wallet source mismatch')

    entries = []
    identity(rtx['source_row'], rtx['wallet'])
    if rtx['network'] != 'bnb-mainnet' or rtx['opening_token_balance_before_buy_raw'] != '0' or rtx['ending_token_balance_after_sells_raw'] != '0':
        raise ValueError('RTX source inventory not closed')
    txs = rtx['txs']
    if len([t for t in txs if t['kind'] == 'buy']) != 1 or len([t for t in txs if t['kind'] == 'sell']) != 5:
        raise ValueError('RTX tx shape mismatch')
    for t in txs:
        if not re.fullmatch(r'0x[0-9a-fA-F]{64}', t['hash']):
            raise ValueError('Missing tx proof hash')
    bought = -sum((D(t['delta_bnb']) for t in txs if t['kind'] == 'buy'), Decimal(0))
    proceeds = sum((D(t['delta_bnb']) for t in txs if t['kind'] == 'sell'), Decimal(0))
    gain = proceeds - bought
    if bought <= 0 or proceeds < 0 or abs(gain - D(rtx['calculation']['net_bnb'])) > Decimal('0.000000000000002'):
        raise ValueError('RTX native cashflow mismatch')
    entries.append({'row': rtx['source_row'], 'wallet': rtx['wallet'], 'chain': 'bnb-mainnet',
                    'token': rtx['token'], 'symbol': rtx['token_symbol'], 'buy_native_bnb': str(bought),
                    'sell_native_bnb': str(proceeds), 'realized_bnb': str(gain),
                    'classification': 'GAIN' if gain > 0 else 'LOSS' if gain < 0 else 'FLAT',
                    'precision': 'FLOAT_SOURCE_APPROXIMATE', 'wallet_pnl': 'UNRESOLVED',
                    'evidence': 'evidence/batch-001-row-016-rtx5090-roundtrip.json'})
    if sauce.get('source_blob_sha') != SOURCE or sauce['network'] != 'bnb-mainnet' or len(sauce['roundtrips']) != 2:
        raise ValueError('Sauce source mismatch')
    seen = set()
    for item in sauce['roundtrips']:
        row = item['row']
        identity(row, item['wallet'])
        if row in seen or row not in (2, 4) or item['token'].lower() != sauce['token']['address'].lower():
            raise ValueError('Sauce identity mismatch')
        seen.add(row)
        balances = item['balance_of_raw']
        if balances['before_buy'] != '0' or balances['after_sale'] != '0' or balances['after_buy2'] != balances['before_sale']:
            raise ValueError('Sauce inventory not closed')
        costs = [-int(x) for x in item['buy_native_net_wallet_deltas_wei']]
        cost, sale = sum(costs), int(item['native_sale_net_wallet_delta_wei'])
        if any(x <= 0 for x in costs) or sale < 0 or cost != int(item['net_cost_wei']) or sale - cost != int(item['net_gain_wei']):
            raise ValueError('Sauce cashflow inconsistent')
        for tx in [*item['buy_tx_hashes'], item['sell_tx'], item['sell_approval_same_block_tx']]:
            if not re.fullmatch(r'0x[0-9a-fA-F]{64}', tx):
                raise ValueError('Missing sauce tx hash')
        net = sale - cost
        entries.append({'row': row, 'wallet': item['wallet'], 'chain': 'bnb-mainnet',
                        'token': item['token'], 'symbol': sauce['token']['symbol'],
                        'buy_native_wei': str(cost), 'sell_native_wei': str(sale),
                        'realized_wei': str(net), 'classification': 'GAIN' if net > 0 else 'LOSS' if net < 0 else 'FLAT',
                        'precision': 'INTEGER_WEI_SOURCE_REPLAY', 'wallet_pnl': 'UNRESOLVED',
                        'evidence': 'evidence/batch-001-rows-002-004-sauce-roundtrips.json'})
    entries.sort(key=lambda v: v['row'])
    return {'schema': 'mission-closed-token-source-replay-v1', 'status': 'SOURCE_REPLAY_ONLY',
            'source_blob_sha': SOURCE, 'entries': entries, 'closed_token_positions': len(entries),
            'positive_positions': sum(v['classification'] == 'GAIN' for v in entries),
            'negative_positions': sum(v['classification'] == 'LOSS' for v in entries),
            'complete_wallet_30d_pnl': 0, 'complete_wallet_lifetime_pnl': 0,
            'note': 'Replays saved input assertions only. No independent onchain verification, no wallet ranking.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for arg in ('manifest', 'rtx', 'sauce'):
        ap.add_argument('--' + arg, type=Path, required=True)
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    sources = [json.loads(getattr(a, k).read_text(encoding='utf-8')) for k in ('manifest', 'rtx', 'sauce')]
    result = index_sources(*sources)
    output = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if a.output:
        a.output.write_text(output, encoding='utf-8')
    else:
        print(output, end='')


if __name__ == '__main__':
    main()
