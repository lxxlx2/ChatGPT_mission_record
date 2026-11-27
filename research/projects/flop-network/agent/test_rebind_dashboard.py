"""Offline tests for one existing FLOP dashboard label, never real launchctl."""
import json
from pathlib import Path
import plistlib
import socket
import tempfile
import unittest
from unittest.mock import patch

import rebind_dashboard as rebind

SHA='a'*40

class PortMigrationTests(unittest.TestCase):
    def test_choose_port_skips_busy_port_without_killing(self):
        with socket.socket() as busy:
            busy.bind(('127.0.0.1',0))
            occupied=busy.getsockname()[1]
            with socket.socket() as spare:
                spare.bind(('127.0.0.1',0))
                free=spare.getsockname()[1]
            self.assertEqual(rebind.choose_port([occupied,free]),free)
    def test_health_rejects_404_even_if_port_open(self):
        with patch.object(rebind,'get_http',side_effect=[
            {'status':404,'body':b''},{'status':200,'body':b'<html/>'}]):
            self.assertFalse(rebind.live_probe(18766,SHA)['verified'])
    def test_health_rejects_wrong_build_and_accepts_identified_process(self):
        body={'service':'flop-dashboard','build':'other','schema':'flop-dashboard.v2',
              'source_path':str(rebind.ROOT.resolve()),
              'git_head_sha':SHA,'pid':77777,'host':'127.0.0.1','port':18766}
        def check():
            with patch.object(rebind,'get_http',side_effect=[
                {'status':200,'body':json.dumps(body).encode()},
                {'status':200,'body':b'<html>FLOP</html>'}]):
                return rebind.live_probe(18766,SHA)
        self.assertFalse(check()['verified'])
        body['build']=rebind.BUILD
        self.assertTrue(check()['verified'])
        body['port']=8766
        self.assertFalse(check()['verified'])
    def test_original_launch_agent_is_preserved_when_port_is_migrated(self):
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp)
            root=(home/'Library/Application Support/FLOPAgent/mission/research/projects/flop-network/agent')
            root.mkdir(parents=True)
            data=home/'flop-data'
            plist=home/'dashboard.plist'
            prior={
                'Label':'com.501.flop-agent.dashboard',
                'WorkingDirectory':str(root),
                'ProgramArguments':['/usr/bin/python3',str(root/'agent.py'),'dashboard'],
                'EnvironmentVariables':{'FLOP_AGENT_DATA_DIR':str(data)},
                'KeepAlive':True,'RunAtLoad':True
            }
            plist.write_bytes(plistlib.dumps(prior))
            ok={'verified':True,'port':18766,'pid':1234}
            class CP: returncode=0
            with patch.object(rebind.Path,'home',return_value=home), \
                patch.object(rebind,'ROOT',root),patch.object(rebind,'DATA',data),\
                patch.object(rebind,'PLIST',plist),patch.object(rebind,'LABEL',prior['Label']),\
                patch.object(rebind,'head_sha',return_value=SHA),\
                patch.object(rebind,'choose_port',return_value=18766),\
                patch.object(rebind,'command_status',return_value={'loaded':True}),\
                patch.object(rebind,'launchctl_bootout',return_value=CP()) as bootout,\
                patch.object(rebind,'launchctl_bootstrap',return_value=CP()) as bootstrap,\
                patch.object(rebind,'wait_health',return_value=ok):
                with patch.object(rebind.sys,'platform','darwin'):
                    result=rebind.migrate(apply=True)
            self.assertEqual(result['status'],'LIVE_HTTP_VERIFIED')
            self.assertEqual(plistlib.loads(plist.read_bytes())['EnvironmentVariables']['FLOP_DASHBOARD_PORT'],'18766')
            self.assertEqual(plistlib.loads(plist.read_bytes())['Label'],prior['Label'])
            self.assertEqual(plistlib.loads(plist.read_bytes())['ProgramArguments'],prior['ProgramArguments'])
            self.assertEqual(bootout.call_count,1)
            self.assertEqual(bootstrap.call_count,1)
            self.assertEqual(json.loads((data/'dashboard-bind.json').read_text())['port'],18766)
            self.assertTrue((data/'dashboard-port-migration-backup.plist').exists())
    def test_existing_plist_accepts_path_alias_but_rejects_other_script(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'actual'
            root.mkdir()
            alias=Path(temp)/'alias'
            alias.symlink_to(root,target_is_directory=True)
            file=Path(temp)/'dashboard.plist'
            props={'Label':rebind.LABEL,
                   'ProgramArguments':['python3',str(root/'agent.py'),'dashboard'],
                   'WorkingDirectory':str(root),
                   'EnvironmentVariables':{}}
            file.write_bytes(plistlib.dumps(props))
            with patch.object(rebind,'ROOT',alias),patch.object(rebind,'PLIST',file):
                self.assertEqual(rebind.existing_plist(),props)
                props['ProgramArguments'][1]=str(root/'unrelated.py')
                file.write_bytes(plistlib.dumps(props))
                with self.assertRaisesRegex(RuntimeError,'EXISTING_JOB_NOT_FLOP_DASHBOARD'):
                    rebind.existing_plist()

    def test_existing_verified_dashboard_no_restarts(self):
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp)
            root=(home/'Library/Application Support/FLOPAgent/mission/research/projects/flop-network/agent')
            root.mkdir(parents=True)
            existing={'EnvironmentVariables':{'FLOP_DASHBOARD_PORT':'18766'}}
            with patch.object(rebind.Path,'home',return_value=home),\
                patch.object(rebind,'ROOT',root),patch.object(rebind,'head_sha',return_value=SHA),\
                patch.object(rebind,'existing_plist',return_value=existing),\
                patch.object(rebind,'live_probe',return_value={'verified':True}),\
                patch.object(rebind,'choose_port') as choose:
                with patch.object(rebind.sys,'platform','darwin'):
                    result=rebind.migrate(apply=True)
            self.assertEqual(result['status'],'ALREADY_VERIFIED')
            choose.assert_not_called()
    def test_old_8766_owner_never_inspected_or_killed(self):
        content=Path(rebind.__file__).read_text()
        self.assertNotIn('os.kill(',content)
        self.assertNotIn('SIGTERM',content)
        self.assertIn('PORTS=range(18766,18796)',content)

if __name__=='__main__':
    unittest.main()
