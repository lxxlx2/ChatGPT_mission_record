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


def audit_recomputed_d1(original, independent, *, require_equal_lanes=False):
    if not isinstance(original, dict) or not isinstance(independent, dict):
        _fail('OBJECTS_REQUIRED')
    original_episodes = original.get('fifo_episodes')
    other_episodes = original.get('fair8_episodes')
    pairs = independent.get('derived', {}).get('setup_rows')
    if not all(isinstance(x, list) for x in (original_episodes, other_episodes, pairs)):
        _fail('EPISODE_ARRAY_REQUIRED')
    if original.get('same_d0_watch_id_and_time') is not True:
        _fail('D0_ID_TIME_UNCONFIRMED')
    if require_equal_lanes:
        if original.get('fifo_setups') != original.get('fair8_setups'):
            _fail('LANE_SETUP_COUNT_DRIFT')
        if (original.get('new_setup_ids') or original.get('lost_setup_ids') or
            original.get('shared_setup_time_changed_ids')):
            _fail('LANE_SETUP_EVENT_DRIFT')
    n = original.get('d0_watch_count')
    if type(n) is not int or n < 1 or len(original_episodes) != n or len(other_episodes) != n or len(pairs) != n:
        _fail('WATCH_DENOMINATOR_MISMATCH')
    by_id = {}
    for ep in original_episodes:
        if not isinstance(ep, dict) or type(ep.get('id')) is not int or ep['id'] in by_id:
            _fail('DUPLICATE_OR_BAD_QUEUE_ID')
        by_id[ep['id']] = ep
    fair_seen = set()
    for ep in other_episodes:
        if not isinstance(ep, dict) or ep.get('id') in fair_seen or ep.get('id') not in by_id:
            _fail('FIFO_FAIR_QUEUE_ID_DRIFT')
        fair_seen.add(ep['id'])
        fields = ('symbol', 'venue', 'first_seen_ms', 'deadline_ms')
        if require_equal_lanes:
            fields += ('status', 'first_valid_eval_ms')
        if any(ep.get(k) != by_id[ep['id']].get(k) for k in fields):
            _fail('FIFO_FAIR_QUEUE_EPISODE_DRIFT')
    actual_ids = set()
    by_day = Counter()
    matched = []
    late = []
    pending = []
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
        elif ep.get('status') == 'PENDING':
            if at is not None or (first_valid is not None and
                (type(first_valid) is not int or not start <= first_valid <= deadline)):
                _fail('PENDING_MUST_NOT_BECOME_SETTLED')
            pending.append(ident)
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
    # New paired_sqlite exports these rows verbatim from the original-core
    # FIFO SQLite events table. The old historical replay does not; absence
    # must remain an explicit evidence gap rather than being imputed as PASS.
    engine_export = original.get('fifo_setup_events')
    engine_events_matched = False
    if 'fifo_setup_events' in original:
        if not isinstance(engine_export, list):
            _fail('ORIGINAL_ENGINE_EVENT_EXPORT_NOT_ARRAY')
        expected = {r['reconstructed_event_id']: r for r in matched}
        if len(engine_export) != len(expected):
            _fail('ORIGINAL_ENGINE_EVENT_EXPORT_COUNT_DRIFT')
        seen_engine_ids = set()
        for event in engine_export:
            if not isinstance(event, dict):
                _fail('ORIGINAL_ENGINE_EVENT_INVALID_ROW')
            event_id = event.get('event_id')
            if not isinstance(event_id, str) or event_id in seen_engine_ids:
                _fail('ORIGINAL_ENGINE_EVENT_DUPLICATE_OR_BAD_ID')
            seen_engine_ids.add(event_id)
            want = expected.get(event_id)
            if want is None:
                _fail('ORIGINAL_ENGINE_EVENT_ID_MISMATCH')
            if (event.get('venue') != 'spot' or
                event.get('event_type') != 'SETUP_ACTIVE' or
                event.get('symbol') != want['symbol'] or
                type(event.get('observed_ms')) is not int or
                event['observed_ms'] != want['reconstructed_observed_ms']):
                _fail('ORIGINAL_ENGINE_EVENT_SYMBOL_OR_TIME_MISMATCH')
            details = event.get('details')
            if not isinstance(details, dict) or details.get('setup_candidate') is not True:
                _fail('ORIGINAL_ENGINE_EVENT_PAYLOAD_MISMATCH')
        if seen_engine_ids != set(expected):
            _fail('ORIGINAL_ENGINE_EVENT_POPULATION_MISMATCH')
        engine_events_matched = True
    if len(matched) != original['fifo_setups']:
        _fail('INDEPENDENT_D1_COUNT_DIFFERS_FROM_ORIGINAL')
    derived = independent['derived']
    if (derived.get('recomputed_setups') != len(matched) or
        derived.get('raw_setups_by_complete_utc_day') != dict(sorted(by_day.items())) or
        sorted(derived.get('evaluated_but_no_setup_queue_ids', [])) != sorted(evaluated_nonsetup) or
        sorted(derived.get('late_queue_ids', [])) != sorted(late) or
        sorted(derived.get('unresolved_pending_queue_ids', [])) != sorted(pending)):
        _fail('INDEPENDENT_LEDGER_INTERNAL_DRIFT')
    return {'scope': 'OFFLINE_POSTHOC_D1_RECOMPUTATION_ONLY',
            'original_episode_count': n, 'recomputed_setup_count': len(matched),
            'nonsetup_evaluated_ids': sorted(evaluated_nonsetup),
            'late_ids': sorted(late), 'unresolved_pending_ids': sorted(pending),
            'setup_counts_by_utc_day': dict(sorted(by_day.items())),
            'reconstructed_setup_events': sorted(matched, key=lambda x:(x['reconstructed_observed_ms'],x['queue_id'])),
            'original_core_fifo_setup_export_present': 'fifo_setup_events' in original,
            'original_core_fifo_setup_export_event_count': len(engine_export) if engine_events_matched else None,
            'original_core_fifo_setup_export_ids_and_times_matched': engine_events_matched,
            'fair8_outcomes_independently_recomputed': False,
            'require_equal_lanes': require_equal_lanes,
            'original_sqlite_event_ids_readback': False, 'historical_live_PIT': 'UNPROVEN',
            'crypto_only_identity': 'UNKNOWN', 'g4_net_executable_pnl': 'UNKNOWN',
            'G6': 'NO_GO'}


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Read-only verification of frozen D1 event ledgers')
    ap.add_argument('--original-replay-json', required=True, type=Path)
    ap.add_argument('--independent-json', required=True, type=Path)
    ap.add_argument('--require-equal-lanes', action='store_true',
                    help='Only when the frozen baseline explicitly expected FIFO8/Fair8 identical')
    args = ap.parse_args()
    report = audit_recomputed_d1(json.loads(args.original_replay_json.read_text()),
                                 json.loads(args.independent_json.read_text()),
                                 require_equal_lanes=args.require_equal_lanes)
    print(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
