import copy
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from lineage_gate import audit, MANIFEST_SHA

SOURCE='0x1c2bffb85341275feb01986241e5067feac16e3f'
A='0xd68def46b1114f51b7e676e6dde89069a2f3fe1a'
B='0x29935ef1417e1c3b1fec68dd666ea9baac31d4ed'
REC=['0x64e5903a79803726fe62bb45b9603f8436ddd1e4','0x88669768e431ad1e6861982309cc694ced330903','0x43e06d3f7c68dcaef4a936a6d4b10894213ded83','0xbeaba42106867743db849d9b26c049f654c54c5e']
H='0x'+'a'*64

def sample():
    manifest={'total':449,'source_blob_sha':MANIFEST_SHA,'items':[{'index':i,'batch':(i-1)//20+1,'address':A if i==15 else B if i==16 else '0x'+format(i,'040x')} for i in range(1,450)]}
    sizes=[3807941716484258253865819,3585042282796115601117696,3455180319427221023944265,3390453993350452655743972,3173276182721853326826943,3170468772755983983773696]
    # no dependence on the precise amounts for untracked receivers
    recipients=[{'address':addr,'source_row':next((i for i,x in enumerate(manifest['items'],1) if x['address']==addr),None), 'amount_raw':str(q), 'source_transaction_hash':H} for addr,q in zip([A,REC[0],REC[1],B,REC[2],REC[3]],sizes)]
    total=sum(sizes)
    buys=[{'hash':'0x'+format(k,'064x'),'native_input_wei':str(paid),'native_wallet_before_wei':str(a),'native_wallet_after_wei':str(b),'token_before_raw':str(before),'token_after_raw':str(after),'sender_nonce_before':nonce,'sender_nonce_after':nonce+1} for k,paid,a,b,before,after,nonce in [
        (1,226792542378128696,5043988649489443163,4816708586001314467,0,13546946872013679602415418,560),
        (2,198253606161547406,4816708586001314467,4617811300249767061,13546946872013679602415418,24352551174882903706205602,561)]]
    total_source=24352551174882903706205602
    exits={'15':{'wallet':A,'received':str(sizes[0]),'closing_raw':'0','transfers':[{'hash':'0x'+format(3,'064x'),'amount_raw':'1942050275406971709471567'},{'hash':'0x'+format(4,'064x'),'amount_raw':str(sizes[0]-1942050275406971709471567)}]},'16':{'wallet':B,'received':str(sizes[3]),'closing_raw':'0','transfers':[{'hash':'0x'+format(5,'064x'),'amount_raw':'2339413255411812332463340'},{'hash':'0x'+format(6,'064x'),'amount_raw':str(sizes[3]-2339413255411812332463340)}]}}
    lineage={'schema':'mission-bsc-hodl-funded-distributor-lineage-v1','frozen_manifest_blob_sha':MANIFEST_SHA,'chain':'bnb-mainnet','token_contract':'0x'+'c'*40,'upstream':{'wallet':SOURCE,'funding_buys':buys,'distribution_tx':H,'recipients':recipients,'bought_token_raw':str(total_source),'remaining_token_raw':str(total_source-total),'post_distribution_balance_raw':str(total_source-total),'buy_total_native_transaction_value_wei':'425046148539676102','buy_block_wallet_native_outflow_wei':'426177349239676102'},'source_wallet_exits':exits}
    return lineage,manifest

class Tests(unittest.TestCase):
    def test_valid_never_assign_basis(self):
        d,m=sample(); r=audit(d,m)
        self.assertEqual(r['status'],'GROUP_TRANSFER_CONSERVATION_ONLY')
        self.assertEqual(r['cost_basis_allocation'],'BLOCKED_NO_ECONOMIC_OWNERSHIP_PROOF')
        self.assertEqual([x['row'] for x in r['recipient_rows']],[15,16])
        self.assertEqual([x['wallet_pnl'] for x in r['recipient_rows']],['UNRESOLVED','UNRESOLVED'])
    def test_fake_extra_allocation_rejected(self):
        d,m=sample();d['upstream']['recipients'][0]['amount_raw']='999999999999999999999'
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_bad_exit_not_closed(self):
        d,m=sample();d['source_wallet_exits']['16']['transfers'][1]['amount_raw']='1'
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_fake_source_roster_link_rejected(self):
        d,m=sample();d['upstream']['recipients'][3]['source_row']=15
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_source_buy_native_spend_forged_rejected(self):
        d,m=sample();d['upstream']['buy_total_native_transaction_value_wei']='1'
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_source_buy_nonce_rejected(self):
        d,m=sample();d['upstream']['funding_buys'][0]['sender_nonce_after']=563
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_duplicate_distribution_recipient_rejected(self):
        d,m=sample();d['upstream']['recipients'][1]['address']=A
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_invented_common_controller_never_changes_basis(self):
        d,m=sample();d['claimed_common_owner']='same-person'
        self.assertEqual(audit(d,m)['recipient_rows'][0]['economic_cost_basis'],'UNRESOLVED')
    def test_changed_bought_token_balance_rejected(self):
        d,m=sample();d['upstream']['funding_buys'][1]['token_after_raw']='1'
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')
    def test_wrong_parent_token_history_rejected(self):
        d,m=sample();d['upstream']['funding_buys'][1]['token_before_raw']='1'
        self.assertEqual(audit(d,m)['status'],'PNL_UNRESOLVED')

if __name__=='__main__': unittest.main()
