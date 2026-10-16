"""Offline exact original 10 transaction WBNB route evidence; zero/partial-safe."""
import copy
import unittest

from bsc_meme_address_model_v1_p4c_wbnb10_source_gate import classify, load


class FrozenFourOwnerWrappedBNBRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = load()

    def assert_reject(self, change):
        data=copy.deepcopy(self.d)
        change(data)
        with self.assertRaises(ValueError):
            classify(data)

    def test_all_four_original_owners_positive_negative_control_and_full_scope(self):
        out=classify(self.d)
        self.assertEqual(out["original_owners"], 4)
        self.assertEqual(out["original_transactions"], 10)
        self.assertEqual((out["positive_source_native_scope_owners"],
                          out["negative_source_native_scope_owners"]), (2,2))
        self.assertEqual((out["complete_exact_block_event_queries"],
                          out["truncated_exact_block_event_queries"]), (19,1))
        self.assertEqual(out["cases"]["31"]["wbnb_event_sums_wei"]["Deposit"],
                         "99000000000000000")
        self.assertEqual(out["cases"]["38"]["wbnb_event_sums_wei"]["Withdrawal"],
                         "1694918377918343466")
        self.assertEqual(out["cases"]["46"]["wbnb_event_sums_wei"]["Withdrawal"],
                         "UNRESOLVED_PARTIAL_LOG_QUERY")
        self.assertEqual(out["cases"]["44"]["wbnb_event_sums_wei"]["Deposit"], "0")
        self.assertEqual(out["cases"]["44"]["quote_route_pnl"], "UNRESOLVED")
        self.assertEqual(out["repeat_trader_profitability"], "UNRESOLVED")
        self.assertEqual(out["public_executable_U"], "UNRESOLVED")
        self.assertEqual(out["P5"], "BLOCKED")
        self.assertEqual(out["PRODUCTION"], "NO_GO")

    def test_cannot_drop_negative_wallet(self):
        self.assert_reject(lambda d:d["scope"]["original_txs"].pop(1))

    def test_cannot_replace_original_signed_hash(self):
        self.assert_reject(lambda d:d["a"]["cases"][0].update(hash="0x"+"0"*64))

    def test_cannot_hide_empty_deposit(self):
        self.assert_reject(lambda d:d["c"]["cases"][0]["events"][0].update(
            selected_tx_events=None))

    def test_cannot_turn_unknown_2adf_withdrawal_into_zero(self):
        def mutate(d):
            d["b"]["cases"][2]["events"][1]["full_block_filter_reply"]=True
            d["b"]["cases"][2]["events"][1]["selected_tx_events"]=[]
        self.assert_reject(mutate)

    def test_cannot_add_fabricated_token_sale_to_other_original_transaction(self):
        def mutate(d):
            event=d["c"]["cases"][1]["events"][1]["selected_tx_events"][0]
            event["transactionHash"]="0x"+"a"*64
        self.assert_reject(mutate)

    def test_cannot_silently_promote_zero_native_adff_initial_input(self):
        self.assert_reject(lambda d:next(x for x in d["csource"]["cases"]
           if x["index"]==44 and x["block"]==121783426).update(tx_value_wei="1000000000000000"))

    def test_cannot_drop_negative_marscoin_exit(self):
        self.assert_reject(lambda d:d["b"]["cases"][0]["events"][1].update(
            selected_tx_events=[]))

    def test_cannot_invert_2adf_native_positive_source_sign(self):
        self.assert_reject(lambda d:d["scope"]["original_txs"][2].update(
            original_native_scope_sign="NEGATIVE_NATIVE_SCOPE"))

    def test_cannot_make_same_wrapper_event_amount_different_from_raw_data(self):
        self.assert_reject(lambda d:d["a"]["cases"][1]["events"][1][
            "selected_tx_events"][0].update(amount_wei="0"))

    def test_cannot_relabel_partial_query_as_complete(self):
        self.assert_reject(lambda d:d["b"]["cases"][2]["events"][1].update(
            full_block_filter_reply=True))

    def test_adff_original_two_in_one_out_inventory_equal_but_cost_not_proven(self):
        result=classify(self.d)
        self.assertEqual(result["ADFF_original_Dragon_transfer_in_raw"],"32546033429758403566")
        self.assertEqual(result["ADFF_original_Dragon_transfer_out_raw"],"32546033429758403566")
        self.assertEqual(result["ADFF_original_first_tx_WBNB_ERC20_received_wei"],"176310176278987")
        self.assertTrue(result["ADFF_all_assets_input_cost"].startswith("UNRESOLVED"))

    def test_adff_inbound_token_amount_tampering_is_rejected(self):
        self.assert_reject(lambda d:d["adff"]["queries"][0]["exact_original_tx_events"][0].update(
            raw_amount="999"))

    def test_adff_other_sender_withdrawal_cannot_be_called_token_owner(self):
        self.assert_reject(lambda d:d["adff"]["queries"][5]["exact_original_tx_events"][0][
            "topics"].__setitem__(1,"0x"+"0"*64))

    def test_adff_missing_external_cost_query_cannot_be_silently_ignored(self):
        self.assert_reject(lambda d:d["adff"]["queries"][3].update(filter_complete=False))

    def test_adff_owner_wide_outgoing_transfer_is_zero_but_acquisition_not_free(self):
        out=classify(self.d)
        self.assertEqual(out["ADFF_initial_signed_tx_standard_ERC20_owner_out"],
                         "ZERO_MATCHES_SINGLE_BLOCK_TRANSFER_TOPIC")
        self.assertEqual(out["ADFF_economic_acquisition_class"],
                         "SOURCE_AMBIGUOUS_NOT_CONFIRMED_BUY_OR_FREE_AIRDROP")
        self.assertTrue(out["ADFF_realized_return"].startswith("UNRESOLVED"))
        self.assertEqual(out["P5"],"BLOCKED")

    def test_adff_cannot_manufacture_payment_outflow_in_original_block(self):
        self.assert_reject(lambda d:d["adff_payment_scope"]["source_queries"][0].update(
            raw_text='[{"transactionHash":"0x'+'0'*64+'"}]'))

    def test_adff_cannot_forge_internal_transfer_service_supported(self):
        self.assert_reject(lambda d:d["adff_payment_scope"]["source_queries"][5].update(
            status="SUCCESS_ALL_INTERNAL_TRANSFERS_READ"))

    def test_adff_cannot_swap_original_signed_first_tx_for_another_acquisition(self):
        self.assert_reject(lambda d:d["adff_payment_scope"].update(
            original_tx=d["adff"]["exact_txs"][1]["hash"]))

    def test_adff_counterparty_outflow_path_cannot_be_silently_changed(self):
        self.assert_reject(lambda d:d["adff_payment_scope"]["source_queries"][6].update(
            raw_text='[{"data":"0x1"}]'))

    def test_cannot_swap_positive_negative_case_order(self):
        self.assert_reject(lambda d:d["a"]["cases"].reverse())


if __name__=="__main__":
    unittest.main()
