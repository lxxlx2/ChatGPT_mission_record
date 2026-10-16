#!/usr/bin/env python3
"""Independent-review follow-up: real production defer semantics and LATE origins."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import monster_v4_shadow as production
import monster_v4_shared_445_burst_audit as audit


class ClaudeFollowupTests(unittest.TestCase):
    def setUp(self):
        self.now = 1770338160000
        self.row = {
            "venue": "spot", "symbol": "TESTUSDT", "id": 42,
            "first_seen_ms": self.now, "deadline_ms": self.now+900000
        }
        self.event = {
            "venue": "spot", "symbol": "TESTUSDT",
            "observed_ms": self.now+1080000
        }

    def test_deadline_path_from_production_payload(self):
        event = dict(self.event, payload=json.dumps({
            "classification": "STALE_NOT_ACTIONABLE",
            "first_seen_ms": self.now,
            "deadline_ms": self.now+900000
        }))
        self.assertEqual(
            audit.classify_late_production_path(event, self.row),
            "D1_PROCESS_QUEUE_DEADLINE_EXPIRED")

    def test_overdue_on_rearmed_watch_is_distinct(self):
        event = dict(self.event, payload=json.dumps({
            "classification": "STALE_NOT_ACTIONABLE",
            "reason": "OVERDUE_WHEN_REARMING_WATCH"
        }))
        self.assertEqual(
            audit.classify_late_production_path(event, self.row),
            "WATCH_REARM_OVERDUE_PRIOR_CANDIDATE")

    def test_unknown_or_spoofed_late_origin_fails_closed(self):
        payloads=[
            {"classification":"STALE_NOT_ACTIONABLE","reason":"OTHER_REASON"},
            {"classification":"STALE_NOT_ACTIONABLE",
             "reason":"OVERDUE_WHEN_REARMING_WATCH",
             "deadline_ms":self.now+900000},
            {"classification":"STALE_NOT_ACTIONABLE",
             "first_seen_ms":self.now+1,"deadline_ms":self.now+900000},
            {"classification":"STALE_NOT_ACTIONABLE",
             "first_seen_ms":self.now,"deadline_ms":self.now+1},
        ]
        for data in payloads:
            with self.subTest(data=data),self.assertRaisesRegex(
                    ValueError, "MONSTER445_LATE_"):
                audit.classify_late_production_path(
                    dict(self.event,payload=json.dumps(data)),self.row)

    def test_late_not_premature(self):
        e=dict(self.event,observed_ms=self.now+899999,payload=json.dumps({
            "classification":"STALE_NOT_ACTIONABLE",
            "first_seen_ms":self.now,"deadline_ms":self.now+900000
        }))
        with self.assertRaisesRegex(ValueError,"PAYLOAD_OR_DEADLINE_DRIFT"):
            audit.classify_late_production_path(e,self.row)

    def test_real_production_zero_quote_is_deferred_then_late_not_unsupported(self):
        with tempfile.TemporaryDirectory() as root:
            db=production.open_store(Path(root)/"shadow.sqlite")
            now=self.now
            db.execute("""INSERT INTO candidate_queue
                (venue,symbol,first_seen_ms,last_seen_ms,priority,reason,
                 status,attempts,retry_after_ms,deadline_ms)
                VALUES ('spot','TESTUSDT',?,?,?,?, 'PENDING',0,0,?)""",
                (now,now,10,"FROZEN_TEST",now+900000))
            db.commit()
            interval=300000
            bars=[]
            for i in range(8):
                opened=now-(8-i)*interval
                bars.append([opened,"1","1.1","0.9","1.05",
                             "1",opened+interval-1,"100"])
            bars[0][7]="0"  # legitimate no trade in earliest supplied 5m
            first=production.process_queue(
                db,now,lambda venue,symbol,t:bars,limit=8)
            row=db.execute("SELECT * FROM candidate_queue").fetchone()
            self.assertEqual(first["deferred"],1)
            self.assertEqual(row["status"],"PENDING")
            self.assertEqual(row["attempts"],1)
            self.assertIn("INVALID_CLOSED_QUOTE",row["last_error"])
            self.assertNotEqual(row["status"],"SOURCE_UNSUPPORTED_D1_ZERO_QUOTE")
            after=production.process_queue(
                db,now+1080000,lambda *_:bars,limit=8)
            row=db.execute("SELECT * FROM candidate_queue").fetchone()
            self.assertEqual(after["late"],1)
            self.assertEqual(row["status"],"LATE")
            late=db.execute(
                "SELECT * FROM events WHERE event_type='LATE_REVIEW'").fetchone()
            self.assertEqual(late["event_id"],
                production.event_key("spot","TESTUSDT","LATE_REVIEW",row["id"]))
            self.assertEqual(
                audit.classify_late_production_path(dict(late),dict(row)),
                "D1_PROCESS_QUEUE_DEADLINE_EXPIRED")
            db.close()

    def test_historical_data_not_asserted_as_live_production_from_flags(self):
        source=Path(audit.__file__).read_text(encoding="utf-8")
        for forbidden in (
            '"D1_market_zero_quote_is_real_no_trade_not_missing_data": True',
            '"D1_original_validates_positive_quote_for_all_8_supplied_candles":'
        ):
            self.assertNotIn(forbidden,source)


if __name__=="__main__":
    unittest.main()
