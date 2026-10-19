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
