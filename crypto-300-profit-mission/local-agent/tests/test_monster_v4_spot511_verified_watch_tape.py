"""Replay-anchored real 53 original WATCH IDs, no HTTP or SQLite mutating I/O."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import monster_v4_shadow as original
import monster_v4_spot511_verified_watch_tape as watch_module

from monster_v4_spot511_verified_watch_tape import (
    PINNED_PAIRED_REPORT_SHA256, PINNED_WATCH_CANONICAL_SHA256,
    SourceIdentityError, load_pinned_original_watch_tape,
    verify_original_watch_inventory, watches_at_tick,
)

EVIDENCE = (
    Path(__file__).resolve().parents[2] / "monster" / "evidence"
    / "MONSTER_SPOT511_4088_REAL_ORIGINAL_CORE_53_WATCH_IDENTITIES_20261025.json"
)


class VerifiedOriginalWatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(EVIDENCE.read_text())
        cls.entries = cls.source["real_original_core_watch_identity_rows"]

    def source_fixture(self):
        events = [
            {"venue":"spot", "symbol":e["symbol"],"event_type":"WATCH_EARLY",
             "observed_ms":e["observed_ms"],"event_id":e["event_id"],
             "details":{"classification":"RESEARCH_WATCH_NOT_BUY",
                        "venue":"spot","observed_ms":e["observed_ms"]}}
            for e in self.entries
        ]
        return {
            "mode":"OFFLINE_HISTORICAL_RESEARCH", "frozen_roster":511, "ticks":3360,
            "verified_full_publisher_symbol_days":4088,
            "full_d0_ticks":2919, "censored_d0_ticks":441,
            "d0_watch_count":53, "same_d0_watch_id_and_time":True, "G6":"NO_GO",
            "fifo_watch_events":events, "fair8_watch_events":deepcopy(events),
        }

    def test_all_53_real_event_identifiers_match_fixed_original_watch_sha(self):
        actual=verify_original_watch_inventory(self.source_fixture())
        self.assertEqual(len(actual),53)
        self.assertEqual(len(set(s for s,_,_ in actual)),39)
        self.assertEqual(len(set(event_id for _,_,event_id in actual)),53)
        self.assertEqual(PINNED_WATCH_CANONICAL_SHA256,
                         self.source["canonical_watch_event_inventory_sha256"])
        self.assertEqual(PINNED_PAIRED_REPORT_SHA256,
                         self.source["provenance"]["original_paired_json_sha256"])

    def test_hash_only_is_not_proof_of_original_artifact(self):
        # Even the exact 53 event identities do NOT make a substituted JSON
        # acceptable. The full exact original report SHA is mandatory.
        with tempfile.TemporaryDirectory() as folder:
            fake=Path(folder)/"paired-4088.json"
            fake.write_text(json.dumps(self.source_fixture()))
            with self.assertRaisesRegex(SourceIdentityError,"SHA_MISMATCH"):
                load_pinned_original_watch_tape(fake)

    def test_wrong_event_id_rejected_in_actual_53(self):
        p=self.source_fixture()
        p["fifo_watch_events"][0]["event_id"]="0"*64
        p["fair8_watch_events"]=deepcopy(p["fifo_watch_events"])
        with self.assertRaisesRegex(SourceIdentityError,"HASH_MISMATCH"):
            verify_original_watch_inventory(p)

    def test_event_content_lanes_must_match(self):
        p=self.source_fixture()
        p["fair8_watch_events"][0]["details"]["classification"]="BUY"
        with self.assertRaisesRegex(SourceIdentityError,"LANE_DISAGREEMENT"):
            verify_original_watch_inventory(p)

    def test_reconstructed_watches_cannot_relabel_source_as_full(self):
        p=self.source_fixture()
        p["verified_full_publisher_symbol_days"]=4599
        with self.assertRaisesRegex(SourceIdentityError,"CENSUS_OR_GATE_MISMATCH"):
            verify_original_watch_inventory(p)

    def test_original_closed_tick_grid_no_forged_time(self):
        p=self.source_fixture()
        p["fifo_watch_events"][1]["observed_ms"]+=1
        p["fair8_watch_events"]=deepcopy(p["fifo_watch_events"])
        with self.assertRaisesRegex(SourceIdentityError,"INVALID_ORIGINAL_WATCH_FIELDS"):
            verify_original_watch_inventory(p)

    def test_preserve_real_multiple_watches_same_symbol(self):
        rows=verify_original_watch_inventory(self.source_fixture())
        self.assertEqual(sum(symbol=="IOSTUSDT" for symbol,_,_ in rows),4)
        self.assertEqual(sum(symbol=="ERAUSDT" for symbol,_,_ in rows),3)

    def test_published_events_are_chronological_without_reordering(self):
        p=self.source_fixture()
        p["fifo_watch_events"][0],p["fifo_watch_events"][1]=(
            p["fifo_watch_events"][1],p["fifo_watch_events"][0])
        p["fair8_watch_events"]=deepcopy(p["fifo_watch_events"])
        with self.assertRaisesRegex(SourceIdentityError,"SORT_ORDER_DRIFT"):
            verify_original_watch_inventory(p)


    def marked_tape(self, rows=None):
        # The flags are intentionally ordinary, PUBLIC, attacker-settable fields.
        inventory=verify_original_watch_inventory(self.source_fixture())
        return {
            "schema":watch_module.SCHEMA,
            "original_paired_json_sha256":PINNED_PAIRED_REPORT_SHA256,
            "original_watch_ledger_integrity_checked":True,
            "watch_identity_rows":inventory if rows is None else rows,
        }

    def test_complete_forged_flags_with_repeated_fake_events_rejected(self):
        first=self.entries[0]
        ms=first["observed_ms"]
        fake_id=original.event_key("spot","FAKEUSDT","WATCH_EARLY",ms)
        forged=(("FAKEUSDT",ms,fake_id),)*53
        with self.assertRaisesRegex(SourceIdentityError,"DUPLICATE_EVENT_ID"):
            watches_at_tick(self.marked_tape(forged),ms)

    def test_same_length_one_rehashed_forged_event_rejected(self):
        rows=list(self.marked_tape()["watch_identity_rows"])
        symbol,ms,_=rows[0]
        rows[0]=("FAKEUSDT",ms,original.event_key("spot","FAKEUSDT","WATCH_EARLY",ms))
        with self.assertRaisesRegex(SourceIdentityError,"CANONICAL_SHA_MISMATCH"):
            watches_at_tick(self.marked_tape(tuple(rows)),ms)

    def test_repeated_original_id_rejected_even_if_length_53(self):
        rows=list(self.marked_tape()["watch_identity_rows"])
        rows[1]=rows[0]
        with self.assertRaisesRegex(SourceIdentityError,"DUPLICATE_EVENT_ID"):
            watches_at_tick(self.marked_tape(tuple(rows)),rows[0][1])

    def test_event_reordering_rejected_even_if_all_ids_valid(self):
        rows=list(self.marked_tape()["watch_identity_rows"])
        rows[0],rows[1]=rows[1],rows[0]
        with self.assertRaisesRegex(SourceIdentityError,"EVENT_ORDER_DRIFT"):
            watches_at_tick(self.marked_tape(tuple(rows)),rows[0][1])

    def test_shift_to_another_valid_tick_and_rehash_still_rejected(self):
        rows=list(self.marked_tape()["watch_identity_rows"])
        symbol,ms,_=rows[0]
        tick=ms-180_000
        rows[0]=(symbol,tick,original.event_key("spot",symbol,"WATCH_EARLY",tick))
        with self.assertRaisesRegex(SourceIdentityError,"CANONICAL_SHA_MISMATCH"):
            watches_at_tick(self.marked_tape(tuple(rows)),tick)

    def test_non_tuple_row_and_non_integer_tick_rejected(self):
        original_rows=self.marked_tape()["watch_identity_rows"]
        rows=list(original_rows)
        rows[0]=list(rows[0])
        with self.assertRaisesRegex(SourceIdentityError,"ROW_SHAPE_DRIFT"):
            watches_at_tick(self.marked_tape(tuple(rows)),original_rows[0][1])
        rows=list(original_rows)
        symbol,ms,eid=rows[0]
        rows[0]=(symbol,float(ms),eid)
        with self.assertRaisesRegex(SourceIdentityError,"ROW_INVALID"):
            watches_at_tick(self.marked_tape(tuple(rows)),ms)

    def test_real_pinned_identity_inventory_emits_exact_original_at_each_tick(self):
        rows=self.marked_tape()["watch_identity_rows"]
        selected=[]
        for tick in sorted({ms for _,ms,_ in rows}):
            selected.extend(watches_at_tick(self.marked_tape(),tick))
        self.assertEqual(len(selected),53)
        self.assertEqual({r["event_id"] for r in selected},{e[2] for e in rows})
        self.assertEqual(len(set(e["symbol"] for e in selected)),39)

    def test_loader_return_mutation_refused_even_with_true_flags(self):
        # An isolated fixture substitutes the paired-report SHA ONLY inside
        # this test. Production accepts ONLY the original fixed byte SHA.
        payload=json.dumps(self.source_fixture(),sort_keys=True).encode()
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"paired-4088-fixture.json"
            p.write_bytes(payload)
            synthetic_sha=hashlib.sha256(payload).hexdigest()
            with mock.patch.object(watch_module,"PINNED_PAIRED_REPORT_SHA256",synthetic_sha):
                verified=load_pinned_original_watch_tape(p)
                self.assertEqual(verified["watch_count"],53)
                original_rows=verified["watch_identity_rows"]
                self.assertTrue(watches_at_tick(verified,original_rows[0][1]))
                changed=list(original_rows)
                symbol,ms,_=changed[0]
                changed[0]=("FAKEUSDT",ms,original.event_key("spot","FAKEUSDT","WATCH_EARLY",ms))
                verified["watch_identity_rows"]=tuple(changed)
                with self.assertRaisesRegex(SourceIdentityError,"CANONICAL_SHA_MISMATCH"):
                    watches_at_tick(verified,ms)

    def test_unverified_tape_cannot_pretend_to_be_original(self):
        p=self.source_fixture()
        rows=verify_original_watch_inventory(p)
        fake={"schema":"MONSTER_SPOT511_4088_ORIGINAL_CORE_WATCH_ADMISSION_V1",
              "original_paired_json_sha256":PINNED_PAIRED_REPORT_SHA256,
              "watch_identity_rows":rows}
        with self.assertRaisesRegex(SourceIdentityError,"WATCH_TICK_OR_PROVENANCE_REQUIRED"):
            watches_at_tick(fake,rows[0][1])


if __name__ == "__main__":
    unittest.main()
