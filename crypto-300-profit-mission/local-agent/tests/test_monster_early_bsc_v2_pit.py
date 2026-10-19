"""No-network regressions for historical BSC V2 initial pool liquidity PIT."""
import json
import unittest
from pathlib import Path
from mission_agent.early.bsc_v2_pit import (
    PAIR_CREATED, SYNC, MINT, SWAP, PITInvalid, first_creation_block,
    first_later_reserve_update, verify_bootstrap,
)


def word(n):
    return format(n, '064x')


def topic(a):
    return '0x' + word(int(a, 16))


class BscV2PitTests(unittest.TestCase):
    def test_binary_search_and_fail_closed_day(self):
        count = lambda b: 100 if b < 23 else (102 if b >= 30 else 101)
        self.assertEqual(first_creation_block(100, 10, 40, count), 23)
        self.assertEqual(first_creation_block(101, 10, 40, count), 30)
        with self.assertRaisesRegex(PITInvalid, 'PREDATES_DAY'):
            first_creation_block(99, 10, 40, count)
        with self.assertRaisesRegex(PITInvalid, 'NOT_YET_CREATED'):
            first_creation_block(102, 10, 40, count)

    def test_first_later_reserve_update_and_real_swap_topic(self):
        timestamp = lambda b: 100 if b < 27 else (145 if b < 50 else 190)
        self.assertEqual(first_later_reserve_update(10, 60, 100, timestamp), 27)
        self.assertIsNone(first_later_reserve_update(10, 20, 100, timestamp))
        self.assertEqual(SWAP, '0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822')
        with self.assertRaisesRegex(PITInvalid, 'TIMESTAMP_MISMATCH'):
            first_later_reserve_update(10, 60, 101, timestamp)

    def test_real_creation_and_mint_layout(self):
        factory = '0x'+'1'*40
        pair = '0x'+'2'*40
        token0='0x'+'3'*40
        token1='0x'+'4'*40
        tx='0x'+'5'*64
        created=dict(address=factory, topics=[PAIR_CREATED,topic(token0),topic(token1)],
                     blockNumber=hex(42), transactionHash=tx, logIndex=hex(9),
                     data='0x'+word(int(pair,16))+word(101))
        sync=dict(address=pair,topics=[SYNC],blockNumber=hex(42),transactionHash=tx,
                  logIndex=hex(13),data='0x'+word(10000)+word(20000))
        mint=dict(address=pair,topics=[MINT],blockNumber=hex(42),transactionHash=tx,
                  logIndex=hex(14),data='0x'+word(10000)+word(20000))
        args=dict(factory=factory,factory_index=100,creation_block=42,pool=pair,
                  token0=token0,token1=token1,factory_logs=[created],pool_logs=[sync,mint])
        got=verify_bootstrap(**args)
        self.assertTrue(got['initial_quote_liquidity_proven'])
        self.assertEqual(got['first_swap'], 'UNKNOWN')
        self.assertEqual(got['reserve0_raw'], '10000')
        no_mint=verify_bootstrap(**{**args,'pool_logs':[sync]})
        self.assertFalse(no_mint['initial_quote_liquidity_proven'])
        with self.assertRaisesRegex(PITInvalid,'PAIR_CREATED_EVENT_NOT_UNIQUE'):
            verify_bootstrap(**{**args,'factory_logs':[]})
        with self.assertRaisesRegex(PITInvalid,'BOOTSTRAP_SYNC_MINT'):
            verify_bootstrap(**{**args,'pool_logs':[sync,{**mint,'data':'0x'+word(1)+word(20000)}]})


    def test_all_30_frozen_factory_creation_records_and_delayed_liquidity_replay(self):
        import json
        from pathlib import Path
        from mission_agent.early.bsc_v2_pit import verify_delayed_mint_sync
        path = Path(__file__).resolve().parents[2] / (
            'monster/evidence/early/P0/P0_SOURCE_PROBE_20261019.json')
        archive = json.loads(path.read_text())
        data = archive['historical_bsc_v2_append_only_factory_enumeration']
        samples = data['creation_liquidity_source_spotchecks']
        cases = samples['cases']
        self.assertEqual([x['rank'] for x in cases], list(range(1, 31)))
        originals = {x['factory_index_zero_based']: x for x in data['first36']}
        logs = {x['rank']: x for x in samples['normalized_event_log_samples']}
        initial = 0
        for case in cases:
            with self.subTest(rank=case['rank']):
                identity = originals[case['index']]
                result = verify_bootstrap(
                    factory='0xca143ce32fe78f1f7019d7d551a6402fc5350c73',
                    factory_index=case['index'], creation_block=case['creation_block'],
                    pool=case['pair'], token0=identity['token0'],
                    token1=identity['token1'],
                    factory_logs=logs[case['rank']]['scope_factory_event'],
                    pool_logs=logs[case['rank']]['scope_pair_same_tx_events'])
                self.assertEqual(result['creation_tx'], case['creation_tx_hash'])
                expected = case['same_tx_erc20_lp_transfer_sync_mint']
                self.assertEqual(result['initial_quote_liquidity_proven'], expected)
                initial += bool(expected)
        self.assertEqual(initial, 25)
        delayed = next(x for x in samples['delayed_liquidity_spotchecks']
                       if x['rank'] == 14)
        pool = next(x for x in cases if x['rank'] == 14)['pair']
        combined = delayed['sync_logs'] + delayed['mint_logs']
        recovered = verify_delayed_mint_sync(
            pool=pool, creation_block=52443568,
            update_block=52446013, pool_logs=combined)
        self.assertTrue(recovered['delayed_initial_liquidity_proven'])
        self.assertEqual(recovered['sell_path'], 'UNKNOWN')

    def test_real_frozen_three_historical_creation_and_mint_source_replay(self):
        repo = Path(__file__).resolve().parents[2]
        path = repo / 'monster/evidence/early/P0/P0_SOURCE_PROBE_20261019.json'
        evidence = json.loads(path.read_text())
        history = evidence['historical_bsc_v2_append_only_factory_enumeration']
        proof = history['creation_liquidity_source_spotchecks']
        all_pools = {x['factory_index_zero_based']: x for x in history['first36']}
        archived = {x['rank']: x for x in proof['normalized_event_log_samples']}
        for case in proof['cases']:
            with self.subTest(rank=case['rank']):
                item = all_pools[case['index']]
                response = archived[case['rank']]
                fact = verify_bootstrap(
                    factory='0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73',
                    factory_index=case['index'],
                    creation_block=case['creation_block'],
                    pool=case['pair'],
                    token0=item['token0'], token1=item['token1'],
                    factory_logs=response['scope_factory_event'],
                    pool_logs=response['scope_pair_same_tx_events'])
                expected = case['same_tx_erc20_lp_transfer_sync_mint']
                self.assertEqual(fact['initial_quote_liquidity_proven'], expected)
                self.assertEqual(fact['creation_tx'], case['creation_tx_hash'])
                if expected:
                    self.assertEqual(fact['reserve0_raw'], case['initial_reserve0_raw'])
                    self.assertEqual(fact['reserve1_raw'], case['initial_reserve1_raw'])
                else:
                    self.assertEqual(fact['status'], 'CREATED_NO_UNIQUE_SAME_TX_MINT_SYNC')
                self.assertEqual(fact['sell_path'], 'UNKNOWN')
                broken = dict(response['scope_factory_event'][0])
                broken['data'] = '0x' + '0'*128
                with self.assertRaisesRegex(PITInvalid, 'PAIR_CREATED_EVENT_NOT_UNIQUE'):
                    verify_bootstrap(factory='0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73',
                                     factory_index=case['index'],
                                     creation_block=case['creation_block'],
                                     pool=case['pair'],
                                     token0=item['token0'], token1=item['token1'],
                                     factory_logs=[broken],
                                     pool_logs=response['scope_pair_same_tx_events'])



