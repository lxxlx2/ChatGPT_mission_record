"""Offline state/offer tests; no real network or signing."""
import unittest
import sqlite3
import json
from unittest.mock import patch
from decimal import Decimal
import runtime
import mail
import faucet
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
    def test_existing_nonce_is_reconciled_without_new_claim_key(self):
        c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
        runtime.ensure_state(c);mail.init(c)
        key=faucet.base_claim_key(W)
        for k,v in {'rpc_genesis_matches_expected':'true','observed_genesis':G,'rpc_reachable':'true','profile_status':'live',
            'finalized_height':'100','wallet_address':W,'faucet_ready':'true','faucet_matches_rpc':'true',
            'faucet_lane_status':'open','faucet_claim_path':'/v1/testnet/agent-claims','faucet_rollover_requires_spend':'true',
            'faucet_signer':M,'faucet_grant_flop':'10','faucet_daily_remaining_flop':'100',
            key:json.dumps({'status':'SAME_NONCE_RECONCILIATION_PENDING','nonce':'123','address':W,'genesis':G})}.items():cycle.put(c,k,v)
        with patch.object(faucet,'request_initial',return_value={'status':'SAME_NONCE_BACKOFF'}) as req:
            self.assertEqual(cycle.run_tick(c,lambda _: 'No block or date is announced.'),'WAITING_GRANT_FINALITY')
            req.assert_called_once()
        self.assertEqual(faucet.active_claim_key(c,W),key)
        self.assertEqual(json.loads(cycle.get(c,key))['nonce'],'123')
        self.assertEqual(c.execute('SELECT COUNT(*) FROM session_attempts').fetchone()[0],0)
        c.close()

    def test_finalized_report_locates_block_without_request_resend(self):
        c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
        runtime.ensure_state(c);mail.init(c)
        key=faucet.base_claim_key(W)
        for k,v in {'rpc_genesis_matches_expected':'true','observed_genesis':G,'rpc_reachable':'true','profile_status':'live',
            'finalized_height':'100','wallet_address':W,'faucet_ready':'true','faucet_matches_rpc':'true',
            'faucet_lane_status':'open','faucet_claim_path':'/v1/testnet/agent-claims','faucet_rollover_requires_spend':'true',
            'faucet_signer':M,'faucet_grant_flop':'10','faucet_daily_remaining_flop':'100',
            key:json.dumps({'status':'CLI_FINALIZED_REPORTED','nonce':'123','address':W,'genesis':G,'at':'2026-11-26T01:15:59+00:00','tx_hash':H,'faucet_signer':M,'reason':'FAUCET_REFUSED'})}.items():cycle.put(c,k,v)
        def verify(kind,data):
            if kind=='locate_grant':return {'ok':True,'genesis':G,'found':True,'block_number':42,'block_hash':'0x'+'b'*64}
            self.assertEqual(kind,'grant');self.assertEqual(data['block_number'],42)
            return {'ok':True,'finalized':True,'genesis':G,'wallet':W,'signer':M,'amount_raw':str(10*cycle.UNIT),'tx_hash':H,'block_number':42,'timestamp_ms':1795655759000}
        with patch.object(faucet,'request_initial') as req:
            self.assertEqual(cycle.run_tick(c,lambda _: 'No block or date is announced.',verifier=verify),'GRANT_FINALIZED_READY_FOR_DISCOVERY')
            req.assert_not_called()
        grant=json.loads(cycle.get(c,key))
        self.assertEqual(grant['status'],'CHAIN_FINALIZED')
        self.assertEqual(grant['previous_reason'],'FAUCET_REFUSED')
        c.close()

    def test_manual_import_is_pending_idempotent_and_no_duplicate(self):
        c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
        runtime.ensure_state(c);mail.init(c)
        key=faucet.base_claim_key(W)
        cycle.put(c,key,json.dumps({'status':'CHAIN_FINALIZED','address':W,'genesis':G,'block_number':10,'timestamp_ms':1000000}))
        rec={'miner':M,'channel':'0x'+'b'*64,'settle_tx':H,'cooperative':True,'verified_turns':1}
        args=(c,W,rec,12,'https://worker.example','test/model','0.005')
        self.assertEqual(cycle.stage_manual(*args),'WAITING_FOR_FINALIZED_SETTLEMENT')
        self.assertEqual(cycle.stage_manual(*args),'ALREADY_STAGED')
        row=c.execute('SELECT * FROM session_attempts').fetchone()
        self.assertEqual(row['chain_verified'],0)
        self.assertEqual(json.loads(row['cli_result'])['tx_hash'],H)
        self.assertEqual(cycle.known_direct(c,W,Decimal('10')),[])
        with self.assertRaises(ValueError):
            cycle.stage_manual(c,W,{**rec,'settle_tx':'0x'+'c'*64},12,'https://worker.example','test/model','0.005')
        c.close()

    def test_unverified_sources_never_become_empty(self):
        with self.assertRaises(ValueError):cycle.rows({'unknown':[]})
        self.assertEqual(cycle.rows({'data':[]}),[])
if __name__=='__main__':unittest.main()
