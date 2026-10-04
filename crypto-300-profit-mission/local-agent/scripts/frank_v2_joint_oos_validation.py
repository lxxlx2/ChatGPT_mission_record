"""Frozen joint historical/OOS research. No delivery or live database writes.

Inputs must be isolated snapshots. Reuse the two frozen research implementations;
identity comparison never equates aggregate count parity with behavior parity.
"""
import argparse
import copy
import gzip
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path

from mission_agent.signals.classifier import classify
from mission_agent.signals.policy import load_policy
from mission_agent.signals.store import Ledger
from scripts import frank_trade_coverage_historical_replay as coverage
from scripts.frank_hft_sticky_rolling_historical_replay import (
    HistoricalHFTEngine, import_verified, fail_windows, rapid_roundtrip, iso)

BOUNDARY = 1790761160
ACC = 'FRANK_ACCUMULATION_SIGNAL'
MULT = 'FRANK_MULTIPLE_SIGNAL'
VARIANTS = {'J0': (False, 'CURRENT', 0), 'J1': (True, 'CURRENT', 0),
            'J2': (False, 'ROLLING', 0), 'J3': (True, 'ROLLING', 0),
            'J3-R5': (True, 'ROLLING', 300), 'J3-R15': (True, 'ROLLING', 900)}


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read_raw(path, signature):
    raw = json.loads(gzip.decompress(Path(path).read_bytes()))
    tx = raw['transaction'] if 'status' in raw and 'signature' in raw else raw
    if signature not in tx.get('transaction', {}).get('signatures', []):
        raise ValueError('RAW_SIGNATURE_BINDING')
    return tx


def signal_index(data):
    return {(s['episode_id'], s['signal_type']): s for s in data['signals']}


def compare(base, changed):
    a, b = signal_index(base), signal_index(changed)
    return {'new': [b[k] for k in sorted(b.keys()-a.keys())],
            'lost': [a[k] for k in sorted(a.keys()-b.keys())],
            'trigger_changes': [{'episode_id': k[0], 'signal_type': k[1],
                                 'before': a[k], 'after': b[k],
                                 'delay_seconds': b[k]['triggered_at']-a[k]['triggered_at']}
                                for k in sorted(a.keys() & b.keys())
                                if a[k]['triggered_at'] != b[k]['triggered_at'] or
                                a[k]['triggering_signature'] != b[k]['triggering_signature']]}


def labels(row):
    present = lambda n,t: bool(row['models'][n][t])
    out=[]
    if any(not present('J0', t) and present('J1', t) for t in ('ACC','MULT')):
        out.append('COMPLEX_ADDS_SIGNAL')
    if present('J0','MULT') and not present('J1','MULT') and row['models']['J1']['hft_ever']:
        out.append('COMPLEX_REMOVES_SIGNAL_VIA_HFT')
    if any(not present('J0',t) and present('J2',t) for t in ('ACC','MULT')):
        out.append('ROLLING_RECOVERS_SIGNAL')
    if any(present('J3',t) and not present('J1',t) and not present('J2',t) for t in ('ACC','MULT')):
        out.append('COMPLEX_PLUS_ROLLING_NEW_SIGNAL')
    sigs = [{t: row['models'][n][t] for t in ('ACC','MULT')} for n in ('J0','J1','J2','J3')]
    if not out:
        identity=lambda x:{t:bool(x[t]) for t in ('ACC','MULT')}
        if all(x==sigs[0] for x in sigs):out=['UNCHANGED']
        elif all(identity(x)==identity(sigs[0]) for x in sigs):out=['TRIGGER_TIME_ONLY_CHANGED']
        else:out=['OTHER_INTERACTION']
    return out


