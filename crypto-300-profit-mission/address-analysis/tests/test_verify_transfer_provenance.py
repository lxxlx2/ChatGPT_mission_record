import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'tools'))
from verify_transfer_provenance import validate, SOURCE


def sample():
    manifest={'total':449,'source_blob_sha':SOURCE,'items':[{'index':i,'batch':(i-1)//20+1,'address':'0x'+format(i,'040x')} for i in range(1,450)]}
    cases=[]
    for row in (2,7,15):
        wallet=manifest['items'][row-1]['address']
        token='0x'+format(row+900, '040x')
        froms=[{'block':'0x110','hash':'0x'+format(row*10+1,'064x'),'from':'0x'+'f'*40,'to':wallet,'raw_amount':'100','token_contract':token}]
        out_to=manifest['items'][0]['address'] if row==2 else '0x'+'e'*40
        outs=[{'block':'0x120','hash':'0x'+format(row*10+2,'064x'),'from':wallet,'to':out_to,'raw_amount':'50','token_contract':token,'destination_original_source_row':1 if row==2 else None}]
        cases.append({'source_row':row,'wallet':wallet,'token_contract':token,'network':'bnb-mainnet','accounting_classification':'COST_BASIS_UNKNOWN',
        'transfer_inventory':{'inbound_events':froms,'outbound_events':outs,'opening_token_raw':'0','total_in_raw':'100','total_out_raw':'50','ending_token_raw':'50','alchemy_erc20_pagination_complete_inbound':True,'alchemy_erc20_pagination_complete_outbound':True},
        'historical_balance_snapshots':[{'block':'0x100','balance':'0'},{'block':'0x120','balance':'50'}],'native_block_deltas':[]})
    return manifest,{'schema':'mission-address-analysis-batch001-three-pending-erc20-provenance-v1','immutable_source_blob':SOURCE,
        'network':'bnb-mainnet','bound':{'fromBlock':'0x0','toBlock':'0x7a4ca36'},'cases':cases}


class TestDisposition(unittest.TestCase):
    def test_valid_flow_not_profit(self):
        manifest,ev=sample();v=validate(manifest,ev)
        self.assertEqual(v['status'],'ARCHIVED_FLOW_CONSISTENT_ONLY')
        self.assertEqual(len(v['records']),3)
        self.assertEqual(v['records'][0]['profit_or_loss'],'UNRESOLVED')
        self.assertEqual(v['wallet_30d_pnl'],'UNRESOLVED')
    def test_missing_paginated_history_rejected(self):
        a,b=sample();b['cases'][0]['transfer_inventory']['alchemy_erc20_pagination_complete_inbound']=False
        self.assertEqual(validate(a,b)['status'],'PNL_UNRESOLVED')
    def test_forged_zero_cost_origin_not_promoted(self):
        a,b=sample();b['cases'][0]['accounting_classification']='COST_ZERO_CLAIM'
        self.assertEqual(validate(a,b)['records'][0]['profit_or_loss'],'UNRESOLVED')
    def test_ledger_outflow_without_inbound_rejected(self):
        a,b=sample();b['cases'][0]['transfer_inventory']['outbound_events'][0]['raw_amount']='500'
        self.assertEqual(validate(a,b)['status'],'PNL_UNRESOLVED')
    def test_forged_source_row_identity_rejected(self):
        a,b=sample();b['cases'][0]['wallet']=a['items'][0]['address']
        self.assertEqual(validate(a,b)['status'],'PNL_UNRESOLVED')
    def test_outbound_known_source_recipient_required(self):
        a,b=sample();b['cases'][0]['transfer_inventory']['outbound_events'][0]['destination_original_source_row']=None
        self.assertEqual(validate(a,b)['status'],'PNL_UNRESOLVED')
    def test_balance_after_end_mismatch_rejected(self):
        a,b=sample();b['cases'][1]['historical_balance_snapshots'][-1]['balance']='0'
        self.assertEqual(validate(a,b)['status'],'PNL_UNRESOLVED')
    def test_unverified_extra_wallet_rejected(self):
        a,b=sample();b['cases'].append(copy.deepcopy(b['cases'][0]))
        self.assertEqual(validate(a,b)['status'],'PNL_UNRESOLVED')
    def test_native_cashflow_block_pair_recomputed(self):
        a,b=sample();snap=b['cases'][2]['historical_balance_snapshots'];snap[0]['block']='0x11f';snap[0]['BNBWei']='1000';snap[0]['nonce']=2
        snap[1]['BNBWei']='1400';snap[1]['nonce']=4
        b['cases'][2]['native_block_deltas']=[{'at_block':'0x120','block_level_delta_wei':'400','signed_nonce_delta':2,'token_delta_raw':'50'}]
        self.assertEqual(validate(a,b)['status'],'ARCHIVED_FLOW_CONSISTENT_ONLY')
        b['cases'][2]['native_block_deltas'][0]['block_level_delta_wei']='401'
        self.assertEqual(validate(a,b)['status'],'PNL_UNRESOLVED')
    def test_fabricated_negative_loss_never_counted(self):
        a,b=sample();b['cases'][1]['accounting_classification']='LOSS_CONFIRMED'
        self.assertEqual(validate(a,b)['records'][1]['profit_or_loss'],'UNRESOLVED')

if __name__=='__main__': unittest.main()
