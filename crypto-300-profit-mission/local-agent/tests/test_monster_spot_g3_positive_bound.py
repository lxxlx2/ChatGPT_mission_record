"""True 46-event original-core overlay and corruption tests; no HTTP or orders."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from mission_agent.early.spot_g3_positive_bound import (
    g3_positive_identity_bound, PositiveBoundError)


EVIDENCE = Path(__file__).resolve().parents[2] / 'monster' / 'evidence'


class PositiveBoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.replay = json.loads((EVIDENCE /
            'MONSTER_SPOT511_4088_REAL_GLOBAL_FIFO8_FAIR8_46_SETUP_EVENTS_20261024.json').read_text())
        cls.crypto = json.loads((EVIDENCE /
            'MONSTER_SPOT511_PRE_EVENT_OFFICIAL_POSITIVE_CRYPTO_26_ASSETS_20261024.json').read_text())
        cls.securities = json.loads((EVIDENCE /
            'MONSTER_SPOT511_OFFICIAL_POSITIVE_BSTOCKS_20261024.json').read_text())

    def audit(self, replay=None, crypto=None, securities=None):
        return g3_positive_identity_bound(
            self.replay if replay is None else replay,
            self.crypto if crypto is None else crypto,
            self.securities if securities is None else securities)

    def test_actual_46_setup_positive_partition(self):
        out=self.audit()
        self.assertEqual(out['raw_setup_events_preserved'],46)
        self.assertEqual(out['positively_source_crypto_identity_count'],37)
        self.assertEqual(out['positively_source_crypto_symbols'],26)
        self.assertEqual(out['positively_source_security_excluded_events'],2)
        self.assertEqual(out['unresolved_identity_events'],7)
        self.assertEqual(out['G3_frozen_seven_day_attention_max'],35)
        self.assertTrue(out['overloaded_even_if_last_source_day_zero_if_all_positive_crypto_eligible'])
        self.assertEqual(out['formal_G6'],'NO_GO')
        self.assertEqual(out['formal_G3'],'NOT_PASSED_PENDING_ELIGIBILITY_AND_FULL_SOURCE')
        self.assertEqual(out['positive_crypto_daily_utc'],
                         {'2026-10-18':6,'2026-10-19':5,'2026-10-20':7,
                          '2026-10-21':8,'2026-10-22':7,'2026-10-23':4})

    def test_inputs_not_modified(self):
        a=deepcopy(self.replay);b=deepcopy(self.crypto);c=deepcopy(self.securities)
        self.audit()
        self.assertEqual(a,self.replay)
        self.assertEqual(b,self.crypto)
        self.assertEqual(c,self.securities)

    def test_exact_original_replay_sha_cannot_be_replaced(self):
        a=deepcopy(self.replay);a['replay_inner_json_sha256']='1'*64
        with self.assertRaises(PositiveBoundError):self.audit(replay=a)

    def test_original_setup_event_count_drift_rejected(self):
        a=deepcopy(self.replay);a['complete_46_original_core_setups'].pop()
        with self.assertRaises(PositiveBoundError):self.audit(replay=a)

    def test_duplicate_actual_event_id_rejected(self):
        a=deepcopy(self.replay)
        a['complete_46_original_core_setups'][1]['event_id']=a['complete_46_original_core_setups'][0]['event_id']
        with self.assertRaises(PositiveBoundError):self.audit(replay=a)

    def test_no_future_source_date_credit(self):
        m=deepcopy(self.crypto);m['rows'][0]['published_utc_date']='2026-10-18'
        with self.assertRaisesRegex(PositiveBoundError,'SOURCE_NOT_PRE_WINDOW_DAY'):
            self.audit(crypto=m)

    def test_no_undated_source_credit(self):
        m=deepcopy(self.crypto);m['rows'][0]['published_utc_date']='unverified'
        with self.assertRaises(PositiveBoundError):self.audit(crypto=m)

    def test_no_unapproved_source_host(self):
        m=deepcopy(self.crypto);m['rows'][0]['source_url']='https://www.binance.com.bad.test/en/support/foo'
        with self.assertRaises(PositiveBoundError):self.audit(crypto=m)

    def test_no_duplicate_positive_symbols(self):
        m=deepcopy(self.crypto);m['rows'].append(deepcopy(m['rows'][0]))
        with self.assertRaises(PositiveBoundError):self.audit(crypto=m)

    def test_security_overlap_cannot_be_crypto(self):
        m=deepcopy(self.crypto);m['rows'][0]['symbol']='SHAZBUSDT'
        with self.assertRaises(PositiveBoundError):self.audit(crypto=m)

    def test_time_outside_frozen_window_rejected(self):
        a=deepcopy(self.replay);a['complete_46_original_core_setups'][0]['observed_ms']=1793000000000
        with self.assertRaises(PositiveBoundError):self.audit(replay=a)

    def test_d0_d1_immutable_replay_must_have_original_id_equality(self):
        a=deepcopy(self.replay)
        a['replay_results']['fifo_fair_setup_id_and_time_equal']=False
        with self.assertRaises(PositiveBoundError):self.audit(replay=a)


if __name__=='__main__':
    unittest.main()
