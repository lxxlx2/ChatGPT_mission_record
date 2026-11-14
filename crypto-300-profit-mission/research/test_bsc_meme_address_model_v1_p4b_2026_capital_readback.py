#!/usr/bin/env python3
"""Adversarial tests for P4-B 2026 pre-frozen multi-market capital readbacks."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_2026_capital_readback as gate

class CapitalReadbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good = gate.load()

    def rejected(self, mutate):
        data = copy.deepcopy(self.good)
        mutate(data)
        with self.assertRaises(ValueError):
            gate.build(data)

    def test_positive_replay_is_not_p5_or_actual_u(self):
        actual = gate.build(self.good)
        self.assertEqual(actual["summary"]["market_CAs"], 4)
        self.assertEqual(actual["summary"]["selected_original_wallet_cases"], 5)
        self.assertEqual(actual["summary"]["frozen_wallet_CA_universe"], 437)
        self.assertEqual(actual["summary"]["qualified_public_executable_U"], 0)
        self.assertEqual(actual["summary"]["P5"], "BLOCKED")
        self.assertEqual(actual["summary"]["marscoin_exact_CA_no_sell_proven_blocks"], [112441395])
        self.assertEqual(actual["summary"]["marscoin_unresolved_truncated_blocks"],
                         [112441396,112441397])
        self.assertTrue(all(c["publicly_observable_U"] == "UNRESOLVED" for c in actual["cases"]))
        self.assertTrue(all(c["native_at_N_wei"] == c["native_at_Nplus1_wei"]
                            for c in actual["cases"]))

    def test_change_wallet_identity_fails(self):
        self.rejected(lambda d: d["readback"]["balance_cases"][0].update(wallet="0xdead"))

    def test_change_signed_observer_block_fails(self):
        self.rejected(lambda d: d["readback"]["balance_cases"][2].update(N=115628770))

    def test_missing_case_fails(self):
        self.rejected(lambda d: d["readback"]["balance_cases"].pop())

    def test_quote_asset_swap_fails(self):
        self.rejected(lambda d: d["readback"]["balance_cases"][2].update(
            quote_ca="0xbe9d156892e55e7154bcd3cb0fea677f9d3103e1"))

    def test_native_balance_nonmatching_fails(self):
        self.rejected(lambda d: d["readback"]["balance_cases"][1].update(
            amount_at_Nplus1_hex="0x1"))

    def test_missing_early_witness_becomes_fake_signal_fails(self):
        self.rejected(lambda d: d["freeze"]["cases"][3].update(
            original_signed_buy_block=73658906, post_witness_block=73658907))

    def test_marscoin_truncated_block_faked_no_sale_fails(self):
        self.rejected(lambda d: d["readback"]["marscoin_sell_checks"][1].update(
            response_status="COMPLETE_JSON", exact_CA_events=0))

    def test_forged_marscoin_full_window_negative_fails(self):
        self.rejected(lambda d: d["readback"]["marscoin_sell_checks"][0].update(
            block=112441403))

    def test_p5_promotion_fails(self):
        self.rejected(lambda d: d["readback"]["gates"].update(P5="PASS"))

    def test_history_blob_tamper_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, _ in gate.SOURCES.values():
                shutil.copyfile(gate.ROOT / name, root / name)
            self.assertEqual(gate.build(gate.load(root))["summary"]["market_CAs"], 4)
            with (root / gate.SOURCES["readback"][0]).open("ab") as f:
                f.write(b" ")
            with self.assertRaisesRegex(ValueError, "P4B_2026_CAPITAL_SOURCE_DRIFT_readback"):
                gate.load(root)

if __name__ == "__main__":
    unittest.main()
