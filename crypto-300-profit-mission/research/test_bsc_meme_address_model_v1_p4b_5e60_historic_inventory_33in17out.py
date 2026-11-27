#!/usr/bin/env python3
"""Negative controls for exact 33-in 17-out inherited wallet token inventory."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_5e60_historic_inventory_33in17out as m

class TruePriorDragonInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pinned=m.load()

    def fails(self,edit,why):
        d=copy.deepcopy(self.pinned)
        edit(d)
        with self.assertRaisesRegex(ValueError,"P4B_5E60_INVENTORY_"+why):
            m.audit(d)

    def test_33_in_17_out_and_real_historic_open_close_balance(self):
        p=m.audit(self.pinned)
        self.assertEqual(p["historical_inbound_transfer_count"],33)
        self.assertEqual(p["historical_outbound_transfer_count"],17)
        self.assertEqual(p["previous_block_wallet_Dragon_raw"],"966415729394361448864776")
        self.assertEqual(p["wallet_Dragon_at_pre_1000USDT_buy_block"],
                         "335173813691889308361853")
        self.assertTrue(p["exact_balance_equation_holds"])
        self.assertEqual(p["previous_966415_Dragon_cost_basis"],"UNRESOLVED_PRE_WINDOW")
        self.assertEqual(p["net_profit"],"UNRESOLVED_ORIGINAL_CASH_COST_NOT_KNOWN")
        self.assertEqual(p["P5"],"BLOCKED")

    def test_first_to_second_page_honest_cursor(self):
        self.fails(lambda d:d["in1"].update(page_key_preserved="bad"),"PAGE1_CURSOR")

    def test_inbound_page3_next_cursor_cannot_drift(self):
        self.fails(lambda d:d["in3out2"]["in_page3"].update(nextCursor="bad"),
                   "EXACT_PAGINATION_CHAIN")

    def test_final_inbound_page_must_be_exhaustive(self):
        self.fails(lambda d:d["in4"].update(remaining_pageKey="still_more"),
                   "EXACT_PAGINATION_CHAIN")

    def test_seventeen_outbound_events_must_all_be_kept(self):
        self.fails(lambda d:d["in3out2"]["out_page2"]["rows"].pop(),
                   "EXACT_PAGINATION_CHAIN")

    def test_original_router_outbound_destination_cannot_be_swapped(self):
        self.fails(lambda d:d["in2out1"]["results"]["OUTBOUND_PAGE1"]["rows"][0].update(
                 to="0x"+"a"*40),"EXACT_IN_AND_OUT_IDENTITIES")

    def test_duplicate_inbound_hash_detected(self):
        def edit(d):
            x=d["in2out1"]["results"]["INBOUND_PAGE2"]["rows"]
            x[1]["hash"]=x[0]["hash"]
        self.fails(edit,"EXACT_IN_AND_OUT_IDENTITIES")

    def test_one_original_inbound_token_amount_cannot_be_inflated(self):
        self.fails(lambda d:d["in1"]["rows"][0].update(raw_Dragon_received="1"),
                   "FROZEN_RAW_TRANSFER_TOTALS")

    def test_one_outbound_token_amount_cannot_be_erased(self):
        self.fails(lambda d:d["in3out2"]["out_page2"]["rows"][1].update(rawUint="0"),
                   "VALID_ERC20_UINT256_AMOUNTS")

    def test_real_opening_state_must_match_32byte_onchain_return(self):
        self.fails(lambda d:d["state"]["observations"][0].update(rawDecimal="1"),
                   "ACTUAL_CHAIN_BALANCE_HEX_MATCHES_RAW")

    def test_wallet_initial_tokens_not_assumed_free(self):
        self.fails(lambda d:d["state"]["economic_classification"].update(
            wallet_opening_Dragon_before_frozen_window="ZERO_COST_BASIS"),
            "COST_BASIS_STILL_MISSING")

    def test_same_original_real_1000usdt_buy_must_match_end_inventory(self):
        self.fails(lambda d:d["buy"]["external_wallet_dragon_state"].update(
            before_buy_raw="0"),"SAME_5E60_PRE_1000USDT_STATE_AND_NO_PNL_PROMOTION")

    def test_cannot_upgrade_p5_when_only_inventory_closed(self):
        self.fails(lambda d:d["state"].update(P5="APPROVED"),
                   "COST_BASIS_STILL_MISSING")

    def test_source_git_blob_bytes_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for n,p in m.FILES.values():
                shutil.copyfile(m.ROOT/n,root/n)
            self.assertEqual(m.audit(m.load(root))["P5"],"BLOCKED")
            with (root/m.FILES["in4"][0]).open("ab") as f:
                f.write(b" ")
            with self.assertRaisesRegex(ValueError,"P4B_5E60_INVENTORY_GIT_PIN_in4"):
                m.load(root)

if __name__=="__main__":
    unittest.main()
