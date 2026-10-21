"""F0 saved one-shot Journal latency-only projections: no RPC or network imports."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest

F0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F0))
import f0_l1_offline_capacity as mod


def fixture(blocks=22, heads=7):
    rows = []
    for index, method in enumerate(
        ["eth_chainId"] + ["eth_blockNumber"] * heads +
        ["eth_getBlockByNumber"] * blocks, 1
    ):
        latency_ms = (425 if method != "eth_getBlockByNumber" else 770)
        rows.append({
            "index": index, "method": method, "state": "RPC_RESPONSE",
            "requested_monotonic_ns": index * 1_000_000_000,
            "completed_monotonic_ns": index * 1_000_000_000 + latency_ms * 1_000_000,
            "params": ["do not leak me"],
        })
    raw = json.dumps({"schema": mod.SCHEMA, "attempted_calls": len(rows),
                      "attempts": rows}).encode()
    return raw, hashlib.sha256(raw).hexdigest()


class OfflineCapacityTests(unittest.TestCase):
    def test_no_transport_or_shell_modules_or_network_calls(self):
        tree = ast.parse((F0 / "f0_l1_offline_capacity.py").read_text())
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(x.name.split(".")[0] for x in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertFalse(imports.intersection({
            "socket", "urllib", "requests", "http", "ssl", "subprocess",
            "websocket", "aiohttp", "threading", "asyncio",
        }))

    def test_exact_saved_journal_accounting_and_private_output(self):
        raw, sha = fixture()
        result = mod.analyze(raw, expected_sha256=sha)
        self.assertEqual(result["private_evidence"]["observed_attempts"], 30)
        self.assertEqual(result["private_evidence"]["observed_method_counts"], {
            "eth_chainId": 1, "eth_blockNumber": 7,
            "eth_getBlockByNumber": 22,
        })
        self.assertEqual(result["private_evidence"]["block_latency_mean_ms"], 770)
        self.assertEqual(result["actual_rpc_calls_during_this_program"], 0)
        self.assertNotIn("do not leak me", json.dumps(result))
        self.assertEqual(len(result["projections"]), 6)

    def test_bad_sha_and_missing_unknown_rows_fail_closed(self):
        raw, sha = fixture()
        with self.assertRaisesRegex(ValueError, "JOURNAL_SHA256_MISMATCH"):
            mod.analyze(raw, expected_sha256="0" * 64)
        data = json.loads(raw)
        data["attempts"][5]["state"] = "ATTEMPTED_OUTCOME_UNKNOWN"
        corrupted = json.dumps(data).encode()
        with self.assertRaisesRegex(ValueError, "JOURNAL_INCOMPLETE_OR_UNSUPPORTED"):
            mod.analyze(corrupted, expected_sha256=hashlib.sha256(corrupted).hexdigest())

    def test_global_rate_gate_and_minimum_inflight_scenarios(self):
        raw, sha = fixture()
        result = mod.analyze(raw, expected_sha256=sha)
        rows = [r for r in result["projections"] if r["head_every"] == 4]
        self.assertEqual([r["inflight"] for r in rows], [1, 2, 3])
        self.assertTrue(all(r["total_requests"] <= 32 for r in rows))
        self.assertEqual([r["head_refreshes"] for r in rows], [5, 5, 5])
        self.assertLess(rows[0]["projected_full_block_delivery_bps"],
                        rows[1]["projected_full_block_delivery_bps"])
        self.assertLess(rows[1]["projected_full_block_delivery_bps"],
                        rows[2]["projected_full_block_delivery_bps"])
        self.assertTrue(all(r["global_min_start_spacing_ms"] == 250
                            for r in rows))
        self.assertFalse(all(r["capacity_above_sample_growth_in_ideal_model"]
                             for r in rows))

    def test_head_schedule_budget_rejects_unaffordable(self):
        self.assertIsNone(mod.scenario_jobs(full_blocks=24, head_every=2,
                                             max_refreshes=6, total_cap=32))
        self.assertEqual(len(mod.scenario_jobs(full_blocks=24, head_every=8,
                                                max_refreshes=6, total_cap=32)), 28)
        raw, sha = fixture()
        _, data = mod.replay_timings(raw, sha)
        self.assertEqual(
            mod.projection(data, inflight=2, head_every=2)["status"],
            "NOT_FEASIBLE_WITHIN_GIVEN_REQUEST_BUDGET",
        )

    def test_sustained_source_rate_is_not_claimed_from_projection(self):
        raw, sha = fixture()
        doc = mod.analyze(raw, expected_sha256=sha)
        self.assertFalse(doc["live_run_authorized_by_this_program"])
        self.assertTrue(doc["original_live_permit_consumed"])
        self.assertTrue(all(row["status"] ==
                            "HYPOTHETICAL_ONLY_NO_PROVIDER_CONCURRENCY_VERIFIED"
                            for row in doc["projections"]))
        self.assertIn("NOT an actual parallel run", doc["interpretation"])


if __name__ == "__main__":
    unittest.main()
