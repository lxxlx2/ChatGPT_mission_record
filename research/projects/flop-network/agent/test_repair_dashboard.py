"""Offline regression tests: stale FLOP 8765 listener is identified safely.

No real launchctl, lsof, signal, mail, wallet, RPC or network calls.
"""
import json
from pathlib import Path
import plistlib
import tempfile
import unittest
from unittest.mock import patch,call

import repair_dashboard as repair


class RepairDashboardTests(unittest.TestCase):
    def test_listener_identity_from_old_temp_checkout(self):
        fake=type('CP',(),{'returncode':0,'stdout':
          '501 /opt/homebrew/bin/python3 /private/var/folders/test/T/flop-agent.OLD/mission/research/projects/flop-network/agent/agent.py dashboard\n'})()
        with patch.object(repair,'UID',501), patch.object(repair,'command',return_value=fake):
            info=repair.listener_info(321)
        self.assertTrue(info['ours'])
        self.assertEqual(info['pid'],321)

    def test_unknown_server_same_port_never_killed_or_restart(self):
        info={'pid':667,'exists':True,'ours':False,'command':'/usr/bin/python3 -m http.server 8765'}
        with patch.object(repair,'stable_root'),patch.object(repair,'git_sha',return_value='a'*40),\
             patch.object(repair,'active_plist'),patch.object(repair,'healthy',return_value=False),\
             patch.object(repair,'listener_pids',return_value=[667]),\
             patch.object(repair,'listener_info',return_value=info),\
             patch.object(repair,'local_get',return_value={'status':404,'json':None}),\
             patch.object(repair,'restart_managed') as restart,\
             patch.object(repair.os,'kill') as kill:
            result=repair.run(apply=True)
        self.assertEqual(result['status'],'BLOCKED_UNRECOGNIZED_8765_OWNER')
        restart.assert_not_called()
        kill.assert_not_called()

    def test_stale_flo_dashboard_replaced_with_existing_launchd_only(self):
        old={'pid':452,'exists':True,'ours':True,
             'command':'python /private/var/folders/T/flop-agent.OLD/mission/research/projects/flop-network/agent/agent.py dashboard'}
        with patch.object(repair,'stable_root'),patch.object(repair,'git_sha',return_value='a'*40),\
             patch.object(repair,'active_plist'),patch.object(repair,'healthy',return_value=False),\
             patch.object(repair,'listener_pids',side_effect=[[452],[452],[]]),\
             patch.object(repair,'listener_info',return_value=old),\
             patch.object(repair,'local_get',return_value={'status':404,'json':None}),\
             patch.object(repair,'restart_managed',return_value={'ok':True,'exit':0}) as restart,\
             patch.object(repair,'await_health',side_effect=[False,True]),\
             patch.object(repair.os,'kill') as kill:
            result=repair.run(apply=True)
        self.assertEqual(result['status'],'REPAIRED_VERIFIED')
        restart.assert_called()
        self.assertEqual(restart.call_count,2)
        kill.assert_called_once_with(452,repair.signal.SIGTERM)

    def test_healthy_route_no_process_termination(self):
        with patch.object(repair,'stable_root'),patch.object(repair,'git_sha',return_value='a'*40),\
             patch.object(repair,'active_plist'),patch.object(repair,'healthy',return_value=True),\
             patch.object(repair,'local_get',return_value={'status':200,'json':None}),\
             patch.object(repair,'listener_pids') as pids,patch.object(repair.os,'kill') as kill:
            result=repair.run(apply=True)
        self.assertEqual(result['status'],'ALREADY_HEALTHY')
        pids.assert_not_called()
        kill.assert_not_called()

    def test_active_plist_must_point_at_repo_dashboard_only(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'dashboard.plist'
            props={'Label':'com.501.flop-agent.dashboard',
                   'ProgramArguments':['python3','/wrong/project/agent.py','dashboard']}
            file.write_bytes(plistlib.dumps(props))
            with patch.object(repair,'PLIST',file),patch.object(repair,'UID',501),\
                 patch.object(repair,'LABEL','com.501.flop-agent.dashboard'):
                with self.assertRaisesRegex(RuntimeError,'WRONG_SCRIPT'):
                    repair.active_plist()

    def test_http_health_schema_and_exact_sha_are_required(self):
        sha='a'*40
        health={'status':200,'json':{'service':'flop-dashboard',
                                    'schema':'flop-dashboard.v2',
                                    'pid':123,'source_path':str(repair.ROOT.resolve()),
                                    'git_head_sha':sha}}
        with patch.object(repair,'local_get',side_effect=[health,{'status':200,'json':None}]):
            self.assertTrue(repair.healthy(sha))
        health['json']['git_head_sha']='b'*40
        with patch.object(repair,'local_get',side_effect=[health,{'status':200,'json':None}]):
            self.assertFalse(repair.healthy(sha))


if __name__=='__main__':
    unittest.main()
