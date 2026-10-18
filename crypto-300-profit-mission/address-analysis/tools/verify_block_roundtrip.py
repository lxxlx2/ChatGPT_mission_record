"""Verify saved event-filter and historical balance evidence; never certify wallet PnL."""
import argparse
import json
from pathlib import Path
import re

SRC = '954f3aba66be21911dd627fa40dd3dd0a9fd1d26'
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ADDRESS = re.compile(r'0x[0-9a-fA-F]{40}\Z')
TX = re.compile(r'0x[0-9a-fA-F]{64}\Z')
HEIGHTS = ['0x6f9e4de', '0x6f9e4df', '0x6f9e4e0', '0x6f9e4e1', '0x7a0db97', '0x7a0db98']
EVENT_HEIGHTS = [HEIGHTS[1], HEIGHTS[3], HEIGHTS[5], HEIGHTS[5]]


def _valid_record(r, token):
    row, wallet = r['source_row'], r['wallet'].lower()
    if row not in (2, 4) or not ADDRESS.fullmatch(wallet):
        raise ValueError('unexpected source row/wallet')
    hashes = r['buy_tx_hashes'] + [r['sell_tx_hash']]
    if len(hashes) != 3 or len(set(hashes)) != 3 or not all(TX.fullmatch(h) for h in hashes):
        raise ValueError('invalid or duplicated transaction hashes')
    snapshots = r['balance_snapshots']
    if len(snapshots) != 6 or [s['block'] for s in snapshots] != HEIGHTS:
        raise ValueError('historical block boundaries changed')
    nonces = [s['nonce'] for s in snapshots]
    if any(type(n) is not int or n < 0 for n in nonces) or [nonces[1]-nonces[0],nonces[3]-nonces[2],nonces[5]-nonces[4]] != [1,1,2]:
        raise ValueError('wallet signed nonce cannot explain observed blocks')
    b = [int(s['native_balance_wei']) for s in snapshots]
    if any(x < 0 for x in b) or b[2] != b[1]:
        raise ValueError('native balance evidence mismatch')
    tokens = [s['token_raw'] for s in snapshots]
    if tokens[0] != '0' or tokens[2] is not None or tokens[5] != '0' or tokens[3] != tokens[4]:
        raise ValueError('token balance snapshots not closed')
    logs = r['transfer_logs']
    if len(logs) != 4 or r['reverse_direction_logs_per_relevant_block'] != 0:
        raise ValueError('missing/surplus token logs or reverse-direction check')
    quantities = []
    for i, log in enumerate(logs):
        if log['block'] != EVENT_HEIGHTS[i] or log['transactionHash'].lower() != hashes[min(i,2)].lower():
            raise ValueError('transaction-to-log provenance mismatch')
        if log['contract'].lower() != token or log['topic0'].lower() != TRANSFER:
            raise ValueError('token contract / Transfer signature mismatch')
        if not TX.fullmatch(log['topic1']) or not TX.fullmatch(log['topic2']) or not TX.fullmatch(log['data']):
            raise ValueError('invalid indexed addresses / data')
        src='0x'+log['topic1'][-40:].lower()
        dest='0x'+log['topic2'][-40:].lower()
        if (i < 2 and (dest != wallet or src == wallet)) or (i >= 2 and (src != wallet or dest == wallet)):
            raise ValueError('wallet direction does not match transfer log')
        q=int(log['data'],16)
        if q <= 0:
            raise ValueError('zero token transfer')
        quantities.append(q)
    buy_total=quantities[0]+quantities[1]
    sell_total=quantities[2]+quantities[3]
    if buy_total != sell_total or quantities[0] != int(tokens[1]) or buy_total != int(tokens[3]):
        raise ValueError('token balance does not reconcile to indexed event logs')
    native_deltas=[b[1]-b[0],b[3]-b[2],b[5]-b[4]]
    if native_deltas[0]>=0 or native_deltas[1]>=0 or native_deltas[2]<=0:
        raise ValueError('unexpected native block cashflow direction')
    if [str(x) for x in native_deltas[:2]] != r['buy_block_native_deltas_wei'] or str(native_deltas[2]) != r['sale_block_native_delta_wei']:
        raise ValueError('block cashflow evidence mismatch')
    observed=sum(native_deltas)
    if str(observed) != r['observed_native_block_net_wei']:
        raise ValueError('observed cashflow arithmetic mismatch')
    return {'source_row':row,'wallet':wallet,'token_bought_raw':str(buy_total),
            'token_sold_raw':str(sell_total),'observed_native_block_net_wei':str(observed),
            'token_event_and_historical_balance_status':'SAVED_EVIDENCE_ARITHMETIC_MATCH',
            'transaction_native_attribution':'UNRESOLVED_WITHOUT_INTERNAL_TRACE',
            'wallet_30d_pnl':'UNRESOLVED','wallet_lifetime_pnl':'UNRESOLVED'}


def audit(data, manifest):
    try:
        if data['schema'] != 'mission-sauce-rows-002-004-narrow-erc20-and-native-block-proof-v1' or data['original_source_blob_sha'] != SRC:
            raise ValueError('wrong evidence source')
        if manifest.get('source_blob_sha') != SRC or manifest.get('total') != 449 or len(manifest.get('items',[])) != 449:
            raise ValueError('wrong original manifest')
        items=manifest['items']
        if any(x.get('index')!=i or x.get('batch')!=(i-1)//20+1 or not ADDRESS.fullmatch(x.get('address','')) for i,x in enumerate(items,1)):
            raise ValueError('manifest order or batch changed')
        if len(set(x['address'].lower() for x in items))!=449:
            raise ValueError('duplicated source addresses')
        token=data['token_contract'].lower()
        if not ADDRESS.fullmatch(token) or len(data['records']) != 2:
            raise ValueError('unsupported token/roundtrip count')
        seen=set()
        results=[]
        for r in data['records']:
            n=r['source_row']
            if n in seen or n not in (2,4) or r['wallet'].lower()!=items[n-1]['address'].lower():
                raise ValueError('duplicate row or source wallet mismatch')
            seen.add(n)
            results.append(_valid_record(r,token))
        if seen!={2,4}:
            raise ValueError('missing wallet')
        return {'schema':'mission-sauce-block-cashflow-audit-v1','status':'SAVED_CHAIN_EVIDENCE_REPLAY',
                'records':results,'full_receipt_status':'TRUNCATED_NOT_AVAILABLE',
                'wallet_pnl_status':'UNRESOLVED',
                'note':'Logs, native block balance and nonce assertions replayed; does not independently fetch chain or attribute native sale proceeds by trace.'}
    except (KeyError, ValueError, TypeError, IndexError) as exc:
        return {'schema':'mission-sauce-block-cashflow-audit-v1','status':'PNL_UNRESOLVED',
                'reason':str(exc),'records':[],'wallet_pnl_status':'UNRESOLVED'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',required=True,type=Path)
    p.add_argument('--evidence',required=True,type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    result=audit(json.loads(a.evidence.read_text()),json.loads(a.manifest.read_text()))
    out=json.dumps(result,indent=2)+'\n'
    if a.output:a.output.write_text(out)
    else:print(out,end='')
    if result['status']!='SAVED_CHAIN_EVIDENCE_REPLAY':raise SystemExit(3)

if __name__=='__main__':main()
