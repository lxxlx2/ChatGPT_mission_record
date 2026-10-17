import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from receipt_probe import inspect_receipt, normalized_wallet, TRANSFER, APPROVAL

W='0x0d8d6c105629e472691f9a970a6f70899195b5e0'
T='0xd7ccd29b6fd1464edb425f24b01115556e737777'
H='0x'+'a'*64
BH='0x'+'b'*64

def sample():
 tx={'chainId':'0x38','hash':H,'from':W,'to':T,'blockHash':BH,'blockNumber':'0x10','input':'0x095ea7b3','value':'0x0','gasPrice':'0x80'}
 receipt={'transactionHash':H,'from':W,'to':T,'blockHash':BH,'blockNumber':'0x10','status':'0x1','gasUsed':'0x10','effectiveGasPrice':'0x80','logs':[{'transactionHash':H,'address':T,'topics':[APPROVAL,'0x'+'0'*24+W[2:],'0x'+'0'*64],'data':'0x'+'0'*64}]}
 return tx,receipt

def transfer(frm,to,quantity,token=T):
 return {'transactionHash':H,'address':token,'topics':[TRANSFER,'0x'+'0'*24+frm[2:],'0x'+'0'*24+to[2:]],'data':'0x'+format(quantity,'064x')}

class TestReceiptProbe(unittest.TestCase):
 def test_approval_real_shape_no_pnl(self):
  tx,receipt=sample();d=inspect_receipt(tx,receipt,W,'bnb-mainnet')
  self.assertEqual(d['status'],'RECEIPT_FACTS_ONLY')
  self.assertEqual(d['classification'],'APPROVAL_NOT_TRADE')
  self.assertEqual(d['gas_cost_native_wei'],'2048')
  self.assertEqual(d['trade_execution'],'UNRESOLVED')
 def test_erc20_net_in(self):
  tx,r=sample();tx['input']='0x12345678';r['logs']=[transfer('0x'+'1'*40,W,12345)]
  d=inspect_receipt(tx,r,W,'bnb-mainnet');self.assertEqual(d['erc20_flows'][T]['net_raw'],'12345')
  self.assertEqual(d['trade_execution'],'UNRESOLVED')
 def test_erc20_net_out_fee_tax(self):
  tx,r=sample();tx['input']='0x12345678';r['logs']=[transfer(W,'0x'+'1'*40,123),transfer(W,'0x'+'2'*40,7)]
  d=inspect_receipt(tx,r,W,'bnb-mainnet');self.assertEqual(d['erc20_flows'][T]['net_raw'],'-130')
 def test_same_wallet_transfer_net_zero(self):
  tx,r=sample();tx['input']='0x12345678';r['logs']=[transfer(W,W,55)]
  self.assertEqual(inspect_receipt(tx,r,W,'bnb-mainnet')['erc20_flows'][T]['net_raw'],'0')
 def test_fails_reverted(self):
  tx,r=sample();r['status']='0x0';self.assertEqual(inspect_receipt(tx,r,W,'bnb-mainnet')['status'],'PNL_UNRESOLVED')
 def test_fails_truncated(self):
  tx,r=sample();r.pop('gasUsed');self.assertEqual(inspect_receipt(tx,r,W,'bnb-mainnet')['status'],'PNL_UNRESOLVED')
 def test_wrong_chain(self):
  tx,r=sample();self.assertEqual(inspect_receipt(tx,r,W,'eth-mainnet')['status'],'PNL_UNRESOLVED')
 def test_wrong_sender(self):
  tx,r=sample();tx['from']='0x'+'1'*40;self.assertEqual(inspect_receipt(tx,r,W,'bnb-mainnet')['status'],'PNL_UNRESOLVED')
 def test_wrong_hash(self):
  tx,r=sample();r['transactionHash']='0x'+'c'*64;self.assertEqual(inspect_receipt(tx,r,W,'bnb-mainnet')['status'],'PNL_UNRESOLVED')
 def test_wrong_block(self):
  tx,r=sample();r['blockHash']='0x'+'c'*64;self.assertEqual(inspect_receipt(tx,r,W,'bnb-mainnet')['status'],'PNL_UNRESOLVED')
 def test_log_hash_mismatch(self):
  tx,r=sample();r['logs'][0]['transactionHash']='0x'+'c'*64;self.assertEqual(inspect_receipt(tx,r,W,'bnb-mainnet')['status'],'PNL_UNRESOLVED')
 def test_nonstandard_transfer_unresolved(self):
  tx,r=sample();r['logs']=[transfer('0x'+'1'*40,W,50)];r['logs'][0]['topics']=r['logs'][0]['topics'][:2]
  self.assertEqual(inspect_receipt(tx,r,W,'bnb-mainnet')['status'],'PNL_UNRESOLVED')
 def test_native_sale_unresolved(self):
  tx,r=sample();tx['input']='0x12345678';r['logs']=[]
  d=inspect_receipt(tx,r,W,'bnb-mainnet');self.assertEqual(d['native_incoming_wei'],'UNRESOLVED_INTERNAL_TRACE')
 def test_native_direct_not_trade(self):
  tx,r=sample();tx['input']='0x';tx['value']='0x100';r['logs']=[]
  d=inspect_receipt(tx,r,W,'bnb-mainnet');self.assertEqual(d['classification'],'NATIVE_TRANSFER_NOT_TRADE_PROVEN')
 def test_source_rejects_swapped_rows(self):
  src={'source_blob_sha':'954f3aba66be21911dd627fa40dd3dd0a9fd1d26','total':449,'items':[{'index':i,'batch':(i-1)//20+1,'address':'0x'+format(i,'040x')} for i in range(1,450)]}
  self.assertEqual(normalized_wallet(src,2),src['items'][1]['address']);src['items'][0],src['items'][1]=src['items'][1],src['items'][0]
  with self.assertRaises(ValueError):normalized_wallet(src,2)
 def test_receipt_effective_gas_price_precedence(self):
  tx,r=sample();tx['gasPrice']='0x40';r['effectiveGasPrice']='0x81';self.assertEqual(inspect_receipt(tx,r,W,'bnb-mainnet')['gas_cost_native_wei'],str(16*129))
 def test_source_duplicate_fails(self):
  src={'source_blob_sha':'954f3aba66be21911dd627fa40dd3dd0a9fd1d26','total':449,'items':[{'index':i,'batch':(i-1)//20+1,'address':'0x'+format(i,'040x')} for i in range(1,450)]}
  src['items'][1]['address']=src['items'][0]['address']
  with self.assertRaises(ValueError):normalized_wallet(src,2)

if __name__=='__main__':unittest.main()
