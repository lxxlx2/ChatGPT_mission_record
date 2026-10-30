import copy,json,unittest
from bsc_meme_address_model_v1_p4c_877af_inventory import ROOT,build,load

class Original877afMARSIncompletePriceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.docs=load(ROOT)
    def test_source_pinned_result(self):
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-877af-marscoin-inventory-closed-quote-unresolved-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(build(self.docs),expected)
    def test_two_inventory_closed_but_not_qualified_economic_rounds(self):
        x=build(self.docs)
        self.assertEqual((x["summary"]["original_rounds"],x["summary"]["raw_owner_full_token_quantity_closed"],x["summary"]["receipt_truncated"]),(2,2,6))
        self.assertEqual([r["p2_ledger_index"] for r in x["rounds"]],[37,38])
        self.assertTrue(all(r["remaining_token_inventory_raw"]=="0" and r["raw_tokens_received"]==r["raw_tokens_sent"] for r in x["rounds"]))
        self.assertTrue(all(r["economic_status"]=="OWNER_TOKEN_CLOSE_BUT_NONNATIVE_QUOTE_GAS_UNRESOLVED" and not r["qualified_realized_net_profit"] for r in x["rounds"]))
        self.assertEqual(x["summary"]["qualified_observer_trades"],0)
        self.assertEqual(x["summary"]["production"],"NO_GO")
    def test_forged_inventory_missing_sell(self):
        d=copy.deepcopy(self.docs)
        z=next(x for x in d[1]["results"] if x["round"]==37 and x["direction"]=="OUT" and x["logs"])
        z["logs"][0]["data"]="0x01"
        with self.assertRaises(ValueError):build(d)
    def test_truncated_receipt_cannot_be_silently_success(self):
        d=copy.deepcopy(self.docs)
        d[2]["rows"][0]["status"]="SUCCESS_FULL_RECEIPT"
        with self.assertRaises(ValueError):build(d)
    def test_duplicate_owner_erc20_event_rejected(self):
        d=copy.deepcopy(self.docs)
        z=next(x for x in d[1]["results"] if x["logs"])
        z["logs"].append(copy.deepcopy(z["logs"][0]))
        with self.assertRaises(ValueError):build(d)
    def test_owner_wallet_native_balance_counterfeit_rejected(self):
        d=copy.deepcopy(self.docs)
        d[3]["rows"][0]["delta_wei"]="1"
        with self.assertRaises(ValueError):build(d)
if __name__=="__main__":unittest.main()
