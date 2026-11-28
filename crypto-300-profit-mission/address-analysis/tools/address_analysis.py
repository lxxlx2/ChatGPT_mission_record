#!/usr/bin/env python3
"""Read-only, fixed-block EVM nonce census and audited closed-token cashflow replay.

No signing, no secret persistence, no live trading and no inferred wallet PnL.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SOURCE_BLOB = '954f3aba66be21911dd627fa40dd3dd0a9fd1d26'
NETWORKS = {
    'bsc': ('ADDR_ANALYSIS_RPC_BSC', 'bnb-mainnet'),
    'ethereum': ('ADDR_ANALYSIS_RPC_ETH', 'eth-mainnet'),
    'base': ('ADDR_ANALYSIS_RPC_BASE', 'base-mainnet'),
}
HEX_ADDR = re.compile(r'^0x[a-fA-F0-9]{40}$')


def assert_source(source):
    if source.get('source_blob_sha') != SOURCE_BLOB or source.get('total') != 449:
        raise ValueError('Wrong or unpinned source snapshot')
    items = source.get('items', [])
    if len(items) != 449 or len({r['address'].lower() for r in items}) != 449:
        raise ValueError('Source cardinality or duplication mismatch')
    if any(r.get('index') != i or r.get('batch') != (i - 1) // 20 + 1 or not HEX_ADDR.fullmatch(r['address'])
           for i, r in enumerate(items, start=1)):
        raise ValueError('Source ordering, batch, or address mismatch')
    return items


def read_json(path):
    with open(path, encoding='utf-8') as file:
        return json.load(file)


def rpc(url, method, params, retries=2):
    # Keep RPC URLs and their embedded API keys out of errors, reports, and logs.
    data = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode()
    for attempt in range(retries + 1):
        try:
            request = Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
            with urlopen(request, timeout=20) as res:
                payload = json.load(res)
            if 'error' in payload:
                raise ValueError('RPC returned an error')
            if 'result' not in payload:
                raise ValueError('RPC missing result')
            return payload['result']
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as ex:
            if attempt == retries:
                raise RuntimeError('RPC_READ_FAILED') from None
            time.sleep(min(2 ** attempt, 3))


def nonce_pair(url, addr, start, end, caller=rpc):
    lo = caller(url, 'eth_getTransactionCount', [addr, start])
    hi = caller(url, 'eth_getTransactionCount', [addr, end])
    if not all(isinstance(x, str) and re.fullmatch(r'0x[0-9a-fA-F]+', x) for x in (lo, hi)):
        raise ValueError('Invalid nonce RPC response')
    a, b = int(lo, 16), int(hi, 16)
    if b < a:
        raise ValueError('Nonce regression')
    return {'start_nonce': a, 'end_nonce': b, 'signed_delta': b - a}


def screen(source, windows, endpoints, batch, caller=rpc, max_workers=4):
    items = assert_source(source)
    if not 1 <= batch <= 23:
        raise ValueError('Batch index outside 1..23')
    selected = items[(batch - 1) * 20:batch * 20]
    if not selected or any(r['batch'] != batch for r in selected):
        raise ValueError('Malformed batch slice')
    blocks = {}
    for chain, url in endpoints.items():
        if chain not in NETWORKS or not url:
            raise ValueError('Unsupported/missing chain endpoint')
        w = windows[chain]
        start, end = w['from']['height'], w['to']['height']
        for side, height in [('from', start), ('to', end)]:
            raw = caller(url, 'eth_getBlockByNumber', [height, False])
            if not isinstance(raw, dict) or raw.get('hash', '').lower() != w[side]['hash'].lower() or raw.get('number', '').lower() != height.lower():
                raise ValueError('BOUNDARY_BLOCK_MISMATCH: '+chain+':'+side)
        blocks[chain] = {'start': start, 'end': end, 'start_hash': w['from']['hash'], 'end_hash': w['to']['hash']}
    rows = [{'source_row': r['index'], 'address': r['address'], 'networks': {}} for r in selected]
    jobs = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for ri, row in enumerate(rows):
            for chain, url in endpoints.items():
                w = blocks[chain]
                jobs[pool.submit(nonce_pair, url, row['address'], w['start'], w['end'], caller)] = (ri, chain)
        for future in as_completed(jobs):
            ri, chain = jobs[future]
            try:
                rows[ri]['networks'][chain] = {'status': 'OK', **future.result()}
            except (RuntimeError, ValueError):
                rows[ri]['networks'][chain] = {'status': 'UNRESOLVED_RPC', 'signed_delta': None}
    rows.sort(key=lambda x: x['source_row'])
    summary = {}
    for chain in endpoints:
        valid = [r['networks'][chain] for r in rows if r['networks'][chain]['status'] == 'OK']
        summary[chain] = {'checked': len(valid), 'rpc_unresolved': len(rows)-len(valid),
                          'signed_active': sum(r['signed_delta'] > 0 for r in valid),
                          'signed_tx_count': sum(r['signed_delta'] for r in valid)}
    full = [r for r in rows if all(r['networks'][c]['status'] == 'OK' for c in endpoints)]
    summary['union_active_proven'] = sum(any(r['networks'][c]['signed_delta'] > 0 for c in endpoints) for r in rows if any(r['networks'][c]['status'] == 'OK' for c in endpoints))
    summary['all_checked_chains_signed_zero'] = [r['source_row'] for r in full if not any(r['networks'][c]['signed_delta'] for c in endpoints)]
    summary['fully_checked_wallets'] = len(full)
    return {'schema': 'mission-address-analysis-readonly-nonce-screen-v1', 'source_blob_sha': SOURCE_BLOB,
            'batch': batch, 'source_rows': [selected[0]['index'], selected[-1]['index']],
            'status': 'PARTIAL' if len(full) != len(rows) else 'SCREENED_CHAINS_ONLY',
            'chains': blocks, 'rows': rows, 'summary': summary,
            'notice': 'Signed nonce activity is NOT swap classification, wallet PnL, or EVM-wide inactivity.'}


def replay_closed_token(item):
    """Replay native-chain cashflow in integer wei; no inferred basis, approvals, or missing credits."""
    required = ['balance_before', 'balance_after', 'basis_verified', 'receipt_success',
                'provenance_complete', 'buy_native_cost_wei', 'sell_native_net_wei', 'token_contract']
    if any(k not in item for k in required):
        return {'status': 'PNL_UNRESOLVED', 'reason': 'missing_required_evidence'}
    if item['balance_before'] != '0' or item['balance_after'] != '0' or not all(
        item[k] is True for k in ['basis_verified', 'receipt_success', 'provenance_complete']
    ) or not HEX_ADDR.fullmatch(item['token_contract']):
        return {'status': 'PNL_UNRESOLVED', 'reason': 'inventory_or_evidence_gap'}
    try:
        cost, proceeds = int(item['buy_native_cost_wei']), int(item['sell_native_net_wei'])
        if cost <= 0 or proceeds < 0:
            raise ValueError()
    except (ValueError, TypeError):
        return {'status': 'PNL_UNRESOLVED', 'reason': 'invalid_cashflow'}
    gain = proceeds - cost
    return {'status': 'TOKEN_CLOSED', 'classification': 'GAIN' if gain > 0 else 'LOSS' if gain < 0 else 'FLAT',
            'gain_wei': str(gain), 'roi_pct': str(Decimal(gain) * 100 / Decimal(cost))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--windows', required=True, type=Path, help='Frozen chain block hash/height JSON')
    parser.add_argument('--batch', type=int, required=True)
    parser.add_argument('--output', type=Path, help='Write result JSON; defaults to stdout')
    args = parser.parse_args()
    urls = {chain: os.environ[env] for chain, (env, _) in NETWORKS.items() if os.environ.get(env)}
    if not urls:
        parser.error('Set at least one ADDR_ANALYSIS_RPC_* environment variable')
    try:
        result = screen(read_json(args.source), read_json(args.windows), urls, args.batch)
    except (ValueError, KeyError, OSError, RuntimeError) as ex:
        print('Screen failed: '+str(ex), file=sys.stderr)
        sys.exit(2)
    content = json.dumps(result, indent=2, ensure_ascii=False)+'\n'
    if args.output:
        args.output.write_text(content, encoding='utf-8')
    else:
        print(content, end='')
    if result['status'] == 'PARTIAL':
        sys.exit(3)

if __name__ == '__main__':
    main()
