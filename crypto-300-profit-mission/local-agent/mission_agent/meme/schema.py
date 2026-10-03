"""Immutable V2 signal identities; null reasons rather than invented facts."""
from datetime import datetime, timezone
from decimal import Decimal
from ..hashing import seal, verify, digest, canonical

FAMILIES = {'TOKEN_CONSENSUS', 'PERSON_PATTERN'}
QUOTE_MINTS = {'So11111111111111111111111111111111111111112', 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'}

def iso(epoch): return datetime.fromtimestamp(float(epoch), timezone.utc).isoformat()
def epoch(value): return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
def missing(reason): return {'value': None, 'reason': reason}

def fact(evidence, observation, created_at, registry, mint, *, prior=(), source_batch_id=None):
    body = {k:v for k,v in evidence.items() if k != 'evidence_sha256'}
    if digest(body) != evidence['evidence_sha256']: raise ValueError('SOURCE_EVIDENCE_HASH')
    p = registry.person('solana', evidence['wallet'])
    if evidence['mechanical_classification'] != 'ACTIVE_SWAP_LIKE': return None
    if evidence['block_time'] is None:raise ValueError('EVENT_TIMESTAMP_UNAVAILABLE')
    ds = [d for d in evidence['token_balance_deltas'] if d['wallet_owned'] and d['mint'] == mint]
    raw = sum(int(d['delta']) for d in ds)
    if raw <= 0 or mint in QUOTE_MINTS: return None
    if not ds or len({d['decimals'] for d in ds}) != 1: raise ValueError('DECIMALS_AMBIGUOUS')
    earlier = [e for e in prior if e['wallet'] == evidence['wallet'] and e['block_time'] < evidence['block_time']]
    seen = [e for e in earlier if any(d['wallet_owned'] and d['mint'] == mint and int(d['delta']) for d in e['token_balance_deltas'])]
    had_zero = any(sum(int(d['post_amount']) for d in e['token_balance_deltas'] if d['wallet_owned'] and d['mint']==mint)==0 for e in seen)
    before = sum(int(d['pre_amount']) for d in ds)
    behavior = 'add' if before > 0 else 'reentry' if had_zero else 'first_entry' if not seen else 'other'
    groups={}
    for d in evidence['token_balance_deltas']:
        if d['wallet_owned']:
            item=groups.setdefault(d['mint'],{'asset':d['mint'],'raw':0,'decimals':d['decimals']})
            if item['decimals']!=d['decimals']:raise ValueError('DENOMINATED_DECIMALS_AMBIGUOUS')
            item['raw']+=int(d['delta'])
    debits=[{**d,'raw':str(-d['raw'])} for d in groups.values() if d['raw']<0]
    identity = {'namespace': registry.namespace, 'person_id': p['person_id'], 'wallet': evidence['wallet'], 'signature': evidence['signature'], 'mint': mint}
    return seal({'schema_version':2, 'namespace':registry.namespace, 'event_id':'meme:event:'+digest(identity), 'person_id':p['person_id'], 'person_display_name':p['display_name'], 'wallet':evidence['wallet'], 'chain':'solana', 'mint':mint, 'signature':evidence['signature'], 'finalized_slot':evidence['slot'], 'finalized_commitment':'finalized', 'event_at':iso(evidence['block_time']), 'detected_at':iso(observation['detected_at']), 'normalized_at':iso(observation['normalized_at']), 'candidate_created_at':created_at, 'source_batch_id':source_batch_id, 'unavailable_reasons':{'source_batch_id':'NO_LEGACY_BATCH_ASSIGNED' if source_batch_id is None else None}, 'buy_amount':{'raw':str(raw), 'decimals':ds[0]['decimals'], 'quantity':str(Decimal(raw)/(Decimal(10)**ds[0]['decimals'])), 'denominated_asset':mint}, 'debit_assets':debits, 'USD_estimate':missing('NO_CAUSAL_USD_MARK'), 'behavior_type':behavior, 'source_evidence_hash':evidence['evidence_sha256'], 'raw_transaction_hash':evidence['raw_transaction_sha256'], 'features':{'prior_observed_activity':len(seen),'prior_account_exposure_raw':str(before),'history_scope':'AVAILABLE_REFERENCED_ACCOUNTS_NOT_LIFETIME', 'lifetime_first_entry_proven':False, 'buy_size_percentile':missing('NO_COMPARABLE_CAUSAL_DENOMINATED_BUY_DISTRIBUTION'),'token_age':missing('NO_VERIFIED_MINT_CREATION_TIME'),'liquidity':missing('NO_CAUSAL_EXECUTABLE_QUOTE'),'market_cap':missing('NO_CAUSAL_SUPPLY_PRICE_SNAPSHOT'),'fill_to_detection_price_change':missing('NO_PRICE_TIME_SERIES'),'fill_to_candidate_price_change':missing('NO_PRICE_TIME_SERIES'),'followability':missing('NO_EXECUTABLE_DELAYED_ENTRY_PRICE'),'reason_codes':['MECHANICAL_ACTIVE_BUY','AVAILABLE_HISTORY_'+behavior.upper()]}})

def candidates(facts, registry, policy):
    ttl = policy['ttl']; window = policy['consensus_window_seconds']
    if ttl['status'] != 'TEMPORARY_SHADOW_TTL' or not 0 < ttl['value_seconds'] <= 3600: raise ValueError('TTL_PROVENANCE')
    valid = []
    for f in facts:
        verify(f)
        if f['schema_version'] != 2 or f['namespace'] != registry.namespace: raise ValueError('FACT_SCHEMA_NAMESPACE')
        if registry.person(f['chain'], f['wallet'])['person_id'] != f['person_id']: raise ValueError('PERSON_FACT_BINDING')
        valid.append(f)
    output = []
    def build(family, rows):
        rows = sorted({r['event_id']:r for r in rows}.values(), key=lambda r:(r['event_at'],r['event_id']))
        people = sorted({r['person_id'] for r in rows}); mint = rows[0]['mint']
        identity = {'schema_version':2,'namespace':registry.namespace,'family':family,'mint':mint,'event_ids':sorted(r['event_id'] for r in rows),'window_seconds':window if family=='TOKEN_CONSENSUS' else None}
        sid='meme:signal:'+digest(identity);first=min(epoch(r['event_at']) for r in rows);last=max(epoch(r['event_at']) for r in rows)
        return seal({'schema_version':2,'namespace':registry.namespace,'candidate_id':'meme:candidate:'+digest(identity),'signal_id':sid,'event_id':sid,'run_id':None,'source_batch_id':None,'signal_family_candidate':family,'person_id':people[0] if len(people)==1 else None,'person_ids':people,'unique_person_count':len(people),'source_wallets':sorted({r['wallet'] for r in rows}),'detected_at':min(r['detected_at'] for r in rows),'normalized_at':max(r['normalized_at'] for r in rows),'candidate_created_at':max(r['candidate_created_at'] for r in rows),'source_evidence_hashes':sorted({r['source_evidence_hash'] for r in rows}),'finalized_slots':sorted({r['finalized_slot'] for r in rows}),'chain':'solana','mint':mint,'tx_signatures':sorted({r['signature'] for r in rows}),'first_event_at':iso(first),'last_event_at':iso(last),'window_seconds':window if family=='TOKEN_CONSENSUS' else 0,'first_qualifying_buy_by_person':{p:next(r['event_at'] for r in rows if r['person_id']==p) for p in people},'facts':rows,'TTL_provenance':ttl,'expires_at':iso(first+ttl['value_seconds']),'deterministic_only':True,'investment_decision':None})
    for f in valid:
        if registry.persons[f['person_id']]['person_pattern_state']=='SIGNAL_ENABLED':output.append(build('PERSON_PATTERN',[f]))
    # Connected chronological window; each underlying qualifying buy has a stable identity.
    for mint in sorted({f['mint'] for f in valid}):
        rows=sorted([f for f in valid if f['mint']==mint],key=lambda r:(r['event_at'],r['event_id']))
        for end,row in enumerate(rows):
            group=[r for r in rows[:end+1] if epoch(row['event_at'])-epoch(r['event_at'])<=window]
            if len({r['person_id'] for r in group})>=2:output.append(build('TOKEN_CONSENSUS',group))
    return list({c['signal_id']:c for c in output}.values())

def run_bundle(items, namespace):
    if namespace not in ('LIVE','TEST'): raise ValueError('NAMESPACE')
    for c in items:
        verify(c)
        if c['namespace'] != namespace: raise ValueError('SYNTHETIC_CANNOT_ENTER_LIVE')
    rid='meme-run-'+digest({'namespace':namespace,'candidate_hashes':sorted(c['payload_sha256'] for c in items)})[:40]
    bounded=[]
    for c in sorted(items,key=lambda c:c['signal_id']):
        b={k:v for k,v in c.items() if k!='payload_sha256'};b['run_id']=rid;b['source_batch_id']=rid;bounded.append(seal(b))
    return seal({'schema_version':2,'namespace':namespace,'run_id':rid,'candidates':bounded,'expires_at':min((c['expires_at'] for c in bounded),default=None),'created_at':max((f['candidate_created_at'] for c in bounded for f in c['facts']),default=None),'gpt_consumer':'$300-3000','decisions':None})

def validate_run(run, *, namespace):
    verify(run)
    if run.get('schema_version')!=2 or run.get('namespace')!=namespace:raise ValueError('RUN_SCHEMA_NAMESPACE')
    if len(canonical(run))>75000:raise ValueError('RUN_SIZE_BOUND')
    if len({c['signal_id'] for c in run['candidates']})!=len(run['candidates']):raise ValueError('SIGNAL_DUPLICATE')
    for c in run['candidates']:
        verify(c)
        if c['schema_version']!=2 or c['run_id']!=run['run_id'] or c['source_batch_id']!=run['run_id'] or c['namespace']!=namespace or c['signal_family_candidate'] not in FAMILIES:raise ValueError('CANDIDATE_BINDING')
        required={'candidate_id','signal_id','event_id','run_id','source_batch_id','signal_family_candidate','person_id','person_ids','source_wallets','chain','mint','tx_signatures','detected_at','normalized_at','candidate_created_at','source_evidence_hashes','finalized_slots','facts','TTL_provenance','expires_at','first_event_at','last_event_at','window_seconds'}
        if not required<=set(c) or not c['facts']:raise ValueError('CANDIDATE_REQUIRED_FACTS')
        if c['person_ids']!=sorted({f['person_id'] for f in c['facts']}) or c['source_wallets']!=sorted({f['wallet'] for f in c['facts']}) or c['tx_signatures']!=sorted({f['signature'] for f in c['facts']}):raise ValueError('CANDIDATE_PERSON_WALLET_SIGNATURE_BINDING')
        if c['first_event_at']!=min(f['event_at'] for f in c['facts']) or c['last_event_at']!=max(f['event_at'] for f in c['facts']):raise ValueError('EVENT_WINDOW_BINDING')
        if c['TTL_provenance']['status']!='TEMPORARY_SHADOW_TTL' or epoch(c['expires_at'])!=epoch(c['first_event_at'])+c['TTL_provenance']['value_seconds']:raise ValueError('TTL_BINDING')
        if c['signal_family_candidate']=='TOKEN_CONSENSUS' and epoch(c['last_event_at'])-epoch(c['first_event_at'])>c['window_seconds']:raise ValueError('CONSENSUS_WINDOW')
        identity={'schema_version':2,'namespace':namespace,'family':c['signal_family_candidate'],'mint':c['mint'],'event_ids':sorted(f['event_id'] for f in c['facts']),'window_seconds':c['window_seconds'] if c['signal_family_candidate']=='TOKEN_CONSENSUS' else None}
        if c['signal_id']!='meme:signal:'+digest(identity) or c['event_id']!=c['signal_id'] or c['candidate_id']!='meme:candidate:'+digest(identity):raise ValueError('STABLE_SIGNAL_IDENTITY')
        if c['unique_person_count']!=len(set(c['person_ids'])):raise ValueError('UNIQUE_PERSON_COUNT')
        if c['signal_family_candidate']=='TOKEN_CONSENSUS' and c['unique_person_count']<2:raise ValueError('CONSENSUS_MINIMUM')
        for f in c['facts']:
            verify(f)
            if f.get('schema_version')!=2 or f['finalized_commitment']!='finalized' or type(f['finalized_slot']) is not int or int(f['buy_amount']['raw'])<=0:raise ValueError('FACT_SCHEMA_BUY')
            identity={'namespace':namespace,'person_id':f['person_id'],'wallet':f['wallet'],'signature':f['signature'],'mint':f['mint']}
            if f['event_id']!='meme:event:'+digest(identity):raise ValueError('STABLE_EVENT_IDENTITY')
            if f['namespace']!=namespace or f['mint']!=c['mint'] or f['person_id'] not in c['person_ids']:raise ValueError('FACT_BINDING')
    originals=[]
    for c in run['candidates']:
        b={k:v for k,v in c.items() if k!='payload_sha256'};b['run_id']=None;b['source_batch_id']=None;originals.append(seal(b)['payload_sha256'])
    expected='meme-run-'+digest({'namespace':namespace,'candidate_hashes':sorted(originals)})[:40]
    if run['run_id']!=expected:raise ValueError('STABLE_RUN_IDENTITY')
    return run
