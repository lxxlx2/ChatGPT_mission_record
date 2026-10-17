import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from address_analysis import assert_source, nonce_pair, screen, replay_closed_token


def fixture():
    items = [{'index': i, 'batch': (i-1)//20+1,
              'address': '0x'+format(i, '040x')} for i in range(1,450)]
    return {'source_blob_sha': '954f3aba66be21911dd627fa40dd3dd0a9fd1d26', 'total':449, 'items':items}


def win():
    return {'bsc':{'from':{'height':'0x5','hash':'0x'+'a'*64}, 'to':{'height':'0x8','hash':'0x'+'b'*64}}}


class TestAddressAnalysis(unittest.TestCase):
    def test_source_pin_and_order(self):
        self.assertEqual(len(assert_source(fixture())),449)
        x=fixture();x['items'][0], x['items'][1]=x['items'][1], x['items'][0]
        with self.assertRaises(ValueError):assert_source(x)
        x=fixture();x['items'][1]['address']=x['items'][0]['address']
        with self.assertRaises(ValueError):assert_source(x)

    def test_nonce_exact_and_regression(self):
        v=iter(['0x3','0x10'])
        self.assertEqual(nonce_pair('endpoint','0x'+'1'*40,'0x5','0x8',lambda *args:next(v))['signed_delta'],13)
        v=iter(['0x10','0x3'])
        with self.assertRaises(ValueError):nonce_pair('endpoint','0x'+'1'*40,'0x5','0x8',lambda *args:next(v))

    def test_census_partial_never_zero_on_failure(self):
        def fake(url,method,params):
            if method=='eth_getBlockByNumber':
                return {'hash':'0x'+('a' if params[0]=='0x5' else 'b')*64,'number':params[0]}
            if params[0].endswith('0002'):raise RuntimeError('429')
            return '0x2' if params[1]=='0x5' else '0x5'
        x=screen(fixture(),win(),{'bsc':'endpoint'},1,caller=fake)
        self.assertEqual(x['status'],'PARTIAL')
        self.assertEqual(x['summary']['bsc']['checked'],19)
        self.assertEqual(x['summary']['bsc']['rpc_unresolved'],1)
        self.assertEqual(x['rows'][1]['networks']['bsc']['signed_delta'],None)
        self.assertEqual(x['summary']['bsc']['signed_tx_count'],57)

    def test_bad_block_hash_rejected(self):
        with self.assertRaisesRegex(ValueError,'BOUNDARY_BLOCK_MISMATCH'):
            screen(fixture(),win(),{'bsc':'endpoint'},1,caller=lambda *a:{'hash':'0x'+'c'*64,'number':'0x5'})

    def test_loss_no_cherrypicking(self):
        p={'balance_before':'0','balance_after':'0','basis_verified':True,
           'receipt_success':True,'provenance_complete':True,
           'token_contract':'0x'+'1'*40,'buy_native_cost_wei':'100','sell_native_net_wei':'20'}
        a=replay_closed_token(p)
        self.assertEqual(a['classification'],'LOSS')
        self.assertEqual(a['gain_wei'],'-80')
        p['provenance_complete']=False
        self.assertEqual(replay_closed_token(p)['status'],'PNL_UNRESOLVED')

    def test_known_sauce_values(self):
        for returned,expected in [('211142080278687674','156828105278687674'),
                                   ('208529773043203099','154215798043203099')]:
            p={'balance_before':'0','balance_after':'0','basis_verified':True,
               'receipt_success':True,'provenance_complete':True,
               'token_contract':'0xd7ccd29b6fd1464edb425f24b01115556e737777',
               'buy_native_cost_wei':'54313975000000000','sell_native_net_wei':returned}
            self.assertEqual(replay_closed_token(p)['gain_wei'],expected)

if __name__ == '__main__':unittest.main()
