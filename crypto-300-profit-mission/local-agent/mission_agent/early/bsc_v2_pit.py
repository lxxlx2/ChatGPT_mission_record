"""Deterministic BSC V2 pool-creation/initial-liquidity proof.

Inputs are archived historical eth_call and eth_getLogs results. This module
never accesses networks, wallet keys, future token outcomes, or trading systems.
"""

PAIR_CREATED = '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9'
SYNC = '0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1'
MINT = '0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f'
SWAP = '0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822'


class PITInvalid(ValueError):
    pass


def first_creation_block(factory_index, first, last, get_length):
    """Earliest block containing zero-based allPairs(factory_index)."""
    if factory_index < 0 or not 0 < first <= last:
        raise PITInvalid('INVALID_INDEX_OR_BOUNDS')
    if get_length(first - 1) > factory_index:
        raise PITInvalid('PAIR_PREDATES_DAY')
    if get_length(last) <= factory_index:
        raise PITInvalid('PAIR_NOT_YET_CREATED')
    lo, hi = first, last
    while lo < hi:
        mid = (lo + hi) // 2
        count = get_length(mid)
        if count > factory_index:
            hi = mid
        else:
            lo = mid + 1
    return lo


def first_later_reserve_update(creation_block, last_block, initial_timestamp, get_timestamp):
    """First subsequent Sync timestamp update. Not proof that its cause was Swap."""
    if not 0 <= creation_block < last_block or initial_timestamp < 0:
        raise PITInvalid('INVALID_RESERVE_SEARCH_RANGE')
    if get_timestamp(creation_block) != initial_timestamp:
        raise PITInvalid('INITIAL_RESERVE_TIMESTAMP_MISMATCH')
    if get_timestamp(last_block) <= initial_timestamp:
        return None
    lo, hi = creation_block + 1, last_block
    while lo < hi:
        mid = (lo + hi) // 2
        if get_timestamp(mid) > initial_timestamp:
            hi = mid
        else:
            lo = mid + 1
    return lo


def as_uint(hex_string):
    if not isinstance(hex_string, str) or not hex_string.startswith('0x'):
        raise PITInvalid('INVALID_HEX')
    try:
        return int(hex_string, 16)
    except ValueError as exc:
        raise PITInvalid('INVALID_HEX') from exc


def address_from_topic(topic):
    if not isinstance(topic, str) or len(topic) != 66 or not topic.startswith('0x'):
        raise PITInvalid('INVALID_ADDRESS_TOPIC')
    as_uint(topic)
    if int(topic[2:26], 16):
        raise PITInvalid('NONZERO_ADDRESS_PADDING')
    return '0x' + topic[-40:].lower()


def words(data, count=2):
    if not isinstance(data, str) or len(data) != 2 + 64 * count or not data.startswith('0x'):
        raise PITInvalid('INVALID_ABI_EVENT_DATA')
    return tuple(as_uint('0x' + data[2 + 64 * i:2 + 64 * (i+1)]) for i in range(count))


def verify_bootstrap(*, factory, factory_index, creation_block, pool, token0, token1,
                     factory_logs, pool_logs):
    """Check actual PairCreated, same-tx Sync+Mint, but NEVER claim swap or sellability."""
    pool = pool.lower()
    factory = factory.lower()
    matched = []
    for row in factory_logs:
        topics = row.get('topics') or []
        if row.get('address', '').lower() != factory or not topics or topics[0].lower() != PAIR_CREATED:
            continue
        if as_uint(row['blockNumber']) != creation_block or len(topics) != 3:
            continue
        if address_from_topic(topics[1]) != token0.lower() or address_from_topic(topics[2]) != token1.lower():
            continue
        pool_word, count = words(row['data'])
        if pool_word != int(pool, 16) or count != factory_index + 1:
            continue
        matched.append(row)
    if len(matched) != 1:
        raise PITInvalid('PAIR_CREATED_EVENT_NOT_UNIQUE_AND_MATCHED')
    created = matched[0]
    tx = created['transactionHash'].lower()
    log_index = as_uint(created['logIndex'])
    same_tx = [r for r in pool_logs if r.get('address', '').lower() == pool
               and r.get('transactionHash', '').lower() == tx
               and as_uint(r['blockNumber']) == creation_block
               and as_uint(r['logIndex']) > log_index]
    sync = [r for r in same_tx if r.get('topics') and r['topics'][0].lower() == SYNC]
    mint = [r for r in same_tx if r.get('topics') and r['topics'][0].lower() == MINT]
    if len(sync) != 1 or len(mint) != 1:
        return {'status': 'CREATED_NO_UNIQUE_SAME_TX_MINT_SYNC', 'factory_index': factory_index,
                'creation_block': creation_block, 'creation_tx': tx, 'pool': pool,
                'initial_quote_liquidity_proven': False, 'sell_path': 'UNKNOWN'}
    reserve0, reserve1 = words(sync[0]['data'])
    amount0, amount1 = words(mint[0]['data'])
    if (reserve0 <= 0 or reserve1 <= 0 or amount0 != reserve0 or amount1 != reserve1
            or as_uint(sync[0]['logIndex']) >= as_uint(mint[0]['logIndex'])):
        raise PITInvalid('BOOTSTRAP_SYNC_MINT_AMOUNTS_OR_ORDER')
    return {'status': 'CREATED_AND_SAME_TX_INITIAL_MINT_SYNC', 'factory_index': factory_index,
            'creation_block': creation_block, 'creation_tx': tx, 'pool': pool,
            'reserve0_raw': str(reserve0), 'reserve1_raw': str(reserve1),
            'initial_quote_liquidity_proven': True,
            'first_swap': 'UNKNOWN', 'sell_path': 'UNKNOWN',
            'realized_pnl': 'UNKNOWN', 'public_observer_time': 'UNVERIFIED'}

