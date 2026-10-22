"""Offline regressions for Monster P0 source-time asof projection.

Not a proof of external event provenance, not a production P1 approval.
"""
import importlib.util
from pathlib import Path
import unittest


SOURCE = (Path(__file__).resolve().parents[1] / "mission_agent" /
          "early" / "pit_asof.py")
spec = importlib.util.spec_from_file_location("monster_p0_pit_asof", SOURCE)
pit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pit)

TOKEN = "56:0x" + "a" * 40
OTHER = "56:0x" + "b" * 40
DECISION = "2025-07-01T00:00:02Z"
CHAIN_AT = "2025-07-01T00:00:01Z"
SRC_HASH = "c" * 64
POLICY_SHA = "d" * 64


def record(**overrides):
    data = {
        "schema_version": "v1", "event_id": "e1", "token_key": TOKEN,
        "event_type": "POOL_CREATED", "venue": "PancakeV2",
        "chain_event_at": CHAIN_AT, "source_sha256": SRC_HASH,
        "origin_kind": "RAW_CHAIN_LOG", "derivation_kind": "DIRECT",
        "pit_status": "PIT_VERIFIED",
        "availability_basis": "ACTUAL_LIVE_OBSERVER_RECEIPT",
        "available_at": "2025-07-01T00:00:01.500Z",
        "observed_at": "2025-07-01T00:00:01.500Z",
        "published_at": None,
        "ingested_at": "2026-10-22T07:00:00Z",
        "future_90day_outcome": "10X",
        "future_hour_volume": 10 ** 30,
    }
    data.update(overrides)
    return data


def projected(items, decision=DECISION, policy="LIVE_OBSERVED", **kw):
    return pit.asof(TOKEN, decision, policy, events=items, **kw)