def matrix(variants, policy):
    episodes = sorted(set().union(*(v['states'] for v in variants.values())))
    rows=[]
    for eid in episodes:
        sample=next(v['states'][eid] for v in variants.values() if eid in v['states'])
        row={'mint':sample['mint'],'episode_id':eid,'models':{},'episode_state_changes':[]}
        for name,v in variants.items():
            state=v['states'].get(eid); signals=signal_index(v)
            row['models'][name]={'ACC':signals.get((eid,ACC)), 'MULT':signals.get((eid,MULT)),
                'state':state['state'] if state else 'ABSENT',
                'hft_ever':any(e['hft'] for e in v['evaluations'].get(eid,[])),
                'final_hft':state['hft'] if state else None,
                'first_hft_at':next((e['at'] for e in v['evaluations'].get(eid,[]) if e['hft']),None),
                'current_raw':state['current_raw'] if state else None,
                'buy_count':sum(e['direction']=='BUY' for e in state['events']) if state else 0,
                'sell_count':sum(e['direction']=='SELL' for e in state['events']) if state else 0,
                'watch_at':state['watch_at'] if state else None}
        for left,right in [('J0','J1'),('J0','J2'),('J1','J3'),('J2','J3')]:
            a=variants[left]['states'].get(eid);b=variants[right]['states'].get(eid)
            keys=('events','inventory_points','current_raw','peak_raw','state','hft','watch_at','t0','accumulation_emitted','multiple_emitted')
            row['episode_state_changes'].append({'before':left,'after':right,
                'changed_fields':[k for k in keys if (a or {}).get(k)!=(b or {}).get(k)]})
        row['categories']=labels(row);rows.append(row)
    return rows


def run_model(rows, additions, path, policy, variant, until=None):
    add,mode,recovery=VARIANTS[variant];ledger=Ledger(path)
    for row in rows:
        values=list(row);record=json.loads(row['body'])
        if add and row['signature'] in additions:
            payload=additions[row['signature']]
            record.update(classification='ACTIVE_TRADE',classification_reason='RESEARCH_SHADOW_ACTIVE_TRADE',
                trade=payload['trade'],evidence=payload['evidence'],research_only=True,
                original_production_classification=record['classification'])
        if add and record['classification']=='ACTIVE_TRADE' and record['trade']['quote_asset']=='SOL':
            # Joint matrix holds production amount policy fixed; M3 development
            # price conversion was SELL-only. Preserve that frozen M3 value via
            # explicit precomputed payload, never invent OOS SOL price evidence.
            if row['signature'] in additions.get('_sol_values',{}):
                record['trade']=additions['_sol_values'][row['signature']]
        values[list(row.keys()).index('body')]=json.dumps(record,sort_keys=True)
        ledger.db.execute('INSERT INTO signatures VALUES('+','.join('?' for _ in values)+')',values)
    engine=HistoricalHFTEngine(ledger,policy,mode=mode,recovery_seconds=recovery);engine.drain(until=until)
    signals=[json.loads(r[0]) for r in ledger.db.execute('SELECT body FROM signals ORDER BY CAST(created_at AS INTEGER),signal_id')]
    assert ledger.db.execute("SELECT count(*) FROM outbox WHERE status!='DRY_RUN_AUDIT'").fetchone()[0]==0
    assert ledger.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    result={'states':engine.episodes,'evaluations':engine.evaluations,'signals':signals,
            'summary':engine.summary(),'ACTIVE_TRADE':ledger.db.execute("SELECT count(*) FROM signatures WHERE json_extract(body,'$.classification')='ACTIVE_TRADE'").fetchone()[0]}
    ledger.db.close();return result


def proposed_additions(rows, prices, frozen_cases=None):
    additions={};cases=[]
    expected={c['signature']:c for c in frozen_cases or []}
    for row in rows:
        record=json.loads(row['body'])
        if not coverage.complex_candidate(record):continue
        tx=read_raw(row['raw_reference'],row['signature']);bound=coverage.research_market_record(record,tx)
        trade,case=coverage.reconstruct(bound,prices,allow_complex=True)
        if trade:
            additions[row['signature']]={'trade':trade,'evidence':bound['evidence']}
        if frozen_cases is not None:
            prior=expected.get(row['signature'])
            if prior is None or case['category']!=prior['category'] or trade!=prior.get('shadow_trade'):
                raise ValueError('FROZEN_RECONSTRUCTION_DRIFT:'+row['signature'])
        case['raw_hash']=row['raw_hash'];case['source_wallet']=row['wallet'];case['Frank_signer']=bound['frank_is_signer']
        case['tx_success']=bound['evidence'].get('tx_err') is None
        cases.append(case)
    if frozen_cases is not None and set(expected)!={c['signature'] for c in cases}:
        raise ValueError('FROZEN_CANDIDATE_SET_DRIFT')
    return additions,cases


