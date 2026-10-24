"""Bound G3 attention load using only pre-event positively sourced crypto IDs.

Research only: no strategy modifications, no price source fetch, no orders.
Crypto identity alone does NOT establish historical venue/PIT/account eligibility.
"""
from collections import Counter
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


class PositiveBoundError(ValueError):
    pass


SHA256_RE = re.compile(r'[0-9a-f]{64}\Z')


def g3_positive_identity_bound(replay, crypto_manifest, security_manifest):
    if not all(isinstance(x, dict) for x in (replay, crypto_manifest, security_manifest)):
        raise PositiveBoundError('REQUIRES_THREE_OBJECTS')
    if crypto_manifest.get('schema') != 'MONSTER_SPOT511_PRE_EVENT_OFFICIAL_POSITIVE_CRYPTO_ASSET_ID_V1':
        raise PositiveBoundError('POSITIVE_MANIFEST_SCHEMA')
    if security_manifest.get('schema') != 'MONSTER_SPOT_HISTORIC_POSITIVE_BSTOCKS_V1':
        raise PositiveBoundError('SECURITY_MANIFEST_SCHEMA')
    if (replay.get('replay_inner_json_sha256') != crypto_manifest.get('freeze_replay_sha') or
        replay.get('replay_results', {}).get('old_42_original_core_events_exactly_preserved') is not True or
        replay.get('replay_results', {}).get('fifo_fair_setup_id_and_time_equal') is not True):
        raise PositiveBoundError('REPLAY_PROVENANCE_OR_OLD_EVENT_DRIFT')
    source = replay.get('complete_46_original_core_setups')
    if (not isinstance(source, list) or
        len(source) != replay['replay_results'].get('current_setup_fifo') or
        len(source) != replay['replay_results'].get('current_setup_fair8')):
        raise PositiveBoundError('ORIGINAL_SETUP_DENOMINATOR_DRIFT')
    window = crypto_manifest.get('frozen_replay_window_utc')
    if not isinstance(window, str) or window.count('/') != 1:
        raise PositiveBoundError('FROZEN_WINDOW_INVALID')
    try:
        begin, end = [datetime.fromisoformat(x.replace('Z','+00:00')) for x in window.split('/')]
    except ValueError as exc:
        raise PositiveBoundError('FROZEN_WINDOW_INVALID') from exc
    if (begin.tzinfo is None or end.tzinfo is None or
        end <= begin or int((end-begin).total_seconds()) != 7*86400):
        raise PositiveBoundError('EXACT_SEVEN_DAY_WINDOW_REQUIRED')
    crypto = {}
    source_rows = crypto_manifest.get('rows')
    if not isinstance(source_rows, list):
        raise PositiveBoundError('POSITIVE_ROWS_REQUIRED')
    for row in source_rows:
        if not isinstance(row, dict):
            raise PositiveBoundError('INVALID_POSITIVE_ROW')
        symbol = row.get('symbol')
        if (not isinstance(symbol, str) or not symbol.endswith('USDT') or
            symbol in crypto or row.get('classification') != 'CRYPTO_ASSET_IDENTITY_POSITIVE_ONLY'):
            raise PositiveBoundError('INVALID_OR_DUPLICATE_POSITIVE_SYMBOL')
        src = row.get('source_url')
        if not isinstance(src, str):
            raise PositiveBoundError('INVALID_OFFICIAL_SOURCE')
        u = urlsplit(src)
        if (u.scheme != 'https' or u.hostname != 'www.binance.com' or
            not (u.path.startswith('/en/support/') or u.path.startswith('/en-PH/support/') or
                 u.path.startswith('/en-IN/support/') or u.path.startswith('/en/research/'))):
            raise PositiveBoundError('INVALID_OFFICIAL_SOURCE')
        when = row.get('published_utc_date')
        if not isinstance(when, str):
            raise PositiveBoundError('BAD_PUBLISH_DATE')
        try:
            parsed = date.fromisoformat(when)
        except ValueError as exc:
            raise PositiveBoundError('BAD_PUBLISH_DATE') from exc
        if parsed.isoformat() != when or parsed >= begin.date():
            raise PositiveBoundError('SOURCE_NOT_PRE_WINDOW_DAY')
        crypto[symbol] = row
    if (len(crypto) != crypto_manifest.get('positive_crypto_type_symbols') or
        crypto_manifest.get('known_positive_crypto_type_setup_events') !=
        sum(1 for e in source if e.get('symbol') in crypto)):
        raise PositiveBoundError('POSITIVE_COUNT_CANNOT_BE_SELF_ASSERTED')
    security = set()
    anns = security_manifest.get('announcements')
    if not isinstance(anns, list):
        raise PositiveBoundError('SECURITY_ROWS_REQUIRED')
    for ann in anns:
        for sym in ann.get('positive_bstock_symbols', []):
            if not isinstance(sym, str) or sym in security:
                raise PositiveBoundError('DUPLICATE_OR_BAD_SECURITY_SYMBOL')
            security.add(sym)
    if (len(security) != security_manifest.get('expected_positive_count') or
        crypto.keys() & security):
        raise PositiveBoundError('POSITIVE_CRYPTO_SECURITY_CONFLICT')
    seen = set()
    verified = []
    excluded = []
    unknown = []
    for event in source:
        if not isinstance(event, dict):
            raise PositiveBoundError('BAD_SETUP_ROW')
        sym, uid, ms = (event.get('symbol'), event.get('event_id'), event.get('observed_ms'))
        if (not isinstance(sym, str) or not sym.endswith('USDT') or
            not isinstance(uid, str) or not SHA256_RE.fullmatch(uid) or uid in seen or
            type(ms) is not int or not int(begin.timestamp()*1000) <= ms < int(end.timestamp()*1000)):
            raise PositiveBoundError('BAD_OR_DUPLICATE_OR_OUTSIDE_WINDOW_SETUP')
        seen.add(uid)
        if sym in crypto:
            verified.append(event)
        elif sym in security:
            excluded.append(event)
        else:
            unknown.append(event)
    if len(source) != crypto_manifest.get('full_event_count'):
        raise PositiveBoundError('SETUP_COUNT_DIFFERS_FROM_FROZEN')
    n_utc_days = 7
    max_for_target = 5*n_utc_days
    return {
        'schema': 'MONSTER_SPOT511_G3_PRE_EVENT_POSITIVE_CRYPTO_OVERLOAD_BOUND_V1',
        'frozen_window_utc': window, 'source_replay_run_id': replay.get('run_id'),
        'raw_setup_events_preserved': len(source),
        'positively_source_crypto_identity_count': len(verified),
        'positively_source_crypto_symbols': len({x['symbol'] for x in verified}),
        'positively_source_security_excluded_events': len(excluded),
        'unresolved_identity_events': len(unknown),
        'unresolved_symbols': sorted({e['symbol'] for e in unknown}),
        'positive_event_ids': sorted(e['event_id'] for e in verified),
        'positive_crypto_daily_utc': dict(sorted(Counter(datetime.fromtimestamp(
            e['observed_ms']/1000,timezone.utc).date().isoformat() for e in verified).items())),
        'G3_frozen_seven_day_attention_max': max_for_target,
        'positive_identity_only_minimum_seven_day_average': len(verified)/7,
        'overloaded_even_if_last_source_day_zero_if_all_positive_crypto_eligible': len(verified) > max_for_target,
        'historical_monitoring_quiz_account_and_dynamic_trade_PIT': 'UNKNOWN',
        'notional_L2_and_net_exit': 'UNKNOWN',
        'formal_G3': 'NOT_PASSED_PENDING_ELIGIBILITY_AND_FULL_SOURCE',
        'formal_G6': 'NO_GO',
        'frozen_D0_D1_unchanged': True,
        'no_mac_deploy_mail_or_trade': True
    }


def main():
    import argparse
    p = argparse.ArgumentParser(description='Bound attention-load from certified-pre-event crypto TYPE only')
    p.add_argument('--replay', type=Path, required=True)
    p.add_argument('--crypto-manifest', type=Path, required=True)
    p.add_argument('--security-manifest', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists() or a.out.is_symlink():
        raise PositiveBoundError('REFUSE_EXISTING_OUTPUT')
    result = g3_positive_identity_bound(
        json.loads(a.replay.read_text()), json.loads(a.crypto_manifest.read_text()),
        json.loads(a.security_manifest.read_text()))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open('x',encoding='utf-8') as fp:
        json.dump(result,fp,sort_keys=True,indent=2)
        fp.write('\n')
    print(json.dumps({k:result[k] for k in ('raw_setup_events_preserved',
        'positively_source_crypto_identity_count','G3_frozen_seven_day_attention_max','formal_G6')}))


if __name__ == '__main__':
    main()
