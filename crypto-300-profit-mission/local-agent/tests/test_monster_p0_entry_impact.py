import unittest
from mission_agent.early.entry_impact import (
    EntryImpactError, audit_frozen30, impact_microbps,
)


def fixture():
    ids = [dict(rank=r, token_ca="0x"+format(r, "040x"),
                pool="0x"+format(r+100, "040x"), creation_block=100,
                first_confirmed_frozen_depth_event={"block": 101})
           for r in range(1, 31)]
    rows = []
    for r in list(range(1, 16))+list(range(18, 23)):
        rows.append(dict(rank=r, token_ca=ids[r-1]["token_ca"],
                         pair=ids[r-1]["pool"], buy_block=110, buy_tx="0x"+"a"*64,
                         buy_transaction_receipt_status="0x1",
                         buy_quote_in_raw="100", buy_preswap_quote_reserve_raw="10000"))
    extras = [dict(rank=r, token_ca=ids[r-1]["token_ca"], pool=ids[r-1]["pool"],
                   real_independent_post_atomic_buy_block=111,
                   real_independent_post_atomic_buy_tx="0x"+"b"*64,
                   actual_buy_receipt_status="0x1", real_buy_quote_into_pool_raw="400",
                   buy_preswap_quote_reserve_raw="10000") for r in (16,17)]
    return {"bsc_v2_p0_current_frozen30_p0_gate_matrix_20261020":{"rows":ids},
            "bsc_v2_p0_uploaded20_actual_buy_and_indexed_real_sell_replay_20261020":{"case_results":rows},
            "bsc_v2_p0_ranks16_17_post_atomic_distinct_buy_and_partial_sell_pilot_20261020":{"cases":extras}}


class ImpactTests(unittest.TestCase):
    def test_fee_only_limit_and_integer_math(self):
        self.assertEqual(impact_microbps("1", "100000000000000000", fee_bps=0), 1)
        self.assertGreater(impact_microbps("1", "100000000000000000"), 25*1000000)
        self.assertGreater(impact_microbps("100", "10000"), 100*1000000)
        self.assertEqual(impact_microbps("100", "10000"), 125062657)

    def test_invalid_inputs_fail_closed(self):
        for bad in (True, -1, 0, "0", "1.0", None):
            with self.subTest(bad=bad), self.assertRaises(EntryImpactError):
                impact_microbps(bad, "100")
        for fee in (-1, True, 10000, "25"):
            with self.subTest(fee=fee), self.assertRaises(EntryImpactError):
                impact_microbps("100", "100", fee_bps=fee)

    def test_frozen_identity_and_missing_8_are_not_zero(self):
        f = fixture()
        r = audit_frozen30(f, 100)
        self.assertEqual((r["selected_historical_buy_count"],r["unknown_count"]),(22,8))
        self.assertEqual(r["above_diagnostic_limit"],22)
        self.assertIsNone(r["rows"][29]["impact_microbps"])
        self.assertEqual(r["rows"][29]["evidence"],"NOT_SCORABLE")
        self.assertFalse(r["p0_gate_passed"])
        f["future_90_day_winners"] = [1,2,3]
        self.assertEqual(r,audit_frozen30(f,100))

    def test_rejects_duplicates_wrong_identity_and_future_trade(self):
        for edit, expected in (
            (lambda f: f["bsc_v2_p0_uploaded20_actual_buy_and_indexed_real_sell_replay_20261020"]["case_results"][1].update(rank=1),"DUPLICATE_OR_INVALID_RANK"),
            (lambda f: f["bsc_v2_p0_uploaded20_actual_buy_and_indexed_real_sell_replay_20261020"]["case_results"][0].update(pair="0x"+"f"*40),"IDENTITY_MISMATCH"),
            (lambda f: f["bsc_v2_p0_uploaded20_actual_buy_and_indexed_real_sell_replay_20261020"]["case_results"][0].update(buy_block=101),"PRETRADE_ORDER_UNPROVEN"),
            (lambda f: f["bsc_v2_p0_uploaded20_actual_buy_and_indexed_real_sell_replay_20261020"]["case_results"][0].update(buy_transaction_receipt_status="0x0"),"PRETRADE_ORDER_UNPROVEN"),
        ):
            f = fixture()
            edit(f)
            with self.subTest(expected=expected),self.assertRaisesRegex(EntryImpactError,expected):
                audit_frozen30(f,100)

    def test_no_inferred_pit_or_common_notional(self):
        r=audit_frozen30(fixture(),100)
        self.assertEqual(r["pit_available_at"],"UNKNOWN")
        self.assertEqual(r["uniform_notional_sellability"],"NOT_SCORABLE")
        self.assertFalse(r["selected_sample_representative"])

if __name__ == "__main__":
    unittest.main()