class DelayedLiquidityTests(unittest.TestCase):
    def test_actual_rank26_delayed_mint_sync_with_corrected_transaction(self):
        from mission_agent.early.bsc_v2_pit import verify_delayed_mint_sync
        archive = json.loads((Path(__file__).resolve().parents[2] /
            'monster/evidence/early/P0/P0_SOURCE_PROBE_20261019.json').read_text())
        history = archive['historical_bsc_v2_append_only_factory_enumeration']
        evidence = history['creation_liquidity_source_spotchecks']
        case = next(c for c in evidence['cases'] if c['rank'] == 26)
        events = next(s for s in evidence['delayed_liquidity_spotchecks'] if s['rank'] == 26)
        checked = verify_delayed_mint_sync(
            pool=case['pair'], creation_block=case['creation_block'],
            update_block=events['block'],
            pool_logs=events['sync_logs'] + events['mint_logs'])
        expected_tx = '0xe722f3db159d390decd678fc7b1a5a7f863599a52d07b737e5be6be0b101d112'
        self.assertEqual(checked['status'], 'DELAYED_FIRST_MINT_SYNC_CONFIRMED')
        self.assertEqual(checked['first_delayed_mint_tx'], expected_tx)
        self.assertEqual(len(expected_tx), 66)
        self.assertEqual(checked['reserve0_raw'], '98000000000000000000000000')
        self.assertEqual(checked['reserve1_raw'], '15000000000000000000')
        self.assertEqual(checked['sell_path'], 'UNKNOWN')
        source = archive['bsc_v2_p0_reference_sequential_amm_20261020']
        self.assertEqual(source['quote_reserve_vectors_reconstructable_from_committed_normalized_logs'], 27)
        self.assertEqual(source['unknown_reserve_vector_ranks'], [16, 17, 18])

    def test_delayed_mint_matches_sync_and_prevents_early_entry(self):
        from mission_agent.early.bsc_v2_pit import verify_delayed_mint_sync
        pair='0x'+'7'*40
        tx='0x'+'8'*64
        sync=dict(address=pair,blockNumber=hex(20),logIndex=hex(3),transactionHash=tx,
                  topics=[SYNC],data='0x'+word(100)+word(200),removed=False)
        mint=dict(sync,logIndex=hex(4),topics=[MINT])
        found=verify_delayed_mint_sync(pool=pair,creation_block=10,update_block=20,
                                       pool_logs=[sync,mint])
        self.assertTrue(found['delayed_initial_liquidity_proven'])
        self.assertEqual(found['sell_path'],'UNKNOWN')
        self.assertEqual(found['first_trade_or_executable_t_entry'],'UNRESOLVED')
        self.assertFalse(verify_delayed_mint_sync(pool=pair,creation_block=10,
                          update_block=20,pool_logs=[sync])['delayed_initial_liquidity_proven'])
        with self.assertRaisesRegex(PITInvalid,'DELAYED_LIQUIDITY_BLOCK'):
            verify_delayed_mint_sync(pool=pair,creation_block=20,update_block=20,
                                     pool_logs=[sync,mint])
        with self.assertRaisesRegex(PITInvalid,'DELAYED_POOL_LOG_SOURCE'):
            verify_delayed_mint_sync(pool=pair,creation_block=10,update_block=20,
                                     pool_logs=[dict(sync,address='0x'+'9'*40),mint])



