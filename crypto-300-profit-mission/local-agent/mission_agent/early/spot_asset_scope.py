"""Research-only asset-type overlay on unchanged original Monster Spot D0/D1 events.

Only positive source-backed historical classifications. Unknown is never crypto.
Never changes detection, event identities, trade permissions or release gates.
"""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlsplit


class ScopeEvidenceError(ValueError):
    pass


def _ms_utc(s):
    if not isinstance(s, str) or not s.endswith('Z'):
        raise ScopeEvidenceError('SOURCE_TIME_UTC_ISO_REQUIRED')
    try:
        date = datetime.fromisoformat(s.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ScopeEvidenceError('SOURCE_TIME_BAD_FORMAT') from exc
    if date.tzinfo is None:
        raise ScopeEvidenceError('SOURCE_TIME_NO_TIMEZONE')
    return int(date.timestamp() * 1000)


def classify_spot_replay(replay, manifest, roster):
    """Fail closed for a 511-symbol original replay. Never infer crypto by absence.

    The official evidence is positive only; event history is immutable.
    Event-level status comparisons use announcement publication and update
    cutoffs, but all classes refer to asset type, not historical fill/eligibility.
    """
    if not isinstance(replay, dict) or not isinstance(manifest, dict):
        raise ScopeEvidenceError('OBJECT_REQUIRED')
    if (not isinstance(roster, list) or len(roster) != 511 or
            sorted(set(roster)) != roster or
            replay.get('frozen_roster') != 511 or
            replay.get('mode') != 'OFFLINE_HISTORICAL_RESEARCH'):
        raise ScopeEvidenceError('FROZEN_511_UNVERIFIED')
    if manifest.get('schema') != 'MONSTER_SPOT_HISTORIC_POSITIVE_BSTOCKS_V1':
        raise ScopeEvidenceError('EVIDENCE_SCHEMA_MISMATCH')
    announcements = manifest.get('announcements')
    if not isinstance(announcements, list) or not announcements:
        raise ScopeEvidenceError('EVIDENCE_MISSING')
    positive = {}
    for announcement in announcements:
        if not isinstance(announcement, dict):
            raise ScopeEvidenceError('MALFORMED_ANNOUNCEMENT')
        ts = _ms_utc(announcement.get('published_utc'))
        updated = announcement.get('last_updated_utc')
        if updated is not None:
            ts = max(ts, _ms_utc(updated))
        url = announcement.get('url')
        if (not isinstance(url, str) or urlsplit(url).scheme != 'https' or
                urlsplit(url).hostname not in ('www.binance.com', 'www.binance.bh')):
            raise ScopeEvidenceError('SOURCE_IS_NOT_BINANCE_OFFICIAL')
        symbols = announcement.get('positive_bstock_symbols')
        if not isinstance(symbols, list) or not symbols or len(set(symbols)) != len(symbols):
            raise ScopeEvidenceError('EMPTY_OR_DUPLICATE_OFFICIAL_SET')
        for symbol in symbols:
            if (not isinstance(symbol, str) or not symbol.endswith('USDT') or
                    symbol not in roster or symbol in positive):
                raise ScopeEvidenceError('POSITIVE_NOT_IN_FROZEN_ROSTER_OR_DUPLICATE')
            positive[symbol] = {'asof_ms': ts, 'url': announcement['url']}
    if (manifest.get('expected_positive_count') != len(positive) or
            manifest.get('roster_count') != 511):
        raise ScopeEvidenceError('MANIFEST_IDENTITY_CENSUS_DRIFT')
    if (not replay.get('same_d0_watch_id_and_time') or
            replay.get('d0_watch_count') != len(replay.get('fifo_watch_events', [])) or
            replay.get('fifo_setups') != len(replay.get('fifo_setup_events', []))):
        raise ScopeEvidenceError('ORIGINAL_EVENT_COUNTS_NOT_VERIFIED')
    if (replay.get('fair8_watch_events') != replay.get('fifo_watch_events') or
            replay.get('G6') != 'NO_GO'):
        raise ScopeEvidenceError('ORIGINAL_D0_IDENTITY_OR_G6_DRIFT')
    counts = {}
    candidate_exclusions = []
    for label, key in [('WATCH', 'fifo_watch_events'), ('SETUP', 'fifo_setup_events')]:
        events = replay[key]
        if not isinstance(events, list):
            raise ScopeEvidenceError('NO_EVENT_LIST')
        accepted = 0
        unknown = 0
        count_by_day = Counter()
        unique_events = set()
        for row in events:
            if (not isinstance(row, dict) or row.get('event_type') != {'WATCH':'WATCH_EARLY','SETUP':'SETUP_ACTIVE'}[label] or
                    row.get('venue') != 'spot' or row.get('symbol') not in roster or
                    not isinstance(row.get('event_id'), str) or row['event_id'] in unique_events or
                    type(row.get('observed_ms')) is not int):
                raise ScopeEvidenceError('MALFORMED_OR_DUPLICATE_ORIGINAL_EVENT')
            unique_events.add(row['event_id'])
            candidate = positive.get(row['symbol'])
            if candidate is not None and row['observed_ms'] >= candidate['asof_ms']:
                accepted += 1
                candidate_exclusions.append({'event_id': row['event_id'], 'event_type': label,
                    'symbol': row['symbol'], 'observed_ms': row['observed_ms'],
                    'identity': 'OUT_OF_SCOPE_TOKENIZED_SECURITY', 'proof_url': candidate['url']})
            else:
                unknown += 1
            if label == 'SETUP':
                day = datetime.fromtimestamp(row['observed_ms'] / 1000, timezone.utc).date().isoformat()
                count_by_day[day] += 1
        counts[label] = {'raw': len(events), 'verified_tokenized_security': accepted,
                         'identity_unresolved': unknown}
        if label == 'SETUP':
            counts[label]['raw_by_utc_day'] = dict(sorted(count_by_day.items()))
    return {
        'schema': 'MONSTER_SPOT511_POSITIVE_ASSET_TYPE_EVENT_OVERLAY_V1',
        'basis': 'OFFICIAL_PRE_EVENT_POSITIVE_BSTOCKS_ONLY',
        'frozen_roster_size': len(roster),
        'known_bstock_symbols_in_frozen_roster': len(positive),
        'unresolved_asset_type_symbols': len(roster) - len(positive),
        'watch': counts['WATCH'], 'setup': counts['SETUP'],
        'positive_excluded_events': sorted(candidate_exclusions,
                key=lambda x:(x['observed_ms'], x['event_id'])),
        'all_unmatched_assets_certified_crypto': False,
        'historical_dynamic_listing_PIT_proven': False,
        'eligible_crypto_only_setup_denominator': None,
        'D0_watch_preserved': True,
        'strategy_thresholds_changed': False,
        'G3': 'NOT_PASSED_NEEDS_CRYPTO_IDENTITY',
        'G6': 'NO_GO'
    }


def main():
    import argparse
    p = argparse.ArgumentParser(description='Posthoc positive-evidence bStocks overlay, no detection edits')
    p.add_argument('--replay', required=True, type=Path)
    p.add_argument('--manifest', required=True, type=Path)
    p.add_argument('--roster', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise ScopeEvidenceError('REFUSE_OVERWRITE')
    payload = classify_spot_replay(json.loads(args.replay.read_text()),
                                  json.loads(args.manifest.read_text()),
                                  json.loads(args.roster.read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
        fp.write('\n')
    print(json.dumps({k:payload[k] for k in ('frozen_roster_size','known_bstock_symbols_in_frozen_roster','watch','setup','G6')}))


if __name__ == '__main__':
    main()
