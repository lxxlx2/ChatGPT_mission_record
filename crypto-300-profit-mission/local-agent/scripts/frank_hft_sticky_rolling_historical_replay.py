"""FRANK HFT STICKY/ROLLING HISTORICAL_REPLAY; never a production entry point.

Only HFT state changes. Engine chronology, clock, T0, WATCH, inventory and gates
are inherited. No network, delivery adapters, OAuth or live database imports.
"""
import argparse
import copy
import gzip
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from mission_agent.hashing import digest
from mission_agent.signals.classifier import classify
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import USDC, load_policy
from mission_agent.signals.store import Ledger


def iso(at):
    return datetime.fromtimestamp(at, timezone.utc).isoformat() if at is not None else None


def fail_windows(events, window=60, minimum=3):
    """Inclusive integer-second windows. One ACTIVE_TRADE per signature.

    An overlapping consecutive triple contributes [last.at, first.at + 60].
    Merge adjacent intervals; next passing second = last failing second + 1.
    Events must already be causal and in production chronological order.
    """
    intervals = []
    for i in range(minimum - 1, len(events)):
        start, end = events[i]['at'], events[i - minimum + 1]['at'] + window
        if start > end:
            continue
        if intervals and start <= intervals[-1]['end'] + 1:
            intervals[-1]['end'] = max(end, intervals[-1]['end'])
        else:
            intervals.append({'start': start, 'end': end})
    return intervals


def rapid_roundtrip(state, policy):
    # Preserve the original sticky rapid-close path even if later SELL records
    # append to an already CLOSED episode. A subsequent BUY resets the episode.
    maximum = policy['mapping']['FRANK_MULTIPLE_SIGNAL']['rapid_roundtrip_reference_seconds']
    if 'inventory_points' in state:
        return any(p['raw'] == '0' and p['at'] - state['events'][0]['at'] <= maximum
                   for p in state['inventory_points'])
    return (state['state'] == 'CLOSED' and
            state['events'][-1]['at'] - state['events'][0]['at'] <= maximum)


def rolling_fail(state, at, policy, recovery_seconds=0):
    m = policy['mapping']['FRANK_MULTIPLE_SIGNAL']
    windows = fail_windows([e for e in state['events'] if e['at'] <= at],
                           m['hft_window_seconds'], m['hft_swaps_min'])
    # R5/R15 require 300/900 continuous passing seconds after inclusive expiry.
    return rapid_roundtrip(state, policy) or any(
        w['start'] <= at <= w['end'] + recovery_seconds for w in windows)


class HistoricalHFTEngine(Engine):
    """Research subclass. CURRENT is exactly super; shadow alters only hft.

    _evaluate also runs on hourly ticks before watch_eligible reads the state.
    Thus WATCH effects are causal consequences of HFT, not a second rule change.
    """
    def __init__(self, ledger, policy, *, mode='CURRENT', recovery_seconds=0):
        if mode not in ('CURRENT', 'ROLLING') or recovery_seconds not in (0, 300, 900):
            raise ValueError('UNFROZEN_RESEARCH_VARIANT')
        self.mode, self.recovery_seconds = mode, recovery_seconds
        self.episodes, self.evaluations = {}, {}
        super().__init__(ledger, policy, dry_run=True)

    def _evaluate(self, state, at, signature, kind):
        if self.mode == 'ROLLING':
            state['hft'] = rolling_fail(state, at, self.policy, self.recovery_seconds)
        result = super()._evaluate(state, at, signature, kind)
        self.evaluations.setdefault(state['episode_id'], []).append({
            'at': at, 'time_utc': iso(at), 'signature': signature, 'kind': kind,
            'hft': state['hft'], 'state': state['state'], 'current_raw': state['current_raw'],
            'peak_raw': state['peak_raw'], 'watch_at': state['watch_at'],
            'result': copy.deepcopy(result)})
        return result

    def _save(self, state):
        self.episodes[state['episode_id']] = copy.deepcopy(state)
        return super()._save(state)


