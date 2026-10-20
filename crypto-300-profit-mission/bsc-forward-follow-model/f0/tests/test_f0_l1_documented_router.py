"""Saved full-block L1 integration with real frozen PR116 addresses, no HTTP."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_l1_window import (offline_window, load_frozen_cohort,
                          FROZEN_ROUTER_REGISTRY_BLOB, git_blob_sha1,
                          DOCUMENTED_ROUTER_MODE)

FAKE = json.loads((ROOT / 'fixtures/l1_fake_cohort.json').read_text())
FIX = json.loads((ROOT / 'fixtures/l1_contiguous_replay.json').read_text())
ROUTER_RAW = (ROOT / 'F0_ROUTER_SOURCE_CANDIDATES.json').read_bytes()
REAL_FILE = ROOT / 'F0_COHORT_PRESELECTION.json'


def bind_real_fixture(real):
    fixture = copy.deepcopy(FIX)
    fixture['cohort_source_kind'] = 'FROZEN_PR116_GIT_BLOB'
    fixture['router_allowlist_kind'] = DOCUMENTED_ROUTER_MODE
    fixture.pop('synthetic_routers')
    prim = [row['wallet'] for row in real['preliminary_wallets'] if row['role'] == 'PRIMARY']
    source_a = FAKE['preliminary_wallets'][0]['wallet']
    source_b = FAKE['preliminary_wallets'][15]['wallet']
    real_router = json.loads(ROUTER_RAW)['routers'][0]['address']
    for attempt in fixture['block_attempts']:
        for tx in (attempt.get('rpc') or {}).get('result', {}).get('transactions', []):
            if tx['from'].lower() == source_a.lower():
                tx['from'] = prim[0]
            if tx['from'].lower() == source_b.lower():
                tx['from'] = prim[10]
            if tx['to'] == FIX['synthetic_routers'][0]:
                tx['to'] = real_router
    return fixture


class DocumentedRouterSavedWindow(unittest.TestCase):
    def test_registry_blob_is_frozen_to_approved_source(self):
        self.assertEqual(git_blob_sha1(ROUTER_RAW), FROZEN_ROUTER_REGISTRY_BLOB)

    @unittest.skipUnless(REAL_FILE.is_file(), 'Real PR116 file absent from isolation, full checkout required')
    def test_real_cohort_and_documented_router_saved_block_split(self):
        raw = REAL_FILE.read_bytes()
        cohort = load_frozen_cohort(raw)
        report = offline_window(bind_real_fixture(cohort), cohort,
                                cohort_raw_bytes=raw, router_registry_raw=ROUTER_RAW)
        self.assertEqual(report['cohort']['cohort_binding'],
                         'VERIFIED_PR116_GIT_BLOB_OFFLINE_ONLY')
        self.assertEqual(report['router_registry_provenance'],
                         'OFFICIAL_DOCUMENTED_ONLY_NO_SWAP_CAUSALITY')
        self.assertEqual(report['metrics']['blocks_received'], 3)
        self.assertEqual(report['metrics']['watch_signer_tx_in_received_blocks'], 3)
        self.assertEqual(report['metrics']['router_control_candidates_in_received_blocks'], 3)
        self.assertFalse(report['router_control_eligible'])
        self.assertTrue(all(not x['control_eligible'] and not x['actual_e3']
                            for x in report['candidate_rows']))
        self.assertTrue(all(x['router_address_match_only']
                            for x in report['candidate_rows'] if x['group'] == 'CONTROL_CANDIDATE'))
        self.assertEqual(report['actual_rpc_calls'], 0)
        self.assertEqual(report['independent_denominator'], 'NOT_MEASURED')

    @unittest.skipUnless(REAL_FILE.is_file(), 'Real PR116 file absent from isolation, full checkout required')
    def test_modified_router_registry_raw_bytes_rejected(self):
        raw = REAL_FILE.read_bytes()
        cohort = load_frozen_cohort(raw)
        changed = ROUTER_RAW.replace(b'v3_universal', b'xx_universal', 1)
        with self.assertRaisesRegex(ValueError, 'FROZEN_ROUTER_REGISTRY_REQUIRED'):
            offline_window(bind_real_fixture(cohort), cohort,
                           cohort_raw_bytes=raw, router_registry_raw=changed)

    def test_synthetic_cohort_cannot_fake_documented_router_mode(self):
        fixture = copy.deepcopy(FIX)
        fixture['router_allowlist_kind'] = DOCUMENTED_ROUTER_MODE
        fixture.pop('synthetic_routers')
        with self.assertRaisesRegex(ValueError, 'FROZEN_ROUTER_REGISTRY_REQUIRED'):
            offline_window(fixture, FAKE, router_registry_raw=ROUTER_RAW)

    def test_original_synthetic_fixture_still_runs_unchanged(self):
        out = offline_window(copy.deepcopy(FIX), copy.deepcopy(FAKE))
        self.assertEqual(out['router_registry_provenance'], 'SYNTHETIC_ROUTER_FIXTURE_ONLY')
        self.assertEqual(out['metrics']['watch_signer_tx_in_received_blocks'], 3)
        self.assertEqual(out['metrics']['router_control_candidates_in_received_blocks'], 3)
        self.assertTrue(all(not x['control_eligible'] for x in out['candidate_rows']))


if __name__ == '__main__':
    unittest.main()
