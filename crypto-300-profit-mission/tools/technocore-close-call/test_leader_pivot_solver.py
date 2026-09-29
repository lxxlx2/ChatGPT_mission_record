from decimal import Decimal
import unittest
from unittest.mock import patch

import close_call_fleet as c


class LeaderPivotSolverTests(unittest.TestCase):
    def price_row(self, sweep="957", applied="230", close="229"):
        applied = Decimal(applied)
        return {
            "sweep": int(sweep),
            "applied": applied,
            "close": Decimal(close),
            "lower_limit": (applied * Decimal("0.95")).quantize(Decimal("0.01")),
            "upper_limit": (applied * Decimal("1.05")).quantize(Decimal("0.01")),
        }

    def test_buyer_fee_matches_base_or_clawback(self):
        qty = Decimal("10")
        self.assertEqual(
            c._leader_buyer_fee(qty, Decimal("230"), Decimal("231")),
            Decimal("23.00"),
        )
        self.assertEqual(
            c._leader_buyer_fee(qty, Decimal("210"), Decimal("230")),
            Decimal("200"),
        )

    def test_open_long_candidate_includes_fee_in_required_carry(self):
        row = self.price_row(applied="223.01", close="228.85")
        result = c._leader_open_long_candidate(
            row,
            target_score=Decimal("790.87"),
            target_mark=Decimal("228.85"),
            target_qty=Decimal("46.07"),
        )
        naive = (
            Decimal("790.87")
            - Decimal("46.07") * (Decimal("228.85") - row["lower_limit"])
        )
        self.assertGreater(result["locked_carry_required_before_open"], naive)
        self.assertGreater(result["buyer_fee"], Decimal("0"))

    def test_direct_flip_value_change_is_clawback_limited(self):
        row = self.price_row(applied="230", close="229")
        pre = {
            "score": Decimal("749.24"),
            "mark": Decimal("229.07"),
            "position": Decimal("-43.57"),
            "position_evidence": "consecutive_pnl_slope",
        }
        target = {
            "score": Decimal("790.87"),
            "mark": Decimal("228.85"),
            "position": Decimal("46.07"),
            "position_evidence": "published_position",
        }
        result = c._leader_direct_flip_candidate(row, pre, target)
        self.assertIsNotNone(result)
        self.assertEqual(result["buy_qty"], Decimal("89.64"))
        self.assertGreater(result["cash_required_before_flip"], Decimal("0"))
        self.assertEqual(result["pre_position_evidence"], "consecutive_pnl_slope")

    def test_two_step_requires_open_after_close(self):
        pre = {
            "score": Decimal("749.24"),
            "mark": Decimal("229.07"),
            "position": Decimal("-43.57"),
            "position_evidence": "consecutive_pnl_slope",
        }
        target = {
            "score": Decimal("790.87"),
            "mark": Decimal("228.85"),
            "position": Decimal("46.07"),
            "position_evidence": "published_position",
        }
        row = self.price_row(sweep="957")
        self.assertIsNone(
            c._leader_two_step_pivot_candidate(row, row, pre, target)
        )


    def test_subject_selection_falls_back_when_live_rank_changed(self):
        state = {"keys": {}}
        pnl_histories = {
            "did-a": [
                {"sweep": 959, "mark": Decimal("228"), "score": Decimal("700")},
                {"sweep": 960, "mark": Decimal("229"), "score": Decimal("740")},
            ],
            "did-b": [
                {"sweep": 960, "mark": Decimal("229"), "score": Decimal("790")},
            ],
        }
        pos_histories = {
            "did-a": {},
            "did-b": {960: Decimal("46.07")},
        }

        def fake_pnl_history(targets):
            return {did: pnl_histories[did] for did in targets}

        def fake_pos_history(targets):
            return {did: pos_histories[did] for did in targets}

        with patch.object(c, "latest_payload", return_value={"t": "pnl"}), \
             patch.object(
                 c,
                 "_pnl_pairs",
                 return_value=[
                     ("did-a", Decimal("1000")),
                     ("did-b", Decimal("999")),
                 ],
             ), \
             patch.object(c, "_leader_pnl_history", side_effect=fake_pnl_history), \
             patch.object(c, "_leader_position_history", side_effect=fake_pos_history):
            subject = c._leader_select_pivot_subject(
                state,
                rank=1,
                target_sweep=960,
            )

        self.assertEqual(subject["leader"]["did"], "did-b")
        self.assertEqual(
            subject["selection_mode"],
            "fallback_highest_current_rank_with_target_published_position",
        )
        self.assertEqual(
            subject["target"]["position_evidence"],
            "published_position",
        )

    def test_two_step_returns_observed_gap(self):
        pre = {
            "score": Decimal("749.24"),
            "mark": Decimal("229.07"),
            "position": Decimal("-43.57"),
            "position_evidence": "consecutive_pnl_slope",
        }
        target = {
            "score": Decimal("790.87"),
            "mark": Decimal("228.85"),
            "position": Decimal("46.07"),
            "position_evidence": "published_position",
        }
        close_row = self.price_row(sweep="957", applied="230", close="229")
        open_row = self.price_row(sweep="958", applied="229", close="228.80")
        result = c._leader_two_step_pivot_candidate(
            close_row, open_row, pre, target
        )
        self.assertIsNotNone(result)
        self.assertIn("observed_minus_modeled", result)
        self.assertGreaterEqual(result["absolute_gap"], Decimal("0"))
        self.assertEqual(result["close_sweep"], 957)
        self.assertEqual(result["open_sweep"], 958)


if __name__ == "__main__":
    unittest.main()
