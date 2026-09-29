from decimal import Decimal
import unittest

import close_call_fleet as c


class LeaderPathReplayTests(unittest.TestCase):
    def test_long_synthetic_entry_below_legal_range_proves_carry(self):
        synthetic, carry = c._leader_min_carry_required(
            score=Decimal("944.41"),
            mark=Decimal("232.18"),
            position=Decimal("46.07"),
            min_legal_buy=Decimal("218.50"),
            max_legal_sell=Decimal("245.00"),
        )
        self.assertLess(synthetic, Decimal("218.50"))
        self.assertGreater(carry, Decimal("0"))

    def test_fee_adjusted_long_carry_bound_includes_mandatory_fee(self):
        score = Decimal("790.87")
        mark = Decimal("228.85")
        qty = Decimal("46.07")
        raw_low = Decimal("211.8595")
        effective = Decimal("213.978095")
        _synthetic, raw = c._leader_min_carry_required(
            score, mark, qty, raw_low, Decimal("244.4190")
        )
        _synthetic, fee_adjusted = c._leader_min_carry_required(
            score,
            mark,
            qty,
            raw_low,
            Decimal("244.4190"),
            effective,
            Decimal("242"),
        )
        self.assertGreater(fee_adjusted, raw)
        self.assertGreater(fee_adjusted, Decimal("100"))

    def test_short_synthetic_entry_above_legal_range_proves_carry(self):
        synthetic, carry = c._leader_min_carry_required(
            score=Decimal("900"),
            mark=Decimal("230"),
            position=Decimal("-40"),
            min_legal_buy=Decimal("210"),
            max_legal_sell=Decimal("240"),
        )
        self.assertGreater(synthetic, Decimal("240"))
        self.assertGreater(carry, Decimal("0"))

    def test_flat_score_is_exact_realized_score(self):
        synthetic, carry = c._leader_min_carry_required(
            score=Decimal("123.45"),
            mark=Decimal("230"),
            position=Decimal("0"),
            min_legal_buy=Decimal("210"),
            max_legal_sell=Decimal("240"),
        )
        self.assertIsNone(synthetic)
        self.assertEqual(carry, Decimal("123.45"))

    def test_transition_classification(self):
        self.assertEqual(
            c._leader_transition_kind(Decimal("0"), Decimal("40")),
            "open_long",
        )
        self.assertEqual(
            c._leader_transition_kind(Decimal("40"), Decimal("20")),
            "reduce_long",
        )
        self.assertEqual(
            c._leader_transition_kind(Decimal("20"), Decimal("-10")),
            "flip_to_short",
        )
        self.assertEqual(
            c._leader_transition_kind(Decimal("-10"), Decimal("0")),
            "flatten",
        )

    def test_trade_perspective_for_maker_and_taker(self):
        payload = {
            "t": "trade",
            "season": c.SEASON,
            "terms": {
                "id": "abc",
                "maker": "did-maker",
                "taker": "did-taker",
                "side": "sell",
                "qty": "12.50",
                "px": "235.00",
                "until": 100,
            },
            "taker": "did-taker",
        }
        maker = c._leader_trade_perspective("did-maker", payload)
        taker = c._leader_trade_perspective("did-taker", payload)
        self.assertEqual(maker["action"], "sell")
        self.assertEqual(maker["signed_qty"], Decimal("-12.50"))
        self.assertEqual(taker["action"], "buy")
        self.assertEqual(taker["signed_qty"], Decimal("12.50"))

    def test_inferred_slope_positions_do_not_become_true_transitions(self):
        pnl = [
            {"sweep": 10, "mark": Decimal("230"), "score": Decimal("100")},
            {"sweep": 11, "mark": Decimal("231"), "score": Decimal("140")},
            {"sweep": 12, "mark": Decimal("232"), "score": Decimal("185")},
        ]
        path = c._leader_build_path("did-x", pnl, {}, [], [])
        self.assertEqual(path["transition_count"], 0)
        self.assertGreater(path["inferred_diagnostic_count"], 0)

    def test_build_path_computes_trade_impact_relative_to_hold(self):
        pnl = [
            {"sweep": 10, "mark": Decimal("230"), "score": Decimal("100")},
            {"sweep": 11, "mark": Decimal("231"), "score": Decimal("150")},
        ]
        pos = {10: Decimal("40"), 11: Decimal("45")}
        reach = [{
            "sweep": 10,
            "min_legal_buy_seen": Decimal("210"),
            "max_legal_sell_seen": Decimal("250"),
        }, {
            "sweep": 11,
            "min_legal_buy_seen": Decimal("210"),
            "max_legal_sell_seen": Decimal("250"),
        }]
        path = c._leader_build_path("did-x", pnl, pos, reach, [])
        self.assertEqual(path["transition_count"], 1)
        transition = path["transitions"][0]
        # Holding 40 contracts through +1 mark would have moved score to 140.
        self.assertEqual(transition["hold_expected_score"], Decimal("140"))
        self.assertEqual(
            transition["trade_impact_at_current_mark"],
            Decimal("10"),
        )


if __name__ == "__main__":
    unittest.main()
