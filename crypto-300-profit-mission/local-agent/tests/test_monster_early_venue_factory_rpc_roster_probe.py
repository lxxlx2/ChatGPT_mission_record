"""Offline-only source-probe regressions: no HTTP call, no wallet, no schedule."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "monster_early_venue_factory_rpc_roster_probe.py"
spec = importlib.util.spec_from_file_location("monster_early_venue_rpc_probe", MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def mocklog(block, token, tx_index=1, log_index=0):
    f = m.CHAINS["base-v3"]
    a = f["bases"][0]
    return {
        "address": f["factory"],
        "topics": [f["topic"], "0x" + "0"*24 + a[2:].lower(),
                   "0x" + "0"*24 + token[2:].lower(), "0x" + "0"*60 + "0bb8"],
        "data": "0x" + "0"*64 + "0"*24 + "a"*40,
        "blockNumber": hex(block), "transactionIndex": hex(tx_index),
        "logIndex": hex(log_index), "transactionHash": "0x" + "3"*64,
        "removed": False,
    }


class FactorySourceProbeTests(unittest.TestCase):
    def test_decode_layout_and_chronological_no_winner_filter(self):
        a = mocklog(100, "0x" + "a"*40, 2, 1)
        b = mocklog(99, "0x" + "b"*40, 1, 0)
        c = mocklog(101, "0x" + "a"*40, 0, 0)
        all_rows, cohort, n = m.build_roster([a, b, c], "base-v3")
        self.assertEqual((len(all_rows), n), (3, 2))
        self.assertEqual([x["block_number"] for x in cohort], [99, 100])
        self.assertEqual(cohort[0]["token_ca"], "0x" + "b"*40)
        self.assertEqual(cohort[0]["pool"], "0x" + "a"*40)
        self.assertTrue(cohort[0]["pool_is_not_liquidity_or_swap_proof"])

    def test_api_wrong_factory_rejects_not_zero(self):
        class Fake:
            def request(self, method, params):
                return [{"address": "0x" + "f"*40, "topics": [],
                         "blockNumber": "0x1"}], b"{}"
        with self.assertRaisesRegex(m.SourceError, "ADDRESS_MISMATCH"):
            m.fetch_logs(Fake(), "base-v3", 0, 2)

    def test_contiguous_resume_and_raw_sha_guard(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = m.CHAINS["base-v3"]
            for st, en in [(9, 9), (10, 11)]:
                raw = json.dumps({"jsonrpc": "2.0", "result": [
                    mocklog(st, "0x" + "a"*40)]}).encode()
                m.safe_file(root / f"{st}-{en}.raw.json", raw)
                receipt = {
                    "chain": "base-v3", "rpc_host": "mainnet.base.org",
                    "factory": cfg["factory"].lower(), "topic": cfg["topic"],
                    "start": st, "end": en, "response_sha256": m.sha(raw),
                }
                m.safe_file(root / f"{st}-{en}.receipt.json",
                            m.plain_json(receipt).encode())
            next_block, rows = m.read_saved(root, 9, 11, "base-v3", "mainnet.base.org")
            self.assertEqual((next_block, len(rows)), (12, 2))
            p = root / "10-11.raw.json"
            p.write_bytes(p.read_bytes() + b"\n")
            with self.assertRaisesRegex(m.SourceError, "SHA_MISMATCH"):
                m.read_saved(root, 9, 11, "base-v3", "mainnet.base.org")

    def test_bsc_v2_factory_event_layout(self):
        c = m.CHAINS["bsc-v2"]
        token = "0x" + "a"*40
        row = {
            "topics": [c["topic"], "0x" + "0"*24 + token[2:],
                       "0x" + "0"*24 + c["bases"][0][2:].lower()],
            "data": "0x" + "0"*24 + "a"*40 + "0"*64,
            "blockNumber": "0x2", "transactionIndex": "0x0", "logIndex": "0x1",
            "transactionHash": "0x" + "1"*64,
        }
        record = m.decode(row, "bsc-v2")
        self.assertEqual(record["token0"], token)
        self.assertEqual(record["pool"], token)

    def test_bsc_v3_poolcreated_decodes_as_v3_not_v2(self):
        row = mocklog(100, "0x" + "e"*40)
        cfg = m.CHAINS["bsc-v3"]
        row["address"] = cfg["factory"]
        row["topics"][0] = cfg["topic"]
        row["topics"][1] = "0x" + "0"*24 + cfg["bases"][0][2:].lower()
        decoded = m.decode(row, "bsc-v3")
        self.assertEqual(decoded["pool"], "0x" + "a"*40)
        _, cohort, n = m.build_roster([row], "bsc-v3")
        self.assertEqual((n, len(cohort)), (1, 1))

    def test_historical_v2_counter_reconciles_actual_archived_paircreated_layout(self):
        cfg = m.CHAINS["bsc-v2"]
        record = {
            "address": cfg["factory"], "topics": [
                cfg["topic"],
                "0x0000000000000000000000001c88e86556b815f4b140ec14297ada7863bc97c8",
                "0x000000000000000000000000bb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"],
            "data": "0x000000000000000000000000b2dc7c7f5b67b2d604603fbc56530ba7832648a800000000000000000000000000000000000000000000000000000000001e4a5d",
            "blockNumber": "0x3c00085", "transactionIndex": "0x46",
            "logIndex": "0xfa",
            "transactionHash": "0xb63846e92b19018da4d0e24cec8aab69d979c14059130b7b76dbfe972e5e1418",
            "removed": False,
        }
        class Counter:
            def request(self, method, params):
                self_method = method == "eth_call" and params[0]["data"] == "0x574f2ba3"
                if not self_method:
                    raise AssertionError("unexpected RPC method")
                block = int(params[1], 16)
                return (hex(1985116 if block == 62914692 else 1985117), b"{}")
        rpc = Counter()
        found = m.reconcile_v2_factory_counter(rpc, 62914693, 62914693, [record])
        self.assertEqual(found["status"], "COUNTER_MATCHES_EVENTS")
        self.assertEqual(found["created_events"], 1)
        self.assertEqual(m.decode(record, "bsc-v2")["pool"],
                         "0xb2dc7c7f5b67b2d604603fbc56530ba7832648a8")
        with self.assertRaisesRegex(m.SourceError, "EVENT_COUNT_MISMATCH"):
            m.reconcile_v2_factory_counter(rpc, 62914693, 62914693, [])
        malformed = dict(record, data=record["data"][:-1] + "0")
        with self.assertRaisesRegex(m.SourceError, "FACTORY_SEQUENCE_MISMATCH"):
            m.reconcile_v2_factory_counter(rpc, 62914693, 62914693, [malformed])

    def test_endpoint_fingerprint_prevents_resume_same_host_different_url(self):
        class Dummy: pass
        a = m.RPC("https://example-rpc.org/a", 56, 8, 0)
        b = m.RPC("https://example-rpc.org/b", 56, 8, 0)
        self.assertEqual(a.host, b.host)
        self.assertNotEqual(a.source_tag, b.source_tag)

    def test_v2_historical_factory_index_enumeration_includes_quote_and_nonquote(self):
        class IndexedRPC:
            source_tag = "fake"
            calls = 0
            def request(self, method, params):
                self.calls += 1
                if method != "eth_call":
                    raise AssertionError("only read eth_call permitted")
                obj, block = params
                contract, data = obj["to"].lower(), obj["data"]
                if data == "0x574f2ba3":
                    value = 100 if int(block, 16) == 9 else 102
                    returned = hex(value)
                elif data.startswith("0x1e3dd18b"):
                    idx = int(data[10:], 16)
                    returned = "0x" + "0"*24 + ("%040x" % (idx - 99))
                elif data == "0x0dfe1681":
                    returned = "0x" + "0"*24 + ("1"*40 if contract.endswith("1") else "2"*40)
                elif data == "0xd21220a7":
                    returned = "0x" + "0"*24 + ("bb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c" if contract.endswith("1") else "e"*40)
                else:
                    raise AssertionError("unexpected read")
                import json
                return returned, json.dumps({"jsonrpc":"2.0","result":returned}).encode()
        with tempfile.TemporaryDirectory() as tmp:
            rpc = IndexedRPC()
            result = m.enumerate_bsc_v2(rpc, 10, 20, limit=2, out_dir=Path(tmp))
            self.assertEqual(result["factory_new_pools_in_day"], 2)
            self.assertEqual(result["status"], "PARTIAL_NOT_30_ELIGIBLE_OR_LIMIT")
            self.assertEqual(result["identity_candidates_found"], 1)
            self.assertEqual(result["sample"][0]["token_ca"], "0x" + "1"*40)
            self.assertEqual(result["factory_index_rows_checked"], 2)
            before = rpc.calls
            result2 = m.enumerate_bsc_v2(rpc, 10, 20, limit=2, out_dir=Path(tmp))
            self.assertEqual(rpc.calls - before, 2)
            src = Path(tmp) / "v2_historical_index_raw" / "100.json"
            payload = json.loads(src.read_text())
            payload["raw_abi_response_records"][0]["sha256"] = "0" * 64
            src.write_text(json.dumps(payload))
            with self.assertRaisesRegex(m.SourceError, "SAVED_RAW_SHA_MISMATCH"):
                m.enumerate_bsc_v2(rpc, 10, 20, limit=2, out_dir=Path(tmp))

    def test_v2_historical_index_rejects_zero_abi_address(self):
        class Fake:
            def request(self, method, params):
                return "0x" + "0"*64, b"{}"
        with self.assertRaisesRegex(m.SourceError, "ZERO_OR_MISSING_PAIR"):
            m.historical_v2_address(Fake(), "0x" + "1"*40, "0x1e3dd18b", 10)

    def test_wrong_chain_and_embedded_credentials_rejected(self):
        with self.assertRaisesRegex(m.SourceError, "CREDENTIALS"):
            m.RPC("https://name:pass@some-rpc.com", 8453, 3, 0)

        class Fake(m.RPC):
            def request(self, method, params):
                return "0x38", b"{}"

        with self.assertRaisesRegex(m.SourceError, "WRONG_CHAIN"):
            Fake("https://mainnet.base.org", 8453, 1, 0).chain_check()

    def test_utc_day_exact_boundary_binary_search(self):
        start = int(m.dt.datetime(2025, 7, 1, tzinfo=m.dt.timezone.utc).timestamp())

        class Fake:
            def request(self, method, params):
                if method == "eth_blockNumber":
                    return "0x8", b"{}"
                block = int(params[0], 16)
                return {"number": hex(block),
                        "timestamp": hex(start + (block - 2)*36000)}, b"{}"

        self.assertEqual(m.resolve_day(Fake(), "2025-07-01"), (2, 4))


if __name__ == "__main__":
    unittest.main()
