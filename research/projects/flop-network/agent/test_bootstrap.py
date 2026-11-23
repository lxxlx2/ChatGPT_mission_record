"""No live Mac, Gmail, wallet signer or network calls. Offline bootstrap tests."""
import json
from pathlib import Path
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import bootstrap
import runtime
import mail

ADDR='5DRhi7dvWicmgUPfKpxdV5p4kxXiQUbLUFXtwp4EcAWLtu4D'

class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.patches=[
            patch.object(bootstrap,'DATA',self.root),
            patch.object(bootstrap,'PRIVATE_KEY',self.root/'agent-key.json'),
            patch.object(bootstrap,'PRIVATE_PASSWORD',self.root/'agent-password'),
            patch.object(bootstrap,'PUBLIC_ID',self.root/'agent-identity.json'),
        ]
        for p in self.patches:p.start()
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()
    def test_new_wallet_once_encrypted_local(self):
        calls=[]
        def fake_run(args,**kw):
            calls.append(args)
            if args[1]=='--version':
                return type('CP',(),{'stdout':'0.8.0\n'})()
            self.assertEqual(args[1:4],['keys','generate','--type'])
            self.assertEqual(args[4],'sr25519')
            self.assertIn('FLOP_KEY_PASSWORD',kw['env'])
            self.assertTrue(kw['env']['FLOP_KEY_PASSWORD'])
            (self.root/'agent-key.json').write_text(json.dumps({'address':ADDR,'encoded':'ENCRYPTED_FIXTURE_ONLY'}))
            return type('CP',(),{'stdout':'{"address":"'+ADDR+'"}'})()
        with patch.object(bootstrap,'run_checked',side_effect=fake_run):
            first=bootstrap.offline_identity('/fake/npm/bin/flop')
            second=bootstrap.offline_identity('/fake/npm/bin/flop')
        self.assertEqual(first['address'],ADDR)
        self.assertTrue(first['created_now'])
        self.assertFalse(second['created_now'])
        self.assertEqual(sum(1 for c in calls if 'generate' in c),1)
        self.assertEqual(bootstrap.PRIVATE_PASSWORD.stat().st_mode & 0o777,0o600)
        self.assertEqual(bootstrap.PRIVATE_KEY.stat().st_mode & 0o777,0o600)
        self.assertNotIn('FLOP_KEY_PASSWORD',bootstrap.PUBLIC_ID.read_text())
    def test_partial_wallet_refuses_regeneration(self):
        bootstrap.PRIVATE_KEY.write_text('{}')
        with patch.object(bootstrap,'run_checked',return_value=type('CP',(),{'stdout':'0.8.0\n'})()):
            with self.assertRaisesRegex(RuntimeError,'PARTIAL_EXISTING_AGENT_KEYS'):
                bootstrap.offline_identity('/fake/npm/bin/flop')
    def test_plist_points_to_fixed_source_and_nvm_cli(self):
        env={'PATH':'/Users/test/.nvm/versions/node/v24.18.0/bin:/usr/bin'}
        import plistlib
        for kind in ('tick','dashboard'):
            data=plistlib.loads(bootstrap.plist_for(kind,'/usr/bin/python3',env))
            self.assertIn('.flop-agent.',data['Label'])
            self.assertTrue(data['ProgramArguments'][1].endswith('.py'))
            self.assertTrue(data['EnvironmentVariables']['PATH'].startswith('/Users/test/.nvm'))
    def test_real_status_planned_schema(self):
        import subprocess
        observed={
          'network':'testnet','profile_status':'planned','genesis_policy':'pin-before-live',
          'rpc':{'url':'wss://testnet.flop.network','reachable':False,'matches_expected':None},
          'faucet':{'reachable':False,'ready':None,'matches_rpc':None}
        }
        cp=type('CP',(),{'returncode':0,'stdout':json.dumps(observed)})()
        with patch.object(runtime.shutil,'which',return_value='/fake/flop'),patch.object(runtime.subprocess,'run',return_value=cp):
            self.assertEqual(runtime.cli_network_status()['reason'],'OFFICIAL_PROFILE_PLANNED')
    def test_cli_live_requires_exact_genesis_finality_and_faucet(self):
        live={'network':'testnet','profile_status':'live',
              'rpc':{'reachable':True,'matches_expected':True,'genesis_hash':'0x'+'a'*64,
                     'finalized_head':123},
              'faucet':{'reachable':True,'ready':True,'matches_rpc':True}}
        def probe():
            cp=type('CP',(),{'returncode':0,'stdout':json.dumps(live)})()
            with patch.object(runtime.shutil,'which',return_value='/fake/flop'),patch.object(runtime.subprocess,'run',return_value=cp):
                return runtime.cli_network_status()
        self.assertTrue(probe()['ready'])
        live['rpc']['matches_expected']=False
        self.assertFalse(probe()['ready'])
        live['rpc']['matches_expected']=True
        live['faucet']['matches_rpc']=False
        self.assertFalse(probe()['ready'])

if __name__=='__main__':
    unittest.main()
