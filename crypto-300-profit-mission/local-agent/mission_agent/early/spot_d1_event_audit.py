"""Fail-closed reconciliation of archived Monster Spot D1 queue vs minute-derived decisions.

Reads offline research JSON only. Never promotes reconstructed SETUP IDs/timestamps
into original SQLite event readbacks, point-in-time quotes, or executable trades.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


class EventAuditError(ValueError):
    pass


def _fail(code):
    raise EventAuditError(code)


def _day(utc_ms):
    return datetime.fromtimestamp(utc_ms / 1000, timezone.utc).date().isoformat()


def audit_recomputed_d1(original, independent):
    if not isinstance(original, dict) or not isinstance(independent, dict):
        _fail('OBJECTS_REQUIRED')
    original_episodes = original.get('fifo_episodes')
    other_episodes = original.get('fair8_episodes')
    pairs = independent.get('derived', {}).get('setup_rows')
    if not all(isinstance(x, list) for x in (original_episodes, other_episodes, pairs)):
        _fail('EPISODE_ARRAY_REQUIRED')
    if original.get('same_d0_watch_id_and_time') is not True:
        _fail('D0_ID_TIME_UNCONFIRMED')
    if original.get('fifo_setups') != original.get('fair8_setups'):
        _fail('LANE_SETUP_COUNT_DRIFT')
    if original.get('new_setup_ids') or original.get('lost_setup_ids') or original.get('shared_setup_time_changed_ids'):
        _fail('LANE_SETUP_EVENT_DRIFT')
    n = original.get('d0_watch_count')
    if type(n) is not int or n < 1 or len(original_episodes) != n or len(other_episodes) != n or len(pairs) != n:
        _fail('WATCH_DENOMINATOR_MISMATCH')
    by_id = {}
    for ep in original_episodes:
        if not isinstance(ep, dict) or type(ep.get('id')) is not int or ep['id'] in by_id:
            _fail('DUPLICATE_OR_BAD_QUEUE_ID')
        by_id[ep['id']] = ep
    for ep in other_episodes:
        if ep.get('id') not in by_id or any(ep.get(k) != by_id[ep['id']].get(k)
            for k in ('symbol', 'venue', 'first_seen_ms', 'deadline_ms', 'status', 'first_valid_eval_ms')):
            _fail('FIFO_FAIR_QUEUE_EPISODE_DRIFT')
    actual_ids = set()
    by_day = Counter()
    matched = []
    late = []
    evaluated_nonsetup = []
    for entry in pairs:
        if not isinstance(entry, list) or len(entry) != 3:
            _fail('INVALID_RECOMPUTED_ROW')
        ident, symbol, at = entry
        if type(ident) is not int or ident not in by_id or ident in actual_ids:
            _fail('RECOMPUTED_EPISODE_ID_MISMATCH')
        actual_ids.add(ident)
        ep = by_id[ident]
        if symbol != ep['symbol'] or ep['venue'] != 'spot':
            _fail('RECOMPUTED_SYMBOL_OR_VENUE_MISMATCH')
        start, deadline, first_valid = (ep.get('first_seen_ms'), ep.get('deadline_ms'), ep.get('first_valid_eval_ms'))
        if (type(start) is not int or type(deadline) is not int or
            deadline-start != 900_000 or start % 180_000 != 0):
            _fail('ORIGINAL_DEADLINE_OR_CLOCK_INVALID')
        if ep.get('status') == 'LATE':
            if at is not None or first_valid is not None:
                _fail('LATE_MUST_NOT_SET_UP')
            late.append(ident)
        elif ep.get('status') == 'EVALUATED':
            if type(first_valid) is not int or first_valid < start or first_valid > deadline:
                _fail('FIRST_VALID_OUTSIDE_EPISODE')
            if at is None:
                evaluated_nonsetup.append(ident)
            else:
                if type(at) is not int or at % 180_000 or not first_valid <= at <= deadline:
                    _fail('SETUP_OUTSIDE_VALID_REPLAY_CLOCK')
                key = hashlib.sha256(
                    f'MONSTER_V4|spot|{symbol}|SETUP_ACTIVE|{ident}'.encode('utf-8')
                ).hexdigest()
                matched.append({'queue_id': ident, 'symbol': symbol,
                                'reconstructed_event_id': key, 'reconstructed_observed_ms': at})
                by_day[_day(at)] += 1
        else:
            _fail('UNKNOWN_QUEUE_STATUS')
    if actual_ids != set(by_id):
        _fail('EPISODE_POPULATION_MISMATCH')
    if len(matched) != original['fifo_setups']:
        _fail('INDEPENDENT_D1_COUNT_DIFFERS_FROM_ORIGINAL')
    derived = independent['derived']
    if (derived.get('recomputed_setups') != len(matched) or
        derived.get('raw_setups_by_complete_utc_day') != dict(sorted(by_day.items())) or
        sorted(derived.get('evaluated_but_no_setup_queue_ids', [])) != sorted(evaluated_nonsetup) or
        sorted(derived.get('late_queue_ids', [])) != sorted(late)):
        _fail('INDEPENDENT_LEDGER_INTERNAL_DRIFT')
    return {'scope': 'OFFLINE_POSTHOC_D1_RECOMPUTATION_ONLY',
            'original_episode_count': n, 'recomputed_setup_count': len(matched),
            'nonsetup_evaluated_ids': sorted(evaluated_nonsetup),
            'late_ids': sorted(late), 'setup_counts_by_utc_day': dict(sorted(by_day.items())),
            'reconstructed_setup_events': sorted(matched, key=lambda x:(x['reconstructed_observed_ms'],x['queue_id'])),
            'original_sqlite_event_ids_readback': False, 'historical_live_PIT': 'UNPROVEN',
            'crypto_only_identity': 'UNKNOWN', 'g4_net_executable_pnl': 'UNKNOWN',
            'G6': 'NO_GO'}


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Read-only verification of frozen D1 event ledgers')
    ap.add_argument('--original-replay-json', required=True, type=Path)
    ap.add_argument('--independent-json', required=True, type=Path)
    args = ap.parse_args()
    report = audit_recomputed_d1(json.loads(args.original_replay_json.read_text()),
                                 json.loads(args.independent_json.read_text()))
    print(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
