"""Full offline seam tests; no RPC client or clocks outside injected fixture."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_rpc_bridge import bridge_fixture, event_id

FIXTURE = json.loads((ROOT / 'fixtures' / 'rpc_bridge_replay.json').read_text())


def altered():
    return copy.deepcopy(FIXTURE)


def states(report):
    return report['state_machine']['event_rows']


def by_side(report, side):
    return next(x for x in states(report) if x['side'] == side)


class BridgeContractTests(unittest.TestCase):
    def test_end_to_end_3_receipts_two_groups_entry_exit(self):
        r = bridge_fixture(altered())
        self.assertEqual(r['events_from_rpc'], 3)
        self.assertEqual(len(r['receipt_observations']), 3)
        self.assertEqual(len(r['archive_quote_observations']), 1)
        self.assertEqual(by_side(r, 'BUY')['quote_state']['60'], 'SYNTHETIC_REPLAY_QUOTE')
        self.assertEqual(by_side(r, 'SELL')['exit_quote_state']['60'], 'NO_QUOTE')
        self.assertEqual(by_side(r, 'UNKNOWN')['state'], 'REJECTED')

    def test_no_real_evidence_promoted(self):
        r = bridge_fixture(altered())
        self.assertEqual((r['e3_actual_count'], r['quoted_actual_count'], r['paper_profit_labels']), (0, 0, 0))
        self.assertEqual((r['state_machine']['e3_actual_count'],r['state_machine']['quoted_actual_count']), (0,0))
        self.assertTrue(all(x['evidence'] == 'E0_SEEN_SYNTHETIC' for x in states(r)))
        self.assertTrue(all(x['E2_attested'] is False and x['finality'] == 'UNRESOLVED_F1_POLICY'
                            for x in r['receipt_observations']))

    def test_provisional_buy_clock_receipt_not_block(self):
        r = bridge_fixture(altered())
        b = by_side(r, 'BUY')
        self.assertEqual((b['first_received_ms'],b['actionable_ms']),(1000,2000))
        scheduled=[x for x in r['state_machine']['audit_trace'] if x['kind']=='quote_request_scheduled'
                   and x['event_id']==b['event_id']]
        self.assertEqual({x['scheduled_ms'] for x in scheduled},{62000,302000,902000})

    def test_sell_independent_exit_clock_and_label(self):
        r=bridge_fixture(altered())
        sell=by_side(r,'SELL')
        self.assertEqual((sell['first_received_ms'],sell['actionable_ms']),(1000,3000))
        self.assertFalse(sell['quote_state'])
        sched=[x for x in r['state_machine']['audit_trace'] if x['kind']=='exit_quote_request_scheduled']
        self.assertEqual({x['scheduled_ms'] for x in sched},{63000,303000,903000})

    def test_fail_receipt_must_not_signal_trade(self):
        r=bridge_fixture(altered())
        row=by_side(r,'UNKNOWN')
        self.assertEqual(row['state'],'REJECTED')
        self.assertIsNone(row['actionable_ms'])
        self.assertFalse(row['quote_state'])

    def test_archive_quote_is_never_timed_quote_response(self):
        f=altered();f['virtual_quotes']=[]
        r=bridge_fixture(f)
        self.assertEqual(r['archive_quote_observations'][0]['status'],'SIMULATED_ARCHIVE_QUOTE')
        self.assertFalse(r['archive_quote_observations'][0]['usable_as_live_quoted'])
        self.assertEqual(r['state_machine']['quote_counts'].get('SYNTHETIC_REPLAY_QUOTE',0),0)

    def test_saved_archive_quote_malformed_keeps_failure(self):
        f=altered();f['archive_quotes'][0]['rpc']={'jsonrpc':'2.0','id':3,'error':{'code':-32000}}
        r=bridge_fixture(f)
        self.assertEqual(r['archive_quote_observations'][0]['status'],'NO_QUOTE')
        self.assertEqual(r['quoted_actual_count'],0)

    def test_control_random_nonrouter_stays_absent(self):
        r=bridge_fixture(altered())
        self.assertEqual(r['events_from_rpc'],3)
        self.assertEqual(r['state_machine']['selected_control_events'],1)
        self.assertEqual({x['group'] for x in states(r)},{'WATCHLIST','CONTROL_RANDOM'})
        self.assertEqual(r['live_control_coverage'],'NOT_MEASURED')

    def test_random_control_not_selected_no_quote_schedule(self):
        f=altered();f['control_modulo']=2**32
        f['virtual_quotes']=[]
        r=bridge_fixture(f)
        sell=by_side(r,'SELL')
        self.assertFalse(sell['selected'])
        self.assertEqual(sell['exit_quote_state'],{})

    def test_backfill_ca_update_stays_without_quotes(self):
        f=altered();f['blocks'][0]['ingest_path']='BACKFILL';f['virtual_quotes']=[]
        r=bridge_fixture(f)
        self.assertEqual(by_side(r,'BUY')['quote_state'],{})
        self.assertEqual(by_side(r,'SELL')['exit_quote_state'],{})
        self.assertEqual(r['state_machine']['backfill_events'],3)

    def test_reorg_cancels_prior_virtual_quote(self):
        f=altered();f['synthetic_reorgs']=[{'tx_hash':f['blocks'][0]['rpc']['result']['transactions'][0]['hash'],
                                            'synthetic_reorg':True,'observed_ms':63000}]
        r=bridge_fixture(f)
        b=by_side(r,'BUY')
        self.assertEqual(b['state'],'INVALIDATED')
        self.assertEqual(set(b['quote_state'].values()),{'REJECTED'})
        self.assertTrue(any(x['kind']=='quote_replay' for x in r['state_machine']['audit_trace']))

    def test_reorg_cancels_exit(self):
        f=altered();f['synthetic_reorgs']=[{'tx_hash':f['blocks'][0]['rpc']['result']['transactions'][1]['hash'],
                                            'synthetic_reorg':True,'observed_ms':64000}]
        r=bridge_fixture(f)
        s=by_side(r,'SELL')
        self.assertEqual(s['state'],'INVALIDATED')
        self.assertEqual(set(s['exit_quote_state'].values()),{'REJECTED'})

    def test_receipt_failure_after_quote_has_no_fake_success(self):
        f=altered();q=f['blocks'][0]['receipts'][0]
        q['rpc']['result']['status']='0x0';q['observed_ms']=64000
        f['virtual_quotes']=[]
        r=bridge_fixture(f)
        b=next(x for x in states(r) if x['wallet']=='0x'+'1'*40)
        self.assertEqual(b['state'],'REJECTED')
        self.assertEqual(b['side'],'UNKNOWN')

    def test_receipt_tx_mismatch_fails(self):
        f=altered();f['blocks'][0]['receipts'][0]['rpc']['result']['blockHash']='0x'+'0'*64
        with self.assertRaisesRegex(ValueError,'RECEIPT_BLOCK_IDENTITY_MISMATCH'):
            bridge_fixture(f)

    def test_wrong_receipt_tx_unobserved_fails(self):
        f=altered();f['blocks'][0]['receipts'][0]['rpc']['result']['transactionHash']='0x'+'d'*64
        with self.assertRaisesRegex(ValueError,'RECEIPT_FOR_UNOBSERVED_TX'):
            bridge_fixture(f)

    def test_observed_receipt_before_block_fails(self):
        f=altered();f['blocks'][0]['receipts'][0]['observed_ms']=999
        with self.assertRaisesRegex(ValueError,'RECEIPT_PRECEDES_BLOCK_OBSERVATION'):
            bridge_fixture(f)

    def test_duplicate_transactions_fails(self):
        f=altered();f['blocks'][0]['rpc']['result']['transactions'].append(
            copy.deepcopy(f['blocks'][0]['rpc']['result']['transactions'][0]))
        with self.assertRaisesRegex(ValueError,'DUPLICATE_TRANSACTION'):
            bridge_fixture(f)

    def test_no_direct_live_mode(self):
        f=altered();f['mode']='LIVE'
        with self.assertRaisesRegex(ValueError,'BRIDGE_ONLY_OFFLINE_TRIAL_INPUT'):
            bridge_fixture(f)

    def test_archive_quote_not_allowed_in_virtual_interface(self):
        f=altered();f['virtual_quotes'][0]['synthetic_response']=False
        with self.assertRaisesRegex(ValueError,'LIVE_OR_ARCHIVE_QUOTE_AS_SYNTHETIC_FORBIDDEN'):
            bridge_fixture(f)

    def test_virtual_response_bad_amount_is_no_quote(self):
        f=altered();f['virtual_quotes'][0].pop('synthetic_amount_out_raw')
        r=bridge_fixture(f)
        self.assertEqual(by_side(r,'BUY')['quote_state']['60'],'NO_QUOTE')

    def test_late_request_not_quoted(self):
        f=altered();f['virtual_quotes'][0]['requested_ms']=62001
        r=bridge_fixture(f)
        self.assertEqual(by_side(r,'BUY')['quote_state']['60'],'MISSED_DEADLINE')

    def test_reject_bad_injected_time(self):
        f=altered();f['blocks'][0]['observed_ms']=True
        with self.assertRaisesRegex(ValueError,'INVALID_INJECTED_CLOCK'):
            bridge_fixture(f)

    def test_wrong_hex_abi_do_not_fabricate_live_quote(self):
        f=altered();f['archive_quotes'][0]['rpc']['result']='0x01'
        r=bridge_fixture(f)
        self.assertEqual(r['archive_quote_observations'][0]['status'],'NO_QUOTE')
        self.assertEqual(r['quoted_actual_count'],0)

    def test_hash_provenance_and_stable_event_id(self):
        r=bridge_fixture(altered())
        self.assertEqual(len(r['source_provenance']),5)
        self.assertTrue(all(len(x['sha256'])==64 for x in r['source_provenance']))
        for x in states(r):
            self.assertEqual(x['event_id'],event_id(x['wallet'],next(y['hash'] for y in
                            altered()['blocks'][0]['rpc']['result']['transactions'] if y['from']==x['wallet'])))

    def test_distinct_batch_order_does_not_change_first_seen(self):
        f=altered();f['blocks'][0]['receipts'].reverse()
        r=bridge_fixture(f)
        self.assertEqual(by_side(r,'BUY')['first_received_ms'],1000)
        self.assertEqual(by_side(r,'BUY')['actionable_ms'],2000)

    def test_scope_uses_only_saved_rpc_and_synthetic_quotes(self):
        r=bridge_fixture(altered())
        self.assertEqual(r['actual_rpc_calls'],0)
        self.assertIn('NO_NETWORK',r['safety'])
        self.assertEqual(r['independent_denominator'],'NOT_MEASURED')
        self.assertEqual(r['clock_provenance'],'INJECTED_OFFLINE_TIMESTAMPS_NOT_PUBLIC_FIRST_SEEN')


if __name__=='__main__':
    unittest.main()
