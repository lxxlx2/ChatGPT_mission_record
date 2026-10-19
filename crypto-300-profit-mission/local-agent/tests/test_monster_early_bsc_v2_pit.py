"""No-network regressions for historical BSC V2 initial pool liquidity PIT."""
import unittest
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


if __name__=='__main__':
    unittest.main()
