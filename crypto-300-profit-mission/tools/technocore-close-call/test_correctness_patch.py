from decimal import Decimal
import unittest

import close_call_fleet as c


class CorrectnessPatchTests(unittest.TestCase):
    def test_room_seen_honors_unlisted_and_relist(self):
        original = c.parse_export
        try:
            rows = [
                {"_payload": {"t": "flow", "n": 10, "rooms": ["cc-test"]}},
                {"_payload": {"t": "flow", "n": 20, "unlisted": ["cc-test"]}},
            ]
            c.parse_export = lambda room: rows if room == "d-close1-flow" else []
            self.assertFalse(c.room_seen("cc-test"))

            rows.append({"_payload": {"t": "flow", "n": 21, "rooms": ["cc-test"]}})
            self.assertTrue(c.room_seen("cc-test"))
        finally:
            c.parse_export = original

    def test_v5a_snapshot_uses_price_ref_and_blocks_explicit_void(self):
        pair = {
            "pair_id": "test-pair",
            "cohort_sweep": 10,
            "copy_no": 1,
            "long": "L",
            "short": "S",
            "qty": Decimal("1"),
            "low": Decimal("95"),
            "high": Decimal("105"),
            "long_trade_id": "long-id",
            "short_trade_id": "short-id",
        }
        refs = {11: Decimal("100")}
        marks = {11: Decimal("999")}

        snap = c._v5a_pair_snapshot(
            {}, pair, refs, marks, set(),
            {"long-id": "settled", "short-id": "settled"},
            Decimal("110"),
        )
        self.assertIsNotNone(snap)
        self.assertEqual(snap["settlement_close"], Decimal("100"))

        omitted_style_unknown = c._v5a_pair_snapshot(
            {}, pair, refs, marks, set(),
            {"long-id": "settled"},
            Decimal("110"),
        )
        self.assertIsNotNone(omitted_style_unknown)
        self.assertEqual(omitted_style_unknown["settlement_close"], Decimal("100"))

        explicit_void = c._v5a_pair_snapshot(
            {}, pair, refs, marks, set(),
            {"long-id": "settled", "short-id": "void"},
            Decimal("110"),
        )
        self.assertIsNone(explicit_void)

    def test_room_seen_uses_exact_names_not_substrings(self):
        original = c.parse_export
        try:
            rows = [
                {"_payload": {"t": "flow", "n": 10, "rooms": ["cc-test-extra"]}},
            ]
            c.parse_export = lambda room: rows if room == "d-close1-flow" else []
            self.assertFalse(c.room_seen("cc-test"))
        finally:
            c.parse_export = original

    def test_compact_void_nested_array_is_detected(self):
        self.assertTrue(c.contains_value([["trade-123", "funds"]], "trade-123"))
        self.assertFalse(c.contains_value([["trade-999", "funds"]], "trade-123"))

    def test_v5b_stop_retains_seed_cushion(self):
        self.assertEqual(c._v5b_stop_score(Decimal("58.95")), Decimal("50.1075"))
        self.assertEqual(c._v5b_stop_score(Decimal("10")), Decimal("20"))

    def test_review_gates_pause_new_v5_work(self):
        self.assertTrue(c.V5A_REVIEW_PAUSE_NEW)
        self.assertTrue(c.V5B_REVIEW_PAUSE_NEW)

    def test_dense_registration_waits_for_room(self):
        originals = (
            c.add_dynamic_key,
            c.room_registration_confirmed,
            c.post_signed,
            c.save_state,
        )
        posted = []
        state = {"keys": {}, "dense": {}, "room": "cc-test"}

        def add_key(st, label):
            st["keys"].setdefault(label, {"did": "did:key:" + label, "seed": "", "nonces": {}})
            return st["keys"][label]

        try:
            c.add_dynamic_key = add_key
            c.save_state = lambda state: None
            c.post_signed = lambda *args, **kwargs: posted.append(args) or "ok"
            c.room_registration_confirmed = lambda state: False

            pending = c.dense_register_pending(state, 100)
            self.assertEqual(pending["status"], "waiting_room")
            self.assertEqual(posted, [])

            c.room_registration_confirmed = lambda state: True
            pending = c.dense_register_pending(state, 101)
            self.assertEqual(pending["status"], "registered")
            self.assertEqual(len(posted), 3)
        finally:
            (
                c.add_dynamic_key,
                c.room_registration_confirmed,
                c.post_signed,
                c.save_state,
            ) = originals

    def test_trade_ids_are_deterministic_and_short(self):
        a = c.deterministic_trade_id("v4l", 123, 456, 7)
        b = c.deterministic_trade_id("v4l", 123, 456, 7)
        other = c.deterministic_trade_id("v4l", 123, 456, 8)
        self.assertEqual(a, b)
        self.assertNotEqual(a, other)
        self.assertLessEqual(len(a), 64)

    def test_v5b_allow_new_false_does_not_create_cycle(self):
        original_save = c.save_state
        original_register = c._v5b_register_pending
        state = {"dense": {"v5b_enabled": True, "v4_enabled": True}}
        called = {"register": False}

        try:
            c.save_state = lambda state: None

            def fail_register(*args, **kwargs):
                called["register"] = True
                raise AssertionError("new V5b registration should be gated")

            c._v5b_register_pending = fail_register
            result = c.dense_v5b_step(state, {"n": 123}, allow_new=False)
            self.assertIsNone(result)
            self.assertFalse(called["register"])
        finally:
            c.save_state = original_save
            c._v5b_register_pending = original_register


if __name__ == "__main__":
    unittest.main()
