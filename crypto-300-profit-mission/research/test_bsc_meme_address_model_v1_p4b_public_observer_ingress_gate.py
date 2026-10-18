"""Public observer inbox gate tests: synthetic data is NEVER strategy evidence."""
import base64
import copy
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import bsc_meme_address_model_v1_p4b_public_observer_ingress_gate as gate


class PublicObserverIngressEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prefreeze, cls.grid = gate.load_frozen()
        cls.example = cls.prefreeze["cases"][2]

    def valid_event(self):
        row = {
            "event_id": "SYNTHETIC_FIXTURE_ONLY_001",
            "network": "bnb-mainnet",
            "wallet": self.example["original_owner"],
            "exact_ca": self.example["exact_ca"],
            "tx_hash": "0x" + "e" * 64,
            "capture_kind": "PUBLIC_PENDING_TRANSACTION_INGRESS",
            "observer_received_utc": "2026-10-18T10:00:00.000000Z",
            "capture_machine_id": "SYNTHETIC_MAC_ID",
            "provider_id": "SYNTHETIC_PUBLIC_NODE",
            "observer_monotonic_ns": 123456789000,
            "clock_sync": {"sync_state": "REPORTED_SYNCED",
                           "source": "SYNTHETIC_CLOCK",
                           "max_abs_offset_ms": 0.5},
        }
        payload = {"jsonrpc": "2.0", "params": {"result": {
            "hash": row["tx_hash"],
            "from": row["wallet"],
            "to": "0x" + "1" * 40,
            "blockNumber": None,
        }}}
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        row["raw_event_base64"] = base64.b64encode(raw).decode("ascii")
        row["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        return row

    def doc(self, events):
        return {"schema": "BSC_P4B_PUBLIC_OBSERVER_INGRESS_V1", "events": events}

    def check(self, event):
        out = gate.ingest_document(self.doc([event]), self.grid, self.prefreeze)
        return out["records"][0], out["counts"]

    def confirmed_log_event(self):
        x = self.valid_event()
        x["capture_kind"] = "PUBLIC_CONFIRMED_ERC20_TRANSFER_LOG_INGRESS"
        event = {"jsonrpc": "2.0", "method": "eth_subscription", "params": {
            "subscription": "0x" + "f" * 64,
            "result": {
                "removed": False,
                "address": x["exact_ca"],
                "topics": [gate.TRANSFER_TOPIC,
                           "0x" + "0" * 24 + "1" * 40,
                           gate._address_topic(x["wallet"])],
                "transactionHash": x["tx_hash"],
                "blockHash": "0x" + "d" * 64,
                "blockNumber": "0x5200000",
                "logIndex": "0x4",
                "data": "0x" + format(10 ** 18, "064x"),
            }
        }}
        self.replace_event(x, event)
        return x

    def replace_event(self, x, event):
        raw = json.dumps(event, sort_keys=True).encode("utf-8")
        x["raw_event_base64"] = base64.b64encode(raw).decode("ascii")
        x["raw_sha256"] = hashlib.sha256(raw).hexdigest()

    def test_confirmed_token_receipt_is_not_assumed_to_be_owner_signed_buy(self):
        r, summary = self.check(self.confirmed_log_event())
        self.assertEqual(r["state"], "POST_BLOCK_TOKEN_RECEIPT_OBSERVER_CANDIDATE_UNATTESTED")
        self.assertEqual(r["received_erc20_raw"], str(10 ** 18))
        self.assertEqual(r["confirmed_block_number"], 0x5200000)
        self.assertIsNone(r["first_public_observer_received_utc"])
        self.assertEqual(r["tx_original_signer"], "UNRESOLVED_RECEIPT_AND_FROM_NOT_READ")
        self.assertEqual(r["exact_ca_trade_buy_validation"], "UNRESOLVED_TRANSFER_MAY_BE_PASSIVE")
        self.assertEqual(summary["unattested_post_block_transfer_candidates"], 1)
        self.assertEqual(summary["proven_net_profitable_follower"], 0)

    def test_log_wrong_recipient_rejected(self):
        x = self.confirmed_log_event()
        event = json.loads(base64.b64decode(x["raw_event_base64"]))
        event["params"]["result"]["topics"][2] = "0x" + "0" * 24 + "c" * 40
        self.replace_event(x, event)
        self.assertEqual(self.check(x)[0]["reason"], "LOG_NOT_EXACT_ERC20_TRANSFER_TO_OWNER")

    def test_log_wrong_contract_rejected(self):
        x = self.confirmed_log_event()
        event = json.loads(base64.b64decode(x["raw_event_base64"]))
        event["params"]["result"]["address"] = "0x" + "a" * 40
        self.replace_event(x, event)
        self.assertEqual(self.check(x)[0]["reason"], "LOG_CA_OR_TRANSACTION_HASH_MISMATCH")

    def test_removed_log_not_actionable(self):
        x = self.confirmed_log_event()
        event = json.loads(base64.b64decode(x["raw_event_base64"]))
        event["params"]["result"]["removed"] = True
        self.replace_event(x, event)
        self.assertEqual(self.check(x)[0]["reason"], "LOG_REMOVED_REORG_NOT_ACTIONABLE")

    def test_reorg_tombstone_revokes_previous_included_log(self):
        included = self.confirmed_log_event()
        removed = copy.deepcopy(included)
        removed["event_id"] = "SYNTHETIC_REORG_REMOVAL_002"
        raw = json.loads(base64.b64decode(removed["raw_event_base64"]))
        raw["params"]["result"]["removed"] = True
        self.replace_event(removed, raw)
        batch = gate.ingest_document(self.doc([included, removed]), self.grid, self.prefreeze)
        self.assertEqual(batch["counts"]["reorg_revoked"], 1)
        self.assertEqual(batch["counts"]["unattested_post_block_transfer_candidates"], 0)
        self.assertEqual(batch["records"][0]["state"], "REORG_REVOKED_POSTBLOCK_LOG")
        self.assertIsNone(batch["records"][0]["target_windows_utc"])
        self.assertEqual(batch["records"][1]["reason"], "LOG_REMOVED_REORG_NOT_ACTIONABLE")
        self.assertEqual(batch["counts"]["verified_public_executable_U"], 0)

    def test_fake_reorg_tombstone_with_modified_sha_cannot_revoke_original(self):
        included = self.confirmed_log_event()
        removed = copy.deepcopy(included)
        removed["event_id"] = "SYNTHETIC_FAKE_TOMBSTONE"
        raw = json.loads(base64.b64decode(removed["raw_event_base64"]))
        raw["params"]["result"]["removed"] = True
        self.replace_event(removed, raw)
        removed["raw_sha256"] = "f" * 64
        batch = gate.ingest_document(self.doc([included, removed]), self.grid, self.prefreeze)
        self.assertEqual(batch["counts"]["reorg_revoked"], 0)
        self.assertEqual(batch["counts"]["unattested_post_block_transfer_candidates"], 1)
        self.assertEqual(batch["records"][1]["reason"], "RAW_EVENT_SHA256_MISMATCH")

    def test_new_chain_same_tx_new_block_hash_not_revoked(self):
        included = self.confirmed_log_event()
        removed = copy.deepcopy(included)
        removed["event_id"] = "SYNTHETIC_REMOVED_FROM_OTHER_BLOCK"
        raw = json.loads(base64.b64decode(removed["raw_event_base64"]))
        raw["params"]["result"]["removed"] = True
        raw["params"]["result"]["blockHash"] = "0x" + "c" * 64
        self.replace_event(removed, raw)
        batch = gate.ingest_document(self.doc([included, removed]), self.grid, self.prefreeze)
        self.assertEqual(batch["counts"]["reorg_revoked"], 0)
        self.assertEqual(batch["counts"]["unattested_post_block_transfer_candidates"], 1)

    def test_log_zero_token_transfer_rejected(self):
        x = self.confirmed_log_event()
        event = json.loads(base64.b64decode(x["raw_event_base64"]))
        event["params"]["result"]["data"] = "0x" + "0" * 64
        self.replace_event(x, event)
        self.assertEqual(self.check(x)[0]["reason"], "INVALID_LOG_TOKEN_AMOUNT")

    def test_log_with_missing_block_or_wrong_hash_rejected(self):
        x = self.confirmed_log_event()
        event = json.loads(base64.b64decode(x["raw_event_base64"]))
        event["params"]["result"]["blockNumber"] = None
        self.replace_event(x, event)
        self.assertEqual(self.check(x)[0]["reason"], "LOG_MISSING_MINED_BLOCK_OR_INDEX")
        x = self.confirmed_log_event()
        event = json.loads(base64.b64decode(x["raw_event_base64"]))
        event["params"]["result"]["transactionHash"] = "0x" + "a" * 64
        self.replace_event(x, event)
        self.assertEqual(self.check(x)[0]["reason"], "LOG_CA_OR_TRANSACTION_HASH_MISMATCH")

    def test_original_five_historical_cases_have_no_first_seen(self):
        out = gate.historical_summary(self.prefreeze)
        self.assertEqual(out["selected_cases"], 5)
        self.assertEqual(out["usable_public_first_seen_records"], 0)
        self.assertEqual([x["case"] for x in out["cases"]],
                         ["DDAC_DRAGON", "239E_DRAGON_R2", "8E6B_HAJIMI",
                          "A83B_NIULAI", "877AF_MARSCOIN"])
        for row in out["cases"]:
            self.assertIsNone(row["first_public_observer_received_utc"])
            self.assertIsNone(row["target_windows_utc"])
            self.assertEqual(row["observer_60_300_900_real_fills"], "UNRESOLVED")

    def test_offline_candidate_is_unverified_even_if_all_self_reported_fields_match(self):
        record, summary = self.check(self.valid_event())
        self.assertEqual(record["state"], "PENDING_OWNER_TX_CAPTURE_CANDIDATE_UNATTESTED")
        self.assertIsNone(record["first_public_observer_received_utc"])
        self.assertEqual(record["first_local_observer_received_utc_claim"],
                         "2026-10-18T10:00:00.000000Z")
        self.assertEqual(record["target_windows_utc"],
                         {"60": "2026-10-18T10:01:00.000000Z",
                          "300": "2026-10-18T10:05:00.000000Z",
                          "900": "2026-10-18T10:15:00.000000Z"})
        self.assertEqual(summary["verified_public_executable_U"], 0)
        self.assertEqual(summary["proven_net_profitable_follower"], 0)

    def test_historical_real_tx_cannot_be_replayed_as_new_live_observation(self):
        x = self.valid_event()
        x["tx_hash"] = self.example["first_signed_buy_tx"]
        raw = json.dumps({"hash": x["tx_hash"], "from": x["wallet"],
                          "blockNumber": None}).encode()
        x["raw_event_base64"] = base64.b64encode(raw).decode()
        x["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        r, summary = self.check(x)
        self.assertEqual(r["reason"], "FROZEN_HISTORICAL_TX_CANNOT_BE_PROMOTED_TO_LIVE_CAPTURE")
        self.assertEqual(summary["verified_public_executable_U"], 0)

    def test_historical_block_replay_is_not_live_capture(self):
        x = self.valid_event()
        x["capture_kind"] = "HISTORICAL_BLOCK_TIMESTAMP"
        r, _ = self.check(x)
        self.assertEqual(r["reason"], "HISTORICAL_OR_SIMULATED_CAPTURE_NOT_LIVE")
        self.assertIsNone(r["first_public_observer_received_utc"])

    def test_raw_mutation_without_sha_update_rejected(self):
        x = self.valid_event()
        x["raw_sha256"] = "a" * 64
        self.assertEqual(self.check(x)[0]["reason"], "RAW_EVENT_SHA256_MISMATCH")

    def test_forged_tx_hash_inside_raw_rejected(self):
        x = self.valid_event()
        payload = {"hash": "0x" + "a" * 64, "from": x["wallet"], "blockNumber": None}
        raw = json.dumps(payload).encode()
        x["raw_event_base64"] = base64.b64encode(raw).decode()
        x["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        self.assertEqual(self.check(x)[0]["reason"], "RAW_EVENT_TX_HASH_OR_FROM_MISMATCH")

    def test_forged_original_signer_inside_raw_rejected(self):
        x = self.valid_event()
        raw = json.dumps({"hash": x["tx_hash"], "from": "0x" + "a" * 40}).encode()
        x["raw_event_base64"] = base64.b64encode(raw).decode()
        x["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        self.assertEqual(self.check(x)[0]["reason"], "RAW_EVENT_TX_HASH_OR_FROM_MISMATCH")

    def test_confirmed_block_replay_not_pending(self):
        x = self.valid_event()
        raw = json.dumps({"hash": x["tx_hash"], "from": x["wallet"], "blockNumber": "0x5"}).encode()
        x["raw_event_base64"] = base64.b64encode(raw).decode()
        x["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        self.assertEqual(self.check(x)[0]["reason"], "RAW_EVENT_IS_CONFIRMED_BLOCK_REPLAY")

    def test_bare_hash_cannot_verify_real_signer(self):
        x = self.valid_event()
        raw = json.dumps({"hash": x["tx_hash"]}).encode()
        x["raw_event_base64"] = base64.b64encode(raw).decode()
        x["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        self.assertEqual(self.check(x)[0]["reason"], "RAW_EVENT_TX_HASH_OR_FROM_MISMATCH")

    def test_invalid_base64_does_not_crash(self):
        x = self.valid_event()
        x["raw_event_base64"] = "$invalid!"
        self.assertEqual(self.check(x)[0]["reason"], "RAW_EVENT_NOT_BASE64")

    def test_fake_source_wallet_or_out_of_cohort_ca_rejected(self):
        x = self.valid_event()
        x["wallet"] = "0x" + "a" * 40
        self.assertEqual(self.check(x)[0]["reason"], "OUTSIDE_FROZEN_23X19")
        y = self.valid_event()
        y["exact_ca"] = "0x" + "b" * 40
        self.assertEqual(self.check(y)[0]["reason"], "OUTSIDE_FROZEN_23X19")

    def test_non_utc_timestamp_fails_no_fallback(self):
        x = self.valid_event()
        x["observer_received_utc"] = "2026-10-18T17:00:00+07:00"
        self.assertEqual(self.check(x)[0]["reason"], "UTC_Z_REQUIRED")

    def test_clock_unsynchronized_fails(self):
        x = self.valid_event()
        x["clock_sync"]["sync_state"] = "UNKNOWN"
        self.assertEqual(self.check(x)[0]["reason"], "CLOCK_SYNC_CLAIM_MISSING_OR_INVALID")

    def test_monotonic_over_53bit_keeps_exact_decimal_string(self):
        x = self.confirmed_log_event()
        x["observer_monotonic_ns"] = "9007199254740993123"
        r, _ = self.check(x)
        self.assertEqual(r["state"], "POST_BLOCK_TOKEN_RECEIPT_OBSERVER_CANDIDATE_UNATTESTED")

    def test_missing_clock_does_not_promote_unverified_timing(self):
        x = self.confirmed_log_event()
        x["clock_sync"] = {"sync_state": "UNKNOWN",
                           "source": "NO_CALIBRATION_SUPPLIED",
                           "max_abs_offset_ms": None}
        r, _ = self.check(x)
        self.assertEqual(r["reason"], "CLOCK_SYNC_CLAIM_MISSING_OR_INVALID")
        self.assertIsNone(r["first_public_observer_received_utc"])

    def test_node_bounded_collector_default_dry_run_when_node_installed(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("node unavailable on this runner")
        script = str(gate.ROOT / "bsc_meme_address_model_v1_p4b_bounded_postblock_log_collector.js")
        syntax = subprocess.run([node, "--check", script], capture_output=True,
                                text=True, timeout=15)
        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        run = subprocess.run([node, script, "--dry-run", "--duration-seconds", "60",
                              "--max-events", "5"], capture_output=True, text=True,
                             timeout=15)
        self.assertEqual(run.returncode, 0, run.stderr)
        out = json.loads(run.stdout)
        self.assertEqual(out["mode"], "OFFLINE_DRY_RUN_NO_NETWORK")
        self.assertEqual((out["original_wallets"], out["exact_cas"]), (23, 19))
        self.assertEqual(len(out["params"][1]["address"]), 19)
        self.assertEqual(len(out["params"][1]["topics"][2]), 23)
        self.assertEqual(out["params"][0], "logs")
        self.assertEqual(out["production"], "NO_GO")

    def test_boolean_monotonic_clock_fails(self):
        x = self.valid_event()
        x["observer_monotonic_ns"] = True
        self.assertEqual(self.check(x)[0]["reason"], "INVALID_MONOTONIC_CLOCK")

    def test_repeated_record_id_is_rejected_not_replaced(self):
        x = self.valid_event()
        out = gate.ingest_document(self.doc([x, copy.deepcopy(x)]), self.grid, self.prefreeze)
        self.assertEqual(out["counts"]["rejected"], 1)
        self.assertEqual(out["records"][1]["reason"], "DUPLICATE_OR_MISSING_EVENT_ID")
        self.assertEqual(out["counts"]["verified_public_executable_U"], 0)

    def test_unbounded_input_rejected(self):
        with self.assertRaisesRegex(ValueError, "INGRESS_EVENTS_NOT_BOUNDED"):
            gate.ingest_document(self.doc([{}] * 501), self.grid, self.prefreeze)

    def test_wrong_schema_rejected(self):
        with self.assertRaisesRegex(ValueError, "INGRESS_SCHEMA_INVALID"):
            gate.ingest_document({"events": []}, self.grid, self.prefreeze)

    def test_invalid_empty_record_still_gated(self):
        r = gate.ingest_document(self.doc([{}]), self.grid, self.prefreeze)
        self.assertEqual(r["counts"]["rejected"], 1)
        self.assertEqual(r["counts"]["verified_public_executable_U"], 0)
        self.assertEqual(r["gates"]["PRODUCTION"], "NO_GO")

    def test_changed_frozen_bytes_rejected_in_temp_dir(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in (gate.FROZEN, gate.GRID):
                shutil.copyfile(gate.ROOT / name, root / name)
            p = root / gate.FROZEN
            p.write_bytes(p.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "PINNED_SOURCE_BLOB_SHA_DRIFT"):
                gate.load_frozen(root)

    def test_public_pending_tx_does_not_verify_exact_ca_trade_or_funding(self):
        r, _ = self.check(self.valid_event())
        self.assertEqual(r["exact_ca_trade_buy_validation"], "UNRESOLVED_ROUTER_AND_TOKEN_LOGS")
        self.assertEqual(r["trade_funding_and_execution"], "UNRESOLVED")
        self.assertEqual(r["follower_net_pnl"], "UNRESOLVED")
        self.assertNotIn("PROVEN", r["state"])


if __name__ == "__main__":
    unittest.main()
