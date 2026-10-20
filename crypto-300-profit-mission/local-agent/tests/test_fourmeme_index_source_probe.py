"""Isolated no-network tests for the bounded Four.meme source probe."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "mission_agent" / "early" /
          "fourmeme_index_source_probe.py")
spec = importlib.util.spec_from_file_location("monster_fourmeme_probe", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class FakeRPC:
    source_sha256 = "offline-fake-source"
    def __init__(self, *, bad_chain=False, zero_at=None, duplicate_at=None,
                 wrong_event=False):
        self.calls = []
        self.bad_chain = bad_chain
        self.zero_at = zero_at
        self.duplicate_at = duplicate_at
        self.wrong_event = wrong_event

    def token_at_index(self, idx, block):
        if block <= m.PRE_BLOCK:
            if idx >= m.START_INDEX:
                return "0x" + "0" * 40
            return "0x" + format(idx + 1, "040x")
        if idx >= m.END_INDEX_EXCLUSIVE:
            return "0x" + "0" * 40
        if idx == m.START_INDEX:
            return m.ANCHORS[0][2]
        if idx == m.END_INDEX_EXCLUSIVE - 1:
            return m.ANCHORS[1][2]
        if idx == self.zero_at:
            return "0x" + "0" * 40
        if idx == self.duplicate_at:
            return m.ANCHORS[0][2]
        return "0x" + format(idx + 1, "040x")

    def request(self, method, params):
        self.calls.append((method, params))
        if method == "eth_chainId":
            result = "0x1" if self.bad_chain else "0x38"
        elif method == "eth_call":
            data = params[0]["data"]
            block = int(params[1], 16)
            if params[0]["to"] == m.MANAGER:
                index = int(data[10:], 16)
                result = "0x" + self.token_at_index(index, block)[2:].rjust(64, "0")
            elif params[0]["to"] == m.MULTICALL3:
                if not data.startswith(m.AGGREGATE3_SELECTOR):
                    raise AssertionError("BAD_MULTICALL3_FUNCTION_SELECTOR")
                raw = bytes.fromhex(data[10:])

                def word(pos):
                    return int.from_bytes(raw[pos:pos + 32], "big")

                array_start = word(0)
                count = word(array_start)
                if not 1 <= count <= m.BATCH_SIZE:
                    raise AssertionError("BAD_MULTICALL3_BATCH_SIZE")
                base = array_start + 32
                addresses = []
                for i in range(count):
                    entry = base + word(base + i * 32)
                    if word(entry) != int(m.MANAGER, 16):
                        raise AssertionError("BAD_INNER_MANAGER")
                    if word(entry + 32) != 1:
                        raise AssertionError("BAD_INNER_ALLOW_FAILURE")
                    dynamic = entry + word(entry + 64)
                    if word(dynamic) != 36:
                        raise AssertionError("BAD_INNER_CALLDATA_SIZE")
                    call_data = raw[dynamic + 32:dynamic + 68]
                    if call_data[:4] != bytes.fromhex(m.SELECTOR[2:]):
                        raise AssertionError("BAD_INNER_TOKEN_SELECTOR")
                    index = int.from_bytes(call_data[4:], "big")
                    addresses.append(self.token_at_index(index, block))
                n = len(addresses)
                return_words = [32, n]
                return_words += [n * 32 + i * 128 for i in range(n)]
                for address in addresses:
                    return_words += [1, 64, 32, int(address, 16)]
                result = "0x" + "".join(m.word_hex(v) for v in return_words)
            else:
                raise AssertionError("UNKNOWN_READ_ONLY_CALL_DESTINATION")
        elif method == "eth_getLogs":
            block = int(params[0]["fromBlock"], 16)
            match = next((a for a in m.ANCHORS if a[1] == block), None)
            if not match:
                raise AssertionError("UNEXPECTED_LOG_BLOCK")
            token = ("0x" + "9" * 40) if self.wrong_event else match[2]
            data = ("0x" + "0" * 24 + "1" * 40 +
                    "0" * 24 + token[2:] + "0" * 64 * 6)
            result = [{"address": m.MANAGER, "topics": [m.CREATE_TOPIC],
                       "data": data, "blockNumber": hex(block),
                       "transactionHash": "0x" + format(block, "064x"),
                       "removed": False}]
        elif method == "eth_getTransactionReceipt":
            result = {"status": "0x1", "transactionHash": params[0]}
        else:
            raise AssertionError("UNEXPECTED_RPC_METHOD")
        raw = json.dumps({"jsonrpc": "2.0", "id": len(self.calls),
                          "result": result}, sort_keys=True).encode("utf-8")
        return result, raw


class FourmemeIndexProbeTests(unittest.TestCase):
    def test_exact_538_addresses_and_two_real_event_shapes_archived(self):
        rpc = FakeRPC()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "one-run"
            result = m.collect(path, rpc)
            self.assertEqual(result["address_count"], 538)
            self.assertEqual(result["rpc_response_count"], 47)
            self.assertEqual(result["range_start"], 247596)
            self.assertEqual(result["range_end_exclusive"], 248134)
            self.assertEqual(result["multicall3_batch_count"], 36)
            self.assertEqual(result["indexed_token_addresses"][0]["token_ca"], m.ANCHORS[0][2])
            self.assertEqual(result["indexed_token_addresses"][-1]["token_ca"], m.ANCHORS[1][2])
            self.assertEqual(len(set(x["token_ca"] for x in result["indexed_token_addresses"])), 538)
            archive = (path / "raw_rpc_responses_base64.jsonl").read_bytes()
            self.assertEqual(m.sha256(archive), result["raw_archive_sha256"])
            self.assertEqual(len(archive.splitlines()), 47)
            self.assertEqual(json.loads((path / "manifest.json").read_text())["address_count"], 538)
            self.assertNotIn("available_at", json.dumps(result))
            self.assertEqual(result["status"], "538_UNIQUE_INDEXED_ADDRESSES_CROSSCHECKED_TWO_CREATION_EVENTS")

    def test_any_hole_fails_closed_does_not_write_success_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "bad"
            with self.assertRaisesRegex(m.ProbeError, "HOLE_IN_FROZEN_INDEX_RANGE"):
                m.collect(target, FakeRPC(zero_at=m.START_INDEX + 12))
            self.assertFalse((target / "manifest.json").exists())
            self.assertTrue((target / "raw_rpc_responses_base64.jsonl").exists())

    def test_duplicate_token_address_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "bad"
            with self.assertRaisesRegex(m.ProbeError, "INVALID_OR_DUPLICATE_TOKEN_CA"):
                m.collect(target, FakeRPC(duplicate_at=m.START_INDEX + 23))
            self.assertFalse((target / "manifest.json").exists())

    def test_wrong_manager_create_event_fails_after_538_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "bad"
            with self.assertRaisesRegex(m.ProbeError, "ANCHOR_NOT_UNIQUE_OR_MISMATCH"):
                m.collect(target, FakeRPC(wrong_event=True))
            self.assertFalse((target / "manifest.json").exists())

    def test_wrong_chain_fails_before_enumeration(self):
        with tempfile.TemporaryDirectory() as tmp:
            rpc = FakeRPC(bad_chain=True)
            with self.assertRaisesRegex(m.ProbeError, "NOT_BNB_MAINNET"):
                m.collect(Path(tmp) / "bad", rpc)
            self.assertEqual(len(rpc.calls), 1)

    def test_reject_existing_output_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "existing"
            target.mkdir()
            (target / "marker").write_text("already present")
            with self.assertRaisesRegex(m.ProbeError, "OUTPUT_DIRECTORY_NOT_EMPTY"):
                m.collect(target, FakeRPC())

    def test_padded_address_word_validation(self):
        self.assertEqual(m.parse_word("0x" + "0" * 24 + "1" * 40), "0x" + "1" * 40)
        for malformed in (None, "0x1234", "0x" + "a" * 63, "0x" + "z" * 64):
            with self.subTest(malformed=malformed):
                with self.assertRaises(m.ProbeError):
                    m.parse_word(malformed)

    def test_unsafe_endpoint_rejected_without_network(self):
        invalid = (None, "http://test.example/v2/key",
                   "https://user:pwd@test.example/v2/key",
                   "https://test.example/v2/key#fragment")
        for url in invalid:
            with self.subTest(url=str(url)):
                with self.assertRaises(m.ProbeError):
                    m.JsonRPC(url, min_interval=0)


    def test_multicall_codec_rejects_bad_result_and_failed_subcall(self):
        def w(v):
            return m.word_hex(v)
        good = "0x" + "".join(w(v) for v in [32, 1, 32, 1, 64, 32,
                                                   int(m.ANCHORS[0][2], 16)])
        self.assertEqual(m.decode_multicall_result(good, 1), [m.ANCHORS[0][2]])
        with self.assertRaisesRegex(m.ProbeError, "INNER_CALL_FAILED"):
            m.decode_multicall_result("0x" + "".join(
                w(v) for v in [32, 1, 32, 0, 64, 32, int(m.ANCHORS[0][2], 16)]), 1)
        with self.assertRaisesRegex(m.ProbeError, "TRUNCATED_OR_UNALIGNED"):
            m.decode_multicall_result(good[:-64], 1)
        with self.assertRaisesRegex(m.ProbeError, "COUNT_MISMATCH"):
            m.decode_multicall_result(good, 2)
        with self.assertRaisesRegex(m.ProbeError, "HOLE_IN_FROZEN_INDEX_RANGE"):
            m.decode_multicall_result("0x" + "".join(
                w(v) for v in [32, 1, 32, 1, 64, 32, 0]), 1)

    def test_no_more_than_15_inner_calls_per_multicall(self):
        with self.assertRaisesRegex(m.ProbeError, "INVALID_MULTICALL_BATCH_SIZE"):
            m.multicall_calldata(range(16))
        with self.assertRaisesRegex(m.ProbeError, "INVALID_MULTICALL_BATCH_SIZE"):
            m.multicall_calldata([])
        code = m.multicall_calldata([m.START_INDEX, m.START_INDEX + 1])
        self.assertTrue(code.startswith("0x82ad56cb"))
        self.assertEqual(len(code), 2 + 8 + 64 * 16)

    def test_request_budget_is_hard_limited(self):
        rpc = m.JsonRPC("https://test.example/v2/sample-secret", min_interval=0,
                        max_requests=0)
        with self.assertRaisesRegex(m.ProbeError, "REQUEST_BUDGET_EXHAUSTED"):
            rpc.request("eth_chainId", [])


if __name__ == "__main__":
    unittest.main()
