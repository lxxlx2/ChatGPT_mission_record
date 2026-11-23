import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('agent', Path(__file__).with_name('agent.py'))
agent = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agent)

class AgentTest(unittest.TestCase):
    def test_first_run(self):
        self.assertEqual(agent.offline_first_test()['result'], 'PASS_OFFLINE')
    def test_no_network_wallet_spend_code(self):
        with tempfile.TemporaryDirectory() as t:
            conn = agent.db(Path(t) / 'ledger.sqlite3')
            self.assertEqual(agent.snapshot(conn)['execution_mode'], 'NO_SIGNING_NO_PAYMENT')
            conn.close()
    def test_unverified_receipts_not_counted(self):
        with tempfile.TemporaryDirectory() as t:
            c = agent.db(Path(t) / 'db.sqlite')
            p = Path(t) / 'receipt.json'
            p.write_text(json.dumps({'request_id':'example','wallet':'example-wallet','channel_id':'0xaabb','test_flop_spent':'0.4'}))
            self.assertEqual(agent.record_receipt(c,p)['status'],'IMPORTED_NOT_VERIFIED')
            s = agent.snapshot(c)
            self.assertEqual(s['receipt_records'],1)
            self.assertEqual(s['direct_onchain_verified_receipts'],0)
            self.assertIsNone(s['airdrop_estimate'])
            c.close()
    def test_duplicate_collect(self):
        with tempfile.TemporaryDirectory() as t:
            c=agent.db(Path(t)/'db.sqlite')
            fixture={'id':101,'name':'test','html_url':'https://github.com/flop-labs/network/releases/tag/test'}
            self.assertEqual(agent.collect(c,fetch=lambda url:[fixture] if 'releases' in url else [])['new_public_items'],1)
            self.assertEqual(agent.collect(c,fetch=lambda url:[fixture] if 'releases' in url else [])['new_public_items'],0)
            c.close()


    def test_dashboard_uses_separate_port_from_technocore(self):
        self.assertEqual(agent.DASHBOARD_HOST, '127.0.0.1')
        self.assertEqual(agent.DASHBOARD_PORT, 8766)
        self.assertNotEqual(agent.DASHBOARD_PORT, 8765)

    def test_dashboard_http_routes_ignore_tracking_query_strings(self):
        from threading import Thread
        from urllib.request import urlopen
        from urllib.error import HTTPError
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp, patch.object(agent, 'DATA', Path(tmp)):
            server = agent.ThreadingHTTPServer(('127.0.0.1', 0), agent.Handler)
            thread = Thread(target=server.serve_forever, kwargs={'poll_interval': 0.05}, daemon=True)
            thread.start()
            root = f'http://127.0.0.1:{server.server_address[1]}'
            try:
                with urlopen(root + '/', timeout=3) as response:
                    expected = response.read()
                    self.assertEqual(response.status, 200)
                with urlopen(root + '/?utm_source=chatgpt.com', timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.read(), expected)
                with urlopen(root + '/api/state?utm_source=chatgpt.com', timeout=3) as response:
                    data = json.load(response)
                    self.assertEqual(response.status, 200)
                    self.assertEqual(data['execution_mode'], 'NO_SIGNING_NO_PAYMENT')
                with urlopen(root + '/api/health?utm_source=chatgpt.com', timeout=3) as response:
                    health=json.load(response)
                    self.assertEqual(response.status,200)
                    self.assertEqual(health['service'],'flop-dashboard')
                    self.assertEqual(health['schema'],'flop-dashboard.v2')
                    self.assertEqual(health['pid'],agent.os.getpid())
                with self.assertRaises(HTTPError) as raised:
                    urlopen(root + '/unknown?utm_source=chatgpt.com', timeout=3)
                self.assertEqual(raised.exception.code, 404)
                raised.exception.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

if __name__=='__main__':
    unittest.main()
