"""Offline-only 24-call read-only qualification: budget, freeze, failures, audit."""
import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_l1_code_probe import (
    MAX_CALLS, MAX_WALLETS, MAX_ROUTERS, METHODS, SCOPE, ENDPOINT,
    AttemptJournal, QualificationClient, atomic_json, fixture_sender, probe,
    source_quantity, transport_error, validate_qualification_permit,
    verify_loaded_sources, bounded_report_path, DEPENDENCIES,
)
from f0_l1_preflight import official_router_addresses

COHORT = json.loads((ROOT/'fixtures/l1_fake_cohort.json').read_text())
REGISTRY = json.loads((ROOT/'F0_ROUTER_SOURCE_CANDIDATES.json').read_text())
WATCH = sorted(r['wallet'] for r in COHORT['preliminary_wallets'] if r['role']=='PRIMARY')
ROUTERS = sorted(official_router_addresses(REGISTRY))


def sequence(height=100):
    calls=[('eth_chainId', [], '0x38'), ('eth_blockNumber', [], hex(height))]
    calls += [('eth_getCode', [w,hex(height)], '0x') for w in WATCH]
    calls += [('eth_getCode', [w,hex(height)], '0x6000') for w in ROUTERS]
    return {'mode':'OFFLINE_SYNTHETIC_ONLY','trial':True,
            'responses':[{'method':m,'params':params,'result':r} for m,params,r in calls]}


def run(rows=None, *, journal=None, cohort=None, sender=None):
    if sender is None:
        sender=fixture_sender({'mode':'OFFLINE_SYNTHETIC_ONLY','trial':True,
                               'responses':rows or sequence()['responses']})
    return probe(sender, copy.deepcopy(cohort or COHORT), copy.deepcopy(REGISTRY),
                 journal=journal, sleep=lambda _: None)


