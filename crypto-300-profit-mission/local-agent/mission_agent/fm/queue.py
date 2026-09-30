from ..hashing import canonical,digest,verify
from ..clock import stamp,parse_utc
from ..db.connection import transaction
from ..storage import admit

SCOPES={'RAW_FRANK_CANDIDATE':('frank:','solana_official_rpc'),'RAW_MONSTER_CANDIDATE':('monster:','binance_official')}

def ingest(repo,value):
    verify(value)
    kind=value.get('event_type')
    if kind not in SCOPES:raise ValueError('FM_EVENT_TYPE')
    prefix,source=SCOPES[kind]
    if not value['event_id'].startswith(prefix) or value.get('source')!=source:raise ValueError('FM_SOURCE_NAMESPACE')
    observed=stamp(parse_utc(value['observed_at']));now=stamp(repo.clock.now());data=canonical(value);sha=digest(value)
    item={'schema_version':1,'event_id':value['event_id'],'event_type':kind,'source':source,'asset':value.get('asset'),'observed_at_utc':observed,'created_at_utc':now,'priority':0,'payload':value,'payload_sha256':sha}
    if len(canonical(item))>2000:raise ValueError('FM_ITEM_OVER_2KB')
    with transaction(repo.db):
        old=repo.db.execute('SELECT payload_sha256 FROM candidates WHERE event_id=?',(value['event_id'],)).fetchone()
        if old:
            if old[0]!=sha:raise ValueError('FM_EVENT_ID_CONFLICT')
            return 'DUPLICATE'
        admit(repo.path.parent,len(data)+65536,repo.disk_budget_bytes)
        repo.db.execute('INSERT INTO candidates VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(value['event_id'],kind,source,value.get('asset'),observed,now,1,0,data.decode(),sha,'PENDING_DECISION',now))
        repo.db.execute("INSERT INTO outbox(event_id,state,created_at,updated_at) VALUES(?,'PENDING',?,?)",(value['event_id'],now,now))
        repo.db.execute("INSERT INTO deliveries(event_id,policy,state,updated_at) VALUES(?,?,'PENDING_DECISION',?)",(value['event_id'],repo.policy,now))
    return 'INSERTED'

def validate_shadow_batch(batch):
    """Schema-only offline consumer; no synthesized GPT investment decision."""
    verify(batch)
    if len(canonical(batch))>75000 or batch['item_count']!=len(batch['items']):raise ValueError('FM_BATCH_CONTRACT')
    if len({x['event_id'] for x in batch['items']})!=len(batch['items']):raise ValueError('FM_BATCH_DUPLICATE')
    for item in batch['items']:
        p=item['payload'];verify(p)
        if item['event_type'] not in SCOPES or item['source']!=SCOPES[item['event_type']][1] or p['event_id']!=item['event_id'] or p['event_type']!=item['event_type'] or p['source']!=item['source'] or digest(p)!=item['payload_sha256']:raise ValueError('FM_ITEM_IDENTITY')
        if len(canonical(item))>2000:raise ValueError('FM_ITEM_OVER_2KB')
    return {'schema_only':True,'items_verified':len(batch['items']),'decision_generated':False,'delivery_generated':False}
