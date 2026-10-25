"""D2-A: exact physical proposal is diagnostic-only and ALWAYS fails closed.

No real networking, no fixed production registry or signatures, no new
dispatcher or patched external API: check ONE existing coordinator before
it can allocate evidence or RID; test live entrypoints remain disabled.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
import http.client
from pathlib import Path
import socket
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from f0_l2_d2a_physical_admission import (
    UnreleasedPhysicalHTTPSProposal, send_live as candidate_send_live)
from f0_l2_d1_coordinator import (
    ExclusiveEvidence, FakeSource, GlobalStartGate, run_fake_concurrent,
    request_physical_source_admission)
from f0_l2_d1_concrete_https import send_live as concrete_send_live
from f0_l2_d1_real_sender_contract import (
    send_live as contract_send_live,
    require_real_sender_release)
from f0_l2_d1_protected_mac_entry import send_live as mac_send_live


class PhysicalSourceAdmissionClosedTests(unittest.TestCase):
    @staticmethod
    def proposal():
        return UnreleasedPhysicalHTTPSProposal(
            reviewed_sha="a" * 40,
            source_manifest_sha256="b" * 64,
            permit_sha256="c" * 64,
            candidate_intent_sha256="d" * 64)

    def test_descriptor_is_fixed_and_diagnostic_not_authority(self):
        source = self.proposal()
        diag = source.to_diagnostic()
        self.assertEqual(diag["endpoint"], "https://bsc-dataseed.bnbchain.org")
        self.assertEqual(diag["chain_id"], 56)
        self.assertEqual(diag["methods"],
                         ["eth_chainId", "eth_blockNumber",
                          "eth_getBlockByNumber"])
        self.assertEqual(diag["max_inflight"], 3)
        self.assertFalse(diag["trusted_d2"])
        self.assertFalse(diag["trusted_d3"])
        self.assertFalse(diag["physical_source_constructed"])
        self.assertEqual(diag["network_requests"], 0)
        self.assertFalse(callable(source))
        self.assertFalse(hasattr(source, "reply"))
        self.assertFalse(hasattr(source, "reply_over_memory_https"))
        with self.assertRaises(FrozenInstanceError):
            source.endpoint = "https://attacker.invalid"

    def test_proposal_forgeries_and_widened_configuration_rejected(self):
        good = {
            "reviewed_sha": "a" * 40,
            "source_manifest_sha256": "b" * 64,
            "permit_sha256": "c" * 64,
            "candidate_intent_sha256": "d" * 64,
        }
        for changed in (
            {"reviewed_sha": "bad"},
            {"source_manifest_sha256": "f" * 63},
            {"permit_sha256": True},
            {"candidate_intent_sha256": "0" * 65},
            {"endpoint": "https://elsewhere.invalid"},
            {"chain_id": True},
            {"methods": ["eth_chainId", "eth_blockNumber",
                         "eth_getBlockByNumber"]},
            {"methods": ("eth_chainId",)},
            {"max_inflight": 4},
            {"max_inflight": True},
        ):
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(
                        ValueError, "D2A_PHYSICAL_PROPOSAL_SCOPE_INVALID"):
                    UnreleasedPhysicalHTTPSProposal(**dict(good, **changed))

    def test_exact_plausible_source_rejected_before_any_side_effect(self):
        with tempfile.TemporaryDirectory() as d:
            evidence = Path(d).resolve() / "evidence"
            evidence.mkdir(mode=0o700)
            candidate = self.proposal()
            with patch.object(ExclusiveEvidence, "__init__",
                              side_effect=AssertionError("WRITER_CREATED")
                              ) as writer, patch(
                    "http.client.HTTPSConnection",
                    side_effect=AssertionError("REAL_HTTPS_CTOR")
                    ) as https, patch.object(
                    socket, "create_connection",
                    side_effect=AssertionError("REAL_SOCKET")
                    ) as sock:
                with self.assertRaisesRegex(
                        ValueError,
                        "D2A_PHYSICAL_SOURCE_ADMISSION_BLOCKED_D2_D3"):
                    run_fake_concurrent(candidate, evidence)
                writer.assert_not_called()
                https.assert_not_called()
                sock.assert_not_called()
            self.assertEqual(list(evidence.iterdir()), [])

    def test_direct_single_coordinator_admission_refuses_all_data(self):
        for proposal in (None, {}, self.proposal()):
            with self.subTest(kind=type(proposal).__name__):
                with self.assertRaisesRegex(
                        ValueError,
                        ("D2A_PHYSICAL_SOURCE_ADMISSION_BLOCKED_D2_D3"
                         if type(proposal) is UnreleasedPhysicalHTTPSProposal
                         else "D2A_PHYSICAL_SOURCE_EXACT_PROPOSAL_REQUIRED")):
                    request_physical_source_admission(proposal)

    def test_direct_shared_gate_cannot_treat_candidate_as_transport(self):
        source = self.proposal()
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("REAL_HTTPS_CTOR")) as ctor:
            gate = GlobalStartGate(250)
            with self.assertRaisesRegex(
                    ValueError, "D2A_PHYSICAL_SOURCE_ADMISSION_BLOCKED_D2_D3"):
                gate.run(
                    {"jsonrpc": "2.0", "id": 1,
                     "method": "eth_chainId", "params": []},
                    source, block_head_deadline=None,
                    dispatch_deadline=time.monotonic() + 5,
                    timeout_ms=5000, reservation_guard=lambda _: None)
            ctor.assert_not_called()
            self.assertEqual(gate.starts, [])

    def test_disguised_fake_subclass_and_instance_callback_refused(self):
        class SneakyFake(FakeSource):
            def reply(self, request):
                raise AssertionError("EXECUTED_UNTRUSTED_REPLY")

        with tempfile.TemporaryDirectory() as d:
            evidence = Path(d).resolve() / "evidence"
            evidence.mkdir(mode=0o700)
            injected = FakeSource(delay_ms=0)
            injected.reply = lambda _: (_ for _ in ()).throw(
                AssertionError("EXECUTED_INJECTED_REPLY"))
            for source in (SneakyFake(delay_ms=0), injected):
                with self.subTest(source=type(source).__name__):
                    with self.assertRaisesRegex(ValueError, "D1_SCOPE_INVALID"):
                        run_fake_concurrent(source, evidence)
                    self.assertEqual(list(evidence.iterdir()), [])

    def test_lower_level_gate_refuses_duck_typed_and_mutated_sources(self):
        payload = {"jsonrpc": "2.0", "id": 1,
                   "method": "eth_chainId", "params": []}
        class DuckTypedNetworkSource:
            def reply(self, _request):
                raise AssertionError("UNTRUSTED_DUCK_REPLY_CALLED")
        subclass = type("InjectedSubclass", (FakeSource,), {
            "reply": lambda self, _r: (_ for _ in ()).throw(
                AssertionError("SUBCLASS_CALLED"))})
        instance = FakeSource(delay_ms=0)
        instance.reply = lambda _r: (_ for _ in ()).throw(
            AssertionError("INSTANCE_CALLED"))
        for source in (DuckTypedNetworkSource(),
                       subclass(delay_ms=0), instance):
            with self.subTest(source=type(source).__name__):
                gate = GlobalStartGate(250)
                with self.assertRaisesRegex(
                        ValueError, "D2A_GATE_NON_FAKE_SOURCE_REFUSED"):
                    gate.run(payload, source, block_head_deadline=None,
                             dispatch_deadline=time.monotonic() + 5,
                             timeout_ms=5000)
                self.assertEqual(gate.starts, [])

    def test_no_valid_candidate_or_test_token_can_open_any_live_entry(self):
        for live in (
                candidate_send_live, concrete_send_live, contract_send_live,
                mac_send_live, require_real_sender_release):
            with self.subTest(entry=live.__module__ + "." + live.__name__):
                with self.assertRaises(ValueError):
                    live(self.proposal(), candidate_intent={"trusted": True},
                         _test_capability=object())


if __name__ == "__main__":
    unittest.main()
