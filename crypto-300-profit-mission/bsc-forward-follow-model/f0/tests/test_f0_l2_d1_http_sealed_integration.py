"""D1 fake HTTPS POST starts plus existing 3-slot ledger; NO real sockets."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_coordinator import (
    SealedMemoryHTTPSSource, run_fake_concurrent, FakeSource)
from f0_l2_d1_https import send_live
from f0_l2_d1_recovery import reconcile_saved_attempts


class SealedMemoryHTTPSIntegrationTests(unittest.TestCase):
    def scenario(self, source):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).absolute()/"private"
            root.mkdir(mode=0o700)
            with patch("http.client.HTTPSConnection",
                       side_effect=AssertionError("real socket forbidden")):
                result=run_fake_concurrent(
                    source,root,max_total=10,max_blocks=3,
                    max_refreshes=5,window_ms=9000,
                    head_min_poll_age_ms=250)
            audit=reconcile_saved_attempts(root)
            rows=[json.loads(s) for s in
                  (root/"attempts.jsonl").read_text().splitlines()]
            return result,audit,rows

    def test_three_slot_fake_https_integration_and_parent_audit(self):
        src=SealedMemoryHTTPSSource(growth_bps=10.0,delay_ms=20)
        result,audit,rows=self.scenario(src)
        self.assertEqual(result["mode"],"D1_OFFLINE_MEMORY_HTTPS_ONLY")
        self.assertEqual(result["network_requests"],0)
        self.assertTrue(result["no_live_sender"])
        self.assertLessEqual(result["max_shared_slots"],3)
        self.assertLessEqual(result["reserved"],10)
        self.assertEqual(result["settled"],result["reserved"])
        self.assertEqual(result["block_attempts"],3)
        self.assertEqual(result["contiguous_commits"],3)
        self.assertEqual(audit["audit_status"],"OFFLINE_ACCOUNTED_NOT_LIVE")
        self.assertEqual(audit["contiguous_commits"],3)
        self.assertEqual(audit["unknown_request_ids"],[])
        self.assertGreaterEqual(result["min_actual_fake_start_gap_ms"],248.5)
        self.assertEqual(audit["contiguous_commits"],
                         result["contiguous_commits"])
        self.assertEqual(len([r for r in rows if r["event"]=="SETTLE"]),
                         result["reserved"])
        self.assertEqual(len([r for r in rows
                              if r["event"]=="RESERVE_UNKNOWN"]),
                         result["reserved"])
        with self.assertRaisesRegex(ValueError,
                                    "D1_LIVE_TRANSPORT_DISABLED"):
            send_live({"jsonrpc":"2.0","id":1,
                       "method":"eth_blockNumber","params":[]})

    def test_http_503_stops_and_preserves_original_request_owner(self):
        src=SealedMemoryHTTPSSource(
            growth_bps=10.0,delay_ms=20,fail_block_ordinal=1)
        result,audit,rows=self.scenario(src)
        self.assertEqual(result["stop"],"RPC_OR_HEAD_FAULT")
        self.assertEqual(result["contiguous_commits"],0)
        self.assertEqual(result["reserved"],result["settled"])
        bad=[r for r in rows if r["event"]=="SETTLE" and
             r.get("http_status")==503]
        self.assertEqual(len(bad),1)
        self.assertTrue("raw_sha256" in bad[0])
        self.assertEqual(bad[0]["category"],"BLOCK")
        self.assertEqual(audit["audit_status"],
                         "INVALID_FOR_PERFORMANCE_CLAIM")
        self.assertEqual(audit["network_retries"],0)

    def test_malformed_json_ends_dispatch_no_cross_gap(self):
        src=SealedMemoryHTTPSSource(
            growth_bps=10.0,delay_ms=20,bad_json_ordinal=1)
        result,audit,rows=self.scenario(src)
        self.assertEqual(result["contiguous_commits"],0)
        self.assertEqual(result["stop"],"RPC_OR_HEAD_FAULT")
        self.assertEqual(audit["audit_status"],
                         "INVALID_FOR_PERFORMANCE_CLAIM")
        self.assertTrue(any(r.get("raw_sha256") for r in rows
                            if r["event"]=="SETTLE"))

    def test_head_ttl_checked_at_fake_post_after_delayed_tls_setup(self):
        # The actual POST begins only after TLS/context preparation. A
        # previously fresh HEAD can expire while preparing, and must not
        # authorize a BLOCK when the HTTP fake's request method starts.
        import time
        from f0_l2_d1_https import _exchange_with_factory as reviewed_exchange
        src=SealedMemoryHTTPSSource(growth_bps=10.0,delay_ms=10)
        def delayed_tls(request, factory, **config):
            if request["method"]=="eth_getBlockByNumber":
                time.sleep(0.65)
            return reviewed_exchange(request,factory,**config)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).absolute()/"private"
            root.mkdir(mode=0o700)
            with patch("f0_l2_d1_coordinator._exchange_with_factory",
                       side_effect=delayed_tls):
                with patch("http.client.HTTPSConnection",
                           side_effect=AssertionError("network denied")):
                    report=run_fake_concurrent(
                        src,root,max_total=5,max_blocks=1,
                        max_refreshes=0,window_ms=5000,
                        head_ttl_ms=500,head_min_poll_age_ms=250)
            self.assertEqual(report["block_attempts"],1)
            self.assertEqual(report["contiguous_commits"],0)
            self.assertEqual(src.block_count,0)
            events=[json.loads(line) for line in
                    (root/"attempts.jsonl").read_text().splitlines()]
            failures=[x for x in events if x["event"]=="SETTLE"
                      and x["category"]=="BLOCK"]
            self.assertEqual(len(failures),1)
            self.assertIn("PRESTART_STALE_HEAD",failures[0]["reason"])
            self.assertFalse(failures[0]["started"])
            self.assertNotEqual(report["stop"],"BLOCK_BUDGET")

    def test_pretend_source_callback_cannot_replace_sealed_method(self):
        src=SealedMemoryHTTPSSource(growth_bps=10.0,delay_ms=0)
        src.reply_over_memory_https=lambda *args, **kw: FakeSource.reply(src,args[0])
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).absolute()/"private"
            root.mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError,"D1_SCOPE_INVALID"):
                run_fake_concurrent(src,root,max_total=6,max_blocks=2,
                                    max_refreshes=2,
                                    head_min_poll_age_ms=250)
            self.assertFalse((root/"attempts.jsonl").exists())


if __name__=="__main__":
    unittest.main()
