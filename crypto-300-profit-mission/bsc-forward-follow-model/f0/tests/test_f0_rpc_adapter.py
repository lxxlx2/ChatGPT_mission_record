import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_rpc_adapter import (block_candidates, receipt_observation,
                            decode_get_amounts_out, transfer_log, envelope)

DATA = json.loads((ROOT / "fixtures/rpc_envelopes.json").read_text())
WATCH = set(DATA["watchlist"])
ROUTERS = set(DATA["routers"])
QUOTES = set(DATA["quote_assets"])


def source():
    return copy.deepcopy(DATA)


def detected(d):
    return block_candidates(d["block"], WATCH, ROUTERS)


def receipt(d):
    c = detected(d)["candidates"][0]
    return receipt_observation(d["receipt"], c, d["tip_number"], QUOTES, ROUTERS)


class RPCTest(unittest.TestCase):
    def test_block_watchlist_and_control(self):
        out = detected(source())
        self.assertEqual(out["full_block_tx_count"], 3)
        self.assertEqual([v["group"] for v in out["candidates"]],
                         ["WATCHLIST", "CONTROL_CANDIDATE"])
        self.assertEqual(out["e3_actual_count"], 0)
        self.assertEqual([v["direction"] for v in out["candidates"]], ["UNKNOWN"] * 2)

    def test_receipt_is_hint_not_attestation(self):
        r = receipt(source())
        self.assertEqual(r["side_hint"], "BUY_CANDIDATE")
        self.assertEqual(r["reason"], "UNVERIFIED_SWAP_ROUTE")
        self.assertFalse(r["E2_attested"])
        self.assertEqual(r["finality"], "UNRESOLVED_F1_POLICY")
        self.assertEqual(r["confirmations_seen"], 4)

    def test_quote_is_never_live(self):
        q = decode_get_amounts_out(DATA["quote"], 2)
        self.assertEqual(q["status"], "SIMULATED_ARCHIVE_QUOTE")
        self.assertEqual(q["amount_out_raw"], "900")
        self.assertEqual(q["quoted_actual_count"], 0)

    def test_quote_failure_modes(self):
        for mutation in ({"result": None}, {"error": {"code": -32000}},
                         {"result": "0x"}, {"result": "0x123"},
                         {"result": "0x" + "0" * 64 * 4},
                         {"result": DATA["quote"]["result"][:-64]},
                         {"result": DATA["quote"]["result"] + "0" * 64}):
            with self.subTest(mutation=str(mutation)[:50]):
                r = {"jsonrpc": "2.0", "id": 9, **mutation}
                self.assertEqual(decode_get_amounts_out(r, 2)["status"], "NO_QUOTE")

    def test_malformed_hash_only_block_fails(self):
        d = source(); d["block"]["result"]["transactions"][0] = "0x" + "0" * 64
        with self.assertRaisesRegex(ValueError, "HASH_ONLY_BLOCK"):
            detected(d)

    def test_tx_number_mismatch_fails(self):
        d = source(); d["block"]["result"]["transactions"][0]["blockNumber"] = "0x33"
        with self.assertRaisesRegex(ValueError, "BLOCK_NUMBER_MISMATCH"):
            detected(d)

    def test_duplicate_tx_fails(self):
        d = source(); t = d["block"]["result"]["transactions"]
        t.append(copy.deepcopy(t[0]))
        with self.assertRaisesRegex(ValueError, "DUPLICATE_TRANSACTION"):
            detected(d)

    def test_tx_wallet_normalizes_case(self):
        d = source(); mixed = '0x' + 'Ab' * 20
        d['block']['result']['transactions'][0]['from'] = mixed
        out = block_candidates(d['block'], {mixed.lower()}, ROUTERS)
        self.assertEqual(out['candidates'][0]['group'], 'WATCHLIST')
        self.assertEqual(out['candidates'][0]['wallet'], mixed.lower())

    def test_reorg_receipt_block_hash_mismatch(self):
        d = source(); d["receipt"]["result"]["blockHash"] = "0x" + "e" * 64
        with self.assertRaisesRegex(ValueError, "RECEIPT_BLOCK_IDENTITY_MISMATCH"):
            receipt(d)

    def test_receipt_failed_is_not_buy(self):
        d = source(); d["receipt"]["result"]["status"] = "0x0"
        r = receipt(d)
        self.assertEqual(r["side_hint"], "UNKNOWN")
        self.assertFalse(r["receipt_success"])

    def test_quote_transfer_missing_does_not_infer_buy(self):
        d = source(); d["receipt"]["result"]["logs"].pop()
        r = receipt(d)
        self.assertEqual(r["side_hint"], "UNKNOWN")
        self.assertFalse(r["E2_attested"])

    def test_fake_transfer_topic_rejected(self):
        d = source(); d["receipt"]["result"]["logs"][0]["topics"][0] = "0x" + "a" * 64
        r = receipt(d)
        self.assertEqual(r["side_hint"], "UNKNOWN")

    def test_duplicate_log_index_fails(self):
        d = source(); logs = d["receipt"]["result"]["logs"]
        logs[1]["logIndex"] = logs[0]["logIndex"]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_LOG_INDEX"):
            receipt(d)

    def test_malformed_address_transfer_topic_fails(self):
        d = source(); d["receipt"]["result"]["logs"][0]["topics"][1] = "0x" + "f" * 64
        with self.assertRaisesRegex(ValueError, "NON_ADDRESS_TOPIC"):
            receipt(d)

    def test_wrong_recipient_is_not_wallet_buy(self):
        d = source(); logs = d["receipt"]["result"]["logs"]
        logs[0]["topics"][2] = "0x" + "0" * 24 + "f" * 40
        self.assertEqual(receipt(d)["side_hint"], "UNKNOWN")

    def test_sell_recognition_is_only_provisional(self):
        d = source(); logs = d["receipt"]["result"]["logs"]
        wallet = next(iter(WATCH))
        logs[0]["topics"][1] = "0x" + "0" * 24 + wallet[2:]
        logs[0]["topics"][2] = "0x" + "0" * 24 + "e" * 40
        logs[1]["topics"][1] = "0x" + "0" * 24 + "e" * 40
        logs[1]["topics"][2] = "0x" + "0" * 24 + wallet[2:]
        self.assertEqual(receipt(d)["side_hint"], "SELL_CANDIDATE")
        self.assertFalse(receipt(d)["E2_attested"])

    def test_rpc_error_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "RPC_ERROR"):
            envelope({"jsonrpc": "2.0", "id": 1, "error": {"code": -32000}})

    def test_prohibition_of_unmarked_live_fixture(self):
        import subprocess
        import tempfile
        d = source(); d["trial"] = False
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "fixture.json"
            p.write_text(json.dumps(d))
            r = subprocess.run([sys.executable, str(ROOT / "f0_rpc_adapter.py"),
                                "--fixture", str(p)], capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("LIVE_OR_UNMARKED_FIXTURE_FORBIDDEN", r.stderr)


if __name__ == "__main__":
    unittest.main()
