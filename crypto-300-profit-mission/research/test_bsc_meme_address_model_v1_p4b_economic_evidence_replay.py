"""Offline replay of pinned BSC research evidence; NEVER establishes trading PnL."""
import hashlib
import json
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PINS = {
    "transcript": ("bsc-meme-address-model-v1-p4b-alchemy-16-live-tool-response-transcript-2026-10-19.json", "39b82f66b3e55b59156f8a2b9847c32128a80a76"),
    "balance": ("bsc-meme-address-model-v1-p4b-8e6b-2adf-historical-balanceof-raw-rpc-2026-10-19.json", "caace6ceccb0be7a5f4791947673313db4e1b017"),
    "transactions": ("bsc-meme-address-model-v1-p4b-8e6b-2adf-eight-source-txs-full-input-receipt-hex-fields-2026-10-19.json", "c915c4999507ebc5ade2a9767c3e91cca0f76dfe"),
    "continuity": ("bsc-meme-address-model-v1-p4b-8e6b-2adf-full-window-bnb-continuity-review-2026-10-19.json", "c2ab84de7cd28fe865c6b1f249140c6d152808fe"),
    "selected": ("bsc-meme-address-model-v1-p4b-8e6b-2adf-adjacent-approve-swap-gas-attributed-native-balance-2026-10-19.json", "b626f75f44d288a8d6575d4d0196f19ab498807a"),
    "blocks": ("bsc-meme-address-model-v1-p4b-8e6b-2adf-signed-round-bnb-block-delta-unattributed-2026-10-19.json", "c183cba46094956bfc831c8ed6f99b0b1920a0e0"),
    "flow": ("bsc-meme-address-model-v1-p4b-8e6b-2adf-two-new-ca-complete-token-flow-2026-10-19.json", "178f832c3008a589dedf574cef7af2def89ba09e"),
}


def original_git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


class BscEconomicEvidenceReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {
            key: json.loads((ROOT / name).read_text(encoding="utf-8"))
            for key, (name, _) in PINS.items()
        }
        cls.calls = cls.documents["transcript"]["records"]
        cls.transactions_by_hash = {
            entry["tx_hash"].lower(): entry
            for entry in cls.documents["transactions"]["transactions"]
        }
        cls.rpc_transactions_by_hash = {
            entry["args"]["transactionHash"].lower(): json.loads(entry["connector_body_text_exact"])
            for entry in cls.calls if entry["kind"] == "eth_getTransactionByHash"
        }

    def test_all_evidence_files_fixed_to_reviewed_git_blob_hashes(self):
        for kind, (name, expected) in PINS.items():
            with self.subTest(kind=kind):
                self.assertEqual(original_git_blob_sha((ROOT / name).read_bytes()), expected)

    def test_same_execution_connector_capture_records_are_explicitly_bounded(self):
        self.assertEqual(len(self.calls), 17)
        self.assertEqual(sum(x["kind"] == "historical_eth_call" for x in self.calls), 9)
        self.assertEqual(sum(x["kind"] == "eth_getTransactionByHash" for x in self.calls), 8)
        self.assertIn("NOT_INDEPENDENTLY_ATTESTED", self.documents["transcript"]["provenance_level"])
        for row in self.calls:
            with self.subTest(subject=row["subject"]):
                self.assertEqual(row["status"], "SUCCEEDED")
                started = datetime.fromisoformat(row["request_started_utc"].replace("Z", "+00:00"))
                finished = datetime.fromisoformat(row["response_received_utc"].replace("Z", "+00:00"))
                self.assertLessEqual(started, finished)
                json.loads(row["connector_body_text_exact"])
                self.assertEqual(row["args"]["network"], "bnb-mainnet")

    def test_historical_balanceof_args_and_verbatim_connector_bodies(self):
        calls = {
            (x["args"]["to"].lower(), x["args"]["data"].lower(), x["args"]["blockNumber"]): x
            for x in self.calls if x["kind"] == "historical_eth_call"
        }
        self.assertEqual(len(calls), 9)
        for case in self.documents["balance"]["cases"]:
            wallet = case["wallet"].lower()
            ca = case["ca"].lower()
            keydata = "0x70a08231" + wallet[2:].rjust(64, "0")
            self.assertEqual(len(case["observations"]), 4)
            for obs in case["observations"]:
                with self.subTest(case=case["id"], phase=obs["phase"]):
                    req = obs["rpc_request"]
                    self.assertEqual(req["method"], "eth_call")
                    to, data = req["params"][0]["to"].lower(), req["params"][0]["data"].lower()
                    block = req["params"][1]
                    self.assertEqual((to, data), (ca, keydata))
                    matching = calls[(to, data, block)]
                    raw = json.loads(matching["connector_body_text_exact"])
                    self.assertEqual(raw, obs["original_provider_return_hex"])
                    self.assertEqual(len(raw), 66)
                    self.assertEqual(str(int(raw, 16)), obs["decoded_uint256_raw"])
            by_phase = {x["phase"]: int(x["decoded_uint256_raw"]) for x in case["observations"]}
            self.assertEqual(by_phase["PRE_BUY"], 0)
            self.assertGreater(by_phase["POST_BUY"], 0)
            self.assertEqual(by_phase["POST_LAST_EXIT"], 0)
            self.assertEqual(by_phase["END_30D"], 0)

    def test_flap_partial_sale_balance_checked_from_raw_rpc(self):
        case = next(x for x in self.documents["balance"]["cases"] if x["id"] == "8E6B_FLAP")
        starting = int(next(x["decoded_uint256_raw"] for x in case["observations"] if x["phase"] == "POST_BUY"))
        record = next(x for x in self.calls if x["subject"] == "FLAP_post_first_exit")
        self.assertEqual(record["args"]["blockNumber"], "0x79d77c1")
        self.assertEqual(record["args"]["to"].lower(), case["ca"].lower())
        remaining = int(json.loads(record["connector_body_text_exact"]), 16)
        self.assertGreater(remaining, 0)
        self.assertLess(remaining, starting)

    def test_full_signed_transaction_calldata_and_identity_match_new_capture(self):
        self.assertEqual(len(self.transactions_by_hash), 8)
        self.assertEqual(len(self.rpc_transactions_by_hash), 8)
        for tx_hash, archived in self.transactions_by_hash.items():
            with self.subTest(tx=tx_hash):
                original = self.rpc_transactions_by_hash[tx_hash]
                fields = archived["original_rpc_fields"]
                for prop in ("hash", "from", "to", "input", "value", "nonce",
                             "blockNumber", "transactionIndex", "type", "gasPrice"):
                    self.assertEqual(original[prop].lower(), fields[prop].lower())
                is_approve = archived["role"].startswith("APPROVE")
                self.assertEqual(len(fields["input"]), 138 if is_approve else 1930)
                if is_approve:
                    self.assertTrue(fields["input"].startswith("0x095ea7b3"))
                    self.assertIn("1de460f363af910f51726def188f9004276bf4bc", fields["input"])
                    self.assertEqual(archived["receipt_original_hex_fields"]["gasUsed"], "0xbf58")
                else:
                    self.assertTrue(fields["input"].startswith("0x4d819a2a"))
                    self.assertIsNone(archived["receipt_original_hex_fields"]["gasUsed"])
                    self.assertTrue(archived["receipt_text_truncated_by_connector"])
                self.assertEqual(archived["receipt_original_hex_fields"]["status"], "0x1")

    def test_token_in_out_and_entry_and_last_exit_positions(self):
        balances = {x["wallet"].lower(): x for x in self.documents["balance"]["cases"]}
        for flow in self.documents["flow"]["cases"]:
            with self.subTest(id=flow["id"]):
                raw_in = sum(int(v, 16) for e in flow["incoming"] for v in e["raw"])
                raw_out = sum(int(v, 16) for e in flow["outgoing"] for v in e["raw"])
                self.assertEqual(str(raw_in), flow["raw_token_in"])
                self.assertEqual(str(raw_out), flow["raw_token_out"])
                self.assertEqual(raw_in, raw_out)
                balance_case = balances[flow["wallet"].lower()]
                bought = next(x for x in balance_case["observations"] if x["phase"] == "POST_BUY")
                self.assertEqual(raw_in, int(bought["decoded_uint256_raw"]))

    def test_exact_wallet_balance_window_reconciliation_not_token_profit(self):
        blocks = {x["wallet"].lower(): x for x in self.documents["blocks"]["cases"]}
        for segment in self.documents["continuity"]["cases"]:
            with self.subTest(wallet=segment["wallet"]):
                rows = blocks[segment["wallet"].lower()]["rows"]
                selected = sum(int(x["after"]) - int(x["before"]) for x in rows)
                full = int(rows[-1]["after"]) - int(rows[0]["before"])
                middle = sum(int(rows[i]["before"]) - int(rows[i - 1]["after"])
                             for i in range(1, len(rows)))
                signed_gaps = [rows[i]["nonce_before"] - rows[i - 1]["nonce_after"]
                               for i in range(1, len(rows))]
                self.assertEqual(selected, int(segment["selected_block_delta_sum_wei"]))
                self.assertEqual(full, int(segment["continuous_window_wallet_delta_wei"]))
                self.assertEqual(middle, int(segment["all_unselected_gap_delta_wei"]))
                self.assertEqual(selected + middle, full)
                self.assertEqual(signed_gaps,
                                 [x["signed_nonce_count_between_selected_blocks"]
                                  for x in segment["intervening_fragments"]])
                self.assertEqual(segment["round_profitability"], "UNRESOLVED")
                self.assertTrue(all("profit" in x.lower() or "delta" in x.lower()
                                    for x in segment["not_profit_columns"]))

    def test_original_approve_and_swap_cumulative_gas_arithmetic(self):
        gas = self.documents["selected"]["cases"]
        for case in gas:
            with self.subTest(case=case["id"]):
                entry = case["buy"]
                tx = self.transactions_by_hash[entry["hash"].lower()]
                self.assertEqual(int(entry["gas_price_wei"]), int(tx["original_rpc_fields"]["gasPrice"], 16))
                used = int(entry["cumulative_gas_after"], 16) - int(entry["cumulative_gas_before"], 16)
                self.assertEqual(str(used), entry["gas_used_from_adjacent_cumulative"])
                self.assertEqual(used * int(entry["gas_price_wei"]),
                                 int(entry["gas_fee_wei"]))
                self.assertEqual(int(entry["balance_delta_wei"]),
                                 -int(tx["original_rpc_fields"]["value"], 16) - int(entry["gas_fee_wei"]))
                for item in case["exits"]:
                    approve = self.transactions_by_hash[item["approval_hash"].lower()]
                    swap = self.transactions_by_hash[item["swap_hash"].lower()]
                    self.assertEqual(int(approve["original_rpc_fields"]["transactionIndex"], 16) + 1,
                                     int(swap["original_rpc_fields"]["transactionIndex"], 16))
                    self.assertEqual(int(approve["original_rpc_fields"]["nonce"], 16) + 1,
                                     int(swap["original_rpc_fields"]["nonce"], 16))
                    self.assertEqual(approve["original_rpc_fields"]["blockNumber"],
                                     swap["original_rpc_fields"]["blockNumber"])
                    cum_app = int(approve["receipt_original_hex_fields"]["cumulativeGasUsed"], 16)
                    cum_swap = int(swap["receipt_original_hex_fields"]["cumulativeGasUsed"], 16)
                    self.assertEqual(cum_app, int(item["cumulative_gas_approval"], 16))
                    self.assertEqual(cum_swap, int(item["cumulative_gas_swap"], 16))
                    self.assertEqual(int(approve["receipt_original_hex_fields"]["gasUsed"], 16), 48984)
                    self.assertEqual(cum_swap - cum_app, int(item["swap_gas_used_from_adjacent_cumulative"]))
                    self.assertEqual((48984 + cum_swap - cum_app) * int(item["gas_price_wei"]),
                                     int(item["approval_plus_swap_fee_wei"]))

    def test_old_rejected_profit_claim_explicitly_superseded(self):
        selected = self.documents["selected"]
        pointer = selected["supersession_notice"]
        self.assertEqual(pointer["original_rejected_blob_sha"],
                         "1d4ebea38477f35ace3be8528a966d663a8f0807")
        self.assertEqual(pointer["independently_review_rejected_commit"],
                         "94777871756da910be2e1ccbf724d520c82ae69f")
        for case in selected["cases"]:
            self.assertTrue(case["owner_economic_profitability"].startswith("UNRESOLVED"))
            self.assertNotIn("owner_profit_grade", case)
            self.assertNotIn("net_selected_block_pct_of_entry", case)
        self.assertEqual(self.documents["continuity"]["gates"]["PRODUCTION"], "NO_GO")


if __name__ == "__main__":
    unittest.main()
