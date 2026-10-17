import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'tools' / 'closed_token_index.py'
spec = importlib.util.spec_from_file_location('closed_token_index', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    src = {'total':449, 'source_blob_sha':m.SOURCE,
           'items':[{'index':i,'address':'0x'+format(i, '040x')} for i in range(1,450)]}
    txs=[{'kind':'buy','hash':'0x'+'1'*64,'delta_bnb':-0.1}]+[
        {'kind':'sell','hash':'0x'+format(i, '064x'),'delta_bnb':0.01} for i in range(2,7)]
    rtx={'source_row':16,'wallet':src['items'][15]['address'], 'network':'bnb-mainnet',
         'opening_token_balance_before_buy_raw':'0','ending_token_balance_after_sells_raw':'0',
         'txs':txs,'token':'0x'+'f'*40,'token_symbol':'X','calculation':{'net_bnb':-0.05}}
    a=[]
    for row in (2,4):
        a.append({'row':row,'wallet':src['items'][row-1]['address'],'token':'0x'+'e'*40,
        'balance_of_raw':{'before_buy':'0','after_sale':'0','after_buy2':'3','before_sale':'3'},
        'buy_native_net_wallet_deltas_wei':['-60','-40'],
        'native_sale_net_wallet_delta_wei':'20','net_cost_wei':'100','net_gain_wei':'-80',
        'buy_tx_hashes':['0x'+'1'*64,'0x'+'2'*64],'sell_tx':'0x'+'3'*64,
        'sell_approval_same_block_tx':'0x'+'4'*64})
    sauce={'source_blob_sha':m.SOURCE,'network':'bnb-mainnet', 'token':{'address':'0x'+'e'*40,'symbol':'Y'},'roundtrips':a}
    return src,rtx,sauce


class ReplayTests(unittest.TestCase):
    def test_loss_is_preserved(self):
        report=m.index_sources(*fixture())
        self.assertEqual(report['negative_positions'],3)
        self.assertEqual(report['complete_wallet_30d_pnl'],0)
        self.assertEqual([v['row'] for v in report['entries']],[2,4,16])

    def test_bad_cost_rejected(self):
        x=list(fixture());x[2]['roundtrips'][0]['net_gain_wei']='1'
        with self.assertRaises(ValueError):m.index_sources(*x)

    def test_bad_identity_rejected(self):
        x=list(fixture());x[1]['wallet']=x[0]['items'][0]['address']
        with self.assertRaises(ValueError):m.index_sources(*x)

    def test_incomplete_inventory_rejected(self):
        x=list(fixture());x[2]['roundtrips'][1]['balance_of_raw']['after_sale']='1'
        with self.assertRaises(ValueError):m.index_sources(*x)

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):m.D('NaN')

if __name__ == '__main__': unittest.main()
