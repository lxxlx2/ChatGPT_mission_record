#!/usr/bin/env python3
"""Stage151 causal offline deterministic unit tests, no market GET."""
import unittest
from decimal import Decimal

import monster_v4_stage151_post_d1_pullback_reclaim as m

D = Decimal
T0 = 1_800_000_000_000


def bars(closes, start=T0, *, quote=D("1000"), trades=10):
    out = []
    for i, val in enumerate(closes):
        close = D(str(val))
        price = D("100")
        out.append((start + i*m.MIN, price,
                    max(price, close)+D("1"),
                    min(price, close)-D("1"),
                    close, quote, trades))
    return out


class Stage151(unittest.TestCase):
    def test_no_pullback_full120(self):
        x = m.decision(bars([100]*120), D("100"), T0)
        self.assertEqual(x["state"], "NO_PULLBACK_WITHIN_120M")
        self.assertIsNone(x["decision_visible_ms"])

    def test_pullback_without_reclaim(self):
        x = m.decision(bars([100,96]+[95]*118), D("100"), T0)
        self.assertEqual(x["state"], "PULLBACK_NO_RECLAIM")
        self.assertEqual(x["armed_bar_index"], 1)
        self.assertIsNone(x["decision_visible_ms"])

    def test_completed_bar_reclaim_entry_next_open(self):
        x = m.decision(bars([100,96,97.2]+[99]*117),D("100"),T0)
        self.assertEqual(x["state"],"PULLBACK_RECLAIM_CONFIRMED_PRICE_ONLY")
        self.assertEqual(x["decision_visible_ms"],T0+3*m.MIN)
        self.assertEqual(x["decision_bar_index"],2)
        self.assertEqual(x["trough_from_completed_closes"],"96")

    def test_future_changes_cannot_change_first_decision(self):
        one = [100,96,97.2]+[99]*117
        two = one[:3]+[1000000]*117
        self.assertEqual(m.decision(bars(one), D("100"),T0),
                         m.decision(bars(two), D("100"),T0))

    def test_can_confirm_at_120th_closed_bar(self):
        x = m.decision(bars([100]*118+[96,98]), D("100"),T0)
        self.assertEqual(x["decision_bar_index"],119)
        self.assertEqual(x["decision_visible_ms"], T0+120*m.MIN)

    def test_high_wick_cannot_confirm(self):
        x = bars([100,96]+[96]*118)
        x[2] = (x[2][0],D("100"),D("500"),D("90"),D("96"),D("1000"),10)
        self.assertEqual(m.decision(x,D("100"),T0)["state"],
                         "PULLBACK_NO_RECLAIM")

    def test_missing_and_invalid_bar_rejected(self):
        x=bars([100]*120)
        with self.assertRaisesRegex(ValueError,"120M"):
            m.decision(x[:119],D("100"),T0)
        y=list(x)
        y[119]=(y[119][0]+m.MIN,*y[119][1:])
        with self.assertRaisesRegex(ValueError,"MISSING_OR_INVALID_OBSERVABLE"):
            m.decision(y,D("100"),T0)
        y=list(x)
        y[3]=(y[3][0],D("100"),D("99"),D("101"),D("100"),D("1000"),10)
        with self.assertRaisesRegex(ValueError,"MISSING_OR_INVALID_OBSERVABLE"):
            m.decision(y,D("100"),T0)

    def test_no_implicit_notional_and_no_real_fill(self):
        rows=bars([100]*361)
        end=rows[360]
        rows[360]=(end[0],D("110"),D("111"),D("109"),D("110"),D("1000"),10)
        lookup={x[0]:x for x in rows}
        x=m.price_path(lookup,T0,D("100"),360)
        self.assertEqual(x["status"],"COMPLETE_UNFILLED_PRICE_PROXY")
        self.assertEqual(D(x["gross_pct"]),D("10"))
        self.assertLess(D(x["illustrative_20bps_each_side_pct"]),D("10"))
        self.assertEqual(x["real_bid_ask_fill_net"],"UNKNOWN")
        self.assertNotIn("notional_quote",x)
        self.assertNotIn("actual_fill",x)

    def test_no_trades_exit_not_pretend_filled(self):
        rows=bars([100]*361)
        e=rows[360]
        rows[360]=(e[0],e[1],e[2],e[3],e[4],D(0),0)
        lookup={x[0]:x for x in rows}
        self.assertEqual(m.price_path(lookup,T0,D("100"),360)["status"],
                         "EXIT_NO_TRADES_PRICE_PROXY_UNSUPPORTED")

    def test_price_path_gaps_rejected(self):
        lookup={x[0]:x for x in bars([100]*361)}
        del lookup[T0+100*m.MIN]
        with self.assertRaisesRegex(ValueError,"GAPPED"):
            m.price_path(lookup,T0,D("100"),360)

    def test_reject_invalid_p0(self):
        with self.assertRaisesRegex(ValueError,"INVALID_FROZEN"):
            m.decision(bars([100]*120),D("NaN"),T0)


if __name__ == "__main__":
    unittest.main()
