import copy,json,unittest
from bsc_meme_address_model_v1_p4c_ddac_adff_a83b_five import ROOT,build,load

class FiveOriginalCrossWalletInventorySourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=load(ROOT)

    def test_exact_source_manifest_replay(self):
        got=build(self.source)
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-ddac-adff-a83b-five-inventory-closed-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(got,expected)

    def test_three_owners_two_major_CA_five_closures(self):
        got=build(self.source);s=got["summary"]
        self.assertEqual((s["frozen_wallets"],s["frozen_major_exact_CAs"],s["source_preselected_rounds"]),(3,2,5))
        self.assertEqual((s["verified_owner_signed_chain56_txs"],s["owner_native_historical_blocks_complete"]),(11,11))
        self.assertEqual((s["complete_full_success_receipts"],s["receipt_body_truncated"]),(5,6))
        self.assertEqual((s["p2_positive_native_block_scope"],s["p2_negative_native_block_scope"]),(2,3))
        self.assertEqual(s["source_proven_new_realized_BNB_profit_rounds"],0)
        self.assertEqual(s["source_proven_new_realized_BNB_loss_rounds"],0)
        self.assertEqual(s["production"],"NO_GO")
        self.assertTrue(all(x["raw_inventory_remaining"]=="0" and x["raw_original_token_bought"]==x["raw_original_token_sold"] and x["actual_quote_gas_complete_owner_round"]=="UNRESOLVED" for x in got["rounds"]))

    def test_both_token_transfer_logs_of_one_adff_buy_are_real(self):
        got=build(self.source)
        adff=next(x for x in got["rounds"] if x["p2_index"]==44)
        self.assertEqual(adff["original_signed_txs"][0]["owner_token_log_count"],2)
        self.assertEqual(adff["original_signed_txs"][0]["token_received_raw"],"32546033429758403566")

    def test_truncated_sell_cannot_be_approved_by_forged_status(self):
        d=copy.deepcopy(self.source)
        d[1]["rows"][1]["status"]="FULL_SUCCESS_RECEIPT"
        with self.assertRaises(ValueError):build(d)

    def test_duplicate_event_key_invalid_even_when_real_amount_correct(self):
        d=copy.deepcopy(self.source)
        row=next(z for z in d[4]["rows"] if z["case"]==44 and z["direction"]=="IN")
        event=next(e for e in row["logs"] if e["transactionHash"]==row["hash"])
        row["logs"].append(copy.deepcopy(event))
        with self.assertRaises(ValueError):build(d)

    def test_spoofed_erc20_owner_buy_rejected(self):
        d=copy.deepcopy(self.source)
        row=next(x for x in d[3]["rows"] if x["direction"]=="IN" and x["logs"])
        row["logs"][0]["topics"][2]="0x"+"0"*64
        with self.assertRaises(ValueError):build(d)

    def test_spoofed_eoa_native_balance_rejected(self):
        d=copy.deepcopy(self.source)
        d[5]["rows"][0]["delta_wei"]="1"
        with self.assertRaises(ValueError):build(d)

    def test_removed_chain_event_rejected(self):
        d=copy.deepcopy(self.source)
        row=next(x for x in d[3]["rows"] if x["logs"])
        row["logs"][0]["removed"]=True
        with self.assertRaises(ValueError):build(d)

    def test_negative_case_drop_rejected(self):
        d=copy.deepcopy(self.source)
        d[0]["rounds"].pop(-1)
        with self.assertRaises(ValueError):build(d)

    def test_wbnb_truncated_rpc_not_converted_to_zero_transfers(self):
        d=copy.deepcopy(self.source)
        d[7]["rows"][1]["status"]="COMPLETE"
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":unittest.main()