def verify_delayed_mint_sync(*, pool, creation_block, update_block, pool_logs):
    """Identify delayed first LP Mint+Sync, without asserting a buy/sell path."""
    if update_block <= creation_block:
        raise PITInvalid('DELAYED_LIQUIDITY_BLOCK_NOT_AFTER_CREATION')
    pair = pool.lower()
    eligible = []
    for log in pool_logs:
        if (str(log.get('address', '')).lower() != pair
                or as_uint(log.get('blockNumber')) != update_block
                or log.get('removed') is True):
            raise PITInvalid('DELAYED_POOL_LOG_SOURCE_MISMATCH')
        eligible.append(log)
    syncs = [x for x in eligible if x.get('topics') and x['topics'][0].lower() == SYNC]
    mints = [x for x in eligible if x.get('topics') and x['topics'][0].lower() == MINT]
    matches = []
    for mint in mints:
        tx = mint['transactionHash'].lower()
        before = [s for s in syncs if s['transactionHash'].lower() == tx
                  and as_uint(s['logIndex']) < as_uint(mint['logIndex'])
                  and s['data'].lower() == mint['data'].lower()]
        if len(before) == 1:
            a, b = words(mint['data'])
            if a > 0 and b > 0:
                matches.append((mint, a, b))
    if len(matches) != 1:
        return {'status': 'DELAYED_FIRST_MINT_SYNC_UNRESOLVED',
                'delayed_initial_liquidity_proven': False,
                'first_sync_update_block': update_block, 'sell_path': 'UNKNOWN'}
    mint, a, b = matches[0]
    return {'status': 'DELAYED_FIRST_MINT_SYNC_CONFIRMED',
            'delayed_initial_liquidity_proven': True,
            'first_sync_update_block': update_block,
            'first_delayed_mint_tx': mint['transactionHash'].lower(),
            'reserve0_raw': str(a), 'reserve1_raw': str(b),
            'first_trade_or_executable_t_entry': 'UNRESOLVED', 'sell_path': 'UNKNOWN'}

def v2_amount_out_from_reserves(amount_in, reserve_in, reserve_out, fee_bps=25):
    """Pancake V2 constant-product *quote* (0.25% fee); never a transfer-tax simulation."""
    if any(type(v) is not int for v in (amount_in, reserve_in, reserve_out, fee_bps)):
        raise PITInvalid('STATIC_QUOTE_REQUIRES_INTEGER_RAW_UNITS')
    if min(amount_in, reserve_in, reserve_out) <= 0 or not 0 <= fee_bps < 10000:
        raise PITInvalid('STATIC_QUOTE_INVALID_AMOUNT_RESERVES_OR_FEE')
    effective = amount_in * (10000 - fee_bps)
    out = (effective * reserve_out) // (reserve_in * 10000 + effective)
    if out <= 0 or out >= reserve_out:
        raise PITInvalid('STATIC_QUOTE_DUST_OR_RESERVE_EXHAUSTION')
    return out


def v2_static_two_way_quote(quote_amount_raw, quote_reserve_raw, token_reserve_raw,
                            fee_bps=25):
    """Two independent quotes against the SAME unmodified historical reserves.

    The return is NOT sequential roundtrip proceeds, not a tax/honeypot check,
    not a trading instruction, and never promotes a venue to sellable evidence.
    """
    token_out = v2_amount_out_from_reserves(
        quote_amount_raw, quote_reserve_raw, token_reserve_raw, fee_bps)
    quote_back = v2_amount_out_from_reserves(
        token_out, token_reserve_raw, quote_reserve_raw, fee_bps)
    return {'status': 'TWO_STATIC_QUOTES_ON_UNCHANGED_HISTORICAL_RESERVES',
            'quote_in_raw': str(quote_amount_raw),
            'indicative_token_out_raw': str(token_out),
            'reverse_quote_back_raw': str(quote_back),
            'fee_bps_per_quote': fee_bps,
            'historical_token_transfer_tax': 'UNKNOWN',
            'sequential_roundtrip_pnl': 'NOT_COMPUTED',
            'historical_sell_executable': 'UNVERIFIED'}

