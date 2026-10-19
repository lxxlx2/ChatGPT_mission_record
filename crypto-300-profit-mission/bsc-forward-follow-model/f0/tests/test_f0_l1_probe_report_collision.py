"""Real CLI collision regression against injected sender; no network/permits."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_l1_code_probe import (main, probe, AttemptJournal, QualificationClient,
                              bounded_report_path, fixture_sender, audit_offline)
from test_f0_l1_code_probe import COHORT, REGISTRY, sequence


class ReportJournalCollisionTests(unittest.TestCase):
    """Exercise real CLI live branch only with fully stubbed sender/permit.

    No real permits, sockets, Git mutation or real RPC; temporary fake files
    exist solely for injection and are deleted when each test returns.
    """
    def fake_cli(self, root: Path, report_filename: str, sender, *,
                 override_probe=None, nonce_observer=None):
        import f0_l1_code_probe as module
        manifest = root / 'F0_COHORT_PRESELECTION.json'
        registry = root / 'F0_ROUTER_SOURCE_CANDIDATES.json'
        script = root / 'f0_l1_code_probe.py'
        permit_path = root / 'permit.json'
        manifest.write_text(json.dumps(COHORT))
        registry.write_text(json.dumps(REGISTRY))
        script.write_text('fake test script, not executable')
        permit_path.write_text(json.dumps({
            'storage_root': str(root), 'max_response_bytes': 1024,
            'min_interval_ms': 100,
            'window_end_utc': '2099-01-01T00:00:00Z'}))
        nonce = nonce_observer if nonce_observer is not None else Mock()
        fake_sender = Mock(side_effect=sender)
        actual_probe = module.probe

        def quick_probe(send, cohort, registry_obj, **kwargs):
            if override_probe is not None:
                return override_probe(send, cohort, registry_obj, **kwargs)
            kwargs['sleep'] = lambda _: None
            return actual_probe(send, cohort, registry_obj, **kwargs)

        args = ['f0_l1_code_probe.py', '--execute-live',
                '--manifest', str(manifest), '--router-registry', str(registry),
                '--permit', str(permit_path), '--report', str(root / report_filename)]
        with (patch('sys.argv', args), patch.object(module, '__file__', str(script)),
              patch.object(module, 'validate_qualification_permit'),
              patch.object(module, 'git_blob_sha1', return_value=module.FROZEN_PR116_BLOB),
              patch.object(module, 'load_frozen_cohort', return_value=COHORT),
              patch.object(module, 'verify_loaded_sources'),
              patch.object(module, 'permit_audit_fields', return_value={}),
              patch.object(module, 'audit_frozen_raw',
                           side_effect=lambda raw, snap, reg: audit_offline(COHORT, snap, reg)),
              patch.object(module, 'consume_nonce', nonce),
              patch.object(module, 'https_sender', fake_sender),
              patch.object(module, 'probe', side_effect=quick_probe)):
            main()
        return nonce, fake_sender

    def test_report_named_journal_rejected_before_nonce_or_send(self):
        with tempfile.TemporaryDirectory(prefix='pr135-p1-', dir='/tmp') as d:
            root = Path(d)
            sends = []
            nonce = Mock()
            with self.assertRaisesRegex(ValueError,
                    'QUALIFICATION_REPORT_OUTSIDE_APPROVED_STORAGE'):
                self.fake_cli(root, 'journal.json',
                              lambda *a: sends.append(a), nonce_observer=nonce)
            nonce.assert_not_called()
            self.assertEqual(sends, [])
            self.assertFalse((root / 'journal.json').exists())
            self.assertFalse((root / 'report.json').exists())

    def test_report_and_journal_roles_cannot_alias(self):
        with tempfile.TemporaryDirectory(prefix='pr135-p1-', dir='/tmp') as d:
            root = Path(d)
            self.assertEqual(bounded_report_path(root/'report.json',root).name,'report.json')
            self.assertEqual(bounded_report_path(root/'journal.json',root,
                             expected_name='journal.json').name, 'journal.json')
            with self.assertRaisesRegex(ValueError,
                    'QUALIFICATION_REPORT_OUTSIDE_APPROVED_STORAGE'):
                bounded_report_path(root/'journal.json',root)
            with self.assertRaisesRegex(ValueError,
                    'QUALIFICATION_REPORT_OUTSIDE_APPROVED_STORAGE'):
                bounded_report_path(root/'report.json',root,expected_name='journal.json')

    def test_successful_real_cli_branch_retains_all_24_journal_rows(self):
        with tempfile.TemporaryDirectory(prefix='pr135-p1-', dir='/tmp') as d:
            root = Path(d)
            source = fixture_sender(sequence())
            observed_presend = []
            def sender(endpoint, payload, cap):
                ledger=json.loads((root/'journal.json').read_text())
                observed_presend.append((ledger['attempted_rpc_calls'],
                                         ledger['attempts'][-1]['state']))
                self.assertEqual(ledger['attempted_rpc_calls'], payload['id'])
                self.assertEqual(ledger['attempts'][-1]['state'],
                                 'ATTEMPTED_OUTCOME_UNKNOWN')
                return source(endpoint,payload,cap)
            nonce, fake_sender = self.fake_cli(root,'report.json',sender)
            ledger=json.loads((root/'journal.json').read_text())
            report=json.loads((root/'report.json').read_text())
            self.assertEqual(len(observed_presend),24)
            self.assertEqual(len(fake_sender.call_args_list),24)
            self.assertEqual((ledger['attempted_rpc_calls'],len(ledger['attempts'])),(24,24))
            self.assertEqual([r['index'] for r in ledger['attempts']],list(range(1,25)))
            self.assertTrue(all(r['state']=='RPC_RESPONSE' for r in ledger['attempts']))
            self.assertEqual(report['attempted_rpc_calls'],24)
            self.assertNotIn('attempts',report)
            nonce.assert_called_once()

    def test_exception_report_retains_durable_inflight_journal(self):
        with tempfile.TemporaryDirectory(prefix='pr135-p1-', dir='/tmp') as d:
            root = Path(d)
            def failing_probe(sender, cohort, reg, **kw):
                client=QualificationClient(sender, kw['journal'],1024)
                client.call('eth_chainId', [], 'SOURCE_IDENTITY')
                raise ValueError('simulated unexpected error with fake key')
            with self.assertRaises(SystemExit) as exc:
                self.fake_cli(root,'report.json',
                              lambda endpoint, payload, cap:
                                  {'jsonrpc':'2.0', 'id':payload['id'], 'result':'0x38'},
                              override_probe=failing_probe)
            self.assertEqual(exc.exception.code,1)
            ledger=json.loads((root/'journal.json').read_text())
            report=json.loads((root/'report.json').read_text())
            self.assertEqual((ledger['attempted_rpc_calls'],len(ledger['attempts'])),(1,1))
            self.assertEqual(ledger['attempts'][0]['index'],1)
            self.assertEqual(ledger['attempts'][0]['state'],'RPC_RESPONSE')
            self.assertEqual(report['stop_state'],'BLOCKED_SOURCE')
            self.assertEqual(report['attempted_rpc_calls'],1)
            self.assertNotIn('fake key',json.dumps(report))
            self.assertNotIn('attempts',report)
