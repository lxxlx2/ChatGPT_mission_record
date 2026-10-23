import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from verify_block_roundtrip import audit, HEIGHTS, EVENT_HEIGHTS, SRC, TRANSFER

TOKEN='0xd7ccd29b6fd1464edb425f24b01115556e737777'
WALLETS={2:'0x0d8d6c105629e472691f9a970a6f70899195b5e0',4:'0x00077705952c90b728c6d7dc450beb4429331111'}

def sample():
    src={'total':449,'source_blob_sha':SRC,'items':[{'index':i,'batch':(i-1)//20+1,'address':WALLETS.get(i,'0x'+format(i,'040x'))} for i in range(1,450)]}
    rows=[]
    for row,wallet in WALLETS.items():
        txs=['0x'+format(row*10+i,'064x') for i in range(3)]
        amounts=[100,200,40,260]
        native=[1000,900,900,800,800,1200]
        nonce=[10,11,11,12,19,21]
        logs=[]
        for i,amount in enumerate(amounts):
            frm='0x'+'1'*40 if i<2 else wallet
            to=wallet if i<2 else '0x'+'1'*40
            logs.append({'block':EVENT_HEIGHTS[i], 'transactionHash':txs[min(i,2)],'contract':TOKEN,
                         'topic0':TRANSFER,'topic1':'0x'+frm[2:].rjust(64,'0'),
                         'topic2':'0x'+to[2:].rjust(64,'0'),'data':'0x'+format(amount,'064x')})
        rows.append({'source_row':row,'wallet':wallet,'buy_tx_hashes':txs[:2], 'sell_tx_hash':txs[2],
                     'transfer_logs':logs,'reverse_direction_logs_per_relevant_block':0,
                     'balance_snapshots':[{'block':b,'native_balance_wei':str(native[i]),'token_raw':(['0','100',None,'300','300','0'][i]),'nonce':nonce[i]} for i,b in enumerate(HEIGHTS)],
                     'buy_block_native_deltas_wei':['-100','-100'],'sale_block_native_delta_wei':'400','observed_native_block_net_wei':'200'})
    evidence={'schema':'mission-sauce-rows-002-004-narrow-erc20-and-native-block-proof-v1','original_source_blob_sha':SRC,'token_contract':TOKEN,'records':rows}
    return evidence,src

class Suite(unittest.TestCase):
    def test_positive_saved_structure_not_wallet_pnl(self):
        d,m=sample();r=audit(d,m)
        self.assertEqual(r['status'],'SAVED_CHAIN_EVIDENCE_REPLAY');self.assertEqual([x['observed_native_block_net_wei'] for x in r['records']],['200','200'])
        self.assertEqual(r['wallet_pnl_status'],'UNRESOLVED')
    def test_wrong_wallet(self):
        d,m=sample();d['records'][0]['wallet']=m['items'][1]['address'].replace('0d8d','0000')
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_duplicate_row(self):
        d,m=sample();d['records'][1]['source_row']=2
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_extra_outbound_activity_fails(self):
        d,m=sample();d['records'][0]['reverse_direction_logs_per_relevant_block']=1
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_second_sale_transfer_not_ignored(self):
        d,m=sample();d['records'][0]['transfer_logs'].pop()
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_nonmatching_txhash(self):
        d,m=sample();d['records'][0]['transfer_logs'][0]['transactionHash']='0x'+'f'*64
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_nonce_gap_mismatch(self):
        d,m=sample();d['records'][0]['balance_snapshots'][1]['nonce']+=1
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_native_balance_mismatch(self):
        d,m=sample();d['records'][0]['balance_snapshots'][5]['native_balance_wei']='999'
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_token_snapshot_mismatch(self):
        d,m=sample();d['records'][0]['balance_snapshots'][3]['token_raw']='299'
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_forged_contract_fails(self):
        d,m=sample();d['records'][0]['transfer_logs'][0]['contract']='0x'+'0'*40
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_forged_manifest_order_fails(self):
        d,m=sample();m['items'][0],m['items'][1]=m['items'][1],m['items'][0]
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_outside_block_log_fails(self):
        d,m=sample();d['records'][0]['transfer_logs'][2]['block']=HEIGHTS[4]
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')

if __name__=='__main__':unittest.main()
