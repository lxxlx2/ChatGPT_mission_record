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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', type=Path, required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--expected-agent-sha', default='e977cc09023bdfcc9ce80660aedf2d58d2febc5f')
    args = parser.parse_args()
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
    collect_pool = pool_vaults.collect_pool_vault_snapshot
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
                with patch.object(cluster.time, 'time', return_value=report['observed_at']), \
                        patch.object(pool_vaults, 'collect_pool_vault_snapshot', historical_pool_clock):
                    analyzer = cluster.WalletClusterAnalyzer(
                        meta['mint'], rpc=rpc,
                        special_registry=cluster.load_registry(args.agent / 'config/meme_special_addresses.json'),
                        **CLUSTER_PRESETS[meta['preset']], **clients)
                    actual = analyzer.analyze()
                rpc.assert_can_publish()
                assert actual == expected, 'BUSINESS_REPORT_MISMATCH:' + ','.join(
                    k for k in set(actual) | set(expected) if actual.get(k) != expected.get(k))
                assert cp.replayed == cp.index == meta['entry_count']
                digests.append(hashlib.sha256(canonical(actual).encode()).hexdigest())
                entries = cp.entries
            finally:
                cp.close()
    assert digests[0] == digests[1]
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
        'report_business_equal_each': True,
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
    (args.capture / 'offline-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
