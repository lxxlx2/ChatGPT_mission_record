#!/usr/bin/env python3
"""Conservation-only read of a sourced distributor graph. Not a cost allocator."""
import argparse
import json
from pathlib import Path
import re

MANIFEST_SHA = '954f3aba66be21911dd627fa40dd3dd0a9fd1d26'
ADDR = re.compile(r'0x[0-9a-fA-F]{40}\Z')
HASH = re.compile(r'0x[0-9a-fA-F]{64}\Z')


def dec(value):
    if not isinstance(value, str) or not re.fullmatch(r'(?:0|[1-9][0-9]*)', value):
        raise ValueError('invalid nonnegative integer amount')
    return int(value)


def audit(lineage, manifest):
    try:
        if lineage['schema'] != 'mission-bsc-hodl-funded-distributor-lineage-v1' or lineage['frozen_manifest_blob_sha'] != MANIFEST_SHA:
            raise ValueError('unapproved lineage schema/source')
        if manifest['source_blob_sha'] != MANIFEST_SHA or manifest['total'] != 449:
            raise ValueError('wrong original manifest')
        rows = manifest['items']
        if len(rows) != 449 or any(item['index'] != i or item['batch'] != (i-1)//20+1 or not ADDR.fullmatch(item['address']) for i,item in enumerate(rows,1)):
            raise ValueError('source roster order invalid')
        if len({x['address'].lower() for x in rows}) != 449:
            raise ValueError('duplicate source address')
        distributor = lineage['upstream']
        if lineage['chain'] != 'bnb-mainnet' or not ADDR.fullmatch(lineage['token_contract']) or not ADDR.fullmatch(distributor['wallet']):
            raise ValueError('invalid network/contract/wallet')
        buys = distributor['funding_buys']
        if not buys or len({b['hash'].lower() for b in buys}) != len(buys) or not all(HASH.fullmatch(b['hash']) for b in buys):
            raise ValueError('missing or duplicated source buy')
        prior_tokens = 0
        native_value = 0
        native_outflow = 0
        for buy in buys:
            if dec(buy['token_before_raw']) != prior_tokens or dec(buy['token_after_raw']) <= prior_tokens:
                raise ValueError('source inventory discontinuity')
            if buy['sender_nonce_after'] - buy['sender_nonce_before'] != 1:
                raise ValueError('source buy signed nonce mismatch')
            raw_paid = dec(buy['native_input_wei'])
            spent = dec(buy['native_wallet_before_wei']) - dec(buy['native_wallet_after_wei'])
            if spent < raw_paid:
                raise ValueError('source buy BNB block spend smaller than native tx value')
            native_value += raw_paid
            native_outflow += spent
            prior_tokens = dec(buy['token_after_raw'])
        recipients = distributor['recipients']
        if not recipients or not HASH.fullmatch(distributor['distribution_tx']):
            raise ValueError('missing distributor transfer')
        seen = set()
        total_distributed = 0
        for recipient in recipients:
            a = recipient['address'].lower()
            if not ADDR.fullmatch(a) or a in seen or a == distributor['wallet'].lower():
                raise ValueError('invalid/duplicate recipient')
            seen.add(a)
            n = next((x['index'] for x in rows if x['address'].lower() == a), None)
            if recipient['source_row'] != n or recipient['source_transaction_hash'].lower() != distributor['distribution_tx'].lower():
                raise ValueError('recipient provenance/roster mismatch')
            total_distributed += dec(recipient['amount_raw'])
        residual = prior_tokens - total_distributed
        if residual < 0 or prior_tokens != dec(distributor['bought_token_raw']) or residual != dec(distributor['remaining_token_raw']) or residual != dec(distributor['post_distribution_balance_raw']):
            raise ValueError('source group conservation mismatch')
        if native_value != dec(distributor['buy_total_native_transaction_value_wei']) or native_outflow != dec(distributor['buy_block_wallet_native_outflow_wei']):
            raise ValueError('source native purchase mismatch')
        result = []
        for label, item in lineage['source_wallet_exits'].items():
            row = int(label)
            if row < 1 or row > 449 or item['wallet'].lower() != rows[row-1]['address'].lower():
                raise ValueError('exit source identity mismatch')
            recipient = next((x for x in recipients if x['address'].lower() == item['wallet'].lower()), None)
            if recipient is None or recipient['source_row'] != row or dec(item['received']) != dec(recipient['amount_raw']):
                raise ValueError('exit not funded by this distribution')
            exits = item['transfers']
            if not exits or len({t['hash'].lower() for t in exits}) != len(exits) or not all(HASH.fullmatch(t['hash']) for t in exits):
                raise ValueError('missing/duplicate exit tx')
            balance = dec(item['received']) - sum(dec(t['amount_raw']) for t in exits)
            if balance < 0 or str(balance) != item['closing_raw']:
                raise ValueError('exit token amount mismatch')
            result.append({'row': row, 'token_received_raw': item['received'], 'remaining_raw': str(balance),
                           'economic_cost_basis': 'UNRESOLVED', 'transaction_native_proceeds': 'UNRESOLVED',
                           'wallet_pnl': 'UNRESOLVED'})
        return {'schema': 'mission-capital-lineage-gate-v1', 'status': 'GROUP_TRANSFER_CONSERVATION_ONLY',
                'source_cost_pool_native_tx_value_wei': str(native_value),
                'source_group_tokens_distributed_raw': str(total_distributed), 'source_tokens_held_raw': str(residual),
                'recipient_rows': sorted(result, key=lambda v: v['row']),
                'cost_basis_allocation': 'BLOCKED_NO_ECONOMIC_OWNERSHIP_PROOF',
                'wallet_30d_pnl': 'UNRESOLVED', 'wallet_lifetime_pnl': 'UNRESOLVED'}
    except (ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        return {'schema': 'mission-capital-lineage-gate-v1', 'status': 'PNL_UNRESOLVED', 'reason': str(exc),
                'recipient_rows': [], 'cost_basis_allocation': 'BLOCKED'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--lineage', type=Path, required=True)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    result = audit(json.loads(a.lineage.read_text()), json.loads(a.manifest.read_text()))
    output = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if a.output: a.output.write_text(output)
    else: print(output, end='')
    if result['status'] != 'GROUP_TRANSFER_CONSERVATION_ONLY': raise SystemExit(3)


if __name__ == '__main__': main()