class FullPlanTests(unittest.TestCase):
    def test_success_is_exact_24_calls_and_no_runtime_privilege(self):
        j=AttemptJournal(None,MAX_CALLS,mode='OFFLINE_INJECTED_SENDER')
        r=run(journal=j)
        self.assertEqual(len(j.rows), 24)
        self.assertEqual((r['attempted_rpc_calls'],r['attempted_primary_getcode'],
                          r['attempted_router_getcode'],r['attempted_identity_reads']),
                         (24,20,2,2))
        self.assertEqual((r['saved_getcode_attempts'],r['saved_getcode_not_checked']), (20,0))
        self.assertEqual(r['stop_state'],'QUALIFICATION_READS_COMPLETE_NOT_LIVE_MONITORING')
        self.assertFalse(r['live_watchlist_enabled'])
        self.assertFalse(r['live_control_enabled'])
        self.assertFalse(r['router_onchain_code_verified'])
        self.assertEqual(r['e3_actual_count'],0)
        self.assertEqual(r['provider_billed'],'UNVERIFIED')
        self.assertEqual(r['actual_rpc_calls'],0)
        self.assertTrue(all(x['state']=='RPC_RESPONSE' for x in j.rows))

    def test_window_expired_blocks_before_attempt_and_sender(self):
        j=AttemptJournal(None,24,mode='OFFLINE')
        called=[]
        expired=datetime.now(timezone.utc)-timedelta(seconds=1)
        c=QualificationClient(lambda *a: called.append(a), j, 1024,
                              deadline=expired)
        with self.assertRaisesRegex(ValueError,'QUALIFICATION_WINDOW_EXPIRED_BEFORE_REQUEST'):
            c.call('eth_chainId',[],'SOURCE_IDENTITY')
        self.assertEqual((len(j.rows),len(called)),(0,0))

    def test_pinned_block_for_all_22_getcode(self):
        j=AttemptJournal(None,24,mode='OFFLINE')
        r=run(journal=j)
        self.assertEqual({tuple(x['params'][1:]) for x in j.rows if x['method']=='eth_getCode'}, {('0x64',)})
        self.assertEqual(len({x['params'][0] for x in j.rows if x['method']=='eth_getCode'}),22)
        self.assertEqual(r['requested_height'],100)

    def test_proposed_cap_prevents_25th_send(self):
        j=AttemptJournal(None,24,mode='OFFLINE')
        run(journal=j)
        with self.assertRaisesRegex(ValueError,'QUALIFICATION_REQUEST_CAP_REACHED'):
            j.begin('eth_getCode',[WATCH[0],'0x64'],'PRIMARY_CODE')
        self.assertEqual(len(j.rows),24)

    def test_journal_recorded_before_transport_failure(self):
        with tempfile.TemporaryDirectory(prefix='f0-24-journal-') as tmp:
            j=AttemptJournal(Path(tmp)/'journal.json',24,mode='OFFLINE_TEST')
            def sender(endpoint, payload, cap):
                prior=json.loads((Path(tmp)/'journal.json').read_text())
                self.assertEqual(prior['attempted_rpc_calls'],1)
                self.assertEqual(prior['attempts'][0]['state'],'ATTEMPTED_OUTCOME_UNKNOWN')
                raise TimeoutError('fake SECRET')
            client=QualificationClient(sender,j,2000)
            row,err,idx=client.call('eth_getCode',[WATCH[0],'0x64'],'PRIMARY_CODE')
            self.assertIsNone(row)
            self.assertEqual((err,idx),('NETWORK_TIMEOUT',1))
            persisted=json.loads((Path(tmp)/'journal.json').read_text())
            self.assertEqual(persisted['attempts'][0]['failure_code'],'NETWORK_TIMEOUT')
            self.assertNotIn('SECRET',json.dumps(persisted))

    def test_unexpected_interrupt_retains_in_flight_journal(self):
        with tempfile.TemporaryDirectory(prefix='f0-24-crash-') as tmp:
            j=AttemptJournal(Path(tmp)/'journal.json',24,mode='OFFLINE_TEST')
            def broken(*args):
                raise KeyboardInterrupt('simulated fatal signal')
            with self.assertRaises(KeyboardInterrupt):
                QualificationClient(broken,j,2000).call('eth_chainId',[],'SOURCE_IDENTITY')
            data=json.loads((Path(tmp)/'journal.json').read_text())
            self.assertEqual(data['attempted_rpc_calls'],1)
            self.assertEqual(data['attempts'][0]['state'],'ATTEMPTED_OUTCOME_UNKNOWN')

    def test_rpc_error_in_wallet_does_not_erase_next_wallet(self):
        rows=sequence()['responses']
        rows[2].pop('result')
        rows[2]['error']={'code': -32000,'message':'fake PRIVATE_KEY_NESTED'}
        r=run(rows)
        self.assertEqual(r['saved_getcode_rpc_errors'],1)
        self.assertEqual(r['saved_getcode_attempts'],20)
        self.assertEqual(r['counts']['NOT_CHECKED'],0)
        self.assertNotIn('PRIVATE_KEY_NESTED',json.dumps(r))

    def test_one_network_failure_counted_and_next_wallet_processed(self):
        j=AttemptJournal(None,24,mode='OFFLINE')
        fake=fixture_sender(sequence())
        def sender(endpoint,payload,cap):
            if payload['id']==3:
                # keep the fixture cursor aligned with the next call
                # sender handles the other 23 by matching current expected slots
                raise TimeoutError('secret')
            if payload['id']>=4:
                index=payload['id']-1
                expected=sequence()['responses'][index]
                return {'jsonrpc':'2.0','id':payload['id'],'result':expected['result']}
            return fake(endpoint,payload,cap)
        r=run(sender=sender,journal=j)
        self.assertEqual((r['saved_getcode_transport_failures'], r['saved_getcode_success_responses']),(1,19))
        self.assertEqual(r['attempted_rpc_calls'],24)

    def test_three_consecutive_failures_stops_without_spending_rest(self):
        def sender(endpoint,payload,cap):
            if payload['id']<=2:
                return {'jsonrpc':'2.0','id':payload['id'],'result':'0x38' if payload['id']==1 else '0x64'}
            raise TimeoutError('secret')
        j=AttemptJournal(None,24,mode='OFFLINE')
        r=run(sender=sender,journal=j)
        self.assertEqual((r['attempted_rpc_calls'],r['attempted_primary_getcode']), (5,3))
        self.assertEqual(r['saved_getcode_transport_failures'],3)
        self.assertEqual(r['saved_getcode_not_checked'],17)
        self.assertEqual(r['stop_state'],'BLOCKED_SOURCE')
        self.assertEqual(r['error_code'],'THREE_CONSECUTIVE_SOURCE_FAILURES')

    def test_wrong_chain_stops_after_one_call(self):
        rows=sequence()['responses']; rows[0]['result']='0x61'
        j=AttemptJournal(None,24,mode='OFFLINE')
        r=run(rows,journal=j)
        self.assertEqual(r['attempted_rpc_calls'],1)
        self.assertEqual(r['saved_getcode_not_checked'],20)
        self.assertEqual(r['stop_state'],'BLOCKED_SOURCE')

    def test_invalid_error_mixed_with_result_cannot_claim_success(self):
        def sender(endpoint,payload,cap):
            if payload['id']<=2:
                return {'jsonrpc':'2.0','id':payload['id'],'result':'0x38' if payload['id']==1 else '0x64'}
            return {'jsonrpc':'2.0','id':payload['id'],'result':'0x', 'error':{'code':-32000}}
        j=AttemptJournal(None,24,mode='OFFLINE')
        r=run(sender=sender,journal=j)
        self.assertEqual(r['attempted_rpc_calls'],3)
        self.assertEqual(r['unreconciled_attempts'],1)
        self.assertEqual(r['stop_state'],'BLOCKED_SOURCE')
        self.assertEqual(r['saved_getcode_not_checked'],20)

    def test_response_id_mismatch_never_becomes_wallet_observation(self):
        def sender(endpoint,payload,cap):
            return {'jsonrpc':'2.0','id':999,'result':'0x38'}
        r=run(sender=sender)
        self.assertEqual(r['attempted_rpc_calls'],1)
        self.assertEqual(r['attempted_identity_reads'],1)
        self.assertEqual(r['stop_state'],'BLOCKED_SOURCE')

    def test_no_synthetic_marker_rejected_before_any_attempt(self):
        c=copy.deepcopy(COHORT);c.pop('synthetic_fixture_only')
        with self.assertRaisesRegex(ValueError,'QUALIFICATION_OFFLINE_FIXTURE_REQUIRED'):
            run(cohort=c)

    def test_no_fake_can_claim_real_raw_manifest(self):
        with self.assertRaisesRegex(ValueError, 'QUALIFICATION_REAL_COHORT_MISSING_OR_CHANGED'):
            probe(fixture_sender(sequence()), COHORT, REGISTRY, strict_frozen=True)

    def test_no_chain_validation_claims_finality_e2_or_pnl(self):
        result=run()
        self.assertEqual(result['e1_finality'],'UNRESOLVED_F1_POLICY')
        self.assertFalse(result['e2_attested'])
        self.assertEqual(result['quoted_actual_count'],0)
        self.assertEqual(result['paper_profit_labels'],0)