class V2HistoricQuoteAndSwapEvidenceTests(unittest.TestCase):
    def test_pancake_v2_fee_integer_math_matches_four_historical_router_reads(self):
        from mission_agent.early.bsc_v2_pit import v2_static_two_way_quote
        # Each result below was read using getAmountsOut at the specified historical
        # block, including the second reverse view against UNCHANGED pool storage.
        cases = [
            (10000000000000000000, 10000000000000000000000, 1600000000000000000000, 1594409576447493625, 9930276362283922020),
            (10000000000000000, 8300000000000000000, 4600000000000000000000000000, 5521677261363602176901855, 9926233485230985),
            (1000000000000000000, 1313968229661012727, 850000000000000000, 366812309648030379, 395408042268688956),
            (10000000000000000, 17000000000000000000, 500000000000000000000000000, 293210307481345504623022, 9938414057573645),
        ]
        for amount, quote, token, expected_buy, expected_reverse in cases:
            with self.subTest(amount=amount, quote=quote):
                q = v2_static_two_way_quote(amount, quote, token)
                self.assertEqual(int(q['indicative_token_out_raw']), expected_buy)
                self.assertEqual(int(q['reverse_quote_back_raw']), expected_reverse)
                self.assertEqual(q['historical_sell_executable'], 'UNVERIFIED')
                self.assertEqual(q['sequential_roundtrip_pnl'], 'NOT_COMPUTED')

    def test_sequential_roundtrip_uses_post_buy_reserves_and_never_claims_execution(self):
        from mission_agent.early.bsc_v2_pit import (
            v2_reference_sequential_roundtrip, v2_static_two_way_quote)
        samples = [
            (10000000000000000000, 10000000000000000000000, 1600000000000000000000, 9950112138733759041),
            (10000000000000000, 8300000000000000000, 4600000000000000000000000000, 9950122293529727),
            (1000000000000000000, 1313968229661012727, 850000000000000000, 997158206422518356),
            (10000000000000000, 17000000000000000000, 500000000000000000000000000, 9950091711211336),
        ]
        for amount, reserve_quote, reserve_token, back in samples:
            with self.subTest(amount=amount, reserve_quote=reserve_quote):
                seq = v2_reference_sequential_roundtrip(amount, reserve_quote, reserve_token)
                static = v2_static_two_way_quote(amount, reserve_quote, reserve_token)
                self.assertEqual(seq['token_bought_raw'], static['indicative_token_out_raw'])
                self.assertEqual(int(seq['reference_quote_back_raw']), back)
                self.assertGreater(back, int(static['reverse_quote_back_raw']))
                self.assertFalse(seq['historical_trade_execution_verified'])
                self.assertEqual(seq['sellable_at_notional'], 'UNVERIFIED')
                self.assertEqual(seq['paper_net_pnl_status'], 'NOT_SCORABLE')

    def test_sequential_amm_reference_rejects_invalid_or_dust_input(self):
        from mission_agent.early.bsc_v2_pit import v2_reference_sequential_roundtrip
        for inputs in [('1', 1000, 1000), (1, 1000000, 1),
                       (0, 10, 10), (10, 0, 100), (10, 100, 0)]:
            with self.subTest(inputs=inputs), self.assertRaises(PITInvalid):
                v2_reference_sequential_roundtrip(*inputs)

    def test_invalid_or_uneconomical_quotes_fail_closed(self):
        from mission_agent.early.bsc_v2_pit import v2_static_two_way_quote
        for args in [(1, 0, 1000), (0, 100, 1000), ('10', 100, 1000), (100, 1000, 1)]:
            with self.subTest(args=args), self.assertRaises(PITInvalid):
                v2_static_two_way_quote(*args)

    def test_replay_three_actual_swap_directions_but_not_sell_guarantees(self):
        from mission_agent.early.bsc_v2_pit import classify_v2_swap_by_quote_side
        evidence = json.loads((Path(__file__).resolve().parents[2] /
            'monster/evidence/early/P0/P0_SOURCE_PROBE_20261019.json').read_text())
        src = evidence['historical_bsc_v2_append_only_factory_enumeration']
        proofs = src['creation_liquidity_source_spotchecks']['first_later_reserve_update_events']
        for rank, direction in [(1,'OBSERVED_QUOTE_TO_TOKEN_SWAP'),
                                (2,'OBSERVED_QUOTE_TO_TOKEN_SWAP'),
                                (5,'OBSERVED_TOKEN_TO_QUOTE_SWAP')]:
            event = next(q for q in proofs if q['rank'] == rank)
            swap = next(x for x in event['events'] if x['topics'][0].lower() == SWAP)
            observed = classify_v2_swap_by_quote_side(swap, quote_is_token0=True)
            self.assertEqual(observed['direction'], direction)
            self.assertEqual(observed['user_same_notional_sellability'], 'UNVERIFIED')
            with self.assertRaisesRegex(PITInvalid, 'NOT_A_V2_SWAP'):
                classify_v2_swap_by_quote_side(
                    {**swap,'topics':[SYNC]}, quote_is_token0=True)


    def test_three_historical_archived_swap_windows_preserve_buy_sell_directions(self):
        from mission_agent.early.bsc_v2_pit import summarize_v2_archived_swap_windows
        archive = json.loads((Path(__file__).resolve().parents[2] /
            'monster/evidence/early/P0/P0_SOURCE_PROBE_20261019.json').read_text())
        history = archive['historical_bsc_v2_append_only_factory_enumeration']
        cohort = {x['cohort_rank']: x for x in history['chronological_quoted_unique_first30']}
        pairs = {x['factory_index_zero_based']: x for x in history['first36']}
        events = history['creation_liquidity_source_spotchecks']['first_later_reserve_update_events']
        for rank, expected in [(1, 'OBSERVED_QUOTE_TO_TOKEN_SWAP'),
                               (2, 'OBSERVED_QUOTE_TO_TOKEN_SWAP'),
                               (5, 'OBSERVED_TOKEN_TO_QUOTE_SWAP')]:
            case = next(x for x in events if x['rank'] == rank)
            item = cohort[rank]
            identity = pairs[item['factory_index']]
            with self.subTest(rank=rank):
                result = summarize_v2_archived_swap_windows(
                    pool=case['pool'], token0=identity['token0'],
                    token1=identity['token1'], quote_asset=item['quote_asset'],
                    windows=[{'name': 'FIRST_LATER_POOL_UPDATE', 'logs': case['events']}])
                self.assertEqual(result['observed_swap_events'], 1)
                self.assertEqual(result['swap_with_prior_same_tx_sync'], 1)
                self.assertEqual(
                    result['first_observed_in_saved_windows']['direction'], expected)
                self.assertEqual(result['historical_token_tax_and_user_sellability'],
                                 'UNVERIFIED')
                self.assertEqual(result['eighteen_of_thirty_sellable_gate'], 'NOT_SCORABLE')

    def test_archived_swap_missing_sync_overlap_and_wrong_scope_fail_closed(self):
        from mission_agent.early.bsc_v2_pit import summarize_v2_archived_swap_windows
        archive = json.loads((Path(__file__).resolve().parents[2] /
            'monster/evidence/early/P0/P0_SOURCE_PROBE_20261019.json').read_text())
        history = archive['historical_bsc_v2_append_only_factory_enumeration']
        case = history['creation_liquidity_source_spotchecks']['first_later_reserve_update_events'][2]
        item = history['chronological_quoted_unique_first30'][4]
        identity = next(r for r in history['first36']
                        if r['factory_index_zero_based'] == item['factory_index'])
        kwargs = dict(pool=item['pool'], token0=identity['token0'],
                      token1=identity['token1'], quote_asset=item['quote_asset'])
        swap = next(x for x in case['events'] if x['topics'][0].lower() == SWAP)
        no_sync = summarize_v2_archived_swap_windows(
            **kwargs, windows=[{'name': 'PARTIAL', 'logs': [swap]}])
        self.assertEqual(no_sync['observed_swap_events'], 1)
        self.assertEqual(no_sync['observed_token_to_quote_with_sync'], 0)
        self.assertEqual(no_sync['absence_of_swap_in_missing_intervals'], 'UNKNOWN')
        repeated = summarize_v2_archived_swap_windows(
            **kwargs, windows=[{'name': 'A', 'logs': case['events']},
                               {'name': 'B', 'logs': case['events']}])
        self.assertEqual(repeated['observed_swap_events'], 1)
        self.assertEqual(repeated['observed_token_to_quote_with_sync'], 1)
        empty = summarize_v2_archived_swap_windows(
            **kwargs, windows=[{'name': 'NONE', 'logs': []}])
        self.assertEqual(empty['observed_swap_events'], 0)
        self.assertIsNone(empty['first_observed_in_saved_windows'])
        with self.assertRaisesRegex(PITInvalid, 'WRONG_PAIR'):
            summarize_v2_archived_swap_windows(
                **kwargs, windows=[{'name': 'WRONG', 'logs': [
                    {**swap, 'address': '0x' + 'f'*40}]}])
        with self.assertRaisesRegex(PITInvalid, 'SCOPE_OR_QUOTE_INVALID'):
            summarize_v2_archived_swap_windows(
                **{**kwargs, 'quote_asset': '0x'+'f'*40},
                windows=[{'name': 'A', 'logs': case['events']}])


    def test_historical_first_runtime_code_boundary_and_preexisting(self):
        from mission_agent.early.bsc_v2_pit import locate_first_runtime_code_block
        day_start = 52440287
        boundaries = [(52440593, 52440617), (52440672, 52440691),
                      (52440725, 52440950), (52441208, 52441231)]
        for deployed_state, pool in boundaries:
            with self.subTest(first_code=deployed_state):
                visited = []
                def has_code(block):
                    visited.append(block)
                    return block >= deployed_state
                result = locate_first_runtime_code_block(day_start, pool, has_code)
                self.assertEqual(result['status'],
                                 'FIRST_NONEMPTY_CODE_IN_FROZEN_DAY_BLOCK_STATE')
                self.assertEqual(result['first_code_block_in_day'], deployed_state)
                self.assertIn(deployed_state - 1, visited)
                self.assertIn(deployed_state, visited)
                self.assertFalse(result['deploy_transaction_verified'])
                self.assertEqual(result['public_observed_at'], 'UNVERIFIED')
        before = locate_first_runtime_code_block(
            day_start, 52440324, lambda b: b >= day_start - 20)
        self.assertEqual(before['status'], 'RUNTIME_CODE_PREEXISTS_FROZEN_UTC_DAY')
        self.assertIsNone(before['first_code_block_in_day'])
        with self.assertRaisesRegex(PITInvalid, 'NO_RUNTIME_CODE'):
            locate_first_runtime_code_block(day_start, day_start + 3, lambda b: False)
        with self.assertRaisesRegex(PITInvalid, 'NOT_BOOLEAN'):
            locate_first_runtime_code_block(day_start, day_start + 3, lambda b: None)
        with self.assertRaisesRegex(PITInvalid, 'INVALID_HISTORIC_CODE_SEARCH_RANGE'):
            locate_first_runtime_code_block(day_start, day_start - 1, lambda b: True)


    def test_real_three_swaps_reconstruct_pretrade_quote_depth_and_frozen_floor(self):
        from mission_agent.early.bsc_v2_pit import summarize_v2_archived_swap_windows
        archive = json.loads((Path(__file__).resolve().parents[2] /
            'monster/evidence/early/P0/P0_SOURCE_PROBE_20261019.json').read_text())
        hist = archive['historical_bsc_v2_append_only_factory_enumeration']
        cases = hist['creation_liquidity_source_spotchecks']['cases']
        windows = hist['creation_liquidity_source_spotchecks']['first_later_reserve_update_events']
        by_index = {x['factory_index_zero_based']: x for x in hist['first36']}
        for rank in (1, 2, 5):
            case = cases[rank - 1]
            item = hist['chronological_quoted_unique_first30'][rank - 1]
            pair = by_index[item['factory_index']]
            event = next(x for x in windows if x['rank'] == rank)
            floor = 1000 * 10**18 if item['quote_asset'].lower().startswith(
                '0x55d398') else 2 * 10**18
            result = summarize_v2_archived_swap_windows(
                pool=case['pair'], token0=pair['token0'], token1=pair['token1'],
                quote_asset=item['quote_asset'], quote_reserve_floor_raw=floor,
                windows=[{'name': 'SAVED_LATER', 'logs': event['events']}])
            fact = result['first_observed_in_saved_windows']
            self.assertTrue(fact['immediately_preceding_same_tx_pool_sync'])
            expected = (case['initial_reserve0_raw']
                        if item['quote_asset'].lower() == pair['token0'].lower()
                        else case['initial_reserve1_raw'])
            self.assertEqual(int(fact['pre_swap_quote_reserve_raw']), int(expected))
            self.assertEqual(result['observed_swaps_without_proven_preswap_depth'], 0)
            self.assertEqual(
                fact['pre_swap_quote_depth_frozen_floor_status'],
                'BELOW_FROZEN_FLOOR' if rank == 5 else 'AT_OR_ABOVE_FROZEN_FLOOR')
            self.assertEqual(result['eighteen_of_thirty_sellable_gate'], 'NOT_SCORABLE')

    def test_missing_or_invalid_adjacent_sync_never_promotes_quote_depth(self):
        from mission_agent.early.bsc_v2_pit import summarize_v2_archived_swap_windows
        pool = '0x' + '1'*40
        token0 = '0x' + '2'*40
        token1 = '0x' + '3'*40
        tx = '0x' + 'a'*64
        base = dict(address=pool, blockNumber='0x20', transactionIndex='0x1',
                    transactionHash=tx, removed=False)
        sync = dict(base, logIndex='0x5', topics=[SYNC],
                    data='0x'+word(1200)+word(10000))
        swap = dict(base, logIndex='0x6',
                    topics=[SWAP, topic(token0), topic(token1)],
                    data='0x'+word(200)+word(0)+word(0)+word(1500))
        kwargs = dict(pool=pool, token0=token0, token1=token1,
                      quote_asset=token0, quote_reserve_floor_raw=1000,
                      windows=[{'name': 'SAVED', 'logs': [sync, swap]}])
        valid = summarize_v2_archived_swap_windows(**kwargs)
        event = valid['observed_direction_events'][0]
        self.assertEqual(event['pre_swap_quote_reserve_raw'], '1000')
        self.assertEqual(event['post_swap_quote_reserve_raw'], '1200')
        self.assertEqual(valid['observed_buy_at_or_above_frozen_quote_depth'], 1)
        missing = summarize_v2_archived_swap_windows(
            **{**kwargs, 'windows': [{'name': 'PARTIAL', 'logs': [swap]}]})
        self.assertIsNone(missing['observed_direction_events'][0]['pre_swap_quote_reserve_raw'])
        self.assertEqual(missing['observed_buy_at_or_above_frozen_quote_depth'], 0)
        intervening = dict(base, logIndex='0x5', topics=[MINT],
                           data='0x'+word(1)+word(1))
        noadj = summarize_v2_archived_swap_windows(
            **{**kwargs, 'windows': [{'name': 'NOT_ADJACENT',
                                       'logs': [sync, {**intervening, 'logIndex': '0x7'},
                                                {**swap, 'logIndex': '0x8'}]}]})
        self.assertEqual(noadj['observed_buy_at_or_above_frozen_quote_depth'], 0)
        with self.assertRaisesRegex(PITInvalid, 'FLOOR_INVALID'):
            summarize_v2_archived_swap_windows(
                **{**kwargs, 'quote_reserve_floor_raw': '1000'})
        with self.assertRaisesRegex(PITInvalid, 'IMPOSSIBLE_PRETRADE_RESERVE'):
            summarize_v2_archived_swap_windows(
                **{**kwargs, 'windows': [{'name': 'INVALID', 'logs': [
                    {**sync, 'data': '0x'+word(100)+word(10000)}, swap]}]})



if __name__=='__main__':
    unittest.main()
