#!/usr/bin/env python3
"""Regression controls for selected owner's bought/partial-exit/exit/reentry historical semantics."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_original_owner_signal_lifecycle as study

class HistoricalOwnedFiveEpisodeLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good=study.load()

    def invalid(self,mutate,expected):
        d=copy.deepcopy(self.good)
        mutate(d)
        with self.assertRaisesRegex(ValueError,expected):
            study.build(d)

    def test_selected_five_owner_episodes_not_causal_followers(self):
        out=study.build(self.good)
        self.assertEqual(out["scope"]["selected_research_episodes"],5)
        self.assertEqual(out["scope"]["selected_owners"],3)
        self.assertEqual(out["scope"]["selected_markets"],2)
        self.assertEqual(out["scope"]["original_possible_cells"],437)
        self.assertEqual(out["scope"]["selected_positive_native_owner_episodes"],3)
        self.assertEqual(out["scope"]["selected_negative_native_owner_episodes"],2)
        self.assertFalse(out["scope"]["return_winrate_representative_of_437"])
        self.assertEqual(out["P5"],"BLOCKED")
        self.assertEqual(out["PUBLIC_EXECUTABLE_U"],"UNRESOLVED")

    def test_ddac_is_closed_at_later_d503_first_buy_block(self):
        o=study.build(self.good)
        p=[q for q in o["historical_checkpoints"]
             if q["fixed_checkpoint_case"]=="DDAC_DRAGON_R1"
             and q["as_of_HISTORICAL_block_end"]==83636000]
        self.assertEqual(len(p),1)
        self.assertEqual(p[0]["historical_SIGNED_EVENT_reconstructed_state"],
                         "CLOSED_EXACT_SELECTED_EPISODE")
        self.assertEqual(p[0]["selected_events_net_token_raw"],"0")
        self.assertTrue(o["original_DDAC_late_external_buyer"]["selected_old_buy_signal_already_closed"])
        self.assertFalse(o["original_DDAC_late_external_buyer"]["could_prove_D503_copied_DDAC"])

    def test_239e_add_then_exit_then_independent_reentry(self):
        o=study.build(self.good)
        snapshots=[q for q in o["historical_checkpoints"]
                   if q["fixed_checkpoint_case"]=="239E_DRAGON_R1"]
        by_block={q["as_of_HISTORICAL_block_end"]:q for q in snapshots}
        self.assertEqual(by_block[85954137]["historical_SIGNED_EVENT_reconstructed_state"],
                         "OPEN_NEW_EPISODE")
        self.assertEqual(by_block[85954824]["historical_SIGNED_EVENT_reconstructed_state"],
                         "OPEN_ADDED_TO_EXISTING_EPISODE")
        self.assertEqual(by_block[85957578]["historical_SIGNED_EVENT_reconstructed_state"],
                         "CLOSED_EXACT_SELECTED_EPISODE")
        self.assertEqual(by_block[85959960]["historical_SIGNED_EVENT_reconstructed_state"],
                         "CLOSED_EXACT_SELECTED_EPISODE")
        self.assertEqual(by_block[85959961]["historical_SIGNED_EVENT_reconstructed_state"],
                         "OPEN_NEW_EPISODE")
        self.assertEqual(by_block[85959961]["current_selected_episode"],"239E_DRAGON_R2")
        self.assertEqual(by_block[85961371]["selected_events_net_token_raw"],"0")
        self.assertEqual(o["original_239E_same_token_rounds_net_wei"],"7315133865250263")

    def test_hajimi_partial_sale_does_not_expire_buy_signal_early(self):
        o=study.build(self.good)
        snapshots={q["as_of_HISTORICAL_block_end"]:q for q in o["historical_checkpoints"]
                   if q["fixed_checkpoint_case"]=="8E6B_HAJIMI_R1"}
        self.assertEqual(snapshots[74741573]["historical_SIGNED_EVENT_reconstructed_state"],
                         "OPEN_PARTIAL_EXIT")
        self.assertEqual(snapshots[74741573]["selected_events_net_token_raw"],
                         "64629048195327088600524")
        self.assertEqual(snapshots[74741587]["historical_SIGNED_EVENT_reconstructed_state"],
                         "CLOSED_EXACT_SELECTED_EPISODE")
        self.assertEqual(snapshots[74741587]["selected_events_net_token_raw"],"0")

    def test_pre_buy_unknown_is_not_asserted_wallet_empty(self):
        o=study.build(self.good)
        rows=[q for q in o["historical_checkpoints"]
             if q["historical_SIGNED_EVENT_reconstructed_state"]=="NO_SELECTED_TX_YET_NOT_PROVEN_FLAT"]
        self.assertGreaterEqual(len(rows),3)
        self.assertTrue(all(q["selected_events_net_token_raw"] is None and
                            q["actual_full_onchain_wallet_inventory_at_arbitrary_block"]=="UNRESOLVED"
                            for q in rows))

    def test_239e_wrong_signed_inventory_delta(self):
        self.invalid(lambda d:d["e239"]["rounds"][0]["txs"][0].update(
            wallet_signed_token_delta_raw="-2756988984252717159259"),
            "239E_OWNER_SIGNED_TOKEN_DELTA")

    def test_239e_oversell_is_never_allowed(self):
        self.invalid(lambda d:d["e239"]["rounds"][0]["txs"][-1].update(
            token_raw="999999999999999999999999999999",
            wallet_signed_token_delta_raw="-999999999999999999999999999999"),
            "ROUND_SIGNED_ORDER_OR_OVERSOLD")

    def test_original_ddac_closed_amount_not_edited(self):
        self.invalid(lambda d:d["ddac"]["round"].update(
            exit_token_amount_raw="1"),"DDAC_CLOSED_REALIZED_NEGATIVE_PROOF")

    def test_239e_mixed_realized_signs_not_both_positive(self):
        self.invalid(lambda d:d["e239"]["rounds"][0].update(
            native_original_EOA_profit_sign="POSITIVE"),
            "239E_TWO_REAL_ROUNDS_MIXED_SIGNS")

    def test_partial_hajimi_sale_not_zero(self):
        self.invalid(lambda d:d["e8"]["rounds"][0]["sells"][0].update(
            sold_token_raw="0"),"SIGNER_EVENT_ENCODING")

    def test_hajimi_cannot_skip_full_second_sale(self):
        self.invalid(lambda d:d["e8"]["rounds"][0]["sells"][1].update(
            sold_token_raw="1"),"8E6B_CLOSED_INVENTORY_AND_PARTIAL_SALE")

    def test_no_fake_live_position_or_public_U(self):
        self.invalid(lambda d:d["freeze"]["gates"].update(
            live_wallet_position_authority="FULL_CHAIN_VALIDATED"),
            "HISTORICAL_POSITION_NOT_LIVE_SIGNAL")

    def test_frozen_437_cohort_cannot_change(self):
        self.invalid(lambda d:d["matrix"]["summary"].update(
            implicit_wallet_CAs=436),"COHORT_OR_PRESELECTED_CHECKPOINT_DRIFT")

    def test_source_byte_tampering_must_fail_without_replay(self):
        with tempfile.TemporaryDirectory() as path:
            root=Path(path)
            for filename,_ in study.FILES.values():
                shutil.copyfile(study.ROOT/filename,root/filename)
            self.assertEqual(study.build(study.load(root))["P4_B"],"PARTIAL")
            with (root/study.FILES["e239"][0]).open("ab") as out:
                out.write(b" ")
            with self.assertRaisesRegex(ValueError,"SOURCE_BLOB_DRIFT_e239"):
                study.load(root)

if __name__=="__main__":
    unittest.main()
