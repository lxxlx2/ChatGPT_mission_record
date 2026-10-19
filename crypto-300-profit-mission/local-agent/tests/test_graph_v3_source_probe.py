"""Offline-only source check tests; all network calls are replaced."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "mission_agent" / "early" / "graph_v3_source_probe.py"
spec = importlib.util.spec_from_file_location("source_probe", SOURCE)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class Response:
    def __init__(self, body):
        self.body = body
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self, size):
        return self.body


def fake_body(tip=52555482, pools=None, errors=False):
    pools = pools if pools is not None else [{
        "id": "0x" + "1" * 40,
        "createdAtBlockNumber": "52440500",
        "createdAtTimestamp": "1751328000",
        "feeTier": "2500",
        "token0": {"id": "0x" + "2" * 40},
        "token1": {"id": "0x" + "3" * 40},
    }]
    result = {"data": {"_meta": {"block": {"number": tip},
                                   "hasIndexingErrors": False}, "pools": pools}}
    if errors:
        result["errors"] = [{"message": "denied"}]
    return json.dumps(result).encode()


class OneQueryProbeTests(unittest.TestCase):
    def test_single_post_secret_header_and_raw_sha_archive(self):
        calls = []
        def opener(req, timeout):
            calls.append(req)
            self.assertEqual(timeout, 20)
            return Response(fake_body())
        with tempfile.TemporaryDirectory() as tmp:
            result = p.probe_once("fake-secret", Path(tmp), opener=opener)
            self.assertEqual(result["status"], "CANDIDATE_SAMPLE_ONLY_NOT_SOURCE_PASS")
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0].get_method(), "POST")
            self.assertEqual(calls[0].get_header("Authorization"), "Bearer fake-secret")
            self.assertNotIn("fake-secret", json.dumps(result))
            self.assertEqual(len(list(Path(tmp).glob("*.json"))), 2)
            raw = next(Path(tmp).glob("*response*.json")).read_bytes()
            self.assertEqual(p.sha256(raw), result["raw_response_sha256"])
            self.assertNotIn(b"fake-secret", raw)

    def test_key_missing_has_no_network(self):
        calls = []
        with self.assertRaisesRegex(p.ProbeError, "GRAPH_API_KEY_REQUIRED"):
            p.probe_once(None, "/tmp/not-used", opener=lambda *a,**k: calls.append(a))
        self.assertFalse(calls)

    def test_index_tip_before_history_never_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = p.probe_once("fake", tmp, opener=lambda *a, **kw: Response(fake_body(tip=50000000)))
            self.assertEqual(r["status"], "HISTORICAL_V3_COVERAGE_UNVERIFIED")

    def test_no_pool_is_not_no_real_pools(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = p.probe_once("fake", tmp, opener=lambda *a, **kw: Response(fake_body(pools=[])))
            self.assertEqual(r["status"], "HISTORICAL_V3_COVERAGE_UNVERIFIED")

    def test_bad_pool_and_errors_fail_closed_no_archive(self):
        wrong = [{"id": "0x" + "1" * 40, "createdAtBlockNumber": "52555483",
                  "createdAtTimestamp": "1751328000", "feeTier": "2500",
                  "token0": {"id": "0x" + "2" * 40}, "token1": {"id": "0x" + "3" * 40}}]
        for raw in (fake_body(pools=wrong), fake_body(errors=True), b"not-json"):
            with self.subTest(raw=raw[:20]), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(p.ProbeError):
                    p.probe_once("fake", tmp, opener=lambda *a, **kw: Response(raw))
                self.assertEqual(list(Path(tmp).glob("*.json")), [])

    def test_data_new_fields_dont_promote_to_pit(self):
        tip, pools = p.validate_body(fake_body())
        self.assertEqual(tip, 52555482)
        self.assertTrue(pools)
        self.assertNotIn("available_at", pools[0])
        self.assertNotIn("can_sell", pools[0])


if __name__ == "__main__":
    unittest.main()
