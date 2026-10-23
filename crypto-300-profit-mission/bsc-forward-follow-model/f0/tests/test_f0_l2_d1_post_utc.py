"""D1 real-thread fake POST UTC scope; no real requests or production keys."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import f0_l2_d1_coordinator as coordinator
from f0_l2_d1_bundle import run_gated_fake_session
from f0_l2_d1_coordinator import SealedMemoryHTTPSSource
from f0_l2_d1_inventory_gate import consume_then_run_fake_once
from f0_l2_d1_post_utc import OfflinePostUTCWindow
from test_f0_l2_d1_bundle import D1BundleTests
from test_f0_l2_d1_inventory_gate import D1InventoryGateTests


class MutableUTC:
    def __init__(self, now):
        self.now=now
    def __call__(self):
        return self.now


class D1PostUTCTests(unittest.TestCase):
    def setUp(self):
        self.fixture=D1BundleTests("test_composed_signed_scope_and_source_are_bound")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.clock=MutableUTC(self.fixture.now)

    def launch(self, source=None, **kwargs):
        fixture=self.fixture
        raw,proofs=fixture.signed()
        output=Path(fixture.tmp.name).absolute()/"post_session"
        output.mkdir(mode=0o700)
        original=coordinator._exchange_with_factory
        clock=self.clock

        def dispatch(request, factory, **options):
            if kwargs.get("expire_before_first_block") and (
                    request["method"]=="eth_getBlockByNumber"):
                clock.now=clock.now+timedelta(minutes=2)
            return original(request,factory,**options)
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("REAL_NETWORK_FORBIDDEN")):
            with patch("f0_l2_d1_coordinator._exchange_with_factory",
                       side_effect=dispatch):
                report=run_gated_fake_session(
                    SealedMemoryHTTPSSource(growth_bps=10.0,delay_ms=10)
                    if source is None else source,
                    output,permit_raw=raw,expected_sha=fixture.sha,
                    proofs=proofs,test_only_trust_roots=fixture.trust,
                    checkout_root=fixture.repo,
                    reviewed_files=fixture.manifest,
                    now=fixture.now,
                    test_only_fake_post_utc_clock=clock)
        return report,output

    def test_each_valid_fake_http_post_checked_in_signed_window(self):
        result,_=self.launch()
        fake=result["fake"]
        self.assertEqual(fake["mode"],"D1_OFFLINE_MEMORY_HTTPS_ONLY")
        self.assertEqual(fake["contiguous_commits"],3)
        self.assertEqual(result["actual_rpc_requests"],0)
        self.assertEqual(fake["fake_post_utc_checks"],
                         fake["physically_started_fake"])
        self.assertGreaterEqual(fake["min_actual_fake_start_gap_ms"],248.5)
        self.assertEqual(result["audit"]["audit_status"],
                         "OFFLINE_ACCOUNTED_NOT_LIVE")

    def test_utc_expiry_after_reserve_before_fake_post_refuses_block(self):
        source=SealedMemoryHTTPSSource(growth_bps=10.0,delay_ms=10)
        result,output=self.launch(source,expire_before_first_block=True)
        self.assertEqual(source.block_count,0)
        self.assertEqual(result["fake"]["contiguous_commits"],0)
        self.assertEqual(result["fake"]["stop"],"RPC_OR_HEAD_FAULT")
        self.assertEqual(result["audit"]["audit_status"],
                         "INVALID_FOR_PERFORMANCE_CLAIM")
        rows=[json.loads(x) for x in
              (output/"attempts.jsonl").read_text().splitlines()]
        block=[x for x in rows if x["event"]=="SETTLE" and
               x["category"]=="BLOCK"]
        self.assertGreaterEqual(len(block),1)
        self.assertTrue(all(x["reason"]=="PRESTART_OFFLINE_PERMIT_UTC_DENIED"
                            and x["started"] is False for x in block))

    def test_clock_rollback_before_head_denies_without_fake_head(self):
        f=self.fixture
        clock=self.clock
        real=coordinator._exchange_with_factory
        source=SealedMemoryHTTPSSource(growth_bps=10.0,delay_ms=10)
        def rewind(request,factory,**kw):
            if request["method"]=="eth_blockNumber":
                clock.now=f.now-timedelta(seconds=5)
            return real(request,factory,**kw)
        raw,proofs=f.signed()
        with tempfile.TemporaryDirectory() as d:
            evidence=Path(d).absolute()
            with patch("http.client.HTTPSConnection",
                       side_effect=AssertionError("REAL_NETWORK_FORBIDDEN")):
                with patch("f0_l2_d1_coordinator._exchange_with_factory",
                           side_effect=rewind):
                    result=run_gated_fake_session(
                        source,evidence,permit_raw=raw,expected_sha=f.sha,
                        proofs=proofs,test_only_trust_roots=f.trust,
                        checkout_root=f.repo, reviewed_files=f.manifest,
                        now=f.now,test_only_fake_post_utc_clock=clock)
        self.assertEqual(source.head_count,0)
        self.assertEqual(result["fake"]["contiguous_commits"],0)
        self.assertEqual(result["fake"]["stop"],"RPC_OR_HEAD_FAULT")

    def test_naive_test_clock_fails_closed_before_fake_source_call(self):
        source=SealedMemoryHTTPSSource(growth_bps=10.0,delay_ms=10)
        self.clock.now=self.fixture.now.replace(tzinfo=None)
        result,_=self.launch(source)
        self.assertEqual(source.head_count,0)
        self.assertEqual(source.block_count,0)
        self.assertEqual(result["fake"]["physically_started_fake"],0)
        self.assertEqual(result["fake"]["stop"],"RPC_OR_HEAD_FAULT")
        self.assertEqual(result["audit"]["audit_status"],
                         "INVALID_FOR_PERFORMANCE_CLAIM")

    def test_unbound_permit_or_unsealed_source_is_rejected(self):
        f=self.fixture
        raw,proofs=f.signed()
        with self.assertRaisesRegex(ValueError,"POST_UTC_SCOPE_UNBOUND"):
            OfflinePostUTCWindow(raw,"f"*40,self.clock)
        from f0_l2_d1_coordinator import FakeSource
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(
                    ValueError,"D1_BUNDLE_POST_UTC_REQUIRES_SEALED_FAKE"):
                run_gated_fake_session(
                    FakeSource(),Path(d).absolute(),permit_raw=raw,
                    expected_sha=f.sha,proofs=proofs,
                    test_only_trust_roots=f.trust,
                    checkout_root=f.repo,reviewed_files=f.manifest,
                    now=f.now,test_only_fake_post_utc_clock=self.clock)

    def test_expired_post_preserves_consumed_offline_marker(self):
        fixture=D1InventoryGateTests(
            "test_independent_fake_signed_inventory_and_permit_are_bound")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        clock=MutableUTC(fixture.now)
        reviewed=coordinator._exchange_with_factory
        source=SealedMemoryHTTPSSource(growth_bps=10.0,delay_ms=10)
        def expire(request,factory,**config):
            if request["method"]=="eth_getBlockByNumber":
                clock.now=fixture.now+timedelta(minutes=5)
            return reviewed(request,factory,**config)
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("REAL_NETWORK_FORBIDDEN")):
            with patch("f0_l2_d1_coordinator._exchange_with_factory",
                       side_effect=expire):
                result=consume_then_run_fake_once(
                    source,fixture.out,permit_raw=fixture.raw,
                    expected_sha=fixture.sha,proofs=fixture.proofs,
                    test_only_trust_roots=fixture.trust,
                    checkout_root=fixture.repo,
                    reviewed_files=fixture.manifest,now=fixture.now,
                    raw_inventory_statement=fixture.statement,
                    inventory_signatures=fixture.inv_proofs,
                    offline_test_registry_root=fixture.registry,
                    test_only_fake_post_utc_clock=clock)
        self.assertEqual(result["session"]["fake"]["contiguous_commits"],0)
        self.assertEqual(source.block_count,0)
        self.assertEqual(result["session"]["audit"]["audit_status"],
                         "INVALID_FOR_PERFORMANCE_CLAIM")
        self.assertEqual(len(list(fixture.registry.iterdir())),1)
        fixture.out=Path(fixture.temp.name).absolute()/"new_output"
        fixture.out.mkdir(mode=0o700)
        with self.assertRaisesRegex(ValueError,"GRANT_ALREADY_CONSUMED"):
            fixture.execute_fake(source=SealedMemoryHTTPSSource(delay_ms=0))


if __name__=="__main__":
    unittest.main()
