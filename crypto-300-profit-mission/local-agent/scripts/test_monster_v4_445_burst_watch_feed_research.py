#!/usr/bin/env python3
"""No-lookahead market WATCH grouping tests; synthetic fixtures never claim historical results."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

import monster_v4_445_burst_watch_feed_research as study


def build_synthetic():
    base=1770200000000
    events=[]
    queue=[]
    for i in range(269):
        sym=f"SYN{i:03d}USDT"
        t=base if i<9 else base+(i-7)*180000
        payload={
            "classification":"RESEARCH_WATCH_NOT_BUY",
            "execution_verified":False,"observed_ms":t,"venue":"spot",
            "quote24_usdt":str(10000+i),
            "trigger_3m_5pct":True,"trigger_15m_8pct":False,
            "trigger_60m_15pct":False,"return_snapshot_pct":6.1,
        }
        events.append({
            "event_type":"WATCH_EARLY","event_id":study.event_hash("spot",sym,"WATCH_EARLY",t),
            "venue":"spot","symbol":sym,"observed_ms":t,
            "payload":json.dumps(payload)
        })
        queue.append({
            "id":i+1,"venue":"spot","symbol":sym,
            "first_seen_ms":t,"deadline_ms":t+900000,
            "status":"EVALUATED",
        })
    return {
        "actually_complete_symbols":445,
        "one_shared_sqlite_for_all_symbols":True,
        "not_independent_OOS":True,
        "not_real_PIT_listing":True,
        "execution_counts":{"polls":3360},
        "D1_model_semantics":"RESEARCH_V2_SOURCE_UNSUPPORTED_ZEROQUOTE",
        "all445_original_production_D1_completed":False,
        "G6":"NO_GO",
        "events":events,"queue_rows":queue,
    }


def read_study(fake):
    raw=json.dumps(fake,sort_keys=True).encode()
    digest=hashlib.sha256(raw).hexdigest()
    with patch.object(study,"SOURCE_SHA",digest):
        return study.project(raw,{"full_replay_json_sha256":digest})


class WatchBurstResearchTests(unittest.TestCase):
    def test_grouping_from_existing_eight_slot_capacity_preserves_all_269(self):
        result=read_study(build_synthetic())
        view=result["point_in_time_display_preview"]
        self.assertEqual(view["total_WATCH"],269)
        self.assertEqual(view["market_burst_cards"],1)
        self.assertEqual(view["burst_member_WATCH"],9)
        self.assertEqual(view["hypothetical_grouped_cards"],261)
        self.assertEqual(view["hypothetical_cards_reduced"],8)
        self.assertEqual(sum("all_watch_event_ids_preserved" in c for c in
                             view["cards_research_only_no_delivery"]),1)
        self.assertEqual(view["BUY"],"FORBIDDEN")

    def test_future_queue_outcomes_cannot_modify_at_watch_preview(self):
        full=build_synthetic()
        early=read_study(full)
        changed=copy.deepcopy(full)
        for i,q in enumerate(changed["queue_rows"]):
            q["status"]="LATE" if i%2 else "INVALIDATED"
        after=read_study(changed)
        self.assertEqual(early["point_in_time_display_preview"],
                         after["point_in_time_display_preview"])
        self.assertNotEqual(early["hindsight_diagnostic_not_for_live_display"],
                            after["hindsight_diagnostic_not_for_live_display"])
        for row in after["point_in_time_display_preview"]["at_WATCH_visible_rows_all_preserved"]:
            self.assertNotIn("status",row)
            self.assertNotIn("last_error",row)
            self.assertNotIn("profit",row)

    def test_invalid_watches_do_not_become_display_cards(self):
        x=build_synthetic()
        broken=copy.deepcopy(x)
        broken["events"][0]["event_id"]="fake"
        with self.assertRaisesRegex(ValueError,"SOURCE_IDENTITY_DRIFT"):
            read_study(broken)
        broken=copy.deepcopy(x)
        p=json.loads(broken["events"][0]["payload"])
        p["quote24_usdt"]="-1"
        broken["events"][0]["payload"]=json.dumps(p)
        with self.assertRaisesRegex(ValueError,"QUOTE_PROXY_INVALID"):
            read_study(broken)

    def test_sha_pin_rejects_even_valid_synthetic_data_without_explicit_patch(self):
        x=build_synthetic()
        raw=json.dumps(x).encode()
        with self.assertRaisesRegex(ValueError,"IMMUTABLE_SOURCE_SHA_MISMATCH"):
            study.project(raw,{"full_replay_json_sha256":hashlib.sha256(raw).hexdigest()})


if __name__=="__main__":
    unittest.main()
