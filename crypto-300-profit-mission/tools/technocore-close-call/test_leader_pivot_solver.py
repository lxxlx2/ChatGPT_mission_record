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

    def test_two_step_allows_ordered_same_sweep_and_rejects_open_earlier(self):
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
        close_row = self.price_row(sweep="957", applied="228.36", close="228.49")
        same = c._leader_two_step_pivot_candidate(
            close_row, close_row, pre, target
        )
        self.assertIsNotNone(same)
        self.assertTrue(same["same_sweep_ordered"])

        earlier = self.price_row(sweep="956", applied="228.20", close="228.30")
        self.assertIsNone(
            c._leader_two_step_pivot_candidate(close_row, earlier, pre, target)
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


    def test_direct_flip_can_be_ruled_out_by_pre_cash_upper_bound(self):
        row = self.price_row(applied="228.36", close="228.49")
        pre = {
            "score": Decimal("749.24"),
            "mark": Decimal("229.07"),
            "position": Decimal("-43.57142857142857"),
            "position_evidence": "consecutive_pnl_slope",
        }
        target = {
            "score": Decimal("790.87"),
            "mark": Decimal("228.85"),
            "position": Decimal("46.07"),
            "position_evidence": "published_position",
        }
        result = c._leader_direct_flip_candidate(
            row,
            pre,
            target,
            pre_cash_upper_bound=Decimal("2300"),
        )
        self.assertEqual(
            result["funds_feasibility"],
            "impossible_from_cash_upper_bound",
        )

    def test_two_step_reports_open_feasibility_and_implied_short_qty(self):
        pre = {
            "score": Decimal("749.24"),
            "mark": Decimal("229.07"),
            "position": Decimal("-43.57142857142857142857142857"),
            "position_evidence": "consecutive_pnl_slope",
        }
        target = {
            "score": Decimal("790.87"),
            "mark": Decimal("228.85"),
            "position": Decimal("46.07"),
            "position_evidence": "published_position",
        }
        close_row = self.price_row(sweep="959", applied="228.56", close="228.26")
        open_row = self.price_row(sweep="960", applied="228.26", close="228.76")
        result = c._leader_two_step_pivot_candidate(
            close_row,
            open_row,
            pre,
            target,
            pre_cash_upper_bound=Decimal("2300"),
        )
        self.assertTrue(result["open_funds_feasible_after_close"])
        self.assertGreater(
            result["flat_cash_after_close"],
            result["cash_required_before_open"],
        )
        self.assertAlmostEqual(
            float(result["implied_pre_short_qty_to_match_target"]),
            46.2761728395,
            places=6,
        )


    def test_short_redeploy_bounds_raise_prior_carry_requirement(self):
        pre = {
            "score": Decimal("749.24"),
            "mark": Decimal("229.07"),
        }
        reach = {
            "min_legal_buy_seen": Decimal("211.8595"),
            "max_legal_sell_seen": Decimal("244.4190"),
        }
        result = c._leader_short_redeploy_bounds(
            pre,
            Decimal("43.18068965517241379310344828"),
            Decimal("498.3051586206896551724137932"),
            reach,
        )
        self.assertTrue(result["feasible"])
        self.assertAlmostEqual(
            float(result["entry_ceiling_from_close_funds"]),
            233.2331370983,
            places=6,
        )
        self.assertGreater(
            result["min_prior_realized_carry_before_short"],
            Decimal("670"),
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