class PermitTests(unittest.TestCase):
    def setUp(self):
        now=datetime.now(timezone.utc)
        iso=lambda d:d.isoformat(timespec='seconds').replace('+00:00','Z')
        self.now=now
        self.permit={
            'scope':SCOPE,'user_authorized':True,
            'approved_commit_sha':'a'*40, 'approved_source_sha256':'b'*64,
            'run_nonce':'c'*64,'approved_endpoint':ENDPOINT,'methods':list(METHODS),
            'chain_id':56,'cost_policy':'FREE_ONLY_NO_PAYMENT',
            'local_environment':'USER_MAC_LOCAL_ONLY','max_total_rpc_calls':24,
            'max_wallet_getcode_calls':20,'max_router_getcode_calls':2,
            'max_response_bytes':2000000,'no_retries':True,'no_ws':True,
            'store_raw_payloads':False,'background':False,'retention_hours':24,
            'storage_root':'/tmp/f0-24-test-probe','window_start_utc':iso(now-timedelta(seconds=5)),
            'window_end_utc':iso(now+timedelta(minutes=5)),
            'approved_manifest_blob':'fcd0029314353313867e565190cd4f2882089f11',
            'min_interval_ms':100,
        }

    def test_import_dependency_bound_including_offline_collector(self):
        self.assertIn('f0_offline_collector.py', DEPENDENCIES)

    def test_valid_dry_permit_never_implies_user_approval(self):
        validate_qualification_permit(self.permit,self.now)

    def test_old_four_call_smoke_permit_cannot_authorize(self):
        p=copy.deepcopy(self.permit);p['scope']='ONE_TIME_BSC_PUBLIC_HTTP_SOURCE_SMOKE_ONLY'
        with self.assertRaisesRegex(ValueError,'QUALIFICATION_AUTHORIZATION_REQUIRED'):
            validate_qualification_permit(p,self.now)

    def test_wrong_limits_and_unknown_methods_rejected(self):
        for key, value in [('max_total_rpc_calls',25),('max_router_getcode_calls',3),
                           ('methods',['eth_chainId','eth_getLogs']),
                           ('min_interval_ms',0),('background',True)]:
            with self.subTest(key=key):
                p=copy.deepcopy(self.permit);p[key]=value
                with self.assertRaises(ValueError):
                    validate_qualification_permit(p,self.now)

    def test_expired_window_rejected(self):
        p=copy.deepcopy(self.permit);p['window_end_utc']='2020-01-01T00:00:00Z'
        with self.assertRaises(ValueError):
            validate_qualification_permit(p,self.now)

    def test_dependency_mutation_fails_closed_without_git(self):
        with self.assertRaises(ValueError):
            verify_loaded_sources(self.permit,ROOT/'f0_l1_code_probe.py')

    def test_report_path_outside_storage_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaisesRegex(ValueError,'QUALIFICATION_REPORT_OUTSIDE_APPROVED_STORAGE'):
                bounded_report_path(root/'othername.json',root)

    def test_atomic_json_journal_writes_private_file_and_nondata(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'journal.json'
            atomic_json(p, {'attempted_rpc_calls':1})
            self.assertEqual(json.loads(p.read_text())['attempted_rpc_calls'],1)
            self.assertFalse((p.parent/(p.name+'.tmp.'+str(__import__('os').getpid()))).exists())


if __name__=='__main__': unittest.main()
