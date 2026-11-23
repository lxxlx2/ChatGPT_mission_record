#!/usr/bin/env python3
"""FLOP research agent: read-only collector, ledger, dashboard, offline acceptance.
No faucet, signing, submit, payment, or daemon installation functions exist.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('FLOP_AGENT_DATA_DIR', '~/.local/share/flop-agent')).expanduser()
ENDPOINTS = {
    'network_commits': 'https://api.github.com/repos/flop-labs/network/commits?per_page=12',
    'network_releases': 'https://api.github.com/repos/flop-labs/network/releases?per_page=12',
    'yellowpaper_commits': 'https://api.github.com/repos/flop-labs/yellowpaper/commits?per_page=12',
}

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')

def db(path=None):
    target = Path(path) if path else DATA / 'ledger.sqlite3'
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    conn = sqlite3.connect(target, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.executescript('''
      CREATE TABLE IF NOT EXISTS evidence (
        fingerprint TEXT PRIMARY KEY, source TEXT NOT NULL,
        url TEXT NOT NULL, title TEXT NOT NULL, observed_utc TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'DISCOVERED_READ_ONLY');
      CREATE TABLE IF NOT EXISTS receipts (
        request_id TEXT PRIMARY KEY, wallet TEXT NOT NULL,
        channel_id TEXT NOT NULL, test_flop_spent TEXT NOT NULL,
        claimed_status TEXT NOT NULL, verified_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
        observed_utc TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS checks (
        time_utc TEXT NOT NULL, name TEXT NOT NULL, outcome TEXT NOT NULL);
    ''')
    conn.commit()
    return conn

def fetch_json(url):
    req = Request(url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'flop-agent-readonly/0.2'})
    with urlopen(req, timeout=12) as response:
        return json.loads(response.read(2_000_000))

def normalize(source, obj):
    if not isinstance(obj, dict):
        return None
    if source.endswith('commits'):
        ident = obj.get('sha')
        title = (obj.get('commit') or {}).get('message', '').split('\n')[0]
        url = obj.get('html_url')
    else:
        ident = obj.get('id')
        title = obj.get('name') or obj.get('tag_name')
        url = obj.get('html_url')
    if not ident or not title or not url or not str(url).startswith('https://github.com/flop-labs/'):
        return None
    fingerprint = hashlib.sha256((source + ':' + str(ident)).encode()).hexdigest()
    return (fingerprint, source, str(url), str(title)[:240], utc())

def collect(conn, fetch=fetch_json):
    added, failures = 0, {}
    for source, url in ENDPOINTS.items():
        try:
            records = fetch(url)
            if not isinstance(records, list):
                raise ValueError('Unexpected GitHub API shape')
            for obj in records:
                entry = normalize(source, obj)
                if entry:
                    cur = conn.execute('INSERT OR IGNORE INTO evidence(fingerprint,source,url,title,observed_utc) VALUES (?,?,?,?,?)', entry)
                    added += cur.rowcount
            conn.execute('INSERT INTO checks VALUES (?,?,?)', (utc(), source, 'READ_OK'))
        except (OSError, HTTPError, URLError, ValueError, TimeoutError) as exc:
            failures[source] = type(exc).__name__
            conn.execute('INSERT INTO checks VALUES (?,?,?)', (utc(), source, 'SOURCE_GAP:' + type(exc).__name__))
    conn.commit()
    return {'new_public_items': added, 'source_gaps': failures, 'status': 'READ_ONLY_NO_AIRDROP_CREDIT'}

def snapshot(conn):
    count = conn.execute('SELECT COUNT(*) FROM evidence').fetchone()[0]
    receipts = conn.execute('SELECT COUNT(*) FROM receipts').fetchone()[0]
    verified = conn.execute("SELECT COUNT(*) FROM receipts WHERE verified_status = 'DIRECT_ONCHAIN_VERIFIED'").fetchone()[0]
    checks = [dict(r) for r in conn.execute('SELECT * FROM checks ORDER BY time_utc DESC LIMIT 12')]
    events = [dict(r) for r in conn.execute('SELECT * FROM evidence ORDER BY observed_utc DESC LIMIT 35')]
    payments = [dict(r) for r in conn.execute('SELECT * FROM receipts ORDER BY observed_utc DESC LIMIT 25')]
    return {
        'fetched_at_utc': utc(), 'testnet_readiness': 'UNVERIFIED',
        'execution_mode': 'NO_SIGNING_NO_PAYMENT', 'airdrop_estimate': None,
        'public_evidence_count': count, 'receipt_records': receipts,
        'direct_onchain_verified_receipts': verified,
        'source_checks': checks, 'items': events, 'receipts': payments,
        'scoring_note': 'Only independently verified direct onchain settled spend may support eligibility; all imported records remain unverified.'
    }

def record_receipt(conn, path):
    """Record *untrusted* report for later chain verification; never claim airdrop."""
    obj = json.loads(Path(path).read_text(encoding='utf-8'))
    required = ('request_id', 'wallet', 'channel_id', 'test_flop_spent')
    if any(not isinstance(obj.get(k), str) or not obj[k].strip() for k in required):
        raise ValueError('Missing text fields in receipt report')
    if not obj['channel_id'].startswith('0x'):
        raise ValueError('Channel ID must be prefixed with 0x')
    from decimal import Decimal
    amount = Decimal(obj['test_flop_spent'])
    if not amount.is_finite() or amount < 0:
        raise ValueError('Invalid amount')
    conn.execute('INSERT OR IGNORE INTO receipts(request_id,wallet,channel_id,test_flop_spent,claimed_status,observed_utc) VALUES (?,?,?,?,?,?)',
                 (obj['request_id'], obj['wallet'], obj['channel_id'], str(amount), 'USER_IMPORTED_UNVERIFIED', utc()))
    conn.commit()
    return {'status': 'IMPORTED_NOT_VERIFIED', 'request_id': obj['request_id']}

def offline_first_test():
    """Exercise real SQLite/normalization/collector flows, but no FLOP spend."""
    with tempfile.TemporaryDirectory() as tmp:
        conn = db(Path(tmp) / 'ledger.sqlite3')
        obj = {'sha': 'sample-test-sha', 'html_url': 'https://github.com/flop-labs/network/commit/sample-test-sha',
               'commit': {'message': 'test: dry-run fixture'}}
        result = collect(conn, fetch=lambda url: [obj] if 'commits' in url else [])
        result2 = collect(conn, fetch=lambda url: [obj] if 'commits' in url else [])
        s = snapshot(conn)
        assert result['new_public_items'] == 2 and result2['new_public_items'] == 0
        assert s['public_evidence_count'] == 2 and s['direct_onchain_verified_receipts'] == 0
        assert s['execution_mode'] == 'NO_SIGNING_NO_PAYMENT'
        conn.close()
    return {'result': 'PASS_OFFLINE', 'tested': ['SQLite', 'GitHub normalization', 'idempotent dedup', 'dashboard state'],
            'real_inference': 'NOT_EXECUTED', 'wallet_payment': 'NOT_EXECUTED', 'airdrop_earned': 'UNVERIFIED'}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            content = (ROOT / 'dashboard.html').read_bytes()
            typ = 'text/html; charset=utf-8'
        elif self.path == '/api/state':
            conn = db()
            try:
                content = json.dumps(snapshot(conn), ensure_ascii=False).encode('utf-8')
            finally:
                conn.close()
            typ = 'application/json; charset=utf-8'
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', typ)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
        self.end_headers()
        self.wfile.write(content)
    def log_message(self, fmt, *args):
        return

def preflight():
    cli = shutil.which('flop')
    out = {'flop_cli_available': bool(cli), 'network': 'testnet', 'only_read_only': True, 'testnet_live': 'UNVERIFIED'}
    if not cli:
        return out
    for key, cmd in [('cli_version', [cli, '--version']), ('network_status', [cli, '--network', 'testnet', 'network', 'status', '--json'])]:
        try:
            cp = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)
            out[key] = {'return_code': cp.returncode, 'output_excerpt': (cp.stdout or cp.stderr)[:700]}
        except (OSError, subprocess.TimeoutExpired) as exc:
            out[key] = {'error': type(exc).__name__}
    return out

def main(argv=None):
    p = argparse.ArgumentParser(description='FLOP local read-only research and receipt observability')
    sub = p.add_subparsers(dest='action', required=True)
    for name in ['first-test', 'collect', 'status', 'dashboard', 'preflight']:
        sub.add_parser(name)
    r = sub.add_parser('import-unverified-receipt')
    r.add_argument('path')
    args = p.parse_args(argv)
    if args.action == 'first-test':
        output = offline_first_test()
    elif args.action == 'preflight':
        output = preflight()
    elif args.action == 'dashboard':
        server = ThreadingHTTPServer(('127.0.0.1', 8765), Handler)
        print('Read-only dashboard: http://127.0.0.1:8765', flush=True)
        server.serve_forever()
        return 0
    else:
        conn = db()
        try:
            if args.action == 'collect':
                output = collect(conn)
            elif args.action == 'status':
                output = snapshot(conn)
            else:
                output = record_receipt(conn, args.path)
        finally:
            conn.close()
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())