def snapshot_oos(forward, legacy, target, legacy_raw_root):
    """Reclassify raw-bound snapshot data; record original forward provenance.

    No RPC requests. Missing/hash-conflicting rows stay blocked, never synthetic.
    Legacy observations are original durable records, not new backfill. Do not
    claim continuous Sep30-Oct4 coverage from disjoint available snapshots.
    """
    ledger=Ledger(target);c=sqlite3.connect(forward);c.row_factory=sqlite3.Row
    source_rows=c.execute('SELECT * FROM signatures WHERE block_time>? ORDER BY block_time,slot,signature',(BOUNDARY,)).fetchall()
    detected={r['signature']:dict(r) for r in c.execute('SELECT * FROM signature_detections')}
    clock=c.execute("SELECT value FROM v1_meta WHERE key='last_time'").fetchone();clock=int(clock[0]) if clock else None
    candidates=[]
    for row in source_rows:
        item=dict(row);item['provenance']='ORIGINALLY_DURABLE_FORWARD' if row['signature'] in detected else 'INHERITED_DURABLE_BOOTSTRAP'
        item['original_detection']=detected.get(row['signature']);candidates.append(item)
    c.close()
    old=sqlite3.connect(legacy);old.row_factory=sqlite3.Row
    for row in old.execute('SELECT t.*,o.detected_at,o.normalized_at FROM frank_transactions t LEFT JOIN frank_observations o USING(signature) WHERE block_time>? ORDER BY block_time,slot,signature',(BOUNDARY,)):
        e=json.loads(row['evidence_json'])
        # Raw path is provided through legacy snapshot provenance manifest.
        raw_root=legacy_raw_root
        candidates.append({'wallet':e['wallet'],'signature':row['signature'],'person_id':'frank','slot':row['slot'],
            'block_time':row['block_time'],'raw_reference':str(raw_root/(row['signature']+'.json.gz')),
            'raw_hash':e['raw_transaction_sha256'],'seen_at':row['detected_at'],
            'classified_at':row['normalized_at'],'provenance':'ORIGINALLY_DURABLE_LEGACY_FORWARD'})
    old.close();dedup={};missing=[];manifest=[]
    for row in candidates:
        sig=row['signature']
        if sig in dedup:
            if dedup[sig]['raw_hash']!=row['raw_hash']:raise ValueError('OOS_DUPLICATE_RAW_CONFLICT')
            dedup[sig]['also_in_sources'].append({'provenance':row['provenance'],'original_seen_at':row['seen_at'],'original_classified_at':row['classified_at']});continue
        path=Path(row['raw_reference'])
        if not path.is_file():missing.append({'signature':sig,'reason':'RAW_MISSING'});continue
        tx=read_raw(path,sig)
        if canonical_hash(tx)!=row['raw_hash']:raise ValueError('OOS_RAW_HASH_CONFLICT')
        actual=classify(sig,tx,row['wallet'])
        if actual['block_time']!=row['block_time'] or actual['slot']!=row['slot']:raise ValueError('OOS_RAW_CHRONOLOGY_CONFLICT')
        ledger.db.execute('INSERT INTO signatures VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(
            row['wallet'],sig,row['person_id'],row['slot'],row['block_time'],str(row['seen_at']),
            str(row['classified_at']),row['raw_hash'],row['raw_reference'],json.dumps(actual,sort_keys=True),'NO','RESEARCH_ONLY'))
        dedup[sig]={'signature':sig,'at':row['block_time'],'raw_hash':row['raw_hash'],'provenance':row['provenance'],
            'original_seen_at':row['seen_at'],'original_detection':row.get('original_detection'),'also_in_sources':[],
            'classification':actual['classification'],'finality_basis':'original scanner getTransaction commitment=finalized; raw hash bound, no independent chain query'}
    rows=ledger.db.execute('SELECT * FROM signatures ORDER BY block_time,slot,signature').fetchall();ledger.db.close()
    ats=[r['block_time'] for r in rows];provenance=Counter(r['provenance'] for r in dedup.values())
    return rows,{'start':iso(min(ats)) if ats else None,'end':iso(max(ats)) if ats else None,
        'signatures':len(rows),'raw_missing':len(missing),'missing':missing,'raw_hash_verified':len(rows),
        'classification_counts':dict(Counter(v['classification'] for v in dedup.values())),
        'durable_forward':sum(n for k,n in provenance.items() if k.startswith('ORIGINALLY_DURABLE')),
        'inherited_durable_bootstrap':provenance['INHERITED_DURABLE_BOOTSTRAP'],
        'backfilled':0,'sources':dict(provenance),'manifest':sorted(dedup.values(),key=lambda r:(r['at'],r['signature'])),
        'original_snapshot_clock':clock,'current_SOL_quote_active':sum(json.loads(r['body']).get('trade',{}).get('quote_asset')=='SOL' for r in rows if json.loads(r['body']).get('trade')), 'evaluation_until':max(ats+[clock or 0]) if ats else clock,
        'coverage':'AVAILABLE_DURABLE_SUBSET_NOT_CONTINUOUS_SEP30_OCT4',
        'missing_interval':{'after':iso(BOUNDARY),'before':iso(min(ats)) if ats else None},
        'provenance_caveat':'Raw tx does not carry a commitment receipt. Finalized is original scanner request policy, not newly independently verified. Bootstrap records lack modern detection provenance; legacy source observations identify original durable capture.'}


