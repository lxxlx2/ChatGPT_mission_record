import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from f0_offline_collector import OfflineReplay, replay_fixture, _hash32

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'fixtures' / 'offline_replay.json').read_text())
ROUTER = FIXTURE['config']['trial_routers'][0]


def clone_fixture():
    return copy.deepcopy(FIXTURE)


def event(report, event_id):
    return next(v for v in report['event_rows'] if v['event_id'] == event_id)


class F0OfflineCollectorTests(unittest.TestCase):
    def test_end_to_end_watchlist_control_same_scheduler(self):
        r = replay_fixture(clone_fixture())
        self.assertEqual(r['events'], 6)
        self.assertEqual(r['selected_control_events'], 1)
        self.assertEqual(event(r, 'event-1')['quote_state'], {k:'SYNTHETIC_REPLAY_QUOTE' for k in ('60','300','900')})
        self.assertEqual(event(r, 'event-2')['quote_state']['900'], 'NO_QUOTE')
        q = [e for e in r['audit_trace'] if e['kind'] == 'quote_request_scheduled']
        self.assertEqual(len([e for e in q if e['event_id']=='event-1']), 3)
        self.assertEqual(len([e for e in q if e['event_id']=='event-2']), 3)
        self.assertEqual(r['quoted_actual_count'], 0)
        self.assertEqual(r['paper_profit_labels'], 0)
        self.assertEqual(r['e3_actual_count'], 0)

    def test_failed_e1_rejects_three_quotes(self):
        r = replay_fixture(clone_fixture())
        self.assertEqual(event(r, 'event-3')['quote_state'], {k:'REJECTED' for k in ('60','300','900')})

    def test_control_failed_e1_symmetric(self):
        f = clone_fixture()
        control_receipt = next(x for x in f['records'] if x['kind']=='receipt' and x['event_id']=='event-2')
        control_receipt['status'] = 0
        r = replay_fixture(f)
        self.assertEqual(event(r, 'event-2')['state'], 'REJECTED')
        self.assertEqual(set(event(r,'event-2')['quote_state'].values()), {'REJECTED'})
        self.assertEqual(r['selected_control_events'], 1)  # never redraw

    def test_backfill_has_no_quote_task(self):
        r = replay_fixture(clone_fixture())
        self.assertEqual(event(r,'event-4')['quote_state'], {})
        self.assertEqual(r['backfill_events'], 1)

    def test_unknown_side_remains_in_l1_without_quote(self):
        r = replay_fixture(clone_fixture())
        self.assertEqual(r['unknown_direction_events'], 1)
        self.assertEqual(event(r, 'event-5')['quote_state'], {})

    def test_quote_path_unresolved_not_e2(self):
        r = replay_fixture(clone_fixture())
        self.assertEqual(event(r, 'event-6')['evidence'], 'E1_CONFIRMED_SYNTHETIC')
        self.assertEqual(event(r,'event-6')['reason'], 'QUOTE_PATH_UNRESOLVED_SYNTHETIC')

    def test_no_future_or_backdated_actionable(self):
        f = clone_fixture()
        f['records'][0]['actionable_ms'] -= 1
        with self.assertRaisesRegex(ValueError,'backdated/future'):
            replay_fixture(f)

    def test_no_wrong_network(self):
        f = clone_fixture()
        f['records'][0]['chain_id'] = 1
        with self.assertRaisesRegex(ValueError,'BSC-only'):
            replay_fixture(f)

    def test_no_outcome_feature_in_input(self):
        f = clone_fixture()
        f['records'][0]['profit_rank'] = 1
        with self.assertRaisesRegex(ValueError,'outcome data'):
            replay_fixture(f)

    def test_quote_not_allowed_before_due(self):
        f = clone_fixture()
        quote = next(x for x in f['records'] if x['kind']=='quote')
        quote['at_ms'] = quote['requested_ms'] - 1
        quote['requested_ms'] = quote['at_ms']
        quote['received_ms'] = quote['at_ms']
        f['records'].sort(key=lambda x:x['at_ms'])
        with self.assertRaisesRegex(ValueError,'before scheduled'):
            replay_fixture(f)

    def test_late_request_flagged_and_not_shifted(self):
        f = clone_fixture()
        quote = next(x for x in f['records'] if x['kind']=='quote')
        quote['requested_ms'] += 1
        r = replay_fixture(f)
        self.assertEqual(event(r,'event-1')['quote_state']['60'], 'MISSED_DEADLINE')
        self.assertEqual(event(r,'event-1')['quote_state']['300'], 'SYNTHETIC_REPLAY_QUOTE')

    def test_reorg_invalidates_prior_quotes(self):
        f = clone_fixture()
        f['records'].append({'kind':'reorg','at_ms':940000,'event_id':'event-1',
                             'tx_hash': next(x['tx_hash'] for x in f['records'] if x['event_id']=='event-1' and x['kind']=='detection')})
        f['records'].sort(key=lambda x:x['at_ms'])
        r = replay_fixture(f)
        self.assertEqual(event(r,'event-1')['state'], 'INVALIDATED')
        self.assertEqual(set(event(r,'event-1')['quote_state'].values()), {'REJECTED'})
        self.assertEqual(len([x for x in r['audit_trace'] if x['kind']=='quote_replay' and x['event_id']=='event-1']), 3)

    def test_bad_quote_causal_path(self):
        f = clone_fixture()
        receipt = next(x for x in f['records'] if x['kind']=='receipt' and x['event_id']=='event-1')
        receipt['flow']['quote']['from'] = '0x'+'9'*40
        r = replay_fixture(f)
        self.assertEqual(event(r,'event-1')['evidence'], 'E1_CONFIRMED_SYNTHETIC')

    def test_wrong_router_fails_closed(self):
        f = clone_fixture()
        receipt = next(x for x in f['records'] if x['kind']=='receipt' and x['event_id']=='event-1')
        receipt['router'] = '0x'+'9'*40
        with self.assertRaisesRegex(ValueError, 'router not on trial allowlist'):
            replay_fixture(f)

    def test_failing_confirmation_depth(self):
        f = clone_fixture()
        receipt = next(x for x in f['records'] if x['kind']=='receipt' and x['event_id']=='event-1')
        receipt['confirmations'] = 0
        r = replay_fixture(f)
        self.assertEqual(event(r,'event-1')['state'], 'REJECTED')

    def test_unordered_clock_fails(self):
        f = clone_fixture()
        f['records'][0], f['records'][1] = f['records'][1],f['records'][0]
        with self.assertRaisesRegex(ValueError,'orphan receipt'):
            replay_fixture(f)

    def test_duplicate_exact_row_idempotent(self):
        f = clone_fixture()
        f['records'].insert(1,copy.deepcopy(f['records'][0]))
        r = replay_fixture(f)
        self.assertEqual(r['duplicates_skipped'], 1)
        self.assertEqual(r['events'], 6)

    def test_conflicting_duplicate_id_rejected(self):
        f = clone_fixture()
        row = copy.deepcopy(f['records'][0])
        row['first_received_ms'] -= 1
        f['records'].insert(1,row)
        with self.assertRaisesRegex(ValueError,'duplicate conflicting'):
            replay_fixture(f)

    def test_signed_sender_mismatch_rejected(self):
        f = clone_fixture()
        receipt = next(x for x in f['records'] if x['kind']=='receipt' and x['event_id']=='event-1')
        receipt['tx_from'] = '0x'+'9'*40
        r = replay_fixture(f)
        self.assertEqual(event(r,'event-1')['state'], 'REJECTED')

    def test_control_deterministic_no_redraw(self):
        f = clone_fixture()
        f['config']['control_modulo'] = 5
        r1 = replay_fixture(f)
        r2 = replay_fixture(f)
        self.assertEqual(r1['event_rows'],r2['event_rows'])
        c = event(r1,'event-2')
        picked = _hash32(f"f0-control-precommit-v1|{c['wallet']}|"+
                         next(x['tx_hash'] for x in f['records'] if x['kind']=='detection' and x['event_id']=='event-2'))%5==0
        self.assertEqual(c['selected'],picked)

    def test_sell_has_own_e2_path_but_no_buy_quote(self):
        f = clone_fixture()
        detect = next(x for x in f['records'] if x['kind']=='detection' and x['event_id']=='event-6')
        detect['side'] = 'SELL'
        receipt = next(x for x in f['records'] if x['kind']=='receipt' and x['event_id']=='event-6')
        receipt['flow']['swap_route_connected'] = True
        receipt['flow']['token']['from'] = detect['wallet']
        receipt['flow']['quote']['to'] = detect['wallet']
        r = replay_fixture(f)
        self.assertEqual(event(r,'event-6')['evidence'], 'E2_TRADE_ATTESTED_SYNTHETIC')
        self.assertEqual(event(r,'event-6')['quote_state'],{})
        self.assertEqual(set(event(r,'event-6')['exit_quote_state'].values()), {'NO_QUOTE'})
        self.assertEqual(len([x for x in r['audit_trace'] if x['kind']=='exit_quote_request_scheduled' and x['event_id']=='event-6']),3)

    def _replace_quote_response(self, event_id, updater):
        f = clone_fixture()
        q = next(x for x in f['records'] if x['kind'] == 'quote' and
                 x['event_id'] == event_id and x['delta_ms'] == 60000)
        updater(q)
        return replay_fixture(f)

    def test_quote_missing_value_watchlist_control(self):
        for eid in ('event-1', 'event-2'):
            with self.subTest(event_id=eid):
                r = self._replace_quote_response(eid, lambda x: x.pop('synthetic_amount_out_raw'))
                self.assertEqual(event(r, eid)['quote_state']['60'], 'NO_QUOTE')
                self.assertEqual(len([t for t in r['audit_trace'] if t['kind']=='quote_unavailable' and
                                      t['event_id']==eid and t['reason']=='MISSING_AMOUNT']), 1)
                self.assertEqual(event(r, eid)['quote_state']['300'], 'SYNTHETIC_REPLAY_QUOTE')

    def test_quote_error_response_watchlist_control(self):
        for eid in ('event-1', 'event-2'):
            with self.subTest(event_id=eid):
                def error_quote(q):
                    q.pop('synthetic_amount_out_raw')
                    q['error']={'code':-32000,'message':'quote unavailable'}
                    q['response_status']='ERROR'
                r = self._replace_quote_response(eid, error_quote)
                self.assertEqual(event(r,eid)['quote_state']['60'], 'NO_QUOTE')
                self.assertTrue(any(t['kind']=='quote_unavailable' and t.get('reason')=='ERROR_RESPONSE' and
                                    t.get('event_id')==eid for t in r['audit_trace']))

    def test_quote_null_value_watchlist_control(self):
        for eid in ('event-1','event-2'):
            with self.subTest(event_id=eid):
                r = self._replace_quote_response(eid,lambda q:q.__setitem__('synthetic_amount_out_raw',None))
                self.assertEqual(event(r,eid)['quote_state']['60'], 'NO_QUOTE')

    def test_quote_invalid_zero_negative_and_missing_status(self):
        for value in ('0','-1','3.0',0,{},True):
            with self.subTest(value=value):
                r = self._replace_quote_response('event-1',lambda q:q.__setitem__('synthetic_amount_out_raw',value))
                self.assertEqual(event(r,'event-1')['quote_state']['60'],'NO_QUOTE')
        def remove_status(q):
            q.pop('response_status')
        r=self._replace_quote_response('event-1',remove_status)
        self.assertEqual(event(r,'event-1')['quote_state']['60'],'NO_QUOTE')

    def _unknown_to_known_fixture(self, side='BUY', receipt_before_update=True):
        f=clone_fixture()
        detect=next(x for x in f['records'] if x['event_id']=='event-5' and x['kind']=='detection')
        rec=next(x for x in f['records'] if x['event_id']=='event-5' and x['kind']=='receipt')
        if side=='SELL':
            rec['flow']['token']['to']=ROUTER
            rec['flow']['token']['from']=detect['wallet']
            rec['flow']['quote']['from']=ROUTER
            rec['flow']['quote']['to']=detect['wallet']
        update={
            'kind':'direction_update','at_ms':10200 if receipt_before_update else 10050,
            'event_id':'event-5','chain_id':56,'wallet':detect['wallet'],
            'tx_hash':detect['tx_hash'],'side':side,
            'ca':'0x'+'a'*40,'first_received_ms':10000,
            'actionable_ms':10200 if receipt_before_update else 10050,'trial':True
        }
        f['records'].append(update)
        f['records'].sort(key=lambda r:r['at_ms'])
        return f

    def test_unknown_upgrade_after_receipt_to_buy_same_event(self):
        r=replay_fixture(self._unknown_to_known_fixture())
        self.assertEqual(r['events'],6)
        self.assertEqual(r['unknown_direction_events'],0)
        e=event(r,'event-5')
        self.assertEqual(e['first_received_ms'],10000)
        self.assertEqual(e['actionable_ms'],10200)
        self.assertEqual(e['side'],'BUY')
        self.assertEqual(e['evidence'],'E2_TRADE_ATTESTED_SYNTHETIC')
        self.assertEqual(set(e['quote_state'].values()),{'NO_QUOTE'})
        scheduled=[t for t in r['audit_trace'] if t['kind']=='quote_request_scheduled' and t['event_id']=='event-5']
        self.assertEqual([q['scheduled_ms'] for q in scheduled],[70200,310200,910200])
        self.assertEqual(len(scheduled),3)
        self.assertEqual(len([x for x in r['event_rows'] if x['event_id']=='event-5']),1)

    def test_unknown_upgrade_before_receipt_to_sell(self):
        r=replay_fixture(self._unknown_to_known_fixture('SELL',False))
        e=event(r,'event-5')
        self.assertEqual((e['side'],e['first_received_ms'],e['actionable_ms']),('SELL',10000,10050))
        self.assertEqual(e['evidence'],'E2_TRADE_ATTESTED_SYNTHETIC')
        self.assertEqual(e['quote_state'],{})
        self.assertEqual(set(e['exit_quote_state'].values()),{'NO_QUOTE'})

    def test_unknown_upgrade_prevents_clock_backdate_or_identity_change(self):
        for attr,value,message in (
            ('actionable_ms',10000,'first actual identification'),
            ('first_received_ms',10001,'cannot rewrite'),
            ('wallet','0x'+'f'*40,'identity mismatch'),
        ):
            with self.subTest(attr=attr):
                f=self._unknown_to_known_fixture()
                u=next(x for x in f['records'] if x['kind']=='direction_update')
                u[attr]=value
                with self.assertRaisesRegex(ValueError,message):replay_fixture(f)

    def test_unknown_upgrade_only_once_and_no_second_event_id(self):
        f=self._unknown_to_known_fixture()
        u=next(x for x in f['records'] if x['kind']=='direction_update')
        bad=dict(u,at_ms=10300,actionable_ms=10300)
        f['records'].append(bad)
        f['records'].sort(key=lambda r:r['at_ms'])
        with self.assertRaisesRegex(ValueError,'requires active UNKNOWN'): replay_fixture(f)
        f=self._unknown_to_known_fixture()
        d=next(x for x in f['records'] if x['kind']=='detection' and x['event_id']=='event-5')
        duplicate=dict(d,event_id='wrong-second-id',at_ms=10001,first_received_ms=10000)
        f['records'].append(duplicate)
        f['records'].sort(key=lambda r:r['at_ms'])
        with self.assertRaisesRegex(ValueError,'same wallet and tx'): replay_fixture(f)

    def test_unknown_upgrade_failed_receipt_stays_rejected(self):
        f=self._unknown_to_known_fixture()
        rec=next(x for x in f['records'] if x['kind']=='receipt' and x['event_id']=='event-5')
        rec['status']=0
        with self.assertRaisesRegex(ValueError,'requires active UNKNOWN'): replay_fixture(f)

    def _sell_fixture(self, group='WATCHLIST', fail=False, reorg=False):
        f=clone_fixture()
        d=next(x for x in f['records'] if x['kind']=='detection' and x['event_id']=='event-6')
        d['side']='SELL'
        d['group']=group
        rec=next(x for x in f['records'] if x['kind']=='receipt' and x['event_id']=='event-6')
        rec['flow']['swap_route_connected']=True
        rec['flow']['token']['from']=d['wallet']
        rec['flow']['quote']['to']=d['wallet']
        if fail:
            rec['status']=0
        if reorg:
            f['records'].append({'kind':'reorg','at_ms':500000,'event_id':'event-6','tx_hash':d['tx_hash']})
        f['records'].append({'kind':'quote','purpose':'EXIT','event_id':'event-6',
                             'at_ms':72080,'delta_ms':60000,'requested_ms':72000,
                             'received_ms':72080,'response_status':'SUCCESS',
                             'synthetic_amount_out_raw':'15'})
        f['records'].sort(key=lambda r:r['at_ms'])
        return f

    def test_sell_exit_quote_independent_and_valid(self):
        r=replay_fixture(self._sell_fixture())
        e=event(r,'event-6')
        self.assertEqual(e['quote_state'],{})
        self.assertEqual(e['exit_quote_state']['60'],'SYNTHETIC_REPLAY_QUOTE')
        self.assertEqual(e['exit_quote_state']['300'],'NO_QUOTE')
        self.assertEqual(len([t for t in r['audit_trace'] if t['kind']=='exit_quote_replay']),1)
        self.assertEqual(r['quoted_actual_count'],0)

    def test_sell_exit_quote_error_and_null(self):
        for value in (None,'0'):
            with self.subTest(value=value):
                f=self._sell_fixture()
                q=next(x for x in f['records'] if x['kind']=='quote' and x['event_id']=='event-6')
                q['synthetic_amount_out_raw']=value
                r=replay_fixture(f)
                self.assertEqual(event(r,'event-6')['exit_quote_state']['60'],'NO_QUOTE')

    def test_sell_exit_e1_failure_and_reorg(self):
        r=replay_fixture(self._sell_fixture(fail=True))
        self.assertEqual(set(event(r,'event-6')['exit_quote_state'].values()),{'REJECTED'})
        r=replay_fixture(self._sell_fixture(reorg=True))
        self.assertEqual(event(r,'event-6')['state'],'INVALIDATED')
        self.assertEqual(set(event(r,'event-6')['exit_quote_state'].values()),{'REJECTED'})
        self.assertEqual(len([t for t in r['audit_trace'] if t['kind']=='exit_quote_replay']),1)

    def test_sell_exit_control_scheduler_symmetry(self):
        r=replay_fixture(self._sell_fixture(group='CONTROL_RANDOM'))
        self.assertEqual(event(r,'event-6')['exit_quote_state']['60'],'SYNTHETIC_REPLAY_QUOTE')
        self.assertEqual(len([t for t in r['audit_trace'] if t['kind']=='exit_quote_request_scheduled']),3)

    def test_only_trial_synthetic_fixture_allowed(self):
        f = clone_fixture()
        f['mode'] = 'LIVE'
        with self.assertRaisesRegex(ValueError,'Only schema-labeled'):
            replay_fixture(f)
        f = clone_fixture()
        f['records'][0]['trial'] = False
        with self.assertRaisesRegex(ValueError,'trial=true'):
            replay_fixture(f)

    def test_replay_output_deterministic(self):
        a = replay_fixture(clone_fixture())
        b = replay_fixture(clone_fixture())
        self.assertEqual(json.dumps(a,sort_keys=True),json.dumps(b,sort_keys=True))


if __name__ == '__main__':
    unittest.main()