class MonsterAsOfGateTests(unittest.TestCase):
    def test_actual_receipt_visible_by_decision(self):
        r = projected([record()])
        self.assertEqual((r["pit_status"], len(r["events"])),
                         ("PIT_VERIFIED", 1))
        self.assertFalse(r["source_provenance_independently_verified"])
        self.assertFalse(r["p1_gate_passed"])

    def test_reconstructed_and_no_verifiable_views_never_approve_p1(self):
        e = record(pit_status="PIT_RECONSTRUCTED_ONLY",
                   availability_basis="RECONSTRUCTED_DELAY_ASSUMPTION",
                   available_at=None)
        r = projected([e], policy="RECONSTRUCTED_CONSERVATIVE",
                      historical_delay_ms=1000,
                      historical_delay_policy_sha256=POLICY_SHA)
        self.assertFalse(r["p1_gate_passed"])
        self.assertFalse(r["source_provenance_independently_verified"])
        unknown = projected([record()], policy="NO_VERIFIABLE_ASOF")
        self.assertFalse(unknown["p1_gate_passed"])

    def test_public_offchain_announcement_with_null_chain_clock(self):
        e = record(event_id="announcement", event_type="ALPHA_ANNOUNCED",
                   chain_event_at=None,
                   availability_basis="ACTUAL_HISTORICAL_PUBLICATION",
                   available_at="2025-07-01T00:00:01Z",
                   published_at="2025-07-01T00:00:01Z")
        r = projected([e])
        self.assertEqual(r["pit_status"], "PIT_VERIFIED")
        self.assertIsNone(r["events"][0]["chain_event_at"])
        self.assertFalse(r["p1_gate_passed"])

    def test_future_optional_chain_clock_cannot_leak_into_past(self):
        e = record(event_id="future-anchor",
                   event_type="ALPHA_ANNOUNCED",
                   chain_event_at="2025-07-03T00:00:00Z",
                   availability_basis="ACTUAL_HISTORICAL_PUBLICATION",
                   available_at="2025-07-01T00:00:01Z",
                   published_at="2025-07-01T00:00:01Z")
        self.assertEqual(projected([e])["events"], [])
        self.assertEqual(projected([record(), e]), projected([record()]))

    def test_missing_onchain_clock_is_not_scored(self):
        self.assertEqual(projected([record(chain_event_at=None)])["events"], [])

    def test_offchain_clock_not_synthesized_from_block_delay(self):
        e = record(event_type="ALPHA_ANNOUNCED", chain_event_at=None,
                   pit_status="PIT_RECONSTRUCTED_ONLY",
                   availability_basis="RECONSTRUCTED_DELAY_ASSUMPTION",
                   available_at=None)
        r = projected([e], policy="RECONSTRUCTED_CONSERVATIVE",
                      historical_delay_ms=1000,
                      historical_delay_policy_sha256=POLICY_SHA)
        self.assertEqual(r["events"], [])
        self.assertEqual(r["pit_status"], "NOT_SCORABLE")

    def test_future_visible_event_is_excluded(self):
        r = projected([record(available_at="2025-07-01T00:00:03Z",
                              observed_at="2025-07-01T00:00:03Z")])
        self.assertEqual(r["events"], [])
        self.assertEqual(r["pit_status"], "NOT_SCORABLE")

    def test_poisoned_future_event_cannot_change_prior_asof(self):
        base = projected([record()])
        extra = record(event_id="future", chain_event_at="2025-07-01T00:00:08Z",
                       available_at="2025-07-01T00:00:08Z",
                       observed_at="2025-07-01T00:00:08Z")
        self.assertEqual(base, projected([record(), extra]))

    def test_later_holder_and_outcome_fields_not_visible(self):
        clean = record()
        clean.pop("future_90day_outcome")
        clean.pop("future_hour_volume")
        poison = record(current_owner="0x" + "0" * 40,
                        future_binance_alpha=True)
        self.assertEqual(projected([clean]), projected([poison]))
        self.assertNotIn("future_90day_outcome",
                         str(projected([poison])))

    def test_missing_available_at_excluded(self):
        self.assertEqual(projected([record(available_at=None)])["events"], [])

    def test_wrong_status_or_basis_excluded(self):
        self.assertEqual(projected([record(pit_status="NOT_SCORABLE")])["events"], [])
        self.assertEqual(projected([record(availability_basis="UNKNOWN")])["events"], [])
        self.assertEqual(projected([record(pit_status="PIT_RECONSTRUCTED_ONLY",
                                            availability_basis="RECONSTRUCTED_DELAY_ASSUMPTION",
                                            available_at=None)])["events"], [])

    def test_foreign_token_same_ticker_stays_separate(self):
        e = record(event_id="e2", token_key=OTHER, token_symbol="SAME")
        self.assertEqual(projected([e])["events"], [])

    def test_identical_duplicate_idempotent(self):
        self.assertEqual(projected([record()]),
                         projected([record(), record()]))

    def test_conflicting_duplicate_rejected(self):
        with self.assertRaisesRegex(pit.PITAsOfError, "CONFLICTING"):
            projected([record(), record(venue="Different")])

    def test_reconstructed_requires_explicit_frozen_parameters(self):
        e = record(pit_status="PIT_RECONSTRUCTED_ONLY",
                   availability_basis="RECONSTRUCTED_DELAY_ASSUMPTION",
                   available_at=None)
        with self.assertRaisesRegex(pit.PITAsOfError, "FROZEN_DELAY"):
            projected([e], policy="RECONSTRUCTED_CONSERVATIVE")
        with self.assertRaisesRegex(pit.PITAsOfError, "FROZEN_DELAY"):
            projected([e], policy="RECONSTRUCTED_CONSERVATIVE",
                      historical_delay_ms=0,
                      historical_delay_policy_sha256=POLICY_SHA)
        with self.assertRaisesRegex(pit.PITAsOfError, "FROZEN_DELAY"):
            projected([e], policy="RECONSTRUCTED_CONSERVATIVE",
                      historical_delay_ms=500)

    def test_reconstructed_boundary_and_never_verified(self):
        e = record(pit_status="PIT_RECONSTRUCTED_ONLY",
                   availability_basis="RECONSTRUCTED_DELAY_ASSUMPTION",
                   available_at=None)
        kw = {"policy": "RECONSTRUCTED_CONSERVATIVE",
              "historical_delay_ms": 1000,
              "historical_delay_policy_sha256": POLICY_SHA}
        self.assertEqual(projected([e], decision="2025-07-01T00:00:01.999Z",
                                   **kw)["events"], [])
        r = projected([e], decision="2025-07-01T00:00:02Z", **kw)
        self.assertEqual(r["pit_status"], "PIT_RECONSTRUCTED_ONLY")
        self.assertEqual(r["events"][0]["pit_status"],
                         "PIT_RECONSTRUCTED_ONLY")
        self.assertEqual(r["assumption_ms"], 1000)

    def test_fake_reconstruction_basis_rejected(self):
        e = record(pit_status="PIT_RECONSTRUCTED_ONLY", available_at=None)
        r = projected([e], policy="RECONSTRUCTED_CONSERVATIVE",
                      historical_delay_ms=1,
                      historical_delay_policy_sha256=POLICY_SHA)
        self.assertEqual(r["events"], [])

    def test_2026_ingested_at_not_reinterpreted_as_2025_observation(self):
        e = record(pit_status="NOT_SCORABLE", available_at=None,
                   availability_basis="UNKNOWN",
                   observed_at="2026-10-22T07:00:00Z")
        self.assertEqual(projected([e])["events"], [])

    def test_unknown_policy_fail_closed(self):
        with self.assertRaisesRegex(pit.PITAsOfError, "INFORMATION_POLICY"):
            projected([record()], policy="ASSUME_INSTANT")
        r = projected([record()], policy="NO_VERIFIABLE_ASOF")
        self.assertEqual(r["events"], [])
        self.assertEqual(r["pit_status"], "NOT_SCORABLE")

    def test_naive_or_invalid_clock_rejected(self):
        with self.assertRaisesRegex(pit.PITAsOfError, "OFFSET_AWARE"):
            projected([record()], decision="2025-07-01T00:00:02")
        with self.assertRaisesRegex(pit.PITAsOfError, "OFFSET_AWARE"):
            projected([record(available_at="yesterday")])

    def test_publication_later_than_claimed_availability_rejected(self):
        e = record(availability_basis="ACTUAL_HISTORICAL_PUBLICATION",
                   published_at="2025-07-01T00:00:03Z")
        with self.assertRaisesRegex(pit.PITAsOfError, "PROOF_CLOCK"):
            projected([e])

    def test_inconsistent_chain_clock_rejected(self):
        e = record(chain_event_at="2025-07-01T00:00:04Z")
        with self.assertRaisesRegex(pit.PITAsOfError, "AVAILABLE_BEFORE"):
            projected([e])

    def test_missing_source_hash_rejected(self):
        with self.assertRaisesRegex(pit.PITAsOfError, "EVENT_ID_TYPE_OR_SOURCE"):
            projected([record(source_sha256="")])

    def test_reconstruction_cannot_claim_verification_in_mixed_view(self):
        e = record(event_id="recon", pit_status="PIT_RECONSTRUCTED_ONLY",
                   availability_basis="RECONSTRUCTED_DELAY_ASSUMPTION",
                   available_at=None)
        r = projected([record(), e], policy="RECONSTRUCTED_CONSERVATIVE",
                      historical_delay_ms=1000,
                      historical_delay_policy_sha256=POLICY_SHA)
        self.assertEqual(r["pit_status"], "PIT_RECONSTRUCTED_ONLY")
        self.assertEqual(len(r["events"]), 2)


if __name__ == "__main__":
    unittest.main()
