"""Directory durability gates, exclusively local files and injected senders."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import f0_l1_code_probe as storage
import f0_l1_durable_journal as transport_free_storage
from f0_l1_live_short import Journal
from datetime import datetime, timedelta, timezone

class DirectoryDurabilityTests(unittest.TestCase):
    def test_atomic_replace_syncs_directory_after_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'journal.json'
            events = []
            replace = storage.os.replace
            with patch.object(storage.os, 'replace', side_effect=lambda a,b:(events.append('replace'),replace(a,b))[-1]), patch.object(storage, 'fsync_directory', side_effect=lambda path:events.append(('directory',path))):
                storage.atomic_json(target, {'attempts': [1]})
            self.assertEqual(events, ['replace', ('directory', target.parent)])
            self.assertEqual(json.loads(target.read_text())['attempts'], [1])

    def test_failed_directory_sync_prevents_sender(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = datetime.now(timezone.utc)
            journal = Journal(root/'journal.json', limit=62, clock=lambda:now,
                              mono=lambda:0.0, sleep=lambda _:None, interval_ms=250,
                              deadline=now+timedelta(minutes=1), raw_dir=root/'raw_responses')
            post = Mock()
            with patch.object(transport_free_storage, 'fsync_directory', side_effect=OSError('simulated sync failure')):
                with self.assertRaises(OSError):
                    journal.request('eth_chainId', [], 'CHAIN_ID', post)
            post.assert_not_called()
            self.assertEqual(json.loads((root/'journal.json').read_text())['attempts'][0]['state'], 'ATTEMPTED_OUTCOME_UNKNOWN')

    def test_directory_sync_supported_on_this_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage.fsync_directory(Path(tmp))

class HttpErrorArchiveTests(unittest.TestCase):
    def test_http_503_body_archived_and_counted_without_retry(self):
        import io
        import urllib.error
        import f0_l1_live_short as live
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = datetime.now(timezone.utc)
            journal = Journal(root/'journal.json', limit=62, clock=lambda:now,
                              mono=lambda:0.0, sleep=lambda _:None, interval_ms=250,
                              deadline=now+timedelta(minutes=1), raw_dir=root/'raw_responses')
            body = b'{"error":"simulated service unavailable"}'
            error = urllib.error.HTTPError(live.ENDPOINT, 503, 'Unavailable',
                                          {'Content-Type':'application/json'}, io.BytesIO(body))
            opener = Mock()
            opener.open.side_effect = error
            with patch.object(live.urllib.request, 'build_opener', return_value=opener):
                response, failure, item = journal.request('eth_chainId', [], 'CHAIN_ID', live.live_https_post)
            self.assertIsNone(response)
            self.assertEqual(failure, 'INVALID_HTTP_OR_RPC_RESPONSE')
            self.assertEqual(opener.open.call_count, 1)
            self.assertEqual((root/'raw_responses'/item['local_raw_response_file']).read_bytes(), body)
            self.assertEqual(item['response_sha256'], live.sha(body))
            self.assertEqual(item['state'], 'FAILED')

class PostPersistenceDeadlineTests(unittest.TestCase):
    def test_expiry_during_persistence_never_calls_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = [datetime.now(timezone.utc)]
            journal = Journal(root/'journal.json', limit=62, clock=lambda:now[0],
                              mono=lambda:0.0, sleep=lambda _:None, interval_ms=250,
                              deadline=now[0]+timedelta(seconds=1), raw_dir=root/'raw_responses')
            persist = journal.persist
            def slow_persist():
                persist()
                now[0] += timedelta(seconds=2)
            post = Mock()
            with patch.object(journal, 'persist', side_effect=slow_persist):
                with self.assertRaisesRegex(ValueError, 'CAPTURE_DEADLINE_EXPIRED'):
                    journal.request('eth_chainId', [], 'CHAIN_ID', post)
            post.assert_not_called()
            self.assertEqual(json.loads((root/'journal.json').read_text())['attempts'][0]['state'], 'ATTEMPTED_OUTCOME_UNKNOWN')
