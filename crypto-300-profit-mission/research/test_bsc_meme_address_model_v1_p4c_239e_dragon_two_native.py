import copy
import json
import unittest
from bsc_meme_address_model_v1_p4c_239e_dragon_two_native import ROOT,build,load

class Original239eTwoRealNativeOutcomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=load(ROOT)

    def test_byte_pinned_result_exact_replay(self):
        got=build(self.src)
        saved=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-239e-dragon-two-owner-native-settlements-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(got,saved)

    def test_negative_and_positive_same_owner_and_CA_not_rank(self):
        d=build(self.src)
        self.assertEqual((d["summary"]["original_closed_owner_rounds"],d["summary"]["owner_native_original_profit_rounds"],d["summary"]["owner_native_original_loss_rounds"]),(2,1,1))
        self.assertEqual([x["original_native_wallet_net_wei"] for x in d["rounds"]],["-15332805033002259","22647938898252522"])
        self.assertEqual(len({x["owner"] for x in d["rounds"]}),1)
        self.assertEqual(len({x["exact_CA"] for x in d["rounds"]}),1)
        self.assertFalse(d["summary"]["profitable_wallet_rank_ready"])
        self.assertEqual(d["summary"]["followable_signals"],0)
        self.assertEqual(d["summary"]["production"],"NO_GO")

    def test_original_full_inventory_and_gas(self):
        a=build(self.src)
        self.assertEqual(sum(len(x["txs"]) for x in a["rounds"]),5)
        self.assertTrue(all(x["token_received_raw"]==x["token_sold_raw"] and x["token_inventory_residual_raw"]=="0" for x in a["rounds"]))
        self.assertTrue(all(int(x["actual_extra_route_delta_wei"])>0 and int(x["original_network_gas_wei"])>0 for x in a["rounds"]))

    def test_actual_native_balance_mismatch_rejected(self):
        d=copy.deepcopy(self.src)
        d[3]["rows"][0]["delta_wei"]="1"
        with self.assertRaises(ValueError):build(d)

    def test_old_source_extra_inbound_external_native_rejected(self):
        d=copy.deepcopy(self.src)
        d[5]["rows"][0]["txs"].append({"hash":"0x"+"1"*64})
        with self.assertRaises(ValueError):build(d)

    def test_double_owner_activity_in_same_block_rejected(self):
        d=copy.deepcopy(self.src)
        d[4]["rows"][0]["txs"].append(d[4]["rows"][0]["txs"][0])
        with self.assertRaises(ValueError):build(d)

    def test_forged_wbnb_withdrawal_rejected(self):
        d=copy.deepcopy(self.src)
        for l in d[2]["rows"][2]["receipt"]["selected_logs"]:
            if l["topics"][0]=="0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65":
                l["data"]="0x1"
        with self.assertRaises(ValueError):build(d)

    def test_forged_token_exit_not_closed_rejected(self):
        d=copy.deepcopy(self.src)
        out=next(x for x in d[1]["results"] if x["round"]==29 and x["direction"]=="OUT" and x["logs"])
        out["logs"][0]["data"]="0x1"
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
