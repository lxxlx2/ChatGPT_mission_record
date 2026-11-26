"""Offline state/offer tests; no real network or signing."""
import unittest
from decimal import Decimal
import cycle
G=cycle.GENESIS
W='5DRhi7dvWicmgUPfKpxdV5p4kxXiQUbLUFXtwp4EcAWLtu4D'
M='5HTMLnhawEEXBdmUc8sswUK3KhFxZ9at7VgWdcJS2oNo3RT8'
H='0x'+'a'*64
class CycleTests(unittest.TestCase):
    def test_rollover_needs_final_grant_spend_time_and_identity(self):
        g={'status':'CHAIN_FINALIZED','address':W,'key':'grant','block_number':10,'timestamp_ms':1000000}
        e={'finalized':True,'genesis':G,'wallet':W,'grant_key':'grant','block_number':12,'tx_hash':H,'spent_raw':'1'}
        self.assertFalse(cycle.claim_eligible(g,e,1000+86399))
        self.assertTrue(cycle.claim_eligible(g,e,1000+86400))
        for k,v in [('wallet',M),('grant_key','old'),('block_number',10),('spent_raw','0'),('finalized',False)]:
            self.assertFalse(cycle.claim_eligible(g,{**e,k:v},1000+86400))
        self.assertFalse(cycle.claim_eligible({**g,'status':'CLI_FINALIZED_REPORTED'},e,1000+86400))
    def test_no_unverified_venue_or_ambiguous_price_or_registry(self):
        m=[{'modelHash':H,'canonical_slug':'test/model'}]
        o={'miner':M,'modelHash':H,'venue':'https://worker.example','venueVerified':True,'expiry':200,'minEscrowFlop':'0.01'}
        f=lambda x:cycle.candidates([x],m,100,W,Decimal('10'),endpoint_ok=lambda u:bool(u))
        self.assertEqual(len(f(o)),1)
        for x in ({**o,'venueVerified':False},{**o,'expiry':110},{**o,'miner':W},{**o,'minEscrowFlop':'0.2'}):
            self.assertFalse(f(x))
        self.assertFalse(f({k:v for k,v in o.items() if k!='minEscrowFlop'}))
        self.assertFalse(cycle.candidates([o],[],100,W,Decimal('10'),endpoint_ok=lambda u:True))
    def test_scoring_never_assumed_from_runtime(self):
        self.assertEqual(cycle.score_state('Voucher earning starts at a future upgrade. No block or date is announced.',200),'UNSCORED_OR_NOT_ANNOUNCED')
        self.assertEqual(cycle.score_state('Voucher earning starts at finalized block 150',149),'WAITING_ACTIVATION_BLOCK_150')
        self.assertEqual(cycle.score_state('Voucher earning starts at finalized block 150',150),'SCORED_AT_FINALIZED_BLOCK_150')
    def test_unverified_sources_never_become_empty(self):
        with self.assertRaises(ValueError):cycle.rows({'unknown':[]})
        self.assertEqual(cycle.rows({'data':[]}),[])
if __name__=='__main__':unittest.main()
