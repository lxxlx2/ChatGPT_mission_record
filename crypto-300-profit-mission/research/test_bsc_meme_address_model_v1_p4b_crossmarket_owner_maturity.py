#!/usr/bin/env python3
"""Reject early-signal / copyable-profit claims from preselected positive wallets."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_crossmarket_owner_maturity as study

class CrossMarketOriginalOwnerMaturityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=study.load()

    def rejects(self,mutate,expected):
        docs=copy.deepcopy(self.data)
        mutate(docs)
        with self.assertRaisesRegex(ValueError,expected):
            study.build(docs)

    def test_three_frozen_signed_original_wallet_rounds_not_copyable_U(self):
        actual=study.build(self.data)
        self.assertEqual(actual["sample"]["original_cells_437"],437)
        self.assertEqual(actual["sample"]["handpicked_existing_high_grade_owner_rounds"],3)
        self.assertEqual(actual["sample"]["markets_in_this_narrow_comparison"],2)
        self.assertEqual(actual["sample"]["observed_causal_follower_profit_rounds"],0)
        self.assertEqual(actual["P5"],"BLOCKED")
        rows=actual["matched_three_source_owned_trade_outcomes"]
        self.assertEqual([q["owner_entry_minus_first_SCOPED_dex_block_count"] for q in rows],
                         [-352,10902409,9948153])
        self.assertEqual([q["owner_actual_BNB_selected_round_net_wei"] for q in rows],
                         ["-92169615514614272","268592992917629933","253300282319389315"])
        self.assertEqual([q["owner_signed_native_round_roi_bps_trunc"] for q in rows],
                         ["-1139","536","844"])
        self.assertEqual(actual["same_Dragon_market"]["D503_buy_happened_after_DDAC_exit_blocks"],200)
        self.assertTrue(all(q["global_market_first_public_buyable_U"]=="UNRESOLVED" for q in rows))

    def test_early_negative_exit_falsified(self):
        self.rejects(lambda d:d["negative"]["round"].update(
            exit_block=83636000), "OWNER_SIGNED_SOURCES_VS_FROZEN_COHORT")

    def test_profit_positive_would_be_mislabeled_if_hajimi_net_changed(self):
        self.rejects(lambda d:d["positive"]["rounds"][0].update(
            actual_native_round_net_wei="-1000"),"OWNER_SIGNED_SOURCES_VS_FROZEN_COHORT")

    def test_early_pool_source_distance_prevent_change(self):
        self.rejects(lambda d:d["matrix"]["markets"][14].update(
            first_scoped_dex_liquidity_block=83635775),
            "SIGNED_ENTRY_IS_NOT_ALWAYS_EARLY_MARKET_ENTRY")

    def test_late_positive_owner_swap_CA_rejected(self):
        self.rejects(lambda d:d["freeze"]["fixed_original_wallet_rounds"][2].update(
            CA="0x"+"1"*40),"OWNER_SIGNED_SOURCES_VS_FROZEN_COHORT")

    def test_no_synthetic_first_global_market_U(self):
        self.rejects(lambda d:d["freeze"]["gates"].update(
            public_first_global_U="PROVEN"),"OVERCLAIM_PUBLIC_U_P5_OR_TRADE")

    def test_provider_truncated_timestamp_cannot_invent_duration(self):
        self.rejects(lambda d:d["header_attempts"]["results"][0].update(
            timestamp="0x69876977"),"NO_PROVIDER_TIMESTAMP_OR_GLOBAL_FIRST_U")

    def test_clipped_source_cannot_claim_parseable(self):
        self.rejects(lambda d:d["header_attempts"]["results"][1].update(
            parsed_complete=True),"NO_PROVIDER_TIMESTAMP_OR_GLOBAL_FIRST_U")

    def test_d503_later_buy_not_before_ddac_exit(self):
        self.rejects(lambda d:d["d503"]["cases"][0].update(
            block=83635777),"SAME_DRAGON_TOKEN_ORIGINAL_OWNER_EXIT_BEFORE_LATER_BUYERS")

    def test_23x19_cohort_cannot_shrink(self):
        self.rejects(lambda d:d["matrix"]["summary"].update(
            implicit_wallet_CAs=436),"FROZEN_23x19_UNIVERSE_NOT_A_WIN_RATE")

    def test_source_sha_byte_modified_fails(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)
            for name,sha in study.FILES.values():
                shutil.copyfile(study.ROOT/name,dest/name)
            self.assertEqual(study.build(study.load(dest))["P5"],"BLOCKED")
            with (dest/study.FILES["positive"][0]).open("ab") as f:
                f.write(b" ")
            with self.assertRaisesRegex(ValueError,"PINNED_SOURCE_DRIFT_positive"):
                study.load(dest)

if __name__=="__main__":
    unittest.main()
