import json
import unittest
from bsc_meme_address_model_v1_p4c_crosswallet_verified23x19 import ROOT,build,load

class CrossWalletSettledSourceProof(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=load(ROOT)

    def test_exact_frozen_source_replay(self):
        got=build(self.source)
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-23x19-crosswallet-native-verified-matrix-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(got,expected)

    def test_only_two_winning_one_losing_original_source(self):
        got=build(self.source)
        self.assertEqual(len(got["verified_economic_rounds"]),3)
        self.assertEqual([r["token"] for r in got["verified_economic_rounds"]],["龙虾","哈基米 / HAJIMI","龙虾"])
        self.assertEqual([r["net_wei"] for r in got["verified_economic_rounds"]],
                         ["-92169615514614272","268592992917629933","253300282319389315"])
        self.assertEqual((got["summary"]["frozen_wallet_candidates"],got["summary"]["frozen_major_exact_CAs"],got["summary"]["implicit_wallet_CAs"]),(23,19,437))
        self.assertEqual((got["summary"]["verified_native_positive_rounds"],got["summary"]["verified_native_negative_rounds"],got["summary"]["not_economically_audited_cells"]),(2,1,434))
        self.assertEqual(got["summary"]["prior_2026_recent_signed_swap_wallets"],7)

    def test_unknown_wallets_never_promoted_to_winners(self):
        got=build(self.source)
        self.assertEqual(got["summary"]["qualified_public_entry_follower_signals"],0)
        self.assertFalse(got["summary"]["profit_rank_ready"])
        self.assertEqual(got["summary"]["production"],"NO_GO")
        self.assertEqual(sum(f=="NOT_ECONOMICALLY_AUDITED" for w in got["wallets"] for f in w["closed_native_round_flags"]),434)

if __name__=="__main__":
    unittest.main()