def classify_v2_swap_by_quote_side(row, *, quote_is_token0):
    """Observed V2 Swap *direction*, not a general token sellability guarantee."""
    if type(quote_is_token0) is not bool or not isinstance(row, dict):
        raise PITInvalid('SWAP_DIRECTION_INPUT_INVALID')
    topics = row.get('topics') or []
    if not topics or str(topics[0]).lower() != SWAP:
        raise PITInvalid('NOT_A_V2_SWAP_LOG')
    values = words(row.get('data'), 4)
    a0_in, a1_in, a0_out, a1_out = values
    quote_in, token_in = (a0_in, a1_in) if quote_is_token0 else (a1_in, a0_in)
    quote_out, token_out = (a0_out, a1_out) if quote_is_token0 else (a1_out, a0_out)
    if quote_in > 0 and token_out > 0 and quote_out == token_in == 0:
        direction = 'OBSERVED_QUOTE_TO_TOKEN_SWAP'
    elif token_in > 0 and quote_out > 0 and quote_in == token_out == 0:
        direction = 'OBSERVED_TOKEN_TO_QUOTE_SWAP'
    else:
        direction = 'OTHER_OR_AMBIGUOUS_SWAP'
    return {'direction': direction, 'quote_in_raw': str(quote_in),
            'quote_out_raw': str(quote_out),
            'token_in_raw': str(token_in), 'token_out_raw': str(token_out),
            'user_same_notional_sellability': 'UNVERIFIED',
            'tax_and_allowed_addresses': 'UNKNOWN'}