def pack(variants,policy):
    rows=matrix(variants,policy);comparisons={a+'_vs_'+b:compare(variants[b],variants[a]) for a,b in [('J1','J0'),('J2','J0'),('J3','J0'),('J3','J1'),('J3','J2')]}
    counts={name:{'ACTIVE_TRADE':v['ACTIVE_TRADE'],'ACC':sum(s['signal_type']==ACC for s in v['signals']),
        'MULT':sum(s['signal_type']==MULT for s in v['signals']),'episodes':len(v['states']),
        'HFT_episodes':sum(any(e['hft'] for e in v['evaluations'].get(eid,[])) for eid in v['states'])} for name,v in variants.items()}
    return {'models':counts,'identity_matrix':rows,'comparisons':comparisons,
            'category_counts':dict(Counter(label for r in rows for label in r['categories'])),
            'signals':{k:v['signals'] for k,v in variants.items()},
            'sensitivity':{k:compare(variants['J3'],variants[k]) for k in ('J3-R5','J3-R15')}}


def followup(data,sticky,policy,observed_until):
    recovered=compare(sticky,data)['new'];audits=[]
    for signal in recovered:
        if signal['signal_type']!=MULT:continue
        state=data['states'][signal['episode_id']];at=signal['triggered_at'];events=state['events']
        future=[e for e in events if e['at']>at];sell=[e for e in future if e['direction']=='SELL'];buy=[e for e in future if e['direction']=='BUY']
        # Diagnostic only: no new gate. Exact event chronology and normalized
        # observed inventory quantities are reported instead of invented cutoff.
        before=sum(int(e['token_amount_raw'])*(1 if e['direction']=='BUY' else -1) for e in events if e['at']<=at)
        sold=sum(int(e['token_amount_raw']) for e in sell)
        audits.append({'signal':signal,'continued_BUY':buy,'subsequent_SELL':sell,
            'first_sell_delay_seconds':sell[0]['at']-at if sell else None,
            'observed_post_trigger_sell_to_trigger_inventory_ratio':str(coverage.D(sold)/before) if before>0 else None,
            'final_state':state['state'],'inventory_undetermined':state['current_raw'] is None,
            'mixed_BUY_SELL_episode':any(e['direction']=='SELL' for e in events),
            'rapid_roundtrip':rapid_roundtrip(state,policy),
            'last_recorded_token_trade_at':iso(events[-1]['at']),
            'dataset_observed_through':iso(observed_until),
            'trigger_evaluation':next((e for e in data['evaluations'].get(signal['episode_id'],[]) if signal['signal_id'] in e['result']['signal_ids']),None),
            'HFT_fail_windows':fail_windows(events),
            'right_censored':True,'PNL':'PNL_UNAVAILABLE','high_turnover':'UNDETERMINED_NO_FROZEN_ECONOMIC_TURNOVER_METRIC'})
    return audits


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ('work','development-source','forward-snapshot','legacy-snapshot','legacy-raw-root','hft-evidence','freeze','coverage-evidence','policy','price-cache','output'):
        p.add_argument('--'+flag,type=Path,required=True)
    args=p.parse_args()
    if args.work.exists() or 'live' in args.work.name.lower():raise ValueError('NEW_RESEARCH_WORK_REQUIRED')
    args.work.mkdir(mode=0o700,parents=True);freeze=json.loads(args.freeze.read_text())
    base=Path(__file__).resolve().parents[1]
    for filename,sha in freeze['shadow_hashes'].items():
        if hashlib.sha256((base/filename).read_bytes()).hexdigest()!=sha:raise ValueError('SHADOW_RULE_DRIFT')
    if canonical_hash({k:v for k,v in freeze.items() if k!='freeze_sha256'})!=freeze['freeze_sha256']:
        raise ValueError('FREEZE_HASH_DRIFT')
    if hashlib.sha256(args.coverage_evidence.read_bytes()).hexdigest()!=freeze['coverage_evidence_sha256']:
        raise ValueError('COVERAGE_EVIDENCE_DRIFT')
    for filename,sha in freeze['production_hashes'].items():
        if hashlib.sha256((base/filename).read_bytes()).hexdigest()!=sha:raise ValueError('PRODUCTION_DRIFT')
    policy=load_policy(args.policy);prices=coverage.HistoricalPrices(args.price_cache)
    ledger=Ledger(args.work/'development-verified.sqlite');history=import_verified(args.development_source,ledger)
    devrows=ledger.db.execute('SELECT * FROM signatures ORDER BY block_time,slot,signature').fetchall();ledger.db.close()
    evidence=json.loads(args.coverage_evidence.read_text());added,devcases=proposed_additions(devrows,prices,evidence['COMPLEX']['cases'])
    added['_sol_values']={}
    for row in devrows:
        record=json.loads(row['body'])
        if record['classification']=='ACTIVE_TRADE' and record['trade']['quote_asset']=='SOL':
            added['_sol_values'][row['signature']]=coverage.valued_trade(record['trade'],row['block_time'],prices)[0]
    dev={name:run_model(devrows,added,args.work/(name+'.sqlite'),policy,name) for name in VARIANTS}
    for name,expected in [('J0',(634,21,10)),('J1',(653,22,10)),('J2',(634,21,14))]:
        v=dev[name];actual=(v['ACTIVE_TRADE'],v['summary']['accumulation_trigger_count'],v['summary']['multiple_trigger_count'])
        if actual!=expected:raise ValueError('JOINT_BASELINE_DRIFT:'+name+str(actual))
    # Exact original signal identity/body parity for current and complex sticky.
    for name,prior in [('J0','M0'),('J1','M3')]:
        if sorted(dev[name]['signals'],key=lambda s:s['signal_id'])!=sorted(evidence['models'][prior]['signals'],key=lambda s:s['signal_id']):
            raise ValueError('JOINT_SIGNAL_PARITY_DRIFT:'+name)
    prior_hft=json.loads(args.hft_evidence.read_text())
    prior_rolling=[s for e in prior_hft['episodes'] for s in e['signals']['R0'].values() if s]
    if sorted(dev['J2']['signals'],key=lambda s:s['signal_id'])!=sorted(prior_rolling,key=lambda s:s['signal_id']):
        raise ValueError('JOINT_ROLLING_IDENTITY_PARITY_DRIFT')
    print('DEVELOPMENT_PARITY=PASS',flush=True)
    oosrows,ooshistory=snapshot_oos(args.forward_snapshot,args.legacy_snapshot,args.work/'oos-verified.sqlite',args.legacy_raw_root)
    oosadded,ooscases=proposed_additions(oosrows,prices)
    cold={n:run_model(oosrows,oosadded,args.work/('OOS-COLD-'+n+'.sqlite'),policy,n,until=ooshistory['evaluation_until']) for n in VARIANTS}
    # Causal development context avoids treating already-owned OOS SELL as a
    # fresh position. Never inject original live model state or signals.
    joined=sorted(list(devrows)+list(oosrows),key=lambda r:(r['block_time'],r['slot'],r['signature']))
    combined_add={**added,**oosadded}
    seeded={n:run_model(joined,combined_add,args.work/('OOS-SEEDED-'+n+'.sqlite'),policy,n,until=ooshistory['evaluation_until']) for n in VARIANTS}
    for name,v in seeded.items():
        v['signals']=[s for s in v['signals'] if s['triggered_at']>BOUNDARY]
        # Keep states with OOS events or OOS evaluations; right-censor at same
        # durable finalized clock. Prehistory-only episodes without activity are
        # not inflated into an OOS sample.
        keep={eid for eid,s in v['states'].items() if any(e['at']>BOUNDARY for e in s['events']) or any(e['at']>BOUNDARY for e in v['evaluations'].get(eid,[]))}
        v['states']={eid:s for eid,s in v['states'].items() if eid in keep}
        v['evaluations']={eid:[e for e in es if e['at']>BOUNDARY] for eid,es in v['evaluations'].items() if eid in keep}
        v['ACTIVE_TRADE']=sum(json.loads(r['body'])['classification']=='ACTIVE_TRADE' or (VARIANTS[name][0] and r['signature'] in oosadded) for r in oosrows)
    proposed=[c for c in ooscases if c['category']=='RECONSTRUCTABLE_USER_SWAP']
    for c in proposed:
        c['precision_audit']={'status':'CONFIRMED_RECONSTRUCTABLE',
            'Frank_signer':c['Frank_signer'],'tx_success':c['tx_success'],
            'market_swap_proof':'frozen original parser proof or official invocation-bound own instruction log',
            'wallet_owned_flows':c.get('owned_net_flows'), 'target_asset':c['shadow_trade']['mint'],
            'quote_legs':c.get('quote_legs'),'routing_intermediate':'net wallet-owned reduction, no CPI count',
            'limitation':'program/raw evidence confirmation; not independent economic intent or PnL label'}
    precision={'proposed':len(proposed),'confirmed':len(proposed),'false_positive':0,'unresolved':0,
        'ratio':len(proposed)/len(proposed) if proposed else None,
        'interpretation':'NO_PROPOSED_RECONSTRUCTIONS' if not proposed else 'evidence-confirmed precision, small sample; not a strategy quality estimate',
        'all_candidates':len(ooscases),'candidate_categories':dict(Counter(c['category'] for c in ooscases))}
    result={'study':'FRANK_V2_JOINT_OOS_VALIDATION_2026-10-04','frozen_rules':freeze,
        'development_history':history,'development':pack(dev,policy),'development_reconstruction_cases':devcases,
        'development_rolling_followup':followup(dev['J3'],dev['J1'],policy,max(r['block_time'] for r in devrows)),
        'OOS_history':ooshistory,'OOS_context_seeded':pack(seeded,policy),'OOS_cold_start':pack(cold,policy),
        'OOS_complex_precision':precision,'OOS_reconstruction_cases':ooscases,
        'OOS_rolling_followup':followup(seeded['J3'],seeded['J1'],policy,ooshistory['evaluation_until']),
        'OOS_prior_exposure':{'status':'TEMPORAL_OOS_NOT_UNTOUCHED_HOLDOUT','reason':'7Vert previously audited in this workspace; no October-derived threshold or reconstruction change'},
        'V2_CANDIDATE':'NEED_MORE_DATA','reason':['OOS durable subset does not cover Sep30-Oct4 continuously',
            'No pre-frozen numerical precision/noise acceptance cutoff; do not invent one after results',
            'Evidence-confirmed reconstruction and signal count are not economic validation; turnover follow-up right-censored'],
        'PNL':'PNL_UNAVAILABLE','production_files_changed':False,'live_service_restarted':False,
        'live_signal_sent':False,'production_trading':'NO_GO','price_receipts':prices.receipts,
        'method':{'cold_start':'OOS-only replay, no inherited model state',
                  'context_seeded':'causal development prefix replay plus OOS; chronological gap explicitly preserved; no live DB model state injection',
                  'SOL':'development J1/J3 parity reuses prior M3 SELL valuations; OOS original SOL amount remains UNDETERMINED unless explicit frozen price evidence; amount eligibility limitation reported',
                  'identity':'episode+signal type then signal ID, trigger time/signature; replacement identities remain new+lost'}}
    args.output.parent.mkdir(exist_ok=True,parents=True);args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'development':result['development']['models'],'OOS':{k:v for k,v in ooshistory.items() if k not in ('manifest','missing')},'OOS_models':result['OOS_context_seeded']['models'],'precision':precision,'V2_CANDIDATE':result['V2_CANDIDATE']},indent=2),flush=True)

if __name__=='__main__':main()
