"""Offline negative cases; no publisher HTTP and no notifications."""
from copy import deepcopy
import unittest
from mission_agent.early.spot_d1_event_audit import audit_recomputed_d1, EventAuditError


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.base={'same_d0_watch_id_and_time': True, 'd0_watch_count': 2,
            'fifo_setups': 1, 'fair8_setups': 1,
            'new_setup_ids': [], 'lost_setup_ids': [], 'shared_setup_time_changed_ids': [],
            'fifo_episodes': [
                {'id':1,'venue':'spot','symbol':'AUSDT','first_seen_ms':180000000,
                 'deadline_ms':180900000,'first_valid_eval_ms':180180000,'status':'EVALUATED'},
                {'id':2,'venue':'spot','symbol':'BUSDT','first_seen_ms':181800000,
                 'deadline_ms':182700000,'first_valid_eval_ms':None,'status':'LATE'}]}
        self.base['fair8_episodes']=deepcopy(self.base['fifo_episodes'])
        self.independent={'derived':{'setup_rows':[[1,'AUSDT',180180000],[2,'BUSDT',None]],
            'recomputed_setups':1,'raw_setups_by_complete_utc_day':{'1970-01-03':1},
            'evaluated_but_no_setup_queue_ids':[],'late_queue_ids':[2]}}

    def test_valid_and_explicit_reconstructed_not_original(self):
        result=audit_recomputed_d1(self.base,self.independent)
        self.assertEqual(result['recomputed_setup_count'],1)
        self.assertFalse(result['original_sqlite_event_ids_readback'])
        self.assertEqual(result['historical_live_PIT'],'UNPROVEN')

    def test_wrong_id_rejected(self):
        x=deepcopy(self.independent);x['derived']['setup_rows'][0][0]=3
        with self.assertRaises(EventAuditError):audit_recomputed_d1(self.base,x)

    def test_wrong_symbol_rejected(self):
        x=deepcopy(self.independent);x['derived']['setup_rows'][0][1]='CUSDT'
        with self.assertRaises(EventAuditError):audit_recomputed_d1(self.base,x)

    def test_future_after_deadline_rejected(self):
        x=deepcopy(self.independent);x['derived']['setup_rows'][0][2]=181080000
        with self.assertRaises(EventAuditError):audit_recomputed_d1(self.base,x)

    def test_late_cannot_become_setup(self):
        x=deepcopy(self.independent);x['derived']['setup_rows'][1][2]=181980000
        with self.assertRaises(EventAuditError):audit_recomputed_d1(self.base,x)

    def test_fifo_fair_status_drift_rejected(self):
        x=deepcopy(self.base);x['fair8_episodes'][1]['status']='EVALUATED'
        with self.assertRaises(EventAuditError):audit_recomputed_d1(x,self.independent,require_equal_lanes=True)

    def test_fair8_divergence_does_not_block_fifo_only_audit(self):
        x=deepcopy(self.base);x['fair8_episodes'][1]['status']='EVALUATED'
        result=audit_recomputed_d1(x,self.independent)
        self.assertEqual(result['recomputed_setup_count'],1)
        self.assertFalse(result['fair8_outcomes_independently_recomputed'])

    def test_right_censored_pending_is_not_mislabeled_as_failure(self):
        x=deepcopy(self.base)
        x['fifo_episodes'][1]['status']='PENDING'
        x['fair8_episodes'][1]['status']='PENDING'
        y=deepcopy(self.independent)
        y['derived']['late_queue_ids']=[]
        y['derived']['unresolved_pending_queue_ids']=[2]
        result=audit_recomputed_d1(x,y)
        self.assertEqual(result['unresolved_pending_ids'],[2])
        self.assertEqual(result['nonsetup_evaluated_ids'],[])

    def test_right_censored_pending_requires_explicit_census(self):
        x=deepcopy(self.base)
        x['fifo_episodes'][1]['status']='PENDING'
        x['fair8_episodes'][1]['status']='PENDING'
        y=deepcopy(self.independent);y['derived']['late_queue_ids']=[]
        with self.assertRaises(EventAuditError):audit_recomputed_d1(x,y)

    def test_false_day_summary_rejected(self):
        x=deepcopy(self.independent);x['derived']['raw_setups_by_complete_utc_day']={'1970-01-04':1}
        with self.assertRaises(EventAuditError):audit_recomputed_d1(self.base,x)

    def test_wrong_setups_rejected(self):
        x=deepcopy(self.base);x['fifo_setups']=2
        with self.assertRaises(EventAuditError):audit_recomputed_d1(x,self.independent)


if __name__=='__main__': unittest.main()
