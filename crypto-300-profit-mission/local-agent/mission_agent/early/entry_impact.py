"""Read-only P0 evidence audit: selected historical buy AMM friction; no P1 gate."""
import re


class EntryImpactError(ValueError):
    pass


def impact_microbps(amount_raw, reserve_raw, fee_bps=25):
    """Ceiling micro-bps of fee-inclusive V2 execution-price premium vs pre-buy mid."""
    if (not isinstance(amount_raw, str) or not isinstance(reserve_raw, str)
            or not re.fullmatch(r'[0-9]+', amount_raw)
            or not re.fullmatch(r'[0-9]+', reserve_raw)
            or type(fee_bps) is not int or not 0 <= fee_bps < 10000):
        raise EntryImpactError('INVALID_INPUT')
    q, r = int(amount_raw), int(reserve_raw)
    if q <= 0 or r <= 0:
        raise EntryImpactError('INVALID_INPUT')
    den = (10000 - fee_bps) * r
    num = fee_bps * r + (10000 - fee_bps) * q
    return (10**10 * num + den - 1) // den


def audit_frozen30(evidence, diagnostic_impact_bps):
    """All 30 kept; only 22 selected *historical* observed buys are assessable."""
    if type(diagnostic_impact_bps) is not int or not 0 < diagnostic_impact_bps < 10000:
        raise EntryImpactError('INVALID_DIAGNOSTIC_LIMIT')
    try:
        ids = evidence['bsc_v2_p0_current_frozen30_p0_gate_matrix_20261020']['rows']
        twenty = evidence['bsc_v2_p0_uploaded20_actual_buy_and_indexed_real_sell_replay_20261020']['case_results']
        two = evidence['bsc_v2_p0_ranks16_17_post_atomic_distinct_buy_and_partial_sell_pilot_20261020']['cases']
    except (KeyError, TypeError):
        raise EntryImpactError('SOURCE_MISSING') from None
    if (not all(isinstance(x, list) for x in (ids, twenty, two))
            or len(ids) != 30 or len(twenty) != 20 or len(two) != 2
            or [x['rank'] for x in ids] != list(range(1, 31))
            or len({x['token_ca'] for x in ids}) != 30
            or len({x['pool'] for x in ids}) != 30):
        raise EntryImpactError('FROZEN_DENOMINATOR_INVALID')
    out = {}
    for row, prefix in [(x, False) for x in twenty] + [(x, True) for x in two]:
        rank = row['rank']
        if type(rank) is not int or not 1 <= rank <= 30 or rank in out:
            raise EntryImpactError('DUPLICATE_OR_INVALID_RANK')
        anchor = ids[rank-1]
        if (row['token_ca'] != anchor['token_ca']
                or row['pool' if prefix else 'pair'] != anchor['pool']):
            raise EntryImpactError('IDENTITY_MISMATCH')
        block = row['real_independent_post_atomic_buy_block' if prefix else 'buy_block']
        status = row['actual_buy_receipt_status' if prefix else 'buy_transaction_receipt_status']
        if (type(block) is not int
                or block <= anchor['first_confirmed_frozen_depth_event']['block']
                or block <= anchor['creation_block'] or status != '0x1'):
            raise EntryImpactError('PRETRADE_ORDER_UNPROVEN')
        q = row['real_buy_quote_into_pool_raw' if prefix else 'buy_quote_in_raw']
        micro = impact_microbps(q, row['buy_preswap_quote_reserve_raw'])
        out[rank] = {'rank': rank, 'token_ca': anchor['token_ca'],
                     'impact_microbps': micro,
                     'evidence': 'AMM_MATH_SELECTED_HISTORICAL_BUY'}
    if len(out) != 22 or not {16, 17}.issubset(out):
        raise EntryImpactError('FROZEN_SELECTED_BUYS_INVALID')
    impacts = sorted(x['impact_microbps'] for x in out.values())
    return {'frozen_population': 30, 'selected_historical_buy_count': 22,
            'unknown_count': 8, 'diagnostic_impact_bps': diagnostic_impact_bps,
            'above_diagnostic_limit': sum(v > diagnostic_impact_bps * 10**6 for v in impacts),
            'median_microbps_rounded_up': (impacts[10] + impacts[11] + 1) // 2,
            'rows': [out.get(x['rank'], {'rank': x['rank'], 'token_ca': x['token_ca'],
                      'impact_microbps': None, 'evidence': 'NOT_SCORABLE'}) for x in ids],
            'pit_available_at': 'UNKNOWN', 'uniform_notional_sellability': 'NOT_SCORABLE',
            'selected_sample_representative': False, 'p0_gate_passed': False}