def import_verified(source, target):
    """Read-only raw-bound full reclassification before any model variant."""
    src = sqlite3.connect('file:' + str(source.resolve()) + '?mode=ro', uri=True)
    src.row_factory = sqlite3.Row
    rows = src.execute('SELECT * FROM signatures ORDER BY block_time,slot,signature').fetchall()
    missing, manifest, counts, duplicates = [], [], Counter(), []
    identities = set()
    for row in rows:
        identity = (row['wallet'], row['signature'])
        if identity in identities:
            duplicates.append(identity)
        identities.add(identity)
        p = Path(row['raw_reference'])
        if not p.is_file():
            missing.append(row['signature'])
            continue
        raw = json.loads(gzip.decompress(p.read_bytes()))
        if 'status' in raw and 'signature' in raw:
            if raw['signature'] != row['signature']:
                raise ValueError('RAW_SIGNATURE_BINDING')
            tx = raw['transaction']
        else:
            tx = raw
        h = hashlib.sha256(json.dumps(tx, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        if h != row['raw_hash']:
            raise ValueError('RAW_HASH_CONFLICT')
        signed = tx.get('transaction', {}).get('signatures')
        if signed is not None and row['signature'] not in signed:
            raise ValueError('RAW_CHAIN_SIGNATURE_BINDING')
        actual = classify(row['signature'], tx, row['wallet'])
        old = json.loads(row['body'])
        for key in ('classification', 'trade', 'block_time', 'slot', 'wallet', 'frank_is_signer'):
            if actual.get(key) != old.get(key):
                raise ValueError('CLASSIFICATION_DRIFT:' + key)
        counts[actual['classification']] += 1
        manifest.append({'wallet': row['wallet'], 'signature': row['signature'], 'raw_hash': h})
        # A fresh raw-bound body removes old signal/audit fields. No ledger.put
        # legacy position logic is needed; Engine reconstructs from signatures.
        values = [row[k] for k in row.keys()]
        values[list(row.keys()).index('body')] = json.dumps(actual, sort_keys=True)
        target.db.execute('INSERT INTO signatures VALUES(' + ','.join('?' for _ in values) + ')', values)
    src.close()
    if missing:
        raise ValueError('RAW_MISSING:' + str(len(missing)))
    if duplicates:
        raise ValueError('HFT_INPUT_DUPLICATION_RISK')
    return {'usable_signatures': len(rows), 'classification_counts': dict(counts),
            'start': iso(min(r['block_time'] for r in rows if r['block_time'] is not None)),
            'end': iso(max(r['block_time'] for r in rows if r['block_time'] is not None)),
            'raw_missing': 0, 'raw_hash_verified': len(manifest),
            'chronology_sha256': digest(manifest), 'duplicate_wallet_signatures': len(duplicates),
            'coverage': 'AVAILABLE_VERIFIED_SUBSET_NOT_WALLET_LIFETIME',
            'hft_input_unit': 'one classified ACTIVE_TRADE event/signature; not DEX CPI hops'}


def run_variant(verified, path, policy, mode, recovery):
    ledger = Ledger(path)
    src = sqlite3.connect('file:' + str(verified) + '?mode=ro', uri=True)
    rows = src.execute('SELECT * FROM signatures ORDER BY block_time,slot,signature').fetchall()
    ledger.db.executemany('INSERT INTO signatures VALUES(' + ','.join('?' for _ in rows[0]) + ')', rows)
    src.close()
    engine = HistoricalHFTEngine(ledger, policy, mode=mode, recovery_seconds=recovery)
    engine.drain()  # Same original clock schedule; no extra synthetic evaluation.
    signals = [json.loads(r[0]) for r in ledger.db.execute('SELECT body FROM signals ORDER BY CAST(created_at AS INTEGER),signal_id')]
    assert not ledger.db.execute("SELECT 1 FROM outbox WHERE status!='DRY_RUN_AUDIT'").fetchone()
    assert ledger.db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    data = {'states': engine.episodes, 'evaluations': engine.evaluations, 'signals': signals,
            'summary': engine.summary(), 'notifications_sent': 0, 'gmail_sent': 0}
    ledger.db.close()
    return data


def first_signal(data, episode, signal_type):
    return next((s for s in data['signals'] if s['episode_id'] == episode and s['signal_type'] == signal_type), None)


def episode_record(state, variants):
    events = state['events']; buys = [e for e in events if e['direction'] == 'BUY']
    windows = fail_windows(events); first = windows[0]['start'] if windows else None
    first_events = [e for e in events if first is not None and first - 60 <= e['at'] <= first]
    # At identical block times only the processed prefix exists at first trigger.
    if windows:
        first_index = next(i for i in range(2, len(events)) if events[i]['at'] == first and events[i]['at'] - events[i-2]['at'] <= 60)
        first_events = [e for e in events[:first_index+1] if first-60 <= e['at'] <= first]
    after = [e for e in buys if first is not None and e['at'] > first]
    later_normal = next((e for e in after if not any(w['start'] <= e['at'] <= w['end'] for w in windows)), None)
    current = Decimal(state['current_raw']) if state['current_raw'] is not None else None
    peak = Decimal(state['peak_raw']); retention = str(current / peak) if current is not None and peak else None
    eid = state['episode_id']; signals = {}
    for name, data in variants.items():
        if name == '_policy':
            continue
        signals[name] = {k: first_signal(data, eid, typ) for k, typ in
                         [('ACCUMULATION', 'FRANK_ACCUMULATION_SIGNAL'), ('MULTIPLE', 'FRANK_MULTIPLE_SIGNAL')]}
    a, b = signals['CURRENT']['MULTIPLE'], signals['R0']['MULTIPLE']
    evals = variants['CURRENT']['evaluations'][eid]
    hft_only = [v for v in evals if v['result']['predicates']['hft'] == 'FAIL' and all(
        v['result']['predicates'][k] == 'PASS' for k in ('prior_accumulation','t0','cumulative_amount','persistence','inventory','distribution','freshness'))]
    if not a and b:
        category = 'STICKY_BLOCKED_ROLLING_MULTIPLE'
    elif not a and not b and windows and hft_only:
        category = 'BOTH_HFT_BLOCKED'
    elif bool(a) == bool(b) and (not a or a['triggered_at'] == b['triggered_at']):
        category = 'SAME_RESULT'
    else:
        category = 'OTHER_DIFFERENCE'
    usdc = sum((Decimal(e['quote_quantity']) for e in buys if e['quote_asset']==USDC),Decimal(0))
    distribution_fail = [v for v in evals if first is not None and v['at'] > first and v['result']['predicates']['distribution']=='FAIL']
    # Raw peak-to-inventory decline is distinct from the unrecovered rolling veto.
    running_peak = 0; drops = []; retained_after = False
    for p in state['inventory_points']:
        if p['raw'] is None: continue
        value = int(p['raw']); running_peak=max(running_peak,value)
        if first is not None and p['at'] > first and running_peak and Decimal(value)/running_peak >= Decimal('.5'):
            retained_after = True
        if running_peak and Decimal(running_peak-value)/running_peak > Decimal('.35'):
            drops.append(p['at'])
    return {'person': state['person_id'], 'mint':state['mint'], 'episode_id':eid,
            'first_buy_at':events[0]['at'],'first_buy_utc':iso(events[0]['at']),
            'last_trade_at':events[-1]['at'],'last_trade_utc':iso(events[-1]['at']),
            'buy_count':len(buys),'sell_count':len(events)-len(buys),'buy_span_seconds':buys[-1]['at']-buys[0]['at'],
            'known_USDC_gross_buys':str(usdc),'quote_assets':sorted({e['quote_asset'] for e in events}),
            'peak_observed_inventory_raw':state['peak_raw'],'final_observed_inventory_raw':state['current_raw'],
            'final_inventory_retention':retention,'final_state':state['state'],
            'sticky_hft_first_trigger_at':first,'sticky_hft_first_trigger_utc':iso(first),
            'sticky_hft_trigger_signature':first_events[-1]['signature'] if first_events else None,
            'first_hft_trade_count':len(first_events),'first_hft_composition':dict(Counter(e['direction'] for e in first_events)),
            'first_hft_events':first_events,'rolling_hft_fail_windows':[{**w,'first_pass_at':w['end']+1} for w in windows],
            'rapid_roundtrip_reference':rapid_roundtrip(state, variants['_policy']),
            'post_first_hft_buys':len(after),'post_first_hft_buy_span_seconds':after[-1]['at']-after[0]['at'] if after else 0,
            'post_first_hft_buy_elapsed_seconds':after[-1]['at']-first if after else 0,
            'first_low_frequency_buy_at':later_normal['at'] if later_normal else None,
            'seconds_from_first_window_expiry_to_low_frequency_buy':later_normal['at']-(windows[0]['end']+1) if later_normal else None,
            'unrecovered_distribution_evaluation_count':len(distribution_fail),
            'observed_peak_drop_gt35':any(first is not None and at > first for at in drops),'inventory_ge50pct_peak_after_hft_seen':retained_after,'hft_only_blocked_evaluation_count':len(hft_only),
            'has_buy_within_60m_after_hft':any(0<e['at']-first<=3600 for e in after),
            'has_buy_after_60m_after_hft':any(e['at']-first>3600 for e in after),
            'has_buy_after_45m_after_hft':any(e['at']-first>2700 for e in after),
            'category':category,'signals':signals,'events':events,
            'intent_classification':'D_UNDETERMINED',
            'intent_basis':'Separate signed user-level trades prove activity; split orders, routing intent and arbitrage profitability cannot be inferred from count alone.',
            'pnl_status':'PNL_UNAVAILABLE'}


def build_comparison(variants, history):
    policy = variants.pop('_policy')
    current=variants['CURRENT']; shadow=variants['R0']
    assert set(current['states'])==set(shadow['states'])
    records=[]
    for eid,s in current['states'].items():
        for name,v in variants.items():
            other=v['states'][eid]
            for key in ('events','inventory_points','current_raw','peak_raw','state','t0','t0_amount_status','accumulation_emitted'):
                assert s[key]==other[key],('NON_HFT_STATE_DRIFT',name,eid,key)
        variants['_policy']=policy
        records.append(episode_record(s,variants))
        variants.pop('_policy')
    records.sort(key=lambda r:(r['first_buy_at'],r['mint'],r['episode_id']))
    acc=lambda v:{(s['episode_id'],s['triggered_at']) for s in v['signals'] if s['signal_type']=='FRANK_ACCUMULATION_SIGNAL'}
    assert all(acc(v)==acc(current) for v in variants.values()),'ACCUMULATION_DIFFERENCE'
    ids=lambda v:{s['episode_id'] for s in v['signals'] if s['signal_type']=='FRANK_MULTIPLE_SIGNAL'}
    base=ids(current);new=ids(shadow)-base;lost=base-ids(shadow)
    hft=[r for r in records if r['rolling_hft_fail_windows']]
    hist={**history,'ACTIVE_TRADE':history['classification_counts'].get('ACTIVE_TRADE',0),
          'tokens':current['summary']['tokens_evaluated'],'episodes':len(records)}
    sensitivity={}
    for name in ('R0','R5','R15'):
        additions=ids(variants[name])-base; deltas=[]
        for eid in sorted(new):
            first=first_signal(variants[name],eid,'FRANK_MULTIPLE_SIGNAL')
            r0=first_signal(shadow,eid,'FRANK_MULTIPLE_SIGNAL')
            deltas.append({'episode_id':eid,'trigger_at':first['triggered_at'] if first else None,
                           'delay_from_R0_seconds':first['triggered_at']-r0['triggered_at'] if first else None})
        sensitivity[name]={'MULTIPLE_count':len(ids(variants[name])),'new_MULTIPLE_count':len(additions),
                           'lost_current_MULTIPLE':len(base-ids(variants[name])),'per_R0_candidate':deltas}
    stats={'episodes_total':len(records),'episodes_hft_ever':sum(bool(r['rolling_hft_fail_windows']) or r['rapid_roundtrip_reference'] for r in records),
           'episodes_60s_hft_ever':len(hft),
           'episodes_sticky_hft_ratio':len(hft)/len(records),
           'episodes_sticky_hft_ratio_definition':'60-second burst episodes / all episodes; rapid roundtrip separate',
           'rapid_roundtrip_episodes':sum(r['rapid_roundtrip_reference'] for r in records),
           'MULTIPLE_current_count':len(base),'MULTIPLE_rolling_count':len(ids(shadow)),
           'new_MULTIPLE_from_rolling':len(new),'new_MULTIPLE_rate':len(new)/len(records),
           'new_MULTIPLE_rate_denominator':'all reconstructed episodes',
           'new_MULTIPLE_relative_to_current':len(new)/len(base) if base else None,
           'current_MULTIPLE_lost_under_rolling':len(lost),
           'ACCUMULATION_current_count':len(acc(current)),'ACCUMULATION_rolling_count':len(acc(shadow)),
           'category_counts':{key:sum(r['category']==key for r in records) for key in ('SAME_RESULT','STICKY_BLOCKED_ROLLING_MULTIPLE','BOTH_HFT_BLOCKED','OTHER_DIFFERENCE')}}
    post={key:sum(bool(r[key]) for r in hft) for key in ('has_buy_within_60m_after_hft','has_buy_after_60m_after_hft','has_buy_after_45m_after_hft','observed_peak_drop_gt35','inventory_ge50pct_peak_after_hft_seen')}
    post.update(final_inventory_ge50pct_peak=sum(r['final_inventory_retention'] is not None and Decimal(r['final_inventory_retention'])>=Decimal('.5') for r in hft),
                unrecovered_distribution_veto=sum(r['unrecovered_distribution_evaluation_count']>0 for r in hft),
                finally_closed=sum(r['final_state']=='CLOSED' for r in hft),inventory_unresolved=sum(r['final_observed_inventory_raw'] is None for r in hft))
    candidates=[r for r in records if r['episode_id'] in new]
    # Separate rankings, fixed descending lexicographic dimensions. No outcome input.
    rankings={key:[r['episode_id'] for r in sorted(candidates,key=lambda r:(r[key] is not None, Decimal(str(r[key] or '0'))),reverse=True)]
              for key in ('post_first_hft_buys','buy_span_seconds','known_USDC_gross_buys','final_inventory_retention')}
    return {'study':'FRANK_HFT_STICKY_ROLLING_HISTORICAL_REPLAY_2026-10-04','history':hist,'metrics':stats,
            'recovery_sensitivity':sensitivity,'hft_post_behavior':post,'episodes':records,
            'behavior_rankings':rankings,'economic_ranking':{'status':'PNL_UNAVAILABLE','episodes':[]},
            'variant_summaries':{k:v['summary'] for k,v in variants.items()},
            'method':{'single_variable':'60-second HFT state, including causal WATCH consequences',
                      'evaluation_schedule':'Original Engine ACTIVE_TRADE plus hourly :29 only; no extra recovery ticks',
                      'R0':'inclusive count>=3; pass first second after expiry',
                      'R5':'R0 expiry plus 300 continuous non-HFT seconds',
                      'R15':'R0 expiry plus 900 continuous non-HFT seconds',
                      'roundtrip':'unchanged proven complete close within 1200 seconds; sticky until episode reset',
                      'amount':'USDC direct numeric; non-USDC without conversion UNDETERMINED',
                      'classification_partition':'new R0=>STICKY_BLOCKED; no A/B MULTIPLE plus HFT-only counterfactual=>BOTH_HFT_BLOCKED; identical first emission=>SAME_RESULT; remaining=>OTHER_DIFFERENCE'},
            'production_files_changed':False,'policy_changed':False,'live_service_restarted':False,
            'notifications_sent':0,'gmail_sent':0,'production_trading':'NO_GO'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
    p.add_argument('--policy',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    # All writes require a new workspace. Refuse live directories and known live DBs.
    if a.work.exists() or 'live' in a.work.name.lower() or a.source.name=='forward.sqlite':
        raise ValueError('ISOLATED_NEW_HISTORICAL_WORKSPACE_REQUIRED')
    a.work.mkdir(parents=True,mode=0o700)
    policy=load_policy(a.policy);verified=Ledger(a.work/'verified.sqlite')
    history=import_verified(a.source,verified);verified.db.close()
    variants={}
    for name,mode,recovery in [('CURRENT','CURRENT',0),('R0','ROLLING',0),('R5','ROLLING',300),('R15','ROLLING',900)]:
        variants[name]=run_variant(a.work/'verified.sqlite',a.work/(name+'.sqlite'),policy,mode,recovery)
    variants['_policy']=policy
    result=build_comparison(variants,history)
    result['input_source_name']=a.source.name
    result['input_source_sha256']=hashlib.sha256(a.source.read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'history':result['history'],'metrics':result['metrics'],'recovery_sensitivity':result['recovery_sensitivity']},indent=2))

if __name__=='__main__':main()