def summarize_v2_archived_swap_windows(*, pool, token0, token1, quote_asset, windows):
    """Replay only archived pair-event windows; never treat gaps as no trading.

    Pair Swap/Sync logs show pool-direction events, not ERC20 transfer amount
    received by the pair or a token's allowance, tax, or holder restrictions.
    Distinct windows can overlap, so equal source events count only once.
    """
    def valid_address(value):
        if not isinstance(value, str) or len(value) != 42 or not value.startswith('0x'):
            return False
        try:
            int(value[2:], 16)
        except ValueError:
            return False
        return True

    if (not all(valid_address(a) for a in (pool, token0, token1, quote_asset))
            or token0.lower() == token1.lower()
            or quote_asset.lower() not in (token0.lower(), token1.lower())
            or not isinstance(windows, list)):
        raise PITInvalid('ARCHIVED_SWAP_SCOPE_OR_QUOTE_INVALID')
    quote_is_token0 = quote_asset.lower() == token0.lower()
    seen = {}
    window_presence = []
    for item in windows:
        if not isinstance(item, dict) or not isinstance(item.get('name'), str):
            raise PITInvalid('ARCHIVED_SWAP_WINDOW_INVALID')
        name = item['name']
        events = item.get('logs')
        if not isinstance(events, list):
            raise PITInvalid('ARCHIVED_SWAP_LOGS_MISSING')
        window_presence.append(name)
        for row in events:
            if not isinstance(row, dict) or row.get('address', '').lower() != pool.lower():
                raise PITInvalid('ARCHIVED_SWAP_WRONG_PAIR_ADDRESS')
            if row.get('removed') is True:
                raise PITInvalid('ARCHIVED_SWAP_REMOVED_LOG')
            topics = row.get('topics')
            if not isinstance(topics, list) or not topics or not isinstance(topics[0], str):
                raise PITInvalid('ARCHIVED_SWAP_MALFORMED_TOPICS')
            if (not isinstance(row.get('transactionHash'), str)
                    or len(row['transactionHash']) != 66
                    or not row['transactionHash'].startswith('0x')):
                raise PITInvalid('ARCHIVED_SWAP_TX_HASH_INVALID')
            try:
                int(row['transactionHash'][2:], 16)
                block = as_uint(row.get('blockNumber'))
                txindex = as_uint(row.get('transactionIndex'))
                logindex = as_uint(row.get('logIndex'))
            except (PITInvalid, ValueError):
                raise PITInvalid('ARCHIVED_SWAP_LOG_INDEX_INVALID') from None
            key = (block, txindex, logindex)
            if key in seen:
                if seen[key] != row:
                    raise PITInvalid('ARCHIVED_SWAP_CONFLICTING_DUPLICATE_LOG')
            else:
                seen[key] = row
    ordered = sorted(seen.items())
    syncs_by_tx = {}
    for (block, txindex, logindex), row in ordered:
        if row['topics'][0].lower() == SYNC:
            words(row.get('data'))
            syncs_by_tx.setdefault((block, txindex, row['transactionHash'].lower()), []).append(logindex)
    swaps = []
    for (block, txindex, logindex), row in ordered:
        if row['topics'][0].lower() != SWAP:
            continue
        if len(row['topics']) != 3:
            raise PITInvalid('ARCHIVED_SWAP_TOPICS_LAYOUT_INVALID')
        direction = classify_v2_swap_by_quote_side(row, quote_is_token0=quote_is_token0)
        sync_prior = any(
            n < logindex for n in syncs_by_tx.get(
                (block, txindex, row['transactionHash'].lower()), []))
        swaps.append({
            'block': block, 'tx_hash': row['transactionHash'].lower(),
            'log_index': logindex, 'direction': direction['direction'],
            'quote_in_raw': direction['quote_in_raw'],
            'quote_out_raw': direction['quote_out_raw'],
            'token_in_raw': direction['token_in_raw'],
            'token_out_raw': direction['token_out_raw'],
            'preceding_same_tx_pool_sync_in_saved_window': sync_prior,
            'actual_erc20_transfer_included_in_pair_logs': False,
            'historical_sellable_at_notional': 'UNVERIFIED',
        })
    verified_sells = [x for x in swaps if (
        x['direction'] == 'OBSERVED_TOKEN_TO_QUOTE_SWAP'
        and x['preceding_same_tx_pool_sync_in_saved_window'])]
    verified_buys = [x for x in swaps if (
        x['direction'] == 'OBSERVED_QUOTE_TO_TOKEN_SWAP'
        and x['preceding_same_tx_pool_sync_in_saved_window'])]
    return {
        'status': 'NONCONTIGUOUS_ARCHIVED_PAIR_WINDOWS_ONLY',
        'archived_windows': window_presence,
        'archived_windows_complete_between_earliest_and_latest': False,
        'observed_swap_events': len(swaps),
        'swap_with_prior_same_tx_sync': sum(
            x['preceding_same_tx_pool_sync_in_saved_window'] for x in swaps),
        'observed_quote_to_token_with_sync': len(verified_buys),
        'observed_token_to_quote_with_sync': len(verified_sells),
        'first_observed_in_saved_windows': swaps[0] if swaps else None,
        'observed_direction_events': swaps,
        'absence_of_swap_in_missing_intervals': 'UNKNOWN',
        'all_token_erc20_transfer_receipts': 'NOT_IN_PAIR_EVENT_SCOPE',
        'historical_token_tax_and_user_sellability': 'UNVERIFIED',
        'twentyfour_of_thirty_complete_pit_gate': 'NOT_SCORABLE',
        'eighteen_of_thirty_sellable_gate': 'NOT_SCORABLE',
    }


def v2_reference_sequential_roundtrip(quote_amount_raw, quote_reserve_raw,
                                       token_reserve_raw, fee_bps=25):
    """Counterfactual two-leg AMM reserve update, with *zero* transfer tax.

    Unlike two getAmountsOut calls on an unchanged pool, the second leg uses
    reserves after the first hypothetical buy. This cannot prove token transfer,
    router execution, holder eligibility, taxes, gas, MEV, or public T_entry.
    """
    token_out = v2_amount_out_from_reserves(
        quote_amount_raw, quote_reserve_raw, token_reserve_raw, fee_bps)
    quote_after_buy = quote_reserve_raw + quote_amount_raw
    token_after_buy = token_reserve_raw - token_out
    quote_back = v2_amount_out_from_reserves(
        token_out, token_after_buy, quote_after_buy, fee_bps)
    if quote_back > quote_amount_raw:
        raise PITInvalid('REFERENCE_ROUNDTRIP_PROCEEDS_EXCEED_INPUT')
    return {
        'status': 'REFERENCE_SEQUENTIAL_AMM_MATH_NO_TOKEN_TAX',
        'quote_in_raw': str(quote_amount_raw),
        'token_bought_raw': str(token_out),
        'quote_reserve_after_buy_raw': str(quote_after_buy),
        'token_reserve_after_buy_raw': str(token_after_buy),
        'reference_quote_back_raw': str(quote_back),
        'reference_amm_only_loss_raw': str(quote_amount_raw - quote_back),
        'fee_bps_per_swap': fee_bps,
        'pool_changes_between_legs_assumed': False,
        'transfer_tax_assumed_zero': True,
        'gas_mev_other_swaps_modeled': False,
        'historical_trade_execution_verified': False,
        'sellable_at_notional': 'UNVERIFIED',
        'paper_net_pnl_status': 'NOT_SCORABLE',
    }
