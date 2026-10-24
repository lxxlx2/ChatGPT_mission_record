"""Positive official bStocks scope overlay regression without REST or trades."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

import monster_v4_stage166_spot511_official_1m_intake as stage166
from mission_agent.early.spot_asset_scope import classify_spot_replay, ScopeEvidenceError

MANIFEST = (Path(__file__).resolve().parents[2] / 'monster/evidence' /
            'MONSTER_SPOT511_OFFICIAL_POSITIVE_BSTOCKS_20261024.json')


class AssetScopeTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text())
        self.roster = stage166.frozen_roster()
        assert len(self.roster) == 511
        def event(sym,kind,serial):
            return {'event_id':f'{serial:064x}','symbol':sym,'venue':'spot',
                    'event_type':kind,'observed_ms':1792500000000 + serial*180000,
                    'details':{'setup_candidate':True}}
        self.watch=[event('SHAZBUSDT','WATCH_EARLY',1),
                    event('BMTUSDT','WATCH_EARLY',2),
                    event('MRNABUSDT','WATCH_EARLY',3)]
        self.setups=[event('SHAZBUSDT','SETUP_ACTIVE',4),
                     event('BMTUSDT','SETUP_ACTIVE',5)]
        self.replay={'frozen_roster':511,'mode':'OFFLINE_HISTORICAL_RESEARCH',
                     'same_d0_watch_id_and_time':True,'d0_watch_count':3,
                     'fifo_setups':2,'G6':'NO_GO',
                     'fifo_watch_events':self.watch,
                     'fair8_watch_events':deepcopy(self.watch),
                     'fifo_setup_events':self.setups}

    def test_positive_official_identity_exclusion(self):
        out=classify_spot_replay(self.replay,self.manifest,self.roster)
        self.assertEqual(out['known_bstock_symbols_in_frozen_roster'],79)
        self.assertEqual(out['watch']['raw'],3)
        self.assertEqual(out['watch']['verified_tokenized_security'],2)
        self.assertEqual(out['setup']['raw'],2)
        self.assertEqual(out['setup']['verified_tokenized_security'],1)
        self.assertEqual(out['setup']['identity_unresolved'],1)
        self.assertIsNone(out['eligible_crypto_only_setup_denominator'])
        self.assertFalse(out['all_unmatched_assets_certified_crypto'])
        self.assertEqual(out['G6'],'NO_GO')

    def test_original_event_inputs_preserved(self):
        before=deepcopy(self.replay)
        classify_spot_replay(self.replay,self.manifest,self.roster)
        self.assertEqual(self.replay,before)

    def test_suffix_not_inferred(self):
        official={s for item in self.manifest['announcements'] for s in item['positive_bstock_symbols']}
        self.assertIn('BMTUSDT',self.roster)
        self.assertNotIn('BMTUSDT',official)

    def test_future_announcement_cannot_backdate_securities(self):
        m=deepcopy(self.manifest)
        m['announcements'][2]['published_utc']='2026-10-30T00:00:00Z'
        result=classify_spot_replay(self.replay,m,self.roster)
        self.assertEqual(result['setup']['verified_tokenized_security'],0)

    def test_duplicate_positive_rejected(self):
        m=deepcopy(self.manifest)
        m['announcements'][0]['positive_bstock_symbols'].append('IBMBUSDT')
        with self.assertRaises(ScopeEvidenceError):classify_spot_replay(self.replay,m,self.roster)

    def test_fake_official_symbol_rejected(self):
        m=deepcopy(self.manifest)
        m['announcements'][0]['positive_bstock_symbols'][0]='FAKETICKERUSDT'
        with self.assertRaises(ScopeEvidenceError):classify_spot_replay(self.replay,m,self.roster)

    def test_malicious_source_domain_rejected(self):
        m=deepcopy(self.manifest)
        m['announcements'][0]['url']='https://www.binance.com.evil.example/official'
        with self.assertRaises(ScopeEvidenceError):classify_spot_replay(self.replay,m,self.roster)

    def test_source_count_invalid_rejected(self):
        m=deepcopy(self.manifest);m['expected_positive_count']=999
        with self.assertRaises(ScopeEvidenceError):classify_spot_replay(self.replay,m,self.roster)

    def test_duplicate_event_rejected(self):
        r=deepcopy(self.replay)
        r['fifo_watch_events'][1]['event_id']=r['fifo_watch_events'][0]['event_id']
        with self.assertRaises(ScopeEvidenceError):classify_spot_replay(r,self.manifest,self.roster)

    def test_nonoriginal_d0_identity_rejected(self):
        r=deepcopy(self.replay);r['fair8_watch_events'][0]['symbol']='WRONGUSDT'
        with self.assertRaises(ScopeEvidenceError):classify_spot_replay(r,self.manifest,self.roster)

    def test_511_roster_identity_required(self):
        with self.assertRaises(ScopeEvidenceError):classify_spot_replay(self.replay,self.manifest,self.roster[:-1])

    def test_setup_count_drift_rejected(self):
        r=deepcopy(self.replay);r['fifo_setups']+=1
        with self.assertRaises(ScopeEvidenceError):classify_spot_replay(r,self.manifest,self.roster)


if __name__=='__main__':unittest.main()
