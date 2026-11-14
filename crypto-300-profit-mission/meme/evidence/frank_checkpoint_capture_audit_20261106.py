#!/usr/bin/env python3
"""Audit a private DONE capture offline; never collect or resume a live job.

Inputs stay private. Only sanitized counts and digests are printed/written.
Example: python -I -B this_file.py --agent /fixed/agent --capture /private/capture
The capture contains checkpoint.sqlite, report.json and status-current.json.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import socket
import sqlite3
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.request
from unittest.mock import patch

sys.dont_write_bytecode = True


def check_retention_coverage(actual, raw_rows):
    """Reconstruct representatives and counts from admitted original source rows."""
    def group(row):
        return tuple(row[k] for k in ('owner','account','balance_phase','closure_at_transaction_end'))
    representatives={};rejected=0
    for row in raw_rows:
        key=group(row)
        if key not in representatives:
            if len(representatives)==200:
                rejected+=1;continue
            representatives[key]=row
        elif row['slot']<representatives[key]['slot']:
            representatives[key]=row
    retained=actual['historical_account_evidence']
    assert retained==list(representatives.values()), 'RETAINED_PROOF_NOT_OLDEST_VALID_SOURCE'
    pairs={(r['owner'],r['account']) for r in retained}
    metadata={'version':1,'mode':'OLDEST_VALID_PER_OWNER_ACCOUNT_PHASE_CLOSURE_STATUS',
              'raw_valid_observations':len(raw_rows),'retained_observations':len(retained),
              'compacted_observations':len(raw_rows)-len(retained)-rejected,
              'limit_rejected_observations':rejected,'represented_owner_accounts':len(pairs),
              'max_observations':200,'complete_history':False}
    assert actual['coverage']['historical_account_retention']==metadata
    return metadata


def check_retention_change(actual, expected, raw_rows, canonical):
    """Check a representative-only derivation against original source records."""
    metadata=check_retention_coverage(actual,raw_rows)
    retained=actual['historical_account_evidence']
    pairs={(r['owner'],r['account']) for r in retained}
    rejected=metadata['limit_rejected_observations']
    old_pairs={(r['owner'],r['account']) for r in expected['historical_account_evidence']}
    def frontier(rows):
        out={}
        for row in rows:
            key=row['owner'],row['account']
            if key not in out or row['slot']<out[key]['slot']:out[key]=row
        return out
    discovered=frontier(retained);previous=frontier(expected['historical_account_evidence'])
    selected={(r['owner'],a) for r in expected['coverage']['owner_account_history'] for a in r['accounts_selected']}
    assert set(discovered)<=selected, 'NEW_SUFFIX_READ_REQUIRED; NOT_RETENTION_ONLY_CAPTURE'
    plans=[{'owner':owner,'account':account,'discovery_signature':row['signature'],
            'discovery_slot':row['slot'],'selected':False,
            'stop_reason':'CURRENT_ACCOUNT_ALREADY_SELECTED','history_complete':False}
           for (owner,account),row in sorted(discovered.items(),key=lambda p:(p[0][0],p[1]['slot'],p[0][1]))]
    assert actual['coverage']['historical_account_history']==plans, 'FRONTIER_NOT_BOUND_TO_RETAINED_PROOFS'
    comparison=json.loads(canonical(actual));baseline=json.loads(canonical(expected))
    for doc in (comparison,baseline):
        doc.pop('historical_account_evidence')
        doc['coverage'].pop('historical_account_history')
    comparison['coverage'].pop('historical_account_retention')
    gaps=set(baseline['coverage']['gaps'])-{'HISTORICAL_ACCOUNT_EVIDENCE_LIMIT','HISTORICAL_ACCOUNT_EVIDENCE_COMPACTED'}
    if rejected:gaps.add('HISTORICAL_ACCOUNT_EVIDENCE_LIMIT')
    if metadata['compacted_observations']:gaps.add('HISTORICAL_ACCOUNT_EVIDENCE_COMPACTED')
    assert set(comparison['coverage']['gaps'])==gaps, 'UNRELATED_COVERAGE_GAP_CHANGE'
    comparison['coverage'].pop('gaps');baseline['coverage'].pop('gaps')
    assert comparison==baseline, 'UNRELATED_REPORT_CHANGE'
    return {'allowed_changes':['historical_account_evidence','coverage.historical_account_history',
                               'coverage.historical_account_retention','coverage.gaps'],
            'retention':metadata,'prior_retained_observations':len(expected['historical_account_evidence']),
            'prior_owner_accounts':len(old_pairs),'restored_current_owner_accounts':len(pairs-old_pairs),
            'earlier_owner_account_proofs':sum(key in previous and row['slot']<previous[key]['slot'] for key,row in discovered.items()),
            'new_noncurrent_owner_accounts':len(pairs-selected),
            'unaffected_report_fields_equal':True,'all_representatives_original_source_rows':True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', type=Path, required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--expected-agent-sha', default='e977cc09023bdfcc9ce80660aedf2d58d2febc5f')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--retention-change-only', action='store_true', help='Verify a representative-only derivation without additional suffix reads')
    parser.add_argument('--derived-report', type=Path)
    args = parser.parse_args()
    protected_inputs={(args.capture/name).resolve() for name in
                      ('report.json','checkpoint.sqlite','status-current.json','done-marker.json','private-plan.json')}
    for output in (args.output,args.derived_report):
        assert output is None or output.resolve() not in protected_inputs, 'CAPTURE_INPUT_MUST_NOT_BE_OVERWRITTEN'
    source_sha = subprocess.check_output(['git', '-C', str(args.agent), 'rev-parse', 'HEAD'], text=True).strip()
    assert source_sha == args.expected_agent_sha and len(source_sha)==40, 'SOURCE_SHA_CHANGED'
    assert not subprocess.check_output(['git', '-C', str(args.agent), 'status', '--porcelain', '--', 'mission_agent', 'config'], text=True)
    sys.path.insert(0, str(args.agent.resolve()))
    from mission_agent.meme import cluster
    from mission_agent.meme import pool_vaults
    from mission_agent.meme.job_checkpoint import JobCheckpoint, CheckpointRPC, CheckpointClient, canonical
    from mission_agent.mission_control.server import CLUSTER_PRESETS
    from mission_agent.signals.classifier import classify

    report_bytes = (args.capture / 'report.json').read_bytes()
    report = json.loads(report_bytes)
    status = json.loads((args.capture / 'status-current.json').read_bytes())
    with sqlite3.connect((args.capture / 'checkpoint.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as db:
        meta = json.loads(db.execute('SELECT body FROM metadata WHERE id=1').fetchone()[0])
    assert status['status'] == meta['status'] == 'DONE'
    assert report['ca_job_id'] == status['job_id'] == meta['job_id']
    counts = Counter()

    def deny(*unused, **kwargs):
        counts['network_attempts_blocked'] += 1
        raise AssertionError('NETWORK_DENIED')

    for name in ('socket', 'SocketType', 'socketpair', 'fromfd', 'create_connection',
                 'getaddrinfo', 'gethostbyname', 'gethostbyname_ex', 'gethostbyaddr'):
        setattr(socket, name, deny)
    urllib.request.urlopen = deny
    urllib.request.OpenerDirector.open = deny

    class DeniedRPC:
        endpoint = 'https://offline.invalid/rpc'
        endpoints = [endpoint]
        def __init__(self):
            self._last_by_endpoint = {}
            self._cooldown_until = {}
            self._monotonic = time.monotonic
        call = staticmethod(deny)
        def assert_can_publish(self):
            return None

    class DeniedClient:
        token_snapshot = pool_snapshot = collect = staticmethod(deny)

    expected = json.loads(report_bytes)
    augmentation = ['ca_job_id', 'assessment_history', 'assessment_history_context', 'collection_checkpoint']
    for key in augmentation:
        expected.pop(key, None)
    expected['coverage'].pop('rpc_call_count_scope', None)
    digests = []
    entries = None
    retention_result=None
    retention_coverage=None
    collect_pool = pool_vaults.collect_pool_vault_snapshot
    original_observer=cluster.observe_token_accounts
    def historical_pool_clock(*values, **kwargs):
        # This is a locally derived receipt timestamp, distinct from the final
        # report timestamp. Freeze both to their recorded values, without
        # changing any source payload, TTL, deadline or business field.
        with patch.object(cluster.time, 'time', return_value=report['pool_vaults']['observed_at']):
            return collect_pool(*values, **kwargs)
    for _ in range(2):
        with tempfile.TemporaryDirectory(prefix='frank-captured-journal-') as temp:
            journal = Path(temp)
            journal.chmod(0o700)
            target = journal / (meta['job_id'] + '.sqlite')
            shutil.copyfile(args.capture / 'checkpoint.sqlite', target)
            target.chmod(0o600)
            cp = JobCheckpoint(journal, meta['job_id'], readonly=True, clock=lambda: meta['last_saved_at'])
            try:
                rpc = CheckpointRPC(cp, DeniedRPC())
                clients = {key: CheckpointClient(cp, DeniedClient(), key) for key in
                           ('market_client', 'independent_market_client', 'narrative_client')}
                raw_rows=[]
                def observe(*values, **kwargs):
                    rows=original_observer(*values, **kwargs)
                    raw_rows.extend(json.loads(canonical(rows)))
                    return rows
                with patch.object(cluster.time, 'time', return_value=report['observed_at']), \
                        patch.object(pool_vaults, 'collect_pool_vault_snapshot', historical_pool_clock), \
                        patch.object(cluster, 'observe_token_accounts', observe):
                    analyzer = cluster.WalletClusterAnalyzer(
                        meta['mint'], rpc=rpc,
                        special_registry=cluster.load_registry(args.agent / 'config/meme_special_addresses.json'),
                        **CLUSTER_PRESETS[meta['preset']], **clients)
                    actual = analyzer.analyze()
                rpc.assert_can_publish()
                if 'historical_account_retention' in actual['coverage']:
                    retention_coverage=check_retention_coverage(actual,raw_rows)
                if args.retention_change_only:
                    retention_result=check_retention_change(actual,expected,raw_rows,canonical)
                else:
                    assert actual == expected, 'BUSINESS_REPORT_MISMATCH:' + ','.join(
                        k for k in set(actual) | set(expected) if actual.get(k) != expected.get(k))
                assert cp.replayed == cp.index == meta['entry_count']
                digests.append(hashlib.sha256(canonical(actual).encode()).hexdigest())
                entries = cp.entries
            finally:
                cp.close()
    assert digests[0] == digests[1]
    if args.retention_change_only:
        report=actual
    if args.derived_report:
        assert args.retention_change_only and args.derived_report.resolve()!=(args.capture/'report.json').resolve()
        args.derived_report.write_text(json.dumps(actual,indent=2)+'\n')
    txs = {}
    for entry in entries:
        request = entry['request']
        if request['channel'] == 'rpc' and request['operation'] == 'getTransaction' and entry['outcome'] == 'OK':
            signature = request['args'][0][0]
            value = entry['response']
            if signature in txs:
                assert txs[signature] == value, 'TRANSACTION_CAPTURE_CHANGED'
            txs[signature] = value
    def success(tx):
        return isinstance(tx, dict) and isinstance(tx.get('meta'), dict) and 'err' in tx['meta'] and tx['meta']['err'] is None
    for field in ('trade_evidence', 'funding_evidence', 'consolidation_evidence', 'edges', 'historical_account_evidence'):
        rows = report[field]
        counts[field + '_checked'] = len(rows)
        serialized = [canonical(row) for row in rows]
        counts[field + '_exact_duplicates'] = len(rows) - len(set(serialized))
        assert counts[field + '_exact_duplicates'] == 0
        for row in rows:
            signature = row.get('signature')
            if signature and signature not in ('MULTI_TX', 'STRUCTURAL'):
                assert success(txs.get(signature)), field + '_UNVERIFIED_SUCCESS'
    keys = [(row['owner'], row['signature']) for row in report['trade_evidence']]
    assert len(keys) == len(set(keys)), 'DUPLICATE_OWNER_TRADE'
    for row in report['trade_evidence']:
        classified = classify(row['signature'], txs[row['signature']], row['owner'])
        trade = classified.get('trade') or {}
        assert classified['classification'] == 'ACTIVE_TRADE' and trade['mint'] == report['mint']
        for key in ('direction', 'quote_asset', 'quote_amount_raw', 'quote_decimals', 'token_amount_raw', 'token_decimals'):
            assert row.get(key) == trade.get(key), 'TRADE_RECLASSIFICATION_MISMATCH'
    for row in report['funding_evidence']:
        tx = txs[row['signature']]
        assert (row['source'], str(row['lamports'])) in cluster._native_funders(tx, row['owner'])
        anchor = txs[row['acquisition_signature']]
        assert success(anchor)
        first = classify(row['acquisition_signature'], anchor, row['owner'])
        assert first['classification'] == 'ACTIVE_TRADE'
        assert first['trade']['mint'] == report['mint'] and first['trade']['direction'] == 'BUY'
        assert tx['blockTime'] == row['block_time'] <= anchor['blockTime']
    for row in report['historical_account_evidence']:
        tx = txs[row['signature']]
        assert row['mint'] == report['mint'] and row['slot'] == tx['slot']
        assert row['response_sha256'] == hashlib.sha256(canonical(tx).encode()).hexdigest()
    signature_pages = {}
    for entry in entries:
        request = entry['request']
        if request['channel'] == 'rpc' and request['operation'] == 'getSignaturesForAddress' and entry['outcome'] == 'OK':
            address = request['args'][0][0]
            signature_pages.setdefault(address, set()).update(x['signature'] for x in entry['response'])
    for window in report['coverage']['history_windows']:
        assert 0 <= window['pages'] <= window['page_limit']
        if window.get('next_before'):
            assert window['next_before'] in signature_pages[window['address']], 'CURSOR_NOT_IN_CAPTURE'
    counts['history_windows_with_preserved_cursor'] = sum(bool(x.get('next_before')) for x in report['coverage']['history_windows'])
    assert counts['network_attempts_blocked'] == 0
    result = {
        'verdict': 'PASS_OFFLINE_CAPTURE_AUDIT',
        'source_sha': source_sha,
        'scope': 'Historical logical-response replay; not fresh wire capture or live crash/resume',
        'report_sha256': hashlib.sha256(report_bytes).hexdigest(),
        'checkpoint_chain_head': meta['head'],
        'replay_count': 2, 'logical_reads_each': len(entries),
        'report_business_equal_each': not args.retention_change_only,
        'report_retention_only_change_verified_each': bool(args.retention_change_only),
        'retention_change': retention_result,
        'retention_coverage_verified_each': retention_coverage is not None,
        'retention_coverage': retention_coverage,
        'derived_report_json_sha256': hashlib.sha256(args.derived_report.read_bytes()).hexdigest() if args.derived_report else None,
        'business_report_sha256_each': digests,
        'excluded_worker_augmentation_root_keys': augmentation,
        'excluded_worker_augmentation_coverage_keys': ['rpc_call_count_scope'],
        'locally_derived_timestamps_frozen': ['observed_at', 'pool_vaults.observed_at'],
        'clock_frozen_to_original_report': True, 'cache_ttls_modified': False,
        'unique_captured_transactions': len(txs),
        'captured_failed_transactions': sum(isinstance(v, dict) and isinstance(v.get('meta'), dict) and v['meta'].get('err') is not None for v in txs.values()),
        'captured_null_transactions': sum(v is None for v in txs.values()),
        'counts': dict(counts), 'new_wire_attempts': 0,
        'network_attempts_blocked': counts['network_attempts_blocked'],
        'live_resume_count': meta['resume_count'],
    }
    (args.output or args.capture / 'offline-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
