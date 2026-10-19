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
