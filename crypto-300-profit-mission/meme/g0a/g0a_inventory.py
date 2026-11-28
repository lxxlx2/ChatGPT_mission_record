"""Offline G0-A inventory. Private inputs are read-only; replays use temporary files.

Run with --help. Output contains aggregate counts and hashes, never private paths,
wallets, signatures, or raw transactions. No network fallback is permitted.
"""
import argparse
import collections
import gzip
import hashlib
import json
import sqlite3
import sys
import subprocess
import tarfile
import io
import shutil
import tempfile
from decimal import Decimal
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2] / 'local-agent'
HISTORICAL_CODE = '89135131dc1a8ae48890dbe6bfd4b98a03ad2b20'


def initialize(directory, study):
    """Export only local Git objects; pin the historical classifier/engine/policy."""
    global digest, classify, USDC, load_policy, USDT, WSOL, complex_candidate
    global pick_causal_candle, reconstruct, replay, research_market_record, PINNED_AGENT
    if study['production_boundary']['starting_HEAD'] != HISTORICAL_CODE:
        raise ValueError('HISTORICAL_CODE_IDENTITY_MISMATCH')
    raw = subprocess.run(['git', '-C', str(AGENT.parents[1]), 'archive', HISTORICAL_CODE,
                          'crypto-300-profit-mission/local-agent/mission_agent',
                          'crypto-300-profit-mission/local-agent/config'],
                         check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        archive.extractall(directory, filter='data')
    PINNED_AGENT = Path(directory) / 'crypto-300-profit-mission/local-agent'
    # The research helpers are unchanged existing repository logic, never their CLI.
    (PINNED_AGENT / 'scripts').mkdir()
    for name in ('frank_trade_coverage_historical_replay.py', 'frank_hft_sticky_rolling_historical_replay.py'):
        shutil.copyfile(AGENT / 'scripts' / name, PINNED_AGENT / 'scripts' / name)
    expected = study['production_boundary']['production_sha256_before']
    for name, value in expected.items():
        if name.startswith(('mission_agent/', 'config/')) and sha(PINNED_AGENT / name) != value:
            raise ValueError('HISTORICAL_CODE_HASH_MISMATCH')
    sys.path.insert(0, str(PINNED_AGENT))
    from mission_agent.hashing import digest
    from mission_agent.signals.classifier import classify
    from mission_agent.signals.policy import USDC, load_policy
    from scripts.frank_trade_coverage_historical_replay import (
        USDT, WSOL, complex_candidate, pick_causal_candle, reconstruct,
        replay, research_market_record,
    )

BUY = {'BUY', 'ADD', 'REENTRY'}
SELL = {'SELL', 'EXIT', 'SELL_POSITION_UNRESOLVED'}
STUDY = Path(__file__).resolve().parents[1] / 'evidence/frank-trade-coverage-sol-usdt-complex-2026-10-04.json'


def ro(path):
    if path is None or not path.is_file():
        raise ValueError('INPUT_UNAVAILABLE')
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    return db


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verified_rows(path, expected):
    """Same raw/classifier checks as import_verified(), with query_only on source.

    Keep rows in memory instead of importing them to a durable target ledger.
    Missing raw or classification drift fails closed, before any denominator.
    """
    db = ro(path)
    try:
        rows = db.execute('SELECT * FROM signatures ORDER BY block_time,slot,signature').fetchall()
    finally:
        db.close()
    if not rows:
        raise ValueError('EMPTY_HISTORY')
    identities, manifest, txs, counts = set(), [], {}, collections.Counter()
    for row in rows:
        identity = (row['wallet'], row['signature'])
        if identity in identities:
            raise ValueError('DUPLICATE_WALLET_SIGNATURE')
        identities.add(identity)
        raw_path = Path(row['raw_reference'])
        if not raw_path.is_file():
            raise ValueError('RAW_UNAVAILABLE')
        raw = json.loads(gzip.decompress(raw_path.read_bytes()))
        tx = raw['transaction'] if 'status' in raw and 'signature' in raw else raw
        if 'status' in raw and 'signature' in raw and raw['signature'] != row['signature']:
            raise ValueError('RAW_SIGNATURE_BINDING')
        h = hashlib.sha256(json.dumps(tx, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        if h != row['raw_hash']:
            raise ValueError('RAW_HASH_CONFLICT')
        signed = tx.get('transaction', {}).get('signatures')
        if signed is not None and row['signature'] not in signed:
            raise ValueError('RAW_CHAIN_SIGNATURE_BINDING')
        actual, old = classify(row['signature'], tx, row['wallet']), json.loads(row['body'])
        for key in ('classification', 'trade', 'block_time', 'slot', 'wallet', 'frank_is_signer'):
            if actual.get(key) != old.get(key):
                raise ValueError('CLASSIFICATION_DRIFT_' + key)
        if actual['signature'] != row['signature'] or actual['wallet'] != row['wallet']:
            raise ValueError('IDENTITY_BINDING')
        counts[actual['classification']] += 1
        manifest.append({'wallet': row['wallet'], 'signature': row['signature'], 'raw_hash': h})
        txs[identity] = tx
    if (len(rows) != expected['usable_signatures'] or dict(counts) != expected['classification_counts']
            or digest(manifest) != expected['chronology_sha256']):
        raise ValueError('ARCHIVED_HISTORY_MISMATCH')
    return rows, txs, {'status': 'VERIFIED', 'usable_signatures': len(rows),
        'raw_hash_verified': len(rows), 'duplicate_wallet_signatures': 0,
        'classification_counts': dict(counts), 'chronology_sha256': digest(manifest),
        'database_sha256': sha(path)}


class OfflinePrices:
    """Only archived study receipts. Never calls HistoricalPrices.get()."""
    def __init__(self, receipts):
        self.receipts = receipts

    def get(self, asset, at):
        if asset == USDC:
            return {'price': '1', 'source': 'FROZEN_V1_USDC_DIRECT_NUMERIC_NOT_PRICE_CONVERSION'}
        symbol = 'SOL-USD' if asset in ('SOL', WSOL) else 'USDT-USD' if asset == USDT else None
        if at is None or symbol is None:
            return None
        matches = [r for r in self.receipts if '/products/' + symbol + '/' in r['endpoint']
                   and r['requested_bucket_start'] == (at // 60 - 1) * 60]
        if len(matches) != 1:
            return None
        receipt = matches[0]
        value = pick_causal_candle(receipt.get('candles', []), at)
        return {**value, 'source': receipt['source'], 'endpoint': receipt['endpoint'],
                'response_sha256': receipt.get('response_sha256')} if value else None


def metrics(records, episode_map):
    identities = {(r['wallet'], r['signature']) for r in records}
    episodes = {episode_map[i] for i in identities if i in episode_map and episode_map[i]}
    return {'signatures': len(identities), 'episodes': len(episodes),
            'mints': len({r['trade']['mint'] for r in records}),
            'episode_unresolved_signatures': sum(not episode_map.get(i) for i in identities)}


def amounts_available(record):
    """Own event-time quote/token ratio, denominated in original quote, not USD."""
    t = record['trade']
    try:
        token = Decimal(t['token_amount_raw']) / Decimal(10) ** t['token_decimals']
        quote = Decimal(t['quote_amount_raw']) / Decimal(10) ** t['quote_decimals']
        return token > 0 and quote > 0 and (quote / token).is_finite()
    except (KeyError, ArithmeticError, TypeError):
        return False


def summarize_model(rows, data, original, additions):
    records, mapping = [], {}
    # Engine evaluations preserve historical episode IDs, including closed episodes.
    by_sig = collections.defaultdict(list)
    for row in rows:
        by_sig[row['signature']].append(row['wallet'])
    for e in data['evaluations']:
        if json.loads(e['body'])['kind'] == 'ACTIVE_TRADE':
            wallets = by_sig[e['signature']]
            if len(wallets) != 1:
                raise ValueError('AMBIGUOUS_REPLAY_SIGNATURE')
            mapping[(wallets[0], e['signature'])] = e['episode_id']
    for row in rows:
        r = json.loads(row['body'])
        added = additions.get(row['signature'])
        if added:
            r = {**r, 'classification': 'ACTIVE_TRADE', 'trade': added['trade']}
        if r['classification'] == 'ACTIVE_TRADE':
            records.append(r)
    directions = collections.Counter(r['trade'].get('direction', 'UNKNOWN') for r in records)
    if directions.keys() - {'BUY', 'SELL'}:
        raise ValueError('ACTIVE_DIRECTION_UNRESOLVED')
    signals = data['signals']
    groups, subsets = {}, {}
    buys = [r for r in records if r['trade']['direction'] == 'BUY']
    for label, subset in [('ALL_ACTIVE_BUY', buys), ('ACTIVE_SELL', [r for r in records if r['trade']['direction'] == 'SELL'])]:
        subsets[label] = subset
        groups[label] = metrics(subset, mapping)
    signal_eps = {s['episode_id'] for s in signals}
    subsets['OTHER_ACTIVE_BUY_OUTSIDE_SIGNAL_EPISODES'] = [
        r for r in buys if mapping.get((r['wallet'], r['signature'])) not in signal_eps]
    groups['OTHER_ACTIVE_BUY_OUTSIDE_SIGNAL_EPISODES'] = metrics(
        subsets['OTHER_ACTIVE_BUY_OUTSIDE_SIGNAL_EPISODES'], mapping)
    for kind in ('FRANK_ACCUMULATION_SIGNAL', 'FRANK_MULTIPLE_SIGNAL'):
        ss = [s for s in signals if s['signal_type'] == kind]
        eps = {s['episode_id'] for s in ss}
        subset = [r for r in buys if mapping.get((r['wallet'], r['signature'])) in eps]
        subsets[kind] = subset
        trigger_ids = {s['triggering_signature'] for s in ss}
        groups[kind] = {**metrics(subset, mapping), 'signal_events': len(ss),
                       'signal_episodes': len(eps), 'signal_mints': len({s['mint'] for s in ss}),
                       'trigger_BUY_signatures': len({r['signature'] for r in buys if r['signature'] in trigger_ids})}
    subsets['SIGNAL_UNION'] = [r for r in buys if mapping.get((r['wallet'], r['signature'])) in signal_eps]
    groups['SIGNAL_UNION'] = {**metrics([r for r in buys if mapping.get((r['wallet'], r['signature'])) in signal_eps], mapping),
                              'signal_events': len(signals), 'signal_episodes': len(signal_eps),
                              'signal_mints': len({s['mint'] for s in signals})}
    # Price coverage uses original chain quote fields, never synthetic M3 USD fields.
    own = []
    for r in buys:
        o = original[(r['wallet'], r['signature'])]
        if o['classification'] == 'ACTIVE_TRADE' and amounts_available(o):
            own.append(o)
    for label, subset in subsets.items():
        original_prices = [original[(r['wallet'], r['signature'])] for r in subset
                           if original[(r['wallet'], r['signature'])]['classification'] == 'ACTIVE_TRADE'
                           and amounts_available(original[(r['wallet'], r['signature'])])]
        groups[label]['original_event_quote_token_ratios'] = metrics(original_prices, mapping)
    if groups['ALL_ACTIVE_BUY']['signatures'] != (groups['SIGNAL_UNION']['signatures'] +
            groups['OTHER_ACTIVE_BUY_OUTSIDE_SIGNAL_EPISODES']['signatures']):
        raise ValueError('BUY_GROUP_PARTITION_CONFLICT')
    return {'ACTIVE_BUY': directions['BUY'], 'ACTIVE_SELL': directions['SELL'],
            'ACTIVE_TOTAL': len(records), 'groups': groups,
            'original_chain_BUY_quote_token_ratios': metrics(own, mapping),
            'recovered_BUY_excluded_from_original_trade_ratio_count': sum(
                original[(r['wallet'], r['signature'])]['classification'] != 'ACTIVE_TRADE' for r in buys)}


def runtime_inventory(path):
    if path is None or not path.is_file():
        return {'status': 'UNRESOLVED', 'reason': 'OPTIONAL_RUNTIME_SNAPSHOT_UNAVAILABLE'}
    db = ro(path)
    try:
        rows = db.execute('SELECT wallet,signature,mint,episode_id,side,body FROM trades').fetchall()
        counts = collections.Counter(r['side'] for r in rows)
        def count(sides):
            rr = [r for r in rows if r['side'] in sides]
            return {'signatures': len({(r['wallet'], r['signature']) for r in rr}),
                    'episodes': len({r['episode_id'] for r in rr if r['episode_id']}),
                    'mints': len({r['mint'] for r in rr})}
        keys = collections.Counter(k for r in rows for k in json.loads(r['body']))
        return {'status': 'AVAILABLE' if rows else 'UNRESOLVED', 'rows': len(rows),
                'side_counts': dict(counts), 'BUY': count(BUY), 'SELL': count(SELL),
                'UNKNOWN': count(set(counts) - BUY - SELL), 'observed_trade_body_keys': sorted(keys)}
    finally:
        db.close()


def cache_inventory(path):
    if path is None or not path.is_dir():
        return {'status': 'UNRESOLVED', 'reason': 'OPTIONAL_CACHE_UNAVAILABLE'}
    files = list(path.glob('*/*.json'))
    txs, other = 0, 0
    for p in files:
        value = json.loads(p.read_text())
        if isinstance(value, dict) and isinstance(value.get('tx'), dict) and 'transaction' in value['tx']:
            txs += 1
        else:
            other += 1
    return {'status': 'AVAILABLE' if files else 'UNRESOLVED', 'json_files': len(files),
            'getTransaction_wrappers': txs, 'other_schema_files': other,
            'price_series_assessment': 'MANUAL_SOURCE_INSPECTION_REQUIRED; raw transaction counts are not delayed quotes'}


def inventory(args):
    s = json.loads(args.study.read_text())
    out = {'status': 'G0_A_PARTIAL', 'study_sha256': sha(args.study),
           'scope': 'KNOWN_DEVELOPMENT_HISTORY_NOT_INDEPENDENT_OOS',
           'historical_code_commit': HISTORICAL_CODE,
           'historical_protected_hashes_match': True,
           'runtime': runtime_inventory(args.runtime_db), 'cache': cache_inventory(args.cache_dir)}
    if args.source is None or not args.source.is_file():
        return {**out, 'history': {'status': 'UNRESOLVED', 'reason': 'HISTORY_SOURCE_UNAVAILABLE'}}
    source_hash_before = sha(args.source)
    rows, txs, out['history'] = verified_rows(args.source, s['history'])
    originals = {(r['wallet'], r['signature']): json.loads(r['body']) for r in rows}
    if len({r['signature'] for r in rows}) != len(rows):
        raise ValueError('RESEARCH_REPLAY_REQUIRES_UNIQUE_SIGNATURES')
    prices = OfflinePrices(s['price_receipts'])
    additions, computed_cases = {}, {}
    for row in rows:
        r = originals[(row['wallet'], row['signature'])]
        if complex_candidate(r):
            research = research_market_record(r, txs[(row['wallet'], row['signature'])])
            trade, details = reconstruct(research, prices, allow_complex=True)
            computed_cases[row['signature']] = details
            if trade:
                additions[row['signature']] = {'trade': trade, 'evidence': research['evidence']}
    archived = {c['signature']: c for c in s['COMPLEX']['cases']}
    if len(archived) != len(s['COMPLEX']['cases']) or set(archived) != set(computed_cases):
        raise ValueError('COMPLEX_CASE_SET_MISMATCH')
    for sig, c in computed_cases.items():
        for k in ('original_classification', 'category', 'shadow_trade'):
            if c.get(k) != archived[sig].get(k):
                raise ValueError('COMPLEX_RECONSTRUCTION_MISMATCH')
    restored = [originals[(r['wallet'], r['signature'])] for r in rows if r['signature'] in additions]
    if any(r['classification'] == 'ACTIVE_TRADE' for r in restored):
        raise ValueError('RESTORATION_OVERLAPS_BASELINE_ACTIVE')
    out['M3_recovery'] = {'candidate_cases': len(computed_cases), 'unique_restored_signatures': len(additions),
        'directions': dict(collections.Counter(a['trade']['direction'] for a in additions.values())),
        'original_classes': dict(collections.Counter(r['classification'] for r in restored)),
        'archived_cases_match': True, 'raw_bound_reconstruction': True}
    policy = load_policy(PINNED_AGENT / 'config/frank_local_signal_v1.json')
    with tempfile.TemporaryDirectory(prefix='g0a-offline-') as directory:
        for label, model in [('J0', 0), ('M3', 3)]:
            data = replay(Path(directory) / (label + '.sqlite'), rows, policy, model, prices, {}, additions)
            if data['signals'] != s['models']['M0' if model == 0 else 'M3']['signals']:
                raise ValueError(label + '_ARCHIVED_SIGNAL_DRIFT')
            out[label] = summarize_model(rows, data, originals, additions if model else {})
            if out[label]['ACTIVE_TOTAL'] != s['models']['M0' if model == 0 else 'M3']['ACTIVE_TRADE']:
                raise ValueError('MODEL_ACTIVE_COUNT_DRIFT')
            if model == 0:
                if args.baseline and args.baseline.is_file():
                    db = ro(args.baseline)
                    try:
                        old = [json.loads(r[0]) for r in db.execute('SELECT body FROM signals ORDER BY signal_id')]
                    finally:
                        db.close()
                    if sorted(old, key=lambda x: x['signal_id']) != sorted(data['signals'], key=lambda x: x['signal_id']):
                        raise ValueError('PRIVATE_BASELINE_SIGNAL_DRIFT')
                    out['baseline'] = {'status': 'VERIFIED', 'signal_count': len(old), 'database_sha256': sha(args.baseline)}
                else:
                    out['baseline'] = {'status': 'UNRESOLVED', 'reason': 'PRIVATE_BASELINE_UNAVAILABLE; archived signals matched'}
    out['price_assessment_method'] = 'MANUAL_SOURCE_INSPECTION of archived reports and inspected DB/cache schemas; no delayed quote dataset supplied'
    out['delay_price_evidence'] = {str(delay): {
        'verified_executable_quote_records': 0,
        'evidence_grade': 'MANUAL_SOURCE_INSPECTION; not a market-wide absence proof',
        'status': 'NO_VERIFIED_RECORDS_IN_INSPECTED_SOURCES; NOT_MARKET_PRICE_ABSENCE',
        'pool_OHLCV': 'UNRESOLVED; manual archived report has 3/18 M3 signal mints at 5m, no raw response/time join',
        'own_trade_price': 'EVENT_TIME_QUOTE_TOKEN_RATIO_ONLY; not a follower delay price',
    } for delay in (30, 120, 300)}
    if sha(args.source) != source_hash_before:
        raise ValueError('HISTORY_SOURCE_CHANGED_DURING_RUN')
    out['history']['source_bytes_unchanged'] = True
    out['research_helper_sha256'] = {name: sha(AGENT / 'scripts' / name) for name in (
        'frank_trade_coverage_historical_replay.py', 'frank_hft_sticky_rolling_historical_replay.py')}
    out['status'] = 'G0_A_COMPLETE' if out['baseline']['status'] == 'VERIFIED' else 'G0_A_PARTIAL'
    return out


def deny_network(event, arguments):
    if event in ('socket.connect', 'socket.getaddrinfo', 'urllib.Request'):
        raise RuntimeError('NETWORK_FORBIDDEN')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'baseline', 'runtime-db', 'cache-dir'):
        p.add_argument('--' + name, type=Path)
    p.add_argument('--study', type=Path, default=STUDY)
    args = p.parse_args()
    sys.addaudithook(deny_network)
    try:
        with tempfile.TemporaryDirectory(prefix='g0a-code-') as directory:
            initialize(directory, json.loads(args.study.read_text()))
            out = inventory(args)
    except (ValueError, OSError, sqlite3.Error, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        # Do not leak SQLite/raw paths or identifiers via exception messages.
        safe = str(exc) if isinstance(exc, ValueError) and str(exc).replace('_', '').isalnum() and str(exc).upper() == str(exc) else type(exc).__name__
        out = {'status': 'G0_A_PARTIAL', 'history': {'status': 'UNRESOLVED', 'reason': safe}}
        print(json.dumps(out, indent=2))
        return 1
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
