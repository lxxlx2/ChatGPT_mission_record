"""Directory durability gates, exclusively local files and injected senders."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import f0_l1_code_probe as storage
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
            with patch.object(storage, 'fsync_directory', side_effect=OSError('simulated sync failure')):
                with self.assertRaises(OSError):
                    journal.request('eth_chainId', [], 'CHAIN_ID', post)
            post.assert_not_called()
            self.assertEqual(json.loads((root/'journal.json').read_text())['attempts'][0]['state'], 'ATTEMPTED_OUTCOME_UNKNOWN')

    def test_directory_sync_supported_on_this_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage.fsync_directory(Path(tmp))
