"""A full 23-wallet proof census cannot turn selected native deltas into win rates."""
import copy
import unittest

from bsc_meme_address_model_v1_p4c_23wallet_economic_census import census, load


class Frozen23WalletEconomicCensus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = load()

    def reject(self, mutator):
        raw = copy.deepcopy(self.original)
        mutator(raw)
        with self.assertRaises(ValueError):
            census(raw)

    def test_complete_23x19_and_no_profitable_ranking(self):
        x = census(self.original)
        self.assertEqual((x["frozen_wallets"], x["frozen_exact_CAs"], x["frozen_cells"]), (23, 19, 437))
        self.assertEqual((x["ERC20_present"], x["ERC20_absent"]), (148,289))
        self.assertEqual((x["curated_wallets"], x["other_wallets_without_selected_rounds_not_losses"]), (7,16))
        self.assertEqual((x["curated_signed_closed_episodes"],
                          x["curated_native_scope_positive_not_realized_PnL"],
                          x["curated_native_scope_negative_not_realized_PnL"],
                          x["curated_mixed_quote_references_not_native_PnL"]), (50,30,18,2))
        self.assertEqual(x["full_wallet_economic_profitable_ranks"],0)
        self.assertEqual(x["P5"],"BLOCKED")
        self.assertEqual(x["PRODUCTION"],"NO_GO")
        self.assertEqual(len(x["wallets"]),23)
        self.assertEqual(sum(len(w["cells"]) for w in x["wallets"]),437)
        self.assertTrue(all(w["profit_rank"] is None and w["buy_signal"]=="NONE_RESEARCH_ONLY" for w in x["wallets"]))
        self.assertTrue(all(c["owner_true_all_asset_net_profit"]=="UNRESOLVED" for w in x["wallets"] for c in w["cells"]))

    def test_other_sixteen_have_unresearched_not_loss_state(self):
        out=census(self.original)
        not_audited=[w for w in out["wallets"] if w["curated_original_signed_closed_episodes"]==0]
        self.assertEqual(len(not_audited),16)
        self.assertTrue(all(c["economic_evidence_state"]=="NO_CURATED_ROUND_DOES_NOT_MEAN_NO_TRADE_OR_LOSS" for w in not_audited for c in w["cells"]))

    def test_only_one_wallet_has_two_selected_2026_receipt_gas_major_sources(self):
        out=census(self.original)
        witnesses=[w for w in out["wallets"] if w["2026_two_distinct_major_selected_positive_gas_witness"]]
        self.assertEqual(len(witnesses),1)
        self.assertEqual(witnesses[0]["wallet"],"0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0")
        self.assertEqual(len([c for c in witnesses[0]["cells"] if c["selected_2026_positive_receipt_gas_major_witness"]]),2)
        self.assertEqual(witnesses[0]["wallet_full_history_realized_PnL"],"UNRESOLVED")

    def test_negative_and_mixed_quote_stay_visible(self):
        out=census(self.original)
        self.assertEqual(sum(w["curated_native_block_negative"] for w in out["wallets"]),18)
        self.assertEqual(sum(w["curated_mixed_quote_reference"] for w in out["wallets"]),2)
        self.assertEqual(sum(c["selected_receipt_gas_scope_count"] for w in out["wallets"] for c in w["cells"]),4)

    def test_changing_437_denominator_rejected(self):
        self.reject(lambda d:d["scope"]["frozen_denominator"].update(cells=436))

    def test_truncating_one_frozen_wallet_rejected(self):
        self.reject(lambda d:d["baseline"]["wallets"].pop())

    def test_deleting_one_frozen_major_ca_cell_rejected(self):
        self.reject(lambda d:d["baseline"]["wallets"][0]["cells"].pop())

    def test_forging_transfer_presence_into_realized_profit_rejected(self):
        self.reject(lambda d:d["baseline"]["wallets"][0]["cells"][0].update(
            realized_cashflow_and_profit="CONFIRMED_PROFIT"))

    def test_dropping_original_negative_curated_round_rejected(self):
        def drop(d):
            d["ledger"]["episodes"].pop(next(i for i,x in enumerate(d["ledger"]["episodes"])
                if x["net_classification"]=="NEGATIVE_NATIVE_SCOPE"))
        self.reject(drop)

    def test_mixed_quote_not_native_profit_rejected(self):
        self.reject(lambda d:next(x for x in d["ledger"]["episodes"]
                     if x["evidence_grade"]=="MIXED_BNB_USDT_SPOT_REFERENCE").update(
                     net_classification="POSITIVE_NATIVE_SCOPE"))

    def test_2026_two_major_first_signed_evidence_cannot_be_swapped(self):
        self.reject(lambda d:d["two_major"]["selected_two_major_positive_receipt_proofs"][0].update(
            buy_block=1))

    def test_source_cashflow_unknown_adff_must_not_be_free(self):
        self.reject(lambda d:d["adff_boundary"].update(
            original_owner_realized_pnl="PROFIT"))

    def test_frozen_23_only_cannot_add_outside_wallet_signed_episode(self):
        self.reject(lambda d:d["ledger"]["episodes"][0].update(wallet="0x"+"9"*40))

    def test_a_missing_source_grade_cannot_enter_curated_profit(self):
        self.reject(lambda d:d["ledger"]["episodes"][0].update(
            evidence_grade="UNSUPPORTED_PROFIT"))


if __name__ == "__main__":
    unittest.main()
