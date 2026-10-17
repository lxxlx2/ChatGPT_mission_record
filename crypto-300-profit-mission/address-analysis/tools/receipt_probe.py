#!/usr/bin/env python3
"""Read-only EVM receipt facts, never a wallet PnL or swap-execution claim."""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

SOURCE = '954f3aba66be21911dd627fa40dd3dd0a9fd1d26'
CHAINS = {'bnb-mainnet': 56, 'eth-mainnet': 1, 'base-mainnet': 8453}
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
APPROVAL = '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925'
ADDR = re.compile(r'0x[a-fA-F0-9]{40}\Z')
HASH = re.compile(r'0x[a-fA-F0-9]{64}\Z')


def hex_int(value, label):
    if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]+', value):
        raise ValueError(f'invalid {label}')
    return int(value, 16)


def assert_address(value):
    if not isinstance(value, str) or not ADDR.fullmatch(value):
        raise ValueError('invalid EVM address')
    return value.lower()


def normalized_wallet(manifest, row):
    if manifest.get('source_blob_sha') != SOURCE or manifest.get('total') != 449:
        raise ValueError('wrong frozen source')
    items = manifest.get('items', [])
    if len(items) != 449 or type(row) is not int or row < 1 or row > 449:
        raise ValueError('invalid source row')
    if any(item.get('index') != i or item.get('batch') != (i-1)//20+1 or not ADDR.fullmatch(item.get('address','')) for i,item in enumerate(items,1)):
        raise ValueError('source order mismatch')
    if len({x['address'].lower() for x in items}) != 449:
        raise ValueError('duplicate addresses')
    return items[row-1]['address'].lower()


def inspect_receipt(tx, receipt, wallet, network):
    try:
        wallet = assert_address(wallet)
        if network not in CHAINS or hex_int(tx['chainId'], 'chainId') != CHAINS[network]:
            raise ValueError('wrong chain')
        h = tx['hash'].lower()
        if not HASH.fullmatch(h) or receipt['transactionHash'].lower() != h:
            raise ValueError('transaction hash mismatch')
        sender = assert_address(tx['from'])
        if sender != wallet or assert_address(receipt['from']) != wallet:
            raise ValueError('wallet not transaction sender')
        tx_to = assert_address(tx['to']) if tx.get('to') is not None else None
        receipt_to = assert_address(receipt['to']) if receipt.get('to') is not None else None
        if tx_to != receipt_to:
            raise ValueError('transaction destination mismatch')
        if tx['blockHash'].lower() != receipt['blockHash'].lower() or hex_int(tx['blockNumber'], 'block number') != hex_int(receipt['blockNumber'], 'receipt block'):
            raise ValueError('block identity mismatch')
        if hex_int(receipt['status'], 'receipt status') != 1:
            raise ValueError('failed or unknown execution')
        gas_used = hex_int(receipt['gasUsed'], 'gasUsed')
        price = hex_int(receipt.get('effectiveGasPrice', tx.get('gasPrice')), 'gas price')
        if gas_used == 0 or price == 0:
            raise ValueError('incomplete gas evidence')
        native_value = hex_int(tx['value'], 'transaction value')
        selector = tx.get('input', '')[:10].lower()
        if not isinstance(tx.get('input'), str) or not tx['input'].startswith('0x'):
            raise ValueError('invalid calldata')
        balances = defaultdict(lambda: {'incoming':0,'outgoing':0})
        transfers = []
        approvals = 0
        for log in receipt['logs']:
            if not isinstance(log,dict) or log.get('transactionHash','').lower() != h:
                raise ValueError('unrelated/malformed log')
            contract = assert_address(log['address'])
            topics = log.get('topics')
            if not isinstance(topics, list) or not topics:
                raise ValueError('malformed topics')
            sig = topics[0].lower()
            if sig == APPROVAL:
                approvals += 1
            if sig != TRANSFER:
                continue
            if len(topics) != 3 or any(not HASH.fullmatch(t) for t in topics[:3]):
                raise ValueError('nonstandard ERC20 transfer log requires review')
            if not isinstance(log.get('data'),str) or not HASH.fullmatch(log['data']):
                raise ValueError('nonstandard transfer amount')
            frm = '0x'+topics[1][-40:].lower()
            to = '0x'+topics[2][-40:].lower()
            qty = hex_int(log['data'], 'token transfer quantity')
            transfers.append({'token':contract,'from':frm,'to':to,'raw_amount':str(qty)})
            if frm == wallet: balances[contract]['outgoing'] += qty
            if to == wallet: balances[contract]['incoming'] += qty
        net_flows = {token:{'incoming_raw':str(x['incoming']),'outgoing_raw':str(x['outgoing']),
                            'net_raw':str(x['incoming']-x['outgoing'])} for token,x in balances.items()}
        if selector == '0x095ea7b3':
            classification = 'APPROVAL_NOT_TRADE'
        elif selector == '0xa9059cbb':
            classification = 'ERC20_TRANSFER_NOT_TRADE_PROVEN'
        elif tx['input'] == '0x' and native_value > 0:
            classification = 'NATIVE_TRANSFER_NOT_TRADE_PROVEN'
        else:
            classification = 'CONTRACT_EXECUTION_UNRESOLVED'
        return {'schema':'mission-receipt-facts-v1','status':'RECEIPT_FACTS_ONLY',
                'network':network,'tx_hash':h,'sender':wallet,'block':hex_int(tx['blockNumber'], 'block'),
                'method':selector,'classification':classification,'native_sent_wei':str(native_value),
                'gas_cost_native_wei':str(gas_used*price),'gas_used':str(gas_used),
                'effective_gas_price_wei':str(price),'erc20_flows':net_flows,
                'erc20_transfers':transfers,'approval_log_count':approvals,
                'native_incoming_wei':'UNRESOLVED_INTERNAL_TRACE',
                'trade_execution':'UNRESOLVED','wallet_30d_pnl':'UNRESOLVED',
                'warning':'Receipt logs prove ERC20 Transfer events, not acquisition cost, native internal proceeds, or entire wallet PnL.'}
    except (TypeError,KeyError,ValueError,AttributeError) as exc:
        return {'schema':'mission-receipt-facts-v1','status':'PNL_UNRESOLVED','reason':str(exc),
                'trade_execution':'UNRESOLVED','wallet_30d_pnl':'UNRESOLVED'}


def rpc(url, method, params):
    if not url.startswith('https://'):
        raise ValueError('only HTTPS read-only RPC endpoints supported')
    body = json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode('utf-8')
    with urlopen(Request(url,data=body,headers={'Content-Type':'application/json'},method='POST'),timeout=20) as response:
        result = json.load(response)
    if 'error' in result or not isinstance(result.get('result'),dict):
        raise ValueError('RPC result unavailable')
    return result['result']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--row',type=int,required=True)
    parser.add_argument('--network',choices=sorted(CHAINS),required=True)
    parser.add_argument('--tx-hash',required=True)
    parser.add_argument('--tx-file',type=Path)
    parser.add_argument('--receipt-file',type=Path)
    parser.add_argument('--rpc-env',help='Name of environment variable holding a HTTPS JSON RPC URL')
    parser.add_argument('--output',type=Path)
    a=parser.parse_args()
    if not HASH.fullmatch(a.tx_hash) or bool(a.rpc_env) == bool(a.tx_file or a.receipt_file) or bool(a.tx_file) != bool(a.receipt_file):
        parser.error('Provide either --rpc-env or both --tx-file and --receipt-file')
    try:
        wallet=normalized_wallet(json.loads(a.manifest.read_text()),a.row)
        if a.rpc_env:
            url=os.environ.get(a.rpc_env)
            if not url: raise ValueError('RPC environment variable unset')
            tx=rpc(url,'eth_getTransactionByHash',[a.tx_hash])
            receipt=rpc(url,'eth_getTransactionReceipt',[a.tx_hash])
        else:
            tx=json.loads(a.tx_file.read_text())
            receipt=json.loads(a.receipt_file.read_text())
        result=inspect_receipt(tx,receipt,wallet,a.network)
    except (OSError,ValueError,TypeError,KeyError) as exc:
        result={'schema':'mission-receipt-facts-v1','status':'PNL_UNRESOLVED','reason':str(exc)}
    result['source_row']=a.row
    result['source_blob_sha']=SOURCE
    result['source_kind']='DIRECT_RPC_READONLY' if a.rpc_env else 'OFFLINE_PROVIDED_RECEIPT'
    content=json.dumps(result,indent=2)+'\n'
    if a.output: a.output.write_text(content)
    else: print(content,end='')
    if result['status']!='RECEIPT_FACTS_ONLY':raise SystemExit(3)


if __name__=='__main__':main()
