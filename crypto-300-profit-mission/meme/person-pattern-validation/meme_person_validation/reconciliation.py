"""Validate lossless indexer imports against raw cached chain records and inventory assertions."""
from decimal import Decimal
from collections import defaultdict
import hashlib,json
class EvidenceError(ValueError): pass
def import_events(path,graph,raw_transactions):
    bundle=json.loads(path.read_text());raw=dict(raw_transactions);out=[]
    for e in bundle.get('events',[]):
        tx=raw.get(e['signature'])
        if tx is None or tx.get('meta',{}).get('err') or e['slot']!=tx.get('slot') or e['block_time']!=tx.get('blockTime'): raise EvidenceError('INDEXER_EVENT_NOT_MATCHED_TO_FINALIZED_RAW_TRANSACTION')
        if not graph.accepts_at(e['wallet'],e['block_time']): raise EvidenceError('INDEXER_WALLET_NOT_ACCEPTED')
        if e.get('verified_swap'):
            required=['route_id','route_evidence','mint','quote_mint','token_delta','quote_delta','source_token_account','destination_token_account','usd_notional','usd_price_evidence']
            if any(e.get(k) is None for k in required): raise EvidenceError('LOSSLESS_SWAP_EVIDENCE_INCOMPLETE')
            if Decimal(str(e['usd_notional']))<=0: raise EvidenceError('INVALID_USD_NOTIONAL')
            message=tx['transaction']['message']; keys={k['pubkey'] if isinstance(k,dict) else k for k in message['accountKeys']}
            if not {e['source_token_account'],e['destination_token_account']}.issubset(keys): raise EvidenceError('SWAP_ACCOUNTS_NOT_IN_RAW_TRANSACTION')
        out.append(e)
    return out,bundle.get('inventory_assertions',[]),hashlib.sha256(path.read_bytes()).hexdigest()
def reconcile(events,assertions):
    inventory=defaultdict(Decimal);unknown=set()
    for e in sorted(events,key=lambda e:(e['block_time'],e.get('slot',0),e['event_id'])):
        mint=e.get('mint')
        if not mint: continue
        if e['event_type'] in {'MARKET_BUY','MARKET_SELL'}: inventory[mint]+=Decimal(str(e['token_delta']))
        elif e['event_type'] not in {'INTERNAL_TRANSFER','FEE','ATA_CREATE','PLATFORM_INFRA'}: unknown.add(mint)
    checked={}
    for a in assertions:
        # Assertions must be attached to a historical finalized owner inventory export.
        if not a.get('evidence_id') or not a.get('complete_owner_inventory') or a.get('initial_quantity')!='0': continue
        mint=a['mint'];checked[mint]=mint not in unknown and inventory[mint]==Decimal(a['final_quantity'])
    return checked
