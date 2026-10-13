#!/usr/bin/env python3
"""P4 bounded historical funding evidence, strict source SHA and no-alpha gates."""
from __future__ import annotations

import copy
import unittest

from bsc_meme_address_model_v1_p4_funding import DIR, FILE_SHA, ROOT, build, load


class P4FundingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load(ROOT)
        cls.result = build(cls.data)

    def test_scope_23_preserved_and_four_precommitted_only(self):
        d = self.result
        self.assertEqual((d["summary"]["wallets"], d["summary"]["funding_probed_wallets"],
                          d["summary"]["other_wallets_unprobed"]), (23, 4, 19))
        self.assertEqual(len({w["wallet"] for w in d["wallets"]}), 23)
        self.assertEqual(len(d["source_manifest"]), len(FILE_SHA))
        self.assertTrue(all(i["path"].startswith(DIR) for i in d["source_manifest"]))

    def test_direct_native_and_quote_snapshots_are_wei_exact(self):
        funded = [w for w in self.result["wallets"] if "nonce_pre_swap" in w]
        self.assertEqual(len(funded), 4)
        bnb = {w["wallet"][:6]: w["observed_native_bnb_pre_swap_BNB"] for w in funded}
        self.assertEqual(bnb, {"0xadff":"4.860355826768457125",
                               "0x8e6":"5.771517369306080363",
                               "0x2ad":"0.31522943205986517",
                               "0xddac":"64.285482295034007645"})
        self.assertTrue(all(w["nonce_pre_swap"] > 0 for w in funded))
        ddac = next(w for w in funded if w["wallet"].startswith("0xddac"))
        self.assertEqual(ddac["observed_wbnb_pre_swap_raw_wei"], "1301171035371946752")
        self.assertEqual(ddac["observed_usdt_pre_swap_raw_18_decimals"], "786450040245340209842")

    def test_native_external_inbound_complete_but_not_all_funding(self):
        w = {x["wallet"][:7]: x for x in self.result["wallets"]
             if "window_external_BNB_inbound_count" in x}
        self.assertEqual([w[k]["window_external_BNB_inbound_count"]
                          for k in ("0xadffb","0x8e6b3","0x2adf9","0xddac9")], [9,1,0,10])
        self.assertEqual(self.result["summary"]["native_external_inbound_records"], 20)
        self.assertEqual(self.result["summary"]["shared_external_native_sender_in_scope"], 0)
        self.assertEqual(self.result["summary"]["control_attribution_proven"], 0)
        self.assertTrue(all(v["common_controller"] == "UNRESOLVED" for v in w.values()))

    def test_ddac_quote_inbound_kept_partial_no_false_completion(self):
        self.assertEqual(self.result["summary"]["selected_quote_windows_fully_paginated"], 3)
        self.assertEqual(self.result["summary"]["selected_quote_windows_partial"], 1)
        self.assertEqual(self.result["summary"]["known_selected_ERC20_inbound_records"], 28)
        ddac = next(x for x in self.result["wallets"] if x["wallet"].startswith("0xddac"))
        self.assertEqual(ddac["selected_WBNB_USDT_inbound_state"], "PARTIAL_FIRST_25_EVENTS")
        self.assertEqual(ddac["selected_WBNB_USDT_inbound_events_known"], 25)
        self.assertEqual(ddac["original_funding_attribution"], "UNRESOLVED")

    def test_missing_provider_page_must_fail(self):
        d = copy.deepcopy(self.data)
        d["bsc-meme-address-model-v1-p4-funding4-external-native-inbound-2026-10-13.json"]["wallets"][0]["pageKey"] = "fake"
        with self.assertRaises(ValueError):
            build(d)

    def test_fabricated_quote_completion_must_fail(self):
        d = copy.deepcopy(self.data)
        d["bsc-meme-address-model-v1-p4-ddac-inbound-erc20-first25-partial-2026-10-13.json"]["completed"] = True
        with self.assertRaises(ValueError):
            build(d)

    def test_no_pnl_copy_trading_or_eligible_miss_promoted(self):
        r = self.result
        self.assertEqual(r["summary"]["qualified_major_opportunity_misses"], "UNRESOLVED")
        self.assertEqual(r["summary"]["production"], "NO_GO")
        self.assertTrue(all(w["qualified_missed_opportunity"] == "UNRESOLVED"
                            and w["realized_PnL"] == "UNRESOLVED"
                            and w["common_controller"] == "UNRESOLVED"
                            for w in r["wallets"]))
        self.assertEqual(len([w for w in r["wallets"]
                              if w.get("historical_funding_probe") == "UNRESOLVED_NO_SNAPSHOT"]),19)


if __name__ == "__main__":
    unittest.main()
