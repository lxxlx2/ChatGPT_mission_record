"""Five historical control cases: prefreeze evidence availability, NOT follower PnL."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "bsc-meme-address-model-v1-p4b-five-case-first-seen-u-prefreeze-2026-10-18.json"


def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes((0,)) + raw).hexdigest()


class HistoricalObserverUPreFreeze(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen = json.loads((ROOT / NAME).read_text(encoding="utf-8"))
        cls.sources = {}
        for key, descriptor in cls.frozen["source_manifest"].items():
            raw = (ROOT / Path(descriptor["path"]).name).read_bytes()
            if git_blob(raw) != descriptor["git_blob_sha"]:
                raise AssertionError("HISTORICAL_OBSERVER_SOURCE_SHA_DRIFT:" + key)
            cls.sources[key] = json.loads(raw)

    def test_source_pins_and_23x19_original_membership(self):
        s = self.sources["grid"]
        cases = self.frozen["cases"]
        wallets = {w["wallet"].lower() for w in s["wallets"]}
        markets = {m["ca"].lower() for m in s["markets"]}
        self.assertEqual((len(wallets), len(markets)), (23, 19))
        self.assertEqual(len(cases), 5)
        self.assertEqual(len({c["original_owner"].lower() for c in cases}), 5)
        self.assertEqual(len({c["exact_ca"].lower() for c in cases}), 4)
        for c in cases:
            self.assertIn(c["original_owner"].lower(), wallets)
            self.assertIn(c["exact_ca"].lower(), markets)

    def test_pinned_original_signed_transactions_are_exact(self):
        d = self.sources["ddac"]["round"]
        p = self.sources["239e"]["rounds"][1]
        h = self.sources["8e6b"]["rounds"][0]
        n = self.sources["negatives"]["rounds"]
        expected = [
            (d["owner"], d["exact_CA"], d["entry_tx"], d["entry_block"],
             d["exit_tx"], d["exit_block"], d["native_closed_owner_round_net_wei"]),
            (p["owner"], p["exact_CA"], p["txs"][0]["hash"], p["txs"][0]["block"],
             p["txs"][-1]["hash"], p["txs"][-1]["block"], p["original_native_wallet_net_wei"]),
            (h["owner"], h["exact_CA"], h["buy"][0]["hash"], h["buy"][0]["block"],
             h["sells"][-1]["hash"], h["sells"][-1]["block"], h["actual_native_round_net_wei"]),
        ]
        expected += [(x["wallet"], x["exact_ca"], x["original_transactions"][0]["hash"],
                      x["first_block"], x["original_transactions"][-1]["hash"],
                      x["last_block"], x["native_wallet_block_scope_wei"]) for x in n]
        observed = [(c["original_owner"], c["exact_ca"], c["first_signed_buy_tx"],
                     c["first_signed_buy_block"], c["last_signed_exit_tx"],
                     c["last_selected_exit_block"], c["owner_native_window_wei"])
                    for c in self.frozen["cases"]]
        self.assertEqual(observed, expected)

    def test_positive_and_negative_controls_preserved_not_success_rate(self):
        signs = [c["observed_native_direction"] for c in self.frozen["cases"]]
        self.assertEqual(signs, ["NEGATIVE", "POSITIVE", "POSITIVE", "NEGATIVE", "NEGATIVE"])
        self.assertEqual(self.frozen["scope"]["selected_native_positive"], signs.count("POSITIVE"))
        self.assertEqual(self.frozen["scope"]["selected_native_negative"], signs.count("NEGATIVE"))
        self.assertIn("POSTHOC", self.frozen["selection"])
        companion = next(x for x in self.frozen["known_nonselected_confounders"]
                         if x["case"] == "239E_DRAGON_R1")
        self.assertEqual(companion["net_wei"], self.sources["239e"]["rounds"][0]["original_native_wallet_net_wei"])
        self.assertLess(int(companion["net_wei"]), 0)

    def test_historical_consensus_time_cannot_invent_public_arrival(self):
        f = self.frozen
        self.assertFalse(f["historical_consensus_block_time_is_first_seen"])
        self.assertFalse(f["historical_mempool_first_seen_reconstructible_from_sources"])
        self.assertEqual(f["fixed_observer_delays_seconds"], [60, 300, 900])
        for c in f["cases"]:
            self.assertIsNone(c["first_public_observer_received_utc"])
            self.assertEqual(c["historical_owner_entry_header_utc"], "NOT_AN_OBSERVER_FIRST_SEEN")
            for seconds in (60, 300, 900):
                self.assertEqual(c["observed_executable_route_at_%ss" % seconds], "UNRESOLVED")
            self.assertEqual(c["follower_net_pnl"], "UNRESOLVED")
            self.assertEqual(c["p5_gate"], "BLOCKED")

    def test_no_new_trading_or_deployment_authorization(self):
        self.assertTrue(self.frozen["no_new_rpc_at_prefreeze"])
        self.assertEqual(self.frozen["capital_amount"], "UNRESOLVED_NOT_CHOSEN_BEFORE_EXECUTION_CONTRACT")
        self.assertEqual(self.frozen["exit_policy"], "UNRESOLVED_NOT_CHOSEN_BEFORE_EXECUTION_CONTRACT")
        self.assertEqual(self.frozen["gates"]["PUBLIC_EXECUTABLE_U"], "UNRESOLVED")
        self.assertEqual(self.frozen["gates"]["P5"], "BLOCKED")
        for key in ("NO_MERGE", "NO_DEPLOY", "NO_GMAIL", "NO_TRADE"):
            self.assertTrue(self.frozen["gates"][key])


if __name__ == "__main__":
    unittest.main()
