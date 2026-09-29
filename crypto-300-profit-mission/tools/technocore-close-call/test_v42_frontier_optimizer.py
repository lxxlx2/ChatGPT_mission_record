from decimal import Decimal
import unittest

import close_call_fleet as c


class V42FrontierOptimizerTests(unittest.TestCase):
    def samples(self):
        applied = Decimal("230")
        moves = [
            "-0.010", "-0.008", "-0.006", "-0.004", "-0.002", "-0.001",
            "0.000", "0.001", "0.002", "0.004", "0.006", "0.008",
            "0.010", "0.012", "0.014", "0.016", "0.018", "0.020",
            "-0.012", "-0.014", "-0.016", "-0.018", "-0.020", "0.003",
        ]
        return [
            {
                "n": i,
                "applied": applied,
                "close": applied * (Decimal("1") + Decimal(move)),
                "move": Decimal(move),
            }
            for i, move in enumerate(moves, 1)
        ]

    def test_v42_pair_is_two_sided_and_within_limits(self):
        pr = {"px": Decimal("230"), "raw": {}}
        plan = c.dense_v42_plan_pair(
            pr,
            self.samples(),
            4,
            Decimal("0.05"),
            Decimal("0.02"),
            Decimal("1.00"),
        )
        self.assertIsNotNone(plan)
        lo, hi = c.dense_v4_limit_bounds(pr)
        self.assertGreaterEqual(plan["low"], lo)
        self.assertLessEqual(plan["high"], hi)
        self.assertGreaterEqual(plan["long_qty"], Decimal("0.10"))
        self.assertGreaterEqual(plan["short_qty"], Decimal("0.10"))
        self.assertLessEqual(plan["short_qty"], plan["long_qty"])

    def test_candidate_score_lines_have_expected_slopes(self):
        pr = {"px": Decimal("230"), "raw": {}}
        plan = c.dense_v42_plan_pair(
            pr,
            self.samples(),
            3,
            Decimal("0.05"),
            Decimal("0.02"),
            Decimal("1.00"),
        )
        lines = c._v42_plan_lines(plan, Decimal("230"), [Decimal("0")])
        row = lines[0]
        self.assertEqual(row["long"][0], plan["long_qty"])
        self.assertEqual(row["short"][0], -plan["short_qty"])
        s1, s2 = Decimal("225"), Decimal("235")
        self.assertGreater(
            c._v42_line_score(row["long"], s2),
            c._v42_line_score(row["long"], s1),
        )
        self.assertLess(
            c._v42_line_score(row["short"], s2),
            c._v42_line_score(row["short"], s1),
        )

    def test_frontier_stats_reward_gap_reduction(self):
        podium = [Decimal("900"), Decimal("900")]
        weak = [[Decimal("100"), Decimal("100")]]
        better = [[Decimal("800"), Decimal("950")]]
        a = c._v42_frontier_stats(weak, podium)
        b = c._v42_frontier_stats(better, podium)
        self.assertGreater(b["covered_cells"], a["covered_cells"])
        self.assertLess(b["total_gap"], a["total_gap"])

    def test_apply_candidate_never_reduces_existing_frontier(self):
        existing = [[Decimal("100"), Decimal("200")]]
        lines = [{
            "long": (Decimal("10"), Decimal("-2100")),
            "short": (Decimal("-10"), Decimal("2500")),
        }]
        grid = [Decimal("220"), Decimal("230")]
        out = c._v42_apply_candidate(existing, lines, grid)
        self.assertGreaterEqual(out[0][0], existing[0][0])
        self.assertGreaterEqual(out[0][1], existing[0][1])

    def test_greedy_select_uses_at_most_requested_copies(self):
        pr = {"px": Decimal("230"), "raw": {}}
        samples = self.samples()
        pool = []
        for long_off, short_off in [
            ("0.01", "0.01"),
            ("0.03", "0.02"),
            ("0.05", "0.05"),
        ]:
            pool.append(
                c.dense_v42_plan_pair(
                    pr,
                    samples,
                    3,
                    Decimal(long_off),
                    Decimal(short_off),
                    Decimal("1.00"),
                )
            )
        s_grid = [Decimal("220"), Decimal("225"), Decimal("230"), Decimal("235"), Decimal("240")]
        existing = {s: Decimal("100") for s in s_grid}
        podium = {s: Decimal("500") for s in s_grid}
        selected, _frontier, meta = c._v42_greedy_select(
            pool,
            existing,
            podium,
            Decimal("230"),
            [Decimal("-0.01"), Decimal("0"), Decimal("0.01")],
            s_grid,
            2,
        )
        self.assertEqual(len(selected), 2)
        self.assertEqual(len(meta["rounds"]), 2)


if __name__ == "__main__":
    unittest.main()
