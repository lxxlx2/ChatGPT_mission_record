import copy,json,unittest
from bsc_meme_address_model_v1_p4c_8e6b_external19 import ROOT,build,load

class Token4All19ExternalEOABlockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.raw=load(ROOT)
    def test_pinned_replay_matches_original_and_final(self):
        actual=build(self.raw)
        saved=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-8e6b-token4-all19-external-exclusivity-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(actual,saved)
    def test_19_exact_owner_only_blocks_not_internal_trace_claim(self):
        o=build(self.raw);s=o["summary"]
        self.assertEqual((s["original_selected_tx_blocks"],s["all_original_owner_external_tx_block_proven"],s["owner_blocks_with_other_external_native_sender"],s["owner_blocks_with_external_native_inbound"],s["provider_truncated_or_pagekey"]),(19,19,0,0,0))
        self.assertEqual(s["internal_native_trace_status"],"UNRESOLVED")
        self.assertEqual(s["public_executable_U"],"UNRESOLVED")
        self.assertEqual(s["followable_signals"],0)
        self.assertEqual(s["production"],"NO_GO")
    def test_unrelated_same_block_external_transfer_rejected(self):
        x=copy.deepcopy(self.raw);x[1]["rows"][0]["directions"][0]["transfers"].append(copy.deepcopy(x[1]["rows"][0]["directions"][0]["transfers"][0]))
        with self.assertRaises(ValueError):build(x)
    def test_native_external_inbound_rejected(self):
        x=copy.deepcopy(self.raw);x[2]["rows"][0]["directions"][1]["transfers"].append(copy.deepcopy(x[2]["rows"][0]["directions"][0]["transfers"][0]))
        with self.assertRaises(ValueError):build(x)
    def test_pagination_unresolved_fails(self):
        x=copy.deepcopy(self.raw);x[3]["rows"][0]["directions"][0]["page_key_present"]=True
        with self.assertRaises(ValueError):build(x)
    def test_owner_signer_spoof_rejected(self):
        x=copy.deepcopy(self.raw);x[4]["rows"][0]["directions"][0]["transfers"][0]["from"]="0x"+"1"*40
        with self.assertRaises(ValueError):build(x)
    def test_new_block_without_precommit_rejected(self):
        x=copy.deepcopy(self.raw);x[4]["rows"][0]["block"]+=1
        with self.assertRaises(ValueError):build(x)
if __name__=="__main__":unittest.main()
