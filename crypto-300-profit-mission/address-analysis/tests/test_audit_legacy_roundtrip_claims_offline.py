"""Historic positive SINGLE-TOKEN proxy != strict attributable wallet PnL."""
from __future__ import annotations

import copy
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from audit_legacy_roundtrip_claims_offline import (
    BLOBS, ROOT, load, reconcile,
)


class HistoricalClaimGradesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = load(ROOT)

    def inputs(self):
        return copy.deepcopy(self.sources)

    def test_three_legacy_proxies_six_distinct_token_rounds_no_strict_net(self):
        out = reconcile(self.inputs())
        self.assertEqual(out["wallets_screened"], 449)
        self.assertEqual(out["active_candidates"], 237)
        self.assertEqual(out["historic_positive_single_token_block_cashflow_examples"], 3)
        self.assertEqual(out["examples_already_in_canonical_five"], 2)
        self.assertEqual(out["distinct_known_closed_token_cases_across_two_ledgers"], 6)
        self.assertEqual(out["strict_attributable_net_trade_pnl_cases"], 0)
        self.assertEqual(out["fully_audited_whole_wallet_30d_and_lifetime"], 0)
        self.assertEqual([x["source_row"] for x in out["cases"]], [2, 4, 16])
        self.assertTrue(all(x["strict_attributed_net_pnl"] is None
                            for x in out["cases"]))

    def test_sauce_exact_integer_wei_values_but_not_verified_profit(self):
        rows = {r["source_row"]: r for r in reconcile(self.inputs())["cases"]}
        self.assertEqual(rows[2]["cashflow_proxy_bnb"],
                         "0.156828105278687674")
        self.assertEqual(rows[4]["cashflow_proxy_bnb"],
                         "0.154215798043203099")
        self.assertEqual(rows[2]["proxy_precision"],
                         "EXACT_INTEGER_WEI_BLOCK_BALANCE_DELTAS")
        self.assertIsNone(rows[4]["strict_attributed_net_pnl"])

    def test_rtx_float_archive_does_not_claim_exact_integer_wei(self):
        rtx = [x for x in reconcile(self.inputs())["cases"]
               if x["source_row"] == 16][0]
        self.assertEqual(rtx["proxy_precision"],
                         "FLOAT_ORIGIN_APPROXIMATE_NOT_INTEGER_WEI")
        self.assertTrue(rtx["cashflow_proxy_bnb"].startswith("0.226099333"))
        self.assertIsNone(rtx["strict_attributed_net_pnl"])

    def test_wrong_sauce_cashflow_rejected(self):
        data = self.inputs()
        data["sauce"]["roundtrips"][0]["net_gain_wei"] = "0"
        with self.assertRaisesRegex(
                ValueError, "SAUCE_PROXY_OR_GRADE_MISMATCH"):
            reconcile(data)

    def test_wrong_legacy_wallet_or_token_inventory_rejected(self):
        data = self.inputs()
        data["rtx"]["wallet"] = "0x" + "f" * 40
        with self.assertRaisesRegex(
                ValueError, "RTX_SOURCE_OR_POSITION_INVALID"):
            reconcile(data)
        data = self.inputs()
        data["sauce"]["roundtrips"][0]["balance_of_raw"]["after_sale"] = "1"
        with self.assertRaisesRegex(
                ValueError, "SAUCE_POSITION_NOT_CLOSED"):
            reconcile(data)

    def test_wrong_rtx_float_net_change_rejected(self):
        data = self.inputs()
        data["rtx"]["txs"][0]["delta_bnb"] = -0.2
        with self.assertRaisesRegex(
                ValueError, "RTX_FLOAT_CASHFLOW_RECONCILE_FAIL"):
            reconcile(data)

    def test_freeze_mutation_stops_loading(self):
        with tempfile.TemporaryDirectory() as home:
            root = Path(home)
            for relative, _digest in BLOBS.values():
                dest = root / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((ROOT / relative).read_bytes())
            target = root / BLOBS["rtx"][0]
            target.write_bytes(target.read_bytes() + b" ")
            with self.assertRaisesRegex(
                    ValueError, "HISTORICAL_SOURCE_BLOB_CHANGED_rtx"):
                load(root)

    def test_no_network_or_execution_paths(self):
        with (patch("http.client.HTTPSConnection",
                    side_effect=AssertionError("NO_HTTPS")) as https,
              patch.object(socket, "create_connection",
                           side_effect=AssertionError("NO_SOCKET")) as sock):
            out = reconcile(self.inputs())
            self.assertEqual(out["mode"],
                             "FROZEN_EVIDENCE_OFFLINE_NO_NEW_RPC")
            https.assert_not_called()
            sock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
