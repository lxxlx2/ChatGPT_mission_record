from decimal import Decimal
import unittest

import close_call_fleet as c


class CounterpartyRedeployScanTests(unittest.TestCase):
    def account(self, name, side, qty, entry, fee, cash):
        return {
            "pair_id": name.rsplit("-", 1)[0],
            "account": name,
            "side": side,
            "qty": Decimal(qty),
            "entry": Decimal(entry),
            "opening_fee": Decimal(fee),
            "cash": Decimal(cash),
            "evidence_mode": "visible_settled",
            "source": "reserve",
        }

    def trio(self):
        target = self.account(
            "T-L", "long", "41.28", "216.87", "459.8592", "587.7472"
        )
        donor_a = self.account(
            "A-S", "short", "41.28", "232.84", "199.3824", "188.9824"
        )
        donor_b = self.account(
            "B-S", "short", "41.28", "232.84", "199.3824", "188.9824"
        )
        return target, donor_a, donor_b

    def test_group_accounts_collapses_identical_terms(self):
        _t, a, b = self.trio()
        groups = c._cp_group_accounts([a, b])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["accounts"], ["A-S", "B-S"])

    def test_other_frontier_excludes_three_selected_accounts(self):
        rows = [
            [
                (Decimal("100"), "A"),
                (Decimal("90"), "B"),
                (Decimal("80"), "C"),
                (Decimal("70"), "D"),
            ],
            [
                (Decimal("50"), "C"),
                (Decimal("40"), "D"),
                (Decimal("30"), "E"),
                (Decimal("20"), "F"),
            ],
        ]
        out = c._cp_other_frontier_from_top(
            rows, {"A", "B", "C"}
        )
        self.assertEqual(out, [Decimal("70"), Decimal("40")])

    def test_quick_stats_accepts_exact_visible_trio(self):
        target, a, b = self.trio()
        s_grid = [Decimal("220"), Decimal("230"), Decimal("240")]
        other = [Decimal("100"), Decimal("100"), Decimal("100")]
        podium = [Decimal("500"), Decimal("500"), Decimal("500")]
        result = c._cp_quick_stats(
            target,
            a,
            b,
            [Decimal("230"), Decimal("233")],
            Decimal("241.44"),
            other,
            podium,
            s_grid,
        )
        self.assertIsNotNone(result)
        self.assertGreater(result["leg2_qty_min"], Decimal("0"))
        self.assertGreaterEqual(
            result["leg2_qty_max"], result["leg2_qty_min"]
        )

    def test_quick_stats_rejects_infeasible_counterparty(self):
        target, a, b = self.trio()
        a["cash"] = Decimal("1")
        result = c._cp_quick_stats(
            target,
            a,
            b,
            [Decimal("230")],
            Decimal("241.44"),
            [Decimal("100")],
            [Decimal("500")],
            [Decimal("230")],
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
