"""Offline faucet tests: no real network calls, no actual claims."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import faucet
import runtime
import mail

ADDR='5DRhi7dvWicmgUPfKpxdV5p4kxXiQUbLUFXtwp4EcAWLtu4D'
GENESIS='0x'+'a'*64

class FaucetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.data=Path(self.temp.name)
        self.db=sqlite3.connect(self.data/'monitor.sqlite3')
        self.db.row_factory=sqlite3.Row
        runtime.ensure_state(self.db)
        mail.init(self.db)
        ident=self.data/'agent-identity.json'
        ident.write_text(json.dumps({'address':ADDR}))
        ident.chmod(0o600)
        self.patcher=patch.object(faucet,'IDENTITY',ident)
        self.patcher.start()
    def tearDown(self):
        self.patcher.stop()
        self.db.close()
        self.temp.cleanup()
    def test_no_unverified_network_faucet(self):
        called=[]
        with patch.object(faucet.shutil,'which',return_value='/bin/flop'):
            self.assertEqual(faucet.request_initial(self.db,'bad',cli_runner=lambda *a,**k:called.append(a))['status'],
                             'BLOCKED_NETWORK_GENESIS_NOT_VERIFIED')
        self.assertFalse(called)
    def test_faucet_claim_is_precommitted_once(self):
        calls=[]
        def fake_run(argv,**kwargs):
            calls.append(argv)
            self.assertEqual(argv[1:4],['--network','testnet','faucet'])
            self.assertEqual(argv[4:6],['request',ADDR])
            self.assertIn('--json',argv)
            return type('CP',(),{'returncode':0,'stdout':'{"status":"accepted"}','stderr':''})()
        with patch.object(faucet.shutil,'which',return_value='/usr/local/bin/flop'):
            first=faucet.request_initial(self.db,GENESIS,cli_runner=fake_run)
            second=faucet.request_initial(self.db,GENESIS,cli_runner=fake_run)
        self.assertEqual(first['status'],'CLI_ACCEPTED_UNVERIFIED')
        self.assertEqual(second['status'],'EXISTING_ATTEMPT_NO_AUTO_RESEND')
        self.assertEqual(len(calls),1)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM flop_mail").fetchone()[0],1)
    def test_timeout_never_auto_retries(self):
        import subprocess
        def timeout(*a,**kw):raise subprocess.TimeoutExpired('flop',100)
        with patch.object(faucet.shutil,'which',return_value='/usr/local/bin/flop'):
            first=faucet.request_initial(self.db,GENESIS,cli_runner=timeout)
            second=faucet.request_initial(self.db,GENESIS,cli_runner=timeout)
        self.assertEqual(first['status'],'OUTCOME_UNKNOWN_NO_RETRY')
        self.assertEqual(second['status'],'EXISTING_ATTEMPT_NO_AUTO_RESEND')
    def test_private_identity_is_mandatory(self):
        faucet.IDENTITY.chmod(0o644)
        with patch.object(faucet.shutil,'which',return_value='/usr/local/bin/flop'):
            self.assertEqual(faucet.request_initial(self.db,GENESIS)['status'],
                             'BLOCKED_AGENT_IDENTITY_NOT_READY')

if __name__=='__main__':
    unittest.main()
