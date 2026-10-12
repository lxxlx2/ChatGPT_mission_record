#!/usr/bin/env python3
"""Read-only Frank source-ledger diagnostic, never a signal or trading writer.

Outputs local-index evidence and a candidate *research* watch universe. A trade
count is never a full-chain completeness claim, and local OPEN != chain-held.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sqlite3
import sys
from urllib.parse import quote

PERSON = 'frank'
USDC = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
BUY = {'BUY', 'ADD', 'REENTRY'}
SELL = {'SELL', 'EXIT', 'SELL_POSITION_UNRESOLVED'}
SCREENSHOT_AMOUNTS = ('3300.00', '2232.34', '7031.56')


def decimal_amount(body: dict):
    original = body.get('original_quote') or {}
    if body.get('quote_normalization') and original:
        asset, qty = original.get('quote_asset'), original.get('quote_quantity')
    else:
        asset = body.get('quote_asset')
        raw, decimals = body.get('quote_amount_raw'), body.get('quote_decimals')
        if raw is None or decimals is None:
            return asset, None
        try:
            qty = Decimal(str(raw)) / (Decimal(10) ** int(decimals))
        except (ValueError, TypeError, InvalidOperation, OverflowError):
            return asset, None
    try:
        value = Decimal(str(qty))
    except (TypeError, InvalidOperation):
        return asset, None
    return asset, str(value) if value.is_finite() and value >= 0 else None


def _utc(ts: int | float | None):
    return datetime.fromtimestamp(int(ts), timezone.utc).isoformat() if ts is not None else None


def _connect(path: Path):
    if not path.is_file():
        raise FileNotFoundError(str(path))
    db = sqlite3.connect('file:' + quote(str(path.resolve()), safe='/') + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    db.execute('PRAGMA busy_timeout=5000')
    return db


def _tables(db):
    return {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def report(path: Path, as_of: int) -> dict:
    db = _connect(path)
    try:
        required = {'signatures', 'trades', 'v1_states'}
        missing = required - _tables(db)
        if missing:
            raise ValueError('MISSING_REQUIRED_TABLES:' + ','.join(sorted(missing)))
        start = as_of - 86400
        signature_rows = db.execute('''SELECT signature,block_time,body FROM signatures
            WHERE person_id=? AND block_time<=? ORDER BY block_time,signature''', (PERSON, as_of)).fetchall()
        seen_sigs: set[str] = set()
        sig_counts = defaultdict(int)
        for row in signature_rows:
            sig = row['signature']
            if sig in seen_sigs:
                continue
            seen_sigs.add(sig)
            if row['block_time'] >= start:
                sig_counts['24h_indexed_signatures'] += 1
                try:
                    b = json.loads(row['body'] or '{}')
                    cls = b.get('classification') or 'UNKNOWN'
                except (ValueError, TypeError, AttributeError):
                    cls = 'INVALID_BODY'
                sig_counts['class_' + str(cls)] += 1
        trade_rows = db.execute('''SELECT t.signature,t.mint,t.side,t.block_time,t.body
            FROM trades t JOIN signatures s ON s.wallet=t.wallet AND s.signature=t.signature
            WHERE s.person_id=? AND t.block_time<=? ORDER BY t.block_time,t.signature,t.mint''', (PERSON, as_of)).fetchall()
        known_trades = set()
        trades_by_mint: dict[str, list[dict]] = defaultdict(list)
        totals = defaultdict(int)
        screenshot_matches = []
        for t in trade_rows:
            key = (t['signature'], t['mint'], t['side'], t['block_time'])
            if key in known_trades:
                continue
            known_trades.add(key)
            try:
                body = json.loads(t['body'] or '{}')
            except (ValueError, TypeError):
                body = {}
            asset, amount = decimal_amount(body)
            row = {'signature': t['signature'], 'mint': t['mint'], 'side': t['side'],
                   'block_time': t['block_time'], 'block_time_utc': _utc(t['block_time']),
                   'quote_asset': asset, 'quote_amount': amount,
                   'evidence_level': 'LOCAL_INDEX_CLASSIFICATION_ONLY'}
            trades_by_mint[t['mint']].append(row)
            if t['block_time'] >= start:
                totals['24h_recognized_buys' if t['side'] in BUY else
                       '24h_recognized_sells' if t['side'] in SELL else '24h_other_trade_sides'] += 1
            if asset == USDC and amount is not None:
                display = Decimal(amount).quantize(Decimal('.01'))
                if str(display) in SCREENSHOT_AMOUNTS:
                    screenshot_matches.append({**row, 'matched_rounded_amount': str(display),
                                               'match_status': 'LOCAL_INDEX_ONLY_NOT_INDEPENDENT_CHAIN_VERIFIED'})
        states = {}
        for row in db.execute('SELECT mint,body FROM v1_states WHERE person_id=?', (PERSON,)):
            try:
                b = json.loads(row['body'] or '{}')
            except (ValueError, TypeError):
                continue
            states[row['mint']] = {'state': b.get('state'), 'current_raw': b.get('current_raw'),
                                   'episode_id': b.get('episode_id')}
        watch = []
        for mint in sorted(set(trades_by_mint) | set(states)):
            ts = trades_by_mint.get(mint, [])
            st = states.get(mint, {})
            latest = ts[-1] if ts else None
            watch.append({'mint': mint, 'local_state': st.get('state') or 'UNKNOWN',
                          'local_current_raw': st.get('current_raw'),
                          'model_episode_id': st.get('episode_id'),
                          'local_recognized_buy_count': sum(x['side'] in BUY for x in ts),
                          'local_recognized_sell_count': sum(x['side'] in SELL for x in ts),
                          'latest_recognized_trade': latest,
                          'watch_eligibility': 'RESEARCH_WALLET_OBSERVED',
                          'chain_balance_verification': 'NOT_DONE_BY_LOCAL_SNAPSHOT',
                          'pnl_completeness': 'UNVERIFIED_HISTORY_AND_COST_BASIS'})
        return {'schema_version': 1, 'status': 'LOCAL_READONLY_AUDIT_ONLY',
                'source_scope': 'LOCAL_INDEX_NOT_FULL_CHAIN', 'chain_completeness_verified': False,
                'person_id': PERSON, 'as_of_utc': _utc(as_of), 'window_24h_from_utc': _utc(start),
                'total_distinct_indexed_signatures_up_to_as_of': len(seen_sigs),
                'window_24h': dict(sorted({**sig_counts, **totals}.items())),
                'local_observed_mints': len(watch), 'watch_seed': watch,
                'screenshot_amount_matches': screenshot_matches,
                'limitations': ['This script does not fetch RPC transactions or current balances.',
                                'A zero in a 24h window is not a zero in lifetime or a complete-chain claim.',
                                'Local index gaps, external signer effects and model signal vetoes are separate.',
                                'Watch seed is historical/local only. No trade decision or notification is generated.']}
    finally:
        db.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--db', type=Path, required=True, help='Existing Frank production forward.sqlite (read only)')
    ap.add_argument('--as-of-epoch', type=int, required=True, help='UTC epoch for a reproducible 24h window')
    ap.add_argument('--out', type=Path, help='JSON audit destination; stdout when omitted')
    a = ap.parse_args(argv)
    result = report(a.db, a.as_of_epoch)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text, encoding='utf-8')
        print(str(a.out))
    else:
        print(text, end='')


if __name__ == '__main__':
    try:
        main()
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print('AUDIT_FAILED: ' + str(exc), file=sys.stderr)
        raise SystemExit(2)
