#!/usr/bin/env python3
"""Historical fixed-size PancakeSwap V2 quote test contract: no false fills or tax claim."""
import copy
import json
import unittest
from bsc_meme_address_model_v1_p4b_router_quotes19 import ROOT,load,build

class HistoricalRouterQuotes19Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources=load(ROOT)

    def test_freeze_and_complete_exact_replay(self):
        actual=build(self.sources)
        frozen=json.loads((ROOT/"bsc-meme-address-model-v1-p4b-19ca-v2-001wbnb-router-math-quotes-2026-10-14.json").read_text(encoding="utf-8"))
        self.assertEqual(actual,frozen)

    def test_all_nineteen_and_original_fixed_size(self):
        actual=build(self.sources)
        self.assertEqual(len(actual["rows"]),19)
        self.assertEqual(len({r["exact_CA"] for r in actual["rows"]}),19)
        self.assertEqual(actual["summary"]["reserve_formula_cross_checks_passed"],19)
        self.assertEqual(actual["summary"]["fixed_input_WBNB_wei"],"10000000000000000")
        self.assertEqual(actual["summary"]["production"],"NO_GO")
        self.assertTrue(all(x["historical_read_block"]==x["first_positive_reserves_block"]+1 for x in actual["rows"]))

    def test_high_price_impact_still_not_treated_as_actual_loss(self):
        r=build(self.sources)["rows"]
        mars=next(x for x in r if x["token"]=="MARSCOIN")
        self.assertGreater(mars["spot_mid_vs_router_output_gap_bps"],9000)
        self.assertEqual(mars["historical_reverse_sell"],"UNRESOLVED")
        self.assertEqual(mars["gas_and_actual_execution"],"UNRESOLVED")
        self.assertTrue(all(x["historical_token_transfer_simulation"]=="NOT_PERFORMED"
                            and x["global_market_first_U"]=="UNRESOLVED"
                            and x["qualified_23_wallet_opportunity"]=="UNRESOLVED"
                            and x["production"]=="NO_GO" for x in r))

    def test_same_original_block_and_pool_mandatory(self):
        d=copy.deepcopy(self.sources)
        d[1]["rows"][0]["read_block"]+=1
        with self.assertRaises(ValueError):build(d)
        d=copy.deepcopy(self.sources)
        d[1]["rows"][0]["pool"]="0x"+"0"*40
        with self.assertRaises(ValueError):build(d)

    def test_unverified_tax_not_promoted_to_execution(self):
        d=copy.deepcopy(self.sources)
        d[1]["rows"][0]["no_token_transfer_executed"]=False
        with self.assertRaises(ValueError):build(d)

    def test_router_out_must_equal_exact_state_swap_math(self):
        d=copy.deepcopy(self.sources)
        row=d[1]["rows"][0]
        hexvalue=row["raw_router_buy_quote"]
        row["raw_router_buy_quote"]=hexvalue[:-1]+("f" if hexvalue[-1]!="f" else "e")
        with self.assertRaises(ValueError):build(d)

    def test_forged_reserve_or_wrong_abi_format_rejected(self):
        d=copy.deepcopy(self.sources)
        d[1]["rows"][1]["raw_getReserves"]="0x"+"0"*192
        with self.assertRaises(ValueError):build(d)
        d=copy.deepcopy(self.sources)
        d[1]["rows"][1]["raw_router_buy_quote"]="0x"+("0"*64)
        with self.assertRaises(ValueError):build(d)

    def test_missing_pool_is_not_inferred_empty(self):
        d=copy.deepcopy(self.sources)
        d[3]["rows"].pop()
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
