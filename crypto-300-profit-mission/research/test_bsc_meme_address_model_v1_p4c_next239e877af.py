import copy
import json
import unittest
from bsc_meme_address_model_v1_p4c_next239e877af import ROOT,build,load

class Fresh239E877AFOriginalSignedRoundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=load(ROOT)

    def test_replay_matches_immutable_git_economics_grade(self):
        got=build(self.source)
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-next239e877af-four-signers-reconciled-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(got,expected)

    def test_four_balanced_no_false_profit(self):
        a=build(self.source)
        self.assertEqual((a["summary"]["wallets"],a["summary"]["tokens"],a["summary"]["rounds"]),(2,2,4))
        self.assertEqual(a["summary"]["owner_verified_bnb_chain56_txs"],11)
        self.assertEqual((a["summary"]["original_native_block_scope_positive"],a["summary"]["original_native_block_scope_negative"]),(2,2))
        self.assertEqual(a["summary"]["profit_rounds_newly_source_qualified"],0)
        self.assertEqual(a["summary"]["production"],"NO_GO")
        self.assertTrue(all(x["actual_original_quote_Gas_full_PnL"]=="UNRESOLVED" for x in a["rounds"]))

    def test_signed_tx_wallet_swap_must_fail(self):
        d=copy.deepcopy(self.source)
        d[1]["rows"][0]["rpc"]["from"]="0x"+"0"*40
        with self.assertRaises(ValueError):build(d)

    def test_signer_chain_id_spoof_must_fail(self):
        d=copy.deepcopy(self.source)
        d[2]["rows"][0]["rpc"]["chainId"]="0x1"
        with self.assertRaises(ValueError):build(d)

    def test_past_positive_only_sample_cherry_pick_rejected(self):
        d=copy.deepcopy(self.source)
        d[0]["rounds"]=d[0]["rounds"][::2]
        with self.assertRaises(ValueError):build(d)

    def test_extra_unoriginal_transaction_rejected(self):
        d=copy.deepcopy(self.source)
        d[2]["rows"].append(copy.deepcopy(d[2]["rows"][0]))
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
