"""Offline D10 tests; no signing, networking, real claims or emails."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import subprocess
import faucet
import runtime
import mail

ADDR='5DRhi7dvWicmgUPfKpxdV5p4kxXiQUbLUFXtwp4EcAWLtu4D'
class FaucetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.db=sqlite3.connect(root/'monitor.sqlite3')
        self.db.row_factory=sqlite3.Row
        runtime.ensure_state(self.db)
        mail.init(self.db)
        self.ident=root/'agent-identity.json'
        for p,body in ((self.ident,json.dumps({'address':ADDR,'purpose':'FLOP_TESTNET_ONLY'})),
                       (root/'agent-key.json',json.dumps({'address':ADDR})),
                       (root/'agent-password','synthetic-test-only')):
            p.write_text(body)
            p.chmod(0o600)
        self.p=patch.object(faucet,'IDENTITY',self.ident)
        self.p.start()
        self.q=patch.object(faucet.shutil,'which',return_value='/fake/flop')
        self.q.start()
        self.calls=[]
        self.t=1000000
    def tearDown(self):
        self.q.stop()
        self.p.stop()
        self.db.close()
        self.temp.cleanup()
    def call(self,argv,**kw):
        if argv[-1]=='--version':
            return SimpleNamespace(returncode=0,stdout='0.9.0',stderr='')
        self.calls.append(argv)
        self.assertIn('--keystore',argv)
        self.assertNotIn(ADDR,argv)
        self.assertEqual(kw['env']['FLOP_KEY_PASSWORD'],'synthetic-test-only')
        self.assertIn('--nonce',argv)
        if len(self.calls)==1:
            raise subprocess.TimeoutExpired('flop',150)
        return SimpleNamespace(returncode=0,stdout=json.dumps({'finalized':True,'tx_hash':'0x'+'a'*64}),stderr='')
    def req(self,genesis=faucet.GENESIS):
        return faucet.request_initial(self.db,genesis,cli_runner=self.call,clock=lambda:self.t)
    def test_invalid_genesis_no_sign(self):
        self.assertEqual(self.req('0x'+'b'*64)['status'],'BLOCKED_NETWORK_GENESIS_NOT_VERIFIED')
        self.assertFalse(self.calls)
    def test_same_nonce_after_timeout_then_stop(self):
        self.assertEqual(self.req()['status'],'SAME_NONCE_RECONCILIATION_PENDING')
        self.assertEqual(self.req()['status'],'SAME_NONCE_BACKOFF')
        self.t+=901
        self.assertEqual(self.req()['status'],'CLI_FINALIZED_REPORTED')
        self.assertEqual(self.calls[0][-1],self.calls[1][-1])
        self.t+=86401
        self.assertEqual(self.req()['status'],'CLI_FINALIZED_REPORTED')
        self.assertEqual(len(self.calls),2)
    def test_no_regenerate(self):
        self.ident.chmod(0o644)
        self.assertEqual(self.req()['status'],'BLOCKED_AGENT_IDENTITY_NOT_READY')
        self.assertFalse(self.calls)
    def test_funding_observation_distinguishes_balance_and_grant(self):
        self.req()
        def read(url):
            if url.endswith('/chain'):
                return json.dumps({'network':'testnet','genesisHash':faucet.GENESIS})
            return json.dumps({'network':'testnet','stale':False,'asOf':'2026-11-26T01:00:00Z','faucet':{'balanceFlop':'100','pendingGrants':3,'dailyCap':{'remainingFlop':'50'},'agent':{'grantFlop':10}}})
        def bal(argv,**kw):
            return SimpleNamespace(returncode=0,stdout=json.dumps({'address':ADDR,'free':'10000000000000000000','reserved':'0'}))
        faucet.funding_observation(self.db,fetch=read,cli_status={'observed_genesis':faucet.GENESIS,'rpc_genesis_matches_expected':True},runner=bal)
        self.assertEqual(runtime.get(self.db,'wallet_free_flop'),'10')
        self.assertEqual(runtime.get(self.db,'faucet_daily_remaining_flop'),'50')
        self.assertEqual(runtime.get(self.db,'faucet_claim_status'),'SAME_NONCE_RECONCILIATION_PENDING')
        self.assertEqual(runtime.get(self.db,'faucet_claim_tx'),'UNVERIFIED')
        self.assertEqual(runtime.get(self.db,'wallet_funding_state'),'POSITIVE_BALANCE_OBSERVED')
        faucet.funding_observation(self.db,fetch=read,cli_status={'observed_genesis':faucet.GENESIS,'rpc_genesis_matches_expected':True},runner=bal)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM flop_mail WHERE mail_key LIKE 'first-funded-wallet-%'").fetchone()[0],1)
    def test_runtime_incompatible_reads_finalized_balance_without_signing(self):
        def read(url):
            if url.endswith('/chain'):
                return json.dumps({'network':'testnet','genesisHash':faucet.GENESIS})
            return json.dumps({'network':'testnet','stale':False,'faucet':{'agent':{'grantFlop':10}}})
        def bal(argv,**kw):
            return SimpleNamespace(returncode=1,stdout='',stderr='RUNTIME_INCOMPATIBLE')
        def chain(kind,params):
            self.assertEqual(kind,'balance')
            self.assertEqual(params,{'wallet':ADDR})
            return {'ok':True,'finalized':True,'genesis':faucet.GENESIS,'address':ADDR,'height':42,'free':'10000000000000000000','reserved':'0'}
        faucet.funding_observation(self.db,fetch=read,cli_status={'observed_genesis':faucet.GENESIS,'rpc_genesis_matches_expected':True},runner=bal,chain_reader=chain)
        self.assertEqual(runtime.get(self.db,'wallet_free_flop'),'10')
        self.assertEqual(runtime.get(self.db,'wallet_balance_source'),'FINALIZED_RPC')
        self.assertEqual(runtime.get(self.db,'wallet_balance_error'),'RUNTIME_INCOMPATIBLE')

    def test_current_official_format(self):
        doc='FLOP Testnet went live on 24 November 2026. This opening is unscored. Genesis block hash '+faucet.GENESIS
        r=runtime.official_testnet_state(lambda _:doc)
        self.assertTrue(r['ready'])
        self.assertEqual(r['genesis'],faucet.GENESIS)
        self.assertEqual(r['scoring_status'],'UNSCORED')

if __name__=='__main__':
    unittest.main()