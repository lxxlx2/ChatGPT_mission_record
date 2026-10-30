#!/usr/bin/env python3
"""Validate archived ERC20 wallet flow evidence, never infer purchase cost or PnL."""
import argparse
import json
from pathlib import Path
import re

SOURCE = '954f3aba66be21911dd627fa40dd3dd0a9fd1d26'
ADDRESS = re.compile(r'0x[0-9a-fA-F]{40}\Z')
HASH = re.compile(r'0x[0-9a-fA-F]{64}\Z')


def validate(source, evidence):
    try:
        items = source['items']
        if source['source_blob_sha'] != SOURCE or source['total'] != 449 or len(items) != 449:
            raise ValueError('source manifest mismatch')
        if any(x['index'] != i or x['batch'] != (i-1)//20+1 or not ADDRESS.fullmatch(x['address']) for i, x in enumerate(items, 1)):
            raise ValueError('source order or address mismatch')
        if len({x['address'].lower() for x in items}) != 449:
            raise ValueError('source duplicate')
        if evidence['schema'] != 'mission-address-analysis-batch001-three-pending-erc20-provenance-v1' or evidence['immutable_source_blob'] != SOURCE:
            raise ValueError('evidence source mismatch')
        if evidence['network'] != 'bnb-mainnet' or evidence['bound']['fromBlock'] != '0x0' or evidence['bound']['toBlock'] != '0x7a4ca36':
            raise ValueError('network/window mismatch')
        observed = set()
        checked = []
        for case in evidence['cases']:
            row = case['source_row']
            if type(row) is not int or row not in (2, 7, 15) or row in observed or case['wallet'].lower() != items[row-1]['address'].lower():
                raise ValueError('wallet row identity mismatch')
            observed.add(row)
            wallet = case['wallet'].lower()
            token = case['token_contract'].lower()
            if not ADDRESS.fullmatch(token) or case['network'] != 'bnb-mainnet':
                raise ValueError('invalid token/chain')
            flow = case['transfer_inventory']
            if flow['alchemy_erc20_pagination_complete_inbound'] is not True or flow['alchemy_erc20_pagination_complete_outbound'] is not True:
                raise ValueError('missing ERC20 transfer page(s)')
            def scan(events, inbound):
                total = 0
                last_block = -1
                for t in events:
                    if t['token_contract'].lower() != token or not HASH.fullmatch(t['hash']):
                        raise ValueError('transfer identity mismatch')
                    if t['from'].lower() == t['to'].lower() or not ADDRESS.fullmatch(t['from']) or not ADDRESS.fullmatch(t['to']):
                        raise ValueError('invalid transfer endpoints')
                    wrong_end = (t['to'].lower() != wallet) if inbound else (t['from'].lower() != wallet)
                    if wrong_end:
                        raise ValueError('transfer direction mismatch')
                    block = int(t['block'], 16)
                    if block < last_block or block > int(evidence['bound']['toBlock'], 16):
                        raise ValueError('transfer out of window or unordered')
                    last_block = block
                    amount = t['raw_amount']
                    if type(amount) is not str or not amount.isdecimal() or int(amount) <= 0:
                        raise ValueError('nonpositive or malformed token quantity')
                    total += int(amount)
                    if not inbound:
                        match = next((i['index'] for i in items if i['address'].lower() == t['to'].lower()), None)
                        if t['destination_original_source_row'] != match:
                            raise ValueError('invented wallet association')
                return total
            incoming = scan(flow['inbound_events'], True)
            outgoing = scan(flow['outbound_events'], False)
            if str(incoming) != flow['total_in_raw'] or str(outgoing) != flow['total_out_raw'] or flow['opening_token_raw'] != '0':
                raise ValueError('source transfer totals mismatch')
            ending = incoming - outgoing
            if ending < 0 or str(ending) != flow['ending_token_raw']:
                raise ValueError('unmatched token inventory')
            snapshots = case['historical_balance_snapshots']
            if not snapshots or snapshots[0]['balance'] != '0' or int(snapshots[-1]['balance']) != ending:
                raise ValueError('historical token balance mismatch')
            if any(int(snapshots[i]['block'],16) >= int(snapshots[i+1]['block'],16) for i in range(len(snapshots)-1)):
                raise ValueError('out-of-order balance snapshots')
            for delta in case['native_block_deltas']:
                b = int(delta['at_block'], 16)
                found = next((i for i in range(1,len(snapshots)) if int(snapshots[i]['block'],16)==b and int(snapshots[i-1]['block'],16)==b-1), None)
                if found is None:
                    raise ValueError('native delta source missing')
                prev, cur = snapshots[found-1], snapshots[found]
                if str(int(cur['BNBWei'])-int(prev['BNBWei'])) != delta['block_level_delta_wei'] or cur['nonce']-prev['nonce'] != delta['signed_nonce_delta'] or str(int(cur['balance'])-int(prev['balance'])) != delta['token_delta_raw']:
                    raise ValueError('native block, nonce or token delta mismatch')
            checked.append({'source_row':row,'token_contract':token,'transfers_in':len(flow['inbound_events']),'transfers_out':len(flow['outbound_events']),
                            'incoming_raw':str(incoming),'outgoing_raw':str(outgoing),'ending_raw':str(ending),
                            'classification':case['accounting_classification'],'profit_or_loss':'UNRESOLVED'})
        if observed != {2, 7, 15}:
            raise ValueError('missing bounded cohort row')
        return {'schema':'mission-erc20-disposition-gate-v1','status':'ARCHIVED_FLOW_CONSISTENT_ONLY','records':checked,
                'wallet_30d_pnl':'UNRESOLVED','wallet_lifetime_pnl':'UNRESOLVED',
                'note':'Original transfer event provenance was asserted in archived RPC evidence. No verified basis, sale proceeds, or network-wide accounting.'}
    except (KeyError, ValueError, TypeError, IndexError, AttributeError) as exc:
        return {'schema':'mission-erc20-disposition-gate-v1','status':'PNL_UNRESOLVED','reason':str(exc),'records':[]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--evidence',type=Path,required=True)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    result=validate(json.loads(a.manifest.read_text()),json.loads(a.evidence.read_text()))
    body=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if a.output:a.output.write_text(body)
    else:print(body,end='')
    if result['status']!='ARCHIVED_FLOW_CONSISTENT_ONLY':raise SystemExit(3)


if __name__=='__main__':main()
