#!/usr/bin/env python3
"""Reviewable 23 wallet x 19 CA historical opportunity evidence gate."""
import copy
import json
import unittest
from bsc_meme_address_model_v1_p4b_wallet_early_grid23x19 import ROOT,load,build

class PreDexWalletGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=load(ROOT)

    def test_exact_reproducible_grid(self):
        actual=build(self.d)
        frozen=json.loads((ROOT/"bsc-meme-address-model-v1-p4b-23x19-early-opportunity-ledger-2026-10-14.json").read_text(encoding="utf-8"))
        self.assertEqual(actual,frozen)

    def test_full_scope_and_unstudied_not_negative(self):
        d=build(self.d)
        s=d["summary"]
        self.assertEqual((s["wallets"],s["major_exact_CAs"],s["implicit_wallet_CA_cells"]),(23,19,437))
        self.assertEqual((s["one_source_proven_owner_signed_pre_dex_buy"],s["remaining_not_audited_owner_early_trade_cells"]),(1,436))
        self.assertEqual(s["existing_recent_major_signed_swap_wallets"],7)
        self.assertEqual((s["market_U_qualified"],s["repeat_profit_ranks"]),(0,0))
        self.assertEqual(s["production"],"NO_GO")
        self.assertTrue(all(w["actual_PnL"]=="UNRESOLVED" and w["qualified_misses"]=="UNRESOLVED" for w in d["wallets"]))

    def test_one_and_only_one_owner_signed_early_buy(self):
        x=build(self.d)
        idx=next(m["i"] for m in x["markets"] if m["token"]=="龙虾")
        ddac=next(w for w in x["wallets"] if w["wallet"].startswith("0xddac928a"))
        self.assertEqual(ddac["early_owner_trade_statuses"][idx],"SIGNED_PRE_DEX_BUY_CONFIRMED")
        self.assertEqual(len(x["known_early_owner_trades"]),1)
        self.assertTrue(all(w["early_owner_trade_statuses"][idx]=="NOT_AUDITED_THIS_STAGE" for w in x["wallets"] if w is not ddac))

    def test_missing_wallet_cannot_pass_cohort(self):
        d=copy.deepcopy(self.d)
        d[0]["wallets"].pop(0)
        with self.assertRaises(ValueError):build(d)

    def test_missing_major_token_cannot_pass(self):
        d=copy.deepcopy(self.d)
        d[1]["rows"].pop(0)
        with self.assertRaises(ValueError):build(d)

    def test_unverified_DDAC_signer_mismatch_fails(self):
        d=copy.deepcopy(self.d)
        d[2]["fact"]["buyer_EOA"]="0x"+"1"*40
        with self.assertRaises(ValueError):build(d)

    def test_false_PnL_source_cannot_be_promoted(self):
        d=copy.deepcopy(self.d)
        d[2]["summary"]["proven_realized_profit"]=1
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
