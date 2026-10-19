"""Offline L1 contiguous-block and Router control-denominator test suite."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_l1_window import (offline_window, cohort_watchlist, utc_ms, SCHEMA, MAX_WINDOW,
                          git_blob_sha1, load_frozen_cohort, FROZEN_PR116_BLOB,
                          FROZEN_PR116_MANIFEST_PATH, ARCHITECTURE_SHA)
from f0_offline_collector import _hash32

FIX = json.loads((ROOT / "fixtures/l1_contiguous_replay.json").read_text())
COHORT = json.loads((ROOT / "fixtures/l1_fake_cohort.json").read_text())


def go(f=None, c=None):
    return offline_window(copy.deepcopy(FIX if f is None else f),
                          copy.deepcopy(COHORT if c is None else c))


class ContiguousBlockWindowOfflineTests(unittest.TestCase):
    def test_nominal_gaps_and_attempts_are_accounted(self):
        out = go()
        m = out['metrics']
        self.assertEqual((m['blocks_expected_window'], m['blocks_received'], m['blocks_failed']), (5, 3, 1))
        self.assertEqual(m['missing_heights'], [101, 102])
        self.assertEqual([v['state'] for v in out['block_rows']],
                         ['RECEIVED', 'FAILED', 'MISSING_NOT_ATTEMPTED', 'RECEIVED', 'RECEIVED'])
        self.assertEqual(m['attempted_full_block_rpc_calls_offline'], 4)
        self.assertEqual(m['attempted_control_discovery_rpc_calls_offline'], 4)

    def test_watch_and_router_control_split(self):
        m = go()['metrics']
        self.assertEqual(m['watch_signer_tx_in_received_blocks'], 3)
        self.assertEqual(m['router_control_candidates_in_received_blocks'], 3)
        self.assertEqual(m['preselected_control_offline'], 2)

    def test_receive_only_not_eligible_from_sent_to_wallet(self):
        x = copy.deepcopy(FIX)
        outsider = x['block_attempts'][0]['rpc']['result']['transactions'][-1]
        outsider['to'] = COHORT['preliminary_wallets'][0]['wallet']
        self.assertEqual(go(x)['metrics']['watch_signer_tx_in_received_blocks'], 3)

    def test_random_selection_uses_approved_algorithm(self):
        out = go()
        control = [c for c in out['candidate_rows'] if c['group']=='CONTROL_CANDIDATE']
        self.assertEqual(len(control), 3)
        for c in control:
            key = COHORT['selection_seed']+'|'+c['wallet']+'|'+c['tx_hash']
            self.assertEqual(c['control_selected_offline'], _hash32(key)%FIX['control_modulo']==0)

    def test_preselected_cohort_not_verified_eoa(self):
        out = go()
        self.assertEqual(out['cohort']['primary_count'], 20)
        self.assertEqual(out['cohort']['technical_eoa_eligibility'], 'UNVERIFIED')
        self.assertFalse(out['cohort']['watch_runtime_enabled'])
        self.assertEqual(out['cohort']['cohort_binding'], 'SYNTHETIC_FIXTURE_NOT_REAL_COHORT')

    def test_no_real_network_and_no_real_labels(self):
        out = go()
        self.assertEqual(out['actual_rpc_calls'], 0)
        self.assertEqual(out['stop_state'], 'NO_RUN')
        self.assertEqual(out['live_control_coverage'], 'NOT_MEASURED')
        self.assertEqual(out['first_actionable_latency'], 'NOT_MEASURED')
        self.assertFalse(out['e2_attested'])
        self.assertEqual((out['e3_actual_count'], out['quoted_actual_count'], out['paper_profit_labels']), (0,0,0))
        self.assertTrue(all(c['side']=='UNKNOWN' and not c['actual_e3'] for c in out['candidate_rows']))

    def test_backfill_is_separate(self):
        out = go()
        self.assertEqual(out['metrics']['backfill_received_blocks'], 1)
        self.assertTrue(all(not c['actual_e3'] for c in out['candidate_rows'] if c['ingest_path']=='BACKFILL'))

    def test_parent_hash_is_checked_when_contiguous(self):
        x = copy.deepcopy(FIX)
        x['block_attempts'][-1]['rpc']['result']['parentHash']='0x'+'01'*32
        with self.assertRaisesRegex(ValueError, 'CONTIGUOUS_PARENT_HASH_MISMATCH'):
            go(x)

    def test_parent_not_presumed_across_missing_height(self):
        out = go()
        self.assertEqual(out['block_rows'][3]['state'], 'RECEIVED')
        self.assertEqual(out['block_rows'][2]['state'], 'MISSING_NOT_ATTEMPTED')

    def test_reject_duplicate_height(self):
        x = copy.deepcopy(FIX); x['block_attempts'].append(copy.deepcopy(x['block_attempts'][0]))
        x['max_rpc_calls'] = x['max_control_discovery_calls'] = 5
        with self.assertRaisesRegex(ValueError, 'OUT_OF_RANGE_OR_DUPLICATE_HEIGHT'):
            go(x)

    def test_reject_wrong_block_number(self):
        x=copy.deepcopy(FIX); x['block_attempts'][0]['rpc']['result']['number']='0x88'
        with self.assertRaisesRegex(ValueError, 'TX_BLOCK_NUMBER_MISMATCH'):
            go(x)

    def test_reject_bad_transaction_origin_block(self):
        x=copy.deepcopy(FIX); x['block_attempts'][0]['rpc']['result']['transactions'][0]['blockHash']='0x'+'00'*32
        with self.assertRaisesRegex(ValueError, 'TX_BLOCK_HASH_MISMATCH'):
            go(x)

    def test_reject_over_total_budget(self):
        x=copy.deepcopy(FIX); x['max_rpc_calls']=3
        with self.assertRaisesRegex(ValueError, 'OFFLINE_RPC_OR_CONTROL_BUDGET_EXCEEDED'):
            go(x)

    def test_reject_over_control_budget(self):
        x=copy.deepcopy(FIX); x['max_control_discovery_calls']=3
        with self.assertRaisesRegex(ValueError, 'OFFLINE_RPC_OR_CONTROL_BUDGET_EXCEEDED'):
            go(x)

    def test_reject_invalid_time_order(self):
        x=copy.deepcopy(FIX); x['block_attempts'][0]['response_utc']='2026-10-19T19:59:59.000Z'
        with self.assertRaisesRegex(ValueError, 'INCONSISTENT_OBSERVATION_CLOCKS'):
            go(x)

    def test_reject_invalid_monotonic_order(self):
        x=copy.deepcopy(FIX); x['block_attempts'][1]['request_monotonic_ms']=1
        with self.assertRaisesRegex(ValueError, 'INCONSISTENT_OBSERVATION_CLOCKS'):
            go(x)

    def test_reject_utc_without_z(self):
        x=copy.deepcopy(FIX); x['block_attempts'][0]['first_received_utc']='2026-10-19T20:00:00+00:00'
        with self.assertRaisesRegex(ValueError, 'UTC_REQUIRED'):
            go(x)

    def test_failed_attempt_is_counted_not_success(self):
        out=go()
        self.assertEqual(out['block_rows'][1]['error_code'], 'NETWORK_TIMEOUT')
        self.assertEqual(out['block_rows'][1]['attempted_calls'], 1)
        self.assertNotIn('source_rpc_sha256',out['block_rows'][1])

    def test_failed_attempt_cannot_fake_receipt(self):
        x=copy.deepcopy(FIX); x['block_attempts'][1]['rpc']={'jsonrpc':'2.0','id':9,'result':{}}
        with self.assertRaisesRegex(ValueError, 'FAILED_CALL_MUST_HAVE_ERROR_NOT_FAKE_RPC'):
            go(x)

    def test_reject_non_allowlisted_router_and_wrong_group(self):
        x=copy.deepcopy(FIX); x['synthetic_routers']=['0x'+'01'*20]
        out=go(x)
        self.assertEqual(out['metrics']['router_control_candidates_in_received_blocks'], 0)
        x['router_allowlist_kind']='UNVERIFIED_REAL'
        with self.assertRaisesRegex(ValueError, 'NO_VERIFIED_ROUTER_ALLOWLIST'):
            go(x)

    def test_bad_frozen_cohort_revision(self):
        c=copy.deepcopy(COHORT); c['reviewed_architecture_commit']='x'
        with self.assertRaisesRegex(ValueError, 'WRONG_FROZEN_COHORT_IDENTITY'):
            go(c=c)

    def test_bad_cohort_source_split(self):
        c=copy.deepcopy(COHORT); c['preliminary_wallets'][0]['source']='PR97_449_BSC_SIGNED'
        with self.assertRaisesRegex(ValueError, 'COHORT_10_PRIMARY_5_BACKUP_EACH_STRATUM_REQUIRED'):
            go(c=c)

    def test_concurrent_block_requests_not_implicitly_forbidden(self):
        x=copy.deepcopy(FIX)
        second=x['block_attempts'][1]
        second['request_monotonic_ms']=150
        second['response_monotonic_ms']=2300
        second['first_received_monotonic_ms']=2320
        second['request_utc']='2026-10-19T20:00:00.050Z'
        second['response_utc']='2026-10-19T20:00:02.200Z'
        second['first_received_utc']='2026-10-19T20:00:02.250Z'
        out=go(x)
        self.assertEqual(out['metrics']['blocks_failed'], 1)

    def test_cohort_backup_strata_must_remain_five_each(self):
        c=copy.deepcopy(COHORT)
        c['preliminary_wallets'][10]['source']='PR97_449_BSC_SIGNED'
        with self.assertRaisesRegex(ValueError, 'COHORT_10_PRIMARY_5_BACKUP_EACH_STRATUM_REQUIRED'):
            go(c=c)

    def test_cohort_outcome_field_forbidden(self):
        c=copy.deepcopy(COHORT); c['preliminary_wallets'][0]['pnl_30d']=100
        with self.assertRaisesRegex(ValueError, 'OUTCOME_FIELDS_FORBIDDEN'):
            go(c=c)

    def test_cohort_runtime_never_autoenabled(self):
        c=copy.deepcopy(COHORT); c['preliminary_wallets'][0]['watch_runtime_enabled']=True
        with self.assertRaisesRegex(ValueError, 'INVALID_COHORT_ENTRY'):
            go(c=c)

    def test_reject_future_expanded_window(self):
        x=copy.deepcopy(FIX); x['end_height']=x['start_height']+MAX_WINDOW
        with self.assertRaisesRegex(ValueError, 'WINDOW_EXCEEDS_OFFLINE_CAP'):
            go(x)

    def test_fixture_cannot_claim_live(self):
        x=copy.deepcopy(FIX); x['mode']='LIVE_BSC_RPC'
        with self.assertRaisesRegex(ValueError, 'OFFLINE_ONLY'):
            go(x)

    def test_control_seed_cannot_override_manifest_seed(self):
        x = copy.deepcopy(FIX)
        x['control_seed'] = 'f0-control-precommit-v1'
        with self.assertRaisesRegex(ValueError, 'FIXTURE_CONTROL_SEED_OVERRIDE_FORBIDDEN'):
            go(x)

    def test_synthetic_cohort_cannot_claim_real_binding(self):
        x = copy.deepcopy(FIX)
        x['cohort_source_kind'] = 'FROZEN_PR116_GIT_BLOB'
        with self.assertRaisesRegex(ValueError, 'FROZEN_COHORT_RAW_BYTES_REQUIRED'):
            go(x)

    def test_frozen_blob_mutation_rejected_preparse(self):
        raw = json.dumps(COHORT, sort_keys=True).encode()
        self.assertNotEqual(git_blob_sha1(raw), FROZEN_PR116_BLOB)
        with self.assertRaisesRegex(ValueError, 'FROZEN_COHORT_GIT_BLOB_MISMATCH'):
            load_frozen_cohort(raw)

    def test_manifest_seed_cannot_be_changed(self):
        c = copy.deepcopy(COHORT)
        c['selection_seed'] = 'f0-control-precommit-v1'
        with self.assertRaisesRegex(ValueError, 'WRONG_FROZEN_COHORT_IDENTITY'):
            go(c=c)

    def test_synthetic_flag_required(self):
        c = copy.deepcopy(COHORT)
        c.pop('synthetic_fixture_only')
        with self.assertRaisesRegex(ValueError, 'SYNTHETIC_COHORT_MUST_BE_EXPLICIT'):
            go(c=c)

    def test_explicit_cohort_source_kind_required(self):
        x = copy.deepcopy(FIX)
        x.pop('cohort_source_kind')
        with self.assertRaisesRegex(ValueError, 'EXPLICIT_COHORT_SOURCE_REQUIRED'):
            go(x)

    @unittest.skipUnless((ROOT / 'F0_COHORT_PRESELECTION.json').is_file(),
                         'Real PR116 manifest exists in checked-out Git tree, absent from isolated local test copy')
    def test_real_pr116_git_blob_and_primary_wallet_positive(self):
        raw = (ROOT / 'F0_COHORT_PRESELECTION.json').read_bytes()
        self.assertEqual(git_blob_sha1(raw), FROZEN_PR116_BLOB)
        cohort = load_frozen_cohort(raw)
        self.assertEqual(cohort['selection_seed'], ARCHITECTURE_SHA)
        self.assertEqual(len(cohort['preliminary_wallets']), 30)
        self.assertNotEqual({row['wallet'] for row in cohort['preliminary_wallets']},
                            {row['wallet'] for row in COHORT['preliminary_wallets']})
        x = copy.deepcopy(FIX)
        x['cohort_source_kind'] = 'FROZEN_PR116_GIT_BLOB'
        real_wallet = next(row['wallet'] for row in cohort['preliminary_wallets']
                           if row['role']=='PRIMARY' and row['source']=='PR40_23')
        x['block_attempts'][0]['rpc']['result']['transactions'][0]['from'] = real_wallet
        out = offline_window(x, cohort, cohort_raw_bytes=raw)
        self.assertEqual(out['cohort']['cohort_binding'], 'VERIFIED_PR116_GIT_BLOB_OFFLINE_ONLY')
        self.assertEqual(out['cohort']['frozen_manifest_blob_sha1'], FROZEN_PR116_BLOB)
        self.assertEqual(out['cohort']['control_seed_source'], 'COHORT_SELECTION_SEED')
        self.assertTrue(any(z['wallet']==real_wallet and z['group']=='WATCHLIST_PRESELECTED'
                            for z in out['candidate_rows']))
        self.assertEqual(out['actual_rpc_calls'], 0)
        self.assertEqual(out['stop_state'], 'NO_RUN')
        self.assertFalse(out['e2_attested'])
        changed = raw.replace(real_wallet.encode(), b'0x' + b'f'*40, 1)
        with self.assertRaisesRegex(ValueError, 'FROZEN_COHORT_GIT_BLOB_MISMATCH'):
            offline_window(x, cohort, cohort_raw_bytes=changed)

    def test_request_counts_do_not_grant_new_permission(self):
        x=copy.deepcopy(FIX); x['max_rpc_calls']=100; x['max_control_discovery_calls']=100
        out=go(x)
        self.assertEqual(out['actual_rpc_calls'], 0)
        self.assertEqual(out['stop_state'], 'NO_RUN')


if __name__ == '__main__':
    unittest.main()
