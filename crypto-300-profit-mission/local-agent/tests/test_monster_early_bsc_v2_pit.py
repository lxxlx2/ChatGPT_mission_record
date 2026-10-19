"""No-network regressions for historical BSC V2 initial pool liquidity PIT."""
import json
import unittest
from pathlib import Path
from mission_agent.early.bsc_v2_pit import (
    PAIR_CREATED, SYNC, MINT, PITInvalid, first_creation_block, verify_bootstrap,
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
                self.assertTrue(fact['initial_quote_liquidity_proven'])
                self.assertEqual(fact['creation_tx'], case['creation_tx_hash'])
                self.assertEqual(fact['reserve0_raw'], case['initial_reserve0_raw'])
                self.assertEqual(fact['reserve1_raw'], case['initial_reserve1_raw'])
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


if __name__=='__main__':
    unittest.main()
