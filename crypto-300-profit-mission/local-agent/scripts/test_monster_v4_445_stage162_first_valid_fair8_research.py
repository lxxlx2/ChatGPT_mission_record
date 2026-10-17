#!/usr/bin/env python3
"""Actual SQLite fairness-selection checks, not evidence of profitable trading."""
import tempfile
import unittest
from pathlib import Path

import monster_v4_shadow as prod
import monster_v4_445_stage162_first_valid_fair8_research as fair


class Stage162ResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store=prod.open_store(Path(self.tmp.name)/"stage162.sqlite")
        self.addCleanup(self.store.close)
        self.t=1770338160000
        self.observer=fair.FairEightObserver()

    def add(self, symbol, first_seen, last_eval=None, retry=0, deadline=None):
        with self.store:
            cursor=self.store.execute("""
                INSERT INTO candidate_queue(
                    venue,symbol,first_seen_ms,last_seen_ms,priority,reason,
                    status,attempts,retry_after_ms,deadline_ms,last_evaluated_bar_ms
                ) VALUES ('spot',?,?,?,99,'TEST','PENDING',0,?,?,?)
            """,(symbol,first_seen,first_seen,retry,
                 first_seen+900000 if deadline is None else deadline,last_eval))
        return cursor.lastrowid

    def original_once(self,store,now,fetch,source_db,*,limit,original_queue,stats):
        rows=store.execute("""
            SELECT id,first_seen_ms FROM candidate_queue WHERE status='PENDING'
            AND retry_after_ms<=? ORDER BY first_seen_ms,id LIMIT ?
        """,(now,limit)).fetchall()
        with store:
            for row in rows:
                store.execute("""
                    UPDATE candidate_queue SET retry_after_ms=?,
                      last_error='NO_SETUP_YET'
                    WHERE id=?
                """,(now+60000,row["id"]))
        return {"selected":len(rows),"deferred":len(rows),
                "completed":0,"late":0}

    def invoke(self,now):
        return self.observer.instrument(self.store,now,None,None,
                    limit=8,original_queue=None,stats={})

    def test_01_qualifying_first_valid_candidates_precede_old_evaluated(self):
        old=self.add("OLDUSDT",self.t-3*60000,last_eval=self.t-5*60000)
        fresh=[self.add(f"X{i}USDT",self.t) for i in range(9)]
        self.observer.real_original_handler=self.original_once
        result=self.invoke(self.t+6*60000)
        self.assertEqual(result["selected"],8)
        self.assertEqual({q["id"] for q in self.observer.slots},set(fresh[:8]))
        self.assertNotIn(old,self.observer.first_selected)
        self.assertNotIn(fresh[8],self.observer.first_selected)
        self.assertEqual(self.store.execute("""
            SELECT retry_after_ms FROM candidate_queue WHERE id=?
        """,(old,)).fetchone()[0],0)
        self.assertEqual(self.observer.busy_ticks[0]["first_mature_fair_priority"],8)

    def test_02_before_postwatch_bar_close_same_oldest_FIFO(self):
        old=self.add("OLDUSDT",self.t-3*60000,last_eval=self.t-5*60000)
        fresh=[self.add(f"X{i}USDT",self.t) for i in range(9)]
        eligible=[dict(r) for r in self.store.execute(
            "SELECT * FROM candidate_queue ORDER BY first_seen_ms,id")]
        early=fair.plan_eligible_eight(eligible,self.t+3*60000)
        self.assertEqual([q["id"] for q in early],[old]+fresh[:7])
        later=fair.plan_eligible_eight(eligible,self.t+6*60000)
        self.assertEqual([q["id"] for q in later],fresh[:8])
        self.assertFalse(fair.first_valid_post_watch_closed_bar(self.t+3*60000,self.t))
        self.assertTrue(fair.first_valid_post_watch_closed_bar(self.t+6*60000,self.t))

    def test_03_expired_must_not_be_priority_eligible_first_valid(self):
        old=self.add("EXPIRED",self.t-12*60000,deadline=self.t)
        new=self.add("NEW",self.t)
        eligible=[dict(r) for r in self.store.execute(
            "SELECT * FROM candidate_queue ORDER BY first_seen_ms,id")]
        planned=fair.plan_eligible_eight(eligible,self.t+6*60000)
        self.assertEqual([q["id"] for q in planned],[new,old])

    def test_04_eight_slot_upper_bound_fails_closed(self):
        self.add("M1",self.t)
        xs=[dict(r) for r in self.store.execute(
            "SELECT * FROM candidate_queue")]
        with self.assertRaisesRegex(ValueError,"CAPACITY_CHANGED"):
            fair.plan_eligible_eight(xs,self.t+6*60000,capacity=9)
        xs[0]["retry_after_ms"]=self.t+99*60000
        with self.assertRaisesRegex(ValueError,"NOT_A_REAL_NOW_ELIGIBLE"):
            fair.plan_eligible_eight(xs,self.t)

    def test_05_exception_restores_all_masked_nonselected_rows(self):
        old=self.add("OLDUSDT",self.t-3*60000,last_eval=self.t-5*60000)
        for i in range(9):
            self.add(f"X{i}USDT",self.t)
        before=[dict(q) for q in self.store.execute("SELECT * FROM candidate_queue")]
        def fail(*args,**kwargs):
            raise RuntimeError("synthetic handler failed")
        self.observer.real_original_handler=fail
        with self.assertRaisesRegex(RuntimeError,"synthetic handler failed"):
            self.invoke(self.t+6*60000)
        after=[dict(q) for q in self.store.execute("SELECT * FROM candidate_queue")]
        self.assertEqual(before,after)
        self.assertEqual(self.observer.selected_total,0)

    def test_06_nonselected_mutation_does_not_get_attributed_to_selected(self):
        old=self.add("OLDUSDT",self.t-3*60000,last_eval=self.t-5*60000)
        for i in range(9):
            self.add(f"X{i}USDT",self.t)
        def original(store,now,fetch,source_db,*,limit,original_queue,stats):
            normal=self.original_once(store,now,fetch,source_db,limit=limit,
                                       original_queue=original_queue,stats=stats)
            with store:
                store.execute("""
                    UPDATE candidate_queue SET last_error='UNAUTHORIZED' WHERE id=?
                """,(old,))
            return normal
        self.observer.real_original_handler=original
        with self.assertRaisesRegex(RuntimeError,"NONSELECTED_DURABLE_ROW_MUTATED"):
            self.invoke(self.t+6*60000)

    def test_07_repeats_and_first_valid_bar_are_observed_not_inferred(self):
        for i in range(8):
            self.add(f"X{i}USDT",self.t)
        def original(store,now,fetch,source_db,*,limit,original_queue,stats):
            rows=store.execute("""
                SELECT id FROM candidate_queue WHERE status='PENDING'
                AND retry_after_ms<=? ORDER BY first_seen_ms,id LIMIT ?
            """,(now,limit)).fetchall()
            with store:
                for q in rows:
                    store.execute("""
                        UPDATE candidate_queue SET retry_after_ms=?,
                            last_evaluated_bar_ms=?
                        WHERE id=?
                    """,(now+60000,now-5*60000,q["id"]))
            return {"selected":len(rows),"deferred":len(rows),
                    "completed":0,"late":0}
        self.observer.real_original_handler=original
        self.invoke(self.t+6*60000)
        self.invoke(self.t+9*60000)
        self.assertEqual(len(self.observer.first_evaluated),8)
        self.assertEqual(self.observer.selected_total,16)
        self.assertEqual(self.observer.repeats_advanced,8)
        self.assertEqual(self.observer.repeats_no_progress,0)


if __name__=="__main__":
    unittest.main()
