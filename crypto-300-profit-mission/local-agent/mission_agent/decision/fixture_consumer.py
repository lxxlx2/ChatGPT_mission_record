"""Explicit fixture labels only; no real GPT call or investment classifier."""
from ..hashing import canonical, verify, digest
from ..clock import parse_utc, stamp
from ..models import DECISIONS


def consume(batch,clock):
    verify(batch)
    if len(canonical(batch))>100_000 or type(batch['schema_version']) is not int or batch['schema_version']!=1:
        raise ValueError('invalid batch size/schema')
    if clock.now()>parse_utc(batch['valid_until']):
        raise ValueError('stale batch')
    items=batch['items']
    if type(batch['item_count']) is not int or batch['item_count']!=len(items) or len({x['event_id'] for x in items})!=len(items):
        raise ValueError('batch membership mismatch')
    if sum(x['priority']==0 for x in items)>40 or sum(x['priority']==1 for x in items)>8:
        raise ValueError('batch count limits')
    decisions=[]
    for item in items:
        if len(canonical(item))>2000 or item['source']!='synthetic':
            raise ValueError('invalid synthetic item scope/size')
        if digest(item['payload'])!=item['payload_sha256']:
            raise ValueError('item hash mismatch')
        result=item['payload'].get('fixture_decision','IGNORE')
        if result not in DECISIONS:
            raise ValueError('unknown fixture label')
        decisions.append({'event_id':item['event_id'],'item_payload_sha256':item['payload_sha256'],
                          'decision':result,'reason':{'fixture':True}})
    return {'schema_version':1,'input_batch_id':batch['batch_id'],'input_payload_sha256':batch['payload_sha256'],
            'consumed_item_count':len(items),'decision_count':len(decisions),'consumer_version':'fixture-v1',
            'decision_timestamp':stamp(clock.now()),'decisions':decisions}
