"""No-network and fail-closed tests for two precommitted signed Dragon candidates."""
import copy
import unittest

from bsc_meme_address_model_v1_p4b_dragon_signed_roundtrip import (
    ROOT, PINS, D503, E11B, classify, load
)


class DragonPostOwnerActualSignedExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = load(ROOT)

    def test_approved_original_two_buyer_source_replay_stays_non_followable(self):
        x = classify(self.original)
        self.assertEqual(len(PINS), 7)
        self.assertEqual(x["frozen_actual_buyers"], 2)
        self.assertEqual(x["postowner_buy_senders_with_direct_pre_migration_sell"], 1)
        self.assertEqual(x["d503_confirmed_original_signed_token_roundtrips"], 2)
        self.assertEqual(x["e11b_direct_curve_sell_to_manager_observed"], 0)
        self.assertEqual(x["first_executable_public_observer_U"], "UNRESOLVED")
        self.assertEqual(x["1_5_15_minute_follower_backtest"],
                         "BLOCKED_NO_UNTOUCHED_VISIBLE_U")
        self.assertEqual(x["production"], "NO_GO")
        self.assertEqual(x["sum_4_selected_wallet_native_block_deltas_wei"],
                         "61218026868859435")

    def must_reject(self, field_change):
        changed = copy.deepcopy(self.original)
        field_change(changed)
        with self.assertRaises(ValueError):
            classify(changed)

    def test_wallet_selection_cannot_change_after_scan(self):
        self.must_reject(lambda d: d["pre"]["actual_buy_candidates_frozen_before_new_exit_RPC"][1].update(
            wallet=D503))

    def test_thirteen_chunks_required_for_both_wallets(self):
        self.must_reject(lambda d: d["escan"]["scans"].pop())

    def test_truncated_chunk_cannot_count_as_zero(self):
        self.must_reject(lambda d: d["escan"]["scans"][4].update(status="TRUNCATED"))

    def test_positive_exit_cannot_be_hidden(self):
        self.must_reject(lambda d: d["dscan"]["scans"][1].update(logs=[], n=0))

    def test_other_wallet_cannot_be_invented_as_curve_exit(self):
        self.must_reject(lambda d: d["escan"]["observed_transfer_to_manager_tx_hashes"].append(
            "0x" + "f" * 64))

    def test_unrelated_token_transfer_cannot_be_counted(self):
        self.must_reject(lambda d: d["dscan"]["scans"][1]["logs"][0].update(
            address="0x" + "f" * 40))

    def test_signed_sender_mismatch_rejected(self):
        self.must_reject(lambda d: d["tx"]["cases"][2].update(from_address="0x" + "f" * 40,
                                                             **{"from": E11B}))

    def test_failed_receipt_rejected(self):
        self.must_reject(lambda d: d["tx"]["cases"][5]["receipt"].update(status="0x0"))

    def test_fake_approval_amount_rejected(self):
        self.must_reject(lambda d: d["tx"]["cases"][1]["matched_original_event"]["words"].__setitem__(
            0, "1"))

    def test_erc20_unclosed_token_inventory_rejected(self):
        self.must_reject(lambda d: d["token"]["samples"][3].update(token_raw="1"))

    def test_outcome_reconciliation_with_two_protocol_fees_rejected_if_modified(self):
        self.must_reject(lambda d: d["tx"]["cases"][2]["matched_original_event"]["words"].__setitem__(
            5, "1"))

    def test_source_native_balance_change_cannot_be_coerced_to_profit(self):
        self.must_reject(lambda d: d["native"]["movements"][1].update(
            block_native_delta_wei="200000000000000000"))

    def test_raw_block_time_cannot_be_fabricated(self):
        self.must_reject(lambda d: d["headers"]["rows"][0].update(
            milliTimestamp_hex="0x1"))

    def test_receipt_truncation_cannot_be_hidden(self):
        self.must_reject(lambda d: d["tx"]["cases"][0]["receipt"].update(complete=True))

    def test_fee_free_quoter_cannot_be_posthoc_assumed(self):
        self.must_reject(lambda d: d["tx"]["cases"][3]["matched_original_event"]["words"].__setitem__(
            5, "0"))


if __name__ == "__main__":
    unittest.main()
